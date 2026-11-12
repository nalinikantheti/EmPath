"""Extract beauty retail candidates from the same frozen OSM snapshot as the graph.
Retail supplies/cosmetics are included; salons alone do not establish supply sales.
"""
from pathlib import Path
import json,time
import osmium
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city'
w,s,e,n=json.loads((OUT/'routing_bbox.json').read_text())
class Beauty(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.rows=[]
 def node(self,r):
  if r.location.valid() and w<=r.location.lon<=e and s<=r.location.lat<=n:
   self.rows.append({'type':'node','id':int(r.id),'tags':dict(r.tags),'coordinates':[r.location.lon,r.location.lat]})
 def way(self,r):
  coords=[[p.location.lon,p.location.lat] for p in r.nodes if p.location.valid()]
  if len(coords)!=len(r.nodes) or not any(w<=x<=e and s<=y<=n for x,y in coords):return
  self.rows.append({'type':'way','id':int(r.id),'tags':dict(r.tags),'coordinates':coords})
if __name__=='__main__':
 h=Beauty();start=time.time()
 h.apply_file(str(ROOT/'data/raw/geofabrik/texas-261111.osm.pbf'),locations=True,idx='flex_mem',filters=[osmium.filter.TagFilter(('shop','hairdresser_supply'),('shop','cosmetics'))])
 (OUT/'beauty_pois_raw.json').write_text(json.dumps({'source':'Geofabrik Texas OSM 2026-11-11','elements':h.rows},indent=2))
 print(json.dumps({'candidates':len(h.rows),'names':[r['tags'].get('name') for r in h.rows],'elapsed_s':time.time()-start}),flush=True)
