"""Controllo diagnostico A: varianza nulla simulata da P2e contro varianza vera di beta_hat.

Piano registrato prima di questo codice: docs/DIAGNOSTIC_A_PLAN.md (commit 49508e5).
Sviluppo diagnostico, non validazione e non verdetto. Analitico: nessun numero casuale nuovo;
rigenera i cataloghi della validazione P2e (semi 40000 + k) con il codice esistente.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_a_variance.py [--n 2000] [--workers 12]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLAN = ROOT / "docs/DIAGNOSTIC_A_PLAN.md"
Z = norm.ppf(1 - p2d.ALPHA_SIDE)               # 2,2414
GAMMA0, ETA0, SD_T = 30.0, 2.0e-24, 15.0       # come synthetic_catalog_p2d
STEP_LEN = 20
ACT = "A_monthly"
_SILSO = None


# ---------------------------------------------------------------- covarianze della componente per rotazione

def lag_matrix(G):
    i = np.arange(G)
    return np.abs(i[:, None] - i[None, :])


def k_ar1(G, phi, kappa):
    kh = phi ** lag_matrix(G) if phi > 0 else np.eye(G)
    return np.kron(np.array([[1.0, kappa], [kappa, 1.0]]), kh)


def k_ar2(G, p1, p2):
    rho = np.empty(G)
    rho[0] = 1.0
    if G > 1:
        rho[1] = p1 / (1 - p2)
    for k in range(2, G):
        rho[k] = p1 * rho[k - 1] + p2 * rho[k - 2]
    return np.kron(np.eye(2), rho[lag_matrix(G)])


def k_steps(grid, first_cr):
    blk = (grid - first_cr) // STEP_LEN
    return np.kron(np.eye(2), (blk[:, None] == blk[None, :]).astype(float))


def k_true(spec, grid, first_cr):
    G = len(grid)
    if spec["kind"] == "none":
        return np.zeros((2 * G, 2 * G))
    if spec["kind"] == "ar1":
        return k_ar1(G, spec["phi"], spec.get("kappa", 0.0))
    if spec["kind"] == "ar2":
        return k_ar2(G, spec["phi1"], spec["phi2"])
    return k_steps(grid, first_cr)


def lag1_true(spec):
    if spec["kind"] == "ar2":
        return spec["phi1"] / (1 - spec["phi2"])
    if spec["kind"] == "steps":
        return (STEP_LEN - 1) / STEP_LEN
    return np.nan


def quad(b, K):
    v = np.concatenate([b[:, 0], b[:, 1]])
    return float(v @ K @ v)


# ---------------------------------------------------------------- un catalogo

def generator_gamma(scenario, seed, n=6000):
    """Ripete synthetic_catalog_p2d fino a gamma (stessa sequenza di numeri casuali) per contare |gamma| > 90."""
    spec = p2d.SCENARIOS[scenario]
    rng = np.random.default_rng(seed)
    silso = _SILSO["monthly"]
    t = pd.to_datetime("2010-06-01") + pd.to_timedelta(rng.uniform(0, 16 * 365.25, n), unit="D")
    cyc_ = np.where(t < pd.Timestamp("2020-01-01"), 24, 25)
    tmin = np.where(cyc_ == 24, np.datetime64("2008-12-01"), np.datetime64("2019-12-01"))
    phase = (t.values - tmin).astype("timedelta64[D]").astype(float) / 365.25 / 11
    hem = rng.choice([1, -1], n)
    lat = hem * np.clip(28 - 20 * phase + rng.normal(0, 4, n), 2, 45)
    s = np.sin(np.radians(np.abs(lat)))
    cr = (2096 + (t - pd.Timestamp("2010-06-01")).days / 27.2753).astype(int)
    phi = 10 ** rng.normal(21.7, 0.4, n)
    crs = np.arange(cr.min(), cr.max() + 1)
    hcol = (hem < 0).astype(int)
    zt = p2d.cr_component(spec, crs, rng)[cr - crs[0], hcol]
    p2d.cr_component(spec, crs, rng)
    scale = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else 1.0
    gamma = GAMMA0 * s + SD_T * scale * rng.normal(0, 1, n) + 0.5 * SD_T * zt
    return gamma, phi, crs[0]


def one(args):
    global _SILSO
    scenario, k = args
    if _SILSO is None:
        _SILSO = run_p2.load_silso()
    p2d.ESTIMATOR = "p2e"
    spec = p2d.SCENARIOS[scenario]
    cat = p2d.synthetic_catalog_p2d(scenario, 40000 + k, 0.0, 0.0)
    gamma_gen, phi_gen, first_cr = generator_gamma(scenario, 40000 + k)
    gen_ok = bool(np.array_equal(phi_gen, cat["USFLUX"].to_numpy()) and first_cr == cat["CR"].min())
    med_phi = float(np.median(cat["USFLUX"]))
    d = run_p2.add_activity(run_p2.samples(cat)["S"], _SILSO)
    out = []
    for test in ("T3", "T5"):
        dz = p2d.design_t3(d) if test == "T3" else p2d.design_t5(d)
        lp = p2d.linear_pieces(dz)
        par = lp["par"]
        if test == "T3":
            a = p2d.wls_row(dz["Xf"], dz["w"])
            y, wphi = dz["y"], dz["w"]
            dd = d[np.isfinite(d[ACT])]
            mu = float(a @ (GAMMA0 * dd["sinlat"].to_numpy()))
            sd_e, sd_x = SD_T, 0.5 * SD_T
            n_wrap = int((np.abs(gamma_gen[dd["HARPNUM"].to_numpy()]) > 90).sum())
            aligned = bool(np.array_equal(dd["phi"].to_numpy(float), wphi))
        else:
            a = p2d.wls_row(dz["Xf_c"], dz["W_c"])[dz["k_of_i"]] * dz["agg"]
            y, wphi = dz["z"], dz["phi"]
            mu = float(ETA0 * a.sum())
            sd_e, sd_x = ETA0, 0.5 * ETA0
            n_wrap, aligned = 0, True
        c = (wphi / med_phi) ** -0.25 if spec.get("hetero") else np.ones_like(wphi)
        grid = par["lo"] + np.arange(par["grid_len"])
        b = lp["B"]
        v_ind_true = float(sd_e ** 2 * np.sum(a ** 2 * c ** 2))
        v_tmp_true = sd_x ** 2 * quad(b, k_true(spec, grid, first_cr))
        v_true = v_ind_true + v_tmp_true
        v_ind_model = float(np.sum(lp["ge"] ** 2))
        row = dict(scenario=scenario, k=k, test=test, applicable=int(par["applicable"]),
                   phi_hat=par["phi"], kappa_hat=par["kappa"], sigma_u2_hat=par["sigma_u2"],
                   beta_obs=par["beta_obs"], beta_lin=float(a @ y), mu_true=mu, m_model=lp["const"],
                   v_true=v_true, v_ind_true=v_ind_true, v_tmp_true=v_tmp_true, v_ind_model=v_ind_model,
                   n_wrap_gamma=n_wrap, generator_ok=gen_ok, units_aligned=aligned)
        if par["applicable"]:
            ph = par["phi"] if np.isfinite(par["phi"]) else 0.0
            ka = par["kappa"] if np.isfinite(par["kappa"]) else 0.0
            v_tmp_model = par["sigma_u2"] * quad(b, k_ar1(len(grid), ph, ka)) if par["sigma_u2"] > 0 else 0.0
            v_model = v_ind_model + v_tmp_model
            sm, st_ = np.sqrt(v_model), np.sqrt(v_true)
            m = lp["const"]
            row.update(v_tmp_model=v_tmp_model, v_model=v_model, R=v_model / v_true,
                       R_ind=v_ind_model / v_ind_true,
                       R_tmp=(v_tmp_model / v_tmp_true) if v_tmp_true > 0 else np.nan,
                       p_pred=float(norm.cdf((m - Z * sm - mu) / st_) + norm.cdf((mu - m - Z * sm) / st_)))
            if spec["kind"] == "ar1":
                v_or = v_ind_model + v_tmp_true
                so = np.sqrt(v_or)
                row.update(R_oracle=v_or / v_true,
                           p_oracle=float(norm.cdf((m - Z * so - mu) / st_) + norm.cdf((mu - m - Z * so) / st_)))
        if spec["kind"] in ("ar2", "steps") and v_tmp_true > 0:
            row["R_AR1"] = sd_x ** 2 * quad(b, k_ar1(len(grid), lag1_true(spec), 0.0)) / v_tmp_true
        out.append(row)
    return out


# ---------------------------------------------------------------- controlli e sintesi

def rel_close(x, y, tol=1e-9):
    x, y = np.asarray(x, float), np.asarray(y, float)
    both_nan = np.isnan(x) & np.isnan(y)
    scale = np.maximum(np.maximum(np.abs(x), np.abs(y)), 1e-300)
    ok = both_nan | (np.abs(x - y) <= tol * scale) | (np.abs(x - y) == 0)
    return ok


def checks(res, raw):
    m = res.merge(raw[["scenario", "k", "test", "applicable", "phi_hat", "kappa_hat", "sigma_u2_hat", "verdict"]],
                  on=["scenario", "k", "test"], suffixes=("", "_raw"), how="left")
    rows = [
        dict(check="1_applicable_equal", n_fail=int((m["applicable"] != m["applicable_raw"]).sum())),
        dict(check="1_phi_hat_equal", n_fail=int((~rel_close(m["phi_hat"], m["phi_hat_raw"])).sum())),
        dict(check="1_kappa_hat_equal", n_fail=int((~rel_close(m["kappa_hat"], m["kappa_hat_raw"])).sum())),
        dict(check="1_sigma_u2_hat_equal", n_fail=int((~rel_close(m["sigma_u2_hat"], m["sigma_u2_hat_raw"])).sum())),
        dict(check="2_linear_beta_equal", n_fail=int((~rel_close(m["beta_lin"], m["beta_obs"])).sum())),
        dict(check="3_mean_true_small", n_fail=int((np.abs(m["mu_true"]) > 1e-6 * np.sqrt(m["v_true"])).sum())),
        dict(check="3_mean_model_small", n_fail=int((np.abs(m["m_model"]) > 1e-6 * np.sqrt(m["v_true"])).sum())),
        dict(check="4_generator_reconstruction", n_fail=int((~m["generator_ok"]).sum())),
        dict(check="4_units_aligned", n_fail=int((~m["units_aligned"]).sum())),
        dict(check="5_regions_abs_gamma_gt_90 (riportato)", n_fail=int(m["n_wrap_gamma"].sum())),
    ]
    c = pd.DataFrame(rows)
    c["n"] = len(m)
    c["mandatory"] = ~c["check"].str.startswith("5_")
    return c, m


def q(x, p):
    x = x.dropna()
    return float(np.quantile(x, p)) if len(x) else np.nan


def summary(m):
    m = m.copy()
    m["false"] = m["verdict"].isin(["quenching supportato (P2d)", "segno opposto (P2d)"])
    rows = []
    for (sc, test), g in m.groupby(["scenario", "test"]):
        a = g[g["applicable"] == 1]
        obs = a["false"].mean()
        se = np.sqrt(obs * (1 - obs) / len(a)) if len(a) else np.nan
        r = dict(scenario=sc, test=test, n=len(g), n_applicable=len(a), false_obs_applicable=obs, se_obs=se,
                 p_pred_mean=a["p_pred"].mean(), p_pred_minus_obs_in_se=(a["p_pred"].mean() - obs) / se if se else np.nan,
                 p_pred_mean_if_false=a.loc[a["false"], "p_pred"].mean(),
                 p_pred_mean_if_not_false=a.loc[~a["false"], "p_pred"].mean(),
                 spearman_R_phi_hat=float(spearmanr(a["R"], a["phi_hat"]).statistic) if len(a) > 2 else np.nan)
        for col in ("R", "R_ind", "R_tmp", "R_oracle", "R_AR1"):
            src = g if col == "R_AR1" else a
            if col in src and src[col].notna().any():
                r.update({f"{col}_median": q(src[col], 0.5), f"{col}_p10": q(src[col], 0.1),
                          f"{col}_p90": q(src[col], 0.9)})
        if "p_oracle" in a and a["p_oracle"].notna().any():
            r["p_oracle_mean"] = a["p_oracle"].mean()
        rows.append(r)
    return pd.DataFrame(rows)


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_DIAGNOSTIC_A_PLAN"] = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    st["status"] = "sviluppo diagnostico, nessun verdetto"
    jobs = [(sc, k) for sc in p2d.SCENARIOS for k in range(args.n)]
    with Pool(args.workers) as pool:
        res = pd.DataFrame([r for part in pool.imap_unordered(one, jobs, chunksize=8) for r in part])
    res = res.sort_values(["scenario", "k", "test"]).reset_index(drop=True)
    raw = pd.read_csv(ROOT / "results/P2/P2E_VALIDATION_RAW.csv.gz")
    raw = raw[raw["beta_frac"] == 0]
    chk, m = checks(res, raw)
    out = ROOT / "results/DIAGNOSTIC"
    out.mkdir(parents=True, exist_ok=True)
    tag = "" if args.n == 2000 else f"_N{args.n}"
    chk.assign(**st).to_csv(out / f"A_CHECKS{tag}.csv", index=False)
    print(chk.to_string(index=False))
    if (chk.loc[chk["mandatory"], "n_fail"] > 0).any():
        print("CONTROLLO OBBLIGATORIO FALLITO: A si ferma (piano §4); nessuna sintesi scritta")
        m.assign(**st).to_csv(out / f"A_BY_CATALOGUE{tag}.csv.gz", index=False)
        return 2
    m.drop(columns=["applicable_raw", "phi_hat_raw", "kappa_hat_raw", "sigma_u2_hat_raw"]).assign(**st).to_csv(
        out / f"A_BY_CATALOGUE{tag}.csv.gz", index=False)
    s = summary(m)
    s.assign(**st).to_csv(out / f"A_SUMMARY{tag}.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(s.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
