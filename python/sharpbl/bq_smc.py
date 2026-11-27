"""BQ-HMI sequential (SMC) block predictive density at fixed psi (draft rev. 4 §6ter.10, NOT frozen). Synthetic only.

Target: log p(y_block | y_train, psi[, training precisions or training latent tilts]).
- Gaussian state z = (theta, AR(1) states at the CRs of the block, effects of the families with >= 2 members in the
  block). Its prior is the EXACT Gaussian conditional of the training fit (bq_core system: theta ~ N(st, S^-1);
  states | theta ~ N(Sx_b - Sx_T theta, Axx^-1)); block families are new: N(0, sigma_f^2). A family with one member in
  the block is absorbed in the variance of that record.
- Records in order (CR, index). At record j, for each particle: predictive mean a.mu, variance c = a Sigma a + r_j.
  The block score accumulates log sum_i W_i^(j-1) p_i(y_j | prefix) with the prefix weights, BEFORE any resampling.
  L1: exact Kalman with one particle (no randomness). L2: the record precision on a discrete measure, a uniform grid
  in u = log(lam) on [-30, 5] with trapezoid weights of the Gamma(nu/2, nu/2) density (Jacobian lam), mass 1
  (n_quad = 200 points; revision of 27 Nov: the generalised Gauss-Laguerre rule used before had log errors of -1.1 at
  20 and -26 at 50 residual scales with 64 nodes, the grid 3.6e-15 in reviews/BQ_L2_QUADRATURE_20261127/). The same
  weighted integrand gives the predictive (its sum), the conditional draw (its normalisation) and the rejuvenation
  draws. L3: ONE routine (images) builds the retained preimages, their weights and the certified bound T/S <= 1e-12
  for the folded predictive (predictive variance integrated), for the proposal of the preimage and for the
  rejuvenation draws; the reported max T/S covers all of them.
- Resampling (systematic) when the ESS of the weights < N/2; then rejuvenation by data-augmentation Gibbs on the prefix
  (z | auxiliaries, then each auxiliary | z), which leaves the conditional of the auxiliaries given the prefix
  invariant (Del Moral, Doucet & Jasra 2006). L2 singleton-family records: b_k | z, lam_k, then lam_k | z, b_k.
The precision of a score is measured with independent replicates, not from the ESS after resampling.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.linalg import cho_solve, cho_solve_banded
from scipy.special import gammaln, log_ndtr

from . import bq_core as B, bq_cv as CV, bq_cvpred as P

LOG2PI = math.log(2 * math.pi)


# ---------------------------------------------------------------- Gaussian prior of the block state

def block_state(d: B.Design, train, ver, x, y_train, lam_train=None, scale=1.0):
    """Prior of z from the training fit and the block's observation structure. Returns dict with mu0, Sig0, rows A
    (one per block record, in processing order), base record variance sig2 (sigma_i^2, without lam or scale), the
    singleton-family extra variance sf2_single (sigma_f^2 or 0), the order and the observed gamma."""
    dt, dv = CV.subset(d, train), CV.subset(d, ver)
    sy = B._system(dt, x, y_train, lam_train, scale)
    p = B.unpack(dt, x)
    m = dt.m
    S_th = cho_solve(sy["cs"], np.eye(m))
    K = np.unique(np.r_[dv.iu, dv.iv] if dv.with_v else dv.iu)
    E = np.zeros((dt.nx, len(K)))
    E[K, np.arange(len(K))] = 1.0
    Ainv_K = cho_solve_banded((sy["cb"], False), E)[K]
    T_K = sy["Sx_T"][K]
    mean_K = sy["Sx_b"][K] - T_K @ sy["st"]
    cov_KK = Ainv_K + T_K @ S_th @ T_K.T
    cov_Kt = -T_K @ S_th
    labels, inv, cnt = np.unique(dv.fam, return_inverse=True, return_counts=True)
    shared = np.flatnonzero(cnt >= 2)
    fpos = -np.ones(len(labels), int)
    fpos[shared] = np.arange(len(shared))
    D = m + len(K) + len(shared)
    mu0 = np.r_[sy["st"], mean_K, np.zeros(len(shared))]
    Sig0 = np.zeros((D, D))
    Sig0[:m, :m] = S_th
    Sig0[m:m + len(K), m:m + len(K)] = cov_KK
    Sig0[m:m + len(K), :m] = cov_Kt
    Sig0[:m, m:m + len(K)] = cov_Kt.T
    Sig0[m + len(K):, m + len(K):] = np.eye(len(shared)) * p["sigma_f"] ** 2
    kpos = {k: i for i, k in enumerate(K)}
    A = np.zeros((dv.n, D))
    A[:, :m] = dv.X
    for i in range(dv.n):
        A[i, m + kpos[dv.iu[i]]] += 1.0
        if dv.with_v:
            A[i, m + kpos[dv.iv[i]]] += dv.s[i]
        if fpos[inv[i]] >= 0:
            A[i, m + len(K) + fpos[inv[i]]] = 1.0
    sig2 = (p["sigma0"] * np.exp(p["q"] * dv.lphi)) ** 2
    sf2_single = np.where(fpos[inv] < 0, p["sigma_f"] ** 2, 0.0)
    order = np.lexsort((np.arange(dv.n), dv.t))
    Sig0 = 0.5 * (Sig0 + Sig0.T)
    return dict(mu0=mu0, Sig0=Sig0, A=A[order], sig2=sig2[order], sf2_single=sf2_single[order], order=order, D=D)


# ---------------------------------------------------------------- helpers

def _lse(v, axis=None):
    m = np.max(v, axis=axis, keepdims=True)
    out = m + np.log(np.exp(v - m).sum(axis=axis, keepdims=True))
    return np.squeeze(out, axis=axis) if axis is not None else float(out)


U_LO, U_HI = -30.0, 5.0


def precision_measure(nu, n=200):
    """Discrete measure (lam_k, log q_k) of Gamma(shape nu/2, rate nu/2): uniform grid in log(lam) on [U_LO, U_HI],
    trapezoid weights of the density times the Jacobian lam, total mass 1."""
    a = nu / 2.0
    u = np.linspace(U_LO, U_HI, n)
    lw = a * math.log(a) - gammaln(a) + a * u - a * np.exp(u)
    w = np.full(n, u[1] - u[0])
    w[[0, -1]] *= 0.5
    lq = lw + np.log(w)
    m = lq.max()
    return np.exp(u), lq - (m + math.log(np.exp(lq - m).sum()))


def _kalman(mu, Sig, a, obs, r):
    """Rank-one update of every particle for observation obs = a.z + noise(var r). Vectorised over particles."""
    Sa = Sig @ a
    c = Sa @ a + r
    mu = mu + Sa * ((obs - mu @ a) / c)[:, None]
    Sig = Sig - np.einsum("ni,nj->nij", Sa, Sa) / c[:, None, None]
    return mu, Sig


def _systematic(W, rng):
    N = len(W)
    u = (rng.uniform() + np.arange(N)) / N
    return np.minimum(np.searchsorted(np.cumsum(W), u), N - 1)


def images(g, mu, sd, tol=P.TAIL_TOL, budget=P.IMAGE_BUDGET):
    """THE preimage routine (score, proposal and rejuvenation): retained preimages x of gamma (lattices g + L k and
    180 - g + L k), their log weights log N(x; mu, sd^2), log S = log sum and the certified ratio T/S of the omitted to
    the retained discrete density (per side and lattice sum_j f(d + jL) <= f(d) + survival(d/sd)/L). Images are added
    symmetrically around the one nearest to mu until T/S <= tol; budget exhausted -> error."""
    if not (-90.0 < g < 90.0 and sd > 0 and math.isfinite(mu)):
        raise ValueError("folded density: gamma in (-90, 90), finite mean and positive sd required")
    lnorm = -0.5 * LOG2PI - math.log(sd)
    L = P.L_PERIOD
    xs, lws, bounds = [], [], []
    for base in (g, 180.0 - g):
        k0 = round((mu - base) / L)
        K = 0
        while True:
            x = base + L * np.arange(k0 - K, k0 + K + 1)
            lw = lnorm - 0.5 * ((x - mu) / sd) ** 2
            b = []
            for kk in (k0 - K - 1, k0 + K + 1):
                dist = abs(base + L * kk - mu)
                b.append(np.logaddexp(lnorm - 0.5 * (dist / sd) ** 2, log_ndtr(-dist / sd) - math.log(L)))
            S_, T_ = _lse(lw), _lse(np.array(b))
            if T_ - S_ <= math.log(tol):
                break
            if 2 * K + 1 >= budget:
                raise RuntimeError("folded density: image budget exhausted before the tail bound")
            K = 2 * K + 1
        xs.append(x)
        lws.append(lw)
        bounds.append(T_)
    x, lw = np.concatenate(xs), np.concatenate(lws)
    ls = _lse(lw)
    return x, lw, ls, float(math.exp(_lse(np.array(bounds)) - ls))


def _draw_image(x, lw, ls, u):
    c = np.cumsum(np.exp(lw - ls))
    return x[min(int((c < u).sum()), len(x) - 1)]


# ---------------------------------------------------------------- SMC

def smc_block(st, y_block, kind="L1", n_particles=1000, rng=None, nu=4.0, n_quad=200, ess_frac=0.5, n_rejuv=1):
    """Sequential estimate of log p(y_block | training, psi). y_block in the ORIGINAL block order (st['order'] is
    applied here). Returns dict(score, n_resample, ess_min, max_tail_ratio, n_particles)."""
    y = np.asarray(y_block, float)[st["order"]]
    nb = len(y)
    N = 1 if kind == "L1" else n_particles
    mu = np.repeat(st["mu0"][None], N, axis=0)
    Sig = np.repeat(st["Sig0"][None], N, axis=0)
    logW = np.full(N, -math.log(N))
    aux = np.zeros((N, nb))
    total, n_res, ess_min, tmax = 0.0, 0, float(N), 0.0
    scale = (nu - 2.0) / nu
    if kind == "L2":
        lam_n, lq_n = precision_measure(nu, n_quad)
    for j in range(nb):
        a = st["A"][j]
        pm = mu @ a
        c = np.einsum("nij,i,j->n", Sig, a, a)
        if kind == "L1":
            r = st["sig2"][j] + st["sf2_single"][j]
            lp = -0.5 * (LOG2PI + np.log(c + r) + (y[j] - pm) ** 2 / (c + r))
            obs, rr = np.full(N, y[j]), np.full(N, r)
        elif kind == "L2":
            v = (c + st["sf2_single"][j])[:, None] + st["sig2"][j] * scale / lam_n[None, :]
            lk = lq_n[None, :] - 0.5 * (LOG2PI + np.log(v) + (y[j] - pm)[:, None] ** 2 / v)
            lp = _lse(lk, axis=1)
            pk = np.exp(lk - lp[:, None])
            kk = (np.cumsum(pk, axis=1) < rng.uniform(size=N)[:, None]).sum(axis=1)
            kk = np.minimum(kk, n_quad - 1)
            aux[:, j] = kk
            obs, rr = np.full(N, y[j]), st["sf2_single"][j] + st["sig2"][j] * scale / lam_n[kk]
        elif kind == "L3":
            r = st["sig2"][j] + st["sf2_single"][j]
            lp, obs = np.empty(N), np.empty(N)
            for i in range(N):
                xs, lw, ls, ts = images(y[j], pm[i], math.sqrt(c[i] + r))
                lp[i], tmax = ls, max(tmax, ts)
                obs[i] = _draw_image(xs, lw, ls, rng.uniform())
            aux[:, j] = obs
            rr = np.full(N, r)
        else:
            raise ValueError(kind)
        total += _lse(logW + lp)
        logW = logW + lp
        logW -= _lse(logW)
        mu, Sig = _kalman(mu, Sig, a, obs, rr)
        W = np.exp(logW)
        ess = 1.0 / (W * W).sum()
        ess_min = min(ess_min, ess)
        if kind != "L1" and ess < ess_frac * N and j < nb - 1:
            idx = _systematic(W, rng)
            aux, logW = aux[idx], np.full(N, -math.log(N))
            n_res += 1
            for _ in range(n_rejuv):
                aux, tr = _rejuvenate(st, y, aux, j, kind, rng, nu, lam_n if kind == "L2" else None, lq_n if kind == "L2" else None)
                tmax = max(tmax, tr)
            mu, Sig = _replay(st, y, aux, j, kind, nu, lam_n if kind == "L2" else None)
    return dict(score=float(total), n_resample=n_res, ess_min=float(ess_min), max_tail_ratio=float(tmax), n_particles=N,
                n_quad=n_quad if kind == "L2" else 0)


def _obs_noise(st, y, aux, k, kind, nu, lam_n):
    N = aux.shape[0]
    if kind == "L2":
        return np.full(N, y[k]), st["sf2_single"][k] + st["sig2"][k] * (nu - 2) / nu / lam_n[aux[:, k].astype(int)]
    if kind == "L3":
        return aux[:, k], np.full(N, st["sig2"][k] + st["sf2_single"][k])
    return np.full(N, y[k]), np.full(N, st["sig2"][k] + st["sf2_single"][k])


def _replay(st, y, aux, j, kind, nu, lam_n):
    """Posterior of z given the prefix 0..j and each particle's auxiliaries (Kalman from the prior)."""
    N = aux.shape[0]
    mu = np.repeat(st["mu0"][None], N, axis=0)
    Sig = np.repeat(st["Sig0"][None], N, axis=0)
    for k in range(j + 1):
        obs, rr = _obs_noise(st, y, aux, k, kind, nu, lam_n)
        mu, Sig = _kalman(mu, Sig, st["A"][k], obs, rr)
    return mu, Sig


