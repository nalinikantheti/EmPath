"""Run pretrained Restor TCD tree segmentation on four small NAIP demo areas.
No Google imagery, no training from scratch, and no changes to the production graph.
"""
from pathlib import Path
import os,importlib.util
# Use Rasterio's matching PROJ database rather than an inherited Conda database.
_rasterio_dir=Path(importlib.util.find_spec("rasterio").origin).parent
if (_rasterio_dir/"proj_data/proj.db").exists(): os.environ["PROJ_DATA"]=str(_rasterio_dir/"proj_data")
import json,hashlib
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from rasterio.features import shapes,geometry_mask
from shapely.geometry import box,shape,mapping,LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/vegetation_geoai'
MODEL_ID='restor/tcd-segformer-mit-b0'
CRS=26914

def get_json(url,**kwargs):
    r=requests.get(url,timeout=90,**kwargs);r.raise_for_status();return r.json()

def acquire_demo_imagery(size=1536,res=.6):
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=OUT/'imagery_manifest.json'
    if manifest.exists():return json.loads(manifest.read_text())
    scope=gpd.read_file(ROOT/'output/four_zip_walking_network/zip_boundaries.geojson').to_crs(CRS)
    pois=gpd.read_file(ROOT/'output/four_zip_walking_network/places_of_interest.geojson').to_crs(CRS)
    records=[]
    for _,z in scope.sort_values('ZCTA5').iterrows():
        cached_meta=OUT/f'imagery_{z.ZCTA5}_metadata.json'
        if cached_meta.exists():
            records.append(json.loads(cached_meta.read_text()));continue
        candidates=pois[pois.category.isin(['pharmacy','supermarket']) & pois.geometry.representative_point().within(z.geometry)]
        center=z.geometry.representative_point()
        if len(candidates):center=candidates.geometry.representative_point().iloc[np.argmin(candidates.geometry.representative_point().distance(center))]
        extent=box(center.x-size*res/2,center.y-size*res/2,center.x+size*res/2,center.y+size*res/2)
        bbox=gpd.GeoSeries([extent],crs=CRS).to_crs(4326).total_bounds.tolist()
        results=get_json('https://planetarycomputer.microsoft.com/api/stac/v1/search',params={'collections':'naip','bbox':','.join(map(str,bbox)),'limit':100})['features']
        if not results:raise RuntimeError('No NAIP items returned for '+str(z.ZCTA5))
        year=max(int(f['properties']['naip:year']) for f in results)
        chosen=[f for f in results if int(f['properties']['naip:year'])==year]
        transform=from_origin(extent.bounds[0],extent.bounds[3],res,res)
        rgb=np.zeros((3,size,size),dtype=np.uint8);valid=np.zeros((size,size),dtype=bool)
        used=[]
        for item in chosen:
            href=item['assets']['image']['href']
            signed=get_json('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':href})['href']
            with rasterio.open(signed) as src:
                with WarpedVRT(src,crs=f'EPSG:{CRS}',transform=transform,width=size,height=size,resampling=Resampling.bilinear,nodata=0) as vrt:
                    tile=vrt.read([1,2,3],masked=True)
                    ok=~np.ma.getmaskarray(tile).any(axis=0)
                    rgb[:,ok]=tile.data[:,ok];valid|=ok
            used.append({'id':item['id'],'date':item['properties']['datetime'],'source_url':href,'native_resolution_m':item['properties'].get('gsd')})
        path=OUT/f'naip_{z.ZCTA5}.tif'
        with rasterio.open(path,'w',driver='GTiff',height=size,width=size,count=3,dtype='uint8',crs=CRS,transform=transform,nodata=0,compress='deflate') as dst:
            dst.write(rgb);dst.write_mask(valid.astype('uint8')*255)
        records.append({'zip':str(z.ZCTA5),'image':str(path.relative_to(ROOT)),'year':year,'items':used,'resolution_m':res,'valid_fraction':float(valid.mean()),'extent_m':list(extent.bounds),'attribution':'USDA NAIP public-domain aerial imagery, accessed through Microsoft Planetary Computer','scope':'Small demonstration tile; NOT complete ZIP coverage'})
        cached_meta.write_text(json.dumps(records[-1],indent=2))
        print('Imagery saved for',z.ZCTA5,flush=True)
    manifest.write_text(json.dumps(records,indent=2));return records

