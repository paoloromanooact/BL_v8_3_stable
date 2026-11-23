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
    wl = pd.read_csv(WL, dtype={"noaa": str})
    assert list(zip(wl.noaa, wl.day)) == list(zip(d.noaa, d.day)), "WL_TILTS order"
    rel = pd.read_csv(RELT, dtype={"noaa": str}).set_index(["noaa", "day_utc"])
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

def check(out=OUT, sub=None, src=None, s2_ref=None, fit=None, reps=REPS, write=True, rec=REC, note=NOTE):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:200]}")

    out = Path(out)
    meta = json.loads((out / "META.json").read_text())
    ok("products match META", all(sha(out / n) == h for n, h in meta["products_sha256"].items())
       and set(meta["products_sha256"]) == {"FITS.csv", "SUMMARIES.csv", "COUNTS.csv", "DECOMPOSITION.json"})
    if note is not None:
        ok("note SHA in META equals the committed note", meta.get("note_sha256") == sha(note))
    if sub is None:
        sub, src = own_subset(), own_sources()
        s2 = json.loads(STABJ.read_text())["S2"]
        s2_ref = (s2["beta"], s2["se"])
        ok("inputs unchanged since the run", all(sha(ROOT / p) == h for p, h in meta["inputs_sha256"].items()))
    ok("S2 subset size", len(sub) == (4694 if note is not None else len(sub)), len(sub))
    F = pd.read_csv(out / "FITS.csv")
    S = pd.read_csv(out / "SUMMARIES.csv", keep_default_na=False, na_values=[""])
    C = pd.read_csv(out / "COUNTS.csv")
    D = json.loads((out / "DECOMPOSITION.json").read_text())
    # D1
    g = own_g(sub)
    gm, gw = sub.gamma_mwo.to_numpy(float), sub.gamma_wl.to_numpy(float)
    u = gm - gw
    dd = axial(u)
    r = dd - u
    terms = dict(g_d=g @ dd, g_gamma_mwo=g @ gm, g_gamma_wl=g @ gw, g_r=g @ r)
    ok("D1 terms with an own g", all(abs(terms[k] - D[k]) < TOL_BETA for k in terms), {k: round(v, 6) for k, v in terms.items()})
    ok("D1 identity g d = g mwo - g wl + g r", abs(terms["g_d"] - (terms["g_gamma_mwo"] - terms["g_gamma_wl"] + terms["g_r"])) < 1e-9
       and abs(D["identity_residual"]) < 1e-9)
    ok("D1 wraps by sign", D["wraps_r_minus180"] == int((r < -1e-9).sum()) and D["wraps_r_plus180"] == int((r > 1e-9).sum())
       and D["wraps_total"] == int((np.abs(r) > 1e-9).sum()), (int((r < -1e-9).sum()), int((r > 1e-9).sum())))
    ok("D1 saved d_WL equals axial(gamma_mwo - gamma_wl)", np.max(np.abs(dd - sub.d_wl.to_numpy(float))) < 1e-9)
    ok("D1 components carry no verdict", "verdict" not in D["M_gamma_mwo"] and "verdict" not in D["M_gamma_wl"])
    # fits: subsets, sizes, own point estimates; M through the common s2_fit (declared dependency)
    groups, srcs = own_groups(sub, src)
    big = np.abs(sub.d_wl.to_numpy(float)) > BIG
    expected = [("full", "S2 complete", np.ones(len(sub), bool))]
    expected += [("leave-one-epoch-out", f"without {e}", groups[f"without {e}"]) for e in LOO]
    expected += [("subset", k, groups[k]) for k in ("source GYUL", "source other")]
    expected += [("subset", f"{n} tercile {t}", groups[f"{n} tercile {t}"]) for n in ("dpd_area", "phi_mwo", "separation") for t in (1, 2, 3)]
    expected += [("sensitivity", f"without |d_WL| > {BIG:g}", ~big)]
    ok("exactly the declared fits, in order", list(zip(F.kind, F.label)) == [(k, l) for k, l, _ in expected], len(F))
    good_n, good_b, good_m, info = True, True, True, []
    for (_, label, mask), (_, row) in zip(expected, F.iterrows()):
        ss = sub[mask].reset_index(drop=True)
        good_n &= int(row.n) == len(ss) and int(row.n_cr) == ss.CR.astype(int).nunique()
        good_n &= abs(row.n_eff - ss.phi_mwo.sum() ** 2 / np.sum(ss.phi_mwo ** 2)) < 1e-6 * row.n_eff if len(ss) else True
        if len(ss) < MIN_FIT:
            good_n &= str(row.state).startswith("sotto soglia") and not np.isfinite(row.get("beta", np.nan))
            continue
        gg = own_g(ss)
        if gg is None:
            good_b &= row.state == "non identificabile"
            continue
        b = float(gg @ ss.d_wl.to_numpy(float))
        good_b &= abs(b - row.beta) < TOL_BETA and abs(row.delta_beta - (b - s2_ref[0])) < TOL_BETA \
            and abs(row.delta_over_se_full - (b - s2_ref[0]) / s2_ref[1]) < 1e-8
        if fit is not None:
            m = fit(ss)
            good_m &= all(abs(m[k] - row[k]) < 1e-9 for k in ("se", "lo", "hi"))
        info.append((label, round(b, 4)))
    ok("fit sizes, n_CR, n_eff and threshold rows", good_n)
    ok("point estimate of every fit with an own g (and delta, delta/SE)", good_b, info[:4])
    if fit is not None:
        ok("SE and intervals of M (common procedure: declared dependency)", good_m)
    # counts
    sc = C[C.item == "source"].set_index("label").n
    ok("source counts", all(int(sc.get(k, 0)) == int((srcs == k).sum()) for k in set(srcs)) and int(sc.sum()) == len(sub))
    a_t = own_terc(sub.A_main, sub.A_main)
    rm = C[C.item == "removed |d_WL|>45 by A tercile"].set_index("label").n
    ok("D6 removed records by activity tercile", all(int(rm[str(t)]) == int((big & (a_t == t)).sum()) for t in (1, 2, 3)))
    # D5 replay
    dv, wv = sub.d_wl.to_numpy(float), sub.phi_mwo.to_numpy(float)
    cells = [(gname, t) for gname in groups for t in ("1", "2", "3", "all")]
    masks = {c: groups[c[0]] & ((a_t == int(c[1])) if c[1] != "all" else True) for c in cells}
    point_ok = True
    for c in cells:
        row = S[(S.group == c[0]) & (S.A_tercile == c[1])]
        if len(row) != 1:
            point_ok = False
            continue
        row = row.iloc[0]
        st = own_stats(dv[masks[c]], wv[masks[c]])
        point_ok &= int(row.n) == int(masks[c].sum()) and all(
            (np.isnan(a) and np.isnan(b)) or abs(a - b) < TOL_STAT for a, b in zip(st, (row["median"], row.wmean, row.share_big)))
    ok("D5 point summaries (n, median, weighted mean, share)", point_ok and len(S) == len(cells), len(S))
    boots = {c: [] for c in cells}
    for idx in own_draws(sub.CR, reps):
        for c in cells:
            sel = idx[masks[c][idx]]
            boots[c].append(own_stats(dv[sel], wv[sel]))
    ci_ok = True
    for c in cells:
        b = np.array(boots[c])
        valid = np.isfinite(b[:, 0])
        row = S[(S.group == c[0]) & (S.A_tercile == c[1])].iloc[0]
        ci_ok &= int(row.valid_reps) == int(valid.sum()) and int(row.empty_reps) == int((~valid).sum())
        for j, s in enumerate(("median", "wmean", "share_big")):
            if valid.sum() >= MIN_VALID:
                lo, hi = np.quantile(b[valid, j], [0.025, 0.975])
                ci_ok &= abs(lo - row[f"{s}_lo"]) < TOL_STAT and abs(hi - row[f"{s}_hi"]) < TOL_STAT
            else:
                ci_ok &= np.isnan(row[f"{s}_lo"]) and np.isnan(row[f"{s}_hi"])
    ok("D5 bootstrap replay: valid/empty replicates and percentile intervals", ci_ok)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=False, checks=checks,
                   diagnosis_meta_sha256=sha(out / "META.json"),
                   dependency="SE and intervals of M via the common s2_fit (not independently verified)")
    if write:
        if Path(rec).exists():
            sys.exit("receipt exists")
        Path(rec).mkdir(parents=True)
        (Path(rec) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)}")
    return passed == len(checks)


