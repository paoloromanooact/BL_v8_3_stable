"""Scarica Br e bitmap dei record selezionati da P1/P1b, direttamente dall'archivio JSOC.

Uso: .venv/bin/python python/sharpbl/download_records.py [--batch 50] [--workers 3] [--limit N]

Metodo "as-is": per ogni blocco di record si interroga DRMS (tutte le keyword e
i percorsi dei segmenti), poi si scaricano i file dal percorso di archivio
(http://jsoc.stanford.edu/SUM...). Non crea job di export, non serve email.
I FITS restano byte per byte come in archivio; le keyword (assenti nei file
as-is, comprese quelle WCS) vanno in <nome>.keys.json, che geometry.read_sharp
unisce all'header.

Per ogni record, in data/sharp/fits/<anno>/:
  hmi.sharp_cea_720s.<HARP>.<YYYYMMDD_HHMMSS>_TAI.Br.fits
  hmi.sharp_cea_720s.<HARP>.<YYYYMMDD_HHMMSS>_TAI.bitmap.fits
  hmi.sharp_cea_720s.<HARP>.<YYYYMMDD_HHMMSS>_TAI.keys.json   (scritto per ultimo)
Un record e' completo solo se esiste keys.json; i download in corso hanno
suffisso .part. Lo script si puo' rilanciare: salta i record completi.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import drms
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SERIES = "hmi.sharp_cea_720s"
SEGMENTS = ("Br", "bitmap")
JSOC = "http://jsoc.stanford.edu"
# keyword salvate in keys.json ("**ALL**" non e' accettato da DRMS con piu' record insieme)
KEYS = [
    "HARPNUM", "T_REC", "T_OBS", "DATE__OBS", "QUALITY", "NOAA_AR", "NOAA_NUM", "NOAA_ARS",
    "CTYPE1", "CTYPE2", "CUNIT1", "CUNIT2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2",
    "CDELT1", "CDELT2", "CROTA2", "IMCRPIX1", "IMCRPIX2", "RSUN_REF", "RSUN_OBS", "DSUN_OBS",
    "CRLN_OBS", "CRLT_OBS", "CAR_ROT", "LAT_FWT", "LON_FWT", "LAT_FWTPOS", "LON_FWTPOS",
    "LAT_FWTNEG", "LON_FWTNEG", "LATDTMIN", "LATDTMAX", "LONDTMIN", "LONDTMAX",
    "USFLUX", "AREA_ACR", "NPIX", "SIZE", "SIZE_ACR", "MASK", "BUNIT",
]


def file_stem(harp: int, t_rec: str) -> str:
    d, t = t_rec.replace("_TAI", "").split("_")
    return f"{SERIES}.{harp}.{d.replace('.', '')}_{t.replace(':', '')}_TAI"


def record_dir(base: Path, t_rec: str) -> Path:
    return base / t_rec[:4]


def complete(base: Path, harp: int, t_rec: str) -> bool:
    return (record_dir(base, t_rec) / f"{file_stem(harp, t_rec)}.keys.json").exists()


def fetch(url: str, dst: Path, retries: int = 4) -> int:
    part = dst.with_name(dst.name + ".part")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(part, "wb") as f:
                f.write(r.read())
            part.rename(dst)
            return dst.stat().st_size
        except Exception:  # errori di rete: ritenta
            if attempt == retries - 1:
                raise
            time.sleep(10 * (attempt + 1))
    return 0


def clean(v):
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def do_batch(client, rows, base: Path, pool) -> tuple[int, int]:
    spec = ",".join(f"{SERIES}[{h}][{t}]" for h, t in rows)
    keys, segs = client.query(spec, key=",".join(KEYS), seg=",".join(SEGMENTS))
    jobs = []
    for i in range(len(keys)):
        harp, t_rec = int(keys["HARPNUM"].iloc[i]), str(keys["T_REC"].iloc[i])
        folder = record_dir(base, t_rec)
        folder.mkdir(parents=True, exist_ok=True)
        stem = file_stem(harp, t_rec)
        files = [(JSOC + segs[s].iloc[i], folder / f"{stem}.{s}.fits") for s in SEGMENTS]
        meta = {k: clean(keys[k].iloc[i]) for k in keys.columns}
        jobs.append((files, folder / f"{stem}.keys.json", meta))
    futures = [(j, [pool.submit(fetch, u, d) for u, d in j[0]]) for j in jobs]
    nbytes = done = 0
    for (files, kpath, meta), fs in futures:
        nbytes += sum(f.result() for f in fs)
        kpath.write_text(json.dumps(meta, indent=0))
        done += 1
    return done, nbytes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=50)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="solo i primi N record mancanti (prova)")
    args = ap.parse_args()

    sel = pd.read_csv(ROOT / "results/P1/P1_RECORD_SELECTION.csv")
    base = ROOT / "data/sharp/fits"
    todo = [(int(h), t) for h, t in zip(sel["HARPNUM"], sel["T_REC"]) if not complete(base, int(h), t)]
    if args.limit:
        todo = todo[: args.limit]
    batches = [todo[i:i + args.batch] for i in range(0, len(todo), args.batch)]
    print(f"{time.strftime('%F %T')} record selezionati {len(sel)}, gia' completi "
          f"{len(sel) - len(todo) if not args.limit else '-'}, da scaricare {len(todo)} "
          f"in {len(batches)} blocchi", flush=True)

    client = drms.Client()
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, rows in enumerate(batches, 1):
            for attempt in range(5):
                try:
                    n, b = do_batch(client, rows, base, pool)
                    total_bytes += b
                    print(f"{time.strftime('%F %T')} blocco {i}/{len(batches)} ({rows[0][1][:10]}) "
                          f"record {n}/{len(rows)}, totale {total_bytes / 1e9:.2f} GB", flush=True)
                    break
                except Exception as exc:  # rete o DRMS: ritenta il blocco intero
                    print(f"{time.strftime('%F %T')} blocco {i} tentativo {attempt + 1} errore: {exc!r}",
                          flush=True)
                    time.sleep(60 * (attempt + 1))
            else:
                print(f"{time.strftime('%F %T')} blocco {i} FALLITO ({rows[0]} ... {rows[-1]})", flush=True)

    missing = sum(not complete(base, int(h), t) for h, t in zip(sel["HARPNUM"], sel["T_REC"]))
    print(f"{time.strftime('%F %T')} FINE: record completi {len(sel) - missing}/{len(sel)}, "
          f"mancanti {missing}", flush=True)
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
