# EmPath annotated resource guide

Reviewed November 8, 2026. These resources support a Python-only, public-data workflow. Availability does not mean a source has been downloaded, licensed for every intended use, or validated in Plano. Current processing status is documented below.

## Start with these five

1. **[Singapore behavioral study](https://www.nature.com/articles/s41598-022-06383-5) and [public data/code](https://osf.io/aj4vk/).** Actual route choices provide labels for learning a shade–distance tradeoff. The repository contains `behavioural_data.csv`, `analysis_final.ipynb`, instructions and experimental materials. The publication reports 408 sun-present choices from 46 participants. Useful for a conditional-logit baseline and model comparisons. It does not contain Plano observations or labels for traffic/crossing penalties. Repeated choices from one participant must remain grouped in evaluation. The cleaning pipeline downloads the CSV and README, retaining control and treatment records separately.

2. **[ASU Cool Routes implementation](https://news.asu.edu/20260610-environment-and-sustainability-new-cool-routes-app-maps-shadiest-routes-your-walk) and [research paper](https://doi.org/10.1016/j.buildenv.2026.114622).** A working example of heat-aware pedestrian routing based on mean radiant temperature. Study its separation of environmental modeling and routing, and its validation of modeled conditions. Do not equate surface temperature, radiant temperature, air temperature, and discomfort. Useful precedent; not a source of locally calibrated Plano preferences.

3. **[Los Angeles County Heat Action Plan viewer guide](https://assets-us-01.kc-usercontent.com/0234f496-d2b7-00b6-17a4-b43e949b70a2/7c1e1129-8bba-4a0b-b22f-d3c74aeedcfa/CHAP%20Data%20Viewer%20Brief.pdf).** A deployed decision-support example combining community indicators with site-level cooling infrastructure. Includes shade over sidewalks, shade at bus stops, cooling centers and pedestrian activity. Useful for dashboard layers and for separating community vulnerability from actual sidewalk conditions. Its 3 p.m. shade layers describe a particular scenario, not all-day conditions or observed pedestrian preferences.

4. **[CoolWalks research](https://pmc.ncbi.nlm.nih.gov/articles/PMC12038045/), [data](https://zenodo.org/records/11103149), and [code](https://github.com/henrik-wolf/CoolWalks).** Methods and reusable data for shade-aware network accessibility, including Manhattan, Barcelona and Valencia. Especially helpful for time-dependent shade and checking the difference between street-centerline proxies and detailed pedestrian networks. The implementation is Julia; EmPath can implement the relevant concepts in Python. Simulation outputs are not independent human-choice labels.

5. **[Plano's park shade map](https://www.plano.gov/ShadeMap) and [official announcement](https://content.civicplus.com/api/assets/tx-plano/97815d86-7b12-4111-848f-f2a51e854cf0).** A local implementation using the city's 2023 tree inventory and generalized building/tree models to explore shade by date and time. Useful for checking whether park shade patterns in EmPath are plausible and for identifying potential local data sources. The city describes it as beta; park coverage does not establish complete sidewalk coverage or downloadable citywide shade data.

## Local geography and pedestrian infrastructure

| Resource | Why it helps | Cleaning / interpretation |
|---|---|---|
| [Plano sidewalk surfaces](https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0) | Mapped physical footprint of sidewalks; useful for coverage checks and imagery validation | **Polygon geometry**, not ready-made graph edges. Preserve surfaces; never treat polygon perimeters as walking centerlines |
| [Plano trail centerlines](https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0) | Linear off-street walking connections and trail attributes | Check categories, permitted uses, materials and crossings; do not auto-connect spatially nearby features |
| [Plano parcels](https://maps.planogis.org/arcgiswad/rest/services/OpenData/Parcels/FeatureServer/1) | Detailed land units and stable parcel IDs for origin-resolution experiments | The inspected layer is geometry/IDs/subdivision names, not a PLUTO-like residential/building inventory; retain IDs as identifiers |
| [Plano address points](https://maps.planogis.org/arcgiswad/rest/services/OpenData/AddressPoints/FeatureServer/0) | Candidate address locations and checking correspondence to parcels | Co-located unit addresses can be legitimate. Point location does not establish a pedestrian entrance or residential use |
| [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | Blocks, block groups, tracts and ZCTAs for origin clusters and reporting | Match geography vintage to population tables; GEOIDs are strings, not numbers. Census blocks are not necessarily residential blocks |
| [2020 Census ZCTA service used by EmPath](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2) | Reproducible scope boundaries already cached for 75025, 75024, 75074 and comparison area 75023 | Service name includes ACS2024 but layer metadata identifies 2020 ZCTA boundaries. ZCTAs approximate postal ZIPs |
| [OSMnx](https://osmnx.readthedocs.io/en/stable/user-reference.html) | Python access to OSM walking networks, amenities, access tags and graph analysis | Validate walking access/crossings; do not silently drop disconnected components or duplicate municipal trails. Preserve OSM attribution and source snapshot |

## Heat, shade and roadway features

| Resource | Why it helps | Cleaning / interpretation |
|---|---|---|
| [Texas 2021 10 m canopy](https://zenodo.org/records/8200761) | Finer spatial canopy features along pedestrian corridors than existing block-group averages | Clip the required area; preserve NoData, valid-value definitions, pixel resolution and 2021 vintage. Does not directly measure time-specific shade |
| [American Forests Tree Equity Score downloads](https://www.treeequityscore.org/methodology?tab=data-download) | Existing EmPath screening layer and neighborhood context | Source canopy fractions range 0–1; current cached EmPath values were already converted to 0–100. Do not convert twice or assign block-group values as independent parcel observations |
| [Annual NLCD impervious surface](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-12-fractional-impervious) | Surrounding pavement and built-surface context | Valid fractions are 0–100%; handle special values using product metadata. 30 m pixels cannot distinguish individual sidewalk conditions. Avoid treating interpolated pixels as new observations |
| [NOAA GHCN-hourly](https://www.ncei.noaa.gov/products/global-historical-climatology-network-hourly) | Historical weather for scenarios and matching observation times | Preserve QC flags and measurement units; select stations by coverage as well as proximity. Keep UTC and derive America/Chicago local times for Plano. Do not substitute New York time because the developer is there |
| [Mapillary API](https://help.mapillary.com/hc/en-us/articles/360010234680-Accessing-imagery-and-data-through-the-Mapillary-API) | Public street-level imagery/detections to inspect obstacles and crossing environments | Audit local image dates, direction, visibility and coverage first. API access/token and usage conditions apply. A missing detection is not evidence that a feature is absent |
| [TxDOT traffic counts](https://www.txdot.gov/data-maps/traffic-count-maps.html) and [roadway inventory](https://www.txdot.gov/data-maps/roadway-inventory.html) | Roadway traffic context and attributes | Keep year, direction, frontage-road distinctions, units and match distance. Annual average daily traffic is not a pedestrian injury probability. Avoid nearest-road joins that jump across parallel roads |
| [TxGIO imagery](https://tnris.org/stratmap/orthoimagery) and [lidar](https://tnris.org/stratmap/elevation-lidar.html) | High-resolution canopy/building extraction and eventual shadow modeling | Record collection year, horizontal/vertical reference systems, units and point classifications. Bare-earth elevation alone omits trees and buildings needed for shade |

## AI training, network validation and accessibility comparisons

| Resource | Why it helps | Limitation |
|---|---|---|
| [APE annotated pedestrian imagery](https://sidewalks.washington.edu/2024/03/01/ape/) | Supervised labels for detecting sidewalks and crossings from imagery | No human comfort labels; validate geographic transfer and imagery reuse conditions |
| [PathwayBench](https://github.com/TaskarCenterAtUW/pathways-bench) | Benchmark focused on extracting **routable** pedestrian graphs | A high pixel-segmentation score is not enough; connectivity and downstream routes must also be evaluated |
| [Washington OS-CONNECT](https://osconnect-viewer.tdei.us/) and [OpenSidewalks](https://tcat.cs.washington.edu/opensidewalks/) | Deployed example of standardized sidewalk/crossing networks and accessibility-oriented data | Washington coverage, not Plano. Useful schemas and QA precedents, not a drop-in local network |
| [Project Sidewalk API](https://sidewalk-pittsburgh.cs.washington.edu/api) | Public accessibility observations and labels useful for understanding barriers | Geographic coverage and annotation quality vary; labels and underlying imagery have distinct reuse conditions |
| [EPA National Walkability Index / Smart Location Database](https://www.epa.gov/smartgrowth/smart-location-mapping) | External block-group context and a conventional walkability comparison | Not ground truth for heat comfort; check Census geography vintage before joining. Never use its own inputs as independent validation of an equivalent score |
| [Paris 15-minute-city framework](https://www.paris.fr/dossiers/paris-ville-du-quart-d-heure-ou-le-pari-de-la-proximite-37) | Organizing access to categories of everyday needs | A policy/accessibility framework, not a transferable dataset of walking-friction labels. Actual 15-minute walking access differs from 15 generalized cost units |

## Priority and current processing status

1. **Implemented first cleaning pass:** Plano sidewalk surfaces, trail lines, parcels, address points; Singapore route-choice CSV. Start with 75025 + 250 m context buffer. Raw API pages, metadata, source IDs, counts and checksums are preserved.
2. **Already available from earlier work:** ZCTA polygons and block-group canopy screening. These are context layers, not a finished pedestrian feature table.
3. **Next acquisitions:** Census blocks and matched population, OSM pedestrian graph and destinations, fine-grained canopy and impervious rasters, selected weather observations, and traffic context.
4. **Later if needed:** imagery ML, lidar shadow modeling, extra-city behavioral datasets. Do not download statewide multi-gigabyte rasters or train several models before deciding the needed features and labels.

## How to clean the remaining sources

**Raw → standardized → validated features → modeling table.** Keep each stage separate. Preserve source metadata and identify which rules changed records. Missing values stay missing unless a justified, documented imputation is applied.

1. Standardize CRS and units. The local vector-cleaning script uses EPSG:26914 (meters), while map display uses EPSG:4326. Native Plano service coordinates are State Plane feet; do not interpret raw service lengths as meters. Use an appropriate equal-area CRS for larger areal comparisons.
2. Inspect and repair invalid geometry conservatively. Quarantine unexpected types and failures; flag duplicate geometries without merging distinct parcel or unit-address records. Preserve full features at scope edges, using a context buffer to prevent boundary truncation.
3. Validate topology separately from geometry. Check disconnected components, dangling sidewalk ends, crossings, bridges, ramps and entrance connectors. Do not resolve all gaps by distance snapping. Sidewalk polygons require a separate, audited centerline/network extraction step or comparison against OSM.
4. Join raster features using corridor sampling or narrow buffers. Preserve valid-pixel coverage and NoData fractions. Record buffer width and run a sensitivity check. Canopy coverage is not the same as sun exposure.
5. Clean weather by station, timestamp, units and QC flag before joining to a scenario. Match conditions to route traversal assumptions. Never invent block-scale temperature differences from one station.
6. Clean destination points by category, entity identity and verified entrance. Nearby businesses are not duplicates simply because they share a shopping center. Keep uncertainty on entrances and opening hours.
7. Preserve participant IDs and treatment flags in behavioral data. Validate route-length components and choice labels. Hold out participants together; do not treat repeated decisions as independent people. The script produces a sun-present subset without claiming to reproduce all paper exclusions.
8. Make a feature table keyed by stable edge ID plus scenario/time. Keep exposure features, hard constraints, missing-data flags and learned outputs separate. Store source vintage and coverage. Do not generate a manual friction label and then describe a model trained on it as independent behavioral learning.

## Evidence the pipeline should produce

- Counts at every stage, including records repaired, quarantined or outside the exact scope.
- Missing attributes and duplicate/co-located geometries needing review.
- Raw checksums and immutable source snapshots.
- Valid geometry and positive metric lengths/areas where applicable.
- A separate future graph audit: component counts, questionable crossings and disconnected origins/destinations.
- A separate future feature audit: raster coverage, weather gaps, POI verification and year mismatch.

The first report is geometry/schema QA. Passing it does not establish routing validity, accurate time-specific shade, or local preference accuracy.
