"""Resumable 2022 NAIP tree-cover inference covering all four pilot ZCTAs.
Predictions are kept separate from the production graph and published canopy.
"""
from pathlib import Path
import sys,os,json,time,subprocess,concurrent.futures,math
import imagery_geoai_demo as demo
import numpy as np,pandas as pd,geopandas as gpd,rasterio,requests
from rasterio.windows import Window,from_bounds,transform as window_transform
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.features import geometry_mask,rasterize,shapes
from shapely.geometry import box,shape,mapping
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/geoai_full_scope';CRS=26914
RES=.6;CORE=896;HALO=64

def status(**kwargs):
 OUT.mkdir(parents=True,exist_ok=True)
 p=OUT/'progress.json';current=json.loads(p.read_text()) if p.exists() else {}
 current.update(kwargs);current['updated_unix']=time.time()
 temp=p.with_suffix('.tmp');temp.write_text(json.dumps(current,indent=2));temp.replace(p)
 print(json.dumps(kwargs),flush=True)

def scope():return gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(CRS)

def acquire_sources():
 OUT.mkdir(exist_ok=True,parents=True);folder=OUT/'imagery';folder.mkdir(exist_ok=True)
 s=scope();region=s.geometry.union_all().buffer(80);ll=gpd.GeoSeries([region],crs=CRS).to_crs(4326).iloc[0]
 manifest=folder/'manifest.json'
 if manifest.exists():return json.loads(manifest.read_text())
 query={'collections':'naip','bbox':','.join(map(str,ll.bounds)),'datetime':'2022-01-01T00:00:00Z/2022-12-31T23:59:59Z','limit':100}
 j=demo.get_json('https://planetarycomputer.microsoft.com/api/stac/v1/search',params=query)
 if any(x['rel']=='next' for x in j.get('links',[])):raise RuntimeError('Unexpected additional STAC page; do not silently truncate imagery inventory')
 items=[f for f in j['features'] if shape(f['geometry']).intersects(ll)]
 footprints=gpd.GeoSeries([shape(f['geometry']) for f in items],crs=4326).to_crs(CRS)
 cover=footprints.union_all()
 if region.difference(cover).area>1:raise RuntimeError('Source footprints do not cover requested buffered study area')
 status(stage='acquiring_imagery',source_scene_count=len(items),source_year=2022,scope_area_km2=float(s.area.sum()/1e6))
 def one(item):
  ident=item['id'];path=folder/(ident+'.tif');meta=path.with_suffix('.json')
  if path.exists() and meta.exists():return json.loads(meta.read_text())
  footprint=gpd.GeoSeries([shape(item['geometry'])],crs=4326).to_crs(CRS).iloc[0]
  area=region.intersection(footprint);bounds=area.bounds
  href=item['assets']['image']['href']
  for attempt in range(3):
   try:
    signed=demo.get_json('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':href})['href']
    with rasterio.open(signed) as src:
     if src.crs.to_epsg()!=CRS:raise RuntimeError('Unexpected source CRS')
     w=from_bounds(*bounds,src.transform)
     col=max(0,math.floor(w.col_off));row=max(0,math.floor(w.row_off))
     width=min(src.width-col,math.ceil(w.col_off+w.width)-col);height=min(src.height-row,math.ceil(w.row_off+w.height)-row)
     win=Window(col,row,width,height);data=src.read([1,2,3],window=win,masked=True)
     profile=src.profile.copy();profile.update(driver='GTiff',count=3,width=width,height=height,transform=src.window_transform(win),compress='deflate',tiled=True,blockxsize=512,blockysize=512,nodata=0)
     tmp=path.with_suffix('.part.tif')
     with rasterio.open(tmp,'w',**profile) as dst:dst.write(data.filled(0));dst.write_mask((~np.ma.getmaskarray(data).any(axis=0)).astype('uint8')*255)
     tmp.replace(path)
    rec={'id':ident,'path':str(path.relative_to(ROOT)),'date':item['properties']['datetime'],'source_url':href,'resolution_m':item['properties']['gsd'],'source':'USDA NAIP via Microsoft Planetary Computer','footprint':mapping(footprint)}
    meta.write_text(json.dumps(rec,indent=2));return rec
   except Exception:
    if attempt==2:raise RuntimeError('Imagery acquisition failed for '+ident+'; rerun to resume') from None
  raise RuntimeError('Acquisition did not complete')
 records=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for rec in pool.map(one,items):
   records.append(rec);status(stage='acquiring_imagery',source_scenes_completed=len(records))
 manifest.write_text(json.dumps(records,indent=2));return records

