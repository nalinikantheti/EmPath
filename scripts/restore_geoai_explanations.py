"""Reusable gallery section for the newer, aligned GeoAI extraction examples."""
from pathlib import Path
ZIPS=('75025','75024','75023','75074')
def render_geoai_explanations():
 tabs=''.join(f'<button type="button" role="tab" id="geoai-tab-{z}" aria-controls="geoai-panel-{z}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}" data-zip="{z}">{z}</button>' for i,z in enumerate(ZIPS))
 panels=''.join(f'''<figure class="geoai-example" role="tabpanel" id="geoai-panel-{z}" aria-labelledby="geoai-tab-{z}" tabindex="0"{'' if i==0 else ' hidden'}><a href="figures/geoai_sequence_{z}.png" target="_blank" rel="noopener" aria-label="Open full-size GeoAI explanation for {z}"><img src="figures/geoai_sequence_{z}.png" width="2934" height="1099" loading="lazy" alt="{z}: aerial photograph, aligned AI tree-pixel predictions, and walking paths colored by nearby predicted tree cover"></a><figcaption><span>Example area in {z}</span><div><a href="figures/geoai_sequence_{z}.png" target="_blank" rel="noopener">View full size ↗</a><a href="figures/geoai_sequence_{z}.png" download>Download image</a></div></figcaption></figure>''' for i,z in enumerate(ZIPS))
 return f'''<section class="geoai-explanations" id="geoai-explanations" aria-labelledby="geoai-explanations-title"><div class="geoai-explanations-heading"><div><h2 id="geoai-explanations-title">See what GeoAI detected</h2><p>Aerial imagery → predicted trees → tree-adjacent walking paths.</p></div><div class="geoai-example-tabs" role="tablist" aria-label="GeoAI example areas">{tabs}</div></div>{panels}<p class="geoai-example-method">These example figures use 5 m path corridors. Current citywide routing uses 20 m-wide corridors. Tree adjacency is a shade proxy.</p></section><script src="geoai-explanations.js" defer></script>'''
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];page=root/'netlify_site/src/gallery.html';html=page.read_text();marker='<section class="map-notes"' if '<section class="map-notes"' in html else '<div class="gallery-grid">'
 if 'id="geoai-explanations"' not in html:
  if marker not in html:raise SystemExit('Gallery insertion point not found; page unchanged.')
  page.write_text(html.replace(marker,render_geoai_explanations()+marker,1))
 print('Restored newer GeoAI explanations for '+', '.join(ZIPS))
