"""Synthetic tests of the shared window measurement (MDI pilot, protocol docs/PROTOCOL_MDI_TILT_PILOT.md).

Run from the root:  .venv/bin/python -m pytest -q tests
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from sharpbl import geometry as geo
from sharpbl import tilt_window as tw


def grid(lat0=15.0, lon0=100.0, step=0.1, half=10.0):
    la = np.arange(lat0 - half, lat0 + half + step / 2, step)
    lo = np.arange(lon0 - half, lon0 + half + step / 2, step)
    lon, lat = np.meshgrid(lo, la)
    return lat, lon % 360.0


def dipole(lat, lon, lat0, lon0, tilt, sep=4.0, lead_sign=1, b=800.0, sigma=0.6):
    """Leading polarity (sign lead_sign) to the west; following displaced by `sep` along the tilt direction."""
    t = np.radians(tilt)
    dx, dy = sep / 2 * np.cos(t), sep / 2 * np.sin(t)          # x west, y north (small-angle)
    clat = np.cos(np.radians(lat0))
    lead = (lat0 - dy, lon0 + dx / clat)                          # leading is west of the midpoint
    foll = (lat0 + dy, lon0 - dx / clat)

    def blob(c):
        dl = ((lon - c[1] + 180) % 360 - 180) * clat
        return np.exp(-((lat - c[0]) ** 2 + dl ** 2) / (2 * sigma ** 2))
    return b * lead_sign * (blob(lead) - blob(foll))


@pytest.mark.parametrize("lat0,tilt,lead_sign", [(15.0, 10.0, 1), (15.0, 10.0, -1), (-20.0, -8.0, 1), (25.0, 35.0, -1)])
def test_dipole_tilt_recovered(lat0, tilt, lead_sign):
    lat, lon = grid(lat0)
    br = dipole(lat, lon, lat0, 100.0, tilt, lead_sign=lead_sign)
    win = tw.window_mask(lat, lon, lat0, 100.0)
    r = tw.measure(lat, lon, br, 1.0, win, bmin=50, bmax=4000)
    assert r["status"] == "ok"
    # the P1 convention measures the vector leading -> following: east-pointing, so tilt ~ 180 - tilt_input
    assert abs(tw.diff_ax(r["tilt_deg"], 180.0 - tilt)) < 0.5
    assert r["leading_sign"] == lead_sign


def test_window_across_zero_longitude():
    lat, lon = grid(10.0, 0.0)
    br = dipole(lat, lon, 10.0, 0.0, 12.0)
    win = tw.window_mask(lat, lon, 10.0, 359.95)
    r = tw.measure(lat, lon, br, 1.0, win, bmin=50, bmax=4000)
    assert r["status"] == "ok" and abs(tw.diff_ax(r["tilt_deg"], 168.0)) < 0.5


def test_body_identical_to_geometry_functions():
    lat, lon = grid()
    br = dipole(lat, lon, 15.0, 100.0, 10.0)
    area = np.cos(np.radians(lat)) * 1e15
    win = tw.window_mask(lat, lon, 15.0, 100.0)
    r = tw.measure(lat, lon, br, area, win, bmin=50, bmax=4000)
    elig = win & (np.abs(br) <= 4000)
    pos, neg = elig & (br >= 50), elig & (br <= -50)
    w = np.abs(br) * area
    cp = geo.weighted_centroid(lon[pos], lat[pos], w[pos])
    cn = geo.weighted_centroid(lon[neg], lat[neg], w[neg])
    assert r["lon_pos"] == cp[0] and r["lat_neg"] == cn[1]
    assert r["flux_pos_mx"] == float(w[pos].sum())


def test_thresholds_and_upper_cut():
    lat, lon = grid()
    br = dipole(lat, lon, 15.0, 100.0, 10.0, b=5000.0)
    win = tw.window_mask(lat, lon, 15.0, 100.0)
    r = tw.measure(lat, lon, br, 1.0, win, bmin=50, bmax=4000)
    assert r["npos"] == int((win & (br >= 50) & (br <= 4000)).sum())
    weak = tw.measure(lat, lon, br * 0.001, 1.0, win, bmin=50, bmax=4000)
    assert weak["status"] == "no_two_polarities"


@pytest.mark.parametrize("frac,expected", [(0.04, "ok"), (0.06, "window_missing")])
def test_missing_pixels_below_and_above_5_percent(frac, expected):
    lat, lon = grid()
    br = dipole(lat, lon, 15.0, 100.0, 10.0)
    win = tw.window_mask(lat, lon, 15.0, 100.0)
    idx = np.flatnonzero(win & (np.abs(br) < 1))                 # remove quiet pixels only
    k = int(frac * win.sum())
    br = br.copy()
    br.flat[idx[:k]] = np.nan
    assert tw.measure(lat, lon, br, 1.0, win, bmin=50, bmax=4000)["status"] == expected


def test_min_pixels_per_polarity_and_empty_window():
    lat, lon = grid()
    br = dipole(lat, lon, 15.0, 100.0, 10.0, sigma=0.12)
    win = tw.window_mask(lat, lon, 15.0, 100.0)
    r = tw.measure(lat, lon, br, 1.0, win, bmin=50, bmax=4000, min_pix_per_pol=10_000)
    assert r["status"] == "polarity_below_min_pixels"
    assert tw.measure(lat, lon, br, 1.0, np.zeros_like(win), bmin=50, bmax=4000)["status"] == "window_empty"


def test_angular_differences_at_the_cuts():
    assert tw.diff_ax(89.0, -89.0) == pytest.approx(-2.0)          # across the +-90 cut
    assert tw.diff_ax(90.0, -90.0) == pytest.approx(0.0)
    assert tw.diff_dir(179.0, -179.0) == pytest.approx(-2.0)       # across the +-180 cut
    assert tw.diff_raw(179.0, -179.0) == pytest.approx(358.0)      # raw is not wrapped
    assert -90.0 <= tw.diff_ax(270.0, 0.0) < 90.0


def test_d_gamma_and_joy_gamma_with_reference_latitude():
    assert tw.d_gamma(10.0, 4.0, 12.0) == pytest.approx(6.0)
    assert tw.d_gamma(10.0, 4.0, -12.0) == pytest.approx(-6.0)
    assert np.isnan(tw.d_gamma(10.0, 4.0, 0.0))                    # undefined, not zero
    assert np.isnan(tw.joy_gamma(10.0, 0.0))
    assert tw.d_gamma(10.0, 4.0, 1.5) == pytest.approx(6.0)        # |lat_ref| < 2: still defined by the sign
    assert tw.joy_gamma(170.0, 10.0) == pytest.approx(10.0)
