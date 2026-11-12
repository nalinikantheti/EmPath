# Environmental cleaning outputs for EmPath

## Work backward from routing

The final routing graph needs one stable record per directed edge `(u, v, key)`, containing its geometry, original length, environmental attributes and coverage flags. Keep the full feasible network. Friction costs and route ranking are a later modeling step, not raster conversion.

| Output | Contents | Purpose |
|---|---|---|
| Clean rasters | Canopy and temperature in original grids, units and dates; invalid pixels masked | Reproducible environmental inputs |
| Optional classified polygons | Canopy/temperature display classes with documented thresholds | Inspect raster-to-vector conversion; not AI inference |
| Census-block environmental layer | Original block GEOID, clipped geometry, separate environmental means and coverage indicators | Dashboard of neighborhood differences |
| Walking-edge environmental layer | Stable edge IDs, geometry, environmental summaries in a specified corridor | Input to edge-cost calculation |
| Origins, services and connectors | Verified categories, entrances, graph links and unresolved access flags | Connect homes to the walking graph; handled by the network workflow |
| Provenance/quality report | CRS, resolution, dates, source, excluded pixels, coverage and skipped inputs | Explain what is known and missing |

## Three maps to inspect

1. **Network and access map:** ZIP outlines + walking segments + homes/services + reviewed connectors. Highlight disconnected origins and uncertain crossings. The existing walking map is a starting point; entrances are not yet validated.
2. **Block environmental map:** census-block outlines colored separately by canopy and temperature, with missing coverage visible. Do not merge unlike units into one unexplained score.
3. **Edge environmental map:** walking edges colored by canopy or temperature, plus source coverage flags. This is the immediate precursor to the friction map.

Not every map needs every layer at once. Census blocks summarize neighborhood patterns; edge features describe specific routes. Block averages are not a replacement for finer edge sampling.

## Run in VS Code

1. Open `notebooks/06_environment_rasters_and_overlays.ipynb` with **Python (EmPath)**.
2. Edit `config/environment_pipeline.json`: set actual raster and census-block paths; verify units, date and source. Temperature input must already have product-specific cloud/quality masks applied; the generic cleaner cannot infer those quality bits.
3. Run the notebook. Missing inputs are skipped explicitly. Output: `output/environment_features/`.
4. Optional: open `notebooks/07_geoai_tree_extraction.ipynb` for pretrained tree extraction. Use a separate GPU/Colab environment if practical; dependency installation and model downloads are opt-in.

Terminal alternative:

```bash
env -u PROJ_DATA -u GDAL_DATA .venv/bin/python scripts/environment_pipeline.py
```

This machine inherits incompatible Anaconda PROJ/GDAL paths. Unsetting them for this command lets Rasterio use its bundled databases; it does not alter global settings. The notebook clears those inherited variables within its own kernel before imports. In a clean environment this workaround is usually unnecessary.

## GeoAI libraries and APIs

- **SamGeo / segment-geospatial:** pretrained text-prompt imagery segmentation. Notebook 07 uses LangSAM (GroundingDINO + SAM) on a small RGB GeoTIFF. GPU recommended; default checkpoints download on first use. Not validated here. https://samgeo.gishub.org/examples/text_prompts/
- **GeoAI Python package:** model discovery, geospatial segmentation and adaptation workflows. Useful for a broader model comparison, not an extra dependency required by notebook 06. https://opengeoai.org/examples/foundation_models/
- **TorchGeo:** geospatial datasets and pretrained model backbones; useful when moving beyond a small pretrained inference demo. https://docs.torchgeo.org/en/stable/api/models.html
- **Rasterio + GeoPandas:** raster cleaning, polygon extraction and vector joins. These are GIS operations, not learned inference. https://rasterio.readthedocs.io/en/stable/topics/features.html
- **exactextract:** partial-pixel polygon summaries when pixel-center approximations are inadequate. Optional future replacement for the current zonal summarizer. https://isciences.github.io/exactextract/
- **Census TIGER/Line:** actual census-block geometries and GEOIDs. Blocks differ from the block-group canopy layer already in the project. https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2020.html
- **USGS Landsat surface temperature:** a potential temperature input; observe product quality flags and scale/offset before interpreting values. It measures surface temperature, not sidewalk air temperature. https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature

## Current limits

No real canopy/temperature raster or census-block file was supplied to the config at implementation time. Both notebooks were executed with missing-input handling; synthetic numerical tests check the GIS code. Pretrained inference was not run because SamGeo and real RGB imagery are absent. The initial edge export is a labeled 200-edge sample; increase the configured limit after checking it. No cleaned output is a validated friction score or certified walking route.
