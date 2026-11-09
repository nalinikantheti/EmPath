# EmPath: One-Week GeoAI Hackathon Plan

Prepared November 8, 2026. This is the active delivery plan. The longer PROJECT_ROADMAP.md is a research backlog, not a one-week commitment.

## Confirmed organizer information

The user confirmed on November 8:

- **Plano is approved.** No NYC migration is required.
- **Submission deadline: November 14, 2026.** Exact submission time and upload mechanics have not been specified.
- **Presentation: five minutes.**
- **Award categories:** social impact; data visualization; presentation/storytelling; and an overall award combining the three, as described by the user. Detailed judging weights have not been provided.

Use these confirmed details over the earlier geographic uncertainty and generic eight-week schedule. Aim for a complete submission package on November 13, with November 14 reserved for final checks and submission before the actual cutoff.

## 1. What the supplied photos actually show

The strongest-project slide in IMG_6329 identifies: a specific NYC problem; a defined scope; a user/beneficiary; documented relevant data; a meaningful GeoAI method; a demonstrable result; a validation method, baseline or sanity check; limitations; a practical use pathway; and reproducible documentation when feasible.

IMG_6333 shows a concept-development exercise organized around problem, dataset, spatial link, limitation and AI-assisted application/research question. It is labeled a 15-minute exercise, not a final submission specification.

IMG_6330 lists possible methods, including satellite-image analysis, terrain/land-cover analysis, clustering, multicriteria ranking, predictive classification and scenario overlays. These are examples rather than evidence that every method must be implemented.

IMG_6331 presents possible sources, including Census, OSM, NASA, NOAA and NYC open-data resources. IMG_6332 explains vector/raster data, spatial reference and metadata.

The photos do not establish final upload requirements, presentation length, code-delivery requirements, judging weights or the exact deadline. Do not invent those requirements.

### Geographic eligibility — resolved

Although the photographed slide mentions NYC, the user has confirmed organizer approval for Plano. Continue the existing Plano case study. Do not spend the remaining time changing cities.

## 2. Minimum demonstrable product

**A Python interface that lets a user select three destinations and compare a small set of residential clusters using ordinary walking costs and a learned shade-sensitive cost model.**

If Plano is eligible, build the detailed demonstration in a small audited portion of 75025. Keep the existing three-ZCTA canopy map as background context; it does not require a completed three-ZCTA routing system.

### Suggested scope caps

- One small, connected, auditable pedestrian subnetwork.
- Five to ten residential cluster/access-point examples, rather than every parcel.
- Three destination categories, with approximately one to three verified suitable destinations in each.
- One interpretable learned shade–distance model plus a distance-only baseline.
- One fixed environmental scenario or an explicitly labeled canopy-exposure proxy.
- One source-data quality report, one model-results table and one route audit.
- One locally runnable interface with saved outputs for the presentation.

These are practical planning caps, not organizer requirements or guarantees of statistical sufficiency. Do not force a route change or a ranking reversal if the actual results do not show one.

## 3. What to defer

- Full routing coverage of three ZIP codes.
- Systematic parcel/block/block-group/tract comparison.
- Ranking all houses or integrating property listings.
- New computer-vision training or lidar-based moving-shadow modeling.
- GNNs and extensive neural-network/boosted-tree benchmarking.
- Learning traffic/crossing preferences without appropriate labels.
- EMS requests or health-outcome prediction.
- Real-time weather routing and full route-traversal time dependence.
- Planner counterfactuals, user accounts, and elaborate deployment infrastructure.

Use existing cleaned parcels and address points only where they help establish a few meaningful origins. Do not spend the week processing data that will not support the demonstration.

## 4. The GeoAI component

Use the public Singapore shade–distance choices already downloaded. Train an interpretable two-alternative preference model and evaluate it by holding out participants. Keep repeated observations from one participant together.

The model learns a supported relationship between length and sun exposure. Its output informs an additive cost on the geographic pedestrian network:

`edge cost = shaded length + (1 + learned sun penalty) × exposed length`

Document coefficient/noise-scale assumptions and any parameter restrictions. Compare against distance alone. The local deployment is a transfer experiment, not validation of Plano residents' preferences.

If only canopy is available locally, call the input a canopy-based exposure proxy. Do not label it time-specific shade or measured thermal stress. Be explicit that applying a sun-exposure coefficient to a canopy proxy adds another transfer/measurement assumption.

XGBoost is a stretch benchmark only after the baseline, held-out evaluation and routing pipeline work. A route classifier's output is not automatically an additive edge cost, so do not deploy it as one without establishing that connection. The supplied slides do not establish a requirement for XGBoost or a neural network.

Check the organizers' actual definition of a meaningful GeoAI method if a separate rubric exists. The project should demonstrate learning, geographic features and resulting network decisions clearly, rather than rely on an AI label.

