from pathlib import Path
from docx import Document
from docx.shared import Pt,RGBColor
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import html
root=Path('output/roadmap_guide')
doc=Document(root/'EmPath_Guide_Citations_and_Page_Numbers.docx')
changes={
'Use 15 hours for the core workflow and up to 3 additional hours for blockers or polish. Reduce sampled origins or optional layers before expanding the interface or model.':'Your budget remains 15–18 hours including the two-hour team meeting. Use Parmukh’s review to share existing tasks; reduce sampled origins or optional layers to protect the time limit.',
'Optional teammate: own either network/data QA or model evaluation, with a specific file and documented check to return.':'Parmukh supports GIS quality checks and model evaluation, mainly on hackathon day. You own the Python pipeline, integration, map and presentation. See the team plan below.'}
for p in doc.paragraphs:
 if p.text in changes:p.text=changes[p.text]
anchor=next(p for p in doc.paragraphs if p.text=='References')
items=[
('Team Roles and Handoffs','Heading 1'),
('Keep the same prototype and four-ZIP scope. Parmukh contributes approximately 12 hours total, including a two-hour team meeting. The allocation below is a proposed schedule; only one hour of individual preparation is expected before hackathon day.','Normal'),
('1  Shared Planning Meeting  2 hours each','Heading 2'),
('Review the current demo, four-area coverage and model approach. Spend 30 minutes on scope and user needs, 30 on graph and data gaps, 30 on GeoAI and evaluation, and 30 on owners and handoffs. Save decisions in docs/TEAM_HANDOFF.md. Count these two hours inside both people’s budgets.','Normal'),
('2  Parmukh Preparation  1 hour','Heading 2'),
('Read the roadmap, coverage checklist and model card. Identify the three highest-priority GIS or modeling risks and add comments to TEAM_HANDOFF.md. No new dataset or model is required before the event.','Normal'),
('3  Parmukh GIS Review  4 hours on hackathon day','Heading 2'),
('Review outputs from Steps 2–4: coordinate systems, missing features by ZIP, disconnected origins, destination entrances and major crossings. Check at least one route per ZIP. Return network_audit.md and a small GeoPackage or CSV of flagged locations, suggested fixes and unresolved issues.','Normal'),
('4  Parmukh Model and Results Review  3 hours on hackathon day','Heading 2'),
('Review Steps 5–7: model inputs, output meaning, nonnegative edge costs and separation of learned terms from assumptions. Check one distance-versus-friction route pair and two penalty settings. Return evaluation.csv and concise additions to MODEL_CARD.md and LIMITATIONS.md. If usable labels exist, report the appropriate validation metric; otherwise report sensitivity and data checks.','Normal'),
('5  Parmukh Integration and Rehearsal  2 hours on hackathon day','Heading 2'),
('Help resolve priority defects, verify the final map and review the five-minute story. Return a short list of checked results and remaining limitations. Total: 2 hours meeting + 1 preparation + 4 GIS review + 3 evaluation + 2 integration = 12 hours.','Normal'),
('Your Implementation Priorities','Heading 2'),
('Continue Steps 1–8 in order. Own the runnable network, GeoAI adapter, routing, map and slides; share saved outputs for review as soon as they exist. The meeting replaces part of the original troubleshooting/polish allowance. If time gets tight, delegate review effort already budgeted in Steps 3 and 7 rather than add work.','Normal'),
('Handoff Rules','Heading 2'),
('Use a stable snapshot of GraphML, GeoPackage and CSV outputs, with units and file paths. Parmukh can review in Python or ArcGIS Pro; return portable files and documented findings. You integrate changes into the Python pipeline. If he is unavailable before the event, continue the core build and queue his review for hackathon day.','Normal')]
for text,style in items:
 e=OxmlElement('w:p');anchor._p.addprevious(e);p=Paragraph(e,anchor._parent);p.style=style;p.add_run(text)
 p.paragraph_format.line_spacing=1.05
 p.paragraph_format.space_after=Pt(6)
 p.paragraph_format.space_before=Pt(8 if style.startswith('Heading') else 0)
 if text=='Team Roles and Handoffs':p.paragraph_format.page_break_before=True
for p in doc.paragraphs:
 for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
out=root/'EmPath_Team_Implementation_Roadmap.docx';doc.save(out)
s=(root/'EmPath_Guide_Citations_Copy_Paste.html').read_text()
for old,new in changes.items():s=s.replace(html.escape(old),html.escape(new))
block=''.join('<'+('h2' if sty=='Heading 1' else 'h3' if sty=='Heading 2' else 'p')+'>'+html.escape(t)+'</'+('h2' if sty=='Heading 1' else 'h3' if sty=='Heading 2' else 'p')+'>' for t,sty in items)
s=s.replace('<h2>References</h2>',block+'<h2>References</h2>')
(root/'EmPath_Team_Roadmap_Copy_Paste.html').write_text(s)
print(out)
