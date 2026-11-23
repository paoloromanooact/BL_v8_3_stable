"""Independent recount of the MDI pilot level 1 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md).

Own code, importing neither python/sharpbl/tilt_window.py nor scripts/mdi_synoptic_adapter.py nor the MWO pipeline:
  - rotation N from an own mean-period Carrington time, CT(t) = 360 ((JD - 2398140.2270) / 27.2752316 - 1), nearest
    integer of (CT(t_DPD) + L_DPD) / 360, ties -> smaller;
  - ephemeris N: own Meeus (Astronomical Algorithms, ch. 29) rotation starts with periodic terms, rotation containing
    t_cm = t_DPD - LCM / 13.2 deg/day; status 'N_ambiguous' iff the two differ;
  - map SHA-256 recomputed with an own reader against the audit; map grid, stitching across rotations, polar-fill band;
  - thresholds, missing pixels, minimum pixels, flux-weighted spherical centroids, P1 tilt, leading polarity,
    separation, flux-weighted latitude, areas per polarity, window and missing counts, statuses;
  - quiet windows (centre L_q = (-CT_q) mod 360, time, DPD contaminants from an own gDPD reader, finite fraction,
    scaled MAD, mean of the valid sides).
The receipt is complete (partial false) only on the real path; injected data gives partial true.

    .venv/bin/python scripts/mdi_pilot_l1_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_l1_recount.py --check
"""
import argparse
import hashlib
import importlib.util
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
PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
R_CM, MSH = 6.96e10, 2.0 * np.pi * 6.96e10 ** 2 * 1e-6
TOL_ANG, TOL_REL = 1e-6, 1e-9
THR = {"main": 50.0, "sens100": 100.0}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- own time and rotations

def jd(t):
    return pd.Timestamp(t).to_julian_date()


def own_ct(t):
    # Reimplement the frozen mean-period definition; Meeus constants below are for the independent ephemeris.
    return 360.0 * (jd(t) - 2398167.329) / 27.2753


def own_n(t, lon):
    x = (own_ct(t) + lon) / 360.0
    lo = int(np.floor(x))
    return lo if abs(360 * lo - lon - own_ct(t)) <= abs(360 * (lo + 1) - lon - own_ct(t)) else lo + 1


def meeus_start(c):
    m = np.radians(281.96 + 26.882476 * c)
    return 2398140.2270 + 27.2752316 * c + 0.1454 * np.sin(m) - 0.0085 * np.sin(2 * m) - 0.0141 * np.cos(2 * m)


def own_eph(t):
    j = jd(t)
    c = int(np.floor((j - 2398140.2270) / 27.2752316))
    while meeus_start(c) > j:
        c -= 1
    while meeus_start(c + 1) <= j:
        c += 1
    return c


# ---------------------------------------------------------------- own maps and windows

class OwnMaps:
    def __init__(self, src=SRC, audit=AUDIT, files=None):
        a = pd.read_csv(audit)
        self.sha = {int(c): h for c, h in zip(a.CAR_ROT, a.sha256)}
        self.path = {int(c): Path(src) / f for c, f in zip(a.CAR_ROT, a.file)} if files is None else files
        self.bad_sha, self.cache = set(), {}

    def get(self, cr):
        if cr not in self.path or not Path(self.path[cr]).exists():
            return None
        if cr not in self.cache:
            if sha(self.path[cr]) != self.sha.get(cr):
                self.bad_sha.add(cr)
            with fits.open(self.path[cr]) as hd:
                h, d = hd[-1].header, hd[-1].data.astype(float)
            x, y = np.arange(1, d.shape[1] + 1), np.arange(1, d.shape[0] + 1)
            self.cache[cr] = dict(h=h, d=d, ct=h["CRVAL1"] + (x - h["CRPIX1"]) * h["CDELT1"],
                                  lat=np.degrees(np.arcsin(np.clip(h.get("CRVAL2", 0.0) + (y - h["CRPIX2"]) * h["CDELT2"], -1, 1))),
                                  area=np.radians(abs(h["CDELT1"])) * abs(h["CDELT2"]) * R_CM ** 2, lat0=h.get("LAT0", 90.0))
        return self.cache[cr]


