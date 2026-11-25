"""Preparatory core for the two SFT pilots (draft protocols, not frozen; synthetic use only).

Drafts: docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_DRAFT.md (rev. 4) and docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md (rev. 3).
Revised after Codex code review docs/SFT_PREP_80b28a4_CODE_REVIEW.md (d3f61b5). No observed map is read here.

Contents
- 1D axisymmetric transport in s = sin(lat) (point 2):
  db/dt = d/ds[ (eta/R^2)(1 - s^2) db/ds - (v(asin s)/R) sqrt(1 - s^2) b ] - b/tau,
  finite volumes on N uniform cells, zero flux at the polar faces, two-point diffusive fluxes and HYBRID advection
  (Patankar): centred face value where the cell Peclet number |a| ds / D <= 2, first-order upwind elsewhere. The
  generator L has non-negative off-diagonal rates and conserves mass in both cases; with the physical parameters the
  scheme is centred (second order) almost everywhere. Crank-Nicolson with the step
  limited to dt <= min(dt_request, 0.9 * 2 / max(-L_ii)), so the explicit half is non-negative too; a shorter final
  sub-step reaches each output time exactly. v(lat) = Du sin(lat) cos(lat)^p (Yeates 2020, eq. 12-13).
  Axial dipole D = (3/2) sum b_j s_j ds (G); net flux 2 pi R^2 sum b_j ds (Mx).
- Linear deposit in s (conserves flux and first moment); points outside the centre support are REFUSED
  (status deposition_out_of_range, no clipping).
- Spherical Gaussian bipole (shape sensitivity) on a grid in rotated coordinates around the bipole midpoint (no seam,
  no pole problem), radial step sigma_min/10, radius half-separation + 8 sigma_max; components normalised before the
  superposition; effective fluxes and centroids of the summed field.
- Field measures with the P1 conventions (geometry.py) and explicit status (ok, one_polarity, empty).
Units: cm, s, G, Mx. eta in km^2/s and Du in km/s are converted explicitly.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.linalg import solve_banded

from sharpbl import geometry as geo

RSUN_CM = geo.RSUN_CM_DEFAULT                 # 6.96e10 cm, RSUN_REF of the SHARP maps (as P1)
DAY, YEAR = 86400.0, 365.25 * 86400.0
REFERENCE = dict(eta_km2s=466.8, du_kms=0.025, p=2.33)                  # Yeates 2020 §3.1, pre-HMI cycles 21-23
SENSITIVITY = [dict(eta_km2s=e, du_kms=d, p=2.33) for e in (350.0, 466.8) for d in (0.025, 0.041)]
OMEGA_C = 14.1844                             # deg/day, Carrington sidereal rate
POS_TOL = 1e-12                               # rounding allowance for positivity, relative to the maximum


class DepositionOutOfRange(Exception):
    pass


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
        if not (int(n) == n and n >= 4 and eta_km2s >= 0 and math.isfinite(du_kms) and r_cm > 0):
            raise ValueError("invalid grid or parameters")
        self.n, self.r = int(n), r_cm
        self.ds = 2.0 / n
        self.s = -1.0 + self.ds * (np.arange(n) + 0.5)            # cell centres
        sf = -1.0 + self.ds * np.arange(n + 1)                      # faces, sf[0] = -1, sf[n] = 1
        d = eta_km2s * 1e10 / r_cm ** 2 * (1.0 - sf ** 2) / self.ds  # diffusive conductance per face
        a = v_merid_cm_s(np.arcsin(np.clip(sf, -1, 1)), du_kms, p) / r_cm * np.sqrt(np.clip(1.0 - sf ** 2, 0, None))
        d[[0, -1]] = 0.0                                            # zero flux at the poles
        a[[0, -1]] = 0.0
        central = 2.0 * d >= np.abs(a)                              # cell Peclet <= 2: centred face value is monotone
        self.central_fraction = float(central[1:-1].mean())
        # face flux G_f = d_f (b_R - b_L) - (cL_f b_L + cR_f b_R), with (cL, cR) = (a/2, a/2) centred or (a+, a-) upwind
        cL = np.where(central, 0.5 * a, np.maximum(a, 0.0))
        cR = np.where(central, 0.5 * a, np.minimum(a, 0.0))
        # db_j/dt = (G_{j+1/2} - G_{j-1/2}) / ds - b_j/tau
        self.di = (-d[1:] - cL[1:] - d[:-1] + cR[:-1]) / self.ds
        self.up = np.r_[(d[1:-1] - cR[1:-1]) / self.ds, 0.0]        # coefficient of b_{j+1} in row j (>= 0)
        self.lo = np.r_[0.0, (d[1:-1] + cL[1:-1]) / self.ds]        # coefficient of b_{j-1} in row j (>= 0)
        if tau_s:
            self.di = self.di - 1.0 / tau_s
        self.dt_max = 0.9 * 2.0 / float(np.max(-self.di))           # positivity of the explicit half of CN

    def apply(self, b):
        out = self.di * b
        out[1:] += self.lo[1:] * b[:-1]
        out[:-1] += self.up[:-1] * b[1:]
        return out

    def _banded(self, dt):
        h = 0.5 * dt
        ab = np.zeros((3, self.n))
        ab[0, 1:] = -h * self.up[:-1]
        ab[1] = 1.0 - h * self.di
        ab[2, :-1] = -h * self.lo[1:]
        return ab

    def evolve(self, b0, t_out_s, dt_s=DAY):
        """b at each requested time (s, finite, non-negative, non-decreasing). Crank-Nicolson with the effective step
        min(dt_s, dt_max) and a shorter final sub-step to reach each time exactly."""
        if not (math.isfinite(dt_s) and dt_s > 0):
            raise ValueError("dt must be positive and finite")
        b = np.asarray(b0, float).copy()
        if b.shape != (self.n,) or not np.isfinite(b).all():
            raise ValueError("initial profile must be finite with N cells")
        dt = min(dt_s, self.dt_max)
        self.dt_used = dt
        ab = self._banded(dt)
        h = 0.5 * dt
        t, out = 0.0, []
        for target in t_out_s:
            if not (math.isfinite(target) and target >= t):
                raise ValueError("output times must be finite, non-negative and non-decreasing")
            k = int(np.floor((target - t) / dt * (1 + 1e-12)))
            for _ in range(k):
                b = solve_banded((1, 1), ab, b + h * self.apply(b))
            rem = target - (t + k * dt)
            if rem > 1e-9 * dt:
                b = solve_banded((1, 1), self._banded(rem), b + 0.5 * rem * self.apply(b))
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
    """exp(-t/tau): exact for the continuous equation with uniform decay (not identical to CN with the tau term)."""
    return np.exp(-np.asarray(t_s, float) / tau_s)


# ---------------------------------------------------------------- deposit and bipoles

def deposit_linear(s, flux, centres):
    """Flux at s split between the two adjacent cell centres with linear weights: conserves sum(F) and sum(F s).
    Returns (cell fluxes, 0), or (None, n) if n points lie outside the support of the centres: the caller records the
    status deposition_out_of_range; nothing is clipped."""
    s, flux = np.asarray(s, float).ravel(), np.asarray(flux, float).ravel()
    c = np.asarray(centres, float)
    if not (np.isfinite(s).all() and np.isfinite(flux).all()):
        raise ValueError("non-finite input to the deposit")
    outside = (s < c[0]) | (s > c[-1])
    if outside.any():
        return None, int(outside.sum())
    j = np.clip(np.searchsorted(c, s, side="right") - 1, 0, len(c) - 2)
    w_hi = (s - c[j]) / (c[j + 1] - c[j])
    out = np.zeros(len(c))
    np.add.at(out, j, flux * (1.0 - w_hi))
    np.add.at(out, j + 1, flux * w_hi)
    return out, 0


def point_bipole(lat_pos_deg, lat_neg_deg, phibar):
    """(s, flux) of the point bipole: +phibar at the positive centroid, -phibar at the negative one."""
    return np.sin(np.radians([lat_pos_deg, lat_neg_deg])), np.array([phibar, -phibar])


def point_bipole_dipole(lat_pos_deg, lat_neg_deg, phibar, r_cm=RSUN_CM):
    return 3.0 * phibar / (4.0 * np.pi * r_cm ** 2) * (np.sin(np.radians(lat_pos_deg)) - np.sin(np.radians(lat_neg_deg)))


def sphere_grid(lat_range, lon_range, step_deg, r_cm=RSUN_CM):
    """Cell centres and exact spherical areas of a regular lat-lon grid (degrees); latitudes must stay in [-90, 90]."""
    if not (step_deg > 0 and -90.0 <= lat_range[0] < lat_range[1] <= 90.0 and lon_range[0] < lon_range[1]):
        raise ValueError("invalid spherical grid")
    la = np.arange(lat_range[0], lat_range[1] + 1e-9, step_deg)
    lo = np.arange(lon_range[0], lon_range[1] + 1e-9, step_deg)
    lat_c, lon_c = 0.5 * (la[:-1] + la[1:]), 0.5 * (lo[:-1] + lo[1:])
    band = r_cm ** 2 * np.radians(step_deg) * (np.sin(np.radians(la[1:])) - np.sin(np.radians(la[:-1])))
    LAT, LON = np.meshgrid(lat_c, lon_c, indexing="ij")
    return LAT, LON, np.repeat(band[:, None], len(lon_c), axis=1)


def rotated_cap_grid(centre_vec, radius_rad, step_rad, r_cm=RSUN_CM):
    """Cells of a spherical cap around centre_vec in rotated polar coordinates (rho, theta): exact areas
    R^2 dtheta (cos rho_in - cos rho_out); returns lat, lon (deg, lon in [0, 360)), area, unit vectors."""
    if not (0 < radius_rad <= math.pi and step_rad > 0):
        raise ValueError("invalid cap")
    m = np.asarray(centre_vec, float) / np.linalg.norm(centre_vec)
    e1 = np.cross(m, [0.0, 0.0, 1.0]) if abs(m[2]) < 0.9 else np.cross(m, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(m, e1)
    nr = int(math.ceil(radius_rad / step_rad))
    re = np.linspace(0.0, radius_rad, nr + 1)
    rc = 0.5 * (re[:-1] + re[1:])
    nt = max(8, int(math.ceil(2 * math.pi * radius_rad / step_rad)))
    tc = (np.arange(nt) + 0.5) * 2 * math.pi / nt
    R_, T_ = np.meshgrid(rc, tc, indexing="ij")
    area = np.repeat((r_cm ** 2 * (2 * math.pi / nt) * (np.cos(re[:-1]) - np.cos(re[1:])))[:, None], nt, axis=1)
    v = (np.cos(R_)[..., None] * m + np.sin(R_)[..., None] * (np.cos(T_)[..., None] * e1 + np.sin(T_)[..., None] * e2))
    lat = np.degrees(np.arcsin(np.clip(v[..., 2], -1, 1)))
    lon = np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360.0
    return lat.ravel(), lon.ravel(), area.ravel(), v.reshape(-1, 3)


def gaussian_bipole(pos, neg, sigma_pos_deg, sigma_neg_deg, phibar, step_deg=None, support_sigma=8.0, r_cm=RSUN_CM):
    """Two spherical Gaussians exp(-delta^2/(2 sigma^2)) centred at pos=(lon, lat) and neg, each normalised to flux
    phibar (with its sign) on the grid BEFORE the superposition; the field is their sum, not rescaled afterwards.
    Grid: cap around the bipole midpoint in rotated coordinates (no seam, no pole cut), step sigma_min/10 unless given,
    radius = half-separation + support_sigma * sigma_max. Returns the cells and the effective measures."""
    if not (sigma_pos_deg > 0 and sigma_neg_deg > 0 and phibar > 0):
        raise ValueError("sigma and phibar must be positive")
    vp, vn = geo.unit_vectors(*pos), geo.unit_vectors(*neg)
    mid = vp + vn
    if np.linalg.norm(mid) == 0:
        raise ValueError("antipodal centres")
    half = 0.5 * math.acos(float(np.clip(vp @ vn, -1, 1)))
    smin, smax = min(sigma_pos_deg, sigma_neg_deg), max(sigma_pos_deg, sigma_neg_deg)
    step = math.radians(step_deg if step_deg else smin / 10.0)
    lat, lon, area, v = rotated_cap_grid(mid, half + math.radians(support_sigma * smax), step, r_cm)
    br = np.zeros(len(lat))
    for c, sig, sgn in ((vp, sigma_pos_deg, 1.0), (vn, sigma_neg_deg, -1.0)):
        delta = np.degrees(np.arccos(np.clip(v @ c, -1, 1)))
        g = np.exp(-delta ** 2 / (2.0 * sig ** 2))
        br += sgn * phibar * g / float((g * area).sum())
    eff = field_measures(lat, lon, br, area, r_cm)
    return dict(lat=lat, lon=lon, area=area, br=br, effective=eff, component_centres=dict(pos=pos, neg=neg),
                step_deg=math.degrees(step), tail_bound=math.exp(-0.5 * support_sigma ** 2))


# ---------------------------------------------------------------- field measures (P1 conventions)

def field_measures(lat_deg, lon_deg, br, area_cm2, r_cm=RSUN_CM, threshold=0.0):
    """D (G), D_bal, fluxes, net flux, polarity centroids (unit-vector mean weighted with |B| dA, renormalised), mean
    latitude, separation, leading polarity (westmost = larger Carrington longitude) and tilt with the P1 convention.
    status: 'ok' (both polarities), 'one_polarity' (its centroid is given; separation, tilt and leading undefined),
    'empty'. threshold = 0 gives the integral measures without a cut. Coordinates and areas of the selected cells must
    be finite and areas positive."""
    lat_deg, lon_deg, br, area = (np.asarray(x, float).ravel() for x in (lat_deg, lon_deg, br, area_cm2))
    fin = np.isfinite(br)
    pos = fin & (br > 0) & (np.abs(br) >= threshold)
    neg = fin & (br < 0) & (np.abs(br) >= threshold)
    sel = pos | neg
    if not (np.isfinite(lat_deg[sel]).all() and np.isfinite(lon_deg[sel]).all() and (area[sel] > 0).all()):
        raise ValueError("selected cells need finite coordinates and positive areas")
    k = 3.0 / (4.0 * np.pi * r_cm ** 2)
    sl = np.sin(np.radians(lat_deg))
    out = dict(D_g=float(k * (br[sel] * sl[sel] * area[sel]).sum()), phi_pos=float((br[pos] * area[pos]).sum()),
               phi_neg=float((-br[neg] * area[neg]).sum()))
    out["phi_net"] = out["phi_pos"] - out["phi_neg"]
    out.update(lon_pos=np.nan, lat_pos=np.nan, lon_neg=np.nan, lat_neg=np.nan, lat_mean=np.nan, D_bal_g=np.nan,
               sep_deg=np.nan, tilt_deg=np.nan, leading=0)
    if not sel.any():
        return dict(out, status="empty")
    out["lat_mean"] = geo.weighted_centroid(lon_deg[sel], lat_deg[sel], np.abs(br[sel]) * area[sel])[1]
    lp = geo.weighted_centroid(lon_deg[pos], lat_deg[pos], br[pos] * area[pos]) if pos.any() else (np.nan, np.nan)
    ln = geo.weighted_centroid(lon_deg[neg], lat_deg[neg], -br[neg] * area[neg]) if neg.any() else (np.nan, np.nan)
    out.update(lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1])
    if not (pos.any() and neg.any()):
        return dict(out, status="one_polarity")
    phibar = 0.5 * (out["phi_pos"] + out["phi_neg"])
    msp = float((br[pos] * area[pos] * sl[pos]).sum() / out["phi_pos"])
    msn = float((-br[neg] * area[neg] * sl[neg]).sum() / out["phi_neg"])
    lead_sign = 1 if abs(geo.tilt_deg(ln, lp)) < 90.0 else -1
    lead, follow = (lp, ln) if lead_sign == 1 else (ln, lp)
    out.update(D_bal_g=float(k * phibar * (msp - msn)), sep_deg=geo.great_circle_deg(*lp, *ln),
               tilt_deg=geo.tilt_deg(lead, follow), leading=lead_sign)
    return dict(out, status="ok")


# ---------------------------------------------------------------- selftest (synthetic only)

def selftest(verbose=True):
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        if verbose:
            print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    t3 = [3 * YEAR]
    m = SFT1D()
    ok("generator: non-negative off-diagonal rates and zero column sums (mass); centred faces with the reference transport",
       (m.lo >= 0).all() and (m.up >= 0).all() and abs(m.di + np.r_[m.lo[1:], 0.0] + np.r_[0.0, m.up[:-1]]).max() <= 1e-12 * np.abs(m.di).max(),
       f"dt_max {m.dt_max / DAY:.3f} day, centred faces {m.central_fraction:.3f}")
    rng = np.random.default_rng(1)
    b0 = np.zeros(m.n)
    b0[rng.integers(0, m.n, 40)] = rng.normal(0, 5, 40)
    b3 = m.evolve(b0, t3)[0]
    ok("net flux conserved after 3 years with flow and diffusion (1e-12 of the unsigned flux)",
       abs(m.net_flux(b3) - m.net_flux(b0)) <= 1e-12 * np.sum(np.abs(b0)) * 2 * np.pi * m.r ** 2 * m.ds)
    # positivity without any clipping: impulses, sharp fronts, Gaussians, single polarity; extreme parameters and grids
    worst, mass = 0.0, 0.0
    for n in (200, 400, 800):
        for par in SENSITIVITY + [dict(eta_km2s=466.8, du_kms=0.0, p=2.33), dict(eta_km2s=0.0, du_kms=0.041, p=2.33)]:
            mm = SFT1D(n=n, **par)
            for b_init in (np.eye(n)[n // 2 + n // 7], (np.abs(mm.s - 0.3) < 0.05).astype(float), np.exp(-((mm.s + 0.4) / 0.03) ** 2)):
                outs = mm.evolve(b_init, [DAY, 27 * DAY])
                for bt_ in outs:
                    worst = min(worst, float(bt_.min() / b_init.max()))
                    mass = max(mass, abs(bt_.sum() - b_init.sum()) / b_init.sum())
    ok("positivity: impulses, fronts and Gaussians stay >= -1e-12 of the maximum (N 200/400/800, all transports, eta = 0, "
       "Du = 0), no clipping", worst >= -POS_TOL, f"min {worst:.1e}")
    ok("mass of a single polarity conserved in the same runs (1e-12)", mass <= 1e-12, f"{mass:.1e}")
    ok("Codex case: diffusion only, N 400, requested step 1 day -> effective step limited and no negative value",
       SFT1D(du_kms=0.0).dt_max < DAY and SFT1D(du_kms=0.0).evolve(np.eye(400)[230], [DAY])[0].min() >= 0)
    # input validation
    bad = 0
    for args in (([-600.0],), ([float("nan")],), ([2 * DAY, DAY],)):
        try:
            m.evolve(b0, *args)
        except ValueError:
            bad += 1
    try:
        m.evolve(b0, [DAY], dt_s=0.0)
    except ValueError:
        bad += 1
    ok("evolve refuses negative, non-finite and decreasing times and a non-positive step", bad == 4)
    t_odd = [601.0, 1.5 * DAY + 7.0]
    ok("non-multiple output times reached exactly with a final sub-step (601 s, 1.5 days + 7 s)",
       all(np.isfinite(x).all() for x in m.evolve(b0, t_odd)))
    # l = 1 mode, diffusion only: exact discrete eigenvector, only the time error of Crank-Nicolson
    md = SFT1D(du_kms=0.0)
    lam = 2.0 * REFERENCE["eta_km2s"] * 1e10 / RSUN_CM ** 2
    bt = md.evolve(md.s.copy(), t3)[0]
    rel = abs(md.dipole(bt) / md.dipole(md.s) - np.exp(-lam * t3[0])) / np.exp(-lam * t3[0])
    ok("l = 1 mode in pure diffusion decays as exp(-2 eta t/R^2) (rel 1e-9)", rel < 1e-9, f"{rel:.1e}")
    ok("b = s is an exact discrete eigenvector of the diffusion operator (up to rounding)", np.abs(md.apply(md.s) + lam * md.s).max() <= 1e-10 * lam)
    tau = 5 * YEAR
    mt = SFT1D(tau_s=tau)
    gaps = []
    for dtd in (0.2, 0.1):
        a_ = mt.dipole(mt.evolve(b0, t3, dt_s=dtd * DAY)[0])
        b_ = m.dipole(m.evolve(b0, t3, dt_s=dtd * DAY)[0]) * float(decay_factor(t3[0], tau))
        gaps.append(abs(a_ - b_) / abs(b_))
    ok("tau as a factor exp(-t/tau) = run with the decay term to second order in dt (gap < 1e-5, ratio 3-5)",
       gaps[0] < 1e-5 and 3.0 < gaps[0] / gaps[1] < 5.0, f"{gaps[0]:.1e} -> {gaps[1]:.1e}")
    br_ = m.evolve(b0[::-1].copy(), t3)[0]
    ok("north-south reflection: b(t)(s) -> b(t)(-s), D -> -D", np.allclose(br_, b3[::-1], rtol=0, atol=1e-12 * np.abs(b3).max())
       and abs(m.dipole(br_) + m.dipole(b3)) <= 1e-10 * abs(m.dipole(b3)))
    ok("polarity inversion: D -> -D", abs(m.dipole(m.evolve(-b0, t3)[0]) + m.dipole(b3)) <= 1e-10 * abs(m.dipole(b3)))
    # deposit
    s = rng.uniform(-0.9, 0.9, 500)
    F = rng.normal(0, 1, 500)
    cf, nout = deposit_linear(s, F, m.s)
    scale = np.abs(F).sum()
    ok("linear deposit conserves sum(F) and sum(F s) (1e-12 of sum|F|)", nout == 0 and abs(cf.sum() - F.sum()) < 1e-12 * scale
       and abs((cf * m.s).sum() - (F * s).sum()) < 1e-12 * scale)
    s2, F2 = np.array([0.3001, 0.3009]), np.array([1.0, -1.0])
    cf2, _ = deposit_linear(s2, F2, m.s)
    ok("opposite polarities in one cell: the first moment is kept", abs((cf2 * m.s).sum() - (F2 * s2).sum()) < 1e-15)
    cf3, n3 = deposit_linear(np.array([0.0, 0.9999]), np.array([1.0, 1.0]), m.s)
    ok("point beyond the last centre: refused (None, count), nothing clipped", cf3 is None and n3 == 1)
    sp, fp = point_bipole(12.0, 9.0, 1e22)
    b_pt = m.profile(deposit_linear(sp, fp, m.s)[0])
    ok("point bipole: D(0) of the deposited profile = formula (rel 1e-12)",
       abs(m.dipole(b_pt) - point_bipole_dipole(12.0, 9.0, 1e22)) <= 1e-12 * abs(point_bipole_dipole(12.0, 9.0, 1e22)))
    # convergence on a bipole at all output times, criterion of the draft
    times = [27 * DAY, 0.5 * YEAR, YEAR, 3 * YEAR]
    dsc = 3.0 * 1e22 / (4 * np.pi * RSUN_CM ** 2)
    worst_c = 0.0
    for par in SENSITIVITY:
        d = {}
        for n, dtd in ((400, 1.0), (800, 1.0), (400, 0.5)):
            mm = SFT1D(n=n, **par)
            mm.dt_max = min(mm.dt_max, dtd * DAY) if dtd < 1 else mm.dt_max
            d[(n, dtd)] = [mm.dipole(x) for x in mm.evolve(mm.profile(deposit_linear(sp, fp, mm.s)[0]), times, dt_s=dtd * DAY)]
        for i in range(len(times)):
            for fine in ((800, 1.0), (400, 0.5)):
                worst_c = max(worst_c, abs(d[fine][i] - d[(400, 1.0)][i]) / max(abs(d[fine][i]), 1e-6 * dsc))
    ok("convergence N 400 -> 800 and step halved, all times and transports: <= 1e-3 max(|D_fine|, 1e-6 D_scale)", worst_c <= 1e-3,
       f"{worst_c:.1e}")
    # Gaussians: separated, overlapping (Codex), across the 0/360 seam, different widths, quadrature
    g = gaussian_bipole((20.0, 10.0), (0.0, 10.0), 1.0, 1.0, 1.0)
    e = g["effective"]
    ok("Gaussian bipole separated: effective fluxes = phibar, centroids = centres", abs(e["phi_pos"] - 1) < 1e-9 and abs(e["phi_neg"] - 1) < 1e-9
       and abs(e["lon_pos"] - 20) < 1e-3 and abs(e["lat_pos"] - 10) < 1e-3, f"{e['phi_pos']:.10f} {e['lon_pos']:.5f}")
    e = gaussian_bipole((1.0, 0.0), (-1.0, 0.0), 2.0, 2.0, 1.0, step_deg=0.02)["effective"]
    ok("Gaussian bipole overlapping (+-1 deg, sigma 2): effective positive flux ~0.383, centroid ~2.61 deg (Codex case)",
       abs(e["phi_pos"] - 0.38284) < 2e-3 and abs(((e["lon_pos"] + 180) % 360 - 180) - 2.612) < 2e-2,
       f"{e['phi_pos']:.5f} {((e['lon_pos'] + 180) % 360 - 180):.3f}")
    gs = gaussian_bipole((179.0, 5.0), (-179.0, 5.0), 0.3, 0.3, 1.0)
    gr = gaussian_bipole((11.0, 5.0), (13.0, 5.0), 0.3, 0.3, 1.0)                   # same geometry away from the seam
    e, er = gs["effective"], gr["effective"]
    circ = lambda x, y: abs((x - y + 180.0) % 360.0 - 180.0)                         # noqa: E731
    ok("across the 0/360 seam: local grid (no 372 deg box); effective fluxes and centroid offsets equal to the same bipole "
       "away from the seam (1e-6); overlap tails reduce both fluxes below phibar",
       len(gs["lat"]) < 2e6 and abs(e["phi_pos"] - er["phi_pos"]) < 1e-6 and e["phi_pos"] < 1
       and abs(circ(e["lon_pos"], 179.0) - circ(er["lon_pos"], 11.0)) < 1e-6 and abs(circ(e["lon_neg"], 181.0) - circ(er["lon_neg"], 13.0)) < 1e-6,
       f"{len(gs['lat'])} cells, phi {e['phi_pos']:.7f} vs {er['phi_pos']:.7f}")
    gw = gaussian_bipole((10.0, 15.0), (5.0, 17.0), 0.2, 1.0, 1.0)
    gw2 = gaussian_bipole((10.0, 15.0), (5.0, 17.0), 0.2, 1.0, 1.0, step_deg=gw["step_deg"] / 2)
    dsc1 = 3.0 / (4 * np.pi * RSUN_CM ** 2)
    ok("different widths (0.2 and 1 deg): step = sigma_min/10, quadrature error on D < 1e-6 D_scale when halving, tail < 1e-13",
       abs(gw["step_deg"] - 0.02) < 1e-12 and abs(gw["effective"]["D_g"] - gw2["effective"]["D_g"]) < 1e-6 * dsc1 and gw["tail_bound"] < 1e-13)
    gp = gaussian_bipole((40.0, 88.0), (220.0, 87.0), 0.5, 0.5, 1.0)                # across the pole, separation 5 deg
    ge = gaussian_bipole((0.0, 0.0), (5.0, 0.0), 0.5, 0.5, 1.0)                     # same separation at the equator
    ok("bipole across the pole: no cut; effective fluxes and separation equal to the same bipole at the equator (1e-6)",
       abs(gp["effective"]["phi_pos"] - ge["effective"]["phi_pos"]) < 1e-6 and abs(gp["effective"]["sep_deg"] - ge["effective"]["sep_deg"]) < 1e-6,
       f"phi {gp['effective']['phi_pos']:.7f} vs {ge['effective']['phi_pos']:.7f}")
    try:
        sphere_grid((89.0, 91.0), (0.0, 1.0), 0.5)
        ok("latitude beyond the pole refused", False)
    except ValueError:
        ok("latitude beyond the pole refused", True)
    # field measures
    LAT, LON, A = sphere_grid((0, 20), (-5, 15), 0.05)
    br = np.zeros(LAT.shape)
    for (lo0, la0), sg in (((10.0, 9.0), 1.0), ((0.0, 11.0), -1.0)):
        br += sg * 500.0 * np.exp(-((LAT - la0) ** 2 + (LON - lo0) ** 2) / (2 * 0.5 ** 2))
    fm = field_measures(LAT, LON, br, A)
    ok("field measures: leading +1 (positive western), sin(tilt) > 0 (raw ~169, reduced ~-11), D < 0, D_bal and lat_mean",
       fm["status"] == "ok" and fm["leading"] == 1 and np.sin(np.radians(fm["tilt_deg"])) > 0
       and abs(geo.reduce_tilt_deg(fm["tilt_deg"]) + 11.5) < 1.5 and fm["D_g"] < 0 and fm["D_bal_g"] < 0 and 9 < fm["lat_mean"] < 11)
    f1 = field_measures(LAT, LON, np.clip(br, 0, None), A)
    ok("one polarity: status one_polarity, its centroid given, separation, tilt and leading undefined",
       f1["status"] == "one_polarity" and abs(f1["lon_pos"] - 10) < 0.01 and np.isnan(f1["tilt_deg"]) and np.isnan(f1["sep_deg"]) and f1["leading"] == 0)
    try:
        field_measures(LAT, LON, br, np.where(LAT > 10, -A, A))
        ok("non-positive areas refused", False)
    except ValueError:
        ok("non-positive areas refused", True)
    ok("rotation relative to Carrington at 15 deg over 4.5 days ~ +1.62 deg", abs(omega_rel_deg_day(15.0) * 4.5 - 1.62) < 0.01)
    if verbose:
        print(f"sft_core selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
