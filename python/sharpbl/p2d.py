"""Protocollo P2d: test di T3 e T5 calibrato per simulazione, e sua validazione.

La stima di P2 e' lineare nei dati: beta_hat = g . y, con g = riga di
(X'WX)^-1 X'W. Sotto la nulla simulata y* = media + u*_{cella} + e_i v_i, quindi
beta* = g.media + sum_celle (sum_{i in cella} g_i) u*_cella + sum_i g_i e_i v_i:
si simulano solo le componenti per cella (AR(1) bivariato) e i segni di
Rademacher, senza ricalcolare la regressione (verificato da un test contro il
ricalcolo diretto).

Interpretazioni di dettaglio (P2d non le fissa oltre il testo):
- "varianza pesata di u_{t,h}" in §3: pesi = peso totale della cella (somma
  dei pesi delle unita');
- T5: le regioni usate sono quelle delle celle con almeno 3 regioni (come P2).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import run_p2  # noqa: E402

M_MAIN = 20000
M_SENS = 5000
SEED_T3, SEED_T5 = 20261109, 20261110          # P2d
SEED_T3_P2E, SEED_T5_P2E = 20261111, 20261112  # P2e §5
PHI_MAX, KAPPA_MAX = 0.95, 0.95
MIN_CR, MIN_PAIRS = 30, 20
ALPHA_SIDE = 0.0125
CH = run_p2.CH


# ---------------------------------------------------------------- disegno

def design_t3(d, act="A_monthly"):
    """Unita' = regioni: y, pesi, X nullo, X completo, cella (CR, emisfero)."""
    d = d[np.isfinite(d[act])]
    s = d["sinlat"].to_numpy()
    Xn = run_p2.ch_columns(d, s)
    Xf = np.column_stack([Xn, (d[act].to_numpy() - 1.0) * s])
    return dict(y=d["gamma"].to_numpy(float), w=d["phi"].to_numpy(float), Xn=Xn, Xf=Xf,
                cr=d["CR"].to_numpy(float), hem=d["hemisphere"].to_numpy(), level="region")


def design_t5(d, act="A_monthly"):
    """Unita' simulate = regioni delle celle con >= 3 regioni; la regressione e' sulle celle (P2d §2)."""
    d = d[np.isfinite(d[act]) & np.isfinite(d["d_star"])].copy()
    d["cell"] = list(zip(d["CR"].astype(float), d["hemisphere"]))
    n = d.groupby("cell")["phi"].transform("size")
    d = d[n >= 3].copy()
    c = run_p2.cells(d, act, "d_star")          # stessa costruzione delle celle di P2
    c["cell"] = list(zip(c["CR"].astype(float), c["hemisphere"]))
    Xn_c = run_p2.ch_columns(c, 1.0)
    Xf_c = np.column_stack([Xn_c, c["abar"].to_numpy() - 1.0])
    W_c = c["phi"].to_numpy(float)
    # mappa regione -> cella e peso di aggregazione phi_i / sum phi della cella
    idx = {k: j for j, k in enumerate(c["cell"])}
    d = d[d["cell"].isin(idx)]
    k_of_i = d["cell"].map(idx).to_numpy()
    agg = d["phi"].to_numpy() / W_c[k_of_i]
    z = (d["d_star"] / d["phi"]).to_numpy(float)
    return dict(z=z, phi=d["phi"].to_numpy(float), k_of_i=k_of_i, agg=agg, Xn_c=Xn_c, Xf_c=Xf_c, W_c=W_c,
                cr=d["CR"].to_numpy(float), hem=d["hemisphere"].to_numpy(), cell_cyc=c["cyc"].to_numpy(),
                cell_hem=c["hemisphere"].to_numpy(), cell_eta=c["eta"].to_numpy(float), level="cell")


def wls_row(X, w, j=-1):
    """Riga j di (X'WX)^-1 X'W (vettore g tale che beta_j = g . y)."""
    A = X.T @ (w[:, None] * X)
    return (np.linalg.pinv(A) @ (X * w[:, None]).T)[j]


# ---------------------------------------------------------------- componenti per cella e parametri

