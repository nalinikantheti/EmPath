# Current EmPath status

- Public entry: https://empathmaps.netlify.app/ ; explorer: /app.html ; guide: /guide.html .
- Origin scope: official Plano city boundary, 186.8 km² and 4,402 clipped Census blocks.
- Active walking/environment/destination coverage: city + 3 km, 98,193 nodes and 290,552 directed finite-weight edges.
- GeoAI: 1,524 NAIP tree-prediction tiles, including 823 compatible reused classifications and 701 new predictions. Prediction coverage is not classification accuracy.
- POIs: 1,648 candidate records in 25 categories, including worship and beauty/hair supply. Entrances, access, eligibility and duplicate records remain review items.
- Public comparisons: each selected category must fit a 10/20/30 effort-minute budget, and the origin-specific exit lower bound must exceed that budget. The minimum eligible-origin bound is 40.6 minutes.
- Public default: grocery + pharmacy + park, 20 effort minutes per destination. 79 matched areas; a 30-minute budget gives 535.
- Public locations are Census areas, not verified homes or listings. Optional address lookup selects an area; routes do not start at the exact entered door.
- Advanced unrestricted comparisons remain at /research.html; longer trips can exceed extent certification.
- Population/affordability/demographic context is separate from route weights. Context comparison now uses the public daily-place profile (grocery, pharmacy, park); the research essential benchmark remains temple, grocery, pharmacy.
- Current context density correlation is about 0.039 across 2,301 eligible non-border residential blocks. Earlier -0.068 referred to the prior temple-profile comparison.
- Manual entrances/crossings and independent Plano tree/comfort validation are still pending. Ordinary time and friction rankings remain highly correlated under the bounded multiplier.

See PUBLIC_TOOL_AND_BOUNDARY.md and Notebook 25 for current workflow. Notebook 24 remains the context review; Notebook 23 is the earlier city expansion. Prior 1 km production data is preserved locally under output/plano_city/prior_1km.
