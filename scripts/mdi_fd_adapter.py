"""MDI full-disk adapter for the MDI pilot, level 2 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4).

mdi.fd_M_96m_lev182 FITS exported by JSOC carry only the data (BSCALE 0.01, BLANK); the geometry comes from the JSOC
keywords of the record (CRPIX1/2, CDELT1/2 in arcsec, CROTA2, RSUN_OBS in arcsec, CRLT_OBS = B0, CRLN_OBS = L0), saved
by the metadata step. Orthographic projection (as for MWO), solar north up after the CROTA2 rotation, x towards the
west limb; Carrington longitude L = L0 + central-meridian distance (west positive, LCM = L - L0 as in DPD).
B_r = B_LOS / mu, window entirely at mu >= 0.8, area of a pixel on the sphere = |CDELT1 CDELT2| (R_sun_cm / RSUN_OBS)^2 / mu.
QUALITY must be explicit and interpretable and belong to the admissible set (original {0}; level 2 uses the frozen
A1 set {0, 0x200}); a missing QUALITY is never taken as zero.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import tilt_window as tw  # noqa: E402

RSUN_CM = 6.96e10
MU_MIN = 0.8
KEYS = ("CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CROTA2", "RSUN_OBS", "CRLT_OBS", "CRLN_OBS")


def read_data(path):
    with fits.open(path) as hd:
        return hd[-1].data.astype(float)                   # BSCALE applied, BLANK -> NaN by astropy


def geometry(k, shape):
    """Per pixel: latitude, Carrington longitude (deg), mu; NaN off disc. k: dict of the JSOC keywords."""
    ny, nx = shape
    x = (np.arange(nx) + 1.0 - float(k["CRPIX1"])) * float(k["CDELT1"])
    y = (np.arange(ny) + 1.0 - float(k["CRPIX2"])) * float(k["CDELT2"])
    X, Y = np.meshgrid(x, y)
    c = math.radians(float(k.get("CROTA2", 0.0)))
    if c:                                                   # rotate image axes to solar north up
        X, Y = X * math.cos(c) - Y * math.sin(c), X * math.sin(c) + Y * math.cos(c)
    xi, eta = X / float(k["RSUN_OBS"]), Y / float(k["RSUN_OBS"])
    r2 = xi * xi + eta * eta
    disk = r2 < 0.999
    mu = np.full(shape, np.nan)
    mu[disk] = np.sqrt(1.0 - r2[disk])
    b0 = math.radians(float(k["CRLT_OBS"]))
    nx_ = mu * math.cos(b0) - eta * math.sin(b0)
    nz = mu * math.sin(b0) + eta * math.cos(b0)
    lat = np.degrees(np.arcsin(np.clip(nz, -1.0, 1.0)))
    lon = (float(k["CRLN_OBS"]) + np.degrees(np.arctan2(xi, nx_))) % 360.0
    return lat, lon, mu


ORIGINAL_ADMISSIBLE = (0,)
A1_ADMISSIBLE = (0, 0x200)                 # frozen amendment A1 (docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md)


def pixel_area_cm2(k, mu):
    """Area of a pixel on the sphere: |CDELT1 CDELT2| (arcsec^2) x (R_sun_cm / RSUN_OBS)^2 / mu."""
    return abs(float(k["CDELT1"]) * float(k["CDELT2"])) * (RSUN_CM / float(k["RSUN_OBS"])) ** 2 / mu


def parse_quality(q):
    """(value or None, state): hex strings ('0x00000200') and integers accepted; a missing QUALITY is never zero."""
    if q is None or (isinstance(q, float) and math.isnan(q)) or str(q).strip() in ("", "MISSING", "nan", "None"):
        return None, "missing"
    s = str(q).strip()
    try:
        return (int(s, 16) if s.lower().startswith("0x") else int(s)), "ok"
    except ValueError:
        return None, "unparsable"


def measure(data, k, lat0, lon0, bmin, bmax=4000.0, min_pix=10, missing_max=0.05, geom=None, admissible=ORIGINAL_ADMISSIBLE):
    """Window around (lat0, lon0): QUALITY (explicit and interpretable, in the admissible set), disc and mu checks,
    then the shared body. Returns the tilt_window dict."""
    q, state = parse_quality(k.get("QUALITY"))
    if state != "ok":
        return dict(status=f"quality_{state}")
    if q not in admissible:                                  # status name kept from the original rule when that set is used
        return dict(status="quality_not_zero" if tuple(admissible) == ORIGINAL_ADMISSIBLE else "quality_not_admissible",
                    quality=f"0x{q:08x}")
    lat, lon, mu = geom if geom is not None else geometry(k, data.shape)
    win = tw.window_mask(lat, lon, lat0, lon0, valid=np.isfinite(mu))
    if not win.any():
        return dict(status="window_off_disk")
    if np.nanmin(mu[win]) < MU_MIN:
        return dict(status="window_outside_mu_domain", mu_min=float(np.nanmin(mu[win])))
    return tw.measure(lat, lon, data / mu, pixel_area_cm2(k, mu), win, bmin=bmin, bmax=bmax,
                      missing=~np.isfinite(data), missing_max_frac=missing_max, min_pix_per_pol=min_pix)
