"""Export annotated static context figures for the current city map gallery."""
from pathlib import Path
import json,shutil
import geopandas as gpd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/social';DEST=ROOT/'netlify_site/src/figures'
def run():
 b=gpd.read_file(OUT/'population_density.gpkg');bg=gpd.read_file(OUT/'acs_context.gpkg');tr=gpd.read_file(OUT/'disability_tracts.gpkg');rows=[]
 specs=[(b,'population_density','Population density · 2020 Census blocks','People per land km²'),(bg,'median_gross_rent','Area median gross rent · 2020–2024 ACS','Median gross rent ($ / month)'),(bg,'median_home_value','Area median home value · 2020–2024 ACS','Owner-reported median home value ($)'),(bg,'median_household_income','Area median household income · 2020–2024 ACS','Median household income ($)'),(bg,'no_vehicle_pct','Households without a vehicle · 2020–2024 ACS','Occupied housing units without a vehicle (%)'),(bg,'age65_pct','Residents aged 65+ · 2020–2024 ACS','Residents aged 65+ (%)'),(bg,'poverty_pct','Residents below poverty threshold · 2020–2024 ACS','Population for whom poverty is determined (%)'),(tr,'disability_pct','Residents with a disability · 2020–2024 ACS','Civilian noninstitutionalized population (%)')]
 for frame,field,title,label in specs:
  fig,ax=plt.subplots(figsize=(12,8));lo,hi=frame[field].dropna().quantile([.02,.98]);frame.plot(ax=ax,column=field,cmap='Purples',vmin=lo,vmax=hi,linewidth=.12,edgecolor='#bbb',legend=True,legend_kwds={'label':label,'shrink':.7},missing_kwds={'color':'#b7bdc3'});ax.set_title(title);ax.set_axis_off()
  caption='Full 2020 block population divided by full Census land area. City-border fragments flagged in interactive map; no allocation to fragments.' if field=='population_density' else '2020–2024 ACS estimates for full '+('tracts' if field=='disability_pct' else 'block groups')+'. Geometry clipped to Plano; not block-level estimates. See interactive popups for 90% margins of error.'
  caption+=' Context only: not part of walking costs. Gray = unavailable. Display clipped at 2nd–98th percentiles.'
  fig.text(.04,.025,caption,fontsize=9,wrap=True);fig.tight_layout(rect=[0,.07,1,1]);image='plano_context_'+field+'.png';fig.savefig(OUT/image,dpi=170);plt.close(fig);shutil.copy2(OUT/image,DEST/image);rows.append({'image':image,'title':title,'caption':caption})
 (OUT/'figure_captions.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':run()
