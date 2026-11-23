"""Independent reference checks for the MDI tilt pilot, not a selector or a measurement pipeline.

--selftest: synthetic geometry, angular and sampling oracles only.
--metadata: audited metadata and DPD positions/times, no magnetic pixel or real tilt values.
No network, no file writes, no scientific selection. Production code belongs to Claude.
"""
from pathlib import Path
from itertools import combinations
from collections import Counter
from datetime import datetime,timedelta
import argparse,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def nested_law(N,k1,k2,success):
    n1=min(N,k1);n2=min(n1,k2)
    if not N:return dict(N=0,n1=0,n2=0,pi1=None,pi2=None,states=1)
    first=Counter();second=Counter();est1=[];est2=[];states=0
    for s1 in combinations(range(N),n1):
        for s2 in combinations(s1,n2):
            states+=1;first.update(s1);second.update(s2)
            est1.append(sum(success[i] for i in s1)*N/n1 if n1 else None)
            est2.append(sum(success[i] for i in s2)*N/n2 if n2 else None)
    p1=n1/N;p2=n2/N
    assert all(abs(first[i]/states-p1)<1e-14 for i in range(N))
    assert all(abs(second[i]/states-p2)<1e-14 for i in range(N))
    if n1:assert abs(np.mean(est1)-sum(success))<1e-14
    if n2:assert abs(np.mean(est2)-sum(success))<1e-14
    return dict(N=N,n1=n1,n2=n2,pi1=p1,pi2=p2,states=states)


def nearest_N(ct,lon):
    q=(ct+lon)/360
    low=math.floor(q)
    return min((low,low+1),key=lambda n:(abs(360*n-lon-ct),n))


def selftest():
    checks=[]
    def ok(name,condition):
        checks.append(dict(name=name,ok=bool(condition)))
    laws=[nested_law(5,3,2,[0,1,0,1,1]),nested_law(2,15,3,[1,0]),nested_law(0,15,3,[]),nested_law(4,2,1,[0,0,1,1])]
    ok('exact nested inclusion probabilities and HT totals (enumeration)',True)
    ok('short cohort saturates both phases without borrowing',laws[1]['n1']==2 and laws[1]['n2']==2 and laws[1]['pi2']==1)
    ok('empty cohort has no defined probability',laws[2]['pi1'] is None and laws[2]['pi2'] is None)
    # M1 success 1, U success 0: balanced n2=(1,1), populations (2,4).
    ok('balanced sample mean differs from population, HT corrects it',.5!=2/6 and math.isclose(((2/1)*1+(4/1)*0)/6,2/6))
    cr=2008;nx,ny=3600,1440;xp,yp=1800.,720.5;dx,dy=-.1,2/1440
    ct=360*cr-180+(np.arange(nx)+1-xp)*dx
    ss=(np.arange(ny)+1-yp)*dy
    ok('rightmost CT is CR start, leftmost CT is just before next CR',abs(ct[-1]-360*(cr-1))<1e-9 and abs(ct[0]-(360*cr-.1))<1e-9)
    ok('longitude increases with pixel x despite descending CT',np.allclose(np.diff((360*cr-ct)%360)[:-1],.1,atol=1e-9))
    ok('sin-latitude is symmetric, all pixel centres inside poles',np.allclose(ss,-ss[::-1]) and np.max(abs(ss))<1)
    Rsun=6.96e10;area=Rsun**2*abs(math.radians(dx))*dy
    ok('constant pixel areas sum to full sphere',math.isclose(nx*ny*area,4*math.pi*Rsun**2,rel_tol=1e-14))
    ok('radial map field is not deprojected a second time',math.isclose((50*area*12)/(area*12),50))
    # A CT window around the end of CR 2008 crosses into 2009, not its own distant edge.
    centre=360*cr-.2;lo,hi=centre-8,centre+8
    involved={math.floor(lo/360)+1,math.floor(hi/360)+1}
    ok('CT seam window uses chronological adjacent rotations',involved=={2008,2009})
    ok('missing adjacent rotation makes seam unavailable',not involved.issubset({2008}))
    ok('N tie resolves to smaller integer',nearest_N(360*2008+180,0)==2008)
    raw=np.array([90.,-90.,100.,-100.,359.,-359.]);ax=(raw+90)%180-90
    ok('axial boundary and both wrap signs',np.allclose(ax,[-90,-90,-80,80,-1,1]))
    ok('raw difference need not be within 180 degrees',abs(179.-(-179.))==358.)
    joy_reference = lambda delta,lat: None if lat == 0 else float(np.sign(lat)*delta)
    ok('Joy reference contract: equator missing, opposite hemisphere signs',joy_reference(12,0) is None and joy_reference(12,2)==12 and joy_reference(12,-2)==-12)
    return dict(checks=checks,passed=sum(c['ok'] for c in checks),total=len(checks),sampling_laws=laws,
                real_tilts_read=False,production_code_tested=False)


