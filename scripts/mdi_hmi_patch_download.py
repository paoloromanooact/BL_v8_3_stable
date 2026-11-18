"""Small MDI/HMI comparison. Default: offline preflight. --fetch uses the frozen records only.

Run with the v8.4 Python environment. No export, redirects, credentials or science measurements.
The fixed output directory and its lock/ledger are shared by retries. Raw DRMS metadata accompany
the as-is FITS. The adapter can open only Br/bitmap initially for the separate R0 check.
"""
import argparse
from contextlib import closing
import fcntl
import http.client
import json
from multiprocessing import get_context
import signal
import time
from urllib.parse import urlencode

import mdi_hmi_patch_io as io

MIB = 1024**2
HOST = "jsoc.stanford.edu"
OUTPUT = io.BASE / "patch_download"
# Reserve the entire separate MTARP→MDATA lookup allowance (§8), irrespective of its ordering.
REQUEST_LIMIT = 200 - 45
SECONDS_LIMIT = 1800 - 300
FILE_LIMIT = 32*MIB
TOTAL_LIMIT = 512*MIB


def save(path, obj):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n")
    temp.replace(path)


def receive(host, target, dest, limit, expected, timeout, port=80):
    """One HTTP request. Parent and worker enforce an elapsed deadline incl. DNS/headers."""
    signal.setitimer(signal.ITIMER_REAL, timeout)
    with closing(http.client.HTTPConnection(host, port, timeout=min(timeout, 20))) as conn:
        conn.request("GET", target, headers={"Accept-Encoding": "identity"})
        with conn.getresponse() as res:
            if res.status != 200 or res.getheader("Content-Encoding", "identity").lower() != "identity":
                raise ValueError(f"Unexpected HTTP response {res.status} or encoding")
            raw = res.getheader("Content-Length")
            length = int(raw) if raw is not None else None
            if length is not None and not 0 < length <= limit:
                raise ValueError("Invalid Content-Length")
            if expected and (res.chunked or length not in expected):
                raise ValueError("FITS Content-Length disagrees with availability")
            with dest.open("xb") as f:
                while f.tell() < limit:
                    chunk = res.read1(min(65536, limit-f.tell()))
                    if not chunk:
                        break
                    f.write(chunk)
                size = f.tell()
            if size == 0 or (length is not None and size != length) or (length is None and size == limit):
                raise ValueError("Incomplete or capped HTTP body")


def transfer(target, dest, limit, expected, timeout):
    child = get_context("spawn").Process(target=receive, args=(HOST, target, dest, limit, expected, timeout))
    start = time.monotonic()
    child.start()
    try:
        child.join(max(0, timeout-(time.monotonic()-start)))
        if child.exitcode != 0:
            raise ValueError("HTTP worker failed or exceeded deadline")
    finally:
        if child.is_alive():
            child.kill()
        child.join()
        child.close()


class Unavailable(Exception):
    """One expected record or segment could not be acquired; keep its place in the manifest."""


def acquire(out, ledger, key, target, cap, expected, validate, transport=transfer):
    events = ledger["events"]
    previous = [e for e in events if e["key"] == key]
    for e in previous:
        if e["state"] == "ok":
            path = out/e["body"]
            io.verify(path, e["sha256"])
            validate(path)
            return path, e["sha256"]
    if len(previous) >= 2:
        raise Unavailable("Two attempts exhausted for "+key)
    budget_time = SECONDS_LIMIT-ledger["prior_seconds"]-sum(e["seconds"] for e in events)
    if (ledger["prior_attempts"]+len(events) >= REQUEST_LIMIT or budget_time < 1
            or expected and cap+sum(e["bytes"] for e in events if e["fits"]) > TOTAL_LIMIT):
        raise ValueError("Cumulative resource limit")
    index = len(events)+1
    path = out / (f"{index:03d}_{key}" + (".fits" if expected else ".json"))
    timeout = min(40., budget_time)
    # Persist worst-case charges before touching the network. After interruption this attempt
    # stays charged and its body never enters the verified manifest.
    e = dict(key=key, url="http://"+HOST+target, body=path.name, state="pending",
             seconds=timeout, bytes=cap, fits=bool(expected))
    events.append(e)
    save(out/"LEDGER.json", ledger)
    start = time.monotonic()
    try:
        transport(target, path, cap, expected, timeout)
        e["bytes"] = path.stat().st_size
        validate(path)
        e.update(state="ok", sha256=io.sha(path))
    except Exception as err:
        e.update(state="failed", error=str(err))
        raise Unavailable(f"{key}: {err}") from err
    finally:
        e["seconds"] = time.monotonic()-start
        save(out/"LEDGER.json", ledger)
    return path, e["sha256"]


