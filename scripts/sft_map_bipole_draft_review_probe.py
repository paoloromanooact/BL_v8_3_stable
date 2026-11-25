"""Synthetic algebra/initialisation checks for the SFT draft; no observed pixels or SFT evolution."""
from pathlib import Path
import sys,json
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from sharpbl import measure,geometry,cycle
rows=[]
R=6.96e10
area=1e18
for cyc in (24,25):
 for lat in (-15.,15.):
  for hale in (-1,1):
   expected=cycle.expected_leading_sign(cyc,lat)
   leading=hale*expected
   lead=(.005,lat-.0025);follow=(-.005,lat+.0025)
   pos,neg=(lead,follow) if leading==1 else (follow,lead)
   lon=np.array([[pos[0],neg[0]]]);la=np.array([[pos[1],neg[1]]])
   with patch.object(geometry,'lonlat_maps',return_value=(lon,la)),patch.object(geometry,'pixel_area_cm2',return_value=area),patch.object(geometry,'rsun_cm',return_value=R),patch.object(cycle,'assign_cycle',return_value=(cyc,1.,'synthetic')):
    m=measure.measure_v84(np.array([[1000.,-1000.]]),np.array([[33,33]]),{'T_REC':'2020.01.01_00:00:00_TAI'})
   d=m['d_axial_bal_g']; proposed=3*m['hale_sign']*m['s_bl']/(4*np.pi*R**3)
   corrected=-m['expected_leading_sign']*3*m['s_bl']/(8*np.pi*R**3)
   err=abs(corrected-d)/abs(d)
   assert m['hale_sign']==hale and err<1e-7
   rows.append(dict(cycle=cyc,latitude=lat,hale=hale,leading=m['leading_sign'],draft_over_exact=proposed/d,corrected_over_exact=corrected/d))
# Two opposite flux packets in the SAME latitude bin: nearest-cell deposition erases their moment.
s=np.array([.101,.109]);q=np.array([1.,-1.]);centres=np.array([.09,.11,.13])
nearest=np.argmin(abs(s[:,None]-centres),axis=1)
qn=np.bincount(nearest,weights=q,minlength=len(centres))
qc=np.zeros(len(centres))
for x,mass in zip(s,q):
 j=np.searchsorted(centres,x)-1;t=(x-centres[j])/(centres[j+1]-centres[j]);qc[j]+=mass*(1-t);qc[j+1]+=mass*t
moment=float(q@s);near=float(qn@centres);cic=float(qc@centres)
assert near==0 and abs(cic-moment)<1e-15 and abs(qc.sum())<1e-15
# Two individually normalised spherical Gaussian components. Overlap changes observable unsigned flux/centroids.
x=np.deg2rad(np.arange(-20.,20.0001,.05));y=np.deg2rad(np.arange(-20.,20.0001,.05))
xx,yy=np.meshgrid(x,y);dA=np.cos(yy)*np.deg2rad(.05)**2;sig=np.deg2rad(2.)
def blob(lon):
 delta=np.arccos(np.clip(np.cos(yy)*np.cos(xx-lon),-1,1));g=np.exp(-delta**2/(2*sig**2));return g/np.sum(g*dA)
gp,gn=blob(np.deg2rad(1.)),blob(np.deg2rad(-1.));b=gp-gn
phi_pos=float(np.sum(np.maximum(b,0)*dA));phi_neg=float(np.sum(np.maximum(-b,0)*dA))
p=b>0
centroid=geometry.weighted_centroid(np.rad2deg(xx[p]),np.rad2deg(yy[p]),b[p]*dA[p])
assert .37<phi_pos<.40 and abs(phi_pos-phi_neg)<1e-12 and 2.5<centroid[0]<2.8
pflow=2.33
peak_factor=(1/(1+pflow))**.5*(pflow/(1+pflow))**(pflow/2)
results=dict(sign_and_factor=rows,deposition=dict(exact_first_moment=moment,nearest_cell=near,linear_moment_conserving=cic),gaussian_overlap=dict(component_flux_each=1.,actual_positive_flux=phi_pos,actual_negative_flux=phi_neg,positive_anchor_lon_deg=1.,actual_positive_centroid_lon_deg=centroid[0]),transport=dict(p=pflow,published_eta=350.,published_Du_km_s=.041,published_vmax_m_s=1000*.041*peak_factor,source_default_eta=466.8,source_default_vmax_m_s=15.5,source_default_Du_km_s=.0155/peak_factor))
print(json.dumps(results,indent=2))

