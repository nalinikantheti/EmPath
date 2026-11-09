from pathlib import Path
import re,unicodedata,html,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image
ROOT=Path.cwd();out=ROOT/'output/proposal_google_docs'
raw=Path('/tmp/empath_layout.txt').read_text()
items=[];current='';intable=False;inequation=False;refs=False;listmode=False

def clean(s):
 s=unicodedata.normalize('NFKC',s).replace(';',';').replace('{[}','[').replace('{]}',']')
 return re.sub(r'\s+',' ',s).strip()
def flush():
 global current
 if current:items.append(('p',current));current=''
def append(s):
 global current
 if current.endswith('-'):current=current[:-1]+s
 else:current+=((' ' if current else '')+s)
lines=raw.splitlines()
for line in lines:
 line=line.replace('\f','');s=clean(line)
 if not s or (s.isdigit() and len(line)-len(line.lstrip()) > 40):continue
 if s.startswith('1. Personal Motivation'):started=True
 elif not globals().get('started',False):continue
 indent=len(line)-len(line.lstrip())
 if intable:
  if s.startswith('USGS provides annual'):
   intable=False
  else:continue
 if s.startswith('7. Data Architecture'):
  flush();items.append(('h1',s));items.append(('table',''));intable=True;continue
 # Standalone display math and its lower limits.
 if re.search(r'\([1-4]\)\s*$',s):
  flush();n=int(re.search(r'\(([1-4])\)\s*$',s).group(1));items.append(('eq',n));continue
 if s in ['e∈P','d∈D'] or ('r∈R' in s and ('selected' in s or 'd∈D' in s)):continue
 if s=='References':flush();refs=True;items.append(('h1',s));continue
 if re.match(r'^\d+\.\d+\s',s):flush();items.append(('h2',s));listmode=False;continue
 if re.match(r'^\d+\.\s',s) and indent<=1:
  flush();items.append(('h1',s));listmode=False;continue
 if refs:
  if indent<=1:flush()
  append(s);continue
 if re.match(r'^\d+\.\s',s):flush();listmode=True;append(s);continue
 if indent>=5 and not listmode:flush()
 append(s)
flush()
# Correct typography artifacts introduced by PDF line wrapping.
fix={'hightraffic':'high-traffic','residentialneighborhood':'residential-neighborhood','shortestpath':'shortest-path','nonnegative':'nonnegative','sun–distance':'sun–distance'}
for i,(kind,s) in enumerate(items):
 if isinstance(s,str):
  for a,b in fix.items():s=s.replace(a,b)
  # Common mathematical inline notation converted to copyable text.
  s=s.replace('G = (V , E)','G = (V, E)').replace('xe denotes','x_e denotes').replace('ht represents','h_t represents').replace('fθ','f_θ').replace('dwθ (r, d)','d_wθ(r, d)').replace('Dselected','D_selected').replace('https://www.planocompplan.org/159/P Environment','https://www.planocompplan.org/159/Pedestrian-Environment').replace('06383- 5','06383-5').replace('063835','06383-5')
  items[i]=(kind,s)
table=[
['Pedestrian streets, paths, and crossings','OpenStreetMap/OSMnx; Plano GIS','Network topology; walking completeness and crossing validity must be checked.'],
['Residential areas and destinations','OpenStreetMap; municipal geographic layers','Origin/destination nodes; coverage, geocoding, and representative centroids need validation.'],
['Pavement and impervious surfaces','USGS Annual NLCD','Contextual land-cover indicators; raster resolution may not describe individual sidewalks.'],
['Tree canopy and shade','Municipal GIS, imagery, or remote sensing','Segment-level features; canopy is an imperfect proxy for time-dependent pedestrian shade.'],
['Temperature and weather','NOAA historical station data; potential spatial products','Temporal conditions; station observations alone do not resolve block-level heat.'],
['Learning labels','To be identified or collected','Essential for AI-fitted weights; valid route preferences or comparable target data are not yet secured.'],
['EMS or police welfare response','Potential municipal administrative records','Optional, aggregate contextual analysis; availability, privacy, and reporting bias unresolved.']]
doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=Inches(.8);sec.left_margin=sec.right_margin=Inches(.85)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 st=doc.styles[name];st.font.name='Calibri';st.font.color.rgb=RGBColor(0,0,0)
doc.styles['Normal'].font.size=Pt(11);doc.styles['Normal'].paragraph_format.space_after=Pt(7);doc.styles['Normal'].paragraph_format.line_spacing=1.15
for name in ['Heading 1','Heading 2']:
 doc.styles[name].paragraph_format.keep_with_next=True
 doc.styles[name].paragraph_format.space_before=Pt(12)
doc.add_paragraph('PathéResistance & EmPath','Title')
doc.add_paragraph('A GeoAI Approach to Learning Pedestrian Accessibility Friction in Car-Dependent Suburban Communities','Subtitle')
doc.add_paragraph('Initial Research Proposal and Development Plan — Revised GeoAI Specification')
doc.add_paragraph('Nalini Kantheti\nCenter for Urban Science and Progress\nNew York University\nNovember 7, 2026')
md=['# PathéResistance & EmPath','','A GeoAI Approach to Learning Pedestrian Accessibility Friction in Car-Dependent Suburban Communities','','Initial Research Proposal and Development Plan — Revised GeoAI Specification','','Nalini Kantheti  \nCenter for Urban Science and Progress  \nNew York University  \nNovember 7, 2026','']
for kind,s in items:
 if kind in ['h1','h2']:
  doc.add_paragraph(s,'Heading 1' if kind=='h1' else 'Heading 2');md+=['## '+s if kind=='h1' else '### '+s,'']
 elif kind=='p':doc.add_paragraph(s);md+=[s,'']
 elif kind=='eq':
  p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  img=out/f'equations/equation_{s}.png';w,h=Image.open(img).size
  p.add_run().add_picture(str(img),width=Inches(min(5.8,w/300)))
  p.add_run(f'  ({s})');md += [f'![Equation {s}]({img})','']
 elif kind=='table':
  # Prose records keep long source descriptions readable and easy to paste.
  for requirement,source,notes in table:
   p=doc.add_paragraph();p.add_run(requirement+'. ').bold=True;p.add_run('Candidate source: '+source+'. '+notes)
   md += [f'**{requirement}.** Candidate source: {source}. {notes}','']
doc.core_properties.title='PathéResistance and EmPath Research Proposal';doc.core_properties.author='Nalini Kantheti'
doc.save(out/'EmPath_Proposal_Google_Docs.docx')
(out/'EmPath_Proposal_Copy_Paste.md').write_text('\n'.join(md))
(out/'extracted_blocks.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
print('Blocks:',len(items),'equations:',[s for k,s in items if k=='eq'])
print('Word count:',sum(len(str(s).split()) for k,s in items))
