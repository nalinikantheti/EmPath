"""User-requested shade-priority scenario, using actual AI tree samples near edges.
Weights are stated preferences, not learned Plano comfort coefficients.
"""
from pathlib import Path
import json,shutil
import numpy as np,pandas as pd,geopandas as gpd,rasterio,shapely
from rasterio.windows import Window
ROOT=Path(__file__).resolve().parents[1];CITY=ROOT/'output/plano_city';OUT=CITY/'shade_priority';ARCHIVE=CITY/'balanced_3km'
def run():
 OUT.mkdir(exist_ok=True);ARCHIVE.mkdir(exist_ok=True)
 # Preserve the prior model and same-scope comparisons before changing production weights.
 for folder,names in [('friction',['block_proxy_edge_costs.csv','block_proxy_method.json']),('accessibility',['nearest_category_costs.csv','block_accessibility.gpkg','block_accessibility.csv','accessibility_method.json','routing_network_method.json'])]:
  (ARCHIVE/folder).mkdir(exist_ok=True)
  for name in names:
   if not (ARCHIVE/folder/name).exists():shutil.copy2(CITY/folder/name,ARCHIVE/folder/name)
 edges=gpd.read_file(CITY/'network/edges.gpkg').to_crs(26914).reset_index(drop=True)
 cache=OUT/'edge_tree_corridor_samples.csv'
 if not cache.exists():
  # Reciprocal edges share geometry. Sample each unique physical geometry once.
  keys=edges.geometry.map(lambda g:shapely.normalize(g).wkb_hex);unique=edges.loc[~keys.duplicated(),['geometry']].copy();unique['geometry_key']=keys[~keys.duplicated()].to_numpy();geoms=unique.geometry.to_numpy();lengths=shapely.length(geoms)
  counts=np.maximum(1,np.ceil(lengths/8).astype(int));ix=np.repeat(np.arange(len(geoms)),counts);starts=np.cumsum(counts)-counts;position=np.arange(int(counts.sum()))-np.repeat(starts,counts);distance=(position+.5)/counts[ix]*lengths[ix]
  p=shapely.line_interpolate_point(geoms[ix],distance);before=shapely.line_interpolate_point(geoms[ix],np.maximum(0,distance-1));after=shapely.line_interpolate_point(geoms[ix],np.minimum(lengths[ix],distance+1));dx=shapely.get_x(after)-shapely.get_x(before);dy=shapely.get_y(after)-shapely.get_y(before);norm=np.hypot(dx,dy);nx=np.divide(-dy,norm,out=np.zeros_like(dy),where=norm>0);ny=np.divide(dx,norm,out=np.zeros_like(dx),where=norm>0);x=shapely.get_x(p);y=shapely.get_y(p)
  with rasterio.open(ROOT/'output/plano_boundary_3km/geoai/city_tree_cover.tif') as src:
   offsets=np.array([-10,-6,-3,0,3,6,10]);cols=np.floor((x[None,:]+offsets[:,None]*nx-src.transform.c)/src.transform.a).astype('int32').ravel();rows=np.floor((y[None,:]+offsets[:,None]*ny-src.transform.f)/src.transform.e).astype('int32').ravel();ei=np.tile(ix,len(offsets));inside=(rows>=0)&(cols>=0)&(rows<src.height)&(cols<src.width);cols,rows,ei=cols[inside],rows[inside],ei[inside];tiles=((rows//1024)*int(np.ceil(src.width/1024))+cols//1024);order=np.argsort(tiles);tiles,cols,rows,ei=tiles[order],cols[order],rows[order],ei[order];cuts=np.r_[0,np.flatnonzero(np.diff(tiles))+1,len(tiles)];trees=np.zeros(len(unique));valid=np.zeros(len(unique));ncol=int(np.ceil(src.width/1024))
   for k,(a,b) in enumerate(zip(cuts[:-1],cuts[1:])):
    tile=int(tiles[a]);r0=(tile//ncol)*1024;c0=(tile%ncol)*1024;arr=src.read(1,window=Window(c0,r0,min(1024,src.width-c0),min(1024,src.height-r0)));v=arr[rows[a:b]-r0,cols[a:b]-c0];ok=v!=255;np.add.at(valid,ei[a:b][ok],1);np.add.at(trees,ei[a:b][ok],v[ok]==1)
    if (k+1)%200==0:print('AI corridor raster blocks sampled:',k+1,'/',len(cuts)-1,flush=True)
  fraction=np.divide(trees,valid,out=np.full(len(unique),np.nan),where=valid>0);coverage=valid/(counts*len(offsets));lookup=pd.DataFrame({'geometry_key':unique.geometry_key,'nearby_tree_cover_01':fraction,'tree_sample_coverage_01':coverage});lookup=lookup.set_index('geometry_key');sample=pd.DataFrame({'u':edges.u,'v':edges.v,'key':edges.key,'nearby_tree_cover_01':keys.map(lookup.nearby_tree_cover_01),'tree_sample_coverage_01':keys.map(lookup.tree_sample_coverage_01)});sample.to_csv(cache,index=False);print('Sampled',len(unique),'physical geometries;',len(cols),'tree queries',flush=True)
 sample=pd.read_csv(cache);cost=pd.read_csv(ARCHIVE/'friction/block_proxy_edge_costs.csv');d=cost.merge(sample,on=['u','v','key'],validate='one_to_one');fallback=d.nearby_tree_cover_01.isna();d['nearby_tree_cover_01']=d.nearby_tree_cover_01.fillna(1-d.block_canopy_deficit_01);d['tree_cover_source']=np.where(fallback,'block_canopy_fallback','sampled_AI_classification_20m_corridor');C=d.nearby_tree_cover_01.clip(0,1);H=d.block_heat_burden_01.clip(0,1);Q=d.block_traffic_burden_01.clip(0,1)
 d['balanced_cost_s']=d.block_proxy_cost_s;d['shade_priority_penalty']=6*(1-C)**2*(1+H)+Q;d['block_proxy_cost_s']=d['length']/1.2*(1+d.shade_priority_penalty);d['shade_priority_cost_s']=d.block_proxy_cost_s;assert d.block_proxy_cost_s.notna().all() and (d.block_proxy_cost_s>=d['length']/1.2-1e-8).all()
 d.to_csv(CITY/'friction/block_proxy_edge_costs.csv',index=False)
 def example(minutes,C,H,Q):return minutes*(1+6*(1-C)**2*(1+H)+Q)
 hot=example(20,.05,.9,.5);canopied=example(50,.8,.8,.1);assert canopied<hot
 method={'model':'Shade-priority stated-preference scenario','formula':'w_e = (L_e / 1.2) * [1 + 6 * (1 - C_e)^2 * (1 + H_e) + Q_e]','canopy':'C_e: sampled predicted-tree fraction in a 20 m-wide corridor, along-path sample interval <=8 m, seven cross-section offsets. Raster is actual 2022 NAIP Restor TCD class output. Tree adjacency is not measured time-specific shade.','heat':'H_e: existing 0–1 block surface-heat context, attenuated by nearby canopy deficit; not air temperature or a calibrated thermal model.','traffic':'Q_e: existing 0–1 nearby mapped traffic burden.','preference':'Coefficient 6 and square exponent intentionally prioritize tree-adjacent walks, requested by the project owner. Not learned or validated human preference/medical risk. Travel time remains additive and all weights are nonnegative.','fallback_edges':int(fallback.sum()),'partial_corridor_coverage_edges':int(d.tree_sample_coverage_01.lt(.98).sum()),'weighted_edges':len(d),'unknown_edges':int(d.block_proxy_cost_s.isna().sum()),'illustrative_50_vs_20_test':{'hot_walk_minutes':20,'hot_tree_fraction':.05,'hot_heat':.9,'hot_traffic':.5,'hot_model_equivalent_minutes':hot,'tree_adjacent_walk_minutes':50,'tree_adjacent_tree_fraction':.8,'tree_adjacent_heat':.8,'tree_adjacent_traffic':.1,'tree_adjacent_model_equivalent_minutes':canopied,'longer_tree_adjacent_route_preferred':canopied<hot,'status':'Synthetic preference test; not a measured Plano pair.'},'limits':'A stronger preference does not guarantee a route is shaded or safe. Road-centerline geometry, model transfer, entrances and crossings need validation. Unrestricted long trips can remain extent-sensitive.'}
 (CITY/'friction/block_proxy_method.json').write_text(json.dumps(method,indent=2));(OUT/'method.json').write_text(json.dumps(method,indent=2));(ROOT/'netlify_site/src/data/shade_priority_method.json').write_text(json.dumps(method,indent=2));print(json.dumps(method,indent=2))
if __name__=='__main__':run()
