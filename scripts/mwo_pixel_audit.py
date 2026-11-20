"""Descriptive pixel audit of every Fe I MWO magnetogram 1974-2013 (no tilt, no catalogue response): field-scale and
saturation statistics on the central disc, to find magnetograms like the 18 of amendment A2 (field x100, saturated)
or 2000/m000806_1660_0fe1.fits (GV 3, median |B| x13, saturated at 32767*BSCALE).

Per magnetogram, with the frozen reader (float32 before BSCALE) and BLANK pixels removed, on mu >= 0.8:
median |B|, 99th percentile, maximum, number and fraction of pixels at the saturation value 32767*BSCALE (within half a
storage step), GV, BSCALE. Output: results/MWO_PIXEL_AUDIT/{PIXELS.csv.gz, META.json}. No decision depends on it: any
exclusion rule must be pre-registered in an amendment before use.

    .venv/bin/python scripts/mwo_pixel_audit.py --run
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py")
C = importlib.util.module_from_spec(_s)
sys.modules["t3_mwo_catalogue"] = C
_s.loader.exec_module(C)
OUT = ROOT / "results/MWO_PIXEL_AUDIT"


def stats(h, B, geo_cache):
    key = (float(h["X0"]), float(h["Y0"]), float(h["R0"]), float(h["B0"]), B.shape)
    if key not in geo_cache:
        geo_cache.clear()
        geo_cache[key] = C.geometry(h, B.shape)
    lat, lon, cmd, mu = geo_cache[key]
    bl = C.blank_mask(h, B)
    sel = np.isfinite(mu) & (mu >= 0.8) & ~bl
    a = np.abs(B[sel]).astype(float)
    bs = float(h.get("BSCALE", 1.0))
    sat = 32767 * bs
    nsat = int((a >= sat - 0.5 * bs).sum())
    return dict(n_pix=int(a.size), median_abs=float(np.median(a)) if a.size else np.nan,
                p99_abs=float(np.percentile(a, 99)) if a.size else np.nan, max_abs=float(a.max()) if a.size else np.nan,
                n_saturated=nsat, frac_saturated=nsat / a.size if a.size else np.nan, bscale=bs, gv=h.get("GV"))


def run():
    if OUT.exists():
        sys.exit("refusing to overwrite")
    rows, cache = [], {}
    for y in range(1974, 2014):
        p = C.MWO_DATA / f"MWO_{y}.tar.gz"
        try:
            tf = tarfile.open(p)
        except (tarfile.TarError, OSError, EOFError):
            continue
        with tf:
            for m in tf:
                if not m.isfile() or C.MP._detect_line(m.name, ("FE",)) != "FE":
                    continue
                try:
                    h, B = C.MP.parse_fits_bytes(tf.extractfile(m).read())
                    rows.append(dict(archive_year=y, member=m.name, **stats(h, B, cache)))
                except Exception as e:                       # noqa: BLE001
                    rows.append(dict(archive_year=y, member=m.name, error=type(e).__name__))
        print(y, len(rows), flush=True)
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True)
    d.to_csv(OUT / "PIXELS.csv.gz", index=False)
    meta = dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), n=len(d),
                git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                products_sha256={"PIXELS.csv.gz": hashlib.sha256((OUT / "PIXELS.csv.gz").read_bytes()).hexdigest()})
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    sys.exit(run() if ap.parse_args().run else 1)
