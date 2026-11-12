# GeoAI and the walking-friction model

## What has actually run

- Environmental cleaning, overlays, canopy-class decoding and traffic normalization: GIS/statistical processing, not a newly fitted AI model.
- Texas canopy: an upstream ML-derived product. Using it does not mean EmPath ran its imagery model.
- New route-preference baseline: a constrained pooled binary logit fitted to public Singapore route-choice labels. This is a lightweight geospatial ML component, not computer vision, a graph neural network or the paper's full hierarchical model.
- Optional SamGeo notebook 07 still has not run inference. It needs real compatible RGB imagery and optional dependencies.

The GeoAI package is one library choice, not a requirement for geospatial ML. If the event specifically requires imagery inference or deep learning, the behavioral model does not fulfill that narrower requirement.

## Where the learned component fits

Public observations of route choices → learned distance/sun trade-off → explicitly calibrated nonnegative segment costs → conventional shortest-path routing.

The new baseline uses 408 sunny-condition route choices from 46 participants. Participants, not rows, are split between training and evaluation. Both a holdout and grouped five-fold cross-validation are saved. The source is Melnikov et al. (2022), https://doi.org/10.1038/s41598-022-06383-5 ; public data/code: https://osf.io/aj4vk/ . EmPath's model simplifies the study by pooling participants and grouping tree/building shade together; it is not an exact reproduction.

Five-fold out-of-participant predictions give distance-only accuracy 73.3% and distance-plus-sun accuracy 72.8%. The latter has slightly lower log loss (0.577 vs 0.581). This is roughly comparable performance, not a demonstrated substantial improvement, and not validation in Plano. Full-data coefficients are a refit for later optional application; evaluation uses held-out fits, not the full-data refit.

The model learns a positive extra cost per sun-exposed meter, on top of physical length. It has no labels for traffic, crossing difficulty, sidewalk completeness, medical risk or personalized mobility. These weights are not learned by this model.

## Normalized inputs

| Feature | Transformation | Interpretation |
|---|---|---|
| canopy_cover_01 | estimated canopy percent / 100 | More cover at larger values |
| canopy_deficit_01 | 1 − canopy_cover_01 | More potential exposure burden at larger values; not actual sunlight |
| traffic_burden_01 | City-referenced traffic index / 100 | More nearby mapped traffic at larger values |
| distance_km | meters / 1000 | Additive travel distance; do not replace with per-edge min-max ranks |
| regional weather | Retain temperature/humidity/wind in original units | Shared summer-afternoon scenario, not spatially varying observations |

Only actual cost factors need normalization, not ZIP codes, IDs, coordinates, boundaries or map labels. Same 0–1 range does not imply equal human burden. Do not count both distance and assumed walking time as independent needs without justification. Missing values remain missing.

No overall walking score is silently assigned. `scenario_score()` requires explicit nonnegative canopy/traffic weights and labels the result as a scenario. The code does not assume those weights are empirically learned.

## Applying the learned model later

A supported additive form is:

`equivalent_distance_m = physical_length_m + learned_extra_sun_factor × sun_exposed_length_m`

This stays nonnegative and is unchanged by splitting a path into shorter segments. But sun-exposed length must be known or modeled. Approximating it by `length × (1 − canopy_fraction)` is a separate, unvalidated Plano scenario: overhead canopy coverage is not the same as time-specific path shade. Building shade, sun angle and weather are absent from that substitution.

The coefficients have not been inserted into the production graph. Traffic must remain a separate stated scenario penalty until suitable preference labels are available. Do not feed negative z-scores directly into Dijkstra edge costs.

## Are the two deliverables enough?

They are the core inputs for a prototype, but the next required steps are:

1. Choose representative homes/block access points and destination categories.
2. Validate their graph connections, entrances and important crossings.
3. Choose a documented cost function, including transfer assumptions and missing-data handling.
4. Compare distance-only and friction routes, then aggregate route costs into residential accessibility rankings.

Apply costs at the walking-segment level. Census-block summaries support interpretation; a whole block should not erase finer differences along a route.

## Open in VS Code

- `notebooks/09_normalized_features_and_route_preferences.ipynb`: inspect normalized tables and the learned baseline.
- `output/friction_features/`: normalized block and edge tables with a feature dictionary.
- `output/route_preference_model/`: fitted coefficients, held-out/out-of-fold predictions and participant splits.

These additions leave the current interactive map unchanged.
