# EmPath pilot geography screening

Prepared November 7, 2026. Python-only screening, not a validated heat-resilience assessment.

## Recommendation

Use Census ZCTAs 75025, 75024, and 75074 as the proposed comparison geography (approximately 38.5 square miles of land in total). All three touch 75025. Keep 75025 as the initial implementation and household case-study area. If a smaller scope is needed, prioritize 75025 + 75074 (approximately 25.5 square miles).

75025 already contains meaningful block-group canopy variation. Expansion is recommended to broaden the range of physical contexts rather than because 75025 is demonstrably homogeneous. 75074 contributes the widest central canopy range; 75024 contributes more low-canopy contexts. This does not establish that one entire ZIP code is hotter or less resilient than another. 75023 was screened but is not prioritized because its central canopy range is less distinctive than 75074's.

## Screening results

| ZCTA | Land area, sq mi | Approx. area-weighted canopy | Area-weighted P10–P90 canopy |
|---|---:|---:|---:|
| 75025 | 9.55 | 18.54% | 12.49–24.28% |
| 75024 | 12.95 | 16.24% | 8.39–26.08% |
| 75074 | 15.98 | 19.79% | 7.56–31.86% |
| 75023 | 9.20 | 19.33% | 11.24–26.68% |

P10–P90 describes the middle 80% of covered geographic area after assigning each overlapping block-group canopy estimate to its clipped ZCTA pieces. It is not a measurement of individual streets. Values are not population weighted. Valid canopy geometry covers approximately 100% of the first three screened ZCTAs other than 75074, where coverage is approximately 98%. All downloaded block-group canopy values are valid; uncovered area is not assigned zero.

## Sources and computation

- American Forests official download page: https://www.treeequityscore.org/methodology?tab=data-download
- Texas GeoJSON archive linked by that page: https://tes-app-data-share.s3.amazonaws.com/tx/tx_geojson.zip
- Boundary service: https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2
- 2020 Census ZCTA polygons, served in the ACS2024 map service.
- Source `treecanopy` values are fractions from 0 to 1, converted to percentages using the archive's data dictionary. Local records identify Google as the canopy source. Underlying canopy acquisition year has not been verified; retrieval date is not acquisition date.
- Intersect block-group geometry with ZCTA geometry in EPSG:5070, then weight canopy estimates and quantiles by intersection area. Block-group values are assumed uniform inside each polygon; this is an approximation.
- An archived third-party ArcGIS copy was inspected and rejected because local canopy values were missing. It is not used in these results.
- Reproduce with `scripts/screen_pilot_scope.py` using requests, GeoPandas, pandas, and Matplotlib.

## Next validation

Before finalizing route demonstrations, calculate canopy along actual sidewalk corridors, impervious coverage, continuous exposed walking time, and verified public rest/shade opportunities. Park greenery or private backyard canopy does not automatically protect a pedestrian. Use one consistent map scale across the whole pilot. A difference in canopy does not itself establish an inequity in health outcomes.

For a heterogeneous demonstration, select multiple residential origins and plausible short routes spanning low-, medium-, and high-protection contexts. Keep the household origin as one example; do not require every route to start there. Permit the routing graph to extend outside the reporting boundary.

## Files

- `canopy_screen.png`: four-ZCTA comparison map, not a temperature map.
- `canopy_screen_summary.csv`: computed statistics.
- `recommended_pilot_zctas.geojson`: the three selected polygons.
- `recommended_pilot_boundary.geojson`: their dissolved union.
- `canopy_zcta_intersections.geojson`: clipped polygons used in calculation.
- `data_dictionary.txt`, `source_metadata.json`: definitions and provenance.
