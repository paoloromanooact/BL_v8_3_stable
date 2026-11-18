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
- Q2 main analysis: hemispheric phase (minima of the smoothed SILSO hemispheric series); conventional phase and the
  historical T4 as sensitivity (Codex's review, 18 Nov). The Q2 generator conditions on the sample: mu is the
  activity-free fit to the observed |lambda| (the response of Q2), which makes the simulation conditional on S.
- Validation grid and criteria follow P2f (docs/PROTOCOL_P2F_VALIDATED_TEST.md §5) on the scenarios 0, 1, 2, 7, 9:
  per main test (Q1, Q2 hemispheric) 10 000 null catalogues per scenario, criteria in every scenario: false verdicts
  <= 3.0 %, each side <= 1.75 %, errors <= 1 %; 2000 catalogues per effect combination (scenarios 1, 2, 7, 9 x two
  effects), criteria: coverage >= 96.5 % (errors count as non-coverage) and the exclusion tail <= 2.0 % (Q1: lower end
  above the true value; Q2: upper end below it). Sensitivities (reported, no criterion): Q2 hemispheric with individual
  SD 4 and 9 deg, Q2 conventional phase. The grid must be complete: exact counts, replica indices and seeds per
  configuration, no duplicates; otherwise the acceptance is False.
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
SD_LAT, SD_LAT_T = 6.0, 3.0
SCEN = (0, 1, 2, 7, 9)
EFF_SCEN = (1, 2, 7, 9)
N0, N1, NS = 10_000, 2000, 2000
LIM_FALSE, LIM_SIDE, LIM_ERR, LIM_COV, LIM_TAIL = 0.030, 0.0175, 0.01, 0.965, 0.020
N_PROC, T_MAX_H = 12, 8.0
Q2_MAIN = "hemispheric"
MAIN_TESTS = ("q1", "q2_hem")
USED = ([tuple(r) for r in P.USED] + [(3_000_000, 5_001_000), (6_000_000, 9_002_000), (20_000_000, 20_001_000),
        (28_000_000, 28_400_000), (29_500_000, 29_500_011), (31_000_000, 33_200_000), (34_000_000, 34_240_000),
        (34_900_000, 34_901_000)])


def configs():
    """Validation grid: one dict per configuration, in a fixed order (index = seed block)."""
    c = []
    for test, effs, sd in (("q1", (-0.1 * GAMMA0, -0.2 * GAMMA0), 15.0), ("q2_hem", (1.0, 2.0), SD_LAT)):
        c += [dict(test=test, role="main", scenario=s, sd_e=sd, effect=0.0, n=N0) for s in SCEN]
        c += [dict(test=test, role="main", scenario=s, sd_e=sd, effect=e, n=N1) for s in EFF_SCEN for e in effs]
    c += [dict(test="q2_hem", role="sensitivity", scenario=s, sd_e=sd, effect=0.0, n=NS) for sd in (4.0, 9.0)
          for s in (1, 7)]
    c += [dict(test="q2", role="sensitivity", scenario=s, sd_e=SD_LAT, effect=0.0, n=NS) for s in SCEN]
    for i, x in enumerate(c):
        x["cfg"] = i
    return c


def seed(cfg, k):
    return 40_000_000 + 100_000 * cfg + k


def seeds_ok():
    s = [seed(c["cfg"], k) for c in configs() for k in range(c["n"])]
    return len(set(s)) == len(s) and not any(lo <= x < hi for x in s for lo, hi in USED) and max(s) < 50_000_000


# ---------------------------------------------------------------- design

def load_design(with_responses=False):
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    d = d[np.isfinite(d["A_monthly"])].reset_index(drop=True)
    base = P.build_design()
    if not d[P.DESIGN_COLS].equals(base):
        raise RuntimeError("design differs from the P2f design")
    cols = P.DESIGN_COLS + ["phase", "t"] + (["gamma"] if with_responses else [])
    out = d[cols].copy()
    out["phase_hem"] = hemispheric_phase(out)
    return out


HEM_MIN_WINDOWS = {24: ("2007-01", "2010-12"), 25: ("2018-01", "2021-12")}


def hemispheric_minima():
    """Month of the minimum of the 13-month smoothed SILSO hemispheric series, per cycle and hemisphere."""
    sm = run_p2.load_silso()["smooth13"]
    return {(c, h): pd.Timestamp(sm.loc[lo:hi, h].idxmin() + "-01") for c, (lo, hi) in HEM_MIN_WINDOWS.items()
            for h in ("N", "S")}


def hemispheric_phase(d):
    mins = hemispheric_minima()
    return np.array([(t - mins[(int(c), h)]).days / 365.25 / 11.0 if (int(c), h) in mins else np.nan
                     for t, c, h in zip(d["t"], d["cyc"], d["hemisphere"])])


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
    if which in ("q2", "q2_hem"):
        ph = d["phase" if which == "q2" else "phase_hem"].to_numpy()
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


def lat_mean(d, phase="phase"):
    """mu of the activity-free T4 model fitted on the real |lambda| (design, not the response of the test)."""
    ph = d[phase].to_numpy()
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
    _D.update(d=d, mu=lat_mean_from_saved(d), mu_hem=lat_mean(d, "phase_hem"))


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
                covered=int(r["lo"] <= truth <= r["hi"]), lo_above=int(r["lo"] > truth), hi_below=int(r["hi"] < truth),
                **{k: r[k] for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2")})


def unit(task):
    cfg, k = task
    c = configs()[cfg]
    d = _D["d"]
    rng = np.random.default_rng(seed(cfg, k))
    if c["test"] == "q1":
        y_all = gen_q1(d, c["scenario"], rng, c["effect"])
        m, X, w, a = matrices(d, "q1")
        out = m_verdict(units(d, m, X, w, a, y_all[m]), c["effect"], -1)
    else:
        hem = c["test"] == "q2_hem"
        y = gen_q2(d, _D["mu_hem" if hem else "mu"], c["scenario"], rng, c["sd_e"], c["effect"])
        m, X, w, a = matrices(d, "q2_hem" if hem else "q2")
        out = m_verdict(units(d, m, X, w, a, y), c["effect"], +1)
    return dict(cfg=cfg, k=k, seed=seed(cfg, k), **{x: c[x] for x in ("test", "role", "scenario", "sd_e", "effect")},
                **out)


def tasks():
    return [(c["cfg"], k) for c in configs() for k in range(c["n"])]


def summarise(raw):
    """Per configuration: denominators, errors, verdicts by side, coverage and tails; acceptance per main test with the
    P2f criteria. Any incompleteness (missing or extra configuration, wrong counts, replica indices or seeds,
    duplicates) makes the acceptance False."""
    rows, problems = [], []
    expected = {c["cfg"]: c for c in configs()}
    if raw.duplicated(["cfg", "k"]).any() or raw.seed.duplicated().any():
        problems.append("duplicated rows or seeds")
    extra = set(raw.cfg) - set(expected)
    if extra:
        problems.append(f"unexpected configurations {sorted(extra)}")
    for cfg, c in expected.items():
        g = raw[raw.cfg == cfg]
        n = len(g)
        complete = (n == c["n"] and sorted(g.k) == list(range(c["n"])) and (g.seed == seed(cfg, g.k)).all()
                    and all((g[x] == c[x]).all() for x in ("test", "scenario", "sd_e", "effect")))
        if not complete:
            problems.append(f"configuration {cfg} incomplete ({n}/{c['n']})")
        err = int((g.verdict == "errore").sum())
        sup, opp = int((g.verdict == "supportato").sum()), int((g.verdict == "opposto").sum())
        good = g[g.verdict != "errore"]
        tail = "lo_above" if c["test"] == "q1" else "hi_below"
        r = dict(c, n_rows=n, complete=complete, errors=err, frac_errors=err / c["n"], supportato=sup / c["n"],
                 opposto=opp / c["n"], false_total=(sup + opp) / c["n"] if c["effect"] == 0 else np.nan,
                 coverage=float(good.covered.sum()) / c["n"], lo_above=float(good.lo_above.sum()) / c["n"],
                 hi_below=float(good.hi_below.sum()) / c["n"], exclusion_tail=float(good[tail].sum()) / c["n"])
        if c["role"] == "main":
            if c["effect"] == 0:
                r["criteria_ok"] = bool(complete and r["false_total"] <= LIM_FALSE and r["supportato"] <= LIM_SIDE
                                        and r["opposto"] <= LIM_SIDE and r["frac_errors"] <= LIM_ERR)
            else:
                r["criteria_ok"] = bool(complete and r["coverage"] >= LIM_COV and r["exclusion_tail"] <= LIM_TAIL)
        rows.append(r)
    tab = pd.DataFrame(rows)
    acc = {t: bool(not problems and tab[(tab.test == t) & (tab.role == "main")].criteria_ok.all()
                   and (tab.test == t).any()) for t in MAIN_TESTS}
    return tab, acc, problems


# ---------------------------------------------------------------- frozen-protocol gate

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def gate_problem(protocol_sha, frozen=None):
    """None if the frozen protocol is present, committed, with the given SHA-256 and the tree is clean; else a reason."""
    frozen = Path(frozen) if frozen else FROZEN
    if not frozen.exists():
        return "frozen protocol missing"
    if hashlib.sha256(frozen.read_bytes()).hexdigest() != protocol_sha:
        return "frozen protocol SHA-256 differs"
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(frozen)], cwd=ROOT, capture_output=True).returncode:
        return "frozen protocol not committed"
    if git("status", "--porcelain", "--untracked-files=no"):
        return "clean tree required"
    return None


