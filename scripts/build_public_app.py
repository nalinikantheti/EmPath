"""Plain-language frontend over the same saved costs and exact route engine."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src'
def publish(raw):
 if 'href="map-help.css"' not in raw:raw=raw.replace('</head>','<link rel="stylesheet" href="map-help.css"></head>')
 if 'src="map-help.js"' not in raw:raw=raw.replace('</body>','<script src="map-help.js"></script></body>')
 (DEST/'research.html').write_text(raw,encoding='utf-8')
 match=re.search(r'const DATA=(.*?);const map=',raw,re.S)
 payload=json.loads(match.group(1));payload['county']=None;payload['county_blocks']=''
 raw_public=raw[:match.start(1)]+json.dumps(payload)+raw[match.end(1):]
 html=raw_public.replace('<body>','<body data-public="true">').replace('<title>EmPath · Choose your walking needs</title>','<title>EmPath · Find your everyday walks</title>')
 html=html.replace('</head>', '<link rel="stylesheet" href="public.css"><script>window.empathPublic=true;window.empathTutorialRequested=new URLSearchParams(location.search).has("tutorial");</script></head>')
 a=html.index('<aside>');z=html.index('<div id="categories"',a)
 header='''<aside><nav class="app-nav"><a class="brand" href="index.html">EmPath<span>Plano</span></a><a href="guide.html">How to use</a></nav><h1>Find your everyday walks.</h1><p>A place can be nearby and still be hard to reach without a car. Choose what matters, then see the walk.</p><h2>1. What do you want nearby?</h2><div class="buttons"><button id="essential" class="primary">Groceries, pharmacy & park</button><button id="clear">Clear</button><button id="all" hidden>All</button></div><label for="scope" hidden>Study area</label><select id="scope" hidden><option value="pilot">City of Plano</option><option value="county">County preview</option></select><div id="county-notice" hidden></div>'''
 html=html[:a]+header+html[z:]
 marker='<div id="categories" class="categories"></div>'
 html=html.replace(marker,marker+'''<h2>2. Explore an area</h2><details id="route-instructions" class="route-help"><summary>How to show and remove walking routes</summary><ol><li>Choose the destination types you want nearby.</li><li>Select an area on the map or find a Plano street address. EmPath generates routes to the lowest-effort mapped destination in each category.</li><li>Select a destination card to focus on its route.</li><li>Use <strong>Remove route</strong> on a card to remove that path, or <strong>Clear routes</strong> on the map to remove all paths. Your location stays selected.</li><li>Use <strong>Show route</strong> or <strong>Show routes</strong> to bring the paths back. <strong>Clear location</strong> resets the location and its routes.</li></ol></details><form id="address-form"><label for="address-input">Have a prospective address? (Optional)</label><div class="address-row"><input id="address-input" type="search" autocomplete="street-address" placeholder="Street address in Plano" maxlength="200"><button type="submit">Find</button></div></form><p id="address-status" class="subtle" aria-live="polite">Or select an area on the map. Results describe neighborhoods, not homes for sale.</p>''')
 # Default essentials are user-neutral; all worship categories remain selectable.
 html=html.replace("let selected=['hindu_temple','supermarket','pharmacy']", "let selected=['supermarket','pharmacy','park']").replace("preset(['hindu_temple','supermarket','pharmacy'])","preset(['supermarket','pharmacy','park'])")
 html=html.replace("hindu_temple:'Hindu temples (candidate catalog)'","hindu_temple:'Hindu temples'").replace("supermarket:'Grocery stores / supermarkets'","supermarket:'Grocery stores'")
 html=html.replace('window.empathContext={map,blocks,lookup,pois,layer,labels,','window.empathContext={publicMode:true,map,blocks,lookup,pois,layer,labels,')
 a=html.index("el('summary').textContent=selected.length?");z=html.index(';const params=new URLSearchParams()',a)
 html=html[:a]+'''el('summary').textContent=selected.length?`${scores.complete.toLocaleString()} of ${blocks.features.length.toLocaleString()} Plano areas compared for your ${selected.length} selected places.`:'Choose at least one type of place to begin.';el('legend').innerHTML='<b>Walking effort · across Plano</b><div class="ramp"></div>Blue: lower → red: higher<br><small>Colors compare average effort for your selected places.<details><summary>What does gray mean?</summary>Incomplete route data for one or more selected places. Colors rescale with your selection and do not indicate safety.</details></small>' '''+html[z:]
 html=html.replace("if(query.get('scope')==='county')el('scope').value='county';",'')
 html=html.replace("function preset(cats)","window.empathRefresh=update;\nfunction preset(cats)")
 html=html.replace("if(!selected.includes(p.category))continue;","if(window.empathPublic||!selected.includes(p.category))continue;")
 html=html.replace('Copy this selection’s link','Share this view').replace('Download block scores','Download area scores')
 html=html.replace('<button id="download">','<button id="download" hidden>')
 a=html.index('<p><a href="index.html">All project maps</a>');z=html.index('</aside>',a)
 html=html[:a]+'''<footer class="app-footer"><a href="context.html">Compare population & housing</a> · <a href="guide.html">How to use</a><div class="app-help-actions"><button id="replay-tutorial" type="button" disabled>Tutorial</button><button id="open-methodology" type="button" disabled>Methodology</button></div><p class="subtle">Neighborhood estimates, not available listings or turn-by-turn navigation. Check entrances, crossings and access before walking.</p></footer>'''+html[z:]
 html=html.replace('<script src="routes.js">','<script src="public.js"></script><script src="routes.js">')
 (DEST/'app.html').write_text(html,encoding='utf-8')
 return DEST/'app.html'
if __name__=='__main__':print(publish((DEST/'research.html').read_text(encoding='utf-8')))
