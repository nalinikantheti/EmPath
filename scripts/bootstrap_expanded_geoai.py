"""Real NAIP tree inference for the 3 km routing context; reuse compatible classes."""
from pathlib import Path
import os,json
import imagery_geoai_demo
import geopandas as gpd,numpy as np,rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.features import geometry_mask
from shapely.geometry import mapping
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_boundary_3km'
def run():
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
 context=gpd.GeoDataFrame({'scope':['Plano + 3000 m environmental and routing context']},geometry=[city.geometry.union_all().buffer(3000)],crs=26914)
 (OUT/'routing_bbox.json').write_text(json.dumps(context.to_crs(4326).total_bounds.tolist()))
 scope=OUT/'environment_context.gpkg';context.to_file(scope,driver='GPKG',index=False)
 os.environ['EMPATH_SCOPE_FILE']=str(scope);os.environ['EMPATH_GEOAI_OUTPUT']=str(OUT/'geoai')
 import full_scope_geoai as base
 cfg=base.plan();tiles=base.OUT/'tiles';tiles.mkdir(exist_ok=True);tf=rasterio.transform.Affine(*cfg['transform']);shape=context.geometry.iloc[0];seeded=0
 with rasterio.open(ROOT/'output/plano_city/geoai/city_tree_cover.tif') as src:
  with WarpedVRT(src,crs=26914,transform=tf,width=cfg['width'],height=cfg['height'],resampling=Resampling.nearest,nodata=255) as vrt:
   for tile in cfg['tiles']:
    path=tiles/(tile['id']+'.tif')
    if path.exists():continue
    win=Window(tile['col'],tile['row'],tile['width'],tile['height']);local=vrt.window_transform(win);inside=geometry_mask([mapping(shape)],out_shape=(tile['height'],tile['width']),transform=local,invert=True);a=vrt.read(1,window=win)
    if inside.any() and np.all(a[inside]!=255):
     a[~inside]=255
     with rasterio.open(path,'w',driver='GTiff',width=tile['width'],height=tile['height'],count=2,dtype='uint8',crs=26914,transform=local,nodata=255,compress='deflate',tiled=True) as dst:
      dst.write(a,1);dst.write(np.full(a.shape,255,dtype='uint8'),2);dst.update_tags(source='Actual cached city NAIP TCD class predictions',probability_band='Unknown; 255, no synthetic probabilities')
     seeded+=1
 old=base.OUT/'bootstrap_report.json';prior=json.loads(old.read_text()) if old.exists() else {}
 report={'scope':'Plano + 3000 m context','planned_tiles':len(cfg['tiles']),'reused_prediction_tiles':max(seeded,prior.get('reused_prediction_tiles',0)),'source':'2022 NAIP, Restor TCD SegFormer-B0 0.6 m; reused class-only probability unknown'};old.write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 import full_scope_geoai_api as inference
 inference.run()
if __name__=='__main__':run()
