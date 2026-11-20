"""Post-freeze, pre-unsealing diagnostic of MWO weights and analytic precision.

Reads DESIGN and the saved header inventory only. No real response or pixel is
read. These are normal-reference calculations under fixed noise assumptions,
not the power of the estimated-variance procedure M. No weights are changed in
any analysis product and no record is excluded.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audit():
    spec = importlib.util.spec_from_file_location('weight_audit_matrix', ROOT / 'scripts/t3_mwo_analysis_recount.py')
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    cat = ROOT / 'results/T3_MWO_CATALOGUE_R2'
    headers = ROOT / 'results/MWO_HEADER_INVENTORY'
    cm = json.loads((cat / 'META.json').read_text())
    hm = json.loads((headers / 'META.json').read_text())
    assert sha(cat / 'DESIGN.csv') == cm['products_sha256']['DESIGN.csv']
    assert sha(headers / 'HEADERS.csv.gz') == hm['products_sha256']['HEADERS.csv.gz']
    d = pd.read_csv(cat / 'DESIGN.csv', dtype={'noaa': str})
    d = d[d.record_set == 'isolated'].reset_index(drop=True)
    key = pd.MultiIndex.from_arrays([d.CR.astype(int), d.hemisphere])
    codes, cells = pd.factorize(key)
    cr = np.array([c for c, _ in cells])
    hemi = np.array([h for _, h in cells])
    K = (hemi[:, None] == hemi[None, :]) * .5 ** abs(cr[:, None] - cr[None, :])
    z = norm.ppf(.9875)
    rows = []
    for name, column in [('flux', 'phi_mwo'), ('area', 'dpd_area'), ('equal', None)]:
        x = d.copy()
        w = d[column].to_numpy(float) if column else np.ones(len(d))
        assert np.isfinite(w).all() and (w > 0).all()
        x['phi_mwo'] = w
        ident, _, X, w = rc.matrix(x)
        assert ident
        g = rc.projection(X, w)
        b = np.bincount(codes, weights=g)
        vt = 7.5 ** 2 * float(b @ K @ b)
        vi = 15. ** 2 * float(g @ g)
        se = math.sqrt(vt + vi)
        target = rc.ramp_true(x, g, .2)
        rows.append(dict(weights=name, n_records=len(d), kish_weight_concentration_n=float(w.sum() ** 2 / (w @ w)),
                         projected_target_20=target, se_known_variance=se, nominal_half_width=z * se,
                         normal_recognition=float(norm.cdf(-z - target / se)), temporal_variance_share=vt / se ** 2))
    fields = ['member', 'GV', 'ICHK', 'BSCALE', 'PSEPMA', 'MRKMOD', 'R0']
    h = pd.read_csv(headers / 'HEADERS.csv.gz', usecols=fields)
    merged = d.merge(h, on='member', how='left', validate='many_to_one')
    assert merged.GV.notna().all()
    w = d.phi_mwo.to_numpy()
    top = merged.nlargest(4, 'phi_mwo')
    summaries = merged.groupby('GV').agg(n_records=('noaa', 'size'), flux=('phi_mwo', 'sum')).reset_index()
    summaries['flux_share'] = summaries.flux / w.sum()
    return dict(scope='Diagnostic after protocol freezing and before opening real tilts; no change of the main analysis',
                assumptions=dict(individual_sd_deg=15., temporal_sd_deg=7.5, temporal_ar1_phi=.5,
                                 cross_hemisphere_kappa=0., nominal_confidence=.975, prescribed_max_reduction=.2),
                analytic_comparison=rows, gv_metadata_summary=summaries.to_dict('records'),
                top_four_flux_share=float(top.phi_mwo.sum() / w.sum()),
                top_four_squared_weight_share=float((top.phi_mwo ** 2).sum() / (w @ w)),
                top_four=top[['noaa', 'day', 'member', 'phi_mwo', 'dpd_area', 'GV', 'BSCALE', 'PSEPMA', 'MRKMOD']].to_dict('records'),
                inputs_sha256={'DESIGN.csv': sha(cat / 'DESIGN.csv'), 'HEADERS.csv.gz': sha(headers / 'HEADERS.csv.gz'),
                               'matrix_recount.py': sha(ROOT / 'scripts/t3_mwo_analysis_recount.py')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit()
    text = json.dumps(result, indent=2) + '\n'
    if args.out:
        with args.out.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
