"""Independent recount of the MDI pilot level 1 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md).

Own code, not importing python/sharpbl/tilt_window.py nor scripts/mdi_synoptic_adapter.py, for: map grid and
Carrington time, window extraction across rotations, thresholds, missing pixels, minimum pixels, flux-weighted
spherical centroids, the P1 tilt (vector leading -> following in the tangent plane at the midpoint, x west = increasing
Carrington longitude, y north), leading polarity, separation and statuses. The rotation N is taken from the record and
checked for consistency with CT_g = 360 N - L_DPD.
NOT YET recounted (open points for the code review): the ephemeris N (N_ephemeris is taken from the record) and the
quiet-window dispersion values.

    .venv/bin/python scripts/mdi_pilot_l1_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_l1_recount.py --check
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
L1 = ROOT / "results/MDI_PILOT_L1"
REC = ROOT / "results/MDI_PILOT_L1_RECOUNT"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
AUDIT = ROOT / "results/MDI_SYNOPTIC_AUDIT/FILES.csv"
SRC = Path("/storage/shared/gianluca/MWO_project/sunpy/data")
R_CM = 6.96e10
TOL_ANG, TOL_REL = 1e-6, 1e-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def own_map(cr, src=SRC, files=None):
    f = (files or {}).get(cr, Path(src) / f"mdi.synoptic_mr_polfil_96m.{cr}.Br_polfil.fits")
    if not Path(f).exists():
        return None
    with fits.open(f) as hd:
        h, d = hd[-1].header, hd[-1].data.astype(float)
    x = np.arange(1, d.shape[1] + 1)
    y = np.arange(1, d.shape[0] + 1)
    ct = h["CRVAL1"] + (x - h["CRPIX1"]) * h["CDELT1"]
    lat = np.degrees(np.arcsin(np.clip(h.get("CRVAL2", 0.0) + (y - h["CRPIX2"]) * h["CDELT2"], -1, 1)))
    return dict(ct=ct, lat=lat, d=d, area=np.radians(abs(h["CDELT1"])) * abs(h["CDELT2"]) * R_CM ** 2, lat0=h.get("LAT0", 90.0))


def own_window(ct_g, lat_c, lon_c, src=SRC, files=None):
    cols = []
    for cr in (int(ct_g // 360) , int(ct_g // 360) + 1, int(ct_g // 360) + 2):
        lo, hi = 360.0 * (cr - 1), 360.0 * cr
        if hi < ct_g - 8 or lo > ct_g + 8:
            continue
        m = own_map(cr, src, files)
        if m is None:
            return "map_missing", None
        rows = np.abs(m["lat"] - lat_c) <= 6
        if np.abs(m["lat"][rows]).max() >= m["lat0"]:
            return "polar_fill_band", None
        c = (m["ct"] >= ct_g - 8) & (m["ct"] <= ct_g + 8)
        if not c.any():
            continue
        LON = (360.0 * cr - m["ct"][c]) % 360.0
        lon2, lat2 = np.meshgrid(LON, m["lat"][rows])
        cols.append((lat2.ravel(), lon2.ravel(), m["d"][np.ix_(rows, c)].ravel(), m["area"]))
    lat = np.concatenate([c[0] for c in cols])
    lon = np.concatenate([c[1] for c in cols])
    b = np.concatenate([c[2] for c in cols])
    a = np.concatenate([np.full(len(c[0]), c[3]) for c in cols])
    dl = (lon - lon_c + 180) % 360 - 180
    w = (np.abs(lat - lat_c) <= 6) & (np.abs(dl) <= 8)
    return "ok", (lat[w], lon[w], b[w], a[w])


def vec(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def centroid(lon, lat, w):
    v = (vec(lon, lat) * w[:, None]).sum(0)
    v /= np.linalg.norm(v)
    return np.degrees(np.arctan2(v[1], v[0])) % 360, np.degrees(np.arcsin(v[2]))


def own_tilt(a, b):
    """Angle of a -> b in the tangent plane at the midpoint; x = increasing longitude, y = north."""
    pa, pb = vec(*a), vec(*b)
    m = pa + pb
    m /= np.linalg.norm(m)
    east = np.array([-m[1], m[0], 0.0])
    east /= np.linalg.norm(east)
    north = np.cross(m, east)
    d = pb - pa
    return float(np.degrees(np.arctan2(d @ north, d @ east)))


def own_measure(lat, lon, b, a, bmin, bmax=4000.0, min_pix=10, miss=0.05):
    n = len(b)
    nm = int((~np.isfinite(b)).sum())
    if n == 0:
        return dict(status="window_empty")
    if nm > miss * n:
        return dict(status="window_missing")
    fin = np.isfinite(b) & (np.abs(np.nan_to_num(b)) <= bmax)
    pos, neg = fin & (np.nan_to_num(b) >= bmin), fin & (np.nan_to_num(b) <= -bmin)
    w = np.abs(np.nan_to_num(b)) * a
    out = dict(npos=int(pos.sum()), nneg=int(neg.sum()), flux_pos_mx=float(w[pos].sum()), flux_neg_mx=float(w[neg].sum()))
    if not (pos.any() and neg.any()):
        return dict(out, status="no_two_polarities")
    if min(out["npos"], out["nneg"]) < min_pix:
        return dict(out, status="polarity_below_min_pixels")
    cp, cn = centroid(lon[pos], lat[pos], w[pos]), centroid(lon[neg], lat[neg], w[neg])
    t = own_tilt(cn, cp)
    lead, fol, sgn = (cp, cn, 1) if abs(t) < 90 else (cn, cp, -1)
    return dict(out, status="ok", tilt_deg=own_tilt(lead, fol), leading_sign=sgn,
                sep_deg=float(np.degrees(np.arccos(np.clip(vec(*cp) @ vec(*cn), -1, 1)))))


def close(a, b, tol, rel=False):
    a, b = float(a), float(b)
    if np.isnan(a) and np.isnan(b):
        return True
    return abs(a - b) <= (tol * max(abs(b), 1e-300) if rel else tol)


def compare(rec, src=SRC, files=None):
    """True if the record is reproduced; returns (ok, reason)."""
    if rec["status"] in ("N_ambiguous",):
        return rec["N"] != rec["N_ephemeris"], "N_ambiguous"
    ct_g = 360.0 * rec["N"] - rec["lon"]
    if abs(ct_g - rec["CT_g"]) > 1e-9:
        return False, "CT_g"
    st, px = own_window(ct_g, rec["lat"], rec["lon"], src, files)
    if st != "ok":
        return rec["status"] == st, st
    good = True
    for tag, bmin in (("main", 50.0), ("sens100", 100.0)):
        m = own_measure(*px, bmin)
        good &= m["status"] == rec[f"{tag}_status"]
        for k in ("npos", "nneg"):
            if k in m:
                good &= int(m[k]) == int(rec[f"{tag}_{k}"])
        for k in ("flux_pos_mx", "flux_neg_mx"):
            if k in m:
                good &= close(m[k], rec[f"{tag}_{k}"], TOL_REL, True)
        if m["status"] == "ok":
            good &= close(m["tilt_deg"], rec[f"{tag}_tilt_deg"], TOL_ANG) and close(m["sep_deg"], rec[f"{tag}_sep_deg"], TOL_ANG) \
                and int(m["leading_sign"]) == int(rec[f"{tag}_leading_sign"])
    return good, "values"


def check(l1=L1, rec_dir=REC, write=True, files=None, sample=None, src=SRC):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(l1) / "META.json").read_text())
    ok("products match META", all(sha(Path(l1) / n) == h for n, h in meta["products_sha256"].items())
       and set(meta["products_sha256"]) == {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"})
    real = sample is None
    if real:
        ok("selection and audit unchanged", meta["selection_meta_sha256"] == sha(SEL / "META.json") and meta["audit_sha256"] == sha(AUDIT))
        sample = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    t = pd.read_csv(Path(l1) / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
    ok("one record per sampled group, same keys and order", list(zip(t.noaa, t.day)) == list(zip(sample.noaa, sample.day)), len(t))
    m = t.merge(sample[["noaa", "day", "lat", "lon", "lcm"]], on=["noaa", "day"])
    n_from = np.round((m.CT_g + m.lon) / 360.0).astype(int)
    ok("N consistent with CT_g = 360 N - L_DPD", (n_from == m.N).all())
    res = [compare(r._asdict() if hasattr(r, "_asdict") else r, src, files) for r in m.to_dict("records")]
    bad = [i for i, (g, _) in enumerate(res) if not g]
    ok("every record reproduced by own extraction and measurement (statuses, counts, fluxes, tilts)", not bad,
       f"{len(res) - len(bad)}/{len(res)} first bad {bad[:5]}")
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, l1_meta_sha256=sha(Path(l1) / "META.json"),
                   dependency="ephemeris N via cr_of of the MWO catalogue (not recomputed here)")
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


def selftest():
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("l1", ROOT / "scripts/mdi_pilot_measure_l1.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    with tempfile.TemporaryDirectory() as td:
        maps = M.synthetic_maps(td, crs=(2000, 2001, 2002), lat0=12.0, lon0=359.0)
        files = {cr: Path(td) / f"mdi.synoptic_mr_polfil_96m.{cr}.Br_polfil.fits" for cr in (2000, 2001, 2002)}
        rows = []
        for lon0, lat0 in ((359.0, 12.0), (200.0, 12.0), (100.0, -20.0)):
            ct_g = 360.0 * 2001 - lon0
            ex = M.A.extract(maps, ct_g, lat0)
            r = dict(noaa=str(int(lon0)), day="2003-01-01", N=2001, N_ephemeris=2001, CT_g=ct_g, lat=lat0, lon=lon0)
            win = M.tw.window_mask(ex["lat"], ex["lon"], lat0, lon0)
            for tag, bmin in M.THRESHOLDS.items():
                mm = M.tw.measure(ex["lat"], ex["lon"], ex["br"], ex["area"], win, bmin=bmin, bmax=4000, missing_max_frac=0.05, min_pix_per_pol=10)
                r.update({f"{tag}_{k}": mm[k] for k in M.KEYS if k in mm})
            r["status"] = r["main_status"]
            rows.append(r)
        good = [compare(r, files=files) for r in rows]
        ok("own extraction and measurement reproduce the adapter + shared module (bipole, border, noise-only)",
           all(g for g, _ in good), [x[1] for x in good])
        statuses = [r["main_status"] for r in rows]
        ok("synthetic cases include ok and a failure status", "ok" in statuses and len(set(statuses)) >= 2, statuses)
        r2 = dict(rows[0], main_tilt_deg=rows[0]["main_tilt_deg"] + 1e-3)
        ok("refused: tilt changed by 1e-3 deg", not compare(r2, files=files)[0])
        r3 = dict(rows[0], main_npos=rows[0]["main_npos"] + 1)
        ok("refused: pixel count changed", not compare(r3, files=files)[0])
    ok("own tilt agrees with sharpbl.geometry.tilt_deg on random pairs", True if _tilt_agree() else False)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def _tilt_agree():
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import geometry as geo
    rng = np.random.default_rng(3)
    for _ in range(500):
        a = (rng.uniform(0, 360), rng.uniform(-50, 50))
        b = (a[0] + rng.uniform(-5, 5), a[1] + rng.uniform(-5, 5))
        if abs(own_tilt(a, b) - geo.tilt_deg(a, b)) > 1e-9:
            return False
    return True


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
