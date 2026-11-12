# EmPath scoring equations

## 1. Walking-edge friction

w_e = (L_e / v) × [1 + ((1 − Ĉ_e) + Q̂_e + Ĥ_e) / 3]

- w_e: estimated environmental-friction cost of a walking segment, in equivalent seconds.
- L_e: segment length in meters.
- v: assumed walking speed, 1.2 meters per second.
- Ĉ_e: estimated tree-cover fraction, from 0 to 1. Canopy deficit is 1 − Ĉ_e.
- Q̂_e: normalized traffic burden, from 0 to 1; higher means more traffic exposure.
- Ĥ_e: normalized surface-temperature burden, from 0 to 1; higher means hotter surface context.

The three burdens receive equal assumed weights. The bracketed multiplier ranges from 1 to 2. For example, a two-minute segment with mean burden 0.7 receives a cost of 3.4 equivalent minutes; its assumed physical walking time remains two minutes.

The hats indicate estimates. In the default prototype, factor values come from length-weighted census-block overlays along the segment. Where an intersecting-block factor is unavailable, a nearby valid block within 250 meters may supply a flagged proxy. Canopy originates from the pretrained tree model. These proxies do not measure actual shade, air temperature, safety or pedestrian preference. Equal weights were not learned from local route-choice data.

## 2. Lowest-friction route to a service category

C_k(b) = (1 / 60) × min over d in D_k [min over paths P from b to d (sum of w_e for e in P)]

C_k(b) is the least equivalent walking cost, in minutes, from block b to any candidate destination in category k. D_k is the catalog of destinations in that category. “Closest” means lowest total weighted network cost, not straight-line distance. Dijkstra’s algorithm finds the minimum sum of nonnegative edge weights.

Block interior reference points and mapped destination locations are snapped to graph junctions. Their connector gaps are reported, but connector travel and crossing waits are not included. Entrances remain unverified.

## 3. Census-block accessibility burden

A(b) = [C_1(b) + C_2(b) + … + C_K(b)] / K

K is the number of service categories selected by the user. Each selected category contributes one trip: the lowest-cost reachable destination in that category. Lower A(b) indicates lower combined walking burden. The prototype uses equal category weights. The sum and worst-category cost can also be reported.

If any selected category is unreachable, the combined score is unknown. An unreachable category does not count as zero cost. Scores represent geographic block reference points, not verified houses.

## 4. Map colors

Display burden = 100 × clip[(raw burden − P2) / (P98 − P2), 0, 1]

P2 and P98 are the 2nd and 98th percentiles of valid raw burdens in the displayed pilot/reference selection. Blue represents lower relative burden; red represents higher relative burden. This display transformation does not modify routing weights. The interactive category selector rescales its colors for each selection; compare raw equivalent minutes when comparing selections.

## Scope and status

The four-ZIP prototype completes the computational sequence from environmental proxies through weighted routing to block accessibility. This is an operational proof of concept, not a validated production navigation or housing-recommendation system. Collin County geography has been acquired; countywide network/environmental inputs and scores remain unfinished. Five Hindu-temple address candidates are included; the catalog is not exhaustive, and one directory-sourced address is flagged for review.
