"""BQ-HMI S-ID, first phase (design docs/BQ_STUDY_DESIGN_DRAFT_20261127.md, NOT registered yet): runner.

G1-G4 x 100 replicates on the T3 design (metadata only), synthetic responses (generators of
scripts/bq_identifiability_pilot.py). Paired L1 fits per replicate: MQ without v and MQ v HN20 on every replicate, MQ
v HN5 on replicates 0-29 (fixed in the manifest). Four chains per fit: warm-up W, saved K (K fixed by the sizing pilot,
a parameter here), extensions of the saved phase to E1 and E2 that CONTINUE the chain (same fixed widths, generator
state restored), then technical status. Each chain is saved as soon as it ends; a resumed run skips finished chains
and refuses changed sources.

Seeds: 36_500_000 + 4000 g + 40 r + 4 f + c (chain), response f = 9, c = 3. The manifest SEEDS.csv is written and
checked for collisions BEFORE any chain.

Per fit: gate (bq_diag: >= 4 chains, rank R-hat <= 1.01, bulk/tail ESS >= 400 on every sampling coordinate, the
conditional mean of beta and the log Savage-Dickey ordinate); beta posterior mean and SD (mixture of the conditional
normals), 95 % interval and coverage of the true beta, P(beta < 0) and log BF_0Q with MC SE (batch means within
chains), the approved threshold_uncertain rule (closed interval estimate +- 2 MCSE reaching or crossing 0.95 or
-log 10), and the evidence rule P(beta < 0) > 0.95 and log BF_0Q < -log 10 for fits that pass the gate and are not
uncertain. Summaries per generator and fit: bias, RMSE, coverage, width, evidence frequency with Wilson 95 %,
technical failures and uncertain fits counted separately on the total.

    --plan            write SEEDS.csv only
    --dev             development run (any size; writes 'development' in META); the registered run needs the freeze
    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_sid_study.py --out <dir> --dev --reps 2 --warm 20 --keep 40 --ext 60,80
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
from scipy.optimize import brentq
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_diag as DG  # noqa: E402
import bq_identifiability_pilot as IP  # noqa: E402

SEED0 = 36_500_000
GENS = ("G1", "G2", "G3", "G4")
BETA_TRUE = {"G1": -5.0, "G2": 0.0, "G3": -5.0, "G4": 0.0}
FITS = (("MQ_no_v", False, None), ("MQ_v_hn20", True, 20.0), ("MQ_v_hn5", True, 5.0))
HN5_REPS = 30
FREEZE = ROOT / "docs/BQ_STUDY_DESIGN_FREEZE.json"            # does not exist until the registration
P_THR, BF_THR = 0.95, -math.log(10.0)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def chain_seed(g, r, f, c):
    return SEED0 + 4000 * g + 40 * r + 4 * f + c


def response_seed(g, r):
    return SEED0 + 4000 * g + 40 * r + 4 * 9 + 3


def fits_for(r):
    return [0, 1] + ([2] if r < HN5_REPS else [])


def seeds_manifest(gens, reps):
    rows = [dict(gen=GENS[g], rep=r, fit="response", chain=-1, seed=response_seed(g, r)) for g in gens for r in range(reps)]
    rows += [dict(gen=GENS[g], rep=r, fit=FITS[f][0], chain=c, seed=chain_seed(g, r, f, c)) for g in gens for r in range(reps)
             for f in fits_for(r) for c in range(4)]
    t = pd.DataFrame(rows)
    if t.seed.duplicated().any() or not t.seed.between(SEED0, SEED0 + 99_999).all():
        raise ValueError("seed manifest: collision or outside the zone")
    return t


def design(with_v, sv):
    D = IP.design_arrays()
    prior = dict(B.PRIOR, q_sd=0.5, sigma_v_hn=sv or 20.0)
    return D, B.Design(t=D["t"], h=D["h"], s=D["s"], a=D["a"], lphi=D["lphi"], cell=D["cell"], fam=D["fam"], n_t=D["n_t"], n_cell=4,
                       with_v=with_v, prior=prior)


def chain_path(out, g, r, f, c):
    return Path(out) / "CHAINS" / f"{GENS[g]}_r{r:03d}_{FITS[f][0]}_c{c}.npz"


def continue_chain(logf, x, w, n, rng):
    """Saved-phase continuation with FIXED widths w (the kernel of slice_chain after its warm-up): n further sweeps."""
    x = np.array(x, float)
    fx = logf(x)
    keep, hits = [], 0
    for _ in range(n):
        x, fx, h = B.slice_sweep(logf, x, fx, w, rng)
        hits += h
        keep.append(x.copy())
    return np.array(keep), hits


def run_chain(job):
    """Base phase (warm + keep) or an extension to `target` saved draws continuing the stored state."""
    g, r, f, c, warm, keep, target, out = job
    os.environ["OMP_NUM_THREADS"] = "1"
    p = chain_path(out, g, r, f, c)
    name, with_v, sv = FITS[f]
    D, d = design(with_v, sv)
    y = IP.simulate(D, GENS[g], np.random.default_rng(response_seed(g, r)))
    logf = lambda z: B.log_post(d, z, y)                      # noqa: E731
    if not p.exists():
        rng = np.random.default_rng(chain_seed(g, r, f, c))
        x0 = np.array([math.log(20.0), -0.4, math.log(2.0), 0.9, -0.4, math.log(3.0)] + ([math.log(5.0), 1.5, 0.3] if with_v else []))
        x0 = x0 + rng.normal(0.0, 0.5, len(x0))
        t0 = time.perf_counter()
        dr, lk, w, hits = B.slice_chain(logf, x0, warm, keep, rng)
        draws, secs = dr, time.perf_counter() - t0
    else:
        z = np.load(p, allow_pickle=False)
        draws, w, hits, secs = z["draws"], z["widths"], int(z["hits"]), float(z["seconds"])
        if len(draws) >= target:
            return str(p)
        rng = np.random.default_rng()
        rng.bit_generator.state = json.loads(str(z["rng_state"]))
        t0 = time.perf_counter()
        dr, h2 = continue_chain(logf, draws[-1], w, target - len(draws), rng)
        draws, hits, secs = np.vstack([draws, dr]), hits + h2, secs + time.perf_counter() - t0
    cond = B.beta_conditionals(d, draws, y)
    tmp = p.with_suffix(".tmp.npz")
    np.savez(tmp, draws=draws, cond=cond, widths=np.asarray(w, float), hits=hits, seconds=secs, seed=chain_seed(g, r, f, c),
             rng_state=json.dumps(rng.bit_generator.state), names=np.array(d.names()))
    os.replace(tmp, p)
    return str(p)


def batch_mean_se(chains, n_batches=10):
    allv = np.concatenate(chains)
    bm = []
    for v in chains:
        size = len(v) // n_batches
        bm += [v[i * size:(i + 1) * size].mean() for i in range(n_batches)]
    return float(allv.mean()), float(np.std(bm, ddof=1) / math.sqrt(len(bm)))


def mixture_quantile(m, v, q):
    sd = np.sqrt(v)
    f = lambda x: float(ndtr((x - m) / sd).mean()) - q          # noqa: E731
    lo, hi = float((m - 10 * sd).min()), float((m + 10 * sd).max())
    return brentq(f, lo, hi, xtol=1e-10)


def wilson(k, n, z=1.959964):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def assess(out, g, r, f):
    zs = [np.load(chain_path(out, g, r, f, c)) for c in range(4)]
    n = min(len(z["draws"]) for z in zs)
    names = list(zs[0]["names"])
    q = {nm: np.stack([z["draws"][:n, i] for z in zs]) for i, nm in enumerate(names)}
    q["beta_cond_mean"] = np.stack([z["cond"][:n, 0] for z in zs])
    lo = [-0.5 * z["cond"][:n, 0] ** 2 / z["cond"][:n, 1] - 0.5 * np.log(2 * math.pi * z["cond"][:n, 1]) for z in zs]
    q["log_sd_ordinate"] = np.stack(lo)
    diag = {nm: DG.diagnose(ch) for nm, ch in q.items()}
    gate = all(dg["passes"] for dg in diag.values())
    m = np.concatenate([z["cond"][:n, 0] for z in zs])
    v = np.concatenate([z["cond"][:n, 1] for z in zs])
    pn, pse = batch_mean_se([ndtr(-z["cond"][:n, 0] / np.sqrt(z["cond"][:n, 1])) for z in zs])
    mx = max(float(x.max()) for x in lo)
    ord_m, ord_se = batch_mean_se([np.exp(x - mx) for x in lo])
    bf = mx + math.log(ord_m) - (-0.5 * math.log(2 * math.pi) - math.log(10.0))
    bf_se = ord_se / ord_m
    unc = (pn - 2 * pse <= P_THR <= pn + 2 * pse) or (bf - 2 * bf_se <= BF_THR <= bf + 2 * bf_se)
    lo95, hi95 = mixture_quantile(m, v, 0.025), mixture_quantile(m, v, 0.975)
    bt = BETA_TRUE[GENS[g]]
    status = "technical_failure" if not gate else ("threshold_uncertain" if unc else "ok")
    return dict(gen=GENS[g], rep=r, fit=FITS[f][0], draws_per_chain=n, gate=gate, status=status, beta_mean=float(m.mean()),
                beta_sd=float(math.sqrt(v.mean() + m.var())), lo95=lo95, hi95=hi95, covers=bool(lo95 <= bt <= hi95), p_beta_neg=pn, p_mcse=pse,
                log_bf0q=bf, bf_mcse=bf_se, evidence=bool(status == "ok" and pn > P_THR and bf < BF_THR),
                rhat_max=max(dg["rhat"] for dg in diag.values()), ess_min=min(min(dg["ess_bulk"], dg["ess_tail"]) for dg in diag.values()),
                seconds_per_chain=float(np.mean([float(z["seconds"]) for z in zs])))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--gens", default="0,1,2,3")
    ap.add_argument("--warm", type=int, default=2000)
    ap.add_argument("--keep", type=int, required=False)
    ap.add_argument("--ext", default="", help="extension targets of saved draws per chain, e.g. 10000,20000")
    ap.add_argument("--procs", type=int, default=16)
    a = ap.parse_args()
    out = Path(a.out)
    gens = [int(x) for x in a.gens.split(",")]
    out.mkdir(parents=True, exist_ok=True)
    seeds = seeds_manifest(gens, a.reps)
    if (out / "SEEDS.csv").exists():
        if not pd.read_csv(out / "SEEDS.csv").equals(seeds):
            sys.exit("seed manifest differs from the stored one")
    else:
        seeds.to_csv(out / "SEEDS.csv", index=False)
    if a.plan:
        print(f"SEEDS.csv: {len(seeds)} seeds, no collision")
        return
    if not a.dev and not FREEZE.exists():
        sys.exit("S-ID: the design is not registered (no freeze receipt); use --dev for development runs")
    if a.keep is None:
        sys.exit("--keep (saved draws per chain, fixed by the sizing pilot) is required")
    srcs = [Path(__file__), ROOT / "python/sharpbl/bq_core.py", ROOT / "python/sharpbl/bq_diag.py", ROOT / "scripts/bq_identifiability_pilot.py",
            ROOT / "scripts/bq_woodbury_benchmark.py"]
    src_sha = {str(p.relative_to(ROOT)): sha(p) for p in srcs}
    if (out / "META.json").exists() and json.loads((out / "META.json").read_text())["sources_sha256"] != src_sha:
        sys.exit("resume refused: sources changed")
    meta = dict(status="running", development=bool(a.dev), sources_sha256=src_sha, seed0=SEED0, reps=a.reps, gens=a.gens, warm=a.warm, keep=a.keep,
                ext=a.ext, hn5_reps=HN5_REPS)
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    (out / "CHAINS").mkdir(exist_ok=True)
    units = [(g, r, f) for g in gens for r in range(a.reps) for f in fits_for(r)]
    targets = [a.keep] + [int(x) for x in a.ext.split(",") if x]
    ctx = get_context("fork")
    rows = {}
    for stage, target in enumerate(targets):
        todo = units if stage == 0 else [u for u in units if rows[u]["status"] == "technical_failure"]
        jobs = [(g, r, f, c, a.warm, a.keep, target, str(out)) for g, r, f in todo for c in range(4)]
        jobs.sort(key=lambda j: -int(FITS[j[2]][1]))                  # the slower v fits first
        with ctx.Pool(a.procs) as pool:
            for p in pool.imap_unordered(run_chain, jobs):
                pass
        for u in todo:
            rows[u] = assess(out, *u)
        print(f"stage {stage} (saved {target}): {sum(rows[u]['status'] == 'technical_failure' for u in units)} technical failures", flush=True)
    res = pd.DataFrame([rows[u] for u in units])
    res.to_csv(out / "FITS.csv", index=False)
    summ = []
    for (gen, fit), x in res.groupby(["gen", "fit"]):
        ok = x[x.status == "ok"]
        k, nn = int(ok.evidence.sum()), len(x)
        wl, wh = wilson(k, nn)
        bt = BETA_TRUE[gen]
        summ.append(dict(gen=gen, fit=fit, n=nn, technical_failures=int((x.status == "technical_failure").sum()),
                         threshold_uncertain=int((x.status == "threshold_uncertain").sum()), evidence=k, evidence_rate=k / nn, wilson_lo=wl,
                         wilson_hi=wh, bias=float((ok.beta_mean - bt).mean()) if len(ok) else np.nan,
                         rmse=float(np.sqrt(((ok.beta_mean - bt) ** 2).mean())) if len(ok) else np.nan,
                         coverage=float(ok.covers.mean()) if len(ok) else np.nan, width=float((ok.hi95 - ok.lo95).mean()) if len(ok) else np.nan))
    pd.DataFrame(summ).to_csv(out / "SUMMARY.csv", index=False)
    meta.update(status="completed", sources_unchanged=all(sha(ROOT / k) == v for k, v in src_sha.items()))
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(pd.DataFrame(summ).to_string())


if __name__ == "__main__":
    main()
