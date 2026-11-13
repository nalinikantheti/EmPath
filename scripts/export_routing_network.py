"""Compact real weighted edges for inspectable client-side routes, no fabricated connectors."""
from pathlib import Path
import os,json,gzip,hashlib
import pandas as pd,geopandas as gpd,numpy as np
from shapely import union_all
from city_scope import buffer_m
ROOT=Path(__file__).resolve().parents[1];CITY=os.environ.get('EMPATH_CITY_MODE')=='1'
OUT=ROOT/('output/plano_city/accessibility' if CITY else 'output/block_accessibility')

def run():
 edges=gpd.read_file(ROOT/('output/plano_city/network/edges.gpkg' if CITY else 'output/geoai_full_scope/ai_walking_edges.gpkg')).to_crs(26914)
 costs=pd.read_csv(ROOT/('output/plano_city/friction/block_proxy_edge_costs.csv' if CITY else 'output/step3_friction/block_proxy_edge_costs.csv'))
 if not CITY:
  tags=pd.read_csv(ROOT/'output/four_zip_walking_network/edges.csv',usecols=['u','v','key','name','highway'])
  edges=edges.merge(tags,on=['u','v','key'],validate='one_to_one')
 if 'nearby_tree_cover_01' not in costs:costs['nearby_tree_cover_01']=1-costs.block_canopy_deficit_01
 for field in ['block_heat_burden_01','block_traffic_burden_01','tree_sample_coverage_01']:
  if field not in costs:costs[field]=np.nan
 d=edges[['u','v','key','length','name','highway','geometry']].merge(costs[['u','v','key','block_proxy_cost_s','block_proxy_nearby_used','nearby_tree_cover_01','block_heat_burden_01','block_traffic_burden_01','tree_sample_coverage_01']],on=['u','v','key'],validate='one_to_one')
 d=d[d.block_proxy_cost_s.notna()].reset_index(drop=True)
 road_file=ROOT/'output/plano_city/traffic_roads.gpkg'
 if not road_file.exists():road_file=ROOT/'data/processed/plano_reference/traffic_roads.gpkg'
 roads=gpd.read_file(road_file).to_crs(26914)
 busy=roads[roads.aadt.ge(25000)]
 corridor=union_all(busy.geometry.buffer(30))
 idx=d.sindex.query(corridor,predicate='intersects');near=np.zeros(len(d))
 if len(idx):near[idx]=np.minimum(1,d.geometry.iloc[idx].intersection(corridor).length.to_numpy()/d['length'].iloc[idx].to_numpy())
 d['busy_road_fraction_01']=near
 ll=d.to_crs(4326);node_path=ROOT/('output/plano_city/network/nodes.csv' if CITY else 'output/four_zip_walking_network/nodes.csv');nodes=pd.read_csv(node_path)
 records=[]
 for r in ll.itertuples():
  shape=r.geometry
  lines=[list(shape.coords)] if shape.geom_type=='LineString' else [list(g.coords) for g in shape.geoms]
  lines=[[[round(x,6),round(y,6)] for x,y in line] for line in lines]
  highway=str(r.highway);path_tag=any(tag in highway for tag in ['footway','path','cycleway','pedestrian','steps'])
  records.append([int(r.u),int(r.v),int(r.key),float(r.block_proxy_cost_s),float(r.length),highway,str(r.name) if not isinstance(r.name,list) and pd.notna(r.name) else str(r.name),bool(path_tag),float(r.busy_road_fraction_01),bool(r.block_proxy_nearby_used),lines,float(r.nearby_tree_cover_01),float(r.block_heat_burden_01) if pd.notna(r.block_heat_burden_01) else None,float(r.block_traffic_burden_01) if pd.notna(r.block_traffic_burden_01) else None,float(r.tree_sample_coverage_01) if pd.notna(r.tree_sample_coverage_01) else None])
 payload={'scope':f'Plano city + {buffer_m()} m context' if CITY else 'Four-ZIP pilot','edge_columns':['u','v','key','cost_equivalent_seconds','length_m','highway_tag','name','path_tag','fraction_within_30m_of_AADT_ge25000','nearby_block_proxy','geometry_lines_lonlat','nearby_predicted_tree_fraction','block_heat_index_01','block_traffic_index_01','tree_sample_coverage_01'],
 'nodes':[[int(r.osmid),float(r.x),float(r.y)] for r in nodes.itertuples()],'edges':records,
 'limits':'Paths are actual weighted network edges. Tags and traffic proximity do not prove sidewalk access or safety. Block-to-network snapping gaps are not legal walking connectors.'}
 encoded=json.dumps(payload,separators=(',',':'),allow_nan=False).encode();blob=gzip.compress(encoded,compresslevel=7)
 path=OUT/'routing_network.json.gz';path.write_bytes(blob)
 dest=ROOT/'netlify_site/src/data';dest.mkdir(exist_ok=True)
 (dest/'routing_network.json.gz').write_bytes(blob)
 report={'scope':payload['scope'],'nodes':len(nodes),'edges':len(records),'gzip_bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'traffic_proximity':'Length fraction within 30 m of mapped TxDOT AADT >=25,000; exposure context, not collision risk.','source_geometry':'Actual OSM graph edge geometry, rounded only for display; routing costs retain full precision.'}
 (OUT/'routing_network_method.json').write_text(json.dumps(report,indent=2));(dest/'routing_network_method.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return report
if __name__=='__main__':run()
