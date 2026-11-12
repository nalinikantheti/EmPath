"""Acquire buffered Plano walking graph and service candidates, separate from pilot."""
from pathlib import Path
import json,os
import requests,geopandas as gpd,pandas as pd,osmnx as ox,networkx as nx
from shapely.geometry import Point,Polygon
from shapely import make_valid
from poi_categories import classify
from city_scope import buffer_m
ROOT=Path(__file__).resolve().parents[1];OUT=Path(os.environ.get('EMPATH_CITY_DATA_ROOT',str(ROOT/'output/plano_city')));N=OUT/'network'

def run():
 N.mkdir(parents=True,exist_ok=True)
 city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914)
 boundary=city.geometry.union_all();area=gpd.GeoSeries([boundary.buffer(float(os.environ.get('EMPATH_NETWORK_BUFFER_M',str(buffer_m()))))],crs=26914).to_crs(4326).iloc[0]
 city.to_file(OUT/'city_boundary.gpkg',driver='GPKG',index=False)
 ox.settings.use_cache=True;ox.settings.cache_folder=str(ROOT/'data/raw/osmnx_cache');ox.settings.log_console=True;ox.settings.requests_timeout=180
 ox.settings.max_query_area_size=50_000_000
 ox.settings.overpass_url="https://overpass-api.de/api"
 ox.settings.overpass_rate_limit=False
 ox.settings.useful_tags_way=list(dict.fromkeys(ox.settings.useful_tags_way+['foot','sidewalk','crossing','surface','access','lit','incline']))
 path=N/'walking_graph.graphml'
 if path.exists():graph=ox.load_graphml(path)
 else:
  graph=ox.graph_from_polygon(area,network_type='walk',simplify=True,retain_all=True,truncate_by_edge=True)
  ox.save_graphml(graph,path)
 nodes,edges=ox.graph_to_gdfs(graph)
 nodes.drop(columns='geometry').to_csv(N/'nodes.csv')
 edge_table=edges.to_crs(26914).reset_index()
 for column in edge_table.select_dtypes(include='object'):
  edge_table[column]=edge_table[column].map(lambda value:json.dumps(value) if isinstance(value,(list,dict,tuple)) else value)
 edge_table.to_file(N/'edges.gpkg',driver='GPKG',index=False)
 # Include nearby destinations outside the municipal line, within the declared buffer.
 w,s,e,n=area.bounds
 query=f'''[out:json][timeout:180];(nwr["amenity"~"^(school|college|university|library|hospital|clinic|pharmacy|community_centre|bus_station|bank)$"]({s},{w},{n},{e});nwr["leisure"~"^(park|playground|fitness_centre|sports_centre)$"]({s},{w},{n},{e});nwr["shop"~"^(supermarket|convenience|hairdresser_supply|cosmetics)$"]({s},{w},{n},{e});nwr["railway"~"^(station|halt|tram_stop)$"]({s},{w},{n},{e});nwr["amenity"="place_of_worship"]({s},{w},{n},{e}););out center tags;'''
 raw=OUT/'city_pois_raw.json'
 local=OUT/'city_osm_extract.json'
 if local.exists():
  data=json.loads(local.read_text());source_elements=data['pois']
 else:
  if not raw.exists():
   r=requests.post('https://overpass-api.de/api/interpreter',data={'data':query},timeout=240);r.raise_for_status();data=r.json()
   if data.get('remark'):raise RuntimeError('OSM response indicates incomplete query')
   raw.write_text(json.dumps(data))
  source_elements=json.loads(raw.read_text())['elements']
 supplement=OUT/'beauty_pois_raw.json'
 if supplement.exists():
  combined={(r['type'],r['id']):r for r in source_elements}
  combined.update({(r['type'],r['id']):r for r in json.loads(supplement.read_text())['elements']})
  source_elements=list(combined.values())
 rows=[]
 for r in source_elements:
  t=r.get('tags',{})
  category=classify(t)
  if category is None:continue
  if 'coordinates' in r:
   coordinates=r['coordinates']
   if r['type']=='node':point=Point(coordinates)
   else:
    geom=make_valid(Polygon(coordinates)) if len(coordinates)>=4 and coordinates[0]==coordinates[-1] else Point(coordinates[0])
    point=geom.intersection(area).representative_point() if geom.intersects(area) else geom.representative_point()
  else:
   center=r.get('center',r);point=Point(center['lon'],center['lat'])
  if point.is_empty or not area.covers(point):continue
  rows.append({'poi_id':f'osm_{r["type"]}_{r["id"]}','name':t.get('name','Unnamed mapped '+str(category)),'category':category,'religion':t.get('religion','unspecified'),'osm_element':r['type'],'osm_id':str(r['id']),'source_url':f'https://www.openstreetmap.org/{r["type"]}/{r["id"]}','address_status':'OSM mapped candidate; entrances, fees and suitability unverified','geometry':point})
 facilities=json.load(open(ROOT/'output/block_accessibility/city_facilities_raw.geojson'))
 for f in facilities['features']:
  p=f['properties'];name=p['Name'];low=name.lower();categories=[]
  if 'recreation center' in low:categories.append('recreation_centre')
  if any(x in low for x in ['pool','aquatic','natatorium']) or name in ['Carpenter Park Recreation Center','Oak Point Recreation Center']:categories.append('swimming_pool')
  point=Point(f['geometry']['coordinates'])
  if point.is_empty or not area.covers(point):continue
  for category in categories:rows.append({'poi_id':f'plano_{p["OBJECTID"]}_{category}','name':name+(' Pool' if category=='swimming_pool' and 'recreation' in low else ''),'category':category,'source_url':p.get('URL') or 'https://www.plano.gov/recreation-centers-pools','address_status':'Municipal facility candidate; eligibility, fees and entrance unverified','geometry':point})
 curated=ROOT/'config/beauty_supply_pois.geojson'
 if curated.exists():
  for f in json.loads(curated.read_text())['features']:
   point=Point(f['geometry']['coordinates'])
   if not area.covers(point):continue
   # Prefer official-address record to an OSM duplicate of the same chain nearby.
   name=f['properties']['name'].lower();chain='sally' if 'sally' in name else 'gold7'
   projected=gpd.GeoSeries([point],crs=4326).to_crs(26914).iloc[0]
   rows=[r for r in rows if not (chain in r['name'].lower().replace(' ','') and projected.distance(gpd.GeoSeries([r['geometry']],crs=4326).to_crs(26914).iloc[0])<150)]
   rows.append({**f['properties'],'geometry':point})
 pois=gpd.GeoDataFrame(rows,crs=4326);pois.to_file(OUT/'pois.gpkg',driver='GPKG',index=False)
 report={'scope':'Official Plano municipal boundary','city_area_km2':boundary.area/1e6,'routing_and_destination_buffer_m':float(os.environ.get('EMPATH_NETWORK_BUFFER_M',str(buffer_m()))),'nodes':len(graph),'directed_edges':graph.number_of_edges(),'weak_components':nx.number_weakly_connected_components(graph),'poi_candidates':len(pois),'category_counts':pois.category.value_counts().to_dict(),'limitations':'OSM walk mode is not a verified continuous sidewalk inventory; mapped POI centers are not entrances.'}
 (OUT/'network_inventory.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
