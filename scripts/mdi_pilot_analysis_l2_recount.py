"""Independent recount of the MDI pilot level-2 analysis (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md, amendment A1).

Every product is rebuilt with own code (importing neither scripts/mdi_pilot_analysis_l2.py nor python/sharpbl/tilt_window.py):
own per-group table built row by row from dictionaries, own yields with w2, own quiet counts, own pairs and angular
differences, own time distances, own groups and bootstrap; the comparison is complete (exact product set, exact
columns and order, every key and value, NaN = NaN, JSON documents equal, NOTES.json and the quiet note equal to the
texts written here). On the real path the upstream contracts are verified before any computation: fixed expected
product sets with actual hashes, strict receipts, frozen protocol and A1 named by every stage that records them, the
links between stages (L1 -> selection; level-1 analysis -> selection, L1, their receipts, release; L2 -> selection,
plan, plan metadata) and the links of the run (every upstream META and receipt, the CLASS_EDGES.json used). The
receipt is complete only there with 2000 replicates.

    .venv/bin/python scripts/mdi_pilot_analysis_l2_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_analysis_l2_recount.py --check
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT, REC = ROOT / "results/MDI_PILOT_ANALYSIS_L2", ROOT / "results/MDI_PILOT_ANALYSIS_L2_RECOUNT"
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
L1, L1_REC = ROOT / "results/MDI_PILOT_L1", ROOT / "results/MDI_PILOT_L1_RECOUNT"
AN1, AN1_REC = ROOT / "results/MDI_PILOT_ANALYSIS_L1", ROOT / "results/MDI_PILOT_ANALYSIS_L1_RECOUNT"
L2, L2_REC = ROOT / "results/MDI_PILOT_L2", ROOT / "results/MDI_PILOT_L2_RECOUNT"
PLAN, PLAN_REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1", ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
SEED, REPS = 71_100_001, 2000
RULES, TAGS, KINDS = ("A1", "original"), ("main", "sens100"), ("Q2", "REPEAT", "Q3FD")
Q0, Q200 = "0x00000000", "0x00000200"
STAT = ["ok", "no_magnetogram", "no_image", "not_determined", "fits_missing", "window_outside_mu_domain", "window_off_disk",
        "window_empty", "window_missing", "no_two_polarities", "polarity_below_min_pixels", "quality_not_zero",
        "quality_not_admissible", "quality_missing", "quality_unparsable", "geometry_keywords_unparsable"]
PRODUCTS = ({"CLASS_EDGES.json", "NOTES.json"} | {f"YIELD_{r}.csv" for r in RULES} | {f"QUIET_AVAILABILITY_{r}.csv" for r in RULES}
            | {f"QUIET_SUMMARY_{r}.json" for r in RULES}
            | {f"{k}_{x}_{r}_{t}.csv" for k in KINDS for x in ("PAIRS", "SUMMARY") for r in RULES for t in TAGS})
# Expected NOTES.json, written here (not imported from the runner): every key and every text is compared.
NOTES_EXPECTED = {
    "comparisons": "descriptive relative differences; no instrument or product is assumed correct",
    "order": "Q2 = synoptic - fd(A); REPEAT = A - B; Q3FD = fd(A) - MWO; ratios = first / second member",
    "q2_time": "T_OBS(A) - t_DPD; the synoptic instant per pixel is undetermined (CT_g and T_ROT kept)",
    "q3fd_time": "MWO - t_DPD (protocol) and MWO - T_OBS(A); the summary median uses |MWO - T_OBS(A)|",
    "repeat_time": "T_OBS(B) - T_OBS(A) from the plan; it includes real evolution and possibly correlated errors, not separated",
    "repeat_interval": "pairs only with the same numeric INTERVAL; an unknown INTERVAL forms no pair",
    "quality_transitions": "pairs with different QUALITY at the same INTERVAL are kept and reported as a group (A1)",
    "mwo_pixel_area_ratios": "not computable: the MWO release has no pixel counts or areas per polarity",
    "quiet": "scaled MAD = observed field dispersion (solar field, noise and processing), not instrumental noise; without a valid "
             "side the value is 'non disponibile', never zero, and it does not invalidate a tilt",
    "separation": "terciles of the successful main level-1 synoptic separations, applied to the MDI member of every comparison",
    "weights": "yields projected with w2 = 1/pi2; comparisons unweighted",
    "original_rule": "secondary table with the original A/B assignments (QUALITY {0}); not a filter of the A1 assignments"}
# Expected upstream product sets (own constants, not read from the manifests under check).
UP_PRODUCTS = {"SEL": {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}, "L1": {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"},
               "AN1": {"Q1_YIELD_CELLS.csv", "Q1_YIELD_PROJECTED.csv", "Q1_QUIET_AVAILABILITY.csv", "Q1_QUIET_SUMMARY.json",
                       "Q1_M_EXPLORATORY.json", "CLASS_EDGES.json", "NOTES.json", "Q3_PAIRS_main.csv", "Q3_SUMMARY_main.csv",
                       "Q3_PAIRS_sens100.csv", "Q3_SUMMARY_sens100.csv"},
               "PLAN": {"CHOICES_A1.csv", "CHOICES_ORIGINAL.csv", "PLAN.csv", "COVERAGE.csv"}, "L2": {"L2_RECORDS.csv"}}


def _mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


R1 = _mod("an1rec", "scripts/mdi_pilot_analysis_l1_recount.py")          # own frames_equal and strict receipt (recount code)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def isnum(v):
    try:
        return math.isfinite(float(v))
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------- own per-group table

def own_groups(samp, l1, l2, ch):
    """List of dicts, one per level-2 group in sample order."""
    l1d = {(r["noaa"], r["day"]): r for r in l1.to_dict("records")}
    chd = {(r["noaa"], r["day"]): r for r in ch.to_dict("records")}
    l2d = {(r["noaa"], r["day"], r["image"]): r for r in l2.to_dict("records")}
    out = []
    for s in samp.to_dict("records"):
        if str(s["level2"]) != "True":
            continue
        k = (s["noaa"], s["day"])
        c = chd[k]
        okc = c["status"] == "ok"
        iv = "no A" if not okc else (f"{float(c['A_interval']):g} s" if isnum(c["A_interval"]) else "unknown")
        out.append(dict(s=s, syn=l1d[k], A=l2d[k + ("A",)], B=l2d[k + ("B",)], c=c, year=s["day"][:4], interval_A=iv,
                        quality_A=str(c["A_quality"]) if okc else "no A"))
    return out


def own_yield(G):
    rows = []
    for img in ("A", "B"):
        sets = [("all", G)]
        for lab, f in (("activity", lambda g: str(g["s"]["act_class"])), ("area", lambda g: str(g["s"]["area_class"])),
                       ("hemisphere", lambda g: str(g["s"]["hemisphere"])), ("cohort", lambda g: str(g["s"]["cohort"])),
                       ("year", lambda g: g["year"]), ("interval_A", lambda g: g["interval_A"]), ("quality_A", lambda g: g["quality_A"])):
            for v in sorted({f(g) for g in G}):
                sets.append((f"{lab}={v}", [g for g in G if f(g) == v]))
        for name, S in sets:
            st = [g[img]["status"] for g in S]
            o = np.array([x == "ok" for x in st], float)
            o1 = np.array([g[img].get("sens100_status") == "ok" for g in S], float)
            w = np.array([float(g["s"]["w2"]) for g in S])
            r = {"image": img, "group": name, "n": len(S), "ok": int(o.sum()), "ok100": int(o1.sum()), "sample_yield": o.mean(),
                 "sample_yield_100": o1.mean(), "projected_yield": (w * o).sum() / w.sum(), "projected_yield_100": (w * o1).sum() / w.sum(),
                 "population_weight": w.sum()}
            r.update({f"cause_{x}": sum(y == x for y in st) for x in STAT})
            rows.append(r)
    return pd.DataFrame(rows)


def own_quiet(G):
    sides, vals = [], []
    for g in G:
        for img in ("A", "B"):
            r = g[img]
            if isinstance(r.get("file"), str) and r["file"]:
                for s in ("qm", "qp"):
                    v = r.get(f"{s}_status")
                    sides.append(v if isinstance(v, str) and v else "not_attempted")
                if isnum(r.get("quiet_mad_g")):
                    vals.append(float(r["quiet_mad_g"]))
    names = sorted(set(sides))
    av = pd.DataFrame({"status": names, "n_sides": [sides.count(x) for x in names]})
    v = np.array(vals)
    q = lambda p: float(np.quantile(v, p)) if len(v) else "non disponibile"      # noqa: E731
    return av, {"images_measured": len(sides) // 2, "sides_total": len(sides), "sides_ok": sides.count("ok"), "images_with_value": len(v),
                "median_g": q(0.5), "p10_g": q(0.1), "p90_g": q(0.9), "note": NOTES_EXPECTED["quiet"]}


def mem(r, tag):
    f = lambda k: float(r[f"{tag}_{k}"])                                   # noqa: E731
    return dict(t=f("tilt_deg"), lead=int(f("leading_sign")), flux=f("flux_pos_mx") + f("flux_neg_mx"), pix=f("npos") + f("nneg"),
                area=f("area_pos_msh") + f("area_neg_msh"), sep=f("sep_deg"))


def hours(a, b):
    return (pd.Timestamp(a) - pd.Timestamp(b)).total_seconds() / 3600.0


def own_pairs(G, kind, tag, e, mwo):
    mw = {(r["noaa"], r["day_utc"]): r for r in mwo.to_dict("records")}
    rows = []
    for g in G:
        s, c = g["s"], g["c"]
        if kind == "Q2":
            if g["syn"].get(f"{tag}_status") != "ok" or g["A"].get(f"{tag}_status") != "ok":
                continue
            one, two = mem(g["syn"], tag), mem(g["A"], tag)
        elif kind == "REPEAT":
            if g["A"].get(f"{tag}_status") != "ok" or g["B"].get(f"{tag}_status") != "ok":
                continue
            one, two = mem(g["A"], tag), mem(g["B"], tag)
        else:
            if s["cohort"] != "M1" or g["A"].get(f"{tag}_status") != "ok":
                continue
            w = mw.get((s["noaa"], s["day"]))
            if w is None:
                raise ValueError("M1 without MWO")
            one = mem(g["A"], tag)
            two = dict(t=float(w["tilt_deg"]), lead=int(w["leading_polarity_sign"]), flux=float(w["flux_window_mx"]), pix=np.nan, area=np.nan, sep=np.nan)
        raw = one["t"] - two["t"]
        ax = (raw + 90.0) % 180.0 - 90.0
        sg = np.sign(float(s["lat"]))
        r = {"noaa": s["noaa"], "day": s["day"], "N": int(g["syn"]["N"]), "hemisphere": s["hemisphere"], "act_class": s["act_class"],
             "area_class": s["area_class"], "cohort": s["cohort"], "sep_class": 1 if one["sep"] < e[0] else (2 if one["sep"] < e[1] else 3),
             "lat": s["lat"], "t_dpd": s["t_dpd"], "quality_A": g["quality_A"], "interval_A": g["interval_A"], "t1_deg": one["t"], "t2_deg": two["t"],
             "d_raw": raw, "d_dir": (raw + 180.0) % 360.0 - 180.0, "d_ax": ax, "d_gamma": np.nan if sg == 0 else sg * ax,
             "lead1": one["lead"], "lead2": two["lead"], "leading_agree": one["lead"] == two["lead"], "flux1_mx": one["flux"],
             "flux2_mx": two["flux"], "flux_ratio": one["flux"] / two["flux"], "pix1": one["pix"], "pix2": two["pix"],
             "pix_ratio": one["pix"] / two["pix"], "area1_msh": one["area"], "area2_msh": two["area"], "area_ratio": one["area"] / two["area"],
             "sep1_deg": one["sep"]}
        if kind == "Q2":
            r.update(A_T_REC=g["A"]["T_REC"], dt_A_minus_tdpd_h=float(c["A_dt_h"]), CT_g=g["syn"]["CT_g"], t_rot=g["syn"]["t_rot"])
            r["abs_dt_h"] = abs(r["dt_A_minus_tdpd_h"])
        elif kind == "REPEAT":
            r.update(A_T_REC=g["A"]["T_REC"], B_T_REC=g["B"]["T_REC"], A_quality_rec=g["A"]["quality"], B_quality_rec=g["B"]["quality"],
                     quality_transition=str(c["quality_transition"]).lower() == "true", pair_dt_min=float(c["pair_dt_min"]))
            r["abs_dt_h"] = abs(r["pair_dt_min"]) / 60.0
        else:
            d1 = hours(w["mwo_time_utc"], s["t_dpd"])
            r.update(A_T_REC=g["A"]["T_REC"], mwo_time_utc=w["mwo_time_utc"], dt_mwo_minus_tdpd_h=d1, dt_mwo_minus_tobsA_h=d1 - float(c["A_dt_h"]))
            r["abs_dt_h"] = abs(r["dt_mwo_minus_tobsA_h"])
        rows.append(r)
    cols = (["noaa", "day", "N", "hemisphere", "act_class", "area_class", "cohort", "sep_class", "lat", "t_dpd", "quality_A", "interval_A",
             "t1_deg", "t2_deg", "d_raw", "d_dir", "d_ax", "d_gamma", "lead1", "lead2", "leading_agree", "flux1_mx", "flux2_mx", "flux_ratio",
             "pix1", "pix2", "pix_ratio", "area1_msh", "area2_msh", "area_ratio", "sep1_deg", "abs_dt_h"]
            + {"Q2": ["A_T_REC", "dt_A_minus_tdpd_h", "CT_g", "t_rot"],
               "REPEAT": ["A_T_REC", "B_T_REC", "A_quality_rec", "B_quality_rec", "quality_transition", "pair_dt_min"],
               "Q3FD": ["A_T_REC", "mwo_time_utc", "dt_mwo_minus_tdpd_h", "dt_mwo_minus_tobsA_h"]}[kind])
    return pd.DataFrame(rows, columns=cols)


def own_summary(p, kind, reps):
    def st(x):
        return (np.nanmedian(x.d_ax) if len(x) else np.nan, np.nanmedian(x.d_gamma) if len(x) and x.d_gamma.notna().any() else np.nan,
                x.leading_agree.astype(float).mean() if len(x) else np.nan)

    def md(v):
        v = v.dropna()
        return float(v.median()) if len(v) else np.nan

    blk = ((p.N.astype(int) - int(p.N.min())) // 6).to_numpy() if len(p) else np.zeros(0, int)
    lab = np.unique(blk)
    mem_ = [np.flatnonzero(blk == b) for b in lab]
    rng = np.random.default_rng(SEED)
    draws = [np.concatenate([mem_[i] for i in rng.integers(0, len(lab), len(lab))]) for _ in range(reps)] if len(lab) else []
    gs = [("all", np.ones(len(p), bool))]
    for col, name in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation")):
        gs += [(f"{name} {k}", (p[col] == k).to_numpy()) for k in (1, 2, 3)]
    gs += [(f"hemisphere {h}", (p.hemisphere == h).to_numpy()) for h in ("N", "S")]
    gs += [(f"quality_A {q}", (p.quality_A == q).to_numpy()) for q in (Q0, Q200)]
    gs += [(f"interval_A {i}", (p.interval_A == i).to_numpy()) for i in ("30 s", "300 s", "unknown")]
    if kind == "REPEAT":
        gs += [(f"quality_transition {v}", (p.quality_transition == v).to_numpy()) for v in (False, True)]
    rows = []
    for name, mk in gs:
        x = p[mk]
        a, g, ag = st(x)
        r = {"group": name, "n_pairs": len(x), "n_blocks": len(np.unique(blk[mk])) if len(x) else 0, "median_d_ax": a, "median_d_gamma": g,
             "leading_agree": ag, "median_flux_ratio": md(x.flux_ratio), "median_pix_ratio": md(x.pix_ratio),
             "median_area_ratio": md(x.area_ratio), "median_abs_dt_h": md(x.abs_dt_h), "valid_reps": np.nan, "d_ax_lo": np.nan,
             "d_ax_hi": np.nan, "d_gamma_lo": np.nan, "d_gamma_hi": np.nan, "agree_lo": np.nan, "agree_hi": np.nan}
        if not len(x):
            r["interval_note"] = "no pairs"
        elif len(x) < 10:
            r["interval_note"] = "fewer than 10 pairs: n and medians only"
        elif r["n_blocks"] < 3:
            r["interval_note"] = "non valutabile (fewer than 3 blocks)"
        else:
            b = np.array([st(p.iloc[d[mk[d]]]) if mk[d].any() else (np.nan,) * 3 for d in draws])
            good = np.isfinite(b[:, 0])
            r["valid_reps"] = int(good.sum())
            if good.sum() >= 1900:
                for j, k in enumerate(("d_ax", "d_gamma", "agree")):
                    vv = b[good, j]
                    vv = vv[np.isfinite(vv)]
                    if len(vv) >= 1900:
                        r[f"{k}_lo"], r[f"{k}_hi"] = np.quantile(vv, [0.025, 0.975])
                r["interval_note"] = ""
            else:
                r["interval_note"] = "fewer than 1900 valid replicates"
        rows.append(r)
    return pd.DataFrame(rows)


def own_all(samp, l1, l2, choices, mwo, reps):
    e = np.quantile(np.sort(l1.loc[l1.main_status == "ok", "main_sep_deg"].to_numpy(float)), [1 / 3, 2 / 3])
    out = {"CLASS_EDGES": {"separation_main_l1_ok": [float(x) for x in e]}}
    for rule in RULES:
        G = own_groups(samp, l1, l2[l2.rule == rule], choices[rule])
        out[f"YIELD_{rule}"] = own_yield(G)
        out[f"QUIET_AVAILABILITY_{rule}"], out[f"QUIET_SUMMARY_{rule}"] = own_quiet(G)
        for kind in KINDS:
            for tag in TAGS:
                p = own_pairs(G, kind, tag, e, mwo)
                out[f"{kind}_PAIRS_{rule}_{tag}"], out[f"{kind}_SUMMARY_{rule}_{tag}"] = p, own_summary(p, kind, reps)
    return out


# ---------------------------------------------------------------- check

def json_equal(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return (a is None and b is None) or (a is not None and b is not None and math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-12))


def upstream(meta):
    """Named upstream contracts, each True or False (an unreadable file or a missing key gives False)."""
    def m(d):
        return json.loads((d / "META.json").read_text())

    def has(d, key, value):
        v = m(d).get(key)
        return isinstance(v, str) and v == value

    def prods(d, names):
        ps = m(d).get("products_sha256")
        return isinstance(ps, dict) and len(names) > 0 and set(ps) == names and all(sha(d / n) == h for n, h in ps.items())

    def protocol():
        fr, fz = json.loads(FREEZE.read_text()), json.loads(A1_FREEZE.read_text())
        return fr["sha256"], fz["sha256"], fz["parent_sha256"]

    stages = {"SEL": SEL, "L1": L1, "AN1": AN1, "PLAN": PLAN, "L2": L2}
    rec = {"SEL": SEL_REC, "L1": L1_REC, "AN1": AN1_REC, "PLAN": PLAN_REC, "L2": L2_REC}
    ms = {k: (lambda d=d: sha(d / "META.json")) for k, d in stages.items()}
    rs = {k: (lambda d=d: sha(d / "RECEIPT.json")) for k, d in rec.items()}
    tests = {
        "protocol and A1 texts, linked to the run": lambda: (lambda P, A, parent: sha(PROTOCOL) == P == parent == meta.get("protocol_sha256")
                                                             and sha(A1) == A == meta.get("a1_sha256"))(*protocol()),
        "selection, level 1, level-1 analysis, plan, level 2: fixed product sets with actual hashes, strict receipts":
            lambda: all(prods(stages[k], UP_PRODUCTS[k]) for k in stages)
            and R1.strict(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json")
            and R1.strict(L1_REC / "RECEIPT.json", "l1_meta_sha256", L1 / "META.json")
            and R1.strict(AN1_REC / "RECEIPT.json", "analysis_meta_sha256", AN1 / "META.json")
            and R1.strict(PLAN_REC / "RECEIPT.json", "plan_meta_sha256", PLAN / "META.json")
            and R1.strict(L2_REC / "RECEIPT.json", "l2_meta_sha256", L2 / "META.json"),
        "frozen protocol named by every stage, frozen A1 by the plan and level 2":
            lambda: all(has(d, "protocol_sha256", protocol()[0]) for d in stages.values())
            and has(PLAN, "a1_sha256", protocol()[1]) and has(L2, "a1_sha256", protocol()[1]),
        "links between stages: L1 -> selection and its receipt; level-1 analysis -> selection, L1, their receipts and the "
        "release; L2 -> selection, plan and the plan's metadata":
            lambda: has(L1, "selection_meta_sha256", ms["SEL"]()) and has(L1, "selection_receipt_sha256", rs["SEL"]())
            and has(AN1, "selection_meta_sha256", ms["SEL"]()) and has(AN1, "l1_meta_sha256", ms["L1"]())
            and has(AN1, "selection_receipt_sha256", rs["SEL"]()) and has(AN1, "l1_receipt_sha256", rs["L1"]())
            and has(AN1, "release_sha256", sha(RELEASE))
            and has(L2, "selection_meta_sha256", ms["SEL"]()) and has(L2, "plan_meta_sha256", ms["PLAN"]())
            and has(L2, "metadata_meta_sha256", m(PLAN).get("metadata_meta_sha256")),
        "run linked to every upstream META and receipt and to the CLASS_EDGES.json of the level-1 analysis":
            lambda: all(meta.get(f) == ms[k]() for f, k in (("selection_meta_sha256", "SEL"), ("l1_meta_sha256", "L1"),
                                                            ("analysis_l1_meta_sha256", "AN1"), ("plan_meta_sha256", "PLAN"), ("l2_meta_sha256", "L2")))
            and meta.get("receipts_sha256") == {n: rs[k]() for n, k in (("selection", "SEL"), ("l1", "L1"), ("analysis_l1", "AN1"),
                                                                       ("plan", "PLAN"), ("l2", "L2"))}
            and meta.get("analysis_l1_class_edges_sha256") == sha(AN1 / "CLASS_EDGES.json") == m(AN1)["products_sha256"]["CLASS_EDGES.json"],
        "MWO release equal to the selection's, seed and replicates":
            lambda: meta.get("release_sha256") == sha(RELEASE) == m(SEL).get("mwo_release_sha256")
            and meta.get("seed") == SEED and meta.get("reps") == REPS}
    out = {}
    for name, f in tests.items():
        try:
            out[name] = bool(f())
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            out[name] = False
    return out


def check(out=OUT, write=True, rec_dir=REC, data=None, reps=REPS):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    def finish():
        passed = sum(c["ok"] for c in checks)
        receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, analysis_l2_meta_sha256=sha(Path(out) / "META.json"))
        if write:
            if not real:
                sys.exit("a receipt is written only on the real path")
            if Path(rec_dir).exists():
                sys.exit("receipt exists")
            Path(rec_dir).mkdir(parents=True)
            (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"recount: {passed}/{len(checks)} (partial {not real})")
        return passed == len(checks)

    real = data is None and reps == REPS
    meta = json.loads((Path(out) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("products: exact set and actual hashes before reading", set(ps) == PRODUCTS and all(sha(Path(out) / n) == h for n, h in ps.items()),
       sorted(set(ps) ^ PRODUCTS)[:4])
    if data is None:
        for name, good in upstream(meta).items():
            ok(name, good)
    if not all(c["ok"] for c in checks):
        print("prerequisites not met: stop before any computation")
        return finish()
    if data is None:
        rd = lambda p, **k: pd.read_csv(p, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip", **k)  # noqa: E731
        data = (rd(SEL / "SAMPLE.csv"), rd(L1 / "L1_RECORDS.csv"), rd(L2 / "L2_RECORDS.csv"),
                {"A1": rd(PLAN / "CHOICES_A1.csv"), "original": rd(PLAN / "CHOICES_ORIGINAL.csv")},
                rd(RELEASE, usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"]))
        an1 = json.loads((AN1 / "CLASS_EDGES.json").read_text())["separation_main_l1_ok"]
    else:
        an1 = None
    own = own_all(*data, reps)
    e = own["CLASS_EDGES"]["separation_main_l1_ok"]
    ok("separation edges: own recomputation equal to the product (and to the preserved level-1 analysis on the real path)",
       json_equal(own["CLASS_EDGES"], json.loads((Path(out) / "CLASS_EDGES.json").read_text())) and (an1 is None or np.allclose(e, an1, rtol=0, atol=1e-12)))
    notes = json.loads((Path(out) / "NOTES.json").read_text())
    ok("notes: every key and every text equal to the expected notes of the recount",
       isinstance(notes, dict) and list(notes) == list(NOTES_EXPECTED) and notes == NOTES_EXPECTED,
       sorted(k for k in set(notes) | set(NOTES_EXPECTED) if notes.get(k) != NOTES_EXPECTED.get(k))[:4] if isinstance(notes, dict) else "")
    bad = []
    for k, v in own.items():
        if k == "CLASS_EDGES":
            continue
        if isinstance(v, pd.DataFrame):
            theirs = pd.read_csv(Path(out) / f"{k}.csv", dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")
            if len(v) == 0 and len(theirs) == 0:
                good, why = list(v.columns) == list(theirs.columns), "columns of an empty table"
            else:
                good, why = R1.frames_equal(theirs, v.astype({c: str for c in ("noaa",) if c in v}))
        else:
            theirs = json.loads((Path(out) / f"{k}.json").read_text())
            good, why = json_equal(v, theirs), "json"
        if not good:
            bad.append((k, why))
    ok("every product rebuilt and equal: yields with causes and w2, quiet, pairs (Q2, REPEAT, Q3FD) and summaries with "
       "bootstrap, both rules and both thresholds", not bad, bad[:4])
    return finish()


# ---------------------------------------------------------------- selftest

def selftest():
    import shutil
    import tempfile
    M = _mod("an2", "scripts/mdi_pilot_analysis_l2.py")                   # runner only to produce the synthetic products
    res = []
    reps = 200

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    data = M.synthetic()
    with tempfile.TemporaryDirectory() as td:
        def produce(d, prods):
            d.mkdir()
            M.write(prods, d)
            (d / "META.json").write_text(json.dumps({"products_sha256": {f.name: sha(f) for f in sorted(d.iterdir())}}))
            return d

        def quiet_check(d, dat=data):
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                return check(d, write=False, data=dat, reps=reps)

        base = produce(Path(td) / "base", M.build(*data, reps=reps))
        ok("synthetic products accepted (partial, no receipt)", quiet_check(base))

        def tamper(name, fname, fn):
            d = Path(td) / name.replace(" ", "_")
            shutil.copytree(base, d)
            f = d / fname
            if fname.endswith(".csv"):
                t = pd.read_csv(f, dtype={"noaa": str}, keep_default_na=False, na_values=[""])
                fn(t).to_csv(f, index=False)
            else:
                f.write_text(json.dumps(fn(json.loads(f.read_text()))))
            m = json.loads((d / "META.json").read_text())
            m["products_sha256"][fname] = sha(f)
            (d / "META.json").write_text(json.dumps(m))
            got = quiet_check(d)
            res.append(not got)
            print(f"[{'OK' if not got else 'FALLITO'}] refused with updated hashes: {name}")

        first = lambda t, c, v: t.assign(**{c: t[c].where(t.index != 0, v)})                   # noqa: E731
        tamper("a Q2 d_ax", "Q2_PAIRS_A1_main.csv", lambda t: first(t, "d_ax", t.d_ax.iloc[0] + 1e-6))
        tamper("a REPEAT pair dropped", "REPEAT_PAIRS_A1_main.csv", lambda t: t.drop(index=0))
        tamper("a Q3FD time distance", "Q3FD_PAIRS_A1_sens100.csv", lambda t: first(t, "dt_mwo_minus_tobsA_h", 0.0))
        tamper("a yield cause count", "YIELD_A1.csv", lambda t: first(t, "cause_window_outside_mu_domain", t.cause_window_outside_mu_domain.iloc[0] + 1))
        tamper("a projected yield", "YIELD_original.csv", lambda t: first(t, "projected_yield", 0.5))
        tamper("a summary median", "Q2_SUMMARY_A1_main.csv", lambda t: first(t, "median_d_ax", 0.0))
        tamper("an empty group given a pair", "REPEAT_SUMMARY_A1_main.csv",
               lambda t: t.assign(n_pairs=t.n_pairs.where(t.group != "interval_A unknown", 1)))
        tamper("a QUALITY group label", "Q2_SUMMARY_original_main.csv", lambda t: t.assign(group=t.group.replace(f"quality_A {Q200}", "quality_A any")))
        tamper("a quiet quantile", "QUIET_SUMMARY_A1.json", lambda j: dict(j, p10_g=0.0))
        tamper("a quiet side count", "QUIET_AVAILABILITY_original.csv", lambda t: first(t, "n_sides", t.n_sides.iloc[0] + 1))
        tamper("a separation edge", "CLASS_EDGES.json", lambda j: {"separation_main_l1_ok": [j["separation_main_l1_ok"][0] + 0.1, j["separation_main_l1_ok"][1]]})
        tamper("a note removed", "NOTES.json", lambda j: {k: v for k, v in j.items() if k != "repeat_time"})
        tamper("comparison order inverted in the notes", "NOTES.json", lambda j: dict(j, order="Q2 = fd(A) - synoptic; Q3FD = MWO - fd(A)"))
        tamper("weights misdescribed in the notes", "NOTES.json", lambda j: dict(j, weights="comparisons weighted by flux"))
        tamper("original rule described as a filter of A1", "NOTES.json", lambda j: dict(j, original_rule="original obtained by filtering A1"))
        tamper("the quiet note in a quiet summary", "QUIET_SUMMARY_A1.json", lambda j: dict(j, note="scaled MAD = instrumental noise"))
        d = Path(td) / "extra_product"
        shutil.copytree(base, d)
        (d / "EXTRA.csv").write_text("x\n1\n")
        m = json.loads((d / "META.json").read_text())
        m["products_sha256"]["EXTRA.csv"] = sha(d / "EXTRA.csv")
        (d / "META.json").write_text(json.dumps(m))
        res.append(not quiet_check(d))
        print(f"[{'OK' if res[-1] else 'FALLITO'}] refused: an extra product")
        # empty subsets: the original rule with no measured image at all, and no M1 group
        samp, l1, l2, ch, mwo = data
        l2e = l2.copy()
        sel = l2e.rule == "original"
        for c in [c for c in l2e.columns if c.startswith(("main_", "sens100_"))]:
            l2e.loc[sel & l2e.main_status.eq("ok"), c] = np.nan
        l2e.loc[sel & (l2e.status == "ok"), ["status", "main_status"]] = "window_outside_mu_domain"
        l2e.loc[sel & l2e.file.notna(), ["qm_status", "qp_status"]] = "dpd_group_inside"
        l2e.loc[sel, ["qm_mad_g", "qp_mad_g", "quiet_mad_g"]] = np.nan
        dat_e = (samp.assign(cohort="U"), l1, l2e, ch, mwo)
        empty = produce(Path(td) / "empty", M.build(*dat_e, reps=reps))
        ok("empty comparisons (original rule without measures, no M1 group) produced and recounted", quiet_check(empty, dat_e)
           and len(pd.read_csv(empty / "Q2_PAIRS_original_main.csv")) == 0 and len(pd.read_csv(empty / "Q3FD_PAIRS_A1_main.csv")) == 0)
        qe = json.loads((empty / "QUIET_SUMMARY_original.json").read_text())
        ok("empty quiet: images measured but no valid side -> 'non disponibile' in the product",
           qe["median_g"] == qe["p10_g"] == qe["p90_g"] == "non disponibile" and qe["images_measured"] > 0 and qe["images_with_value"] == 0)
        qe["median_g"] = 0.0
        (empty / "QUIET_SUMMARY_original.json").write_text(json.dumps(qe))
        m = json.loads((empty / "META.json").read_text())
        m["products_sha256"]["QUIET_SUMMARY_original.json"] = sha(empty / "QUIET_SUMMARY_original.json")
        (empty / "META.json").write_text(json.dumps(m))
        ok("refused with updated hashes: 'non disponibile' written as zero", not quiet_check(empty, dat_e))
        # 2000 replicates: own bootstrap equal to the runner's, intervals present, a bound tampered is refused
        g = M.group_frame(*data[:4], "A1")
        e = np.array(M.separation_edges(data[1]))
        p = M.pairs(g, "Q2", "main", e)
        theirs = M.summary(p, "Q2", 2000)
        mine = own_summary(own_pairs(own_groups(data[0], data[1], data[2][data[2].rule == "A1"], data[3]["A1"]), "Q2", "main", e, data[4]), "Q2", 2000)
        good, why = R1.frames_equal(theirs, mine)
        ok("2000 replicates: own summary equal to the runner's, interval present for the full group",
           good and np.isfinite(theirs[theirs.group == "all"].d_ax_lo.iloc[0]), why)
        bad = theirs.assign(d_ax_lo=theirs.d_ax_lo.where(theirs.group != "all", theirs.d_ax_lo + 1e-9))
        ok("2000 replicates: a bound moved by 1e-9 is refused", not R1.frames_equal(bad, mine)[0])
        # upstream contracts on synthetic trees made by the runner's fixture; the checks are this module's own code
        names = [k for s in M.UPSTREAM for k in s[:2]] + ["PROTOCOL", "FREEZE", "A1", "A1_FREEZE", "RELEASE"]
        saved = {k: globals()[k] for k in names}
        try:
            def gate(name, case=None, after=None, run_change=None):
                P, rm = M.gate_fixture(Path(td) / "gate" / name.replace(" ", "_"), case)
                if after:
                    after(P)
                if run_change:
                    run_change(rm)
                globals().update(P)
                return upstream(rm)
            base_gate = gate("base")
            ok("upstream: synthetic tree accepted", all(base_gate.values()), [k for k, v in base_gate.items() if not v])
            for name, stage, change in M.GATE_CASES:
                ok(f"upstream refuses: {name}", not all(gate(name, (stage, change)).values()))
            ok("upstream refuses: level-2 product bytes changed without updating the hash",
               not all(gate("bytes", after=lambda P: (P["L2"] / "L2_RECORDS.csv").write_text("changed\n")).values()))
            ok("upstream refuses: run names another CLASS_EDGES.json",
               not all(gate("edges", run_change=lambda rm: rm.update(analysis_l1_class_edges_sha256="0" * 64)).values()))
            ok("upstream refuses: run names a stale level-1 analysis receipt",
               not all(gate("receipt", run_change=lambda rm: rm["receipts_sha256"].update(analysis_l1="0" * 64)).values()))
        finally:
            globals().update(saved)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
