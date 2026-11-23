"""Independent R4 validation review: RAW only contains synthetic responses; real SEALED is never read.
All SEs are reconstructed using a QR WLS row and lag-polynomial covariance aggregation.
"""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np,pandas as pd
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 v=ROOT/'results/T3_MWO_VALIDATION_R4';c=ROOT/'results/T3_MWO_CATALOGUE_R4';q=ROOT/'results/T3_MWO_DESIGN_CHECK_R4'
 meta=read(v/'META.json');assert meta['provenance_start']==meta['provenance_end']
 for n,h in meta['products_sha256'].items():assert sha(v/n)==h
 for n,h in meta['provenance_start'].items():
  assert sha(ROOT/n)==h
  assert hashlib.sha256(subprocess.check_output(['git','show',meta['start_commit']+':'+n],cwd=ROOT)).hexdigest()==h
 assert meta['design_check_meta_sha256']==sha(q/'META.json')
 recpath=ROOT/'results/T3_MWO_VALIDATION_R4_RECOUNT/RECEIPT.json';rec=read(recpath)
 assert rec['passed']==rec['total']==8 and rec['partial'] is False and rec['technical_ok'] is True
 assert len(rec['checks'])==8 and all(t['ok'] is True for t in rec['checks']) and rec['validation_meta_sha256']==sha(v/'META.json')
 rd=read(ROOT/'results/T3_MWO_VALIDATION_R4_READING/READ.json')
 assert rd['acceptance_sha256']==sha(v/'ACCEPTANCE.json') and rd['recount_receipt_sha256']==sha(recpath)
 assert rd['accepted_15deg'] is True and rd['path']=='verdetto possibile'
 raw=pd.read_csv(v/'RAW.csv.gz');summary=pd.read_csv(v/'SUMMARY.csv');targets=read(q/'TARGETS.json')
 grid=[(s,15.,0.,10000) for s in [0,1,2,7,9]]+[(s,15.,e,2000) for s in [1,2,7,9] for e in [.1,.2]]+[(s,25.,0.,2000) for s in [0,1,2,7,9]]
 assert len(raw)==76000 and not raw.duplicated(['cfg','k']).any() and not raw.seed.duplicated().any()
 z=norm.ppf(.9875);ok=raw.verdict!='errore';a=raw[ok]
 assert raw.verdict.isin(['errore','supportato','opposto','non deciso']).all()
 assert np.isfinite(a[['beta','se','lo','hi','var_a','var_b','phi','kappa','sigma_x2','truth']]).all().all()
 assert a.se.gt(0).all() and a.phi.between(0,.98).all() and a.kappa.abs().le(.98).all() and a.sigma_x2.gt(0).all()
 assert (abs(a.lo-a.beta+z*a.se)<=1e-9*a.se).all() and (abs(a.hi-a.beta-z*a.se)<=1e-9*a.se).all()
 assert (a.verdict==np.where(a.hi<0,'supportato',np.where(a.lo>0,'opposto','non deciso'))).all()
 assert (a.covered==((a.lo<=a.truth)&(a.truth<=a.hi)).astype(int)).all()
 assert (a.lo_above==(a.lo>a.truth).astype(int)).all() and (a.hi_below==(a.hi<a.truth).astype(int)).all()
 rows=[]
 for i,(scenario,sd,e,n) in enumerate(grid):
  b=raw[raw.cfg==i];assert len(b)==n and sorted(b.k)==list(range(n))
  assert (b.seed==60000000+100000*i+b.k).all() and b.scenario.eq(scenario).all() and b.sd_e.eq(sd).all() and b.effect.eq(e).all()
  truth=0. if e==0 else targets['delta_beta_'+str(round(100*e))]
  assert np.allclose(b.loc[b.verdict!='errore','truth'],truth,rtol=0,atol=1e-12)
  good=b[b.verdict!='errore'];sp=b.verdict.eq('supportato').sum()/n;op=b.verdict.eq('opposto').sum()/n;er=b.verdict.eq('errore').sum()/n
  cv=good.covered.sum()/n;tail=good.lo_above.sum()/n
  crit=(sp+op<=.03 and sp<=.0175 and op<=.0175 and er<=.01) if e==0 else (cv>=.965 and tail<=.02)
  saved=summary[summary.cfg==i];assert len(saved)==1
  for name,val in [('supportato',sp),('opposto',op),('frac_errors',er),('coverage',cv),('exclusion_tail',tail)]:assert abs(saved.iloc[0][name]-val)<1e-12
  assert bool(saved.iloc[0].criteria_ok)==bool(crit)
  rows.append(dict(cfg=i,scenario=scenario,sd=sd,effect=e,criteria=bool(crit),false_total=sp+op,coverage=cv,power=sp))
 assert read(v/'ACCEPTANCE.json')=={'accepted_15deg':all(r['criteria'] for r in rows if r['sd']==15),'problems':[]}
 # WLS matrix rebuilt from the frozen model, without importing runner or recount.
 d=pd.read_csv(c/'DESIGN.csv');d=d[d.record_set=='isolated'].reset_index(drop=True);w=d.phi_mwo.to_numpy();sl=d.sinlat.to_numpy()
 columns=[]
 for cy in sorted(d.cycle.unique()):
  for h in 'NS':
   mask=((d.cycle==cy)&(d.hemisphere==h)).to_numpy()
   if mask.any():columns.append(sl*mask)
 order=['E'+str(i) for i in range(1,9)];refs={}
 for h in 'NS':
  count=d.loc[d.hemisphere==h,'epoch'].value_counts();refs[h]=sorted(count.index,key=lambda e:(-count[e],order.index(e)))[0]
 for ep in order:
  for h in 'NS':
   mask=((d.epoch==ep)&(d.hemisphere==h)).to_numpy()
   if mask.any() and ep!=refs[h]:columns.append(sl*mask)
 X=np.column_stack(columns+[(d.A_main.to_numpy()-1)*sl]);sw=np.sqrt(w)
 assert np.linalg.matrix_rank(X*sw[:,None])==X.shape[1]
 Q,R=np.linalg.qr(X*sw[:,None]);g=np.linalg.solve(R,Q.T)[-1]*sw
 cr=d.CR.to_numpy(int);hemi=d.hemisphere.eq('S').to_numpy(int);L=int(cr.max()-cr.min()+1)
 b=np.bincount(2*(cr-cr.min())+hemi,weights=g,minlength=2*L).reshape(L,2)
 same=np.zeros(L);cross=np.zeros(L)
 for lag in range(L):
  p=b[:L-lag];t=b[lag:];factor=1 if lag==0 else 2
  same[lag]=factor*np.sum(p*t);cross[lag]=factor*np.sum(p[:,0]*t[:,1]+p[:,1]*t[:,0])
 phi=a.phi.to_numpy();kap=a.kappa.to_numpy()
 temporal=a.sigma_x2.to_numpy()*(np.polynomial.polynomial.polyval(phi,same)+kap*np.polynomial.polynomial.polyval(phi,cross))
 lp=np.log(w);lp-=lp.mean();individual=np.empty(len(a));g2=g*g
 for lo in range(0,len(a),256):
  part=a.iloc[lo:lo+256]
  individual[lo:lo+len(part)]=np.exp(part.var_a.to_numpy())*(np.exp(part.var_b.to_numpy()[:,None]*lp)@g2)
 se=np.sqrt(temporal+individual);dev=abs(se/a.se.to_numpy()-1)
 assert np.isfinite(se).all() and (dev<1e-8).all()
 result=dict(rows=len(raw),successful_SE=len(a),M_fit_errors=int((~ok).sum()),max_relative_SE_deviation=float(dev.max()),main_accepted=True,all_18_criteria=all(r['criteria'] for r in rows),configurations=rows,validation_meta_sha256=sha(v/'META.json'),reading_sha256=sha(ROOT/'results/T3_MWO_VALIDATION_R4_READING/READ.json'))
 print(json.dumps(result,indent=2));return result
if __name__=='__main__':main()
