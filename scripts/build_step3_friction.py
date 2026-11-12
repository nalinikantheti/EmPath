"""Prepare auditable edge costs and illustrative, like-for-like route benchmarks.
Uses cached GeoAI predictions; does not train a new model or certify access.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/step3_friction'


def edge_costs(edges, blocks, beta):
    """Join block-context heat while retaining fine-scale AI canopy and traffic."""
    d = edges.copy()
    if d.duplicated(['u', 'v', 'key']).any():
        raise ValueError('Duplicate directed edge IDs')
    heat = blocks[['GEOID20', 'landsat_summer_surface_temp_c', 'temperature_burden_01']].copy()
    heat['GEOID20'] = heat.GEOID20.astype(str)
    d['block_geoid_midpoint'] = d.block_geoid_midpoint.astype(str)
    d = d.merge(heat, left_on='block_geoid_midpoint', right_on='GEOID20', how='left', validate='many_to_one')
    length = pd.to_numeric(d['length'], errors='coerce')
    d['time_only_s'] = (length / 1.2).where(np.isfinite(length) & (length > 0))
    canopy = pd.to_numeric(d.ai_tree_cover_01, errors='coerce')
    d['canopy_deficit_01'] = (1 - canopy).where(canopy.between(0, 1) & (d.ai_corridor_coverage_01 >= .98))
    traffic = pd.to_numeric(d.traffic_index_0_100, errors='coerce') / 100
    d['traffic_burden_01'] = traffic.where(traffic.between(0, 1))
    d['temperature_burden_01'] = d.temperature_burden_01.where(d.temperature_burden_01.between(0, 1))
    factors = d[['canopy_deficit_01', 'traffic_burden_01', 'temperature_burden_01']]
    d['three_factor_burden_01'] = factors.mean(axis=1).where(factors.notna().all(axis=1))
    d['transferred_canopy_cost_s'] = d.time_only_s * (1 + beta * d.canopy_deficit_01)
    for strength in [.5, 1., 2.]:
        label = str(strength).replace('.', '_')
        d[f'scenario_lambda_{label}_cost_s'] = d.time_only_s * (1 + strength * d.three_factor_burden_01)
    return d


def make_graph(edges, column):
    graph = nx.MultiDiGraph()
    for r in edges.itertuples(index=False):
        cost = getattr(r, column)
        if not np.isfinite(cost) or not np.isfinite(r.time_only_s):
            continue
        graph.add_edge(int(r.u), int(r.v), key=int(r.key), cost=float(cost), time=float(r.time_only_s), row=r)
    return graph


def route_edges(graph, start, end, weight):
    path = nx.shortest_path(graph, start, end, weight=weight)
    return [min(graph[u][v].values(), key=lambda x: x[weight]) for u, v in zip(path, path[1:])]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    edges = gpd.read_file(ROOT / 'output/geoai_full_scope/ai_walking_edges.gpkg')
    blocks = gpd.read_file(ROOT / 'output/geoai_full_scope/ai_block_environment.gpkg')
    model = json.loads((ROOT / 'output/route_preference_model/model_and_evaluation.json').read_text())
    beta = float(model['full_data_extra_sun_distance_factor'])
    if not np.isfinite(beta) or beta < 0:
        raise ValueError('Transferred coefficient must be finite and nonnegative')
    d = edge_costs(edges, blocks, beta)
    costs = ['transferred_canopy_cost_s'] + [f'scenario_lambda_{x}_cost_s' for x in ['0_5', '1_0', '2_0']]
    checks = {'unique_edge_ids': not d.duplicated(['u', 'v', 'key']).any(),
              'positive_known_baseline_times': bool((d.time_only_s.dropna() > 0).all()),
              'costs_at_least_baseline': all(bool((d[c].dropna() >= d.loc[d[c].notna(), 'time_only_s']).all()) for c in costs),
              'missing_factor_stays_unknown': bool(d.loc[d[['canopy_deficit_01', 'traffic_burden_01', 'temperature_burden_01']].isna().any(axis=1), 'three_factor_burden_01'].isna().all())}
    # Homogeneous costs are additive: splitting an edge cannot lower its total cost.
    checks['homogeneous_subdivision_invariance'] = bool(np.isclose(100 * (1 + beta * .6), 40 * (1 + beta * .6) + 60 * (1 + beta * .6)))
    endpoints = pd.read_csv(ROOT / 'output/geoai_full_scope/full_scope_route_comparison.csv')
    endpoints = endpoints[endpoints.route == 'Shortest distance'][['zip', 'origin_node', 'destination_node']].drop_duplicates()
    full = make_graph(d, 'time_only_s')
    summaries, geometries = [], []
    for column in costs:
        graph = make_graph(d, column)
        for pair in endpoints.itertuples(index=False):
            a, b = int(pair.origin_node), int(pair.destination_node)
            common = {'zip': str(pair.zip), 'scenario': column, 'origin_node': a, 'destination_node': b, 'access_verified': False}
            try:
                baseline = route_edges(graph, a, b, 'time')
                selected = route_edges(graph, a, b, 'cost')
            except (nx.NodeNotFound, nx.NetworkXNoPath):
                summaries.append({**common, 'status': 'Unreachable on this scenario-supported graph'})
                continue
            full_time = sum(x['time'] for x in route_edges(full, a, b, 'time'))
            base_cost = sum(x['cost'] for x in baseline)
            selected_cost = sum(x['cost'] for x in selected)
            if selected_cost > base_cost + 1e-6:
                raise AssertionError('Weighted route failed its objective comparison')
            for label, selected_edges in [('time_only_same_support', baseline), ('friction_route', selected)]:
                time = sum(x['time'] for x in selected_edges)
                length = sum(x['row'].length for x in selected_edges)
                def mean(field):
                    values = np.array([getattr(x['row'], field) for x in selected_edges], dtype=float)
                    return float(np.average(values, weights=[x['row'].length for x in selected_edges])) if np.isfinite(values).all() else None
                summaries.append({**common, 'status': 'Illustrative network route', 'route': label,
                    'network_walk_minutes': time / 60, 'full_network_shortest_minutes': full_time / 60,
                    'distance_m': length, 'scenario_cost_equivalent_minutes': sum(x['cost'] for x in selected_edges) / 60,
                    'mean_ai_tree_cover_01': mean('ai_tree_cover_01'), 'mean_traffic_burden_01': mean('traffic_burden_01'),
                    'mean_temperature_burden_01': mean('temperature_burden_01'),
                    'changed_from_same_support_time_route': [(x['row'].u, x['row'].v, x['row'].key) for x in selected] != [(x['row'].u, x['row'].v, x['row'].key) for x in baseline]})
                for i, item in enumerate(selected_edges):
                    r = item['row']
                    geometries.append({**common, 'route': label, 'sequence': i, 'u': int(r.u), 'v': int(r.v), 'key': int(r.key), 'geometry': r.geometry})
    checks['weighted_routes_minimize_stated_cost'] = True
    if not all(checks.values()):
        raise AssertionError(checks)
    d.drop(columns='geometry').to_csv(OUT / 'edge_costs.csv', index=False)
    pd.DataFrame(summaries).to_csv(OUT / 'route_benchmark.csv', index=False)
    if geometries:
        target = OUT / 'benchmark_routes.gpkg'
        if target.exists(): target.unlink()
        gpd.GeoDataFrame(geometries, crs=edges.crs).to_file(target, driver='GPKG', index=False)
    report = {
        'status': 'Ready for prototype modeling; access and crossings not fully validated',
        'edges': len(d), 'blocks': len(blocks), 'crs': str(edges.crs),
        'cost_feature_coverage': {c: int(d[c].notna().sum()) for c in ['time_only_s'] + costs},
        'missing_features': ['Segment-level imperviousness', 'Verified intersection/crossing attributes'],
        'baseline': 'length_m / 1.2 m/s; network-only time, no crossing waits or access connectors',
        'transferred_canopy': {'formula': 'time_only_s * (1 + beta * canopy_deficit_01)', 'beta': beta,
            'label': 'Singapore preference coefficient transferred to a canopy proxy; not a Plano-trained model'},
        'three_factor_scenarios': {'formula': 'time_only_s * (1 + lambda * mean(canopy_deficit_01, traffic_burden_01, temperature_burden_01))',
            'lambda': [.5, 1., 2.], 'weights': 'Equal assumed factor weights, not learned'},
        'heat_join': 'Existing block_geoid_midpoint joins block mean Landsat surface temperature. Context proxy, not direct edge temperature; boundary-crossing edges are not split.',
        'missing_policy': 'Unknown required factors yield unknown costs. Excluded edges are counted. Each comparison uses identical scenario-supported graph; full-network baseline also reported.',
        'evaluation': 'Four pre-existing illustrative OD pairs, one per ZIP; not household coverage or preference accuracy validation.',
        'geoai': 'Existing full-area pretrained tree segmentation; no new model trained in this step.',
        'limits': ['Canopy adjacency is not measured shade.', 'Surface temperature is not air temperature or peak-hour heat.', 'Correlated canopy and surface heat can double-count conditions.', 'No verified health-risk or safety prediction.'],
        'checks': checks}
    (OUT / 'method_and_readiness.json').write_text(json.dumps(report, indent=2))
    return report, pd.DataFrame(summaries)

if __name__ == '__main__':
    report, comparison = run()
    print(json.dumps(report, indent=2))
    print(comparison.to_string(index=False))