def load_model():
    from transformers import AutoImageProcessor,SegformerForSemanticSegmentation
    import torch
    cache=ROOT/'data/models/restor-tcd-b0';cache.mkdir(parents=True,exist_ok=True)
    info=get_json('https://huggingface.co/api/models/'+MODEL_ID)
    revision=info['sha']
    for name in ['config.json','preprocessor_config.json','model.safetensors']:
        p=cache/name
        if not p.exists():
            r=requests.get(f'https://huggingface.co/{MODEL_ID}/resolve/{revision}/{name}',timeout=120);r.raise_for_status();p.write_bytes(r.content)
    processor=AutoImageProcessor.from_pretrained(cache)
    model=SegformerForSemanticSegmentation.from_pretrained(cache).eval()
    # CPU is the portable default for this project's existing Python environment.
    torch.set_num_threads(4)
    metadata={'model_id':MODEL_ID,'revision':revision,'weights_sha256':hashlib.sha256((cache/'model.safetensors').read_bytes()).hexdigest(),'classes':model.config.id2label,'device':'cpu','torch':torch.__version__,'trained_resolution_m':.1,'inference_resolution_m':.6,'domain_shift':'NAIP is coarser than the 10 cm model training imagery; predictions require local validation. No artificial upsampling claimed as extra detail.','model_card':'https://huggingface.co/'+MODEL_ID,'license_note':'Research demonstration. Review model card: SegFormer research terms and CC BY/NC training sources before deployment.'}
    (OUT/'model_provenance.json').write_text(json.dumps(metadata,indent=2))
    return processor,model

def segment_all(records):
    import torch
    processor,model=load_model()
    tile_size=512;stride=384
    for rec in records:
        out=OUT/f'tree_mask_{rec["zip"]}.tif'
        if out.exists():continue
        with rasterio.open(ROOT/rec['image']) as src:
            rgb=src.read([1,2,3]);valid=src.dataset_mask()>0;profile=src.profile.copy()
        h,w=valid.shape;total=np.zeros((h,w),dtype=np.float32);counts=np.zeros((h,w),dtype=np.uint16)
        ys=sorted(set(list(range(0,max(1,h-tile_size+1),stride))+[max(0,h-tile_size)]))
        xs=sorted(set(list(range(0,max(1,w-tile_size+1),stride))+[max(0,w-tile_size)]))
        for y in ys:
            for x in xs:
                patch=np.moveaxis(rgb[:,y:y+tile_size,x:x+tile_size],0,-1)
                inputs=processor(images=patch,return_tensors='pt',do_resize=False)
                with torch.inference_mode():
                    logits=model(**inputs).logits
                    logits=torch.nn.functional.interpolate(logits,size=patch.shape[:2],mode='bilinear',align_corners=False)
                    prob=logits.softmax(dim=1)[0,1].cpu().numpy()
                total[y:y+patch.shape[0],x:x+patch.shape[1]]+=prob
                counts[y:y+patch.shape[0],x:x+patch.shape[1]]+=1
        probability=total/np.maximum(counts,1)
        profile.update(count=1,dtype='float32',nodata=-9999)
        with rasterio.open(OUT/f'tree_probability_{rec["zip"]}.tif','w',**profile) as dst:dst.write(np.where(valid,probability,-9999).astype('float32'),1)
        profile.update(dtype='uint8',nodata=255)
        with rasterio.open(out,'w',**profile) as dst:dst.write(np.where(valid,probability>=.5,255).astype('uint8'),1)
        print('AI inference completed for',rec['zip'],flush=True)

