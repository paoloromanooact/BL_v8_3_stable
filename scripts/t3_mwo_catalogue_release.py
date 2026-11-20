"""Release of the MWO magnetic tilt catalogue 1974-2012 (step 12 of the T3-on-MWO plan,
docs/T3_MWO_CATALOGUE_RELEASE_PLAN_DRAFT.md). Runs only AFTER the beta3 estimate is preserved in Git: the tilts are
sealed until then, and this script refuses to read SEALED.csv.gz before.

  --export   two tables (isolated, all) joining DESIGN and SEALED with curated column names and units, the list of
             excluded magnetograms (A2, A3), a README skeleton; output results/MWO_TILT_CATALOGUE_RELEASE/.
  --joy      Joy's law per cycle and hemisphere: k in gamma = k sin|lat| (flux-weighted WLS and unweighted), with
             block-bootstrap intervals over CR; descriptive coherence check only.

    .venv/bin/python scripts/t3_mwo_catalogue_release.py --selftest
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
EST = ROOT / "results/T3_MWO_ESTIMATE_R4"
OUT = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE"
A2_LIST = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A2_EXCLUDED_FITS.csv"
A3_LIST = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A3_EXCLUDED_FITS.csv"
JOY_SEED, JOY_REPS, JOY_BLOCK = 69_500_001, 2000, 6

COLUMNS = [  # (release name, source column, unit / meaning)
    ("noaa", "noaa", "DPD group number (string, letters kept)"),
    ("day_utc", "day", "UTC day of the DPD row and of the MWO scan"),
    ("mwo_time_utc", "obs_time", "UTC instant of the MWO magnetogram (session date + TAVG-UT)"),
    ("mwo_file", "member", "FITS member of the MWO archive"),
    ("epoch", "epoch", "instrumental epoch E1-E8 (protocol §4)"),
    ("resolution_class", "res_class", "R1 ~9.5x13 arcsec, R2 ~13x20, R3 ~14x17, R0 other"),
    ("carrington_rotation", "CR", "Carrington rotation of the MWO instant"),
    ("cycle", "cycle", "solar cycle by date (minima 1976-03, 1986-09, 1996-08, 2008-12)"),
    ("hemisphere", "hemisphere", "N or S, sign of lat_flux_weighted"),
    ("lat_flux_weighted_deg", "lat_bar", "flux-weighted latitude of the measured pixels, deg"),
    ("dpd_lat_deg", "dpd_lat", "latitude of the DPD group, deg"),
    ("dpd_carrington_lon_deg", "dpd_lon", "Carrington longitude of the DPD group, deg"),
    ("dpd_lcm_deg", "lcm", "longitude from the central meridian of the DPD group, deg"),
    ("dpd_area_msh", "dpd_area", "corrected whole-spot area of the DPD group, millionths of the hemisphere"),
    ("flux_window_mx", "phi_mwo", "unsigned flux of the pixels with 50 <= |B_r| <= 4000 G in the window, Mx"),
    ("tilt_deg", "tilt_deg", "tilt in the P1 convention (leading = westernmost polarity), deg"),
    ("joy_gamma_deg", "gamma_deg", "Joy variable sign(lat) asin(sin tilt), positive for leading closer to the equator"),
    ("leading_polarity_sign", "leading_sign", "sign of the leading (west) polarity"),
    ("hale_expected_sign", "hale_expected", "leading sign expected from Hale's law for the cycle and hemisphere"),
    ("lon_pos_deg", "lon_pos", "Carrington longitude of the positive-polarity centroid, deg"),
    ("lat_pos_deg", "lat_pos", "latitude of the positive-polarity centroid, deg"),
    ("lon_neg_deg", "lon_neg", "Carrington longitude of the negative-polarity centroid, deg"),
    ("lat_neg_deg", "lat_neg", "latitude of the negative-polarity centroid, deg"),
    ("separation_deg", "sep_deg", "great-circle distance of the two centroids, deg"),
    ("isolated_day", "isolated", "no other DPD group centre inside the window on that day"),
    ("n_neighbours", "n_neighbours", "other DPD group centres inside the window"),
    ("candidate_rank", "rank", "position of the chosen day in the |LCM| order of the candidate days"),
    ("n_candidate_days", "n_cand", "candidate days of the group"),
    ("n_blank_window", "n_blank_win", "BLANK pixels in the window (amendment A1)"),
    ("activity_dpd_norm", "A_main", "monthly hemispheric DPD activity, normalised to the 1974-2012 mean"),
]


def committed(path):
    p = Path(path)
    rel = str(p.relative_to(ROOT))
    files = [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
    tracked = set(subprocess.run(["git", "ls-files", rel], cwd=ROOT, capture_output=True, text=True).stdout.split())
    dirty = subprocess.run(["git", "status", "--porcelain", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return bool(files) and all(str(f.relative_to(ROOT)) in tracked for f in files) and not dirty


def tables(design, sealed):
    out = {}
    for set_name in ("isolated", "all"):
        d = design[design.record_set == set_name]
        s = sealed[sealed.record_set == set_name].drop(columns=["record_set", "day"], errors="ignore")
        m = d.merge(s, on="noaa", how="inner", validate="one_to_one")
        if len(m) != len(d):
            raise ValueError(f"{set_name}: design and sealed rows do not match one to one")
        out[set_name] = m[[src for _, src, _ in COLUMNS]].rename(columns={src: name for name, src, _ in COLUMNS})
    return out


def joy(t, weights=True, reps=JOY_REPS, seed=JOY_SEED):
    """k per (cycle, hemisphere): WLS of gamma on sin|lat| through the origin; block bootstrap over CR."""
    rng = np.random.default_rng(seed)
    rows = []
    for (c, h), g in t.groupby(["cycle", "hemisphere"]):
        s = np.sin(np.radians(np.abs(g.lat_flux_weighted_deg.to_numpy())))
        y = g.joy_gamma_deg.to_numpy()
        w = g.flux_window_mx.to_numpy(float) if weights else np.ones(len(g))
        k = float(np.sum(w * s * y) / np.sum(w * s * s))
        blk = ((g.carrington_rotation - g.carrington_rotation.min()) // JOY_BLOCK).to_numpy()
        ub = np.unique(blk)
        boots = []
        for _ in range(reps):
            pick = np.concatenate([np.nonzero(blk == b)[0] for b in rng.choice(ub, len(ub))])
            boots.append(np.sum(w[pick] * s[pick] * y[pick]) / np.sum(w[pick] * s[pick] ** 2))
        lo, hi = np.quantile(boots, [0.025, 0.975])
        rows.append(dict(cycle=c, hemisphere=h, n=len(g), weighted=weights, k_deg=k, lo=float(lo), hi=float(hi)))
    return pd.DataFrame(rows)


def export():
    if not committed(EST):
        sys.exit("the beta3 estimate is not preserved in Git: tilts stay sealed, no release")
    if OUT.exists():
        sys.exit("release exists")
    design = pd.read_csv(CAT / "DESIGN.csv", dtype={"noaa": str})
    sealed = pd.read_csv(CAT / "SEALED.csv.gz", dtype={"noaa": str})
    tb = tables(design, sealed)
    OUT.mkdir(parents=True)
    tb["isolated"].to_csv(OUT / "MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv", index=False)
    tb["all"].to_csv(OUT / "MWO_TILT_CATALOGUE_ALL_1974_2012.csv", index=False)
    ex = pd.concat([pd.read_csv(A2_LIST).assign(amendment="A2"), pd.read_csv(A3_LIST).assign(amendment="A3")])
    ex.to_csv(OUT / "EXCLUDED_MAGNETOGRAMS.csv", index=False)
    pd.DataFrame(COLUMNS, columns=["column", "source", "definition"]).to_csv(OUT / "COLUMNS.csv", index=False)
    pd.concat([joy(tb["isolated"], True), joy(tb["isolated"], False)]).to_csv(OUT / "JOY_BY_CYCLE.csv", index=False)
    meta = dict(catalogue_meta_sha256=hashlib.sha256((CAT / "META.json").read_bytes()).hexdigest(),
                estimate_meta_sha256=hashlib.sha256((EST / "META.json").read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                products_sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(OUT.iterdir())})
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    return 0


def selftest():
    import tempfile
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    rng = np.random.default_rng(1)
    rows, srows = [], []
    for i in range(400):
        h = "N" if i % 2 else "S"
        lat = rng.uniform(5, 35) * (1 if h == "N" else -1)
        g = 24.0 * np.sin(np.radians(abs(lat))) + rng.normal(0, 5)
        for st in ("isolated", "all"):
            rows.append(dict(record_set=st, noaa=str(i), day="2000-01-01", obs_time="2000-01-01T18:00:00", member="m",
                             epoch="E8", res_class="R1", CR=1950 + i // 20, cycle=23, hemisphere=h, lat_bar=lat,
                             dpd_lat=lat, dpd_lon=100.0, lcm=1.0, dpd_area=100, phi_mwo=1e21 * (1 + i % 3),
                             isolated=True, n_neighbours=0, rank=1, n_cand=3, n_blank_win=0, A_main=1.0))
            srows.append(dict(record_set=st, noaa=str(i), day="2000-01-01", gamma_deg=g, tilt_deg=g, leading_sign=1,
                              hale_expected=1, lon_pos=101.0, lat_pos=lat, lon_neg=99.0, lat_neg=lat, sep_deg=2.0))
    tb = tables(pd.DataFrame(rows), pd.DataFrame(srows))
    ok("two tables, one row per group, curated columns", len(tb["isolated"]) == 400 and len(tb["all"]) == 400
       and list(tb["isolated"].columns) == [c for c, _, _ in COLUMNS])
    j = joy(tb["isolated"], True, reps=200)
    ok("Joy coefficient recovered (true 24 deg) within 3 deg in both hemispheres; interval contains the estimate",
       np.allclose(j.k_deg, 24, atol=3) and ((j.lo <= j.k_deg) & (j.k_deg <= j.hi)).all(), j.k_deg.round(2).tolist())
    bad = pd.DataFrame(srows).iloc[:-1]
    try:
        tables(pd.DataFrame(rows), bad)
        ok("mismatch between design and sealed refused", False)
    except ValueError:
        ok("mismatch between design and sealed refused", True)
    with tempfile.TemporaryDirectory() as td:
        ok("seal: no export before the estimate is preserved (estimate directory not in Git)", not committed(EST))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (export() if a.export else 1))
