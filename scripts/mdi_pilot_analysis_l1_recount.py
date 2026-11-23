"""Independent recount of the MDI pilot level-1 analysis (Q1, Q3; frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md).

Every product is rebuilt with own code (not importing scripts/mdi_pilot_analysis_l1.py nor python/sharpbl/tilt_window.py)
and compared in full: exact column lists, exact key sets and order, every value (NaN = NaN). Procedure M for the
exploratory covariance fit is the common one of scripts/t3_mwo_analysis.py (declared dependency); its variance
parameters are compared within 1e-5 relative (numerical sensitivity observed in the synthetic test), while state,
finiteness, domain, boundary flags, n, cells and rotations are compared exactly. On the real path the upstream
products, receipts and links are verified before reading; the receipt is complete only on the real path with 2000
bootstrap replicates.

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
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
L1, L1_REC = ROOT / "results/MDI_PILOT_L1", ROOT / "results/MDI_PILOT_L1_RECOUNT"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
M_MODULES = ("scripts/t3_mwo_analysis.py", "python/sharpbl/p2d.py", "python/sharpbl/p2f_pilot.py", "python/sharpbl/p2f_validation.py")
SEED, REPS = 71_100_001, 2000
PRODUCTS = {"Q1_YIELD_CELLS.csv", "Q1_YIELD_PROJECTED.csv", "Q1_QUIET_AVAILABILITY.csv", "Q1_QUIET_SUMMARY.json",
            "Q1_M_EXPLORATORY.json", "CLASS_EDGES.json", "NOTES.json", "Q3_PAIRS_main.csv", "Q3_SUMMARY_main.csv",
            "Q3_PAIRS_sens100.csv", "Q3_SUMMARY_sens100.csv"}
K = ["act_class", "hemisphere", "area_class", "cohort"]
NOTE_KEYS = {"bard_mdi", "mwo_pixel_area_ratios", "synoptic_time", "abs_lcm_classes", "quiet"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strict(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    si = lambda x: isinstance(x, int) and not isinstance(x, bool)          # noqa: E731
    return (si(p) and si(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False and r.get(key) == sha(meta))


def frames_equal(a, b, tol=1e-12):
    """(ok, reason): same columns in the same order, same length, every value equal (NaN = NaN)."""
    if list(a.columns) != list(b.columns):
        return False, f"columns {sorted(set(a.columns) ^ set(b.columns))}"
    if len(a) != len(b):
        return False, f"rows {len(a)} vs {len(b)}"
    for c in a.columns:
        x, y = a[c].reset_index(drop=True), b[c].reset_index(drop=True)
        xn, yn = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
        if (xn.notna() | x.isna()).all() and (yn.notna() | y.isna()).all() and x.dtype != object and y.dtype != object:
            if not np.allclose(xn.to_numpy(float), yn.to_numpy(float), rtol=tol, atol=tol, equal_nan=True):
                return False, c
        else:
            norm = lambda s: s.astype(str).replace({"nan": "", "None": "", "NaN": ""})     # noqa: E731
            if not (norm(x).to_numpy() == norm(y).to_numpy()).all():
                return False, c
    return True, ""


# ---------------------------------------------------------------- own reconstruction

def own_cycle(day):
    return 20 + sum(pd.Timestamp(day) >= pd.Timestamp(m) for m in ("1976-03-01", "1986-09-01", "1996-08-01", "2008-12-01"))


def own_q1(rec, samp, cells):
    m = samp.merge(rec[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left")
    st = sorted(m.status.unique())
    rows = []
    for _, c in cells.iterrows():
        g = m[(m.act_class == c.act_class) & (m.hemisphere == c.hemisphere) & (m.area_class == c.area_class) & (m.cohort == c.cohort)]
        r = {k: c[k] for k in K}
        r.update(N=c.N, n=len(g), ok=int((g.status == "ok").sum()), ok100=int((g.sens100_status == "ok").sum()))
        r.update({f"cause_{s}": int((g.status == s).sum()) for s in st})
        rows.append(r)
    cell = pd.DataFrame(rows)
    prj = []
    for by in (None, "act_class", "area_class", "hemisphere", "cohort"):
        parts = [("all", m)] if by is None else [(f"{by}={v}", m[m[by] == v]) for v in sorted(m[by].unique())]
        for name, g in parts:
            w, o, o1 = g.w1.to_numpy(float), (g.status == "ok").to_numpy(), (g.sens100_status == "ok").to_numpy()
            prj.append(dict(group=name, n=len(g), ok=int(o.sum()), ok100=int(o1.sum()), sample_yield=o.mean(), sample_yield_100=o1.mean(),
                            projected_yield=(w * o).sum() / w.sum(), projected_yield_100=(w * o1).sum() / w.sum(), population_weight=w.sum()))
    sides = pd.concat([rec.qm_status, rec.qp_status]).fillna("not_attempted")
    av = sides.value_counts().sort_index()
    avail = pd.DataFrame(dict(status=av.index, n_sides=av.to_numpy()))
    v = rec.quiet_mad_g.dropna().to_numpy()
    summ = dict(sides_total=len(sides), sides_ok=int((sides == "ok").sum()), groups_total=len(rec), groups_with_value=len(v),
                median_g=float(np.quantile(v, 0.5)) if len(v) else None, p10_g=float(np.quantile(v, 0.1)) if len(v) else None,
                p90_g=float(np.quantile(v, 0.9)) if len(v) else None)
    return cell, pd.DataFrame(prj), avail, summ


def own_m(rec, samp, A):
    d = rec.merge(samp[["noaa", "day"]], on=["noaa", "day"])
    d = d[d.main_status == "ok"].reset_index(drop=True)
    lat = d.main_lat_bar.to_numpy(float)
    hem = np.where(lat >= 0, "N", "S")
    s = np.sin(np.radians(np.abs(lat)))
    cyc = np.array([own_cycle(x) for x in d.day])
    w = (d.main_flux_pos_mx + d.main_flux_neg_mx).to_numpy(float)
    X = np.zeros((len(d), 0))
    for c in sorted(set(cyc)):
        for h in ("N", "S"):
            col = s * ((cyc == c) & (hem == h))
            if col.any() and np.linalg.matrix_rank(np.column_stack([X, col]) * np.sqrt(w)[:, None]) > X.shape[1]:
                X = np.column_stack([X, col])
    gam = np.where(np.sign(lat) == 0, np.nan, np.sign(lat) * np.degrees(np.arcsin(np.sin(np.radians(d.main_tilt_deg.to_numpy(float))))))
    dd = d.assign(hemisphere=hem, CR=d.N.astype(int), phi_mwo=w)
    codes, uniq = A.cell_codes(dd)
    r = A.m_verdict(A.m_unit(dd, X, w, A.g_row(X, w), gam, codes, uniq), 0.0)
    p = {k: r.get(k) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2")}
    fin = all(v is not None and np.isfinite(v) for v in p.values())
    return dict(p, error=r.get("error"), state="errore di M" if r.get("verdict") == "errore" else "stimato", finite=fin,
                in_domain=bool(fin and 0 <= p["phi"] <= 0.98 and abs(p["kappa"]) <= 0.98 and p["sigma_x2"] > 0),
                phi_at_bound=bool(fin and (p["phi"] <= 1e-9 or p["phi"] >= 0.98 - 1e-9)), kappa_at_bound=bool(fin and abs(p["kappa"]) >= 0.98 - 1e-9),
                n=len(d), cells=len(uniq), rotations=int(dd.CR.nunique()), cr_min=int(dd.CR.min()), cr_max=int(dd.CR.max()))


def own_edges(rec):
    x = np.sort(rec.loc[rec.main_status == "ok", "main_sep_deg"].to_numpy(float))
    return np.quantile(x, [1 / 3, 2 / 3])


def own_pairs(rec, samp, mwo, tag, e):
    m = samp[samp.cohort == "M1"].merge(rec, on=["noaa", "day"])
    m = m[m[f"{tag}_status"] == "ok"].merge(mwo.rename(columns={"day_utc": "day"}), on=["noaa", "day"], how="inner")
    t1, t2 = m[f"{tag}_tilt_deg"].to_numpy(float), m.tilt_deg.to_numpy(float)
    raw = t1 - t2
    ax = (raw + 90) % 180 - 90
    sg = np.sign(m.lat.to_numpy(float))
    sep = m[f"{tag}_sep_deg"].to_numpy(float)
    hours = lambda a, b: (pd.to_datetime(a, format="ISO8601") - pd.to_datetime(b, format="ISO8601")).dt.total_seconds().to_numpy() / 3600.0   # noqa: E731
    f = (m[f"{tag}_flux_pos_mx"] + m[f"{tag}_flux_neg_mx"]).to_numpy(float)
    return pd.DataFrame({"noaa": m.noaa, "day": m.day, "N": m.N.astype(int), "hemisphere": m.hemisphere, "act_class": m.act_class,
                         "area_class": m.area_class, "sep_class": np.where(sep < e[0], 1, np.where(sep < e[1], 2, 3)), "lat": m.lat,
                         "t_dpd": m.t_dpd, "mwo_time_utc": m.mwo_time_utc, "dt_mwo_minus_tdpd_h": hours(m.mwo_time_utc, m.t_dpd),
                         "CT_g": m.CT_g, "t_rot": m.t_rot, "t_cm": m.t_cm, "dt_mwo_minus_tcm_h_approx": hours(m.mwo_time_utc, m.t_cm),
                         "mdi_tilt_deg": t1, "mwo_tilt_deg": t2, "d_raw": raw, "d_dir": (raw + 180) % 360 - 180, "d_ax": ax,
                         "d_gamma": np.where(sg == 0, np.nan, sg * ax), "mdi_leading_sign": m[f"{tag}_leading_sign"].astype(int),
                         "mwo_leading_sign": m.leading_polarity_sign.astype(int),
                         "leading_agree": m[f"{tag}_leading_sign"].astype(int).to_numpy() == m.leading_polarity_sign.astype(int).to_numpy(),
                         "mdi_flux_pos_mx": m[f"{tag}_flux_pos_mx"], "mdi_flux_neg_mx": m[f"{tag}_flux_neg_mx"], "mdi_flux_mx": f,
                         "mwo_flux_mx": m.flux_window_mx, "flux_ratio": f / m.flux_window_mx.to_numpy(float),
                         "mdi_npos": m[f"{tag}_npos"], "mdi_nneg": m[f"{tag}_nneg"], "mdi_area_pos_msh": m[f"{tag}_area_pos_msh"],
                         "mdi_area_neg_msh": m[f"{tag}_area_neg_msh"], "mdi_sep_deg": sep}).reset_index(drop=True)


def own_summary(p, reps):
    def st(x):
        return (np.nanmedian(x.d_ax) if len(x) else np.nan, np.nanmedian(x.d_gamma) if len(x) and x.d_gamma.notna().any() else np.nan,
                x.leading_agree.mean() if len(x) else np.nan)
    blk = ((p.N.astype(int) - int(p.N.min())) // 6).to_numpy()
    lab = np.unique(blk)
    mem = [np.flatnonzero(blk == b) for b in lab]
    rng = np.random.default_rng(SEED)
    draws = [np.concatenate([mem[i] for i in rng.integers(0, len(lab), len(lab))]) for _ in range(reps)]
    gs = [("all", np.ones(len(p), bool))]
    for col, name in (("act_class", "activity"), ("area_class", "area"), ("sep_class", "separation")):
        gs += [(f"{name} {k}", (p[col] == k).to_numpy()) for k in (1, 2, 3)]
    gs += [(f"hemisphere {h}", (p.hemisphere == h).to_numpy()) for h in ("N", "S")]
    rows = []
    for name, mk in gs:
        x = p[mk]
        a, g, ag = st(x)
        r = {"group": name, "n_pairs": len(x), "n_blocks": len(np.unique(blk[mk])) if len(x) else 0, "median_d_ax": a, "median_d_gamma": g,
             "leading_agree": ag, "median_flux_ratio": x.flux_ratio.median() if len(x) else np.nan,
             "median_abs_dt_dpd_h": x.dt_mwo_minus_tdpd_h.abs().median() if len(x) else np.nan, "valid_reps": np.nan,
             "d_ax_lo": np.nan, "d_ax_hi": np.nan, "d_gamma_lo": np.nan, "d_gamma_hi": np.nan, "agree_lo": np.nan, "agree_hi": np.nan}
        if len(x) < 10:
            r["interval_note"] = "fewer than 10 pairs: n and medians only"
        elif r["n_blocks"] < 3:
            r["interval_note"] = "non valutabile (fewer than 3 blocks)"
        else:
            b = np.array([st(p.iloc[d[mk[d]]]) if mk[d].any() else (np.nan,) * 3 for d in draws])
            ok = np.isfinite(b[:, 0])
            r["valid_reps"] = int(ok.sum())
            if ok.sum() >= 1900:
                for j, k in enumerate(("d_ax", "d_gamma", "agree")):
                    vv = b[ok, j]
                    vv = vv[np.isfinite(vv)]
                    if len(vv) >= 1900:
                        r[f"{k}_lo"], r[f"{k}_hi"] = np.quantile(vv, [0.025, 0.975])
                r["interval_note"] = ""
            else:
                r["interval_note"] = "fewer than 1900 valid replicates"
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- check

def upstream(meta):
    fr = json.loads(FREEZE.read_text())
    sm = json.loads((SEL / "META.json").read_text())
    lm = json.loads((L1 / "META.json").read_text())
    prods = lambda f, m, names: set(m.get("products_sha256", {})) == names and all(sha(f / n) == h for n, h in m["products_sha256"].items())  # noqa: E731
    return dict(
        protocol=sha(PROTOCOL) == fr["sha256"] == meta.get("protocol_sha256") == sm.get("protocol_sha256") == lm.get("protocol_sha256"),
        selection=prods(SEL, sm, {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}) and strict(SEL_REC / "RECEIPT.json", "selection_meta_sha256", SEL / "META.json")
        and meta.get("selection_meta_sha256") == sha(SEL / "META.json") and meta.get("selection_receipt_sha256") == sha(SEL_REC / "RECEIPT.json"),
        l1=prods(L1, lm, {"L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"}) and strict(L1_REC / "RECEIPT.json", "l1_meta_sha256", L1 / "META.json")
        and lm.get("selection_meta_sha256") == sha(SEL / "META.json") and meta.get("l1_meta_sha256") == sha(L1 / "META.json")
        and meta.get("l1_receipt_sha256") == sha(L1_REC / "RECEIPT.json"),
        release=meta.get("release_sha256") == sha(RELEASE) == sm.get("mwo_release_sha256"),
        m_modules=meta.get("m_modules_sha256") == {p: sha(ROOT / p) for p in M_MODULES},
        seed_reps=meta.get("seed") == SEED and meta.get("reps") == REPS)


def check(out=OUT, write=True, rec_dir=REC, data=None, reps=REPS, A=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(out) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("products: exact set and actual hashes before reading", set(ps) == PRODUCTS and all(sha(Path(out) / n) == h for n, h in ps.items()))
    real = data is None and reps == REPS
    if data is None:
        u = upstream(meta)
        ok("upstream: protocol, selection and L1 products, receipts and links, MWO release, M modules, seed and reps", all(u.values()),
           {k: v for k, v in u.items() if not v})
        samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
        cells = pd.read_csv(SEL / "CELLS.csv")
        rec = pd.read_csv(L1 / "L1_RECORDS.csv", dtype={"noaa": str}, float_precision="round_trip")
        mwo = pd.read_csv(RELEASE, dtype={"noaa": str}, float_precision="round_trip",
                          usecols=["noaa", "day_utc", "mwo_time_utc", "tilt_deg", "leading_polarity_sign", "flux_window_mx"])
    else:
        rec, samp, cells, mwo = data
    rd = lambda n: pd.read_csv(Path(out) / n, dtype={"noaa": str, "group": str, "status": str, "hemisphere": str, "cohort": str,  # noqa: E731
                                                     "interval_note": str, "t_rot": str}, keep_default_na=True, float_precision="round_trip")
    js = lambda n: json.loads((Path(out) / n).read_text())                  # noqa: E731
    cell, proj, avail, qsum = own_q1(rec, samp, cells)
    for name, own in (("Q1_YIELD_CELLS.csv", cell), ("Q1_YIELD_PROJECTED.csv", proj), ("Q1_QUIET_AVAILABILITY.csv", avail)):
        g, why = frames_equal(rd(name), own)
        ok(f"{name}: every column, key and value", g, why)
    Q = js("Q1_QUIET_SUMMARY.json")
    ok("Q1_QUIET_SUMMARY.json: counts, denominators and percentiles", set(Q) == set(qsum) | {"note"} and all(
        (Q[k] is None and v is None) or (v is not None and Q[k] is not None and np.isclose(Q[k], v, rtol=1e-12, atol=0)) for k, v in qsum.items()))
    if A is None:
        spec = importlib.util.spec_from_file_location("t3a", ROOT / "scripts/t3_mwo_analysis.py")
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
    om, M = own_m(rec, samp, A), js("Q1_M_EXPLORATORY.json")
    var = ("var_a", "var_b", "phi", "kappa", "sigma_x2")
    exact = [k for k in om if k not in var]
    ok("Q1_M_EXPLORATORY.json: state, error, finiteness, domain, flags, n, cells, rotations exact; variance parameters within "
       "1e-5 relative (common M: declared dependency); no coefficient", set(M) == set(om) | {"note"}
       and all(M[k] == om[k] for k in exact) and all((om[k] is None and M[k] is None) or (om[k] is not None and M[k] is not None and np.isclose(M[k], om[k], rtol=1e-5, atol=1e-9)) for k in var)
       and not any(k in M for k in ("beta", "se", "lo", "hi", "verdict")), {k: (M.get(k), om[k]) for k in exact if M.get(k) != om[k]})
    e = own_edges(rec)
    E = js("CLASS_EDGES.json")
    ok("CLASS_EDGES.json: one set of separation edges from the main successful L1 measurements", set(E) == {"separation_main_l1_ok"}
       and np.allclose(E["separation_main_l1_ok"], e, rtol=1e-12, atol=0))
    ok("NOTES.json: BARD deferred, MWO ratios not computable, time, |LCM| omitted, quiet wording", set(js("NOTES.json")) == NOTE_KEYS)
    for tag in ("main", "sens100"):
        p = own_pairs(rec, samp, mwo, tag, e)
        g, why = frames_equal(rd(f"Q3_PAIRS_{tag}.csv"), p)
        ok(f"Q3_PAIRS_{tag}.csv: every column, key and value", g, why)
        g, why = frames_equal(rd(f"Q3_SUMMARY_{tag}.csv"), own_summary(p, reps))
        ok(f"Q3_SUMMARY_{tag}.csv: every column incl. valid replicates, bounds and notes (bootstrap replay)", g, why)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, analysis_meta_sha256=sha(Path(out) / "META.json"),
                   dependency="procedure M of scripts/t3_mwo_analysis.py for the exploratory covariance fit")
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path with 2000 replicates")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    check.last_receipt = receipt
    return passed == len(checks)


# ---------------------------------------------------------------- selftest

def selftest():
    import tempfile
    spec = importlib.util.spec_from_file_location("ana", ROOT / "scripts/mdi_pilot_analysis_l1.py")
    Mx = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Mx)
    A = Mx.load_m()
    res = []
    data = Mx.synthetic()
    reps = 60
    prods = Mx.build(*data, A, reps=reps)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "a"
        d.mkdir()
        Mx.write(prods, d)

        def remeta():
            (d / "META.json").write_text(json.dumps(dict(products_sha256={f.name: sha(f) for f in d.iterdir() if f.name != "META.json"})))
        remeta()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            base = check(d, write=False, data=data, reps=reps, A=A)
        res.append(base and check.last_receipt["partial"] is True)
        print("[OK]" if res[-1] else "[FALLITO]", "recount passes on synthetic outputs, partial (synthetic, 60 replicates)")
        if not base:
            print(buf.getvalue())

        def tamper(name, f, fn, js=False):
            p = d / f
            orig = p.read_text()
            if js:
                j = json.loads(orig)
                fn(j)
                p.write_text(json.dumps(j))
            else:
                t = pd.read_csv(p, dtype={"noaa": str}, float_precision="round_trip")
                fn(t).to_csv(p, index=False)
            remeta()
            with contextlib.redirect_stdout(io.StringIO()):
                bad = not check(d, write=False, data=data, reps=reps, A=A)
            res.append(bad)
            print("[OK]" if bad else "[FALLITO]", f"refused with updated hashes: {name}")
            p.write_text(orig)
            remeta()
        first = lambda t, c, v: t.assign(**{c: t[c].where(t.index != 0, v)})          # noqa: E731
        tamper("cause_map_missing = 999 (Codex 1)", "Q1_YIELD_CELLS.csv", lambda t: first(t, "cause_map_missing", 999))
        tamper("ok100 = 999 (Codex 2)", "Q1_YIELD_CELLS.csv", lambda t: first(t, "ok100", 999))
        tamper("N = 999 (Codex 3)", "Q1_YIELD_CELLS.csv", lambda t: first(t, "N", 999))
        tamper("projected_yield_100 = 999 (Codex 4)", "Q1_YIELD_PROJECTED.csv", lambda t: first(t, "projected_yield_100", 999))
        tamper("p10_g = 999 (Codex 5)", "Q1_QUIET_SUMMARY.json", lambda j: j.update(p10_g=999.0), js=True)
        tamper("d_raw = 999 (Codex 6)", "Q3_PAIRS_main.csv", lambda t: first(t, "d_raw", 999))
        tamper("median_flux_ratio = 999 (Codex 7)", "Q3_SUMMARY_main.csv", lambda t: first(t, "median_flux_ratio", 999))
        tamper("valid_reps = 0 (Codex 8)", "Q3_SUMMARY_main.csv", lambda t: t.assign(valid_reps=t.valid_reps.where(t.valid_reps.isna(), 0)))
        tamper("phi_at_bound inverted (Codex 9)", "Q1_M_EXPLORATORY.json", lambda j: j.update(phi_at_bound=not j["phi_at_bound"]), js=True)
        tamper("M state changed", "Q1_M_EXPLORATORY.json", lambda j: j.update(state="errore di M"), js=True)
        tamper("separation edges changed", "CLASS_EDGES.json", lambda j: j.update(separation_main_l1_ok=[1.0, 2.0]), js=True)
        tamper("a sens100 separation class changed", "Q3_PAIRS_sens100.csv", lambda t: first(t, "sep_class", 4))
        tamper("time distance to t_DPD changed", "Q3_PAIRS_main.csv", lambda t: first(t, "dt_mwo_minus_tdpd_h", 0.0))
        tamper("a summary row dropped", "Q3_SUMMARY_sens100.csv", lambda t: t.drop(index=1))
        tamper("an interval note changed", "Q3_SUMMARY_main.csv", lambda t: first(t, "interval_note", "x"))
        tamper("a quiet availability count changed", "Q1_QUIET_AVAILABILITY.csv", lambda t: first(t, "n_sides", 1))
        tamper("a note removed", "NOTES.json", lambda j: j.pop("bard_mdi"), js=True)
    # A faithfully reported exploratory M failure must not invalidate the remaining descriptive products.
    saved_verdict = A.m_verdict
    try:
        A.m_verdict = lambda unit, truth: dict(verdict="errore", error="synthetic M failure")
        error_prods = dict(prods, Q1_M_EXPLORATORY=Mx.q1_m_fit(data[0], data[1], A))
        with tempfile.TemporaryDirectory() as ed:
            ep = Path(ed)
            Mx.write(error_prods, ep)
            (ep / "META.json").write_text(json.dumps(dict(products_sha256={f.name: sha(f) for f in ep.iterdir() if f.name != "META.json"})))
            with contextlib.redirect_stdout(io.StringIO()):
                accepted_error = check(ep, write=False, data=data, reps=reps, A=A)
            res.append(accepted_error and check.last_receipt["partial"] is True)
            print("[OK]" if res[-1] else "[FALLITO]", "exploratory M error reported consistently, other products recounted (partial)")
    finally:
        A.m_verdict = saved_verdict
    # upstream provenance on synthetic folders (globals redirected, restored afterwards)
    g = globals()
    saved = {k: g[k] for k in ("SEL", "SEL_REC", "L1", "L1_REC", "RELEASE", "PROTOCOL", "FREEZE")}
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        try:
            for k in ("SEL", "SEL_REC", "L1", "L1_REC"):
                g[k] = td / k
                g[k].mkdir()
            g["RELEASE"], g["PROTOCOL"], g["FREEZE"] = td / "rel.csv", td / "prot.md", td / "freeze.json"
            g["RELEASE"].write_text("noaa,day_utc\n")
            g["PROTOCOL"].write_text("frozen")
            g["FREEZE"].write_text(json.dumps(dict(sha256=sha(g["PROTOCOL"]))))
            for n in ("POPULATION.csv", "SAMPLE.csv", "CELLS.csv"):
                (g["SEL"] / n).write_text(n)
            for n in ("L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"):
                (g["L1"] / n).write_text(n)
            prot = sha(g["PROTOCOL"])

            def metas():
                (g["SEL"] / "META.json").write_text(json.dumps(dict(protocol_sha256=prot, mwo_release_sha256=sha(g["RELEASE"]),
                                                                    products_sha256={n: sha(g["SEL"] / n) for n in ("POPULATION.csv", "SAMPLE.csv", "CELLS.csv")})))
                (g["L1"] / "META.json").write_text(json.dumps(dict(protocol_sha256=prot, selection_meta_sha256=sha(g["SEL"] / "META.json"),
                                                                   products_sha256={n: sha(g["L1"] / n) for n in ("L1_RECORDS.csv", "CT_DIAGNOSTIC.csv")})))
                for f, key, m in ((g["SEL_REC"], "selection_meta_sha256", g["SEL"] / "META.json"), (g["L1_REC"], "l1_meta_sha256", g["L1"] / "META.json")):
                    (f / "RECEIPT.json").write_text(json.dumps({"passed": 1, "total": 1, "partial": False, "checks": [{"ok": True}], key: sha(m)}))
                return dict(protocol_sha256=prot, selection_meta_sha256=sha(g["SEL"] / "META.json"), selection_receipt_sha256=sha(g["SEL_REC"] / "RECEIPT.json"),
                            l1_meta_sha256=sha(g["L1"] / "META.json"), l1_receipt_sha256=sha(g["L1_REC"] / "RECEIPT.json"),
                            release_sha256=sha(g["RELEASE"]), m_modules_sha256={q: sha(ROOT / q) for q in M_MODULES}, seed=SEED, reps=REPS)
            meta = metas()
            res.append(all(upstream(meta).values()))
            print("[OK]" if res[-1] else "[FALLITO]", "upstream: a consistent synthetic chain is accepted")
            cases = [("SAMPLE changed with its META unchanged", lambda: (g["SEL"] / "SAMPLE.csv").write_text("changed"), "selection"),
                     ("L1 product changed with its META unchanged", lambda: (g["L1"] / "L1_RECORDS.csv").write_text("changed"), "l1"),
                     ("L1 receipt missing", lambda: (g["L1_REC"] / "RECEIPT.json").unlink(), "l1"),
                     ("selection receipt partial", lambda: (g["SEL_REC"] / "RECEIPT.json").write_text(json.dumps(
                         {"passed": 1, "total": 1, "partial": True, "checks": [{"ok": True}], "selection_meta_sha256": sha(g["SEL"] / "META.json")})), "selection"),
                     ("MWO release differs from the one of the selection", lambda: g["RELEASE"].write_text("other"), "release")]
            for name, fn, key in cases:
                for n in ("POPULATION.csv", "SAMPLE.csv", "CELLS.csv"):
                    (g["SEL"] / n).write_text(n)
                for n in ("L1_RECORDS.csv", "CT_DIAGNOSTIC.csv"):
                    (g["L1"] / n).write_text(n)
                g["RELEASE"].write_text("noaa,day_utc\n")
                meta = metas()
                fn()
                res.append(upstream(meta)[key] is False)
                print("[OK]" if res[-1] else "[FALLITO]", f"upstream refused: {name}")
            meta = metas()
            res.append(upstream(dict(meta, reps=200))["seed_reps"] is False)
            print("[OK]" if res[-1] else "[FALLITO]", "upstream refused: META with reps != 2000")
        finally:
            g.update(saved)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
