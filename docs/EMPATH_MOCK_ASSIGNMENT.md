# EmPath: build a GeoAI pedestrian-accessibility prototype

## Your assignment

Build a Python-based prototype that helps people who cannot rely on a car compare residential locations by walking access to a temple, grocery store and pharmacy. Investigate how environmental walking costs change the result compared with distance alone.

**Study area:** 75025, 75024, 75023 and 75074. All four remain in scope. Use Census ZCTA boundaries as reproducible approximations of postal ZIP areas.

**Deadline:** November 14, 2026. **Presentation:** five minutes. **Preparation budget:** nine focused hours, followed by hackathon work as available. The estimates below divide those nine hours; they are time boxes, not promises that every technical dependency can be completed in that time.

This is a personal mock assignment inspired by your course briefs, not a replacement for their requirements or a statement of official hackathon rules. Their semester deadlines, word counts, legal-source quotas and presentation lengths are not imported here.

## What you will hand in

1. A Python prototype or reproducible interactive map with real computed results.
2. A short project notebook or methods note containing sources, cleaning decisions, model definition, evaluation and limitations. Reuse tables and screenshots rather than writing a separate long report.
3. A five-minute presentation with a backup recording or screenshots.
4. Code, dependency information and clear run instructions.

## How to work

Complete one assignment at a time. Each has a task, a deliverable and a stopping rule. Save the result before moving on. Record unfinished work honestly. A screenshot of a broken route or an unsuccessful model is evidence to diagnose, not a completed analysis.

### Assignment 1 — State the question (15 minutes)

**Task:** Write five sentences: the problem, affected users, the four-ZCTA study area, the decision the tool supports, and the comparison you will test.

Suggested research question: “How do environmental walking costs change residential access to temples, groceries and pharmacies compared with shortest-distance routing across four Plano ZIP areas?”

**Hand in:** one short project brief.

**Done when:** someone can explain what your tool helps a household decide. Scope selection is already complete; do not repeat it.

### Assignment 2 — Check your ingredients (45 minutes)

**Task:** Use the existing coverage audit. Inventory sources for walking geometry, origins, destinations, environmental features and behavioral training observations. For each, record source URL, date, geographic coverage, unit, intended use and limitation. Retrieve missing walking coverage across all four areas; if retrieval runs longer, keep the coverage table accurate and continue independent documentation.

**Hand in:** a source table and four-area coverage checklist.

**Done when:** every area is explicitly marked complete, partial or missing for each required input. Current saved walking data fully covers only 75025; online city features exist in all four areas.

### Assignment 3 — Make the data usable (60 minutes)

**Task:** Reuse the existing cleaning script for the expanded scope. Preserve raw snapshots. Standardize coordinate systems, check geometry and IDs, flag duplicates and preserve missing values. Check destination categories and residential origin definitions. Do not assume every parcel is residential or every address is an entrance.

**Hand in:** cleaned spatial files and a before/after quality table, broken out by ZCTA.

**Done when:** the files load, their coverage is documented, and unresolved issues are listed. Do not call data complete simply because a download succeeded.

### Assignment 4 — Build the walking skeleton (90 minutes)

**Task:** Build a pedestrian network across the four-area scope with surrounding context. A reusable OSM walking network can be a starting point. Inspect it using the city's sidewalk and trail layers. Attach residential origins and destinations at plausible pedestrian access points. Check disconnected components and sample crossings in every ZCTA.

**Hand in:** one saved graph, an origin/destination layer, a map and a connectivity summary.

**Done when:** sample origins in each area either have plausible routes or an explicitly documented reason for being unreachable. Sidewalk polygons are not automatically routing edges. Never join every pair of walking nodes with a straight line.

### Assignment 5 — Describe each edge (45 minutes)

**Task:** Add length and the environmental features your actual inputs support. For example, a canopy statistic can be an environmental proxy, but it is not time-specific sidewalk shade. Record feature units, missingness and provenance. Add crossing or traffic attributes only when supported by evidence.

**Hand in:** an edge-feature table and small data dictionary.

**Done when:** you can point to an edge and explain what is measured, estimated or unknown.

### Assignment 6 — Train one defensible AI model (90 minutes)

