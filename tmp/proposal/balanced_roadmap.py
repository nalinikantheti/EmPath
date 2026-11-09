from pathlib import Path
import html,re,base64
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
out=Path('output/roadmap_guide');out.mkdir(exist_ok=True)
doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=Inches(.8);sec.left_margin=sec.right_margin=Inches(.85)
for name in ['Normal','Title','Heading 1','Heading 2','List Bullet']:
 s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
 pf=s.paragraph_format;pf.line_spacing=1.1;pf.space_after=Pt(5);pf.space_before=Pt(0)
 f=s.element.get_or_add_rPr().get_or_add_rFonts()
 for a in list(f.attrib):
  if 'Theme' in a:del f.attrib[a]
 for a in ['ascii','hAnsi','eastAsia','cs']:f.set(qn('w:'+a),'Times New Roman')
for n in ['Title','Heading 1','Heading 2']:
 doc.styles[n].font.bold=True;doc.styles[n].paragraph_format.keep_with_next=True;doc.styles[n].paragraph_format.space_before=Pt(9)
web=[];md=[]
def heading(t,title=False):
 doc.add_paragraph(t,'Title' if title else 'Heading 1');web.append('<h1>'+html.escape(t)+'</h1>' if title else '<h2>'+html.escape(t)+'</h2>');md.extend([('# ' if title else '## ')+t,''])
def para(t,bold=False):
 p=doc.add_paragraph();p.add_run(t).bold=bold;web.append('<p>'+('<b>' if bold else '')+html.escape(t)+('</b>' if bold else '')+'</p>');md.extend([t,''])
def bullet(t):
 p=doc.add_paragraph(t,'List Bullet');web.append('<li>'+html.escape(t)+'</li>');md.append('- '+t)
def linked(t,url):
 p=doc.add_paragraph();h=OxmlElement('w:hyperlink');h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True));r=OxmlElement('w:r');pr=OxmlElement('w:rPr');f=OxmlElement('w:rFonts');f.set(qn('w:ascii'),'Times New Roman');f.set(qn('w:hAnsi'),'Times New Roman');pr.append(f);size=OxmlElement('w:sz');size.set(qn('w:val'),'24');pr.append(size);c=OxmlElement('w:color');c.set(qn('w:val'),'000000');pr.append(c);r.append(pr);text=OxmlElement('w:t');text.text=t;r.append(text);h.append(r);p._p.append(h)
 web.append('<p><a href="'+html.escape(url,quote=True)+'">'+html.escape(t)+'</a></p>');md.extend([f'[{t}]({url})',''])
heading('EmPath Implementation Roadmap',True)
para('Purpose: build a Python prototype that compares residential access to temples, groceries and pharmacies using distance-only and environmental-friction routes.')
para('Scope: Plano ZIP areas 75025, 75024, 75023 and 75074, represented by Census ZCTA boundaries. Budget: one week, 15 hours of core work plus up to 3 hours for troubleshooting and polish.')
para('Minimum demonstration: approximately 5–10 verified residential origins per ZIP, individual destinations in three categories, one environmental scenario and one reused or adapted GeoAI component. Keep the four-area scope; reduce sample size or optional features if needed.')
heading('Workflow at a Glance')
rows=[['1. Inventory','0.5 h','Sources and coverage checklist'],['2. Clean inputs','2 h','Clean data and quality report'],['3. Build network','2.5 h','Walking graph and connection audit'],['4. Add features','2 h','Edge features and data dictionary'],['5. Adapt GeoAI','3 h','Model adapter and model card'],['6. Route and rank','1.5 h','Routes and residential rankings'],['7. Evaluate and map','2 h','Comparison results and interactive map'],['8. Package','1.5 h','README, slides and backup']]
t=doc.add_table(rows=1,cols=3);t.autofit=False
for c,w in zip(t.columns,[1.6,.65,4.25]):c.width=Inches(w)
for c,v in zip(t.rows[0].cells,['Step','Time','Deliverable']):c.text=v
for row in rows:
 for c,v in zip(t.add_row().cells,row):c.text=v
