"""Q1 (P2's T2 as a test: Joy coefficient cycle 25 - cycle 24), Q2 (P2's T4 as a test: latitude vs activity at fixed
phase) and Q3 (local quenching, descriptive) on the HMI sample S, with P2f procedure M on the contrast row.

Draft protocol docs/PROTOCOL_HMI_FOLLOWUPS_DRAFT.md (to be frozen as docs/PROTOCOL_HMI_FOLLOWUPS.md). Nothing here reads
tilts or latitudes as responses before the freeze: --selftest uses synthetic responses on the real design;
--validate and --run refuse without the frozen protocol; --run also needs an accepted validation.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/hmi_followups.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/hmi_followups.py --benchmark
    OMP_NUM_THREADS=1 .venv/bin/python scripts/hmi_followups.py --validate --protocol-sha SHA   # after the freeze
    OMP_NUM_THREADS=1 .venv/bin/python scripts/hmi_followups.py --run --protocol-sha SHA        # after validation

Implementation choices (for the review):
- Units dict for V.procedure_m built as in p2f_validation.units(test="T3") with the contrast row in place of the
  slope row (cell_level and the REML use the full matrix; b = cell sums of the row).
- Q1 generator: V.responses (P2f, beta_frac 0) on the whole design, then the effect -2.4 deg * sin|lambda| added to
  cycle-25 records, then the window. Q2 generator: |lambda| = mu + c sd_e e + x_scale * 3 deg * x_(CR,h) (+ beta (A-1)),
  mu = fit of the activity-free T4 model on the real |lambda| (design, not response of the test), e normal or t4/sqrt2
  (scenario 9), c the heteroscedastic factor of P2f for scenarios 5 and 9, x from V.gen_x.
- Validation sizes: Q1 and Q2 (sd 6 deg) 2000 null catalogues in scenarios 0, 1, 2, 7, 9 and 500 with effect in 1 and 7;
  Q2 sensitivity sd 4 and 9 deg: 1000 null catalogues in scenarios 1 and 7. Acceptance: Clopper-Pearson 95 % upper
  bound of all false verdicts <= 4 % in scenarios 0, 1, 2 (P2f rule).
"""
from __future__ import annotations

import argparse
import hashlib
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2d, p2f_pilot as P, p2f_validation as V, run_p2  # noqa: E402

FROZEN = ROOT / "docs/PROTOCOL_HMI_FOLLOWUPS.md"
OUT_VAL = ROOT / "results/HMI_FOLLOWUPS_VALIDATION"
OUT_RUN = ROOT / "results/HMI_FOLLOWUPS"
GAMMA0 = 24.0
EFF_Q1 = -0.1 * GAMMA0          # deg of Joy coefficient in cycle 25
EFF_Q2 = 1.0                    # deg per unit activity
SD_LAT, SD_LAT_T = 6.0, 3.0
SCEN = (0, 1, 2, 7, 9)
CORRECT = (0, 1, 2)
N_NULL, N_EFF, N_SENS = 2000, 500, 1000
N_PROC, T_MAX_H = 12, 8.0
USED = ([tuple(r) for r in P.USED] + [(3_000_000, 5_001_000), (6_000_000, 9_002_000), (20_000_000, 20_001_000),
        (28_000_000, 28_400_000), (29_500_000, 29_500_011), (31_000_000, 33_200_000), (34_000_000, 34_240_000),
        (34_900_000, 34_901_000)])


# ---------------------------------------------------------------- seeds

def seed(kind, i, k):
    base = {"q1_null": 35_100_000, "q1_eff": 35_700_000, "q2_null": 36_100_000, "q2_sens": 36_700_000,
            "q2_eff": 37_200_000}[kind]
    return base + 100_000 * i + k


def seeds_ok():
    s = ([seed("q1_null", i, k) for i in range(5) for k in range(N_NULL)] +
         [seed("q1_eff", i, k) for i in range(2) for k in range(N_EFF)] +
         [seed("q2_null", i, k) for i in range(5) for k in range(N_NULL)] +
         [seed("q2_sens", i, k) for i in range(4) for k in range(N_SENS)] +
         [seed("q2_eff", i, k) for i in range(2) for k in range(N_EFF)])
    return len(set(s)) == len(s) and not any(lo <= x < hi for x in s for lo, hi in USED)


