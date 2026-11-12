# Prototype · available-factor friction

## Open
- `notebooks/19_full_weighted_walking_network.ipynb`
- `output/weighted_walking_network/full_weighted_network.html`

The full geographic map defaults to available-factor scoring. Dashed edges are estimates based on one or two factors. Click for available-factor count, missing names and route cost. The selector preserves complete-data mode and adds pessimistic sensitivity mode.

## Equation
`cost_seconds = ordinary_time_seconds × (1 + mean(available canopy deficit, traffic burden, heat burden))`

Equal factor weights among available factors, lambda=1. No available factors means unknown cost. All three known gives exactly the original score. Missing observations are not replaced with zero. The 98% imagery-coverage criterion remains unchanged; no new measurements or AI training were added.

## Results
- 80,110 edges: all three usable factors.
- 12,090: two factors; 1,248: one factor; four: none.
- Prototype: 93,448 weighted edges out of 93,452.
- Activity graph: 328 reachable pairs from all four existing origins, versus 79 strict-friction pairs. The distance-only baseline also has 328; twelve pairs remain disconnected.
- `prototype_friction_activity_graph.graphml` retains origin→POI only, one minimum-cost route per pair.
- `prototype_route_sensitivity.csv` reports each route's estimated-distance fraction and sensitivity flag.

## Sensitivity and limitation
The separate pessimistic scenario assigns missing burdens a value of 1 as an explicit assumption. 184 of 328 prototype routes change under that assumption. Mean route distance using partially observed edges is about 9.9%. These results show material dependence on missing-data assumptions; they do not establish accurate preferences, safety, or optimal comfort.

Available-factor costs are not fully comparable across different factor combinations and can favor poorly observed paths. This is an exploratory prototype, with raw missingness preserved. Entrance/crossing checks and broader residential-origin coverage remain unfinished.

## Rebuild
1. Run `scripts/prototype_missing_data.py` to export the annotated edge-cost table.
2. Run `scripts/build_residential_poi_graph.py` to rebuild all four objectives and sensitivity summaries.
3. Run `scripts/visualize_weighted_walking_network.py` to rebuild the map and PNG.

Generated HTML uses the existing local basemap credential configuration. Keep it out of Git; the deployed website has not been changed.
