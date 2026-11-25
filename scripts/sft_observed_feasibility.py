"""Geometric feasibility of the common domain for the observed-evolution pilot (point 3), from keys.json and P1 metadata.

Version 2, after Codex review f4ad0a7 (docs/SFT_INDEPENDENT_CHECKS_20261125.md). No pixel value is read: the coverage
of a patch is the set of cells of a Carrington grid (step 0.06 deg) that contain at least one pixel centre of its CEA
grid, computed from the header WCS (P1 adapter); NAXIS = 2 CRPIX - 1 (verified by Codex on all 2046 headers).
- common longitude branch: the control coverage is put on the branch of the primary (CRVAL1 difference within 180 deg);
- erosion rule of the draft: C = erode(P0) intersect P1, with P0 the primary coverage and P1 the control coverage;
- directional margin as coordinate offsets: in latitude m_lat = sqrt(4 eta dt)/R + v_max dt/R + 0.5 deg; in longitude
  m_lon = (sqrt(4 eta dt)/R + 0.5 deg)/cos(lat_max) + max|omega - omega_C| dt, with lat_max the largest |lat| of the
  patch (distance along the parallel converted to longitude degrees), eta and Du at the maxima of the parameter grid;
- binary erosion with a rectangular element of half-widths m_lat, m_lon (in cells, rounded up);
- area of C as a solid angle, sum dA/R^2 (180/pi)^2 deg^2; feasible if >= 25 deg^2.
Version 1 (isotropic and directional margins on bounding boxes, 690ded3) is kept in Git history.

    PYTHONPATH=python .venv/bin/python scripts/sft_observed_feasibility.py [--out docs/SFT_OBSERVED_FEASIBILITY_RESULTS.txt]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits
from scipy.ndimage import binary_erosion

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo, sft_core as C  # noqa: E402

STEP = 0.06
R_KM = 6.96e5
ETA_MAX, DU_MAX, P = 466.8, 0.041, 2.33
AREA_MIN = 25.0


def pool():
    c = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv",
                    usecols=["HARPNUM", "T_REC", "role", "NOAA_NUM", "family_rank", "valid_bl"], low_memory=False)
    c["t"] = pd.to_datetime(c.T_REC.str.replace("_TAI", "").str.replace(".", "-", n=2).str.replace("_", " "))
    p, k = c[c.role == "primary"].set_index("HARPNUM"), c[c.role == "control"].set_index("HARPNUM")
    j = p.join(k, lsuffix="_p", rsuffix="_c", how="inner")
    j["gap_d"] = (j.t_c - j.t_p).dt.total_seconds() / 86400
    return j[(j.gap_d >= 1) & (j.gap_d <= 4.5) & (j.valid_bl_p == 1) & (j.family_rank_p == 0)].copy()


def keys(harp, trec):
    f = (ROOT / "data/sharp/fits" / trec[:4] /
         f"hmi.sharp_cea_720s.{harp}.{trec[:4]}{trec[5:7]}{trec[8:10]}_{trec[11:13]}{trec[14:16]}{trec[17:19]}_TAI.keys.json")
    return json.loads(f.read_text())


def pixel_centres(k, branch):
    h = fits.Header()
    for x in ("CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2", "CROTA2"):
        h[x] = k[x]
    nx, ny = int(round(2 * k["CRPIX1"] - 1)), int(round(2 * k["CRPIX2"] - 1))
    lon, lat = geo.lonlat_maps(h, (ny, nx))
    lon = (lon - branch + 180.0) % 360.0 - 180.0 + branch            # common branch around the primary CRVAL1
    return lat.ravel(), lon.ravel()


def feasibility(k0, k1, gap_days):
    branch = float(k0["CRVAL1"])
    la0, lo0 = pixel_centres(k0, branch)
    la1, lo1 = pixel_centres(k1, branch)
    lat_lo, lat_hi = min(la0.min(), la1.min()) - 1, max(la0.max(), la1.max()) + 1
    lon_lo, lon_hi = min(lo0.min(), lo1.min()) - 1, max(lo0.max(), lo1.max()) + 1
    ny, nx = int(math.ceil((lat_hi - lat_lo) / STEP)), int(math.ceil((lon_hi - lon_lo) / STEP))

    def cover(la, lo):
        g = np.zeros((ny, nx), bool)
        g[((la - lat_lo) / STEP).astype(int), ((lo - lon_lo) / STEP).astype(int)] = True
        return g
    P0, P1 = cover(la0, lo0), cover(la1, lo1)
    dts = gap_days * 86400.0
    dif = math.degrees(math.sqrt(4 * ETA_MAX * dts) / R_KM)
    lat_r = np.radians(np.linspace(0, 80, 801))
    vmax = DU_MAX * float(np.max(np.sin(lat_r) * np.cos(lat_r) ** P))
    latmax = float(np.abs(la0).max())
    rot = float(np.max(np.abs(C.omega_rel_deg_day(np.linspace(la0.min(), la0.max(), 60))))) * gap_days
    m_lat = dif + math.degrees(vmax * dts / R_KM) + 0.5
    m_lon = (dif + 0.5) / math.cos(math.radians(latmax)) + rot
    ky, kx = int(math.ceil(m_lat / STEP)), int(math.ceil(m_lon / STEP))
    Cdom = binary_erosion(P0, structure=np.ones((2 * ky + 1, 2 * kx + 1), bool), border_value=0) & P1
    lat_e = lat_lo + STEP * np.arange(ny + 1)
    band = math.radians(STEP) * (np.sin(np.radians(lat_e[1:])) - np.sin(np.radians(lat_e[:-1])))
    area = float((Cdom * band[:, None]).sum()) * (180 / math.pi) ** 2
    return area, m_lat, m_lon, abs(float(k1["CRVAL1"]) - float(k0["CRVAL1"])) > 180


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    q = pool()
    rows = []
    for h, r in q.iterrows():
        area, ml, mo, branch_diff = feasibility(keys(h, r["T_REC_p"]), keys(h, r["T_REC_c"]), r["gap_d"])
        rows.append(dict(HARPNUM=h, gap_d=r["gap_d"], cx="un NOAA" if r["NOAA_NUM_p"] == 1 else "altro/ignoto", area=area,
                         m_lat=ml, m_lon=mo, branch_diff=branch_diff))
    R = pd.DataFrame(rows)
    R["dt_class"] = np.where(R.gap_d < 3, "1-3", "3-4.5")
    R["ok"] = R.area >= AREA_MIN
    lines = [f"pool {len(R)}; CRVAL1 on different branches (put on a common branch): {int(R.branch_diff.sum())}",
             f"margins: m_lat {R.m_lat.min():.2f}-{R.m_lat.max():.2f} deg, m_lon {R.m_lon.min():.2f}-{R.m_lon.max():.2f} deg",
             f"feasible (C >= {AREA_MIN} deg2): {int(R.ok.sum())}", "per cell (feasible / pool):"]
    t = R.groupby(["dt_class", "cx"]).agg(feasible=("ok", "sum"), pool=("ok", "size"))
    lines += [t.to_string(), "per 1-day class (feasible):",
              pd.crosstab(np.select([R.gap_d < 2, R.gap_d < 3], ["1-2", "2-3"], "3-4.5"), R.cx, values=R.ok, aggfunc="sum").to_string(),
              f"area of C: median {R.area.median():.1f}, quartiles {R.area.quantile(.25):.1f} {R.area.quantile(.75):.1f} deg2"]
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        Path(a.out).write_text("Version 2 (Codex review f4ad0a7 applied): common branch, C = erode(P0) & P1, metric margin, "
                               "effective coverage from pixel centres. Header keywords only, no pixel value read.\n" + text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
