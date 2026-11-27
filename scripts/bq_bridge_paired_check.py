"""BQ-HMI bridge: paired Monte Carlo SE of D = log BF_0Q(bridge) - log BF_0Q(Savage-Dickey) and the effect of fitting
the bridge proposal on the same chains (Codex, 27 Nov). Synthetic only (the small design of bq_bridge_selftest test 4).

R independent replicates; in each, new MQ and M0 chains (2 x (300 + 1500) slice draws) and two bridges per model on
the SAME chains and the same proposal-draw seed:
- adapted: normal proposal fitted on the first halves of the chains (the estimator in use);
- fixed: normal proposal fitted once on an independent reference run of the same model (no adaptation).
Savage-Dickey on every 5th MQ draw. Per replicate: D, the paired SE (bq_bridge.paired_difference_se) and the naive
unpaired SE. Summary per variant: mean of D, empirical sd of D over replicates, mean predicted paired SE, their ratio
and the share of replicates with |D - mean D| <= 2 SE. The predicted SE is adequate if the ratio is near 1; the
adaptation effect is the difference between the variants (empirical sd and mean of D).

Seeds (zone 36_411_000-939; outside 36_405_000-36_409_999 of the weekend generators G0-G4): reference runs 36_411_000 + k (MQ) and 36_411_050 + k (M0); replicate r chains
36_411_100 + 10 r + k (MQ) and 36_411_500 + 10 r + k (M0), proposal draws 36_411_900 + r (MQ) and 36_411_950 + r (M0),
distinct streams per model (Codex, 27 Nov; the same seed for the fixed and adapted variants of one model), r < 40.
Also reported: the SE with the fixed-point factor 1 / (1 - h'(log r)) of each bridge (paired_difference_se(fixed_point=True)).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_bridge_paired_check.py --out <dir> [--reps 30 --procs 6]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_bridge as BR, bq_core as B  # noqa: E402

SEED = 36_400_501                                   # design and response of bq_bridge_selftest test 4
XF = np.array([2.5, -0.4, 1.0, 0.8, -0.3, 0.7])
WARM, KEEP, SD_STEP = 300, 1500, 5


def problem():
    import bq_core_selftest as T
    dq = T.synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150)
    d0 = T.synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150, with_beta=False)
    yv = np.random.default_rng(SEED + 3).multivariate_normal(dq.X[:, :4] @ np.array([20, 22, 18, 25.0]) - 4.0 * dq.a * dq.s,
                                                              T.dense_cov(dq, B.unpack(dq, XF)))
    return dq, d0, yv


def chains(d, yv, seed0):
    return [B.slice_chain(lambda z: B.log_post(d, z, yv), XF, WARM, KEEP, np.random.default_rng(seed0 + k))[0] for k in range(2)]


def reference(_):
    dq, d0, yv = problem()
    out = {}
    for name, d, s0 in (("MQ", dq, 36_411_000), ("M0", d0, 36_411_050)):
        dr = np.concatenate([B.slice_chain(lambda z: B.log_post(d, z, yv), XF, WARM, 3000, np.random.default_rng(s0 + k))[0] for k in range(2)])
        out[name] = (dr.mean(0), np.cov(dr.T) + 1e-12 * np.eye(dr.shape[1]))
    return out


def replicate(job):
    r, ref = job
    dq, d0, yv = problem()
    cq, c0 = chains(dq, yv, 36_411_100 + 10 * r), chains(d0, yv, 36_411_500 + 10 * r)
    pos = BR.chain_positions(cq, SD_STEP)
    cond = B.beta_conditionals(dq, np.array([cq[c][k] for c, k in pos]), yv)
    lsd, rel = BR.savage_dickey_terms(cond, dq.prior["beta_sd"])
    rows = []
    for variant in ("adapted", "fixed"):
        ev = {}
        for name, d, ch in (("MQ", dq, cq), ("M0", d0, c0)):
            ev[name] = BR.bridge_log_evidence(lambda z: B.log_post(d, z, yv), ch, np.random.default_rng((36_411_900 if name == "MQ" else 36_411_950) + r),
                                              proposal=None if variant == "adapted" else ref[name])
        p = BR.paired_difference_se(ev["M0"], ev["MQ"], rel, pos)
        pf = BR.paired_difference_se(ev["M0"], ev["MQ"], rel, pos, fixed_point=True)
        rows.append(dict(rep=r, variant=variant, lbf_bridge=ev["M0"]["log_evidence"] - ev["MQ"]["log_evidence"], lbf_sd=lsd,
                         D=ev["M0"]["log_evidence"] - ev["MQ"]["log_evidence"] - lsd, se_paired=p["se"], se_paired_fp=pf["se"],
                         fp_factor_mq=ev["MQ"]["fp_factor"], fp_factor_m0=ev["M0"]["fp_factor"], se_naive=p["se_unpaired_naive"],
                         var_post_paired=p["var_post_paired"], var_prop_mq=p["var_prop_mq"], var_m0=p["var_m0"],
                         converged=bool(ev["M0"]["converged"] and ev["MQ"]["converged"])))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--procs", type=int, default=6)
    a = ap.parse_args()
    if a.reps > 40:
        sys.exit("at most 40 replicates (seed zone)")
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_bridge.py", ROOT / "python/sharpbl/bq_core.py", ROOT / "scripts/bq_core_selftest.py"]
    sha = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in srcs}
    meta = dict(status="running", reps=a.reps, procs=a.procs, sources_sha256=sha, note="synthetic; development")
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    ref = reference(None)
    with get_context("fork").Pool(a.procs) as pool:
        for rows in pool.imap_unordered(replicate, [(r, ref) for r in range(a.reps)]):
            pd.DataFrame(rows).to_csv(out / "REPLICATES.csv", mode="a", header=not (out / "REPLICATES.csv").exists(), index=False)
            print(rows[0]["rep"], [(x["variant"], round(x["D"], 4), round(x["se_paired"], 4)) for x in rows], flush=True)
    t = pd.read_csv(out / "REPLICATES.csv")
    summ = []
    for v, x in t.groupby("variant"):
        dm = x.D.mean()
        summ.append(dict(variant=v, reps=len(x), mean_D=dm, sd_D=x.D.std(ddof=1), mean_se_paired=x.se_paired.mean(),
                         ratio_sd_over_se=x.D.std(ddof=1) / x.se_paired.mean(), mean_se_paired_fp=x.se_paired_fp.mean(),
                         ratio_sd_over_se_fp=x.D.std(ddof=1) / x.se_paired_fp.mean(), fp_factor_mq_mean=x.fp_factor_mq.mean(),
                         fp_factor_m0_mean=x.fp_factor_m0.mean(), mean_se_naive=x.se_naive.mean(),
                         within_2se=float((abs(x.D - dm) <= 2 * x.se_paired).mean()), mean_lbf_bridge=x.lbf_bridge.mean(),
                         sd_lbf_bridge=x.lbf_bridge.std(ddof=1), all_converged=bool(x.converged.all())))
    s = pd.DataFrame(summ)
    s.to_csv(out / "SUMMARY.csv", index=False)
    meta.update(status="completed", sources_unchanged=all(hashlib.sha256((ROOT / k).read_bytes()).hexdigest() == v for k, v in sha.items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(s.to_string())


if __name__ == "__main__":
    main()
