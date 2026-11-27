"""Independent recount of the SFT map-bipole pilot (point 2; frozen protocol docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md).

Own code; it imports neither scripts/sft_map_bipole_pilot.py nor python/sharpbl/sft_core.py (the selftest uses the runner
only to produce synthetic products). Own pieces:
- population, strata and stratified draw;
- P1-style mask, fluxes, unit-vector centroids, balancing and pixel dipoles;
- linear deposit in s and the out-of-range rule;
- point bipole; Gaussian components on their own 8-sigma rotated caps, and effective quantities on the common cap
  (the same discretisation spec as the runner, rewritten);
- hybrid finite-volume generator;
- Crank-Nicolson PROPAGATOR MATRICES built explicitly and raised to the needed powers (an algorithm different from the
  runner's step loop, mathematically equivalent), applied to all profiles at once;
- tau factors, weighted summaries (incl. the 18 cells), ratio threshold, denominators;
- amendment A1: synthetic preflight (first passing N), convergence on the observed cases (4 transports, 2N, dt/2) and
  both requirements; manifest of the map files re-hashed now, with the expected set derived from SAMPLE.
Provenance (real path): parent protocol and receipt pinned, exact receipt input set, A1 text and receipt, sft_core.py
blob at the run HEAD = A1 receipt = META, script blob at the run HEAD, catalogue, seed, run declared valid.
Declared dependencies: the P1 map reader and WCS (geometry.read_sharp, lonlat_maps, pixel_area_cm2, rsun_cm) and the
SHARP file naming (download_records.record_dir, file_stem).
Comparison: exact product set and columns; unique keys; counts integral and exactly equal; strings and booleans exact;
floats relative 1e-9 (plus 1e-12 of the column scale); convergence criteria within 1e-8 absolute. CURVES are
mandatory with an exact row count. The receipt is complete only on the real path and only if every requirement holds.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_map_bipole_pilot_recount.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_map_bipole_pilot_recount.py --check
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
from scipy.linalg import solve, solve_banded

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo  # noqa: E402  (declared dependency: P1 map reader and WCS)

OUT, REC = ROOT / "results/SFT_MAP_BIPOLE_PILOT", ROOT / "results/SFT_MAP_BIPOLE_PILOT_RECOUNT"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md", ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_FREEZE.json"
PIN = "380b79829fbac870479acc02797ef245623b689c09af9ff9f595ac5a81b61d38"
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
DAY, YEAR = 86400.0, 365.25 * 86400.0
SEED, PER_CELL, N_CELLS = 36_100_000, 4, 400
TIMES = (("0", 0.0), ("27d", 27 * DAY), ("0.5y", 0.5 * YEAR), ("1y", YEAR), ("3y", 3 * YEAR))
GRID = [(e, d) for e in (350.0, 466.8) for d in (0.025, 0.041)]
REF = (466.8, 0.025)
P_EXP, OMEGA_UNUSED = 2.33, None
PRODUCTS = {"SAMPLE.csv", "CELLS.csv", "REGIONS.csv", "DIPOLES.csv.gz", "CURVES.csv.gz", "SUMMARY.csv", "RATIOS.csv.gz", "CONVERGENCE.csv", "PREFLIGHT.csv",
            "MANIFEST.csv", "DENOMINATORS.csv", "META.json"}
CAT_COLS = ["HARPNUM", "T_REC", "role", "valid_bl", "family_rank", "NOAA_NUM", "USFLUX", "LAT_FWT", "d_axial_g", "d_axial_bal_g",
            "d_cm", "tilt_deg", "phi_pos_mx", "phi_neg_mx"]
RECEIPT_PIN = "a5f289876fef388b86be17e813e2c3d8578bdb170cb51392e7eb40a8a3f9f849"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_FREEZE.json"
CONV_TOL, N_CHOICES, CENTRES = 1e-3, (400, 800, 1600), (5.0, 15.0, 30.0, 60.0)
CONV_FLOOR, RATIO_RES = 1e-2, 0.01
INPUTS_EXPECTED = {"results/P1/P1_SBL_CATALOG_BY_HARP.csv", "python/sharpbl/geometry.py", "python/sharpbl/measure.py", "python/sharpbl/cycle.py",
                   "docs/BL_SFT_HMI_INVENTORY.md"}
EXACT = {"HARPNUM", "valid_bl", "family_rank", "NOAA_NUM", "flux_class", "perm_rank", "N_cell", "n_cell", "n_pos", "n_neg", "n", "n_ratio",
         "selected", "region_ok", "N", "n_below_ratio_threshold", "n_ratio_unresolved", "n_ratio_resolved", "n_sign_unresolved"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tname(e, d):
    return f"eta{e:g}_du{d:g}"


# ---------------------------------------------------------------- own geometry helpers

def unitv(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def centroid(lon, lat, w):
    v = (unitv(lon, lat) * np.asarray(w, float)[:, None]).sum(0)
    v = v / np.linalg.norm(v)
    return float(np.degrees(np.arctan2(v[1], v[0]))), float(np.degrees(np.arcsin(np.clip(v[2], -1, 1))))


# ---------------------------------------------------------------- own sample

def own_sample(cat):
    p = cat[cat.role.isin(["primary", "both"]) & (cat.valid_bl == 1) & (cat.family_rank == 0)]
    p = p[np.isfinite(p.USFLUX.astype(float))].sort_values("HARPNUM").reset_index(drop=True)
    u = p.USFLUX.astype(float).to_numpy()
    q1, q2 = np.quantile(u, [1 / 3, 2 / 3])
    fc = 1 + (u > q1).astype(int) + (u > q2).astype(int)
    al = np.abs(p.LAT_FWT.astype(float).to_numpy())
    band = np.where(al < 10, "<10", np.where(al < 20, "10-20", ">=20"))
    mult = np.where(p.NOAA_NUM.to_numpy() == 1, "un NOAA", "altro/ignoto")
    cell = list(zip(mult, fc, band))
    N = {}
    for c in cell:
        N[c] = N.get(c, 0) + 1
    perm = np.random.default_rng(SEED).permutation(len(p))
    taken, chosen = {}, []
    for idx in perm:
        if taken.get(cell[idx], 0) < PER_CELL:
            taken[cell[idx]] = taken.get(cell[idx], 0) + 1
            chosen.append(idx)
    rank = np.empty(len(p), int)
    rank[perm] = np.arange(len(p))
    rows = []
    for idx in chosen:
        c = cell[idx]
        rows.append(dict({k: p[k][idx] for k in CAT_COLS}, multiplicity=c[0], flux_class=int(c[1]), lat_band=c[2],
                         noaa_absent=bool(p.NOAA_NUM[idx] == 0), perm_rank=int(rank[idx]), N_cell=N[c], n_cell=taken[c],
                         pi=taken[c] / N[c], weight=N[c] / taken[c]))
    cells = pd.DataFrame([dict(multiplicity=k[0], flux_class=int(k[1]), lat_band=k[2], N_cell=v) for k, v in N.items()])
    return pd.DataFrame(rows), cells


# ---------------------------------------------------------------- own transport (propagator matrices)

class Model:
    def __init__(self, eta, du, n=N_CELLS, r=6.96e10):
        self.n, self.ds = n, 2.0 / n
        self.s = -1 + self.ds * (np.arange(n) + 0.5)
        f = -1 + self.ds * np.arange(n + 1)
        D = eta * 1e10 / r ** 2 * (1 - f ** 2) / self.ds
        lat = np.arcsin(np.clip(f, -1, 1))
        a = du * 1e5 * np.sin(lat) * np.cos(lat) ** P_EXP / r * np.sqrt(np.clip(1 - f ** 2, 0, None))
        D[0] = D[-1] = a[0] = a[-1] = 0.0
        cen = 2 * D >= np.abs(a)
        cl = np.where(cen, a / 2, np.maximum(a, 0))
        cr = np.where(cen, a / 2, np.minimum(a, 0))
        L = np.zeros((n, n))
        for j in range(n):
            # flux through face j+1 (right) minus flux through face j (left), each G = D (b_R - b_L) - (cl b_L + cr b_R)
            L[j, j] += (-D[j + 1] - cl[j + 1] - D[j] + cr[j]) / self.ds
            if j + 1 < n:
                L[j, j + 1] += (D[j + 1] - cr[j + 1]) / self.ds
            if j > 0:
                L[j, j - 1] += (D[j] + cl[j]) / self.ds
        self.L = L
        self.dt = min(DAY, 0.9 * 2.0 / float(np.max(-np.diag(L))))
        self.r = r
        self._P, self._M = {}, {}                    # propagators by step; interval operators by (dt, k, remainder)

    def prop(self, dt):
        key = round(dt, 6)
        if key not in self._P:
            I = np.eye(self.n)
            self._P[key] = solve(I - 0.5 * dt * self.L, I + 0.5 * dt * self.L)
        return self._P[key]

    def evolve_many(self, B0, targets):
        """B0: (n, m) profiles; returns list of (n, m) at each target, with the step rule of the protocol."""
        B, t, out, cache = np.asarray(B0, float), 0.0, [], self._M
        for target in targets:
            k = int(np.floor((target - t) / self.dt * (1 + 1e-12)))
            rem = target - (t + k * self.dt)
            key = (self.dt, k, round(rem, 6))
            if key not in cache:
                M = np.linalg.matrix_power(self.prop(self.dt), k) if k else np.eye(self.n)
                if rem > 1e-9 * self.dt:
                    M = self.prop(rem) @ M
                cache[key] = M
            B = cache[key] @ B
            t = target
            out.append(B)
        return out

    def dip(self, B):
        return 1.5 * (self.s @ B) * self.ds

    def deposit(self, s, F):
        if (s < self.s[0]).any() or (s > self.s[-1]).any():
            return None, int(((s < self.s[0]) | (s > self.s[-1])).sum())
        j = np.minimum(((s - self.s[0]) // self.ds).astype(int), self.n - 2)
        j = np.where(s >= self.s[j + 1], j + 1, j)
        j = np.minimum(j, self.n - 2)
        w = (s - self.s[j]) / self.ds
        out = np.zeros(self.n)
        np.add.at(out, j, F * (1 - w))
        np.add.at(out, j + 1, F * w)
        return out / (2 * np.pi * (6.96e10) ** 2 * self.ds), 0


# ---------------------------------------------------------------- own Gaussians

def cap(centre_v, radius, step, r):
    m = centre_v / np.linalg.norm(centre_v)
    e1 = np.cross(m, [0.0, 0.0, 1.0]) if abs(m[2]) < 0.9 else np.cross(m, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(m, e1)
    nr = int(math.ceil(radius / step))
    re = np.linspace(0, radius, nr + 1)
    rc = (re[:-1] + re[1:]) / 2
    nt = max(8, int(math.ceil(2 * math.pi * radius / step)))
    tc = (np.arange(nt) + 0.5) * 2 * math.pi / nt
    RR, TT = np.meshgrid(rc, tc, indexing="ij")
    v = np.cos(RR)[..., None] * m + np.sin(RR)[..., None] * (np.cos(TT)[..., None] * e1 + np.sin(TT)[..., None] * e2)
    area = np.repeat((r * r * 2 * math.pi / nt * (np.cos(re[:-1]) - np.cos(re[1:])))[:, None], nt, axis=1)
    v = v.reshape(-1, 3)
    return v, area.ravel()


def gauss_cells(lon, lat, sig, flux, r):
    c = unitv(lon, lat)
    v, a = cap(c, math.radians(8 * sig), math.radians(sig / 10), r)
    g = np.exp(-np.degrees(np.arccos(np.clip(v @ c, -1, 1))) ** 2 / (2 * sig * sig)) * a
    return v[:, 2], flux * g / g.sum()


def gauss_effective(pos, neg, sp, sn, phibar, r):
    vp, vn = unitv(*pos), unitv(*neg)
    half = 0.5 * math.acos(float(np.clip(vp @ vn, -1, 1)))
    v, a = cap(vp + vn, half + math.radians(8 * max(sp, sn)), math.radians(min(sp, sn) / 10), r)
    br = np.zeros(len(a))
    for c, sg, sign in ((vp, sp, 1.0), (vn, sn, -1.0)):
        g = np.exp(-np.degrees(np.arccos(np.clip(v @ c, -1, 1))) ** 2 / (2 * sg * sg))
        br += sign * phibar * g / (g * a).sum()
    lat = np.degrees(np.arcsin(np.clip(v[:, 2], -1, 1)))
    lon = np.degrees(np.arctan2(v[:, 1], v[:, 0])) % 360
    pos_, neg_ = br > 0, br < 0
    cp = centroid(lon[pos_], lat[pos_], br[pos_] * a[pos_])
    cn = centroid(lon[neg_], lat[neg_], -br[neg_] * a[neg_])
    return dict(eff_phi_pos=float((br[pos_] * a[pos_]).sum()), eff_phi_neg=float((-br[neg_] * a[neg_]).sum()),
                eff_lon_pos=cp[0], eff_lat_pos=cp[1], eff_lon_neg=cn[0], eff_lat_neg=cn[1])


# ---------------------------------------------------------------- own region processing

def own_ingredients(br, bm, h, thr):
    area, r = geo.pixel_area_cm2(h), geo.rsun_cm(h)
    lon, lat = geo.lonlat_maps(h, br.shape)
    sel = np.isfinite(br) & (np.abs(br) <= 10000.0) & np.isfinite(bm) & (bm >= 33) & (np.abs(br) >= thr) & np.isfinite(lon) & np.isfinite(lat)
    pos, neg = sel & (br > 0), sel & (br < 0)
    d = dict(n_pos=int(pos.sum()), n_neg=int(neg.sum()), r=r)
    if not (pos.any() and neg.any()):
        return dict(d, status="no_two_polarities")
    php, phn = br[pos].sum() * area, -br[neg].sum() * area
    pb = (php + phn) / 2
    cp, cn = centroid(lon[pos], lat[pos], br[pos]), centroid(lon[neg], lat[neg], -br[neg])
    s = np.sin(np.radians(lat[sel]))
    Fb = np.where(br[sel] > 0, br[sel] * area * pb / php, br[sel] * area * pb / phn)
    k = 3 / (4 * np.pi * r * r)
    return dict(d, status="ok", phi_pos=float(php), phi_neg=float(phn), phibar=float(pb), imbalance=float((php - phn) / (php + phn)),
                lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1], area_pos=float(pos.sum() * area), area_neg=float(neg.sum() * area),
                D_pix_raw=float(k * (br[sel] * area * s).sum()), D_pix_bal=float(k * (Fb * s).sum()), D_scale=float(3 * pb / (4 * np.pi * r * r)),
                s=s, F=Fb)


def own_all(cat, read_maps, curves=True, n=N_CELLS):
    samp, cells = own_sample(cat)
    models = {tname(e, d): model(e, d, n) for e, d in GRID}
    reg_rows, profiles = [], []                     # profiles: (HARPNUM, thr, rep, profile)
    for _, row in samp.iterrows():
        base = dict(HARPNUM=row.HARPNUM, T_REC=row.T_REC, multiplicity=row.multiplicity, noaa_absent=row.noaa_absent, flux_class=row.flux_class,
                    lat_band=row.lat_band, weight=row.weight, pi=row.pi, perm_rank=row.perm_rank, D_P1=row.d_axial_g, D_bal_P1=row.d_axial_bal_g,
                    sep_cm_P1=row.d_cm, tilt_P1=row.tilt_deg)
        try:
            br, bm, h = read_maps(row.HARPNUM, row.T_REC)
        except (OSError, ValueError, KeyError) as exc:
            reg_rows += [dict(base, threshold=t, status=f"read_error:{type(exc).__name__}") for t in (100.0, 300.0)]
            continue
        n_prof = len(profiles)
        try:
            reg_rows += _own_region(base, br, bm, h, models, profiles)
        except Exception as exc:
            del profiles[n_prof:]
            reg_rows += [dict(base, threshold=t, status=f"technical_error:{type(exc).__name__}") for t in (100.0, 300.0)]
    return _own_finish(samp, cells, reg_rows, profiles, models, curves)


def _own_region(base, br, bm, h, models, profiles):
    reg_rows = []
    row = pd.Series(base)
    if True:
        for thr in (100.0, 300.0):
            ing = own_ingredients(br, bm, h, thr)
            reg = dict(base, threshold=thr, status=ing["status"], n_pos=ing["n_pos"], n_neg=ing["n_neg"])
            if ing["status"] == "ok":
                reg.update({k: ing[k] for k in ("phi_pos", "phi_neg", "phibar", "imbalance", "lon_pos", "lat_pos", "lon_neg", "lat_neg",
                                                "area_pos", "area_neg", "D_pix_raw", "D_pix_bal", "D_scale")})
                m0 = models[tname(*REF)]
                srcs = {"M": (ing["s"], ing["F"]),
                        "B_point": (np.sin(np.radians([ing["lat_pos"], ing["lat_neg"]])), np.array([ing["phibar"], -ing["phibar"]]))}
                reps = {k: m0.deposit(*v) for k, v in srcs.items()}
                extras = {"M": {}, "B_point": {}}
                if thr == 100.0:
                    r = ing["r"]
                    sa = (math.degrees(math.sqrt(ing["area_pos"] / (2 * math.pi * r * r))), math.degrees(math.sqrt(ing["area_neg"] / (2 * math.pi * r * r))))
                    for name, (sp, sn) in (("B_gauss_area", sa), ("B_gauss_2deg", (2.0, 2.0)), ("B_gauss_4deg", (4.0, 4.0))):
                        zp, fp = gauss_cells(ing["lon_pos"], ing["lat_pos"], sp, ing["phibar"], r)
                        zn, fn = gauss_cells(ing["lon_neg"], ing["lat_neg"], sn, -ing["phibar"], r)
                        srcs[name] = (np.r_[zp, zn], np.r_[fp, fn])
                        reps[name] = m0.deposit(*srcs[name])
                        extras[name] = dict(sigma_pos=sp, sigma_neg=sn, **gauss_effective((ing["lon_pos"], ing["lat_pos"]), (ing["lon_neg"], ing["lat_neg"]),
                                                                                          sp, sn, ing["phibar"], r))
                for name, (prof, nout) in reps.items():
                    reg.update({f"{name}_status": "ok" if prof is not None else "deposition_out_of_range", f"{name}_n_out": nout,
                                **{f"{name}_{k}": v for k, v in extras[name].items()}})
                    if prof is not None:
                        profiles.append((row.HARPNUM, thr, name, prof, srcs[name]))
            reg_rows.append(reg)
    return reg_rows


def _own_finish(samp, cells, reg_rows, profiles, models, curves):
    regions = pd.DataFrame(reg_rows)
    dips, curves_rows = [], []
    if profiles:
        P = np.stack([p[3] for p in profiles], axis=1)
        for tn, mdl in models.items():
            outs = mdl.evolve_many(P, [t for _, t in TIMES])
            lev = own_levels(profiles, P, tn, mdl.n)
            for j, ((tl, ts), B) in enumerate(zip(TIMES, outs)):
                Dv = mdl.dip(B)
                for i, ((h_, thr, rep, _, _), dv) in enumerate(zip(profiles, Dv)):
                    vals = dict(D=dv, D_2N=lev["2N"][j, i], D_4N=lev["4N"][j, i], D_dthalf=lev["dt_half"][j, i])
                    dips.append(dict(HARPNUM=h_, threshold=thr, representation=rep, transport=tn, time=tl, t_s=ts, **vals))
                    if tn == tname(*REF):
                        for tau, lab in ((5.0, "ref_tau5y"), (10.0, "ref_tau10y")):
                            f = math.exp(-ts / (tau * YEAR))
                            dips.append(dict(HARPNUM=h_, threshold=thr, representation=rep, transport=lab, time=tl, t_s=ts,
                                             **{k: v * f for k, v in vals.items()}))
            if tn == tname(*REF) and curves:
                sel = [i for i, p in enumerate(profiles) if p[1] == 100.0 and p[2] in ("M", "B_point")]
                ct = [d * DAY for d in range(0, 1096)] + [3 * YEAR]
                for ts, B in zip(ct, mdl.evolve_many(P[:, sel], ct)):
                    for i, dv in zip(sel, mdl.dip(B)):
                        curves_rows.append(dict(HARPNUM=profiles[i][0], representation=profiles[i][2], t_day=ts / DAY, D=dv))
    return samp, cells, regions, pd.DataFrame(dips), pd.DataFrame(curves_rows, columns=["HARPNUM", "representation", "t_day", "D"]), models


_OWN_ADJ = {}


def own_adjoint(e, d, n):
    """Own transposed Crank-Nicolson sweep at TIMES on the grid n (used for 4N): bands taken from the own dense L."""
    key = (e, d, n)
    if key not in _OWN_ADJ:
        m = model(e, d, n)
        dg, sup, sub = np.diag(m.L).copy(), np.diag(m.L, 1).copy(), np.diag(m.L, -1).copy()   # L[j,j+1], L[j+1,j]

        def lt(x):                                   # L^T x: (L^T)[j,j+1] = L[j+1,j], (L^T)[j,j-1] = L[j-1,j]
            y = dg * x
            y[:-1] += sub * x[1:]
            y[1:] += sup * x[:-1]
            return y

        def stepper(h):
            ab = np.zeros((3, m.n))
            ab[0, 1:] = -h * sub
            ab[1] = 1.0 - h * dg
            ab[2, :-1] = -h * sup
            return lambda g: (lambda x: x + h * lt(x))(solve_banded((1, 1), ab, g))
        plan, t = [], 0.0
        for _, target in TIMES:
            k = int(np.floor((target - t) / m.dt * (1 + 1e-12)))
            rem = target - (t + k * m.dt)
            plan.append((k, rem))
            t = target
        full, rows = stepper(0.5 * m.dt), []
        for j in range(len(TIMES)):
            g = 1.5 * m.s * m.ds
            for k, rem in plan[j::-1]:
                if rem > 1e-9 * m.dt:
                    g = stepper(0.5 * rem)(g)
                for _ in range(k):
                    g = full(g)
            rows.append(g)
        _OWN_ADJ[key] = np.array(rows)
    return _OWN_ADJ[key]


def own_levels(profiles, P, tn, n):
    """D on 2N (own propagators), N with the halved step (own propagators) and 4N (own adjoint): arrays (times, profiles)."""
    e, d = next((e, d) for e, d in GRID if tname(e, d) == tn)
    tt = [t for _, t in TIMES]

    def dep(mm):
        cols = [mm.deposit(*p[4])[0] for p in profiles]
        return np.stack([c if c is not None else np.full(mm.n, np.nan) for c in cols], axis=1)
    m2, mh, m4 = model(e, d, 2 * n), model(e, d, n, half=True), model(e, d, 4 * n)
    return {"2N": np.array([m2.dip(B) for B in m2.evolve_many(dep(m2), tt)]),
            "dt_half": np.array([mh.dip(B) for B in mh.evolve_many(P, tt)]),
            "4N": own_adjoint(e, d, 4 * n) @ dep(m4)}


def own_wq(x, w, q):
    x, w = np.asarray(x, float), np.asarray(w, float)
    if not len(x):
        return np.nan
    o = np.argsort(x, kind="mergesort")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][int(np.argmax(c >= q - 1e-12))])


LEV = ("N", "2N", "4N", "dt_half")
LEVCOL = {"N": "D", "2N": "D_2N", "4N": "D_4N", "dt_half": "D_dthalf"}


def own_ratios(regions, dips):
    reg = regions.set_index(["HARPNUM", "threshold"])
    key = ["HARPNUM", "threshold", "transport", "time"]
    Mi = dips[dips.representation == "M"].set_index(key)
    B = dips[dips.representation != "M"].copy()
    kk = list(zip(B.HARPNUM, B.threshold, B.transport, B.time))
    B = B[[k in Mi.index for k in kk]].copy()
    kk = list(zip(B.HARPNUM, B.threshold, B.transport, B.time))
    for c in LEVCOL.values():
        B[c + "_M"] = Mi.loc[kk, c].to_numpy(float)
    rk = list(zip(B.HARPNUM, B.threshold))
    for c in ("D_scale", "weight", "multiplicity", "flux_class", "lat_band"):
        B[c] = reg.loc[rk, c].to_numpy()
    ref_m = dips[(dips.representation == "M") & (dips.threshold == 100.0) & (dips.transport == tname(*REF))]
    for lv in LEV:
        c = LEVCOL[lv]
        thr = {}
        for t, g in ref_m.groupby("time"):
            w = reg.loc[list(zip(g.HARPNUM, g.threshold)), "weight"].to_numpy()
            thr[t] = 0.1 * own_wq(np.abs(g[c]), w, 0.5)
        B[f"thr_{lv}"] = B.time.map(thr)
        B[f"elig_{lv}"] = (B[f"thr_{lv}"] > 0) & (B[c + "_M"].abs() >= B[f"thr_{lv}"])
        B[f"r_{lv}"] = (B[c] - B[c + "_M"]) / B[c + "_M"].abs()
    vals = B[[LEVCOL[l] for l in LEV] + [LEVCOL[l] + "_M" for l in LEV]].to_numpy(float)
    fin = np.isfinite(vals).all(axis=1)
    E = np.column_stack([B[f"elig_{l}"].to_numpy(bool) for l in LEV])
    dr = np.column_stack([np.abs(B.r_2N - B.r_N), np.abs(B.r_4N - B.r_2N), np.abs(B.r_dt_half - B.r_N)])
    status = []
    for f_, e_, d_ in zip(fin, E, dr):
        if not f_:
            status.append("ratio_unresolved")
        elif not e_.any():
            status.append("below_ratio_threshold")
        elif e_.all() and (d_ <= RATIO_RES).all():
            status.append("ratio_resolved")
        else:
            status.append("ratio_unresolved")
    B["ratio_status"] = status
    B["dr_max"] = np.where(E.all(axis=1), dr.max(axis=1), np.nan)
    B["dD"] = B.D - B.D_M
    B["dD_scaled"] = B.dD / B.D_scale
    B["dD_numdiff"] = np.max([np.abs((B[LEVCOL[l]] - B[LEVCOL[l] + "_M"]) - B.dD) for l in LEV[1:]], axis=0) / B.D_scale
    sb, sm = np.sign(vals[:, :4]), np.sign(vals[:, 4:])
    B["sign_resolved"] = fin & np.all(sb == sb[:, [0]], axis=1) & np.all(sm == sm[:, [0]], axis=1) & (sb[:, 0] != 0) & (sm[:, 0] != 0)
    B["cell"] = [f"{a}|{int(b)}|{c}" for a, b, c in zip(B.multiplicity, B.flux_class, B.lat_band)]
    return B


def own_summary(regions, dips):
    B = own_ratios(regions, dips)
    rows = []
    for (rep, thr, tr, tm), g in B.groupby(["representation", "threshold", "transport", "time"], sort=True):
        parts = [("all", g)]
        for col in ("multiplicity", "flux_class", "lat_band", "cell"):
            parts += [(f"{col}={v}", x) for v, x in g.groupby(col)]
        for label, x in parts:
            w = x.weight.to_numpy(float)
            st = x.ratio_status.to_numpy()
            res = st == "ratio_resolved"
            rv = (x.D - x.D_M).to_numpy() / np.abs(x.D_M.to_numpy())
            r = dict(representation=rep, threshold=thr, transport=tr, time=tm, group=label, n=len(x),
                     n_below_ratio_threshold=int((st == "below_ratio_threshold").sum()), n_ratio_unresolved=int((st == "ratio_unresolved").sum()),
                     n_ratio_resolved=int(res.sum()), ratio_threshold=float(x.thr_N.iloc[0]))
            for k_ in ("below_ratio_threshold", "ratio_unresolved", "ratio_resolved"):
                r[f"w_share_{k_}"] = float(w[st == k_].sum() / w.sum())
            for key, v, ww in (("dD_scaled", x.dD_scaled.to_numpy(), w), ("abs_dD", x.dD.abs().to_numpy(), w), ("ratio", rv[res], w[res])):
                for q, lab in ((0.1, "q10"), (0.5, "median"), (0.9, "q90")):
                    r[f"{key}_{lab}_w"] = own_wq(v, ww, q)
                r[f"{key}_median_unw"] = float(np.median(v)) if len(v) else np.nan
            r["dD_numdiff_median_w"] = own_wq(x.dD_numdiff.to_numpy(), w, 0.5)
            r["dD_numdiff_max"] = float(np.max(x.dD_numdiff))
            if tm == "3y":
                sr = x.sign_resolved.to_numpy(bool)
                same = (np.sign(x.D.to_numpy()) == np.sign(x.D_M.to_numpy()))[sr]
                r["n_sign_unresolved"] = int((~sr).sum())
                r["same_sign_w"] = float((w[sr] * same).sum() / w[sr].sum()) if sr.any() else np.nan
                r["same_sign_unw"] = float(same.mean()) if sr.any() else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


RATIOS_KEEP = ["HARPNUM", "threshold", "representation", "transport", "time", "D", "D_2N", "D_4N", "D_dthalf", "D_M", "D_2N_M", "D_4N_M",
               "D_dthalf_M"] + [f"{p}_{l}" for l in LEV for p in ("thr", "elig", "r")] + ["dr_max", "ratio_status", "dD_numdiff", "sign_resolved"]


def own_point(m, lp, ln, phi):
    return m.deposit(np.sin(np.radians([lp, ln])), np.array([phi, -phi]))[0]


_MODELS = {}


def model(eta, du, n, half=False):
    """Shared models (their operators are cached): reference step, or the step halved."""
    key = (eta, du, n, half)
    if key not in _MODELS:
        m = Model(eta, du, n=n)
        if half:
            m.dt = 0.5 * m.dt
        _MODELS[key] = m
    return _MODELS[key]


def own_refinements_many(profile_fns, n, eta, du, d_scales):
    """For several cases at once: dipoles at TIMES on (N, dt), (2N, dt(2N)) and (N, dt/2); per case a list of
    (refinement, time, D_ref, D_fine, criterion)."""
    tt = [t for _, t in TIMES]
    runs = {}
    for lab, m in (("ref", model(eta, du, n)), ("N_double", model(eta, du, 2 * n)), ("dt_half", model(eta, du, n, half=True))):
        P = np.stack([fn(m) for fn in profile_fns], axis=1)
        runs[lab] = [m.dip(B) for B in m.evolve_many(P, tt)]
    out = []
    for i, dsc in enumerate(d_scales):
        rows = []
        for lab in ("N_double", "dt_half"):
            for (tl, _), a, b in zip(TIMES, runs["ref"], runs[lab]):
                a_, b_ = float(a[i]), float(b[i])
                rows.append((lab, tl, a_, b_, abs(b_ - a_) / max(abs(b_), CONV_FLOOR * dsc)))
        out.append(rows)
    return out


def own_refinements(profile_fn, n, eta, du, d_scale):
    return own_refinements_many([profile_fn], n, eta, du, [d_scale])[0]


_CASES = {}


def own_preflight_cases(m):
    """A1 2.1, rewritten: name -> (profile or None, single-polarity flag); cached per grid size."""
    if m.n not in _CASES:
        _CASES[m.n] = _own_preflight_cases(m)
    return _CASES[m.n]


def _own_preflight_cases(m):
    out = {}
    for c in CENTRES:
        dl = math.sin(math.radians(10.0))
        lp, ln = c - dl, c + dl
        out[f"point_{c:g}"] = (own_point(m, lp, ln, 1e22), False)
        for sg in (2.0, 4.0):
            zp, fp = gauss_cells(1.0, lp, sg, 1e22, m.r)
            zn, fn = gauss_cells(-1.0, ln, sg, -1e22, m.r)
            out[f"gauss{sg:g}_{c:g}"] = (m.deposit(np.r_[zp, zn], np.r_[fp, fn])[0], False)
            out[f"gauss{sg:g}_pos_{c:g}"] = (m.deposit(zp, fp)[0], True)
        imp = np.zeros(m.n)
        imp[int(np.argmin(np.abs(m.s - math.sin(math.radians(c)))))] = 1e22 / (2 * np.pi * m.r ** 2 * m.ds)
        out[f"impulse_{c:g}"] = (imp, True)
    return out


def own_preflight():
    """Returns (first N that passes or None, table) with the runner's columns."""
    rows, dsc = [], 3e22 / (4 * math.pi * 6.96e10 ** 2)
    for n in N_CHOICES:
        good_all = True
        for e, d in GRID:
            m = model(e, d, n)
            cases = own_preflight_cases(m)
            fine_cases = own_preflight_cases(model(e, d, 2 * n))
            refin = [c for c, (prof, single) in cases.items() if prof is not None and fine_cases[c][0] is not None and not single]
            res = dict(zip(refin, own_refinements_many([lambda mm, c=c: own_preflight_cases(mm)[c][0] for c in refin], n, e, d,
                                                       [dsc] * len(refin))))
            for case, (prof, single) in cases.items():
                if prof is None or fine_cases[case][0] is None:
                    rows.append(dict(N=n, transport=tname(e, d), case=case, refinement="deposit", time="all", criterion=np.nan,
                                     passes=np.nan, status="deposition_out_of_range"))
                    continue
                if single:
                    outs = m.evolve_many(prof[:, None], [t for _, t in TIMES])
                    mx = float(np.abs(prof).max())
                    neg = min(float(B.min()) for B in outs)
                    mass = max(abs(float(B.sum() - prof.sum())) for B in outs) / float(np.abs(prof).sum())
                    g = neg >= -1e-12 * mx and mass <= 1e-12
                    rows.append(dict(N=n, transport=tname(e, d), case=case, refinement="positivity", time="all", criterion=max(-neg / mx, mass),
                                     passes=g, status="ok"))
                    good_all &= g
                    continue
                for lab, tl, a, b, c_ in res[case]:
                    rows.append(dict(N=n, transport=tname(e, d), case=case, refinement=lab, time=tl, D_ref=a, D_fine=b, D_scale=dsc, criterion=c_,
                                     passes=bool(c_ <= CONV_TOL), status="ok"))
                    good_all &= c_ <= CONV_TOL
        if good_all:
            return n, pd.DataFrame(rows)
    return None, pd.DataFrame(rows)


