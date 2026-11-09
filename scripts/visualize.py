"""Build EmPath's static and interactive canopy maps from cached public data."""
import argparse
from pathlib import Path

import branca.colormap as cm
import folium
import geopandas as gpd
from branca.element import Element
from folium.plugins import Fullscreen, MeasureControl

from screen_pilot_scope import run

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "scope_screen"


def build_map():
    pieces = gpd.read_file(OUT / "canopy_zcta_intersections.geojson").to_crs(4326)
    zips = gpd.read_file(OUT / "zcta_boundaries.geojson").to_crs(4326)
    palette = cm.LinearColormap(["#fff7bc", "#a1d99b", "#238b45", "#005a32"], vmin=0, vmax=60)
    palette.caption = "Block-group canopy (%) — one consistent scale across all areas"
    m = folium.Map(location=[33.07, -96.73], zoom_start=12, tiles="OpenStreetMap", control_scale=True)
    for code in ["75025", "75024", "75074", "75023"]:
        selected = pieces[pieces.ZCTA5 == code][["ZCTA5", "geoid", "treecanopy", "geometry"]]
        folium.GeoJson(
            selected.to_json(), name=f"{code} canopy" + (" (comparison only)" if code == "75023" else ""),
            style_function=lambda feature: {
                "fillColor": palette(feature["properties"]["treecanopy"]),
                "color": "#ffffff", "weight": .5, "fillOpacity": .78,
            },
            highlight_function=lambda feature: {"weight": 2, "color": "#163c46", "fillOpacity": .95},
            tooltip=folium.GeoJsonTooltip(fields=["ZCTA5", "geoid", "treecanopy"],
                aliases=["ZCTA", "Census block group", "Canopy (%)"], localize=True),
        ).add_to(m)
    folium.GeoJson(
        zips[["ZCTA5", "geometry"]].to_json(), name="ZCTA boundaries",
        style_function=lambda f: {"color": "#263644", "weight": 2, "fillOpacity": 0},
        tooltip=folium.GeoJsonTooltip(fields=["ZCTA5"], aliases=["ZCTA"]),
    ).add_to(m)
    palette.add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    Fullscreen(position="topleft").add_to(m)
    MeasureControl(position="topleft").add_to(m)
    bounds = zips.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding_top_left=[20, 150])
    m.get_root().html.add_child(Element('''
    <style>.legend {position:fixed!important;top:auto!important;bottom:90px!important;
      left:12px!important;width:350px!important;max-width:calc(100vw - 24px);
      background:white;padding:4px;border-radius:6px}</style>
    <div style="position:fixed;top:12px;left:60px;right:50px;z-index:999;background:white;
      padding:14px 18px;border-radius:10px;box-shadow:0 3px 14px #0002;
      max-width:470px;font-family:system-ui;color:#173e46">
      <div style="font-size:25px;font-weight:750">EmPath</div>
      <div style="font-size:14px;margin:4px 0">Pedestrian heat-protection research · Pilot scope explorer</div>
      <div style="font-size:12px;color:#53656b">Proposed: 75025 + 75024 + 75074. Hover for canopy values;
      toggle layers at right. 75023 is included for comparison.</div>
    </div>
    <div style="position:fixed;bottom:28px;left:12px;z-index:999;background:white;
      padding:10px 14px;border-radius:7px;max-width:520px;font:12px system-ui;color:#46575b">
      <details><summary>Data sources and interpretation</summary>
      American Forests Texas download, retrieved November 7, 2026; 2020 Census ZCTAs.
      Underlying canopy imagery date unverified. Block-group estimates are repeated within clipped pieces;
      this is not sidewalk shade, air temperature, a trained routing model, or medical risk.
      Approximately 2% of 75074 has no canopy geometry coverage.</details>
      <a href="canopy_screen_summary.csv">Download summary CSV</a> ·
      <a href="recommended_pilot_boundary.geojson">Pilot boundary</a>
    </div>'''))
    m.save(OUT / "empath_map.html")
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Refresh public data before plotting")
    args = parser.parse_args()
    run(refresh=args.refresh)
    build_map()
    print(f"\nInteractive map: {OUT / 'empath_map.html'}")
    print("Serve: .venv/bin/python -m http.server 8765 --bind 127.0.0.1 --directory output/scope_screen")
    print("Open: http://127.0.0.1:8765/empath_map.html")


if __name__ == "__main__":
    main()
