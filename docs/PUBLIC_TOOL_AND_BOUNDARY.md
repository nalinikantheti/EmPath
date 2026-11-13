# EmPath public explorer and boundary correction

## Public experience
- Home: `https://empathmaps.netlify.app/` — the illustrative temple-walk story, why everyday access matters, then one clear invitation to explore.
- Explorer: `/app.html` — choose places, compare walking effort across Plano, inspect an area or look up an address, then view actual routes. There is no walking-budget cutoff.
- Guide: `/guide.html` — household/homebuyer, city-planner and housing-organization workflows; plain-language effort explanation.
- Optional context: `/context.html`; optional technical interface: `/research.html`.
- Methods, checks, static gallery and the earlier research archive remain available through “Behind the map.”

## What is corrected
Production acquisition now extends three kilometers beyond the official Plano boundary. Roads/paths, destinations, real GeoAI tree predictions, traffic context, summer Landsat summaries and finite edge costs were expanded together. Origin areas remain the same 4,402 city-clipped Census blocks.

Current support: 98,193 nodes; 290,552 directed weighted edges; zero unknown weights. Tree inference covers 1,524 tiles (823 compatible cached class tiles and 701 new predictions). The expanded catalog contains 1,648 candidate records across 25 categories. Access/entrances and catalog completeness remain unverified.

## How route-specific coverage checks work
1. Every edge cost is at least `length_m / 1.2` seconds, because the environmental multiplier is >=1.
2. Reaching any candidate or detour outside the analysis geometry requires first reaching its boundary.
3. For the actual snapped origin, compute `exit_lower_bound_minutes = 0.99 × projected distance to outer boundary / 1.2 / 60`. The factor 0.99 is conservative relative to every source edge's length-to-projected-geometry ratio (minimum observed approximately 0.99766).
4. The minimum exit bound across housing-positive origins passing the <=100 m connection-distance filter is approximately 40.6 minutes.
5. A known route cost below its origin's exit bound cannot be improved by an outside destination or outside detour under this model. The public map displays longer routes as well, with a coverage note when a selected trip reaches or exceeds that bound.

This certifies the sufficiency of the search extent for individual routes below their origin's bound. It does not prove real-world path/POI completeness, entrance legality, continuous sidewalks, personal comfort or safety. Longer comparisons in both public and advanced maps remain qualified individually.

## Public interpretation
- Effort minutes combine modeled walking time and an assumed environmental allowance; they are not actual elapsed time or predicted fatigue. Ordinary walking minutes are shown separately.
- Heat context is a summer 2025 surface-temperature composite, not current weather or pedestrian air temperature.
- Blue/red compares average effort across all areas with complete route data for the selected categories, not safety. Gray indicates incomplete selected-category route data. Housing and connection-distance filters apply to suggested residential areas, not the color scale.
- Routes start at an area reference point, not the searched home's entrance. Address lookup uses approximate Census geocoding and is not saved by the application.
- Near-street/trail area labels come from the nearest named walking edge within 500 m; they are location cues, not verified addresses or neighborhood boundaries.
- Demographic and housing-price context does not enter route weights. Census rent and home-value medians are not listings, transactions or individual appraisals.

## Checks completed
- All source costs finite and >= ordinary walking-time cost.
- Projection allowance checked against all source edge geometries.
- All eligible housing/connection origins pass the 30-minute extent bound.
- The current public default colors 4,331 of 4,402 areas for grocery + pharmacy + park. The remaining 71 lack complete selected-category route data. The former budget-filtered view colored 79 areas at 20 minutes or 535 at 30 minutes; those cutoffs are no longer applied.
- Actual displayed routes match cached scores; no straight-line connectors are invented.
- Category selection, full-map coverage, longer routes and their coverage notes, address-to-area lookup, deselection, share/reload, advanced mode and mobile layout checked in Chrome. Legacy budget URL parameters are removed on load.

## Reproduction order
The 3 km extract and original source caches are retained under `output/plano_boundary_3km` and `data/raw`. They are intentionally not uploaded to GitHub.
1. `bootstrap_expanded_geoai.py`: reuse compatible classifications; infer missing NAIP tiles.
2. `prepare_plano_city_network.py` and `prepare_plano_city_context.py` with `EMPATH_CITY_DATA_ROOT` pointing to the expanded data folder; include expanded traffic acquisition.
3. `landsat_summer_heat.py` with `EMPATH_HEAT_OUTPUT`, `EMPATH_HEAT_SCOPE`, `EMPATH_HEAT_BLOCKS` set to expanded paths.
4. `summarize_plano_city_geoai.py` with the expanded data root; then `block_proxy_friction.py` with expanded edge/block/output paths.
5. `promote_expanded_scope.py`: validates completeness and preserves the prior 1 km snapshot locally.
6. `enrich_plano_housing.py`; `EMPATH_CITY_MODE=1 score_block_accessibility.py`.
7. `certify_short_walk_coverage.py`; `label_public_areas.py`.
8. `EMPATH_CITY_MODE=1 export_routing_network.py`, `map_block_accessibility.py`, `build_accessibility_app.py`.
9. Refresh evaluation/context/gallery artifacts; build the static website. `build_accessibility_app.py` also generates the plain-language app through `build_public_app.py`; do not replace it manually with the advanced HTML.

See `boundary_corrected_method.json` for measured bounds and qualifications, and `weighted_boundary_before_after.csv` for changes. Before/after differences include expanded environmental aggregation and catalog/snap changes, not just a controlled boundary treatment.
