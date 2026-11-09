# EmPath: related projects and methods

Research checked November 8, 2026. Repository code was inspected, not installed or executed. These are precedents and possible implementation references, not evidence that their models transfer accurately to Plano.

## 1. Closest research design: sidewalk-level heat accessibility in Los Angeles

**Colaninno et al., “A sidewalk-level urban heat risk assessment framework using pedestrian mobility and urban microclimate modeling.”**

- [Paper](https://journals.sagepub.com/doi/10.1177/23998083241280746)
- [Open author PDF](https://re.public.polimi.it/retrieve/7ce82972-3315-4bae-9698-0de06a45c311/colaninno-et-al-2024-a-sidewalk-level-urban-heat-risk-assessment-framework-using-pedestrian-mobility-and-urban.pdf)

The study combines residential origins, several everyday destination categories, pedestrian networks, and microclimate modeling during an LA heat wave. This closely matches EmPath's homes-to-essential-services framing. Adapt its separation of pedestrian accessibility and heat exposure. Full replication is unsuitable for the nine-hour prototype: the workflow includes QGIS-based microclimate tools and StreetLight-based pedestrian calibration. It is not an open training set of perceived walking friction. No exact full-study implementation repository was verified.

## 2. Closest inspected Python routing implementation: Street Shadow

- [Repository](https://github.com/jlgonrod/street_shadow)
- [Graph, shadow fraction, edge weight and routing functions](https://github.com/jlgonrod/street_shadow/blob/main/modules/graphs.py)
- [Route-generation workflow](https://github.com/jlgonrod/street_shadow/blob/main/main_get_routes.py)

Uses OSMnx, NetworkX-compatible routing, GeoPandas and mapped route comparisons. The transferable sequence is pedestrian graph → per-edge shadow fraction → nonnegative edge costs → shortest paths → comparison map. Its shadow modeling depends on local building/cadastral inputs; do not copy the Malaga configuration into Plano. Its shade preference parameter is specified manually, not learned. The inspected implementation sometimes returns zero shade on processing errors; EmPath should distinguish missing estimates from observed absence of shade. Repository license: GPL-3.0; review obligations before incorporating code.

## 3. Strong scientific reference for shade-weighted networks: CoolWalks

- [Scientific Reports paper](https://www.nature.com/articles/s41598-025-97200-2)
- [Code](https://github.com/henrik-wolf/CoolWalks)
- [Released research data](https://zenodo.org/records/11103149)
- [Network measures implementation](https://github.com/henrik-wolf/CoolWalks/blob/main/src/measures.jl)

Examines shade-sensitive routing in Manhattan, Barcelona and Valencia. The conceptual edge cost is shaded length plus sunlit length multiplied by a sun-aversion parameter. Useful for comparing distance-optimal and shade-sensitive accessibility at different times. The code is Julia, so use the methodology rather than changing EmPath's Python stack. A selected sun-aversion parameter is a scenario assumption, not a learned Plano preference. Repository license: MIT.

## 4. Python origins-to-destinations accessibility: UNA

- [Current repository](https://github.com/City-Form-Lab/urban_network_analysis)
- [Documentation and tutorials](https://urban-network-analysis.readthedocs.io/en/latest/index.html)
- [Earlier Madina repository](https://github.com/City-Form-Lab/madina)

MIT City Form Lab's Python library connects weighted origins and destinations to spatial networks and computes accessibility and pedestrian flows. It supports perceived-length edge costs. This supplies a useful architecture for residential origins and individual destinations. Madina's README points to UNA as its successor; avoid starting from the archived predecessor. UNA does not itself provide learned heat-friction coefficients. For nine hours, retain the existing stack unless switching solves a specific implementation problem.

## 5. Open amenity-accessibility scoring: Walkable Accessibility Score

- [Repository and methodology](https://github.com/kcredit/Walkable-Accessibility-Score)
- [Public-data tutorials](https://github.com/kcredit/Walkable-Accessibility-Score/tree/main/tutorials)
- [Paper](https://journals.sagepub.com/doi/10.1177/23998083251377116)

Useful for transparent amenity categories and distance-decay accessibility scoring. Its distance approach is Euclidean rather than sidewalk-network routing, so it cannot substitute for EmPath's crossings and heat-sensitive paths. The historical research uses InfoUSA business data; use the public-data tutorials rather than assuming every original input is freely reusable. Inspect licensing before copying code.

## 6. A concrete visual reference: Philadelphia Pedestrian Shade Routing

- [Project explanation and route visualizations](https://kavanaraju.github.io/projects/shade-routing.html)

Shows a Python geospatial pipeline and interactive presentation of shade-aware pedestrian alternatives. Useful for deciding how to show a shortest route alongside a shade-favoring route. Its published weighting examples are manually specified. A source repository for this exact implementation was not verified, and the project's reported results were not independently reproduced.

## 7. Walk Score: residential scoring inspiration

- [Official methodology](https://www.walkscore.com/methodology.shtml)

Scores proximity to amenity categories using distance decay, with pedestrian-friendliness measures such as intersection density and block length. Useful for a simple location score and explaining why access to several essential services matters. The methodology page is not a reusable open implementation of its proprietary score. It does not supply learned heat-sensitive sidewalk edge weights.

## 8. City Health Dashboard: reporting and context

- [Walkability metric](https://www.cityhealthdashboard.com/metric/walkability)
- [Data access](https://www.cityhealthdashboard.com/data-access)
- [Technical documentation](https://www.cityhealthdashboard.com/technical-documentation)

Useful for neighborhood comparisons, contextual indicators, source documentation and map design. Its walkability metric uses Walk Score and is presented at city and census-tract scales; it is not a separate independent validation source. The metric's limitations include omission of weather and sidewalk quality. Public data access and documentation are available; an official application source repository was not verified.

## Recommended combination for EmPath

1. Use the LA study to justify the research question: heat-sensitive access from homes to essential destinations.
2. Use Street Shadow and CoolWalks to guide pedestrian edge costs and route comparisons.
3. Use UNA's origin/destination architecture, with the existing Python network stack where practical.
4. Borrow clear location scoring and contextual map presentation from Walk Score and City Health Dashboard.

Keep edge conditions, preference parameters and routing separate. None of these examples establishes a publicly trained model that jointly learns Plano residents' trade-offs among heat, shade, distance, traffic and crossings. XGBoost or LightGBM would still require a defined target and relevant labels. Scenario penalties must be identified as assumptions. A classifier that predicts whole-route preference does not automatically yield additive edge costs.

For the hackathon, a defensible contribution is a Plano demonstration of how heat-sensitive pedestrian accessibility changes residential rankings for household-selected essential destinations. Compare against shortest-distance routing and disclose uncertainty; do not claim that shade-aware routing itself is new.