def cell_components(r, w, cr, hem):
    """u_{t,h} (media pesata dei residui), e_i = r_i - u, varianza di campionamento della media di cella."""
    key = pd.MultiIndex.from_arrays([cr, hem])
    df = pd.DataFrame({"r": r, "w": w}, index=key)
    W = df.groupby(level=[0, 1])["w"].sum()
    u = (df["r"] * df["w"]).groupby(level=[0, 1]).sum() / W
    e = r - u.reindex(key).to_numpy()
    s2 = ((df["w"] ** 2) * (e ** 2)).groupby(level=[0, 1]).sum().to_numpy() / W.to_numpy() ** 2
    return u, W, e, pd.Series(s2, index=u.index)


def estimate_temporal(u, W, s2):
    """P2d §3: phi, sigma_u^2, kappa con vincoli, bordi e non stimabilita'."""
    flags = {}
    crs = np.array(sorted(set(u.index.get_level_values(0))))
    lo, hi = int(crs.min()), int(crs.max())
    grid = np.arange(lo, hi + 1)
    U = np.full((len(grid), 2), np.nan)
    for (t, h), val in u.items():
        U[int(t) - lo, 0 if h == "N" else 1] = val
    flags["n_cr"] = int(len(crs))
    a, b = U[1:], U[:-1]
    ok = np.isfinite(a) & np.isfinite(b)
    flags["n_pairs_phi"] = int(ok.sum())
    phi_raw = float((a[ok] * b[ok]).sum() / (b[ok] ** 2).sum()) if ok.sum() and (b[ok] ** 2).sum() > 0 else np.nan
    phi = float(np.clip(phi_raw, 0.0, PHI_MAX)) if np.isfinite(phi_raw) else np.nan
    flags["phi_raw"] = phi_raw
    flags["phi_at_boundary"] = int(np.isfinite(phi_raw) and (phi_raw <= 0 or phi_raw >= PHI_MAX))
    Wv = W.to_numpy()
    uv = u.to_numpy()
    mu = np.average(uv, weights=Wv)
    var_u = float(np.average((uv - mu) ** 2, weights=Wv) - np.average(s2.to_numpy(), weights=Wv))
    flags["sigma_u_at_boundary"] = int(var_u <= 0)
    sigma_u2 = max(var_u, 0.0)
    if np.isfinite(phi):
        inn = U[1:] - phi * U[:-1]
        both = np.isfinite(inn).all(axis=1)
    else:
        inn, both = np.full((len(grid) - 1, 2), np.nan), np.zeros(len(grid) - 1, bool)
    flags["n_cr_kappa"] = int(both.sum())
    kappa_raw = float(np.corrcoef(inn[both, 0], inn[both, 1])[0, 1]) if both.sum() >= 3 else np.nan
    kappa = float(np.clip(kappa_raw, -KAPPA_MAX, KAPPA_MAX)) if np.isfinite(kappa_raw) else np.nan
    flags["kappa_raw"] = kappa_raw
    flags["kappa_at_boundary"] = int(np.isfinite(kappa_raw) and abs(kappa_raw) >= KAPPA_MAX)
    flags["phi_not_estimable"] = int(flags["n_pairs_phi"] < MIN_PAIRS)
    flags["kappa_not_estimable"] = int(flags["n_cr_kappa"] < MIN_PAIRS)
    flags["too_few_cr"] = int(flags["n_cr"] < MIN_CR)
    flags["applicable"] = int(not (flags["phi_not_estimable"] or flags["kappa_not_estimable"] or flags["too_few_cr"]))
    return dict(phi=phi, sigma_u2=sigma_u2, kappa=kappa, lo=lo, grid_len=len(grid), **flags)


def leverage_variance(r, w, cr, hem, u):
    """P2e §1: leva h_i = w_i / W_cella e varianza di campionamento v corretta per la leva."""
    key = pd.MultiIndex.from_arrays([cr, hem])
    df = pd.DataFrame({"w": w}, index=key)
    W = df.groupby(level=[0, 1])["w"].transform("sum").to_numpy()
    h = w / W
    e = r - u.reindex(key).to_numpy()
    one_minus = np.maximum(1 - h, 0.05)
    v = pd.Series((w ** 2) * (e ** 2) / one_minus, index=key).groupby(level=[0, 1]).sum()
    Wc = df.groupby(level=[0, 1])["w"].sum()
    return v / Wc ** 2, one_minus


