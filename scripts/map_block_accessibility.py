"""Network-derived block accessibility choropleth, replacing environmental proxy default."""
from pathlib import Path
import os,json,gzip,base64,re,shutil
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from carto_basemap import tiles_url,ATTR,load_key
ROOT=Path(__file__).resolve().parents[1];CITY_MODE=os.environ.get('EMPATH_CITY_MODE')=='1';OUT=ROOT/('output/plano_city/accessibility' if CITY_MODE else 'output/block_accessibility')
SCOPE_FILE=ROOT/('data/processed/plano_reference/plano_city_boundary.gpkg' if CITY_MODE else 'output/four_zip_walking_network/zip_boundaries.geojson')

def packed(data):return base64.b64encode(gzip.compress(json.dumps(data,separators=(',',':'),allow_nan=False).encode(),compresslevel=7)).decode()

def layer_code(map_name, control_name, payload):
 return '''
const accBlocks=await empathDecode(__BLOCKS__);
const accScale=v=>{if(v==null)return '#adb5bd';const c=['#2166ac','#67a9cf','#ffffbf','#ef8a62','#b2182b'];return c[Math.min(4,Math.floor(Math.max(0,Math.min(99.999,v))/20))];};
const accessibilityLayer=L.geoJSON(accBlocks,{style:f=>({color:'#607080',weight:.3,fillColor:accScale(f.properties.access_all_categories_burden_0_100),fillOpacity:.82}),onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup('<b>Block '+p.GEOID20+'</b><br>Network-derived accessibility burden: '+(p.access_all_categories_burden_0_100==null?'Incomplete':p.access_all_categories_burden_0_100.toFixed(1)+' / 100')+'<br>Mean nearest-category cost: '+(p.access_all_categories_mean_equiv_min==null?'Unknown':p.access_all_categories_mean_equiv_min.toFixed(1)+' equivalent min')+'<br>Categories reached: '+p.access_all_categories_reached_categories+'/'+p.access_all_categories_total_categories+'<br>Reference-point snap gap: '+p.access_snap_gap_m.toFixed(0)+' m<br>Entrances unverified. Equal category weights.');}}).addTo(__MAP__);
__CONTROL__.addOverlay(accessibilityLayer,'Walking accessibility — nearest service in each category (network-derived)');
const accessibilityLegend=L.control({position:'bottomright'});accessibilityLegend.onAdd=()=>{const d=L.DomUtil.create('div');d.style.cssText='background:white;padding:12px;max-width:280px;font:13px system-ui';d.innerHTML='<b>Network-derived accessibility burden</b><div style="height:12px;background:linear-gradient(90deg,#2166ac,#67a9cf,#ffffbf,#ef8a62,#b2182b)"></div>Blue: lower trip costs → red: higher<br>Gray: at least one category unreachable<br>Relative 0–100 display; raw costs are equivalent minutes.<br>Closest candidate per category; equal category weights.';return d;};accessibilityLegend.addTo(__MAP__);
'''.replace('__BLOCKS__',json.dumps(payload)).replace('__MAP__',map_name).replace('__CONTROL__',control_name)


