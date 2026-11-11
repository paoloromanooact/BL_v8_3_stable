"""Pilota di sviluppo per P2f: due procedure candidate (M e B) sul disegno reale congelato.

Piano: docs/P2F_PILOT_PLAN.md (83b0fc1) con l'emendamento docs/P2F_PILOT_PLAN_A1.md (59971e7),
registrati prima di questo codice. Sviluppo, non validazione: nessun verdetto, nessuna risposta
reale (gamma, D*) usata. Il disegno reale fornisce solo CR, emisfero, latitudine, Phi, attivita',
ciclo e celle.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_pilot.py --selftest   # test preliminari (A1 §6)
    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_pilot.py              # pilota (solo dopo i test)
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import LinAlgError, cho_factor, cho_solve, cholesky
from scipy.optimize import minimize
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLANS = (ROOT / "docs/P2F_PILOT_PLAN.md", ROOT / "docs/P2F_PILOT_PLAN_A1.md")
OUT = ROOT / "results/P2F_PILOT"
ACT = "A_monthly"
ALPHA = p2d.ALPHA_SIDE
Z = norm.ppf(1 - ALPHA)
GAMMA0, SD_E, SD_X = 24.0, 15.0, 7.5
ETA_BAR = 3.56e-25
BLOCK = 13
B_BOOT = 9999
WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
RESPONSE_COLS = ("sintilt", "d_axial_bal_g", "s_bl", "gamma", "d_star", "s_star", "leg_sintilt", "leg_s_bl",
                 "leg_d_axial_bal_g")
DESIGN_COLS = ["HARPNUM", "CR", "hemisphere", "lat", "sinlat", "phi", "cyc", ACT]
N_NULL, N_POWER = 1000, 300
EFFECTS = (-0.1, -0.2, -0.3)

SCENARIOS = {
    0: dict(kind="none"),
    1: dict(kind="ar1", phi=0.5, kappa=0.0),
    2: dict(kind="ar1", phi=0.9, kappa=0.0),
    3: dict(kind="ar1", phi=0.9, kappa=-0.8),
    4: dict(kind="ar1", phi=0.5, kappa=0.6),
    5: dict(kind="ar1", phi=0.8, kappa=0.0, hetero=True),
    6: dict(kind="ar2", phi1=0.5, phi2=0.3),
    7: dict(kind="steps", length=20),
    8: dict(kind="ar1", phi=0.8, kappa=0.0, t4=True),
}
USED = [(30000, 32000), (40000, 42000), (50000, 54000), (60000, 64002), (70000, 72000), (100000, 100500),
        (140000, 140500), (260000, 264002), (360000, 364002), (1_000_000, 1_410_000), (1_900_000, 1_950_000),
        (20261103, 20261113), (20261106, 20271107)]


class CandidateError(Exception):
    """Esito `errore` di una candidata (A1 §5): mai un verdetto."""


# ---------------------------------------------------------------- semi

def seed_null(s, k):
    return 3_000_000 + 100_000 * s + k


def seed_power(s, e, k):
    return 3_900_000 + 10_000 * (3 * (s - 1) + e) + k


def seed_boot_null(s, k, t):
    return 4_000_000 + 100_000 * s + 2 * k + t


def seed_boot_power(s, e, k, t):
    return 4_900_000 + 10_000 * (3 * (s - 1) + e) + 2 * k + t


def seeds_ok():
    seeds = [seed_null(s, k) for s in SCENARIOS for k in range(N_NULL)]
    seeds += [seed_power(s, e, k) for s in (1, 2) for e in range(3) for k in range(N_POWER)]
    seeds += [seed_boot_null(s, k, t) for s in SCENARIOS for k in range(N_NULL) for t in (0, 1)]
    seeds += [seed_boot_power(s, e, k, t) for s in (1, 2) for e in range(3) for k in range(N_POWER) for t in (0, 1)]
    seeds += [5_000_000 + k for k in range(1000)]
    clash = any(lo <= x < hi for x in seeds for lo, hi in USED)
    return (not clash) and len(set(seeds)) == len(seeds)


# ---------------------------------------------------------------- disegno reale congelato (solo variabili di disegno)

def build_design():
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    d = d[np.isfinite(d[ACT])][DESIGN_COLS].copy().reset_index(drop=True)
    del cat
    bad = [c for c in d.columns if c in RESPONSE_COLS or c.startswith("leg_")]
    assert not bad, f"colonne di risposta nel disegno: {bad}"
    return d


# ---------------------------------------------------------------- componente per rotazione e risposte sintetiche

def ar2_stationary_var(p1, p2):
    return (1 - p2) / ((1 + p2) * ((1 - p2) ** 2 - p1 ** 2))


def gen_x(spec, G, rng):
    """(G, 2) a varianza marginale 1 (piano §3)."""
    x = np.zeros((G, 2))
    if spec["kind"] == "none":
        return x
    if spec["kind"] == "ar1":
        k = spec["kappa"]
        L = np.linalg.cholesky(np.array([[1.0, k], [k, 1.0]]))
        phi = spec["phi"]
        x[0] = L @ rng.standard_normal(2)
        for t in range(1, G):
            x[t] = phi * x[t - 1] + np.sqrt(1 - phi ** 2) * (L @ rng.standard_normal(2))
        return x
    if spec["kind"] == "ar2":
        p1, p2 = spec["phi1"], spec["phi2"]
        z = np.zeros((G + 200, 2))
        for t in range(2, G + 200):
            z[t] = p1 * z[t - 1] + p2 * z[t - 2] + rng.standard_normal(2)
        return z[200:] / np.sqrt(ar2_stationary_var(p1, p2))
    if spec["kind"] == "steps":
        L = spec["length"]
        phase = int(rng.integers(0, L))
        blk = (np.arange(G) + phase) // L
        lev = rng.choice([-1.0, 1.0], size=(blk.max() + 1, 2))
        return lev[blk]
    raise ValueError(spec)


def responses(design, s, rng, beta_frac=0.0):
    """Risposte sintetiche T3 (gamma) e T5 (d_star) sotto il modello del piano §2."""
    spec = SCENARIOS[s]
    d = design
    lo, hi = int(d["CR"].min()), int(d["CR"].max())
    G = hi - lo + 1
    ti = d["CR"].astype(int).to_numpy() - lo
    hi_ = (d["hemisphere"] == "S").to_numpy().astype(int)
    x3 = gen_x(spec, G, rng)[ti, hi_]
    x5 = gen_x(spec, G, rng)[ti, hi_]
    n = len(d)
    if spec.get("t4"):
        e3 = rng.standard_t(4, n) / np.sqrt(2.0)
        e5 = rng.standard_t(4, n) / np.sqrt(2.0)
    else:
        e3 = rng.standard_normal(n)
        e5 = rng.standard_normal(n)
    phi = d["phi"].to_numpy()
    c = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else np.ones(n)
    s_ = d["sinlat"].to_numpy()
    a = d[ACT].to_numpy() - 1.0
    gamma = (GAMMA0 + beta_frac * GAMMA0 * a) * s_ + SD_E * c * e3 + SD_X * x3
    dstar = phi * ETA_BAR * (1.0 + beta_frac * a + c * e5 + 0.5 * x5)
    out = d.copy()
    out["gamma"] = gamma
    out["d_star"] = dstar
    return out


# ---------------------------------------------------------------- strumenti comuni

def wls(X, w, y):
    A = X.T @ (w[:, None] * X)
    if np.linalg.cond(A) > 1e12:
        raise CandidateError("XtWX mal condizionata")
    return np.linalg.solve(A, X.T @ (w * y))


def cell_keys(cr, hem):
    key = pd.MultiIndex.from_arrays([np.asarray(cr).astype(int), np.asarray(hem)])
    codes, uniq = pd.factorize(key)
    return codes, uniq


def test_units(dd, test):
    """Unita' della regressione di P2 e contributi a_i a beta_hat, con celle (CR, emisfero)."""
    if test == "T3":
        dz = p2d.design_t3(dd)
        a = p2d.wls_row(dz["Xf"], dz["w"])
        return dict(level="region", y=dz["y"], w=dz["w"], Xn=dz["Xn"], Xf=dz["Xf"], a=a,
                    cr=dz["cr"].astype(int), hem=dz["hem"], phi=dz["w"], beta=float(a @ dz["y"]))
    dz = p2d.design_t5(dd)
    g = p2d.wls_row(dz["Xf_c"], dz["W_c"])
    a = g[dz["k_of_i"]] * dz["agg"]
    cell_cr = pd.Series(dz["cr"]).groupby(dz["k_of_i"]).first().sort_index().to_numpy().astype(int)
    cell_hem = dz["cell_hem"]
    eta_c = np.bincount(dz["k_of_i"], weights=dz["agg"] * dz["z"], minlength=len(dz["W_c"]))
    return dict(level="cell", y=dz["z"], phi=dz["phi"], k_of_i=dz["k_of_i"], agg=dz["agg"], Xn_c=dz["Xn_c"],
                Xf_c=dz["Xf_c"], W_c=dz["W_c"], g=g, a=a, cr=dz["cr"].astype(int), hem=dz["hem"],
                cell_cr=cell_cr, cell_hem=cell_hem, eta_c=eta_c, beta=float(g @ eta_c))


