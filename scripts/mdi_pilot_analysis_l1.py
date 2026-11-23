"""MDI pilot, phase 6 (level-1 part): descriptive Q1 and Q3 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §5).

Q1 - yield on all 530 sampled groups (denominator = sample; failures, including map_missing with empty measurement
     columns, stay in it), by cell x cohort with causes; projected yield on the eligible population with the sampling
     weights w1 = 1/pi1 (ratio estimator); 100 G sensitivity; quiet-window availability and exclusion causes per side
     and the observed field dispersion (scaled MAD; not instrumental noise); exploratory M fit of the covariance on the
     residuals of gamma from a Joy model per cycle x hemisphere (only variance parameters and boundary flags are kept;
     no coefficient, SE or interval is saved).
Q3 - cohort M1 only (MWO isolated record on the chosen day), main threshold measurement ok: relative differences
     MDI(synoptic) - MWO, without assuming either instrument correct: d_raw, d_dir, d_ax, d_gamma = sign(lat_DPD) d_ax
     (undefined at lat_DPD = 0), leading agreement, flux ratio syn/MWO, time distance MWO - t_cm. Classes fixed
     before any difference is computed: activity and area classes of the sample, separation terciles from the
     level-1 successful measurements (all cohorts), |LCM| terciles of the M1 pairs. Bootstrap: blocks
     floor((N - N_min)/6) on the pairs of each group, 2000 replicates, seed 71 100 001, percentiles only with >= 1900
     valid replicates; < 10 pairs -> n and medians only; < 3 blocks -> interval 'non valutabile'. 100 G as secondary.
BARD-MDI is not compared here: BARD has no NOAA number and the frozen text fixes no matching rule (open point).

    .venv/bin/python scripts/mdi_pilot_analysis_l1.py --selftest
    .venv/bin/python scripts/mdi_pilot_analysis_l1.py --run         # after the code review
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

PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
L1, L1_REC = ROOT / "results/MDI_PILOT_L1", ROOT / "results/MDI_PILOT_L1_RECOUNT"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
OUT = ROOT / "results/MDI_PILOT_ANALYSIS_L1"
SEED, REPS, MIN_VALID, MIN_PAIRS, MIN_BLOCKS, BLOCK = 71_100_001, 2000, 1900, 10, 3, 6
MINIMA = [(21, "1976-03-01"), (22, "1986-09-01"), (23, "1996-08-01"), (24, "2008-12-01")]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strict_receipt(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    si = lambda x: isinstance(x, int) and not isinstance(x, bool)       # noqa: E731
    return (si(p) and si(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False and r.get(key) == sha(meta))


def products_ok(folder, names):
    m = json.loads((Path(folder) / "META.json").read_text())
    ps = m.get("products_sha256", {})
    return set(ps) == set(names) and all(sha(Path(folder) / n) == h for n, h in ps.items()), m


def cycle_of(day):
    c = 20
    for k, m in MINIMA:
        if pd.Timestamp(day) >= pd.Timestamp(m):
            c = k
    return c


# ---------------------------------------------------------------- Q1

def q1_yield(rec, samp, pop_cells):
    """rec, samp: aligned on (noaa, day), all sampled groups. Returns (per cell x cohort table, projected table)."""
    m = samp.merge(rec[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left", validate="one_to_one")
    if m.status.isna().any():
        raise ValueError("sampled group without a level-1 record")
    m["ok"] = m.status == "ok"
    m["ok100"] = m.sens100_status == "ok"
    keys = ["act_class", "hemisphere", "area_class", "cohort"]
    causes = pd.crosstab([m[k] for k in keys], m.status).add_prefix("cause_").reset_index()
    cell = m.groupby(keys).agg(n=("ok", "size"), ok=("ok", "sum"), ok100=("ok100", "sum")).reset_index().merge(causes, on=keys)
    cell = pop_cells[keys + ["N"]].merge(cell, on=keys, how="left").fillna({"n": 0, "ok": 0, "ok100": 0})
    proj = []
    for by in (None, "act_class", "area_class", "hemisphere", "cohort"):
        groups = [("all", m)] if by is None else [(f"{by}={v}", g) for v, g in m.groupby(by)]
        for name, g in groups:
            w = g.w1.to_numpy(float)
            proj.append(dict(group=name, n=len(g), ok=int(g.ok.sum()), sample_yield=float(g.ok.mean()),
                             projected_yield=float((w * g.ok).sum() / w.sum()), projected_yield_100=float((w * g.ok100).sum() / w.sum()),
                             population_weight=float(w.sum())))
    return cell, pd.DataFrame(proj), m


def q1_quiet(rec):
    sides = pd.concat([rec[["noaa", "day", f"{s}_status", f"{s}_mad_g"]].rename(columns={f"{s}_status": "status", f"{s}_mad_g": "mad"}).assign(side=s)
                       for s in ("qm", "qp")])
    avail = sides.status.fillna("not_attempted").value_counts().rename_axis("status").reset_index(name="n_sides")
    v = rec.quiet_mad_g.dropna()
    summ = dict(sides_total=int(len(sides)), sides_ok=int((sides.status == "ok").sum()), groups_with_value=int(v.size),
                groups_total=int(len(rec)), median_g=float(v.median()) if len(v) else None,
                p10_g=float(v.quantile(0.1)) if len(v) else None, p90_g=float(v.quantile(0.9)) if len(v) else None,
                note="observed field dispersion (scaled MAD), not instrumental noise")
    return avail, summ


def q1_m_fit(ok_rec, A=None):
    """Exploratory covariance fit: procedure M on gamma with a Joy model per cycle x hemisphere; only the variance
    parameters and boundary flags are returned (no coefficient, SE or interval)."""
    if A is None:
        spec = importlib.util.spec_from_file_location("t3_mwo_analysis", ROOT / "scripts/t3_mwo_analysis.py")
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    d = ok_rec.copy()
    d["hemisphere"] = np.where(d.main_lat_bar >= 0, "N", "S")
    d["sinlat"] = np.sin(np.radians(np.abs(d.main_lat_bar)))
    d["cycle"] = [cycle_of(x) for x in d.day]
    d["CR"] = d.N.astype(int)
    d["phi_mwo"] = d.main_flux_pos_mx + d.main_flux_neg_mx
    gamma = tw.joy_gamma(d.main_tilt_deg.to_numpy(float), d.main_lat_bar.to_numpy(float))
    s, cyc, hem = d.sinlat.to_numpy(), d.cycle.to_numpy(), d.hemisphere.to_numpy()
    cols = [s * ((cyc == c) & (hem == h)) for c in sorted(set(cyc)) for h in ("N", "S") if ((cyc == c) & (hem == h)).any()]
    Z = np.column_stack(cols)
    w = d.phi_mwo.to_numpy(float)
    keep, cur = [], np.zeros((len(d), 0))
    for j in range(Z.shape[1]):
        t = np.column_stack([cur, Z[:, j]])
        if np.linalg.matrix_rank(t * np.sqrt(w)[:, None]) > cur.shape[1]:
            keep.append(j)
            cur = t
    Xr = Z[:, keep]
    codes, uniq = A.cell_codes(d.reset_index(drop=True))
    g = A.g_row(Xr, w)                                       # target: one Joy coefficient (nuisance; not saved)
    r = A.m_verdict(A.m_unit(d, Xr, w, g, gamma, codes, uniq), 0.0)
    out = {k: r.get(k) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2", "error")}
    out.update(n=int(len(d)), cells=int(len(uniq)), rotations=int(d.CR.nunique()), cr_min=int(d.CR.min()), cr_max=int(d.CR.max()),
               phi_at_bound=bool(out.get("phi") is not None and np.isfinite(out["phi"]) and (out["phi"] <= 1e-9 or out["phi"] >= 0.98 - 1e-9)),
               kappa_at_bound=bool(out.get("kappa") is not None and np.isfinite(out["kappa"]) and abs(out["kappa"]) >= 0.98 - 1e-9),
               note="exploratory; little informative by construction (sparse sample); not a measurement of the "
                    "correlation between rotations; no coefficient, SE or interval saved")
    return out


# ---------------------------------------------------------------- Q3

def tercile_edges(x):
    return np.quantile(np.asarray(x, float), [1 / 3, 2 / 3])


def tercile_class(x, e):
    return np.searchsorted(e, np.asarray(x, float), side="right") + 1


def q3_pairs(rec, samp, mwo, tag="main"):
    """M1 pairs with the level-1 measurement ok at threshold `tag`; classes are attached before the differences."""
    ok_all = rec[rec[f"{tag}_status"] == "ok"]
    sep_edges = tercile_edges(ok_all[f"{tag}_sep_deg"])                  # fixed before any difference
    m = samp[samp.cohort == "M1"].merge(rec, on=["noaa", "day"], validate="one_to_one")
    m = m[m[f"{tag}_status"] == "ok"].merge(mwo, left_on=["noaa", "day"], right_on=["noaa", "day_utc"], how="left", validate="one_to_one")
    if m.tilt_deg.isna().any():
        raise ValueError("M1 pair without an MWO record on the same day")
    m["sep_class"] = tercile_class(m[f"{tag}_sep_deg"], sep_edges)
    lcm_edges = tercile_edges(m.lcm.abs())
    m["lcm_class"] = tercile_class(m.lcm.abs(), lcm_edges)
    t1, t2 = m[f"{tag}_tilt_deg"].to_numpy(float), m.tilt_deg.to_numpy(float)
    m["d_raw"], m["d_dir"], m["d_ax"] = tw.diff_raw(t1, t2), tw.diff_dir(t1, t2), tw.diff_ax(t1, t2)
    m["d_gamma"] = tw.d_gamma(t1, t2, m.lat.to_numpy(float))
    m["leading_agree"] = m[f"{tag}_leading_sign"].astype(int) == m.leading_polarity_sign.astype(int)
    m["flux_ratio"] = (m[f"{tag}_flux_pos_mx"] + m[f"{tag}_flux_neg_mx"]) / m.flux_window_mx
    m["dt_mwo_minus_tcm_h"] = (pd.to_datetime(m.mwo_time_utc) - pd.to_datetime(m.t_cm)).dt.total_seconds() / 3600.0
    return m, dict(sep_edges=[float(x) for x in sep_edges], lcm_edges=[float(x) for x in lcm_edges])


def stats(x):
    return (float(np.nanmedian(x.d_ax)) if len(x) else np.nan, float(np.nanmedian(x.d_gamma)) if x.d_gamma.notna().any() else np.nan,
            float(x.leading_agree.mean()) if len(x) else np.nan)


def bootstrap_table(pairs, groups, reps=REPS, seed=SEED):
    """Common block draws on the pairs (blocks of 6 rotations, both hemispheres together), groups applied after."""
    n0 = int(pairs.N.min())
    blk = ((pairs.N.astype(int) - n0) // BLOCK).to_numpy()
    labels = np.unique(blk)
    members = [np.flatnonzero(blk == b) for b in labels]
    rng = np.random.default_rng(seed)
    draws = [np.concatenate([members[i] for i in rng.integers(0, len(labels), len(labels))]) for _ in range(reps)]
    rows = []
    for name, mask in groups:
        x = pairs[mask]
        nb = int(len(np.unique(blk[mask.to_numpy()]))) if len(x) else 0
        med_ax, med_g, agree = stats(x)
        row = dict(group=name, n_pairs=int(len(x)), n_blocks=nb, median_d_ax=med_ax, median_d_gamma=med_g, leading_agree=agree,
                   median_flux_ratio=float(x.flux_ratio.median()) if len(x) else np.nan,
                   median_abs_dt_h=float(x.dt_mwo_minus_tcm_h.abs().median()) if len(x) else np.nan)
        if len(x) < MIN_PAIRS:
            row["interval_note"] = f"fewer than {MIN_PAIRS} pairs: n and medians only"
        elif nb < MIN_BLOCKS:
            row["interval_note"] = "non valutabile (fewer than 3 blocks)"
        else:
            mm = mask.to_numpy()
            b = np.array([stats(pairs.iloc[d[mm[d]]]) if mm[d].any() else (np.nan, np.nan, np.nan) for d in draws])
            valid = np.isfinite(b[:, 0])
            row["valid_reps"] = int(valid.sum())
            if valid.sum() >= MIN_VALID:
                for j, k in enumerate(("d_ax", "d_gamma", "agree")):
                    vv = b[valid, j]
                    vv = vv[np.isfinite(vv)]
                    row[f"{k}_lo"], row[f"{k}_hi"] = (np.quantile(vv, [0.025, 0.975]) if len(vv) >= MIN_VALID else (np.nan, np.nan))
                row["interval_note"] = ""
            else:
                row["interval_note"] = f"fewer than {MIN_VALID} valid replicates"
        rows.append(row)
    return pd.DataFrame(rows)


def q3_groups(p):
    g = [("all", pd.Series(True, index=p.index))]
    for col, lab in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation"), ("lcm_class", "abs_LCM")):
        g += [(f"{lab} {k}", p[col] == k) for k in (1, 2, 3)]
    g += [(f"hemisphere {h}", p.hemisphere == h) for h in ("N", "S")]
    return g


# ---------------------------------------------------------------- run

def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    s_ok, s_meta = products_ok(SEL, {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"})
    l_ok, l_meta = products_ok(L1, {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"})
    if not (s_ok and l_ok and strict_receipt(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json")
            and strict_receipt(L1_REC / "RECEIPT.json", "l1_meta_sha256", L1 / "META.json")
            and l_meta.get("selection_meta_sha256") == sha(SEL / "META.json") and s_meta.get("protocol_sha256") == fr["sha256"]):
        sys.exit("upstream products, receipts or links not verified")
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    cells = pd.read_csv(SEL / "CELLS.csv")
    rec = pd.read_csv(L1 / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
    mwo = pd.read_csv(RELEASE, dtype={"noaa": str}, float_precision="round_trip",
                      usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"])
    prods = build(rec, samp, cells, mwo)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        write(prods, tmp)
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"),
                    selection_meta_sha256=sha(SEL / "META.json"), l1_meta_sha256=sha(L1 / "META.json"),
                    selection_receipt_sha256=sha(SEL_REC / "RECEIPT.json"), l1_receipt_sha256=sha(L1_REC / "RECEIPT.json"),
                    release_sha256=sha(RELEASE), seed=SEED, reps=REPS,
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(f"written {out}")
    return 0


def build(rec, samp, cells, mwo, reps=REPS, A=None):
    cell, proj, merged = q1_yield(rec, samp, cells)
    avail, quiet_summ = q1_quiet(rec)
    ok_rec = rec.merge(samp[["noaa", "day"]], on=["noaa", "day"])
    ok_rec = ok_rec[ok_rec.main_status == "ok"].reset_index(drop=True)
    mfit = q1_m_fit(ok_rec, A)
    out = dict(Q1_YIELD_CELLS=cell, Q1_YIELD_PROJECTED=proj, Q1_QUIET_AVAILABILITY=avail,
               Q1_QUIET_SUMMARY=quiet_summ, Q1_M_EXPLORATORY=mfit, CLASS_EDGES={})
    for tag in ("main", "sens100"):
        pairs, edges = q3_pairs(rec, samp.drop(columns=[c for c in ("status",) if c in samp]), mwo, tag)
        out[f"Q3_PAIRS_{tag}"] = pairs[["noaa", "day", "N", "hemisphere", "act_class", "area_class", "sep_class", "lcm_class", "lat",
                                        f"{tag}_tilt_deg", "tilt_deg", "d_raw", "d_dir", "d_ax", "d_gamma", f"{tag}_leading_sign",
                                        "leading_polarity_sign", "leading_agree", "flux_ratio", "dt_mwo_minus_tcm_h"]]
        out[f"Q3_SUMMARY_{tag}"] = bootstrap_table(pairs, q3_groups(pairs), reps)
        out["CLASS_EDGES"][tag] = edges
    return out


def write(prods, folder):
    for k, v in prods.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(Path(folder) / f"{k}.csv", index=False)
        else:
            (Path(folder) / f"{k}.json").write_text(json.dumps(v, indent=2, default=float) + "\n")


# ---------------------------------------------------------------- selftest (synthetic)

def synthetic(n=200, seed=4):
    rng = np.random.default_rng(seed)
    day = pd.date_range("1999-01-01", periods=n, freq="7D").strftime("%Y-%m-%d")
    samp = pd.DataFrame(dict(noaa=[str(9000 + i) for i in range(n)], day=day, lat=rng.choice([-1, 1], n) * rng.uniform(3, 30, n),
                             lcm=rng.uniform(-20, 20, n), act_class=rng.integers(1, 4, n), area_class=rng.integers(1, 4, n),
                             cohort=np.where(np.arange(n) % 2 == 0, "M1", "U")))
    samp["hemisphere"] = np.where(samp.lat >= 0, "N", "S")
    samp["w1"] = rng.uniform(1, 20, n)
    status = np.where(np.arange(n) % 17 == 0, "map_missing", np.where(np.arange(n) % 13 == 0, "no_two_polarities", "ok"))
    rec = pd.DataFrame(dict(noaa=samp.noaa, day=day, N=1950 + np.arange(n) // 4, t_cm=day, status=status, main_status=status,
                            sens100_status=np.where(np.arange(n) % 5 == 0, "polarity_below_min_pixels", status)))
    tilt = np.where(samp.lat >= 0, 1, -1) * rng.normal(8, 15, n) % 360
    tilt = (tilt + 180) % 360 - 180
    for tag in ("main", "sens100"):
        okm = rec[f"{tag}_status"] == "ok"
        rec[f"{tag}_tilt_deg"] = np.where(okm, tilt, np.nan)
        rec[f"{tag}_lat_bar"] = np.where(okm, samp.lat + rng.normal(0, 0.3, n), np.nan)
        rec[f"{tag}_sep_deg"] = np.where(okm, rng.uniform(2, 10, n), np.nan)
        rec[f"{tag}_leading_sign"] = np.where(okm, 1, np.nan)
        rec[f"{tag}_flux_pos_mx"] = np.where(okm, 10 ** rng.uniform(20, 22, n), np.nan)
        rec[f"{tag}_flux_neg_mx"] = rec[f"{tag}_flux_pos_mx"]
    for s in ("qm", "qp"):
        rec[f"{s}_status"] = np.where(np.arange(n) % 3 == 0, "dpd_group_inside", "ok")
        rec[f"{s}_mad_g"] = np.where(rec[f"{s}_status"] == "ok", rng.uniform(3, 8, n), np.nan)
    rec["quiet_mad_g"] = rec[["qm_mad_g", "qp_mad_g"]].mean(axis=1)
    m1 = samp.cohort == "M1"
    mwo = pd.DataFrame(dict(noaa=samp.noaa[m1], day_utc=samp.day[m1], mwo_time_utc=samp.day[m1] + "T18:00:00",
                            tilt_deg=(tilt[m1] + rng.normal(0, 5, m1.sum()) + 180) % 360 - 180, leading_polarity_sign=1,
                            flux_window_mx=10 ** rng.uniform(20, 22, m1.sum())))
    cells = samp.groupby(["act_class", "hemisphere", "area_class", "cohort"]).size().reset_index(name="N")
    return rec, samp, cells, mwo


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    rec, samp, cells, mwo = synthetic()
    cell, proj, merged = q1_yield(rec, samp, cells)
    ok("Q1: cells keep n, ok and one cause_ column per status (no name collision)", {"n", "ok", "ok100"} <= set(cell.columns)
       and all(c.startswith("cause_") for c in cell.columns if c not in ("act_class", "hemisphere", "area_class", "cohort", "N", "n", "ok", "ok100")))
    ok("Q1: every sampled group in the denominator, map_missing (empty measurement columns) included",
       proj[proj.group == "all"].n.iloc[0] == len(samp) and (merged.status == "map_missing").sum() == (rec.status == "map_missing").sum())
    w, okk = samp.w1.to_numpy(), (rec.status == "ok").to_numpy()
    ok("Q1: projected yield = sum(w1 ok) / sum(w1)", abs(proj[proj.group == "all"].projected_yield.iloc[0] - (w * okk).sum() / w.sum()) < 1e-12)
    avail, qs = q1_quiet(rec)
    ok("Q1: quiet availability counts both sides and their causes", qs["sides_total"] == 2 * len(rec)
       and int(avail.n_sides.sum()) == 2 * len(rec) and qs["sides_ok"] == int((rec.qm_status == "ok").sum() + (rec.qp_status == "ok").sum()))
    pairs, edges = q3_pairs(rec, samp, mwo)
    ok("Q3: only cohort M1 with main ok, joined to MWO on the same day", set(pairs.noaa) <= set(samp.noaa[samp.cohort == "M1"])
       and len(pairs) == int(((samp.cohort == "M1") & (rec.status == "ok")).sum()))
    sep_ok = rec[rec.main_status == "ok"].main_sep_deg
    ok("Q3: separation edges from all level-1 successful measurements (fixed before the differences)",
       np.allclose(edges["sep_edges"], np.quantile(sep_ok, [1 / 3, 2 / 3])))
    ok("Q3: d_ax, d_gamma with the DPD latitude, MDI - MWO order", np.allclose(pairs.d_ax, tw.diff_ax(pairs.main_tilt_deg, pairs.tilt_deg))
       and np.allclose(pairs.d_gamma, np.sign(pairs.lat) * pairs.d_ax))
    samp0 = samp.copy()
    samp0.loc[samp0.index[0], "lat"] = 0.0
    p0, _ = q3_pairs(rec, samp0, mwo)
    ok("Q3: d_gamma undefined (NaN, not zero) at lat_DPD = 0", np.isnan(p0[p0.noaa == samp0.noaa.iloc[0]].d_gamma).all())
    tab = bootstrap_table(pairs, q3_groups(pairs), reps=200)
    small = tab[tab.n_pairs < MIN_PAIRS]
    ok("bootstrap: < 10 pairs -> n and medians only", (small.interval_note.str.startswith("fewer than 10")).all())
    big = tab[(tab.n_pairs >= MIN_PAIRS) & (tab.n_blocks >= MIN_BLOCKS)]
    ok("bootstrap: with 200 replicates no interval (needs >= 1900 valid)", (big.interval_note.str.contains("valid replicates")).all())
    tab2 = bootstrap_table(pairs, q3_groups(pairs), reps=2000)
    t2 = bootstrap_table(pairs, q3_groups(pairs), reps=2000)
    ok("bootstrap: reproducible from the seed, intervals present for the full group", tab2.equals(t2)
       and np.isfinite(tab2[tab2.group == "all"].d_ax_lo.iloc[0]))
    one = pairs.assign(N=1950)
    t3 = bootstrap_table(one, [("all", pd.Series(True, index=one.index))], reps=50)
    ok("bootstrap: fewer than 3 blocks -> interval non valutabile", t3.interval_note.iloc[0].startswith("non valutabile"))
    spec = importlib.util.spec_from_file_location("t3a", ROOT / "scripts/t3_mwo_analysis.py")
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    okr = rec.merge(samp[["noaa", "day"]], on=["noaa", "day"])
    mf = q1_m_fit(okr[okr.main_status == "ok"].reset_index(drop=True).assign(N=lambda x: x.N), A)
    ok("Q1: exploratory M fit returns only covariance parameters (no beta, SE or interval)",
       not any(k in mf for k in ("beta", "se", "lo", "hi", "verdict")) and "phi" in mf, {k: mf[k] for k in ("n", "cells", "phi")})
    ok("Q1: boundary flag set when phi = 0 (lower bound)", mf["phi_at_bound"] == (mf["phi"] <= 1e-9 or mf["phi"] >= 0.98 - 1e-9))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
