"""T5-D2: controlli oracolo sulla procedura M nello scenario a salti (docs/PROTOCOL_T5_ORACLE.md, congelato in f77d39b,
con l'emendamento A1 in docs/PROTOCOL_T5_ORACLE_A1.md, 2b334bb).

Diagnostica non cieca, solo cataloghi sintetici della validazione P2f (stessi semi, ricostruiti). Non cambia T5, M,
il protocollo P2f o i suoi output.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_t5_oracle.py --selftest   # controlli §6 (1-3), prima del run
    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_t5_oracle.py --run        # esecuzione unica (dopo il selftest)
    .venv/bin/python python/sharpbl/diag_t5_oracle.py --check                         # controllo indipendente degli output
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2f_pilot as P, p2f_validation as V  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_T5_ORACLE.md"
AMEND = ROOT / "docs/PROTOCOL_T5_ORACLE_A1.md"
RAW_P2F = ROOT / "results/P2F/VALIDATION_RAW.csv.gz"
OUT = ROOT / "results/T5_ORACLE"
ETA0 = V.ETA_BAR
SX2_TRUE = (0.5 * ETA0) ** 2
SIG2_TRUE = ETA0 ** 2
Z = V.Z
TAU_MAX = 218
JOBS_SPEC = ([("null", 7, 0.0, k) for k in range(10_000)]
             + [("effect", 7, e, k) for e in (-0.1, -0.2, -0.3, -0.35) for k in range(2000)]
             + [("null", 10, 0.0, k) for k in range(10_000)]
             + [("null", s, 0.0, k) for s in (1, 2) for k in range(2000)])
ARMS = ("A0", "A1a", "A1b", "A2", "A3", "A2p")


# ---------------------------------------------------------------- covarianze vere e approssimazione AR(1)

def k_steps(lag, L):
    return np.maximum(0.0, 1.0 - np.abs(lag) / L)


def k_true(t, h, scen):
    lag = np.abs(t[:, None] - t[None, :])
    same = h[:, None] == h[None, :]
    if scen == 7:
        return k_steps(lag, 20) * same
    if scen == 10:
        return k_steps(lag, 13) * np.ones_like(same, float)
    spec = V.SCENARIOS[scen]
    return P.ar1_k(t, h, spec["phi"], spec["kappa"])


def best_ar1(L):
    tau = np.arange(TAU_MAX + 1)
    grid = np.round(np.arange(0, 0.98 + 1e-12, 1e-4), 4)
    sse = [(np.sum((g ** tau - k_steps(tau, L)) ** 2)) for g in grid]
    return float(grid[int(np.argmin(sse))])


PHI_STAR = {7: best_ar1(20), 10: best_ar1(13)}
KAPPA_STAR = {7: 0.0, 10: 0.98}


# ---------------------------------------------------------------- bracci

def interval(beta, var):
    if not (np.isfinite(var) and var > 0 and np.isfinite(beta)):
        return None
    se = float(np.sqrt(var))
    return dict(se=se, lo=beta - Z * se, hi=beta + Z * se)


def est_sig2(u):
    e, h = V.cell_residuals(u)
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    ab, _, _ = P.varfun_fit(e, h, u["codes"], logphi - m)
    s2 = np.exp(ab[0] + ab[1] * (logphi - m))
    if not np.isfinite(s2).all():
        raise V.CandidateError("varianza individuale non finita")
    return s2


def arms_for(u, scen):
    beta = u["beta"]
    res = {}
    s2_true = np.full(len(u["y"]), SIG2_TRUE)
    yc, Xc, vc, b, t, h, ind_true = V.cell_level(u, s2_true)
    Kt = k_true(t, h, scen)
    try:
        r0 = V.procedure_m(u)
        res["A0"] = dict(se=r0["se"], lo=r0["lo"], hi=r0["hi"])
        # A1a (emendamento A1): individuale vera, parametri temporali della REML di A0, non ristimati
        iv = interval(beta, r0["sigma_x2"] * float(b @ P.ar1_k(t, h, r0["phi"], r0["kappa"]) @ b) + ind_true)
        res["A1a"] = iv if iv else dict(error="varianza non finita o non positiva")
    except V.CandidateError as exc:
        res["A0"] = dict(error=str(exc))
        res["A1a"] = dict(error="A0 senza REML: " + str(exc))
    # A1b: individuale vera, REML AR(1) ristimata con v vera
    try:
        fit = P.reml_fit(yc, Xc, vc, t, h)
        iv = interval(beta, fit["sigma_x2"] * float(b @ P.ar1_k(t, h, fit["phi"], fit["kappa"]) @ b) + ind_true)
        res["A1b"] = iv if iv else dict(error="varianza non finita o non positiva")
    except V.CandidateError as exc:
        res["A1b"] = dict(error=str(exc))
    # A3: entrambe vere
    iv = interval(beta, SX2_TRUE * float(b @ Kt @ b) + ind_true)
    res["A3"] = iv if iv else dict(error="varianza non finita o non positiva")
    # A2, A2': individuale stimata
    try:
        s2e = est_sig2(u)
        _, _, vce, be, te, he, ind_est = V.cell_level(u, s2e)
        if not (np.isfinite(vce).all() and (vce > 0).all()):
            raise V.CandidateError("varianze di cella non finite o nulle")
        iv = interval(beta, SX2_TRUE * float(be @ Kt @ be) + ind_est)
        res["A2"] = iv if iv else dict(error="varianza non finita o non positiva")
        if scen in PHI_STAR:
            Ka = P.ar1_k(te, he, PHI_STAR[scen], KAPPA_STAR[scen])
            iv = interval(beta, SX2_TRUE * float(be @ Ka @ be) + ind_est)
            res["A2p"] = iv if iv else dict(error="varianza non finita o non positiva")
    except V.CandidateError as exc:
        res["A2"] = dict(error=str(exc))
        if scen in PHI_STAR:
            res["A2p"] = dict(error=str(exc))
    return beta, res


_DESIGN = None


def _design():
    global _DESIGN
    if _DESIGN is None:
        _DESIGN = pd.read_pickle(OUT / "_design.pkl")
    return _DESIGN


def job(spec):
    kind, s, e, k = spec
    seed = V.seed_null(s, k) if kind == "null" else V.seed_effect(s, e, k)
    dd = V.responses(_design(), s, np.random.default_rng(seed), e)
    u = V.units(dd, "T5")
    assert u["n_check"] == V.EXPECTED["T5"]
    beta, res = arms_for(u, s)
    bt = V.beta_true("T5", e)
    rows = []
    for arm, r in res.items():
        row = dict(kind=kind, scenario=s, effect=e, k=k, arm=arm, beta=beta, beta_true=bt)
        if "error" in r:
            row.update(verdict="errore", error=r["error"], covered=0, below=0, above=0)
        else:
            lo, hi = r["lo"], r["hi"]
            row.update(se=r["se"], lo=lo, hi=hi, verdict="supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso"),
                       covered=int(lo <= bt <= hi), below=int(lo > bt), above=int(hi < bt))
        rows.append(row)
    return rows


# ---------------------------------------------------------------- controlli preliminari (piano §6, punti 1-3)

def selftest():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []

    def add(name, value, ok):
        rows.append(dict(test=name, value=value, passed=bool(ok)))
    # 1. prove costruite a mano
    add("1a_k_steps_values", "", np.allclose(k_steps(np.array([0, 5, 19, 20, 30]), 20), [1, 0.75, 0.05, 0, 0]))
    t = np.arange(219); tt = np.repeat(t, 2); hh = np.tile([0, 1], 219)
    for sc in (7, 10, 1, 2):
        K = k_true(tt, hh, sc)
        ev = float(np.linalg.eigvalsh(K).min())
        add(f"1b_K_true_symmetric_psd_s{sc}", ev, np.allclose(K, K.T) and ev > -1e-9)
    add("1c_K7_cross_hemisphere_zero", "", float(np.abs(k_true(tt, hh, 7)[hh[:, None] != hh[None, :]]).max()) == 0.0)
    add("1d_phi_star", f"{PHI_STAR[7]} / {PHI_STAR[10]}", 0 < PHI_STAR[10] < PHI_STAR[7] < 0.98)
    # 2. covarianza empirica di gen_x contro K_steps (semi 28 000 000 + k)
    for sc, L in ((7, 20), (10, 13)):
        G, n = 221, 200_000
        acc = np.zeros((31, 2)); acc2 = np.zeros((31, 2))
        for k in range(n):
            x = V.gen_x(V.SCENARIOS[sc], G, np.random.default_rng(28_000_000 + (0 if sc == 7 else n) + k))
            for lag in range(31):
                same = float(np.mean(x[: G - lag, 0] * x[lag:, 0]))
                cross = float(np.mean(x[: G - lag, 0] * x[lag:, 1]))
                acc[lag] += (same, cross); acc2[lag] += (same ** 2, cross ** 2)
        m = acc / n; se = np.sqrt(np.maximum(acc2 / n - m ** 2, 0) / n)
        tgt_same = k_steps(np.arange(31), L); tgt_cross = tgt_same if sc == 10 else np.zeros(31)
        dz = np.max(np.abs(np.column_stack([m[:, 0] - tgt_same, m[:, 1] - tgt_cross])) / np.maximum(se, 1e-12))
        add(f"2_gen_x_covariance_s{sc}_max_abs_z", float(dz), dz < 5.0)
    # 3. riproduzione A0 su 50 cataloghi dello scenario 7 contro VALIDATION_RAW
    design = P.build_design(); design.to_pickle(OUT / "_design.pkl")
    raw = pd.read_csv(RAW_P2F, low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
    ref = raw[(raw["kind"] == "null") & (raw["scenario"] == 7) & (raw["test"] == "T5") & (raw["k"] < 50)].set_index("k")
    worst, verd_ok = 0.0, True
    for k in range(50):
        rr = [r for r in job(("null", 7, 0.0, k)) if r["arm"] == "A0"][0]
        g = ref.loc[k]
        if g["verdict"] == "errore" or rr["verdict"] == "errore":
            verd_ok &= g["verdict"] == rr["verdict"]
            continue
        worst = max(worst, abs(rr["beta"] / g["beta"] - 1), abs(rr["se"] / g["se"] - 1))
        verd_ok &= rr["verdict"] == g["verdict"]
    add("3_A0_reproduces_validation_50", worst, worst <= 1e-9 and verd_ok)
    res = pd.DataFrame(rows).assign(**provenance())
    res.to_csv(OUT / "PRELIM_TESTS.csv", index=False)
    print(res[["test", "value", "passed"]].to_string(index=False))
    return 0 if res["passed"].all() else 2


def provenance():
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_PROTOCOL_T5_ORACLE"] = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    st["sha256_PROTOCOL_T5_ORACLE_A1"] = hashlib.sha256(AMEND.read_bytes()).hexdigest()
    st["sha256_PROTOCOL_P2F"] = hashlib.sha256(V.PROTOCOL.read_bytes()).hexdigest()
    st["sha256_VALIDATION_RAW"] = hashlib.sha256(RAW_P2F.read_bytes()).hexdigest()
    st["status"] = "diagnostica T5-D2, non cieca, nessun verdetto"
    return st


# ---------------------------------------------------------------- sintesi

def summarize(raw):
    rows = []
    for (kind, s, e, arm), g in raw.groupby(["kind", "scenario", "effect", "arm"]):
        n = len(g); ok = g[g["verdict"] != "errore"]
        r = (ok["beta"] - ok["beta_true"]) / ETA0; sv = ok["se"] / ETA0
        z = r / sv
        row = dict(kind=kind, scenario=s, effect=e, arm=arm, n=n, errors=int(n - len(ok)),
                   R=float(np.mean(sv ** 2) / np.var(r, ddof=1)), sd_z=float(np.std(z, ddof=1)),
                   z_q0125=float(np.quantile(z, 0.0125)), z_q9875=float(np.quantile(z, 0.9875)))
        if kind == "null":
            f = int(g["verdict"].isin(["supportato", "opposto"]).sum())
            row.update(false=f, false_frac=f / n, false_mc_se=float(np.sqrt(f / n * (1 - f / n) / n)),
                       supported=int((g["verdict"] == "supportato").sum()), opposite=int((g["verdict"] == "opposto").sum()))
        cov = int(g["covered"].sum())
        row.update(covered=cov, coverage=cov / n, coverage_mc_se=float(np.sqrt(cov / n * (1 - cov / n) / n)),
                   below=int(g["below"].sum()), above=int(g["above"].sum()))
        rows.append(row)
    summ = pd.DataFrame(rows)
    a0 = raw[raw["arm"] == "A0"].set_index(["kind", "scenario", "effect", "k"])["verdict"]
    pr = []
    for arm in ARMS[1:]:
        x = raw[raw["arm"] == arm].set_index(["kind", "scenario", "effect", "k"])["verdict"]
        j = pd.concat([a0.rename("a0"), x.rename("arm")], axis=1, join="inner")
        for (kind, s, e), g in j.groupby(level=[0, 1, 2]):
            pr.append(dict(kind=kind, scenario=s, effect=e, arm=arm, n=len(g), same=int((g["a0"] == g["arm"]).sum()),
                           decided_in_A0_not_arm=int((g["a0"].isin(["supportato", "opposto"]) & (g["arm"] == "non deciso")).sum()),
                           decided_in_arm_not_A0=int((g["arm"].isin(["supportato", "opposto"]) & (g["a0"] == "non deciso")).sum())))
    return summ, pd.DataFrame(pr)


def run(workers):
    from multiprocessing import Pool
    st = provenance()
    pt = pd.read_csv(OUT / "PRELIM_TESTS.csv")
    if not pt["passed"].all() or pt["git_commit"].iloc[0] != st["git_commit"] or int(pt["git_dirty"].iloc[0]) or st["git_dirty"]:
        print("controlli preliminari non superati, su un altro commit o albero non pulito: non parte")
        return 2
    if (OUT / "ORACLE_RAW.csv.gz").exists():
        print("output già presenti: esecuzione unica, non si sovrascrive")
        return 2
    P.build_design().to_pickle(OUT / "_design.pkl")
    out = []
    with Pool(workers) as pool:
        for i, part in enumerate(pool.imap_unordered(job, JOBS_SPEC, chunksize=4), 1):
            out += part
            if i % 2000 == 0:
                print(f"{i}/{len(JOBS_SPEC)} cataloghi", flush=True)
    raw = pd.DataFrame(out).sort_values(["kind", "scenario", "effect", "k", "arm"]).reset_index(drop=True)
    raw.assign(**st).to_csv(OUT / "ORACLE_RAW.csv.gz", index=False)
    summ, pr = summarize(raw)
    summ.assign(**st).to_csv(OUT / "ORACLE_SUMMARY.csv", index=False)
    pr.assign(**st).to_csv(OUT / "ORACLE_PAIRED_VS_A0.csv", index=False)
    (OUT / "ORACLE_META.json").write_text(json.dumps(dict(phi_star=PHI_STAR, kappa_star=KAPPA_STAR, sx2_true=SX2_TRUE,
                                                          sig2_true=SIG2_TRUE, n_jobs=len(JOBS_SPEC), **st), indent=2))
    print("fatto")
    return 0


# ---------------------------------------------------------------- controllo indipendente (prima di leggere le sintesi)

def check():
    raw = pd.read_csv(OUT / "ORACLE_RAW.csv.gz", low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
    rows = []

    def add(name, value, ok):
        rows.append(dict(check=name, value=value, passed=bool(ok)))
    exp = {(k_, s, float(e), k, a) for (k_, s, e, k) in JOBS_SPEC for a in ARMS if a != "A2p" or s in (7, 10)}
    got = set(zip(raw["kind"], raw["scenario"].astype(int), raw["effect"].astype(float), raw["k"].astype(int), raw["arm"]))
    add("keys_equal_expected", f"mancanti {len(exp - got)}, inattese {len(got - exp)}", exp == got and not raw.duplicated(["kind", "scenario", "effect", "k", "arm"]).any())
    add("provenance_single_commit_clean", raw["git_commit"].iloc[0][:7], raw["git_commit"].nunique() == 1 and (raw["git_dirty"] == 0).all())
    add("protocol_sha_unchanged", raw["sha256_PROTOCOL_T5_ORACLE"].iloc[0][:8], (raw["sha256_PROTOCOL_T5_ORACLE"] == hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()).all())
    bstd = raw.groupby(["kind", "scenario", "effect", "k"])["beta"].nunique()
    add("beta_identical_across_arms", int((bstd > 1).sum()), (bstd == 1).all())
    ok = raw[raw["verdict"] != "errore"]
    add("A3_never_error", int((raw[raw["arm"] == "A3"]["verdict"] == "errore").sum()), (raw[raw["arm"] == "A3"]["verdict"] != "errore").all())
    fin = np.isfinite(ok[["beta", "se", "lo", "hi"]]).all(axis=1) & (ok["se"] > 0)
    add("finite_positive_se", int(fin.sum()), fin.all())
    d1 = np.abs((ok["beta"] - ok["lo"]) / ok["se"] - Z); d2 = np.abs((ok["hi"] - ok["beta"]) / ok["se"] - Z)
    add("half_widths_equal_z", float(max(d1.max(), d2.max())), max(d1.max(), d2.max()) <= 1e-9)
    vr = np.where(ok["hi"] < 0, "supportato", np.where(ok["lo"] > 0, "opposto", "non deciso"))
    add("verdicts_from_intervals", int((vr == ok["verdict"]).sum()), (vr == ok["verdict"]).all())
    ident = raw["covered"] + raw["below"] + raw["above"] + (raw["verdict"] == "errore").astype(int)
    add("tail_identity", int((ident == 1).sum()), (ident == 1).all())
    # A0 contro la validazione P2f, tutte le righe
    p2 = pd.read_csv(RAW_P2F, low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
    p2 = p2[(p2["test"] == "T5") & (p2["scenario"].isin([1, 2, 7, 10]))].copy()
    p2["kind"] = p2["kind"].astype(str)
    a0 = raw[raw["arm"] == "A0"].merge(p2, on=["kind", "scenario", "effect", "k"], suffixes=("", "_p2f"))
    add("A0_rows_matched_to_validation", len(a0), len(a0) == len(JOBS_SPEC))
    same_v = (a0["verdict"] == a0["verdict_p2f"]).all()
    m = a0["verdict"] != "errore"
    rel = float(np.max(np.abs(a0.loc[m, "se"] / a0.loc[m, "se_p2f"] - 1))) if m.any() else 0.0
    relb = float(np.max(np.abs(a0["beta"] / a0["beta_p2f"] - 1)))
    add("A0_reproduces_validation_all", f"se {rel:.1e}, beta {relb:.1e}", same_v and rel <= 1e-9 and relb <= 1e-9)
    # riconteggio indipendente dei falsi verdetti e della copertura, contro ORACLE_SUMMARY
    summ = pd.read_csv(OUT / "ORACLE_SUMMARY.csv")
    bad = 0
    for _, s in summ.iterrows():
        g = raw[(raw["kind"] == s["kind"]) & (raw["scenario"] == s["scenario"]) & np.isclose(raw["effect"], s["effect"]) & (raw["arm"] == s["arm"])]
        cov = int(g["covered"].sum())
        bad += int(cov != s["covered"] or len(g) != s["n"])
        if s["kind"] == "null":
            bad += int(int(g["verdict"].isin(["supportato", "opposto"]).sum()) != s["false"])
    add("summary_recount_equal", int(bad), bad == 0)
    res = pd.DataFrame(rows).assign(**provenance())
    for f in ("ORACLE_RAW.csv.gz", "ORACLE_SUMMARY.csv", "ORACLE_PAIRED_VS_A0.csv"):
        res[f"sha256_{f.split('.')[0]}"] = hashlib.sha256((OUT / f).read_bytes()).hexdigest()
    res.to_csv(OUT / "POST_CHECKS.csv", index=False)
    print(res[["check", "value", "passed"]].to_string(index=False))
    return 0 if res["passed"].all() else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.workers) if a.run else check() if a.check else 2)
