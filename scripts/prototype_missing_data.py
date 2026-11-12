"""Explicit available-factor prototype and pessimistic missing-data sensitivity."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
FACTORS=['canopy_deficit_01','traffic_burden_01','temperature_burden_01']

def enrich_costs(frame):
 d=frame.copy()
 f=d[FACTORS].apply(pd.to_numeric,errors='coerce')
 f=f.where(np.isfinite(f)&f.ge(0)&f.le(1))
 d['known_factor_count']=f.notna().sum(axis=1)
 d['available_factor_burden_01']=f.mean(axis=1,skipna=True)
 d['prototype_friction_cost_s']=d.time_only_s*(1+d.available_factor_burden_01)
 # Separate explicit bound: missing burdens set to 1 as an assumption, never an observation.
 d['missing_high_burden_cost_s']=d.time_only_s*(1+f.fillna(1).mean(axis=1))
 d['estimated_weight']=d.known_factor_count.lt(3)
 d['missing_factors']=f.isna().apply(lambda r:', '.join(c for c in FACTORS if r[c]),axis=1)
 assert d.loc[d.known_factor_count.eq(0),'prototype_friction_cost_s'].isna().all()
 full=d.known_factor_count.eq(3)
 assert np.allclose(d.loc[full,'prototype_friction_cost_s'],d.loc[full,'scenario_lambda_1_0_cost_s'])
 assert d.available_factor_burden_01.dropna().between(0,1).all()
 assert (d.prototype_friction_cost_s.dropna()>=d.loc[d.prototype_friction_cost_s.notna(),'time_only_s']).all()
 assert (d.missing_high_burden_cost_s>=d.prototype_friction_cost_s.fillna(d.missing_high_burden_cost_s)-1e-8).all()
 proxy_path=ROOT/'output/step3_friction/block_proxy_edge_costs.csv'
 if proxy_path.exists() and 'block_proxy_cost_s' not in d:
  proxy=pd.read_csv(proxy_path,dtype={'block_canopy_deficit_01_nearby_geoid':str,'block_traffic_burden_01_nearby_geoid':str,'block_heat_burden_01_nearby_geoid':str})
  proxy=proxy.drop(columns=['length'],errors='ignore')
  d=d.merge(proxy,on=['u','v','key'],how='left',validate='one_to_one')
 return d

def run():
 out=ROOT/'output/step3_friction';d=enrich_costs(pd.read_csv(out/'edge_costs.csv'))
 d.to_csv(out/'prototype_edge_costs.csv',index=False)
 report={'formula':'time_only_s * [1 + sum(available normalized burdens) / number_of_available_factors]',
 'strict_formula':'time_only_s * [1 + (canopy_deficit + traffic_burden + heat_burden)/3], only if all known',
 'counts_by_known_factors':{str(k):int(v) for k,v in d.known_factor_count.value_counts().sort_index().items()},
 'missing_policy':'Do not fill observations. Average available factors for exploratory costs; no available factors gives unknown. Partial costs are marked estimated, not comparable evidence of equal quality.',
 'sensitivity':'Separate pessimistic scenario assumes burden=1 for missing factors. Test route changes rather than asserting estimated routes are best.',
 'unchanged':'Raw factors and strict costs remain intact. No new imagery inference or training. No change to 98% canopy coverage quality threshold.',
 'limits':'Available-factor routing can favor poorly observed edges. Dashed lines and route estimated-distance fractions expose this; pessimistic scenario is a sensitivity bound, not ground truth.',
 'checks':{'complete_case_equals_original':True,'unknown_not_replaced_with_zero':True,'costs_nonnegative':True,'all_unknown_prototype_cost_unknown':True}}
 (out/'prototype_missing_data_method.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':print(json.dumps(run(),indent=2))
