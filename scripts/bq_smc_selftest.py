"""Selftest of python/sharpbl/bq_smc.py at FIXED psi on synthetic designs and responses only (no observed response).

 1. block state: prior of z from the training system = dense Gaussian conditional of theta and of the block states
    (built from the dense covariance of the training records), within 1e-8;
 2. L1: sequential Kalman score = analytic l(train + block) - l(train) (u and u+v, a family shared inside the block,
    singleton families absorbed), within 1e-8 absolute;
 3. L2 on a 2-record block with one record about 20 residual scales out (tail): SMC (8 replicates x 2000 particles) =
    exact sum over all node pairs of the SAME discrete precision measure (log-lambda grid, 200 points), each pair scored
    with the Gaussian core; the discretisation (100 vs 200 points) below 1e-8;
 4. L3 on 2 correlated records (same CR and hemisphere): SMC (8 replicates x 2000) = joint enumeration of the preimage
    pairs scored with the Gaussian core;
 5. rejuvenation preserves the prefix conditional: on a 14-record L2 block and a 6-record L3 block, runs with
    resampling and data-augmentation Gibbs FORCED at every record agree with plain runs (replicate means within 4
    combined SE); the forced runs resample at every record.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_smc_selftest.py
"""
from __future__ import annotations

import itertools
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_cv as CV  # noqa: E402
if len(sys.argv) > 1 and sys.argv[1] == "--module":           # scratch revision under test
    import importlib.util
    _sp = importlib.util.spec_from_file_location("sharpbl.bq_smc", sys.argv[2])
    S = importlib.util.module_from_spec(_sp)
    _sp.loader.exec_module(S)
else:
    from sharpbl import bq_smc as S  # noqa: E402
from bq_core_selftest import synth_design, dense_cov  # noqa: E402

SEED = 36_400_901
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def lse(v):
    v = np.asarray(v, float)
    return float(v.max() + np.log(np.exp(v - v.max()).sum()))


def two_record_block(d, train, ver):
    """Keep two block records on the same CR and hemisphere (correlated through u)."""
    vidx = np.flatnonzero(ver)
    for i in vidx:
        same = vidx[(d.t[vidx] == d.t[i]) & (d.h[vidx] == d.h[i])]
        if len(same) >= 2:
            v2 = np.zeros(d.n, bool)
            v2[same[:2]] = True
            return train & ~v2, v2
    raise SystemExit("setup: no two block records on one CR and hemisphere")


def with_shared_family(d, ver):
    """Two block records on different CRs made members of one family (absent from the training by construction)."""
    vidx = np.flatnonzero(ver)
    i = vidx[0]
    j = next(k for k in vidx if d.t[k] != d.t[i])
    fam = d.fam.copy()
    fam[j] = fam[i]
    return B.Design(t=d.t, h=d.h, s=d.s, a=d.a, lphi=d.lphi, cell=d.cell, fam=fam, n_t=d.n_t, n_cell=d.n_cell, with_v=d.with_v)


