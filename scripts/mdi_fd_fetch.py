"""MDI pilot, phase 4b: download of the level-2 full-disk FITS of the A1 plan (results/MDI_PILOT_L2_PLAN_A1).
NETWORK: only after code review AND the user's explicit authorisation (--fetch).

Before any request: frozen A1 (SHA), plan products and hashes, strict plan recount receipt bound to the plan META;
the whole run holds the ledger RunLock and every attempt reserves 32 MiB (sizes unknown in the metadata), replaced by
the actual bytes when it ends. Transport: A1 transport of scripts/mdi_hmi_patch_download.py (plain HTTP, at most one
redirect to an allowed JSOC host with verified TLS), actual requests and bytes recorded.
Persistent checkpoint results/MDI_PILOT_L2_FITS/CHECKPOINT.jsonl (append-only, committed after every run): one line per
attempt with path, T_REC, attempt number, status, bytes, file name, SHA-256 of a completed file and the plan META SHA.
  - at most 2 attempts per file over ALL runs (counted from the checkpoint);
  - a file already in the destination must match the SHA of its completed checkpoint line; a mismatch, or a file
    without a completed line (unknown provenance), stops the run without overwriting anything;
  - the run stops after 3 consecutive failures of the same class or when the ledger refuses a reservation.
Each run writes RUN_<n>.json with per-file states and an explicit completeness; exit 0 only if every planned file is
complete. FITS are stored outside Git (data/sharp/mdi_pilot_l2/).

    .venv/bin/python scripts/mdi_fd_fetch.py --selftest
    .venv/bin/python scripts/mdi_fd_fetch.py --fetch      # only after review and the user's authorisation
"""
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PLAN, PLAN_REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1", ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
DEST = ROOT / "data/sharp/mdi_pilot_l2"
STATE = ROOT / "results/MDI_PILOT_L2_FITS"
MAX_ATTEMPTS, MAX_SAME_CLASS, TIMEOUT_S = 2, 3, 120
PLAN_PRODUCTS = {"CHOICES_A1.csv", "CHOICES_ORIGINAL.csv", "PLAN.csv", "COVERAGE.csv"}
_spec = importlib.util.spec_from_file_location("mdi_l2_ledger", ROOT / "scripts/mdi_l2_ledger.py")
LG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LG)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def strict_receipt(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    si = lambda x: isinstance(x, int) and not isinstance(x, bool)          # noqa: E731
    return (si(p) and si(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False and r.get(key) == sha(meta))


def gate(plan=PLAN, plan_rec=PLAN_REC, a1=A1, a1_freeze=A1_FREEZE):
    probs = []
    fz = json.loads(Path(a1_freeze).read_text())
    m = json.loads((Path(plan) / "META.json").read_text())
    if sha(a1) != fz.get("sha256") or m.get("a1_sha256") != fz.get("sha256"):
        probs.append("A1")
    ps = m.get("products_sha256", {})
    if set(ps) != PLAN_PRODUCTS or any(sha(Path(plan) / n) != h for n, h in ps.items()):
        probs.append("plan products")
    if not strict_receipt(Path(plan_rec) / "RECEIPT.json", "plan_meta_sha256", Path(plan) / "META.json"):
        probs.append("plan recount receipt")
    return probs


def real_transport(target, dest, limit, expected, timeout):
    import mdi_hmi_patch_download as dl
    return dl.transfer_a1(target, dest, limit, expected, timeout)


def check_fits(path):
    try:
        with fits.open(path) as hd:
            if hd[-1].data is None or hd[-1].data.shape != (1024, 1024):
                return "unexpected_shape"
    except Exception as exc:
        return f"unreadable ({type(exc).__name__})"
    return "ok"


def file_name(t_rec):
    return "mdi.fd_M_96m_lev182." + str(t_rec).replace(":", "").replace(".", "") + ".data.fits"


def read_checkpoint(path):
    p = Path(path)
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def append_checkpoint(path, entry):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a") as f:
        f.write(json.dumps(dict(entry, utc=datetime.now(timezone.utc).isoformat())) + "\n")


def run(plan=PLAN, plan_rec=PLAN_REC, a1=A1, a1_freeze=A1_FREEZE, dest=DEST, state=STATE, transport=real_transport, ledger=None, require_clean=True):
    ledger = ledger or LG.LEDGER
    probs = gate(plan, plan_rec, a1, a1_freeze)
    if require_clean and subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        probs.append("tracked tree not clean")
    if probs:
        sys.exit("gate: " + "; ".join(probs))
    plan_sha = sha(Path(plan) / "META.json")
    P = pd.read_csv(Path(plan) / "PLAN.csv", keep_default_na=False, na_values=[""])
    ck = Path(state) / "CHECKPOINT.jsonl"
    Path(dest).mkdir(parents=True, exist_ok=True)
    stopped, last_kind, same_kind, states = "", None, 0, {}
    with LG.RunLock(ledger):
        entries = read_checkpoint(ck)
        if any(e.get("plan_meta_sha256") != plan_sha for e in entries):
            sys.exit("checkpoint belongs to another plan")
        done = {e["path"]: e for e in entries if e["status"] == "ok"}
        attempts = {}
        for e in entries:
            attempts[e["path"]] = attempts.get(e["path"], 0) + 1
        for r in P.itertuples():
            f = Path(dest) / file_name(r.T_REC)
            if r.path in done:
                if not f.exists():
                    states[r.path] = "completed_file_missing"
                    stopped = stopped or "a completed file is missing from the destination"
                    break
                if sha(f) != done[r.path]["sha256"]:
                    stopped = "SHA of a completed file differs from its checkpoint: stop, nothing overwritten"
                    states[r.path] = "sha_mismatch"
                    break
                states[r.path] = "complete"
                continue
            if f.exists():
                stopped = "file present without a completed checkpoint line (unknown provenance): stop"
                states[r.path] = "unknown_provenance"
                break
            if attempts.get(r.path, 0) >= MAX_ATTEMPTS:
                states[r.path] = "failed_attempts_exhausted"
                continue
            while attempts.get(r.path, 0) < MAX_ATTEMPTS:
                i, why = LG.reserve("fits", r.path, LG.FILE_CAP_BYTES, ledger)
                if i is None:
                    stopped = f"ledger refused: {why}"
                    break
                n = attempts.get(r.path, 0) + 1
                attempts[r.path] = n
                tmp = f.with_suffix(".part")
                if tmp.exists():
                    tmp.unlink()
                try:
                    nreq, final_url = transport(r.path, tmp, LG.FILE_CAP_BYTES, None, TIMEOUT_S)
                    got = tmp.stat().st_size if tmp.exists() else 0
                    st = check_fits(tmp)
                    if st == "ok":
                        tmp.rename(f)
                        h = sha(f)
                        LG.finish(i, "fits", nreq, got, "ok", path=ledger)
                        append_checkpoint(ck, dict(path=r.path, T_REC=r.T_REC, attempt=n, status="ok", bytes=got, file=f.name, sha256=h,
                                                   final_url=final_url, plan_meta_sha256=plan_sha))
                        states[r.path] = "complete"
                        last_kind, same_kind = None, 0
                        break
                    LG.finish(i, "fits", nreq, got, "partial", st, "check", path=ledger)
                    kind, err = "invalid_file", st
                except Exception as exc:
                    got = tmp.stat().st_size if tmp.exists() else 0
                    kind = getattr(exc, "kind", type(exc).__name__)
                    err = f"{kind}: {exc}"
                    LG.finish(i, "fits", getattr(exc, "requests", LG.OPEN_REQUESTS), got, "failed", err, "transfer", path=ledger)
                if tmp.exists():
                    tmp.unlink()
                append_checkpoint(ck, dict(path=r.path, T_REC=r.T_REC, attempt=n, status="failed", bytes=got, file=f.name, error=err,
                                           plan_meta_sha256=plan_sha))
                states[r.path] = "failed" if attempts[r.path] < MAX_ATTEMPTS else "failed_attempts_exhausted"
                same_kind = same_kind + 1 if kind == last_kind else 1
                last_kind = kind
                if same_kind >= MAX_SAME_CLASS:
                    stopped = f"{MAX_SAME_CLASS} consecutive failures of class {kind}"
                    break
            if stopped:
                break
        for r in P.itertuples():
            states.setdefault(r.path, "not_attempted")
        complete = all(states[p] == "complete" for p in P.path)
        runs = sorted(Path(state).glob("RUN_*.json"))
        summary = dict(run=len(runs) + 1, plan_meta_sha256=plan_sha, script_sha256=sha(__file__), planned=len(P),
                       complete=int(sum(v == "complete" for v in states.values())), completeness="complete" if complete else "incomplete",
                       stopped=stopped, states={k: v for k, v in states.items() if v != "complete"}, ledger_totals_after=LG.totals(ledger),
                       checkpoint_sha256=sha(ck) if ck.exists() else None)
        Path(state).mkdir(parents=True, exist_ok=True)
        (Path(state) / f"RUN_{len(runs) + 1:03d}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("planned", "complete", "completeness", "stopped")}))
    return 0 if complete else 2


# ---------------------------------------------------------------- selftest (offline, fake transport)

def synthetic_fits(path, shape=(1024, 1024), value=0.0):
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(np.full(shape, value, dtype=np.float32))]).writeto(path)


def fixture(td, paths):
    """Consistent synthetic A1 freeze, plan (products, META) and strict plan recount receipt."""
    td = Path(td)
    td.mkdir(parents=True, exist_ok=True)
    (td / "a1.md").write_text("A1 frozen")
    (td / "a1_freeze.json").write_text(json.dumps(dict(sha256=sha(td / "a1.md"))))
    pl, pr = td / "plan", td / "planrec"
    pl.mkdir()
    pr.mkdir()
    pd.DataFrame(dict(path=paths, T_REC=[f"2000.06.01_0{k}:00:00_TAI" for k in range(len(paths))], size=[None] * len(paths))).to_csv(pl / "PLAN.csv", index=False)
    for n in ("CHOICES_A1.csv", "CHOICES_ORIGINAL.csv", "COVERAGE.csv"):
        (pl / n).write_text("x\n")
    (pl / "META.json").write_text(json.dumps(dict(a1_sha256=sha(td / "a1.md"), products_sha256={n: sha(pl / n) for n in PLAN_PRODUCTS})))
    (pr / "RECEIPT.json").write_text(json.dumps(dict(passed=1, total=1, partial=False, checks=[dict(ok=True)], plan_meta_sha256=sha(pl / "META.json"))))
    return dict(plan=pl, plan_rec=pr, a1=td / "a1.md", a1_freeze=td / "a1_freeze.json", require_clean=False)


def selftest():
    import contextlib
    import io
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    class TErr(Exception):
        def __init__(self, kind):
            super().__init__(kind)
            self.kind, self.requests = kind, 1

    def quiet(*a, **k):
        with contextlib.redirect_stdout(io.StringIO()):
            return run(*a, **k)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        good, bad = td / "good.fits", td / "bad.fits"
        synthetic_fits(good)
        synthetic_fits(bad, (10, 10))
        script = {}

        def fake(target, dest, limit, expected, timeout):
            act = script[target].pop(0)
            if act in ("ok", "bad"):
                shutil.copyfile(good if act == "ok" else bad, dest)
                return 2, "https://jsoc1.stanford.edu" + target
            Path(dest).write_bytes(b"x" * 100)
            raise TErr(act)
        fx = fixture(td / "f1", ["/SUM/1", "/SUM/2", "/SUM/3"])
        script.update({"/SUM/1": ["ok"], "/SUM/2": ["http_500", "ok"], "/SUM/3": ["bad", "bad"]})
        kw = dict(dest=td / "d1", state=td / "s1", transport=fake, ledger=td / "L1.jsonl", **fx)
        rc = quiet(**kw)
        ck = read_checkpoint(td / "s1/CHECKPOINT.jsonl")
        ok("run 1: two complete (one after a retry), one invalid twice -> incomplete, exit 2", rc == 2
           and [e["status"] for e in ck] == ["ok", "failed", "ok", "failed", "failed"])
        t = LG.totals(td / "L1.jsonl")
        ok("ledger: actual bytes replace reservations; failed bytes counted", t["open_attempts"] == 0 and t["files"] == 2
           and t["bytes"] == 2 * good.stat().st_size + 100 + 2 * bad.stat().st_size, t)
        script.update({"/SUM/3": ["ok"]})
        rc = quiet(**kw)
        ok("run 2: attempts persist across runs (file 3 exhausted, not retried); completed files verified by checkpoint SHA",
           rc == 2 and script["/SUM/3"] == ["ok"])
        f1 = td / "d1" / file_name("2000.06.01_00:00:00_TAI")
        synthetic_fits(td / "tmp.fits", value=7.0)
        shutil.copyfile(td / "tmp.fits", f1)
        rc = quiet(**kw)
        r = json.loads(sorted((td / "s1").glob("RUN_*.json"))[-1].read_text())
        ok("resume refuses a completed file whose pixels changed, nothing overwritten", rc == 2 and "SHA" in r["stopped"]
           and sha(f1) == sha(td / "tmp.fits"))
        fx2 = fixture(td / "f2", ["/SUM/a"])
        (td / "d2").mkdir()
        synthetic_fits(td / "d2" / file_name("2000.06.01_00:00:00_TAI"))
        script.update({"/SUM/a": ["ok"]})
        rc = quiet(dest=td / "d2", state=td / "s2", transport=fake, ledger=td / "L2.jsonl", **fx2)
        ok("a file present without checkpoint provenance stops the run without requests", rc == 2 and script["/SUM/a"] == ["ok"])
        fx3 = fixture(td / "f3", [f"/SUM/t{k}" for k in range(3)])
        script.update({f"/SUM/t{k}": ["timeout", "timeout"] for k in range(3)})
        rc = quiet(dest=td / "d3", state=td / "s3", transport=fake, ledger=td / "L3.jsonl", **fx3)
        r = json.loads(sorted((td / "s3").glob("RUN_*.json"))[-1].read_text())
        ok("stop after 3 consecutive failures of the same class", rc == 2 and "consecutive" in r["stopped"], r["stopped"])
        fx4 = fixture(td / "f4", ["/SUM/z"])
        big = td / "L4.jsonl"
        i, _ = LG.reserve("fits", "/x", LG.CAP_BYTES - 1000, big)
        LG.finish(i, "fits", 1, LG.CAP_BYTES - 1000, "ok", path=big)
        script.update({"/SUM/z": ["ok"]})
        rc = quiet(dest=td / "d4", state=td / "s4", transport=fake, ledger=big, **fx4)
        ok("ledger refusal before any request (32 MiB reservation over the residual budget)", rc == 2 and script["/SUM/z"] == ["ok"])
        fx5 = fixture(td / "f5", ["/SUM/q"])
        rc5 = json.loads((fx5["plan_rec"] / "RECEIPT.json").read_text())
        (fx5["plan_rec"] / "RECEIPT.json").write_text(json.dumps(dict(rc5, partial=True)))
        script.update({"/SUM/q": ["ok"]})
        try:
            quiet(dest=td / "d5", state=td / "s5", transport=fake, ledger=td / "L5.jsonl", **fx5)
            ok("partial plan receipt: refused before any request", False)
        except SystemExit:
            ok("partial plan receipt: refused before any request", script["/SUM/q"] == ["ok"])
        fx6 = fixture(td / "f6", ["/SUM/c1"])
        script.update({"/SUM/c1": ["ok"]})
        rc = quiet(dest=td / "d6", state=td / "s6", transport=fake, ledger=td / "L6.jsonl", **fx6)
        ok("complete plan -> exit 0, completeness complete", rc == 0)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
