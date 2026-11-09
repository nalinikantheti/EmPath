from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
p=Path('output/roadmap_guide');d=Document();s=d.sections[0];s.top_margin=s.bottom_margin=Inches(.7);s.left_margin=s.right_margin=Inches(.8)
for name in ['Normal','Title','Heading 1','Heading 2','List Bullet']:
 st=d.styles[name];st.font.name='Times New Roman';st.font.size=Pt(12);st.font.color.rgb=RGBColor(0,0,0)
 st.paragraph_format.space_after=Pt(5);st.paragraph_format.line_spacing=1.05
for name in ['Heading 1','Heading 2']:d.styles[name].paragraph_format.space_before=Pt(10)
def para(t,style=None):return d.add_paragraph(t,style)
def bullet(t):para(t,'List Bullet')
def head(t):para(t,'Heading 1')
para('EmPath Team Work Plan','Title')
para('Scope: Plano ZIP areas 75025, 75024, 75023, and 75074.')
bullet('Nalini — 20 hours: implementation, routing, map, and presentation.')
bullet('Pramukh — 15 hours: GIS review, model evaluation, and troubleshooting.')
bullet('Both totals include the same two-hour team meeting.')
head('1 Before the Hackathon')
para('Nalini — 9 hours','Heading 2')
for t in ['1 hour: Confirm Python setup; complete sources and coverage checklist.','2 hours: Clean boundaries, walking data, residential origins, and destinations.','2.5 hours: Build walking graph; connect origins and destinations.','2 hours: Add canopy and environmental features.','1.5 hours: Select and test an existing GeoAI model or workflow.']:bullet(t)
para('Pramukh — 4 flexible hours outside the hackathon','Heading 2')
for t in ['1 hour: Review roadmap, data coverage, and model approach.','3 hours: Fix a priority network/data gap, reproduce the model workflow, or verify entrances and crossings.','Return reviewed files, documented fixes, and unresolved issues. Schedule when available; Nalini continues independently if needed.']:bullet(t)
head('2 Shared Team Meeting')
para('Two hours each, already included in both budgets.')
for t in ['30 minutes: Confirm scope and minimum demo.','30 minutes: Review walking graph and data gaps.','30 minutes: Agree on GeoAI approach and evaluation.','30 minutes: Assign tasks and handoffs. Save one shared task list.']:bullet(t)
head('3 Hackathon')
para('Nine hours each. Nalini reserves hours 6–9 for packaging and presentation.')
for h,ts in [('Hours 0 to 4',['Nalini: Finish GeoAI adapter; calculate routes and residential rankings.','Pramukh: Audit GIS layers, connections, entrances, and at least one route per ZIP.']),('Hours 4 to 7',['Nalini: Finish the map and priority fixes by hour 6; then begin packaging and slides.','Pramukh: Check model outputs; compare distance-only and friction routes; test two penalty settings.']),('Hours 7 to 9',['Nalini: Finalize demo, README, backup, and five-minute presentation.','Pramukh: Resolve final issues, verify results, and rehearse.'])]:
 para(h,'Heading 2')
 for t in ts:bullet(t)
head('4 Required Deliverables')
bullet('Nalini: Sources checklist; clean data; walking graph and features; runnable GeoAI component; routes and rankings; interactive map; README; slides and backup.')
bullet('Pramukh: Network audit with flagged locations and fixes; model/route evaluation; limitations and completed checks.')
head('5 Optional Work for Pramukh')
para('Only after the planned 15 hours, if more time is available.')
for t in ['1 hour: Verify additional routes and destinations.','1–2 hours: Test how penalty settings affect residential rankings.','2–3 hours: Compare a second existing model if compatible data and labels are available.','Prioritize fixes and validation before new features.']:bullet(t)
head('6 Working Rules')
for t in ['Exchange GraphML, GeoPackage, and CSV files with stable IDs and documented units.','Pramukh may review in Python or ArcGIS Pro; Nalini maintains the Python pipeline.','Track issues in one list: Problem → Owner → Fix → Status.','If behind, reduce sampled homes or optional layers; retain all four ZIP areas.']:bullet(t)
head('Time Check')
bullet('Nalini: 9 hours preparation + 2 hours meeting + 9 hours hackathon = 20 hours.')
bullet('Pramukh: 4 flexible hours + 2 hours meeting + 9 hours hackathon = 15 hours.')
h=s.header.paragraphs[0];h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');h._p.append(f)
for st in d.styles:
 if st.type==1:st.font.name='Times New Roman';st.font.size=Pt(12);st.font.color.rgb=RGBColor(0,0,0)
for x in d.paragraphs:
 for r in x.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
d.save(p/'EmPath_Concise_Team_Work_Plan.docx')
