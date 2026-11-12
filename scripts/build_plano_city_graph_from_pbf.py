"""Build and clip a walking graph from a verified local OSM extract."""
from pathlib import Path
import json,re,os
import geopandas as gpd,osmnx as ox
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('EMPATH_OSM_DIR',str(ROOT/'output/plano_city')));N=OUT/'network'
def run():
 source=json.load(open(OUT/'city_osm_extract.json'));elements=source['elements'];allowed=[];ids=set()
 deny=re.compile('abandoned|bus_guideway|construction|motor|no|planned|platform|proposed|raceway|razed|rest_area|services')
 for el in elements:
  if el['type']!='way':continue
  t=el['tags'];h=t.get('highway','')
  if t.get('area')=='yes' or t.get('access') in ['private','no'] or t.get('foot')=='no' or t.get('service')=='private' or deny.search(h):continue
  if h=='cycleway' and t.get('foot') not in ['yes','designated','permissive']:continue
  if any(t.get(k)=='separate' for k in ['sidewalk','sidewalk:both','sidewalk:left','sidewalk:right']):continue
  allowed.append(el);ids.update(el['nodes'])
 selected=[el for el in elements if el['type']=='node' and el['id'] in ids]+allowed
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
 area=gpd.GeoSeries([city.geometry.union_all().buffer(float(os.environ.get('EMPATH_NETWORK_BUFFER_M','1000')))],crs=26914).to_crs(4326).iloc[0]
 ox.settings.useful_tags_way=list(dict.fromkeys(ox.settings.useful_tags_way+['foot','sidewalk','crossing','surface','access','lit','incline']))
 graph=ox.graph._create_graph([{'elements':selected}],bidirectional=True)
 graph=ox.truncate.truncate_graph_polygon(graph,area,truncate_by_edge=True)
 if os.environ.get('EMPATH_PRESERVE_CITY_ANCHORS')=='1':
  import pandas as pd
  anchors=set(pd.read_csv(ROOT/'output/plano_city/accessibility/accessibility_pois.csv').network_node.astype(int))
  anchors.update(pd.read_csv(ROOT/'output/plano_city/accessibility/block_accessibility.csv').access_network_node.astype(int))
  for node in anchors:
   if node in graph:graph.nodes[node]['boundary_audit_anchor']=True
  graph=ox.simplification.simplify_graph(graph,node_attrs_include=['boundary_audit_anchor'])
 else:graph=ox.simplification.simplify_graph(graph)
 N.mkdir(parents=True,exist_ok=True);ox.save_graphml(graph,N/'walking_graph.graphml')
 print('City walking graph:',len(graph),'nodes,',graph.number_of_edges(),'edges',flush=True)
 return graph
if __name__=='__main__':run()
