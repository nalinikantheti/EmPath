"""Static report figures from the completed full-area GeoAI datasets."""
from pathlib import Path
import json
import full_scope_geoai as pipeline
import geopandas as gpd
from shapely import normalize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tree_adjacency_visuals import CMAP,NORM
ROOT=pipeline.ROOT;OUT=pipeline.OUT

def main():
 blocks=gpd.read_file(OUT/'ai_block_environment.gpkg').to_crs(26914)
 edges=gpd.read_file(OUT/'ai_walking_edges.gpkg').to_crs(26914)
 edges=edges.loc[~edges.geometry.map(lambda g:normalize(g).wkb_hex).duplicated()]
 scope=pipeline.scope();records=[]
 for column,title,palette,name in [('ai_canopy_cover_pct','GeoAI-predicted tree cover — full four-ZIP scope','YlGn','full_geoai_tree_cover.png'),('ai_full_scope_friction_0_100','Provisional walking friction — AI canopy deficit + traffic','YlOrRd','full_geoai_walking_friction.png')]:
  fig,ax=plt.subplots(figsize=(11,8))
  blocks.plot(ax=ax,column=column,cmap=palette,vmin=0,vmax=100,legend=True,linewidth=0,missing_kwds={'color':'#ccc'},legend_kwds={'label':'Percent' if column=='ai_canopy_cover_pct' else 'Provisional index (0–100)','shrink':.7})
  scope.boundary.plot(ax=ax,color='#333',linewidth=.8)
  for _,z in scope.iterrows():
   p=z.geometry.representative_point();ax.text(p.x,p.y,str(z.ZCTA5),ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
  ax.set_title(title);ax.set_axis_off()
  caption='USDA NAIP 2022 (60 cm), Restor TCD SegFormer-B0. Predicted tree cover is not measured shade.\nLocal transfer accuracy is unvalidated. Gray = missing; index uses assumed 50/50 canopy-deficit/traffic weights.'
  fig.text(.05,.025,caption,fontsize=9);fig.savefig(OUT/name,dpi=180,bbox_inches='tight');plt.close(fig)
  records.append({'image':name,'caption':caption})
 fig,ax=plt.subplots(figsize=(11,8))
 edges.plot(ax=ax,column='ai_tree_cover_01',cmap=CMAP,norm=NORM,linewidth=.45,legend=True,legend_kwds={'label':'Predicted tree fraction in 5 m path corridor','ticks':[0,.1,.25,.5,.75,1],'shrink':.7},missing_kwds={'color':'#999'})
 scope.boundary.plot(ax=ax,color='#444',linewidth=.7);ax.set_axis_off();ax.set_title('Walking paths — least to most tree-adjacent')
 caption='Orange = least nearby predicted trees; dark green = most. Gray = unknown.\nOSM segments may be street centerlines, not exact sidewalks. No measured shade or pedestrian access validation.'
 fig.text(.05,.025,caption,fontsize=9);name='full_geoai_tree_adjacent_paths.png';fig.savefig(OUT/name,dpi=180,bbox_inches='tight');plt.close(fig);records.append({'image':name,'caption':caption})
 (OUT/'figure_captions.json').write_text(json.dumps(records,indent=2));return records
if __name__=='__main__':print(json.dumps(main(),indent=2))