def estimate_temporal_p2e(u, W, v, n_groups):
    """P2e §2: momenti corretti per rumore (v con leva) e per la media stimata (B(phi), n_bar)."""
    from scipy.optimize import brentq
    flags = {}
    crs = np.array(sorted(set(u.index.get_level_values(0))))
    lo, hi = int(crs.min()), int(crs.max())
    G = hi - lo + 1
    U = np.full((G, 2), np.nan)
    Vv = np.full((G, 2), np.nan)
    for (t, h), val in u.items():
        j = 0 if h == "N" else 1
        U[int(t) - lo, j] = val
        Vv[int(t) - lo, j] = v[(t, h)]
    ubar = np.nanmean(U)
    Uc = U - ubar
    flags["n_cr"] = int(len(crs))
    c0 = float(np.nanmean(Uc ** 2) - np.nanmean(Vv))
    a, b = Uc[1:], Uc[:-1]
    ok = np.isfinite(a) & np.isfinite(b)
    flags["n_pairs_phi"] = int(ok.sum())
    c1 = float((a[ok] * b[ok]).mean()) if ok.any() else np.nan
    nbar = float(np.isfinite(U).sum()) / max(n_groups, 1)
    flags.update(c0=c0, c1=c1, nbar=nbar, ratio=(c1 / c0 if c0 > 0 else np.nan))
    B = lambda f: (1 + f) / ((1 - f) * nbar)  # noqa: E731
    phi, sigma_u2, kappa = np.nan, 0.0, np.nan
    flags["sigma_u_at_boundary"] = int(c0 <= 0)
    flags["phi_at_boundary"] = 0
    flags["kappa_at_boundary"] = 0
    flags["phi_raw"] = np.nan
    flags["kappa_raw"] = np.nan
    if c0 > 0 and np.isfinite(c1):
        R = c1 / c0
        g = lambda f: (f - B(f)) / (1 - B(f)) - R  # noqa: E731
        try:
            phi = float(brentq(g, 0.0, PHI_MAX))
            flags["phi_raw"] = phi
        except ValueError:
            phi = 0.0 if g(0.0) > 0 else PHI_MAX
            flags["phi_at_boundary"] = 1
        sigma_u2 = c0 / (1 - B(phi))
    both = np.zeros(G - 1, bool)
    if c0 > 0 and np.isfinite(phi):
        inn = Uc[1:] - phi * Uc[:-1]
        both = np.isfinite(inn).all(axis=1)
        if both.sum() >= 3:
            vnoise = Vv[1:][both] + phi ** 2 * Vv[:-1][both]
            sw2 = (inn[both] ** 2).mean(axis=0) - vnoise.mean(axis=0)
            flags["sw2_N"], flags["sw2_S"] = float(sw2[0]), float(sw2[1])
            if (sw2 > 0).all():
                kr = float((inn[both, 0] * inn[both, 1]).mean() / np.sqrt(sw2[0] * sw2[1]))
                flags["kappa_raw"] = kr
                kappa = float(np.clip(kr, -KAPPA_MAX, KAPPA_MAX))
                flags["kappa_at_boundary"] = int(abs(kr) >= KAPPA_MAX)
    if c0 <= 0:   # componente temporale assente: phi e kappa non usati
        phi, kappa = 0.0, 0.0
    flags["n_cr_kappa"] = int(both.sum())
    flags["phi_not_estimable"] = int(flags["n_pairs_phi"] < MIN_PAIRS)
    flags["kappa_not_estimable"] = int(flags["n_cr_kappa"] < MIN_PAIRS or (c0 > 0 and not np.isfinite(kappa)))
    flags["too_few_cr"] = int(flags["n_cr"] < MIN_CR)
    flags["applicable"] = int(not (flags["phi_not_estimable"] or flags["kappa_not_estimable"] or flags["too_few_cr"]))
    return dict(phi=phi, sigma_u2=sigma_u2, kappa=kappa, lo=lo, grid_len=G, **flags)


ESTIMATOR = "p2d"   # "p2d" (congelato) o "p2e" (emendamento)