b=OxmlElement('w:tblBorders')
for n in ['top','bottom','left','right','insideH','insideV']:
 e=OxmlElement('w:'+n);e.set(qn('w:val'),'single');e.set(qn('w:color'),'000000');e.set(qn('w:sz'),'4');b.append(e)
t._tbl.tblPr.append(b)
for ri,row in enumerate(t.rows):
 for c in row.cells:
  for p in c.paragraphs:
   p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3);p.paragraph_format.line_spacing=1
   for r in p.runs:r.bold=ri==0
web.append('<table><tr><th>Step</th><th>Time</th><th>Deliverable</th></tr>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</table>')
md+=['| Step | Time | Deliverable |','|---|---|---|']+['| '+' | '.join(row)+' |' for row in rows]+['']
heading('1 Inventory Sources and Coverage')
bullet('Open EmPath.code-workspace in VS Code. Select .venv/bin/python and the EmPath Jupyter kernel. Read README.md and docs/CONFIRMED_SCOPE.md.')
bullet('List boundaries, walking infrastructure, residential origins, destinations, environmental features and model inputs. For each ZIP, mark coverage as downloaded, partial, available online or unverified.')
bullet('Record provider, source URL, vintage, resolution, format, reuse terms, intended use and local file. Reuse scripts/audit_walking_coverage.py for walking coverage.')
para('Tools: pandas, GeoPandas, requests. Save: sources table and four-area coverage checklist. Done when every required input has a status and next action.')
heading('2 Download and Clean Essential Inputs')
bullet('Run .venv/bin/python scripts/clean_data.py --zipcodes 75025 75024 75023 75074. Preserve raw snapshots; inspect the generated quality report.')
bullet('Check IDs, geometry, duplicates and missing values. Use EPSG:26914 for metric operations and EPSG:4326 for map display.')
bullet('Use Plano address points for a small verified residential sample. Parcels support checking but do not prove residential use or pedestrian entrances.')
bullet('Query OSM destination candidates: pharmacies, supermarkets/groceries and appropriate places of worship. Verify names, categories and access points. Missing tags do not prove that a facility is absent.')
para('Tools: GeoPandas, Shapely, pandas, requests, OSMnx. Save: cleaned GeoPackages, origins.gpkg, destinations.gpkg and quality_report.md. Done when all four areas have documented coverage or explicit gaps.')
heading('3 Build and Audit the Pedestrian Network')
bullet('Use OSMnx graph_from_polygon with network_type="walk" and retain_all=True. Start with the four-ZCTA union plus roughly 500 m surrounding context; expand if routes are truncated.')
bullet('Save the original GraphML. Compare with Plano sidewalk surfaces and trails. Sidewalk polygons are supporting data, not ready-made routing edges.')
bullet('Connect origins and destinations through plausible access points. Audit nearest-node connectors for fences, inaccessible entrances and major crossings. Record components and disconnected origins.')
bullet('Inspect at least one route per ZIP. Add municipal paths only after checking access, topology and duplicates; preserve unreachable results.')
para('Tools: OSMnx, NetworkX, GeoPandas, Folium. Reference: Street Shadow for graph-to-route structure; UNA for origin/destination architecture. Save: walking_graph.graphml, access_connectors.gpkg and network_audit.md.')
heading('4 Add Environmental Features')
bullet('Acquire a manageable clip of the Texas 2021 10 m canopy raster. Sample a documented corridor around each edge; start with a 10 m buffer and record that choice.')
bullet('Save edge ID, length_m, canopy_fraction, valid_pixel_fraction, source vintage and verified crossing constraints. Check ranges and missingness by ZIP; preserve NoData.')
bullet('Treat canopy as an environmental proxy, not time-specific shade or measured heat stress. Keep Tree Equity Score values as neighborhood context. Add weather, traffic, imperviousness or shadows only after core features work.')
para('Tools: Rasterio, NumPy, GeoPandas, Shapely. Reference: CoolWalks for shade-sensitive costs. Save: edge_features.gpkg and DATA_DICTIONARY.md. Done when every scoring feature has units, provenance and coverage checks.')
heading('5 Reuse or Adapt One GeoAI Component')
para('Choose one feasible approach: integrate an existing environmental predictor with compatible public inputs, or adapt a released shade–distance route-choice workflow. New model architecture or training from scratch is not required.')
bullet('Check that the chosen method meets the hackathon’s GeoAI requirement. Record model/version, license, input features, predicted quantity, original training geography and local adaptation.')
bullet('For the Singapore study, inspect the public data and reproduce its released analysis before modifying it. Keep participants grouped when fitting and evaluating. Behavioral calibration is not automatically deep learning.')
bullet('Use XGBoost or LightGBM only if a suitable existing workflow and meaningful observed labels are available. Install only the selected model’s dependencies.')
bullet('Keep route-level predictions separate from additive edge costs. Identify manually specified penalties as assumptions; do not claim learned preference weights for unobserved factors.')
para('Save: model adapter or notebook and MODEL_CARD.md. Done when the model runs, outputs are checked and reuse is explicit. A precomputed ML canopy product is an input, not proof of a newly implemented model; record any unresolved GeoAI gap.')
heading('How the Components Connect')
img=Path('output/roadmap_guide/EmPath_Workflow.png')
p=doc.add_paragraph();p.paragraph_format.line_spacing=1;p.add_run().add_picture(str(img),width=Inches(6.4))
data=base64.b64encode(img.read_bytes()).decode();web.append('<figure><img src="data:image/png;base64,'+data+'" alt="EmPath system architecture"></figure>');md.extend([f'![System architecture]({img.resolve()})',''])
heading('6 Calculate Routes and Residential Rankings')
bullet('Define nonnegative additive edge costs with explicit units. Separate model-derived terms from scenario assumptions. Applying sunlight preferences to canopy requires a disclosed transfer assumption.')
bullet('Use NetworkX Dijkstra-based routing for distance-only and environmental-friction scenarios. Find the lowest-cost reachable destination in each of the three categories for each origin.')
bullet('Rank origins by an equal-weight sum of category costs. Flag missing or unreachable categories; do not present incomplete origins as fully accessible. Destinations need not occur inside every ZIP.')
para('Tools: NetworkX, OSMnx, pandas, GeoPandas. References: Street Shadow, CoolWalks and Walk Score’s amenity framing. Save: routes.gpkg and residential_rankings.csv with origin/ZIP, destination IDs, distances, category costs, total cost and reachability.')
heading('7 Evaluate and Build the Demonstration')
bullet('Audit at least one route per ZIP and one major crossing. Inspect connectivity, access and suspicious jumps.')
bullet('Compare a baseline/alternative route pair using distance, canopy proxy and modeled cost. Test two plausible penalty settings and record ranking changes. Report the result even if routes do not improve.')
bullet('Evaluate the reused model separately. Performance on observations outside Plano does not establish accuracy for Plano pedestrians.')
bullet('Build one Folium map with boundaries, origins, destinations, ranked-origin popups and route alternatives. Precompute results; add Streamlit only if essential and time remains.')
para('Tools: Folium, pandas, matplotlib and model-specific evaluation tools. References: LA sidewalk heat study for research design; City Health Dashboard for communication. Save: empath_demo.html, evaluation.csv and LIMITATIONS.md. Done when a viewer can explain a ranking; prepare screenshots because basemap tiles may need internet.')
heading('8 Package and Present')
bullet('Update README.md with installation, interpreter/kernel, execution order, download instructions, attribution and tested model/library versions. Verify the demo from a fresh session.')
bullet('Prepare five-minute slides: problem and user; data and scope; graph and GeoAI; demonstration and finding; limitations and next steps. Save a backup recording or screenshots.')
bullet('Hand off sources/coverage, clean-data provenance, graph/features, model adapter/card, routes/rankings, evaluation, demo, code and slides. Reuse generated outputs rather than write a separate long report.')
para('Completion check: the demo loads reproducibly, recommendations are explainable, gaps are disclosed and the presentation fits five minutes. Environmental accessibility does not certify safety or medical suitability.')
heading('Working Rules')
bullet('Use 15 hours for the core workflow and up to 3 additional hours for blockers or polish. Reduce sampled origins or optional layers before expanding the interface or model.')
bullet('Python is the reproducible pipeline: VS Code, Jupyter and a browser. ArcGIS Pro is optional for a teammate’s review; exchange GeoPackage/GeoJSON files.')
bullet('Optional teammate: own either network/data QA or model evaluation, with a specific file and documented check to return.')
bullet('Future expansion: local preference validation, detailed crossing/traffic data, time-dependent heat/shade and point-to-point lowest-friction navigation.')
heading('Source and Reference Links')
for label,url in [
('Census ZCTA boundaries — study scope','https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2'),
('Plano sidewalks — supporting polygon inventory','https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0'),
('Plano trail centerlines — walking connections to verify','https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0'),
('Plano address points — candidate origins','https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0'),
('Plano parcels — supporting geometry','https://maps.planogis.org/arcgiswad/rest/services/OpenData/Parcels/FeatureServer/1'),
('Texas 2021 canopy — 10 m raster; download size needs planning','https://zenodo.org/records/8200761'),
('Tree Equity Score — neighborhood context','https://www.treeequityscore.org/methodology?tab=data-download'),
('Singapore behavioral study — shade–distance observations','https://doi.org/10.1038/s41598-022-06383-5'),
('Singapore data and analysis notebook — reuse and inspect','https://osf.io/aj4vk/'),
('Street Shadow — inspect modules/graphs.py; manually parameterized shade weights','https://github.com/jlgonrod/street_shadow'),
('CoolWalks — routing methodology; Julia implementation','https://www.nature.com/articles/s41598-025-97200-2'),
('LA sidewalk heat study — residential heat-accessibility framework','https://doi.org/10.1177/23998083241280746'),
('UNA — origin/destination architecture; optional reference','https://github.com/City-Form-Lab/urban_network_analysis'),
('Walk Score — amenity-access framing','https://www.walkscore.com/methodology.shtml'),
('City Health Dashboard — contextual visualization; its walkability uses Walk Score','https://www.cityhealthdashboard.com/metric/walkability'),
('OSMnx — network and destination query documentation','https://osmnx.readthedocs.io/en/stable/user-reference.html'),
('NetworkX — shortest-path documentation','https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html'),
('Rasterio — windowed reading; requires a readable raster, not only a ZIP URL','https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html'),
('Folium — interactive-map documentation','https://python-visualization.github.io/folium/latest/user_guide.html')]:linked(label,url)
para('Detailed source notes: docs/RELATED_PROJECTS.md and docs/resources.md. Core libraries: GeoPandas, Shapely, pandas, requests, NumPy, OSMnx, NetworkX, Rasterio, Folium and matplotlib. Add only the selected model’s extra dependencies.')
# Explicit formatting overrides prevent theme fonts/colors leaking into runs or links.
for p in doc.paragraphs:
 for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
for table in doc.tables:
 for row in table.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
doc.core_properties.title='EmPath Implementation Roadmap';doc.core_properties.author='Nalini Kantheti';doc.save(out/'EmPath_Implementation_Guide.docx')
css='body{font-family:"Times New Roman",serif;font-size:12pt;line-height:1.25;color:#000;max-width:7in;margin:36px auto;padding:0 20px}h1,h2,h3,p,li,a,table,th,td{font-family:"Times New Roman",serif;font-size:12pt;color:#000}h1,h2{font-weight:bold;margin:18px 0 7px}p{margin:6px 0}li{margin:5px 0 5px 20px}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #000;padding:7px;text-align:left}figure{margin:15px 0}img{max-width:100%;height:auto}a{text-decoration:underline}'
(out/'EmPath_Implementation_Guide_Copy_Paste.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>EmPath Implementation Roadmap</title><style>'+css+'</style></head><body>'+''.join(web)+'</body></html>')
(out/'EmPath_Implementation_Guide.md').write_text('\n'.join(md))
print('Created balanced guide with one table and one diagram.')
