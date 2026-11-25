"""Independent synthetic checks of preparatory SFT code; no observed data or scientific pilot."""
from pathlib import Path
import sys,json,hashlib
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'python'))
from sharpbl import sft_core as C,sft_local as L
out={'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['python/sharpbl/sft_core.py','python/sharpbl/sft_local.py','scripts/sft_prep_selftest.py']}}
# Non-negative field must stay non-negative, separately for each physical polarity component.
m=C.SFT1D(du_kms=0.);b=np.zeros(m.n);b[m.n//2]=1.;z=m.evolve(b,[C.DAY])[0]
out['one_dimensional_diffusion']={'minimum':float(z.min()),'mass_over_initial':float(z.sum())}
a=C.SFT1D(eta_km2s=0.);b=np.zeros(a.n);b[np.argmin(abs(a.s-np.sin(np.deg2rad(15))))]=1.;z=a.evolve(b,[600.],dt_s=600.)[0]
out['one_dimensional_advection']={'minimum':float(z.min()),'mass_over_initial':float(z.sum())}
box=L.LocalBox((14,16),(0,4),step_deg=.1,diffusion=False,meridional=False)
B=np.zeros((box.ny,box.nx));B[:,(box.lon>1.5)&(box.lon<2.0)]=1.
z=box.step_once(B)
out['two_dimensional_advection']={'minimum':float(z.min()),'mass_over_initial':float((z*box.A).sum()/(B*box.A).sum())}
d=L.LocalBox((59,61),(0,2),step_deg=.06,rotation=False,meridional=False)
B=np.zeros((d.ny,d.nx));B[d.ny//2,d.nx//2]=1.;z=d.step_once(B)
out['two_dimensional_diffusion']={'minimum':float(z.min()),'mass_over_initial':float((z*d.A).sum()/(B*d.A).sum())}
# Opposite pixels separated by the HMI pixel pitch (.03 deg) mapped onto a .06 deg grid.
e=L.LocalBox((-.3,.3),(.7,1.3),step_deg=.06,rotation=False,meridional=False)
lat=np.array([-.015,.015]);lon=np.array([1.,1.]);flux=np.array([1.,-1.])
B,nout=e.deposit(lat,lon,flux);me=e.measures(B)
true_D=3/(4*np.pi*e.r**2)*float(flux@np.sin(np.deg2rad(lat)))
out['mixed_polarity_deposit']={'outside':nout,'original_phi_pos':1.,'original_phi_neg':1.,'mapped_phi_pos':me['phi_pos'],'mapped_phi_neg':me['phi_neg'],'D_ratio':me['D_g']/true_D,'original_lat_pos':lat[0],'mapped_lat_pos':me['lat_pos']}
# Demonstrate the geometry/spacing request without allocating an enormous wrap-crossing Gaussian grid.
class Captured(Exception):pass
bounds={}
def capture(la,lo,step,*args,**kw):bounds.update(lat_range=la,lon_range=lo,step=step);raise Captured
with patch.object(C,'sphere_grid',side_effect=capture):
 try:C.gaussian_bipole((179.,15.),(-179.,15.),.2,1.,1.)
 except Captured:pass
out['gaussian_requested_grid']=dict(bounds,longitude_width=bounds['lon_range'][1]-bounds['lon_range'][0],allowed_step_from_smallest_sigma=.02)
# Required finite T_OBS interval, not necessarily a multiple of 600 s.
B=np.zeros((box.ny,box.nx));B[5,5]=1.
for t in (601.,-600.):
 try:z=box.evolve(B,t);result={'accepted':True,'unchanged':bool(np.array_equal(z,B))}
 except Exception as x:result={'accepted':False,'error_type':type(x).__name__,'error':str(x)}
 out[f'elapsed_seconds_{t:g}']=result
# Validation of spherical coordinates/areas and lone-polarity output.
latg,long,ar=C.sphere_grid((89.,91.),(-1.,1.),.1)
out['invalid_latitude_grid']={'negative_areas':int((ar<0).sum()),'area_min':float(ar.min())}
one=C.field_measures([15.],[20.],[1.],[1.]);out['one_polarity_centroid']={'positive_flux':one['phi_pos'],'lon_pos':one['lon_pos'],'lat_pos':one['lat_pos']}
assert out['one_dimensional_diffusion']['minimum']<-.27
assert out['two_dimensional_advection']['minimum']<0
assert abs(out['mixed_polarity_deposit']['D_ratio']-1)<1e-12
assert abs(out['mixed_polarity_deposit']['mapped_phi_pos']-.5)<1e-5
print(json.dumps(out,indent=2))