# ---------------------------------------------------------------- candidata M: funzione di varianza (A1 §1)

def varfun_fit(p, logphi_c):
    Zm = np.column_stack([np.ones_like(logphi_c), logphi_c])
    beta = np.array([np.log(np.mean(p)), 0.0])
    for _ in range(100):
        eta = Zm @ beta
        mu = np.exp(eta)
        zw = eta + (p - mu) / mu
        new = np.linalg.lstsq(Zm, zw, rcond=None)[0]
        if np.max(np.abs(new - beta)) < 1e-8:
            return new
        beta = new
    raise CandidateError("IRLS della funzione di varianza non convergente")


def pseudo_obs(u):
    """Pseudo-osservazioni e_i^2 / (1 - 2h_i + sum h_j^2) nelle celle con almeno 2 unita'."""
    if u["level"] == "region":
        mean = u["Xn"] @ wls(u["Xn"], u["w"], u["y"])
        w = u["w"]
    else:
        eta_hat = u["Xn_c"] @ wls(u["Xn_c"], u["W_c"], u["eta_c"])
        mean = eta_hat[u["k_of_i"]]
        w = u["phi"]
    r = u["y"] - mean
    codes, _ = cell_keys(u["cr"], u["hem"])
    W = np.bincount(codes, weights=w)
    ucell = np.bincount(codes, weights=w * r) / W
    e = r - ucell[codes]
    h = w / W[codes]
    H = np.bincount(codes, weights=h ** 2)[codes]
    ncell = np.bincount(codes)[codes]
    multi = ncell >= 2                       # celle con una sola unita': nessuna pseudo-osservazione (A1 §5)
    p = np.full(len(e), np.nan)
    p[multi] = e[multi] ** 2 / (1 - 2 * h[multi] + H[multi])
    keep = multi & (p > 0)
    return p, keep, int((multi & ~(p > 0)).sum())


