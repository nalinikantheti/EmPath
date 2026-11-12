"""Download and clean public TxDOT AADT roadway context for EmPath."""
from datetime import datetime,timezone
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely import make_valid
from clean_data import query
ROOT=Path(__file__).resolve().parents[1]
URL='https://services.arcgis.com/KTcxiTD9dsQw4r7Z/ArcGIS/rest/services/TxDOT_AADT/FeatureServer/0'


def main():
    raw=ROOT/'data/raw/txdot_aadt';out=ROOT/'data/processed/txdot_aadt'
    raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
    context=scope.geometry.union_all().buffer(1000)
    bbox=gpd.GeoSeries([context],crs=26914).to_crs(4326).total_bounds
    meta=raw/'metadata.json'
    if not meta.exists():meta.write_text(json.dumps(query(URL,{'f':'json'})))
    idsfile=raw/'ids.json'
    if not idsfile.exists():
        idsfile.write_text(json.dumps(query(URL+'/query',{'f':'json','where':'1=1','returnIdsOnly':'true',
            'geometry':','.join(map(str,bbox)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects'})))
    ids=sorted(json.loads(idsfile.read_text()).get('objectIds') or [])
    if not ids:raise ValueError('No traffic features returned')
    features=[]
    for i in range(0,len(ids),75):
        p=raw/f'page75_{i//75:03d}.geojson'
        if not p.exists():p.write_text(json.dumps(query(URL+'/query',{'f':'geojson','objectIds':','.join(map(str,ids[i:i+75])),
            'outFields':'*','outSR':4326,'returnGeometry':'true'})))
        features.extend(json.loads(p.read_text())['features'])
    df=gpd.GeoDataFrame.from_features(features,crs=4326)
    if len(df)!=len(ids) or not df.OBJECTID.is_unique:raise ValueError('Incomplete/duplicate source records')
    df['geometry_repaired']=~df.geometry.is_valid
    df.loc[df.geometry_repaired,'geometry']=df.loc[df.geometry_repaired].geometry.map(make_valid)
    df=df.to_crs(26914);df=df[df.intersects(context)].copy()
    df['aadt']=pd.to_numeric(df.AADT_CUR,errors='coerce').where(lambda x:x>0)
    df['aadt_year']=pd.NA  # EXT_DATE is extraction date, not automatically traffic count year.
    df['source_feature_id']=df.OBJECTID.astype(str)
    bad=df.geometry.isna()|df.geometry.is_empty|~df.geometry.is_valid|~df.geom_type.isin(['LineString','MultiLineString'])
    df[bad].drop(columns='geometry').to_csv(out/'quarantine.csv',index=False)
    df=df[~bad].copy();df.to_file(out/'traffic_roads.gpkg',driver='GPKG',index=False)
    summary={'source':URL,'processed_utc':datetime.now(timezone.utc).isoformat(),'features':len(df),
        'missing_or_nonpositive_aadt':int(df.aadt.isna().sum()),'quarantined':int(bad.sum()),
        'aadt_year':'Unknown in this service schema; do not treat EXT_DATE as count year.',
        'coverage':'Service roadway coverage only, not all local traffic; nearby AADT is contextual and does not establish crossing safety.',
        'context_buffer_m':1000}
    (out/'source_metadata.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
