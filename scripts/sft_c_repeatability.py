"""Repeatability C (draft rev. 3, NOT frozen): observed short-lag differences of the SFT observables. Synthetic only.

Spec: docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md. This file implements the measurement and the summaries on synthetic
CEA patches; --run is refused until the spec is frozen (no pixel of the real pairs is read here).
- Pairs: consecutive local records of one HARP with 0 < Delta T_OBS <= 7200 s (selection and graph from the metadata
  closure, Codex bb23d3e); every listed pair is measured, no replacement on failure.
- Grid 0.06 deg on the branch of the first CRVAL1; bounds = extent of the WCS centres of BOTH patches +- 1 deg.
- C_geo = erode(P0) & P1 with the directional margins of the observed pilot at the largest diffusion/velocity of its
  grid (466.8 km^2/s, Du 0.041 km/s, p 2.33) and the real Delta T_OBS; C_fin adds valid coverage at both instants;
  area < 25 deg^2 -> finite_coverage_insufficient.
- Preparations: raw (all finite |Br| <= 10000 G, main), p1_source (bitmap >= 33, |Br| >= 100 G), balanced (polarities
  rescaled; status balance_unavailable if one polarity is empty).
- Observables on C_fin at t0 and t1 (LocalBox.measures): D_g, fluxes, centroids, separation, tilt, mean latitude,
  plus unsigned and net flux; differences X(t1) - X(t0) (axial for the tilt, circular for longitudes); dD / S_D with
  S_D = 3 Phi_unsigned(t0)/(8 pi R^2); leading-polarity change flagged.
- Secondary (predefined): rotation only. C_rot = C_fin & {cells whose rotation preimage over the gap falls on valid
  t0 coverage for at least 8 of 4 x 4 sub-points}; on C_rot both the persistence and the rotation-only differences are
  recomputed (same support for observation, persistence and rotation, rev. 3); the main C_fin is unchanged.
  area(C_rot) < 25 deg^2 -> the secondary is not evaluable (rot_status). With the observed-pilot margins (which include
  max|omega - omega_C| x gap) C_rot = C_fin by construction; it is kept as a safety restriction.
- Summaries: weights 1/(K n_component); mean, median, q10/q90, centred RMS, scaled MAD; circular statistics for the
  angles; lag classes (0, 1.5 h] and (1.5, 2 h]; hemispheres; USFLUX(t0) metadata terciles; component bootstrap
  (2000 replicates, seed 36_300_001), no interval with fewer than 10 components.
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
    out = []
    for kind in kinds:
        rec = dict(base, kind=kind)
        if kind == "balanced":
            # balancing needs both polarities among the finite pixels at both instants (spec §4); explicit status otherwise
            both = all(((br[np.isfinite(br) & (np.abs(br) <= 10000.0)] > 0).any() and (br[np.isfinite(br) & (np.abs(br) <= 10000.0)] < 0).any())
                       for br in (br0, br1))
            if not both:
                out.append(dict(rec, status="balance_unavailable"))
                continue
        try:
            la0, lo0, F0, LAT0, LON0, fin0 = OP.pixels(br0, bm0, h0, branch, kind)
            la1, lo1, F1, LAT1, LON1, fin1 = OP.pixels(br1, bm1, h1, branch, kind)
        except OP.BalanceUnavailable:
            out.append(dict(rec, status="balance_unavailable"))
            continue
        P0, P1 = OP.coverage(box, LAT0[fin0], LON0[fin0]), OP.coverage(box, LAT1[fin1], LON1[fin1])
        Cm, area = OP.domain(box, P0, P1, m_lat, m_lon)
        rec["area_C_fin"] = area
        if area < AREA_MIN:
            out.append(dict(rec, status="finite_coverage_insufficient"))
            continue
        B0, n0 = box.deposit(la0, lo0, F0)
        B1, n1 = box.deposit(la1, lo1, F1)
        if B0 is None or B1 is None:
            out.append(dict(rec, status="deposition_out_of_range"))
            continue
        m0, m1 = box.measures(B0, Cm), box.measures(B1, Cm)
        Crot = Cm & rotation_preimage_covered(box, P0, gap_s)        # secondary support (rotation only)
        area_rot = float((Crot * box.A).sum()) / box.r ** 2 * (180 / math.pi) ** 2
        rot_ok = area_rot >= AREA_MIN
        if rot_ok:
            mr, m0r, m1r = box.measures(box.evolve(B0, gap_s), Crot), box.measures(B0, Crot), box.measures(B1, Crot)
        uns0 = float(np.abs(B0[Cm] * box.A[Cm]).sum())
        uns1 = float(np.abs(B1[Cm] * box.A[Cm]).sum())
        s_d = 3.0 * uns0 / (8.0 * math.pi * box.r ** 2)
        rec.update(status="ok", C_cells=int(Cm.sum()), S_D=s_d, phi_uns_0=uns0, phi_uns_1=uns1, d_phi_uns=uns1 - uns0,
                   d_dD_over_SD=(m1["D_g"] - m0["D_g"]) / s_d if s_d > 0 else np.nan,
                   leading_change=bool(np.sign(m0["lon_pos"] - m0["lon_neg"]) != np.sign(m1["lon_pos"] - m1["lon_neg"])) if np.isfinite(m0["lon_pos"]) and np.isfinite(m1["lon_pos"]) else np.nan,
                   **{f"x0_{k}": m0[k] for k in OBS}, **{f"x1_{k}": m1[k] for k in OBS},
                   **{f"d_{k}": diff(k, m0[k], m1[k]) for k in OBS}, area_C_rot=area_rot,
                   rot_status="ok" if rot_ok else "rot_coverage_insufficient",
                   **{f"drot_{k}": (diff(k, mr[k], m1r[k]) if rot_ok else np.nan) for k in OBS},
                   **{f"dpers_rot_{k}": (diff(k, m0r[k], m1r[k]) if rot_ok else np.nan) for k in OBS})
        out.append(rec)
    return out


def rotation_preimage_covered(box, P0, gap_s):
    """Cells whose 4 x 4 sub-points, moved back by the rotation relative to Carrington over gap_s (latitude unchanged),
    fall on cells covered at t0 for at least 8 of 16 sub-points (the rule of the observed pilot's advected mask)."""
    sub = (np.arange(4) + 0.5) / 4
    la = box.lat_e[:-1, None, None, None] + box.step * sub[None, None, :, None]
    lo = box.lon_e[None, :-1, None, None] + box.step * sub[None, None, None, :]
    la = np.broadcast_to(la, (box.ny, box.nx, 4, 4))
    lo = np.broadcast_to(lo, (box.ny, box.nx, 4, 4)) - C.omega_rel_deg_day(la) * (gap_s / C.DAY)
    iy = np.floor((la - box.lat_e[0]) / box.step).astype(int)
    ix = np.floor((lo - box.lon_e[0]) / box.step).astype(int)
    inside = (iy >= 0) & (iy < box.ny) & (ix >= 0) & (ix < box.nx)
    hit = np.zeros(la.shape, bool)
    hit[inside] = P0[iy[inside], ix[inside]]
    return hit.sum(axis=(2, 3)) >= 8


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


def summarise(df, components):
    """df: ok rows of one kind; components: Series HARPNUM pair key -> component id (from the metadata graph).
    Weights 1/(K n_component)."""
    comp = df.pair_key.map(components)
    nk = comp.map(comp.value_counts())
    w = (1.0 / (comp.nunique() * nk)).to_numpy(float)
    rows = []
    for prefix in ("d_", "drot_", "dpers_rot_"):
        for k in LINEAR:
            col = "d_dD_over_SD" if k == "dD_over_SD" else ("d_phi_uns" if k == "phi_uns" else f"{prefix}{k}")
            if prefix != "d_" and k in ("dD_over_SD", "phi_uns"):
                continue
            if col in df:
                rows.append(dict(diff=prefix.rstrip("_"), quantity=k, **linear_stats(df[col], w), unweighted_median=float(np.nanmedian(df[col]))))
        for k, kind in ANGULAR:
            rows.append(dict(diff=prefix.rstrip("_"), quantity=k, **angular_stats(df[f"{prefix}{k}"], w, kind)))
    return pd.DataFrame(rows)


def bootstrap(df, components, col, rng, n=N_BOOT):
    """Percentile 95 % interval of the weighted centred RMS of col, resampling components with replacement."""
    comp = df.pair_key.map(components).to_numpy()
    ids = np.unique(comp)
    if len(ids) < MIN_COMPONENTS:
        return dict(n_components=len(ids), lo=np.nan, hi=np.nan, note="fewer than 10 components: no interval")
    by = {c: np.flatnonzero(comp == c) for c in ids}
    x = df[col].to_numpy(float)
    vals = []
    for _ in range(n):
        pick = rng.choice(ids, len(ids), replace=True)
        idx = np.concatenate([by[c] for c in pick])
        ww = np.concatenate([np.full(len(by[c]), 1.0 / len(by[c])) for c in pick])
        ok = np.isfinite(x[idx])
        xi, wi = x[idx][ok], ww[ok]
        m = np.average(xi, weights=wi)
        vals.append(math.sqrt(np.average((xi - m) ** 2, weights=wi)))
    return dict(n_components=len(ids), lo=float(np.quantile(vals, 0.025)), hi=float(np.quantile(vals, 0.975)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        sys.exit("repeatability C: the spec is not frozen; --run refused")
    print("use scripts/sft_c_repeatability_selftest.py")