# ---------------------------------------------------------------- candidata M: REML (A1 §2)

def ar1_k(t, h, phi, kappa):
    lag = np.abs(t[:, None] - t[None, :])
    same = h[:, None] == h[None, :]
    return np.where(same, 1.0, kappa) * phi ** lag


def neg_reml(theta, y, X, v, t, h):
    phi, kappa, lsig = theta
    V = np.exp(lsig) * ar1_k(t, h, phi, kappa) + np.diag(v)
    try:
        cf = cho_factor(V, lower=True, check_finite=False)
    except (LinAlgError, ValueError):
        return 1e100
    logdet = 2 * np.sum(np.log(np.diag(cf[0])))
    ViX = cho_solve(cf, X, check_finite=False)
    Viy = cho_solve(cf, y, check_finite=False)
    A = X.T @ ViX
    try:
        ca = cho_factor(A, lower=True, check_finite=False)
    except (LinAlgError, ValueError):
        return 1e100
    logdetA = 2 * np.sum(np.log(np.diag(ca[0])))
    bhat = cho_solve(ca, X.T @ Viy, check_finite=False)
    r = y - X @ bhat
    quad = float(r @ cho_solve(cf, r, check_finite=False))
    val = 0.5 * (logdet + logdetA + quad)
    return val if np.isfinite(val) else 1e100


