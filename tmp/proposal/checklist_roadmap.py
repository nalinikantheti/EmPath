from pathlib import Path
import html,base64,zipfile,re
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
out=Path('output/roadmap_checklist');doc=Document();sec=doc.sections[0]
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1);sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.header_distance=Inches(.5)
for name in ['Normal','Title','Heading 1','Heading 2']:
 s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
 pf=s.paragraph_format;pf.line_spacing=1.15;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.first_line_indent=Inches(0)
 fonts=s.element.get_or_add_rPr().get_or_add_rFonts()
 for a in list(fonts.attrib):
  if 'Theme' in a:del fonts.attrib[a]
 for a in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+a),'Times New Roman')
for n in ['Title','Heading 1','Heading 2']:
 doc.styles[n].font.bold=True;doc.styles[n].paragraph_format.keep_with_next=True;doc.styles[n].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER if n!='Heading 2' else WD_ALIGN_PARAGRAPH.LEFT
p=sec.header.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
web=[];md=[]
def head(t,level=1):
 doc.add_paragraph(t,'Title' if level==0 else 'Heading 1' if level==1 else 'Heading 2');web.append(f'<h{level+1}>{html.escape(t)}</h{level+1}>');md.extend(['#'*(level+1)+' '+t,''])
def para(t,bold=False):
 p=doc.add_paragraph();p.paragraph_format.line_spacing=1.15;p.paragraph_format.space_after=Pt(6);p.add_run(t).bold=bold;web.append('<p>'+('<b>' if bold else '')+html.escape(t)+('</b>' if bold else '')+'</p>');md.extend([t,''])
def check(t):
 p=doc.add_paragraph();p.paragraph_format.line_spacing=1.15;p.paragraph_format.space_after=Pt(6);p.paragraph_format.left_indent=Inches(.18);p.paragraph_format.first_line_indent=Inches(-.18);p.add_run('☐ '+t)
 web.append('<p class="check">☐ '+html.escape(t)+'</p>');md.append('- [ ] '+t)
def page():doc.add_page_break();web.append('<hr class="pagebreak">');md.append('')
def link(p,label,url):
 h=OxmlElement('w:hyperlink');h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True));r=OxmlElement('w:r');pr=OxmlElement('w:rPr');fonts=OxmlElement('w:rFonts');fonts.set(qn('w:ascii'),'Times New Roman');fonts.set(qn('w:hAnsi'),'Times New Roman');pr.append(fonts);r.append(pr);t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);p._p.append(h)
def table(headers,rows,widths):
 t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Inches(w)
 border=OxmlElement('w:tblBorders')
 for n in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+n);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');border.append(e)
 t._tbl.tblPr.append(border)
 for i,val in enumerate(headers):t.rows[0].cells[i].text=val
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 for row in rows:
  cells=t.add_row().cells
  for c,val in zip(cells,row):
   if isinstance(val,tuple):link(c.paragraphs[0],val[0],val[1])
   else:c.text=str(val)
 for ri,row in enumerate(t.rows):
  nr=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(nr)
  for ci,c in enumerate(row.cells):
   c.width=Inches(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tc=c._tc.get_or_add_tcPr();m=OxmlElement('w:tcMar')
   for side in ['top','left','bottom','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:w'),'80');e.set(qn('w:type'),'dxa');m.append(e)
   tc.append(m)
   if ri==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF0');tc.append(sh)
   for p in c.paragraphs:
    p.paragraph_format.line_spacing=1;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(11);r.bold=ri==0
 doc.add_paragraph().paragraph_format.line_spacing=1
 web.append('<table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>')
 for row in rows:
  web.append('<tr>'+''.join('<td>'+('<a href="'+html.escape(v[1],quote=True)+'">'+html.escape(v[0])+'</a>' if isinstance(v,tuple) else html.escape(str(v)))+'</td>' for v in row)+'</tr>')
 web.append('</tbody></table>');md.append('| '+' | '.join(headers)+' |');md.append('| '+' | '.join(['---']*len(headers))+' |')
 for row in rows:md.append('| '+' | '.join(f'[{v[0]}]({v[1]})' if isinstance(v,tuple) else str(v) for v in row)+' |')
 md.append('')