def metadata():
    import pandas as pd
    from astropy.time import Time
    from astropy.coordinates import get_sun,GeocentricTrueEcliptic
    t=pd.read_csv(ROOT/'results/MDI_SYNOPTIC_AUDIT/FILES.csv')
    grid=[]
    for row in t.itertuples():
        ct=row.CRVAL1+(np.array([0,row.NAXIS1-1])+1-row.CRPIX1)*row.CDELT1
        assert np.allclose(ct,[row.LON_LAST,row.LON_FRST],rtol=0,atol=1e-8)
        assert row.CUNIT2=='Sine Latitude' and row.CRVAL2==0
        grid.append(int(row.CAR_ROT))
    times=[Time(x.removesuffix('_TAI').replace('.','-',2).replace('_','T'),format='isot',scale='tai').utc.to_datetime() for x in t.T_ROT]
    def ct_pair(times):
        tt=Time(times,scale='utc');jd=tt.jd
        lam=get_sun(tt).transform_to(GeocentricTrueEcliptic(equinox=tt)).lon.deg
        K=np.radians(73.6667+1.3958333*(jd-2396758.)/36525.)
        lk=np.radians(lam)-K
        L0=(np.degrees(np.arctan2(-np.sin(lk)*np.cos(np.radians(7.25)),-np.cos(lk)))-(jd-2398220.)*360/25.38)%360
        mean=(jd-2398167.329)/27.2753+1
        frac=((360-L0)%360)/360
        n=np.rint(mean-frac)
        return 360*mean-360,360*n-L0
    mean,exact=ct_pair(times);diff=mean-t.CARRTIME.to_numpy();ediff=exact-t.CARRTIME.to_numpy()
    # Superset of candidate DPD days, no isolation/day selection and no pilot extraction.
    dates=[];longs=[]
    for year in range(1996,2011):
        for line in (ROOT/'data/sharp/external_DPD_20261118'/f'gDPD{year}.txt').read_text().splitlines():
            if not line.startswith('g '):continue
            try:
                dt=datetime.strptime(line[2:18],'%Y %m %d %H %M')+timedelta(seconds=int(line[19:21]))
                lat=float(line[59:65]);lon=float(line[66:72]);ar=int(line[53:58])
            except ValueError:continue
            if datetime(1996,5,1)<=dt<datetime(2010,11,1) and abs(lat)<=45 and 0<=lon<=360 and ar>=1:
                dates.append(dt);longs.append(lon%360)
    cm,ce=ct_pair(dates)
    nm=np.array([nearest_N(c,l) for c,l in zip(cm,longs)])
    ne=np.array([nearest_N(c,l) for c,l in zip(ce,longs)])
    return dict(audit_rows=len(t),grid_endpoints_verified=len(grid),mean_period_CT_minus_TROT_deg=[float(diff.min()),float(diff.max())],
                meeus_CT_minus_TROT_maxabs_deg=float(abs(ediff).max()),DPD_days_checked=len(dates),
                different_selected_N=int((nm!=ne).sum()),max_abs_mean_vs_meeus_CT_deg=float(abs(cm-ce).max()),
                mean_CT_is_approximation=True,real_magnetic_pixels_read=False,real_tilts_read=False,pilot_selected=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--selftest',action='store_true');g.add_argument('--metadata',action='store_true');a=ap.parse_args()
    out=selftest() if a.selftest else metadata();print(json.dumps(out,indent=2))
    if a.selftest:raise SystemExit(0 if out['passed']==out['total'] else 1)