def reml_fit(y, X, v, t, h):
    n, k = X.shape
    r = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    s0 = float(r @ r / (n - k))
    lo_s, hi_s = np.log(1e-6 * s0), np.log(1e3 * s0)
    th0 = np.log(max(s0 - float(np.mean(v)), 0.1 * s0))
    best, n_valid = None, 0
    for phi0, k0 in ((0.0, 0.0), (0.5, 0.0), (0.9, 0.0), (0.5, -0.5), (0.5, 0.5)):
        res = minimize(neg_reml, x0=np.array([phi0, k0, th0]), args=(y, X, v, t, h), method="L-BFGS-B",
                       bounds=[(0.0, 0.98), (-0.98, 0.98), (lo_s, hi_s)],
                       options=dict(ftol=1e-10, gtol=1e-6, maxiter=500))
        if res.success and np.isfinite(res.fun) and res.fun < 1e99:
            n_valid += 1
            if best is None or res.fun < best.fun:
                best = res
    if best is None:
        raise CandidateError("REML: nessun avvio valido")
    phi, kappa, lsig = best.x
    V = np.exp(lsig) * ar1_k(t, h, phi, kappa) + np.diag(v)
    if np.linalg.cond(X.T @ np.linalg.solve(V, X)) > 1e12:
        raise CandidateError("XtV-1X mal condizionata all'ottimo")
    return dict(phi=float(phi), kappa=float(kappa), sigma_x2=float(np.exp(lsig)), n_valid_starts=n_valid,
                sigma_x_at_lower=int(lsig <= lo_s + 1e-6), neg_reml=float(best.fun))


def cell_level(u, sig2):
    """Risposte di cella, effetti fissi aggregati, varianze di campionamento, b (A1 §2)."""
    if u["level"] == "region":
        codes, uniq = cell_keys(u["cr"], u["hem"])
        w = u["w"]
        W = np.bincount(codes, weights=w)
        yc = np.bincount(codes, weights=w * u["y"]) / W
        Xc = np.column_stack([np.bincount(codes, weights=w * u["Xn"][:, j]) / W for j in range(u["Xn"].shape[1])])
        vc = np.bincount(codes, weights=w ** 2 * sig2) / W ** 2
        b = np.bincount(codes, weights=u["a"])
        cr = np.array([c for c, _ in uniq])
        hm = np.array([hh for _, hh in uniq])
        ind = float(np.sum(u["a"] ** 2 * sig2))
    else:
        k = u["k_of_i"]
        yc = u["eta_c"]
        Xc = u["Xn_c"]
        vc = np.bincount(k, weights=u["agg"] ** 2 * sig2, minlength=len(u["W_c"]))
        b = u["g"].copy()
        cr, hm = u["cell_cr"], u["cell_hem"]
        ind = float(np.sum(u["g"] ** 2 * vc))
    t = cr - cr.min()
    h = (hm == "S").astype(int)
    return yc, Xc, vc, b, t, h, ind


def candidate_m(u):
    p, keep, n_nonpos = pseudo_obs(u)
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    ab = varfun_fit(p[keep], logphi[keep] - m)
    sig2 = np.exp(ab[0] + ab[1] * (logphi - m))
    if not np.isfinite(sig2).all():
        raise CandidateError("varianza individuale non finita")
    yc, Xc, vc, b, t, h, ind = cell_level(u, sig2)
    if not (np.isfinite(vc).all() and (vc > 0).all()):
        raise CandidateError("varianze di cella non finite o nulle")
    fit = reml_fit(yc, Xc, vc, t, h)
    var = fit["sigma_x2"] * float(b @ ar1_k(t, h, fit["phi"], fit["kappa"]) @ b) + ind
    if not (np.isfinite(var) and var > 0):
        raise CandidateError("varianza di beta non finita o non positiva")
    zstat = u["beta"] / np.sqrt(var)
    return dict(stat=float(zstat), var_a=float(ab[0]), var_b=float(ab[1]), n_pseudo=int(keep.sum()),
                n_pseudo_nonpos=n_nonpos, **fit)


def m_variance_given(u, sig2, phi, kappa, sigma_x2):
    """Var(beta_hat) della candidata M con parametri dati (test preliminare 4)."""
    yc, Xc, vc, b, t, h, ind = cell_level(u, sig2)
    return sigma_x2 * float(b @ ar1_k(t, h, phi, kappa) @ b) + ind


