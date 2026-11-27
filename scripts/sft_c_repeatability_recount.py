"""Independent recount of repeatability C (spec docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md rev. 3 + §4bis, NOT frozen).
Synthetic only: --check on real products is refused until the spec, the runner and this recount are frozen.

Own code; it imports neither scripts/sft_c_repeatability.py nor sft_observed_pilot.py, sft_local.py or sft_core.py (the
selftest uses the runner only to produce the rows to be recounted). Own pieces:
- grid (edges rounded up to cover the extent + 1 deg), exact cell areas, margins of the observed pilot (same constants
  and the same 801-point latitude grid for the maximal meridional speed, which is part of the definition);
- pixel preparations (raw, p1_source), cell coverage, the deposit stencil and the deposit (np.bincount accumulation);
- footprints G/V, C_geo and C_fin with an erosion by summed-area table (not scipy.ndimage);
- field measures (D, D_bal, fluxes, unit-vector centroids, separation, P1 tilt and leading), balancing on C_fin;
- remapping report on the full support; fine 0.03 deg grid on the children of C_fin;
- C_rot: numerical domain of dependence by boolean propagation stage by stage (not the closed form [i-4n, i+2n]) and
  the rotation-only TVD-minmod SSP-RK2 transport rewritten;
- component weights after missing values, linear and angular (axial / circular) statistics, the whole SUMMARY table of
  the runner's summarise(), component bootstrap. Not yet: the operational products of assemble() (selection, manifest,
  denominators, grouped summaries and bootstrap), to be recounted once their schema is agreed.
Declared dependencies: the P1 map reader and WCS (geometry.read_sharp, lonlat_maps, pixel_area_cm2) and the SHARP file
naming (download_records), as the A1 recount. Definitions shared with the runner by construction (they are the spec):
the rotation law (Snodgrass & Ulrich 1990, as P1d/P1e), the P1 tilt and leading convention, the margin constants.

Comparison: every key of every row; strings, statuses and integer counts exact; floats relative 1e-9 plus 1e-12 of a
pair-level scale of their family (unsigned flux for fluxes, S_D for dipoles), 1e-9 deg absolute for angles (a
difference of two tilts amplifies the centroid round-off by ~1/separation: 1e-12 deg was too tight, first run), 1e-12
for ratios.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_c_repeatability_recount.py --selftest
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo  # noqa: E402  (declared dependency: P1 map reader and WCS)

STEP, FINE, AREA_MIN, PAD = 0.06, 0.03, 25.0, 1.0
ETA_MAX, DU_MAX, P_EXP, R_KM, R_CM = 466.8, 0.041, 2.33, 6.96e5, 6.96e10
CAP, BITMAP_MIN, THR_P1, DAY, DT_MAX = 10000.0, 33, 100.0, 86400.0, 600.0
OMEGA_C = 14.1844
SEED_BOOT, MIN_COMPONENTS = 36_300_001, 10
OBS = ("D_g", "phi_pos", "phi_neg", "phi_net", "lat_pos", "lon_pos", "lat_neg", "lon_neg", "sep_deg", "tilt_deg", "lat_mean")
REMAP = ("D_g", "D_bal_g", "phi_pos", "phi_neg", "phi_net", "lat_mean", "lat_pos", "lat_neg", "sep_deg", "lon_pos", "lon_neg")


def omega_rel(lat_deg):
    s2 = np.sin(np.radians(lat_deg)) ** 2
    return 14.713 - 2.396 * s2 - 1.787 * s2 ** 2 - OMEGA_C


def wrap(x, period):
    return (x + period / 2) % period - period / 2


def pdiff(k, a, b):
    """X(t1) - X(t0): axial for the tilt, circular for longitudes."""
    if k == "tilt_deg":
        return wrap(b - a, 180.0)
    if k.startswith("lon_"):
        return wrap(b - a, 360.0)
    return b - a


# ---------------------------------------------------------------- grid

class Grid:
    def __init__(self, lat_lo, lat_hi, lon_lo, lon_hi, step):
        ny, nx = math.ceil((lat_hi - lat_lo) / step - 1e-9), math.ceil((lon_hi - lon_lo) / step - 1e-9)
        self.step, self.ny, self.nx = step, ny, nx
        self.lat_e, self.lon_e = lat_lo + np.arange(ny + 1) * step, lon_lo + np.arange(nx + 1) * step
        self.lat, self.lon = 0.5 * (self.lat_e[:-1] + self.lat_e[1:]), 0.5 * (self.lon_e[:-1] + self.lon_e[1:])
        row = R_CM ** 2 * math.radians(step) * np.diff(np.sin(np.radians(self.lat_e)))
        self.A = np.broadcast_to(row[:, None], (ny, nx)).copy()

    def area_deg2(self, m):
        return float(self.A[m].sum()) / R_CM ** 2 * (180 / math.pi) ** 2

    def cover(self, lat, lon):
        g = np.zeros((self.ny, self.nx), bool)
        iy, ix = np.floor((lat - self.lat_e[0]) / self.step).astype(int), np.floor((lon - self.lon_e[0]) / self.step).astype(int)
        k = (iy >= 0) & (iy < self.ny) & (ix >= 0) & (ix < self.nx)
        g[iy[k], ix[k]] = True
        return g

    def _weights(self, lat, lon):
        sc, s = np.sin(np.radians(self.lat)), np.sin(np.radians(lat))
        out = (s < sc[0]) | (s > sc[-1]) | (lon < self.lon[0]) | (lon > self.lon[-1])
        s, lo = s[~out], lon[~out]
        iy = np.minimum(np.maximum(np.searchsorted(sc, s, side="right") - 1, 0), self.ny - 2)
        ix = np.minimum(np.maximum(np.searchsorted(self.lon, lo, side="right") - 1, 0), self.nx - 2)
        wy, wx = (s - sc[iy]) / (sc[iy + 1] - sc[iy]), (lo - self.lon[ix]) / (self.lon[ix + 1] - self.lon[ix])
        corners = [(iy + dy, ix + dx, fy * fx) for dy, fy in ((0, 1 - wy), (1, wy)) for dx, fx in ((0, 1 - wx), (1, wx))]
        return corners, out

    def stencil(self, lat, lon):
        corners, out = self._weights(lat, lon)
        m = np.zeros((self.ny, self.nx), bool)
        for iy, ix, w in corners:
            m[iy[w > 0], ix[w > 0]] = True
        return m, int(out.sum())

    def deposit(self, lat, lon, flux):
        corners, out = self._weights(lat, lon)
        if out.any():
            return None
        f = flux[~out]
        F = sum(np.bincount(iy * self.nx + ix, weights=f * w, minlength=self.ny * self.nx) for iy, ix, w in corners)
        return F.reshape(self.ny, self.nx) / self.A


def margins(gap_days, lat_lo, lat_hi):
    dts = gap_days * DAY
    dif = math.degrees(math.sqrt(4 * ETA_MAX * dts) / R_KM)
    lr = np.radians(np.linspace(0, 80, 801))
    vmax = DU_MAX * float(np.max(np.sin(lr) * np.cos(lr) ** P_EXP))
    rot = float(np.max(np.abs(omega_rel(np.linspace(lat_lo, lat_hi, 60))))) * gap_days
    latmax = max(abs(lat_lo), abs(lat_hi))
    return dif + math.degrees(vmax * dts / R_KM) + 0.5, (dif + 0.5) / math.cos(math.radians(latmax)) + rot


def erode(mask, ky, kx):
    """Cells whose whole (2ky+1) x (2kx+1) window lies in the grid and in mask (summed-area table)."""
    ny, nx = mask.shape
    S = np.zeros((ny + 1, nx + 1), int)
    S[1:, 1:] = mask.astype(int).cumsum(0).cumsum(1)
    out = np.zeros_like(mask)
    y0, y1, x0, x1 = ky, ny - ky, kx, nx - kx
    if y1 <= y0 or x1 <= x0:
        return out
    yy, xx = np.arange(y0, y1)[:, None], np.arange(x0, x1)[None, :]
    tot = S[yy + ky + 1, xx + kx + 1] - S[yy - ky, xx + kx + 1] - S[yy + ky + 1, xx - kx] + S[yy - ky, xx - kx]
    out[y0:y1, x0:x1] = tot == (2 * ky + 1) * (2 * kx + 1)
    return out


# ---------------------------------------------------------------- pixels and measures

def prepare(br, bm, h, branch, kind):
    lon, lat = geo.lonlat_maps(h, br.shape)
    lon = wrap(lon - branch, 360.0) + branch
    valid = np.isfinite(br) & (np.abs(br) <= CAP)
    pos = np.isfinite(lon) & np.isfinite(lat)
    sel = valid & pos
    if kind == "p1_source":
        sel &= np.isfinite(bm) & (bm >= BITMAP_MIN) & (np.abs(br) >= THR_P1)
    return lat[sel], lon[sel], br[sel] * geo.pixel_area_cm2(h), lat[pos], lon[pos], valid[pos]


def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def centroid(lon, lat, w):
    if len(w) == 0 or w.sum() <= 0:
        return np.nan, np.nan
    v = (unit(lon, lat) * w[:, None]).sum(0)
    v = v / np.linalg.norm(v)
    return float(np.degrees(np.arctan2(v[1], v[0]))), float(np.degrees(np.arcsin(np.clip(v[2], -1, 1))))


def tilt(lead, follow):
    a, b = unit(*lead), unit(*follow)
    m = (a + b) / np.linalg.norm(a + b)
    west = np.array([-m[1], m[0], 0.0])
    west /= np.linalg.norm(west)
    north = np.cross(m, west)
    v = b - a
    return float(np.degrees(np.arctan2(v @ north, v @ west)))


def measures(lat, lon, flux):
    """Measures of fluxes (Mx) at points; P1 tilt and leading (westmost polarity)."""
    k = 3 / (4 * math.pi * R_CM ** 2)
    sl = np.sin(np.radians(lat))
    p, n = flux > 0, flux < 0
    s = p | n
    o = dict(D_g=float(k * (flux[s] * sl[s]).sum()), phi_pos=float(flux[p].sum()), phi_neg=float(-flux[n].sum()))
    o.update(phi_net=o["phi_pos"] - o["phi_neg"], lon_pos=np.nan, lat_pos=np.nan, lon_neg=np.nan, lat_neg=np.nan, lat_mean=np.nan,
             D_bal_g=np.nan, sep_deg=np.nan, tilt_deg=np.nan, leading=0)
    if not s.any():
        return dict(o, status="empty")
    o["lat_mean"] = centroid(lon[s], lat[s], np.abs(flux[s]))[1]
    lp = centroid(lon[p], lat[p], flux[p]) if p.any() else (np.nan, np.nan)
    ln = centroid(lon[n], lat[n], -flux[n]) if n.any() else (np.nan, np.nan)
    o.update(lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1])
    if not (p.any() and n.any()):
        return dict(o, status="one_polarity")
    pb = 0.5 * (o["phi_pos"] + o["phi_neg"])
    msp, msn = (flux[p] * sl[p]).sum() / o["phi_pos"], (-flux[n] * sl[n]).sum() / o["phi_neg"]
    lead = 1 if abs(tilt(ln, lp)) < 90.0 else -1
    a, b = (lp, ln) if lead == 1 else (ln, lp)
    va, vb = unit(*lp), unit(*ln)
    o.update(D_bal_g=float(k * pb * (msp - msn)), sep_deg=float(np.degrees(np.arctan2(np.linalg.norm(np.cross(va, vb)), va @ vb))),
             tilt_deg=tilt(a, b), leading=lead)
    return dict(o, status="ok")


def grid_measures(g, B, m):
    LAT, LON = np.meshgrid(g.lat, g.lon, indexing="ij")
    return measures(LAT[m], LON[m], (B * g.A)[m])


def balance(B, A, m):
    a = (B * A)[m]
    pp, nn = a[a > 0].sum(), -a[a < 0].sum()
    if not (pp > 0 and nn > 0):
        return None, (np.nan, np.nan)
    pb = 0.5 * (pp + nn)
    return np.where(B > 0, B * (pb / pp), B * (pb / nn)), (pb / pp, pb / nn)


# ---------------------------------------------------------------- rotation only

class Rotation:
    def __init__(self, g):
        self.g = g
        self.u = np.radians(omega_rel(g.lat)) / DAY * R_CM * np.cos(np.radians(g.lat))
        self.lz = R_CM * math.radians(g.step)
        rate = (np.abs(self.u)[:, None] * self.lz * 2) / g.A
        self.dt = float(min(DT_MAX, 0.5 / rate.max() if rate.max() > 0 else np.inf))

    def steps(self, t):
        k = int(np.floor(t / self.dt * (1 + 1e-12)))
        return [self.dt] * k + ([t - k * self.dt] if t - k * self.dt > 1e-9 * self.dt else [])

    def adv(self, B):
        Bp = np.concatenate([B[:, :1], B, B[:, -1:]], axis=1)
        a, b = Bp[:, 1:-1] - Bp[:, :-2], Bp[:, 2:] - Bp[:, 1:-1]
        sl = np.where(a * b > 0, np.sign(a) * np.minimum(np.abs(a), np.abs(b)), 0.0)
        up = self.u[:, None] > 0
        face = np.where(up, (B + 0.5 * sl)[:, :-1], (B - 0.5 * sl)[:, 1:]) * self.u[:, None] * self.lz
        F = np.concatenate([np.zeros((self.g.ny, 1)), face, np.zeros((self.g.ny, 1))], axis=1)
        return -(F[:, 1:] - F[:, :-1]) / self.g.A

    def evolve(self, B, t):
        for h in self.steps(t):
            k1 = B + h * self.adv(B)
            B = 0.5 * (B + k1 + h * self.adv(k1))
        return B

    def dependence(self, V0, t):
        """Boolean propagation through each stage: a stage value at i depends on [i-2, i+1] (u > 0), [i-1, i+2] (u < 0),
        nothing (u = 0); positions beyond the box are not valid."""
        bad = ~V0
        pos, neg = self.u > 0, self.u < 0
        for _ in self.steps(t):
            for _stage in range(2):
                P = np.concatenate([np.ones((self.g.ny, 2), bool), bad, np.ones((self.g.ny, 2), bool)], axis=1)
                win_p = P[:, 0:-4] | P[:, 1:-3] | P[:, 2:-2] | P[:, 3:-1]      # i-2 .. i+1
                win_n = P[:, 1:-3] | P[:, 2:-2] | P[:, 3:-1] | P[:, 4:]        # i-1 .. i+2
                bad = bad | np.where(pos[:, None], win_p, np.where(neg[:, None], win_n, False))
        return bad


# ---------------------------------------------------------------- one pair

def recount_pair(read, harp, t0, t1, kinds=("raw", "p1_source", "balanced")):
    (br0, bm0, h0), (br1, bm1, h1) = read(harp, t0), read(harp, t1)
    tt = [pd.Timestamp(str(h["T_OBS"]).replace("_TAI", "").replace(".", "-", 2).replace("_", " ")) for h in (h0, h1)]
    gap = (tt[1] - tt[0]).total_seconds()
    branch = float(h0["CRVAL1"])
    ll = [geo.lonlat_maps(h, br.shape) for br, h in ((br0, h0), (br1, h1))]
    lons = [wrap(lo - branch, 360.0) + branch for lo, _ in ll]
    lats = [la for _, la in ll]
    la_lo = max(-89.0, min(np.nanmin(x) for x in lats) - PAD)
    la_hi = min(89.0, max(np.nanmax(x) for x in lats) + PAD)
    lo_lo, lo_hi = min(np.nanmin(x) for x in lons) - PAD, max(np.nanmax(x) for x in lons) + PAD
    g = Grid(la_lo, la_hi, lo_lo, lo_hi, STEP)
    m_lat, m_lon = margins(gap / DAY, g.lat_e[0], g.lat_e[-1])
    base = dict(HARPNUM=harp, T_REC_0=t0, T_REC_1=t1, gap_s=gap, m_lat=m_lat, m_lon=m_lon)
    GV, n_out = [], 0
    for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1)):
        *_, la, lo, va = prepare(br, bm, h, branch, "raw")
        G = g.cover(la, lo)
        bad = g.cover(la[~va], lo[~va]) | g.stencil(la[~va], lo[~va])[0]
        V = g.cover(la[va], lo[va]) & G & ~bad
        GV.append((G, V))
        n_out += g.stencil(la[~va], lo[~va])[1] + g.stencil(la[va], lo[va])[1]
    ky, kx = math.ceil(m_lat / STEP), math.ceil(m_lon / STEP)
    Cgeo = erode(GV[0][0], ky, kx) & GV[1][0]
    Cm = erode(GV[0][1], ky, kx) & GV[1][1]
    area = g.area_deg2(Cm)
    base.update(area_C_geo=g.area_deg2(Cgeo), area_C_fin=area, C_geo_cells=int(Cgeo.sum()), C_cells=int(Cm.sum()))
    if n_out:
        return [dict(base, kind=k, status="deposition_out_of_range", n_out=n_out) for k in kinds]
    if area < AREA_MIN:
        return [dict(base, kind=k, status="finite_coverage_insufficient") for k in kinds]
    dep, remap = {}, {}
    for kind in sorted({"raw" if k == "balanced" else k for k in kinds}):
        pair, rm = [], {}
        for j, (br, bm, h) in enumerate(((br0, bm0, h0), (br1, bm1, h1))):
            la, lo, F, *_ = prepare(br, bm, h, branch, kind)
            B = g.deposit(la, lo, F)
            pair.append(B)
            pm, gm = measures(la, lo, F), grid_measures(g, B, np.ones((g.ny, g.nx), bool))
            rm.update({f"remap{j}_{k}": (wrap(gm[k] - pm[k], 360.0) if k.startswith("lon_") else gm[k] - pm[k]) for k in REMAP})
        dep[kind], remap[kind] = pair, rm
    # fine grid on the children of C_fin
    f = Grid(g.lat_e[0], g.lat_e[-1], g.lon_e[0], g.lon_e[-1], FINE)
    Cf = np.zeros((f.ny, f.nx), bool)
    Cf[:2 * g.ny, :2 * g.nx] = np.repeat(np.repeat(Cm, 2, 0), 2, 1)[:f.ny, :f.nx]
    taint, f_out = np.zeros((f.ny, f.nx), bool), 0
    for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1)):
        *_, la, lo, va = prepare(br, bm, h, branch, "raw")
        st, o1 = f.stencil(la[~va], lo[~va])
        taint |= f.cover(la[~va], lo[~va]) | st
        f_out += o1 + f.stencil(la[va], lo[va])[1]
    f_bad = int((Cf & taint).sum())
    fine = dict(fine_status="fine_deposition_out_of_range" if f_out else ("fine_support_invalid" if f_bad else "ok"),
                fine_cells_invalid=f_bad, area_fine=f.area_deg2(Cf))
    fdep = {k: [f.deposit(*prepare(br, bm, h, branch, k)[:3]) for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1))] for k in dep} \
        if fine["fine_status"] == "ok" else {}
    rot = Rotation(g)
    Crot = Cm & ~rot.dependence(GV[0][1], gap)
    area_rot = g.area_deg2(Crot)
    rot_ok = area_rot >= AREA_MIN
    out = []
    for kind in kinds:
        rec = dict(base, kind=kind, **remap["raw" if kind == "balanced" else kind], **fine)
        if kind == "balanced":
            (B0, f0), (B1, f1) = balance(dep["raw"][0], g.A, Cm), balance(dep["raw"][1], g.A, Cm)
            if B0 is None or B1 is None:
                out.append(dict(rec, status="balance_polarity_missing"))
                continue
            rec.update(bal_fpos_0=f0[0], bal_fneg_0=f0[1], bal_fpos_1=f1[0], bal_fneg_1=f1[1])
        else:
            B0, B1 = dep[kind]
        m0, m1 = grid_measures(g, B0, Cm), grid_measures(g, B1, Cm)
        u0, u1 = float(np.abs(B0 * g.A)[Cm].sum()), float(np.abs(B1 * g.A)[Cm].sum())
        sd = 3.0 * u0 / (8.0 * math.pi * R_CM ** 2)
        rec.update(status="ok", S_D=sd, phi_uns_0=u0, phi_uns_1=u1, d_phi_uns=u1 - u0, d_dD_over_SD=(m1["D_g"] - m0["D_g"]) / sd if sd > 0 else np.nan,
                   status_0=m0["status"], status_1=m1["status"], leading_0=m0["leading"], leading_1=m1["leading"],
                   leading_change=bool(m0["leading"] != m1["leading"]) if m0["status"] == m1["status"] == "ok" else np.nan,
                   **{f"x0_{k}": m0[k] for k in OBS}, **{f"x1_{k}": m1[k] for k in OBS}, **{f"d_{k}": pdiff(k, m0[k], m1[k]) for k in OBS},
                   area_C_rot=area_rot, area_lost_rot=area - area_rot, rot_status="ok" if rot_ok else "rot_coverage_insufficient")
        if rot_ok:
            mr, a0, a1 = grid_measures(g, rot.evolve(B0, gap), Crot), grid_measures(g, B0, Crot), grid_measures(g, B1, Crot)
        rec.update({f"drot_{k}": pdiff(k, mr[k], a1[k]) if rot_ok else np.nan for k in OBS})
        rec.update({f"dpers_rot_{k}": pdiff(k, a0[k], a1[k]) if rot_ok else np.nan for k in OBS})
        if fine["fine_status"] == "ok":
            if kind == "balanced":
                (F0, _), (F1, _) = balance(fdep["raw"][0], f.A, Cf), balance(fdep["raw"][1], f.A, Cf)
            else:
                F0, F1 = fdep[kind]
            if F0 is None or F1 is None:
                rec["fine_kind_status"] = "balance_polarity_missing"
            else:
                n0, n1 = grid_measures(f, F0, Cf), grid_measures(f, F1, Cf)
                rec.update(fine_kind_status="ok", **{f"fine_x0_{k}": n0[k] for k in OBS}, **{f"fine_x1_{k}": n1[k] for k in OBS})
                for k in OBS:
                    rec[f"fine_d_{k}"] = pdiff(k, n0[k], n1[k])
                    rec[f"grid_dd_{k}"] = pdiff(k, pdiff(k, m0[k], m1[k]), rec[f"fine_d_{k}"])
        out.append(rec)
    return out


# ---------------------------------------------------------------- comparison

EXACT_INT = ("C_cells", "C_geo_cells", "fine_cells_invalid", "n_out", "leading_0", "leading_1", "HARPNUM")


def family_scale(key, sc):
    """sc: pair-level scales (max over the rows of the pair: the raw row carries them even when a variant failed)."""
    if "phi" in key:
        return max(sc["phi"], 1.0)
    if "D_g" in key or "D_bal" in key or key == "S_D":
        return max(sc["D"], 1e-300)
    if any(t in key for t in ("lat", "lon", "sep", "tilt")):
        return 1e3              # degrees: 1e-9 deg absolute (differences of angles amplify centroid round-off ~1/sep)
    return 1.0


SCALAR = (str, bool, int, float, np.bool_, np.integer, np.floating, type(None))


def rows_match(theirs, ours):
    """(ok, first difference). Exact key set; only scalar values (a list or dict is a refusal with its reason);
    strings, statuses and integer counts exact (a boolean is not a count); floats relative 1e-9 plus 1e-12 of the
    family scale."""
    if len(theirs) != len(ours):
        return False, f"rows {len(theirs)} vs {len(ours)}"
    num = lambda r, k: abs(float(r[k])) if isinstance(r.get(k), (int, float)) and np.isfinite(float(r[k])) else 0.0   # noqa: E731
    sc = dict(phi=max([num(r, "phi_uns_0") for r in ours] + [0.0]), D=max([num(r, "S_D") for r in ours] + [0.0]))
    for a, b in zip(theirs, ours):
        if set(a) != set(b):
            return False, f"keys {sorted(set(a) ^ set(b))[:4]} ({a.get('kind')})"
        for k in a:
            x, y = a[k], b[k]
            if not (isinstance(x, SCALAR) and isinstance(y, SCALAR)):
                return False, f"{k}: non-scalar value ({type(x).__name__} / {type(y).__name__})"
            if isinstance(x, str) or isinstance(y, str):
                if x != y:
                    return False, f"{k}: {x!r} vs {y!r}"
                continue
            if k in EXACT_INT and (isinstance(x, (bool, np.bool_)) or isinstance(y, (bool, np.bool_))):
                return False, f"{k}: a boolean is not a count ({x!r} vs {y!r})"
            if k in EXACT_INT or k == "leading_change":
                xn, yn = (x is None or (isinstance(x, float) and np.isnan(x))), (y is None or (isinstance(y, float) and np.isnan(y)))
                if xn != yn or (not xn and (float(x) != float(y) or float(x) != round(float(x)))):
                    return False, f"{k} (exact): {x!r} vs {y!r}"
                continue
            x, y = float(x), float(y)
            if np.isnan(x) and np.isnan(y):
                continue
            tol = 1e-9 * max(abs(x), abs(y)) + 1e-12 * family_scale(k, sc)
            if not (np.isfinite(x) and np.isfinite(y) and abs(x - y) <= tol):
                return False, f"{k} ({a.get('kind')}): {x!r} vs {y!r}"
    return True, ""


# ---------------------------------------------------------------- summaries

def weights(comp, x):
    fin = np.isfinite(x)
    w = np.zeros(len(x))
    ids, inv, cnt = np.unique(comp[fin], return_inverse=True, return_counts=True)
    w[fin] = 1.0 / (len(ids) * cnt[inv])
    return w, len(ids)


def wq(x, w, q):
    k = np.isfinite(x)
    x, w = x[k], w[k]
    if not len(x):
        return np.nan
    o = np.argsort(x, kind="mergesort")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][int(np.argmax(c >= q - 1e-12))])


def lin_stats(x, w):
    k = np.isfinite(x)
    x, w = x[k], w[k]
    if not len(x):
        return dict(n=0)
    m = float((w * x).sum() / w.sum())
    med = wq(x, w, 0.5)
    return dict(n=int(len(x)), mean=m, median=med, q10=wq(x, w, 0.1), q90=wq(x, w, 0.9),
                rms_centred=math.sqrt(float((w * (x - m) ** 2).sum() / w.sum())), median_abs=wq(np.abs(x), w, 0.5),
                mad_scaled=1.4826 * wq(np.abs(x - med), w, 0.5), second_moment=float((w * x * x).sum() / w.sum()))


def ang_stats(x, w, kind):
    k = np.isfinite(x)
    x, w = x[k], w[k]
    if not len(x):
        return dict(n=0)
    m = 2.0 if kind == "axial" else 1.0
    c, s_ = (w * np.cos(m * np.radians(x))).sum() / w.sum(), (w * np.sin(m * np.radians(x))).sum() / w.sum()
    r = math.hypot(c, s_)
    sd = math.degrees(math.sqrt(-2.0 * math.log(r))) / m if 0 < r < 1 else (0.0 if r == 1 else np.nan)
    return dict(n=int(len(x)), resultant=r, mean=math.degrees(math.atan2(s_, c)) / m if r > 0 else np.nan,
                median_abs=wq(np.abs(x), w, 0.5), q90_abs=wq(np.abs(x), w, 0.9), circ_sd=sd)


LIN_Q = ("D_g", "phi_pos", "phi_neg", "phi_net", "phi_uns", "lat_pos", "lat_neg", "sep_deg", "lat_mean", "dD_over_SD")
ANG_Q = (("tilt_deg", "axial"), ("lon_pos", "circular"), ("lon_neg", "circular"))


def own_summary(df, components):
    """The whole SUMMARY of one preparation, own code: rows (diff, quantity) for d_, drot_, dpers_rot_."""
    comp = df.pair_key.map(components)
    if comp.isna().any():
        raise ValueError("pair_key without component")
    comp = comp.to_numpy()
    rows = []
    for pre in ("d_", "drot_", "dpers_rot_"):
        for q in LIN_Q:
            if pre != "d_" and q in ("dD_over_SD", "phi_uns"):
                continue
            col = {"dD_over_SD": "d_dD_over_SD", "phi_uns": "d_phi_uns"}.get(q, f"{pre}{q}")
            if col not in df:
                continue
            x = df[col].to_numpy(float)
            w, ke = weights(comp, x)
            fx = x[np.isfinite(x)]
            rows.append(dict(diff=pre[:-1], quantity=q, n_components=ke, n_missing=int(len(x) - len(fx)), **lin_stats(x, w),
                             unweighted_median=float(np.median(fx)) if len(fx) else np.nan))
        for q, kind in ANG_Q:
            x = df[f"{pre}{q}"].to_numpy(float)
            w, ke = weights(comp, x)
            rows.append(dict(diff=pre[:-1], quantity=q, n_components=ke, n_missing=int((~np.isfinite(x)).sum()), **ang_stats(x, w, kind)))
    return pd.DataFrame(rows)


def summary_match(theirs, ours):
    if set(theirs.columns) != set(ours.columns) or len(theirs) != len(ours):
        return False, f"columns/rows {sorted(set(theirs.columns) ^ set(ours.columns))[:4]} {len(theirs)} vs {len(ours)}"
    a = theirs.sort_values(["diff", "quantity"]).reset_index(drop=True)
    b = ours[list(a.columns)].sort_values(["diff", "quantity"]).reset_index(drop=True)
    # scales by unit: statistics in the unit U of the quantity share one row scale; second_moment is in U^2 and uses
    # its square; resultant is dimensionless (Codex: a 1e40 Mx^2 second moment must not hide a flux mean set to 0)
    ucols = [c for c in ("mean", "median", "q10", "q90", "rms_centred", "median_abs", "mad_scaled", "unweighted_median", "q90_abs",
                         "circ_sd") if c in b.columns]
    row_scale = np.nan_to_num(np.nanmax(np.abs(b[ucols].to_numpy(float)), axis=1, initial=0.0)) if ucols else np.zeros(len(b))
    for c in a.columns:
        x, y = a[c], b[c]
        if c in ("diff", "quantity"):
            if not (x == y).all():
                return False, c
            continue
        xv, yv = x.to_numpy(float), y.to_numpy(float)
        if c in ("n", "n_components", "n_missing"):
            if not ((np.isnan(xv) == np.isnan(yv)).all() and (xv[~np.isnan(xv)] == yv[~np.isnan(yv)]).all()):
                return False, f"{c} (count)"
            continue
        # absolute tolerance in degrees only on rows of angular quantities: 1e-9 deg; circ_sd = sqrt(-2 ln r) is
        # ill-conditioned as r -> 1 (an error of ~1e-16 on r gives up to sqrt(2e-16) rad ~ 8e-7 deg): 2e-6 deg
        angular = a.quantity.isin(["lat_pos", "lon_pos", "lat_neg", "lon_neg", "sep_deg", "tilt_deg", "lat_mean"]).to_numpy()
        deg = np.where(angular, 2e-6 if c == "circ_sd" else 1e-9, 0.0) if c not in ("resultant",) else 0.0
        scale = 1.0 if c == "resultant" else (row_scale ** 2 if c == "second_moment" else row_scale)
        good = (np.isnan(xv) & np.isnan(yv)) | (np.abs(xv - yv) <= 1e-9 * np.maximum(np.abs(xv), np.abs(yv)) + 1e-12 * scale + deg)
        if not good.all():
            return False, f"{c} ({int((~good).sum())})"
    return True, ""


def boot(comp, x, seed, n):
    fin = np.isfinite(x)
    ids = np.unique(comp[fin])
    rng = np.random.default_rng(seed)
    if len(ids) < MIN_COMPONENTS:
        return np.nan, np.nan, len(ids)
    members = [np.flatnonzero(fin & (comp == c)) for c in ids]
    vals = []
    for _ in range(n):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([members[int(np.searchsorted(ids, c))] for c in pick])
        wi = np.concatenate([np.full(len(members[int(np.searchsorted(ids, c))]), 1.0 / len(members[int(np.searchsorted(ids, c))])) for c in pick])
        m = (wi * x[idx]).sum() / wi.sum()
        vals.append(math.sqrt((wi * (x[idx] - m) ** 2).sum() / wi.sum()))
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975)), len(ids)


# ---------------------------------------------------------------- selftest (synthetic only)

def selftest():
    import tempfile
    sys.path.insert(0, str(ROOT / "scripts"))
    import sft_c_repeatability as CR                      # only to produce the rows to recount
    import sft_c_repeatability_selftest as T              # synthetic CEA patches
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:220]}")

    t0 = pd.Timestamp("2014-05-01 10:00:00")
    hole = lambda fld: (lambda lon, lat: np.where(np.arange(lon.size).reshape(lon.shape) == 99 * lon.shape[1] + 149, np.nan, fld(lon, lat)))  # noqa: E731
    cases = [("identical", 1, 15.0, 120.0, T.bipole(15.0, 120.0), T.bipole(15.0, 120.0), 1.0, {}),
             ("rotation 2 h at 40 deg", 2, 40.0, 200.0, T.bipole(40.0, 200.0),
              T.bipole(40.0, 200.0, dlon=float(omega_rel(40.0)) * 2 / 24), 2.0, dict(ny=299, nx=399)),
             ("one polarity", 3, 20.0, 300.0, T.bipole(20.0, 300.0, one=True), T.bipole(20.0, 300.0, one=True), 1.0, {}),
             ("small patch", 4, 10.0, 10.0, T.bipole(10.0, 10.0), T.bipole(10.0, 10.0), 1.0, dict(ny=49, nx=49)),
             ("NaN pixel at t0", 6, 15.0, 120.0, hole(T.bipole(15.0, 120.0)), T.bipole(15.0, 120.0), 1.0, {}),
             ("negative outside C_fin", 8, 15.0, 140.0, T.with_edge_negative(T.bipole(15.0, 140.0, one=True)),
              T.with_edge_negative(T.bipole(15.0, 140.0, one=True)), 1.0, {}),
             ("extra negative outside C_fin", 9, 15.0, 160.0, T.with_edge_negative(T.bipole(15.0, 160.0)),
              T.with_edge_negative(T.bipole(15.0, 160.0)), 1.0, {})]
    with tempfile.TemporaryDirectory() as td:
        read = CR.OP.reader(Path(td) / "fits")
        theirs_all = {}
        for name, harp, lat0, lon0, f0, f1, hours, kw in cases:
            a = T.write_patch(td, harp, t0, lat0, lon0, f0, **kw)
            b = T.write_patch(td, harp, t0 + pd.Timedelta(hours=hours), lat0, lon0, f1, **kw)
            theirs, ours = CR.measure_pair(read, harp, a, b), recount_pair(read, harp, a, b)
            g = rows_match(theirs, ours)
            ok(f"pair recounted ({name}): every key of the three preparations", g[0],
               g[1] or f"statuses {[r['status'] for r in ours]}, rot {[r.get('rot_status') for r in ours][:1]}, fine {ours[0].get('fine_status')}")
            theirs_all[name] = theirs
        # whole SUMMARY recounted on the measured rows (ok rows of each preparation; two pairs share a component)
        comps = {}
        for name, rows in theirs_all.items():
            for r in rows:
                r["pair_key"] = f"{r['HARPNUM']}|{r['T_REC_0']}"
                comps[r["pair_key"]] = r["HARPNUM"] if r["HARPNUM"] != 9 else 8
        comps = pd.Series(comps)
        for kind in ("raw", "p1_source", "balanced"):
            okr = pd.DataFrame([r for rows in theirs_all.values() for r in rows if r["kind"] == kind and r["status"] == "ok"])
            g = summary_match(CR.summarise(okr, comps), own_summary(okr, comps))
            ok(f"SUMMARY ({kind}): every row and column of the runner's summarise() incl. axial and circular statistics", g[0],
               g[1] or f"{len(okr)} pairs")
            if kind == "raw":
                tam = CR.summarise(okr, comps)
                i0 = tam.index[tam["mean"].notna() & (tam["mean"] != 0)][0]
                tam.loc[i0, "mean"] *= 1 + 1e-6
                ok("refused: one SUMMARY weighted mean moved by 1e-6 relative", not summary_match(tam, own_summary(okr, comps))[0])
        # Codex counterexample: a flux mean of 1e20 Mx set to 0 next to a second moment of 1e40 Mx^2 must be refused
        one = pd.DataFrame([dict(diff="d", quantity="phi_pos", n=5, n_components=4, n_missing=0, mean=1e20, median=1e20, q10=5e19, q90=2e20,
                                 rms_centred=3e19, median_abs=1e20, mad_scaled=2e19, second_moment=1e40, unweighted_median=1e20)])
        ok("refused: a flux mean of 1e20 Mx set to 0 with a second moment of 1e40 Mx^2 (scales by unit)",
           not summary_match(one.assign(mean=0.0), one)[0] and summary_match(one.copy(), one)[0])
        # refusals: one value, one status, one key, one count
        base = theirs_all["rotation 2 h at 40 deg"]
        ours = [dict(r) for r in base]
        for lab, fn in (("a 3-decimal change of d_lon_pos (1e-6 relative)", lambda r: r.__setitem__("d_lon_pos", r["d_lon_pos"] * (1 + 1e-6))),
                        ("a status", lambda r: r.__setitem__("rot_status", "rot_coverage_insufficient")),
                        ("a key dropped (remap0_phi_pos)", lambda r: r.pop("remap0_phi_pos")),
                        ("a count (C_cells + 1)", lambda r: r.__setitem__("C_cells", r["C_cells"] + 1)),
                        ("a fractional count (C_cells + 0.5)", lambda r: r.__setitem__("C_cells", r["C_cells"] + 0.5)),
                        ("a balancing factor (1e-7 relative)", lambda r: r.__setitem__("bal_fpos_0", r.get("bal_fpos_0", 1.0) * (1 + 1e-7))),
                        ("a count given as a boolean (C_cells = True)", lambda r: r.__setitem__("C_cells", True)),
                        ("a list value", lambda r: r.__setitem__("d_lon_pos", [r["d_lon_pos"]])),
                        ("a dict value", lambda r: r.__setitem__("status", {"s": "ok"}))):
            t = [dict(r) for r in base]
            fn(t[2] if "balancing" in lab else t[0])
            if "boolean" in lab:
                ours_b = [dict(r) for r in ours]
                ours_b[0]["C_cells"], t[0]["C_cells"] = 1, True                # Codex case: True against the expected 1
                got = rows_match(t, ours_b)
            else:
                got = rows_match(t, ours)
            ok(f"refused: {lab}", not got[0], got[1])
    # summaries: weights after missing values and bootstrap, against the runner's functions
    rng = np.random.default_rng(5)
    n = 40
    df = pd.DataFrame(dict(pair_key=[f"p{i}" for i in range(n)], d_D_g=np.where(np.arange(n) % 9 == 4, np.nan, rng.normal(0, 1, n))))
    comps = pd.Series({f"p{i}": i // 3 for i in range(n)})
    comp = df.pair_key.map(comps).to_numpy()
    x = df.d_D_g.to_numpy()
    w, ke = weights(comp, x)
    w_r, ke_r = CR.component_weights(comp, x)
    lin = CR.linear_stats(x, w_r)
    mine = dict(mean=float((w[np.isfinite(x)] * x[np.isfinite(x)]).sum()), median=wq(x, w, 0.5), q10=wq(x, w, 0.1), q90=wq(x, w, 0.9))
    ok("summaries: weights 1/(K_eval n_finite), weighted mean and lower quantiles = runner",
       ke == ke_r and np.allclose(w, w_r, rtol=1e-14, atol=0) and all(abs(mine[k] - lin[k]) <= 1e-12 for k in mine), f"K_eval {ke}")
    lo, hi, kb = boot(comp, x, SEED_BOOT, 400)
    br = CR.bootstrap(df, comps, "d_D_g", np.random.default_rng(SEED_BOOT), n=400)
    ok("bootstrap over evaluable components, same seed: interval = runner", kb == br["n_components"] and abs(lo - br["lo"]) <= 1e-12
       and abs(hi - br["hi"]) <= 1e-12, f"[{lo:.6f}, {hi:.6f}] vs [{br['lo']:.6f}, {br['hi']:.6f}]")
    # C_rot: closed form of the runner vs own stage-by-stage propagation, both signs of the velocity, final short step
    g = Grid(20.0, 45.0, 100.0, 106.0, STEP)
    V0 = np.ones((g.ny, g.nx), bool)
    V0[100:104, 40:43] = V0[300:302, 70:71] = V0[:, :2] = False
    from sharpbl import sft_local as L                    # the runner's box, only as the object under check
    box = L.LocalBox((g.lat_e[0], g.lat_e[-1]), (g.lon_e[0], g.lon_e[-1]), STEP, meridional=False, diffusion=False)
    same = all(np.array_equal(CR.rotation_dependence(box, V0, t), Rotation(g).dependence(V0, t)) for t in (0.0, 1800.0, 3600.0, 7000.0))
    B = np.random.default_rng(9).normal(0, 50, (g.ny, g.nx))
    ev = np.max(np.abs(box.evolve(B, 7000.0) - Rotation(g).evolve(B, 7000.0))) / np.max(np.abs(B))
    ok("C_rot: runner closed form [i-4n, i+2n] = own stage-by-stage propagation (t 0, 0.5 h, 1 h, 7000 s); own transport = runner",
       same and ev <= 1e-12 and Rotation(g).dt == box.dt, f"transport max rel diff {ev:.1e}, dt {Rotation(g).dt:.1f} vs {box.dt:.1f}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    gr = ap.add_mutually_exclusive_group(required=True)
    gr.add_argument("--selftest", action="store_true")
    gr.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        sys.exit("repeatability C recount: the spec, the runner and this recount are not frozen; --check refused")
    sys.exit(0 if selftest() else 1)
