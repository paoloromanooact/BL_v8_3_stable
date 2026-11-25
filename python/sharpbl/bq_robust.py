"""BQ-HMI likelihoods L2 (Student-t, nu = 4 fixed) and L3 (folded latent tilt), draft rev. 4, not frozen. Synthetic only.

Both are Gibbs samplers built on the Gaussian core (bq_core):
- psi | (lam or branches): coordinate slice sweep on log prior + Gaussian log-likelihood with the coefficients and
  latent states integrated;
- latents | psi: one joint Gaussian draw (coefficients, AR(1) states, replicated families, singleton effects kept
  explicit, as required for the L2 step of lam);
- L2: lam_i | e_i ~ Gamma((nu + 1)/2, rate (nu + e_i^2 / s_i^2)/2), s_i^2 = sigma_i^2 (nu - 2)/nu, so that the marginal
  SD of the residual is sigma_i as in L1;
- L3: the observed gamma = F(theta), F = arcsin(sin) in degrees, theta latent and already signed by hemisphere. Given
  the shared part m_i, theta_i is DISCRETE over the preimages gamma + 360k and 180 - gamma + 360k with weights
  N(theta; m_i, sigma_i^2) (unit Jacobian on each branch). All preimages within 180 + R sigma_i of m_i are kept
  (R = 8.5): the omitted mass is below exp(-R^2/2) of the largest included weight per side.
beta under L3 is a coefficient of the LATENT tilt; comparisons with T3 need the projection of E[gamma | x].
"""
from __future__ import annotations

import math

import numpy as np

from . import bq_core as B

NU = 4.0
R_TRUNC = 8.5


def folded_logpdf(g, mu, sigma, r=R_TRUNC):
    """log f(gamma | mu, sigma) of gamma = F(theta), theta ~ N(mu, sigma^2), for -90 < gamma < 90 (degrees)."""
    g, mu, sigma = np.broadcast_arrays(np.asarray(g, float), np.asarray(mu, float), np.asarray(sigma, float))
    half = 180.0 + r * sigma.max()
    kmax = int(math.ceil((half + abs(mu).max() + 180.0) / 360.0)) + 1
    k = np.arange(-kmax, kmax + 1)
    cand = np.concatenate([g[..., None] + 360.0 * k, 180.0 - g[..., None] + 360.0 * k], axis=-1)
    z = (cand - mu[..., None]) / sigma[..., None]
    lw = -0.5 * z * z - 0.5 * math.log(2 * math.pi) - np.log(sigma)[..., None]
    m = lw.max(axis=-1)
    return m + np.log(np.exp(lw - m[..., None]).sum(axis=-1))


def draw_branches(g, m, sigma, rng, r=R_TRUNC):
    """theta_i from its discrete conditional over the preimages of gamma_i."""
    half = 180.0 + r * float(np.max(sigma))
    kmax = int(math.ceil((half + float(np.max(np.abs(m - g))) + 180.0) / 360.0)) + 1
    k = np.arange(-kmax, kmax + 1)
    cand = np.concatenate([g[:, None] + 360.0 * k, 180.0 - g[:, None] + 360.0 * k], axis=1)
    lw = -0.5 * ((cand - m[:, None]) / sigma[:, None]) ** 2
    lw -= lw.max(axis=1, keepdims=True)
    p = np.exp(lw)
    p /= p.sum(axis=1, keepdims=True)
    u = rng.uniform(size=len(g))[:, None]
    idx = (np.cumsum(p, axis=1) < u).sum(axis=1)
    return cand[np.arange(len(g)), np.minimum(idx, cand.shape[1] - 1)]


def _residual_sd(d, x, scale=1.0):
    p = B.unpack(d, x)
    return p["sigma0"] * np.exp(p["q"] * d.lphi) * math.sqrt(scale)


def gibbs(d: B.Design, y, x0, n_warm, n_keep, rng, kind="L2", nu=NU, keep_theta=True):
    """kind 'L2' (Student-t residuals) or 'L3' (folded latent tilt). Returns dict of saved psi draws, coefficient
    draws (theta), and per-iteration summaries (mean lam for L2, share of non-identity branches for L3)."""
    x = np.array(x0, float)
    scale = (nu - 2.0) / nu if kind == "L2" else 1.0
    lam = np.ones(d.n) if kind == "L2" else None
    obs = np.asarray(y, float)
    yy = obs.copy()                                  # L3: current latent tilt (identity branch at the start)

    def logf_factory():
        return lambda z: B.log_prior(d, z) + B.loglik(d, z, yy, lam=lam, scale=scale)
    logf = logf_factory()
    fx = logf(x)
    if not np.isfinite(fx):
        raise ValueError("initial point has zero density")
    W = B.Widths(len(x), n_warm)
    out = dict(psi=[], theta=[], summary=[], hits=0)
    for it in range(n_warm + n_keep):
        W.update(it, x)
        x, fx, h = B.slice_sweep(logf, x, fx, W.w, rng)
        out["hits"] += h
        W.record(it, x)
        theta, _, _, _, mean = B.draw_latents(d, x, yy, rng, lam=lam, scale=scale)
        if kind == "L2":
            s2 = _residual_sd(d, x, scale) ** 2
            e = yy - mean
            lam = rng.gamma((nu + 1.0) / 2.0, 2.0 / (nu + e * e / s2))
            summ = float(lam.mean())
        else:
            yy = draw_branches(obs, mean, _residual_sd(d, x), rng)
            summ = float(np.mean(np.abs(yy - obs) > 1e-9))
        logf = logf_factory()
        fx = logf(x)
        if it >= n_warm:
            out["psi"].append(x.copy())
            if keep_theta:
                out["theta"].append(theta)
            out["summary"].append(summ)
    return {k: (np.array(v) if isinstance(v, list) else v) for k, v in out.items()}
