"""Independent recount of the HMI follow-ups (Q1, Q2, Q3); does not import scripts/hmi_followups.py.

After the frozen run: (1) rebuilds sample S, the Q1 window, the matrices and the contrast estimates with its own code;
(2) recomputes every SE from the M parameters saved per row (individual variance exp(a + b (log Phi - mean)), temporal
AR(1) with cross-hemisphere correlation kappa on the cells), for the estimates and for every validation row;
(3) recounts the validation summary and the acceptance from RAW.

    .venv/bin/python scripts/hmi_followups_recount.py --selftest
    .venv/bin/python scripts/hmi_followups_recount.py --check        # after validation and run
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist, norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import run_p2  # noqa: E402  (shared upstream: catalogue sample S and SILSO activity)

VAL = ROOT / "results/HMI_FOLLOWUPS_VALIDATION"
RUN = ROOT / "results/HMI_FOLLOWUPS"
OUT = ROOT / "results/HMI_FOLLOWUPS_RECOUNT"
Z = norm.ppf(1 - 0.0125)


def sample():
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    return d[np.isfinite(d["A_monthly"])].reset_index(drop=True)


def window(d, symmetric=False):
    ph25 = d.loc[d.cyc == 25, "phase"].max()
    m = (d.cyc == 25) | ((d.cyc == 24) & (d.phase <= ph25))
    if symmetric:
        m &= d.phase >= d.loc[d.cyc == 24, "phase"].min()
    return m.to_numpy()


def coef_rows(X, w):
    """(X' W X)^-1 X' W via a QR of sqrt(W) X (independent of p2d.wls_row's pinv)."""
    sw = np.sqrt(w)
    Q, R = np.linalg.qr(X * sw[:, None])
    return np.linalg.solve(R, Q.T) * sw[None, :]


def contrast(d, which, symmetric=False):
    s, cyc, hem = d.sinlat.to_numpy(), d.cyc.to_numpy(), d.hemisphere.to_numpy()
    w = d.phi.to_numpy(float)
    ind = lambda c, h: ((cyc == c) & (hem == h)).astype(float)  # noqa: E731
    if which.startswith("q1"):
        m = window(d, symmetric)
        if which == "q1":
            X = np.column_stack([s * (cyc == 24), s * (cyc == 25)])
            c = np.array([-1.0, 1.0])
        else:
            X = np.column_stack([s * ind(c_, h_) for c_ in (24, 25) for h_ in "NS"])
            c = np.array([-0.5, -0.5, 0.5, 0.5])
        return m, (c @ coef_rows(X[m], w[m]))
    m = np.ones(len(d), bool)
    base = np.column_stack([ind(c_, h_) for c_, h_ in run_p2.CH])
    if which in ("q2", "q2_hem"):
        ph = d.phase.to_numpy() if which == "q2" else d.phase_hem.to_numpy()
        X = np.column_stack([base, ph, ph ** 2, ph ** 3, d.A_monthly.to_numpy() - 1])
        return m, coef_rows(X, w)[-1]
    lp = np.log10(w)
    mlog = np.sum(w * lp) / np.sum(w)
    act = (d.A_monthly.to_numpy() - 1) * s
    if which == "q3_b":
        X = np.column_stack([base * s[:, None], (lp - mlog) * s, act])
        return m, coef_rows(X, w)[4]
    q = int(which[-1])
    qi = np.searchsorted(np.quantile(w, [0.2, 0.4, 0.6, 0.8]), w, side="right")
    X = np.column_stack([base * s[:, None]] + [(qi == j) * s for j in range(1, 5)] + [act])
    return m, coef_rows(X, w)[q + 2]


def se_from_params(d, m, a, p):
    w = d.phi.to_numpy(float)[m]
    lp = np.log(w)
    sig2 = np.exp(p["var_a"] + p["var_b"] * (lp - lp.mean()))
    key = pd.MultiIndex.from_arrays([d.CR.to_numpy()[m].astype(int), d.hemisphere.to_numpy()[m]])
    codes, uniq = pd.factorize(key)
    b = np.bincount(codes, weights=a)
    t = np.array([c for c, _ in uniq], float)
    h = np.array([x for _, x in uniq])
    lag = np.abs(t[:, None] - t[None, :])
    K = np.where(h[:, None] == h[None, :], 1.0, p["kappa"]) * p["phi"] ** lag
    return math.sqrt(p["sigma_x2"] * float(b @ K @ b) + float(np.sum(a ** 2 * sig2)))


def cp_upper(k, n):
    return 1.0 if k >= n else float(beta_dist.ppf(0.95, k + 1, n - k))


def hemispheric_phase(d):
    sm = run_p2.load_silso()["smooth13"]
    mins = {(c, h): pd.Timestamp(sm.loc[lo:hi, h].idxmin() + "-01")
            for c, (lo, hi) in {24: ("2007-01", "2010-12"), 25: ("2018-01", "2021-12")}.items() for h in "NS"}
    return np.array([(t - mins[(int(c), h)]).days / 365.25 / 11 for t, c, h in zip(d.t, d.cyc, d.hemisphere)])


def check():
    d = sample()
    d["phase_hem"] = hemispheric_phase(d)
    res = []

    def ok(name, cond, value=""):
        res.append(dict(name=name, ok=bool(cond), value=str(value)))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    est = pd.read_csv(RUN / "ESTIMATES.csv")
    which = {"Q1 main (T2 window)": ("q1", False, d.gamma), "Q1 symmetric window": ("q1", True, d.gamma),
             "Q1 hemisphere-averaged": ("q1_hem", False, d.gamma), "Q2": ("q2", False, d.lat.abs()),
             "Q2 hemispheric phase": ("q2_hem", False, d.lat.abs()), "Q3 b (log10 Phi)": ("q3_b", False, d.gamma)}
    which.update({f"Q3 quintile {q} - 1": (f"q3_q{q}", False, d.gamma) for q in range(2, 6)})
    worst_b = worst_se = 0.0
    for r in est.itertuples():
        wname, sym, y = which[r.analysis]
        m, a = contrast(d, wname, sym)
        b = float(a @ y.to_numpy()[m])
        se = se_from_params(d, m, a, r._asdict())
        worst_b = max(worst_b, abs(b - r.beta) / max(abs(r.beta), 1e-12))
        worst_se = max(worst_se, abs(se / r.se - 1))
        ok(f"{r.analysis}: interval = beta -/+ z SE", abs(r.lo - (r.beta - Z * r.se)) < 1e-9 * r.se
           and abs(r.hi - (r.beta + Z * r.se)) < 1e-9 * r.se)
    ok("estimates recomputed independently", worst_b < 1e-8, f"max rel {worst_b:.1e}")
    ok("SE recomputed from saved M parameters", worst_se < 1e-6, f"max rel {worst_se:.1e}")
    raw = pd.read_csv(VAL / "RAW.csv.gz")
    worst = 0.0
    sample_rows = raw[raw.verdict != "errore"].groupby(["test", "kind", "scenario", "sd_e"]).head(3)
    for r in sample_rows.itertuples():
        m, a = contrast(d, r.test, False)
        worst = max(worst, abs(se_from_params(d, m, a, r._asdict()) / r.se - 1))
    ok("validation SE recomputed on 3 rows per configuration", worst < 1e-6, f"max rel {worst:.1e}")
    summ = pd.read_csv(VAL / "SUMMARY.csv")
    acc_saved = pd.read_csv(VAL / "ACCEPTANCE.csv").iloc[0].to_dict()
    acc = {}
    for t in ("q1", "q2", "q2_hem"):
        rows = []
        for (kind, scen, sd), g in raw[(raw.test == t) & (raw.effect == 0)].groupby(["kind", "scenario", "sd_e"]):
            f = int(g.verdict.isin(["supportato", "opposto"]).sum())
            rows.append(dict(kind=kind, scenario=scen, cp=cp_upper(f, len(g))))
        acc[t] = all(r["cp"] <= 0.04 for r in rows if r["scenario"] in (0, 1, 2) and r["kind"].endswith("null"))
    ok("acceptance recounted from RAW", acc == {k: bool(v) for k, v in acc_saved.items()}, acc)
    ok("summary has one row per configuration", len(summ) == raw.groupby(["test", "kind", "scenario", "sd_e"]).ngroups)
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "RECEIPT.json").write_text(json.dumps(dict(checks=res, passed=sum(r["ok"] for r in res), total=len(res)),
                                                 indent=2) + "\n")
    return all(r["ok"] for r in res)


def selftest():
    d = sample()
    d["phase_hem"] = hemispheric_phase(d)
    s, cyc = d.sinlat.to_numpy(), d.cyc.to_numpy()
    m, a = contrast(d, "q1")
    y = 20 * s * (cyc == 24) + 17 * s * (cyc == 25)
    c1 = abs(a @ y[m] + 3) < 1e-9 and int(m.sum()) == 2238
    m2, a2 = contrast(d, "q2_hem")
    p = dict(var_a=4.0, var_b=0.2, phi=0.5, kappa=0.3, sigma_x2=9.0)
    c2 = np.isfinite(se_from_params(d, m2, a2, p))
    c3 = abs(cp_upper(0, 100) - (1 - 0.05 ** (1 / 100))) < 1e-12
    # equivalence with the P2f variance formula (selftest only; --check never uses P2f code)
    from sharpbl import p2f_pilot as P, p2f_validation as V
    w = d.phi.to_numpy(float)[m2]
    codes, uniq = P.cell_keys(d.CR.to_numpy()[m2].astype(int), d.hemisphere.to_numpy()[m2])
    u = dict(test="T3", codes=codes, uniq=uniq, w=w, y=np.zeros(len(w)), Xf=np.ones((len(w), 1)), a_row=a2)
    lp = np.log(w)
    sig2 = np.exp(p["var_a"] + p["var_b"] * (lp - lp.mean()))
    ref = math.sqrt(V.m_variance_given(u, sig2, p["phi"], p["kappa"], p["sigma_x2"]))
    c4 = abs(se_from_params(d, m2, a2, p) / ref - 1) < 1e-10
    for n, c in (("Q1 contrast -3 on 2238 regions (independent QR rows)", c1), ("SE from parameters finite", c2),
                 ("Clopper-Pearson upper bound", c3), ("SE formula equals P2f m_variance_given", c4)):
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    return c1 and c2 and c3 and c4


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
