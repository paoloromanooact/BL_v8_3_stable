"""BQ-HMI: bridge sampling for the L1 evidence (draft rev. 4 §6: optional evidence; synthetic only until frozen).

p(y | M) = integral of q(psi) = prior(psi) p(y | psi) over the sampling coordinates psi (coefficients and latent
states are already integrated analytically in bq_core.loglik).
- Proposal g: multivariate normal fitted on the FIRST half of the posterior draws (of every chain); the SECOND half
  enters the estimator, so the draws used to build the proposal are not reused for the integral.
- Iterative optimal bridge (Meng and Wong 1996; Gronau et al. 2017), on the log scale:
      r <- [mean_j l2_j / (s1 l2_j + s2 r)] / [mean_i 1 / (s1 l1_i + s2 r)],
  with l1 = q/g on the posterior draws, l2 = q/g on the proposal draws, s1 = N1eff/(N1eff + N2),
  s2 = N2/(N1eff + N2) and N1eff the effective size of the posterior half (batch means).
- Relative error (Fruhwirth-Schnatter 2004): RE^2 ~ Var_g(f1)/(N2 E_g(f1)^2) + tau Var_p(f2)/(N1 E_p(f2)^2), with
  f1 = l2/(s1 l2 + s2 r), f2 = 1/(s1 l1 + s2 r) and tau the integrated autocorrelation from batch means. The SE of the
  log evidence is about RE. The estimate is declared usable only by rules fixed before the data (rev. 4).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import logsumexp


def batch_tau(v, n_batches=20):
    """Integrated autocorrelation factor of v from batch means (at least 1)."""
    v = np.asarray(v, float)
    nb = min(n_batches, len(v) // 5)
    if nb < 4 or v.var() == 0:
        return 1.0
    bm = np.array([b.mean() for b in np.array_split(v, nb)])
    return max(1.0, float(bm.var(ddof=1) * (len(v) / nb) / v.var(ddof=1)))


def split_chains(chains):
    """List of (n_i, dim) chains -> (fit draws, estimation draws): first and second half of every chain."""
    fit, est = [], []
    for c in chains:
        c = np.asarray(c, float)
        c = c[:, None] if c.ndim == 1 else c
        h = len(c) // 2
        fit.append(c[:h])
        est.append(c[h:2 * h])
    return np.concatenate(fit), np.concatenate(est)


def bridge_log_evidence(logq, chains, rng, n_prop=None, tol=1e-10, max_iter=1000):
    """logq: log unnormalised posterior on the sampling coordinates; chains: list of (n, dim) arrays of posterior
    draws in chain order. Returns dict(log_evidence, se_log, iterations, converged, n1, n1_eff, n2)."""
    fit, est = split_chains(chains)
    dim = fit.shape[1]
    mu = fit.mean(0)
    cov = np.atleast_2d(np.cov(fit.T)) + 1e-12 * np.eye(dim)
    L = np.linalg.cholesky(cov)
    logdet = 2.0 * float(np.log(np.diag(L)).sum())

    def logg(x):
        z = np.linalg.solve(L, (np.atleast_2d(x) - mu).T)
        return -0.5 * (dim * math.log(2 * math.pi) + logdet + (z * z).sum(0))
    n1 = len(est)
    n2 = int(n_prop or n1)
    prop = mu + rng.standard_normal((n2, dim)) @ L.T
    l1 = np.array([logq(x) for x in est]) - logg(est)
    l2 = np.array([logq(x) for x in prop]) - logg(prop)
    l2 = np.where(np.isfinite(l2), l2, -np.inf)              # proposal draws outside the support contribute zero
    tau = batch_tau(np.exp(l1 - l1.max()))
    n1e = n1 / tau
    ls1, ls2 = math.log(n1e / (n1e + n2)), math.log(n2 / (n1e + n2))
    lr, conv = float(np.median(l1)), False
    for it in range(max_iter):
        num = logsumexp(l2 - np.logaddexp(ls1 + l2, ls2 + lr)) - math.log(n2)
        den = logsumexp(-np.logaddexp(ls1 + l1, ls2 + lr)) - math.log(n1)
        new = num - den
        if abs(new - lr) < tol:
            lr, conv = new, True
            break
        lr = new
    f1 = np.exp(l2 - np.logaddexp(ls1 + l2, ls2 + lr))
    f2 = np.exp(lr - np.logaddexp(ls1 + l1, ls2 + lr))      # scaled by r: the relative variance is unchanged
    re2 = f1.var(ddof=1) / (n2 * f1.mean() ** 2) + batch_tau(f2) * f2.var(ddof=1) / (n1 * f2.mean() ** 2)
    return dict(log_evidence=lr, se_log=math.sqrt(re2), iterations=it + 1, converged=conv, n1=n1, n1_eff=n1e, n2=n2)
