# EmPath: Detailed Project Roadmap and Implementation Plan

Prepared November 8, 2026

> **Scope update:** Plano eligibility is confirmed. The hackathon is due November 14, 2026, with a five-minute presentation. Use `ONE_WEEK_HACKATHON_PLAN.md` as the active delivery plan. This longer roadmap is retained as a research backlog. Award categories are social impact, data visualization, presentation/storytelling, and overall, as reported by the user.

## 1. Project purpose

EmPath will help households compare residential locations according to pedestrian access to destinations they care about, such as temples, grocery stores, pharmacies, and other everyday services. It is intended to support people who cannot rely on driving in car-dependent suburban environments.

The project will distinguish geographic proximity from the burden of reaching a destination on foot. A short route may involve substantial sun exposure or a difficult crossing, while a somewhat longer route may offer better pedestrian conditions.

The final proof of concept will combine:

1. **PathéResistance:** public geospatial data preparation, pedestrian-network construction, environmental features, learned or explicitly assumed edge costs, and accessibility analysis.
2. **EmPath:** a Python dashboard for selecting destinations, comparing residential origins, viewing routes, and understanding the reasons for a ranking.

The system will estimate environmental accessibility. It will not establish medical safety, diagnose vulnerability, determine whether a person can navigate independently, or guarantee that a route is safe. The housing output will compare modeled locations, not claim that properties are available for sale.

This plan covers the proposal and requirements discussed so far. Any separate course rubric, submission format, or required institutional approval should be mapped to the deliverables before final submission.

## 2. Fixed decisions and boundaries

| Decision | Project specification |
|---|---|
| Implementation | Python scripts, Jupyter notebooks, and a Python-authored dashboard; no ArcGIS Pro or QGIS workflow required |
| Evidence | Publicly accessible datasets and published research; no new participant survey assumed |
| Initial build area | ZCTA 75025, with an initial 250 m processing buffer |
| Expanded comparison area | ZCTAs 75025, 75024, and 75074; 75023 remains an optional comparison |
| Geography terminology | Use Census ZCTAs for reproducible boundaries; distinguish them from postal ZIP codes |
| Residential origins | Census blocks initially; use parcels/access-point samples for resolution comparisons |
| Destinations | Individual suitable facilities or businesses, connected through plausible pedestrian entrances |
| Routing network | Detailed sidewalk, trail, junction, entrance, and crossing connections |
| AI objective | Learn supported environmental/behavioral relationships, with the initial behavioral experiment focused on shade versus distance |
| Core limitation | Public Singapore preferences cannot establish accuracy for vulnerable pedestrians in Plano |

The 250 m buffer is a starting processing choice, not proof that all useful routes fit inside it. Increase the routing/download extent where routes, entrances, or relevant destinations extend farther. Reporting boundaries and routing boundaries serve different purposes.

## 3. Current project status

### Completed foundation

- VS Code workspace named EmPath.
- Working project Python environment and a discoverable `Python (EmPath)` notebook kernel.
- Initial canopy comparison of four candidate ZCTAs.
- Static and interactive canopy maps.
- Public resource guide with case studies, dataset links, uses, and limitations.
- First cleaning pipeline with immutable raw snapshots, metadata, checksums, and processed files.
- Geometry/schema cleaning for 75025 plus a 250 m context buffer.
- Public Singapore behavioral CSV downloaded and checked.
- Cleaning notebook executed with outputs saved.
- Four targeted cleaning tests passed.

### Available cleaned records

| Dataset | Retained records | Interpretation |
|---|---:|---|
| Sidewalk surfaces | 5,247 | Polygons, not ready-made routing centerlines |
| Trail features | 406 | Lines, not yet an audited connected graph |
| Parcels | 17,277 | Not yet classified as residential origins |
| Address points | 17,558 | Not confirmed pedestrian entrances |
| Singapore choices | 728 | Repeated observations from 56 participants |
| Singapore sun-present subset | 408 | Repeated observations from 46 participants |

These record counts are outputs of the current snapshot and scope, not permanent counts of all infrastructure in the postal ZIP code. Two sidewalk geometries were repaired. Duplicate geometries were retained and flagged. Spatial filtering removed records outside the actual buffered scope after a broader rectangular API query.

### Not yet implemented

