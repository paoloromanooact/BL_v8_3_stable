"""BQ-HMI blocked cross-validation (draft rev. 4 §6, not frozen): internal blocks of the observed period.

- 10 contiguous intervals of the full CR calendar (all integer CRs from first to last), lengths differing by at most
  one, remainder to the first intervals. Every record of a block is verification.
- Training excludes the block, `buffer` CRs on each side (11 main, 22 sensitivity) and EVERY member of a family
  present in the verification, wherever it is. Excluded records score in no block of that fold.
- Score of a block: log p(y_ver | y_train) = log of the posterior mean, over psi | y_train, of
  p(y_ver | y_train, psi), and log p(y_ver | y_train, psi) = l(train + ver; psi) - l(train; psi) exactly, with the
  coefficients and latent states integrated (same calendar, so the states of the block are interpolated from both
  sides: temporal interpolation, not a forecast of the future Sun).
- Monte Carlo error of the log-mean-exp by batch means.
Synthetic use only until the protocol is frozen.
"""
from __future__ import annotations

import math

import numpy as np

from . import bq_core as B


def cv_blocks(n_t, n_blocks=10):
    base, rem = divmod(n_t, n_blocks)
    out, lo = [], 0
    for i in range(n_blocks):
        ln = base + (1 if i < rem else 0)
        out.append((lo, lo + ln - 1))
        lo += ln
    return out


def cv_masks(d: B.Design, block, buffer):
    lo, hi = block
    ver = (d.t >= lo) & (d.t <= hi)
    near = (d.t >= lo - buffer) & (d.t <= hi + buffer)
    fam_ver = np.isin(d.fam, d.fam[ver])
    train = ~near & ~fam_ver
    return train, ver


def subset(d: B.Design, mask):
    """Same calendar, cells and flags; family structure recomputed on the subset."""
    return B.Design(t=d.t[mask], h=d.h[mask], s=d.s[mask], a=d.a[mask], lphi=d.lphi[mask], cell=d.cell[mask], fam=d.fam[mask],
                    n_t=d.n_t, n_cell=d.n_cell, with_v=d.with_v, with_beta=d.with_beta, prior=dict(d.prior))


def support(d: B.Design, train, ver):
    """Records per cycle-hemisphere cell in training and verification, activity ranges (prior-dominated cells flagged)."""
    out = dict(n_train=int(train.sum()), n_ver=int(ver.sum()))
    for c in range(d.n_cell):
        out[f"train_cell{c}"] = int((train & (d.cell == c)).sum())
        out[f"ver_cell{c}"] = int((ver & (d.cell == c)).sum())
    out["prior_dominated_cells"] = [c for c in range(d.n_cell) if out[f"ver_cell{c}"] > 0 and out[f"train_cell{c}"] == 0]
    out["a_train"] = (float(d.a[train].min()), float(d.a[train].max())) if train.any() else (np.nan, np.nan)
    out["a_ver"] = (float(d.a[ver].min()), float(d.a[ver].max())) if ver.any() else (np.nan, np.nan)
    return out


def conditional_terms(d: B.Design, train, ver, y, draws):
    """log p(y_ver | y_train, psi) for each draw (psi sampled from the training posterior)."""
    both = train | ver
    dj, dt = subset(d, both), subset(d, train)
    yj, yt = y[both], y[train]
    return np.array([B.loglik(dj, x, yj) - B.loglik(dt, x, yt) for x in draws])


def log_mean_exp(v, n_batches=20):
    """log mean exp(v) and its Monte Carlo SE by batch means (delta method on the mean of exp(v - max))."""
    v = np.asarray(v, float)
    m = v.max()
    e = np.exp(v - m)
    est = m + math.log(e.mean())
    nb = min(n_batches, len(v))
    if nb < 2:
        return est, np.nan
    bm = np.array([b.mean() for b in np.array_split(e, nb)])
    se = bm.std(ddof=1) / math.sqrt(nb) / e.mean()
    return est, se


def run_fold(d: B.Design, y, block, buffer, x0, n_warm, n_keep, rng, thin=1):
    """One fold for one model: training chain, then the block score. Returns a dict with the score, its MC SE,
    the support table and sampler diagnostics."""
    train, ver = cv_masks(d, block, buffer)
    dt = subset(d, train)
    draws, lk, w, hits = B.slice_chain(lambda z: B.log_post(dt, z, y[train]), x0, n_warm, n_keep, rng)
    terms = conditional_terms(d, train, ver, y, draws[::thin])
    score, se = log_mean_exp(terms)
    return dict(block=block, buffer=buffer, score=score, mc_se=se, n_draws=len(terms), stepping_limit_hits=hits,
                **support(d, train, ver))
