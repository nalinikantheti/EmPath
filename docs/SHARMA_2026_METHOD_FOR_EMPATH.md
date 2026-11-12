# How Sharma et al. (2026) informs EmPath

Source: *Mobility and urban form effects on air quality in New York City*. DOI: https://doi.org/10.1080/14786451.2026.2665968. Reviewed the supplied paper, especially sections 3, 3.3, 3.4.6 and 5.5.

## Use directly as methodological inspiration
- Put indicators on a common scale, align their directions, and combine them transparently.
- Section 3.4.6 (printed p. 12; PDF p. 13) uses min–max normalization and the arithmetic mean of five indicators. This is an equal-weight composite index, not AI-estimated preference weights.
- Keep area-level indices and network routing as related but distinct outputs.
- Compare alternative priority scenarios; the paper's routing example uses ten origin–destination pairs as proof of concept rather than citywide behavioral validation.

## Adapt for EmPath
- Name the result a **provisional walking-friction index**: higher means less potential canopy protection and/or more nearby traffic.
- Current 50/50 index is consistent with the paper's general equal-weight approach, but is not an exact replication: EmPath uses physical canopy percentage and a City-of-Plano traffic CDF index rather than min–max scaling of the paper's five indicators.
- Compare 25/75 and 75/25 canopy/traffic scenarios. These remain assumptions, not coefficients estimated from Plano respondents.
- NOAA summer-afternoon weather is shared regional context. It cannot distinguish blocks. Do not invent a block-level heat layer or count canopy deficit twice as both canopy and heat.
- Add genuinely independent variables only when their meaning, coverage and direction are established.

## Do not copy without modification
- The paper's edge cost is a weighted sum of z-scored time and emissions plus a fixed positive shift. A constant per edge introduces an edge-count preference: splitting the same physical path into more edges changes its total cost. For EmPath, prefer a nonnegative distance/time multiplied by an explicit burden term, plus real crossing costs if supported.
- An arbitrary fixed shift does not guarantee positivity for every possible z-score. Check actual edge costs.
- Z-scores are not inherently robust to outliers, despite that characterization in the text.
- The paper's equal weights are still a modeling choice; equal ranges do not prove equal effects on perceived comfort.

## What the paper does not supply
- Plano heat/traffic/shade preference training labels.
- AI-derived indicator weights or imagery segmentation in its described index method.
- Validation of subjective pedestrian discomfort. Section 5.5 explicitly acknowledges that perceived safety, sidewalk quality and pedestrian comfort are not captured.

## Keep the prototype simple
1. Use local planning feedback to justify factors.
2. Use a pretrained GeoAI model to extract a relevant imagery feature, documenting its actual demonstration coverage and errors.
3. Combine normalized factors with declared scenario weights.
4. Compare block rankings and a small set of routes across scenarios.
5. Describe the result as an exploratory decision-support index, not a validated measure of an individual's walking experience.
