"""Selftest of python/sharpbl/bq_core.py on synthetic designs and responses only (no observed response is read).

Independent dense reference: the covariance is built directly (sd^2 phi^|t-t'| kappa^[h!=h'], every family as a
latent, X V X^T added) and log N is evaluated by a dense Cholesky.
Checks:
 1. log-likelihood: structured (banded + Schur) vs dense, with and without beta and v, several parameter sets;
 2. conditional posterior of the coefficients given psi vs the dense Gaussian formula;
 3. AR(1) precision inverted = phi^|dt| kappa^[h!=h'] on a calendar with CR gaps (no compressed calendar);
 4. slice sampler on a correlated Gaussian;
 5. Savage-Dickey (quadrature over one free coordinate) = ratio of evidences (quadrature) for nested M0/MQ, and
    the sampled Savage-Dickey estimate within Monte Carlo error;
 6. recovery of beta = -8, 0, +8 with short chains on a moderate synthetic design;
 7. timing on the real design structure (metadata only, synthetic y);
 8-11. blocked cross-validation: blocks, masks (buffer and families), exact conditional density vs dense, end to end;
 12. joint latent draw vs dense posterior; 13-14. L3 folded density and branch draw; 15-16. L2 and L3 Gibbs recovery;
 17. L3 with a large dispersion (many folded records).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_core_selftest.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import bq_core as B, bq_cv as CV, bq_robust as RB  # noqa: E402

SEED = 36_400_101
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def synth_design(rng, n_t=40, n=180, with_v=False, with_beta=True, gap_every=7):
    t_all = np.array([t for t in range(n_t) if t % gap_every != 3])          # some CRs without records
    t = np.sort(rng.choice(t_all, n))
    h = rng.integers(0, 2, n)
    s = rng.uniform(0.05, 0.5, n)
    a = rng.uniform(-1.0, 2.0, n)
    lphi = rng.uniform(0.0, 1.5, n)
    cell = (t >= n_t // 2).astype(int) * 2 + h
    fam = np.arange(n)
    for i in range(1, n):                                                       # some recurrences (1-3 CR apart)
        if rng.uniform() < 0.25 and 0 < t[i] - t[i - 1] <= 3:
            fam[i] = fam[i - 1]
    return B.Design(t=t, h=h, s=s, a=a, lphi=lphi, cell=cell, fam=fam, n_t=n_t, n_cell=4, with_v=with_v, with_beta=with_beta)


def dense_cov(d, p):
    tt, hh = d.t[:, None], d.h[None, :]
    same_h = (d.h[:, None] == d.h[None, :])
    C = np.diag((p["sigma0"] * np.exp(p["q"] * d.lphi)) ** 2)
    C += p["sigma_x"] ** 2 * p["phi"] ** np.abs(tt - d.t[None, :]) * np.where(same_h, 1.0, p["kappa"])
    if d.with_v:
        C += np.outer(d.s, d.s) * p["sigma_v"] ** 2 * p["phi_v"] ** np.abs(tt - d.t[None, :]) * np.where(same_h, 1.0, p["kappa_v"])
    C += p["sigma_f"] ** 2 * (d.fam[:, None] == d.fam[None, :])
    del hh
    return C


def dense_loglik(d, x, y):
    p = B.unpack(d, x)
    C = dense_cov(d, p) + d.X @ np.diag(d.vprior) @ d.X.T
    c = cho_factor(C, lower=True)
    return -0.5 * (len(y) * math.log(2 * math.pi) + 2 * np.log(np.diag(c[0])).sum() + y @ cho_solve(c, y))


def dense_post(d, x, y):
    p = B.unpack(d, x)
    C0 = dense_cov(d, p)
    Ci = np.linalg.inv(C0)
    cov = np.linalg.inv(np.diag(1 / d.vprior) + d.X.T @ Ci @ d.X)
    return cov @ d.X.T @ Ci @ y, cov


def random_x(d, rng):
    x = [rng.uniform(1.5, 3.5), rng.uniform(-1.2, 0.5), rng.uniform(-1, 2.5), rng.uniform(-2.5, 2.5), rng.uniform(-2, 2),
         rng.uniform(-1, 2)]
    if d.with_v:
        x += [rng.uniform(-1, 3), rng.uniform(-2.5, 2.5), rng.uniform(-2, 2)]
    return np.array(x)


def main():
    rng = np.random.default_rng(SEED)
    # 1-2
    worst_l, worst_p = 0.0, 0.0
    for with_v in (False, True):
        for with_beta in (True, False):
            d = synth_design(rng, with_v=with_v, with_beta=with_beta)
            for _ in range(4):
                x = random_x(d, rng)
                y = rng.normal(0, 20, d.n)
                ls, mu, cov = B.loglik(d, x, y, return_post=True)
                ld = dense_loglik(d, x, y)
                worst_l = max(worst_l, abs(ls - ld) / abs(ld))
                mu_d, cov_d = dense_post(d, x, y)
                worst_p = max(worst_p, np.max(np.abs(mu - mu_d)) / np.max(np.abs(mu_d)), np.max(np.abs(cov - cov_d)) / np.max(np.abs(cov_d)))
    ok("1. log-likelihood banded+Schur = dense (u, u+v; with/without beta; 16 cases)", worst_l < 1e-10, f"max rel {worst_l:.1e}")
    ok("2. coefficient posterior given psi = dense Gaussian formula", worst_p < 1e-8, f"max rel {worst_p:.1e}")
    # 3
    P, ld = B._ar1_precision(9, 1.7, -0.6, 0.4)
    t = np.repeat(np.arange(9), 2)
    hh = np.tile([0, 1], 9)
    Cd = 1.7 ** 2 * (-0.6) ** np.abs(t[:, None] - t[None, :]) * np.where(hh[:, None] == hh[None, :], 1.0, 0.4)
    ok("3. AR(1) precision^-1 = sd^2 phi^|dt| kappa^[h!=h'] (negative phi), log-det", np.allclose(np.linalg.inv(P), Cd, atol=1e-12)
       and abs(ld - np.linalg.slogdet(Cd)[1]) < 1e-10)
    # 4
    S = np.array([[1.0, 0.8], [0.8, 2.0]])
    Si = np.linalg.inv(S)
    dr, _, _, _ = B.slice_chain(lambda z: -0.5 * z @ Si @ z, np.zeros(2), 500, 6000, np.random.default_rng(SEED + 1))
    ok("4. slice sampler: correlated Gaussian mean and covariance", np.all(np.abs(dr.mean(0)) < 0.15) and np.allclose(np.cov(dr.T), S, rtol=0.15, atol=0.1),
       f"mean {dr.mean(0).round(3)}, cov {np.cov(dr.T).round(2).tolist()}")
    # 5: one free coordinate (log sigma0); the others fixed and shared by M0 and MQ
    dq = synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150)
    d0 = synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150, with_beta=False)
    xf = np.array([2.5, -0.4, 1.0, 0.8, -0.3, 0.7])
    pq = B.unpack(dq, xf)
    yv = np.random.default_rng(SEED + 3).multivariate_normal(dq.X[:, :4] @ np.array([20, 22, 18, 25.0]) - 4.0 * dq.a * dq.s,
                                                              dense_cov(dq, pq))
    grid = np.linspace(1.0, 4.5, 4001)
    dx = grid[1] - grid[0]

    def lpost(d, g):
        z = xf.copy()
        z[0] = g
        return B.log_prior(d, z) + B.loglik(d, z, yv)      # the fixed coordinates add the same constant to M0 and MQ
    lq = np.array([lpost(dq, g) for g in grid])
    l0 = np.array([lpost(d0, g) for g in grid])
    mx = max(lq.max(), l0.max())
    zq, z0 = np.exp(lq - mx).sum() * dx, np.exp(l0 - mx).sum() * dx
    log_bf_ev = math.log(z0) - math.log(zq)
    wq = np.exp(lq - lq.max())
    wq /= wq.sum()
    ords = []
    for g in grid[::20]:
        z = xf.copy()
        z[0] = g
        _, mu, cov = B.loglik(dq, z, yv, return_post=True)
        ords.append(math.exp(-0.5 * mu[-1] ** 2 / cov[-1, -1]) / math.sqrt(2 * math.pi * cov[-1, -1]))
    sd_post0 = float(np.dot(wq[::20] / wq[::20].sum(), ords))
    log_bf_sd = math.log(sd_post0) - math.log(1 / (math.sqrt(2 * math.pi) * dq.prior["beta_sd"]))
    ok("5a. Savage-Dickey (quadrature) = ratio of evidences (quadrature), nested M0/MQ with shared priors",
       abs(log_bf_sd - log_bf_ev) < 2e-3, f"log BF0Q: evidences {log_bf_ev:.5f}, Savage-Dickey {log_bf_sd:.5f}")
    # sampled version: chain on the single coordinate
    dr1, _, _, _ = B.slice_chain(lambda g: lpost(dq, g[0]), np.array([2.5]), 200, 2000, np.random.default_rng(SEED + 4))
    cond = []
    for g in dr1[:, 0]:
        z = xf.copy()
        z[0] = g
        _, mu, cov = B.loglik(dq, z, yv, return_post=True)
        cond.append((mu[-1], cov[-1, -1]))
    est, se = B.savage_dickey_log_bf0q(dq, np.array(cond))
    ok("5b. sampled Savage-Dickey within Monte Carlo error (4 x naive SE, inflated x3 for autocorrelation)",
       abs(est - log_bf_ev) < 4 * 3 * se + 1e-3, f"estimate {est:.4f} +- {se:.4f} vs {log_bf_ev:.4f}")
    # 6: recovery with all coordinates sampled
    for bt in (-8.0, 0.0, 8.0):
        rr = np.random.default_rng(SEED + 10 + int(bt))
        d6 = synth_design(rr, n_t=60, n=420)
        x6 = np.array([math.log(12.0), -0.3, math.log(3.0), 0.9, -0.4, math.log(2.0)])
        p6 = B.unpack(d6, x6)
        y6 = rr.multivariate_normal(d6.X[:, :4] @ np.array([22, 24, 18, 20.0]) + bt * d6.a * d6.s, dense_cov(d6, p6))
        dr6, _, _, _ = B.slice_chain(lambda z: B.log_post(d6, z, y6), x6, 150, 250, rr)
        c6 = B.beta_conditionals(d6, dr6[::5], y6)
        m = c6[:, 0].mean()
        sd = math.sqrt(c6[:, 1].mean() + c6[:, 0].var())
        ok(f"6. recovery beta = {bt:+.0f} (short chain; posterior mean within 3 SD)", abs(m - bt) < 3 * sd, f"mean {m:.2f}, SD {sd:.2f}")
    # 8-11: blocked cross-validation
    bl = CV.cv_blocks(221)
    lens = [hi - lo + 1 for lo, hi in bl]
    ok("8. CV blocks: 10 contiguous intervals covering the calendar, lengths differ by <= 1, remainder first",
       bl[0][0] == 0 and bl[-1][1] == 220 and all(bl[i + 1][0] == bl[i][1] + 1 for i in range(9)) and max(lens) - min(lens) <= 1
       and lens == sorted(lens, reverse=True), f"lengths {lens}")
    d8 = synth_design(np.random.default_rng(SEED + 30), n_t=60, n=300)
    far = np.flatnonzero(d8.t > 50)[0]
    d8.fam[far] = d8.fam[np.flatnonzero(d8.t < 6)[0]]                          # a family member far from the block
    d8 = B.Design(t=d8.t, h=d8.h, s=d8.s, a=d8.a, lphi=d8.lphi, cell=d8.cell, fam=d8.fam, n_t=60, n_cell=4)
    tr, ve = CV.cv_masks(d8, (0, 5), 11)
    ok("9. CV masks: block, buffer of 11 CR and every family member of the verification excluded from training (also far away)",
       not (tr & ve).any() and not tr[(d8.t <= 16)].any() and not tr[far] and tr[(d8.t > 16) & ~np.isin(d8.fam, d8.fam[ve])].all())
    # 10: exact conditional density = dense Gaussian conditional
    x10 = random_x(d8, np.random.default_rng(SEED + 31))
    y10 = np.random.default_rng(SEED + 32).normal(0, 20, d8.n)
    tr, ve = CV.cv_masks(d8, (24, 29), 11)
    val = CV.conditional_terms(d8, tr, ve, y10, [x10])[0]
    both = tr | ve
    dj = CV.subset(d8, both)
    Cj = dense_cov(dj, B.unpack(dj, x10)) + dj.X @ np.diag(dj.vprior) @ dj.X.T
    it, iv = np.flatnonzero(tr[both]), np.flatnonzero(ve[both])
    yj = y10[both]
    Ctt, Cvt, Cvv = Cj[np.ix_(it, it)], Cj[np.ix_(iv, it)], Cj[np.ix_(iv, iv)]
    K = Cvt @ np.linalg.inv(Ctt)
    mu, Sg = K @ yj[it], Cvv - K @ Cvt.T
    ref = -0.5 * (len(iv) * math.log(2 * math.pi) + np.linalg.slogdet(Sg)[1] + (yj[iv] - mu) @ np.linalg.solve(Sg, yj[iv] - mu))
    marg = sum(-0.5 * (math.log(2 * math.pi * Cvv[i, i]) + (yj[iv][i] - 0) ** 2 / Cvv[i, i]) for i in range(len(iv)))
    ok("10. block score given psi: l(train+ver) - l(train) = dense conditional Gaussian density (joint, not a sum of marginals)",
       abs(val - ref) < 1e-8 * abs(ref), f"{val:.6f} vs {ref:.6f}; sum of independent prior marginals would give {marg:.2f}")
    # 11: end to end on a strong synthetic effect: MQ should predict the blocks better than M0
    rr = np.random.default_rng(SEED + 40)
    dq = synth_design(rr, n_t=60, n=420)
    d0 = B.Design(t=dq.t, h=dq.h, s=dq.s, a=dq.a, lphi=dq.lphi, cell=dq.cell, fam=dq.fam, n_t=60, n_cell=4, with_beta=False)
    x11 = np.array([math.log(10.0), -0.3, math.log(2.0), 0.5, 0.0, math.log(2.0)])
    y11 = rr.multivariate_normal(dq.X[:, :4] @ np.array([22, 24, 18, 20.0]) - 15.0 * dq.a * dq.s, dense_cov(dq, B.unpack(dq, x11)))
    tot = {}
    for name, dm in (("MQ", dq), ("M0", d0)):
        sc = [CV.run_fold(dm, y11, blk, 5, x11, 60, 120, np.random.default_rng(SEED + 41 + k), thin=4) for k, blk in enumerate(CV.cv_blocks(60, 5))]
        tot[name] = (sum(f["score"] for f in sc), math.sqrt(sum(f["mc_se"] ** 2 for f in sc)))
    ok("11. end to end, beta = -15 (strong): MQ total block score > M0 (5 blocks, buffer 5, short chains)", tot["MQ"][0] > tot["M0"][0],
       f"MQ {tot['MQ'][0]:.1f} +- {tot['MQ'][1]:.2f}, M0 {tot['M0'][0]:.1f} +- {tot['M0'][1]:.2f}")
    # 12: joint latent draw = dense posterior (theta moments, and the shared part E[y - eps | y])
    d12 = synth_design(np.random.default_rng(SEED + 50), n_t=30, n=150, with_v=True)
    x12 = random_x(d12, np.random.default_rng(SEED + 51))
    y12 = np.random.default_rng(SEED + 52).normal(0, 20, d12.n)
    r12 = np.random.default_rng(SEED + 53)
    dr = [B.draw_latents(d12, x12, y12, r12) for _ in range(3000)]
    th = np.array([z[0] for z in dr])
    sh = np.array([z[4] for z in dr])
    mu_d, cov_d = dense_post(d12, x12, y12)
    p12 = B.unpack(d12, x12)
    C12 = dense_cov(d12, p12) + d12.X @ np.diag(d12.vprior) @ d12.X.T
    sig2 = (p12["sigma0"] * np.exp(p12["q"] * d12.lphi)) ** 2
    e_sh = y12 - sig2 * np.linalg.solve(C12, y12)
    se_th = np.sqrt(np.diag(cov_d) / len(th))
    se_sh = sh.std(0) / math.sqrt(len(sh))
    ok("12. joint latent draw (u+v, families): coefficient mean/cov and shared part = dense posterior (within 4.5 MC SE)",
       np.all(np.abs(th.mean(0) - mu_d) < 4.5 * se_th)
       and np.all(np.abs(np.cov(th.T) - cov_d) <= 0.1 * np.sqrt(np.outer(np.diag(cov_d), np.diag(cov_d))))
       and np.mean(np.abs(sh.mean(0) - e_sh) < 4.5 * se_sh) > 0.99,
       f"max |z| coeff {np.max(np.abs(th.mean(0) - mu_d) / se_th):.2f}")
    # 13: folded density normalised on (-90, 90) for sigma 12, 30, 150, 400 and several mu (incl. aliases)
    gg = np.linspace(-90, 90, 200001)                 # the density is finite at the end points: keep them in the rule
    errs = []
    for sg in (12.0, 30.0, 150.0, 400.0):
        for mu in (0.0, 75.0, -170.0, 400.0):
            f = np.exp(RB.folded_logpdf(gg, mu, sg))
            errs.append(abs(np.trapezoid(f, gg) - 1.0))
    ok("13. L3 folded density integrates to one on (-90, 90) (sigma 12/30/150/400, mu incl. 400)", max(errs) < 1e-6, f"max error {max(errs):.1e}")
    # 14: branch sampler = exact discrete conditional (frequencies)
    rb = np.random.default_rng(SEED + 60)
    gv, mv, sv = np.full(40000, 80.0), np.full(40000, 95.0), np.full(40000, 20.0)
    th14 = RB.draw_branches(gv, mv, sv, rb)
    w80, w100 = math.exp(-0.5 * (15 / 20) ** 2), math.exp(-0.5 * (5 / 20) ** 2)
    pf = np.mean(np.isclose(th14, 100.0))
    ok("14. L3 branch draw: frequencies of the preimages 80 / 100 match the discrete conditional", abs(pf - w100 / (w80 + w100)) < 0.01,
       f"P(100) {pf:.4f} vs {w100 / (w80 + w100):.4f}")
    # 15-16: L2 and L3 recover beta on synthetic data of their own kind
    for kind in ("L2", "L3"):
        rr = np.random.default_rng(SEED + 70 + (kind == "L3"))
        dk = synth_design(rr, n_t=50, n=400)
        sg0 = 12.0 if kind == "L2" else 35.0
        xk = np.array([math.log(sg0), -0.2, math.log(2.0), 0.6, -0.2, math.log(2.0)])
        pk = B.unpack(dk, xk)
        mean = dk.X[:, :4] @ np.array([22, 24, 18, 20.0]) - 8.0 * dk.a * dk.s
        Cs = dense_cov(dk, pk) - np.diag((pk["sigma0"] * np.exp(pk["q"] * dk.lphi)) ** 2)
        shared = mean + rr.multivariate_normal(np.zeros(dk.n), Cs)
        sdi = pk["sigma0"] * np.exp(pk["q"] * dk.lphi)
        if kind == "L2":
            eps = sdi * math.sqrt(0.5) * rr.standard_t(4, dk.n)
            yk = shared + eps
        else:
            yk = np.degrees(np.arcsin(np.sin(np.radians(shared + sdi * rr.standard_normal(dk.n)))))
        g = RB.gibbs(dk, yk, xk, 150, 300, rr, kind=kind)
        bb = g["theta"][:, -1]
        extra = f"mean lam {np.mean(g['summary']):.3f}" if kind == "L2" else f"share folded {np.mean(g['summary']):.3f}"
        ok(f"{15 if kind == 'L2' else 16}. {kind} Gibbs recovers beta = -8 on its own synthetic data (within 3 posterior SD)",
           abs(bb.mean() + 8.0) < 3 * bb.std(), f"mean {bb.mean():.2f}, SD {bb.std():.2f}; sigma0 {np.exp(g['psi'][:, 0]).mean():.1f} (true {sg0}); {extra}")
    # 17: L3 with a large dispersion (many folded records) against the oracle fit on the true latent tilt
    rr = np.random.default_rng(SEED + 80)
    d17 = synth_design(rr, n_t=50, n=500)
    x17 = np.array([math.log(70.0), 0.0, math.log(3.0), 0.6, -0.2, math.log(2.0)])
    p17 = B.unpack(d17, x17)
    mean17 = d17.X[:, :4] @ np.array([60, 70, 50, 65.0]) - 30.0 * d17.a * d17.s
    Cs17 = dense_cov(d17, p17) - np.diag(np.full(d17.n, 70.0 ** 2))
    th17 = mean17 + rr.multivariate_normal(np.zeros(d17.n), Cs17) + 70.0 * rr.standard_normal(d17.n)
    y17 = np.degrees(np.arcsin(np.sin(np.radians(th17))))
    folded = float(np.mean(np.abs(th17) > 90.0))
    g17 = RB.gibbs(d17, y17, x17, 200, 600, rr, kind="L3")
    b17, s17 = g17["theta"][:, -1], np.exp(g17["psi"][:, 0])
    # oracle: the Gaussian model fitted on the TRUE latent tilt (perfect unfolding), same priors. With sigma0 = 70 the
    # prior N(0, 10^2) on beta shrinks the estimate a lot, so the reference is the oracle posterior, not the true -30.
    dro, _, _, _ = B.slice_chain(lambda z: B.log_post(d17, z, th17), x17, 100, 300, rr)
    co = B.beta_conditionals(d17, dro[::5], th17)
    mo, so = co[:, 0].mean(), math.sqrt(co[:, 1].mean() + co[:, 0].var())
    dr1, _, _, _ = B.slice_chain(lambda z: B.log_post(d17, z, y17), x17, 100, 200, rr)
    c1 = B.beta_conditionals(d17, dr1[::4], y17)
    halves = (b17[:300].mean(), b17[300:].mean())
    ok("17. L3 with large dispersion (sigma0 = 70, ~20 % folded): beta close to the oracle fit on the true latent tilt, sigma0 recovered, "
       "no drift between chain halves",
       abs(b17.mean() - mo) < 1.5 * math.hypot(b17.std(), so) and abs(s17.mean() - 70.0) < 3 * s17.std() + 2.0
       and abs(halves[0] - halves[1]) < b17.std(),
       f"folded share true {folded:.2f}, sampled {np.mean(g17['summary']):.2f}; L3 beta {b17.mean():.1f} +- {b17.std():.1f} "
       f"(halves {halves[0]:.1f}/{halves[1]:.1f}), oracle {mo:.1f} +- {so:.1f}; sigma0 L3 {s17.mean():.1f}, L1 on folded gamma "
       f"{np.exp(dr1[:, 0]).mean():.1f} (beta {c1[:, 0].mean():.1f}, different target)")
    # 7: timing on the real design structure (design columns only)
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import bq_woodbury_benchmark as W
        dd = W.design()
        t_ = dd.CR.to_numpy() - dd.CR.min()
        cyc = dd.cyc.to_numpy()
        hem = (dd.hemisphere.to_numpy() == "S").astype(int)
        cell = (cyc == 25).astype(int) * 2 + hem
        lab, fam = np.unique(dd.family_id.to_numpy(), return_inverse=True)
        out = []
        for with_v in (False, True):
            dR = B.Design(t=t_, h=hem, s=dd.sinlat.to_numpy(), a=dd.A_monthly.to_numpy() - 1.0, lphi=np.log10(dd.phi.to_numpy() / 1e21),
                          cell=cell, fam=fam, n_t=int(t_.max()) + 1, n_cell=4, with_v=with_v)
            xR = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)] + ([math.log(5), 1.1, 0.2] if with_v else []))
            yR = np.random.default_rng(SEED + 20).normal(0, 25, dR.n)
            t0 = time.perf_counter()
            for _ in range(20):
                B.loglik(dR, xR, yR)
            out.append((with_v, dR.bw, (time.perf_counter() - t0) / 20))
        ok("7. timing on the real design structure (synthetic y): per log-likelihood evaluation", True,
           "; ".join(f"v={v}: bandwidth {bw}, {tm * 1e3:.1f} ms" for v, bw, tm in out))
    except Exception as exc:                                                     # timing is informative only
        ok("7. timing on the real design structure", False, repr(exc))
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
