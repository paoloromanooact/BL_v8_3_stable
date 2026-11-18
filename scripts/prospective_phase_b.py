"""Phase B of the prospective information plan: simulations with procedure M for the 4 selected candidates.

Plan docs/PROSPECTIVE_INFORMATION_PLAN.md (frozen 71c7d17) §5 B, amendment A1 (551d829); candidates from
results/PROSPECTIVE_PHASE_A/B_SELECTION.csv (all T5, family F5, model (a), activity offset -0.5, f = 0.75, k = 1.5).
For each candidate j: the 10th design realisation (r10) regenerated with the phase A generator, then 1000 noise
catalogues under null and 1000 under the scenario with the same paired noise and offsets (seeds 34 000 000 + 10 000 j
+ k), each analysed with the unchanged P2f procedure M on the plan's model (a) matrix. Synthetic only; T5 stays
descriptive. Not blind.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/prospective_phase_b.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/prospective_phase_b.py --benchmark
    OMP_NUM_THREADS=1 .venv/bin/python scripts/prospective_phase_b.py --run        # clean tree, detached

Implementation choices (for the review):
- Responses on z_i = D*_i/Phi_i as in the P2f generator: z = eta_bar (1 + k_i e_i + 0.5 x_scale x_{CR,h}) + s_i
  (+ Delta eta_c(i) under the scenario), with k_i = 1.5 for MDI records, s_i = coef * |Delta beta_5(E0)| * (A_c - 1) for
  MDI records (family F5, constant and drift zero), Delta eta_c from the proxy (A0, delta_max 0.20, E0 quantiles).
- Per catalogue: one generator from the seed; first the temporal component (V.gen_x of P2f scenario 1 or 7 on the
  contiguous CR grid of the cells), then the individual normals in record order.
- Procedure M = p2f_validation.procedure_m on a units dict built from the plan's matrix (columns I_{c,h}, I^{M24}_h, x5);
  the matrix is rebuilt here and checked equal (row g) to phase A.
- Reported: false verdicts by side (null), 'supportato' (scenario), coverage of the target (0 or Delta beta) and of the
  WLS expectation (bias m included), R = median(SE)/SD(beta_hat), errors; analytic predictions from phase A RAW.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2d, p2f_pilot as P, p2f_validation as V  # noqa: E402

_spec = importlib.util.spec_from_file_location("prospective_phase_a", ROOT / "scripts/prospective_phase_a.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

PHASE_A = ROOT / "results/PROSPECTIVE_PHASE_A"
OUT = ROOT / "results/PROSPECTIVE_PHASE_B"
N_CAT = 1000
N_PROC = 12
T_MAX_H = 8.0
ETA, Z = A.ETA, A.Z
SCEN = {"ar1_05": 1, "ar1_09": 2, "steps20": 7}


def candidates():
    b = pd.read_csv(PHASE_A / "B_SELECTION.csv")
    c = b[b.selected == 1].sort_values("j")
    if list(c.j.astype(int)) != list(range(len(c))) or not (c.test == "T5").all() or not (c.model == "a").all():
        raise A.TechnicalError("unexpected phase B selection")
    out = c.to_dict("records")
    for x in out:
        x["j"], x["r10"] = int(x["j"]), int(x["r10"])
    return out


_STATE = {}


def build(cand):
    """Design of candidate cand (10th realisation) and every static piece of the T5 model (a)."""
    S, silso = _STATE["S"], _STATE["silso"]
    st, R0 = _STATE["st"], _STATE["R0"]
    e = [i for i, (x, f) in enumerate(A.EXT_F) if x == cand["ext"] and f == cand["f"]][0]
    seed = A.design_seed(e, int(cand["r10"]))
    add, _, _ = A.generate(cand["ext"], cand["f"], seed, st, R0)
    R = pd.concat([R0, add[R0.columns]], ignore_index=True)
    dz = A.t5_design(R)
    Rt, codes, W, cyc_c, abar, Mc, cell_cr, cell_h, tc = A.t5_cells(R)
    cols = A.ch_cols(cyc_c, cell_h, 1.0)
    cols.update({f"M24{h}": Mc * ((cyc_c == 24) & (cell_h == h)) for h in ("N", "S")})
    cols["x5"] = abar - 1.0
    X, names, _ = A._finish(cols, W, "x5")
    g = p2d.wls_row(X, W, names.index("x5"))
    if names[-1] != "x5" or not np.allclose(g, dz["rows"]["a"]["g"], rtol=0, atol=1e-12 * np.abs(g).max()):
        raise A.TechnicalError("rebuilt matrix differs from phase A")
    a_lo, a_hi = _STATE["q"]
    d_eta = A.t5_delta_eta(dz, a_lo, a_hi, 0.20)
    target = float(g @ d_eta)
    u1 = _STATE["u1"]
    s_rec = cand["activity_coef"] * u1 * (abar[codes] - 1.0) * Rt["M"].to_numpy(float)
    m = float(g @ np.bincount(codes, weights=dz["agg"] * s_rec, minlength=len(W)))
    lo = int(cell_cr.min())
    return dict(cand=cand, seed_design=seed, X=X, W=W, g=g, codes=codes, agg=dz["agg"], phi=Rt["phi"].to_numpy(float),
                Mrec=Rt["M"].to_numpy(float), cell_cr=cell_cr, cell_h=cell_h, d_eta=d_eta, target=target, m=m,
                s_rec=s_rec, t_idx=Rt["CR"].to_numpy(int) - lo, h_idx=(Rt["hem"].to_numpy() == "S").astype(int),
                G=int(cell_cr.max()) - lo + 1, n_records=len(Rt), n_cells=len(W))


def responses(d, k, noise=True):
    rng = np.random.default_rng(A.b_noise_seed(int(d["cand"]["j"]), k))
    xs = 1.0
    if noise:
        x = V.gen_x(V.SCENARIOS[SCEN[d["cand"]["form"]]], d["G"], rng)[d["t_idx"], d["h_idx"]]
        e = rng.standard_normal(len(d["phi"]))
    else:
        x = e = np.zeros(len(d["phi"]))
    kf = np.where(d["Mrec"] == 1, d["cand"]["k"], 1.0)
    z0 = ETA * (1.0 + kf * e + 0.5 * xs * x) + d["s_rec"]
    return z0, z0 + d["d_eta"][d["codes"]]


def units(d, z):
    eta_c = np.bincount(d["codes"], weights=d["agg"] * z, minlength=len(d["W"]))
    bf = P.wls(d["X"], d["W"], eta_c)
    return dict(test="T5", y=z, w=d["phi"], k_of_i=d["codes"], agg=d["agg"], Xf_c=d["X"], W_c=d["W"], g=d["g"],
                beta=float(d["g"] @ eta_c), r=z - (d["X"] @ bf)[d["codes"]], codes=d["codes"], cell_cr=d["cell_cr"],
                cell_hem=d["cell_h"], eta_c=eta_c, phi=d["phi"])


def analyse(d, z, truth_target, truth_exp):
    try:
        r = V.procedure_m(units(d, z))
    except V.CandidateError as exc:
        return dict(verdict="errore", error=str(exc))
    return dict(beta=r["beta"], se=r["se"], lo=r["lo"], hi=r["hi"], verdict=r["verdict"],
                cov_target=int(r["lo"] <= truth_target <= r["hi"]), cov_expect=int(r["lo"] <= truth_exp <= r["hi"]))


def _init():
    S, silso = A.load_inputs()
    st = A.Strata(S, silso)
    R0 = A.e0_records(S)
    meta = json.loads((PHASE_A / "META.json").read_text())
    _STATE.update(S=S, silso=silso, st=st, R0=R0, q=(float(meta["A_lo"]), float(meta["A_hi"])),
                  u1=float(meta["units"]["abs_dbeta5_E0"]), designs={})


def unit(task):
    j, k = task
    if j not in _STATE["designs"]:
        _STATE["designs"][j] = build(candidates()[j])
    d = _STATE["designs"][j]
    t0 = time.monotonic()
    z0, z1 = responses(d, k)
    out = []
    for sig, z, tt, te in (("null", z0, 0.0, d["m"]), ("scenario", z1, d["target"], d["target"] + d["m"])):
        out.append(dict(j=j, k=k, seed=A.b_noise_seed(j, k), signal=sig, **analyse(d, z, tt, te)))
    for o in out:
        o["seconds"] = time.monotonic() - t0
    return out


def pool_map(tasks, log=print):
    rows = []
    with Pool(N_PROC, initializer=_init) as pool:
        for i, part in enumerate(pool.imap_unordered(unit, tasks, chunksize=4)):
            rows += part
            if log and (i + 1) % 400 == 0:
                log(f"{i + 1}/{len(tasks)} units")
    return pd.DataFrame(rows)


def predictions():
    raw = pd.read_csv(PHASE_A / "RAW.csv.gz")
    meta = json.loads((PHASE_A / "META.json").read_text())
    u1 = meta["units"]["abs_dbeta5_E0"]
    out = []
    for c in candidates():
        n = [i for i, (f, s, xs) in enumerate(A.NOISE) if f == c["form"] and xs == 1.0][0]
        x = raw[(raw.ext == c["ext"]) & (raw.f == c["f"]) & (raw.r == c["r10"]) & (raw.test == "T5") &
                (raw.model == "a") & (raw.noise == n) & (raw.k == c["k"])].iloc[0]
        m = c["activity_coef"] * u1 * x.B1
        out.append(dict(j=int(c["j"]), se_analytic=x.se, target_analytic=x.target_020, m_analytic=m,
                        **{f"pred_{k}_null": v for k, v in A.freqs(0.0, m, x.se).items()},
                        **{f"pred_{k}_scen": v for k, v in A.freqs(x.target_020, m, x.se).items()}))
    return pd.DataFrame(out)


def summarise(raw, pred):
    rows = []
    for (j, sig), g in raw.groupby(["j", "signal"]):
        ok = g[g.verdict != "errore"]
        n = len(g)
        r = dict(j=j, signal=sig, n=n, errors=int((g.verdict == "errore").sum()),
                 supportato=float((g.verdict == "supportato").sum() / n), opposto=float((g.verdict == "opposto").sum() / n),
                 cov_target=float(ok.cov_target.sum() / n), cov_expect=float(ok.cov_expect.sum() / n),
                 beta_mean=float(ok.beta.mean()), beta_sd=float(ok.beta.std(ddof=1)), se_median=float(ok.se.median()))
        r["R"] = r["se_median"] / r["beta_sd"]
        r["mcse_supportato"] = math.sqrt(r["supportato"] * (1 - r["supportato"]) / n)
        rows.append(r)
    return pd.DataFrame(rows).merge(pred, on="j")


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    _init()
    cs = candidates()
    ok("4 selected candidates, j = 0..3, all T5 model (a)", len(cs) == 4)
    seeds = [A.b_noise_seed(j, k) for j in range(4) for k in range(N_CAT)]
    ok("noise seeds 34 000 000 + 10 000 j + k, disjoint from used ranges and from design seeds",
       not any(lo <= s < hi for s in seeds for lo, hi in A.USED_RANGES) and max(seeds) < 34_900_000 and len(set(seeds)) == 4000)
    pred = predictions()
    for c in cs[:2]:
        d = build(c)
        p = pred[pred.j == c["j"]].iloc[0]
        ok(f"j={c['j']}: rebuilt target equals phase A RAW", abs(d["target"] / p.target_analytic - 1) < 1e-10,
           f"{d['target']:.4e}")
        ok(f"j={c['j']}: bias m equals coef * u1 * B1 of phase A", abs(d["m"] / p.m_analytic - 1) < 1e-10, f"{d['m']:.3e}")
        z0, z1 = responses(d, 0, noise=False)
        b0, b1 = units(d, z0)["beta"], units(d, z1)["beta"]
        ok(f"j={c['j']}: noise-free WLS slope = m (null) and target + m (scenario)",
           abs(b0 - d["m"]) < 1e-9 * abs(d["m"]) and abs(b1 - d["target"] - d["m"]) < 1e-9 * abs(d["target"]))
        r = unit((c["j"], 0))
        ok(f"j={c['j']}: one paired catalogue analysed by M", len(r) == 2 and all(x["verdict"] in
           ("supportato", "opposto", "non deciso", "errore") for x in r), [x["verdict"] for x in r])
        same = responses(d, 5)[0] - responses(d, 5)[1]
        ok(f"j={c['j']}: paired noise, scenario - null = Delta eta of the cell", np.allclose(-same, d["d_eta"][d["codes"]]))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def benchmark():
    tasks = [(j, k) for j in range(4) for k in range(N_CAT, N_CAT + 3)]   # seeds outside the grid (k >= 1000 unused)
    t0 = time.time()
    _init()
    rows = []
    for t in tasks:
        rows += unit(t)
    per = (time.time() - t0) / len(tasks)
    total_h = per * 4 * N_CAT / N_PROC / 3600
    print(f"benchmark: {per:.2f} s per paired unit (incl. design build); predicted {total_h:.2f} h on {N_PROC} processes")
    return total_h


def run():
    if git("status", "--porcelain", "--untracked-files=no"):
        print("modifiche non committate: albero pulito richiesto")
        return 2
    if OUT.exists():
        print(f"{OUT} esiste già")
        return 2
    if not selftest():
        return 1
    h = benchmark()
    if h > T_MAX_H:
        print(f"durata prevista {h:.1f} h > {T_MAX_H} h: arresto prima della griglia (piano §5 B8)")
        return 1
    t0 = time.time()
    raw = pool_map([(j, k) for j in range(4) for k in range(N_CAT)])
    summ = summarise(raw, predictions())
    tmp = OUT.with_name(OUT.name + f".partial_{os.getpid()}")
    tmp.mkdir(parents=True)
    raw.to_csv(tmp / "RAW.csv.gz", index=False)
    summ.to_csv(tmp / "SUMMARY.csv", index=False)
    hashes = {f.name: A.sha(f) for f in tmp.iterdir()}
    os.rename(tmp, OUT)
    meta = dict(plan_sha256=A.SHA_PLAN, amendment_sha256=A.SHA_AMEND, git_commit=git("rev-parse", "HEAD"),
                script_sha256=A.sha(__file__), phase_a_meta_sha256=A.sha(PHASE_A / "META.json"),
                b_selection_sha256=A.sha(PHASE_A / "B_SELECTION.csv"), n_catalogues=N_CAT, hours=(time.time() - t0) / 3600,
                predicted_hours=h, products_sha256=hashes, outcome="eseguita")
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"fase B eseguita in {meta['hours']:.2f} h")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.benchmark:
        benchmark()
        return 0
    if a.run:
        return run()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
