"""Concurrency probe before a parallel run (rule of 27 Nov: no throughput collapse from memory-bandwidth contention).

Runs the same short L1 slice chain (T3 design, synthetic response, no v) in 1 process, then in P processes at once,
and reports the seconds per iteration of each. Prints the recommended number of processes: the P with the largest TOTAL
throughput P x (single-process time / per-process time), 1 included. (Until 27 Nov 13:00 the rule required a
per-process speed >= 60 % of the single process, which chose 1 process although 12 gave 3.8 times the throughput.)

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_concurrency_probe.py [--procs 16,8,4 --iters 30]
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B  # noqa: E402



def chain(args):
    iters, seed = args
    import bq_identifiability_pilot as IP
    D = IP.design_arrays()
    y = IP.simulate(D, "G1", np.random.default_rng(seed))
    d = B.Design(t=D["t"], h=D["h"], s=D["s"], a=D["a"], lphi=D["lphi"], cell=D["cell"], fam=D["fam"], n_t=D["n_t"], n_cell=4,
                 prior=dict(B.PRIOR, q_sd=0.5))
    x0 = np.array([math.log(20.0), -0.4, math.log(2.0), 0.9, -0.4, math.log(3.0)])
    t0 = time.perf_counter()
    B.slice_chain(lambda z: B.log_post(d, z, y), x0, 0, iters, np.random.default_rng(seed + 1), w0=0.5)
    return (time.perf_counter() - t0) / iters


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--procs", default="16,8,4")
    ap.add_argument("--iters", type=int, default=30)
    a = ap.parse_args()
    ctx = get_context("fork")
    solo = chain((a.iters, 1))
    print(f"1 process: {solo:.3f} s/iteration", flush=True)
    best, best_tp = 1, 1.0
    for p in sorted({int(x) for x in a.procs.split(",")}, reverse=True):
        with ctx.Pool(p) as pool:
            t = pool.map(chain, [(a.iters, 1 + k) for k in range(p)])
        ratio = solo / float(np.mean(t))
        tp = p * ratio
        print(f"{p} processes: {np.mean(t):.3f} s/iteration per process, speed ratio {ratio:.2f}, total throughput {tp:.2f}", flush=True)
        if tp > best_tp:
            best, best_tp = p, tp
    print(f"RECOMMENDED_PROCS {best}")


if __name__ == "__main__":
    main()
