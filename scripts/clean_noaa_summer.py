"""NOAA GHCNh regional summer-afternoon scenario, not a local heat raster."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly'
STATION='USW00003970'  # Dallas Addison airport; regional context, not each block.
YEAR=2025
ALLOWED_QC={'','0','1','4','5','9'}


def summarize(frame):
    d=frame.copy()
    d['time_utc']=pd.to_datetime(d.DATE,utc=True,errors='coerce')
    d['time_local']=d.time_utc.dt.tz_convert('America/Chicago')
    d=d[d.time_local.dt.year.eq(YEAR)&d.time_local.dt.month.isin([6,7,8])&
        d.time_local.dt.hour.ge(12)&d.time_local.dt.hour.lt(18)].copy()
    if d.empty:raise ValueError('No observations in requested local summer window')
    rejected={}
    for col,bounds in {'temperature':(-90,65),'dew_point_temperature':(-100,65),
                       'wind_speed':(0,150),'relative_humidity':(0,100)}.items():
        vals=pd.to_numeric(d[col],errors='coerce')
        qc=d[col+'_Quality_Code'].fillna('').astype(str).str.strip()
        good=qc.isin(ALLOWED_QC)&vals.between(*bounds)&np.isfinite(vals)
        rejected[col]=int((~good).sum())
        d[col]=vals.where(good)
    d['local_hour']=d.time_local.dt.floor('h')
    cols=['temperature','dew_point_temperature','wind_speed','relative_humidity']
    hourly=d.groupby('local_hour')[cols].median().reset_index()
    # Subhourly reports do not get extra weight in summer scenario statistics.
    stats={}
    for col in cols:
        v=hourly[col].dropna()
        stats[col]={'median':float(v.median()) if len(v) else None,
                    'p90':float(v.quantile(.9)) if len(v) else None,'valid_hours':len(v)}
    return d,hourly,{'rows_in_window':len(d),'hourly_statistics':stats,'masked_values':rejected,
        'expected_hours':92*6,'valid_temperature_hour_fraction':stats['temperature']['valid_hours']/(92*6)}


def main():
    raw=ROOT/'data/raw/noaa_ghcnh';out=ROOT/'data/processed/noaa_summer_2025'
    raw.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    url=f'{BASE}/access/by-year/{YEAR}/psv/GHCNh_{STATION}_{YEAR}.psv'
    path=raw/f'GHCNh_{STATION}_{YEAR}.psv'
    if not path.exists():
        session=requests.Session();session.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=1,status_forcelist=[429,500,502,503,504])))
        with session.get(url,stream=True,timeout=(30,120)) as r:
            r.raise_for_status();tmp=path.with_suffix('.partial')
            with tmp.open('wb') as f:
                for chunk in r.iter_content(1024*1024):f.write(chunk)
            tmp.replace(path)
    frame=pd.read_csv(path,sep='|',dtype=str)
    selected,hourly,stats=summarize(frame)
    selected.to_csv(out/'selected_observations.csv',index=False)
    hourly.to_csv(out/'hourly_clean.csv',index=False)
    metadata={'source':url,'station':STATION,'station_name':str(frame.Station_name.iloc[0]),
        'station_coordinates':{'lat':float(frame.LATITUDE.iloc[0]),'lon':float(frame.LONGITUDE.iloc[0])},
        'year':YEAR,'months':[6,7,8],'local_start_hour':12,'local_end_hour_exclusive':18,
        'timezone':'America/Chicago','raw_rows':len(frame),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'processed_utc':datetime.now(timezone.utc).isoformat(),'units':{'temperature':'C','dew_point_temperature':'C','wind_speed':'m/s','relative_humidity':'percent'},
        'qc_policy':'Retain blank and legacy 0/1/4/5/9; mask failure/other codes; blanks not proof of a passed check.',
        'aggregation':'Median within local hour, then median/p90 across hourly values. Variables summarized independently, not a coincident multivariate extreme.',
        'limitation':'One airport station is regional context; no spatial temperature differences between blocks or edges are inferred.',**stats}
    (out/'summer_scenario.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2),flush=True)

if __name__=='__main__':main()
