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
- tau factors, weighted summaries, ratio threshold, convergence check.
Declared dependency: the P1 map reader and WCS (geometry.read_sharp, lonlat_maps, pixel_area_cm2, rsun_cm).
Comparison: exact product set and columns; keys exact; counts and statuses exact; floats relative 1e-9 (plus 1e-12 of
the column scale). The receipt is complete only on the real path.

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
from scipy.linalg import solve

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
PRODUCTS = {"SAMPLE.csv", "CELLS.csv", "REGIONS.csv", "DIPOLES.csv.gz", "CURVES.csv.gz", "SUMMARY.csv", "CONVERGENCE.csv", "META.json"}


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
        rows.append(dict(HARPNUM=int(p.HARPNUM[idx]), T_REC=p.T_REC[idx], multiplicity=c[0], flux_class=int(c[1]), lat_band=c[2],
                         noaa_absent=bool(p.NOAA_NUM[idx] == 0), perm_rank=int(rank[idx]), N_cell=N[c], n_cell=taken[c],
                         pi=taken[c] / N[c], weight=N[c] / taken[c], d_axial_g=p.d_axial_g[idx], d_axial_bal_g=p.d_axial_bal_g[idx],
                         d_cm=p.d_cm[idx], tilt_deg=p.tilt_deg[idx]))
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
        self._P = {}

    def prop(self, dt):
        key = round(dt, 6)
        if key not in self._P:
            I = np.eye(self.n)
            self._P[key] = solve(I - 0.5 * dt * self.L, I + 0.5 * dt * self.L)
        return self._P[key]

    def evolve_many(self, B0, targets):
        """B0: (n, m) profiles; returns list of (n, m) at each target, with the step rule of the protocol."""
        B, t, out, cache = np.asarray(B0, float), 0.0, [], {}
        for target in targets:
            k = int(np.floor((target - t) / self.dt * (1 + 1e-12)))
            rem = target - (t + k * self.dt)
            key = (k, round(rem, 6))
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


def own_all(cat, read_maps, curves=True):
    samp, cells = own_sample(cat)
    models = {tname(e, d): Model(e, d) for e, d in GRID}
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
        for thr in (100.0, 300.0):
            ing = own_ingredients(br, bm, h, thr)
            reg = dict(base, threshold=thr, status=ing["status"], n_pos=ing["n_pos"], n_neg=ing["n_neg"])
            if ing["status"] == "ok":
                reg.update({k: ing[k] for k in ("phi_pos", "phi_neg", "phibar", "imbalance", "lon_pos", "lat_pos", "lon_neg", "lat_neg",
                                                "area_pos", "area_neg", "D_pix_raw", "D_pix_bal", "D_scale")})
                m0 = models[tname(*REF)]
                reps = {"M": m0.deposit(ing["s"], ing["F"]),
                        "B_point": m0.deposit(np.sin(np.radians([ing["lat_pos"], ing["lat_neg"]])), np.array([ing["phibar"], -ing["phibar"]]))}
                extras = {"M": {}, "B_point": {}}
                if thr == 100.0:
                    r = ing["r"]
                    sa = (math.degrees(math.sqrt(ing["area_pos"] / (2 * math.pi * r * r))), math.degrees(math.sqrt(ing["area_neg"] / (2 * math.pi * r * r))))
                    for name, (sp, sn) in (("B_gauss_area", sa), ("B_gauss_2deg", (2.0, 2.0)), ("B_gauss_4deg", (4.0, 4.0))):
                        zp, fp = gauss_cells(ing["lon_pos"], ing["lat_pos"], sp, ing["phibar"], r)
                        zn, fn = gauss_cells(ing["lon_neg"], ing["lat_neg"], sn, -ing["phibar"], r)
                        reps[name] = m0.deposit(np.r_[zp, zn], np.r_[fp, fn])
                        extras[name] = dict(sigma_pos=sp, sigma_neg=sn, **gauss_effective((ing["lon_pos"], ing["lat_pos"]), (ing["lon_neg"], ing["lat_neg"]),
                                                                                          sp, sn, ing["phibar"], r))
                for name, (prof, nout) in reps.items():
                    reg.update({f"{name}_status": "ok" if prof is not None else "deposition_out_of_range", f"{name}_n_out": nout,
                                **{f"{name}_{k}": v for k, v in extras[name].items()}})
                    if prof is not None:
                        profiles.append((row.HARPNUM, thr, name, prof))
            reg_rows.append(reg)
    regions = pd.DataFrame(reg_rows)
    dips, curves_rows = [], []
    if profiles:
        P = np.stack([p[3] for p in profiles], axis=1)
        for tn, mdl in models.items():
            outs = mdl.evolve_many(P, [t for _, t in TIMES])
            for (tl, ts), B in zip(TIMES, outs):
                Dv = mdl.dip(B)
                for (h_, thr, rep, _), dv in zip(profiles, Dv):
                    dips.append(dict(HARPNUM=h_, threshold=thr, representation=rep, transport=tn, time=tl, t_s=ts, D=dv))
                    if tn == tname(*REF):
                        for tau, lab in ((5.0, "ref_tau5y"), (10.0, "ref_tau10y")):
                            dips.append(dict(HARPNUM=h_, threshold=thr, representation=rep, transport=lab, time=tl, t_s=ts, D=dv * math.exp(-ts / (tau * YEAR))))
            if tn == tname(*REF) and curves:
                sel = [i for i, p in enumerate(profiles) if p[1] == 100.0 and p[2] in ("M", "B_point")]
                ct = [d * DAY for d in range(0, 1096)] + [3 * YEAR]
                for ts, B in zip(ct, mdl.evolve_many(P[:, sel], ct)):
                    for i, dv in zip(sel, mdl.dip(B)):
                        curves_rows.append(dict(HARPNUM=profiles[i][0], representation=profiles[i][2], t_day=ts / DAY, D=dv))
    return samp, cells, regions, pd.DataFrame(dips), pd.DataFrame(curves_rows), models


