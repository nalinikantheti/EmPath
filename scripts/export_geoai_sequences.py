"""Explain AI feature extraction separately from GIS scoring; one example per ZIP."""
from pathlib import Path
import json
import imagery_geoai_demo  # Match Rasterio's PROJ database before GIS imports.
import numpy as np,geopandas as gpd,rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from shapely.geometry import box
from shapely import normalize
from tree_adjacency_visuals import CMAP,NORM
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/vegetation_geoai'
def main():
 records=json.loads((OUT/'imagery_manifest.json').read_text());edges=gpd.read_file(ROOT/'output/geoai_full_scope/ai_walking_edges.gpkg').to_crs(26914);manifest=[]
 for rec in records:
  z=rec['zip']
  with rasterio.open(ROOT/rec['image']) as src:
   rgb=np.moveaxis(src.read([1,2,3]),0,-1);extent=[src.bounds.left,src.bounds.right,src.bounds.bottom,src.bounds.top]
  with rasterio.open(ROOT/rec['image']) as src:
   with rasterio.open(ROOT/'output/geoai_full_scope/full_scope_tree_cover.tif') as full:
    with WarpedVRT(full,crs=src.crs,transform=src.transform,width=src.width,height=src.height,resampling=Resampling.nearest,nodata=255) as vrt:mask=vrt.read(1)
  bounds=box(extent[0],extent[2],extent[1],extent[3])
  subset=edges[edges.geometry.buffer(5).within(bounds)].copy()
  subset=subset.loc[~subset.geometry.map(lambda g:normalize(g).wkb_hex).duplicated()]
  # Only complete edges are shown, so their average is supported entirely by the visible image.

  fig=plt.figure(figsize=(18,6.6));grid=fig.add_gridspec(1,4,width_ratios=[1,1,1,.045],wspace=.11)
  axes=[fig.add_subplot(grid[0,i]) for i in range(3)];cax=fig.add_subplot(grid[0,3])
  titles=['1. Input: aerial photograph','2. GeoAI: predict tree-covered pixels','3. Actual path scores + 5 m corridors']
  for ax,title in zip(axes,titles):ax.imshow(rgb,extent=extent);ax.set_title(title,fontsize=13,pad=12);ax.set_axis_off()
  overlay=np.ma.masked_where(mask!=1,mask)
  axes[1].imshow(overlay,extent=extent,cmap=ListedColormap(['#00ad69']),vmin=0,vmax=1,alpha=.6)
  axes[2].imshow(np.ones_like(rgb)*255,extent=extent,alpha=.55)
  axes[2].imshow(overlay,extent=extent,cmap=ListedColormap(['#00ad69']),vmin=0,vmax=1,alpha=.3)
  subset.geometry.buffer(5).boundary.plot(ax=axes[2],color='#555',linewidth=.35,alpha=.6)
  subset.plot(ax=axes[2],column='ai_tree_cover_01',cmap=CMAP,norm=NORM,linewidth=2.3,legend=True,cax=cax,legend_kwds={'ticks':[0,.1,.25,.5,.75,1]})
  cax.set_yticklabels(['0%','10%','25%','50%','75%','100%']);cax.set_ylabel('Predicted trees within a 5 m path corridor',fontsize=10)
  for ax in axes:ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:])
  fig.suptitle(f'ZIP {z} — from an aerial image to tree-adjacency scores',fontsize=18,y=.98)
  fig.text(.04,.035,'USDA NAIP 2022 imagery; pretrained Restor TCD SegFormer-B0; existing OpenStreetMap paths.\nExact full-area predictions and scores are used. Thin outlines show 5 m measurement corridors; colors are whole-edge averages.\nTrees outside a corridor do not count toward its score. One example area per ZIP; not measured shade or validated accuracy.',fontsize=10)
  fig.subplots_adjust(top=.86,bottom=.18,left=.025,right=.95)
  name=f'geoai_sequence_{z}.png';fig.savefig(OUT/name,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
  manifest.append({'image':name,'zip':z,'title':f'{z}: aerial image → AI tree prediction → path score','caption':'Uses the same full-area tree predictions and path scores as the live map. Thin outlines show 5 m corridors. Complete edges only; colors are whole-edge averages, not shade predictions.'})
 (OUT/'geoai_sequence_captions.json').write_text(json.dumps(manifest,indent=2));print('Saved four GeoAI image sequences, with routing overlays removed.')
 return manifest
if __name__=='__main__':main()
