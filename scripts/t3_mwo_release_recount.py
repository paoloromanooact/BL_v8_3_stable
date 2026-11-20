"""Independent verification of the MWO catalogue release. No import of the exporter in check().
Real --check requires committed estimate/recount and consistent input hashes before reading SEALED.
--selftest uses temporary synthetic exports only. One process; no simulations or downloads.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'results/T3_MWO_CATALOGUE_R4'; STAB=ROOT/'results/T3_MWO_STABILITY_R4'
EST=ROOT/'results/T3_MWO_ESTIMATE_R4'; REC=ROOT/'results/T3_MWO_ESTIMATE_R4_RECOUNT'
RELEASE=ROOT/'results/MWO_TILT_CATALOGUE_RELEASE'; OUT=ROOT/'results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT'
FIELDS=dict(x.split(':') for x in '''noaa:noaa day_utc:day mwo_time_utc:obs_time mwo_file:member epoch:epoch
resolution_class:res_class carrington_rotation:CR cycle:cycle hemisphere:hemisphere lat_flux_weighted_deg:lat_bar
dpd_lat_deg:dpd_lat dpd_carrington_lon_deg:dpd_lon dpd_lcm_deg:lcm dpd_area_msh:dpd_area flux_window_mx:phi_mwo
tilt_deg:tilt_deg joy_gamma_deg:gamma_deg leading_polarity_sign:leading_sign hale_expected_sign:hale_expected
lon_pos_deg:lon_pos lat_pos_deg:lat_pos lon_neg_deg:lon_neg lat_neg_deg:lat_neg separation_deg:sep_deg
isolated_day:isolated n_neighbours:n_neighbours candidate_rank:rank n_candidate_days:n_cand
n_blank_window:n_blank_win activity_dpd_norm:A_main'''.split())
TEXT={'noaa','day_utc','mwo_time_utc','mwo_file','epoch','resolution_class','hemisphere','isolated_day'}
COMPARISONS=('S1_TABLE.csv','S1_DPD_SOURCES.csv','S2_P1.json','S2_P1_MATCHED.csv','S3_HALE.csv','S4_DWL_ALL.csv','WL_TILTS.csv')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def committed(p):
    p=Path(p)
    if not p.exists():return False
    rel=str(p.relative_to(ROOT))
    tracked=set(subprocess.check_output(['git','ls-files','--',rel],cwd=ROOT,text=True).splitlines())
    return bool(tracked) and not subprocess.check_output(['git','status','--porcelain','--',rel],cwd=ROOT,text=True).strip() and all(str(f.relative_to(ROOT)) in tracked for f in p.rglob('*') if f.is_file())
def products(p):
    m=read(p/'META.json'); declared=m.get('products_sha256',{})
    actual={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and str(f.relative_to(p)) not in {'META.json','RUN.log'}}
    return bool(declared) and set(declared)==actual and all(sha(p/n)==h for n,h in declared.items())
def receipt(p,meta):
    r=read(p);n=r.get('total');k=r.get('passed');c=r.get('checks')
    return type(n) is int and type(k) is int and n>0 and n==k and r.get('partial') is False and isinstance(c,list) and len(c)==n and all(isinstance(x,dict) and x.get('ok') is True for x in c) and r.get('estimate_meta_sha256')==sha(meta)
def check(cat=CAT,stab=STAB,est=EST,rec=REC,release=RELEASE,out=OUT,require_git=True,write=True):
    cat,stab,est,rec,release=map(Path,(cat,stab,est,rec,release));checks=[];completed=False
    def ok(name,value):checks.append(dict(name=name,ok=bool(value)))
    try:
        ok('prerequisites preserved',not require_git or all(committed(p) for p in [cat,stab,est,rec,release]))
        ok('input and release product hashes',all(products(p) for p in [cat,stab,est,release]))
        ok('estimate recount complete and bound',receipt(rec/'RECEIPT.json',est/'META.json'))
        em,rm=read(est/'META.json'),read(release/'META.json')
        ok('current catalogue and stability links',em.get('catalogue_meta_sha256')==sha(cat/'META.json') and em.get('stability_meta_sha256')==sha(stab/'META.json') and all(rm.get(k)==sha(p) for k,p in [('catalogue_meta_sha256',cat/'META.json'),('stability_meta_sha256',stab/'META.json'),('estimate_meta_sha256',est/'META.json'),('estimate_recount_receipt_sha256',rec/'RECEIPT.json')]))
        if not all(c['ok'] for c in checks):raise ValueError('prerequisite refused before SEALED')
        d=pd.read_csv(cat/'DESIGN.csv',dtype={'noaa':str});s=pd.read_csv(cat/'SEALED.csv.gz',dtype={'noaa':str})
        for label in ['isolated','all']:
            left=d[d.record_set==label];right=s[s.record_set==label]
            a=pd.read_csv(release/f'MWO_TILT_CATALOGUE_{label.upper()}_1974_2012.csv',dtype={'noaa':str})
            keys=lambda f:set(zip(f.noaa,f['day'] if 'day' in f else f.day_utc))
            ok(label+' keys and multiplicity',len(keys(left))==len(left)==len(right)==len(a)==len(keys(right))==len(keys(a)) and keys(left)==keys(right)==keys(a))
            ok(label+' exact schema',list(a.columns)==list(FIELDS))
            left=left.set_index(['noaa','day']);right=right.set_index(['noaa','day']);a=a.set_index(['noaa','day_utc'])
            for name,src in FIELDS.items():
                if name in ['noaa','day_utc']:continue
                original=left[src] if src in left else right[src]
                original=original.reindex(a.index)
                same=(original.astype(str).to_numpy()==a[name].astype(str).to_numpy()).all() if name in TEXT else np.allclose(original.to_numpy(float),a[name].to_numpy(float),rtol=1e-12,atol=1e-12,equal_nan=True)
                ok(label+' '+name,same)
        cols=pd.read_csv(release/'COLUMNS.csv')
        ok('column dictionary names and sources',cols.column.tolist()==list(FIELDS) and cols.source.tolist()==list(FIELDS.values()))
        for n in COMPARISONS:ok('comparison '+n,(release/'COMPARISONS'/n).exists() and sha(release/'COMPARISONS'/n)==sha(stab/n))
        ok('README present',bool((release/'README.md').read_text().strip()))
        ex=pd.read_csv(release/'EXCLUDED_MAGNETOGRAMS.csv');expected=[]
        for tag in ['A2','A3']:
            source=pd.read_csv(ROOT/f'docs/PROTOCOL_T3_MWO_AMENDMENT_{tag}_EXCLUDED_FITS.csv')
            expected.extend((tag,r.member,r.sha256) for r in source.itertuples())
        ok('26 excluded FITS identities and amendments',sorted(zip(ex.amendment,ex.member,ex.sha256))==sorted(expected))
        # Independent point estimates and sample sizes; bootstrap RNG remains the exporter's implementation.
        a=pd.read_csv(release/'MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv');j=pd.read_csv(release/'JOY_BY_CYCLE.csv')
        seen=set()
        for (cycle,hem),g in a.groupby(['cycle','hemisphere']):
            for weighted in [True,False]:
                z=j[(j.cycle==cycle)&(j.hemisphere==hem)&(j.weighted==weighted)]
                assert len(z)==1
                row=z.iloc[0];x=np.sin(np.deg2rad(abs(g.lat_flux_weighted_deg.to_numpy())))
                w=g.flux_window_mx.to_numpy() if weighted else np.ones(len(g))
                k=float(np.dot(w*x,g.joy_gamma_deg)/np.dot(w*x,x))
                ok(f'Joy {cycle}{hem} {weighted}',np.isclose(row.k_deg,k,rtol=1e-12,atol=1e-12) and row.n_regions==len(g) and row.n_cr==g.carrington_rotation.nunique() and row.n_blocks==((g.carrington_rotation-g.carrington_rotation.min())//6).nunique() and bool(row.partial_cycle)==(cycle in [20,24]) and 0<=row.invalid_replicates<=2000 and np.isfinite([row.lo,row.hi]).all() and row.lo<=row.hi)
                seen.add((cycle,hem,weighted))
        ok('Joy keys complete',len(j)==len(seen) and set(zip(j.cycle,j.hemisphere,j.weighted))==seen)
        for weighted in [True,False]:
            rng=np.random.default_rng(69_500_001)
            for (cycle,hem),g in a.groupby(['cycle','hemisphere']):
                x=np.sin(np.deg2rad(abs(g.lat_flux_weighted_deg.to_numpy())));y=g.joy_gamma_deg.to_numpy()
                w=g.flux_window_mx.to_numpy() if weighted else np.ones(len(g))
                blocks=((g.carrington_rotation-g.carrington_rotation.min())//6).to_numpy();ids=np.unique(blocks)
                values=[];invalid=0
                for _ in range(2000):
                    draw=rng.choice(ids,len(ids));indices=np.concatenate([np.flatnonzero(blocks==k) for k in draw])
                    den=np.dot(w[indices]*x[indices],x[indices])
                    if not den>0:invalid+=1;continue
                    values.append(np.dot(w[indices]*x[indices],y[indices])/den)
                lo,hi=np.quantile(values,[.025,.975]) if values else (np.nan,np.nan)
                row=j[(j.cycle==cycle)&(j.hemisphere==hem)&(j.weighted==weighted)].iloc[0]
                ok(f'Joy bootstrap {cycle}{hem} {weighted}',np.allclose([lo,hi],[row.lo,row.hi],rtol=1e-10,atol=1e-10,equal_nan=True) and invalid==row.invalid_replicates)

        completed=True
    except (OSError,ValueError,KeyError,AssertionError,TypeError) as e:ok('verification completed: '+str(e),False)
    good=bool(checks) and all(c['ok'] for c in checks)
    if write:
        Path(out).mkdir(parents=True,exist_ok=False)
        (Path(out)/'RECEIPT.json').write_text(json.dumps(dict(passed=sum(c['ok'] for c in checks),total=len(checks),checks=checks,partial=(not require_git or not completed),release_meta_sha256=sha(release/'META.json') if (release/'META.json').exists() else None,scope='table values, provenance, copied comparisons, Joy estimates/counts and deterministic percentile replay; no statistical calibration claim'),indent=2)+'\n')
    return good

def selftest():
    # Approved producer fixture creates a temporary package; checker does not import producer code.
    probe=ROOT/'scripts/t3_mwo_release_review_probe.py';code=probe.read_text()
    marker="    print('PASS: valid synthetic release exported atomically with both tables, all comparisons and matching hashes')"
    extra="""
    assert independent_check(cat,stab,est,rc,out,require_git=False,write=False)
    path=out/'MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv'
    original_meta=(out/'META.json').read_bytes()
    clean=path.read_bytes();table=pd.read_csv(path,dtype={'noaa':str});table.loc[0,'tilt_deg']+=1;table.to_csv(path,index=False)
    changed=json.loads((out/'META.json').read_text());changed['products_sha256'][path.name]=R.h256(path);(out/'META.json').write_text(json.dumps(changed))
    assert not independent_check(cat,stab,est,rc,out,require_git=False,write=False)
    path.write_bytes(clean);(out/'META.json').write_bytes(original_meta)
    old_receipt=(rc/'RECEIPT.json').read_bytes();bad_receipt=json.loads(old_receipt);bad_receipt['partial']=True
    (rc/'RECEIPT.json').write_text(json.dumps(bad_receipt))
    from unittest.mock import patch
    with patch('pandas.read_csv',side_effect=AssertionError('must not read data')) as spy:
        assert not independent_check(cat,stab,est,rc,out,require_git=False,write=False)
        assert spy.call_count==0
    (rc/'RECEIPT.json').write_bytes(old_receipt)
    print('PASS independent guard: partial estimate receipt refuses before any table read')
    print('PASS independent release checker: baseline passes, altered value refused even with updated hash')
"""
    assert marker in code
    ns={'__file__':str(probe),'__name__':'release_checker_fixture','independent_check':check}
    try:exec(compile(code.replace(marker,marker+'\n'+extra),str(probe),'exec'),ns)
    except SystemExit as e:assert e.code==0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--selftest',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.selftest:selftest()
    elif a.check:sys.exit(0 if check() else 1)
    else:p.error('specify --selftest or --check')
