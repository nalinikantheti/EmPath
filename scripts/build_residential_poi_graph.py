"""Contract shortest pedestrian routes into origin-to-POI edges only.

The detailed pedestrian network is retained privately as the routing substrate.
The output activity graph has no origin-origin or POI-POI edges and no parallel
routes per origin/POI pair within a given objective.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
from shapely.geometry import MultiLineString

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/residential_poi_graph'
OBJECTIVES = {'shortest_time': 'time_only_s', 'lowest_friction': 'scenario_lambda_1_0_cost_s', 'prototype_friction': 'prototype_friction_cost_s', 'missing_high_burden_sensitivity': 'missing_high_burden_cost_s', 'block_context_proxy': 'block_proxy_cost_s'}


def routing_graph(table, cost):
    graph = nx.MultiDiGraph()
    for r in table.itertuples(index=False):
        value = getattr(r, cost)
        if not np.isfinite(value) or value < 0 or not np.isfinite(r.length) or r.length <= 0:
            continue
        graph.add_edge(int(r.u), int(r.v), key=int(r.key), weight=float(value),
                       length=float(r.length), time=float(r.time_only_s), estimated=True if cost=='block_proxy_cost_s' else bool(r.estimated_weight), known_factors=int(r.block_proxy_factor_count) if cost=='block_proxy_cost_s' else int(r.known_factor_count), nearby_proxy=bool(getattr(r,'block_proxy_nearby_used',False)) if cost=='block_proxy_cost_s' else False)
    return graph


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'output/network_connections/candidate_connections.gpkg'
    points = gpd.read_file(source)
    if points.location_id.duplicated().any():
        raise ValueError('Location IDs must be unique')
    if not points.role.isin(['origin', 'destination']).all():
        raise ValueError('Only origin and destination roles are allowed')
    origins = points[points.role == 'origin']
    destinations = points[points.role == 'destination']
    if origins.empty or destinations.empty:
        raise ValueError('Need at least one origin and destination')
    from prototype_missing_data import enrich_costs
    costs = enrich_costs(pd.read_csv(ROOT / 'output/step3_friction/edge_costs.csv'))
    if costs.duplicated(['u', 'v', 'key']).any():
        raise ValueError('Duplicate directed walking edge IDs')
    geometries = gpd.read_file(ROOT / 'output/geoai_full_scope/ai_walking_edges.gpkg')
    lookup = {(int(r.u), int(r.v), int(r.key)): r.geometry for r in geometries.itertuples(index=False)}
    ll = points.to_crs(4326).set_index('location_id')
    all_pairs, all_segments, all_routes, reports = [], [], [], {}
    for objective, cost in OBJECTIVES.items():
        if cost not in costs: continue
        substrate = routing_graph(costs, cost)
        activity = nx.DiGraph(objective=objective, edge_weight_units='seconds' if objective == 'shortest_time' else 'equivalent seconds',
                              access_verified=False, description='Provisional residential-origin to POI shortest-route contraction; no same-role edges')
        for p in points.itertuples(index=False):
            activity.add_node(str(p.location_id), role=str(p.role), label=str(p.label),
                category='' if pd.isna(getattr(p, 'category', None)) else str(p.category),
                network_node=int(p.network_node), longitude=float(ll.loc[p.location_id].geometry.x),
                latitude=float(ll.loc[p.location_id].geometry.y), connector_distance_m=float(p.connector_distance_m),
                entrance_verified=False)
        union_ids = set()
        unreachable = 0
        for origin in origins.itertuples(index=False):
            start = int(origin.network_node)
            distances, paths = nx.single_source_dijkstra(substrate, start, weight='weight') if start in substrate else ({}, {})
            for dest in destinations.itertuples(index=False):
                end = int(dest.network_node)
                common = {'objective': objective, 'origin': str(origin.location_id), 'destination': str(dest.location_id),
                          'origin_gap_m': float(origin.connector_distance_m), 'destination_gap_m': float(dest.connector_distance_m), 'access_verified': False}
                if end not in distances:
                    unreachable += 1
                    all_pairs.append({**common, 'status': 'unreachable_on_objective_supported_network'})
                    continue
                path = paths[end]
                chosen = []
                for u, v in zip(path, path[1:]):
                    key, attr = min(substrate[u][v].items(), key=lambda pair: (pair[1]['weight'], pair[0]))
                    chosen.append(((u, v, key), attr))
                total = sum(a['weight'] for _, a in chosen)
                assert np.isclose(total, distances[end]), 'Route cost does not equal shortest-path distance'
                attrs = {'weight': float(total), 'distance_m': sum(a['length'] for _, a in chosen),
                         'network_walk_minutes': sum(a['time'] for _, a in chosen) / 60,
                         'cost_equivalent_minutes': total / 60, 'segment_count': len(chosen), 'access_verified': False}
                attrs['estimated_distance_fraction'] = sum(a['length'] for _, a in chosen if a['estimated']) / attrs['distance_m'] if attrs['distance_m'] else 0.0
                attrs['nearby_block_distance_fraction'] = sum(a['length'] for _, a in chosen if a['nearby_proxy']) / attrs['distance_m'] if attrs['distance_m'] else 0.0
                attrs['minimum_known_factor_count'] = min((a['known_factors'] for _, a in chosen), default=0)
                activity.add_edge(str(origin.location_id), str(dest.location_id), **attrs)
                all_pairs.append({**common, 'status': 'provisional_network_route', **attrs})
                lines = []
                for i, (identity, a) in enumerate(chosen):
                    union_ids.add(identity)
                    all_segments.append({**common, 'sequence': i, 'u': identity[0], 'v': identity[1], 'key': identity[2], 'segment_cost_s': a['weight']})
                    geom = lookup[identity]
                    lines.extend(list(geom.geoms) if geom.geom_type == 'MultiLineString' else [geom])
                # Co-snapped endpoints have zero network distance, but do not imply zero door-to-door distance.
                if lines:
                    all_routes.append({**common, **attrs, 'geometry': MultiLineString(lines)})
        assert all(activity.nodes[u]['role'] == 'origin' and activity.nodes[v]['role'] == 'destination' for u, v in activity.edges)
        assert all(activity.in_degree(n) == 0 for n in origins.location_id)
        assert all(activity.out_degree(n) == 0 for n in destinations.location_id)
        nx.write_graphml(activity, OUT / f'{objective}_activity_graph.graphml')
        union = geometries[[ (int(r.u), int(r.v), int(r.key)) in union_ids for r in geometries.itertuples(index=False) ]].copy()
        union_path = OUT / f'{objective}_selected_network.gpkg'
        if union_path.exists(): union_path.unlink()
        if not union.empty: union.to_file(union_path, driver='GPKG', index=False)
        reports[objective] = {'activity_nodes': activity.number_of_nodes(), 'origin_to_poi_edges': activity.number_of_edges(),
                              'unreachable_pairs': unreachable, 'unique_selected_walking_edges': len(union_ids),
                              'supported_substrate_edges': substrate.number_of_edges()}
    pd.DataFrame(all_pairs).to_csv(OUT / 'origin_poi_costs.csv', index=False)
    pd.DataFrame(all_segments).to_csv(OUT / 'route_segments.csv', index=False)
    path = OUT / 'origin_poi_routes.gpkg'
    if path.exists(): path.unlink()
    if all_routes: gpd.GeoDataFrame(all_routes, crs=geometries.crs).to_file(path, driver='GPKG', index=False)
    points.to_file(OUT / 'activity_nodes.gpkg', driver='GPKG', index=False)
    report = {'origins': len(origins), 'destinations': len(destinations), 'potential_origin_poi_pairs': len(origins) * len(destinations),
        'origin_inventory': 'Existing four illustrative block-origin candidates, not all homes or all residential blocks. Address-containing blocks are not proven residential.',
        'objectives': reports,
        'edge_rule': 'Exactly one minimum-cost network route per reachable origin/POI pair, separately for each objective. Equal-cost ties keep one available path. No origin-origin, POI-POI or reverse recommendation edges.',
        'block_context_rule': 'Separate block-overlay proxy: length-weighted block factors; bounded nearest-valid-block fallback with provenance. Every weight in this mode is a block-context estimate, not a direct edge measurement.',
        'prototype_rule': 'Available-factor mean, with partial-input routes flagged; no-factor edges remain unavailable. Separate pessimistic missing-burden=1 sensitivity. Route table reports estimated-distance fraction.',
        'friction_rule': 'Use Step 3 assumed equal-weight canopy-deficit, traffic and midpoint-block surface-temperature burden; lambda=1. Weight is equivalent seconds, not measured travel time or learned overall preference.',
        'baseline_rule': 'Constant-speed shortest time equals shortest distance. Full baseline and friction may use different supported edges; Notebook 17 supplies same-support comparisons.',
        'union_rule': 'Selected-network layers contain only detailed walking edges used by retained routes, with shared segments deduplicated by u/v/key. The full source network is not overwritten.',
        'missing': 'Missing friction inputs remove edges from that objective. Unreachable pairs are reported, never given zero weight or fabricated connectors.',
        'connections': 'Nearest-node candidates; entrances/crossings not verified. Costs omit connector travel and crossing waits. Co-snapped nodes can have zero network distance.',
        'checks': {'same_role_edges_absent': True, 'one_edge_per_pair_per_objective': True, 'route_cost_equals_dijkstra_minimum': True}}
    (OUT / 'graph_method.json').write_text(json.dumps(report, indent=2))
    write_sensitivity(pd.DataFrame(all_pairs), pd.DataFrame(all_segments))
    return report, pd.DataFrame(all_pairs)


def write_sensitivity(costs, segments):
    paths = {k: tuple(zip(g.u, g.v, g.key)) for k, g in segments.groupby(['objective', 'origin', 'destination'], sort=False)}
    p = costs[costs.objective.eq('prototype_friction') & costs.status.eq('provisional_network_route')].copy()
    p['path_changes_under_missing_high_burden'] = [paths.get(('prototype_friction', r.origin, r.destination)) != paths.get(('missing_high_burden_sensitivity', r.origin, r.destination)) for r in p.itertuples()]
    p['path_differs_from_distance_route'] = [paths.get(('prototype_friction', r.origin, r.destination)) != paths.get(('shortest_time', r.origin, r.destination)) for r in p.itertuples()]
    p.to_csv(OUT / 'prototype_route_sensitivity.csv', index=False)
    report = {'reachable_prototype_pairs': len(p), 'changed_paths_under_missing_high_burden': int(p.path_changes_under_missing_high_burden.sum()),
        'different_from_distance_route': int(p.path_differs_from_distance_route.sum()),
        'median_estimated_distance_fraction': float(p.estimated_distance_fraction.median()),
        'mean_estimated_distance_fraction': float(p.estimated_distance_fraction.mean()),
        'warning': 'Route changes compare assumptions, not accuracy. Same path does not imply unbiased weight.'}
    (OUT / 'prototype_sensitivity_summary.json').write_text(json.dumps(report, indent=2))

if __name__ == '__main__':
    report, _ = run()
    print(json.dumps(report, indent=2))
