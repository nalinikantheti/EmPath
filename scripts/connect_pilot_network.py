"""Screen candidate connections and baseline routes; never certify pedestrian access."""
from pathlib import Path
import json
import geopandas as gpd
import pandas as pd
import networkx as nx
import osmnx as ox
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/network_connections'

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    graph=ox.load_graphml(ROOT/'output/clean_deliverables/walking_graph.graphml')
    graph=ox.project_graph(graph,to_crs=26914)
    nodes,edges=ox.graph_to_gdfs(graph)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(26914)
    blocks=gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg').to_crs(26914)
    pois=gpd.read_file(ROOT/'output/four_zip_walking_network/places_of_interest.geojson').to_crs(26914)
    template=OUT/'reviewed_locations.csv'
    if template.exists():
        locations=pd.read_csv(template)
        required={'location_id','role','longitude','latitude','entrance_verified'}
        if not required.issubset(locations):
            raise ValueError(f'Reviewed CSV needs {sorted(required)}')
        points=gpd.GeoDataFrame(locations,geometry=gpd.points_from_xy(locations.longitude,locations.latitude),crs=4326).to_crs(26914)
    else:
        rows=[]
        # One reproducible starting example per ZIP, not a residential inventory.
        for _,zone in scope.iterrows():
            eligible=blocks[(blocks.mapped_address_count>0)&blocks.geometry.representative_point().within(zone.geometry)]
            if eligible.empty: continue
            r=eligible.loc[eligible.geometry.representative_point().distance(zone.geometry.representative_point()).idxmin()]
            rows.append({'location_id':'block_'+str(r.GEOID20),'role':'origin','label':r.representative_address,'entrance_verified':False,'geometry':r.geometry.representative_point()})
        selected=pois[pois.category.isin(['pharmacy','supermarket','convenience','place_of_worship'])].copy()
        for i,r in selected.iterrows():
            rows.append({'location_id':f'poi_{i}','role':'destination','label':str(r.get('name',r.category)),'category':r.category,'entrance_verified':False,'geometry':r.geometry.representative_point()})
        points=gpd.GeoDataFrame(rows,crs=26914)
        ll=points.to_crs(4326)
        table=pd.DataFrame(points.drop(columns='geometry'));table['longitude']=ll.geometry.x;table['latitude']=ll.geometry.y
        table.to_csv(OUT/'candidate_locations.csv',index=False)
    if points.location_id.duplicated().any(): raise ValueError('Location IDs must be unique')
    nearest,dist=ox.distance.nearest_nodes(graph,points.geometry.x.to_numpy(),points.geometry.y.to_numpy(),return_dist=True)
    points['network_node']=nearest;points['connector_distance_m']=dist
    points['connection_status']=['review_nearby_node' if d<=100 else 'review_large_gap' for d in dist]
    # A nearby node does not prove a usable connection; no straight line is added to the graph.
    points.to_file(OUT/'candidate_connections.gpkg',driver='GPKG')
    points.drop(columns='geometry').to_csv(OUT/'candidate_connections.csv',index=False)
    pairs=[]
    for _,origin in points[points.role.eq('origin')].iterrows():
        distances=nx.single_source_dijkstra_path_length(graph,origin.network_node,weight='length')
        for _,dest in points[points.role.eq('destination')].iterrows():
            length=distances.get(dest.network_node)
            pairs.append({'origin':origin.location_id,'destination':dest.location_id,'network_reachable':length is not None,'network_distance_m':length,'baseline_network_minutes':None if length is None else length/1.2/60,'origin_gap_m':origin.connector_distance_m,'destination_gap_m':dest.connector_distance_m,'access_validated':False})
    pd.DataFrame(pairs).to_csv(OUT/'baseline_od_review.csv',index=False)
    report={'nodes':len(nodes),'directed_edges':len(edges),'weak_components':nx.number_weakly_connected_components(graph),'locations':len(points),'od_pairs':len(pairs),'unreachable_pairs':sum(not r['network_reachable'] for r in pairs),'note':'Provisional nearest-node screening, not verified entrances. Network-only times assume 1.2 m/s, exclude connector gaps and crossing waits. All alternatives retained. Review connections before accessibility claims.'}
    (OUT/'audit.json').write_text(json.dumps(report,indent=2))
    return report
if __name__=='__main__': print(json.dumps(run(),indent=2))
