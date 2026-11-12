# Debanjan feedback: priorities for EmPath

## Core purpose
Help people compare residential areas by the effort of walking to destinations they choose. Population, housing and demographic layers explain the context; they do not establish how comfortable a route is.

## Immediate priorities
- **Actual wayfinding:** keep selected-block routes, clear start/destination markers, route focus, ordinary walking time and busy-road/path context. Inspect real entrances and crossings before claiming navigation quality.
- **Inclusive destinations:** beauty/hair supply stores added; cosmetics-only stores separate. Expand worship categories to churches, mosques/masjids, synagogues and other mapped worship facilities in a subsequent catalog update. Do not infer a user's religion or required destinations from demographics.
- **Boundary effects:** existing city analysis includes a 1 km routing/destination buffer. Test larger buffers for edge blocks and compare raw equivalent-minute costs. If costs fall materially, label edge estimates incomplete and extend acquisition. Do not lower outer-block scores cosmetically: genuine remoteness can also raise costs.

## Next comparison layers
- **Population density:** 2020 block population is already in the working data. Calculate people per land area with Census land-area fields; flag clipped border blocks whose full population cannot be assigned precisely to the city fragment. Show density beside accessibility. Population counts show where people lived at the Census date, not where people are moving now.
- **Redundancy test:** compare density and accessibility on matching geographies (scatterplot/rank correlation); highlight dense blocks with poor access and lower-density blocks with good access. Similar patterns do not alone establish redundancy: EmPath supplies destination-specific route explanations.
- **Affordability:** start with ACS block-group median gross rent/home value and margins of error, or clearly labeled appraisal data. These are different from current listing or transaction prices. Compare affordability versus access; do not imply block-level price precision or current homes for sale.
- **Demographics:** use aggregate age, disability, household vehicle availability and income to evaluate who is served or underserved. Use the published geography and uncertainty. Keep these out of the environmental edge-cost formula and avoid resident-profile-based neighborhood steering.

## Later extensions
- Satellite basemap: licensed imagery background for inspection; it is not a new analytical model. Add zoom-to-route controls and retain source attribution.
- Slope: elevation-derived edge grade, distinguishing direction, bridges and ramps. A slope map alone does not establish wheelchair accessibility; curb ramps, surface and width are also needed.
- Schools: destinations already exist. Ratings are contextual and value-laden, not a validated walking-quality factor; avoid a universal neighborhood quality score.
- Crime: if considered, keep separate, dated and contextualized. Reporting and enforcement patterns affect recorded incidents; do not present them as individual pedestrian danger predictions or combine them automatically into friction.
- Translation, destination icons and screen-reader support: prioritize labeled controls and readable route summaries; optional text-to-speech later.
- Other cities: make study boundary, sources and POI catalog configurable, then repeat coverage and route audits. Scaling is a data/validation task, not just enlarging the map.

## Policy and presentation
- Households: compare access to their chosen daily destinations within an affordability context.
- City planners: identify populated areas with poor service access and inspect potential crossing, sidewalk or shade interventions.
- Developers/housing organizations: evaluate pedestrian connections and service gaps alongside affordability; avoid equating high accessibility with a mandate for higher prices.
- Future-state story: a person without a car can reach daily needs; show one concrete route problem and an intervention scenario. Label assumed interventions and modeled benefits.

## Scope rule
Keep the working route prototype stable. Add one comparison layer at a time; avoid merging demographics, house prices, school ratings and recorded crime into an unexplained "best neighborhood" score.