## 5. Day-by-day work plan

Use the calendar schedule below. The day-by-day task lists that follow describe work packages; compress them to meet the confirmed November 14 deadline.

| Date | Priority | Required end-of-day outcome |
|---|---|---|
| Nov 8 | Freeze the small Plano demonstration; prepare the learned baseline | Fixed scope, selected origin/destination candidates, model evaluation setup |
| Nov 9 | Build and audit the pedestrian network | Plausible baseline routes and verified demonstration connectors |
| Nov 10 | Finish the environmental feature approach | Documented edge features, coverage, and proxy limitations |
| Nov 11 | Integrate learned costs and residential ranking | One end-to-end comparison, saved results and essential validation |
| Nov 12 | Finish the interface and principal figures | Feature freeze; usable prototype and exported visual evidence |
| Nov 13 | Assemble, time and rehearse the five-minute story | Complete submission package, backup demo and rehearsed talk |
| Nov 14 | Final checks and submission | Submit before the actual cutoff; avoid new features |

If a dependency slips, reduce the number of origins or the network extent. Preserve November 13 for communication and rehearsal rather than adding model families.

### Day 1 — Scope, eligibility and learning baseline

1. Confirm geography eligibility and actual submission format/deadline.
2. Write the project in five sentences: problem, user, study area, method, intended decision.
3. Freeze the demonstration scope and selected destinations.
4. Review the existing cleaned files rather than redoing the data pipeline.
5. Inspect Singapore variables and save participant-grouped evaluation partitions.
6. Fit and save the first interpretable choice model and distance-only comparison.
7. Start a running slide outline and limitations list.

**End-of-day output:** scope statement, confirmed deliverable checklist, reproducible first model and preliminary results table. If model fitting is blocked, diagnose it before adding another model family.

### Day 2 — Audited pedestrian subnetwork

1. Obtain the walking network for the confirmed small study area and context.
2. Compare its paths with municipal sidewalk/trail evidence.
3. Verify destination identities, entrances and candidate residential access points.
4. Review crossings, disconnected components and obvious shortcuts.
5. Restrict demonstration routes to the part that can be audited reliably.
6. Generate distance-only routes and save graph/route files.

**End-of-day output:** reproducible distance routes between the chosen origins and destinations, with uncertain connections identified.

**Scope stop:** if the graph is still unreliable, shrink the subarea or number of origins. Do not start large-area network reconstruction.

### Day 3 — Environmental feature extraction

1. Acquire one suitable fine-grained canopy source for the small study area, preferably by a subset/window workflow.
2. Calculate a consistent corridor-level canopy feature and valid coverage for edges.
3. Verify source units, NoData handling, resolution and date.
4. Inspect several low-/medium-/high-canopy corridors visually.
5. Use the existing block-group canopy only as context if finer data fail; do not portray it as independent street-scale measurement.
6. Attach source and uncertainty flags to the feature table.

**End-of-day output:** edge features plus a coverage/limitations map.

**Fallback:** if defensible local environmental features cannot be obtained, reduce the environmental claim and demonstrate the learned routing method on a suitable public reference network, with the local canopy map presented separately. Label the two demonstrations distinctly rather than implying a completed local model.

### Day 4 — Weighted routes and residential comparisons

1. Apply the learned cost to supported edge inputs.
2. Keep verified inaccessible connections excluded; keep any assumed crossing penalties in a separate scenario.
3. Calculate distance-only and shade-sensitive routes.
4. Sum category-specific minimum costs for each residential example. Do not take the minimum across all categories and ignore the others.
5. Preserve unreachable destination categories and show why an origin is not ranked.
6. Save physical distance/time separately from generalized cost.
7. Inspect selected routes again for unintended network shortcuts.

**End-of-day output:** a working end-to-end query, ranking table and route comparison. A ranking that stays the same is a valid outcome.

### Day 5 — Interface and essential validation

1. Build the simplest Python interface around precomputed/cached results where useful.
2. Add destination selection, origin rankings and route viewing.
3. Display a short explanation for each result: distance, exposure proxy, cost, constraints and data coverage.
4. Finish grouped model evaluation and report uncertainty appropriately for the small source sample.
5. Test several sun-penalty values and record whether routes/rankings change.
6. Check one complete user journey and every final demonstration route.

**End-of-day output:** a runnable prototype plus a compact validation table.

**Stretch only:** try a small XGBoost preference benchmark if the core product is already stable. Do not trade a working demo for additional model complexity.

### Day 6 — Story, documentation and rehearsal

1. Assemble presentation material around problem → data → spatial link → learning → routes → household comparison → evidence → limitations.
2. Export one scope map, one cleaned-data/feature map, one route comparison, one model-results table and one ranking example.
3. Write a plain-language paragraph on what is learned versus transferred versus assumed.
4. Document run commands, sources, metadata and known gaps.
5. Prepare screenshots or a short recording as a backup; confirm organizer format before choosing a final duration.
6. Rehearse the demo with a fixed scenario and reset procedure.

