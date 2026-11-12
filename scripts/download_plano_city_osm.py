"""Resumable small bounding-box OSM queries; filter walk access locally."""
from pathlib import Path
import json,math,time,re
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import box
import requests,geopandas as gpd,osmnx as ox
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/network';CACHE=ROOT/'data/raw/plano_city_osm_geom_5km'

def run():
 OUT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
 area=gpd.GeoSeries([city.geometry.union_all().buffer(1000)],crs=26914).to_crs(4326).iloc[0]
 w,s,e,n=area.bounds;cols=math.ceil((e-w)/.05);rows=math.ceil((n-s)/.05);elements={}
 # The prior pilot request included its full 500 m OSMnx buffer. Reuse a conservative inner 350 m region.
 pilot=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
 known_area=gpd.GeoSeries([pilot.geometry.union_all().buffer(350)],crs=26914).to_crs(4326).iloc[0]
 cached=ROOT/'data/raw/osmnx_cache/4a0a4c8c82406cbdcfd1bdca04008847c0fc67f0.json'
 if cached.exists():
  for element in json.loads(cached.read_text())['elements']:elements[(element['type'],element['id'])]=element
 tasks=[]
 for row in range(rows):
  for col in range(cols):
   xmin=w+(e-w)*col/cols;xmax=w+(e-w)*(col+1)/cols;ymin=s+(n-s)*row/rows;ymax=s+(n-s)*(row+1)/rows
   bbox=box(xmin,ymin,xmax,ymax)
   if not bbox.intersects(area):continue
   if elements and known_area.covers(bbox):
    print('Reuse previously downloaded network cell',row,col,flush=True);continue
   tasks.append((row,col,xmin,ymin,xmax,ymax))
 def fetch(task):
  row,col,xmin,ymin,xmax,ymax=task;path=CACHE/f'cell_{row}_{col}.json'
  if not path.exists():
   q=f'[out:json][timeout:25];way["highway"]({ymin:.6f},{xmin:.6f},{ymax:.6f},{xmax:.6f});out geom;'
   for attempt in range(3):
    r=requests.post('https://overpass-api.de/api/interpreter',data={'data':q},headers={'User-Agent':'EmPath academic pedestrian accessibility prototype','Accept':'application/json'},timeout=90)
    if r.status_code==200:
     d=r.json()
     if 'remark' not in d:break
    print('Cell request failure:',row,col,r.status_code,flush=True)
    if attempt==2:raise RuntimeError(f'OSM cell {row}/{col} unavailable; cached cells preserved')
    time.sleep(10*(2**attempt))
   tmp=path.with_suffix('.partial');tmp.write_text(json.dumps(d));tmp.replace(path);time.sleep(.5)
  print('Cached new network cell',row,col,flush=True)
  return json.loads(path.read_text())['elements']
 print('Additional network cells required:',len(tasks),flush=True)
 with ThreadPoolExecutor(max_workers=2) as pool:
  for fetched in pool.map(fetch,tasks):
   for el in fetched:
    elements[(el['type'],el['id'])]=el
    if el['type']=='way' and 'geometry' in el:
     for node_id,point in zip(el['nodes'],el['geometry']):
      if point is not None:elements[('node',node_id)]={'type':'node','id':node_id,'lat':point['lat'],'lon':point['lon']}
 deny=re.compile('abandoned|bus_guideway|construction|motor|no|planned|platform|proposed|raceway|razed|rest_area|services')
 allowed=[];node_ids=set()
 for el in elements.values():
  if el['type']!='way':continue
  t=el.get('tags',{});highway=t.get('highway','')
  if t.get('area')=='yes' or t.get('access') in ['private','no'] or t.get('foot')=='no' or t.get('service')=='private' or deny.search(highway):continue
  if highway=='cycleway' and t.get('foot') not in ['yes','designated','permissive']:continue
  if any(t.get(k)=='separate' for k in ['sidewalk','sidewalk:both','sidewalk:left','sidewalk:right']):continue
  allowed.append(el);node_ids.update(el['nodes'])
 selected=[el for el in elements.values() if el['type']=='node' and el['id'] in node_ids]+allowed
 ox.settings.useful_tags_way=list(dict.fromkeys(ox.settings.useful_tags_way+['foot','sidewalk','crossing','surface','access','lit','incline']))
 graph=ox.graph._create_graph([{'elements':selected}],bidirectional=True)
 graph=ox.truncate.truncate_graph_polygon(graph,area,truncate_by_edge=True)
 graph=ox.simplification.simplify_graph(graph)
 ox.save_graphml(graph,OUT/'walking_graph.graphml')
 print('City graph saved:',len(graph),'nodes;',graph.number_of_edges(),'edges',flush=True)
 return graph
if __name__=='__main__':run()
