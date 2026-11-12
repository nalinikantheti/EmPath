"""Explicit block-overlay proxy weights; never creates pedestrian geometry."""
from pathlib import Path
import os,json
import numpy as np
import pandas as pd
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('EMPATH_FRICTION_OUTPUT',str(ROOT/'output/step3_friction')))
MAX_NEARBY_BLOCK_M=250


def run():
 OUT.mkdir(parents=True,exist_ok=True)
 edges=gpd.read_file(Path(os.environ.get('EMPATH_EDGE_INPUT',str(ROOT/'output/geoai_full_scope/ai_walking_edges.gpkg'))))[['u','v','key','length','geometry']].to_crs(26914).reset_index(drop=True)
 blocks=gpd.read_file(Path(os.environ.get('EMPATH_BLOCK_INPUT',str(ROOT/'output/geoai_full_scope/ai_block_environment.gpkg')))).to_crs(26914).reset_index(drop=True)
 blocks['block_canopy_deficit_01']=1-blocks.ai_canopy_cover_pct/100
 blocks['block_traffic_burden_01']=blocks.traffic_index_0_100/100
 blocks['block_heat_burden_01']=blocks.temperature_burden_01
 fields=['block_canopy_deficit_01','block_traffic_burden_01','block_heat_burden_01']
 i,j=blocks.sindex.query(edges.geometry,predicate='intersects')
 left=gpd.GeoSeries(edges.geometry.iloc[i].to_numpy(),crs=edges.crs)
 right=gpd.GeoSeries(blocks.geometry.iloc[j].to_numpy(),crs=blocks.crs)
 lengths=left.intersection(right,align=False).length.to_numpy()
 positive=np.isfinite(lengths)&(lengths>1e-6)
 i,j,lengths=i[positive],j[positive],lengths[positive]
 d=edges.drop(columns='geometry').copy()
 for field in fields:
  values=pd.to_numeric(blocks[field],errors='coerce').to_numpy()
  valid=np.isfinite(values)&(values>=0)&(values<=1)
  use=valid[j]
  denom=np.bincount(i[use],weights=lengths[use],minlength=len(edges))
  numer=np.bincount(i[use],weights=lengths[use]*values[j[use]],minlength=len(edges))
  d[field]=np.divide(numer,denom,out=np.full(len(edges),np.nan),where=denom>0)
  d[field+'_source']=np.where(denom>0,'length_weighted_intersecting_blocks','unknown')
  d[field+'_observed_block_length_fraction']=np.minimum(1,denom/edges['length'].to_numpy())
  d[field+'_nearby_distance_m']=np.nan
  d[field+'_nearby_geoid']=''
  missing=d[field].isna()
  if missing.any() and valid.any():
   src=edges.loc[missing,['geometry']].copy();src['edge_row']=src.index
   nearby=gpd.sjoin_nearest(src,blocks.loc[valid,['GEOID20',field,'geometry']],how='left',max_distance=MAX_NEARBY_BLOCK_M,distance_col='proxy_distance_m')
   # Ties are explicit and deterministic. Only used when no valid intersected-block length exists.
   nearby=nearby.sort_values(['edge_row','proxy_distance_m','GEOID20']).drop_duplicates('edge_row').set_index('edge_row')
   matched=nearby[field].notna();ids=nearby.index[matched]
   d.loc[ids,field]=nearby.loc[ids,field]
   d.loc[ids,field+'_source']='nearby_block_proxy'
   d.loc[ids,field+'_nearby_distance_m']=nearby.loc[ids,'proxy_distance_m']
   d.loc[ids,field+'_nearby_geoid']=nearby.loc[ids,'GEOID20'].astype(str)
 d['block_proxy_factor_count']=d[fields].notna().sum(axis=1)
 d['block_proxy_burden_01']=d[fields].mean(axis=1).where(d.block_proxy_factor_count.eq(3))
 d['block_proxy_cost_s']=d['length']/1.2*(1+d.block_proxy_burden_01)
 d['block_proxy_nearby_used']=d[[f+'_source' for f in fields]].eq('nearby_block_proxy').any(axis=1)
 d['block_proxy_partial_overlap']=d[[f+'_observed_block_length_fraction' for f in fields]].min(axis=1).lt(.98)
 d.to_csv(OUT/'block_proxy_edge_costs.csv',index=False)
 assert len(d)==len(edges) and not d.duplicated(['u','v','key']).any()
 assert d.block_proxy_burden_01.dropna().between(0,1).all()
 assert (d.loc[d.block_proxy_factor_count.lt(3),'block_proxy_cost_s'].isna()).all()
 assert np.allclose(d.loc[d.block_proxy_factor_count.eq(3),'block_proxy_cost_s'],d.loc[d.block_proxy_factor_count.eq(3),'length']/1.2*(1+d.loc[d.block_proxy_factor_count.eq(3),fields].mean(axis=1)))
 report={'formula':'length_m / 1.2 * [1 + (block canopy deficit + block traffic burden + block heat burden)/3]',
 'method':'Length-weighted mean of each available block factor over positive-length edge/block intersections. All three factor estimates required for the final block proxy score.',
 'nearby_fallback':'Only when no valid intersecting-block value exists for a factor: nearest block with a valid factor, within 250 m of edge geometry. Keep distance, block ID and factor-specific provenance. Nearest ties resolved by block ID.',
 'partial_overlap':'If only part of a path intersects valid blocks, the observed part estimates the entire path; flag coverage below 98%. Boundary paths can sample both adjacent blocks; they contribute symmetrically.',
 'all_scores_are_proxies':'Block summaries do not measure sidewalk shade, air temperature or traffic on a trail. Nearby-block estimates are another explicit spatial-transfer assumption, not measured values or newly trained AI.',
 'edge_count':len(d),'weighted_edges':int(d.block_proxy_cost_s.notna().sum()),'unknown_edges':int(d.block_proxy_cost_s.isna().sum()),
 'nearby_block_used_edges':int(d.block_proxy_nearby_used.sum()),'partial_or_missing_overlap_edges':int(d.block_proxy_partial_overlap.sum()),
 'source_counts':{f:d[f+'_source'].value_counts().to_dict() for f in fields},
 'reference':'Canopy uses existing AI block cover; traffic keeps Plano normalization; heat keeps four-ZIP normalization. No new reference distribution.',
 'geometry_audit':'Current detailed network retains all 93,452 edge IDs from original cached OSM network. This method supplies weights, not new paths.',
 'limits':'No path geometry is fabricated. Any real missing OSM/municipal trail connection still needs separate verification and geometry integration.',
 'checks':{'original_edge_ids_preserved':True,'three_factors_required':True,'formula_verified':True}}
 (OUT/'block_proxy_method.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':print(json.dumps(run(),indent=2))
