"""Verify clipping semantics without downloading the statewide dataset."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from clip_texas_canopy import clip_one


class CanopyClipTests(unittest.TestCase):
    def test_zero_nodata_polygon_mask_and_grid(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            pixels = np.arange(16, dtype='uint8').reshape(4, 4)
            pixels[1, 1] = 255
            with rasterio.open(folder / 'source.tif', 'w', driver='GTiff',
                               width=4, height=4, count=1, dtype='uint8',
                               crs='EPSG:26914', transform=from_origin(0, 40, 10, 10),
                               nodata=255) as dst:
                dst.write(pixels, 1)
            with rasterio.open(folder / 'source.tif') as src:
                image, _ = clip_one(src, [Polygon([(0, 40), (40, 40), (0, 0)])],
                                    folder / 'clip.tif')
            with rasterio.open(folder / 'clip.tif') as dst:
                result = dst.read(1, masked=True)
                self.assertEqual(result[0, 0], 0)
                self.assertFalse(result.mask[0, 0])
                self.assertTrue(result.mask[1, 1])
                self.assertTrue(result.mask[3, 3])
                self.assertEqual(dst.res, (10, 10))
                self.assertEqual(dst.crs.to_epsg(), 26914)
                np.testing.assert_array_equal(result.compressed(), image.compressed())


if __name__ == '__main__':
    unittest.main()
