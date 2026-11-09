import json, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import geopandas as gpd
from shapely.geometry.polygon import orient
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from clean_data import session, BASE
def query(url, params):
    response = session().post(url, data=params, timeout=90)
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result
root=ROOT
z=gpd.read_file(root/'output/scope_screen/zcta_boundaries.geojson').to_crs(26914)
z=z[z.ZCTA5.isin(['75025','75024','75023','75074'])].sort_values('ZCTA5')
folder=root/'data/processed/75025_buffer250m'
context=gpd.read_file(folder/'context_boundary.gpkg').to_crs(26914).geometry.unary_union
layers={n:gpd.read_file(folder/f'{n}.gpkg').to_crs(26914) for n in ['sidewalk_surfaces','trails']}
def fetch(task):
    code,geom,name,service=task
    parts=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
    rings=[]
    for p in parts:
        p=orient(p,sign=-1)
        rings.append(list(p.exterior.coords))
        rings.extend(list(r.coords) for r in p.interiors)
    url=f'{BASE}{service}/FeatureServer/0/query'
    result=query(url,{'f':'json','where':'1=1','returnCountOnly':'true','geometry':json.dumps({'rings':rings,'spatialReference':{'wkid':26914}}),'geometryType':'esriGeometryPolygon','inSR':26914,'spatialRel':'esriSpatialRelIntersects'})
    return (code,name,result['count'])
tasks=[(r.ZCTA5,r.geometry,n,s) for _,r in z.iterrows() for n,s in [('sidewalk_surfaces','Sidewalks'),('trails','TrailCenterlines')]]
with ThreadPoolExecutor(max_workers=4) as pool:
    counts={(c,n):v for c,n,v in pool.map(fetch,tasks)}
rows=[]
for _,r in z.iterrows():
    entry={'zcta':r.ZCTA5,'cached_query_area_pct':round(100*r.geometry.intersection(context).area/r.geometry.area,2)}
    for name,frame in layers.items():
        entry[f'cached_{name}']=int(frame.intersects(r.geometry).sum())
        entry[f'source_{name}']=counts[r.ZCTA5,name]
    rows.append(entry)
out=root/'output/coverage_audit';out.mkdir(exist_ok=True)
(out/'walking_coverage.json').write_text(json.dumps(rows,indent=2))
lines=['# Walking data coverage audit','', 'Checked November 8, 2026 against cached Census ZCTA polygons and live Plano GIS feature counts.','', '| ZCTA | Area inside cached processing boundary | Cached sidewalk polygons | Source sidewalk polygons | Cached trail features | Source trail features |','|---|---:|---:|---:|---:|---:|']
for r in rows:
    lines.append(f"| {r['zcta']} | {r['cached_query_area_pct']}% | {r['cached_sidewalk_surfaces']:,} | {r['source_sidewalk_surfaces']:,} | {r['cached_trails']:,} | {r['source_trails']:,} |")
lines+=['','Counts represent features intersecting each ZCTA, not unique totals across all ZCTAs; boundary-spanning features may appear more than once. Cached geometries retain full features, so some extend beyond the cached query area. Source counts establish available mapped features, not complete real-world sidewalk inventories or routable connectivity. Sidewalks are polygons, not ready-made routing edges. No dedicated crossing layer or validated pedestrian graph was found in the processed data.','', '## Conclusion','', 'The saved walking data does not cover the full four-ZCTA study area. Only 75025 plus a 250 m buffer has been downloaded and cleaned. The live city service contains sidewalk and trail features in all four ZCTAs. The next step is to retrieve and clean the full four-ZCTA area, then validate connections and crossings.','', 'Sources:','- '+BASE+'Sidewalks/FeatureServer/0','- '+BASE+'TrailCenterlines/FeatureServer/0']
(out/'walking_coverage.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(rows,indent=2))
