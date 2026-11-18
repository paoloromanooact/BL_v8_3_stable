"""Acquisition of the DPD spot rows sDPD<year>.txt, 1974-2012, for the white-light tilts of the T3-on-MWO stability
checks (docs/PROTOCOL_T3_MWO.md §5, §9 step 3: after the freeze, with SHA-256). Same server as the group rows already
in data/sharp/external_DPD_20261118 (RETRIEVED_UTC.txt there).

Writes data/sharp/external_sDPD_<YYYYMMDD>/: sDPD<year>.txt, SHA256SUMS.txt, RETRIEVED_UTC.txt, FETCH_LOG.json.
Refuses to overwrite. Every request is logged; a file that is not a DPD spot file (no 's ' rows and no 'd ' rows) is
an error (at least 95 % of the non-empty lines must be 's ' rows, as in the real files). Three attempts per file, then stop.

    .venv/bin/python scripts/t3_mwo_fetch_sdpd.py --selftest
    .venv/bin/python scripts/t3_mwo_fetch_sdpd.py --run
"""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://fenyi.solarobs.epss.hun-ren.hu/ftp/pub/DPD/data/sDPD{year}.txt"
YEARS = range(1974, 2013)
TRIES = 3


def http_get(url, timeout=120):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read()


def looks_like_spots(body):
    text = body.decode("ascii", "replace")
    lines = [l for l in text.splitlines() if l.strip()]
    n_s = sum(l.startswith("s ") for l in lines)
    return n_s > 0 and n_s >= 0.95 * len(lines)


def fetch(out_dir, years=YEARS, get=http_get, pause=1.0):
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise SystemExit(f"refusing to overwrite {out_dir}")
    tmp = out_dir.with_name(out_dir.name + ".partial")
    tmp.mkdir(parents=True, exist_ok=False)
    log, sums = [], []
    for y in years:
        url = BASE.format(year=y)
        for attempt in range(1, TRIES + 1):
            try:
                status, body = get(url)
                ok = status == 200 and looks_like_spots(body)
                log.append(dict(url=url, attempt=attempt, status=status, bytes=len(body), valid=ok))
                if ok:
                    (tmp / f"sDPD{y}.txt").write_bytes(body)
                    sums.append(f"{hashlib.sha256(body).hexdigest()}  sDPD{y}.txt")
                    break
            except Exception as e:                       # noqa: BLE001
                log.append(dict(url=url, attempt=attempt, error=f"{type(e).__name__}: {e}"))
            time.sleep(pause)
        else:
            (tmp / "FETCH_LOG.json").write_text(json.dumps(log, indent=2) + "\n")
            raise SystemExit(f"failed after {TRIES} attempts: {url} (partial directory kept: {tmp})")
    (tmp / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    (tmp / "RETRIEVED_UTC.txt").write_text(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\n"
                                           + f"source {BASE.replace('{year}', '<year>')} via HTTP, "
                                           f"{min(years)}-{max(years)}\n")
    (tmp / "FETCH_LOG.json").write_text(json.dumps(log, indent=2) + "\n")
    tmp.rename(out_dir)
    return out_dir


def selftest():
    import tempfile
    res = []

    def ok(n, c):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    good = (b"s 1974 01 02 03 20 30    312     1    45   227    23   116 -14.86  43.24  -5.51 155.45 0.2242\n"
            b"s 1974 01 03 00 56 30    312     1    37   289    19   147 -15.86  43.18   6.29 205.75 0.2435\n")
    calls = []

    def fake(url):
        calls.append(url)
        if url.endswith("1991.txt") and calls.count(url) == 1:
            raise OSError("timeout")
        if url.endswith("1992.txt"):
            return 200, b"<html>not found</html>"
        return 200, good
    with tempfile.TemporaryDirectory() as td:
        d = fetch(Path(td) / "x", years=[1990, 1991], get=fake, pause=0)
        sums = (d / "SHA256SUMS.txt").read_text().split()
        ok("two years fetched, one after a retry, SHA-256 recorded",
           sums[0] == hashlib.sha256(good).hexdigest() and len(json.loads((d / "FETCH_LOG.json").read_text())) == 3)
        try:
            fetch(Path(td) / "x", years=[1990], get=fake, pause=0)
            ok("refuses to overwrite", False)
        except SystemExit:
            ok("refuses to overwrite", True)
        try:
            fetch(Path(td) / "y", years=[1992], get=fake, pause=0)
            ok("a page that is not a DPD spot file is refused after three attempts", False)
        except SystemExit:
            ok("a page that is not a DPD spot file is refused after three attempts",
               not (Path(td) / "y").exists() and (Path(td) / "y.partial/FETCH_LOG.json").exists())
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.run:
        print(fetch(ROOT / f"data/sharp/external_sDPD_{datetime.now(timezone.utc):%Y%m%d}"))
        sys.exit(0)
    ap.print_help()
    sys.exit(1)
