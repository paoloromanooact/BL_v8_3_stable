"""Audit the preserved HMI synthetic validation only; never estimate real responses.

Independent of hmi_followups.py and hmi_followups_recount.py. Reuses the frozen
upstream sample/activity definitions. Contrasts use QR; temporal quadratic forms
are evaluated as polynomials in AR(1) lag, on every successful synthetic row.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from sharpbl import run_p2  # noqa: E402

PROTOCOL_SHA = '316fa968e610559362174513b411395912d87a34585f9022d910f5385b7951c8'
Z = norm.ppf(0.9875)
MAIN = ('q1', 'q2_hem')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid():
    out = []
    for test, effects, sd in (('q1', (-2.4, -4.8), 15.), ('q2_hem', (1., 2.), 6.)):
        out += [(test, 'main', sc, sd, 0., 10000) for sc in (0, 1, 2, 7, 9)]
        out += [(test, 'main', sc, sd, eff, 2000) for sc in (1, 2, 7, 9) for eff in effects]
    out += [('q2_hem', 'sensitivity', sc, sd, 0., 2000) for sd in (4., 9.) for sc in (1, 7)]
    out += [('q2', 'sensitivity', sc, 6., 0., 2000) for sc in (0, 1, 2, 7, 9)]
    return out


def sample():
    cat = pd.read_csv(ROOT / 'results/P1/P1_SBL_CATALOG_BY_HARP.csv', low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)['S'], run_p2.load_silso())
    return d[np.isfinite(d.A_monthly)].reset_index(drop=True)


def contrast(d, test):
    cyc, hem = d.cyc.to_numpy(), d.hemisphere.to_numpy()
    if test == 'q1':
        mask = (cyc == 25) | ((cyc == 24) & (d.phase <= d.loc[d.cyc == 25, 'phase'].max()))
        s = d.sinlat.to_numpy()[mask]
        X = np.column_stack([s * (cyc[mask] == c) for c in (24, 25)])
        c = np.array([-1., 1.])
    else:
        mask = np.ones(len(d), dtype=bool)
        if test == 'q2_hem':
            minima = {(24, 'N'): '2007-12-01', (24, 'S'): '2009-02-01',
                      (25, 'N'): '2019-12-01', (25, 'S'): '2019-05-01'}
            ph = np.array([(pd.Timestamp(t) - pd.Timestamp(minima[(int(y), h)])).days / (365.25 * 11)
                           for t, y, h in zip(d.t, cyc, hem)])
        elif test == 'q2':
            ph = d.phase.to_numpy()
        else:
            raise ValueError(f'Unknown contrast {test}')
        X = np.column_stack([((cyc == y) & (hem == h)).astype(float) for y in (24, 25) for h in ('N', 'S')]
                            + [ph, ph ** 2, ph ** 3, d.A_monthly.to_numpy() - 1])
        c = np.eye(X.shape[1])[-1]
    sub = d.loc[mask].reset_index(drop=True)
    w = sub.phi.to_numpy(float)
    Q, R = np.linalg.qr(X * np.sqrt(w)[:, None])
    a = c @ np.linalg.solve(R, Q.T) * np.sqrt(w)
    return sub, a


def variance_cache(sub, a):
    key = pd.MultiIndex.from_arrays([sub.CR.to_numpy().astype(int), sub.hemisphere])
    codes, cells = pd.factorize(key)
    b = np.bincount(codes, weights=a)
    cr = np.array([k[0] for k in cells])
    hem = np.array([k[1] for k in cells])
    lag = np.abs(cr[:, None] - cr[None, :])
    cross = hem[:, None] != hem[None, :]
    bb = np.outer(b, b)
    same = np.bincount(lag.ravel(), weights=np.where(cross, 0., bb).ravel())
    other = np.bincount(lag.ravel(), weights=np.where(cross, bb, 0.).ravel(), minlength=len(same))
    lp = np.log(sub.phi.to_numpy(float))
    return a ** 2, lp - lp.mean(), same, other


def se_batch(params, cache):
    a2, lp, same, cross = cache
    va, vb, phi, kap, sx = params.T
    individual = np.exp(va) * (np.exp(vb[:, None] * lp) @ a2)
    powers = phi[:, None] ** np.arange(len(same))[None, :]
    temporal = (powers @ same + kap * (powers @ cross)) * sx
    return np.sqrt(individual + temporal)


def audit(val):
    val = Path(val)
    meta = json.loads((val / 'META.json').read_text())
    issues = []
    def require(cond, msg):
        if not bool(cond):
            issues.append(msg)
    require(meta['protocol_sha256'] == PROTOCOL_SHA, 'protocol SHA in META')
    require(sha(ROOT / 'docs/PROTOCOL_HMI_FOLLOWUPS.md') == PROTOCOL_SHA, 'frozen protocol changed')
    for name in ('RAW.csv.gz', 'SUMMARY.csv', 'ACCEPTANCE.csv'):
        require(sha(val / name) == meta['products_sha256'].get(name), f'hash mismatch {name}')
    start_commit = meta['git_commit']
    for name in ('scripts/hmi_followups.py', 'python/sharpbl/run_p2.py',
                 'results/P1/P1_SBL_CATALOG_BY_HARP.csv', 'ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv'):
        previous = subprocess.check_output(['git', 'show', f'{start_commit}:{name}'], cwd=ROOT)
        previous_sha = hashlib.sha256(previous).hexdigest()
        require(sha(ROOT / name) == previous_sha, f'input/source changed since start: {name}')
        if name == 'scripts/hmi_followups.py':
            require(previous_sha == meta['script_sha256'], 'runner SHA differs from recorded start revision')
    raw, summ = pd.read_csv(val / 'RAW.csv.gz'), pd.read_csv(val / 'SUMMARY.csv')
    expected = grid()
    require(len(raw) == 150000 and len(summ) == 35, 'total row/config counts')
    require(set(raw.cfg) == set(range(35)) and set(summ.cfg) == set(range(35)), 'configuration identities')
    require(not raw.duplicated(['cfg', 'k']).any() and not raw.seed.duplicated().any(), 'duplicates')
    allowed = {'errore', 'non deciso', 'supportato', 'opposto'}
    require(set(raw.verdict) <= allowed, 'unknown verdict')
    good = raw[raw.verdict != 'errore'].copy()
    cols = ['beta', 'se', 'lo', 'hi', 'var_a', 'var_b', 'phi', 'kappa', 'sigma_x2']
    require(np.isfinite(good[cols].to_numpy(float)).all(), 'non-finite successful row')
    require((good.se > 0).all() and (good.lo <= good.hi).all(), 'invalid SE or interval')
    require((good.phi.abs() <= 1).all() and (good.kappa.abs() <= 1).all() and (good.sigma_x2 >= 0).all(),
            'invalid covariance parameters')
    require(np.allclose(good.lo, good.beta - Z * good.se, rtol=1e-10, atol=1e-10)
            and np.allclose(good.hi, good.beta + Z * good.se, rtol=1e-10, atol=1e-10), 'interval formula')
    sup = np.where(good.test == 'q1', good.hi < 0, good.lo > 0)
    opp = np.where(good.test == 'q1', good.lo > 0, good.hi < 0)
    require((good.verdict.to_numpy() == np.where(sup, 'supportato', np.where(opp, 'opposto', 'non deciso'))).all(),
            'verdict does not match interval')
    require((good.covered == ((good.lo <= good.effect) & (good.hi >= good.effect)).astype(int)).all(), 'coverage flag')
    require((good.lo_above == (good.lo > good.effect).astype(int)).all(), 'lower exclusion flag')
    require((good.hi_below == (good.hi < good.effect).astype(int)).all(), 'upper exclusion flag')
    acc = dict.fromkeys(MAIN, True)
    failures = []
    for cfg, (test, role, sc, sd, eff, n) in enumerate(expected):
        g, sr = raw[raw.cfg == cfg], summ[summ.cfg == cfg]
        complete = len(g) == n and np.array_equal(np.sort(g.k), np.arange(n))
        complete &= (g.seed == 40000000 + 100000 * cfg + g.k).all()
        complete &= (g.test == test).all() and (g.role == role).all() and (g.scenario == sc).all()
        complete &= np.isclose(g.sd_e, sd, atol=1e-12, rtol=0).all() and np.isclose(g.effect, eff, atol=1e-12, rtol=0).all()
        require(complete, f'incomplete or mismatched cfg {cfg}')
        if len(sr) != 1:
            require(False, f'summary multiplicity cfg {cfg}')
            continue
        r = sr.iloc[0]
        successful = g[g.verdict != 'errore']
        values = {'frac_errors': (g.verdict == 'errore').sum() / n,
                  'supportato': (g.verdict == 'supportato').sum() / n,
                  'opposto': (g.verdict == 'opposto').sum() / n,
                  'coverage': successful.covered.sum() / n,
                  'lo_above': successful.lo_above.sum() / n,
                  'hi_below': successful.hi_below.sum() / n}
        values['exclusion_tail'] = values['lo_above' if test == 'q1' else 'hi_below']
        require(all(np.isclose(float(r[k]), v, atol=1e-12, rtol=0) for k, v in values.items()), f'summary cfg {cfg}')
        if role == 'main':
            passed = (values['supportato'] + values['opposto'] <= .03 and values['supportato'] <= .0175
                      and values['opposto'] <= .0175 and values['frac_errors'] <= .01) if eff == 0 else (
                          values['coverage'] >= .965 and values['exclusion_tail'] <= .02)
            acc[test] &= bool(complete and passed)
            if not passed:
                failures.append(dict(cfg=cfg, test=test, scenario=sc, effect=eff, **values))
    saved = pd.read_csv(val / 'ACCEPTANCE.csv').iloc[0].to_dict()
    require(all(isinstance(saved.get(k), (bool, np.bool_)) and saved[k] == v for k, v in acc.items()), 'acceptance CSV')
    require(meta['acceptance'] == acc, 'acceptance META')
    d = sample()
    worst, count = 0., 0
    for test, rows in good.groupby('test'):
        sub, a = contrast(d, test)
        cache = variance_cache(sub, a)
        for start in range(0, len(rows), 256):
            block = rows.iloc[start:start + 256]
            actual = se_batch(block[['var_a', 'var_b', 'phi', 'kappa', 'sigma_x2']].to_numpy(float), cache)
            rel = np.abs(actual / block.se.to_numpy() - 1)
            require(np.isfinite(rel).all(), f'invalid recomputed SE {test}')
            if np.isfinite(rel).all():
                worst = max(worst, float(rel.max()))
            count += len(block)
    require(worst < 1e-6 and count == len(good), 'recomputed SE mismatch')
    return dict(passed=not issues, issues=issues, recounted_acceptance=acc, n_rows=len(raw),
                n_successful=count, n_errors=int((raw.verdict == 'errore').sum()), n_configs=len(expected),
                max_relative_se_error=worst, failed_scientific_configs=failures,
                script_sha256=sha(__file__), validation_meta_sha256=sha(val / 'META.json'),
                scope='Synthetic validation only; no real-response estimation; no MWO sealed values read')


def selftest():
    # Compare the lag polynomial against the full quadratic form for signed contrast weights.
    rng = np.random.default_rng(91)
    sub = pd.DataFrame({'CR': [2000, 2000, 2003, 2007], 'hemisphere': ['N', 'S', 'N', 'S'], 'phi': [1., 2., 4., 3.]})
    a = np.array([.3, -.5, .8, -.6])
    p = np.array([[2., .4, .7, .3, 9.], [1., -.1, .95, -.2, 4.]])
    actual = se_batch(p, variance_cache(sub, a))
    direct = []
    lp = np.log(sub.phi.to_numpy()); lp -= lp.mean()
    lag = abs(sub.CR.to_numpy()[:, None] - sub.CR.to_numpy()[None, :])
    same = sub.hemisphere.to_numpy()[:, None] == sub.hemisphere.to_numpy()[None, :]
    for va, vb, phi, k, sx in p:
        K = np.where(same, 1., k) * phi ** lag
        direct.append(np.sqrt(np.exp(va) * np.sum(a ** 2 * np.exp(vb * lp)) + sx * a @ K @ a))
    assert np.allclose(actual, direct, rtol=1e-13, atol=0)
    assert len(grid()) == 35 and sum(x[-1] for x in grid()) == 150000
    print('selftest: lag polynomial equals full covariance; grid 35/150000')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--validation', type=Path, default=ROOT / 'results/HMI_FOLLOWUPS_VALIDATION')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.out:
        result = audit(args.validation)
        with args.out.open('x') as f:
            json.dump(result, f, indent=2); f.write('\n')
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['passed'] else 1)
    else:
        ap.error('--out PATH is required, or use --selftest')
