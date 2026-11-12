"""Clean environmental rasters and summarize them over block/edge polygons.
No inference or invented friction weights: ML extraction is a separate script.
Paths in the JSON config are relative to the project root.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask, shapes
from rasterio.mask import mask
from shapely.geometry import shape, Polygon
from shapely import union_all, normalize

ROOT = Path(__file__).resolve().parents[1]
ZIPCODES = {'75025', '75024', '75023', '75074'}
METRIC = 26914


def resolve(value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else ROOT / p


def read_scope(config):
    scope = gpd.read_file(resolve(config['scope']))
    if scope.crs is None:
        raise ValueError('Scope CRS is missing; do not guess a CRS.')
    if 'ZCTA5' not in scope or set(scope.ZCTA5.astype(str)) != ZIPCODES:
        raise ValueError('Scope must contain all four confirmed ZCTAs.')
    if scope.geometry.isna().any() or (~scope.geometry.is_valid).any():
        raise ValueError('Repair/review scope geometry first.')
    return scope


def inventory(config):
    rows = []
    entries = [('census_blocks', config.get('blocks'))] + [(r['name'], r.get('path')) for r in config['rasters']]
    for name, path in entries:
        rows.append({'input': name, 'path': path, 'status': 'ready' if path and resolve(path).exists() else 'missing'})
    return pd.DataFrame(rows)


def clean_raster(spec, scope, output):
    """Clip in source CRS/resolution; apply source scale/offset, preserve NoData."""
    if not spec.get('units') or not spec.get('source') or not spec.get('vintage'):
        raise ValueError('Set units, source and vintage before processing.')
    srcpath = resolve(spec['path'])
    with rasterio.open(srcpath) as src:
        if src.crs is None:
            raise ValueError('Raster CRS missing.')
        band = spec.get('band', 1)
        if not 1 <= band <= src.count:
            raise ValueError('Requested raster band is absent.')
        if src.transform.b or src.transform.d:
            raise ValueError('Rotated raster: warp to a north-up grid explicitly first.')
        geo = scope.to_crs(src.crs).geometry
        data, transform = mask(src, geo, indexes=band, crop=True, filled=False)
        scale = spec.get('scale') if spec.get('scale') is not None else src.scales[band-1]
        offset = spec.get('offset') if spec.get('offset') is not None else src.offsets[band-1]
        if not np.isfinite([scale, offset]).all() or scale == 0:
            raise ValueError('Invalid scale/offset.')
        data = data.astype('float32') * scale + offset
        arr = np.asarray(data.data, dtype='float32')
        invalid = np.ma.getmaskarray(data) | ~np.isfinite(arr)
        if spec.get('valid_min') is not None:
            invalid |= arr < spec['valid_min']
        if spec.get('valid_max') is not None:
            invalid |= arr > spec['valid_max']
        valid = arr[~invalid]
        if not valid.size:
            raise ValueError('No valid pixels after clip and range checks.')
        target = output / f"{spec['name']}_clean.tif"
        profile = dict(driver='GTiff', height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype='float32', crs=src.crs, transform=transform, nodata=-9999.0,
                       compress='deflate')
        arr[invalid] = -9999.0
        with rasterio.open(target, 'w', **profile) as dst:
            dst.write(arr, 1)
            dst.update_tags(units=spec['units'], source=spec['source'], vintage=spec['vintage'],
                            method='clip; source scale/offset; mask invalid/out-of-range; no resampling')
        report = {'source_path': str(srcpath), 'output_path': str(target),
                  'crs': str(src.crs), 'resolution': list(src.res), 'units': spec['units'],
                  'vintage': spec['vintage'], 'source': spec['source'], 'valid_pixels': int(valid.size),
                  'masked_pixels_in_clipped_rectangle': int(invalid.sum()),
                  'min': float(valid.min()), 'max': float(valid.max()),
                  'applied_scale': scale, 'applied_offset': offset}
    return target, report


def polygonize_classes(path, bins, target, max_pixels=5_000_000):
    """Polygonize explicit display classes, never individual continuous values."""
    if not bins or list(bins) != sorted(set(bins)) or not np.isfinite(bins).all():
        raise ValueError('Provide increasing, unique, finite class thresholds.')
    with rasterio.open(path) as src:
        if src.width * src.height > max_pixels:
            raise ValueError('Polygon conversion too large: clip smaller or omit polygonize.')
        data = src.read(1, masked=True)
        classes = np.digitize(data.data, bins).astype('int16')
        records = [{'class_id': int(value), 'geometry': shape(geom)}
                   for geom, value in shapes(classes, mask=~np.ma.getmaskarray(data), transform=src.transform)]
        if not records:
            raise ValueError('No polygons extracted.')
        gdf = gpd.GeoDataFrame(records, crs=src.crs)
    gdf['class_label'] = gdf.class_id.map(lambda i: (f'< {bins[0]}' if i == 0 else
        f'>= {bins[-1]}' if i == len(bins) else f'{bins[i-1]} to < {bins[i]}'))
    gdf.to_file(target, driver='GPKG', index=False)
    return len(gdf)


def zonal_summary(zones, raster_path, prefix):
    """Pixel-center means; report overlap and valid-center coverage separately.