- Audited pedestrian graph and crossing/entrance connections.
- Residential Census-block origins and verified destination inventory.
- Fine-grained canopy, weather, traffic, and impervious-surface edge features.
- Trained preference models and held-out evaluation.
- Least-friction residential accessibility ranking.
- Destination-selection dashboard and resolution/sensitivity experiments.

## 4. Requirements-to-deliverables checklist

| Requirement | Evidence to produce | Completion condition |
|---|---|---|
| Civic problem and intended users | Written problem statement and stakeholder map | Explains who needs the tool, why conventional proximity is insufficient, and what the tool can support |
| Public data feasibility | Source inventory, licenses/access notes, coverage map | Every used feature has documented provenance, date, resolution and missingness |
| Geographic heterogeneity | Scope comparison and local corridor examples | Selected area contains a documented range of pedestrian environments, rather than only a visually stretched color scale |
| Reproducible cleaning | Download/clean scripts, raw manifests, QA reports | Another run can reproduce the snapshot-derived analysis |
| Pedestrian network | Graph files and route audit | Demonstration routes have no unresolved critical crossing/access problems |
| GeoAI application | Training data, learned parameters/models, evaluation notebook | Shows what was learned from observations and what remains assumed |
| Personalized accessibility | Origin-destination costs, category selection, rankings | All required destination categories influence results and unreachable needs remain visible |
| Spatial-resolution analysis | Parcel/block/block-group comparison | Uses consistent destination sets, costs, scenarios, and aggregation rules |
| Evaluation | Baselines, held-out metrics, sensitivity results | Claims match the actual evidence and uncertainty |
| Governance and accountability | Data/model cards, privacy and maintenance notes | Explains limitations, responsible interpretation, updates, and institutional status |
| Final communication | Dashboard, figures, report, slides, demo | A reviewer can follow inputs → model → routes → recommendation |

## 5. Phase 1: Finalize the research specification

**Goal:** settle what the system will measure before expanding the code.

### Steps

1. Write a one-paragraph problem statement focused on non-driving access to essential destinations in Plano.
2. State the principal research question: **How do shade-sensitive pedestrian costs change residential accessibility rankings compared with walking distance/time alone?**
3. State the AI question: **How well do candidate models predict held-out public route-choice observations involving shade–distance tradeoffs?**
4. State the spatial-resolution question: **How much do accessibility estimates and rankings change when residential origins are aggregated differently?**
5. Separate these questions from a future health-outcome study. Heat-related EMS data may provide context if appropriate data become available; it is not a required dependency of this prototype.
6. Define an analysis scenario, initially a fixed warm-season daytime setting. Later select additional dates/times supported by the data. A weather scenario is not an observed block-level heat measurement.
7. Define the main cost unit. Start with generalized equivalent distance, because the behavioral data describe path lengths. Actual walking minutes should remain a separate output. Conversion to equivalent minutes requires a stated speed assumption.
8. Decide which needs are hard constraints, such as excluding a verified prohibited crossing, and which are modeled penalties. Unknown crossing status should remain unknown rather than being declared accessible.
9. Write a scope statement distinguishing the initial implementation, expanded comparison geography, and any route buffer.
10. Map these deliverables to the course rubric if one is available. Record any requirement that the current plan does not yet cover.

**Deliverable:** `docs/research_specification.md` — planned file.

**Completion gate:** a reader can identify the prediction target, intended use, geographic extent, cost unit, and limits without guessing.

## 6. Phase 2: Consolidate the source inventory and reproducibility setup

**Goal:** prevent incompatible years, units, geographic scales, or source assumptions from entering the analysis unnoticed.

### Steps

1. Review `docs/resources.md`; classify sources as essential now, useful later, or optional.
2. Create a dataset inventory containing source URL, access method, license/reuse notes, acquisition period, retrieval time, geometry/raster type, spatial resolution, CRS, units, coverage, and intended use.
3. Keep raw downloads unchanged. The existing `clean_data.py` creates timestamped snapshots; retain that approach for new sources.
4. Store source identifiers and checksums. Keep transformations in scripts rather than manually editing downloaded files.
5. Select a primary analysis vintage where feasible. If canopy, road, and imagery dates differ, document the mismatch and inspect places that may have changed.
6. Preserve API credentials outside source code if a service requires them. Do not commit tokens.
7. Record package versions. Later test an isolated environment rather than relying only on the current environment's inherited Anaconda packages.
8. Keep file naming consistent: public raw source, standardized output, analytical feature table, model artifact, and presentation output should be distinguishable.

