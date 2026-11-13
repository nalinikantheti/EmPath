"""Publish the actual edge-local AI tree fractions, separately from block summaries."""
from pathlib import Path
import json,gzip
import geopandas as gpd
from shapely.geometry import LineString,MultiLineString
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src'
r=json.loads(gzip.decompress((DEST/'data/routing_network.json.gz').read_bytes()));seen=set();rows=[]
for e in r['edges']:
 key=(min(e[0],e[1]),max(e[0],e[1]),e[2])
 if key in seen:continue
 seen.add(key);rows.append([e[11],e[14],e[4],e[10]])
payload={'source':'Restor TCD predicted tree raster from 2022 NAIP; 20 m-wide path corridor','columns':['predicted_tree_fraction','raster_sample_coverage','length_m','lines_lonlat'],'paths':rows,'limit':'Nearby predicted trees, not time-specific shade. Incomplete or absent raster samples may use block-level estimates.'}
p=DEST/'data/ai_tree_paths.json.gz';p.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode()))
city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(4326)
g=gpd.GeoDataFrame({'tree':[a[0] for a in rows]},geometry=[LineString(a[3][0]) if len(a[3])==1 else MultiLineString(a[3]) for a in rows],crs=4326);g=gpd.clip(g,city).to_crs(26914)
fig,ax=plt.subplots(figsize=(12,8));cmap=LinearSegmentedColormap.from_list('tree_paths',['#d65b06','#fff3a3','#86c98c','#00632a']);g.plot(ax=ax,column='tree',cmap=cmap,vmin=0,vmax=1,linewidth=.4,legend=True,legend_kwds={'label':'Predicted tree fraction beside walking paths','shrink':.7});city.to_crs(26914).boundary.plot(ax=ax,color='#45534b',linewidth=.7);ax.set_axis_off();ax.set_title('GeoAI · tree adjacency along walking paths');fig.text(.04,.025,'2022 NAIP → pretrained tree segmentation → 20 m-wide path-corridor samples.\nTree adjacency is a shade proxy; mapped pedestrian access and model transfer are unvalidated.',fontsize=9);fig.tight_layout(rect=[0,.08,1,1]);fig.savefig(DEST/'figures/plano_ai_tree_paths.png',dpi=160);plt.close(fig);print(json.dumps({'unique_paths':len(rows),'gzip_bytes':p.stat().st_size}))