def figure(n,filename,caption):
 p=doc.add_paragraph();p.add_run('Figure '+str(n)).bold=True;p.paragraph_format.keep_with_next=True
 p=doc.add_paragraph();p.add_run(caption).italic=True;p.paragraph_format.keep_with_next=True
 p=doc.add_paragraph();p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(out/'diagrams'/filename),width=Inches(6.4))
 data=base64.b64encode((out/'diagrams'/filename).read_bytes()).decode();web.append(f'<figure><b>Figure {n}</b><figcaption><i>{html.escape(caption)}</i></figcaption><img src="data:image/png;base64,{data}" alt="{html.escape(caption)}"></figure>');md.extend([f'![{caption}]({(out/"diagrams"/filename).resolve()})',''])
head('EmPath Roadmap and Delivery Checklist',0)
para('Python prototype • Plano 75025, 75024, 75023 and 75074 • One week • 15–18 hours')
para('Goal: compare residential access to temples, groceries and pharmacies using distance-only and environmental-friction routes.')
figure(1,'01_project_pathway.png','Project pathway and time budget')
table(['Step / suggested day','Core time','Save before moving on'],[
['1. Inventory / Day 1','0.5 h','Sources + four-area coverage checklist'],['2. Clean data / Day 1','2 h','Clean spatial inputs + quality report'],['3. Build graph / Day 2','2.5 h','Graph + access connectors + audit'],['4. Add features / Day 3','2 h','Edge features + data dictionary'],['5. Adapt GeoAI / Day 4','3 h','Working model adapter + model card'],['6. Route and rank / Day 5','1.5 h','Routes + residential rankings'],['7. Evaluate and map / Day 6','2 h','Comparison table + interactive map'],['8. Package / Day 7','1.5 h','Run instructions + five-minute slides'],['Troubleshooting / as needed','Up to 3 h','Resolve blockers; polish after core works']],[2.45,.7,3.35])
para('Time boxes guide priorities; they do not guarantee completion. Reserve extra hours for missing data, graph repairs or model compatibility.')
page();head('1 Inventory and Setup')
check('Open EmPath.code-workspace in VS Code; select .venv/bin/python and the EmPath Jupyter kernel.')
check('Read README.md, docs/CONFIRMED_SCOPE.md and docs/RELATED_PROJECTS.md. Reuse existing scripts and cleaned files.')
check('For every required layer, mark each ZIP: downloaded / partial / available online / unverified.')
check('Record source link, vintage, resolution, format, license/access terms, intended use and local file path.')
para('Save: docs/DATA_SOURCES.md and docs/COVERAGE_CHECKLIST.md. Done: every required input has a status and next action.',True)
head('2 Acquire and Clean Data')
table(['Input / priority','Source ID','Required check'],[
['Study boundary / required','D1','All four ZCTAs; distinguish ZIPs from ZCTAs'],['Walking network / required','D2 + OSM','Roads alone do not establish sidewalks or crossings'],['Residential origins / required','D3','Verify residential use and plausible entrances'],['Destinations / required','OSM','Temple, grocery and pharmacy; verify category/access'],['Edge canopy / required for canopy scenario','D4','Fine-scale coverage; NoData and 2021 vintage'],['Behavioral evidence / if used','R1','Understand route alternatives and choice labels'],['Neighborhood canopy / context','D5','Use for context, not as sidewalk shade']],[2.2,1,3.3])
check('Run .venv/bin/python scripts/clean_data.py --zipcodes 75025 75024 75023 75074; retain raw snapshots.')
check('Use GeoPandas, pandas, requests and Shapely: validate IDs/geometry, flag duplicates, preserve missing values; use EPSG:26914 for metric operations.')
check('Select roughly 5–10 verified residential origins per ZIP. Use OSMnx for destination candidates; verify names and access points. Missing OSM tags do not establish missing facilities.')
para('Save: cleaned GeoPackages, origins.gpkg, destinations.gpkg and quality_report.md. Done: coverage and unresolved gaps are documented for all four areas.',True)
page();head('3 Build and Audit the Walking Graph')
check('Use OSMnx graph_from_polygon(network_type="walk", retain_all=True); start with the four-ZCTA union plus roughly 500 m context. Expand if routes are truncated.')
check('Save the original GraphML. Inspect against Plano sidewalks and trails; do not turn sidewalk polygon boundaries into route edges.')
check('Attach origins/destinations at plausible pedestrian access points. Check nearest-node connectors for fences, inaccessible entrances and major-road crossings.')
check('Record connected components and disconnected origins. Preserve unreachable results; add trail connections only after checking topology, access and duplicates.')
para('Tools: OSMnx, NetworkX, GeoPandas, Folium. References: Street Shadow (R2); UNA architecture (R5).',True)
para('Save: walking_graph.graphml, access_connectors.gpkg, network_audit.md. Done: inspect at least one plausible route per ZIP.')
head('4 Add Environmental Features')
check('Acquire a manageable clip of Texas 2021 canopy (D4); use Rasterio and NumPy to sample a documented edge corridor, initially a 10 m buffer.')
check('Store edge ID, length_m, canopy_fraction, valid_pixel_fraction, feature vintage and verified crossing constraints. Keep unknown values flagged.')
check('Check feature ranges and missingness by ZIP. Canopy is a proxy; do not describe it as time-specific shade or measured heat stress.')
check('Add traffic, weather, imperviousness or modeled shadows only after core features work. Neighborhood Tree Equity Score values remain contextual.')
para('Save: edge_features.gpkg and docs/DATA_DICTIONARY.md. Done: each scoring feature has units, provenance and missingness checks.',True)
page();head('5 Reuse and Adapt One GeoAI Component')
figure(2,'02_system_architecture.png','Separate environmental prediction from routing and residential ranking')
table(['Option','Use when','Evidence to save'],[
['Existing environmental model','Runnable model + compatible public inputs are available','Model/version, prediction samples and local feature checks'],['Released route-choice analysis (R1)','Investigating shade–distance preferences','Reproduced notebook, parameters and transfer limitations'],['XGBoost or LightGBM adaptation','An existing suitable workflow and observed labels are available','Prediction target, inputs and held-out performance']],[1.7,2.4,2.4])
check('Choose ONE path. Reuse published code or pretrained weights; no new architecture or training from scratch is required.')
check('Write: model name/version; inputs; predicted quantity; original training geography; adaptation; role in edge costs; license.')
check('For Singapore choices, reproduce the released analysis; split by participant when fitting/evaluating. Treat it as behavioral calibration, not automatically deep learning.')
check('Check the event’s GeoAI requirement. A precomputed ML canopy product is an input, not a newly implemented model.')
check('Separate route predictions from additive edge costs. Label manual penalties as assumptions; do not claim learned weights for unobserved factors.')
para('Save: model adapter/notebook and docs/MODEL_CARD.md. Done: the model runs, outputs are checked and reuse is explicit. Record any unresolved GeoAI gap.',True)
page();head('6 Calculate Routes and Rank Origins')
check('Define nonnegative additive edge costs. State units, model-derived terms and scenario assumptions. Applying a sunlight preference to canopy requires an explicit transfer assumption.')
check('Use NetworkX Dijkstra-based routing twice: distance-only baseline and environmental-friction costs.')
check('For each origin, select the lowest-cost reachable destination within each of the three categories. Destinations need not occur in every ZIP; retain surrounding network context.')
check('Rank by an equal-weight sum of the three category costs. Flag missing/unreachable categories; do not rank incomplete origins as fully accessible.')
para('Tools: NetworkX, OSMnx, pandas, GeoPandas. References: Street Shadow (R2), CoolWalks (R3), Walk Score framing (R6).',True)
para('Save: routes.gpkg and residential_rankings.csv with origin/ZIP, destination IDs, distances, category costs, total cost and reachability.')
head('7 Evaluate and Build the Map')
check('Audit at least one route per ZIP and one major crossing; inspect connectors, access and suspicious jumps.')
check('Compare one baseline/alternative route pair: distance, canopy proxy and modeled cost. Test two plausible penalty settings; record ranking changes without forcing a preferred result.')
check('Evaluate model predictions separately. Performance on foreign observations does not establish accuracy for Plano pedestrians.')
check('Use Folium layer controls, markers, tooltips and popups for boundaries, origins, destination categories and route comparisons. Precompute results; use matplotlib for presentation figures.')
check('Use Streamlit only if interactive Python queries are essential and time remains. Prepare screenshots; basemap tiles can still require internet.')
para('Save: output/empath_demo.html, evaluation.csv and docs/LIMITATIONS.md. Done: a viewer can see which origin ranks better and why. References: LA study (R4), City Health Dashboard (R6).',True)
page();head('8 Package and Present')
check('Update README.md: installation, interpreter/kernel, execution order, data retrieval, source attribution and model/library versions.')
check('Verify the demo loads from a fresh session. Cache computed outputs and preserve a screenshot or recording backup.')
check('Prepare five-minute slides: problem/user → data/scope → graph/GeoAI → demo/finding → limitations/next steps.')
check('Disclose coverage gaps, proxy assumptions and geographic transfer. Environmental accessibility does not certify safety or medical suitability.')
head('Final Handoff Checklist')
table(['Deliverable','Completion test'],[
['Sources + coverage checklist','Links, vintages, status and limitations for all four ZIP areas'],['Clean inputs + quality report','Raw provenance retained; geometry/schema gaps documented'],['Graph + edge features','Audited connections; stable IDs; missing values flagged'],['Model adapter + model card','Runs; reuse is attributed; target and limitations explained'],['Routes + rankings + evaluation','Three category costs; distance baseline; unreachable results retained'],['Demo + code + README','Loads reproducibly; dependencies and run sequence documented'],['Slides + backup','Fits five minutes; demonstration survives a live-download failure']],[2.3,4.2])
head('Scope and Teamwork Rules')
check('Keep all four study areas. Reduce sampled origins, optional features or scenarios before expanding the model or interface.')
check('Use up to three additional hours for blockers and polish. Never replace missing evidence with fabricated values.')
check('Optional teammate: own either network/data QA or model evaluation; return a file and a documented check. ArcGIS Pro review is optional; exchange GeoPackage/GeoJSON.')
check('Future work: local validation, detailed crossings/traffic, time-dependent heat/shade and point-to-point lowest-friction navigation.')
page();head('Source and Reference Key')
para('Use the links below at the numbered steps. Existing project bibliography: docs/RELATED_PROJECTS.md and docs/resources.md.')
table(['ID','Source link','Use / limitation'],[
['D1',('Census ZCTA boundaries','https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2'),'Study boundary; ZCTAs approximate postal ZIPs'],
['D2',('Plano sidewalk surfaces','https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0'),'Polygon inventory; not routing edges'],
['D2',('Plano trail centerlines','https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0'),'Candidate walking connections; verify access'],
['D3',('Plano address points','https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0'),'Origin candidates; verify residential use/entrance'],
['D3',('Plano parcels','https://maps.planogis.org/arcgiswad/rest/services/OpenData/Parcels/FeatureServer/1'),'Supporting geometry; not residential classification'],
['D4',('Texas 2021 canopy raster','https://zenodo.org/records/8200761'),'10 m canopy proxy; substantial download may be needed'],
['D5',('Tree Equity Score','https://www.treeequityscore.org/methodology?tab=data-download'),'Neighborhood context, not sidewalk shade'],
['OSM',('OSMnx user reference','https://osmnx.readthedocs.io/en/stable/user-reference.html'),'Walking graph and destination queries; local completeness varies']],[.5,2.15,3.85])
table(['ID','Case study / implementation','What to reuse'],[
['R1',('Melnikov et al. (2022), study','https://doi.org/10.1038/s41598-022-06383-5'),'Observed shade–distance route choices; geographic transfer uncertain'],
['R1',('Singapore public data and code','https://osf.io/aj4vk/'),'Released analysis notebook; inspect data definitions'],
['R2',('Street Shadow Python repository','https://github.com/jlgonrod/street_shadow'),'modules/graphs.py: shade fractions, weights and routing; manual preference parameter'],
['R3',('CoolWalks, Wolf et al. (2025)','https://www.nature.com/articles/s41598-025-97200-2'),'Shade-sensitive costs and comparisons; code is Julia'],
['R4',('LA sidewalk heat study, Colaninno et al.','https://doi.org/10.1177/23998083241280746'),'Homes-to-essentials heat/accessibility framing; full workflow uses QGIS'],
['R5',('UNA Python repository','https://github.com/City-Form-Lab/urban_network_analysis'),'Origin/destination architecture; optional reference, not another required dependency'],
['R6',('Walk Score methodology','https://www.walkscore.com/methodology.shtml'),'Amenity-access score framing; not heat labels'],
['R6',('City Health Dashboard','https://www.cityhealthdashboard.com/metric/walkability'),'Context and map communication; walkability uses Walk Score']],[.5,2.5,3.5])
table(['Tool','Documentation','Purpose'],[
['NetworkX',('Shortest paths','https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html'),'Weighted routing'],['Rasterio',('Windowed raster reads','https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html'),'Feature extraction; requires readable raster, not just ZIP URL'],['Folium',('Mapping user guide','https://python-visualization.github.io/folium/latest/user_guide.html'),'Interactive HTML map']],[1.15,2,3.35])
para('Core libraries: GeoPandas, pandas, Shapely, requests, NumPy, OSMnx, NetworkX, Rasterio, Folium and matplotlib. Add model-specific libraries only after selecting the model. Implementation remains Python-based.')
for p in doc.paragraphs:
 for r in p.runs:r.font.name='Times New Roman'
