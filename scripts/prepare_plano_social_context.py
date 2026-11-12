"""Official 2020 block density and 2024 ACS block-group context; never route costs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,requests,pandas as pd,numpy as np,geopandas as gpd
from prepare_plano_reference import fetch_features
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw/plano_social';OUT=ROOT/'output/plano_city/social';DEST=ROOT/'netlify_site/src/data'
ACS='https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/'
GEO='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2024/MapServer/10'
TABLES=['B25064','B25077','B19013','B25044','C17002','B01001','B03002']

def run():
 RAW.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 b=gpd.read_file(ROOT/'output/plano_city/accessibility/block_accessibility.gpkg').to_crs(26914);city=gpd.read_file(ROOT/'data/processed/plano_reference/plano_city_boundary.gpkg').to_crs(26914).geometry.union_all()
 # Earlier geometry caches did not retain every land-area attribute; refresh by stable GEOID.
 ids=b.GEOID20.astype(str).tolist();chunks=[ids[i:i+150] for i in range(0,len(ids),150)]
 def land(item):
  i,group=item;p=RAW/f'block_land_{i:02}.json'
  if not p.exists():
   r=requests.get('https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/tigerWMS_Census2020/MapServer/10/query',params={'f':'json','where':"GEOID IN ("+','.join("'"+v+"'" for v in group)+")",'outFields':'GEOID,AREALAND,POP100,HU100','returnGeometry':'false'},timeout=45);r.raise_for_status();data=r.json();assert 'error' not in data and not data.get('exceededTransferLimit');p.write_text(json.dumps(data))
  return [f['attributes'] for f in json.loads(p.read_text())['features']]
 with ThreadPoolExecutor(max_workers=4) as pool:rows=[r for chunk in pool.map(land,enumerate(chunks)) for r in chunk]
 lt=pd.DataFrame(rows);lt['GEOID20']=lt.GEOID.astype(str);assert set(lt.GEOID20)==set(ids) and lt.GEOID20.is_unique
 b=b.drop(columns=['AREALAND','POP100','HU100']);b=b.merge(lt[['GEOID20','AREALAND','POP100','HU100']],on='GEOID20',validate='one_to_one')
 detail=pd.read_csv(ROOT/'output/plano_city/accessibility/nearest_category_costs.csv',dtype={'GEOID20':str})
 pivot=detail.pivot(index='GEOID20',columns='category',values='min_friction_equivalent_minutes')[['supermarket','pharmacy','park']]
 means=pivot.mean(axis=1).where(pivot.notna().all(axis=1));b['comparison_walk_cost_min']=b.GEOID20.astype(str).map(means)
 gr=RAW/'geography';gr.mkdir(exist_ok=True)
 bg=fetch_features(GEO,b.to_crs(4326).total_bounds,[],gr,400).to_crs(26914);bg=bg[bg.intersects(city)].copy();bg['GEOID_BG']=bg.GEOID.astype(str);ids=set('1500000US'+x for x in bg.GEOID_BG)
 def fetch(table):
  p=RAW/(table+'.json')
  if p.exists():data=json.loads(p.read_text())
  else:
   r=requests.get(ACS+'acsdt5y2024-'+table.lower()+'.dat',stream=True,timeout=(20,120));r.raise_for_status();lines=r.iter_lines();header=next(lines).decode('utf-8-sig').split('|');data=[header]
   for line in lines:
    if line.split(b'|',1)[0].decode() in ids:data.append(line.decode().split('|'))
   assert len(data)>1,table
   p.write_text(json.dumps(data));print('ACS table:',table,len(data)-1,'block groups',flush=True)
  df=pd.DataFrame(data[1:],columns=data[0]);df['GEOID_BG']=df.GEO_ID.str.replace('1500000US','',regex=False)
  assert set(df.GEOID_BG)==set(bg.GEOID_BG),table+' coverage mismatch'
  for c in df:
   if c not in ['GEO_ID','GEOID_BG']:df[c]=pd.to_numeric(df[c],errors='coerce').where(lambda v:v>=0)
  return df.drop(columns='GEO_ID')
 with ThreadPoolExecutor(max_workers=3) as pool:
  for t in pool.map(fetch,TABLES):bg=bg.merge(t,on='GEOID_BG',validate='one_to_one')
 def col(table,num,kind='E'):return f'{table}_{kind}{num:03}'
 fields={}
 for name,table in [('median_gross_rent','B25064'),('median_home_value','B25077'),('median_household_income','B19013')]:
  bg[name]=bg[col(table,1)];bg[name+'_moe']=bg[col(table,1,'M')];fields[name]={'label':name.replace('_',' ').title()+' ($)','unit':'USD','moe_field':name+'_moe','source_table':table}
 specs={'no_vehicle_pct':('B25044',[3,10],1),'poverty_pct':('C17002',[2,3],1),'age65_pct':('B01001',list(range(20,26))+list(range(44,50)),1),'white_nonhispanic_pct':('B03002',[3],1),'black_nonhispanic_pct':('B03002',[4],1),'asian_nonhispanic_pct':('B03002',[6],1),'hispanic_latino_pct':('B03002',[12],1)}
 for name,(table,nums,den) in specs.items():
  numerator=bg[[col(table,i) for i in nums]].sum(axis=1,min_count=len(nums));nmoe=np.sqrt((bg[[col(table,i,'M') for i in nums]]**2).sum(axis=1,min_count=len(nums)));denom=bg[col(table,den)].where(lambda x:x>0);dmoe=bg[col(table,den,'M')]
  ratio=numerator/denom;bg[name]=100*ratio
  # Census proportion approximation; use addition fallback when subtraction radicand <0.
  a=nmoe**2-ratio**2*dmoe**2;bg[name+'_moe']=100*np.sqrt(a.where(a>=0,nmoe**2+ratio**2*dmoe**2))/denom
  fields[name]={'label':name.replace('_pct','').replace('_',' ').title()+' (%)','unit':'percent','moe_field':name+'_moe','source_table':table,'moe_note':'Approximate 90% ACS proportion MOE; numerator sums use RSS; no covariance available.'}
 for f in fields:
  if f.endswith('_pct'):assert bg[f].dropna().between(0,100).all(),f+' must be a proportion'
 for key,label in {'no_vehicle_pct':'Households without a vehicle (%)','poverty_pct':'Population below poverty threshold (%)','age65_pct':'Residents aged 65+ (%)','white_nonhispanic_pct':'White, non-Hispanic (%)','black_nonhispanic_pct':'Black, non-Hispanic (%)','asian_nonhispanic_pct':'Asian, non-Hispanic (%)','hispanic_latino_pct':'Hispanic / Latino, any race (%)'}.items():fields[key]['label']=label
 # Full-block land density attached to city-clipped geometry, never redistribute whole-block population.
 b['population_2020']=pd.to_numeric(b.POP100,errors='coerce');b['full_block_land_km2']=pd.to_numeric(b.AREALAND,errors='coerce')/1e6
 b['population_density']=b.population_2020/b.full_block_land_km2.where(b.full_block_land_km2>0);b['partial_city_block']=b.city_area_fraction.lt(.99)
 origin=b[['GEOID20','geometry']].copy();origin.geometry=origin.geometry.representative_point();joined=gpd.sjoin(origin,bg[['GEOID_BG','geometry']],how='left',predicate='intersects').drop_duplicates('GEOID20')
 b=b.merge(joined[['GEOID20','GEOID_BG']],on='GEOID20',validate='one_to_one')
 eligible=(pd.to_numeric(b.HU100)>0)&b.access_snap_gap_m.le(100)&b.comparison_walk_cost_min.notna()
 b['comparison_eligible']=eligible&~b.partial_city_block&b.population_density.notna()
 agg=b[eligible].groupby('GEOID_BG').agg(mean_context_equiv_min=('comparison_walk_cost_min','mean'),ranked_block_count=('GEOID20','size'))
 bg=bg.merge(agg,on='GEOID_BG',how='left');bg['city_geometry_fraction']=bg.geometry.intersection(city).area/bg.area
 bg.geometry=bg.geometry.intersection(city)
 good=eligible&~b.partial_city_block&b.population_density.notna()
 stats={'block_density_access_spearman':float(b.loc[good,'population_density'].rank().corr(b.loc[good,'comparison_walk_cost_min'].rank())),'density_matched_blocks':int(good.sum()),'block_groups':len(bg),'block_count':len(b),'partial_city_blocks':int(b.partial_city_block.sum()),'acs_missing_block_groups':int(bg.median_gross_rent.isna().sum()),'bg_context_correlations':{}}
 for f in ['median_gross_rent','median_home_value','median_household_income','no_vehicle_pct','poverty_pct','age65_pct']:
  valid=bg[f].notna()&bg.mean_context_equiv_min.notna()&bg.ranked_block_count.ge(5)
  stats['bg_context_correlations'][f]={'spearman':float(bg.loc[valid,f].rank().corr(bg.loc[valid,'mean_context_equiv_min'].rank())),'matched_block_groups':int(valid.sum())}
 # Disability is available at tract scale, not block-group scale.
 traw=RAW/'tract_geography';traw.mkdir(exist_ok=True)
 tr=fetch_features(GEO.replace('/10','/8'),b.to_crs(4326).total_bounds,[],traw,400).to_crs(26914);tr=tr[tr.intersects(city)].copy();tr['GEOID_TRACT']=tr.GEOID.astype(str)
 target=set('1400000US'+x for x in tr.GEOID_TRACT);cache=RAW/'B18101_tract.json'
 if not cache.exists():
  r=requests.get(ACS+'acsdt5y2024-b18101.dat',stream=True,timeout=(20,120));r.raise_for_status();it=r.iter_lines();head=next(it).decode('utf-8-sig').split('|');data=[head]
  for line in it:
   if line.split(b'|',1)[0].decode() in target:data.append(line.decode().split('|'))
  cache.write_text(json.dumps(data))
 data=json.loads(cache.read_text());dt=pd.DataFrame(data[1:],columns=data[0]);dt['GEOID_TRACT']=dt.GEO_ID.str.replace('1400000US','',regex=False)
 assert set(dt.GEOID_TRACT)==set(tr.GEOID_TRACT)
 for c in dt:
  if c not in ['GEO_ID','GEOID_TRACT']:dt[c]=pd.to_numeric(dt[c],errors='coerce').where(lambda v:v>=0)
 tr=tr.merge(dt,on='GEOID_TRACT',validate='one_to_one')
 nums=[4,7,10,13,16,19,23,26,29,32,35,38]
 numerator=tr[[f'B18101_E{i:03}' for i in nums]].sum(axis=1,min_count=len(nums));nmoe=np.sqrt((tr[[f'B18101_M{i:03}' for i in nums]]**2).sum(axis=1,min_count=len(nums)))
 denominator=tr.B18101_E001.where(lambda x:x>0);ratio=numerator/denominator;tr['disability_pct']=100*ratio
 a=nmoe**2-ratio**2*tr.B18101_M001**2;tr['disability_pct_moe']=100*np.sqrt(a.where(a>=0,nmoe**2+ratio**2*tr.B18101_M001**2))/denominator
 ta=b[eligible].assign(GEOID_TRACT=lambda x:x.GEOID_BG.str[:11]).groupby('GEOID_TRACT').agg(mean_context_equiv_min=('comparison_walk_cost_min','mean'),ranked_block_count=('GEOID20','size'))
 tr=tr.merge(ta,on='GEOID_TRACT',how='left');valid=tr.disability_pct.notna()&tr.mean_context_equiv_min.notna()&tr.ranked_block_count.ge(5)
 stats['bg_context_correlations']['disability_pct']={'spearman':float(tr.loc[valid,'disability_pct'].rank().corr(tr.loc[valid,'mean_context_equiv_min'].rank())),'matched_tracts':int(valid.sum()),'geography':'tract'}
 assert tr.disability_pct.dropna().between(0,100).all(),'Disability measure must be a count proportion, not an earnings table'
 tr.geometry=tr.geometry.intersection(city);tr['area_type']='2024 Census tract';tr['GEOID_BG']=tr.GEOID_TRACT
 fields['disability_pct']={'label':'Civilian noninstitutionalized population with a disability (%)','unit':'percent','moe_field':'disability_pct_moe','source_table':'B18101','geography':'tract','moe_note':'Approximate 90% proportion MOE.'}
 import gzip
 frame=tr[['GEOID_BG','NAME','area_type','disability_pct','disability_pct_moe','mean_context_equiv_min','ranked_block_count','geometry']]
 frame.drop(columns='geometry').to_csv(DEST/'social_tracts.csv',index=False)
 (DEST/'social_tracts.geojson.gz').write_bytes(gzip.compress(frame.to_crs(4326).to_json(drop_id=True).encode()));frame.to_file(OUT/'disability_tracts.gpkg',driver='GPKG',index=False)
 bgfields=[f for f in fields if f!='disability_pct']
 keep=['GEOID_BG','NAME','city_geometry_fraction','mean_context_equiv_min','ranked_block_count']+bgfields+[f+'_moe' for f in bgfields]
 bg[keep+['geometry']].to_file(OUT/'acs_context.gpkg',driver='GPKG',index=False)
 b[['GEOID20','population_2020','population_density','partial_city_block','comparison_eligible','GEOID_BG','comparison_walk_cost_min','geometry']].to_file(OUT/'population_density.gpkg',driver='GPKG',index=False)
 import gzip
 for name,frame in [('social_block_groups',bg[keep+['geometry']]),('population_blocks',b[['GEOID20','population_2020','population_density','partial_city_block','comparison_eligible','GEOID_BG','comparison_walk_cost_min','geometry']])]:
  frame=frame.copy();frame.geometry=frame.geometry.simplify(1,preserve_topology=True)
  blob=frame.to_crs(4326).to_json(drop_id=True).encode();(OUT/(name+'.geojson.gz')).write_bytes(gzip.compress(blob));(DEST/(name+'.geojson.gz')).write_bytes(gzip.compress(blob))
  frame.drop(columns='geometry').to_csv(DEST/(name+'.csv'),index=False)
 method={'acs_period':'2020–2024 ACS 5-year estimates','acs_source':ACS,'geometry_source':GEO,'population_period':'2020 decennial Census','density':'Full 2020 block population divided by full Census AREALAND. City-clipped border polygons flagged; population is not allocated to city fragments. Zero land area is unknown.','context':'ACS estimates and 90% margins of error belong to whole 2024 block groups (disability: Census tracts), including portions outside city; displayed geometry clipped for scope only. No block-level demographic/price inference.','affordability':'Median gross rent and owner-reported median home value, not current listings, transactions, appraisals or individual prices.','reference_profile':['supermarket','pharmacy','park'],'comparison':'Daily-place access score averaged over housing-positive blocks with snap<=100m; comparisons require >=5 such blocks per 2024 block group. Descriptive, ecological, unweighted across block origins, not causal or individual inference.','fields':fields,'statistics':stats,'safety':'Context fields do not enter route costs or personalized neighborhood ranking; no demographic suitability labels. Margins of error may be large; missing is gray, not zero.'}
 for folder in [OUT,DEST]:(folder/'social_context_method.json').write_text(json.dumps(method,indent=2,allow_nan=False))
 print(json.dumps(stats,indent=2));return method
if __name__=='__main__':run()
