"""Mosaic completed inference tiles and summarize coverage by block and walking edge."""
from pathlib import Path
import json,math
import full_scope_geoai as pipeline
import numpy as np,pandas as pd,geopandas as gpd,rasterio,folium
from rasterio.windows import Window,from_bounds
from rasterio.features import rasterize,geometry_mask,shapes
from rasterio.transform import from_origin
from shapely.geometry import box,mapping,shape
from shapely import normalize
from carto_basemap import add_basemap
from tree_adjacency_visuals import tree_color,legend_html
ROOT=pipeline.ROOT;OUT=pipeline.OUT

def summarize():
 cfg=json.loads((OUT/'tile_plan.json').read_text());paths=[OUT/'tiles'/(t['id']+'.tif') for t in cfg['tiles']]
 missing=[str(p) for p in paths if not p.exists()]
 if missing:raise RuntimeError(f'{len(missing)} inference tiles missing. Resume inference before making full-area claims.')
 blocks=gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg').to_crs(26914).reset_index(drop=True)
 edges=gpd.read_file(ROOT/'output/clean_deliverables/walking_edges.gpkg').to_crs(26914).reset_index(drop=True)
 corridors=gpd.GeoSeries(edges.geometry.buffer(5),crs=26914)
 bn=np.zeros(len(blocks),dtype=np.int64);bt=bn.copy();bexpected=bn.copy()
 en=np.zeros(len(edges),dtype=np.int64);et=en.copy()
 zip_scope=pipeline.scope().reset_index(drop=True);zn=np.zeros(len(zip_scope),dtype=np.int64);zexpected=zn.copy()
 polygons=[];transform=from_origin(cfg['transform'][2],cfg['transform'][5],pipeline.RES,pipeline.RES)
 mosaic=OUT/'full_scope_tree_cover.tif'
 profile=dict(driver='GTiff',width=cfg['width'],height=cfg['height'],count=1,dtype='uint8',crs=26914,transform=transform,nodata=255,tiled=True,blockxsize=512,blockysize=512,compress='deflate',BIGTIFF='IF_SAFER')
 observed=total=0
 with rasterio.open(mosaic,'w',**profile) as dst:
  for y in range(0,cfg['height'],512):
   h=min(512,cfg['height']-y);dst.write(np.full((h,cfg['width']),255,dtype='uint8'),1,window=Window(0,y,cfg['width'],h))
  for i,(tile,path) in enumerate(zip(cfg['tiles'],paths)):
   with rasterio.open(path) as src:
    mask=src.read(1);valid=mask!=255;tf=src.transform;bounds=box(*src.bounds)
    dst.write(mask,1,window=Window(tile['col'],tile['row'],tile['width'],tile['height']))
    ids=blocks.sindex.query(bounds,predicate='intersects')
    labels=rasterize([(blocks.geometry.iloc[k],int(k)+1) for k in ids],out_shape=mask.shape,transform=tf,fill=0,dtype='int32')
    bexpected+=np.bincount(labels.ravel(),minlength=len(blocks)+1)[1:]
    bn+=np.bincount(labels[valid],minlength=len(blocks)+1)[1:]
    bt+=np.bincount(labels[mask==1],minlength=len(blocks)+1)[1:]
    zip_labels=rasterize([(z.geometry,i+1) for i,z in zip_scope.iterrows()],out_shape=mask.shape,transform=tf,fill=0,dtype='int16')
    zexpected+=np.bincount(zip_labels.ravel(),minlength=len(zip_scope)+1)[1:]
    zn+=np.bincount(zip_labels[valid],minlength=len(zip_scope)+1)[1:]
    observed+=int(valid.sum())
    for k in corridors.sindex.query(bounds,predicate='intersects'):
     geom=corridors.iloc[k];minx,miny,maxx,maxy=geom.bounds
     raw=from_bounds(minx,miny,maxx,maxy,tf)
     col=max(0,math.floor(raw.col_off));row=max(0,math.floor(raw.row_off))
     endcol=min(src.width,math.ceil(raw.col_off+raw.width));endrow=min(src.height,math.ceil(raw.row_off+raw.height))
     if endcol<=col or endrow<=row:continue
     small=mask[row:endrow,col:endcol]
     zone=geometry_mask([mapping(geom)],out_shape=small.shape,transform=src.window_transform(Window(col,row,endcol-col,endrow-row)),invert=True)
     en[k]+=int((zone&(small!=255)).sum());et[k]+=int((zone&(small==1)).sum())
    for geom,value in shapes(mask,mask=mask==1,transform=tf):
     if value==1:polygons.append({'tile_id':tile['id'],'geometry':shape(geom)})
   if (i+1)%25==0:pipeline.status(stage='summarizing',summary_tiles_completed=i+1,total_tiles=len(paths))
  dst.update_tags(model='restor/tcd-segformer-mit-b0',source='USDA NAIP 2022',classes='0 not detected tree; 1 predicted tree; 255 outside scope or missing',note='not actual shade; local transfer accuracy not validated')
 blocks['ai_canopy_valid_pixels']=bn;blocks['ai_canopy_expected_pixels']=bexpected
 blocks['ai_canopy_cover_pct']=np.divide(bt*100,bn,out=np.full(len(bn),np.nan),where=bn>0)
 blocks['ai_imagery_coverage_01']=np.divide(bn,bexpected,out=np.full(len(bn),np.nan),where=bexpected>0)
 blocks['ai_full_scope_friction_0_100']=.5*(100-blocks.ai_canopy_cover_pct)+.5*blocks.traffic_index_0_100
 blocks.to_file(OUT/'ai_block_environment.gpkg',driver='GPKG',index=False)
 blocks.drop(columns='geometry').to_csv(OUT/'ai_block_environment.csv',index=False)
 edges['ai_tree_cover_01']=np.divide(et,en,out=np.full(len(en),np.nan),where=en>0)
 edges['ai_corridor_valid_pixels']=en
 edges['ai_corridor_coverage_01']=np.minimum(1,np.divide(en*pipeline.RES**2,corridors.area,out=np.zeros(len(en)),where=corridors.area>0))
 beta=json.loads((ROOT/'output/route_preference_model/model_and_evaluation.json').read_text())['full_data_extra_sun_distance_factor']
 edges['ai_canopy_proxy_cost_m']=edges['length']*(1+beta*(1-edges.ai_tree_cover_01))
 edges.to_file(OUT/'ai_walking_edges.gpkg',driver='GPKG',index=False);edges.drop(columns='geometry').to_csv(OUT/'ai_walking_edges.csv',index=False)
 gpd.GeoDataFrame(polygons,geometry='geometry',crs=26914).to_file(OUT/'predicted_tree_polygons.gpkg',driver='GPKG',index=False)
 perzip=[]
 for zi,z in zip_scope.iterrows():
  idx=blocks.geometry.representative_point().within(z.geometry)
  perzip.append({'zip':str(z.ZCTA5),'blocks':int(idx.sum()),'expected_pixels':int(zexpected[zi]),'observed_pixels':int(zn[zi]),'coverage_pct':100*zn[zi]/zexpected[zi],'blocks_with_prediction':int((idx&(bn>0)).sum())})
 pd.DataFrame(perzip).to_csv(OUT/'coverage_by_zip.csv',index=False)
 report={'inference_tiles':len(paths),'source_year':2022,'native_pixel_size_m':pipeline.RES,'scope_area_km2':float(pipeline.scope().area.sum()/1e6),'observed_pixels':observed,'blocks':len(blocks),'blocks_with_prediction':int((bn>0).sum()),'edges':len(edges),'edges_with_prediction':int((en>0).sum()),'tree_polygons':len(polygons),'coverage_by_zip':perzip,'limitations':['Tree segmentation, not measured shade or all vegetation.','10 cm model training versus 60 cm NAIP inference: local accuracy unvalidated.','5 m corridors around OSM paths may represent road centers, not exact sidewalks.','Combined friction weights remain explicit 50/50 assumptions.','Unknown observations are not imputed as zero.','Published production graph and canopy dataset unchanged; AI layers saved separately.']}
 (OUT/'coverage_report.json').write_text(json.dumps(report,indent=2))
 render(blocks,edges)
 pipeline.status(stage='aggregated',**{k:v for k,v in report.items() if k not in ['limitations','coverage_by_zip']})
 return report

