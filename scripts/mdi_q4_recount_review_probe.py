from pathlib import Path
import importlib.util, sys, contextlib, io, copy, json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('q4rec_review',ROOT/'scripts/mdi_q4_recount.py')
R=importlib.util.module_from_spec(spec);sys.modules[spec.name]=R;spec.loader.exec_module(R)
original_check=R.check
fixture={}
class Captured(Exception): pass
def capture(*a,**kw):
 fixture.update(kw);raise Captured
R.check=capture
with contextlib.redirect_stdout(io.StringIO()):
 try: R.selftest()
 except Captured: pass
R.check=original_check
assert fixture['n_real']==2
# Compute expected results once independently; subsequent tests vary only the checked products.
original_compute=R.compute
cache={}
def compute(*a,**kw):
 if 'v' not in cache: cache['v']=original_compute(*a,**kw)
 return copy.deepcopy(cache['v'])
R.compute=compute
results=[]
def run(name,change=None):
 kw=copy.deepcopy(fixture)
 if change: change(kw['outputs'])
 with contextlib.redirect_stdout(io.StringIO()) as log: accepted=R.check(**kw)
 results.append({'case':name,'accepted':bool(accepted)})
 print(name,accepted,flush=True)
 return accepted
assert run('valid synthetic base')
def summary_tol(o):
 t=o['SUMMARY'];i=t.index[t.model.eq('bA')][0];c=next(c for c in t if c.startswith('tol_units_A_'));t.loc[i,c]=0.0
run('protected SUMMARY tolerance set to zero',summary_tol)
def raw_negative(o):
 t=o['RAW'];i=t.index[t.model.eq('bA') & t.status.eq('ok')][0];c=next(c for c in t if c.startswith('tol_units_A_'));t.loc[i,c]=-1e30
run('protected RAW negative tolerance',raw_negative)
def duplicate_yield(o):
 t=o['YIELD_EFFECTS']; t.iloc[1]=t.iloc[0]
run('YIELD_EFFECTS duplicated key and missing step',duplicate_yield)
def yield_label(o):
 t=o['YIELD_EFFECTS']; extra=[c for c in t if c not in ['threshold','design','step_order','value']]
 if not extra: t['invented_column']='wrong'
 else: t.loc[t.index[0],extra[0]]='wrong label'
run('YIELD_EFFECTS altered label or extra column',yield_label)
def meta_choices(o):
 o['META']['implementation_choices']=['wrong']*9
run('META implementation choices replaced',meta_choices)
def extra_meta(o):o['META']['unverified_extra']='invented'
run('META extra unverified field',extra_meta)
def fraction_count(o):
 t=o['CELL_COUNTS']; cols=[c for c in t if c not in R.CELL_KEYS and pd.api.types.is_numeric_dtype(t[c])];c=cols[0]; t[c]=t[c].astype(float);i=t.index[t[c].gt(0)][0];t.loc[i,c]+=1e-9
run('CELL_COUNTS noninteger count',fraction_count)
print(json.dumps(results, indent=2))
# A review probe deliberately exits nonzero while any substantive mutation passes.
substantive=[r for r in results[1:] if r['case'] != 'META extra unverified field']
sys.exit(1 if any(r['accepted'] for r in substantive) else 0)
