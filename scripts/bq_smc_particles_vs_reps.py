"""BQ-HMI L2 on the 395-record block (Codex decision of 27 Nov): one 2000-particle replicate against two independent
1000-particle replicates combined by log-mean-exp of the density estimates, with the 1000-particle reference; same
block, synthetic response and psi as the SMC benchmark, bq_smc as integrated in 3383084 (log-lambda grid, 200 points).
ISOLATED run: one process, configurations in sequence. Each configuration is repeated R times with independent seeds
to measure the dispersion of its final estimate. Development, at fixed psi.

Configurations: A = 1 x 1000 particles, B = 1 x 2000, C = 2 x 1000 combined (log of the mean of the two densities).
Seeds: 36_402_500 + 100 * config + 10 * repeat + k (k = 0, 1 for the two replicates of C). Every replicate is saved as
soon as it ends (REPLICATES.csv); SUMMARY.csv per configuration: mean, sd and SE of the final estimate, mean seconds per
estimate (sum over its replicates), mean resamplings.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_smc_particles_vs_reps.py --out reviews/BQ_SMC_PARTICLES_VS_REPS_20261127 [--repeats 6]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_cv as CV, bq_smc as S  # noqa: E402
import bq_smc_stability as BS  # noqa: E402

SEED0 = 36_402_500
CONFIGS = (("A_1x1000", 1, 1000), ("B_1x2000", 1, 2000), ("C_2x1000", 2, 1000))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=6)
    ap.add_argument("--size", type=int, default=395)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_smc.py", ROOT / "python/sharpbl/bq_core.py", ROOT / "scripts/bq_smc_stability.py"]
    meta = dict(status="running", sources_sha256={str(p.relative_to(ROOT)): sha(p) for p in srcs}, seed0=SEED0, repeats=a.repeats, size=a.size,
                configs=[list(c) for c in CONFIGS], note="L2, fixed psi, isolated single process; development")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    d = BS.design()
    rng0 = np.random.default_rng(BS.SEED0)
    y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
    blk = next(b for b in CV.cv_blocks(d.n_t) if int(CV.cv_masks(d, b, 11)[1].sum()) == a.size)
    train, ver = CV.cv_masks(d, blk, 11)
    x = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)])
    st = S.block_state(d, train, ver, x, y2[train], np.ones(int(train.sum())), 0.5)
    rows, ests = [], []
    for ci, (name, k_rep, n_part) in enumerate(CONFIGS):
        for rep in range(a.repeats):
            scores, secs, res = [], 0.0, 0
            for k in range(k_rep):
                seed = SEED0 + 100 * ci + 10 * rep + k
                t0 = time.perf_counter()
                r = S.smc_block(st, y2[ver], "L2", n_part, np.random.default_rng(seed))
                dt = time.perf_counter() - t0
                rows.append(dict(config=name, repeat=rep, k=k, seed=seed, particles=n_part, score=r["score"], n_resample=r["n_resample"],
                                 ess_min=r["ess_min"], n_quad=r.get("n_quad"), seconds=dt))
                pd.DataFrame([rows[-1]]).to_csv(out / "REPLICATES.csv", mode="a", header=not (out / "REPLICATES.csv").exists(), index=False)
                print(rows[-1], flush=True)
                scores.append(r["score"])
                secs += dt
                res += r["n_resample"]
            v = np.array(scores)
            est = float(v.max() + math.log(np.exp(v - v.max()).mean()))     # log of the mean density
            ests.append(dict(config=name, repeat=rep, estimate=est, seconds=secs, resamplings=res))
    e = pd.DataFrame(ests)
    e.to_csv(out / "ESTIMATES.csv", index=False)
    s = e.groupby("config").agg(n=("estimate", "size"), mean=("estimate", "mean"), sd=("estimate", "std"), seconds=("seconds", "mean"),
                                resamplings=("resamplings", "mean")).reset_index()
    s["se"] = s.sd / np.sqrt(s.n)
    s.to_csv(out / "SUMMARY.csv", index=False)
    meta.update(status="completed", sources_unchanged=all(sha(ROOT / kk) == vv for kk, vv in meta["sources_sha256"].items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(s.to_string())


if __name__ == "__main__":
    main()
