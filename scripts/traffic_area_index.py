"""Area traffic context from nearby road centerlines; transparent z-score index.
Buffering and aggregation are declared scenarios, not learned danger scores.
"""
from datetime import datetime,timezone
from math import erf,sqrt
from pathlib import Path
import gzip,json,shutil
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import normalize
import osmnx as ox
from block_locations import add_location_fields
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/clean_deliverables'


def primary_roads(roads):
    # KG is the centerline/single-roadbed representation. Keep supplemental
    # roadbeds only for routes with no KG representation in this local extract.
    roads=roads.to_crs(26914).copy()
    base=roads.RTE_NM.str.replace(r'-[^-]+$','',regex=True)
    has_primary=set(base[roads.RDBD_TYPE.eq('KG')])
    keep=roads.RDBD_TYPE.eq('KG')|~base.isin(has_primary)
    selected=roads.loc[keep].copy()
    selected=selected[selected.aadt.notna()&selected.aadt.gt(0)]
    # Remove only identical geometry + AADT, not legitimate segmented records.
    selected['_geom']=selected.geometry.map(lambda g:normalize(g).wkb_hex)
    selected=selected.drop_duplicates(['_geom','aadt']).drop(columns='_geom')
    return selected.reset_index(drop=True)


def area_summary(zones,roads,buffer_m=100,batch_size=2000):
    """Length-weighted mean over road portions within the buffered zone.
All intersections must have positive length; point touches have no weight.
"""
    if buffer_m<0:raise ValueError('Buffer must be nonnegative')
    zones=zones.to_crs(26914).reset_index(drop=True)
    roads=roads.to_crs(26914).reset_index(drop=True)
    results=[]
    for start in range(0,len(zones),batch_size):
        geom=zones.geometry.iloc[start:start+batch_size].buffer(buffer_m).reset_index(drop=True)
        zone_idx,road_idx=roads.sindex.query(geom,predicate='intersects')
        weighted=np.zeros(len(geom));lengths=np.zeros(len(geom));counts=np.zeros(len(geom),dtype=int)
        maxima=np.full(len(geom),-np.inf)
        if len(zone_idx):
            left=gpd.GeoSeries(geom.iloc[zone_idx].to_numpy(),crs=26914)
            right=gpd.GeoSeries(roads.geometry.iloc[road_idx].to_numpy(),crs=26914)
            length=left.intersection(right,align=False).length.to_numpy()
            vals=roads.aadt.iloc[road_idx].to_numpy(dtype=float)
            valid=(length>1e-6)&np.isfinite(vals)
            i=zone_idx[valid];length=length[valid];vals=vals[valid]
            np.add.at(weighted,i,length*vals);np.add.at(lengths,i,length);np.add.at(counts,i,1)
            np.maximum.at(maxima,i,vals)
        mean=np.divide(weighted,lengths,out=np.full(len(geom),np.nan),where=lengths>0)
        maxima[~np.isfinite(maxima)]=np.nan
        results.append(pd.DataFrame({'traffic_area_mean_aadt':mean,'traffic_area_max_aadt':maxima,
            'traffic_road_length_m':lengths,'traffic_road_section_count':counts,
            'traffic_area_buffer_m':buffer_m}))
    return pd.concat(results,ignore_index=True)


def normalize_traffic(values,parameters=None):
    values=pd.to_numeric(values,errors='coerce');valid=values.notna()&values.ge(0)
    logs=np.log1p(values.where(valid))
    if parameters is None:
        if valid.sum()<2:raise ValueError('Need at least two valid areas to standardize')
        parameters={'raw_mean':float(values[valid].mean()),'raw_std':float(values[valid].std(ddof=0)),
                    'log_mean':float(logs[valid].mean()),'log_std':float(logs[valid].std(ddof=0)),
                    'reference':'All four-ZCTA clipped census blocks with valid mapped road lengths; equal weight per block',
                    'ddof':0}
    zlog=(logs-parameters['log_mean'])/parameters['log_std'] if parameters['log_std']>0 else logs*0
    zraw=(values.where(valid)-parameters['raw_mean'])/parameters['raw_std'] if parameters['raw_std']>0 else values*0
    # Normal-CDF score, not a percentile rank or probability of danger.
    index=zlog.map(lambda z:50*(1+erf(z/sqrt(2))) if pd.notna(z) else np.nan)
    return pd.DataFrame({'traffic_z_raw':zraw,'traffic_z_log':zlog,'traffic_index_0_100':index}),parameters


