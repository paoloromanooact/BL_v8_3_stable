"""Independent algebraic contract checks for repeatability and proposed SFT convergence floor.
Synthetic finite vectors only, no random seeds, observations, SFT solvers or fits.
"""
import argparse,json,math
from pathlib import Path
import numpy as np

def run():
 checks=[]
 def ok(name,test,**values):checks.append(dict(name=name,ok=bool(test),**values))
 v=np.array([1.,-1.,1.,-1.]);w=np.array([1.,1.,-1.,-1.]);z=np.array([1.,-1.,-1.,1.])
 for rho in (0.,.5,.9,-.5):
  e0=v;e1=rho*v+math.sqrt(1-rho*rho)*w
  measured=float(np.var(e1-e0));expected=2*(1-rho)
  ok(f'known correlated errors rho={rho}',abs(measured-expected)<1e-14,variance_difference=measured,expected=expected)
 rho=.5;c=1.5;delta=rho*v+math.sqrt(1-rho*rho)*w-v+c*z
 ok('independent evolution adds variance',abs(np.var(delta)-(2*(1-rho)+c*c))<1e-14,variance_difference=float(np.var(delta)))
 inferred=math.sqrt(float(np.var(.5*v+math.sqrt(.75)*w-v))/2)
 ok('sqrt(2) conversion fails when errors correlated',abs(inferred-1)>.2,naive_single_sigma=inferred,true_single_sigma=1.)
 x=np.r_[np.ones(10),5.];weights=np.r_[np.full(10,1/20),.5]
 ok('each group has same total weight',abs(np.dot(x,weights)-3)<1e-14,weighted_mean=float(np.dot(x,weights)),pair_mean=float(np.mean(x)))
 x2=np.r_[np.ones(100),5.];weights2=np.r_[np.full(100,1/200),.5]
 ok('duplicating within one group leaves group target unchanged',abs(np.dot(x2,weights2)-np.dot(x,weights))<1e-14)
 axial=lambda a,b:(a-b+90)%180-90
 circ=lambda a,b:(a-b+180)%360-180
 ok('axial seam',axial(89.,-89.)==-2.)
 ok('longitude seam',circ(1.,359.)==2.)
 r=abs(np.mean(np.exp(2j*np.radians([89.,-89.]))));sd=.5*math.sqrt(-2*math.log(r))*180/math.pi
 ok('axial concentration near seam not linear spread',sd<2.,circular_sigma_deg=sd,linear_rms_deg=89.)
 # Removing all nodes connected to the protected pool must be transitive.
 adj={0:{1},1:{0,2},2:{1},3:set()};reached={0};pending=[0]
 while pending:
  for n in adj[pending.pop()]:
   if n not in reached:reached.add(n);pending.append(n)
 ok('protected component excludes indirect connections',reached=={0,1,2} and 3 not in reached)
 # Proper Gaussian marginal-likelihood references for BQ: no real-data inference.
 def log_marginal(y,X,V,C):
  y=np.asarray(y,float);S=C+X@V@X.T;L=np.linalg.cholesky(S)
  z=np.linalg.solve(L,y)
  return -.5*(len(y)*math.log(2*math.pi)+2*np.log(np.diag(L)).sum()+z@z)
 yy=np.array([0.]);xx=np.ones((1,1));cc=np.eye(1)
 lz=log_marginal(yy,xx,np.array([[4.]]),cc)
 ok('proper prior integrates to known marginal variance',abs(lz+.5*math.log(2*math.pi*5))<1e-14)
 l0=log_marginal(yy,np.empty((1,0)),np.empty((0,0)),cc)
 for tau in (1.,10.):
  l1=log_marginal(yy,xx,np.array([[tau*tau]]),cc)
  bf=math.exp(l0-l1)
  ok(f'null versus proper alternative prior scale {tau}',abs(bf-math.sqrt(1+tau*tau))<1e-12,BF01_at_zero=bf)
 corr=np.array([[1.,.9],[.9,1.]])
 x=np.ones(2);pv=1/(1+x@np.linalg.solve(corr,x));pv_ind=1/(1+x@x)
 ok('correlated measurements are not independent copies',pv>pv_ind and abs(pv-1/(1+2/1.9))<1e-14,posterior_variance_correlated=pv,posterior_variance_independent=pv_ind)
 examples=[]
 for floor in (.01,.1):
  ds=1.;median=1e-4;dm=2e-5;bc=dm;bf=bc+.0009*floor
  criterion=abs(bf-bc)/max(abs(bf),floor*ds)
  ratio_coarse=(bc-dm)/dm;ratio_fine=(bf-dm)/dm
  case=dict(floor=floor,D_scale=ds,m_t=median,D_M=dm,D_B_coarse=bc,D_B_fine=bf,criterion=criterion,passes=criterion<=1e-3,ratio_defined=abs(dm)>.1*median,ratio_change=ratio_fine-ratio_coarse)
  examples.append(case)
  ok(f'floor {floor} can pass while ratio changes substantially',case['passes'] and case['ratio_defined'] and case['ratio_change']>.4,**case)
 return dict(scope='algebraic checks and counterexamples, not SFT convergence or observed-error validation',passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks,ratio_counterexamples=examples)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);a=p.parse_args();r=run()
 if a.out:
  if a.out.exists():raise SystemExit('refusing overwrite')
  a.out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r,indent=2))
 raise SystemExit(0 if r['passed']==r['total'] else 1)
