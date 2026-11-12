# Deploy EmPath from GitHub to Netlify

The repository is prepared for Netlify Git integration. This is separate from Netlify Drop.

## One-time setup
1. The website is pushed on **codex/netlify-static**: https://github.com/nalinikantheti/EmPath/tree/codex/netlify-static . Use this branch for Netlify production, rather than the analysis branch containing oversized generated GIS files.
2. Connect the EmPath repository, then set **Project configuration → Developer settings → Continuous deployment → Branches and deploy contexts → Configure → Production branch** to `codex/netlify-static`. Dashboard versions may label Developer settings as Build & deploy.
3. Netlify reads these settings from `netlify.toml`:
   - Base directory: `netlify_site`
   - Build command: `node ../scripts/build_netlify_site.mjs`
   - Publish directory: **`dist`** when the base is `netlify_site`. The resolved repository-root path is `netlify_site/dist`.
4. Add environment variable **CARTO_BASEMAP_API_KEY**, using your existing basemap key. Do not paste the key into source code. Its scope must include **Functions**. The key stays in the server function environment and is not written into published HTML. Keep Netlify secret scanning enabled.
5. Deploy. The current website is https://empathmaps.netlify.app/ . The homepage embeds maps as they scroll into view and provides static GeoAI previews.

The homepage lives in `netlify_site/src/index.html`. Plain HTML is sufficient. No JSX, Python/GIS installation, model inference or Node dependencies are needed for the website build. The maps use a small Netlify function to fetch CARTO tiles without exposing the key.

## Update maps
Run the relevant Python notebook first, then:

```
.venv/bin/python scripts/prepare_netlify_assets.py
node scripts/build_netlify_site.mjs
```

Update the refreshed source snapshots on **codex/netlify-static**. Netlify rebuilds after a push to that production branch. Do not commit `.env` or `netlify_site/dist/`. Source snapshots contain a placeholder; the build replaces the tile URL with the same-origin basemap function URL. It never substitutes a key into HTML.

The site includes both the complete four-ZIP GeoAI layer and the four close-up imagery examples. Full-area processing completed 505 tiles with valid source pixels across 100% of each ZIP at the analysis grid. This measures data coverage, not local prediction accuracy.

## Use the website in Google Sites or Google Docs
Use the real hosted URL as a normal link in Google Docs. In Google Sites, choose Insert → Embed → By URL and paste the desired map URL. Do not paste the entire map source into Google Sites.

References:
- https://docs.netlify.com/build/configure-builds/file-based-configuration/
- https://docs.netlify.com/build/configure-builds/environment-variables/
