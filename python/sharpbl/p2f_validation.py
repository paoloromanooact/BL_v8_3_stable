"""Validazione della procedura M (protocollo P2f, docs/PROTOCOL_P2F_VALIDATED_TEST.md, congelato in 500c56a).

Validazione, non applicazione: nessuna risposta reale letta, nessun verdetto sul quenching. Riusa dal pilota
(`p2f_pilot`, commit 67058f6) il disegno congelato, la funzione di varianza (A2) e la REML (A1); qui cambiano,
come fissato dal protocollo §1 e §3: residui e matrice degli effetti fissi del MODELLO COMPLETO, generatore T5
con la media semplice di attivita' della cella, dodici scenari, intervalli con conteggio delle code.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_validation.py --selftest   # test preliminari (§6.1)
    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_validation.py              # validazione (solo dopo i test)
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, p2f_pilot as P, run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_P2F_VALIDATED_TEST.md"
OUT = ROOT / "results/P2F"
ACT = "A_monthly"
ALPHA = p2d.ALPHA_SIDE                 # 0.0125 per verso
Z = float(norm.ppf(1 - ALPHA))         # precisione completa (2,241 e' solo la rappresentazione)
GAMMA0, SD_E, SD_X = P.GAMMA0, P.SD_E, P.SD_X
ETA_BAR = P.ETA_BAR
N_NULL, N_EFF = 10_000, 2000
EFFECTS = (-0.1, -0.2, -0.3, -0.35)
EFFECT_SCENARIOS = (1, 2, 7, 9)
CandidateError = P.CandidateError

SCENARIOS = {
    0: dict(kind="none"),
    1: dict(kind="ar1", phi=0.5, kappa=0.0),
    2: dict(kind="ar1", phi=0.9, kappa=0.0),
    3: dict(kind="ar1", phi=0.9, kappa=-0.8),
    4: dict(kind="ar1", phi=0.5, kappa=0.6),
    5: dict(kind="ar1", phi=0.8, kappa=0.0, hetero=True),
    6: dict(kind="ar2", phi1=0.5, phi2=0.3, kappa=0.0),
    7: dict(kind="steps", length=20, shared=False),
    8: dict(kind="ar1", phi=0.8, kappa=0.0, t4=True),
    9: dict(kind="ar1", phi=0.53, kappa=-0.85, hetero=True, t4=True, x_scale=2.0),
    10: dict(kind="steps", length=13, shared=True),
    11: dict(kind="ar2", phi1=0.5, phi2=0.3, kappa=-0.8),
}
PILOT_RANGES = [(3_000_000, 3_950_300), (4_000_000, 4_950_600), (5_000_000, 5_001_000)]


# ---------------------------------------------------------------- semi (protocollo §5)

def seed_null(s, k):
    return 6_000_000 + 100_000 * s + k


def j_index(s, e):
    return 4 * EFFECT_SCENARIOS.index(s) + EFFECTS.index(e)


def seed_effect(s, e, k):
    return 7_500_000 + 100_000 * j_index(s, e) + k


SEED_TEST = 20_000_000


def seeds_ok():
    seeds = [seed_null(s, k) for s in SCENARIOS for k in range(N_NULL)]
    seeds += [seed_effect(s, e, k) for s in EFFECT_SCENARIOS for e in EFFECTS for k in range(N_EFF)]
    seeds += [SEED_TEST + k for k in range(1000)]
    used = P.USED + PILOT_RANGES
    clash = any(lo <= x < hi for x in seeds for lo, hi in used)
    return (not clash) and len(set(seeds)) == len(seeds)


# ---------------------------------------------------------------- generatore (protocollo §3, §4)

def gen_x(spec, G, rng):
    """(G, 2) a varianza marginale 1."""
    kind = spec["kind"]
    if kind in ("none", "ar1"):
        return P.gen_x(spec, G, rng)
    if kind == "ar2":
        p1, p2, k = spec["phi1"], spec["phi2"], spec["kappa"]
        L = np.linalg.cholesky(np.array([[1.0, k], [k, 1.0]]))
        z = np.zeros((G + 200, 2))
        for t in range(2, G + 200):
            z[t] = p1 * z[t - 1] + p2 * z[t - 2] + L @ rng.standard_normal(2)
        return z[200:] / np.sqrt(P.ar2_stationary_var(p1, p2))
    if kind == "steps":
        Lb = spec["length"]
        phase = int(rng.integers(0, Lb))
        blk = (np.arange(G) + phase) // Lb
        nb = blk.max() + 1
        if spec["shared"]:
            lev = np.repeat(rng.choice([-1.0, 1.0], size=(nb, 1)), 2, axis=1)
        else:
            lev = rng.choice([-1.0, 1.0], size=(nb, 2))
        return lev[blk]
    raise ValueError(spec)


def cell_mean_activity(design):
    """A-bar della cella (CR, emisfero): media semplice di A sulle regioni della cella (come run_p2.cells)."""
    return design.groupby(["CR", "hemisphere"])[ACT].transform("mean").to_numpy()


def responses(design, s, rng, beta_frac=0.0, noise=True):
    spec = SCENARIOS[s]
    d = design
    lo, hi = int(d["CR"].min()), int(d["CR"].max())
    G = hi - lo + 1
    ti = d["CR"].astype(int).to_numpy() - lo
    hi_ = (d["hemisphere"] == "S").to_numpy().astype(int)
    n = len(d)
    if noise:
        x3 = gen_x(spec, G, rng)[ti, hi_]
        x5 = gen_x(spec, G, rng)[ti, hi_]
        if spec.get("t4"):
            e3 = rng.standard_t(4, n) / np.sqrt(2.0)
            e5 = rng.standard_t(4, n) / np.sqrt(2.0)
        else:
            e3 = rng.standard_normal(n)
            e5 = rng.standard_normal(n)
    else:
        x3 = x5 = e3 = e5 = np.zeros(n)
    phi = d["phi"].to_numpy()
    c = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else np.ones(n)
    xs = spec.get("x_scale", 1.0)
    s_ = d["sinlat"].to_numpy()
    a = d[ACT].to_numpy() - 1.0
    abar = cell_mean_activity(d) - 1.0
    gamma = (GAMMA0 + beta_frac * GAMMA0 * a) * s_ + SD_E * c * e3 + xs * SD_X * x3
    dstar = phi * ETA_BAR * (1.0 + beta_frac * abar + c * e5 + xs * 0.5 * x5)
    out = d.copy()
    out["gamma"] = gamma
    out["d_star"] = dstar
    return out


def beta_true(test, beta_frac):
    return beta_frac * (GAMMA0 if test == "T3" else ETA_BAR)


# ---------------------------------------------------------------- procedura M (protocollo §1): modello completo

def units(dd, test):
    if test == "T3":
        dz = p2d.design_t3(dd)
        y, w, Xf = dz["y"], dz["w"], dz["Xf"]
        a = P.wls(Xf, w, y)                       # stima WLS completa (cond check)
        row = p2d.wls_row(Xf, w)
        beta = float(row @ y)
        r = y - Xf @ a                            # residui del modello completo
        codes, uniq = P.cell_keys(dz["cr"].astype(int), dz["hem"])
        return dict(test=test, y=y, w=w, Xf=Xf, a_row=row, beta=beta, r=r, codes=codes, uniq=uniq, phi=w,
                    n_check=(len(y), len(uniq)))
    dz = p2d.design_t5(dd)
    k = dz["k_of_i"]
    W_c, Xf_c = dz["W_c"], dz["Xf_c"]
    eta_c = np.bincount(k, weights=dz["agg"] * dz["z"], minlength=len(W_c))
    bf = P.wls(Xf_c, W_c, eta_c)
    g = p2d.wls_row(Xf_c, W_c)
    beta = float(g @ eta_c)
    r = dz["z"] - (Xf_c @ bf)[k]                  # residui del modello completo riportati alle regioni
    cell_cr = pd.Series(dz["cr"]).groupby(k).first().sort_index().to_numpy().astype(int)
    return dict(test=test, y=dz["z"], w=dz["phi"], k_of_i=k, agg=dz["agg"], Xf_c=Xf_c, W_c=W_c, g=g, beta=beta, r=r,
                codes=k, cell_cr=cell_cr, cell_hem=dz["cell_hem"], eta_c=eta_c, phi=dz["phi"],
                n_check=(len(W_c), len(dz["z"])))


def cell_residuals(u):
    w, r, codes = u["w"], u["r"], u["codes"]
    W = np.bincount(codes, weights=w)
    e = r - (np.bincount(codes, weights=w * r) / W)[codes]
    h = w / W[codes]
    return e, h


def cell_level(u, sig2):
    """Risposte medie di cella, X completa aggregata, v, b, t, h, parte individuale di Var(beta)."""
    if u["test"] == "T3":
        codes, uniq, w = u["codes"], u["uniq"], u["w"]
        W = np.bincount(codes, weights=w)
        yc = np.bincount(codes, weights=w * u["y"]) / W
        Xc = np.column_stack([np.bincount(codes, weights=w * u["Xf"][:, j]) / W for j in range(u["Xf"].shape[1])])
        vc = np.bincount(codes, weights=w ** 2 * sig2) / W ** 2
        b = np.bincount(codes, weights=u["a_row"])
        cr = np.array([c for c, _ in uniq])
        hm = np.array([hh for _, hh in uniq])
        ind = float(np.sum(u["a_row"] ** 2 * sig2))
    else:
        k = u["k_of_i"]
        yc, Xc = u["eta_c"], u["Xf_c"]
        vc = np.bincount(k, weights=u["agg"] ** 2 * sig2, minlength=len(u["W_c"]))
        b = u["g"].copy()
        cr, hm = u["cell_cr"], u["cell_hem"]
        ind = float(np.sum(u["g"] ** 2 * vc))
    return yc, Xc, vc, b, cr - cr.min(), (hm == "S").astype(int), ind


def procedure_m(u):
    if not np.isfinite(u["beta"]):
        raise CandidateError("beta non finito")
    e, h = cell_residuals(u)
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    ab, n_fit, n_zero = P.varfun_fit(e, h, u["codes"], logphi - m)
    sig2 = np.exp(ab[0] + ab[1] * (logphi - m))
    if not np.isfinite(sig2).all():
        raise CandidateError("varianza individuale non finita")
    yc, Xc, vc, b, t, hh, ind = cell_level(u, sig2)
    if not (np.isfinite(vc).all() and (vc > 0).all()):
        raise CandidateError("varianze di cella non finite o nulle")
    fit = P.reml_fit(yc, Xc, vc, t, hh)
    var = fit["sigma_x2"] * float(b @ P.ar1_k(t, hh, fit["phi"], fit["kappa"]) @ b) + ind
    if not (np.isfinite(var) and var > 0):
        raise CandidateError("varianza di beta non finita o non positiva")
    se = float(np.sqrt(var))
    lo, hi = u["beta"] - Z * se, u["beta"] + Z * se
    if not (np.isfinite(lo) and np.isfinite(hi)):
        raise CandidateError("intervallo non finito")
    verdict = "supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso")
    return dict(beta=u["beta"], se=se, stat=u["beta"] / se, lo=lo, hi=hi, verdict=verdict, var_a=float(ab[0]),
                var_b=float(ab[1]), n_varfun=n_fit, n_zero_residuals=n_zero, **fit)


def m_variance_given(u, sig2, phi, kappa, sigma_x2):
    yc, Xc, vc, b, t, hh, ind = cell_level(u, sig2)
    return sigma_x2 * float(b @ P.ar1_k(t, hh, phi, kappa) @ b) + ind


# ---------------------------------------------------------------- un catalogo

EXPECTED = {"T3": (2485, 394), "T5": (318, 2375)}


def run_catalogue(design, s, seed, beta_frac=0.0):
    dd = responses(design, s, np.random.default_rng(seed), beta_frac)
    rows = []
    for test in ("T3", "T5"):
        u = units(dd, test)
        assert u["n_check"] == EXPECTED[test], f"disegno non congelato: {test} {u['n_check']}"
        bt = beta_true(test, beta_frac)
        row = dict(test=test, beta_true=bt)
        try:
            r = procedure_m(u)
            row.update(r, covered=int(r["lo"] <= bt <= r["hi"]), below=int(r["lo"] > bt), above=int(r["hi"] < bt))
        except CandidateError as exc:
            row.update(verdict="errore", error=str(exc), covered=0, below=0, above=0)
        rows.append(row)
    return rows


_DESIGN = None


def _design():
    global _DESIGN
    if _DESIGN is None:
        _DESIGN = pd.read_pickle(OUT / "_design.pkl")
    return _DESIGN


def job(args):
    kind, s, e, k = args
    if kind == "null":
        rows = run_catalogue(_design(), s, seed_null(s, k))
        frac = 0.0
    else:
        frac = EFFECTS[e]
        rows = run_catalogue(_design(), s, seed_effect(s, frac, k), beta_frac=frac)
    for r in rows:
        r.update(kind=kind, scenario=s, effect=frac, k=k)
    return rows


# ---------------------------------------------------------------- test preliminari (protocollo §6.1)

def _t1_series(k):
    rng = np.random.default_rng(SEED_TEST + k)
    G = 400
    x = P.gen_x(dict(kind="ar1", phi=0.8, kappa=0.5), G, rng)
    t = np.repeat(np.arange(G), 2)
    h = np.tile([0, 1], G)
    y = x.ravel() + np.where(h == 0, 1.0, -0.5) + rng.normal(0, 0.5, 2 * G)
    keep = rng.random(2 * G) >= 0.15
    X = np.column_stack([(h == 0), (h == 1)]).astype(float)[keep]
    try:
        f = P.reml_fit(y[keep], X, np.full(keep.sum(), 0.25), t[keep], h[keep])
        return dict(k=k, ok=1, **f)
    except CandidateError:
        return dict(k=k, ok=0)


def _t2_rep(args):
    k, base = args
    rng = np.random.default_rng(base + k)
    dd = _design().copy()
    phi = dd["phi"].to_numpy()
    c = (phi / np.median(phi)) ** -0.25
    dd["gamma"] = 15.0 * c * rng.standard_normal(len(dd))
    dd["d_star"] = phi * ETA_BAR               # non usato dal test 2 (solo T3), ma richiesto dal disegno
    u = units(dd, "T3")
    e, h = cell_residuals(u)
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    ab, _, _ = P.varfun_fit(e, h, u["codes"], logphi - m)
    a_true = np.log(225.0) - 0.5 * (m - np.log(np.median(phi)))
    return dict(group="2a" if base == SEED_TEST + 200 else "2b", k=k, seed=base + k, a_hat=ab[0], b_hat=ab[1],
                a_true=a_true, b_true=-0.5)


def selftest(workers):
    from multiprocessing import Pool
    OUT.mkdir(parents=True, exist_ok=True)
    design = P.build_design()                 # test 5: asserzione sulle colonne di risposta
    design.to_pickle(OUT / "_design.pkl")
    rows = [dict(test="5_no_real_responses", value=0, condition="nessuna colonna di risposta", passed=True)]
    with Pool(workers) as pool:
        t1 = pd.DataFrame(pool.map(_t1_series, range(200)))
        t2 = pd.DataFrame(pool.map(_t2_rep, [(k, base) for base in (SEED_TEST + 200, SEED_TEST + 600) for k in range(200)]))
    v = t1[t1["ok"] == 1]
    rows += [
        dict(test="1_reml_valid_series", value=int(t1["ok"].sum()), condition=">= 198 su 200", passed=bool(t1["ok"].sum() >= 198)),
        dict(test="1_reml_mean_phi", value=float(v["phi"].mean()), condition="|media - 0,8| <= 0,02", passed=bool(abs(v["phi"].mean() - 0.8) <= 0.02)),
        dict(test="1_reml_mean_kappa", value=float(v["kappa"].mean()), condition="|media - 0,5| <= 0,05", passed=bool(abs(v["kappa"].mean() - 0.5) <= 0.05)),
        dict(test="1_reml_mean_sigma_x2", value=float(v["sigma_x2"].mean()), condition="|media - 1| <= 0,10", passed=bool(abs(v["sigma_x2"].mean() - 1.0) <= 0.10)),
    ]
    for grp, g in t2.groupby("group"):
        rows += [
            dict(test=f"{grp}_varfun_mean_b", value=float(g["b_hat"].mean()), condition="|media + 0,5| <= 0,05", passed=bool(abs(g["b_hat"].mean() + 0.5) <= 0.05)),
            dict(test=f"{grp}_varfun_mean_a_minus_true", value=float((g["a_hat"] - g["a_true"]).mean()),
                 condition="|media(a_hat) - a| <= 0,05", passed=bool(abs((g["a_hat"] - g["a_true"]).mean()) <= 0.05)),
        ]
    # 4: Var(beta) di M con parametri veri contro V_true di A (V1, k = 0, seme 40000)
    sil = run_p2.load_silso()
    cat = p2d.synthetic_catalog_p2d("V1", 40000, 0.0, 0.0)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], sil)
    a_ref = pd.read_csv(ROOT / "results/DIAGNOSTIC/A_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "test", "v_true"])
    for test, s2, sx2 in (("T3", 15.0 ** 2, 7.5 ** 2), ("T5", (2.0e-24) ** 2, (0.5 * 2.0e-24) ** 2)):
        u = units(d, test)
        var = m_variance_given(u, np.full(len(u["y"]), s2), 0.5, 0.0, sx2)
        ref = float(a_ref[(a_ref["scenario"] == "V1") & (a_ref["k"] == 0) & (a_ref["test"] == test)]["v_true"].iloc[0])
        rel = abs(var / ref - 1)
        rows.append(dict(test=f"4_M_variance_vs_A_{test}", value=rel, condition="scarto relativo <= 1e-9", passed=bool(rel <= 1e-9)))
    # 6: prova deterministica senza rumore: la stima WLS restituisce il coefficiente iniettato (-0,2 della scala)
    dd = responses(design, 0, np.random.default_rng(SEED_TEST + 900), beta_frac=-0.2, noise=False)
    for test in ("T3", "T5"):
        u = units(dd, test)
        rel = abs(u["beta"] / beta_true(test, -0.2) - 1)
        rows.append(dict(test=f"6_deterministic_recovery_{test}", value=rel, condition="scarto relativo <= 1e-9", passed=bool(rel <= 1e-9)))
    # disegno congelato
    dd = responses(design, 0, np.random.default_rng(SEED_TEST + 901))
    for test in ("T3", "T5"):
        nc = units(dd, test)["n_check"]
        rows.append(dict(test=f"design_counts_{test}", value=f"{nc[0]}/{nc[1]}", condition=f"{EXPECTED[test][0]}/{EXPECTED[test][1]}", passed=nc == EXPECTED[test]))
    rows.append(dict(test="seeds_not_overlapping", value=0, condition="nessuna sovrapposizione", passed=seeds_ok()))
    res = pd.DataFrame(rows)
    st = provenance()
    res.assign(**st).to_csv(OUT / "PRELIM_TESTS.csv", index=False)
    t1.assign(**st).to_csv(OUT / "PRELIM_T1_REML.csv", index=False)
    t2.assign(**st).to_csv(OUT / "PRELIM_T2_VARFUN.csv", index=False)
    print(res.to_string(index=False))
    return 0 if res["passed"].all() else 2


# ---------------------------------------------------------------- validazione

def provenance():
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_PROTOCOL_P2F"] = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    for pl in P.PLANS:
        st[f"sha256_{pl.stem}"] = hashlib.sha256(pl.read_bytes()).hexdigest()
    st["status"] = "validazione della procedura M, nessun verdetto sul quenching"
    return st


def summarize(raw):
    rows = []
    for (test, s), g in raw[raw["kind"] == "null"].groupby(["test", "scenario"]):
        n = len(g)
        sup, opp, err = [int((g["verdict"] == v).sum()) for v in ("supportato", "opposto", "errore")]
        rows.append(dict(test=test, scenario=s, n=n, false=sup + opp, false_frac=(sup + opp) / n, supported=sup,
                         supported_frac=sup / n, opposite=opp, opposite_frac=opp / n, errors=err, error_frac=err / n,
                         scenario_ok=bool((sup + opp) / n <= 0.03 and sup / n <= 0.0175 and opp / n <= 0.0175 and err / n <= 0.01)))
    fv = pd.DataFrame(rows)
    rows = []
    for (test, s, e), g in raw[raw["kind"] == "effect"].groupby(["test", "scenario", "effect"]):
        n = len(g)
        err = int((g["verdict"] == "errore").sum())
        cov, below, above = int(g["covered"].sum()), int(g["below"].sum()), int(g["above"].sum())
        rows.append(dict(test=test, scenario=s, effect=e, n=n, covered=cov, coverage=cov / n,
                         coverage_mc_se=float(np.sqrt(cov / n * (1 - cov / n) / n)), below=below, below_frac=below / n,
                         above=above, above_frac=above / n, errors=err, power=float((g["verdict"] == "supportato").mean()),
                         combo_ok=bool(cov / n >= 0.965 and below / n <= 0.02)))
    cp = pd.DataFrame(rows)
    dec = []
    for test in ("T3", "T5"):
        f = fv[fv["test"] == test]
        c = cp[cp["test"] == test]
        ok = bool(len(f) == 12 and f["scenario_ok"].all() and len(c) == 16 and c["combo_ok"].all())
        dec.append(dict(test=test, n_null_scenarios=len(f), null_ok=bool(f["scenario_ok"].all()), n_effect_combos=len(c),
                        effect_ok=bool(c["combo_ok"].all()), validated=ok))
    return fv, cp, pd.DataFrame(dec)


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    if args.selftest:
        return selftest(args.workers)
    st = provenance()
    pre = OUT / "PRELIM_TESTS.csv"
    if not pre.exists():
        print("test preliminari assenti: eseguire --selftest (protocollo §6.1)")
        return 2
    pt = pd.read_csv(pre)
    if not pt["passed"].all() or pt["git_commit"].iloc[0] != st["git_commit"] or int(pt["git_dirty"].iloc[0]) or st["git_dirty"]:
        print("test preliminari non superati, eseguiti su un altro commit o albero non pulito: la validazione non parte")
        return 2
    design = P.build_design()
    design.to_pickle(OUT / "_design.pkl")
    jobs = [("null", s, 0, k) for s in SCENARIOS for k in range(N_NULL)]
    jobs += [("effect", s, e, k) for s in EFFECT_SCENARIOS for e in range(len(EFFECTS)) for k in range(N_EFF)]
    out = []
    with Pool(args.workers) as pool:
        for i, part in enumerate(pool.imap_unordered(job, jobs, chunksize=4), 1):
            out += part
            if i % 2500 == 0:
                print(f"{i}/{len(jobs)} cataloghi", flush=True)
    raw = pd.DataFrame(out).sort_values(["kind", "scenario", "effect", "k", "test"]).reset_index(drop=True)
    raw.assign(**st).to_csv(OUT / "VALIDATION_RAW.csv.gz", index=False)
    fv, cp, dec = summarize(raw)
    fv.assign(**st).to_csv(OUT / "VALIDATION_FALSE_VERDICTS.csv", index=False)
    cp.assign(**st).to_csv(OUT / "VALIDATION_COVERAGE_POWER.csv", index=False)
    dec.assign(**st).to_csv(OUT / "VALIDATION_DECISION.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(fv.round(4).to_string(index=False))
        print(cp.round(4).to_string(index=False))
        print(dec.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
