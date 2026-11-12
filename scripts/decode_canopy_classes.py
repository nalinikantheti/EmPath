"""Decode the verified Texas canopy class key into explicit midpoint estimates."""
import hashlib,json,shutil
from pathlib import Path
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parents[1]
# Source key: 1=Not tree; 10=10–19%, ..., 80=80–89%, 90=>=90%.
MIDPOINTS={1:0.,**{v:v+4.5 for v in range(10,90,10)},90:95.}


def decode_classes(data):
    data=np.ma.asarray(data)
    valid=data.compressed()
    unexpected=set(np.unique(valid))-set(MIDPOINTS)
    if unexpected:raise ValueError(f'Unrecognized canopy class codes: {sorted(unexpected)}')
    result=np.zeros(data.shape,dtype='float32')
    for code,value in MIDPOINTS.items():result[data.data==code]=value
    return np.ma.array(result,mask=np.ma.getmaskarray(data))


def main():
    folder=ROOT/'output/canopy_2021';target=folder/'canopy_scope_2021.tif';raw=folder/'canopy_scope_2021_classes.tif'
    if not raw.exists():shutil.copy2(target,raw)
    with rasterio.open(raw) as src:
        result=decode_classes(src.read(1,masked=True));profile=src.profile
        profile.update(dtype='float32',nodata=-9999)
        with rasterio.open(target,'w',**profile) as dst:
            dst.write(result.filled(-9999),1)
            dst.update_tags(source='https://zenodo.org/records/8200761',vintage='2021',units='estimated percent canopy from class midpoints',
                class_key='TX_lu_ecoclass_key.xlsx canopy_key; 1=Not tree; 10=10–19%; ...; 90=>=90%',
                conversion='Not tree -> 0; decade classes -> midpoint; >=90 -> 95. Within-class estimates, not exact observed percent.')
    p=folder/'source_metadata.json';meta=json.loads(p.read_text())
    meta.update(raw_class_raster=str(raw.relative_to(ROOT)),raw_class_geotiff_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
        clipped_geotiff_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        value_semantics='Class midpoint estimates; 1 means Not tree, not 1% canopy.',
        verified_class_key='https://zenodo.org/records/8200761/files/TX_lu_ecoclass_key.xlsx',class_midpoints=MIDPOINTS)
    p.write_text(json.dumps(meta,indent=2))
    print('Decoded canopy class codes into explicitly labeled midpoint estimates.')

if __name__=='__main__':main()
