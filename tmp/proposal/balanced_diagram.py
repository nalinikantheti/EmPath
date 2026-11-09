import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
from matplotlib import font_manager,rcParams
for n in ['Times New Roman.ttf','Times New Roman Bold.ttf']:font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/'+n)
rcParams.update({'font.family':'Times New Roman','font.size':12,'text.color':'black'})
fig=plt.figure(figsize=(6.4,3.2));ax=fig.add_axes([0,0,1,1]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
positions=[(.02,.58),(.36,.58),(.70,.58),(.70,.08),(.36,.08),(.02,.08)]
labels=[('Spatial inputs','Network, origins,\ndestinations and canopy'),('Existing GeoAI','Reuse and adapt\none suitable model'),('Edge features','Distance, predictions\nand missing-data flags'),('Edge costs','Nonnegative costs;\nstate assumptions'),('Routing','Lowest-friction and\ndistance-only routes'),('Residential ranking','Combine access to\nthree service categories')]
for (x,y),(title,sub) in zip(positions,labels):
 ax.add_patch(FancyBboxPatch((x,y),.28,.32,boxstyle='round,pad=0.008,rounding_size=0.015',facecolor='white',edgecolor='black',linewidth=1))
 ax.text(x+.14,y+.235,title,ha='center',va='center',fontsize=12,fontweight='bold');ax.text(x+.14,y+.105,sub,ha='center',va='center',fontsize=12)
for a,b in [((.31,.74),(.345,.74)),((.65,.74),(.685,.74)),((.84,.56),(.84,.42)),((.685,.24),(.65,.24)),((.345,.24),(.31,.24))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=11,color='black',linewidth=1))
fig.savefig('output/roadmap_guide/EmPath_Workflow.png',dpi=300,facecolor='white');plt.close(fig)
