"""Compare three declared route objectives on the full attributed pilot graph."""
from pathlib import Path
import json
import numpy as np,pandas as pd,geopandas as gpd,networkx as nx
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/geoai_full_scope'

def run():
 edges=gpd.read_file(OUT/'ai_walking_edges.gpkg')
 usable=edges[(edges.ai_corridor_coverage_01>=.98)&edges.ai_tree_cover_01.notna()&(edges['length']>0)]
 graph=nx.MultiDiGraph()
 for _,r in usable.iterrows():graph.add_edge(int(r.u),int(r.v),key=int(r.key),length=float(r['length']),cost=float(r.ai_canopy_proxy_cost_m),cover=float(r.ai_tree_cover_01),geometry=r.geometry)
 original=pd.read_csv(ROOT/'output/vegetation_geoai/route_comparison.csv')
 endpoints=original[original.route=='Shortest distance'][['zip','origin_node','destination_node']].drop_duplicates()
 nodes=pd.read_csv(ROOT/'output/four_zip_walking_network/nodes.csv').set_index('osmid')
 point_rows=[]
 for _,pair in endpoints.iterrows():
  for role,column in [('Start','origin_node'),('Destination','destination_node')]:
   node=nodes.loc[int(pair[column])]
   point_rows.append({'zip':str(pair.zip),'role':role,'node_id':int(pair[column]),'longitude':node.x,'latitude':node.y})
 points=pd.DataFrame(point_rows)
 gpd.GeoDataFrame(points,geometry=gpd.points_from_xy(points.longitude,points.latitude),crs=4326).to_file(OUT/'illustrative_endpoints.geojson',driver='GeoJSON',index=False)
 summaries=[];route_rows=[];all_candidates=[]
 for _,pair in endpoints.iterrows():
  a,b=int(pair.origin_node),int(pair.destination_node);zipcode=str(pair.zip)
  if a not in graph or b not in graph or not nx.has_path(graph,a,b):
   summaries.append({'zip':zipcode,'route':'Unavailable','note':'Endpoint missing or unreachable after corridor-coverage screening'});continue
  distance_path=nx.shortest_path(graph,a,b,weight='length');balanced_path=nx.shortest_path(graph,a,b,weight='cost')
  def select(path,weight):return [min(graph[u][v].values(),key=lambda d:d[weight]) for u,v in zip(path,path[1:])]
  distance_edges=select(distance_path,'length');balanced_edges=select(balanced_path,'cost')
  baseline=sum(e['length'] for e in distance_edges)
  # Collapse each parallel node pair to its shortest edge for loopless candidate generation.
  simple=nx.DiGraph()
  for u,v,d in graph.edges(data=True):
   if not simple.has_edge(u,v) or d['length']<simple[u][v]['length']:simple.add_edge(u,v,**d)
  options=[];seen=set()
  def add_candidate(path,es,source):
   length=sum(e['length'] for e in es)
   signature=tuple(e['geometry'].wkb_hex for e in es)
   if signature in seen or length>1.5*baseline+1e-6:return
   seen.add(signature)
   adjacency=sum(e['length']*e['cover'] for e in es)/length
   all_candidates.append({'zip':zipcode,'candidate':len(options)+1,'search_priority':source,'distance_m':length,'mean_tree_adjacency_01':adjacency})
   options.append((adjacency,-length,path,es))
  # Include canopy-focused candidates so the search is not dominated by tiny parking-lot detours.
  for strength in [0,.19,.5,1,2,5,20]:
   for _,_,d in graph.edges(data=True):d['search_cost']=d['length']*(1+strength*(1-d['cover']))
   path=nx.shortest_path(graph,a,b,weight='search_cost')
   add_candidate(path,select(path,'search_cost'),f'canopy penalty {strength}')
  for i,path in enumerate(nx.shortest_simple_paths(simple,a,b,weight='length')):
   es=[simple[u][v] for u,v in zip(path,path[1:])]
   if sum(e['length'] for e in es)>1.5*baseline:break
   add_candidate(path,es,'distance-ordered alternative')
   if len(options)>=30 or i>=99:break
  _,_,priority_path,priority_edges=max(options,key=lambda x:(x[0],x[1]))
  for label,path,es in [('Shortest distance',distance_path,distance_edges),('Distance–canopy trade-off',balanced_path,balanced_edges),('Tree-adjacency priority',priority_path,priority_edges)]:
   length=sum(e['length'] for e in es);adjacency=sum(e['length']*e['cover'] for e in es)/length
   summaries.append({'zip':zipcode,'route':label,'origin_node':a,'destination_node':b,'distance_m':length,'detour_ratio':length/baseline,'mean_tree_adjacency_01':adjacency,'cost_equivalent_m':sum(e['cost'] for e in es),'access_verified':False,'candidate_count':len(options)})
   for i,e in enumerate(es):route_rows.append({'zip':zipcode,'route':label,'sequence':i,'ai_tree_cover_01':e['cover'],'geometry':e['geometry']})
 pd.DataFrame(summaries).to_csv(OUT/'full_scope_route_comparison.csv',index=False)
 pd.DataFrame(all_candidates).to_csv(OUT/'full_scope_route_candidates.csv',index=False)
 if route_rows:gpd.GeoDataFrame(route_rows,crs=edges.crs).to_file(OUT/'full_scope_routes.gpkg',driver='GPKG',index=False)
 (OUT/'full_scope_routing_method.json').write_text(json.dumps({'endpoints':'Same four illustrative endpoint pairs as Notebook 13. Not verified home/service entrances.','tree_objective':'Highest length-weighted average predicted tree fraction among up to 30 unique loopless candidate paths within 1.5x shortest network distance, seeded by several distance/canopy priorities and supplemented with distance-ordered alternatives.','candidate_graph':'Canopy-priority seeds use the full multigraph. Additional distance-ordered alternatives collapse parallel node-pair connections to the shortest edge. Search settings are explicit scenarios, not learned preferences.','balanced_objective':'Distance multiplied by [1 + transferred Singapore beta × predicted canopy deficit]. Canopy replaces sun exposure as an unvalidated scenario proxy.','coverage_filter':'Require at least 98% estimated image coverage of the 5 m edge corridor.','validation':'Illustrative comparisons, not route-choice validation or a guarantee of actual shade, access, or safety.'},indent=2))
 return pd.DataFrame(summaries)
if __name__=='__main__':print(run().to_string(index=False))