def own_window(maps, ct_c, lat_c, lon_c):
    """Pixels of the measurement window centred on (lat_c, lon_c), drawn from the columns |CT - ct_c| <= 8."""
    parts, used = [], []
    first = int(np.floor((ct_c - 8) / 360.0)) + 1
    for cr in range(first, int(np.floor((ct_c + 8) / 360.0)) + 2):
        if 360.0 * cr < ct_c - 8 or 360.0 * (cr - 1) > ct_c + 8:
            continue
        m = maps.get(cr)
        if m is None:
            return "map_missing", None, None
        rows = np.abs(m["lat"] - lat_c) <= 6
        if np.abs(m["lat"][rows]).max() >= m["lat0"]:
            return "polar_fill_band", None, None
        cols = (m["ct"] >= ct_c - 8) & (m["ct"] <= ct_c + 8)
        if not cols.any():
            continue
        lon2, lat2 = np.meshgrid((360.0 * cr - m["ct"][cols]) % 360.0, m["lat"][rows])
        parts.append((lat2.ravel(), lon2.ravel(), m["d"][np.ix_(rows, cols)].ravel(), np.full(lat2.size, m["area"])))
        used.append(cr)
    lat, lon, b, a = (np.concatenate([p[i] for p in parts]) for i in range(4))
    w = (np.abs(lat - lat_c) <= 6) & (np.abs((lon - lon_c + 180) % 360 - 180) <= 8)
    return "ok", (lat[w], lon[w], b[w], a[w]), used


def vec(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def centroid(lon, lat, w):
    v = (vec(lon, lat) * w[:, None]).sum(0)
    v /= np.linalg.norm(v)
    return np.degrees(np.arctan2(v[1], v[0])) % 360, np.degrees(np.arcsin(v[2]))


def own_tilt(a, b):
    pa, pb = vec(*a), vec(*b)
    m = (pa + pb) / np.linalg.norm(pa + pb)
    east = np.array([-m[1], m[0], 0.0]) / np.hypot(m[0], m[1])
    north = np.cross(m, east)
    d = pb - pa
    return float(np.degrees(np.arctan2(d @ north, d @ east)))


def own_measure(lat, lon, b, a, bmin, bmax=4000.0, min_pix=10, miss=0.05):
    n, nm = len(b), int((~np.isfinite(b)).sum())
    if n == 0:
        return dict(status="window_empty", n_win=0, n_missing_win=0)
    if nm > miss * n:
        return dict(status="window_missing", n_win=n, n_missing_win=nm)
    bb = np.nan_to_num(b)
    fin = np.isfinite(b) & (np.abs(bb) <= bmax)
    pos, neg = fin & (bb >= bmin), fin & (bb <= -bmin)
    w = np.abs(bb) * a
    out = dict(n_win=n, n_missing_win=nm, npos=int(pos.sum()), nneg=int(neg.sum()), flux_pos_mx=float(w[pos].sum()),
               flux_neg_mx=float(w[neg].sum()), area_pos_msh=float(a[pos].sum() / MSH), area_neg_msh=float(a[neg].sum() / MSH))
    if not (pos.any() and neg.any()):
        return dict(out, status="no_two_polarities")
    if min(out["npos"], out["nneg"]) < min_pix:
        return dict(out, status="polarity_below_min_pixels")
    both = pos | neg
    cp, cn = centroid(lon[pos], lat[pos], w[pos]), centroid(lon[neg], lat[neg], w[neg])
    t = own_tilt(cn, cp)
    lead, fol, sgn = (cp, cn, 1) if abs(t) < 90 else (cn, cp, -1)
    sep = float(np.degrees(np.arccos(np.clip(vec(*cp) @ vec(*cn), -1, 1))))
    return dict(out, status="ok", tilt_deg=own_tilt(lead, fol), leading_sign=sgn, sep_deg=sep, sep_lonsteps=sep / 0.1,
                lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1],
                lat_bar=float((lat[both] * w[both]).sum() / w[both].sum()))


