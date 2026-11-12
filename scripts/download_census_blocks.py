"""Download official 2020 Census blocks intersecting the four EmPath ZCTAs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import requests
import geopandas as gpd
from shapely import make_valid, union_all
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import folium
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
URL='https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10'


def query(params):
    session=requests.Session()
    session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[429,500,502,503,504])))
    r=session.get(URL+'/query',params=params,timeout=90);r.raise_for_status();d=r.json()
    if 'error' in d or d.get('exceededTransferLimit') or d.get('properties',{}).get('exceededTransferLimit'):
        raise RuntimeError(d.get('error','Truncated response'))
    return d


def main():
    raw=ROOT/'data/raw/census_blocks_2020';raw.mkdir(parents=True,exist_ok=True)
    out=ROOT/'data/processed/census_blocks_2020';out.mkdir(parents=True,exist_ok=True)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(4326)
    bbox=','.join(map(str,scope.total_bounds))
    idsfile=raw/'object_ids.json'
    if not idsfile.exists():
        d=query({'f':'json','where':'1=1','returnIdsOnly':'true','geometry':bbox,'geometryType':'esriGeometryEnvelope',
                 'inSR':4326,'spatialRel':'esriSpatialRelIntersects'})
        idsfile.write_text(json.dumps(d))
    ids=sorted(json.loads(idsfile.read_text())['objectIds'])
    if not ids:raise ValueError('No block IDs returned')
    chunks=[ids[i:i+500] for i in range(0,len(ids),500)]
    def fetch(item):
        i,chunk=item;p=raw/f'page_{i:03d}.geojson'
        if not p.exists():
            d=query({'f':'geojson','objectIds':','.join(map(str,chunk)),
                     'outFields':'OBJECTID,GEOID,STATE,COUNTY,TRACT,BLOCK','outSR':4326,'returnGeometry':'true'})
            temp=p.with_suffix('.partial');temp.write_text(json.dumps(d));temp.replace(p)
        return json.loads(p.read_text())['features']
    with ThreadPoolExecutor(max_workers=4) as pool:pages=list(pool.map(fetch,enumerate(chunks)))
    features=[f for page in pages for f in page]
    got=[f['properties']['OBJECTID'] for f in features]
    if len(got)!=len(ids) or set(got)!=set(ids):raise ValueError('Incomplete/duplicate source IDs')
    blocks=gpd.GeoDataFrame.from_features(features,crs=4326)
    blocks['GEOID20']=blocks.GEOID.astype('string')
    if blocks.GEOID20.duplicated().any() or not blocks.GEOID20.str.fullmatch(r'\d{15}').all():
        raise ValueError('Invalid/duplicate census block GEOIDs')
    union=scope.geometry.union_all();blocks=blocks[blocks.intersects(union)].copy()
    blocks['geometry_repaired']=~blocks.geometry.is_valid
    repaired_ids=blocks.loc[blocks.geometry_repaired,'GEOID20'].tolist()
    blocks.loc[blocks.geometry_repaired,'geometry']=blocks.loc[blocks.geometry_repaired].geometry.map(make_valid)
    if not blocks.geometry.is_valid.all() or not blocks.geom_type.isin(['Polygon','MultiPolygon']).all():
        raise ValueError('Unresolved block geometries after repair; inspect source.')
    # Keep complete source polygons; the analysis pipeline clips them explicitly.
    blocks.to_file(out/'blocks.gpkg',driver='GPKG',index=False)
    clipped=blocks.to_crs(26914);clipped.geometry=clipped.geometry.intersection(scope.to_crs(26914).geometry.union_all())
    clipped=clipped[clipped.area>0].copy()
    clipped.geometry=clipped.geometry.map(lambda g: union_all([p for p in g.geoms if p.geom_type in ['Polygon','MultiPolygon']]) if g.geom_type=='GeometryCollection' else g)
    ax=clipped.boundary.plot(color='#666666',linewidth=.25,figsize=(11,8))
    scope.to_crs(26914).boundary.plot(ax=ax,color='black',linewidth=1.2)
    for _,row in scope.to_crs(26914).iterrows():
        p=row.geometry.representative_point();ax.text(p.x,p.y,str(row.ZCTA5),fontsize=11,ha='center',bbox={'facecolor':'white','edgecolor':'none','alpha':.85})
    ax.set_title('2020 Census blocks within the four EmPath ZIP areas');ax.set_axis_off()
    ax.figure.savefig(out/'census_block_boundaries.png',dpi=170,bbox_inches='tight');plt.close(ax.figure)
    view=folium.Map(location=[33.05,-96.74],tiles='OpenStreetMap')
    folium.GeoJson(json.loads(clipped[['GEOID20','geometry']].to_crs(4326).to_json()),
        style_function=lambda f: {'color':'#666666','weight':.5,'fillOpacity':0},
        tooltip=folium.GeoJsonTooltip(fields=['GEOID20'])).add_to(view)
    b=scope.total_bounds;view.fit_bounds([[b[1],b[0]],[b[3],b[2]]])
    view.save(out/'census_block_boundaries.html')
    coverage=[];blockunion=clipped.geometry.union_all()
    for _,r in scope.to_crs(26914).iterrows():
        coverage.append({'zcta':str(r.ZCTA5),'area_fraction_covered':blockunion.intersection(r.geometry).area/r.geometry.area,
                         'intersecting_blocks':int((clipped.intersection(r.geometry).area>0).sum())})
    report={'source':URL,'retrieved_utc':datetime.now(timezone.utc).isoformat(),'bbox_wgs84':bbox,
            'repaired_block_ids':repaired_ids,'bbox_features':len(ids),'intersecting_features':len(blocks),'coverage':coverage,
            'note':'2020 Census block geometry, not block groups or residential clusters. Full source blocks retained; maps clipped to ZCTA union. GEOID20 copied from Census2020 GEOID.'}
    (out/'source_metadata.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
