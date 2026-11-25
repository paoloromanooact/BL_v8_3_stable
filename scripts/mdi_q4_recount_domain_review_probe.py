from pathlib import Path
import types,sys,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
R=types.ModuleType('q4_working_domain_review');R.__file__=str(ROOT/'scripts/mdi_q4_recount.py');sys.modules[R.__name__]=R
exec(compile(Path(R.__file__).read_bytes(),R.__file__,'exec'),R.__dict__)
cases=[]
a=pd.DataFrame({'model':['bA'],'status':['ok'],'B1_A':[0.0],'target_null_020':[True],'tol_units_A_020':[1e30]})
_,got=R.protected_tolerances(a);cases.append({'case':'null target with B1 exactly zero and finite tolerance 1e30','accepted':bool(got),'expected_accepted':False})
for col,original,mutant in [('n_ok',2,2.000000001),('n_records_min',5223,5223.000000001),('n_mdi',0,False)]:
 if col=='n_ok':got=R.json_close({'x':{'n_ok':original}},{'x':{'n_ok':mutant}})
 else:got=R.close_cols(pd.DataFrame({col:[mutant]}),pd.DataFrame({col:[original]}))[0]
 cases.append({'case':col,'expected_value':original,'altered_value':mutant,'accepted':bool(got),'expected_accepted':False})
res={'a2':1.,'a2_mdi':1.,'bKb':{(1,False):0.},'B1':{'A':0.},**{f'target_{tag}':0. for tag in R.TAGS}}
f=pd.DataFrame(R.nrows(res,[0],[(15.,2.)],False,{'d3':1.,'sbar':1.})).assign(model='bA',status='ok')
m=f.copy();m.loc[0,'tol_units_A_020']=1e30
fn,fg=R.protected_tolerances(f);mn,mg=R.protected_tolerances(m)
match,_=R.frames_match(mn,fn,['model','status'])
cases.append({'case':'null-target RAW row from nrows: corrupted finite tolerance passes both domain and normalised comparison','accepted':bool(fg and mg and match),'expected_accepted':False})
nf=json.loads(R.NOTE_FREEZE.read_text());af=json.loads((R.ROOT/R.A2_FREEZE_REL).read_text())
problems=R.provenance(nf,af,R.sha(R.NOTE_FREEZE),R.sha(R.ROOT/R.A2_FREEZE_REL),root=R.ROOT)
assert problems==[],problems
print(json.dumps(cases,indent=2))
sys.exit(1 if any(c['accepted'] != c['expected_accepted'] for c in cases) else 0)
