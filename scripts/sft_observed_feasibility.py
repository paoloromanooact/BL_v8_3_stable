"""Geometric feasibility of the common domain for the observed-evolution pilot (point 3), from keys.json and P1 metadata only.

No pixel is read: footprints in Carrington coordinates come from the edges of the CEA grid through the P1 WCS adapter.
Primary and control footprints are intersected and eroded with the margin of the draft (maxima over the parameter grid);
interior area as a solid angle. Variants: isotropic margin (draft rev. 2), directional margin (rev. 3), and two looser
alternatives. Run: PYTHONPATH=python .venv/bin/python scripts/sft_observed_feasibility.py
"""
import json, numpy as np, pandas as pd
from pathlib import Path
from astropy.io import fits
from sharpbl import geometry as geo, sft_core as C
c=pd.read_csv("results/P1/P1_SBL_CATALOG_BY_HARP.csv",usecols=["HARPNUM","T_REC","role","USFLUX","NOAA_NUM","family_rank","valid_bl"],low_memory=False)
c["t"]=pd.to_datetime(c.T_REC.str.replace("_TAI","").str.replace(".", "-",n=2).str.replace("_"," "))
p=c[c.role=="primary"].set_index("HARPNUM"); k=c[c.role=="control"].set_index("HARPNUM")
j=p.join(k,lsuffix="_p",rsuffix="_c",how="inner"); j["gap"]=(j.t_c-j.t_p).dt.total_seconds()/86400
q=j[(j.gap>=1)&(j.gap<=4.5)&(j.valid_bl_p==1)&(j.family_rank_p==0)].copy()
D=Path("data/sharp/fits")
def keys(h,trec):
    f=D/trec[:4]/f"hmi.sharp_cea_720s.{h}.{trec[:4]}{trec[5:7]}{trec[8:10]}_{trec[11:13]}{trec[14:16]}{trec[17:19]}_TAI.keys.json"
    return json.loads(f.read_text()) if f.exists() else None
def footprint(k):
    hd=fits.Header()
    for x in ("CTYPE1","CTYPE2","CUNIT1","CUNIT2","CRPIX1","CRPIX2","CRVAL1","CRVAL2","CDELT1","CDELT2","CROTA2"): hd[x]=k[x]
    nx,ny=int(round(2*k["CRPIX1"]-1)),int(round(2*k["CRPIX2"]-1))
    lon,lat=geo.lonlat_maps(hd,(ny,nx))
    e=np.concatenate([lon[0],lon[-1],lon[:,0],lon[:,-1]]); a=np.concatenate([lat[0],lat[-1],lat[:,0],lat[:,-1]])
    e=(e-k["CRVAL1"]+180)%360-180+k["CRVAL1"]
    return e.min(),e.max(),a.min(),a.max()
Rkm=6.96e5; lat=np.radians(np.linspace(0,60,601)); vfac=np.max(np.sin(lat)*np.cos(lat)**2.33)
fp={}
for h,r in q.iterrows():
    k0,k1=keys(h,r["T_REC_p"]),keys(h,r["T_REC_c"])
    fp[h]=(footprint(k0),footprint(k1),r["gap"],"un NOAA" if r["NOAA_NUM_p"]==1 else "altro/ignoto")
def feas(dif_k, thr, aniso):
    rows=[]
    for h,(a,b,g,cx) in fp.items():
        lo=max(a[0],b[0]); hi=min(a[1],b[1]); la=max(a[2],b[2]); lh=min(a[3],b[3]); dts=g*86400
        d=dif_k*np.degrees(np.sqrt(2*466.8*dts)/Rkm)
        rot=np.max(np.abs(C.omega_rel_deg_day(np.linspace(a[2],a[3],50))))*g
        mer=np.degrees(0.041*vfac*dts/Rkm)
        mlon=d+rot+0.5+(0 if aniso else mer); mlat=d+mer+0.5+(0 if aniso else rot)
        lo2,hi2,la2,lh2=lo+mlon,hi-mlon,la+mlat,lh-mlat
        area=np.radians(hi2-lo2)*(np.sin(np.radians(lh2))-np.sin(np.radians(la2)))*(180/np.pi)**2 if (hi2>lo2 and lh2>la2) else 0.0
        rows.append(dict(g=g,cx=cx,ok=area>=thr))
    R=pd.DataFrame(rows); R["dtc"]=np.select([R.g<2,R.g<3],["1-2","2-3"],"3-4.5")
    return pd.crosstab(R.dtc,R.cx,values=R.ok,aggfunc="sum").astype(int)
for name,(dk,thr,an) in {"current (isotropic, sqrt(4 eta t), 25)":(np.sqrt(2),25,False),
                         "A anisotropic, sqrt(4 eta t), 25":(np.sqrt(2),25,True),
                         "B anisotropic, sqrt(2 eta t) = 1 sigma, 25":(1.0,25,True),
                         "C anisotropic, sqrt(4 eta t), 10":(np.sqrt(2),10,True),
                         "D anisotropic, 1 sigma, 10":(1.0,10,True)}.items():
    t=feas(dk,thr,an); print(name, "total", int(t.values.sum())); print(t.to_string())
