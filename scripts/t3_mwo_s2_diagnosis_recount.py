"""Independent recount of the descriptive S2 diagnosis (docs/T3_MWO_S2_DIAGNOSIS_NOTE.md).

Own code for: the S2 subset (join of DESIGN, WL_TILTS and the verified release), the design matrix and its reduction,
the WLS row g of beta3, the D1 identity with the axial term and the wraps, the point estimate of every fit, the
groups, terciles and record losses, and the D5 summaries replaying the same block draws. Standard errors and
intervals of procedure M are recomputed through the common s2_fit of scripts/t3_mwo_analysis.py: a DECLARED
DEPENDENCY, not an independent verification of the SE. SEALED.csv.gz is never read.

    .venv/bin/python scripts/t3_mwo_s2_diagnosis_recount.py --selftest
    .venv/bin/python scripts/t3_mwo_s2_diagnosis_recount.py --check
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs/T3_MWO_S2_DIAGNOSIS_NOTE.md"
OUT = ROOT / "results/T3_MWO_S2_DIAGNOSIS_R4"
REC = ROOT / "results/T3_MWO_S2_DIAGNOSIS_R4_RECOUNT"
DESIGN = ROOT / "results/T3_MWO_CATALOGUE_R4/DESIGN.csv"
WL = ROOT / "results/T3_MWO_STABILITY_R4/WL_TILTS.csv"
STABJ = ROOT / "results/T3_MWO_STABILITY_R4/STABILITY.json"
RELT = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
DAILY = ROOT / "data/sharp/external_DPD_20261118/dailyDPD1974_2016.txt"
EPOCHS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")
LOO = ("E2", "E3", "E4", "E5", "E6", "E8")
SEED, REPS, BLOCK, MIN_VALID, MIN_FIT, BIG = 69_600_001, 2000, 6, 1900, 300, 45.0
TOL_BETA, TOL_STAT = 1e-8, 1e-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- own subset, sources, design, g

def own_subset():
    d = pd.read_csv(DESIGN, dtype={"noaa": str})
    d = d[d.record_set == "isolated"].reset_index(drop=True)
    wl = pd.read_csv(WL, dtype={"noaa": str}, float_precision="round_trip")
    assert list(zip(wl.noaa, wl.day)) == list(zip(d.noaa, d.day)), "WL_TILTS order"
    rel = pd.read_csv(RELT, dtype={"noaa": str}, float_precision="round_trip").set_index(["noaa", "day_utc"])
    assert rel.index.is_unique
    key = pd.MultiIndex.from_arrays([d.noaa, d.day])
    d["gamma_mwo"] = rel.loc[key, "joy_gamma_deg"].to_numpy()
    d["separation"] = rel.loc[key, "separation_deg"].to_numpy()
    d["gamma_wl"], d["d_wl"] = wl.gamma_wl.to_numpy(), wl.d_wl.to_numpy()
    return d[wl.wl_status.to_numpy() == "ok"].reset_index(drop=True)


def own_sources():
    out = {}
    for line in DAILY.read_text().splitlines():
        t = line.split()
        if line.startswith("d ") and len(t) >= 12:
            out["-".join(t[1:4])] = t[7] if t[7].isalpha() else "(none)"
    return out


def own_design(d):
    """Columns as in the protocol (cycle x hemisphere Joy terms, epoch x hemisphere Joy shifts with the most populated
    epoch of each hemisphere as reference), greedy weighted-rank reduction in that order, target last."""
    s, cyc, hem, ep = d.sinlat.to_numpy(float), d.cycle.to_numpy(), d.hemisphere.to_numpy(), d.epoch.to_numpy()
    sw = np.sqrt(d.phi_mwo.to_numpy(float))
    cols = [s * ((cyc == c) & (hem == h)) for c in sorted(set(cyc)) for h in ("N", "S") if ((cyc == c) & (hem == h)).any()]
    for e in EPOCHS:
        for h in ("N", "S"):
            m = (ep == e) & (hem == h)
            hh = d[hem == h].epoch.value_counts()
            ref = sorted(hh.index, key=lambda x: (-hh[x], EPOCHS.index(x)))[0] if len(hh) else None
            if m.any() and e != ref:
                cols.append(s * m)
    kept = np.zeros((len(d), 0))
    for c in cols:
        t = np.column_stack([kept, c])
        if np.any(c != 0) and np.linalg.matrix_rank(t * sw[:, None]) > kept.shape[1]:
            kept = t
    x3 = (d.A_main.to_numpy(float) - 1.0) * s
    X = np.column_stack([kept, x3])
    ident = np.linalg.matrix_rank(X * sw[:, None]) == X.shape[1]
    return X, bool(ident)


def own_g(d):
    X, ident = own_design(d)
    if not ident:
        return None
    sw = np.sqrt(d.phi_mwo.to_numpy(float))
    return np.linalg.pinv(X * sw[:, None])[-1] * sw                     # beta3 = g @ y


def axial(x):
    return (np.asarray(x, float) + 90.0) % 180.0 - 90.0


# ---------------------------------------------------------------- own D5

def own_draws(cr, reps=REPS, seed=SEED):
    cr = np.asarray(cr).astype(int)
    raw = (cr - cr.min()) // BLOCK
    labels = np.unique(raw)
    members = [np.flatnonzero(raw == b) for b in labels]
    rng = np.random.default_rng(seed)
    for _ in range(reps):
        yield np.concatenate([members[i] for i in rng.integers(0, len(labels), len(labels))])


def own_stats(dv, wv):
    if len(dv) == 0:
        return np.nan, np.nan, np.nan
    return float(np.median(dv)), float(np.sum(wv * dv) / np.sum(wv)), float(np.mean(np.abs(dv) > BIG))


def own_terc(x, ref):
    q = np.quantile(np.asarray(ref, float), [1 / 3, 2 / 3])
    x = np.asarray(x, float)
    return np.where(x < q[0], 1, np.where(x < q[1], 2, 3))             # == searchsorted(q, x, 'right') + 1


def own_groups(d, src):
    s = np.array([src.get(x, "(missing)") for x in d.day])
    alpha = np.array([v.isalpha() for v in s])
    g = {"all": np.ones(len(d), bool), "N": (d.hemisphere == "N").to_numpy(), "S": (d.hemisphere == "S").to_numpy()}
    g.update({f"without {e}": (d.epoch != e).to_numpy() for e in LOO})
    g.update({"source GYUL": s == "GYUL", "source other": alpha & (s != "GYUL"), "source missing or non-alphabetic": ~alpha})
    for name in ("dpd_area", "phi_mwo", "separation"):
        t = own_terc(d[name], d[name])
        g.update({f"{name} tercile {k}": t == k for k in (1, 2, 3)})
    return g, s


# ---------------------------------------------------------------- check

# own list of the run inputs (written independently of the runner's INPUTS)
EXPECTED_INPUTS = {
    "docs/T3_MWO_S2_DIAGNOSIS_NOTE.md", "scripts/t3_mwo_s2_diagnosis.py", "scripts/t3_mwo_analysis.py",
    "scripts/t3_mwo_stability_extras.py", "python/sharpbl/p2d.py", "python/sharpbl/p2f_pilot.py",
    "python/sharpbl/p2f_validation.py", "results/T3_MWO_CATALOGUE_R4/DESIGN.csv", "results/T3_MWO_CATALOGUE_R4/META.json",
    "results/T3_MWO_STABILITY_R4/WL_TILTS.csv", "results/T3_MWO_STABILITY_R4/STABILITY.json",
    "results/T3_MWO_STABILITY_R4/META.json", "results/T3_MWO_ESTIMATE_R4/META.json",
    "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv",
    "results/MWO_TILT_CATALOGUE_RELEASE/META.json", "data/sharp/external_DPD_20261118/dailyDPD1974_2016.txt",
    "results/T3_MWO_STABILITY_R4_RECOUNT/RECEIPT.json", "results/T3_MWO_ESTIMATE_R4_RECOUNT/RECEIPT.json",
    "results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT/RECEIPT.json"}
M_KEYS = ("beta", "se", "lo", "hi", "var_a", "var_b", "phi", "kappa", "sigma_x2")
PRODUCT_SET = {"FITS.csv", "SUMMARIES.csv", "COUNTS.csv", "DECOMPOSITION.json"}


def close(a, b, tol):
    a = np.nan if a is None else float(a)
    b = np.nan if b is None else float(b)
    return (np.isnan(a) and np.isnan(b)) or abs(a - b) <= tol


def note_str(v):
    return "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def bool_or_none(v):
    s = note_str(v)
    return None if s == "" else (s == "True")


def own_comp(ss, col):
    return {str(k): int(v) for k, v in ss[col].value_counts().sort_index().items()}


def git_out(*a):
    import subprocess
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def inputs_problem(inp, root=ROOT, expected=EXPECTED_INPUTS):
    if not isinstance(inp, dict) or set(inp) != set(expected):
        return "declared input set differs"
    for p, h in inp.items():
        try:
            if h is None or sha(Path(root) / p) != h:
                return f"{p} changed or missing"
        except OSError:
            return f"{p} missing"
    return None


def component_m(AN):
    """Common procedure M for a component response on the S2 design (declared dependency)."""
    def f(sub, y):
        w = sub.phi_mwo.to_numpy(float)
        names, Z, x3 = AN.columns(sub)
        _, Xr = AN.reduce(names, Z, x3, w)
        codes, uniq = AN.cell_codes(sub)
        m = AN.m_verdict(AN.m_unit(sub, Xr, w, AN.g_row(Xr, w), y, codes, uniq), 0.0)
        return {k: m[k] for k in M_KEYS + ("error",) if k in m}
    return f


def check(out=OUT, sub=None, src=None, s2_ref=None, fit=None, mfit=None, reps=REPS, write=True, rec=REC, note=NOTE):
    """Full receipt (partial False) only on the real path: real subset and sources rebuilt here, REPS draws, M through
    the common procedure, note and outputs committed. Any injected data, reduced draws, missing note or missing M
    gives partial True."""
    checks = []
    if mfit is None:                             # the component check always runs, through the common procedure
        spec = importlib.util.spec_from_file_location("t3_mwo_analysis_dep", ROOT / "scripts/t3_mwo_analysis.py")
        AN = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(AN)
        mfit = component_m(AN)
    real = sub is None and reps == REPS and fit is not None and note is not None

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:200]}")

    out = Path(out)
    meta = json.loads((out / "META.json").read_text())
    ps = meta.get("products_sha256")
    ok("products match META (exact set)", isinstance(ps, dict) and set(ps) == PRODUCT_SET
       and all(sha(out / n) == h for n, h in ps.items()))
    if note is not None:
        ok("note SHA in META equals the current note", meta.get("note_sha256") == sha(note))
    if real:
        inp = meta.get("inputs_sha256")
        ok("inputs: exact declared set, hashes unchanged since the run", inputs_problem(inp) is None, inputs_problem(inp))
        ok("note and script in META equal the declared inputs", meta.get("note_sha256") == (inp or {}).get(
            "docs/T3_MWO_S2_DIAGNOSIS_NOTE.md") and meta.get("script_sha256") == (inp or {}).get("scripts/t3_mwo_s2_diagnosis.py"))
        rel = str(out.relative_to(ROOT))
        c1, tracked = git_out("ls-files", rel)
        c2, _ = git_out("diff", "--quiet", "HEAD", "--", rel)
        c3, notec = git_out("ls-files", str(Path(note).relative_to(ROOT)))
        c4, _ = git_out("diff", "--quiet", "HEAD", "--", str(Path(note).relative_to(ROOT)))
        ok("outputs and note committed and unchanged in Git", c1 == 0 and set(tracked.splitlines()) ==
           {f"{rel}/{n}" for n in PRODUCT_SET | {"META.json"}} and c2 == 0 and notec != "" and c4 == 0)
        sub, src = own_subset(), own_sources()
        s2 = json.loads(STABJ.read_text())["S2"]
        s2_ref = (s2["beta"], s2["se"])
        ok("S2 subset size", len(sub) == 4694, len(sub))
    F = pd.read_csv(out / "FITS.csv")
    S = pd.read_csv(out / "SUMMARIES.csv", dtype={"A_tercile": str})
    C = pd.read_csv(out / "COUNTS.csv", dtype={"label": str})
    D = json.loads((out / "DECOMPOSITION.json").read_text())
    # D1 -----------------------------------------------------------------
    g = own_g(sub)
    gm, gw = sub.gamma_mwo.to_numpy(float), sub.gamma_wl.to_numpy(float)
    u = gm - gw
    dd = axial(u)
    r = dd - u
    neg, pos = r < -1e-9, r > 1e-9
    terms = dict(g_d=g @ dd, g_gamma_mwo=g @ gm, g_gamma_wl=g @ gw, g_r=g @ r,
                 g_r_from_minus180=g[neg] @ r[neg], g_r_from_plus180=g[pos] @ r[pos])
    ok("D1 terms with an own g (incl. the axial term by sign)", all(close(terms[k], D.get(k), TOL_BETA) for k in terms),
       {k: round(float(v), 6) for k, v in terms.items()})
    ok("D1 identity g d = g mwo - g wl + g r", abs(terms["g_d"] - (terms["g_gamma_mwo"] - terms["g_gamma_wl"] + terms["g_r"])) < 1e-9
       and close(D.get("identity_residual"), terms["g_d"] - (D["g_gamma_mwo"] - D["g_gamma_wl"] + D["g_r"]), 1e-12))
    ok("D1 n, identifiability, tolerance, wraps by sign, saved d max deviation",
       D.get("n") == len(sub) and D.get("identifiable") is True and D.get("wrap_tolerance") == 1e-9
       and D.get("wraps_r_minus180") == int(neg.sum()) and D.get("wraps_r_plus180") == int(pos.sum())
       and D.get("wraps_total") == int((neg | pos).sum())
       and close(D.get("d_equals_saved_dwl_maxabs"), np.max(np.abs(dd - sub.d_wl.to_numpy(float))), 1e-12)
       and D["d_equals_saved_dwl_maxabs"] < 1e-9, (int(neg.sum()), int(pos.sum())))
    ok("D1 components carry no verdict", all(isinstance(D.get(k), dict) and "verdict" not in D[k] for k in ("M_gamma_mwo", "M_gamma_wl")))
    if mfit is not None:
        good = True
        for name, y in (("gamma_mwo", gm), ("gamma_wl", gw)):
            m = mfit(sub, y)
            good &= all(close(m.get(k), D[f"M_{name}"].get(k), 1e-9) for k in M_KEYS) and \
                set(D[f"M_{name}"]) == {k for k in m if k in M_KEYS + ("error",)}
        ok("D1 components: all M fields (common procedure: declared dependency)", good)
    # FITS ---------------------------------------------------------------
    groups, srcs = own_groups(sub, src)
    big = np.abs(sub.d_wl.to_numpy(float)) > BIG
    expected = [("full", "S2 complete", np.ones(len(sub), bool))]
    expected += [("leave-one-epoch-out", f"without {e}", groups[f"without {e}"]) for e in LOO]
    expected += [("subset", k, groups[k]) for k in ("source GYUL", "source other")]
    expected += [("subset", f"{n} tercile {t}", groups[f"{n} tercile {t}"]) for n in ("dpd_area", "phi_mwo", "separation") for t in (1, 2, 3)]
    expected += [("sensitivity", f"without |d_WL| > {BIG:g}", ~big)]
    order_ok = list(zip(F.kind, F.label)) == [(k, l) for k, l, _ in expected]
    ok("exactly the declared fits, in order", order_ok, len(F))
    good_d, good_b, good_m, info = order_ok, order_ok, order_ok, []
    for (_, label, mask), (_, row) in zip(expected, F.iterrows()):
        ss = sub[mask].reset_index(drop=True)
        n = len(ss)
        w = ss.phi_mwo.to_numpy(float)
        cr = ss.CR.astype(int)
        desc = (int(row.n) == n and int(row.n_cr) == cr.nunique()
                and int(row.n_blocks) == (len(np.unique((cr - cr.min()) // BLOCK)) if n else 0)
                and json.loads(row.cycles) == own_comp(ss, "cycle") and json.loads(row.epochs) == own_comp(ss, "epoch")
                and json.loads(row.hemispheres) == own_comp(ss, "hemisphere")
                and close(row.A_min, ss.A_main.min() if n else np.nan, 1e-12) and close(row.A_max, ss.A_main.max() if n else np.nan, 1e-12)
                and close(row.n_eff, w.sum() ** 2 / np.sum(w ** 2) if n else np.nan, 1e-9 * max(1.0, n)))
        good_d &= desc
        if n < MIN_FIT:
            good_b &= note_str(row.state).startswith("sotto soglia") and not np.isfinite(row.get("beta", np.nan)) \
                and bool_or_none(row.identifiable) is None
            continue
        gg = own_g(ss)
        good_b &= bool_or_none(row.identifiable) == (gg is not None)
        if gg is None:
            good_b &= row.state == "non identificabile"
            continue
        if fit is not None:
            m = fit(ss)
            good_m &= row.state == m.get("state")
            if m.get("state") == "stimato":
                good_m &= all(close(m.get(k), row[k], 1e-9) for k in M_KEYS)
                phi, kap = m["phi"], m["kappa"]
                good_m &= bool_or_none(row.phi_at_bound) == bool(phi <= 1e-9 or phi >= 0.98 - 1e-9) \
                    and bool_or_none(row.kappa_at_bound) == bool(abs(kap) >= 0.98 - 1e-9)
            else:                                    # an M error is a state to report, not a successful row
                good_m &= not np.isfinite(row.get("beta", np.nan))
        if np.isfinite(row.get("beta", np.nan)):
            b = float(gg @ ss.d_wl.to_numpy(float))
            good_b &= abs(b - row.beta) < TOL_BETA and abs(row.delta_beta - (b - s2_ref[0])) < TOL_BETA \
                and abs(row.delta_over_se_full - (b - s2_ref[0]) / s2_ref[1]) < 1e-8
            info.append((label, round(b, 4)))
    ok("fit descriptions: n, n_CR, blocks, composition, A range, n_eff, threshold rows", good_d)
    ok("point estimate of every fit with an own g (and delta, delta/SE), identifiability", good_b, info[:4])
    if fit is not None:
        ok("state, all M parameters and boundary flags (common procedure: declared dependency)", good_m)
    # COUNTS -------------------------------------------------------------
    a_t = own_terc(sub.A_main, sub.A_main)
    exp_counts = {("source", s_): int((srcs == s_).sum()) for s_ in set(srcs)}
    for name, col in (("A_main", "A_main"), ("dpd_area", "dpd_area"), ("phi_mwo", "phi_mwo"), ("separation", "separation")):
        t = own_terc(sub[col], sub[col])
        exp_counts.update({(f"tercile {name}", str(k)): int((t == k).sum()) for k in (1, 2, 3)})
    hem = sub.hemisphere.to_numpy()
    rem = {("removed |d_WL|>45 by A tercile", str(t)): a_t == t for t in (1, 2, 3)}
    rem.update({("removed |d_WL|>45 by hemisphere", h): hem == h for h in ("N", "S")})
    edges = {f"tercile edges {k}": np.quantile(sub[col].to_numpy(float), [1 / 3, 2 / 3])
             for k, col in (("dpd_area", "dpd_area"), ("phi_mwo", "phi_mwo"), ("separation", "separation"), ("A_main", "A_main"))}
    keys = list(zip(C["item"], C["label"]))
    want = set(exp_counts) | set(rem) | {k for k in edges}
    have = {(i, l) if not i.startswith("tercile edges") else i for i, l in keys}
    good = len(keys) == len(set(keys)) and have == want
    for _, row in C.iterrows():
        k = (row["item"], row["label"])
        if row["item"].startswith("tercile edges"):
            e = edges.get(row["item"])
            good &= e is not None and np.allclose(json.loads(row["label"]), e, rtol=0, atol=1e-12) and not np.isfinite(row.get("n", np.nan))
        elif k in exp_counts:
            good &= int(row.n) == exp_counts[k]
        elif k in rem:
            den = int(rem[k].sum())
            good &= int(row.n) == int((big & rem[k]).sum()) and (
                close(row.share, int((big & rem[k]).sum()) / den, 1e-12) and note_str(row.get("share_note")) == "" if den
                else (not np.isfinite(row.share) and note_str(row.get("share_note")) == "empty denominator"))
        else:
            good = False
    ok("counts: exact unique key set, all counts, tercile edges, removed records and shares", good, len(C))
    # SUMMARIES ----------------------------------------------------------
    dv, wv = sub.d_wl.to_numpy(float), sub.phi_mwo.to_numpy(float)
    cells = [(gname, t) for gname in groups for t in ("1", "2", "3", "all")]
    masks = {c: groups[c[0]] & ((a_t == int(c[1])) if c[1] != "all" else True) for c in cells}
    skeys = list(zip(S.group, S.A_tercile))
    ok("summaries: exact unique key set", len(skeys) == len(set(skeys)) and set(skeys) == set(cells), len(S))
    Sx = S.set_index(["group", "A_tercile"])
    point_ok = set(skeys) == set(cells)
    for c in cells if point_ok else []:
        row = Sx.loc[c]
        st = own_stats(dv[masks[c]], wv[masks[c]])
        point_ok &= int(row.n) == int(masks[c].sum()) and all(close(a, b, TOL_STAT) for a, b in zip(st, (row["median"], row.wmean, row.share_big)))
    ok("D5 point summaries (n, median, weighted mean, share)", point_ok)
    boots = {c: [] for c in cells}
    for idx in own_draws(sub.CR, reps):
        for c in cells:
            sel = idx[masks[c][idx]]
            boots[c].append(own_stats(dv[sel], wv[sel]))
    ci_ok = set(skeys) == set(cells)
    for c in cells if ci_ok else []:
        b = np.array(boots[c])
        valid = np.isfinite(b[:, 0])
        row = Sx.loc[c]
        ci_ok &= int(row.valid_reps) == int(valid.sum()) and int(row.empty_reps) == int((~valid).sum())
        for j, s_ in enumerate(("median", "wmean", "share_big")):
            if valid.sum() >= MIN_VALID:
                lo, hi = np.quantile(b[valid, j], [0.025, 0.975])
                ci_ok &= close(lo, row[f"{s_}_lo"], TOL_STAT) and close(hi, row[f"{s_}_hi"], TOL_STAT) and note_str(row[f"{s_}_ci_note"]) == ""
            else:
                cause = f"fewer than {MIN_VALID} valid replicates" if masks[c].any() else "empty group"
                ci_ok &= not np.isfinite(row[f"{s_}_lo"]) and not np.isfinite(row[f"{s_}_hi"]) and note_str(row[f"{s_}_ci_note"]) == cause
    ok("D5 bootstrap replay: valid/empty replicates, percentile intervals and causes of missing intervals", ci_ok)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks,
                   diagnosis_meta_sha256=sha(out / "META.json"),
                   dependency="SE, intervals and parameters of M via the common s2_fit/procedure (not independently verified)")
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec).exists():
            sys.exit("receipt exists")
        Path(rec).mkdir(parents=True)
        (Path(rec) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    check.last_receipt = receipt
    return passed == len(checks)


def selftest():
    import contextlib
    import io
    import shutil
    import tempfile
    spec = importlib.util.spec_from_file_location("diag", ROOT / "scripts/t3_mwo_s2_diagnosis.py")
    DG = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(DG)
    sub = DG.synthetic()
    days = sorted(set(sub.day))
    src = {x: ("GYUL" if i % 3 else "DEBR") for i, x in enumerate(days)}
    src[days[0]] = "(none)"
    ref = DG.A.s2_fit(sub)
    prods = DG.build(sub, src, (ref["beta"], ref["se"]), reps=40)
    cache = {}

    def fit(ss):                                  # common s2_fit with a cache (same results, faster tampering tests)
        k = (tuple(ss.noaa), ss.d_wl.to_numpy(float).tobytes())
        if k not in cache:
            cache[k] = DG.A.s2_fit(ss)
        return cache[k]

    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        note = td / "note.md"
        note.write_text("frozen note")
        out = td / "o"
        DG.write_atomic(out, prods, dict(note_sha256=sha(note)))
        kw = dict(sub=sub, src=src, s2_ref=(ref["beta"], ref["se"]), fit=fit, mfit=component_m(DG.A), reps=40, write=False, note=note)

        def run_check(o, **extra):
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                good = check(o, **dict(kw, **extra))
            return good, check.last_receipt, buf.getvalue()

        good, rc, txt = run_check(out)
        ok("base synthetic outputs pass all checks", good, f"{rc['passed']}/{rc['total']}")
        if not good:
            print(txt)
        ok("synthetic path gives partial = True", rc["partial"] is True)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                check(out, **dict(kw, write=True, rec=td / "rec"))
            ok("no receipt written outside the real path", False)
        except SystemExit:
            ok("no receipt written outside the real path", not (td / "rec").exists())
        g_own = own_g(sub)
        names, Z, x3 = DG.A.columns(sub)
        _, Xr = DG.A.reduce(names, Z, x3, sub.phi_mwo.to_numpy(float))
        ok("own g equals the analysis row on synthetic data", np.allclose(g_own, DG.A.g_row(Xr, sub.phi_mwo.to_numpy(float)), atol=1e-10))

        def tamper(label, fn):
            o2 = td / label.replace(" ", "_").replace("|", "").replace(">", "")
            shutil.copytree(out, o2)
            fn(o2)
            meta = json.loads((o2 / "META.json").read_text())
            meta["products_sha256"] = {n: sha(o2 / n) for n in meta["products_sha256"]}
            (o2 / "META.json").write_text(json.dumps(meta))
            good2, _, _ = run_check(o2)
            ok(f"refused: {label}", not good2)

        def csv_edit(name, fn, **rk):
            def f(o):
                t = pd.read_csv(o / name, **rk)
                fn(t)
                t.to_csv(o / name, index=False)
            return f

        def json_edit(fn):
            def f(o):
                j = json.loads((o / "DECOMPOSITION.json").read_text())
                fn(j)
                (o / "DECOMPOSITION.json").write_text(json.dumps(j))
            return f

        cases = [
            ("a leave-one-epoch-out beta changed", csv_edit("FITS.csv", lambda t: t.__setitem__("beta", t.beta.where(t.index != 1, t.beta + 0.01)))),
            ("main phi 123 and phi_at_bound False (Codex)", csv_edit("FITS.csv", lambda t: (t.__setitem__("phi", t.phi.where(t.index != 0, 123.0)),
                                                                                         t.__setitem__("phi_at_bound", False)))),
            ("a fit state changed", csv_edit("FITS.csv", lambda t: t.__setitem__("state", t.state.where(t.index != 2, "errore di M")))),
            ("a fit composition changed", csv_edit("FITS.csv", lambda t: t.__setitem__("epochs", t.epochs.where(t.index != 0, '{"E2": 1}')))),
            ("n_blocks changed", csv_edit("FITS.csv", lambda t: t.__setitem__("n_blocks", t.n_blocks + (t.index == 4)))),
            ("a declared fit missing", csv_edit("FITS.csv", lambda t: t.drop(index=3, inplace=True))),
            ("D1 component SE and limits 999 (Codex)", json_edit(lambda j: j["M_gamma_wl"].update(se=999.0, lo=-999.0, hi=999.0))),
            ("D1 g_r from -180 changed", json_edit(lambda j: j.update(g_r_from_minus180=j["g_r_from_minus180"] + 1.0))),
            ("D1 wrap count changed", json_edit(lambda j: j.update(wraps_r_minus180=j["wraps_r_minus180"] + 1))),
            ("tercile count and removed by hemisphere 99999 (Codex)", csv_edit("COUNTS.csv", lambda t: (
                t.__setitem__("n", t.n.where(~((t["item"] == "tercile dpd_area") & (t["label"] == "1")), 99999)),
                t.__setitem__("n", t.n.where(t["item"] != "removed |d_WL|>45 by hemisphere", 99999))), dtype={"label": str})),
            ("a counts row duplicated", csv_edit("COUNTS.csv", lambda t: t.loc.__setitem__(len(t), t.iloc[0]), dtype={"label": str})),
            ("a summary median changed", csv_edit("SUMMARIES.csv", lambda t: t.__setitem__("median", t["median"].where(t.index != 3, t["median"] + 0.5)))),
            ("bootstrap empty count changed", csv_edit("SUMMARIES.csv", lambda t: t.__setitem__("empty_reps", t.empty_reps + (t.index == 0)))),
            ("cause of a missing interval changed", csv_edit("SUMMARIES.csv", lambda t: t.__setitem__("median_ci_note", "x"))),
        ]
        for label, fn in cases:
            tamper(label, fn)
        note.write_text("note edited after the run")
        good3, _, _ = run_check(out)
        ok("refused: note changed after the run", not good3)
        root = td / "root"
        (root / "a").mkdir(parents=True)
        (root / "a/x.txt").write_text("1")
        inp = {"a/x.txt": sha(root / "a/x.txt")}
        ok("inputs check accepts the exact declared set", inputs_problem(inp, root, {"a/x.txt"}) is None)
        ok("inputs check refuses an incomplete or empty declared set", inputs_problem({}, root, {"a/x.txt"}) is not None
           and inputs_problem({"a/x.txt": inp["a/x.txt"]}, root, {"a/x.txt", "b"}) is not None)
        (root / "a/x.txt").write_text("2")
        ok("inputs check refuses an input changed after the run", inputs_problem(inp, root, {"a/x.txt"}) is not None)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.check:
        spec = importlib.util.spec_from_file_location("an", ROOT / "scripts/t3_mwo_analysis.py")
        AN = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(AN)
        sys.exit(0 if check(fit=AN.s2_fit, mfit=component_m(AN)) else 1)
    sys.exit(1)
