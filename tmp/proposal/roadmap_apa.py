from pathlib import Path
import html
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
out=Path('output/roadmap_apa');doc=Document();sec=doc.sections[0]
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1);sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.header_distance=Inches(.5)
for name in ['Normal','Title','Heading 1']:
 s=doc.styles[name];s.font.name='Times New Roman';s.font.size=Pt(12);s.font.color.rgb=RGBColor(0,0,0)
 f=s.element.get_or_add_rPr().get_or_add_rFonts()
 for a in list(f.attrib):
  if 'Theme' in a:del f.attrib[a]
 for a in ['ascii','hAnsi','eastAsia','cs']:f.set(qn('w:'+a),'Times New Roman')
 pf=s.paragraph_format;pf.line_spacing=2;pf.space_before=Pt(0);pf.space_after=Pt(0);pf.first_line_indent=Inches(.5) if name=='Normal' else Inches(0)
doc.styles['Title'].font.bold=True;doc.styles['Title'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
doc.styles['Heading 1'].font.bold=True;doc.styles['Heading 1'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
p=sec.header.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.RIGHT;p.paragraph_format.first_line_indent=Inches(0)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
title='EmPath Project Roadmap'
p=doc.add_paragraph(title,'Title');p.paragraph_format.space_before=Pt(72);p.paragraph_format.space_after=Pt(24)
for t in ['Nalini Kantheti','Center for Urban Science and Progress, New York University','November 8, 2026']:
 p=doc.add_paragraph(t);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Inches(0)
doc.add_page_break();doc.add_paragraph(title,'Heading 1')
intro='EmPath is a Python-based GeoAI prototype comparing residential access to temples, groceries, and pharmacies through environmental walking friction and distance. The study covers Plano ZIP areas 75025, 75024, 75023, and 75074. Development is limited to one week and approximately 10 hours, primarily by one developer.'
doc.add_paragraph(intro)
steps=[('Data (2 hours).','Verify coverage, document sources, and clean essential inputs. Deliverables: sources and coverage table and usable datasets.'),('Network (2 hours).','Connect residential origins and destinations to a pedestrian graph; inspect crossings and connectivity. Deliverables: walking graph and map.'),('GeoAI and friction (2 hours).','Adapt existing models or methods to derive environmental features or costs. Separate model outputs from assumed penalties. Deliverables: documented GeoAI component and weighted graph.'),('Analysis (1.5 hours).','Calculate routes and residential rankings; compare distance-only results and audit sample routes. Deliverables: comparisons, rankings, and limitations.'),('Demonstration (1.5 hours).','Explain results through one interactive map. Deliverable: runnable prototype.'),('Handoff (1 hour).','Document execution and prepare a five-minute presentation. Deliverables: README, references, slides, and backup screenshots.')]
for label,text in steps:
 p=doc.add_paragraph();p.add_run(label+' ').bold=True;p.add_run(text)
end='The minimum prototype includes four areas, sample origins, three destination categories, one environmental scenario, and one meaningful GeoAI component. Validate model outputs and disclose assumptions. An optional teammate can review data, networks, or models. Future expansion would support lowest-friction navigation.'
doc.add_paragraph(end)
doc.core_properties.title=title;doc.core_properties.author='Nalini Kantheti';doc.save(out/'EmPath_Project_Roadmap_APA.docx')
body='<h1>'+title+'</h1><p class="byline">Nalini Kantheti<br>Center for Urban Science and Progress, New York University<br>November 8, 2026</p><p>'+html.escape(intro)+'</p>'
for a,b in steps:body+='<p><b>'+html.escape(a)+'</b> '+html.escape(b)+'</p>'
body+='<p>'+html.escape(end)+'</p>'
(out/'EmPath_Project_Roadmap_Copy_Paste.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>'+title+'</title><style>body{font:12pt/2 "Times New Roman",serif;max-width:6.5in;margin:1in auto;padding:0 16px}h1{font-size:12pt;text-align:center;margin:0;font-weight:bold}p{margin:0;text-indent:.5in}.byline{text-align:center;text-indent:0;margin-bottom:24pt}</style></head><body>'+body+'</body></html>')
print('Created roadmap document and copy-paste HTML.')
