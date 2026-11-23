"""Descriptive post-reading diagnosis of S2 on catalogue R4 (docs/T3_MWO_S2_DIAGNOSIS_NOTE.md, frozen before the run).

Not an amendment: S2, the frozen rule and the descriptive outcome of beta3 are unchanged; no verdict, no causal label,
no classification. Fits use s2_fit and the helpers of scripts/t3_mwo_analysis.py unchanged; intervals of subsets and
components are nominal and NOT validated. SEALED.csv.gz is never read: gamma_MWO comes from the verified release.

    .venv/bin/python scripts/t3_mwo_s2_diagnosis.py --selftest
    .venv/bin/python scripts/t3_mwo_s2_diagnosis.py --run          # only after the code review
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs/T3_MWO_S2_DIAGNOSIS_NOTE.md"
STAB = ROOT / "results/T3_MWO_STABILITY_R4"
STAB_REC = ROOT / "results/T3_MWO_STABILITY_R4_RECOUNT"
EST = ROOT / "results/T3_MWO_ESTIMATE_R4"
EST_REC = ROOT / "results/T3_MWO_ESTIMATE_R4_RECOUNT"
REL = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE"
REL_REC = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT"
OUT = ROOT / "results/T3_MWO_S2_DIAGNOSIS_R4"
SEED = 69_600_001
JOY_SEED = 69_500_001
REPS, BLOCK, MIN_VALID = 2000, 6, 1900
MIN_FIT = 300
BIG = 45.0
WRAP_TOL = 1e-9
N_S2 = 4694
LOO_EPOCHS = ("E2", "E3", "E4", "E5", "E6", "E8")
D4_VARS = (("dpd_area", "dpd_area"), ("phi_mwo", "phi_mwo"), ("separation", "separation"))
FIT_KEYS = ("beta", "se", "lo", "hi", "var_a", "var_b", "phi", "kappa", "sigma_x2", "error")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A = load_module("t3_mwo_analysis", ROOT / "scripts/t3_mwo_analysis.py")
EX = load_module("t3_mwo_stability_extras", ROOT / "scripts/t3_mwo_stability_extras.py")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- terciles, blocks, bootstrap (note: rules)

def tercile_edges(x):
    return np.quantile(np.asarray(x, float), [1 / 3, 2 / 3])          # linear method, unweighted, full S2 subset


def tercile_class(x, edges):
    return np.searchsorted(edges, np.asarray(x, float), side="right") + 1


def block_ids(cr):
    cr = np.asarray(cr).astype(int)
    b = (cr - cr.min()) // BLOCK
    _, inv = np.unique(b, return_inverse=True)
    return inv                                                          # 0..nb-1 in CR order


def multiplicities(blk, reps=REPS, seed=SEED):
    """Common block draws on the whole subset: per replicate, how many times each record enters."""
    nb = int(blk.max()) + 1
    rng = np.random.default_rng(seed)
    out = np.empty((reps, len(blk)), dtype=np.int32)
    for k in range(reps):
        cnt = np.bincount(rng.integers(0, nb, nb), minlength=nb)
        out[k] = cnt[blk]
    return out


def median_mult(vals, mult):
    """Median of vals repeated mult times (equal to np.median(np.repeat(vals, mult))); NaN if empty."""
    order = np.argsort(vals, kind="stable")
    v, m = np.asarray(vals)[order], np.asarray(mult)[order]
    n = int(m.sum())
    if n == 0:
        return np.nan
    c = np.cumsum(m)
    lo = v[np.searchsorted(c, (n - 1) // 2, side="right")]
    hi = v[np.searchsorted(c, n // 2, side="right")]
    return 0.5 * (lo + hi)


def stats(d, w, mult):
    n = int(mult.sum())
    if n == 0:
        return n, np.nan, np.nan, np.nan
    ww = w * mult
    return n, median_mult(d, mult), float(np.sum(ww * d) / np.sum(ww)), float(np.sum(mult * (np.abs(d) > BIG)) / n)


def summaries(groups, d, w, act_cls, M):
    """D5: for every group (boolean mask) and activity tercile (1, 2, 3, all): n, unweighted median, Phi-weighted
    mean, unweighted share |d| > 45, with percentile intervals from the common draws M."""
    rows = []
    for gname, gmask in groups:
        for t in (1, 2, 3, "all"):
            mask = gmask & ((act_cls == t) if t != "all" else True)
            idx = np.flatnonzero(mask)
            n0, med, mean, share = stats(d[idx], w[idx], np.ones(len(idx), int))
            row = dict(group=gname, A_tercile=str(t), n=n0, median=med, wmean=mean, share_big=share)
            boots = np.array([stats(d[idx], w[idx], M[k, idx])[1:] for k in range(M.shape[0])]) if len(idx) else \
                np.full((M.shape[0], 3), np.nan)
            valid = np.isfinite(boots[:, 0])
            row["valid_reps"], row["empty_reps"] = int(valid.sum()), int((~valid).sum())
            for j, s in enumerate(("median", "wmean", "share_big")):
                if valid.sum() >= MIN_VALID:
                    row[f"{s}_lo"], row[f"{s}_hi"] = np.quantile(boots[valid, j], [0.025, 0.975])
                    row[f"{s}_ci_note"] = ""
                else:
                    row[f"{s}_lo"] = row[f"{s}_hi"] = np.nan
                    row[f"{s}_ci_note"] = f"fewer than {MIN_VALID} valid replicates" if len(idx) else "empty group"
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- fits

def describe(sub):
    w = sub.phi_mwo.to_numpy(float)
    comp = lambda c: json.dumps({str(k): int(v) for k, v in sub[c].value_counts().sort_index().items()})  # noqa: E731
    return dict(n=len(sub), n_cr=int(sub.CR.astype(int).nunique()),
                n_blocks=int(len(np.unique((sub.CR.astype(int) - sub.CR.astype(int).min()) // BLOCK))) if len(sub) else 0,
                cycles=comp("cycle"), epochs=comp("epoch"), hemispheres=comp("hemisphere"),
                A_min=float(sub.A_main.min()) if len(sub) else np.nan, A_max=float(sub.A_main.max()) if len(sub) else np.nan,
                n_eff=float(w.sum() ** 2 / np.sum(w ** 2)) if len(sub) else np.nan)


def boundary(r):
    phi, kappa = r.get("phi", np.nan), r.get("kappa", np.nan)
    return dict(phi_at_bound=bool(np.isfinite(phi) and (phi <= 1e-9 or phi >= 0.98 - 1e-9)),
                kappa_at_bound=bool(np.isfinite(kappa) and abs(kappa) >= 0.98 - 1e-9))


def fit_row(kind, label, sub, ref_beta, ref_se, fit=None):
    fit = fit or A.s2_fit
    row = dict(kind=kind, label=label, **describe(sub))
    if len(sub) < MIN_FIT:
        row.update(identifiable=None, state=f"sotto soglia (n < {MIN_FIT})")
        return row
    names, Z, x3 = A.columns(sub)
    info, _ = A.reduce(names, Z, x3, sub.phi_mwo.to_numpy(float))
    row["identifiable"] = bool(info["identifiable"])
    r = fit(sub.reset_index(drop=True))
    row["state"] = r.get("state")
    row.update({k: r.get(k, np.nan) for k in FIT_KEYS})
    row.update(boundary(r))
    if np.isfinite(row.get("beta", np.nan)):
        row["delta_beta"] = row["beta"] - ref_beta
        row["delta_over_se_full"] = row["delta_beta"] / ref_se
    return row


def decomposition(sub):
    """D1 on the same records, order, weights, activity, sin|lat| and reduced matrix for all responses."""
    w = sub.phi_mwo.to_numpy(float)
    names, Z, x3 = A.columns(sub)
    info, Xr = A.reduce(names, Z, x3, w)
    g = A.g_row(Xr, w)
    gm, gw = sub.gamma_mwo.to_numpy(float), sub.gamma_wl.to_numpy(float)
    u = gm - gw
    d = A.axial(u)
    r = d - u
    out = dict(identifiable=bool(info["identifiable"]), n=len(sub),
               g_d=float(g @ d), g_gamma_mwo=float(g @ gm), g_gamma_wl=float(g @ gw), g_r=float(g @ r))
    out["identity_residual"] = out["g_d"] - (out["g_gamma_mwo"] - out["g_gamma_wl"] + out["g_r"])
    out["d_equals_saved_dwl_maxabs"] = float(np.max(np.abs(d - sub.d_wl.to_numpy(float))))
    neg, pos = r < -WRAP_TOL, r > WRAP_TOL
    out.update(wraps_total=int((neg | pos).sum()), wraps_r_minus180=int(neg.sum()), wraps_r_plus180=int(pos.sum()),
               g_r_from_minus180=float(g[neg] @ r[neg]), g_r_from_plus180=float(g[pos] @ r[pos]),
               wrap_tolerance=WRAP_TOL)
    codes, uniq = A.cell_codes(sub)
    for name, y in (("gamma_mwo", gm), ("gamma_wl", gw)):
        m = A.m_verdict(A.m_unit(sub, Xr, w, g, y, codes, uniq), 0.0)
        out[f"M_{name}"] = {k: m.get(k) for k in FIT_KEYS if k in m}          # nominal, not validated; no verdict
    out["note"] = ("nominal intervals of the components are not validated for these responses; the SEs are not "
                   "subtracted and the components are not independent; no verdict or T3 label for gamma_wl")
    return out


# ---------------------------------------------------------------- data and gates

CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
PRODUCTS = {
    "STAB": {"S1_DPD_SOURCES.csv", "S1_TABLE.csv", "S2_P1.json", "S2_P1_MATCHED.csv", "S3_HALE.csv", "S4.csv",
             "S4_DWL_ALL.csv", "S4_ISOLATION.csv", "STABILITY.json", "WL_TILTS.csv"},
    "EST": {"ESTIMATE.csv", "FINAL.json"},
    "REL": {"COLUMNS.csv", "COMPARISONS/S1_DPD_SOURCES.csv", "COMPARISONS/S1_TABLE.csv", "COMPARISONS/S2_P1.json",
            "COMPARISONS/S2_P1_MATCHED.csv", "COMPARISONS/S3_HALE.csv", "COMPARISONS/S4_DWL_ALL.csv",
            "COMPARISONS/WL_TILTS.csv", "EXCLUDED_MAGNETOGRAMS.csv", "JOY_BY_CYCLE.csv",
            "MWO_TILT_CATALOGUE_ALL_1974_2012.csv", "MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv", "README.md"},
}
# every file whose content enters the run (code, note, inputs, receipts); hashed before the computation and again
# before writing
INPUTS = ("docs/T3_MWO_S2_DIAGNOSIS_NOTE.md", "scripts/t3_mwo_s2_diagnosis.py", "scripts/t3_mwo_analysis.py",
          "scripts/t3_mwo_stability_extras.py", "python/sharpbl/p2d.py", "python/sharpbl/p2f_pilot.py",
          "python/sharpbl/p2f_validation.py", "results/T3_MWO_CATALOGUE_R4/DESIGN.csv",
          "results/T3_MWO_CATALOGUE_R4/META.json", "results/T3_MWO_STABILITY_R4/WL_TILTS.csv",
          "results/T3_MWO_STABILITY_R4/STABILITY.json", "results/T3_MWO_STABILITY_R4/META.json",
          "results/T3_MWO_ESTIMATE_R4/META.json", "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv",
          "results/MWO_TILT_CATALOGUE_RELEASE/META.json", "data/sharp/external_DPD_20261118/dailyDPD1974_2016.txt",
          "results/T3_MWO_STABILITY_R4_RECOUNT/RECEIPT.json", "results/T3_MWO_ESTIMATE_R4_RECOUNT/RECEIPT.json",
          "results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT/RECEIPT.json")


def strict_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def receipt_problem(path, key, meta_path):
    """Strict receipt: integer non-boolean counts, total > 0, passed == total, exactly `total` checks each with
    ok is True, partial is False, bound to the current META."""
    try:
        r = json.loads(Path(path).read_text())
        mh = sha(meta_path)
    except (OSError, ValueError) as exc:
        return f"{Path(path).parent.name}: unreadable ({type(exc).__name__})"
    if not isinstance(r, dict):
        return f"{Path(path).parent.name}: not an object"
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    if not (strict_int(p) and strict_int(t) and t > 0 and p == t):
        return f"{Path(path).parent.name}: counts not strict ({p!r}/{t!r})"
    if not (isinstance(ch, list) and len(ch) == t and all(isinstance(c, dict) and c.get("ok") is True for c in ch)):
        return f"{Path(path).parent.name}: checks not complete or not all ok is True"
    if r.get("partial") is not False:
        return f"{Path(path).parent.name}: partial not False"
    if r.get(key) != mh:
        return f"{Path(path).parent.name}: not bound to the current META"
    return None


def manifest_problems(folder, expected):
    try:
        m = json.loads((Path(folder) / "META.json").read_text())
    except (OSError, ValueError) as exc:
        return [f"{Path(folder).name}: META unreadable ({type(exc).__name__})"], {}
    ps = m.get("products_sha256")
    if not isinstance(ps, dict) or set(ps) != set(expected):
        return [f"{Path(folder).name}: product set differs from the expected one"], m
    probs = []
    for n, h in ps.items():
        try:
            if sha(Path(folder) / n) != h:
                probs.append(f"{Path(folder).name}/{n}: hash differs from META")
        except OSError:
            probs.append(f"{Path(folder).name}/{n}: missing")
    return probs, m


def chain_problems():
    probs = []
    for rec, key, src in ((STAB_REC, "stability_meta_sha256", STAB), (EST_REC, "estimate_meta_sha256", EST),
                          (REL_REC, "release_meta_sha256", REL)):
        p = receipt_problem(rec / "RECEIPT.json", key, src / "META.json")
        if p:
            probs.append(p)
    metas = {}
    for name, folder in (("STAB", STAB), ("EST", EST), ("REL", REL)):
        p, metas[name] = manifest_problems(folder, PRODUCTS[name])
        probs += p
    try:
        cat_meta = json.loads((CAT / "META.json").read_text())
        h_cat = sha(CAT / "META.json")
        if cat_meta.get("products_sha256", {}).get("DESIGN.csv") != sha(CAT / "DESIGN.csv"):
            probs.append("DESIGN.csv not bound to the catalogue META")
        links = [(metas.get("STAB", {}).get("catalogue_meta_sha256"), h_cat, "stability -> catalogue"),
                 (metas.get("STAB", {}).get("script_sha256"), sha(ROOT / "scripts/t3_mwo_analysis.py"), "stability -> analysis script"),
                 (metas.get("STAB", {}).get("extras_sha256"), sha(ROOT / "scripts/t3_mwo_stability_extras.py"), "stability -> extras"),
                 (metas.get("EST", {}).get("stability_meta_sha256"), sha(STAB / "META.json"), "estimate -> stability"),
                 (metas.get("EST", {}).get("catalogue_meta_sha256"), h_cat, "estimate -> catalogue"),
                 (metas.get("REL", {}).get("catalogue_meta_sha256"), h_cat, "release -> catalogue"),
                 (metas.get("REL", {}).get("stability_meta_sha256"), sha(STAB / "META.json"), "release -> stability"),
                 (metas.get("REL", {}).get("estimate_meta_sha256"), sha(EST / "META.json"), "release -> estimate"),
                 (metas.get("REL", {}).get("estimate_recount_receipt_sha256"), sha(EST_REC / "RECEIPT.json"),
                  "release -> estimate recount")]
        probs += [f"stale link: {what}" for have, want, what in links if have != want]
    except (OSError, ValueError, AttributeError) as exc:
        probs.append(f"catalogue or links unreadable ({type(exc).__name__})")
    return probs


def input_hashes():
    out = {}
    for p in INPUTS:
        try:
            out[p] = sha(ROOT / p)
        except OSError:
            out[p] = None
    return out


def load_subset():
    d = A.load_design()
    wl = pd.read_csv(STAB / "WL_TILTS.csv", dtype={"noaa": str}, float_precision="round_trip")
    if len(wl) != len(d) or not (wl.noaa.to_numpy() == d.noaa.to_numpy()).all() or not (wl.day.to_numpy() == d.day.to_numpy()).all():
        raise ValueError("WL_TILTS does not align with the design")
    d["gamma_wl"], d["d_wl"], d["wl_status"] = wl.gamma_wl.to_numpy(), wl.d_wl.to_numpy(), wl.wl_status.to_numpy()
    rel = pd.read_csv(REL / "MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv", dtype={"noaa": str}, float_precision="round_trip")
    if rel.duplicated(["noaa", "day_utc"]).any():
        raise ValueError("release keys not unique")
    m = d.merge(rel[["noaa", "day_utc", "joy_gamma_deg", "separation_deg"]], left_on=["noaa", "day"],
                right_on=["noaa", "day_utc"], how="left", validate="one_to_one")
    if m.joy_gamma_deg.isna().any():
        raise ValueError("design rows without a release row")
    d["gamma_mwo"], d["separation"] = m.joy_gamma_deg.to_numpy(), m.separation_deg.to_numpy()
    sub = d[d.wl_status == "ok"].reset_index(drop=True)
    if len(sub) != N_S2:
        raise ValueError(f"S2 subset has {len(sub)} rows, expected {N_S2}")
    return sub


def removed(item, label, big, mask):
    den = int(mask.sum())
    n = int((big & mask).sum())
    return dict(item=item, label=label, n=n, share=(n / den) if den else np.nan,
                share_note="" if den else "empty denominator")


def build(sub, src, ref, reps=REPS):
    """All products from the S2 subset; src maps day -> DPD source code; ref = (beta, se) of the full S2."""
    rb, rs = ref
    fits = [fit_row("full", "S2 complete", sub, rb, rs)]
    fits += [fit_row("leave-one-epoch-out", f"without {e}", sub[sub.epoch != e], rb, rs) for e in LOO_EPOCHS]
    source = np.array([src.get(x, "(missing)") for x in sub.day])
    alpha = np.array([s.isalpha() for s in source])
    gyul, other, nosrc = source == "GYUL", alpha & (source != "GYUL"), ~alpha
    fits += [fit_row("subset", "source GYUL", sub[gyul], rb, rs), fit_row("subset", "source other", sub[other], rb, rs)]
    edges, classes = {}, {}
    for name, col in D4_VARS:
        edges[name] = tercile_edges(sub[col])
        classes[name] = tercile_class(sub[col], edges[name])
        fits += [fit_row("subset", f"{name} tercile {t}", sub[classes[name] == t], rb, rs) for t in (1, 2, 3)]
    big = np.abs(sub.d_wl.to_numpy(float)) > BIG
    fits.append(fit_row("sensitivity", f"without |d_WL| > {BIG:g}", sub[~big], rb, rs))
    edges["A_main"] = tercile_edges(sub.A_main)
    a_cls = tercile_class(sub.A_main, edges["A_main"])
    hem = sub.hemisphere.to_numpy()
    groups = [("all", np.ones(len(sub), bool)), ("N", hem == "N"), ("S", hem == "S")]
    groups += [(f"without {e}", (sub.epoch != e).to_numpy()) for e in LOO_EPOCHS]
    groups += [("source GYUL", gyul), ("source other", other), ("source missing or non-alphabetic", nosrc)]
    groups += [(f"{name} tercile {t}", classes[name] == t) for name, _ in D4_VARS for t in (1, 2, 3)]
    M = multiplicities(block_ids(sub.CR), reps)
    summ = summaries(groups, sub.d_wl.to_numpy(float), sub.phi_mwo.to_numpy(float), a_cls, M)
    counts = [dict(item="source", label=s, n=int((source == s).sum())) for s in sorted(set(source))]
    counts += [dict(item=f"tercile {k}", label=str(t), n=int(((a_cls if k == "A_main" else classes[k]) == t).sum()))
               for k in ["A_main"] + [n for n, _ in D4_VARS] for t in (1, 2, 3)]
    counts += [dict(item=f"tercile edges {k}", label=json.dumps([float(x) for x in v]), n=None) for k, v in edges.items()]
    counts += [removed("removed |d_WL|>45 by A tercile", str(t), big, a_cls == t) for t in (1, 2, 3)]
    counts += [removed("removed |d_WL|>45 by hemisphere", h, big, hem == h) for h in ("N", "S")]
    return dict(FITS=pd.DataFrame(fits), DECOMPOSITION=decomposition(sub), SUMMARIES=summ, COUNTS=pd.DataFrame(counts))


def write_atomic(out, prods, meta):
    out = Path(out)
    if out.exists():
        sys.exit("refusing to overwrite")
    tmp = out.parent / f".{out.name}.tmp-{os.getpid()}"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    prods["FITS"].to_csv(tmp / "FITS.csv", index=False)
    prods["SUMMARIES"].to_csv(tmp / "SUMMARIES.csv", index=False)
    prods["COUNTS"].to_csv(tmp / "COUNTS.csv", index=False)
    (tmp / "DECOMPOSITION.json").write_text(json.dumps(prods["DECOMPOSITION"], indent=2) + "\n")
    meta = dict(meta, products_sha256={f.name: sha(f) for f in sorted(tmp.iterdir())})
    (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    os.rename(tmp, out)


def seed_collisions(seed=SEED):
    grid = set(A.grid_seeds())
    return dict(in_grid=seed in grid, grid_size=len(grid), in_used=any(lo <= seed < hi for lo, hi in A.USED),
                equals_s1=seed == A.SEED_S1, equals_joy=seed == JOY_SEED)


def run():
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()  # noqa: E731
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("tracked tree not clean")
    for p in INPUTS[:7]:                                   # note, scripts and modules must be committed
        if git("ls-files", p) == "":
            sys.exit(f"{p} not committed")
    before = input_hashes()
    if any(h is None for h in before.values()):
        sys.exit("missing inputs: " + ", ".join(p for p, h in before.items() if h is None))
    probs = chain_problems()
    if probs:
        sys.exit("chain problems: " + "; ".join(probs))
    sc = seed_collisions()
    if sc["in_grid"] or sc["in_used"] or sc["equals_s1"] or sc["equals_joy"] or sc["grid_size"] != 76_000:
        sys.exit(f"seed problem {sc}")
    sub = load_subset()
    st = json.loads((STAB / "STABILITY.json").read_text())["S2"]
    ref = (st["beta"], st["se"])
    check = A.s2_fit(sub)
    if not all(abs(check[k] - st[k]) <= 1e-9 for k in ("beta", "se", "lo", "hi")):
        sys.exit("s2_fit on the rebuilt subset does not reproduce STABILITY.json")
    if np.max(np.abs(A.axial(sub.gamma_mwo - sub.gamma_wl) - sub.d_wl)) > 1e-9:
        sys.exit("axial(gamma_mwo - gamma_wl) differs from the saved d_WL")
    prods = build(sub, EX.daily_sources(), ref)
    after = input_hashes()
    if after != before or git("status", "--porcelain", "--untracked-files=no") or chain_problems():
        sys.exit("inputs, tracked tree or chain changed during the computation: nothing written")
    meta = dict(note_sha256=before[INPUTS[0]], script_sha256=before[INPUTS[1]], inputs_sha256=before,
                inputs_hashed="before the computation and again before writing (identical)",
                git_commit=git("rev-parse", "HEAD"), seed=SEED, reps=REPS, seed_check=sc,
                s2_reference=dict(beta=ref[0], se=ref[1]), sealed_read=False, post_hoc=True, changes_outcome=False)
    write_atomic(OUT, prods, meta)
    print(f"written {OUT}")
    return 0


# ---------------------------------------------------------------- selftest (synthetic data only)

def synthetic(n=900, seed=7):
    rng = np.random.default_rng(seed)
    cr = np.sort(rng.integers(1700, 1700 + 120, n))
    ep = np.where(cr < 1730, "E2", np.where(cr < 1760, "E3", np.where(cr < 1790, "E5", "E8")))
    hem = rng.choice(["N", "S"], n)
    s = np.sin(np.radians(rng.uniform(5, 35, n)))
    d = pd.DataFrame(dict(noaa=[str(i) for i in range(n)], day=pd.Timestamp("1980-01-01") + pd.to_timedelta(cr - 1700, "D") * 27,
                          CR=cr, epoch=ep, hemisphere=hem, sinlat=s, phi_mwo=10 ** rng.uniform(20, 22, n),
                          cycle=np.where(cr < 1760, 21, 22), A_main=rng.uniform(0.2, 2.0, n),
                          dpd_area=rng.integers(1, 500, n).astype(float), separation=rng.uniform(1, 10, n)))
    d["day"] = d.day.dt.strftime("%Y-%m-%d")
    d["gamma_mwo"] = 24 * s + rng.normal(0, 15, n)
    d["gamma_wl"] = 20 * s + rng.normal(0, 20, n)
    d["d_wl"] = A.axial(d.gamma_mwo - d.gamma_wl)
    return d


def synthetic_chain(base, mutate=None):
    """Builds a minimal valid chain under `base`, applies `mutate`, runs chain_problems() on it, restores globals."""
    g = globals()
    saved = {k: g[k] for k in ("CAT", "STAB", "EST", "REL", "STAB_REC", "EST_REC", "REL_REC")}
    dirs = {k: Path(base) / k for k in saved}
    try:
        for d in dirs.values():
            d.mkdir(parents=True)
        (dirs["CAT"] / "DESIGN.csv").write_text("design\n")
        (dirs["CAT"] / "META.json").write_text(json.dumps({"products_sha256": {"DESIGN.csv": sha(dirs["CAT"] / "DESIGN.csv")}}))
        h_cat = sha(dirs["CAT"] / "META.json")

        def products(folder, names, extra):
            for n in names:
                (folder / n).parent.mkdir(parents=True, exist_ok=True)
                (folder / n).write_text(n)
            (folder / "META.json").write_text(json.dumps(dict(extra, products_sha256={n: sha(folder / n) for n in names})))

        def receipt(folder, key, meta, n=3):
            (folder / "RECEIPT.json").write_text(json.dumps(dict(passed=n, total=n, partial=False, checks=[dict(name=str(i), ok=True)
                                                                                                         for i in range(n)], **{key: sha(meta)})))

        products(dirs["STAB"], PRODUCTS["STAB"], dict(catalogue_meta_sha256=h_cat, script_sha256=sha(ROOT / "scripts/t3_mwo_analysis.py"),
                                                       extras_sha256=sha(ROOT / "scripts/t3_mwo_stability_extras.py")))
        receipt(dirs["STAB_REC"], "stability_meta_sha256", dirs["STAB"] / "META.json")
        products(dirs["EST"], PRODUCTS["EST"], dict(stability_meta_sha256=sha(dirs["STAB"] / "META.json"), catalogue_meta_sha256=h_cat))
        receipt(dirs["EST_REC"], "estimate_meta_sha256", dirs["EST"] / "META.json")
        products(dirs["REL"], PRODUCTS["REL"], dict(catalogue_meta_sha256=h_cat, stability_meta_sha256=sha(dirs["STAB"] / "META.json"),
                                                     estimate_meta_sha256=sha(dirs["EST"] / "META.json"),
                                                     estimate_recount_receipt_sha256=sha(dirs["EST_REC"] / "RECEIPT.json")))
        receipt(dirs["REL_REC"], "release_meta_sha256", dirs["REL"] / "META.json")
        if mutate:
            mutate(dirs)
        g.update(dirs)
        return chain_problems()
    finally:
        g.update(saved)


def chain_cases():
    def rec(name, **kw):
        def f(d):
            p = d[name] / "RECEIPT.json"
            r = json.loads(p.read_text())
            r.update(kw)
            p.write_text(json.dumps(r))
        return f

    def write(path_fn, text):
        return lambda d: path_fn(d).write_text(text)

    def empty_manifest(d):
        p = d["EST"] / "META.json"
        m = json.loads(p.read_text())
        m["products_sha256"] = {}
        p.write_text(json.dumps(m))

    def stale_link(d):
        p = d["REL"] / "META.json"
        m = json.loads(p.read_text())
        m["stability_meta_sha256"] = "0" * 64
        p.write_text(json.dumps(m))
        rec("REL_REC", release_meta_sha256=sha(p))(d)

    return [("valid synthetic chain accepted", None, True),
            ("receipt 0/0 with no checks refused", rec("STAB_REC", passed=0, total=0, checks=[]), False),
            ("boolean counts refused", rec("EST_REC", passed=True, total=True, checks=[dict(ok=True)]), False),
            ("check with ok not boolean refused", rec("REL_REC", checks=[dict(ok="yes")] * 3), False),
            ("partial receipt refused", rec("STAB_REC", partial=True), False),
            ("empty product manifest refused", empty_manifest, False),
            ("modified stability product refused", write(lambda d: d["STAB"] / "WL_TILTS.csv", "changed"), False),
            ("modified estimate product refused", write(lambda d: d["EST"] / "FINAL.json", "changed"), False),
            ("modified design refused", write(lambda d: d["CAT"] / "DESIGN.csv", "changed"), False),
            ("stale link refused", stale_link, False),
            ("missing receipt refused", lambda d: (d["EST_REC"] / "RECEIPT.json").unlink(), False)]


def selftest():
    import tempfile
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    # axial cut and wraps in both directions
    u = np.array([90.0, 100.0, -100.0, 30.0, -90.0])
    dd = A.axial(u)
    r = dd - u
    ok("axial: +90 -> -90 (r = -180), 100 -> -80 (r = -180), -100 -> 80 (r = +180), no wrap at 30 and -90",
       np.allclose(dd, [-90, -80, 80, 30, -90]) and np.allclose(r, [-180, -180, 180, 0, 0]))
    sub = synthetic()
    dec = decomposition(sub)
    ok("D1 identity with wraps (synthetic)", abs(dec["identity_residual"]) < 1e-9 and dec["wraps_total"] > 0
       and dec["wraps_r_minus180"] + dec["wraps_r_plus180"] == dec["wraps_total"], (dec["wraps_total"], dec["identity_residual"]))
    s0 = sub.copy()
    s0["gamma_wl"] = s0.gamma_mwo - 10.0
    s0["d_wl"] = A.axial(s0.gamma_mwo - s0.gamma_wl)
    d0 = decomposition(s0)
    ok("D1 without wraps: g r ~ 0 (rounding only) and g d = g gamma_mwo - g gamma_wl", d0["wraps_total"] == 0 and abs(d0["g_r"]) < 1e-9
       and abs(d0["g_d"] - (d0["g_gamma_mwo"] - d0["g_gamma_wl"])) < 1e-9)
    s9 = sub.copy()
    s9.loc[:4, "gamma_wl"] = s9.loc[:4, "gamma_mwo"] - 90.0
    s9["d_wl"] = A.axial(s9.gamma_mwo - s9.gamma_wl)
    d9 = decomposition(s9)
    ok("D1 at the +90 cut: counted as r = -180", d9["wraps_r_minus180"] >= 5 and abs(d9["identity_residual"]) < 1e-9)
    ok("D1 components: no verdict field", "verdict" not in dec["M_gamma_mwo"] and "verdict" not in dec["M_gamma_wl"])
    # terciles with ties and an empty tercile
    x = np.array([1, 1, 1, 1, 2, 2, 3, 3, 3])
    e = tercile_edges(x)
    c = tercile_class(x, e)
    ok("terciles: ties never split", all(len(set(c[x == v])) == 1 for v in set(x)), (e.tolist(), c.tolist()))
    xe = np.array([5.0] * 9)
    ce = tercile_class(xe, tercile_edges(xe))
    ok("terciles: all equal -> one class, others empty (declared by counts)", set(ce) == {3})
    # weighted-median helper equals np.median(np.repeat)
    rng = np.random.default_rng(1)
    good = True
    for _ in range(200):
        v, m = rng.normal(size=11), rng.integers(0, 4, 11)
        exp = np.median(np.repeat(v, m)) if m.sum() else np.nan
        got = median_mult(v, m)
        good &= (np.isnan(exp) and np.isnan(got)) or abs(exp - got) < 1e-12
    ok("median with multiplicities equals np.median(np.repeat)", good)
    # bootstrap: empty replicates and the 1900 threshold
    blk = np.array([0, 0, 1, 1, 2])
    Mm = multiplicities(blk, reps=300, seed=3)
    mask = np.array([False, False, False, False, True])
    sm = summaries([("tiny", mask)], np.arange(5.0), np.ones(5), np.array([1, 1, 2, 2, 3]), Mm)
    row = sm[(sm.group == "tiny") & (sm.A_tercile == "all")].iloc[0]
    ok("bootstrap: empty replicates counted, no interval below 1900 valid", row.empty_reps > 0 and np.isnan(row.median_lo)
       and row.valid_reps + row.empty_reps == 300, (row.valid_reps, row.empty_reps))
    M1 = multiplicities(blk, reps=5, seed=SEED)
    M2 = multiplicities(blk, reps=5, seed=SEED)
    ok("bootstrap: draws reproducible from the seed, blocks kept whole", (M1 == M2).all()
       and all(len(set(r[blk == b])) == 1 for r in M1 for b in range(3)))
    # fits: below threshold, non-identifiable, full run on synthetic data
    small = sub.iloc[:120]
    fr = fit_row("subset", "small", small, 0.0, 1.0)
    ok("fit below 300 records: explicit row, not fitted", fr["state"].startswith("sotto soglia") and "beta" not in fr)
    ni = sub.copy()
    ni["A_main"] = 1.0                                                   # x3 = 0: beta3 not identifiable
    fn = fit_row("subset", "flat activity", ni, 0.0, 1.0)
    ok("fit not identifiable: explicit row with its state", fn["identifiable"] is False and fn["state"] == "non identificabile", fn["state"])
    src = {dday: ("GYUL" if i % 3 else "DEBR") for i, dday in enumerate(sorted(set(sub.day)))}
    src[sorted(set(sub.day))[0]] = "(none)"
    ref = A.s2_fit(sub)
    prods = build(sub, src, (ref["beta"], ref["se"]), reps=50)
    F = prods["FITS"]
    ok("build: 1 full + 6 leave-one-epoch-out + 2 source + 9 tercile + 1 sensitivity rows", len(F) == 19
       and (F.kind == "leave-one-epoch-out").sum() == 6 and (F.kind == "subset").sum() == 11, len(F))
    full = F.iloc[0]
    ok("full row reproduces s2_fit, delta 0", abs(full.beta - ref["beta"]) < 1e-12 and abs(full.delta_beta) < 1e-12)
    ok("no ±C flag and no verdict column", not any(c in F.columns for c in ("verdict", "within_C", "covered")))
    S = prods["SUMMARIES"]
    ok("summaries: 21 groups x 4 activity classes", len(S) == 21 * 4 and S.group.nunique() == 21, len(S))
    C = prods["COUNTS"]
    ok("counts: missing or non-alphabetic source counted", ((C.item == "source") & (C.label == "(none)")).any())
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "o"
        write_atomic(out, prods, dict(test=True))
        meta = json.loads((out / "META.json").read_text())
        ok("atomic write: products hashed, no temporary folder left", set(meta["products_sha256"]) ==
           {"FITS.csv", "SUMMARIES.csv", "COUNTS.csv", "DECOMPOSITION.json"} and not list(Path(td).glob(".o.tmp*")))
        try:
            write_atomic(out, prods, {})
            ok("refuses to overwrite", False)
        except SystemExit:
            ok("refuses to overwrite", True)
    # strict chain guards on a synthetic chain (no real product touched)
    ok("removed share with an empty denominator: missing with cause, not 0",
       np.isnan(removed("x", "1", np.array([True]), np.array([False]))["share"])
       and removed("x", "1", np.array([True]), np.array([False]))["share_note"] == "empty denominator")
    with tempfile.TemporaryDirectory() as td:
        for label, mutate, expect_ok in chain_cases():
            probs = synthetic_chain(Path(td) / label, mutate)
            ok(f"chain guard: {label}", (not probs) == expect_ok, probs[:2])
    sc = seed_collisions()
    joy_src =(ROOT / "scripts/t3_mwo_catalogue_release.py").read_text()
    ok("seed 69 600 001 against the 76 000 grid seeds, USED, S1 and Joy", sc["grid_size"] == 76_000 and not any(
        sc[k] for k in ("in_grid", "in_used", "equals_s1", "equals_joy")) and re.search(r"JOY_SEED[^=]*=\s*69_500_001", joy_src), sc)
    src_txt = Path(__file__).read_text().split("def selftest")[0]
    ok("SEALED never read", "SEALED.csv" not in src_txt.replace("SEALED.csv.gz is never read", ""))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (run() if a.run else 1))
