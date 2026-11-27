"""BQ-HMI: cost and replicate stability of the sequential block score (bq_smc) on the REAL T3 design (metadata only:
CR, hemisphere, latitude, activity, flux, family; no observed tilt) with a SYNTHETIC response, at fixed psi.
Draft rev. 4 §6ter.10, not frozen. Development measurement, not a validation and not a result on the Sun.

For blocks of increasing size (default the T3 internal blocks of 22, 102, 236, 395 records, buffer 11):
- L1: sequential Kalman vs the analytic block density (exactness at scale);
- L2: R independent SMC replicates with N particles (training precisions = 1, synthetic t4 response);
- L3: R replicates (synthetic latent tilts with sigma0 70, folded; training latent tilts = the true synthetic ones).
Per block and likelihood: score mean, SD and SE between replicates, resamplings, minimum ESS, max certified T/S of the
SEQUENTIAL steps (L3; the rejuvenation draws are not included), seconds per replicate. At start: output directory,
snapshot of the sources with SHA-256 (SOURCES/) and META with status running; every replicate is appended to
REPLICATES.csv as soon as it ends (Codex review of the benchmark); SUMMARY and the final META at the end.
L2 uses the 64-node discrete precision measure: the replicate spread is the Monte Carlo variability at 64 nodes, not
the quadrature error (to be checked separately on tail cases). Seeds: 36_400_960 + 1000 * likelihood index + 100 * block index + replicate, with CANONICAL indices (L1 0, L2 1, L3 2;
blocks of 22/102/236/395 records 0/1/2/3), independent of the --kinds and --sizes lists (fixed on 27 Nov: a run with
--sizes 395 alone had used block index 0, unpaired with the full benchmark).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_smc_stability.py --out reviews/BQ_SMC_STABILITY_<date> [--reps 8] [--particles 1000]
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
from sharpbl import bq_core as B, bq_cv as CV, bq_smc as S  # noqa: E402
import bq_woodbury_benchmark as W  # noqa: E402  (design columns of the T3 catalogue, metadata only)

SEED0 = 36_400_960
KIND_INDEX = {"L1": 0, "L2": 1, "L3": 2}
SIZE_INDEX = {22: 0, 102: 1, 236: 2, 395: 3}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def design():
    dd = W.design()
    t_ = dd.CR.to_numpy() - dd.CR.min()
    hem = (dd.hemisphere.to_numpy() == "S").astype(int)
    _, fam = np.unique(dd.family_id.to_numpy(), return_inverse=True)
    return B.Design(t=t_, h=hem, s=dd.sinlat.to_numpy(), a=dd.A_monthly.to_numpy() - 1.0, lphi=np.log10(dd.phi.to_numpy() / 1e21),
                    cell=(dd.cyc.to_numpy() == 25).astype(int) * 2 + hem, fam=fam, n_t=int(t_.max()) + 1, n_cell=4)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--particles", type=int, default=1000)
    ap.add_argument("--sizes", default="22,102,236,395", help="T3 block sizes to use (records)")
    ap.add_argument("--kinds", default="L1,L2,L3")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_smc.py", ROOT / "python/sharpbl/bq_core.py", ROOT / "python/sharpbl/bq_cv.py",
            ROOT / "python/sharpbl/bq_cvpred.py", ROOT / "scripts/bq_woodbury_benchmark.py"]
    (out / "SOURCES").mkdir(parents=True)
    for f in srcs:
        (out / "SOURCES" / f.name).write_bytes(f.read_bytes())
    src_sha = {str(f.relative_to(ROOT)): sha(f) for f in srcs}
    meta = dict(status="running", sources_sha256=src_sha, seed0=SEED0, reps=a.reps, particles=a.particles, sizes=a.sizes, kinds=a.kinds,
                note="synthetic response on the real T3 design (metadata only); development measurement at fixed psi, not a validation")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    rep_csv = out / "REPLICATES.csv"

    def save(row):
        pd.DataFrame([row]).to_csv(rep_csv, mode="a", header=not rep_csv.exists(), index=False)
    d = design()
    blocks = CV.cv_blocks(d.n_t)
    want = [int(s) for s in a.sizes.split(",")]
    sizes = {int(CV.cv_masks(d, b, 11)[1].sum()): b for b in blocks}
    chosen = [(n, sizes[n]) for n in want]
    rng0 = np.random.default_rng(SEED0)
    y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)                  # synthetic L1/L2 response
    th = np.random.default_rng(SEED0 + 1).normal(-5, 70, d.n)                  # synthetic latent tilts (L3)
    g3 = np.degrees(np.arcsin(np.sin(np.radians(th))))
    x = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)])
    x3 = np.array([math.log(70), 0.0, math.log(5), 0.97, -0.45, math.log(3)])
    rows = []
    for bi, (n, blk) in enumerate(chosen):
        train, ver = CV.cv_masks(d, blk, 11)
        for li, kind in enumerate(a.kinds.split(",")):
            if kind == "L1":
                st = S.block_state(d, train, ver, x, y2[train])
                t0 = time.perf_counter()
                r = S.smc_block(st, y2[ver], "L1")
                sec = time.perf_counter() - t0
                an = B.loglik(CV.subset(d, train | ver), x, y2[train | ver]) - B.loglik(CV.subset(d, train), x, y2[train])
                rows.append(dict(kind=kind, block=str(blk), records=n, D=st["D"], replicate=0, particles=1, seed=-1, score=r["score"], analytic=an,
                                 n_resample=0, ess_min=1.0, max_tail_ratio_sequential=0.0, seconds=sec))
                save(rows[-1])
                continue
            if kind == "L2":
                st = S.block_state(d, train, ver, x, y2[train], np.ones(int(train.sum())), 0.5)
                yv = y2[ver]
            else:
                st = S.block_state(d, train, ver, x3, th[train])
                yv = g3[ver]
            for rep in range(a.reps):
                seed = SEED0 + 1000 * KIND_INDEX[kind] + 100 * SIZE_INDEX[n] + rep
                t0 = time.perf_counter()
                r = S.smc_block(st, yv, kind, a.particles, np.random.default_rng(seed))
                rows.append(dict(kind=kind, block=str(blk), records=n, D=st["D"], replicate=rep, particles=a.particles, seed=seed, score=r["score"],
                                 analytic=np.nan, n_resample=r["n_resample"], ess_min=r["ess_min"],
                                 max_tail_ratio_sequential=r["max_tail_ratio"], seconds=time.perf_counter() - t0))
                save(rows[-1])
                print(f"{kind} {n:4d} rep {rep}: {r['score']:.4f} ({rows[-1]['seconds']:.1f} s, {r['n_resample']} resamplings)", flush=True)
    t = pd.DataFrame(rows)
    g = t.groupby(["kind", "records"]).agg(D=("D", "first"), n=("score", "size"), mean=("score", "mean"), sd=("score", "std"),
                                           analytic=("analytic", "first"), resamplings=("n_resample", "mean"), ess_min=("ess_min", "min"),
                                           max_tail_ratio_sequential=("max_tail_ratio_sequential", "max"), seconds=("seconds", "mean")).reset_index()
    g["se"] = g.sd / np.sqrt(g.n)
    g.to_csv(out / "SUMMARY.csv", index=False)
    meta.update(status="completed", psi_L1_L2=x.tolist(), psi_L3=x3.tolist(), sources_unchanged=all(sha(ROOT / k) == v for k, v in src_sha.items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(g.to_string())


if __name__ == "__main__":
    main()
