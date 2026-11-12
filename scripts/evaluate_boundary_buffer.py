"""Compare 1 km versus 3 km acquisition support on time-only walking costs.
This diagnostic does not fabricate environmental features outside their coverage.
"""
from pathlib import Path
import json,gzip
import geopandas as gpd,pandas as pd,numpy as np,networkx as nx,osmnx as ox
from shapely.geometry import Point,Polygon
from shapely import make_valid
from scipy.spatial import cKDTree
from poi_categories import classify
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility';EXP=ROOT/'output/plano_boundary_3km';DEST=ROOT/'netlify_site/src/data'
def run():
 graph=ox.load_graphml(EXP/'network/walking_graph.graphml');nodes=ox.graph_to_gdfs(graph,edges=False).to_crs(26914)
 for u,v,k,d in graph.edges(keys=True,data=True):d['walk_seconds']=float(d['length'])/1.2
 tree=cKDTree(np.c_[nodes.geometry.x,nodes.geometry.y]);ids=nodes.index.to_numpy();reverse=graph.reverse(copy=False)
 blocks=gpd.read_file(OUT/'block_accessibility.gpkg').to_crs(26914);pois=gpd.read_file(OUT/'accessibility_pois.gpkg').to_crs(26914)
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914).geometry.union_all();area=city.buffer(3000);ll=gpd.GeoSeries([area],crs=26914).to_crs(4326).iloc[0]
 old=pois.set_index('poi_id');rows=[]
 for r in json.load(open(EXP/'city_osm_extract.json'))['pois']:
  category=classify(r['tags']);id=f'osm_{r["type"]}_{r["id"]}'
  if category is None or id in old.index:continue
  c=r['coordinates'];shape=Point(c) if r['type']=='node' else make_valid(Polygon(c)) if len(c)>=4 and c[0]==c[-1] else Point(c[0])
  point=shape.representative_point()
  if not ll.covers(point):continue
  rows.append({'poi_id':id,'category':category,'name':r['tags'].get('name','Unnamed'),'geometry':point})
 new=gpd.GeoDataFrame(rows,crs=4326).to_crs(26914);new=new[new.intersects(area)]
 newgap,newix=tree.query(np.c_[new.geometry.x,new.geometry.y]);new['network_node']=ids[newix];new['snap_gap_m']=newgap
 # Preserve original reference node IDs, to isolate support changes from snapping changes.
 missing_origins=~blocks.access_network_node.astype(int).isin(graph.nodes)
 assert not missing_origins.any(),'Original block junction disappeared; explicit matching required'
 preserved=pois.network_node.astype(int).isin(graph.nodes)
 assert preserved.all(),'Original destination junction disappeared; explicit matching required'
 extended=pd.concat([pois[['poi_id','category','name','network_node','snap_gap_m']],new.drop(columns='geometry')],ignore_index=True)
 table=pd.read_csv(OUT/'nearest_category_costs.csv',dtype={'GEOID20':str});details=[]
 for cat in sorted(pois.category.unique()):
  targets=extended[extended.category.eq(cat)].sort_values('poi_id').drop_duplicates('network_node').set_index('network_node')
  distances,paths=nx.multi_source_dijkstra(reverse,targets.index.astype(int).tolist(),weight='walk_seconds')
  base=table[table.category.eq(cat)].set_index('GEOID20');base.index=base.index.astype(str)
  for b in blocks.itertuples():
   id=str(b.GEOID20);n=int(b.access_network_node);time=distances.get(n);prior=base.loc[id,'baseline_time_minutes'];minutes=None if time is None else time/60
   gain=None if minutes is None or pd.isna(prior) else float(prior-minutes)
   winner=None if n not in paths else targets.loc[paths[n][0]]
   details.append({'GEOID20':id,'category':cat,'baseline_1km_walk_min':prior,'expanded_3km_walk_min':minutes,'reduction_minutes':gain,'winner_3km':None if winner is None else str(winner['name']),'winner_snap_gap_m':None if winner is None else float(winner.snap_gap_m),'newly_reachable':bool(pd.isna(prior) and minutes is not None),'city_boundary_distance_m':float(b.geometry.representative_point().distance(city.boundary))})
  print('Buffer test:',cat,flush=True)
 d=pd.DataFrame(details);d.to_csv(OUT/'boundary_buffer_comparison.csv',index=False)
 # Small numerical variation from changed simplification is allowed; material increases need investigation.
 assert not d.reduction_minutes.dropna().lt(-.02).any(),'Expanded network materially increased travel time'
 flags=d[d.reduction_minutes.gt(1)|d.newly_reachable];payload={}
 for id,g in flags.groupby('GEOID20'):payload[id]={r.category:{'minutes_saved':None if pd.isna(r.reduction_minutes) else round(r.reduction_minutes,2),'newly_reachable':r.newly_reachable,'expanded_candidate':r.winner_3km} for r in g.itertuples()}
 report={'comparison':'Time-only on 1 km production support versus 3 km support, identical city origin/destination junction IDs where already cataloged; new 3 km candidates included. Same OSM snapshot and filters.','scope':'Plano city origins; 1 km versus 3 km routing/destination buffer','categories':sorted(pois.category.unique()),'blocks':len(blocks),'larger_graph_nodes':len(graph),'larger_graph_edges':graph.number_of_edges(),'additional_candidates':len(new),'material_threshold_minutes':1,'flagged_blocks':len(payload),'flagged_block_category_pairs':len(flags),'newly_reachable_pairs':int(d.newly_reachable.sum()),'max_reduction_minutes':float(d.reduction_minutes.max()),'pairs_increased_over_0_02_min':int(d.reduction_minutes.lt(-.02).sum()),'edge_effect_not_corrected':'This is a support diagnostic, not a replacement weighted score. Expanded environmental coverage/weights and validated entrances are still required to use the additional routes in production. Three kilometers is not proof of convergence. No cosmetic edge correction or demographic adjustment applied.'}
 (OUT/'boundary_buffer_method.json').write_text(json.dumps(report,indent=2));(DEST/'boundary_buffer_method.json').write_text(json.dumps(report,indent=2));(DEST/'boundary_flags.json').write_text(json.dumps(payload));(DEST/'boundary_buffer_comparison.csv').write_bytes((OUT/'boundary_buffer_comparison.csv').read_bytes())
 print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