doc.core_properties.title='EmPath Roadmap and Delivery Checklist';doc.core_properties.author='Nalini Kantheti';doc.save(out/'EmPath_Checklist_Roadmap.docx')
style='body{font:12pt/1.35 "Times New Roman",serif;max-width:7in;margin:36px auto;padding:0 20px}h1,h2,h3{font-size:12pt;margin:18px 0 8px;font-weight:bold}h1{text-align:center}p{margin:5px 0}.check{padding-left:20px;text-indent:-20px}table{border-collapse:collapse;width:100%;font:11pt/1.3 "Times New Roman",serif;margin:12px 0 20px}td,th{border:1px solid #d9d9d9;padding:8px;text-align:left;vertical-align:middle}th{background:#e8edf0}figure{margin:16px 0}img{width:100%;height:auto}a{overflow-wrap:anywhere}.pagebreak{border:0;margin:24px 0}'
(out/'EmPath_Checklist_Copy_Paste.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>EmPath Roadmap Checklist</title><style>'+style+'</style></head><body>'+''.join(web)+'</body></html>')
(out/'EmPath_Checklist_Roadmap.md').write_text('\n'.join(md))
with zipfile.ZipFile(out/'EmPath_Diagram_Images.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((out/'diagrams').glob('*.png')):z.write(p,p.name)
print('Created checklist document, HTML, Markdown and diagram images.')
