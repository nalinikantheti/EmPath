# Rowlett Creek Trail · visibility and connectivity audit

Open `output/rowlett_creek_audit/rowlett_creek_trail.html` for a focused comparison.
The full weighted map now also includes a green actual-OSM-edge locator and a **Zoom to Rowlett Creek Trail** button. Toggle the locator off to inspect the underlying friction colors; green indicates identity, not a shade score.

## Findings
- 38 directed original OSM edges are named Rowlett Creek Trail or its connections, representing about 2.576 km of unique named line geometry.
- 13 municipal reference pieces represent about 2.831 km, including north/south connections.
- Only about 0.055 m of the municipal line is more than 10 m from any graph edge in the cached OSM network. This screening tolerance supports presence, not exact equivalence or real-world access validation.
- About 520 m is not near a **named** Rowlett edge, but is near other graph geometry. Trail-name matching alone would therefore understate coverage.
- All 21 named trail nodes belong to the largest weakly connected graph component.
- All four existing provisional origins can reach all 21 named trail nodes on the weighted block-proxy network.
- Strict three-factor costs existed for 10/38 named directed edges. The block-proxy version provides weights for all 38.

## Meaning
This trail was not omitted from the routing network. Previous score missingness, general friction colors and lack of name labels made it difficult to locate. Block-proxy weights smooth trail conditions; they do not measure true shade. Existing local GeoAI canopy predictions remain available for inspection.

## Files
- `scripts/audit_rowlett_creek_trail.py`: reproducible geometry and connectivity audit.
- `scripts/highlight_rowlett_creek.py`: locator injection, reused by the full-map generator.
- `output/rowlett_creek_audit/rowlett_audit.json`: detailed counts and checks.
- `rowlett_osm_edges.gpkg` and `rowlett_official_reference.gpkg`: exact compared sources.

The focused map uses green for named OSM graph geometry, optional purple for the municipal reference, and red dashes for reference geometry outside the 10 m tolerance. No new graph connections were invented. Source: cached Plano TrailCenterlines and original OSM walking extract. Park access, closures, surfaces and crossings still need field/source validation before navigation claims.

Maps are local outputs; the deployed Netlify website is unchanged.
