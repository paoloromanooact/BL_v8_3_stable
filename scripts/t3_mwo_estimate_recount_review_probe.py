"""Residual estimate-recount cases on synthetic data; never opens real tilt data."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import contextlib,hashlib,importlib.util,io,json,math,sys,tempfile
import numpy as np,pandas as pd

root=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('estimate_review',root/'scripts/t3_mwo_estimate_recount.py')
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
def put(p,obj):p.write_text(json.dumps(obj))
results={}
with tempfile.TemporaryDirectory() as td:
    td=Path(td);dirs={k:td/k for k in ['cat','cat_rc','check_dir','check_rc','val','val_rc','val_read','stab','stab_rc','est']}
    for d in dirs.values():d.mkdir()
    rows=[];rng=np.random.default_rng(8)
    for j,(epoch,cycle,year) in enumerate([('E2',21,1978),('E5',22,1990),('E8',24,2011)]):
        for i in range(60):
            rows.append(dict(record_set='isolated',noaa=f'{j}{i:03}',day=f'{year}-06-15',epoch=epoch,cycle=cycle,
                    hemisphere='N' if i%2 else 'S',sinlat=.15+.3*rng.random(),CR=1650+j*140+i//4,
                    A_main=.4+1.2*rng.random(),phi_mwo=1e21*(1+rng.random()),dpd_area=50+150*rng.random(),
                    rank=1 if i%3 else 2,res_class='R1' if i%4 else 'R2'))
    d=pd.DataFrame(rows);d['A_own']=d.A_main*1.1;d['A_silso_split']=d.A_main*.9;d['A_silso_hem']=d.A_main
    gamma=24*d.sinlat-2*(d.A_main-1)*d.sinlat+rng.normal(0,2,len(d))
    design=pd.concat([d,d.assign(record_set='all')],ignore_index=True)
    sealed=pd.DataFrame(dict(record_set=design.record_set,noaa=design.noaa,day=design.day,gamma_deg=np.r_[gamma,gamma]))
    design.to_csv(dirs['cat']/'DESIGN.csv',index=False);sealed.to_csv(dirs['cat']/'SEALED.csv.gz',index=False)
    put(dirs['cat']/'META.json',dict(products_sha256={n:R.h256(dirs['cat']/n) for n in ['DESIGN.csv','SEALED.csv.gz']}))
    def receipt(folder,key,meta):
        put(dirs[folder]/'RECEIPT.json',dict(passed=1,total=1,partial=False,checks=[dict(ok=True)],**{key:R.h256(meta)}))
    receipt('cat_rc','catalogue_meta_sha256',dirs['cat']/'META.json')
    put(dirs['check_dir']/'TARGETS.json',dict(delta_beta_20=-1.))
    put(dirs['check_dir']/'IDENTIFIABILITY.json',dict(joy=dict(identifiable=True)))
    put(dirs['check_dir']/'META.json',dict(catalogue_meta_sha256=R.h256(dirs['cat']/'META.json'),
        products_sha256={n:R.h256(dirs['check_dir']/n) for n in ['TARGETS.json','IDENTIFIABILITY.json']}))
    receipt('check_rc','design_check_meta_sha256',dirs['check_dir']/'META.json')
    put(dirs['val']/'ACCEPTANCE.json',dict(accepted_15deg=False,problems=[]))
    put(dirs['val']/'META.json',dict(design_check_meta_sha256=R.h256(dirs['check_dir']/'META.json'),
        products_sha256={'ACCEPTANCE.json':R.h256(dirs['val']/'ACCEPTANCE.json')}))
    receipt('val_rc','validation_meta_sha256',dirs['val']/'META.json')
    put(dirs['val_read']/'READ.json',dict(acceptance_sha256=R.h256(dirs['val']/'ACCEPTANCE.json'),
        recount_receipt_sha256=R.h256(dirs['val_rc']/'RECEIPT.json')))
    put(dirs['stab']/'STABILITY.json',dict(rule=dict(outcome='descrittivo',reasons='S2 non determinato')))
    put(dirs['stab']/'META.json',dict(products_sha256={'STABILITY.json':R.h256(dirs['stab']/'STABILITY.json')},
        catalogue_meta_sha256=R.h256(dirs['cat']/'META.json'),design_check_meta_sha256=R.h256(dirs['check_dir']/'META.json'),
        validation_meta_sha256=R.h256(dirs['val']/'META.json'),reading_sha256=R.h256(dirs['val_read']/'READ.json')))
    rec=dict(passed=1,total=1,partial=False,checks=[dict(ok=True)],stability_meta_sha256=R.h256(dirs['stab']/'META.json'))
    put(dirs['stab_rc']/'RECEIPT.json',rec)
    pars=dict(var_a=math.log(25),var_b=.1,phi=.5,kappa=.1,sigma_x2=3.)
    estimates=[]
    for label,opt in R.ANALYSES.items():
        x=d.assign(gamma_mwo=gamma).copy()
        x=R.subset(x,opt.get('filt')).reset_index(drop=True)
        act=opt.get('act','A_main');x=x[np.isfinite(x[act])].reset_index(drop=True)
        ident,X,w=R.design_matrix(x,act,opt.get('form','joy'),opt.get('weights','phi_mwo'));assert ident
        g=R.RC.projection(X,w);beta=float(g@x.gamma_mwo)
        codes,uq=pd.factorize(pd.MultiIndex.from_arrays([x.CR,x.hemisphere]));cr=np.array([c for c,h in uq]);lp=np.log(w)
        se=R.RC.se_from_saved(SimpleNamespace(**pars),x,g,codes,cr-cr.min(),np.array([h for c,h in uq]),lp-lp.mean())
        lo,hi=beta-R.RC.Z*se,beta+R.RC.Z*se
        estimates.append(dict(analysis=label,state='stimato',identifiable=True,n=len(x),beta=beta,se=se,lo=lo,hi=hi,
                       verdict='supportato' if hi<0 else 'opposto' if lo>0 else 'non deciso',**pars))
    tab=pd.DataFrame(estimates);tab.to_csv(dirs['est']/'ESTIMATE.csv',index=False)
    main=tab.iloc[0]
    final=dict(outcome='descrittivo',reasons='S2 non determinato',verdict=None,main_state='stimato',beta3=main.beta,
              se=main.se,lo=main.lo,hi=main.hi,targets=dict(delta_beta_20=-1.))
    put(dirs['est']/'FINAL.json',final)
    def save_meta():
        put(dirs['est']/'META.json',dict(products_sha256={n:R.h256(dirs['est']/n) for n in ['ESTIMATE.csv','FINAL.json']},
              stability_meta_sha256=R.h256(dirs['stab']/'META.json'),catalogue_meta_sha256=R.h256(dirs['cat']/'META.json')))
    save_meta()
    kw={k:dirs[k] for k in ['cat','stab','stab_rc','est','check_dir','val','val_read']};kw.update(write=False)
    def checked(real=False):
        with contextlib.redirect_stdout(io.StringIO()),patch.object(R,'committed',return_value=True):
            return R.check(**kw,require_git=real)
    assert checked() and checked(real=True),'synthetic baseline must pass first'
    print('PASS: synthetic estimate baseline with full upstream metadata and negative but technically valid validation')
    bad=dict(final,se=999.,lo=-1000.,hi=1000.,main_state='invented',targets={'delta_beta_20':999.})
    put(dirs['est']/'FINAL.json',bad);save_meta()
    results['false_FINAL_interval_state_targets_accepted']=checked()
    put(dirs['est']/'FINAL.json',final);save_meta()
    put(dirs['stab_rc']/'RECEIPT.json',dict(rec,checks=[dict(ok=False)]))
    results['failed_stability_receipt_accepted']=checked(real=True)
    put(dirs['stab_rc']/'RECEIPT.json',rec)
    # A changed STABILITY product with an unchanged META makes its old receipt stale.
    put(dirs['stab']/'STABILITY.json',dict(rule=dict(outcome='verdetto',reasons='changed')))
    put(dirs['est']/'FINAL.json',dict(final,outcome='verdetto',verdict=main.verdict));save_meta()
    results['changed_stability_product_turns_result_into_verdict']=checked(real=True)
print(json.dumps(results,indent=2))
sys.exit(1 if any(results.values()) else 0)
