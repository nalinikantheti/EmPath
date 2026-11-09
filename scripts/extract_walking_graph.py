"""Download a connected OSM walking graph and retain an audit of excluded pieces."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import networkx as nx
import osmnx as ox

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default="Brooklyn, New York, USA")
    parser.add_argument("--dist", type=float, default=500, help="Bounding-box half-width in meters")
    parser.add_argument("--output", type=Path, default=ROOT / "output/walking_network")
    args = parser.parse_args()
    if args.dist <= 0:
        parser.error("--dist must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.cache_folder = ROOT / "data/raw/osmnx_cache"
    ox.settings.log_console = True
    ox.settings.requests_timeout = 180
    ox.settings.useful_tags_way = list(dict.fromkeys(
        ox.settings.useful_tags_way + ["foot", "sidewalk", "crossing", "surface", "access", "lit", "incline", "steps"]
    ))
    center = ox.geocoder.geocode(args.address)
    raw = ox.graph.graph_from_point(
        center, dist=args.dist, dist_type="bbox", network_type="walk",
        simplify=True, retain_all=True,
    )
    components = sorted(nx.weakly_connected_components(raw), key=len, reverse=True)
    if not components:
        raise RuntimeError("No walking nodes were found in the selected area")
    graph = raw.subgraph(components[0]).copy()
    assert nx.is_weakly_connected(graph)
    ox.io.save_graphml(raw, args.output / "walking_network_all_components.graphml")
    ox.io.save_graphml(graph, args.output / "walking_network.graphml")
    ox.io.save_graph_geopackage(graph, args.output / "walking_network.gpkg", directed=True)
    nodes, edges = ox.convert.graph_to_gdfs(graph)
    nodes.drop(columns="geometry").to_csv(args.output / "nodes.csv")
    edges.to_csv(args.output / "edges.csv")  # geometry is WKT; edge IDs are (u, v, key)
    fig, ax = ox.plot.plot_graph(graph, show=False, close=False, bgcolor="white",
                                node_color="#167d8d", edge_color="#334155", node_size=12)
    ax.set_title("OSM walking network · © OpenStreetMap contributors")
    fig.savefig(args.output / "walking_network.png", dpi=180, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    summary = {
        "source": "© OpenStreetMap contributors, https://www.openstreetmap.org/copyright",
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "osmnx_version": ox.__version__, "address": args.address,
        "center_lat_lon": list(center), "bbox_half_width_m": args.dist,
        "network_type": "walk", "component_node_counts": [len(c) for c in components],
        "nodes": len(graph), "directed_edges": graph.number_of_edges(),
        "excluded_nodes": len(raw) - len(graph),
        "weakly_connected": nx.is_weakly_connected(graph),
        "strongly_connected": nx.is_strongly_connected(graph),
        "limitations": [
            "Bounding box, not a 500 m walking-distance catchment or circular radius.",
            "Largest component retained; disconnected mapped paths remain in the all-components file.",
            "OSM walk filtering is not validation of sidewalk coverage, legal crossings, or accessibility.",
            "Buildings and house entrances are not automatically attached to the walking graph.",
            "Reciprocal directed edges can represent the same physical segment.",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
