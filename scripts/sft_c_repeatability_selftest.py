"""Selftest of scripts/sft_c_repeatability.py on synthetic CEA patches (uncompressed, exact) and synthetic tables.

A. identical maps at t0 and t1 (1 h): every difference exactly zero, C_fin >= 25 deg^2;
B. field rotated relative to Carrington over the gap (2 days, to make the shift measurable): the persistence difference
   of the longitudes equals the shift, the rotation-only difference is much smaller; C_rot inside C_fin and smaller;
   A2: identical maps, C_rot ~ C_fin and secondary differences zero;
C. pixel noise with correlation rho between the two maps (no evolution): Var(dD)_rho / Var(dD)_0 = 1 - rho (0.8 -> 0.2);
D. one polarity: balanced -> balance_unavailable, raw still measured;
E. small patch -> finite_coverage_insufficient;
F. angular statistics at the seam (axial 89 / -89, circular 359 / 1);
G. weights 1/(K n_component);
H. bootstrap: no interval with fewer than 10 components; an interval containing the point value otherwise;
I. --run refused (spec not frozen).

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
        # B
        gap = 2.0
        shift = float(C.omega_rel_deg_day(15.0)) * gap
        b0 = write_patch(td, 2, t0, 15.0, 200.0, bipole(15.0, 200.0), ny=399, nx=599)       # 2-day margins need a larger patch
        b1 = write_patch(td, 2, t0 + pd.Timedelta(days=gap), 15.0, 200.0, bipole(15.0, 200.0, dlon=shift), ny=399, nx=599)
        rB = [r for r in CR.measure_pair(read, 2, b0, b1) if r["kind"] == "raw"][0]
        if rB["status"] != "ok":
            raise SystemExit(f"test B setup: {rB['status']} (area {rB.get('area_C_fin')})")
        ok("B. rotation relative to Carrington: persistence d_lon = shift, rotation-only difference much smaller",
           abs(rB["d_lon_pos"] - shift) < 0.15 * abs(shift) and abs(rB["drot_lon_pos"]) < 0.2 * abs(rB["d_lon_pos"]),
           f"shift {shift:.3f}, d {rB['d_lon_pos']:.3f}, drot {rB['drot_lon_pos']:.4f}")
        # the C_fin margins already include the rotation over the gap (observed-pilot margins), so C_rot = C_fin here:
        # C_rot is a safety restriction, not expected to bite with these margins
        ok("B2. C_rot inside C_fin, equal to it when the erosion margin covers the rotation (2 days); persistence on C_rot sees the shift",
           rB["rot_status"] == "ok" and rB["area_C_rot"] <= rB["area_C_fin"] + 1e-9 and abs(rB["area_C_rot"] - rB["area_C_fin"]) < 1e-9
           and abs(rB["dpers_rot_lon_pos"] - shift) < 0.15 * abs(shift),
           f"C_fin {rB['area_C_fin']:.1f}, C_rot {rB['area_C_rot']:.1f} deg2; persistence on C_rot {rB['dpers_rot_lon_pos']:.3f}")
        rA0 = [r for r in rA if r["kind"] == "raw"][0]
        ok("A2. identical maps at 1 h: C_rot nearly equal to C_fin, every secondary difference zero",
           rA0["area_C_rot"] > 0.95 * rA0["area_C_fin"] and all(abs(rA0[f"dpers_rot_{k}"]) < 1e-12 * max(1.0, abs(rA0[f"x0_{k}"]))
                                                               for k in CR.OBS if np.isfinite(rA0[f"x0_{k}"])),
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
        ok("D. one polarity: balanced -> balance_unavailable; raw measured", rD["balanced"] == "balance_unavailable" and rD["raw"] == "ok", str(rD))
        # E
        e0 = write_patch(td, 4, t0, 10.0, 10.0, bipole(10.0, 10.0), ny=49, nx=49)
        e1 = write_patch(td, 4, t0 + pd.Timedelta(hours=1), 10.0, 10.0, bipole(10.0, 10.0), ny=49, nx=49)
        rE = CR.measure_pair(read, 4, e0, e1)
        ok("E. small patch -> finite_coverage_insufficient", all(r["status"] == "finite_coverage_insufficient" for r in rE))
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
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