**Deliverables:** dataset inventory and an environment reproduction check.

**Completion gate:** every dataset actually used in a result has a traceable source snapshot and processing path.

## 7. Phase 3: Finish source-specific cleaning and QA

**Goal:** move from valid files to trustworthy inputs without claiming the network is already validated.

### Steps

1. Open `notebooks/02_data_cleaning.ipynb` and review the counts and maps.
2. Inspect the two repaired sidewalk geometries and the flagged duplicate geometries. Distinct parcel records or unit addresses may legitimately share locations; do not merge them solely on geometry.
3. Check missing trail attributes, including crossings and condition fields. Blank means unrecorded, not absent or zero.
4. Preserve the distinction between sidewalk **surface polygons** and trail **centerlines**. Never convert polygon perimeters directly into walking routes.
5. Keep local metric operations in a suitable projected CRS. Current local cleaning uses EPSG:26914 in meters; native Plano service coordinates use State Plane feet. Do not use native length fields as meters without checking their definition.
6. Keep display layers in latitude/longitude where the map library requires it. Reproject; do not merely relabel the CRS.
7. Add record accounting for every new dataset: downloaded, retained, repaired, quarantined, filtered out, and unresolved.
8. For rasters, preserve NoData and valid-value definitions. Check pixel alignment, extent and resolution before calculating statistics.
9. For weather, preserve station IDs, quality flags, units and UTC timestamps; derive local scenario time using **America/Chicago** for Plano.
10. For behavioral data, preserve participant IDs, treatment flags and the distinction between tree shade and building shade. Keep control observations separately identifiable.

**Existing command:**

```bash
.venv/bin/python scripts/clean_data.py
```

**Existing report:** `data/processed/75025_buffer250m/quality_report.md`.

**Completion gate:** no silently dropped records, unresolved required-column failures, or unexplained unit conversions. This gate does not establish crossing validity or actual sidewalk shade.

## 8. Phase 4: Build residential origins and destination nodes

**Goal:** represent meaningful places people start from and want to reach.

### Residential-origin steps

1. Download Census blocks, block groups and tracts intersecting the study area, using consistent geography vintages.
2. Obtain matching population/household information at available scales. Do not assume detailed socioeconomic variables exist at Census-block resolution.
3. Keep GEOIDs and parcel IDs as strings.
4. Identify plausible residential areas using an appropriate land-use/building/address source. Parcel geometry alone does not establish residential use.
5. Start with one or more representative pedestrian access points per inhabited residential block. Use multiple access points when a block is large or physically divided.
6. Connect origins through audited access paths. A straight connector must not cut through a fence, private barrier, water feature, or divided roadway.
7. Select a manageable set of parcel/access-point examples for the high-resolution comparison. Expand only after the workflow works.
8. Assign household/population weights only where the allocation is supported; otherwise present unweighted samples with that limitation.

### Destination steps

1. Build an initial inventory of temples, grocery stores, pharmacies, and the user's other example businesses.
2. Query public OSM/municipal sources and verify entity identity against official facility/business information where available.
3. Keep separate facilities separate, even when they share a shopping center or address.
4. Record destination category, stable ID, name, source date, location, entrance status, and verification status.
5. Verify the nearby temple candidate rather than assuming the closest point is the temple used by the household. Distinguish straight-line proximity from a feasible walking route.
6. Connect a verified entrance to the appropriate side of the pedestrian network.
7. Distinguish a user-selected specific destination from the nearest suitable destination in a category. A preferred temple is not automatically interchangeable with every other temple.

**Deliverables:** residential-origin and destination tables with connector geometry and verification flags.

**Completion gate:** every demonstration origin/destination has an explainable connection or an explicit unresolved/unreachable status.

## 9. Phase 5: Construct and audit the pedestrian graph

**Goal:** create physically plausible walking routes before optimizing environmental costs.

### Steps

