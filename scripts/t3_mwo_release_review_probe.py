"""Release-export review on synthetic rows only; never reads any real sealed value."""
from pathlib import Path
import hashlib,importlib.util,json,sys,tempfile
from unittest.mock import patch
import pandas as pd

root=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('release_review',root/'scripts/t3_mwo_catalogue_release.py')
R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
sealed_fields={'tilt_deg','gamma_deg','leading_sign','hale_expected','lon_pos','lat_pos','lon_neg','lat_neg','sep_deg'}
design,sealed=[],[]
for st in ['isolated','all']:
    d={src:1 for _,src,_ in R.COLUMNS if src not in sealed_fields}
    d.update(record_set=st,noaa='001',day='2000-01-01')
    s={src:1 for src in sealed_fields}
    s.update(record_set=st,noaa='001',day='2000-01-01')
    design.append(d);sealed.append(s)
D,S=pd.DataFrame(design),pd.DataFrame(sealed)
assert all(len(t)==1 for t in R.tables(D,S).values())
bad_day=S.copy();bad_day['day']='1999-01-01'
extra=pd.concat([S,S.iloc[[1]].assign(noaa='999')],ignore_index=True)
results={}
for label,bad in [('wrong_sealed_day_accepted',bad_day),('extra_sealed_group_accepted',extra)]:
    try:R.tables(D,bad)
    except ValueError:results[label]=False
    else:results[label]=True

class WouldReadSeal(Exception):pass
with tempfile.TemporaryDirectory() as td:
    td=Path(td);est=td/'estimate';est.mkdir();rc=td/'estimate_rc';rc.mkdir();cat=td/'cat';cat.mkdir()
    (est/'META.json').write_text(json.dumps(dict(catalogue_meta_sha256='obsolete-catalogue')))
    (cat/'META.json').write_text(json.dumps(dict(catalogue='current')))
    receipt=dict(passed=1,total=1,partial=False,checks=[dict(ok=True)],
                 estimate_meta_sha256=hashlib.sha256((est/'META.json').read_bytes()).hexdigest())
    (rc/'RECEIPT.json').write_text(json.dumps(receipt))
    def read(path,*args,**kwargs):
        if Path(path).name=='DESIGN.csv':return D
        if Path(path).name=='SEALED.csv.gz':raise WouldReadSeal()
        raise AssertionError(str(path))
    with patch.object(R,'EST',est),patch.object(R,'OUT',td/'export'),patch.object(R,'CAT',cat),\
            patch.object(R.release_problem,'__defaults__',(est,rc,None)),\
            patch.object(R,'committed',return_value=True),patch.object(R.pd,'read_csv',side_effect=read):
        try:R.export()
        except WouldReadSeal:results['stale_catalogue_still_reaches_sealed_reader']=True
        except (SystemExit,ValueError,FileNotFoundError):results['stale_catalogue_still_reaches_sealed_reader']=False
        else:raise AssertionError('export unexpectedly completed')
print(json.dumps(results,indent=2))
sys.exit(1 if any(results.values()) else 0)
