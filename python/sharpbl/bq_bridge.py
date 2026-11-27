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


def posterior_mean_variance(values, chain_sizes):
    """Variance of the pooled mean from within-chain batch means.

    Independent chains contribute n_c * var_c * tau_c to the variance of the
    sum. Preserve the bridge's iid lower bound on the variance estimate.
    """
    within_chain = []
    start = 0
    for size in chain_sizes:
        chain = values[start:start + size]
        start += size
        if size > 1:
            within_chain.append(size * float(chain.var(ddof=1)) * batch_tau(chain))
    n_draws = len(values)
    iid_variance = float(values.var(ddof=1)) / n_draws
    return max(iid_variance, math.fsum(within_chain) / n_draws ** 2)


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


def bridge_log_evidence(logq, chains, rng, n_prop=None, tol=1e-10, max_iter=1000, proposal=None):
    """logq: log unnormalised posterior on the sampling coordinates; chains: list of (n, dim) arrays of posterior
    draws in chain order. Returns dict(log_evidence, se_log, iterations, converged, n1, n1_eff, n2) and, for paired
    errors (paired_difference_se), the linearised terms: rel_post = f2 / mean(f2) - 1 on the estimation draws, their
    positions est_positions = [(chain, index in chain)], chain_lengths, rel_var_prop = Var(f1) / (N2 mean(f1)^2) (the
    independent proposal part of RE^2) and rel_var_post (the posterior part, chain boundaries kept).
    proposal = (mu, cov) replaces the normal fitted on the first halves (used only to measure the effect of that
    adaptation; the first halves are then still left out of the estimator)."""
    chains = list(chains)
    chain_sizes = [len(chain) // 2 for chain in chains]
    fit, est = split_chains(chains)
    dim = fit.shape[1]
    if proposal is None:
        mu = fit.mean(0)
        cov = np.atleast_2d(np.cov(fit.T)) + 1e-12 * np.eye(dim)
    else:
        mu, cov = np.asarray(proposal[0], float), np.atleast_2d(np.asarray(proposal[1], float))
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
    scaled_ratios = np.exp(l1 - l1.max())
    ratio_mean_variance = posterior_mean_variance(scaled_ratios, chain_sizes)
    iid_ratio_variance = float(scaled_ratios.var(ddof=1)) / n1
    n1e = n1 * iid_ratio_variance / ratio_mean_variance if ratio_mean_variance > 0 else float(n1)
    ls1, ls2 = math.log(n1e / (n1e + n2)), math.log(n2 / (n1e + n2))

    def h(x):                                                   # one step of the iteration on log r
        return (logsumexp(l2 - np.logaddexp(ls1 + l2, ls2 + x)) - math.log(n2)
                - logsumexp(-np.logaddexp(ls1 + l1, ls2 + x)) + math.log(n1))
    lr, conv = float(np.median(l1)), False
    for it in range(max_iter):
        new = h(lr)
        if abs(new - lr) < tol:
            lr, conv = new, True
            break
        lr = new
    f1 = np.exp(l2 - np.logaddexp(ls1 + l2, ls2 + lr))
    f2 = np.exp(lr - np.logaddexp(ls1 + l1, ls2 + lr))      # scaled by r: the relative variance is unchanged
    eps = 1e-5
    slope = (h(lr + eps) - h(lr - eps)) / (2 * eps)            # h'(log r) at the fixed point
    rv_prop = f1.var(ddof=1) / (n2 * f1.mean() ** 2)
    rv_post = posterior_mean_variance(f2, chain_sizes) / f2.mean() ** 2
    re2 = rv_prop + rv_post
    pos = [(c, len(chains[c]) // 2 + k) for c, h in enumerate(chain_sizes) for k in range(h)]
    return dict(log_evidence=lr, se_log=math.sqrt(re2), iterations=it + 1, converged=conv, n1=n1, n1_eff=n1e, n2=n2,
                rel_post=f2 / f2.mean() - 1.0, est_positions=pos, chain_lengths=[len(c) for c in chains], rel_var_prop=rv_prop,
                rel_var_post=rv_post, fp_slope=float(slope), fp_factor=float(1.0 / (1.0 - slope)))


def savage_dickey_terms(cond, beta_sd):
    """Savage-Dickey log BF_0Q from Rao-Blackwellised ordinates (as bq_core.savage_dickey_log_bf0q) and the linearised
    per-draw terms rel = o / mean(o) - 1 for paired errors."""
    cond = np.asarray(cond, float)
    o = np.exp(-0.5 * cond[:, 0] ** 2 / cond[:, 1]) / np.sqrt(2 * math.pi * cond[:, 1])
    return math.log(o.mean()) + math.log(math.sqrt(2 * math.pi) * beta_sd), o / o.mean() - 1.0


def paired_difference_se(ev_m0, ev_mq, sd_rel, sd_positions, fixed_point=False):
    """MC SE of D = (log Z_M0 - log Z_MQ) - log BF_SD when the bridge of MQ and Savage-Dickey use the same MQ chains.

    Delta method on both estimators: d log Z ~ mean_j (f1_j / mean f1 - 1) - mean_i (f2_i / mean f2 - 1) (proposal
    draws j independent, posterior estimation draws i) and d log BF_SD ~ mean_s (o_s / mean o - 1). The two posterior
    parts are put on one per-iteration series per MQ chain, g = rel_post / N1 at the estimation draws minus
    sd_rel / N_SD at the Savage-Dickey draws, and Var(sum of g) is taken from within-chain batch means (chain boundaries
    kept), so their covariance enters. Added independently: the proposal part of the MQ bridge and the whole RE^2 of the
    M0 bridge (its chains are separate). The effect of fitting the proposal on the same chains is NOT in the formula.
    With fixed_point=True the MQ terms are multiplied by its fp_factor = 1 / (1 - h'(log r)) and the M0 variance by
    fp_factor^2 (full delta method of the fixed point log r = h(log r), where the RE formula holds the weights at r).
    Malformed inputs are refused (ValueError): lengths that differ, duplicated positions, positions outside the chains.
    Returns dict(se, se_unpaired_naive, var_post_paired, var_prop_mq, var_m0)."""
    lengths = [int(n) for n in ev_mq["chain_lengths"]]
    for lab, rel, P in (("Savage-Dickey", sd_rel, sd_positions), ("bridge", ev_mq["rel_post"], ev_mq["est_positions"])):
        P = [(int(c), int(k)) for c, k in P]
        if len(rel) != len(P):
            raise ValueError(f"{lab}: {len(rel)} terms for {len(P)} positions")
        if len(set(P)) != len(P):
            raise ValueError(f"{lab}: duplicated positions")
        if any(not (0 <= c < len(lengths) and 0 <= k < lengths[c]) for c, k in P):
            raise ValueError(f"{lab}: position outside the chains")
    g = [np.zeros(n) for n in lengths]
    n1 = len(ev_mq["rel_post"])
    fq = ev_mq["fp_factor"] if fixed_point else 1.0
    f0 = ev_m0["fp_factor"] if fixed_point else 1.0
    for (c, k), v in zip(ev_mq["est_positions"], ev_mq["rel_post"]):
        g[c][k] += fq * v / n1
    ns = len(sd_rel)
    for (c, k), v in zip(sd_positions, sd_rel):
        g[c][k] -= v / ns
    allg = np.concatenate(g)
    var_post = posterior_mean_variance(allg, lengths) * len(allg) ** 2
    var_prop, var_m0 = fq ** 2 * ev_mq["rel_var_prop"], f0 ** 2 * ev_m0["se_log"] ** 2
    naive = var_m0 + ev_mq["se_log"] ** 2 + float(np.var(sd_rel, ddof=1)) / ns
    return dict(se=math.sqrt(var_post + var_prop + var_m0), se_unpaired_naive=math.sqrt(naive), var_post_paired=var_post,
                var_prop_mq=var_prop, var_m0=var_m0)


def chain_positions(chains, step=1):
    """(chain, index) of every `step`-th draw of each chain, in chain order (the draws used for Savage-Dickey)."""
    return [(c, k) for c, ch in enumerate(chains) for k in range(0, len(ch), step)]
