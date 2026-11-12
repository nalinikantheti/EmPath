# Deploy EmPath from GitHub to Netlify

The repository is prepared for Netlify Git integration. This is separate from Netlify Drop.

## One-time setup
1. Commit and push `netlify.toml`, `netlify_site/src/`, `netlify_site/package.json`, and `scripts/build_netlify_site.mjs` to the GitHub repository. They are currently local changes; no push or deployment has been performed.
2. In Netlify choose **Add new project → Import an existing project → GitHub**, then select EmPath.
3. Netlify reads these settings from `netlify.toml`:
   - Base directory: `netlify_site`
   - Build command: `node ../scripts/build_netlify_site.mjs`
   - Publish directory: `netlify_site/dist` relative to the repository root (`dist` relative to the base).
4. Add environment variable **CARTO_BASEMAP_API_KEY**, using your existing basemap key. Do not paste the key into source code. Its scope must include **Functions**. The key stays in the server function environment and is not written into published HTML. Keep Netlify secret scanning enabled.
5. Deploy. Share the actual HTTPS URL Netlify gives you; no public URL exists yet.

The homepage lives in `netlify_site/src/index.html`. Plain HTML is sufficient. No JSX, Python/GIS installation, model inference or Node dependencies are needed for the website build. The maps use a small Netlify function to fetch CARTO tiles without exposing the key.

## Update maps
Run the relevant Python notebook first, then:

```
.venv/bin/python scripts/prepare_netlify_assets.py
node scripts/build_netlify_site.mjs
```

Commit/push the refreshed `netlify_site/src/` files. Netlify rebuilds after a push. Do not commit `.env` or `netlify_site/dist/`. Source snapshots contain a placeholder; the build replaces the tile URL with the same-origin basemap function URL. It never substitutes a key into HTML.

The GeoAI source snapshot currently reflects the four demonstration tiles. Replace it with a clearly labeled full-area product only after full-area processing and coverage checks complete.

## Use the website in Google Sites or Google Docs
Use the real hosted URL as a normal link in Google Docs. In Google Sites, choose Insert → Embed → By URL and paste the desired map URL. Do not paste the entire map source into Google Sites.

References:
- https://docs.netlify.com/build/configure-builds/file-based-configuration/
- https://docs.netlify.com/build/configure-builds/environment-variables/
