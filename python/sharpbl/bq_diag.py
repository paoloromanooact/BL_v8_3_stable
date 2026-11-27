"""BQ-HMI chain diagnostics (draft rev. 4, NOT frozen): rank-normalised split R-hat (bulk and folded) and bulk / tail
effective sample sizes, after Vehtari, Gelman, Simpson, Carpenter & Buerkner (2021, Bayesian Analysis 16, 667), with the
conventions of Stan and ArviZ (split halves keep the first and the last n//2 draws; ranks with average ties; normal
scores (r - 3/8) / (S + 1/4); Geyer's initial monotone sequence; tau floored at 1 / log10(S)).

Gate proposed by Codex (review of f17d230, §1.2), to be frozen with the protocol: at least MIN_CHAINS = 4 ORIGINAL
chains (Vehtari et al. 2021 recommend four by default; the split halves do not count), R-hat <= 1.01 and bulk and tail
ESS >= 400 over all chains, for every monitored quantity. A non-evaluable R-hat component (bulk or folded) makes R-hat
NaN with status rhat_not_evaluable: never the finite maximum of the other one. These are necessary checks, not a proof of convergence or of
an exploration of every mode / branch.

Only numpy/scipy. Input: array (n_chains, n_draws) of one scalar quantity, post warm-up, chain boundaries preserved.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm, rankdata

RHAT_MAX, ESS_MIN, MIN_CHAINS = 1.01, 400.0, 4


def _check(chains):
    c = np.asarray(chains, float)
    if c.ndim != 2 or c.shape[0] < 1 or c.shape[1] < 4:
        raise ValueError("chains must be (n_chains >= 1, n_draws >= 4)")
    if not np.isfinite(c).all():
        raise ValueError("non-finite draws")
    return c


def split_chains(c):
    """Each chain into its first and last n//2 draws (the middle draw of an odd chain is dropped)."""
    h = c.shape[1] // 2
    return np.concatenate([c[:, :h], c[:, -h:]], axis=0)


def z_scale(c):
    """Normal scores of the pooled ranks (average ties)."""
    r = rankdata(c, method="average").reshape(c.shape)
    return norm.ppf((r - 0.375) / (c.size + 0.25))


def rhat_classic(c):
    """Gelman-Rubin potential scale reduction of already split chains."""
    n = c.shape[1]
    w = c.var(axis=1, ddof=1).mean()
    b = n * c.mean(axis=1).var(ddof=1)
    return float(math.sqrt((b / w + n - 1) / n)) if w > 0 else np.nan


def autocov(x):
    """Biased autocovariance (divide by n) of each row at every lag, by FFT with zero padding."""
    x = np.asarray(x, float)
    n = x.shape[-1]
    xc = x - x.mean(axis=-1, keepdims=True)
    m = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(xc, n=m, axis=-1)
    return np.fft.irfft(f * np.conj(f), n=m, axis=-1)[..., :n] / n


def ess_of(c):
    """ESS of chains c (n_chains, n) for their mean: combined autocorrelation (Vehtari 2021 eq. 10), Geyer's initial
    positive and monotone sequences, tau >= 1 / log10(S)."""
    m, n = c.shape
    acov = autocov(c)
    chain_var = acov[:, 0] * n / (n - 1)
    mean_var = chain_var.mean()
    var_plus = mean_var * (n - 1) / n + (c.mean(axis=1).var(ddof=1) if m > 1 else 0.0)
    if not var_plus > 0:
        return np.nan
    rho = np.zeros(n)
    rho[0] = 1.0
    even, odd = 1.0, 1.0 - (mean_var - acov[:, 1].mean()) / var_plus
    rho[1] = odd
    t = 1
    while t < n - 3 and even + odd > 0:
        even = 1.0 - (mean_var - acov[:, t + 1].mean()) / var_plus
        odd = 1.0 - (mean_var - acov[:, t + 2].mean()) / var_plus
        if even + odd >= 0:
            rho[t + 1], rho[t + 2] = even, odd
        t += 2
    max_t = t - 2
    if even > 0:
        rho[max_t + 1] = even
    t = 1
    while t <= max_t - 2:                                   # initial monotone sequence
        if rho[t + 1] + rho[t + 2] > rho[t - 1] + rho[t]:
            rho[t + 1] = rho[t + 2] = 0.5 * (rho[t - 1] + rho[t])
        t += 2
    s = m * n
    tau = -1.0 + 2.0 * rho[:max_t + 1].sum() + rho[max_t + 1:max_t + 2].sum()
    tau = max(tau, 1.0 / math.log10(s))
    return float(s / tau)


def rhat(chains):
    """(R-hat, bulk, folded): rank-normalised split R-hat of the draws and of |draws - median|; R-hat = max."""
    c = split_chains(_check(chains))
    bulk = rhat_classic(z_scale(c))
    fd = np.abs(c - np.median(c))
    folded = rhat_classic(z_scale(fd)) if np.ptp(fd) > 0 else np.nan
    both = math.isfinite(bulk) and math.isfinite(folded)
    return (max(bulk, folded) if both else np.nan), bulk, folded


def ess_bulk(chains):
    return ess_of(z_scale(split_chains(_check(chains))))


def ess_tail(chains):
    """Minimum of the ESS of the indicators I(x <= q05) and I(x <= q95) on split chains."""
    c = split_chains(_check(chains))
    out = []
    for q in (0.05, 0.95):
        ind = (c <= np.quantile(c, q)).astype(float)
        out.append(ess_of(ind) if 0 < ind.mean() < 1 else np.nan)
    return float(min(out)) if np.isfinite(out).all() else np.nan


def diagnose(chains, min_chains=MIN_CHAINS):
    """Diagnostics of one scalar quantity and the proposed gate. Status: 'constant'; 'too_few_chains' (fewer original
    chains than min_chains: values still reported, gate fails); 'rhat_not_evaluable' (a component is NaN); else 'ok'."""
    c = _check(chains)
    base = dict(n_chains=int(c.shape[0]), n_draws=int(c.shape[1]))
    if np.ptp(c) == 0:
        return dict(base, rhat=np.nan, rhat_bulk=np.nan, rhat_folded=np.nan, ess_bulk=np.nan, ess_tail=np.nan, status="constant", passes=False)
    r, rb, rf = rhat(c)
    eb, et = ess_bulk(c), ess_tail(c)
    status = "too_few_chains" if c.shape[0] < min_chains else ("rhat_not_evaluable" if not math.isfinite(r) else "ok")
    good = bool(status == "ok" and np.isfinite([r, eb, et]).all() and r <= RHAT_MAX and eb >= ESS_MIN and et >= ESS_MIN)
    return dict(base, rhat=r, rhat_bulk=rb, rhat_folded=rf, ess_bulk=eb, ess_tail=et, status=status, passes=good)