# ---------------------------------------------------------------- design

def load_design(with_responses=False):
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    d = d[np.isfinite(d["A_monthly"])].reset_index(drop=True)
    base = P.build_design()
    if not d[P.DESIGN_COLS].equals(base):
        raise RuntimeError("design differs from the P2f design")
    cols = P.DESIGN_COLS + ["phase"] + (["gamma"] if with_responses else [])
    return d[cols].copy()


def q1_window(d, symmetric=False):
    phmax = d.loc[d["cyc"] == 25, "phase"].max()
    keep = (d["cyc"] == 25) | ((d["cyc"] == 24) & (d["phase"] <= phmax))
    if symmetric:
        lo = d.loc[d["cyc"] == 24, "phase"].min()
        keep &= d["phase"] >= lo
    return keep.to_numpy(), float(phmax)


def matrices(d, which, symmetric=False):
    """(mask, X, w, contrast row a, column names) for 'q1', 'q1_hem', 'q2', 'q3_b', 'q3_q<k>'."""
    s, cyc, hem = d["sinlat"].to_numpy(), d["cyc"].to_numpy(), d["hemisphere"].to_numpy()
    if which in ("q1", "q1_hem"):
        m, _ = q1_window(d, symmetric)
        if which == "q1":
            X = np.column_stack([s * (cyc == 24), s * (cyc == 25)])[m]
            a = lambda X, w: p2d.wls_row(X, w, 1) - p2d.wls_row(X, w, 0)  # noqa: E731
        else:
            X = np.column_stack([s * ((cyc == c) & (hem == h)) for c in (24, 25) for h in "NS"])[m]
            a = lambda X, w: 0.5 * (p2d.wls_row(X, w, 2) - p2d.wls_row(X, w, 0)  # noqa: E731
                                    + p2d.wls_row(X, w, 3) - p2d.wls_row(X, w, 1))
        w = d["phi"].to_numpy(float)[m]
        return m, X, w, a(X, w)
    m = np.ones(len(d), bool)
    w = d["phi"].to_numpy(float)
    if which == "q2":
        ph = d["phase"].to_numpy()
        X = np.column_stack([run_p2.ch_columns(d, 1.0), ph, ph ** 2, ph ** 3, d["A_monthly"].to_numpy() - 1.0])
        return m, X, w, p2d.wls_row(X, w, X.shape[1] - 1)
    lphi = np.log10(w)
    mlog = float(np.sum(w * lphi) / np.sum(w))
    act = (d["A_monthly"].to_numpy() - 1.0) * s
    if which == "q3_b":
        X = np.column_stack([run_p2.ch_columns(d, s), (lphi - mlog) * s, act])
        return m, X, w, p2d.wls_row(X, w, 4)
    q = int(which[-1])
    edges = np.quantile(w, [0.2, 0.4, 0.6, 0.8])
    qi = np.searchsorted(edges, w, side="right")
    X = np.column_stack([run_p2.ch_columns(d, s)] + [(qi == j) * s for j in range(1, 5)] + [act])
    return m, X, w, p2d.wls_row(X, w, q + 2)   # columns: 4 cycle x hemisphere, quintiles 2..5 at 4..7, activity


def units(d, mask, X, w, a, y):
    cr = d["CR"].to_numpy()[mask].astype(int)
    hem = d["hemisphere"].to_numpy()[mask]
    coef = P.wls(X, w, y)
    codes, uniq = P.cell_keys(cr, hem)
    return dict(test="T3", y=y, w=w, Xf=X, a_row=a, beta=float(a @ y), r=y - X @ coef, codes=codes, uniq=uniq,
                phi=w, n_check=(len(y), len(uniq)))


# ---------------------------------------------------------------- generators

