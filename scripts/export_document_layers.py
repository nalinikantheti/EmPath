"""Export independent, document-ready images of the interactive map's data layers.
No basemap tiles or API keys are embedded in these PNGs.
"""
from pathlib import Path
import json
import html
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import normalize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm,ListedColormap
from matplotlib.ticker import FuncFormatter
from branca.utilities import color_brewer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/document_layers'


def export_all():
    OUT.mkdir(parents=True,exist_ok=True)
    data=ROOT/'output/clean_deliverables'
    blocks=gpd.read_file(data/'block_environment.gpkg').to_crs(26914)
    edges=gpd.read_file(data/'walking_edges.gpkg').to_crs(26914)
    physical=edges.loc[~edges.geometry.map(lambda g:normalize(g).wkb_hex).duplicated()].copy()
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
    city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
    roads=gpd.read_file(ROOT/'data/processed/txdot_aadt/traffic_roads.gpkg').to_crs(26914)
    pois=gpd.read_file(ROOT/'output/four_zip_walking_network/places_of_interest.geojson').to_crs(26914)
    pois.geometry=pois.geometry.representative_point()
    bounds=scope.total_bounds;records=[]
    def base(title):
        fig,ax=plt.subplots(figsize=(10,8));ax.set_title(title,fontsize=15,pad=14)
        ax.set_axis_off();return fig,ax
    def outlines(ax,labels=True):
        scope.boundary.plot(ax=ax,color='#333',linewidth=.85)
        if labels:
            for _,r in scope.iterrows():
                pt=r.geometry.representative_point();ax.text(pt.x,pt.y,str(r.ZCTA5),ha='center',fontsize=10,bbox={'facecolor':'white','alpha':.85,'edgecolor':'none','pad':2})
    def save(fig,ax,name,caption,full=False):
        if not full:
            ax.set_xlim(bounds[0]-400,bounds[2]+400);ax.set_ylim(bounds[1]-400,bounds[3]+400)
        fig.text(.06,.035,caption,fontsize=9,wrap=True)
        fig.subplots_adjust(bottom=.12)
        path=OUT/name;fig.savefig(path,dpi=200,bbox_inches='tight',facecolor='white');plt.close(fig)
        records.append({'image':name,'caption':caption})
    fig,ax=base('EmPath study scope — four Census ZIP areas')
    scope.plot(ax=ax,column='ZCTA5',cmap='Set2',alpha=.35);outlines(ax)
    save(fig,ax,'01_four_zip_scope.png','Source: Census ZCTA polygons. ZIP areas approximate postal geography; all four remain in the pilot.')
    fig,ax=base('Census blocks within the four-ZIP pilot')
    blocks.boundary.plot(ax=ax,color='#777',linewidth=.22);outlines(ax)
    save(fig,ax,'02_census_blocks.png','Source: 2020 Census blocks. Polygons are clipped to the pilot; they are not automatically residential clusters.')
    fig,ax=base('Estimated 2021 canopy cover by census block')
    blocks.plot(ax=ax,column='canopy_mean',cmap='YlGn',vmin=0,vmax=100,legend=True,linewidth=0,
                legend_kwds={'label':'Estimated canopy cover (%)','shrink':.7},missing_kwds={'color':'#ccc'})
    outlines(ax)
    save(fig,ax,'03_canopy_cover.png','Texas 2021 canopy classes converted to midpoint estimates; pixel-center block means. Gray = missing. Cover is not time-specific shade.')
    fig,ax=base('Nearby traffic relative to the City of Plano')
    bins=[-5,-1.5,-.5,0,.5,1,2,5];centers=[(a+b)/2 for a,b in zip(bins,bins[1:])]
    labels=['<−1.5 SD','−1.5 to −0.5','−0.5 to 0','0 to +0.5','+0.5 to +1','+1 to +2','>+2 SD']
    blocks.plot(ax=ax,column='traffic_z_log',cmap=ListedColormap(color_brewer('Blues',n=7)),norm=BoundaryNorm(bins,7),legend=True,linewidth=0,
        legend_kwds={'ticks':centers,'format':FuncFormatter(lambda v,p:labels[centers.index(v)] if v in centers else ''),'shrink':.7},missing_kwds={'color':'#ccc'})
    outlines(ax)
    save(fig,ax,'04_normalized_traffic.png','Length-weighted mean AADT within block + 100 m; log z-score referenced to 4,387 valid Plano city blocks. Darker = more traffic; not measured danger.')
    fig,ax=base('TxDOT road-level annual average daily traffic')
    rb=[0,1000,5000,10000,25000,50000,100000,250000]
    roads.plot(ax=ax,column='aadt',cmap=ListedColormap(color_brewer('Blues',n=7)),norm=BoundaryNorm(rb,7),linewidth=1.3,legend=True,
        legend_kwds={'label':'AADT (vehicles/day)','shrink':.7,'ticks':[0,10000,25000,50000,100000,250000]})
    outlines(ax)
    save(fig,ax,'05_road_traffic_counts.png','Source: TxDOT AADT inventory extract. Values describe road sections, not total block traffic. Count year is unavailable in this service schema.')
    fig,ax=base('OpenStreetMap pedestrian network — four ZIP areas')
    physical.plot(ax=ax,color='#315879',linewidth=.35);outlines(ax)
    save(fig,ax,'06_walking_network.png','Source: OpenStreetMap/OSMnx. Reciprocal geometry is drawn once; graph directions and disconnected components are retained. Access/crossings remain unvalidated.')
    fig,ax=base('Plano municipal reference boundary and pilot ZIP areas')
    city.plot(ax=ax,facecolor='#eeeeee',edgecolor='#111',linewidth=1.4)
    scope.plot(ax=ax,column='ZCTA5',cmap='tab10',facecolor='none',linewidth=1.7);outlines(ax)
    save(fig,ax,'07_plano_reference_boundary.png','Official City of Plano municipal polygon defines the traffic reference. Displayed pilot ZIP areas are a different geography.',full=True)
    fig,ax=base('Walking network and mapped places of interest')
    physical.plot(ax=ax,color='#abb8c4',linewidth=.3)
    pois['display_category']=np.select([pois.category.eq('pharmacy'),pois.category.isin(['supermarket','convenience'])],['Pharmacy','Food retail candidate'],default='Other mapped POI')
    for category,color in [('Other mapped POI','#737373'),('Food retail candidate','#e69f00'),('Pharmacy','#b51f40')]:
        subset=pois[pois.display_category.eq(category)]
        subset.plot(ax=ax,color=color,markersize=13,label=category,alpha=.9)
    outlines(ax);ax.legend(loc='lower left',fontsize=9)
    save(fig,ax,'08_network_and_pois.png','POIs are OSM feature locations, not verified entrances. Inventory includes 317 selected POIs; temples are not yet included. Convenience shops are not necessarily full grocery stores.')
    # A detail image for the zoom-dependent labels, away from the resolved Morada check.
    fig,ax=base('Example block address labels — close-up in 75025')
    center=gpd.GeoSeries(gpd.points_from_xy([-96.7365],[33.0906]),crs=4326).to_crs(26914).iloc[0]
    detail=blocks[blocks.geometry.intersects(center.buffer(500))]
    detail.boundary.plot(ax=ax,color='#777',linewidth=.6)
    placed=[]
    for _,r in detail.sort_values('mapped_address_count',ascending=False).iterrows():
        pt=r.geometry.representative_point()
        if not (center.x-500 < pt.x < center.x+500 and center.y-500 < pt.y < center.y+500): continue
        if any(pt.distance(other)<140 for other in placed): continue
        placed.append(pt)
        address=str(r.get('representative_address','')).split(',')[0] if r.get('mapped_address_count',0)>0 else 'No in-block address'
        ax.text(pt.x,pt.y,address+'\nBlock '+str(r.GEOID20)[-4:],fontsize=6,ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':1})
    ax.set_xlim(center.x-550,center.x+550);ax.set_ylim(center.y-550,center.y+550)
    save(fig,ax,'09_block_address_detail.png','Example of the interactive close-zoom labels. An address represents one mapped point inside a block; it is not the address of the whole block or a verified entrance.',full=True)
    from combined_block_index import calculate
    combined=calculate(blocks)
    fig,ax=base('Provisional walking-friction index — equal weights')
    combined.plot(ax=ax,column='combined_burden_0_100',cmap='YlOrRd',vmin=0,vmax=100,legend=True,linewidth=0,legend_kwds={'label':'Provisional friction (0–100)','shrink':.7},missing_kwds={'color':'#ccc'})
    outlines(ax)
    save(fig,ax,'10_provisional_walking_friction.png','50% canopy deficit + 50% traffic; assumed weights. Gray = missing. Not a learned or validated personal comfort score. Regional weather is shared context.')
    (OUT/'captions.json').write_text(json.dumps(records,indent=2))
    (OUT/'README.md').write_text('# Individual map layers for documents\n\n'+ '\n\n'.join(f"- **{r['image']}** — {r['caption']}" for r in records)+'\n\nImages are exported from local vector data without basemap tiles or API keys. Regional NOAA weather is popup context, not a separate spatial heat layer; it is therefore not rendered as a misleading block-temperature map.\n')
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>EmPath document figures</title><style>body{font:16px Georgia;max-width:1000px;margin:40px auto}img{width:100%}figure{margin:30px 0}</style><h1>EmPath document figures</h1><p><a href="interactive_map_links.html">Open interactive maps</a></p>'+''.join('<figure><a href="'+r['image']+'"><img src="'+r['image']+'"></a><figcaption>'+html.escape(r['caption'])+'</figcaption></figure>' for r in records))
    return records

if __name__=='__main__':
    print(json.dumps(export_all(),indent=2))
