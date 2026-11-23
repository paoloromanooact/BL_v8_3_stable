"""MDI synoptic adapter for the MDI pilot, level 1 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4).

Maps: mdi.synoptic_Mr_polfil_96m, CR 1909-2104, verified against the SHA-256 of results/MDI_SYNOPTIC_AUDIT.
Grid (FITS 1-based pixel indices i+1, j+1):
    CT = CRVAL1 + (i + 1 - CRPIX1) * CDELT1        Carrington time; L = (360 CR - CT) mod 360
    sin(lat) = CRVAL2 + (j + 1 - CRPIX2) * CDELT2
Field already radial (no division by mu). Pixel area constant: dlon(rad) * dsin(lat) * R_sun^2.
Group rotation: N = integer minimising |360 N - L_DPD - CT(t_DPD)|, ties -> smaller N, with CT(t) = 360 R(t) - 360 and
R(t) from carrington_continuous_from_date of the frozen MWO pipeline (mean period: used ONLY to choose N).
Independent ephemeris check: N must equal cr_of(t_cm), t_cm = t_DPD - LCM / 13.2 deg/day; otherwise 'N_ambiguous'.
The window is extracted along CT, stitching the maps CR and CR +- 1; a part in a missing CR -> 'map_missing'; a window
reaching |lat| >= LAT0 -> 'polar_fill_band'.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/storage/shared/gianluca/MWO_project/sunpy/data")
AUDIT = ROOT / "results/MDI_SYNOPTIC_AUDIT/FILES.csv"
RSUN_CM = 6.96e10
OMEGA_DEG_PER_DAY = 13.2
DIAG_TOL_DEG = 3.0


def _load(name, path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def mwo_pipeline():
    return _load("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py").MP


def ephemeris_cr(times):
    """Integer Carrington rotation from the ephemeris with periodic terms (cr_of of the MWO catalogue)."""
    return _load("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py").cr_of(times)


def parse_jsoc_time(s):
    """'YYYY.MM.DD_hh:mm:ss[_TAI]' with seconds = 60 taken as an interval (as in DPD)."""
    d, h = s[:10].split("."), s[11:19].split(":")
    return datetime(int(d[0]), int(d[1]), int(d[2]), int(h[0]), int(h[1])) + timedelta(seconds=int(h[2]))


# ---------------------------------------------------------------- maps

class Maps:
    """Lazy, SHA-verified access to the synoptic maps by Carrington rotation."""

    def __init__(self, src=SRC, audit=AUDIT, verify=True):
        self.src = Path(src)
        t = pd.read_csv(audit)
        self.sha = dict(zip(t.CAR_ROT.astype(int), t.sha256))
        self.files = dict(zip(t.CAR_ROT.astype(int), t.file))
        self.verify = verify
        self.cache = {}

    def available(self, cr):
        return int(cr) in self.files

    def get(self, cr):
        cr = int(cr)
        if cr not in self.cache:
            p = self.src / self.files[cr]
            if self.verify and hashlib.sha256(p.read_bytes()).hexdigest() != self.sha[cr]:
                raise ValueError(f"SHA mismatch for CR {cr}")
            with fits.open(p) as hd:
                h = hd[-1].header
                data = hd[-1].data.astype(float)
            self.cache[cr] = (h, data)
        return self.cache[cr]


def grid(h, shape):
    """CT per column and latitude (deg) per row."""
    i = np.arange(shape[1])
    j = np.arange(shape[0])
    ct = float(h["CRVAL1"]) + (i + 1 - float(h["CRPIX1"])) * float(h["CDELT1"])
    sinlat = float(h.get("CRVAL2", 0.0)) + (j + 1 - float(h["CRPIX2"])) * float(h["CDELT2"])
    return ct, np.degrees(np.arcsin(np.clip(sinlat, -1, 1)))


def pixel_area_cm2(h):
    return abs(np.radians(float(h["CDELT1"]))) * abs(float(h["CDELT2"])) * RSUN_CM ** 2


# ---------------------------------------------------------------- group rotation

def ct_of_time(t):
    return 360.0 * mwo_pipeline().carrington_continuous_from_date(pd.Timestamp(t).to_pydatetime()) - 360.0


def group_rotation(t_dpd, lon_dpd, lcm):
    """(N, CT_g, N_ephemeris, t_cm). N from the mean-period function (only to pick the integer)."""
    ct_t = ct_of_time(t_dpd)
    x = (ct_t + lon_dpd) / 360.0
    lo = int(np.floor(x))
    cand = [lo, lo + 1]
    dist = [abs(360.0 * n - lon_dpd - ct_t) for n in cand]
    n = cand[0] if dist[0] <= dist[1] else cand[1]                   # ties -> smaller N
    t_cm = pd.Timestamp(t_dpd) - pd.Timedelta(days=float(lcm) / OMEGA_DEG_PER_DAY)
    n_eph = int(ephemeris_cr(pd.DatetimeIndex([t_cm]))[0])
    return n, 360.0 * n - lon_dpd, n_eph, t_cm


# ---------------------------------------------------------------- window extraction

def extract(maps, ct_g, lat0, dlat=6.0, dlon=8.0, margin_deg=0.0):
    """Pixels of the window around (CT_g, lat0), stitched along CT. Returns dict(status, lat, lon, ct, br, area,
    maps, headers) or a failure status. CT window: |CT - CT_g| <= dlon + margin (deg)."""
    half = dlon + margin_deg
    lo_ct, hi_ct = ct_g - half, ct_g + half
    crs = sorted({int(np.floor(c / 360.0)) + 1 for c in (lo_ct, ct_g, hi_ct)})      # CT in [360 (CR - 1), 360 CR)
    if any(not maps.available(c) for c in crs):
        return dict(status="map_missing", maps=crs)
    parts, used, hdrs = [], [], {}
    for c in crs:
        h, data = maps.get(c)
        ct, lat = grid(h, data.shape)
        cols = np.flatnonzero((ct >= lo_ct) & (ct <= hi_ct))
        rows = np.flatnonzero(np.abs(lat - lat0) <= dlat)
        if not len(cols):
            continue
        if np.max(np.abs(lat[rows])) >= float(h.get("LAT0", 90.0)):
            return dict(status="polar_fill_band", maps=crs)
        sub = data[np.ix_(rows, cols)]
        CT, LAT = np.meshgrid(ct[cols], lat[rows])
        parts.append((LAT, CT, sub, np.full(sub.shape, pixel_area_cm2(h)), np.full(sub.shape, c)))
        used.append(c)
        hdrs[c] = h
    lat = np.concatenate([p[0].ravel() for p in parts])
    ct = np.concatenate([p[1].ravel() for p in parts])
    br = np.concatenate([p[2].ravel() for p in parts])
    area = np.concatenate([p[3].ravel() for p in parts])
    crs_px = np.concatenate([p[4].ravel() for p in parts])
    lon = (360.0 * crs_px - ct) % 360.0
    return dict(status="ok", lat=lat, lon=lon, ct=ct, br=br, area=area, maps=used, headers=hdrs)


def map_info(hdrs):
    return dict(maps=";".join(str(c) for c in sorted(hdrs)), img_num=";".join(str(hdrs[c].get("IMG_NUM")) for c in sorted(hdrs)),
                t_start=";".join(str(hdrs[c].get("T_START")) for c in sorted(hdrs)),
                t_stop=";".join(str(hdrs[c].get("T_STOP")) for c in sorted(hdrs)),
                t_rot=";".join(str(hdrs[c].get("T_ROT")) for c in sorted(hdrs)))


def diagnostic_ct(audit=AUDIT):
    """|CT(T_ROT) - CARRTIME| for every map (header metadata only)."""
    t = pd.read_csv(audit)
    d = np.array([ct_of_time(parse_jsoc_time(tr)) - ct for tr, ct in zip(t.T_ROT, t.CARRTIME)])
    return pd.DataFrame(dict(CAR_ROT=t.CAR_ROT, diff_deg=d))
