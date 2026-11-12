"""Load the local CARTO basemap key without logging it."""
import os
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
ATTR='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>'


def load_key():
    key=os.environ.get('CARTO_BASEMAP_API_KEY','').strip()
    if not key:
        path=ROOT/'.env'
        if path.exists():
            for line in path.read_text().splitlines():
                name,sep,value=line.strip().partition('=')
                if sep and name.removeprefix('export ').strip()=='CARTO_BASEMAP_API_KEY':
                    key=value.strip().strip('\"\'');break
    if not key or key=='your_key_here':
        raise ValueError('Set CARTO_BASEMAP_API_KEY in the project .env file.')
    return key


def tiles_url():
    return 'https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png?key='+quote(load_key(),safe='')


def add_basemap(view):
    import folium
    folium.TileLayer(tiles=tiles_url(),attr=ATTR,name='CARTO Positron',max_zoom=19).add_to(view)
    return view
