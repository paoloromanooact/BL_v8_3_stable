import sys, math, numpy as np
sys.path.insert(0,'python'); sys.path.insert(0,'scripts')
from sharpbl import bq_core as B, bq_cv as CV, bq_cvpred as P
from bq_core_selftest import synth_design
rng = np.random.default_rng(36_400_811)
x = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
for n, nt, blk in ((70, 20, (8, 10)), (200, 30, (12, 16)), (600, 40, (16, 22)), (1500, 50, (20, 25))):
    d = synth_design(np.random.default_rng(36_400_812), n_t=nt, n=n)
    y = np.random.default_rng(36_400_813).normal(0, 20, d.n)
    tr, ve = CV.cv_masks(d, blk, 2)
    dt, dv = CV.subset(d, tr), CV.subset(d, ve)
    an = B.loglik(CV.subset(d, tr | ve), x, y[tr | ve]) - B.loglik(dt, x, y[tr])
    t, _ = P.block_terms(dt, y[tr], dv, y[ve], [(x, None)], rng, "L1", n_latent=4000)
    s = P.score(t)
    print(f"block {dv.n:4d} records: MC raw {s['score_raw']:.3f} +- {s['mc_se']:.3f} vs analytic {an:.3f}; ESS weights {s['ess_weights']:.1f} of 4000, max share {s['max_weight']:.3f}; status {s['status']}")
