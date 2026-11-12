"""Matched-network sensitivity of residential block recommendations, not preference accuracy."""
from pathlib import Path
import json,time
import numpy as np,pandas as pd,networkx as nx
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility'

def run():
 b=pd.read_csv(OUT/'block_accessibility.csv',dtype={'GEOID20':str});p=pd.read_csv(OUT/'accessibility_pois.csv')
 d=pd.read_csv(ROOT/'output/plano_city/friction/block_proxy_edge_costs.csv');d=d[d.block_proxy_cost_s.notna()]
 features=d[['block_canopy_deficit_01','block_traffic_burden_01','block_heat_burden_01']].to_numpy();time_s=d['length'].to_numpy()/1.2
 scenarios={'equal':[1/3,1/3,1/3],'canopy_priority':[.6,.2,.2],'traffic_priority':[.2,.6,.2],'heat_priority':[.2,.2,.6]}
 eligible=(pd.to_numeric(b.HU100,errors='coerce')>0)&b.access_snap_gap_m.le(100)&b.access_essential_mean_equiv_min.notna()
 table=b[['GEOID20','access_network_node','HU100','access_snap_gap_m']].copy();report={'profile':['hindu_temple','supermarket','pharmacy'],'eligible_housing_blocks':int(eligible.sum()),'scenarios':{}}
 for name,weights in scenarios.items():
  graph=nx.DiGraph();costs=time_s*(1+features@np.array(weights))
  for row,cost in zip(d.itertuples(),costs):
   u,v=int(row.u),int(row.v)
   if not graph.has_edge(u,v) or cost<graph[u][v]['weight']:graph.add_edge(u,v,weight=float(cost))
  reverse=graph.reverse(copy=False);columns=[]
  for category in report['profile']:
   targets=p.loc[p.category.eq(category),'network_node'].astype(int).unique().tolist()
   distances=nx.multi_source_dijkstra_path_length(reverse,targets,weight='weight')
   columns.append(b.access_network_node.map(distances).to_numpy()/60)
  values=np.column_stack(columns);mean=np.mean(values,axis=1);table[name+'_mean_equiv_min']=mean
  baseline=b.access_essential_mean_equiv_min.to_numpy();valid=eligible&np.isfinite(mean)
  if name=='equal':assert np.allclose(mean,baseline,equal_nan=True)
  ranks=pd.Series(mean).rank(method='min');base_ranks=pd.Series(baseline).rank(method='min')
  current=set(b.loc[valid].assign(cost=mean[valid]).nsmallest(20,'cost').GEOID20)
  original=set(b.loc[valid].nsmallest(20,'access_essential_mean_equiv_min').GEOID20)
  report['scenarios'][name]={'factor_weights_canopy_traffic_heat':weights,'eligible_complete_blocks':int(valid.sum()),'spearman_vs_equal':float(pd.Series(mean[valid]).rank().corr(pd.Series(baseline[valid]).rank())),
   'top20_overlap_with_equal':len(current&original),'median_cost_equiv_min':float(np.median(mean[valid]))}
  print('Sensitivity evaluated:',name,flush=True)
 baseline=b.access_essential_baseline_mean_walk_min;friction=b.access_essential_mean_equiv_min
 top_time=set(b.loc[eligible].nsmallest(20,'access_essential_baseline_mean_walk_min').GEOID20);top_friction=set(b.loc[eligible].nsmallest(20,'access_essential_mean_equiv_min').GEOID20)
 report['time_only_vs_friction_residential']={'spearman':float(friction[eligible].rank().corr(baseline[eligible].rank())),'top20_overlap':len(top_time&top_friction),'matched_network':True}
 report['interpretation']='Stability is not local preference accuracy. Strong time/friction correlation indicates distance is a major driver under the bounded 1–2× cost multiplier. Manual entrance, crossing and route-condition review remains necessary.'
 table.to_csv(OUT/'residential_sensitivity.csv',index=False);(OUT/'evaluation_sensitivity.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
