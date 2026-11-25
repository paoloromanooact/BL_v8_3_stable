"""Synthetic review probe: no observed maps or scientific real-data runs.
Caching only avoids repeating the same independent reconstruction between comparison mutations.
"""
import contextlib,hashlib,importlib.util,io,json,sys,tempfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=load('runner','scripts/sft_map_bipole_pilot.py'); B=load('recount','scripts/sft_map_bipole_pilot_recount.py')
report={'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['scripts/sft_map_bipole_pilot.py','scripts/sft_map_bipole_pilot_recount.py','python/sharpbl/sft_core.py']},'cases':{}}
# Retain two ordinary synthetic bipoles; reduce comparison times but not solver/grid.
A.TIMES=B.TIMES=(('0',0.),('27d',27*A.C.DAY))
with tempfile.TemporaryDirectory() as td:
 cat,reader=A.synthetic_env(td,n_harp=4);cat=cat[cat.HARPNUM>=3].copy()
 prods,_=A.build(cat,reader,curves=False)
 cache=B.own_all(cat,reader,curves=False);cv=B.own_convergence(cache[2],reader)
 B.own_all=lambda *args,**kwargs:cache
 B.own_convergence=lambda *args,**kwargs:cv
 def trial(name,outputs):
  with contextlib.redirect_stdout(io.StringIO()): got=B.check(write=False,data=(cat,reader),outputs=outputs)
  report['cases'][name]={'accepted':bool(got)};print(name,got,flush=True)
 trial('baseline_synthetic_without_required_daily_curves',prods)
 bad=dict(prods);bad['SAMPLE']=prods['SAMPLE'].drop(columns=['weight','pi','perm_rank'])
 trial('sample_weight_pi_perm_rank_columns_deleted',bad)
 # This is an acceptance-rule probe, with the independently rebuilt failed convergence table
 # injected on both sides. It does not claim a numerical failure of the physical solver.
 bad=dict(prods);cvbad=cv.copy();cvbad['criterion']=0.1;cvbad['passes']=False
 B.own_convergence=lambda *args,**kwargs:cvbad
 bad['CONVERGENCE']=cvbad
 trial('matched_convergence_failure_not_vetoed',bad)
 small=prods['CELLS'].copy();small.loc[small.index[0],'N_cell']+=1e-10
 report['cases']['fractional_count_accepted_by_comparator']={'accepted':B.frames_match(small,prods['CELLS'],['multiplicity','flux_class','lat_band'])[0]}
 # Gate tested against a corrupted in-memory freeze receipt; no disk inputs are altered.
 orig=A.json.loads
 A.json.loads=lambda *args,**kw: dict(orig(*args,**kw),inputs_sha256={})
 report['cases']['empty_freeze_input_manifest']={'gate_problems':A.gate()}
Path('/tmp/bl_sft_evening_review/PROBE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
