"""Synthetic counterexample for the review of f12d093. No real tilt is read.

Run from the BL repository; the output shows whether the reviewed guard accepts
these cases. This probe is separate from the method's scientific validation.
"""
from pathlib import Path
import importlib.util,json,tempfile
import numpy as np,pandas as pd
root=Path(__file__).resolve().parents[1]
def load(n):
 s=importlib.util.spec_from_file_location(n,root/'scripts'/f'{n}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=load('t3_mwo_analysis');r=load('t3_mwo_analysis_recount')
with tempfile.TemporaryDirectory() as td:
 td=Path(td);cat=td/'cat';chk=td/'check';val=td/'val'
 for p in (cat,chk,val):p.mkdir()
 d=a.synthetic_design(n_per=6);d.to_csv(cat/'DESIGN.csv',index=False)
 ident,kept,X,w=r.matrix(d);g=r.projection(X,w)
 truths={e:r.ramp_true(d,g,e) for e in (.1,.2)}
 (chk/'TARGETS.json').write_text(json.dumps({'delta_beta_10':truths[.1],'delta_beta_20':truths[.2]}));(chk/'META.json').write_text('{}')
 key=pd.MultiIndex.from_arrays([d.CR.astype(int),d.hemisphere]);codes,u=pd.factorize(key)
 cr=np.array([x for x,_ in u]);hh=np.array([h for _,h in u]);lp=np.log(w);lp-=lp.mean()
 pars={'var_a':np.log(225.),'var_b':0.,'phi':.5,'kappa':.25,'sigma_x2':56.25}
 from types import SimpleNamespace
 se=r.se_from_saved(SimpleNamespace(**pars),d,g,codes,cr,hh,lp)
 cfgs=a.configs()
 for c in cfgs:c['n']=3
 a.configs=lambda:cfgs
 r.grid=lambda:[(c['scenario'],c['sd_e'],c['effect'],3) for c in cfgs]
 rows=[]
 for c in cfgs:
  truth=truths[c['effect']] if c['effect'] else 0.
  lo,hi=truth-r.Z*se,truth+r.Z*se
  for k in range(3):
   rows.append(dict(cfg=c['cfg'],k=k,seed=a.seed(c['cfg'],k),role=c['role'],scenario=c['scenario'],sd_e=c['sd_e'],
      effect=c['effect'],truth=truth,beta=truth,se=se,lo=lo,hi=hi,covered=1,lo_above=0,hi_below=0,
      verdict='supportato' if hi<0 else 'opposto' if lo>0 else 'non deciso',**pars))
 raw=pd.DataFrame(rows)
 raw.loc[1,'sigma_x2']=np.nan
 tab,acc,problems=a.summarise(raw,truths)
 print('NaN variance parameter accepted by runner:',acc,problems)
 raw.to_csv(val/'RAW.csv.gz',index=False);tab.to_csv(val/'SUMMARY.csv',index=False)
 (val/'ACCEPTANCE.json').write_text(json.dumps({'accepted_15deg':acc,'problems':problems}))
 hashes={p.name:r.h256(p) for p in val.iterdir()}
 (val/'META.json').write_text(json.dumps({'products_sha256':hashes,'provenance_start':{'input':'unchanged'},'provenance_end':{'input':'unchanged'},'design_check_meta_sha256':r.h256(chk/'META.json')}))
 print('Independent recount result:',r.check_validation(cat,chk,val,td/'receipt',write=True))
 print('Receipt:',(td/'receipt/RECEIPT.json').read_text())
