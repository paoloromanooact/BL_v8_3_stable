"""Offline review of phase 5 at bedc06c. Only synthetic FITS and preserved metadata; no network.
Exit 1 means a residual defect has been reproduced. No scientific products or receipts are written.
"""
import contextlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
def load(name, file):
    spec=importlib.util.spec_from_file_location(name, ROOT/'scripts'/file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
M=load('phase5_runner','mdi_pilot_measure_l2.py');R=load('phase5_recount','mdi_pilot_l2_recount.py')
checks=[]
def record(name, cond, **info): checks.append(dict(name=name,ok=bool(cond),**info))
with tempfile.TemporaryDirectory() as td:
    td=Path(td);env=M.synthetic_env(td/'synthetic')
    tab=M.build(**env);kw,conflicts=R.own_keywords(env['answers'])
    rows,badsha=R.expected_rows(env['samp'],env['choices'],kw,env['checkpoint'],env['dest'],env['dpd'])
    record('synthetic baseline reproduced',not R.compare(tab,rows,env['choices']) and not badsha)
    t=tab.copy();t.loc[0,'pair_status']='invented_pair'
    record('pair_status mutation refused',bool(R.compare(t,rows,env['choices'])))
    t=tab.copy();t.loc[0,'main_npos']=float(t.loc[0,'main_npos'])+0.4
    record('fractional pixel count refused',bool(R.compare(t,rows,env['choices'])))
    c={key:value.copy() for key,value in env['choices'].items()}
    k={key:dict(value) for key,value in kw.items()}
    for rule in c:
        c[rule].loc[0,'A_interval']=float('nan');c[rule].loc[0,'B']=None
    k[c['A1'].loc[0,'A']]['INTERVAL']='MISSING'
    try:
        R.expected_rows(env['samp'],c,k,env['checkpoint'],env['dest'],env['dpd'])
        record('unknown INTERVAL handled without crash',True)
    except (ValueError,TypeError) as exc:
        record('unknown INTERVAL handled without crash',False,error=str(exc))
    d=td/'bad_product';d.mkdir();tab.to_csv(d/'L2_RECORDS.csv',index=False)
    (d/'META.json').write_text(json.dumps(dict(products_sha256={'L2_RECORDS.csv':'0'*64})))
    orig=R.expected_rows;called=[]
    def forbidden(*args,**kwargs):
        called.append(True);raise RuntimeError('measurement reached after invalid upstream hash')
    R.expected_rows=forbidden
    try:
        try:
            with contextlib.redirect_stdout(io.StringIO()):R.check(d,write=False,env=env)
        except RuntimeError:pass
    finally:R.expected_rows=orig
    record('invalid product hash stops before FITS reconstruction',not called)
    # Actual runner gate on preserved metadata, with a copied SAMPLE modified under its unchanged META.
    import shutil,types
    sel=td/'selection';shutil.copytree(M.SEL,sel)
    sample=pd.read_csv(sel/'SAMPLE.csv',dtype={'noaa':str},float_precision='round_trip');sample.loc[0,'lat']+=1
    sample.to_csv(sel/'SAMPLE.csv',index=False)
    state=td/'state';state.mkdir();ck=[dict(e,plan_meta_sha256=M.sha(M.PLAN/'META.json')) for e in env['checkpoint']]
    (state/'CHECKPOINT.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in ck))
    saved=(M.SEL,M.STATE,M._load,M.build);reached=[]
    # Isolate the scientific gate from unrelated concurrent tracked changes.
    # build is replaced by a sentinel: this cannot read FITS or write real products.
    git_run=M.subprocess.run
    def clean_status(args,**kwargs):
        if args[:3]==['git','status','--porcelain']:return types.SimpleNamespace(stdout='')
        return git_run(args,**kwargs)
    M.subprocess.run=clean_status
    def fake_load(name,rel):
        if name=='t3_mwo_catalogue':return types.SimpleNamespace(dpd_groups=lambda **kwargs:env['dpd'])
        return saved[2](name,rel)
    def forbidden_build(*args,**kwargs):
        reached.append(True);raise RuntimeError('measurement reached with modified selection')
    M.SEL,M.STATE,M._load,M.build=sel,state,fake_load,forbidden_build
    try:
        try:M.run(td/'not_written')
        except (SystemExit,RuntimeError):pass
    finally:
        M.SEL,M.STATE,M._load,M.build=saved
        M.subprocess.run=git_run
    record('runner refuses modified selection before measurement',not reached)
print(json.dumps(dict(passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks,network_used=False,real_fits_read=False),indent=2))
raise SystemExit(0 if all(c['ok'] for c in checks) else 1)