**End-of-day output:** a complete draft submission and backup demonstration.

### Day 7 — Freeze, check and submit

1. Freeze features. Fix only failures that affect correctness or the demonstration.
2. Restart and run the notebook/interface from documented commands.
3. Check every map label, legend, unit, citation and numerical claim.
4. Verify that the demo does not depend on an untested API response during presentation.
5. Check files/links and remove secrets or unintended identifying personal details from shared outputs.
6. Practice the presentation once at the required length.
7. Submit in the confirmed format with a time buffer before the actual deadline.

**End-of-day output:** submitted, inspectable proof of concept with limitations and reproducible evidence.

## 6. Match the slide guidance to concrete evidence

| Visible guidance | EmPath evidence |
|---|---|
| Specific NYC problem | Organizer-approved Plano exception, confirmed by the user; retain the specific local problem |
| Defined scope | Small study boundary and explicit origin/destination sample |
| Identifiable beneficiary | Non-driving household comparing everyday destination access |
| Documented relevant data | Existing inventory, manifests and quality report |
| Meaningful GeoAI method | Learned shade–distance preference model applied to geographic route costs, with assumptions exposed |
| Demonstrable result | Select destinations → compare residential origins → inspect supporting routes |
| Validation/baseline/sanity check | Participant-held-out choice metrics, distance-only baseline, audited routes and parameter sensitivity |
| Limitations | External preferences, canopy proxy, network uncertainty and limited spatial/sample coverage |
| Practical use pathway | Household decision support and a clear explanation of each result |
| Reproducibility where feasible | Python code, cached snapshots, run commands, saved model and outputs |

## 7. Five-minute presentation plan

The duration is confirmed; the following slide count and timing are recommendations. Rehearse a roughly 4:40 talk so transitions or a slow demo do not push it over five minutes.

| Time | Suggested visual | Message |
|---|---|---|
| 0:00–0:40 | One concrete walking-access example and a simple map | A nearby destination can still be burdensome to reach without a car. Establish the beneficiary and personal motivation without disclosing unnecessary medical details |
| 0:40–1:10 | Small Plano study area with origins and destinations | Explain exactly what the prototype compares and its limited geography |
| 1:10–1:55 | One pipeline graphic and a clear baseline/model comparison | Explain what the model learns from public observations, how geographic features become route costs, and which assumptions remain |
| 1:55–3:15 | Main route map and residential comparison | Demonstrate one household query. Show physical distance/time separately from generalized cost. Display only results actually observed |
| 3:15–4:00 | Compact validation figure/table | Show held-out behavioral performance, route checks and one sensitivity result. Distinguish external-data validation from local preference accuracy |
| 4:00–4:40 | Impact/use case, limits and next step | Explain the practical decision supported, the main limitation, and what would strengthen the tool |
| 4:40–5:00 | Timing buffer | Absorb transitions; do not add another feature explanation |

### Award alignment

- **Social impact:** identify one specific non-driving household need, show the decision the tool supports, and explain why distance alone can miss pedestrian burdens. Do not claim reduced illness or validated safety.
- **Data visualization:** use a legible route comparison, consistent scales, clearly labeled origins/destinations and explicit missing data. Show the user what changes and why, with physical and generalized costs distinguished.
- **Presentation/storytelling:** follow one household question from motivation to an inspectable result. Explain the GeoAI in plain language and avoid a long list of libraries.
- **Overall:** connect the same question, evidence, visualization and practical use throughout. No separate extra feature is needed for this award.

Use the same fixed demonstration query in rehearsals. Have a saved image or short recording ready if the live interface stalls. Neither a specific video length nor a code-upload requirement has been confirmed.

The strongest honest claim is a working, evaluated method for exploring how shade-sensitive costs affect destination accessibility. Do not claim comprehensive health-risk prediction, locally validated vulnerable-user preferences, or a medically safe housing recommendation.

## 8. Definition of done

- [x] Plano geographic eligibility is confirmed by the user.
- [x] November 14 deadline and five-minute presentation duration are confirmed.
- [ ] Exact deadline time and submission mechanics are recorded when available.
- [ ] One coherent public-data workflow runs end to end.
- [ ] A learned model and a distance-only baseline have saved evaluation results.
- [ ] The final demonstration network and connectors have been reviewed.
- [ ] Environmental data and proxy assumptions are visible.
- [ ] All required destination categories contribute to the residential comparison.
- [ ] Unreachable needs and uncertainty remain visible.
- [ ] The Python prototype works from documented commands.
- [ ] Presentation and backup outputs are complete.
- [ ] Sources, limitations and future work are documented.

Finish this checklist before adding geographic coverage, model families or extra dashboard features.
