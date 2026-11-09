"""Download and conservatively clean Plano layers and public route choices.

Defaults to ZCTA 75025 plus a 250 m context buffer. No network snapping,
centerline inference, or friction labels are invented during cleaning.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from shapely import make_valid, normalize

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://maps.planogis.org/arcgiswad/rest/services/OpenData/"
LAYERS = {"sidewalk_surfaces": ("Sidewalks", 0, "Polygon"),
          "trails": ("TrailCenterlines", 0, "LineString"),
          "parcels": ("Parcels", 1, "Polygon"),
          "address_points": ("AddressPoints", 0, "Point")}
METRIC_CRS = 26914  # NAD83 / UTM zone 14N; meters, suitable for Plano.


def session():
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504])))
    return s


def query(url, params):
    r = session().get(url, params=params, timeout=90)
    r.raise_for_status()
    d = r.json()
    if "error" in d:
        raise RuntimeError(d["error"])
    if d.get("exceededTransferLimit") or d.get("properties", {}).get("exceededTransferLimit"):
        raise RuntimeError("Truncated response; reduce batch size")
    return d


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def download_layer(name, definition, raw, bbox):
    service, layer, family = definition
    url = f"{BASE}{service}/FeatureServer/{layer}"
    folder = raw / name
    folder.mkdir()
    metadata = query(url, {"f": "json"})
    save_json(folder / "metadata.json", metadata)
    ids_response = query(url + "/query", {
        "f": "json", "where": "1=1", "returnIdsOnly": "true",
        "geometry": ",".join(map(str, bbox)), "geometryType": "esriGeometryEnvelope",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects"})
    save_json(folder / "object_ids.json", ids_response)
    ids = sorted(set(ids_response.get("objectIds") or []))
    oid = metadata["objectIdField"]
    features = []
    for i in range(0, len(ids), 300):
        batch = query(url + "/query", {"f": "geojson", "objectIds": ",".join(map(str, ids[i:i+300])),
            "outFields": "*", "outSR": 4326, "returnGeometry": "true"})
        save_json(folder / f"page_{i//300:04d}.geojson", batch)
        features.extend(batch["features"])
    got = [f["properties"][oid] for f in features]
    if len(got) != len(ids) or set(got) != set(ids):
        raise RuntimeError(f"Incomplete or duplicate source IDs in {name}")
    return {"source": url, "geometry_type": metadata["geometryType"], "rows": len(features),
            "oid_field": oid, "expected_family": family}


def clean_vector(frame, oid, family, core, context):
    """Keep distinct source records; flag co-located features instead of merging."""
    frame = frame.copy()
    frame.columns = [re.sub(r"[^a-z0-9_]+", "_", c.lower()) for c in frame.columns]
    oid = oid.lower()
    if frame[oid].isna().any() or frame[oid].duplicated().any():
        raise ValueError("Missing or duplicate source IDs require source-level review")
    frame["source_id"] = frame[oid].astype(str)
    for c in frame.columns:
        if c != "geometry" and (frame[c].dtype == "object"):
            frame[c] = frame[c].map(lambda v: v.strip() or None if isinstance(v, str) else v)
    frame["geometry_repaired"] = (~frame.geometry.is_valid) & frame.geometry.notna()
    frame.loc[frame.geometry_repaired, "geometry"] = frame.loc[frame.geometry_repaired].geometry.map(make_valid)
    acceptable = frame.geom_type.isin([family, "Multi" + family])
    bad = frame.geometry.isna() | frame.geometry.is_empty | ~frame.geometry.is_valid | ~acceptable
    quarantined = frame.loc[bad].copy()
    quarantined["reason"] = "missing_empty_invalid_or_unexpected_geometry_after_repair"
    good = frame.loc[~bad].to_crs(METRIC_CRS).copy()
    inside = good.intersects(context)
    outside = int((~inside).sum())
    good = good.loc[inside].copy()
    good["intersects_core"] = good.intersects(core)
    good["duplicate_geometry"] = good.geometry.map(lambda x: normalize(x).wkb_hex).duplicated(keep=False)
    if family == "Polygon":
        good["area_m2"] = good.area
    elif family == "LineString":
        good["length_m"] = good.length
    stats = {"raw_rows": len(frame), "clean_rows": len(good), "quarantined_rows": len(quarantined),
             "outside_context_rows": outside, "repaired_rows": int(frame.geometry_repaired.sum()),
             "duplicate_geometry_rows_retained": int(good.duplicate_geometry.sum()),
             "core_intersecting_rows": int(good.intersects_core.sum()),
             "missing_attributes": {c: int(good[c].isna().sum()) for c in good.columns if c != "geometry"}}
    assert len(frame) == len(good) + len(quarantined) + outside
    return good, quarantined, stats


def clean_choices(raw, output):
    frame = pd.read_csv(raw / "behavioural_data.csv", dtype={"Participant": "string"})
    frame.columns = frame.columns.str.lower()
    required = ["participant", "trial", "ts", "b_chosen", "treatment"] + [
        f"{r}_{suffix}" for r in ["a", "b"] for suffix in ["length", "sun_length", "tree_length", "shade_length"]]
    if not set(required).issubset(frame):
        raise ValueError("Behavioral source schema changed")
    for c in required:
        if c != "participant":
            frame[c] = pd.to_numeric(frame[c], errors="coerce")
    lengths = [c for c in required if c.endswith("length")]
    reason = pd.Series("", index=frame.index)
    def flag(mask, label):
        reason.loc[mask] += label + ";"
    flag(frame[required].isna().any(axis=1), "missing_required_value")
    numeric = [c for c in required if c != "participant"]
    flag(~np.isfinite(frame[numeric]).all(axis=1), "nonfinite_required_value")
    flag(pd.to_datetime(frame.ts, unit="s", utc=True, errors="coerce").isna(), "invalid_timestamp")
    flag((frame.trial < 1) | (frame.trial % 1 != 0), "invalid_trial_number")
    flag(~frame.b_chosen.isin([0, 1]) | ~frame.treatment.isin([0, 1]), "invalid_binary_flag")
    flag((frame[lengths] < 0).any(axis=1), "negative_length")
    flag((frame[["a_length", "b_length"]] <= 0).any(axis=1), "nonpositive_route_length")
    flag(frame.duplicated(["participant", "trial"], keep=False), "repeated_participant_trial_review")
    for r in ["a", "b"]:
        discrepancy = (frame[f"{r}_length"] - frame[[f"{r}_sun_length", f"{r}_tree_length", f"{r}_shade_length"]].sum(axis=1)).abs()
        flag(discrepancy > .05, f"{r}_length_components_disagree")
    clean = frame.loc[reason == ""].copy()
    clean["timestamp_utc"] = pd.to_datetime(clean.ts, unit="s", utc=True, errors="coerce")
    for r in ["a", "b"]:
        clean[f"{r}_sun_fraction"] = clean[f"{r}_sun_length"] / clean[f"{r}_length"]
    clean["delta_length_b_minus_a"] = clean.b_length - clean.a_length
    clean["delta_sun_length_b_minus_a"] = clean.b_sun_length - clean.a_sun_length
    clean.to_csv(output / "singapore_choices.csv", index=False)
    treatment = clean.loc[clean.treatment == 1].copy()
    treatment.to_csv(output / "singapore_sun_present_choices.csv", index=False)
    quarantine = frame.loc[reason != ""].copy()
    quarantine["reason"] = reason[reason != ""]
    quarantine.to_csv(output / "singapore_choices_quarantine.csv", index=False)
    return {"raw_rows": len(frame), "clean_rows": len(clean), "quarantined_rows": len(quarantine),
        "participants": clean.participant.nunique(), "sun_present_rows": len(treatment),
        "sun_present_participants": treatment.participant.nunique(),
        "note": "Treatment flag retained as published; no participant exclusion rules invented. Split models by participant."}


def run(zipcodes=("75025",), buffer_m=250, refresh=False):
    if not 0 <= buffer_m <= 5000:
        raise ValueError("Buffer must be between 0 and 5000 meters")
    z = gpd.read_file(ROOT / "output/scope_screen/zcta_boundaries.geojson")
    selected = z[z.ZCTA5.isin(zipcodes)].copy()
    if set(selected.ZCTA5) != set(zipcodes):
        raise ValueError("Requested ZCTA missing from cached Census boundary file")
    core = selected.to_crs(METRIC_CRS).unary_union
    context = core.buffer(buffer_m)
    bounds = gpd.GeoSeries([context], crs=METRIC_CRS).to_crs(4326).total_bounds.tolist()
    scope = "_".join(sorted(zipcodes)) + f"_buffer{buffer_m}m"
    rawroot = ROOT / "data/raw" / scope
    rawroot.mkdir(parents=True, exist_ok=True)
    candidates = sorted(p for p in rawroot.iterdir() if (p / "manifest.json").exists())
    if candidates and not refresh:
        raw = candidates[-1]
        manifest = json.loads((raw / "manifest.json").read_text())
    else:
        raw = rawroot / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        raw.mkdir()
        definitions = list(LAYERS.items())
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda item: download_layer(item[0], item[1], raw, bounds), definitions))
        manifest = {"retrieved_utc": datetime.now(timezone.utc).isoformat(), "scope": scope,
            "boundary_source": "output/scope_screen/zcta_boundaries.geojson (2020 Census ZCTAs)",
            "query_bbox_wgs84": bounds, "layers": dict(zip(LAYERS, results))}
        for name, url in {"behavioural_data.csv": "https://osf.io/download/h62em/",
                          "singapore_README.txt": "https://osf.io/download/97qxr/"}.items():
            response = session().get(url, timeout=90)
            response.raise_for_status()
            (raw / name).write_bytes(response.content)
        manifest["behavioral_source"] = "https://osf.io/aj4vk/"
        manifest["sha256"] = {str(p.relative_to(raw)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in raw.rglob("*") if p.is_file()}
        save_json(raw / "manifest.json", manifest)
    # Verify the immutable snapshot before reusing it.
    for name, expected in manifest["sha256"].items():
        if hashlib.sha256((raw / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Raw snapshot was modified: {name}")
    output = ROOT / "data/processed" / scope
    output.mkdir(parents=True, exist_ok=True)
    selected.to_file(output / "core_zctas.geojson", driver="GeoJSON")
    gpd.GeoDataFrame({"buffer_m": [buffer_m]}, geometry=[context], crs=METRIC_CRS).to_file(
        output / "context_boundary.gpkg", driver="GPKG")
    report = {"scope": scope, "raw_snapshot": str(raw.relative_to(ROOT)),
              "metric_crs": f"EPSG:{METRIC_CRS}", "layers": {}}
    for name, info in manifest["layers"].items():
        features = []
        for path in sorted((raw / name).glob("page_*.geojson")):
            features.extend(json.loads(path.read_text())["features"])
        if not features:
            report["layers"][name] = {"raw_rows": 0, "clean_rows": 0, "note": "No source features returned"}
            continue
        frame = gpd.GeoDataFrame.from_features(features, crs=4326)
        good, quarantine, stats = clean_vector(frame, info["oid_field"], info["expected_family"], core, context)
        if not good.empty:
            good.to_file(output / f"{name}.gpkg", driver="GPKG", index=False)
        quarantine.drop(columns="geometry").to_csv(output / f"{name}_quarantine.csv", index=False)
        report["layers"][name] = stats
        print(name, {k: v for k, v in stats.items() if k != "missing_attributes"}, flush=True)
    report["behavioral_choices"] = clean_choices(raw, output)
    report["not_yet_validated"] = ["Sidewalk centerlines and network connectivity", "Legal/physical crossings",
        "Parcel residential status and entrances", "Raster, weather, OSM and traffic feature joins",
        "Behavioral transfer from Singapore to Plano"]
    save_json(output / "quality_report.json", report)
    lines = ["# EmPath data cleaning report", "", f"Scope: {scope}; raw snapshot: `{report['raw_snapshot']}`.",
        "", "| Layer | Raw | Clean | Repaired | Quarantined | Outside context | Duplicate geometries retained |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for name, s in report["layers"].items():
        lines.append(f"| {name} | {s['raw_rows']} | {s['clean_rows']} | {s.get('repaired_rows', 0)} | {s.get('quarantined_rows', 0)} | {s.get('outside_context_rows', 0)} | {s.get('duplicate_geometry_rows_retained', 0)} |")
    lines += ["", "## Behavioral data", "", "```json", json.dumps(report["behavioral_choices"], indent=2), "```", "",
        "## Interpretation", "", "Sidewalks remain polygons, not routing edges. Trail lines are not yet a validated graph. "
        "Full feature geometries are retained at scope boundaries. Duplicate geometries are flagged, not automatically merged. "
        "Address points do not establish entrances, and parcels are not classified as homes. "
        "Unknown attributes stay missing rather than becoming zeros.", "", "## Remaining checks", ""]
    lines += ["- " + s for s in report["not_yet_validated"]]
    (output / "quality_report.md").write_text("\n".join(lines))
    print("Report:", output / "quality_report.md", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zipcodes", nargs="+", default=["75025"])
    parser.add_argument("--buffer-m", type=int, default=250)
    parser.add_argument("--refresh", action="store_true", help="Create a NEW raw snapshot; never overwrite an existing snapshot")
    args = parser.parse_args()
    run(tuple(args.zipcodes), args.buffer_m, args.refresh)
