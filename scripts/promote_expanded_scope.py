"""Promote validated 3 km source coverage, retaining the prior 1 km snapshot locally."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'output/plano_boundary_3km';DEST=ROOT/'output/plano_city'
def run():
 cov=json.load(open(SRC/'environment_coverage.json'));cost=json.load(open(SRC/'friction/block_proxy_method.json'))
 assert cov['city_blocks']==4402 and cov['context_pixel_coverage_fraction']>.999
 expected=json.load(open(SRC/'network_inventory.json'))['directed_edges']
 assert cost['edge_count']==expected and cost['unknown_edges']==0,'Do not promote a graph with unknown weights'
 archive=DEST/'prior_1km';archive.mkdir(exist_ok=True)
 files=['block_environment.gpkg','block_environment_context.gpkg','block_context_base.gpkg','environment_context.gpkg','environment_coverage.json','network_inventory.json','pois.gpkg']
 for name in files:
  if (DEST/name).exists() and not (archive/name).exists():shutil.copy2(DEST/name,archive/name)
 for name in ['nearest_category_costs.csv','block_accessibility.csv','accessibility_method.json','routing_network_method.json']:
  p=DEST/'accessibility'/name
  if p.exists() and not (archive/name).exists():shutil.copy2(p,archive/name)
 for directory in ['network','friction']:
  if not (archive/directory).exists():shutil.copytree(DEST/directory,archive/directory)
  shutil.copytree(SRC/directory,DEST/directory,dirs_exist_ok=True)
 for name in files:shutil.copy2(SRC/name,DEST/name)
 shutil.copy2(SRC/'traffic_roads.gpkg',DEST/'traffic_roads.gpkg')
 scope={'routing_buffer_m':3000,'public_max_effort_minutes':30,'expanded_data_root':'output/plano_boundary_3km','source_tiles':cov['planned_and_summarized_tiles'],'tree_inference_source':'2022 NAIP; Restor TCD SegFormer-B0; actual cached and new predictions','previous_scope_archive':'output/plano_city/prior_1km','note':'Production graph, POIs and environmental features all expanded together; city origins unchanged.'}
 (DEST/'active_scope.json').write_text(json.dumps(scope,indent=2));print(json.dumps(scope,indent=2))
if __name__=='__main__':run()