def own_convergence(regions, read_maps, n):
    ok = regions[(regions.threshold == 100.0) & (regions.status == "ok") & (regions.get("M_status", pd.Series(index=regions.index, dtype=object)) == "ok")
                 & (regions.get("B_point_status", pd.Series(index=regions.index, dtype=object)) == "ok")].sort_values("perm_rank").head(3)
    rows = []
    for _, row in ok.iterrows():
        br, bm, h = read_maps(row.HARPNUM, row.T_REC)
        ing = own_ingredients(br, bm, h, 100.0)
        for rep in ("M", "B_point"):
            fn = (lambda m: m.deposit(ing["s"], ing["F"])[0]) if rep == "M" else \
                (lambda m: own_point(m, ing["lat_pos"], ing["lat_neg"], ing["phibar"]))
            for e, d in GRID:
                for lab, tl, a, b, c_ in own_refinements(fn, n, e, d, ing["D_scale"]):
                    rows.append(dict(HARPNUM=row.HARPNUM, representation=rep, transport=tname(e, d), refinement=lab, time=tl, D_ref=a, D_fine=b,
                                     criterion=c_, passes=bool(c_ <= CONV_TOL)))
    t = pd.DataFrame(rows, columns=["HARPNUM", "representation", "transport", "refinement", "time", "D_ref", "D_fine", "criterion", "passes"])
    status = "no_usable_convergence_case" if len(ok) == 0 else "convergence_failed" if not t.passes.all() else \
        ("ok" if len(ok) == 3 else f"ok_with_{len(ok)}_cases")
    return t, status


