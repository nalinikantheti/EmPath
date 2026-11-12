"""Compare network distance with AI-canopy-informed proxy costs inside imagery tiles."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString,Point
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/vegetation_geoai'

def route_demo():
    edges=gpd.read_file(OUT/'ai_walking_edges.gpkg')
    beta=float(json.loads((ROOT/'output/route_preference_model/model_and_evaluation.json').read_text())['full_data_extra_sun_distance_factor'])
    summaries=[];routes=[];candidates=[]
    for zipcode,subset in edges.groupby('demo_zip'):
        subset=subset[subset.complete_corridor.astype(bool)&subset.ai_tree_cover_01.notna()].copy()
        subset['ai_proxy_cost_m']=subset['length']*(1+beta*(1-subset.ai_tree_cover_01))
        graph=nx.MultiDiGraph()
        for _,r in subset.iterrows():graph.add_edge(int(r.u),int(r.v),key=int(r.key),length=float(r['length']),ai_proxy_cost_m=float(r.ai_proxy_cost_m),geometry=r.geometry,ai_tree_cover_01=float(r.ai_tree_cover_01))
        if not graph:continue
        comp=max(nx.strongly_connected_components(graph),key=len);graph=graph.subgraph(comp).copy()
        # Fixed deterministic source: first node in largest component, not a verified home.
        source=sorted(graph.nodes)[len(graph)//2]
        lengths,paths=nx.single_source_dijkstra(graph,source,weight='length')
        costs,aipaths=nx.single_source_dijkstra(graph,source,weight='ai_proxy_cost_m')
        options=[]
        def selected(path,weight):return [min(graph[a][b].values(),key=lambda d:d[weight]) for a,b in zip(path,path[1:])]
        for target in sorted(graph.nodes):
            distance=lengths[target]
            if not 200<=distance<=1000:continue
            dpath=paths[target];apath=aipaths[target]
            de=selected(dpath,'length');ae=selected(apath,'ai_proxy_cost_m')
            basecost=sum(e['ai_proxy_cost_m'] for e in de)
            improvement=basecost-costs[target]
            candidates.append({'zip':zipcode,'origin_node':source,'destination_node':target,'distance_baseline_m':distance,'proxy_cost_improvement_m':improvement,'node_sequence_changed':dpath!=apath})
            options.append((improvement,target,de,ae,dpath,apath))
        if not options:continue
        # Explicit exploratory selection, not an unbiased validation sample.
        improvement,target,de,ae,dpath,apath=max(options,key=lambda r:(r[0],-r[1]))
        # Explicit bounded tree-adjacency objective, separate from learned distance trade-off.
        simple=nx.DiGraph()
        for a,b,data in graph.edges(data=True):
            if not simple.has_edge(a,b) or data['length']<simple[a][b]['length']:
                simple.add_edge(a,b,**data)
        tree_options=[]
        for index,path in enumerate(nx.shortest_simple_paths(simple,source,target,weight='length')):
            es=[simple[a][b] for a,b in zip(path,path[1:])]
            length=sum(e['length'] for e in es)
            if length>1.5*lengths[target]+1e-6:break
            cover=sum(e['length']*e['ai_tree_cover_01'] for e in es)/length
            tree_options.append((cover,-length,path,es))
            if index>=29:break
        cover,negative_length,tpath,te=max(tree_options,key=lambda r:(r[0],r[1]))
        for label,es,path in [('Shortest distance',de,dpath),('AI canopy proxy',ae,apath),('Tree-adjacency priority',te,tpath)]:
            length=sum(e['length'] for e in es);gap=sum(e['length']*(1-e['ai_tree_cover_01']) for e in es)
            # Contiguous edges with <10% nearby predicted tree cover; proxy only.
            longest=current=0
            for e in es:
                current=current+e['length'] if e['ai_tree_cover_01']<.1 else 0
                longest=max(longest,current)
            summaries.append({'zip':zipcode,'route':label,'origin_node':source,'destination_node':target,'distance_m':length,'mean_tree_adjacency_01':1-gap/length,'candidate_limit':30,'detour_limit_ratio':1.5,'ai_canopy_gap_proxy_m':gap,'cost_equivalent_m':length+beta*gap,'longest_low_canopy_edge_run_m':longest,'route_changed':dpath!=path,'access_verified':False})
            for i,e in enumerate(es):routes.append({'zip':zipcode,'route':label,'sequence':i,'geometry':e['geometry']})
    pd.DataFrame(summaries).to_csv(OUT/'route_comparison.csv',index=False)
    pd.DataFrame(candidates).to_csv(OUT/'all_screened_route_candidates.csv',index=False)
    if routes:gpd.GeoDataFrame(routes,crs=edges.crs).to_file(OUT/'comparison_routes.gpkg',driver='GPKG')
    (OUT/'routing_method.json').write_text(json.dumps({'beta':beta,'formula':'length_m * (1 + beta * (1 - predicted_tree_cover_within_5m_corridor))','limitations':['Canopy proximity is substituted for sun exposure; this is an unvalidated scenario, not a learned Plano heat model.','Complete imagery corridors only; tile boundary restricts the graph.','Endpoints are network-node demonstrations, not confirmed residential/service entrances.','One fixed source per tile; displayed target selected for largest cost change among 200–1000 m reachable targets. All screened targets exported. This is illustrative selection, not a validation sample.','Small changes or unchanged routes are valid outcomes; no routes forced to change.','Tree-adjacency priority maximizes length-weighted mean predicted tree fraction among up to 30 loopless distance-ordered paths within 1.5x shortest distance. It is not a global optimum over all paths and is separate from the transferred Singapore cost.','Low-canopy edge runs are not measured uninterrupted sun exposure.']},indent=2))
    return pd.DataFrame(summaries)

if __name__=='__main__':print(route_demo().to_string(index=False))
