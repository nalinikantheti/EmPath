# Network-derived walking accessibility

## Open
- Notebook 21: `notebooks/21_network_accessibility_scores.ipynb`.
- Full weighted paths: `output/weighted_walking_network/block_proxy_weighted_network.html`.
- New block choropleth: `output/block_accessibility/block_accessibility_map.html`.
- Original full layer stack: `output/clean_deliverables/all_layers_map.html`, now defaulting to the network-derived accessibility layer instead of the provisional environmental overlay.

## Calculation
1. Retain the existing detailed pedestrian graph. Assign `w_e = length/1.2 × [1 + (estimated canopy deficit + estimated traffic burden + estimated heat burden)/3]` in equivalent seconds.
2. For every census block, snap a representative interior point to a graph junction; report the gap and flag >100 m.
3. For each category, find the minimum sum of edge weights to any candidate destination in that category. Multi-source Dijkstra runs on the reversed directed graph so this represents travel **from block to POI**, not the reverse.
4. Average these category costs with equal weights. Also export their sum and maximum. Unreachable categories make the overall score unknown, not zero.
5. Color raw mean costs with a 0–100 2nd–98th percentile stretch across complete pilot blocks: blue lower burden, red higher burden. This display step does not change route weights.

## Results and graphs
- 93,450 finite weighted directed walking edges; two unsupported edges excluded rather than accidentally receiving NetworkX's default weight.
- 2,862 block reference nodes, including nonresidential land.
- 322 POI candidates: original 317 plus five curated Hindu-temple address candidates.
- 14 categories; all-category and temple/supermarket/pharmacy profiles.
- 2,804 blocks have complete reachability; 58 remain unknown on the choropleth.
- `weighted_walking_graph.graphml.gz`: full weighted routing network.
- `block_nearest_category_activity_graph.graphml`: block origins to nearest POI per category only. Block nodes carry average combined cost and relative score; edges carry category trip costs. No block–block or POI–POI edges.
- `nearest_category_costs.csv`: selected destination and raw equivalent minutes for every block/category.
- `block_accessibility.gpkg/csv`: geometry/attributes and combined scores.

## Display and replacement
The full path map now stretches relative burden enough for blue low-friction paths to be visible. The Rowlett green locator remains separate and can be switched off. New accessibility maps and two PNGs are in the local website source and Map Gallery; the old environmental index is retained as a clearly labeled historical comparison. No live deployment is claimed.

## Important limits
Block reference points and POI parcel/feature locations are not verified entrances. Scores exclude connector travel and crossing waits. All blocks are scored geographically; this is not a verified housing inventory. Network access/crossings and POI completeness still require review. Candidate destinations are limited to pilot bounds, which can disadvantage boundary areas.

Equal environmental/category weights are assumptions. Block proxies smooth trail-level variation; surface temperature is not air temperature, canopy is not actual shade, and these scores are not medical risk predictions. The GeoAI model is the existing pretrained tree model; routing and aggregation add no new machine-learning claim.

The original OSM query omitted worship. Temple candidates are in `config/accessibility_temples.json`, matched to the city's address points. Four addresses are supported by official institution websites. Raghunath's address is directory-sourced and marked for review because its official contact page does not provide the street address. The temple inventory is not exhaustive or a substitute for user-specific religious suitability.

## Checks
- Forward shortest-path spot checks agree with reverse multi-source category costs.
- Recomputed table means and display scores match the exported block scores.
- Unknown category costs remain unknown in combined scores.
- Weighted block-node attributes equal combined category costs.
- JavaScript syntax checked for standalone maps and the preserved all-layer viewer.
- Website source snapshots checked for absence of the local CARTO key.
- Notebook 21 executed; network and choropleth PNGs visually reviewed.

Rebuild: `score_block_accessibility.py` → `map_block_accessibility.py`. For path color changes first run `visualize_weighted_walking_network.py`. Source website generation does not deploy the site.
