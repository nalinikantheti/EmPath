# EmPath

A Python-only research project exploring pedestrian heat-protective infrastructure in Plano, Texas.

For the detailed implementation sequence, deliverables, validation gates and final submission checklist, see [the project roadmap](docs/PROJECT_ROADMAP.md).

**Current delivery scope:** organizer-approved Plano case study, due November 14, 2026, with a five-minute presentation. Follow [the one-week hackathon plan](docs/ONE_WEEK_HACKATHON_PLAN.md); the long roadmap is a future-work backlog. Prioritize social impact, data visualization and storytelling, with the prototype feature-complete by November 12 and rehearsed by November 13.

The current working milestone is a reproducible canopy screening and interactive map for ZCTAs 75025, 75024, 75074, and comparison area 75023. **It does not yet implement a trained edge-weight model or validated pedestrian routing.**

## Open in VS Code

Open `EmPath.code-workspace`. The project selects `.venv/bin/python` as its interpreter. Recommended extensions: Microsoft Python and Jupyter. Open `notebooks/01_pilot_scope.ipynb`, select the EmPath Python kernel/interpreter, and choose **Run All**.

If VS Code asks for a kernel, choose **Select Kernel → Select Another Kernel → Jupyter Kernel → Python (EmPath)**, or **Python Environments → .venv**. The project kernel is registered in your user Jupyter directory so VS Code can discover it. A default Python interpreter setting alone does not select a notebook kernel. To register it again after recreating/moving the environment:

```bash
.venv/bin/python -m ipykernel install --user --name empath --display-name "Python (EmPath)"
```

## Run from the terminal

```bash
.venv/bin/python scripts/visualize.py
.venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory output/scope_screen
```

Visit http://127.0.0.1:8765/empath_map.html. Hover over canopy polygons and toggle ZIP layers. The HTML can also be opened directly in a browser; linked downloads work best through the local server. Basemap tiles and mapping JavaScript require internet access. The existing data analysis runs from cached files without downloading sources again.

In VS Code, **Run and Debug → EmPath: build canopy maps** generates both maps. **Terminal → Run Task → EmPath: serve interactive map** starts the local viewer.

## Environment

On this computer, `.venv` was created from the existing Anaconda Python with `--system-site-packages`, reusing its installed GIS and notebook libraries. This is a lightweight local environment, not a fully isolated environment.

For an independent setup on another computer:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The requirements file uses compatible ranges, not an exact lockfile. The local verified package versions are recorded in `environment-verified.txt`.

## Data refresh

```bash
.venv/bin/python scripts/visualize.py --refresh
```

Refresh overwrites the downloaded source snapshot and derived maps. Source retrieval timestamps and limitations are retained in `output/scope_screen/source_metadata.json`. Retrieval date is not imagery acquisition date.

## Files

- `notebooks/01_pilot_scope.ipynb`: runnable notebook with statistics, map, and limitations.
- `scripts/screen_pilot_scope.py`: download/cache, canopy intersection analysis, and static map.
- `scripts/visualize.py`: interactive Folium map.
- `output/scope_screen/`: cached data, CSV, maps, and proposed pilot boundaries.
- `output/scope_screen/README.md`: screening methodology and interpretation.

## Interpretation

Canopy is an environmental indicator, not actual time-specific sidewalk shade. Block-group estimates are assigned uniformly to their intersections with ZIP boundaries; results are approximate and area weighted. No personal address is embedded in the map or notebook. The initial scope explorer uses public environmental and Census data.

## Resources and data cleaning

See [the annotated resource guide](docs/resources.md) for case studies, public datasets, their uses, and source-specific cleaning rules.

Run the first cleaning pass:

```bash
.venv/bin/python scripts/clean_data.py
```

This downloads immutable raw snapshots for Plano sidewalk **polygons**, trail centerlines, parcels and address points in 75025 plus a 250 m context buffer, as well as Singapore route-choice observations. It produces metric GeoPackages, behavioral CSVs, quarantine files and `data/processed/75025_buffer250m/quality_report.md`. Later runs verify checksums and reuse the cached snapshot. `--refresh` creates a new timestamped snapshot. Raw and processed data directories are excluded from Git; source code and provenance instructions remain versionable.

