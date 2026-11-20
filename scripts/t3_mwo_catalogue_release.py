"""Release of the MWO magnetic tilt catalogue 1974-2012 (step 12 of the T3-on-MWO plan,
docs/T3_MWO_CATALOGUE_RELEASE_PLAN_DRAFT.md). Runs only after the beta3 estimate is preserved in Git AND its
independent recount is complete and bound; the tilts are sealed until then, and this script refuses to read
SEALED.csv.gz before the whole guard passes.

  --export   writes, atomically, results/MWO_TILT_CATALOGUE_RELEASE/:
             MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv and MWO_TILT_CATALOGUE_ALL_1974_2012.csv (DESIGN joined with
             SEALED on record set, group and day, curated names), COLUMNS.csv, EXCLUDED_MAGNETOGRAMS.csv (A2, A3),
             JOY_BY_CYCLE.csv (descriptive Joy's law per cycle and hemisphere, with counts), COMPARISONS/ (copies of the
             stability outputs: white-light and P1 comparisons, Hale agreement), README.md and META.json.

    .venv/bin/python scripts/t3_mwo_catalogue_release.py --selftest
    .venv/bin/python scripts/t3_mwo_catalogue_release.py --export
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
STAB = ROOT / "results/T3_MWO_STABILITY_R4"
EST = ROOT / "results/T3_MWO_ESTIMATE_R4"
EST_RC = ROOT / "results/T3_MWO_ESTIMATE_R4_RECOUNT"
OUT = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE"
A2_LIST = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A2_EXCLUDED_FITS.csv"
A3_LIST = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A3_EXCLUDED_FITS.csv"
JOY_SEED, JOY_REPS, JOY_BLOCK = 69_500_001, 2000, 6
PARTIAL_CYCLES = (20, 24)          # only tails inside 1974-2012
COMPARISON_FILES = ("S1_TABLE.csv", "S1_DPD_SOURCES.csv", "S2_P1.json", "S2_P1_MATCHED.csv", "S3_HALE.csv",
                    "S4_DWL_ALL.csv", "WL_TILTS.csv")

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

POPULATION = """Population. DPD groups (corrected whole-spot area >= 1 millionth, |latitude| <= 45 deg), 1974-01-01 to
2012-12-31 UTC, measured on Mount Wilson Fe I 5250 A full-disc magnetograms of the same UTC day (ephemeris checks,
amendments A2 and A3 exclusions applied before the choice; finest resolution class, then closest to the DPD time).
A record exists when the window |lat - lat_DPD| <= 6 deg, |L - L_DPD| <= 8 deg lies entirely at mu >= 0.8 and both
polarities have pixels with 50 <= |B_r| <= 4000 G (B_r = B_LOS / mu, BLANK pixels excluded, amendment A1). The
isolated table keeps, per group, the first candidate day in |LCM| order on which the group is isolated (no other DPD
group centre in the window) and the measurement succeeds; the all table drops the isolation condition, so the same
group can have a different day in the two tables. This is the population of isolated (or all) MEASURABLE regions at the
selected instant: large regions are measurable more often, and measurability depends on activity (see LOSSES.csv of the
catalogue). Known limits: observing resolution ~10-20 arcsec; saturation and zero-point corrections in the native
FITS are not documented; instrumental epochs before 1996 are known only from the headers; the GV=0.03 and the
anomalous-distribution magnetograms are excluded (EXCLUDED_MAGNETOGRAMS.csv)."""


def h256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def committed(path):
    p = Path(path)
    rel = str(p.relative_to(ROOT))
    files = [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
    tracked = set(subprocess.run(["git", "ls-files", rel], cwd=ROOT, capture_output=True, text=True).stdout.split())
    dirty = subprocess.run(["git", "status", "--porcelain", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return bool(files) and all(str(f.relative_to(ROOT)) in tracked for f in files) and not dirty


def products_match(directory):
    m = json.loads((Path(directory) / "META.json").read_text())
    listed = m.get("products_sha256", {})
    present = {f.name for f in Path(directory).iterdir() if f.is_file() and f.name not in ("META.json", "RUN.log")}
    return bool(listed) and set(listed) == present and all(h256(Path(directory) / n) == h for n, h in listed.items())


def release_problem(est=EST, est_rc=EST_RC, cat=CAT, stab=STAB, is_committed=None):
    """Whole guard before SEALED is read (Codex, b2a7944): estimate, its recount, catalogue and stability preserved;
    recount receipt with the full semantics and bound to the estimate META; estimate bound to the CURRENT catalogue and
    stability META; actual products of catalogue, stability and estimate equal to their META."""
    is_committed = is_committed or committed
    for p, name in ((est, "estimate"), (est_rc, "estimate recount"), (cat, "catalogue"), (stab, "stability")):
        if not is_committed(p):
            return f"the {name} is not preserved in Git: tilts stay sealed, no release"
    r = json.loads((Path(est_rc) / "RECEIPT.json").read_text())
    is_int = lambda x: isinstance(x, int) and not isinstance(x, bool)    # noqa: E731
    if not (is_int(r.get("total")) and is_int(r.get("passed")) and r["total"] > 0 and r["passed"] == r["total"]
            and r.get("partial") is False and isinstance(r.get("checks"), list) and len(r["checks"]) == r["total"]
            and all(isinstance(c, dict) and c.get("ok") is True for c in r["checks"])
            and r.get("estimate_meta_sha256") == h256(Path(est) / "META.json")):
        return "estimate recount receipt not complete or not bound to the estimate META"
    em = json.loads((Path(est) / "META.json").read_text())
    if em.get("catalogue_meta_sha256") != h256(Path(cat) / "META.json"):
        return "the estimate is bound to another catalogue"
    if em.get("stability_meta_sha256") != h256(Path(stab) / "META.json"):
        return "the estimate is bound to another stability stage"
    for d in (cat, stab, est):
        if not products_match(d):
            return f"{Path(d).name}: products do not match META"
    return None


def tables(design, sealed):
    """Join on (record set, group, day) with one-to-one equality of the keys: no extra or missing SEALED row."""
    out = {}
    for set_name in ("isolated", "all"):
        d = design[design.record_set == set_name]
        s = sealed[sealed.record_set == set_name]
        kd, ks = set(zip(d.noaa, d.day)), set(zip(s.noaa, s.day))
        if len(kd) != len(d) or len(ks) != len(s) or kd != ks:
            raise ValueError(f"{set_name}: DESIGN and SEALED keys (group, day) differ or repeat")
        m = d.merge(s.drop(columns=["record_set"]), on=["noaa", "day"], how="inner", validate="one_to_one")
        out[set_name] = m[[src for _, src, _ in COLUMNS]].rename(columns={src: name for name, src, _ in COLUMNS})
    return out


def joy(t, weights=True, reps=JOY_REPS, seed=JOY_SEED):
    """Descriptive k per (cycle, hemisphere): least squares of gamma on sin|lat| through the origin; percentile
    bootstrap over blocks of 6 consecutive CR inside the group; counts and invalid replicates reported."""
    rng = np.random.default_rng(seed)
    rows = []
    for (c, h), g in t.groupby(["cycle", "hemisphere"]):
        s = np.sin(np.radians(np.abs(g.lat_flux_weighted_deg.to_numpy())))
        y = g.joy_gamma_deg.to_numpy()
        w = g.flux_window_mx.to_numpy(float) if weights else np.ones(len(g))
        k = float(np.sum(w * s * y) / np.sum(w * s * s))
        blk = ((g.carrington_rotation - g.carrington_rotation.min()) // JOY_BLOCK).to_numpy()
        ub = np.unique(blk)
        boots, invalid = [], 0
        for _ in range(reps):
            pick = np.concatenate([np.nonzero(blk == b)[0] for b in rng.choice(ub, len(ub))])
            den = np.sum(w[pick] * s[pick] ** 2)
            if not den > 0:
                invalid += 1
                continue
            boots.append(np.sum(w[pick] * s[pick] * y[pick]) / den)
        lo, hi = np.quantile(boots, [0.025, 0.975]) if boots else (np.nan, np.nan)
        rows.append(dict(cycle=c, hemisphere=h, weighted=weights, n_regions=len(g), n_cr=int(g.carrington_rotation.nunique()),
                         n_blocks=len(ub), k_deg=k, lo=float(lo), hi=float(hi), invalid_replicates=invalid,
                         partial_cycle=bool(c in PARTIAL_CYCLES)))
    return pd.DataFrame(rows)


def readme(tb, joy_tab, meta):
    lines = ["# Mount Wilson magnetic tilt catalogue 1974-2012", "",
             "Built for test T3 of the SHARP BL project (docs/PROTOCOL_T3_MWO.md, amendments A1-A3).", "",
             POPULATION, "",
             f"Tables: isolated {len(tb['isolated'])} regions, all {len(tb['all'])} regions.", "",
             "## Columns", ""] + [f"- `{n}`: {d}" for n, _, d in COLUMNS] + [
             "", "## Joy's law per cycle (descriptive, no test)", "",
             "k in gamma = k sin|lat| per cycle and hemisphere, through the origin; flux-weighted and unweighted; "
             "percentile bootstrap over blocks of 6 CR (2000 replicates, seed 69 500 001). Cycles 20 and 24 are "
             "only partly covered.", "", joy_tab.round(3).to_string(index=False), "",
             "## Comparisons", "",
             "COMPARISONS/ holds the stability outputs: white-light DPD tilts by epoch (S1), the comparison with "
             "SDO/HMI (P1) in 2010-2012 (S2_P1), Hale agreement by epoch (S3) and the d_WL of the all-records set.", "",
             "## Provenance", "", "```", json.dumps(meta, indent=2), "```", ""]
    return "\n".join(lines)


def export(cat=CAT, stab=STAB, est=EST, est_rc=EST_RC, out=OUT, is_committed=None):
    why = release_problem(est, est_rc, cat, stab, is_committed)
    if why:
        sys.exit(why)
    if Path(out).exists():
        sys.exit("release exists")
    design = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    sealed = pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})      # only after the guard
    tb = tables(design, sealed)
    jt = pd.concat([joy(tb["isolated"], True), joy(tb["isolated"], False)], ignore_index=True)
    tmp = Path(out).with_name(Path(out).name + f".partial_{os.getpid()}")       # atomic: rename at the end
    (tmp / "COMPARISONS").mkdir(parents=True)
    tb["isolated"].to_csv(tmp / "MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv", index=False)
    tb["all"].to_csv(tmp / "MWO_TILT_CATALOGUE_ALL_1974_2012.csv", index=False)
    pd.concat([pd.read_csv(A2_LIST).assign(amendment="A2"), pd.read_csv(A3_LIST).assign(amendment="A3")]).to_csv(
        tmp / "EXCLUDED_MAGNETOGRAMS.csv", index=False)
    pd.DataFrame(COLUMNS, columns=["column", "source", "definition"]).to_csv(tmp / "COLUMNS.csv", index=False)
    jt.to_csv(tmp / "JOY_BY_CYCLE.csv", index=False)
    for f in COMPARISON_FILES:
        if (Path(stab) / f).exists():
            shutil.copy2(Path(stab) / f, tmp / "COMPARISONS" / f)
    meta = dict(catalogue_meta_sha256=h256(Path(cat) / "META.json"), stability_meta_sha256=h256(Path(stab) / "META.json"),
                estimate_meta_sha256=h256(Path(est) / "META.json"),
                estimate_recount_receipt_sha256=h256(Path(est_rc) / "RECEIPT.json"),
                script_sha256=h256(Path(__file__)))
    (tmp / "README.md").write_text(readme(tb, jt, meta))
    meta["products_sha256"] = {str(f.relative_to(tmp)): h256(f) for f in sorted(tmp.rglob("*")) if f.is_file()}
    (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    os.rename(tmp, out)
    return 0


def selftest():
    """Synthetic data only; the real estimate state is never used."""
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
            day = "2000-01-01" if st == "isolated" else "2000-01-02"
            rows.append(dict(record_set=st, noaa=str(i), day=day, obs_time=f"{day}T18:00:00", member="m",
                             epoch="E8", res_class="R1", CR=1950 + i // 20, cycle=23, hemisphere=h, lat_bar=lat,
                             dpd_lat=lat, dpd_lon=100.0, lcm=1.0, dpd_area=100, phi_mwo=1e21 * (1 + i % 3),
                             isolated=True, n_neighbours=0, rank=1, n_cand=3, n_blank_win=0, A_main=1.0))
            srows.append(dict(record_set=st, noaa=str(i), day=day, gamma_deg=g, tilt_deg=g, leading_sign=1,
                              hale_expected=1, lon_pos=101.0, lat_pos=lat, lon_neg=99.0, lat_neg=lat, sep_deg=2.0))
    D, S = pd.DataFrame(rows), pd.DataFrame(srows)
    tb = tables(D, S)
    ok("two tables, one row per group, curated columns, days kept per set",
       len(tb["isolated"]) == 400 and len(tb["all"]) == 400 and list(tb["isolated"].columns) == [c for c, _, _ in COLUMNS]
       and set(tb["all"].day_utc) == {"2000-01-02"})
    for label, bad in (("SEALED day discordant", S.assign(day=np.where(np.arange(len(S)) == 0, "1999-12-31", S.day))),
                       ("extra SEALED row", pd.concat([S, S.iloc[[0]].assign(noaa="9999")])),
                       ("missing SEALED row", S.iloc[1:])):
        try:
            tables(D, bad)
            ok(f"join refuses: {label}", False)
        except ValueError:
            ok(f"join refuses: {label}", True)
    j = joy(tb["isolated"], True, reps=200)
    ok("Joy: true 24 deg recovered within 3 deg; counts and partial-cycle flag reported",
       np.allclose(j.k_deg, 24, atol=3) and {"n_regions", "n_cr", "n_blocks", "invalid_replicates", "partial_cycle"} <= set(j.columns),
       j.k_deg.round(2).tolist())
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cat, stab, est, rc, out = (td / x for x in ("cat", "stab", "est", "rc", "out"))
        for p in (cat, stab, est, rc):
            p.mkdir()
        D.to_csv(cat / "DESIGN.csv", index=False)
        S.to_csv(cat / "SEALED.csv.gz", index=False)
        (cat / "META.json").write_text(json.dumps(dict(products_sha256={n: h256(cat / n) for n in ("DESIGN.csv", "SEALED.csv.gz")})))
        (stab / "S2_P1.json").write_text("{}")
        (stab / "META.json").write_text(json.dumps(dict(products_sha256={"S2_P1.json": h256(stab / "S2_P1.json")})))
        (est / "FINAL.json").write_text("{}")
        (est / "META.json").write_text(json.dumps(dict(products_sha256={"FINAL.json": h256(est / "FINAL.json")},
                                                       catalogue_meta_sha256=h256(cat / "META.json"),
                                                       stability_meta_sha256=h256(stab / "META.json"))))
        good = dict(passed=2, total=2, partial=False, checks=[{"ok": True}, {"ok": True}], estimate_meta_sha256=h256(est / "META.json"))
        yes = lambda p: True   # noqa: E731
        (rc / "RECEIPT.json").write_text(json.dumps(dict(good, passed=1)))
        p1 = release_problem(est, rc, cat, stab, yes)
        (rc / "RECEIPT.json").write_text(json.dumps(dict(good, estimate_meta_sha256="old")))
        p2 = release_problem(est, rc, cat, stab, yes)
        (rc / "RECEIPT.json").write_text(json.dumps(good))
        p3 = release_problem(est, rc, cat, stab, yes)
        p4 = release_problem(est, rc, cat, stab, lambda p: p != rc)
        em = json.loads((est / "META.json").read_text())
        (est / "META.json").write_text(json.dumps(dict(em, catalogue_meta_sha256="old")))
        good2 = dict(good, estimate_meta_sha256=h256(est / "META.json"))
        (rc / "RECEIPT.json").write_text(json.dumps(good2))
        p5 = release_problem(est, rc, cat, stab, yes)                       # estimate bound to an obsolete catalogue
        (est / "META.json").write_text(json.dumps(em))
        (rc / "RECEIPT.json").write_text(json.dumps(good))
        S.iloc[:-1].to_csv(cat / "SEALED.csv.gz", index=False)
        p6 = release_problem(est, rc, cat, stab, yes)                       # SEALED changed, META not
        S.to_csv(cat / "SEALED.csv.gz", index=False)
        ok("guard: incomplete or unbound receipt, missing recount, obsolete catalogue, changed product refused; full chain accepted",
           p1 and p2 and p3 is None and p4 and p5 and p6, (p1, p2, p3, p4, p5, p6))
        export(cat, stab, est, rc, out, yes)
        made = sorted(str(f.relative_to(out)) for f in out.rglob("*") if f.is_file())
        meta = json.loads((out / "META.json").read_text())
        ok("export: atomic directory with tables, README, Joy, exclusions, comparisons and product hashes",
           {"MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv", "MWO_TILT_CATALOGUE_ALL_1974_2012.csv", "README.md",
            "JOY_BY_CYCLE.csv", "EXCLUDED_MAGNETOGRAMS.csv", "COLUMNS.csv", "COMPARISONS/S2_P1.json"} <= set(made)
           and not list(td.glob("out.partial_*")) and all(h256(out / n) == h for n, h in meta["products_sha256"].items()))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (export() if a.export else 1))
