"""Instrument-independent tilt measurement in a window around a DPD position (MDI pilot, frozen protocol
docs/PROTOCOL_MDI_TILT_PILOT.md §4-5).

The caller (an instrument adapter) supplies pixel arrays already in heliographic coordinates: latitude and Carrington
longitude (deg), radial field B_r (G, NaN where the pixel is missing) and the area of each pixel on the sphere (cm^2).
Instrument-specific checks (disc, mu domain, polar-fill band, map availability) stay in the adapters.

The measurement body reproduces the MWO catalogue (scripts/t3_mwo_catalogue.py `measure`, after amendment A1):
thresholds bmin <= |B_r| <= bmax, flux weights |B_r| * area, flux-weighted spherical centroids of the two
polarities, tilt in the P1 convention (leading = polarity whose vector to the other is within 90 deg of west),
great-circle separation and flux-weighted mean latitude. The MWO chain itself is not modified or imported.
"""
from __future__ import annotations

import numpy as np

from sharpbl import geometry as geo

RSUN_CM = 6.96e10
MSH_CM2 = 2.0 * np.pi * RSUN_CM ** 2 * 1e-6          # one millionth of the solar hemisphere, cm^2


def window_mask(lat, lon, lat0, lon0, dlat=6.0, dlon=8.0, valid=None):
    """|lat - lat0| <= dlat and |lon - lon0| <= dlon (longitude difference wrapped to [-180, 180))."""
    dl = (np.asarray(lon) - lon0 + 180.0) % 360.0 - 180.0
    w = (np.abs(np.asarray(lat) - lat0) <= dlat) & (np.abs(dl) <= dlon)
    return w if valid is None else (w & valid)


def measure(lat, lon, br, area, win, *, bmin, bmax, missing=None, missing_max_frac=0.05, min_pix_per_pol=None):
    """Measure one window. Returns a dict with `status` in
    'window_empty', 'window_missing', 'no_two_polarities', 'polarity_below_min_pixels', 'ok'.

    missing: boolean mask of missing pixels (default: non-finite br); the window fails when the missing pixels in it
    exceed missing_max_frac of the window pixels (strict inequality, as amendment A1 of T3 on MWO)."""
    br = np.asarray(br, dtype=float)
    win = np.asarray(win, dtype=bool)
    missing = ~np.isfinite(br) if missing is None else np.asarray(missing, dtype=bool)
    n_win = int(win.sum())
    if n_win == 0:
        return dict(status="window_empty", n_win=0, n_missing_win=0)
    n_missing = int((missing & win).sum())
    if missing_max_frac is not None and n_missing > missing_max_frac * n_win:
        return dict(status="window_missing", n_win=n_win, n_missing_win=n_missing)
    elig = win & ~missing & np.isfinite(br) & (np.abs(br) <= bmax)
    pos, neg = elig & (br >= bmin), elig & (br <= -bmin)
    wgt = np.abs(br) * area
    out = dict(status="ok", n_win=n_win, n_missing_win=n_missing, npos=int(pos.sum()), nneg=int(neg.sum()),
               flux_pos_mx=float(wgt[pos].sum()), flux_neg_mx=float(wgt[neg].sum()),
               area_pos_msh=float(np.sum(np.broadcast_to(area, br.shape)[pos]) / MSH_CM2),
               area_neg_msh=float(np.sum(np.broadcast_to(area, br.shape)[neg]) / MSH_CM2))
    if not (pos.any() and neg.any()):
        out["status"] = "no_two_polarities"
        return out
    if min_pix_per_pol is not None and min(out["npos"], out["nneg"]) < min_pix_per_pol:
        out["status"] = "polarity_below_min_pixels"
        return out
    both = pos | neg
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    out["lat_bar"] = float((lat[both] * wgt[both]).sum() / wgt[both].sum())
    cp = geo.weighted_centroid(lon[pos], lat[pos], wgt[pos])
    cn = geo.weighted_centroid(lon[neg], lat[neg], wgt[neg])
    t_np = geo.tilt_deg(cn, cp)
    lead, follow = (cp, cn) if abs(t_np) < 90 else (cn, cp)
    out.update(lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1], leading_sign=1 if abs(t_np) < 90 else -1,
               tilt_deg=geo.tilt_deg(lead, follow), sep_deg=geo.great_circle_deg(*cp, *cn))
    return out


# ---------------------------------------------------------------- angular conventions (protocol §5)

def joy_gamma(tilt_deg, lat_ref):
    """gamma = sign(lat_ref) * asin(sin tilt); NaN when lat_ref == 0 (undefined, not zero)."""
    s = np.sign(lat_ref)
    return np.where(s == 0, np.nan, s * np.degrees(np.arcsin(np.sin(np.radians(tilt_deg)))))


def diff_raw(t1, t2):
    """t1 - t2, in (-360, 360) for tilts in (-180, 180]."""
    return np.asarray(t1, dtype=float) - np.asarray(t2, dtype=float)


def diff_dir(t1, t2):
    """Oriented difference in [-180, 180)."""
    return (diff_raw(t1, t2) + 180.0) % 360.0 - 180.0


def diff_ax(t1, t2):
    """Axial difference in [-90, 90)."""
    return (diff_raw(t1, t2) + 90.0) % 180.0 - 90.0


def d_gamma(t1, t2, lat_ref):
    """Joy-signed axial difference with a common reference latitude; NaN when lat_ref == 0."""
    s = np.sign(lat_ref)
    return np.where(s == 0, np.nan, s * diff_ax(t1, t2))
