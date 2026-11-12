"""Reuse compatible existing tree classifications; infer only unfilled city tiles."""
from pathlib import Path
import os,json
import geopandas as gpd,numpy as np,rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.features import geometry_mask
from shapely.geometry import mapping
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city'

def run():
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
 context=gpd.GeoDataFrame({'scope':['Plano + 1000 m environmental/routing context']},geometry=[city.geometry.union_all().buffer(1000)],crs=26914)
 boundary=OUT/'environment_context.gpkg';context.to_file(boundary,driver='GPKG',index=False)
 os.environ['EMPATH_SCOPE_FILE']=str(boundary);os.environ['EMPATH_GEOAI_OUTPUT']=str(OUT/'geoai')
 import full_scope_geoai as base
 cfg=base.plan();tiles=base.OUT/'tiles';tiles.mkdir(exist_ok=True)
 tf=rasterio.transform.Affine(*cfg['transform']);shape=context.geometry.iloc[0];seeded=0
 with rasterio.open(ROOT/'output/geoai_full_scope/full_scope_tree_cover.tif') as src:
  with WarpedVRT(src,crs=26914,transform=tf,width=cfg['width'],height=cfg['height'],resampling=Resampling.nearest,nodata=255) as vrt:
   for tile in cfg['tiles']:
    p=tiles/(tile['id']+'.tif')
    if p.exists():continue
    win=Window(tile['col'],tile['row'],tile['width'],tile['height']);local=vrt.window_transform(win)
    inside=geometry_mask([mapping(shape)],out_shape=(tile['height'],tile['width']),transform=local,invert=True)
    arr=vrt.read(1,window=win)
    if inside.any() and np.all(arr[inside]!=255):
     arr[~inside]=255
     with rasterio.open(p,'w',driver='GTiff',width=tile['width'],height=tile['height'],count=2,dtype='uint8',crs=26914,transform=local,nodata=255,compress='deflate',tiled=True) as dst:
      dst.write(arr,1);dst.write(np.full(arr.shape,255,dtype='uint8'),2);dst.update_tags(source='Reused actual 2022 NAIP Restor TCD class predictions from four-ZIP run',probability_band='Unknown: class-only cached mosaic; 255, not synthetic probability')
     seeded+=1
 report={'scope':'Plano + 1000 m context','planned_tiles':len(cfg['tiles']),'reused_prediction_tiles':seeded,'prediction_source':'Same cached TCD model, 2022 NAIP, 0.6 m. Missing probability is marked unknown, never manufactured.'}
 (base.OUT/'bootstrap_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 import full_scope_geoai_api as inference
 return inference.run()
if __name__=='__main__':run()
