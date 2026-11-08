"""Final Sentinel-2 processing port; original pixel mapping and mask retained."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,hashlib,csv,sys,warnings
import numpy as np,rasterio
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_bounds
from PIL import Image
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-root',type=Path,required=True,help='S2_SELECTED_ITEMS.json and native_windows directory')
parser.add_argument('--output-root',type=Path,required=True)
args=parser.parse_args();R=args.input_root.resolve(strict=True);D=R/'native_windows';O=args.output_root.resolve()
if O.exists() or O.is_relative_to(R) or R.is_relative_to(O) or O.is_relative_to(Path(__file__).resolve().parents[3]):
 raise ValueError('Use a new external output directory separate from input')
contract=json.loads((Path(__file__).resolve().parents[3]/'data/schema/sentinel2_processing_contract.json').read_text('utf-8'))
for relative,expected in contract['files'].items():
 if hashlib.sha256((R/relative).read_bytes()).hexdigest()!=expected:raise ValueError('Unqualified Sentinel input: '+relative)
O.mkdir(parents=True)
(O/'INPUT_SHA256.json').write_text(json.dumps(contract,indent=2),'utf-8')
xmin,xmax,ymin,ymax=[693223.2258440853,761117.4350810092,4071851.8866474433,4137938.3366950154]
extent=(xmin,ymin,xmax,ymax)
ledger=[]
def read(i,b):
 with rasterio.open(D/(i+'_'+b+'.tif')) as ds:return ds.read(1),ds.transform,ds.crs
def warp(a,tr,crs,shape,dt,dtype=None,method=Resampling.nearest,nodata=0,dst_crs='EPSG:25829'):
 target=np.full(shape,nodata,dtype=dtype or a.dtype)
 reproject(a,target,src_transform=tr,src_crs=crs,dst_transform=dt,dst_crs=dst_crs,resampling=method,src_nodata=nodata,dst_nodata=nodata,num_threads=2)
 return target
def save_tif(p,a,dt,nodata):
 arr=a if a.ndim==3 else a[None,...]
 pr=dict(driver='GTiff',width=arr.shape[-1],height=arr.shape[-2],count=arr.shape[0],dtype=str(a.dtype),crs='EPSG:25829',transform=dt,nodata=nodata,compress='deflate',tiled=True,blockxsize=256,blockysize=256)
 with rasterio.open(p,'w',**pr) as dst:dst.write(arr)
def render(name,rgb,count,dt,extra):
 # Fixed display mapping for both sensors. No histogram equalization or synthetic sharpening.
 valid=count>0
 disp=np.empty((rgb.shape[1],rgb.shape[2],4),dtype=np.uint8)
 for b in range(3):disp[:,:,b]=(np.power(np.clip(np.nan_to_num(rgb[b],nan=0)/0.30,0,1),1/1.6)*255).round().astype(np.uint8)
 disp[:,:,3]=valid.astype(np.uint8)*255
 Image.fromarray(disp,'RGBA').save(O/(name+'.png'),dpi=(300,300))
 save_tif(O/(name+'_REFLECTANCE.tif'),rgb,dt,np.nan)
 save_tif(O/(name+'_VALID_DATE_COUNT.tif'),count,dt,255)
 rec=dict(candidate=name,created_utc=datetime.now(timezone.utc).isoformat(),bounds=list(extent),crs='EPSG:25829',shape=list(count.shape),pixel_size=[dt.a,-dt.e],valid_pixels=int(valid.sum()),total_pixels=int(count.size),valid_fraction=float(valid.mean()),valid_date_count_histogram={str(k):int(v) for k,v in zip(*np.unique(count,return_counts=True))},display=dict(rgb='red,green,blue',reflectance_limits=[0,0.30],gamma=1.6,alpha='0 for no valid observation; 255 otherwise',upsampling='none beyond exact-extent nearest-neighbour registration'),**extra)
 for field in ['png','reflectance','valid_date_count']:
  suffix={'png':'.png','reflectance':'_REFLECTANCE.tif','valid_date_count':'_VALID_DATE_COUNT.tif'}[field]
  pp=O/(name+suffix);rec[field]=dict(path=pp.name,sha256=hashlib.sha256(pp.read_bytes()).hexdigest())
 (O/(name+'_QA.json')).write_text(json.dumps(rec,indent=2));print(json.dumps(rec,indent=2),flush=True)
 return rec
kind='s2'
if kind in ('s2','all'):
 fs=json.loads((R/'S2_SELECTED_ITEMS.json').read_text())
 width=math.ceil((xmax-xmin)/10);height=math.ceil((ymax-ymin)/10);shape=(height,width);dt=from_bounds(*extent,width,height)
 mosaic=np.full((3,*shape),np.nan,dtype='float32');support=np.zeros(shape,dtype='uint8');tilecoverage=np.zeros(shape,dtype='uint8')
 for f in fs:
  i=f['id'];r,tr,crs=read(i,'red');g,tg,cg=read(i,'green');b,tb,cb=read(i,'blue');scl,ts,cs=read(i,'scl')
  assert tr==tg==tb and crs==cg==cb and r.shape==g.shape==b.shape
  sq=warp(scl,ts,cs,r.shape,tr,dtype='uint8',dst_crs=crs)
  # Keep clear land/water/unclassified and dark pixels. Exclude no-data,
  # defective/saturated, cloud shadow, medium/high cloud, cirrus and snow.
  valid=np.isin(sq,[2,4,5,6,7])&(r>0)&(g>0)&(b>0)
  target=warp(valid.astype('uint8'),tr,crs,shape,dt)
  tilecoverage+=target
  use=(support==0)&(target==1)
  assert f['properties']['earthsearch:boa_offset_applied'] is True
  for k,band in enumerate((r,g,b)):
   sr=band.astype('float32')*0.0001;sr[~valid]=np.nan
   temp=warp(sr,tr,crs,shape,dt,dtype='float32',nodata=np.nan)
   mosaic[k,use]=temp[use]
  support[use]=1
  ledger.append(dict(sensor='Sentinel-2B',source_collection='EarthSearch sentinel-2-l2a',source_item=i,gee_collection='COPERNICUS/S2_SR_HARMONIZED',gee_counterpart='COPERNICUS/S2_SR_HARMONIZED/20220720T110629_20220720T110853_T'+i.split('_')[1],acquisition_datetime=f['properties']['datetime'],nominal_resolution_m=10,cloud_cover_catalog=f['properties']['eo:cloud_cover'],native_window_pixels=int(valid.size),native_window_valid_pixels=int(valid.sum()),registered_valid_tile_pixels=int(target.sum()),registered_pixels_contributed=int(use.sum()),valid_date_identity='2022-07-20',scale=0.0001,offset_applied_in_this_task=0,provider_offset_already_applied=True,mask='SCL in 2,4,5,6,7 and all RGB DN>0',role='Same-date geographic background; no independent repeat counts'))
  print('mosaicked',i,int(use.sum()),flush=True)
 assert np.array_equal(np.all(np.isfinite(mosaic),axis=0),support.astype(bool))
 save_tif(O/'SENTINEL2_20220720_VALID_TILE_COUNT.tif',tilecoverage,dt,255)
 render('SENTINEL2_20220720',mosaic,support,dt,dict(acquisition_dates=['2022-07-20'],source_tile_count=4,valid_observation_meaning='Distinct acquisition dates, 0 or 1. Overlapping tiles are not independent temporal observations.',processing='First valid pixel in fixed selected-item order, all four granules from one datatake. SCL nearest-neighbour from20m to10m. Reflectance scale0.0001, no second -0.1 offset because provider already harmonized.'))
# Separate ledgers support sequential runs before complete acquisition.
pp=O/(kind.upper()+'_IMAGE_LEDGER.csv')
with pp.open('w',newline='',encoding='utf-8-sig') as fh:
 w=csv.DictWriter(fh,fieldnames=list(ledger[0]));w.writeheader();w.writerows(ledger)
print('PROCESSING_COMPLETE',kind,flush=True)

if hashlib.sha256((O/'SENTINEL2_20220720.png').read_bytes()).hexdigest()!=contract['expected_png_sha256']:
 raise ValueError('RGB output differs from final production identity')
if not all(hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in contract['files'].items()):
 raise ValueError('Input changed during rendering')
