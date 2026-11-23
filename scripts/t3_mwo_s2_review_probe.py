"""Synthetic review probes for the S2 diagnostic runner/recount (9106186); no observed data read.
Prints whether deliberately changed products or empty prerequisites are accepted.
These are review counterexamples, not a validation of the statistical procedure.
"""
import importlib.util,contextlib,io,json,tempfile,hashlib,shutil
from pathlib import Path
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,root/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=mod('dg','scripts/t3_mwo_s2_diagnosis.py');R=mod('rc','scripts/t3_mwo_s2_diagnosis_recount.py')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={}
# Design reconstructed independently, no real catalogue data.
base=D.synthetic();cases={'base':base,'north_only':base[base.hemisphere=='N'].copy(),'single_epoch':base[base.epoch=='E8'].copy(),'constant_activity':base.assign(A_main=1.),'rescaled_weights':base.assign(phi_mwo=base.phi_mwo*1e-20)}
report['design_cases']={}
for name,s in cases.items():
 ns,z,x=D.A.columns(s);inf,X=D.A.reduce(ns,z,x,s.phi_mwo.to_numpy(float));g=R.own_g(s)
 assert (g is not None)==inf['identifiable']
 err=None if g is None else float(np.max(np.abs(g-D.A.g_row(X,s.phi_mwo.to_numpy(float)))))
 assert err is None or err<1e-10
 report['design_cases'][name]={'identifiable':inf['identifiable'],'max_abs_g_difference':err}
ref=D.A.s2_fit(base);days=sorted(set(base.day));src={day:('GYUL' if i%3 else 'DEBR') for i,day in enumerate(days)}
products=D.build(base,src,(ref['beta'],ref['se']),reps=40)
# Use cached reference M values for FITS: real check(fit=...) reaches this same comparison;
# mutations below touch only products not compared to M by the recount.
cache={}
origfit=D.A.s2_fit
def fakefit(s):
 key=(tuple(s.noaa),hashlib.sha256(s.d_wl.to_numpy(float).tobytes()).hexdigest())
 if key not in cache:cache[key]=origfit(s)
 return cache[key]
with tempfile.TemporaryDirectory() as td:
 td=Path(td);orig=td/'base';D.write_atomic(orig,products,{})
 kw=dict(sub=base,src=src,s2_ref=(ref['beta'],ref['se']),fit=fakefit,reps=40,write=False,note=None)
 def check(p):
  with contextlib.redirect_stdout(io.StringIO()):return R.check(p,**kw)
 assert check(orig)
 report['synthetic_base_accepted']=True
 def mutate(name,fn):
  o=td/name;shutil.copytree(orig,o);fn(o)
  m=json.loads((o/'META.json').read_text());m['products_sha256']={n:h(o/n) for n in m['products_sha256']};(o/'META.json').write_text(json.dumps(m))
  report[name+'_accepted']=bool(check(o))
 def comp(o):
  p=o/'DECOMPOSITION.json';j=json.loads(p.read_text());j['M_gamma_wl']['se']=999.;j['M_gamma_wl']['lo']=-999.;j['M_gamma_wl']['hi']=999.;p.write_text(json.dumps(j))
 def param(o):
  p=o/'FITS.csv';f=pd.read_csv(p);f.loc[0,'phi']=123.;f.loc[0,'phi_at_bound']=False;f.to_csv(p,index=False)
 def cnt(o):
  p=o/'COUNTS.csv';f=pd.read_csv(p);f.loc[(f.item=='tercile dpd_area')&(f.label=='1'),'n']=99999;f.loc[f.item=='removed |d_WL|>45 by hemisphere','n']=99999;f.to_csv(p,index=False)
 mutate('D1_component_interval_tampered',comp);mutate('FITS_covariance_tampered',param);mutate('tercile_and_hemisphere_counts_tampered',cnt)
 # Strict receipt completeness and bindings are checked on synthetic directories only.
 for name in ['STAB','EST','REL','STAB_REC','EST_REC','REL_REC']:
  setattr(D,name,td/name);getattr(D,name).mkdir()
 for name,key in [('STAB','stability_meta_sha256'),('EST','estimate_meta_sha256'),('REL','release_meta_sha256')]:
  p=getattr(D,name);(p/'META.json').write_text(json.dumps({'products_sha256':{}}));(getattr(D,name+'_REC')/'RECEIPT.json').write_text(json.dumps({'passed':0,'total':0,'partial':False,'checks':[],key:h(p/'META.json')}))
 report['empty_receipts_and_empty_manifests_problems']=D.chain_problems()
print(json.dumps(report,indent=2))
