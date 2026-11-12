# Plano evidence and the walking-friction index

## What public local evidence supports

| Source | Relevant evidence | How EmPath can use it | What it cannot establish |
|---|---|---|---|
| City of Plano, June 2023 draft Parks, Recreation, Trails & Open Space Master Plan, printed p. 48 | Summarizes public interest in safer park walking paths, sidewalk/trail connections, and pavilions/shade structures. Reports 93% support for improved neighborhood-to-nature-preserve trail connections in the virtual engagement results. | Supports including pedestrian continuity and potential shade protection. | Exact heat-versus-traffic coefficients, walking-route choices, or preferences specific to the four ZIPs. Park users are not identical to all pedestrians. |
| Plano Comprehensive Plan, Virtual Tour Survey Results and Analysis, Oct. 1, 2020, p. 3 | Summarizes requested improvements including shade/less parking, landscaping, multimodal infrastructure and safer crossings. | Supports factor selection and checks against local planning priorities. | Representative resident preferences; this was a committee/site-review exercise, not a ZIP-level pedestrian choice experiment. Mention counts are not utility coefficients. |
| Douglass Community neighborhood-plan survey instrument, 2002 resolution exhibit | Asks about walking comfort, sidewalks, crossings and traffic calming. | Useful example questions and local policy context. | The instrument alone supplies no completed responses, model-training labels or numerical weights; geographic coverage must be verified separately. |

Sources:
- https://plano.novusagenda.com/agendapublic/AttachmentViewer.ashx?AttachmentID=17926&ItemID=8401
- https://www.planocompplan.org/DocumentCenter/View/4044/Memo-Virtual-Tour-Survey-Results-and-Analysis---October-1-2020?bidId=
- https://content.civicplus.com/api/assets/ed16745e-081c-4cec-a6a2-3a9e799f593c

## Recommended prototype interpretation

**Provisional walking-friction index**, not validated perceived comfort or safety. The current map combines canopy deficit and nearby road traffic with explicit 50/50 scenario weights. Compare 25/75 and 75/25 cases to show how much those assumptions affect block rankings. Local evidence justifies relevant themes; it does not determine these numerical weights.

- Traffic AADT is vehicles/day, not traffic congestion or population density. Do not double-count overlapping traffic indicators.
- Regional NOAA summer-afternoon weather is shared context, not block-level heat. It cannot create spatial differences by normalization.
- Canopy deficit is an imperfect proxy for potential heat protection; adding both canopy deficit and an identical heat proxy would double-count the same information.
- Distance belongs in route costs. Block environmental scores do not measure destination accessibility without network distances.
- Missing data stay unknown, not zero friction.

## Where GeoAI contributes

The imagery notebook applies a real pretrained tree-segmentation model to georeferenced imagery and measures predictions near walking segments. GIS/statistics then aggregate features and compute an explicit index. Qualitative comments could be organized into geolocated themes with AI-assisted text analysis, but text classification does not automatically learn valid heat/traffic trade-offs. Suitable route preferences or comfort ratings with matched features are needed to estimate those weights empirically.

No reusable, ZIP-specific pedestrian preference training dataset for all four areas was verified in this search. This is a search finding, not a claim that such data do not exist. The already fitted Singapore model supplies a transferable sun/distance scenario, not a Plano traffic/heat preference model.
