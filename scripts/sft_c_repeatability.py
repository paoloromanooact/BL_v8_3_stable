"""Repeatability C (draft rev. 3, NOT frozen): observed short-lag differences of the SFT observables. Synthetic only.

Spec: docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md. This file implements the measurement and the summaries on synthetic
CEA patches; --run reads the real pairs only through gate() (the C freeze receipt with spec, runner, recount and
candidates SHA, freeze commit ancestor of HEAD holding the spec, non-blindness text, clean tree, script = HEAD blob, no
existing output) and after unique_file_problems() (every record file exactly once under data/sharp/fits).
- Pairs: consecutive local records of one HARP with 0 < Delta T_OBS <= 7200 s (selection and graph from the metadata
  closure, Codex bb23d3e); every listed pair is measured, no replacement on failure.
- Grid 0.06 deg on the branch of the first CRVAL1; lower bounds = minimum of the WCS centres of BOTH patches - 1 deg,
  cells up to cover the maximum + 1 deg, rounded up (grid_range; before 27 Nov the last edge was rounded down).
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
  the conservative POTENTIAL support of the scheme (Codex, 27 Nov), not the minimal support active on a given field,
  and not a sub-point rule: there is no partial coverage. It guarantees neither the accuracy of the transport nor
  isolation from measurement errors nor transfer to days. The balanced field is not necessarily balanced on C_rot (a
  different domain) and is not rescaled again there. It is much wider than the
  physical displacement (n <= 12 at 2 h: up to 48 cells, 2.9 deg upstream), so C_rot < C_fin in general and multi-day
  gaps leave it empty. Persistence and rotation-only differences are both recomputed on C_rot; the main C_fin is
  unchanged. area(C_rot) < 25 deg^2 -> rot_status rot_coverage_insufficient.
- Remapping (draft §4): for each instant and deposited preparation (raw, p1_source; balanced reports the raw deposit,
  i.e. before balancing) the differences grid - pixels of the measures on the FULL support (sft_local.remap_report):
  deposit conserves net flux and D there, while polarity fluxes and centroids may change by cancellation within cells.
  Recorded as remap0_* / remap1_*, never corrected.
- Fine grid (draft §4, numerical sensitivity): the same pixels deposited at 0.03 deg; support = the 2 x 2 children of
  C_fin (same physical domain, no new selection; the fine and coarse edges must coincide). Observed coverage comes
  from C_fin (at the pixel scale some fine cells hold no centre by aliasing); at the fine grid only the reach of
  invalid pixels is checked: if one reaches a child cell (its centre cell or its fine deposit stencil) or a pixel falls
  outside the fine deposit support, fine_status says so and nothing is re-selected. The balanced variant takes its factors on the fine support.
  Recorded per preparation: fine_x0_*, fine_x1_*, fine_d_* and grid_dd_* = fine_d - d (preparation error of the
  difference, not solar noise).
- Summaries (point 4): for each quantity, the target is a component drawn among those with at least one finite value,
  then one of its pairs with a finite value: weights 1/(K_eval n_finite(component)), 0 for missing values. Mean,
  median, q10/q90, centred RMS, scaled MAD; circular statistics for the angles; lag classes (0, 1.5 h] and (1.5, 2 h];
  hemispheres; USFLUX(t0) metadata terciles; component bootstrap (2000 replicates, seed 36_300_001) over the
  evaluable components with the same weights; no interval with fewer than 10 evaluable components or if a replicate
  fails (both counted). A pair_key without an assigned component is refused (ValueError), not taken as missing.
- Descriptive additions of draft §6 (spec §4bis.8): QUALITY of both records from the headers and the group
  quality = both0 / not_both0 / missing (the QUALITY = 0 sensitivity of §2.2 is the group both0); geometric mu of C_fin
  at both instants (mu_mean_j, area-weighted over cells with mu > 0, and mu_offdisk_cells_j; not a LOS correction);
  TRIPLES (links t -> t+1 -> t+2 among the selected pairs of one HARP, not new replicates); YEARS (pairs per year of
  T_REC_0 and preparation); BOOTSTRAP_BLOCKS (sensitivity: non-overlapping blocks of 6 Carrington rotations, mean
  synodic rule, each component in the block of its first CR, seed 36_300_002 restarted per call, no interval with
  fewer than 10 evaluable blocks).
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
STEP_FINE = 0.03            # numerical sensitivity (draft §4): same physical support, children of C_fin
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


def grid_range(lo, hi):
    """Draft §4: cells from lo up to COVER hi, rounded up (LocalBox places edges at lo + k STEP up to its upper bound)."""
    return lo, lo + math.ceil((hi - lo) / STEP - 1e-9) * STEP


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


def children(box, fbox, Cm):
    """2 x 2 children of the coarse cells in Cm on the fine box. The fine box must be exactly the 2 x 2 refinement
    (shape 2ny x 2nx, every coarse edge a fine edge within 1e-9 deg ABSOLUTE, rtol 0): a shifted or truncated fine grid
    is refused, so no selected child can be lost (Codex review C_FINE_REVIEW_20261127)."""
    if (fbox.ny, fbox.nx) != (2 * box.ny, 2 * box.nx):
        raise ValueError(f"fine grid {fbox.ny} x {fbox.nx} is not the 2 x 2 refinement of {box.ny} x {box.nx}")
    if not (np.allclose(fbox.lat_e[::2], box.lat_e, rtol=0.0, atol=1e-9) and np.allclose(fbox.lon_e[::2], box.lon_e, rtol=0.0, atol=1e-9)):
        raise ValueError("fine and coarse cell edges do not coincide")
    return np.kron(Cm, np.ones((2, 2), bool))


def mu_stats(box, Cm, h):
    """Area-weighted mean of mu = cos(heliocentric angle) over the C_fin cells on the disk, with the observer at
    (CRLN_OBS, CRLT_OBS) of the header, and the number of C_fin cells with mu <= 0. Descriptive only (draft §6): not the
    LOS correction of Br, no instrumental inference. Missing observer keys -> (NaN, -1)."""
    if "CRLN_OBS" not in h or "CRLT_OBS" not in h:
        return np.nan, -1
    L0, B0 = math.radians(float(h["CRLN_OBS"])), math.radians(float(h["CRLT_OBS"]))
    LAT, LON = np.meshgrid(np.radians(box.lat), np.radians(box.lon), indexing="ij")
    mu = math.sin(B0) * np.sin(LAT) + math.cos(B0) * np.cos(LAT) * np.cos(LON - L0)
    on = Cm & (mu > 0)
    mean = float((mu * box.A)[on].sum() / box.A[on].sum()) if on.any() else np.nan
    return mean, int((Cm & (mu <= 0)).sum())


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
    lat_rng = grid_range(max(-89.0, min(np.nanmin(lats[0]), np.nanmin(lats[1])) - PAD_DEG),
                         min(89.0, max(np.nanmax(lats[0]), np.nanmax(lats[1])) + PAD_DEG))
    lon_rng = grid_range(min(np.nanmin(lons[0]), np.nanmin(lons[1])) - PAD_DEG, max(np.nanmax(lons[0]), np.nanmax(lons[1])) + PAD_DEG)
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
    for j, h in enumerate((h0, h1)):                                  # draft §6: geometric mu of C_fin (descriptive)
        base[f"mu_mean_{j}"], base[f"mu_offdisk_cells_{j}"] = mu_stats(box, Cm, h)
    if n_out:
        return [dict(base, kind=k, status="deposition_out_of_range", n_out=n_out) for k in kinds]
    if area < AREA_MIN:
        return [dict(base, kind=k, status="finite_coverage_insufficient") for k in kinds]
    dep, remap = {}, {}
    for kind in sorted({"raw" if k == "balanced" else k for k in kinds}):       # balanced is derived from raw on C_fin
        pair, rm = [], {}
        for j, (br, bm, h) in enumerate(((br0, bm0, h0), (br1, bm1, h1))):
            la, lo, F, _, _, _ = OP.pixels(br, bm, h, branch, kind)
            B, n = box.deposit(la, lo, F)
            if B is None:                                        # cannot happen after the n_out check above
                raise RuntimeError(f"deposit refused {n} points after the support check")
            pair.append(B)
            rr = L.remap_report(C.field_measures(la, lo, F, np.ones(len(F)), box.r), box.measures(B))
            rm.update({f"remap{j}_{k[2:]}": v for k, v in rr.items()})
        dep[kind], remap[kind] = pair, rm
    # fine-grid sensitivity on the children of C_fin (no new selection)
    fbox = L.LocalBox(lat_rng, lon_rng, STEP_FINE, meridional=False, diffusion=False)
    Cf = children(box, fbox, Cm)
    # at the pixel scale some fine cells hold no centre (aliasing): observed coverage comes from C_fin; at the fine grid
    # only the reach of invalid pixels (their centre cell and fine deposit stencil) is checked
    f_taint, f_out = np.zeros((fbox.ny, fbox.nx), bool), 0
    for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1)):
        _, _, _, LAT, LON, valid = OP.pixels(br, bm, h, branch, "raw")
        pos = np.isfinite(LAT) & np.isfinite(LON)
        la, lo, va = LAT[pos], LON[pos], valid[pos]
        f_taint |= OP.coverage(fbox, la[~va], lo[~va])
        cells, outside = deposit_stencil(fbox, la[~va], lo[~va])
        for iy, ix in cells:
            f_taint[iy, ix] = True
        f_out += int(outside.sum()) + int(deposit_stencil(fbox, la[va], lo[va])[1].sum())
    f_bad = int((Cf & f_taint).sum())
    fine = dict(fine_status="fine_deposition_out_of_range" if f_out else ("fine_support_invalid" if f_bad else "ok"),
                fine_cells_invalid=f_bad, area_fine=float((Cf * fbox.A).sum()) / fbox.r ** 2 * (180 / math.pi) ** 2)
    fdep = {}
    if fine["fine_status"] == "ok":
        for kind in dep:
            fdep[kind] = [fbox.deposit(*OP.pixels(br, bm, h, branch, kind)[:3])[0] for br, bm, h in ((br0, bm0, h0), (br1, bm1, h1))]
    rot_taint = rotation_dependence(box, V0, gap_s)
    Crot = Cm & ~rot_taint                                       # secondary support (rotation only)
    area_rot = float((Crot * box.A).sum()) / box.r ** 2 * (180 / math.pi) ** 2
    rot_ok = area_rot >= AREA_MIN
    out = []
    for kind in kinds:
        rec = dict(base, kind=kind, **remap["raw" if kind == "balanced" else kind], **fine)
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
        rec.update(fine_measures(fbox, Cf, fdep, kind, m0, m1) if fine["fine_status"] == "ok" else {})
        out.append(rec)
    return out


def fine_measures(fbox, Cf, fdep, kind, m0, m1):
    """Measures at 0.03 deg on the children of C_fin and the difference fine - coarse of the pair difference."""
    if kind == "balanced":
        (F0, _), (F1, _) = balance_on(fdep["raw"][0], fbox.A, Cf), balance_on(fdep["raw"][1], fbox.A, Cf)
        if F0 is None or F1 is None:
            return dict(fine_kind_status="balance_polarity_missing")
    else:
        F0, F1 = fdep[kind]
    f0, f1 = fbox.measures(F0, Cf), fbox.measures(F1, Cf)
    out = dict(fine_kind_status="ok", **{f"fine_x0_{k}": f0[k] for k in OBS}, **{f"fine_x1_{k}": f1[k] for k in OBS})
    for k in OBS:
        out[f"fine_d_{k}"] = diff(k, f0[k], f1[k])
        out[f"grid_dd_{k}"] = diff(k, diff(k, m0[k], m1[k]), out[f"fine_d_{k}"])
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


def components_of(df, components):
    """Component of every pair; a pair_key without an assigned component is refused (not a missing value)."""
    comp = df.pair_key.map(components)
    if comp.isna().any():
        raise ValueError(f"pair_key without component: {list(df.pair_key[comp.isna()])[:5]}")
    return comp.to_numpy()


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
    comp = components_of(df, components)
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
    comp = components_of(df, components)
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


# ---------------------------------------------------------------- operational assembly (synthetic only until the freeze)

CANDIDATES = ROOT / "reviews/C_REPEATABILITY_METADATA_CLOSURE_20261125/AUDIT/CANDIDATES.csv"
LAG_SPLIT_S = 5400.0                     # lag classes (0, 1.5 h] and (1.5 h, 2 h]
BOOT_QUANTITIES = ("D_g", "dD_over_SD", "phi_net", "phi_uns", "lat_pos", "lat_neg", "sep_deg")
GROUP_COLS = ("hemisphere", "lag_class", "flux_tercile", "quality")
SEED_BOOT_BLOCKS = 36_300_002            # block bootstrap of 6 CR (draft §6 sensitivity), restarted per call
CR_BLOCK = 6
FITS_BASE = ROOT / "data/sharp/fits"
OUT = ROOT / "results/SFT_C_REPEATABILITY"


def file_paths(base):
    from sharpbl.download_records import file_stem, record_dir

    def paths(harp, t_rec):
        folder, stem = record_dir(base, t_rec), file_stem(int(harp), t_rec)
        return [folder / f"{stem}.{k}" for k in ("Br.fits", "bitmap.fits", "keys.json")]
    return paths


def tercile_bounds(f):
    """Draft §4bis.6: linear quantile with rational index (n - 1) k / 3 on the sorted values; an integral index takes the
    sample value itself (no floating-point index, no tolerance)."""
    x = np.sort(np.asarray(f, float))
    n = len(x)
    out = []
    for k in (1, 2):
        i, r = divmod((n - 1) * k, 3)
        out.append(float(x[i]) if r == 0 else float(x[i] + (x[i + 1] - x[i]) * (r / 3)))
    return tuple(out)


def eligible_flags(v):
    """metadata_eligible: booleans, or the exact strings 'True' / 'False'; anything else stops the selection."""
    out = []
    for x in v:
        if isinstance(x, (bool, np.bool_)):
            out.append(bool(x))
        elif x in ("True", "False"):
            out.append(x == "True")
        else:
            raise ValueError(f"metadata_eligible must be a boolean or 'True'/'False', got {x!r}")
    return np.array(out, bool)


SEL_COLS = ["pair_key", "node", "HARPNUM", "T_REC_a", "T_REC_b", "gap_ns", "gap_meta_s", "component", "family", "USFLUX_t0",
            "LAT_FWT_t0", "LON_FWT_t0", "hemisphere", "lag_class", "flux_tercile"]


def selection(cand):
    """SELECTION (metadata-eligible pairs, every one measured, no replacement) and EXCLUSIONS (the others, with their
    recorded reasons). Groups from metadata only: hemisphere of LAT_FWT at t0, lag class from Delta T_OBS of the audit,
    USFLUX(t0) terciles recomputed on the selection (classes 1 <= q1 < 2 <= q2 < 3; missing / non-positive -> 'missing')."""
    c = cand.copy()
    c["pair_key"] = c.HARPNUM.astype(int).astype(str) + "|" + c.T_REC_a + "|" + c.T_REC_b
    if c.pair_key.duplicated().any():
        raise ValueError("duplicate pair keys in the candidates")
    el = eligible_flags(c.metadata_eligible)
    sel = c[el].copy()
    exc = c[~el][["pair_key", "node", "HARPNUM", "pregraph_reasons", "protected_component", "component"]].copy()
    sel["gap_meta_s"] = sel.gap_ns.astype(float) / 1e9
    sel["hemisphere"] = np.where(sel.LAT_FWT_t0 > 0, "N", np.where(sel.LAT_FWT_t0 < 0, "S", "missing"))
    sel["lag_class"] = np.where(sel.gap_meta_s <= LAG_SPLIT_S, "le_1.5h", "gt_1.5h_le_2h")
    f = sel.USFLUX_t0.astype(float)
    good = np.isfinite(f) & (f > 0)
    q1, q2 = tercile_bounds(f[good]) if good.any() else (np.nan, np.nan)
    sel["flux_tercile"] = np.where(~good, "missing", np.where(f <= q1, "1", np.where(f <= q2, "2", "3")))
    sel = sel.sort_values("pair_key").reset_index(drop=True)
    sel = sel[SEL_COLS + [k for k in sel.columns if k not in SEL_COLS]] if len(sel) else pd.DataFrame(columns=SEL_COLS)
    return sel, exc.sort_values("pair_key").reset_index(drop=True), dict(tercile_q1=float(q1), tercile_q2=float(q2))


def manifest(sel, paths_fn):
    import hashlib
    rows = []
    for _, r in sel.iterrows():
        for side, t in (("t0", r.T_REC_a), ("t1", r.T_REC_b)):
            for p in paths_fn(r.HARPNUM, t):
                ex = Path(p).exists()
                rows.append(dict(pair_key=r.pair_key, side=side, path=str(p), exists=ex,
                                 sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest() if ex else ""))
    return pd.DataFrame(rows, columns=["pair_key", "side", "path", "exists", "sha256"])


def measurement_keys_exact(meas, sel):
    """Exactly one row per (pair_key, preparation) of the selection: no missing, extra or duplicated key."""
    got = list(zip(meas.pair_key, meas.kind)) if len(meas) else []
    want = {(p, k) for p in sel.pair_key for k in KINDS}
    return bool(len(got) == len(set(got)) and set(got) == want)


def quality_group(h0, h1):
    """QUALITY of the two records from their headers (read before any pixel): 'both0', 'not_both0' or 'missing'."""
    q = []
    for h in (h0, h1):
        try:
            v = h["QUALITY"]
            v = v.strip() if isinstance(v, str) else v                                  # DRMS may give '0x00000000'
            q.append(float(int(v, 16 if v.lower().startswith("0x") else 10)) if isinstance(v, str) else float(v))
        except (KeyError, TypeError, ValueError, AttributeError):
            q.append(np.nan)
    grp = "missing" if not np.isfinite(q).all() else ("both0" if q[0] == 0 and q[1] == 0 else "not_both0")
    return dict(quality_0=q[0], quality_1=q[1], quality=grp)


def carrington_rotation(t_rec):
    """Carrington rotation number of a T_REC (mean synodic rule 1690 + (JD - 2444235.34) / 27.2753; TAI taken as UTC;
    used only to group pairs into blocks of 6 CR for a sensitivity bootstrap)."""
    t = pd.Timestamp(str(t_rec).replace("_TAI", "").replace(".", "-", 2).replace("_", " "))
    return int(math.floor(1690 + (t.to_julian_date() - 2444235.34) / 27.2753))


def component_blocks(sel):
    """Block of 6 CR of every component: the block of the first CR of its pairs (draft §6)."""
    if not len(sel):
        return pd.Series(dtype=int)
    cr = sel.T_REC_a.map(carrington_rotation)
    first = cr.groupby(sel.component.to_numpy()).min()
    return (first // CR_BLOCK).astype(int)


def bootstrap_blocks(df, components, cblock, col, rng, n=N_BOOT):
    """Sensitivity: resample the non-overlapping blocks of 6 CR (each component whole, in the block of its first CR)
    with replacement; weights 1/n_finite within each component as in bootstrap(); no interval with fewer than
    MIN_COMPONENTS evaluable blocks or a failed replicate."""
    comp = components_of(df, components)
    x = df[col].to_numpy(float)
    fin = np.isfinite(x)
    ids = np.unique(comp[fin])
    blk = {c: int(cblock[c]) for c in ids}
    blocks = np.unique([blk[c] for c in ids])
    info = dict(n_blocks=int(len(blocks)), n_components=int(len(ids)), n_rep_failed=0)
    if len(blocks) < MIN_COMPONENTS:
        return dict(info, lo=np.nan, hi=np.nan, note=f"fewer than {MIN_COMPONENTS} evaluable blocks: no interval")
    members = {b: [c for c in ids if blk[c] == b] for b in blocks}
    by = {c: np.flatnonzero(fin & (comp == c)) for c in ids}
    vals = []
    for _ in range(n):
        pick = [c for b in rng.choice(blocks, len(blocks), replace=True) for c in members[b]]
        idx = np.concatenate([by[c] for c in pick])
        wi = np.concatenate([np.full(len(by[c]), 1.0 / len(by[c])) for c in pick])
        m = np.average(x[idx], weights=wi)
        v = math.sqrt(np.average((x[idx] - m) ** 2, weights=wi))
        if math.isfinite(v):
            vals.append(v)
        else:
            info["n_rep_failed"] += 1
    if info["n_rep_failed"]:
        return dict(info, lo=np.nan, hi=np.nan, note="failed replicates: no interval")
    return dict(info, lo=float(np.quantile(vals, 0.025)), hi=float(np.quantile(vals, 0.975)))


def triples(sel):
    """Local triples t -> t+1 -> t+2 of one HARP among the selected pairs (draft §6): links between pairs already
    admitted, not new replicates."""
    cols = ["HARPNUM", "T_REC_0", "T_REC_1", "T_REC_2", "pair_key_1", "pair_key_2"]
    if not len(sel):
        return pd.DataFrame(columns=cols)
    m = sel.merge(sel, left_on=["HARPNUM", "T_REC_b"], right_on=["HARPNUM", "T_REC_a"], suffixes=("_1", "_2"))
    return pd.DataFrame(dict(HARPNUM=m.HARPNUM, T_REC_0=m.T_REC_a_1, T_REC_1=m.T_REC_b_1, T_REC_2=m.T_REC_b_2, pair_key_1=m.pair_key_1,
                             pair_key_2=m.pair_key_2), columns=cols).sort_values(["HARPNUM", "T_REC_0"]).reset_index(drop=True)


def years(meas):
    """Distribution per year of T_REC_0 and preparation: selected pairs and pairs measured ok (draft §6)."""
    cols = ["kind", "year", "selected", "ok"]
    if not len(meas):
        return pd.DataFrame(columns=cols)
    y = meas.assign(year=meas.T_REC_0.astype(str).str[:4].astype(int))
    g = y.groupby(["kind", "year"]).agg(selected=("pair_key", "size"), ok=("status", lambda s_: int((s_ == "ok").sum()))).reset_index()
    return g[cols]


def unique_file_problems(base, sel, paths_fn):
    """Draft §1 / package item 7: in the adopted layout every record must resolve to exactly one Br, bitmap and keys
    file; another copy with the same name anywhere under `base` is a problem (stop before any pixel)."""
    probs = []
    names = {}
    for p in Path(base).rglob("*"):
        if p.is_file():
            names.setdefault(p.name, []).append(p)
    for _, r in sel.iterrows():
        for t in (r.T_REC_a, r.T_REC_b):
            for p in paths_fn(r.HARPNUM, t):
                found = names.get(Path(p).name, [])
                if len(found) != 1 or Path(found[0]).resolve() != Path(p).resolve():
                    probs.append(f"{Path(p).name}: {len(found)} copies")
    return probs


def assemble(cand, read, paths_fn, n_boot=N_BOOT):
    """Products of one run (synthetic until the freeze): SELECTION, EXCLUSIONS, INPUT_MANIFEST, MEASUREMENTS (with
    QUALITY and the geometric mu of C_fin), DENOMINATORS, COMPONENTS, SUMMARY, BOOTSTRAP, BOOTSTRAP_BLOCKS (6 CR), TRIPLES,
    YEARS and run information. Every selected pair is measured once; a failure is
    a status (read_error / technical_error), never a removal or a replacement."""
    sel, exc, terc = selection(cand)
    man0 = manifest(sel, paths_fn)
    rows = []
    for _, r in sel.iterrows():
        fail = lambda st: [dict(HARPNUM=r.HARPNUM, T_REC_0=r.T_REC_a, T_REC_1=r.T_REC_b, kind=k, status=st) for k in KINDS]  # noqa: E731
        qual = dict(quality_0=np.nan, quality_1=np.nan, quality="missing")
        try:                                                          # reading: both maps, before any computation
            cache = {t: read(r.HARPNUM, t) for t in (r.T_REC_a, r.T_REC_b)}
        except Exception as exc_:                                     # noqa: BLE001 (recorded as read_error)
            got = fail(f"read_error:{type(exc_).__name__}")
        else:
            qual = quality_group(cache[r.T_REC_a][2], cache[r.T_REC_b][2])
            try:
                got = measure_pair(lambda h, t: cache[t], r.HARPNUM, r.T_REC_a, r.T_REC_b)
            except Exception as exc_:                                 # noqa: BLE001 (recorded, the run continues)
                got = fail(f"technical_error:{type(exc_).__name__}")
        rows += [dict(g, pair_key=r.pair_key, **qual) for g in got]
    meas = pd.DataFrame(rows, columns=None if rows else ["pair_key", "kind", "status", "T_REC_0", "quality"])
    meas = meas.merge(sel[["pair_key", "component", "hemisphere", "lag_class", "flux_tercile"]], on="pair_key", how="left", validate="many_to_one")
    man1 = manifest(sel, paths_fn)
    comps = sel.set_index("pair_key").component
    cblock = component_blocks(sel)
    den, summ, boot, bblk = [], [], [], []
    for kind in KINDS:
        mk = meas[meas.kind == kind]
        for gname, part in [("all", mk)] + [(f"{c}={v}", x) for c in GROUP_COLS for v, x in mk.groupby(c, sort=True)]:
            d = dict(kind=kind, group=gname, selected=int(len(part)), ok=int((part.status == "ok").sum()))
            d.update({f"failed_{st}": int(n) for st, n in part.status[part.status != "ok"].value_counts().items()})
            den.append(d)
            okp = part[part.status == "ok"]
            if len(okp):
                sm = summarise(okp, comps)
                summ.append(sm.assign(kind=kind, group=gname))
                for q in BOOT_QUANTITIES:
                    col = "d_dD_over_SD" if q == "dD_over_SD" else ("d_phi_uns" if q == "phi_uns" else f"d_{q}")
                    b = bootstrap(okp, comps, col, np.random.default_rng(SEED_BOOT), n=n_boot)     # same seed per call: order-free
                    boot.append(dict(kind=kind, group=gname, quantity=q, **b))
                    bb = bootstrap_blocks(okp, comps, cblock, col, np.random.default_rng(SEED_BOOT_BLOCKS), n=n_boot)
                    bblk.append(dict(kind=kind, group=gname, quantity=q, **bb))
    info = dict(selected=int(len(sel)), excluded=int(len(exc)), components=int(sel.component.nunique()), **terc,
                manifest_unchanged=bool(man0[["path", "exists", "sha256"]].equals(man1[["path", "exists", "sha256"]])),
                all_inputs_present=bool(man0.exists.all()), measured_pairs=int(meas.pair_key.nunique()),
                measurement_keys_exact=measurement_keys_exact(meas, sel),
                read_errors=int(meas.status.astype(str).str.startswith("read_error").sum()),
                technical_errors=int(meas.status.astype(str).str.startswith("technical_error").sum()))
    # draft §4bis.7: scientific statuses are admitted outcomes; reading/computing failures and any key mismatch are not
    info["run_valid"] = bool(len(sel) > 0 and info["manifest_unchanged"] and info["all_inputs_present"] and info["measurement_keys_exact"]
                             and info["read_errors"] == 0 and info["technical_errors"] == 0)
    return dict(SELECTION=sel, EXCLUSIONS=exc, INPUT_MANIFEST=man0, MEASUREMENTS=meas, DENOMINATORS=pd.DataFrame(den).fillna(0),
                COMPONENTS=sel.groupby("component").agg(n_pairs=("pair_key", "size"), harps=("HARPNUM", "nunique")).reset_index(),
                SUMMARY=pd.concat(summ, ignore_index=True) if summ else pd.DataFrame(),
                BOOTSTRAP=pd.DataFrame(boot), BOOTSTRAP_BLOCKS=pd.DataFrame(bblk), TRIPLES=triples(sel), YEARS=years(meas)), info


PRODUCTS = ("SELECTION", "EXCLUSIONS", "INPUT_MANIFEST", "MEASUREMENTS", "DENOMINATORS", "COMPONENTS", "SUMMARY", "BOOTSTRAP",
            "BOOTSTRAP_BLOCKS", "TRIPLES", "YEARS")
SPEC = ROOT / "docs/SFT_HMI_REPEATABILITY_PLAN_DRAFT.md"
FREEZE = ROOT / "docs/SFT_HMI_REPEATABILITY_FREEZE.json"          # does not exist until the freeze


def _sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_products(prods, info, out, cand_path, extra=None):
    """Products of one run: every table as CSV in a temporary sibling directory, then META.json (run information,
    SHA-256 of every product, of the candidates table, of the code and of the spec, git HEAD), then an atomic rename to
    `out`. An existing destination is refused (no overwrite)."""
    import json
    import os
    import subprocess
    import tempfile
    out = Path(out)
    if out.exists():
        raise FileExistsError(f"{out} exists (single run, no overwrite)")
    tmp = Path(tempfile.mkdtemp(prefix=f".{out.name}.tmp-", dir=out.parent))
    for k in PRODUCTS:
        prods[k].to_csv(tmp / f"{k}.csv", index=False)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    meta = dict(info, products_sha256={f"{k}.csv": _sha(tmp / f"{k}.csv") for k in PRODUCTS}, candidates_sha256=_sha(cand_path),
                runner_sha256=_sha(__file__), observed_pilot_sha256=_sha(OP.__file__), sft_local_sha256=_sha(L.__file__),
                sft_core_sha256=_sha(C.__file__), spec_sha256=_sha(SPEC), git_head=head, seed_boot=SEED_BOOT, n_boot=N_BOOT, **(extra or {}))
    (tmp / "META.json").write_text(json.dumps(meta, indent=2, default=float) + "\n")
    os.replace(tmp, out)
    return meta


RECEIPT_FIELDS = ("sha256", "runner_sha256", "recount_sha256", "candidates_sha256", "freeze_commit", "not_blind")


def gate():
    """Provenance before any map is read (model of the A1 gate): the C freeze receipt with every field, the spec, the
    runner, the recount and the candidates equal to the receipt, the freeze commit an ancestor of HEAD holding the spec
    with the same SHA, a text non-blindness declaration, a clean tracked tree, this script equal to its HEAD blob and no
    existing output."""
    import json
    import subprocess
    if not FREEZE.exists():
        return ["C freeze receipt missing (spec not frozen)"]
    fz = json.loads(FREEZE.read_text())
    probs = [f"receipt field missing: {k}" for k in RECEIPT_FIELDS if k not in fz]
    if probs:
        return probs
    for k, path in (("sha256", SPEC), ("runner_sha256", Path(__file__)), ("recount_sha256", ROOT / "scripts/sft_c_repeatability_recount.py"),
                    ("candidates_sha256", CANDIDATES)):
        if fz[k] != _sha(path):
            probs.append(f"{k} differs from the current file")
    fc = str(fz["freeze_commit"])
    blob = subprocess.run(["git", "show", f"{fc}:{SPEC.relative_to(ROOT)}"], cwd=ROOT, capture_output=True)
    anc = subprocess.run(["git", "merge-base", "--is-ancestor", fc, "HEAD"], cwd=ROOT, capture_output=True).returncode == 0
    import hashlib
    if not (fc and anc and blob.returncode == 0 and hashlib.sha256(blob.stdout).hexdigest() == fz["sha256"]):
        probs.append("freeze commit missing, not an ancestor of HEAD, or without this spec")
    if not (isinstance(fz["not_blind"], str) and fz["not_blind"].strip()):
        probs.append("non-blindness declaration missing")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        probs.append("tracked tree not clean")
    head = subprocess.run(["git", "show", f"HEAD:scripts/{Path(__file__).name}"], cwd=ROOT, capture_output=True)
    if head.returncode != 0 or hashlib.sha256(head.stdout).hexdigest() != _sha(__file__):
        probs.append("script differs from HEAD")
    if OUT.exists():
        probs.append("output directory exists (single run)")
    return probs


def run():
    probs = gate()
    if probs:
        sys.exit("repeatability C --run refused: " + "; ".join(probs))
    cand = pd.read_csv(CANDIDATES)
    sel, _, _ = selection(cand)
    paths = file_paths(FITS_BASE)
    uniq = unique_file_problems(FITS_BASE, sel, paths)
    if uniq:
        sys.exit("refused before any pixel: " + "; ".join(uniq[:5]))
    prods, info = assemble(cand, OP.reader(FITS_BASE), paths)
    meta = write_products(prods, info, OUT, CANDIDATES, extra=dict(freeze_receipt_sha256=_sha(FREEZE)))
    print(f"written {OUT}; run valid {meta['run_valid']}")
    return 0 if meta["run_valid"] else 3


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        sys.exit(run())
    print("use scripts/sft_c_repeatability_selftest.py")
