"""BQ-HMI L2: resolution of the discrete precision measure (generalised Gauss-Laguerre of Gamma(nu/2, nu/2)) used by
bq_smc, on tail cases (Codex review of the SMC benchmark). Pure numerics, no data.

Per record the L2 predictive is p(y) = int N(y; m, c + s^2 / lam) Gamma(lam; nu/2, nu/2) dlam, s = residual scale
sigma sqrt((nu - 2)/nu), c = predictive variance of the shared latent part. In units of s: z = (y - m)/s,
rho = c / s^2. Reference: adaptive quadrature in log(lam) (scipy quad, relative 1e-13) and, for rho = 0, the exact
Student-t density (cross-check of the reference). Reported: log p(n nodes) - log p(reference) for n = 32 ... 512 of
the generalised Gauss-Laguerre rule (used by bq_smc), and for an alternative discrete measure: a uniform grid in
u = log(lam) on [U_LO, U_HI] with trapezoid weights of the Gamma density (Jacobian lam), renormalised to total mass 1
(n_log = 100, 200, 400). Integration and conditional sampling would use the same measure, as now.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_l2_quadrature_check.py --out reviews/BQ_L2_QUADRATURE_20261127
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.special import gammaln, roots_genlaguerre
from scipy.stats import t as student_t

NU = 4.0
Z = (0.0, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0)
RHO = (0.0, 0.1, 1.0, 10.0)
NODES = (32, 64, 128, 256, 512)


def nodes(n, nu=NU):
    a = nu / 2.0
    u, w = roots_genlaguerre(n, a - 1.0)
    return u / a, np.log(w) - gammaln(a)


def log_pred_nodes(z, rho, n, nu=NU):
    lam, lq = nodes(n, nu)
    v = rho + 1.0 / lam
    lk = lq - 0.5 * (math.log(2 * math.pi) + np.log(v) + z * z / v)
    m = lk.max()
    return float(m + math.log(np.exp(lk - m).sum()))


U_LO, U_HI = -30.0, 5.0
NLOG = (100, 200, 400)


def nodes_log(n, nu=NU):
    a = nu / 2.0
    u = np.linspace(U_LO, U_HI, n)
    lw = a * math.log(a) - gammaln(a) + a * u - a * np.exp(u)          # log Gamma density + log Jacobian lam
    w = np.full(n, u[1] - u[0])
    w[[0, -1]] *= 0.5
    lq = lw + np.log(w)
    m = lq.max()
    lq -= m + math.log(np.exp(lq - m).sum())                            # total mass 1
    return np.exp(u), lq


def log_pred_nodes_log(z, rho, n, nu=NU):
    lam, lq = nodes_log(n, nu)
    v = rho + 1.0 / lam
    lk = lq - 0.5 * (math.log(2 * math.pi) + np.log(v) + z * z / v)
    m = lk.max()
    return float(m + math.log(np.exp(lk - m).sum()))


def log_pred_ref(z, rho, nu=NU):
    a = nu / 2.0

    def f(u):                                    # u = log lam
        lam = math.exp(u)
        v = rho + 1.0 / lam
        lg = a * math.log(a) - gammaln(a) + (a - 1) * u - a * lam + u      # Gamma density times the Jacobian lam
        return math.exp(lg - 0.5 * (math.log(2 * math.pi) + math.log(v) + z * z / v))
    val = quad(f, -60, 12, epsabs=0, epsrel=1e-13, limit=500, points=[-math.log(1 + z * z), 0.0])[0]
    return math.log(val)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    rows = []
    for rho in RHO:
        for z in Z:
            ref = log_pred_ref(z, rho)
            exact = float(student_t.logpdf(z, NU, scale=math.sqrt(1.0 / 1.0)) + 0.0) if rho == 0 else np.nan
            r = dict(rho=rho, z=z, log_ref=ref, ref_minus_exact_t=(ref - exact) if rho == 0 else np.nan)
            for n in NODES:
                with np.errstate(all="ignore"):
                    try:
                        r[f"err_{n}"] = log_pred_nodes(z, rho, n) - ref
                    except (ValueError, FloatingPointError):
                        r[f"err_{n}"] = np.nan
            for n in NLOG:
                r[f"errlog_{n}"] = log_pred_nodes_log(z, rho, n) - ref
            rows.append(r)
    t = pd.DataFrame(rows)
    out.mkdir(parents=True)
    t.to_csv(out / "QUADRATURE.csv", index=False)
    (out / "META.json").write_text(json.dumps(dict(nu=NU, z=Z, rho=RHO, nodes=NODES, log_grid=dict(u_lo=U_LO, u_hi=U_HI, n=NLOG),
                                                   units="z and rho in units of the residual scale s"), indent=2) + "\n")
    pd.set_option("display.width", 200)
    print(t.to_string(float_format=lambda v: f"{v:.2e}"))


if __name__ == "__main__":
    main()
