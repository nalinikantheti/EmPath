"""Audit cached four-ZCTA graph without changing topology or downloading data."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / 'output/four_zip_walking_network'
    out = ROOT / 'output/cleaning_start'
    out.mkdir(parents=True, exist_ok=True)
    graph = ox.io.load_graphml(source / 'walking_network_all_components.graphml')
    nodes, edges = ox.convert.graph_to_gdfs(graph)
    lengths = pd.to_numeric(edges['length'], errors='coerce')
    missing = edges.geometry.isna() | edges.geometry.is_empty
    flags = pd.DataFrame(index=edges.index)
    flags['missing_empty_geometry'] = missing
    flags['invalid_geometry'] = ~edges.geometry.is_valid
    flags['bad_length'] = ~np.isfinite(lengths) | (lengths <= 0)
    flags['self_loop_review'] = edges.index.get_level_values('u') == edges.index.get_level_values('v')
    flags['long_edge_review'] = lengths > 1000
    # Self loops and long simplified edges are review candidates, not automatic errors.
    flagged = flags[flags.any(axis=1)].copy()
    flagged['length_m'] = lengths.reindex(flagged.index)
    flagged.reset_index().to_csv(out / 'edge_review.csv', index=False)
    components = sorted(nx.weakly_connected_components(graph), key=len, reverse=True)
    membership = {n: i for i, c in enumerate(components) for n in c}
    nodes['component_id'] = nodes.index.map(membership)
    scope = gpd.read_file(source / 'zip_boundaries.geojson').to_crs(nodes.crs)
    counts = []
    for _, row in scope.iterrows():
        inside = nodes[nodes.geometry.intersects(row.geometry)]
        counts.append({'zcta': str(row.ZCTA5), 'nodes': len(inside),
                       'nodes_outside_largest_component': int((inside.component_id != 0).sum())})
    pd.DataFrame(counts).to_csv(out / 'network_coverage_by_zip.csv', index=False)
    pois = gpd.read_file(source / 'places_of_interest.geojson')
    pois.groupby('category', dropna=False).size().rename('count').to_csv(out / 'poi_categories.csv')
    summary = {
        'graph_file': str((source / 'walking_network_all_components.graphml').relative_to(ROOT)),
        'nodes': graph.number_of_nodes(), 'directed_edges': graph.number_of_edges(),
        'weak_components': len(components), 'largest_component_nodes': len(components[0]),
        'crs': str(nodes.crs), 'unique_node_ids': bool(nodes.index.is_unique),
        'unique_u_v_key': bool(edges.index.is_unique),
        'edge_review_flag_counts': {c: int(flags[c].sum()) for c in flags},
        'poi_count': len(pois), 'poi_categories': pois.category.value_counts().to_dict(),
        'processed_municipal_scopes': sorted(p.name for p in (ROOT / 'data/processed').iterdir() if p.is_dir()),
        'note': 'Automated structural checks only. No access, entrance, crossing or sidewalk validation performed. Directed reciprocal edges and valid parallel edges retained.'}
    (out / 'audit.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
