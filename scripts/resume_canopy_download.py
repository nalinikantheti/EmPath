"""Finish a cached Zenodo canopy ZIP with verified HTTP byte ranges and MD5."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from clip_texas_canopy import URL, MD5, ROOT


def main():
    folder=ROOT/'data/raw/texas_canopy_2021';folder.mkdir(parents=True,exist_ok=True)
    archive=folder/'TX_10m_canopy_cover_2021.zip'
    if archive.exists():
        print('Archive already exists; clipping script verifies its MD5.');return
    partial=archive.with_suffix('.zip.part')
    start=partial.stat().st_size if partial.exists() else 0
    with requests.get(URL,headers={'Range':'bytes=0-0'},stream=True,timeout=40) as r:
        r.raise_for_status()
        if r.status_code!=206:raise RuntimeError('Range requests not supported')
        total=int(r.headers['Content-Range'].split('/')[-1])
    parts=folder/'range_parts';parts.mkdir(exist_ok=True)
    ranges=[(a,min(a+64*1024*1024,total)-1) for a in range(start,total,64*1024*1024)]
    def fetch(pair):
        a,b=pair;path=parts/f'{a:012d}_{b:012d}.bin'
        if path.exists() and path.stat().st_size==b-a+1:return path
        session=requests.Session();session.mount('https://',HTTPAdapter(max_retries=Retry(total=4,backoff_factor=2,status_forcelist=[429,500,502,503,504])))
        with session.get(URL,headers={'Range':f'bytes={a}-{b}'},stream=True,timeout=(30,180)) as r:
            r.raise_for_status()
            if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {a}-{b}/{total}':
                raise RuntimeError('Unexpected byte range; no assembly performed')
            tmp=path.with_suffix('.partial')
            with tmp.open('wb') as f:
                for chunk in r.iter_content(4*1024*1024):f.write(chunk)
            if tmp.stat().st_size!=b-a+1:raise RuntimeError('Incomplete range')
            tmp.replace(path)
        print(f'Range finished {a/1e6:.0f}–{(b+1)/1e6:.0f} MB',flush=True)
        return path
    print(f'Resume prefix: {start/1e6:.0f} MB; remaining {(total-start)/1e6:.0f} MB',flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:files=list(pool.map(fetch,ranges))
    assembled=archive.with_suffix('.assembled')
    with assembled.open('wb') as dst:
        if partial.exists():
            with partial.open('rb') as src:shutil.copyfileobj(src,dst,8*1024*1024)
        for p in files:
            with p.open('rb') as src:shutil.copyfileobj(src,dst,8*1024*1024)
    digest=hashlib.md5()
    with assembled.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):digest.update(chunk)
    if assembled.stat().st_size!=total or digest.hexdigest()!=MD5:
        raise ValueError('Archive MD5 mismatch; cached inputs preserved for inspection')
    assembled.replace(archive)
    (folder/'download_verified.json').write_text(json.dumps({'url':URL,'bytes':total,'md5':MD5},indent=2))
    print('Canopy ZIP complete; checksum verified.',flush=True)

if __name__=='__main__':main()