def preflight():
    pairs, records = io.plan()
    cert, schemas = io.reference_inputs()
    prior = io.BASE/"availability/REQUESTS.json"
    io.verify(prior, "a0a42a3983636ea420f3695720a203e91bb21f620dfc76a9491852eaa2e0fa84")
    request_log = io.readjson(prior)
    n = request_log["prior_attempts"] + len(request_log["requests"])
    seconds = request_log["prior_seconds"] + sum(r["seconds"] for r in request_log["requests"])
    sizes = []
    for (series, key), files in records.items():
        side = "hmi" if series == io.HMI else "smarp"
        c = cert[side, key]
        for r in files.values():
            size = int(r["reported_bytes"])+1
            if not 0 < size <= FILE_LIMIT or r["dims"] != c["dims"] or c["state"] != "certified":
                raise ValueError("Per-file estimate or certificate")
            sizes.append(size)
    if n+len(records)+len(sizes)>REQUEST_LIMIT or sum(sizes)>TOTAL_LIMIT or seconds>=SECONDS_LIMIT:
        raise ValueError("Initial budget insufficient")
    return pairs, records, cert, schemas, n, seconds, sum(sizes)


def run(out, prepared, transport=transfer):
    pairs, records, certificates, schemas, n, seconds, total = prepared
    out.mkdir(parents=True, exist_ok=True)
    with (out/"LOCK").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        initial = dict(protocol=io.PROTOCOL_HASH, pairs=io.PAIR_HASH, segments=io.SEGMENT_HASH,
                       prior_attempts=n, prior_seconds=seconds, estimated_fits_bytes=total)
        ledger_path = out/"LEDGER.json"
        ledger = io.readjson(ledger_path) if ledger_path.exists() else dict(initial, events=[])
        if any(ledger.get(k) != v for k,v in initial.items()):
            raise ValueError("Ledger input mismatch")
        if not ledger_path.exists() and any(p.name!="LOCK" for p in out.iterdir()):
            raise ValueError("Missing ledger in populated directory")
        meta = {}
        manifest = []
        unavailable = {}
        def checkpoint():
            save(out/"MANIFEST.json", dict(protocol=io.PROTOCOL_HASH, estimated_bytes=total,
                 status="complete" if len(manifest)==sum(map(len, records.values())) and not unavailable else "partial",
                 segments=manifest, unavailable=unavailable))
        for p in pairs:
            times = {}
            for side in ("smarp", "hmi"):
                series, rec = p[side+"_series"], p[side+"_record"]
                num, t = rec.split("|")
                files = records[series, rec]
                tag = f"{int(p['slot']):02d}_{side}"
                quality = p["quality_mdi" if side=="smarp" else "quality_hmi"]
                target = "/cgi-bin/ajax/jsoc_info?"+urlencode(dict(op="rs_list",
                         ds=f"{series}[{num}][{t}]", key="**ALL**", seg=",".join(files), M=1))
                def check_meta(path):
                    kw = io.metadata(io.readjson(path), series, rec, files)
                    nx,ny = map(int,certificates[side,rec]["dims"].split("x"))
                    io.physical_header(kw, series, quality, (ny,nx), schemas[series])
                    return kw
                try:
                    path, digest = acquire(out, ledger, tag+"_keys", target, 2*MIB, (), check_meta, transport)
                except Unavailable as exc:
                    unavailable[tag+"_keys"] = str(exc)
                    checkpoint()
                    continue
                kw = check_meta(path)
                times[side] = io.tai(kw["T_OBS"])
                meta[series,rec] = dict(metadata=path.name, metadata_sha256=digest, t_obs=kw["T_OBS"])
            if len(times) < 2:
                continue
            dt = (times["hmi"]-times["smarp"]).to_value("sec")
            if abs(dt)>360 or abs(dt-float(p["dt_obs_s"]))>1.01:
                raise ValueError("T_OBS differs from selected pair")
        for (series, rec), files in records.items():
            if (series,rec) not in meta:
                continue
            for name,r in files.items():
                tag = f"{int(r['slot']):02d}_{'hmi' if series==io.HMI else 'smarp'}_{name}"
                size = int(r["reported_bytes"])
                # Archived jsoc_info starts its single-segment size sum at -1.
                expected = (size, size+1)
                def check_fits(path):
                    with path.open("rb") as f:
                        signature = f.read(9)
                    if signature != b"SIMPLE  =" or path.stat().st_size not in expected or path.stat().st_size%2880:
                        raise ValueError("Unexpected native FITS signature or archive size")
                try:
                    path,digest = acquire(out, ledger, tag, r["path"], size+1, expected, check_fits, transport)
                except Unavailable as exc:
                    unavailable[tag] = str(exc)
                    checkpoint()
                    continue
                manifest.append(dict(**r, file=path.name, sha256=digest, actual_bytes=path.stat().st_size,
                                     **meta[series,rec]))
                checkpoint()
        checkpoint()
        return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="perform the reviewed download")
    args = ap.parse_args()
    data = preflight()
    print(f"{len(data[0])} pairs; {len(data[1])} records; FITS budget estimate {data[-1]} bytes")
    if args.fetch:
        acquired = run(OUTPUT, data)
        print(f"Verified {len(acquired)}/84 FITS. See {OUTPUT}/MANIFEST.json")
        if len(acquired) != 84:
            raise SystemExit(1)
