"""Preserve all original layer controls while compressing embedded GeoJSON."""
from pathlib import Path
import re,json,gzip,base64
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=ROOT/'output/clean_deliverables/combined_environment_map.html';s=source.read_text();decoder=json.JSONDecoder();matches=list(re.finditer(r'geo_json_\w+_add\(\s*(\{)',s));count=0
 for m in reversed(matches):
  start=m.start(1);obj,used=decoder.raw_decode(s[start:]);payload=base64.b64encode(gzip.compress(json.dumps(obj,separators=(',',':')).encode(),compresslevel=9)).decode();s=s[:start]+'await empathDecode('+json.dumps(payload)+')'+s[start+used:];count+=1
 helper="async function empathDecode(s){const a=Uint8Array.from(atob(s),c=>c.charCodeAt(0));return JSON.parse(await new Response(new Blob([a]).stream().pipeThrough(new DecompressionStream('gzip'))).text());}\n"
 # Folium renders map setup in its final inline script; wrap that script for async data decoding.
 scripts=list(re.finditer(r'<script>(.*?)</script>',s,re.S));m=scripts[-1];body=m.group(1);s=s[:m.start(1)]+ '(async()=>{\n'+helper+body+'\n})().catch(()=>{document.body.insertAdjacentHTML("beforeend","<p>Map data could not load. Please use a current browser.</p>");});\n'+s[m.end(1):]
 out=ROOT/'output/clean_deliverables/all_layers_map.html';out.write_text(s);print('Preserved full original controls; compressed',count,'GeoJSON collections to',len(s),'characters.')
if __name__=='__main__':main()
