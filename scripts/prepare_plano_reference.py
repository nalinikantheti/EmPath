"""Cache official Plano city limits, city-wide blocks and traffic context."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely import make_valid,union_all
from clean_data import query
ROOT=Path(__file__).resolve().parents[1]
CITY='https://maps.planogis.org/arcgiswad/rest/services/OpenData/MunicipalBoundary/FeatureServer/0'
CENSUS='https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10'
TRAFFIC='https://services.arcgis.com/KTcxiTD9dsQw4r7Z/ArcGIS/rest/services/TxDOT_AADT/FeatureServer/0'


def fetch_features(url,bbox,cached_files,raw,batch):
    known={}
    for p in cached_files:
        for f in json.loads(p.read_text()).get('features',[]):known[f['properties']['OBJECTID']]=f
    ids_path=raw/'ids.json'
    if not ids_path.exists():
        d=query(url+'/query',{'f':'json','where':'1=1','returnIdsOnly':'true','geometry':','.join(map(str,bbox)),
            'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'})
        ids_path.write_text(json.dumps(d))
    ids=sorted(json.loads(ids_path.read_text()).get('objectIds') or [])
    if not ids:raise ValueError('Source returned no IDs')
    missing=[i for i in ids if i not in known]
    chunks=[missing[i:i+batch] for i in range(0,len(missing),batch)]
    def fetch(item):
        i,chunk=item;p=raw/f'page_{i:04d}.geojson'
        if not p.exists():
            d=query(url+'/query',{'f':'geojson','objectIds':','.join(map(str,chunk)),
                'outFields':'*','outSR':4326,'returnGeometry':'true'})
            p.write_text(json.dumps(d))
        return json.loads(p.read_text())['features']
    print(f'{raw.name}: {len(ids)} IDs; {len(missing)} additional features to fetch',flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for features in pool.map(fetch,enumerate(chunks)):
            for f in features:known[f['properties']['OBJECTID']]=f
    if any(i not in known for i in ids):raise ValueError('Incomplete source response')
    return gpd.GeoDataFrame.from_features([known[i] for i in ids],crs=4326)


def polygon_only(g):
    return union_all([x for x in g.geoms if x.geom_type in ['Polygon','MultiPolygon']]) if g.geom_type=='GeometryCollection' else g


def main():
    raw=ROOT/'data/raw/plano_reference';out=ROOT/'data/processed/plano_reference'
    raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    cityfile=raw/'municipal_boundary.geojson'
    if not cityfile.exists():cityfile.write_text(json.dumps(query(CITY+'/query',{'f':'geojson','where':'1=1','outFields':'*','outSR':4326,'returnGeometry':'true'})))
    city=gpd.read_file(cityfile).to_crs(26914)
    city.geometry=city.geometry.map(make_valid).map(polygon_only)
    city=city[~city.geometry.is_empty].copy();city.to_file(out/'plano_city_boundary.gpkg',driver='GPKG',index=False)
    boundary=city.geometry.union_all();bbox=city.to_crs(4326).total_bounds
    br=raw/'blocks';br.mkdir(exist_ok=True)
    blocks=fetch_features(CENSUS,bbox,list((ROOT/'data/raw/census_blocks_2020').glob('page_*.geojson')),br,400)
    blocks=blocks.to_crs(26914);blocks.geometry=blocks.geometry.map(make_valid)
    blocks=blocks[blocks.intersects(boundary)].copy()
    blocks['GEOID20']=blocks.GEOID.astype(str)
    original_area=blocks.area
    blocks.geometry=blocks.geometry.intersection(boundary).map(polygon_only)
    blocks['city_area_fraction']=blocks.area/original_area
    blocks=blocks[blocks.area>1e-6].copy()
    assert blocks.GEOID20.is_unique and blocks.geometry.is_valid.all()
    blocks.to_file(out/'plano_reference_blocks.gpkg',driver='GPKG',index=False)
    coverage=blocks.geometry.union_all().intersection(boundary).area/boundary.area
    if coverage<.999:raise ValueError(f'Incomplete city block coverage: {coverage}')
    pilot=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914).geometry.union_all()
    context=boundary.union(pilot).buffer(1000)
    tb=gpd.GeoSeries([context],crs=26914).to_crs(4326).total_bounds
    tr=raw/'traffic';tr.mkdir(exist_ok=True)
    traffic=fetch_features(TRAFFIC,tb,list((ROOT/'data/raw/txdot_aadt').glob('page75_*.geojson')),tr,75).to_crs(26914)
    traffic.geometry=traffic.geometry.map(make_valid);traffic=traffic[traffic.intersects(context)].copy()
    traffic['aadt']=__import__('pandas').to_numeric(traffic.AADT_CUR,errors='coerce').where(lambda x:x>0)
    traffic['source_feature_id']=traffic.OBJECTID.astype(str)
    if not traffic.geometry.is_valid.all():raise ValueError('Traffic geometries unresolved')
    traffic.to_file(out/'traffic_roads.gpkg',driver='GPKG',index=False)
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'city_boundary_source':CITY,'census_source':CENSUS,
        'traffic_source':TRAFFIC,'city_blocks':len(blocks),'city_area_coverage':coverage,'traffic_sections':len(traffic),
        'context_buffer_m':1000,'scope':'Official Plano municipal polygon, not four-ZIP union; clipped block portions with positive city area',
        'note':'All clipped city blocks contribute equally to reference; not population-weighted. Traffic outside city retained for nearby buffer context and pilot edges. Source vintage remains explicit.'}
    (out/'source_metadata.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
