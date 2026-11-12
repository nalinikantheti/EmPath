"""Explicit address-based visual checks, independent of short census block codes."""
from pathlib import Path
import json
import geopandas as gpd
import folium
from branca.element import MacroElement,Template
ROOT=Path(__file__).resolve().parents[1]


def add_morada_check(view,blocks):
    cache=ROOT/'data/processed/place_checks/morada_address_point.geojson'
    if cache.exists():point=gpd.read_file(cache)
    else:
        source=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/address_points.gpkg')
        point=source[source.addrnum.astype(str).eq('1009')&source.roadname.fillna('').str.fullmatch('14TH',case=False)].copy()
        if len(point)!=1:raise ValueError('Morada address lookup is ambiguous; review municipal address points.')
        cache.parent.mkdir(parents=True,exist_ok=True)
        point[['source_id','address','zipcode','geometry']].to_crs(4326).to_file(cache,driver='GeoJSON',index=False)
    ll=point.to_crs(4326).geometry.iloc[0]
    location=point.to_crs(blocks.crs).geometry.iloc[0]
    matched=blocks[blocks.geometry.covers(location)].copy()
    if len(matched)!=1:raise ValueError('Address point does not match exactly one block.')
    row=matched.iloc[0]
    group=folium.FeatureGroup(name='Location check: Morada Plano — 1009 14th Street',show=True).add_to(view)
    popup=f'<b>Morada Plano</b><br>1009 14th Street, Plano, TX 75074<br>Census GEOID: {row.GEOID20}<br>Estimated 2021 block canopy: {row.canopy_mean:.1f}%<br>This is the address point, not an asserted entrance. The canopy value summarizes the block, not the apartment property.'
    folium.Marker([ll.y,ll.x],icon=folium.Icon(color='purple',icon='info-sign'),popup=folium.Popup(popup,max_width=380),
        tooltip=folium.Tooltip('Morada Plano — 1009 14th Street',permanent=True,direction='top')).add_to(group)
    folium.GeoJson(json.loads(matched[['GEOID20','geometry']].to_crs(4326).to_json()),
        name='Morada address block',control=False,style_function=lambda f:{'color':'#d4008f','weight':4,'fill':False,'interactive':False}).add_to(group)
    control=MacroElement();control.map_name=view.get_name();control.lat=ll.y;control.lon=ll.x
    control._template=Template('''{% macro script(this, kwargs) %}
        (function(){
            var control=L.control({position:'topleft'});
            control.onAdd=function(){
                var div=L.DomUtil.create('div','leaflet-bar');
                div.innerHTML='<button style="background:white;border:0;padding:8px;cursor:pointer;font-size:12px">Zoom to Morada Plano</button>';
                L.DomEvent.disableClickPropagation(div);
                div.firstChild.onclick=function(){ {{this.map_name}}.flyTo([{{this.lat}},{{this.lon}}],17); };
                return div;
            };
            control.addTo({{this.map_name}});
        })();
    {% endmacro %}''');control.add_to(view)
