"""Scarica i metadati (solo keyword, nessun FITS) di tutte le HARP SHARP CEA.

Interroga hmi.sharp_cea_720s a cadenza oraria, un mese per volta, e salva un CSV
per mese. I mesi gia' presenti vengono saltati, quindi lo script si puo'
rilanciare dopo un'interruzione. Non richiede email JSOC.

Uso, dalla radice del repository:
    python python/sharpbl/fetch_metadata.py [--start 2010-05] [--end 2026-11]
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import drms

SERIES = "hmi.sharp_cea_720s"
KEYS = [
    "HARPNUM", "T_REC", "NOAA_AR", "NOAA_NUM", "NOAA_ARS", "QUALITY",
    "LAT_FWT", "LON_FWT", "LAT_FWTPOS", "LON_FWTPOS", "LAT_FWTNEG", "LON_FWTNEG",
    "LATDTMIN", "LATDTMAX", "LONDTMIN", "LONDTMAX",
    "CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CRLN_OBS", "CRLT_OBS",
    "USFLUX", "AREA_ACR", "NPIX",
]
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "sharp" / "metadata"


def months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) < (end.year, end.month):
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield date(y, m, 1), date(ny, nm, 1)
        y, m = ny, nm


def parse_month(s: str) -> date:
    y, m = s.split("-")
    return date(int(y), int(m), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="2010-05")
    ap.add_argument("--end", default="2026-11", help="mese escluso")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--cadence", default="1h")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    client = drms.Client()
    for a, b in months(parse_month(args.start), parse_month(args.end)):
        path = args.out / f"sharp_meta_{a:%Y_%m}.csv"
        if path.exists():
            continue
        q = (f"{SERIES}[][{a:%Y.%m.%d}_00:00:00_TAI-"
             f"{b:%Y.%m.%d}_00:00:00_TAI@{args.cadence}]")
        for attempt in range(5):
            try:
                df = client.query(q, key=",".join(KEYS))
                break
            except Exception as exc:  # errori di rete o del server JSOC
                print(f"{a:%Y-%m} tentativo {attempt + 1}: {exc}", flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            print(f"{a:%Y-%m} FALLITO", flush=True)
            continue
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        tmp.rename(path)
        nh = df["HARPNUM"].nunique() if len(df) else 0
        print(f"{a:%Y-%m} righe {len(df)} HARP {nh}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
