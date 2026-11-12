"""Plain-language area labels from nearby named OSM walking edges, not addresses."""
from pathlib import Path
import json
import pandas as pd,geopandas as gpd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility'
def run():
 b=gpd.read_file(OUT/'block_accessibility.gpkg').to_crs(26914);e=gpd.read_file(ROOT/'output/plano_city/network/edges.gpkg').to_crs(26914)
 def name(v):
  if not isinstance(v,str) or v.strip().lower() in ['nan','none','unnamed','']:return None
  try:values=json.loads(v) if v.startswith('[') else [v]
  except ValueError:values=[v]
  return next((str(x) for x in values if str(x).strip().lower() not in ['none','nan','']),None)
 e['street_label']=e['name'].map(name);e=e[e.street_label.notna()].drop_duplicates(['u','v','street_label'])
 points=b[['GEOID20','geometry']].copy();points.geometry=points.geometry.representative_point()
 match=gpd.sjoin_nearest(points,e[['street_label','geometry']],how='left',max_distance=500,distance_col='label_distance_m').sort_values(['GEOID20','label_distance_m','street_label']).drop_duplicates('GEOID20').set_index('GEOID20')
 b['public_area_label']=b.GEOID20.map(match.street_label).map(lambda s:'Near '+s if isinstance(s,str) else 'Area reference')
 b['public_area_label_distance_m']=b.GEOID20.map(match.label_distance_m)
 b.to_file(OUT/'block_accessibility.gpkg',driver='GPKG',index=False);b.drop(columns='geometry').to_csv(OUT/'block_accessibility.csv',index=False)
 print('Named area labels:',int(b.public_area_label.ne('Area reference').sum()),'of',len(b))
if __name__=='__main__':run()
