"""T5: sensitivity of power to signal shape, temporal noise and method on the fixed HMI design.

Plan docs/T5_POWER_SENSITIVITY_PLAN.md (frozen in 4b67632, SHA-256 fac76b1a...) and amendment A1
docs/T5_POWER_SENSITIVITY_PLAN_A1.md (8dc6d48, SHA-256 60323789...). Not a validation: synthetic catalogues
only, no real T5 slope, no verdict on quenching. Not blind.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_sensitivity.py --selftest    # plan §6 points 1-5 + A1 §1
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_sensitivity.py --gate        # plan §6 point 6
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_sensitivity.py --benchmark   # plan §3e/§6.7 + A1 §2
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_sensitivity.py --run         # single run (after review)

Implementation choices (not new decision rules; listed for the review):
- x_scale enters through the unchanged `V.responses`: nine scenario specs equal to P2f scenarios 1, 2, 7 plus the key
  `x_scale` are registered in memory in `V.SCENARIOS` under the new keys "ps0".."ps8" (the file p2f_validation.py is
  not modified; the original keys are checked unchanged). For x_scale = 1 the catalogue is bit-identical to P2f.
- The linear mean uses the cell mean activity of `V.cell_mean_activity` (the one of `V.responses` with beta_frac),
  checked equal to the activity column of the T5 cells; the S mean maps CELLS.csv rows to T5 cells by order, checked
  through A_cell and W_c against `run_p2.cells` on the design.
- Besides the L/S identity of A1 §1, each unit also checks the deterministic form of the §3a invariant on paired
  noise, beta_WLS(signal) - beta_WLS(N) = Delta_beta, with the slope tolerance tau_beta of A1 §1.
- G reuses the REML parameters and the variance-function coefficients returned by M; Var(beta_G) is the last
  diagonal element of (X' V^-1 X)^-1. A Cholesky failure of V_hat is an expected error of G.
- O failures and any exception other than the expected procedure errors are technical errors.
- Preliminary receipts are written under results/T5_POWER_SENSITIVITY_PRELIM/<MODE>_<commit12>/ and never
  overwritten; --run refuses unless selftest, gate and benchmark receipts exist for the same script SHA-256.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import traceback
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import LinAlgError, cho_factor, cho_solve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import diag_t5_oracle as D, p2d, p2f_pilot as P, p2f_validation as V, run_p2  # noqa: E402

PLAN = ROOT / "docs/T5_POWER_SENSITIVITY_PLAN.md"
AMEND = ROOT / "docs/T5_POWER_SENSITIVITY_PLAN_A1.md"
SHA_PLAN = "fac76b1ab60d0aba003bd3c895d03d2ecf9e894281a3465c175549b8d41a3fcd"
SHA_A1 = "603237898eed6b45b3102e1b7fdcf247fe2dfa8990107be7812095e9c6dab262"
CELLS = ROOT / "results/T5_PROXY_SENSITIVITY/CELLS.csv"
SUMMARY_PROXY = ROOT / "results/T5_PROXY_SENSITIVITY/SUMMARY.csv"
SHA_CELLS = "0c899647f3119501f7397364573fbe6ed57fa82243b1f44a523b01e1d0628f02"
SHA_SUMMARY_PROXY = "88a291100b9d68a0225f7dc77bcaf6c0bbabd2193424c23e8aa905ae2b055e30"
VALIDATION_RAW = ROOT / "results/P2F/VALIDATION_RAW.csv.gz"
SHA_VALIDATION_RAW = "9553f49ac4e0ec7a7209f366062552a1d3a6cd0933449b9002658aa80cff4178"
ORACLE_RAW = ROOT / "results/T5_ORACLE/ORACLE_RAW.csv.gz"
SHA_ORACLE_RAW = "d6d6400f364f85e2491332249f365eef8950c239a46dcd98b6279676ff76edaf"
P2F_DESIGN_PKL = ROOT / "results/P2F/_design.pkl"      # local, git-ignored: compared if present
OUT = ROOT / "results/T5_POWER_SENSITIVITY"
PRELIM = ROOT / "results/T5_POWER_SENSITIVITY_PRELIM"

ETA = V.ETA_BAR                                       # 3.56e-25 G/Mx
Z = V.Z                                               # Phi^-1(0.9875), full precision
SIGNALS = ("N", "L1", "L2", "S1", "S2")               # plan §3a
METHODS = ("M", "G", "B", "O")                        # plan §3c
PAIRS = (("L1", "S1"), ("L2", "S2"))
DMAX = {"S1": "0.10", "S2": "0.20"}
# plan §3a: e_L = e_ref of results/T5_PROXY_SENSITIVITY/SUMMARY.csv (39c010c), full representation
E_L = {"L1": -0.051494066951105075, "L2": -0.10305075387820256}
PLAN_DBETA = {"L1": -1.8331887834593406e-26, "L2": -3.668606838064011e-26}
DBETA = {"N": 0.0, "L1": E_L["L1"] * ETA, "S1": E_L["L1"] * ETA, "L2": E_L["L2"] * ETA, "S2": E_L["L2"] * ETA}
# plan §3b: forms outer, scales inner
FORMS = (("ar1_05", 1), ("ar1_09", 2), ("steps20", 7))
SCALES = (0.5, 1.0, 2.0)
NOISE = tuple((f, s, xs) for f, s in FORMS for xs in SCALES)          # n = 0..8
N_REP = 1000
N_PROC = 12
T_MAX_H = 8.0                                                           # A1 §2 stop
# A1 §1 tolerances
REL_SLOPE = 1e-12
ABS_SLOPE = 1e-38            # G/Mx
TOL_CELL = 1e-12 * ETA       # G/Mx, cell level
TOL_DIMLESS = 1e-12
TOL_SE_O = 1e-12             # relative
GATE_RTOL = 1e-9             # plan §6.6
O_RTOL = 1e-9                # plan §6.5


def tau_beta(sig):
    """A1 §1: tau_beta = 1e-12 |Delta_beta| + 1e-38 G/Mx."""
    return REL_SLOPE * abs(DBETA[sig]) + ABS_SLOPE


# ---------------------------------------------------------------- seeds (plan §3d, A1 §2)

def seed_base(n, k):
    return 31_000_000 + 100_000 * n + k


def seed_boot(n, k):
    return 32_000_000 + 100_000 * n + k


def seed_bench(n, r):
    return 33_000_000 + 4 * n + r


def seed_bench_boot(n, r):
    return 33_100_000 + 4 * n + r


def seed_self(j):
    if not 0 <= j < 50:
        raise ValueError("selftest seed index outside 0..49")
    return 33_000_050 + j


def seed_self_boot(j):
    if not 0 <= j < 50:
        raise ValueError("selftest seed index outside 0..49")
    return 33_100_050 + j


USED_RANGES = ([tuple(r) for r in P.USED] + [(3_000_000, 5_001_000), (6_000_000, 9_002_000),
                                             (20_000_000, 20_001_000), (28_000_000, 28_400_000),
                                             (29_500_000, 29_500_011)])


def seed_sets():
    return dict(
        grid_base=[seed_base(n, k) for n in range(9) for k in range(N_REP)],
        grid_boot=[seed_boot(n, k) for n in range(9) for k in range(N_REP)],
        bench_base=[seed_bench(n, r) for n in range(9) for r in range(4)],
        bench_boot=[seed_bench_boot(n, r) for n in range(9) for r in range(4)],
        self_base=[seed_self(j) for j in range(50)],
        self_boot=[seed_self_boot(j) for j in range(50)])


def seeds_check():
    s = seed_sets()
    allv = [x for v in s.values() for x in v]
    unique = len(set(allv)) == len(allv)
    clash = [x for x in allv if any(lo <= x < hi for lo, hi in USED_RANGES)]
    ranges = {k: (min(v), max(v)) for k, v in s.items()}
    expected = dict(grid_base=(31_000_000, 31_800_999), grid_boot=(32_000_000, 32_800_999),
                    bench_base=(33_000_000, 33_000_035), bench_boot=(33_100_000, 33_100_035),
                    self_base=(33_000_050, 33_000_099), self_boot=(33_100_050, 33_100_099))
    return unique and not clash and ranges == expected, dict(unique=unique, n_clash=len(clash), ranges=ranges)


# ---------------------------------------------------------------- errors and guards (plan §6, proxy script)

class TechnicalError(Exception):
    """Generator, mapping, pairing or provenance failure: invalidates the run (plan §6)."""


class ExpectedError(Exception):
    """Expected procedure error (M, G, B): an attempt kept in the denominator with its reason."""


def require_finite(name, *arrays):
    for a in arrays:
        if not np.all(np.isfinite(np.asarray(a, float))):
            raise TechnicalError(f"non-finite values in {name}")


def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a, runner=subprocess.run):
    """Run git and fail loudly: a failed command is never read as an empty (clean) answer."""
    p = runner(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise TechnicalError(f"git {' '.join(a)} failed ({p.returncode}): {p.stderr.strip()}")
    return p.stdout.strip()


def head_commit(git_fn=git):
    h = git_fn("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", h):
        raise TechnicalError(f"invalid HEAD commit {h!r}")
    return h


def tree_clean(git_fn=git):
    return git_fn("status", "--porcelain", "--untracked-files=no") == ""


def finite_json(obj):
    if isinstance(obj, dict):
        return {k: finite_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [finite_json(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return f"non-finite: {obj!r}"
    return obj


def write_meta(path, meta):
    """META always written (allow_nan=False); non-finite values make the outcome a technical error."""
    try:
        text = json.dumps(meta, indent=2, default=str, allow_nan=False)
        ok = True
    except ValueError:
        meta = finite_json(meta)
        meta["outcome"] = "non riuscito: valori non finiti in META"
        text = json.dumps(meta, indent=2, default=str, allow_nan=False)
        ok = False
    Path(path).write_text(text)
    return ok


def check_inputs():
    """Hashes of plan, A1 and the proxy outputs; e_L and Delta_beta against the stored representation."""
    for p, h in ((PLAN, SHA_PLAN), (AMEND, SHA_A1), (CELLS, SHA_CELLS), (SUMMARY_PROXY, SHA_SUMMARY_PROXY)):
        if sha(p) != h:
            raise TechnicalError(f"SHA-256 of {p.relative_to(ROOT)} differs from the frozen value")
    sm = pd.read_csv(SUMMARY_PROXY, float_precision="round_trip")
    for lab, dm in (("L1", 0.10), ("L2", 0.20)):
        row = sm[sm["delta_max"] == dm]
        if len(row) != 1:
            raise TechnicalError(f"SUMMARY.csv: no unique row for delta_max {dm}")
        if float(row["e_ref"].iloc[0]) != E_L[lab]:
            raise TechnicalError(f"e_L {lab} differs from e_ref in SUMMARY.csv")
        if abs(DBETA[lab] - PLAN_DBETA[lab]) > tau_beta(lab):
            raise TechnicalError(f"Delta_beta {lab} differs from the plan value")
        if abs(float(row["delta_beta_G_per_Mx"].iloc[0]) - DBETA[lab]) > tau_beta(lab):
            raise TechnicalError(f"Delta_beta {lab} differs from g . Delta_eta stored in SUMMARY.csv")


# ---------------------------------------------------------------- noise configurations (plan §3b)

def register_specs():
    """Register 'ps0'..'ps8' = P2f scenario spec + x_scale in V.SCENARIOS (in memory only)."""
    for n, (form, s, xs) in enumerate(NOISE):
        base = V.SCENARIOS[s]
        if "x_scale" in base:
            raise TechnicalError(f"scenario {s} already has x_scale")
        spec = dict(base, x_scale=xs)
        key = f"ps{n}"
        if key in V.SCENARIOS and V.SCENARIOS[key] != spec:
            raise TechnicalError(f"key {key} already used with another spec")
        V.SCENARIOS[key] = spec


ORIGINAL_SPECS = {s: dict(V.SCENARIOS[s]) for s in (1, 2, 7)}
register_specs()


def noise_catalogue(design, n, seed):
    """Base noise catalogue of plan §3a: V.responses with beta_frac = 0 and the configuration's x_scale."""
    return V.responses(design, f"ps{n}", np.random.default_rng(seed), 0.0)


