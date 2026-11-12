"""Optional pretrained GroundingDINO + SAM tree extraction on a small RGB GeoTIFF.
Install optional dependencies separately. Model download/inference is explicit.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import numpy as np
import rasterio
from PIL import Image


def predict_trees(source, output, prompt='tree', box_threshold=.24, text_threshold=.24):
    source, output = Path(source), Path(output)
    with rasterio.open(source) as src:
        if src.crs is None or src.count < 3 or any(t != 'uint8' for t in src.dtypes[:3]):
            raise ValueError('Provide georeferenced uint8 RGB aerial imagery with RGB in bands 1–3, not an indexed canopy/temperature map.')
        if max(src.width, src.height) > 1536:
            raise ValueError('Clip a tile at most 1536 pixels per side first. No automatic downsampling.')
        rgb = src.read([1, 2, 3])
        valid = (src.read_masks([1, 2, 3]) > 0).all(axis=0)
        profile = dict(driver='GTiff', height=src.height, width=src.width, count=1,
                       dtype='uint8', crs=src.crs, transform=src.transform, nodata=255, compress='deflate')
    # Import here so the GIS notebook does not require ML dependencies.
    from samgeo.text_sam import LangSAM
    model = LangSAM()
    model.predict(Image.fromarray(np.moveaxis(rgb, 0, -1)), prompt,
                  box_threshold=box_threshold, text_threshold=text_threshold)
    masks = model.masks
    if masks is None:
        raise RuntimeError('Model returned no mask array. Inspect model logs/version before exporting.')
    if hasattr(masks, 'detach'):
        masks = masks.detach().cpu().numpy()
    masks = np.asarray(masks)
    if masks.size:
        if masks.ndim == 4 and masks.shape[1] == 1:
            masks = masks[:, 0]
        if masks.ndim != 3 or tuple(masks.shape[1:]) != tuple(valid.shape):
            raise ValueError(f'Unexpected mask dimensions: {masks.shape}')
        result = (masks > 0).any(axis=0).astype('uint8')
    else:
        result = np.zeros(valid.shape, dtype='uint8')
    result[~valid] = 255
    output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output, 'w', **profile) as dst:
        dst.write(result, 1)
        dst.update_tags(units='binary tree prediction', model='SamGeo LangSAM: GroundingDINO + SAM',
                        note='0 not detected; 1 detected tree; 255 source NoData; not calibrated canopy truth or shade')
    metadata = {'created_utc': datetime.now(timezone.utc).isoformat(), 'source': str(source),
        'output': str(output), 'model': 'LangSAM default pretrained models',
        'package_version': importlib.metadata.version('segment-geospatial'),
        'prompt': prompt, 'box_threshold': box_threshold, 'text_threshold': text_threshold,
        'source_vintage': 'Record imagery acquisition date separately before feature joining.',
        'validation': 'Not validated for Plano. Review false positives and missed trees on independent image patches.',
        'model_weights': 'Default weights resolved by installed SamGeo; record downloaded checkpoint names/checksums for reproducibility.',
        'reference': 'https://samgeo.gishub.org/examples/text_prompts/'}
    output.with_suffix('.json').write_text(json.dumps(metadata, indent=2))
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('output')
    parser.add_argument('--prompt', default='tree')
    args = parser.parse_args()
    print(predict_trees(args.source, args.output, args.prompt))
