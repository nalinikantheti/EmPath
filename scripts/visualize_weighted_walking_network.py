"""Geographic full pedestrian graph with exact Step 3 edge costs; no new fitting."""
from pathlib import Path
import json, gzip, base64
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from carto_basemap import tiles_url, ATTR
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/weighted_walking_network'

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 edges=gpd.read_file(ROOT/'output/geoai_full_scope/ai_walking_edges.gpkg')
 from prototype_missing_data import enrich_costs
 costs=enrich_costs(pd.read_csv(ROOT/'output/step3_friction/edge_costs.csv'))
 fields=['block_proxy_cost_s','block_proxy_factor_count','block_canopy_deficit_01','block_traffic_burden_01','block_heat_burden_01','block_proxy_nearby_used','block_proxy_partial_overlap','block_canopy_deficit_01_source','block_traffic_burden_01_source','block_heat_burden_01_source','prototype_friction_cost_s','missing_high_burden_cost_s','known_factor_count','missing_factors','available_factor_burden_01','u','v','key','time_only_s','canopy_deficit_01','traffic_burden_01','temperature_burden_01','landsat_summer_surface_temp_c','three_factor_burden_01','scenario_lambda_1_0_cost_s']
 d=edges[['u','v','key','length','ai_tree_cover_01','geometry']].merge(costs[fields],on=['u','v','key'],validate='one_to_one')
 d['strict_multiplier']=d.scenario_lambda_1_0_cost_s/d.time_only_s
 d['multiplier']=d.block_proxy_cost_s/d.time_only_s
 lo,hi=d.multiplier.dropna().quantile([.02,.98])
 d['relative_edge_burden_0_100']=100*((d.multiplier-lo)/(hi-lo)).clip(0,1)
 valid=d.multiplier.notna()
 assert np.allclose(d.loc[valid,'multiplier'],1+d.loc[valid,['block_canopy_deficit_01','block_traffic_burden_01','block_heat_burden_01']].mean(axis=1))
 assert d.loc[valid,'multiplier'].between(1,2).all()
 zones=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(d.crs)
 pois=gpd.read_file(ROOT/'output/four_zip_walking_network/places_of_interest.geojson').to_crs(d.crs)
 pois.geometry=pois.geometry.representative_point()
 blocks=gpd.read_file(ROOT/'output/geoai_full_scope/ai_block_environment.gpkg')[['GEOID20','ai_canopy_cover_pct','traffic_index_0_100','landsat_summer_surface_temp_c','provisional_walking_friction_heat_0_100','geometry']]
 trails=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/trails.gpkg')[['geometry']]
 nodes=pd.read_csv(ROOT/'output/four_zip_walking_network/nodes.csv')
 node_geo=gpd.GeoDataFrame(nodes[['osmid']],geometry=gpd.points_from_xy(nodes.x,nodes.y),crs=4326)
 selected=gpd.read_file(ROOT/'output/residential_poi_graph/shortest_time_selected_network.gpkg')[['u','v','key','geometry']]
 # The PNG is a geographic overview of all edges, not a schematic graph subset.
 fig,ax=plt.subplots(figsize=(13,9))
 d.loc[~valid].plot(ax=ax,color='#9ca3af',linewidth=.4,zorder=1)
 d.loc[valid & ~(d.block_proxy_nearby_used | d.block_proxy_partial_overlap)].plot(ax=ax,column='relative_edge_burden_0_100',cmap='RdYlBu_r',vmin=0,vmax=100,linewidth=.55,legend=True,legend_kwds={'label':'Relative edge burden (0–100): blue = lower, red = higher','shrink':.7},zorder=2)
 d.loc[valid & (d.block_proxy_nearby_used | d.block_proxy_partial_overlap)].plot(ax=ax,column='relative_edge_burden_0_100',cmap='RdYlBu_r',vmin=0,vmax=100,linewidth=.65,linestyle='dashed',zorder=2)
 zones.boundary.plot(ax=ax,color='#4f46a5',linewidth=1,zorder=3)
 pois.plot(ax=ax,color='#ed8a24',markersize=9,edgecolor='white',linewidth=.25,zorder=4)
 for _,zone in zones.iterrows():
  p=zone.geometry.representative_point();ax.text(p.x,p.y,str(zone.ZCTA5),ha='center',fontsize=10,weight='bold',bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'},zorder=5)
 ax.set_title('EmPath · Estimated walking friction from census-block overlays',fontsize=15)
 ax.set_axis_off();ax.legend(handles=[Line2D([0],[0],color='#c44726',linestyle='dashed',label='Nearby-block or partial-overlap estimate'),Line2D([0],[0],color='#9ca3af',label='Unknown friction: missing required data'),Line2D([0],[0],marker='o',color='w',markerfacecolor='#ed8a24',label='Mapped POI')],loc='lower left',frameon=True)
 fig.text(.06,.025,'Every mapped walking segment is retained. Colors stretch the pilot’s 2nd–98th percentiles for visibility; blue is relatively lower burden, not friction-free. Actual edge costs are unchanged.\nThree-factor block proxy; dashed = nearby-block transfer or partial overlap. Missing observations stay missing. Not measured shade, safety or validated comfort.',fontsize=9)
 fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(OUT/'full_weighted_network.png',dpi=180);plt.close(fig)
 def pack(frame):
  s=frame.to_crs(4326).to_json(drop_id=True)
  return base64.b64encode(gzip.compress(s.encode(),compresslevel=7)).decode()
 display=d.rename(columns={'length':'length_m','scenario_lambda_1_0_cost_s':'friction_cost_s'})
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EmPath · Full weighted walking graph</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>html,body,#map{height:100%;margin:0;font:14px system-ui}.card{background:white;padding:12px;max-width:325px;border-radius:8px;box-shadow:0 1px 7px #888;line-height:1.45}.ramp{height:12px;background:linear-gradient(90deg,#2c7bb6,#abd9e9,#ffffbf,#fdae61,#d7191c)}.leaflet-control-layers-list{max-height:55vh;overflow:auto}#status{position:fixed;left:50%;top:18px;transform:translateX(-50%);background:white;padding:12px;z-index:2000;border-radius:6px}</style><div id="map"></div><div id="status">Loading the complete walking graph…</div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
let scoring='block';const PAYLOAD=__PAYLOAD__;const map=L.map('map',{preferCanvas:true});const renderer=L.canvas({padding:.4});
L.tileLayer(__TILES__,{attribution:__ATTR__,maxZoom:20}).addTo(map);
const esc=v=>String(v??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const fmt=(v,n=2)=>v==null?'Unknown':Number(v).toFixed(n);const palette=['#2c7bb6','#abd9e9','#ffffbf','#fdae61','#d7191c'];
function uncertain(p){return scoring==='block'?(p.block_proxy_nearby_used||p.block_proxy_partial_overlap):(scoring!=='strict'&&p.known_factor_count<3);}
function costFor(p){if(scoring==='block')return p.block_proxy_cost_s;return scoring==='strict'?p.friction_cost_s:scoring==='pessimistic'?p.missing_high_burden_cost_s:p.prototype_friction_cost_s;}
function multiplierFor(p){const c=costFor(p);return c==null?null:c/p.time_only_s;}
const color=v=>v==null?'#9ca3af':palette[Math.min(4,Math.max(0,Math.floor((v-__COLOR_LOW__)/(__COLOR_HIGH__-__COLOR_LOW__)*5)))];
async function unpack(s){const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));return JSON.parse(await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).text());}
const legend=L.control({position:'bottomleft'});legend.onAdd=()=>{const d=L.DomUtil.create('div','card');d.innerHTML='<b>Full geographic walking graph</b><br>31,372 junction / endpoint nodes<br>93,452 directed walking edges<br>317 mapped POI candidates<br><hr><b>Provisional friction multiplier</b><div class="ramp"></div>Blue: lower relative burden → red: higher<br>2nd–98th percentile stretch; routing costs unchanged<br><span style="color:#6b7280">Gray: unknown required factors</span><hr><b>Edge cost = walking time × multiplier</b><br>Default: 1 + average of all three block-proxy burdens.<br>All block scores are estimates.<br>Dashed = nearby-block transfer or partial overlap.<br>Use the scoring selector to compare strict and pessimistic assumptions.<br><small>Equal assumed weights, not learned overall preferences. Heat = block-context surface temperature. Canopy ≠ measured shade. Click a segment for values.</small>';L.DomEvent.disableClickPropagation(d);L.DomEvent.disableScrollPropagation(d);return d;};legend.addTo(map);
(async()=>{try{const [edges,zones,pois,nodes,selected,blocks,trails]=await Promise.all(['edges','zones','pois','nodes','selected','blocks','trails'].map(k=>unpack(PAYLOAD[k])));const overlays={};
const base=L.geoJSON(edges,{renderer,style:f=>({color:color(multiplierFor(f.properties)),weight:2,opacity:.85,dashArray:uncertain(f.properties)?'5 4':null}),onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup(()=>'<b>Walking edge '+esc(p.u)+' → '+esc(p.v)+' (key '+esc(p.key)+')</b><br>Physical length: '+fmt(p.length_m,1)+' m<br>Ordinary walking time: '+fmt(p.time_only_s/60)+' min<br>Friction multiplier: '+fmt(multiplierFor(p))+'×<br><b>Weighted cost: '+(costFor(p)==null?'Unknown':fmt(costFor(p)/60)+' equivalent min')+'</b><br><b>Available factors: '+(scoring==='block'?p.block_proxy_factor_count:p.known_factor_count)+'/3</b><br>Missing: '+esc(scoring==='block'?(p.block_proxy_factor_count===3?'No unknown block factors; proxy estimates': 'Some block proxies unavailable'):(p.missing_factors||'None'))+'<hr>Original edge AI tree fraction: '+fmt(p.ai_tree_cover_01)+'<br>Canopy deficit: '+fmt(p.canopy_deficit_01)+'<br>Traffic burden (Plano reference): '+fmt(p.traffic_burden_01)+'<br>Surface-temperature burden (four-ZIP reference): '+fmt(p.temperature_burden_01)+'<br>Block surface temperature: '+fmt(p.landsat_summer_surface_temp_c,1)+' °C<hr><b>Block-context proxy inputs</b><br>Canopy deficit: '+fmt(p.block_canopy_deficit_01)+' ('+esc(p.block_canopy_deficit_01_source)+')<br>Traffic: '+fmt(p.block_traffic_burden_01)+' ('+esc(p.block_traffic_burden_01_source)+')<br>Heat: '+fmt(p.block_heat_burden_01)+' ('+esc(p.block_heat_burden_01_source)+')<br>Block factors available: '+p.block_proxy_factor_count+'/3<hr><small>Unknown inputs are not zero. Network-only costs exclude access connectors and crossing waits. Access is unverified.</small>');}}).addTo(map);overlays['Full walking graph · friction colors']=base;
const scoringControl=L.control({position:'topleft'});scoringControl.onAdd=()=>{const div=L.DomUtil.create('div','card');div.innerHTML='<b>Estimated walking friction</b><br><select id="scoring-mode"><option value="block">Three block overlays · proxy estimate</option><option value="prototype">Available factors · estimated gaps</option><option value="strict">Complete data only · original</option><option value="pessimistic">Sensitivity · missing burden = 1</option></select><br><small>Partial inputs can bias route choices.<br>Pessimistic values are assumptions, not observations.</small>';L.DomEvent.disableClickPropagation(div);L.DomEvent.disableScrollPropagation(div);return div;};scoringControl.addTo(map);document.getElementById('scoring-mode').onchange=e=>{scoring=e.target.value;base.setStyle(f=>({color:color(multiplierFor(f.properties)),weight:2,opacity:.85,dashArray:uncertain(f.properties)?'5 4':null}));base.closePopup();};
overlays['Census blocks · source environmental summaries']=L.geoJSON(blocks,{renderer,style:{color:'#586b7c',weight:.8,fillOpacity:.06},onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup('<b>Block '+esc(p.GEOID20)+'</b><br>AI canopy: '+fmt(p.ai_canopy_cover_pct)+'%<br>Traffic index: '+fmt(p.traffic_index_0_100)+' / 100<br>Surface temperature: '+fmt(p.landsat_summer_surface_temp_c)+' °C<br>Original three-factor index: '+fmt(p.provisional_walking_friction_heat_0_100));}});
overlays['Municipal trail reference · not integrated into routing']=L.geoJSON(trails,{renderer,style:{color:'#00a7a0',weight:3,dashArray:'8 4'},onEachFeature:(f,l)=>l.bindPopup('Plano municipal trail reference. This overlay does not add a verified connection or routing edge.')});
const boundary=L.geoJSON(zones,{style:{color:'#6b46c1',weight:2,fill:false},onEachFeature:(f,l)=>l.bindTooltip('ZIP '+esc(f.properties.ZCTA5))}).addTo(map);map.fitBounds(boundary.getBounds());overlays['Four ZIP boundaries']=boundary;
overlays['Graph junctions / endpoints (31,372)']=L.geoJSON(nodes,{renderer,pointToLayer:(f,ll)=>L.circleMarker(ll,{renderer,radius:2.5,color:'white',weight:.5,fillColor:'#0891b2',fillOpacity:.8}),onEachFeature:(f,l)=>l.bindPopup('Walking junction '+esc(f.properties.osmid)+'<br>Not a residential activity node.')});
overlays['Only segments in retained shortest residential → POI routes']=L.geoJSON(selected,{renderer,style:{color:'#713ac7',weight:3,opacity:.8}});
const categories=[...new Set(pois.features.map(f=>f.properties.category))].sort();for(const category of categories){const collection={type:'FeatureCollection',features:pois.features.filter(f=>f.properties.category===category)};const group=L.geoJSON(collection,{renderer,pointToLayer:(f,ll)=>L.circleMarker(ll,{renderer,radius:5,color:'white',weight:1,fillColor:'#ed8a24',fillOpacity:1}),onEachFeature:(f,l)=>l.bindPopup('<b>'+esc(f.properties.name)+'</b><br>'+esc(f.properties.category)+'<br>Mapped candidate, not verified entrance')}).addTo(map);overlays['POI: '+category]=group;}
L.control.layers(null,overlays,{collapsed:false}).addTo(map);document.getElementById('status').remove();}catch(e){document.getElementById('status').textContent='Could not load the graph. Open in a current Chrome, Edge or Safari browser. '+e.message;}})();</script></html>'''
 payload={k:pack(v) for k,v in {'edges':display,'zones':zones,'pois':pois,'nodes':node_geo,'selected':selected,'blocks':blocks,'trails':trails}.items()}
 html=html.replace('__COLOR_LOW__',str(float(lo))).replace('__COLOR_HIGH__',str(float(hi)))
 html=html.replace('__PAYLOAD__',json.dumps(payload)).replace('__TILES__',json.dumps(tiles_url())).replace('__ATTR__',json.dumps(ATTR))
 from highlight_rowlett_creek import inject
 html=inject(html)
 (OUT/'full_weighted_network.html').write_text(html)
 method={'edge_cost':'w_e = (L_e / v) * [1 + lambda * (alpha * (1-C_e) + beta * Q_e + gamma * H_e)]',
 'color_scale':{'normalization':'2nd–98th percentile stretch; display only','multiplier_lower':float(lo),'multiplier_upper':float(hi)},
 'settings':{'v_m_per_s':1.2,'lambda':1,'alpha':1/3,'beta':1/3,'gamma':1/3},
 'factors':{'C':'GeoAI-predicted tree fraction in a 5 m edge corridor; valid only with >=98% corridor coverage','Q':'Existing City-of-Plano-referenced traffic index / 100','H':'Existing four-ZIP min-max normalized block Landsat surface-temperature context, assigned by edge midpoint block'},
 'route_cost':'Sum w_e along detailed edges; choose minimum sum for each residential-origin to POI pair.',
 'missing':'Default block proxy requires three estimated block factors. Nearby-block transfer is bounded at 250 m and partial overlaps flagged. Original available-factor, strict and pessimistic modes remain separately selectable; raw observations are unchanged.',
 'edge_count':len(d),'weighted_edges':int(valid.sum()),'unknown_weight_edges':int((~valid).sum()),'poi_count':len(pois),
 'block_proxy_formula':'w_e = time_only_s * [1 + (block canopy deficit + block traffic burden + block heat burden)/3]; all three estimates required',
 'prototype_formula':'w_e = time_only_s * (1 + mean(available burdens)); unknown if none available',
 'not_learned':'Equal factor weights and penalty strength are assumptions. The AI component is pretrained tree segmentation, not learning all friction trade-offs.',
 'display':'Full walking substrate shown geographically; junctions are not residential activity nodes. Junction dots are optional for performance. Retained shortest residential-to-POI segment union is a separate overlay.'}
 (OUT/'weight_equation.json').write_text(json.dumps(method,indent=2))
 import shutil
 shutil.copy2(OUT/'full_weighted_network.html',OUT/'block_proxy_weighted_network.html')
 shutil.copy2(OUT/'full_weighted_network.png',OUT/'block_proxy_weighted_network.png')
 return OUT/'block_proxy_weighted_network.html',OUT/'block_proxy_weighted_network.png'

if __name__=='__main__':print(*run(),sep='\n')
