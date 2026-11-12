"""Replace only canopy attributes after corrected raster decoding; preserve traffic/address fields."""
from pathlib import Path
import gzip,json,shutil
import geopandas as gpd
import numpy as np
import pandas as pd
import osmnx as ox
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/clean_deliverables'


def main():
    base=gpd.read_file(OUT/'block_environment.gpkg')
    new=gpd.read_file(ROOT/'output/environment_features/block_environment.gpkg')
    columns=[c for c in new if c.startswith('canopy_')]
    attrs=new[['GEOID20']+columns]
    base=base.drop(columns=[c for c in columns if c in base]).merge(attrs,on='GEOID20',how='left',validate='one_to_one')
    base['canopy_value_method']='Class-midpoint estimate: Not tree=0; 10–19%=14.5; ...; >=90%=95. Not exact measured percent.'
    base.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
    base.to_crs(4326).to_file(OUT/'block_environment.geojson',driver='GeoJSON',index=False)
    base.drop(columns='geometry').to_csv(OUT/'block_environment.csv',index=False)
    edges=gpd.read_file(OUT/'walking_edges.gpkg')
    new=pd.read_csv(ROOT/'output/environment_features/edge_environment_sample.csv')
    columns=[c for c in new if c.startswith('canopy_')]
    attrs=new[['u','v','key']+columns]
    edges=edges.drop(columns=[c for c in columns if c in edges]).merge(attrs,on=['u','v','key'],how='left',validate='one_to_one')
    edges.to_file(OUT/'walking_edges.gpkg',driver='GPKG',index=False)
    old=pd.read_csv(OUT/'walking_edge_attributes.csv',dtype={'block_geoid_midpoint':str})
    old=old.drop(columns=[c for c in columns if c in old]).merge(attrs,on=['u','v','key'],how='left',validate='one_to_one')
    old.to_csv(OUT/'walking_edge_attributes.csv',index=False)
    graph=ox.io.load_graphml(OUT/'walking_graph.graphml')
    for row in attrs.itertuples(index=False,name=None):
        u,v,k,*values=row
        for name,value in zip(columns,values):
            if pd.notna(value):graph.edges[u,v,k][name]=value.item() if isinstance(value,np.generic) else value
            else:graph.edges[u,v,k].pop(name,None)
    graph.graph['canopy_value_method']=base.canopy_value_method.iloc[0]
    ox.io.save_graphml(graph,OUT/'walking_graph.graphml')
    with (OUT/'walking_graph.graphml').open('rb') as src,gzip.open(OUT/'walking_graph.graphml.gz','wb') as dst:shutil.copyfileobj(src,dst)
    target=base[base.GEOID20.eq('480850319022006')]
    print('Morada address block canopy estimate:',target.canopy_mean.iloc[0],flush=True)
    report={'verified_key':'https://zenodo.org/records/8200761/files/TX_lu_ecoclass_key.xlsx','error_corrected':'Original integer canopy class codes were treated as continuous percentages.',
        'conversion':'Not tree -> 0; 10–19 -> 14.5; ...; >=90 -> 95. A within-class estimate, not observed exact cover.',
        'morada_address':'1009 14th St, Plano TX 75074','morada_block':'480850319022006','morada_estimated_canopy_percent':float(target.canopy_mean.iloc[0]),
        'note':'Morada is not the densest block in the saved dataset. Exact original clicked block is unknown; overlapping thematic fills now prevented.'}
    (OUT/'canopy_semantics_audit.json').write_text(json.dumps(report,indent=2))

if __name__=='__main__':main()
