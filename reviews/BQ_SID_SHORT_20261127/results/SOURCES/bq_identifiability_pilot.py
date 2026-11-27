"""BQ-HMI preparation: identifiability pilot of beta (quenching) against v (temporal Joy coefficient), synthetic only.

NOT the frozen study (generators, replicates and chain lengths are a pilot to inform the freeze). Real T3 design
structure (CR, hemisphere, sin|lat|, activity, flux, family; no response read); synthetic responses from the model:
    gamma_i = k_(c,h) s_i + beta a_i s_i + u_(t,h) + v_(t,h) s_i + b_f + eps_i,  eps_i ~ N(0, sigma_i^2),
with generator values near the historical non-blind ones (sigma0 20, q -0.4, sigma_x 2.1, phi 0.75, kappa -0.42,
sigma_f 3; k = 23/25/21/22). Generators:
  G1 beta = -5, no v;   G2 beta = 0, v AR(1) (sigma_v 10, phi_v 0.95, kappa_v 0.5);   G3 both;
  G4 beta = 0, v_i s_i = -5 a_i s_i (the temporal Joy term reproduces the activity regressor exactly: confounded by
  construction; the fits must show the ambiguity, not resolve it).
Fits on every data set: MQ without v, MQ with v (sigma_v HN 5), MQ with v (sigma_v HN 20), rev. 4 priors with
q ~ N(0, 0.5^2). Reported: posterior mean/SD of beta, P(beta < 0), Savage-Dickey log BF_0Q (Rao-Blackwellised),
posterior mean of sigma_v, stepping-limit hits.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_identifiability_pilot.py --out reviews/BQ_IDENTIFIABILITY_PILOT_20261125 \
        [--reps 4 --warm 200 --keep 400 --procs 10]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B  # noqa: E402

SEED = 36_400_301
GEN = {"G1": dict(beta=-5.0, v=None), "G2": dict(beta=0.0, v="ar1"), "G3": dict(beta=-5.0, v="ar1"), "G4": dict(beta=0.0, v="activity")}
TRUE = dict(sigma0=20.0, q=-0.4, sigma_x=2.1, phi=0.75, kappa=-0.42, sigma_f=3.0, k=(23.0, 25.0, 21.0, 22.0),
            sigma_v=10.0, phi_v=0.95, kappa_v=0.5, c_act=-5.0)
FITS = (("MQ_no_v", False, None), ("MQ_v_hn5", True, 5.0), ("MQ_v_hn20", True, 20.0))


def design_arrays():
    import bq_woodbury_benchmark as W
    d = W.design()
    t = (d.CR.to_numpy() - d.CR.min()).astype(int)
    h = (d.hemisphere.to_numpy() == "S").astype(int)
    cell = (d.cyc.to_numpy() == 25).astype(int) * 2 + h
    fam = pd.factorize(d.family_id.to_numpy())[0]
    return dict(t=t, h=h, s=d.sinlat.to_numpy(), a=d.A_monthly.to_numpy() - 1.0, lphi=np.log10(d.phi.to_numpy() / 1e21),
                cell=cell, fam=fam, n_t=int(t.max()) + 1)


def ar1(rng, n_t, sd, phi, kappa):
    z = np.empty((n_t, 2))
    c = math.sqrt(1 - kappa ** 2)

    def e():
        a = rng.standard_normal()
        return np.array([a, kappa * a + c * rng.standard_normal()])
    z[0] = e()
    for t in range(1, n_t):
        z[t] = phi * z[t - 1] + math.sqrt(1 - phi ** 2) * e()
    return sd * z


def simulate(D, gen, rng):
    g = GEN[gen]
    T = TRUE
    k = np.array(T["k"])[D["cell"]]
    u = ar1(rng, D["n_t"], T["sigma_x"], T["phi"], T["kappa"])[D["t"], D["h"]]
    y = k * D["s"] + g["beta"] * D["a"] * D["s"] + u
    if g["v"] == "ar1":
        y = y + ar1(rng, D["n_t"], T["sigma_v"], T["phi_v"], T["kappa_v"])[D["t"], D["h"]] * D["s"]
    elif g["v"] == "activity":
        y = y + T["c_act"] * D["a"] * D["s"]
    y = y + rng.standard_normal(D["fam"].max() + 1)[D["fam"]] * T["sigma_f"]
    return y + T["sigma0"] * np.exp(T["q"] * D["lphi"]) * rng.standard_normal(len(y))


def fit_one(job):
    gen, rep, name, with_v, sv, warm, keep = job
    D = design_arrays()
    rng = np.random.default_rng(SEED + 1000 * list(GEN).index(gen) + rep)
    y = simulate(D, gen, rng)                        # same data for every fit of (gen, rep)
    prior = dict(B.PRIOR, q_sd=0.5, sigma_v_hn=sv or 20.0)
    d = B.Design(t=D["t"], h=D["h"], s=D["s"], a=D["a"], lphi=D["lphi"], cell=D["cell"], fam=D["fam"], n_t=D["n_t"], n_cell=4,
                 with_v=with_v, prior=prior)
    x0 = [math.log(20.0), -0.4, math.log(2.0), 0.9, -0.4, math.log(3.0)] + ([math.log(5.0), 1.5, 0.3] if with_v else [])
    t0 = time.time()
    dr, _, _, hits = B.slice_chain(lambda z: B.log_post(d, z, y), np.array(x0), warm, keep, np.random.default_rng(SEED + 7 + rep))
    cond = B.beta_conditionals(d, dr[::4], y)
    m, v_ = cond[:, 0], cond[:, 1]
    sd = math.sqrt(v_.mean() + m.var())
    from scipy.stats import norm
    p_neg = float(np.mean(norm.cdf(-m / np.sqrt(v_))))
    lbf, se = B.savage_dickey_log_bf0q(d, cond)
    return dict(generator=gen, rep=rep, fit=name, beta_true=GEN[gen]["beta"], beta_mean=float(m.mean()), beta_sd=sd, p_beta_neg=p_neg,
                log_bf0q_sd=lbf, log_bf0q_se_naive=se, sigma_v_mean=float(np.exp(dr[:, 6]).mean()) if with_v else np.nan,
                sigma0_mean=float(np.exp(dr[:, 0]).mean()), stepping_hits=int(hits), seconds=round(time.time() - t0, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--warm", type=int, default=200)
    ap.add_argument("--keep", type=int, default=400)
    ap.add_argument("--procs", type=int, default=10)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    jobs = [(g, r, n, wv, sv, a.warm, a.keep) for g in GEN for r in range(a.reps) for n, wv, sv in FITS]
    with Pool(a.procs) as pool:
        rows = pool.map(fit_one, jobs, chunksize=1)
    t = pd.DataFrame(rows)
    a.out.mkdir(parents=True)
    t.to_csv(a.out / "FITS.csv", index=False)
    (a.out / "META.json").write_text(json.dumps(dict(seed=SEED, reps=a.reps, warm=a.warm, keep=a.keep, generators=GEN, true=TRUE,
                                                     fits=[f[0] for f in FITS], note="pilot, not the frozen study; synthetic responses only"),
                                                indent=2) + "\n")
    pd.set_option("display.width", 250)
    print(t.groupby(["generator", "fit"])[["beta_mean", "beta_sd", "p_beta_neg", "log_bf0q_sd", "sigma_v_mean"]].mean().round(3).to_string())
