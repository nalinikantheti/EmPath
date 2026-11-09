from pathlib import Path
from docx import Document
from PIL import Image,ImageDraw,ImageFont
import zipfile
out=Path('output/roadmap_guide');folder=out/'tables';folder.mkdir(exist_ok=True)
doc=Document(out/'EmPath_Implementation_Guide.docx')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman.ttf',50)
bold=ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf',50)
names=['01_time_and_deliverables','02_data_requirements','03_model_options','04_final_handoff','05_dataset_sources','06_case_studies','07_software_docs']
for index,t in enumerate(doc.tables):
 widths=[int(c.width/914400*300) for c in t.columns];scale=2100/sum(widths);widths=[int(w*scale) for w in widths];W=sum(widths)+2
 scratch=ImageDraw.Draw(Image.new('RGB',(1,1)))
 rows=[]
 for ri,row in enumerate(t.rows):
  cells=[]
  for ci,cell in enumerate(row.cells):
   text=''.join(e.text or '' for e in cell._tc.xpath('.//w:t'))
   f=bold if ri==0 else font;lines=[]
   for paragraph in text.split('\n'):
    line=''
    for word in paragraph.split():
     test=(line+' '+word).strip()
     if line and scratch.textlength(test,font=f)>widths[ci]-36:lines.append(line);line=word
     else:line=test
    lines.append(line)
   cells.append(lines)
  rows.append((cells,max(map(len,cells))*61+34))
 H=sum(h for _,h in rows)+2;im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im);y=1
 for ri,(cells,h) in enumerate(rows):
  x=1
  for ci,lines in enumerate(cells):
   d.rectangle((x,y,x+widths[ci],y+h),fill='#e8edf0' if ri==0 else 'white',outline='#bfc6ca',width=2)
   ty=y+(h-len(lines)*61)/2
   for line in lines:d.text((x+18,ty),line,font=bold if ri==0 else font,fill='black');ty+=61
   x+=widths[ci]
  y+=h
 im.save(folder/(names[index]+'.png'),dpi=(300,300))
with zipfile.ZipFile(out/'EmPath_All_Visuals.zip','w',zipfile.ZIP_DEFLATED) as z:
 z.write(out/'EmPath_Workflow.png','EmPath_Workflow.png')
 for directory in ['tables']:
  for p in sorted((out/directory).glob('*.png')):z.write(p,str(p.relative_to(out)))
print('Exported',len(doc.tables),'tables and 2 diagrams.')
