from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib import font_manager,rcParams
out=Path('output/roadmap_checklist/diagrams')
for n in ['Times New Roman.ttf','Times New Roman Bold.ttf']:font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/'+n)
rcParams['font.family']='Times New Roman'
def box(ax,x,y,w,h,title,sub):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.025',facecolor='#f3f5f6',edgecolor='#374b55',linewidth=1.2))
 ax.text(x+w/2,y+h*.67,title,ha='center',va='center',fontsize=12,fontweight='bold');ax.text(x+w/2,y+h*.30,sub,ha='center',va='center',fontsize=10)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,linewidth=1.4,color='#374b55'))
fig,ax=plt.subplots(figsize=(10.8,3.3));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
labels=[('1. Inventory','0.5 hour'),('2. Clean data','2 hours'),('3. Build graph','2.5 hours'),('4. Add features','2 hours'),('5. Adapt GeoAI','3 hours'),('6. Route and rank','1.5 hours'),('7. Evaluate and map','2 hours'),('8. Package and present','1.5 hours')]
positions=[(.025,.60),(.275,.60),(.525,.60),(.775,.60),(.775,.12),(.525,.12),(.275,.12),(.025,.12)]
for (title,sub),(x,y) in zip(labels,positions):box(ax,x,y,.20,.27,title,sub)
for i in range(3):arrow(ax,(positions[i][0]+.205,.735),(positions[i+1][0]-.015,.735))
arrow(ax,(.875,.58),(.875,.41))
for i in range(4,7):arrow(ax,(positions[i][0]-.015,.255),(positions[i+1][0]+.215,.255))
ax.text(.5,.015,'15 hours of core work + up to 3 hours for troubleshooting and polish',ha='center',fontsize=11)
fig.savefig(out/'01_project_pathway.png',dpi=300,bbox_inches='tight',pad_inches=.12,facecolor='white');plt.close(fig)
fig,ax=plt.subplots(figsize=(10.8,4.4));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,.025,.64,.25,.22,'Public spatial inputs','Walking network, origins,\ndestinations, canopy / imagery')
box(ax,.375,.64,.25,.22,'Existing GeoAI model','Reuse or adapt; record\ninputs, outputs and validation')
box(ax,.725,.64,.25,.22,'Edge features','Distance + supported predictions\n+ missing-data flags')
arrow(ax,(.285,.75),(.36,.75));arrow(ax,(.635,.75),(.71,.75))
box(ax,.725,.15,.25,.23,'Nonnegative edge costs','Model-derived terms + explicit\npreference / scenario assumptions')
box(ax,.375,.15,.25,.23,'Network routing','Find minimum total cost;\ncompare distance-only routes')
box(ax,.025,.15,.25,.23,'Residential comparison','Best reachable destination\nin each of three categories')
arrow(ax,(.85,.62),(.85,.40));arrow(ax,(.71,.265),(.64,.265));arrow(ax,(.36,.265),(.29,.265))
ax.text(.5,.035,'GeoAI predicts or estimates; routing selects paths. Keep the two components separate.',ha='center',fontsize=11)
fig.savefig(out/'02_system_architecture.png',dpi=300,bbox_inches='tight',pad_inches=.12,facecolor='white');plt.close(fig)
