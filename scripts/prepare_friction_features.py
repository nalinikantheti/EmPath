"""Direction-consistent environmental features, without invented composite weights."""
from pathlib import Path
import json
import geopandas as gpd
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/friction_features'


def normalize_features(df):
    out=df.copy()
    canopy=pd.to_numeric(out.canopy_mean,errors='coerce')
    traffic=pd.to_numeric(out.traffic_index_0_100,errors='coerce')
    out['canopy_cover_01']=(canopy/100).where(canopy.between(0,100))
    out['canopy_deficit_01']=1-out.canopy_cover_01
    out['traffic_burden_01']=(traffic/100).where(traffic.between(0,100))
    out['environment_features_complete']=out[['canopy_deficit_01','traffic_burden_01']].notna().all(axis=1)
    if 'length' in out:
        out['distance_km']=pd.to_numeric(out.length,errors='coerce')/1000
    # Constant regional weather has no meaningful within-area z-score.
    out['weather_is_spatially_discriminating']=False
    return out


def scenario_score(df,canopy_weight,traffic_weight):
    weights=np.array([canopy_weight,traffic_weight],dtype=float)
    if not np.isfinite(weights).all() or (weights<0).any() or weights.sum()<=0:
        raise ValueError('Explicit finite nonnegative scenario weights with positive sum required.')
    weights=weights/weights.sum()
    values=df[['canopy_deficit_01','traffic_burden_01']]
    needed=values.iloc[:,weights>0].notna().all(axis=1)
    result=values.fillna(0).to_numpy()@weights
    return pd.Series(result,index=df.index).where(needed)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    base=ROOT/'output/clean_deliverables'
    blocks=normalize_features(gpd.read_file(base/'block_environment.gpkg'))
    edges=normalize_features(gpd.read_file(base/'walking_edges.gpkg'))
    blocks.to_file(OUT/'normalized_blocks.gpkg',driver='GPKG',index=False)
    blocks.drop(columns='geometry').to_csv(OUT/'normalized_blocks.csv',index=False)
    keep=['u','v','key','length','distance_km','baseline_walk_seconds','canopy_cover_01','canopy_deficit_01','traffic_burden_01','environment_features_complete','weather_is_spatially_discriminating','geometry']
    edges[keep].to_file(OUT/'normalized_edges.gpkg',driver='GPKG',index=False)
    edges[keep].drop(columns='geometry').to_csv(OUT/'normalized_edges.csv',index=False)
    metadata={'features':{'canopy_deficit_01':'1 − estimated canopy cover/100. Higher = less canopy; not measured sun exposure.',
        'traffic_burden_01':'City-of-Plano-referenced traffic normal-CDF index / 100. Higher = more nearby traffic.',
        'distance_km':'Length in meters /1000; retain additive distance rather than per-edge min-max scaling.',
        'weather':'Regional June-August 2025 afternoon scenario constant across scope; no spatial normalization or separate heat-index term invented.'},
        'composite_score_created':False,'weights':'Must be supplied explicitly as assumptions or learned from suitable labels. Same numeric range does not imply equivalent walking burden.',
        'missing_policy':'Retain NaN and feature-completeness flag; never treat unknown as zero burden.',
        'reference':'Traffic normalized against the City of Plano; canopy uses its physical percent scale because no city-wide canopy reference was computed.'}
    (OUT/'feature_dictionary.json').write_text(json.dumps(metadata,indent=2))
    print('Normalized features saved:',len(blocks),'blocks and',len(edges),'directed edges. No arbitrary composite created.',flush=True)

if __name__=='__main__':main()
