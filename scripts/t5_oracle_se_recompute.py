"""Independent recompute of the T5-D2 oracle SEs for A2, A3 and A2p (docs/T5_ORACLE_SE_RECOMPUTE_NOTE.md,
frozen in 61f8884 before this code was written).

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


def ratio(x, y, scale):
    """|x - y| / (atol + rtol |y|); <= 1 passes (note §4). Vectors: maxima over components."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.shape != y.shape:
        return np.inf
    return float(np.max(np.abs(x - y)) / (ATOL_FACTOR * scale + RTOL * np.max(np.abs(y))))


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
        out["A2"] = dict(v=vce, ind=ind_e, bKb=float(be @ Kt @ be), var=D.SX2_TRUE * float(be @ Kt @ be) + ind_e)
        if scen in D.PHI_STAR:
            Ka = P.ar1_k(te, he, D.PHI_STAR[scen], D.KAPPA_STAR[scen])
            out["A2p"] = dict(v=vce, ind=ind_e, bKb=float(be @ Ka @ be), var=D.SX2_TRUE * float(be @ Ka @ be) + ind_e)
    except V.CandidateError as exc:
        out["A2"] = dict(err=str(exc))
        if scen in D.PHI_STAR:
            out["A2p"] = dict(err=str(exc))
    return out


def compare_components(b, ind_out, prod):
    """Worst tolerance ratio over the components of each arm (b, v, ind, bKb, var)."""
    res = {}
    bscale = float(np.max(np.abs(prod["b"])))
    rb = ratio(b, prod["b"], bscale)
    for arm, r in ind_out.items():
        p = prod.get(arm, {})
        if "err" in r or "err" in p:
            res[arm] = dict(comp_ratio=np.nan, comp_state=f"ind:{'err' if 'err' in r else 'ok'} prod:{'err' if 'err' in p else 'ok'}")
            continue
        rs = [rb, ratio(r["v"], p["v"], ETA0 ** 2), ratio(r["ind"], p["ind"], ETA0 ** 2),
              ratio(r["bKb"], p["bKb"], bscale ** 2), ratio(r["var"], p["var"], ETA0 ** 2),
              ratio(SX2 * r["bKb"], SX2 * p["bKb"], ETA0 ** 2)]
        res[arm] = dict(comp_ratio=max(rs), comp_state="ok")
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
        return [dict(kind=kind, scenario=s, effect=e, k=k, arm="ALL", status="unexpected", err_class="exception",
                     msg=repr(exc))]
    for arm, r in out.items():
        row = dict(kind=kind, scenario=s, effect=e, k=k, arm=arm, beta=beta, beta_true=bt)
        if "err" in r:
            row.update(status="errore", err_class=r["err"], msg=r["msg"])
        else:
            row.update(status="valido", se=r["se"], lo=r["lo"], hi=r["hi"], verdict=r["verdict"],
                       covered=r["covered"], below=r["below"], above=r["above"], var=r["var"])
        row.update(comp[arm])
        rows.append(row)
    return rows


# ---------------------------------------------------------------- comparison with ORACLE_RAW (note §4a, §5, §6)

def raw_class(msg):
    m = str(msg)
    if "funzione di varianza" in m or "varianza individuale" in m:
        return "varfun"
    if "varianze di cella" in m:
        return "cell"
    return "other"


