"""Geographic lookup links and zoom-aware labels for census block polygons."""
from pathlib import Path
import json
from html import escape
import geopandas as gpd
import folium
from branca.element import MacroElement,Template
ROOT=Path(__file__).resolve().parents[1]


def add_location_fields(blocks):
    blocks=blocks.copy()
    points=blocks.to_crs(26914).geometry.representative_point()
    ll=gpd.GeoSeries(points,crs=26914).to_crs(4326)
    blocks['block_latitude']=ll.y.to_numpy();blocks['block_longitude']=ll.x.to_numpy()
    blocks['block_google_maps_url']=blocks.apply(lambda r:f'https://www.google.com/maps/search/?api=1&query={r.block_latitude:.6f},{r.block_longitude:.6f}',axis=1)
    blocks['block_street_view_url']=blocks.apply(lambda r:f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={r.block_latitude:.6f},{r.block_longitude:.6f}',axis=1)
    blocks['block_location_note']='Representative point inside the block, not a verified street address or entrance. Street View may show a nearby street or be unavailable.'
    return blocks


def add_zoom_labels(view,blocks,min_zoom=16):
    view.get_root().header.add_child(folium.Element('<style>.empath-block-label{pointer-events:none!important;}</style>'))
    group=folium.FeatureGroup(name='Block address labels (zoom 16+)',show=True).add_to(view)
    records=[{'id':str(r.GEOID20),'lat':r.block_latitude,'lon':r.block_longitude,'address':escape(str(r.get('representative_address','')).split(',')[0]) if r.get('mapped_address_count',0)>0 else ''} for _,r in blocks.iterrows()]
    macro=MacroElement();macro._name='BlockLocationLabels'
    macro.map_name=view.get_name();macro.group_name=group.get_name();macro.records=json.dumps(records);macro.min_zoom=min_zoom
    macro._template=Template('''{% macro script(this, kwargs) %}
    (function(){
        var map={{this.map_name}}, labels={{this.group_name}}, points={{this.records|safe}};
        function drawLabels(){
            labels.clearLayers();
            if(map.getZoom()<{{this.min_zoom}})return;
            var bounds=map.getBounds().pad(0.05);
            points.forEach(function(p){
                if(!bounds.contains([p.lat,p.lon]))return;
                var text=(p.address?'Address: '+p.address:'No mapped address inside')+'<br>Census block '+p.id.slice(-4);
                L.marker([p.lat,p.lon],{interactive:false,keyboard:false,icon:L.divIcon({
                    className:'empath-block-label',iconSize:[190,36],iconAnchor:[95,18],
                    html:'<div style="pointer-events:none;text-align:center;background:rgba(255,255,255,.9);border:1px solid #aaa;border-radius:3px;padding:2px;font:10px Arial;color:#111">'+text+'</div>'
                })}).addTo(labels);
            });
        }
        map.on('zoomend moveend',drawLabels);drawLabels();
    })();
    {% endmacro %}''')
    macro.add_to(view)
    return group


def main():
    out=ROOT/'output/clean_deliverables'
    blocks=add_location_fields(gpd.read_file(out/'block_environment.gpkg'))
    blocks.to_file(out/'block_environment.gpkg',driver='GPKG',index=False)
    blocks.to_crs(4326).to_file(out/'block_environment.geojson',driver='GeoJSON',index=False)
    blocks.drop(columns='geometry').to_csv(out/'block_environment.csv',index=False)
    print(f'Added block coordinates and lookup links to {len(blocks)} records.')

if __name__=='__main__':main()
