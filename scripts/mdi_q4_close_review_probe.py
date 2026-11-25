"""Q4 fed1775: synthetic independent numeric checks, no MDI design run or tilt read.
Uses scipy Normal CDF and a direct weighted least-squares solve for expected values; production dependencies are imported.
"""
import importlib.util,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('Q',ROOT/'scripts/mdi_q4_prospective.py');Q=importlib.util.module_from_spec(s);s.loader.exec_module(Q)
checks=[]
def ok(n,c):checks.append(dict(name=n,ok=bool(c)))
rng=np.random.default_rng(60413);n=120
R=pd.DataFrame(dict(CR=np.repeat(np.arange(2000,2030),4),hem=np.tile(['N','S'],60),sinlat=rng.uniform(.1,.6,n),lat=rng.uniform(5,30,n),cyc=23,A=rng.uniform(.1,3.,n),M=np.r_[np.ones(60),np.zeros(60)],phi=rng.uniform(1,5,n),t_years=np.linspace(-12,0,n),act_class=rng.integers(1,4,n)))
u=dict(d3=1.6,sbar=.3);dprod=(-.5,-.8,-1.2)
a=Q.analyse(R,('a',),True,d_prod=dprod,u=u)['a']
w=R.phi.to_numpy();sin=R.sinlat.to_numpy();activity=R.A.to_numpy();mdi=R.M.to_numpy()
X=np.column_stack([sin*(R.hem.to_numpy()=='N'),sin*(R.hem.to_numpy()=='S'),(activity-1)*sin])
g=np.linalg.solve(X.T@(w[:,None]*X),X.T*w)[-1]
ab=R.groupby(['CR','hem']).A.transform('mean').to_numpy();quant=np.quantile(ab,[.05,.95])
ok('identifiable synthetic design',a['status']=='ok')
ok('record variance coefficients match independent WLS solve',np.isclose(a['a2'],np.sum(g*g),rtol=1e-10) and np.isclose(a['a2_mdi'],np.dot(g*g,mdi),rtol=1e-10))
for suffix,lo,hi in [('020',Q.A_LO_E0,Q.A_HI_E0),('010',Q.A_LO_E0,Q.A_HI_E0),('qd_020',*quant),('qd_010',*quant)]:
 width=.2 if suffix.endswith('020') else .1
 target=g@(-24*width*np.clip((ab-lo)/(hi-lo),0,1)*sin)
 ok('target independently projected '+suffix,np.isclose(a['target_'+suffix],target,rtol=1e-10,atol=1e-12))
mprod=g@np.where(mdi==1,np.array(dprod)[R.act_class.to_numpy()-1],0)
ok('product difference projection matches independent WLS solve',np.isclose(a['m_prod'],mprod,rtol=1e-10,atol=1e-12))
noise=next(i for i,x in enumerate(Q.NOISE) if x[1:]==(1,1.0));row=Q.noise_rows(a,[noise],[(15.,2.)],u=u)[0]
se=np.sqrt(225*a['a2']+4*a['a2_mdi']+56.25*a['bKb'][(1,False)])
ok('variance scaling and SE',np.isclose(row['se'],se,rtol=1e-12))
for suffix in Q.TARGETS:
 target=a['target_'+suffix]
 ok('SE/target '+suffix,np.isclose(row['se_over_target_'+suffix],se/abs(target),rtol=1e-12))
 ok('normal recognition '+suffix,np.isclose(row['recognition_'+suffix],norm.cdf(-Q.PA.Z-target/se),rtol=1e-12))
 ok('product shift/target '+suffix,np.isclose(row['m_prod_over_target_'+suffix],mprod/abs(target),rtol=1e-10,atol=1e-12))
 for fam,unit in [('A',u['d3']*u['sbar']),('J',u['d3'])]:
  slope=g@(mdi*(activity-1)*(sin if fam=='J' else 1.))
  tol=.5*abs(target)/(unit*abs(slope))
  ok('tolerance '+fam+' '+suffix,np.isclose(row['tol_units_'+fam+'_'+suffix],tol,rtol=1e-9))
  for C in (.25,.5):
   shifts=[C*unit*slope,-C*unit*slope]
   expected=min(norm.cdf(-Q.PA.Z-(target+x)/se) for x in shifts)
   ok('both-sign worst case '+fam+' '+str(C)+' '+suffix,np.isclose(row[f'sup_scen_worst_{fam}_C{C}_{suffix}'],expected,rtol=1e-11,atol=1e-13))
zero=dict(a,**{f'target_{t}':0. for t in Q.TARGETS})
z=Q.noise_rows(zero,[noise],[(15.,2.)],u=u)[0]
ok('all four zero targets keep SE and normal-null frequency',np.isfinite(z['se']) and all(z[f'target_null_{t}'] and np.isnan(z[f'se_over_target_{t}']) and np.isnan(z[f'm_prod_over_target_{t}']) and np.isclose(z[f'recognition_{t}'],norm.cdf(-Q.PA.Z)) for t in Q.TARGETS))
ok('empty design returns explicit state',Q.analyse(R.iloc[:0],('a','bA','bJ'),True)['a']['status']=='empty_design')
# Entirely failed and single-failure configurations: summary must retain keys and proper denominators.
base=dict(design='MS',threshold='main',variant='ref',model='a',sigma_int=15.,sigma_m=2.,noise=noise,form='ar1',scen=1,x_scale=1.)
rows=[dict(base,r=i,status='empty_design',se=np.nan) for i in range(20)]
summary,_=Q.summarise(pd.DataFrame(rows),20)
ok('all 20 failures retained in SUMMARY',len(summary)==1 and summary.n_ok.iloc[0]==0 and summary.n_fail.iloc[0]==20)
rows[0].update(status='ok',se=2.);summary,_=Q.summarise(pd.DataFrame(rows),20)
ok('one success and 19 failures retained',summary.n_ok.iloc[0]==1 and summary.n_fail.iloc[0]==19)
try:Q.summarise(pd.DataFrame(rows+[rows[0]]),20);ok('duplicate realisation rejected',False)
except Q.TechnicalError:ok('duplicate realisation rejected',True)
ok('real frozen receipts remain valid without changing any files',Q.receipts_ok()==[])
result=dict(passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks,script_sha256=hashlib.sha256((ROOT/'scripts/mdi_q4_prospective.py').read_bytes()).hexdigest(),mdi_precision_computed=False,synthetic_only=True)
print(json.dumps(result,indent=2));raise SystemExit(0 if all(c['ok'] for c in checks) else 1)