def own_denominators(regions):
    rows = []
    reg = regions.assign(cell=[f"{a}|{int(b)}|{c}" for a, b, c in zip(regions.multiplicity, regions.flux_class, regions.lat_band)])
    for (cell, thr), g in reg.groupby(["cell", "threshold"]):
        r = dict(cell=cell, threshold=thr, selected=len(g), region_ok=int((g.status == "ok").sum()))
        r.update({f"failed_{k}": int(v) for k, v in g.status[g.status != "ok"].value_counts().items()})
        for rep in ("M", "B_point", "B_gauss_area", "B_gauss_2deg", "B_gauss_4deg"):
            if f"{rep}_status" in g:
                r[f"{rep}_ok"] = int((g[f"{rep}_status"] == "ok").sum())
                r[f"{rep}_out_of_range"] = int((g[f"{rep}_status"] == "deposition_out_of_range").sum())
        rows.append(r)
    return pd.DataFrame(rows).fillna(0)


def own_manifest(sample, paths_fn):
    rows = []
    for h_, t_ in zip(sample.HARPNUM, sample.T_REC):
        for kind, p in zip(("Br", "bitmap", "keys"), paths_fn(h_, t_)):
            ex = Path(p).exists()
            rows.append(dict(HARPNUM=h_, T_REC=t_, kind=kind, path=str(p), exists=ex, sha256=sha(p) if ex else "",
                             T_OBS=json.loads(Path(p).read_text()).get("T_OBS") if ex and kind == "keys" else None))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- comparison and check