def simulate_ar1(par, M, rng):
    """u* sulla griglia completa di CR: array (M, G, 2), partenza stazionaria."""
    G = par["grid_len"]
    phi, s2, k = par["phi"], par["sigma_u2"], par["kappa"]
    L = np.linalg.cholesky(np.array([[1.0, k], [k, 1.0]]) + 1e-12 * np.eye(2))
    out = np.empty((M, G, 2))
    sd_w = np.sqrt(s2 * (1 - phi ** 2))
    out[:, 0] = (rng.standard_normal((M, 2)) @ L.T) * np.sqrt(s2)
    for t in range(1, G):
        out[:, t] = phi * out[:, t - 1] + (rng.standard_normal((M, 2)) @ L.T) * sd_w
    return out


# ---------------------------------------------------------------- test calibrato

def linear_pieces(dz):
    """Pezzi lineari della stima: beta* = const + sum(B * U*) + V . ge, piu' stima osservata e parametri."""
    if dz["level"] == "region":
        y, w, Xn, Xf = dz["y"], dz["w"], dz["Xn"], dz["Xf"]
        mean = Xn @ (np.linalg.pinv(Xn.T @ (w[:, None] * Xn)) @ (Xn.T @ (w * y)))
        g = wls_row(Xf, w)
        beta_obs = float(g @ y)
        r = y - mean
        u, W, e, s2 = cell_components(r, w, dz["cr"], dz["hem"])
        coef_unit = g                     # contributo di ogni unita' a beta
    else:
        z, phi_i, k_of_i, agg = dz["z"], dz["phi"], dz["k_of_i"], dz["agg"]
        Xn_c, Xf_c, W_c = dz["Xn_c"], dz["Xf_c"], dz["W_c"]
        eta_c = np.bincount(k_of_i, weights=agg * z, minlength=len(W_c))
        eta_hat = Xn_c @ (np.linalg.pinv(Xn_c.T @ (W_c[:, None] * Xn_c)) @ (Xn_c.T @ (W_c * eta_c)))
        mean = eta_hat[k_of_i]
        g_c = wls_row(Xf_c, W_c)
        beta_obs = float(g_c @ eta_c)
        r = z - mean
        u, W, e, s2 = cell_components(r, phi_i, dz["cr"], dz["hem"])
        coef_unit = g_c[k_of_i] * agg     # beta = sum_i g_{k(i)} phi_i/Phi_k z_i
    if ESTIMATOR == "p2e":
        wts = dz["w"] if dz["level"] == "region" else dz["phi"]
        v, one_minus = leverage_variance(r, wts, dz["cr"], dz["hem"], u)
        if dz["level"] == "region":
            n_groups = int((np.abs(dz["Xn"]).sum(axis=0) > 0).sum())
        else:
            n_groups = len(set(zip(dz["cell_cyc"], dz["cell_hem"])))
        par = estimate_temporal_p2e(u, W, v, n_groups)
        e = e / np.sqrt(one_minus)        # P2e §1: residui corretti per la leva nel wild bootstrap
    else:
        par = estimate_temporal(u, W, s2)
    par["beta_obs"] = beta_obs
    t_idx = (dz["cr"].astype(int) - par["lo"])
    h_idx = (dz["hem"] == "S").astype(int)
    B = np.zeros((par["grid_len"], 2))
    np.add.at(B, (t_idx, h_idx), coef_unit)
    return dict(const=float(coef_unit @ mean), B=B, ge=coef_unit * e, mean=mean, e=e,
                t_idx=t_idx, h_idx=h_idx, par=par)


def null_distribution(dz, M, seed, chunk=2000):
    """Distribuzione nulla di beta (M valori) e parametri; (None, par) se P2d non applicabile."""
    rng = np.random.default_rng(seed)
    lp = linear_pieces(dz)
    par = lp["par"]
    if not par["applicable"]:
        return None, par
    sims = np.empty(M)
    for a in range(0, M, chunk):
        m = min(chunk, M - a)
        U = simulate_ar1(par, m, rng)
        V = rng.choice([-1.0, 1.0], size=(m, len(lp["ge"])))
        sims[a:a + m] = lp["const"] + np.einsum("mgh,gh->m", U, lp["B"]) + V @ lp["ge"]
    return sims, par