# ---------------------------------------------------------------- per-design statics (plan §3a)

class Statics:
    """Everything that depends only on the design: record -> T5 cell map, the five added means, references."""

    def __init__(self, design):
        self.design = design
        dd0 = V.responses(design, 1, np.random.default_rng(0), 0.0, noise=False)     # rng unused without noise
        u0 = V.units(dd0, "T5")
        if u0["n_check"] != V.EXPECTED["T5"]:
            raise TechnicalError(f"T5 design {u0['n_check']} differs from {V.EXPECTED['T5']}")
        self.u0 = u0
        self.cell_cr, self.cell_hem = u0["cell_cr"].copy(), np.asarray(u0["cell_hem"]).copy()
        idx = {(int(c), h): j for j, (c, h) in enumerate(zip(self.cell_cr, self.cell_hem))}
        if len(idx) != len(self.cell_cr):
            raise TechnicalError("duplicate T5 cell keys")
        keys = zip(design["CR"].astype(int), design["hemisphere"])
        self.rec_cell = np.array([idx.get((int(c), h), -1) for c, h in keys])
        self.phi = design["phi"].to_numpy(float)
        self.abar_rec = V.cell_mean_activity(design) - 1.0
        cells = pd.read_csv(CELLS, float_precision="round_trip")
        if len(cells) != len(self.cell_cr) or not np.array_equal(cells["cell"].to_numpy(), np.arange(len(cells))):
            raise TechnicalError("CELLS.csv rows do not match the T5 cells")
        self.cells = cells
        self.d_eta = {s: cells[f"delta_eta_dmax_{DMAX[s]}"].to_numpy(float) for s in ("S1", "S2")}
        require_finite("CELLS.csv", cells[["A_cell", "W_c"]].to_numpy(), *self.d_eta.values())
        require_finite("design", self.phi, self.abar_rec)
        self.add = {"N": np.zeros(len(design))}
        for s in ("L1", "L2"):
            self.add[s] = self.phi * ETA * E_L[s] * self.abar_rec
        for s in ("S1", "S2"):
            d = np.where(self.rec_cell >= 0, self.d_eta[s][np.maximum(self.rec_cell, 0)], 0.0)
            self.add[s] = self.phi * d
        for s, a in self.add.items():
            require_finite(f"added mean {s}", a)

    def linear(self, e):
        """Linear mean with an arbitrary e (used only by selftest and gate)."""
        return self.phi * ETA * e * self.abar_rec


def build_units(st, base, add):
    dd = base.assign(d_star=base["d_star"].to_numpy(float) + add)
    require_finite("injected d_star", dd["d_star"].to_numpy())
    u = V.units(dd, "T5")
    if u["n_check"] != V.EXPECTED["T5"]:
        raise TechnicalError(f"T5 units {u['n_check']}")
    if not (np.array_equal(u["cell_cr"], st.cell_cr) and np.array_equal(np.asarray(u["cell_hem"]), st.cell_hem)):
        raise TechnicalError("T5 cells differ from the reference cells")
    require_finite("T5 units", u["eta_c"], u["W_c"], u["Xf_c"], u["g"], [u["beta"]])
    return u, dd


# ---------------------------------------------------------------- methods (plan §3c)

def verdict_interval(lo, hi):
    return "supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso")


def method_m(u):
    try:
        r = V.procedure_m(u)
    except V.CandidateError as exc:
        raise ExpectedError(str(exc)) from None
    return r


def gls_last(X, Vm, y):
    """Last element of (X' V^-1 X)^-1 X' V^-1 y and of the diagonal of (X' V^-1 X)^-1."""
    try:
        cf = cho_factor(Vm, lower=True, check_finite=True)
    except (LinAlgError, ValueError) as exc:
        raise ExpectedError(f"V_hat non definita positiva: {exc}") from None
    ViX = cho_solve(cf, X, check_finite=False)
    A = X.T @ ViX
    try:
        Ainv = np.linalg.inv(A)
    except np.linalg.LinAlgError as exc:
        raise ExpectedError(f"X'V^-1X singolare: {exc}") from None
    coef = Ainv @ (ViX.T @ y)
    return float(coef[-1]), float(Ainv[-1, -1])


def g_sig2(u, rm):
    """Individual variance of M rebuilt from its returned coefficients (same formula as V.procedure_m)."""
    logphi = np.log(u["phi"])
    m = float(np.mean(logphi))
    return np.exp(rm["var_a"] + rm["var_b"] * (logphi - m))


