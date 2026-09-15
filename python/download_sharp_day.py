#!/usr/bin/env python3
"""
Download SHARP CEA 720s data for one day from JSOC.

Examples
--------
Full day, Br + bitmap:
    python download_sharp_day.py 2024-05-08 --email you@example.com --out data/20240508

Download Br and bitmap:
    python download_sharp_day.py 2024-05-08 --email you@example.com --segments Br,bitmap --out data/20240508

One time only, useful for tests:
    python download_sharp_day.py 2024-05-08 --email you@example.com --times 03:12 --out data/test

Notes
-----
Requires:
    pip install drms pandas

A full day for all HARPNUM at 720 s cadence can be large. Use --times for a first test.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import drms


def parse_date(date_text: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            pass
    raise SystemExit(f"Could not parse date: {date_text}. Use YYYY-MM-DD or YYYYMMDD.")


def jsoc_time(dt: datetime) -> str:
    return dt.strftime("%Y.%m.%d_%H:%M:%S_TAI")


def build_recordset(day: datetime, segments: Iterable[str], times: list[str] | None) -> list[str]:
    seg = "{" + ",".join(segments) + "}"

    if times:
        recordsets = []
        for hhmm in times:
            hh, mm = [int(x) for x in hhmm.split(":")]
            t = day.replace(hour=hh, minute=mm, second=0)
            recordsets.append(f"hmi.sharp_cea_720s[][{jsoc_time(t)}]{seg}")
        return recordsets

    start = day.replace(hour=0, minute=0, second=0)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return [f"hmi.sharp_cea_720s[][{jsoc_time(start)}-{jsoc_time(end)}]{seg}"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("date", help="Day to download, YYYY-MM-DD or YYYYMMDD")
    ap.add_argument("--email", required=True, help="JSOC registered email address")
    ap.add_argument("--out", default=None, help="Output directory")
    ap.add_argument("--segments", default="Br,bitmap", help="Comma-separated segments, e.g. Br or Br,bitmap")
    ap.add_argument("--times", default=None, help="Comma-separated HH:MM times; omit for full day")
    ap.add_argument("--protocol", default="fits", help="JSOC export protocol, default fits")
    ap.add_argument("--method", default="url", help="JSOC export method, default url")
    args = ap.parse_args()

    day = parse_date(args.date)
    out = Path(args.out or day.strftime("%Y%m%d"))
    out.mkdir(parents=True, exist_ok=True)

    segments = [s.strip() for s in args.segments.split(",") if s.strip()]
    times = [s.strip() for s in args.times.split(",")] if args.times else None

    client = drms.Client(email=args.email)
    recordsets = build_recordset(day, segments, times)

    for recordset in recordsets:
        print(f"Submitting export: {recordset}")
        req = client.export(recordset, protocol=args.protocol, method=args.method)
        print("Waiting for JSOC export...")
        req.wait()
        print(f"Downloading {len(req.urls)} files to {out}")
        req.download(str(out))

    print(f"Done. Files written under: {out}")


if __name__ == "__main__":
    main()
