"""Observed-evolution draft review: selection metadata plus synthetic initialisation/frame checks."""
from pathlib import Path
from unittest.mock import patch
import sys,json,hashlib
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
from sharpbl import measure,geometry,cycle,recurrence,select_records
# Selected P1 metadata only: no FITS, tilt or measured-flux columns.
p=ROOT/'results/P1/P1_RECORD_SELECTION.csv'
d=pd.read_csv(p,usecols=['HARPNUM','T_REC','role','USFLUX'])
a=d[d.role.isin(['primary','both'])].set_index('HARPNUM')
b=d[d.role.isin(['control','both'])].set_index('HARPNUM')
assert a.index.is_unique and b.index.is_unique and set(a.index)==set(b.index)
ratio=(b.USFLUX/a.USFLUX).astype(float); assert (ratio>=1).all()
times={}
# Nominal T_REC availability only, not an observational error sample.
for name,root in [('p1',ROOT/'data/sharp/fits'),('p3',ROOT/'data/sharp/fits_p3'),('test',ROOT/'data/sharp/test_20240508')]:
 for f in root.rglob('*.Br.fits'):
  v=f.name.split('.')
  if len(v)<6: continue
  h=int(v[2]);t=pd.to_datetime(v[3],format='%Y%m%d_%H%M%S_TAI')
  times.setdefault(h,set()).add(t)
close=[]
for h,t in times.items():
 t=sorted(t)
 for x,y in zip(t,t[1:]):
  dt=(y-x).total_seconds()
  if 0<dt<=7200:close.append((h,dt))
# Perfect persistence, with no transport: balancing the input alone already changes D.
lon=np.array([[.2,-.2]]);lat=np.array([[16.,14.]])
with patch.object(geometry,'lonlat_maps',return_value=(lon,lat)),patch.object(geometry,'pixel_area_cm2',return_value=1e18),patch.object(geometry,'rsun_cm',return_value=6.96e10),patch.object(cycle,'assign_cycle',return_value=(24,1.,'synthetic')):
 q=measure.measure_v84(np.array([[2000.,-1000.]]),np.array([[33,33]]),{'T_REC':'2020.01.01_00:00:00_TAI'})
assert q['valid_bl']==1 and abs(q['d_axial_g']-q['d_axial_bal_g'])>0
# Illustrate why future max selection cannot yield a falling endpoint stratum.
fake=pd.DataFrame(dict(HARPNUM=[1,1,1],T_REC=['2020.01.01_00:00:00_TAI','2020.01.02_00:00:00_TAI','2020.01.03_00:00:00_TAI'],QUALITY=[0,0,0],USFLUX=[10.,8.,6.],LON_FWT=[0.,13.,26.]))
fake['t']=pd.to_datetime(fake.T_REC.str.removesuffix('_TAI'),format='%Y.%m.%d_%H:%M:%S')
sel,_=select_records.select(fake.assign(LAT_FWT=15.,NOAA_NUM=1,NOAA_AR=1,NOAA_ARS='1'))
assert len(sel)==1 and sel.role.iloc[0]=='both'
lat0=15.;om=float(recurrence.omega(lat0));dt=4.5
out=dict(selection=dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),harps=len(ratio),control_below_primary=int((ratio<1).sum()),decline_over_20_percent=int((ratio<.8).sum()),minimum_control_over_primary=float(ratio.min()),explanation='Control candidates include the selected primary; maximum USFLUX cannot be below primary.'),nominal_short_pairs=dict(harps=len({h for h,_ in close}),pairs=len(close),min_seconds=min((t for _,t in close),default=None),max_seconds=max((t for _,t in close),default=None)),initialisation=dict(raw_D=q['d_axial_g'],balanced_D=q['d_axial_bal_g'],perfect_persistence_error=0.,balanced_input_vs_raw_target_error=q['d_axial_g']-q['d_axial_bal_g']),frame=dict(latitude=lat0,days=dt,omega_sidereal_deg_per_day=om,carrington_rate=recurrence.OMEGA_CARR,shift_without_frame_correction_deg=om*dt,shift_in_carrington_deg=(om-recurrence.OMEGA_CARR)*dt))
print(json.dumps(out,indent=2))
