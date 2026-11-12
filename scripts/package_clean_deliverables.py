"""Package two main deliverables: block context and attributed walking graph.
An explicitly labeled equal-weight scenario layer is included. Unknown values remain missing.
"""
from datetime import datetime,timezone
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import folium
from carto_basemap import add_basemap
from block_locations import add_location_fields,add_zoom_labels

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/clean_deliverables'


def attach_traffic(zones,roads):
    """Nearest mapped road within 1 km; not all traffic or personal exposure."""
    zones=zones.reset_index(drop=True).to_crs(26914)
    roads=roads.to_crs(26914)[['source_feature_id','aadt','geometry']]
    joined=gpd.sjoin_nearest(zones[['geometry']],roads,how='left',max_distance=1000,distance_col='traffic_distance_m')
    joined=joined.sort_values(['traffic_distance_m','source_feature_id']).loc[lambda x:~x.index.duplicated()]
    zones['traffic_distance_m']=joined.traffic_distance_m.reindex(zones.index)
    zones['nearest_mapped_road_aadt']=joined.aadt.reindex(zones.index)
    zones['traffic_source_id']=joined.source_feature_id.reindex(zones.index)
    zones['traffic_context_matched']=zones.traffic_source_id.notna()
    busy=roads[roads.aadt>=10000]
    zones['busy_road_threshold_aadt']=10000  # Explicit scenario threshold, not learned.
    if len(busy):
        match=gpd.sjoin_nearest(zones[['geometry']],busy,how='left',max_distance=1000,distance_col='busy_road_distance_m')
        match=match.sort_values(['busy_road_distance_m','source_feature_id']).loc[lambda x:~x.index.duplicated()]
        zones['busy_road_distance_m']=match.busy_road_distance_m.reindex(zones.index)
        zones['nearest_busy_road_aadt']=match.aadt.reindex(zones.index)
    else:
        zones['busy_road_distance_m']=np.nan;zones['nearest_busy_road_aadt']=np.nan
    return zones


def add_weather(frame,weather):
    stats=weather['hourly_statistics']
    frame['regional_summer_temp_median_c']=stats['temperature']['median']
    frame['regional_summer_temp_p90_c']=stats['temperature']['p90']
    frame['regional_summer_rh_median_pct']=stats['relative_humidity']['median']
    frame['regional_summer_wind_median_mps']=stats['wind_speed']['median']
    frame['weather_station']=weather['station'];frame['weather_year']=weather['year']
    frame['weather_window']='June-August; 12:00-18:00 America/Chicago; same regional context across scope'
    return frame


