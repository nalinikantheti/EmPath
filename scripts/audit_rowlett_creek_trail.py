"""Locate named Rowlett Creek trail geometry and compare cached OSM to Plano."""
from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
import networkx as nx
import numpy as np
from shapely import union_all
import folium
from carto_basemap import add_basemap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/rowlett_creek_audit'

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 tags=pd.read_csv(ROOT/'output/four_zip_walking_network/edges.csv',usecols=['u','v','key','name','highway','foot','access'])
 named=tags['name'].fillna('').str.contains('rowlett creek',case=False)
 edges=gpd.read_file(ROOT/'output/geoai_full_scope/ai_walking_edges.gpkg')
 rowlett=edges.merge(tags.loc[named],on=['u','v','key'],how='inner',validate='one_to_one')
 trails=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/trails.gpkg').to_crs(edges.crs)
 official=trails[trails.trail_name.fillna('').str.contains('rowlett creek',case=False)].copy()
 if rowlett.empty or official.empty:raise ValueError('Named trail not found; inspect sources before creating a highlight.')
 named_union=union_all(rowlett.geometry)
 reference_union=union_all(official.geometry)
 local_edges=edges[edges.intersects(reference_union.buffer(25))]
 all_union=union_all(local_edges.geometry)
 missing=reference_union.difference(all_union.buffer(10))
 unmatched_name=reference_union.difference(named_union.buffer(10))
 costs=pd.read_csv(ROOT/'output/step3_friction/edge_costs.csv')
 block=pd.read_csv(ROOT/'output/step3_friction/block_proxy_edge_costs.csv')
 rowlett=rowlett.merge(costs[['u','v','key','scenario_lambda_1_0_cost_s','canopy_deficit_01','traffic_burden_01','temperature_burden_01']],on=['u','v','key'],validate='one_to_one')
 rowlett=rowlett.merge(block[['u','v','key','block_proxy_cost_s','block_canopy_deficit_01','block_traffic_burden_01','block_heat_burden_01']],on=['u','v','key'],validate='one_to_one')
 graph=nx.DiGraph()
 graph.add_edges_from(zip(tags.u.astype(int),tags.v.astype(int)))
 main=max(nx.weakly_connected_components(graph),key=len)
 trail_nodes=set(rowlett.u.astype(int))|set(rowlett.v.astype(int))
 origin=pd.read_csv(ROOT/'output/network_connections/candidate_connections.csv');origin=origin[origin.role.eq('origin')]
 representative=int(rowlett.u.iloc[0])
 access={str(r.location_id):nx.has_path(graph,int(r.network_node),representative) for r in origin.itertuples()}
 weighted=nx.DiGraph()
 known=block[block.block_proxy_cost_s.notna()]
 weighted.add_weighted_edges_from(zip(known.u.astype(int),known.v.astype(int),known.block_proxy_cost_s))
 weighted_access={}
 for r in origin.itertuples():
  reachable=nx.single_source_dijkstra_path_length(weighted,int(r.network_node),weight='weight')
  weighted_access[str(r.location_id)]=sum(n in reachable for n in trail_nodes)
 report={'osm_named_directed_edges':len(rowlett),'named_geometry_unique_length_m':float(named_union.length),
 'official_reference_pieces':len(official),'official_unique_length_m':float(reference_union.length),
 'official_length_not_within_10m_of_any_osm_edge_m':float(missing.length),
 'official_length_not_within_10m_of_named_osm_edge_m':float(unmatched_name.length),
 'weighted_block_proxy_reachable_trail_nodes_per_origin':weighted_access,
 'rowlett_nodes':len(trail_nodes),'nodes_in_largest_weak_component':sum(n in main for n in trail_nodes),
 'illustrative_origins_can_reach_one_named_trail_node':access,
 'strict_cost_known_directed_edges':int(rowlett.scenario_lambda_1_0_cost_s.notna().sum()),
 'block_proxy_cost_known_directed_edges':int(rowlett.block_proxy_cost_s.notna().sum()),
 'ai_tree_fraction_min':float(rowlett.ai_tree_cover_01.min()),'ai_tree_fraction_max':float(rowlett.ai_tree_cover_01.max()),
 'geometry_comparison':'10 m proximity is a screening tolerance, not proof of same alignment, public access or traversable connection. Remaining pieces are reference candidates, not added graph edges.',
 'interpretation':'The named trail exists in the current graph. Full-scope map previously lacked a trail-name highlight and used general friction colors. Name coverage and reference geometry may differ.',
 'source':'Cached Plano TrailCenterlines layer and original OSM extract; no new routes fabricated.'}
 (OUT/'rowlett_audit.json').write_text(json.dumps(report,indent=2))
 rowlett.to_file(OUT/'rowlett_osm_edges.gpkg',driver='GPKG',index=False)
 official.to_file(OUT/'rowlett_official_reference.gpkg',driver='GPKG',index=False)
 region=reference_union.buffer(600)
 context=edges.loc[edges.intersects(region),['geometry']].to_crs(4326)
 m=folium.Map(tiles=None,prefer_canvas=True);add_basemap(m)
 folium.GeoJson(json.loads(context.to_json()),name='Existing walking network nearby',style_function=lambda f:{'color':'#64748b','weight':1,'opacity':.55}).add_to(m)
 properties=['u','v','key','name','ai_tree_cover_01','ai_corridor_coverage_01','scenario_lambda_1_0_cost_s','block_proxy_cost_s','geometry']
 folium.GeoJson(json.loads(rowlett[properties].to_crs(4326).to_json()),name='Rowlett Creek · actual named OSM graph edges',style_function=lambda f:{'color':'#00883f','weight':5,'opacity':1},tooltip=folium.GeoJsonTooltip(fields=properties[:-1])).add_to(m)
 folium.GeoJson(json.loads(official[['trail_name','type','users','geometry']].to_crs(4326).to_json()),name='Plano official Rowlett Creek trail reference',show=False,style_function=lambda f:{'color':'#a42ea5','weight':4,'dashArray':'7 5'},tooltip=folium.GeoJsonTooltip(fields=['trail_name','type','users'])).add_to(m)
 if not missing.is_empty:
  gaps=gpd.GeoDataFrame({'note':['Official geometry more than 10 m from any existing OSM edge; not automatically connected']},geometry=[missing],crs=edges.crs)
  gaps.to_file(OUT/'reference_geometry_to_review.gpkg',driver='GPKG',index=False)
  folium.GeoJson(json.loads(gaps.to_crs(4326).to_json()),name='Possible geometry gaps · review before routing',style_function=lambda f:{'color':'#df311c','weight':5,'dashArray':'4 6'},tooltip=folium.GeoJsonTooltip(fields=['note'])).add_to(m)
 bounds=official.to_crs(4326).total_bounds;m.fit_bounds([[bounds[1],bounds[0]],[bounds[3],bounds[2]]])
 center=official.geometry.union_all().representative_point() if hasattr(official.geometry,'union_all') else reference_union.representative_point()
 point=gpd.GeoSeries([center],crs=edges.crs).to_crs(4326).iloc[0]
 folium.Marker([point.y,point.x],tooltip='Rowlett Creek Trail · Plano / Oak Point area',icon=folium.Icon(color='green',icon='leaf')).add_to(m)
 m.get_root().html.add_child(folium.Element('<div style="position:fixed;bottom:25px;left:20px;z-index:9999;background:white;padding:14px;font:14px system-ui;max-width:330px"><b>Rowlett Creek Trail audit</b><br>Green: actual named OSM graph edges.<br>Purple (toggle): official trail reference.<br>Red dashes: official geometry >10 m from any graph edge; review needed.<br>Highlight colors identify sources, not shade.<br>No new connections have been fabricated.</div>'))
 folium.LayerControl(collapsed=False).add_to(m);m.save(OUT/'rowlett_creek_trail.html')
 return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
