"""BQ-HMI preparation: L3 branch-exploration diagnostic (kept DISTINCT from the selftest), synthetic only.

Synthetic data with a large dispersion (sigma0 70, about 20 % folded; the case of selftest 17) on a synthetic design.
Three chains from different branch configurations (identity, |gamma| > 60 reflected, random reflection). Reported:
- per chain: posterior mean and SD of beta, sigma0, folded share;
- split R-hat across chains of beta, log sigma0 and folded share (agreement of the posteriors);
- branch changes in the saved phase: share of records that changed branch at least once, overall and for |gamma| > 60,
  and mean changes per record.
A positive outcome here does not prove complete exploration for the real data: it is one diagnostic.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_l3_branch_diagnostic.py --out reviews/BQ_L3_BRANCH_DIAGNOSTIC_20261125 [--warm 300 --keep 900]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_robust as RB  # noqa: E402

SEED = 36_400_401
INITS = ("identity", "fold_high", "random")


def data():
    import bq_core_selftest as T
    rr = np.random.default_rng(SEED)
    d = T.synth_design(rr, n_t=50, n=500)
    x = np.array([math.log(70.0), 0.0, math.log(3.0), 0.6, -0.2, math.log(2.0)])
    p = B.unpack(d, x)
    mean = d.X[:, :4] @ np.array([60, 70, 50, 65.0]) - 30.0 * d.a * d.s
    Cs = T.dense_cov(d, p) - np.diag(np.full(d.n, 70.0 ** 2))
    th = mean + rr.multivariate_normal(np.zeros(d.n), Cs) + 70.0 * rr.standard_normal(d.n)
    return d, x, th, np.degrees(np.arcsin(np.sin(np.radians(th))))


def chain(job):
    init, warm, keep = job
    d, x, th, g = data()
    rng = np.random.default_rng(SEED + 1 + INITS.index(init))
    out = RB.gibbs(d, g, x, warm, keep, rng, kind="L3", theta_init=RB.preimage_init(g, init, rng))
    return dict(init=init, beta=out["theta"][:, -1], log_sigma0=out["psi"][:, 0], folded=out["summary"], switches=out["switches"],
                true_folded=float(np.mean(np.abs(th) > 90)), high=np.abs(g) > 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--warm", type=int, default=300)
    ap.add_argument("--keep", type=int, default=900)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    with Pool(3) as pool:
        res = pool.map(chain, [(i, a.warm, a.keep) for i in INITS])
    rows = [dict(init=r["init"], beta_mean=r["beta"].mean(), beta_sd=r["beta"].std(), sigma0_mean=float(np.exp(r["log_sigma0"]).mean()),
                 folded_share_mean=float(np.mean(r["folded"])), changed_any=float(np.mean(r["switches"] > 0)),
                 changed_any_high=float(np.mean(r["switches"][r["high"]] > 0)), changes_per_record=float(r["switches"].mean()))
            for r in res]
    rh = dict(beta=RB.split_rhat([r["beta"] for r in res]), log_sigma0=RB.split_rhat([r["log_sigma0"] for r in res]),
              folded_share=RB.split_rhat([r["folded"] for r in res]))
    a.out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(a.out / "CHAINS.csv", index=False)
    (a.out / "SUMMARY.json").write_text(json.dumps(dict(seed=SEED, warm=a.warm, keep=a.keep, split_rhat=rh, true_folded_share=res[0]["true_folded"],
                                                        note="synthetic only; one diagnostic, not a proof of exploration"), indent=2) + "\n")
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("split R-hat", {k: round(v, 3) for k, v in rh.items()}, "true folded share", round(res[0]["true_folded"], 3))
