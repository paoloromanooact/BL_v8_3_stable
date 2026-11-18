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
import ssl
import time
from urllib.parse import urlencode, urlsplit

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


# ---------------------------------------------------------------- amendment A1 (docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON_A1.md)

A1_HASH = "42ca9d3c802079c4b16ef45b5639a812c25c34596c1b821216d511cd86162778"
A1_HOSTS = ("jsoc.stanford.edu", "jsoc1.stanford.edu", "jsoc2.stanford.edu")
A1_REQUESTS = 250
A1_SECONDS = 1200
A1_STOP_AFTER = 3
OUTPUT_A1 = io.BASE / "patch_download_a1"


class TransportError(ValueError):
    """Failure with a class label for the systematic-error stop (A1 §5)."""

    def __init__(self, kind, msg):
        super().__init__(f"{kind}: {msg}")
        self.kind = kind


def follow_location(location, path):
    """A1 §3: one redirect to an allowed JSOC host with the same /SUM.../S.../<segment>.fits; else None."""
    if not location:
        return None
    u = urlsplit(location)
    scheme, host = (u.scheme or "http").lower(), (u.hostname or HOST).lower()
    if scheme not in ("http", "https") or host not in A1_HOSTS or u.query or u.fragment or u.username:
        return None
    if not (u.path == path or u.path.endswith(path)):
        return None
    return scheme, host, u.port or (443 if scheme == "https" else 80), u.path


def _body(res, dest, limit, expected):
    raw = res.getheader("Content-Length")
    length = int(raw) if raw is not None else None
    if res.getheader("Content-Encoding", "identity").lower() != "identity":
        raise TransportError("encoding", "unexpected Content-Encoding")
    if length is not None and not 0 < length <= limit:
        raise TransportError("length", "invalid Content-Length")
    if expected and (res.chunked or length not in expected):
        raise TransportError("length", "FITS Content-Length disagrees with availability")
    with dest.open("xb") as f:
        while f.tell() < limit:
            chunk = res.read1(min(65536, limit - f.tell()))
            if not chunk:
                break
            f.write(chunk)
        size = f.tell()
    if size == 0 or (length is not None and size != length) or (length is None and size == limit):
        raise TransportError("length", "incomplete or capped HTTP body")


def receive_a1(target, dest, limit, expected, timeout, sidecar, opener=None):
    """GET http://jsoc.stanford.edu<target>; follow at most one allowed redirect with verified TLS.
    The number of HTTP requests and the final URL are written to sidecar (JSON) before any body check."""
    opener = opener or _open
    info = dict(requests=0, final_url=None)
    try:
        info["requests"] += 1
        status, location, res, conn = opener("http", HOST, 80, target, timeout)
        try:
            if status in (301, 302, 303, 307, 308):
                nxt = follow_location(location, target)
                if nxt is None:
                    raise TransportError("redirect", f"redirect not allowed: {location}")
                conn.close()
                info["requests"] += 1
                status, location, res, conn = opener(*nxt, timeout)
                if status in (301, 302, 303, 307, 308):
                    raise TransportError("redirect", "second redirect")
                info["final_url"] = f"{nxt[0]}://{nxt[1]}{nxt[3]}"
            else:
                info["final_url"] = f"http://{HOST}{target}"
            if status != 200:
                raise TransportError(f"http_{status}", "unexpected status")
            _body(res, dest, limit, expected)
        finally:
            conn.close()
    except ssl.SSLError as exc:
        raise TransportError("tls", str(exc)) from exc
    finally:
        sidecar.write_text(json.dumps(info))


def _open(scheme, host, port, path, timeout):
    if scheme == "https":
        conn = http.client.HTTPSConnection(host, port, timeout=min(timeout, 20), context=ssl.create_default_context())
    else:
        conn = http.client.HTTPConnection(host, port, timeout=min(timeout, 20))
    conn.request("GET", path, headers={"Accept-Encoding": "identity"})
    res = conn.getresponse()
    return res.status, res.getheader("Location"), res, conn


def _child(target, dest, limit, expected, timeout, sidecar, errfile):
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        receive_a1(target, dest, limit, expected, timeout, sidecar)
    except TransportError as exc:
        errfile.write_text(json.dumps(dict(kind=exc.kind, error=str(exc))))
        raise


def transfer_a1(target, dest, limit, expected, timeout):
    """Spawned worker with an elapsed deadline (as transfer); returns (requests, final_url)."""
    sidecar, errfile = dest.with_suffix(".transport.json"), dest.with_suffix(".error.json")
    child = get_context("spawn").Process(target=_child, args=(target, dest, limit, expected, timeout, sidecar, errfile))
    start = time.monotonic()
    child.start()
    try:
        child.join(max(0, timeout - (time.monotonic() - start)))
        info = json.loads(sidecar.read_text()) if sidecar.exists() else dict(requests=2, final_url=None)
        if child.exitcode != 0:
            kind = json.loads(errfile.read_text())["kind"] if errfile.exists() else "worker"
            raise TransportError(kind, "HTTP worker failed or exceeded deadline")
        return info["requests"], info["final_url"]
    finally:
        if child.is_alive():
            child.kill()
        child.join()
        child.close()