# ---------------------------------------------------------------- candidata B: wild cluster bootstrap ristretto (A1 §3)

def b_units(u):
    if u["level"] == "region":
        return u["y"], u["w"], u["Xf"], u["Xn"], u["cr"]
    return u["eta_c"], u["W_c"], u["Xf_c"], u["Xn_c"], u["cell_cr"]


def wcr_pieces(y, w, X, X0, cl):
    n, k = X.shape
    G = int(cl.max()) + 1
    A = X.T @ (w[:, None] * X)
    if np.linalg.cond(A) > 1e12:
        raise CandidateError("XtWX mal condizionata")
    bread = np.linalg.inv(A)
    q = bread[-1]
    zeta = w * (X @ q)
    c = G / (G - 1) * (n - 1) / (n - k)
    beta = bread @ (X.T @ (w * y))
    uhat = y - X @ beta
    s = np.bincount(cl, weights=zeta * uhat, minlength=G)
    V = c * float(s @ s)
    if not (np.isfinite(V) and V > 0):
        raise CandidateError("V_CR1 osservata non positiva")
    t_obs = beta[-1] / np.sqrt(V)
    y0 = X0 @ wls(X0, w, y)
    rt = y - y0
    beta_y0 = bread @ (X.T @ (w * y0))
    C = np.vstack([bread @ (X[cl == g].T @ (w[cl == g] * rt[cl == g])) for g in range(G)])
    Ag = np.bincount(cl, weights=zeta * y0, minlength=G)
    Rg = np.bincount(cl, weights=zeta * rt, minlength=G)
    Q = np.vstack([zeta[cl == g] @ X[cl == g] for g in range(G)])
    return dict(t_obs=float(t_obs), beta_y0=beta_y0, C=C, Ag=Ag, Rg=Rg, Q=Q, c=c, G=G)


def wcr_tstar(pc, Wm):
    bstar = pc["beta_y0"][None, :] + Wm @ pc["C"]
    sstar = pc["Ag"][None, :] + Wm * pc["Rg"][None, :] - bstar @ pc["Q"].T
    Vstar = pc["c"] * np.sum(sstar ** 2, axis=1)
    if not (np.isfinite(Vstar).all() and (Vstar > 0).all()):
        raise CandidateError("V_CR1* non positiva")
    return bstar[:, -1] / np.sqrt(Vstar)


def wcr_tstar_direct(y, w, X, X0, cl, Wm):
    """Calcolo diretto (test preliminare 3): ristima completa per ogni replica."""
    n, k = X.shape
    G = int(cl.max()) + 1
    c = G / (G - 1) * (n - 1) / (n - k)
    y0 = X0 @ wls(X0, w, y)
    rt = y - y0
    out = np.empty(len(Wm))
    for b in range(len(Wm)):
        ys = y0 + rt * Wm[b, cl]
        A = X.T @ (w[:, None] * X)
        bread = np.linalg.inv(A)
        beta = bread @ (X.T @ (w * ys))
        uh = ys - X @ beta
        meat = np.zeros((k, k))
        for g in range(G):
            sg = X[cl == g].T @ (w[cl == g] * uh[cl == g])
            meat += np.outer(sg, sg)
        V = c * (bread @ meat @ bread)
        out[b] = beta[-1] / np.sqrt(V[-1, -1])
    return out


def candidate_b(u, seed):
    y, w, X, X0, cr = b_units(u)
    cl = (cr - cr.min()) // BLOCK
    _, cl = np.unique(cl, return_inverse=True)
    pc = wcr_pieces(y, w, X, X0, cl)
    rng = np.random.default_rng(seed)
    tstar = np.concatenate([wcr_tstar(pc, rng.choice(WEBB, size=(m, pc["G"])))
                            for m in (2000, 2000, 2000, 2000, 1999)])
    p_low = (1 + int((tstar <= pc["t_obs"]).sum())) / (B_BOOT + 1)
    p_high = (1 + int((tstar >= pc["t_obs"]).sum())) / (B_BOOT + 1)
    return dict(stat=pc["t_obs"], p_low=p_low, p_high=p_high, n_clusters=pc["G"])


