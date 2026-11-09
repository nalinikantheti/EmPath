from pathlib import Path
import json,re,ast,base64,html,zipfile
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image
out=Path('output/proposal_apa');items=json.loads(Path('output/proposal_google_docs/extracted_blocks.json').read_text())
source=ast.parse(Path('tmp/proposal/build.py').read_text());table=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='table' for t in n.targets))
doc=Document();sec=doc.sections[0];sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1);sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.header_distance=Inches(.5)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
 s.paragraph_format.line_spacing=2;s.paragraph_format.space_before=Pt(0);s.paragraph_format.space_after=Pt(0)
 s.paragraph_format.first_line_indent=Inches(.5) if name=='Normal' else Inches(0)
for name in ['Heading 1','Heading 2']:
 s=doc.styles[name];s.font.bold=True;s.font.italic=False;s.paragraph_format.keep_with_next=True
 s.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER if name=='Heading 1' else WD_ALIGN_PARAGRAPH.LEFT
h=sec.header.paragraphs[0];h.alignment=WD_ALIGN_PARAGRAPH.RIGHT;h.paragraph_format.first_line_indent=Inches(0)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');h._p.append(f)
title='PathéResistance and EmPath: A GeoAI Approach to Learning Pedestrian Accessibility Friction in Car-Dependent Suburban Communities'
p=doc.add_paragraph(title,'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(72);p.paragraph_format.space_after=Pt(24);p.runs[0].bold=True
for text in ['Nalini Kantheti','Center for Urban Science and Progress, New York University','November 7, 2026']:
 p=doc.add_paragraph(text);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Inches(0)
doc.add_page_break();p=doc.add_paragraph(title,'Heading 1')
refs=False;bodyhtml=[]
def addtext(p,text):
 # Preserve inline subscripts as editable Word formatting.
 pattern=r'(x_e|h_t|f_θ|d_wθ|D_selected)'
 for bit in re.split(pattern,text):
  if re.fullmatch(pattern,bit or ''):
   first,sub=bit.split('_',1);p.add_run(first).italic=True;r=p.add_run(sub);r.font.subscript=True
  else:p.add_run(bit)
for kind,s in items:
 if kind in ['h1','h2']:
  text=re.sub(r'^\d+(?:\.\d+)?\.?\s+','',s)
  if text=='References':doc.add_page_break();refs=True
  p=doc.add_paragraph(text,'Heading 1' if kind=='h1' else 'Heading 2');bodyhtml.append(f'<h{2 if kind=="h1" else 3}>{html.escape(text)}</h{2 if kind=="h1" else 3}>')
 elif kind=='p':
  p=doc.add_paragraph()
  if refs:
   p.paragraph_format.left_indent=Inches(.5);p.paragraph_format.first_line_indent=Inches(-.5)
   italic_titles=['Geographical Analysis, 57','Scientific Reports, 12','Heat and chronic conditions','Pedestrian environment','Climate Data Online','Annual National Land Cover Database Collection 1 products (Version 1.2)']
   match=next((x for x in italic_titles if x in s),None)
   if match:
    a,b=s.split(match,1);p.add_run(a);p.add_run(match).italic=True;p.add_run(b)
   else:p.add_run(s)
  else:
   if s.startswith('5. Decision relevance:') and ' These are prototype' in s:
    a,b=s.split(' These are prototype',1);addtext(p,a);p=doc.add_paragraph();addtext(p,'These are prototype'+b)
   else:addtext(p,s)
  bodyhtml.append('<p'+(' class="reference"' if refs else '')+'>'+html.escape(s)+'</p>')
 elif kind=='eq':
  p=doc.add_paragraph();p.paragraph_format.first_line_indent=Inches(0);p.paragraph_format.line_spacing=1;p.paragraph_format.space_before=Pt(12);p.paragraph_format.space_after=Pt(12)
  p.paragraph_format.tab_stops.add_tab_stop(Inches(3.25),WD_TAB_ALIGNMENT.CENTER);p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5),WD_TAB_ALIGNMENT.RIGHT)
  img=out/f'equations/equation_{s}.png';w,h=Image.open(img).size
  p.add_run('\t').add_picture(str(img),width=Inches(w/450));p.add_run(f'\t({s})')
  # Keep introductory paragraph with its equation.
  prev=p._p.getprevious()
  if prev is not None:
   pp=prev.get_or_add_pPr();kw=OxmlElement('w:keepNext');pp.append(kw)
  data=base64.b64encode(img.read_bytes()).decode();bodyhtml.append(f'<p class="equation"><img src="data:image/png;base64,{data}" alt="Equation {s}" style="width:{w/450}in"> ({s})</p>')
 elif kind=='table':
  for requirement,src,notes in table:
   p=doc.add_paragraph();p.add_run(requirement+'. ').bold=True;p.add_run('Candidate source: '+src+'. '+notes)
   bodyhtml.append('<p><b>'+html.escape(requirement)+'.</b> '+html.escape('Candidate source: '+src+'. '+notes)+'</p>')
for style in doc.styles:
 if style.type == 1 or style.type == 2:
  style.font.name='Times New Roman'
  fonts=style.element.get_or_add_rPr().get_or_add_rFonts()
  for attr in list(fonts.attrib):
   if 'Theme' in attr: del fonts.attrib[attr]
  for attr in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+attr),'Times New Roman')
for paragraph in doc.paragraphs:
 for run in paragraph.runs:run.font.name='Times New Roman'
doc.core_properties.title=title;doc.core_properties.author='Nalini Kantheti';doc.save(out/'EmPath_Proposal_APA.docx')
page='<!doctype html><html><head><meta charset="utf-8"><title>EmPath APA Proposal</title><style>body{font:12pt/2 "Times New Roman",serif;max-width:6.5in;margin:1in auto}p{margin:0;text-indent:.5in}h1,h2,h3{font-size:12pt;line-height:2;margin:0;font-weight:bold}h1,h2{text-align:center}h3{text-align:left}.reference{margin-left:.5in;text-indent:-.5in}.equation{text-align:center;text-indent:0;margin:12pt 0;line-height:1}.equation img{max-width:100%;vertical-align:middle}.title{text-align:center;text-indent:0}</style></head><body><h1>'+html.escape(title)+'</h1><p class="title">Nalini Kantheti<br>Center for Urban Science and Progress, New York University<br>November 7, 2026</p>'+''.join(bodyhtml)+'</body></html>'
(out/'EmPath_Proposal_APA_Copy_Paste.html').write_text(page)
with zipfile.ZipFile(out/'EmPath_Equations_Times_New_Roman.zip','w',zipfile.ZIP_DEFLATED) as z:
 for img in sorted((out/'equations').glob('*.png')):z.write(img,img.name)
(out/'formatting_notes.txt').write_text('APA 7 student-paper layout: 12-point Times New Roman, double spacing, US Letter, 1-inch margins, page numbers, title page, hierarchical headings, hanging-indent references. Course and instructor were not supplied and are omitted. Original proposal wording, date and superseded five-mile scope are retained. All four numbered equations are PNG images, using Times New Roman for text and variables. The membership symbol (U+2208), absent from the installed Times New Roman font, uses the matching STIX fallback. Formatting conversion is not a full reference-content or factual audit.\n')
print(out/'EmPath_Proposal_APA.docx')