def gen_q1(d, scen, rng, effect=0.0):
    g = V.responses(d, scen, rng, 0.0)["gamma"].to_numpy()
    return g + effect * d["sinlat"].to_numpy() * (d["cyc"].to_numpy() == 25)


def lat_mean(d):
    """mu of the activity-free T4 model fitted on the real |lambda| (design, not the response of the test)."""
    ph = d["phase"].to_numpy()
    X0 = np.column_stack([run_p2.ch_columns(d, 1.0), ph, ph ** 2, ph ** 3])
    y = d["lat"].abs().to_numpy()
    return X0 @ P.wls(X0, d["phi"].to_numpy(float), y)


def gen_q2(d, mu, scen, rng, sd_e=SD_LAT, effect=0.0):
    spec = V.SCENARIOS[scen]
    lo = int(d["CR"].min())
    G = int(d["CR"].max()) - lo + 1
    x = V.gen_x(spec, G, rng)[d["CR"].astype(int).to_numpy() - lo, (d["hemisphere"] == "S").to_numpy().astype(int)]
    n = len(d)
    e = rng.standard_t(4, n) / math.sqrt(2.0) if spec.get("t4") else rng.standard_normal(n)
    phi = d["phi"].to_numpy()
    c = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else np.ones(n)
    return mu + c * sd_e * e + spec.get("x_scale", 1.0) * SD_LAT_T * x + effect * (d["A_monthly"].to_numpy() - 1.0)


# ---------------------------------------------------------------- one catalogue

_D = {}


def _init():
    d = load_design()
    _D.update(d=d, mu=lat_mean_from_saved(d))


def lat_mean_from_saved(d):
    # load_design omits responses; |lambda| is a design column of P2f ("lat")
    return lat_mean(d)


def m_verdict(u, truth, predicted):
    try:
        r = V.procedure_m(u)
    except V.CandidateError as exc:
        return dict(verdict="errore", error=str(exc))
    sup = r["hi"] < 0 if predicted < 0 else r["lo"] > 0
    opp = r["lo"] > 0 if predicted < 0 else r["hi"] < 0
    return dict(beta=r["beta"], se=r["se"], lo=r["lo"], hi=r["hi"],
                verdict="supportato" if sup else ("opposto" if opp else "non deciso"),
                covered=int(r["lo"] <= truth <= r["hi"]))


def unit(task):
    test, kind, i, k, scen, sd_e, effect = task
    d = _D["d"]
    rng = np.random.default_rng(seed(kind, i, k))
    if test == "q1":
        y_all = gen_q1(d, scen, rng, effect)
        m, X, w, a = matrices(d, "q1")
        out = m_verdict(units(d, m, X, w, a, y_all[m]), effect, -1)
    else:
        y = gen_q2(d, _D["mu"], scen, rng, sd_e, effect)
        m, X, w, a = matrices(d, "q2")
        out = m_verdict(units(d, m, X, w, a, y), effect, +1)
    return dict(test=test, kind=kind, i=i, k=k, scenario=scen, sd_e=sd_e, effect=effect, seed=seed(kind, i, k), **out)


def tasks():
    t = [("q1", "q1_null", i, k, s, 15.0, 0.0) for i, s in enumerate(SCEN) for k in range(N_NULL)]
    t += [("q1", "q1_eff", i, k, s, 15.0, EFF_Q1) for i, s in enumerate((1, 7)) for k in range(N_EFF)]
    t += [("q2", "q2_null", i, k, s, SD_LAT, 0.0) for i, s in enumerate(SCEN) for k in range(N_NULL)]
    t += [("q2", "q2_sens", i, k, s, sd, 0.0) for i, (sd, s) in enumerate([(4.0, 1), (4.0, 7), (9.0, 1), (9.0, 7)])
          for k in range(N_SENS)]
    t += [("q2", "q2_eff", i, k, s, SD_LAT, EFF_Q2) for i, s in enumerate((1, 7)) for k in range(N_EFF)]
    return t


