"""BQ-HMI core (draft rev. 4, not frozen): Gaussian working likelihood L1 with shared temporal and family effects.

Model (docs/PROTOCOL_BQ_HMI_DRAFT.md §2-§4), in degrees:
    gamma_i = sum_(c,h) k_(c,h) [cell_i = (c,h)] s_i  (+ beta a_i s_i in MQ)
              + u_(t_i, h_i)  (+ v_(t_i, h_i) s_i in the v sensitivity)  + b_(f_i) + eps_i,
    eps_i ~ N(0, sigma_i^2), sigma_i = sigma0 exp(q log10(Phi_i / 1e21 Mx)).
- u (and v): stationary bivariate AR(1) on EVERY integer CR of the span, Cov = sd^2 phi^|t-t'| kappa^[h != h'];
  phi = tanh(z_phi), kappa = tanh(z_kappa). CRs without records keep their latent state (no compressed calendar).
- b_f ~ N(0, sigma_f^2): families with one member enter the diagonal (exact in L1), replicated ones are latents.
- Coefficients k (and beta) have proper Gaussian priors and are integrated analytically.

Computation: y ~ N(0, D + L K L^T) with latents (x = u[,v] by CR, f, theta). Woodbury, with the family latents
eliminated exactly (diagonal Schur complement), the AR(1) latents in a banded Cholesky, and theta in a small dense
Schur complement. The posterior of theta given psi is Gaussian; beta's conditional gives the Savage-Dickey ordinate.

Prior (rev. 4 proposals): k ~ N(0, 40^2); beta ~ N(0, tau^2), tau = 10; sigma0 ~ HN(30); sigma_x ~ HN(10);
sigma_f ~ HN(5); q ~ N(0, 1); z_phi, z_kappa ~ N(0, 1); sigma_v ~ HN(20) (or 5); z_phi_v, z_kappa_v ~ N(0, 1).
Sampling coordinates: log of every scale (Jacobian included), q and the z's as they are.

Only numpy/scipy. No observed response is read here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.linalg import cho_factor, cho_solve, cholesky_banded, cho_solve_banded, solve_banded, solve_triangular

LOG2PI = math.log(2.0 * math.pi)
PRIOR = dict(k_sd=40.0, beta_sd=10.0, sigma0_hn=30.0, sigma_x_hn=10.0, sigma_f_hn=5.0, q_sd=1.0, sigma_v_hn=20.0)


@dataclass
class Design:
    """Design-only arrays (no response): CR index from 0 on the full calendar, hemisphere 0/1, s = sin|lat|,
    a = activity - 1, log10(Phi/1e21), cycle-hemisphere cell index, family label."""
    t: np.ndarray
    h: np.ndarray
    s: np.ndarray
    a: np.ndarray
    lphi: np.ndarray
    cell: np.ndarray
    fam: np.ndarray
    n_t: int
    n_cell: int
    with_v: bool = False
    with_beta: bool = True
    prior: dict = field(default_factory=lambda: dict(PRIOR))

    def __post_init__(self):
        self.n = len(self.t)
        self.p = 4 if self.with_v else 2                       # latents per CR: (u_N, u_S[, v_N, v_S])
        self.nx = self.p * self.n_t
        self.iu = self.t * self.p + self.h                     # index of u_(t,h)
        self.iv = self.t * self.p + 2 + self.h if self.with_v else None
        X = np.zeros((self.n, self.n_cell + (1 if self.with_beta else 0)))
        X[np.arange(self.n), self.cell] = self.s
        if self.with_beta:
            X[:, -1] = self.a * self.s
        self.X = X
        self.m = X.shape[1]
        self.vprior = np.r_[np.full(self.n_cell, self.prior["k_sd"] ** 2), [self.prior["beta_sd"] ** 2] if self.with_beta else []]
        labels, inv, counts = np.unique(self.fam, return_inverse=True, return_counts=True)
        rep = counts[inv] >= 2
        self.single = ~rep
        rep_labels = np.unique(inv[rep])
        remap = -np.ones(len(labels), int)
        remap[rep_labels] = np.arange(len(rep_labels))
        self.fidx = np.where(rep, remap[inv], -1)              # replicated-family index or -1
        self.n_f = len(rep_labels)
        # family member pairs (same replicated family, ordered, including i == j) for the Schur update
        members = [np.flatnonzero(self.fidx == f) for f in range(self.n_f)]
        self.members = members
        pi = [i for mem in members for i in mem for _ in mem]
        pj = [j for mem in members for _ in mem for j in mem]
        self.pair_i, self.pair_j = np.array(pi, int), np.array(pj, int)
        self.pair_f = self.fidx[self.pair_i] if len(pi) else np.array([], int)
        # bandwidth of the AR(1)-latent block after the family elimination
        span = 0
        for mem in members:
            span = max(span, int(self.t[mem].max() - self.t[mem].min()))
        self.bw = self.p * (max(span, 1) + 1) - 1

    def names(self):
        nm = ["log_sigma0", "q", "log_sigma_x", "z_phi", "z_kappa", "log_sigma_f"]
        return nm + (["log_sigma_v", "z_phi_v", "z_kappa_v"] if self.with_v else [])


def unpack(d: Design, x):
    p = dict(sigma0=math.exp(x[0]), q=x[1], sigma_x=math.exp(x[2]), phi=math.tanh(x[3]), kappa=math.tanh(x[4]),
             sigma_f=math.exp(x[5]))
    if d.with_v:
        p.update(sigma_v=math.exp(x[6]), phi_v=math.tanh(x[7]), kappa_v=math.tanh(x[8]))
    return p


def log_prior(d: Design, x):
    """Log prior density on the sampling coordinates (Jacobians of the log-scales included)."""
    pr = d.prior

    def hn_log(logsig, scale):                                  # half-normal on sigma, coordinate log sigma
        sig = math.exp(logsig)
        return math.log(2.0) - 0.5 * LOG2PI - math.log(scale) - 0.5 * (sig / scale) ** 2 + logsig

    def n_log(v, sd):
        return -0.5 * LOG2PI - math.log(sd) - 0.5 * (v / sd) ** 2
    lp = hn_log(x[0], pr["sigma0_hn"]) + n_log(x[1], pr["q_sd"]) + hn_log(x[2], pr["sigma_x_hn"]) + n_log(x[3], 1.0) \
        + n_log(x[4], 1.0) + hn_log(x[5], pr["sigma_f_hn"])
    if d.with_v:
        lp += hn_log(x[6], pr["sigma_v_hn"]) + n_log(x[7], 1.0) + n_log(x[8], 1.0)
    return lp


def _ar1_precision(n_t, sd, phi, kappa):
    """Precision and log-determinant of the covariance sd^2 T(phi) (x) H(kappa), index t*2 + h."""
    om = 1.0 - phi * phi
    Ti = np.zeros((n_t, n_t))
    idx = np.arange(n_t)
    Ti[idx, idx] = 1.0 + phi * phi
    Ti[0, 0] = Ti[-1, -1] = 1.0
    Ti[idx[:-1], idx[1:]] = Ti[idx[1:], idx[:-1]] = -phi
    Ti /= om
    ok = 1.0 - kappa * kappa
    Hi = np.array([[1.0, -kappa], [-kappa, 1.0]]) / ok
    logdet = 2 * n_t * math.log(sd * sd) + 2 * (n_t - 1) * math.log(om) + n_t * math.log(ok)
    return np.kron(Ti, Hi) / (sd * sd), logdet


def _prec_x(d: Design, p):
    Pu, ld = _ar1_precision(d.n_t, p["sigma_x"], p["phi"], p["kappa"])
    if not d.with_v:
        return Pu, ld
    Pv, ldv = _ar1_precision(d.n_t, p["sigma_v"], p["phi_v"], p["kappa_v"])
    P = np.zeros((d.nx, d.nx))
    t2 = np.repeat(np.arange(d.n_t), 2) * 4 + np.tile([0, 1], d.n_t)
    P[np.ix_(t2, t2)] = Pu
    P[np.ix_(t2 + 2, t2 + 2)] = Pv
    return P, ld + ldv


def _band(A, bw):
    """Upper banded storage for cholesky_banded."""
    n = len(A)
    ab = np.zeros((bw + 1, n))
    for k in range(bw + 1):
        ab[bw - k, k:] = np.diagonal(A, k)
    return ab


def _system(d: Design, x, y, lam=None, scale=1.0):
    """Linear system of the latents (x states, replicated families eliminated, theta) for parameters x.
    lam: per-record precision multipliers of the individual residual (L2), scale: (nu-2)/nu for L2."""
    p = unpack(d, x)
    sig2 = (p["sigma0"] * np.exp(p["q"] * d.lphi)) ** 2 * scale
    if lam is not None:
        sig2 = sig2 / lam
    D = sig2 + np.where(d.single, p["sigma_f"] ** 2, 0.0)
    w = 1.0 / D
    Axx, ldK = _prec_x(d, p)
    np.add.at(Axx, (d.iu, d.iu), w)
    if d.with_v:
        np.add.at(Axx, (d.iv, d.iv), w * d.s ** 2)
        np.add.at(Axx, (d.iu, d.iv), w * d.s)
        np.add.at(Axx, (d.iv, d.iu), w * d.s)
    Axt = np.zeros((d.nx, d.m))
    Xw = d.X * w[:, None]
    np.add.at(Axt, d.iu, Xw)
    if d.with_v:
        np.add.at(Axt, d.iv, Xw * d.s[:, None])
    Att = np.diag(1.0 / d.vprior) + d.X.T @ Xw
    bx = np.zeros(d.nx)
    np.add.at(bx, d.iu, w * y)
    if d.with_v:
        np.add.at(bx, d.iv, w * y * d.s)
    bt = d.X.T @ (w * y)
    sy = dict(p=p, sig2=sig2, D=D, w=w, ldK=ldK, ldf=0.0, quad_f=0.0, a=None, bf=None, gx=None, Gt=None)
    if d.n_f:
        sf2 = p["sigma_f"] ** 2
        rf = d.fidx >= 0
        a = np.full(d.n_f, 1.0 / sf2)
        np.add.at(a, d.fidx[rf], w[rf])
        bf = np.zeros(d.n_f)
        np.add.at(bf, d.fidx[rf], (w * y)[rf])
        cpair = w[d.pair_i] * w[d.pair_j] / a[d.pair_f]
        np.add.at(Axx, (d.iu[d.pair_i], d.iu[d.pair_j]), -cpair)
        if d.with_v:
            np.add.at(Axx, (d.iv[d.pair_i], d.iv[d.pair_j]), -cpair * d.s[d.pair_i] * d.s[d.pair_j])
            np.add.at(Axx, (d.iu[d.pair_i], d.iv[d.pair_j]), -cpair * d.s[d.pair_j])
            np.add.at(Axx, (d.iv[d.pair_i], d.iu[d.pair_j]), -cpair * d.s[d.pair_i])
        Gt = np.zeros((d.n_f, d.m))
        np.add.at(Gt, d.fidx[rf], Xw[rf])
        gx = np.zeros((d.nx, d.n_f))
        np.add.at(gx, (d.iu[rf], d.fidx[rf]), w[rf])
        if d.with_v:
            np.add.at(gx, (d.iv[rf], d.fidx[rf]), w[rf] * d.s[rf])
        Axt -= (gx / a) @ Gt
        Att -= (Gt.T / a) @ Gt
        bx -= gx @ (bf / a)
        bt -= Gt.T @ (bf / a)
        sy.update(a=a, bf=bf, gx=gx, Gt=Gt, ldf=d.n_f * math.log(sf2) + float(np.log(a).sum()), quad_f=float((bf * bf / a).sum()))
    cb = cholesky_banded(_band(Axx, d.bw), lower=False)
    Sx_b = cho_solve_banded((cb, False), bx)
    Sx_T = cho_solve_banded((cb, False), Axt)
    S = Att - Axt.T @ Sx_T
    r = bt - Axt.T @ Sx_b
    cs = cho_factor(S, lower=True)
    sy.update(cb=cb, Axt=Axt, bx=bx, Sx_b=Sx_b, Sx_T=Sx_T, cs=cs, r=r, st=cho_solve(cs, r))
    return sy


def loglik(d: Design, x, y, return_post=False, lam=None, scale=1.0):
    """log N(y; 0, D + L K L^T) with the coefficients integrated; optionally the Gaussian conditional of theta."""
    sy = _system(d, x, y, lam, scale)
    ldx = 2.0 * float(np.log(sy["cb"][-1]).sum())
    ldt = 2.0 * float(np.log(np.diag(sy["cs"][0])).sum())
    quad = float(y @ (sy["w"] * y)) - sy["quad_f"] - float(sy["bx"] @ sy["Sx_b"]) - float(sy["r"] @ sy["st"])
    logdet = float(np.log(sy["D"]).sum()) + sy["ldK"] + float(np.log(d.vprior).sum()) + sy["ldf"] + ldx + ldt
    ll = -0.5 * (d.n * LOG2PI + logdet + quad)
    if not return_post:
        return ll
    return ll, sy["st"], cho_solve(sy["cs"], np.eye(d.m))


def draw_latents(d: Design, x, y, rng, lam=None, scale=1.0):
    """One joint Gaussian draw of all latents given psi (and lam): theta, then the AR(1) states given theta, then the
    replicated families given both, then the singleton family effects. Returns (theta, states, f, b_record, mean_i)
    with mean_i = X theta + Z states + b (the full shared part of record i, without the individual residual)."""
    sy = _system(d, x, y, lam, scale)
    L = sy["cs"][0]
    theta = sy["st"] + solve_triangular(L, rng.standard_normal(d.m), lower=True, trans="T")
    xs = cho_solve_banded((sy["cb"], False), sy["bx"] - sy["Axt"] @ theta) \
        + solve_banded((0, d.bw), sy["cb"], rng.standard_normal(d.nx))
    zx = xs[d.iu] + (xs[d.iv] * d.s if d.with_v else 0.0)
    shared = d.X @ theta + zx
    b = np.zeros(d.n)
    f = np.zeros(d.n_f)
    w = sy["w"]
    if d.n_f:
        rf = d.fidx >= 0
        lin = np.zeros(d.n_f)
        np.add.at(lin, d.fidx[rf], (w * (y - shared))[rf])
        f = lin / sy["a"] + rng.standard_normal(d.n_f) / np.sqrt(sy["a"])
        b[rf] = f[d.fidx[rf]]
    sg = d.single
    if sg.any():
        sf2, s2 = sy["p"]["sigma_f"] ** 2, sy["sig2"][sg]
        prec = 1.0 / sf2 + 1.0 / s2
        b[sg] = ((y - shared)[sg] / s2) / prec + rng.standard_normal(int(sg.sum())) / np.sqrt(prec)
    return theta, xs, f, b, shared + b


def log_post(d: Design, x, y):
    lp = log_prior(d, x)
    if not np.isfinite(lp):
        return -np.inf
    try:
        return lp + loglik(d, x, y)
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        return -np.inf


# ---------------------------------------------------------------- slice sampler (Neal 2003, stepping out + shrinkage)

def slice_sweep(logf, x, fx, w, rng, max_steps=50):
    """One sweep of coordinate-wise slice updates (stepping out + shrinkage). Returns (x, fx, stepping-limit hits)."""
    x = np.array(x, float)
    hits = 0
    for j in range(len(x)):
        logy = fx + math.log(rng.uniform())
        lo = x[j] - w[j] * rng.uniform()
        hi = lo + w[j]
        jl = int(math.floor(max_steps * rng.uniform()))
        jr = max_steps - 1 - jl
        xt = x.copy()
        while True:
            xt[j] = lo
            if logf(xt) <= logy:
                break
            if jl == 0:
                hits += 1
                break
            lo -= w[j]
            jl -= 1
        while True:
            xt[j] = hi
            if logf(xt) <= logy:
                break
            if jr == 0:
                hits += 1
                break
            hi += w[j]
            jr -= 1
        while True:
            xt[j] = rng.uniform(lo, hi)
            ft = logf(xt)
            if ft > logy:
                x, fx = xt.copy(), ft
                break
            if xt[j] < x[j]:
                lo = xt[j]
            else:
                hi = xt[j]
    return x, fx, hits


class Widths:
    """Warm-up-only width rule: w0 in the first half of the warm-up, 2 x SD of that half in the second half, 2 x SD
    of the second half for the saved phase (fixed kernel)."""

    def __init__(self, dim, n_warm, w0=1.0):
        self.w, self.n_warm, self.buf = np.full(dim, float(w0)), n_warm, []

    def update(self, it, x):
        if it == self.n_warm // 2 and self.buf:
            self.w = np.clip(2.0 * np.std(np.array(self.buf), axis=0), 1e-3, 10.0)
            self.buf = []
        if it == self.n_warm and self.buf:
            self.w = np.clip(2.0 * np.std(np.array(self.buf), axis=0), 1e-3, 10.0)
            self.buf = []

    def record(self, it, x):
        if it < self.n_warm:
            self.buf.append(np.array(x, float))


def slice_chain(logf, x0, n_warm, n_keep, rng, w0=1.0, max_steps=50):
    """Coordinate-wise slice sampling with the warm-up-only width rule (Widths). Returns (saved draws, saved log
    densities, final widths, count of stepping-out limits hit)."""
    x = np.array(x0, float)
    fx = logf(x)
    if not np.isfinite(fx):
        raise ValueError("initial point has zero density")
    W = Widths(len(x), n_warm, w0)
    keep, lk, hits = [], [], 0
    for it in range(n_warm + n_keep):
        W.update(it, x)
        x, fx, h = slice_sweep(logf, x, fx, W.w, rng, max_steps)
        hits += h
        W.record(it, x)
        if it >= n_warm:
            keep.append(x.copy())
            lk.append(fx)
    return np.array(keep), np.array(lk), W.w, hits


# ---------------------------------------------------------------- beta: conditional posterior and Savage-Dickey

def beta_conditionals(d: Design, draws, y):
    """Per saved draw: conditional mean and variance of beta given psi and y (last coefficient)."""
    if not d.with_beta:
        raise ValueError("design without beta")
    out = np.empty((len(draws), 2))
    for i, x in enumerate(draws):
        _, mu, cov = loglik(d, x, y, return_post=True)
        out[i] = mu[-1], cov[-1, -1]
    return out


def savage_dickey_log_bf0q(d: Design, cond):
    """log BF_0Q = log p(beta = 0 | y, MQ) - log p(beta = 0 | MQ), Rao-Blackwellised over the draws; returns the
    estimate and a naive Monte Carlo SE on the log scale (independent-draw formula; inflate by the IAT)."""
    dens = np.exp(-0.5 * cond[:, 0] ** 2 / cond[:, 1]) / np.sqrt(2 * math.pi * cond[:, 1])
    m = dens.mean()
    se = dens.std(ddof=1) / math.sqrt(len(dens)) / m
    prior0 = 1.0 / (math.sqrt(2 * math.pi) * d.prior["beta_sd"])
    return math.log(m) - math.log(prior0), se
