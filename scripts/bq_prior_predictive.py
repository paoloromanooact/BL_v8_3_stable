"""BQ-HMI preparation: prior predictive checks on the real T3 design (rev. 4 §2, §4, §7). No response is read.

Design columns only (bq_woodbury_benchmark.design: CR, hemisphere, sin|lat|, flux, activity, cycle, family). For each
prior draw:
- quenching component Q_i = beta a_i s_i (a = A - 1) and temporal-Joy component V_i = v_(t_i,h_i) s_i (bivariate AR(1)
  on the full calendar), their variances over the records;
- how much V can imitate beta: slope of V on the activity column after removing the four cycle-hemisphere columns
  (k s), i.e. the "beta-equivalent" of a v realisation, and the share of var(V) it explains;
- prior predictive latent tilt theta_i (all components plus the individual residual) and the share |theta| > 90
  (folded), the spread of sigma_i from q, and quantiles of the observed-scale gamma = F(theta).
Variants: sigma_v half-Normal 5 and 20; q sd 1 and 0.5; beta sd 2.5/5/10/20/40.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_prior_predictive.py --out reviews/BQ_PRIOR_PREDICTIVE_20261125 [--draws 4000]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import bq_woodbury_benchmark as W  # noqa: E402

SEED = 36_400_201


def hn(rng, scale, size):
    return np.abs(rng.normal(0.0, scale, size))


def ar1_paths(rng, n_draws, n_t, sd, phi, kappa):
    """(n_draws, n_t, 2) stationary bivariate AR(1) paths with marginal SD sd, persistence phi, correlation kappa."""
    z = np.empty((n_draws, n_t, 2))
    c = np.sqrt(np.clip(1 - kappa ** 2, 0, None))

    def biv():
        e1 = rng.standard_normal(n_draws)
        e2 = kappa * e1 + c * rng.standard_normal(n_draws)
        return np.stack([e1, e2], axis=1)
    z[:, 0] = biv()
    innov = np.sqrt(np.clip(1 - phi ** 2, 0, None))[:, None]
    for t in range(1, n_t):
        z[:, t] = phi[:, None] * z[:, t - 1] + innov * biv()
    return z * sd[:, None, None]


def run(n_draws):
    d = W.design()
    t = (d.CR.to_numpy() - d.CR.min()).astype(int)
    n_t = int(t.max()) + 1
    h = (d.hemisphere.to_numpy() == "S").astype(int)
    s = d.sinlat.to_numpy()
    a = d.A_monthly.to_numpy() - 1.0
    lphi = np.log10(d.phi.to_numpy() / 1e21)
    cell = (d.cyc.to_numpy() == 25).astype(int) * 2 + h
    Xk = np.zeros((len(d), 4))
    Xk[np.arange(len(d)), cell] = s
    x3 = a * s
    # residual maker on the k columns (unweighted: a geometric descriptor of the design, not an estimator)
    Q_, _ = np.linalg.qr(Xk)
    x3r = x3 - Q_ @ (Q_.T @ x3)
    rng = np.random.default_rng(SEED)
    rows = []
    for sv_scale in (5.0, 20.0):
        sv = hn(rng, sv_scale, n_draws)
        phv, kav = np.tanh(rng.standard_normal(n_draws)), np.tanh(rng.standard_normal(n_draws))
        vpath = ar1_paths(rng, n_draws, n_t, sv, phv, kav)
        V = vpath[:, t, h] * s                                           # (draws, records)
        Vr = V - (V @ Q_) @ Q_.T
        beta_eq = (Vr @ x3r) / (x3r @ x3r)
        share = (beta_eq ** 2 * (x3r @ x3r)) / np.maximum((Vr ** 2).sum(1), 1e-300)
        rows.append(dict(kind="v", sigma_v_scale=sv_scale, var_V_median=float(np.median(V.var(1))),
                         var_V_q90=float(np.quantile(V.var(1), 0.9)),
                         beta_equiv_abs_median=float(np.median(np.abs(beta_eq))), beta_equiv_abs_q90=float(np.quantile(np.abs(beta_eq), 0.9)),
                         beta_equiv_sd=float(beta_eq.std()), share_var_V_on_activity_median=float(np.median(share)),
                         share_var_V_on_activity_q90=float(np.quantile(share, 0.9))))
    for tau in (2.5, 5.0, 10.0, 20.0, 40.0):
        b = rng.normal(0.0, tau, n_draws)
        Qv = np.outer(b, x3)
        rows.append(dict(kind="beta", beta_sd=tau, var_Q_median=float(np.median(Qv.var(1))), var_Q_q90=float(np.quantile(Qv.var(1), 0.9)),
                         sd_x3_over_records=float(x3.std()), sd_x3_resid_on_k=float(x3r.std())))
    # full prior predictive (sigma_v 20 variant and base without v), q sd 1 and 0.5
    for with_v in (False, True):
        for q_sd in (1.0, 0.5):
            k = rng.normal(0, 40.0, (n_draws, 4))
            b = rng.normal(0, 10.0, n_draws)
            s0, sx, sf = hn(rng, 30.0, n_draws), hn(rng, 10.0, n_draws), hn(rng, 5.0, n_draws)
            q = rng.normal(0, q_sd, n_draws)
            ph, ka = np.tanh(rng.standard_normal(n_draws)), np.tanh(rng.standard_normal(n_draws))
            u = ar1_paths(rng, n_draws, n_t, sx, ph, ka)[:, t, h]
            mean = k @ Xk.T + np.outer(b, x3) + u
            if with_v:
                sv = hn(rng, 20.0, n_draws)
                mean = mean + ar1_paths(rng, n_draws, n_t, sv, np.tanh(rng.standard_normal(n_draws)),
                                        np.tanh(rng.standard_normal(n_draws)))[:, t, h] * s
            fam = pd.factorize(d.family_id.to_numpy())[0]
            bf = rng.standard_normal((n_draws, fam.max() + 1)) * sf[:, None]
            sig = s0[:, None] * np.exp(q[:, None] * lphi[None, :])
            theta = mean + bf[:, fam] + sig * rng.standard_normal(sig.shape)
            gam = np.degrees(np.arcsin(np.sin(np.radians(theta))))
            ratio = sig.max(1) / sig.min(1)
            rows.append(dict(kind="predictive", with_v=with_v, q_sd=q_sd, folded_share_median=float(np.median(np.mean(np.abs(theta) > 90, 1))),
                             folded_share_q90=float(np.quantile(np.mean(np.abs(theta) > 90, 1), 0.9)),
                             abs_theta_q50=float(np.median(np.abs(theta))), abs_theta_q90=float(np.quantile(np.abs(theta), 0.9)),
                             gamma_abs_q50=float(np.median(np.abs(gam))), gamma_abs_q90=float(np.quantile(np.abs(gam), 0.9)),
                             sigma_ratio_max_over_min_median=float(np.median(ratio)), sigma_ratio_q90=float(np.quantile(ratio, 0.9)),
                             sigma_i_q99=float(np.quantile(sig, 0.99))))
    meta = dict(seed=SEED, draws=n_draws, records=int(len(d)), n_cr=n_t, log10_flux_range=[float(lphi.min()), float(lphi.max())],
                note="design-only prior predictive; no response read; unweighted geometric projections")
    return pd.DataFrame(rows), meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=4000)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    t, meta = run(a.draws)
    a.out.mkdir(parents=True)
    t.to_csv(a.out / "PRIOR_PREDICTIVE.csv", index=False)
    (a.out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(json.dumps(meta))
    print(t.to_string(index=False))
