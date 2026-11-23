"""Synthetic probes only; no real MDI measurements or MWO comparison read."""
import contextlib, copy, hashlib, importlib.util, io, json, tempfile
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load(name, file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('ana_probe','mdi_pilot_analysis_l1.py')
R=load('rec_probe','mdi_pilot_analysis_l1_recount.py')
A=load('m_procedure_probe','t3_mwo_analysis.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Memoize identical synthetic M calls; fit remains the actual common procedure.
real_unit=A.m_unit
cache={}
def cached(*args):
    key=tuple(np.asarray(a).tobytes() if isinstance(a,np.ndarray) else str(a) for a in args)
    if key not in cache: cache[key]=real_unit(*args)
    return copy.deepcopy(cache[key])
A.m_unit=cached
rec,samp,cells,mwo=M.synthetic()
prods=M.build(rec,samp,cells,mwo,reps=2,A=A)
out={}
out['main_sep_edges']=prods['CLASS_EDGES']['main']['sep_edges']
out['sens100_sep_edges']=prods['CLASS_EDGES']['sens100']['sep_edges']
with tempfile.TemporaryDirectory() as td:
    d=Path(td)
    def check(p):
        M.write(p,d)
        (d/'META.json').write_text(json.dumps({'products_sha256':{f.name:sha(f) for f in d.iterdir() if f.name!='META.json'}}))
        with contextlib.redirect_stdout(io.StringIO()):
            return R.check(d,write=False,data=(rec,samp,mwo),reps=2,A=A)
    out['base_accepted']=check(prods)
    mutations={
        'cell_causes': lambda p: p['Q1_YIELD_CELLS'].__setitem__('cause_map_missing',999),
        'cell_ok100': lambda p: p['Q1_YIELD_CELLS'].__setitem__('ok100',999),
        'cell_population': lambda p: p['Q1_YIELD_CELLS'].__setitem__('N',999),
        'quiet_percentile': lambda p: p['Q1_QUIET_SUMMARY'].__setitem__('p10_g',999),
        'raw_differences': lambda p: p['Q3_PAIRS_main'].__setitem__('d_raw',999),
        'flux_summary': lambda p: p['Q3_SUMMARY_main'].__setitem__('median_flux_ratio',999),
        'bootstrap_valid_count': lambda p: p['Q3_SUMMARY_main'].__setitem__('valid_reps',0),
        'm_boundary_flag': lambda p: p['Q1_M_EXPLORATORY'].__setitem__('phi_at_bound',not p['Q1_M_EXPLORATORY']['phi_at_bound']),
    }
    def subgroup(p):
        t=p['Q1_YIELD_PROJECTED'];t.loc[t.group!='all','projected_yield_100']=999
    mutations['projected100_subgroups']=subgroup
    for name,mut in mutations.items():
        p=copy.deepcopy(prods);mut(p);out[name+'_mutation_accepted']=check(p)
print(json.dumps(out,indent=2))
