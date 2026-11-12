"""Validate timezone filtering/QC and traffic context matching."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Point,LineString
from clean_noaa_summer import summarize
from package_clean_deliverables import attach_traffic


def test_local_summer_hours_qc_and_hourly_weighting():
    # In summer Chicago is UTC-5. 17Z is noon; 23Z is 18:00 and excluded.
    frame=pd.DataFrame({'DATE':['2025-06-01T16:59:00','2025-06-01T17:00:00','2025-06-01T17:30:00',
                                '2025-06-01T18:00:00','2025-06-01T23:00:00'],
                        'temperature':['99','30','34','50','99']})
    for col in ['dew_point_temperature','wind_speed','relative_humidity']:frame[col]='10'
    for col in ['temperature','dew_point_temperature','wind_speed','relative_humidity']:frame[col+'_Quality_Code']='1'
    frame.loc[3,'temperature_Quality_Code']='s'
    selected,hourly,report=summarize(frame)
    assert len(selected)==3
    assert report['hourly_statistics']['temperature']['median']==32
    assert report['hourly_statistics']['temperature']['valid_hours']==1
    assert report['masked_values']['temperature']==1


def test_nearest_traffic_unknown_not_zero():
    zones=gpd.GeoDataFrame({'id':[1,2]},geometry=[Point(700000,3670000),Point(710000,3670000)],crs=26914)
    roads=gpd.GeoDataFrame({'source_feature_id':['r1'],'aadt':[12000]},
                          geometry=[LineString([(700010,3669990),(700010,3670010)])],crs=26914)
    out=attach_traffic(zones,roads)
    assert out.loc[0,'traffic_distance_m']==pytest.approx(10)
    assert out.loc[0,'nearest_mapped_road_aadt']==12000
    assert pd.isna(out.loc[1,'nearest_mapped_road_aadt'])
    assert not out.loc[1,'traffic_context_matched']