def run_a1(prepared, old=OUTPUT, out=OUTPUT_A1, transport=transfer_a1):
    """A1 §4-§5: keywords reused from the first ledger (SHA-256 verified), one remaining attempt per FITS,
    separate budget of HTTP requests and seconds, stop after 3 consecutive failures of the same class."""
    pairs, records, certificates, schemas, n, seconds, total = prepared
    io.verify(io.ROOT / "docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON_A1.md", A1_HASH)
    first = io.readjson(old / "LEDGER.json")
    if (first["protocol"], first["pairs"], first["segments"]) != (io.PROTOCOL_HASH, io.PAIR_HASH, io.SEGMENT_HASH):
        raise ValueError("First ledger provenance")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "LOCK").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lp = out / "LEDGER.json"
        ledger = io.readjson(lp) if lp.exists() else dict(
            protocol=io.PROTOCOL_HASH, pairs=io.PAIR_HASH, segments=io.SEGMENT_HASH, amendment=A1_HASH,
            first_ledger_sha256=io.sha(old / "LEDGER.json"), events=[])
        if ledger.get("amendment") != A1_HASH:
            raise ValueError("Ledger amendment mismatch")
        events = ledger["events"]
        diag = out / "DIAGNOSIS.json"
        diag_requests = 1 if diag.exists() else 0
        # keys: copy the verified first-ledger bodies (no network) under the same key names
        ok_first = {e["key"]: e for e in first["events"] if e["state"] == "ok"}
        failed_first = {e["key"]: e for e in first["events"] if e["state"] != "ok"}
        for key, e in ok_first.items():
            if not key.endswith("_keys") or any(x["key"] == key for x in events):
                continue
            src = old / e["body"]
            io.verify(src, e["sha256"])
            dst = out / e["body"]
            dst.write_bytes(src.read_bytes())
            events.append(dict(e, copied_from=str(src.relative_to(io.BASE)), requests=0))
        save(lp, ledger)
        manifest, unavailable, last_kinds = [], {}, []

        def used():
            return (diag_requests + sum(x.get("requests", 0) for x in events),
                    sum(x.get("seconds", 0) for x in events if "copied_from" not in x))

        def checkpoint(stopped=None):
            save(out / "MANIFEST.json", dict(protocol=io.PROTOCOL_HASH, amendment=A1_HASH, estimated_bytes=total,
                 status=("complete" if len(manifest) == 84 and not unavailable else "partial"),
                 stopped=stopped, requests_used=used()[0], seconds_used=used()[1],
                 segments=manifest, unavailable=unavailable))
        for (series, rec), files in records.items():
            side = "hmi" if series == io.HMI else "smarp"
            for name, r in files.items():
                tag = f"{int(r['slot']):02d}_{side}_{name}"
                done = [x for x in events if x["key"] == tag and x["state"] == "ok"]
                if done:
                    path = out / done[0]["body"]
                    io.verify(path, done[0]["sha256"])
                    manifest.append(dict(**r, file=path.name, sha256=done[0]["sha256"], actual_bytes=path.stat().st_size,
                                         final_url=done[0].get("final_url")))
                    continue
                tried = (1 if tag in failed_first else 0) + sum(1 for x in events if x["key"] == tag)
                if tried >= 2:
                    unavailable[tag] = "two attempts exhausted"
                    continue
                req, secs = used()
                fits_bytes = sum(x["bytes"] for x in events if x.get("fits") and "copied_from" not in x)
                size = int(r["reported_bytes"])
                if req + 2 > A1_REQUESTS or A1_SECONDS - secs < 1 or fits_bytes + size + 1 > TOTAL_LIMIT:
                    checkpoint("A1 budget")
                    raise ValueError("A1 budget exhausted")
                path = out / f"{len(events) + 1:03d}_{tag}.fits"
                e = dict(key=tag, url="http://" + HOST + r["path"], body=path.name, state="pending",
                         seconds=min(40., A1_SECONDS - secs), bytes=size + 1, fits=True, requests=2)
                events.append(e)
                save(lp, ledger)
                start = time.monotonic()
                try:
                    nreq, final = transport(r["path"], path, size + 1, (size, size + 1), e["seconds"])
                    e.update(requests=nreq, final_url=final, bytes=path.stat().st_size)
                    with path.open("rb") as f:
                        if f.read(9) != b"SIMPLE  =" or path.stat().st_size % 2880:
                            raise TransportError("signature", "unexpected FITS signature or size")
                    e.update(state="ok", sha256=io.sha(path))
                    manifest.append(dict(**r, file=path.name, sha256=e["sha256"], actual_bytes=e["bytes"], final_url=final))
                    last_kinds = []
                except TransportError as exc:
                    e.update(state="failed", error=str(exc), kind=exc.kind)
                    unavailable[tag] = str(exc)
                    last_kinds.append(exc.kind)
                finally:
                    e["seconds"] = time.monotonic() - start
                    side_info = path.with_suffix(".transport.json")
                    if side_info.exists():
                        e["requests"] = json.loads(side_info.read_text())["requests"]
                    save(lp, ledger)
                    checkpoint()
                if len(last_kinds) >= A1_STOP_AFTER and len(set(last_kinds[-A1_STOP_AFTER:])) == 1:
                    checkpoint(f"systematic error: {last_kinds[-1]}")
                    raise ValueError(f"stopped after {A1_STOP_AFTER} consecutive '{last_kinds[-1]}' failures")
        checkpoint()
        return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fetch", action="store_true", help="perform the reviewed download")
    ap.add_argument("--fetch-a1", action="store_true", help="amendment A1 transport (one allowed redirect)")
    args = ap.parse_args()
    data = preflight()
    print(f"{len(data[0])} pairs; {len(data[1])} records; FITS budget estimate {data[-1]} bytes")
    if args.fetch_a1:
        acquired = run_a1(data)
        print(f"Verified {len(acquired)}/84 FITS. See {OUTPUT_A1}/MANIFEST.json")
        raise SystemExit(0 if len(acquired) == 84 else 1)
    if args.fetch:
        acquired = run(OUTPUT, data)
        print(f"Verified {len(acquired)}/84 FITS. See {OUTPUT}/MANIFEST.json")
        if len(acquired) != 84:
            raise SystemExit(1)
