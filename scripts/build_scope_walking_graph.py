"""Extract and map the walking network across all four EmPath ZCTAs."""
import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path

import folium
from folium.plugins import MarkerCluster
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import osmnx as ox

ROOT = Path(__file__).resolve().parents[1]
ZIPCODES = ['75025', '75024', '75074', '75023']
COLORS = {'75025': '#7c3aed', '75024': '#db2777', '75074': '#ea580c', '75023': '#2563eb'}
POI_TAGS = {
    'amenity': ['school', 'college', 'university', 'library', 'hospital', 'clinic',
                'pharmacy', 'community_centre', 'bus_station'],
    'leisure': ['park', 'playground'], 'shop': ['supermarket', 'convenience'],
    'railway': ['station', 'halt', 'tram_stop'],
}


def load_scope():
    scope = gpd.read_file(ROOT / 'output/scope_screen/zcta_boundaries.geojson').to_crs(4326)
    scope = scope[scope.ZCTA5.astype(str).isin(ZIPCODES)].copy().sort_values('ZCTA5')
    if set(scope.ZCTA5) != set(ZIPCODES):
        raise ValueError('Expected all four EmPath ZCTA boundaries')
    if not scope.geometry.is_valid.all():
        raise ValueError('Invalid scope polygons')
    return scope


def poi_category(row):
    for key in ['amenity', 'leisure', 'shop', 'railway']:
        value = row.get(key)
        if isinstance(value, str) and value in POI_TAGS[key]:
            return value
    return 'place of interest'


def fetch_pois(polygon, target):
    try:
        # The detailed ZCTA outline can exceed the server's query-size limit.
        # Query its simple convex hull, then filter/clip back to the exact scope.
        features = ox.features.features_from_polygon(polygon.convex_hull, POI_TAGS)
    except ox._errors.InsufficientResponseError:
        features = gpd.GeoDataFrame(columns=['name', 'category', 'osm_element', 'osm_id', 'geometry'], crs=4326)
    if len(features):
        features = features[features.geometry.intersects(polygon)].copy()
        features.geometry = features.geometry.intersection(polygon)
        features = features.reset_index()
        features['category'] = features.apply(poi_category, axis=1)
        if 'name' not in features:
            features['name'] = None
        features['name'] = features['name'].fillna('Unnamed mapped feature').astype(str)
        features = features.rename(columns={'element': 'osm_element', 'id': 'osm_id'})
        features = features[['name', 'category', 'osm_element', 'osm_id', 'geometry']]
    features.to_file(target, driver='GeoJSON')
    return features


