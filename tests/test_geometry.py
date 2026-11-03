"""Test della geometria su bipoli sintetici in mappe CEA oblique come quelle SHARP.

Eseguire dalla radice:  .venv/bin/python -m pytest -q tests
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from sharpbl import geometry as geo  # noqa: E402
from sharpbl import measure  # noqa: E402

R_CM = 6.96e10


def make_header(lon0, lat0, nx=1001, ny=601, cdelt=0.03, t_rec="2024.05.08_03:12:00_TAI"):
    h = fits.Header()
    h["NAXIS"] = 2
    h["NAXIS1"], h["NAXIS2"] = nx, ny
    h["CTYPE1"], h["CTYPE2"] = "CRLN-CEA", "CRLT-CEA"
    h["CUNIT1"], h["CUNIT2"] = "degree", "degree"
    h["CRPIX1"], h["CRPIX2"] = (nx + 1) / 2, (ny + 1) / 2
    h["CRVAL1"], h["CRVAL2"] = lon0, lat0
    h["CDELT1"], h["CDELT2"] = cdelt, cdelt
    h["RSUN_REF"] = R_CM / 100
    h["T_REC"] = t_rec
    h["CRLN_OBS"] = lon0
    return h


def bipole(h, lead, follow, lead_sign=+1, amp=1500.0, sigma_deg=0.8):
    ny, nx = h["NAXIS2"], h["NAXIS1"]
    lon, lat = geo.lonlat_maps(h, (ny, nx))
    u = geo.unit_vectors(lon, lat)

    def blob(c):
        ang = np.degrees(np.arccos(np.clip(u @ geo.unit_vectors(*c), -1, 1)))
        return amp * np.exp(-0.5 * (ang / sigma_deg) ** 2)

    return lead_sign * (blob(lead) - blob(follow))


def displaced(center, s_deg, tilt_joy_deg):
    """Leading e following a distanza s, con la following a est e verso nord di tilt_joy."""
    lon_c, lat_c = center
    a = np.radians(tilt_joy_deg)
    dlon = 0.5 * s_deg * np.cos(a) / np.cos(np.radians(lat_c))
    dlat = 0.5 * s_deg * np.sin(a)
    return (lon_c + dlon, lat_c - dlat), (lon_c - dlon, lat_c + dlat)


def test_wcs_matches_sharp_header_bounds():
    """Sul file reale 11142: la WCS riproduce LATDTMIN/LATDTMAX al centro della patch."""
    f = Path(__file__).resolve().parents[1] / "data/sharp/test_20240508/hmi.sharp_cea_720s.11142.20240508_031200_TAI.Br.fits"
    if not f.exists():
        pytest.skip("caso di prova non scaricato")
    br, h = geo.read_sharp(f)
    lon, lat = geo.lonlat_maps(h, br.shape)
    xc = br.shape[1] // 2
    assert abs(lat[0, xc] - h["LATDTMIN"]) < 0.01
    assert abs(lat[-1, xc] - h["LATDTMAX"]) < 0.01


@pytest.mark.parametrize("lat_c", [0.0, 15.0, 30.0, -30.0, 45.0])
@pytest.mark.parametrize("offset_lon", [0.0, 12.0])
def test_v84_recovers_separation_and_tilt(lat_c, offset_lon):
    h = make_header(200.0, lat_c, nx=1301)
    lead, follow = displaced((200.0 + offset_lon, lat_c), 6.0, 10.0)
    br = bipole(h, lead, follow)
    out = measure.measure_v84(br, None, h)
    d_true = np.radians(geo.great_circle_deg(*lead, *follow)) * R_CM
    assert out["leading_sign"] == 1
    assert out["d_cm"] == pytest.approx(d_true, rel=0.01)
    t_true = geo.tilt_deg(lead, follow)
    assert out["tilt_deg"] == pytest.approx(t_true, abs=0.3)
    # la following e' a nord: sin(alpha) = sin(10 gradi)
    assert out["sintilt"] == pytest.approx(np.sin(np.radians(10.0)), abs=0.01)
    assert out["lat_mean_deg"] == pytest.approx(lat_c, abs=0.2)


def test_legacy_latitude_is_biased_on_oblique_maps():
    h = make_header(200.0, 30.0)
    lead, follow = displaced((200.0, 34.0), 6.0, 10.0)
    br = bipole(h, lead, follow)
    leg = measure.measure_legacy(br, None, h)
    new = measure.measure_v84(br, None, h, bmap_min=1)
    assert new["lat_mean_deg"] == pytest.approx(34.0, abs=0.2)
    assert abs(leg["lat_mean_deg"] - 34.0) > 0.3


def test_dipole_sign():
    """Bipolo con la positiva piu' vicina al polo nord: contributo al dipolo positivo."""
    h = make_header(200.0, 20.0)
    br = bipole(h, (202.0, 18.0), (198.0, 22.0), lead_sign=-1)  # leading negativa, following positiva a nord
    out = measure.measure_v84(br, None, h)
    assert out["d_axial_g"] > 0 and out["d_axial_bal_g"] > 0


def test_reduce_tilt():
    assert geo.reduce_tilt_deg(170.0) == pytest.approx(-10.0)
    assert geo.reduce_tilt_deg(-170.0) == pytest.approx(10.0)
    assert geo.reduce_tilt_deg(45.0) == pytest.approx(45.0)
