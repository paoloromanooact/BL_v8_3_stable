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


def spot_row_ok(line, year):
    """One 's' row of the DPD format (DPDformat.txt): fixed columns, numeric fields parse, the date is valid and in the
    requested year, positions in range (999999 marks an intermittent phase and is accepted)."""
    if not line.startswith("s ") or len(line.rstrip()) < 93:
        return False
    try:
        y, mo, d, hh, mi, ss = (int(line[a:b]) for a, b in ((2, 6), (7, 9), (10, 12), (13, 15), (16, 18), (19, 21)))
        datetime(y, mo, d, hh, mi, ss)
        int(line[29:34]), int(line[35:40]), int(line[41:46]), int(line[47:52]), int(line[53:58])
        lat, lon, lcm = float(line[59:65]), float(line[66:72]), float(line[73:79])
        float(line[80:86]), float(line[87:93])
    except ValueError:
        return False
    if y != year or not line[22:29].strip():
        return False
    if lat > 900 or lon > 900 or lcm > 900:
        return True
    return abs(lat) <= 90 and 0 <= lon <= 360 and abs(lcm) <= 90


def looks_like_spots(body, year):
    """Every non-empty line must be a valid 's' row of the requested year (\r and trailing blanks tolerated)."""
    text = body.decode("ascii", "replace")
    lines = [l.rstrip("\r") for l in text.splitlines() if l.strip()]
    return len(lines) > 0 and all(spot_row_ok(l, year) for l in lines)


def fetch(out_dir, years=YEARS, get=http_get, pause=1.0):
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise SystemExit(f"refusing to overwrite {out_dir}")
    tmp = out_dir.with_name(out_dir.name + ".partial")
    tmp.mkdir(parents=True, exist_ok=False)
    log, sums = [], []

    def save_log():                                   # written after every request, so it survives an interruption
        (tmp / "FETCH_LOG.json").write_text(json.dumps(log, indent=2) + "\n")
    for y in years:
        url = BASE.format(year=y)
        for attempt in range(1, TRIES + 1):
            try:
                status, body = get(url)
                ok = status == 200 and looks_like_spots(body, y)
                log.append(dict(url=url, attempt=attempt, utc=datetime.now(timezone.utc).isoformat(), status=status,
                                bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), valid=ok))
                save_log()
                if ok:
                    (tmp / f"sDPD{y}.txt").write_bytes(body)
                    sums.append(f"{hashlib.sha256(body).hexdigest()}  sDPD{y}.txt")
                    break
            except Exception as e:                       # noqa: BLE001
                log.append(dict(url=url, attempt=attempt, utc=datetime.now(timezone.utc).isoformat(),
                                error=f"{type(e).__name__}: {e}"))
                save_log()
            time.sleep(pause)
        else:
            raise SystemExit(f"failed after {TRIES} attempts: {url} (partial directory kept: {tmp})")
    (tmp / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    (tmp / "RETRIEVED_UTC.txt").write_text(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + "\n"
                                           + f"source {BASE.replace('{year}', '<year>')} via HTTP, "
                                           f"{min(years)}-{max(years)}\n")
    save_log()
    tmp.rename(out_dir)
    return out_dir


def selftest():
    import tempfile
    res = []

    def ok(n, c):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    real = ("s 1974 01 02 03 20 30    312     1    45   227    23   116 -14.86  43.24  -5.51 155.45 0.2242\r\n"
            "s 1974 01 04 09 52 30    312     2     1    -1     1    -1 -15.87  43.35  24.53 241.07 0.4582\n")
    body = lambda y: real.replace("s 1974", f"s {y}").encode()           # noqa: E731
    ok("real DPD spot rows accepted (with CRLF and negative shared areas)", looks_like_spots(body(1974), 1974))
    ok("rows of another year refused", not looks_like_spots(body(1974), 1990))
    ok("'s garbage' refused", not looks_like_spots(b"s garbage\n", 1974))
    bad_num = real.splitlines()[0].replace(" -14.86", " -1x.86")
    ok("non-numeric essential field refused", not looks_like_spots(bad_num.encode(), 1974))
    ok("invalid date refused", not looks_like_spots(real.splitlines()[0].replace("1974 01 02", "1974 02 30").encode(), 1974))
    ok("intermittent-phase marker 999999 accepted",
       looks_like_spots((real.splitlines()[0][:58] + " 999999 999999 999999 999999 999999").encode(), 1974))
    calls = []

    def fake(url):
        calls.append(url)
        y = int(url[-8:-4])
        if y == 1991 and calls.count(url) == 1:
            raise OSError("timeout")
        if y == 1992:
            return 200, b"<html>not found</html>"
        if y == 1993:
            return 200, body(1974)                     # right format, wrong year
        return 200, body(y)
    with tempfile.TemporaryDirectory() as td:
        d = fetch(Path(td) / "x", years=[1990, 1991], get=fake, pause=0)
        sums = (d / "SHA256SUMS.txt").read_text().split()
        ok("two years fetched with their own content, one after a retry; SHA-256 and log recorded",
           sums[0] == hashlib.sha256(body(1990)).hexdigest() and sums[2] == hashlib.sha256(body(1991)).hexdigest()
           and (d / "sDPD1991.txt").read_bytes() == body(1991) and len(json.loads((d / "FETCH_LOG.json").read_text())) == 3)
        try:
            fetch(Path(td) / "x", years=[1990], get=fake, pause=0)
            ok("refuses to overwrite", False)
        except SystemExit:
            ok("refuses to overwrite", True)
        for y, name in ((1992, "a page that is not a DPD spot file"), (1993, "a spot file of another year")):
            try:
                fetch(Path(td) / f"y{y}", years=[1990, y], get=fake, pause=0)
                ok(f"{name} is refused after three attempts", False)
            except SystemExit:
                log = json.loads((Path(td) / f"y{y}.partial/FETCH_LOG.json").read_text())
                ok(f"{name} is refused after three attempts; the progressive log keeps every request",
                   not (Path(td) / f"y{y}").exists() and len(log) == 4 and not any(e.get("valid") for e in log[1:]))
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
