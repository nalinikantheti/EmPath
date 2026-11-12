# Plano city scope, route inspection and evaluation

## Current live product
https://empathmaps.netlify.app/app.html

The current scope is the official Plano municipal boundary, not ZIP codes or Collin County. City area: 186.8 km²; 4,402 clipped Census block reference areas. Walking network and destinations include a 1 km buffer to reduce boundary artifacts.

## What changed
- Full buffered OSM network: 64,936 junctions and 193,128 directed edges; every edge has a three-factor block-context proxy cost.
- City-context GeoAI: 973 tiles, 359 reused compatible classifications and 614 newly inferred. All city blocks have tree predictions; source-image coverage does not establish classification accuracy.
- Summer 2025 Landsat block summaries: 4,169 city blocks with valid direct summaries. Missing heat and other required factors use the existing flagged, bounded block-proxy rules; raw missingness remains preserved.
- 883 destination candidate records in 19 categories. Mapped/curated duplicate institutions may remain; the category cost selects only one lowest-cost candidate, not an average over all records.
- Complete essential/all-category access for 4,331 references; 71 disconnected, including 40 housing-positive references. These are model connection failures, not proof of real-world inaccessibility.
- Public 2020 HU100 counts refreshed for all city blocks: 2,852 housing-positive. Default ranked-list filters also require a <=100 m snap gap and complete selected-category access. Essential-profile eligible candidates: 2,346.

## Actual walking routes
Click a ranked block or map polygon. The app loads the actual weighted graph and runs Dijkstra to the cached lowest-cost candidate for each selected category. It checks that displayed route costs agree with the stored scores. Routes are actual edge geometries, not straight activity-node connectors.

Route cards show physical distance, ordinary walking time, equivalent friction minutes, mapped path/trail tags, and length within 30 m of mapped TxDOT AADT >=25,000. Those tags/proximity values are audit context, not proof of shade, continuous sidewalks or safety. Click a route card to focus one category; use Show all selected routes to restore the full set.

The white start marker is the snapped graph junction. The block reference-point gap and destination gap are reported; connector travel and crossing waits are excluded. Block recommendations are not verified homes or available listings. Census housing counts refer to full 2020 blocks and do not prove housing lies in every city-clipped boundary fragment.

## Data provenance
The live Overpass service was unreliable for road extraction. A Geofabrik Texas PBF snapshot through 2026-11-11T21:22:47Z was downloaded and MD5 verified. Native PyOsmium retained real OSM node IDs; private/no-foot/car-only ways were filtered before building and simplifying the graph. No crossings were invented from mere geometric intersections.

Census geography/housing: Census2020 TIGERweb. Municipal boundary: Plano GIS. Traffic reference: the existing citywide TxDOT/Plano block normalization. Trees: pretrained Restor TCD, 2022 NAIP at 0.6 m. Heat: quality-screened summer 2025 Landsat surface temperature. These vintages differ; current access and land-cover changes need review.

## Evaluation completed
- Same-network time-only accessibility baseline.
- Forward/reverse shortest-path checks, finite cost checks and block aggregation consistency.
- Browser checks for ranked results, residential filters, actual route/score agreement, route focus, category changes, empty selections and mobile layout.
- Essential-service factor sensitivity: equal, canopy-priority, traffic-priority, heat-priority.
- Six spatially spread block origins × three categories: weighted versus fastest routes to the same destination.

Results: residential essential ranking Spearman correlation with time-only is about 0.994; 19/20 top blocks overlap. The three 60/20/20 factor scenarios retained the same top-20 set. Distance is therefore a major driver; this does not prove local comfort validity. In the 18-trip sample, 12 routes changed, average extra walking time was about 15 seconds, and two reduced busy-road-proximity length. No universal improvement is claimed.

Public evaluation page: https://empathmaps.netlify.app/validation.html . Manual review template entries are explicitly NOT REVIEWED.

## Still required for validation
Inspect representative entrances, barriers, crossings and destination eligibility; investigate the 546 >100 m snap gaps and the disconnected references. Independently labeled Plano imagery is needed for local segmentation accuracy. Independent local route-choice/comfort observations are needed to assess preference accuracy. Public maps and imagery can support a small geographic audit without collecting new surveys.

## Local entry point
Use Notebook 23 for current city outputs. Notebook 21 is the earlier four-ZIP stage. County material remains an unscored future-expansion preview.
