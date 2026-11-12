"""Package generated local maps for authorized team sharing; never publish or copy .env."""
from pathlib import Path
import html,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/team_share'
MAPS=[('geoai_full_scope.html','Full four-ZIP GeoAI tree analysis','output/geoai_full_scope/full_scope_geoai_map.html'),('environment.html','Block environment and combined index','output/clean_deliverables/combined_environment_map.html'),('walking_network.html','Walking graph and places of interest','output/four_zip_walking_network/walking_scope_map_carto.html'),('shaded_trails.html','Shaded trail candidates','output/trail_finder/shaded_trail_candidates.html'),('geoai_routes.html','GeoAI tree predictions and illustrative routes','output/vegetation_geoai/geoai_canopy_routes.html'),('figures.html','Individual map-layer figures','output/document_layers/index.html')]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,label,relative in MAPS:
        source=ROOT/relative
        if not source.exists():continue
        shutil.copy2(source,OUT/name);rows.append((name,label,source))
    shutil.copytree(ROOT/'output/vegetation_geoai/display_images',OUT/'display_images',dirs_exist_ok=True)
    # Figure gallery references image files alongside its HTML.
    for p in (ROOT/'output/document_layers').glob('*.png'):shutil.copy2(p,OUT/p.name)
    combined=ROOT/'output/combined_block_index/combined_block_burden.png'
    if combined.exists():shutil.copy2(combined,OUT/'combined_block_burden.png')
    if (ROOT/'output/document_layers/interactive_map_links.html').exists():
        (OUT/'interactive_map_links.html').write_text('<meta http-equiv="refresh" content="0;url=index.html">')
    links=''.join(f'<li><a href="{name}">{html.escape(label)}</a></li>' for name,label,_ in rows)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>EmPath team maps</title><style>body{font:18px Georgia;max-width:850px;margin:50px auto;line-height:1.7}a{color:#145b76}</style><h1>EmPath team maps</h1><p>Download and unzip the complete folder, then open this page. Internet is required for map libraries and basemaps.</p><ul>'+links+'</ul><p>GeoAI inference covers small demonstration areas only. Routes and entrances are not verified. Environmental indices are not validated personal safety scores.</p>')
    (OUT/'README.txt').write_text('EmPath team maps\nDownload and unzip the entire folder; open index.html.\nInternet is needed for external map libraries and tiles.\nGenerated maps contain a browser-visible CARTO basemap key; .env is NOT included. Configure provider/domain permissions before public hosting.\nNo public deployment has been performed.\n')
    with zipfile.ZipFile(OUT/'EmPath_maps.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in OUT.rglob('*'):
            if p.is_file() and p.suffix.lower() in ['.html','.png','.txt']:archive.write(p,'EmPath_maps/'+str(p.relative_to(OUT)))
    text='# EmPath map links\n\nThese are LOCAL file URLs, not public links for teammates. For shared Google Docs use the Drive link to the ZIP, or hosted HTTPS map URLs. No hosting is configured.\n\n'
    for name,label,source in rows:text+=f'## {label}\n\n{source.as_uri()}\n\n'
    text+='## Sharing folder\n\n'+OUT.as_uri()+'\n\nSee docs/SHARE_EMPATH_MAPS.md for Google Sites embed instructions.\n'
    (ROOT/'docs/LOCAL_MAP_LINKS.txt').write_text(text)
    (OUT/'google_sites_embed_template.txt').write_text('<iframe src="YOUR_HOSTED_MAP_URL" title="EmPath interactive map" width="100%" height="750" style="border:0" loading="lazy" allowfullscreen></iframe>\n\nReplace YOUR_HOSTED_MAP_URL after hosting. Local files and localhost URLs will not work for teammates.\n')
    print('Team maps packaged:',len(rows),'maps. No public hosting or credential output.')
if __name__=='__main__':main()
