"""Independent recount of the MDI pilot level-1 analysis (Q1, Q3; frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md).

Own code (not importing scripts/mdi_pilot_analysis_l1.py nor python/sharpbl/tilt_window.py) for: yields per cell x
cohort and projected with w1, quiet availability and summary, Q3 pairs (M1, main ok, same-day MWO), class edges,
angular differences, leading agreement, flux ratio, time distance, and the bootstrap replay with the same draws.
Exploratory M fit: own Joy design per cycle x hemisphere; procedure M itself is the common one of
scripts/t3_mwo_analysis.py (declared dependency). Strict receipt, partial outside the real path.

    .venv/bin/python scripts/mdi_pilot_analysis_l1_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_analysis_l1_recount.py --check
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
OUT = ROOT / "results/MDI_PILOT_ANALYSIS_L1"
REC = ROOT / "results/MDI_PILOT_ANALYSIS_L1_RECOUNT"
SEL, L1 = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_L1"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
SEED, REPS = 71_100_001, 2000
PRODUCTS = {"Q1_YIELD_CELLS.csv", "Q1_YIELD_PROJECTED.csv", "Q1_QUIET_AVAILABILITY.csv", "Q1_QUIET_SUMMARY.json",
            "Q1_M_EXPLORATORY.json", "CLASS_EDGES.json", "Q3_PAIRS_main.csv", "Q3_SUMMARY_main.csv", "Q3_PAIRS_sens100.csv",
            "Q3_SUMMARY_sens100.csv"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ax(a, b):
    return (np.asarray(a, float) - np.asarray(b, float) + 90.0) % 180.0 - 90.0


def terc(x, ref):
    q = np.quantile(np.asarray(ref, float), [1 / 3, 2 / 3])
    x = np.asarray(x, float)
    return np.where(x < q[0], 1, np.where(x < q[1], 2, 3)), q


def eq(a, b, tol=1e-9):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return a.shape == b.shape and np.allclose(a, b, rtol=tol, atol=tol, equal_nan=True)


def own_pairs(rec, samp, mwo, tag):
    okall = rec[rec[f"{tag}_status"] == "ok"]
    m = samp[samp.cohort == "M1"].merge(rec, on=["noaa", "day"])
    m = m[m[f"{tag}_status"] == "ok"].merge(mwo.rename(columns={"day_utc": "day"}), on=["noaa", "day"], how="inner")
    m["sep_class"], qs = terc(m[f"{tag}_sep_deg"], okall[f"{tag}_sep_deg"])
    m["lcm_class"], ql = terc(m.lcm.abs(), m.lcm.abs())
    d = ax(m[f"{tag}_tilt_deg"], m.tilt_deg)
    m["d_ax"], m["d_gamma"] = d, np.where(np.sign(m.lat) == 0, np.nan, np.sign(m.lat) * d)
    m["leading_agree"] = m[f"{tag}_leading_sign"].astype(int).to_numpy() == m.leading_polarity_sign.astype(int).to_numpy()
    m["flux_ratio"] = (m[f"{tag}_flux_pos_mx"] + m[f"{tag}_flux_neg_mx"]) / m.flux_window_mx
    m["dt_h"] = (pd.to_datetime(m.mwo_time_utc) - pd.to_datetime(m.t_cm)).dt.total_seconds() / 3600
    return m, qs, ql


def own_boot(m, groups, reps=REPS):
    n0 = int(m.N.min())
    blk = ((m.N.astype(int) - n0) // 6).to_numpy()
    lab = np.unique(blk)
    mem = [np.flatnonzero(blk == b) for b in lab]
    rng = np.random.default_rng(SEED)
    draws = [np.concatenate([mem[i] for i in rng.integers(0, len(lab), len(lab))]) for _ in range(reps)]
    out = {}
    for name, mask in groups:
        mk = np.asarray(mask)
        x = m[mk]
        nb = len(np.unique(blk[mk])) if mk.any() else 0
        row = dict(n_pairs=len(x), n_blocks=nb, median_d_ax=np.nanmedian(x.d_ax) if len(x) else np.nan,
                   median_d_gamma=np.nanmedian(x.d_gamma) if x.d_gamma.notna().any() else np.nan,
                   leading_agree=x.leading_agree.mean() if len(x) else np.nan)
        if len(x) >= 10 and nb >= 3:
            v = []
            for d in draws:
                s = d[mk[d]]
                y = m.iloc[s]
                v.append((np.nanmedian(y.d_ax), np.nanmedian(y.d_gamma) if y.d_gamma.notna().any() else np.nan, y.leading_agree.mean()) if len(s) else (np.nan,) * 3)
            v = np.array(v)
            ok = np.isfinite(v[:, 0])
            if ok.sum() >= 1900:
                for j, k in enumerate(("d_ax", "d_gamma", "agree")):
                    vv = v[ok, j]
                    vv = vv[np.isfinite(vv)]
                    row[f"{k}_lo"], row[f"{k}_hi"] = np.quantile(vv, [0.025, 0.975]) if len(vv) >= 1900 else (np.nan, np.nan)
        out[name] = row
    return out


def check(out=OUT, write=True, rec_dir=REC, data=None, reps=REPS, A=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(out) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("products: exact set and actual hashes before reading", set(ps) == PRODUCTS and all(sha(Path(out) / n) == h for n, h in ps.items()))
    real = data is None
    if real:
        fr = json.loads(FREEZE.read_text())
        ok("frozen protocol and upstream links unchanged", sha(PROTOCOL) == fr["sha256"] == meta.get("protocol_sha256")
           and meta.get("selection_meta_sha256") == sha(SEL / "META.json") and meta.get("l1_meta_sha256") == sha(L1 / "META.json")
           and meta.get("release_sha256") == sha(RELEASE))
        samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
        rec = pd.read_csv(L1 / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
        mwo = pd.read_csv(RELEASE, dtype={"noaa": str}, float_precision="round_trip",
                          usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"])
    else:
        rec, samp, mwo = data
    rd = lambda n: pd.read_csv(Path(out) / n, dtype={"noaa": str, "group": str}, float_precision="round_trip")   # noqa: E731
    # Q1 yields
    m = samp.merge(rec[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left")
    okv = (m.status == "ok").to_numpy()
    P = rd("Q1_YIELD_PROJECTED.csv")
    allrow = P[P.group == "all"].iloc[0]
    w = m.w1.to_numpy(float)
    ok("Q1: all sampled groups in the denominator; projected yields (main, 100 G)", allrow.n == len(samp) and m.status.notna().all()
       and abs(allrow.projected_yield - (w * okv).sum() / w.sum()) < 1e-12
       and abs(allrow.projected_yield_100 - (w * (m.sens100_status == "ok")).sum() / w.sum()) < 1e-12)
    good = True
    for by in ("act_class", "area_class", "hemisphere", "cohort"):
        for v, g in m.groupby(by):
            r = P[P.group == f"{by}={v}"]
            ww, oo = g.w1.to_numpy(float), (g.status == "ok").to_numpy()
            good &= len(r) == 1 and int(r.n.iloc[0]) == len(g) and abs(r.projected_yield.iloc[0] - (ww * oo).sum() / ww.sum()) < 1e-12
    ok("Q1: projected yields by class", good)
    C = rd("Q1_YIELD_CELLS.csv")
    keys = ["act_class", "hemisphere", "area_class", "cohort"]
    g2 = m.groupby(keys).agg(n=("status", "size"), okn=("status", lambda s: int((s == "ok").sum()))).reset_index()
    cc = C.merge(g2, on=keys, how="left", suffixes=("", "_own"))
    ok("Q1: cells (n, ok)", (cc.n.fillna(0) == cc.n_own.fillna(0)).all() and (cc.ok.fillna(0) == cc.okn.fillna(0)).all())
    sides = pd.concat([rec[f"{s}_status"] for s in ("qm", "qp")]).fillna("not_attempted")
    Q = json.loads((Path(out) / "Q1_QUIET_SUMMARY.json").read_text())
    QA = rd("Q1_QUIET_AVAILABILITY.csv").set_index("status").n_sides
    vq = rec.quiet_mad_g.dropna()
    ok("Q1: quiet availability, causes and summary", int(QA.sum()) == len(sides) and all(int(QA.get(k, 0)) == int(v) for k, v in sides.value_counts().items())
       and Q["sides_ok"] == int((sides == "ok").sum()) and Q["groups_with_value"] == len(vq)
       and (len(vq) == 0 or abs(Q["median_g"] - vq.median()) < 1e-12))
    # Q1 M (own design, common M)
    if A is None:
        spec = importlib.util.spec_from_file_location("t3a", ROOT / "scripts/t3_mwo_analysis.py")
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    d = rec.merge(samp[["noaa", "day"]], on=["noaa", "day"])
    d = d[d.main_status == "ok"].reset_index(drop=True)
    d["hemisphere"] = np.where(d.main_lat_bar >= 0, "N", "S")
    s = np.sin(np.radians(np.abs(d.main_lat_bar.to_numpy())))
    cyc = np.array([20 + sum(pd.Timestamp(x) >= pd.Timestamp(y) for y in ("1976-03-01", "1986-09-01", "1996-08-01", "2008-12-01")) for x in d.day])
    cols = [s * ((cyc == c) & (d.hemisphere.to_numpy() == h)) for c in sorted(set(cyc)) for h in ("N", "S") if ((cyc == c) & (d.hemisphere.to_numpy() == h)).any()]
    wv = (d.main_flux_pos_mx + d.main_flux_neg_mx).to_numpy(float)
    X = np.zeros((len(d), 0))
    for c in cols:
        t = np.column_stack([X, c])
        if np.linalg.matrix_rank(t * np.sqrt(wv)[:, None]) > X.shape[1]:
            X = t
    t_ = np.radians(d.main_tilt_deg.to_numpy(float))
    gam = np.sign(d.main_lat_bar.to_numpy()) * np.degrees(np.arcsin(np.sin(t_)))
    dd = d.assign(CR=d.N.astype(int), phi_mwo=wv)
    codes, uniq = A.cell_codes(dd)
    r = A.m_verdict(A.m_unit(dd, X, wv, A.g_row(X, wv), gam, codes, uniq), 0.0)
    MJ = json.loads((Path(out) / "Q1_M_EXPLORATORY.json").read_text())
    # tolerance 1e-5 relative: exploratory fit, REML optimum flat at the kappa/phi bounds (last-bit input differences
    # move sigma_x2 by ~3e-7 relative in the synthetic test; same behaviour as the S2 diagnosis)
    ok("Q1: exploratory M (own design, common M: declared dependency; variance parameters within 1e-5 relative); "
       "no coefficient saved",
       all(np.isclose(MJ.get(k), r.get(k), rtol=1e-5, atol=1e-9) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2") if r.get(k) is not None)
       and not any(k in MJ for k in ("beta", "se", "lo", "hi", "verdict")) and MJ["n"] == len(d))
    # Q3
    E = json.loads((Path(out) / "CLASS_EDGES.json").read_text())
    for tag in ("main", "sens100"):
        p, qs, ql = own_pairs(rec, samp, mwo, tag)
        Pf = rd(f"Q3_PAIRS_{tag}.csv")
        same_keys = list(zip(Pf.noaa, Pf.day)) == list(zip(p.noaa, p.day))
        ok(f"Q3 {tag}: pairs (M1, ok, same day), class edges and classes", same_keys and eq(E[tag]["sep_edges"], qs) and eq(E[tag]["lcm_edges"], ql)
           and (Pf.sep_class.to_numpy() == p.sep_class).all() and (Pf.lcm_class.to_numpy() == p.lcm_class).all(), (len(Pf), len(p)))
        ok(f"Q3 {tag}: d_ax, d_gamma, leading agreement, flux ratio, time distance", same_keys and eq(Pf.d_ax, p.d_ax) and eq(Pf.d_gamma, p.d_gamma)
           and (Pf.leading_agree.astype(str).to_numpy() == p.leading_agree.astype(str)).all() and eq(Pf.flux_ratio, p.flux_ratio, 1e-12)
           and eq(Pf.dt_mwo_minus_tcm_h, p.dt_h))
        groups = [("all", np.ones(len(p), bool))]
        for col, lab in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation"), ("lcm_class", "abs_LCM")):
            groups += [(f"{lab} {k}", (p[col] == k).to_numpy()) for k in (1, 2, 3)]
        groups += [(f"hemisphere {h}", (p.hemisphere == h).to_numpy()) for h in ("N", "S")]
        own = own_boot(p, groups, reps)
        S = rd(f"Q3_SUMMARY_{tag}.csv").set_index("group")
        good = list(S.index) == [g for g, _ in groups]
        for gname, row in own.items():
            if gname not in S.index:
                good = False
                continue
            sr = S.loc[gname]
            for k, v in row.items():
                good &= eq(sr.get(k, np.nan), v, 1e-12)
        ok(f"Q3 {tag}: summary and bootstrap replay (same draws)", good)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, analysis_meta_sha256=sha(Path(out) / "META.json"),
                   dependency="procedure M of scripts/t3_mwo_analysis.py for the exploratory covariance fit")
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


def selftest():
    import tempfile
    spec = importlib.util.spec_from_file_location("ana", ROOT / "scripts/mdi_pilot_analysis_l1.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    spec2 = importlib.util.spec_from_file_location("t3a", ROOT / "scripts/t3_mwo_analysis.py")
    A = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(A)
    res = []
    rec, samp, cells, mwo = M.synthetic()
    prods = M.build(rec, samp, cells, mwo, reps=REPS, A=A)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "a"
        d.mkdir()
        M.write(prods, d)
        (d / "META.json").write_text(json.dumps(dict(products_sha256={f.name: sha(f) for f in d.iterdir() if f.name != "META.json"})))
        res.append(check(d, write=False, data=(rec, samp, mwo), A=A))
        print("[OK]" if res[-1] else "[FALLITO]", "recount passes on synthetic analysis outputs")

        def tamper(name, fn, f):
            t = pd.read_csv(d / f, dtype={"noaa": str, "group": str}, float_precision="round_trip")
            t0 = t.copy()
            fn(t).to_csv(d / f, index=False)
            (d / "META.json").write_text(json.dumps(dict(products_sha256={x.name: sha(x) for x in d.iterdir() if x.name != "META.json"})))
            bad = not check(d, write=False, data=(rec, samp, mwo), A=A)
            res.append(bad)
            print("[OK]" if bad else "[FALLITO]", f"refused: {name}")
            t0.to_csv(d / f, index=False)
            (d / "META.json").write_text(json.dumps(dict(products_sha256={x.name: sha(x) for x in d.iterdir() if x.name != "META.json"})))
        tamper("projected yield changed", lambda t: t.assign(projected_yield=t.projected_yield + 0.01), "Q1_YIELD_PROJECTED.csv")
        tamper("a pair d_ax changed", lambda t: t.assign(d_ax=t.d_ax.where(t.index != 0, t.d_ax + 0.5)), "Q3_PAIRS_main.csv")
        tamper("a separation class changed", lambda t: t.assign(sep_class=t.sep_class.where(t.index != 0, 4)), "Q3_PAIRS_main.csv")
        tamper("a bootstrap bound changed", lambda t: t.assign(d_ax_lo=t.d_ax_lo + 0.1), "Q3_SUMMARY_main.csv")
        tamper("a summary median changed", lambda t: t.assign(median_d_gamma=t.median_d_gamma + 0.1), "Q3_SUMMARY_sens100.csv")
        tamper("a pair dropped", lambda t: t.drop(index=0), "Q3_PAIRS_main.csv")
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
