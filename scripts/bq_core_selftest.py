"""Selftest of python/sharpbl/bq_core.py on synthetic designs and responses only (no observed response is read).

Independent dense reference: the covariance is built directly (sd^2 phi^|t-t'| kappa^[h!=h'], every family as a
latent, X V X^T added) and log N is evaluated by a dense Cholesky.
Checks:
 1. log-likelihood: structured (banded + Schur) vs dense, with and without beta and v, several parameter sets;
 2. conditional posterior of the coefficients given psi vs the dense Gaussian formula;
 3. AR(1) precision inverted = phi^|dt| kappa^[h!=h'] on a calendar with CR gaps (no compressed calendar);
 4. slice sampler on a correlated Gaussian;
 5. Savage-Dickey (quadrature over one free coordinate) = ratio of evidences (quadrature) for nested M0/MQ, and
    the sampled Savage-Dickey estimate within Monte Carlo error;
 6. recovery of beta = -8, 0, +8 with short chains on a moderate synthetic design;
 7. timing on the real design structure (metadata only, synthetic y).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_core_selftest.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import bq_core as B  # noqa: E402

SEED = 36_400_101
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def synth_design(rng, n_t=40, n=180, with_v=False, with_beta=True, gap_every=7):
    t_all = np.array([t for t in range(n_t) if t % gap_every != 3])          # some CRs without records
    t = np.sort(rng.choice(t_all, n))
    h = rng.integers(0, 2, n)
    s = rng.uniform(0.05, 0.5, n)
    a = rng.uniform(-1.0, 2.0, n)
    lphi = rng.uniform(0.0, 1.5, n)
    cell = (t >= n_t // 2).astype(int) * 2 + h
    fam = np.arange(n)
    for i in range(1, n):                                                       # some recurrences (1-3 CR apart)
        if rng.uniform() < 0.25 and 0 < t[i] - t[i - 1] <= 3:
            fam[i] = fam[i - 1]
    return B.Design(t=t, h=h, s=s, a=a, lphi=lphi, cell=cell, fam=fam, n_t=n_t, n_cell=4, with_v=with_v, with_beta=with_beta)


def dense_cov(d, p):
    tt, hh = d.t[:, None], d.h[None, :]
    same_h = (d.h[:, None] == d.h[None, :])
    C = np.diag((p["sigma0"] * np.exp(p["q"] * d.lphi)) ** 2)
    C += p["sigma_x"] ** 2 * p["phi"] ** np.abs(tt - d.t[None, :]) * np.where(same_h, 1.0, p["kappa"])
    if d.with_v:
        C += np.outer(d.s, d.s) * p["sigma_v"] ** 2 * p["phi_v"] ** np.abs(tt - d.t[None, :]) * np.where(same_h, 1.0, p["kappa_v"])
    C += p["sigma_f"] ** 2 * (d.fam[:, None] == d.fam[None, :])
    del hh
    return C


def dense_loglik(d, x, y):
    p = B.unpack(d, x)
    C = dense_cov(d, p) + d.X @ np.diag(d.vprior) @ d.X.T
    c = cho_factor(C, lower=True)
    return -0.5 * (len(y) * math.log(2 * math.pi) + 2 * np.log(np.diag(c[0])).sum() + y @ cho_solve(c, y))


def dense_post(d, x, y):
    p = B.unpack(d, x)
    C0 = dense_cov(d, p)
    Ci = np.linalg.inv(C0)
    cov = np.linalg.inv(np.diag(1 / d.vprior) + d.X.T @ Ci @ d.X)
    return cov @ d.X.T @ Ci @ y, cov


def random_x(d, rng):
    x = [rng.uniform(1.5, 3.5), rng.uniform(-1.2, 0.5), rng.uniform(-1, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(-2, 2),
         rng.uniform(-1, 2)]
    if d.with_v:
        x += [rng.uniform(-1, 3), rng.uniform(-2.5, 2.5), rng.uniform(-2, 2)]
    return np.array(x)


def main():
    rng = np.random.default_rng(SEED)
    # 1-2
    worst_l, worst_p = 0.0, 0.0
    for with_v in (False, True):
        for with_beta in (True, False):
            d = synth_design(rng, with_v=with_v, with_beta=with_beta)
            for _ in range(4):
                x = random_x(d, rng)
                y = rng.normal(0, 20, d.n)
                ls, mu, cov = B.loglik(d, x, y, return_post=True)
                ld = dense_loglik(d, x, y)
                worst_l = max(worst_l, abs(ls - ld) / abs(ld))
                mu_d, cov_d = dense_post(d, x, y)
                worst_p = max(worst_p, np.max(np.abs(mu - mu_d)) / np.max(np.abs(mu_d)), np.max(np.abs(cov - cov_d)) / np.max(np.abs(cov_d)))
    ok("1. log-likelihood banded+Schur = dense (u, u+v; with/without beta; 16 cases)", worst_l < 1e-10, f"max rel {worst_l:.1e}")
    ok("2. coefficient posterior given psi = dense Gaussian formula", worst_p < 1e-8, f"max rel {worst_p:.1e}")
    # 3
    P, ld = B._ar1_precision(9, 1.7, -0.6, 0.4)
    t = np.repeat(np.arange(9), 2)
    hh = np.tile([0, 1], 9)
    Cd = 1.7 ** 2 * (-0.6) ** np.abs(t[:, None] - t[None, :]) * np.where(hh[:, None] == hh[None, :], 1.0, 0.4)
    ok("3. AR(1) precision^-1 = sd^2 phi^|dt| kappa^[h!=h'] (negative phi), log-det", np.allclose(np.linalg.inv(P), Cd, atol=1e-12)
       and abs(ld - np.linalg.slogdet(Cd)[1]) < 1e-10)
    # 4
    S = np.array([[1.0, 0.8], [0.8, 2.0]])
    Si = np.linalg.inv(S)
    dr, _, _, _ = B.slice_chain(lambda z: -0.5 * z @ Si @ z, np.zeros(2), 500, 6000, np.random.default_rng(SEED + 1))
    ok("4. slice sampler: correlated Gaussian mean and covariance", np.all(np.abs(dr.mean(0)) < 0.15) and np.allclose(np.cov(dr.T), S, rtol=0.15, atol=0.1),
       f"mean {dr.mean(0).round(3)}, cov {np.cov(dr.T).round(2).tolist()}")
    # 5: one free coordinate (log sigma0); the others fixed and shared by M0 and MQ
    dq = synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150)
    d0 = synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150, with_beta=False)
    xf = np.array([2.5, -0.4, 1.0, 0.8, -0.3, 0.7])
    pq = B.unpack(dq, xf)
    yv = np.random.default_rng(SEED + 3).multivariate_normal(dq.X[:, :4] @ np.array([20, 22, 18, 25.0]) - 4.0 * dq.a * dq.s,
                                                              dense_cov(dq, pq))
    grid = np.linspace(1.0, 4.5, 4001)
    dx = grid[1] - grid[0]

    def lpost(d, g):
        z = xf.copy()
        z[0] = g
        return B.log_prior(d, z) + B.loglik(d, z, yv)      # the fixed coordinates add the same constant to M0 and MQ
    lq = np.array([lpost(dq, g) for g in grid])
    l0 = np.array([lpost(d0, g) for g in grid])
    mx = max(lq.max(), l0.max())
    zq, z0 = np.exp(lq - mx).sum() * dx, np.exp(l0 - mx).sum() * dx
    log_bf_ev = math.log(z0) - math.log(zq)
    wq = np.exp(lq - lq.max())
    wq /= wq.sum()
    ords = []
    for g in grid[::20]:
        z = xf.copy()
        z[0] = g
        _, mu, cov = B.loglik(dq, z, yv, return_post=True)
        ords.append(math.exp(-0.5 * mu[-1] ** 2 / cov[-1, -1]) / math.sqrt(2 * math.pi * cov[-1, -1]))
    sd_post0 = float(np.dot(wq[::20] / wq[::20].sum(), ords))
    log_bf_sd = math.log(sd_post0) - math.log(1 / (math.sqrt(2 * math.pi) * dq.prior["beta_sd"]))
    ok("5a. Savage-Dickey (quadrature) = ratio of evidences (quadrature), nested M0/MQ with shared priors",
       abs(log_bf_sd - log_bf_ev) < 2e-3, f"log BF0Q: evidences {log_bf_ev:.5f}, Savage-Dickey {log_bf_sd:.5f}")
    # sampled version: chain on the single coordinate
    dr1, _, _, _ = B.slice_chain(lambda g: lpost(dq, g[0]), np.array([2.5]), 200, 2000, np.random.default_rng(SEED + 4))
    cond = []
    for g in dr1[:, 0]:
        z = xf.copy()
        z[0] = g
        _, mu, cov = B.loglik(dq, z, yv, return_post=True)
        cond.append((mu[-1], cov[-1, -1]))
    est, se = B.savage_dickey_log_bf0q(dq, np.array(cond))
    ok("5b. sampled Savage-Dickey within Monte Carlo error (4 x naive SE, inflated x3 for autocorrelation)",
       abs(est - log_bf_ev) < 4 * 3 * se + 1e-3, f"estimate {est:.4f} +- {se:.4f} vs {log_bf_ev:.4f}")
    # 6: recovery with all coordinates sampled
    for bt in (-8.0, 0.0, 8.0):
        rr = np.random.default_rng(SEED + 10 + int(bt))
        d6 = synth_design(rr, n_t=60, n=420)
        x6 = np.array([math.log(12.0), -0.3, math.log(3.0), 0.9, -0.4, math.log(2.0)])
        p6 = B.unpack(d6, x6)
        y6 = rr.multivariate_normal(d6.X[:, :4] @ np.array([22, 24, 18, 20.0]) + bt * d6.a * d6.s, dense_cov(d6, p6))
        dr6, _, _, _ = B.slice_chain(lambda z: B.log_post(d6, z, y6), x6, 150, 250, rr)
        c6 = B.beta_conditionals(d6, dr6[::5], y6)
        m = c6[:, 0].mean()
        sd = math.sqrt(c6[:, 1].mean() + c6[:, 0].var())
        ok(f"6. recovery beta = {bt:+.0f} (short chain; posterior mean within 3 SD)", abs(m - bt) < 3 * sd, f"mean {m:.2f}, SD {sd:.2f}")
    # 7: timing on the real design structure (design columns only)
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import bq_woodbury_benchmark as W
        dd = W.design()
        t_ = dd.CR.to_numpy() - dd.CR.min()
        cyc = dd.cyc.to_numpy()
        hem = (dd.hemisphere.to_numpy() == "S").astype(int)
        cell = (cyc == 25).astype(int) * 2 + hem
        lab, fam = np.unique(dd.family_id.to_numpy(), return_inverse=True)
        out = []
        for with_v in (False, True):
            dR = B.Design(t=t_, h=hem, s=dd.sinlat.to_numpy(), a=dd.A_monthly.to_numpy() - 1.0, lphi=np.log10(dd.phi.to_numpy() / 1e21),
                          cell=cell, fam=fam, n_t=int(t_.max()) + 1, n_cell=4, with_v=with_v)
            xR = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)] + ([math.log(5), 1.1, 0.2] if with_v else []))
            yR = np.random.default_rng(SEED + 20).normal(0, 25, dR.n)
            t0 = time.perf_counter()
            for _ in range(20):
                B.loglik(dR, xR, yR)
            out.append((with_v, dR.bw, (time.perf_counter() - t0) / 20))
        ok("7. timing on the real design structure (synthetic y): per log-likelihood evaluation", True,
           "; ".join(f"v={v}: bandwidth {bw}, {tm * 1e3:.1f} ms" for v, bw, tm in out))
    except Exception as exc:                                                     # timing is informative only
        ok("7. timing on the real design structure", False, repr(exc))
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
