"""BQ-HMI block score averaged over the posterior draws of psi of the TRAINING fit, with the sequential SMC density at
each draw (draft rev. 4 §6ter.11; numbers of draws, particles and SMC replicates are OPEN). Synthetic only.

1) Training fit: n_chains chains (L1: slice on psi; L2/L3: bq_robust.gibbs with keep_aux, so every kept psi comes with
   its training auxiliary state: lam in L2, the latent tilts in L3), warm-up, kept draws, thinning.
2) Evaluation order: kept draws taken round-robin over the chains (iteration-major), so every checkpoint is balanced.
3) For draw s: R SMC estimates p_s,r with independent seeds (L1: the exact Kalman value, R = 1); log p_s = log-mean-exp
   over r. On a subset fixed beforehand (every `repeat_every`-th kept draw of each chain) R_extra further estimates
   are added for the decomposition "SMC noise within a draw vs variability between draws of psi".
4) Checkpoints (numbers of evaluated draws fixed beforehand, multiples of the number of chains: balanced chain
   prefixes): score = log-mean-exp of log p_s; MC SE by batch means WITHIN each chain on the rescaled densities, with
   every contribution of the score included (batches of nearly equal length); weights ESS. Budget: maximum draws
   (multiple of the chains) and maximum hours, both stopping only at a balanced prefix; at the budget the status is
   score_not_established if MCSE > 0.1 or weights ESS < 100.
5) Every value is saved as soon as it is computed (DRAWS.csv: chain, iteration, chain seed, SMC seeds, log densities,
   resamplings, seconds); TRAINING.npz keeps psi and the auxiliary states; CHECKPOINTS.csv; DECOMPOSITION.csv; META.

Designs: the real T3 design (metadata only) or --synthetic-design for small checks. Model (27 Nov, for the comparison
runs): --model M0 (no beta) or MQ, --v none or hn20 (half-normal 20 on sigma_v), the same prior otherwise. Block:
--block-id k (index into bq_cv.cv_blocks, explicit) or, by default, the first block with --size records. Responses:
--response bench (the SMC benchmark's synthetic responses, as before) or a generator G0-G4 of the identifiability pilot
(G0 added here: beta = 0, no v; G1 beta = -5; G2 v AR(1); G3 both; G4 v tied to activity), replicate --response-rep,
seed 36_405_000 + 1000 * generator index + response-rep, Gaussian noise; L3 folds them into (-90, 90]. Deadline:
--deadline YYYY-MM-DDTHH:MM (local time) is absolute and covers the fit: before each chain of the training fit the run
stops (status deadline_in_fit, nothing scored) if the remaining time is shorter than the longest chain so far (the
first chain needs --deadline-margin-min); in the SMC phase it stops at the first balanced prefix with less than
--deadline-margin-min minutes left. Fit and SMC seconds are recorded separately. --stop-when-established N (27 Nov,
weekend gate): stop at the first checkpoint with at least N draws where MCSE <= 0.1 and weights ESS >= 100, otherwise go
on to the next checkpoint up to the budget; the fit and every contribution computed so far are kept in the same run. Seeds: chain c 36_403_000 + 10 c; SMC estimate r of evaluated draw i
36_403_500 + 100_000 r + i. The repeated subset is every `repeat_every`-th thinned draw of each chain (position
0, repeat_every, 2 repeat_every, ... within the chain).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_cv_psi_smc.py --kind L2 --out <dir> [--size 395 --chains 4 --warm 300
        --keep 600 --thin 6 --checkpoints 25,50,100,200 --budget-draws 400 --budget-hours 6 --particles 1000 --smc-reps 1]
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dtm
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

SEED_CHAIN, SEED_SMC, SEED_RESP = 36_403_000, 36_403_500, 36_405_000
GENS = ("G0", "G1", "G2", "G3", "G4")
MCSE_MAX, ESS_W_MIN = 0.1, 100.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lme(v):
    v = np.asarray(v, float)
    m = v.max()
    return float(m + math.log(np.exp(v - m).mean()))


def score_and_mcse(logp, chain, n_batches=10):
    """log-mean-exp of the per-draw log densities and its MC SE by batch means within chains, on the rescaled densities
    exp(log p - max). EVERY contribution of the score enters the MC SE (Codex, 27 Nov): each chain is split into
    contiguous batches of nearly equal length (np.array_split, no tail dropped) and the variance of the overall mean is
    B/(B-1) sum_b (n_b/N)^2 (mean_b - mean)^2, which reduces to the usual batch-means formula for equal batches."""
    logp, chain = np.asarray(logp, float), np.asarray(chain)
    mx = logp.max()
    e = np.exp(logp - mx)
    ybar = e.mean()
    est = mx + math.log(ybar)
    w = e / e.sum()
    essw = float(1 / (w * w).sum())
    sizes, means = [], []
    for c in np.unique(chain):
        ec = e[chain == c]
        nb = min(n_batches, len(ec) // 2)
        if nb < 2:
            return float(est), np.nan, essw
        for b in np.array_split(ec, nb):
            sizes.append(len(b))
            means.append(b.mean())
    sizes, means = np.array(sizes, float), np.array(means)
    B, N = len(means), sizes.sum()
    var = B / (B - 1) * float((((sizes / N) ** 2) * (means - ybar) ** 2).sum())
    return float(est), float(math.sqrt(var) / ybar), essw


def fold(y):
    return np.degrees(np.arcsin(np.sin(np.radians(y))))


def setup(a):
    if a.synthetic_design:
        from bq_core_selftest import synth_design
        d = synth_design(np.random.default_rng(36_403_900), n_t=30, n=160)
        blk, buf = (12, 15), 2
    else:
        import bq_smc_stability as BS
        d = BS.design()
        blk, buf = None, 11
    prior = dict(d.prior, sigma_v_hn=20.0) if a.v == "hn20" else dict(d.prior)
    d = dataclasses.replace(d, with_beta=(a.model == "MQ"), with_v=(a.v == "hn20"), prior=prior)
    if a.block_id is not None:
        blk = CV.cv_blocks(d.n_t)[a.block_id]
    elif blk is None:
        blk = next(b for b in CV.cv_blocks(d.n_t) if int(CV.cv_masks(d, b, buf)[1].sum()) == a.size)
    if a.response == "bench":
        rng0 = np.random.default_rng(36_400_960)                     # the SMC benchmark's synthetic responses
        y2 = rng0.normal(0, 25, d.n) + 8 * rng0.standard_t(4, d.n)
        g3 = fold(np.random.default_rng(36_400_961).normal(-5, 70, d.n))
        y = g3 if a.kind == "L3" else y2
    else:
        import bq_identifiability_pilot as IP
        IP.GEN.setdefault("G0", dict(beta=0.0, v=None))
        D = dict(t=d.t, h=d.h, s=d.s, a=d.a, lphi=d.lphi, cell=d.cell, fam=d.fam, n_t=d.n_t)
        y = IP.simulate(D, a.response, np.random.default_rng(SEED_RESP + 1000 * GENS.index(a.response) + a.response_rep))
        y = fold(y) if a.kind == "L3" else y
    train, ver = CV.cv_masks(d, blk, buf)
    return d, blk, train, ver, y


def x_start(kind, with_v):
    x0 = [math.log(20), -0.4, math.log(2.1), 0.9, -0.4, math.log(3)] if kind != "L3" else [math.log(60), 0.0, math.log(5), 0.9, -0.4, math.log(3)]
    return np.array(x0 + ([math.log(5.0), 1.5, 0.3] if with_v else []))


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
    ap.add_argument("--model", choices=("M0", "MQ"), default="MQ")
    ap.add_argument("--v", choices=("none", "hn20"), default="none")
    ap.add_argument("--block-id", type=int)
    ap.add_argument("--response", choices=("bench",) + GENS, default="bench")
    ap.add_argument("--response-rep", type=int, default=0)
    ap.add_argument("--deadline", help="absolute local time YYYY-MM-DDTHH:MM, covering the fit")
    ap.add_argument("--deadline-margin-min", type=float, default=10.0)
    ap.add_argument("--stop-when-established", type=int, default=0, help="minimum draws for the early stop (0: off)")
    a = ap.parse_args()
    deadline = dtm.datetime.fromisoformat(a.deadline).timestamp() if a.deadline else math.inf
    left = lambda: deadline - time.time()                                       # noqa: E731
    if left() <= 60 * a.deadline_margin_min:
        sys.exit("deadline too close: nothing started")
    cps = sorted(int(x) for x in a.checkpoints.split(","))
    if any(c % a.chains for c in cps) or a.budget_draws % a.chains:
        sys.exit("checkpoints and budget must be multiples of the number of chains (balanced chain prefixes)")
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
    x0 = x_start(a.kind, d.with_v)
    meta.update(block=str(blk), records=int(ver.sum()), training_records=int(train.sum()), model=a.model, v=a.v, response=a.response,
                response_seed=None if a.response == "bench" else SEED_RESP + 1000 * GENS.index(a.response) + a.response_rep, deadline=a.deadline)
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    # 1) training fit
    t0 = time.perf_counter()
    psi, aux, cid, it, chain_secs = [], [], [], [], []
    for c in range(a.chains):
        need = max(chain_secs) if chain_secs else 60 * a.deadline_margin_min
        if left() < need:
            meta.update(status="deadline_in_fit", chains_done=c, fit_seconds_per_chain=chain_secs)
            (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
            sys.exit(4)
        tc = time.perf_counter()
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
        chain_secs.append(time.perf_counter() - tc)
    t_fit = time.perf_counter() - t0
    meta.update(fit_seconds=t_fit, fit_seconds_per_chain=chain_secs)
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    np.savez(out / "TRAINING.npz", psi=np.array(psi), chain=np.array(cid), iteration=np.array(it),
             **({"aux": np.array(aux)} if a.kind != "L1" else {}))
    # 2) round-robin order
    per = {c: [i for i in range(len(psi)) if cid[i] == c] for c in range(a.chains)}
    pos = {i: j for c in per for j, i in enumerate(per[c])}               # position of draw i within its chain
    order = [i for row in zip(*per.values()) for i in row]
    rows, logp, chs, cprows = [], [], [], []
    t_start = time.perf_counter()
    status, stop = "running", None
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
        balanced = n_done % a.chains == 0                                    # every chain has the same prefix length
        stop = ("all_draws" if n_done == len(order) else "budget_draws" if n_done >= a.budget_draws else "budget_hours" if hours >= a.budget_hours
                else "deadline" if left() < 60 * a.deadline_margin_min else None)
        last = balanced and stop is not None
        if (n_done in cps and balanced) or last:
            sc, se, essw = score_and_mcse(logp, chs)
            cprows.append(dict(draws=n_done, score=sc, mcse=se, ess_weights=essw, hours=hours))
            pd.DataFrame([cprows[-1]]).to_csv(out / "CHECKPOINTS.csv", mode="a", header=not (out / "CHECKPOINTS.csv").exists(), index=False)
            print(cprows[-1], flush=True)
            if (not last and a.stop_when_established and n_done >= a.stop_when_established and np.isfinite(se)
                    and se <= MCSE_MAX and essw >= ESS_W_MIN):
                stop, last = "established", True
        if last:
            status = "ok" if (np.isfinite(se) and se <= MCSE_MAX and essw >= ESS_W_MIN) else "score_not_established"
            break
    # 3) decomposition on the subset (diagnostic only; the total MC SE is the batch-means one): on ONE common scale
    # (densities divided by exp(max over every replicate of the subset)), per draw i the mean m_i of its R_i SMC
    # estimates and their variance s_i^2. The variance between the m_i still contains SMC noise: the variability
    # between draws of psi is var(m_i) - mean(s_i^2 / R_i) (Codex, 27 Nov). Reported relative to mean(m_i)^2.
    dec = pd.DataFrame(rows)
    sub = dec[dec.n_extra > 0]
    if len(sub):
        vals = [np.array(json.loads(v)) for v in sub.log_density_all]
        M = max(float(v.max()) for v in vals)
        e = [np.exp(v - M) for v in vals]
        m = np.array([x.mean() for x in e])
        s2 = np.array([x.var(ddof=1) for x in e])
        R = np.array([len(x) for x in e], float)
        mm = m.mean()
        between_raw = float(m.var(ddof=1))
        smc_part = float((s2 / R).mean())
        pd.DataFrame([dict(subset_draws=len(sub), replicates_per_draw=float(R.mean()), smc_rel_var_single=float(s2.mean() / mm ** 2),
                           smc_rel_var_in_means=smc_part / mm ** 2, between_means_rel_var_raw=between_raw / mm ** 2,
                           between_psi_rel_var=(between_raw - smc_part) / mm ** 2,
                           smc_log_sd_mean=float(np.mean([np.std(v, ddof=1) for v in vals])))]).to_csv(out / "DECOMPOSITION.csv", index=False)
    meta.update(status="completed", score_status=status, stop_reason=stop, smc_seconds=time.perf_counter() - t_start, draws_scored=len(logp),
                sources_unchanged=all(sha(ROOT / k) == v for k, v in meta["sources_sha256"].items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    main()
