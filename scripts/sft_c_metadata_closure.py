"""C draft feasibility from preserved metadata only. No FITS opened, pixels measured, or inferential fits."""
import argparse,datetime,decimal,hashlib,json,math,re
from pathlib import Path
import numpy as np
import pandas as pd
from astropy.io.fits import Header
from astropy.wcs import WCS
import warnings
ROOT=Path(__file__).resolve().parents[1]
AUDIT=Path('reviews/SFT_HMI_REPEATABILITY_METADATA_20261125')
CAT=Path('results/P1/P1_SBL_CATALOG_BY_HARP.csv')
ALLOWED=('T_OBS','QUALITY','LON_FWT','LAT_FWT','USFLUX','CRVAL1','CRVAL2','CRPIX1','CRPIX2','CTYPE1','CTYPE2','CUNIT1','CUNIT2','CDELT1','CDELT2','CROTA2','OBS_VR')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tns(s):
 m=re.fullmatch(r'(\d{4})\.(\d{2})\.(\d{2})_(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)_TAI',str(s))
 if not m:raise ValueError('Explicit TAI required')
 y,mo,d,h,mi=map(int,m.groups()[:5]);sec=decimal.Decimal(m.group(6))
 if not (h<24 and mi<60 and 0<=sec<=60):raise ValueError('Time range')
 days=(datetime.date(y,mo,d)-datetime.date(1970,1,1)).days
 ns=(decimal.Decimal(days*86400+h*3600+mi*60)+sec)*10**9
 if ns!=int(ns):raise ValueError('Sub-nanosecond time not represented')
 return int(ns)
def quality(x):
 s=str(x).strip();return int(s,16) if s.lower().startswith('0x') else int(s)
def number(x):
 try:return float(x)
 except (ValueError,TypeError):return float('nan')
def box(k):
 h=Header()
 for name in ('CTYPE1','CTYPE2','CUNIT1','CUNIT2','CRPIX1','CRPIX2','CRVAL1','CRVAL2','CDELT1','CDELT2','CROTA2'):h[name]=k[name]
 nx=round(2*float(k['CRPIX1'])-1);ny=round(2*float(k['CRPIX2'])-1)
 x=np.r_[np.arange(nx),np.arange(nx),np.zeros(ny),np.full(ny,nx-1)]
 y=np.r_[np.zeros(nx),np.full(nx,ny-1),np.arange(ny),np.arange(ny)]
 with warnings.catch_warnings():
  warnings.simplefilter('ignore');lon,lat=WCS(h).wcs_pix2world(x,y,0)
 lon=(lon-float(k['CRVAL1'])+180)%360-180+float(k['CRVAL1'])
 if not (np.isfinite(lon).all() and np.isfinite(lat).all()):raise ValueError('Invalid bbox')
 return float(lat.min()),float(lat.max()),float(lon.min()),float(lon.max())
def overlap(a,b):
 return a[0]<=b[1] and b[0]<=a[1] and abs((.5*(a[2]+a[3]-b[2]-b[3])+180)%360-180)<=.5*(a[3]-a[2]+b[3]-b[2])
class Graph:
 def __init__(self,n):self.p=list(range(n))
 def find(self,a):
  while a!=self.p[a]:self.p[a]=self.p[self.p[a]];a=self.p[a]
  return a
 def union(self,a,b):self.p[self.find(b)]=self.find(a)
def selftest():
 checks=[]
 def ok(name,x):checks.append(dict(name=name,ok=bool(x)))
 ok('TAI 7200 seconds exact',tns('2010.01.01_02:00:04_TAI')-tns('2010.01.01_00:00:04_TAI')==7200*10**9)
 ok('7201 seconds is outside',tns('2010.01.01_02:00:05_TAI')-tns('2010.01.01_00:00:04_TAI')>7200*10**9)
 ok('seconds60 equals next minute',tns('2010.01.01_00:00:60_TAI')==tns('2010.01.01_00:01:00_TAI'))
 ok('fraction preserved',tns('2010.01.01_00:00:00.125_TAI')%10**9==125000000)
 g=Graph(4);g.union(0,1);g.union(1,2)
 ok('protected graph transitive exclusion',g.find(0)==g.find(2) and g.find(0)!=g.find(3))
 ok('bbox longitude seam',overlap((0,2,358,362),(1,3,-1,3)))
 ok('different latitude not overlap',not overlap((0,2,358,362),(3,4,-1,3)))
 for x in ('missing','nan',''):
  try:quality(x);ok('quality invalid '+x,False)
  except ValueError:ok('quality invalid '+x,True)
 return dict(passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks)
