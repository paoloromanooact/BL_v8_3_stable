"""Shared, cumulative, append-only network ledger of the MDI pilot level 2 (metadata and FITS together).

Every network attempt is appended BEFORE its outcome is used, then completed with a second line: kind (metadata|fits),
target, HTTP requests made (redirects included), bytes received (also for failed or partial transfers), status
(ok|failed|partial) and error. Caps are cumulative over the whole ledger, failures included:
<= 600 requests, <= 220 FITS files received, <= 1.5e9 bytes. A size that is not known is never counted as zero: the
budget check uses the per-file cap instead. The ledger file is committed after every networked step.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results/MDI_PILOT_L2_LEDGER/LEDGER.jsonl"
CAP_REQUESTS, CAP_FILES, CAP_BYTES = 600, 220, int(1.5e9)
FILE_CAP_BYTES = 32 * 1024 ** 2


def entries(path=LEDGER):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def totals(path=LEDGER):
    """Cumulative usage: completed attempts count their actual requests and bytes; an attempt started but never
    completed counts as the worst case (2 requests, the per-file cap for FITS)."""
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
    for i, e in started.items():
        if i not in done:                                   # interrupted: worst case, never zero
            req += 2
            byt += FILE_CAP_BYTES if e["kind"] == "fits" else 0
    return dict(requests=req, bytes=byt, files=files, open_attempts=len(set(started) - done))


def can_start(kind, expected_bytes=None, path=LEDGER):
    t = totals(path)
    need_b = FILE_CAP_BYTES if (kind == "fits" and not expected_bytes) else int(expected_bytes or 0)
    if t["requests"] + 2 > CAP_REQUESTS:
        return False, "request cap"
    if kind == "fits" and t["files"] + 1 > CAP_FILES:
        return False, "file cap"
    if t["bytes"] + need_b > CAP_BYTES:
        return False, "byte cap"
    return True, ""


def start(kind, target, path=LEDGER):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    i = f"{kind}-{len(entries(p))}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    with p.open("a") as f:
        f.write(json.dumps(dict(id=i, phase="start", kind=kind, target=target, utc=datetime.now(timezone.utc).isoformat())) + "\n")
    return i


def finish(i, kind, requests, nbytes, status, error="", path=LEDGER):
    with Path(path).open("a") as f:
        f.write(json.dumps(dict(id=i, phase="end", kind=kind, requests=int(requests), bytes=int(nbytes), status=status, error=error,
                                utc=datetime.now(timezone.utc).isoformat())) + "\n")


def selftest():
    import tempfile
    res = []

    def ok(n, c):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n}")

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "L.jsonl"
        i = start("metadata", "q1", p)
        finish(i, "metadata", 1, 5000, "ok", path=p)
        i = start("fits", "/SUM/a", p)
        finish(i, "fits", 2, 1000, "failed", "http_404", path=p)
        start("fits", "/SUM/b", p)                                       # interrupted
        t = totals(p)
        ok("cumulative totals: failed transfers counted, interrupted attempt as worst case",
           t["requests"] == 1 + 2 + 2 and t["bytes"] == 5000 + 1000 + FILE_CAP_BYTES and t["files"] == 0 and t["open_attempts"] == 1)
        ok("unknown FITS size budgeted at the per-file cap, never zero", can_start("fits", None, p)[0]
           and not can_start("fits", CAP_BYTES, p)[0])
        q = Path(td) / "full.jsonl"
        for k in range(300):
            j = start("metadata", f"q{k}", q)
            finish(j, "metadata", 2, 10, "ok", path=q)
        ok("request cap enforced cumulatively", not can_start("metadata", 0, q)[0])
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