def compare_raw(rows, raw):
    key = ["kind", "scenario", "effect", "k", "arm"]
    r = raw.set_index(key)
    a0 = raw[raw.arm == "A0"].set_index(["kind", "scenario", "effect", "k"])["beta"]
    out = []
    for x in rows:
        x = dict(x)
        if x["arm"] == "ALL":
            x.update(outcome="unexpected")
            out.append(x)
            continue
        ref = r.loc[(x["kind"], x["scenario"], x["effect"], x["k"], x["arm"])]
        b0 = a0.get((x["kind"], x["scenario"], x["effect"], x["k"]))
        x["beta_ratio_A0"] = ratio(x["beta"], b0, ETA0) if b0 is not None and np.isfinite(b0) else np.nan
        ref_err = ref["verdict"] == "errore"
        if x["status"] == "errore" and ref_err:
            same_cls = raw_class(ref["error"]) == x["err_class"]
            x.update(outcome="errore_atteso" if same_cls else "unexpected", raw_err_class=raw_class(ref["error"]))
        elif x["status"] == "errore" or ref_err:
            x.update(outcome="unexpected")
        else:
            rr = max(ratio(x["beta"], ref["beta"], ETA0), ratio(x["se"], ref["se"], ETA0),
                     ratio(x["lo"], ref["lo"], ETA0), ratio(x["hi"], ref["hi"], ETA0))
            same_flags = (x["verdict"] == ref["verdict"] and x["covered"] == int(ref["covered"])
                          and x["below"] == int(ref["below"]) and x["above"] == int(ref["above"]))
            bt_ok = ratio(x["beta_true"], ref["beta_true"], ETA0) <= 1
            x["raw_ratio"] = rr
            x["se_raw"] = ref["se"]
            ok = rr <= 1 and same_flags and bt_ok and x["comp_ratio"] <= 1
            x.update(outcome="ok" if ok else "mismatch", flags_equal=same_flags)
        if x["arm"] == "A3" and x["status"] == "errore":
            x["outcome"] = "unexpected"
        out.append(x)
    return pd.DataFrame(out)


def summarize(df):
    g = df[df.arm != "ALL"].groupby(["kind", "scenario", "effect", "arm"], dropna=False)
    s = g.agg(n=("k", "size"), ok=("outcome", lambda o: int((o == "ok").sum())),
              errore_atteso=("outcome", lambda o: int((o == "errore_atteso").sum())),
              mismatch=("outcome", lambda o: int((o == "mismatch").sum())),
              unexpected=("outcome", lambda o: int((o == "unexpected").sum())),
              max_raw_ratio=("raw_ratio", "max"), max_comp_ratio=("comp_ratio", "max"),
              max_beta_ratio_A0=("beta_ratio_A0", "max")).reset_index()
    valid = df[(df.arm != "ALL") & (df.status == "valido") & df.se_raw.notna()]
    d = (valid.se - valid.se_raw).abs()
    s = s.merge(valid.assign(abs_se=d, rel_se=d / valid.se_raw.abs()).groupby(
        ["kind", "scenario", "effect", "arm"], dropna=False).agg(max_abs_se=("abs_se", "max"), max_rel_se=("rel_se", "max")).reset_index(),
        how="left", on=["kind", "scenario", "effect", "arm"])
    return s


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