# ---------------------------------------------------------------- un catalogo

def verdict_m(r):
    if r["stat"] < -Z:
        return "supportato"
    if r["stat"] > Z:
        return "opposto"
    return "non deciso"


def verdict_b(r):
    if r["p_low"] <= ALPHA:
        return "supportato"
    if r["p_high"] <= ALPHA:
        return "opposto"
    return "non deciso"


def run_catalogue(design, s, rng_seed, boot_seeds, beta_frac=0.0):
    dd = responses(design, s, np.random.default_rng(rng_seed), beta_frac)
    rows = []
    for t, test in enumerate(("T3", "T5")):
        u = test_units(dd, test)
        n_units = len(u["y"]) if test == "T3" else len(u["W_c"])
        assert n_units == (2485 if test == "T3" else 318), f"disegno non congelato: {test} {n_units}"
        for cand in ("M", "B"):
            row = dict(test=test, cand=cand)
            try:
                r = candidate_m(u) if cand == "M" else candidate_b(u, boot_seeds[t])
                row.update(r, verdict=verdict_m(r) if cand == "M" else verdict_b(r))
            except CandidateError as exc:
                row.update(verdict="errore", error=str(exc))
            rows.append(row)
    return rows


_DESIGN = None


def job(args):
    global _DESIGN
    kind, s, e, k = args
    if _DESIGN is None:
        _DESIGN = pd.read_pickle(OUT / "_design.pkl")
    if kind == "null":
        rows = run_catalogue(_DESIGN, s, seed_null(s, k), (seed_boot_null(s, k, 0), seed_boot_null(s, k, 1)))
        frac = 0.0
    else:
        frac = EFFECTS[e]
        rows = run_catalogue(_DESIGN, s, seed_power(s, e, k), (seed_boot_power(s, e, k, 0), seed_boot_power(s, e, k, 1)),
                             beta_frac=frac)
    for r in rows:
        r.update(kind=kind, scenario=s, effect=frac, k=k)
    return rows


# ---------------------------------------------------------------- test preliminari (A1 §6)

def _t1_series(k):
    rng = np.random.default_rng(5_000_000 + k)
    G = 400
    x = gen_x(dict(kind="ar1", phi=0.8, kappa=0.5), G, rng)
    t = np.repeat(np.arange(G), 2)
    h = np.tile([0, 1], G)
    y = x.ravel() + np.where(h == 0, 1.0, -0.5) + rng.normal(0, 0.5, 2 * G)
    keep = rng.random(2 * G) >= 0.15
    X = np.column_stack([(h == 0), (h == 1)]).astype(float)[keep]
    try:
        f = reml_fit(y[keep], X, np.full(keep.sum(), 0.25), t[keep], h[keep])
        return dict(k=k, ok=1, **f)
    except CandidateError:
        return dict(k=k, ok=0)


def _t2_rep(args):
    k, = args
    global _DESIGN
    if _DESIGN is None:
        _DESIGN = pd.read_pickle(OUT / "_design.pkl")
    rng = np.random.default_rng(5_000_000 + 200 + k)
    dd = _DESIGN.copy()
    phi = dd["phi"].to_numpy()
    c = (phi / np.median(phi)) ** -0.25
    dd["gamma"] = 15.0 * c * rng.standard_normal(len(dd))
    u = test_units(dd, "T3")
    p, keep, _ = pseudo_obs(u)
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    ab = varfun_fit(p[keep], logphi[keep] - m)
    a_true = np.log(225.0) - 0.5 * (m - np.log(np.median(phi)))
    return dict(k=k, a_hat=ab[0], b_hat=ab[1], a_true=a_true, b_true=-0.5)


