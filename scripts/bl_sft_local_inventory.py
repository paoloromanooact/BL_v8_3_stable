"""Read-only local inventory for the BL SFT pilot. Filenames, stat, JSON keywords and selected FITS headers only.
No image arrays, tilt columns, flux measurements, Q4 output, network or simulation are read/executed.
Writes only an explicitly supplied JSON inventory path.
"""
import argparse,collections,datetime,hashlib,json,os,re,shutil
from pathlib import Path
import numpy as np,pandas as pd
from astropy.io import fits
ROOT=Path(__file__).resolve().parents[1]
PAT=re.compile(r'^hmi\.sharp_cea_720s\.(\d+)\.(\d{8})_(\d{6})_TAI\.(Br|bitmap)\.fits$')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scan(folder):
 records={};counts=collections.Counter();sizes=collections.Counter();errors=[];others=collections.Counter()
 def err(e):errors.append(dict(path=e.filename,error=type(e).__name__))
 for base,dirs,files in os.walk(folder,onerror=err):
  dirs.sort()
  for n in sorted(files):
   p=Path(base)/n;m=PAT.match(n)
   if not m:others[p.suffix]+=1;continue
   harp,date,time,seg=m.groups();key=(harp,date,time);records.setdefault(key,{})[seg]=str(p)
   counts[seg]+=1
   try:sizes[seg]+=p.stat().st_size
   except OSError as e:err(e)
 return records,dict(counts),dict(sizes),errors,dict(others)
