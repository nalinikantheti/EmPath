import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import box,LineString
from traffic_area_index import area_summary,normalize_traffic


def test_nearby_highway_contributes_even_with_local_street():
    zones=gpd.GeoDataFrame(geometry=[box(700000,3670000,700020,3670020)],crs=26914)
    roads=gpd.GeoDataFrame({'aadt':[179,100000]},geometry=[
        LineString([(699990,3670010),(700030,3670010)]),
        LineString([(699990,3670050),(700030,3670050)])],crs=26914)
    out=area_summary(zones,roads,100)
    assert out.traffic_area_mean_aadt.iloc[0]==pytest.approx((179+100000)/2)
    assert out.traffic_area_max_aadt.iloc[0]==100000
    assert out.traffic_road_section_count.iloc[0]==2


def test_segmentation_does_not_change_area_mean():
    zones=gpd.GeoDataFrame(geometry=[box(700000,3670000,700100,3670100)],crs=26914)
    a=gpd.GeoDataFrame({'aadt':[2000]},geometry=[LineString([(700000,3670050),(700100,3670050)])],crs=26914)
    b=gpd.GeoDataFrame({'aadt':[2000,2000]},geometry=[LineString([(700000,3670050),(700050,3670050)]),LineString([(700050,3670050),(700100,3670050)])],crs=26914)
    assert area_summary(zones,a,0).traffic_area_mean_aadt.iloc[0]==area_summary(zones,b,0).traffic_area_mean_aadt.iloc[0]


def test_standardization_monotonic_and_missing_preserved():
    x=pd.Series([100,200,1000,20000,200000,np.nan])
    out,params=normalize_traffic(x)
    assert out.traffic_z_log.mean()==pytest.approx(0,abs=1e-12)
    assert out.traffic_z_log.std(ddof=0)==pytest.approx(1)
    assert out.traffic_index_0_100.dropna().is_monotonic_increasing
    assert out.traffic_index_0_100.dropna().between(0,100).all()
    assert pd.isna(out.traffic_index_0_100.iloc[-1])
    edge,_=normalize_traffic(pd.Series([1000]),params)
    assert edge.traffic_index_0_100.iloc[0]==out.traffic_index_0_100.iloc[2]
