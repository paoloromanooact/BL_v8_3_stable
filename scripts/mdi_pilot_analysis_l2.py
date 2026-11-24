"""MDI pilot, phase 6 (level-2 part): descriptive analyses of the full-disk measurement (frozen protocol
docs/PROTOCOL_MDI_TILT_PILOT.md §4-5 and frozen amendment A1). Everything is descriptive; no instrument is assumed correct.

For each assignment (A1 {0, 0x200} main; original {0} secondary, with its own A/B assignments and two supplementary files)
and each threshold (main 50 G, sens100 100 G):
  YIELD   - denominator = the 90 level-2 groups for image A and for image B; one cause_<status> column per status;
            projected yield on the eligible population with w2 = 1/pi2 (ratio estimator); losses by year and by INTERVAL
            of A (30 s, 300 s, unknown, no A) and by QUALITY of A, as required by §4 and A1.
  QUIET   - side statuses of the measured images; the scaled MAD is observed field dispersion, not instrumental noise;
            without a valid side the value is 'non disponibile' (never zero) and does not invalidate a tilt.
  Q2      - synoptic (level 1) - fd(A); time: T_OBS(A) - t_DPD (the synoptic instant per pixel is undetermined; CT_g
            and T_ROT kept).
  REPEAT  - A - B on the pairs with the same numeric INTERVAL (no pair when INTERVAL is unknown); Delta t = T_OBS(B) -
            T_OBS(A) from the plan; QUALITY transitions kept and reported as a group, not excluded.
  Q3FD    - fd(A) - MWO, cohort M1 (MWO isolated record on the chosen day); time: MWO - t_DPD (protocol) and
            MWO - T_OBS(A) = MWO - (t_DPD + A_dt_h). MWO pixel and area ratios are not computable (not in the release).
Differences d_raw, d_dir, d_ax, d_gamma = sign(lat_DPD) d_ax (undefined at lat_DPD = 0); ratios = first / second member
of each comparison. Separation classes: the terciles of the successful MAIN level-1 synoptic separations (equal to the
preserved level-1 analysis CLASS_EDGES), applied identically to every comparison and to both thresholds, to the
separation of the first (MDI) member. Groups: all, activity, area, separation, hemisphere, QUALITY of A, INTERVAL of A
(and QUALITY transition for REPEAT); an empty group gives n = 0 and the note 'no pairs'.
Bootstrap as level 1: blocks floor((N - N_min)/6) on the pairs of the comparison (N = level-1 Carrington rotation),
2000 replicates, seed 71 100 001; percentiles only with >= 1900 valid replicates; < 10 pairs -> n and medians only;
< 3 blocks -> 'non valutabile'. Comparisons are unweighted (sample pairs); only the yields use w2.

    .venv/bin/python scripts/mdi_pilot_analysis_l2.py --selftest
    .venv/bin/python scripts/mdi_pilot_analysis_l2.py --run         # after the code review
"""
import argparse
import hashlib
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

PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
L1, L1_REC = ROOT / "results/MDI_PILOT_L1", ROOT / "results/MDI_PILOT_L1_RECOUNT"
AN1, AN1_REC = ROOT / "results/MDI_PILOT_ANALYSIS_L1", ROOT / "results/MDI_PILOT_ANALYSIS_L1_RECOUNT"
L2, L2_REC = ROOT / "results/MDI_PILOT_L2", ROOT / "results/MDI_PILOT_L2_RECOUNT"
PLAN, PLAN_REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1", ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
OUT = ROOT / "results/MDI_PILOT_ANALYSIS_L2"
SEED, REPS, MIN_VALID, MIN_PAIRS, MIN_BLOCKS, BLOCK = 71_100_001, 2000, 1900, 10, 3, 6
TAGS, RULES = ("main", "sens100"), ("A1", "original")
KEYS = ["act_class", "hemisphere", "area_class", "cohort"]
Q0, Q200 = "0x00000000", "0x00000200"
STATUSES = ("ok", "no_magnetogram", "no_image", "not_determined", "fits_missing", "window_outside_mu_domain", "window_off_disk",
            "window_empty", "window_missing", "no_two_polarities", "polarity_below_min_pixels", "quality_not_zero",
            "quality_not_admissible", "quality_missing", "quality_unparsable", "geometry_keywords_unparsable")
SUMMARY_COLS = ["group", "n_pairs", "n_blocks", "median_d_ax", "median_d_gamma", "leading_agree", "median_flux_ratio",
                "median_pix_ratio", "median_area_ratio", "median_abs_dt_h", "valid_reps", "d_ax_lo", "d_ax_hi", "d_gamma_lo",
                "d_gamma_hi", "agree_lo", "agree_hi", "interval_note"]
YIELD_COLS = ["image", "group", "n", "ok", "ok100", "sample_yield", "sample_yield_100", "projected_yield", "projected_yield_100",
              "population_weight"] + [f"cause_{s}" for s in STATUSES]
