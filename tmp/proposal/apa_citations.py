from pathlib import Path
import re,html
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
root=Path('output/roadmap_guide');doc=Document(root/'EmPath_Implementation_Guide_Polished.docx')
# Citation placement follows the source-dependent methodological statements.
rules=[
('Run .venv/bin/python scripts/clean_data.py',' (City of Plano, n.d.-a, n.d.-b, n.d.-c, n.d.-d).'),
('Use OSMnx graph_from_polygon',' (OSMnx contributors, n.d.).'),
('Acquire a manageable clip of the Texas 2021',' (Diamond et al., 2023).'),
('Treat canopy as an environmental proxy',' (American Forests, n.d.; Wolf et al., 2025).'),
('For the Singapore study, inspect',' (Melnikov et al., 2022).'),
('Use NetworkX Dijkstra-based routing',' (NetworkX developers, n.d.).'),
('Build one Folium map',' (Folium contributors, n.d.).')]
for p in doc.paragraphs:
 if p.text.startswith("Scope: Plano ZIP areas"):
  p.text=p.text.replace("Census ZCTA boundaries.", "Census ZCTA boundaries (U.S. Census Bureau, n.d.).")
 for prefix,cite in rules:
  if p.text.startswith(prefix):
   text=p.text.rstrip().rstrip('.');p.text=text+cite
 for old,new in [('Street Shadow for graph-to-route structure','Street Shadow for graph-to-route structure (jlgonrod, n.d.)'),('CoolWalks for shade-sensitive costs','CoolWalks for shade-sensitive costs (Wolf et al., 2025)'),('Walk Score’s amenity framing','Walk Score’s amenity framing (Walk Score, n.d.)'),('LA sidewalk heat study for research design','LA sidewalk heat study for research design (Colaninno et al., 2025)'),('City Health Dashboard for communication','City Health Dashboard for communication (City Health Dashboard, n.d.)'),('UNA for origin/destination architecture','UNA for origin/destination architecture (City Form Lab, n.d.)')]:
  if old in p.text:p.text=p.text.replace(old,new)
# Replace the old link directory, preserving the main guide.
cut=False
for p in list(doc.paragraphs):
 if p.text=='Source and Reference Links':cut=True
 if cut:p._element.getparent().remove(p._element)
refs=[
('American Forests. (n.d.). ','Tree Equity Score methods and data','. https://www.treeequityscore.org/methodology?tab=data-download'),
('City Form Lab. (n.d.). ','UNA urban network analysis',' [Computer software]. GitHub. https://github.com/City-Form-Lab/urban_network_analysis'),
('City Health Dashboard. (n.d.). ','Walkability','. https://www.cityhealthdashboard.com/metric/walkability'),
('City of Plano. (n.d.-a). ','Address points',' [Data set]. https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0'),
('City of Plano. (n.d.-b). ','Parcels',' [Data set]. https://maps.planogis.org/arcgiswad/rest/services/OpenData/Parcels/FeatureServer/1'),
('City of Plano. (n.d.-c). ','Sidewalks',' [Data set]. https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0'),
('City of Plano. (n.d.-d). ','Trail centerlines',' [Data set]. https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0'),
('Colaninno, N., Basu, R., Hosseini, M., Alhassan, A., Liu, L., & Sevtsuk, A. (2025). A sidewalk-level urban heat risk assessment framework using pedestrian mobility and urban microclimate modeling. ','Environment and Planning B: Urban Analytics and City Science, 52','(5). https://doi.org/10.1177/23998083241280746'),
('Diamond, D., Sunde, M., & Elliott, L. (2023). ','Texas statewide landcover, ecological systems, and percentage canopy classifications (10-meter resolution) (2021)',' [Data set]. Zenodo. https://zenodo.org/records/8200761'),
('Folium contributors. (n.d.). ','User guide','. https://python-visualization.github.io/folium/latest/user_guide.html'),
('jlgonrod. (n.d.). ','Street Shadow',' [Computer software]. GitHub. https://github.com/jlgonrod/street_shadow'),
('Melnikov, V. R., Christopoulos, G. I., Krzhizhanovskaya, V. V., Lees, M. H., & Sloot, P. M. A. (2022). Behavioural thermal regulation explains pedestrian path choices in hot urban environments. ','Scientific Reports, 12',', Article 2441. https://doi.org/10.1038/s41598-022-06383-5'),
('NetworkX developers. (n.d.). ','Shortest paths','. https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html'),
('OSMnx contributors. (n.d.). ','User reference','. https://osmnx.readthedocs.io/en/stable/user-reference.html'),
('Rasterio contributors. (n.d.). ','Windowed reading and writing','. https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html'),
('U.S. Census Bureau. (n.d.). ','ZIP Code Tabulation Areas',' [Data set]. TIGERweb. https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2'),
('Walk Score. (n.d.). ','Walk Score methodology','. https://www.walkscore.com/methodology.shtml'),
('Wolf, H., Vierø, A. R., & Szell, M. (2025). CoolWalks for active mobility in urban street networks. ','Scientific Reports, 15',', Article 14911. https://doi.org/10.1038/s41598-025-97200-2')]
# Add citations for the raster workflow and the named comparison application.
for p in doc.paragraphs:
 if p.text.startswith('Tools: Rasterio'):p.add_run(' See Rasterio contributors (n.d.) for raster-processing documentation.')