def is_count(c):
    return c in EXACT or c.startswith("failed_") or c.endswith(("_ok", "_out_of_range", "_n_out"))


def frames_match(a, b, key, tol=1e-9, abs_cols=()):
    """Exact column set, unique keys, equal rows; counts integral and exactly equal; strings and booleans exact; floats
    relative `tol` plus 1e-12 of the column scale; columns in `abs_cols` within 1e-8 absolute."""
    if set(a.columns) != set(b.columns):
        return False, f"columns {sorted(set(a.columns) ^ set(b.columns))[:4]}"
    if len(a) != len(b):
        return False, f"rows {len(a)} vs {len(b)}"
    for f, lab in ((a, "theirs"), (b, "ours")):
        if f.duplicated(key).any():
            return False, f"duplicate keys ({lab})"
    a = a.sort_values(key, kind="mergesort").reset_index(drop=True)
    b = b[list(a.columns)].sort_values(key, kind="mergesort").reset_index(drop=True)
    for c in a.columns:
        x, y = a[c], b[c]
        xn, yn = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
        if x.dtype == object or y.dtype == object or pd.api.types.is_bool_dtype(x) or pd.api.types.is_bool_dtype(y):
            nm = lambda s: s.astype(str).replace({"nan": "", "None": "", "NaN": ""}).to_numpy()      # noqa: E731
            if not (nm(x) == nm(y)).all():
                return False, c
            continue
        xv, yv = xn.to_numpy(float), yn.to_numpy(float)
        if is_count(c):
            fx, fy = np.isfinite(xv), np.isfinite(yv)
            if not ((fx == fy).all() and (xv[fx] == np.round(xv[fx])).all() and (xv[fx] == yv[fy]).all()):
                return False, f"{c} (count)"
            continue
        fin = np.isfinite(xv) & np.isfinite(yv)
        if c in abs_cols:
            good = (np.isnan(xv) & np.isnan(yv)) | (fin & (np.abs(xv - yv) <= 1e-8))
        else:
            scale = np.nanmax(np.abs(yv[fin])) if fin.any() else 0.0
            good = (np.isnan(xv) & np.isnan(yv)) | (fin & (np.abs(xv - yv) <= tol * np.maximum(np.abs(xv), np.abs(yv)) + 1e-12 * scale))
        if not good.all():
            return False, f"{c} ({int((~good).sum())})"
    return True, ""


