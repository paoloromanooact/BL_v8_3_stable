"""MDI pilot, level 1: tilts from the MDI synoptic maps at the DPD positions of the level-1 sample (frozen protocol
docs/PROTOCOL_MDI_TILT_PILOT.md §4-5). Requires the preserved selection and its complete recount receipt.

Per sampled group: rotation N (mean-period function only to choose N; ephemeris check), stitched window,
tilt_window.measure with 50 G (main) and 100 G (sensitivity), 4000 G upper cut, >= 10 pixels per polarity, missing
pixels > 5 % -> failure. Records the maps, IMG_NUM, T_START/T_STOP/T_ROT, CT_g, areas per polarity, separation in
units of the 0.1 deg longitude step, and the observed field dispersion in two quiet windows (L_DPD +- 30 deg):
a quiet window is dropped if its box enlarged by +-6 deg lat / +-8 deg lon contains the centre of any DPD group
observed within +-1 day of that longitude's central-meridian passage, or if it has < 50 % finite pixels; statistic =
1.4826 median|B - median B| over finite pixels (observed dispersion, not instrumental noise).

    .venv/bin/python scripts/mdi_pilot_measure_l1.py --selftest
    .venv/bin/python scripts/mdi_pilot_measure_l1.py --run        # after the code review
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import tilt_window as tw  # noqa: E402

AD = importlib.util.spec_from_file_location("mdi_synoptic_adapter", ROOT / "scripts/mdi_synoptic_adapter.py")
A = importlib.util.module_from_spec(AD)
sys.modules["mdi_synoptic_adapter"] = A
AD.loader.exec_module(A)

PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
SEL_REC = ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
OUT = ROOT / "results/MDI_PILOT_L1"
BMAX, MIN_PIX, MISSING_MAX = 4000.0, 10, 0.05
THRESHOLDS = {"main": 50.0, "sens100": 100.0}
QUIET_OFFSET, QUIET_DAYS, QUIET_MIN_FINITE = 30.0, 1.0, 0.5
LON_STEP = 0.1
KEYS = ("status", "npos", "nneg", "flux_pos_mx", "flux_neg_mx", "area_pos_msh", "area_neg_msh", "lat_bar", "lon_pos",
        "lat_pos", "lon_neg", "lat_neg", "leading_sign", "tilt_deg", "sep_deg", "n_win", "n_missing_win")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def mad_scaled(x):
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def quiet(maps, ct_g, lat0, t_cm, dpd_all):
    """Observed field dispersion in the two quiet windows; returns (value or NaN, details)."""
    vals, det = [], []
    for side in (-1, 1):
        ct_q = ct_g + side * QUIET_OFFSET
        t_q = pd.Timestamp(t_cm) + pd.Timedelta(days=side * QUIET_OFFSET / A.OMEGA_DEG_PER_DAY)
        ex = A.extract(maps, ct_q, lat0)
        if ex["status"] != "ok":
            det.append(f"{side:+d}:{ex['status']}")
            continue
        l_q = float(np.median(ex["lon"]))
        near = dpd_all[(dpd_all.t_dpd >= t_q - pd.Timedelta(days=QUIET_DAYS)) & (dpd_all.t_dpd <= t_q + pd.Timedelta(days=QUIET_DAYS))]
        hit = ((near.lat - lat0).abs() <= 12.0) & (((near.lon - l_q + 180.0) % 360.0 - 180.0).abs() <= 16.0)
        win = tw.window_mask(ex["lat"], ex["lon"], lat0, l_q)
        fin = np.isfinite(ex["br"][win]).mean() if win.any() else 0.0
        if hit.any():
            det.append(f"{side:+d}:dpd_group_inside")
        elif fin < QUIET_MIN_FINITE:
            det.append(f"{side:+d}:finite_below_50pct")
        else:
            v = mad_scaled(ex["br"][win])
            vals.append(v)
            det.append(f"{side:+d}:{v:.3f}")
    return (float(np.mean(vals)) if vals else np.nan), ";".join(det)


def measure_group(maps, r, dpd_all):
    n, ct_g, n_eph, t_cm = A.group_rotation(r.t_dpd, r.lon, r.lcm)
    out = dict(noaa=r.noaa, day=r.day, N=n, N_ephemeris=n_eph, CT_g=ct_g, t_cm=str(t_cm))
    if n != n_eph:
        return dict(out, status="N_ambiguous")
    ex = A.extract(maps, ct_g, r.lat)
    if ex["status"] != "ok":
        return dict(out, status=ex["status"], maps=";".join(str(c) for c in ex.get("maps", [])))
    out.update(A.map_info(ex["headers"]))
    win = tw.window_mask(ex["lat"], ex["lon"], r.lat, r.lon)
    for tag, bmin in THRESHOLDS.items():
        m = tw.measure(ex["lat"], ex["lon"], ex["br"], ex["area"], win, bmin=bmin, bmax=BMAX,
                       missing_max_frac=MISSING_MAX, min_pix_per_pol=MIN_PIX)
        for k in KEYS:
            if k in m:
                out[f"{tag}_{k}"] = m[k]
        if "sep_deg" in m:
            out[f"{tag}_sep_lonsteps"] = m["sep_deg"] / LON_STEP
    out["status"] = out["main_status"]
    out["quiet_mad_g"], out["quiet_detail"] = quiet(maps, ct_g, r.lat, t_cm, dpd_all)
    return out


def receipt_ok(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    strict = lambda x: isinstance(x, int) and not isinstance(x, bool)       # noqa: E731
    return (strict(p) and strict(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False
            and r.get(key) == sha(meta))


def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    if not receipt_ok(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json"):
        sys.exit("selection recount receipt missing, incomplete or not bound")
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip", parse_dates=["t_dpd"])
    cat = A._load("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py")
    dpd_all = cat.dpd_groups(years=range(1995, 2012))
    maps = A.Maps()
    rows = [measure_group(maps, r, dpd_all) for r in samp.itertuples()]
    t = pd.DataFrame(rows)
    diag = A.diagnostic_ct()
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        t.to_csv(tmp / "L1_RECORDS.csv", index=False)
        diag.to_csv(tmp / "CT_DIAGNOSTIC.csv", index=False)
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), adapter_sha256=sha(ROOT / "scripts/mdi_synoptic_adapter.py"),
                    module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"), selection_meta_sha256=sha(SEL / "META.json"),
                    selection_receipt_sha256=sha(SEL_REC / "RECEIPT.json"), audit_sha256=sha(A.AUDIT),
                    ct_diagnostic_max_abs_deg=float(diag.diff_deg.abs().max()),
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(t.status.value_counts().to_string())
    return 0


# ---------------------------------------------------------------- selftest (synthetic maps + real headers only)

def synthetic_maps(td, crs=(2000, 2001), lat0=12.0, lon0=2.0, tilt=10.0, sep=4.0, nan_frac=0.0, missing=(), seed=0):
    """Synthetic synoptic maps with the real grid convention and a bipole at (lat0, Carrington lon0) in rotation 2001
    (CT_g = 360*2001 - lon0), close to the border with CR 2000 when lon0 is near 360 or 0."""
    rng = np.random.default_rng(seed)
    rows = []
    for cr in crs:
        if cr in missing:
            continue
        nx, ny = 3600, 1440
        h = fits.Header(dict(CRPIX1=1800.0, CRVAL1=360.0 * cr - 180.0, CDELT1=-0.1, CRPIX2=720.5, CRVAL2=0.0,
                             CDELT2=1.0 / 720.0, CAR_ROT=cr, LAT0=60.0, IMG_NUM=400, T_START="x", T_STOP="y", T_ROT="z"))
        ct, lat = A.grid(h, (ny, nx))
        LON = (360.0 * cr - ct) % 360.0
        lon, la = np.meshgrid(LON, lat)
        t = np.radians(tilt)
        clat = np.cos(np.radians(lat0))
        c = {+1: (lat0 - sep / 2 * np.sin(t), lon0 + sep / 2 * np.cos(t) / clat),
             -1: (lat0 + sep / 2 * np.sin(t), lon0 - sep / 2 * np.cos(t) / clat)}
        B = np.zeros((ny, nx))
        for sgn, (cla, clo) in c.items():                     # same region at its longitude in every map
            dl = ((lon - clo + 180) % 360 - 180) * clat
            B += sgn * 900.0 * np.exp(-((la - cla) ** 2 + dl ** 2) / (2 * 0.7 ** 2))
        B += rng.normal(0, 5.0, B.shape)
        if nan_frac:
            sel = (np.abs(la - lat0) <= 6) & (np.abs(((lon - lon0 + 180) % 360) - 180) <= 8) & (np.abs(B) < 30)
            idx = np.flatnonzero(sel)
            B.flat[idx[: int(nan_frac * sel.sum())]] = np.nan
        f = Path(td) / f"mdi.synoptic_mr_polfil_96m.{cr}.Br_polfil.fits"
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(B.astype(np.float32), header=h)]).writeto(f)
        rows.append(dict(CAR_ROT=cr, file=f.name, sha256=sha(f)))
    pd.DataFrame(rows).to_csv(Path(td) / "FILES.csv", index=False)
    return A.Maps(td, Path(td) / "FILES.csv")


from astropy.io import fits  # noqa: E402


def selftest():
    import tempfile as tf
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    # real header metadata (no pixel data, no tilt)
    d = A.diagnostic_ct()
    ok("CT diagnostic on real headers: |CT(T_ROT) - CARRTIME| <= 3 deg for every map", d.diff_deg.abs().max() <= A.DIAG_TOL_DEG,
       f"max {d.diff_deg.abs().max():.3f}")
    au = pd.read_csv(A.AUDIT)
    good = True
    for _, r in au.iterrows():
        ct, _ = A.grid(dict(CRVAL1=r.CRVAL1, CRPIX1=r.CRPIX1, CDELT1=r.CDELT1, CRVAL2=r.CRVAL2, CRPIX2=r.CRPIX2, CDELT2=r.CDELT2), (1440, 3600))
        good &= abs(ct.min() - r.LON_FRST) < 1e-6 and abs(ct.max() - r.LON_LAST) < 1e-6
    ok("grid formula reproduces LON_FRST/LON_LAST of every real map", good)
    nxt = au.set_index("CAR_ROT")
    gap = [nxt.at[c + 1, "LON_FRST"] - (nxt.at[c, "LON_LAST"] + 0.1) for c in nxt.index if c + 1 in nxt.index]
    ok("border continuity: CT of CR+1 continues CR with the 0.1 deg step", np.allclose(gap, -360.0 + 0.0 * np.array(gap)) or np.allclose(gap, 0.0),
       f"{np.unique(np.round(gap, 6))[:3]}")
    cat = A._load("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py")
    g = cat.dpd_groups(years=range(2000, 2002)).sample(500, random_state=2)
    L0 = np.array([A.mwo_pipeline().cenlon_from_carrington_cont(A.mwo_pipeline().carrington_continuous_from_date(x.to_pydatetime()))
                   for x in g.t_dpd])
    med = float(np.median(g.lcm - ((g.lon - L0 + 180) % 360 - 180)))
    ok("LCM sign on real DPD rows: LCM = L - L0 (so t_cm = t_DPD - LCM / 13.2)", abs(med) < 1.5, f"median {med:.2f}")
    agree = [A.group_rotation(r.t_dpd, r.lon, r.lcm) for r in g.head(200).itertuples()]
    frac = np.mean([a[0] == a[2] for a in agree])
    ok("N from the mean-period function agrees with the ephemeris on real DPD rows (diagnostic)", frac > 0.97, f"{frac:.3f}")
    # synthetic maps
    with tf.TemporaryDirectory() as td:
        maps = synthetic_maps(td, crs=(2000, 2001, 2002), lat0=12.0, lon0=200.0)
        ex = A.extract(maps, 360.0 * 2001 - 200.0, 12.0)
        win = tw.window_mask(ex["lat"], ex["lon"], 12.0, 200.0)
        m = tw.measure(ex["lat"], ex["lon"], ex["br"], ex["area"], win, bmin=50, bmax=4000, min_pix_per_pol=10)
        ok("synthetic bipole in the middle of a map: tilt recovered", m["status"] == "ok" and abs(tw.diff_ax(m["tilt_deg"], 170.0)) < 0.5,
           m.get("tilt_deg"))
    with tf.TemporaryDirectory() as td:
        maps = synthetic_maps(td, crs=(2000, 2001, 2002), lat0=12.0, lon0=359.0)
        ct_g = 360.0 * 2001 - 359.0
        ex = A.extract(maps, ct_g, 12.0)
        win = tw.window_mask(ex["lat"], ex["lon"], 12.0, 359.0)
        m = tw.measure(ex["lat"], ex["lon"], ex["br"], ex["area"], win, bmin=50, bmax=4000, min_pix_per_pol=10)
        ok("synthetic bipole at the border between rotations: stitched maps, tilt recovered",
           ex["maps"] == [2000, 2001] and m["status"] == "ok" and abs(tw.diff_ax(m["tilt_deg"], 170.0)) < 0.5, (ex["maps"], m.get("tilt_deg")))
    with tf.TemporaryDirectory() as td:
        maps = synthetic_maps(td, crs=(2000, 2001, 2002), lat0=12.0, lon0=359.0, missing=(2000,))
        ok("window touching a missing rotation -> map_missing", A.extract(maps, 360.0 * 2001 - 359.0, 12.0)["status"] == "map_missing")
    for frac, exp in ((0.03, "ok"), (0.08, "window_missing")):
        with tf.TemporaryDirectory() as td:
            maps = synthetic_maps(td, crs=(2001,), lat0=12.0, lon0=200.0, nan_frac=frac)
            ex = A.extract(maps, 360.0 * 2001 - 200.0, 12.0)
            win = tw.window_mask(ex["lat"], ex["lon"], 12.0, 200.0)
            st = tw.measure(ex["lat"], ex["lon"], ex["br"], ex["area"], win, bmin=50, bmax=4000, missing_max_frac=0.05)["status"]
            ok(f"missing pixels at {frac:.0%} of the window -> {exp}", st == exp, st)
    with tf.TemporaryDirectory() as td:
        maps = synthetic_maps(td, crs=(2001,), lat0=12.0, lon0=200.0)
        ok("window reaching LAT0 -> polar_fill_band", A.extract(maps, 360.0 * 2001 - 200.0, 57.0)["status"] == "polar_fill_band")
        h, _ = maps.get(2001)
        ok("pixel area constant and equal to dlon dsin R^2", abs(A.pixel_area_cm2(h) - np.radians(0.1) / 720.0 * A.RSUN_CM ** 2) < 1e3)
        t_cm = pd.Timestamp("2003-01-01")
        dpd = pd.DataFrame(dict(t_dpd=[t_cm + pd.Timedelta(days=30 / 13.2)], lat=[12.0], lon=[170.0]))   # inside the +1 window
        v, det = quiet(maps, 360.0 * 2001 - 200.0, 12.0, t_cm, dpd)
        ok("quiet windows: scaled MAD of the noise (sigma 5) where no DPD group; DPD group inside drops the window",
           "+1:dpd_group_inside" in det and det.startswith("-1:") and np.isfinite(v) and abs(v - 5.0) < 0.5, det)
    with tf.TemporaryDirectory() as td:
        maps = synthetic_maps(td, crs=(2001,), lat0=12.0, lon0=200.0)
        p = Path(td) / "mdi.synoptic_mr_polfil_96m.2001.Br_polfil.fits"
        p.write_bytes(p.read_bytes()[:-10] + b"0123456789")
        try:
            maps.get(2001)
            ok("map with a changed SHA refused", False)
        except ValueError:
            ok("map with a changed SHA refused", True)
    src = Path(__file__).read_text().split("def selftest")[0]
    ok("no division by mu in the synoptic path", "/ mu" not in src and "/mu" not in src)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
