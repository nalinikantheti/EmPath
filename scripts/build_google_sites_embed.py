"""Build a compact, self-contained block-map embed; no public hosting required for data."""
from pathlib import Path
import sys,json,gzip,base64
import geopandas as gpd
from combined_block_index import calculate
from carto_basemap import tiles_url,ATTR
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/google_sites_embed'

def main():
 OUT.mkdir(exist_ok=True,parents=True)
 b=calculate(gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg')).to_crs(26914)
 b.geometry=b.geometry.simplify(5,preserve_topology=True)
 cols=['GEOID20','canopy_mean','traffic_index_0_100','combined_burden_0_100','representative_address','geometry']
 geo=b[cols].to_crs(4326).to_json(drop_id=True)
 payload=base64.b64encode(gzip.compress(geo.encode(),compresslevel=9)).decode()
 page='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><style>html,body{margin:0;height:100%;font:14px Arial}#map{height:750px;min-height:500px}.info{background:white;padding:10px;max-width:320px;line-height:1.4}select{max-width:290px}</style></head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const map=L.map('map');L.tileLayer(TILE_URL,{attribution:ATTRIBUTION,maxZoom:19}).addTo(map);
const escapeHtml=x=>String(x??'Unknown').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const info=L.control({position:'topright'});let layer,mode='combined_burden_0_100';
const ramps={canopy_mean:['#ffffcc','#006837'],traffic_index_0_100:['#f7fbff','#08306b'],combined_burden_0_100:['#ffffcc','#800026']};
function color(v){if(v===null||!Number.isFinite(v))return '#ccc';const a=ramps[mode].map(x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16)));return '#'+a[0].map((x,i)=>Math.round(x+(a[1][i]-x)*v/100).toString(16).padStart(2,'0')).join('');}
function style(f){return {fillColor:color(f.properties[mode]),fillOpacity:.78,color:'#777',weight:.35};}
info.onAdd=()=>{const d=L.DomUtil.create('div','info');d.innerHTML='<b>EmPath — four-ZIP block map</b><br><select id="mode"><option value="combined_burden_0_100">Walking friction: provisional equal weights</option><option value="canopy_mean">Estimated canopy cover</option><option value="traffic_index_0_100">Traffic index vs City of Plano</option></select><p>Darker = higher selected value.<br>Friction = 50% canopy deficit + 50% traffic.<br>Gray = missing. Scenario weights, not AI-learned.<br>Canopy is not measured shade. Traffic is not measured danger.<br>Click a block for its address and values.</p>';L.DomEvent.disableClickPropagation(d);return d;};info.addTo(map);
document.getElementById('mode').onchange=e=>{mode=e.target.value;if(layer)layer.setStyle(style);};
(async()=>{try{const bytes=Uint8Array.from(atob(PAYLOAD),c=>c.charCodeAt(0));const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));const data=JSON.parse(await new Response(stream).text());layer=L.geoJSON(data,{style,onEachFeature:(f,l)=>{const p=f.properties;const val=k=>p[k]===null?'Unknown':Number(p[k]).toFixed(1);l.bindPopup('<b>Census block '+escapeHtml(p.GEOID20)+'</b><br>'+escapeHtml(p.representative_address)+'<br>Canopy: '+val('canopy_mean')+'%<br>Traffic index: '+val('traffic_index_0_100')+'<br>Provisional walking friction: '+val('combined_burden_0_100'));}}).addTo(map);map.fitBounds(layer.getBounds());}catch(e){document.getElementById('map').innerText='Map could not load. Use a current browser with DecompressionStream support.';}})();
</script></body></html>'''
 page=page.replace('TILE_URL',json.dumps(tiles_url())).replace('ATTRIBUTION',json.dumps(ATTR)).replace('PAYLOAD',json.dumps(payload))
 (OUT/'GOOGLE_SITES_COMPACT_BLOCK_MAP.html').write_text(page)
 (OUT/'GOOGLE_SITES_COMPACT_BLOCK_MAP.txt').write_text(page)
 print('Saved compact, self-contained block-map HTML and text:',len(page),'characters. Display boundaries simplified by 5 m; data values unchanged. Separate from full graph viewer. Google Sites embedding not yet tested.')
if __name__=='__main__':main()
