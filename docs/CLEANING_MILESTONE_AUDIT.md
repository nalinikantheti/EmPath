# Cleaning and connection milestone

The two main assets—block environment polygons and the attributed walking graph—complete the core data-preparation handoff. They do not yet establish verified entrance connections or validated walking routes.

| Roadmap item | Status | Remaining work |
|---|---|---|
| Normalize | Mostly complete | Document mixed observation years and validate destination categories. Metric analysis uses EPSG:26914; display uses geographic coordinates. |
| Geometry and missing data | Automated checks complete | Review flagged features and missing canopy/traffic; do not replace missing values with zero. Preserve legitimate reciprocal and parallel edges. |
| Traversable graph | Structural graph available | Verify selected crossings, access restrictions and sidewalk connections. Disconnected components remain visible. |
| Origins and services | Provisional screening notebook added | Confirm actual entrances and suitable destinations, inspect connector gaps, review unreachable pairs and example routes. |

## Revised graph requirement
Keep all feasible pedestrian alternatives in the underlying graph. Calculate distance-shortest and lowest-friction routes from that graph. Retaining only distance-shortest paths would remove cooler alternatives. Exclude origin-to-origin recommendations from the results, rather than removing residential streets.

## Small feasible next milestone
1. Run Notebook 11 to create candidate origins, services and network-only baseline distances.
2. Review a small set of origins across all four ZIPs, plus groceries, pharmacies and temples. Add missing services.
3. Confirm access points and crossings; investigate large snapping gaps and unreachable pairs.
4. Compare baseline routes with documented, nonnegative friction costs. GeoAI-derived preference estimates remain separate from the structural network checks.

Notebook 11 performs nearest-node screening. It never certifies access, adds unverified straight connectors, or automatically repairs barriers. Network travel times assume 1.2 m/s and omit connector travel and crossing waits.

## Step 3 handoff update

Full-area GeoAI and Landsat inputs now exist. See `docs/STEP3_FRICTION_HANDOFF.md` and Notebook 17 for current feature coverage, missing inputs and tested cost scenarios. Core preparation is sufficient to begin prototype modeling; this does not close the entrance, crossing and connectivity validation gaps above.