def summarise(raw):
    rows = []
    for (test, kind, scen, sd_e), g in raw.groupby(["test", "kind", "scenario", "sd_e"]):
        n = len(g)
        sup, opp = int((g.verdict == "supportato").sum()), int((g.verdict == "opposto").sum())
        null = g.effect.iloc[0] == 0
        r = dict(test=test, kind=kind, scenario=scen, sd_e=sd_e, n=n, errors=int((g.verdict == "errore").sum()),
                 supportato=sup / n, opposto=opp / n, coverage=float(g.covered.sum() / n))
        if null:
            r["false_cp_upper95"] = p2d.cp_upper(sup + opp, n)
            r["accepted_rule"] = bool(r["false_cp_upper95"] <= 0.04) if (scen in CORRECT and kind.endswith("null")) else None
        rows.append(r)
    tab = pd.DataFrame(rows)
    acc = {t: bool(tab[(tab.test == t) & tab.accepted_rule.notna()].accepted_rule.all()) for t in ("q1", "q2")}
    return tab, acc


# ---------------------------------------------------------------- frozen-protocol gate

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def gate(protocol_sha):
    if not FROZEN.exists() or hashlib.sha256(FROZEN.read_bytes()).hexdigest() != protocol_sha:
        sys.exit("frozen protocol missing or SHA-256 differs")
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(FROZEN)], cwd=ROOT, capture_output=True).returncode:
        sys.exit("frozen protocol not committed")
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("clean tree required")


