"""Explicit scenario index, not a learned score or measured walking danger."""
from pathlib import Path
import json
import geopandas as gpd
import folium
from branca.colormap import linear
from branca.element import MacroElement,Template
from prepare_friction_features import normalize_features,scenario_score
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/combined_block_index'

def calculate(blocks,canopy_weight=.5,traffic_weight=.5):
    result=normalize_features(blocks)
    result['combined_burden_0_100']=100*scenario_score(result,canopy_weight,traffic_weight)
    total=canopy_weight+traffic_weight
    result['canopy_weight']=canopy_weight/total
    result['traffic_weight']=traffic_weight/total
    return result

def add_layer(view,blocks,other_layers=()):
    blocks=calculate(blocks).to_crs(4326)
    scale=linear.YlOrRd_09.scale(0,100)
    group=folium.FeatureGroup(name='Earlier two-factor baseline — canopy deficit + traffic',show=False)
    fields=['GEOID20','combined_burden_0_100','canopy_mean','traffic_index_0_100']
    def style(f):
        value=f['properties']['combined_burden_0_100']
        return {'fillColor':'#ccc' if value is None else scale(value),'fillOpacity':.78,'color':'#777','weight':.2}
    folium.GeoJson(json.loads(blocks[fields+['geometry']].to_json()),style_function=style,
        tooltip=folium.GeoJsonTooltip(fields=fields,aliases=['Census block','Walking-friction index (0–100; assumed equal weights)','Estimated canopy cover (%)','Traffic index (0–100)'],localize=True)).add_to(group)
    group.add_to(view)
    legend='<div id="empath-combined-legend" style="display:none;position:fixed;bottom:125px;right:20px;z-index:9999;background:white;padding:12px;max-width:310px;font:12px sans-serif"><b>Provisional walking-friction index</b><div style="height:14px;background:linear-gradient(to right,#ffffcc,#fd8d3c,#800026)"></div>0: lower burden → 100: higher burden<br>50% canopy deficit + 50% traffic.<br>Scenario weights, not learned or validated.<br>Gray = one or both inputs missing.<br>Regional weather is not a separate spatial factor.</div>'
    view.get_root().html.add_child(folium.Element(legend))
    macro=MacroElement();macro.map_name=view.get_name();macro.layer=group.get_name();macro.others=[x.get_name() for x in other_layers]
    macro._template=Template('''{% macro script(this, kwargs) %}
    var combinedPeers=[{% for name in this.others %}{{name}}{% if not loop.last %},{% endif %}{% endfor %}];
    function combinedLegend(){document.getElementById('empath-combined-legend').style.display={{this.map_name}}.hasLayer({{this.layer}})?'block':'none';}
    {{this.map_name}}.on('overlayadd',function(e){
      if(e.layer==={{this.layer}}){combinedPeers.forEach(function(l){ {{this.map_name}}.removeLayer(l); });}
      else if(combinedPeers.indexOf(e.layer)>=0){ {{this.map_name}}.removeLayer({{this.layer}}); }
      combinedLegend();
    });
    {{this.map_name}}.on('overlayremove',combinedLegend);combinedLegend();
    {% endmacro %}''');macro.add_to(view)
    return group

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    blocks=calculate(gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg'))
    blocks.to_file(OUT/'combined_blocks.gpkg',driver='GPKG',index=False)
    blocks.to_crs(4326).to_file(OUT/'combined_blocks.geojson',driver='GeoJSON',index=False)
    blocks.drop(columns='geometry').to_csv(OUT/'combined_blocks.csv',index=False)
    meta={'formula':'100 * (0.5 * (1 - canopy_mean/100) + 0.5 * traffic_index_0_100/100)',
          'meaning':'Higher = less canopy and/or more nearby traffic; not measured danger or personal comfort.',
          'weights':'Explicit equal-weight scenario; no AI fitted these weights.',
          'missing':'Unknown if either required input is missing; never treated as zero.',
          'weather':'Shared regional weather excluded from spatial score.',
          'blocks':len(blocks),'complete_scores':int(blocks.combined_burden_0_100.notna().sum())}
    (OUT/'method.json').write_text(json.dumps(meta,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10,8))
    blocks.plot(column='combined_burden_0_100',ax=ax,cmap='YlOrRd',vmin=0,vmax=100,legend=True,linewidth=0,missing_kwds={'color':'#ccc'},legend_kwds={'label':'Combined burden (0–100)','shrink':.7})
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(blocks.crs)
    scope.boundary.plot(ax=ax,color='#333',linewidth=.8)
    for _,r in scope.iterrows():
        pt=r.geometry.representative_point();ax.text(pt.x,pt.y,str(r.ZCTA5),ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
    ax.set_title('Provisional walking-friction index — assumed equal weights');ax.set_axis_off()
    fig.text(.05,.035,'50% canopy deficit + 50% traffic. Higher = more burden. Gray = missing.\nScenario index, not AI-learned, measured shade, or validated pedestrian danger.',fontsize=9)
    fig.savefig(OUT/'combined_block_burden.png',dpi=200,bbox_inches='tight');plt.close(fig)
    print(json.dumps(meta,indent=2))
    return blocks
if __name__=='__main__':main()
