"""Independent recompute of the T5-D2 oracle SEs for A2, A3 and A2p (docs/T5_ORACLE_SE_RECOMPUTE_NOTE.md,
frozen in 61f8884 before this code was written), with clarification C1
(docs/T5_ORACLE_SE_RECOMPUTE_NOTE_C1.md) after the review of 1e55cf8.

Shared code reused as is (note §2): P.build_design, V.seed_null/seed_effect/responses, V.units, V.cell_residuals,
P.varfun_fit. The independent part (note §3) does not import diag_t5_oracle and does not call V.cell_level,
P.ar1_k or V.procedure_m. The producer's functions are called only to extract its components for comparison (b).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_oracle_se_recompute.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_oracle_se_recompute.py --run --workers 12
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2f_pilot as P, p2f_validation as V  # noqa: E402

NOTE = ROOT / "docs/T5_ORACLE_SE_RECOMPUTE_NOTE.md"
NOTE_C1 = ROOT / "docs/T5_ORACLE_SE_RECOMPUTE_NOTE_C1.md"
RAW = ROOT / "results/T5_ORACLE/ORACLE_RAW.csv.gz"
OUT = ROOT / "results/T5_ORACLE_SE_RECOMPUTE"

# ---------------------------------------------------------------- constants from the protocol texts (note §3)
ETA0 = 3.56e-25
SX2 = (0.5 * ETA0) ** 2
SIG2 = ETA0 ** 2
Z = float(norm.ppf(0.9875))
AR1_SCEN = {1: (0.5, 0.0), 2: (0.9, 0.0)}          # P2f protocol, scenarios 1 and 2
STEP_L = {7: 20, 10: 13}
KAPPA_STAR = {7: 0.0, 10: 0.98}
PHI_STAR_DOC = {7: 0.9106, 10: 0.8657}
RTOL = 1e-9
ATOL_FACTOR = 1e-12
JOBS = ([("null", 7, 0.0, k) for k in range(10_000)]
        + [("effect", 7, e, k) for e in (-0.1, -0.2, -0.3, -0.35) for k in range(2000)]
        + [("null", 10, 0.0, k) for k in range(10_000)]
        + [("null", s, 0.0, k) for s in (1, 2) for k in range(2000)])
SELFTEST_SEED = 29_500_000                          # disjoint from P2f, T5-D2 and their pretests


class SharedError(Exception):
    """Expected error raised by the shared variance-function code or by non-positive cell variances."""

    def __init__(self, cls, msg):
        super().__init__(msg)
        self.cls = cls


# ---------------------------------------------------------------- independent part

def k_steps_ind(lag, L):
    return np.clip(1.0 - lag / L, 0.0, None)


def k_true_ind(t, h, scen):
    lag = np.abs(np.subtract.outer(t, t)).astype(float)
    same = np.equal.outer(h, h)
    if scen in STEP_L:
        k = k_steps_ind(lag, STEP_L[scen])
        return k * same if scen == 7 else k
    phi, kappa = AR1_SCEN[scen]
    k = phi ** lag
    k[~same] *= kappa
    return k


def k_ar1_ind(t, h, phi, kappa):
    lag = np.abs(np.subtract.outer(t, t)).astype(float)
    k = phi ** lag
    k[~np.equal.outer(h, h)] *= kappa
    return k


def phi_star_ind(L):
    tau = np.arange(219, dtype=float)
    target = k_steps_ind(tau, L)
    best, best_sse = None, np.inf
    for j in range(9801):                           # 0.0000 ... 0.9800
        g = j / 10_000
        sse = float(np.sum((g ** tau - target) ** 2))
        if sse < best_sse:
            best, best_sse = g, sse
    return best


def cell_var_ind(k_of_i, agg, s2, ncell):
    v = np.zeros(ncell)
    np.add.at(v, k_of_i, agg * agg * s2)
    return v


def s2_est_ind(u):
    """Shared: residuals and variance-function fit. Independent: the composition of s^2."""
    try:
        e, h = V.cell_residuals(u)
        lp = np.log(u["phi"])
        ab, _, _ = P.varfun_fit(e, h, u["codes"], lp - lp.mean())
    except V.CandidateError as exc:
        raise SharedError("varfun", str(exc))
    s2 = np.exp(ab[0] + ab[1] * (lp - lp.mean()))
    if not np.all(np.isfinite(s2)):
        raise SharedError("varfun", "varianza individuale non finita")
    return s2


def arm_ind(beta, b, K, v):
    ind = float(np.sum(b * b * v))
    tmp = float(b @ K @ b)
    var = SX2 * tmp + ind
    se = float(np.sqrt(var))
    return dict(bKb=tmp, ind=ind, var=var, se=se, lo=beta - Z * se, hi=beta + Z * se)


def flags(lo, hi, bt):
    verdict = "supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso")
    return verdict, int(lo <= bt <= hi), int(lo > bt), int(hi < bt)


# ---------------------------------------------------------------- tolerance rule (note §4; clarification C1 §2)

def ratio(x, y, scale):
    """Per-component |x_i - y_i| / (atol + rtol |y_i|), then the maximum; <= 1 passes.

    Any non-finite value on either side, a shape mismatch, an empty input or a non-finite scale gives inf
    (rejected). A zero denominator passes only for an exact zero difference.
    """
    x, y = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))
    if x.shape != y.shape or x.size == 0 or not np.isfinite(scale):
        return np.inf
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return np.inf
    num = np.abs(x - y)
    den = ATOL_FACTOR * abs(scale) + RTOL * np.abs(y)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.where(num == 0, 0.0, np.inf))
    return float(np.max(r))


def worst(values):
    """Maximum that never skips a NaN: any NaN gives inf."""
    v = np.asarray(values, float)
    return np.inf if v.size == 0 or np.isnan(v).any() else float(np.max(v))



def independent(u, scen, bt, phi_star):
    t_raw, hem = u["cell_cr"], u["cell_hem"]
    t = (t_raw - t_raw.min()).astype(float)
    h = (np.asarray(hem) == "S").astype(int)
    b = np.asarray(u["g"], float)
    n = len(b)
    beta = float(u["beta"])
    Kt = k_true_ind(t, h, scen)
    out = {}
    v_true = cell_var_ind(u["k_of_i"], u["agg"], np.full(len(u["agg"]), SIG2), n)
    out["A3"] = arm_ind(beta, b, Kt, v_true)
    out["A3"]["v"] = v_true
    try:
        s2 = s2_est_ind(u)
        v_est = cell_var_ind(u["k_of_i"], u["agg"], s2, n)
        if not (np.all(np.isfinite(v_est)) and np.all(v_est > 0)):
            raise SharedError("cell", "varianze di cella non finite o nulle")
        out["A2"] = arm_ind(beta, b, Kt, v_est)
        out["A2"]["v"] = v_est
        if scen in STEP_L:
            out["A2p"] = arm_ind(beta, b, k_ar1_ind(t, h, phi_star[scen], KAPPA_STAR[scen]), v_est)
            out["A2p"]["v"] = v_est
    except SharedError as exc:
        out["A2"] = dict(err=exc.cls, msg=str(exc))
        if scen in STEP_L:
            out["A2p"] = dict(err=exc.cls, msg=str(exc))
    for r in out.values():
        if "err" not in r:
            r["verdict"], r["covered"], r["below"], r["above"] = flags(r["lo"], r["hi"], bt)
    return beta, b, out


# ---------------------------------------------------------------- producer components (note §4b)

def producer(u, scen):
    from sharpbl import diag_t5_oracle as D
    out = {}
    _, _, vc, b, t, h, ind_t = V.cell_level(u, np.full(len(u["y"]), D.SIG2_TRUE))
    Kt = D.k_true(t, h, scen)
    out["b"] = b
    out["A3"] = dict(v=vc, ind=ind_t, bKb=float(b @ Kt @ b), var=D.SX2_TRUE * float(b @ Kt @ b) + ind_t)
    try:
        s2e = D.est_sig2(u)
        _, _, vce, be, te, he, ind_e = V.cell_level(u, s2e)
        if not (np.isfinite(vce).all() and (vce > 0).all()):
            raise V.CandidateError("varianze di cella non finite o nulle")
        out["A2"] = dict(v=vce, ind=ind_e, bKb=float(be @ Kt @ be), var=D.SX2_TRUE * float(be @ Kt @ be) + ind_e)
        if scen in D.PHI_STAR:
            Ka = P.ar1_k(te, he, D.PHI_STAR[scen], D.KAPPA_STAR[scen])
            out["A2p"] = dict(v=vce, ind=ind_e, bKb=float(be @ Ka @ be), var=D.SX2_TRUE * float(be @ Ka @ be) + ind_e)
    except V.CandidateError as exc:
        out["A2"] = dict(err=str(exc))
        if scen in D.PHI_STAR:
            out["A2p"] = dict(err=str(exc))
    return out


COMPONENTS = ("b", "v", "ind", "bKb", "sx2_bKb", "var")


def compare_components(b, ind_out, prod):
    """Per arm: producer state and error class, one tolerance ratio per component, and their maximum."""
    res = {}
    bscale = float(np.max(np.abs(prod["b"]))) if np.size(prod["b"]) else np.nan
    rb = ratio(b, prod["b"], bscale)
    for arm, r in ind_out.items():
        p = prod.get(arm)
        row = dict(prod_state="missing" if p is None else ("errore" if "err" in p else "valido"),
                   prod_err_class=raw_class(p["err"]) if p is not None and "err" in p else "")
        if p is None or "err" in r or "err" in p:
            row.update({f"r_{c}": np.nan for c in COMPONENTS}, comp_ratio=np.nan)
        else:
            rs = dict(r_b=rb, r_v=ratio(r["v"], p["v"], ETA0 ** 2), r_ind=ratio(r["ind"], p["ind"], ETA0 ** 2),
                      r_bKb=ratio(r["bKb"], p["bKb"], bscale ** 2),
                      r_sx2_bKb=ratio(SX2 * r["bKb"], SX2 * p["bKb"], ETA0 ** 2),
                      r_var=ratio(r["var"], p["var"], ETA0 ** 2))
            row.update(rs, comp_ratio=worst(list(rs.values())))
        res[arm] = row
    return res


# ---------------------------------------------------------------- one catalogue

_DESIGN = None
_PHI_STAR = None


def _init():
    global _DESIGN, _PHI_STAR
    if _DESIGN is None:
        _DESIGN = P.build_design()
        _PHI_STAR = {L: phi_star_ind(STEP_L[L]) for L in STEP_L}


def regen(kind, s, e, k, seed=None):
    if seed is None:
        seed = V.seed_null(s, k) if kind == "null" else V.seed_effect(s, e, k)
    dd = V.responses(_DESIGN, s, np.random.default_rng(seed), e)
    u = V.units(dd, "T5")
    assert u["n_check"] == V.EXPECTED["T5"]
    return u


def job(spec, seed=None):
    _init()
    kind, s, e, k = spec
    rows = []
    try:
        u = regen(kind, s, e, k, seed)
        bt = e * ETA0
        beta, b, out = independent(u, s, bt, _PHI_STAR)
        comp = compare_components(b, out, producer(u, s))
    except Exception as exc:                        # unexpected: recorded, never hidden
        return [dict(kind=kind, scenario=s, effect=e, k=k, arm="ALL", status="eccezione", err_class="exception",
                     msg=repr(exc))]
    for arm, r in out.items():
        row = dict(kind=kind, scenario=s, effect=e, k=k, arm=arm, beta=beta, beta_true=bt)
        if "err" in r:
            row.update(status="errore", err_class=r["err"], msg=r["msg"])
        else:
            row.update(status="valido", err_class="", se=r["se"], lo=r["lo"], hi=r["hi"], verdict=r["verdict"],
                       covered=r["covered"], below=r["below"], above=r["above"], var=r["var"])
        row.update(comp[arm])
        rows.append(row)
    return rows


# ---------------------------------------------------------------- comparison with ORACLE_RAW (note §4a, §5, §6; C1 §3)

def raw_class(msg):
    m = str(msg)
    if "funzione di varianza" in m or "varianza individuale" in m:
        return "varfun"
    if "varianze di cella" in m:
        return "cell"
    return "other"


ROW_COLS = ["kind", "scenario", "effect", "k", "arm", "status", "err_class", "msg", "prod_state", "prod_err_class",
            "raw_state", "raw_err_class", "outcome", "reason", "beta", "beta_true", "se", "se_raw", "lo", "hi", "var",
            "verdict", "covered", "below", "above", "raw_ratio", "beta_ratio_A0", "comp_ratio"] + [f"r_{c}" for c in COMPONENTS]


def valid_numbers(x):
    vals = [x.get(c) for c in ("beta", "se", "lo", "hi", "var")]
    return all(v is not None and np.isfinite(v) for v in vals) and x["se"] > 0 and x["var"] > 0


def compare_raw(rows, raw):
    key = ["kind", "scenario", "effect", "k", "arm"]
    r = raw.set_index(key)
    a0 = raw[raw.arm == "A0"].set_index(["kind", "scenario", "effect", "k"])["beta"]
    out = []
    for x in rows:
        x = dict(x)
        if x["arm"] == "ALL":
            x.update(outcome="unexpected", reason="exception in catalogue")
            out.append(x)
            continue
        kk = (x["kind"], x["scenario"], x["effect"], x["k"], x["arm"])
        if kk not in r.index or isinstance(r.loc[kk], pd.DataFrame):
            x.update(outcome="unexpected", reason="raw key missing or duplicated")
            out.append(x)
            continue
        ref = r.loc[kk]
        b0 = a0.get(kk[:4])
        x["beta_ratio_A0"] = ratio(x["beta"], b0, ETA0) if b0 is not None else np.inf
        ref_err = ref["verdict"] == "errore"
        x["raw_state"] = "errore" if ref_err else "valido"
        x["raw_err_class"] = raw_class(ref["error"]) if ref_err else ""
        states = (x["status"], x.get("prod_state"), x["raw_state"])
        if x["arm"] == "A3" and "errore" in states:
            x.update(outcome="unexpected", reason="A3 error")
        elif states == ("errore", "errore", "errore"):
            same = x["err_class"] == x.get("prod_err_class") == x["raw_err_class"] and x["err_class"] in ("varfun", "cell")
            x.update(outcome="errore_atteso" if same else "unexpected", reason="" if same else "error classes differ")
        elif states != ("valido", "valido", "valido"):
            x.update(outcome="unexpected", reason=f"states ind/prod/raw = {'/'.join(map(str, states))}")
        elif not valid_numbers(x):
            x.update(outcome="mismatch", reason="non-finite or non-positive value in recompute")
        else:
            rr = worst([ratio(x["beta"], ref["beta"], ETA0), ratio(x["se"], ref["se"], ETA0),
                        ratio(x["lo"], ref["lo"], ETA0), ratio(x["hi"], ref["hi"], ETA0),
                        ratio(x["beta_true"], ref["beta_true"], ETA0)])
            same_flags = (x["verdict"] == ref["verdict"] and x["covered"] == int(ref["covered"])
                          and x["below"] == int(ref["below"]) and x["above"] == int(ref["above"]))
            x["raw_ratio"], x["se_raw"] = rr, ref["se"]
            reasons = [n for n, bad in (("raw", not rr <= 1), ("flags", not same_flags),
                                        ("components", not x.get("comp_ratio", np.inf) <= 1),
                                        ("beta A0", not x["beta_ratio_A0"] <= 1)) if bad]
            x.update(outcome="mismatch" if reasons else "ok", reason=",".join(reasons))
        out.append(x)
    return pd.DataFrame(out).reindex(columns=ROW_COLS)


def expected_keys(jobs):
    return {(kd, s, e, k, arm) for kd, s, e, k in jobs for arm in (("A2", "A3", "A2p") if s in STEP_L else ("A2", "A3"))}


def keyset_check(df, raw, jobs):
    """Exact key sets and uniqueness (C1 §4): results, raw rows of the recomputed arms, raw A0."""
    exp = expected_keys(jobs)
    res = df[df.arm != "ALL"]
    got = list(map(tuple, res[["kind", "scenario", "effect", "k", "arm"]].itertuples(index=False)))
    rr = raw[raw.arm.isin(["A2", "A3", "A2p"])]
    raw_got = list(map(tuple, rr[["kind", "scenario", "effect", "k", "arm"]].itertuples(index=False)))
    a0 = list(map(tuple, raw[raw.arm == "A0"][["kind", "scenario", "effect", "k"]].itertuples(index=False)))
    c = dict(n_expected=len(exp), n_rows=len(got), rows_unique=len(got) == len(set(got)), rows_exact=set(got) == exp,
             n_raw=len(raw_got), raw_unique=len(raw_got) == len(set(raw_got)), raw_exact=set(raw_got) == exp,
             n_a0=len(a0), a0_unique=len(a0) == len(set(a0)), a0_exact=set(a0) == set(map(tuple, jobs)),
             n_all_rows=int((df.arm == "ALL").sum()))
    c["passed"] = all(c[k] for k in ("rows_unique", "rows_exact", "raw_unique", "raw_exact", "a0_unique", "a0_exact")) \
        and c["n_all_rows"] == 0
    return c


def summarize(df):
    df = df.reindex(columns=ROW_COLS)
    g = df.groupby(["kind", "scenario", "effect", "arm"], dropna=False)
    s = g.agg(n=("k", "size"), ok=("outcome", lambda o: int((o == "ok").sum())),
              errore_atteso=("outcome", lambda o: int((o == "errore_atteso").sum())),
              mismatch=("outcome", lambda o: int((o == "mismatch").sum())),
              unexpected=("outcome", lambda o: int((o == "unexpected").sum())),
              max_raw_ratio=("raw_ratio", "max"), max_comp_ratio=("comp_ratio", "max"),
              max_beta_ratio_A0=("beta_ratio_A0", "max"),
              **{f"max_r_{c}": (f"r_{c}", "max") for c in COMPONENTS}).reset_index()
    valid = df[(df.outcome == "ok") | (df.outcome == "mismatch")].copy()
    valid["abs_se"] = (pd.to_numeric(valid.se) - pd.to_numeric(valid.se_raw)).abs()
    valid["rel_se"] = valid.abs_se / pd.to_numeric(valid.se_raw).abs()
    m = valid.groupby(["kind", "scenario", "effect", "arm"], dropna=False).agg(
        max_abs_se=("abs_se", "max"), max_rel_se=("rel_se", "max")).reset_index()
    return s.merge(m, how="left", on=["kind", "scenario", "effect", "arm"])


def evaluate(df, raw, jobs, consts):
    """Final outcome predicate (note §6; C1 §4-5)."""
    s = summarize(df)
    kc = keyset_check(df, raw, jobs)
    res = df[df.arm != "ALL"]
    beta_all = bool(len(res) > 0 and (pd.to_numeric(res.beta_ratio_A0) <= 1).all())
    cc_ok = all(v for k, v in consts.items() if k != "phi_star")
    counts = dict(ok=int((df.outcome == "ok").sum()), errore_atteso=int((df.outcome == "errore_atteso").sum()),
                  mismatch=int((df.outcome == "mismatch").sum()), unexpected=int((df.outcome == "unexpected").sum()),
                  outcome_missing=int(df.outcome.isna().sum()))
    passed = (kc["passed"] and beta_all and cc_ok and counts["mismatch"] == 0 and counts["unexpected"] == 0
              and counts["outcome_missing"] == 0 and counts["ok"] + counts["errore_atteso"] == kc["n_expected"])
    return passed, dict(keys=kc, beta_regeneration_check=beta_all, constants_ok=cc_ok, **counts), s


# ---------------------------------------------------------------- provenance

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def constants_check(phi_star):
    from sharpbl import diag_t5_oracle as D
    return dict(eta0_equal=ETA0 == V.ETA_BAR, sx2_equal=SX2 == D.SX2_TRUE, sig2_equal=SIG2 == D.SIG2_TRUE,
                z_equal=Z == V.Z, ar1_equal=all(V.SCENARIOS[s]["phi"] == AR1_SCEN[s][0] and V.SCENARIOS[s]["kappa"] == AR1_SCEN[s][1] for s in AR1_SCEN),
                phi_star=phi_star, phi_star_doc_equal=all(round(phi_star[s], 4) == PHI_STAR_DOC[s] for s in phi_star),
                phi_star_producer_equal=all(phi_star[s] == D.PHI_STAR[s] for s in phi_star),
                kappa_star_equal=KAPPA_STAR == D.KAPPA_STAR)


# ---------------------------------------------------------------- selftest (note §7.2; C1 §6): no run catalogue

def _fake_raw(rows):
    fake = [dict(kind=r["kind"], scenario=r["scenario"], effect=r["effect"], k=r["k"], arm=r["arm"], beta=r["beta"],
                 beta_true=r["beta_true"], se=r.get("se"), lo=r.get("lo"), hi=r.get("hi"),
                 verdict=r.get("verdict", "errore") if r["status"] == "valido" else "errore", covered=r.get("covered", 0),
                 below=r.get("below", 0), above=r.get("above", 0),
                 error="" if r["status"] == "valido" else "funzione di varianza: ottimizzazione non valida") for r in rows]
    fake.append(dict(fake[0], arm="A0", verdict="non deciso", error=""))
    return pd.DataFrame(fake)


def selftest():
    res = []

    def ok(name, cond):
        res.append((name, bool(cond)))

    # hand-built case: 3 cells, eta0 scaled to 1 for the hand arithmetic
    t = np.array([0.0, 1.0, 2.0]); h = np.array([0, 0, 1]); b = np.array([1.0, -2.0, 1.0])
    K7 = k_true_ind(t, h, 7)
    ok("K7 by hand", np.allclose(K7, [[1, .95, 0], [.95, 1, 0], [0, 0, 1]], rtol=0, atol=1e-15))
    ok("bKb sc7 = 2.2", abs(float(b @ K7 @ b) - 2.2) < 1e-14)
    ok("bKb sc10 = 4/13", abs(float(b @ k_true_ind(t, h, 10) @ b) - 4 / 13) < 1e-14)
    ok("bKb sc1 = 4", abs(float(b @ k_true_ind(t, h, 1) @ b) - 4.0) < 1e-14)
    ok("K sc2 cross-hem zero", k_true_ind(t, h, 2)[0, 2] == 0.0)
    v = cell_var_ind(np.array([0, 0, 1, 2]), np.array([1.0, 2.0, 1.0, 1.0]), np.array([1.0, 1.0, 2.0, 3.0]), 3)
    ok("cell variances [5,2,3]", np.array_equal(v, [5.0, 2.0, 3.0]))
    ok("individual part 16", float(np.sum(b * b * v)) == 16.0)
    ok("var = 0.25*2.2 + 16", abs(0.25 * float(b @ K7 @ b) + 16.0 - 16.55) < 1e-13)
    ok("flags", flags(-3.0, -1.0, -2.0) == ("supportato", 1, 0, 0) and flags(-1.0, 1.0, -2.0) == ("non deciso", 0, 1, 0))
    ps = {s: phi_star_ind(L) for s, L in STEP_L.items()}
    ok("phi* documented", round(ps[7], 4) == 0.9106 and round(ps[10], 4) == 0.8657)

    # tolerance rule (Codex blocking 1 and 2)
    ok("tol pass 1e-12 rel", ratio(ETA0 * (1 + 1e-12), ETA0, ETA0) <= 1)
    ok("tol catches 1e-6 rel", ratio(ETA0 * (1 + 1e-6), ETA0, ETA0) > 1)
    ok("tol near zero uses atol", ratio(1e-40, 0.0, ETA0) <= 1 and ratio(1e-30, 0.0, ETA0) > 1)
    ok("zero vs zero with zero scale passes", ratio(0.0, 0.0, 0.0) == 0.0)
    ok("nonzero vs zero with zero scale fails", ratio(1e-300, 0.0, 0.0) == np.inf)
    ok("vector large component altered caught", ratio(np.array([1.0, 2.0 * (1 + 1e-6)]), np.array([1.0, 2.0]), 2.0) > 1)
    ok("vector small component altered caught (per component)",
       ratio(np.array([1.0, 1e-6 + 1e-10]), np.array([1.0, 1e-6]), 1.0) > 1)
    for bad in (np.nan, np.inf, -np.inf):
        ok(f"scalar {bad} in candidate rejected", ratio(bad, ETA0, ETA0) == np.inf)
        ok(f"scalar {bad} in reference rejected", ratio(ETA0, bad, ETA0) == np.inf)
        ok(f"vector {bad} in second position rejected", ratio(np.array([1.0, bad]), np.array([1.0, 1.0]), 1.0) == np.inf)
    ok("non-finite scale rejected", ratio(1.0, 1.0, np.nan) == np.inf)
    ok("worst never skips NaN", worst([0.1, np.nan]) == np.inf and worst([np.nan, 0.1]) == np.inf)

    # selftest catalogues: seeds outside every run, ORACLE_RAW never read
    _init()
    specs = [("null", 7, 0.0, 0), ("effect", 7, -0.3, 1), ("null", 10, 0.0, 2), ("null", 1, 0.0, 3), ("null", 2, 0.0, 4)]
    all_rows = []
    for j, sp in enumerate(specs):
        rows = job(sp, seed=SELFTEST_SEED + j)
        all_rows += rows
        good = all(r["status"] == "valido" and r["prod_state"] == "valido" and r["comp_ratio"] <= 1 for r in rows)
        ok(f"components agree, selftest catalogue {sp[0]} {sp[1]} {sp[2]}", good and len(rows) == (3 if sp[1] in STEP_L else 2))
    u = regen("null", 7, 0.0, 0, seed=SELFTEST_SEED)
    beta, bb, out = independent(u, 7, 0.0, _PHI_STAR)
    prod = producer(u, 7)
    p1 = {**prod, "A3": dict(prod["A3"], var=prod["A3"]["var"] * (1 + 1e-7))}
    ok("altered producer variance caught", compare_components(bb, out, p1)["A3"]["comp_ratio"] > 1)
    p2 = {**prod, "A3": dict(prod["A3"], var=np.nan)}
    ok("producer NaN variance caught", compare_components(bb, out, p2)["A3"]["comp_ratio"] == np.inf)
    vv = prod["A3"]["v"].copy(); vv[5] = np.nan
    p3 = {**prod, "A3": dict(prod["A3"], v=vv)}
    ok("producer NaN in v (not first) caught", compare_components(bb, out, p3)["A3"]["r_v"] == np.inf)
    cc = constants_check(_PHI_STAR)
    ok("constants", all(v for k, v in cc.items() if k != "phi_star"))

    # classification against fake raws built from selftest catalogues (Codex blocking 1 and 3)
    rows = job(("null", 7, 0.0, 0), seed=SELFTEST_SEED)
    fr = _fake_raw(rows)
    arm_of = lambda d, a: d.set_index("arm").loc[a]
    ok("fake raw: all ok", set(compare_raw(rows, fr).outcome) == {"ok"})
    f2 = fr.copy(); f2.loc[f2.arm == "A2", "se"] *= 1 + 1e-6
    ok("fake raw: altered SE -> mismatch", arm_of(compare_raw(rows, f2), "A2").outcome == "mismatch")
    r_nan = [dict(r, se=np.nan) if r["arm"] == "A2" else r for r in rows]
    ok("candidate SE NaN -> not ok", arm_of(compare_raw(r_nan, fr), "A2").outcome == "mismatch")
    f_inf = fr.copy(); f_inf.loc[f_inf.arm == "A3", "hi"] = np.inf
    ok("raw hi inf -> not ok", arm_of(compare_raw(rows, f_inf), "A3").outcome == "mismatch")
    r_comp = [dict(r, comp_ratio=np.nan) if r["arm"] == "A2" else r for r in rows]
    ok("component ratio NaN -> not ok", arm_of(compare_raw(r_comp, fr), "A2").outcome == "mismatch")
    f3 = fr.copy(); f3.loc[f3.arm == "A2p", ["verdict", "error"]] = ["errore", "funzione di varianza: x"]
    ok("raw error vs value -> unexpected", arm_of(compare_raw(rows, f3), "A2p").outcome == "unexpected")
    err = dict(status="errore", err_class="varfun", msg="x")
    f4 = fr.copy(); f4.loc[f4.arm == "A2", ["verdict", "error"]] = ["errore", "funzione di varianza: ottimizzazione non valida"]
    r4 = [dict(r, **err, prod_state="errore", prod_err_class="varfun") if r["arm"] == "A2" else r for r in rows]
    ok("three-way same-class error -> errore_atteso", arm_of(compare_raw(r4, f4), "A2").outcome == "errore_atteso")
    r5 = [dict(r, **err, prod_state="valido", prod_err_class="") if r["arm"] == "A2" else r for r in rows]
    ok("ind err + raw err, producer valid -> unexpected", arm_of(compare_raw(r5, f4), "A2").outcome == "unexpected")
    r6 = [dict(r, **err, prod_state="errore", prod_err_class="cell") if r["arm"] == "A2" else r for r in rows]
    ok("producer error of other class -> unexpected", arm_of(compare_raw(r6, f4), "A2").outcome == "unexpected")
    r7 = [dict(r, prod_state="errore", prod_err_class="varfun") if r["arm"] == "A2" else r for r in rows]
    ok("producer error alone -> unexpected", arm_of(compare_raw(r7, fr), "A2").outcome == "unexpected")
    f8 = f4.copy(); f8.loc[f8.arm == "A2", "error"] = "altro"
    ok("raw error of other class -> unexpected", arm_of(compare_raw(r4, f8), "A2").outcome == "unexpected")
    r9 = [dict(r, **err, prod_state="errore", prod_err_class="varfun") if r["arm"] == "A3" else r for r in rows]
    f9 = fr.copy(); f9.loc[f9.arm == "A3", ["verdict", "error"]] = ["errore", "funzione di varianza: x"]
    ok("A3 error -> unexpected", arm_of(compare_raw(r9, f9), "A3").outcome == "unexpected")

    # final predicate and key sets on a one-catalogue fixture (Codex blocking 4)
    jobs1 = [("null", 7, 0.0, 0)]
    good, _, _ = evaluate(compare_raw(rows, fr), fr, jobs1, cc)
    ok("predicate: complete fixture passes", good)
    only_a3 = [r for r in rows if r["arm"] == "A3"]
    ok("predicate: missing arms fail", not evaluate(compare_raw(only_a3, fr), fr, jobs1, cc)[0])
    dup = rows + [rows[0]]
    ok("predicate: duplicated key fails", not evaluate(compare_raw(dup, fr), fr, jobs1, cc)[0])
    sub = [dict(r, arm="A2") if r["arm"] == "A2p" else r for r in rows]
    ok("predicate: substituted key fails", not evaluate(compare_raw(sub, fr), fr, jobs1, cc)[0])
    fr_extra = pd.concat([fr, fr[fr.arm == "A3"].assign(k=1)])
    ok("predicate: unexpected raw key fails", not evaluate(compare_raw(rows, fr_extra), fr_extra, jobs1, cc)[0])
    fr_noa0 = fr[fr.arm != "A0"]
    ok("predicate: missing A0 reference fails", not evaluate(compare_raw(rows, fr_noa0), fr_noa0, jobs1, cc)[0])
    jobs2 = jobs1 + [("null", 7, 0.0, 1)]
    ok("predicate: missing catalogue fails", not evaluate(compare_raw(rows, fr), fr, jobs2, cc)[0])
    bad_c = dict(cc, z_equal=False)
    ok("predicate: constant mismatch fails", not evaluate(compare_raw(rows, fr), fr, jobs1, bad_c)[0])

    # failure handling (Codex 5): total and partial failures summarized and counted
    allrow = [dict(kind="null", scenario=7, effect=0.0, k=0, arm="ALL", status="eccezione", err_class="exception", msg="boom")]
    try:
        p, d, s = evaluate(compare_raw(allrow, fr), fr, jobs1, cc)
        ok("total failure: summarized, counted, fails", (not p) and d["unexpected"] == 1 and int(s.unexpected.sum()) == 1)
    except Exception:
        ok("total failure: summarized, counted, fails", False)
    p, d, s = evaluate(compare_raw(rows[:1] + allrow, fr), fr, jobs1, cc)
    ok("partial failure: ALL counted in summary", (not p) and int(s.unexpected.sum()) == 1)

    for n, c in res:
        print(("PASS " if c else "FAIL ") + n)
    n_ok = sum(c for _, c in res)
    print(f"{n_ok}/{len(res)} passed")
    return n_ok == len(res)


# ---------------------------------------------------------------- run (note §7.3; C1 §5)

def run(workers, out_dir):
    from multiprocessing import Pool
    import traceback
    if git("status", "--porcelain", "--untracked-files=no"):
        print("tracked tree not clean: refusing to run")
        return 2
    out_dir.mkdir(parents=True, exist_ok=False)     # never overwrite an attempt, failed or not
    meta = dict(note=str(NOTE.relative_to(ROOT)), sha256_note=sha(NOTE), clarification=str(NOTE_C1.relative_to(ROOT)),
                sha256_clarification=sha(NOTE_C1), sha256_script=sha(__file__), sha256_raw_before=sha(RAW),
                git_commit=git("rev-parse", "HEAD"), rtol=RTOL, atol_factor=ATOL_FACTOR, n_catalogues=len(JOBS),
                env=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                         scipy=__import__("scipy").__version__), outcome="non superato")
    code = 1
    try:
        rows = []
        with Pool(workers) as pool:
            for i, rr in enumerate(pool.imap(job, JOBS, chunksize=50), 1):
                rows.extend(rr)
                if i % 2000 == 0:
                    print(f"{i}/{len(JOBS)} cataloghi", flush=True)
        raw = pd.read_csv(RAW, keep_default_na=False, na_values=[""],
                          usecols=["kind", "scenario", "effect", "k", "arm", "beta", "beta_true", "se", "lo", "hi",
                                   "verdict", "covered", "below", "above", "error"])
        raw = raw[raw.arm.isin(["A0", "A2", "A3", "A2p"])]
        df = compare_raw(rows, raw)
        df.to_csv(out_dir / "ROWS.csv.gz", index=False)
        _init()
        cc = constants_check(_PHI_STAR)
        passed, details, s = evaluate(df, raw, JOBS, cc)
        s.to_csv(out_dir / "SUMMARY.csv", index=False)
        meta.update(constants=cc, **details)
        if passed and sha(RAW) == meta["sha256_raw_before"]:
            meta["outcome"], code = "superato", 0
    except Exception:
        meta["exception"] = traceback.format_exc()
    finally:
        meta["sha256_raw_after"] = sha(RAW)
        (out_dir / "META.json").write_text(json.dumps(meta, indent=2, default=str))
        print(json.dumps({k: meta.get(k) for k in ("outcome", "ok", "errore_atteso", "mismatch", "unexpected",
                                                   "beta_regeneration_check")}, default=str))
        print("fatto")
    return code


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.run:
        sys.exit(run(a.workers, Path(a.out)))