To extend the same pipeline:

```bash
.venv/bin/python scripts/clean_data.py --zipcodes 75025 75024 75074
```

The current pass checks geometry, source IDs and basic behavioral consistency. It does not yet validate crossings, extract sidewalk centerlines, classify residential parcels, or clean/join weather and raster data. Open `notebooks/02_data_cleaning.ipynb` to inspect results interactively.

## Next modeling milestone

### Clip the 2021 Texas canopy dataset without a statewide laptop download

Upload `notebooks/03_canopy_clip_colab.ipynb` to [Google Colab](https://colab.research.google.com/) and run its cells in order. It embeds the four existing ZCTA boundaries and clipping script. The statewide Zenodo download (~2.25 GB) happens in Colab; only the cropped GeoTIFFs, labeled PNG preview, boundaries and provenance are downloaded to your computer. Runtime disk space must accommodate the archive and extracted raster; allow at least 30 GB. Default scope: 75025, 75024, 75074 and comparison 75023, intersected with Collin County. Set `FULL_ZCTAS=True` in the notebook to include portions outside the county.

Extract the resulting small ZIP under `output/canopy_2021/`, then open `canopy_preview.png`. These are 2021 canopy percentages at the source 10 m resolution, not pedestrian shade estimates. The current block-group screening map remains a separate product. The statewide run requires Colab; it has not been executed locally. The notebook checks the archive checksum and valid pixel range before exporting.

If the statewide raster is already available locally, retain its companion `.ige` beside the `.img` and run:

```bash
.venv/bin/python scripts/clip_texas_canopy.py --source-raster /path/to/TX_10m_canopy_cover_2021.img
```

If this computer's Anaconda environment reports a PROJ database version mismatch, prefix the local command with `env -u PROJ_DATA -u GDAL_DATA` so Rasterio uses its bundled database. This is not needed in a clean Colab runtime.

Extract a connected OpenStreetMap walking network (default: a 1 km-wide box centered on the geocoded Brooklyn example):

For the actual four-ZCTA project scope, open `notebooks/05_walking_graph_scope.ipynb` using **Python (EmPath)**, or use **Terminal → Run Task → EmPath: extract walking graph**. Both run `scripts/build_scope_walking_graph.py` for the full saved footprints of **75025, 75024, 75074 and comparison 75023**, including portions outside Collin County. Results go to `output/four_zip_walking_network/`. Open `walking_scope_map.html` for colored ZIP boundaries, larger teal nodes and named POI markers with category toggles. A PNG preview is also saved. All mapped network components are displayed to preserve area coverage; `walking_network_connected.graphml` contains the largest connected component separately. No artificial connections are added. `summary.json` records node counts per ZCTA and component sizes. POIs are selected OSM parks, schools, libraries, healthcare, groceries and transit features; their markers are representative feature locations, not validated entrances. Repeated runs reuse exported graph and POI files. `--refresh` rebuilds them using OSMnx's HTTP cache where available.

The **Run and Debug** entry **EmPath: walking graph (all four ZIP areas)** runs this same scope. The separate **EmPath: extract walking graph (Brooklyn example)** entry still runs the original small example with the project interpreter.

```bash
.venv/bin/python scripts/extract_walking_graph.py
.venv/bin/python scripts/extract_walking_graph.py --address "Plano, Texas, USA" --dist 500 --output output/plano_walking_network
```

Use a specific public landmark/address to control the center; a city name uses the geocoder's representative point. Outputs include GraphML, a GeoPackage, node/edge CSVs, a PNG and a connectivity/provenance summary. The largest weakly connected component is used; all mapped components are also saved for audit. Load the graph with `ox.io.load_graphml("output/walking_network/walking_network.graphml")`. Nodes are simplified junctions/dead ends and edges are walkable mapped segments with lengths in meters. Reciprocal directed edges are not separate physical paths. Buildings require separate extraction and validated entrance connections. This is a baseline OSM network, not a validated sidewalk/crossing network; compare it with the Plano GIS layers before routing.

Build and audit the pedestrian graph, join edge-level environmental features, define the training target, and calibrate nonnegative edge costs against appropriate observations. Keep training, routing, and the map interface separate so their assumptions remain inspectable.