def write(out, frames, meta):
    tmp = out.with_name(out.name + f".partial_{os.getpid()}")
    tmp.mkdir(parents=True)
    for name, df in frames.items():
        df.to_csv(tmp / name, index=False)
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in tmp.iterdir()}
    os.rename(tmp, out)
    (out / "META.json").write_text(json.dumps(dict(meta, products_sha256=hashes, git_commit=git("rev-parse", "HEAD"),
                                                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                                              indent=2, default=str) + "\n")


def validate(protocol_sha):
    gate(protocol_sha)
    if OUT_VAL.exists():
        sys.exit("validation output exists")
    if not selftest():
        return 1
    h = benchmark()
    if h > T_MAX_H:
        sys.exit(f"predicted {h:.1f} h > {T_MAX_H} h: stop before the grid")
    t0 = time.time()
    with Pool(N_PROC, initializer=_init) as pool:
        raw = pd.DataFrame(pool.map(unit, tasks(), chunksize=8))
    tab, acc = summarise(raw)
    write(OUT_VAL, {"RAW.csv.gz": raw, "SUMMARY.csv": tab, "ACCEPTANCE.csv": pd.DataFrame([acc])},
          dict(protocol_sha256=protocol_sha, hours=(time.time() - t0) / 3600, predicted_hours=h, acceptance=acc))
    print(tab.to_string(index=False))
    print(acc)
    return 0


def run(protocol_sha):
    gate(protocol_sha)
    acc = pd.read_csv(OUT_VAL / "ACCEPTANCE.csv").iloc[0].to_dict()
    if OUT_RUN.exists():
        sys.exit("run output exists")
    d = load_design(with_responses=True)
    rows = []
    for name, which, sym, pred, y in (("Q1 main (T2 window)", "q1", False, -1, d["gamma"].to_numpy()),
                                      ("Q1 symmetric window", "q1", True, -1, d["gamma"].to_numpy()),
                                      ("Q1 hemisphere-averaged", "q1_hem", False, -1, d["gamma"].to_numpy()),
                                      ("Q2", "q2", False, +1, d["lat"].abs().to_numpy()),
                                      ("Q3 b (log10 Phi)", "q3_b", False, -1, d["gamma"].to_numpy())) + tuple(
            (f"Q3 quintile {q} - 1", f"q3_q{q}", False, -1, d["gamma"].to_numpy()) for q in range(2, 6)):
        m, X, w, a = matrices(d, which, sym)
        r = m_verdict(units(d, m, X, w, a, y[m]), 0.0, pred)
        verdict_allowed = (name.startswith("Q1 main") and acc["q1"]) or (name == "Q2" and acc["q2"])
        rows.append(dict(analysis=name, n=int(m.sum()), **{k: v for k, v in r.items() if k != "covered"},
                         verdict_reported=(r.get("verdict") if verdict_allowed else "descrittivo")))
    write(OUT_RUN, {"ESTIMATES.csv": pd.DataFrame(rows)}, dict(protocol_sha256=protocol_sha, validation=acc))
    print(pd.DataFrame(rows).to_string(index=False))
    return 0


# ---------------------------------------------------------------- selftest and benchmark

def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    d = load_design()
    ok("seeds unique and disjoint from every used range", seeds_ok())
    m, phmax = q1_window(d)
    ok("Q1 window reproduces P2's T2 (2238 regions)", int(m.sum()) == 2238, (int(m.sum()), round(phmax, 3)))
    s, cyc = d["sinlat"].to_numpy(), d["cyc"].to_numpy()
    y = 20 * s * (cyc == 24) + 17 * s * (cyc == 25)
    for which, sym in (("q1", False), ("q1", True), ("q1_hem", False)):
        mm, X, w, a = matrices(d, which, sym)
        ok(f"{which}{' sym' if sym else ''}: noise-free contrast = -3", abs(a @ y[mm] + 3) < 1e-9, a @ y[mm])
    mu = lat_mean(d)
    mm, X, w, a = matrices(d, "q2")
    ok("Q2: noise-free slope recovers +1.5", abs(a @ (mu + 1.5 * (d["A_monthly"].to_numpy() - 1)) - 1.5) < 1e-9)
    ok("Q2: activity-free mean gives slope 0", abs(a @ mu) < 1e-9)
    lphi = np.log10(d["phi"].to_numpy())
    wv = d["phi"].to_numpy()
    mlog = np.sum(wv * lphi) / np.sum(wv)
    yq3 = s * (20 + 2.0 * (lphi - mlog)) + 0.3 * (d["A_monthly"].to_numpy() - 1) * s
    mm, X, w, a = matrices(d, "q3_b")
    ok("Q3: noise-free local slope recovers +2", abs(a @ yq3 - 2.0) < 1e-9)
    edges = np.quantile(wv, [0.2, 0.4, 0.6, 0.8])
    qi = np.searchsorted(edges, wv, side="right")
    yq = s * (20 + np.array([0.0, 1.0, 2.0, 3.0, 4.0])[qi]) + 0.3 * (d["A_monthly"].to_numpy() - 1) * s
    ok("Q3 quintiles: noise-free offsets 1..4 recovered",
       all(abs(matrices(d, f"q3_q{q}")[3] @ yq - (q - 1)) < 1e-9 for q in range(2, 6)))
    rng = np.random.default_rng(1)
    e = gen_q2(d, mu, 0, rng) - mu
    ok("Q2 generator: individual SD about 6 deg (scenario 0)", abs(e.std() - 6) < 0.3, round(float(e.std()), 2))
    _D.update(d=d, mu=mu)
    r1 = unit(("q1", "q1_null", 1, 0, 1, 15.0, 0.0))
    r2 = unit(("q2", "q2_null", 1, 0, 1, SD_LAT, 0.0))
    ok("one Q1 and one Q2 catalogue analysed by M", r1["verdict"] != "errore" and r2["verdict"] != "errore",
       (r1["verdict"], r2["verdict"]))
    ok("--validate/--run refuse before the freeze", not FROZEN.exists())
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def benchmark():
    _init()
    sample = [(t[0], t[1], t[2], 9000 + j, t[4], t[5], t[6]) for j, t in enumerate(tasks()[::1300][:16])]
    t0 = time.time()
    for t in sample:
        unit(t)
    per = (time.time() - t0) / len(sample)
    h = per * len(tasks()) / N_PROC / 3600
    print(f"benchmark: {len(sample)} complete units, {per:.2f} s each; predicted {h:.2f} h on {N_PROC} processes "
          f"for {len(tasks())} units")
    return h


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for f in ("selftest", "benchmark", "validate", "run"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--protocol-sha")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.benchmark:
        benchmark()
        return 0
    if a.validate and a.protocol_sha:
        return validate(a.protocol_sha)
    if a.run and a.protocol_sha:
        return run(a.protocol_sha)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
