"""Recover a local canopy clip from an interrupted source ZIP.

Only use an existing prefix of this exact archive. The small IMG member is
CRC-verified by zipfile. Incomplete IGE data are never padded: GDAL read errors
abort the local clip. This does NOT verify the full archive's MD5.
"""
import io
import json
import hashlib
import logging
from pathlib import Path
import struct
import zipfile
import zlib
import requests
import geopandas as gpd
import rasterio
from clip_texas_canopy import ROOT, URL, clip_one

class RemoteZip(io.RawIOBase):
    def __init__(self):
        self.pos=0;self.session=requests.Session()
        with self.session.get(URL,headers={'Range':'bytes=0-0'},stream=True,timeout=40) as r:
            r.raise_for_status()
            if r.status_code!=206:raise RuntimeError('Server does not support byte ranges')
            self.length=int(r.headers['Content-Range'].split('/')[-1])
    def seekable(self):return True
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.length+offset
        return self.pos
    def tell(self):return self.pos
    def read(self,n=-1):
        n=min(self.length-self.pos,n if n>=0 else self.length-self.pos)
        if n<=0:return b''
        a=self.pos;b=a+n-1
        r=self.session.get(URL,headers={'Range':f'bytes={a}-{b}'},timeout=60);r.raise_for_status()
        if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {a}-{b}/{self.length}':
            raise ValueError('Byte-range response mismatch')
        self.pos+=len(r.content);return r.content

class ReadError(logging.Handler):
    def emit(self,record):
        if record.levelno>=logging.ERROR:raise RuntimeError('GDAL read error: '+record.getMessage())


def main():
    partial=ROOT/'data/raw/texas_canopy_2021/TX_10m_canopy_cover_2021.zip.part'
    if not partial.exists():raise FileNotFoundError('No cached prefix. Use the normal full-download/Colab workflow.')
    raw=ROOT/'data/raw/texas_canopy_partial';raw.mkdir(parents=True,exist_ok=True)
    img=raw/'TX_10m_canopy_cover_2021.img';ige=raw/'TX_10m_canopy_cover_2021.ige'
    if not img.exists():
        with zipfile.ZipFile(RemoteZip()) as z:img.write_bytes(z.read('TX_10m_canopy_cover_2021.img'))
    metadatafile=raw/'prefix_metadata.json'
    cached=json.loads(metadatafile.read_text()) if metadatafile.exists() else {}
    if not ige.exists() or cached.get('compressed_prefix_bytes')!=partial.stat().st_size:
        with partial.open('rb') as src,ige.open('wb') as dst:
            v=struct.unpack('<I5H3I2H',src.read(30));name=src.read(v[-2]);src.read(v[-1])
            if name!=b'TX_10m_canopy_cover_2021.ige' or v[3]!=8:raise ValueError('Unexpected ZIP layout')
            decoder=zlib.decompressobj(-15)
            for chunk in iter(lambda:src.read(4*1024*1024),b''):dst.write(decoder.decompress(chunk))
        metadatafile.write_text(json.dumps({'compressed_prefix_bytes':partial.stat().st_size,
            'uncompressed_prefix_bytes':ige.stat().st_size,'complete':decoder.eof},indent=2))
    output=ROOT/'output/canopy_2021';output.mkdir(parents=True,exist_ok=True)
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson')
    handler=ReadError();logger=logging.getLogger('rasterio');logger.addHandler(handler)
    target=output/'canopy_scope_2021.tif'
    try:
        with rasterio.open(img) as src:
            data,transform=clip_one(src,scope.to_crs(src.crs).geometry.tolist(),target,class_coded=True)
            info={'source':URL,'vintage':2021,'source_resolution':list(src.res),'source_crs':str(src.crs),
                'scope':scope.ZCTA5.tolist(),'collin_county_only':False,'valid_pixels':int(data.count()),
                'source_nodata':src.nodata,'img_metadata_crc_verified':True,'archive_checksum_verified':False,
                'download_method':'Local pixels recovered from decompressed cached ZIP prefix. GDAL read errors abort; missing IGE bytes not padded. Full statewide archive checksum unverified.',
                'clipped_geotiff_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        (output/'source_metadata.json').write_text(json.dumps(info,indent=2))
    finally:logger.removeHandler(handler)
    print('Local canopy clip complete; full archive checksum remains unverified.',flush=True)

if __name__=='__main__':main()
