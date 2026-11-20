"""Release review with a valid synthetic export first, then bad joins and stale input.
No real sealed catalogue or response is read.
"""
from pathlib import Path
from unittest.mock import patch
import hashlib,importlib.util,json,sys,tempfile
import pandas as pd

root=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('release_review',root/'scripts/t3_mwo_catalogue_release.py')
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
sealed_fields={'tilt_deg','gamma_deg','leading_sign','hale_expected','lon_pos','lat_pos','lon_neg','lat_neg','sep_deg'}
design,sealed=[],[]
for st,day in [('isolated','2000-01-01'),('all','2000-01-02')]:
    d={src:1 for _,src,_ in R.COLUMNS if src not in sealed_fields}
    d.update(record_set=st,noaa='001',day=day,obs_time=day+'T18:00:00',member='synthetic.fits',epoch='E8',
             res_class='R1',CR=1950,cycle=23,hemisphere='N',lat_bar=15.,phi_mwo=1e21,isolated=True)
    s={src:1 for src in sealed_fields};s.update(record_set=st,noaa='001',day=day)
    design.append(d);sealed.append(s)
D,S=pd.DataFrame(design),pd.DataFrame(sealed)
assert all(len(t)==1 for t in R.tables(D,S).values())
results={}
for label,bad in [('wrong_sealed_day_accepted',S.assign(day='1999-01-01')),
                  ('extra_sealed_group_accepted',pd.concat([S,S.iloc[[1]].assign(noaa='999')],ignore_index=True))]:
    try:R.tables(D,bad)
    except ValueError:results[label]=False
    else:results[label]=True

with tempfile.TemporaryDirectory() as td:
    td=Path(td);cat,stab,est,rc=[td/k for k in ['cat','stab','est','rc']]
    for d in [cat,stab,est,rc]:d.mkdir()
    def put(path,obj):path.write_text(json.dumps(obj))
    def meta(folder,**links):
        put(folder/'META.json',dict(products_sha256={p.name:R.h256(p) for p in folder.iterdir() if p.is_file() and p.name!='META.json'},**links))
    D.to_csv(cat/'DESIGN.csv',index=False);S.to_csv(cat/'SEALED.csv.gz',index=False);meta(cat)
    # Copy-only comparison placeholders: the independent stability statistics are not run here.
    for n in R.COMPARISON_FILES:
        (stab/n).write_text('{}' if n.endswith('.json') else 'synthetic\n1\n')
    meta(stab)
    put(est/'FINAL.json',dict(outcome='descrittivo'))
    meta(est,catalogue_meta_sha256=R.h256(cat/'META.json'),stability_meta_sha256=R.h256(stab/'META.json'))
    receipt=dict(passed=1,total=1,partial=False,checks=[dict(ok=True)],estimate_meta_sha256=R.h256(est/'META.json'))
    put(rc/'RECEIPT.json',receipt)
    yes=lambda _:True
    assert R.release_problem(est,rc,cat,stab,yes) is None,'valid synthetic guard must pass'
    out=td/'release';assert R.export(cat,stab,est,rc,out,yes)==0
    m=json.loads((out/'META.json').read_text())
    assert all(R.h256(out/n)==h for n,h in m['products_sha256'].items())
    assert all((out/'COMPARISONS'/n).exists() for n in R.COMPARISON_FILES)
    assert (out/'README.md').exists() and not list(td.glob('release.partial*'))
    print('PASS: valid synthetic release exported atomically with both tables, all comparisons and matching hashes')
    em=json.loads((est/'META.json').read_text());em['catalogue_meta_sha256']='obsolete-catalogue'
    put(est/'META.json',em);receipt['estimate_meta_sha256']=R.h256(est/'META.json');put(rc/'RECEIPT.json',receipt)
    reason=R.release_problem(est,rc,cat,stab,yes)
    assert reason and 'another catalogue' in reason,reason
    reads=[]
    def read(*args,**kwargs):reads.append(str(args[0]));raise AssertionError('guard must stop before catalogue reads')
    with patch.object(R.pd,'read_csv',side_effect=read):
        try:R.export(cat,stab,est,rc,td/'bad_export',yes)
        except SystemExit:results['stale_catalogue_still_reaches_sealed_reader']=False
        else:results['stale_catalogue_still_reaches_sealed_reader']=True
    assert not reads,'stale inputs reached a catalogue reader'
print(json.dumps(results,indent=2))
sys.exit(1 if any(results.values()) else 0)
