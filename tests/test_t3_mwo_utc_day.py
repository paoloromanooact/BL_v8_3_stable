"""Same-UTC-day matching must use TAVG-UT, including values beyond midnight.

Only synthetic 2x2 FITS are used. No archived fields or real tilt is measured.
"""
import importlib.util
import io
from datetime import datetime
from pathlib import Path
import tarfile

from astropy.io import fits
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def archive(tmp_path):
    with tarfile.open(tmp_path / 'MWO_2011.tar.gz', 'w:gz') as tf:
        for stamp, tavg in (('110317_2450', 24.5), ('110318_0050', 0.5)):
            h = fits.Header()
            for key, val in dict(CENLON=100.0, B0=0.0, DXB_OBS=9.6, DYB_OBS=13.0).items():
                h[key] = val
            h['TAVG-UT'] = tavg
            f = io.BytesIO()
            fits.PrimaryHDU(np.zeros((2, 2), dtype=np.int16), h).writeto(f)
            info = tarfile.TarInfo(f'2011/m{stamp}_0fe1.fits')
            info.size = len(f.getvalue())
            tf.addfile(info, io.BytesIO(f.getvalue()))
    return tmp_path


def test_runner_groups_by_observed_utc_day(archive, monkeypatch):
    c = load('t3_mwo_catalogue')
    monkeypatch.setattr(c.P, 'ephemeris_ok', lambda h, t: (True, 0.0, 0.0))
    mags = c.magnetogram_table(archive, years=[2011])
    assert len(mags) == 2
    assert set(mags.day) == {'2011-03-18'}
    assert set(mags.filename_day) == {'2011-03-17', '2011-03-18'}
    assert set(mags.obs_time) == {datetime(2011, 3, 18, 0, 30)}
    by_day = {d: g.to_dict('records') for d, g in mags.groupby('day')}
    assert '2011-03-17' not in by_day
    # Both represent the same instant; frozen tie rule chooses lower TAVG-UT.
    assert c.choose(by_day['2011-03-18'], datetime(2011, 3, 18, 1))['tavg'] == 0.5


def test_independent_recount_uses_the_observed_day(archive, monkeypatch):
    c = load('t3_mwo_catalogue_recount')
    monkeypatch.setattr(c, 'meeus', lambda t: (100.0, 0.0))
    mags = c.magnetograms(archive, years=[2011])
    assert len(mags) == 2
    assert {m['day'] for m in mags} == {'2011-03-18'}
    assert {m['ot'] for m in mags} == {datetime(2011, 3, 18, 0, 30)}
    assert all(m['eph'] for m in mags)
