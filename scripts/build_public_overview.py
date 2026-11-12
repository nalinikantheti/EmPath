"""A faithful static snapshot of the public 20-effort-minute default selection."""
from pathlib import Path
import json,shutil
import geopandas as gpd,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/public'
def run():
 OUT.mkdir(exist_ok=True);b=gpd.read_file(ROOT/'output/plano_city/accessibility/block_accessibility.gpkg');d=pd.read_csv(ROOT/'output/plano_city/accessibility/nearest_category_costs.csv',dtype={'GEOID20':str});p=d.pivot(index='GEOID20',columns='category',values='min_friction_equivalent_minutes')[['supermarket','pharmacy','park']]
 b['mean']=b.GEOID20.map(p.mean(axis=1));b['worst']=b.GEOID20.map(p.max(axis=1));b['complete']=b.GEOID20.map(p.notna().all(axis=1))
 valid=b.complete&b.worst.le(20)&b.HU100.gt(0)&b.access_snap_gap_m.le(100)&b.boundary_exit_lower_bound_min.gt(20)
 fig,ax=plt.subplots(figsize=(12,8));b.plot(ax=ax,color='#e1e5e5',linewidth=0)
 lo,hi=b.loc[valid,'mean'].quantile([.02,.98]);b.loc[valid].plot(ax=ax,column='mean',cmap='RdYlBu_r',vmin=lo,vmax=hi,linewidth=0,legend=True,legend_kwds={'label':'Average effort minutes · lower is easier','shrink':.7});ax.set_axis_off();ax.set_title('Everyday walks in Plano · groceries, pharmacy and park')
 caption='Each selected destination must be within a 20-effort-minute budget. 2020 residential areas passing an automatic connection-distance filter.\nBlue = lower average modeled effort; red = higher among matches. Gray = not a match or needs review; not a safety rating.\nRoutes use a fully weighted 3 km context beyond Plano; extent sufficiency checked for short walks. Entrances remain unverified.\nSources: OpenStreetMap contributors; City of Plano; Census Bureau; TxDOT; USDA NAIP; USGS Landsat.'
 fig.text(.04,.025,caption,fontsize=9);fig.tight_layout(rect=[0,.10,1,1]);image='plano_public_everyday_walks.png';fig.savefig(OUT/image,dpi=170);plt.close(fig)
 (OUT/'figure_captions.json').write_text(json.dumps([{'image':image,'title':'Public explorer · everyday walks within a 20-minute effort budget','caption':caption.replace('\n',' ')}],indent=2));shutil.copy2(OUT/image,ROOT/'netlify_site/src/figures'/image);print('Public 20-minute matches:',int(valid.sum()))
if __name__=='__main__':run()
