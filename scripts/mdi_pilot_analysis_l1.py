"""MDI pilot, phase 6 (level-1 part): descriptive Q1 and Q3 (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §5).

Q1 - yield on all sampled groups (denominator = sample; failures incl. map_missing stay in it), per cell x cohort with
     one cause_<status> column per status, projected on the eligible population with w1 = 1/pi1 (ratio estimator),
     main and 100 G; quiet-window availability (both sides, causes) and summary of the observed field dispersion
     (scaled MAD; not instrumental noise); exploratory M covariance fit on gamma with a Joy model per cycle x
     hemisphere (variance parameters, state, domain and boundary flags only; no coefficient, SE or interval).
Q3 - cohort M1 only (MWO isolated record on the chosen day), measurement ok: relative differences MDI(synoptic) - MWO,
     no instrument assumed correct. Separation classes: terciles of the separations of the successful MAIN level-1
     measurements (all cohorts), fixed once before any difference and reused at 100 G (and later for full-disk).
     Time: MWO instant - t_DPD (protocol); CT_g and T_ROT kept because the synoptic instant is undetermined; the
     distance to the estimated central-meridian passage t_cm is supplementary and approximate. MDI fluxes, counts,
     areas and separation are exported; MWO counts/areas per polarity are not in the release (not computable).
     Bootstrap: blocks floor((N - N_min)/6) on the pairs, 2000 replicates, seed 71 100 001, groups all / activity /
     area / separation / hemisphere; percentiles only with >= 1900 valid replicates; < 10 pairs -> n and medians
     only; < 3 blocks -> 'non valutabile'. No |LCM| classes (not fixed by the protocol). BARD-MDI deferred.

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
M_MODULES = ("scripts/t3_mwo_analysis.py", "python/sharpbl/p2d.py", "python/sharpbl/p2f_pilot.py", "python/sharpbl/p2f_validation.py")
OUT = ROOT / "results/MDI_PILOT_ANALYSIS_L1"
SEED, REPS, MIN_VALID, MIN_PAIRS, MIN_BLOCKS, BLOCK = 71_100_001, 2000, 1900, 10, 3, 6
MINIMA = [(21, "1976-03-01"), (22, "1986-09-01"), (23, "1996-08-01"), (24, "2008-12-01")]
TAGS = ("main", "sens100")
KEYS = ["act_class", "hemisphere", "area_class", "cohort"]
PAIR_COLS = ["noaa", "day", "N", "hemisphere", "act_class", "area_class", "sep_class", "lat", "t_dpd", "mwo_time_utc",
             "dt_mwo_minus_tdpd_h", "CT_g", "t_rot", "t_cm", "dt_mwo_minus_tcm_h_approx", "mdi_tilt_deg", "mwo_tilt_deg",
             "d_raw", "d_dir", "d_ax", "d_gamma", "mdi_leading_sign", "mwo_leading_sign", "leading_agree",
             "mdi_flux_pos_mx", "mdi_flux_neg_mx", "mdi_flux_mx", "mwo_flux_mx", "flux_ratio", "mdi_npos", "mdi_nneg",
             "mdi_area_pos_msh", "mdi_area_neg_msh", "mdi_sep_deg"]
SUMMARY_COLS = ["group", "n_pairs", "n_blocks", "median_d_ax", "median_d_gamma", "leading_agree", "median_flux_ratio",
                "median_abs_dt_dpd_h", "valid_reps", "d_ax_lo", "d_ax_hi", "d_gamma_lo", "d_gamma_hi", "agree_lo", "agree_hi",
                "interval_note"]
NOTES = dict(bard_mdi="deferred: BARD has no NOAA number and the frozen protocol fixes no matching rule; a separate "
                      "note is required before any matching",
             mwo_pixel_area_ratios="not computable: the MWO release has no pixel counts or areas per polarity",
             synoptic_time="the synoptic instant per pixel is undetermined; MWO - t_DPD is the protocol distance; "
                           "MWO - t_cm (estimated central-meridian passage) is supplementary and approximate",
             abs_lcm_classes="omitted: not fixed by the frozen protocol",
             quiet="scaled MAD = observed field dispersion (solar field, noise and processing), not instrumental noise")


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


def upstream_problems():
    probs = []
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        probs.append("frozen protocol changed")
    s_ok, sm = products_ok(SEL, {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"})
    l_ok, lm = products_ok(L1, {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"})
    if not s_ok:
        probs.append("selection products differ from META")
    if not l_ok:
        probs.append("L1 products differ from META")
    if not strict_receipt(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json"):
        probs.append("selection receipt")
    if not strict_receipt(L1_REC / "RECEIPT.json", "l1_meta_sha256", L1 / "META.json"):
        probs.append("L1 receipt")
    if lm.get("selection_meta_sha256") != sha(SEL / "META.json"):
        probs.append("L1 not linked to the current selection")
    if sm.get("protocol_sha256") != fr["sha256"] or lm.get("protocol_sha256") != fr["sha256"]:
        probs.append("selection or L1 made under another protocol")
    if sm.get("mwo_release_sha256") != sha(RELEASE):
        probs.append("MWO release differs from the one used by the selection")
    return probs


def cycle_of(day):
    c = 20
    for k, m in MINIMA:
        if pd.Timestamp(day) >= pd.Timestamp(m):
            c = k
    return c


# ---------------------------------------------------------------- Q1

def q1_yield(rec, samp, cells):
    m = samp.merge(rec[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left", validate="one_to_one")
    if m.status.isna().any():
        raise ValueError("sampled group without a level-1 record")
    m["ok"], m["ok100"] = m.status == "ok", m.sens100_status == "ok"
    statuses = sorted(m.status.unique())
    agg = m.groupby(KEYS).agg(n=("ok", "size"), ok=("ok", "sum"), ok100=("ok100", "sum")).reset_index()
    cause = pd.crosstab([m[k] for k in KEYS], m.status).reindex(columns=statuses, fill_value=0).add_prefix("cause_").reset_index()
    tab = cells[KEYS + ["N"]].merge(agg, on=KEYS, how="left").merge(cause, on=KEYS, how="left")
    cnt = ["n", "ok", "ok100"] + [f"cause_{s}" for s in statuses]
    tab = tab.fillna({c: 0 for c in cnt})
    for c in cnt:
        tab[c] = tab[c].astype(int)
    proj = []
    for by in (None, "act_class", "area_class", "hemisphere", "cohort"):
        for name, g in ([("all", m)] if by is None else [(f"{by}={v}", g) for v, g in m.groupby(by)]):
            w = g.w1.to_numpy(float)
            proj.append(dict(group=name, n=len(g), ok=int(g.ok.sum()), ok100=int(g.ok100.sum()), sample_yield=float(g.ok.mean()),
                             sample_yield_100=float(g.ok100.mean()), projected_yield=float((w * g.ok).sum() / w.sum()),
                             projected_yield_100=float((w * g.ok100).sum() / w.sum()), population_weight=float(w.sum())))
    return tab, pd.DataFrame(proj)


def q1_quiet(rec):
    sides = pd.concat([rec[f"{s}_status"] for s in ("qm", "qp")]).fillna("not_attempted")
    avail = sides.value_counts().sort_index().rename_axis("status").reset_index(name="n_sides")
    v = rec.quiet_mad_g.dropna()
    q = lambda p: float(v.quantile(p)) if len(v) else None              # noqa: E731
    return avail, dict(sides_total=int(len(sides)), sides_ok=int((sides == "ok").sum()), groups_total=int(len(rec)),
                       groups_with_value=int(v.size), median_g=q(0.5), p10_g=q(0.1), p90_g=q(0.9), note=NOTES["quiet"])


def q1_m_fit(rec, samp, A):
    d = rec.merge(samp[["noaa", "day"]], on=["noaa", "day"])
    d = d[d.main_status == "ok"].reset_index(drop=True)
    d["hemisphere"] = np.where(d.main_lat_bar >= 0, "N", "S")
    d["CR"] = d.N.astype(int)
    d["phi_mwo"] = d.main_flux_pos_mx + d.main_flux_neg_mx
    s = np.sin(np.radians(np.abs(d.main_lat_bar.to_numpy(float))))
    cyc, hem = np.array([cycle_of(x) for x in d.day]), d.hemisphere.to_numpy()
    w = d.phi_mwo.to_numpy(float)
    X = np.zeros((len(d), 0))
    for c in sorted(set(cyc)):
        for h in ("N", "S"):
            col = s * ((cyc == c) & (hem == h))
            if col.any():
                t = np.column_stack([X, col])
                if np.linalg.matrix_rank(t * np.sqrt(w)[:, None]) > X.shape[1]:
                    X = t
    gamma = tw.joy_gamma(d.main_tilt_deg.to_numpy(float), d.main_lat_bar.to_numpy(float))
    codes, uniq = A.cell_codes(d)
    r = A.m_verdict(A.m_unit(d, X, w, A.g_row(X, w), gamma, codes, uniq), 0.0)
    out = {k: r.get(k) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2")}
    out["error"] = r.get("error")
    out["state"] = "errore di M" if r.get("verdict") == "errore" else "stimato"
    fin = all(out[k] is not None and np.isfinite(out[k]) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2"))
    out["finite"] = bool(fin)
    out["in_domain"] = bool(fin and 0.0 <= out["phi"] <= 0.98 and abs(out["kappa"]) <= 0.98 and out["sigma_x2"] > 0)
    out["phi_at_bound"] = bool(fin and (out["phi"] <= 1e-9 or out["phi"] >= 0.98 - 1e-9))
    out["kappa_at_bound"] = bool(fin and abs(out["kappa"]) >= 0.98 - 1e-9)
    out.update(n=int(len(d)), cells=int(len(uniq)), rotations=int(d.CR.nunique()), cr_min=int(d.CR.min()), cr_max=int(d.CR.max()),
               note="exploratory, little informative by construction; not a measurement of the correlation between "
                    "rotations; no coefficient, SE or interval saved")
    return out


# ---------------------------------------------------------------- Q3

def separation_edges(rec):
    """Terciles of the separations of the successful MAIN level-1 measurements (all cohorts); fixed once."""
    return np.quantile(rec.loc[rec.main_status == "ok", "main_sep_deg"].to_numpy(float), [1 / 3, 2 / 3])


def q3_pairs(rec, samp, mwo, tag, sep_edges):
    m = samp[samp.cohort == "M1"].merge(rec, on=["noaa", "day"], validate="one_to_one")
    m = m[m[f"{tag}_status"] == "ok"].merge(mwo, left_on=["noaa", "day"], right_on=["noaa", "day_utc"], how="left", validate="one_to_one")
    if m.tilt_deg.isna().any():
        raise ValueError("M1 pair without an MWO record on the same day")
    t1, t2 = m[f"{tag}_tilt_deg"].to_numpy(float), m.tilt_deg.to_numpy(float)
    p = pd.DataFrame(dict(noaa=m.noaa, day=m.day, N=m.N.astype(int), hemisphere=m.hemisphere, act_class=m.act_class,
                          area_class=m.area_class, sep_class=np.searchsorted(sep_edges, m[f"{tag}_sep_deg"].to_numpy(float), side="right") + 1,
                          lat=m.lat, t_dpd=m.t_dpd, mwo_time_utc=m.mwo_time_utc,
                          dt_mwo_minus_tdpd_h=(pd.to_datetime(m.mwo_time_utc, format="ISO8601") - pd.to_datetime(m.t_dpd, format="ISO8601")).dt.total_seconds() / 3600.0,
                          CT_g=m.CT_g, t_rot=m.t_rot, t_cm=m.t_cm,
                          dt_mwo_minus_tcm_h_approx=(pd.to_datetime(m.mwo_time_utc, format="ISO8601") - pd.to_datetime(m.t_cm, format="ISO8601")).dt.total_seconds() / 3600.0,
                          mdi_tilt_deg=t1, mwo_tilt_deg=t2, d_raw=tw.diff_raw(t1, t2), d_dir=tw.diff_dir(t1, t2), d_ax=tw.diff_ax(t1, t2),
                          d_gamma=tw.d_gamma(t1, t2, m.lat.to_numpy(float)), mdi_leading_sign=m[f"{tag}_leading_sign"].astype(int),
                          mwo_leading_sign=m.leading_polarity_sign.astype(int)))
    p["leading_agree"] = p.mdi_leading_sign == p.mwo_leading_sign
    p["mdi_flux_pos_mx"], p["mdi_flux_neg_mx"] = m[f"{tag}_flux_pos_mx"].to_numpy(), m[f"{tag}_flux_neg_mx"].to_numpy()
    p["mdi_flux_mx"] = p.mdi_flux_pos_mx + p.mdi_flux_neg_mx
    p["mwo_flux_mx"] = m.flux_window_mx.to_numpy()
    p["flux_ratio"] = p.mdi_flux_mx / p.mwo_flux_mx
    for a, b in (("mdi_npos", "npos"), ("mdi_nneg", "nneg"), ("mdi_area_pos_msh", "area_pos_msh"), ("mdi_area_neg_msh", "area_neg_msh"), ("mdi_sep_deg", "sep_deg")):
        p[a] = m[f"{tag}_{b}"].to_numpy()
    return p[PAIR_COLS].reset_index(drop=True)


def groups_of(p):
    g = [("all", np.ones(len(p), bool))]
    for col, lab in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation")):
        g += [(f"{lab} {k}", (p[col] == k).to_numpy()) for k in (1, 2, 3)]
    return g + [(f"hemisphere {h}", (p.hemisphere == h).to_numpy()) for h in ("N", "S")]


def _stats(x):
    return (np.nanmedian(x.d_ax) if len(x) else np.nan,
            np.nanmedian(x.d_gamma) if len(x) and x.d_gamma.notna().any() else np.nan,
            x.leading_agree.mean() if len(x) else np.nan)


def bootstrap_table(p, reps=REPS, seed=SEED):
    blk = ((p.N.astype(int) - int(p.N.min())) // BLOCK).to_numpy() if len(p) else np.zeros(0, int)
    labels = np.unique(blk)
    members = [np.flatnonzero(blk == b) for b in labels]
    rng = np.random.default_rng(seed)
    draws = [np.concatenate([members[i] for i in rng.integers(0, len(labels), len(labels))]) for _ in range(reps)] if len(labels) else []
    rows = []
    for name, mk in groups_of(p):
        x = p[mk]
        a, g, ag = _stats(x)
        row = dict(group=name, n_pairs=int(len(x)), n_blocks=int(len(np.unique(blk[mk]))) if len(x) else 0, median_d_ax=a,
                   median_d_gamma=g, leading_agree=ag, median_flux_ratio=float(x.flux_ratio.median()) if len(x) else np.nan,
                   median_abs_dt_dpd_h=float(x.dt_mwo_minus_tdpd_h.abs().median()) if len(x) else np.nan, valid_reps=np.nan,
                   d_ax_lo=np.nan, d_ax_hi=np.nan, d_gamma_lo=np.nan, d_gamma_hi=np.nan, agree_lo=np.nan, agree_hi=np.nan)
        if len(x) < MIN_PAIRS:
            row["interval_note"] = f"fewer than {MIN_PAIRS} pairs: n and medians only"
        elif row["n_blocks"] < MIN_BLOCKS:
            row["interval_note"] = "non valutabile (fewer than 3 blocks)"
        else:
            b = np.array([_stats(p.iloc[d[mk[d]]]) if mk[d].any() else (np.nan,) * 3 for d in draws])
            valid = np.isfinite(b[:, 0])
            row["valid_reps"] = int(valid.sum())
            if valid.sum() >= MIN_VALID:
                for j, k in enumerate(("d_ax", "d_gamma", "agree")):
                    vv = b[valid, j]
                    vv = vv[np.isfinite(vv)]
                    if len(vv) >= MIN_VALID:
                        row[f"{k}_lo"], row[f"{k}_hi"] = np.quantile(vv, [0.025, 0.975])
                row["interval_note"] = ""
            else:
                row["interval_note"] = f"fewer than {MIN_VALID} valid replicates"
        rows.append(row)
    return pd.DataFrame(rows)[SUMMARY_COLS]


# ---------------------------------------------------------------- build, write, run

def build(rec, samp, cells, mwo, A, reps=REPS):
    cell, proj = q1_yield(rec, samp, cells)
    avail, quiet = q1_quiet(rec)
    edges = separation_edges(rec)
    out = dict(Q1_YIELD_CELLS=cell, Q1_YIELD_PROJECTED=proj, Q1_QUIET_AVAILABILITY=avail, Q1_QUIET_SUMMARY=quiet,
               Q1_M_EXPLORATORY=q1_m_fit(rec, samp, A), CLASS_EDGES=dict(separation_main_l1_ok=[float(x) for x in edges]), NOTES=NOTES)
    for tag in TAGS:
        p = q3_pairs(rec, samp, mwo, tag, edges)
        out[f"Q3_PAIRS_{tag}"], out[f"Q3_SUMMARY_{tag}"] = p, bootstrap_table(p, reps)
    return out


def write(prods, folder):
    for k, v in prods.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(Path(folder) / f"{k}.csv", index=False)
        else:
            (Path(folder) / f"{k}.json").write_text(json.dumps(v, indent=2) + "\n")


def load_inputs():
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    cells = pd.read_csv(SEL / "CELLS.csv")
    rec = pd.read_csv(L1 / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
    mwo = pd.read_csv(RELEASE, dtype={"noaa": str}, float_precision="round_trip",
                      usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"])
    return rec, samp, cells, mwo


def load_m():
    spec = importlib.util.spec_from_file_location("t3_mwo_analysis", ROOT / "scripts/t3_mwo_analysis.py")
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    probs = upstream_problems()
    if probs:
        sys.exit("upstream not verified: " + "; ".join(probs))
    prods = build(*load_inputs(), load_m())
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        write(prods, tmp)
        fr = json.loads(FREEZE.read_text())
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"),
                    m_modules_sha256={p: sha(ROOT / p) for p in M_MODULES}, selection_meta_sha256=sha(SEL / "META.json"),
                    l1_meta_sha256=sha(L1 / "META.json"), selection_receipt_sha256=sha(SEL_REC / "RECEIPT.json"),
                    l1_receipt_sha256=sha(L1_REC / "RECEIPT.json"), release_sha256=sha(RELEASE), seed=SEED, reps=REPS,
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(f"written {out}")
    return 0


# ---------------------------------------------------------------- selftest (synthetic)

def synthetic(n=200, seed=4):
    rng = np.random.default_rng(seed)
    day = pd.date_range("1999-01-01", periods=n, freq="7D").strftime("%Y-%m-%d")
    samp = pd.DataFrame(dict(noaa=[str(9000 + i) for i in range(n)], day=day, t_dpd=[d + " 08:00:00" for d in day],
                             lat=rng.choice([-1, 1], n) * rng.uniform(3, 30, n), lcm=rng.uniform(-20, 20, n),
                             act_class=rng.integers(1, 4, n), area_class=rng.integers(1, 4, n),
                             cohort=np.where(np.arange(n) % 2 == 0, "M1", "U")))
    samp["hemisphere"] = np.where(samp.lat >= 0, "N", "S")
    samp["w1"] = rng.uniform(1, 20, n)
    st = np.where(np.arange(n) % 17 == 0, "map_missing", np.where(np.arange(n) % 13 == 0, "no_two_polarities", "ok"))
    rec = pd.DataFrame(dict(noaa=samp.noaa, day=day, N=1950 + np.arange(n) // 4, CT_g=1e5 + np.arange(n), t_rot="x",
                            t_cm=[d + " 12:00:00" for d in day], status=st, main_status=st,
                            sens100_status=np.where(np.arange(n) % 5 == 0, "polarity_below_min_pixels", st)))
    tilt = (np.where(samp.lat >= 0, 1, -1) * rng.normal(8, 15, n) + 180) % 360 - 180
    for tag in TAGS:
        okm = rec[f"{tag}_status"] == "ok"
        nan = lambda v: np.where(okm, v, np.nan)                      # noqa: E731
        rec[f"{tag}_tilt_deg"], rec[f"{tag}_lat_bar"] = nan(tilt), nan(samp.lat + rng.normal(0, 0.3, n))
        rec[f"{tag}_sep_deg"], rec[f"{tag}_leading_sign"] = nan(rng.uniform(2, 10, n)), nan(1.0)
        rec[f"{tag}_flux_pos_mx"] = nan(10 ** rng.uniform(20, 22, n))
        rec[f"{tag}_flux_neg_mx"] = rec[f"{tag}_flux_pos_mx"]
        rec[f"{tag}_npos"], rec[f"{tag}_nneg"] = nan(rng.integers(10, 300, n)), nan(rng.integers(10, 300, n))
        rec[f"{tag}_area_pos_msh"], rec[f"{tag}_area_neg_msh"] = nan(rng.uniform(5, 200, n)), nan(rng.uniform(5, 200, n))
    for s in ("qm", "qp"):
        rec[f"{s}_status"] = np.where(np.arange(n) % 3 == 0, "dpd_group_inside", np.where(st == "map_missing", None, "ok"))
        rec[f"{s}_mad_g"] = np.where(rec[f"{s}_status"] == "ok", rng.uniform(3, 8, n), np.nan)
    rec["quiet_mad_g"] = rec[["qm_mad_g", "qp_mad_g"]].mean(axis=1)
    m1 = samp.cohort == "M1"
    mwo = pd.DataFrame(dict(noaa=samp.noaa[m1], day_utc=samp.day[m1], mwo_time_utc=samp.day[m1] + "T18:00:00",
                            tilt_deg=(tilt[m1] + rng.normal(0, 5, m1.sum()) + 180) % 360 - 180, leading_polarity_sign=1,
                            flux_window_mx=10 ** rng.uniform(20, 22, m1.sum())))
    mwo.loc[mwo.index[::2], "mwo_time_utc"] += ".125"  # mixed ISO precision, as in real MWO metadata
    cells = samp.groupby(KEYS).size().reset_index(name="N")
    return rec, samp, cells, mwo


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    rec, samp, cells, mwo = synthetic()
    A = load_m()
    pr = build(rec, samp, cells, mwo, A, reps=200)
    proj, cell = pr["Q1_YIELD_PROJECTED"], pr["Q1_YIELD_CELLS"]
    ok("Q1: every sampled group in the denominator, map_missing included", proj[proj.group == "all"].n.iloc[0] == len(samp)
       and int(cell.cause_map_missing.sum()) == int((rec.status == "map_missing").sum()))
    w, okk = samp.w1.to_numpy(), (rec.status == "ok").to_numpy()
    ok("Q1: projected yield = sum(w1 ok) / sum(w1)", abs(proj[proj.group == "all"].projected_yield.iloc[0] - (w * okk).sum() / w.sum()) < 1e-12)
    ok("Q1: one cause_ column per status, no collision with the counts", {"n", "ok", "ok100"} <= set(cell.columns)
       and sorted(c for c in cell.columns if c.startswith("cause_")) == sorted(f"cause_{s}" for s in set(rec.status)))
    ok("Q1: quiet availability counts both sides, not attempted included", pr["Q1_QUIET_SUMMARY"]["sides_total"] == 2 * len(rec)
       and "not_attempted" in set(pr["Q1_QUIET_AVAILABILITY"].status))
    e = pr["CLASS_EDGES"]["separation_main_l1_ok"]
    ok("Q3: one set of separation edges from the main successful measurements, reused at 100 G",
       np.allclose(e, np.quantile(rec[rec.main_status == "ok"].main_sep_deg, [1 / 3, 2 / 3]))
       and (pr["Q3_PAIRS_sens100"].sep_class.to_numpy() == np.searchsorted(e, pr["Q3_PAIRS_sens100"].mdi_sep_deg, side="right") + 1).all())
    p = pr["Q3_PAIRS_main"]
    ok("Q3: M1 only, MDI - MWO, d_gamma with the DPD latitude", set(p.noaa) <= set(samp.noaa[samp.cohort == "M1"])
       and np.allclose(p.d_ax, tw.diff_ax(p.mdi_tilt_deg, p.mwo_tilt_deg)) and np.allclose(p.d_gamma, np.sign(p.lat) * p.d_ax))
    ok("Q3: time distance MWO - t_DPD (protocol) and MWO - t_cm (supplementary)",
       np.allclose(p.dt_mwo_minus_tdpd_h, 10.0) and np.allclose(p.dt_mwo_minus_tcm_h_approx, 6.0))
    expected_dt = (p.mwo_time_utc.map(pd.Timestamp) - p.t_dpd.map(pd.Timestamp)).dt.total_seconds() / 3600.0
    ok("Q3: mixed integer/fractional ISO timestamps preserve exact time distances",
       mwo.mwo_time_utc.str.contains(r"\.", regex=True).any()
       and (~mwo.mwo_time_utc.str.contains(r"\.", regex=True)).any()
       and np.allclose(p.dt_mwo_minus_tdpd_h, expected_dt, rtol=0, atol=1e-12))
    ok("Q3: no |LCM| classes", not any("LCM" in g for g in pr["Q3_SUMMARY_main"].group))
    s0 = samp.copy()
    s0.loc[s0.index[0], "lat"] = 0.0
    p0 = q3_pairs(rec, s0, mwo, "main", np.array(e))
    ok("Q3: d_gamma undefined (NaN) at lat_DPD = 0", np.isnan(p0[p0.noaa == s0.noaa.iloc[0]].d_gamma).all())
    t = pr["Q3_SUMMARY_main"]
    ok("bootstrap: < 10 pairs -> medians only; 200 replicates -> no interval", (t[t.n_pairs < 10].interval_note.str.startswith("fewer than 10")).all()
       and (t[(t.n_pairs >= 10) & (t.n_blocks >= 3)].interval_note.str.contains("valid replicates")).all())
    t2 = bootstrap_table(p, 2000)
    ok("bootstrap: 2000 replicates reproducible, interval for the full group", t2.equals(bootstrap_table(p, 2000))
       and np.isfinite(t2[t2.group == "all"].d_ax_lo.iloc[0]))
    ok("bootstrap: fewer than 3 blocks -> non valutabile", bootstrap_table(p.assign(N=1950), 30).interval_note.iloc[0].startswith("non valutabile"))
    mf = pr["Q1_M_EXPLORATORY"]
    ok("Q1: M exploratory keeps state, finiteness, domain and flags; no coefficient", not any(k in mf for k in ("beta", "se", "lo", "hi", "verdict"))
       and all(k in mf for k in ("state", "finite", "in_domain", "phi_at_bound", "kappa_at_bound"))
       and mf["phi_at_bound"] == (mf["phi"] <= 1e-9 or mf["phi"] >= 0.98 - 1e-9))
    ok("notes: BARD deferred, MWO pixel/area ratios not computable", "deferred" in pr["NOTES"]["bard_mdi"] and "not computable" in pr["NOTES"]["mwo_pixel_area_ratios"])
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
