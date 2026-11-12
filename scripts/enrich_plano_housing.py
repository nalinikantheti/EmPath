"""Fetch complete public 2020 housing counts; never interpret missing as zero."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,requests,pandas as pd,geopandas as gpd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city'
URL='https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10/query'

def run():
 b=gpd.read_file(OUT/'block_environment.gpkg');ids=b.OBJECTID.astype(int).tolist();cache=ROOT/'data/raw/plano_city_housing';cache.mkdir(exist_ok=True)
 chunks=[ids[i:i+500] for i in range(0,len(ids),500)]
 def fetch(item):
  i,group=item;p=cache/f'{i:02}.json'
  if not p.exists():
   r=requests.get(URL,params={'f':'json','objectIds':','.join(map(str,group)),'outFields':'OBJECTID,GEOID,HU100,POP100','returnGeometry':'false'},timeout=45);r.raise_for_status();d=r.json()
   if 'error'in d or d.get('exceededTransferLimit'):raise RuntimeError('Housing metadata request incomplete')
   p.write_text(json.dumps(d))
  return [x['attributes'] for x in json.loads(p.read_text())['features']]
 with ThreadPoolExecutor(max_workers=4) as pool:rows=[r for group in pool.map(fetch,enumerate(chunks)) for r in group]
 t=pd.DataFrame(rows);assert len(t)==len(b) and t.GEOID.nunique()==len(b)
 t['GEOID20']=t.GEOID.astype(str);t=t[['GEOID20','HU100','POP100']]
 b=b.drop(columns=['HU100','POP100'],errors='ignore');b['GEOID20']=b.GEOID20.astype(str);b=b.merge(t,on='GEOID20',validate='one_to_one');b.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
 report={'source':URL,'year':2020,'blocks':len(b),'housing_count_known_blocks':int(b.HU100.notna().sum()),'housing_positive_blocks':int(pd.to_numeric(b.HU100).gt(0).sum()),'note':'Full Census block housing units; not current homes for sale or proof of housing in the city-clipped part of boundary blocks.'}
 (OUT/'housing_metadata.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));return report
if __name__=='__main__':run()
