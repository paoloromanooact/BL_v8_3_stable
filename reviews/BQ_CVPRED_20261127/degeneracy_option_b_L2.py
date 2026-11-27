"""Option (b) for L2: shared latents integrated with the Gaussian core, block precisions lam_ver ~ Gamma(nu/2, nu/2)
drawn; same psi, same training precisions; compared with option (a)-direct (latents drawn, t density). Synthetic."""
import sys, math, numpy as np
sys.path.insert(0,'python'); sys.path.insert(0,'scripts')
from sharpbl import bq_core as B, bq_cv as CV, bq_cvpred as P
from bq_core_selftest import synth_design
rng = np.random.default_rng(36_400_821)
x = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
nu, scale, S = 4.0, 0.5, 4000
for n, nt, blk in ((70, 20, (8, 10)), (200, 30, (12, 16)), (600, 40, (16, 22)), (1500, 50, (20, 25))):
    d = synth_design(np.random.default_rng(36_400_812), n_t=nt, n=n)
    # synthetic L2 response: Gaussian core plus t4 residuals
    y = np.random.default_rng(36_400_813).normal(0, 20, d.n) + 8 * np.random.default_rng(36_400_814).standard_t(4, d.n)
    tr, ve = CV.cv_masks(d, blk, 2)
    both = tr | ve
    dt, dv, dj = CV.subset(d, tr), CV.subset(d, ve), CV.subset(d, both)
    lam_t = np.random.default_rng(36_400_815).gamma(2.0, 0.5, int(tr.sum()))
    pos_t, pos_v = np.flatnonzero(tr[both]), np.flatnonzero(ve[both])
    lt = B.loglik(dt, x, y[tr], lam=lam_t, scale=scale)
    tb = []
    for _ in range(S):
        lam = np.empty(int(both.sum())); lam[pos_t] = lam_t; lam[pos_v] = rng.gamma(nu / 2, 2 / nu, len(pos_v))
        tb.append(B.loglik(dj, x, y[both], lam=lam, scale=scale) - lt)
    sb = P.score(np.array(tb))
    ta, _ = P.block_terms(dt, y[tr], dv, y[ve], [(x, lam_t)], rng, "L2", nu=nu, n_latent=S)
    sa = P.score(ta)
    print(f"block {dv.n:4d}: (b) {sb['score_raw']:.3f} +- {sb['mc_se']:.3f}, ESS {sb['ess_weights']:7.1f}, max {sb['max_weight']:.3f}, {sb['status']:22s} | "
          f"direct {sa['score_raw']:.3f} +- {sa['mc_se']:.3f}, ESS {sa['ess_weights']:6.1f}, {sa['status']}")