def run(root,out):
 if out.exists():raise SystemExit('Refuse overwrite')
 m=json.loads((root/AUDIT/'META.json').read_text())
 for f,h in m['products_sha256'].items():
  if sha(root/AUDIT/f)!=h:raise ValueError('Audit product changed '+f)
 if sha(root/CAT)!=m['catalogue_sha256']:raise ValueError('Catalogue changed')
 pairs=pd.read_csv(root/AUDIT/'PAIRS.csv');keys=pd.read_csv(root/AUDIT/'KEYWORDS.csv');headers=pd.read_csv(root/AUDIT/'HEADERS.csv')
 lookup={(int(x.HARPNUM),x.T_REC):x for x in keys.itertuples(index=False)}
 shapes={(int(x.HARPNUM),x.T_REC):(int(x.ny),int(x.nx)) for x in headers.itertuples(index=False)}
 cat=pd.read_csv(root/CAT,usecols=['HARPNUM','T_REC','role','valid_bl','family_rank','family_id'])
 fam={}
 for h,g in cat.groupby('HARPNUM'):
  u=g.family_id.dropna().unique()
  if len(u)>1:raise ValueError('Inconsistent family')
  fam[int(h)]=int(u[0]) if len(u) else None
 cache={};inputs={str(AUDIT/'META.json'):sha(root/AUDIT/'META.json'),str(CAT):sha(root/CAT)}
 def get(h,t):
  key=(int(h),t)
  if key not in cache:
   rr=lookup[key];p=root/rr.keys_path
   if sha(p)!=rr.keys_sha256:raise ValueError('Keyword changed '+str(key))
   d=json.loads(p.read_text());k={n:d.get(n) for n in ALLOWED}
   if str(k['T_OBS'])!=rr.T_OBS:raise ValueError('T_OBS changed')
   cache[key]=k;inputs[rr.keys_path]=rr.keys_sha256
  return cache[key]
 nodes=[]
 prim=cat[cat.role=='primary'].set_index('HARPNUM');ctrl=cat[cat.role=='control'].set_index('HARPNUM')
 assert prim.index.is_unique and ctrl.index.is_unique
 for h in sorted(set(prim.index)&set(ctrl.index)):
  a=prim.loc[h];b=ctrl.loc[h]
  if a.valid_bl!=1 or a.family_rank!=0 or (int(h),a.T_REC) not in lookup or (int(h),b.T_REC) not in lookup:continue
  k0=get(h,a.T_REC);k1=get(h,b.T_REC);t0=tns(k0['T_OBS']);t1=tns(k1['T_OBS'])
  if 86400*10**9<=t1-t0<=int(4.5*86400)*10**9:
   nodes.append(dict(kind='pool',harp=int(h),family=fam.get(int(h)),a=a.T_REC,b=b.T_REC,t0=t0,t1=t1,box=box(k0)))
 n_pool=len(nodes);candidate_rows=[]
 for row in pairs.itertuples(index=False):
  if row.status!='metadata_ok':continue
  h=int(row.HARPNUM);k0=get(h,row.T_REC_a);k1=get(h,row.T_REC_b);t0=tns(k0['T_OBS']);t1=tns(k1['T_OBS'])
  if not 0<t1-t0<=7200*10**9:continue
  i=len(nodes);nodes.append(dict(kind='C',harp=h,family=fam.get(h),a=row.T_REC_a,b=row.T_REC_b,t0=t0,t1=t1,box=box(k0)))
  reasons=[]
  if quality(k0['QUALITY']) not in (0,128) or quality(k1['QUALITY']) not in (0,128):reasons.append('quality')
  if not all(np.isfinite(number(k['LON_FWT'])) and abs(number(k['LON_FWT']))<=60 for k in (k0,k1)):reasons.append('lcm')
  if not bool(row.shape_matches_CRPIX):reasons.append('shape')
  if not np.isfinite(row.common_area_deg2) or row.common_area_deg2<25:reasons.append('geometry')
  if fam.get(h) is None:reasons.append('family_unknown')
  flux=number(k0['USFLUX'])
  candidate_rows.append(dict(node=i,HARPNUM=h,T_REC_a=row.T_REC_a,T_REC_b=row.T_REC_b,gap_ns=t1-t0,area_deg2=row.common_area_deg2,family=fam.get(h),USFLUX_t0=flux,flux_metadata_positive=bool(np.isfinite(flux) and flux>0),OBS_VR_present=k0['OBS_VR'] is not None,LON_FWT_t0=number(k0['LON_FWT']),LAT_FWT_t0=number(k0['LAT_FWT']),pregraph_reasons=';'.join(reasons)))
 graph=Graph(len(nodes));edges=[]
 for i,a in enumerate(nodes):
  for j in range(i):
   b=nodes[j];why=[]
   if a['harp']==b['harp']:why.append('harp')
   if a['family'] is not None and a['family']==b['family']:why.append('family')
   if a['t0']<=b['t1'] and b['t0']<=a['t1'] and overlap(a['box'],b['box']):why.append('spacetime_bbox')
   if why:graph.union(i,j);edges.append(dict(node_a=j,node_b=i,causes=';'.join(why)))
 protected={graph.find(i) for i in range(n_pool)}
 df=pd.DataFrame(candidate_rows);df['component']=df.node.map(graph.find);df['protected_component']=df.component.isin(protected)
 df['metadata_eligible']=(df.pregraph_reasons=='') & ~df.protected_component
 selected=df[df.metadata_eligible].copy()
 vals=selected.loc[selected.flux_metadata_positive,'USFLUX_t0']
 q1,q2=(float(x) for x in vals.quantile([1/3,2/3])) if len(vals) else (math.nan,math.nan)
 def cls(row):
  if not row.flux_metadata_positive:return 'missing_or_invalid'
  return '1' if row.USFLUX_t0<=q1 else ('2' if row.USFLUX_t0<=q2 else '3')
 df['flux_class_provisional']=df.apply(cls,axis=1);selected=df[df.metadata_eligible]
 by_year=selected.T_REC_a.str[:4].value_counts().sort_index().to_dict()
 summary=dict(scope=__doc__,pool_nodes=n_pool,C_nodes=len(df),graph_nodes=len(nodes),graph_edges=len(edges),protected_C_nodes=int(df.protected_component.sum()),metadata_eligible_pairs=len(selected),metadata_eligible_harps=int(selected.HARPNUM.nunique()),metadata_eligible_components=int(selected.component.nunique()),positive_USFLUX=int(selected.flux_metadata_positive.sum()),missing_OBS_VR=int((~selected.OBS_VR_present).sum()),tercile_bounds=[q1,q2],tercile_counts=selected.flux_class_provisional.value_counts().sort_index().to_dict(),lag_1h=int((selected.gap_ns<=5400*10**9).sum()),lag_2h=int((selected.gap_ns>5400*10**9).sum()),by_year=by_year,notes=['Provisional metadata eligibility, not frozen scientific selection.','Pixel finiteness, C_fin and C_rot not evaluated; no observational error measured.','Bounding boxes from audited metadata CRPIX-inferred shapes; real runner must verify actual headers and exact mask geometry.','Unknown family excluded provisionally; no nests inferred.'])
 out.mkdir(parents=True);df.to_csv(out/'CANDIDATES.csv',index=False);pd.DataFrame(edges).to_csv(out/'EDGES.csv',index=False)
 pd.DataFrame([{k:v for k,v in n.items() if k!='box'}|dict(node=i,bbox=list(n['box'])) for i,n in enumerate(nodes)]).to_csv(out/'NODES.csv',index=False)
 (out/'SELFTEST.json').write_text(json.dumps(selftest(),indent=2)+'\n')
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
 meta=dict(code_sha256=sha(__file__),inputs_sha256=inputs,products_sha256={p.name:sha(p) for p in out.iterdir()},magnetic_arrays_read=False,network_used=False,source_draft_sha256=sha(root/'docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md'))
 (out/'META.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--selftest',action='store_true');a=p.parse_args()
 if a.selftest:
  s=selftest();print(json.dumps(s,indent=2));raise SystemExit(0 if s['passed']==s['total'] else 1)
 if a.out is None:p.error('--out required without --selftest')
 run(a.root,a.out)