def plan():
 s=scope();region=s.geometry.union_all();xmin,ymin,xmax,ymax=region.bounds
 left=math.floor(xmin/RES)*RES;top=math.ceil(ymax/RES)*RES
 width=math.ceil((xmax-left)/RES);height=math.ceil((top-ymin)/RES);transform=from_origin(left,top,RES,RES)
 tiles=[]
 for row in range(0,height,CORE):
  for col in range(0,width,CORE):
   w=min(CORE,width-col);h=min(CORE,height-row);bounds=rasterio.windows.bounds(Window(col,row,w,h),transform)
   if region.intersection(box(*bounds)).area>0:tiles.append({'id':f'r{row:05d}_c{col:05d}','row':row,'col':col,'width':w,'height':h})
 cfg={'resolution_m':RES,'core_pixels':CORE,'halo_pixels':HALO,'width':width,'height':height,'transform':list(transform)[:6],'tiles':tiles,'model':'restor/tcd-segformer-mit-b0','year':2022,'scope_zips':['75023','75024','75025','75074']}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'tile_plan.json').write_text(json.dumps(cfg,indent=2));return cfg

def infer():
 records=acquire_sources();cfg=plan();s=scope();region=s.geometry.union_all()
 tiles=OUT/'tiles';tiles.mkdir(exist_ok=True);work=OUT/'work';work.mkdir(exist_ok=True)
 python=ROOT/'.venv-geoai-arm/bin/python'
 if not python.exists():raise RuntimeError('Install native worker dependencies described in Notebook 14')
 stderr=open(OUT/'worker.log','a')
 worker=subprocess.Popen(['/usr/bin/arch','-arm64',str(python),str(ROOT/'scripts/geoai_native_worker.py')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1)
 ready=json.loads(worker.stdout.readline());status(stage='inference',device=ready.get('device'),total_tiles=len(cfg['tiles']))
 datasets=[]
 try:
  transform=from_origin(cfg['transform'][2],cfg['transform'][5],RES,RES)
  for r in records:
   src=rasterio.open(ROOT/r['path']);datasets.append(src)
  for i,tile in enumerate(cfg['tiles']):
   dest=tiles/(tile['id']+'.tif')
   if dest.exists():continue
   inputwin=Window(tile['col']-HALO,tile['row']-HALO,tile['width']+2*HALO,tile['height']+2*HALO)
   tf=window_transform(inputwin,transform);h=int(inputwin.height);w=int(inputwin.width)
   bounds=rasterio.windows.bounds(Window(0,0,w,h),tf)
   rgb=np.zeros((3,h,w),dtype=np.uint8);valid=np.zeros((h,w),dtype=bool)
   for src in datasets:
    if not box(*src.bounds).intersects(box(*bounds)):continue
    with WarpedVRT(src,crs=CRS,transform=tf,width=w,height=h,resampling=Resampling.bilinear,nodata=0) as vrt:
     arr=vrt.read([1,2,3],masked=True);ok=~np.ma.getmaskarray(arr).any(axis=0)
     rgb[:,ok]=arr.data[:,ok];valid|=ok
   input_path=work/'input.npy';output_path=work/'prediction.npy'
   np.save(input_path,np.moveaxis(rgb,0,-1))
   worker.stdin.write(json.dumps({'input':str(input_path),'output':str(output_path)})+'\n');worker.stdin.flush()
   response=worker.stdout.readline()
   if not response:raise RuntimeError('Inference worker stopped; inspect worker.log')
   result=json.loads(response)
   if not result.get('ok'):raise RuntimeError('Inference error: '+result.get('error','unknown'))
   predicted=np.load(output_path)[:,HALO:HALO+tile['height'],HALO:HALO+tile['width']]
   core_tf=window_transform(Window(tile['col'],tile['row'],tile['width'],tile['height']),transform)
   in_scope=geometry_mask([mapping(region)],out_shape=(tile['height'],tile['width']),transform=core_tf,invert=True)
   observed=valid[HALO:HALO+tile['height'],HALO:HALO+tile['width']] & in_scope
   predicted[:,~observed]=255
   tmp=dest.with_suffix('.part.tif')
   with rasterio.open(tmp,'w',driver='GTiff',width=tile['width'],height=tile['height'],count=2,dtype='uint8',crs=CRS,transform=core_tf,nodata=255,compress='deflate',tiled=True) as dst:
    dst.write(predicted);dst.update_tags(model=demo.MODEL_ID,band_1='predicted tree class: 0/1; 255 unknown/outside',band_2='tree probability percent: 0–100; 255 unknown/outside',note='not measured shade; local accuracy unvalidated')
   tmp.replace(dest)
   status(stage='inference',completed_tiles=sum((tiles/(x['id']+'.tif')).exists() for x in cfg['tiles']),total_tiles=len(cfg['tiles']))
 finally:
  for src in datasets:src.close()
  worker.stdin.close();worker.wait(timeout=60);stderr.close()
 return cfg

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--acquire-only',action='store_true');parser.add_argument('--plan-only',action='store_true');a=parser.parse_args()
 if a.plan_only:print(json.dumps({k:v for k,v in plan().items() if k!='tiles'},indent=2))
 elif a.acquire_only:acquire_sources()
 else:infer()
