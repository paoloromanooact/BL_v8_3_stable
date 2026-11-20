"""Synthetic residual cases for stability recount 7fd1121; no real seal read."""
from pathlib import Path
import contextlib, importlib.util, io, json, sys, tempfile
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np, pandas as pd
ROOT=Path('/home/gianluca/BL_v8_3_stable')
s=importlib.util.spec_from_file_location('stability_review',ROOT/'scripts/t3_mwo_stability_recount.py')
R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
results={}
with tempfile.TemporaryDirectory() as td:
 kw,frames,save,iso,vr=R._fixture(Path(td))
 cache=R.s1_own(iso,vr)
 def checked():
  with contextlib.redirect_stdout(io.StringIO()): return R.check(**kw,s1_cache=cache)
 assert checked()
 # Negative AR parameter is outside the frozen M domain but has a valid covariance.
 s2=frames['STABILITY.json']['S2'];s2['phi']=-.1
 _,_,X,w=R.RC.matrix(iso);g=R.RC.projection(X,w)
 key=pd.MultiIndex.from_arrays([iso.CR,iso.hemisphere]);codes,unique=pd.factorize(key)
 cr=np.array([c for c,h in unique]);hh=np.array([h for c,h in unique]);lp=np.log(w)
 se=R.RC.se_from_saved(SimpleNamespace(**s2),iso,g,codes,cr-cr.min(),hh,lp-lp.mean())
 s2.update(se=se,lo=s2['beta']-R.RC.Z*se,hi=s2['beta']+R.RC.Z*se)
 save();results['out_of_domain_phi_accepted']=checked()
with tempfile.TemporaryDirectory() as td:
 ds={k:Path(td)/k for k in R.CHAIN}
 stab=Path(td)/'stab';stab.mkdir()
 for p in ds.values():p.mkdir()
 def put(k,n,obj):(ds[k]/n).write_text(json.dumps(obj))
 def rec(k,key,meta):put(k,'RECEIPT.json',dict(passed=1,total=1,partial=False,checks=[dict(ok=True)],**{key:R.h256(meta)}))
 put('cat','META.json',{})
 put('check','META.json',dict(catalogue_meta_sha256=R.h256(ds['cat']/'META.json')))
 put('val','META.json',dict(design_check_meta_sha256='obsolete'))
 put('val','ACCEPTANCE.json',dict(accepted_15deg=False,problems=['incomplete grid']))
 for k,key,m in [('cat_recount','catalogue_meta_sha256','cat'),('check_recount','design_check_meta_sha256','check'),('val_recount','validation_meta_sha256','val')]:rec(k,key,ds[m]/'META.json')
 put('val_read','READ.json',dict(acceptance_sha256=R.h256(ds['val']/'ACCEPTANCE.json'),recount_receipt_sha256=R.h256(ds['val_recount']/'RECEIPT.json')))
 (stab/'META.json').write_text(json.dumps({key:R.h256(ds[k]/n) for key,k,n in [('catalogue_meta_sha256','cat','META.json'),('design_check_meta_sha256','check','META.json'),('validation_meta_sha256','val','META.json'),('reading_sha256','val_read','READ.json')]}))
 with patch.object(R,'committed',return_value=True):
  results['stale_technically_invalid_validation_chain_accepted']=not R.chain_problems(stab,ds)
print(json.dumps(results,indent=2))
sys.exit(1 if any(results.values()) else 0)
