"""Selftest of the preparatory SFT code (synthetic only; protocols not frozen; no observed map read).

Runs the selftests of python/sharpbl/sft_core.py and sft_local.py and adds the consistency with the P1 measurement on a
synthetic CEA patch, whose header uses the same WCS keywords as the SHARP sidecars (CRLN-CEA/CRLT-CEA, 0.03 deg,
RSUN_REF 696 Mm; values invented, no file read):
- point 2: polarities rescaled to phibar, linear deposit in s, D of the 1D profile = d_axial_bal_g of measure_v84;
- point 3: pixel fluxes deposited on the local box, D of the grid field = d_axial_g of measure_v84 (pixels >= 100 G).

    OMP_NUM_THREADS=1 PYTHONPATH=python .venv/bin/python scripts/sft_prep_selftest.py
"""
import sys
from pathlib import Path

import numpy as np
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo, measure, sft_core as C, sft_local as L  # noqa: E402


def synthetic_patch():
    h = fits.Header()
    for k, v in dict(T_REC="2015.01.12_22:00:00_TAI", CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="degree",
                     CRPIX1=300.5, CRPIX2=200.5, CRVAL1=124.3, CRVAL2=-15.0, CDELT1=0.03, CDELT2=0.03, CROTA2=0.0,
                     RSUN_REF=696000000, CRLN_OBS=110.0, CRLT_OBS=-4.3).items():
        h[k] = v
    shape = (400, 600)
    lon, lat = geo.lonlat_maps(h, shape)
    br = np.zeros(shape)
    for (lo0, la0), amp in (((127.0, -16.0), 900.0), ((121.0, -13.5), -800.0), ((125.0, -12.0), 150.0)):
        br += amp * np.exp(-((lon - lo0) ** 2 + (lat - la0) ** 2) / (2 * 0.8 ** 2))
    br += np.random.default_rng(7).normal(0, 8, shape)
    bitmap = np.full(shape, 34.0)
    bitmap[:, :20] = 1.0                                    # some exterior pixels, excluded as in P1
    return br, bitmap, h, lon, lat


def p1_consistency():
    res = []
    br, bitmap, h, lon, lat = synthetic_patch()
    m = measure.measure_v84(br, bitmap, h)
    area = geo.pixel_area_cm2(h)
    r = geo.rsun_cm(h)
    mask = measure.base_mask(br, bitmap, 33, measure.MAX_ABS_BR_G) & (np.abs(br) >= measure.THRESHOLD_G)
    pos, neg = mask & (br > 0), mask & (br < 0)
    phip, phin = br[pos].sum() * area, -br[neg].sum() * area
    phibar = 0.5 * (phip + phin)
    bal = np.zeros_like(br)
    bal[pos] = br[pos] * phibar / phip
    bal[neg] = br[neg] * phibar / phin
    s1 = C.SFT1D(r_cm=r)
    cf, nout = C.deposit_linear(np.sin(np.radians(lat[mask])), bal[mask] * area, s1.s)
    d1 = s1.dipole(s1.profile(cf))
    rel1 = abs(d1 - m["d_axial_bal_g"]) / abs(m["d_axial_bal_g"])
    res.append(("point 2: rescaled map deposited in s gives D = d_axial_bal_g of measure_v84 (rel 1e-12)", nout == 0 and rel1 < 1e-12,
                f"{rel1:.1e}"))
    box = L.LocalBox((float(lat[mask].min()) - 1, float(lat[mask].max()) + 1), (float(lon[mask].min()) - 1, float(lon[mask].max()) + 1),
                     step_deg=0.06, r_cm=r)
    Bg, nout2 = box.deposit(lat[mask], lon[mask], br[mask] * area)
    d2 = box.measures(Bg)["D_g"]
    rel2 = abs(d2 - m["d_axial_g"]) / abs(m["d_axial_g"])
    res.append(("point 3: pixels deposited on the local box give D = d_axial_g of measure_v84 (rel 1e-12)", nout2 == 0 and rel2 < 1e-12,
                f"{rel2:.1e}"))
    fm = box.measures(Bg)
    res.append(("point 3 (P1 pixels): fluxes on the grid = phi_pos/phi_neg of measure_v84 in this well-separated case (rel 1e-12); "
                "not a general identity (see the remap report)",
                abs(fm["phi_pos"] - m["phi_pos_mx"]) < 1e-12 * m["phi_pos_mx"] and abs(fm["phi_neg"] - m["phi_neg_mx"]) < 1e-12 * m["phi_neg_mx"]))
    # point 3 main field: all finite pixels, no bitmap and no threshold (weak field and noise included)
    raw = np.isfinite(br) & (np.abs(br) <= measure.MAX_ABS_BR_G)
    pix = C.field_measures(lat[raw], lon[raw], br[raw], np.full(raw.sum(), area), r)
    reps = {}
    for step in (0.06, 0.03):
        bx = L.LocalBox((float(lat[raw].min()) - 0.5, float(lat[raw].max()) + 0.5), (float(lon[raw].min()) - 0.5, float(lon[raw].max()) + 0.5),
                        step_deg=step, r_cm=r)
        Bg2, n2 = bx.deposit(lat[raw], lon[raw], br[raw] * area)
        reps[step] = (n2, L.remap_report(pix, bx.measures(Bg2)))
    r6, r3 = reps[0.06][1], reps[0.03][1]
    res.append(("point 3 raw field (no bitmap, no threshold): D and net flux kept by the deposit (1e-12 of D_scale and of the unsigned flux)",
                reps[0.06][0] == 0 and abs(r6["d_D_g"]) <= 1e-12 * 3 * 0.5 * (pix["phi_pos"] + pix["phi_neg"]) / (4 * np.pi * r * r)
                and abs(r6["d_phi_net"]) <= 1e-12 * (pix["phi_pos"] + pix["phi_neg"]), f"dD {r6['d_D_g']:.1e}"))
    res.append(("point 3 raw field: the deposit lowers the unsigned flux (noise cancels in coarse cells) and moves centroids; "
                "both are reported and shrink when the grid is refined 0.06 -> 0.03 deg",
                r6["d_phi_pos"] < 0 and abs(r3["d_phi_pos"]) < abs(r6["d_phi_pos"]) and abs(r3["d_lon_pos"]) <= abs(r6["d_lon_pos"]) + 1e-9,
                f"d phi_pos/phi_pos {r6['d_phi_pos'] / pix['phi_pos']:.3f} -> {r3['d_phi_pos'] / pix['phi_pos']:.3f}; "
                f"d lon_pos {r6['d_lon_pos']:.4f} -> {r3['d_lon_pos']:.4f} deg"))
    return res


def main():
    ok_core = C.selftest()
    ok_local = L.selftest()
    res = p1_consistency()
    for name, good, *info in res:
        print(f"[{'OK' if good else 'FALLITO'}] {name} {info[0] if info else ''}")
    good = ok_core and ok_local and all(r[1] for r in res)
    print(f"sft prep selftest: {'all passed' if good else 'FAILED'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
