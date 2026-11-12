"""Build a standalone gallery of all current static map layers and GeoAI sequences."""
from pathlib import Path
import json,html,shutil
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'netlify_site/src'
def main():
 figures=DEST/'figures';figures.mkdir(parents=True,exist_ok=True)
 groups=[('Plano city · current analysis',ROOT/'output/plano_city/accessibility' if (ROOT/'output/plano_city/accessibility/figure_captions.json').exists() else ROOT/'output/block_accessibility','figure_captions.json'),('Archived four-ZIP environmental proxies and Landsat heat',ROOT/'output/landsat_heat','figure_captions.json'),('Archived four-ZIP GeoAI maps',ROOT/'output/geoai_full_scope', 'figure_captions.json'),('Archived four-ZIP environment and network layers',ROOT/'output/document_layers','captions.json'),('GeoAI explained — one example per ZIP',ROOT/'output/vegetation_geoai','geoai_sequence_captions.json')]
 if (ROOT/'output/plano_city/social/figure_captions.json').exists():groups.insert(1,('Plano city · population, affordability and demographics',ROOT/'output/plano_city/social','figure_captions.json'))
 sections=[];count=0
 for title,folder,manifest in groups:
  rows=json.loads((folder/manifest).read_text());cards=[]
  for row in rows:
   image=row['image'];shutil.copy2(folder/image,figures/image);count+=1
   heading=row.get('title',image.replace('_',' ').replace('.png',''))
   if image in ['full_geoai_walking_friction.png','10_provisional_walking_friction.png','three_factor_walking_friction.png']:heading='Earlier environmental proxy — '+heading
   cards.append(f'<figure><h3>{html.escape(heading)}</h3><a href="figures/{image}" target="_blank" rel="noopener"><img src="figures/{image}" alt="{html.escape(heading,quote=True)}" loading="lazy"></a><figcaption>{html.escape(row["caption"])}</figcaption><a class="download" href="figures/{image}" download>Download PNG</a></figure>')
  sections.append('<section><h2>'+html.escape(title)+'</h2>'+''.join(cards)+'</section>')
 page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EmPath · Map Gallery</title><style>body{margin:0;background:#f3f5f0;color:#183c35;font:16px/1.65 system-ui,sans-serif}main{max-width:1150px;margin:auto;padding:35px 22px}nav{display:flex;gap:20px;margin-bottom:25px}a{color:#125b46}h1{font:normal 48px Georgia,serif}h2{font:normal 30px Georgia,serif;margin-top:45px}h3{font:normal 22px Georgia,serif}figure{margin:22px 0;background:white;border:1px solid #d2ded5;padding:20px;border-radius:12px}img{display:block;width:100%;height:auto}figcaption{font-size:14px;color:#496259;margin:12px 0}.download{display:inline-block;padding:7px 12px;border:1px solid #bfd1c3;border-radius:6px}a:focus-visible{outline:3px solid #d38329}</style></head><body><main><nav><a href="index.html">Interactive maps</a><strong>Map Gallery</strong><a href="index.html#geoai-demo">How GeoAI works</a></nav><h1>Map Gallery</h1><p>All static map layers and illustrative GeoAI sequences in one place. Open an image at full size or download its PNG for a document or presentation. Each figure includes its interpretation and limitations.</p>'''+''.join(sections)+'</main></body></html>'
 (DEST/'gallery.html').write_text(page)
 (figures/'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../gallery.html"><title>EmPath Map Gallery</title><a href="../gallery.html">Open the complete Map Gallery</a>')
 print('Map Gallery includes',count,'figures.')
if __name__=='__main__':main()