def gate(protocol_sha):
    why = gate_problem(protocol_sha)
    if why:
        sys.exit(why)


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
    rows = []
    with Pool(N_PROC, initializer=_init) as pool:
        for i, r in enumerate(pool.imap_unordered(unit, tasks(), chunksize=16)):
            rows.append(r)
            if (i + 1) % 5000 == 0:
                print(f"{i + 1}/{len(tasks())} units, {(time.time() - t0) / 3600:.2f} h", flush=True)
    raw = pd.DataFrame(rows).sort_values(["cfg", "k"]).reset_index(drop=True)
    tab, acc, problems = summarise(raw)
    write(OUT_VAL, {"RAW.csv.gz": raw, "SUMMARY.csv": tab, "ACCEPTANCE.csv": pd.DataFrame([acc])},
          dict(protocol_sha256=protocol_sha, hours=(time.time() - t0) / 3600, predicted_hours=h, acceptance=acc,
               problems=problems))
    print(tab.to_string(index=False), flush=True)
    print(acc, problems, flush=True)
    return 0


def run(protocol_sha):
    gate(protocol_sha)
    vmeta = json.loads((OUT_VAL / "META.json").read_text())
    for name, h in vmeta["products_sha256"].items():
        if hashlib.sha256((OUT_VAL / name).read_bytes()).hexdigest() != h:
            sys.exit(f"validation product {name} changed")
    if vmeta["protocol_sha256"] != protocol_sha:
        sys.exit("validation ran under another protocol")
    acc = pd.read_csv(OUT_VAL / "ACCEPTANCE.csv").iloc[0].to_dict()
    if OUT_RUN.exists():
        sys.exit("run output exists")
    d = load_design(with_responses=True)
    rows = []
    for name, which, sym, pred, y in (("Q1 main (T2 window)", "q1", False, -1, d["gamma"].to_numpy()),
                                      ("Q1 symmetric window", "q1", True, -1, d["gamma"].to_numpy()),
                                      ("Q1 hemisphere-averaged", "q1_hem", False, -1, d["gamma"].to_numpy()),
                                      ("Q2 hemispheric phase", "q2_hem", False, +1, d["lat"].abs().to_numpy()),
                                      ("Q2 conventional phase (historical T4)", "q2", False, +1, d["lat"].abs().to_numpy()),
                                      ("Q3 b (log10 Phi)", "q3_b", False, -1, d["gamma"].to_numpy())) + tuple(
            (f"Q3 quintile {q} - 1", f"q3_q{q}", False, -1, d["gamma"].to_numpy()) for q in range(2, 6)):
        m, X, w, a = matrices(d, which, sym)
        r = m_verdict(units(d, m, X, w, a, y[m]), 0.0, pred)
        q2_main = "Q2 hemispheric phase"
        verdict_allowed = ((name.startswith("Q1 main") and acc["q1"]) or
                           (name == q2_main and acc["q2_hem"]))
        rows.append(dict(analysis=name, n=int(m.sum()), **{k: v for k, v in r.items() if k != "covered"},
                         verdict_reported=(r.get("verdict") if verdict_allowed else "descrittivo")))
    write(OUT_RUN, {"ESTIMATES.csv": pd.DataFrame(rows)},
          dict(protocol_sha256=protocol_sha, validation=acc, q2_main=Q2_MAIN,
               validation_meta_sha256=hashlib.sha256((OUT_VAL / "META.json").read_bytes()).hexdigest()))
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
    _D.update(d=d, mu=mu, mu_hem=lat_mean(d, "phase_hem"))
    cs = configs()
    i1 = [c["cfg"] for c in cs if c["test"] == "q1" and c["scenario"] == 1 and c["effect"] == 0][0]
    i2 = [c["cfg"] for c in cs if c["test"] == "q2_hem" and c["scenario"] == 1 and c["effect"] == 0][0]
    r1, r2 = unit((i1, 0)), unit((i2, 0))
    ok("one Q1 and one Q2 catalogue analysed by M", r1["verdict"] != "errore" and r2["verdict"] != "errore",
       (r1["verdict"], r2["verdict"]))
    mins = hemispheric_minima()
    ok("hemispheric minima inside their search windows", all(pd.Timestamp(HEM_MIN_WINDOWS[c][0] + "-01") <= v <=
       pd.Timestamp(HEM_MIN_WINDOWS[c][1] + "-01") for (c, h), v in mins.items()),
       {f"{c}{h}": v.strftime("%Y-%m") for (c, h), v in mins.items()})
    ok("hemispheric phase finite for every record", np.isfinite(d["phase_hem"]).all())
    mm, X, w, a = matrices(d, "q2_hem")
    muh = lat_mean(d, "phase_hem")
    ok("Q2 hemispheric phase: noise-free slope recovers +1.5",
       abs(a @ (muh + 1.5 * (d["A_monthly"].to_numpy() - 1)) - 1.5) < 1e-9)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "P.md"
        g1 = gate_problem("x" * 64, f)
        f.write_text("frozen text")
        sha_f = hashlib.sha256(f.read_bytes()).hexdigest()
        g2, g3 = gate_problem("y" * 64, f), gate_problem(sha_f, f)
    ok("gate: missing, wrong SHA-256 and uncommitted protocol all refused (temporary files; the real file not touched)",
       g1 == "frozen protocol missing" and g2 == "frozen protocol SHA-256 differs" and g3 == "frozen protocol not committed",
       (g1, g2, g3))
    ok("seeds and grid: 150 000 units in 35 configurations", len(tasks()) == 150_000 and len(cs) == 35, len(tasks()))
    # acceptance must fail on broken grids (Codex's counter-examples)
    def fake(rows_fn):
        recs = []
        for c in cs:
            for k in range(c["n"]):
                recs.append(dict(cfg=c["cfg"], k=k, seed=seed(c["cfg"], k), test=c["test"], role=c["role"],
                                 scenario=c["scenario"], sd_e=c["sd_e"], effect=c["effect"], **rows_fn(c, k)))
        return pd.DataFrame(recs)
    good = lambda c, k: dict(verdict="non deciso", covered=1, lo_above=0, hi_below=0)  # noqa: E731
    base = fake(good)
    acc0 = summarise(base)[1]
    q1_null = [c["cfg"] for c in cs if c["test"] == "q1" and c["effect"] == 0 and c["scenario"] == 0][0]
    only = base[base.cfg == q1_null].assign(verdict="errore")
    acc1, pr1 = summarise(only)[1:]
    dup = pd.concat([base, base.iloc[:1]])
    acc2 = summarise(dup)[1]
    bad_side = base.copy()
    sel = (bad_side.cfg == q1_null) & (bad_side.k < 200)
    bad_side.loc[sel, "verdict"] = "supportato"
    acc3 = summarise(bad_side)[1]
    bad_cov = base.copy()
    eff1 = [c["cfg"] for c in cs if c["test"] == "q2_hem" and c["effect"] > 0][0]
    sel = (bad_cov.cfg == eff1) & (bad_cov.k < 100)
    bad_cov.loc[sel, ["covered", "hi_below"]] = [0, 1]
    acc4 = summarise(bad_cov)[1]
    ok("acceptance: complete clean grid accepted", acc0 == {"q1": True, "q2_hem": True}, acc0)
    ok("acceptance: one scenario all in error (and the rest missing) refused for every test",
       acc1 == {"q1": False, "q2_hem": False} and pr1, acc1)
    ok("acceptance: duplicated row refused", acc2 == {"q1": False, "q2_hem": False})
    ok("acceptance: one side at 2 % in one null scenario refused for that test only",
       acc3 == {"q1": False, "q2_hem": True}, acc3)
    ok("acceptance: exclusion tail 5 % under effect refused for that test only", acc4 == {"q1": True, "q2_hem": False}, acc4)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def _ready(_):
    return len(_D["d"])


def benchmark():
    """Representative units on the real 12-process pool, start-up timed separately (workers load S first); units
    spread over every configuration with replica indices beyond the grid, so no grid seed is used."""
    cs = configs()
    sample = [(c["cfg"], c["n"] + 100 + j) for j in range(10) for c in cs]   # 350 units, k outside the grid
    t0 = time.time()
    with Pool(N_PROC, initializer=_init) as pool:
        pool.map(_ready, range(4 * N_PROC), chunksize=1)
        t_start = time.time() - t0
        t1 = time.time()
        pool.map(unit, sample, chunksize=2)
        t_run = time.time() - t1
    h = (t_run / len(sample)) * len(tasks()) / 3600 + t_start / 3600
    print(f"benchmark: start-up {t_start:.0f} s; {len(sample)} units in {t_run:.0f} s on {N_PROC} processes; "
          f"predicted {h:.2f} h for {len(tasks())} units")
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