def guarded(fn):
    """Run a comparison; any exception on malformed products is a refusal with its type, not a crash."""
    try:
        return fn()
    except Exception as exc:                              # noqa: BLE001 (recorded as a failed check)
        return False, f"comparison raised {type(exc).__name__}: {str(exc)[:120]}"


def git_blob_sha(head, path):
    r = subprocess.run(["git", "show", f"{head}:{path}"], cwd=ROOT, capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def fits_paths(harp, t_rec):
    spec = importlib.util.find_spec("sharpbl.download_records")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    folder, stem = mod.record_dir(ROOT / "data/sharp/fits", t_rec), mod.file_stem(int(harp), t_rec)
    return folder / f"{stem}.Br.fits", folder / f"{stem}.bitmap.fits", folder / f"{stem}.keys.json"


def fits_read(harp, t_rec):
    pb, pm, _ = fits_paths(harp, t_rec)
    br, h = geo.read_sharp(pb)
    bm, _ = geo.read_sharp(pm)
    return br, bm, h


fits_read.paths = fits_paths
CSV_PRODUCTS = {k: (f"{k}.csv.gz" if k in ("DIPOLES", "CURVES", "RATIOS") else f"{k}.csv")
                for k in ("SAMPLE", "CELLS", "REGIONS", "DIPOLES", "CURVES", "SUMMARY", "RATIOS", "CONVERGENCE", "PREFLIGHT", "MANIFEST", "DENOMINATORS")}
N_CURVE_TIMES = 1097


def check(out=OUT, write=True, rec_dir=REC, data=None, outputs=None, info=None, cache=None):
    """Real path: data, outputs and info are None (read from `out`). Selftest: data = (catalogue, reader with .paths),
    outputs = product frames, info = the runner's run information (n_cells, numerical_status, manifest_unchanged,
    run_valid)."""
    checks = []

    def ok(name, cond, info_=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info_)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info_)[:160]}")

    real = data is None and outputs is None
    if real:
        fz = json.loads(FREEZE.read_text())
        meta = json.loads((Path(out) / "META.json").read_text())
        ok("frozen protocol and its receipt pinned; receipt inputs: exact set, unchanged", sha(PROTOCOL) == fz["sha256"] == PIN == meta.get("protocol_sha256")
           and sha(FREEZE) == RECEIPT_PIN == meta.get("freeze_receipt_sha256") and set(fz["inputs_sha256"]) == INPUTS_EXPECTED
           and all(sha(ROOT / p) == h for p, h in fz["inputs_sha256"].items()))
        a1 = json.loads(A1_FREEZE.read_text()) if A1_FREEZE.exists() and A1.exists() else {}
        core_blob = git_blob_sha(meta.get("git_head", ""), "python/sharpbl/sft_core.py")
        ok("amendment A1 frozen: text, receipt, parent; transport code at the run HEAD = A1 receipt = META", bool(a1)
           and sha(A1) == a1.get("sha256") == meta.get("a1_sha256") and sha(A1_FREEZE) == meta.get("a1_freeze_receipt_sha256")
           and a1.get("parent_sha256") == PIN and core_blob == a1.get("sft_core_sha256") == meta.get("sft_core_sha256"))
        ok("products: exact set and hashes", {p.name for p in Path(out).iterdir()} == PRODUCTS
           and all(sha(Path(out) / n) == h for n, h in meta["products_sha256"].items()) and set(meta["products_sha256"]) == PRODUCTS - {"META.json"})
        ok("run: script equal to the blob at the run HEAD; catalogue unchanged; seed",
           git_blob_sha(meta["git_head"], "scripts/sft_map_bipole_pilot.py") == meta["script_sha256"]
           and meta["catalogue_sha256"] == sha(CATALOGUE) and meta["seed"] == SEED)
        if not all(c["ok"] for c in checks):
            return _finish(checks, real, write, rec_dir, out)
        rd = lambda n: pd.read_csv(Path(out) / n, low_memory=False, float_precision="round_trip", keep_default_na=True)     # noqa: E731
        outputs = {}
        for k, f in CSV_PRODUCTS.items():
            try:
                outputs[k] = rd(f)
            except pd.errors.EmptyDataError:
                outputs[k] = pd.DataFrame()
        info = meta
        data = (pd.read_csv(CATALOGUE, usecols=CAT_COLS, low_memory=False), fits_read)
    cat, reader = data
    ok("run declared valid: numerical status ok, manifest unchanged during the run",
       info.get("run_valid") is True and str(info.get("numerical_status", "")).startswith("ok") and info.get("manifest_unchanged") is True,
       f"{info.get('numerical_status')} {info.get('manifest_unchanged')}")
    # A1 preflight, recomputed with propagator matrices
    memo = cache if cache is not None else {}
    if "pre" not in memo:
        memo["pre"] = own_preflight()
    n_own, pre = memo["pre"]
    tp = outputs["PREFLIGHT"]
    g = frames_match(tp, pre, ["N", "transport", "case", "refinement", "time"], abs_cols=("criterion",)) if len(tp) else (False, "empty")
    req = pre[pre.status == "ok"]
    ok("PREFLIGHT (A1 2.1-2.2): same cases, criteria within 1e-8 absolute, pass flags; first passing N = the run N; requirement met",
       g[0] and n_own is not None and n_own == info.get("n_cells") and req[req.N == n_own].passes.astype(bool).all()
       and all(not req[req.N == n].passes.astype(bool).all() for n in N_CHOICES if n < n_own), f"{g[1]} N own {n_own} run {info.get('n_cells')}")
    n_run = int(info.get("n_cells") or N_CELLS)
    if ("all", n_run) not in memo:
        memo[("all", n_run)] = own_all(cat, reader, curves=True, n=n_run)
    samp, cells, regions, dips, curves, _ = memo[("all", n_run)]
    g = frames_match(outputs["SAMPLE"], samp, ["HARPNUM"])
    ok("SAMPLE: exact columns; same HARPs, catalogue values, strata, permutation ranks, N, n, pi and weights", g[0], g[1])
    ok("CELLS: population counts per cell", frames_match(outputs["CELLS"], cells, ["multiplicity", "flux_class", "lat_band"])[0])
    g = frames_match(outputs["REGIONS"], regions, ["HARPNUM", "threshold"])
    ok("REGIONS: statuses, fluxes, centroids, balancing, pixel dipoles, deposit statuses, Gaussian effective quantities", g[0], g[1])
    g = frames_match(outputs["DIPOLES"], dips, ["HARPNUM", "threshold", "representation", "transport", "time"])
    ok("DIPOLES: every representation, threshold, transport, tau factor and time (propagator matrices vs step loop)", g[0], g[1])
    r100 = regions[(regions.threshold == 100.0) & (regions.status == "ok")]
    n_curves = N_CURVE_TIMES * sum(int((r100.get(f"{r}_status", pd.Series(dtype=object)) == "ok").sum()) for r in ("M", "B_point"))
    g = frames_match(outputs["CURVES"], curves, ["HARPNUM", "representation", "t_day"]) if len(outputs["CURVES"]) else (False, "empty")
    ok("CURVES: mandatory; daily reference curves of M and B_point at 100 G, exact row count", g[0] and len(outputs["CURVES"]) == n_curves > 0,
       f"{g[1]} rows {len(outputs['CURVES'])} expected {n_curves}")
    # summaries recomputed from THEIR regions and dipoles: a malformed product (duplicate keys, missing columns) must be
    # refused, never crash the check
    g = guarded(lambda: frames_match(outputs["SUMMARY"], own_summary(outputs["REGIONS"], outputs["DIPOLES"]),
                                     ["representation", "threshold", "transport", "time", "group"]))
    ok("SUMMARY: weighted and unweighted quantiles, ratio threshold, same-sign fractions; groups incl. the 18 cells", g[0], g[1])
    g = guarded(lambda: frames_match(outputs["RATIOS"], own_ratios(outputs["REGIONS"], outputs["DIPOLES"])[RATIOS_KEEP],
                                     ["HARPNUM", "threshold", "representation", "transport", "time"], abs_cols=("dr_max",))
                if len(outputs["RATIOS"]) else (False, "empty"))
    ok("RATIOS (A1 2ter): levels N/2N/4N/dt_half, thresholds and eligibility per level, ratio and sign statuses", g[0], g[1])
    g = frames_match(outputs["DENOMINATORS"], own_denominators(regions), ["cell", "threshold"])
    ok("DENOMINATORS: per cell and threshold, selected, successes and failures by cause (integral counts)", g[0], g[1])
    mf = own_manifest(samp, reader.paths)
    g = frames_match(outputs["MANIFEST"], mf, ["HARPNUM", "kind"])
    ok("MANIFEST: Br, bitmap and keys of every sampled record (set derived from SAMPLE); SHA-256 and T_OBS re-read now",
       g[0] and mf.exists.all() and len(mf) == 3 * len(samp), g[1])
    if ("conv", n_run) not in memo:
        memo[("conv", n_run)] = own_convergence(regions, reader, n_run)
    oc, st = memo[("conv", n_run)]
    g = frames_match(outputs["CONVERGENCE"], oc, ["HARPNUM", "representation", "transport", "refinement", "time"], abs_cols=("criterion",)) \
        if len(outputs["CONVERGENCE"]) else (False, "empty")
    ok("CONVERGENCE (A1 2.3): 4 transports, 2N and dt/2, criteria within 1e-8 absolute, pass flags", g[0], g[1])
    ok("convergence requirement met on the observed cases (else the run is not valid and the receipt is not complete)",
       st.startswith("ok") and st == info.get("numerical_status"), f"own {st} run {info.get('numerical_status')}")
    return _finish(checks, real, write, rec_dir, out)


