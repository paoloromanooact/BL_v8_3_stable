"""MDI pilot, prospective note Q4: expected precision of T3 with an MDI 1996-2010 catalogue (frozen note).

Implements docs/MDI_PILOT_Q4_NOTE.md (frozen, receipt docs/MDI_PILOT_Q4_NOTE_FREEZE.json) with amendment A2
(docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md, receipt ..._A2_FREEZE.json). Analytic WLS variance of the T3 slope,
conditional on 20 random realisations of the design (inclusion by yield, yield draws, flux donors).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_q4_prospective.py --selftest  # synthetic checks + note §6 proofs 1-2
    OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_q4_prospective.py --run       # single run (after code review, clean tree)

--selftest writes nothing under results/. It runs the synthetic checks of note §6.3, the E0 reproduction (§6.1), the
deterministic yield reproduction (§6.2), the preparatory-count consistency and a synthetic end-to-end compute(); it
computes no precision on MDI designs. --run repeats all of them and stops on the first failure (technical stop).

No MDI tilt column is read: L1/L2/Q2 files are read with explicit column whitelists (COLS_*), checked by the selftest.

Implementation choices kept apart from the frozen rules: IMPLEMENTATION_CHOICES (nine items, also in META.json).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_dist

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import diag_t5_oracle as D, p2d  # noqa: E402


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PA = _load("prospective_phase_a", "scripts/prospective_phase_a.py")
PC = _load("mdi_q4_prep_counts", "scripts/mdi_q4_prep_counts.py")     # also loads mdi_synoptic_adapter as PC.A
PX = PA.PX                                                                # t5_proxy_sensitivity (ramp)

NOTE = ROOT / "docs/MDI_PILOT_Q4_NOTE.md"
NOTE_FREEZE = ROOT / "docs/MDI_PILOT_Q4_NOTE_FREEZE.json"
A2 = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md"
A2_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2_FREEZE.json"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
L1 = ROOT / "results/MDI_PILOT_L1/L1_RECORDS.csv"
L2 = ROOT / "results/MDI_PILOT_L2/L2_RECORDS.csv"
AUDIT = ROOT / "results/MDI_SYNOPTIC_AUDIT/FILES.csv"
AN1 = ROOT / "results/MDI_PILOT_ANALYSIS_L1/Q1_YIELD_PROJECTED.csv"
AN2 = ROOT / "results/MDI_PILOT_ANALYSIS_L2"
PHASE_A_RAW = ROOT / "results/PROSPECTIVE_PHASE_A/RAW.csv.gz"
PREP_META = ROOT / "results/MDI_Q4_PREP_COUNTS/META.json"
OUT = ROOT / "results/MDI_Q4_PROSPECTIVE"

# column whitelists: no tilt column (note §6.3, §10)
COLS_L1 = ["noaa", "day", "N", "N_ephemeris", "maps", "status", "sens100_status", "main_flux_pos_mx",
           "main_flux_neg_mx", "sens100_flux_pos_mx", "sens100_flux_neg_mx"]
COLS_L2 = ["rule", "noaa", "day", "image", "status", "sens100_status"]
COLS_Q2P = ["flux_ratio"]
COLS_Q2S = ["group", "median_d_gamma"]
COLS_AUDIT = ["CAR_ROT"]
FORBIDDEN = ("tilt", "d_ax", "d_raw", "d_dir", "t1_deg", "t2_deg", "lat_pos", "lat_neg", "lon_pos", "lon_neg",
             "leading", "sep_deg", "lat_bar")

KEYS = ["act_class", "hemisphere", "area_class", "cohort"]
THR = ("main", "sens100")
SEED0 = 35_200_000
N_REAL = 20
K_COMPONENTS = 5
SIG_INT = (15.0, 25.0, 30.0)
SIG_M = (0.0, 2.0, 10.0)
SD_X = 7.5
REF_SIG = ((15.0, 2.0), (30.0, 10.0))
# noise rows: phase A NOISE (forms 1, 2, 7 x scales) then scenarios 3 and 4 x scales
NOISE = tuple(PA.NOISE) + tuple((f, s, x) for f, s in (("ar1_09_km08", 3), ("ar1_05_kp06", 4)) for x in PA.SCALES)
MAIN_FORMS = ((1, 1.0), (2, 1.0), (7, 1.0))
N_NN = 5
END_DATE, CR_H = PC.END_DATE, PC.CR_H
GAP = PC.GAP
A_LO_E0, A_HI_E0 = 0.5020189558504007, 2.7602501179328134
E0_TARGET = -1.602647454341313
D_GAMMA_NOTE = {"main": (-0.53, -0.79, -1.19), "sens100": (-0.58, -1.29, -1.34)}
POOLS = ([("cohort", (c,)) for c in ("M1", "U")]
         + [("cohort_act", (c, a)) for c in ("M1", "U") for a in (1, 2, 3)]
         + [("cohort_area", (c, a)) for c in ("M1", "U") for a in (1, 2, 3)])
POOL_SETS = {"cohort": range(0, 2), "cohort_act": range(2, 8), "cohort_area": range(8, 14)}
AVAIL = (0.8, 0.6)
W_SCALES = (0.5, 2.0)
PSD_TOL = 1e-10
MODELS_ALONE, MODELS_COMB = ("a",), ("a", "bJ", "bA")
CRIT = dict(useful=0.7, useful_robust=0.8, marginal=0.9, mf=1.1, other_cycle=1.0, cyc23_min=50)


class TechnicalError(Exception):
    pass


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def uniforms(r, k, n):
    """Note §3.6: generator SEED0 + 1000 k + r, vector in the fixed order of its list."""
    if not (0 <= k < K_COMPONENTS and 0 <= r < N_REAL):
        raise TechnicalError(f"random component {k} / realisation {r} outside the frozen zone")
    return np.random.default_rng(SEED0 + 1000 * k + r).random(n)


def seeds_ok():
    seeds = [SEED0 + 1000 * k + r for k in range(K_COMPONENTS) for r in range(N_REAL)]
    clash = [s for s in seeds for lo, hi in PA.USED_RANGES if lo <= s < hi]
    return not clash and min(seeds) == 35_200_000 and max(seeds) == 35_204_019


# ---------------------------------------------------------------- inputs

def read_whitelisted(path, cols, **kw):
    if any(f in c for c in cols for f in FORBIDDEN):
        raise TechnicalError(f"forbidden column requested from {path}")
    return pd.read_csv(path, usecols=cols, **kw)


def yield_pools_mf(units, ok_col):
    """Note §3.3: per pool, ratio estimate with original weights on admissible units, Kish n_eff, r_eff."""
    out = []
    for kind, key in POOLS:
        m = units.cohort == key[0]
        if kind == "cohort_act":
            m &= units.act_class == key[1]
        elif kind == "cohort_area":
            m &= units.area_class == key[1]
        g = units[m]
        w = g.w.to_numpy(float)
        if len(g) == 0:
            out.append(dict(pool=kind, key="|".join(map(str, key)), n=0, ok=0, p_hat=np.nan, n_eff=0.0, r_eff=np.nan))
            continue
        p = float((w * g[ok_col]).sum() / w.sum())
        ne = float(w.sum() ** 2 / (w ** 2).sum())
        out.append(dict(pool=kind, key="|".join(map(str, key)), n=len(g), ok=int(g[ok_col].sum()), p_hat=p, n_eff=ne,
                        r_eff=p * ne))
    return pd.DataFrame(out)


def pool_index(pop, kind):
    """Index (0-13, POOLS order) of the pool of every population group for a pool reading."""
    idx = np.full(len(pop), -1)
    for j in POOL_SETS[kind]:
        _, key = POOLS[j]
        m = (pop.cohort == key[0]).to_numpy()
        if kind == "cohort_act":
            m &= (pop.act_class == key[1]).to_numpy()
        elif kind == "cohort_area":
            m &= (pop.area_class == key[1]).to_numpy()
        idx[m] = j
    return idx


def nn_tables(pop, donors):
    """L-NN (note §3.5, A2): for every population row, the 5 donors of its cell nearest in |lat| (ties: distance, then
    (noaa, day) order) as indices into donors; and the cell's donor list in (noaa, day) order (no-latitude sensitivity).
    Rows of cells with fewer than 5 donors get -1."""
    nn = np.full((len(pop), N_NN), -1)
    dist = np.full(len(pop), np.nan)
    cell_lists = {c: np.flatnonzero(donors.cell_idx.to_numpy() == c) for c in range(36)}
    alat_d = donors.alat.to_numpy()
    for c, ix in cell_lists.items():
        rows = np.flatnonzero(pop.cell_idx.to_numpy() == c)
        if len(ix) < N_NN:
            continue
        for g in rows:
            dl = np.abs(alat_d[ix] - abs(pop.lat.iat[g]))
            order = np.lexsort((np.arange(len(ix)), dl))[:N_NN]          # donors already in (noaa, day) order
            nn[g] = ix[order]
            dist[g] = dl[order].max()
    return nn, dist, cell_lists


def build_population(pop, cells, silso, missing_maps):
    pop = pop.copy()
    pop["t"] = pd.to_datetime(pop.t_dpd)
    key = {tuple(r): i for i, r in enumerate(cells[KEYS].itertuples(index=False, name=None))}
    pop["cell_idx"] = [key[tuple(r)] for r in pop[KEYS].itertuples(index=False, name=None)]
    rot = [PC.A.group_rotation(r.t_dpd, r.lon, r.lcm) for r in pop.itertuples()]
    pop["N_rot"] = [x[0] for x in rot]
    pop["N_amb"] = [x[0] != x[2] for x in rot]
    pop["map_missing"] = [bool(set(PC.required_maps(x[1])) & set(missing_maps)) for x in rot]
    pop["CR"] = [PC.cr_of_time(x) for x in pop.t]
    st = PA.cr_start(pop.CR.to_numpy())
    pop["cyc"] = [PA.cycle_of_time(s)[0] for s in st]
    pop["t_years"] = [PA.years(s) for s in st]
    pop["sinlat"] = np.sin(np.radians(np.abs(pop.lat.to_numpy(float))))
    ym = pop.t.dt.strftime("%Y-%m")
    tab = silso["monthly"]
    pop["A_silso"] = [float(tab.at[m, h]) if m in tab.index else np.nan for m, h in zip(ym, pop.hemisphere)]
    pop["year"] = pop.t.dt.year
    f1 = pop.t.dt.normalize() <= END_DATE
    f2 = pop.CR < CR_H
    gap = (pop.t >= GAP[0]) & (pop.t < GAP[1])
    pop["in_MS"] = f1 & f2 & ~pop.map_missing & ~pop.N_amb
    pop["in_MF"] = f1 & f2 & ~gap
    pop["f1"], pop["f2"], pop["gap"] = f1, f2, gap
    return pop


def load_inputs(H=None):
    """All Q4 inputs (real data). H: optional preloaded (R0) to avoid reloading the P1 catalogue."""
    meta = json.loads((SEL / "META.json").read_text())
    pop = pd.read_csv(SEL / "POPULATION.csv", dtype={"noaa": str})
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str})
    cells = pd.read_csv(SEL / "CELLS.csv")
    l1 = read_whitelisted(L1, COLS_L1, dtype={"noaa": str, "maps": str})
    l2 = read_whitelisted(L2, COLS_L2, dtype={"noaa": str})
    q2p = {t: read_whitelisted(AN2 / f"Q2_PAIRS_A1_{t}.csv", COLS_Q2P).flux_ratio.to_numpy(float) for t in THR}
    q2s = {t: read_whitelisted(AN2 / f"Q2_SUMMARY_A1_{t}.csv", COLS_Q2S) for t in THR}
    inv = set(read_whitelisted(AUDIT, COLS_AUDIT).CAR_ROT.astype(int))
    missing_maps = sorted(c for c in range(min(inv), max(inv) + 1) if c not in inv)
    if H is None:
        S, silso = PA.load_inputs()
        H = PA.e0_records(S)
    else:
        silso = PA.run_p2.load_silso()
    return assemble(meta, pop, samp, cells, l1, l2, q2p, q2s, missing_maps, silso, H)


def assemble(meta, pop, samp, cells, l1, l2, q2p, q2s, missing_maps, silso, H):
    pop = build_population(pop, cells, silso, missing_maps)
    I = dict(meta=meta, cells=cells, missing_maps=missing_maps, H=H.reset_index(drop=True), rho_q=q2p)
    # MS yields per cell (note §3.2): L1 units minus units with missing required maps
    s = samp.merge(l1[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left", validate="one_to_one")
    if s.status.isna().any():
        raise TechnicalError("sampled group without a level-1 record")
    s = s.merge(pop[["noaa", "day", "cell_idx", "map_missing", "lat", "area"]], on=["noaa", "day"], how="left",
                suffixes=("", "_pop"), validate="one_to_one")
    s["ok_main"], s["ok_sens100"] = s.status == "ok", s.sens100_status == "ok"
    if (s.map_missing & (s.ok_main | s.ok_sens100)).any():
        raise TechnicalError("a successful L1 unit has a missing required map")
    I["ms_counts_all"] = {t: (np.bincount(s.cell_idx, minlength=36), np.bincount(s.cell_idx, weights=s[f"ok_{t}"],
                                                                                  minlength=36)) for t in THR}
    keep = s[~s.map_missing]
    I["ms_counts"] = {t: (np.bincount(keep.cell_idx, minlength=36), np.bincount(keep.cell_idx, weights=keep[f"ok_{t}"],
                                                                               minlength=36)) for t in THR}
    I["ms_removed"] = int(s.map_missing.sum())
    # MF units (note §3.3): level 2, rule A1, image A, original weights, admissible units only
    a = l2[(l2.rule == "A1") & (l2.image == "A")]
    u = samp[samp.level2].merge(a[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left",
                                validate="one_to_one")
    if u.status.isna().any() or len(u) != int(samp.level2.sum()):
        raise TechnicalError("level-2 unit without an A1 image-A record")
    u = u.merge(cells[KEYS + ["N", "n2"]], on=KEYS, how="left")
    u["w"] = u.N / u.n2
    if not np.allclose(u.w, u.w2, rtol=1e-12, atol=0):
        raise TechnicalError("w2 differs from N/n2")
    t = pd.to_datetime(u.t_dpd)
    u["gap"] = (t >= GAP[0]) & (t < GAP[1])
    u["ok_main"], u["ok_sens100"] = u.status == "ok", u.sens100_status == "ok"
    I["mf_units_all"] = u
    I["mf_units"] = u[~u.gap].reset_index(drop=True)
    I["mf_pools"] = {t: yield_pools_mf(I["mf_units"], f"ok_{t}") for t in THR}
    I["mf_missing_years"] = sorted(set(range(pop[pop.in_MF].year.min(), pop[pop.in_MF].year.max() + 1))
                                   - set(pd.to_datetime(samp[samp.level2].t_dpd).dt.year))
    # donors (note §3.5): L1 successes per threshold, rho = (|F+| + |F-|) / DPD area, (noaa, day) order
    s = s.merge(l1[["noaa", "day"] + COLS_L1[7:]], on=["noaa", "day"], how="left", validate="one_to_one")
    I["donors"] = {}
    for th in THR:
        d = s[s[f"ok_{th}"]].sort_values(["noaa", "day"]).reset_index(drop=True)
        rho = (d[f"{th}_flux_pos_mx"].abs() + d[f"{th}_flux_neg_mx"].abs()) / d.area.astype(float)
        I["donors"][th] = pd.DataFrame(dict(noaa=d.noaa, day=d.day, cell_idx=d.cell_idx, alat=d.lat.abs(), rho=rho))
        if not np.isfinite(rho).all() or (rho <= 0).any():
            raise TechnicalError(f"non-positive or non-finite donor flux ratio ({th})")
    I["nn"] = {th: nn_tables(pop, I["donors"][th]) for th in THR}
    # product-difference scenario (note §5)
    I["d_gamma"] = {}
    for th in THR:
        q = q2s[th].set_index("group").median_d_gamma
        d = tuple(float(q.at[f"activity {k}"]) for k in (1, 2, 3))
        if tuple(round(v, 2) for v in d) != D_GAMMA_NOTE[th]:
            raise TechnicalError(f"Q2 d_gamma by activity {d} differ from the note {D_GAMMA_NOTE[th]}")
        I["d_gamma"][th] = d
    I["pop"] = pop
    I["samp"] = samp
    return I


# ---------------------------------------------------------------- designs

def ms_probs(I, th, V1):
    n, r = I["ms_counts"][th]
    if (n == 0).any():
        return None
    p_cell = beta_dist.ppf(V1, r + 0.5, n - r + 0.5)
    return p_cell[I["pop"].cell_idx.to_numpy()]


def mf_probs(I, th, V2, kind="cohort", avail=1.0):
    pools = I["mf_pools"][th]
    idx = pool_index(I["pop"], kind)
    js = list(POOL_SETS[kind])
    if (pools.n.iloc[js] == 0).any() or (idx[I["pop"].in_MF.to_numpy()] < 0).any():
        return None
    a_ = pools.r_eff.to_numpy() + 0.5
    b_ = pools.n_eff.to_numpy() - pools.r_eff.to_numpy() + 0.5
    p_pool = np.full(len(POOLS), np.nan)
    p_pool[js] = beta_dist.ppf(V2[js], a_[js], b_[js])
    p = p_pool[np.where(idx < 0, 0, idx)]
    if avail != 1.0:
        p = p * np.where(I["pop"].year.isin(I["mf_missing_years"]).to_numpy(), avail, 1.0)
    return p


def fluxes(I, th, Dg, nolat=False):
    """Phi per population row (NaN where the cell has fewer than 5 donors)."""
    pop, don = I["pop"], I["donors"][th]
    nn, _, lists = I["nn"][th]
    rho_d = don.rho.to_numpy()
    if nolat:
        choice = np.full(len(pop), -1)
        for c, ix in lists.items():
            rows = np.flatnonzero(pop.cell_idx.to_numpy() == c)
            if len(ix):
                choice[rows] = ix[np.floor(len(ix) * Dg[rows]).astype(int)]
    else:
        pick = np.floor(N_NN * Dg).astype(int)
        choice = np.where(nn[:, 0] >= 0, nn[np.arange(len(pop)), pick], -1)
    rho = np.where(choice >= 0, rho_d[np.maximum(choice, 0)], np.nan)
    return pop.area.to_numpy(float) * rho


def mdi_records(I, design, th, r, variant):
    """MDI records of one realisation (note §3). Returns (R or None, info)."""
    pop = I["pop"]
    U0 = uniforms(r, 0, len(pop))
    V1 = uniforms(r, 1, 36)
    V2 = uniforms(r, 2, len(POOLS))
    Dg = uniforms(r, 3, len(pop))
    Rg = uniforms(r, 4, len(pop))
    dom = pop[f"in_{design}"].to_numpy()
    if design == "MS":
        p = ms_probs(I, th, V1)
    else:
        kind = {"mf_pool_cohort_act": "cohort_act", "mf_pool_cohort_area": "cohort_area"}.get(variant, "cohort")
        avail = {"avail_0.8": 0.8, "avail_0.6": 0.6}.get(variant, 1.0)
        p = mf_probs(I, th, V2, kind, avail)
    info = dict(n_domain=int(dom.sum()))
    if p is None:
        return None, dict(info, status="empty_yield_stratum")
    phi = fluxes(I, th, Dg, nolat=(variant == "flux_nolat"))
    if variant == "flux_mf_rho" and design == "MF":
        q = I["rho_q"][th]
        phi = phi / q[np.floor(len(q) * Rg).astype(int)]
    inc = dom & (U0 < p)
    if np.isnan(phi[inc]).any():
        return None, dict(info, status="flux_cell_lt5_donors")
    act = pop.A_main.to_numpy(float) if variant == "act_amain" else pop.A_silso.to_numpy(float)
    keep = inc & np.isfinite(act)
    g = pop[keep]
    R = pd.DataFrame(dict(CR=g.CR.to_numpy(int), hem=g.hemisphere.to_numpy(), lat=g.lat.to_numpy(float),
                          sinlat=g.sinlat.to_numpy(float), phi=phi[keep], cyc=g.cyc.to_numpy(int), A=act[keep],
                          M=1, t_years=g.t_years.to_numpy(float), act_class=g.act_class.to_numpy(int),
                          row=np.flatnonzero(keep)))
    nn_dist = I["nn"][th][1]
    info.update(status="ok", n_included=int(inc.sum()), n_excluded_yield=int(dom.sum() - inc.sum()),
                n_no_activity=int((inc & ~np.isfinite(act)).sum()),
                expected_yield=float(np.mean(p[dom])),
                lat_dist_median=float(np.nanmedian(nn_dist[dom])), lat_dist_p90=float(np.nanquantile(nn_dist[dom], 0.9)))
    return R, info


# ---------------------------------------------------------------- matrix adapter, target, variance (note §4, §5)

def rank_w(cols, sw):
    if not cols:
        return 0
    X = np.column_stack(cols) * sw[:, None]
    nrm = np.linalg.norm(X, axis=0)
    X = X[:, nrm > 0] / nrm[nrm > 0]
    return int(np.linalg.matrix_rank(X)) if X.shape[1] else 0


def design_columns(R, model, combined):
    s, M, hem, cyc = R.sinlat.to_numpy(float), R.M.to_numpy(float), R.hem.to_numpy(), R.cyc.to_numpy()
    a1 = R.A.to_numpy(float) - 1.0
    nuis = [(f"I{c}{h}", ((cyc == c) & (hem == h)) * s) for c in sorted(set(cyc)) for h in ("N", "S")
            if ((cyc == c) & (hem == h)).any()]
    if combined:
        nuis += [(f"M24{h}", M * ((cyc == 24) & (hem == h)) * s) for h in ("N", "S")]
        if model == "bJ":
            nuis += [("M_x3", M * a1 * s)]
        elif model == "bA":
            nuis += [("M_N", M * (hem == "N")), ("M_S", M * (hem == "S")), ("M_A", M * a1)]
    return nuis, ("x3", a1 * s)


def reduce_columns(nuis, x3, w):
    """Incremental rank (note §4): a nuisance column enters only if it raises the rank of the weighted matrix."""
    sw = np.sqrt(w)
    used, dropped, cols, rk = [], [], [], 0
    for name, v in nuis:
        r1 = rank_w(cols + [v], sw)
        if r1 > rk:
            used.append(name)
            cols.append(v)
            rk = r1
        else:
            dropped.append(name)
    if rank_w(cols + [x3[1]], sw) != rk + 1:
        return None, used, dropped
    return np.column_stack(cols + [x3[1]]), used + ["x3"], dropped


def cells_of(R):
    codes, uniq = pd.factorize(pd.MultiIndex.from_arrays([R.CR.to_numpy(), R.hem.to_numpy()]))
    cell_cr = np.array([c for c, _ in uniq], int)
    cell_h = np.array([h for _, h in uniq])
    return codes, cell_cr, cell_h


_PSD = {}


def k_matrix(cell_cr, cell_h, scen, cross_zero):
    t = cell_cr - cell_cr.min()
    h = (cell_h == "S").astype(int)
    K = D.k_true(t, h, scen)
    if cross_zero:
        inst = cell_cr >= CR_H
        K = K * (inst[:, None] == inst[None, :])
    key = (cell_cr.tobytes(), cell_h.tobytes(), scen, cross_zero)
    if key not in _PSD:
        if not np.allclose(K, K.T, rtol=0, atol=0):
            raise TechnicalError("temporal covariance not symmetric")
        ev = np.linalg.eigvalsh(K)
        _PSD[key] = bool(ev.min() >= -PSD_TOL * ev.max())
    if not _PSD[key]:
        raise TechnicalError(f"temporal covariance not PSD (scenario {scen}, cross_zero {cross_zero})")
    return K


def analyse(R, models, combined, cross_variants=(False,), d_prod=None, u=None):
    """Per model: reduced columns, WLS row, targets (E0 and design quantiles), variance pieces, bias bases.
    A design without records gives status 'empty_design' for every model, before cells, quantiles or covariances."""
    if len(R) == 0:
        return {m: dict(status="empty_design", columns="", dropped="", n_records=0, n_mdi=0, n_cells=0, n_cr=0) for m in models}
    w = R.phi.to_numpy(float)
    codes, cell_cr, cell_h = cells_of(R)
    A = R.A.to_numpy(float)
    abar = pd.Series(A).groupby(codes).transform("mean").to_numpy()
    s = R.sinlat.to_numpy(float)
    M = R.M.to_numpy(float)
    qd = tuple(float(v) for v in np.quantile(abar, [PX.Q_LO, PX.Q_HI]))
    out = {}
    Ks = {(sc, cz): k_matrix(cell_cr, cell_h, sc, cz) for sc in sorted({n[1] for n in NOISE}) for cz in cross_variants}
    for model in models:
        nuis, x3 = design_columns(R, model, combined)
        X, names, dropped = reduce_columns(nuis, x3, w)
        base = dict(columns="|".join(names), dropped="|".join(dropped), n_records=len(R), n_mdi=int(M.sum()),
                    n_cells=len(cell_cr), n_cr=len(set(cell_cr)))
        if X is None:
            out[model] = dict(base, status="x3_not_identifiable")
            continue
        g = p2d.wls_row(X, w, names.index("x3"))
        b = np.bincount(codes, weights=g, minlength=len(cell_cr))
        res = dict(base, status="ok", a2=float(np.sum(g ** 2)), a2_mdi=float(np.sum(g ** 2 * M)))
        for dmax, tag in ((0.20, "020"), (0.10, "010")):
            res[f"target_{tag}"] = float(g @ (-PX.ramp(abar, A_LO_E0, A_HI_E0, dmax) * PA.GAMMA0 * s))
            res[f"target_qd_{tag}"] = float(g @ (-PX.ramp(abar, qd[0], qd[1], dmax) * PA.GAMMA0 * s))
        res["A_lo_design"], res["A_hi_design"] = qd
        res["bKb"] = {(sc, cz): float(b @ K @ b) for (sc, cz), K in Ks.items()}
        if combined:
            dz = dict(M=M, a1=A - 1.0, t=R.t_years.to_numpy(float), s=s, abar=abar)
            fams = {"a": ("A", "J"), "bA": ("A",), "bJ": ("J",)}[model]
            res["bias"] = {f: PA.bias_bases(dz, g, f) for f in fams}
        if d_prod is not None:
            k = R.act_class.to_numpy()
            dv = np.where(M == 1, np.array([np.nan, *d_prod])[np.where(M == 1, k, 0)], 0.0)
            res["m_prod"] = float(g @ dv)
        out[model] = res
    return out


TARGETS = ("020", "010", "qd_020", "qd_010")
KEEP = ("columns", "dropped", "n_records", "n_mdi", "n_cells", "n_cr", "target_020", "target_010", "target_qd_020", "target_qd_010",
        "A_lo_design", "A_hi_design")


def grid(noise_set, sig_set):
    """The configurations (sigma_int, sigma_m, noise) of one design row, in the order of noise_rows."""
    return [dict(sigma_int=si, sigma_m=sm, noise=n, form=NOISE[n][0], scen=NOISE[n][1], x_scale=NOISE[n][2])
            for si, sm in sig_set for n in noise_set]


def noise_rows(res, noise_set, sig_set, cross_zero=False, u=None):
    """Expand one analysed model into rows (sigma_int, sigma_m, noise)."""
    rows = []
    for si, sm in sig_set:
        for n in noise_set:
            form, scen, xs = NOISE[n]
            temporal = (SD_X * xs) ** 2 * res["bKb"][(scen, cross_zero)]
            var = si ** 2 * res["a2"] + sm ** 2 * res["a2_mdi"] + temporal
            if not (np.isfinite(var) and var > 0):
                raise TechnicalError("variance not finite/positive")
            se = float(np.sqrt(var))
            row = dict(sigma_int=si, sigma_m=sm, noise=n, form=form, scen=scen, x_scale=xs, se=se,
                       h_gamma0=PA.Z * se / PA.GAMMA0, var_temporal_share=temporal / var)
            null = {tag: not (np.isfinite(res[f"target_{tag}"]) and res[f"target_{tag}"] != 0) for tag in TARGETS}
            for tag in TARGETS:
                tg = res[f"target_{tag}"]
                row[f"target_null_{tag}"] = null[tag]          # zero ramp: ratios to the target are not defined (NaN)
                row[f"se_over_target_{tag}"] = np.nan if null[tag] else se / abs(tg)
                row[f"recognition_{tag}"] = float(PA.freqs(tg, 0.0, se)["sup"]) if np.isfinite(tg) else np.nan
            if "m_prod" in res:
                row["m_prod"] = res["m_prod"]
                for tag in TARGETS:
                    row[f"m_prod_over_target_{tag}"] = np.nan if null[tag] else res["m_prod"] / abs(res[f"target_{tag}"])
            if "bias" in res and u is not None:
                for fam, B in res["bias"].items():
                    un = PA.family_units(fam, u)
                    row[f"B1_{fam}"] = B[1]
                    for C in PA.C_LIMITS:
                        for tag in TARGETS:
                            wc = PA.worst_case(res[f"target_{tag}"], B[1], un[1], C, se)
                            row[f"tol_units_{fam}_{tag}"] = wc["tolerance_units"]      # same for both C
                            row[f"sup_scen_worst_{fam}_C{C}_{tag}"] = wc["sup_scen_worst"]
                        row[f"sup_null_worst_{fam}_C{C}"] = wc["sup_null_worst"]      # does not depend on the target
            rows.append(row)
    return rows


# ---------------------------------------------------------------- compute

FULL_NOISE = tuple(range(len(NOISE)))
SENS_NOISE = tuple(i for i, (f, sc, xs) in enumerate(NOISE) if (sc, xs) in MAIN_FORMS)
FULL_SIG = tuple((si, sm) for si in SIG_INT for sm in SIG_M)
MDI_VARIANTS = {"ref": ("MS", "MF"), "mf_pool_cohort_act": ("MF",), "mf_pool_cohort_area": ("MF",),
                "avail_0.8": ("MF",), "avail_0.6": ("MF",), "flux_nolat": ("MS", "MF"), "flux_mf_rho": ("MF",),
                "act_amain": ("MS", "MF")}
COMB_ONLY = ("w_x0.5", "w_x2", "w_norm", "cov_zero_cross")


def h_reference(I):
    H = I["H"][["CR", "hem", "lat", "sinlat", "phi", "cyc", "A", "M", "t_years"]].copy()
    H["act_class"] = 0
    res = analyse(H, ("a", "bJ", "bA"), combined=True, cross_variants=(False,))
    sbar = float(np.sum(H.phi * H.sinlat) / np.sum(H.phi))
    u = dict(d3=abs(res["a"]["target_020"]), sbar=sbar)
    return H, res, u


def compute(I, n_real=N_REAL, log=print):
    H, hres, u = h_reference(I)
    rows, designs = [], []
    common_cols = ["CR", "hem", "lat", "sinlat", "phi", "cyc", "A", "M", "t_years", "act_class"]
    # H rows (identical in every realisation)
    for model in ("a",):
        for row in noise_rows(hres[model], FULL_NOISE, tuple((si, 0.0) for si in SIG_INT)):
            rows.append(dict(design="H", threshold="-", variant="ref", r=-1, model=model, status="ok",
                             **{k: hres[model][k] for k in KEEP},
                             **row))
    for r in range(n_real):
        for th in THR:
            for variant, dsg in MDI_VARIANTS.items():
                for design in dsg:
                    Rm, info = mdi_records(I, design, th, r, variant)
                    designs.append(dict(r=r, threshold=th, variant=variant, design=design, **info))
                    sig = FULL_SIG if variant == "ref" else REF_SIG
                    nset = FULL_NOISE if variant == "ref" else SENS_NOISE
                    dprod = I["d_gamma"][th] if design == "MS" else None
                    entries = []                    # (design name, model, analysed model or None, status, variant, cross zero)
                    # MDI alone
                    if Rm is not None:
                        c23 = Rm[Rm.cyc == 23].hem.value_counts()
                        sep_ok = all(c23.get(h, 0) >= CRIT["cyc23_min"] for h in ("N", "S"))
                        for model, rs in analyse(Rm[common_cols], MODELS_ALONE, combined=False, d_prod=dprod).items():
                            st = rs["status"] if rs["status"] != "ok" or sep_ok else "not_separate_measure"
                            entries.append((design, model, rs, st, variant, False))
                    else:
                        entries += [(design, model, None, info["status"], variant, False) for model in MODELS_ALONE]
                    # combined: every expected variant name, also when the MDI design is not computable
                    if variant != "act_amain":
                        names = ["ref", "w_x0.5", "w_x2", "w_norm"] if variant == "ref" else [variant]
                        if Rm is None:
                            for vname in names + (["cov_zero_cross"] if variant == "ref" else []):
                                entries += [(f"{design}+H", model, None, info["status"], vname, vname == "cov_zero_cross")
                                            for model in MODELS_COMB]
                        else:
                            RC = pd.concat([H[common_cols], Rm[common_cols]], ignore_index=True)
                            for vname in names:
                                x = RC.copy()
                                if vname.startswith("w_x"):
                                    x.loc[x.M == 1, "phi"] *= float(vname[3:])
                                elif vname == "w_norm":
                                    for m_ in (0, 1):
                                        x.loc[x.M == m_, "phi"] /= x.loc[x.M == m_, "phi"].mean()
                                cz = (False, True) if vname == "ref" else (False,)
                                for model, rs in analyse(x, MODELS_COMB, combined=True, cross_variants=cz, d_prod=dprod, u=u).items():
                                    entries.append((f"{design}+H", model, rs, rs["status"], vname, False))
                                    if vname == "ref":
                                        entries.append((f"{design}+H", model, rs, rs["status"], "cov_zero_cross", True))
                    for dname, model, rs, st, vname, cz in entries:
                        sg = sig if vname == variant else REF_SIG
                        ns = nset if vname == variant else SENS_NOISE
                        base = dict(design=dname, threshold=th, variant=vname, r=r, model=model, status=st)
                        if rs is None or rs["status"] != "ok":
                            # not computable: one row per expected configuration, so that SUMMARY keeps every key
                            known = {k: rs[k] for k in KEEP if rs is not None and k in rs}
                            rows += [dict(base, **known, **gc) for gc in grid(ns, sg)]
                            continue
                        keep = {k: rs[k] for k in KEEP}
                        rows += [dict(base, **keep, **row) for row in noise_rows(rs, ns, sg, cross_zero=cz, u=u)]
        log(f"realisation {r}: {len(rows)} rows")
    raw = pd.DataFrame(rows)
    hh = raw[raw.design == "H"].set_index(["sigma_int", "noise"]).h_gamma0
    den = np.array([hh.get((si, n), np.nan) for si, n in zip(raw.sigma_int, raw.noise)], float)
    raw["h_over_hH"] = raw.h_gamma0 / den
    return raw, pd.DataFrame(designs), u


KEYCOLS = ["design", "threshold", "variant", "model", "sigma_int", "sigma_m", "noise", "form", "scen", "x_scale"]


def summarise(raw, n_real=N_REAL):
    """Median, min, max over the computable realisations of every configuration that appears in RAW (failures are
    expanded on the expected grid by compute), with n_ok and n_fail = n_real - n_ok; NOT_COMPUTABLE lists the causes."""
    mdi = raw[raw.design != "H"]
    if mdi.duplicated(KEYCOLS + ["r"]).any():
        raise TechnicalError("a configuration appears twice in the same realisation")
    keys = raw[KEYCOLS].drop_duplicates().reset_index(drop=True)
    ok = raw[raw.status == "ok"]
    vals = [c for c in ok.columns if c not in KEYCOLS + ["r", "status", "columns", "dropped"]
            and pd.api.types.is_numeric_dtype(ok[c]) and not pd.api.types.is_bool_dtype(ok[c])]
    agg = ok.groupby(KEYCOLS, dropna=False)[vals].agg(["median", "min", "max"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    flags = [c for c in ok.columns if c.startswith("target_null_")]
    agg = agg.join(ok.groupby(KEYCOLS, dropna=False)[flags].sum().astype(int).add_suffix("_n"))
    agg = agg.join(ok.groupby(KEYCOLS, dropna=False).r.nunique().rename("n_ok")).reset_index()
    out = keys.merge(agg, on=KEYCOLS, how="left")
    out["n_ok"] = out.n_ok.fillna(0).astype(int)
    out["n_fail"] = np.where(out.design == "H", 0, n_real - out.n_ok)
    fails = raw[raw.status != "ok"].groupby(["design", "threshold", "variant", "model", "status"]).r.nunique()
    return out, fails.rename("n_realisations").reset_index()


def paired_ratio(raw, num, den, variant_num="ref", variant_den="ref", th="main", sig=(15.0, 2.0), model="a"):
    """Median over realisations of h(num)/h(den) in the same realisation, per main form; n_fail counted."""
    out = {}
    for sc, xs in MAIN_FORMS:
        sel = lambda d, v: raw[(raw.status == "ok") & (raw.design == d) & (raw.variant == v) & (raw.threshold.isin([th, "-"])) &
                               (raw.model == ("a" if d == "H" else model)) & (raw.scen == sc) & (raw.x_scale == xs) &
                               (raw.sigma_int == sig[0]) & (raw.sigma_m == (0.0 if d == "H" else sig[1]))]
        a = sel(num, variant_num).set_index("r").h_gamma0
        if den == "H":
            ratio = a / float(sel("H", "ref").h_gamma0.iloc[0])
        else:
            ratio = a / sel(den, variant_den).set_index("r").h_gamma0
        nreal = raw[raw.design != "H"].r.nunique()
        ratio = ratio.dropna()
        out[sc] = dict(median=float(ratio.median()) if len(ratio) else np.nan, n_ok=int(len(ratio)),
                       n_fail=int(nreal - len(ratio)))
    return out


def criteria(raw, th="main"):
    """Note §7, fixed before the calculations: classification only if no realisation of the used rows failed."""
    rows = []

    def all_ok(rs):
        return all(v["n_fail"] == 0 for v in rs.values())

    useful = paired_ratio(raw, "MS+H", "H", th=th)
    robust = paired_ratio(raw, "MS+H", "H", th=th, sig=(30.0, 10.0))
    if not (all_ok(useful) and all_ok(robust)):
        verdict = "nessuna classificazione (realizzazioni non calcolabili)"
    elif all(v["median"] <= CRIT["useful"] for v in useful.values()) and \
            all(v["median"] <= CRIT["useful_robust"] for v in robust.values()):
        verdict = "utile come limite"
    elif all(v["median"] <= CRIT["marginal"] for v in useful.values()):
        verdict = "marginale"
    else:
        verdict = "riduzione inferiore al criterio fissato, nelle configurazioni esaminate"
    rows.append(dict(criterion="contributo MDI (MS+H vs H)", threshold=th, verdict=verdict,
                     detail=json.dumps(dict(ref=useful, robust=robust))))
    for d in ("MS", "MF"):
        x = paired_ratio(raw, d, "H", th=th)
        v = ("nessuna classificazione (realizzazioni non calcolabili)" if not all_ok(x) else
             ("misura T3 su un altro periodo/ciclo (essenzialmente il 23), con precisione prospettica almeno pari"
              if all(t["median"] <= CRIT["other_cycle"] for t in x.values()) else "precisione inferiore a H"))
        rows.append(dict(criterion=f"{d} da solo vs H", threshold=th, verdict=v, detail=json.dumps(x)))
    mf = {k: paired_ratio(raw, "MF+H", "MS+H", variant_num=k, th=th) for k in ("ref", "mf_pool_cohort_act")}
    if not all(all_ok(x) for x in mf.values()):
        v = "nessuna classificazione (realizzazioni non calcolabili)"
    elif all(t["median"] <= CRIT["mf"] for x in mf.values() for t in x.values()):
        v = "MF da considerare"
    else:
        v = "MF non considerato (perdita di resa)"
    rows.append(dict(criterion="prodotto MF+H vs MS+H", threshold=th, verdict=v, detail=json.dumps(mf)))
    for mdl in ("bJ", "bA"):
        rows.append(dict(criterion=f"accanto: modello protetto {mdl}, MS+H vs H", threshold=th, verdict="(senza criterio)",
                         detail=json.dumps(paired_ratio(raw, "MS+H", "H", th=th, model=mdl))))
    return pd.DataFrame(rows)


def cell_counts(I):
    """Note §3.1: per selection cell, original N and N after each filter, in the order of the note, and the final
    MS and MF domains; MS yield units (n, r) per threshold (§3.2). Deterministic, not per realisation."""
    pop, cells = I["pop"], I["cells"]
    ci = pop.cell_idx.to_numpy()
    cnt = lambda m: np.bincount(ci[np.asarray(m, bool)], minlength=len(cells))          # noqa: E731
    f12 = pop.f1 & pop.f2
    out = cells[KEYS].copy()
    out["N_selection"] = cells.N.to_numpy()
    out["N_orig"] = cnt(np.ones(len(pop), bool))
    out["N_f1_date"] = cnt(pop.f1)
    out["N_f2_cr"] = cnt(f12)
    out["MS_f3_maps"] = cnt(f12 & ~pop.map_missing)
    out["MS_f3_N_ambiguous"] = cnt(pop.in_MS)
    out["MF_f4_gap"] = cnt(pop.in_MF)
    out["N_MS"], out["N_MF"] = out.MS_f3_N_ambiguous, out.MF_f4_gap
    for th in THR:
        n, r = I["ms_counts"][th]
        out[f"ms_units_n_{th}"], out[f"ms_units_r_{th}"] = n.astype(int), r.astype(int)
    return out


def yield_effects(I):
    """Note §3.2, §6.2: expected yield of the design under successive changes, one change per step (no identity
    required, no Beta identity imposed). MS: published r/n -> map-missing units removed -> Q4 domain -> Beta mean.
    MF: published ratio estimate -> gap units removed -> pool p_hat on the whole population -> Q4 domain -> Beta mean."""
    pop, rows = I["pop"], []
    cells = I["cells"]
    ci = pop.cell_idx.to_numpy()
    N = cells.N.to_numpy(float)

    def add(th, design, k, step, change, value):
        rows.append(dict(threshold=th, design=design, step_order=k, step=step, change=change, value=float(value)))

    for th in THR:
        n, r = I["ms_counts"][th]
        n0, r0 = I["ms_counts_all"][th]
        dom = pop.in_MS.to_numpy()
        add(th, "MS", 1, "r/n, all L1 units, eligible population (published)", "-", (N * r0 / n0).sum() / N.sum())
        add(th, "MS", 2, "r/n, map-missing units removed, eligible population", "units", (N * r / n).sum() / N.sum())
        add(th, "MS", 3, "r/n, map-missing units removed, Q4 domain", "domain", np.mean((r / n)[ci][dom]))
        add(th, "MS", 4, "Beta mean, Q4 domain", "Beta", np.mean(((r + 0.5) / (n + 1))[ci][dom]))
        ua, uf = I["mf_units_all"], I["mf_units"]
        dm = pop.in_MF.to_numpy()
        add(th, "MF", 1, "ratio estimate, all level-2 units, eligible population (published)", "-",
            (ua.w * ua[f"ok_{th}"]).sum() / ua.w.sum())
        add(th, "MF", 2, "ratio estimate, gap units removed, eligible population", "units", (uf.w * uf[f"ok_{th}"]).sum() / uf.w.sum())
        pools = I["mf_pools"][th]
        for k, kind in enumerate(("cohort", "cohort_act", "cohort_area")):
            idx = pool_index(pop, kind)
            ph = pools.p_hat.to_numpy()[idx]
            be = ((pools.r_eff + 0.5) / (pools.n_eff + 1)).to_numpy()[idx]
            add(th, "MF", 3 + 3 * k, f"pool {kind} p_hat, eligible population", "pool", np.mean(ph))
            add(th, "MF", 4 + 3 * k, f"pool {kind} p_hat, Q4 domain", "domain", np.mean(ph[dm]))
            add(th, "MF", 5 + 3 * k, f"pool {kind} Beta mean, Q4 domain", "Beta", np.mean(be[dm]))
    return pd.DataFrame(rows)


IMPLEMENTATION_CHOICES = [
    "1. 'quantili ricalcolati sul disegno' (note §4, §6): 5-95 % numpy-linear quantiles of the cell activity replicated "
    "on the records of the T3 design itself (phase A used T5 records, which Q4 does not build); a different set from "
    "T5. Reported as columns target_qd_* with every target-dependent product, and the quantiles A_lo_design, A_hi_design.",
    "2. covariance check (note §5): min eigenvalue >= -1e-10 * max eigenvalue, cached per (cell CR, cell hemisphere, "
    "scenario, cross-zero variant); the key keeps the order of the cells.",
    "3. ratios h/h_H use H with model (a), the same sigma_int and the same noise row; H has sigma_m,HMI = 0 and does "
    "not depend on the realisation, the threshold or the MDI sensitivity.",
    "4. A_main sensitivity (MDI alone only): a declared numeric scenario. target_* keep the E0 SILSO quantiles (units "
    "differ from SILSO: not the same activity range nor the same physical slope; no direct physical comparison of "
    "the betas), target_qd_* report the design's own quantiles; not used by the criteria.",
    "5. flux donors: a target group may receive itself as donor when it is a successful L1 unit (L-NN and no-latitude "
    "sensitivity); donors are reused with replacement. This is not an independent verification of that group's flux.",
    "6. domains: MF excludes the 1998 gap but not the missing synoptic maps; MS also excludes N ambiguous (as the "
    "note); MS/MF population differences are not compensated by choosing other groups.",
    "7. one-at-a-time sensitivities are also computed for combinations the note does not require (for example MS "
    "alone with flux_nolat): a superset of §6, same rule, labelled; no new criterion and no crossing of sensitivities.",
    "null target: a zero ramp makes the ratios to the target (se_over_target, m_prod_over_target) not defined (NaN, "
    "flag target_null_*); SE, h and recognition are kept; no epsilon is added.",
    "not computable designs: failures are expanded on the expected grid of configurations, so that SUMMARY has every "
    "key with n_ok and n_fail; criteria do not classify when a used realisation failed.",
]


# ---------------------------------------------------------------- proofs on real data (note §6.1, §6.2)

def proof_e0(I, H_res=None):
    """E0 reproduction against phase A RAW (all T3 rows, noise 0-8) and against t3_var."""
    H, res, u = h_reference(I) if H_res is None else H_res
    ref = pd.read_csv(PHASE_A_RAW)
    ref = ref[(ref.ext == "E0") & (ref.test == "T3")]
    bad = []
    mp = {("A", "a"): "a", ("A", "b"): "bA", ("J", "a"): "a", ("J", "b"): "bJ"}
    for _, x in ref.iterrows():
        rs = res[mp[(x.family, x.model)]]
        form, scen, xs = NOISE[int(x.noise)]
        temporal = (SD_X * xs) ** 2 * rs["bKb"][(scen, False)]
        var = 15.0 ** 2 * rs["a2"] + temporal
        checks = dict(columns=rs["columns"] == x["columns"], dropped=rs["dropped"] == x["dropped"],
                      target=abs(rs["target_020"] - x.target_020) <= 1e-12 * abs(x.target_020),
                      target010=abs(rs["target_010"] - x.target_010) <= 1e-12 * abs(x.target_010),
                      se=abs(np.sqrt(var) - x.se) <= 1e-12 * x.se,
                      share=abs(temporal / var - x.var_temporal_share) <= 1e-12 * x.var_temporal_share)
        if not all(checks.values()):
            bad.append((x.family, x.model, int(x.noise), {k: v for k, v in checks.items() if not v}))
    ok_t = abs(res["a"]["target_020"] - E0_TARGET) <= 1e-12 * abs(E0_TARGET)
    # direct comparison with phase A t3_var
    R0 = I["H"]
    dz = PA.t3_design(R0)
    tv = []
    for mk, mine in (("a", "a"), ("bJ", "bJ"), ("bA", "bA")):
        g = dz["rows"][mk]["g"]
        for n in range(len(PA.NOISE)):
            v, tmp = PA.t3_var(dz, g, n, 1.0)
            form, scen, xs = NOISE[n]
            mv = 15.0 ** 2 * res[mine]["a2"] + (SD_X * xs) ** 2 * res[mine]["bKb"][(scen, False)]
            tv.append(abs(mv - v) <= 1e-12 * v)
    return dict(rows=len(ref), failures=bad, target_ok=ok_t, t3_var_ok=all(tv), n_t3_var=len(tv))


def proof_yields(I):
    """Deterministic reproduction (no Beta, no pool, no Q4 filter) of the published projected yields."""
    samp, cells = I["samp"], I["cells"]
    l1 = read_whitelisted(L1, COLS_L1, dtype={"noaa": str, "maps": str})
    s = samp.merge(l1[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], validate="one_to_one")
    s["ok"], s["ok100"] = s.status == "ok", s.sens100_status == "ok"
    pub = pd.read_csv(AN1)
    worst = 0.0
    n = 0
    for by in (None, "act_class", "area_class", "hemisphere", "cohort"):
        for name, g in ([("all", s)] if by is None else [(f"{by}={v}", g) for v, g in s.groupby(by)]):
            w = g.w1.to_numpy(float)
            for okc, col in (("ok", "projected_yield"), ("ok100", "projected_yield_100")):
                v = float((w * g[okc]).sum() / w.sum())
                pv = float(pub[pub.group == name][col].iloc[0])
                worst = max(worst, abs(v - pv) / abs(pv) if pv else abs(v - pv))
                n += 1
    u = I["mf_units_all"]
    pub2 = pd.read_csv(AN2 / "YIELD_A1.csv")
    pub2 = pub2[pub2.image == "A"]
    u = u.assign(activity=u.act_class, area=u.area_class, year=u.day.str[:4])
    for by in (None, "activity", "area", "hemisphere", "cohort", "year"):
        for name, g in ([("all", u)] if by is None else [(f"{by}={v}", g) for v, g in u.groupby(by)]):
            v = float((g.w * g.ok_main).sum() / g.w.sum())
            pv = float(pub2[pub2.group == name].projected_yield.iloc[0])
            worst = max(worst, abs(v - pv) / abs(pv) if pv else abs(v - pv))
            n += 1
    return dict(n=n, max_rel=worst, ok=worst <= 1e-12 and n == 46)


def proof_prep_counts(I):
    m = json.loads(PREP_META.read_text())
    pop = I["pop"]
    got = dict(MF_before_gap=int((pop.f1 & pop.f2).sum()), MS=int(pop.in_MS.sum()),
               map_missing=int(pop.map_missing.sum()), N_ambiguous=int(pop.N_amb.sum()))
    exp = dict(MF_before_gap=m["C3"]["MF"], MS=m["C3"]["MS"], map_missing=m["C2"]["population_map_missing"],
               N_ambiguous=m["C2"]["population_N_ambiguous"])
    dist = I["nn"]["main"][1][pop.in_MS.to_numpy()]
    c7 = (abs(float(np.quantile(dist, 0.9)) - m["C7"]["main"]["nn_p90_max_dlat"]) < 1e-9
          and abs(float(np.median(dist)) - m["C7"]["main"]["nn_median_max_dlat"]) < 1e-9)
    return dict(ok=(got == exp) and c7 and int(pop.in_MF.sum()) == 5062 and I["missing_maps"] == [1938, 1939, 1940]
                and I["mf_missing_years"] == [1996, 2008], got=got, expected=exp, c7=c7,
                MF=int(pop.in_MF.sum()), missing_years=I["mf_missing_years"])


# ---------------------------------------------------------------- selftest (synthetic; note §6.3)

def fake_inputs(seed=3):
    """Small synthetic inputs with the real structure (no real file)."""
    rng = np.random.default_rng(seed)
    cells = pd.DataFrame([dict(act_class=a, hemisphere=h, area_class=s, cohort=c) for a in (1, 2, 3) for h in ("N", "S")
                          for s in (1, 2, 3) for c in ("M1", "U")])
    rows = []
    for i in range(1200):
        t = pd.Timestamp("1996-06-01") + pd.Timedelta(days=int(rng.integers(0, 5000)))
        if pd.Timestamp("1998-05-01") <= t < pd.Timestamp("1998-12-01"):     # no synthetic group on missing maps
            t += pd.Timedelta(days=240)
        c = cells.iloc[i % 36]
        lat = (1 if c.hemisphere == "N" else -1) * float(rng.uniform(2, 35))
        rows.append(dict(noaa=f"{20000 + i}", day=t.strftime("%Y-%m-%d"), t_dpd=str(t), lat=lat, lon=float(rng.uniform(0, 360)),
                         lcm=float(rng.uniform(-10, 10)), area=int(rng.integers(1, 400)), A_main=float(rng.uniform(.2, 3)),
                         hemisphere=c.hemisphere, act_class=c.act_class, area_class=c.area_class, cohort=c.cohort, mwo_label="x"))
    pop = pd.DataFrame(rows)
    cells["N"] = pop.groupby(KEYS).size().reindex(pd.MultiIndex.from_frame(cells[KEYS])).to_numpy()
    cells["n1"], cells["n2"] = 12, 3
    samp = []
    for i, c in cells.iterrows():
        g = pop.merge(pd.DataFrame([c[KEYS]]), on=KEYS).head(12)
        for j, x in enumerate(g.itertuples(index=False)):
            samp.append(dict(x._asdict(), level2=j < 3, w1=c.N / 12, w2=c.N / 3))
    samp = pd.DataFrame(samp)
    l1 = pd.DataFrame(dict(noaa=samp.noaa, day=samp.day, N=0, N_ephemeris=0, maps="",
                           status=np.where(rng.random(len(samp)) < .9, "ok", "window_missing"),
                           sens100_status=np.where(rng.random(len(samp)) < .8, "ok", "no_two_polarities"),
                           main_flux_pos_mx=rng.uniform(1e20, 1e22, len(samp)), main_flux_neg_mx=rng.uniform(1e20, 1e22, len(samp)),
                           sens100_flux_pos_mx=rng.uniform(1e20, 1e22, len(samp)),
                           sens100_flux_neg_mx=rng.uniform(1e20, 1e22, len(samp))))
    s2 = samp[samp.level2]
    l2 = pd.DataFrame(dict(rule="A1", noaa=s2.noaa, day=s2.day, image="A",
                           status=np.where(rng.random(len(s2)) < .6, "ok", "no_magnetogram")))
    l2["sens100_status"] = l2.status
    q2p = {t: rng.uniform(.6, 1.0, 30) for t in THR}
    q2s = {t: pd.DataFrame(dict(group=[f"activity {k}" for k in (1, 2, 3)], median_d_gamma=list(D_GAMMA_NOTE[t]))) for t in THR}
    S, silso = None, PA.run_p2.load_silso()
    nH = 600
    crH = rng.integers(2096, 2317, nH)
    hemH = np.where(rng.random(nH) < .5, "N", "S")
    latH = np.where(hemH == "N", 1, -1) * rng.uniform(2, 35, nH)
    H = pd.DataFrame(dict(CR=crH, hem=hemH, lat=latH, sinlat=np.sin(np.radians(np.abs(latH))), phi=rng.uniform(1e20, 1e22, nH),
                          cyc=np.where(crH < 2225, 24, 25), A=rng.uniform(.1, 2.5, nH), M=0,
                          t_years=[PA.years(s) for s in PA.cr_start(crH)]))
    return assemble({}, pop, samp, cells, l1, l2, q2p, q2s, [1938, 1939, 1940], silso, H)


def selftest(real=True):
    res = []

    def ok(name, cond, value=""):
        res.append((name, bool(cond), str(value)))
        print(("PASS " if cond else "FAIL ") + name + (f"  [{value}]" if value != "" else ""))

    # column whitelists and reading through read_whitelisted only
    ok("no forbidden (tilt) column in the whitelists",
       not any(f in c for cols in (COLS_L1, COLS_L2, COLS_Q2P, COLS_Q2S, COLS_AUDIT) for c in cols for f in FORBIDDEN))
    calls = []
    orig = pd.read_csv

    def spy(path, *a, **k):
        calls.append((str(path), k.get("usecols")))
        return orig(path, *a, **k)
    pd.read_csv = spy
    try:
        read_whitelisted(L1, COLS_L1, dtype={"noaa": str, "maps": str})
        try:
            read_whitelisted(L1, ["main_tilt_deg"])
            refused = False
        except TechnicalError:
            refused = True
    finally:
        pd.read_csv = orig
    ok("read_whitelisted passes usecols and refuses a tilt column", calls[0][1] == COLS_L1 and refused)
    src = Path(__file__).read_text().split("def selftest")[0]
    ok("L1/L2/Q2/AUDIT read only through read_whitelisted",
       all(src.count(f"read_csv({v}") == 0 for v in ("L1", "L2", "AUDIT")) and "Q2_PAIRS_A1_{t}.csv\", COLS_Q2P" in src)
    ok("seed zone 35200000-35204019 disjoint from phase A USED_RANGES", seeds_ok())
    # random numbers: stable, indexed, independent of the design
    a = uniforms(3, 0, 5401)
    b = uniforms(3, 0, 5401)
    ok("uniforms reproducible and indexed by row (same vector whatever the design)",
       np.array_equal(a, b) and not np.array_equal(a, uniforms(4, 0, 5401)) and not np.array_equal(a, uniforms(3, 3, 5401)))
    try:
        uniforms(20, 0, 3)
        bad = False
    except TechnicalError:
        bad = True
    ok("realisation 20 refused (zone fixed at 20)", bad)
    # Beta yields
    v = np.array([0.1, 0.5, 0.9])
    p0 = beta_dist.ppf(v, 0 + .5, 5 - 0 + .5)
    p5 = beta_dist.ppf(v, 5 + .5, 0 + .5)
    ok("Beta r=0 and r=n: quantiles inside (0,1), ordered, symmetric to each other",
       np.all((p0 > 0) & (p0 < 1)) and np.all(np.diff(p0) > 0) and np.allclose(p0, 1 - p5[::-1], atol=1e-12))
    # pool estimator: hand-computed example, unequal weights
    units = pd.DataFrame(dict(cohort=["M1"] * 3 + ["U"] * 2, act_class=[1, 1, 2, 1, 3], area_class=[1, 2, 2, 1, 1],
                              w=[2.0, 2.0, 6.0, 1.0, 3.0], ok_main=[1, 0, 1, 0, 1]))
    pl = yield_pools_mf(units, "ok_main").set_index(["pool", "key"])
    ok("pool M1: p_hat = (2+6)/10, n_eff = 100/44", abs(pl.at[("cohort", "M1"), "p_hat"] - 0.8) < 1e-15
       and abs(pl.at[("cohort", "M1"), "n_eff"] - 100 / 44) < 1e-12)
    ok("pool U x act 2 empty -> n = 0, p_hat NaN", pl.at[("cohort_act", "U|2"), "n"] == 0
       and np.isnan(pl.at[("cohort_act", "U|2"), "p_hat"]))
    ok("pool U x area 1: p_hat = 3/4, r_eff = p_hat n_eff", abs(pl.at[("cohort_area", "U|1"), "p_hat"] - 0.75) < 1e-15
       and abs(pl.at[("cohort_area", "U|1"), "r_eff"] - 0.75 * 16 / 10) < 1e-12)
    # incremental rank
    n = 40
    rng = np.random.default_rng(1)
    c1, c2 = rng.random(n), rng.random(n)
    w = rng.uniform(1, 5, n)
    X, names, dropped = reduce_columns([("c1", c1), ("dup", 2 * c1), ("c2", c2), ("zero", np.zeros(n))], ("x3", rng.random(n)), w)
    ok("incremental rank: duplicate and zero columns dropped, x3 kept last", names == ["c1", "c2", "x3"] and dropped == ["dup", "zero"])
    X, names, dropped = reduce_columns([("c1", c1), ("c2", c2)], ("x3", c1 - 3 * c2), w)
    ok("x3 in the span of the nuisance columns -> not identifiable", X is None)
    # MDI alone: M24 coincide with I24 and drop; bJ coincides with x3
    R = pd.DataFrame(dict(CR=np.repeat(np.arange(2000, 2010), 4), hem=np.tile(["N", "S"], 20), sinlat=rng.uniform(.1, .6, 40),
                          cyc=np.repeat([23, 24], 20), A=rng.uniform(.2, 2, 40), M=1, phi=rng.uniform(1, 2, 40),
                          t_years=np.linspace(-10, -8, 40), act_class=1))
    nu, x3 = design_columns(R, "a", True)
    _, names, dropped = reduce_columns(nu, x3, R.phi.to_numpy())
    ok("MDI-only with instrument terms: M24N/M24S coincide with I24N/I24S and drop", dropped == ["M24N", "M24S"])
    nu, x3 = design_columns(R, "bJ", True)
    X, _, _ = reduce_columns(nu, x3, R.phi.to_numpy())
    ok("MDI-only bJ: M_x3 = x3 -> x3 not identifiable (model not applicable)", X is None)
    # variance formula vs brute force covariance
    Rb = R.copy()
    Rb.loc[:19, "M"] = 0
    res_ = analyse(Rb, ("a",), combined=False)["a"]
    nu, x3 = design_columns(Rb, "a", False)
    X, names, _ = reduce_columns(nu, x3, Rb.phi.to_numpy())
    g = p2d.wls_row(X, Rb.phi.to_numpy(), names.index("x3"))
    codes, ccr, ch = cells_of(Rb)
    Z = np.zeros((len(Rb), len(ccr)))
    Z[np.arange(len(Rb)), codes] = 1
    K = D.k_true(ccr - ccr.min(), (ch == "S").astype(int), 2)
    Sig = np.diag(15 ** 2 + 2 ** 2 * Rb.M.to_numpy()) + (7.5 * 2) ** 2 * Z @ K @ Z.T
    brute = float(g @ Sig @ g)
    mine = 15 ** 2 * res_["a2"] + 2 ** 2 * res_["a2_mdi"] + (7.5 * 2) ** 2 * res_["bKb"][(2, False)]
    ok("variance formula = a' Sigma a (brute force)", abs(mine - brute) <= 1e-10 * brute, f"{mine:.6g} vs {brute:.6g}")
    # target: ramp by hand
    ab = pd.Series(Rb.A).groupby(codes).transform("mean").to_numpy()
    dg = -0.2 * np.clip((ab - A_LO_E0) / (A_HI_E0 - A_LO_E0), 0, 1) * 24.0 * Rb.sinlat.to_numpy()
    ok("target = g . ramp (hand formula)", abs(res_["target_020"] - g @ dg) <= 1e-12 * abs(g @ dg))
    # PSD with zeroed cross blocks
    ccr2 = np.array([2090, 2091, 2095, 2096, 2097, 2100])
    ch2 = np.array(["N", "S", "N", "N", "S", "N"])
    for sc in (1, 2, 3, 4, 7):
        Kz = k_matrix(ccr2, ch2, sc, True)
    ok("zeroed MDI-HMI blocks: symmetric, PSD, cross entries 0",
       np.all(Kz[:3, 3:] == 0) and np.linalg.eigvalsh(Kz).min() >= -1e-12)
    # donors L-NN with ties
    popx = pd.DataFrame(dict(cell_idx=[0, 0], lat=[10.0, -20.0]))
    don = pd.DataFrame(dict(cell_idx=[0] * 7, alat=[9.0, 11.0, 10.0, 30.0, 12.0, 8.0, 10.0], rho=1.0))
    nn, dist, _ = nn_tables(popx, don)
    ok("L-NN: nearest 5 in |lat|, ties by (noaa, day) order", list(nn[0]) == [2, 6, 0, 1, 4] and dist[0] == 2.0,
       list(nn[0]))
    ok("L-NN: cell with < 5 donors -> -1", (nn_tables(popx, don.head(4))[0] == -1).all())
    # synthetic end-to-end
    t0 = time.time()
    Ifk = fake_inputs()
    raw, des, u = compute(Ifk, n_real=2, log=lambda *a: None)
    hrows = raw[raw.design == "H"]
    ok("synthetic end-to-end: rows for every design, H once, finite SE",
       set(raw.design) == {"H", "MS", "MF", "MS+H", "MF+H"} and hrows.r.eq(-1).all()
       and np.isfinite(raw[raw.status == "ok"].se).all(), f"{len(raw)} rows, {time.time() - t0:.0f} s")
    x = raw[(raw.status == "ok") & (raw.design.isin(["MS+H", "MF+H"]))]
    ok("synthetic: combined designs contain H records (n_records > H)", (x.n_records > len(Ifk["H"])).all())
    pr = criteria(raw)
    ok("synthetic: criteria table produced", len(pr) == 6 and pr.verdict.notna().all())
    pop_ = Ifk["pop"]
    U0 = uniforms(0, 0, len(pop_))
    exp_ms = np.flatnonzero(pop_.in_MS.to_numpy() & (U0 < ms_probs(Ifk, "main", uniforms(0, 1, 36))))
    exp_mf = np.flatnonzero(pop_.in_MF.to_numpy() & (U0 < mf_probs(Ifk, "main", uniforms(0, 2, len(POOLS)))))
    Rs, _ = mdi_records(Ifk, "MS", "main", 0, "ref")
    Rf, _ = mdi_records(Ifk, "MF", "main", 0, "ref")
    both = np.intersect1d(Rs.row, Rf.row)
    ok("synthetic: inclusion = (U_g < p) with the shared U_g of POPULATION rows; same Phi in MS and MF",
       np.array_equal(Rs.row, exp_ms) and np.array_equal(Rf.row, exp_mf) and len(both) > 0
       and np.array_equal(Rs.set_index("row").phi.loc[both], Rf.set_index("row").phi.loc[both]), f"{len(both)} shared")
    # --- review bb39a23, point 2: null target (identifiable design, every cell activity below A_lo of E0)
    Rn = Rb.assign(A=rng.uniform(0.1, 0.45, len(Rb)))
    rn = analyse(Rn, ("a",), combined=False, d_prod=(-0.5, -0.8, -1.2))["a"]
    rows_n = noise_rows(rn, SENS_NOISE, REF_SIG)
    ok("null target: status ok, target_020 = target_010 = 0, SE finite, ratios NaN with flag, design-quantile target defined",
       rn["status"] == "ok" and rn["target_020"] == 0 and rn["target_010"] == 0 and rn["target_qd_020"] != 0
       and all(np.isfinite(x["se"]) and np.isnan(x["se_over_target_020"]) and x["target_null_020"] and np.isnan(x["m_prod_over_target_010"])
               and np.isfinite(x["se_over_target_qd_020"]) and not x["target_null_qd_020"] for x in rows_n))
    Rnc = Rn.assign(M=np.r_[np.zeros(20), np.ones(20)])
    rc_ = analyse(Rnc, ("a",), combined=True, u=dict(d3=1.6, sbar=0.3))["a"]
    xr = noise_rows(rc_, SENS_NOISE[:1], REF_SIG[:1], u=dict(d3=1.6, sbar=0.3))[0]
    ok("null target, combined: bias and tolerance columns for every target, no division error",
       all(f"tol_units_{f}_{t}" in xr and f"sup_scen_worst_{f}_C0.25_{t}" in xr for f in ("A", "J") for t in TARGETS)
       and xr["target_null_020"])
    # --- point 3: empty design
    em = analyse(Rb.iloc[:0], MODELS_COMB, combined=True)
    ok("empty design: status 'empty_design' for every model, no exception", all(v["status"] == "empty_design" and v["n_records"] == 0
                                                                                for v in em.values()))
    # --- point 4: target-dependent products for E0 and design quantiles, both widths; quantiles in RAW
    okr = raw[raw.status == "ok"]
    msr = okr[okr.design == "MS"]
    cbr = okr[(okr.design == "MS+H") & (okr.model == "a")]               # model a carries both offset families
    ok("products for target_020/010/qd_020/qd_010: SE/target, recognition, m_prod/target, tolerance, worst cases; A_lo/hi_design in RAW",
       all(f"{c}_{t}" in raw for t in TARGETS for c in ("se_over_target", "recognition", "target_null"))
       and all(msr[f"m_prod_over_target_{t}"].notna().all() for t in TARGETS)
       and all(cbr[f"tol_units_A_{t}"].notna().all() and cbr[f"sup_scen_worst_J_C0.5_{t}"].notna().all() for t in TARGETS)
       and okr.A_lo_design.notna().all() and okr.A_hi_design.notna().all()
       and np.allclose(okr.target_qd_020, 2 * okr.target_qd_010, rtol=1e-12))
    # --- point 3: failures expanded on the grid; zero successes, one failure; criteria do not classify
    real_mdi = mdi_records

    def failing(I_, design, th, r, variant):
        if design == "MF" and (variant == "avail_0.6" or (variant == "ref" and r == 1)):
            return None, dict(n_domain=0, status="empty_yield_stratum")
        return real_mdi(I_, design, th, r, variant)
    globals()["mdi_records"] = failing
    try:
        rawf, _, _ = compute(Ifk, n_real=2, log=lambda *a: None)
    finally:
        globals()["mdi_records"] = real_mdi
    sm0, _ = summarise(raw, 2)
    smf, nc = summarise(rawf, 2)
    kk = lambda d: set(map(tuple, d[KEYCOLS].astype(str).to_numpy()))           # noqa: E731
    z = smf[(smf.design.isin(["MF", "MF+H"])) & (smf.variant == "avail_0.6")]
    one = smf[(smf.design == "MF") & (smf.variant == "ref")]
    onec = smf[(smf.design == "MF+H") & (smf.variant.isin(["ref", "w_x0.5", "w_x2", "w_norm", "cov_zero_cross"]))]
    ok("failures expanded: SUMMARY has the same configurations as without failures; zero successes -> n_ok 0, n_fail 2; "
       "one failure -> n_ok 1, n_fail 1 (also every combined weight and covariance variant)",
       kk(smf) == kk(sm0) and len(z) > 0 and (z.n_ok == 0).all() and (z.n_fail == 2).all()
       and (one.n_ok == 1).all() and (one.n_fail == 1).all() and len(onec) == len(sm0[(sm0.design == "MF+H") & sm0.variant.isin(onec.variant.unique())])
       and (onec.n_fail == 1).all() and (nc.status == "empty_yield_stratum").any(), f"{len(smf)} vs {len(sm0)} keys")
    cf = criteria(rawf)
    ok("criteria with a failed realisation: no classification for MF alone and MF+H vs MS+H; MS unaffected",
       cf[cf.criterion == "MF da solo vs H"].verdict.iloc[0].startswith("nessuna classificazione")
       and cf[cf.criterion == "prodotto MF+H vs MS+H"].verdict.iloc[0].startswith("nessuna classificazione")
       and cf[cf.criterion == "MS da solo vs H"].verdict.iloc[0] == criteria(raw)[lambda d: d.criterion == "MS da solo vs H"].verdict.iloc[0])
    # --- point 5: cell counts, yield steps, implementation choices
    cc = cell_counts(Ifk)
    pf = Ifk["pop"]
    ok("cell counts: 36 cells, filters monotone, sums = population, MS and MF domains",
       len(cc) == 36 and cc.N_orig.sum() == len(pf) and cc.N_MS.sum() == int(pf.in_MS.sum()) and cc.N_MF.sum() == int(pf.in_MF.sum())
       and (cc.N_orig >= cc.N_f1_date).all() and (cc.N_f1_date >= cc.N_f2_cr).all() and (cc.N_f2_cr >= cc.MS_f3_maps).all()
       and (cc.MS_f3_maps >= cc.MS_f3_N_ambiguous).all() and (cc.N_f2_cr >= cc.MF_f4_gap).all() and (cc.N_orig == cc.N_selection).all())
    ye = yield_effects(Ifk)
    uf = Ifk["mf_units"]
    ok("yield effects: one change per step, MF gap step = ratio on the filtered units, published step on all units",
       not ye.duplicated(["threshold", "design", "step_order"]).any() and set(ye.change) == {"-", "units", "domain", "Beta", "pool"}
       and abs(ye[(ye.design == "MF") & (ye.step_order == 2) & (ye.threshold == "main")].value.iloc[0]
               - (uf.w * uf.ok_main).sum() / uf.w.sum()) < 1e-15)
    ok("implementation choices: the seven declared choices and the two handling rules recorded for META",
       [c[:2] for c in IMPLEMENTATION_CHOICES[:7]] == [f"{k}." for k in range(1, 8)] and len(IMPLEMENTATION_CHOICES) == 9)
    if real:
        t0 = time.time()
        # --- point 1: receipts anchored; each alteration (in memory, one per case) is reported by its own check
        ok("freeze receipts: every anchored check matched", receipts_ok() == [], receipts_ok())
        nf0, af0 = json.loads(NOTE_FREEZE.read_text()), json.loads(A2_FREEZE.read_text())
        fs = (sha(NOTE_FREEZE), sha(A2_FREEZE))

        def alt(fn, on="nf"):
            nf, af = json.loads(json.dumps(nf0)), json.loads(json.dumps(af0))
            fn(nf if on == "nf" else af)
            return receipts_ok(nf, af, *fs)
        one_in = sorted(EXPECTED_INPUTS)[0]
        cases = [
            ("empty input list", lambda d: d.update(inputs_sha256={}), "nf", "input set (17) and hashes"),
            ("one input missing", lambda d: d["inputs_sha256"].pop(one_in), "nf", "input set (17) and hashes"),
            ("one input hash changed", lambda d: d["inputs_sha256"].update({one_in: "0" * 64}), "nf", "input set (17) and hashes"),
            ("empty code list", lambda d: d.update(reused_code_sha256={}), "nf", "reused-code set (9) and hashes"),
            ("one extra code file", lambda d: d["reused_code_sha256"].update({"scripts/mdi_q4_prospective.py": "0" * 64}), "nf",
             "reused-code set (9) and hashes"),
            ("parent SHA in the note receipt", lambda d: d.update(parent_sha256="0" * 64), "nf", "parent protocol"),
            ("A2 receipt SHA named by the note", lambda d: d.update(amendment_A2_receipt_sha256="0" * 64), "nf", "A2 receipt named by the note receipt"),
            ("note freeze commit not existing", lambda d: d.update(freeze_commit="0" * 40), "nf", "note blob at its freeze commit, ancestor of HEAD"),
            ("note freeze commit before the note existed", lambda d: d.update(freeze_commit="510274e"), "nf",
             "note blob at its freeze commit, ancestor of HEAD"),
            ("seed zone [0, 0]", lambda d: d.update(seed_zone=[0, 0]), "nf", "seed0, seed zone, realisations, z"),
            ("A2 freeze commit in the A2 receipt", lambda d: d.update(freeze_commit="1674f57267da350fa40169378ce568f3b13401b6"), "af",
             "A2 blob at its freeze commit, same commit in both receipts"),
            ("prep META SHA in the A2 receipt", lambda d: d.update(prep_counts_meta_sha256="0" * 64), "af", "preparatory-count rules and META"),
        ]
        for name, fn, on, expect in cases:
            pr_ = alt(fn, on)
            ok(f"receipt altered in memory ({name}) -> '{expect}' only", pr_ == [expect], pr_)
        pr_ = receipts_ok(nf0, af0, "0" * 64, fs[1])
        ok("note receipt file SHA different from the pinned one -> refused", pr_ == ["note receipt pinned"], pr_)
        I = load_inputs()
        pe = proof_e0(I)
        ok("§6.1 E0 reproduction: columns, dropped, targets, 9 SE and shares of every model (rel 1e-12)",
           pe["rows"] == 36 and not pe["failures"] and pe["target_ok"], pe["failures"][:3])
        ok("§6.1 generalised variance = phase A t3_var on E0 (all models, noise 0-8)", pe["t3_var_ok"], pe["n_t3_var"])
        py = proof_yields(I)
        ok("§6.2 deterministic yields reproduced (22 L1 + 24 L2 rows, rel 1e-12)", py["ok"], f"max rel {py['max_rel']:.2e}")
        pp = proof_prep_counts(I)
        ok("preparatory counts C2/C3/C7 and filters reproduced; missing years {1996, 2008}", pp["ok"], pp)
        pools = I["mf_pools"]["main"].query("pool == 'cohort'").set_index("key")
        ok("MF pools after filter 4 = note table (M1 49/53, U 12/35)",
           (pools.at["M1", "ok"], pools.at["M1", "n"], pools.at["U", "ok"], pools.at["U", "n"]) == (49, 53, 12, 35)
           and abs(pools.at["M1", "p_hat"] - 0.9540534038970411) < 1e-12 and abs(pools.at["U", "n_eff"] - 31.368496494837025) < 1e-9)
        n_, r_ = I["ms_counts"]["main"]
        ok("MS cells: n >= 6 everywhere, 8 map-missing units removed", n_.min() >= 6 and I["ms_removed"] == 8)
        ok("every cell has >= 5 donors at 50 and 100 G",
           all((I["nn"][t][0][I["pop"].in_MS.to_numpy() | I["pop"].in_MF.to_numpy()] >= 0).all() for t in THR))
        ok("no SILSO month missing in the MDI domain", I["pop"][I["pop"].in_MS | I["pop"].in_MF].A_silso.notna().all())
        cr_ = cell_counts(I)
        ok("cell counts on real data: N_orig = selection N (5401), MS 5151, MF 5062",
           (cr_.N_orig == cr_.N_selection).all() and cr_.N_orig.sum() == 5401 and cr_.N_MS.sum() == 5151 and cr_.N_MF.sum() == 5062)
        print(f"real-data proofs: {time.time() - t0:.0f} s")
    n_ok = sum(r[1] for r in res)
    print(f"selftest {n_ok}/{len(res)}")
    return res


# ---------------------------------------------------------------- run

# Frozen versions, verified by Codex (90/90) after the freeze: the receipts are anchored to their own SHA-256 and to the
# expected input and code sets; everything else is checked against the receipts, the files and the commits.
PIN = dict(note_receipt="0f9b3acc01e6a58a182685259350f71a8caf82edc2381c209f210d89b5b2410d",
           a2_receipt="76a26f061ab99c659f312d84a599a9b3e540b77b321529bd2c99ae83b5a23326",
           note="e13a3a72875e15bed296414cfcf9423b7f4d032c3d3a8efaeb67e9ad7882ade9",
           a2="c834077011ff7e201d01eabc318de7e6fbfc547bbffcfca05a0091e87636203e",
           parent="77367350e8f9a5f71933afdcc791429b307c95ec1875224c1f2d7486950d086f",
           rules="9ce409fc1030e5d41ffac1d994887d8b540ccc711f25b488426e9c387ad8a77a")
PARENT = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
RULES = ROOT / "docs/MDI_Q4_PREP_COUNTS_RULES.md"
EXPECTED_INPUTS = frozenset({
    "results/MDI_PILOT_SELECTION/POPULATION.csv", "results/MDI_PILOT_SELECTION/SAMPLE.csv", "results/MDI_PILOT_SELECTION/CELLS.csv",
    "results/MDI_PILOT_SELECTION/META.json", "results/MDI_PILOT_L1/L1_RECORDS.csv", "results/MDI_PILOT_L2/L2_RECORDS.csv",
    "results/MDI_SYNOPTIC_AUDIT/FILES.csv", "results/MDI_PILOT_ANALYSIS_L1/Q1_YIELD_PROJECTED.csv",
    "results/MDI_PILOT_ANALYSIS_L2/YIELD_A1.csv", "results/MDI_PILOT_ANALYSIS_L2/Q2_PAIRS_A1_main.csv",
    "results/MDI_PILOT_ANALYSIS_L2/Q2_PAIRS_A1_sens100.csv", "results/MDI_PILOT_ANALYSIS_L2/Q2_SUMMARY_A1_main.csv",
    "results/MDI_PILOT_ANALYSIS_L2/Q2_SUMMARY_A1_sens100.csv", "results/PROSPECTIVE_PHASE_A/RAW.csv.gz",
    "results/P1/P1_SBL_CATALOG_BY_HARP.csv", "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv", "results/MDI_Q4_PREP_COUNTS/META.json"})
EXPECTED_CODE = frozenset({
    "scripts/prospective_phase_a.py", "scripts/t5_proxy_sensitivity.py", "python/sharpbl/diag_t5_oracle.py", "python/sharpbl/p2d.py",
    "python/sharpbl/run_p2.py", "python/sharpbl/p2f_validation.py", "python/sharpbl/p2f_pilot.py", "scripts/mdi_synoptic_adapter.py",
    "scripts/mdi_q4_prep_counts.py"})
NOTE_REL, A2_REL, PARENT_REL = "docs/MDI_PILOT_Q4_NOTE.md", "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A2.md", "docs/PROTOCOL_MDI_TILT_PILOT.md"


def blob_sha(commit, path):
    """SHA-256 of a file as committed in `commit`, or None if the commit or the path does not exist."""
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def is_ancestor(commit):
    return subprocess.run(["git", "merge-base", "--is-ancestor", str(commit), "HEAD"], cwd=ROOT, capture_output=True).returncode == 0


def receipts_ok(nf=None, af=None, nf_file_sha=None, af_file_sha=None):
    """Names of the failed checks ([] = all matched). Arguments default to the files on disk; the selftest passes
    altered copies in memory with the file SHAs, to prove each check on its own."""
    nf = json.loads(NOTE_FREEZE.read_text()) if nf is None else nf
    af = json.loads(A2_FREEZE.read_text()) if af is None else af
    nf_file_sha = sha(NOTE_FREEZE) if nf_file_sha is None else nf_file_sha
    af_file_sha = sha(A2_FREEZE) if af_file_sha is None else af_file_sha
    probs = []

    def need(name, f):
        try:
            good = bool(f())
        except (KeyError, TypeError, ValueError, AttributeError, OSError):
            good = False
        if not good:
            probs.append(name)

    def files_match(d, expected):
        return isinstance(d, dict) and set(d) == set(expected) and all(isinstance(h, str) and sha(ROOT / p) == h for p, h in d.items())

    need("note receipt pinned", lambda: nf_file_sha == PIN["note_receipt"])
    need("A2 receipt pinned", lambda: af_file_sha == PIN["a2_receipt"])
    need("receipt paths", lambda: nf["protocol"] == NOTE_REL and af["protocol"] == A2_REL and nf["amendment_A2"] == A2_REL
         and nf["parent_protocol"] == af["parent_protocol"] == PARENT_REL)
    need("note text", lambda: sha(NOTE) == nf["sha256"] == PIN["note"])
    need("note blob at its freeze commit, ancestor of HEAD", lambda: blob_sha(nf["freeze_commit"], NOTE_REL) == nf["sha256"]
         and is_ancestor(nf["freeze_commit"]))
    need("A2 text", lambda: sha(A2) == af["sha256"] == nf["amendment_A2_sha256"] == PIN["a2"])
    need("A2 blob at its freeze commit, same commit in both receipts", lambda: blob_sha(af["freeze_commit"], A2_REL) == af["sha256"]
         and nf["amendment_A2_freeze_commit"] == af["freeze_commit"] and is_ancestor(af["freeze_commit"]))
    need("A2 receipt named by the note receipt", lambda: nf["amendment_A2_receipt_sha256"] == af_file_sha)
    need("parent protocol", lambda: sha(PARENT) == nf["parent_sha256"] == af["parent_sha256"] == PIN["parent"])
    need("preparatory-count rules and META", lambda: sha(RULES) == nf["prep_counts_rules_sha256"] == af["prep_counts_rules_sha256"] == PIN["rules"]
         and af["prep_counts_meta_sha256"] == sha(PREP_META))      # the note's copy is checked with the input set
    need("input set (17) and hashes", lambda: files_match(nf["inputs_sha256"], EXPECTED_INPUTS))
    need("reused-code set (9) and hashes", lambda: files_match(nf["reused_code_sha256"], EXPECTED_CODE))
    need("seed0, seed zone, realisations, z", lambda: nf["seed0"] == SEED0 and nf["n_realisations"] == N_REAL and nf["z"] == PA.Z
         and list(nf["seed_zone"]) == [SEED0, SEED0 + 1000 * (K_COMPONENTS - 1) + N_REAL - 1])
    return probs


def run():
    if git("status", "--porcelain", "--untracked-files=no"):
        raise TechnicalError("tracked files modified: run only on a clean tree")
    if sha(__file__) != hashlib.sha256(subprocess.run(["git", "show", f"HEAD:scripts/{Path(__file__).name}"], cwd=ROOT,
                                                      capture_output=True, check=True).stdout).hexdigest():
        raise TechnicalError("script differs from HEAD")
    probs = receipts_ok()
    if probs:
        raise TechnicalError(f"freeze receipts not matched: {probs}")
    if OUT.exists():
        raise TechnicalError(f"{OUT} exists: single run")
    st = selftest(real=True)
    if not all(r[1] for r in st):
        raise TechnicalError("selftest/proofs failed: technical stop, no product")
    t0 = time.time()
    I = load_inputs()
    raw, des, u = compute(I)
    summ, fails = summarise(raw, N_REAL)
    crit = pd.concat([criteria(raw, "main"), criteria(raw, "sens100")], ignore_index=True)
    OUT.mkdir(parents=True)
    raw.to_csv(OUT / "RAW.csv.gz", index=False)
    summ.to_csv(OUT / "SUMMARY.csv", index=False)
    fails.to_csv(OUT / "NOT_COMPUTABLE.csv", index=False)
    crit.to_csv(OUT / "CRITERIA.csv", index=False)
    des.to_csv(OUT / "DESIGNS.csv", index=False)
    yield_effects(I).to_csv(OUT / "YIELD_EFFECTS.csv", index=False)
    cell_counts(I).to_csv(OUT / "CELL_COUNTS.csv", index=False)
    pd.concat([I["mf_pools"][t].assign(threshold=t) for t in THR]).to_csv(OUT / "MF_POOLS.csv", index=False)
    pd.DataFrame(st, columns=["check", "ok", "value"]).to_csv(OUT / "PROOFS.csv", index=False)
    meta = dict(script_sha256=sha(__file__), git_head=git("rev-parse", "HEAD"), note_sha256=sha(NOTE), a2_sha256=sha(A2),
                note_freeze_sha256=sha(NOTE_FREEZE), a2_freeze_sha256=sha(A2_FREEZE), seed0=SEED0, n_realisations=N_REAL,
                z=PA.Z, units=u, mf_missing_years=I["mf_missing_years"], noise=[list(n) for n in NOISE],
                filters=dict(population=len(I["pop"]), excl_date=int((~I["pop"].f1).sum()),
                             excl_cr=int((I["pop"].f1 & ~I["pop"].f2).sum()),
                             MS_excl_map_missing=int((I["pop"].f1 & I["pop"].f2 & I["pop"].map_missing).sum()),
                             MS_excl_N_ambiguous=int((I["pop"].f1 & I["pop"].f2 & ~I["pop"].map_missing & I["pop"].N_amb).sum()),
                             MF_excl_gap=int((I["pop"].f1 & I["pop"].f2 & I["pop"].gap).sum()),
                             MS=int(I["pop"].in_MS.sum()), MF=int(I["pop"].in_MF.sum())),
                runtime_s=round(time.time() - t0, 1), python=platform.python_version(), numpy=np.__version__,
                pandas=pd.__version__, omp=os.environ.get("OMP_NUM_THREADS"),
                receipts_problems=probs, implementation_choices=IMPLEMENTATION_CHOICES)
    (OUT / "META.json").write_text(json.dumps(meta, indent=1, default=str) + "\n")
    print(crit.to_string())


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        res = selftest(real=True)
        sys.exit(0 if all(r[1] for r in res) else 1)
    try:
        run()
    except TechnicalError as e:
        print(f"TECHNICAL STOP: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