def method_g(u, rm):
    sig2 = g_sig2(u, rm)
    yc, Xc, vc, b, t, h, ind = V.cell_level(u, sig2)
    Vh = rm["sigma_x2"] * P.ar1_k(t, h, rm["phi"], rm["kappa"]) + np.diag(vc)
    beta, var = gls_last(Xc, Vh, yc)
    if not (np.isfinite(beta) and np.isfinite(var) and var > 0):
        raise ExpectedError("beta_G o Var(beta_G) non finite o non positive")
    se = math.sqrt(var)
    lo, hi = beta - Z * se, beta + Z * se
    return dict(beta=beta, se=se, stat=beta / se, lo=lo, hi=hi, verdict=verdict_interval(lo, hi))


def b_adapter(u):
    """Plan §3c: units of V.units(dd, 'T5') -> dict expected by P.b_units."""
    return dict(level="cell", eta_c=u["eta_c"], W_c=u["W_c"], Xf_c=u["Xf_c"], Xn_c=u["Xf_c"][:, :-1],
                cell_cr=u["cell_cr"])


def method_b(u, seed):
    try:
        r = P.candidate_b(b_adapter(u), seed)
    except V.CandidateError as exc:
        raise ExpectedError(str(exc)) from None
    return dict(r, verdict=P.verdict_b(r))


def o_variance(u, n):
    """True variance of the WLS slope under the generator of configuration n (A3 of T5-D2 with x_scale)."""
    form, s, xs = NOISE[n]
    yc, Xc, vc, b, t, h, ind = V.cell_level(u, np.full(len(u["y"]), ETA ** 2))
    Kt = D.k_true(t, h, s)
    sx2 = (0.5 * ETA * xs) ** 2
    return sx2 * float(b @ Kt @ b) + ind, Kt, sx2


def method_o(u, n):
    var, _, _ = o_variance(u, n)
    if not (np.isfinite(var) and var > 0):
        raise TechnicalError("O: true variance not finite or not positive")
    se = math.sqrt(var)
    beta = u["beta"]
    lo, hi = beta - Z * se, beta + Z * se
    return dict(beta=beta, se=se, stat=beta / se, lo=lo, hi=hi, verdict=verdict_interval(lo, hi))


M_EXTRA = ("var_a", "var_b", "n_varfun", "n_zero_residuals", "phi", "kappa", "sigma_x2", "n_valid_starts",
           "sigma_x_at_lower", "neg_reml")


def analyse(u, n, sig, boot):
    """The four methods on one response. Returns {method: row}."""
    target = DBETA[sig]
    out = {}

    def base_row(method):
        return dict(method=method, signal=sig, target=target, beta_wls=u["beta"], state="ok", reason="")

    def fill(row, r):
        row.update(beta=r["beta"], se=r.get("se", np.nan), lo=r.get("lo", np.nan), hi=r.get("hi", np.nan),
                   stat=r["stat"], verdict=r["verdict"])
        if "lo" in r:
            row.update(covered=int(r["lo"] <= target <= r["hi"]), below=int(r["lo"] > target),
                       above=int(r["hi"] < target))
        return row

    rm = None
    row = base_row("M")
    try:
        rm = method_m(u)
        fill(row, rm)
        row.update({k: rm[k] for k in M_EXTRA})
    except ExpectedError as exc:
        row.update(verdict="errore", state="errore previsto", reason=str(exc))
    out["M"] = row
    row = base_row("G")
    if rm is None:
        row.update(verdict="errore", state="errore previsto", reason="M senza REML: " + out["M"]["reason"])
    else:
        try:
            fill(row, method_g(u, rm))
            row.update(beta_g_minus_wls=row["beta"] - u["beta"])
        except ExpectedError as exc:
            row.update(verdict="errore", state="errore previsto", reason=str(exc))
    out["G"] = row
    row = base_row("B")
    try:
        rb = method_b(u, boot)
        row.update(beta=u["beta"], stat=rb["stat"], p_low=rb["p_low"], p_high=rb["p_high"],
                   n_cluster=rb["n_clusters"], verdict=rb["verdict"],
                   reason="n/a: B restituisce solo p-value (SE, intervallo, copertura)")
    except ExpectedError as exc:
        row.update(verdict="errore", state="errore previsto", reason=str(exc))
    out["B"] = row
    row = base_row("O")
    fill(row, method_o(u, n))
    out["O"] = row
    return out


# ---------------------------------------------------------------- A1 §1 identities and boundary cases

def classify_o_pair(oL, oS, tau_b):
    """Returns None (identical verdicts) or a boundary-case dict; raises TechnicalError otherwise (A1 §1)."""
    if oL["state"] != "ok" or oS["state"] != "ok":
        raise TechnicalError("O not available for a paired L/S response")
    if abs(oL["beta"] - oS["beta"]) > tau_b:
        raise TechnicalError(f"O beta differs between L and S: {oL['beta']!r} vs {oS['beta']!r}")
    if abs(oL["se"] - oS["se"]) > TOL_SE_O * max(oL["se"], oS["se"]):
        raise TechnicalError(f"O SE differs between L and S: {oL['se']!r} vs {oS['se']!r}")
    if oL["verdict"] == oS["verdict"]:
        return None
    vs = {oL["verdict"], oS["verdict"]}
    if vs == {"supportato", "opposto"}:
        raise TechnicalError("O verdicts supportato vs opposto between paired L and S")
    ends = (["hi"] if "supportato" in vs else []) + (["lo"] if "opposto" in vs else [])
    tau_v = tau_b + Z * abs(oL["se"] - oS["se"])
    dist = min(abs(o[e]) for o in (oL, oS) for e in ends)
    if dist > tau_v:
        raise TechnicalError(f"O verdicts differ ({oL['verdict']} / {oS['verdict']}) outside the boundary tolerance")
    return dict(verdict_L=oL["verdict"], verdict_S=oS["verdict"], endpoint=",".join(ends),
                lo_L=oL["lo"], hi_L=oL["hi"], lo_S=oS["lo"], hi_S=oS["hi"], se_L=oL["se"], se_S=oS["se"],
                tau_v=tau_v, min_endpoint_distance=dist)


def unit_identities(res):
    """§3a invariant on paired noise and A1 §1 L/S identities; returns (boundary cases, diagnostics)."""
    diag = {}
    bN = res["N"]["M"]["beta_wls"]
    for sig in SIGNALS[1:]:
        dev = (res[sig]["M"]["beta_wls"] - bN) - DBETA[sig]
        diag[f"dev_wls_{sig}_over_tau"] = abs(dev) / tau_beta(sig)
        if abs(dev) > tau_beta(sig):
            raise TechnicalError(f"beta_WLS({sig}) - beta_WLS(N) differs from Delta_beta by {dev!r}")
    bounds = []
    for L, S in PAIRS:
        d = res[L]["M"]["beta_wls"] - res[S]["M"]["beta_wls"]
        diag[f"dev_wls_{L}{S}_over_tau"] = abs(d) / tau_beta(L)
        if abs(d) > tau_beta(L):
            raise TechnicalError(f"beta_WLS({L}) != beta_WLS({S}): {d!r}")
        b = classify_o_pair(res[L]["O"], res[S]["O"], tau_beta(L))
        if b is not None:
            bounds.append(dict(pair=f"{L}/{S}", **b))
    return bounds, diag


# ---------------------------------------------------------------- the unit of work (A1 §2)

_ST = None


def _init(design):
    global _ST
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    _ST = Statics(design)


def unit(n, k, seed, boot, st=None):
    """One base noise catalogue (n, k) x 5 signals x 4 methods, with the identities checked inside."""
    st = st or _ST
    base = noise_catalogue(st.design, n, seed)
    require_finite("noise catalogue", base["d_star"].to_numpy())
    res = {}
    for sig in SIGNALS:
        u, _ = build_units(st, base, st.add[sig])
        res[sig] = analyse(u, n, sig, boot)
    bounds, diag = unit_identities(res)
    form, s, xs = NOISE[n]
    rows = []
    for sig in SIGNALS:
        for m in METHODS:
            rows.append(dict(n=n, form=form, x_scale=xs, k=k, seed_base=seed, seed_boot=boot, **res[sig][m]))
    for b in bounds:
        b.update(n=n, k=k, seed_base=seed)
    return rows, bounds, diag


