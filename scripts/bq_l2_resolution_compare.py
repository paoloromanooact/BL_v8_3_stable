"""BQ-HMI L2: resolution comparison of the discrete precision measure on the SAME block, the SAME synthetic response,
the SAME psi and the SAME seeds as the SMC benchmark (scripts/bq_smc_stability.py), at fixed psi. Development.

Runs only the REVISED sequential scorer (log-lambda grid, 200 points; module file given by --module, snapshotted in the
output) with the benchmark's L2 seeds; the generalised Gauss-Laguerre (64 nodes) scores are the benchmark's own
REPLICATES.csv. Reported per block: the paired difference (same seed) of the scores, its mean and SE over replicates
(quadrature component), and separately the replicate SD of each scorer (Monte Carlo component).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_l2_resolution_compare.py --module <revised bq_smc.py> \
        --bench reviews/BQ_SMC_STABILITY_20261127 --out reviews/BQ_L2_RESOLUTION_20261127 [--sizes 102,236,395 --procs 8]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
import bq_smc_stability as BS  # noqa: E402  (design, seeds, response and psi of the benchmark)

MOD = None


def load(path):
    spec = importlib.util.spec_from_file_location("sharpbl.bq_smc_revised", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def job(args):
    module, size, bi, rep, particles = args
    S = load(module)
    d = BS.design()
    rng0 = np.random.default_rng(BS.SEED0)
    y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
    blk = next(b for b in CV.cv_blocks(d.n_t) if int(CV.cv_masks(d, b, 11)[1].sum()) == size)
    train, ver = CV.cv_masks(d, blk, 11)
    x = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)])
    st = S.block_state(d, train, ver, x, y2[train], np.ones(int(train.sum())), 0.5)
    seed = BS.SEED0 + 1000 * 1 + 100 * bi + rep                      # the benchmark's L2 seed (kind index 1)
    t0 = time.perf_counter()
    r = S.smc_block(st, y2[ver], "L2", particles, np.random.default_rng(seed))
    return dict(records=size, replicate=rep, seed=seed, score_loggrid=r["score"], n_resample=r["n_resample"], ess_min=r["ess_min"],
                n_quad=r.get("n_quad", np.nan), seconds=time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--module", required=True)
    ap.add_argument("--bench", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sizes", default="102,236,395")
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--particles", type=int, default=1000)
    ap.add_argument("--procs", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    (out / "bq_smc_revised.py").write_bytes(Path(a.module).read_bytes())
    all_sizes = [int(s) for s in "22,102,236,395".split(",")]             # block index bi as in the benchmark
    sizes = [int(s) for s in a.sizes.split(",")]
    jobs = [(str(out / "bq_smc_revised.py"), s, all_sizes.index(s), r, a.particles) for s in sizes for r in range(a.reps)]
    meta = dict(module_sha256=hashlib.sha256(Path(a.module).read_bytes()).hexdigest(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                bench=str(a.bench), sizes=sizes, reps=a.reps, particles=a.particles)
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    rows = []
    with get_context("fork").Pool(a.procs) as pool:
        for r in pool.imap_unordered(job, jobs):
            rows.append(r)
            pd.DataFrame([r]).to_csv(out / "LOGGRID_REPLICATES.csv", mode="a", header=not (out / "LOGGRID_REPLICATES.csv").exists(), index=False)
            print(r, flush=True)
    lg = pd.DataFrame(rows)
    bench = pd.read_csv(Path(a.bench) / "REPLICATES.csv")
    gl = bench[bench.kind == "L2"][["records", "replicate", "seed", "score"]].rename(columns={"score": "score_gl64"})
    m = lg.merge(gl, on=["records", "replicate", "seed"], how="left")
    m["diff"] = m.score_loggrid - m.score_gl64
    s = m.groupby("records").agg(n=("diff", "count"), diff_mean=("diff", "mean"), diff_sd=("diff", "std"), sd_loggrid=("score_loggrid", "std"),
                                 sd_gl64=("score_gl64", "std"), mean_loggrid=("score_loggrid", "mean"), mean_gl64=("score_gl64", "mean")).reset_index()
    s["diff_se"] = s.diff_sd / np.sqrt(s.n)
    m.to_csv(out / "PAIRED.csv", index=False)
    s.to_csv(out / "SUMMARY.csv", index=False)
    print(s.to_string())


if __name__ == "__main__":
    main()