1. Retrieve an OSM walking graph for 75025 and sufficient surrounding context. Preserve source tags and a dated snapshot.
2. Overlay that graph with the cleaned Plano sidewalk surfaces and trail lines.
3. Identify where OSM represents sidewalks as separate paths versus street-centerline walking proxies. Record which representation is used; do not portray a roadway centerline as a measured sidewalk location.
4. Audit a small subarea first. Prefer reviewed local corrections over automatically merging all geometries.
5. Add verified municipal trail connections while avoiding duplicate representations of the same physical path.
6. Where needed, evaluate a separate sidewalk-centerline extraction method. Validate its output inside the surface polygons and against visible real-world connections.
7. Represent opposite sides of major roads separately when the available data support that detail.
8. Create crossing links only where physical/legal access is supported. A geometric intersection between lines does not establish a pedestrian crossing, particularly at bridges or different elevations.
9. Preserve direction and access restrictions where relevant. Do not assume every edge is bidirectional merely because walking often is.
10. Assign stable node/edge IDs and calculate metric edge lengths. Remove or explain zero-length artifacts; identify self-loops and duplicated paths for review.
11. Calculate connected components, dangling ends, and disconnected origins/destinations. Do not hide disconnected areas by retaining only the largest component.
12. Generate a review set spanning residential streets, commercial corridors, trails, major intersections, and scope boundaries.
13. Check proposed routes against available imagery and public infrastructure evidence. Keep a table of accepted routes, uncertain crossings, and rejected routes with reasons.
14. Revisit the download buffer if a plausible route needs to leave it.

**Deliverables:** pedestrian graph, source crosswalk, route audit table, and a baseline route map.

**Completion gate:** every route used in the final demonstration has no unresolved critical barrier. Uncertain areas are flagged or excluded from the demonstration; they are not declared safe.

## 10. Phase 6: Create edge-level environmental features

**Goal:** replace neighborhood-level proxies with measurements appropriate to the walking corridor.

### Steps

1. Define a feature schema keyed by edge ID and, where relevant, scenario/date/time.
2. Include physical length, baseline walking time, edge type, source and access status.
3. Extract fine-grained canopy around actual walking geometry using documented corridor widths or sampling points. Run a buffer-width sensitivity check.
4. Store canopy percentage and valid-data coverage separately. The existing block-group canopy layer is context, not independent sidewalk-level evidence.
5. Add surrounding imperviousness from an appropriate raster. Keep its original resolution in the metadata; resampling does not create new spatial detail.
6. If shade geometry is available, calculate sun-exposed length for each scenario. Otherwise label canopy-derived exposure explicitly as a proxy.
7. If modeling shadows, obtain tree/building height information and sun position. Bare-earth elevation alone cannot model tree/building shade. Validate selected predicted shadows against independent imagery or an appropriate reference.
8. Add traffic and roadway context using defensible spatial matching. Preserve road identity, data year, direction, match distance and any frontage-road ambiguity.
9. Add crossing attributes only where supported: crossing type, signal information, roadway context, and uncertainty. Avoid a false numerical precision for unobserved crossing difficulty.
10. Add weather scenarios from suitable stations after checking completeness and QC. A shared station observation is a time-varying context feature, not a block-scale temperature map.
11. Preserve missing-feature flags. Do not equate unknown canopy with full sun or unknown crossings with no crossing burden.
12. Check minimum/maximum values, units, valid coverage, duplicates, and impossible combinations. Store the analytical feature table separately from source geometries.

**Deliverables:** edge-feature table, feature dictionary, coverage map, and missingness report.

**Completion gate:** every feature used in a cost has a documented definition, unit, source, scale, and missing-data policy. Demonstration routes cannot silently rely on missing required inputs.

## 11. Phase 7: Reproduce the behavioral learning baseline

**Goal:** demonstrate genuine learning from public observations before benchmarking more complex models.

### Steps

