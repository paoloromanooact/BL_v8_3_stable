"""BQ-HMI L1: the block score averaged over the posterior draws of psi of the TRAINING fit, on the real T3 design (metadata
only) with a synthetic response. Development measurement (draft rev. 4 §6ter), not a validation.

For each block (default the T3 internal blocks of 22, 102, 236, 395 records, buffer 11): n_chains slice chains of the
L1 training posterior (bq_core.slice_chain; warm-up, kept draws, thinning), and for every kept draw the ANALYTIC
term l(train + block; psi) - l(train; psi) = log p(y_block | y_train, psi). Score = log mean exp(term) over all draws.
Monte Carlo error of the score: batch means computed WITHIN each chain (chain boundaries kept, n_batches per chain),
delta method on the mean of exp(term - max). Also reported: weights ESS and largest share, and the rank R-hat and
bulk/tail ESS of the term (bq_diag) as a check of the chains for this quantity. TERMS.csv keeps every term with its
chain and iteration, for a recount.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_psi_average_check.py --out reviews/BQ_PSI_AVERAGE_20261127
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
from sharpbl import bq_core as B, bq_cv as CV, bq_diag as DG  # noqa: E402
from bq_smc_stability import design  # noqa: E402  (T3 design, metadata only)

SEED0 = 36_400_960             # response: same synthetic y as the SMC benchmark
SEED_CHAINS = 36_400_970       # + 100 * block index + chain


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def batch_mcse_log_mean_exp(terms, chain, n_batches):
    """log mean exp(terms) and its MC SE by batch means within each chain (equal batches; a remainder at the END of a
    chain is dropped from the variance only), delta method."""
    v = np.asarray(terms, float)
    mx = v.max()
    e = np.exp(v - mx)
    est = mx + math.log(e.mean())
    bm = []
    for c in np.unique(chain):
        ec = e[chain == c]
        size = len(ec) // n_batches
        if size < 1:
            return est, np.nan
        bm += [ec[i * size:(i + 1) * size].mean() for i in range(n_batches)]
    bm = np.array(bm)
    return float(est), float(bm.std(ddof=1) / math.sqrt(len(bm)) / e.mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sizes", default="22,102,236,395")
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warm", type=int, default=300)
    ap.add_argument("--keep", type=int, default=500)
    ap.add_argument("--thin", type=int, default=5)
    ap.add_argument("--batches", type=int, default=10)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_core.py", ROOT / "python/sharpbl/bq_cv.py", ROOT / "python/sharpbl/bq_diag.py",
            ROOT / "scripts/bq_smc_stability.py", ROOT / "scripts/bq_woodbury_benchmark.py"]
    meta = dict(status="running", sources_sha256={str(f.relative_to(ROOT)): sha(f) for f in srcs}, seed_response=SEED0, seed_chains=SEED_CHAINS,
                **{k: getattr(a, k) for k in ("sizes", "chains", "warm", "keep", "thin", "batches")},
                note="L1, synthetic response on the real T3 design (metadata only); development measurement, not a validation")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    d = design()
    rng0 = np.random.default_rng(SEED0)
    y = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
    blocks = CV.cv_blocks(d.n_t)
    x0 = np.array([math.log(20), -0.4, math.log(2.1), 0.97, -0.45, math.log(3)])
    rows = []
    for bi, size in enumerate(int(s) for s in a.sizes.split(",")):
        blk = next(b for b in blocks if int(CV.cv_masks(d, b, 11)[1].sum()) == size)
        tr, ve = CV.cv_masks(d, blk, 11)
        dt, dj = CV.subset(d, tr), CV.subset(d, tr | ve)
        t0 = time.perf_counter()
        terms, chain, it = [], [], []
        for c in range(a.chains):
            dr, _, _, hits = B.slice_chain(lambda z: B.log_post(dt, z, y[tr]), x0, a.warm, a.keep, np.random.default_rng(SEED_CHAINS + 100 * bi + c))
            for k, z in enumerate(dr[::a.thin]):
                terms.append(B.loglik(dj, z, y[tr | ve]) - B.loglik(dt, z, y[tr]))
                chain.append(c)
                it.append(k * a.thin)
        terms, chain = np.array(terms), np.array(chain)
        pd.DataFrame(dict(block=str(blk), records=size, chain=chain, iteration=it, term=terms)).to_csv(
            out / "TERMS.csv", mode="a", header=not (out / "TERMS.csv").exists(), index=False)
        est, se = batch_mcse_log_mean_exp(terms, chain, a.batches)
        w = np.exp(terms - terms.max())
        w /= w.sum()
        dg = DG.diagnose(terms.reshape(a.chains, -1))
        rows.append(dict(block=str(blk), records=size, draws=len(terms), score=est, mcse_batch=se, term_sd=float(terms.std()),
                         term_range=float(np.ptp(terms)), ess_weights=float(1 / (w * w).sum()), max_weight=float(w.max()),
                         rhat_term=dg["rhat"], ess_bulk_term=dg["ess_bulk"], ess_tail_term=dg["ess_tail"], diag_status=dg["status"],
                         seconds=time.perf_counter() - t0))
        pd.DataFrame([rows[-1]]).to_csv(out / "SUMMARY.csv", mode="a", header=not (out / "SUMMARY.csv").exists(), index=False)
        print(" ".join(f"{k} {v:.4g}" if isinstance(v, float) else f"{k} {v}" for k, v in rows[-1].items()), flush=True)
    meta.update(status="completed", sources_unchanged=all(sha(ROOT / k) == v for k, v in meta["sources_sha256"].items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