def own_wq(x, w, q):
    x, w = np.asarray(x, float), np.asarray(w, float)
    if not len(x):
        return np.nan
    o = np.argsort(x, kind="mergesort")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][int(np.argmax(c >= q - 1e-12))])


def own_summary(regions, dips):
    reg = regions.set_index(["HARPNUM", "threshold"])
    M = dips[dips.representation == "M"].set_index(["HARPNUM", "threshold", "transport", "time"]).D
    rows = []
    ref_m = dips[(dips.representation == "M") & (dips.threshold == 100.0) & (dips.transport == tname(*REF))]
    thr_t = {}
    for t, g in ref_m.groupby("time"):
        w = reg.loc[list(zip(g.HARPNUM, g.threshold)), "weight"].to_numpy()
        thr_t[t] = 0.1 * own_wq(np.abs(g.D), w, 0.5)
    B = dips[dips.representation != "M"].copy()
    keys = list(zip(B.HARPNUM, B.threshold, B.transport, B.time))
    B["D_M"] = [M.get(k, np.nan) for k in keys]
    B = B[B.D_M.notna()]
    rk = list(zip(B.HARPNUM, B.threshold))
    for c in ("D_scale", "weight", "multiplicity", "flux_class", "lat_band"):
        B[c] = reg.loc[rk, c].to_numpy()
    B["dD"] = B.D - B.D_M
    B["dD_scaled"] = B.dD / B.D_scale
    B["rt"] = B.time.map(thr_t)
    B["ratio"] = np.where((B.rt > 0) & (B.D_M.abs() >= B.rt), B.dD / B.D_M.abs(), np.nan)
    for (rep, thr, tr, tm), g in B.groupby(["representation", "threshold", "transport", "time"], sort=True):
        parts = [("all", g)]
        for col in ("multiplicity", "flux_class", "lat_band"):
            parts += [(f"{col}={v}", x) for v, x in g.groupby(col)]
        for label, x in parts:
            w = x.weight.to_numpy(float)
            de = x.ratio.notna().to_numpy()
            r = dict(representation=rep, threshold=thr, transport=tr, time=tm, group=label, n=len(x), n_ratio=int(de.sum()), ratio_threshold=thr_t.get(tm, np.nan))
            for key, vals, ww in (("dD_scaled", x.dD_scaled.to_numpy(), w), ("abs_dD", x.dD.abs().to_numpy(), w), ("ratio", x.ratio.to_numpy()[de], w[de])):
                for q, lab in ((0.1, "q10"), (0.5, "median"), (0.9, "q90")):
                    r[f"{key}_{lab}_w"] = own_wq(vals, ww, q)
                r[f"{key}_median_unw"] = float(np.median(vals)) if len(vals) else np.nan
            if tm == "3y":
                same = np.sign(x.D.to_numpy()) == np.sign(x.D_M.to_numpy())
                r["same_sign_w"] = float((w * same).sum() / w.sum())
                r["same_sign_unw"] = float(same.mean())
            rows.append(r)
    return pd.DataFrame(rows)


