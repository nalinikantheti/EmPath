"""Native PBF scan, retaining real OSM node identities and POI geometries."""
from pathlib import Path
import sys,json,time
import osmium
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city';w,s,e,n=json.loads((OUT/'routing_bbox.json').read_text())
POIS={'amenity':{'school','college','university','library','hospital','clinic','pharmacy','community_centre','bus_station','bank','place_of_worship'},'leisure':{'park','playground','fitness_centre','sports_centre'},'shop':{'supermarket','convenience'},'railway':{'station','halt','tram_stop'}}
def wanted(tags):return any(tags.get(k) in vals for k,vals in POIS.items())
class Extract(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.nodes={};self.ways=[];self.pois=[];self.seen=0
 def node(self,node):
  if not node.location.valid():return
  x,y=node.location.lon,node.location.lat
  if w<=x<=e and s<=y<=n:
   tags=dict(node.tags)
   if wanted(tags):self.pois.append({'type':'node','id':node.id,'tags':tags,'coordinates':[x,y]})
 def way(self,way):
  tags=dict(way.tags);road='highway' in tags;poi=wanted(tags)
  if not road and not poi:return
  self.seen+=1
  coords=[];inside=False
  for ref in way.nodes:
   if not ref.location.valid():return
   x,y=ref.location.lon,ref.location.lat;coords.append((int(ref.ref),x,y))
   if w<=x<=e and s<=y<=n:inside=True
  if not inside:return
  if road:
   self.ways.append({'type':'way','id':int(way.id),'nodes':[r[0] for r in coords],'tags':tags})
   for id,x,y in coords:self.nodes[id]={'type':'node','id':id,'lat':y,'lon':x}
  if poi:self.pois.append({'type':'way','id':int(way.id),'tags':tags,'coordinates':[[r[1],r[2]] for r in coords]})
handler=Extract();start=time.time()
handler.apply_file(str(ROOT/'data/raw/geofabrik/texas-261111.osm.pbf'),locations=True,idx='flex_mem',filters=[osmium.filter.KeyFilter('highway','amenity','shop','leisure','railway')])
result={'source':'Geofabrik Texas extract, data through 2026-11-11T21:22:47Z','elements':list(handler.nodes.values())+handler.ways,'pois':handler.pois}
(OUT/'city_osm_extract.json').write_text(json.dumps(result));print(json.dumps({'nodes':len(handler.nodes),'ways':len(handler.ways),'pois':len(handler.pois),'elapsed_seconds':time.time()-start}),flush=True)