def main():
    rng = np.random.default_rng(SEED)
    x0 = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
    # 1-2
    for with_v in (False, True):
        d = synth_design(np.random.default_rng(SEED + 1), n_t=20, n=90, with_v=with_v)
        y = np.random.default_rng(SEED + 2).normal(0, 20, d.n)
        d = with_shared_family(d, CV.cv_masks(d, (8, 11), 2)[1])
        train, ver = CV.cv_masks(d, (8, 11), 2)
        x = np.r_[x0, [math.log(3), 0.5, 0.1]] if with_v else x0
        st = S.block_state(d, train, ver, x, y[train])
        # dense reference of the block state: Gaussian conditional of (theta, states) given the training records
        dt = CV.subset(d, train)
        p = B.unpack(dt, x)
        Ct = dense_cov(dt, p)
        m = dt.m
        Vth = np.diag(dt.vprior)
        Kidx = np.unique(np.r_[CV.subset(d, ver).iu, CV.subset(d, ver).iv] if with_v else CV.subset(d, ver).iu)
        # prior covariance of the states (AR(1) of u, v) at Kidx and their covariance with the training latents
        tt, hh = Kidx // dt.p, Kidx % dt.p

        def kcov(t1, c1, t2, c2):
            same_comp = (c1 >= 2) == (c2 >= 2)
            if not same_comp:
                return 0.0
            if c1 >= 2:
                return p["sigma_v"] ** 2 * p["phi_v"] ** abs(t1 - t2) * (1.0 if c1 == c2 else p["kappa_v"])
            return p["sigma_x"] ** 2 * p["phi"] ** abs(t1 - t2) * (1.0 if c1 == c2 else p["kappa"])
        PK = np.array([[kcov(a, b, c, e) for c, e in zip(tt, hh)] for a, b in zip(tt, hh)])
        # covariance of states with the training observations y_t = X theta + u(+sv) + f + e
        CKy = np.array([[kcov(a, b, dt.t[i], dt.h[i]) + (dt.s[i] * kcov(a, b, dt.t[i], 2 + dt.h[i]) if with_v else 0.0)
                         for i in range(dt.n)] for a, b in zip(tt, hh)])
        Cy = Ct + dt.X @ Vth @ dt.X.T
        Cty = Vth @ dt.X.T
        G = np.vstack([Cty, CKy])
        P0 = np.block([[Vth, np.zeros((m, len(Kidx)))], [np.zeros((len(Kidx), m)), PK]])
        Ci = np.linalg.inv(Cy)
        mu_d = G @ Ci @ y[train]
        Sg_d = P0 - G @ Ci @ G.T
        nz = m + len(Kidx)
        e1 = max(np.max(np.abs(st["mu0"][:nz] - mu_d)) / np.max(np.abs(mu_d)), np.max(np.abs(st["Sig0"][:nz, :nz] - Sg_d)) / np.max(np.abs(Sg_d)))
        ok(f"1. block state ({'u+v' if with_v else 'u'}): mean and covariance = dense Gaussian conditional (1e-8 relative)", e1 < 1e-8,
           f"max rel {e1:.1e}; D = {st['D']} ({len(Kidx)} states, {st['D'] - nz} shared families)")
        analytic = B.loglik(CV.subset(d, train | ver), x, y[train | ver]) - B.loglik(dt, x, y[train])
        r = S.smc_block(st, y[ver], "L1")
        ok(f"2. L1 ({'u+v' if with_v else 'u'}): sequential Kalman = analytic l(train+block) - l(train) (1e-8)", abs(r["score"] - analytic) < 1e-8,
           f"{r['score']:.10f} vs {analytic:.10f}; block {int(ver.sum())} records")
    # 3. L2, two records, exact node sum
    d = synth_design(np.random.default_rng(SEED + 3), n_t=20, n=90)
    y = np.random.default_rng(SEED + 4).normal(0, 20, d.n) + 6 * np.random.default_rng(SEED + 5).standard_t(4, d.n)
    train, ver = CV.cv_masks(d, (8, 11), 2)
    train, ver = two_record_block(d, train, ver)
    y[np.flatnonzero(ver)[0]] += 250.0                                # tail record (~20 residual scales)
    lam_t = np.random.default_rng(SEED + 6).gamma(2.0, 0.5, int(train.sum()))
    st = S.block_state(d, train, ver, x0, y[train], lam_t, 0.5)
    both = train | ver
    dj, dt = CV.subset(d, both), CV.subset(d, train)
    pos_t, pos_v = np.flatnonzero(train[both]), np.flatnonzero(ver[both])
    lt = B.loglik(dt, x0, y[train], lam=lam_t, scale=0.5)

    def node_sum(n):
        lam_n, lq = S.precision_measure(4.0, n)
        out = []
        for a, b in itertools.product(range(n), range(n)):
            lam = np.empty(int(both.sum()))
            lam[pos_t], lam[pos_v] = lam_t, (lam_n[a], lam_n[b])
            out.append(lq[a] + lq[b] + B.loglik(dj, x0, y[both], lam=lam, scale=0.5) - lt)
        return lse(out)
    ref64, ref128 = node_sum(200), node_sum(100)        # names kept: 200-point measure (used) and 100-point check
    reps = [S.smc_block(st, y[ver], "L2", 2000, np.random.default_rng(SEED + 10 + k))["score"] for k in range(8)]
    mean, se = float(np.mean(reps)), float(np.std(reps, ddof=1) / math.sqrt(len(reps)))
    ok("3. L2, 2 records (one ~20 residual scales out): SMC replicate mean = exact sum over the 200-point pairs within 4 SE; 100 vs 200 points < 1e-8",
       abs(mean - ref64) <= 4 * se + 1e-12 and abs(ref64 - ref128) < 1e-8, f"SMC {mean:.5f} +- {se:.5f} vs {ref64:.5f}; 200 vs 100 points {ref64 - ref128:.1e}")
    # 4. L3, two correlated records, joint enumeration
    d = synth_design(np.random.default_rng(SEED + 7), n_t=20, n=90)
    train, ver = CV.cv_masks(d, (8, 11), 2)
    train, ver = two_record_block(d, train, ver)
    theta_t = np.random.default_rng(SEED + 8).normal(0, 70, int(train.sum()))
    gv = np.array([78.0, -63.0])
    x3 = np.array([math.log(70), 0.0, math.log(15), 0.6, 0.4, math.log(10)])
    st = S.block_state(d, train, ver, x3, theta_t)
    both = train | ver
    dj, dt = CV.subset(d, both), CV.subset(d, train)
    pos_t, pos_v = np.flatnonzero(train[both]), np.flatnonzero(ver[both])
    lt = B.loglik(dt, x3, theta_t)
    k = np.arange(-4, 5)
    pre = [np.r_[g + 360.0 * k, 180.0 - g + 360.0 * k] for g in gv]
    yj = np.empty(int(both.sum()))
    yj[pos_t] = theta_t
    lv = []
    for a, b in itertools.product(pre[0], pre[1]):
        yj[pos_v] = (a, b)
        lv.append(B.loglik(dj, x3, yj) - lt)
    enum = lse(lv)
    yv = np.empty(2)
    yv[:] = gv                                                   # gv is in the original block order of ver
    reps = [S.smc_block(st, yv, "L3", 2000, np.random.default_rng(SEED + 30 + k)) for k in range(8)]
    sc = [r["score"] for r in reps]
    mean, se = float(np.mean(sc)), float(np.std(sc, ddof=1) / math.sqrt(len(sc)))
    ok("4. L3, 2 correlated records: SMC replicate mean = joint enumeration within 4 SE; tail bound certified (one image routine)",
       abs(mean - enum) <= 4 * se + 1e-12 and max(r["max_tail_ratio"] for r in reps) <= 1e-12,
       f"SMC {mean:.5f} +- {se:.5f} vs {enum:.5f} ({len(lv)} pairs)")
    # 5. forced resampling + rejuvenation at every record vs plain runs (L2 with a shared family, L3)
    d = synth_design(np.random.default_rng(SEED + 3), n_t=20, n=90)
    y = np.random.default_rng(SEED + 4).normal(0, 20, d.n) + 6 * np.random.default_rng(SEED + 5).standard_t(4, d.n)
    d = with_shared_family(d, CV.cv_masks(d, (8, 11), 2)[1])
    train, ver = CV.cv_masks(d, (8, 11), 2)
    lam_t = np.random.default_rng(SEED + 6).gamma(2.0, 0.5, int(train.sum()))
    st = S.block_state(d, train, ver, x0, y[train], lam_t, 0.5)
    t0 = time.perf_counter()
    rP = [S.smc_block(st, y[ver], "L2", 2000, np.random.default_rng(SEED + 50 + k)) for k in range(6)]
    tP = (time.perf_counter() - t0) / 6
    t0 = time.perf_counter()
    rF = [S.smc_block(st, y[ver], "L2", 2000, np.random.default_rng(SEED + 70 + k), ess_frac=1.01) for k in range(6)]
    tF = (time.perf_counter() - t0) / 6
    a_, b_ = [r["score"] for r in rP], [r["score"] for r in rF]
    seA, seB = np.std(a_, ddof=1) / math.sqrt(len(a_)), np.std(b_, ddof=1) / math.sqrt(len(b_))
    ok(f"5a. L2, {int(ver.sum())} records (shared families {st['D'] - CV.subset(d, ver).m - len(np.unique(CV.subset(d, ver).iu))}): forced "
       "resampling + rejuvenation at every record = plain runs within 4 combined SE",
       abs(np.mean(a_) - np.mean(b_)) <= 4 * math.hypot(seA, seB) and min(r["n_resample"] for r in rF) == int(ver.sum()) - 1,
       f"plain {np.mean(a_):.4f} +- {seA:.4f} ({tP:.1f} s) vs forced {np.mean(b_):.4f} +- {seB:.4f} ({tF:.1f} s, "
       f"{rF[0]['n_resample']} resamplings)")
    d = synth_design(np.random.default_rng(SEED + 7), n_t=20, n=90)
    train, ver = CV.cv_masks(d, (9, 10), 2)
    theta_t = np.random.default_rng(SEED + 8).normal(0, 70, int(train.sum()))
    gv = np.random.default_rng(SEED + 9).uniform(-85, 85, int(ver.sum()))
    st = S.block_state(d, train, ver, x3, theta_t)
    rP = [S.smc_block(st, gv, "L3", 1000, np.random.default_rng(SEED + 90 + k))["score"] for k in range(6)]
    rF = [S.smc_block(st, gv, "L3", 1000, np.random.default_rng(SEED + 110 + k), ess_frac=1.01) for k in range(6)]
    fF = [r["score"] for r in rF]
    seA, seB = np.std(rP, ddof=1) / math.sqrt(len(rP)), np.std(fF, ddof=1) / math.sqrt(len(fF))
    ok(f"5b. L3, {int(ver.sum())} records: forced resampling + rejuvenation = plain runs within 4 combined SE; max T/S incl. rejuvenation <= 1e-12",
       abs(np.mean(rP) - np.mean(fF)) <= 4 * math.hypot(seA, seB) and min(r["n_resample"] for r in rF) == int(ver.sum()) - 1
       and max(r["max_tail_ratio"] for r in rF) <= 1e-12,
       f"plain {np.mean(rP):.4f} +- {seA:.4f} vs forced {np.mean(fF):.4f} +- {seB:.4f}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
