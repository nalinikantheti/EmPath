import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,rcParams
for n in ['Times New Roman.ttf','Times New Roman Bold.ttf']:font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/'+n)
rcParams.update({'font.family':'Times New Roman','font.size':12,'text.color':'black'})
fig=plt.figure(figsize=(6.4,3.2));ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
ax.plot([.1,.9],[.68,.68],color='black',lw=1.6);ax.scatter([.1,.9],[.68,.68],color='black',s=25)
ax.plot([.1,.30,.70,.9],[.50,.35,.35,.50],color='black',lw=1.6,ls='--');ax.scatter([.1,.9],[.50,.50],color='black',s=25)
ax.text(.5,.84,'Route A: 400 m; example total cost 700 units',ha='center',fontsize=12)
ax.text(.5,.58,'Shorter, with a larger exposure penalty',ha='center',fontsize=12)
ax.text(.5,.27,'Route B: 600 m; example total cost 650 units',ha='center',fontsize=12)
ax.text(.5,.19,'Longer, but lower modeled friction',ha='center',fontsize=12)
ax.text(.1,.96,'Home',ha='center',fontweight='bold',fontsize=12);ax.text(.9,.96,'Pharmacy',ha='center',fontweight='bold',fontsize=12)
ax.text(.5,.065,'Illustrative values only; not measured routes\nor model predictions.',ha='center',fontsize=12,va='center')
fig.savefig('output/roadmap_guide/EmPath_Route_Example.png',dpi=300,facecolor='white');plt.close(fig)