def selftest(workers):
    from multiprocessing import Pool
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    # 5: nessuna risposta reale (asserzione in build_design)
    design = build_design()
    design.to_pickle(OUT / "_design.pkl")
    rows.append(dict(test="5_no_real_responses", value=0, condition="nessuna colonna di risposta", passed=True))
    with Pool(workers) as pool:
        t1 = pd.DataFrame(pool.map(_t1_series, range(200)))
        t2 = pd.DataFrame(pool.map(_t2_rep, [(k,) for k in range(200)]))
    v = t1[t1["ok"] == 1]
    rows += [
        dict(test="1_reml_valid_series", value=int(t1["ok"].sum()), condition=">= 198 su 200", passed=bool(t1["ok"].sum() >= 198)),
        dict(test="1_reml_mean_phi", value=float(v["phi"].mean()), condition="|media - 0,8| <= 0,02",
             passed=bool(abs(v["phi"].mean() - 0.8) <= 0.02)),
        dict(test="1_reml_mean_kappa", value=float(v["kappa"].mean()), condition="|media - 0,5| <= 0,05",
             passed=bool(abs(v["kappa"].mean() - 0.5) <= 0.05)),
        dict(test="1_reml_mean_sigma_x2", value=float(v["sigma_x2"].mean()), condition="|media - 1| <= 0,10",
             passed=bool(abs(v["sigma_x2"].mean() - 1.0) <= 0.10)),
        dict(test="2_varfun_mean_b", value=float(t2["b_hat"].mean()), condition="|media + 0,5| <= 0,05",
             passed=bool(abs(t2["b_hat"].mean() + 0.5) <= 0.05)),
        dict(test="2_varfun_mean_a_minus_true", value=float((t2["a_hat"] - t2["a_true"]).mean()),
             condition="|media(a_hat) - a| <= 0,05", passed=bool(abs((t2["a_hat"] - t2["a_true"]).mean()) <= 0.05)),
    ]
    # 3: wild cluster bootstrap vettorizzato contro diretto
    rng = np.random.default_rng(5_000_000 + 900)
    n, G = 30, 5
    X = np.column_stack([np.ones(n), rng.normal(size=n), rng.normal(size=n)])
    X0 = X[:, :2]
    w = rng.uniform(0.5, 2.0, n)
    y = X @ np.array([1.0, 0.5, 0.0]) + rng.normal(size=n)
    cl = np.repeat(np.arange(G), n // G)
    Wm = rng.choice(WEBB, size=(200, G))
    pc = wcr_pieces(y, w, X, X0, cl)
    tv = wcr_tstar(pc, Wm)
    td = wcr_tstar_direct(y, w, X, X0, cl, Wm)
    dmax = float(np.max(np.abs(tv - td)))
    pv = [(1 + int((tt <= pc["t_obs"]).sum())) / 201 for tt in (tv, td)]
    rows.append(dict(test="3_wcr_max_abs_diff", value=dmax, condition="<= 1e-10", passed=bool(dmax <= 1e-10)))
    rows.append(dict(test="3_wcr_pvalues_identical", value=float(pv[0] - pv[1]), condition="identici", passed=pv[0] == pv[1]))
    # 4: varianza di beta di M con parametri veri contro V_true di A (V1, k = 0)
    sil = run_p2.load_silso()
    cat = p2d.synthetic_catalog_p2d("V1", 40000, 0.0, 0.0)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], sil)
    a_ref = pd.read_csv(ROOT / "results/DIAGNOSTIC/A_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "test", "v_true"])
    for test, s2, sx2 in (("T3", 15.0 ** 2, 7.5 ** 2), ("T5", (2.0e-24) ** 2, (0.5 * 2.0e-24) ** 2)):
        u = test_units(d, test)
        var = m_variance_given(u, np.full(len(u["y"]), s2), 0.5, 0.0, sx2)
        ref = float(a_ref[(a_ref["scenario"] == "V1") & (a_ref["k"] == 0) & (a_ref["test"] == test)]["v_true"].iloc[0])
        rel = abs(var / ref - 1)
        rows.append(dict(test=f"4_M_variance_vs_A_{test}", value=rel, condition="scarto relativo <= 1e-9", passed=bool(rel <= 1e-9)))
    rows.append(dict(test="seeds_not_overlapping", value=0, condition="nessuna sovrapposizione", passed=seeds_ok()))
    res = pd.DataFrame(rows)
    st = provenance()
    res.assign(**st).to_csv(OUT / "PRELIM_TESTS.csv", index=False)
    t1.assign(**st).to_csv(OUT / "PRELIM_T1_REML.csv", index=False)
    t2.assign(**st).to_csv(OUT / "PRELIM_T2_VARFUN.csv", index=False)
    print(res.to_string(index=False))
    return 0 if res["passed"].all() else 2


# ---------------------------------------------------------------- pilota

def provenance():
    st = stamp(("P2", "P2d", "P2e"))
    for pl in PLANS:
        st[f"sha256_{pl.stem}"] = hashlib.sha256(pl.read_bytes()).hexdigest()
    st["status"] = "pilota di sviluppo, nessun verdetto"
    return st


def summarize(raw):
    rows = []
    null = raw[raw["kind"] == "null"]
    for (test, cand, s), g in null.groupby(["test", "cand", "scenario"]):
        n = len(g)
        fv = g["verdict"].isin(["supportato", "opposto"])
        err = g["verdict"] == "errore"
        ok = ~err
        rows.append(dict(test=test, cand=cand, scenario=s, n=n, false=int(fv.sum()), false_frac=fv.sum() / n,
                         false_supported=int((g["verdict"] == "supportato").sum()),
                         false_opposite=int((g["verdict"] == "opposto").sum()),
                         errors=int(err.sum()), error_frac=err.sum() / n,
                         false_frac_among_valid=fv[ok].mean() if ok.any() else np.nan,
                         scenario_ok=bool(fv.sum() <= 40 and err.sum() / n <= 0.02)))
    tab = pd.DataFrame(rows)
    pw = []
    power = raw[raw["kind"] == "power"]
    for (test, cand, s, e), g in power.groupby(["test", "cand", "scenario", "effect"]):
        det = g["verdict"] == "supportato"
        ok = g["verdict"] != "errore"
        pw.append(dict(test=test, cand=cand, scenario=s, effect=e, n=len(g), power=det.mean(),
                       power_among_valid=det[ok].mean() if ok.any() else np.nan, errors=int((~ok).sum())))
    pw = pd.DataFrame(pw)
    choice = []
    for test in ("T3", "T5"):
        kept = {c: bool(tab[(tab["test"] == test) & (tab["cand"] == c)]["scenario_ok"].all()) for c in ("M", "B")}
        pm = {c: float(pw[(pw["test"] == test) & (pw["cand"] == c) & np.isclose(pw["effect"], -0.2)]["power"].mean())
              for c in ("M", "B")}
        if kept["M"] and kept["B"]:
            pick = "B" if pm["B"] >= pm["M"] - 0.02 else "M"
        elif kept["M"] or kept["B"]:
            pick = "M" if kept["M"] else "B"
        else:
            pick = "nessuna"
        choice.append(dict(test=test, kept_M=kept["M"], kept_B=kept["B"], power_M=pm["M"], power_B=pm["B"], choice=pick))
    return tab, pw, pd.DataFrame(choice)


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
        print("test preliminari assenti: eseguire --selftest (A1 §6)")
        return 2
    pt = pd.read_csv(pre)
    if not pt["passed"].all() or pt["git_commit"].iloc[0] != st["git_commit"] or int(pt["git_dirty"].iloc[0]) or st["git_dirty"]:
        print("test preliminari non superati, eseguiti su un altro commit o albero non pulito: il pilota non parte")
        return 2
    design = build_design()
    design.to_pickle(OUT / "_design.pkl")
    jobs = [("null", s, 0, k) for s in SCENARIOS for k in range(N_NULL)]
    jobs += [("power", s, e, k) for s in (1, 2) for e in range(3) for k in range(N_POWER)]
    out = []
    with Pool(args.workers) as pool:
        for i, part in enumerate(pool.imap_unordered(job, jobs, chunksize=2), 1):
            out += part
            if i % 250 == 0:
                print(f"{i}/{len(jobs)} cataloghi", flush=True)
    raw = pd.DataFrame(out).sort_values(["kind", "scenario", "effect", "k", "test", "cand"]).reset_index(drop=True)
    raw.assign(**st).to_csv(OUT / "PILOT_RAW.csv.gz", index=False)
    tab, pw, ch = summarize(raw)
    tab.assign(**st).to_csv(OUT / "PILOT_FALSE_VERDICTS.csv", index=False)
    pw.assign(**st).to_csv(OUT / "PILOT_POWER.csv", index=False)
    ch.assign(**st).to_csv(OUT / "PILOT_CHOICE.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(tab.round(4).to_string(index=False))
        print(pw.round(3).to_string(index=False))
        print(ch.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
