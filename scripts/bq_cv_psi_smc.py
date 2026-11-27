"""BQ-HMI block score averaged over the posterior draws of psi of the TRAINING fit, with the sequential SMC density at
each draw (draft rev. 4 §6ter.11; numbers of draws, particles and SMC replicates are OPEN). Synthetic only.

1) Training fit: n_chains chains (L1: slice on psi; L2/L3: bq_robust.gibbs with keep_aux, so every kept psi comes with
   its training auxiliary state: lam in L2, the latent tilts in L3), warm-up, kept draws, thinning.
2) Evaluation order: kept draws taken round-robin over the chains (iteration-major), so every checkpoint is balanced.
3) For draw s: R SMC estimates p_s,r with independent seeds (L1: the exact Kalman value, R = 1); log p_s = log-mean-exp
   over r. On a subset fixed beforehand (every `repeat_every`-th kept draw of each chain) R_extra further estimates
   are added for the decomposition "SMC noise within a draw vs variability between draws of psi".
4) Checkpoints (numbers of evaluated draws fixed beforehand): score = log-mean-exp of log p_s; MC SE by batch means
   WITHIN each chain on the rescaled densities exp(log p_s - max), delta method; weights ESS. Budget: maximum draws and
   maximum hours; at the budget the status is score_not_established if MCSE > 0.1 or weights ESS < 100.
5) Every value is saved as soon as it is computed (DRAWS.csv: chain, iteration, chain seed, SMC seeds, log densities,
   resamplings, seconds); TRAINING.npz keeps psi and the auxiliary states; CHECKPOINTS.csv; DECOMPOSITION.csv; META.

Designs: the real T3 design (metadata only) with the synthetic responses of the SMC benchmark, block of `size` records,
or --synthetic-design for small checks. Seeds: chain c 36_403_000 + 10 c; SMC estimate r of evaluated draw i
36_403_500 + 100_000 r + i. The repeated subset is every `repeat_every`-th thinned draw of each chain (position
0, repeat_every, 2 repeat_every, ... within the chain).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_cv_psi_smc.py --kind L2 --out <dir> [--size 395 --chains 4 --warm 300
        --keep 600 --thin 6 --checkpoints 25,50,100,200 --budget-draws 400 --budget-hours 6 --particles 1000 --smc-reps 1]
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
from sharpbl import bq_core as B, bq_cv as CV, bq_robust as RB, bq_smc as S  # noqa: E402

SEED_CHAIN, SEED_SMC = 36_403_000, 36_403_500
MCSE_MAX, ESS_W_MIN = 0.1, 100.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lme(v):
    v = np.asarray(v, float)
    m = v.max()
    return float(m + math.log(np.exp(v - m).mean()))


def score_and_mcse(logp, chain, n_batches=10):
    """log-mean-exp of the per-draw log densities and its MC SE by batch means within chains (rescaled densities)."""
    logp, chain = np.asarray(logp, float), np.asarray(chain)
    mx = logp.max()
    e = np.exp(logp - mx)
    est = mx + math.log(e.mean())
    bm = []
    for c in np.unique(chain):
        ec = e[chain == c]
        nb = min(n_batches, len(ec) // 2)
        if nb < 2:
            return est, np.nan, float(1 / ((e / e.sum()) ** 2).sum())
        size = len(ec) // nb
        bm += [ec[i * size:(i + 1) * size].mean() for i in range(nb)]
    w = e / e.sum()
    return float(est), float(np.std(bm, ddof=1) / math.sqrt(len(bm)) / e.mean()), float(1 / (w * w).sum())


def setup(a):
    if a.synthetic_design:
        from bq_core_selftest import synth_design
        d = synth_design(np.random.default_rng(36_403_900), n_t=30, n=160)
        blk = (12, 15)
    else:
        import bq_smc_stability as BS
        d = BS.design()
        blk = next(b for b in CV.cv_blocks(d.n_t) if int(CV.cv_masks(d, b, 11)[1].sum()) == a.size)
    rng0 = np.random.default_rng(36_400_960)                         # the SMC benchmark's synthetic responses
    y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
    th = np.random.default_rng(36_400_961).normal(-5, 70, d.n)
    g3 = np.degrees(np.arcsin(np.sin(np.radians(th))))
    train, ver = CV.cv_masks(d, blk, 11 if not a.synthetic_design else 2)
    y = g3 if a.kind == "L3" else y2
    return d, blk, train, ver, y


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", choices=("L1", "L2", "L3"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=395)
    ap.add_argument("--synthetic-design", action="store_true")
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warm", type=int, default=300)
    ap.add_argument("--keep", type=int, default=600)
    ap.add_argument("--thin", type=int, default=6)
    ap.add_argument("--checkpoints", default="25,50,100,200")
    ap.add_argument("--budget-draws", type=int, default=400)
    ap.add_argument("--budget-hours", type=float, default=6.0)
    ap.add_argument("--particles", type=int, default=1000)
    ap.add_argument("--smc-reps", type=int, default=1)
    ap.add_argument("--repeat-every", type=int, default=10)
    ap.add_argument("--extra-reps", type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_smc.py", ROOT / "python/sharpbl/bq_core.py", ROOT / "python/sharpbl/bq_robust.py",
            ROOT / "python/sharpbl/bq_cv.py"]
    meta = dict(status="running", sources_sha256={str(p.relative_to(ROOT)): sha(p) for p in srcs}, args=vars(a), seed_chain=SEED_CHAIN, seed_smc=SEED_SMC,
                note="development; synthetic responses; numbers of draws/particles/replicates open (draft §6ter.11)")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    d, blk, train, ver, y = setup(a)
    dt = CV.subset(d, train)
    x0 = np.array([math.log(20), -0.4, math.log(2.1), 0.9, -0.4, math.log(3)]) if a.kind != "L3" else \
        np.array([math.log(60), 0.0, math.log(5), 0.9, -0.4, math.log(3)])
    # 1) training fit
    t0 = time.perf_counter()
    psi, aux, cid, it = [], [], [], []
    for c in range(a.chains):
        rng = np.random.default_rng(SEED_CHAIN + 10 * c)
        xs = x0 + rng.normal(0.0, 0.3, len(x0))
        if a.kind == "L1":
            dr, _, _, _ = B.slice_chain(lambda z: B.log_post(dt, z, y[train]), xs, a.warm, a.keep, rng)
            ax = [None] * len(dr)
        else:
            g = RB.gibbs(dt, y[train], xs, a.warm, a.keep, rng, kind=a.kind, keep_theta=False, keep_aux=True,
                         theta_init=RB.preimage_init(y[train], "identity", rng) if a.kind == "L3" else None)
            dr, ax = g["psi"], g["aux"]
        for k in range(a.thin - 1, len(dr), a.thin):
            psi.append(dr[k])
            aux.append(ax[k])
            cid.append(c)
            it.append(a.warm + k + 1)
    t_fit = time.perf_counter() - t0
    np.savez(out / "TRAINING.npz", psi=np.array(psi), chain=np.array(cid), iteration=np.array(it),
             **({"aux": np.array(aux)} if a.kind != "L1" else {}))
    # 2) round-robin order
    per = {c: [i for i in range(len(psi)) if cid[i] == c] for c in range(a.chains)}
    pos = {i: j for c in per for j, i in enumerate(per[c])}               # position of draw i within its chain
    order = [i for row in zip(*per.values()) for i in row]
    cps = sorted(int(x) for x in a.checkpoints.split(","))
    rows, logp, chs, cprows = [], [], [], []
    t_start = time.perf_counter()
    status = "running"
    for n_done, i in enumerate(order, start=1):
        x, ax = psi[i], aux[i]
        if a.kind == "L1":
            st = S.block_state(d, train, ver, x, y[train])
            vals, seeds, res = [S.smc_block(st, y[ver], "L1")["score"]], [-1], [0]
        else:
            if a.kind == "L2":
                st = S.block_state(d, train, ver, x, y[train], ax, (4.0 - 2.0) / 4.0)     # training lam, scale (nu-2)/nu
            else:
                st = S.block_state(d, train, ver, x, ax)                               # training latent tilts
            in_subset = pos[i] % a.repeat_every == 0
            nrep = a.smc_reps + (a.extra_reps if in_subset else 0)
            vals, seeds, res = [], [], []
            for r in range(nrep):
                seed = SEED_SMC + 100_000 * r + i
                rr = S.smc_block(st, y[ver], a.kind, a.particles, np.random.default_rng(seed))
                vals.append(rr["score"])
                seeds.append(seed)
                res.append(rr["n_resample"])
        main_lp = lme(vals[:max(1, a.smc_reps)])
        rows.append(dict(order=n_done, draw=i, chain=cid[i], iteration=it[i], chain_seed=SEED_CHAIN + 10 * cid[i], smc_seeds=json.dumps(seeds),
                         log_density=main_lp, log_density_all=json.dumps(vals), n_main=max(1, a.smc_reps), n_extra=len(vals) - max(1, a.smc_reps),
                         resamplings=json.dumps(res), seconds=time.perf_counter() - t_start))
        pd.DataFrame([rows[-1]]).to_csv(out / "DRAWS.csv", mode="a", header=not (out / "DRAWS.csv").exists(), index=False)
        logp.append(main_lp)
        chs.append(cid[i])
        hours = (time.perf_counter() - t_start) / 3600
        last = n_done == len(order) or n_done >= a.budget_draws or hours >= a.budget_hours
        if n_done in cps or last:
            sc, se, essw = score_and_mcse(logp, chs)
            cprows.append(dict(draws=n_done, score=sc, mcse=se, ess_weights=essw, hours=hours))
            pd.DataFrame([cprows[-1]]).to_csv(out / "CHECKPOINTS.csv", mode="a", header=not (out / "CHECKPOINTS.csv").exists(), index=False)
            print(cprows[-1], flush=True)
        if last:
            status = "ok" if (np.isfinite(se) and se <= MCSE_MAX and essw >= ESS_W_MIN) else "score_not_established"
            break
    # 3) decomposition on the subset: SMC noise within a draw vs variability between draws (density scale, relative)
    dec = pd.DataFrame(rows)
    sub = dec[dec.n_extra > 0]
    if len(sub):
        within, means = [], []
        for v in sub.log_density_all:
            v = np.array(json.loads(v))
            m = v.max()
            e = np.exp(v - m)
            within.append(e.var(ddof=1) / e.mean() ** 2)              # relative variance of one SMC estimate
            means.append(m + math.log(e.mean()))
        lm = np.array(means)
        em = np.exp(lm - lm.max())
        pd.DataFrame([dict(subset_draws=len(sub), smc_rel_var_mean=float(np.mean(within)), between_rel_var=float(em.var(ddof=1) / em.mean() ** 2),
                           smc_log_sd_mean=float(np.mean([np.std(json.loads(v), ddof=1) for v in sub.log_density_all])),
                           between_log_sd=float(lm.std(ddof=1)))]).to_csv(out / "DECOMPOSITION.csv", index=False)
    meta.update(status="completed", score_status=status, fit_seconds=t_fit, block=str(blk), records=int(ver.sum()),
                sources_unchanged=all(sha(ROOT / k) == v for k, v in meta["sources_sha256"].items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
