"""Independent mathematical fixtures for SFT tests. No production SFT import, observed map, network or PDE solver.

--selftest checks these reference formulas, not Claude's solvers. --write-fixtures creates a new directory only.
The characteristic oracle solves a scalar travel-time quadrature, not an SFT field evolution.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,platform
from pathlib import Path
import numpy as np
import scipy
from numpy.polynomial import Legendre
from scipy.integrate import quad
from scipy.optimize import brentq

R_KM=696000.; R_CM=R_KM*1e5
DAY=86400.; YEAR=365.25*DAY
TIMES=(0.,601.,27.*DAY,.5*YEAR,YEAR,3.*YEAR)


def mode_cell_means(l,n):
    """Exact averages of P_l(s) over uniform s cells, evaluated via its antiderivative."""
    if l<0 or n<2:raise ValueError('l >= 0, n >= 2 required')
    e=np.linspace(-1.,1.,n+1);p=Legendre.basis(l).integ()
    return (p(e[1:])-p(e[:-1]))/(2./n)


def mode_decay(l,eta_km2s,t_s):
    if l<0 or eta_km2s<0 or t_s<0:raise ValueError('non-negative l, eta, t required')
    return float(np.exp(-l*(l+1)*eta_km2s*t_s/R_KM**2))


def gaussian_first_moment(sigma_deg):
    """<cos(delta)> for a spherical Gaussian. u=delta/sigma resolves narrow spots.
    exp(-u^2/2) beyond u=12 is negligible; this scalar quadrature does not construct a map.
    """
    if not np.isfinite(sigma_deg) or not 0<sigma_deg<=10:raise ValueError('supported reference range: 0 < sigma <= 10 deg')
    sig=np.deg2rad(sigma_deg);top=min(np.pi/sig,12.)
    den=quad(lambda u:np.exp(-u*u/2)*np.sin(sig*u),0.,top,epsabs=1e-14,epsrel=1e-12)[0]
    num=quad(lambda u:np.exp(-u*u/2)*np.cos(sig*u)*np.sin(sig*u),0.,top,epsabs=1e-14,epsrel=1e-12)[0]
    return float(num/den)


def gaussian_dipole(lat_pos,lat_neg,sig_pos,sig_neg,phibar):
    return float(3.*phibar/(4.*np.pi*R_CM**2)*(gaussian_first_moment(sig_pos)*np.sin(np.deg2rad(lat_pos))-gaussian_first_moment(sig_neg)*np.sin(np.deg2rad(lat_neg))))


def omega_rel(lat_deg):
    s2=np.sin(np.deg2rad(lat_deg))**2
    return float(14.713-2.396*s2-1.787*s2*s2-14.1844)


def characteristic(lat0_deg,lon0_deg,t_s,du_kms=0.025,p=2.33):
    """Axisymmetric meridional-advection characteristic, without diffusion. Returns latitude, unwrapped longitude,
    and the multiplier of a smooth 1D flux density b(s) along this characteristic (not a change of packet flux).
    """
    if not np.isfinite(t_s) or t_s<0 or t_s>4.5*DAY or du_kms<0 or abs(lat0_deg)>60:raise ValueError('reference domain violated')
    s0=float(np.sin(np.deg2rad(lat0_deg)));q=.5*(p+1.)
    if t_s==0:return float(lat0_deg),float(lon0_deg),1.
    if du_kms==0:return float(lat0_deg),float(lon0_deg+omega_rel(lat0_deg)*t_s/DAY),1.
    if s0==0:return 0.,float(lon0_deg+omega_rel(0.)*t_s/DAY),float(np.exp(-du_kms*t_s/R_KM))
    y0=abs(s0);scale=R_KM/du_kms
    inv=lambda y:1./(y*(1.-y*y)**q)
    travel=lambda y:scale*quad(inv,y0,y,epsabs=1e-14,epsrel=1e-12)[0]
    upper=min(.999999,y0+.1)
    if travel(upper)<t_s:raise ValueError('characteristic outside quadrature bracket')
    y1=brentq(lambda y:travel(y)-t_s,y0,upper,xtol=1e-14,rtol=1e-14)
    lat1=float(np.rad2deg(np.arcsin(np.copysign(y1,s0))))
    dl=scale/DAY*quad(lambda y:omega_rel(np.rad2deg(np.arcsin(y)))*inv(y),y0,y1,epsabs=1e-14,epsrel=1e-12)[0]
    density=(y0*(1-y0*y0)**q)/(y1*(1-y1*y1)**q)
    return lat1,float(lon0_deg+dl),float(density)


def fixtures():
    modes=[]
    n=400;s=-1.+(np.arange(n)+.5)*2/n
    for l in range(4):
        b0=mode_cell_means(l,n);d0=1.5*float(b0@s)*2/n
        for eta in (350.,466.8):
            for t in TIMES:
                f=mode_decay(l,eta,t)
                modes.append(dict(l=l,n=n,eta_km2_s=eta,t_s=t,decay_factor=f,continuum_dipole_g=f if l==1 else 0.,midpoint_dipole_of_exact_cellmeans_g=d0*f))
    gaussian=[]
    for lp,ln,sp,sn in [(15.,14.,.2,.2),(15.,14.,2.,2.),(15.,14.,4.,4.),(15.,14.,.2,1.),(20.,-20.,1.,4.)]:
        gaussian.append(dict(lat_pos_deg=lp,lat_neg_deg=ln,sigma_pos_deg=sp,sigma_neg_deg=sn,component_flux_mx=1e21,moment_pos=gaussian_first_moment(sp),moment_neg=gaussian_first_moment(sn),dipole_g=gaussian_dipole(lp,ln,sp,sn,1e21)))
    markers=[]
    for lat in (-45.,-15.,0.,15.,45.):
        for du in (0.,.025,.041):
            for t in (0.,601.,DAY,4.5*DAY):
                la,lo,density=characteristic(lat,179.,t,du)
                markers.append(dict(lat0_deg=lat,lon0_deg=179.,t_s=t,du_km_s=du,p=2.33,lat1_deg=la,lon1_unwrapped_deg=lo,lon1_wrapped_deg=(lo+180.)%360.-180.,density_multiplier_1d=density))
    decay=[dict(t_s=t,tau_s=tau*YEAR,factor=float(np.exp(-t/(tau*YEAR)))) for tau in (5.,10.) for t in TIMES]
    return {'SPHERICAL_MODES.csv':modes,'GAUSSIAN_DIPOLES.csv':gaussian,'CHARACTERISTICS.csv':markers,'UNIFORM_DECAY.csv':decay}


def selftest():
    checks=[]
    def ok(n,c):checks.append({'name':n,'ok':bool(c)})
    for l in range(4):
        v=mode_cell_means(l,400)
        ok(f'mode {l}: exact cell masses integrate correctly',abs(v.sum()*2/400-(2. if l==0 else 0.))<1e-13)
        ok(f'mode {l}: zero diffusion leaves the mode unchanged',mode_decay(l,0.,YEAR)==1.)
    c=gaussian_first_moment(.2);x=np.deg2rad(.2)**2
    ok('narrow spherical Gaussian has the correct first-moment expansion',abs(c-(1-x+2*x*x/3))<1e-12)
    ok('Gaussian finite width reduces the first moment monotonically',1.>gaussian_first_moment(.2)>gaussian_first_moment(2.)>gaussian_first_moment(4.)>0.)
    ok('identical coincident opposite components have zero dipole',gaussian_dipole(15.,15.,2.,2.,1e21)==0.)
    ok('reflecting Gaussian centres reverses the axial dipole',abs(gaussian_dipole(15.,14.,.2,1.,1e21)+gaussian_dipole(-15.,-14.,.2,1.,1e21))<1e-16)
    for du in (.025,.041):
        n=characteristic(15.,179.,4.5*DAY,du);s=characteristic(-15.,179.,4.5*DAY,du)
        ok(f'characteristic Du={du}: hemispheric symmetry, positive density, poleward motion',n[0]>15 and s[0]<-15 and abs(n[0]+s[0])<1e-12 and abs(n[1]-s[1])<1e-12 and n[2]>0 and abs(n[2]-s[2])<1e-12)
    for du in (.025,.041):
        errors=[]
        for lat in (-15.,15.):
            for t in (601.,4.5*DAY):
                z=float(np.sin(np.deg2rad(lat)));e=float(np.exp(-2*du*t/R_KM));a=z*z+(1-z*z)*e
                exact_lat=float(np.rad2deg(np.arcsin(z/np.sqrt(a))));exact_density=a**1.5/e
                la,_,rho=characteristic(lat,179.,t,du,p=1.)
                errors.append(max(abs(la-exact_lat),abs(rho-exact_density)))
        ok(f'characteristic Du={du}: agrees with independent analytic p=1 logistic solution',max(errors)<1e-10)
    _,lo,_=characteristic(15.,179.,4.5*DAY,0.)
    ok('Carrington rotation marker follows the exact relative rate',abs(lo-179.-omega_rel(15.)*4.5)<1e-12)
    ok('fractional duration 601 seconds is a valid reference',all(np.isfinite(characteristic(15.,179.,601.,.025))))
    for name,fn in [('negative elapsed time',lambda:characteristic(15.,0.,-1.)),('zero Gaussian width',lambda:gaussian_first_moment(0.))]:
        try:fn();refused=False
        except ValueError:refused=True
        ok(name+' rejected',refused)
    out={'passed':sum(x['ok'] for x in checks),'total':len(checks),'checks':checks,'scope':'reference formulas only; does not validate production SFT code'}
    print(json.dumps(out,indent=2));return out


def write_fixtures(folder):
    folder=Path(folder)
    if folder.exists():raise ValueError('refusing to overwrite a fixture directory')
    folder.mkdir(parents=True)
    for name,rows in fixtures().items():
        with (folder/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    meta={'schema':1,'synthetic_only':True,'observed_maps_read':False,'production_sft_imported':False,'pde_solver_run':False,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'R_km':R_KM,'year_s':YEAR,'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'products_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('*.csv'))}}
    (folder/'META.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True);g.add_argument('--selftest',action='store_true');g.add_argument('--write-fixtures',type=Path);a=ap.parse_args()
    if a.selftest:
        r=selftest();raise SystemExit(0 if r['passed']==r['total'] else 1)
    write_fixtures(a.write_fixtures)