def run():
 b=gpd.read_file(OUT/'block_accessibility.gpkg');pois=gpd.read_file(OUT/'accessibility_pois.gpkg').to_crs(4326)
 fields=[c for c in ['HU100','POP100','city_area_fraction','boundary_exit_lower_bound_min','public_area_label'] if c in b]+['GEOID20','representative_address','mapped_address_count','access_network_node','access_snap_gap_m','access_connection_needs_review']+[c for c in b if c.startswith('access_all_categories_') or c.startswith('access_essential_')]
 slim=b[fields+['geometry']].to_crs(4326)
 # GeoPandas converts NaN to JSON null; reserialize strictly for the embedded viewer.
 blocks=json.loads(slim.to_json(drop_id=True))
 table=pd.read_csv(OUT/'nearest_category_costs.csv',dtype={'GEOID20':str}).replace({np.nan:None})
 details={}
 for r in table.to_dict('records'):details.setdefault(r['GEOID20'],[]).append(r)
 zones=json.loads(gpd.read_file(SCOPE_FILE).to_crs(4326).to_json(drop_id=True))
 cols=['network_node','poi_id','name','category','snap_gap_m','source_url','address_status','geometry']
 poidata=json.loads(pois[cols].to_json(drop_id=True))
 for profile in ['all_categories','essential']:
  f,ax=plt.subplots(figsize=(12,8));b.plot(ax=ax,column=f'access_{profile}_burden_0_100',cmap='RdYlBu_r',vmin=0,vmax=100,linewidth=0,legend=True,legend_kwds={'label':'Relative accessibility burden · lower = blue, higher = red','shrink':.7},missing_kwds={'color':'#adb5bd'})
  scope=gpd.read_file(SCOPE_FILE).to_crs(b.crs);scope['ZCTA5']='Plano' if CITY_MODE else scope.ZCTA5
  scope.boundary.plot(ax=ax,color='#333',linewidth=.8)
  for r in scope.itertuples():
   pt=r.geometry.representative_point();ax.text(pt.x,pt.y,str(r.ZCTA5),ha='center',weight='bold',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
  ax.set_axis_off();ax.set_title('Network-derived block walking accessibility · '+('all POI categories' if profile=='all_categories' else 'temple, grocery and pharmacy'))
  f.text(.05,.025,'Mean lowest-friction cost to the closest reachable candidate in each selected category. Equal assumed category weights.\nBlue–red: pilot 2nd–98th percentile display stretch. Gray: incomplete category coverage. Block/POI access points unverified.',fontsize=9)
  f.tight_layout(rect=[0,.07,1,1]);f.savefig(OUT/f'block_accessibility_{profile}.png',dpi=180);plt.close(f)
 payload={'blocks':packed(blocks),'details':packed(details),'zones':packed(zones),'pois':packed(poidata)}
 html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EmPath · Network-derived block accessibility</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>html,body,#map{height:100%;margin:0;font:14px system-ui}.card{background:white;padding:12px;max-width:350px;border-radius:7px;box-shadow:0 1px 7px #999;line-height:1.45}.ramp{height:12px;background:linear-gradient(90deg,#2166ac,#67a9cf,#ffffbf,#ef8a62,#b2182b)}select{padding:8px;max-width:330px}table{border-collapse:collapse;font-size:12px}td,th{padding:4px;border-bottom:1px solid #ddd;text-align:left}.leaflet-popup-content{max-height:500px;overflow:auto}</style><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const DATA=__DATA__;const map=L.map('map',{preferCanvas:true});L.tileLayer(__TILES__,{attribution:__ATTR__,maxZoom:20}).addTo(map);let profile='all_categories';const esc=v=>String(v??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const fmt=(v,n=1)=>v==null?'Unknown':Number(v).toFixed(n);const palette=['#2166ac','#67a9cf','#ffffbf','#ef8a62','#b2182b'];const color=v=>v==null?'#adb5bd':palette[Math.min(4,Math.floor(Math.max(0,Math.min(99.999,v))/20))];
async function unpack(s){const b=Uint8Array.from(atob(s),c=>c.charCodeAt(0));return JSON.parse(await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).text());}
(async()=>{const[blocks,details,zones,pois]=await Promise.all(['blocks','details','zones','pois'].map(k=>unpack(DATA[k])));const overlays={};let selected=null;const property=s=>'access_'+profile+'_'+s;
const style=f=>({color:f.properties.access_connection_needs_review?'#666':'#555',weight:.35,dashArray:f.properties.access_connection_needs_review?'3 4':null,fillColor:color(f.properties[property('burden_0_100')]),fillOpacity:.82});
const layer=L.geoJSON(blocks,{style,onEachFeature:(f,l)=>{const p=f.properties;l.bindTooltip(()=>'<b>Block '+esc(p.GEOID20)+'</b><br>Relative burden: '+fmt(p[property('burden_0_100')])+' / 100<br>Mean nearest-category cost: '+fmt(p[property('mean_equiv_min')])+' equivalent min');l.bindPopup(()=>{const rows=(details[p.GEOID20]||[]).filter(r=>profile==='all_categories'||['hindu_temple','supermarket','pharmacy'].includes(r.category));return '<b>Block '+esc(p.GEOID20)+'</b><br>'+esc(p.representative_address)+'<br><b>Accessibility burden: '+fmt(p[property('burden_0_100')])+' / 100</b><br>Mean category cost: '+fmt(p[property('mean_equiv_min')])+' equivalent min<br>Combined category cost: '+fmt(p[property('sum_equiv_min')])+' equivalent min<br>Reached: '+p[property('reached_categories')]+'/'+p[property('total_categories')]+' categories<br>Origin snap gap: '+fmt(p.access_snap_gap_m,0)+' m'+(p.access_connection_needs_review?' · REVIEW CONNECTION':'')+'<hr><table><tr><th>Category</th><th>Lowest-cost candidate</th><th>Equiv. min</th></tr>'+rows.map(r=>'<tr><td>'+esc(r.category)+'</td><td>'+esc(r.closest_poi_name)+'</td><td>'+fmt(r.min_friction_equivalent_minutes)+'</td></tr>').join('')+'</table><hr><small>Closest means least weighted network cost among catalog candidates. Equal category weights; estimated environmental costs; unverified entrances. Gray means incomplete, not zero friction.</small>';},{maxWidth:550});}}).addTo(map);overlays['Network-derived block accessibility']=layer;
const boundary=L.geoJSON(zones,{style:{color:'#38386a',weight:2,fill:false}}).addTo(map);map.fitBounds(boundary.getBounds());overlays['Four ZIP boundaries']=boundary;
overlays['Candidate POIs (including Hindu temples)']=L.geoJSON(pois,{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:f.properties.category==='hindu_temple'?7:4,color:'white',weight:1,fillColor:f.properties.category==='hindu_temple'?'#8c3bc7':'#ed8a24',fillOpacity:1}),onEachFeature:(f,l)=>l.bindPopup('<b>'+esc(f.properties.name)+'</b><br>'+esc(f.properties.category)+'<br>'+esc(f.properties.address_status)+'<br>Network snap gap: '+fmt(f.properties.snap_gap_m,0)+' m')});
L.control.layers(null,overlays,{collapsed:false}).addTo(map);
const control=L.control({position:'topleft'});control.onAdd=()=>{const d=L.DomUtil.create('div','card');d.innerHTML='<b>Walking accessibility by census block</b><br><select id="profile"><option value="all_categories">Closest service in every category</option><option value="essential">Hindu temple + grocery + pharmacy</option></select><p>Each block chooses the lowest-friction reachable candidate in each category. The score combines those trips—not every business.</p><div class="ramp"></div>Blue: lower costs → red: higher costs<br>Gray: at least one category unreachable<br><small>Relative display stretch, not a learned risk score.<br>Block reference points and entrances need review.<br>Click a block for destinations and route costs.</small>';L.DomEvent.disableClickPropagation(d);L.DomEvent.disableScrollPropagation(d);return d;};control.addTo(map);document.getElementById('profile').onchange=e=>{profile=e.target.value;layer.setStyle(style);layer.closePopup();};})();</script></html>'''
 html=html.replace('__DATA__',json.dumps(payload)).replace('__TILES__',json.dumps(tiles_url())).replace('__ATTR__',json.dumps(ATTR))
 (OUT/'block_accessibility_map.html').write_text(html)
 # Preserve original nine-layer viewer; replace its old provisional default with network-derived layer.
 original=ROOT/'output/clean_deliverables/all_layers_map.html'
 if original.exists() and not CITY_MODE:
  s=original.read_text();backup=original.with_name('all_layers_before_network_accessibility.html')
  if not backup.exists():shutil.copy2(original,backup)
  if 'const accBlocks=' not in s:
   map_name=re.search(r'var (map_\w+) = L.map',s).group(1);control_name=re.findall(r'var (layer_control_\w+)',s)[-1]
   old=re.search(r'"Walking friction.*?"\s*:\s*(feature_group_\w+)',s)
   code=layer_code(map_name,control_name,payload['blocks'])
   if old:code=f'{control_name}.removeLayer({old.group(1)});{map_name}.removeLayer({old.group(1)});\n'+code
   s=s.replace('})().catch(',code+'\n})().catch(',1)
   s=s.replace('Provisional walking-friction index','Legacy environment index (not network accessibility)')
   original.write_text(s)
  else:
   # Refresh the compressed block collection after rerunning scoring.
   s=re.sub(r'const accBlocks=await empathDecode\("[A-Za-z0-9+/=]+"\);','const accBlocks=await empathDecode('+json.dumps(payload['blocks'])+');',s)
   original.write_text(s)
 # Safe website snapshots, without publishing or exposing the local key.
 key=load_key();from urllib.parse import quote
 dest=ROOT/'netlify_site/src';(dest/'maps').mkdir(exist_ok=True)
 for name,path in ([('block_accessibility.html',OUT/'block_accessibility_map.html')] if CITY_MODE else [('block_accessibility.html',OUT/'block_accessibility_map.html'),('environment.html',original),('weighted_walking_network.html',ROOT/'output/weighted_walking_network/block_proxy_weighted_network.html')]):
  text=path.read_text().replace(quote(key,safe=''),'__EMPATH_CARTO_PUBLIC_KEY__').replace(key,'__EMPATH_CARTO_PUBLIC_KEY__')
  assert key not in text
  (dest/'maps'/name).write_text(text)
 for name in ['all_categories','essential']:shutil.copy2(OUT/f'block_accessibility_{name}.png',dest/'figures'/f'block_accessibility_{name}.png')
 block_cols=['GEOID20','access_snap_gap_m']+[c for c in b if c.startswith('access_all_categories_') or c.startswith('access_essential_')]
 b[block_cols].to_csv(dest/'data/block_accessibility.csv',index=False)
 shutil.copy2(OUT/'accessibility_method.json',dest/'data/accessibility_method.json')
 return OUT/'block_accessibility_map.html'

if __name__=='__main__':print(run())
