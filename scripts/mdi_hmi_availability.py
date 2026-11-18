"""Segment availability for a frozen MDI-HMI sample: one rs_list per series and segment on the exact selected records
(generalised from Codex's local availability.py of the first sample; same checks). Metadata only, no FITS.

    .venv/bin/python scripts/mdi_hmi_availability.py --selftest
    .venv/bin/python scripts/mdi_hmi_availability.py --pairs DIR/selection/PAIRS.csv --pairs-sha SHA --n N --out DIR/availability
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlencode

ENDPOINT = "http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?"
SIDES = (("smarp", "TARPNUM", ("bitmap", "magnetogram")), ("hmi", "HARPNUM", ("bitmap", "magnetogram", "Br", "Bt", "Bp")))


def parse(doc, key, segment, keys, series):
    """Check identity and build SEGMENTS rows from one rs_list answer; keys maps (id, T_REC) -> slot."""
    if doc.get("status") != 0 or doc.get("count") != len(keys):
        raise ValueError(f"status/count {doc.get('status')} {doc.get('count')}")
    cols = {x["name"]: x["values"] for x in doc["keywords"]}
    items = list(zip(cols[key], cols["T_REC"]))
    if Counter(items) != Counter(list(keys)):
        raise ValueError("record identity mismatch")
    [seg] = doc["segments"]
    if seg["name"] != segment or not all(len(x) == len(keys) for x in (*cols.values(), seg["values"], seg["dims"])):
        raise ValueError("segment list or lengths")
    rows = []
    for j, k in enumerate(items):
        p, sz, online = seg["values"][j], cols["*size*"][j], cols["*online*"][j]
        good = (online == "Y" and str(sz).isdigit() and int(sz) > 0 and p.startswith("/SUM")
                and re.fullmatch(r"[1-9]\d*x[1-9]\d*", seg["dims"][j]))
        rows.append(dict(slot=keys[k], series=series, record="|".join(k), segment=segment, path=p, dims=seg["dims"][j],
                         online=online, reported_bytes=sz, status="online_metadata" if good else "unconfirmed"))
    return rows


def run(pairs_file, pairs_sha, n, out):
    pairs_file, out = Path(pairs_file), Path(out)
    if hashlib.sha256(pairs_file.read_bytes()).hexdigest() != pairs_sha:
        sys.exit("pairs manifest SHA-256 differs")
    rows = list(csv.DictReader(pairs_file.open()))
    if len(rows) != n:
        sys.exit(f"{len(rows)} pairs, expected {n}")
    out.mkdir(parents=False, exist_ok=False)
    ledger = dict(pairs_sha256=pairs_sha, requests=[])

    def save():
        (out / "REQUESTS.tmp").write_text(json.dumps(ledger, indent=2) + "\n")
        (out / "REQUESTS.tmp").replace(out / "REQUESTS.json")
    segments = []
    for side, key, names in SIDES:
        series = rows[0][side + "_series"]
        keys = {tuple(r[side + "_record"].split("|")): r["slot"] for r in rows}
        ds = ",".join(f"{series}[{i}][{t}]" for i, t in keys)
        for segment in names:
            url = ENDPOINT + urlencode(dict(op="rs_list", ds=ds, key=key + ",T_REC,*online*,*size*", seg=segment))
            rec = dict(side=side, segment=segment, url=url, status="started")
            ledger["requests"].append(rec)
            save()
            tag = f"{side}_{segment}"
            t0 = time.monotonic()
            proc = subprocess.run(["curl", "--disable", "--proto", "=http", "--noproxy", "*", "--retry", "0",
                                   "--max-time", "25", "--connect-timeout", "7", "--max-filesize", "262144",
                                   "--silent", "--show-error", "--header", "Accept-Encoding: identity",
                                   "--dump-header", str(out / (tag + ".headers")), "--output", str(out / (tag + ".json")),
                                   url], capture_output=True)
            data = (out / (tag + ".json")).read_bytes() if (out / (tag + ".json")).exists() else b""
            rec.update(seconds=time.monotonic() - t0, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                       exit=proc.returncode, error=proc.stderr.decode().strip(), status="received")
            save()
            if proc.returncode or not re.search(r"^HTTP/\S+ 200\b", (out / (tag + ".headers")).read_text(), re.M):
                sys.exit(f"request failed: {tag}")
            segments += parse(json.loads(data), key, segment, keys, series)
            rec["status"] = "identity_verified"
            save()
    with (out / "SEGMENTS.csv").open("x", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(segments[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(segments)
    ledger.update(segments=len(segments), online=sum(r["status"] == "online_metadata" for r in segments),
                  archive_bytes_reported=sum(int(r["reported_bytes"]) for r in segments if str(r["reported_bytes"]).isdigit()))
    save()
    print(json.dumps({k: v for k, v in ledger.items() if k != "requests"}, indent=1))
    return 0


def selftest():
    keys = {("1", "T1"): "1", ("2", "T2"): "2"}
    doc = dict(status=0, count=2, keywords=[dict(name="HARPNUM", values=["2", "1"]), dict(name="T_REC", values=["T2", "T1"]),
                                            dict(name="*online*", values=["Y", "N"]), dict(name="*size*", values=["5760", "5760"])],
               segments=[dict(name="Br", values=["/SUM1/D2/S00000/Br.fits", "/SUM1/D1/S00000/Br.fits"], dims=["3x2", "3x2"])])
    rows = parse(doc, "HARPNUM", "Br", keys, "hmi.sharp_cea_720s")
    ok1 = [r["status"] for r in rows] == ["online_metadata", "unconfirmed"] and rows[0]["slot"] == "2"
    bad = dict(doc, keywords=[dict(name="HARPNUM", values=["2", "3"])] + doc["keywords"][1:])
    try:
        parse(bad, "HARPNUM", "Br", keys, "hmi.sharp_cea_720s")
        ok2 = False
    except ValueError:
        ok2 = True
    print(f"[{'OK' if ok1 else 'FALLITO'}] parse: slot mapping and offline segment marked unconfirmed")
    print(f"[{'OK' if ok2 else 'FALLITO'}] parse: record identity mismatch refused")
    return ok1 and ok2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pairs")
    ap.add_argument("--pairs-sha")
    ap.add_argument("--n", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.pairs and a.pairs_sha and a.n and a.out:
        return run(a.pairs, a.pairs_sha, a.n, a.out)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