Not exact area-weighted extraction. Tiny zones may contain no pixel centers.
"""
    if zones.crs is None or zones.geometry.isna().any() or (~zones.geometry.is_valid).any():
        raise ValueError('Zones need a known CRS and valid, nonmissing geometries.')
    rows = []
    with rasterio.open(raster_path) as src:
        local = zones.to_crs(src.crs)
        footprint = Polygon([src.transform * p for p in [(0,0), (src.width,0),
                            (src.width,src.height), (0,src.height)]])
        metric_footprint = gpd.GeoSeries([footprint], crs=src.crs).to_crs(METRIC).iloc[0]
        metric_zones = zones.to_crs(METRIC)
        for geom, metric_geom in zip(local.geometry, metric_zones.geometry):
            total_area = metric_geom.area
            if geom.is_empty or not total_area:
                raise ValueError('Empty/zero-area zone.')
            overlap = metric_geom.intersection(metric_footprint).area / total_area
            rec = {f'{prefix}_mean': np.nan, f'{prefix}_min': np.nan, f'{prefix}_max': np.nan,
                   f'{prefix}_valid_pixels': 0, f'{prefix}_zone_centers_in_raster': 0,
                   f'{prefix}_valid_center_fraction': np.nan,
                   f'{prefix}_raster_overlap_fraction': min(1., max(0., overlap))}
            if geom.intersects(footprint):
                try:
                    data, trans = mask(src, [geom], indexes=1, crop=True, filled=False)
                except ValueError:
                    rows.append(rec);continue
                inside = geometry_mask([geom], out_shape=data.shape, transform=trans, invert=True)
                valid = inside & ~np.ma.getmaskarray(data) & np.isfinite(data.data)
                vals = data.data[valid]
                count = int(inside.sum())
                rec[f'{prefix}_valid_pixels'] = int(vals.size)
                rec[f'{prefix}_zone_centers_in_raster'] = count
                rec[f'{prefix}_valid_center_fraction'] = float(vals.size/count) if count else np.nan
                if vals.size:
                    for stat, value in [('mean', vals.mean()), ('min', vals.min()), ('max', vals.max())]:
                        rec[f'{prefix}_{stat}'] = float(value)
            rows.append(rec)
    return pd.DataFrame(rows, index=zones.index)


def prepare_blocks(config, scope):
    blocks = gpd.read_file(resolve(config['blocks']))
    col = config['block_id']
    if blocks.crs is None or col not in blocks:
        raise ValueError('Blocks require a known CRS and configured ID column.')
    ids = blocks[col].astype('string')
    if ids.isna().any() or not ids.str.fullmatch(r'\d{15}', na=False).all() or ids.duplicated().any():
        raise ValueError('Expected unique 15-digit census block GEOIDs, not block-group IDs.')
    blocks[col] = ids
    if blocks.geometry.isna().any() or (~blocks.geometry.is_valid).any():
        raise ValueError('Review/repair invalid block geometries before overlay.')
    blocks = blocks.to_crs(METRIC)
    original_area = blocks.area
    union = scope.to_crs(METRIC).geometry.union_all()
    blocks['scope_area_fraction'] = blocks.geometry.intersection(union).area / original_area
    blocks = blocks.loc[blocks.scope_area_fraction > 0].copy()
    blocks.geometry = blocks.geometry.intersection(union)
    blocks.geometry = blocks.geometry.map(lambda g: union_all([p for p in g.geoms if p.geom_type in ['Polygon','MultiPolygon']]) if g.geom_type == 'GeometryCollection' else g)
    if blocks.empty:
        raise ValueError('No census blocks overlap the four ZIPs.')
    return blocks.reset_index(drop=True)


def run(config):
    out = resolve(config['output']);out.mkdir(parents=True, exist_ok=True)
    scope = read_scope(config)
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'inventory': inventory(config).to_dict('records'), 'rasters': {}, 'warnings': [],
              'ai_inference_performed': False}
    cleaned = {}
    for spec in config['rasters']:
        name = spec['name']
        if not re.fullmatch(r'[a-z][a-z0-9_]*', name) or name in cleaned:
            raise ValueError('Raster names must be unique lowercase identifiers.')
        if not spec.get('path') or not resolve(spec['path']).exists():
            report['warnings'].append(f'{name}: missing input; skipped, no synthetic substitute.');continue
        try:
            path, info = clean_raster(spec, scope, out)
            cleaned[name] = path;report['rasters'][name] = info
            if spec.get('polygonize'):
                info['polygons'] = polygonize_classes(path, spec.get('bins'), out / f'{name}_classes.gpkg')
        except ValueError as exc:
            report['warnings'].append(f'{name}: {exc}')
    if config.get('blocks') and resolve(config['blocks']).exists():
        blocks = prepare_blocks(config, scope)
        union = blocks.geometry.union_all()
        coverage = []
        for _, row in scope.to_crs(METRIC).iterrows():
            coverage.append({'zcta': str(row.ZCTA5), 'block_area_coverage': union.intersection(row.geometry).area/row.geometry.area})
        report['block_coverage_by_zip'] = coverage
        for name, path in cleaned.items():
            blocks = blocks.join(zonal_summary(blocks, path, name))
        blocks.to_file(out / 'block_environment.gpkg', driver='GPKG', index=False)
        blocks.drop(columns='geometry').to_csv(out / 'block_environment.csv', index=False)
    else:
        report['warnings'].append('Census blocks missing: block-group screening layer is not a substitute.')
    if cleaned and config.get('edges') and config.get('edge_sample_limit', 0):
        edges = gpd.read_file(resolve(config['edges']), layer=config.get('edge_layer')).to_crs(METRIC)
        if not {'u', 'v', 'key'}.issubset(edges.columns) or edges.duplicated(['u','v','key']).any():
            raise ValueError('Edges need unique (u,v,key) IDs.')
        total = len(edges)
        limit = config['edge_sample_limit']
        if limit < 0 or config['edge_buffer_m'] <= 0:
            raise ValueError('Positive buffer and nonnegative edge limit required.')
        # Evenly distributed deterministic subset for a fast first run, not a full graph join.
        edges = edges.iloc[np.linspace(0, total-1, min(limit, total), dtype=int)].reset_index(drop=True)
        corridors = edges[['geometry']].copy();corridors.geometry = edges.buffer(config['edge_buffer_m'])
        # Reciprocal directed edges often have identical physical corridors.
        # Score each normalized corridor once, then restore all (u,v,key) records.
        corridor_keys = corridors.geometry.map(lambda g: normalize(g).wkb_hex)
        keep = ~corridor_keys.duplicated()
        unique_corridors = corridors.loc[keep].reset_index(drop=True)
        for name, path in cleaned.items():
            summary = zonal_summary(unique_corridors, path, name)
            summary.index = corridor_keys[keep].to_numpy()
            restored = summary.reindex(corridor_keys.to_numpy()).reset_index(drop=True)
            edges = edges.join(restored)
        edges.to_file(out / 'edge_environment_sample.gpkg', driver='GPKG', index=False)
        edges.drop(columns='geometry').to_csv(out / 'edge_environment_sample.csv', index=False)
        report['edge_sample'] = {'processed': len(edges), 'total': total, 'buffer_m': config['edge_buffer_m']}
    report['notes'] = ['Native raster grids retained; source resolution not improved.',
        'Zonal statistics use pixel centers, not exact area-weighted extraction.',
        'Continuous layers joined as separate columns, not averaged into invented friction.',
        'Canopy != time-specific shade; surface temperature != air temperature.',
        'Polygonization and overlay are GIS; run the separate inference notebook for GeoAI.']
    (out / 'run_report.json').write_text(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config/environment_pipeline.json')
    args = parser.parse_args()
    print(json.dumps(run(json.loads(resolve(args.config).read_text())), indent=2))
