"""Header-only inventory of the MWO magnetogram archives (no pixel read, no tilt), for the instrumental epochs of the
T3-on-MWO draft (docs/PROTOCOL_T3_MWO_DRAFT.md §4).

Reads every FITS header in MWO_<year>.tar.gz (1967-2013) and records the keywords that describe the instrument and
the scale: filename family, LAMBDA, MRKMOD (hardware: 0=datex, 256=ael, 1280-1283=fm, 1284=24ch), PSEPMA, ICHK,
DXB_OBS/DYB_OBS, DXB_IMG, R0, BSCALE, BZERO, BITPIX, TELESCOP, plus DATE-OBS, TAVG-UT, CARROT. Writes
results/MWO_HEADER_INVENTORY/{HEADERS.csv.gz, BY_YEAR.csv, META.json}.

    .venv/bin/python scripts/mwo_header_inventory.py --selftest
    .venv/bin/python scripts/mwo_header_inventory.py --run
"""
import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MWO_DATA = Path("/storage/shared/gianluca/MWO_project/Desktop/MWO/data MWO")
OUT = ROOT / "results/MWO_HEADER_INVENTORY"
KEYS = ("DATE-OBS", "TAVG-UT", "CARROT", "LAMBDA", "MRKMOD", "PSEPMA", "ICHK", "DXB_OBS", "DYB_OBS", "DXB_IMG",
        "DYB_IMG", "R0", "X0", "Y0", "BSCALE", "BZERO", "BITPIX", "NAXIS1", "NAXIS2", "TELESCOP", "BUNIT", "GV")


def header(fobj):
    cards = []
    while True:
        block = fobj.read(2880)
        if len(block) < 2880:
            return None
        cards += [block[i:i + 80].decode("ascii", "replace") for i in range(0, 2880, 80)]
        if any(c.startswith("END") and c[3:].strip() == "" for c in cards[-36:]):
            break
    h = {}
    for c in cards:
        if c.startswith("END") and c[3:].strip() == "":
            break
        if c[8:10] == "= ":
            k = c[:8].strip()
            raw = c[10:80]
            raw = raw.split("'")[1] if raw.strip().startswith("'") else raw.split("/")[0]
            h[k] = raw.strip()
    return h


def family(name):
    base = name.rsplit("/", 1)[-1].lower()
    if base.startswith("mp00_5250"):
        return "legacy_MP00_5250"
    if "fe1" in base:
        return "modern_fe1"
    if "na1" in base:
        return "modern_na1"
    return "other"


def scan(year, path):
    rows = []
    with tarfile.open(path) as tf:
        for m in tf:
            if not (m.isfile() and m.name.lower().endswith((".fits", ".fit", ".fts"))):
                continue
            h = header(tf.extractfile(m))
            r = dict(archive_year=year, member=m.name, family=family(m.name), read_ok=h is not None)
            if h:
                r.update({k: h.get(k, "") for k in KEYS})
            rows.append(r)
    return rows


def by_year(d):
    num = lambda c: pd.to_numeric(d[c], errors="coerce")  # noqa: E731
    d = d.assign(**{c: num(c) for c in ("MRKMOD", "PSEPMA", "DXB_OBS", "DYB_OBS", "BSCALE", "R0", "LAMBDA")})
    g = d.groupby(["archive_year", "family"])
    out = g.size().rename("n").to_frame()
    out["mrkmod_values"] = g.MRKMOD.apply(lambda s: ";".join(f"{int(k)}:{v}" for k, v in s.value_counts().sort_index().items()))
    out["bscale_values"] = g.BSCALE.apply(lambda s: ";".join(f"{k:g}:{v}" for k, v in s.value_counts().sort_index().items()))
    out["lambda_values"] = g.LAMBDA.apply(lambda s: ";".join(f"{k:g}:{v}" for k, v in s.value_counts().sort_index().items()))
    for c in ("DXB_OBS", "DYB_OBS", "PSEPMA", "R0"):
        out[f"{c}_median"] = g[c].median()
        out[f"{c}_min"] = g[c].min()
        out[f"{c}_max"] = g[c].max()
    return out.reset_index()


def selftest():
    from astropy.io import fits
    buf = io.BytesIO()
    hdu = fits.PrimaryHDU()
    for k, v in dict(MRKMOD=1284, PSEPMA=67.4, DXB_OBS=13.0, BSCALE=0.05, TELESCOP="150 ft", LAMBDA=5250.2).items():
        hdu.header[k] = v
    hdu.writeto(buf)
    h = header(io.BytesIO(buf.getvalue()))
    c1 = h["MRKMOD"] == "1284" and float(h["PSEPMA"]) == 67.4 and h["TELESCOP"] == "150 ft"
    c2 = (family("1974/MP00_5250MWO_00_0740102_1746.fits"), family("2005/m050307_2082_0fe1.fits"),
          family("x/m050307_2082_0na1.fits")) == ("legacy_MP00_5250", "modern_fe1", "modern_na1")
    c3 = header(io.BytesIO(b"x" * 100)) is None
    for n, c in (("header keywords parsed", c1), ("filename families", c2), ("truncated header refused", c3)):
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    return c1 and c2 and c3


def run():
    if OUT.exists():
        sys.exit("refusing to overwrite")
    if not selftest():
        return 1
    rows = []
    for y in range(1967, 2014):
        p = MWO_DATA / f"MWO_{y}.tar.gz"
        try:
            r = scan(y, p)
        except (tarfile.TarError, OSError, EOFError) as e:
            r = [dict(archive_year=y, member="", family="archive_unreadable", read_ok=False, error=str(e))]
        rows += r
        print(y, len(r), flush=True)
    d = pd.DataFrame(rows)
    OUT.mkdir(parents=True)
    d.to_csv(OUT / "HEADERS.csv.gz", index=False)
    by_year(d[d.read_ok]).to_csv(OUT / "BY_YEAR.csv", index=False)
    meta = dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), n_rows=len(d),
                n_read=int(d.read_ok.sum()),
                git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                products_sha256={n: hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in ("HEADERS.csv.gz", "BY_YEAR.csv")})
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (run() if a.run else 1))
