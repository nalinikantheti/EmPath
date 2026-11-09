from pathlib import Path
import re,html,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
out=Path('output/roadmap_apa');out.mkdir(exist_ok=True)
title='EmPath Implementation Roadmap and Team Guide'
sections=[
('Project Brief',[
('Goal','Compare residential access to temples, groceries, and pharmacies using distance-only and environmental-friction pedestrian routes. Cover Plano ZIP areas 75025, 75024, 75023, and 75074 using Census ZCTA boundaries.'),
('Minimum demonstration','Represent all four areas with approximately 5–10 verified residential origins per area, individual destination points, one environmental scenario, and one reused or adapted GeoAI component. Treat these counts as a sampling target, not completed work. A destination category need not occur inside every ZIP; report inaccessible or absent services honestly.'),
('Time and sequence','One week; 10 hours total. Complete Sessions 1–8 in order across the week: data and setup first, network next, environmental features and model next, routing and demonstration last. Nine hours are allocated below; reserve one hour for failures. These are time boxes, not guaranteed completion estimates.')]),
('Working Environment',[
('Software','VS Code, the project .venv Python interpreter, Jupyter notebooks, and a browser. Use Python throughout. Keep ArcGIS Pro optional for a teammate’s review; exchange GeoPackage or GeoJSON files rather than requiring an ArcGIS project.'),
('Libraries','Reuse GeoPandas, pandas, requests, matplotlib, Folium, and ipykernel. Add OSMnx and NetworkX for graph work; Rasterio and NumPy for raster features. Add scikit-learn, statsmodels, joblib, XGBoost, or LightGBM only when required by the selected existing model. Record tested versions; do not install every alternative.'),
('Existing entry points','Read README.md, docs/CONFIRMED_SCOPE.md, docs/resources.md, and docs/RELATED_PROJECTS.md. Reuse scripts/clean_data.py, scripts/audit_walking_coverage.py, and notebooks/02_data_cleaning.ipynb. The output files named below are planned deliverables, not a claim that they already exist.')]),
('Session 1 Data Inventory and Setup 30 Minutes',[
('Actions','Open EmPath.code-workspace; select .venv/bin/python and the EmPath notebook kernel. Inventory boundaries, walking infrastructure, residential origins, destinations, environmental features, and model inputs. Mark each dataset downloaded, partial, available online, or unverified for each ZIP.'),
('Tools and sources','VS Code, Jupyter, pandas, GeoPandas, and requests. Use Census boundaries and the Plano GIS services listed under Data Sources.'),
('Deliverable and check','Save docs/DATA_SOURCES.md and docs/COVERAGE_CHECKLIST.md. Include URLs, provider, vintage, format, resolution, access/reuse conditions, role, local file, and four-area status. Stop when every required input has a status and a next action.')]),
('Session 2 Acquire and Clean Data 90 Minutes',[
('Actions','Run the existing cleaner with --zipcodes 75025 75024 75023 75074. Preserve raw snapshots; check IDs, geometry, duplicates, and missingness. Use EPSG:26914 for local metric operations and EPSG:4326 for map display. Inspect the quality report.'),
('Origins and destinations','Use a small manually verified sample of residential address points. Parcels can support checking, but do not prove residential use or entrances. Query OSM for pharmacies, supermarkets/groceries, and appropriate places of worship; verify names, categories, and access points. Census-block origins are an extension if address sampling is insufficient.'),
('Tools and sources','GeoPandas, pandas, requests, Shapely, and OSMnx. Use Plano sidewalks, trails, parcels/address points, and OSM destination candidates.'),
('Deliverable and check','Save cleaned GeoPackages, origins.gpkg, destinations.gpkg, and quality_report.md under data/processed/. Confirm coverage in every ZIP and document remaining gaps. Do not interpret zero returned POIs as proof that no facility exists.')]),
('Session 3 Build and Audit the Network 90 Minutes',[
('Actions','Use OSMnx graph_from_polygon with network_type="walk" and retain_all=True. Query the union of all four boundaries with approximately 500 m surrounding context; expand if boundary effects remain. Save the source graph before editing. Inspect it against Plano sidewalk polygons and trail lines.'),
('Connections','Attach origins and destinations using plausible access points; audit nearest-node connectors for fences and major-road crossings. Record components and disconnected origins. Add municipal paths only after checking topology and access; avoid duplicates. Sidewalk polygon outlines are not pedestrian centerlines.'),
('Tools and references','OSMnx, NetworkX, GeoPandas, and Folium. Follow Street Shadow’s graph-to-route structure. Consult UNA for origin/destination architecture rather than adding another routing library.'),
('Deliverable and check','Save walking_graph.graphml, access_connectors.gpkg, and network_audit.md. Inspect at least one route per ZIP. Preserve unreachable locations; never create straight-line edges between every pair of locations.')]),
('Session 4 Add Environmental Features 60 Minutes',[
('Actions','Obtain a manageable study-area clip of the Texas 2021 10 m canopy raster. Use Rasterio to sample valid canopy pixels within a documented corridor around each edge; begin with a 10 m buffer and record that choice. Preserve NoData and valid-pixel fractions. Keep neighborhood Tree Equity Score values as context.'),
('Feature table','Save edge ID, length_m, canopy_fraction, valid_pixel_fraction, feature source/year, and any verified crossing constraints. Add traffic, imperviousness, weather, or time-specific shade only if usable data is already available; they are optional extensions.'),
('Tools and references','Rasterio, NumPy, GeoPandas, and Shapely. Use CoolWalks for the distinction between shaded and sunlit route costs. A canopy corridor is a proxy, not a measured shade fraction.'),
('Deliverable and check','Save edge_features.gpkg and docs/DATA_DICTIONARY.md. Check ranges, units, and missingness by ZIP. If fine-scale canopy cannot be acquired, disclose the gap; do not quietly substitute block-group averages as street measurements.')]),
('Session 5 Reuse and Adapt GeoAI 90 Minutes',[
('Select one path','Reuse the Singapore study’s released analysis model and notebook to investigate shade–distance preferences, or integrate an existing pretrained environmental predictor with compatible public inputs. New model architecture or training from scratch is not required. Select the path based on accessible code, inputs, licensing, and runtime.'),
('Specify the model','Write its name/version, input features, predicted quantity, original training geography, local adaptation, and role in edge costs. For Singapore preferences, reproduce the released analysis before modifying it; evaluate by held-out participant where fitting is performed. For environmental predictions, inspect independent reference samples.'),
('Tools and references','Use Jupyter and the selected project’s dependencies. The Singapore data/code are at OSF aj4vk (Melnikov et al., 2022). XGBoost or LightGBM is optional only when a compatible existing workflow and meaningful labels are available.'),
('Deliverable and check','Save model_adapter.py or a model notebook and docs/MODEL_CARD.md. A route-level classifier does not automatically supply additive edge costs. Show what was reused and changed. A precomputed ML-derived canopy product is an input, not evidence of a newly developed model. If no usable model runs, mark GeoAI incomplete rather than relabeling manual penalties.')]),
('Session 6 Calculate Routes and Rankings 60 Minutes',[
('Actions','Create nonnegative, additive edge costs. Begin with length plus an explicitly defined environmental penalty; document units and distinguish model-derived terms from scenario assumptions. Do not apply a sunlight coefficient to canopy without labeling the transfer assumption.'),
('Routing and ranking','Use NetworkX Dijkstra-based routing. For each origin, find the lowest-cost reachable destination in each category; rank origins by an equal-weight sum across the three category costs. Keep unreachable categories flagged and exclude incomplete origins from the all-services ranking. Compare against a distance-only baseline.'),
('Tools and references','NetworkX, pandas, OSMnx, and GeoPandas. Use Street Shadow and CoolWalks for weighted paths; Walk Score for amenity-access framing, not a heat-friction label.'),
('Deliverable and check','Save routes.gpkg and residential_rankings.csv. Include origin ID, ZIP, chosen destination IDs, route distances, category costs, combined cost, and reachability. Confirm all three categories influence ranking.')]),
('Session 7 Evaluate and Build the Map 75 Minutes',[
('Evaluate','Inspect at least one route per ZIP and one major crossing. For one origin/destination pair, report distance-only versus friction-sensitive route length, canopy proxy, and modeled cost. Test two plausible environmental-penalty settings and record ranking changes. Evaluate the reused model separately from routing.'),
('Visualize','Use Folium to display the four boundaries, origins, destination categories, baseline and alternative routes, and ranked-origin popups. Precompute results; use layer controls and tooltips instead of building a complex frontend. Use Streamlit only if a Python query interface is essential and time remains.'),
('Tools and references','Folium, pandas, matplotlib, and the selected model’s evaluation tools. Use City Health Dashboard for explanatory map design and the LA sidewalk heat study for connecting residential access to exposure.'),
('Deliverable and check','Save output/empath_demo.html, evaluation.csv, and docs/LIMITATIONS.md. The map must show why a result differs; do not force an improvement if the analysis finds none. Cached results support the demo, but external basemap tiles may still need internet.')]),
('Session 8 Package and Present 45 Minutes',[
('Actions','Update README.md with installation, kernel selection, run order, source attribution, and data-download instructions. Record model and library versions. Save screenshots or a short backup recording. Rehearse a five-minute explanation: problem, data, method, demonstration, finding, limitation.'),
('Deliverable and check','Hand off code, source/coverage documents, data provenance, graph/features, model adapter/card, routes/rankings, evaluation, demo, and slides. Reuse generated outputs rather than write a separate long report. A fresh session should reproduce or load the documented demo.')]),
('Scope Control and Optional Teamwork',[
('Troubleshooting reserve','Use the remaining hour for acquisition failures, graph errors, or packaging. If blocked, first reduce sampled origins, display layers, or model complexity while retaining the four-area study boundary. Do not label missing data or disconnected routes as completed coverage.'),
('Optional teammate','Delegate either data/network review or model evaluation, with a defined file and check to return. An ArcGIS Pro user can inspect the same GeoPackage/GeoJSON layers; Python remains the reproducible pipeline.'),
('Future work','Add local preference validation, crossing/traffic attributes, time-dependent shade and weather, larger origin coverage, and eventually origin-to-destination lowest-friction navigation. These are extensions, not minimum hackathon deliverables.')]),
('Data Sources',[
('Census boundaries','U.S. Census Bureau. (n.d.). TIGERweb ZCTA layer. https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2'),
('Plano walking data','City of Plano. (n.d.). Sidewalks and trail centerlines. https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0 ; https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0'),
('Plano origins','City of Plano. (n.d.). Address points and parcels. https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0 ; https://maps.planogis.org/arcgiswad/rest/services/OpenData/Parcels/FeatureServer/1'),
('Canopy raster','Diamond, D., Sunde, M., & Elliott, L. (2023). Texas statewide landcover, ecological systems, and percentage canopy classifications (10-meter resolution) (2021) [Data set]. Zenodo. https://zenodo.org/records/8200761'),
('Context and public observations','American Forests. (n.d.). Tree Equity Score methods and data. https://www.treeequityscore.org/methodology?tab=data-download ; Singapore study data and code: https://osf.io/aj4vk/')]),
('Methods and Case Studies',[
('Behavioral calibration','Melnikov, V. R., Christopoulos, G. I., Krzhizhanovskaya, V. V., Lees, M. H., & Sloot, P. M. A. (2022). Behavioural thermal regulation explains pedestrian path choices in hot urban environments. Scientific Reports, 12, Article 2441. https://doi.org/10.1038/s41598-022-06383-5'),
('Python implementation','jlgonrod. (n.d.). Street Shadow [Computer software]. GitHub. https://github.com/jlgonrod/street_shadow ; inspect modules/graphs.py. Shade weighting is manually parameterized; it is not a pretrained preference model.'),
('Shade routing','Wolf, H., Vierø, A. R., & Szell, M. (2025). CoolWalks for active mobility in urban street networks. Scientific Reports, 15, Article 14911. https://www.nature.com/articles/s41598-025-97200-2 ; code: https://github.com/henrik-wolf/CoolWalks . Use the methodology; its implementation is Julia.'),
('Residential heat accessibility','Colaninno, N., Basu, R., Hosseini, M., Alhassan, A., Liu, L., & Sevtsuk, A. (2025). A sidewalk-level urban heat risk assessment framework using pedestrian mobility and urban microclimate modeling. Environment and Planning B: Urban Analytics and City Science. https://doi.org/10.1177/23998083241280746 . Use the research design, not its full QGIS-dependent workflow.'),
('Accessibility and presentation','UNA: https://github.com/City-Form-Lab/urban_network_analysis ; Walk Score: https://www.walkscore.com/methodology.shtml ; City Health Dashboard: https://www.cityhealthdashboard.com/metric/walkability . The dashboard’s walkability measure uses Walk Score, so these are not independent validation sources.')]),
('Software Documentation',[
('Network and mapping','OSMnx: https://osmnx.readthedocs.io/en/stable/user-reference.html ; NetworkX: https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html ; Folium: https://python-visualization.github.io/folium/latest/user_guide.html'),
('Raster processing','Rasterio windowed reading: https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html . Clipping or windowing requires a readable raster; a large ZIP archive cannot automatically be treated as a remotely tiled raster.')])]
# Main implementation guide. Resource entries are annotated references for use during work.
doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1);sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.header_distance=Inches(.5)
for name in ['Normal','Title','Heading 1']:
 s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0);pf=s.paragraph_format;pf.line_spacing=2;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.first_line_indent=Inches(.5) if name=='Normal' else Inches(0)
 fonts=s.element.get_or_add_rPr().get_or_add_rFonts()
 for a in list(fonts.attrib):
  if 'Theme' in a:del fonts.attrib[a]
 for a in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+a),'Times New Roman')
