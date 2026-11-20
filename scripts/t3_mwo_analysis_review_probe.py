"""Reproduce delivery-2 review counterexamples using synthetic data only.

No real DESIGN, SEALED or white-light tilt is read. The output identifies the
reviewed source by hash. Run again after corrections to inspect changed states.
This is an audit probe, not the method's selftest or scientific validation.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def probe():
    source = ROOT / 'scripts/t3_mwo_analysis.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location('mwo_stat_review', source)
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    result = dict(script_sha256=before)
    d = a.synthetic_design(n_per=4)
    for name, action in (
        ('single_hemisphere', lambda: a.columns(d[d.hemisphere == 'N'].reset_index(drop=True))),
        ('empty_sensitivity', lambda: a.fit_beta3(d.iloc[:0].copy())),
    ):
        try:
            action()
            result[name] = 'handled'
        except Exception as exc:
            result[name] = dict(exception=type(exc).__name__, message=str(exc))
    with patch.object(a, 'dpd_group_times', return_value={('1990-01-01', '123'): '1990 01 01 12 00 00'}), \
         patch.object(a, 'spot_rows', return_value={('1990 01 01 12 00 00', '123'): [(12., 100., 5), (14., 102., 5)]}), \
         patch.object(a, 'wl_tilt', side_effect=RuntimeError('REAL_TILT_CALCULATION_ATTEMPTED')):
        try:
            a.wl_for_records(pd.DataFrame([dict(day='1990-01-01', noaa='123')]), tilt=False)
            result['availability_angle'] = 'not calculated'
        except RuntimeError as exc:
            result['availability_angle'] = str(exc)
    with patch.object(a, 'committed', return_value=True), \
         patch.object(a.pd, 'read_csv', return_value='opened_without_recount'):
        try:
            result['seal_check_with_committed_only'] = a.read_sealed(cat=Path('/synthetic'), val=Path('/synthetic-val'))
        except Exception as exc:
            result['seal_check_with_committed_only'] = dict(exception=type(exc).__name__, message=str(exc))
    raw = pd.DataFrame([
        dict(cfg=c['cfg'], k=k, seed=a.seed(c['cfg'], k), role=c['role'], scenario=c['scenario'],
             sd_e=c['sd_e'], effect=c['effect'], truth=0., beta=0., se=1., lo=-3., hi=3.,
             verdict='non deciso', covered=1, lo_above=0, hi_below=0)
        for c in a.configs() for k in range(c['n'])
    ])
    result['synthetic_base_accepted'] = a.summarise(raw)[1]
    raw.loc[0, 'se'] = np.nan
    result['successful_nan_se_accepted'] = a.summarise(raw)[1]
    raw.loc[0, 'se'] = 1.
    raw.loc[0, 'verdict'] = 'unknown'
    result['unknown_verdict_accepted'] = a.summarise(raw)[1]
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Source changed during the review; discard this probe')
    return result


if __name__ == '__main__':
    print(json.dumps(probe(), indent=2))