def work(task):
    """Pool task: wall and CPU time measured by the worker; every exception recorded (technical)."""
    n, k, seed, boot = task
    t0, c0 = time.perf_counter(), time.process_time()
    try:
        rows, bounds, diag = unit(n, k, seed, boot)
        tech = None
    except Exception as exc:                       # noqa: BLE001 - every failure is recorded, never hidden
        rows, bounds, diag = [], [], {}
        tech = dict(n=n, k=k, seed_base=seed, exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
    return dict(n=n, k=k, seed_base=seed, seed_boot=boot, wall_s=time.perf_counter() - t0,
                cpu_s=time.process_time() - c0, pid=os.getpid(), rows=rows, bounds=bounds, diag=diag, tech=tech)


def predicted_duration_s(tbar_by_n, n_rep=N_REP, n_proc=N_PROC):
    """A1 §2, explicit: T_hat = (1000 / 12) * sum_{n=0}^{8} tbar_n.

    tbar_n is the mean wall time, measured by the worker under the 12-process load, of one unit of work of noise
    configuration n; each unit comprises the five signals (N, L1, L2, S1, S2) and the four methods (M, G, B, O).
    The grid has 1000 units per configuration spread over 12 processes."""
    t = [float(x) for x in tbar_by_n]
    if len(t) != 9 or not all(math.isfinite(x) and x > 0 for x in t):
        raise TechnicalError("tbar must hold 9 finite positive values (n = 0..8)")
    return (n_rep / n_proc) * sum(t)


# ---------------------------------------------------------------- summaries (plan §4, §5)

def binom_mcse(c, n):
    p = c / n
    return math.sqrt(p * (1 - p) / n)


def summarize(raw):
    rows = []
    for (n, sig, m), g in raw.groupby(["n", "signal", "method"], sort=True):
        N = len(g)
        ok = g[g["state"] == "ok"]
        cnt = {v: int((g["verdict"] == v).sum()) for v in ("supportato", "opposto", "non deciso", "errore")}
        row = dict(n=n, form=g["form"].iloc[0], x_scale=g["x_scale"].iloc[0], signal=sig, method=m, N=N,
                   target=g["target"].iloc[0], **{f"n_{k.replace(' ', '_')}": v for k, v in cnt.items()})
        for k, v in cnt.items():
            row[f"frac_{k.replace(' ', '_')}"] = v / N
            row[f"mcse_{k.replace(' ', '_')}"] = binom_mcse(v, N)
        if sig == "N":
            f = cnt["supportato"] + cnt["opposto"]
            row.update(false_total=f, false_frac=f / N, false_mcse=binom_mcse(f, N))
        if m in ("M", "G", "O"):
            cov = int(g["covered"].fillna(0).sum())
            row.update(covered=cov, coverage=cov / N, coverage_mcse=binom_mcse(cov, N),
                       below=int(g["below"].fillna(0).sum()), above=int(g["above"].fillna(0).sum()))
            if len(ok) > 1:
                vb = float(np.var(ok["beta"], ddof=1))
                row.update(n_valid=len(ok), mean_beta=float(ok["beta"].mean()), sd_beta=math.sqrt(vb),
                           mean_se=float(ok["se"].mean()),
                           R=float(np.mean(ok["se"] ** 2) / vb) if vb > 0 else np.nan,
                           mean_beta_wls_valid=float(ok["beta_wls"].mean()))
            if m == "G" and len(ok) > 1:
                row.update(bias_G=float(ok["beta"].mean()) - row["target"],
                           mean_G_minus_WLS=float(ok["beta_g_minus_wls"].mean()),
                           sd_G_minus_WLS=float(np.std(ok["beta_g_minus_wls"], ddof=1)))
        else:
            row.update(covered="n/a", coverage="n/a", mean_se="n/a", R="n/a")
        rows.append(row)
    summ = pd.DataFrame(rows)
    # beta_WLS on all constructed catalogues (one per response: the M rows)
    w = raw[raw["method"] == "M"].groupby(["n", "signal"])["beta_wls"].agg(["count", "mean", "std"]).reset_index()
    w = w.rename(columns={"count": "n_constructed", "mean": "mean_beta_wls_all", "std": "sd_beta_wls_all"})
    summ = summ.merge(w, on=["n", "signal"], how="left")
    return summ


def paired_ls(raw):
    """Plan §5.1: paired difference of 'supportato' between S and L on the same noise (T5-D2 §6.5 formula)."""
    out = []
    key = ["n", "k", "method"]
    for L, S in PAIRS:
        a = raw[raw["signal"] == L].set_index(key)["verdict"]
        b = raw[raw["signal"] == S].set_index(key)["verdict"]
        j = pd.concat([a.rename("L"), b.rename("S")], axis=1, join="inner")
        for (n, m), g in j.groupby(level=[0, 2]):
            eL, eS = g["L"] == "supportato", g["S"] == "supportato"
            N = len(g)
            bb, cc = int((eL & ~eS).sum()), int((eS & ~eL).sum())
            se = math.sqrt((bb + cc - (cc - bb) ** 2 / N) / (N * (N - 1))) if N > 1 else np.nan
            out.append(dict(n=n, method=m, pair=f"{S}-{L}", N=N, b_only_L=bb, c_only_S=cc, delta=(cc - bb) / N,
                            se_paired=se))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- provenance helpers

def provenance(git_fn=git):
    return dict(git_commit=head_commit(git_fn), git_dirty=0, sha256_plan=sha(PLAN), sha256_A1=sha(AMEND),
                sha256_script=sha(__file__), sha256_proxy_CELLS=sha(CELLS), sha256_proxy_SUMMARY=sha(SUMMARY_PROXY),
                env=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                         OMP_NUM_THREADS=os.environ.get("OMP_NUM_THREADS")))


def guard_start(git_fn=git):
    if os.environ.get("OMP_NUM_THREADS") != "1":
        print("OMP_NUM_THREADS must be 1: refusing to run")
        return False
    try:
        if not tree_clean(git_fn):
            print("tracked tree not clean: refusing to run")
            return False
    except TechnicalError as exc:
        print(f"refusing to run: {exc}")
        return False
    return True


def load_design():
    d = P.build_design()
    info = {}
    if P2F_DESIGN_PKL.exists():
        same = d.equals(pd.read_pickle(P2F_DESIGN_PKL))
        info["design_equals_P2F_design_pkl"] = bool(same)
        if not same:
            raise TechnicalError("reconstructed design differs from results/P2F/_design.pkl")
    else:
        info["design_equals_P2F_design_pkl"] = "file locale assente"
    info["design_rows"] = len(d)
    info["design_hash"] = str(int(pd.util.hash_pandas_object(d, index=True).sum() % (2 ** 63)))
    return d, info


def prelim_dir(mode, commit):
    return PRELIM / f"{mode}_{commit[:12]}"


# ---------------------------------------------------------------- selftest (plan §6 points 1-5, A1 §1)