p=doc.add_paragraph('References','Heading 1');p.paragraph_format.page_break_before=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
for a,b,c in refs:
 p=doc.add_paragraph();p.paragraph_format.left_indent=Inches(.5);p.paragraph_format.first_line_indent=Inches(-.5);p.paragraph_format.line_spacing=1.15;p.paragraph_format.space_after=Pt(8);p.add_run(a);p.add_run(b).italic=True;p.add_run(c)
for sec in doc.sections:
 sec.header_distance=Inches(.4)
 p=sec.header.paragraphs[0];p.clear();p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
 f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
for p in doc.paragraphs:
 for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
file=root/'EmPath_Guide_Citations_and_Page_Numbers.docx';doc.save(file)
# Keep the self-contained copy-paste HTML and update its citations/reference section.
source=(root/'EmPath_Implementation_Guide_Polished_Copy_Paste.html').read_text()
source=source[:source.index('<h2>Source and Reference Links</h2>')]
source=source.replace('Census ZCTA boundaries.', 'Census ZCTA boundaries (U.S. Census Bureau, n.d.).')
for prefix,cite in rules:
 pattern=r'<p>'+re.escape(html.escape(prefix))+r'.*?</p>'
 # Bullets are separately handled below.
 for tag in ['p','li']:
  pattern=r'<'+tag+'>'+re.escape(html.escape(prefix))+r'.*?</'+tag+'>'
  source=re.sub(pattern,lambda m:m[0][:-len('</'+tag+'>')].rstrip('. ')+html.escape(cite)+'</'+tag+'>',source)
for old,new in [('Street Shadow for graph-to-route structure','Street Shadow for graph-to-route structure (jlgonrod, n.d.)'),('CoolWalks for shade-sensitive costs','CoolWalks for shade-sensitive costs (Wolf et al., 2025)'),('Walk Score’s amenity framing','Walk Score’s amenity framing (Walk Score, n.d.)'),('LA sidewalk heat study for research design','LA sidewalk heat study for research design (Colaninno et al., 2025)'),('City Health Dashboard for communication','City Health Dashboard for communication (City Health Dashboard, n.d.)'),('UNA for origin/destination architecture','UNA for origin/destination architecture (City Form Lab, n.d.)')]:source=source.replace(html.escape(old),html.escape(new))
source+='<h2>References</h2>'+''.join('<p style="margin-left:.5in;text-indent:-.5in">'+html.escape(a)+'<i>'+html.escape(b)+'</i>'+html.escape(c)+'</p>' for a,b,c in refs)+'</body></html>'
source=source.replace('. (','. (')
(root/'EmPath_Guide_Citations_Copy_Paste.html').write_text(source)
print(file)