def main(out):
 if Path(out).exists():raise SystemExit('refusing to overwrite an existing inventory')
 inventory=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),root=str(ROOT),scope='filenames/stat, selection IDs, JSON keywords and deterministic FITS headers only',fits_arrays_read=False,tilt_columns_read=False,network_used=False,simulation_run=False)
 all_rec={};inventory['patch_collections']={}
 for rel in ['data/sharp/fits','data/sharp/fits_p3','data/sharp/test_20240508']:
  folder=ROOT/rel;rec,counts,sizes,errors,others=scan(folder)
  inventory['patch_collections'][rel]=dict(realpath=str(folder.resolve()),files=counts,bytes=sizes,records=len(rec),harps=len({k[0] for k in rec}),date_min=min((k[1] for k in rec),default=None),date_max=max((k[1] for k in rec),default=None),errors=errors,other_extensions=others)
  for k,v in rec.items():all_rec.setdefault(k,{}).update(v)
 primary_rec,_,_,_,_=scan(ROOT/'data/sharp/fits')
 selpath=ROOT/'results/P1/P1_RECORD_SELECTION.csv';sel=pd.read_csv(selpath,usecols=['HARPNUM','T_REC','role'],dtype={'HARPNUM':str})
 byrole={};missing=[]
 for role,g in sel.groupby('role'):
  count=0
  for r in g.itertuples():
   date,time=r.T_REC.removesuffix('_TAI').split('_');key=(r.HARPNUM,date.replace('.',''),time.replace(':',''));found=primary_rec.get(key,{})
   keyfile=Path(found['Br']).with_name(Path(found['Br']).name.removesuffix('.Br.fits')+'.keys.json') if 'Br' in found else None
   if set(found)=={'Br','bitmap'} and keyfile.exists():count+=1
   else:missing.append(dict(harp=r.HARPNUM,t_rec=r.T_REC,role=role,segments_present=sorted(found),keys_present=bool(keyfile and keyfile.exists())))
  byrole[role]=dict(selected=len(g),with_Br_bitmap_and_keys=count)
 inventory['selection']=dict(path=str(selpath),sha256=sha(selpath),rows=len(sel),harps=int(sel.HARPNUM.nunique()),by_role=byrole,missing=missing)
 byharp=collections.defaultdict(list)
 for k,v in all_rec.items():
  if set(v)=={'Br','bitmap'}:byharp[k[0]].append(datetime.datetime.strptime(k[1]+k[2],'%Y%m%d%H%M%S'))
 distribution=collections.Counter(len(set(v)) for v in byharp.values());gaps=[];span=[]
 for v in byharp.values():
  times=sorted(set(v));dt=np.diff(np.array(times,dtype='datetime64[s]')).astype('timedelta64[s]').astype(float)/86400.
  gaps.extend(dt.tolist())
  if len(times)>1:span.append((times[-1]-times[0]).total_seconds()/86400.)
 inventory['temporal_availability']=dict(note='Nominal T_REC in TAI; pooled local patches; availability only, not tracking or physical identity. Not a fixed-cadence time series.',harps_by_record_count={str(k):v for k,v in sorted(distribution.items())},harps_ge2=sum(n for k,n in distribution.items() if k>=2),harps_ge3=sum(n for k,n in distribution.items() if k>=3),harps_ge5=sum(n for k,n in distribution.items() if k>=5),consecutive_gaps_days_quantiles={str(q):float(np.quantile(gaps,q)) for q in [0,.25,.5,.75,1]} if gaps else {},harp_spans_days_quantiles={str(q):float(np.quantile(span,q)) for q in [0,.5,1]} if span else {})
 selected_times=sel.copy();selected_times['t']=pd.to_datetime(selected_times.T_REC.str.removesuffix('_TAI'),format='%Y.%m.%d_%H:%M:%S')
 pa=selected_times[selected_times.role=='primary'].set_index('HARPNUM').t;co=selected_times[selected_times.role=='control'].set_index('HARPNUM').t;dt=(co-pa).dt.total_seconds()/86400.
 inventory['primary_control_availability']=dict(paired_harps=len(dt),control_later=int((dt>0).sum()),control_earlier=int((dt<0).sum()),same_record_both=int((sel.role=='both').sum()),signed_dt_days_quantiles={str(q):float(dt.quantile(q)) for q in [0,.25,.5,.75,1]},later_at_least_days={str(v):int((dt>=v).sum()) for v in [1,2,3,5]},note='TAI T_REC availability only, not a source-free evolution sample; masks, geometry, further emergence and QUALITY at both times need a new protocol.')
 # Header-only sample: first complete record per year, deterministic from primary names.
 samples={}
 for k,v in sorted(primary_rec.items(),key=lambda item:(item[0][1],item[0][2],int(item[0][0]))):
  if set(v)=={'Br','bitmap'}:samples.setdefault(k[1][:4],(k,v))
 hs=[]
 for year,(k,v) in sorted(samples.items()):
  item=dict(year=year,harp=k[0],nominal_time_TAI=k[1]+k[2],file=v['Br'])
  try:
   with fits.open(v['Br'],memmap=True,do_not_scale_image_data=True,lazy_load_hdus=True) as hd:
    h=next(x.header for x in hd if int(x.header.get('NAXIS',0))==2)
    fields=['NAXIS1','NAXIS2','CTYPE1','CTYPE2','CRVAL1','CRVAL2','CDELT1','CDELT2','CRPIX1','CRPIX2','T_REC','T_OBS','DATE-OBS','QUALITY','BUNIT','CRLN_OBS','CRLT_OBS','RSUN_REF','DSUN_OBS']
    item['header']={n:h.get(n) for n in fields}
   stem=Path(v['Br']).name.removesuffix('.Br.fits');keyfile=Path(v['Br']).with_name(stem+'.keys.json');item['keys_json_exists']=keyfile.exists()
   if keyfile.exists():
    keys=json.loads(keyfile.read_text());item['keys_sha256']=sha(keyfile);item['effective_keywords']={n:(item['header'][n] if item['header'][n] is not None else keys.get(n)) for n in fields};item['keyword_source']='FITS header then keys.json, as in the frozen reader'
  except Exception as e:item['error']=type(e).__name__+': '+str(e)
  hs.append(item)
 inventory['header_sample']=hs
 # Shared original synoptic observations: filenames only; no derived polar-flux products imported.
 syn=Path('/storage/shared/gianluca/MWO_project/sunpy/data');synpaths=sorted(syn.glob('hmi.synoptic_mr_polfil_720s.*.Mr_polfil.fits'))
 crs=[int(p.name.split('.')[2]) for p in synpaths]
 inventory['hmi_synoptic_original_files']=dict(path=str(syn),count=len(crs),min_cr=min(crs,default=None),max_cr=max(crs,default=None),missing_in_span=sorted(set(range(min(crs),max(crs)+1))-set(crs)) if crs else [],bytes=sum(p.stat().st_size for p in synpaths),note='Original HMI synoptic files only; no calibration coefficients or SINDy results used. Polar-filled composite, not instantaneous full disk or an independent local time series.')
 inventory['tools']={n:shutil.which(n) for n in ['gfortran','h5fc','nf-config','mpif90','make','cmake','octave','matlab']}
 inventory['python_packages']={}
 import importlib.metadata
 for n in ['numpy','scipy','astropy','sunpy','drms','h5py','netCDF4']:
  try:inventory['python_packages'][n]=importlib.metadata.version(n)
  except importlib.metadata.PackageNotFoundError:inventory['python_packages'][n]=None
 Path(out).write_text(json.dumps(inventory,indent=2,default=str)+'\n')
 print(json.dumps({k:inventory[k] for k in ['patch_collections','selection','temporal_availability','hmi_synoptic_original_files','tools','python_packages']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);args=p.parse_args();main(args.out)