def render_map(blocks,edges):
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(4326)
    view=folium.Map(location=[33.05,-96.74],tiles=None,prefer_canvas=True)
    add_basemap(view)
    display_cols=['GEOID20','canopy_mean','regional_summer_temp_median_c','regional_summer_temp_p90_c',
                  'traffic_distance_m','nearest_mapped_road_aadt','busy_road_distance_m','nearest_busy_road_aadt',
                  'traffic_area_mean_aadt','traffic_area_max_aadt','traffic_z_log','traffic_index_0_100',
                  'representative_address','mapped_address_count','address_note','nearby_address_reference','nearby_address_distance_m','geometry']
    blockview=add_location_fields(blocks[display_cols].to_crs(4326))
    blockview['block_coordinates']=blockview.apply(lambda r:f'{r.block_latitude:.6f}, {r.block_longitude:.6f}',axis=1)
    blockview['block_map_links']=blockview.apply(lambda r:f'<a href="{r.block_google_maps_url}" target="_blank" rel="noopener">Open in Google Maps</a><br><a href="{r.block_street_view_url}" target="_blank" rel="noopener">Try nearby Street View</a>',axis=1)
    bands=[-1e6,-1.5,-.5,0,.5,1,2,1e6]
    road_bands=[0,1000,5000,10000,25000,50000,100000,250000]
    thematic_layers=[]
    for column,title in [('canopy_mean','Estimated canopy cover (%) — class-derived, not shade'),
                         ('traffic_z_log','Area traffic vs City of Plano — log z-score')]:
        data=blockview.dropna(subset=[column])
        if len(data):
            opts={'bins':bands} if column=='traffic_z_log' else {}
            choropleth=folium.Choropleth(geo_data=json.loads(data.to_json()),data=data.drop(columns='geometry'),
                columns=['GEOID20',column],key_on='feature.properties.GEOID20',name=title,
                fill_color='YlGn' if column=='canopy_mean' else 'Blues',fill_opacity=.75,line_weight=.15,
                legend_name=title,show=column=='canopy_mean',nan_fill_color='lightgray',**opts)
            choropleth.add_to(view)
            thematic_layers.append(choropleth)
            if column=='traffic_z_log':
                # A categorical key avoids treating low counts as visual zero.
                for key,child in list(choropleth._children.items()):
                    if child is choropleth.color_scale:del choropleth._children[key]
    blockview['traffic_count_label']=blockview.traffic_area_mean_aadt.map(lambda v: f'{v:,.0f} vehicles/day' if pd.notna(v) else 'Unknown')
    folium.GeoJson(json.loads(blockview.to_json()),name='Census blocks and environmental attributes',
        style_function=lambda f:{'color':'#777','weight':.3,'fillOpacity':0},
        tooltip=folium.GeoJsonTooltip(fields=['GEOID20','traffic_index_0_100','traffic_z_log','traffic_count_label','traffic_area_max_aadt','canopy_mean'],
            aliases=['Census block','Traffic index (0–100; higher = more nearby traffic)','Log traffic z-score (standard deviations)','Length-weighted mean nearby AADT','Maximum nearby road AADT','Mean canopy cover (%)'],localize=True),
        popup=folium.GeoJsonPopup(fields=['GEOID20','representative_address','mapped_address_count','nearby_address_reference','nearby_address_distance_m','block_coordinates','address_note'],
            aliases=['Census block','Representative address inside block','Mapped addresses inside block','Nearby address outside block (orientation only)','Distance from block point to nearby address (m)','Latitude, longitude','Address meaning'],localize=False,max_width=420)).add_to(view)
    add_zoom_labels(view,blockview)
    from branca.utilities import color_brewer
    colors=color_brewer('Blues',n=len(bands)-1)
    labels=['Below −1.5 SD','−1.5 to −0.5 SD','−0.5 to 0 SD','0 to +0.5 SD','+0.5 to +1 SD','+1 to +2 SD','Above +2 SD']
    def road_color(value):
        if pd.isna(value):return '#999999'
        index=min(len(colors)-1,max(0,int(np.searchsorted(road_bands,value,side='right')-1)))
        return colors[index]
    roads=gpd.read_file(ROOT/'data/processed/txdot_aadt/traffic_roads.gpkg').to_crs(4326)
    # The underlying road layer exposes the counts directly, without assigning them to a block.
    roads['AADT_label']=roads.aadt.map(lambda v:f'{v:,.0f} vehicles/day' if pd.notna(v) else 'Unknown')
    folium.GeoJson(json.loads(roads[['source_feature_id','aadt','AADT_label','geometry']].to_json()),
        name='Source road AADT counts (separate from normalized block index)',show=False,
        style_function=lambda f:{'color':road_color(f['properties']['aadt']),'weight':2.5,'opacity':.9},
        tooltip=folium.GeoJsonTooltip(fields=['AADT_label','source_feature_id'],aliases=['Road traffic (AADT)','TxDOT source ID'])).add_to(view)
    swatches=''.join(f'<div><span style="display:inline-block;width:18px;height:12px;background:{color};border:1px solid #aaa;margin-right:6px"></span>{label}</div>' for color,label in zip(colors,labels))
    view.get_root().html.add_child(folium.Element('<div id="empath-traffic-legend" style="display:none;position:fixed;bottom:125px;left:20px;z-index:9999;background:white;padding:10px;font:12px sans-serif"><b>Traffic vs City of Plano · log z-score</b>'+swatches+'<div>Gray = unknown</div></div>'))
    # Physical lines can be duplicated by reciprocal directed edges; graph retains both.
    folium.GeoJson(json.loads(edges[['u','v','key','geometry']].to_crs(4326).to_json()),
        name='Walking network — connectivity/access still require review',show=False,
        style_function=lambda f:{'color':'#233b64','weight':1,'opacity':.55}).add_to(view)
    folium.GeoJson(json.loads(scope.to_json()),name='Four ZIP area boundaries',
        style_function=lambda f:{'color':'black','weight':2,'fill':False,'fillOpacity':0,'interactive':False}).add_to(view)
    city_path=ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg'
    if city_path.exists():
        city=gpd.read_file(city_path).to_crs(4326)
        folium.GeoJson(json.loads(city.to_json()),name='Plano municipal reference boundary',show=False,style_function=lambda f:{'color':'#222','weight':2,'dashArray':'5,5','fill':False,'fillOpacity':0,'interactive':False}).add_to(view)
    from landsat_map_layer import add_heat_layer
    add_heat_layer(view,blocks)
    from combined_block_index import add_layer
    add_layer(view,blocks,thematic_layers)
    folium.LayerControl(collapsed=False).add_to(view)
    if len(thematic_layers)==2:
        from branca.element import MacroElement,Template
        exclusive=MacroElement()
        exclusive.map_name=view.get_name()
        exclusive.layer_a=thematic_layers[0].get_name();exclusive.layer_b=thematic_layers[1].get_name()
        exclusive.canopy_scale=thematic_layers[0].color_scale.get_name()
        exclusive._template=Template('''{% macro script(this, kwargs) %}
        function updateThematicLegends(){
            var trafficLegend=document.getElementById('empath-traffic-legend');
            if(trafficLegend)trafficLegend.style.display={{this.map_name}}.hasLayer({{this.layer_b}})?'block':'none';
            if(typeof {{this.canopy_scale}}!=='undefined' && {{this.canopy_scale}}.legend){
                {{this.canopy_scale}}.legend.getContainer().style.display={{this.map_name}}.hasLayer({{this.layer_a}})?'block':'none';
            }
        }
        {{this.map_name}}.on('overlayadd',function(e){
            if(e.layer==={{this.layer_a}}){{this.map_name}}.removeLayer({{this.layer_b}});
            if(e.layer==={{this.layer_b}}){{this.map_name}}.removeLayer({{this.layer_a}});
            updateThematicLegends();
        });
        {{this.map_name}}.on('overlayremove',updateThematicLegends);
        updateThematicLegends();
        {% endmacro %}''')
        exclusive.add_to(view)
    view.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:20px;left:20px;z-index:9999;background:white;padding:10px;max-width:420px;font:13px sans-serif">Darker blue = higher nearby traffic relative to the City of Plano. Based on road-length-weighted mean AADT within block + 100 m, then log z-score. Hover for the 0–100 index, raw mean and maximum. A relative traffic indicator, not measured danger; gray = unknown.</div>'))
    b=scope.total_bounds;view.fit_bounds([[b[1],b[0]],[b[3],b[2]]]);view.save(OUT/'combined_environment_map.html')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    blocks=gpd.read_file(ROOT/'output/environment_features/block_environment.gpkg').to_crs(26914)
    roads=gpd.read_file(ROOT/'data/processed/txdot_aadt/traffic_roads.gpkg')
    weather=json.loads((ROOT/'data/processed/noaa_summer_2025/summer_scenario.json').read_text())
    blocks=add_location_fields(add_weather(attach_traffic(blocks,roads),weather))
    if 'canopy_mean' not in blocks:blocks['canopy_mean']=np.nan
    blocks['canopy_is_time_specific_shade']=False
    blocks['temperature_is_block_measurement']=False
    blocks.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
    blocks.to_crs(4326).to_file(OUT/'block_environment.geojson',driver='GeoJSON',index=False)
    blocks.drop(columns='geometry').to_csv(OUT/'block_environment.csv',index=False)
    print('Block dataset packaged:',len(blocks),flush=True)
    graph=ox.io.load_graphml(ROOT/'output/four_zip_walking_network/walking_network_all_components.graphml')
    edges=ox.convert.graph_to_gdfs(graph,nodes=False).reset_index()
    edges=add_weather(attach_traffic(edges,roads),weather)
    envfile=ROOT/'output/environment_features/edge_environment_sample.csv'
    if envfile.exists():
        attrs=pd.read_csv(envfile)
        cols=['u','v','key']+[c for c in attrs if c.startswith('canopy_')]
        attrs=attrs[cols]
        if attrs.duplicated(['u','v','key']).any():raise ValueError('Duplicate edge feature IDs')
        edges=edges.merge(attrs,on=['u','v','key'],how='left',validate='one_to_one')
    if 'canopy_mean' not in edges:edges['canopy_mean']=np.nan
    mids=gpd.GeoDataFrame({'row':edges.index},geometry=edges.to_crs(26914).geometry.interpolate(.5,normalized=True),crs=26914)
    matched=gpd.sjoin(mids,blocks[['GEOID20','geometry']],how='left',predicate='intersects')
    matched=matched.sort_values('GEOID20').drop_duplicates('row').set_index('row')
    edges['block_geoid_midpoint']=matched.GEOID20.reindex(edges.index)
    # Explicit scenario speed, excludes crossing waits and other personal differences.
    edges['baseline_walk_seconds']=pd.to_numeric(edges.length)/1.2
    fields=[c for c in edges if c.startswith(('canopy_','regional_','traffic_','nearest_','busy_','weather_','block_geoid'))]+['baseline_walk_seconds']
    for row in edges[['u','v','key']+fields].itertuples(index=False,name=None):
        u,v,key,*vals=row
        for name,value in zip(fields,vals):
            if pd.isna(value):continue
            if isinstance(value,np.generic):value=value.item()
            graph.edges[u,v,key][name]=value
    graph.graph.update(environment_join='Canopy corridor summaries where available; midpoint block ID is an index, not a whole-edge block allocation.',
        walking_speed_mps=1.2,friction_model_status='Not fitted; no learned friction cost in this cleaning deliverable',
        temperature_context=weather['limitation'])
    ox.io.save_graphml(graph,OUT/'walking_graph.graphml')
    # Vector companion for map inspection; only scalar attributes are exported.
    scalar=['u','v','key','length','geometry']+fields
    edges[scalar].to_file(OUT/'walking_edges.gpkg',driver='GPKG',index=False)
    edges[['u','v','key']+fields].to_csv(OUT/'walking_edge_attributes.csv',index=False)
    from traffic_area_index import main as update_area_traffic
    update_area_traffic()
    from add_block_addresses import main as update_addresses
    update_addresses()
    blocks=gpd.read_file(OUT/'block_environment.gpkg')
    edges=gpd.read_file(OUT/'walking_edges.gpkg')
    render_map(blocks,edges)
    summary={'created_utc':datetime.now(timezone.utc).isoformat(),'blocks':len(blocks),
        'graph_nodes':graph.number_of_nodes(),'graph_directed_edges':graph.number_of_edges(),
        'blocks_with_canopy':int(blocks.canopy_mean.notna().sum()),'edges_with_canopy':int(edges.canopy_mean.notna().sum()),
        'block_traffic_matches':int(blocks.traffic_context_matched.sum()),'edge_traffic_matches':int(edges.traffic_context_matched.sum()),
        'weather':weather,'missing_temperature_raster':True,'walking_speed_mps_assumption':1.2,'busy_road_aadt_threshold_assumption':10000,
        'limitations':['Canopy source and coverage details in output/canopy_2021/source_metadata.json',
        'No time-specific shade or local temperature predictions.', 'Nearest road within 1 km is context, not route-specific crossing safety.',
        'Traffic count year absent from service; extraction date not used as count year.',
        'Block midpoint ID does not represent full edge-block overlap.',
        'Raw graph topology retained; entrances and crossings are not yet validated.',
        'GeoAI inference not run; published canopy dataset is ML-derived, not newly inferred here.']}
    (OUT/'quality_report.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k not in ['weather','limitations']},indent=2),flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-only',action='store_true',help='Redraw from existing cleaned datasets; do not recompute features.')
    args=parser.parse_args()
    if args.map_only:
        render_map(gpd.read_file(OUT/'block_environment.gpkg'),gpd.read_file(OUT/'walking_edges.gpkg'))
        print('Traffic-volume map regenerated from saved data. Key not displayed.')
    else:
        main()
