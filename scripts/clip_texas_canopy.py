"""Clip Zenodo's 2021 Texas canopy raster; use --download on a cloud computer."""
import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.plot import plotting_extent
import requests

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://zenodo.org/records/8200761/files/TX_10m_canopy_cover_2021.zip?download=1'
MD5 = '79aec57e7339c8aa74e8a424b0000d32'
COUNTY = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query'


def download_source(folder):
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / 'TX_10m_canopy_cover_2021.zip'
    if not archive.exists():
        partial = archive.with_suffix('.zip.part')
        # Resume an interrupted download only when the server confirms the exact range.
        resume = partial.stat().st_size if partial.exists() else 0
        headers = {'Range': f'bytes={resume}-'} if resume else {}
        with requests.get(URL, headers=headers, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            if resume and response.status_code != 206:
                raise RuntimeError('Server did not confirm resume; retain partial file and retry with a new cache directory.')
            if resume and not response.headers.get('Content-Range', '').startswith(f'bytes {resume}-'):
                raise RuntimeError('Resume range mismatch; existing partial file was not modified.')
            with partial.open('ab' if resume else 'wb') as stream:
                total = resume
                last = resume
                for chunk in response.iter_content(8 * 1024 * 1024):
                    stream.write(chunk)
                    total += len(chunk)
                    if total - last >= 128 * 1024 * 1024:
                        print(f'Downloaded {total / 1e6:.0f} MB', flush=True)
                        last = total
        partial.replace(archive)
    digest = hashlib.md5()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != MD5:
        raise ValueError(f'Checksum mismatch: delete {archive} and retry')
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (folder / member.filename).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise ValueError('Unsafe archive member')
            if not target.exists() or target.stat().st_size != member.file_size:
                bundle.extract(member, folder)
    return folder / 'TX_10m_canopy_cover_2021.img'


def prepare_scope(boundaries, zipcodes, full_zctas, output):
    scope = gpd.read_file(boundaries).to_crs(4326)
    scope = scope[scope.ZCTA5.astype(str).isin(zipcodes)].copy()
    if set(scope.ZCTA5.astype(str)) != set(zipcodes):
        raise ValueError('Some requested ZCTAs are missing from the boundary file')
    if not full_zctas:
        response = requests.get(COUNTY, params={
            'where': "GEOID='48085'", 'outFields': 'GEOID,NAME',
            'returnGeometry': 'true', 'outSR': '4326', 'f': 'geojson',
        }, timeout=90)
        response.raise_for_status()
        payload = response.json()
        if len(payload.get('features', [])) != 1:
            raise ValueError(f'Could not retrieve Collin County: {payload}')
        (output / 'collin_county_source.geojson').write_text(json.dumps(payload))
        county = gpd.GeoDataFrame.from_features(payload['features'], crs=4326)
        scope.geometry = scope.geometry.intersection(county.geometry.iloc[0])
        if scope.geometry.is_empty.any():
            raise ValueError('A requested ZCTA has no area in Collin County')
    scope.to_file(output / 'clipping_boundaries.geojson', driver='GeoJSON')
    return scope


def clip_one(src, geometries, target, class_coded=False):
    # crop=True reads only the bounding window, not the statewide pixel array.
    data, transform = mask(src, geometries, crop=True, filled=False, indexes=1)
    scaled = data.astype('float32') * src.scales[0] + src.offsets[0]
    valid = scaled.compressed()
    if not valid.size:
        raise ValueError('No valid canopy pixels intersect this scope')
    if valid.min() < 0 or valid.max() > 100:
        raise ValueError('Values are outside 0–100: inspect source class key/NoData before mapping')
    if class_coded:
        from decode_canopy_classes import decode_classes
        scaled = decode_classes(scaled)
    profile = dict(driver='GTiff', height=data.shape[0], width=data.shape[1], count=1,
                   dtype='float32', crs=src.crs, transform=transform, nodata=-9999,
                   compress='deflate', tiled=True)
    with rasterio.open(target, 'w', **profile) as dst:
        dst.write(scaled.filled(-9999), 1)
        dst.update_tags(source=URL, vintage='2021', units='estimated percent from verified class midpoints' if class_coded else 'percent canopy cover',
                        boundary_rule='pixel center inside polygon; outside and source NoData masked')
    return scaled, transform


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boundaries', type=Path, default=ROOT / 'output/scope_screen/zcta_boundaries.geojson')
    p.add_argument('--zipcodes', nargs='+', default=['75025', '75024', '75074', '75023'])
    p.add_argument('--full-zctas', action='store_true', help='Keep portions outside Collin County too')
    p.add_argument('--source-raster', type=Path, help='Existing .img with companion .ige in same folder')
    p.add_argument('--download', action='store_true', help='Download statewide archive (~2.25 GB); intended for Colab')
    p.add_argument('--cache', type=Path, default=ROOT / 'data/raw/texas_canopy_2021')
    p.add_argument('--output', type=Path, default=ROOT / 'output/canopy_2021')
    args = p.parse_args()
    if not args.source_raster and not args.download:
        p.error('Provide --source-raster, or run with --download on Colab')
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.source_raster or download_source(args.cache)
    scope = prepare_scope(args.boundaries, args.zipcodes, args.full_zctas, args.output)
    with rasterio.open(source) as src:
        if src.crs is None or src.count != 1:
            raise ValueError('Expected a georeferenced, single-band canopy raster')
        projected = scope.to_crs(src.crs)
        image, transform = clip_one(src, projected.geometry.tolist(), args.output / 'canopy_scope_2021.tif', class_coded=True)
        for _, row in projected.iterrows():
            clip_one(src, [row.geometry], args.output / f'canopy_{row.ZCTA5}_2021.tif', class_coded=True)
        fig, ax = plt.subplots(figsize=(10, 9))
        plot = ax.imshow(image, extent=plotting_extent(image, transform), cmap='YlGn', vmin=0, vmax=100)
        projected.boundary.plot(ax=ax, color='#333333', linewidth=.8)
        for _, row in projected.iterrows():
            point = row.geometry.representative_point()
            ax.text(point.x, point.y, row.ZCTA5, fontsize=10, ha='center')
        fig.colorbar(plot, ax=ax, label='Canopy cover (%)', shrink=.7)
        ax.set_title('2021 canopy cover · 10 m Texas dataset\n' + ('Full ZCTAs' if args.full_zctas else 'ZCTAs within Collin County'))
        ax.set_axis_off()
        fig.text(.1, .02, 'Diamond, Sunde & Elliott · Zenodo 8200761\nCanopy cover is not time-specific pedestrian shade.', fontsize=9)
        fig.savefig(args.output / 'canopy_preview.png', dpi=180, bbox_inches='tight')
        plt.close(fig)
        metadata = dict(source=URL, archive_md5=MD5, vintage=2021,
                        processed_at_utc=datetime.now(timezone.utc).isoformat(),
                        zipcodes=args.zipcodes, collin_county_only=not args.full_zctas,
                        source_crs=str(src.crs), source_resolution=list(src.res),
                        source_nodata=src.nodata, source_scale=src.scales[0], source_offset=src.offsets[0],
                        boundary_source=str(args.boundaries), county_source=COUNTY if not args.full_zctas else None,
                        note='ZCTAs approximate postal ZIPs. Pixel-center mask; source NoData preserved. No resampling.')
        (args.output / 'source_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Clipped outputs: {args.output.resolve()}')


if __name__ == '__main__':
    main()
