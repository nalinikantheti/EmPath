"""Apply the authenticated CARTO basemap to already-generated maps."""
import json
from pathlib import Path
import re
from carto_basemap import ROOT,tiles_url,ATTR


def main():
    url=tiles_url()
    targets=['output/clean_deliverables/combined_environment_map.html',
             'output/four_zip_walking_network/walking_scope_map_carto.html',
             'data/processed/census_blocks_2020/census_block_boundaries.html']
    for name in targets:
        p=ROOT/name
        if not p.exists():continue
        text=p.read_text();count=0
        def replace(match):
            nonlocal count
            old=json.loads(match.group(1))
            if not any(x in old for x in ['tile.openstreetmap.org','carto','global.ssl.fastly.net']):return match.group(0)
            opts=json.loads(match.group(2));opts.update(attribution=ATTR,maxZoom=19,maxNativeZoom=19);opts.pop('subdomains',None)
            count+=1
            return 'L.tileLayer(\n                '+json.dumps(url)+',\n                '+json.dumps(opts)+'\n            )'
        text=re.sub(r'L\.tileLayer\(\s*("(?:[^"\\]|\\.)*"),\s*(\{[^\n]*\})\s*\)',replace,text)
        text=text.replace('"OpenStreetMap": tile_layer_', '"CARTO Positron": tile_layer_')
        p.write_text(text)
        print(f'Updated {name}: {count} basemap layer(s). Key not displayed.')

if __name__=='__main__':main()