1. Read the Singapore README, experimental design, paper, and analysis notebook. The existing cleaning pass checks consistency; it does not reproduce the statistical analysis.
2. Confirm the 728 total and 408 sun-present records and their participant counts.
3. Identify the precise model inputs supported by the source: route lengths, sun-exposed lengths, tree/building shade components, treatment and trial information.
4. Reserve participant-grouped training/validation/test partitions before tuning. Save participant split IDs and random seeds.
5. Fit a distance-only choice baseline and document tie handling.
6. Fit an interpretable two-alternative logit/conditional-logit specification for shade versus distance. Distinguish this simplified baseline from the paper's richer hierarchical model; do not call it a full paper reproduction unless it actually is one.
7. Estimate choice-noise/scale consistently with the cost parameterization. Consider whether tree and building shade can be distinguished with the available evidence.
8. Report coefficient uncertainty using an appropriate grouped approach, such as participant-level bootstrap resampling. Do not treat repeated decisions as independent people.
9. Inspect failed predictions and whether performance differs across the experimental task sets.
10. Document transfer limitations: population, climate, route scale, setting and feature coverage differ from Plano.

### Initial deployable cost structure

For edge e:

`cost(e) = shaded_length(e) + (1 + alpha) × sun_exposed_length(e)`

Here alpha represents the additional generalized cost of sun exposure. It is estimated from observations under a specified model, rather than chosen because it produces an attractive map. A nonnegative-alpha restriction is a modeling assumption; disclose it and investigate evidence that conflicts with it. Do not silently alter a fitted coefficient to force the desired story.

This formulation yields additive equivalent-distance costs. It does not learn penalties for traffic, highways, psychiatric conditions, or every form of heat stress from a shade-choice dataset.

**Deliverables:** planned `03_behavioral_baseline.ipynb`, split manifest, model artifact and evaluation table.

**Completion gate:** a saved learned model can predict held-out observations, its target and training population are clear, and its edge-cost interpretation is documented.

## 12. Phase 8: Compare XGBoost, LightGBM and an optional neural model

**Goal:** test whether additional flexibility improves supported predictions, not assume complexity improves validity.

### Steps

1. Use the same underlying observations and participant-grouped partitions for all comparisons.
2. Start with XGBoost and LightGBM choice-prediction experiments using supported route attributes or differences. Do not supply fabricated traffic labels or unavailable Plano outcomes.
3. Check sensitivity to route A/B ordering. Equivalent presentation of the same pair should not create contradictory recommendations. Any swapped/augmented pair must stay in its original participant split.
4. Keep tuning small and documented, given the limited number of participants. Use grouped validation or nested grouped cross-validation as appropriate, preserving a final evaluation that is not repeatedly used for selection.
5. Compare accuracy, log loss, calibration, runtime, and uncertainty. Prediction quality on this dataset is not accuracy for Plano residents.
6. Train a small neural challenger only if it answers a specific question. A shared segment/component cost scorer trained through summed route costs can preserve additivity; a generic route classifier does not automatically do so.
7. Distinguish **prediction benchmarks** from **deployable routing models**. A high-performing XGBoost/LightGBM route classifier may be retained as an analytical benchmark without being usable to price unseen graph edges.
8. To deploy a flexible scorer, demonstrate nonnegative additive edge costs, sensible behavior under edge subdivision, and a defined interpretation on the feature domain actually supported by training.
9. Never split a route-level label into identical independent labels on every edge and claim that those are observed edge-level preferences.
10. Choose the simplest eligible routing model supported by evaluation. Keep the conditional-logit cost as the default if boosted classifiers improve prediction but cannot provide valid edge costs.

**Deliverables:** benchmark notebook, comparison table, eligible deployment decision, model card.

**Completion gate:** model selection reflects validation evidence and routing requirements. If performance differences are small or uncertain, say so. GNNs remain optional future work.

## 13. Phase 9: Integrate learned costs with routing

**Goal:** produce explainable least-friction paths between residential origins and destinations.

### Steps

1. Apply the selected learned shade-cost function to eligible pedestrian edges.
2. Handle verified unavailable connections as graph constraints, not merely very large discomfort penalties.
3. Keep unsupported traffic/crossing penalties as separate named scenarios. Record whether each term is measured, learned, transferred, or assumed.
4. Compare at least distance/time-only routing and learned shade-sensitive routing. Include a declared manual baseline if useful.
5. Initially freeze costs for a fixed scenario during each route calculation. Document this approximation rather than implying the algorithm accounts for sun movement during a long journey.
6. Remember that multiplying all edges by one common weather factor will not change the shortest route. Weather-sensitive route changes need spatially varying exposure interactions supported by the model or explicit scenario assumptions.
7. Calculate route outputs including physical distance, estimated walking time, generalized cost, exposure proxy or sun-exposed length, and crossing information.
8. Record unreachable origins/destinations explicitly. Never drop them from a total and make an inaccessible location look favorable.
9. Confirm that duplicate parallel edges are handled consistently when extracting a displayed route from graph results.
10. If reporting round trips, calculate return routes where direction or scenario differs; do not automatically double a one-way cost.
11. Audit representative routes again after cost integration. Optimization can expose network shortcuts that did not appear in distance-only examples.

