"""Compact municipal address search; block assignment stays internal to routing."""
from pathlib import Path
import json,gzip
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
features=[]
for p in sorted((ROOT/'data/raw/plano_city_addresses').glob('b400_*.geojson')):features.extend(json.loads(p.read_text())['features'])
a=gpd.GeoDataFrame.from_features(features,crs=4326).drop_duplicates('OBJECTID')
b=gpd.read_file(ROOT/'output/plano_city/accessibility/block_accessibility.gpkg').to_crs(4326)
c=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(4326)
a=a[a.geometry.intersects(c.geometry.union_all())].copy()
j=gpd.sjoin(a,b[['GEOID20','HU100','geometry']],how='left',predicate='intersects').drop_duplicates('OBJECTID')
rows=[]
for r in j.itertuples():
 label=str(r.ADDRESS).strip()+', Plano, TX '+str(r.ZIPCODE).split('.')[0]
 rows.append([label,round(r.geometry.x,7),round(r.geometry.y,7),str(r.GEOID20) if isinstance(r.GEOID20,str) else None])
rows.sort();payload={'source':'City of Plano municipal address points','columns':['address','lon','lat','block_id'],'addresses':rows}
p=ROOT/'netlify_site/src/data/address_search.json.gz';p.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode()))
print(json.dumps({'addresses':len(rows),'assigned_blocks':sum(r[3] is not None for r in rows),'gzip_bytes':p.stat().st_size}))
