"""Selftest of scripts/sft_c_repeatability.py on synthetic CEA patches (uncompressed, exact) and synthetic tables.

A. identical maps at t0 and t1 (1 h): every difference exactly zero, C_fin >= 25 deg^2;
B. field rotated relative to Carrington over 2 h at 40 deg (the real maximum lag): the persistence difference of the
   longitudes equals the shift, the rotation-only difference is much smaller; B2: C_rot inside C_fin, persistence on
   C_rot sees the shift; B3: a 2-day gap leaves C_rot below 25 deg^2 (explicit rot status, main still measured);
   A2: identical maps, C_rot inside C_fin and secondary persistence differences zero;
C. pixel noise with correlation rho between the two maps (no evolution): Var(dD)_rho / Var(dD)_0 = 1 - rho (0.8 -> 0.2);
D. one polarity: balanced -> balance_polarity_missing, raw still measured;
E. small patch -> finite_coverage_insufficient;
F. angular statistics at the seam (axial 89 / -89, circular 359 / 1);
G. weights 1/(K n_component);
H. bootstrap: no interval with fewer than 10 components; an interval containing the point value otherwise;
I. --run refused (spec not frozen).
Regressions for the Codex review b26c357 (each with the counterexample the previous rule got wrong):
J. (1) a valid and an invalid centre (NaN, then |Br| > cap) in one cell: the cell and the stencil cells of the invalid
   pixel are not observed; in a patch, C_fin loses them and no zero enters as data;
K. (2) negative polarity only outside C_fin: balanced -> balance_polarity_missing, raw measured and not rescaled;
   K2: extra negative flux outside C_fin: the balanced fluxes ON C_fin are equal;
L. (3) leading change at the +-180 seam (no spurious change) and with one polarity (undefined, not True);
M. (4) weights and bootstrap after missing values: component -> pair target, evaluable components counted, no crash;
N. (5) C_rot: N1 the numerical domain of dependence is exact (a perturbation outside it leaves the evolved field
   bitwise unchanged); N2 a cell with 8 of 16 preimage sub-points on an invalid cell is not in C_rot;
O. remapping recorded per instant on the full support: net flux and D kept, polarity fluxes not increased;
P. a pair_key without component is refused in the summaries and the bootstrap;
Q. fine grid 0.03 deg on the children of C_fin: same area; identical maps -> fine differences zero; the 2 h rotation
   of test B -> fine d_lon = shift and a small grid_dd; a NaN pixel at t0 -> explicit fine status (no re-selection)
   or a valid fine support; Q4 children() refuses a fine grid shifted by 1e-4 deg or truncated (no lost children);
R. operational assembly on a synthetic candidates table: selection/exclusions, every pair measured once (an unreadable
   map is a read_error status, never removed), denominators per kind and group (hemisphere, lag class, USFLUX tercile),
   summaries and bootstrap per group, input manifest before/after, run validity; tercile tie exactly on q2 -> class 2;
   R3 a failure after a successful read is technical_error, not read_error, and blocks the receipt; R4 all inputs good
   -> run valid, a dropped or duplicated (pair_key, preparation) key detected; R5 metadata_eligible strings 'False'
   excluded, other values refused, empty selection without crash and not valid; R6 real metadata terciles 28/27/27.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_c_repeatability_selftest.py
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
import sft_c_repeatability as CR  # noqa: E402
from sharpbl import geometry as geo, sft_core as C  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402

res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def write_patch(td, harp, t, lat0, lon0, field, ny=199, nx=299):
    from astropy.io import fits
    trec = t.strftime("%Y.%m.%d_%H:%M:%S") + "_TAI"
    h = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="degree", CRPIX1=(nx + 1) / 2, CRPIX2=(ny + 1) / 2, CRVAL1=lon0,
             CRVAL2=lat0, CDELT1=0.03, CDELT2=0.03, CROTA2=0.0, RSUN_REF=696000000, T_REC=trec, T_OBS=trec, CRLN_OBS=lon0, CRLT_OBS=0.0)
    hdr = fits.Header()
    for k, v in h.items():
        hdr[k] = v
    lon, lat = geo.lonlat_maps(hdr, (ny, nx))
    br = field(lon, lat)
    bm = np.where(np.abs(br) > 50, 34.0, 1.0)
    folder = record_dir(Path(td) / "fits", trec)
    folder.mkdir(parents=True, exist_ok=True)
    stem = file_stem(harp, trec)
    fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(br.astype(np.float64))]).writeto(folder / f"{stem}.Br.fits", overwrite=True)
    fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(bm.astype(np.float32))]).writeto(folder / f"{stem}.bitmap.fits", overwrite=True)
    (folder / f"{stem}.keys.json").write_text(json.dumps(h))
    return trec


def bipole(lat0, lon0, dlon=0.0, one=False):
    def f(lon, lat):
        dl = (lon - lon0 - dlon + 180) % 360 - 180
        b = 900 * np.exp(-((dl - 1.0) ** 2 + (lat - lat0 + 0.4) ** 2) / (2 * 0.5 ** 2))
        if not one:
            b = b - 800 * np.exp(-((dl + 1.0) ** 2 + (lat - lat0 - 0.4) ** 2) / (2 * 0.5 ** 2))
        return b
    return f


def with_edge_negative(field, width=0.4, amp=-800.0):
    """field plus a negative block within `width` deg of the patch edge at the lowest longitude."""
    def f(lon, lat):
        b = field(lon, lat)
        lat0 = 0.5 * (np.nanmin(lat) + np.nanmax(lat))
        return b + np.where((lon < np.nanmin(lon) + width) & (np.abs(lat - lat0) < 0.5), amp, 0.0)
    return f


def old_rotation_rule(box, P0, gap_s):
    """Superseded rule (before Codex b26c357 point 5), kept only as the counterexample: >= 8 of 16 sub-points."""
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


def main():
    t0 = pd.Timestamp("2014-05-01 10:00:00")
    with tempfile.TemporaryDirectory() as td:
        read = CR.OP.reader(Path(td) / "fits")
        # A
        a0 = write_patch(td, 1, t0, 15.0, 120.0, bipole(15.0, 120.0))
        a1 = write_patch(td, 1, t0 + pd.Timedelta(hours=1), 15.0, 120.0, bipole(15.0, 120.0))
        rA = CR.measure_pair(read, 1, a0, a1)
        zero = all(r["status"] == "ok" and all(abs(r[f"d_{k}"]) < 1e-12 * max(1.0, abs(r[f"x0_{k}"])) for k in CR.OBS if np.isfinite(r[f"x0_{k}"]))
                   for r in rA)
        ok("A. identical maps: every difference zero for raw, p1_source, balanced; C_fin >= 25 deg^2", zero and min(r["area_C_fin"] for r in rA) >= 25,
           f"areas {[round(r['area_C_fin'], 1) for r in rA]}")
        # B: 2 h at 40 deg (omega - omega_C ~ -0.77 deg/day: shift ~ -0.064 deg, about one cell)
        gap = 2.0 / 24.0
        shift = float(C.omega_rel_deg_day(40.0)) * gap
        b0 = write_patch(td, 2, t0, 40.0, 200.0, bipole(40.0, 200.0), ny=299, nx=399)       # C_rot loses up to 2.9 deg upstream
        b1 = write_patch(td, 2, t0 + pd.Timedelta(hours=2), 40.0, 200.0, bipole(40.0, 200.0, dlon=shift), ny=299, nx=399)
        rB = [r for r in CR.measure_pair(read, 2, b0, b1) if r["kind"] == "raw"][0]
        if rB["status"] != "ok" or rB["rot_status"] != "ok":
            raise SystemExit(f"test B setup: {rB['status']} / {rB.get('rot_status')} (areas {rB.get('area_C_fin')}, {rB.get('area_C_rot')})")
        ok("B. rotation relative to Carrington (2 h): persistence d_lon = shift, rotation-only difference much smaller",
           abs(rB["d_lon_pos"] - shift) < 0.15 * abs(shift) and abs(rB["drot_lon_pos"]) < 0.2 * abs(rB["d_lon_pos"]),
           f"shift {shift:.4f}, d {rB['d_lon_pos']:.4f}, drot {rB['drot_lon_pos']:.5f}")
        ok("B2. C_rot inside C_fin (numerical domain of dependence); persistence on C_rot sees the shift",
           rB["area_C_rot"] <= rB["area_C_fin"] + 1e-9 and abs(rB["dpers_rot_lon_pos"] - shift) < 0.15 * abs(shift),
           f"C_geo {rB['area_C_geo']:.1f}, C_fin {rB['area_C_fin']:.1f}, C_rot {rB['area_C_rot']:.1f} deg2; persistence on C_rot {rB['dpers_rot_lon_pos']:.4f}")
        gap2 = 2.0
        shift2 = float(C.omega_rel_deg_day(15.0)) * gap2
        c20 = write_patch(td, 5, t0, 15.0, 260.0, bipole(15.0, 260.0), ny=399, nx=599)
        c21 = write_patch(td, 5, t0 + pd.Timedelta(days=gap2), 15.0, 260.0, bipole(15.0, 260.0, dlon=shift2), ny=399, nx=599)
        rB3 = [r for r in CR.measure_pair(read, 5, c20, c21) if r["kind"] == "raw"][0]
        ok("B3. 2-day gap: C_rot below 25 deg2 -> rot_coverage_insufficient, secondary NaN, main measured (d_lon = shift)",
           rB3["status"] == "ok" and rB3["rot_status"] == "rot_coverage_insufficient" and np.isnan(rB3["drot_lon_pos"])
           and abs(rB3["d_lon_pos"] - shift2) < 0.15 * abs(shift2),
           f"C_fin {rB3['area_C_fin']:.1f}, C_rot {rB3['area_C_rot']:.1f} deg2")
        rA0 = [r for r in rA if r["kind"] == "raw"][0]
        ok("A2. identical maps at 1 h: C_rot inside C_fin, every secondary persistence difference zero",
           rA0["rot_status"] == "ok" and rA0["area_C_rot"] <= rA0["area_C_fin"] + 1e-9
           and all(abs(rA0[f"dpers_rot_{k}"]) < 1e-12 * max(1.0, abs(rA0[f"x0_{k}"])) for k in CR.OBS if np.isfinite(rA0[f"x0_{k}"])),
           f"C_rot / C_fin {rA0['area_C_rot'] / rA0['area_C_fin']:.3f}")
        # C
        rng = np.random.default_rng(36_300_901)
        var = {}
        for rho in (0.0, 0.8):
            dd = []
            for j in range(40):
                harp = 100 + j + (0 if rho == 0 else 100)
                n0 = rng.standard_normal((199, 299))
                n1 = rho * n0 + math.sqrt(1 - rho * rho) * rng.standard_normal((199, 299))
                f0 = (lambda nn: (lambda lon, lat: bipole(-12.0, 50.0)(lon, lat) + 60.0 * nn))(n0)
                f1 = (lambda nn: (lambda lon, lat: bipole(-12.0, 50.0)(lon, lat) + 60.0 * nn))(n1)
                c0 = write_patch(td, harp, t0 + pd.Timedelta(days=j), -12.0, 50.0, f0)
                c1 = write_patch(td, harp, t0 + pd.Timedelta(days=j, hours=1), -12.0, 50.0, f1)
                dd.append([r for r in CR.measure_pair(read, harp, c0, c1, kinds=("raw",))][0]["d_D_g"])
            var[rho] = float(np.var(dd, ddof=1))
        ratio = var[0.8] / var[0.0]
        ok("C. correlated pixel noise, no evolution: Var(dD) ratio rho 0.8 / rho 0 = 1 - rho = 0.2 (40 pairs each)",
           0.1 < ratio < 0.35, f"ratio {ratio:.3f}")
        # D
        d0 = write_patch(td, 3, t0, 20.0, 300.0, bipole(20.0, 300.0, one=True))
        d1 = write_patch(td, 3, t0 + pd.Timedelta(hours=1), 20.0, 300.0, bipole(20.0, 300.0, one=True))
        rD = {r["kind"]: r["status"] for r in CR.measure_pair(read, 3, d0, d1)}
        ok("D. one polarity: balanced -> balance_polarity_missing; raw measured", rD["balanced"] == "balance_polarity_missing" and rD["raw"] == "ok", str(rD))
        # E
        e0 = write_patch(td, 4, t0, 10.0, 10.0, bipole(10.0, 10.0), ny=49, nx=49)
        e1 = write_patch(td, 4, t0 + pd.Timedelta(hours=1), 10.0, 10.0, bipole(10.0, 10.0), ny=49, nx=49)
        rE = CR.measure_pair(read, 4, e0, e1)
        ok("E. small patch -> finite_coverage_insufficient", all(r["status"] == "finite_coverage_insufficient" for r in rE))
        # J (point 1): mixed cell in a patch: one NaN pixel inside the field
        def holed(field, cap=False):
            def f(lon, lat):
                b = field(lon, lat)
                b[99, 149] = 2e4 if cap else np.nan
                return b
            return f
        j0 = write_patch(td, 6, t0, 15.0, 120.0, holed(bipole(15.0, 120.0)))
        j1 = write_patch(td, 6, t0 + pd.Timedelta(hours=1), 15.0, 120.0, bipole(15.0, 120.0))
        jc0 = write_patch(td, 7, t0, 15.0, 120.0, holed(bipole(15.0, 120.0), cap=True))
        jc1 = write_patch(td, 7, t0 + pd.Timedelta(hours=1), 15.0, 120.0, bipole(15.0, 120.0))
        rJ = [r for r in CR.measure_pair(read, 6, j0, j1, kinds=("raw",))][0]
        rJc = [r for r in CR.measure_pair(read, 7, jc0, jc1, kinds=("raw",))][0]
        ok("J2. patch with one NaN (or above-cap) pixel at t0: C_fin loses its cells, C_geo does not; measures finite",
           rJ["status"] == "ok" and rJ["C_cells"] < rA0["C_cells"] and rJ["C_geo_cells"] == rA0["C_geo_cells"]
           and rJc["C_cells"] == rJ["C_cells"] and np.isfinite(rJ["x0_D_g"]) and np.isfinite(rJ["d_D_g"]),
           f"C_fin cells {rA0['C_cells']} -> {rJ['C_cells']} (NaN), {rJc['C_cells']} (cap); C_geo {rJ['C_geo_cells']}")
        # K (point 2): negative polarity only outside C_fin
        k0 = write_patch(td, 8, t0, 15.0, 140.0, with_edge_negative(bipole(15.0, 140.0, one=True)))
        k1 = write_patch(td, 8, t0 + pd.Timedelta(hours=1), 15.0, 140.0, with_edge_negative(bipole(15.0, 140.0, one=True)))
        rK = {r["kind"]: r for r in CR.measure_pair(read, 8, k0, k1)}
        # twin without the edge block (same geometry, hence same C_fin): raw on C_fin must be identical, i.e. neither
        # rescaled nor touched by the flux outside C_fin
        w0 = write_patch(td, 10, t0, 15.0, 140.0, bipole(15.0, 140.0, one=True))
        w1 = write_patch(td, 10, t0 + pd.Timedelta(hours=1), 15.0, 140.0, bipole(15.0, 140.0, one=True))
        rW = [r for r in CR.measure_pair(read, 10, w0, w1, kinds=("raw",))][0]
        ok("K. negative only outside C_fin: balanced -> balance_polarity_missing (the whole patch has both); raw measured, "
           "not rescaled (fluxes on C_fin = twin patch without the outside negative flux)",
           rK["balanced"]["status"] == "balance_polarity_missing" and rK["raw"]["status"] == "ok" and rK["raw"]["C_cells"] == rW["C_cells"]
           and rK["raw"]["x0_phi_neg"] == 0.0 and abs(rK["raw"]["x0_phi_pos"] / rW["x0_phi_pos"] - 1) < 1e-12
           and abs(rK["raw"]["x1_phi_pos"] / rW["x1_phi_pos"] - 1) < 1e-12,
           f"balanced {rK['balanced']['status']}; raw phi+ / twin {rK['raw']['x0_phi_pos'] / rW['x0_phi_pos']:.15f}, phi- {rK['raw']['x0_phi_neg']}")
        q0 = write_patch(td, 9, t0, 15.0, 160.0, with_edge_negative(bipole(15.0, 160.0)))
        q1 = write_patch(td, 9, t0 + pd.Timedelta(hours=1), 15.0, 160.0, with_edge_negative(bipole(15.0, 160.0)))
        rQ = {r["kind"]: r for r in CR.measure_pair(read, 9, q0, q1)}
        bq, rq = rQ["balanced"], rQ["raw"]
        ok("K2. extra negative flux outside C_fin: balanced fluxes equal ON C_fin at both instants (factors from C_fin)",
           bq["status"] == "ok" and abs(bq["x0_phi_pos"] / bq["x0_phi_neg"] - 1) < 1e-12 and abs(bq["x1_phi_pos"] / bq["x1_phi_neg"] - 1) < 1e-12,
           f"raw phi+/phi- on C_fin {rq['x0_phi_pos'] / rq['x0_phi_neg']:.4f}; balanced {bq['x0_phi_pos'] / bq['x0_phi_neg']:.15f}, "
           f"factors +{bq['bal_fpos_0']:.4f} -{bq['bal_fneg_0']:.4f}")
    # F
    ax = CR.angular_stats([89.0, -89.0], [1.0, 1.0], "axial")
    ci = CR.angular_stats([359.0, 1.0], [1.0, 1.0], "circular")
    ok("F. angular statistics at the seam: axial 89/-89 -> mean +-90, small SD; circular 359/1 -> mean 0, small SD",
       abs(abs(ax["mean"]) - 90.0) < 1e-9 and ax["circ_sd"] < 1.5 and abs(ci["mean"]) < 1e-9 and ci["circ_sd"] < 1.5,
       f"axial mean {ax['mean']:.3f} SD {ax['circ_sd']:.3f}; circular mean {ci['mean']:.3f} SD {ci['circ_sd']:.3f}")
    # G
    df = pd.DataFrame(dict(pair_key=["a", "b", "c", "d"], d_D_g=[1.0, 2.0, 2.0, 2.0]))
    comps = pd.Series({"a": 0, "b": 1, "c": 1, "d": 1})
    s = CR.summarise(df.assign(**{f"d_{k}": np.nan for k in CR.OBS if k != "D_g"}, **{f"drot_{k}": np.nan for k in CR.OBS},
                               **{f"dpers_rot_{k}": np.nan for k in CR.OBS},
                               d_dD_over_SD=np.nan, d_phi_uns=np.nan), comps)
    m = s[(s["diff"] == "d") & (s.quantity == "D_g")]["mean"].iloc[0]
    ok("G. weights 1/(K n_component): two components (1 and 3 pairs) -> mean 1.5", abs(m - 1.5) < 1e-12, f"mean {m}")
    # H
    rngb = np.random.default_rng(CR.SEED_BOOT)
    small = CR.bootstrap(df, comps, "d_D_g", rngb, n=100)
    big = pd.DataFrame(dict(pair_key=[f"p{i}" for i in range(30)], d_D_g=np.random.default_rng(1).normal(0, 1, 30)))
    bc = pd.Series({f"p{i}": i // 2 for i in range(30)})
    bb = CR.bootstrap(big, bc, "d_D_g", rngb, n=400)
    w = 1.0 / (15 * 2)
    pt = math.sqrt(np.average((big.d_D_g - big.d_D_g.mean()) ** 2, weights=np.full(30, w)))
    ok("H. bootstrap: no interval with < 10 components; percentile interval contains the point value otherwise",
       np.isnan(small["lo"]) and bb["lo"] <= pt <= bb["hi"], f"point {pt:.3f} in [{bb['lo']:.3f}, {bb['hi']:.3f}]")
    # I
    r = subprocess.run([sys.executable, str(ROOT / "scripts/sft_c_repeatability.py"), "--run"], capture_output=True, text=True)
    ok("I. --run refused while the spec is not frozen", r.returncode != 0 and "refused" in (r.stderr + r.stdout))
    # J1 (point 1): footprints on a small box, one valid and one invalid centre in the same cell
    bx = CR.L.LocalBox((10.0, 12.0), (20.0, 22.0), 0.06, meridional=False, diffusion=False)
    ly, lx = bx.lat_e[5], bx.lon_e[5]
    lat = np.array([ly + 0.01, ly + 0.045, bx.lat_e[6] + 0.03, bx.lat_e[10] + 0.03])
    lon = np.array([lx + 0.01, lx + 0.045, bx.lon_e[6] + 0.03, bx.lon_e[10] + 0.03])
    valid = np.array([True, False, True, True])
    G, V, nout = CR.footprints(bx, lat, lon, valid)
    old_V = CR.OP.coverage(bx, lat[valid], lon[valid])
    ok("J1. one valid and one invalid centre in a cell: cell in G, not in V (old rule: in V); the invalid pixel's stencil "
       "cell (6,6) with a valid centre is not in V; an isolated valid cell is",
       G[5, 5] and not V[5, 5] and old_V[5, 5] and G[6, 6] and not V[6, 6] and V[10, 10] and nout == 0)
    # L (point 3): leading change at the seam and with one polarity
    A2 = np.full(2, 1e18)
    mA = C.field_measures(np.array([10.0, 10.0]), np.array([179.0, -179.0]), np.array([100.0, -100.0]), A2)
    mB = C.field_measures(np.array([10.0, 10.0]), np.array([178.9, 179.5]), np.array([100.0, -100.0]), A2)
    mU = C.field_measures(np.array([10.0, 10.0]), np.array([178.9, 179.5]), np.array([100.0, 50.0]), A2)
    old = lambda a, b: bool(np.sign(a["lon_pos"] - a["lon_neg"]) != np.sign(b["lon_pos"] - b["lon_neg"])) if np.isfinite(a["lon_pos"]) and np.isfinite(b["lon_pos"]) else np.nan  # noqa: E731
    lc, lu = CR.leading_change(mA, mB), CR.leading_change(mA, mU)
    ok("L. leading change: seam (+179 / -179 -> 178.9 / 179.5, negative leading at both) no change (old: True); one "
       "polarity -> undefined (old: True)",
       mA["leading"] == -1 and mB["leading"] == -1 and lc is False and np.isnan(lu) and old(mA, mB) is True and old(mA, mU) is True,
       f"leading {mA['leading']}/{mB['leading']}, change {lc}; one polarity {lu}")
    # M (point 4): weights and bootstrap after missing values
    dfm = pd.DataFrame(dict(pair_key=["a", "b", "c", "d"], d_D_g=[1.0, 2.0, np.nan, 2.0]))
    sm = CR.summarise(dfm.assign(**{f"d_{k}": np.nan for k in CR.OBS if k != "D_g"}, **{f"drot_{k}": np.nan for k in CR.OBS},
                                 **{f"dpers_rot_{k}": np.nan for k in CR.OBS}, d_dD_over_SD=np.nan, d_phi_uns=np.nan), comps)
    rm = sm[(sm["diff"] == "d") & (sm.quantity == "D_g")].iloc[0]
    one = pd.DataFrame(dict(pair_key=[f"p{i}" for i in range(30)], d_D_g=[1.0, 2.0] + [np.nan] * 28))
    oc = pd.Series({f"p{i}": i // 2 for i in range(30)})
    b1 = CR.bootstrap(one, oc, "d_D_g", np.random.default_rng(CR.SEED_BOOT), n=200)
    nine = pd.DataFrame(dict(pair_key=[f"p{i}" for i in range(24)], d_D_g=np.r_[np.random.default_rng(2).normal(0, 1, 18), [np.nan] * 6]))
    nc = pd.Series({f"p{i}": i // 2 for i in range(24)})
    b9 = CR.bootstrap(nine, nc, "d_D_g", np.random.default_rng(CR.SEED_BOOT), n=200)
    fifteen = big.assign(d_D_g=np.where(np.arange(30) % 7 == 3, np.nan, big.d_D_g))
    b15 = CR.bootstrap(fifteen, bc, "d_D_g", np.random.default_rng(CR.SEED_BOOT), n=400)
    ok("M. missing values: component -> pair weights (mean 1.5, old rule 1.4), evaluable components counted (1 and 9 -> no "
       "interval, no crash), 15 with some missing -> interval, missing and failed replicates counted",
       abs(rm["mean"] - 1.5) < 1e-12 and rm["n_missing"] == 1 and rm["n_components"] == 2
       and b1["n_components"] == 1 and np.isnan(b1["lo"]) and b9["n_components"] == 9 and np.isnan(b9["lo"])
       and b15["n_components"] == 15 and b15["n_missing"] == 4 and b15["n_rep_failed"] == 0 and b15["lo"] < b15["hi"],
       f"mean {rm['mean']}; components {b1['n_components']}, {b9['n_components']}, {b15['n_components']}; "
       f"interval [{b15['lo']:.3f}, {b15['hi']:.3f}]")
    # N1 (point 5): the domain of dependence is exact for the effective transport (rotation-only LocalBox.evolve)
    rngn = np.random.default_rng(36_300_902)
    bn = CR.L.LocalBox((20.0, 45.0), (100.0, 110.0), 0.06, meridional=False, diffusion=False)
    V0 = np.ones((bn.ny, bn.nx), bool)
    V0[:, :3] = V0[:, -3:] = False
    for _ in range(12):
        y, x = rngn.integers(0, bn.ny - 10), rngn.integers(0, bn.nx - 10)
        V0[y:y + rngn.integers(1, 10), x:x + rngn.integers(1, 10)] = False
    gap_n = 7200.0
    Bn = rngn.normal(0, 100, (bn.ny, bn.nx))
    Bp = Bn + np.where(V0, 0.0, rngn.normal(0, 300, (bn.ny, bn.nx)))
    dn = np.abs(bn.evolve(Bp, gap_n) - bn.evolve(Bn, gap_n))
    taint = CR.rotation_dependence(bn, V0, gap_n)
    ok("N1. rotation-only transport over 2 h: perturbing only cells outside V0 leaves the field bitwise unchanged outside "
       "the computed domain of dependence (and changes it inside)",
       dn[~taint].max() == 0.0 and dn[taint & V0].max() > 0, f"steps {CR.transport_steps(bn, gap_n)}, max change outside "
       f"{dn[~taint].max():.1e}, inside (valid cells) {dn[taint & V0].max():.1e}; tainted valid cells {int((taint & V0).sum())}")
    # N2 (point 5): 8 valid and 8 invalid preimage sub-points are not full coverage
    b2 = CR.L.LocalBox((38.5, 41.5), (100.0, 103.0), 0.06, meridional=False, diffusion=False)
    gap2 = 0.5 * b2.step / abs(float(C.omega_rel_deg_day(40.0))) * C.DAY         # rotation shift = half a cell at 40 deg
    P0 = np.ones((b2.ny, b2.nx), bool)
    j = b2.nx // 2
    P0[:, j] = False
    yy = b2.ny // 2
    oldc, t2 = old_rotation_rule(b2, P0, gap2), CR.rotation_dependence(b2, P0, gap2)
    ok("N2. a cell whose preimage has 8 of 16 sub-points on an invalid cell: old rule covered, new rule excluded from C_rot",
       oldc[yy, j - 1] and t2[yy, j - 1], f"gap {gap2:.0f} s; old {bool(oldc[yy, j - 1])}, excluded {bool(t2[yy, j - 1])}")
    # O: remapping report (identical maps of test A, raw): full-support net flux and D kept by the deposit
    rO = rA0
    tolO = 1e-12 * max(abs(rO["x0_phi_pos"]), abs(rO["x0_phi_neg"]))
    ok("O. remapping recorded at both instants (raw, balanced = raw deposit): net flux and D kept on the full support, "
       "polarity fluxes not increased by cancellation",
       all(abs(rO[f"remap{j}_phi_net"]) <= tolO and abs(rO[f"remap{j}_D_g"]) <= 1e-12 * abs(rO["x0_D_g"]) + 1e-30
           and rO[f"remap{j}_phi_pos"] <= tolO for j in (0, 1))
       and all(r[f"remap0_{k}"] == rO[f"remap0_{k}"] for r in rA if r["kind"] == "balanced" for k in ("phi_pos", "lon_neg")),
       f"d phi_pos {rO['remap0_phi_pos']:.3e}, d lon_pos {rO['remap0_lon_pos']:.2e}, d D {rO['remap0_D_g']:.1e}")
    # Q: fine grid
    qa = [r for r in rA if r["kind"] == "raw"][0]
    ok("Q1. fine grid on the children of C_fin: same area (1e-9), identical maps -> fine differences zero for every preparation",
       qa["fine_status"] == "ok" and abs(qa["area_fine"] / qa["area_C_fin"] - 1) < 1e-9
       and all(r["fine_kind_status"] == "ok" and all(abs(r[f"fine_d_{k}"]) < 1e-12 * max(1.0, abs(r[f"fine_x0_{k}"]))
                                                    for k in CR.OBS if np.isfinite(r[f"fine_x0_{k}"])) for r in rA),
       f"areas {qa['area_C_fin']:.3f} / {qa['area_fine']:.3f}")
    ok("Q2. 2 h rotation (test B): fine d_lon = shift, grid_dd small compared with the shift",
       rB["fine_status"] == "ok" and abs(rB["fine_d_lon_pos"] - shift) < 0.15 * abs(shift) and abs(rB["grid_dd_lon_pos"]) < 0.1 * abs(shift),
       f"fine d {rB['fine_d_lon_pos']:.4f}, grid_dd {rB['grid_dd_lon_pos']:.2e}, D grid_dd {rB['grid_dd_D_g']:.2e}")
    ok("Q3. NaN pixel at t0 (test J2): fine status explicit or fine support valid; no re-selection (C_fin cells unchanged)",
       rJ["fine_status"] in ("ok", "fine_support_invalid") and rJ["C_cells"] == rJc["C_cells"],
       f"fine status {rJ['fine_status']}, invalid children {rJ['fine_cells_invalid']}")
    # Q4: children() negative regressions (Codex counterexamples: shifted by 1e-4 deg, truncated to 80 %)
    bq = CR.L.LocalBox((10.0, 12.0), (20.0, 22.0), 0.06, meridional=False, diffusion=False)
    Cq = np.ones((bq.ny, bq.nx), bool)
    refused = []
    for fb in (CR.L.LocalBox((10.0001, 12.0001), (20.0, 22.0), 0.03, meridional=False, diffusion=False),
               CR.L.LocalBox((10.0, 12.0), (20.0, 21.6), 0.03, meridional=False, diffusion=False)):
        try:
            CR.children(bq, fb, Cq)
            refused.append(False)
        except ValueError:
            refused.append(True)
    good = CR.children(bq, CR.L.LocalBox((10.0, 12.0), (20.0, 22.0), 0.03, meridional=False, diffusion=False), Cq)
    ok("Q4. children(): fine grid shifted by 1e-4 deg refused, truncated fine grid refused, exact refinement keeps every child",
       all(refused) and int(good.sum()) == 4 * int(Cq.sum()), f"refused {refused}")
    # R: operational assembly (synthetic candidates and patches)
    with tempfile.TemporaryDirectory() as tdr:
        rows = []
        spec = [(201, 12.0, 30.0, 1, 5e21, 11), (202, -14.0, 60.0, 2, 9e21, 12), (203, 18.0, 90.0, 1, 2e22, 13),
                (204, -20.0, 120.0, 2, 4e21, 13), (205, 10.0, 150.0, 1, 1.5e22, 14), (206, -11.0, 180.0, 2, 7e21, 15)]
        for harp, lat0, lon0, hours, fl, comp in spec:
            ta = t0 + pd.Timedelta(days=harp - 200)
            a = write_patch(tdr, harp, ta, lat0, lon0, bipole(lat0, lon0))
            b = write_patch(tdr, harp, ta + pd.Timedelta(hours=hours), lat0, lon0, bipole(lat0, lon0))
            rows.append(dict(node=harp, HARPNUM=harp, T_REC_a=a, T_REC_b=b, gap_ns=int(hours * 3600e9), area_deg2=50.0, family=harp,
                             USFLUX_t0=fl, LON_FWT_t0=0.0, LAT_FWT_t0=lat0, pregraph_reasons="", component=comp, protected_component=False,
                             metadata_eligible=True))
        rows.append(dict(rows[0], node=900, HARPNUM=900, metadata_eligible=False, pregraph_reasons="geometry", component=900))
        cand = pd.DataFrame(rows)
        paths = CR.file_paths(Path(tdr) / "fits")
        paths(206, rows[5]["T_REC_b"])[0].unlink()                    # pair 206: unreadable map at t1
        prods, info = CR.assemble(cand, CR.OP.reader(Path(tdr) / "fits"), paths, n_boot=50)
        M, Dn = prods["MEASUREMENTS"], prods["DENOMINATORS"]
        dall = Dn[(Dn.group == "all")]
        groups = set(Dn.group)
        ok("R1. assembly: 6 selected, 1 excluded, 18 measurement rows (unreadable pair kept as read_error), denominators per "
           "kind and group, summaries and bootstrap per group; missing input -> run not valid",
           len(prods["SELECTION"]) == 6 and len(prods["EXCLUSIONS"]) == 1 and len(M) == 18 and M.pair_key.nunique() == 6
           and (M[M.HARPNUM == 206].status.str.startswith("read_error")).all() and (dall.selected == 6).all()
           and (dall.filter(like="failed_read_error").sum(axis=1) == 1).all()
           and {"hemisphere=N", "hemisphere=S", "lag_class=le_1.5h", "lag_class=gt_1.5h_le_2h", "flux_tercile=1", "flux_tercile=3"} <= groups
           and len(prods["SUMMARY"]) > 0 and (prods["BOOTSTRAP"].lo.isna()).all() and not info["run_valid"] and not info["all_inputs_present"],
           f"groups {sorted(groups)[:8]}; info {dict((k, info[k]) for k in ('selected', 'components', 'run_valid', 'manifest_unchanged'))}")
        tie = cand[cand.metadata_eligible].copy()
        tie["USFLUX_t0"] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        tie = pd.concat([tie, tie.assign(node=tie.node + 1000, HARPNUM=tie.HARPNUM + 1000, USFLUX_t0=[7.0, 8.0, 9.0, 10.0, 11.0, 12.0])])
        tie = pd.concat([tie, tie.iloc[:1].assign(node=5000, HARPNUM=5000, USFLUX_t0=13.0)])
        st, _, tq = CR.selection(tie)                                  # n = 13: (n-1) 2/3 = 8, q2 = x[8] = 9 exactly
        ok("R2. tercile tie exactly on q2 (n 13, q2 = 9 = a sample): that pair is class 2 (q1 < x <= q2)",
           tq["tercile_q2"] == 9.0 and st[st.USFLUX_t0 == 9.0].flux_tercile.iloc[0] == "2", f"q {tq}")
        good = cand[cand.HARPNUM != 206]
        base_read = CR.OP.reader(Path(tdr) / "fits")

        def no_tobs(h, t):                                            # read succeeds, the computation fails (KeyError)
            br_, bm_, hh = base_read(h, t)
            if int(h) == 203:
                hh = dict(hh)
                hh.pop("T_OBS")
            return br_, bm_, hh
        p3, i3 = CR.assemble(good, no_tobs, paths, n_boot=20)
        M3 = p3["MEASUREMENTS"]
        ok("R3. failure after a successful read -> technical_error (not read_error), the pair kept, run not valid",
           (M3[M3.HARPNUM == 203].status == "technical_error:KeyError").all() and i3["technical_errors"] == 3 and i3["read_errors"] == 0
           and not i3["run_valid"] and i3["measurement_keys_exact"], f"{M3[M3.HARPNUM == 203].status.tolist()}")
        p4, i4 = CR.assemble(good, base_read, paths, n_boot=20)
        M4 = p4["MEASUREMENTS"]
        dropped = CR.measurement_keys_exact(M4.drop(index=M4.index[0]), p4["SELECTION"])
        dup = CR.measurement_keys_exact(pd.concat([M4, M4.iloc[:1]]), p4["SELECTION"])
        ok("R4. every input good -> run valid; a dropped or a duplicated (pair_key, preparation) key is detected",
           i4["run_valid"] and i4["measurement_keys_exact"] and not dropped and not dup, f"info {i4}")
        c5 = good.assign(metadata_eligible=["True", "False", "True", "False", "True", "False"])
        s5, e5, _ = CR.selection(c5)
        try:
            CR.selection(good.assign(metadata_eligible=["True", "maybe", "True", "True", "True", "False"]))
            bad5 = False
        except ValueError:
            bad5 = True
        p5, i5 = CR.assemble(good.assign(metadata_eligible=False), base_read, paths, n_boot=20)
        ok("R5. 'False' strings excluded, other values refused; empty selection: no crash, explicit empty products, not valid",
           len(s5) == 3 and len(e5) == 3 and bad5 and i5["selected"] == 0 and not i5["run_valid"] and list(p5["SELECTION"].columns)[:3] == ["pair_key", "node", "HARPNUM"],
           f"selected {len(s5)}, excluded {len(e5)}, empty info {i5['selected']} {i5['run_valid']}")
    cand_real = pd.read_csv(CR.CANDIDATES)                            # metadata only (no pixel)
    s6, _, q6 = CR.selection(cand_real)
    f6 = np.sort(s6.USFLUX_t0.astype(float).to_numpy())
    ok("R6. real metadata: q2 = x[54] exactly (integral rational index), classes 28/27/27, HARP 3098 pair in class 2",
       q6["tercile_q2"] == f6[54] and s6.flux_tercile.value_counts().to_dict() == {"1": 28, "2": 27, "3": 27}
       and s6[s6.pair_key.str.startswith("3098|2013.08.19_22")].flux_tercile.iloc[0] == "2", f"{q6} {s6.flux_tercile.value_counts().to_dict()}")
    # P: pair_key without component
    bad = dfm.assign(pair_key=["a", "b", "c", "zz"])
    raised = []
    for fn in (lambda: CR.summarise(bad.assign(**{f"d_{k}": np.nan for k in CR.OBS if k != "D_g"}, **{f"drot_{k}": np.nan for k in CR.OBS},
                                               **{f"dpers_rot_{k}": np.nan for k in CR.OBS}, d_dD_over_SD=np.nan, d_phi_uns=np.nan), comps),
               lambda: CR.bootstrap(bad, comps, "d_D_g", np.random.default_rng(1), n=10)):
        try:
            fn()
            raised.append(False)
        except ValueError:
            raised.append(True)
    ok("P. pair_key without component: refused in summarise and bootstrap (not treated as a missing value)", all(raised), str(raised))
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