def own_convergence(regions, read_maps):
    ok = regions[(regions.threshold == 100.0) & (regions.status == "ok")].sort_values("perm_rank").head(3)
    rows = []
    for _, row in ok.iterrows():
        br, bm, h = read_maps(row.HARPNUM, row.T_REC)
        ing = own_ingredients(br, bm, h, 100.0)
        for rep in ("M", "B_point"):
            res = {}
            for lab, n, half in (("ref", 400, False), ("N800", 800, False), ("dt_half", 400, True)):
                m = Model(*REF, n=n)
                if half:
                    m.dt = min(DAY, 0.5 * 0.9 * 2.0 / float(np.max(-np.diag(m.L))))
                prof = m.deposit(ing["s"], ing["F"])[0] if rep == "M" else \
                    m.deposit(np.sin(np.radians([ing["lat_pos"], ing["lat_neg"]])), np.array([ing["phibar"], -ing["phibar"]]))[0]
                res[lab] = [float(m.dip(B)[0]) for B in m.evolve_many(prof[:, None], [t for _, t in TIMES])]
            for fine in ("N800", "dt_half"):
                for (tl, _), dc, df in zip(TIMES, res["ref"], res[fine]):
                    c = abs(df - dc) / max(abs(df), 1e-6 * ing["D_scale"])
                    rows.append(dict(HARPNUM=row.HARPNUM, representation=rep, refinement=fine, time=tl, D_ref=dc, D_fine=df, criterion=c, passes=bool(c <= 1e-3)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- comparison and check

def frames_match(a, b, key, tol=1e-9):
    if set(a.columns) != set(b.columns):
        return False, f"columns {sorted(set(a.columns) ^ set(b.columns))[:4]}"
    if len(a) != len(b):
        return False, f"rows {len(a)} vs {len(b)}"
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
        fin = np.isfinite(xv) & np.isfinite(yv)
        scale = np.nanmax(np.abs(yv[fin])) if fin.any() else 0.0
        good = (np.isnan(xv) & np.isnan(yv)) | (fin & (np.abs(xv - yv) <= tol * np.maximum(np.abs(xv), np.abs(yv)) + 1e-12 * scale))
        if not good.all():
            return False, f"{c} ({int((~good).sum())})"
    return True, ""


def check(out=OUT, write=True, rec_dir=REC, data=None, outputs=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    real = data is None and outputs is None
    if real:
        fz = json.loads(FREEZE.read_text())
        meta = json.loads((Path(out) / "META.json").read_text())
        ok("frozen protocol pinned, receipt inputs unchanged", sha(PROTOCOL) == fz["sha256"] == PIN == meta.get("protocol_sha256")
           and all(sha(ROOT / p) == h for p, h in fz["inputs_sha256"].items()))
        ok("products: exact set and hashes", {p.name for p in Path(out).iterdir()} == PRODUCTS
           and all(sha(Path(out) / n) == h for n, h in meta["products_sha256"].items()) and set(meta["products_sha256"]) == PRODUCTS - {"META.json"})
        blob = subprocess.run(["git", "show", f"{meta['git_head']}:scripts/sft_map_bipole_pilot.py"], cwd=ROOT, capture_output=True)
        ok("run: script equal to the blob at the run HEAD; catalogue unchanged", hashlib.sha256(blob.stdout).hexdigest() == meta["script_sha256"]
           and meta["catalogue_sha256"] == sha(CATALOGUE) and meta["seed"] == SEED)
        if not all(c["ok"] for c in checks):
            return _finish(checks, real, write, rec_dir, out)
        rd = lambda n: pd.read_csv(Path(out) / n, low_memory=False, float_precision="round_trip")          # noqa: E731
        outputs = {k: rd(f) for k, f in (("SAMPLE", "SAMPLE.csv"), ("CELLS", "CELLS.csv"), ("REGIONS", "REGIONS.csv"), ("DIPOLES", "DIPOLES.csv.gz"),
                                          ("CURVES", "CURVES.csv.gz"), ("SUMMARY", "SUMMARY.csv"), ("CONVERGENCE", "CONVERGENCE.csv"))}
        cat = pd.read_csv(CATALOGUE, usecols=["HARPNUM", "T_REC", "role", "valid_bl", "family_rank", "NOAA_NUM", "USFLUX", "LAT_FWT", "d_axial_g",
                                              "d_axial_bal_g", "d_cm", "tilt_deg"], low_memory=False)

        def reader(harp, t_rec):
            spec = importlib.util.find_spec("sharpbl.download_records")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            folder, stem = mod.record_dir(ROOT / "data/sharp/fits", t_rec), mod.file_stem(int(harp), t_rec)
            br, h = geo.read_sharp(folder / f"{stem}.Br.fits")
            bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
            return br, bm, h
        data = (cat, reader)
    cat, reader = data
    samp, cells, regions, dips, curves, _ = own_all(cat, reader, curves=len(outputs["CURVES"]) > 0)
    th = outputs["SAMPLE"]
    common = [c for c in samp.columns if c in th.columns]
    g1 = frames_match(th[common], samp[common], ["HARPNUM"])
    ok("SAMPLE: same HARPs, strata, permutation ranks, N, n, pi and weights", g1[0] and len(th) == len(samp), g1[1])
    ok("CELLS: population counts per cell", frames_match(outputs["CELLS"], cells, ["multiplicity", "flux_class", "lat_band"])[0])
    g = frames_match(outputs["REGIONS"], regions, ["HARPNUM", "threshold"])
    ok("REGIONS: statuses, fluxes, centroids, balancing, pixel dipoles, deposit statuses, Gaussian effective quantities", g[0], g[1])
    g = frames_match(outputs["DIPOLES"], dips, ["HARPNUM", "threshold", "representation", "transport", "time"])
    ok("DIPOLES: every representation, threshold, transport, tau factor and time (propagator matrices vs step loop)", g[0], g[1])
    if len(outputs["CURVES"]):
        g = frames_match(outputs["CURVES"], curves, ["HARPNUM", "representation", "t_day"])
        ok("CURVES: daily reference curves", g[0], g[1])
    g = frames_match(outputs["SUMMARY"], own_summary(outputs["REGIONS"], outputs["DIPOLES"]), ["representation", "threshold", "transport", "time", "group"])
    ok("SUMMARY: weighted and unweighted quantiles, ratio threshold, same-sign fractions", g[0], g[1])
    oc = own_convergence(regions, reader)
    kc = ["HARPNUM", "representation", "refinement", "time"]
    tc = outputs["CONVERGENCE"]
    g = frames_match(tc.drop(columns=["criterion"]), oc.drop(columns=["criterion"]), kc)
    # the criterion is a relative difference of two nearly equal dipoles: compared with an absolute tolerance 1e-8
    # (five orders below the 1e-3 rule); the pass/fail flag must be identical
    cm = tc.sort_values(kc).criterion.to_numpy(float) - oc.sort_values(kc).criterion.to_numpy(float) if len(tc) == len(oc) else np.array([np.inf])
    ok("CONVERGENCE: refinements, dipoles, pass flags; criterion within 1e-8 absolute", g[0] and np.abs(cm).max() <= 1e-8,
       g[1] or f"max criterion gap {np.abs(cm).max():.1e}")
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
        prods, _ = Rn.build(cat, reader, curves=False)
        outs = {k: v.copy() for k, v in prods.items()}
        with tempfile.TemporaryDirectory() as t2:                                      # CSV round trip
            for k, v in outs.items():
                v.to_csv(Path(t2) / f"{k}.csv", index=False)
            rt = {k: (pd.read_csv(Path(t2) / f"{k}.csv", low_memory=False, float_precision="round_trip") if len(outs[k]) else outs[k]) for k in outs}

        def quiet(o):
            with contextlib.redirect_stdout(io.StringIO()):
                return check(write=False, data=(cat, reader), outputs=o)
        ok("synthetic run recounted in full (own propagators, Gaussians, summaries)", quiet(rt))

        def tamper(name, key, fn):
            o = dict(rt)
            o[key] = fn(rt[key].copy())
            got = quiet(o)
            res.append(not got)
            print(f"[{'OK' if not got else 'FALLITO'}] refused: {name}")
        i0 = rt["DIPOLES"].index[(rt["DIPOLES"].time == "3y")][0]
        tamper("a 3-year dipole moved by 1e-7 relative", "DIPOLES", lambda t: t.assign(D=t.D.where(t.index != i0, t.D * (1 + 1e-7))))
        tamper("a dipole row dropped", "DIPOLES", lambda t: t.drop(index=i0))
        tamper("a sampled HARP replaced", "SAMPLE", lambda t: t.assign(HARPNUM=t.HARPNUM.where(t.index != 0, 999)))
        tamper("a weight", "SAMPLE", lambda t: t.assign(weight=t.weight.where(t.index != 0, t.weight * 2)))
        tamper("a deposit status", "REGIONS", lambda t: t.assign(M_status=t.M_status.where(t.index != t.index[t.M_status.eq("ok")][0], "deposition_out_of_range")))
        tamper("a Gaussian effective flux", "REGIONS", lambda t: t.assign(B_gauss_2deg_eff_phi_pos=t.B_gauss_2deg_eff_phi_pos * (1 + 1e-6)))
        tamper("a weighted median", "SUMMARY", lambda t: t.assign(dD_scaled_median_w=t.dD_scaled_median_w.where(t.index != 0, 0.123)))
        tamper("a same-sign fraction", "SUMMARY", lambda t: t.assign(same_sign_w=t.same_sign_w.where(t.same_sign_w.isna() | (t.index != t.index[t.same_sign_w.notna()][0]), 0.5)))
        tamper("a convergence criterion", "CONVERGENCE", lambda t: t.assign(criterion=t.criterion.where(t.index != 0, 0.5)))
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
