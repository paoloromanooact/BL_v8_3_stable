"""Shared, cumulative, append-only network ledger of the MDI pilot level 2 (metadata and FITS together).

Protocol of an attempt:
  reserve(kind, target, reserve_bytes) -> id   under a global lock: checks the cumulative caps INCLUDING the bytes
                                               reserved by every open attempt, then appends a 'start' line with the
                                               reservation; refuses (None, reason) if the caps would be exceeded;
  finish(id, kind, requests, bytes, status)    appends the actual HTTP requests (redirects included) and bytes
                                               RECEIVED, also for failed or partial transfers.
An attempt never finished keeps its reservation (2 requests and the reserved bytes): never counted as zero.
RunLock: exclusive lock held for a whole networked run, so that two runs cannot proceed concurrently.
Caps (cumulative, failures included): <= 600 requests, <= 220 FITS received, <= 1.5e9 bytes.
"""
import fcntl
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results/MDI_PILOT_L2_LEDGER/LEDGER.jsonl"
CAP_REQUESTS, CAP_FILES, CAP_BYTES = 600, 220, int(1.5e9)
FILE_CAP_BYTES = 32 * 1024 ** 2
METADATA_CAP_BYTES = 5_000_000
OPEN_REQUESTS = 2


def entries(path=LEDGER):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def totals(path=LEDGER):
    req = byt = files = 0
    started, done = {}, set()
    for e in entries(path):
        if e["phase"] == "start":
            started[e["id"]] = e
        else:
            done.add(e["id"])
            req += int(e["requests"])
            byt += int(e["bytes"])
            files += int(e["kind"] == "fits" and e["status"] == "ok")
    open_ = [e for i, e in started.items() if i not in done]
    req += OPEN_REQUESTS * len(open_)
    byt += sum(int(e["reserve_bytes"]) for e in open_)
    return dict(requests=req, bytes=byt, files=files, open_attempts=len(open_))


class _Lock:
    def __init__(self, path, blocking=True):
        self.path, self.blocking, self.f = Path(str(path) + ".lock"), blocking, None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = self.path.open("a")
        try:
            fcntl.flock(self.f, fcntl.LOCK_EX | (0 if self.blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            self.f.close()
            raise RuntimeError("another networked run holds the ledger")
        return self

    def __exit__(self, *a):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def RunLock(path=LEDGER):
    """Exclusive, non-blocking lock for a whole networked run."""
    return _Lock(Path(str(path) + ".run"), blocking=False)


def reserve(kind, target, reserve_bytes, path=LEDGER):
    """Atomic check-and-start. Returns (id, '') or (None, reason)."""
    with _Lock(path):
        t = totals(path)
        if t["requests"] + OPEN_REQUESTS > CAP_REQUESTS:
            return None, "request cap"
        if kind == "fits" and t["files"] + 1 > CAP_FILES:
            return None, "file cap"
        if t["bytes"] + int(reserve_bytes) > CAP_BYTES:
            return None, "byte cap"
        i = f"{kind}-{len(entries(path))}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
        with Path(path).open("a") as f:
            f.write(json.dumps(dict(id=i, phase="start", kind=kind, target=target, reserve_bytes=int(reserve_bytes),
                                    utc=datetime.now(timezone.utc).isoformat())) + "\n")
        return i, ""


def finish(i, kind, requests, nbytes, status, error="", stage="", path=LEDGER):
    with _Lock(path):
        with Path(path).open("a") as f:
            f.write(json.dumps(dict(id=i, phase="end", kind=kind, requests=int(requests), bytes=int(nbytes), status=status,
                                    stage=stage, error=error, utc=datetime.now(timezone.utc).isoformat())) + "\n")


def selftest():
    import tempfile
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "L.jsonl"
        i, _ = reserve("metadata", "q1", METADATA_CAP_BYTES, p)
        finish(i, "metadata", 1, 1234, "failed", "HTTP 500", "http", p)
        i, _ = reserve("metadata", "q2", METADATA_CAP_BYTES, p)
        finish(i, "metadata", 1, 800, "ok", path=p)
        reserve("fits", "/SUM/b", FILE_CAP_BYTES, p)                         # interrupted
        t = totals(p)
        ok("failed bytes counted (1234 + 800); open attempt keeps its reservation and 2 requests",
           t["bytes"] == 1234 + 800 + FILE_CAP_BYTES and t["requests"] == 1 + 1 + 2 and t["open_attempts"] == 1, t)
        q = Path(td) / "near.jsonl"
        i, _ = reserve("fits", "/x", CAP_BYTES - METADATA_CAP_BYTES + 1, q)
        finish(i, "fits", 1, CAP_BYTES - METADATA_CAP_BYTES + 1, "ok", path=q)
        j, why = reserve("metadata", "q", METADATA_CAP_BYTES, q)
        ok("residual budget below the metadata reservation -> refused before any request", j is None and why == "byte cap", why)
        r = Path(td) / "req.jsonl"
        for k in range(300):
            a, _ = reserve("metadata", f"q{k}", 10, r)
            finish(a, "metadata", 2, 10, "ok", path=r)
        ok("request cap enforced cumulatively", reserve("metadata", "q", 10, r)[0] is None)
        s = Path(td) / "run.jsonl"
        with RunLock(s):
            try:
                with RunLock(s):
                    ok("a second concurrent run is refused", False)
            except RuntimeError:
                ok("a second concurrent run is refused", True)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
