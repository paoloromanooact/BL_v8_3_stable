"""Selftest of python/sharpbl/bq_diag.py on synthetic chains only (no observed response, no BQ fit).

 1. autocovariance by FFT = direct sum (every lag, three chains);
 2. classic split R-hat = its formula written out on a hand example;
 3. iid normal chains (4 x 4000): R-hat < 1.01, bulk ESS within 12 % of 16000, tail ESS > 0.6 x 16000; gate passes;
 4. AR(1) chains, phi 0.9 (4 x 25000): bulk ESS within 12 % of N (1 - phi) / (1 + phi) = 5263;
 5. one chain shifted by 0.5 SD: R-hat > 1.01, gate fails;
 6. same mean, one chain with three times the scale: bulk R-hat below the folded one, R-hat = folded > 1.01;
 7. rank-based diagnostics invariant under a monotone transform (exp): identical R-hat and ESS;
 8. heavy tails (Cauchy, iid): rank R-hat < 1.01 and bulk ESS within 12 % of N, where the classic split R-hat on the
    raw draws is not defined by finite moments (reported only);
 9. odd chain length: the middle draw is dropped (first and last n//2);
10. constant quantity -> status 'constant', gate fails; non-finite draws refused;
11. one chain of 4000 draws (its halves allow a split R-hat): status too_few_chains, gate fails although R-hat and ESS
    are fine; three chains also fail, four pass;
12. folded R-hat not evaluable (draws in {-1, +1}: |x - median| constant): R-hat NaN (not the finite bulk value),
    status rhat_not_evaluable, gate fails.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_diag_selftest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import bq_diag as D  # noqa: E402

SEED = 36_400_701
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def ar1(rng, m, n, phi):
    x = np.empty((m, n))
    x[:, 0] = rng.normal(0, 1 / np.sqrt(1 - phi * phi), m)                 # stationary start
    e = rng.normal(0, 1, (m, n))
    for t in range(1, n):
        x[:, t] = phi * x[:, t - 1] + e[:, t]
    return x


def main():
    rng = np.random.default_rng(SEED)
    # 1
    x = rng.normal(0, 1, (3, 257))
    xc = x - x.mean(axis=1, keepdims=True)
    direct = np.array([[(xc[i, :x.shape[1] - k] * xc[i, k:]).sum() / x.shape[1] for k in range(x.shape[1])] for i in range(3)])
    ok("1. autocovariance FFT = direct sum at every lag", np.max(np.abs(D.autocov(x) - direct)) < 1e-12, f"{np.max(np.abs(D.autocov(x) - direct)):.1e}")
    # 2
    c = np.array([[1.0, 2.0, 3.0, 4.0], [2.0, 3.0, 4.0, 5.0]])
    n, w, b = 4, np.mean([np.var(r, ddof=1) for r in c]), 4 * np.var(c.mean(axis=1), ddof=1)
    ok("2. classic R-hat formula on a hand example", abs(D.rhat_classic(c) - np.sqrt(((n - 1) / n * w + b / n) / w)) < 1e-15)
    # 3
    iid = rng.normal(0, 1, (4, 4000))
    d3 = D.diagnose(iid)
    ok("3. iid normal: R-hat < 1.01, bulk ESS within 12 % of N, tail ESS > 0.6 N, gate passes",
       d3["rhat"] < 1.01 and abs(d3["ess_bulk"] / 16000 - 1) < 0.12 and d3["ess_tail"] > 0.6 * 16000 and d3["passes"],
       f"R-hat {d3['rhat']:.4f}, ESS bulk {d3['ess_bulk']:.0f}, tail {d3['ess_tail']:.0f}")
    # 4
    phi = 0.9
    a = ar1(rng, 4, 25000, phi)
    th = a.size * (1 - phi) / (1 + phi)
    e4 = D.ess_bulk(a)
    ok("4. AR(1) phi 0.9: bulk ESS within 12 % of N (1 - phi)/(1 + phi)", abs(e4 / th - 1) < 0.12, f"ESS {e4:.0f} vs {th:.0f}")
    # 5
    sh = rng.normal(0, 1, (4, 2000))
    sh[0] += 0.5
    d5 = D.diagnose(sh)
    ok("5. one chain shifted by 0.5 SD: R-hat > 1.01, gate fails", d5["rhat"] > 1.01 and not d5["passes"], f"R-hat {d5['rhat']:.3f}")
    # 6
    sc = rng.normal(0, 1, (4, 2000))
    sc[0] *= 3.0
    r6, b6, f6 = D.rhat(sc)
    ok("6. one chain with three times the scale: bulk R-hat below folded, R-hat = folded > 1.01", b6 < f6 and r6 == f6 and r6 > 1.01,
       f"bulk {b6:.4f}, folded {f6:.4f}")
    # 7
    y = ar1(rng, 4, 3000, 0.5)
    dy, de = D.diagnose(y), D.diagnose(np.exp(y))
    ok("7. invariance under a monotone transform (exp): identical R-hat, bulk and tail ESS",
       all(dy[k] == de[k] for k in ("rhat", "ess_bulk", "ess_tail")), f"{dy['rhat']:.5f} / {de['rhat']:.5f}")
    # 8
    cy = rng.standard_cauchy((4, 4000))
    d8 = D.diagnose(cy)
    ok("8. Cauchy iid: rank R-hat < 1.01, bulk ESS within 12 % of N (classic R-hat on raw draws reported only)",
       d8["rhat"] < 1.01 and abs(d8["ess_bulk"] / 16000 - 1) < 0.12,
       f"rank R-hat {d8['rhat']:.4f}, ESS {d8['ess_bulk']:.0f}; classic on raw {D.rhat_classic(D.split_chains(cy)):.3f}")
    # 9
    od = np.arange(2 * 7, dtype=float).reshape(2, 7)
    sp = D.split_chains(od)
    ok("9. odd length 7: halves are the first 3 and the last 3 draws (middle dropped)",
       sp.shape == (4, 3) and (sp[0] == od[0, :3]).all() and (sp[2] == od[0, -3:]).all())
    # 10
    d10 = D.diagnose(np.ones((4, 100)))
    try:
        D.diagnose(np.array([[0.0, 1.0, np.nan, 2.0, 3.0]] * 2))
        refused = False
    except ValueError:
        refused = True
    ok("10. constant quantity -> status constant, gate fails; non-finite draws refused", d10["status"] == "constant" and not d10["passes"] and refused)
    # 11
    one = rng.normal(0, 1, (1, 4000))
    d11 = D.diagnose(one)
    three, four = D.diagnose(rng.normal(0, 1, (3, 2000))), D.diagnose(rng.normal(0, 1, (4, 2000)))
    ok("11. one chain of 4000: too_few_chains and gate fails (R-hat and ESS fine); 3 chains fail, 4 pass",
       d11["status"] == "too_few_chains" and not d11["passes"] and d11["rhat"] < 1.01 and d11["ess_bulk"] > 400
       and three["status"] == "too_few_chains" and not three["passes"] and four["passes"],
       f"one chain R-hat {d11['rhat']:.4f}, ESS {d11['ess_bulk']:.0f}")
    # 12
    pm = np.tile(np.r_[np.ones(500), -np.ones(500)], (4, 1))
    for row in pm:
        rng.shuffle(row)
    d12 = D.diagnose(pm)
    ok("12. folded R-hat not evaluable: R-hat NaN, status rhat_not_evaluable, gate fails",
       np.isnan(d12["rhat"]) and np.isfinite(d12["rhat_bulk"]) and np.isnan(d12["rhat_folded"]) and d12["status"] == "rhat_not_evaluable"
       and not d12["passes"], f"bulk {d12['rhat_bulk']:.4f}, folded {d12['rhat_folded']}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