NOTES = dict(
    comparisons="descriptive relative differences; no instrument or product is assumed correct",
    order="Q2 = synoptic - fd(A); REPEAT = A - B; Q3FD = fd(A) - MWO; ratios = first / second member",
    q2_time="T_OBS(A) - t_DPD; the synoptic instant per pixel is undetermined (CT_g and T_ROT kept)",
    q3fd_time="MWO - t_DPD (protocol) and MWO - T_OBS(A); the summary median uses |MWO - T_OBS(A)|",
    repeat_time="T_OBS(B) - T_OBS(A) from the plan; it includes real evolution and possibly correlated errors, not separated",
    repeat_interval="pairs only with the same numeric INTERVAL; an unknown INTERVAL forms no pair",
    quality_transitions="pairs with different QUALITY at the same INTERVAL are kept and reported as a group (A1)",
    mwo_pixel_area_ratios="not computable: the MWO release has no pixel counts or areas per polarity",
    quiet="scaled MAD = observed field dispersion (solar field, noise and processing), not instrumental noise; without "
          "a valid side the value is 'non disponibile', never zero, and it does not invalidate a tilt",
    separation="terciles of the successful main level-1 synoptic separations, applied to the MDI member of every comparison",
    weights="yields projected with w2 = 1/pi2; comparisons unweighted",
    original_rule="secondary table with the original A/B assignments (QUALITY {0}); not a filter of the A1 assignments")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strict_receipt(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    ch = r.get("checks")
    return (type(r.get("passed")) is int and type(r.get("total")) is int and r["total"] > 0 and r["passed"] == r["total"]
            and isinstance(ch, list) and len(ch) == r["total"] and all(isinstance(c, dict) and c.get("ok") is True for c in ch)
            and r.get("partial") is False and r.get(key) == sha(meta))


# Expected upstream product sets, fixed here and never taken from the manifests under check.
SEL_PRODUCTS = frozenset({"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"})
L1_PRODUCTS = frozenset({"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"})
AN1_PRODUCTS = frozenset({"CLASS_EDGES.json", "NOTES.json", "Q1_M_EXPLORATORY.json", "Q1_QUIET_AVAILABILITY.csv", "Q1_QUIET_SUMMARY.json",
                          "Q1_YIELD_CELLS.csv", "Q1_YIELD_PROJECTED.csv", "Q3_PAIRS_main.csv", "Q3_PAIRS_sens100.csv",
                          "Q3_SUMMARY_main.csv", "Q3_SUMMARY_sens100.csv"})
PLAN_PRODUCTS = frozenset({"CHOICES_A1.csv", "CHOICES_ORIGINAL.csv", "PLAN.csv", "COVERAGE.csv"})
L2_PRODUCTS = frozenset({"L2_RECORDS.csv"})


def products_ok(folder, names):
    m = json.loads((Path(folder) / "META.json").read_text())
    ps = m["products_sha256"]
    return isinstance(ps, dict) and set(ps) == set(names) and len(names) > 0 and all(sha(Path(folder) / n) == h for n, h in ps.items()), m


def upstream_problems():
    """Names of the failed upstream contracts: products (fixed expected sets and actual hashes), strict receipts,
    frozen protocol and A1 named by every stage that records them, and the links between stages (L1 -> selection and
    its receipt; level-1 analysis -> selection, L1, their receipts and the MWO release; L2 -> selection, plan and the
    plan's metadata)."""
    probs = []

    def need(name, f):
        try:
            good = bool(f())
        except (OSError, ValueError, KeyError, TypeError):
            good = False
        if not good:
            probs.append(name)

    fr, fz = json.loads(FREEZE.read_text()), json.loads(A1_FREEZE.read_text())
    P, A = fr["sha256"], fz["sha256"]
    meta = lambda d: json.loads((d / "META.json").read_text())             # noqa: E731
    msha, rsha = (lambda d: sha(d / "META.json")), (lambda d: sha(d / "RECEIPT.json"))
    need("protocol and A1 texts", lambda: sha(PROTOCOL) == P == fz["parent_sha256"] and sha(A1) == A)
    need("selection", lambda: products_ok(SEL, SEL_PRODUCTS)[0]
         and strict_receipt(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json")
         and meta(SEL)["protocol_sha256"] == P)
    need("level 1", lambda: products_ok(L1, L1_PRODUCTS)[0]
         and strict_receipt(L1_REC / "RECEIPT.json", "l1_meta_sha256", L1 / "META.json")
         and meta(L1)["protocol_sha256"] == P
         and meta(L1)["selection_meta_sha256"] == msha(SEL) and meta(L1)["selection_receipt_sha256"] == rsha(SEL_REC))
    need("level-1 analysis (separation edges)", lambda: products_ok(AN1, AN1_PRODUCTS)[0]
         and strict_receipt(AN1_REC / "RECEIPT.json", "analysis_meta_sha256", AN1 / "META.json")
         and meta(AN1)["protocol_sha256"] == P
         and meta(AN1)["selection_meta_sha256"] == msha(SEL) and meta(AN1)["l1_meta_sha256"] == msha(L1)
         and meta(AN1)["selection_receipt_sha256"] == rsha(SEL_REC) and meta(AN1)["l1_receipt_sha256"] == rsha(L1_REC)
         and meta(AN1)["release_sha256"] == sha(RELEASE))
    need("plan", lambda: products_ok(PLAN, PLAN_PRODUCTS)[0]
         and strict_receipt(PLAN_REC / "RECEIPT.json", "plan_meta_sha256", PLAN / "META.json")
         and meta(PLAN)["protocol_sha256"] == P and meta(PLAN)["a1_sha256"] == A)
    need("level 2", lambda: products_ok(L2, L2_PRODUCTS)[0]
         and strict_receipt(L2_REC / "RECEIPT.json", "l2_meta_sha256", L2 / "META.json")
         and meta(L2)["protocol_sha256"] == P and meta(L2)["a1_sha256"] == A
         and meta(L2)["plan_meta_sha256"] == msha(PLAN) and meta(L2)["selection_meta_sha256"] == msha(SEL)
         and meta(L2)["metadata_meta_sha256"] == meta(PLAN)["metadata_meta_sha256"])
    need("MWO release used by the selection", lambda: meta(SEL)["mwo_release_sha256"] == sha(RELEASE))
    return probs


# ---------------------------------------------------------------- inputs per rule

def interval_label(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "unknown"
    return f"{x:g} s" if np.isfinite(x) else "unknown"


def group_frame(samp, l1, l2, choices, rule):
    """One row per level-2 group: sample columns, L1 synoptic values (prefix syn_), A and B full-disk values (prefixes
    A_, B_) of the rule, plan fields (A quality and interval, Delta t, pair Delta t, QUALITY transition)."""
    g = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    l1 = l1.rename(columns={c: f"syn_{c}" for c in l1.columns if c not in ("noaa", "day")})
    g = g.merge(l1, on=["noaa", "day"], how="left", validate="one_to_one")
    ch = choices[rule][["noaa", "day", "status", "A_quality", "A_interval", "A_dt_h", "B_dt_h", "pair_dt_min", "pair_status",
                        "quality_transition"]].rename(columns={"status": "choice_status", "A_quality": "plan_A_quality",
                                                               "A_interval": "plan_A_interval", "A_dt_h": "plan_A_dt_h", "B_dt_h": "plan_B_dt_h"})
    g = g.merge(ch, on=["noaa", "day"], how="left", validate="one_to_one")
    for img in ("A", "B"):
        x = l2[(l2.rule == rule) & (l2.image == img)].drop(columns=["rule", "image"])
        x = x.rename(columns={c: f"{img}_{c}" for c in x.columns if c not in ("noaa", "day")})
        g = g.merge(x, on=["noaa", "day"], how="left", validate="one_to_one")
    if g.syn_N.isna().any() or g.choice_status.isna().any() or g.A_status.isna().any() or g.B_status.isna().any():
        raise ValueError("level-2 group without its level-1 record, plan choice or level-2 rows")
    g["year"] = g.day.str[:4]
    g["interval_A"] = np.where(g.choice_status == "ok", [interval_label(v) for v in g.plan_A_interval], "no A")
    g["quality_A"] = np.where(g.choice_status == "ok", g.plan_A_quality.astype(str), "no A")
    return g


# ---------------------------------------------------------------- yield and quiet

def yield_table(g):
    rows = []
    for img in ("A", "B"):
        st, st100 = g[f"{img}_status"], g.get(f"{img}_sens100_status")
        ok, ok100 = (st == "ok").to_numpy(), (st100 == "ok").to_numpy() if st100 is not None else np.zeros(len(g), bool)
        unknown = sorted(set(st) - set(STATUSES))
        if unknown:
            raise ValueError(f"status not in the declared list: {unknown}")
        parts = [("all", np.ones(len(g), bool))]
        for col, lab in (("act_class", "activity"), ("area_class", "area"), ("hemisphere", "hemisphere"), ("cohort", "cohort"),
                         ("year", "year"), ("interval_A", "interval_A"), ("quality_A", "quality_A")):
            parts += [(f"{lab}={v}", (g[col].astype(str) == v).to_numpy()) for v in sorted(g[col].astype(str).unique())]
        w = g.w2.to_numpy(float)
        for name, mk in parts:
            r = dict(image=img, group=name, n=int(mk.sum()), ok=int(ok[mk].sum()), ok100=int(ok100[mk].sum()),
                     sample_yield=float(ok[mk].mean()), sample_yield_100=float(ok100[mk].mean()),
                     projected_yield=float((w[mk] * ok[mk]).sum() / w[mk].sum()),
                     projected_yield_100=float((w[mk] * ok100[mk]).sum() / w[mk].sum()), population_weight=float(w[mk].sum()))
            r.update({f"cause_{s}": int((st[mk] == s).sum()) for s in STATUSES})
            rows.append(r)
    return pd.DataFrame(rows)[YIELD_COLS]


def quiet_tables(g):
    sides, vals = [], []
    for img in ("A", "B"):
        m = g[g[f"{img}_file"].notna()]
        for s in ("qm", "qp"):
            sides += list(m[f"{img}_{s}_status"].fillna("not_attempted"))
        vals += list(m[f"{img}_quiet_mad_g"].dropna())
    sv = pd.Series(sides, dtype=object)
    av = sv.value_counts().sort_index()
    avail = pd.DataFrame(dict(status=list(av.index), n_sides=[int(x) for x in av.to_numpy()]))
    v = np.asarray(vals, float)
    na = "non disponibile"
    summ = dict(images_measured=int(len(sides) // 2), sides_total=int(len(sides)), sides_ok=int((sv == "ok").sum()),
                images_with_value=int(len(v)), median_g=float(np.quantile(v, 0.5)) if len(v) else na,
                p10_g=float(np.quantile(v, 0.1)) if len(v) else na, p90_g=float(np.quantile(v, 0.9)) if len(v) else na,
                note=NOTES["quiet"])
    return avail, summ


# ---------------------------------------------------------------- comparisons

PAIR_BASE = ["noaa", "day", "N", "hemisphere", "act_class", "area_class", "cohort", "sep_class", "lat", "t_dpd", "quality_A", "interval_A"]
PAIR_COMMON = ["t1_deg", "t2_deg", "d_raw", "d_dir", "d_ax", "d_gamma", "lead1", "lead2", "leading_agree", "flux1_mx", "flux2_mx",
               "flux_ratio", "pix1", "pix2", "pix_ratio", "area1_msh", "area2_msh", "area_ratio", "sep1_deg", "abs_dt_h"]
EXTRA = dict(Q2=["A_T_REC", "dt_A_minus_tdpd_h", "CT_g", "t_rot"],
             REPEAT=["A_T_REC", "B_T_REC", "A_quality_rec", "B_quality_rec", "quality_transition", "pair_dt_min"],
             Q3FD=["A_T_REC", "mwo_time_utc", "dt_mwo_minus_tdpd_h", "dt_mwo_minus_tobsA_h"])


def _member(g, pre, tag):
    """(tilt, leading, flux, pixels, area, separation) of one MDI member; pre = 'syn_' or 'A_' or 'B_'."""
    f = lambda k: g[f"{pre}{tag}_{k}"].to_numpy(float)           # noqa: E731
    return (f("tilt_deg"), f("leading_sign"), f("flux_pos_mx") + f("flux_neg_mx"), f("npos") + f("nneg"),
            f("area_pos_msh") + f("area_neg_msh"), f("sep_deg"))


def pairs(g, kind, tag, edges, mwo=None):
    if kind == "Q2":
        m = g[(g[f"syn_{tag}_status"] == "ok") & (g[f"A_{tag}_status"] == "ok")].reset_index(drop=True)
        one, two = _member(m, "syn_", tag), _member(m, "A_", tag)
    elif kind == "REPEAT":
        m = g[(g[f"A_{tag}_status"] == "ok") & (g[f"B_{tag}_status"] == "ok")].reset_index(drop=True)
        one, two = _member(m, "A_", tag), _member(m, "B_", tag)
    else:
        m = g[(g.cohort == "M1") & (g[f"A_{tag}_status"] == "ok")].merge(
            mwo, left_on=["noaa", "day"], right_on=["noaa", "day_utc"], how="left", validate="one_to_one").reset_index(drop=True)
        if m.tilt_deg.isna().any():
            raise ValueError("M1 pair without an MWO record on the same day")
        one = _member(m, "A_", tag)
        nan = np.full(len(m), np.nan)
        two = (m.tilt_deg.to_numpy(float), m.leading_polarity_sign.to_numpy(float), m.flux_window_mx.to_numpy(float), nan, nan, nan)
    t1, t2 = one[0], two[0]
    p = pd.DataFrame({k: m[k].to_numpy() for k in ("noaa", "day", "hemisphere", "act_class", "area_class", "cohort", "lat", "t_dpd",
                                                   "quality_A", "interval_A")})
    p.insert(2, "N", m.syn_N.astype(int).to_numpy())
    p.insert(7, "sep_class", np.searchsorted(edges, one[5], side="right") + 1)
    p["t1_deg"], p["t2_deg"] = t1, t2
    p["d_raw"], p["d_dir"], p["d_ax"] = tw.diff_raw(t1, t2), tw.diff_dir(t1, t2), tw.diff_ax(t1, t2)
    p["d_gamma"] = tw.d_gamma(t1, t2, m.lat.to_numpy(float))
    p["lead1"], p["lead2"] = one[1].astype(int), two[1].astype(int)
    p["leading_agree"] = p.lead1 == p.lead2
    p["flux1_mx"], p["flux2_mx"], p["flux_ratio"] = one[2], two[2], one[2] / two[2]
    p["pix1"], p["pix2"], p["pix_ratio"] = one[3], two[3], one[3] / two[3]
    p["area1_msh"], p["area2_msh"], p["area_ratio"] = one[4], two[4], one[4] / two[4]
    p["sep1_deg"] = one[5]
    if kind == "Q2":
        p["A_T_REC"], p["dt_A_minus_tdpd_h"], p["CT_g"], p["t_rot"] = m.A_T_REC.to_numpy(), m.plan_A_dt_h.to_numpy(float), m.syn_CT_g.to_numpy(), m.syn_t_rot.to_numpy()
        p["abs_dt_h"] = np.abs(p.dt_A_minus_tdpd_h)
    elif kind == "REPEAT":
        p["A_T_REC"], p["B_T_REC"], p["A_quality_rec"], p["B_quality_rec"] = m.A_T_REC.to_numpy(), m.B_T_REC.to_numpy(), m.A_quality.to_numpy(), m.B_quality.to_numpy()
        p["quality_transition"] = m.quality_transition.astype(str).str.lower().eq("true").to_numpy()
        p["pair_dt_min"] = m.pair_dt_min.to_numpy(float)
        p["abs_dt_h"] = np.abs(p.pair_dt_min) / 60.0
    else:
        hours = lambda a, b: (pd.to_datetime(a, format="ISO8601") - pd.to_datetime(b, format="ISO8601")).dt.total_seconds().to_numpy() / 3600.0  # noqa: E731
        p["A_T_REC"], p["mwo_time_utc"] = m.A_T_REC.to_numpy(), m.mwo_time_utc.to_numpy()
        p["dt_mwo_minus_tdpd_h"] = hours(m.mwo_time_utc, m.t_dpd)
        p["dt_mwo_minus_tobsA_h"] = p.dt_mwo_minus_tdpd_h - m.plan_A_dt_h.to_numpy(float)
        p["abs_dt_h"] = np.abs(p.dt_mwo_minus_tobsA_h)
    return p[PAIR_BASE + PAIR_COMMON + EXTRA[kind]].reset_index(drop=True)


def groups_of(p, kind):
    gs = [("all", np.ones(len(p), bool))]
    for col, lab in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation")):
        gs += [(f"{lab} {k}", (p[col] == k).to_numpy()) for k in (1, 2, 3)]
    gs += [(f"hemisphere {h}", (p.hemisphere == h).to_numpy()) for h in ("N", "S")]
    gs += [(f"quality_A {q}", (p.quality_A == q).to_numpy()) for q in (Q0, Q200)]
    gs += [(f"interval_A {i}", (p.interval_A == i).to_numpy()) for i in ("30 s", "300 s", "unknown")]
    if kind == "REPEAT":
        gs += [(f"quality_transition {v}", (p.quality_transition == v).to_numpy()) for v in (False, True)]
    return gs


def _stats(x):
    return (np.nanmedian(x.d_ax) if len(x) else np.nan,
            np.nanmedian(x.d_gamma) if len(x) and x.d_gamma.notna().any() else np.nan,
            x.leading_agree.mean() if len(x) else np.nan)


def _med(s):
    s = s.dropna()
    return float(s.median()) if len(s) else np.nan


def summary(p, kind, reps=REPS, seed=SEED):
    blk = ((p.N.astype(int) - int(p.N.min())) // BLOCK).to_numpy() if len(p) else np.zeros(0, int)
    labels = np.unique(blk)
    members = [np.flatnonzero(blk == b) for b in labels]
    rng = np.random.default_rng(seed)
    draws = [np.concatenate([members[i] for i in rng.integers(0, len(labels), len(labels))]) for _ in range(reps)] if len(labels) else []
    rows = []
    for name, mk in groups_of(p, kind):
        x = p[mk]
        a, gm, ag = _stats(x)
        row = dict(group=name, n_pairs=int(len(x)), n_blocks=int(len(np.unique(blk[mk]))) if len(x) else 0, median_d_ax=a,
                   median_d_gamma=gm, leading_agree=ag, median_flux_ratio=_med(x.flux_ratio), median_pix_ratio=_med(x.pix_ratio),
                   median_area_ratio=_med(x.area_ratio), median_abs_dt_h=_med(x.abs_dt_h), valid_reps=np.nan, d_ax_lo=np.nan,
                   d_ax_hi=np.nan, d_gamma_lo=np.nan, d_gamma_hi=np.nan, agree_lo=np.nan, agree_hi=np.nan)
        if len(x) == 0:
            row["interval_note"] = "no pairs"
        elif len(x) < MIN_PAIRS:
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


def separation_edges(l1):
    return np.quantile(l1.loc[l1.main_status == "ok", "main_sep_deg"].to_numpy(float), [1 / 3, 2 / 3])


def build(samp, l1, l2, choices, mwo, reps=REPS):
    edges = separation_edges(l1)
    out = dict(CLASS_EDGES=dict(separation_main_l1_ok=[float(x) for x in edges]), NOTES=NOTES)
    for rule in RULES:
        g = group_frame(samp, l1, l2, choices, rule)
        out[f"YIELD_{rule}"] = yield_table(g)
        out[f"QUIET_AVAILABILITY_{rule}"], out[f"QUIET_SUMMARY_{rule}"] = quiet_tables(g)
        for kind in ("Q2", "REPEAT", "Q3FD"):
            for tag in TAGS:
                p = pairs(g, kind, tag, edges, mwo)
                out[f"{kind}_PAIRS_{rule}_{tag}"], out[f"{kind}_SUMMARY_{rule}_{tag}"] = p, summary(p, kind, reps)
    return out


# ---------------------------------------------------------------- write, run

def write(prods, folder):
    for k, v in prods.items():
        if isinstance(v, pd.DataFrame):
            v.to_csv(Path(folder) / f"{k}.csv", index=False)
        else:
            (Path(folder) / f"{k}.json").write_text(json.dumps(v, indent=2) + "\n")


def load_inputs():
    rd = lambda p, **k: pd.read_csv(p, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip", **k)  # noqa: E731
    samp, l1, l2 = rd(SEL / "SAMPLE.csv"), rd(L1 / "L1_RECORDS.csv"), rd(L2 / "L2_RECORDS.csv")
    choices = {"A1": rd(PLAN / "CHOICES_A1.csv"), "original": rd(PLAN / "CHOICES_ORIGINAL.csv")}
    mwo = rd(RELEASE, usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"])
    return samp, l1, l2, choices, mwo


def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    probs = upstream_problems()
    if probs:
        sys.exit("upstream not verified: " + "; ".join(probs))
    samp, l1, l2, choices, mwo = load_inputs()
    edges = separation_edges(l1)
    edges_bytes = (AN1 / "CLASS_EDGES.json").read_bytes()
    edges_sha = hashlib.sha256(edges_bytes).hexdigest()
    if edges_sha != json.loads((AN1 / "META.json").read_text())["products_sha256"]["CLASS_EDGES.json"]:
        sys.exit("CLASS_EDGES.json differs from the preserved level-1 analysis manifest")
    an1 = json.loads(edges_bytes)["separation_main_l1_ok"]
    if not np.allclose(edges, an1, rtol=0, atol=1e-12):
        sys.exit("separation edges differ from the preserved level-1 analysis")
    prods = build(samp, l1, l2, choices, mwo)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        write(prods, tmp)
        fr, fz = json.loads(FREEZE.read_text()), json.loads(A1_FREEZE.read_text())
        meta = dict(protocol_sha256=fr["sha256"], a1_sha256=fz["sha256"], script_sha256=sha(__file__),
                    module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"), selection_meta_sha256=sha(SEL / "META.json"),
                    l1_meta_sha256=sha(L1 / "META.json"), analysis_l1_meta_sha256=sha(AN1 / "META.json"),
                    analysis_l1_class_edges_sha256=edges_sha,
                    plan_meta_sha256=sha(PLAN / "META.json"), l2_meta_sha256=sha(L2 / "META.json"),
                    receipts_sha256={n: sha(d / "RECEIPT.json") for n, d in (("selection", SEL_REC), ("l1", L1_REC), ("analysis_l1", AN1_REC),
                                                                             ("plan", PLAN_REC), ("l2", L2_REC))},
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


# ---------------------------------------------------------------- synthetic data (also used by the recount)

MEAS = ("npos", "nneg", "flux_pos_mx", "flux_neg_mx", "area_pos_msh", "area_neg_msh", "leading_sign", "tilt_deg", "sep_deg")


def synthetic(n=90, seed=7):
    """Level-2 sample, level-1 records, level-2 rows for both rules, plan choices and MWO records with known
    relations: fd(A) = synoptic + 2 deg, B = A - 1 deg, MWO = A - 3 deg (before wrapping); every structure the
    analysis meets (no magnetogram, no B, unknown INTERVAL, QUALITY transition, mu losses) is present."""
    rng = np.random.default_rng(seed)
    day = pd.date_range("1997-01-01", periods=n, freq="29D").strftime("%Y-%m-%d")
    lat = rng.choice([-1, 1], n) * rng.uniform(3, 30, n)
    samp = pd.DataFrame(dict(noaa=[str(8000 + i) for i in range(n)], day=day, t_dpd=[d + " 08:00:00" for d in day], lat=lat,
                             lon=rng.uniform(0, 360, n), act_class=rng.integers(1, 4, n), area_class=rng.integers(1, 4, n),
                             cohort=np.where(np.arange(n) % 3 == 0, "U", "M1"), level2=True))
    samp["hemisphere"] = np.where(lat >= 0, "N", "S")
    samp["pi2"] = rng.uniform(0.01, 0.3, n)
    samp["w2"] = 1 / samp.pi2
    extra = samp.iloc[:5].assign(noaa=[str(7000 + i) for i in range(5)], level2=False)       # level-1 only groups
    samp = pd.concat([samp, extra], ignore_index=True)
    base = (np.where(lat >= 0, 1, -1) * rng.normal(8, 15, n) + 180) % 360 - 180
    st1 = np.where(np.arange(n) % 23 == 5, "window_missing", "ok")
    l1 = pd.DataFrame(dict(noaa=samp.noaa[:n], day=day, N=1915 + np.arange(n) // 3, CT_g=1e5 + np.arange(n), t_rot="x",
                           status=st1, main_status=st1, sens100_status=np.where(np.arange(n) % 7 == 0, "polarity_below_min_pixels", st1)))
    l1 = pd.concat([l1, pd.DataFrame(dict(noaa=extra.noaa, day=extra.day, N=1900, CT_g=0.0, t_rot="x", status="ok", main_status="ok",
                                          sens100_status="ok"))], ignore_index=True)

    def fill(df, pre, tilt, okm):
        for tag in TAGS:
            o = okm & (df[f"{pre}{tag}_status"].to_numpy() == "ok")
            v = lambda x: np.where(o, x, np.nan)                       # noqa: E731
            df[f"{pre}{tag}_tilt_deg"], df[f"{pre}{tag}_leading_sign"] = v((tilt + 180) % 360 - 180), v(np.where(np.arange(len(df)) % 11 == 0, -1.0, 1.0))
            df[f"{pre}{tag}_flux_pos_mx"] = df[f"{pre}{tag}_flux_neg_mx"] = v(10 ** rng.uniform(20, 22, len(df)))
            df[f"{pre}{tag}_npos"], df[f"{pre}{tag}_nneg"] = v(rng.integers(10, 300, len(df)).astype(float)), v(rng.integers(10, 300, len(df)).astype(float))
            df[f"{pre}{tag}_area_pos_msh"], df[f"{pre}{tag}_area_neg_msh"] = v(rng.uniform(5, 200, len(df))), v(rng.uniform(5, 200, len(df)))
            df[f"{pre}{tag}_sep_deg"] = v(rng.uniform(2, 10, len(df)))

    fill(l1, "", np.concatenate([base, np.zeros(5)]), np.ones(len(l1), bool))
    l1["main_sep_deg"] = np.where(l1.main_status == "ok", l1.main_sep_deg, np.nan)
    i = np.arange(n)
    ch_status = np.where(i % 10 == 9, "no_magnetogram", "ok")
    interval = np.where(i % 4 == 0, 300.0, np.where(i % 17 == 3, np.nan, 30.0))
    qa = np.where(i % 5 == 0, Q0, Q200)
    has_b = (ch_status == "ok") & np.isfinite(interval) & (i % 13 != 1)
    qb = np.where(i % 29 == 2, Q0 if False else np.where(qa == Q0, Q200, Q0), qa)
    a_dt = rng.uniform(-2, 1, n)
    pair_dt = np.where(has_b, rng.choice([-96.0, 96.0], n), np.nan)
    ch = pd.DataFrame(dict(noaa=samp.noaa[:n], day=day, status=ch_status, A=[f"T{k}A" for k in i], A_quality=np.where(ch_status == "ok", qa, None),
                           A_interval=np.where(ch_status == "ok", interval, np.nan), A_dt_h=np.where(ch_status == "ok", a_dt, np.nan),
                           B_dt_h=np.where(has_b, a_dt + pair_dt / 60, np.nan), pair_dt_min=pair_dt,
                           pair_status=np.where(has_b, np.where(pair_dt > 0, "after", "before"), "no_pair"),
                           quality_transition=has_b & (qb != qa)))
    ch.loc[ch.status != "ok", "A"] = None
    orig = ch.copy()
    keep = qa == Q0
    orig.loc[~keep, ["status", "A", "A_quality", "A_interval", "A_dt_h", "B_dt_h", "pair_dt_min", "quality_transition"]] = \
        ["no_magnetogram", None, None, np.nan, np.nan, np.nan, np.nan, False]
    orig.loc[~keep, "pair_status"] = "no_pair"
    rows = []
    for rule, c in (("A1", ch), ("original", orig)):
        for img in ("A", "B"):
            for k, r in enumerate(c.itertuples()):
                st = r.status if r.status != "ok" else ("ok" if img == "A" or np.isfinite(r.pair_dt_min) else "no_image")
                if st == "ok" and k % 9 == 4:
                    st = "window_outside_mu_domain"
                q = r.A_quality if img == "A" else (qb[k] if st == "ok" else None)
                rows.append(dict(rule=rule, noaa=r.noaa, day=r.day, image=img, choice_status=r.status, pair_status=r.pair_status,
                                 T_REC=f"T{k}{img}" if st in ("ok", "window_outside_mu_domain") else None, status=st,
                                 file=f"f{k}{img}" if st in ("ok", "window_outside_mu_domain") else None, quality=q,
                                 interval_s=r.A_interval, main_status=st if st in ("ok", "window_outside_mu_domain") else None,
                                 sens100_status=(("polarity_below_min_pixels" if k % 8 == 0 else "ok") if st == "ok" else
                                                 (st if st == "window_outside_mu_domain" else None))))
    l2 = pd.DataFrame(rows)
    shift = np.where(l2.image == "A", 2.0, 1.0)
    l2_t = np.tile(np.concatenate([base, base]), 2) + shift
    fill(l2, "", l2_t, l2.file.notna().to_numpy())
    meas = l2.file.notna().to_numpy()
    for s in ("qm", "qp"):
        l2[f"{s}_status"] = np.where(meas, np.where(np.arange(len(l2)) % 6 == 0, "ok", "window_outside_mu_domain"), None)
        l2[f"{s}_mad_g"] = np.where(l2[f"{s}_status"] == "ok", rng.uniform(3, 8, len(l2)), np.nan)
    l2["quiet_mad_g"] = l2[["qm_mad_g", "qp_mad_g"]].mean(axis=1)
    m1 = samp.iloc[:n][samp.cohort.iloc[:n] == "M1"]
    mwo = pd.DataFrame(dict(noaa=m1.noaa, day_utc=m1.day, mwo_time_utc=m1.day + "T18:00:00",
                            tilt_deg=(base[m1.index] - 1.0 + 180) % 360 - 180, leading_polarity_sign=1,
                            flux_window_mx=10 ** rng.uniform(20, 22, len(m1))))
    mwo.loc[mwo.index[::2], "mwo_time_utc"] += ".125"
    return samp, l1, l2, {"A1": ch, "original": orig}, mwo


UPSTREAM = (("SEL", "SEL_REC", "selection_meta_sha256"), ("L1", "L1_REC", "l1_meta_sha256"), ("AN1", "AN1_REC", "analysis_meta_sha256"),
            ("PLAN", "PLAN_REC", "plan_meta_sha256"), ("L2", "L2_REC", "l2_meta_sha256"))
# Counterexamples of the upstream contract (Codex review of 3c79d78 and the analogous links): (name, stage, change of its META).
GATE_CASES = (
    ("level-1 analysis names a stale L1 META", "AN1", lambda m: m.update(l1_meta_sha256="0" * 64)),
    ("level-1 analysis names a stale selection META", "AN1", lambda m: m.update(selection_meta_sha256="0" * 64)),
    ("level-1 analysis names a stale selection receipt", "AN1", lambda m: m.update(selection_receipt_sha256="0" * 64)),
    ("level-1 analysis names a stale L1 receipt", "AN1", lambda m: m.update(l1_receipt_sha256="0" * 64)),
    ("level-1 analysis names another MWO release", "AN1", lambda m: m.update(release_sha256="0" * 64)),
    ("level-1 analysis with an empty product manifest", "AN1", lambda m: m.update(products_sha256={})),
    ("level-1 analysis manifest without CLASS_EDGES.json", "AN1", lambda m: m["products_sha256"].pop("CLASS_EDGES.json")),
    ("selection names another protocol", "SEL", lambda m: m.update(protocol_sha256="0" * 64)),
    ("level 1 names another protocol", "L1", lambda m: m.update(protocol_sha256="0" * 64)),
    ("level-1 analysis names another protocol", "AN1", lambda m: m.update(protocol_sha256="0" * 64)),
    ("plan names another protocol", "PLAN", lambda m: m.update(protocol_sha256="0" * 64)),
    ("level 2 names another protocol", "L2", lambda m: m.update(protocol_sha256="0" * 64)),
    ("plan names another A1", "PLAN", lambda m: m.update(a1_sha256="0" * 64)),
    ("level 2 names another A1", "L2", lambda m: m.update(a1_sha256="0" * 64)),
    ("level 1 names a stale selection META", "L1", lambda m: m.update(selection_meta_sha256="0" * 64)),
    ("level 1 names a stale selection receipt", "L1", lambda m: m.update(selection_receipt_sha256="0" * 64)),
    ("level 2 names a stale plan META", "L2", lambda m: m.update(plan_meta_sha256="0" * 64)),
    ("level 2 names a stale selection META", "L2", lambda m: m.update(selection_meta_sha256="0" * 64)),
    ("level 2 names other metadata than the plan", "L2", lambda m: m.update(metadata_meta_sha256="0" * 64)),
    ("selection names another MWO release", "SEL", lambda m: m.update(mwo_release_sha256="0" * 64)))


def gate_fixture(root, case=None):
    """Synthetic upstream tree for the gate regressions (no real file is read): protocol, A1, release, the five stages
    with products, META carrying every link of the contract, strict receipts, and the META of a run on it.
    case = (stage, change) alters that stage's META before it is written; later stages link to the altered bytes, so
    only the targeted link is wrong. Returns (paths by global name, run META)."""
    root = Path(root)
    P = {k: root / k for s in UPSTREAM for k in s[:2]}
    for p in P.values():
        p.mkdir(parents=True)
    P.update(PROTOCOL=root / "protocol.md", FREEZE=root / "freeze.json", A1=root / "a1.md", A1_FREEZE=root / "a1_freeze.json",
             RELEASE=root / "release.csv")
    P["PROTOCOL"].write_text("synthetic protocol\n")
    P["A1"].write_text("synthetic A1\n")
    P["RELEASE"].write_text("noaa\n1\n")
    ph, ah, rel = sha(P["PROTOCOL"]), sha(P["A1"]), sha(P["RELEASE"])
    P["FREEZE"].write_text(json.dumps(dict(sha256=ph)))
    P["A1_FREEZE"].write_text(json.dumps(dict(sha256=ah, parent_sha256=ph)))
    names = dict(SEL=SEL_PRODUCTS, L1=L1_PRODUCTS, AN1=AN1_PRODUCTS, PLAN=PLAN_PRODUCTS, L2=L2_PRODUCTS)
    ms, rs = (lambda k: sha(P[k] / "META.json")), (lambda k: sha(P[k + "_REC"] / "RECEIPT.json"))
    links = dict(SEL=lambda: dict(mwo_release_sha256=rel),
                 L1=lambda: dict(selection_meta_sha256=ms("SEL"), selection_receipt_sha256=rs("SEL")),
                 AN1=lambda: dict(selection_meta_sha256=ms("SEL"), l1_meta_sha256=ms("L1"), selection_receipt_sha256=rs("SEL"),
                                  l1_receipt_sha256=rs("L1"), release_sha256=rel),
                 PLAN=lambda: dict(a1_sha256=ah, metadata_meta_sha256="m" * 64),
                 L2=lambda: dict(a1_sha256=ah, plan_meta_sha256=ms("PLAN"), selection_meta_sha256=ms("SEL"), metadata_meta_sha256="m" * 64))
    for k, rec, key in UPSTREAM:
        for n in sorted(names[k]):
            (P[k] / n).write_text('{"separation_main_l1_ok": [3.0, 6.0]}\n' if n == "CLASS_EDGES.json" else "{}\n" if n.endswith(".json") else "x\n1\n")
        m = dict(protocol_sha256=ph, **links[k](), products_sha256={n: sha(P[k] / n) for n in sorted(names[k])})
        if case is not None and case[0] == k:
            case[1](m)
        (P[k] / "META.json").write_text(json.dumps(m, indent=2) + "\n")
        (P[rec] / "RECEIPT.json").write_text(json.dumps(dict(passed=1, total=1, partial=False, checks=[dict(name="synthetic", ok=True)],
                                                             **{key: ms(k)})))
    run_meta = dict(protocol_sha256=ph, a1_sha256=ah, release_sha256=rel, seed=SEED, reps=REPS,
                    analysis_l1_class_edges_sha256=sha(P["AN1"] / "CLASS_EDGES.json"),
                    receipts_sha256={n: rs(k) for n, k in (("selection", "SEL"), ("l1", "L1"), ("analysis_l1", "AN1"), ("plan", "PLAN"), ("l2", "L2"))},
                    **{f: ms(k) for f, k in (("selection_meta_sha256", "SEL"), ("l1_meta_sha256", "L1"), ("analysis_l1_meta_sha256", "AN1"),
                                             ("plan_meta_sha256", "PLAN"), ("l2_meta_sha256", "L2"))})
    return P, run_meta


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    # upstream gate on synthetic trees: the module paths are rebound only inside this block
    saved = {k: globals()[k] for s in UPSTREAM for k in s[:2]} | {k: globals()[k] for k in ("PROTOCOL", "FREEZE", "A1", "A1_FREEZE", "RELEASE")}
    try:
        with tempfile.TemporaryDirectory() as td:
            def gate(name, case=None, after=None):
                P, _ = gate_fixture(Path(td) / name.replace(" ", "_"), case)
                if after:
                    after(P)
                globals().update(P)
                return upstream_problems()
            base = gate("base")
            ok("gate: synthetic upstream accepted", base == [], base)
            for name, stage, change in GATE_CASES:
                ok(f"gate refuses: {name}", gate(name, (stage, change)) != [])
            ok("gate refuses: level-2 product bytes changed without updating the hash",
               gate("bytes", after=lambda P: (P["L2"] / "L2_RECORDS.csv").write_text("changed\n")) != [])
    finally:
        globals().update(saved)

    samp, l1, l2, choices, mwo = synthetic()
    pr = build(samp, l1, l2, choices, mwo, reps=200)
    y = pr["YIELD_A1"]
    a_all = y[(y.image == "A") & (y.group == "all")].iloc[0]
    ok("yield: denominator = level-2 groups for A and for B; causes sum to n", a_all.n == 90
       and (y[y.group == "all"].n == 90).all() and (y[[f"cause_{s}" for s in STATUSES]].sum(axis=1) == y.n).all())
    g = group_frame(samp, l1, l2, choices, "A1")
    w, okA = g.w2.to_numpy(), (g.A_status == "ok").to_numpy()
    ok("yield: projected = sum(w2 ok) / sum(w2)", abs(a_all.projected_yield - (w * okA).sum() / w.sum()) < 1e-12)
    ok("yield: losses by year, by INTERVAL of A (unknown and no A included) and by QUALITY of A",
       any(y.group.str.startswith("year=")) and {"interval_A=30 s", "interval_A=300 s", "interval_A=unknown", "interval_A=no A"} <= set(y.group)
       and {f"quality_A={Q0}", f"quality_A={Q200}", "quality_A=no A"} <= set(y.group))
    q2 = pr["Q2_PAIRS_A1_main"]
    ok("Q2: synoptic - fd(A) = -2 deg (axial), d_gamma = sign(lat) d_ax, ratios first/second",
       len(q2) > 0 and np.allclose(q2.d_ax, -2.0) and np.allclose(q2.d_gamma, np.sign(q2.lat) * q2.d_ax)
       and np.allclose(q2.flux_ratio, q2.flux1_mx / q2.flux2_mx) and np.allclose(q2.pix_ratio, q2.pix1 / q2.pix2))
    ok("Q2: only groups with level-1 and A ok; time T_OBS(A) - t_DPD", len(q2) == int(((g.syn_main_status == "ok") & (g.A_main_status == "ok")).sum())
       and np.allclose(q2.abs_dt_h, np.abs(q2.dt_A_minus_tdpd_h)))
    rp = pr["REPEAT_PAIRS_A1_main"]
    ok("REPEAT: A - B = +1 deg; only pairs with both ok; Delta t from the plan in hours",
       len(rp) > 0 and np.allclose(rp.d_ax, 1.0) and np.allclose(rp.abs_dt_h, np.abs(rp.pair_dt_min) / 60)
       and len(rp) == int(((g.A_main_status == "ok") & (g.B_main_status == "ok")).sum()))
    ok("REPEAT: unknown INTERVAL forms no pair; QUALITY transitions kept as a group",
       not (rp.interval_A == "unknown").any() and rp.quality_transition.any()
       and "quality_transition True" in set(pr["REPEAT_SUMMARY_A1_main"].group))
    q3 = pr["Q3FD_PAIRS_A1_main"]
    ok("Q3FD: M1 only, fd(A) - MWO = +3 deg, MWO - T_OBS(A) = MWO - t_DPD - A_dt_h, pixel/area ratios not computable",
       len(q3) > 0 and set(q3.cohort) == {"M1"} and np.allclose(q3.d_ax, 3.0)
       and np.allclose(q3.dt_mwo_minus_tobsA_h, q3.dt_mwo_minus_tdpd_h - g.set_index("noaa").loc[q3.noaa, "plan_A_dt_h"].to_numpy())
       and q3.pix_ratio.isna().all() and q3.area_ratio.isna().all())
    e = pr["CLASS_EDGES"]["separation_main_l1_ok"]
    ok("separation edges from the main level-1 synoptic separations, applied to the MDI member everywhere",
       np.allclose(e, np.quantile(l1[l1.main_status == "ok"].main_sep_deg, [1 / 3, 2 / 3]))
       and all((pr[k].sep_class.to_numpy() == np.searchsorted(e, pr[k].sep1_deg, side="right") + 1).all()
               for k in pr if "_PAIRS_" in k))
    t, tr = pr["Q2_SUMMARY_A1_main"], pr["REPEAT_SUMMARY_A1_main"]
    ok("summary: QUALITY and INTERVAL groups present; empty group (REPEAT, unknown INTERVAL) -> n 0, 'no pairs', no crash",
       {f"quality_A {Q0}", f"quality_A {Q200}", "interval_A 30 s", "interval_A 300 s", "interval_A unknown"} <= set(t.group)
       and t[t.group == "interval_A unknown"].n_pairs.iloc[0] > 0 and tr[tr.group == "interval_A unknown"].n_pairs.iloc[0] == 0
       and (tr[tr.n_pairs == 0].interval_note == "no pairs").all())
    ok("yield: class groups non-empty and summing to n", all(y[(y.image == "A") & y.group.str.startswith(f"{c}=")].n.sum() == 90
                                                             for c in ("activity", "area", "hemisphere", "cohort", "year", "interval_A", "quality_A")))
    so = pr["REPEAT_SUMMARY_original_sens100"]
    ok("secondary original rule: separate tables, small n -> medians only", (so[so.n_pairs.between(1, 9)].interval_note.str.startswith("fewer than 10")).all()
       and len(pr["Q2_PAIRS_original_main"]) < len(q2))
    empty = pairs(g.assign(A_main_status="window_outside_mu_domain"), "Q2", "main", np.array(e))
    se = summary(empty, "Q2", 50)
    ok("whole comparison empty: no crash, every group n 0 'no pairs'", len(empty) == 0 and (se.n_pairs == 0).all() and (se.interval_note == "no pairs").all())
    qs = pr["QUIET_SUMMARY_A1"]
    g0 = g.copy()
    for img in ("A", "B"):
        for s in ("qm", "qp"):
            g0[f"{img}_{s}_status"] = np.where(g0[f"{img}_file"].notna(), "dpd_group_inside", None)
        g0[f"{img}_quiet_mad_g"] = np.nan
    ok("quiet: counts over measured images; none valid -> 'non disponibile', never zero",
       qs["sides_total"] == 2 * qs["images_measured"] and quiet_tables(g0)[1]["median_g"] == "non disponibile")
    t2 = summary(q2, "Q2", 2000)
    ok("bootstrap: 2000 replicates reproducible, interval for the full group", t2.equals(summary(q2, "Q2", 2000))
       and np.isfinite(t2[t2.group == "all"].d_ax_lo.iloc[0]))
    ok("bootstrap: fewer than 3 blocks -> non valutabile", summary(q2.assign(N=1950), "Q2", 30).interval_note.iloc[0].startswith("non valutabile"))
    s0 = samp.copy()
    s0.loc[0, "lat"] = 0.0
    p0 = pairs(group_frame(s0, l1, l2, choices, "A1"), "Q2", "main", np.array(e))
    ok("d_gamma undefined (NaN) at lat_DPD = 0", p0[p0.noaa == s0.noaa.iloc[0]].d_gamma.isna().all() if (p0.noaa == s0.noaa.iloc[0]).any() else False)
    try:
        pairs(g, "Q3FD", "main", np.array(e), mwo.iloc[1:])
        ok("Q3FD: an M1 pair without MWO record stops", False)
    except ValueError:
        ok("Q3FD: an M1 pair without MWO record stops", True)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    gp = ap.add_mutually_exclusive_group(required=True)
    gp.add_argument("--selftest", action="store_true")
    gp.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
