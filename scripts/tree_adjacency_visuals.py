"""Shared quantitative tree-adjacency colors for PNG and interactive routes."""
import numpy as np
from matplotlib.colors import ListedColormap,BoundaryNorm
BINS=[0,.1,.25,.5,.75,1.000001]
COLORS=['#d95f0e','#fec44f','#a1d99b','#41ab5d','#006d2c']
LABELS=['0–10%','10–25%','25–50%','50–75%','75–100%']
CMAP=ListedColormap(COLORS);NORM=BoundaryNorm(BINS,len(COLORS))
def tree_color(value):
 if value is None or not np.isfinite(value):return '#999999'
 return COLORS[min(len(COLORS)-1,max(0,int(np.searchsorted(BINS,value,side='right')-1)))]
def legend_html():
 swatches=''.join(f'<div><span style="display:inline-block;width:24px;height:5px;background:{c};margin-right:8px;vertical-align:middle"></span>{l}</div>' for c,l in zip(COLORS,LABELS))
 return '<div style="position:fixed;bottom:20px;right:20px;z-index:9999;background:white;padding:12px;max-width:330px;font:13px sans-serif"><b>Predicted tree adjacency</b><br>Tree-covered pixels in a 5 m corridor<br>'+swatches+'<div>Orange: least nearby trees → dark green: most.<br>Gray: unknown. This is not measured shade.<br><b>Route outlines:</b> dashed = shortest distance;<br>dotted = distance–canopy trade-off;<br>solid = tree-adjacency priority (≤1.5× distance,<br>up to 30 loopless candidates).<br>Route colors use this same scale.</div></div>'
