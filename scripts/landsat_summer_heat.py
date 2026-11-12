"""Quality-screened Landsat 8/9 Collection 2 summer 2025 surface temperature.
A temporal median of clear observations, not air temperature or daily maximum heat.
"""
from pathlib import Path
import os,json,math,concurrent.futures,warnings,time
from urllib.parse import urlsplit
from datetime import datetime
from zoneinfo import ZoneInfo
import imagery_geoai_demo  # Ensure Rasterio uses its matching PROJ database.
import requests,numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds,Window
from shapely.geometry import mapping
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('EMPATH_HEAT_OUTPUT',str(ROOT/'output/landsat_heat')));NODATA=-9999.
SCOPE_FILE=Path(os.environ.get('EMPATH_HEAT_SCOPE',str(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson')))
BLOCK_FILE=Path(os.environ.get('EMPATH_HEAT_BLOCKS',str(ROOT/'output/clean_deliverables/block_environment.gpkg')))

def quality_mask(dn,qa,uncertainty,cloud_distance):
    # USGS QA_PIXEL bits 0–5: fill, dilated cloud, cirrus, cloud, shadow, snow.
    bad=(qa.astype('uint16') & 63)!=0
    cloud_conf=(qa.astype('uint16')>>8)&3
    cirrus_conf=(qa.astype('uint16')>>14)&3
    return (dn>0)&~bad&(cloud_conf<2)&(cirrus_conf<2)&(uncertainty*.01<=3)&(cloud_distance*.01>=1)

def main():
 OUT.mkdir(exist_ok=True,parents=True);cache=OUT/'scenes';cache.mkdir(exist_ok=True)
 scope=gpd.read_file(SCOPE_FILE).to_crs(26914)
 bounds=scope.total_bounds;left=math.floor(bounds[0]/30)*30;top=math.ceil(bounds[3]/30)*30
 width=math.ceil((bounds[2]-left)/30);height=math.ceil((top-bounds[1])/30);tf=from_origin(left,top,30,30)
 inside=geometry_mask([mapping(scope.geometry.union_all())],out_shape=(height,width),transform=tf,invert=True)
 inventory=OUT/'stac_search.json'
 if not inventory.exists():
  query={'collections':'landsat-c2-l2','bbox':','.join(map(str,scope.to_crs(4326).total_bounds)),'datetime':'2025-06-01T00:00:00Z/2025-08-31T23:59:59Z','limit':100}
  r=requests.get('https://planetarycomputer.microsoft.com/api/stac/v1/search',params=query,timeout=60);r.raise_for_status();inventory.write_text(json.dumps(r.json(),indent=2))
 search=json.loads(inventory.read_text())
 if any(l['rel']=='next' for l in search.get('links',[])):raise RuntimeError('More STAC pages exist; do not silently omit scenes')
 items=[f for f in search['features'] if f['properties']['platform'] in ['landsat-8','landsat-9'] and f['properties'].get('landsat:correction')=='L2SP' and f['properties'].get('landsat:collection_category')=='T1' and 'lwir11' in f['assets']]
 # One account/container SAS token, reused across assets; honor service throttling.
 token_path=OUT/'sas_cache.json'
 if token_path.exists():
  from urllib.parse import parse_qs
  from datetime import timezone
  query=json.loads(token_path.read_text())['query'];expiry=parse_qs(query).get('se',[''])[0]
  if not expiry or datetime.fromisoformat(expiry.replace('Z','+00:00'))<=datetime.now(timezone.utc):token_path.unlink()
 if token_path.exists():token=json.loads(token_path.read_text())['query']
 else:
  href=items[0]['assets']['lwir11']['href'] if False else search['features'][0]['assets']['lwir11']['href']
  for attempt in range(6):
   r=requests.get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':href},timeout=40)
   if r.status_code!=429:break
   time.sleep(min(60,int(r.headers.get('retry-after','20'))))
  r.raise_for_status();token=urlsplit(r.json()['href']).query;token_path.write_text(json.dumps({'query':token}))
 def read_band(item,name):
  href=item['assets'][name]['href'];signed=href+'?'+token
  with rasterio.Env(PROJ_DATA=imagery_geoai_demo.os.environ['PROJ_DATA'],GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT=60):
   with rasterio.open(signed) as src:
    # Align continuous temperature and QA on the same 30 m grid without invented finer detail.
    with WarpedVRT(src,crs=26914,transform=tf,width=width,height=height,resampling=Resampling.nearest,nodata=0) as vrt:return vrt.read(1)
 def process(item):
  path=cache/(item['id']+'.npz');meta=cache/(item['id']+'.json')
  if path.exists() and meta.exists():return np.load(path)['temperature_c'],json.loads(meta.read_text())
  bands={}
  for name in ['lwir11','qa_pixel','qa','cdist']:bands[name]=read_band(item,name)
  good=inside&quality_mask(bands['lwir11'],bands['qa_pixel'],bands['qa'],bands['cdist'])
  scaling=item['assets']['lwir11']['raster:bands'][0]
  assert abs(scaling['scale']-.00341802)<1e-10 and scaling['offset']==149
  temperature=bands['lwir11'].astype('float32')*scaling['scale']+scaling['offset']-273.15
  result=np.where(good,temperature,np.nan).astype('float32')
  local=datetime.fromisoformat(item['properties']['datetime'].replace('Z','+00:00')).astimezone(ZoneInfo('America/Chicago'))
  info={'scene_id':item['id'],'platform':item['properties']['platform'],'acquired_utc':item['properties']['datetime'],'acquired_local':local.isoformat(),'scene_cloud_cover_pct':item['properties'].get('eo:cloud_cover'),'pilot_valid_pixels':int(good.sum()),'pilot_valid_fraction':float(good.sum()/inside.sum()),'thermal_asset':item['assets']['lwir11']['href'],'source_doi':'10.5066/P9OGBGM6'}
  np.savez_compressed(path,temperature_c=result);meta.write_text(json.dumps(info,indent=2));return result,info
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for array,info in pool.map(process,items):
   results.append((array,info));print('Processed',info['scene_id'],'valid pilot fraction',round(info['pilot_valid_fraction'],3),flush=True)
 # Mosaic same-day observations before the temporal summary to avoid duplicate weighting.
 days={}
 for array,info in results:days.setdefault(info['acquired_local'][:10],[]).append(array)
 daily=[]
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',RuntimeWarning)
  for arrays in days.values():daily.append(np.nanmedian(np.stack(arrays),axis=0))
  stack=np.stack(daily);count=np.isfinite(stack).sum(axis=0).astype('uint16');median=np.nanmedian(stack,axis=0)
 eligible=inside&(count>=3)
 median=np.where(eligible,median,np.nan)
 profile=dict(driver='GTiff',width=width,height=height,count=1,crs=26914,transform=tf,compress='deflate')
 with rasterio.open(OUT/'summer_2025_surface_temperature_c.tif','w',dtype='float32',nodata=NODATA,**profile) as dst:
  dst.write(np.where(np.isfinite(median),median,NODATA).astype('float32'),1);dst.update_tags(units='degree Celsius',statistic='median of quality-screened acquisition-day observations, June–August 2025',note='surface temperature, not air temperature or daily maximum; 100 m native thermal resolution resampled to 30 m; minimum 3 valid dates')
 with rasterio.open(OUT/'summer_2025_valid_observation_dates.tif','w',dtype='uint16',nodata=65535,**profile) as dst:dst.write(np.where(inside,count,65535).astype('uint16'),1)
 blocks=gpd.read_file(BLOCK_FILE).to_crs(26914)
 stats=[]
 for geom in blocks.geometry:
  w=from_bounds(*geom.bounds,transform=tf);col=max(0,math.floor(w.col_off));row=max(0,math.floor(w.row_off));endcol=min(width,math.ceil(w.col_off+w.width));endrow=min(height,math.ceil(w.row_off+w.height))
  if endcol<=col or endrow<=row:stats.append((np.nan,0,0,0,np.nan,np.nan));continue
  win=Window(col,row,endcol-col,endrow-row)
  zone=geometry_mask([mapping(geom)],out_shape=(endrow-row,endcol-col),transform=rasterio.windows.transform(win,tf),invert=True)
  values=median[row:endrow,col:endcol];observations=count[row:endrow,col:endcol];good=zone&np.isfinite(values)
  stats.append((float(values[good].mean()) if good.any() else np.nan,int(good.sum()),int(zone.sum()),float(observations[good].mean()) if good.any() else np.nan,int(observations[good].min()) if good.any() else np.nan,int(observations[good].max()) if good.any() else np.nan))
 columns=['landsat_summer_surface_temp_c','landsat_valid_composite_pixels','landsat_block_pixel_centers','landsat_mean_valid_dates','landsat_min_valid_dates','landsat_max_valid_dates']
 for i,name in enumerate(columns):blocks[name]=[s[i] for s in stats]
 blocks['landsat_valid_pixel_fraction']=np.divide(blocks.landsat_valid_composite_pixels,blocks.landsat_block_pixel_centers,out=np.full(len(blocks),np.nan),where=blocks.landsat_block_pixel_centers>0)
 blocks['landsat_summary_period']='June–August 2025; satellite acquisition times; not daily maximum'
 blocks.to_file(OUT/'block_environment_with_heat.gpkg',driver='GPKG',index=False)
 blocks.drop(columns='geometry').to_csv(OUT/'block_environment_with_heat.csv',index=False)
 joincols=['GEOID20']+[c for c in blocks if c.startswith('landsat_')]
 # Add explicitly named heat attributes to current block datasets; leave friction weights unchanged.
 if 'EMPATH_HEAT_OUTPUT' not in os.environ:
  for relative in ['output/clean_deliverables/block_environment.gpkg','output/geoai_full_scope/ai_block_environment.gpkg']:
   path=ROOT/relative;existing=gpd.read_file(path);existing=existing.drop(columns=[c for c in existing if c.startswith('landsat_')]);existing=existing.merge(blocks[joincols],on='GEOID20',how='left',validate='one_to_one');existing.to_file(path,driver='GPKG',index=False)
   existing.drop(columns='geometry').to_csv(path.with_suffix('.csv'),index=False)
  # Keep the existing GeoJSON counterpart synchronized.
  gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg').to_crs(4326).to_file(ROOT/'output/clean_deliverables/block_environment.geojson',driver='GeoJSON',index=False)
 infos=[i for a,i in results];pd.DataFrame(infos).to_csv(OUT/'scene_manifest.csv',index=False)
 report={'source':'USGS Landsat Collection 2 Level-2 Tier 1 Surface Temperature (Landsat 8/9), accessed via Microsoft Planetary Computer','period':'2025-06-01 through 2025-08-31','scenes':len(items),'unique_acquisition_dates':len(days),'local_acquisition_times':[i['acquired_local'] for i in infos],'scale_formula_celsius':'DN * 0.00341802 + 149 - 273.15','qa_policy':'Mask QA_PIXEL bits 0–5, medium/high cloud and cirrus confidence, ST_QA > 3 K, distance to cloud < 1 km; keep water unless separately masked by QA. Require >=3 valid acquisition dates per pixel.','native_thermal_resolution_m':100,'delivered_grid_m':30,'spatial_aggregation':'Block mean of pixelwise temporal medians, pixel-center inclusion; small blocks without centers remain missing. Not independent temperature sensors in every block.','scope_pixel_coverage_fraction':float(eligible.sum()/inside.sum()),'blocks':len(blocks),'blocks_with_temperature':int(blocks.landsat_summer_surface_temp_c.notna().sum()),'temperature_range_c':[float(np.nanmin(median)),float(np.nanmax(median))],'minimum_dates_per_composite_pixel':3,'existing_friction_score_changed':False,'limitations':['Clear-sky satellite surface temperature, not pedestrian air temperature, heat index, or daily maximum.','30 m pixels are resampled from 100 m thermal information.','Only actual overpass times are represented; this is not a June–August peak-hour average.','Uneven valid observations and small-block sampling must be reviewed.','Summer 2025 temperature differs in vintage from 2022 NAIP and 2021 published canopy.'],'references':['https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature','https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands']}
 (OUT/'method_and_coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
 return report
if __name__=='__main__':main()
