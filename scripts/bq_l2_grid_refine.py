"""BQ-HMI L2: residual error of the log-lambda grid, 200 against 400 points, on the SAME block, response, psi and seeds as
the SMC benchmark and the resolution comparison (Codex, 27 Nov). Development, at fixed psi.

Runs the revised scorer (module snapshotted by scripts/bq_l2_resolution_compare.py) with n_quad = 400 and the
benchmark L2 seeds, and pairs each replicate with the 200-point replicate of reviews/BQ_L2_RESOLUTION_20261127/.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_l2_grid_refine.py --res reviews/BQ_L2_RESOLUTION_20261127 \
        --out reviews/BQ_L2_GRID_REFINE_20261127 [--size 395 --reps 4 --procs 4]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_cv as CV  # noqa: E402
import bq_smc_stability as BS  # noqa: E402
import bq_l2_resolution_compare as RC  # noqa: E402


def job(args):
    module, size, bi, rep, particles, n_quad = args
    S = RC.load(module)
    d = BS.design()
    rng0 = np.random.default_rng(BS.SEED0)
    y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
    blk = next(b for b in CV.cv_blocks(d.n_t) if int(CV.cv_masks(d, b, 11)[1].sum()) == size)
    train, ver = CV.cv_masks(d, blk, 11)
    x = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)])
    st = S.block_state(d, train, ver, x, y2[train], np.ones(int(train.sum())), 0.5)
    seed = BS.SEED0 + 1000 * 1 + 100 * bi + rep
    t0 = time.perf_counter()
    r = S.smc_block(st, y2[ver], "L2", particles, np.random.default_rng(seed), n_quad=n_quad)
    return dict(records=size, replicate=rep, seed=seed, score_400=r["score"], n_resample_400=r["n_resample"], seconds=time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=395)
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--particles", type=int, default=1000)
    ap.add_argument("--procs", type=int, default=4)
    a = ap.parse_args()
    out, res = Path(a.out), Path(a.res)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    module = res / "bq_smc_revised.py"
    bi = [22, 102, 236, 395].index(a.size)
    meta = dict(module_sha256=hashlib.sha256(module.read_bytes()).hexdigest(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                size=a.size, reps=a.reps, particles=a.particles, n_quad=400, paired_with=str(res / "LOGGRID_REPLICATES.csv"))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    rows = []
    with get_context("fork").Pool(a.procs) as pool:
        for r in pool.imap_unordered(job, [(str(module), a.size, bi, k, a.particles, 400) for k in range(a.reps)]):
            rows.append(r)
            pd.DataFrame([r]).to_csv(out / "GRID400_REPLICATES.csv", mode="a", header=not (out / "GRID400_REPLICATES.csv").exists(), index=False)
            print(r, flush=True)
    g200 = pd.read_csv(res / "LOGGRID_REPLICATES.csv")
    m = pd.DataFrame(rows).merge(g200[["records", "replicate", "seed", "score_loggrid", "n_resample"]], on=["records", "replicate", "seed"])
    m["diff_400_200"] = m.score_400 - m.score_loggrid
    m.to_csv(out / "PAIRED.csv", index=False)
    s = dict(n=len(m), diff_mean=float(m.diff_400_200.mean()), diff_se=float(m.diff_400_200.std(ddof=1) / math.sqrt(len(m))) if len(m) > 1 else np.nan,
             sd_400=float(m.score_400.std(ddof=1)), sd_200=float(m.score_loggrid.std(ddof=1)))
    (out / "SUMMARY.json").write_text(json.dumps(s, indent=2) + "\n")
    print(s)


if __name__ == "__main__":
    main()
