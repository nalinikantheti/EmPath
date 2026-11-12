"""Add real mapped addresses inside blocks; label outside references separately."""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/clean_deliverables'


def main():
    blocks=gpd.read_file(OUT/'block_environment.gpkg').to_crs(26914)
    address=gpd.read_file(ROOT/'data/processed/75023_75024_75025_75074_buffer250m/address_points.gpkg').to_crs(26914)
    address=address[address.address.notna()&address.addrnum.notna()].copy()
    address['formatted_address']=address.apply(lambda r:', '.join(str(v).strip() for v in [r.address,r.municipality,r.zipcode] if pd.notna(v) and str(v).strip()),axis=1)
    points=blocks.set_index('GEOID20').geometry.representative_point()
    joined=gpd.sjoin(address[['source_id','formatted_address','geometry']],blocks[['GEOID20','geometry']],how='inner',predicate='within')
    comparison=gpd.GeoSeries(joined.GEOID20.map(points).to_numpy(),crs=26914)
    joined['distance_to_block_point_m']=joined.geometry.reset_index(drop=True).distance(comparison,align=False).to_numpy()
    selected=joined.sort_values(['distance_to_block_point_m','source_id']).drop_duplicates('GEOID20').set_index('GEOID20')
    blocks['representative_address']=blocks.GEOID20.map(selected.formatted_address).fillna('No mapped street address inside this block')
    blocks['representative_address_source_id']=blocks.GEOID20.map(selected.source_id)
    blocks['mapped_address_count']=blocks.GEOID20.map(joined.groupby('GEOID20').source_id.nunique()).fillna(0).astype(int)
    blocks['address_note']='One municipal address point inside the block, chosen near its representative point. Not the address of the whole block or a verified entrance.'
    blocks.loc[blocks.mapped_address_count.eq(0),'address_note']='No mapped address inside. A nearby address, if supplied, is outside the block and only for orientation.'
    blocks['nearby_address_reference']=None;blocks['nearby_address_distance_m']=np.nan
    missing=blocks[blocks.mapped_address_count.eq(0)]
    if len(missing):
        lookup=gpd.GeoDataFrame({'GEOID20':missing.GEOID20.to_numpy()},geometry=missing.geometry.representative_point().to_numpy(),crs=26914)
        near=gpd.sjoin_nearest(lookup,address[['source_id','formatted_address','geometry']],how='left',max_distance=500,distance_col='distance_m')
        near=near.sort_values(['distance_m','source_id']).drop_duplicates('GEOID20').set_index('GEOID20')
        blocks['nearby_address_reference']=blocks.GEOID20.map(near.formatted_address)
        blocks['nearby_address_distance_m']=blocks.GEOID20.map(near.distance_m)
    blocks.to_file(OUT/'block_environment.gpkg',driver='GPKG',index=False)
    blocks.to_crs(4326).to_file(OUT/'block_environment.geojson',driver='GeoJSON',index=False)
    blocks.drop(columns='geometry').to_csv(OUT/'block_environment.csv',index=False)
    assert (selected.index.isin(joined.GEOID20)).all()
    print('Blocks with an in-block mapped address:',int(blocks.mapped_address_count.gt(0).sum()),'of',len(blocks),flush=True)

if __name__=='__main__':main()