for name in ['Title','Heading 1']:
 doc.styles[name].font.bold=True;doc.styles[name].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER;doc.styles[name].paragraph_format.keep_with_next=True
p=sec.header.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;p.paragraph_format.first_line_indent=Inches(0);f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
p=doc.add_paragraph(title,'Title');p.paragraph_format.space_before=Pt(72);p.paragraph_format.space_after=Pt(24)
for t in ['Nalini Kantheti','Center for Urban Science and Progress, New York University','November 8, 2026']:
 p=doc.add_paragraph(t);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Inches(0)
doc.add_page_break()
md=['# '+title,''];web=[]
for heading,paragraphs in sections:
 if heading=='Data Sources':doc.add_page_break()
 doc.add_paragraph(heading,'Heading 1');md+=['## '+heading,''];web+=['<h2>'+html.escape(heading)+'</h2>']
 for label,text in paragraphs:
  p=doc.add_paragraph();p.add_run(label+'. ').bold=True;p.add_run(text)
  md+=['**'+label+'.** '+text,''];escaped=html.escape(text);escaped=re.sub(r'(https?://[^\s;]+)',r'<a href="\1">\1</a>',escaped)
  web+=['<p><b>'+html.escape(label)+'.</b> '+escaped+'</p>']
for p in doc.paragraphs:
 for r in p.runs:r.font.name='Times New Roman'
doc.core_properties.title=title;doc.core_properties.author='Nalini Kantheti';doc.save(out/'EmPath_Detailed_Roadmap_APA.docx')
(out/'EmPath_Detailed_Roadmap.md').write_text('\n'.join(md))
(out/'EmPath_Detailed_Roadmap_Copy_Paste.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>'+title+'</title><style>body{font:12pt/2 "Times New Roman",serif;max-width:6.5in;margin:1in auto;padding:0 16px}h1,h2{font-size:12pt;text-align:center;margin:18pt 0 0;font-weight:bold}p{margin:0;text-indent:.5in}a{overflow-wrap:anywhere}</style></head><body><h1>'+title+'</h1>'+''.join(web)+'</body></html>')
print('Words:',sum(len(t.split())+len(l.split()) for _,ps in sections for l,t in ps))
