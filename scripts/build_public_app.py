"""Plain-language frontend over the same saved costs and exact route engine."""
from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src'
def publish(raw):
 (DEST/'research.html').write_text(raw)
 match=re.search(r'const DATA=(.*?);const map=',raw,re.S)
 payload=json.loads(match.group(1));payload['county']=None;payload['county_blocks']=''
 raw_public=raw[:match.start(1)]+json.dumps(payload)+raw[match.end(1):]
 html=raw_public.replace('<body>','<body data-public="true">').replace('<title>EmPath · Choose your walking needs</title>','<title>EmPath · Find your everyday walks</title>')
 html=html.replace('</head>', '<link rel="stylesheet" href="public.css"><script>window.empathPublic=true;window.empathBudget=[10,20,30].includes(Number(new URLSearchParams(location.search).get("budget")))?Number(new URLSearchParams(location.search).get("budget")):20;</script></head>')
 a=html.index('<aside>');z=html.index('<div id="categories"',a)
 header='''<aside><nav class="app-nav"><a class="brand" href="index.html">EmPath<span>Plano</span></a><a href="guide.html">How to use</a></nav><h1>Find your everyday walks.</h1><p>A place can be nearby and still be hard to reach without a car. Choose what matters, then see the walk.</p><h2>1. What do you want nearby?</h2><div class="buttons"><button id="essential" class="primary">Groceries, pharmacy & park</button><button id="clear">Clear</button><button id="all" hidden>All</button></div><label for="scope" hidden>Study area</label><select id="scope" hidden><option value="pilot">City of Plano</option><option value="county">County preview</option></select><div id="county-notice" hidden></div>'''
 html=html[:a]+header+html[z:]
 marker='<div id="categories" class="categories"></div>'
 html=html.replace(marker,marker+'''<div class="budget"><label for="walk-budget"><strong>2. Set a walking-effort budget</strong></label><select id="walk-budget"><option value="10">10 effort minutes per destination</option><option value="20">20 effort minutes per destination</option><option value="30">30 effort minutes per destination</option></select><details class="explain"><summary>How is this different from walking time?</summary><p>We start with distance, then add an allowance for heat, limited tree cover and nearby traffic. This is a summer-focused comparison, not live weather. A 10-minute walk can use more than 10 effort minutes. Each route also shows its ordinary walking time. These are estimates, not personal health or safety advice.</p></details></div><h2>3. Explore an area</h2><form id="address-form"><label for="address-input">Have a prospective address? (Optional)</label><div class="address-row"><input id="address-input" type="search" autocomplete="street-address" placeholder="Street address in Plano" maxlength="200"><button type="submit">Find</button></div></form><p id="address-status" class="subtle" aria-live="polite">Or select an area on the map. Results describe neighborhoods, not homes for sale.</p>''')
 # Default essentials are user-neutral; all worship categories remain selectable.
 html=html.replace("let selected=['hindu_temple','supermarket','pharmacy']", "let selected=['supermarket','pharmacy','park']").replace("preset(['hindu_temple','supermarket','pharmacy'])","preset(['supermarket','pharmacy','park'])")
 html=html.replace("hindu_temple:'Hindu temples (candidate catalog)'","hindu_temple:'Hindu temples'").replace("supermarket:'Grocery stores / supermarkets'","supermarket:'Grocery stores'")
 start=html.index('function computeScores(');end=html.index('\n(async()=>',start)
 html=html[:start]+'''function computeScores(features,lookup,selected){const rows={},means=[];for(const f of features){const p=f.properties,id=p.GEOID20,choices=selected.map(c=>lookup[id]?.[c]);const valid=selected.length>0&&choices.every(r=>r&&Number.isFinite(r.min_friction_equivalent_minutes));const mean=valid?choices.reduce((s,r)=>s+r.min_friction_equivalent_minutes,0)/selected.length:null;const coverage=Number(p.boundary_exit_lower_bound_min)>window.empathBudget;const withinBudget=valid&&coverage&&Number(p.HU100)>0&&p.access_snap_gap_m<=100&&choices.every(r=>r.min_friction_equivalent_minutes<=window.empathBudget);rows[id]={mean,sum:mean==null?null:mean*selected.length,reached:choices.filter(r=>r&&Number.isFinite(r.min_friction_equivalent_minutes)).length,score:null,withinBudget,coverage};if(withinBudget)means.push(mean)}means.sort((a,b)=>a-b);const lo=means.length?quantile(means,.02):null,hi=means.length?quantile(means,.98):null;for(const r of Object.values(rows))if(r.withinBudget)r.score=hi>lo?100*Math.max(0,Math.min(1,(r.mean-lo)/(hi-lo))):0;return{rows,lo,hi,complete:means.length}}''' + html[end:]
 html=html.replace('window.empathContext={map,blocks,lookup,pois,layer,labels,','window.empathContext={publicMode:true,map,blocks,lookup,pois,layer,labels,')
 a=html.index("el('summary').textContent=selected.length?");z=html.index(';const params=new URLSearchParams()',a)
 html=html[:a]+'''el('summary').textContent=selected.length?`${scores.complete.toLocaleString()} residential areas match all ${selected.length} selected places within your ${window.empathBudget}-minute effort budget.`:'Choose at least one type of place to begin.';el('legend').innerHTML='<b>Walking effort · matching areas</b><div class="ramp"></div>Blue: lower → red: higher<br><small><details><summary>What does gray mean?</summary>Outside your budget, no 2020 housing record, or connection needs review. Colors compare this selection—not safety.</details></small>' '''+html[z:]
 html=html.replace("if(query.get('scope')==='county')el('scope').value='county';",'')
 html=html.replace("function preset(cats)","window.empathRefresh=update;\nfunction preset(cats)")
 html=html.replace("params.set('categories',selected.join(','));","params.set('categories',selected.join(','));params.set('budget',String(window.empathBudget));")
 html=html.replace("if(!selected.includes(p.category))continue;","if(window.empathPublic||!selected.includes(p.category))continue;")
 html=html.replace('Copy this selection’s link','Share this view').replace('Download block scores','Download area scores')
 html=html.replace('<button id="download">','<button id="download" hidden>')
 a=html.index('<p><a href="index.html">All project maps</a>');z=html.index('</aside>',a)
 html=html[:a]+'''<footer class="app-footer"><a href="context.html">Compare population & housing</a> · <a href="guide.html">Help</a><details><summary>Behind the map</summary><p><a href="research.html">Advanced map</a> · <a href="method.html">How scores work</a> · <a href="validation.html">Coverage & checks</a> · <a href="gallery.html">Map gallery</a></p></details><p class="subtle">Neighborhood estimates, not available listings or turn-by-turn navigation. Check entrances, crossings and access before walking.</p></footer>'''+html[z:]
 html=html.replace('<script src="routes.js">','<script src="public.js"></script><script src="routes.js">')
 (DEST/'app.html').write_text(html)
 return DEST/'app.html'
if __name__=='__main__':print(publish((DEST/'research.html').read_text()))
