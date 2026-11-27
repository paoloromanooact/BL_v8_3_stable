"""BQ-HMI S-ID sizing pilot (development, NOT the registered study): how many saved draws per chain are needed.

Generators G1-G4 and the T3 design (metadata only) of scripts/bq_identifiability_pilot.py; synthetic responses. For
each generator and replicate, the paired L1 fits MQ without v and MQ with v (sigma_v HN 20), rev. 4 priors (q SD 0.5).
Four chains per fit, 2000 warm-up iterations (slice widths adapted only there), 5000 saved; each chain starts from the
pilot's point plus a seeded N(0, 0.5^2) jitter on every sampling coordinate. One process and one thread per chain;
each chain is saved (CHAINS/*.npz) as soon as it ends.
Diagnostics at 1000, 2000 and 5000 saved draws per chain (the first n of every chain), with bq_diag (gate: >= 4
chains, rank R-hat bulk and folded <= 1.01, bulk and tail ESS >= 400): every sampling coordinate, the Rao-Blackwellised
conditional mean of beta, and the log Savage-Dickey ordinate log p(beta = 0 | psi, y) that enters the Bayes factor.
Also the Savage-Dickey log BF_0Q with its MC SE by batch means within chains (10 batches per chain) on the rescaled
ordinates; P(beta < 0) as the mean of the per-draw contribution Phi(-m_s / sqrt(v_s)) actually used, with its MC SE by
the same within-chain batch means (chain order and boundaries kept); the threshold_uncertain flags of the approved
rule (closed interval estimate +- 2 MCSE reaching or crossing 0.95 for P(beta < 0) or -log 10 for log BF_0Q); and
seconds per chain.
Seeds (zone separate from the study, 36_401_000 - 36_404_999): response 36_401_000 + 1000 g + 100 r + 99; chain
36_401_000 + 1000 g + 100 r + 10 f + c (g 0-3, r < 9, f 0-1, c 0-3).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_sizing_pilot.py --out reviews/BQ_SIZING_PILOT_<date> [--reps 2 --procs 16]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_diag as DG  # noqa: E402
import bq_identifiability_pilot as IP  # noqa: E402  (generators, design arrays)

SEED0 = 36_401_000
GENS = ("G1", "G2", "G3", "G4")
FITS = (("MQ_no_v", False, None), ("MQ_v_hn20", True, 20.0))
CHECKPOINTS = (1000, 2000, 5000)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def response(D, g, r):
    return IP.simulate(D, GENS[g], np.random.default_rng(SEED0 + 1000 * g + 100 * r + 99))


def make_design(D, with_v, sv):
    prior = dict(B.PRIOR, q_sd=0.5, sigma_v_hn=sv or 20.0)
    return B.Design(t=D["t"], h=D["h"], s=D["s"], a=D["a"], lphi=D["lphi"], cell=D["cell"], fam=D["fam"], n_t=D["n_t"], n_cell=4,
                    with_v=with_v, prior=prior)


def run_chain(job):
    g, r, f, c, warm, keep, out = job
    os.environ["OMP_NUM_THREADS"] = "1"
    path = Path(out) / "CHAINS" / f"{GENS[g]}_r{r}_{FITS[f][0]}_c{c}.npz"
    if path.exists():
        return str(path)
    D = IP.design_arrays()
    y = response(D, g, r)
    name, with_v, sv = FITS[f]
    d = make_design(D, with_v, sv)
    seed = SEED0 + 1000 * g + 100 * r + 10 * f + c
    rng = np.random.default_rng(seed)
    x0 = np.array([math.log(20.0), -0.4, math.log(2.0), 0.9, -0.4, math.log(3.0)] + ([math.log(5.0), 1.5, 0.3] if with_v else []))
    x0 = x0 + rng.normal(0.0, 0.5, len(x0))
    t0 = time.perf_counter()
    dr, lk, w, hits = B.slice_chain(lambda z: B.log_post(d, z, y), x0, warm, keep, rng)
    t1 = time.perf_counter()
    cond = B.beta_conditionals(d, dr, y)
    np.savez(path, draws=dr, cond=cond, seconds_chain=t1 - t0, seconds_cond=time.perf_counter() - t1, hits=hits, seed=seed, x0=x0,
             names=np.array(d.names()))
    return str(path)


def log_ordinate(cond):
    return -0.5 * cond[:, 0] ** 2 / cond[:, 1] - 0.5 * np.log(2 * math.pi * cond[:, 1])


def sd_bf(cond_chains, beta_sd, n_batches=10):
    """Savage-Dickey log BF_0Q over all chains and its MC SE by batch means within chains (rescaled ordinates)."""
    lo = [log_ordinate(c) for c in cond_chains]
    mx = max(float(v.max()) for v in lo)
    e = [np.exp(v - mx) for v in lo]
    allm = np.concatenate(e).mean()
    bm = []
    for ec in e:
        size = len(ec) // n_batches
        bm += [ec[i * size:(i + 1) * size].mean() for i in range(n_batches)]
    se = float(np.std(bm, ddof=1) / math.sqrt(len(bm)) / allm)
    prior0 = -0.5 * math.log(2 * math.pi) - math.log(beta_sd)
    return mx + math.log(allm) - prior0, se


def batch_mean_se(chains, n_batches=10):
    """Mean over all chains of per-draw values and its MC SE by batch means within each chain."""
    allv = np.concatenate(chains)
    bm = []
    for v in chains:
        size = len(v) // n_batches
        bm += [v[i * size:(i + 1) * size].mean() for i in range(n_batches)]
    return float(allv.mean()), float(np.std(bm, ddof=1) / math.sqrt(len(bm)))


def uncertain(est, se, thr):
    """Approved rule: the closed interval est +- 2 se reaches or crosses thr."""
    return bool(est - 2 * se <= thr <= est + 2 * se)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--warm", type=int, default=2000)
    ap.add_argument("--keep", type=int, default=5000)
    ap.add_argument("--procs", type=int, default=16)
    ap.add_argument("--gens", default="0,1,2,3")
    a = ap.parse_args()
    out = Path(a.out)
    resume = out.exists()
    (out / "CHAINS").mkdir(parents=True, exist_ok=True)
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_core.py", ROOT / "python/sharpbl/bq_diag.py", ROOT / "scripts/bq_identifiability_pilot.py",
            ROOT / "scripts/bq_woodbury_benchmark.py"]
    src_sha = {str(p.relative_to(ROOT)): sha(p) for p in srcs}
    if resume:
        old = json.loads((out / "META.json").read_text())
        if old["sources_sha256"] != src_sha:
            sys.exit("resume refused: sources changed since the first launch")
    else:
        (out / "SOURCES").mkdir()
        for p in srcs:
            (out / "SOURCES" / p.name).write_bytes(p.read_bytes())
    meta = dict(status="running", sources_sha256=src_sha, seed0=SEED0, reps=a.reps, warm=a.warm, keep=a.keep, procs=a.procs, gens=a.gens,
                fits=[f[0] for f in FITS], checkpoints=CHECKPOINTS,
                note="sizing pilot, development (not the registered study); synthetic responses on the T3 design, metadata only")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    gens = [int(x) for x in a.gens.split(",")]
    jobs = [(g, r, f, c, a.warm, a.keep, str(out)) for g in gens for r in range(a.reps) for f in range(len(FITS)) for c in range(4)]
    jobs.sort(key=lambda j: -j[2])                       # the slower v fits first
    with get_context("fork").Pool(a.procs) as pool:
        for p in pool.imap_unordered(run_chain, jobs):
            print("done", Path(p).name, flush=True)
    rows, bfs = [], []
    for g in gens:
        for r in range(a.reps):
            for f, (name, with_v, sv) in enumerate(FITS):
                zs = [np.load(out / "CHAINS" / f"{GENS[g]}_r{r}_{name}_c{c}.npz") for c in range(4)]
                names = list(zs[0]["names"])
                secs = float(np.mean([z["seconds_chain"] for z in zs]))
                for n in CHECKPOINTS:
                    q = {nm: np.stack([z["draws"][:n, i] for z in zs]) for i, nm in enumerate(names)}
                    q["beta_cond_mean"] = np.stack([z["cond"][:n, 0] for z in zs])
                    q["log_sd_ordinate"] = np.stack([log_ordinate(z["cond"][:n]) for z in zs])
                    for nm, ch in q.items():
                        dg = DG.diagnose(ch)
                        rows.append(dict(gen=GENS[g], rep=r, fit=name, draws_per_chain=n, quantity=nm, **dg))
                    bf, se = sd_bf([z["cond"][:n] for z in zs], 10.0)
                    pn, pse = batch_mean_se([ndtr(-z["cond"][:n, 0] / np.sqrt(z["cond"][:n, 1])) for z in zs])
                    bfs.append(dict(gen=GENS[g], rep=r, fit=name, draws_per_chain=n, log_bf0q=bf, mcse=se, p_beta_neg=pn, p_beta_neg_mcse=pse,
                                    uncertain_p=uncertain(pn, pse, 0.95), uncertain_bf=uncertain(bf, se, -math.log(10.0)),
                                    seconds_per_chain_full=secs))
    diag = pd.DataFrame(rows)
    diag.to_csv(out / "DIAGNOSTICS.csv", index=False)
    pd.DataFrame(bfs).to_csv(out / "BAYES_FACTORS.csv", index=False)
    summ = diag.groupby(["fit", "draws_per_chain"]).agg(fits=("passes", "size"), passes=("passes", "sum"), rhat_max=("rhat", "max"),
                                                        ess_bulk_min=("ess_bulk", "min"), ess_tail_min=("ess_tail", "min")).reset_index()
    summ.to_csv(out / "SUMMARY.csv", index=False)
    meta.update(status="completed", sources_unchanged=all(sha(ROOT / k) == v for k, v in src_sha.items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(summ.to_string())
    print(pd.DataFrame(bfs).to_string())


if __name__ == "__main__":
    main()
