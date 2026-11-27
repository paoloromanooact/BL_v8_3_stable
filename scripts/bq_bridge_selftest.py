"""Selftest of python/sharpbl/bq_bridge.py, synthetic only.

1. Gaussian toy in 3 dimensions with exact posterior draws: known evidence (closed form).
2. One-dimensional non-Gaussian posterior (half-normal prior on a scale, Gaussian data): evidence by quadrature.
3. BQ model with one free coordinate (log sigma0, the others fixed): bridge from slice draws = quadrature.
4. BQ model, all six coordinates free, small synthetic design: log BF_0Q from two bridges (M0, MQ) agrees with the
   Savage-Dickey estimate from the MQ draws within the combined errors. The two are not fully independent checks.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_bridge_selftest.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_bridge as BR, bq_core as B  # noqa: E402

SEED = 36_400_501
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def main():
    rng = np.random.default_rng(SEED)
    # 1. Gaussian toy: y_k ~ N(theta, I) k = 1..m, theta ~ N(0, s^2 I), dim 3
    dim, m, s = 3, 10, 2.0
    yk = rng.normal(0.7, 1.0, (m, dim))
    prec = m + 1 / s ** 2
    pm = yk.sum(0) / prec

    def logq(th):
        return float(-0.5 * ((yk - th) ** 2).sum() - 0.5 * m * dim * math.log(2 * math.pi)
                     - 0.5 * (th @ th) / s ** 2 - 0.5 * dim * math.log(2 * math.pi * s * s))
    # exact log evidence: per coordinate, y_.k ~ N(0, I + s^2 11^T)
    C = np.eye(m) + s * s * np.ones((m, m))
    ld = np.linalg.slogdet(C)[1]
    exact = sum(-0.5 * (m * math.log(2 * math.pi) + ld + yk[:, j] @ np.linalg.solve(C, yk[:, j])) for j in range(dim))
    draws = pm + rng.standard_normal((4000, dim)) / math.sqrt(prec)
    r1 = BR.bridge_log_evidence(logq, [draws[:2000], draws[2000:]], rng)
    ok("1. Gaussian toy (3 dims, exact draws): bridge = closed-form evidence within 4 SE", r1["converged"]
       and abs(r1["log_evidence"] - exact) < 4 * r1["se_log"] + 1e-6, f"{r1['log_evidence']:.5f} +- {r1['se_log']:.5f} vs {exact:.5f}")
    # 2. 1-D non-Gaussian: z = log sigma, sigma ~ HN(5), data ~ N(0, sigma^2), n = 15
    yd = rng.normal(0, 3.0, 15)

    def lq2(z):
        z = float(np.atleast_1d(z)[0])
        sg = math.exp(z)
        return (math.log(2) - 0.5 * math.log(2 * math.pi) - math.log(5.0) - 0.5 * (sg / 5.0) ** 2 + z
                - 0.5 * len(yd) * math.log(2 * math.pi * sg * sg) - 0.5 * (yd @ yd) / sg ** 2)
    grid = np.linspace(-3, 4, 70001)
    lv = np.array([lq2(g) for g in grid])
    quad = float(lv.max() + math.log(np.trapezoid(np.exp(lv - lv.max()), grid)))
    ch, _, _, _ = B.slice_chain(lambda z: lq2(z), np.array([1.0]), 300, 4000, rng)
    r2 = BR.bridge_log_evidence(lq2, [ch], rng)
    ok("2. one-dimensional skewed posterior (log-scale of a half-normal scale): bridge = quadrature within 4 SE",
       abs(r2["log_evidence"] - quad) < 4 * r2["se_log"] + 1e-6, f"{r2['log_evidence']:.5f} +- {r2['se_log']:.5f} vs {quad:.5f}")
    # 3-4: BQ model
    import bq_core_selftest as T
    dq = T.synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150)
    d0 = T.synth_design(np.random.default_rng(SEED + 2), n_t=30, n=150, with_beta=False)
    xf = np.array([2.5, -0.4, 1.0, 0.8, -0.3, 0.7])
    yv = np.random.default_rng(SEED + 3).multivariate_normal(dq.X[:, :4] @ np.array([20, 22, 18, 25.0]) - 4.0 * dq.a * dq.s,
                                                              T.dense_cov(dq, B.unpack(dq, xf)))

    def lp1(d, g):
        z = xf.copy()
        z[0] = float(np.atleast_1d(g)[0])
        return B.log_prior(d, z) + B.loglik(d, z, yv)
    grid = np.linspace(1.0, 4.5, 3501)
    lv = np.array([lp1(dq, g) for g in grid])
    quad3 = float(lv.max() + math.log(np.trapezoid(np.exp(lv - lv.max()), grid)))
    ch3, _, _, _ = B.slice_chain(lambda g: lp1(dq, g), np.array([2.5]), 200, 3000, rng)
    r3 = BR.bridge_log_evidence(lambda g: lp1(dq, g), [ch3], rng)
    ok("3. BQ model, one free coordinate: bridge = quadrature within 4 SE", abs(r3["log_evidence"] - quad3) < 4 * r3["se_log"] + 1e-6,
       f"{r3['log_evidence']:.5f} +- {r3['se_log']:.5f} vs {quad3:.5f}")
    ev, chq = {}, None
    for name, d in (("MQ", dq), ("M0", d0)):
        chains = [B.slice_chain(lambda z: B.log_post(d, z, yv), xf, 300, 1500, np.random.default_rng(SEED + 10 + k))[0] for k in range(2)]
        ev[name] = BR.bridge_log_evidence(lambda z: B.log_post(d, z, yv), chains, rng)
        if name == "MQ":
            chq = np.concatenate(chains)
    lbf_bridge = ev["M0"]["log_evidence"] - ev["MQ"]["log_evidence"]
    se_bridge = math.hypot(ev["M0"]["se_log"], ev["MQ"]["se_log"])
    cond = B.beta_conditionals(dq, chq[::5], yv)
    lbf_sd, se_sd = B.savage_dickey_log_bf0q(dq, cond)
    ok("4. BQ model, six free coordinates: log BF_0Q bridge vs Savage-Dickey within 4 combined SE (SD SE x3 for autocorrelation)",
       abs(lbf_bridge - lbf_sd) < 4 * math.hypot(se_bridge, 3 * se_sd) + 1e-3,
       f"bridge {lbf_bridge:.4f} +- {se_bridge:.4f}, Savage-Dickey {lbf_sd:.4f} +- {se_sd:.4f}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