# ---------------------------------------------------------------- selftest (note §7.2): no run catalogue

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
    # tolerance rule, including deliberate alterations
    ok("tol pass 1e-12 rel", ratio(ETA0 * (1 + 1e-12), ETA0, ETA0) <= 1)
    ok("tol catches 1e-6 rel", ratio(ETA0 * (1 + 1e-6), ETA0, ETA0) > 1)
    ok("tol near zero uses atol", ratio(1e-40, 0.0, ETA0) <= 1 and ratio(1e-30, 0.0, ETA0) > 1)
    ok("vector alteration caught", ratio(np.array([1.0, 2.0 * (1 + 1e-6)]), np.array([1.0, 2.0]), 2.0) > 1)
    # catalogues with seeds outside every run: independent vs producer components only (no raw read)
    _init()
    specs = [("null", 7, 0.0, 0), ("effect", 7, -0.3, 1), ("null", 10, 0.0, 2), ("null", 1, 0.0, 3), ("null", 2, 0.0, 4)]
    for j, sp in enumerate(specs):
        rows = job(sp, seed=SELFTEST_SEED + j)
        bad = [r for r in rows if r.get("status") == "unexpected" or (r.get("comp_state") == "ok" and not r["comp_ratio"] <= 1)]
        ok(f"components agree, selftest catalogue {sp[0]} {sp[1]} {sp[2]}", not bad and len(rows) == (3 if sp[1] in STEP_L else 2))
    # a deliberately altered producer value is caught by the component comparison
    u = regen("null", 7, 0.0, 0, seed=SELFTEST_SEED)
    beta, bb, out = independent(u, 7, 0.0, _PHI_STAR)
    prod = producer(u, 7)
    prod["A3"]["var"] *= 1 + 1e-7
    ok("altered producer variance caught", compare_components(bb, out, prod)["A3"]["comp_ratio"] > 1)
    ok("constants", all(v for k, v in constants_check(_PHI_STAR).items() if k != "phi_star"))
    # classification against a fake raw built from a selftest catalogue (not ORACLE_RAW)
    rows = job(("null", 7, 0.0, 0), seed=SELFTEST_SEED)
    fake = []
    for r in rows:
        fake.append(dict(kind=r["kind"], scenario=r["scenario"], effect=r["effect"], k=r["k"], arm=r["arm"],
                         beta=r["beta"], beta_true=r["beta_true"], se=r["se"], lo=r["lo"], hi=r["hi"],
                         verdict=r["verdict"], covered=r["covered"], below=r["below"], above=r["above"], error=""))
    fake.append(dict(fake[0], arm="A0"))
    fr = pd.DataFrame(fake)
    ok("fake raw: all ok", set(compare_raw(rows, fr).outcome) == {"ok"})
    f2 = fr.copy(); f2.loc[f2.arm == "A2", "se"] *= 1 + 1e-6
    ok("fake raw: altered SE -> mismatch", compare_raw(rows, f2).set_index("arm").loc["A2", "outcome"] == "mismatch")
    f3 = fr.copy(); f3.loc[f3.arm == "A2p", "verdict"] = "errore"
    ok("fake raw: error vs value -> unexpected", compare_raw(rows, f3).set_index("arm").loc["A2p", "outcome"] == "unexpected")
    r4 = [dict(r, status="errore", err_class="varfun", msg="x") if r["arm"] == "A2" else r for r in rows]
    f4 = fr.copy(); f4.loc[f4.arm == "A2", ["verdict", "error"]] = ["errore", "funzione di varianza: ottimizzazione non valida"]
    ok("fake raw: same-class error -> errore_atteso", compare_raw(r4, f4).set_index("arm").loc["A2", "outcome"] == "errore_atteso")
    f5 = f4.copy(); f5.loc[f5.arm == "A2", "error"] = "altro"
    ok("fake raw: other-class error -> unexpected", compare_raw(r4, f5).set_index("arm").loc["A2", "outcome"] == "unexpected")
    for n, c in res:
        print(("PASS " if c else "FAIL ") + n)
    n_ok = sum(c for _, c in res)
    print(f"{n_ok}/{len(res)} passed")
    return n_ok == len(res)


# ---------------------------------------------------------------- run (note §7.3)

def run(workers):
    from multiprocessing import Pool
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("tracked tree not clean: refusing to run")
    OUT.mkdir(parents=True, exist_ok=False)
    raw_sha_before = sha(RAW)
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
    df.to_csv(OUT / "ROWS.csv.gz", index=False)
    s = summarize(df)
    s.to_csv(OUT / "SUMMARY.csv", index=False)
    _init()
    cc = constants_check(_PHI_STAR)
    beta_all = bool((df.drop_duplicates(["kind", "scenario", "effect", "k"]).beta_ratio_A0 <= 1).all())
    passed = (beta_all and int(s.mismatch.sum()) == 0 and int(s.unexpected.sum()) == 0
              and int((df.arm == "ALL").sum()) == 0 and all(v for k, v in cc.items() if k != "phi_star")
              and len(df.drop_duplicates(["kind", "scenario", "effect", "k"])) == len(JOBS))
    meta = dict(note=str(NOTE.relative_to(ROOT)), sha256_note=sha(NOTE), sha256_script=sha(__file__),
                sha256_raw_before=raw_sha_before, sha256_raw_after=sha(RAW), git_commit=git("rev-parse", "HEAD"),
                constants=cc, rtol=RTOL, atol_factor=ATOL_FACTOR, n_catalogues=len(JOBS), n_rows=int(len(df)),
                beta_regenerated_all=beta_all, mismatch=int(s.mismatch.sum()), unexpected=int(s.unexpected.sum()),
                errore_atteso=int(s.errore_atteso.sum()), ok=int(s.ok.sum()),
                env=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                         scipy=__import__("scipy").__version__),
                outcome="superato" if passed and sha(RAW) == raw_sha_before else "non superato")
    (OUT / "META.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps({k: meta[k] for k in ("outcome", "ok", "errore_atteso", "mismatch", "unexpected", "beta_regenerated_all")}))
    print("fatto")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.run:
        run(a.workers)
