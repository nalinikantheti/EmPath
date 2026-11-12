# Prototype and county status

## User-facing prototype
- Public app: https://empathmaps.netlify.app/app.html
- Scoring explanation: https://empathmaps.netlify.app/method.html
- Choose any subset of 19 service categories; map recomputes mean closest-category cost and relative color scale immediately from cached weighted shortest paths.
- Categories include Hindu temples, groceries, pharmacies, gyms, recreation centers, pools, parks, banks and schools. Pool eligibility, gym membership and entrance access remain unverified.
- Added public locations from OSM fitness/bank/sports tags and Plano City Facilities. Config snapshot: `config/additional_category_pois.geojson`. Pool co-location at Oak Point and Carpenter is supported by https://www.plano.gov/recreation-centers-pools . No private backyard pools were inferred as destinations.
- 390 destination candidates; 2,862 reference blocks; 2,804 complete block scores for all categories. Catalog and inputs remain incomplete representations of the world.
- Selection links and CSV exports work. Browser tests covered essential/all/custom/empty selections, county preview and CSV downloads, with no page errors. Desktop/mobile screenshots reviewed.

## Is Path of Resistance complete?
The computational proof of concept is implemented: environmental GeoAI/proxies → nonnegative edge costs → weighted routing → closest POI per selected category → block accessibility → interactive display.

It is not a validated production service. Access points, crossings, destination eligibility, local preference calibration and missing-data uncertainty remain. The equation is an explicitly assumed cost model; the tree segmentation is the pretrained GeoAI component.

## County extension
- Collin County (FIPS 48085), not Cook County.
- Official boundary and all 16,324 2020 Census block polygons downloaded; 17 invalid geometries repaired.
- County is about 18.5 times the four-ZIP pilot's area. Source geometries are not environmental observations.
- Resumable county imagery plan: 8,085 tiles, no county inference run.
- Website county preview shows real county block geography and overlays existing pilot scores; outside-pilot blocks remain unscored.
- Full county weighted network, county POIs/environmental coverage and countywide accessibility remain uncomputed. This is a prepared expansion, not completed county analysis.
- Notebook 22 provides the data status, buffered OSM network acquisition and separate-scope imagery commands. County summarizers/scoring still need county inputs rather than pilot hardcoded paths.

## Sources
Census geography: https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer

Plano facilities: https://maps.planogis.org/arcgiswad/rest/services/OpenData/CityFacilities/FeatureServer

OSM extras: standard POST Overpass query for banks, fitness centers and sports centers; clipped to pilot geometry, excluding explicitly private/no-access features. Raw GET requests were rejected; standard POST worked. No key is required for that API.
