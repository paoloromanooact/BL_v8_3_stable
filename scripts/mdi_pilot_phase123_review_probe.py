"""Synthetic counterexamples for the phase 1–3 code review; no real MDI pixels or network."""
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
S = load('sel_probe', 'mdi_pilot_select.py')
R = load('rec_probe', 'mdi_pilot_select_recount.py')
M = load('measure_probe', 'mdi_pilot_measure_l1.py')
L = load('l1_rec_probe', 'mdi_pilot_l1_recount.py')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
out = {}
p, _ = S.synthetic_population()
s, cells = S.draw(p)
with tempfile.TemporaryDirectory() as td:
    d = Path(td)
    def check(sample):
        p.to_csv(d/'POPULATION.csv', index=False)
        sample.to_csv(d/'SAMPLE.csv', index=False)
        cells.to_csv(d/'CELLS.csv', index=False)
        (d/'META.json').write_text(json.dumps({'products_sha256': {n:sha(d/n) for n in R.PRODUCTS}}))
        with contextlib.redirect_stdout(io.StringIO()):
            return R.check(d, write=False, pop_own=p)
    out['selection_base_accepted'] = check(s)
    for name, col, value in [('latitude','lat',0.0), ('longitude','lon',315.0), ('time','t_dpd','2000-01-01'), ('activity','A_main',123.0), ('level2_weight','w2',999999.0)]:
        altered = s.copy()
        i = altered.index[altered.level2][0]
        altered.loc[i,col] = value
        out['selection_mutated_'+name+'_accepted'] = check(altered)
out['l1_fabricated_ambiguous_record_accepted'] = L.compare({'status':'N_ambiguous','N':9999,'N_ephemeris':1}, {'t_dpd':'2000-01-01','lon':100.,'lat':12.,'lcm':0.}, None, pd.DataFrame())[0]

# Synthetic extraction crossing longitude zero; no real maps or tilts.
original = M.A.extract
def extract(*args, **kw):
    lon = (-args[1]) % 360.0
    return {'status':'ok','lon':np.array([(lon-1)%360,(lon+1)%360]),'lat':np.array([0.,0.]),'br':np.array([-10.,10.]) if lon == 0 else np.array([-5.,5.])}
M.A.extract = extract
empty = pd.DataFrame({'t_dpd':pd.to_datetime([]),'lat':[],'lon':[]})
q = M.quiet(None, 720030., 0., pd.Timestamp('2000-01-01'), empty)
v, detail = q['quiet_mad_g'], [q['qm_status'], q['qp_status']]
out['quiet_wrap_finite_result'] = bool(np.isfinite(v))
out['quiet_wrap_detail'] = detail
out['quiet_wrap_value'] = v
out['quiet_wrap_expected_value'] = 1.4826 * (10+5)/2
M.A.extract = original
out['boundary_N'] = [L.own_n(pd.Timestamp('2000-01-01'), 187.80178403062745 + e) for e in (-0.01,0.01)]
assert out['selection_base_accepted']
assert not any(out[k] for k in out if k.startswith('selection_mutated_'))
assert not out['l1_fabricated_ambiguous_record_accepted']
assert out['quiet_wrap_finite_result'] and detail == ['ok', 'ok']
assert abs(out['quiet_wrap_value'] - out['quiet_wrap_expected_value']) < 1e-12
assert out['boundary_N'] == [1957,1958]
report = json.dumps(out, indent=2)
print(report)
