"""Add an actual-graph Rowlett Creek locator to generated full-network maps."""
from pathlib import Path
import json
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]

def inject(html):
 if 'rowlett-locator-control' in html:return html
 source=ROOT/'output/rowlett_creek_audit/rowlett_osm_edges.gpkg'
 if not source.exists():return html
 d=gpd.read_file(source).to_crs(4326)
 keep=['u','v','key','name','ai_tree_cover_01','scenario_lambda_1_0_cost_s','block_proxy_cost_s','geometry']
 data=d[keep].to_json(drop_id=True)
 code='''
const rowlettLayer=L.geoJSON(__DATA__,{renderer,style:{color:'#008c42',weight:5,opacity:1},onEachFeature:(f,l)=>{const p=f.properties;l.bindPopup('<b>'+esc(p.name)+'</b><br>Actual original OSM graph edge: '+esc(p.u)+' → '+esc(p.v)+'<br>AI nearby tree fraction: '+fmt(p.ai_tree_cover_01)+'<br>Block-proxy cost: '+(p.block_proxy_cost_s==null?'Unknown':fmt(p.block_proxy_cost_s/60)+' equivalent minutes')+'<br><small>Green is a locator highlight, not the friction scale. Toggle it off to see friction colors. Access and seasonal conditions are unverified.</small>');}}).addTo(map);
overlays['Rowlett Creek Trail · actual graph edges (green locator)']=rowlettLayer;
const rowlettControl=L.control({position:'topright'});rowlettControl.onAdd=()=>{const div=L.DomUtil.create('div','card');const button=document.createElement('button');button.id='rowlett-locator-control';button.textContent='Zoom to Rowlett Creek Trail';button.style.cssText='padding:9px;cursor:pointer';button.onclick=()=>{rowlettLayer.addTo(map);map.fitBounds(rowlettLayer.getBounds(),{padding:[35,35]});};div.appendChild(button);L.DomEvent.disableClickPropagation(div);return div;};rowlettControl.addTo(map);
'''.replace('__DATA__',data)
 marker="overlays['Full walking graph · friction colors']=base;"
 if marker not in html:raise ValueError('Full graph viewer insertion point missing')
 return html.replace(marker,marker+code,1)

def run():
 for name in ['full_weighted_network.html','block_proxy_weighted_network.html']:
  p=ROOT/'output/weighted_walking_network'/name
  if p.exists():p.write_text(inject(p.read_text()))
if __name__=='__main__':run()