def selftest():
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
    res = []
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "o"
        DG.write_atomic(out, prods, dict(test=True))
        kw = dict(sub=sub, src=src, s2_ref=(ref["beta"], ref["se"]), reps=40, write=False, note=None)
        res.append(check(out, fit=DG.A.s2_fit, **kw))
        print("[OK]" if res[-1] else "[FALLITO]", "recount passes on synthetic outputs")
        g_own = own_g(sub)
        names, Z, x3 = DG.A.columns(sub)
        _, Xr = DG.A.reduce(names, Z, x3, sub.phi_mwo.to_numpy(float))
        g_an = DG.A.g_row(Xr, sub.phi_mwo.to_numpy(float))
        res.append(np.allclose(g_own, g_an, atol=1e-10))
        print("[OK]" if res[-1] else "[FALLITO]", "own g equals the analysis row on synthetic data")

        def tamper(fn, label):
            o2 = Path(td) / label
            DG.write_atomic(o2, {k: (v.copy() if hasattr(v, "copy") else v) for k, v in prods.items()}, dict(test=True))
            fn(o2)
            meta = json.loads((o2 / "META.json").read_text())
            meta["products_sha256"] = {n: sha(o2 / n) for n in meta["products_sha256"]}
            (o2 / "META.json").write_text(json.dumps(meta))
            bad = not check(o2, **kw)
            res.append(bad)
            print("[OK]" if bad else "[FALLITO]", f"refused: {label}")

        def f_beta(o):
            F = pd.read_csv(o / "FITS.csv")
            F.loc[1, "beta"] += 0.01
            F.to_csv(o / "FITS.csv", index=False)

        def f_wrap(o):
            D = json.loads((o / "DECOMPOSITION.json").read_text())
            D["wraps_r_minus180"] += 1
            (o / "DECOMPOSITION.json").write_text(json.dumps(D))

        def f_ci(o):
            S = pd.read_csv(o / "SUMMARIES.csv")
            S.loc[0, "empty_reps"] += 1
            S.to_csv(o / "SUMMARIES.csv", index=False)

        def f_med(o):
            S = pd.read_csv(o / "SUMMARIES.csv")
            S.loc[3, "median"] += 0.5
            S.to_csv(o / "SUMMARIES.csv", index=False)

        def f_drop(o):
            F = pd.read_csv(o / "FITS.csv")
            F.drop(index=3).to_csv(o / "FITS.csv", index=False)

        for fn, lab in ((f_beta, "a leave-one-epoch-out beta changed"), (f_wrap, "wrap count changed"),
                        (f_ci, "bootstrap empty count changed"), (f_med, "a summary median changed"),
                        (f_drop, "a declared fit missing")):
            tamper(fn, lab)
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
        sys.exit(0 if check(fit=AN.s2_fit) else 1)
    sys.exit(1)
