"""Synthetic numerical checks; fixtures are not Plano observations."""
import importlib.util
from pathlib import Path
import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

spec = importlib.util.spec_from_file_location('ep', Path(__file__).parents[1]/'scripts/environment_pipeline.py')
ep = importlib.util.module_from_spec(spec);spec.loader.exec_module(ep)


def fixture_raster(tmp_path):
    path = tmp_path/'source.tif'
    with rasterio.open(path,'w',driver='GTiff',height=2,width=2,count=1,dtype='int16',
                       crs='EPSG:26914',transform=from_origin(700000,3670000,10,10),nodata=-9999) as dst:
        dst.write(np.array([[10,20],[30,-9999]],dtype='int16'),1)
        dst.scales=(2.,)
    scope = gpd.GeoDataFrame({'ZCTA5':['75025']},geometry=[box(700000,3669980,700020,3670000)],crs=26914)
    return path, scope


def test_scale_nodata_zonal_and_polygonization(tmp_path):
    path, scope = fixture_raster(tmp_path)
    config={'name':'canopy','path':str(path),'units':'percent','source':'synthetic test only',
            'vintage':'test','valid_min':0,'valid_max':100}
    target, info = ep.clean_raster(config,scope,tmp_path)
    assert info['valid_pixels']==3
    with rasterio.open(target) as src:
        data=src.read(1,masked=True)
        assert np.allclose(data.compressed(),[20,40,60])
        assert data.mask[1,1]
        assert src.scales==(1.,)  # Applied once, not again during joins.
    stats=ep.zonal_summary(scope,target,'canopy').iloc[0]
    assert stats.canopy_mean==40
    assert stats.canopy_valid_center_fraction==.75
    assert stats.canopy_raster_overlap_fraction==1
    ep.polygonize_classes(target,[30,50],tmp_path/'classes.gpkg')
    polygons=gpd.read_file(tmp_path/'classes.gpkg')
    assert polygons.area.sum()==pytest.approx(300)
    assert set(polygons.class_id)=={0,1,2}


def test_outside_raster_stays_missing(tmp_path):
    path, scope=fixture_raster(tmp_path)
    scope.geometry=[box(710000,3670000,710010,3670010)]
    stats=ep.zonal_summary(scope,path,'temp').iloc[0]
    assert np.isnan(stats.temp_mean)
    assert stats.temp_valid_pixels==0
    assert stats.temp_raster_overlap_fraction==0


def test_range_exclusion_and_missing_units(tmp_path):
    path,scope=fixture_raster(tmp_path)
    cfg={'name':'canopy','path':str(path),'units':'percent','source':'test','vintage':'test','valid_max':50}
    _,info=ep.clean_raster(cfg,scope,tmp_path)
    assert info['valid_pixels']==2
    cfg['units']=None
    with pytest.raises(ValueError,match='units'):
        ep.clean_raster(cfg,scope,tmp_path)


def test_full_pipeline_block_overlay(tmp_path):
    path,scope=fixture_raster(tmp_path)
    scope=gpd.GeoDataFrame({'ZCTA5':['75025','75024','75023','75074']},geometry=[
        box(700000,3669990,700010,3670000),box(700010,3669990,700020,3670000),
        box(700000,3669980,700010,3669990),box(700010,3669980,700020,3669990)],crs=26914)
    scopefile=tmp_path/'scope.geojson';scope.to_file(scopefile,driver='GeoJSON')
    blocks=gpd.GeoDataFrame({'GEOID20':['480850001001001']},geometry=[box(700000,3669980,700020,3670000)],crs=26914)
    blockfile=tmp_path/'blocks.gpkg';blocks.to_file(blockfile,driver='GPKG')
    out=tmp_path/'out'
    report=ep.run({'scope':str(scopefile),'blocks':str(blockfile),'block_id':'GEOID20',
                   'output':str(out),'edge_sample_limit':0,'rasters':[{
                   'name':'canopy','path':str(path),'units':'percent','source':'synthetic test only',
                   'vintage':'test','valid_min':0,'valid_max':100}]})
    result=gpd.read_file(out/'block_environment.gpkg')
    assert result.iloc[0].canopy_mean==40
    assert len(report['block_coverage_by_zip'])==4
    assert all(r['block_area_coverage']==pytest.approx(1) for r in report['block_coverage_by_zip'])
