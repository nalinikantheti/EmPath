"""Render compact inspection maps from the two cleaned deliverables."""
from pathlib import Path
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.ticker import FuncFormatter
from branca.utilities import color_brewer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/clean_deliverables'


def main():
    blocks=gpd.read_file(OUT/'block_environment.gpkg')
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(blocks.crs)
    fig,axes=plt.subplots(1,2,figsize=(14,7))
    for ax,col,title,cmap in zip(axes,['canopy_mean','traffic_z_log'],
        ['Estimated 2021 canopy cover (%)','Traffic relative to City of Plano (log z-score)'],['YlGn','Blues']):
        extra={}
        if col=='traffic_z_log':
            bins=[-5,-1.5,-.5,0,.5,1,2,5]
            cmap=ListedColormap(color_brewer('Blues',n=7))
            labels=['< −1.5 SD','−1.5 to −0.5','−0.5 to 0','0 to +0.5','+0.5 to +1','+1 to +2','> +2 SD']
            centers=[(a+b)/2 for a,b in zip(bins,bins[1:])]
            extra={'norm':BoundaryNorm(bins,7),'legend_kwds':{'ticks':centers,'format':FuncFormatter(lambda v,p: labels[centers.index(v)] if v in centers else '')}}
        blocks.plot(ax=ax,column=col,cmap=cmap,legend=True,linewidth=0,
                    missing_kwds={'color':'lightgray','label':'Missing pixels'},**extra)
        scope.boundary.plot(ax=ax,color='#333',linewidth=.7)
        for _,r in scope.iterrows():
            p=r.geometry.representative_point();ax.text(p.x,p.y,str(r.ZCTA5),ha='center',fontsize=9,
                bbox={'facecolor':'white','alpha':.8,'edgecolor':'none'})
        ax.set_title(title,fontsize=12);ax.set_axis_off()
    fig.suptitle('EmPath census-block environmental context',fontsize=16)
    fig.text(.08,.04,'NOAA regional scenario: June–August 2025, noon–6 p.m. America/Chicago; median 33°C, p90 36°C.\nCanopy is not time-specific shade. Blue = standardized nearby road traffic; higher is more traffic, not measured walking danger. Missing pixels remain missing.',fontsize=9)
    fig.savefig(OUT/'block_environment_preview.png',dpi=160,bbox_inches='tight');plt.close(fig)
    edges=gpd.read_file(OUT/'walking_edges.gpkg')
    fig,ax=plt.subplots(figsize=(11,8))
    scope.boundary.plot(ax=ax,color='#777',linewidth=.7)
    edges.plot(ax=ax,color='lightgray',linewidth=.3)
    edges[edges.canopy_mean.notna()].plot(ax=ax,column='canopy_mean',cmap='YlGn',vmin=0,vmax=100,
                                          linewidth=.6,legend=True,legend_kwds={'label':'Class-derived canopy estimate in 10 m edge corridor (%)','shrink':.7})
    ax.set_title('Walking network with canopy attributes — all four ZIP areas');ax.set_axis_off()
    fig.text(.1,.02,'Raw network topology retained. Gray edges lack canopy values.\nCanopy sampled directly from raster; entrances, crossings and friction costs still need review.',fontsize=9)
    fig.savefig(OUT/'walking_canopy_preview.png',dpi=160,bbox_inches='tight');plt.close(fig)
    print('Both preview maps saved.',flush=True)

if __name__=='__main__':main()
