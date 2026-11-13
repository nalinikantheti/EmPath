"""Local-redesign assets from current full-Plano production data; no publication."""
from pathlib import Path
import json,gzip
import geopandas as gpd,pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src/data';OUT=ROOT/'output/plano_city/accessibility'
def packed(name,frame):
 frame=frame.to_crs(4326).copy();frame.geometry=frame.geometry.simplify(.000005,preserve_topology=True)
 (DEST/name).write_bytes(gzip.compress(frame.to_json(drop_id=True).encode()))
def run():
 b=gpd.read_file(OUT/'block_accessibility.gpkg');fields=['GEOID20','representative_address','mapped_address_count','public_area_label','POP100','HU100','ai_canopy_cover_pct','traffic_index_0_100','traffic_area_mean_aadt','landsat_summer_surface_temp_c','temperature_burden_01','ai_imagery_coverage_01','access_all_categories_mean_equiv_min','access_essential_mean_equiv_min','access_network_node','access_snap_gap_m','boundary_exit_lower_bound_min','geometry'];b['environment_burden']=((1-b.ai_canopy_cover_pct/100)+b.traffic_index_0_100/100+b.temperature_burden_01)/3
 d=pd.read_csv(OUT/'nearest_category_costs.csv',dtype={'GEOID20':str});profile=sorted(d.category.unique());time=d.pivot(index='GEOID20',columns='category',values='baseline_time_minutes')[profile];shade=d.pivot(index='GEOID20',columns='category',values='min_friction_equivalent_minutes')[profile];b['family_time_min']=b.GEOID20.map(time.mean(axis=1).where(time.notna().all(axis=1)));b['family_shade_min']=b.GEOID20.map(shade.mean(axis=1).where(shade.notna().all(axis=1)));valid=b.HU100.gt(0)&b.access_snap_gap_m.le(100)&b.family_time_min.notna()&b.family_shade_min.notna();tr=(b.loc[valid,'family_time_min'].rank()-1)/(valid.sum()-1)*100;sr=(b.loc[valid,'family_shade_min'].rank()-1)/(valid.sum()-1)*100;b['family_rank_delta']=sr-tr;packed('master_blocks.geojson.gz',b[fields+['environment_burden','family_time_min','family_shade_min','family_rank_delta']]);packed('master_pois.geojson.gz',gpd.read_file(OUT/'accessibility_pois.gpkg'))
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg');(DEST/'plano_boundary.geojson').write_text(city.to_crs(4326).to_json(drop_id=True))
 nodes=pd.read_csv(ROOT/'output/plano_city/network/nodes.csv');xy=gpd.GeoSeries(gpd.points_from_xy(nodes.x,nodes.y),crs=4326).to_crs(26914)
 (DEST/'routing_node_xy.json.gz').write_bytes(gzip.compress(json.dumps([[int(n),round(x,3),round(y,3)] for n,x,y in zip(nodes.osmid,xy.x,xy.y)],separators=(',',':')).encode()))
 scope=gpd.read_file(ROOT/'output/plano_city/environment_context.gpkg').to_crs(26914)
 (DEST/'routing_extent.json').write_text(scope.to_json(drop_id=True))
 print('Full-city master assets:',len(b),'blocks; full routing node coordinates',len(nodes))
if __name__=='__main__':run()
