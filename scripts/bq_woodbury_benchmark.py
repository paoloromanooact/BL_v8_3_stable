"""BQ-HMI preparation: Woodbury vs dense Cholesky for the Gaussian marginal likelihood (L1), synthetic responses only.

Structure from the frozen T3 design (CR, hemisphere, P1e family; no response read): records i, latent u_(CR,h)
bivariate stationary AR(1) on every integer CR of the span, optional v_(CR,h) multiplying s_i, replicated families as
latents, singleton families on the diagonal. Covariance C = D + Z K Z^T with D_ii = sigma_i^2 (+ sigma_f^2 for
singleton families). Checks log N(y; 0, C) by both routes on synthetic y and parameter sets, and times them.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_woodbury_benchmark.py --out reviews/BQ_WOODBURY_BENCHMARK_20261125
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2f_pilot as P  # noqa: E402

SEED = 36_400_001


def design():
    d = P.build_design()
    fam = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", usecols=["HARPNUM", "family_id"], low_memory=False).drop_duplicates()
    d = d.merge(fam, on="HARPNUM", how="left", validate="one_to_one")
    d["CR"] = d.CR.astype(int)
    return d


def ar1_biv_cov(n_t, sd, phi, kappa):
    """Stationary bivariate AR(1): Cov(x_(t,h), x_(t',h')) = sd^2 kappa^[h!=h'] phi^|t-t'|; index t*2+h."""
    t = np.arange(n_t)
    T = phi ** np.abs(t[:, None] - t[None, :])
    H = np.array([[1.0, kappa], [kappa, 1.0]])
    return sd * sd * np.kron(T, H)


def structure(d, with_v):
    cr0 = d.CR.min()
    n_t = d.CR.max() - cr0 + 1
    idx = (d.CR.to_numpy() - cr0) * 2 + (d.hemisphere.to_numpy() == "S")
    fs = d.groupby("family_id").size()
    rep = {f: j for j, f in enumerate(fs[fs >= 2].index)}
    single = d.family_id.map(fs).to_numpy() == 1
    n = len(d)
    blocks = [("u", 2 * n_t)] + ([("v", 2 * n_t)] if with_v else []) + [("f", len(rep))]
    m = sum(b for _, b in blocks)
    Z = np.zeros((n, m))
    Z[np.arange(n), idx] = 1.0
    off = 2 * n_t
    if with_v:
        Z[np.arange(n), off + idx] = d.sinlat.to_numpy()
        off += 2 * n_t
    rows = [i for i, f in enumerate(d.family_id) if f in rep]
    Z[rows, [off + rep[d.family_id.iloc[i]] for i in rows]] = 1.0
    return dict(Z=Z, n_t=n_t, single=single, n_rep=len(rep), with_v=with_v)


def params_K_D(st, d, p):
    K = [ar1_biv_cov(st["n_t"], p["sx"], p["phi"], p["kappa"])]
    if st["with_v"]:
        K.append(ar1_biv_cov(st["n_t"], p["sv"], p["phi_v"], p["kappa_v"]))
    K.append(p["sf"] ** 2 * np.eye(st["n_rep"]))
    m = sum(k.shape[0] for k in K)
    Kb = np.zeros((m, m))
    o = 0
    for k in K:
        Kb[o:o + len(k), o:o + len(k)] = k
        o += len(k)
    sig = p["s0"] * np.exp(p["q"] * np.log10(d.phi.to_numpy() / 1e21))
    D = sig ** 2 + np.where(st["single"], p["sf"] ** 2, 0.0)
    return Kb, D


def loglik_dense(y, Z, K, D):
    C = np.diag(D) + Z @ K @ Z.T
    c = cho_factor(C, lower=True)
    return -0.5 * (len(y) * math.log(2 * math.pi) + 2 * np.log(np.diag(c[0])).sum() + y @ cho_solve(c, y))


def loglik_woodbury(y, Z, K, D):
    Di = 1.0 / D
    ck = cho_factor(K, lower=True)
    Kinv = cho_solve(ck, np.eye(len(K)))
    A = Kinv + (Z.T * Di) @ Z
    ca = cho_factor(A, lower=True)
    zy = Z.T @ (Di * y)
    quad = y @ (Di * y) - zy @ cho_solve(ca, zy)
    logdet = np.log(D).sum() + 2 * np.log(np.diag(ck[0])).sum() + 2 * np.log(np.diag(ca[0])).sum()
    return -0.5 * (len(y) * math.log(2 * math.pi) + logdet + quad)


def run():
    d = design()
    rng = np.random.default_rng(SEED)
    sets = [dict(s0=20.0, q=-0.4, sx=2.1, phi=0.75, kappa=-0.42, sf=3.0, sv=5.0, phi_v=0.8, kappa_v=0.2),
            dict(s0=15.0, q=0.0, sx=8.0, phi=0.98, kappa=0.9, sf=0.5, sv=20.0, phi_v=-0.3, kappa_v=-0.7),
            dict(s0=30.0, q=-1.15, sx=0.05, phi=0.1, kappa=0.0, sf=8.0, sv=0.1, phi_v=0.99, kappa_v=0.0)]
    rows = []
    for with_v in (False, True):
        st = structure(d, with_v)
        for k, p in enumerate(sets):
            K, D = params_K_D(st, d, p)
            y = rng.normal(0, 25, len(d))
            t0 = time.perf_counter()
            ld = loglik_dense(y, st["Z"], K, D)
            t1 = time.perf_counter()
            lw = loglik_woodbury(y, st["Z"], K, D)
            t2 = time.perf_counter()
            rows.append(dict(with_v=with_v, set=k, latent_dim=st["Z"].shape[1], loglik_dense=ld, loglik_woodbury=lw,
                             abs_diff=abs(ld - lw), rel_diff=abs(ld - lw) / abs(ld), t_dense_s=t1 - t0, t_woodbury_s=t2 - t1))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    t = run()
    ok = bool((t.rel_diff <= 1e-10).all())
    a.out.mkdir(parents=True)
    t.to_csv(a.out / "BENCHMARK.csv", index=False)
    (a.out / "META.json").write_text(json.dumps(dict(seed=SEED, agreement_rel_1e10=ok, numpy=np.__version__,
                                                     note="synthetic y only; timings single-thread, indicative"), indent=2) + "\n")
    print(t.to_string(index=False))
    print("agreement within 1e-10 relative:", ok)
    sys.exit(0 if ok else 1)
