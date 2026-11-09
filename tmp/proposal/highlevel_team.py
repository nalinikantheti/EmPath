from pathlib import Path
from html import escape
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
root=Path('output/roadmap_guide')
items=[('title','EmPath Team Work Guide'),('p','A flexible guide for dividing work and keeping the prototype moving. Adjust responsibilities as needs and availability change.'),('h','Shared Goal'),('b','Build a Python-based demo comparing distance-only and environmental-friction walking access across Plano ZIP areas 75025, 75024, 75023, and 75074.'),('h','Nalini Leads Implementation and Storytelling'),('b','Prepare the data and walking network.'),('b','Connect the GeoAI component to route scoring and residential rankings.'),('b','Build the interactive map and explain the project through the final presentation.'),('h','Pramukh Leads GIS and Data Science Support'),('b','Review data coverage, network connections, and geographic assumptions.'),('b','Help adapt the existing model and evaluate whether results make sense.'),('b','Troubleshoot priority issues and help check the final demo.'),('h','Work in Three Broad Phases'),('b','Prepare: organize data, agree on a feasible approach, and get the basic pipeline running.'),('b','Build and review: Nalini connects the components while Pramukh reviews outputs and helps resolve gaps.'),('b','Finish: focus on one clear demonstration, explain limitations, and rehearse the presentation.'),('h','Coordinate Simply'),('b','Use the two-hour meeting to review progress, choose priorities, and agree on ownership.'),('b','Keep one shared list: task, owner, status, and blocker. Hand off saved outputs as they become available.'),('b','Keep the core workflow reproducible in Python. Pramukh can use GIS software for review if helpful.'),('h','Time and Priorities'),('b','Nalini: about 20 hours total, including the meeting and nine-hour hackathon.'),('b','Pramukh: about 15 hours total, including the same meeting and hackathon; schedule the remaining time flexibly.'),('b','Prioritize a working network, a usable GeoAI component, explainable routes, and a clear map. Reduce optional features if needed.'),('b','If Pramukh has extra time: check more routes, explore sensitivity to scoring assumptions, or improve the visualization.'),('h','Aim to Finish With'),('b','A working demo and reproducible code.'),('b','A concise record of sources, methods, checks, and limitations.'),('b','A five-minute presentation with backup screenshots.')]
d=Document();sec=d.sections[0]
sec.top_margin=sec.bottom_margin=Inches(.65)
for name in ['Normal','Title','Heading 1','List Bullet']:
 st=d.styles[name];st.font.name='Times New Roman';st.font.size=Pt(12);st.font.color.rgb=RGBColor(0,0,0);st.paragraph_format.space_after=Pt(4);st.paragraph_format.line_spacing=1
for kind,text in items:
 p=d.add_paragraph(text,{'title':'Title','h':'Heading 1','b':'List Bullet','p':'Normal'}[kind])
 if kind in ['h','title']:
  p.paragraph_format.space_before=Pt(8)
  for r in p.runs:r.bold=True
h=sec.header.paragraphs[0];h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');h._p.append(f)
d.save(root/'EmPath_Flexible_Team_Guide.docx')
parts=[];listing=False
for kind,t in items:
 if listing and kind!='b':parts.append('</ul>');listing=False
 if kind=='b' and not listing:parts.append('<ul>');listing=True
 tag='li' if kind=='b' else 'p';sty='font-family:Times New Roman,serif;font-size:12pt;color:#000;margin-bottom:6pt;'
 if kind in ['h','title']:sty+='font-weight:bold;margin-top:12pt;'
 parts.append(f'<{tag} style="{sty}">{escape(t)}</{tag}>')
if listing:parts.append('</ul>')
s='<!doctype html><html><head><meta charset="utf-8"><title>EmPath Team Work Guide</title></head><body style="font-family:Times New Roman,serif;font-size:12pt;color:#000;background:white;max-width:7in;margin:32px auto;line-height:1.1">'+''.join(parts)+'</body></html>'
(root/'EmPath_Flexible_Team_Guide_Copy_Paste.html').write_text(s)
# Update the previously shared copy-paste link so its refreshed tab shows the revision.
(root/'EmPath_Concise_Team_Work_Plan_Copy_Paste.html').write_text(s)