def create_maps(graph, scope, pois, output, node_radius):
    nodes, edges = ox.convert.graph_to_gdfs(graph)
    # Draw physical segments once while retaining reciprocal edges in graph exports.
    physical = ox.convert.to_undirected(graph)
    physical_edges = ox.convert.graph_to_gdfs(physical, nodes=False)
    points = pois.copy()
    if len(points):
        points = points.to_crs(26914)
        points.geometry = points.geometry.representative_point()
        points = points.to_crs(4326)
    bounds = scope.total_bounds
    m = folium.Map(location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
                   tiles='OpenStreetMap', prefer_canvas=True, control_scale=True)
    network_layer = folium.FeatureGroup(name='Walking segments', show=True)
    folium.GeoJson(json.loads(physical_edges[['geometry']].to_json()),
                   style_function=lambda _: {'color': '#334155', 'weight': 1.5, 'opacity': .8}).add_to(network_layer)
    network_layer.add_to(m)
    node_layer = folium.FeatureGroup(name='Graph nodes (larger dots)', show=True)
    node_features = nodes[['geometry']].copy()
    node_features['osm_node'] = nodes.index.astype(str)
    folium.GeoJson(json.loads(node_features.to_json()),
                   marker=folium.CircleMarker(radius=node_radius, weight=.5, color='white',
                                              fill=True, fill_color='#0891b2', fill_opacity=.85),
                   tooltip=folium.GeoJsonTooltip(fields=['osm_node'], aliases=['OSM node:'])).add_to(node_layer)
    node_layer.add_to(m)
    # Each ZCTA is independently toggleable; boundaries are drawn over the network.
    for _, row in scope.iterrows():
        code = row.ZCTA5
        color = COLORS[code]
        layer = folium.FeatureGroup(name=f'ZIP area {code}' + (' (comparison)' if code == '75023' else ''), show=True)
        feature = gpd.GeoDataFrame({'ZCTA5': [code]}, geometry=[row.geometry], crs=scope.crs)
        folium.GeoJson(json.loads(feature.to_json()),
                       style_function=lambda _, color=color: {'color': color, 'weight': 3,
                                                              'fillColor': color, 'fillOpacity': .025},
                       tooltip=folium.GeoJsonTooltip(fields=['ZCTA5'], aliases=['ZIP area:'])).add_to(layer)
        label = row.geometry.representative_point()
        folium.Marker([label.y, label.x], icon=folium.DivIcon(
            html=f'<div style="font: bold 15px sans-serif;color:{color};background:white;border:2px solid {color};padding:3px;width:65px;text-align:center">{code}</div>')).add_to(layer)
        layer.add_to(m)
    categories = sorted(points.category.unique()) if len(points) else []
    for category in categories:
        layer = folium.FeatureGroup(name=f'POI: {category.replace("_", " ")}', show=True)
        cluster = MarkerCluster(disableClusteringAtZoom=15, maxClusterRadius=35).add_to(layer)
        for _, row in points[points.category == category].iterrows():
            name = escape(row['name'])
            osm_url = f'https://www.openstreetmap.org/{row.osm_element}/{row.osm_id}'
            popup = (f'<b>{name}</b><br>{escape(category)}<br>'
                     'Marker represents mapped feature, not a verified entrance.<br>'
                     f'<a href="{osm_url}" target="_blank">View on OpenStreetMap</a>')
            folium.Marker([row.geometry.y, row.geometry.x], tooltip=f'{name} · {category}',
                          popup=folium.Popup(popup, max_width=300),
                          icon=folium.Icon(color='orange', icon='info-sign')).add_to(cluster)
        layer.add_to(m)
    legend = '''<div style="position:fixed;bottom:25px;left:15px;z-index:9999;background:white;
        padding:12px;max-width:310px;border:1px solid #ccc;font:13px sans-serif">
        <b>EmPath · four ZIP areas</b><br>Teal dots: graph junctions / endpoints<br>
        Dark lines: mapped walkable segments<br>Orange markers: places of interest<br>
        Colored outlines: Census ZCTAs (ZIP approximations)<br>
        All mapped components shown; crossings and entrances need validation.<br>
        © OpenStreetMap contributors</div>'''
    m.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    m.save(output / 'walking_scope_map.html')

    projected = scope.to_crs(26914)
    fig, ax = plt.subplots(figsize=(16, 13))
    physical_edges.to_crs(26914).plot(ax=ax, color='#475569', linewidth=.45, zorder=1)
    # The overview spans 124 km²; large dots are available in the zoomable map.
    nodes.to_crs(26914).plot(ax=ax, color='#0891b2', markersize=3, alpha=.7, zorder=2)
    for _, row in projected.iterrows():
        gpd.GeoSeries([row.geometry], crs=projected.crs).boundary.plot(ax=ax, color=COLORS[row.ZCTA5], linewidth=2, zorder=3)
        label = row.geometry.representative_point()
        ax.annotate(row.ZCTA5, (label.x, label.y), fontsize=13, fontweight='bold',
                    color=COLORS[row.ZCTA5], bbox={'facecolor': 'white', 'alpha': .9, 'edgecolor': 'none'}, zorder=5)
    if len(points):
        points.to_crs(26914).plot(ax=ax, color='#f97316', markersize=34, marker='*', edgecolor='white', linewidth=.3, zorder=4)
    ax.legend(handles=[Line2D([], [], marker='o', linestyle='', color='#0891b2', label='Walking nodes'),
                       Line2D([], [], color='#475569', label='Walking segments'),
                       Line2D([], [], marker='*', linestyle='', color='#f97316', label='Mapped places of interest')], loc='upper left')
    ax.set_title('EmPath walking network · 75025, 75024, 75074 & 75023', fontsize=17)
    ax.set_axis_off()
    fig.text(.12, .03, '© OpenStreetMap contributors · Census ZCTA boundaries · All mapped components shown\n'
             'POIs are mapped feature locations, not verified entrances. Network is not a validated sidewalk inventory.', fontsize=10)
    fig.savefig(output / 'walking_scope_map.png', dpi=180, bbox_inches='tight')
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT / 'output/four_zip_walking_network')
    p.add_argument('--refresh', action='store_true', help='Rebuild graph and POIs; OSMnx HTTP cache may still be reused')
    p.add_argument('--node-radius', type=float, default=3, help='Interactive node radius in pixels')
    args = p.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    scope = load_scope()
    polygon = scope.geometry.union_all()
    scope.to_file(output / 'zip_boundaries.geojson', driver='GeoJSON')
    ox.settings.cache_folder = ROOT / 'data/raw/osmnx_cache'
    ox.settings.use_cache = True
    ox.settings.log_console = True
    ox.settings.requests_timeout = 300
    ox.settings.useful_tags_way = list(dict.fromkeys(ox.settings.useful_tags_way +
        ['foot', 'sidewalk', 'crossing', 'surface', 'access', 'lit', 'incline']))
    graph_path = output / 'walking_network_all_components.graphml'
    if graph_path.exists() and not args.refresh:
        graph = ox.io.load_graphml(graph_path)
    else:
        graph = ox.graph.graph_from_polygon(polygon, network_type='walk', simplify=True,
                                           retain_all=True, truncate_by_edge=True)
        ox.io.save_graphml(graph, graph_path)
    components = sorted(nx.weakly_connected_components(graph), key=len, reverse=True)
    connected = graph.subgraph(components[0]).copy()
    if args.refresh or not (output / 'walking_network_connected.graphml').exists():
        ox.io.save_graphml(connected, output / 'walking_network_connected.graphml')
    if args.refresh or not (output / 'walking_network.gpkg').exists():
        ox.io.save_graph_geopackage(graph, output / 'walking_network.gpkg', directed=True)
    nodes, edges = ox.convert.graph_to_gdfs(graph)
    if args.refresh or not (output / 'nodes.csv').exists():
        nodes.drop(columns='geometry').to_csv(output / 'nodes.csv')
    if args.refresh or not (output / 'edges.csv').exists():
        edges.to_csv(output / 'edges.csv')
    per_zip = []
    for _, row in scope.iterrows():
        inside = nodes.geometry.intersects(row.geometry)
        per_zip.append({'zcta': row.ZCTA5, 'mapped_nodes': int(inside.sum()),
                        'nodes_in_largest_component': int(nodes.index[inside].isin(connected.nodes).sum())})
    if any(row['mapped_nodes'] == 0 for row in per_zip):
        raise RuntimeError('At least one ZCTA has no graph nodes; inspect extraction before proceeding')
    poi_path = output / 'places_of_interest.geojson'
    pois = (gpd.read_file(poi_path) if poi_path.exists() and not args.refresh else fetch_pois(polygon, poi_path))
    summary = {'source': '© OpenStreetMap contributors', 'scope_zctas': ZIPCODES,
               'scope': 'Full cached Census ZCTA footprints, including any portions outside Collin County',
               'processed_at_utc': datetime.now(timezone.utc).isoformat(),
               'graph_created_at': graph.graph.get('created_date'), 'osmnx_version': ox.__version__,
               'nodes': len(graph), 'directed_edges': graph.number_of_edges(),
               'component_count': len(components), 'component_node_counts': [len(c) for c in components],
               'connected_nodes': len(connected), 'connected_directed_edges': connected.number_of_edges(),
               'per_zcta': per_zip, 'poi_features': len(pois),
               'limitations': ['All components retained for geographic coverage; largest connected graph exported separately.',
                               'Boundary-adjacent nodes outside the ZCTAs may be retained to preserve crossing edges.',
                               'No artificial links added between disconnected components.',
                               'OSM walking filter does not establish sidewalk completeness, crossing safety or legal access.',
                               'POI representative points are not verified entrances or graph connections.',
                               'POI categories are a selected inventory, not an exhaustive destination dataset.']}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    create_maps(graph, scope, pois, output, args.node_radius)
    print(json.dumps(summary, indent=2), flush=True)
    print(f'Interactive map: {output / "walking_scope_map.html"}', flush=True)


if __name__ == '__main__':
    main()
