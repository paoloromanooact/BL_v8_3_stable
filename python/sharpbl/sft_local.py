"""Preparatory 2D local transport for the observed-evolution pilot (point 3; draft protocol rev. 2, not frozen).

Synthetic use only; no observed map is read. Equation in the Carrington frame (draft §5):
  dB/dt = -(omega(lat) - omega_C) dB/dphi - 1/(R cos lat) d(v B cos lat)/dlat + eta lap_h B,
finite volumes on a regular lon-lat box (degrees) with exact spherical cell areas, zero-flux box edges.
Scheme (draft §5, an open point of the review): Crank-Nicolson for diffusion (sparse LU factorised once) and explicit
second-order upwind advection (Heun), fixed step. Deposit from pixel coordinates to the grid: linear weights in
longitude and in s = sin(lat) between neighbouring cell centres, conserving flux and the first moments in lon and s
(hence D).
"""
from __future__ import annotations

import numpy as np
from scipy.sparse import diags, identity, kron
from scipy.sparse.linalg import splu

from sharpbl import sft_core as C

DAY = C.DAY


class LocalBox:
    def __init__(self, lat_range, lon_range, step_deg=0.06, eta_km2s=C.REFERENCE["eta_km2s"], du_kms=C.REFERENCE["du_kms"],
                 p=C.REFERENCE["p"], r_cm=C.RSUN_CM, dt_s=600.0, rotation=True, meridional=True, diffusion=True):
        self.r, self.dt, self.step = r_cm, dt_s, step_deg
        self.lat_e = np.arange(lat_range[0], lat_range[1] + 1e-9, step_deg)
        self.lon_e = np.arange(lon_range[0], lon_range[1] + 1e-9, step_deg)
        self.lat = 0.5 * (self.lat_e[:-1] + self.lat_e[1:])
        self.lon = 0.5 * (self.lon_e[:-1] + self.lon_e[1:])
        self.ny, self.nx = len(self.lat), len(self.lon)
        dphi, dlam = np.radians(step_deg), np.radians(step_deg)
        self.area_row = r_cm ** 2 * dphi * (np.sin(np.radians(self.lat_e[1:])) - np.sin(np.radians(self.lat_e[:-1])))
        self.A = np.repeat(self.area_row[:, None], self.nx, axis=1)
        lat_r, latf_r = np.radians(self.lat), np.radians(self.lat_e)
        eta = eta_km2s * 1e10 if diffusion else 0.0
        # zonal velocity at the cell centres (cm/s) and meridional velocity at the lat faces (cm/s)
        self.u = (np.radians(C.omega_rel_deg_day(self.lat)) / DAY * r_cm * np.cos(lat_r)) if rotation else np.zeros(self.ny)
        self.vf = C.v_merid_cm_s(latf_r, du_kms, p) if meridional else np.zeros(self.ny + 1)
        self.vf[[0, -1]] = 0.0
        self.len_zonal = r_cm * dlam                         # length of a constant-lon face
        self.len_merid = r_cm * np.cos(latf_r) * dphi        # length of a constant-lat face
        # diffusion operator (flux form, zero flux at the box edges), acting on the flattened field (row = lat)
        n = self.ny * self.nx
        dx_c = r_cm * np.cos(lat_r) * dphi                   # zonal distance between centres in each row
        wz = eta * self.len_zonal / dx_c                     # conductance across zonal faces, per row
        wm = eta * self.len_merid[1:-1] / (r_cm * dlam)      # conductance across interior lat faces
        ex = np.ones(self.nx)
        Lx_row = diags([ex[:-1], np.r_[-1.0, -2.0 * ex[1:-1], -1.0], ex[:-1]], [-1, 0, 1], shape=(self.nx, self.nx))
        Lx = kron(diags(wz), Lx_row)
        main = np.zeros(self.ny)
        main[:-1] -= wm
        main[1:] -= wm
        Ly = kron(diags([wm, main, wm], [-1, 0, 1], shape=(self.ny, self.ny)), identity(self.nx))
        Ainv = diags(1.0 / self.A.ravel())
        self.Ldif = (Ainv @ (Lx + Ly)).tocsc()
        I = identity(n, format="csc")
        self._lu = splu((I - 0.5 * dt_s * self.Ldif).tocsc())
        self._rhs = (I + 0.5 * dt_s * self.Ldif).tocsr()

    # advection: flux divergence with second-order upwind face values (zero flux at the box edges)
    def _adv(self, B):
        out = np.zeros_like(B)
        if np.any(self.u):
            u = self.u[:, None]
            Fz = np.zeros((self.ny, self.nx + 1))
            bl = B[:, :-1] + 0.5 * np.diff(np.pad(B, ((0, 0), (1, 0)), mode="edge")[:, :-1], axis=1)   # from the left
            br = B[:, 1:] - 0.5 * np.diff(np.pad(B, ((0, 0), (0, 1)), mode="edge")[:, 1:], axis=1)    # from the right
            Fz[:, 1:-1] = np.where(u > 0, u * bl, u * br) * self.len_zonal
            out -= (Fz[:, 1:] - Fz[:, :-1])
        if np.any(self.vf):
            v = self.vf[1:-1, None]
            Fm = np.zeros((self.ny + 1, self.nx))
            bs = B[:-1] + 0.5 * np.diff(np.pad(B, ((1, 0), (0, 0)), mode="edge")[:-1], axis=0)
            bn = B[1:] - 0.5 * np.diff(np.pad(B, ((0, 1), (0, 0)), mode="edge")[1:], axis=0)
            Fm[1:-1] = np.where(v > 0, v * bs, v * bn) * self.len_merid[1:-1, None]
            out -= (Fm[1:] - Fm[:-1])
        return out / self.A

    def step_once(self, B):
        k1 = self._adv(B)
        k2 = self._adv(B + self.dt * k1)
        Bs = B + 0.5 * self.dt * (k1 + k2)
        return self._lu.solve(self._rhs @ Bs.ravel()).reshape(B.shape)

    def evolve(self, B0, t_s):
        n = int(round(t_s / self.dt))
        if abs(n * self.dt - t_s) > 1e-6:
            raise ValueError("t must be a multiple of dt")
        B = np.asarray(B0, float).copy()
        for _ in range(n):
            B = self.step_once(B)
        return B

    def deposit(self, lat_deg, lon_deg, flux):
        """Flux (Mx) of pixel centres to the grid: linear weights in lon and in s; returns B (G). Points outside the
        centre range are counted and clipped."""
        lat_deg, lon_deg, flux = (np.asarray(x, float).ravel() for x in (lat_deg, lon_deg, flux))
        s_c = np.sin(np.radians(self.lat))
        s = np.sin(np.radians(lat_deg))
        iy = np.clip(np.searchsorted(s_c, s) - 1, 0, self.ny - 2)
        wy = (s - s_c[iy]) / (s_c[iy + 1] - s_c[iy])
        ix = np.clip(np.searchsorted(self.lon, lon_deg) - 1, 0, self.nx - 2)
        wx = (lon_deg - self.lon[ix]) / (self.lon[ix + 1] - self.lon[ix])
        outside = int(((wy < 0) | (wy > 1) | (wx < 0) | (wx > 1)).sum())
        wy, wx = np.clip(wy, 0, 1), np.clip(wx, 0, 1)
        F = np.zeros((self.ny, self.nx))
        for dy, fy in ((0, 1 - wy), (1, wy)):
            for dx, fx in ((0, 1 - wx), (1, wx)):
                np.add.at(F, (iy + dy, ix + dx), flux * fy * fx)
        return F / self.A, outside

    def measures(self, B, mask=None, threshold=0.0):
        LAT, LON = np.meshgrid(self.lat, self.lon, indexing="ij")
        m = np.ones(B.shape, bool) if mask is None else mask
        return C.field_measures(LAT[m], LON[m], B[m], self.A[m], self.r, threshold)


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
    ok("identity at dt = 0: measures of the same field coincide", full.measures(B0) == full.measures(full.evolve(B0, 0.0)))
    Bt = full.evolve(B0, T)
    f0, ft = (B0 * full.A).sum(), (Bt * full.A).sum()
    ok("net flux conserved with rotation, meridional flow and diffusion, zero-flux box (rel 1e-12 of the unsigned flux)",
       abs(ft - f0) <= 1e-12 * (np.abs(B0) * full.A).sum(), f"{abs(ft - f0) / (np.abs(B0) * full.A).sum():.1e}")
    # pure rotation: translation in longitude by omega_rel(lat0) t
    rot = LocalBox((10, 20), (0, 20), step_deg=0.05, meridional=False, diffusion=False)
    G = gaussian_field(rot, 15.0, 8.0, 1.0, 100.0)
    Gt = rot.evolve(G, T)
    LATr, LONr = np.meshgrid(rot.lat, rot.lon, indexing="ij")
    c0 = C.geo.weighted_centroid(LONr.ravel(), LATr.ravel(), (G * rot.A).ravel())
    ct = C.geo.weighted_centroid(LONr.ravel(), LATr.ravel(), (np.clip(Gt, 0, None) * rot.A).ravel())
    shift = ct[0] - c0[0]
    expect = C.omega_rel_deg_day(15.0) * 3.0
    ok("pure rotation: centroid moves by (omega - omega_C) t at the centroid latitude (0.01 deg)", abs(shift - expect) < 0.01,
       f"{shift:.4f} vs {expect:.4f}")
    # pure diffusion, local limit: each in-plane variance grows by 2 eta t / R^2
    dif = LocalBox((-8, 8), (-8, 8), step_deg=0.05, rotation=False, meridional=False, dt_s=1800.0)
    G = gaussian_field(dif, 0.0, 0.0, 1.0, 1.0)
    Gt = dif.evolve(G, T)
    LAT, LON = np.meshgrid(dif.lat, dif.lon, indexing="ij")
    var = lambda F, X: float((F * dif.A * X ** 2).sum() / (F * dif.A).sum())          # noqa: E731
    grow = var(Gt, LON) - var(G, LON)
    expect = np.degrees(1.0) ** 2 * 2 * C.REFERENCE["eta_km2s"] * 1e10 * T / C.RSUN_CM ** 2
    ok("pure diffusion near the equator: longitude variance grows by 2 eta t/R^2 (1 %)", abs(grow / expect - 1) < 0.01,
       f"{grow:.4f} vs {expect:.4f} deg^2")
    # polarity inversion and north-south reflection on a symmetric box
    sym = LocalBox((-10, 10), (0, 20), step_deg=0.1)
    Bs = gaussian_field(sym, 5.0, 8.0, 1.0, 300.0) - gaussian_field(sym, 3.0, 12.0, 1.0, 300.0)
    Bst = sym.evolve(Bs, T)
    ok("polarity inversion: B(t) -> -B(t)", np.allclose(sym.evolve(-Bs, T), -Bst, rtol=0, atol=1e-10 * np.abs(Bst).max()))
    ok("north-south reflection: B(t)(lat) -> B(t)(-lat), D -> -D",
       np.allclose(sym.evolve(Bs[::-1], T), Bst[::-1], rtol=0, atol=1e-10 * np.abs(Bst).max())
       and abs(sym.measures(Bst[::-1])["D_g"] + sym.measures(Bst)["D_g"]) <= 1e-10 * abs(sym.measures(Bst)["D_g"]))
    # boundary: widening the box does not change the measures on an inner common domain
    small = LocalBox((5, 25), (-5, 25), step_deg=0.1)
    wide = LocalBox((0, 30), (-10, 30), step_deg=0.1)
    mk = lambda bx: gaussian_field(bx, 15.0, 10.0, 1.0, 500.0) - gaussian_field(bx, 13.0, 6.0, 1.0, 480.0)   # noqa: E731
    Bsm, Bwd = small.evolve(mk(small), T), wide.evolve(mk(wide), T)
    inner = lambda bx: np.meshgrid((bx.lat > 9) & (bx.lat < 21), (bx.lon > 0) & (bx.lon < 20), indexing="ij")   # noqa: E731
    msk = lambda bx: inner(bx)[0] & inner(bx)[1]                                                               # noqa: E731
    a, b = small.measures(Bsm, msk(small)), wide.measures(Bwd, msk(wide))
    ok("boundary: widening the box changes the inner measures by < 1e-6 relative",
       all(abs(a[k] - b[k]) <= 1e-6 * max(abs(b[k]), 1e-30) for k in ("D_g", "phi_pos", "phi_neg")),
       f"D {abs(a['D_g'] - b['D_g']) / abs(b['D_g']):.1e}")
    # deposit: flux and first moments in lon and s
    rng = np.random.default_rng(3)
    la, lo, fl = rng.uniform(1, 24, 2000), rng.uniform(-9, 29, 2000), rng.normal(0, 1e19, 2000)
    Bd, nout = full.deposit(la, lo, fl)
    LAT, LON = np.meshgrid(full.lat, full.lon, indexing="ij")
    F = Bd * full.A
    ok("deposit conserves flux and the first moments in lon and sin(lat) (rel 1e-12), nothing outside",
       nout == 0 and abs(F.sum() - fl.sum()) < 1e-12 * np.abs(fl).sum()
       and abs((F * LON).sum() - (fl * lo).sum()) < 1e-12 * np.abs(fl * lo).sum()
       and abs((F * np.sin(np.radians(LAT))).sum() - (fl * np.sin(np.radians(la))).sum()) < 1e-12 * np.abs(fl).sum())
    if verbose:
        print(f"sft_local selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
