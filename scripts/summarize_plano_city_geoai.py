"""Mosaic city tree predictions and aggregate to context blocks, preserving coverage."""
from pathlib import Path
import json
import imagery_geoai_demo  # Rasterio-compatible PROJ database.
import geopandas as gpd,pandas as pd,numpy as np,rasterio
from rasterio.windows import Window
from rasterio.features import rasterize
from rasterio.transform import Affine
from shapely.geometry import box
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city';AI=OUT/'geoai'

def run():
 cfg=json.load(open(AI/'tile_plan.json'));blocks=gpd.read_file(OUT/'block_context_base.gpkg').to_crs(26914).reset_index(drop=True)
 valid_count=np.zeros(len(blocks),dtype=np.int64);tree_count=valid_count.copy();expected=valid_count.copy()
 tf=Affine(*cfg['transform']);mosaic=AI/'city_tree_cover.tif'
 with rasterio.open(mosaic,'w',driver='GTiff',width=cfg['width'],height=cfg['height'],count=1,dtype='uint8',crs=26914,transform=tf,nodata=255,compress='deflate',tiled=True,BIGTIFF='IF_SAFER') as dst:
  for row in range(0,cfg['height'],512):
   h=min(512,cfg['height']-row);dst.write(np.full((h,cfg['width']),255,dtype='uint8'),1,window=Window(0,row,cfg['width'],h))
  for i,tile in enumerate(cfg['tiles']):
   path=AI/'tiles'/(tile['id']+'.tif')
   if not path.exists():raise RuntimeError('Missing inference tile: '+tile['id'])
   with rasterio.open(path) as src:
    a=src.read(1);valid=a!=255;dst.write(a,1,window=Window(tile['col'],tile['row'],tile['width'],tile['height']))
    ids=blocks.sindex.query(box(*src.bounds),predicate='intersects')
    if len(ids):
     labels=rasterize([(blocks.geometry.iloc[k],int(k)+1) for k in ids],out_shape=a.shape,transform=src.transform,fill=0,dtype='int32')
     expected+=np.bincount(labels.ravel(),minlength=len(blocks)+1)[1:]
     valid_count+=np.bincount(labels[valid],minlength=len(blocks)+1)[1:]
     tree_count+=np.bincount(labels[a==1],minlength=len(blocks)+1)[1:]
   if (i+1)%100==0:print('Summarized city GeoAI tiles:',i+1,'/',len(cfg['tiles']),flush=True)
  dst.update_tags(model='restor/tcd-segformer-mit-b0',source='2022 USDA NAIP; reused compatible pilot class predictions plus new inference',classes='0 no tree, 1 predicted tree, 255 unknown; not actual shade')
 blocks['ai_canopy_cover_pct']=np.divide(tree_count*100,valid_count,out=np.full(len(blocks),np.nan),where=valid_count>0)
 blocks['ai_imagery_coverage_01']=np.divide(valid_count,expected,out=np.full(len(blocks),np.nan),where=expected>0)
 heat=gpd.read_file(OUT/'heat/block_environment_with_heat.gpkg')
 cols=['GEOID20']+[c for c in heat if c.startswith('landsat_')]
 heat['GEOID20']=heat.GEOID20.astype(str);blocks=blocks.merge(heat[cols],on='GEOID20',validate='one_to_one')
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_reference_blocks.gpkg').to_crs(26914)
 city_ids=set(city.GEOID20.astype(str));reference=blocks.loc[blocks.GEOID20.isin(city_ids),'landsat_summer_surface_temp_c'];lo,hi=reference.min(),reference.max()
 blocks['temperature_burden_01']=((blocks.landsat_summer_surface_temp_c-lo)/(hi-lo)).clip(0,1)
 blocks.to_file(OUT/'block_environment_context.gpkg',driver='GPKG',index=False)
 attributes=blocks.drop(columns=['geometry']);city['GEOID20']=city.GEOID20.astype(str)
 # Official city-clipped geometries define origins; environmental estimates retain declared block context.
 overlapping=[c for c in attributes if c!='GEOID20' and c in city]
 city=city.drop(columns=overlapping).merge(attributes,on='GEOID20',how='left',validate='one_to_one')
 city.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
 report={'scope':'Official Plano city, plus 1000 m environmental context','city_blocks':len(city),'context_blocks':len(blocks),'planned_and_summarized_tiles':len(cfg['tiles']),
 'city_blocks_with_canopy':int(city.ai_canopy_cover_pct.notna().sum()),'city_blocks_with_temperature':int(city.landsat_summer_surface_temp_c.notna().sum()),
 'observed_class_pixels':int(valid_count.sum()),'expected_block_pixels':int(expected.sum()),'context_pixel_coverage_fraction':float(valid_count.sum()/expected.sum()),
 'heat_reference':'Min-max of valid block temperature summaries for city block IDs; outside context clipped to 0–1 using same city reference','temperature_min_c':float(lo),'temperature_max_c':float(hi),
 'traffic_reference':'Existing official Plano city reference, unchanged','canopy_source':'Restor TCD pretrained segmentation, 2022 NAIP 0.6 m; cached pilot and fresh city-context predictions',
 'limitations':'Tree cover is not measured shade; block context can smooth trail conditions. Block estimates may include portions outside the city inside the routing buffer; origin geometry is clipped to official city limits.'}
 (OUT/'environment_coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
