"""Certify search-extent sufficiency for bounded public walks under the fixed model.
No assertion of real-world POI completeness, verified access, or preference accuracy.
"""
from pathlib import Path
import json
import geopandas as gpd,pandas as pd,numpy as np
from city_scope import buffer_m
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/plano_city/accessibility';DEST=ROOT/'netlify_site/src/data'
def run():
 b=gpd.read_file(OUT/'block_accessibility.gpkg').to_crs(26914);node=pd.read_csv(ROOT/'output/plano_city/network/nodes.csv').set_index('osmid')
 coords=node.loc[b.access_network_node.astype(int)]
 points=gpd.GeoSeries(gpd.points_from_xy(coords.x,coords.y),crs=4326).to_crs(26914).reset_index(drop=True)
 area=gpd.read_file(ROOT/'output/plano_city/environment_context.gpkg').to_crs(26914).geometry.union_all()
 costs=pd.read_csv(ROOT/'output/plano_city/friction/block_proxy_edge_costs.csv');assert costs.block_proxy_cost_s.notna().all()
 assert (costs.block_proxy_cost_s>=costs['length']/1.2-1e-8).all()
 # Verify the 1% projection safety allowance against every current source edge.
 e=gpd.read_file(ROOT/'output/plano_city/network/edges.gpkg').to_crs(26914)
 ratio=e['length']/e.geometry.length.where(lambda x:x>0);minimum=float(ratio.min());assert minimum>=.99
 b['boundary_exit_lower_bound_min']=np.where(points.within(area),points.distance(area.boundary)*.99/1.2/60,0)
 b['public_30min_extent_sufficient']=b.boundary_exit_lower_bound_min.gt(30)
 housing=pd.to_numeric(b.HU100).gt(0)&b.access_snap_gap_m.le(100)
 assert b.loc[housing,'public_30min_extent_sufficient'].all(),'Some eligible origins require a smaller budget or wider scope'
 d=pd.read_csv(OUT/'nearest_category_costs.csv',dtype={'GEOID20':str});bound=b.set_index('GEOID20').boundary_exit_lower_bound_min
 d['boundary_exit_lower_bound_min']=d.GEOID20.map(bound);d['extent_certified_cost']=d.min_friction_equivalent_minutes.lt(d.boundary_exit_lower_bound_min)
 d.to_csv(OUT/'nearest_category_costs.csv',index=False)
 b.to_file(OUT/'block_accessibility.gpkg',driver='GPKG',index=False);b.drop(columns='geometry').to_csv(OUT/'block_accessibility.csv',index=False)
 old=pd.read_csv(ROOT/'output/plano_city/prior_1km/nearest_category_costs.csv',dtype={'GEOID20':str})
 change=old[['GEOID20','category','min_friction_equivalent_minutes']].merge(d[['GEOID20','category','min_friction_equivalent_minutes']],on=['GEOID20','category'],suffixes=('_1km','_3km'),validate='one_to_one');change['reduction_equiv_min']=change.min_friction_equivalent_minutes_1km-change.min_friction_equivalent_minutes_3km
 change.to_csv(DEST/'weighted_boundary_before_after.csv',index=False)
 report={'production_buffer_m':buffer_m(),'fully_weighted_edges':len(costs),'unknown_weight_edges':int(costs.block_proxy_cost_s.isna().sum()),'city_blocks':len(b),'eligible_housing_and_connection_blocks':int(housing.sum()),'public_budget_choices_minutes':[10,20,30],'public_max_effort_minutes':30,'all_eligible_origins_extent_sufficient_for_30min':bool(b.loc[housing,'public_30min_extent_sufficient'].all()),'minimum_eligible_exit_lower_bound_minutes':float(b.loc[housing,'boundary_exit_lower_bound_min'].min()),'minimum_source_length_to_projected_geometry_length_ratio':minimum,'conservative_projection_factor':.99,
 'proof':'Every edge cost is at least length / 1.2 m/s. Any route to a candidate outside the expanded geometry must first reach its boundary. A conservative lower bound is 0.99 * projected distance from the actual snapped origin to that boundary / 1.2 / 60. If the per-destination effort budget is below this bound, no outside candidate or outside detour can improve a qualifying result, and none can be reached within that budget under this fixed model.',
 'what_was_corrected':'Network, destination catalog, GeoAI canopy predictions, traffic context, Landsat summaries and edge weights were extended together to 3 km. All city category costs and routes were recomputed. The public tool uses bounded walks with an origin-specific extent check; it does not merely renormalize outer blocks.',
 'qualifications':['Sufficiency is for the search extent under the current graph/catalog and proxy cost model, not proof that all real-world POIs, entrances or paths are mapped.','Block and entrance snap connectors/crossing waits remain excluded. Model predictions and block proxies remain uncertain.','Trips exceeding the origin-specific exit lower bound are not certified; unrestricted advanced-map comparisons may retain extent effects.','Before/after changes include re-extraction/aggregation of expanded environmental context as well as routing/destination expansion; they are not a controlled estimate of the boundary effect alone.'],
 'weighted_before_after':{'matched_pairs':len(change),'pairs_lower_by_more_than_one_equiv_min':int(change.reduction_equiv_min.gt(1).sum()),'pairs_higher_by_more_than_one_equiv_min':int(change.reduction_equiv_min.lt(-1).sum()),'largest_reduction_equiv_min':float(change.reduction_equiv_min.max())}}
 for folder in [OUT,DEST]:(folder/'boundary_corrected_method.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