def selftest_checks(st, ok):
    design = st.design
    # 1. seeds
    good, info = seeds_check()
    ok("1 seeds: base, bootstrap, benchmark and selftest unique, disjoint from used ranges, expected ranges",
       good, json.dumps(info["ranges"]) + f"; clashes {info['n_clash']}")
    # inputs
    try:
        check_inputs()
        ok("inputs: SHA-256 of plan, A1, CELLS.csv, SUMMARY.csv; e_L = e_ref; Delta_beta = plan value", True, "")
    except TechnicalError as exc:
        ok("inputs: SHA-256 of plan, A1, CELLS.csv, SUMMARY.csv; e_L = e_ref; Delta_beta = plan value", False, str(exc))
    ok("registered specs: original scenarios 1, 2, 7 unchanged; ps<n> = original + x_scale",
       all(V.SCENARIOS[s] == ORIGINAL_SPECS[s] for s in (1, 2, 7))
       and all(V.SCENARIOS[f"ps{n}"] == dict(ORIGINAL_SPECS[s], x_scale=xs) for n, (_, s, xs) in enumerate(NOISE)), "")
    # 2a. mapping and injection without noise
    u0 = st.u0
    c = run_p2.cells(V.responses(design, 1, np.random.default_rng(0), 0.0, noise=False), V.ACT, "d_star")
    a_cell = st.cells["A_cell"].to_numpy(float)
    w_cell = st.cells["W_c"].to_numpy(float)
    dA = float(np.max(np.abs(a_cell - (u0["Xf_c"][:, -1] + 1.0))))
    dA2 = float(np.max(np.abs(a_cell - c["abar"].to_numpy(float))))
    dW = float(np.max(np.abs(w_cell - u0["W_c"]) / u0["W_c"]))
    dW2 = float(np.max(np.abs(w_cell - c["phi"].to_numpy(float)) / w_cell))
    keys_ok = (len(c) == 318 and np.array_equal(c["CR"].astype(int).to_numpy(), st.cell_cr)
               and np.array_equal(c["hemisphere"].to_numpy(), st.cell_hem))
    ok("2a mapping: CELLS.csv A_cell and W_c equal run_p2.cells and the T5 units (318 cells, same order)",
       keys_ok and max(dA, dA2) <= TOL_DIMLESS and max(dW, dW2) <= TOL_DIMLESS,
       f"max|dA| {max(dA, dA2):.3e}, max rel dW {max(dW, dW2):.3e}")
    in_t5 = st.rec_cell >= 0
    dab = float(np.max(np.abs(st.abar_rec[in_t5] - u0["Xf_c"][st.rec_cell[in_t5], -1])))
    ok("2a linear mean: V.cell_mean_activity - 1 equals the T5 activity column on the 2375 T5 records",
       int(in_t5.sum()) == 2375 and dab <= TOL_DIMLESS, f"{int(in_t5.sum())} records, max|d| {dab:.3e}")
    base0 = V.responses(design, 1, np.random.default_rng(0), 0.0, noise=False)
    for s in ("S1", "S2"):
        u, _ = build_units(st, base0, st.add[s])
        d = float(np.max(np.abs(u["eta_c"] - (ETA + st.d_eta[s]))))
        ok(f"2a {s} without noise: eta_c = eta_bar + Delta_eta_c on 318 cells (|d| <= 1e-12 eta_bar)",
           d <= TOL_CELL, f"max|d| {d:.3e} G/Mx")
        e = float(st.u0["g"] @ st.d_eta[s]) / ETA
        lab = "L1" if s == "S1" else "L2"
        ok(f"2a g . Delta_eta_{s} / eta_bar = e_{lab} (|d| <= 1e-12)", abs(e - E_L[lab]) <= TOL_DIMLESS,
           f"{e!r} vs {E_L[lab]!r}")
    for s in ("L1", "L2"):
        u, _ = build_units(st, base0, st.add[s])
        expect = ETA * (1.0 + E_L[s] * (u0["Xf_c"][:, -1]))
        d = float(np.max(np.abs(u["eta_c"] - expect)))
        ok(f"2a {s} without noise: eta_c = eta_bar (1 + e_L (A_c - 1)) (|d| <= 1e-12 eta_bar)", d <= TOL_CELL,
           f"max|d| {d:.3e} G/Mx")
        e = float(u0["g"] @ (ETA * E_L[s] * u0["Xf_c"][:, -1])) / ETA
        ok(f"2a g . (eta_bar e_{s} (A - 1)) / eta_bar = e_{s} (|d| <= 1e-12)", abs(e - E_L[s]) <= TOL_DIMLESS, f"{e!r}")
    g1 = float(np.abs(u0["g"] @ np.ones(318)))
    ga = float(abs(u0["g"] @ u0["Xf_c"][:, -1] - 1.0))
    ok("2a g . 1 = 0 and g . (A - 1) = 1 (|d| <= 1e-12)", g1 <= TOL_DIMLESS and ga <= TOL_DIMLESS,
       f"{g1:.3e}, {ga:.3e}")
    # registration: x_scale = 1 bit-identical to P2f; x_scale scaling of the temporal part
    for j, (n, s) in enumerate(((1, 1), (4, 2), (7, 7))):
        a = noise_catalogue(design, n, seed_self(23 + j))["d_star"].to_numpy()
        b = V.responses(design, s, np.random.default_rng(seed_self(23 + j)), 0.0)["d_star"].to_numpy()
        ok(f"2 noise: configuration {n} (x_scale 1) bit-identical to V.responses scenario {s}", np.array_equal(a, b), "")
    for j, f0 in enumerate((0, 3, 6)):
        sd = seed_self(26 + j)
        f = [noise_catalogue(design, f0 + i, sd)["d_star"].to_numpy() / (st.phi * ETA) for i in range(3)]
        d = float(np.max(np.abs((f[2] - f[1]) - 2.0 * (f[1] - f[0]))))
        nz = float(np.max(np.abs(f[1] - f[0])))
        ok(f"2 noise: {NOISE[f0][0]} temporal part scales with x_scale (f(2)-f(1) = 2(f(1)-f(0.5)), |d| <= 1e-12)",
           d <= TOL_DIMLESS and nz > 0, f"max|d| {d:.3e}, max|f(1)-f(0.5)| {nz:.3e}")
    # 2e. L with e = -0.1 vs V.responses beta_frac = -0.1
    for j, (n, s) in enumerate(((1, 1), (4, 2), (7, 7))):
        sd = seed_self(20 + j)
        base = noise_catalogue(design, n, sd)
        u, _ = build_units(st, base, st.linear(-0.1))
        uv = V.units(V.responses(design, s, np.random.default_rng(sd), -0.1), "T5")
        d = float(np.max(np.abs(u["eta_c"] - uv["eta_c"])))
        tb = REL_SLOPE * 0.1 * ETA + ABS_SLOPE
        ok(f"2e L with e = -0.1 equals V.responses beta_frac = -0.1 (scenario {s}): eta_c and beta_WLS",
           d <= TOL_CELL and abs(u["beta"] - uv["beta"]) <= tb,
           f"max|d eta_c| {d:.3e}, |d beta| {abs(u['beta'] - uv['beta']):.3e} (tau {tb:.3e})")
    # 2d + whole unit with noise, one per configuration: identities, G reuse, B, O
    worst, nb, gre, units_ok = {}, 0, 0.0, True
    for n in range(9):
        try:
            rows, bounds, diag = unit(n, -1, seed_self(n), seed_self_boot(n), st)
        except TechnicalError as exc:
            units_ok = False
            ok(f"2d unit with noise, configuration {n}", False, str(exc))
            continue
        nb += len(bounds)
        for k, v in diag.items():
            worst[k] = max(worst.get(k, 0.0), v)
        # G reuse: M's variance formula with the rebuilt individual variance gives M's SE
        base = noise_catalogue(design, n, seed_self(n))
        u, _ = build_units(st, base, st.add["S2"])
        try:
            rm = method_m(u)
            yc, Xc, vc, b, t, h, ind = V.cell_level(u, g_sig2(u, rm))
            var = rm["sigma_x2"] * float(b @ P.ar1_k(t, h, rm["phi"], rm["kappa"]) @ b) + ind
            gre = max(gre, abs(math.sqrt(var) - rm["se"]) / rm["se"])
        except ExpectedError:
            pass
    ok("2d with noise (9 units, one per configuration): beta_WLS(L) = beta_WLS(S) and signal - N = Delta_beta "
       "within tau_beta; O SE within 1e-12 rel.; O verdicts equal or boundary", units_ok,
       f"worst dev/tau {json.dumps({k: float(f'{v:.3g}') for k, v in worst.items()})}; boundary cases {nb}")
    ok("3 G reuses M: individual variance rebuilt from var_a, var_b reproduces M's SE (rel <= 1e-12)",
       gre <= 1e-12, f"max rel {gre:.3e}")
    # 3. G on synthetic cases
    X = np.column_stack([np.ones(3), np.array([0.0, 1.0, 2.0])])
    y = np.array([0.0, 0.0, 1.0])
    w = np.array([1.0, 1.0, 100.0])
    b_ols, _ = gls_last(X, np.eye(3), y)
    b_gls, _ = gls_last(X, np.diag(1.0 / w), y)
    swX, swy = X * np.sqrt(w)[:, None], y * np.sqrt(w)
    b_wls = float(np.linalg.lstsq(swX, swy, rcond=None)[0][-1])
    ok("3 G hand example: OLS 0.5, WLS = GLS(diag(1/w)) = 100/167",
       abs(b_ols - 0.5) <= 1e-12 and abs(b_gls - 100 / 167) <= 1e-12 and abs(b_wls - 100 / 167) <= 1e-12,
       f"OLS {b_ols!r}, GLS {b_gls!r}, WLS {b_wls!r}")
    rng = np.random.default_rng(seed_self(30))
    Xs = np.column_stack([np.ones(40), rng.normal(size=(40, 2))])
    Lm = rng.normal(size=(40, 40))
    Vs = Lm @ Lm.T + 40 * np.eye(40)
    ys = Xs @ np.array([1.0, 2.0, -3.0]) + rng.normal(size=40)
    Vi = np.linalg.inv(Vs)
    Ai = np.linalg.inv(Xs.T @ Vi @ Xs)
    ref_b, ref_v = float((Ai @ Xs.T @ Vi @ ys)[-1]), float(Ai[-1, -1])
    gb, gv = gls_last(Xs, Vs, ys)
    ok("3 G synthetic known V: equals the explicit GLS solution and variance (rel <= 1e-10)",
       abs(gb - ref_b) <= 1e-10 * abs(ref_b) and abs(gv - ref_v) <= 1e-10 * ref_v, f"{gb!r} vs {ref_b!r}")
    base = noise_catalogue(design, 4, seed_self(31))
    u, _ = build_units(st, base, st.add["S1"])
    gw, _ = gls_last(u["Xf_c"], 2.5e-49 * np.diag(1.0 / u["W_c"]), u["eta_c"])
    ok("3 G on the T5 design: V = sigma^2 diag(1/W_c) returns the WLS slope g . eta (rel <= 1e-10)",
       abs(gw - u["beta"]) <= 1e-10 * abs(u["beta"]), f"{gw!r} vs {u['beta']!r}")
    # 4. B adapter vs original path, 10 catalogues
    same, det = True, []
    for j in range(10):
        n, sig = j % 9, SIGNALS[j % 5]
        base = noise_catalogue(design, n, seed_self(10 + j))
        u, dd = build_units(st, base, st.add[sig])
        ut = P.test_units(dd, "T5")
        ad = b_adapter(u)
        eq_units = all(np.array_equal(ad[k], ut[k]) for k in ("eta_c", "W_c", "Xf_c", "Xn_c", "cell_cr"))
        ra = P.candidate_b(ad, seed_self_boot(10 + j))
        rt = P.candidate_b(ut, seed_self_boot(10 + j))
        e = eq_units and all(ra[k] == rt[k] for k in ("stat", "p_low", "p_high", "n_clusters")) \
            and P.verdict_b(ra) == P.verdict_b(rt)
        same &= e
        det.append(f"{ra['n_clusters']}")
    ok("4 B adapter: units, statistic, p_low, p_high, clusters and verdict identical to P.test_units on 10 catalogues",
       same, "clusters " + ",".join(det))
    cl = (st.cell_cr - st.cell_cr.min()) // P.BLOCK
    ok("4 B clusters: blocks of 13 CR from the first T5 CR 2097", int(st.cell_cr.min()) == 2097 and P.BLOCK == 13,
       f"first CR {int(st.cell_cr.min())}, {len(np.unique(cl))} blocks")
    # 5. O reproduces A3 of T5-D2 on validation catalogues; covariance and scale
    if sha(ORACLE_RAW) != SHA_ORACLE_RAW:
        ok("5 O vs A3: ORACLE_RAW SHA-256", False, "hash differs")
    else:
        orc = pd.read_csv(ORACLE_RAW, float_precision="round_trip", keep_default_na=False, na_values=["", "nan", "NaN"],
                          low_memory=False, usecols=["kind", "scenario", "k", "arm", "beta", "se"])
        orc = orc[(orc["arm"] == "A3") & (orc["kind"] == "null")].set_index(["scenario", "k"])
        worst_o, good_o = 0.0, True
        for n, s in ((7, 7), (1, 1), (4, 2)):
            for k in range(5):
                base = noise_catalogue(design, n, V.seed_null(s, k))
                u, _ = build_units(st, base, st.add["N"])
                r = method_o(u, n)
                ref = orc.loc[(s, k)]
                rel = abs(r["se"] - ref["se"]) / ref["se"]
                worst_o = max(worst_o, rel)
                good_o &= rel <= O_RTOL and abs(r["beta"] - ref["beta"]) <= GATE_RTOL * abs(ref["beta"])
        ok("5 O reproduces A3 of T5-D2: 5 null catalogues of scenario 7 (plus 5 each of scenarios 1, 2), "
           "SE rel <= 1e-9", good_o, f"max rel {worst_o:.3e}")
    u = st.u0
    for n in (6, 7, 8):
        _, Kt, sx2 = o_variance(u, n)
        t, h = u["cell_cr"] - u["cell_cr"].min(), (np.asarray(u["cell_hem"]) == "S").astype(int)
        Kref = D.k_steps(np.abs(t[:, None] - t[None, :]), 20) * (h[:, None] == h[None, :])
        ok(f"5 O steps20 x_scale {NOISE[n][2]}: K = K_steps(L=20, independent hemispheres), scale (0.5 eta x_scale)^2",
           np.array_equal(Kt, Kref) and sx2 == (0.5 * ETA * NOISE[n][2]) ** 2, f"sx2 {sx2!r}")
    for n in (0, 4):
        _, Kt, _ = o_variance(u, n)
        s = NOISE[n][1]
        t, h = u["cell_cr"] - u["cell_cr"].min(), (np.asarray(u["cell_hem"]) == "S").astype(int)
        ok(f"5 O {NOISE[n][0]}: K = AR(1) of the P2f scenario {s}",
           np.array_equal(Kt, P.ar1_k(t, h, V.SCENARIOS[s]["phi"], V.SCENARIOS[s]["kappa"])), "")