**Task:** First write “My model predicts ___ from ___ using labels from ___.” Use the downloaded public Singapore observations to investigate the shade–distance trade-off. Check the study README and alternative definitions before fitting. Start with a simple shared-parameter route-choice model; compare one XGBoost or LightGBM model only if time and labels permit. Split by participant, not randomly by observation.

**Hand in:** a training script/notebook, saved model or coefficients, baseline comparison and model card naming the training population, target and limitations.

**Done when:** the target is observed rather than a score you invented, and evaluation uses held-out participants. If fitting is blocked, record the blocker; a manually chosen penalty does not satisfy this AI deliverable.

**Important:** a whole-route preference classifier does not automatically produce additive edge costs. A shared additive choice model can estimate a shade–distance trade-off if the observations support it. Features absent from training data, such as traffic or highway crossings, cannot receive supposedly learned behavioral weights. If only canopy proxies are available in Plano, transferring a sunlight coefficient to them is an additional assumption to disclose.

### Assignment 7 — Calculate resistance and accessibility (45 minutes)

**Task:** Define nonnegative edge costs with explicit units and separate learned quantities from scenario assumptions. Compute both shortest-distance and environmental-cost routes. For each residential origin, find the lowest-cost reachable destination in each required category. Combine all three category costs using an explicit rule, such as a weighted sum or worst-journey score. Preserve unreachable results.

**Hand in:** weighted graph, route outputs and a residential accessibility table.

**Done when:** all three destination categories affect the ranking and you can explain every term in the cost. Do not take the minimum across the three categories: that would reward access to only one service.

### Assignment 8 — Check whether it works (45 minutes)

**Task:** Evaluate three separate things: held-out behavioral prediction, physical plausibility of sample routes across all four areas, and ranking sensitivity to uncertain penalties. Compare route length, available exposure proxies and rank changes against distance-only results.

**Hand in:** one results table, inspected route examples and three limitations.

**Done when:** you distinguish predictive performance on Singapore observations from unvalidated preference transfer to Plano. Sensitivity is not proof of local accuracy. If routing fails, diagnose the connections before polishing the interface.

### Assignment 9 — Show the result (45 minutes)

**Task:** Make one clear map interface with the four-area boundary, origins, destinations, selected routes and an explanation panel. Offer distance-only and environmental-cost comparison. Show missing information and assumptions. Use a clearly labeled sample of residential origins if exhaustive computation is unfinished; keep the study boundary intact.

**Hand in:** a runnable dashboard or interactive map and one illustrative comparison.

**Done when:** someone can answer “Which location ranks better, and why?” from the interface. A mockup must be labeled as a mockup; do not present it as computed evidence.

### Assignment 10 — Tell the story and package it (60 minutes)

**Task:** Prepare roughly five slides: problem/user; data and four-area scope; graph and GeoAI; demonstration and result; limitations and next steps. Keep sources in a reference slide or linked document. Rehearse to five minutes. Save a backup recording or screenshots and verify run instructions from a fresh session.

**Hand in:** presentation, backup and reproducible project folder.

**Done when:** you can demonstrate one real finding without depending on a live download. Include one sentence about maintenance responsibility and one about appropriate use. Environmental accessibility does not establish medical suitability or independent navigation safety.

## Your self-check rubric (not an official judging rubric)

| Area | Points | Evidence |
|---|---:|---|
| Civic purpose and user story | 20 | A clear household decision and plausible public value |
| Data and network quality | 25 | Four-area coverage accounting, provenance and route checks |
| Meaningful GeoAI | 20 | Observed labels, defined target, held-out evaluation, honest transfer limitations |
| Analysis and visualization | 20 | Distance baseline, environmental comparison, explainable residential ranking |
| Communication and reproducibility | 15 | Five-minute story, sources, runnable code and backup |

## When time runs short

Keep the four-ZCTA study area. Reduce the number of residential origins shown, the number of scenarios and the number of models. Use one documented environmental feature well before adding several weak ones. Cache results. Keep missing coverage visible. Do not replace an incomplete learned model with a scenario and call it trained AI.

## Your immediate task

Assignment 1 is mostly decided. Begin Assignment 2 with the existing coverage audit: retrieve and clean walking coverage for 75023, 75024, 75025 and 75074. Your next checkpoint is a four-row coverage table plus a map of the downloaded walking features.
