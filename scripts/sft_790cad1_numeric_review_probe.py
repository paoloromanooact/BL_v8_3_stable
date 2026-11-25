"""Synthetic numerical review of proposed discretisations; no observed data or pilot run."""
import numpy as np,json
from pathlib import Path
from scipy.linalg import solve_banded
R=696000.;eta=466.8;N=400;ds=2/N;dt=86400.
faces=np.linspace(-1,1,N+1);c=eta/R**2*(1-faces**2)/ds**2
lower=c[1:-1];upper=lower.copy();diag=-(c[:-1]+c[1:])
u=np.zeros(N);u[N//2]=1.
def step(theta):
 ab=np.zeros((3,N));ab[0,1:]=-theta*dt*upper;ab[1]=1-theta*dt*diag;ab[2,:-1]=-theta*dt*lower
 rhs=(1+(1-theta)*dt*diag)*u;rhs[1:]+=(1-theta)*dt*lower*u[:-1];rhs[:-1]+=(1-theta)*dt*upper*u[1:]
 return solve_banded((1,1),ab,rhs)
cn=step(.5);be=step(1.)
assert cn.min()<-.25 and be.min()>=0 and abs(cn.sum()-1)<1e-12 and abs(be.sum()-1)<1e-12
p=2.33;fac=(1/(1+p))**.5*(p/(1+p))**(p/2);t=4.5*86400.;lat=15.;omega=14.713-2.396*np.sin(np.deg2rad(lat))**2-1.787*np.sin(np.deg2rad(lat))**4
margins=[]
for du in (.025,.041):
 diff=np.rad2deg(np.sqrt(4*eta*t)/R);flow=np.rad2deg(du*fac*t/R);rot=abs(omega-14.1844)*4.5
 margins.append(dict(Du=du,diffusion_deg=diff,meridional_deg=flow,rotation_deg=rot,margin_deg=diff+flow+rot+.5))
out=dict(pure_diffusion_impulse=dict(N=N,dt_s=dt,eta_km2_s=eta,CN_min=float(cn.min()),CN_mass=float(cn.sum()),BE_min=float(be.min()),BE_mass=float(be.sum())),margins_at_15deg_4p5days=margins)
print(json.dumps(out,indent=2))