def _finish(checks, real, write, rec_dir, out):
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks)
    if real:
        receipt.update(recount_sha256=sha(__file__), outputs_sha256={p.name: sha(p) for p in sorted(Path(out).iterdir())})
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


def selftest():
    import contextlib
    import io
    import tempfile
    spec = importlib.util.spec_from_file_location("sft_runner_selftest", ROOT / "scripts/sft_map_bipole_pilot.py")
    Rn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Rn)
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    with tempfile.TemporaryDirectory() as td:
        cat, reader = Rn.synthetic_env(td)
        prods, info = Rn.build(cat, reader, curves=True)                                # preflight included (n_cells None)
        with tempfile.TemporaryDirectory() as t2:                                      # CSV round trip, as on the real path
            rt = {}
            for k, v in prods.items():
                v.to_csv(Path(t2) / f"{k}.csv", index=False)
                try:
                    rt[k] = pd.read_csv(Path(t2) / f"{k}.csv", low_memory=False, float_precision="round_trip")
                except pd.errors.EmptyDataError:
                    rt[k] = pd.DataFrame()
        memo = {}

        def run_check(o, inf=None):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                got = check(write=False, data=(cat, reader), outputs=o, info=dict(info if inf is None else inf), cache=memo)
            return got, buf.getvalue()
        good, txt = run_check(rt)
        ok("synthetic run recounted in full (own preflight, propagators, Gaussians, summaries, denominators, manifest, convergence)", good,
           " | ".join(l for l in txt.splitlines() if "FALLITO" in l)[:400])

        def tamper(name, key, fn, inf=None):
            o = dict(rt)
            if key is not None:
                o[key] = fn(rt[key].copy())
            got, _ = run_check(o, inf)
            res.append(not got)
            print(f"[{'OK' if not got else 'FALLITO'}] refused: {name}")
        D = rt["DIPOLES"]
        i0 = D.index[D.time == "3y"][0]
        tamper("a 3-year dipole moved by 1e-7 relative", "DIPOLES", lambda t: t.assign(D=t.D.where(t.index != i0, t.D * (1 + 1e-7))))
        tamper("a dipole row dropped", "DIPOLES", lambda t: t.drop(index=i0))
        tamper("a duplicated key (one row replaced by a copy of another)", "DIPOLES", lambda t: pd.concat([t.drop(index=i0), t.loc[[t.index[0]]]]))
        tamper("a sampled HARP replaced", "SAMPLE", lambda t: t.assign(HARPNUM=t.HARPNUM.where(t.index != 0, 999)))
        tamper("a weight", "SAMPLE", lambda t: t.assign(weight=t.weight.where(t.index != 0, t.weight * 2)))
        tamper("a SAMPLE column dropped (USFLUX)", "SAMPLE", lambda t: t.drop(columns=["USFLUX"]))
        tamper("a REGIONS column dropped (D_pix_raw)", "REGIONS", lambda t: t.drop(columns=["D_pix_raw"]))
        tamper("a deposit status", "REGIONS", lambda t: t.assign(M_status=t.M_status.where(t.index != t.index[t.M_status.eq("ok")][0], "deposition_out_of_range")))
        tamper("a Gaussian effective flux", "REGIONS", lambda t: t.assign(B_gauss_2deg_eff_phi_pos=t.B_gauss_2deg_eff_phi_pos * (1 + 1e-6)))
        tamper("empty curves", "CURVES", lambda t: t.iloc[0:0])
        tamper("truncated curves (last day of one region dropped)", "CURVES", lambda t: t.drop(index=t.index[-1]))
        tamper("a weighted median", "SUMMARY", lambda t: t.assign(dD_scaled_median_w=t.dD_scaled_median_w.where(t.index != 0, 0.123)))
        tamper("a same-sign fraction", "SUMMARY", lambda t: t.assign(same_sign_w=t.same_sign_w.where(t.same_sign_w.isna() | (t.index != t.index[t.same_sign_w.notna()][0]), 0.5)))
        tamper("cell summaries dropped", "SUMMARY", lambda t: t[~t.group.str.startswith("cell=")])
        tamper("a fractional count (n + 0.5)", "SUMMARY", lambda t: t.assign(n=t.n.astype(float).where(t.index != 0, t.n.iloc[0] + 0.5)))
        tamper("a fractional denominator (selected + 0.5)", "DENOMINATORS", lambda t: t.assign(selected=t.selected.astype(float).where(t.index != 0, t.selected.iloc[0] + 0.5)))
        tamper("a failure moved between causes", "DENOMINATORS", lambda t: t.assign(region_ok=t.region_ok.where(t.index != 0, t.region_ok.iloc[0] + 1)))
        Rt = rt["RATIOS"]
        j0 = Rt.index[Rt.ratio_status == "ratio_resolved"][0] if (Rt.ratio_status == "ratio_resolved").any() else Rt.index[0]
        tamper("a ratio status (resolved -> unresolved)", "RATIOS", lambda t: t.assign(ratio_status=t.ratio_status.where(t.index != j0, "ratio_unresolved")))
        tamper("a 4N dipole moved by 1e-6 relative", "DIPOLES", lambda t: t.assign(D_4N=t.D_4N.where(t.index != i0, t.D_4N * (1 + 1e-6))))
        tamper("a resolved-ratio count", "SUMMARY", lambda t: t.assign(n_ratio_resolved=t.n_ratio_resolved.where(t.index != 0, t.n_ratio_resolved.iloc[0] + 1)))
        tamper("the 2N level column dropped from RATIOS", "RATIOS", lambda t: t.drop(columns=["r_2N"]))
        tamper("a convergence criterion", "CONVERGENCE", lambda t: t.assign(criterion=t.criterion.where(t.index != 0, 0.5)))
        tamper("convergence rows of one transport dropped", "CONVERGENCE", lambda t: t[t.transport != t.transport.iloc[0]])
        tamper("a preflight criterion moved by 1e-6 absolute", "PREFLIGHT", lambda t: t.assign(criterion=t.criterion.where(t.index != 0, t.criterion.iloc[0] + 1e-6)))
        tamper("a preflight case dropped", "PREFLIGHT", lambda t: t.drop(index=t.index[0]))
        tamper("run N different from the first passing N (400 instead of 800)", None, None, inf=dict(info, n_cells=400))
        tamper("a manifest hash", "MANIFEST", lambda t: t.assign(sha256=t.sha256.where(t.index != 0, "0" * 64)))
        tamper("a manifest row dropped", "MANIFEST", lambda t: t.drop(index=t.index[0]))
        tamper("run declared not valid (convergence_failed)", None, None, inf=dict(info, numerical_status="convergence_failed", run_valid=False))
        tamper("manifest changed during the run", None, None, inf=dict(info, manifest_unchanged=False, run_valid=False))
        # convergence requirement: the same failing table on both sides is still refused
        global CONV_TOL
        saved = CONV_TOL, Rn.CONV_TOL
        # 1e-12: far above the round-off criteria at t = 0 (~1e-15) and far below the real ones (>= ~1e-10), so that
        # the pass flags cannot flip between the two implementations (1e-15 sat on the round-off level)
        CONV_TOL = Rn.CONV_TOL = 1e-12
        try:
            t_bad, st_bad = Rn.convergence(prods["REGIONS"], reader, info["n_cells"])
            memo_bad = {k: v for k, v in memo.items() if k != ("conv", info["n_cells"])}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                got = check(write=False, data=(cat, reader), outputs=dict(rt, CONVERGENCE=t_bad), info=dict(info, numerical_status=st_bad),
                            cache=memo_bad)
        finally:
            CONV_TOL, Rn.CONV_TOL = saved
        lines = buf.getvalue().splitlines()
        ok("refused: convergence requirement not met although the values agree (no complete receipt)",
           not got and any(l.startswith("[OK] CONVERGENCE") for l in lines) and any(l.startswith("[FALLITO] convergence requirement") for l in lines),
           " | ".join(l[:110] for l in lines if "CONVERGENCE" in l or "convergence requirement" in l))
        # a map changed after the run is detected by the manifest re-read
        p0 = Path(rt["MANIFEST"].path.iloc[0])
        p0.write_bytes(p0.read_bytes() + b"x")
        got, _ = run_check(rt)
        ok("refused: a map file changed after the run (manifest hash re-read)", not got)
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
