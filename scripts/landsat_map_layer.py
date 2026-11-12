"""Actual summer surface-temperature layer and explicit three-factor scenario index."""
from pathlib import Path
import json
import numpy as np,pandas as pd,geopandas as gpd,folium
from branca.colormap import linear
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/landsat_heat'
def update_index():
 ai=gpd.read_file(ROOT/'output/geoai_full_scope/ai_block_environment.gpkg')
 temp=ai.landsat_summer_surface_temp_c
 lo=float(temp.min());hi=float(temp.max())
 if hi<=lo:raise ValueError('Temperature range cannot be normalized')
 ai['temperature_burden_01']=(temp-lo)/(hi-lo)
 ai['provisional_walking_friction_heat_0_100']=100*(ai.temperature_burden_01+ai.traffic_index_0_100/100+1-ai.ai_canopy_cover_pct/100)/3
 columns=['GEOID20','ai_canopy_cover_pct','temperature_burden_01','provisional_walking_friction_heat_0_100']
 for path in [ROOT/'output/clean_deliverables/block_environment.gpkg',ROOT/'output/geoai_full_scope/ai_block_environment.gpkg',OUT/'block_environment_with_heat.gpkg']:
  d=gpd.read_file(path).drop(columns=[c for c in columns[1:] if c in gpd.read_file(path,rows=0).columns])
  d=d.merge(ai[columns],on='GEOID20',validate='one_to_one');d.to_file(path,driver='GPKG',index=False);d.drop(columns='geometry').to_csv(path.with_suffix('.csv'),index=False)
 method={'formula':'100 * (temperature_burden_01 + traffic_index_0_100/100 + 1 - ai_canopy_cover_pct/100) / 3','temperature_reference':'Min–max across valid block surface-temperature summaries in the four-ZIP pilot','temperature_min_c':lo,'temperature_max_c':hi,'traffic_reference':'Existing City-of-Plano-referenced nearby traffic-volume index, not a pure distance-to-road measure','canopy':'AI-predicted cover / 100','weights':'Explicit equal weights; not learned from preferences','missing':'Any missing required factor gives unknown score','limits':'Surface temperature and canopy may be correlated. This is a scenario index, not validated comfort, air temperature or health risk.'}
 (OUT/'three_factor_index_method.json').write_text(json.dumps(method,indent=2));return ai,method

def add_heat_layer(view,blocks):
 if 'landsat_summer_surface_temp_c' not in blocks:return
 d=blocks.to_crs(4326);lo=float(d.landsat_summer_surface_temp_c.min());hi=float(d.landsat_summer_surface_temp_c.max());scale=linear.YlOrRd_09.scale(lo,hi)
 group=folium.FeatureGroup(name='Landsat summer 2025 surface temperature (°C)',show=False)
 folium.GeoJson(json.loads(d[['GEOID20','landsat_summer_surface_temp_c','landsat_mean_valid_dates','landsat_valid_pixel_fraction','representative_address','geometry']].to_json()),style_function=lambda f:{'fillColor':'#ccc' if f['properties']['landsat_summer_surface_temp_c'] is None else scale(f['properties']['landsat_summer_surface_temp_c']),'fillOpacity':.8,'color':'#777','weight':.2},tooltip=folium.GeoJsonTooltip(fields=['GEOID20','landsat_summer_surface_temp_c','landsat_mean_valid_dates','landsat_valid_pixel_fraction','representative_address'],aliases=['Block','Summer median surface temperature (°C)','Mean valid observation dates','Valid composite pixel fraction','Representative address'])).add_to(group)
 group.add_to(view)
 if 'provisional_walking_friction_heat_0_100' in d:
  score=folium.FeatureGroup(name='Walking friction — temperature + traffic − AI canopy (equal weights)',show=False)
  palette=linear.YlOrRd_09.scale(0,100)
  folium.GeoJson(json.loads(d[['GEOID20','provisional_walking_friction_heat_0_100','geometry']].to_json()),style_function=lambda f:{'fillColor':'#ccc' if f['properties']['provisional_walking_friction_heat_0_100'] is None else palette(f['properties']['provisional_walking_friction_heat_0_100']),'fillOpacity':.8,'weight':.2},tooltip=folium.GeoJsonTooltip(fields=['GEOID20','provisional_walking_friction_heat_0_100'],aliases=['Block','Three-factor friction (0–100)'])).add_to(score)
  score.add_to(view)
 # Exact ranges and meaning stay visible when the corresponding layer is selected.
 from branca.element import MacroElement,Template
 view.get_root().html.add_child(folium.Element(f'<div id="landsat-legend" style="display:none;position:fixed;bottom:25px;right:20px;z-index:9999;background:white;padding:12px;font:13px sans-serif;max-width:310px"><b>Landsat surface temperature</b><div style="height:12px;background:linear-gradient(to right,#ffffcc,#800026)"></div>{lo:.1f} °C → {hi:.1f} °C<br>Summer 2025 clear-sky medians around noon.<br>Gray = unknown; not air temperature.</div>'))
 macro=MacroElement();macro.map_name=view.get_name();macro.heat=group.get_name()
 macro._template=Template("""{% macro script(this, kwargs) %}
 function heatLegend(){document.getElementById('landsat-legend').style.display={{this.map_name}}.hasLayer({{this.heat}})?'block':'none';}{{this.map_name}}.on('overlayadd overlayremove',heatLegend);heatLegend();
 {% endmacro %}""");macro.add_to(view)
 return group

def figures():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 blocks,method=update_index();scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(blocks.crs);records=[]
 for field,title,name,legend in [('landsat_summer_surface_temp_c','Landsat summer 2025 surface temperature','landsat_surface_temperature.png','Surface temperature (°C)'),('provisional_walking_friction_heat_0_100','Provisional walking friction — temperature, traffic and canopy','three_factor_walking_friction.png','Provisional index (0–100)')]:
  fig,ax=plt.subplots(figsize=(11,8));kw={'vmin':0,'vmax':100} if field.startswith('provisional') else {}
  blocks.plot(ax=ax,column=field,cmap='YlOrRd',linewidth=0,legend=True,legend_kwds={'label':legend,'shrink':.7},missing_kwds={'color':'#ccc'},**kw);scope.boundary.plot(ax=ax,color='#333',linewidth=.8)
  for _,z in scope.iterrows():
   p=z.geometry.representative_point();ax.text(p.x,p.y,str(z.ZCTA5),ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
  ax.set_axis_off();ax.set_title(title)
  caption='June–August 2025 clear-sky overpass observations; ≥3 valid dates per composite pixel.\nSurface temperature, not air temperature or daily maximum. 100 m thermal data delivered on a 30 m grid. Gray = unknown.' if field.startswith('landsat') else '100 × [normalized surface temperature + normalized nearby traffic + (1 − predicted canopy fraction)] / 3.\nEqual assumed weights; correlated factors; not validated perceived friction or health risk. Gray = unknown.'
  fig.text(.05,.025,caption,fontsize=9);fig.savefig(OUT/name,dpi=180,bbox_inches='tight');plt.close(fig);records.append({'image':name,'caption':caption,'title':title})
 (OUT/'figure_captions.json').write_text(json.dumps(records,indent=2));return records
if __name__=='__main__':figures()
