# Residential-to-POI weighted graph

## Structure
- Activity nodes: existing four provisional block origins and 85 destination candidates.
- Activity edges: origin → destination only; one minimum-cost walking route per reachable pair per objective.
- No origin → origin, destination → destination, or reverse recommendation edges.
- Equal-cost ties keep one available route. Longer alternatives under the same objective are omitted.
- A detailed street junction is not an activity node. Walking paths may pass through residential streets or past other destinations.

## Two separate objectives
1. **Shortest-time graph:** minimum physical distance, using a fixed 1.2 m/s speed. 328 reachable pairs; 12 unreachable.
2. **Lowest-friction graph:** minimum Step 3 assumed three-factor cost, lambda 1. 79 reachable pairs; 261 unavailable on the supported graph.

The latter does not necessarily follow the distance-shortest route. Separate graphs avoid storing competing alternatives as parallel recommendation edges.

**Important:** friction-unavailable does not mean physically unreachable. Missing environmental factors exclude walking edges and fragment the supported graph. Resolve feature coverage or agree on a documented missing-data policy before using this graph for comprehensive residential ranking. Do not silently replace unknowns with zero burden.

## Files
Run `notebooks/18_residential_to_poi_weighted_graph.ipynb` or `scripts/build_residential_poi_graph.py`.

In `output/residential_poi_graph/`:
- `shortest_time_activity_graph.graphml`, `lowest_friction_activity_graph.graphml`: NetworkX-readable recommendation graphs.
- `origin_poi_costs.csv`: costs and unavailable pairs.
- `origin_poi_routes.gpkg`: actual route geometries, not straight origin/destination connectors.
- `route_segments.csv`: ordered original u/v/key segments for every retained route.
- `*_selected_network.gpkg`: union of used detailed edges, with shared segments stored once.
- `activity_nodes.gpkg`: provisional activity-node locations.
- `graph_method.json`: source inventory, assumptions and checks.
- `selected_origin_preview.html`: notebook-generated preview of five destinations for a selected origin; no remote basemap dependency.

## Checks and scope
GraphML round-trip passed. Every recommendation edge has the correct role direction and nonnegative weight. Every retained route cost equals its Dijkstra minimum. The full underlying graph is preserved.

This first inventory is not all residential blocks or all homes. Origins, POI entrances, access and crossings are provisional. Costs omit connector travel and crossing waits. An address-containing block is not proof of residential use. Co-snapped locations can have zero network distance without zero door-to-door distance.

## Available-factor prototype update
See `docs/PROTOTYPE_MISSING_DATA.md`. Complete-data costs remain available; a separately labeled prototype restores 328 pairs using available factors and exposes partial evidence. Pessimistic missing-data sensitivity changes 184 routes, so this is not validated preference routing.
