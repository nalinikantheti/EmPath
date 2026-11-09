# Walking data coverage audit

Checked November 8, 2026 against cached Census ZCTA polygons and live Plano GIS feature counts.

| ZCTA | Area inside cached processing boundary | Cached sidewalk polygons | Source sidewalk polygons | Cached trail features | Source trail features |
|---|---:|---:|---:|---:|---:|
| 75023 | 9.08% | 595 | 4,077 | 12 | 332 |
| 75024 | 3.54% | 356 | 4,442 | 0 | 392 |
| 75025 | 100.0% | 4,266 | 4,266 | 388 | 388 |
| 75074 | 0.71% | 12 | 7,242 | 0 | 623 |

Counts represent features intersecting each ZCTA, not unique totals across all ZCTAs; boundary-spanning features may appear more than once. Cached geometries retain full features, so some extend beyond the cached query area. Source counts establish available mapped features, not complete real-world sidewalk inventories or routable connectivity. Sidewalks are polygons, not ready-made routing edges. No dedicated crossing layer or validated pedestrian graph was found in the processed data.

## Conclusion

The saved walking data does not cover the full four-ZCTA study area. Only 75025 plus a 250 m buffer has been downloaded and cleaned. The live city service contains sidewalk and trail features in all four ZCTAs. The next step is to retrieve and clean the full four-ZCTA area, then validate connections and crossings.

Sources:
- https://maps.planogis.org/arcgiswad/rest/services/OpenData/Sidewalks/FeatureServer/0
- https://maps.planogis.org/arcgiswad/rest/services/OpenData/TrailCenterlines/FeatureServer/0