def main():
    blocks=gpd.read_file(OUT/'block_environment.gpkg')
    reference_folder=ROOT/'data/processed/plano_reference'
    if not (reference_folder/'plano_reference_blocks.gpkg').exists():
        raise FileNotFoundError('Run scripts/prepare_plano_reference.py before using the Plano reference.')
    original=gpd.read_file(reference_folder/'traffic_roads.gpkg')
    roads=primary_roads(original)
    summary=area_summary(blocks,roads)
    reference_blocks=gpd.read_file(reference_folder/'plano_reference_blocks.gpkg')
    reference_summary=area_summary(reference_blocks,roads)
    reference_normalized,parameters=normalize_traffic(reference_summary.traffic_area_mean_aadt)
    parameters.update(reference='2020 census block portions with positive area inside official Plano municipal boundary; equal weight per valid block',
        reference_area='City of Plano',reference_total_blocks=len(reference_blocks),reference_valid_blocks=int(reference_summary.traffic_area_mean_aadt.notna().sum()),
        city_boundary_source='https://maps.planogis.org/arcgiswad/rest/services/OpenData/MunicipalBoundary/FeatureServer/0')
    reference_values=reference_blocks[['GEOID20','city_area_fraction']].reset_index(drop=True).join(reference_summary).join(reference_normalized)
    reference_values.to_csv(OUT/'plano_reference_traffic.csv',index=False)
    normalized,_=normalize_traffic(summary.traffic_area_mean_aadt,parameters)
    columns=list(summary)+list(normalized)
    blocks=blocks.drop(columns=[c for c in columns if c in blocks]).reset_index(drop=True).join(summary).join(normalized)
    sensitivity={}
    for radius in [50,200]:
        alternate=area_summary(blocks,roads,radius).traffic_area_mean_aadt
        sensitivity[str(radius)]={'rank_correlation_with_100m':float(alternate.rank().corr(summary.traffic_area_mean_aadt.rank())),
            'matched_blocks':int(alternate.notna().sum())}
    blocks=add_location_fields(blocks)
    blocks.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
    blocks.to_crs(4326).to_file(OUT/'block_environment.geojson',driver='GeoJSON',index=False)
    blocks.drop(columns='geometry').to_csv(OUT/'block_environment.csv',index=False)
    print('Block traffic aggregation and standardization complete.',flush=True)
    edges=gpd.read_file(OUT/'walking_edges.gpkg')
    # Preserve all directed edge identities while scoring reciprocal geometry once.
    keys=edges.geometry.map(lambda g:normalize(g).wkb_hex);keep=~keys.duplicated()
    unique=edges.loc[keep,['geometry']].reset_index(drop=True)
    edge_summary=area_summary(unique,roads)
    edge_norm,_=normalize_traffic(edge_summary.traffic_area_mean_aadt,parameters)
    edge_values=edge_summary.join(edge_norm);edge_values.index=keys[keep].to_numpy()
    restored=edge_values.reindex(keys.to_numpy()).reset_index(drop=True)
    edges=edges.drop(columns=[c for c in columns if c in edges]).reset_index(drop=True).join(restored)
    edges.to_file(OUT/'walking_edges.gpkg',driver='GPKG',index=False)
    # Preserve the existing ancillary fields in the CSV and append corrected metrics.
    csv=pd.read_csv(OUT/'walking_edge_attributes.csv',dtype={'block_geoid_midpoint':str})
    csv=csv.drop(columns=[c for c in columns if c in csv])
    csv=csv.merge(edges[['u','v','key']+columns],on=['u','v','key'],how='left',validate='one_to_one')
    csv.to_csv(OUT/'walking_edge_attributes.csv',index=False)
    graph=ox.io.load_graphml(OUT/'walking_graph.graphml')
    for row in edges[['u','v','key']+columns].itertuples(index=False,name=None):
        u,v,k,*values=row
        for name,value in zip(columns,values):
            if pd.notna(value):graph.edges[u,v,k][name]=value.item() if isinstance(value,np.generic) else value
            else:graph.edges[u,v,k].pop(name,None)
    graph.graph['traffic_area_index_method']='100m nearby primary-centerline length-weighted mean AADT; log1p z-score using official City of Plano block reference; 0–100 normal-CDF transform; not validated danger or learned routing cost.'
    graph.graph['traffic_reference_parameters']=json.dumps(parameters)
    ox.io.save_graphml(graph,OUT/'walking_graph.graphml')
    with (OUT/'walking_graph.graphml').open('rb') as src,gzip.open(OUT/'walking_graph.graphml.gz','wb') as dst:shutil.copyfileobj(src,dst)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
    highway=roads[roads.RTE_PRFX.isin(['IH','US','SH'])&roads.aadt.ge(50000)]
    audit=[]
    for _,ziprow in scope.iterrows():
        sample=blocks.to_crs(26914).geometry.representative_point().within(ziprow.geometry)
        z=blocks[sample]
        nearby=highway[highway.intersects(ziprow.geometry.buffer(100))]
        audit.append({'zcta':str(ziprow.ZCTA5),'blocks':len(z),'unique_mean_aadt':int(z.traffic_area_mean_aadt.nunique()),
            'median_mean_aadt':float(z.traffic_area_mean_aadt.median()),'median_index':float(z.traffic_index_0_100.median()),
            'highway_sections_ge_50000_within_100m':len(nearby),
            'highway_max_aadt':float(nearby.aadt.max()) if len(nearby) else None})
    pd.DataFrame(audit).to_csv(OUT/'traffic_index_by_zip.csv',index=False)
    report={'created_utc':datetime.now(timezone.utc).isoformat(),'normalization':parameters,
        'input_road_sections':len(original),'selected_primary_road_sections':len(roads),
        'buffer_m':100,'sensitivity':sensitivity,'by_zip':audit,
        'pilot_block_z_mean':float(blocks.traffic_z_log.mean()),'pilot_block_z_std':float(blocks.traffic_z_log.std(ddof=0)),
        'reference_z_mean':float(reference_normalized.traffic_z_log.mean()),'reference_z_std':float(reference_normalized.traffic_z_log.std(ddof=0)),
        'block_index_min':float(blocks.traffic_index_0_100.min()),'block_index_max':float(blocks.traffic_index_0_100.max()),
        'missing_blocks':int(blocks.traffic_index_0_100.isna().sum()),
        'note':'Length-weighted mean is not total vehicles in an area. Source sectioning does not change weighting. Primary centerlines avoid repeated roadbed representations; unsourced gaps stay unknown. Shared 179 source estimates are retained, not perturbed. Z-scores are not additive routing costs.'}
    (OUT/'traffic_index_method.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