**Deliverables:** route-cost table, route geometries, baseline-versus-learned comparisons, and route audit updates.

**Completion gate:** the route selected by the solver matches the documented edge-cost sum and traversal constraints. A longer shaded route should emerge only where supported by actual features and model assumptions; no such result is required in advance.

## 14. Phase 10: Rank residential origins across required destinations

**Goal:** compare locations according to all selected needs rather than proximity to just one facility.

### Steps

1. Let the user choose either specific destinations or acceptable destination categories.
2. For each origin h and category k, calculate:

   `C_k(h) = minimum network cost from h to a suitable destination in category k`.

3. Respect specific-destination choices. Do not replace a selected temple with a different temple merely because it is closer.
4. Calculate the default combined score:

   `A(h) = sum over categories of importance_weight(k) × C_k(h)`.

5. Normalize or document importance weights so scores remain interpretable across comparable queries. Do not compare scores from different selected destination sets as though they measure the same thing.
6. Offer a worst-journey view or feasibility thresholds so one excellent trip cannot conceal an unacceptable trip to another required service.
7. Enforce unavailable categories and user constraints before ranking; show why an origin was excluded.
8. Show category-specific costs alongside the overall score, along with physical travel time and exposure information.
9. Keep rankings about residential areas/access points unless individual homes have actually been classified and connected. Parcel polygons are not verified property listings.
10. Use ties or rank bands when uncertainty makes fine ordering unjustified.

**Deliverables:** residential ranking table, category-level accessibility maps, and explanation records.

**Completion gate:** all required categories influence the recommendation; missing services cannot improve a score; every displayed ranking has an understandable explanation.

## 15. Phase 11: Test spatial resolution, assumptions and transfer

**Goal:** measure how much the results depend on modeling choices.

### Resolution experiment

1. Define a stable set of detailed residential access points or parcel examples.
2. Calculate accessibility at that detailed reference level.
3. Aggregate the same reference results to Census blocks and block groups; optionally tracts. Report the distribution within each area, not only its mean.
4. Separately compare against a centroid-based shortcut. This distinguishes aggregation effects from errors introduced by moving every household to one artificial point.
5. Keep destination categories, weather scenario, graph and friction model fixed across these comparisons.
6. Compare population-weighted results only where population allocation is justified; otherwise keep weighting explicit and limited.
7. Report rank changes, within-area spread, unreachable-origin shares and the locations where aggregation conceals barriers.

### Sensitivity experiment

1. Vary learned shade parameters within supported uncertainty or clearly labeled transfer scenarios.
2. Vary unsupported crossing/traffic penalties separately; do not combine them into a falsely precise confidence interval.
3. Test canopy-buffer widths, missing-feature policies and routing-buffer extent.
4. Compare fixed times/scenarios supported by the environmental inputs. If real time-dependent shade is unavailable, do not animate a canopy proxy as though it were measured moving shade.
5. Examine whether top-ranked locations and selected routes remain stable.
6. Map where conclusions are stable and where they depend heavily on assumptions.

### Validation limits

External observations can validate a model on the source task. Public imagery can help check mapped infrastructure. Sensitivity analysis can assess robustness. None of these alone establishes local preference accuracy or medical safety.

**Deliverables:** resolution comparison, sensitivity figures, error/uncertainty discussion and clear limitations.

**Completion gate:** the report explains which findings survive reasonable changes and which remain uncertain, including cases where the model does not improve on the baseline.

## 16. Phase 12: Build the Python dashboard

**Goal:** make the analysis usable without exposing implementation details that do not help the user decide.

### Steps