def regression_checks(ok):
    """Guards and helpers on synthetic inputs only."""
    class _Proc:
        def __init__(self, rc, out="", err=""):
            self.returncode, self.stdout, self.stderr = rc, out, err
    ok("guard: failed git command raises", _raises(lambda: git("status", runner=lambda *a, **k: _Proc(128, "", "fatal"))), "")
    ok("guard: empty or non-hex HEAD rejected", _raises(lambda: head_commit(lambda *a: "")) and
       _raises(lambda: head_commit(lambda *a: "HEAD")), "")
    ok("guard: git failure refuses to start", not _quiet(lambda: guard_start(lambda *a: (_ for _ in ()).throw(TechnicalError("x")))), "")
    ok("guard: dirty tree refuses to start", not _quiet(lambda: guard_start(lambda *a: " M x")), "")
    ok("guard: non-finite rejected", _raises(lambda: require_finite("x", [1.0, np.nan])) and
       _raises(lambda: require_finite("x", [np.inf])), "")
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "m.json"
        r = write_meta(p, dict(outcome="eseguita", x=float("nan")))
        m = json.loads(p.read_text())
        ok("guard: META with NaN written, outcome becomes non riuscito", (not r) and m["outcome"].startswith("non riuscito"), "")
        d = Path(tmp) / "o"
        d.mkdir()
        ok("guard: existing output directory never overwritten", _raises(lambda: d.mkdir(exist_ok=False), FileExistsError), "")
    # A1 §1 classification on hand-made pairs
    tb = tau_beta("L1")
    se = 1e-26

    def o(beta, se_, v=None):
        lo, hi = beta - Z * se_, beta + Z * se_
        return dict(state="ok", beta=beta, se=se_, lo=lo, hi=hi, verdict=v or verdict_interval(lo, hi))
    ok("A1: identical O responses -> no boundary case", classify_o_pair(o(-3e-26, se), o(-3e-26, se), tb) is None, "")
    edge = -Z * se                                  # hi = 0 exactly at beta = -Z se
    bL, bS = o(edge - 1e-39, se), o(edge + 1e-39, se)
    c = classify_o_pair(bL, bS, tb) if bL["verdict"] != bS["verdict"] else "same"
    ok("A1: verdicts differ with hi within tau_v of zero -> boundary case recorded", isinstance(c, dict), str(c)[:80])
    ok("A1: verdicts differ far from zero -> technical error",
       _raises(lambda: classify_o_pair(o(-3e-26, se, "supportato"), o(-3e-26, se, "non deciso"), tb)), "")
    ok("A1: supportato vs opposto -> technical error",
       _raises(lambda: classify_o_pair(o(0.0, se, "supportato"), o(0.0, se, "opposto"), tb)), "")
    ok("A1: beta beyond tau_beta -> technical error", _raises(lambda: classify_o_pair(o(-3e-26, se), o(-3e-26 + 3 * tb, se), tb)), "")
    ok("A1: SE beyond 1e-12 rel -> technical error", _raises(lambda: classify_o_pair(o(-3e-26, se), o(-3e-26, se * (1 + 1e-11)), tb)), "")
    res = {s: {"M": dict(beta_wls=1e-26 + DBETA[s])} for s in SIGNALS}
    for s in SIGNALS:
        res[s]["O"] = o(res[s]["M"]["beta_wls"], se)
    res2 = {s: dict(v) for s, v in res.items()}
    res2["S1"] = dict(res["S1"], M=dict(beta_wls=res["S1"]["M"]["beta_wls"] + 5 * tb))
    ok("A1: unit identities pass on consistent input, fail on a 5 tau_beta shift",
       unit_identities(res)[0] == [] and _raises(lambda: unit_identities(res2)), "")
    # worker records any exception as technical
    global _ST
    saved = _ST
    _ST = None
    r = work((0, 0, 1, 1))
    _ST = saved
    ok("work: an exception inside the unit is recorded as technical (type, message, traceback)",
       r["tech"] is not None and r["rows"] == [] and r["tech"]["traceback"], r["tech"]["exception_type"] if r["tech"] else "")
    # duration formula
    ok("duration: T_hat = (1000/12) * sum of 9 tbar; 9 x 1 s -> 750 s; wrong length rejected",
       predicted_duration_s([1.0] * 9) == 750.0 and _raises(lambda: predicted_duration_s([1.0] * 8)), "")
    # summaries on a hand-made raw
    raw = []
    for k in range(4):
        for sig, vL in (("L1", "supportato" if k < 2 else "non deciso"), ("S1", "supportato" if k in (1, 2) else "non deciso")):
            for m in METHODS:
                raw.append(dict(n=0, form="ar1_05", x_scale=0.5, k=k, signal=sig, method=m, target=DBETA[sig],
                                beta_wls=1e-26 * k, beta=1e-26 * k, se=1e-26, state="ok", verdict=vL,
                                covered=1, below=0, above=0, beta_g_minus_wls=0.0))
    raw = pd.DataFrame(raw)
    pl = paired_ls(raw)
    r0 = pl[(pl["method"] == "M")].iloc[0]
    ref_se = math.sqrt((1 + 1 - 0 / 4) / (4 * 3))
    sm = summarize(raw)
    s0 = sm[(sm["signal"] == "L1") & (sm["method"] == "M")].iloc[0]
    ok("summaries: hand counts (2/4 supportato), paired b = c = 1, delta 0, se sqrt(2/12)",
       s0["n_supportato"] == 2 and s0["N"] == 4 and r0["b_only_L"] == 1 and r0["c_only_S"] == 1
       and r0["delta"] == 0 and abs(r0["se_paired"] - ref_se) < 1e-15, f"se {r0['se_paired']:.6f}")


