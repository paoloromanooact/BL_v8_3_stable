import sys, math, numpy as np
sys.path.insert(0,'python'); sys.path.insert(0,'scripts')
from sharpbl import bq_core as B, bq_cv as CV, bq_smc as S
from bq_core_selftest import synth_design
from bq_smc_selftest import with_shared_family
SEED = 36_400_901
x0 = np.array([math.log(15), -0.3, math.log(4), 0.8, 0.3, math.log(3)])
d = synth_design(np.random.default_rng(SEED + 3), n_t=20, n=90)
y = np.random.default_rng(SEED + 4).normal(0, 20, d.n) + 6 * np.random.default_rng(SEED + 5).standard_t(4, d.n)
d = with_shared_family(d, CV.cv_masks(d, (8, 11), 2)[1])
train, ver = CV.cv_masks(d, (8, 11), 2)
lam_t = np.random.default_rng(SEED + 6).gamma(2.0, 0.5, int(train.sum()))
st = S.block_state(d, train, ver, x0, y[train], lam_t, 0.5)
dv = CV.subset(d, ver)
print("D", st["D"], "m", dv.m, "states", len(np.unique(dv.iu)), "sf2_single zeros", int((st["sf2_single"] == 0).sum()))
def stats(v): v=np.array(v); return f"{v.mean():.4f} +- {v.std(ddof=1)/math.sqrt(len(v)):.4f} (sd {v.std(ddof=1):.4f}, n {len(v)})"
big = [S.smc_block(st, y[ver], "L2", 30000, np.random.default_rng(SEED + 500 + k))["score"] for k in range(4)]
print("plain N=30000:", stats(big))
pl = [S.smc_block(st, y[ver], "L2", 2000, np.random.default_rng(SEED + 600 + k))["score"] for k in range(24)]
print("plain N=2000 :", stats(pl))
fo = [S.smc_block(st, y[ver], "L2", 2000, np.random.default_rng(SEED + 700 + k), ess_frac=1.01)["score"] for k in range(24)]
print("forced N=2000:", stats(fo))