1. Build on the existing notebook/map prototype. Select one Python dashboard framework after checking the required map and widget interactions; avoid rebuilding the interface across several frameworks.
2. Add destination category selection and specific-destination selection.
3. Add scenario selection, supported access constraints, and destination-importance controls.
4. Display candidate residential locations or clusters, ranked results, and the routes supporting each result.
5. Allow comparison of ordinary distance/time routing and the learned shade-sensitive model.
6. Add a click-to-explain view: distance, time, exposure information, crossings, data coverage and generalized cost.
7. Show unreachable needs and uncertain connections without suggesting that no data means no problem.
8. Keep physical walking minutes distinct from equivalent cost. A generalized 15-unit threshold is not a literal 15-minute walk.
9. Offer a planner-oriented scenario only after household ranking works: estimate accessibility changes from hypothetical shade or crossing improvements, clearly marking those changes as counterfactual assumptions.
10. Use consistent color scales across comparison maps and show missing coverage separately. Do not exaggerate contrast through per-area scales without clear labeling.
11. Test a complete household query from selected destinations to ranked origins and route explanations.
12. Add export options for a map, ranking table and scenario assumptions. Cache repeated queries where useful.

**Deliverables:** locally runnable dashboard, README commands, demonstration scenario and exported figures.

**Completion gate:** a new user can select needs, interpret rankings and identify the assumptions behind them. Core functionality should not require reading the code.

## 17. Phase 13: Complete civic framing, governance and presentation

**Goal:** make the project assessable as research and civic technology, rather than only a map demonstration.

### Steps

1. Identify affected users and potential institutional stakeholders, including non-driving households, disability/older-adult organizations, planners and infrastructure managers.
2. Explain whose preferences the public training data represent and whose experiences they may miss. Do not infer individual needs from ethnicity, age or diagnosis.
3. Relate the analysis to documented local pedestrian, shade and accessibility priorities without implying city endorsement.
4. Write the theory of change: public data and learned costs → clearer accessibility comparisons → potential household/planning decisions. Treat longer-term benefits as hypotheses, not demonstrated effects.
5. Prepare a data card describing sources, coverage, dates, transformations, licensing notes and known defects.
6. Prepare a model card describing training population, features, target, splits, evaluation, transfer, assumptions and intended use.
7. Describe a maintenance plan: who would update destinations, network access, imagery and model assumptions, and how stale records would be identified.
8. Choose anonymized or public demonstration origins. Obtain any needed permission before exposing identifiable household narratives or routes in public materials.
9. Prepare slides covering problem, stakeholders, scope, data, graph design, GeoAI target, evaluation, accessibility results, spatial resolution, limitations and future work.
10. Include a process diagram showing raw data → cleaning → graph/features → learned costs → routes → residential rankings.
11. Use a case study chosen through documented criteria, showing baseline and shade-sensitive results. Report a null or mixed result honestly if that is what appears.
12. Prepare a backup recording or static figures for the live demonstration, and record the exact data/model version used.
13. Run the project from a clean setup where practical. Verify that notebooks and README commands work and that credentials are not embedded.
14. If creating a GitHub repository, name it EmPath. Check source-data redistribution conditions and personal information before pushing. A repository is useful for reproducibility but is not necessary to finish the local prototype.

**Completion gate:** all findings are traceable, limitations are visible, and a reviewer can reproduce or inspect the demonstrated workflow.

## 18. Fallback decisions

| Problem | Defensible response |
|---|---|
| Sidewalk topology is incomplete | Restrict the demonstration to audited corridors; show gaps and do not claim full-area routing |
| Time-specific shade cannot be modeled | Use a clearly labeled canopy-exposure proxy, evaluate it as a proxy, and narrow environmental claims |
| Singapore learning does not transfer credibly | Present an externally trained behavioral model with transfer scenarios; do not call Plano preferences validated |
| XGBoost/LightGBM improve route classification but lack additive costs | Keep them as prediction benchmarks and deploy the interpretable additive cost model |
| No candidate model improves over distance alone | Report that result and retain the simpler baseline while explaining data/model limits |
| Traffic/crossing preference labels remain unavailable | Use hard exclusions where warranted and disclosed scenario penalties elsewhere |
| EMS microdata cannot be obtained | Remove it from the core workflow; keep health-outcome validation as future work |
| Expanding to three ZCTAs is too expensive | Finish the end-to-end 75025 demonstration and document expansion as a tested or planned extension |
| House-level information is insufficient | Rank blocks/access-point samples rather than claim precise recommendations for individual homes |