def decide(beta_obs, sims):
    """P2d §4: p-value Monte Carlo per verso con correzione finita, pareggi a sfavore."""
    M = len(sims)
    p_low = (1 + int((sims <= beta_obs).sum())) / (M + 1)
    p_high = (1 + int((sims >= beta_obs).sum())) / (M + 1)
    if p_low <= ALPHA_SIDE:
        v = "quenching supportato (P2d)"
    elif p_high <= ALPHA_SIDE:
        v = "segno opposto (P2d)"
    else:
        v = "non deciso (P2d)"
    return dict(p_low=p_low, p_high=p_high, verdict_p2d=v)


def p2d_test(d, test, M=M_MAIN, seed=None):
    dz = design_t3(d) if test == "T3" else design_t5(d)
    if seed is None:
        seed = ((SEED_T3_P2E if test == "T3" else SEED_T5_P2E) if ESTIMATOR == "p2e"
                else (SEED_T3 if test == "T3" else SEED_T5))
    sims, par = null_distribution(dz, M, seed)
    if sims is None:
        return dict(test=test, verdict_p2d="non applicabile (P2d §3)", **par)
    return dict(test=test, M=M, **par, **decide(par["beta_obs"], sims),
                null_mean=float(sims.mean()), null_sd=float(sims.std()))


# ---------------------------------------------------------------- validazione (P2d §5)

SCENARIOS = {
    "V0": dict(kind="none"),
    "V1": dict(kind="ar1", phi=0.5, kappa=0.0),
    "V2": dict(kind="ar1", phi=0.8, kappa=0.0),
    "V3": dict(kind="ar1", phi=0.8, kappa=0.6),
    "V4": dict(kind="ar1", phi=0.8, kappa=0.0, hetero=True),
    "V5": dict(kind="ar2", phi1=0.5, phi2=0.3),
    "V6": dict(kind="steps", length=20),
}
CORRECTLY_SPECIFIED = ["V0", "V1", "V2", "V3", "V4"]


def cr_component(spec, crs, rng):
    """Componente per rotazione (G, 2) a varianza marginale 1, secondo lo scenario."""
    G = len(crs)
    z = np.zeros((G, 2))
    if spec["kind"] == "none":
        return z
    if spec["kind"] == "ar1":
        k = spec.get("kappa", 0.0)
        L = np.linalg.cholesky(np.array([[1, k], [k, 1]]) + 1e-12 * np.eye(2))
        phi = spec["phi"]
        z[0] = L @ rng.standard_normal(2)
        for t in range(1, G):
            z[t] = phi * z[t - 1] + np.sqrt(1 - phi ** 2) * (L @ rng.standard_normal(2))
        return z
    if spec["kind"] == "ar2":
        p1, p2 = spec["phi1"], spec["phi2"]
        x = np.zeros((G + 200, 2))
        for t in range(2, G + 200):
            x[t] = p1 * x[t - 1] + p2 * x[t - 2] + rng.standard_normal(2)
        x = x[200:]
        return x / x.std(axis=0)
    if spec["kind"] == "steps":
        nb = int(np.ceil(G / spec["length"]))
        lev = rng.choice([-1.0, 1.0], size=(nb, 2))
        return np.repeat(lev, spec["length"], axis=0)[:G]
    raise ValueError(spec)