def _raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return True
    return False


def _quiet(fn):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn()


def selftest():
    if not guard_start():
        return 2
    commit = head_commit()
    out = prelim_dir("SELFTEST", commit)
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(mode="selftest", plan_points="§6 points 1-5, A1 §1", outcome="non riuscito")
    res = []

    def ok(name, cond, value=""):
        res.append(dict(check=name, passed=bool(cond), value=value))
        print(("PASS " if cond else "FAIL ") + name + (f"  [{value}]" if value else ""), flush=True)
    code = 1
    t0 = time.time()
    try:
        meta.update(provenance())
        design, dinfo = load_design()
        meta.update(dinfo)
        st = Statics(design)
        selftest_checks(st, ok)
        regression_checks(ok)
        n_ok = sum(r["passed"] for r in res)
        meta.update(n_checks=len(res), n_passed=n_ok, passed=n_ok == len(res))
        meta["outcome"] = "superato" if n_ok == len(res) else "non superato"
        code = 0 if n_ok == len(res) else 1
        print(f"{n_ok}/{len(res)} passed")
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        print(traceback.format_exc())
        code = 1
    finally:
        meta["duration_s"] = time.time() - t0
        pd.DataFrame(res, columns=["check", "passed", "value"]).to_csv(out / "SELFTEST.csv", index=False)
        if not write_meta(out / "SELFTEST_META.json", meta):
            code = 1
        print(f"receipt: {out.relative_to(ROOT)}")
    return code


# ---------------------------------------------------------------- gate (plan §6 point 6)

def gate():
    if not guard_start():
        return 2
    commit = head_commit()
    out = prelim_dir("GATE", commit)
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(mode="gate", plan_points="§6 point 6 (compatibility, not validation)", outcome="non riuscito")
    rows, code, t0 = [], 1, time.time()
    try:
        meta.update(provenance())
        if sha(VALIDATION_RAW) != SHA_VALIDATION_RAW:
            raise TechnicalError("VALIDATION_RAW.csv.gz SHA-256 differs")
        meta["sha256_VALIDATION_RAW"] = SHA_VALIDATION_RAW
        design, dinfo = load_design()
        meta.update(dinfo)
        st = Statics(design)
        vr = pd.read_csv(VALIDATION_RAW, float_precision="round_trip", keep_default_na=False, na_values=["", "nan", "NaN"],
                         low_memory=False, usecols=["test", "kind", "scenario", "effect", "k", "beta", "se", "verdict"])
        vr = vr[vr["test"] == "T5"]
        cases = ([("effect", 2, -0.1, k, 4, V.seed_effect(2, -0.1, k)) for k in range(20)]
                 + [("null", 7, 0.0, k, 7, V.seed_null(7, k)) for k in range(20)])
        for kind, s, e, k, n, seed in cases:
            ref = vr[(vr["kind"] == kind) & (vr["scenario"] == s) & (vr["effect"] == e) & (vr["k"] == k)]
            if len(ref) != 1:
                raise TechnicalError(f"VALIDATION_RAW: {len(ref)} rows for {kind} {s} {e} {k}")
            ref = ref.iloc[0]
            base = noise_catalogue(design, n, seed)
            u, _ = build_units(st, base, st.linear(e) if e != 0.0 else st.add["N"])
            row = dict(kind=kind, scenario=s, effect=e, k=k, config=n, seed=seed, beta_ref=ref["beta"], se_ref=ref["se"],
                       verdict_ref=ref["verdict"])
            try:
                r = method_m(u)
                rb = abs(r["beta"] - ref["beta"]) / abs(ref["beta"])
                rs = abs(r["se"] - ref["se"]) / ref["se"]
                row.update(beta=r["beta"], se=r["se"], verdict=r["verdict"], rel_beta=rb, rel_se=rs,
                           passed=bool(rb <= GATE_RTOL and rs <= GATE_RTOL and r["verdict"] == ref["verdict"]))
            except ExpectedError as exc:
                row.update(verdict="errore", error=str(exc), passed=ref["verdict"] == "errore")
            rows.append(row)
            print(f"{kind} s{s} e{e} k{k}: rel beta {row.get('rel_beta', np.nan):.2e} rel se {row.get('rel_se', np.nan):.2e} "
                  f"{'PASS' if row['passed'] else 'FAIL'}", flush=True)
        g = pd.DataFrame(rows)
        meta.update(n_catalogues=len(g), n_passed=int(g["passed"].sum()), max_rel_beta=float(g["rel_beta"].max()),
                    max_rel_se=float(g["rel_se"].max()), tolerance_rel=GATE_RTOL)
        meta["outcome"] = "superata" if g["passed"].all() else "non superata"
        code = 0 if g["passed"].all() else 1
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        print(traceback.format_exc())
        code = 1
    finally:
        meta["duration_s"] = time.time() - t0
        pd.DataFrame(rows).to_csv(out / "GATE.csv", index=False)
        if not write_meta(out / "GATE_META.json", meta):
            code = 1
        print(json.dumps({k: meta.get(k) for k in ("outcome", "n_passed", "n_catalogues", "max_rel_beta", "max_rel_se")}))
        print(f"receipt: {out.relative_to(ROOT)}")
    return code


# ---------------------------------------------------------------- pool execution (benchmark and run)

def run_pool(design, tasks, progress_every=0, log=print):
    results = []
    t0 = time.perf_counter()
    with Pool(N_PROC, initializer=_init, initargs=(design,)) as pool:
        for i, r in enumerate(pool.imap_unordered(work, tasks, chunksize=1), 1):
            results.append(r)
            if progress_every and i % progress_every == 0:
                log(f"{i}/{len(tasks)} units, {time.perf_counter() - t0:.0f} s, technical {sum(x['tech'] is not None for x in results)}")
    return results, time.perf_counter() - t0


