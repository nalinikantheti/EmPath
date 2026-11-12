"""Prepare city-context Census blocks and existing city-referenced traffic."""
from pathlib import Path
import json
import geopandas as gpd,pandas as pd,numpy as np
from shapely import make_valid
from prepare_plano_reference import fetch_features,CENSUS,polygon_only
from traffic_area_index import primary_roads,area_summary,normalize_traffic
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city'

def run():
 scope=gpd.read_file(OUT/'environment_context.gpkg').to_crs(26914);region=scope.geometry.union_all()
 bbox=scope.to_crs(4326).total_bounds;raw=ROOT/'data/raw/plano_city_context_blocks';raw.mkdir(exist_ok=True)
 cached=list((ROOT/'data/raw/census_blocks_2020').glob('page_*.geojson'))+list((ROOT/'data/raw/plano_reference/blocks').glob('page_*.geojson'))
 b=fetch_features(CENSUS,bbox,cached,raw,400).to_crs(26914)
 b['geometry_repaired']=~b.geometry.is_valid;b.geometry=b.geometry.map(make_valid);b=b[b.intersects(region)].copy();b['GEOID20']=b.GEOID.astype(str)
 b.geometry=b.geometry.intersection(region).map(polygon_only);b=b[b.area>1e-6].reset_index(drop=True)
 roads=primary_roads(gpd.read_file(ROOT/'data/processed/plano_reference/traffic_roads.gpkg'))
 summary=area_summary(b,roads)
 parameters=json.load(open(ROOT/'output/clean_deliverables/traffic_index_method.json'))['normalization']
 norm,_=normalize_traffic(summary.traffic_area_mean_aadt,parameters)
 b=b.join(summary).join(norm)
 old=pd.read_csv(ROOT/'output/geoai_full_scope/ai_block_environment.csv',dtype={'GEOID20':str})
 keep=['GEOID20','representative_address','mapped_address_count']
 b=b.merge(old[keep],on='GEOID20',how='left',validate='one_to_one')
 ll=b.geometry.representative_point().to_crs(4326);b['block_latitude']=ll.y;b['block_longitude']=ll.x
 b['representative_address']=b.representative_address.fillna('No representative street address assigned; use block reference coordinates')
 b.to_file(OUT/'block_context_base.gpkg',driver='GPKG',index=False)
 b.drop(columns='geometry').to_csv(OUT/'block_context_base.csv',index=False)
 print('City-context blocks:',len(b),'traffic-supported:',int(b.traffic_index_0_100.notna().sum()),flush=True)
 return b
if __name__=='__main__':run()
