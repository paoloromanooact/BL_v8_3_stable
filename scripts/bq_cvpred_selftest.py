"""Selftest of python/sharpbl/bq_cvpred.py on synthetic designs and responses only (no observed response, no fit).

At FIXED training posterior states (psi and, for L2, the training precisions; for L3 the training latent tilts), the
Monte Carlo block score over latent draws is compared with routes that integrate differently:
 1. folded density with the adaptive bound: against a long independent sum (sigma 1 ... 1000, means incl. +-400,
    gamma up to 89.5), certified T/S <= 1e-12; integrates to one over (-90, 90); invalid inputs and an exhausted
    budget refused;
 2. L1: MC score = analytic log p(y_block | y_train, psi) = l(train + block) - l(train) (u and u+v designs, a family
    shared by two block records) within 4 MC SE;
 3. L2: MC score (latents drawn, block precisions integrated by the t density) = second route (latents integrated
    analytically with the Gaussian core, block precisions drawn from Gamma(nu/2, nu/2)) within 4 combined SE;
 4. L3: MC score (latents drawn, preimages summed) = joint enumeration of the preimage pairs of two correlated block
    records (same CR and hemisphere), each pair scored with the analytic Gaussian conditional, within 4 MC SE;
 5. score(): log-mean-exp equal to bq_cv.log_mean_exp, weights ESS and largest share on a hand example;
 6. degeneracy guard: on a 45-record L1 block (direct estimator, 4000 draws) the weights ESS falls below 100 and the
    status is score_not_established (score NaN, raw value kept), while the 7-record block of test 2 is ok.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_cvpred_selftest.py
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_cv as CV, bq_cvpred as P  # noqa: E402
from bq_core_selftest import synth_design  # noqa: E402  (synthetic designs of the core selftest)

SEED = 36_400_801
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def lme(v):
    v = np.asarray(v, float)
    m = v.max()
    return m + math.log(np.exp(v - m).mean())


def main():
    rng = np.random.default_rng(SEED)
    # 1. folded density
    worst, tsmax = 0.0, 0.0
    for sig in (1.0, 12.0, 30.0, 150.0, 400.0, 1000.0):
        for mu in (-400.0, 17.0, 400.0):
            for g in (-80.0, 10.0, 89.5):
                v, ts = P.folded_logpdf_bounded(g, mu, sig)
                k = np.arange(-60, 61)
                cand = np.r_[g + 360.0 * k, 180.0 - g + 360.0 * k]
                lw = -0.5 * math.log(2 * math.pi) - math.log(sig) - 0.5 * ((cand - mu) / sig) ** 2
                ref = lw.max() + math.log(np.exp(lw - lw.max()).sum())
                worst, tsmax = max(worst, abs(v - ref)), max(tsmax, ts)
    integ = quad(lambda g: math.exp(P.folded_logpdf_bounded(g, 37.0, 30.0)[0]), -90 + 1e-12, 90 - 1e-12, limit=200)[0]
    refused = []
    for args in ((90.0, 0.0, 10.0), (10.0, 0.0, 0.0), (10.0, float("nan"), 10.0)):
        try:
            P.folded_logpdf_bounded(*args)
            refused.append(False)
        except ValueError:
            refused.append(True)
    try:
        P.folded_logpdf_bounded(10.0, 0.0, 1e5, budget=3)
        refused.append(False)
    except RuntimeError:
        refused.append(True)
    ok("1. folded density with adaptive bound = long sum (1e-11), T/S <= 1e-12, integral 1, invalid inputs and budget refused",
       worst < 1e-11 and tsmax <= 1e-12 and abs(integ - 1) < 1e-8 and all(refused), f"max |log diff| {worst:.1e}, max T/S {tsmax:.1e}, integral {integ:.10f}")
    # common block setup
    for with_v in (False, True):
        d = synth_design(np.random.default_rng(SEED + 1), n_t=20, n=70, with_v=with_v)
        y = np.random.default_rng(SEED + 2).normal(0, 20, d.n)
        train, ver = CV.cv_masks(d, (8, 10), 2)
        dt, dv = CV.subset(d, train), CV.subset(d, ver)
        x = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)] + ([math.log(3), 0.5, 0.1] if with_v else []))
        analytic = B.loglik(CV.subset(d, train | ver), x, y[train | ver]) - B.loglik(dt, x, y[train])
        terms, _ = P.block_terms(dt, y[train], dv, y[ver], [(x, None)], rng, "L1", n_latent=6000)
        sc = P.score(terms)
        shared_fam = len(np.unique(dv.fam)) < dv.n
        ok(f"2. L1 ({'u+v' if with_v else 'u'}): MC block score = analytic l(train+block) - l(train) within 4 MC SE, status ok",
           abs(sc["score_raw"] - analytic) <= 4 * sc["mc_se"] and sc["status"] == "ok",
           f"MC {sc['score']:.4f} +- {sc['mc_se']:.4f} vs {analytic:.4f}; block {dv.n} records, shared family {shared_fam}, ESS w {sc['ess_weights']:.0f}")
    # 3. L2
    d = synth_design(np.random.default_rng(SEED + 3), n_t=20, n=70)
    y = np.random.default_rng(SEED + 4).normal(0, 20, d.n)
    train, ver = CV.cv_masks(d, (8, 10), 2)
    dt, dv = CV.subset(d, train), CV.subset(d, ver)
    x = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
    nu, scale = 4.0, 0.5
    lam_t = np.random.default_rng(SEED + 5).gamma(2.0, 0.5, int(train.sum()))
    tA, _ = P.block_terms(dt, y[train], dv, y[ver], [(x, lam_t)], rng, "L2", nu=nu, n_latent=6000)
    sA = P.score(tA)
    both = train | ver
    dj = CV.subset(d, both)
    pos_t, pos_v = np.flatnonzero(train[both]), np.flatnonzero(ver[both])
    lt = B.loglik(dt, x, y[train], lam=lam_t, scale=scale)
    tB = []
    for _ in range(3000):
        lam = np.empty(int(both.sum()))
        lam[pos_t], lam[pos_v] = lam_t, rng.gamma(nu / 2, 2 / nu, len(pos_v))
        tB.append(B.loglik(dj, x, y[both], lam=lam, scale=scale) - lt)
    sB = P.score(np.array(tB))
    ok("3. L2: latents drawn + t density = latents integrated + block precisions drawn (Gamma(nu/2, nu/2)), within 4 combined SE",
       abs(sA["score_raw"] - sB["score_raw"]) <= 4 * math.hypot(sA["mc_se"], sB["mc_se"]),
       f"{sA['score']:.4f} +- {sA['mc_se']:.4f} vs {sB['score']:.4f} +- {sB['mc_se']:.4f}")
    # 4. L3: two correlated block records (same CR and hemisphere), enumeration of the preimage pairs
    d = synth_design(np.random.default_rng(SEED + 6), n_t=20, n=70)
    train, ver = CV.cv_masks(d, (8, 10), 2)
    vidx = np.flatnonzero(ver)
    t0, h0 = d.t[vidx[0]], d.h[vidx[0]]
    keep = vidx[(d.t[vidx] == t0) & (d.h[vidx] == h0)][:2]
    if len(keep) < 2:                                          # force two records on the same CR and hemisphere
        keep = vidx[:2]
        d.t[keep[1]], d.h[keep[1]] = d.t[keep[0]], d.h[keep[0]]
        d = B.Design(t=d.t, h=d.h, s=d.s, a=d.a, lphi=d.lphi, cell=d.cell, fam=d.fam, n_t=d.n_t, n_cell=d.n_cell)
        train, ver = CV.cv_masks(d, (8, 10), 2)
    ver2 = np.zeros(d.n, bool)
    ver2[keep] = True
    train = train & ~ver2
    dt, dv = CV.subset(d, train), CV.subset(d, ver2)
    rng4 = np.random.default_rng(SEED + 7)
    theta_t = rng4.normal(0, 70, int(train.sum()))                # training latent tilts (any values: fixed state)
    gv = np.array([78.0, -63.0])                                   # block observations (folded tilts)
    x = np.array([math.log(70), 0.0, math.log(15), 0.6, 0.4, math.log(10)])
    tA, tsA = P.block_terms(dt, [theta_t], dv, gv, [(x, None)], rng, "L3", n_latent=6000)
    sA = P.score(tA)
    k = np.arange(-4, 5)
    pre = [np.r_[g + 360.0 * k, 180.0 - g + 360.0 * k] for g in gv]
    both = train | ver2
    dj = CV.subset(d, both)
    pos_v = np.flatnonzero(ver2[both])
    lt = B.loglik(dt, x, theta_t)
    yj = np.empty(int(both.sum()))
    yj[np.flatnonzero(train[both])] = theta_t
    lv = []
    for a, b in itertools.product(pre[0], pre[1]):
        yj[pos_v] = (a, b)
        lv.append(B.loglik(dj, x, yj) - lt)
    lv = np.array(lv)
    enum = lv.max() + math.log(np.exp(lv - lv.max()).sum())
    ok("4. L3: MC (latents drawn, preimages summed) = joint enumeration of the preimage pairs (Gaussian conditional) within 4 MC SE",
       abs(sA["score_raw"] - enum) <= 4 * sA["mc_se"] and tsA <= 1e-12,
       f"MC {sA['score']:.4f} +- {sA['mc_se']:.4f} vs enumeration {enum:.4f} ({len(lv)} pairs); max T/S {tsA:.1e}")
    # 5
    v = np.array([-3.0, -1.0, -2.0, -1.5, -0.5, -4.0])
    s5 = P.score(v, n_batches=3)
    e5, se5 = CV.log_mean_exp(v, n_batches=3)
    w = np.exp(v - v.max()) / np.exp(v - v.max()).sum()
    ok("5. score(): log-mean-exp and MC SE = bq_cv.log_mean_exp; weights ESS and largest share",
       abs(s5["score_raw"] - e5) < 1e-14 and abs(s5["mc_se"] - se5) < 1e-14 and abs(s5["ess_weights"] - 1 / (w * w).sum()) < 1e-12
       and abs(s5["max_weight"] - w.max()) < 1e-15)
    # 6
    d = synth_design(np.random.default_rng(36_400_812), n_t=30, n=200)
    y = np.random.default_rng(36_400_813).normal(0, 20, d.n)
    tr, ve = CV.cv_masks(d, (12, 16), 2)
    x = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
    t6, _ = P.block_terms(CV.subset(d, tr), y[tr], CV.subset(d, ve), y[ve], [(x, None)], rng, "L1", n_latent=4000)
    s6 = P.score(t6)
    ok("6. degeneracy guard: 45-record block, weights ESS < 100 -> score_not_established, score NaN, raw value kept",
       int(ve.sum()) >= 40 and s6["ess_weights"] < 100 and s6["status"] == "score_not_established" and np.isnan(s6["score"]) and np.isfinite(s6["score_raw"]),
       f"{int(ve.sum())} records, ESS {s6['ess_weights']:.1f}, max share {s6['max_weight']:.2f}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
