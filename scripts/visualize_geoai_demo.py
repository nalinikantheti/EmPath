"""Document and visualize actual saved model predictions, with review templates."""
from pathlib import Path
import json
import imagery_geoai_demo  # Initialize matching Rasterio PROJ data before GIS imports.
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import transform_bounds,calculate_default_transform,reproject
from rasterio.enums import Resampling
from rasterio.transform import array_bounds
import folium
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from shapely.geometry import box
from shapely import normalize
from tree_adjacency_visuals import CMAP,NORM,tree_color,legend_html
from matplotlib.lines import Line2D
from carto_basemap import add_basemap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/vegetation_geoai'

def visualize():
    records=json.loads((OUT/'imagery_manifest.json').read_text())
    edges=gpd.read_file(OUT/'ai_walking_edges.gpkg')
    trees=gpd.read_file(OUT/'predicted_tree_polygons.gpkg')
    routes_path=OUT/'comparison_routes.gpkg'
    routes=gpd.read_file(routes_path) if routes_path.exists() else None
    if routes is not None:
        lookup=edges.assign(_geom=edges.geometry.map(lambda g:normalize(g).wkb_hex)).groupby('_geom').ai_tree_cover_01.mean()
        routes['ai_tree_cover_01']=routes.geometry.map(lambda g:lookup.get(normalize(g).wkb_hex,np.nan))
    view=folium.Map(location=[33.07,-96.75],tiles=None,prefer_canvas=True);add_basemap(view)
    review=[]
    for rec in records:
        zipcode=rec['zip']
        with rasterio.open(ROOT/rec['image']) as src:
            rgb=np.moveaxis(src.read([1,2,3]),0,-1);extent=[src.bounds.left,src.bounds.right,src.bounds.bottom,src.bounds.top]
            web_tf,web_w,web_h=calculate_default_transform(src.crs,3857,src.width,src.height,*src.bounds)
            source_tf=src.transform;source_crs=src.crs
            bounds=transform_bounds(3857,4326,*array_bounds(web_h,web_w,web_tf))
        with rasterio.open(OUT/f'tree_mask_{zipcode}.tif') as src:mask=src.read(1)
        # Reproject display imagery to Web Mercator: bounding-box placement alone
        # would rotate/shift the UTM imagery relative to vector paths.
        web_rgb=np.zeros((3,web_h,web_w),dtype='uint8')
        for band in range(3):
            reproject(rgb[:,:,band],web_rgb[band],src_transform=source_tf,src_crs=source_crs,dst_transform=web_tf,dst_crs=3857,resampling=Resampling.bilinear)
        web_mask=np.full((web_h,web_w),255,dtype='uint8')
        reproject(mask,web_mask,src_transform=source_tf,src_crs=source_crs,dst_transform=web_tf,dst_crs=3857,src_nodata=255,dst_nodata=255,resampling=Resampling.nearest)
        display_dir=OUT/'display_images';display_dir.mkdir(exist_ok=True)
        Image.fromarray(np.moveaxis(web_rgb,0,-1)).save(display_dir/f'naip_{zipcode}.jpg',quality=88,optimize=True)
        rgba=np.zeros((*web_mask.shape,4),dtype=np.uint8);rgba[web_mask==1]=[30,180,50,150]
        Image.fromarray(rgba).save(display_dir/f'trees_{zipcode}.png',optimize=True)
        group=folium.FeatureGroup(name=f'{zipcode}: NAIP imagery and AI tree mask',show=True)
        for relative,name,opacity in [('./display_images/naip_'+zipcode+'.jpg','NAIP',1),('./display_images/trees_'+zipcode+'.png','AI tree prediction',.7)]:
            overlay=folium.raster_layers.ImageOverlay(np.zeros((1,1,4),dtype='uint8'),bounds=[[bounds[1],bounds[0]],[bounds[3],bounds[2]]],name=name,opacity=opacity)
            overlay.url=relative  # Keep a browser URL instead of embedding the image bytes.
            overlay.add_to(group)
        group.add_to(view)
        subset=edges[edges.demo_zip.astype(str).eq(str(zipcode))]
        fig,axs=plt.subplots(1,3,figsize=(16,6))
        axs[0].imshow(rgb,extent=extent);axs[0].set_title(f'{zipcode}: NAIP aerial image ({rec["year"]})')
        axs[1].imshow(rgb,extent=extent);axs[1].imshow(np.ma.masked_where(mask!=1,mask),extent=extent,cmap='Greens',vmin=0,vmax=1,alpha=.65);axs[1].set_title('Pretrained AI tree prediction')
        axs[2].imshow(rgb,extent=extent,alpha=.55)
        subset.plot(ax=axs[2],column='ai_tree_cover_01',cmap=CMAP,norm=NORM,linewidth=2,legend=True,legend_kwds={'label':'Predicted tree fraction in 5 m corridor','shrink':.6,'ticks':[0,.1,.25,.5,.75,1]})
        if routes is not None:
            for label,pattern in [('Shortest distance','--'),('AI canopy proxy',':'),('Tree-adjacency priority','-')]:
                r=routes[(routes.zip.astype(str)==str(zipcode))&(routes.route==label)]
                if len(r):
                    r.plot(ax=axs[2],color='#333333',linewidth=4.5,linestyle=pattern)
                    r.plot(ax=axs[2],column='ai_tree_cover_01',cmap=CMAP,norm=NORM,linewidth=2.5,linestyle=pattern)
            axs[2].legend(handles=[Line2D([0],[0],color='#333',linestyle='--',label='Distance baseline'),Line2D([0],[0],color='#333',linestyle=':',label='Distance–canopy trade-off'),Line2D([0],[0],color='#333',label='Tree-adjacency priority')],loc='lower left',fontsize=7)
        axs[2].set_title('Walking segments and illustrative routes')
        for ax in axs:ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_axis_off()
        fig.text(.05,.04,'USDA NAIP imagery; Restor TCD SegFormer-B0 predictions. Small demonstration area only.\nGreen = predicted trees, not measured shade. Model transfer and pedestrian access are unvalidated.',fontsize=10)
        fig.savefig(OUT/f'geoai_demo_{zipcode}.png',dpi=160,bbox_inches='tight');plt.close(fig)
        # Blind-review patches can be manually delineated independently of predictions.
        patchdir=OUT/'validation_patches';patchdir.mkdir(exist_ok=True)
        for i,(y,x) in enumerate([(192,192),(192,1024),(1024,192),(1024,1024)]):
            patch=rgb[y:y+256,x:x+256];filename=f'{zipcode}_patch_{i}.png';Image.fromarray(patch).save(patchdir/filename)
            review.append({'zip':zipcode,'image':filename,'manual_tree_fraction':'','model_tree_fraction':float((mask[y:y+256,x:x+256]==1).mean()),'review_notes':''})
    review_path=OUT/'manual_review_template.csv'
    if not review_path.exists():pd.DataFrame(review).to_csv(review_path,index=False)
    complete=edges[edges.complete_corridor.astype(bool)].copy()
    folium.GeoJson(json.loads(complete[['u','v','key','demo_zip','ai_tree_cover_01','ai_canopy_gap_proxy_m','geometry']].to_crs(4326).to_json()),name='AI-attributed walking segments',style_function=lambda f:{'color':tree_color(f['properties'].get('ai_tree_cover_01')),'weight':2.5,'opacity':.9},tooltip=folium.GeoJsonTooltip(fields=['demo_zip','ai_tree_cover_01','ai_canopy_gap_proxy_m'],aliases=['Demo ZIP','Predicted tree cover within 5 m corridor (0–1)','Canopy-deficit length proxy (m; not actual sun exposure)'])).add_to(view)
    if routes is not None:
        for label,pattern in [('Shortest distance','8 6'),('AI canopy proxy','2 6'),('Tree-adjacency priority',None)]:
            r=routes[routes.route==label]
            group=folium.FeatureGroup(name=label+' — colors show tree adjacency',show=label=='Tree-adjacency priority')
            folium.GeoJson(json.loads(r.to_crs(4326).to_json()),style_function=lambda f,p=pattern:{'color':'#333','weight':7,'dashArray':p,'opacity':.8}).add_to(group)
            folium.GeoJson(json.loads(r.to_crs(4326).to_json()),style_function=lambda f,p=pattern:{'color':tree_color(f['properties'].get('ai_tree_cover_01')),'weight':4,'dashArray':p},tooltip=folium.GeoJsonTooltip(fields=['zip','route','ai_tree_cover_01'],aliases=['Demo ZIP','Routing method','Predicted tree fraction in 5 m corridor'])).add_to(group)
            group.add_to(view)
    view.get_root().html.add_child(folium.Element(legend_html()))
    folium.LayerControl(collapsed=False).add_to(view)
    view.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:20px;left:20px;z-index:9999;background:white;padding:12px;max-width:380px;font:13px sans-serif"><b>Actual pretrained GeoAI inference — demonstration</b><br>Four small NAIP tiles, not full ZIP coverage. Green areas = model-predicted tree cover. Paths use the same orange-to-green tree-adjacency scale. Toggle routing layers to compare overlapping paths. Tree-priority selects the highest mean nearby canopy among up to 30 candidate paths within 1.5× shortest distance. The separate balanced cost trades distance for canopy. Neither measures actual shade. Tree proximity is not measured shade. Entrances and crossings remain unverified.</div>'))
    total=gpd.GeoSeries([box(*r['extent_m']) for r in records],crs=26914).to_crs(4326).total_bounds
    view.fit_bounds([[total[1],total[0]],[total[3],total[2]]]);view.save(OUT/'geoai_canopy_routes.html')
    method={'inference_completed':True,'full_zip_coverage':False,'demo_tiles':len(records),'tree_polygon_count':len(trees),'attributed_directed_edges':len(edges),'edges_with_full_corridor_coverage':len(complete),'validation':'Review template and 16 imagery-only patches provided. Independent manual labels not yet supplied; no local accuracy claimed.','production_graph_modified':False,'display':'Web-Mercator-reprojected JPEG imagery and PNG masks served as external assets. JPEG is display-only; inference uses original lossless RGB.','next_step':'Review predictions and route accessibility before replacing production features or expanding imagery coverage.'}
    (OUT/'demo_summary.json').write_text(json.dumps(method,indent=2));return method
if __name__=='__main__':print(json.dumps(visualize(),indent=2))
