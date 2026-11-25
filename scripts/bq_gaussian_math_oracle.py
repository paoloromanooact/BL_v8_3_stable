"""Independent deterministic BQ mathematical reference; no repository inputs or production inference code."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.linalg import cho_factor,cho_solve
from scipy.special import logsumexp,gammaln
from scipy.stats import norm

def gaussian(y,C):
    L=np.linalg.cholesky(C);z=np.linalg.solve(L,y)
    return float(-.5*(len(y)*math.log(2*math.pi)+2*np.log(np.diag(L)).sum()+z@z))

def folded(y,mu,sigma,images=12):
    if not -90<=y<=90: return 0.
    ks=np.arange(-images,images+1,dtype=float)
    logs=np.r_[norm.logpdf(y+360*ks,mu,sigma),norm.logpdf(180-y+360*ks,mu,sigma)]
    return float(np.exp(logsumexp(logs)))

def run():
    checks=[]
    def ok(name,test,**values): checks.append(dict(name=name,ok=bool(test),**values))
    times=np.array([0,2,5,6]);hem=np.array([0,1,0,1]);phi=-.6;kappa=-.3
    H=np.array([[1.,kappa],[kappa,1.]])
    K=1.3**2*phi**np.abs(times[:,None]-times[None,:])*H[hem[:,None],hem[None,:]]
    ok('Missing CR retain actual lags with signed AR coefficient',abs(K[0,2]-1.3**2*phi**5)<1e-14 and np.linalg.eigvalsh(K).min()>0)
    # Full CR grid bivariate stationary covariance, independent recursive construction.
    Hfull=np.kron(phi**np.abs(np.arange(7)[:,None]-np.arange(7)[None,:]),H)*1.3**2
    keep=2*times+hem
    ok('Full-grid submatrix agrees with direct observed covariance',np.max(np.abs(Hfull[np.ix_(keep,keep)]-K))<1e-14)
    Z=np.array([[1.,0.],[1.,0.],[0.,1.],[0.,0.]])
    noise=np.array([.7,1.2,.8,1.1])**2
    fam_cov=Z@Z.T*.4**2
    d=noise.copy();d[2]+=.4**2
    Zrep=Z[:,:1]
    ok('Gaussian singleton integration equals diagonal addition',np.max(abs(np.diag(noise)+fam_cov-(np.diag(d)+Zrep@Zrep.T*.4**2)))<1e-14)
    # Covariance low-rank identity, fixed deterministic vectors.
    y=np.array([.3,-.8,1.2,.7]);U=np.array([[1.,.2],[.2,1.],[-.3,.8],[.7,-.2]])
    Q=np.array([[1.3,.2],[.2,.9]]);D=np.diag(noise)
    C=D+U@Q@U.T
    A=np.linalg.inv(Q)+U.T@np.diag(1/noise)@U
    rhs=U.T@(y/noise)
    qform=y@(y/noise)-rhs@np.linalg.solve(A,rhs)
    logdet=np.log(noise).sum()+np.linalg.slogdet(Q)[1]+np.linalg.slogdet(A)[1]
    ll=-.5*(len(y)*math.log(2*math.pi)+logdet+qform)
    ok('Woodbury determinant and quadratic agree with dense Cholesky',abs(ll-gaussian(y,C))<1e-12,error=float(ll-gaussian(y,C)))
    X=np.array([[1.,.2],[1.,-.8],[1.,.4],[1.,1.1]])
    V=np.diag([2.,.9]);S=C+X@V@X.T
    Cinv=cho_solve(cho_factor(C),np.eye(4))
    P=np.linalg.inv(V)+X.T@Cinv@X
    postcov=np.linalg.inv(P);postmean=postcov@X.T@Cinv@y
    # Gaussian evidence identity and nested Savage-Dickey with nuisance coefficient.
    lq=gaussian(y,S);l0=gaussian(y,C+np.outer(X[:,0],X[:,0])*V[0,0])
    logsd=norm.logpdf(0,postmean[1],math.sqrt(postcov[1,1]))-norm.logpdf(0,0,math.sqrt(V[1,1]))
    ok('Savage-Dickey matches exact nested evidence with compatible nuisance prior',abs(logsd-(l0-lq))<1e-12,logBF0Q=l0-lq)
    # Conditional prediction of held-out correlated observations.
    train=np.array([0,2]);test=np.array([1,3]);Stt=S[np.ix_(train,train)];Svt=S[np.ix_(test,train)]
    pm=Svt@np.linalg.solve(Stt,y[train]);pc=S[np.ix_(test,test)]-Svt@np.linalg.solve(Stt,Svt.T)
    cond=gaussian(y[test]-pm,pc)
    ok('Joint block prediction equals joint minus training log-density',abs(cond-(gaussian(y,S)-gaussian(y[train],Stt)))<1e-12)
    naive=sum(norm.logpdf(y[test],pm,np.sqrt(np.diag(pc))))
    ok('Independent pointwise score differs from correlated block score',abs(naive-cond)>1e-4,difference=float(naive-cond))
    # Folded density: normalization, symmetry, Jacobian in degree units and mean.
    for mu,sigma in [(25.,12.),(120.,30.),(-35.,150.)]:
        integral=quad(lambda z:folded(z,mu,sigma),-90,90,epsabs=1e-10)[0]
        ok(f'Folded density normalizes mu={mu} sigma={sigma}',abs(integral-1)<1e-10,integral=integral)
    ok('Folded density aliases latent mu+360 and 180-mu',abs(folded(17.,25.,30.)-folded(17.,385.,30.))<1e-14 and abs(folded(17.,25.,30.)-folded(17.,155.,30.))<1e-14)
    # Wide sigma makes a fixed three-image approximation demonstrably unsafe.
    wide=quad(lambda z:folded(z,25.,400.,images=1),-90,90)[0]
    ok('Three-image truncation need not normalize for broad scales',wide<.9,integral=wide)
    # Singleton normal plus t noise is not a t with added variance.
    nu=4.;sigma=1.;sf=.8
    def tpdf(z,scale):
        return math.exp(gammaln((nu+1)/2)-gammaln(nu/2))/(math.sqrt(nu*math.pi)*scale)*(1+z*z/(nu*scale*scale))**(-(nu+1)/2)
    conv=quad(lambda b:norm.pdf(b,0,sf)*tpdf(-b,math.sqrt(.5)),-8,8,epsabs=1e-10)[0]
    shortcut=tpdf(0,math.sqrt((1+sf*sf)/2))
    ok('Student singleton integration is convolution not variance-inflated Student',abs(conv-shortcut)>1e-3,convolution=conv,shortcut=shortcut)
    # Short-lag correlations can make difference scale smaller, without changing single-measurement variance.
    ratio=math.sqrt((1-.8)/(1-0.))
    ok('Short-lag difference need not bound day-lag difference',ratio<.5,short_to_day_scale=ratio)
    return dict(scope=__doc__,passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);a=p.parse_args();r=run()
    if a.out:
        with a.out.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed']==r['total'] else 1)
