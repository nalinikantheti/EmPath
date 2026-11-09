from pathlib import Path
from docx import Document
from docx.shared import Pt,RGBColor
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import html
root=Path('output/roadmap_guide');doc=Document(root/'EmPath_Team_Implementation_Roadmap.docx')
changes={
'Budget: one week, 15 hours of core work plus up to 3 hours for troubleshooting and polish.':'Your budget: 20 hours this week, including a two-hour team meeting and the nine-hour hackathon.',
'Your budget remains 15–18 hours including the two-hour team meeting. Use Parmukh’s review to share existing tasks; reduce sampled origins or optional layers to protect the time limit.':'Your 20-hour budget includes nine hours of individual preparation, a two-hour team meeting and nine hours at the hackathon. Use the personal schedule below to allocate your time.',
'Continue Steps 1–8 in order. Own the runnable network, GeoAI adapter, routing, map and slides; share saved outputs for review as soon as they exist. The meeting replaces part of the original troubleshooting/polish allowance. If time gets tight, delegate review effort already budgeted in Steps 3 and 7 rather than add work.':'Own the runnable network, GeoAI adapter, routing, map and slides. Follow the 20-hour personal schedule below and share outputs with Parmukh as they become available. His review runs alongside your implementation; it does not add hours to your budget.'}
for p in doc.paragraphs:
 for old,new in changes.items():
  if old in p.text:p.text=p.text.replace(old,new)
# Keep the overview step estimates aligned with the personal schedule (meeting listed separately).
for table in doc.tables:
 if len(table.rows)==9 and len(table.columns)==3:
  for row,t in zip(table.rows[1:],['1 h','2 h','2.5 h','2 h','3 h','2 h','2.5 h','3 h']):row.cells[1].text=t
anchor=next(p for p in doc.paragraphs if p.text=='Team Roles and Handoffs')
items=[
('Your 20 Hour Work Roadmap','Heading 1'),
('Total: 9 hours of individual preparation + 2 hours meeting + 9 hours hackathon = 20 hours. The step estimates on page 1 total 18 hours of individual work; the meeting adds two hours. Parmukh’s 12 hours are a separate contribution, with the same meeting counted once for each person.','Normal'),
('Before the Hackathon  9 hours','Heading 2'),
('1. Sources and setup — 1 hour. Open the workspace and confirm the Python environment. Complete the sources and four-ZIP coverage checklist. Deliverable: a clear list of available inputs and gaps (Step 1).','Normal'),
('2. Clean essential data — 2 hours. Prepare boundaries, walking data, a small residential sample and verified destinations. Check IDs, missing values and coordinate systems. Deliverable: cleaned layers and quality report (Step 2).','Normal'),
('3. Build the walking graph — 2.5 hours. Build and save the network; attach origins and destinations; flag disconnected locations and questionable connectors. Deliverable: GraphML, access connectors and draft network audit (Step 3).','Normal'),
('4. Add environmental features — 2 hours. Sample canopy, preserve missingness and document units and provenance. Deliverable: edge features and data dictionary (Step 4).','Normal'),
('5. Prepare the GeoAI adapter — 1.5 hours. Select a feasible existing model or released workflow, check its inputs and license, and attempt the first run. Deliverable: runnable starting notebook or a documented blocker (first half of Step 5).','Normal'),
('Team Meeting  2 hours','Heading 2'),
('Meet once the graph and first model attempt are ready. Review scope and user needs, data/network gaps, GeoAI and evaluation, then task ownership: 30 minutes each. Give Parmukh saved layers and a prioritized issue list. Deliverable: TEAM_HANDOFF.md and agreed hackathon tasks. If an output is unfinished, review the blocker instead.','Normal'),
('At the Hackathon  9 hours','Heading 2'),
('Hours 0–1.5: finish the GeoAI adapter and model card (complete Step 5). Parmukh begins GIS review using your saved graph and layers.','Normal'),
('Hours 1.5–3.5: calculate distance-only and friction routes; rank residential origins (Step 6). Deliverable: routes and rankings. Send a comparison pair to Parmukh for evaluation.','Normal'),
('Hours 3.5–6: build the Folium demo, compare scenarios and integrate priority audit findings (Step 7). Deliverable: interactive map, evaluation results and limitations. Parmukh completes GIS review and model/results checks.','Normal'),
('Hours 6–9: freeze the demo, finish README and five-minute slides, save a backup and rehearse (Step 8). Parmukh uses the final two hours for integration and rehearsal support. Deliverable: reproducible demo and presentation package.','Normal'),
('Time Limit Rule','Heading 2'),
('Protect the final three hours for packaging and presentation. Reduce sampled origins or optional layers if needed; keep all four ZIP areas represented. The minimum demo needs a runnable, documented GeoAI component, explainable routes and disclosed data gaps.','Normal')]
for text,style in items:
 e=OxmlElement('w:p');anchor._p.addprevious(e);p=Paragraph(e,anchor._parent);p.style=style;p.add_run(text)
 p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(6);p.paragraph_format.space_before=Pt(8 if style.startswith('Heading') else 0)
 if text=='Your 20 Hour Work Roadmap':p.paragraph_format.page_break_before=True
# Update all typography after replacement, including overview table cells.
for p in list(doc.paragraphs)+[p for t in doc.tables for row in t.rows for c in row.cells for p in c.paragraphs]:
 for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12);r.font.color.rgb=RGBColor(0,0,0)
out=root/'EmPath_20_Hour_Team_Roadmap.docx';doc.save(out)
s=(root/'EmPath_Team_Roadmap_Copy_Paste.html').read_text()
for old,new in changes.items():s=s.replace(html.escape(old),html.escape(new))
# Time cells in the existing overview table.
import re
start=s.index('<table');end=s.index('</table>',start)
chunk=s[start:end];times=iter(['1 h','2 h','2.5 h','2 h','3 h','2 h','2.5 h','3 h'])
chunk=re.sub(r'<td>\s*(?:0\.5|1\.5|2\.5|2|3) h\s*</td>',lambda m:'<td>'+next(times)+'</td>',chunk)
s=s[:start]+chunk+s[end:]
block=''.join('<'+('h2' if sty=='Heading 1' else 'h3' if sty=='Heading 2' else 'p')+'>'+html.escape(t)+'</'+('h2' if sty=='Heading 1' else 'h3' if sty=='Heading 2' else 'p')+'>' for t,sty in items)
s=s.replace('<h2>Team Roles and Handoffs</h2>',block+'<h2>Team Roles and Handoffs</h2>')
(root/'EmPath_20_Hour_Roadmap_Copy_Paste.html').write_text(s)
print(out)
