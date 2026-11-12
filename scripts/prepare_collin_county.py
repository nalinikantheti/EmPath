"""Official county expansion geography; outside-pilot accessibility stays unscored."""
from pathlib import Path
from shapely import make_valid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
import requests
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/collin_county'
BASE='https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer'

def query(layer,params):
 r=requests.get(f'{BASE}/{layer}/query',params=params,timeout=60);r.raise_for_status();d=r.json()
 if 'error' in d or d.get('exceededTransferLimit'):raise RuntimeError('Census query failed or truncated')
 return d

def run():
 OUT.mkdir(exist_ok=True);cache=OUT/'block_pages';cache.mkdir(exist_ok=True)
 boundary_file=OUT/'county_boundary.geojson'
 if not boundary_file.exists():
  d=query(82,{'f':'geojson','where':"GEOID='48085'",'outFields':'*','outSR':4326,'returnGeometry':'true'})
  if len(d.get('features',[]))!=1:raise ValueError('Expected one Collin County boundary')
  boundary_file.write_text(json.dumps(d))
 idfile=OUT/'object_ids.json'
 if not idfile.exists():idfile.write_text(json.dumps(query(10,{'f':'json','where':"STATE='48' AND COUNTY='085'",'returnIdsOnly':'true'})))
 ids=sorted(json.loads(idfile.read_text())['objectIds']);chunks=[ids[i:i+500] for i in range(0,len(ids),500)]
 def fetch(item):
  i,chunk=item;p=cache/f'{i:03}.geojson'
  if not p.exists():
   d=query(10,{'f':'geojson','objectIds':','.join(map(str,chunk)),'outFields':'OBJECTID,GEOID,STATE,COUNTY,TRACT,BLOCK','outSR':4326,'returnGeometry':'true'})
   tmp=p.with_suffix('.partial');tmp.write_text(json.dumps(d));tmp.replace(p)
  return json.loads(p.read_text())['features']
 with ThreadPoolExecutor(max_workers=4) as pool:pages=list(pool.map(fetch,enumerate(chunks)))
 features=[f for page in pages for f in page]
 assert len(features)==len(ids) and len({f['properties']['OBJECTID'] for f in features})==len(ids)
 b=gpd.GeoDataFrame.from_features(features,crs=4326);b['GEOID20']=b.GEOID.astype(str)
 assert not b.GEOID20.duplicated().any()
 b['geometry_repaired']=~b.geometry.is_valid
 invalid_ids=b.loc[b.geometry_repaired,'GEOID20'].tolist()
 b.loc[b.geometry_repaired,'geometry']=b.loc[b.geometry_repaired].geometry.map(make_valid)
 assert b.geometry.is_valid.all()
 b.to_file(OUT/'county_census_blocks.gpkg',driver='GPKG',index=False)
 boundary=gpd.read_file(boundary_file).to_crs(26914)
 pilot=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
 # No environmental values or accessibility outside the processed pilot are fabricated.
 report={'scope':'Collin County, Texas','fips':'48085','source':BASE,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
 'census_blocks':len(b),'county_area_km2':float(boundary.area.sum()/1e6),'pilot_area_km2':float(pilot.area.sum()/1e6),
 'county_area_covered_by_pilot_km2':float(pilot.geometry.intersection(boundary.geometry.iloc[0]).area.sum()/1e6),
 'status':'County geography acquired; full county weighted network, environmental feature coverage and destination inventory NOT yet acquired or scored.',
 'block_scores':'Current four-ZIP scores remain pilot-only. County extension must rerun routes across a connected county network and include a boundary buffer, not extrapolate pilot scores.',
 'repaired_block_ids':invalid_ids,'block_geometry_valid':bool(b.geometry.is_valid.all()),'unique_ids':True,
 'next_steps':['Acquire county walking network plus a routing buffer; audit OSM access and connectivity.','Acquire county POIs including verified temples and entrances.','Extend NAIP GeoAI/heat/traffic coverage and choose consistent normalization references.','Join features and benchmark weights, then rerun nearest-category accessibility for county blocks.'],
 'network_acquisition_note':'GET queries failed; standard POST queries subsequently succeeded for pilot POIs. County network still needs separate acquisition, topology checks and feature processing.'}
 (OUT/'expansion_status.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
