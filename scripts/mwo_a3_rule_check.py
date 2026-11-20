"""Reconstruct proposed A3 from saved pixel summaries and UTC metadata only.

No FITS or sealed catalogue is read. Seven UTC calendar dates, not +/-72 hours.
Use --selftest or --check [--out PATH]; PATH is created exclusively.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ratios(frame):
    """Median of all other valid scans on day-3,...,day+3; exclude self by member."""
    if frame.member.duplicated().any():
        raise ValueError('duplicate member')
    x = frame.copy()
    x['utc_day'] = pd.to_datetime(x.obs_time, format='ISO8601').dt.floor('D')
    x = x[np.isfinite(x.median_abs) & x.utc_day.notna()].sort_values(['utc_day', 'member']).reset_index(drop=True)
    t = x.utc_day.to_numpy(dtype='datetime64[D]').astype('int64')
    m = x.median_abs.to_numpy(float)
    refs, counts = [], []
    for i, day in enumerate(t):
        lo, hi = np.searchsorted(t, day-3, 'left'), np.searchsorted(t, day+3, 'right')
        vals = np.concatenate((m[lo:i], m[i+1:hi]))
        counts.append(len(vals))
        refs.append(float(np.median(vals)) if len(vals) else np.nan)
    x['n_reference'] = counts
    x['reference_median'] = refs
    den = np.asarray(refs)
    x['ratio'] = np.divide(m, den, out=np.full(len(x), np.nan), where=np.isfinite(den) & (den > 0))
    return x


def check():
    audit = ROOT/'results/MWO_PIXEL_AUDIT'
    cat = ROOT/'results/T3_MWO_CATALOGUE_R3'
    listed = ROOT/'docs/PROTOCOL_T3_MWO_AMENDMENT_A3_EXCLUDED_FITS.csv'
    am, cm = json.loads((audit/'META.json').read_text()), json.loads((cat/'META.json').read_text())
    assert sha(audit/'PIXELS.csv.gz') == am['products_sha256']['PIXELS.csv.gz']
    for name in ['MAGNETOGRAMS.csv.gz','ATTEMPTS.csv.gz','DESIGN.csv']:
        assert sha(cat/name) == cm['products_sha256'][name]
    p = pd.read_csv(audit/'PIXELS.csv.gz')
    m = pd.read_csv(cat/'MAGNETOGRAMS.csv.gz')
    assert len(p) == am['n'] == 30952 and p.member.is_unique and m.member.is_unique
    a2 = set(pd.read_csv(ROOT/'docs/PROTOCOL_T3_MWO_AMENDMENT_A2_EXCLUDED_FITS.csv').member)
    joined = p.merge(m[['member','obs_time']], on='member', validate='one_to_one')
    assert len(joined) == len(p)
    joined = joined[~joined.member.isin(a2)]
    assert not (np.isfinite(joined.median_abs) & joined.obs_time.isna()).any()
    x = ratios(joined)
    selected = x[x.ratio > 3].sort_values('member')
    saved = pd.read_csv(listed).sort_values('member')
    assert selected.member.tolist() == saved.member.tolist() and len(saved) == 8
    numeric = ['median_abs','n_reference','reference_median','ratio','p99_abs','max_abs','frac_saturated']
    assert np.allclose(selected[numeric].to_numpy(float), saved[numeric].to_numpy(float), rtol=1e-12, atol=1e-12)
    a = pd.read_csv(cat/'ATTEMPTS.csv.gz'); a = a[a.member.notna()]
    a = a.merge(x[['member','n_reference']], on='member', how='left', validate='many_to_one')
    d = pd.read_csv(cat/'DESIGN.csv')
    empty = set(p.loc[p.n_pix.eq(0), 'member'])
    assert not d.member.isin(empty).any()
    valid_ratio = x.ratio[np.isfinite(x.ratio)]
    return dict(rule='m > 3 * median(other finite medians on seven UTC dates day-3 through day+3); A2 excluded',
                audit_n=len(p), a2_n=int(p.member.isin(a2).sum()), zero_central_pixels=int(p.n_pix.eq(0).sum()),
                read_errors=int(p.error.notna().sum()), comparable_n=len(x),
                no_reference=int(x.n_reference.eq(0).sum()), finite_ratios=len(valid_ratio),
                ratio_quantile_999=float(valid_ratio.quantile(.999)),
                ratio_gap_2_5_to_3=int((valid_ratio.gt(2.5)&valid_ratio.le(3)).sum()),
                excluded_members=selected.member.tolist(),
                attempts_with_magnetogram=len(a), attempts_fewer_than_3_refs=int(a.n_reference.lt(3).sum()),
                attempts_without_central_statistic=int(a.n_reference.isna().sum()),
                empty_central_attempt_statuses=a[a.member.isin(empty)].groupby('status').size().to_dict(),
                selected_records_with_empty_central_mask=int(d.member.isin(empty).sum()),
                inputs_sha256={str(q.relative_to(ROOT)):sha(q) for q in [audit/'META.json', audit/'PIXELS.csv.gz', cat/'META.json', listed]})


def selftest():
    # End dates are included even when their clock times are more than 72h away.
    x = pd.DataFrame(dict(member=list('abcde'), obs_time=['2000-01-01 00:01:00','2000-01-04 23:59:00',
          '2000-01-04 10:00:00','2000-01-08 00:00:00','2000-01-04 11:00:00'], median_abs=[1.,3.,1.,1.,np.nan]))
    r = ratios(x).set_index('member')
    assert r.loc['b','n_reference'] == 2 and r.loc['b','ratio'] == 3
    assert not bool(r.loc['b','ratio'] > 3)
    assert r.loc['d','n_reference'] == 0 and np.isnan(r.loc['d','ratio'])
    assert 'e' not in r.index
    zero = x.iloc[:2].copy();zero.loc[zero.index[0],'median_abs'] = 0
    assert np.isnan(ratios(zero).set_index('member').loc['b','ratio'])
    try: ratios(pd.concat([x,x.iloc[:1]]))
    except ValueError: pass
    else: raise AssertionError('duplicate accepted')
    print('PASS: UTC calendar boundaries, self-exclusion, finite inputs, missing/zero reference, strict threshold and duplicate refusal')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--selftest',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.selftest: selftest()
    if a.check:
        result=check();content=json.dumps(result,indent=2)+'\n'
        if a.out:
            with a.out.open('x') as f:f.write(content)
        print(content)
    if not (a.selftest or a.check):p.error('specify --selftest or --check')
