"""Wait for the active tile run, then build the full-area products locally."""
import time,json,os
from pathlib import Path
from full_scope_geoai import OUT
cfg=json.loads((OUT/'tile_plan.json').read_text())
active=json.loads((OUT/'active_run.json').read_text())
while True:
    missing=[t['id'] for t in cfg['tiles'] if not (OUT/'tiles'/(t['id']+'.tif')).exists()]
    if not missing:break
    try:os.kill(int(active['pid']),0)
    except ProcessLookupError:raise RuntimeError(f'Inference stopped with {len(missing)} tiles missing. Rerun Notebook 14 to resume.')
    time.sleep(10)
from summarize_full_scope_geoai import summarize,render
summarize()
from full_scope_route_comparison import run
print(run().to_string(index=False),flush=True)
import geopandas as gpd
render(gpd.read_file(OUT/'ai_block_environment.gpkg'),gpd.read_file(OUT/'ai_walking_edges.gpkg'))
from full_scope_geoai import status
status(stage='complete',route_comparisons_completed=True)
print('Full-area inference, aggregation, route comparisons and interactive map complete.',flush=True)
