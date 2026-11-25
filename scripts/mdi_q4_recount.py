"""Independent recount of the Q4 prospective run (frozen note docs/MDI_PILOT_Q4_NOTE.md, amendment A2).

Rebuilds every product of results/MDI_Q4_PROSPECTIVE with own code and compares it in full. It does not import
scripts/mdi_q4_prospective.py (only the selftest uses it, to produce synthetic outputs to recount).
Own code: Meeus rotation start and CR(t), cycle and years, SILSO monthly normalisation, filters and cell counts, MS cell
counts, MF units, pools and Kish, missing years, L1 donors and L-NN, seeded uniforms, Beta yields, inclusion, fluxes,
design columns and incremental rank, WLS row by QR (not p2d.wls_row), cell activity, ramp targets (E0 and design
quantiles), temporal covariances (AR(1) and 20-CR steps written here), variance, offsets, normal frequencies,
tolerances, product-difference shift, failure expansion, SUMMARY, NOT_COMPUTABLE, CRITERIA, DESIGNS, YIELD_EFFECTS,
MF_POOLS.
Declared dependencies (inputs, not the computation under check): the HMI E0 records through
prospective_phase_a.load_inputs/e0_records (reproduced against phase A by the run's proof §6.1); the pilot rotation rule
(mdi_synoptic_adapter.group_rotation) and the required-map rule of the preparatory counts (mdi_q4_prep_counts), whose
counts the recount checks against the preserved preparatory META.
Tolerances: strings, statuses, counts and flags exact; floats relative 1e-8 (plus 1e-12 of the column scale).
The receipt is complete (partial false) only on the real path; injected data gives partial true and writes nothing.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_q4_recount.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_q4_recount.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import solve_triangular
from scipy.stats import beta as beta_dist, norm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/MDI_Q4_PROSPECTIVE"
REC = ROOT / "results/MDI_Q4_PROSPECTIVE_RECOUNT"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
L1F = ROOT / "results/MDI_PILOT_L1/L1_RECORDS.csv"
L2F = ROOT / "results/MDI_PILOT_L2/L2_RECORDS.csv"
AUDIT = ROOT / "results/MDI_SYNOPTIC_AUDIT/FILES.csv"
AN2 = ROOT / "results/MDI_PILOT_ANALYSIS_L2"
PHASE_A_RAW = ROOT / "results/PROSPECTIVE_PHASE_A/RAW.csv.gz"
PREP_META = ROOT / "results/MDI_Q4_PREP_COUNTS/META.json"
SILSO = ROOT / "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv"
NOTE_FREEZE = ROOT / "docs/MDI_PILOT_Q4_NOTE_FREEZE.json"
SCRIPT_REL = "scripts/mdi_q4_prospective.py"
EXPECTED = dict(script="033b233bebfa63acfa6743b53ca4e0b9d27548301bb6e45824257514d0667bb6",
                head="1c25c2e87ec5d045877e345799909f73b4183a5a",
                note="e13a3a72875e15bed296414cfcf9423b7f4d032c3d3a8efaeb67e9ad7882ade9",
                a2="c834077011ff7e201d01eabc318de7e6fbfc547bbffcfca05a0091e87636203e",
                note_receipt="0f9b3acc01e6a58a182685259350f71a8caf82edc2381c209f210d89b5b2410d",
                a2_receipt="76a26f061ab99c659f312d84a599a9b3e540b77b321529bd2c99ae83b5a23326")
CHOICES_SHA = "5b352e8cb4cc04177bda83c3f8b2f08087b4ec082fa7118c5a01969f1cf15fc1"
META_KEYS = {"script_sha256", "git_head", "note_sha256", "a2_sha256", "note_freeze_sha256", "a2_freeze_sha256", "seed0", "n_realisations",
             "z", "units", "mf_missing_years", "noise", "filters", "runtime_s", "python", "numpy", "pandas", "omp", "receipts_problems",
             "implementation_choices"}
PRODUCTS = {"RAW.csv.gz", "SUMMARY.csv", "NOT_COMPUTABLE.csv", "CRITERIA.csv", "DESIGNS.csv", "YIELD_EFFECTS.csv",
            "CELL_COUNTS.csv", "MF_POOLS.csv", "PROOFS.csv", "META.json", "RUN.log", "RUN.exit"}

NOTE_REL, A2_REL = "docs/MDI_PILOT_Q4_NOTE.md", "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md"
A2_FREEZE_REL, PARENT_REL, RULES_REL = ("docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_FREEZE.json", "docs/PROTOCOL_MDI_TILT_PILOT.md",
                                        "docs/MDI_Q4_PREP_COUNTS_RULES.md")
PIN_PARENT = "77367350e8f9a5f71933afdcc791429b307c95ec1875224c1f2d7486950d086f"
PIN_RULES = "9ce409fc1030e5d41ffac1d994887d8b540ccc711f25b488426e9c387ad8a77a"
CODE9 = frozenset({"scripts/prospective_phase_a.py", "scripts/t5_proxy_sensitivity.py", "python/sharpbl/diag_t5_oracle.py",
                   "python/sharpbl/p2d.py", "python/sharpbl/run_p2.py", "python/sharpbl/p2f_validation.py", "python/sharpbl/p2f_pilot.py",
                   "scripts/mdi_synoptic_adapter.py", "scripts/mdi_q4_prep_counts.py"})
INPUTS17 = frozenset({
    "results/MDI_PILOT_SELECTION/POPULATION.csv", "results/MDI_PILOT_SELECTION/SAMPLE.csv", "results/MDI_PILOT_SELECTION/CELLS.csv",
    "results/MDI_PILOT_SELECTION/META.json", "results/MDI_PILOT_L1/L1_RECORDS.csv", "results/MDI_PILOT_L2/L2_RECORDS.csv",
    "results/MDI_SYNOPTIC_AUDIT/FILES.csv", "results/MDI_PILOT_ANALYSIS_L1/Q1_YIELD_PROJECTED.csv",
    "results/MDI_PILOT_ANALYSIS_L2/YIELD_A1.csv", "results/MDI_PILOT_ANALYSIS_L2/Q2_PAIRS_A1_main.csv",
    "results/MDI_PILOT_ANALYSIS_L2/Q2_PAIRS_A1_sens100.csv", "results/MDI_PILOT_ANALYSIS_L2/Q2_SUMMARY_A1_main.csv",
    "results/MDI_PILOT_ANALYSIS_L2/Q2_SUMMARY_A1_sens100.csv", "results/PROSPECTIVE_PHASE_A/RAW.csv.gz",
    "results/P1/P1_SBL_CATALOG_BY_HARP.csv", "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv", "results/MDI_Q4_PREP_COUNTS/META.json"})
GATE_ROOT = ROOT                         # the selftest points it to a fixture to prove the stop


def provenance(nf, af, nf_sha, af_sha, root=None):
    """Names of the failed provenance checks of the files the recount reads or imports now ([] = all matched)."""
    root = Path(GATE_ROOT if root is None else root)
    probs = []

    def need(name, f):
        try:
            good = bool(f())
        except (OSError, KeyError, TypeError, ValueError):
            good = False
        if not good:
            probs.append(name)

    def files(d, expected):
        return isinstance(d, dict) and set(d) == set(expected) and all(sha(root / p) == h for p, h in d.items())

    need("note receipt pinned", lambda: nf_sha == EXPECTED["note_receipt"])
    need("A2 receipt pinned", lambda: af_sha == EXPECTED["a2_receipt"])
    need("note text", lambda: sha(root / NOTE_REL) == nf["sha256"] == EXPECTED["note"])
    need("A2 text and A2 receipt named by the note", lambda: sha(root / A2_REL) == af["sha256"] == nf["amendment_A2_sha256"] == EXPECTED["a2"]
         and nf["amendment_A2_receipt_sha256"] == af_sha)
    need("parent protocol", lambda: sha(root / PARENT_REL) == nf["parent_sha256"] == af["parent_sha256"] == PIN_PARENT)
    need("preparatory-count rules and META", lambda: sha(root / RULES_REL) == nf["prep_counts_rules_sha256"] == af["prep_counts_rules_sha256"]
         == PIN_RULES and af["prep_counts_meta_sha256"] == sha(root / "results/MDI_Q4_PREP_COUNTS/META.json"))
    need("reused code (9): exact set and current hashes", lambda: files(nf["reused_code_sha256"], CODE9))
    need("inputs (17): exact set and current hashes", lambda: files(nf["inputs_sha256"], INPUTS17))
    return probs


# ---- frozen constants of the note, written here (checked against the receipt and the phase A RAW where possible)
SEED0, N_REAL, N_COMP = 35_200_000, 20, 5
GAMMA0, SDX, TILT = 24.0, 7.5, 2.107
Z = float(norm.ppf(1 - 0.0125))
SIG_INT, SIG_M = (15.0, 25.0, 30.0), (0.0, 2.0, 10.0)
REF_SIG = ((15.0, 2.0), (30.0, 10.0))
NOISE = [(f, s, x) for f, s in (("ar1_05", 1), ("ar1_09", 2), ("steps20", 7), ("ar1_09_km08", 3), ("ar1_05_kp06", 4))
         for x in (0.5, 1.0, 2.0)]
AR1 = {1: (0.5, 0.0), 2: (0.9, 0.0), 3: (0.9, -0.8), 4: (0.5, 0.6)}
MAIN3 = ((1, 1.0), (2, 1.0), (7, 1.0))
FULL_N = list(range(15))
SENS_N = [i for i, (_, s, x) in enumerate(NOISE) if (s, x) in MAIN3]
FULL_S = [(a, b) for a in SIG_INT for b in SIG_M]
C_LIM = (0.25, 0.5)
TAGS = ("020", "010", "qd_020", "qd_010")
THR = ("main", "sens100")
CELL_KEYS = ["act_class", "hemisphere", "area_class", "cohort"]
POOLS = ([("cohort", (c,)) for c in ("M1", "U")] + [("cohort_act", (c, a)) for c in ("M1", "U") for a in (1, 2, 3)]
         + [("cohort_area", (c, a)) for c in ("M1", "U") for a in (1, 2, 3)])
POOL_J = {"cohort": [0, 1], "cohort_act": list(range(2, 8)), "cohort_area": list(range(8, 14))}
VARIANTS = {"ref": ("MS", "MF"), "mf_pool_cohort_act": ("MF",), "mf_pool_cohort_area": ("MF",), "avail_0.8": ("MF",),
            "avail_0.6": ("MF",), "flux_nolat": ("MS", "MF"), "flux_mf_rho": ("MF",), "act_amain": ("MS", "MF")}
END, CR_H = pd.Timestamp("2010-04-30"), 2096
GAP = (pd.Timestamp("1998-06-01"), pd.Timestamp("1998-11-01"))
M_MIN = {22: pd.Timestamp("1985-08-01"), 23: pd.Timestamp("1996-08-01"), 24: pd.Timestamp("2008-12-01"),
         25: pd.Timestamp("2019-12-01")}
T_REF = pd.Timestamp("2010-05-01")
KEYC = ["design", "threshold", "variant", "model", "sigma_int", "sigma_m", "noise", "form", "scen", "x_scale"]
ROWKEY = ["design", "threshold", "variant", "r", "model", "sigma_int", "sigma_m", "noise"]
NA_SEP = "nessuna classificazione (realizzazioni non calcolabili)"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, m)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- own calendar and activity

def cr_start(c):
    c = np.asarray(c, float)
    m = np.radians(281.96 + 26.882476 * c)
    jde = 2398140.2270 + 27.2752316 * c + 0.1454 * np.sin(m) - 0.0085 * np.sin(2 * m) - 0.0141 * np.cos(2 * m)
    return pd.to_datetime(jde - 2440587.5, unit="D")


def cr_of(ts):
    ts = pd.Timestamp(ts)
    c = int((ts - pd.Timestamp("1853-11-09")).days // 27.2753) + 1
    cand = np.arange(c - 4, c + 5)
    return int(cand[np.asarray(cr_start(cand) <= ts)].max())


def cycle(ts):
    ts = pd.Timestamp(ts)
    return max([k for k, m in M_MIN.items() if m <= ts], default=22)


def years(ts):
    return (pd.Timestamp(ts) - T_REF).days / 365.25


def silso_monthly():
    s = pd.read_csv(SILSO, sep=";", header=None, skipinitialspace=True)
    s = pd.DataFrame({"ym": [f"{int(y)}-{int(m):02d}" for y, m in zip(s[0], s[1])], "N": s[4].astype(float), "S": s[5].astype(float)})
    s = s.set_index("ym").replace(-1.0, np.nan)
    return s / s.loc["2010-05":"2026-09"].mean()


def uni(r, k, n):
    return np.random.default_rng(SEED0 + 1000 * k + r).random(n)


# ---------------------------------------------------------------- own inputs

def assemble(pop, samp, cells, l1, l2, q2p, q2s, missing_maps, H, rot):
    """rot(t_dpd, lon, lcm) -> (N, ct_g, N_eph); req(ct_g) -> required maps (declared dependency)."""
    rotate, required = rot
    mon = silso_monthly()
    P = pop.copy().reset_index(drop=True)
    P["t"] = pd.to_datetime(P.t_dpd)
    ck = {tuple(v): i for i, v in enumerate(cells[CELL_KEYS].itertuples(index=False, name=None))}
    P["cell"] = [ck[tuple(v)] for v in P[CELL_KEYS].itertuples(index=False, name=None)]
    rr = [rotate(a, b, c) for a, b, c in zip(P.t_dpd, P.lon, P.lcm)]
    P["N_amb"] = [x[0] != x[2] for x in rr]
    mm = set(missing_maps)
    P["map_missing"] = [bool(set(required(x[1])) & mm) for x in rr]
    P["CR"] = [cr_of(t) for t in P.t]
    starts = cr_start(P.CR.to_numpy())
    P["cyc"] = [cycle(s) for s in starts]
    P["ty"] = [years(s) for s in starts]
    P["sinlat"] = np.sin(np.radians(np.abs(P.lat.astype(float))))
    P["A_silso"] = [mon.at[m, h] if m in mon.index else np.nan for m, h in zip(P.t.dt.strftime("%Y-%m"), P.hemisphere)]
    P["year"] = P.t.dt.year
    P["f1"] = P.t.dt.normalize() <= END
    P["f2"] = P.CR < CR_H
    P["gap"] = (P.t >= GAP[0]) & (P.t < GAP[1])
    P["MS"] = P.f1 & P.f2 & ~P.map_missing & ~P.N_amb
    P["MF"] = P.f1 & P.f2 & ~P.gap
    X = dict(P=P, cells=cells, H=H.reset_index(drop=True), q2p=q2p, missing_maps=sorted(mm))
    pm = {(a, b): (c, d) for a, b, c, d in zip(P.noaa, P.day, P.cell, P.map_missing)}
    pl = {(a, b): (la, ar) for a, b, la, ar in zip(P.noaa, P.day, P.lat, P.area)}
    st1 = {(a, b): (s, s1) for a, b, s, s1 in zip(l1.noaa, l1.day, l1.status, l1.sens100_status)}
    rows = []
    for s in samp.to_dict("records"):
        k = (s["noaa"], s["day"])
        c, mmiss = pm[k]
        rows.append(dict(noaa=k[0], day=k[1], cell=c, mm=mmiss, ok_main=st1[k][0] == "ok", ok_sens100=st1[k][1] == "ok",
                         lat=pl[k][0], area=pl[k][1]))
    U = pd.DataFrame(rows)
    X["ms_all"], X["ms"] = {}, {}
    for th in THR:
        n = np.zeros(36)
        r = np.zeros(36)
        n0 = np.zeros(36)
        r0 = np.zeros(36)
        for x in U.itertuples():
            n0[x.cell] += 1
            r0[x.cell] += getattr(x, f"ok_{th}")
            if not x.mm:
                n[x.cell] += 1
                r[x.cell] += getattr(x, f"ok_{th}")
        X["ms_all"][th], X["ms"][th] = (n0, r0), (n, r)
    X["ms_removed"] = int(U.mm.sum())
    a = l2[(l2.rule == "A1") & (l2.image == "A")]
    sa = {(x, y): (s, s1) for x, y, s, s1 in zip(a.noaa, a.day, a.status, a.sens100_status)}
    cN = {tuple(v[:4]): (v[4], v[5]) for v in cells[CELL_KEYS + ["N", "n2"]].itertuples(index=False, name=None)}
    mf = []
    for s in samp[samp.level2.astype(bool)].to_dict("records"):
        Nn, n2 = cN[(s["act_class"], s["hemisphere"], s["area_class"], s["cohort"])]
        t = pd.Timestamp(s["t_dpd"])
        st, st1_ = sa[(s["noaa"], s["day"])]
        mf.append(dict(noaa=s["noaa"], day=s["day"], cohort=s["cohort"], act_class=s["act_class"], area_class=s["area_class"],
                       w=Nn / n2, gap=GAP[0] <= t < GAP[1], ok_main=st == "ok", ok_sens100=st1_ == "ok", year=t.year))
    MFU = pd.DataFrame(mf)
    X["mf_all"], X["mf"] = MFU, MFU[~MFU.gap].reset_index(drop=True)
    X["pools"] = {th: own_pools(X["mf"], f"ok_{th}") for th in THR}
    yrs = P[P.MF].year
    X["missing_years"] = sorted(set(range(int(yrs.min()), int(yrs.max()) + 1)) - set(MFU.year))
    X["donors"], X["nn"] = {}, {}
    fx = {(a, b): v for a, b, *v in l1[["noaa", "day", "main_flux_pos_mx", "main_flux_neg_mx", "sens100_flux_pos_mx",
                                            "sens100_flux_neg_mx"]].itertuples(index=False, name=None)}
    for th in THR:
        d = U[U[f"ok_{th}"]].sort_values(["noaa", "day"])
        j = 0 if th == "main" else 2
        rho = [(abs(fx[(a, b)][j]) + abs(fx[(a, b)][j + 1])) / float(ar) for a, b, ar in zip(d.noaa, d.day, d.area)]
        D = pd.DataFrame(dict(cell=d.cell.to_numpy(), alat=np.abs(d.lat.to_numpy(float)), rho=rho))
        X["donors"][th] = D
        X["nn"][th] = own_nn(P, D)
    X["dg"] = {th: tuple(float(q2s[th].set_index("group").at[f"activity {k}", "median_d_gamma"]) for k in (1, 2, 3)) for th in THR}
    return X


def own_pools(u, col):
    out = []
    for kind, key in POOLS:
        m = u.cohort == key[0]
        if kind == "cohort_act":
            m = m & (u.act_class == key[1])
        if kind == "cohort_area":
            m = m & (u.area_class == key[1])
        g = u[m]
        w = g.w.to_numpy(float)
        o = g[col].to_numpy(float)
        if not len(g):
            out.append(dict(pool=kind, key="|".join(map(str, key)), n=0, ok=0, p_hat=np.nan, n_eff=0.0, r_eff=np.nan))
            continue
        p = (w * o).sum() / w.sum()
        ne = w.sum() ** 2 / (w * w).sum()
        out.append(dict(pool=kind, key="|".join(map(str, key)), n=len(g), ok=int(o.sum()), p_hat=p, n_eff=ne, r_eff=p * ne))
    return pd.DataFrame(out)


def own_nn(P, D):
    nn = -np.ones((len(P), 5), int)
    dist = np.full(len(P), np.nan)
    lists = {}
    cells = P.cell.to_numpy()
    alat = np.abs(P.lat.to_numpy(float))
    for c in range(36):
        ix = np.flatnonzero(D.cell.to_numpy() == c)
        lists[c] = ix
        if len(ix) < 5:
            continue
        for g in np.flatnonzero(cells == c):
            dl = np.abs(D.alat.to_numpy()[ix] - alat[g])
            o = sorted(range(len(ix)), key=lambda q: (dl[q], q))[:5]
            nn[g] = ix[o]
            dist[g] = dl[o].max()
    return nn, dist, lists


def pool_idx(P, kind):
    idx = -np.ones(len(P), int)
    for j in POOL_J[kind]:
        k, key = POOLS[j]
        m = (P.cohort == key[0]).to_numpy()
        if kind == "cohort_act":
            m &= (P.act_class == key[1]).to_numpy()
        if kind == "cohort_area":
            m &= (P.area_class == key[1]).to_numpy()
        idx[m] = j
    return idx


# ---------------------------------------------------------------- own designs

def records(X, design, th, r, variant):
    P = X["P"]
    n = len(P)
    U0, V1, V2, Dg, Rg = uni(r, 0, n), uni(r, 1, 36), uni(r, 2, 14), uni(r, 3, n), uni(r, 4, n)
    dom = P[design].to_numpy()
    info = dict(n_domain=int(dom.sum()))
    if design == "MS":
        nn_, rr_ = X["ms"][th]
        if (nn_ == 0).any():
            return None, dict(info, status="empty_yield_stratum")
        p = beta_dist.ppf(V1, rr_ + 0.5, nn_ - rr_ + 0.5)[P.cell.to_numpy()]
    else:
        kind = {"mf_pool_cohort_act": "cohort_act", "mf_pool_cohort_area": "cohort_area"}.get(variant, "cohort")
        pools, idx, js = X["pools"][th], pool_idx(P, kind), POOL_J[kind]
        if (pools.n.to_numpy()[js] == 0).any() or (idx[dom] < 0).any():
            return None, dict(info, status="empty_yield_stratum")
        pp = np.full(14, np.nan)
        re_, ne_ = pools.r_eff.to_numpy(), pools.n_eff.to_numpy()
        pp[js] = beta_dist.ppf(V2[js], re_[js] + 0.5, ne_[js] - re_[js] + 0.5)
        p = pp[np.maximum(idx, 0)]
        fac = {"avail_0.8": 0.8, "avail_0.6": 0.6}.get(variant)
        if fac is not None:
            p = p * np.where(P.year.isin(X["missing_years"]).to_numpy(), fac, 1.0)
    nn, dist, lists = X["nn"][th]
    rho = X["donors"][th].rho.to_numpy()
    if variant == "flux_nolat":
        ch = -np.ones(n, int)
        for c, ix in lists.items():
            rows = np.flatnonzero(P.cell.to_numpy() == c)
            if len(ix):
                ch[rows] = ix[(len(ix) * Dg[rows]).astype(int)]
    else:
        ch = np.where(nn[:, 0] >= 0, nn[np.arange(n), (5 * Dg).astype(int)], -1)
    phi = P.area.to_numpy(float) * np.where(ch >= 0, rho[np.maximum(ch, 0)], np.nan)
    if variant == "flux_mf_rho" and design == "MF":
        q = X["q2p"][th]
        phi = phi / q[(len(q) * Rg).astype(int)]
    inc = dom & (U0 < p)
    if np.isnan(phi[inc]).any():
        return None, dict(info, status="flux_cell_lt5_donors")
    act = (P.A_main if variant == "act_amain" else P.A_silso).to_numpy(float)
    keep = inc & np.isfinite(act)
    R = pd.DataFrame(dict(CR=P.CR.to_numpy()[keep], hem=P.hemisphere.to_numpy()[keep], sinlat=P.sinlat.to_numpy()[keep], phi=phi[keep],
                          cyc=P.cyc.to_numpy()[keep], A=act[keep], M=1.0, ty=P.ty.to_numpy()[keep], k=P.act_class.to_numpy()[keep]))
    info.update(status="ok", n_included=int(inc.sum()), n_excluded_yield=int(dom.sum() - inc.sum()), n_no_activity=int((inc & ~np.isfinite(act)).sum()),
                expected_yield=float(p[dom].mean()), lat_dist_median=float(np.nanmedian(dist[dom])), lat_dist_p90=float(np.nanquantile(dist[dom], 0.9)))
    return R, info


# ---------------------------------------------------------------- own model

def rank(cols, sw):
    if not cols:
        return 0
    A = np.column_stack(cols) * sw[:, None]
    nr = np.sqrt((A * A).sum(0))
    A = A[:, nr > 0] / nr[nr > 0]
    if not A.shape[1]:
        return 0
    s = np.linalg.svd(A, compute_uv=False)
    return int((s > s.max() * max(A.shape) * np.finfo(float).eps).sum())


def columns(R, model, comb):
    s, M, h, c = R.sinlat.to_numpy(float), R.M.to_numpy(float), R.hem.to_numpy(), R.cyc.to_numpy()
    a1 = R.A.to_numpy(float) - 1.0
    out = []
    for cc in sorted(set(c)):
        for hh in ("N", "S"):
            m = (c == cc) & (h == hh)
            if m.any():
                out.append((f"I{cc}{hh}", m * s))
    if comb:
        out += [(f"M24{hh}", M * ((c == 24) & (h == hh)) * s) for hh in ("N", "S")]
        if model == "bJ":
            out.append(("M_x3", M * a1 * s))
        if model == "bA":
            out += [("M_N", M * (h == "N")), ("M_S", M * (h == "S")), ("M_A", M * a1)]
    return out, a1 * s


def wls_g(X, w):
    """Last row of (X'WX)^-1 X'W through QR of sqrt(W) X."""
    sw = np.sqrt(w)
    Q, Rr = np.linalg.qr(X * sw[:, None])
    e = np.zeros(X.shape[1])
    e[-1] = 1.0
    v = solve_triangular(Rr, e, trans="T")
    return (Q @ v) * sw


def kmat(cr, hem, scen, cross_zero):
    t = cr - cr.min()
    lag = np.abs(t[:, None] - t[None, :]).astype(float)
    same = hem[:, None] == hem[None, :]
    if scen == 7:
        K = np.maximum(0.0, 1.0 - lag / 20.0) * same
    else:
        ph, ka = AR1[scen]
        K = np.where(same, 1.0, ka) * ph ** lag
    if cross_zero:
        ins = cr >= CR_H
        K = K * (ins[:, None] == ins[None, :])
    return K


def analyse(R, models, comb, cz=(False,), dprod=None, a_e0=None):
    if len(R) == 0:
        return {m: dict(status="empty_design", columns="", dropped="", n_records=0, n_mdi=0, n_cells=0, n_cr=0) for m in models}
    w = R.phi.to_numpy(float)
    key = list(zip(R.CR.to_numpy(), R.hem.to_numpy()))
    uk = sorted(set(key))
    pos = {k: i for i, k in enumerate(uk)}
    codes = np.array([pos[k] for k in key])
    ccr, chm = np.array([k[0] for k in uk]), np.array([k[1] for k in uk])
    A = R.A.to_numpy(float)
    abar = (np.bincount(codes, A) / np.bincount(codes))[codes]
    s, M = R.sinlat.to_numpy(float), R.M.to_numpy(float)
    qd = (float(np.quantile(abar, 0.05)), float(np.quantile(abar, 0.95)))
    out = {}
    for model in models:
        nu, x3 = columns(R, model, comb)
        sw = np.sqrt(w)
        used, dropped, cols, rk = [], [], [], 0
        for nm, v in nu:
            r1 = rank(cols + [v], sw)
            if r1 > rk:
                used.append(nm)
                cols.append(v)
                rk = r1
            else:
                dropped.append(nm)
        base = dict(columns="|".join(used + ["x3"]), dropped="|".join(dropped), n_records=len(R), n_mdi=int(M.sum()),
                    n_cells=len(uk), n_cr=len(set(ccr)))
        if rank(cols + [x3], sw) != rk + 1:
            out[model] = dict(base, columns="|".join(used), status="x3_not_identifiable")
            continue
        g = wls_g(np.column_stack(cols + [x3]), w)
        b = np.bincount(codes, g, minlength=len(uk))
        res = dict(base, status="ok", a2=float(g @ g), a2_mdi=float((g * g * M).sum()), A_lo_design=qd[0], A_hi_design=qd[1])
        for (lo, hi), pre in ((a_e0, ""), (qd, "qd_")):
            for dm, tg in ((0.20, "020"), (0.10, "010")):
                res[f"target_{pre}{tg}"] = float(g @ (-dm * np.clip((abar - lo) / (hi - lo), 0, 1) * GAMMA0 * s))
        res["bKb"] = {(sc, z): float(b @ kmat(ccr, chm, sc, z) @ b) for sc in (1, 2, 3, 4, 7) for z in cz}
        if comb:
            a1 = A - 1.0
            res["B1"] = {f: float(g @ (M * a1 * (s if f == "J" else 1.0))) for f in {"a": ("A", "J"), "bA": ("A",), "bJ": ("J",)}[model]}
        if dprod is not None:
            k = R.k.to_numpy()
            dv = np.where(M == 1, np.array([np.nan, *dprod])[np.where(M == 1, k, 0)], 0.0)
            res["m_prod"] = float(g @ dv)
        out[model] = res
    return out


def nrows(res, nset, sset, cz, u):
    rows = []
    for si, sm in sset:
        for n in nset:
            f, sc, xs = NOISE[n]
            tv = (SDX * xs) ** 2 * res["bKb"][(sc, cz)]
            var = si * si * res["a2"] + sm * sm * res["a2_mdi"] + tv
            se = math.sqrt(var)
            row = dict(sigma_int=si, sigma_m=sm, noise=n, form=f, scen=sc, x_scale=xs, se=se, h_gamma0=Z * se / GAMMA0, var_temporal_share=tv / var)
            for t in TAGS:
                tg = res[f"target_{t}"]
                nul = not (math.isfinite(tg) and tg != 0)
                row[f"target_null_{t}"] = nul
                row[f"se_over_target_{t}"] = np.nan if nul else se / abs(tg)
                row[f"recognition_{t}"] = float(norm.cdf(-Z - tg / se)) if math.isfinite(tg) else np.nan
                if "m_prod" in res:
                    row[f"m_prod_over_target_{t}"] = np.nan if nul else res["m_prod"] / abs(tg)
            if "m_prod" in res:
                row["m_prod"] = res["m_prod"]
            if "B1" in res and u is not None:
                for fam, b1 in res["B1"].items():
                    unit = u["d3"] * u["sbar"] if fam == "A" else u["d3"]
                    row[f"B1_{fam}"] = b1
                    for C in C_LIM:
                        mags = (C * unit * b1, -C * unit * b1)
                        for t in TAGS:
                            tg = res[f"target_{t}"]
                            row[f"tol_units_{fam}_{t}"] = 0.5 * abs(tg) / (unit * abs(b1)) if b1 != 0 else np.inf
                            row[f"sup_scen_worst_{fam}_C{C}_{t}"] = min(float(norm.cdf(-Z - (tg + m) / se)) for m in mags)
                        row[f"sup_null_worst_{fam}_C{C}"] = max(float(norm.cdf(-Z - m / se)) for m in mags)
            rows.append(row)
    return rows


def grid(nset, sset):
    return [dict(sigma_int=si, sigma_m=sm, noise=n, form=NOISE[n][0], scen=NOISE[n][1], x_scale=NOISE[n][2]) for si, sm in sset for n in nset]


KEEP = ("columns", "dropped", "n_records", "n_mdi", "n_cells", "n_cr", "target_020", "target_010", "target_qd_020", "target_qd_010",
        "A_lo_design", "A_hi_design")


def compute(X, a_e0, n_real=N_REAL):
    H = X["H"][["CR", "hem", "sinlat", "phi", "cyc", "A", "M"]].copy()
    H["ty"] = X["H"].t_years.to_numpy(float)
    H["k"] = 0
    H["M"] = H.M.astype(float)
    hres = analyse(H, ("a", "bJ", "bA"), True, a_e0=a_e0)
    u = dict(d3=abs(hres["a"]["target_020"]), sbar=float((H.phi * H.sinlat).sum() / H.phi.sum()))
    rows = [dict(design="H", threshold="-", variant="ref", r=-1, model="a", status="ok", **{k: hres["a"][k] for k in KEEP}, **x)
            for x in nrows(hres["a"], FULL_N, [(si, 0.0) for si in SIG_INT], False, None)]
    designs = []
    cc = ["CR", "hem", "sinlat", "phi", "cyc", "A", "M", "ty", "k"]
    for r in range(n_real):
        for th in THR:
            for variant, dsg in VARIANTS.items():
                for design in dsg:
                    Rm, info = records(X, design, th, r, variant)
                    designs.append(dict(r=r, threshold=th, variant=variant, design=design, **info))
                    sig, ns = (FULL_S, FULL_N) if variant == "ref" else (list(REF_SIG), SENS_N)
                    dp = X["dg"][th] if design == "MS" else None
                    ent = []
                    if Rm is None:
                        ent.append((design, "a", None, info["status"], variant, False))
                    else:
                        n23 = Rm[Rm.cyc == 23].hem.value_counts()
                        okc = n23.get("N", 0) >= 50 and n23.get("S", 0) >= 50
                        rs = analyse(Rm[cc], ("a",), False, dprod=dp, a_e0=a_e0)["a"]
                        ent.append((design, "a", rs, rs["status"] if rs["status"] != "ok" or okc else "not_separate_measure", variant, False))
                    if variant != "act_amain":
                        names = ["ref", "w_x0.5", "w_x2", "w_norm"] if variant == "ref" else [variant]
                        if Rm is None:
                            for vn in names + (["cov_zero_cross"] if variant == "ref" else []):
                                ent += [(f"{design}+H", m, None, info["status"], vn, vn == "cov_zero_cross") for m in ("a", "bJ", "bA")]
                        else:
                            base = pd.concat([H[cc], Rm[cc]], ignore_index=True)
                            for vn in names:
                                x = base.copy()
                                ph = x.phi.to_numpy(float).copy()
                                mm = x.M.to_numpy() == 1
                                if vn == "w_x0.5":
                                    ph[mm] *= 0.5
                                elif vn == "w_x2":
                                    ph[mm] *= 2.0
                                elif vn == "w_norm":
                                    ph[~mm] /= ph[~mm].mean()
                                    ph[mm] /= ph[mm].mean()
                                x["phi"] = ph
                                czs = (False, True) if vn == "ref" else (False,)
                                for m, rs in analyse(x, ("a", "bJ", "bA"), True, czs, dp, a_e0).items():
                                    ent.append((f"{design}+H", m, rs, rs["status"], vn, False))
                                    if vn == "ref":
                                        ent.append((f"{design}+H", m, rs, rs["status"], "cov_zero_cross", True))
                    for dn, m, rs, st, vn, cz in ent:
                        sg, nn_ = (sig, ns) if vn == variant else (list(REF_SIG), SENS_N)
                        b = dict(design=dn, threshold=th, variant=vn, r=r, model=m, status=st)
                        if rs is None or rs["status"] != "ok":
                            kn = {k: rs[k] for k in KEEP if rs is not None and k in rs}
                            rows += [dict(b, **kn, **gc) for gc in grid(nn_, sg)]
                        else:
                            kp = {k: rs[k] for k in KEEP}
                            rows += [dict(b, **kp, **x) for x in nrows(rs, nn_, sg, cz, u)]
    raw = pd.DataFrame(rows)
    hh = {(a, b): v for a, b, v in raw[raw.design == "H"][["sigma_int", "noise", "h_gamma0"]].itertuples(index=False, name=None)}
    raw["h_over_hH"] = raw.h_gamma0 / np.array([hh.get((a, b), np.nan) for a, b in zip(raw.sigma_int, raw.noise)])
    return raw, pd.DataFrame(designs), u


# ---------------------------------------------------------------- own summaries and criteria

def summarise(raw, n_real):
    keys = raw[KEYC].drop_duplicates()
    ok = raw[raw.status == "ok"]
    vals = [c for c in ok.columns if c not in KEYC + ["r", "status", "columns", "dropped"] and pd.api.types.is_numeric_dtype(ok[c])
            and not pd.api.types.is_bool_dtype(ok[c])]
    g = ok.groupby(KEYC, dropna=False)
    parts = [g[vals].median().add_suffix("_median"), g[vals].min().add_suffix("_min"), g[vals].max().add_suffix("_max"),
             g[[c for c in ok.columns if c.startswith("target_null_")]].sum().astype(int).add_suffix("_n"), g.r.nunique().rename("n_ok")]
    agg = pd.concat(parts, axis=1).reset_index()
    out = keys.merge(agg, on=KEYC, how="left")
    out["n_ok"] = out.n_ok.fillna(0).astype(int)
    out["n_fail"] = np.where(out.design == "H", 0, n_real - out.n_ok)
    nc = raw[raw.status != "ok"].groupby(["design", "threshold", "variant", "model", "status"]).r.nunique().rename("n_realisations").reset_index()
    return out, nc


def paired(raw, num, den, vn="ref", vd="ref", th="main", sig=(15.0, 2.0), model="a"):
    ok = raw[raw.status == "ok"]
    nreal = raw[raw.design != "H"].r.nunique()
    out = {}
    for sc, xs in MAIN3:
        def sel(d, v):
            return ok[(ok.design == d) & (ok.variant == v) & ok.threshold.isin([th, "-"]) & (ok.model == ("a" if d == "H" else model))
                      & (ok.scen == sc) & (ok.x_scale == xs) & (ok.sigma_int == sig[0]) & (ok.sigma_m == (0.0 if d == "H" else sig[1]))]
        a = sel(num, vn).set_index("r").h_gamma0
        q = a / float(sel("H", "ref").h_gamma0.iloc[0]) if den == "H" else a / sel(den, vd).set_index("r").h_gamma0
        q = q.dropna()
        out[sc] = dict(median=float(q.median()) if len(q) else np.nan, n_ok=int(len(q)), n_fail=int(nreal - len(q)))
    return out


def criteria(raw, th):
    good = lambda d: all(v["n_fail"] == 0 for v in d.values())          # noqa: E731
    rows = []
    u1, u2 = paired(raw, "MS+H", "H", th=th), paired(raw, "MS+H", "H", th=th, sig=(30.0, 10.0))
    if not (good(u1) and good(u2)):
        v = NA_SEP
    elif all(x["median"] <= 0.7 for x in u1.values()) and all(x["median"] <= 0.8 for x in u2.values()):
        v = "utile come limite"
    elif all(x["median"] <= 0.9 for x in u1.values()):
        v = "marginale"
    else:
        v = "riduzione inferiore al criterio fissato, nelle configurazioni esaminate"
    rows.append(dict(criterion="contributo MDI (MS+H vs H)", threshold=th, verdict=v, detail=dict(ref=u1, robust=u2)))
    for d in ("MS", "MF"):
        x = paired(raw, d, "H", th=th)
        v = NA_SEP if not good(x) else ("misura T3 su un altro periodo/ciclo (essenzialmente il 23), con precisione prospettica almeno pari"
                                        if all(t["median"] <= 1.0 for t in x.values()) else "precisione inferiore a H")
        rows.append(dict(criterion=f"{d} da solo vs H", threshold=th, verdict=v, detail=x))
    mf = {k: paired(raw, "MF+H", "MS+H", vn=k, th=th) for k in ("ref", "mf_pool_cohort_act")}
    if not all(good(x) for x in mf.values()):
        v = NA_SEP
    elif all(t["median"] <= 1.1 for x in mf.values() for t in x.values()):
        v = "MF da considerare"
    else:
        v = "MF non considerato (perdita di resa)"
    rows.append(dict(criterion="prodotto MF+H vs MS+H", threshold=th, verdict=v, detail=mf))
    for m in ("bJ", "bA"):
        rows.append(dict(criterion=f"accanto: modello protetto {m}, MS+H vs H", threshold=th, verdict="(senza criterio)",
                         detail=paired(raw, "MS+H", "H", th=th, model=m)))
    return rows


def cell_table(X):
    P, cells = X["P"], X["cells"]
    out = cells[CELL_KEYS].copy()
    out["N_selection"] = cells.N.to_numpy()
    for name, m in (("N_orig", np.ones(len(P), bool)), ("N_f1_date", P.f1), ("N_f2_cr", P.f1 & P.f2),
                    ("MS_f3_maps", P.f1 & P.f2 & ~P.map_missing), ("MS_f3_N_ambiguous", P.MS), ("MF_f4_gap", P.MF)):
        out[name] = [int((np.asarray(m, bool) & (P.cell.to_numpy() == c)).sum()) for c in range(len(cells))]
    out["N_MS"], out["N_MF"] = out.MS_f3_N_ambiguous, out.MF_f4_gap
    for th in THR:
        out[f"ms_units_n_{th}"], out[f"ms_units_r_{th}"] = X["ms"][th][0].astype(int), X["ms"][th][1].astype(int)
    return out


def yield_steps(X):
    """Own YIELD_EFFECTS with every column (labels written here, not taken from the runner)."""
    P, N = X["P"], X["cells"].N.to_numpy(float)
    c = P.cell.to_numpy()
    rows = []

    def add(th, d, k, step, change, v):
        rows.append(dict(threshold=th, design=d, step_order=k, step=step, change=change, value=float(v)))
    for th in THR:
        n, r = X["ms"][th]
        n0, r0 = X["ms_all"][th]
        d = P.MS.to_numpy()
        add(th, "MS", 1, "r/n, all L1 units, eligible population (published)", "-", (N * r0 / n0).sum() / N.sum())
        add(th, "MS", 2, "r/n, map-missing units removed, eligible population", "units", (N * r / n).sum() / N.sum())
        add(th, "MS", 3, "r/n, map-missing units removed, Q4 domain", "domain", (r / n)[c][d].mean())
        add(th, "MS", 4, "Beta mean, Q4 domain", "Beta", ((r + 0.5) / (n + 1))[c][d].mean())
        a, f = X["mf_all"], X["mf"]
        add(th, "MF", 1, "ratio estimate, all level-2 units, eligible population (published)", "-", (a.w * a[f"ok_{th}"]).sum() / a.w.sum())
        add(th, "MF", 2, "ratio estimate, gap units removed, eligible population", "units", (f.w * f[f"ok_{th}"]).sum() / f.w.sum())
        pl = X["pools"][th]
        dm = P.MF.to_numpy()
        for k, kind in enumerate(("cohort", "cohort_act", "cohort_area")):
            ix = pool_idx(P, kind)
            ph = pl.p_hat.to_numpy()[ix]
            be = ((pl.r_eff + 0.5) / (pl.n_eff + 1)).to_numpy()[ix]
            add(th, "MF", 3 + 3 * k, f"pool {kind} p_hat, eligible population", "pool", ph.mean())
            add(th, "MF", 4 + 3 * k, f"pool {kind} p_hat, Q4 domain", "domain", ph[dm].mean())
            add(th, "MF", 5 + 3 * k, f"pool {kind} Beta mean, Q4 domain", "Beta", be[dm].mean())
    return pd.DataFrame(rows)


def expected_choices():
    """IMPLEMENTATION_CHOICES of the runner as committed at the run HEAD, parsed from the blob (no import), and pinned."""
    import ast
    src = subprocess.run(["git", "show", f"{EXPECTED['head']}:{SCRIPT_REL}"], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "IMPLEMENTATION_CHOICES" for t in node.targets):
            v = ast.literal_eval(node.value)
            if hashlib.sha256(json.dumps(v).encode()).hexdigest() != CHOICES_SHA:
                raise ValueError("implementation choices at the run HEAD differ from the pinned ones")
            return v
    raise ValueError("IMPLEMENTATION_CHOICES not found at the run HEAD")


# ---------------------------------------------------------------- comparison helpers

EXACT = {"n_records", "n_mdi", "n_cells", "n_cr", "noise", "r", "scen", "n_ok", "n_fail", "n_domain", "n_included",
         "n_excluded_yield", "n_no_activity", "N_selection", "N_orig", "N_f1_date", "N_f2_cr", "MS_f3_maps", "MS_f3_N_ambiguous",
         "MF_f4_gap", "N_MS", "N_MF", "ms_units_n_main", "ms_units_r_main", "ms_units_n_sens100", "ms_units_r_sens100", "n", "ok",
         "n_realisations", "step_order", "act_class", "area_class"}
SIGNED = {"r"}                           # r = -1 for the H rows


def is_exact(c):
    return c in EXACT or (c.startswith("target_null_") and c.endswith("_n"))


def close_cols(a, b, tol=1e-8):
    """(ok, reason) for two aligned frames with the same columns. Counts (by column meaning, not by dtype) must be finite,
    integer, non-negative where expected and exactly equal; flags must be True/False (or missing on both sides);
    other numbers are compared with the relative tolerance."""
    for c in a.columns:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        xn, yn = pd.to_numeric(pd.Series(x), errors="coerce").to_numpy(float), pd.to_numeric(pd.Series(y), errors="coerce").to_numpy(float)
        if is_exact(c):
            nx, ny = pd.Series(x).isna().to_numpy(), pd.Series(y).isna().to_numpy()
            v = xn[~nx]
            if not (np.array_equal(nx, ny) and np.isfinite(v).all() and (v == np.round(v)).all() and (c in SIGNED or (v >= 0).all())
                    and np.array_equal(v, yn[~ny])):
                return False, f"{c} (count: not finite, not integer, negative or different)"
            continue
        if c.startswith("target_null_"):
            sx, sy = pd.Series(x).astype(str).to_numpy(), pd.Series(y).astype(str).to_numpy()
            if not (set(sx) <= {"True", "False", "nan"} and (sx == sy).all()):
                return False, f"{c} (flag)"
            continue
        numeric = (pd.Series(x).isna() | ~np.isnan(xn)).all() and (pd.Series(y).isna() | ~np.isnan(yn)).all() and a[c].dtype != object
        if pd.api.types.is_bool_dtype(a[c]) or pd.api.types.is_bool_dtype(b[c]):
            if not (pd.Series(x).astype(str).to_numpy() == pd.Series(y).astype(str).to_numpy()).all():
                return False, c
        elif numeric:
            both_nan = np.isnan(xn) & np.isnan(yn)
            same_inf = np.isinf(xn) & np.isinf(yn) & (np.sign(xn) == np.sign(yn))
            fin = np.isfinite(xn) & np.isfinite(yn)
            scale = np.nanmax(np.abs(np.where(fin, yn, np.nan))) if fin.any() else 0.0
            okv = both_nan | same_inf | (fin & (np.abs(xn - yn) <= tol * np.maximum(np.abs(xn), np.abs(yn)) + 1e-12 * scale))
            if not okv.all():
                return False, f"{c} ({int((~okv).sum())} values)"
        else:
            nm = lambda s: pd.Series(s).astype(str).replace({"nan": "", "None": "", "NaN": ""}).to_numpy()      # noqa: E731
            if not (nm(x) == nm(y)).all():
                return False, c
    return True, ""


def frames_match(theirs, mine, key, tol=1e-8, ordered=False):
    """Exact column set (and order if `ordered`), same number of rows, unique and equal keys, then every value."""
    if ordered and list(theirs.columns) != list(mine.columns):
        return False, f"schema {list(theirs.columns)} vs {list(mine.columns)}"
    if set(theirs.columns) != set(mine.columns):
        return False, f"columns: extra {sorted(set(theirs.columns) - set(mine.columns))[:3]}, missing {sorted(set(mine.columns) - set(theirs.columns))[:3]}"
    if len(theirs) != len(mine):
        return False, f"rows {len(theirs)} vs {len(mine)}"
    a = theirs.sort_values(key, kind="mergesort").reset_index(drop=True)
    b = mine[list(theirs.columns)].sort_values(key, kind="mergesort").reset_index(drop=True)
    if a.duplicated(key).any() or b.duplicated(key).any():
        return False, "duplicated keys"
    kk = lambda d: d[key].astype(str).agg("|".join, axis=1).to_numpy()   # noqa: E731
    if not (kk(a) == kk(b)).all():
        return False, "keys differ"
    return close_cols(a, b, tol)


PROTECTED = {"bA": "A", "bJ": "J"}      # the protected model contains the offset shape of its own family: B1 = 0 analytically


NULL_TOL = -2.0                          # sentinel for a protected tolerance with a null target (0 or +inf by formula)


def protected_tolerances(df, summary=False):
    """Protected models contain the offset shape of their own family, so B1 of that family is zero by construction
    (numerically ~1e-17) and 0.5|target|/(unit |B1|) is numerical noise of arbitrary size. Returns (copy with those
    tolerances normalised, domain check). Rules, RAW: successful rows need a finite negligible B1 (<= 1e-10 of the
    scale of the other rows) and, per target, a tolerance that is +inf or >= 1e6 (positive), or, when the target is null,
    0 or +inf (normalised to a sentinel); failed rows need B1 and tolerances missing. SUMMARY: with n_ok = 0 every value
    missing; otherwise +inf or >= 1e6, or 0 only when that target was null in some realisation. Missing values stay
    missing; non-protected families are not touched."""
    d = df.copy()
    good = True
    for model, fam in PROTECTED.items():
        m = (d.model == model).to_numpy()
        cols = [c for c in d.columns if c.startswith(f"tol_units_{fam}_")]
        if not m.any() or not cols:
            continue
        if not summary:
            okr = (d.status == "ok").to_numpy()
            b = pd.to_numeric(d[f"B1_{fam}"], errors="coerce").to_numpy(float)
            other = okr & ~m & np.isfinite(b)
            sc = np.nanmax(np.abs(b[other])) if other.any() else 1.0
            good &= bool(np.isfinite(b[m & okr]).all() and (np.abs(b[m & okr]) <= 1e-10 * sc).all() and np.isnan(b[m & ~okr]).all())
            for c in cols:
                tag = c[len(f"tol_units_{fam}_"):]
                v = pd.to_numeric(d[c], errors="coerce").to_numpy(float)
                nul = d[f"target_null_{tag}"].astype(str).eq("True").to_numpy()
                big = (v == np.inf) | (np.isfinite(v) & (v >= 1e6))
                zero_or_inf = (v == 0) | (v == np.inf)
                good &= bool(np.isnan(v[m & ~okr]).all() and (big | (nul & zero_or_inf))[m & okr].all())
                out = v.copy()
                out[m & okr & nul] = NULL_TOL
                out[m & okr & ~nul] = np.inf
                d[c] = out
        else:
            nok = pd.to_numeric(d.n_ok, errors="coerce").to_numpy(float)
            for c in cols:
                tag = c[len(f"tol_units_{fam}_"):].rsplit("_", 1)[0]
                v = pd.to_numeric(d[c], errors="coerce").to_numpy(float)
                nn = pd.to_numeric(d.get(f"target_null_{tag}_n", 0), errors="coerce")
                nn = np.zeros(len(d)) if np.isscalar(nn) else nn.to_numpy(float)
                big = (v == np.inf) | (np.isfinite(v) & (v >= 1e6))
                good &= bool(np.isnan(v[m & (nok == 0)]).all() and (big | ((v == 0) & (nn > 0)))[m & (nok > 0)].all())
                out = v.copy()
                out[m & big] = np.inf
                d[c] = out
    return d, good


def json_close(a, b, tol=1e-8):
    if isinstance(a, dict):
        return isinstance(b, dict) and set(map(str, a)) == set(map(str, b)) and all(json_close(a[k], b[str(k)] if str(k) in b else b[k], tol) for k in a)
    if isinstance(a, (list, tuple)):
        return isinstance(b, (list, tuple)) and len(a) == len(b) and all(json_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if a is None or b is None:
        return a is None and b is None
    fa, fb = float(a), float(b)
    return (math.isnan(fa) and math.isnan(fb)) or fa == fb or abs(fa - fb) <= tol * max(abs(fa), abs(fb))


# ---------------------------------------------------------------- check

def real_inputs():
    PA = _load_dep("prospective_phase_a", "scripts/prospective_phase_a.py")
    PC = _load_dep("mdi_q4_prep_counts", "scripts/mdi_q4_prep_counts.py")
    rd = lambda p, cols=None, **k: pd.read_csv(p, usecols=cols, **k)       # noqa: E731
    pop = rd(SEL / "POPULATION.csv", dtype={"noaa": str})
    samp = rd(SEL / "SAMPLE.csv", dtype={"noaa": str})
    cells = rd(SEL / "CELLS.csv")
    l1 = rd(L1F, ["noaa", "day", "status", "sens100_status", "main_flux_pos_mx", "main_flux_neg_mx", "sens100_flux_pos_mx",
                  "sens100_flux_neg_mx"], dtype={"noaa": str})
    l2 = rd(L2F, ["rule", "noaa", "day", "image", "status", "sens100_status"], dtype={"noaa": str})
    q2p = {t: rd(AN2 / f"Q2_PAIRS_A1_{t}.csv", ["flux_ratio"]).flux_ratio.to_numpy(float) for t in THR}
    q2s = {t: rd(AN2 / f"Q2_SUMMARY_A1_{t}.csv", ["group", "median_d_gamma"]) for t in THR}
    inv = set(rd(AUDIT, ["CAR_ROT"]).CAR_ROT.astype(int))
    miss = [c for c in range(min(inv), max(inv) + 1) if c not in inv]
    S, _ = PA.load_inputs()
    H = PA.e0_records(S)
    rot = (lambda t, lo, lc: PC.A.group_rotation(t, lo, lc)[:3], PC.required_maps)
    return (pop, samp, cells, l1, l2, q2p, q2s, miss, H, rot)


def _load_dep(name, rel):
    return sys.modules[name] if name in sys.modules else _mod(name, rel)


def e0_quantiles():
    r = pd.read_csv(PHASE_A_RAW, usecols=["ext", "A_lo_ext", "A_hi_ext"])
    q = r[r.ext == "E0"][["A_lo_ext", "A_hi_ext"]].drop_duplicates()
    if len(q) != 1:
        raise ValueError("E0 quantiles not unique in the phase A RAW")
    return float(q.A_lo_ext.iloc[0]), float(q.A_hi_ext.iloc[0])


def check(out=OUT, write=True, rec_dir=REC, data=None, n_real=N_REAL, outputs=None):
    """data: injected raw inputs (selftest); outputs: dict of injected product frames instead of the files."""
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    real = data is None and outputs is None
    if real:
        nf = json.loads((Path(GATE_ROOT) / "docs/MDI_PILOT_Q4_NOTE_FREEZE.json").read_text())
        af = json.loads((Path(GATE_ROOT) / A2_FREEZE_REL).read_text())
        pv = provenance(nf, af, sha(Path(GATE_ROOT) / "docs/MDI_PILOT_Q4_NOTE_FREEZE.json"), sha(Path(GATE_ROOT) / A2_FREEZE_REL))
        ok("provenance of the files read or imported now: receipts pinned, note, A2, parent, rules, 9 reused code files and 17 "
           "inputs with exact sets and current hashes", not pv, pv)
        if pv:
            print("provenance not verified: stop before reading outputs or importing dependencies")
            return _finish(checks, real, write, rec_dir, out)
        files = {p.name for p in Path(out).iterdir()}
        ok("outputs: exact product set", files == PRODUCTS, sorted(files ^ PRODUCTS))
        meta = json.loads((Path(out) / "META.json").read_text())
        blob = subprocess.run(["git", "show", f"{EXPECTED['head']}:{SCRIPT_REL}"], cwd=ROOT, capture_output=True)
        ok("run: script SHA = fed1775 correction, equal to the blob at the run HEAD; note, A2 and receipts pinned; no receipt problem",
           meta["script_sha256"] == EXPECTED["script"] == hashlib.sha256(blob.stdout).hexdigest() and meta["git_head"] == EXPECTED["head"]
           and meta["note_sha256"] == EXPECTED["note"] and meta["a2_sha256"] == EXPECTED["a2"]
           and meta["note_freeze_sha256"] == EXPECTED["note_receipt"] and meta["a2_freeze_sha256"] == EXPECTED["a2_receipt"]
           and meta["receipts_problems"] == [])
        nf = json.loads(NOTE_FREEZE.read_text())
        ok("inputs unchanged since the freeze (17 files of the note receipt)", sha(NOTE_FREEZE) == EXPECTED["note_receipt"]
           and all(sha(ROOT / p) == h for p, h in nf["inputs_sha256"].items()))
        ok("run: exit 0, internal selftest and proofs 55/55, no technical stop",
           (Path(out) / "RUN.exit").read_text().strip() == "0" and "selftest 55/55" in (Path(out) / "RUN.log").read_text()
           and "TECHNICAL STOP" not in (Path(out) / "RUN.log").read_text())
        pr = pd.read_csv(Path(out) / "PROOFS.csv")
        ok("PROOFS: 55 checks, all true", len(pr) == 55 and pr.ok.astype(str).eq("True").all())
        ok("seed0, realisations, z", meta["seed0"] == SEED0 == nf["seed0"] and meta["n_realisations"] == N_REAL and meta["z"] == Z == nf["z"])
        if not all(c["ok"] for c in checks):
            print("prerequisites not met: stop before any computation")
            return _finish(checks, real, write, rec_dir, out)
        rd = lambda n, **k: pd.read_csv(Path(out) / n, keep_default_na=False, na_values=[""], **k)   # noqa: E731
        outputs = dict(RAW=pd.read_csv(Path(out) / "RAW.csv.gz", keep_default_na=False, na_values=[""], low_memory=False),
                       SUMMARY=rd("SUMMARY.csv", low_memory=False), NOT_COMPUTABLE=rd("NOT_COMPUTABLE.csv"), CRITERIA=rd("CRITERIA.csv"),
                       DESIGNS=rd("DESIGNS.csv"), YIELD_EFFECTS=rd("YIELD_EFFECTS.csv"), CELL_COUNTS=rd("CELL_COUNTS.csv"),
                       MF_POOLS=rd("MF_POOLS.csv", dtype={"key": str}), META=meta)
        data = real_inputs()
    a_e0 = e0_quantiles()
    ok("E0 quantiles read from the phase A RAW at full precision", a_e0 == (0.5020189558504007, 2.7602501179328134), a_e0)
    X = assemble(*data)
    if real:
        pm = json.loads(PREP_META.read_text())
        P = X["P"]
        ok("filters and counts: MS 5151, MF 5062, MF before the gap, map-missing and N-ambiguous as the preparatory META; missing maps "
           "1938-1940, MS units removed 8, missing years 1996 and 2008",
           int(P.MS.sum()) == pm["C3"]["MS"] == 5151 and int(P.MF.sum()) == 5062 and int((P.f1 & P.f2).sum()) == pm["C3"]["MF"]
           and int(P.map_missing.sum()) == pm["C2"]["population_map_missing"] and int(P.N_amb.sum()) == pm["C2"]["population_N_ambiguous"]
           and X["missing_maps"] == [1938, 1939, 1940] and X["ms_removed"] == 8 and X["missing_years"] == [1996, 2008])
        ok("d_gamma of the Q2 summaries equal to the note (rounded)", {t: tuple(round(v, 2) for v in X["dg"][t]) for t in THR}
           == {"main": (-0.53, -0.79, -1.19), "sens100": (-0.58, -1.29, -1.34)})
    raw, des, u = compute(X, a_e0, n_real)
    tr, g1 = protected_tolerances(outputs["RAW"])
    mr, g2 = protected_tolerances(raw)
    ok("protected models (bA family A, bJ family J): B1 negligible (<= 1e-10 of the scale) and tolerance unbounded (>= 1e6 or inf), "
       "in the run and in the recount; compared as unbounded below", g1 and g2)
    good, why = frames_match(tr, mr, ["design", "threshold", "variant", "r", "model", "sigma_int", "sigma_m", "noise"])
    ok("RAW: every row and column rebuilt (keys, statuses, columns used and dropped, counts, targets, quantiles, SE, h, shares, "
       "ratios and flags, recognition, product shift, offsets, tolerances, worst cases, h/h_H)", good, why)
    sm, nc = summarise(raw, n_real)
    ts_, g3 = protected_tolerances(outputs["SUMMARY"], True)
    ms_, g4 = protected_tolerances(sm, True)
    good, why = frames_match(ts_, ms_, KEYC)
    ok("SUMMARY: protected tolerances in their domain; every configuration, median/min/max, null-target counts, n_ok and n_fail",
       good and g3 and g4, why if not good else f"domain run {g3}, recount {g4}")
    t_nc = outputs["NOT_COMPUTABLE"]
    ok("NOT_COMPUTABLE: same causes and counts", (len(t_nc) == 0 and len(nc) == 0 and list(t_nc.columns) == list(nc.columns))
       or frames_match(t_nc, nc, ["design", "threshold", "variant", "model", "status"])[0], f"{len(t_nc)} vs {len(nc)}")
    good, why = frames_match(outputs["DESIGNS"], des, ["r", "threshold", "variant", "design"], ordered=True)
    ok("DESIGNS: domains, statuses, inclusions, exclusions, activity losses, expected yields, |lat| distances", good, why)
    mine = criteria(raw, "main") + criteria(raw, "sens100")
    th_ = outputs["CRITERIA"]
    ok("CRITERIA: exact schema; criteria, verdicts and every paired median, n_ok and n_fail (both thresholds)",
       list(th_.columns) == ["criterion", "threshold", "verdict", "detail"] and len(th_) == len(mine) and all(a.criterion == b["criterion"] and a.threshold == b["threshold"] and a.verdict == b["verdict"]
                                     and json_close(b["detail"], json.loads(a.detail)) for a, b in zip(th_.itertuples(), mine)))
    good, why = frames_match(outputs["CELL_COUNTS"], cell_table(X), CELL_KEYS, ordered=True)
    ok("CELL_COUNTS: N per cell, original and after each filter, MS/MF domains, MS units", good, why)
    good, why = frames_match(outputs["YIELD_EFFECTS"], yield_steps(X), ["threshold", "design", "step_order"], ordered=True)
    ok("YIELD_EFFECTS: exact schema, unique and complete keys, labels, changes and values (one change per step)", good, why)
    mp = pd.concat([X["pools"][t].assign(threshold=t) for t in THR], ignore_index=True)
    good, why = frames_match(outputs["MF_POOLS"].astype({"key": str}), mp, ["threshold", "pool", "key"], ordered=True)
    ok("MF_POOLS: n, ok, p_hat, Kish n_eff, r_eff per pool and threshold", good, why)
    meta = outputs["META"]
    P = X["P"]
    filt = dict(population=len(P), excl_date=int((~P.f1).sum()), excl_cr=int((P.f1 & ~P.f2).sum()),
                MS_excl_map_missing=int((P.f1 & P.f2 & P.map_missing).sum()),
                MS_excl_N_ambiguous=int((P.f1 & P.f2 & ~P.map_missing & P.N_amb).sum()), MF_excl_gap=int((P.f1 & P.f2 & P.gap).sum()),
                MS=int(P.MS.sum()), MF=int(P.MF.sum()))
    choices = expected_choices()
    if real:
        ok("META: exact key set", set(meta) == META_KEYS, sorted(set(meta) ^ META_KEYS))
    ok("META: H units (d3, sbar), missing years, noise rows, filter counts, the nine implementation choices in order",
       json_close(u, meta["units"]) and meta["mf_missing_years"] == X["missing_years"]
       and [list(x) for x in NOISE] == meta["noise"] and meta["filters"] == filt and meta["implementation_choices"] == choices)
    return _finish(checks, real, write, rec_dir, out)


def _finish(checks, real, write, rec_dir, out):
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks)
    if real:
        receipt["outputs_sha256"] = {p.name: sha(p) for p in sorted(Path(out).iterdir())}
        receipt["recount_sha256"] = sha(__file__)
        used = sorted(INPUTS17 | CODE9 | {NOTE_REL, A2_REL, A2_FREEZE_REL, PARENT_REL, RULES_REL, "docs/MDI_PILOT_Q4_NOTE_FREEZE.json"})
        receipt["inputs_sha256"] = {p: sha(ROOT / p) for p in used}
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


# ---------------------------------------------------------------- selftest

def selftest():
    import contextlib
    import io
    import tempfile
    Q = _mod("q4_runner_for_selftest", SCRIPT_REL)              # runner only to produce synthetic outputs
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    ok("own Z equal to the frozen z", Z == json.loads(NOTE_FREEZE.read_text())["z"])
    ok("own cr_start, CR(t), cycle and years equal to phase A on a range of dates",
       all(cr_of(t) == Q.PC.cr_of_time(t) and cycle(cr_start([cr_of(t)])[0]) == Q.PA.cycle_of_time(cr_start([cr_of(t)])[0])[0]
           and years(cr_start([cr_of(t)])[0]) == Q.PA.years(cr_start([cr_of(t)])[0])
           for t in pd.date_range("1996-01-03", "2026-09-28", freq="37D")))
    mon = silso_monthly()
    ref = Q.PA.run_p2.load_silso()["monthly"]
    ok("own SILSO monthly normalisation equal to run_p2", np.allclose(mon.to_numpy(), ref.to_numpy(), rtol=1e-14, atol=0, equal_nan=True))
    rng = np.random.default_rng(5)
    Xm, w = rng.random((60, 5)), rng.uniform(1, 3, 60)
    ok("WLS row by QR equal to p2d.wls_row", np.allclose(wls_g(Xm, w), Q.p2d.wls_row(Xm, w, 4), rtol=1e-10, atol=1e-14))
    cr = np.array([2000, 2001, 2003, 2096, 2097, 2100])
    hm = np.array(["N", "S", "N", "S", "N", "N"])
    ok("own temporal covariances equal to diag_t5_oracle.k_true (scenarios 1, 2, 3, 4, 7)",
       all(np.allclose(kmat(cr, hm, s, False), Q.D.k_true(cr - cr.min(), (hm == "S").astype(int), s), rtol=0, atol=1e-15) for s in (1, 2, 3, 4, 7)))
    captured = {}
    real_assemble = Q.assemble

    def spy(*a):
        captured["a"] = a
        return real_assemble(*a)
    Q.assemble = spy
    try:
        I = Q.fake_inputs()
    finally:
        Q.assemble = real_assemble
    _, pop, samp, cells, l1, l2, q2p, q2s, miss, silso, H = captured["a"]
    data = (pop, samp, cells, l1, l2, q2p, q2s, miss, H, (lambda t, lo, lc: Q.PC.A.group_rotation(t, lo, lc)[:3], Q.PC.required_maps))
    raw, des, u = Q.compute(I, n_real=2, log=lambda *a: None)
    sm, nc = Q.summarise(raw, 2)
    crit = pd.concat([Q.criteria(raw, "main"), Q.criteria(raw, "sens100")], ignore_index=True)
    outputs = dict(RAW=raw, SUMMARY=sm, NOT_COMPUTABLE=nc, CRITERIA=crit, DESIGNS=des, YIELD_EFFECTS=Q.yield_effects(I),
                   CELL_COUNTS=Q.cell_counts(I), MF_POOLS=pd.concat([I["mf_pools"][t].assign(threshold=t) for t in Q.THR]),
                   META=dict(units=u, mf_missing_years=I["mf_missing_years"], noise=[list(n) for n in Q.NOISE],
                             filters=dict(population=len(I["pop"]), excl_date=int((~I["pop"].f1).sum()), excl_cr=int((I["pop"].f1 & ~I["pop"].f2).sum()),
                                          MS_excl_map_missing=int((I["pop"].f1 & I["pop"].f2 & I["pop"].map_missing).sum()),
                                          MS_excl_N_ambiguous=int((I["pop"].f1 & I["pop"].f2 & ~I["pop"].map_missing & I["pop"].N_amb).sum()),
                                          MF_excl_gap=int((I["pop"].f1 & I["pop"].f2 & I["pop"].gap).sum()), MS=int(I["pop"].in_MS.sum()),
                                          MF=int(I["pop"].in_MF.sum())), implementation_choices=Q.IMPLEMENTATION_CHOICES))
    # the CSV round trip of the real run
    with tempfile.TemporaryDirectory() as td:
        for k, v in outputs.items():
            if isinstance(v, pd.DataFrame):
                v.to_csv(Path(td) / f"{k}.csv", index=False)
        rt = {k: (pd.read_csv(Path(td) / f"{k}.csv", keep_default_na=False, na_values=[""], low_memory=False, **({"dtype": {"key": str}} if k == "MF_POOLS" else {}))
                  if isinstance(v, pd.DataFrame) else v) for k, v in outputs.items()}

    def quiet(o, d=data):
        with contextlib.redirect_stdout(io.StringIO()):
            return check(write=False, data=d, n_real=2, outputs=o)
    ok("synthetic run (2 realisations, CSV round trip) recounted in full", quiet(rt))

    def tamper(name, key, fn):
        o = dict(rt)
        o[key] = fn(rt[key].copy())
        got = quiet(o)
        res.append(not got)
        print(f"[{'OK' if not got else 'FALLITO'}] refused: {name}")
    i0 = rt["RAW"].index[(rt["RAW"].design == "MS+H") & (rt["RAW"].status == "ok")][0]
    first = lambda t, c, v, i=0: t.assign(**{c: t[c].where(t.index != i, v)})                  # noqa: E731
    tamper("a SE moved by 1e-6 relative", "RAW", lambda t: first(t, "se", t.se[i0] * (1 + 1e-6), i0))
    tamper("a recognition probability", "RAW", lambda t: first(t, "recognition_qd_010", t.recognition_qd_010[i0] * 1.01 + 1e-9, i0))
    tamper("a dropped column name", "RAW", lambda t: first(t, "dropped", "x", i0))
    tamper("a worst case of family J", "RAW", lambda t: first(t, "sup_scen_worst_J_C0.5_020", 0.5, i0))
    tamper("a status", "RAW", lambda t: first(t, "status", "x3_not_identifiable", i0))
    tamper("a RAW row dropped", "RAW", lambda t: t.drop(index=i0))
    tamper("an h/h_H", "RAW", lambda t: first(t, "h_over_hH", 0.5, i0))
    tamper("a SUMMARY median", "SUMMARY", lambda t: first(t, "se_median", 1.0))
    tamper("a SUMMARY n_fail", "SUMMARY", lambda t: first(t, "n_fail", 1))
    tamper("a verdict", "CRITERIA", lambda t: first(t, "verdict", "utile come limite" if t.verdict[0] != "utile come limite" else "marginale"))
    tamper("a paired median in a criterion detail", "CRITERIA",
           lambda t: first(t, "detail", t.detail[2].replace('"median": ', '"median": 1', 1), 2))
    tamper("a design inclusion count", "DESIGNS", lambda t: first(t, "n_included", t.n_included[0] + 1))
    tamper("an expected yield", "DESIGNS", lambda t: first(t, "expected_yield", 0.5))
    tamper("a yield step", "YIELD_EFFECTS", lambda t: first(t, "value", 0.123))
    tamper("a cell count", "CELL_COUNTS", lambda t: first(t, "MF_f4_gap", t.MF_f4_gap[0] + 1))
    tamper("a Kish n_eff", "MF_POOLS", lambda t: first(t, "n_eff", 1.0))
    tamper("META units", "META", lambda m: dict(m, units=dict(m["units"], d3=1.0)))
    # Codex review of 0344bc3: the six accepted alterations
    def first_where(t, mask, col, v):
        t = t.copy()
        t.loc[t.index[mask][0], col] = v
        return t
    tolA = lambda t: next(c for c in t.columns if c.startswith("tol_units_A_"))   # noqa: E731
    tamper("protected SUMMARY tolerance set to zero", "SUMMARY", lambda t: first_where(t, t.model.eq("bA").to_numpy(), tolA(t), 0.0))
    tamper("protected RAW tolerance negative (-1e30)", "RAW",
           lambda t: first_where(t, (t.model.eq("bA") & t.status.eq("ok")).to_numpy(), tolA(t), -1e30))
    tamper("protected RAW tolerance -inf", "RAW", lambda t: first_where(t, (t.model.eq("bA") & t.status.eq("ok")).to_numpy(), tolA(t), -np.inf))

    def dup_yield(t):
        t = t.copy()
        t.iloc[1] = t.iloc[0]
        return t
    tamper("YIELD_EFFECTS duplicated key and missing step", "YIELD_EFFECTS", dup_yield)
    tamper("YIELD_EFFECTS step label", "YIELD_EFFECTS", lambda t: first(t, "step", "wrong label"))
    tamper("YIELD_EFFECTS fractional step_order", "YIELD_EFFECTS", lambda t: t.assign(step_order=t.step_order.astype(float).where(t.index != 0, 1.5)))
    tamper("META implementation choices replaced", "META", lambda m: dict(m, implementation_choices=["wrong"] * 9))
    tamper("META implementation choices reordered", "META", lambda m: dict(m, implementation_choices=m["implementation_choices"][::-1]))

    def frac(t):
        t = t.copy()
        t["N_orig"] = t.N_orig.astype(float)
        t.loc[t.index[t.N_orig.gt(0)][0], "N_orig"] += 1e-9
        return t
    tamper("CELL_COUNTS non-integer count (+1e-9)", "CELL_COUNTS", frac)
    tamper("DESIGNS negative count", "DESIGNS", lambda t: first(t, "n_no_activity", -1))
    tamper("RAW flag not boolean", "RAW", lambda t: t.assign(target_null_020=t.target_null_020.astype(object).where(t.index != 0, "maybe")))
    tamper("CRITERIA extra column", "CRITERIA", lambda t: t.assign(extra="x"))
    # provenance gate on a fixture root (symbolic links to the real files; the real files are never touched)
    nf0 = json.loads(NOTE_FREEZE.read_text())
    af0 = json.loads((ROOT / A2_FREEZE_REL).read_text())
    fs = (sha(NOTE_FREEZE), sha(ROOT / A2_FREEZE_REL))
    ok("provenance on the real files: every check matched", provenance(nf0, af0, *fs, root=ROOT) == [], provenance(nf0, af0, *fs, root=ROOT))
    with tempfile.TemporaryDirectory() as fx:
        rels = sorted(INPUTS17 | CODE9 | {NOTE_REL, A2_REL, A2_FREEZE_REL, PARENT_REL, RULES_REL, "docs/MDI_PILOT_Q4_NOTE_FREEZE.json"})
        for rel in rels:
            (Path(fx) / rel).parent.mkdir(parents=True, exist_ok=True)
            (Path(fx) / rel).symlink_to(ROOT / rel)
        ok("provenance on the fixture of links: every check matched", provenance(nf0, af0, *fs, root=fx) == [])

        def altered(rel):
            f = Path(fx) / rel
            data_ = f.read_bytes()
            f.unlink()
            f.write_bytes(data_ + b"\n# altered\n")
        altered("python/sharpbl/p2d.py")
        pr = provenance(nf0, af0, *fs, root=fx)
        ok("a reused code file altered -> refused by its check only", pr == ["reused code (9): exact set and current hashes"], pr)
        altered(NOTE_REL)
        pr = provenance(nf0, af0, *fs, root=fx)
        ok("the note text altered -> refused", "note text" in pr, pr)
        nf1 = json.loads(json.dumps(nf0))
        nf1["reused_code_sha256"].pop("python/sharpbl/p2d.py")
        ok("a reused code entry missing in the receipt -> refused", "reused code (9): exact set and current hashes" in provenance(nf1, af0, *fs, root=ROOT))
        ok("receipt file SHA different from the pin -> refused", provenance(nf0, af0, "0" * 64, fs[1], root=ROOT) == ["note receipt pinned"])
        g = globals()
        called = []
        saved = (g["GATE_ROOT"], g["real_inputs"], g["compute"])
        g["GATE_ROOT"] = Path(fx)
        g["real_inputs"] = lambda *a_, **k_: called.append("inputs")
        g["compute"] = lambda *a_, **k_: called.append("compute")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                got = check(write=False)
        finally:
            g["GATE_ROOT"], g["real_inputs"], g["compute"] = saved
        ok("check() on the real path with an altered fixture: refused before reading outputs, importing or computing",
           got is False and not called)
    # failures: a realisation not computable for MF must be recounted on the expanded grid
    real_rec = Q.mdi_records

    def failing(I_, design, th, r, variant):
        if design == "MF" and variant == "ref" and r == 1:
            return None, dict(n_domain=0, status="empty_yield_stratum")
        return real_rec(I_, design, th, r, variant)
    Q.mdi_records = failing
    try:
        rawf, desf, _ = Q.compute(I, n_real=2, log=lambda *a: None)
    finally:
        Q.mdi_records = real_rec
    global records
    own_rec = records

    def own_failing(X, design, th, r, variant):
        if design == "MF" and variant == "ref" and r == 1:
            return None, dict(n_domain=0, status="empty_yield_stratum")
        return own_rec(X, design, th, r, variant)
    smf, ncf = Q.summarise(rawf, 2)
    of = dict(outputs, RAW=rawf, SUMMARY=smf, NOT_COMPUTABLE=ncf, DESIGNS=desf,
              CRITERIA=pd.concat([Q.criteria(rawf, "main"), Q.criteria(rawf, "sens100")], ignore_index=True))
    records = own_failing
    try:
        good = quiet(of)
    finally:
        records = own_rec
    ok("failed realisation (MF ref, r = 1): failures expanded, n_fail, NOT_COMPUTABLE and no classification recounted", good)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