def render(blocks,edges):
 scope=pipeline.scope().to_crs(4326)
 view=folium.Map(location=[33.06,-96.75],tiles=None,prefer_canvas=True);add_basemap(view)
 thematic=[]
 for column,title,colors in [('ai_canopy_cover_pct','GeoAI-predicted tree cover — NAIP 2022','YlGn'),('ai_full_scope_friction_0_100','Provisional friction — AI canopy deficit + traffic, 50/50','YlOrRd')]:
  data=blocks[['GEOID20',column,'representative_address','ai_imagery_coverage_01','geometry']].to_crs(4326)
  layer=folium.Choropleth(geo_data=json.loads(data.to_json()),data=data.drop(columns='geometry'),columns=['GEOID20',column],key_on='feature.properties.GEOID20',name=title,bins=[0,10,25,50,75,100.00001],fill_color=colors,nan_fill_color='#ccc',show=column=='ai_canopy_cover_pct',line_weight=.2,legend_name=title)
  layer.add_to(view);thematic.append(layer)
  folium.GeoJsonTooltip(fields=['GEOID20',column,'representative_address','ai_imagery_coverage_01'],aliases=['Block',title,'Representative address','Observed fraction of block pixels']).add_to(layer.geojson)
 physical=edges.loc[~edges.geometry.map(lambda g:normalize(g).wkb_hex).duplicated()].copy()
 physical['tree_adjacency_pct']=physical.ai_tree_cover_01*100
 folium.GeoJson(json.loads(physical[['u','v','key','tree_adjacency_pct','ai_tree_cover_01','ai_corridor_coverage_01','geometry']].to_crs(4326).to_json()),name='Walking paths — orange to green tree adjacency',show=False,style_function=lambda f:{'color':tree_color(f['properties'].get('ai_tree_cover_01')),'weight':2,'opacity':.9},tooltip=folium.GeoJsonTooltip(fields=['tree_adjacency_pct','ai_corridor_coverage_01'],aliases=['Predicted nearby tree cover (%)','Observed corridor coverage'])).add_to(view)
 route_path=OUT/'full_scope_routes.gpkg'
 if route_path.exists():
  routes=gpd.read_file(route_path).to_crs(4326)
  for method,pattern in [('Shortest distance','8 6'),('Distance–canopy trade-off','2 6'),('Tree-adjacency priority',None)]:
   subset=routes[routes.route==method]
   group=folium.FeatureGroup(name=method+' — four illustrative endpoint pairs',show=method=='Tree-adjacency priority')
   data=json.loads(subset.to_json())
   folium.GeoJson(data,style_function=lambda f,p=pattern:{'color':'#333','weight':7,'dashArray':p,'opacity':.8}).add_to(group)
   folium.GeoJson(data,style_function=lambda f,p=pattern:{'color':tree_color(f['properties'].get('ai_tree_cover_01')),'weight':4,'dashArray':p},tooltip=folium.GeoJsonTooltip(fields=['zip','route','ai_tree_cover_01'],aliases=['Example ZIP','Route objective','Nearby predicted tree fraction'])).add_to(group)
   group.add_to(view)
 endpoints=OUT/'illustrative_endpoints.geojson'
 if endpoints.exists():
  locations=gpd.read_file(endpoints).to_crs(4326)
  group=folium.FeatureGroup(name='Illustrative route endpoints — not verified entrances',show=True)
  for _,row in locations.iterrows():
   folium.CircleMarker(location=[row.geometry.y,row.geometry.x],radius=5,color='#111',fill=True,fill_color='white' if row.role=='Start' else '#111',fill_opacity=1,tooltip=f"{row['zip']}: {row.role}; illustrative network node {row.node_id}").add_to(group)
  group.add_to(view)
 folium.GeoJson(json.loads(scope.to_json()),name='Four ZIP boundaries',style_function=lambda f:{'color':'#333','weight':2,'fill':False,'interactive':False}).add_to(view)
 from branca.element import MacroElement,Template
 control=MacroElement();control.map_name=view.get_name();control.a=thematic[0].get_name();control.b=thematic[1].get_name();control.ca=thematic[0].color_scale.get_name();control.cb=thematic[1].color_scale.get_name()
 control._template=Template('''{% macro script(this, kwargs) %}
 function fullScopeLegends(){
  {{this.ca}}.legend.getContainer().style.display={{this.map_name}}.hasLayer({{this.a}})?'block':'none';
  {{this.cb}}.legend.getContainer().style.display={{this.map_name}}.hasLayer({{this.b}})?'block':'none';
 }
 {{this.map_name}}.on('overlayadd',function(e){
  if(e.layer==={{this.a}}){{this.map_name}}.removeLayer({{this.b}});
  if(e.layer==={{this.b}}){{this.map_name}}.removeLayer({{this.a}});
  fullScopeLegends();
 });
 {{this.map_name}}.on('overlayremove',fullScopeLegends);fullScopeLegends();
 {% endmacro %}''');control.add_to(view)
 folium.LayerControl(collapsed=False).add_to(view);view.get_root().html.add_child(folium.Element(legend_html()))
 b=scope.total_bounds;view.fit_bounds([[b[1],b[0]],[b[3],b[2]]]);view.save(OUT/'full_scope_geoai_map.html')

if __name__=='__main__':print(json.dumps(summarize(),indent=2))
