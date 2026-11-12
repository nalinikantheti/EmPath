import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import geopandas as gpd
from shapely.geometry import Polygon
from block_locations import add_location_fields


def test_representative_point_and_coordinate_links():
    # Concave polygon: centroid can be unsuitable, representative point stays inside.
    polygon=Polygon([(700000,3670000),(700100,3670000),(700100,3670020),(700020,3670020),(700020,3670100),(700000,3670100)])
    b=gpd.GeoDataFrame({'GEOID20':['480850001001001']},geometry=[polygon],crs=26914)
    result=add_location_fields(b)
    point=gpd.GeoSeries(gpd.points_from_xy(result.block_longitude,result.block_latitude),crs=4326).to_crs(26914).iloc[0]
    assert polygon.covers(point)
    assert 'query=' in result.block_google_maps_url.iloc[0]
    assert 'map_action=pano' in result.block_street_view_url.iloc[0]
    assert 'not a verified street address' in result.block_location_note.iloc[0]
