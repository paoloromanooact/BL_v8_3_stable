"""Phase A of the prospective information plan: A0 targets and A1 analytic WLS precision and bias.

Plan docs/PROSPECTIVE_INFORMATION_PLAN.md, frozen as a conserved plan in 71c7d17 (SHA-256 c92be19b...), launched on
the user's explicit decision of 2026-11-18. Not a validation and not an application: no real slope, no catalogue
simulation (that is phase B), no MDI data. The extended designs E1-E4 are resampled copies of HMI cells (plan §3).
Not blind: T3, P2f, T5-D1/D2 and the power study are known.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/prospective_phase_a.py --selftest   # synthetic checks + E0 reproduction
    OMP_NUM_THREADS=1 .venv/bin/python scripts/prospective_phase_a.py --run        # single run (after review, clean tree)

Implementation choices (not new decision rules; listed for the review):
- CR start dates: Meeus, Astronomical Algorithms ch. 29 (JDE = 2398140.2270 + 27.2752316 C plus the three periodic
  terms), taken as UTC calendar dates; checked against the CR column of the HMI records (selftest).
- Activity of a slot: run_p2.load_silso()["monthly"] of the month of the CR start, per hemisphere (normalised to the
  HMI mean 2010-05 -> 2026-09). E0 records keep their own A_monthly (record month), as in P2f.
- Terciles: pooled over the 442 E0 slots (both hemispheres; activity already normalised per hemisphere),
  numpy.quantile linear at 1/3 and 2/3; class 0 if A < q1, 1 if q1 <= A < q2, 2 otherwise.
- Cycle of time and phase of a slot from its CR start date (also for the donor cells, where o = record cycle - cycle
  of time of the donor slot); counts with record dates are reported beside (plan §3 quotes 2 and 2 in S).
- E2 slots: CR start in [1996-01-01, 2010-05-01), CR interval [start, next start) not intersecting
  [1998-06-01, 1998-11-01), and CR < 2096 (CR 2096 starts on 2010-04-22 and is already an E0 slot).
- E1 slots CR 2317..2383; analogue CRs = CR starting in [2016-03-01, 2021-03-01), in order, cyclically (plan §10).
- E3 has its own seeds (plan §3: seeds per extension and f) and draws its E1 and E2 parts in CR order; E4 reuses the
  E2 designs of the same f and r with zero offsets (plan: "come E2"), analytic only.
- Draw order per slot, slots in CR order then N, S: one uniform for the empty slot, one integer for the donor, then
  (MDI only) one uniform per copied record for the yield f. Donors are drawn with replacement, uniformly in stratum.
- The T3-J drift is multiplied by sin|lambda| like the rest of family J; the T3-A drift is not.
- Columns identically zero on a design (e.g. I^{M24}_h without MDI) are dropped and recorded; any further rank
  deficiency is a technical error. beta is always the column named x5 or x3.
- t for the drifts: years from 2010-05-01 to the CR start of the record's slot, per decade (t/10).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import diag_t5_oracle as D, p2d, p2f_pilot as P, p2f_validation as V, run_p2  # noqa: E402

_spec = importlib.util.spec_from_file_location("t5_proxy_sensitivity", ROOT / "scripts/t5_proxy_sensitivity.py")
PX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PX)

PLAN = ROOT / "docs/PROSPECTIVE_INFORMATION_PLAN.md"
SHA_PLAN = "c92be19b5ccbbe2bfe0770046b72ba8f8ae16cd36fb386996530a1a02939dc5f"
FREEZE_COMMIT = "71c7d179b2161b49c1f4c1c7c1d1c3f91d303037"
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
PROXY_META = ROOT / "results/T5_PROXY_SENSITIVITY/META.json"
POWER_RAW = ROOT / "results/T5_POWER_SENSITIVITY/RAW.csv.gz"
P3_SUMMARY = ROOT / "results/P3/P3_BARD_SUMMARY.csv"
OUT = ROOT / "results/PROSPECTIVE_PHASE_A"

ETA = V.ETA_BAR                      # 3.56e-25 G/Mx
GAMMA0, SD_E, SD_X = 24.0, 15.0, 7.5   # P2f generator (degrees)
Z = V.Z                              # Phi^-1(0.9875)
DMAX = (0.20, 0.10)                  # principal, secondary
TARGET_T5_E0 = {0.20: -3.668606838064011e-26, 0.10: -1.8331887834593406e-26}   # 39c010c
T3_HIST = -0.2 * GAMMA0
TILT_SCALE = 2.107                   # P3 C1 MDI median axial distance (c41fa4c)
FORMS = (("ar1_05", 1), ("ar1_09", 2), ("steps20", 7))
SCALES = (0.5, 1.0, 2.0)
NOISE = tuple((f, s, xs) for f, s in FORMS for xs in SCALES)   # same order as the power study
K_GRID = (1.0, 1.5, 2.0)
F_GRID = (0.5, 0.75, 1.0)
N_REAL = 20
T_REF = pd.Timestamp("2010-05-01")
M_MIN = {22: pd.Timestamp("1985-08-01"), 23: pd.Timestamp("1996-08-01"),
         24: run_p2.T_MIN[24], 25: run_p2.T_MIN[25]}
E0_CR = (2096, 2316)
E1_CR = (2317, 2383)
E2_WINDOW = (pd.Timestamp("1996-01-01"), pd.Timestamp("2010-05-01"))
E2_GAP = (pd.Timestamp("1998-06-01"), pd.Timestamp("1998-11-01"))
ANALOGUE = (pd.Timestamp("2016-03-01"), pd.Timestamp("2021-03-01"))
PHASE_EDGES = (0.2, 0.4, 0.6, 0.8)
# design draws (plan §3): e indexes (extension, f)
EXT_F = (("E1", 1.0), ("E2", 0.5), ("E2", 0.75), ("E2", 1.0), ("E3", 0.5), ("E3", 0.75), ("E3", 1.0))
# offset grids in units of the family (plan §4)
GRID = {"F5": dict(c0=(0, .05, -.05, .1, -.1), c1=(0, .25, -.25, .5, -.5), c2=(0, .25, -.25)),
        "A": dict(c0=(0, .5, -.5, 1, -1), c1=(0, .25, -.25, .5, -.5), c2=(0, .25, -.25)),
        "J": dict(c0=(0, .5, -.5, 1, -1), c1=(0, .25, -.25, .5, -.5), c2=(0, .25, -.25))}
C_LIMITS = (0.25, 0.5)
B_BANDS = {"ar1_05": (0.20, 0.90), "ar1_09": (0.20, 0.90), "steps20": (0.10, 0.95)}
B_CAP = 24
USED_RANGES = ([tuple(r) for r in P.USED] + [(3_000_000, 5_001_000), (6_000_000, 9_002_000), (20_000_000, 20_001_000),
               (28_000_000, 28_400_000), (29_500_000, 29_500_011), (31_000_000, 33_200_000)])


class TechnicalError(Exception):
    pass


def design_seed(e, r):
    return 34_900_000 + 100 * e + r


def b_noise_seed(j, k):
    return 34_000_000 + 10_000 * j + k


# ---------------------------------------------------------------- calendar, phase, strata (plan §3, §10)

def cr_start(cr):
    """Start of Carrington rotation(s) cr, Meeus ch. 29, as pandas Timestamps (UTC calendar)."""
    c = np.asarray(cr, float)
    m = np.radians(281.96 + 26.882476 * c)
    jde = 2398140.2270 + 27.2752316 * c + 0.1454 * np.sin(m) - 0.0085 * np.sin(2 * m) - 0.0141 * np.cos(2 * m)
    return pd.to_datetime(jde - 2440587.5, unit="D")


def cycle_of_time(ts):
    """Cycle with the most recent minimum (22 before m23) and conventional phase in units of 11 years."""
    ts = pd.Timestamp(ts)
    c = max(k for k, m in M_MIN.items() if m <= ts) if ts >= M_MIN[22] else 22
    return c, (ts - M_MIN[c]).days / 365.25 / 11.0


def phase_class(ph):
    return int(np.searchsorted(PHASE_EDGES, ph, side="right"))


def tercile(a, q):
    return 0 if a < q[0] else (1 if a < q[1] else 2)


def years(ts):
    return (pd.Timestamp(ts) - T_REF).days / 365.25


def monthly_activity(silso, ts, hem):
    return float(silso["monthly"].at[pd.Timestamp(ts).strftime("%Y-%m"), hem])


def registered_values(silso_raw=None):
    """Plan §10 from the smoothed sum of the two hemispheres (unnormalised), recomputed."""
    s = pd.read_csv(run_p2.SILSO, sep=";", header=None, skipinitialspace=True).iloc[:, [0, 1, 4, 5]]
    s.columns = ["year", "month", "N", "S"]
    s["ym"] = s["year"].astype(int).astype(str) + "-" + s["month"].astype(int).map("{:02d}".format)
    s = s.set_index("ym")[["N", "S"]].astype(float).replace(-1.0, np.nan)
    tot = s.rolling(13, center=True, min_periods=7).mean().sum(axis=1, min_count=2)
    last = tot.dropna().index.max()
    return dict(m23=tot.loc["1995-01":"1998-12"].idxmin(), max24=tot.loc["2011-01":"2016-12"].idxmax(),
                max25=tot.loc["2022-01":last].idxmax(), last=last)


def make_slot(cr, hem, silso, instrument, date=None, analogue=None, q=None):
    start = cr_start(cr)
    src = start if analogue is None else cr_start(analogue)
    c, ph = cycle_of_time(src)
    if analogue is not None:
        c += 1
    a = monthly_activity(silso, src, hem)
    out = dict(CR=int(cr), hem=hem, start=start, A=a, cyc_time=c, phase=ph, pclass=phase_class(ph),
               M=int(instrument == "MDI"), t_years=years(start), analogue=analogue)
    if q is not None:
        out["terc"] = tercile(a, q)
    return out


def e2_crs():
    crs = np.arange(1900, 2100)
    st = cr_start(crs)
    nx = cr_start(crs + 1)
    keep = (st >= E2_WINDOW[0]) & (st < E2_WINDOW[1]) & ~((st < E2_GAP[1]) & (nx > E2_GAP[0])) & (crs < E0_CR[0])
    return [int(c) for c in crs[keep]]


def analogue_crs():
    crs = np.arange(2150, 2260)
    st = cr_start(crs)
    return [int(c) for c in crs[(st >= ANALOGUE[0]) & (st < ANALOGUE[1])]]


class Strata:
    """E0 slots, terciles, empty-slot probabilities, donor cells and the fixed merge order (plan §3)."""

    def __init__(self, S, silso):
        self.S, self.silso = S, silso
        slots = [make_slot(cr, h, silso, "HMI") for cr in range(E0_CR[0], E0_CR[1] + 1) for h in ("N", "S")]
        a = np.array([s["A"] for s in slots])
        if not np.isfinite(a).all():
            raise TechnicalError("E0 slot activity not finite")
        self.q = tuple(float(v) for v in np.quantile(a, [1 / 3, 2 / 3]))
        for s in slots:
            s["terc"] = tercile(s["A"], self.q)
        self.e0_slots = pd.DataFrame(slots)
        rec = S.groupby(["CR", "hemisphere"]).indices
        self.donor_rows = {(int(c), h): np.sort(ix) for (c, h), ix in rec.items()}
        if not set(self.donor_rows) <= {(s["CR"], s["hem"]) for s in slots}:
            raise TechnicalError("S records outside the E0 slots")
        self.table = {}
        for s in slots:
            key = (s["hem"], s["pclass"], s["terc"])
            t = self.table.setdefault(key, dict(n_slots=0, n_empty=0, donors=[]))
            t["n_slots"] += 1
            if (s["CR"], s["hem"]) in self.donor_rows:
                t["donors"].append((s["CR"], s["hem"]))
            else:
                t["n_empty"] += 1
        self.donor_cycle_time = {k: cycle_of_time(cr_start(k[0]))[0] for k in self.donor_rows}
        self.merges = {}

    def resolve(self, key):
        """Stratum statistics for key, merged by the fixed order only if key has no E0 slot."""
        if key in self.merges:
            return self.merges[key]
        hem, p, t = key
        if key in self.table:
            res = (key, self.table[key], "own")
        else:
            res = None
            for cand, how in (((hem, p, t - 1), "lower tercile"), ((hem, p, t + 1), "upper tercile"),
                              ((hem, p - 1, t), "previous phase class"), ((hem, p + 1, t), "next phase class")):
                if cand in self.table:
                    res = (cand, self.table[cand], how)
                    break
            if res is None:
                pooled = dict(n_slots=0, n_empty=0, donors=[])
                for k, v in self.table.items():
                    if k[0] == hem:
                        pooled["n_slots"] += v["n_slots"]
                        pooled["n_empty"] += v["n_empty"]
                        pooled["donors"] += v["donors"]
                res = ((hem, "all", "all"), pooled, "all classes of the hemisphere")
        self.merges[key] = res
        return res

    def records_offsets(self, use_record_time=False):
        o = []
        for (cr, h), ix in self.donor_rows.items():
            for i in ix:
                tc = (cycle_of_time(self.S["t"].iat[i])[0] if use_record_time else self.donor_cycle_time[(cr, h)])
                o.append(int(self.S["cyc"].iat[i]) - tc)
        return pd.Series(o).value_counts().sort_index().to_dict()


# ---------------------------------------------------------------- generator (plan §3)

REC_COLS = ["CR", "hem", "lat", "sinlat", "phi", "cyc", "A", "gamma", "hale", "d_cm", "d_star", "M", "t_years"]


def e0_records(S):
    R = pd.DataFrame(dict(CR=S["CR"].astype(int).to_numpy(), hem=S["hemisphere"].to_numpy(), lat=S["lat"].to_numpy(float),
                          sinlat=S["sinlat"].to_numpy(float), phi=S["phi"].to_numpy(float),
                          cyc=S["cyc"].astype(int).to_numpy(), A=S["A_monthly"].to_numpy(float),
                          gamma=S["gamma"].to_numpy(float), hale=S["hale_sign"].to_numpy(float),
                          d_cm=S["d_cm"].to_numpy(float), d_star=S["d_star"].to_numpy(float)))
    R["M"] = 0
    R["t_years"] = [years(s) for s in cr_start(R["CR"].to_numpy())]
    return R


def extension_slots(ext, st):
    out = []
    if ext in ("E2", "E3"):
        out += [make_slot(cr, h, st.silso, "MDI", q=st.q) for cr in e2_crs() for h in ("N", "S")]
    if ext in ("E1", "E3"):
        an = analogue_crs()
        crs = range(E1_CR[0], E1_CR[1] + 1)
        out += [make_slot(cr, h, st.silso, "HMI", analogue=an[k % len(an)], q=st.q)
                for k, cr in enumerate(crs) for h in ("N", "S")]
    out.sort(key=lambda s: (s["CR"], s["hem"]))
    return out


def generate(ext, f, seed, st, R0):
    """Added records for one design realisation and per-slot log; E0 records are not resampled."""
    rng = np.random.default_rng(seed)
    S = st.S
    rows, log = [], []
    n_discard = 0
    for s in extension_slots(ext, st):
        key = (s["hem"], s["pclass"], s["terc"])
        used_key, tab, how = st.resolve(key)
        p_empty = tab["n_empty"] / tab["n_slots"]
        u = rng.random()
        entry = dict(CR=s["CR"], hem=s["hem"], M=s["M"], stratum=key, used=used_key, merge=how, p_empty=p_empty,
                     empty=int(u < p_empty or not tab["donors"]), donor=None, n_copied=0, n_kept=0)
        if entry["empty"]:
            log.append(entry)
            continue
        donor = tab["donors"][int(rng.integers(len(tab["donors"])))]
        ix = st.donor_rows[donor]
        o = S["cyc"].to_numpy()[ix].astype(int) - st.donor_cycle_time[donor]
        if not np.isin(o, (-1, 0, 1)).all():
            raise TechnicalError(f"cycle offset outside -1..1 for donor {donor}")
        cyc = s["cyc_time"] + o
        keep = cyc >= 22
        n_discard += int((~keep).sum())
        if s["M"]:
            keep &= rng.random(len(ix)) < f
        D_ = R0.iloc[ix[keep]].copy()
        D_["CR"] = s["CR"]
        D_["A"] = s["A"]
        D_["cyc"] = cyc[keep]
        D_["M"] = s["M"]
        D_["t_years"] = s["t_years"]
        rows.append(D_)
        entry.update(donor=donor, n_copied=len(ix), n_kept=int(keep.sum()))
        log.append(entry)
    add = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=REC_COLS)
    return add, pd.DataFrame(log), n_discard


# ---------------------------------------------------------------- matrices (plan §4)

def _finish(cols, w, target):
    names = [k for k, v in cols.items() if np.any(v != 0)]
    dropped = [k for k in cols if k not in names]
    if target not in names:
        raise TechnicalError(f"column {target} missing")
    X = np.column_stack([cols[k] for k in names])
    if np.linalg.matrix_rank(X * np.sqrt(w)[:, None]) != X.shape[1]:
        raise TechnicalError(f"rank deficient design: {names}")
    return X, names, dropped


def ch_cols(cyc, hem, scale):
    return {f"I{c}{h}": ((cyc == c) & (hem == h)) * scale for c in sorted(set(cyc)) for h in ("N", "S")}


def t3_design(R):
    R = R[np.isfinite(R["A"])].reset_index(drop=True)
    s, M, hem, cyc = R["sinlat"].to_numpy(), R["M"].to_numpy(float), R["hem"].to_numpy(), R["cyc"].to_numpy()
    a1 = R["A"].to_numpy() - 1.0
    base = ch_cols(cyc, hem, s)
    base.update({f"M24{h}": M * ((cyc == 24) & (hem == h)) * s for h in ("N", "S")})
    base["x3"] = a1 * s
    models = {"a": dict(base),
              "bJ": dict(base, M_x3=M * a1 * s),
              "bA": dict(base, M_N=M * (hem == "N"), M_S=M * (hem == "S"), M_A=M * a1)}
    w = R["phi"].to_numpy(float)
    codes, uniq = pd.factorize(pd.MultiIndex.from_arrays([R["CR"].to_numpy(), hem]))
    cell_cr = np.array([c for c, _ in uniq])
    cell_h = np.array([h for _, h in uniq])
    abar = pd.Series(R["A"].to_numpy()).groupby(codes).transform("mean").to_numpy()
    rows = {}
    for m, cols in models.items():
        X, names, dropped = _finish(cols, w, "x3")
        rows[m] = dict(g=p2d.wls_row(X, w, names.index("x3")), names=names, dropped=dropped)
    return dict(R=R, w=w, codes=codes, cell_cr=cell_cr, cell_h=cell_h, abar=abar, M=M, s=s, a1=a1,
                t=R["t_years"].to_numpy(float), rows=rows)


def t5_cells(R):
    R = R[np.isfinite(R["A"]) & np.isfinite(R["d_star"])].reset_index(drop=True)
    key = pd.MultiIndex.from_arrays([R["CR"].to_numpy(), R["hem"].to_numpy()])
    n = pd.Series(1, index=key).groupby(level=[0, 1]).transform("size").to_numpy()
    R = R[n >= 3].reset_index(drop=True)
    codes, uniq = pd.factorize(pd.MultiIndex.from_arrays([R["CR"].to_numpy(), R["hem"].to_numpy()]))
    nc = len(uniq)
    phi = R["phi"].to_numpy(float)
    W = np.bincount(codes, weights=phi, minlength=nc)
    fl = R.assign(code=codes).groupby(["code", "cyc"])["phi"].sum()
    cyc_c = np.array([int(fl.loc[j].idxmax()) for j in range(nc)])
    abar = np.bincount(codes, weights=R["A"].to_numpy(), minlength=nc) / np.bincount(codes, minlength=nc)
    Mc = np.bincount(codes, weights=R["M"].to_numpy(float), minlength=nc) / np.bincount(codes, minlength=nc)
    if not np.isin(Mc, (0.0, 1.0)).all():
        raise TechnicalError("T5 cell mixing instruments")
    cell_cr = np.array([c for c, _ in uniq])
    cell_h = np.array([h for _, h in uniq])
    tc = np.bincount(codes, weights=R["t_years"].to_numpy(), minlength=nc) / np.bincount(codes, minlength=nc)
    return R, codes, W, cyc_c, abar, Mc, cell_cr, cell_h, tc


def t5_design(R):
    R, codes, W, cyc_c, abar, Mc, cell_cr, cell_h, tc = t5_cells(R)
    base = ch_cols(cyc_c, cell_h, 1.0)
    base.update({f"M24{h}": Mc * ((cyc_c == 24) & (cell_h == h)) for h in ("N", "S")})
    base["x5"] = abar - 1.0
    models = {"a": dict(base), "b": dict(base, M_x5=Mc * (abar - 1.0))}
    rows = {}
    for m, cols in models.items():
        X, names, dropped = _finish(cols, W, "x5")
        rows[m] = dict(g=p2d.wls_row(X, W, names.index("x5")), names=names, dropped=dropped)
    agg = R["phi"].to_numpy(float) / W[codes]
    return dict(R=R, codes=codes, W=W, agg=agg, abar=abar, M=Mc, cell_cr=cell_cr, cell_h=cell_h, t=tc, rows=rows,
                Mrec=R["M"].to_numpy(float))


# ---------------------------------------------------------------- A0 targets, A1 variances and biases (plan §5)

def t5_delta_eta(dz, a_lo, a_hi, dmax):
    R = dz["R"]
    delta = PX.ramp(dz["abar"][dz["codes"]], a_lo, a_hi, dmax)
    lat, gam = R["lat"].to_numpy(), R["gamma"].to_numpy()
    dd = PX.delta_d(R["hale"].to_numpy(), R["phi"].to_numpy(), lat, R["d_cm"].to_numpy(), gam,
                    PX.shifted_gamma(gam, lat, delta))
    PX.require_finite("Delta_D", dd)
    return np.bincount(dz["codes"], weights=dd, minlength=len(dz["W"])) / dz["W"]


def t3_delta_gamma(dz, a_lo, a_hi, dmax):
    return -PX.ramp(dz["abar"], a_lo, a_hi, dmax) * GAMMA0 * dz["s"]


def t5_quantiles(dz):
    return tuple(float(v) for v in np.quantile(dz["abar"][dz["codes"]], [PX.Q_LO, PX.Q_HI]))


def t5_var(dz, g, n, k):
    form, scen, xs = NOISE[n]
    sig2 = ETA ** 2 * np.where(dz["Mrec"] == 1, k ** 2, 1.0)
    vc = np.bincount(dz["codes"], weights=dz["agg"] ** 2 * sig2, minlength=len(dz["W"]))
    t = dz["cell_cr"] - dz["cell_cr"].min()
    h = (dz["cell_h"] == "S").astype(int)
    K = D.k_true(t, h, scen)
    temporal = (0.5 * ETA * xs) ** 2 * float(g @ K @ g)
    return temporal + float(np.sum(g ** 2 * vc)), temporal


def t3_var(dz, a, n, k):
    form, scen, xs = NOISE[n]
    sig2 = SD_E ** 2 * np.where(dz["M"] == 1, k ** 2, 1.0)
    b = np.bincount(dz["codes"], weights=a)
    t = dz["cell_cr"] - dz["cell_cr"].min()
    h = (dz["cell_h"] == "S").astype(int)
    temporal = (SD_X * xs) ** 2 * float(b @ D.k_true(t, h, scen) @ b)
    return temporal + float(np.sum(a ** 2 * sig2)), temporal


def bias_bases(dz, g, family):
    """Projections of the three offset shapes (constant, activity, drift per decade) on beta (plan §4)."""
    if family == "F5":
        M, a1, t = dz["M"], dz["abar"] - 1.0, dz["t"]
        shapes = (M, M * a1, M * t / 10)
    else:
        M, a1, t = dz["M"], dz["a1"], dz["t"]
        sc = dz["s"] if family == "J" else 1.0
        shapes = (M * sc, M * a1 * sc, M * t / 10 * sc)
    return tuple(float(g @ s) for s in shapes)


def freqs(dbeta, m, se):
    """Normal reference with the signed bias (plan §5 A1)."""
    x = (dbeta + m) / se
    return dict(sup=norm.cdf(-Z - x), opp=norm.cdf(-Z + x), cov=norm.cdf(Z - m / se) - norm.cdf(-Z - m / se))


def analyse_design(R, ext, f, r, seed, a_lo, a_hi, k_values):
    """Targets, SE per noise and k, and bias bases for every test/family/model of one design."""
    out = []
    has_mdi = bool((R["M"] == 1).any())
    d5, d3 = t5_design(R), t3_design(R)
    q_ext = t5_quantiles(d5)
    common = dict(ext=ext, f=f, r=r, seed=seed, has_mdi=int(has_mdi))
    tests = [("T5", "F5", m, d5) for m in ("a", "b")] + [("T3", fam, m, d3) for fam in ("A", "J") for m in ("a", "b")]
    for test, fam, model, dz in tests:
        mkey = model if test == "T5" else ("a" if model == "a" else "b" + fam)
        row = dz["rows"][mkey]
        g = row["g"]
        tg, tg_ext = {}, {}
        for dmax in DMAX:
            if test == "T5":
                tg[dmax] = float(g @ t5_delta_eta(dz, a_lo, a_hi, dmax))
                tg_ext[dmax] = float(g @ t5_delta_eta(dz, *q_ext, dmax))
            else:
                tg[dmax] = float(g @ t3_delta_gamma(dz, a_lo, a_hi, dmax))
                tg_ext[dmax] = float(g @ t3_delta_gamma(dz, *q_ext, dmax))
        B = bias_bases(dz, g, fam)
        info = dict(test=test, family=fam, model=model, columns="|".join(row["names"]), dropped="|".join(row["dropped"]),
                    n_units=len(g), n_cells=len(dz["W"]) if test == "T5" else len(dz["cell_cr"]),
                    n_records=len(dz["R"]), n_mdi_records=int((dz["R"]["M"] == 1).sum()),
                    target_020=tg[0.20], target_010=tg[0.10], target_extq_020=tg_ext[0.20], target_extq_010=tg_ext[0.10],
                    B0=B[0], B1=B[1], B2=B[2], A_lo_ext=q_ext[0], A_hi_ext=q_ext[1])
        for n in range(len(NOISE)):
            for k in (k_values if has_mdi else (1.0,)):
                var, temporal = (t5_var(dz, g, n, k) if test == "T5" else t3_var(dz, g, n, k))
                if not (np.isfinite(var) and var > 0):
                    raise TechnicalError(f"variance not finite/positive {ext} {test} {n} {k}")
                out.append(dict(common, **info, noise=n, form=NOISE[n][0], x_scale=NOISE[n][2], k=k,
                                se=float(np.sqrt(var)), var_temporal_share=temporal / var))
    return out


# ---------------------------------------------------------------- tables from RAW

def family_units(fam, u):
    """Offset units fixed on E0 (plan §4): constant, activity coefficient, drift per decade."""
    if fam == "F5":
        return (ETA, u["d5"], u["d5"])
    if fam == "A":
        return (TILT_SCALE, u["d3"] * u["sbar"], u["d3"] * u["sbar"])
    return (TILT_SCALE / u["sbar"], u["d3"], u["d3"])


def offset_grid(family, with_offsets):
    g = GRID[family] if with_offsets else dict(c0=(0,), c1=(0,), c2=(0,))
    return pd.DataFrame([dict(c0=a, c1=b, c2=c) for a in g["c0"] for b in g["c1"] for c in g["c2"]])


def frequency_table(raw, u):
    """Plan §5 A1 products for every design row and offset combination, then median/min/max over realisations."""
    parts = []
    for (fam, with_off), x in raw.assign(off=(raw.has_mdi == 1) & (raw.ext != "E4")).groupby(["family", "off"]):
        un = family_units(fam, u)
        df = x.merge(offset_grid(fam, with_off), how="cross")
        m = (df.c0 * un[0] * df.B0 + df.c1 * un[1] * df.B1 + df.c2 * un[2] * df.B2).to_numpy()
        se = df.se.to_numpy()
        null = freqs(0.0, m, se)
        cols = dict(sup_null=null["sup"], opp_null=null["opp"], cov_null=null["cov"])
        for tag in ("020", "010"):
            tg = df[f"target_{tag}"].to_numpy()
            sc = freqs(tg, m, se)
            cols.update({f"se_over_target_{tag}": se / np.abs(tg), f"m_over_target_{tag}": m / np.abs(tg),
                         f"sup_scen_{tag}": sc["sup"], f"opp_scen_{tag}": sc["opp"], f"cov_scen_{tag}": sc["cov"]})
        parts.append(df[["ext", "f", "r", "test", "family", "model", "noise", "form", "x_scale", "k", "c0", "c1", "c2"]]
                     .assign(**cols))
    df = pd.concat(parts, ignore_index=True)
    keys = ["ext", "f", "test", "family", "model", "noise", "form", "x_scale", "k", "c0", "c1", "c2"]
    vals = [c for c in df.columns if c not in keys + ["r"]]
    agg = df.groupby(keys, dropna=False)[vals].agg(["median", "min", "max"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    n = df.groupby(keys, dropna=False)["r"].nunique().rename("n_realisations")
    return agg.join(n).reset_index()


def sensitivity_c(raw, u):
    recs = []
    sub = raw[(raw.model == "a") & (raw.has_mdi == 1) & raw.ext.isin(["E2", "E3"])]
    for _, x in sub.iterrows():
        un = family_units(x.family, u)
        for C in C_LIMITS:
            mag = C * un[1] * abs(x.B1)
            rec = dict(ext=x.ext, f=x.f, r=x.r, test=x.test, family=x.family, noise=x.noise, form=x.form,
                       x_scale=x.x_scale, k=x.k, C=C)
            for tag, col in (("020", "target_020"), ("010", "target_010")):
                tg = x[col]
                worst_rec = freqs(tg, +mag * np.sign(-tg), x.se)       # bias towards zero
                worst_false = freqs(0.0, -mag * np.sign(-tg), x.se)    # bias towards the predicted sign
                tol = 0.5 * abs(tg) / (un[1] * abs(x.B1)) if x.B1 != 0 else np.inf
                rec.update({f"sup_scen_worst_{tag}": worst_rec["sup"], f"cov_scen_worst_{tag}": worst_rec["cov"],
                            f"sup_null_worst_{tag}": worst_false["sup"], f"tolerance_units_{tag}": tol})
            recs.append(rec)
    df = pd.DataFrame(recs)
    if df.empty:
        return df
    keys = ["ext", "f", "test", "family", "noise", "form", "x_scale", "k", "C"]
    vals = [c for c in df.columns if c not in keys + ["r"]]
    agg = df.groupby(keys)[vals].agg(["median", "min", "max"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    return agg.reset_index()


def b_selection(raw, u):
    """Phase B candidate set, index, bands, simulated realisation, cap and seeds (plan §5 B). Deterministic."""
    cands = []
    for test, fam in (("T5", "F5"), ("T3", "A"), ("T3", "J")):
        for ext in ("E1", "E2", "E3"):
            for model in ("a", "b"):
                for form in ("ar1_05", "ar1_09", "steps20"):
                    for coef in (0.0, -0.5, 0.5):
                        if ext == "E1" and (model == "b" or coef != 0 or fam == "J"):
                            continue
                        cands.append((test, fam, ext, model, form, coef))
    rows = []
    for order, (test, fam, ext, model, form, coef) in enumerate(cands):
        n = [i for i, (fm, s, xs) in enumerate(NOISE) if fm == form and xs == 1.0][0]
        sel = (raw.ext == ext) & (raw.test == test) & (raw.family == fam) & (raw.model == model) & (raw.noise == n)
        if ext != "E1":
            sel &= (raw.f == 0.75) & (raw.k == 1.5)
        x = raw[sel].sort_values("r")
        if len(x) != N_REAL:
            raise TechnicalError(f"B candidate {test}/{fam}/{ext}/{model}/{form}: {len(x)} realisations")
        un = family_units(fam, u)
        p = np.array([freqs(t, coef * un[1] * b1, se)["sup"] for t, b1, se in zip(x.target_020, x.B1, x.se)])
        order_r = sorted(zip(p, x.r), key=lambda v: (v[0], v[1]))
        p10, r10 = order_r[9]
        lo, hi = B_BANDS[form]
        inside = bool(p.max() >= lo and p.min() <= hi)
        rows.append(dict(order=order, test=test, family=fam, ext=ext, model=model, form=form, activity_coef=coef,
                         f=(0.75 if ext != "E1" else np.nan), k=(1.5 if ext != "E1" else np.nan),
                         p_min=float(p.min()), p_max=float(p.max()), band_lo=lo, band_hi=hi, in_band=int(inside),
                         p10=float(p10), r10=int(r10)))
    df = pd.DataFrame(rows)
    chosen = df[df.in_band == 1].copy()
    if len(chosen) > B_CAP:
        chosen = chosen.assign(dist=(chosen.p10 - 0.5).abs()).sort_values(["dist", "order"]).head(B_CAP)
    chosen = chosen.sort_values("order")
    df["selected"] = df["order"].isin(chosen["order"]).astype(int)
    jmap = {o: j for j, o in enumerate(chosen["order"])}
    df["j"] = df["order"].map(jmap)
    df["noise_seed_first"] = df["j"].map(lambda j: b_noise_seed(int(j), 0) if pd.notna(j) else np.nan)
    df["noise_seed_last"] = df["j"].map(lambda j: b_noise_seed(int(j), 999) if pd.notna(j) else np.nan)
    return df


# ---------------------------------------------------------------- inputs, provenance

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def load_inputs():
    silso = run_p2.load_silso()
    cat = pd.read_csv(CATALOGUE, low_memory=False)
    S = run_p2.add_activity(run_p2.samples(cat)["S"], silso)
    del cat
    S = S[np.isfinite(S["A_monthly"])].reset_index(drop=True)
    if not S[P.DESIGN_COLS].equals(P.build_design()):
        raise TechnicalError("S design differs from the P2f design")
    return S, silso


def seeds_ok():
    seeds = [design_seed(e, r) for e in range(len(EXT_F)) for r in range(N_REAL)]
    seeds += [b_noise_seed(j, k) for j in range(B_CAP) for k in range(1000)]
    clash = any(lo <= s < hi for s in seeds for lo, hi in USED_RANGES)
    return (not clash) and len(set(seeds)) == len(seeds) and max(seeds[:len(EXT_F) * N_REAL]) < 34_901_000


def compute(S, silso, log=print):
    """E0 and all design realisations: RAW (one row per design, test, family, model, noise, k) and design logs."""
    st = Strata(S, silso)
    R0 = e0_records(S)
    d5 = t5_design(R0)
    a_lo, a_hi = t5_quantiles(d5)
    raw = analyse_design(R0, "E0", np.nan, 0, np.nan, a_lo, a_hi, (1.0,))
    designs, slots = [], []
    designs.append(dict(ext="E0", f=np.nan, r=0, seed=np.nan, n_added_slots=0, n_empty=0, n_added_records=0,
                        n_discarded_cycle=0, n_records=len(R0)))
    for e, (ext, f) in enumerate(EXT_F):
        for r in range(N_REAL):
            seed = design_seed(e, r)
            add, lg, n_disc = generate(ext, f, seed, st, R0)
            R = pd.concat([R0, add[R0.columns]], ignore_index=True)
            exts = [(ext, f)] + ([("E4", f)] if ext == "E2" else [])
            for ex, ff in exts:
                raw += analyse_design(R, ex, ff, r, seed, a_lo, a_hi, K_GRID)
                designs.append(dict(ext=ex, f=ff, r=r, seed=seed, n_added_slots=len(lg), n_empty=int(lg["empty"].sum()),
                                    n_added_records=len(add), n_discarded_cycle=n_disc, n_records=len(R)))
            slots.append(lg.assign(ext=ext, f=f, r=r, seed=seed))
        log(f"{ext} f={f}: {N_REAL} realisations")
    raw = pd.DataFrame(raw)
    d3 = t3_design(R0)
    u = dict(d5=abs(raw[(raw.ext == "E0") & (raw.test == "T5") & (raw.model == "a")].target_020.iloc[0]),
             d3=abs(raw[(raw.ext == "E0") & (raw.test == "T3") & (raw.model == "a")].target_020.iloc[0]),
             sbar=float(np.sum(d3["w"] * d3["s"]) / np.sum(d3["w"])))
    strata = pd.DataFrame([dict(hem=k[0], pclass=k[1], terc=k[2], n_slots=v["n_slots"], n_empty=v["n_empty"],
                                n_donors=len(v["donors"])) for k, v in sorted(st.table.items())])
    merges = pd.DataFrame([dict(stratum=str(k), used=str(v[0]), how=v[2]) for k, v in st.merges.items()])
    return dict(raw=raw, designs=pd.DataFrame(designs), slots=pd.concat(slots, ignore_index=True), strata=strata,
                merges=merges, units=u, a_lo=a_lo, a_hi=a_hi, terciles=st.q, st=st)


# ---------------------------------------------------------------- selftest

def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append((name, bool(cond), str(value)))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")

    # synthetic
    ok("CR 1 starts on 1853-11-09 (Carrington's definition)", cr_start(1).strftime("%Y-%m-%d") == "1853-11-09",
       cr_start(1))
    ok("cycle of time and phase", cycle_of_time("1996-01-01")[0] == 22 and cycle_of_time("2009-01-01")[0] == 24
       and abs(cycle_of_time("2019-12-01")[1]) < 1e-12)
    ok("phase classes", [phase_class(x) for x in (0, .199, .2, .79, .8, 1.3)] == [0, 0, 1, 3, 4, 4])
    rng = np.random.default_rng(1)
    X = np.column_stack([np.ones(50), rng.normal(size=50), rng.normal(size=50)])
    w = rng.uniform(1, 3, 50)
    g = p2d.wls_row(X, w, 2)
    ok("WLS row reproduces the coefficient of the named column", abs(g @ X[:, 2] - 1) < 1e-12 and abs(g @ X[:, 1]) < 1e-12)
    s = rng.normal(size=(3, 50))
    c = np.array([.3, -.2, .7])
    ok("bias is linear in the offset coefficients", abs(g @ (c @ s) - sum(ci * (g @ si) for ci, si in zip(c, s))) < 1e-12)
    f1, f2 = freqs(0.0, 0.0, 1.0), freqs(-3.0, 0.0, 1.0)
    ok("null without bias: each side 1.25 %", abs(f1["sup"] - 0.0125) < 1e-12 and abs(f1["cov"] - 0.975) < 1e-12)
    ok("exclusion under null = recognition of the symmetric alternative",
       abs(freqs(3.0, 0.0, 1.0)["opp"] - f2["sup"]) < 1e-15)
    ok("negative bias raises false 'supportato'", freqs(0.0, -1.0, 1.0)["sup"] > f1["sup"])
    ok("seeds disjoint from every used range and unique", seeds_ok())
    # synthetic strata and generator
    fake = _fake_strata()
    st, R0 = fake
    add, lg, nd = generate("E2", 0.0, 123, st, R0)
    ok("f = 0 keeps no MDI record", len(add) == 0 and (lg["empty"] == 0).any())
    add1, lg1, _ = generate("E2", 1.0, 123, st, R0)
    add2, lg2, _ = generate("E2", 1.0, 123, st, R0)
    ok("same seed, same design", add1.equals(add2) and lg1.equals(lg2))
    ok("empty probability 1 gives empty slots", lg1.loc[lg1.p_empty == 1, "empty"].all() if (lg1.p_empty == 1).any()
       else True)
    ok("hemispheres never merged", all(u_[0] == s_[0] for s_, u_ in zip(lg1.stratum, lg1.used)))
    ok("arrival cycles >= 22", (add1["cyc"] >= 22).all() if len(add1) else True)
    # E0 reproduction (plan §9)
    S, silso = load_inputs()
    out = {}
    reg = registered_values()
    ok("registered m23, cycle-24 and cycle-25 maxima (plan §10)",
       (reg["m23"], reg["max24"], reg["max25"]) == ("1996-08", "2014-04", "2024-10"), reg)
    an = analogue_crs()
    ok("analogue window CR count (67 E1 CR, cyclic)", 60 <= len(an) <= 70, f"{len(an)} CR {an[0]}..{an[-1]}")
    st_real = Strata(S, silso)
    rec_t = S["t"]
    lo_ok = (rec_t >= cr_start(S["CR"].to_numpy())) & (rec_t < cr_start(S["CR"].to_numpy() + 1))
    ok("record dates inside their CR (Meeus starts)", lo_ok.mean() > 0.99, f"{int(lo_ok.sum())}/{len(S)}")
    o_slot, o_rec = st_real.records_offsets(False), st_real.records_offsets(True)
    ok("cycle offsets o in {-1,0,+1}; plan §3 quotes +1: 2, -1: 2 (record dates)",
       set(o_slot) <= {-1, 0, 1} and o_rec.get(1, 0) == 2 and o_rec.get(-1, 0) == 2,
       f"slot dates {o_slot}; record dates {o_rec}")
    R0 = e0_records(S)
    d5, d3 = t5_design(R0), t3_design(R0)
    ok("E0 T5 design 2375 records in 318 cells", (len(d5["R"]), len(d5["W"])) == (2375, 318))
    ok("E0 T3 design 2485 records in 394 cells", (len(d3["R"]), len(d3["cell_cr"])) == (2485, 394))
    meta = json.loads(PROXY_META.read_text())
    a_lo, a_hi = t5_quantiles(d5)
    ok("A_lo, A_hi equal to the proxy note", (repr(a_lo), repr(a_hi)) == (meta["A_lo"], meta["A_hi"]), (a_lo, a_hi))
    for dmax in DMAX:
        tg = float(d5["rows"]["a"]["g"] @ t5_delta_eta(d5, a_lo, a_hi, dmax))
        ok(f"A0 T5 target on E0, delta_max {dmax} (39c010c)",
           abs(tg - TARGET_T5_E0[dmax]) <= 1e-10 * abs(TARGET_T5_E0[dmax]), f"{tg!r} ({tg / ETA:.5f} eta_bar)")
        out[f"t5_{dmax}"] = tg
    ok("E0 model (b) equals (a) without MDI", all(np.array_equal(d["rows"][m]["g"], d["rows"]["a"]["g"])
                                                 for d, ms in ((d5, ["b"]), (d3, ["bA", "bJ"])) for m in ms))
    # T5 A1 = O of the power study
    raw = pd.read_csv(POWER_RAW, usecols=["n", "method", "se"])
    o = raw[raw.method == "O"].groupby("n")["se"].agg(["min", "max"])
    worst = 0.0
    for n in range(len(NOISE)):
        se = np.sqrt(t5_var(d5, d5["rows"]["a"]["g"], n, 1.0)[0])
        worst = max(worst, abs(se / o.loc[n, "min"] - 1), abs(se / o.loc[n, "max"] - 1))
    ok("A1 T5 SE on E0 equals the O reference of the power study (9 configurations)", worst <= 1e-9, f"max rel {worst:.2e}")
    # T3 A1 = cell_level of P2f
    dd = V.responses(P.build_design(), 1, np.random.default_rng(0), 0.0, noise=False)
    u3 = V.units(dd, "T3")
    a3 = d3["rows"]["a"]["g"]
    same_row = np.allclose(np.sort(a3), np.sort(u3["a_row"]), rtol=0, atol=1e-12 * np.abs(u3["a_row"]).max())
    ok("T3 WLS record row equal to P2f units (as a multiset)", same_row)
    worst3 = 0.0
    for n in range(len(NOISE)):
        form, scen, xs = NOISE[n]
        yc, Xc, vc, b, t, hh, ind = V.cell_level(u3, np.full(len(u3["y"]), SD_E ** 2))
        ref = (SD_X * xs) ** 2 * float(b @ D.k_true(t, hh, scen) @ b) + ind
        mine = t3_var(d3, a3, n, 1.0)[0]
        worst3 = max(worst3, abs(mine / ref - 1))
    ok("A1 T3 variance on E0 equals the individual + temporal parts of V.cell_level", worst3 <= 1e-9,
       f"max rel {worst3:.2e}")
    tg3 = float(a3 @ t3_delta_gamma(d3, a_lo, a_hi, 0.20))
    ok("A0 T3 target on E0 computed (not previously registered)", np.isfinite(tg3),
       f"{tg3:.4f} deg = {tg3 / GAMMA0:.4f} gamma0 (historical grid {T3_HIST} deg)")
    bard = pd.read_csv(P3_SUMMARY)
    v = bard[(bard["set"] == "MDI") & (bard["comparison"] == "C1")]["median_axial_delta_deg"].iloc[0]
    ok("tilt scale 2.107 deg = P3 C1 MDI median axial distance", round(float(v), 3) == TILT_SCALE, v)
    # one real realisation end to end
    add, lg, nd = generate("E3", 0.75, design_seed(5, 0), st_real, R0)
    R = pd.concat([R0, add[R0.columns]], ignore_index=True)
    rows = analyse_design(R, "E3", 0.75, 0, design_seed(5, 0), a_lo, a_hi, K_GRID)
    # T5 (a, b) + T3-A (a, b) + T3-J (a, b) = 6 matrices x 9 noise configurations x 3 values of k
    ok("one E3 realisation analysed end to end", len(rows) == 6 * 9 * 3 and all(np.isfinite(x["se"]) for x in rows),
       f"{len(add)} added records, {int(lg['empty'].sum())}/{len(lg)} empty slots, {nd} discarded (cycle < 22)")
    ok("no column dropped on a design with MDI records", {x["dropped"] for x in rows} == {""})
    e0_rows = analyse_design(R0, "E0", np.nan, 0, np.nan, a_lo, a_hi, (1.0,))
    mdi_cols = {"M24N", "M24S", "M_x5", "M_x3", "M_N", "M_S", "M_A"}
    ok("on E0 exactly the MDI columns are dropped",
       all({"M24N", "M24S"} <= set(x["dropped"].split("|")) <= mdi_cols for x in e0_rows),
       {x["dropped"] for x in e0_rows})
    n_fail = sum(not c for _, c, _ in res)
    print(f"selftest: {len(res) - n_fail}/{len(res)} superati")
    return n_fail == 0, res


def _fake_strata():
    """Synthetic S with two strata per hemisphere, for generator checks only."""
    silso = run_p2.load_silso()
    rng = np.random.default_rng(7)
    rows = []
    for cr in range(E0_CR[0], E0_CR[1] + 1, 3):
        for h in ("N", "S"):
            for _ in range(int(rng.integers(1, 5))):
                lat = (1 if h == "N" else -1) * rng.uniform(5, 30)
                t = cr_start(cr) + pd.Timedelta(days=5)
                c = 24 if t < run_p2.T_MIN[25] else 25
                rows.append(dict(CR=cr, hemisphere=h, lat=lat, sinlat=np.sin(np.radians(abs(lat))), phi=1e22, cyc=c,
                                 A_monthly=1.0, gamma=10.0, hale_sign=1.0, d_cm=5e9, d_star=1e-3, t=t))
    S = pd.DataFrame(rows)
    return Strata(S, silso), e0_records(S)


# ---------------------------------------------------------------- run

def run():
    if git("status", "--porcelain", "--untracked-files=no"):
        print("modifiche non committate: la fase A registra il commit e richiede un albero pulito")
        return 2
    if sha(PLAN) != SHA_PLAN:
        print("SHA-256 del piano diverso da quello congelato")
        return 2
    passed, checks = selftest()
    if not passed:
        print("selftest non superato: nessun calcolo")
        return 1
    t0 = time.time()
    S, silso = load_inputs()
    res = compute(S, silso)
    raw, u = res["raw"], res["units"]
    freq = frequency_table(raw, u)
    sens = sensitivity_c(raw, u)
    bsel = b_selection(raw, u)
    OUT.mkdir(parents=True, exist_ok=True)
    raw.to_csv(OUT / "RAW.csv.gz", index=False)
    freq.to_csv(OUT / "FREQUENCIES.csv.gz", index=False)
    sens.to_csv(OUT / "SENSITIVITY_C.csv", index=False)
    bsel.to_csv(OUT / "B_SELECTION.csv", index=False)
    res["designs"].to_csv(OUT / "DESIGNS.csv", index=False)
    res["slots"].to_csv(OUT / "SLOTS.csv.gz", index=False)
    res["strata"].to_csv(OUT / "STRATA_E0.csv", index=False)
    res["merges"].to_csv(OUT / "STRATA_MERGES.csv", index=False)
    meta = dict(plan=str(PLAN.relative_to(ROOT)), plan_sha256=SHA_PLAN, freeze_commit=FREEZE_COMMIT,
                git_commit=git("rev-parse", "HEAD"), script_sha256=sha(__file__),
                inputs={str(p.relative_to(ROOT)): sha(p) for p in (CATALOGUE, run_p2.SILSO, PROXY_META, POWER_RAW, P3_SUMMARY)},
                env=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
                A_lo=repr(res["a_lo"]), A_hi=repr(res["a_hi"]), terciles=list(res["terciles"]),
                units=dict(eta_bar=ETA, abs_dbeta5_E0=u["d5"], abs_dbeta3_E0=u["d3"], sbar_E0=u["sbar"],
                           tilt_scale_deg=TILT_SCALE),
                t3_historical_grid_target_deg=T3_HIST, seconds=round(time.time() - t0, 1),
                selftest=[dict(name=n, ok=c, value=v) for n, c, v in checks],
                n_b_selected=int(bsel.selected.sum()), outcome="eseguita")
    (OUT / "META.json").write_text(json.dumps(meta, indent=2, default=str))
    print(f"fase A eseguita in {meta['seconds']} s; candidati B selezionati: {meta['n_b_selected']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest()[0] else 1
    if a.run:
        return run()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
