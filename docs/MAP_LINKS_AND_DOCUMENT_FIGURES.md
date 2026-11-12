# Live EmPath map portal

https://empathmaps.netlify.app/ — scroll to view the maps embedded on the homepage. Public URLs are listed in `docs/MAP_LINKS_COPY_PASTE.txt`.

Full-area GeoAI: `notebooks/14_full_four_zip_geoai.ipynb`; four close-up examples: `notebooks/13_imagery_geoai_and_route_demo.ipynb`.

# EmPath maps and document figures

## Open interactive maps locally
- [Final block environment map](../output/clean_deliverables/combined_environment_map.html)
- [Walking graph and POIs — CARTO version](../output/four_zip_walking_network/walking_scope_map_carto.html)
- [Map links page](../output/document_layers/interactive_map_links.html)

## Figures for Google Docs
- Run `notebooks/10_document_map_layers.ipynb` with Python (EmPath).
- PNG files and captions are saved in `output/document_layers/`.
- [Figure gallery](../output/document_layers/index.html)
- Includes scope, census blocks, canopy, normalized traffic, road AADT, walking network, city reference boundary, network with POIs, and an address-label example.
- NOAA weather is a shared regional scenario, not a separate measured block-temperature layer.

## Put it in Google Docs
1. Insert the relevant PNG using Insert > Image > Upload from computer.
2. Add text such as “Open the interactive EmPath map.”
3. Upload the HTML to Google Drive and share its file link for downloading. This is a file download, not a live web map.
4. For an interactive browser experience, host the HTML on a web server and use that HTTPS URL with Insert > Link (Cmd+K).

Google Docs cannot execute an iframe/interactive HTML map in the document. Local file links are not shared web URLs. No public hosting has been configured. Before public hosting, configure the basemap key for the intended public domain and provider permissions.
