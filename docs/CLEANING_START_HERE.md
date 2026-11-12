# EmPath cleaning starting point

## What already exists

- Scope: full cached ZCTA footprints for 75025, 75024, 75023 and 75074.
- Starting graph: `output/four_zip_walking_network/walking_network_all_components.graphml`.
- Existing map: `output/four_zip_walking_network/walking_scope_map.html`.
- Municipal layers cleaned so far: `data/processed/75025_buffer250m/`; this does not cover the four-area scope.
- Current POI extraction omits places of worship. Add `amenity=place_of_worship` and inspect religion/name/access; do not assume every place of worship meets a user's temple requirement.
- Canopy screening map: neighborhood context only. Do not assign its block-group percentage as observed sidewalk shade.

## Agree on the graph before cleaning

Keep two separate representations:

1. **Routing network:** intersections/access points connected by mapped walkable segments. Keep feasible alternative paths and distinct parallel edges. Preserve source IDs and disconnected components for review. Do not assume mapped connections prove legal or safe access.
2. **Residential-to-service results:** a table with one row per origin–destination–scenario. Save the minimum-distance route for the baseline and minimum-friction route for the environmental scenario, both calculated on the underlying routing network. No residential-to-residential result edges are required.

Do not delete streets merely because they connect residential areas or are absent from baseline shortest paths. A longer route may have lower friction. Google Maps and OSM are different systems; use the existing OSM graph as the reproducible routing source. A Google Maps screenshot can support visual review but is not the graph source.

## First work session

### Nalini — normalize the required municipal layers

Run from the project folder:

```bash
.venv/bin/python scripts/clean_data.py --zipcodes 75025 75024 75023 75074
```

- This downloads missing raw snapshots; allow time for city API responses. Do not use `--refresh` unless a new snapshot is intended.
- Use EPSG:26914 for local distances/buffers; EPSG:4326 for web display.
- Review generated `quality_report.md` under the matching `data/processed/` scope folder.
- Keep source IDs, raw snapshots and quarantined records. Flag co-located features before merging; distinct features can share geometry.
- Municipal sidewalks are polygons. Use them to check the OSM graph, not directly as routable lines.
- Keep acquisition year, retrieval date and analysis scenario separate. Do not relabel 2021 canopy as current observations.

**Return:** four-area cleaned municipal layers, quality report, and unresolved gaps.

### Pramukh — review the existing network in parallel

```bash
.venv/bin/python scripts/audit_existing_network.py
```

- Read `output/cleaning_start/audit.json`, `network_coverage_by_zip.csv` and `edge_review.csv`.
- Review at least one origin/service route and a major crossing per ZIP, including suspicious component breaks.
- An isolated component can be a genuine disconnected path; do not bridge it automatically or silently discard it.
- Reciprocal directed edges and distinct parallel paths are not duplicate errors. Use `(u, v, key)` as the edge identifier.
- Check boundary-adjacent routes; retain surrounding context or expand the extraction if the boundary cuts a plausible route.

**Return:** flagged locations with evidence, recommended fixes, and unresolved access questions.

## Then connect origins and destinations

- Begin with a small verified residential sample across all four ZIPs, plus suitable temples, groceries and pharmacies.
- Keep original feature geometry separate from the routing entrance point. Parcel centroids and POI markers do not prove an entrance.
- Record original location, entrance/access point, snapped node/edge, connector distance and review status.
- Review long connectors and connectors crossing fences, divided roads, water or disconnected components. Nearest-node snapping alone is insufficient.
- Preserve missing/unreachable pairs with an explicit reason.

**Return:** `origins.gpkg`, `destinations.gpkg`, `access_connectors.gpkg` and a connection-review table.

## Establish the baseline before adding friction

- Route by the existing `length` attribute; save origin/destination IDs, scenario, route edge IDs, distance and reachability.
- If showing time, document a configurable assumed walking speed. This is estimated time, not measured travel time; include connector distance and disclose omitted crossing waits.
- Keep alternative network paths available for the later friction calculation.
- Add edge-level canopy only from a verified local raster with CRS, units, vintage and NoData checks. Confirm the raster is actually present before joining it.
- Leave weather, imperviousness and additional traffic features for the next pass if their cleaned inputs are not ready. Exclude crisis/EMS integrations from this initial cleaning task.

## Completion gate

- All four ZIPs represented; missing coverage explicitly reported.
- Geometry/ID/length checks passed or flagged; unresolved access questions retained.
- Verified sample origin/service connections and at least one reviewed baseline route per ZIP.
- Sources, assumptions and reproducible outputs saved. Call this a checked prototype baseline, not a fully validated sidewalk inventory.

## Technical reference

OSMnx supports shortest paths using a selected edge-weight attribute, with graph edges identified by `(u, v, key)`: https://osmnx.readthedocs.io/en/stable/user-reference.html and https://osmnx.readthedocs.io/en/stable/getting-started.html.