def events_frames(results):
    tech = pd.DataFrame([r["tech"] for r in results if r["tech"] is not None])
    bounds = pd.DataFrame([b for r in results for b in r["bounds"]])
    diag = pd.DataFrame([dict(n=r["n"], k=r["k"], **r["diag"]) for r in results if r["diag"]])
    return tech, bounds, diag


def benchmark():
    if not guard_start():
        return 2
    commit = head_commit()
    out = prelim_dir("BENCHMARK", commit)
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(mode="benchmark", plan_points="§3e, §6.7, A1 §2", outcome="non riuscito",
                formula="T_hat = (1000/12) * sum_{n=0}^{8} tbar_n; unit = 1 base catalogue x 5 signals x 4 methods",
                n_proc=N_PROC, stop_hours=T_MAX_H)
    code, t0 = 1, time.time()
    try:
        meta.update(provenance())
        check_inputs()
        design, dinfo = load_design()
        meta.update(dinfo)
        Statics(design)                              # fail early in the parent
        # same task distribution as the run: replica outer, configuration inner
        tasks = [(n, r, seed_bench(n, r), seed_bench_boot(n, r)) for r in range(4) for n in range(9)]
        results, wall = run_pool(design, tasks)
        units = pd.DataFrame([{k: r[k] for k in ("n", "k", "seed_base", "seed_boot", "wall_s", "cpu_s", "pid")}
                              | dict(technical=r["tech"] is not None,
                                     n_expected_errors=sum(x["state"] == "errore previsto" for x in r["rows"]),
                                     n_boundary=len(r["bounds"])) for r in results]).rename(columns={"k": "r"})
        units = units.sort_values(["n", "r"]).reset_index(drop=True)
        units.to_csv(out / "BENCHMARK_UNITS.csv", index=False)
        cfg = units.groupby("n").agg(n_units=("wall_s", "size"), tbar_s=("wall_s", "mean"), tmin_s=("wall_s", "min"),
                                     tmax_s=("wall_s", "max"), cpu_mean_s=("cpu_s", "mean")).reset_index()
        cfg.insert(1, "form", [NOISE[n][0] for n in cfg["n"]])
        cfg.insert(2, "x_scale", [NOISE[n][2] for n in cfg["n"]])
        cfg.to_csv(out / "BENCHMARK_CONFIG.csv", index=False)
        # errors (expected, with reasons) and boundary cases kept as computed; verdicts not written
        errs = pd.DataFrame([dict(n=x["n"], r=x["k"], signal=x["signal"], method=x["method"], state=x["state"],
                                  reason=x["reason"]) for r in results for x in r["rows"] if x["state"] != "ok"])
        errs.to_csv(out / "BENCHMARK_EXPECTED_ERRORS.csv", index=False)
        tech, bounds, diag = events_frames(results)
        tech.to_csv(out / "BENCHMARK_TECHNICAL_ERRORS.csv", index=False)
        bounds.to_csv(out / "BENCHMARK_BOUNDARY_CASES.csv", index=False)
        diag.to_csv(out / "BENCHMARK_IDENTITY_DIAGNOSTICS.csv", index=False)
        n_tech = int(units["technical"].sum())
        meta.update(n_units=len(units), wall_benchmark_s=wall, n_technical=n_tech, n_expected_errors=len(errs),
                    n_boundary_cases=len(bounds), tbar_s={int(n): float(t) for n, t in zip(cfg["n"], cfg["tbar_s"])})
        if n_tech or len(cfg) != 9 or (cfg["n_units"] != 4).any():
            meta["outcome"] = "non riuscito: errori tecnici o unità mancanti"
            code = 1
        else:
            T = predicted_duration_s(cfg.sort_values("n")["tbar_s"].to_numpy())
            meta.update(T_hat_s=T, T_hat_h=T / 3600.0, within_limit=bool(T / 3600.0 <= T_MAX_H))
            meta["outcome"] = "eseguito: entro il limite" if T / 3600.0 <= T_MAX_H else "eseguito: oltre il limite, arresto"
            code = 0
            print(cfg.to_string(index=False))
            print(f"T_hat = (1000/12) * {cfg['tbar_s'].sum():.3f} s = {T:.0f} s = {T / 3600:.2f} h (limit {T_MAX_H} h)")
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        print(traceback.format_exc())
        code = 1
    finally:
        meta["duration_s"] = time.time() - t0
        if not write_meta(out / "BENCHMARK_META.json", meta):
            code = 1
        print(json.dumps({k: meta.get(k) for k in ("outcome", "n_technical", "n_expected_errors", "n_boundary_cases",
                                                   "wall_benchmark_s", "T_hat_h")}))
        print(f"receipt: {out.relative_to(ROOT)}")
    return code


def prelim_receipts(script_sha):
    """Selftest, gate and benchmark receipts for this script SHA-256, all positive."""
    found = {}
    for mode, f, good in (("SELFTEST", "SELFTEST_META.json", lambda m: m.get("outcome") == "superato"),
                          ("GATE", "GATE_META.json", lambda m: m.get("outcome") == "superata"),
                          ("BENCHMARK", "BENCHMARK_META.json", lambda m: m.get("within_limit") is True)):
        for p in sorted(PRELIM.glob(f"{mode}_*/{f}")):
            m = json.loads(p.read_text())
            if m.get("sha256_script") == script_sha and m.get("git_dirty") == 0 and good(m):
                found[mode] = str(p.relative_to(ROOT))
    return found


def run():
    if not guard_start():
        return 2
    rec = prelim_receipts(sha(__file__))
    if set(rec) != {"SELFTEST", "GATE", "BENCHMARK"}:
        print(f"preliminary receipts missing for this script: {sorted(set(['SELFTEST', 'GATE', 'BENCHMARK']) - set(rec))}")
        return 2
    OUT.mkdir(parents=True, exist_ok=False)          # never overwrite an attempt
    meta = dict(mode="run", outcome="non riuscito", receipts=rec, n_rep=N_REP, n_proc=N_PROC)
    code, t0 = 1, time.time()
    log = lambda s: print(time.strftime("%H:%M:%S ") + s, flush=True)  # noqa: E731
    try:
        meta.update(provenance())
        check_inputs()
        design, dinfo = load_design()
        meta.update(dinfo)
        Statics(design)
        tasks = [(n, k, seed_base(n, k), seed_boot(n, k)) for k in range(N_REP) for n in range(9)]
        meta["seeds"] = dict(base="31000000 + 100000 n + k", boot="32000000 + 100000 n + k", n="0..8", k="0..999")
        results, wall = run_pool(design, tasks, progress_every=200, log=log)
        raw = pd.DataFrame([x for r in results for x in r["rows"]])
        tech, bounds, diag = events_frames(results)
        raw.sort_values(["n", "k", "signal", "method"]).to_csv(OUT / "RAW.csv.gz", index=False)
        tech.to_csv(OUT / "TECHNICAL_ERRORS.csv", index=False)
        bounds.to_csv(OUT / "BOUNDARY_CASES.csv", index=False)
        diag.to_csv(OUT / "IDENTITY_DIAGNOSTICS.csv", index=False)
        pd.DataFrame([{k: r[k] for k in ("n", "k", "wall_s", "cpu_s", "pid")} for r in results]).to_csv(
            OUT / "UNIT_TIMES.csv", index=False)
        meta.update(n_units=len(results), n_rows=len(raw), n_technical=len(tech), n_boundary_cases=len(bounds),
                    wall_run_s=wall)
        if len(tech) or len(raw) != 9 * N_REP * 20:
            meta["outcome"] = "non riuscito: errori tecnici o righe mancanti (nessuna lettura dei risultati)"
            code = 1
        else:
            summ = summarize(raw)
            summ.to_csv(OUT / "SUMMARY.csv", index=False)
            paired_ls(raw).to_csv(OUT / "PAIRED_LS.csv", index=False)
            meta["sha256_SUMMARY"] = sha(OUT / "SUMMARY.csv")
            meta["outcome"] = "eseguita"
            code = 0
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        log(traceback.format_exc())
        code = 1
    finally:
        meta["duration_s"] = time.time() - t0
        if not write_meta(OUT / "META.json", meta):
            code = 1
        log(json.dumps({k: meta.get(k) for k in ("outcome", "n_units", "n_rows", "n_technical", "n_boundary_cases",
                                                 "exception_type", "exception")}))
        log("fatto")
    return code


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--gate", action="store_true")
    g.add_argument("--benchmark", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else gate() if a.gate else benchmark() if a.benchmark else run())
