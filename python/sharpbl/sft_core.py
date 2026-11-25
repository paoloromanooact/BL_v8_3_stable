"""Preparatory core for the two SFT pilots (draft protocols, not frozen; synthetic use only).

Drafts: docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md (rev. 3) and docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md (rev. 2).
This module contains only the parts already settled in review (Codex 9aa3fce, 7f5d703); sampling, FITS reading and the
runners come after the freeze. No observed map is read here.

Contents
- 1D axisymmetric transport in s = sin(lat) (point 2):
  db/dt = d/ds[ (eta/R^2)(1 - s^2) db/ds - (v(asin s)/R) sqrt(1 - s^2) b ] - b/tau,
  finite volumes on N uniform cells, zero flux at the polar faces, Crank-Nicolson; v(lat) = Du sin(lat) cos(lat)^p
  (Yeates 2020, eq. 12-13). Axial dipole D = (3/2) sum b_j s_j ds (G), net flux 2 pi R^2 sum b_j ds (Mx).
- Linear deposit in s, which conserves flux and first moment (D at t = 0); point bipole; spherical Gaussian bipole
  (shape sensitivity) with the effective fluxes and centroids of the summed field.
- Field measures on a set of cells (point 3): D, fluxes, net flux, polarity centroids, separation, tilt and leading
  polarity with the P1 conventions (python/sharpbl/geometry.py); rotation rate relative to Carrington.
Units: cm, s, G, Mx. eta in km^2/s and Du in km/s are converted explicitly.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_banded

from sharpbl import geometry as geo

RSUN_CM = geo.RSUN_CM_DEFAULT                 # 6.96e10 cm, RSUN_REF of the SHARP maps (as P1)
DAY, YEAR = 86400.0, 365.25 * 86400.0
REFERENCE = dict(eta_km2s=466.8, du_kms=0.025, p=2.33)                  # Yeates 2020 §3.1, pre-HMI cycles 21-23
SENSITIVITY = [dict(eta_km2s=e, du_kms=d, p=2.33) for e in (350.0, 466.8) for d in (0.025, 0.041)]
OMEGA_C = 14.1844                             # deg/day, Carrington sidereal rate


def v_merid_cm_s(lat_rad, du_kms, p):
    """Meridional flow (cm/s), positive northward: Du sin(lat) cos(lat)^p."""
    return du_kms * 1e5 * np.sin(lat_rad) * np.cos(lat_rad) ** p


def omega_rel_deg_day(lat_deg):
    """Rotation of magnetic features relative to the Carrington frame (Snodgrass & Ulrich 1990, as P1d/P1e)."""
    s2 = np.sin(np.radians(lat_deg)) ** 2
    return 14.713 - 2.396 * s2 - 1.787 * s2 ** 2 - OMEGA_C


# ---------------------------------------------------------------- 1D transport in s

class SFT1D:
    def __init__(self, n=400, eta_km2s=REFERENCE["eta_km2s"], du_kms=REFERENCE["du_kms"], p=REFERENCE["p"],
                 r_cm=RSUN_CM, tau_s=None):
        self.n, self.r = n, r_cm
        self.ds = 2.0 / n
        self.s = -1.0 + self.ds * (np.arange(n) + 0.5)            # cell centres
        sf = -1.0 + self.ds * np.arange(n + 1)                      # faces, sf[0] = -1, sf[n] = 1
        dif = eta_km2s * 1e10 / r_cm ** 2 * (1.0 - sf ** 2)          # (eta/R^2)(1 - s^2), 1/s
        adv = v_merid_cm_s(np.arcsin(np.clip(sf, -1, 1)), du_kms, p) / r_cm * np.sqrt(np.clip(1.0 - sf ** 2, 0, None))
        dif[[0, -1]] = 0.0                                          # zero flux at the poles
        adv[[0, -1]] = 0.0
        # face flux G_f = dif_f (b_R - b_L)/ds - adv_f (b_L + b_R)/2 ; db_j/dt = (G_{j+1/2} - G_{j-1/2})/ds - b_j/tau
        lo, di, up = np.zeros(n), np.zeros(n), np.zeros(n)
        for j in range(n):
            gR_d, gR_a = dif[j + 1] / self.ds, adv[j + 1] / 2.0       # face j+1/2
            gL_d, gL_a = dif[j] / self.ds, adv[j] / 2.0               # face j-1/2
            # + G_{j+1/2}: coefficient of b_j = -gR_d - gR_a, of b_{j+1} = gR_d - gR_a
            # - G_{j-1/2}: coefficient of b_{j-1} = gL_d + gL_a, of b_j = -gL_d + gL_a
            di[j] = (-gR_d - gR_a - gL_d + gL_a) / self.ds
            if j + 1 < n:
                up[j] = (gR_d - gR_a) / self.ds
            if j > 0:
                lo[j] = (gL_d + gL_a) / self.ds
        if tau_s:
            di -= 1.0 / tau_s
        self.lo, self.di, self.up = lo, di, up

    def apply(self, b):
        out = self.di * b
        out[1:] += self.lo[1:] * b[:-1]
        out[:-1] += self.up[:-1] * b[1:]
        return out

    def _cn_step(self, b, dt):
        h = 0.5 * dt
        ab = np.zeros((3, self.n))
        ab[0, 1:] = -h * self.up[:-1]
        ab[1] = 1.0 - h * self.di
        ab[2, :-1] = -h * self.lo[1:]
        return solve_banded((1, 1), ab, b + h * self.apply(b))

    def evolve(self, b0, t_out_s, dt_s=DAY):
        """b at each requested time (s, increasing); Crank-Nicolson with step dt_s, and a shorter final step when a
        requested time is not a multiple of dt_s (e.g. 3 Julian years = 1095.75 days)."""
        h = 0.5 * dt_s
        ab = np.zeros((3, self.n))
        ab[0, 1:] = -h * self.up[:-1]
        ab[1] = 1.0 - h * self.di
        ab[2, :-1] = -h * self.lo[1:]
        b, t, out = np.asarray(b0, float).copy(), 0.0, []
        for target in t_out_s:
            if target < t - 1e-9:
                raise ValueError("output times must be increasing")
            k = int(np.floor((target - t) / dt_s + 1e-9))
            for _ in range(k):
                b = solve_banded((1, 1), ab, b + h * self.apply(b))
            rem = target - (t + k * dt_s)
            if rem > 1e-6:
                b = self._cn_step(b, rem)
            t = target
            out.append(b.copy())
        return out

    def dipole(self, b):
        return 1.5 * float(np.sum(b * self.s) * self.ds)

    def net_flux(self, b):
        return 2.0 * np.pi * self.r ** 2 * float(np.sum(b) * self.ds)

    def profile(self, cell_flux):
        """b_j (G) from the flux deposited in each cell (Mx)."""
        return np.asarray(cell_flux, float) / (2.0 * np.pi * self.r ** 2 * self.ds)


def decay_factor(t_s, tau_s):
    return np.exp(-np.asarray(t_s, float) / tau_s)


# ---------------------------------------------------------------- deposit and bipoles

def deposit_linear(s, flux, centres):
    """Flux at s split between the two adjacent cell centres with linear weights: conserves sum(F) and sum(F s).
    Points beyond the first/last centre go to the extreme cell (counted, first moment not conserved there)."""
    s, flux = np.asarray(s, float), np.asarray(flux, float)
    c = np.asarray(centres, float)
    out = np.zeros(len(c))
    j = np.clip(np.searchsorted(c, s) - 1, 0, len(c) - 2)
    w_hi = (s - c[j]) / (c[j + 1] - c[j])
    outside = (w_hi < 0) | (w_hi > 1)
    w_hi = np.clip(w_hi, 0.0, 1.0)
    np.add.at(out, j, flux * (1.0 - w_hi))
    np.add.at(out, j + 1, flux * w_hi)
    return out, int(outside.sum())


def point_bipole(lat_pos_deg, lat_neg_deg, phibar):
    """(s, flux) of the point bipole: +phibar at the positive centroid, -phibar at the negative one."""
    return np.sin(np.radians([lat_pos_deg, lat_neg_deg])), np.array([phibar, -phibar])


def point_bipole_dipole(lat_pos_deg, lat_neg_deg, phibar, r_cm=RSUN_CM):
    return 3.0 * phibar / (4.0 * np.pi * r_cm ** 2) * (np.sin(np.radians(lat_pos_deg)) - np.sin(np.radians(lat_neg_deg)))


def sphere_grid(lat_range, lon_range, step_deg, r_cm=RSUN_CM):
    """Cell centres and exact spherical areas of a regular lat-lon grid (degrees)."""
    la = np.arange(lat_range[0], lat_range[1] + 1e-9, step_deg)
    lo = np.arange(lon_range[0], lon_range[1] + 1e-9, step_deg)
    lat_c, lon_c = 0.5 * (la[:-1] + la[1:]), 0.5 * (lo[:-1] + lo[1:])
    band = r_cm ** 2 * np.radians(step_deg) * (np.sin(np.radians(la[1:])) - np.sin(np.radians(la[:-1])))
    LAT, LON = np.meshgrid(lat_c, lon_c, indexing="ij")
    return LAT, LON, np.repeat(band[:, None], len(lon_c), axis=1)


def gaussian_bipole(pos, neg, sigma_pos_deg, sigma_neg_deg, phibar, step_deg=None, r_cm=RSUN_CM):
    """Two spherical Gaussians exp(-delta^2/(2 sigma^2)) centred at pos=(lon, lat) and neg, each normalised to flux
    phibar (with its sign) BEFORE superposition; the field is their sum, not rescaled afterwards. Returns the field on a
    fine grid and the effective quantities of the summed field."""
    smax = max(sigma_pos_deg, sigma_neg_deg)
    step = step_deg or min(smax / 10.0, 0.05)
    pad = 7.0 * smax
    lats, lons = (pos[1], neg[1]), (pos[0], neg[0])
    LAT, LON, A = sphere_grid((min(lats) - pad, max(lats) + pad), (min(lons) - pad, max(lons) + pad), step, r_cm)
    v = geo.unit_vectors(LON, LAT)
    br = np.zeros(LAT.shape)
    for (lon0, lat0), sig, sgn in ((pos, sigma_pos_deg, 1.0), (neg, sigma_neg_deg, -1.0)):
        c = geo.unit_vectors(lon0, lat0)
        delta = np.degrees(np.arccos(np.clip(v @ c, -1, 1)))
        g = np.exp(-delta ** 2 / (2.0 * sig ** 2))
        br += sgn * phibar * g / float((g * A).sum())
    eff = field_measures(LAT.ravel(), LON.ravel(), br.ravel(), A.ravel(), r_cm)
    return dict(lat=LAT, lon=LON, area=A, br=br, effective=eff, component_centres=dict(pos=pos, neg=neg))


# ---------------------------------------------------------------- field measures (P1 conventions)

def field_measures(lat_deg, lon_deg, br, area_cm2, r_cm=RSUN_CM, threshold=0.0):
    """D (G), fluxes, net flux, polarity centroids (unit-vector mean weighted with |B|, renormalised), separation,
    leading polarity (westmost = larger Carrington longitude) and tilt with the P1 convention (sin > 0 if the following
    polarity is north of the leading one). threshold = 0 gives the integral measures without a cut."""
    lat_deg, lon_deg, br, area = (np.asarray(x, float).ravel() for x in (lat_deg, lon_deg, br, area_cm2))
    fin = np.isfinite(br)
    pos = fin & (br > 0) & (np.abs(br) >= threshold)
    neg = fin & (br < 0) & (np.abs(br) >= threshold)
    sel = pos | neg
    k = 3.0 / (4.0 * np.pi * r_cm ** 2)
    out = dict(D_g=float(k * (br[sel] * np.sin(np.radians(lat_deg[sel])) * area[sel]).sum()),
               phi_pos=float((br[pos] * area[pos]).sum()), phi_neg=float((-br[neg] * area[neg]).sum()))
    out["phi_net"] = out["phi_pos"] - out["phi_neg"]
    out.update(lon_pos=np.nan, lat_pos=np.nan, lon_neg=np.nan, lat_neg=np.nan, sep_deg=np.nan, tilt_deg=np.nan, leading=0)
    if pos.any() and neg.any():
        lp = geo.weighted_centroid(lon_deg[pos], lat_deg[pos], br[pos] * area[pos])
        ln = geo.weighted_centroid(lon_deg[neg], lat_deg[neg], -br[neg] * area[neg])
        lead_sign = 1 if abs(geo.tilt_deg(ln, lp)) < 90.0 else -1
        lead, follow = (lp, ln) if lead_sign == 1 else (ln, lp)
        out.update(lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1], sep_deg=geo.great_circle_deg(*lp, *ln),
                   tilt_deg=geo.tilt_deg(lead, follow), leading=lead_sign)
    return out


# ---------------------------------------------------------------- selftest (synthetic only)

def selftest(verbose=True):
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        if verbose:
            print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    t3 = [3 * YEAR]
    # flux conservation with full transport
    m = SFT1D()
    rng = np.random.default_rng(1)
    b0 = np.zeros(m.n)
    b0[rng.integers(0, m.n, 40)] = rng.normal(0, 5, 40)
    b3 = m.evolve(b0, t3)[0]
    ok("net flux conserved after 3 years with flow and diffusion (rel 1e-12)",
       abs(m.net_flux(b3) - m.net_flux(b0)) <= 1e-12 * np.sum(np.abs(b0)) * 2 * np.pi * m.r ** 2 * m.ds)
    # l = 1 mode, diffusion only: exact discrete eigenvector, only the time error of Crank-Nicolson
    md = SFT1D(du_kms=0.0)
    lam = 2.0 * REFERENCE["eta_km2s"] * 1e10 / RSUN_CM ** 2
    bt = md.evolve(md.s.copy(), t3)[0]
    rel = abs(md.dipole(bt) / md.dipole(md.s) - np.exp(-lam * t3[0])) / np.exp(-lam * t3[0])
    ok("l = 1 mode in pure diffusion decays as exp(-2 eta t/R^2) (rel 1e-9)", rel < 1e-9, f"{rel:.1e}")
    ok("b = s is an exact discrete eigenvector of the diffusion operator (up to rounding, 1e-10 of the rate)",
       np.abs(md.apply(md.s) + lam * md.s).max() <= 1e-10 * lam)
    # decay: exp(-t/tau) a posteriori against the integrator with tau (Crank-Nicolson, O(dt^2))
    tau = 5 * YEAR
    mt = SFT1D(tau_s=tau)
    # identity of the continuous equation; Crank-Nicolson reproduces it to O(dt^2): the gap must shrink ~4x with dt/2
    gaps = []
    for dtd in (1.0, 0.5):
        a_ = mt.dipole(mt.evolve(b0, t3, dt_s=dtd * DAY)[0])
        b_ = m.dipole(m.evolve(b0, t3, dt_s=dtd * DAY)[0]) * float(decay_factor(t3[0], tau))
        gaps.append(abs(a_ - b_) / abs(b_))
    ok("tau as a factor exp(-t/tau) = run with the decay term, to second order in dt (gap < 1e-4, ratio 3-5 when dt halves)",
       gaps[0] < 1e-4 and 3.0 < gaps[0] / gaps[1] < 5.0, f"{gaps[0]:.1e} -> {gaps[1]:.1e}")
    # north-south reflection and polarity inversion
    br_ = m.evolve(b0[::-1].copy(), t3)[0]
    ok("north-south reflection: b(t)(s) -> b(t)(-s), D -> -D", np.allclose(br_, b3[::-1], rtol=1e-12, atol=1e-12 * np.abs(b3).max())
       and abs(m.dipole(br_) + m.dipole(b3)) <= 1e-10 * abs(m.dipole(b3)))
    ok("polarity inversion: D -> -D", abs(m.dipole(m.evolve(-b0, t3)[0]) + m.dipole(b3)) <= 1e-10 * abs(m.dipole(b3)))
    # deposit: flux and first moment, opposite polarities in the same cell (Codex case)
    s = rng.uniform(-0.9, 0.9, 500)
    F = rng.normal(0, 1, 500)
    cf, nout = deposit_linear(s, F, m.s)
    ok("linear deposit conserves sum(F) and sum(F s) (rel 1e-12), nothing outside", nout == 0 and abs(cf.sum() - F.sum()) < 1e-12 * np.abs(F).sum()
       and abs((cf * m.s).sum() - (F * s).sum()) < 1e-12 * np.abs(F).sum())
    s2 = np.array([0.3001, 0.3009])
    F2 = np.array([1.0, -1.0])
    cf2, _ = deposit_linear(s2, F2, m.s)
    nearest = np.zeros(m.n)
    np.add.at(nearest, np.argmin(np.abs(m.s[None, :] - s2[:, None]), axis=1), F2)
    ok("opposite polarities in the same cell: linear deposit keeps the first moment, nearest-cell deposit loses it",
       abs((cf2 * m.s).sum() - (F2 * s2).sum()) < 1e-15 and abs((nearest * m.s).sum()) < 1e-15 and abs((F2 * s2).sum()) > 1e-4)
    # point bipole: D(0) after deposit equals the formula
    sp, fp = point_bipole(12.0, 9.0, 1e22)
    b_pt = m.profile(deposit_linear(sp, fp, m.s)[0])
    ok("point bipole: D(0) of the deposited profile = 3 phibar/(4 pi R^2)(sin lat+ - sin lat-) (rel 1e-12)",
       abs(m.dipole(b_pt) - point_bipole_dipole(12.0, 9.0, 1e22)) <= 1e-12 * abs(point_bipole_dipole(12.0, 9.0, 1e22)))
    # convergence on a bipole: N and dt
    d3 = {}
    for n, dtd in ((200, 1.0), (400, 1.0), (800, 1.0), (400, 2.0), (400, 0.5)):
        mm = SFT1D(n=n)
        d3[(n, dtd)] = mm.dipole(mm.evolve(mm.profile(deposit_linear(sp, fp, mm.s)[0]), t3, dt_s=dtd * DAY)[0])
    cN = abs(d3[(400, 1.0)] - d3[(800, 1.0)]) / abs(d3[(800, 1.0)])
    cT = abs(d3[(400, 1.0)] - d3[(400, 0.5)]) / abs(d3[(400, 0.5)])
    ok("convergence of D(3 yr): N 400 -> 800 and dt 1 -> 0.5 day below 1e-3 (criterion of the draft)", cN < 1e-3 and cT < 1e-3,
       f"N {cN:.1e}, dt {cT:.1e}")
    # Gaussian bipole: well separated recovers the ingredients; Codex overlap case
    g = gaussian_bipole((20.0, 10.0), (0.0, 10.0), 1.0, 1.0, 1.0)
    e = g["effective"]
    ok("Gaussian bipole well separated: effective fluxes = phibar and centroids = centres",
       abs(e["phi_pos"] - 1) < 1e-6 and abs(e["phi_neg"] - 1) < 1e-6 and abs(e["lon_pos"] - 20) < 1e-3 and abs(e["lat_pos"] - 10) < 1e-3,
       f"{e['phi_pos']:.8f} {e['lon_pos']:.5f}")
    g = gaussian_bipole((1.0, 0.0), (-1.0, 0.0), 2.0, 2.0, 1.0, step_deg=0.02)
    e = g["effective"]
    ok("Gaussian bipole overlapping (+-1 deg, sigma 2 deg): effective positive flux ~0.383 and centroid ~2.61 deg (Codex case)",
       abs(e["phi_pos"] - 0.38284) < 2e-3 and abs(e["lon_pos"] - 2.612) < 2e-2, f"{e['phi_pos']:.5f} {e['lon_pos']:.3f}")
    # field measures: P1 conventions
    LAT, LON, A = sphere_grid((0, 20), (-5, 15), 0.05)
    lead_p = ((10.0, 9.0), 1.0)
    follow_n = ((0.0, 11.0), -1.0)
    br = np.zeros(LAT.shape)
    for (lo0, la0), sg in (lead_p, follow_n):
        br += sg * 500.0 * np.exp(-((LAT - la0) ** 2 + (LON - lo0) ** 2) / (2 * 0.5 ** 2))
    fm = field_measures(LAT, LON, br, A)
    # P1 convention: atan2 in the tangent plane with x west; a Joy-like pair (leading west and south) gives a raw tilt
    # near 169 deg with sin > 0 and a reduced tilt near -11 deg
    ok("field measures: positive polarity western -> leading +1; following north -> sin(tilt) > 0 (raw ~169, reduced ~-11); D < 0",
       fm["leading"] == 1 and np.sin(np.radians(fm["tilt_deg"])) > 0 and abs(geo.reduce_tilt_deg(fm["tilt_deg"]) + 11.5) < 1.5
       and fm["phi_net"] == fm["phi_pos"] - fm["phi_neg"] and fm["D_g"] < 0,
       f"tilt {fm['tilt_deg']:.2f}, D {fm['D_g']:.3e}")
    ok("rotation relative to Carrington at 15 deg over 4.5 days ~ +1.62 deg, faster than Carrington (Codex check)",
       abs(omega_rel_deg_day(15.0) * 4.5 - 1.62) < 0.01,
       f"{omega_rel_deg_day(15.0) * 4.5:.3f}")
    if verbose:
        print(f"sft_core selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
