"""Whole-city weighted network viewer using the exact routing dataset."""
from pathlib import Path
import json,base64,gzip
import geopandas as gpd,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility'

def run():
 edges=gpd.read_file(ROOT/'output/plano_city/network/edges.gpkg').to_crs(26914)
 cost=pd.read_csv(ROOT/'output/plano_city/friction/block_proxy_edge_costs.csv')
 d=edges.merge(cost[['u','v','key','block_proxy_burden_01']],on=['u','v','key'],validate='one_to_one')
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914);region=city.geometry.union_all()
 shown=d[d.intersects(region)].copy();reference=shown.block_proxy_burden_01.dropna();lo,hi=reference.quantile([.02,.98]);shown['relative']=100*((shown.block_proxy_burden_01-lo)/(hi-lo)).clip(0,1)
 fig,ax=plt.subplots(figsize=(12,8));shown.plot(ax=ax,column='relative',cmap='RdYlBu_r',vmin=0,vmax=100,linewidth=.5,legend=True,legend_kwds={'label':'Relative edge burden · blue lower / red higher','shrink':.75},missing_kwds={'color':'gray'});city.boundary.plot(ax=ax,color='#252545',linewidth=1.2)
 ax.set_title('Plano city · weighted pedestrian network');ax.set_axis_off();fig.text(.05,.025,'Official municipal boundary; 3 km routing context retained in analysis. Colors use the city’s 2nd–98th percentile stretch.\nActual routing costs are unchanged. Environmental proxies and OSM paths are not verified shade or sidewalk safety.',fontsize=9);fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(OUT/'plano_weighted_network.png',dpi=180);plt.close(fig)
 boundary=json.loads(city.to_crs(4326).to_json(drop_id=True));payload=base64.b64encode(gzip.compress(json.dumps(boundary).encode())).decode()
 html='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Plano weighted walking network</title><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>html,body,#map{height:100%;margin:0;font:14px system-ui}.card{background:white;padding:12px;max-width:340px;border-radius:7px;box-shadow:0 1px 6px #999}.ramp{height:12px;background:linear-gradient(90deg,#2166ac,#67a9cf,#ffffbf,#ef8a62,#b2182b)}#loading{position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:2000;background:white;padding:12px}</style><div id="map"></div><div id="loading">Loading citywide walking edges…</div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const map=L.map('map',{preferCanvas:true});L.tileLayer('https://empathmaps.netlify.app/.netlify/functions/basemap?z={z}&x={x}&y={y}',{attribution:'© OpenStreetMap contributors · © CARTO',maxNativeZoom:19,maxZoom:20}).addTo(map);const scale=[__LO__,__HI__],colors=['#2166ac','#67a9cf','#ffffbf','#ef8a62','#b2182b'];const color=v=>colors[Math.max(0,Math.min(4,Math.floor((v-scale[0])/(scale[1]-scale[0])*5)))];const esc=v=>String(v??'Unnamed').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function decode(bytes){if(bytes[0]===31&&bytes[1]===139)return JSON.parse(await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text());return JSON.parse(new TextDecoder().decode(bytes));}
(async()=>{try{const boundary=await decode(Uint8Array.from(atob('__BOUNDARY__'),c=>c.charCodeAt(0)));const outline=L.geoJSON(boundary,{style:{color:'#383858',weight:2,fill:false}}).addTo(map);map.fitBounds(outline.getBounds());const r=await fetch('../data/routing_network.json.gz');if(!r.ok)throw Error('Routing dataset unavailable');const data=await decode(new Uint8Array(await r.arrayBuffer()));const renderer=L.canvas();const paths=L.featureGroup();for(const e of data.edges){if(e[0]>e[1])continue;const lines=e[10].map(line=>line.map(([x,y])=>[y,x]));L.polyline(lines,{renderer,color:color(e[3]/(e[4]/1.2)-1),weight:2,opacity:.8}).bindPopup('<b>'+esc(e[6])+'</b><br>OSM tag: '+esc(e[5])+'<br>Distance: '+e[4].toFixed(0)+' m<br>Walking time: '+(e[4]/1.2/60).toFixed(2)+' min<br>Friction cost: '+(e[3]/60).toFixed(2)+' equivalent min<br>Near mapped busy-road corridor: '+(e[8]*100).toFixed(0)+'%<br><small>Block-context proxy cost, not verified sidewalk comfort or safety.</small>').addTo(paths);}paths.addTo(map);outline.bringToFront();L.control.layers(null,{'Weighted city + context paths':paths,'Official Plano boundary':outline},{collapsed:false}).addTo(map);document.getElementById('loading').remove();const control=L.control({position:'bottomleft'});control.onAdd=()=>{const d=L.DomUtil.create('div','card');d.innerHTML='<b>Plano city weighted walking graph</b><br>'+data.nodes.length.toLocaleString()+' junctions · '+data.edges.length.toLocaleString()+' directed edges<div class="ramp"></div>Blue = lower relative burden; red = higher.<br>City 2nd–98th percentile stretch.<br>3 km routing buffer includes paths outside city.<br><a href="../app.html">Choose a block and inspect routes →</a>';return d;};control.addTo(map);}catch(e){document.getElementById('loading').textContent=e.message;}})();</script>'''
 html=html.replace('__LO__',str(float(lo))).replace('__HI__',str(float(hi))).replace('__BOUNDARY__',payload)
 (OUT/'plano_weighted_network.html').write_text(html);(ROOT/'netlify_site/src/maps/weighted_walking_network.html').write_text(html)
 import shutil
 shutil.copy2(OUT/'plano_weighted_network.png',ROOT/'netlify_site/src/figures/plano_weighted_network.png')
 return OUT/'plano_weighted_network.html'
if __name__=='__main__':print(run())