def own_quiet(maps, ct_g, lat0, t_cm, dpd):
    out, vals = {}, []
    for side, tag in ((-1, "qm"), (1, "qp")):
        ct_q = ct_g + 30.0 * side
        l_q = (-ct_q) % 360.0
        t_q = pd.Timestamp(t_cm) + pd.Timedelta(days=30.0 * side / 13.2)
        out[f"{tag}_lon"], out[f"{tag}_time"] = l_q, t_q
        st, px, _ = own_window(maps, ct_q, lat0, l_q)
        if st != "ok":
            out[f"{tag}_status"] = st
            continue
        nb = dpd[(dpd.t_dpd >= t_q - pd.Timedelta(days=1)) & (dpd.t_dpd <= t_q + pd.Timedelta(days=1))]
        hit = ((nb.lat - lat0).abs() <= 12) & (((nb.lon - l_q + 180) % 360 - 180).abs() <= 16)
        out[f"{tag}_finite_frac"] = float(np.isfinite(px[2]).mean()) if len(px[2]) else 0.0
        if hit.any():
            out[f"{tag}_status"] = "dpd_group_inside"
        elif out[f"{tag}_finite_frac"] < 0.5:
            out[f"{tag}_status"] = "finite_below_50pct"
        else:
            x = px[2][np.isfinite(px[2])]
            out[f"{tag}_status"], out[f"{tag}_mad_g"] = "ok", float(1.4826 * np.median(np.abs(x - np.median(x))))
            vals.append(out[f"{tag}_mad_g"])
    out["quiet_mad_g"] = float(np.mean(vals)) if vals else np.nan
    return out


# ---------------------------------------------------------------- comparison

def close(a, b, tol, rel=False):
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if np.isnan(a) and np.isnan(b):
        return True
    return abs(a - b) <= (tol * max(abs(b), 1e-300) if rel else tol)


def compare(rec, smp, maps, dpd):
    """rec: an L1 record; smp: its sample row (t_dpd, lat, lon, lcm). Returns (ok, reason)."""
    n, t_cm = own_n(smp["t_dpd"], smp["lon"]), pd.Timestamp(smp["t_dpd"]) - pd.Timedelta(days=float(smp["lcm"]) / 13.2)
    n_eph = own_eph(t_cm)
    if int(rec.get("N", -1)) != n or int(rec.get("N_ephemeris", -1)) != n_eph:
        return False, f"N {rec.get('N')}/{n} eph {rec.get('N_ephemeris')}/{n_eph}"
    if abs(pd.Timestamp(rec["t_cm"]) - t_cm) > pd.Timedelta(seconds=1) or not close(rec["CT_g"], 360.0 * n - smp["lon"], 1e-9):
        return False, "t_cm or CT_g"
    if n != n_eph:
        return rec["status"] == "N_ambiguous", "N_ambiguous"
    ct_g = 360.0 * n - smp["lon"]
    st, px, used = own_window(maps, ct_g, smp["lat"], smp["lon"])
    if st != "ok":
        return rec["status"] == st, st
    if any(c in maps.bad_sha for c in used):
        return False, "map SHA"
    hd = {c: maps.get(c)["h"] for c in used}
    if str(rec.get("maps")) != ";".join(str(c) for c in sorted(hd)) or \
            str(rec.get("img_num")) != ";".join(str(hd[c].get("IMG_NUM")) for c in sorted(hd)) or \
            any(str(rec.get(k)) != ";".join(str(hd[c].get(K)) for c in sorted(hd)) for k, K in (("t_start", "T_START"), ("t_stop", "T_STOP"), ("t_rot", "T_ROT"))):
        return False, "map metadata"
    for tag, bmin in THR.items():
        m = own_measure(*px, bmin)
        if m["status"] != rec.get(f"{tag}_status"):
            return False, f"{tag} status"
        for k, v in m.items():
            if k == "status":
                continue
            r = rec.get(f"{tag}_{k}")
            if k in ("npos", "nneg", "n_win", "n_missing_win", "leading_sign"):
                if int(r) != int(v):
                    return False, f"{tag}_{k}"
            elif k.startswith("lon_"):                      # circular: the same longitude may be given in another range
                if not (r is not None and np.isfinite(float(r)) and abs((float(v) - float(r) + 180.0) % 360.0 - 180.0) <= TOL_ANG):
                    return False, f"{tag}_{k}"
            elif not close(v, r, TOL_REL if "flux" in k or "area" in k else TOL_ANG, rel="flux" in k or "area" in k):
                return False, f"{tag}_{k}"
    if rec["status"] != rec.get("main_status"):
        return False, "global status"
    q = own_quiet(maps, ct_g, smp["lat"], t_cm, dpd)
    for k, v in q.items():
        r = rec.get(k)
        if k.endswith("_time"):
            if abs(pd.Timestamp(r) - v) > pd.Timedelta(seconds=1):
                return False, k
        elif k.endswith("_status"):
            if str(r) != v:
                return False, k
        elif not close(v, r, 1e-9, rel=k.endswith("mad_g")):
            return False, k
    return True, "values"


