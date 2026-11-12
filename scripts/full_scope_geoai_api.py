"""Windowed NAIP retrieval through the documented Planetary Computer Data API.
Retains 60 cm georeferencing and date; pipelines retrieval with native MPS inference.
"""
from pathlib import Path
import json,io,subprocess,concurrent.futures,time
import full_scope_geoai as base
import imagery_geoai_demo as demo
import numpy as np,geopandas as gpd,rasterio,requests
from PIL import Image
from rasterio.transform import from_origin
from rasterio.windows import Window,transform as window_transform
from rasterio.features import geometry_mask
from shapely.geometry import shape,box,mapping
ROOT=base.ROOT;OUT=base.OUT

def run():
 cfg=base.plan();study=base.scope().geometry.union_all();region=study.buffer(80)
 ll=gpd.GeoSeries([region],crs=26914).to_crs(4326).iloc[0]
 query={'collections':'naip','bbox':','.join(map(str,ll.bounds)),'datetime':'2022-01-01T00:00:00Z/2022-12-31T23:59:59Z','limit':100}
 inventory=demo.get_json('https://planetarycomputer.microsoft.com/api/stac/v1/search',params=query)
 if any(l['rel']=='next' for l in inventory.get('links',[])):raise RuntimeError('Inventory requires pagination')
 items=[x for x in inventory['features'] if shape(x['geometry']).intersects(ll)]
 for item in items:item['_footprint']=gpd.GeoSeries([shape(item['geometry'])],crs=4326).to_crs(26914).iloc[0]
 if region.difference(gpd.GeoSeries([x['_footprint'] for x in items],crs=26914).union_all()).area>1:raise RuntimeError('Source footprint gap')
 manifest=[{'id':x['id'],'date':x['properties']['datetime'],'native_resolution_m':x['properties']['gsd'],'source_url':x['assets']['image']['href'],'source':'USDA NAIP, Microsoft Planetary Computer Data API bounding-box crop, no color stretch'} for x in items]
 (OUT/'imagery_sources.json').write_text(json.dumps(manifest,indent=2))
 inputs=OUT/'inputs';inputs.mkdir(exist_ok=True);tiles=OUT/'tiles';tiles.mkdir(exist_ok=True);work=OUT/'work';work.mkdir(exist_ok=True)
 global_tf=from_origin(cfg['transform'][2],cfg['transform'][5],base.RES,base.RES)
 def fetch(tile):
  path=inputs/(tile['id']+'.tif')
  if path.exists():return tile,path
  win=Window(tile['col']-base.HALO,tile['row']-base.HALO,tile['width']+2*base.HALO,tile['height']+2*base.HALO)
  tf=window_transform(win,global_tf);h=int(win.height);w=int(win.width)
  bounds=rasterio.windows.bounds(Window(0,0,w,h),tf);extent=box(*bounds)
  sources=[x for x in items if x['_footprint'].intersects(extent)]
  covering=[x for x in sources if x['_footprint'].covers(extent)]
  if covering:sources=covering[:1]
  rgb=np.zeros((h,w,3),dtype='uint8');valid=np.zeros((h,w),dtype=bool);used=[]
  for item in sources:
   url='https://planetarycomputer.microsoft.com/api/data/v1/item/bbox/'+','.join(f'{v:.4f}' for v in bounds)+f'/{w}x{h}.png'
   params={'collection':'naip','item':item['id'],'assets':'image','asset_bidx':'image|1,2,3','coord_crs':'EPSG:26914','dst_crs':'EPSG:26914','return_mask':'true','resampling':'nearest','reproject':'nearest'}
   for attempt in range(4):
    try:
     r=requests.get(url,params=params,timeout=120);r.raise_for_status()
     image=np.asarray(Image.open(io.BytesIO(r.content)).convert('RGBA'))
     if image.shape!=(h,w,4):raise ValueError('Unexpected imagery dimensions')
     good=image[:,:,3]>0;rgb[good]=image[good,:3];valid|=good;used.append(item['id']);break
    except Exception:
     if attempt==3:raise RuntimeError('Imagery window failed: '+tile['id']) from None
   if valid.all():break
  with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True,PROJ_DATA=demo.os.environ['PROJ_DATA']):
   temp=path.with_suffix('.part.tif')
   with rasterio.open(temp,'w',driver='GTiff',height=h,width=w,count=3,dtype='uint8',crs=26914,transform=tf,compress='deflate') as dst:dst.write(np.moveaxis(rgb,-1,0));dst.write_mask(valid.astype('uint8')*255)
   temp.replace(path)
  path.with_suffix('.json').write_text(json.dumps({'tile':tile['id'],'source_items':used,'bounds_utm14':bounds,'resolution_m':base.RES,'imagery_window_valid_fraction':float(valid.mean())},indent=2))
  return tile,path
 remaining=[t for t in cfg['tiles'] if not (tiles/(t['id']+'.tif')).exists()]
 worker_log=open(OUT/'worker.log','a')
 worker=subprocess.Popen(['/usr/bin/arch','-arm64',str(ROOT/'.venv-geoai-arm/bin/python'),str(ROOT/'scripts/geoai_native_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=worker_log,text=True,bufsize=1)
 ready=json.loads(worker.stdout.readline());completed=len(cfg['tiles'])-len(remaining)
 base.status(stage='inference',retrieval='Planetary Computer lossless RGB window API',device=ready.get('device'),completed_tiles=completed,total_tiles=len(cfg['tiles']))
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
   pending={};iterator=iter(remaining)
   def add():
    try:t=next(iterator)
    except StopIteration:return False
    pending[pool.submit(fetch,t)]=t;return True
   for _ in range(20):add()
   while pending:
    finished,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
    for future in finished:
     pending.pop(future);tile,path=future.result();add()
     with rasterio.open(path) as src:rgb=src.read([1,2,3]);valid=src.dataset_mask()>0
     ip=work/'input.npy';op=work/'prediction.npy';np.save(ip,np.moveaxis(rgb,0,-1))
     worker.stdin.write(json.dumps({'input':str(ip),'output':str(op)})+'\n');worker.stdin.flush()
     message=worker.stdout.readline()
     if not message:raise RuntimeError('Native model worker stopped; inspect worker.log')
     result=json.loads(message)
     if not result.get('ok'):raise RuntimeError(result.get('error','Inference failed'))
     prediction=np.load(op)[:,base.HALO:base.HALO+tile['height'],base.HALO:base.HALO+tile['width']]
     tf=window_transform(Window(tile['col'],tile['row'],tile['width'],tile['height']),global_tf)
     inside=geometry_mask([mapping(study)],out_shape=(tile['height'],tile['width']),transform=tf,invert=True)
     observed=inside & valid[base.HALO:base.HALO+tile['height'],base.HALO:base.HALO+tile['width']]
     prediction[:,~observed]=255
     dest=tiles/(tile['id']+'.tif');temp=dest.with_suffix('.part.tif')
     with rasterio.open(temp,'w',driver='GTiff',height=tile['height'],width=tile['width'],count=2,dtype='uint8',crs=26914,transform=tf,nodata=255,compress='deflate',tiled=True) as dst:
      dst.write(prediction);dst.update_tags(model=demo.MODEL_ID,source='NAIP 2022, 60 cm; lossless RGB crop',class_values='0 not detected; 1 tree; 255 unknown/outside',probability_band='0–100 percent; 255 unknown/outside',device=ready.get('device'))
     temp.replace(dest);completed+=1
     base.status(stage='inference',completed_tiles=completed,total_tiles=len(cfg['tiles']))
 finally:
  worker.stdin.close();worker.wait(timeout=60);worker_log.close()
 return cfg
if __name__=='__main__':run()
