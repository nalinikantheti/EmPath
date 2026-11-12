"""Compare weighted and fastest routes to identical destinations on a spatial sample."""
from pathlib import Path
import json,gzip
import pandas as pd,numpy as np,networkx as nx
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility'
def run():
 data=json.loads(gzip.decompress((OUT/'routing_network.json.gz').read_bytes()));es=data['edges'];graph=nx.MultiDiGraph()
 for i,e in enumerate(es):graph.add_edge(e[0],e[1],key=e[2],weight=e[3],time=e[4]/1.2,index=i)
 b=pd.read_csv(OUT/'block_accessibility.csv',dtype={'GEOID20':str});p=pd.read_csv(OUT/'accessibility_pois.csv').set_index('poi_id');nearest=pd.read_csv(OUT/'nearest_category_costs.csv',dtype={'GEOID20':str}).set_index(['GEOID20','category'])
 eligible=b[(b.HU100>0)&b.access_snap_gap_m.le(100)&b.access_essential_mean_equiv_min.notna()]
 selected=[]
 for column,ascending in [('access_essential_mean_equiv_min',True),('access_essential_mean_equiv_min',False),('block_latitude',False),('block_latitude',True),('block_longitude',False),('block_longitude',True)]:
  candidates=eligible[~eligible.GEOID20.isin(selected)].sort_values(column,ascending=ascending);selected.append(candidates.GEOID20.iloc[0])
 rows=[]
 for id in selected:
  block=b[b.GEOID20.eq(id)].iloc[0];start=int(block.access_network_node)
  for category in ['hindu_temple','supermarket','pharmacy']:
   item=nearest.loc[(id,category)];dest=p.loc[item.closest_poi_id];end=int(dest.network_node);routes={}
   for objective in ['weight','time']:
    path=nx.shortest_path(graph,start,end,weight=objective);indices=[min(graph[u][v].values(),key=lambda a:a[objective])['index'] for u,v in zip(path,path[1:])];parts=[es[i] for i in indices];distance=sum(e[4] for e in parts)
    routes[objective]={'edge_indices':indices,'distance_m':distance,'walking_minutes':distance/1.2/60,'friction_equivalent_minutes':sum(e[3] for e in parts)/60,'busy_road_length_m':sum(e[4]*e[8] for e in parts),'path_tag_length_m':sum(e[4] for e in parts if e[7])}
   a,z=routes['weight'],routes['time'];assert a['friction_equivalent_minutes']<=z['friction_equivalent_minutes']+1e-6
   assert a['walking_minutes']>=z['walking_minutes']-1e-6
   row={'GEOID20':id,'category':category,'destination':str(dest['name']),'routes_differ':a['edge_indices']!=z['edge_indices'],'access_verified':False}
   for label,metrics in [('friction_route',a),('fastest_same_destination',z)]:row.update({label+'_'+k:v for k,v in metrics.items() if k!='edge_indices'})
   rows.append(row)
  print('Benchmarked block routes:',id,flush=True)
 t=pd.DataFrame(rows);t.to_csv(OUT/'route_benchmark_city.csv',index=False)
 report={'sample':'Six distinct housing-positive, <=100m-snap blocks: lowest/highest essential cost and north/south/east/west extremes; three essential categories each. Same destination for both route objectives.',
 'pairs':len(t),'different_routes':int(t.routes_differ.sum()),'weighted_objective_checks_passed':True,'mean_extra_actual_walk_minutes':float((t.friction_route_walking_minutes-t.fastest_same_destination_walking_minutes).mean()),
 'pairs_with_less_busy_road_length':int((t.friction_route_busy_road_length_m<t.fastest_same_destination_busy_road_length_m-1e-6).sum()),
 'interpretation':'Model optimization and exposure-proxy comparison, not a human preference accuracy test or a guarantee of access. The sample is small and not representative of all households.'}
 (OUT/'route_benchmark_city_method.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