def synthetic_catalog_p2d(scenario, seed, beta_t_frac=0.0, beta_eta_frac=0.0, n=6000):
    """Come run_p2.synthetic_catalog, con la componente per rotazione dello scenario (P2d §5)."""
    spec = SCENARIOS[scenario]
    gamma0, eta0, sd_t = 30.0, 2.0e-24, 15.0
    rng = np.random.default_rng(seed)
    silso = run_p2.load_silso()["monthly"]
    t = pd.to_datetime("2010-06-01") + pd.to_timedelta(rng.uniform(0, 16 * 365.25, n), unit="D")
    cyc_ = np.where(t < pd.Timestamp("2020-01-01"), 24, 25)
    tmin = np.where(cyc_ == 24, np.datetime64("2008-12-01"), np.datetime64("2019-12-01"))
    phase = (t.values - tmin).astype("timedelta64[D]").astype(float) / 365.25 / 11
    hem = rng.choice([1, -1], n)
    lat = hem * np.clip(28 - 20 * phase + rng.normal(0, 4, n), 2, 45)
    a = np.array([silso.at[m, "N" if h > 0 else "S"] for m, h in zip(t.strftime("%Y-%m"), hem)])
    s = np.sin(np.radians(np.abs(lat)))
    cr = (2096 + (t - pd.Timestamp("2010-06-01")).days / 27.2753).astype(int)
    phi = 10 ** rng.normal(21.7, 0.4, n)
    crs = np.arange(cr.min(), cr.max() + 1)
    hcol = (hem < 0).astype(int)
    zt = cr_component(spec, crs, rng)[cr - crs[0], hcol]
    zd = cr_component(spec, crs, rng)[cr - crs[0], hcol]
    scale = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else 1.0
    gamma = (gamma0 + beta_t_frac * gamma0 * (a - 1)) * s + sd_t * scale * rng.normal(0, 1, n) + 0.5 * sd_t * zt
    dstar = phi * eta0 * (1 + beta_eta_frac * (a - 1) + scale * rng.normal(0, 1, n) + 0.5 * zd)
    sc = np.where(cyc_ == 24, 1.0, -1.0)
    sintilt = np.sin(np.radians(gamma)) * np.sign(lat)
    cat = pd.DataFrame({
        "HARPNUM": np.arange(n), "T_REC": t.strftime("%Y.%m.%d_%H:%M:%S_TAI"), "role": "both",
        "qual_0x80": 0, "NOAA_NUM": 1, "USFLUX": phi, "LAT_FWT": lat, "CR": cr,
        "valid_bl": 1, "npos": 100, "nneg": 100, "phi_mx": phi, "lat_mean_deg": lat, "cycle": cyc_,
        "cycle_state": "DATE", "sintilt": sintilt, "d_axial_bal_g": dstar / sc,
        "s_bl": np.sign(lat) * dstar * 1e40, "diagnostic_reason": "NONE",
    })
    for c in ("valid_bl", "phi_mx", "lat_mean_deg", "cycle", "sintilt", "s_bl"):
        cat[f"leg_{c}"] = cat[c]
    return cat


_SILSO = None


def one_outer(args):
    """Una simulazione esterna: procedura completa (stima + calibrazione interna + decisione)."""
    global _SILSO
    scenario, k, beta_frac, M = args
    if _SILSO is None:
        _SILSO = run_p2.load_silso()
    p2e = ESTIMATOR == "p2e"
    base = (40000 if p2e else 30000) if beta_frac == 0 else (140000 if p2e else 100000)
    inner = 60000 if p2e else 50000
    cat = synthetic_catalog_p2d(scenario, base + k, beta_frac, beta_frac)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], _SILSO)
    out = []
    for test, seed in (("T3", inner + 2 * k), ("T5", inner + 1 + 2 * k)):
        r = p2d_test(d, test, M=M, seed=seed)
        out.append(dict(scenario=scenario, k=k, beta_frac=beta_frac, test=test, verdict=r["verdict_p2d"],
                        applicable=r["applicable"], phi_at_boundary=r["phi_at_boundary"],
                        sigma_u_at_boundary=r["sigma_u_at_boundary"], kappa_at_boundary=r["kappa_at_boundary"],
                        phi_hat=r["phi"], kappa_hat=r["kappa"], sigma_u2_hat=r["sigma_u2"],
                        estimator=ESTIMATOR))
    return out


def cp_upper(k, n, a=0.05):
    return 1.0 if k >= n else float(beta_dist.ppf(1 - a, k + 1, n - k))


