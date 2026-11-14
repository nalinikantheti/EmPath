# EmPath + PathéResistance — website presentation

**Target: 3 minutes 40 seconds. Hard stop: 4 minutes.**

**Tracks:** Transportation and Mobility · Climate Action and Resilience · GeoAI for Social Good.

Five spoken chapters use four existing website tabs. Chapters 3 and 4 both use Methodology; there is no separate Maps tab. Page 1 and the rest of the website remain unchanged.

## Run of show

| Time | Chapter | Website visual | Takeaway |
|---|---|---|---|
| 0:00–0:40 | 1. Story / problem | [Story](https://empathmaps.netlify.app/) | Non-driving residents face more than a distance problem. |
| 0:40–1:35 | 2. What we built + demo | [Tool](https://empathmaps.netlify.app/app) | Working route and residential-area comparisons. |
| 1:35–2:20 | 3. Data + method | [Method → Data & method](https://empathmaps.netlify.app/method#process) | Public inputs become connected paths, costs and area rankings. |
| 2:20–3:05 | 4. GeoAI + evidence | [GeoAI](https://empathmaps.netlify.app/method#imagery), then [Results](https://empathmaps.netlify.app/method#results) | Image predictions feed the model; computed routes change. |
| 3:05–3:40 | 5. Limits + next steps + close | [Limits](https://empathmaps.netlify.app/method#next-steps), then [Ideas](https://empathmaps.netlify.app/feedback) | Clear limits, a practical validation plan and a community invitation. |

## 1. Story / Problem Statement — final; keep unchanged

- Walking is a human right
- In car-dependent cities like Plano, TX, it doesn’t always feel that way.
- What does living in Plano look like when you don’t have a car?
  - Biking 30 min to gym in the heat story
- We are Nalini and Pramukh, and this is why we built EmPath.

**Delivery:** rehearse this story to 40 seconds. Keep the personal example at the level you already chose; do not add identifiable family health details from the proposal.

## 2. Solution / Tool — 55 seconds

### Refined outline

- **EmPath offers two workflows:** plan a walk; compare residential areas by access to everyday destinations.
- **PathéResistance is the reusable engine used to create EmPath.** It combines a pedestrian network with environmental features and calculates modeled effort costs.
- **Walk planning:** compare a route optimized for walking time with one optimized for environmental effort.
- **Residential comparison:** select categories, find the lowest-cost reachable destination in each, average those trip costs and rank eligible residential blocks.
- Demonstrate one category selection, an area result, and a prepared route comparison. Show the open-source link briefly; do not navigate away to GitHub.

### Suggested narration

> “EmPath turns that question into two working tools: a walking navigator and a residential-area comparison. Underneath is PathéResistance, our reusable open-source engine. For a walk, we compare ordinary travel time with modeled effort from trees, heat and traffic. For an area, choose everyday services—groceries, a pharmacy or a temple. We find the lowest-cost reachable destination in each category and average those trip costs. Lower scores mean lower modeled effort. Here, changing the walking priority changes what the tool recommends. You can inspect the route and the information behind it.”

**Demo actions:** use a rehearsed category preset and a prepared walk to the same destination. Keep the map visible. Do not type a private home address, request GPS permission or configure wandering/social features during the timed presentation. If only one workflow fits, demonstrate residential results and point to the prepared walk comparison.

## 3. Methodology — 45 seconds

### Refined outline

- **Data selection:** paths and places from OpenStreetMap/Geofabrik; 2022 NAIP imagery; summer 2025 Landsat surface temperature; TxDOT road-volume counts; Plano boundaries and Census/ACS area context.
- **Preparation:** harmonize coordinates, categories and geometry; connect reference origins and destinations to the detailed walking graph; record missing connections.
- **Resistance model:** walking time multiplied by a nonnegative environmental penalty. Current coefficients are chosen, not learned from local route preferences.
- **Optimization:** add segment costs; Dijkstra minimizes the total. Average the best trip cost per selected category for area comparisons.
- **Scope:** current Plano municipal analysis plus 3 km of surrounding context; the original four ZIPs were the pilot, not the current full extent.

### Suggested narration

> “We combine mapped paths and destinations with aerial imagery, surface heat, traffic counts and Census geography. We align the data and connect origins and services to the walking network, keeping alternative routes. Each segment starts with walking time; sparse trees, heat and traffic add modeled effort. Dijkstra finds the route with the lowest total. The residential tool averages the best trip in each selected category. We now cover Plano with three kilometers of surrounding context. Our effort settings are explicit assumptions, not preferences learned from Plano walkers.”

**Visual:** point across the four pipeline cards. The input strip names the actual sources. Do not read the equations or open the technical guide during the presentation.

**Correction to the draft:** CDC is background motivation, not an analysis dataset or health-risk layer. NOAA and NLCD were proposed sources; they are not current inputs to the displayed formula. Do not present all proposed datasets as implemented.

## 4. GeoAI application + results — 45 seconds

### Refined outline

- **Image → prediction → measurement:** Restor TCD SegFormer-B0 predicts tree-covered pixels from aerial imagery; measure predicted tree fraction near mapped paths.
- **Why this approach:** imagery provides a spatially detailed, consistent tree feature across many segments. Reuse a pretrained model; do not claim a new architecture or locally trained detector.
- **Evidence:** show the actual aligned image/prediction/path outputs, then the computed benchmark: 12 of 18 route pairs differ from time-only routing; objective checks pass.
- **Novelty:** join image-derived environmental information to routes and destination-aware residential comparisons in a working, inspectable application.
- **Interpretation:** evidence of a functioning pipeline and changed model behavior; not evidence of validated comfort, medical safety or local tree accuracy.

### Suggested narration

> “This is where GeoAI enters. A pretrained tree-detection model turns aerial photographs into predicted tree pixels. We measure their fraction beside each path, which feeds the effort model. The original illustrations use five-meter corridors; current routing uses twenty-meter-wide corridors. Nearby trees indicate potential shade, not shade at a particular hour. In our eighteen-trip benchmark, twelve effort routes differed from time-only routes, and optimization checks passed. That shows the pipeline changes decisions; it does not establish what people prefer. Our contribution is connecting these predictions to everyday route and neighborhood choices.”

**Visual:** spend about 20 seconds on the three-panel 75025 image, then 25 seconds on Results. The optional computed Kroger example shows 41.2 versus 42.1 walking minutes and 71.1 versus 69.0 effort minutes. These are real model outputs, not observed walking experience; both walks remain long. Never substitute the invented teaching examples for measured results.

**Map choice:** the interactive master map remains on Methodology for exploration. Use it only if it replaces part of this chapter; do not add an extra unbudgeted map tour. Keep ranking-change maps as backup evidence.

## 5. Limitations + future development — 35 seconds

### Refined outline

- **Limits:** dated environmental inputs; trees as a shade proxy; chosen effort settings; unverified crossings, entrances and sidewalk continuity; block reference points instead of front doors.
- **Next evidence:** local image/network audits and route-preference observations, with held-out evaluation against walking-time-only routing.
- **Feasibility:** reuse the engine, replace local datasets, refresh inputs and repeat validation city by city. No city partnership or validated adoption impact is claimed.
- **Future ideas:** opt-in walk logging and social features, multilingual support and community-led feature priorities. These are proposals, not completed features.
- Show the existing Ideas page and helpful-vote board without submitting a test message.
- Close on independence, everyday access and community participation.

### Suggested narration

> “This is a working prototype, with clear limits: tree cover is not measured shade, preferences need local validation, and crossings and entrances need audits. Next we want route-choice studies, local checks and expansion city by city. Opt-in walk logging and social features are future ideas. The same work connects transportation access, heat resilience and social good. Our goal is to make everyday independence visible in neighborhood decisions. Try EmPath, share an idea, or build with PathéResistance.”

## How the three tracks connect

- **Transportation and Mobility:** connected pedestrian routing and destination-based access for people who cannot rely on a car.
- **Climate Action and Resilience:** tree and surface-heat features make environmental exposure visible in route comparisons. Reduced heat injury or improved climate outcomes have not been established.
- **GeoAI for Social Good:** image-derived environmental information supports a tool intended for walking-dependent residents and households; the reusable engine invites wider participation. Intended benefit is not yet evaluated impact.

## Judge coverage

| Criterion | Evidence in this presentation |
|---|---|
| Problem formulation & relevance · 5 | Page 1's concrete car-dependence story; who benefits; three explicit track connections. |
| Data selection · 5 | Actual source strip, dates, spatial preparation and boundary context on Page 3. |
| Methodology & GeoAI · 5 | Pretrained model outputs, corridor feature, transparent cost rule, routing and benchmark; distinguish checked behavior from missing validation. |
| Completeness · 5 | Working area and walk workflows, real imagery outputs, deployed application and open-source engine. Avoid implying all work happened during the hackathon unless the team can document that timeline. |
| Impact & feasibility · 5 | Intended users, repeatable public-data workflow, city-by-city checks and local validation plan. |
| Presentation · 3 | Five chapters, prepared demo state, 3:40 target and a self-contained close; no reliance on Q&A. |
| Novelty · 2 | Integration of image-derived environmental features, inspectable effort routing and user-selected residential accessibility; not invention of Dijkstra or the pretrained detector. |

## Rehearsal checklist

1. Load Story, prepared Tool states, Methodology at `#process`, `#imagery`, `#results`, `#next-steps`, and Ideas in advance. All are views of the actual website, not a slide deck.
2. Choose one person to control navigation. Suggested handoff: Nalini tells the story and demos; Pramukh explains the method and GeoAI; Nalini closes. Adjust to your preferences.
3. Rehearse every click. Page 2 ends by 1:35; Page 4 ends by 3:05. Keep 20 seconds of headroom.
4. If a live request is slow, use the preloaded result or the static GeoAI/benchmark outputs already on Methodology. Do not spend the talk troubleshooting.
5. For a three-minute version: story 30s, tool 45s, method 35s, GeoAI/results 40s, close 30s. Cut optional maps and future-feature detail before cutting the AI explanation or validation limits.
6. The technical guide retains graph definitions, all four calculations, the current formula, interactive examples and detailed coverage notes for later reading.

## Claims to keep precise

- Say **predicted nearby tree cover**, not measured shade or a cooler/safe route guarantee.
- Say **modeled effort minutes**, not literal walking duration or probability of illness.
- Say **stated-preference baseline**, not AI-learned human preferences.
- Say **residential blocks / areas**, not ranked individual houses or property listings.
- Say **nearest reachable destination per selected category, averaged**, not a sum of arbitrary chosen individual places or a multi-stop trip.
- Say **12 of 18 computed route pairs changed**, not 67% accuracy or proof that 67% of residents benefit.
- Dijkstra uses the full connected network and alternative paths; do not adopt the roadmap's proposal to discard all but preselected time-shortest paths.
- The benchmark is a small purposive sample. Local preference, shade, accessibility and health outcomes remain unvalidated.
