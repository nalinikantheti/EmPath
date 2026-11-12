# Block-context friction prototype

Open Notebook 20 or `output/weighted_walking_network/block_proxy_weighted_network.html`.

All 93,452 original OSM directed edge IDs remain present. Block proxies provide three-factor weights for 93,450; two remain unsupported. This does not mean OSM captures every actual path.

The block version intersects each edge with census polygons and takes a length-weighted mean per available factor. A missing factor can use the nearest block with a valid value, within 250 m of the edge. That transfer is explicitly recorded. If no such value exists, the factor stays unknown. All three proxy factors are required for the combined cost. Partially covered edge lengths are extrapolated from their supported portions and flagged.

`cost = length_m / 1.2 × [1 + (estimated canopy deficit + estimated traffic burden + estimated heat burden)/3]`

Equal weights are assumptions. Canopy is an existing AI tree prediction; block overlay and nearest-block transfer are GIS operations, not additional machine learning. Heat is surface temperature, not air temperature. Nearby block context is not a direct observation of the trail. Boundary lines sample both adjacent blocks symmetrically when both have positive-length intersection.

874 edges use at least one nearby-block transfer; 2,664 have incomplete overlap. Full map uses blue for lower multipliers and red for higher. Dashed lines identify partial overlap/nearby transfer. Original edge/available-factor/strict/pessimistic variants remain selectable. Popups disclose block sources.

A block boundary layer exposes the actual overlays. The municipal trail reference overlay helps locate source geometry gaps, but does not create graph connections. Missing walking geometry must be verified and incorporated separately.

Activity graph: `block_context_proxy_activity_graph.graphml`, 328 reachable pairs; 12 disconnected, with only four provisional residential-origin candidates. No same-role recommendation edges.

Rebuild: `block_proxy_friction.py` → `build_residential_poi_graph.py` → `visualize_weighted_walking_network.py`.

Generated map is local and authenticated; deployed Netlify site is unchanged. Outputs remain ignored by Git. Keep data vintages, block smoothing, geometry completeness, entrance/crossing checks and proxy uncertainty visible in the demonstration.