Do not substitute fabricated ground truth for missing evidence. Synthetic data may test software behavior, but it cannot establish real-world preference accuracy.

## 19. Suggested working schedule

This is an illustrative eight-week sequence, not a deadline commitment. Data access, network audits and available working hours may change it.

| Week | Main work | Reviewable output |
|---|---|---|
| 1 | Research specification, inventory, cleaning review, Census origins and initial destinations | Clear study specification and usable origin/destination samples |
| 2 | Small-area graph construction and crossing/entrance audit | Plausible distance-only routes in a reviewed subarea |
| 3 | Fine-grained environmental acquisition and edge-feature QA | Feature table with coverage and uncertainty |
| 4 | Singapore baseline reproduction and grouped evaluation | Learned shade–distance model and baseline results |
| 5 | XGBoost/LightGBM comparison; eligible cost deployment; route audits | Honest benchmark and explainable route comparisons |
| 6 | Residential ranking, spatial-resolution and sensitivity experiments | Accessibility maps and stability results |
| 7 | Dashboard and expansion where feasible | End-to-end household query demonstration |
| 8 | Reproducibility, civic framing, report, slides and backup demo | Submission-ready package |

If time is short, prioritize one audited 75025 subarea, the interpretable learned model, baseline comparison and an honest validation section. Do not sacrifice network correctness to add more models or a larger map.

## 20. Immediate next work session

1. Open `EmPath.code-workspace` in VS Code.
2. Open `notebooks/02_data_cleaning.ipynb` and select `Python (EmPath)`.
3. Review the existing cleaning report and geometry figure.
4. Inspect flagged sidewalk/trail/parcel duplicates and record which need further review.
5. Finalize the short research specification and initial fixed analysis scenario.
6. Acquire Census blocks and matched population/household information.
7. Create a small, verified destination table, including temple candidates whose identity and access remain to be confirmed.
8. Choose a small route-audit subarea within 75025.
9. Build the first OSM walking graph and compare it with the cleaned sidewalk surfaces/trails.
10. In the next independent work session, open the Singapore analysis notebook and establish the participant-grouped modeling split.

The next milestone is **one audited origin-to-destination walking route with documented features**, alongside a reproducible behavioral-learning baseline. Model complexity and geographic expansion come after those foundations.

## 21. Final submission package

- [ ] Problem statement, research questions and stakeholder analysis.
- [ ] Geographic scope and heterogeneity rationale.
- [ ] Annotated sources and dataset inventory.
- [ ] Raw-data provenance, scripts and cleaning QA.
- [ ] Residential origins, destinations and verified connectors.
- [ ] Pedestrian graph and route/crossing audit.
- [ ] Edge-feature dictionary and coverage report.
- [ ] Behavioral model, participant-grouped evaluation and uncertainty.
- [ ] XGBoost/LightGBM comparison or documented rationale for deferring an unsupported experiment.
- [ ] Nonnegative additive deployed costs with learned versus assumed terms identified.
- [ ] Baseline and shade-sensitive route/accessibility comparisons.
- [ ] Residential rankings that account for all required destination categories.
- [ ] Spatial-resolution and sensitivity findings.
- [ ] Python dashboard and reproducible run instructions.
- [ ] Civic/policy context, theory of change, privacy, limitations and maintenance notes.
- [ ] Report, slides, process diagram, final figures and backup demo.

## 22. Supporting resources

The detailed annotated guide is in `docs/resources.md`. Begin with:

- Singapore route-choice data/code: https://osf.io/aj4vk/
- Singapore study: https://www.nature.com/articles/s41598-022-06383-5
- CoolWalks dataset: https://zenodo.org/records/11103149
- CoolWalks code: https://github.com/henrik-wolf/CoolWalks
- ASU Cool Routes implementation: https://news.asu.edu/20260610-environment-and-sustainability-new-cool-routes-app-maps-shadiest-routes-your-walk
- Plano GIS sources: https://maps.planogis.org/arcgiswad/rest/services/OpenData
- Census geographies: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- EPA conventional walkability comparison: https://www.epa.gov/smartgrowth/smart-location-mapping

Existing files are explicitly identified as current in this plan. Other suggested notebooks, model artifacts and analytical deliverables are planned work, not completed results.