def check(l1=L1, rec_dir=REC, write=True, sample=None, maps=None, dpd=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:200]}")

    meta = json.loads((Path(l1) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("L1 products: exact set and actual hashes before reading", set(ps) == {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"}
       and all(sha(Path(l1) / n) == h for n, h in ps.items()))
    real = sample is None
    if real:
        fr = json.loads(FREEZE.read_text())
        ok("frozen protocol unchanged and equal to the one of the run", sha(PROTOCOL) == fr["sha256"] == meta.get("protocol_sha256"))
        sm = json.loads((SEL / "META.json").read_text())
        ok("selection: META linked, products exact and unchanged, audit unchanged",
           meta.get("selection_meta_sha256") == sha(SEL / "META.json") and set(sm["products_sha256"]) == {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}
           and all(sha(SEL / n) == h for n, h in sm["products_sha256"].items()) and meta.get("audit_sha256") == sha(AUDIT))
        sample = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
        maps = OwnMaps()
        spec = importlib.util.spec_from_file_location("selrec", ROOT / "scripts/mdi_pilot_select_recount.py")
        S = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(S)
        dpd = S.read_gdpd(years=range(1995, 2012))
    t = pd.read_csv(Path(l1) / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
    ok("one record per sampled group, same keys and order, unique",
       list(zip(t.noaa, t.day)) == list(zip(sample.noaa, sample.day)) and not t.duplicated(["noaa", "day"]).any(), len(t))
    smp = sample.set_index(["noaa", "day"])
    res = []
    for r in t.to_dict("records"):
        key = (r["noaa"], r["day"])
        res.append(compare(r, smp.loc[key].to_dict(), maps, dpd) if key in smp.index else (False, "not in sample"))
    bad = [(i, why) for i, (g, why) in enumerate(res) if not g]
    ok("every record reproduced: N, ephemeris, t_cm, maps and metadata, statuses, counts, fluxes, areas, centroids, "
       "tilts, separation, lat_bar, quiet windows", not bad, f"{len(res) - len(bad)}/{len(res)} first bad {bad[:4]}")
    ok("maps read with actual SHA equal to the audit", not maps.bad_sha, sorted(maps.bad_sha))
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, l1_meta_sha256=sha(Path(l1) / "META.json"))
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


# ---------------------------------------------------------------- selftest

def t_for(ct, lcm=0.0):
    """A UTC time at which a longitude with Carrington time ct has LCM = lcm (own mean-period inverse)."""
    j = ct / 360.0 * 27.2753 + 2398167.329 + lcm / 13.2
    return pd.Timestamp(pd.to_datetime(j - 2440587.5, unit="D"))


def selftest():
    import tempfile
    spec = importlib.util.spec_from_file_location("l1m", ROOT / "scripts/mdi_pilot_measure_l1.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import geometry as geo
    rng = np.random.default_rng(3)
    pairs = [((rng.uniform(0, 360), rng.uniform(-50, 50)),) for _ in range(300)]
    agree = all(abs(own_tilt(a, (a[0] + d1, a[1] + d2)) - geo.tilt_deg(a, (a[0] + d1, a[1] + d2))) < 1e-9
                for (a,), d1, d2 in zip(pairs, rng.uniform(-5, 5, 300), rng.uniform(-5, 5, 300)))
    ok("own tilt agrees with sharpbl.geometry.tilt_deg on random pairs", agree)
    # Regression: a 0.52-degree discrepancy in the wrong mean-period formula changed N near this boundary.
    boundary_t = pd.Timestamp("2000-01-01")
    boundary_lon = 187.80178403062745
    ok("frozen mean-period N on both sides of the decision boundary (not a tie)",
       own_n(boundary_t, boundary_lon - 0.01) == 1957 and own_n(boundary_t, boundary_lon + 0.01) == 1958
       and all(own_n(boundary_t, boundary_lon + e) == M.A.group_rotation(boundary_t, boundary_lon + e, 0.0)[0]
               for e in (-0.01, 0.01)))
    starts = [meeus_start(c) for c in (1909, 2000, 2104)]
    ok("own Meeus rotation starts close to the mean period (|periodic terms| < 0.2 d)",
       all(abs(s - (2398140.2270 + 27.2752316 * c)) < 0.2 for s, c in zip(starts, (1909, 2000, 2104))))
    with tempfile.TemporaryDirectory() as td:
        M.synthetic_maps(td, crs=(2000, 2001, 2002), lat0=12.0, lon0=200.0)
        files = {c: Path(td) / f"mdi.synoptic_mr_polfil_96m.{c}.Br_polfil.fits" for c in (2000, 2001, 2002)}
        maps_m = M.A.Maps(td, Path(td) / "FILES.csv")
        dpd = pd.DataFrame(dict(t_dpd=pd.to_datetime([t_for(360 * 2001 - 230.0)]), lat=[12.0], lon=[230.0]))
        rows = []
        for lon, lat in ((200.0, 12.0), (100.0, -20.0), (330.0, 15.0)):
            ct = 360.0 * 2001 - lon
            rows.append(dict(noaa=str(int(lon)), day="2003-01-01", t_dpd=t_for(ct, 2.0), lat=lat, lon=lon, lcm=2.0))
        samp = pd.DataFrame(rows)
        rec = pd.DataFrame([M.measure_group(maps_m, r, dpd) for r in samp.itertuples()])
        statuses = list(rec.status)
        ok("synthetic records include ok and a failure status, and a quiet side dropped by a DPD group",
           "ok" in statuses and len(set(statuses)) >= 2 and (rec.qm_status == "dpd_group_inside").any(), statuses)
        own = OwnMaps(td, Path(td) / "FILES.csv", files)
        good = [compare(r, s, own, dpd) for r, s in zip(rec.to_dict("records"), samp.to_dict("records"))]
        ok("own N, ephemeris, extraction, measurement and quiet windows reproduce the measured records", all(g for g, _ in good),
           [w for _, w in good])

        def refused(name, mut, s_mut=None):
            r2 = dict(rec.iloc[0].to_dict(), **mut)
            ok(f"refused: {name}", not compare(r2, dict(samp.iloc[0].to_dict(), **(s_mut or {})), own, dpd)[0])
        refused("invented N_ambiguous row (Codex)", dict(status="N_ambiguous", N=9999, N_ephemeris=1))
        refused("N changed", dict(N=2002))
        refused("main tilt changed by 1e-3 deg", dict(main_tilt_deg=rec.iloc[0].main_tilt_deg + 1e-3))
        refused("lat_bar changed", dict(main_lat_bar=rec.iloc[0].main_lat_bar + 1e-3))
        refused("area per polarity changed", dict(main_area_pos_msh=rec.iloc[0].main_area_pos_msh * 1.01))
        refused("n_missing_win changed", dict(main_n_missing_win=rec.iloc[0].main_n_missing_win + 1))
        refused("centroid changed", dict(main_lon_neg=rec.iloc[0].main_lon_neg + 1e-3))
        refused("separation in steps changed", dict(main_sep_lonsteps=rec.iloc[0].main_sep_lonsteps + 0.1))
        refused("quiet value changed", dict(quiet_mad_g=rec.iloc[0].quiet_mad_g * 1.01))
        refused("quiet side status changed", dict(qm_status="ok"))
        refused("map metadata changed", dict(img_num="1"))
        refused("global status differs from main", dict(status="no_two_polarities"))
        refused("sample time moved by one rotation", {}, dict(t_dpd=t_for(360 * 2002 - 200.0, 2.0)))
        p = files[2001]
        p.write_bytes(p.read_bytes()[:-10] + b"0123456789")
        own2 = OwnMaps(td, Path(td) / "FILES.csv", files)
        compare(rec.iloc[0].to_dict(), samp.iloc[0].to_dict(), own2, dpd)
        ok("map with a changed SHA detected by the own reader", 2001 in own2.bad_sha)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
