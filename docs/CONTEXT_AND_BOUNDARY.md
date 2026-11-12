**Current boundary correction:** the former 1 km diagnostic below is historical. Production now has weighted 3 km coverage and bounded public comparisons. See `PUBLIC_TOOL_AND_BOUNDARY.md`.

# Population, housing, worship and boundary coverage

## What is implemented
- Optional population, affordability and demographic overlays in the route app.
- A comparison page at /context.html, with interactive map, scatterplots, data downloads and sources.
- Eight static context maps in the gallery.
- Churches, mosques/masjids, a synagogue and other/unspecified worship sites in the actual routable POI catalog. Categories without current source records are not invented.
- A 1 km versus 3 km support test, plus selected-category warnings on affected blocks.
- Notebook 24 for reviewing cached data and results.

## Sources and cleaning
| Source | Fields / geography | Interpretation |
|---|---|---|
| Census2020 TIGERweb blocks | POP100, HU100, AREALAND; 2020 blocks | Stable GEOID queries refreshed all attributes, because older geometry caches omitted most land-area values. Population divided by full original Census land area. City-border fragments flagged; no population redistribution. |
| 2020–2024 ACS summary files | B25064 rent, B25077 home value, B19013 income; 2024 block groups | Medians and 90% MOEs, not listings, sale prices, or individual appraisals. |
| Same ACS release | B25044 vehicle availability, C17002 poverty, B01001 age, B03002 race/ethnicity; 2024 block groups | Negative sentinel/missing estimates retained as unknown. Rates use explicit numerator and denominator. Race/ethnicity is aggregate context, never a suitability score. |
| Same ACS release | B18101 disability; 2024 tracts | Tract geography preserved; no artificial block-group disability estimates. |
| TIGERweb ACS2024 | Block-group and tract polygons | Clipped to city for display; statistics describe the whole original area, not the clipped fragment. |
| Frozen Geofabrik Texas OSM, 2026-11-11 | Public mapped worship and retail candidates | Categories use explicit tags. Religion never inferred from residents or names. Candidate/entrance completeness remains unverified. |

Census API estimate requests required a key, so official freely downloadable table-based summary files were streamed instead. Only relevant Census rows are cached. No API credential was needed.

ACS percentage margins of error use root-sum-of-squares for summed numerators, then the Census proportion approximation (addition fallback where subtraction gives a negative radicand). They are approximate because covariance is unavailable. The universe differs by table: occupied housing units for vehicle availability, poverty-determined population for poverty, and civilian noninstitutionalized population for disability. Selected race categories are not an exhaustive breakdown.

## Comparison method
- Context reference profile: grocery + pharmacy + park. The research essential benchmark remains Hindu temple + grocery + pharmacy.
- Block comparison: housing-positive, snap <=100 m, complete costs; exclude city-border fragments and missing/zero land area for density correlation.
- ACS comparison: spatially assign each eligible block reference point to the matching 2024 block group (tract for disability); average block-origin costs, unweighted across origins. Require at least five eligible origins per Census area.
- Density versus essential-cost Spearman correlation: approximately 0.039 across 2,301 matched blocks.
- Rent and home-value correlations are descriptive ecological comparisons, not causal effects or local preference accuracy. Geography, mixed vintages and uncertainty affect interpretation.
- Context data never enter environmental weights or resident-profile-based recommendations.

## Boundary evaluation
- Acquire a separate 3 km buffer from the same frozen PBF and apply identical walk filters.
- Preserve production origin and destination OSM junction IDs as simplification anchors, avoiding a change in snapping as the explanation for different costs.
- Keep original candidates; add mapped candidates inside the expanded area.
- Compare time-only minimum-category costs, not unobserved extended environmental friction.
- Flag reductions greater than one minute (or newly reachable trips). Expanded support must not materially increase fastest cost; the check passed.
- 3,499 blocks have at least one affected category; rare destination categories dominate many flags. Warnings depend on categories actually selected.
- This diagnoses acquisition effects; it does not correct weighted production scores. Extend environmental coverage and recompute costs before adopting expanded routes. Three kilometers is not a convergence guarantee. Genuine remoteness and disconnected components also matter.

## Policy use
Households can inspect chosen-service routes alongside affordability. City planners can investigate populated areas with poor access and test connectivity/shade proposals. Developers and housing organizations can evaluate affordable pedestrian connections. No current housing listings, health outcomes, school-quality judgments or crime-based neighborhood suitability scores are generated.

## Reproduce
1. `scripts/prepare_plano_social_context.py` retrieves/caches official context and computes summaries.
2. `scripts/build_plano_social_gallery.py` and `scripts/build_map_gallery.py` export annotated PNGs.
3. `scripts/extract_city_pbf_native.py` supports `EMPATH_OSM_DIR` containing a routing_bbox.json for the larger extract.
4. `scripts/build_plano_city_graph_from_pbf.py` supports `EMPATH_OSM_DIR`, `EMPATH_NETWORK_BUFFER_M=3000`, and `EMPATH_PRESERVE_CITY_ANCHORS=1`.
5. `scripts/evaluate_boundary_buffer.py` compares the support and exports flags.
6. Rebuild app and validation pages, then `node scripts/build_netlify_site.mjs`.

## Primary references
U.S. Census Bureau. (2020). 2020 Census block geography and population/land attributes. https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10

U.S. Census Bureau. (2026). 2020–2024 ACS five-year table-based summary files. https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html

U.S. Census Bureau. (2024). ACS2024 statistical geography. https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer
