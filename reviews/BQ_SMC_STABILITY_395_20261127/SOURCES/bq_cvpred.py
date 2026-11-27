"""BQ-HMI block predictive density for L1/L2/L3 by Monte Carlo over the training posterior (draft rev. 4 §6ter, NOT
frozen). Synthetic only.

For one posterior state of the TRAINING fit (psi; in L2 the training precisions lam; in L3 the training latent tilts),
one joint Gaussian draw of the latents from the training conditional (bq_core.draw_latents: coefficients theta, the
AR(1) states on the FULL calendar, so also at the CRs of the block) and one effect b_f ~ N(0, sigma_f^2) for each
family of the block (block families are excluded from the training, hence new), shared by all its members. With
m_i = X_i theta + u + s_i v + b_f and sigma_i = sigma0 exp(q log10(Phi/1e21)):
- L1: N(gamma_i; m_i, sigma_i^2);
- L2: t_nu(gamma_i; m_i, scale sigma_i sqrt((nu - 2)/nu)), the precision of the block residual integrated;
- L3: sum over ALL preimages of gamma_i of N(.; m_i, sigma_i^2), images added around the mean until the analytic bound
  of the omitted discrete density T over the retained S is <= 1e-12 (Codex reference BQ_L3_TAIL_REFERENCE_20261127):
  per side and lattice, sum_j f(d + j L) <= f(d) + survival(d / sigma) / L, L = 360 deg. Budget exhausted -> error.
The block term of one draw is sum_i log p(gamma_i | draw); the score is log mean_s exp(term_s) over the draws, never
the product of means, the mean of logs or a sum of marginals.

LIMIT (measured 27 Nov on synthetic L1 blocks against the analytic value, 4000 draws): this DIRECT estimator degenerates
as the block grows (weights ESS 277 / 12 / 2.6 / 1.0 for 7 / 45 / 111 / 197 records; bias -0.03 / -1.4 / -2.6 / -8.0,
with a stated MC SE that underestimates the error). HMI blocks have ~250 records: for L2/L3 a sequential or annealed
scheme must be chosen and verified before use (draft §6ter.5). score() therefore returns status score_not_established
when the weights ESS < ESS_W_MIN or the MC SE > MCSE_MAX (proposed thresholds, to be decided).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import gammaln, log_ndtr

from . import bq_core as B

L_PERIOD = 360.0
TAIL_TOL, IMAGE_BUDGET = 1e-12, 100_000
ESS_W_MIN, MCSE_MAX = 100.0, 0.1          # proposed (draft §6ter.5), not frozen


def shared_mean(dv: B.Design, theta, xs):
    """X theta + u (+ s v) of the block records, from a latent draw of the training fit (same calendar)."""
    return dv.X @ theta + xs[dv.iu] + (xs[dv.iv] * dv.s if dv.with_v else 0.0)


def new_family_effects(dv: B.Design, sigma_f, rng):
    """One N(0, sigma_f^2) effect per family of the block, shared by its members."""
    _, inv = np.unique(dv.fam, return_inverse=True)
    return rng.normal(0.0, sigma_f, inv.max() + 1)[inv]


def _logsumexp(v):
    m = np.max(v)
    return float(m + np.log(np.exp(v - m).sum()))


def folded_logpdf_bounded(g, mu, sigma, tol=TAIL_TOL, budget=IMAGE_BUDGET):
    """log of sum over the preimages g + L k and 180 - g + L k of N(.; mu, sigma^2), and the certified ratio T/S of
    the omitted to the retained discrete density. Images are added symmetrically around the one nearest to mu on each
    lattice until T/S <= tol."""
    if not (-90.0 < g < 90.0 and sigma > 0 and math.isfinite(mu)):
        raise ValueError("folded density: gamma in (-90, 90), finite mean and positive sigma required")
    lnorm = -0.5 * math.log(2 * math.pi) - math.log(sigma)
    terms, bound_logs = [], []
    for base in (g, 180.0 - g):
        k0 = round((mu - base) / L_PERIOD)
        K = 0
        while True:
            ks = np.arange(k0 - K, k0 + K + 1)
            x = base + L_PERIOD * ks
            lw = lnorm - 0.5 * ((x - mu) / sigma) ** 2
            # first omitted image on each side and its distance from the mean
            b = []
            for kk in (k0 - K - 1, k0 + K + 1):
                dist = abs(base + L_PERIOD * kk - mu)
                lf = lnorm - 0.5 * (dist / sigma) ** 2
                ls = log_ndtr(-dist / sigma) - math.log(L_PERIOD)          # survival(d/sigma) / L, a density
                b.append(np.logaddexp(lf, ls))
            S, T = _logsumexp(lw), _logsumexp(np.array(b))
            if T - S <= math.log(tol) or 2 * K + 1 >= budget:
                break
            K = 2 * K + 1
        if T - S > math.log(tol):
            raise RuntimeError("folded density: image budget exhausted before the tail bound")
        terms.append(lw)
        bound_logs.append(T)
    S = _logsumexp(np.concatenate(terms))
    return S, float(math.exp(_logsumexp(np.array(bound_logs)) - S))


def t_logpdf(x, m, scale, nu):
    z = (x - m) / scale
    return gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * math.log(nu * math.pi) - np.log(scale) - (nu + 1) / 2 * np.log1p(z * z / nu)


def block_term(dv: B.Design, yv, x, theta, xs, rng, kind="L1", nu=4.0):
    """sum_i log p(gamma_i | draw) over the block records and, for L3, the largest certified T/S."""
    p = B.unpack(dv, x)
    m = shared_mean(dv, theta, xs) + new_family_effects(dv, p["sigma_f"], rng)
    sig = p["sigma0"] * np.exp(p["q"] * dv.lphi)
    if kind == "L1":
        return float((-0.5 * math.log(2 * math.pi) - np.log(sig) - 0.5 * ((yv - m) / sig) ** 2).sum()), 0.0
    if kind == "L2":
        return float(t_logpdf(yv, m, sig * math.sqrt((nu - 2) / nu), nu).sum()), 0.0
    if kind == "L3":
        out = [folded_logpdf_bounded(g, mi, si) for g, mi, si in zip(yv, m, sig)]
        return float(sum(o[0] for o in out)), max(o[1] for o in out)
    raise ValueError(kind)


def block_terms(dt: B.Design, yt_state, dv: B.Design, yv, states, rng, kind="L1", nu=4.0, n_latent=1):
    """Block terms for a list of training posterior states (x, lam) (lam None for L1/L3; for L3 yt_state is a list of
    training latent tilts, one per state). n_latent latent draws per state. Returns (terms, max T/S)."""
    scale = (nu - 2.0) / nu if kind == "L2" else 1.0
    terms, tmax = [], 0.0
    for j, (x, lam) in enumerate(states):
        yt = yt_state[j] if kind == "L3" else yt_state
        for _ in range(n_latent):
            theta, xs, _, _, _ = B.draw_latents(dt, x, yt, rng, lam=lam, scale=scale)
            v, ts = block_term(dv, yv, x, theta, xs, rng, kind, nu)
            terms.append(v)
            tmax = max(tmax, ts)
    return np.array(terms), tmax


def score(terms, n_batches=20):
    """log mean exp of the block terms, MC SE by batch means (delta method), ESS of the weights and the largest share."""
    v = np.asarray(terms, float)
    mx = v.max()
    e = np.exp(v - mx)
    est = mx + math.log(e.mean())
    w = e / e.sum()
    nb = min(n_batches, len(v))
    se = np.nan
    if nb >= 2:
        bm = np.array([b.mean() for b in np.array_split(e, nb)])
        se = bm.std(ddof=1) / math.sqrt(nb) / e.mean()
    ess = float(1.0 / (w * w).sum())
    good = bool(np.isfinite(se) and ess >= ESS_W_MIN and se <= MCSE_MAX)
    return dict(score=float(est) if good else np.nan, score_raw=float(est), mc_se=float(se), ess_weights=ess, max_weight=float(w.max()),
                n=int(len(v)), status="ok" if good else "score_not_established")
