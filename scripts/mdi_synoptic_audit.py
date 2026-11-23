"""Provenance and header audit of the MDI synoptic Br maps on disk (mdi.synoptic_Mr_polfil_96m, CR 1909-2104).

Read-only: SHA-256 of every file, header keys that define the grid, the time composition and the calibration, and
pixel statistics (finite fraction, |B| max). No tilt is measured, no file is changed, no network request.
Outputs results/MDI_SYNOPTIC_AUDIT/ (refuses to overwrite): FILES.csv, CONSISTENCY.json, HEADER_EXAMPLE.txt, META.json.

    .venv/bin/python scripts/mdi_synoptic_audit.py --selftest
    .venv/bin/python scripts/mdi_synoptic_audit.py --run
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/storage/shared/gianluca/MWO_project/sunpy/data")
OUT = ROOT / "results/MDI_SYNOPTIC_AUDIT"
PATTERN = re.compile(r"^mdi\.synoptic_mr_polfil_96m\.(\d+)\.Br_polfil\.fits$")
KEYS = ("CAR_ROT", "CARRTIME", "T_START", "T_STOP", "T_ROT", "T_OBS", "IMG_NUM", "IMG_FRST", "IMG_LAST", "IMG_ROT",
        "CADENCE", "W_WEIGHT", "W_OFFSET", "HWNWIDTH", "EQPOINTS", "NSIGMA", "CARSTRCH", "DIFROT_A", "DIFROT_B",
        "DIFROT_C", "METHOD", "LATFIL", "LATFIL1", "LAT0", "NMAX", "CALVER64", "DATE", "NAXIS1", "NAXIS2", "CTYPE1",
        "CTYPE2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2", "CUNIT2", "LON_FRST", "LON_LAST",
        "LON_STEP", "BUNIT", "BSCALE", "BZERO", "TOTVALS", "DATAVALS", "MISSVALS", "DATAMIN", "DATAMAX", "DATARMS",
        "B0_ROT", "DRMS_ID", "LICENSE")
GRID_KEYS = ("NAXIS1", "NAXIS2", "CTYPE1", "CTYPE2", "CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CUNIT2", "BUNIT", "LON_STEP")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audit_file(p):
    with fits.open(p) as hd:
        h = hd[-1].header
        d = hd[-1].data.astype(float)
    row = {k: h.get(k) for k in KEYS}
    m = PATTERN.match(Path(p).name)
    row.update(file=Path(p).name, cr_from_name=int(m.group(1)), sha256=sha(p), size=Path(p).stat().st_size,
               finite_fraction=float(np.isfinite(d).mean()), abs_max=float(np.nanmax(np.abs(d))) if np.isfinite(d).any() else np.nan,
               lowlat_finite_fraction=float(np.isfinite(d[:, :][np.abs(np.arange(d.shape[0]) - (d.shape[0] - 1) / 2) <= d.shape[0] / 2 * np.sin(np.radians(45))]).mean()))
    return row


def consistency(t, crs_expected):
    present = set(t.cr_from_name)
    grid = {k: sorted({str(v) for v in t[k]}) for k in GRID_KEYS}
    return dict(n_files=len(t), cr_min=int(t.cr_from_name.min()), cr_max=int(t.cr_from_name.max()),
                missing_crs=sorted(set(crs_expected) - present), name_matches_CAR_ROT=bool((t.cr_from_name == t.CAR_ROT).all()),
                carrtime_is_360_cr_minus_180=bool((t.CARRTIME == 360 * t.CAR_ROT - 180).all()),
                grid_values=grid, grid_identical=all(len(v) == 1 for v in grid.values()),
                calver64_values=sorted({str(v) for v in t.CALVER64}), w_weight_values=sorted({str(v) for v in t.W_WEIGHT}),
                hwnwidth_values=sorted({str(v) for v in t.HWNWIDTH}), method_values=sorted({str(v) for v in t.METHOD}),
                img_num_min=int(t.IMG_NUM.min()), img_num_median=float(t.IMG_NUM.median()), img_num_max=int(t.IMG_NUM.max()),
                files_with_missing_pixels=int((t.finite_fraction < 1).sum()),
                files_with_missing_lowlat_pixels=int((t.lowlat_finite_fraction < 1).sum()),
                build_dates=sorted({str(v)[:10] for v in t.DATE}))


def run(src=SRC, out=OUT, crs=range(1909, 2105), require_git=True):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    files = sorted(f for f in Path(src).iterdir() if PATTERN.match(f.name))
    t = pd.DataFrame([audit_file(f) for f in files]).sort_values("cr_from_name").reset_index(drop=True)
    cons = consistency(t, crs)
    Path(out).mkdir(parents=True)
    t.to_csv(Path(out) / "FILES.csv", index=False)
    (Path(out) / "CONSISTENCY.json").write_text(json.dumps(cons, indent=2) + "\n")
    with fits.open(files[len(files) // 2]) as hd:
        (Path(out) / "HEADER_EXAMPLE.txt").write_text(repr(hd[-1].header) + "\n")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() if require_git else ""
    meta = dict(source_dir=str(src), script_sha256=sha(__file__), git_commit=commit, tilts_measured=False, network=False,
                products_sha256={f.name: sha(f) for f in sorted(Path(out).iterdir())})
    (Path(out) / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({k: v for k, v in cons.items() if k != "grid_values"}, indent=1))
    return 0


def selftest():
    res = []

    def ok(n, c):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for cr in (1000, 1001, 1003):
            d = np.zeros((12, 36))
            if cr == 1003:
                d[0, 0] = np.nan
            h = fits.Header(dict(CAR_ROT=cr, CARRTIME=360 * cr - 180, CTYPE1="CRLN-CEA", CDELT1=-10.0, IMG_NUM=5 + cr % 7,
                                 W_WEIGHT="Even", HWNWIDTH=20.0, CALVER64=0, DATE="2018-01-01T00:00:00"))
            fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(d, header=h)]).writeto(td / f"mdi.synoptic_mr_polfil_96m.{cr}.Br_polfil.fits")
        (td / "other.fits").write_text("not a map")
        run(td, td / "out", crs=range(1000, 1004), require_git=False)
        c = json.loads((td / "out/CONSISTENCY.json").read_text())
        t = pd.read_csv(td / "out/FILES.csv")
        ok("only map files read; missing CR found", c["n_files"] == 3 and c["missing_crs"] == [1002])
        ok("name equals CAR_ROT; CARRTIME = 360 CR - 180", c["name_matches_CAR_ROT"] and c["carrtime_is_360_cr_minus_180"])
        ok("missing pixel counted", c["files_with_missing_pixels"] == 1 and t.finite_fraction.min() < 1)
        ok("SHA-256 recorded and correct", all(sha(td / f) == h for f, h in zip(t.file, t.sha256)))
        try:
            run(td, td / "out", crs=range(1000, 1004), require_git=False)
            ok("refuses to overwrite", False)
        except SystemExit:
            ok("refuses to overwrite", True)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (selftest() if a.selftest else run() == 0) else 1)
