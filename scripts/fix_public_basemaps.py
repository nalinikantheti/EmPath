"""Replace CARTO tile dependencies in generated maps with standard OSM tiles."""
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
TILES='https://tile.openstreetmap.org/{z}/{x}/{y}.png'
ATTR='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'


def fix_html(text):
    count=0
    pattern=r'L\.tileLayer\(\s*("(?:[^"\\]|\\.)*"),\s*(\{[^\n]*\})\s*\)'
    def replace(match):
        nonlocal count
        url=json.loads(match.group(1))
        if 'carto' not in url:return match.group(0)
        options=json.loads(match.group(2));options['attribution']=ATTR
        options['maxZoom']=19;options['maxNativeZoom']=19;options.pop('subdomains',None)
        count+=1
        return 'L.tileLayer(\n                '+json.dumps(TILES)+',\n                '+json.dumps(options)+'\n            )'
    result=re.sub(pattern,replace,text)
    if count:result=result.replace('"cartodbpositron"','"OpenStreetMap"')
    return result,count


def main():
    changed=[]
    for path in (ROOT/'output').rglob('*.html'):
        text=path.read_text()
        if 'carto' not in text.lower():continue
        new,count=fix_html(text)
        if count:path.write_text(new);changed.append({'file':str(path.relative_to(ROOT)),'tile_layers':count})
    print(json.dumps(changed,indent=2))

if __name__=='__main__':main()
