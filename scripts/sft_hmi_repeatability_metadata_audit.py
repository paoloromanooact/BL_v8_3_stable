"""Header-only assessment of local HMI short-lag repeatability for SFT §7.
No magnetic arrays, measured tilts/fluxes, simulations, or network access.
Availability counts are not an error estimate or a frozen selection rule.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,math,re,sys,warnings
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.time import Time,TimeDelta
from astropy.wcs import WCS,FITSFixedWarning
from scipy.ndimage import minimum_filter,binary_erosion
ROOT=Path(__file__).resolve().parents[1]
PAT=re.compile(r'^hmi\.sharp_cea_720s\.(\d+)\.(\d{8})_(\d{6})_TAI\.(Br|bitmap)\.fits$')
COLLECTIONS=('data/sharp/fits','data/sharp/fits_p3','data/sharp/test_20240508')
STEP=.06
WCS_KEYS=('CTYPE1','CTYPE2','CUNIT1','CUNIT2','CRPIX1','CRPIX2','CRVAL1','CRVAL2','CDELT1','CDELT2','CROTA2')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tai(s):
 m=re.fullmatch(r'(\d{4})\.(\d\d)\.(\d\d)_(\d\d):(\d\d):(\d\d(?:\.\d+)?)_TAI',str(s))
 if not m:raise ValueError('explicit TAI time required')
 y,mo,d,h,mi=map(int,m.groups()[:5]);sec=float(m.group(6))
 if not (0<=h<24 and 0<=mi<60 and 0<=sec<=60):raise ValueError('time component range')
 day=datetime.date(y,mo,d)
 return Time(day.isoformat(),scale='tai')+TimeDelta(h*3600+mi*60+sec,format='sec')
def gap(a,b):return float((b-a).to_value('sec'))
def nominal(key):
 h,d,t=key;return f'{d[:4]}.{d[4:6]}.{d[6:]}_{t[:2]}:{t[2:4]}:{t[4:]}_TAI'
def scan(root):
 rec={};duplicates=[]
 for rel in COLLECTIONS:
  for p in sorted((root/rel).rglob('*.fits')):
   m=PAT.fullmatch(p.name)
   if not m:continue
   h,d,t,seg=m.groups();key=(int(h),d,t)
   if seg in rec.setdefault(key,{}):duplicates.append({'record':list(key),'segment':seg,'preferred':rec[key][seg],'alternative':str(p.relative_to(root))})
   else:rec[key][seg]=str(p.relative_to(root))
 return rec,duplicates

def wcs_header(k):
 h=fits.Header()
 for name in WCS_KEYS:h[name]=k[name]
 return h

def coords(h,shape,branch,edges=False):
 ny,nx=shape
 if edges:
  x=np.r_[np.arange(nx),np.arange(nx),np.zeros(ny),np.full(ny,nx-1)]
  y=np.r_[np.zeros(nx),np.full(nx,ny-1),np.arange(ny),np.arange(ny)]
 else:y,x=np.mgrid[:ny,:nx]
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',FITSFixedWarning)
  lo,la=WCS(h).wcs_pix2world(x,y,0)
 return np.asarray(la).ravel(),((np.asarray(lo).ravel()-branch+180)%360)-180+branch

def bbox(k,shape):
 la,lo=coords(wcs_header(k),shape,float(k['CRVAL1']),edges=True)
 return float(la.min()),float(la.max()),float(lo.min()),float(lo.max())

def boxes_overlap(a,b):
 dl=(.5*(a[2]+a[3]-b[2]-b[3])+180)%360-180
 return a[0]<=b[1] and b[0]<=a[1] and abs(dl)<=.5*(a[3]-a[2]+b[3]-b[2])

def geometry(k0,sh0,k1,sh1,seconds):
 branch=float(k0['CRVAL1']);la0,lo0=coords(wcs_header(k0),sh0,branch);la1,lo1=coords(wcs_header(k1),sh1,branch)
 lowla=min(la0.min(),la1.min())-1;lowlo=min(lo0.min(),lo1.min())-1
 ny=math.ceil((max(la0.max(),la1.max())+1-lowla)/STEP);nx=math.ceil((max(lo0.max(),lo1.max())+1-lowlo)/STEP)
 def cover(la,lo):
  g=np.zeros((ny,nx),dtype=bool);g[np.floor((la-lowla)/STEP).astype(int),np.floor((lo-lowlo)/STEP).astype(int)]=True;return g
 p0,p1=cover(la0,lo0),cover(la1,lo1)
 dif=math.degrees(math.sqrt(4*466.8*seconds)/696000.)
 lat=np.radians(np.linspace(0,80,801));vmax=.041*np.max(np.sin(lat)*np.cos(lat)**2.33)
 ml=dif+math.degrees(vmax*seconds/696000.)+.5
 la=np.radians(np.linspace(la0.min(),la0.max(),60))
 rot=np.max(np.abs(14.713-2.396*np.sin(la)**2-1.787*np.sin(la)**4-14.1844))*seconds/86400.
 mo=(dif+.5)/math.cos(math.radians(np.max(np.abs(la0))))+rot
 ky,kx=math.ceil(ml/STEP),math.ceil(mo/STEP)
 # For a full rectangular element this minimum filter is exactly binary erosion.
 c=minimum_filter(p0.astype(np.uint8),size=(2*ky+1,2*kx+1),mode='constant',cval=0).astype(bool)&p1
 e=lowla+STEP*np.arange(ny+1);a=np.radians(STEP)*(np.sin(np.radians(e[1:]))-np.sin(np.radians(e[:-1])))
 return float((c*a[:,None]).sum())*(180/math.pi)**2,ml,mo

def selftest():
 checks=[]
 def ok(n,v):checks.append({'name':n,'ok':bool(v)})
 ok('fractional TAI seconds',abs(gap(tai('2026.01.01_00:00:00.25_TAI'),tai('2026.01.01_00:00:01.75_TAI'))-1.5)<1e-8)
 ok('seconds 60 carries',abs(gap(tai('2026.01.01_00:00:60_TAI'),tai('2026.01.01_00:01:00_TAI')))<1e-8)
 ok('two-hour endpoint',abs(gap(tai('2026.01.01_00:00:00_TAI'),tai('2026.01.01_02:00:00_TAI'))-7200)<1e-8)
 for s in ('2026.01.01_00:00:00_UTC','2026.01.01_00:00:61_TAI','2026.02.30_00:00:00_TAI'):
  try:tai(s);ok('reject '+s,False)
  except ValueError:ok('reject '+s,True)
 x=np.ones((17,19),dtype=np.uint8);x[8,9]=0
 ok('minimum filter equals rectangular erosion',np.array_equal(minimum_filter(x,size=(3,5),mode='constant',cval=0),binary_erosion(x,structure=np.ones((3,5)),border_value=0)))
 ok('bounding boxes cross 360',boxes_overlap((5,10,358,362),(6,11,-1,3)))
 ok('same location different latitude not overlapping',not boxes_overlap((5,10,358,362),(12,13,-1,3)))
 print(json.dumps({'passed':sum(x['ok'] for x in checks),'total':len(checks),'checks':checks},indent=2))
 return all(x['ok'] for x in checks)

def run(root,out):
 if out.exists():raise SystemExit('refusing to overwrite existing audit')
 rec,dup=scan(root);complete={k:v for k,v in rec.items() if set(v)=={'Br','bitmap'}}
 info={};bad=[];manifest=[]
 for key,v in sorted(complete.items()):
  kp=root/v['Br'];kp=kp.with_name(kp.name.removesuffix('.Br.fits')+'.keys.json')
  try:
   data=json.loads(kp.read_text());t=tai(data['T_OBS']);info[key]=(v,data,t,kp)
  except (OSError,ValueError,KeyError) as exc:bad.append({'record':list(key),'error':type(exc).__name__+': '+str(exc)})
 byharp={}
 for key in complete:byharp.setdefault(key[0],[]).append(key)
 pairs_nom=set();pairs_obs=set()
 for keys in byharp.values():
  keys=sorted(keys,key=lambda k:(k[1],k[2]))
  for a,b in zip(keys,keys[1:]):
   if 0<gap(tai(nominal(a)),tai(nominal(b)))<=7200+1e-7:pairs_nom.add((a,b))
  valid=sorted((k for k in keys if k in info),key=lambda k:info[k][2].jd)
  for a,b in zip(valid,valid[1:]):
   if 0<gap(info[a][2],info[b][2])<=7200+1e-7:pairs_obs.add((a,b))
 catp=root/'results/P1/P1_SBL_CATALOG_BY_HARP.csv'
 cat=pd.read_csv(catp,usecols=['HARPNUM','T_REC','role','valid_bl','family_rank','family_id'])
 families={int(h):int(g.family_id.iloc[0]) for h,g in cat.groupby('HARPNUM') if pd.notna(g.family_id.iloc[0])}
 prim=cat[cat.role=='primary'].set_index('HARPNUM');ctrl=cat[cat.role=='control'].set_index('HARPNUM')
 def key_for(h,t):return int(h),t[:4]+t[5:7]+t[8:10],t[11:13]+t[14:16]+t[17:19]
 pool=[]
 for harp in sorted(set(prim.index)&set(ctrl.index)):
  p=prim.loc[harp];c=ctrl.loc[harp]
  if p.valid_bl!=1 or p.family_rank!=0:continue
  a,b=key_for(harp,p.T_REC),key_for(harp,c.T_REC)
  if a not in info or b not in info:continue
  secs=gap(info[a][2],info[b][2])
  if 86400-1e-7<=secs<=4.5*86400+1e-7:
   k=info[a][1];sh=(int(round(2*k['CRPIX2']-1)),int(round(2*k['CRPIX1']-1)))
   pool.append((int(harp),families.get(int(harp)),info[a][2].jd,info[b][2].jd,bbox(k,sh)))
 pool_h={p[0] for p in pool};pool_f={p[1] for p in pool if p[1] is not None}
 rows=[];header_cache={}
 def header(key):
  if key in header_cache:return header_cache[key]
  v,k,t,kp=info[key];sh=[];hashes=[]
  for seg in ('Br','bitmap'):
   path=root/v[seg]
   with fits.open(path,memmap=True,lazy_load_hdus=True,do_not_scale_image_data=True) as hd:
    hh=next(h.header.copy() for h in hd if int(h.header.get('NAXIS',0))==2)
   sh.append((int(hh['NAXIS2']),int(hh['NAXIS1'])));hashes.append(hashlib.sha256(hh.tostring().encode()).hexdigest())
  assert sh[0]==sh[1],('Br/bitmap shape differs',key)
  manifest.append(dict(HARPNUM=key[0],T_REC=nominal(key),T_OBS=k['T_OBS'],keys_path=str(kp.relative_to(root)),keys_sha256=sha(kp),Br_path=v['Br'],bitmap_path=v['bitmap'],Br_bytes=(root/v['Br']).stat().st_size,bitmap_bytes=(root/v['bitmap']).stat().st_size,Br_header_sha256=hashes[0],bitmap_header_sha256=hashes[1],ny=sh[0][0],nx=sh[0][1]))
  header_cache[key]=sh[0];return sh[0]
 for idx,(a,b) in enumerate(sorted(pairs_nom|pairs_obs)):
  row=dict(HARPNUM=a[0],T_REC_a=nominal(a),T_REC_b=nominal(b),nominal_within_2h=(a,b) in pairs_nom,observed_within_2h=(a,b) in pairs_obs)
  try:
   va,ka,ta,kpa=info[a];vb,kb,tb,kpb=info[b];secs=gap(ta,tb)
   row.update(T_OBS_a=ka['T_OBS'],T_OBS_b=kb['T_OBS'],gap_s=secs,QUALITY_a=str(ka.get('QUALITY','missing')),QUALITY_b=str(kb.get('QUALITY','missing')),same_harp_in_observed_pool=a[0] in pool_h,same_family_in_observed_pool=families.get(a[0]) in pool_f,family_known=a[0] in families)
   sh0,sh1=header(a),header(b)
   row['shape_matches_CRPIX']=(sh0==(round(2*ka['CRPIX2']-1),round(2*ka['CRPIX1']-1)) and sh1==(round(2*kb['CRPIX2']-1),round(2*kb['CRPIX1']-1)))
   if secs>0:
    area,ml,mo=geometry(ka,sh0,kb,sh1,secs);row.update(common_area_deg2=area,area_ge_25=area>=25,m_lat_deg=ml,m_lon_deg=mo)
   box=bbox(ka,sh0);possible=[p[0] for p in pool if ta.jd<=p[3] and p[2]<=tb.jd and boxes_overlap(box,p[4])]
   row.update(possible_spacetime_overlap_with_pool=len(possible),overlap_pool_harps=';'.join(map(str,possible)),status='metadata_ok')
  except (OSError,ValueError,KeyError,AssertionError) as exc:row.update(status='metadata_error',error=type(exc).__name__+': '+str(exc))
  rows.append(row)
  if (idx+1)%50==0:print('header-only pairs',idx+1,'/',len(pairs_nom|pairs_obs),flush=True)
 df=pd.DataFrame(rows);q=df[df.observed_within_2h & (df.status=='metadata_ok')]
 conservative=q[~q.same_harp_in_observed_pool & ~q.same_family_in_observed_pool & (q.possible_spacetime_overlap_with_pool==0)]
 summary=dict(scope='metadata/header audit only, not an error estimate or final selection',magnetic_arrays_read=False,tilt_flux_columns_read=False,network_used=False,simulation_run=False,nominal_pairs=len(pairs_nom),nominal_harps=len({a[0] for a,b in pairs_nom}),t_obs_pairs=len(pairs_obs),t_obs_harps=len({a[0] for a,b in pairs_obs}),nominal_pairs_lost_under_t_obs=len(pairs_nom-pairs_obs),t_obs_pairs_new=len(pairs_obs-pairs_nom),metadata_error_records=len(bad),metadata_error_pairs=int((df.status!='metadata_ok').sum()),observed_pilot_pool_harps=len(pool),duplicate_segment_paths=len(dup),valid_pair_gap_s_quantiles={str(x):float(q.gap_s.quantile(x)) for x in (0,.5,1)},pairs_with_area_ge_25=int(q.area_ge_25.sum()),pairs_same_harp_as_pool=int(q.same_harp_in_observed_pool.sum()),pairs_same_family_as_pool=int(q.same_family_in_observed_pool.sum()),pairs_possible_spacetime_overlap=int((q.possible_spacetime_overlap_with_pool>0).sum()),conservative_reserve_pairs=len(conservative),conservative_reserve_harps=int(conservative.HARPNUM.nunique()),conservative_reserve_area_ge_25=int(conservative.area_ge_25.sum()),notes=['Conservative reserve excludes the ENTIRE eligible primary-control pool, its known families and possible bounding-box overlaps; it is availability accounting, not the final frozen sample.','No pilot sample is frozen/selected yet: independence must be rechecked on the preserved final sample and family/spatial graph.','Missing families and unknown/modified data need explicit handling before measurement.','Pairs sharing records or families are not independent replicates.','FITS headers only; input pixel finiteness and actual repetition scatter have not been measured.'])
 out.mkdir(parents=True)
 df.to_csv(out/'PAIRS.csv',index=False,lineterminator='\n');pd.DataFrame(manifest).to_csv(out/'HEADERS.csv',index=False,lineterminator='\n')
 pd.DataFrame([dict(HARPNUM=k[0],T_REC=nominal(k),T_OBS=v[1]['T_OBS'],keys_path=str(v[3].relative_to(root)),keys_sha256=sha(v[3])) for k,v in sorted(info.items())]).to_csv(out/'KEYWORDS.csv',index=False,lineterminator='\n')
 (out/'META.json').write_text(json.dumps(dict(summary=summary,code_sha256=sha(__file__),catalogue_sha256=sha(catp),collections=list(COLLECTIONS),collection_precedence='first complete-segment path in collection order, recorded; no claim that duplicate pixels are identical',bad_records=bad,duplicate_segments=dup,products_sha256={p.name:sha(p) for p in out.iterdir()}),indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=ROOT);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--selftest',action='store_true');g.add_argument('--out',type=Path);a=ap.parse_args()
 if a.selftest:sys.exit(0 if selftest() else 1)
 run(a.root,a.out)