def vectorize_and_measure(records):
    edges=gpd.read_file(ROOT/'output/clean_deliverables/walking_edges.gpkg').to_crs(CRS)
    blocks=gpd.read_file(ROOT/'output/clean_deliverables/block_environment.gpkg').to_crs(CRS)
    all_polys=[];all_edges=[];all_blocks=[]
    for rec in records:
        with rasterio.open(OUT/f'tree_mask_{rec["zip"]}.tif') as src:
            mask=src.read(1);valid=mask!=255;transform=src.transform
            # Polygonize the actual inference output, not a colored screenshot.
            polygons=[shape(g) for g,v in shapes(mask,mask=(mask==1),transform=transform) if v==1]
            coverage=unary_union([shape(g) for g,v in shapes(valid.astype('uint8'),mask=valid,transform=transform) if v==1])
            extent=box(*src.bounds)
            areas=gpd.GeoDataFrame({'demo_zip':[rec['zip']]*len(polygons)},geometry=polygons,crs=CRS)
            if len(areas):all_polys.append(areas)
            subset=edges[edges.geometry.intersects(extent)].copy()
            def metric(geom):
                corridor=geom.buffer(5)
                zone=geometry_mask([mapping(corridor)],out_shape=mask.shape,transform=transform,invert=True)
                good=zone&valid
                expected=corridor.area/(rec['resolution_m']**2)
                fraction=min(1,float(good.sum()/expected)) if expected else 0
                mean=float((mask[good]==1).mean()) if good.any() else np.nan
                return mean,fraction
            values=[metric(g) for g in subset.geometry]
            subset['ai_tree_cover_01']=[v[0] for v in values]
            subset['imagery_corridor_coverage_01']=[v[1] for v in values]
            subset['complete_corridor']=subset.geometry.buffer(5).map(coverage.covers)
            subset['demo_zip']=rec['zip'];subset['ai_canopy_gap_proxy_m']=subset['length']*(1-subset.ai_tree_cover_01)
            # These scores use canopy proximity, not actual shadow or measured sun exposure.
            all_edges.append(subset)
            b=blocks[blocks.geometry.intersects(extent)].copy()
            means=[];fractions=[]
            for geom in b.geometry:
                zone=geometry_mask([mapping(geom)],out_shape=mask.shape,transform=transform,invert=True);good=zone&valid
                means.append(float((mask[good]==1).mean()*100) if good.any() else np.nan)
                fractions.append(min(1,float(good.sum()*rec['resolution_m']**2/geom.area)) if geom.area else 0)
            b['ai_tree_percent_observed_part']=means;b['imagery_block_coverage_01']=fractions;b['demo_zip']=rec['zip']
            all_blocks.append(b[['GEOID20','demo_zip','ai_tree_percent_observed_part','imagery_block_coverage_01','geometry']])
    trees=gpd.GeoDataFrame(pd.concat(all_polys,ignore_index=True),crs=CRS) if all_polys else gpd.GeoDataFrame({'demo_zip':[]},geometry=[],crs=CRS)
    tree_edges=gpd.GeoDataFrame(pd.concat(all_edges,ignore_index=True),crs=CRS)
    block_parts=gpd.GeoDataFrame(pd.concat(all_blocks,ignore_index=True),crs=CRS)
    trees.to_file(OUT/'predicted_tree_polygons.gpkg',driver='GPKG')
    tree_edges.to_file(OUT/'ai_walking_edges.gpkg',driver='GPKG')
    block_parts.to_file(OUT/'observed_block_parts.gpkg',driver='GPKG')
    tree_edges.drop(columns='geometry').to_csv(OUT/'ai_walking_edges.csv',index=False)
    return trees,tree_edges,block_parts

if __name__=='__main__':
    records=acquire_demo_imagery();segment_all(records);vectorize_and_measure(records)