def summarize_validation(raw):
    rows = []
    null = raw[raw["beta_frac"] == 0]
    for (sc, test), g in null.groupby(["scenario", "test"]):
        n = len(g)
        app = g["applicable"] == 1
        sup = (g["verdict"] == "quenching supportato (P2d)").sum()
        opp = (g["verdict"] == "segno opposto (P2d)").sum()
        fp = sup + opp
        n_app = int(app.sum())
        rows.append(dict(
            scenario=sc, test=test, n=n, n_applicable=n_app, frac_applicable=n_app / n,
            n_fallback=int(n - n_app), false_total=int(fp), false_frac_total=fp / n,
            false_cp_upper95=cp_upper(int(fp), n), mc_se=np.sqrt((fp / n) * (1 - fp / n) / n),
            false_among_applicable=(fp / n_app) if n_app else np.nan,
            false_cp_upper95_applicable=cp_upper(int(fp), n_app) if n_app else np.nan,
            false_predicted_direction=int(sup), false_opposite_direction=int(opp),
            frac_not_decided=float((g["verdict"] == "non deciso (P2d)").mean()),
            frac_phi_boundary=float(g["phi_at_boundary"].mean()), frac_sigma_boundary=float(g["sigma_u_at_boundary"].mean()),
            frac_kappa_boundary=float(g["kappa_at_boundary"].mean()),
            accepted_rule=bool(cp_upper(int(fp), n) <= 0.04) if sc in CORRECTLY_SPECIFIED else None))
    tab = pd.DataFrame(rows)
    fw = null.assign(false=null["verdict"].isin(["quenching supportato (P2d)", "segno opposto (P2d)"]))
    fw = fw.groupby(["scenario", "k"])["false"].any().groupby("scenario").agg(["sum", "size"])
    tab = tab.merge(fw.rename(columns={"sum": "n_any_false_T3_T5", "size": "n_catalogues"}).reset_index(),
                    on="scenario", how="left")
    power = raw[raw["beta_frac"] != 0].groupby(["scenario", "test"]).apply(
        lambda g: pd.Series(dict(n=len(g), power=float((g["verdict"] == "quenching supportato (P2d)").mean()))),
        include_groups=False).reset_index()
    acc = {t: bool(tab[(tab["test"] == t) & tab["scenario"].isin(CORRECTLY_SPECIFIED)]["accepted_rule"].all())
           for t in ("T3", "T5")}
    return tab, power, acc


def run_validation(n_outer=2000, n_power=500, M=M_MAIN, workers=12):
    from multiprocessing import Pool
    jobs = [(sc, k, 0.0, M) for sc in SCENARIOS for k in range(n_outer)]
    jobs += [(sc, k, -0.2, M) for sc in ("V1", "V2") for k in range(n_power)]
    with Pool(workers) as pool:  # lanciare con OMP_NUM_THREADS=1 (un thread BLAS per processo)
        raw = [r for part in pool.imap_unordered(one_outer, jobs, chunksize=4) for r in part]
    return pd.DataFrame(raw)


def main() -> int:
    import argparse
    from sharpbl.provenance import ROOT, stamp
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--n-outer", type=int, default=2000)
    ap.add_argument("--n-power", type=int, default=500)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--estimator", choices=["p2d", "p2e"], default="p2e")
    args = ap.parse_args()
    global ESTIMATOR
    ESTIMATOR = args.estimator
    if not args.validate:
        print("uso: --validate (P2d §5)")
        return 1
    st = stamp(("P2", "P2b", "P2c", "P2d", "P2e"))
    st["estimator"] = ESTIMATOR
    if st.get("git_dirty"):
        print("modifiche non committate: la validazione registra il commit all'avvio e richiede un albero pulito")
        return 2
    out = ROOT / "results/P2"
    out.mkdir(parents=True, exist_ok=True)
    raw = run_validation(args.n_outer, args.n_power, workers=args.workers)
    tag = "P2E" if ESTIMATOR == "p2e" else "P2D"
    raw.assign(**st).to_csv(out / f"{tag}_VALIDATION_RAW.csv", index=False)
    tab, power, acc = summarize_validation(raw)
    tab.assign(**st).to_csv(out / f"{tag}_VALIDATION.csv", index=False)
    power.assign(**st).to_csv(out / f"{tag}_VALIDATION_POWER.csv", index=False)
    pd.DataFrame([dict(test=t, accepted=v) for t, v in acc.items()]).assign(**st).to_csv(
        out / f"{tag}_ACCEPTANCE.csv", index=False)
    params = raw[raw["beta_frac"] == 0].groupby(["scenario", "test"])[["phi_hat", "kappa_hat", "sigma_u2_hat"]].agg(
        ["mean", "std"])
    params.columns = ["_".join(c) for c in params.columns]
    params.reset_index().assign(**st).to_csv(out / f"{tag}_VALIDATION_PARAMETERS.csv", index=False)
    print(tab.to_string(index=False))
    print(power.to_string(index=False))
    print(acc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
