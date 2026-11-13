"""Refresh municipal address reference coverage for the entire Plano boundary."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,requests,geopandas as gpd,pandas as pd
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw/plano_city_addresses';OUT=ROOT/'output/plano_city';URL='https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0/query'
def run():
 RAW.mkdir(exist_ok=True);b=gpd.read_file(OUT/'accessibility/block_accessibility.gpkg').to_crs(26914);city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914);bbox=city.to_crs(4326).total_bounds
 p=RAW/'ids.json'
 if not p.exists():
  r=requests.get(URL,params={'f':'json','where':'1=1','returnIdsOnly':'true','geometry':','.join(map(str,bbox)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'},timeout=60);r.raise_for_status();p.write_text(json.dumps(r.json()))
 ids=sorted(json.loads(p.read_text())['objectIds']);chunks=[ids[i:i+400] for i in range(0,len(ids),400)]
 def fetch(item):
  i,ids=item;p=RAW/f'b400_{i:03}.geojson'
  if not p.exists():
   r=requests.get(URL,params={'f':'geojson','objectIds':','.join(map(str,ids)),'outFields':'OBJECTID,ADDRESS,FULLNAME,ZIPCODE','outSR':4326},timeout=90);r.raise_for_status();d=r.json();assert 'error' not in d and not d.get('exceededTransferLimit');p.write_text(json.dumps(d))
  return json.loads(p.read_text())['features']
 with ThreadPoolExecutor(max_workers=4) as pool:features=[f for group in pool.map(fetch,enumerate(chunks)) for f in group]
 a=gpd.GeoDataFrame.from_features(features,crs=4326).to_crs(26914);a=a[a.intersects(city.geometry.union_all())].copy();a['OBJECTID']=a.OBJECTID.astype(int)
 join=gpd.sjoin(a[['OBJECTID','ADDRESS','geometry']],b[['GEOID20','geometry']],how='inner',predicate='intersects').sort_values(['GEOID20','OBJECTID']).drop_duplicates(['GEOID20','OBJECTID'])
 counts=join.groupby('GEOID20').size();centers=b.set_index('GEOID20').geometry.representative_point();join['reference_distance_m']=[p.distance(centers[id]) for p,id in zip(join.geometry,join.GEOID20)]
 chosen=join.sort_values(['GEOID20','reference_distance_m','OBJECTID']).drop_duplicates('GEOID20').set_index('GEOID20')
 b['mapped_address_count']=b.GEOID20.map(counts).fillna(0).astype(int);b['representative_address']=b.GEOID20.map(chosen.ADDRESS).fillna('No municipal address mapped inside this block')
 b.to_file(OUT/'accessibility/block_accessibility.gpkg',driver='GPKG',index=False);b.drop(columns='geometry').to_csv(OUT/'accessibility/block_accessibility.csv',index=False)
 report={'scope':'Official Plano municipal boundary','source':URL,'retrieved_date':'2026-11-13','address_points':len(a),'city_blocks':len(b),'blocks_with_address':int(b.mapped_address_count.gt(0).sum()),'housing_positive_blocks_without_address':int((b.HU100.gt(0)&b.mapped_address_count.eq(0)).sum()),'note':'Representative municipal address nearest the block interior point; not a verified entrance or listing.'};(OUT/'address_coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':run()
