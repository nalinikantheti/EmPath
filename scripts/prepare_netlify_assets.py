"""Copy current map snapshots to versionable static assets, stripping the local basemap key."""
from pathlib import Path
import shutil
from urllib.parse import quote
from carto_basemap import load_key
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src'
def main():
 key=load_key();encoded=quote(key,safe='')
 sources={'block_accessibility.html':'output/block_accessibility/block_accessibility_map.html','weighted_walking_network.html':'output/weighted_walking_network/block_proxy_weighted_network.html','geoai_full_scope.html':'output/geoai_full_scope/full_scope_geoai_map.html','environment.html':'output/clean_deliverables/all_layers_map.html','walking_network.html':'output/four_zip_walking_network/walking_scope_map_carto.html','geoai_routes.html':'output/vegetation_geoai/geoai_canopy_routes.html','shaded_trails.html':'output/trail_finder/shaded_trail_candidates.html'}
 for name,source in sources.items():
  text=(ROOT/source).read_text();text=text.replace(encoded,'__EMPATH_CARTO_PUBLIC_KEY__').replace(key,'__EMPATH_CARTO_PUBLIC_KEY__')
  if key in text or encoded in text:raise RuntimeError('Credential stripping failed')
  (DEST/'maps'/name).write_text(text)
 shutil.copytree(ROOT/'output/vegetation_geoai/display_images',DEST/'maps/display_images',dirs_exist_ok=True)
 for image in (ROOT/'output/geoai_full_scope').glob('full_geoai_*.png'):shutil.copy2(image,DEST/'figures'/image.name)
 figures=ROOT/'output/document_layers'
 for p in figures.glob('*.png'):shutil.copy2(p,DEST/'figures'/p.name)
 text=(figures/'index.html').read_text().replace('interactive_map_links.html','../index.html');(DEST/'figures/index.html').write_text(text)
 data_dir=DEST/'data';data_dir.mkdir(exist_ok=True)
 import pandas as pd
 heat=ROOT/'output/landsat_heat'
 table=pd.read_csv(heat/'block_environment_with_heat.csv')
 cols=['GEOID20']+[c for c in table if c.startswith('landsat_') or c in ['temperature_burden_01','provisional_walking_friction_heat_0_100','ai_canopy_cover_pct','traffic_index_0_100']]
 table[cols].to_csv(data_dir/'landsat_block_summary.csv',index=False)
 shutil.copy2(heat/'method_and_coverage.json',data_dir/'landsat_methods.json')
 shutil.copy2(heat/'three_factor_index_method.json',data_dir/'friction_method.json')
 from build_map_gallery import main as build_gallery
 build_gallery()
 print('Prepared map snapshots and figures with basemap-key placeholders. No credentials logged.')
if __name__=='__main__':main()