def _rejuvenate(st, y, aux, j, kind, rng, nu, lam_n, lq_n):
    """Data-augmentation Gibbs on the prefix: z | auxiliaries (Gaussian), then each auxiliary | z."""
    N = aux.shape[0]
    mu, Sig = _replay(st, y, aux, j, kind, nu, lam_n)
    Sig = 0.5 * (Sig + np.transpose(Sig, (0, 2, 1)))
    L = np.linalg.cholesky(Sig + 1e-12 * np.eye(st["D"]) * np.trace(Sig, axis1=1, axis2=2)[:, None, None] / st["D"])
    z = mu + np.einsum("nij,nj->ni", L, rng.standard_normal(mu.shape))
    m = z @ st["A"][:j + 1].T                                   # (N, j+1) shared means of the prefix records
    out = aux.copy()
    tmax = 0.0
    for k in range(j + 1):
        if kind == "L2":
            s2 = st["sig2"][k] * (nu - 2) / nu
            sf2 = st["sf2_single"][k]
            lam = lam_n[aux[:, k].astype(int)]
            e0 = y[k] - m[:, k]
            if sf2 > 0:                                         # singleton family effect b_k | z, lam_k
                prec = 1.0 / sf2 + lam / s2
                b = (e0 * lam / s2) / prec + rng.standard_normal(N) / np.sqrt(prec)
            else:
                b = 0.0
            e = e0 - b
            lk = lq_n[None, :] - 0.5 * (np.log(s2 / lam_n)[None, :] + e[:, None] ** 2 * lam_n[None, :] / s2)
            pk = np.exp(lk - _lse(lk, axis=1)[:, None])
            out[:, k] = np.minimum((np.cumsum(pk, axis=1) < rng.uniform(size=N)[:, None]).sum(axis=1), len(lam_n) - 1)
        elif kind == "L3":
            sd = math.sqrt(st["sig2"][k] + st["sf2_single"][k])
            for i in range(N):
                xs, lw, ls, ts = images(y[k], m[i, k], sd)
                tmax = max(tmax, ts)
                out[i, k] = _draw_image(xs, lw, ls, rng.uniform())
    return out, tmax
