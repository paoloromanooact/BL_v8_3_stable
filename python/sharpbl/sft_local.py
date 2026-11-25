"""Preparatory 2D local transport for the observed-evolution pilot (point 3; draft protocol rev. 3, not frozen).

Synthetic use only; no observed map is read. Revised after Codex code review docs/SFT_PREP_80b28a4_CODE_REVIEW.md.
Equation in the Carrington frame (draft §5):
  dB/dt = -(omega(lat) - omega_C) dB/dphi - 1/(R cos lat) d(v B cos lat)/dlat + eta lap_h B,
finite volumes on a box regular in longitude and latitude (degrees) with spherical metric factors and exact cell areas
R^2 dphi (sin lat_n - sin lat_s); zero-flux box edges.
Scheme (draft §5): Strang splitting per step - half step of diffusion with Crank-Nicolson (two-point operator with
non-negative off-diagonal rates), one advection step with TVD minmod reconstruction and SSP-RK2, half step of diffusion.
Step = min(dt_max_request (600 s), 0.5 CFL of advection, 0.9 * 2 / max(-L_ii) for the CN half step), with a shorter
final step to reach the requested duration exactly. Deposit from pixel coordinates: linear weights in longitude and in
s = sin(lat) between neighbouring cell centres (conserves flux and the first moments, hence D); points outside the
centre support are refused (status deposition_out_of_range).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.sparse import diags, identity, kron
from scipy.sparse.linalg import splu

from sharpbl import sft_core as C

DAY = C.DAY


def minmod(a, b):
    return np.where(a * b > 0, np.sign(a) * np.minimum(np.abs(a), np.abs(b)), 0.0)


class LocalBox:
    def __init__(self, lat_range, lon_range, step_deg=0.06, eta_km2s=C.REFERENCE["eta_km2s"], du_kms=C.REFERENCE["du_kms"],
                 p=C.REFERENCE["p"], r_cm=C.RSUN_CM, dt_max_s=600.0, rotation=True, meridional=True, diffusion=True):
        if not (step_deg > 0 and -90 < lat_range[0] < lat_range[1] < 90 and lon_range[0] < lon_range[1] and dt_max_s > 0):
            raise ValueError("invalid box or step")
        self.r, self.step = r_cm, step_deg
        self.lat_e = np.arange(lat_range[0], lat_range[1] + 1e-9, step_deg)
        self.lon_e = np.arange(lon_range[0], lon_range[1] + 1e-9, step_deg)
        self.lat = 0.5 * (self.lat_e[:-1] + self.lat_e[1:])
        self.lon = 0.5 * (self.lon_e[:-1] + self.lon_e[1:])
        self.ny, self.nx = len(self.lat), len(self.lon)
        dphi = dlam = math.radians(step_deg)
        self.area_row = r_cm ** 2 * dphi * (np.sin(np.radians(self.lat_e[1:])) - np.sin(np.radians(self.lat_e[:-1])))
        self.A = np.repeat(self.area_row[:, None], self.nx, axis=1)
        lat_r, latf_r = np.radians(self.lat), np.radians(self.lat_e)
        eta = eta_km2s * 1e10 if diffusion else 0.0
        self.u = (np.radians(C.omega_rel_deg_day(self.lat)) / DAY * r_cm * np.cos(lat_r)) if rotation else np.zeros(self.ny)
        self.vf = C.v_merid_cm_s(latf_r, du_kms, p) if meridional else np.zeros(self.ny + 1)
        self.vf[[0, -1]] = 0.0
        self.len_zonal = r_cm * dlam
        self.len_merid = r_cm * np.cos(latf_r) * dphi
        # diffusion operator, flux form, zero flux at the box edges, rows = latitude
        n = self.ny * self.nx
        dx_c = r_cm * np.cos(lat_r) * dphi
        wz = eta * self.len_zonal / dx_c
        wm = eta * self.len_merid[1:-1] / (r_cm * dlam)
        ex = np.ones(self.nx)
        Lx = kron(diags(wz), diags([ex[:-1], np.r_[-1.0, -2.0 * ex[1:-1], -1.0], ex[:-1]], [-1, 0, 1], shape=(self.nx, self.nx)))
        main = np.zeros(self.ny)
        main[:-1] -= wm
        main[1:] -= wm
        Ly = kron(diags([wm, main, wm], [-1, 0, 1], shape=(self.ny, self.ny)), identity(self.nx))
        self.Ldif = (diags(1.0 / self.A.ravel()) @ (Lx + Ly)).tocsc()
        diag = -self.Ldif.diagonal()
        dt_dif = 2.0 * 0.9 * 2.0 / float(diag.max()) if diag.max() > 0 else np.inf      # CN half step of dt/2
        # advection CFL (per cell: outgoing face fluxes over the cell content), TVD SSP-RK2 needs CFL <= 0.5
        out_rate = np.zeros((self.ny, self.nx))
        if rotation:
            out_rate += (np.abs(self.u)[:, None] * self.len_zonal * 2) / self.A
        if meridional:
            out_rate += (np.abs(self.vf[:-1])[:, None] * self.len_merid[:-1, None] + np.abs(self.vf[1:])[:, None] * self.len_merid[1:, None]) / self.A
        dt_adv = 0.5 / float(out_rate.max()) if out_rate.max() > 0 else np.inf
        self.dt = float(min(dt_max_s, dt_dif, dt_adv))
        self.dt_limits = dict(request=dt_max_s, diffusion=dt_dif, advection=dt_adv)
        self._ops = {}

    def _cn(self, h):
        """Crank-Nicolson factors for a diffusion sub-step of length h (cached)."""
        key = round(h, 9)
        if key not in self._ops:
            I = identity(self.ny * self.nx, format="csc")
            self._ops[key] = (splu((I - 0.5 * h * self.Ldif).tocsc()), (I + 0.5 * h * self.Ldif).tocsr())
        return self._ops[key]

    def _adv(self, B):
        """Flux divergence of the advection with TVD minmod reconstruction, upwind face values, zero flux at the edges."""
        out = np.zeros_like(B)
        if np.any(self.u):
            Bp = np.pad(B, ((0, 0), (1, 1)), mode="edge")
            slope = minmod(Bp[:, 1:-1] - Bp[:, :-2], Bp[:, 2:] - Bp[:, 1:-1])
            left = (B + 0.5 * slope)[:, :-1]                 # value at face i+1/2 from cell i
            right = (B - 0.5 * slope)[:, 1:]                 # value at face i+1/2 from cell i+1
            u = self.u[:, None]
            Fz = np.zeros((self.ny, self.nx + 1))
            Fz[:, 1:-1] = np.where(u > 0, u * left, u * right) * self.len_zonal
            out -= Fz[:, 1:] - Fz[:, :-1]
        if np.any(self.vf):
            Bp = np.pad(B, ((1, 1), (0, 0)), mode="edge")
            slope = minmod(Bp[1:-1] - Bp[:-2], Bp[2:] - Bp[1:-1])
            south = (B + 0.5 * slope)[:-1]
            north = (B - 0.5 * slope)[1:]
            v = self.vf[1:-1, None]
            Fm = np.zeros((self.ny + 1, self.nx))
            Fm[1:-1] = np.where(v > 0, v * south, v * north) * self.len_merid[1:-1, None]
            out -= Fm[1:] - Fm[:-1]
        return out / self.A

    def _step(self, B, dt):
        lu, rhs = self._cn(0.5 * dt)
        B = lu.solve(rhs @ B.ravel()).reshape(B.shape)
        k1 = B + dt * self._adv(B)                           # SSP-RK2
        B = 0.5 * (B + k1 + dt * self._adv(k1))
        return lu.solve(rhs @ B.ravel()).reshape(B.shape)

    def evolve(self, B0, t_s):
        """Field after t_s seconds (finite, >= 0): steps of self.dt and a shorter final step."""
        if not (math.isfinite(t_s) and t_s >= 0):
            raise ValueError("duration must be finite and non-negative")
        B = np.asarray(B0, float).copy()
        if B.shape != (self.ny, self.nx) or not np.isfinite(B).all():
            raise ValueError("initial field must be finite on the box")
        k = int(np.floor(t_s / self.dt * (1 + 1e-12)))
        for _ in range(k):
            B = self._step(B, self.dt)
        rem = t_s - k * self.dt
        if rem > 1e-9 * self.dt:
            B = self._step(B, rem)
        return B

    def deposit(self, lat_deg, lon_deg, flux):
        """Flux (Mx) of pixel centres to the grid: linear weights in lon and in s; returns (B in G, 0), or (None, n) when
        n points lie outside the support of the cell centres (status deposition_out_of_range; nothing clipped)."""
        lat_deg, lon_deg, flux = (np.asarray(x, float).ravel() for x in (lat_deg, lon_deg, flux))
        if not (np.isfinite(lat_deg).all() and np.isfinite(lon_deg).all() and np.isfinite(flux).all()):
            raise ValueError("non-finite input to the deposit")
        s_c = np.sin(np.radians(self.lat))
        s = np.sin(np.radians(lat_deg))
        outside = (s < s_c[0]) | (s > s_c[-1]) | (lon_deg < self.lon[0]) | (lon_deg > self.lon[-1])
        if outside.any():
            return None, int(outside.sum())
        iy = np.clip(np.searchsorted(s_c, s, side="right") - 1, 0, self.ny - 2)
        wy = (s - s_c[iy]) / (s_c[iy + 1] - s_c[iy])
        ix = np.clip(np.searchsorted(self.lon, lon_deg, side="right") - 1, 0, self.nx - 2)
        wx = (lon_deg - self.lon[ix]) / (self.lon[ix + 1] - self.lon[ix])
        F = np.zeros((self.ny, self.nx))
        for dy, fy in ((0, 1 - wy), (1, wy)):
            for dx, fx in ((0, 1 - wx), (1, wx)):
                np.add.at(F, (iy + dy, ix + dx), flux * fy * fx)
        return F / self.A, 0

    def measures(self, B, mask=None, threshold=0.0):
        LAT, LON = np.meshgrid(self.lat, self.lon, indexing="ij")
        m = np.ones(B.shape, bool) if mask is None else mask
        return C.field_measures(LAT[m], LON[m], B[m], self.A[m], self.r, threshold)


def remap_report(pixel_measures, grid_measures):
    """Differences introduced by the deposit before any transport (recorded, never corrected afterwards)."""
    circ = lambda a, b: (a - b + 180.0) % 360.0 - 180.0             # noqa: E731
    out = {}
    for k in ("D_g", "D_bal_g", "phi_pos", "phi_neg", "phi_net", "lat_mean", "lat_pos", "lat_neg", "sep_deg"):
        out[f"d_{k}"] = grid_measures[k] - pixel_measures[k]
    for k in ("lon_pos", "lon_neg"):
        out[f"d_{k}"] = circ(grid_measures[k], pixel_measures[k])
    return out


def gaussian_field(box, lat0, lon0, sigma_deg, amp=1.0):
    LAT, LON = np.meshgrid(box.lat, box.lon, indexing="ij")
    v = C.geo.unit_vectors(LON, LAT)
    d = np.degrees(np.arccos(np.clip(v @ C.geo.unit_vectors(lon0, lat0), -1, 1)))
    return amp * np.exp(-d ** 2 / (2 * sigma_deg ** 2))


def selftest(verbose=True):
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        if verbose:
            print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    T = 3 * DAY
    full = LocalBox((-5, 25), (-10, 30), step_deg=0.1)
    B0 = gaussian_field(full, 15.0, 10.0, 1.0, 500.0) - gaussian_field(full, 13.0, 6.0, 1.0, 480.0)
    ok("identity at dt = 0: the field and its measures are unchanged", np.array_equal(full.evolve(B0, 0.0), B0),
       f"dt {full.dt:.0f} s (limits {', '.join(f'{k} {v:.0f}' for k, v in full.dt_limits.items())})")
    Bt = full.evolve(B0, T)
    f0, ft = (B0 * full.A).sum(), (Bt * full.A).sum()
    ok("net flux conserved with rotation, meridional flow and diffusion (1e-12 of the unsigned flux)",
       abs(ft - f0) <= 1e-12 * (np.abs(B0) * full.A).sum(), f"{abs(ft - f0) / (np.abs(B0) * full.A).sum():.1e}")
    # positivity without clipping: single polarity, blocks and impulses, extreme parameters, high latitude
    worst, mass = 0.0, 0.0
    cases = []
    for par in C.SENSITIVITY:
        cases.append(LocalBox((5, 25), (0, 20), step_deg=0.06, **par))
    cases.append(LocalBox((57, 63), (0, 6), step_deg=0.06))                          # Codex case 59-61 deg
    cases.append(LocalBox((10, 20), (0, 10), step_deg=0.06, meridional=False, diffusion=False))   # advection only
    for bx in cases:
        LAT, LON = np.meshgrid(bx.lat, bx.lon, indexing="ij")
        lc, oc = bx.lat[len(bx.lat) // 2], bx.lon[len(bx.lon) // 2]
        block = ((np.abs(LAT - lc) < 1.0) & (np.abs(LON - oc) < 1.0)).astype(float)
        impulse = np.zeros_like(block)
        impulse[len(bx.lat) // 2, len(bx.lon) // 2] = 1.0
        for B_init in (block, impulse, gaussian_field(bx, lc, oc, 0.5)):
            for t in (600.0, 601.0, 2 * DAY):
                Bt_ = bx.evolve(B_init, t)
                worst = min(worst, float(Bt_.min() / B_init.max()))
                mass = max(mass, abs((Bt_ * bx.A).sum() - (B_init * bx.A).sum()) / (B_init * bx.A).sum())
    ok("positivity: blocks, impulses and Gaussians of one polarity stay >= -1e-12 of the maximum (all transports, 59-61 deg, "
       "advection only, 600 s, 601 s, 2 days), no clipping", worst >= -C.POS_TOL, f"min {worst:.1e}")
    ok("mass of a single polarity conserved in the same runs (1e-12)", mass <= 1e-12, f"{mass:.1e}")
    bad = 0
    for t in (-600.0, float("nan")):
        try:
            full.evolve(B0, t)
        except ValueError:
            bad += 1
    ok("evolve refuses negative and non-finite durations; 601 s accepted with a final sub-step", bad == 2
       and np.isfinite(full.evolve(B0, 601.0)).all())
    # pure rotation: translation in longitude by omega_rel(lat0) t (no clipping)
    rot = LocalBox((10, 20), (0, 20), step_deg=0.05, meridional=False, diffusion=False)
    G = gaussian_field(rot, 15.0, 8.0, 1.0, 100.0)
    Gt = rot.evolve(G, T)
    LATr, LONr = np.meshgrid(rot.lat, rot.lon, indexing="ij")
    c0 = C.geo.weighted_centroid(LONr.ravel(), LATr.ravel(), (G * rot.A).ravel())
    ct = C.geo.weighted_centroid(LONr.ravel(), LATr.ravel(), (Gt * rot.A).ravel())
    expect = C.omega_rel_deg_day(15.0) * 3.0
    ok("pure rotation: centroid moves by (omega - omega_C) t (0.01 deg), field non-negative without clipping",
       abs(ct[0] - c0[0] - expect) < 0.01 and Gt.min() >= -C.POS_TOL * G.max(), f"{ct[0] - c0[0]:.4f} vs {expect:.4f}")
    # pure diffusion, local limit
    dif = LocalBox((-8, 8), (-8, 8), step_deg=0.05, rotation=False, meridional=False, dt_max_s=1800.0)
    G = gaussian_field(dif, 0.0, 0.0, 1.0, 1.0)
    Gt = dif.evolve(G, T)
    LAT, LON = np.meshgrid(dif.lat, dif.lon, indexing="ij")
    var = lambda F, X: float((F * dif.A * X ** 2).sum() / (F * dif.A).sum())          # noqa: E731
    grow = var(Gt, LON) - var(G, LON)
    expect = math.degrees(1.0) ** 2 * 2 * C.REFERENCE["eta_km2s"] * 1e10 * T / C.RSUN_CM ** 2
    ok("pure diffusion near the equator: longitude variance grows by 2 eta t/R^2 (1 %)", abs(grow / expect - 1) < 0.01,
       f"{grow:.4f} vs {expect:.4f} deg^2")
    sym = LocalBox((-10, 10), (0, 20), step_deg=0.1)
    Bs = gaussian_field(sym, 5.0, 8.0, 1.0, 300.0) - gaussian_field(sym, 3.0, 12.0, 1.0, 300.0)
    Bst = sym.evolve(Bs, T)
    ok("polarity inversion: B(t) -> -B(t)", np.allclose(sym.evolve(-Bs, T), -Bst, rtol=0, atol=1e-10 * np.abs(Bst).max()))
    ok("north-south reflection: B(t)(lat) -> B(t)(-lat), D -> -D",
       np.allclose(sym.evolve(Bs[::-1], T), Bst[::-1], rtol=0, atol=1e-10 * np.abs(Bst).max())
       and abs(sym.measures(Bst[::-1])["D_g"] + sym.measures(Bst)["D_g"]) <= 1e-10 * abs(sym.measures(Bst)["D_g"]))
    small = LocalBox((5, 25), (-5, 25), step_deg=0.1)
    wide = LocalBox((0, 30), (-10, 30), step_deg=0.1)
    mk = lambda bx: gaussian_field(bx, 15.0, 10.0, 1.0, 500.0) - gaussian_field(bx, 13.0, 6.0, 1.0, 480.0)   # noqa: E731
    Bsm, Bwd = small.evolve(mk(small), T), wide.evolve(mk(wide), T)
    inner = lambda bx: np.outer((bx.lat > 9) & (bx.lat < 21), (bx.lon > 0) & (bx.lon < 20))                  # noqa: E731
    a, b = small.measures(Bsm, inner(small)), wide.measures(Bwd, inner(wide))
    ok("boundary: widening the box changes the inner measures by < 1e-6 relative",
       all(abs(a[k] - b[k]) <= 1e-6 * max(abs(b[k]), 1e-30) for k in ("D_g", "phi_pos", "phi_neg")),
       f"D {abs(a['D_g'] - b['D_g']) / abs(b['D_g']):.1e}")
    # deposit: moments exact; out of range refused; the two-pixel case of Codex (unsigned flux and centroid change)
    rng = np.random.default_rng(3)
    la, lo, fl = rng.uniform(1, 24, 2000), rng.uniform(-9, 29, 2000), rng.normal(0, 1e19, 2000)
    Bd, nout = full.deposit(la, lo, fl)
    LAT, LON = np.meshgrid(full.lat, full.lon, indexing="ij")
    F = Bd * full.A
    sc = np.abs(fl).sum()
    ok("deposit conserves flux and the first moments in lon and sin(lat) (1e-12 of sum|F|)",
       nout == 0 and abs(F.sum() - fl.sum()) < 1e-12 * sc and abs((F * LON).sum() - (fl * lo).sum()) < 1e-12 * np.abs(fl * lo).sum()
       and abs((F * np.sin(np.radians(LAT))).sum() - (fl * np.sin(np.radians(la))).sum()) < 1e-12 * sc)
    ok("deposit outside the centre support: refused (None, count)", full.deposit([24.99], [10.0], [1.0]) == (None, 1))
    box2 = LocalBox((9, 11), (9, 11), step_deg=0.06)
    lat2, lon2, fl2 = np.array([10.0, 10.0]), np.array([10.0 - 0.015, 10.0 + 0.015]), np.array([1.0, -1.0])
    pix = C.field_measures(lat2, lon2, fl2, np.ones(2))
    Bg, _ = box2.deposit(lat2, lon2, fl2)
    rep = remap_report(pix, box2.measures(Bg * box2.A / box2.A))
    grid = box2.measures(Bg)
    ok("two pixels 0.03 deg apart on a 0.06 deg grid (Codex case): D kept, unsigned flux and centroids change and are "
       "reported by remap_report before any transport",
       abs(grid["D_g"] - C.field_measures(lat2, lon2, fl2 / 1.0, np.ones(2))["D_g"] * 1.0) <= 1e-12 * abs(grid["D_g"]) + 1e-30
       and grid["phi_pos"] < 0.9 * pix["phi_pos"] and abs(rep["d_lon_pos"]) > 0.005, f"phi_pos {grid['phi_pos']:.3f}, d_lon_pos {rep['d_lon_pos']:.4f}")
    if verbose:
        print(f"sft_local selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
