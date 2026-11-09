"""Reproducible block-group canopy screen; not a sidewalk-shade assessment.

Run with a Python environment containing requests, geopandas, matplotlib.
Uses American Forests' official Texas download; snapshot retrieval date is
recorded separately from the unverified underlying canopy acquisition year.
"""
import json
import io
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "scope_screen"
OUT.mkdir(parents=True, exist_ok=True)
TES = "https://tes-app-data-share.s3.amazonaws.com/tx/tx_geojson.zip"
ZCTA = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/2"


def fetch(url, params):
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    if data.get("exceededTransferLimit") or data.get("properties", {}).get("exceededTransferLimit"):
        raise RuntimeError("Incomplete query: pagination required")
    return data


def run(refresh=False):
    zcache = OUT / "zcta_boundaries.geojson"
    zjson = json.loads(zcache.read_text()) if zcache.exists() and not refresh else fetch(ZCTA + "/query", {
        "where": "ZCTA5 IN ('75025','75023','75024','75074')",
        "outFields": "ZCTA5,AREALAND,AREAWATER", "outSR": 4326, "f": "geojson",
    })
    assert len(zjson["features"]) == 4
    zips = gpd.GeoDataFrame.from_features(zjson["features"], crs=4326)
    bounds = zips.total_bounds
    bcache = OUT / "canopy_blocks.geojson"
    if bcache.exists() and not refresh:
        blocks = gpd.read_file(bcache)
    else:
        response = requests.get(TES, timeout=60)
        response.raise_for_status()
        archive = zipfile.ZipFile(io.BytesIO(response.content))
        tesjson = json.loads(archive.read("tx_tes.geojson"))
        (OUT / "data_dictionary.txt").write_bytes(archive.read("data_dictionary.txt"))
        blocks = gpd.GeoDataFrame.from_features(tesjson["features"], crs=4326)
        blocks = blocks.cx[bounds[0]:bounds[2], bounds[1]:bounds[3]].copy()
        blocks["treecanopy"] = blocks.treecanopy * 100
        blocks = blocks.rename(columns={"GEOID": "geoid", "cnpysource": "source"})
        for name, data in [("zcta_boundaries", zjson), ("canopy_blocks", json.loads(blocks.to_json()))]:
            (OUT / (name + ".geojson")).write_text(json.dumps(data))
        (OUT / "source_metadata.json").write_text(json.dumps({
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "canopy_service": TES, "boundary_service": ZCTA,
            "download_last_modified": response.headers.get("Last-Modified"),
            "limitations": ["Official download snapshot; underlying canopy acquisition year unverified.",
                "Block-group canopy values assigned to overlapping ZCTA pieces, not measured within each piece.",
                "Not sidewalk shade, current heat resilience, air temperature, or medical risk."]
        }, indent=2))
    # EPSG:5070 gives area in square meters. Retain the original block-group
    # canopy estimate on each intersected piece; this is an approximation.
    valid = blocks[blocks.treecanopy.between(0, 100)].copy()
    pieces = gpd.overlay(valid.to_crs(5070), zips.to_crs(5070), how="intersection")
    if pieces.empty:
        raise RuntimeError("No valid canopy intersections; no result can be reported")
    pieces["piece_m2"] = pieces.area
    pieces.to_crs(4326).to_file(OUT / "canopy_zcta_intersections.geojson", driver="GeoJSON")
    rows = []
    for code, group in pieces.groupby("ZCTA5"):
        zip_area = zips.loc[zips.ZCTA5 == code].to_crs(5070).area.sum()
        ordered = group.sort_values("treecanopy")
        cdf = ordered.piece_m2.cumsum() / ordered.piece_m2.sum()
        quantile = lambda q: float(ordered.loc[cdf >= q, "treecanopy"].iloc[0])
        rows.append({"zcta": code, "land_area_sqmi": float(zips.loc[zips.ZCTA5 == code, "AREALAND"].iloc[0]) / 2589988.110336,
            "valid_canopy_coverage_pct": 100 * group.piece_m2.sum() / zip_area,
            "overlapping_block_groups": group.geoid.nunique(),
            "approx_area_weighted_canopy_pct": (group.treecanopy * group.piece_m2).sum() / group.piece_m2.sum(),
            "weighted_p10_canopy_pct": quantile(.1), "weighted_p90_canopy_pct": quantile(.9),
            "min_block_canopy_pct": group.treecanopy.min(), "max_block_canopy_pct": group.treecanopy.max()})
    import pandas as pd
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "canopy_screen_summary.csv", index=False)
    print(summary.round(2).to_string(index=False))
    print("Canopy sources:", blocks.source.value_counts().to_dict())
    print("Invalid/missing canopy blocks:", len(blocks) - len(valid))

    fig, ax = plt.subplots(figsize=(10, 8))
    pieces.plot(column="treecanopy", cmap="YlGn", vmin=0, vmax=60, ax=ax,
                legend=True, legend_kwds={"label": "Block-group canopy (%)", "shrink": .65})
    projected = zips.to_crs(5070)
    projected.boundary.plot(ax=ax, color="#25313e", linewidth=1.3)
    for _, row in projected.iterrows():
        point = row.geometry.representative_point()
        ax.text(point.x, point.y, row.ZCTA5, ha="center", fontsize=12,
                bbox={"facecolor": "white", "alpha": .85, "edgecolor": "none", "pad": 3})
    ax.set_title("Pilot scope screening: 75025 and adjacent ZCTAs", loc="left", fontsize=15)
    ax.set_axis_off()
    fig.text(.08, .03, "American Forests Texas canopy snapshot; 2020 Census ZCTA boundaries.\n"
             "Colors repeat block-group estimates across clipped pieces; not measured sidewalk shade.", fontsize=9)
    fig.savefig(OUT / "canopy_screen.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    selected = zips[zips.ZCTA5.isin(["75025", "75024", "75074"])].copy()
    selected.to_file(OUT / "recommended_pilot_zctas.geojson", driver="GeoJSON")
    gpd.GeoDataFrame({"name": ["EmPath pilot"]}, geometry=[selected.unary_union], crs=zips.crs).to_file(OUT / "recommended_pilot_boundary.geojson", driver="GeoJSON")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download fresh source snapshots (otherwise use local files)")
    run(refresh=parser.parse_args().refresh)
