"""Read-only HMI nesting feasibility inventory. No nest identification or tilt/flux fitting.
Reads hourly SHARP metadata and P1 identity/family columns only; no FITS or network.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
COLS=['HARPNUM','T_REC','QUALITY','LAT_FWT','LON_FWT','CRLN_OBS','NOAA_NUM','NOAA_ARS']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalise(df,month):
 raw=len(df);owned=df.T_REC.astype(str).str.slice(0,7).eq(month.replace('_','.'))
 outside=int((~owned).sum());d=df[owned].copy()
 numeric=pd.to_numeric(d.HARPNUM,errors='coerce');good=np.isfinite(numeric)&(numeric>0)&(numeric==np.floor(numeric))
 bad_h=int((~good).sum());d=d[good].copy();d['HARPNUM']=numeric[good].astype(int)
 t=pd.to_datetime(d.T_REC.astype(str).str.removesuffix('_TAI'),format='%Y.%m.%d_%H:%M:%S',errors='coerce')
 bad_t=int(t.isna().sum());d=d[t.notna()].copy();d['t']=t[t.notna()]
 dup=d.duplicated(['HARPNUM','T_REC'],keep='first');dup_count=int(dup.sum())
 conflicts=0
 for _,g in d[d.duplicated(['HARPNUM','T_REC'],keep=False)].groupby(['HARPNUM','T_REC']):
  conflicts+=int(len(g[COLS].astype(str).drop_duplicates())>1)
 d=d[~dup].sort_values(['HARPNUM','t'])
 for c in ['QUALITY','LAT_FWT','LON_FWT','CRLN_OBS','NOAA_NUM']:d[c]=pd.to_numeric(d[c],errors='coerce')
 d['lon_carr']=(d.LON_FWT+d.CRLN_OBS)%360
 d['position_present']=np.isfinite(d[['LAT_FWT','LON_FWT','CRLN_OBS']]).all(axis=1)
 return d,dict(raw_rows=raw,rows_outside_filename_month=outside,invalid_harp=bad_h,invalid_time=bad_t,duplicate_rows=dup_count,conflicting_duplicate_keys=conflicts,canonical_rows=len(d))
def numbers(v):return {int(s) for s in re.findall(r'\d+',str(v)) if int(s)>0} if pd.notna(v) else set()
def selftest():
 base=dict(HARPNUM=1,QUALITY=0,LAT_FWT=5,LON_FWT=-10,CRLN_OBS=5,NOAA_NUM=1,NOAA_ARS='123,124')
 d=pd.DataFrame([dict(base,T_REC='2020.02.01_01:00:00_TAI'),dict(base,T_REC='2020.02.01_00:00:00_TAI'),dict(base,T_REC='2020.02.01_00:00:00_TAI'),dict(base,T_REC='2020.03.01_00:00:00_TAI'),dict(base,T_REC='2020.02.31_00:00:00_TAI')])
 n,info=normalise(d,'2020_02')
 c={'owned month only':info['rows_outside_filename_month']==1,'duplicate key counted':info['duplicate_rows']==1,'invalid calendar counted':info['invalid_time']==1,'chronological first record':n.T_REC.iloc[0]=='2020.02.01_00:00:00_TAI','Carrington seam':float(n.lon_carr.iloc[0])==355.,'NOAA multiple association':numbers('123,124')=={123,124},'missing NOAA not zero identity':not numbers(np.nan)}
 print(json.dumps(dict(passed=sum(c.values()),total=len(c),checks=c),indent=2));return all(c.values())
def run(root,out):
 if out.exists():raise SystemExit('refusing to overwrite')
 states={};files=[];schema=[];months=[]
 paths=sorted((root/'data/sharp/metadata').glob('sharp_meta_*.csv'))
 for i,p in enumerate(paths):
  month=p.stem.removeprefix('sharp_meta_');headers=list(pd.read_csv(p,nrows=0).columns)
  missing=sorted(set(COLS)-set(headers))
  if missing:raise ValueError(f'missing required columns {p}: {missing}')
  d,ct=normalise(pd.read_csv(p,usecols=COLS,low_memory=False),month)
  files.append(dict(path=str(p.relative_to(root)),sha256=sha(p),bytes=p.stat().st_size,columns=';'.join(headers),has_T_OBS='T_OBS' in headers,has_emergence_time=any(k in headers for k in ('T_FRST','T_FRST1','EMERGENCE_TIME')),**ct))
  months.append(month)
  for h,g in d.groupby('HARPNUM',sort=True):
   h=int(h);first,last=g.iloc[0],g.iloc[-1];valid=g[g.QUALITY.isin([0,128]) & g.position_present]
   st=states.setdefault(h,dict(rows=0,quality_position_rows=0,missing_position_rows=0,noaa=set(),max_gap_hours=0.0))
   gaps=g.t.diff().dt.total_seconds().dropna()/3600.
   if len(gaps):st['max_gap_hours']=max(st['max_gap_hours'],float(gaps.max()))
   if 'last_t' in st:st['max_gap_hours']=max(st['max_gap_hours'],(first.t-st['last_t']).total_seconds()/3600.)
   if 'first_t' not in st:st.update(first_t=first.t,first_lat=first.LAT_FWT,first_lcm=first.LON_FWT,first_lon_carr=first.lon_carr)
   st.update(last_t=last.t,last_lcm=last.LON_FWT,last_lon_carr=last.lon_carr)
   st['rows']+=len(g);st['quality_position_rows']+=len(valid);st['missing_position_rows']+=int((~g.position_present).sum())
   for n in g.NOAA_ARS.dropna().unique():st['noaa'].update(numbers(n))
   if len(valid):
    f=valid.iloc[0]
    if 'first_qual_t' not in st:st.update(first_qual_t=f.t,first_qual_lat=f.LAT_FWT,first_qual_lcm=f.LON_FWT,first_qual_lon_carr=f.lon_carr)
    st['last_qual_t']=valid.t.iloc[-1]
  if (i+1)%40==0:print('metadata files',i+1,'/',len(paths),flush=True)
 catp=root/'results/P1/P1_SBL_CATALOG_BY_HARP.csv'
 cat=pd.read_csv(catp,usecols=['HARPNUM','role','family_id','family_rank','first_seen_on_disk'])
 prim=cat[cat.role.isin(['primary','both'])].set_index('HARPNUM')
 if prim.index.has_duplicates:raise ValueError('primary identity duplicate')
 rows=[]
 for h,st in sorted(states.items()):
  row=dict(HARPNUM=h,n_hourly_records=st['rows'],first_T_REC=str(st['first_t']),last_T_REC=str(st['last_t']),span_days=(st['last_t']-st['first_t']).total_seconds()/86400.,first_lat=st['first_lat'],first_LCM=st['first_lcm'],first_lon_carr=st['first_lon_carr'],last_LCM=st['last_lcm'],last_lon_carr=st['last_lon_carr'],max_gap_hours=st['max_gap_hours'],quality_0_or_128_position_records=st['quality_position_rows'],missing_position_records=st['missing_position_rows'],first_qual_T_REC=str(st.get('first_qual_t','')),first_qual_lat=st.get('first_qual_lat',np.nan),first_qual_LCM=st.get('first_qual_lcm',np.nan),first_qual_lon_carr=st.get('first_qual_lon_carr',np.nan),last_qual_T_REC=str(st.get('last_qual_t','')),n_noaa_ids_ever=len(st['noaa']),noaa_ids_ever=';'.join(map(str,sorted(st['noaa']))),in_P1=h in prim.index)
  if h in prim.index:
   a=prim.loc[h];row.update(P1_family_id=a.family_id,P1_family_rank=a.family_rank,P1_first_seen_on_disk=a.first_seen_on_disk)
  rows.append(row)
 harps=pd.DataFrame(rows);F=pd.DataFrame(files)
 missing_months=[]
 if months:
  expected=pd.period_range(months[0].replace('_','-'),months[-1].replace('_','-'),freq='M').strftime('%Y_%m')
  missing_months=sorted(set(expected)-set(months))
 summary=dict(scope='availability inventory only; no nests identified and no tilt/flux outcomes parsed',fits_read=False,network_used=False,clustering_run=False,bayesian_fit_run=False,metadata_files=len(files),bytes=int(F.bytes.sum()),raw_rows=int(F.raw_rows.sum()),canonical_unique_rows=int(F.canonical_rows.sum()),boundary_rows_outside_owner_month=int(F.rows_outside_filename_month.sum()),duplicates_within_files=int(F.duplicate_rows.sum()),conflicting_duplicates=int(F.conflicting_duplicate_keys.sum()),invalid_time=int(F.invalid_time.sum()),harps=len(harps),P1_primary_harps=int(harps.in_P1.sum()),harps_no_P1=int((~harps.in_P1).sum()),harps_with_quality_and_position=int((harps.quality_0_or_128_position_records>0).sum()),harps_with_no_NOAA_ids=int((harps.n_noaa_ids_ever==0).sum()),harps_with_multiple_NOAA_ids=int((harps.n_noaa_ids_ever>1).sum()),files_with_T_OBS=int(F.has_T_OBS.sum()),files_with_emergence_time_keyword=int(F.has_emergence_time.sum()),month_min=months[0],month_max=months[-1],missing_months=missing_months,first_T_REC=harps.first_T_REC.min(),last_T_REC=harps.last_T_REC.max(),harp_span_days_quantiles={str(q):float(harps.span_days.quantile(q)) for q in [0,.25,.5,.75,1]},harps_with_gap_over_2h=int((harps.max_gap_hours>2).sum()),P1_recurrence_candidates=int((harps.P1_family_rank>0).sum()),notes=['Times are nominal hourly T_REC in TAI, not measured emergence times.','Each row belongs to its filename month; inclusive month-end query rows are logged and removed from that file only.','Quality {0,128} is counted as the existing P1 rule, not a new nest selection.','NOAA identifiers are associations over time, not a one-to-one HARP/event identity.','Hourly metadata do not provide continuous magnetic images; only sparse selected maps are local.'])
 out.mkdir(parents=True);harps.to_csv(out/'HARP_AVAILABILITY.csv',index=False,lineterminator='\n');F.to_csv(out/'INPUTS.csv',index=False,lineterminator='\n')
 (out/'META.json').write_text(json.dumps(dict(summary=summary,code_sha256=sha(__file__),catalogue_sha256=sha(catp),products_sha256={p.name:sha(p) for p in out.iterdir()}),indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--selftest',action='store_true');g.add_argument('--out',type=Path);a=p.parse_args()
 if a.selftest:sys.exit(0 if selftest() else 1)
 run(a.root,a.out)
