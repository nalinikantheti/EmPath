"""Weighted full network and nearest-POI-per-category census-block accessibility."""
from pathlib import Path
import json,gzip
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/block_accessibility'


def annotate_block_nodes(activity, blocks):
 for r in blocks.itertuples():
  node=activity.nodes['block_'+str(r.GEOID20)]
  node['snap_gap_m']=float(r.access_snap_gap_m)
  node['connection_needs_review']=bool(r.access_connection_needs_review)
  node['score_complete']=bool(pd.notna(r.access_all_categories_mean_equiv_min))
  node['categories_reached']=int(r.access_all_categories_reached_categories)
  if node['score_complete']:
   node['weight']=float(r.access_all_categories_mean_equiv_min)
   node['relative_burden_0_100']=float(r.access_all_categories_burden_0_100)
   node['combined_category_cost_equiv_min']=float(r.access_all_categories_sum_equiv_min)


def run():
 OUT.mkdir(parents=True,exist_ok=True)
 costs=pd.read_csv(ROOT/'output/step3_friction/block_proxy_edge_costs.csv')
 raw_nodes=pd.read_csv(ROOT/'output/four_zip_walking_network/nodes.csv')
 nodes=gpd.GeoDataFrame(raw_nodes[['osmid']],geometry=gpd.points_from_xy(raw_nodes.x,raw_nodes.y),crs=4326).to_crs(26914)
 tree=cKDTree(np.c_[nodes.geometry.x,nodes.geometry.y])
 blocks=gpd.read_file(ROOT/'output/geoai_full_scope/ai_block_environment.gpkg').to_crs(26914)
 blocks['GEOID20']=blocks.GEOID20.astype(str)
 origin_points=blocks.geometry.representative_point()
 gaps,idx=tree.query(np.c_[origin_points.x,origin_points.y]);blocks['access_network_node']=nodes.osmid.to_numpy()[idx];blocks['access_snap_gap_m']=gaps
 blocks['access_connection_needs_review']=gaps>100
 blocks['access_origin_method']='Block interior representative point snapped to nearest junction; not verified entrance'
 pois=gpd.read_file(ROOT/'output/four_zip_walking_network/places_of_interest.geojson').to_crs(26914)
 pois.geometry=pois.geometry.representative_point();pois['poi_id']='osm_'+pois.osm_element.astype(str)+'_'+pois.osm_id.astype(str)
 pois['source_url']='https://www.openstreetmap.org/'+pois.osm_element.astype(str)+'/'+pois.osm_id.astype(str)
 pois['address_status']='OSM mapped candidate; entrance unverified'
 addresses=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/address_points.gpkg').to_crs(26914)
 additions=[]
 for i,t in enumerate(json.loads((ROOT/'config/accessibility_temples.json').read_text())):
  match=addresses[addresses.address.str.upper().eq(t['address'])]
  if match.empty:raise ValueError('Municipal address match missing: '+t['name'])
  match=match.sort_values('source_id');r=match.iloc[0]
  additions.append({**t,'poi_id':f'temple_{i}','category':'hindu_temple','geometry':r.geometry})
 pois=gpd.GeoDataFrame(pd.concat([pois,gpd.GeoDataFrame(additions,crs=26914)],ignore_index=True),crs=26914)
 extra_file=ROOT/'config/additional_category_pois.geojson'
 if not extra_file.exists():extra_file=OUT/'additional_category_pois.geojson'
 if extra_file.exists():
  extra=gpd.read_file(extra_file).to_crs(26914)
  pois=gpd.GeoDataFrame(pd.concat([pois,extra],ignore_index=True),crs=26914)
 pois['name']=pois['name'].fillna('Unnamed mapped feature')
 pgap,pidx=tree.query(np.c_[pois.geometry.x,pois.geometry.y]);pois['network_node']=nodes.osmid.to_numpy()[pidx];pois['snap_gap_m']=pgap
 graph=nx.MultiDiGraph(crs='EPSG:4326',weight_units='equivalent_seconds',cost_method='block proxy, equal factor weights, lambda=1, walking speed 1.2 m/s')
 for r in raw_nodes.itertuples():graph.add_node(int(r.osmid),x=float(r.x),y=float(r.y))
 valid=costs.block_proxy_cost_s.notna()
 for r in costs[valid].itertuples():graph.add_edge(int(r.u),int(r.v),key=int(r.key),weight=float(r.block_proxy_cost_s),length_m=float(r.length),walk_seconds=float(r.length)/1.2,nearby_block_proxy=bool(r.block_proxy_nearby_used))
 # Missing weights must not fall through to NetworkX's default weight of 1.
 assert graph.number_of_edges()==int(valid.sum())
 target=OUT/'weighted_walking_graph.graphml.gz'
 with gzip.open(target,'wb') as f:nx.write_graphml(graph,f)
 reverse=graph.reverse(copy=False)
 details=[];activity=nx.DiGraph(weight_units='equivalent_minutes',rule='origin to nearest reachable candidate per category only')
 for r in pois.itertuples():activity.add_node(str(r.poi_id),role='destination',category=str(r.category),label=str(r.name))
 for r in blocks.itertuples():activity.add_node('block_'+str(r.GEOID20),role='origin',label=str(r.GEOID20),network_node=int(r.access_network_node))
 categories=sorted(pois.category.unique());validation=[]
 for category in categories:
  targets=pois[pois.category.eq(category)].sort_values('poi_id')
  representatives=targets.drop_duplicates('network_node').set_index('network_node')
  lengths,paths=nx.multi_source_dijkstra(reverse,sources=representatives.index.astype(int).tolist(),weight='weight')
  for k,r in enumerate(blocks.itertuples()):
   n=int(r.access_network_node);value=lengths.get(n);poi_id=None;name=None
   if value is not None:
    winner=representatives.loc[paths[n][0]];poi_id=str(winner.poi_id);name=str(winner['name'])
    activity.add_edge('block_'+str(r.GEOID20),poi_id,weight=float(value)/60,category=str(category),access_verified=False)
    if k in [0,len(blocks)//2] and category in ['pharmacy','supermarket','hindu_temple']:
     check=nx.shortest_path_length(graph,n,int(winner.network_node) if 'network_node' in winner else int(paths[n][0]),weight='weight')
     assert np.isclose(check,value);validation.append(True)
   details.append({'GEOID20':str(r.GEOID20),'category':category,'closest_poi_id':poi_id,'closest_poi_name':name,'min_friction_equivalent_minutes':None if value is None else float(value)/60,'reachable':value is not None,'origin_snap_gap_m':float(r.access_snap_gap_m),'destination_snap_gap_m':None if value is None else float(winner.snap_gap_m)})
  print('Scored category:',category,flush=True)
 table=pd.DataFrame(details);table.to_csv(OUT/'nearest_category_costs.csv',index=False)
 pivot=table.pivot(index='GEOID20',columns='category',values='min_friction_equivalent_minutes')
 scale_parameters={}
 for profile,selected in [('all_categories',categories),('essential',['hindu_temple','supermarket','pharmacy'])]:
  values=pivot[selected]
  count=values.notna().sum(axis=1);complete=count.eq(len(selected))
  total=values.sum(axis=1,min_count=len(selected));mean=total/len(selected)
  lo,hi=mean.dropna().quantile([.02,.98]).tolist() if mean.notna().any() else (np.nan,np.nan)
  scale_parameters[profile]={'mean_cost_equiv_min_at_2nd_percentile':float(lo),'mean_cost_equiv_min_at_98th_percentile':float(hi)}
  score=100*((mean-lo)/(hi-lo)).clip(0,1) if hi>lo else mean*0
  summary=pd.DataFrame({'GEOID20':pivot.index,f'access_{profile}_reached_categories':count,f'access_{profile}_total_categories':len(selected),f'access_{profile}_sum_equiv_min':total,f'access_{profile}_mean_equiv_min':mean,f'access_{profile}_worst_equiv_min':values.max(axis=1).where(complete),f'access_{profile}_burden_0_100':score}).reset_index(drop=True)
  blocks=blocks.merge(summary,on='GEOID20',validate='one_to_one')
  print(profile,'complete blocks',int(complete.sum()),'of',len(blocks),flush=True)
 annotate_block_nodes(activity,blocks)
 nx.write_graphml(activity,OUT/'block_nearest_category_activity_graph.graphml')
 blocks.to_file(OUT/'block_accessibility.gpkg',driver='GPKG',index=False)
 blocks.drop(columns='geometry').to_csv(OUT/'block_accessibility.csv',index=False)
 pois.to_file(OUT/'accessibility_pois.gpkg',driver='GPKG',index=False)
 pois.drop(columns='geometry').to_csv(OUT/'accessibility_pois.csv',index=False)
 method={'edge_formula':'w_e = length_m / 1.2 * [1 + (block canopy deficit + block traffic burden + block heat burden)/3]',
 'nearest_category':'C_k(b) = min over destinations d in category k of weighted shortest-path cost from snapped block reference node to snapped destination node',
 'aggregate':'A(b) = sum_k C_k(b) / number_of_categories; all selected categories must be reachable. Sum and worst trip are also exported. Equal category weights are assumptions.',
 'profiles':{'all_categories':categories,'essential':['hindu_temple','supermarket','pharmacy']},
 'color_only':'0–100 display uses 2nd–98th percentile stretch of complete-block mean costs within the four-ZIP pilot, clipped at extremes. Blue=lower burden; red=higher. Raw costs remain equivalent minutes.',
 'color_scale_parameters':scale_parameters,
 'weighted_edges':int(valid.sum()),'excluded_unknown_edges':int((~valid).sum()),'blocks':len(blocks),'pois':len(pois),'temple_candidates':len(additions),
 'missing':'Any unreachable selected category means unknown overall score; not zero and not average of only reachable services.',
 'snapping':'Block representative points and POI mapped positions snap to nearest original graph junction. Connector gaps are reported; >100 m flagged. Access/entrances not verified and gap travel/crossing waits omitted.',
 'inventory':'All 2,862 blocks scored as geographic reference nodes, including nonresidential land. Address counts do not establish residential use. POI catalog is incomplete and confined to pilot; boundary effects can inflate costs.',
 'temples':'Five curated Hindu temple address candidates matched to Plano address points. Sources in config/accessibility_temples.json. Raghunath street address is directory-sourced and needs review; other addresses matched official websites. Parcel points are not entrances. Catalog is not all religions or all temples.',
 'graph':'Detailed graph has finite weights only. Activity graph contains one edge per block to the nearest reachable POI in each category; no block-block or POI-POI edges.',
 'validation':{'reverse_multi_source_matches_forward_dijkstra':all(validation),'spot_checks':len(validation),'no_same_role_activity_edges':all(activity.nodes[u]['role']=='origin' and activity.nodes[v]['role']=='destination' for u,v in activity.edges)}}
 (OUT/'accessibility_method.json').write_text(json.dumps(method,indent=2));return blocks,method

if __name__=='__main__':run()
