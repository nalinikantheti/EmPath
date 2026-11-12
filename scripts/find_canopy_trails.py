"""Locate candidate shaded bike-path sections using official trails and 2021 canopy."""
from pathlib import Path
import json
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import normalize
import folium
from branca.colormap import linear
from environment_pipeline import zonal_summary
from carto_basemap import add_basemap
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/trail_finder'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
    trails=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/trails.gpkg').to_crs(26914)
    trails=trails[trails.users.fillna('').str.contains('Bikes',case=False)&~trails.trail_name.fillna('').str.contains('golf|cart path',case=False)].copy()
    trails['_geom']=trails.geometry.map(lambda g:normalize(g).wkb_hex)
    trails=trails.drop_duplicates(['trail_name','_geom'])
    pieces=gpd.overlay(trails[['trail_name','source_id','users','geometry']],scope[['ZCTA5','geometry']],how='intersection',keep_geom_type=True).explode(index_parts=False).reset_index(drop=True)
    pieces['section_length_m']=pieces.length
    corridors=pieces[['geometry']].copy();corridors.geometry=corridors.buffer(10)
    stats=zonal_summary(corridors,ROOT/'output/canopy_2021/canopy_scope_2021.tif','canopy')
    pieces=pieces.join(stats)
    pieces.to_file(OUT/'bike_trail_canopy.gpkg',driver='GPKG',index=False)
    usable=pieces[pieces.canopy_mean.notna()&pieces.canopy_valid_center_fraction.ge(.8)].copy()
    usable['weighted_canopy']=usable.canopy_mean*usable.section_length_m
    groups=usable.groupby(['ZCTA5','trail_name']).agg(length_m=('section_length_m','sum'),
        weighted=('weighted_canopy','sum'),sections=('source_id','size')).reset_index()
    groups['length_weighted_mean_canopy_pct']=groups.weighted/groups.length_m
    groups.drop(columns='weighted').sort_values(['ZCTA5','length_weighted_mean_canopy_pct'],ascending=[True,False]).to_csv(OUT/'trail_summary_by_zip.csv',index=False)
    eligible=usable[usable.section_length_m.ge(100)].sort_values('canopy_mean',ascending=False)
    chosen=[]
    for code in ['75025','75024','75023','75074']:
        selected=[]
        for idx,row in eligible[eligible.ZCTA5.eq(code)].iterrows():
            midpoint=row.geometry.interpolate(.5,normalized=True)
            if any(midpoint.distance(pt)<300 for pt in selected):continue
            selected.append(midpoint);chosen.append(idx)
            if len(selected)>=4:break
    candidates=pieces.loc[chosen].copy().reset_index(drop=True)
    points=candidates.geometry.interpolate(.5,normalized=True)
    ll=gpd.GeoSeries(points,crs=26914).to_crs(4326)
    candidates['latitude']=ll.y.to_numpy();candidates['longitude']=ll.x.to_numpy()
    candidates['candidate_id']=[f'T{i+1}' for i in range(len(candidates))]
    candidates['google_maps_url']=candidates.apply(lambda r:f'https://www.google.com/maps/search/?api=1&query={r.latitude:.6f},{r.longitude:.6f}',axis=1)
    candidates['street_view_url']=candidates.apply(lambda r:f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={r.latitude:.6f},{r.longitude:.6f}',axis=1)
    candidates['location_note']='Representative point on trail section; not a verified entrance. Street View may be on a nearby street or unavailable.'
    candidates.drop(columns='geometry').to_csv(OUT/'high_canopy_candidates.csv',index=False)
    candidates.to_file(OUT/'high_canopy_candidates.gpkg',driver='GPKG',index=False)
    view=folium.Map(location=[33.07,-96.74],tiles=None,prefer_canvas=True);add_basemap(view)
    cmap=linear.YlGn_09.scale(0,100);cmap.caption='Estimated 2021 canopy cover from classes — 10 m trail corridor (%)';cmap.add_to(view)
    folium.GeoJson(json.loads(pieces[['trail_name','ZCTA5','canopy_mean','geometry']].to_crs(4326).to_json()),
        name='Municipal bike-compatible trails with canopy estimates',
        style_function=lambda f:{'color':cmap(f['properties']['canopy_mean']) if f['properties']['canopy_mean'] is not None else '#999','weight':4},
        tooltip=folium.GeoJsonTooltip(fields=['trail_name','ZCTA5','canopy_mean'],aliases=['Trail','ZIP area','Estimated 2021 canopy cover (%)']),
        popup=folium.GeoJsonPopup(fields=['trail_name','ZCTA5','canopy_mean'],aliases=['Trail','ZIP area','Estimated canopy cover from 2021 classes (%)'],localize=True)).add_to(view)
    folium.GeoJson(json.loads(scope.to_crs(4326).to_json()),name='Four ZIP boundaries',style_function=lambda f:{'color':'#444','weight':1,'fill':False,'fillOpacity':0,'interactive':False}).add_to(view)
    folium.LayerControl().add_to(view)
    b=scope.to_crs(4326).total_bounds;view.fit_bounds([[b[1],b[0]],[b[3],b[2]]]);view.save(OUT/'shaded_trail_candidates.html')
    print(candidates[['candidate_id','ZCTA5','trail_name','canopy_mean','section_length_m','latitude','longitude']].round(4).to_string(index=False),flush=True)

if __name__=='__main__':main()
