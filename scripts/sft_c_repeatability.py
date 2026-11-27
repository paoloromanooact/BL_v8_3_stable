"""Repeatability C (draft rev. 3, NOT frozen): observed short-lag differences of the SFT observables. Synthetic only.

Spec: docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md. This file implements the measurement and the summaries on synthetic
CEA patches; --run is refused until the spec is frozen (no pixel of the real pairs is read here).
- Pairs: consecutive local records of one HARP with 0 < Delta T_OBS <= 7200 s (selection and graph from the metadata
  closure, Codex bb23d3e); every listed pair is measured, no replacement on failure.
- Grid 0.06 deg on the branch of the first CRVAL1; bounds = extent of the WCS centres of BOTH patches +- 1 deg.
- Footprints per instant (revised after Codex b26c357, point 1): G = cells containing a pixel centre (any Br); V = cells
  of G that contain a valid centre (finite Br, |Br| <= 10000 G) and receive NO deposit weight from an invalid pixel
  (the effective stencil of LocalBox.deposit: linear weights between neighbouring cell centres). Invalid pixels are
  never deposited, so no zero is imputed as data, and a cell mixing valid and invalid centres is not observed.
  C_geo = erode(G0) & G1 (reported); C_fin = erode(V0) & V1, with the directional margins of the observed pilot at the
  largest diffusion/velocity of its grid (466.8 km^2/s, Du 0.041 km/s, p 2.33) and the real Delta T_OBS. The erosion of
  V0 (not only of G0) is an implementation choice: an invalid hole at t0 is treated like an edge of the observed
  region. area(C_fin) < 25 deg^2 -> finite_coverage_insufficient. C_fin is the same for every preparation.
- Preparations: raw (all valid pixels, main), p1_source (bitmap >= 33, |Br| >= 100 G), balanced (point 2): the raw
  deposited field with its two polarities rescaled by factors computed ON C_fin at each instant and applied to the whole
  box; status balance_polarity_missing if a polarity is empty on C_fin at either instant (raw is not affected).
- Observables on C_fin at t0 and t1 (LocalBox.measures): D_g, fluxes, centroids, separation, tilt, mean latitude,
  plus unsigned and net flux; differences X(t1) - X(t0) (axial for the tilt, circular for longitudes); dD / S_D with
  S_D = 3 Phi_unsigned(t0)/(8 pi R^2). Leading change (point 3) from the P1 convention returned by measures
  (`leading`, westmost polarity, periodic), defined only if both instants have both polarities (else NaN).
- Secondary (predefined): rotation only, with the effective transport (LocalBox.evolve, rotation only). C_rot (point 5)
  = C_fin minus every cell whose NUMERICAL domain of dependence over the gap touches a cell outside V0: per step of the
  TVD-minmod SSP-RK2 scheme a cell depends on 4 cells upstream and 2 downstream (rows with omega - omega_C = 0: none),
  so after n steps on [i - 4n, i + 2n] (mirrored for the other sign); cells beyond the box count as not valid. This is
  the exact support of the scheme, not a sub-point rule: there is no partial coverage. It is much wider than the
  physical displacement (n <= 12 at 2 h: up to 48 cells, 2.9 deg upstream), so C_rot < C_fin in general and multi-day
  gaps leave it empty. Persistence and rotation-only differences are both recomputed on C_rot; the main C_fin is
  unchanged. area(C_rot) < 25 deg^2 -> rot_status rot_coverage_insufficient.
- Summaries (point 4): for each quantity, the target is a component drawn among those with at least one finite value,
  then one of its pairs with a finite value: weights 1/(K_eval n_finite(component)), 0 for missing values. Mean,
  median, q10/q90, centred RMS, scaled MAD; circular statistics for the angles; lag classes (0, 1.5 h] and (1.5, 2 h];
  hemispheres; USFLUX(t0) metadata terciles; component bootstrap (2000 replicates, seed 36_300_001) over the
  evaluable components with the same weights; no interval with fewer than 10 evaluable components or if a replicate
  fails (both counted).
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
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import geometry as geo, sft_core as C, sft_local as L  # noqa: E402
import sft_observed_pilot as OP  # noqa: E402  (shared, already reviewed geometry: margins, coverage, domain, pixels)

STEP, AREA_MIN, PAD_DEG = 0.06, 25.0, 1.0
SEED_BOOT, N_BOOT, MIN_COMPONENTS = 36_300_001, 2000, 10
KINDS = ("raw", "p1_source", "balanced")
OBS = ("D_g", "phi_pos", "phi_neg", "phi_net", "lat_pos", "lon_pos", "lat_neg", "lon_neg", "sep_deg", "tilt_deg", "lat_mean")
LINEAR = ("D_g", "phi_pos", "phi_neg", "phi_net", "phi_uns", "lat_pos", "lat_neg", "sep_deg", "lat_mean", "dD_over_SD")
ANGULAR = (("tilt_deg", "axial"), ("lon_pos", "circular"), ("lon_neg", "circular"))


def diff(k, a, b):
    if k == "tilt_deg":
        return OP.axial(b, a)
    if k.startswith("lon_"):
        return OP.circ(b, a)
    return b - a


def deposit_stencil(box, lat, lon):
    """Cells receiving a non-zero weight from each point in LocalBox.deposit (same index arithmetic), and the mask of
    points outside the centre support (refused by the deposit)."""
    lat, lon = np.asarray(lat, float).ravel(), np.asarray(lon, float).ravel()
    s_c = np.sin(np.radians(box.lat))
    s = np.sin(np.radians(lat))
    outside = (s < s_c[0]) | (s > s_c[-1]) | (lon < box.lon[0]) | (lon > box.lon[-1])
    s, lon = s[~outside], lon[~outside]
    iy = np.clip(np.searchsorted(s_c, s, side="right") - 1, 0, box.ny - 2)
    wy = (s - s_c[iy]) / (s_c[iy + 1] - s_c[iy])
    ix = np.clip(np.searchsorted(box.lon, lon, side="right") - 1, 0, box.nx - 2)
    wx = (lon - box.lon[ix]) / (box.lon[ix + 1] - box.lon[ix])
    cells = []
    for dy, fy in ((0, 1 - wy), (1, wy)):
        for dx, fx in ((0, 1 - wx), (1, wx)):
            m = fy * fx > 0
            cells.append((iy[m] + dy, ix[m] + dx))
    return cells, outside


def footprints(box, lat, lon, valid):
    """G (cells containing a pixel centre) and V (cells of G with a valid centre, no invalid centre and no deposit
    weight from an invalid pixel); n_out = points outside the deposit support (valid or not)."""
    G = OP.coverage(box, lat, lon)
    V = OP.coverage(box, lat[valid], lon[valid]) & G & ~OP.coverage(box, lat[~valid], lon[~valid])
    cells, outside = deposit_stencil(box, lat[~valid], lon[~valid])
    for iy, ix in cells:
        V[iy, ix] = False
    return G, V, int(outside.sum()) + int(deposit_stencil(box, lat[valid], lon[valid])[1].sum())


def balance_on(B, A, Cm):
    """Raw field with each polarity rescaled to the mean of the two fluxes measured on Cm; factors from Cm, applied to
    the whole box. None if a polarity is empty on Cm."""
    a = B[Cm] * A[Cm]
    pp, nn = float(a[a > 0].sum()), float(-a[a < 0].sum())
    if not (pp > 0 and nn > 0):
        return None, (np.nan, np.nan)
    pb = 0.5 * (pp + nn)
    return np.where(B > 0, B * (pb / pp), B * (pb / nn)), (pb / pp, pb / nn)


def leading_change(m0, m1):
    """Change of the leading polarity (P1 convention of measures: westmost, periodic); NaN unless both instants have
    both polarities."""
    if m0["status"] != "ok" or m1["status"] != "ok":
        return np.nan
    return bool(m0["leading"] != m1["leading"])


def measure_pair(read, harp, t_rec0, t_rec1, kinds=KINDS):
    br0, bm0, h0 = read(harp, t_rec0)
    br1, bm1, h1 = read(harp, t_rec1)
    gap_s = (OP.t_obs(h1) - OP.t_obs(h0)).total_seconds()
    branch = float(h0["CRVAL1"])
    lons, lats = [], []
    for br, h in ((br0, h0), (br1, h1)):
        lo, la = geo.lonlat_maps(h, br.shape)
        lons.append((lo - branch + 180.0) % 360.0 - 180.0 + branch)
        lats.append(la)
    lat_rng = (max(-89.0, min(np.nanmin(lats[0]), np.nanmin(lats[1])) - PAD_DEG), min(89.0, max(np.nanmax(lats[0]), np.nanmax(lats[1])) + PAD_DEG))
    lon_rng = (min(np.nanmin(lons[0]), np.nanmin(lons[1])) - PAD_DEG, max(np.nanmax(lons[0]), np.nanmax(lons[1])) + PAD_DEG)
    m_lat, m_lon = OP.margins(gap_s / C.DAY, lat_rng)
    box = L.LocalBox(lat_rng, lon_rng, STEP, meridional=False, diffusion=False)
    base = dict(HARPNUM=harp, T_REC_0=t_rec0, T_REC_1=t_rec1, gap_s=gap_s, m_lat=m_lat, m_lon=m_lon)
    # footprints and domains: one C_geo / C_fin per pair, shared by every preparation
    GV, n_out = [], 0
    for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1)):
        _, _, _, LAT, LON, valid = OP.pixels(br, bm, h, branch, "raw")
        pos = np.isfinite(LAT) & np.isfinite(LON)
        G, V, n = footprints(box, LAT[pos], LON[pos], valid[pos])
        GV.append((G, V))
        n_out += n
    (G0, V0), (G1, V1) = GV
    Cgeo, area_geo = OP.domain(box, G0, G1, m_lat, m_lon)
    Cm, area = OP.domain(box, V0, V1, m_lat, m_lon)
    base.update(area_C_geo=area_geo, area_C_fin=area, C_geo_cells=int(Cgeo.sum()), C_cells=int(Cm.sum()))
    if n_out:
        return [dict(base, kind=k, status="deposition_out_of_range", n_out=n_out) for k in kinds]
    if area < AREA_MIN:
        return [dict(base, kind=k, status="finite_coverage_insufficient") for k in kinds]
    dep = {}
    for kind in sorted({"raw" if k == "balanced" else k for k in kinds}):       # balanced is derived from raw on C_fin
        pair = []
        for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1)):
            la, lo, F, _, _, _ = OP.pixels(br, bm, h, branch, kind)
            B, n = box.deposit(la, lo, F)
            if B is None:                                        # cannot happen after the n_out check above
                raise RuntimeError(f"deposit refused {n} points after the support check")
            pair.append(B)
        dep[kind] = pair
    rot_taint = rotation_dependence(box, V0, gap_s)
    Crot = Cm & ~rot_taint                                       # secondary support (rotation only)
    area_rot = float((Crot * box.A).sum()) / box.r ** 2 * (180 / math.pi) ** 2
    rot_ok = area_rot >= AREA_MIN
    out = []
    for kind in kinds:
        rec = dict(base, kind=kind)
        if kind == "balanced":
            (B0, f0), (B1, f1) = balance_on(dep["raw"][0], box.A, Cm), balance_on(dep["raw"][1], box.A, Cm)
            if B0 is None or B1 is None:
                out.append(dict(rec, status="balance_polarity_missing"))
                continue
            rec.update(bal_fpos_0=f0[0], bal_fneg_0=f0[1], bal_fpos_1=f1[0], bal_fneg_1=f1[1])
        else:
            B0, B1 = dep[kind]
        m0, m1 = box.measures(B0, Cm), box.measures(B1, Cm)
        if rot_ok:
            mr, m0r, m1r = box.measures(box.evolve(B0, gap_s), Crot), box.measures(B0, Crot), box.measures(B1, Crot)
        uns0 = float(np.abs(B0[Cm] * box.A[Cm]).sum())
        uns1 = float(np.abs(B1[Cm] * box.A[Cm]).sum())
        s_d = 3.0 * uns0 / (8.0 * math.pi * box.r ** 2)
        rec.update(status="ok", S_D=s_d, phi_uns_0=uns0, phi_uns_1=uns1, d_phi_uns=uns1 - uns0,
                   d_dD_over_SD=(m1["D_g"] - m0["D_g"]) / s_d if s_d > 0 else np.nan,
                   status_0=m0["status"], status_1=m1["status"], leading_0=m0["leading"], leading_1=m1["leading"],
                   leading_change=leading_change(m0, m1),
                   **{f"x0_{k}": m0[k] for k in OBS}, **{f"x1_{k}": m1[k] for k in OBS},
                   **{f"d_{k}": diff(k, m0[k], m1[k]) for k in OBS}, area_C_rot=area_rot, area_lost_rot=area - area_rot,
                   rot_status="ok" if rot_ok else "rot_coverage_insufficient",
                   **{f"drot_{k}": (diff(k, mr[k], m1r[k]) if rot_ok else np.nan) for k in OBS},
                   **{f"dpers_rot_{k}": (diff(k, m0r[k], m1r[k]) if rot_ok else np.nan) for k in OBS})
        out.append(rec)
    return out


def transport_steps(box, gap_s):
    """Number of steps LocalBox.evolve takes for gap_s (same rule: full steps plus a shorter final one)."""
    k = int(np.floor(gap_s / box.dt * (1 + 1e-12)))
    return k + (1 if gap_s - k * box.dt > 1e-9 * box.dt else 0)


def rotation_dependence(box, V0, gap_s):
    """Cells whose value after LocalBox.evolve (rotation only) over gap_s can depend on a cell outside V0: the numerical
    domain of dependence of the TVD-minmod SSP-RK2 step is [i - 4, i + 2] for omega - omega_C > 0 (mirrored for < 0,
    empty for 0), hence [i - 4n, i + 2n] after n steps; positions beyond the box count as not valid."""
    if box.vf.any() or box.Ldif.count_nonzero():
        raise ValueError("rotation_dependence assumes a rotation-only box")
    n = transport_steps(box, gap_s)
    bad = ~V0
    out = np.zeros_like(bad)
    cs = np.concatenate([np.zeros((box.ny, 1), int), np.cumsum(bad, axis=1)], axis=1)
    i = np.arange(box.nx)
    for y in range(box.ny):
        if box.u[y] == 0 or n == 0:
            out[y] = bad[y]
            continue
        up, down = (4 * n, 2 * n) if box.u[y] > 0 else (2 * n, 4 * n)
        lo, hi = i - up, i + down
        cnt = cs[y, np.minimum(hi, box.nx - 1) + 1] - cs[y, np.maximum(lo, 0)]
        out[y] = (cnt > 0) | (lo < 0) | (hi > box.nx - 1)
    return out


# ---------------------------------------------------------------- summaries

def wquant(x, w, q):
    x, w = np.asarray(x, float), np.asarray(w, float)
    ok = np.isfinite(x)
    x, w = x[ok], w[ok]
    if not len(x):
        return np.nan
    o = np.argsort(x, kind="mergesort")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][np.searchsorted(c, q - 1e-12)])


def linear_stats(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    ok = np.isfinite(x)
    x, w = x[ok], w[ok]
    if not len(x):
        return dict(n=0)
    m = float(np.average(x, weights=w))
    med = wquant(x, w, 0.5)
    return dict(n=int(len(x)), mean=m, median=med, q10=wquant(x, w, 0.1), q90=wquant(x, w, 0.9),
                rms_centred=float(math.sqrt(np.average((x - m) ** 2, weights=w))), median_abs=wquant(np.abs(x), w, 0.5),
                mad_scaled=1.4826 * wquant(np.abs(x - med), w, 0.5), second_moment=float(np.average(x * x, weights=w)))


def angular_stats(x_deg, w, kind):
    """kind 'axial' (period 180) or 'circular' (period 360): weighted resultant of exp(i k x), k = 2 or 1."""
    x, w = np.asarray(x_deg, float), np.asarray(w, float)
    ok = np.isfinite(x)
    x, w = x[ok], w[ok]
    if not len(x):
        return dict(n=0)
    k = 2.0 if kind == "axial" else 1.0
    z = np.average(np.exp(1j * k * np.radians(x)), weights=w)
    r = float(abs(z))
    out = dict(n=int(len(x)), resultant=r, mean=float(np.degrees(np.angle(z)) / k) if r > 0 else np.nan,
               median_abs=wquant(np.abs(x), w, 0.5), q90_abs=wquant(np.abs(x), w, 0.9))
    out["circ_sd"] = float(np.degrees(math.sqrt(-2.0 * math.log(r))) / k) if 0 < r < 1 else (0.0 if r == 1 else np.nan)
    return out


def component_weights(comp, x):
    """Weights of the target 'a component among those with a finite value, then one of its pairs with a finite value':
    1/(K_eval n_finite(component)) on finite values, 0 on missing ones; also returns K_eval."""
    x = np.asarray(x, float)
    fin = np.isfinite(x)
    c = pd.Series(np.asarray(comp)[fin])
    w = np.zeros(len(x))
    if fin.any():
        w[fin] = 1.0 / (c.nunique() * c.map(c.value_counts()).to_numpy(float))
    return w, int(c.nunique())


def summarise(df, components):
    """df: ok rows of one kind; components: Series pair key -> component id (from the metadata graph). Weights per
    quantity as in component_weights (missing values do not move weight between components' pairs)."""
    comp = df.pair_key.map(components).to_numpy()
    rows = []
    for prefix in ("d_", "drot_", "dpers_rot_"):
        for k in LINEAR:
            col = "d_dD_over_SD" if k == "dD_over_SD" else ("d_phi_uns" if k == "phi_uns" else f"{prefix}{k}")
            if prefix != "d_" and k in ("dD_over_SD", "phi_uns"):
                continue
            if col in df:
                x = df[col].to_numpy(float)
                w, ke = component_weights(comp, x)
                fx = x[np.isfinite(x)]
                rows.append(dict(diff=prefix.rstrip("_"), quantity=k, n_components=ke, n_missing=int(len(x) - len(fx)),
                                 **linear_stats(x, w), unweighted_median=float(np.median(fx)) if len(fx) else np.nan))
        for k, kind in ANGULAR:
            x = df[f"{prefix}{k}"].to_numpy(float)
            w, ke = component_weights(comp, x)
            rows.append(dict(diff=prefix.rstrip("_"), quantity=k, n_components=ke, n_missing=int((~np.isfinite(x)).sum()),
                             **angular_stats(x, w, kind)))
    return pd.DataFrame(rows)


def bootstrap(df, components, col, rng, n=N_BOOT):
    """Percentile 95 % interval of the weighted centred RMS of col: resample the evaluable components (at least one
    finite value) with replacement, weights 1/n_finite within each drawn component (the target of summarise). No
    interval with fewer than MIN_COMPONENTS evaluable components or if a replicate fails; both are counted."""
    comp = df.pair_key.map(components).to_numpy()
    x = df[col].to_numpy(float)
    fin = np.isfinite(x)
    ids = np.unique(comp[fin])
    info = dict(n_components=int(len(ids)), n_pairs=int(fin.sum()), n_missing=int((~fin).sum()), n_rep_failed=0)
    if len(ids) < MIN_COMPONENTS:
        return dict(info, lo=np.nan, hi=np.nan, note=f"fewer than {MIN_COMPONENTS} evaluable components: no interval")
    by = {c: np.flatnonzero(fin & (comp == c)) for c in ids}
    vals = []
    for _ in range(n):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([by[c] for c in pick])
        wi = np.concatenate([np.full(len(by[c]), 1.0 / len(by[c])) for c in pick])
        xi = x[idx]
        m = np.average(xi, weights=wi)
        v = math.sqrt(np.average((xi - m) ** 2, weights=wi))
        if math.isfinite(v):
            vals.append(v)
        else:
            info["n_rep_failed"] += 1
    if info["n_rep_failed"]:
        return dict(info, lo=np.nan, hi=np.nan, note="failed replicates: no interval")
    return dict(info, lo=float(np.quantile(vals, 0.025)), hi=float(np.quantile(vals, 0.975)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        sys.exit("repeatability C: the spec is not frozen; --run refused")
    print("use scripts/sft_c_repeatability_selftest.py")
