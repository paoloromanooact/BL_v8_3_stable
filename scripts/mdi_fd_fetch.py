"""MDI pilot, phase 4b: download of the level-2 full-disk FITS of the frozen download plan (results/MDI_PILOT_L2_METADATA).
NETWORK: only after code review AND the user's explicit authorisation (--fetch); a blind amendment on QUALITY, if any,
is frozen BEFORE this step.

Transport: the A1 transport of scripts/mdi_hmi_patch_download.py (plain HTTP to jsoc.stanford.edu, at most one redirect
to an allowed JSOC host with verified TLS). Every attempt goes through the shared cumulative ledger
(scripts/mdi_l2_ledger.py) before its outcome is used; caps are cumulative with the metadata step. At most 2 attempts per
file; the run stops after 3 consecutive failures of the same class. Each file is checked (FITS readable, 1024 x 1024,
size equal to the metadata size when known), hashed, and never overwritten; files already present with a recorded
SHA-256 are kept (resume). FITS are stored outside Git (data/sharp/mdi_pilot_l2/); the manifest is in results/.

    .venv/bin/python scripts/mdi_fd_fetch.py --selftest
    .venv/bin/python scripts/mdi_fd_fetch.py --fetch      # only after review, authorisation and any amendment
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
META_DIR = ROOT / "results/MDI_PILOT_L2_METADATA"
DEST = ROOT / "data/sharp/mdi_pilot_l2"
OUT = ROOT / "results/MDI_PILOT_L2_FITS"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
MAX_ATTEMPTS, MAX_SAME_CLASS, TIMEOUT_S = 2, 3, 120
_spec = importlib.util.spec_from_file_location("mdi_l2_ledger", ROOT / "scripts/mdi_l2_ledger.py")
LG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LG)
META_PRODUCTS = {"ANSWERS.json", "CHOICES.csv", "DISCARDED.csv", "DOWNLOAD_PLAN.csv", "QUALITY_INTERVAL.csv", "ADMISSIBLE_ALTERNATIVES.csv"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def real_transport(target, dest, limit, expected, timeout):
    import mdi_hmi_patch_download as dl
    return dl.transfer_a1(target, dest, limit, expected, timeout)


def check_fits(path, expected_size):
    try:
        if expected_size and Path(path).stat().st_size != int(expected_size):
            return "size_differs_from_metadata"
        with fits.open(path) as hd:
            if hd[-1].data is None or hd[-1].data.shape != (1024, 1024):
                return "unexpected_shape"
    except Exception as exc:                                             # unreadable file
        return f"unreadable ({type(exc).__name__})"
    return "ok"


def file_name(t_rec):
    return "mdi.fd_M_96m_lev182." + str(t_rec).replace(":", "").replace(".", "") + ".data.fits"


def run(meta_dir=META_DIR, dest=DEST, out=OUT, transport=real_transport, ledger=None, verify_upstream=True):
    ledger = ledger or LG.LEDGER
    if Path(out).exists():
        sys.exit("refusing to overwrite the manifest")
    if verify_upstream:
        fr = json.loads(FREEZE.read_text())
        m = json.loads((Path(meta_dir) / "META.json").read_text())
        if sha(PROTOCOL) != fr["sha256"] or m.get("protocol_sha256") != fr["sha256"]:
            sys.exit("protocol differs")
        ps = m.get("products_sha256", {})
        if set(ps) != META_PRODUCTS or any(sha(Path(meta_dir) / n) != h for n, h in ps.items()):
            sys.exit("metadata products differ from their META")
    plan = pd.read_csv(Path(meta_dir) / "DOWNLOAD_PLAN.csv")
    Path(dest).mkdir(parents=True, exist_ok=True)
    rows, last_kind, same_kind = [], None, 0
    for r in plan.itertuples():
        f = Path(dest) / file_name(r.T_REC)
        size = int(r.size) if pd.notna(r.size) else None
        if f.exists():                                                   # resume: keep, verify, never overwrite
            st = check_fits(f, size)
            rows.append(dict(T_REC=r.T_REC, path=r.path, file=f.name, status=st if st != "ok" else "present", sha256=sha(f), bytes=f.stat().st_size, attempts=0))
            continue
        status, err, attempts = "failed", "", 0
        while attempts < MAX_ATTEMPTS:
            i, why = LG.reserve("fits", r.path, size or LG.FILE_CAP_BYTES, ledger)
            if i is None:
                rows.append(dict(T_REC=r.T_REC, path=r.path, file=f.name, status=f"not_attempted_{why.replace(' ', '_')}", attempts=attempts))
                return finish(rows, plan, meta_dir, dest, out, ledger, stopped=why)
            attempts += 1
            tmp = f.with_suffix(".part")
            if tmp.exists():
                tmp.unlink()
            try:
                nreq, final_url = transport(r.path, tmp, size or LG.FILE_CAP_BYTES, {size} if size else None, TIMEOUT_S)
                got = tmp.stat().st_size if tmp.exists() else 0
                st = check_fits(tmp, size)
                LG.finish(i, "fits", nreq, got, "ok" if st == "ok" else "partial", "" if st == "ok" else st, path=ledger)
                if st == "ok":
                    os.rename(tmp, f)
                    status, err = "ok", ""
                    last_kind, same_kind = None, 0
                    rows.append(dict(T_REC=r.T_REC, path=r.path, file=f.name, status="ok", sha256=sha(f), bytes=f.stat().st_size,
                                     attempts=attempts, final_url=final_url))
                    break
                err = st
                kind = "invalid_file"
            except Exception as exc:
                got = tmp.stat().st_size if tmp.exists() else 0
                kind = getattr(exc, "kind", type(exc).__name__)
                err = f"{kind}: {exc}"
                LG.finish(i, "fits", 2, got, "failed", err, path=ledger)
            if tmp.exists():
                tmp.unlink()
            same_kind = same_kind + 1 if kind == last_kind else 1
            last_kind = kind
            if same_kind >= MAX_SAME_CLASS:
                rows.append(dict(T_REC=r.T_REC, path=r.path, file=f.name, status="failed", error=err, attempts=attempts))
                return finish(rows, plan, meta_dir, dest, out, ledger, stopped=f"{MAX_SAME_CLASS} consecutive failures of class {kind}")
        if status != "ok":
            rows.append(dict(T_REC=r.T_REC, path=r.path, file=f.name, status="failed", error=err, attempts=attempts))
    return finish(rows, plan, meta_dir, dest, out, ledger, stopped="")


def finish(rows, plan, meta_dir, dest, out, ledger, stopped):
    man = pd.DataFrame(rows)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        man.to_csv(tmp / "MANIFEST.csv", index=False)
        meta = dict(script_sha256=sha(__file__), metadata_meta_sha256=sha(Path(meta_dir) / "META.json"), dest=str(dest),
                    planned=len(plan), done_ok=int(man.status.isin(["ok", "present"]).sum()) if len(man) else 0,
                    stopped=stopped, ledger_totals_after=LG.totals(ledger),
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {"MANIFEST.csv": sha(tmp / "MANIFEST.csv")}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps(dict(statuses=man.status.value_counts().to_dict() if len(man) else {}, stopped=stopped, ledger=LG.totals(ledger)), indent=1))
    return 0 if not stopped else 2


# ---------------------------------------------------------------- selftest (offline, fake transport)

def synthetic_fits(path, shape=(1024, 1024)):
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(np.zeros(shape, dtype=np.float32))]).writeto(path)


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    class TErr(Exception):
        def __init__(self, kind):
            super().__init__(kind)
            self.kind = kind

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        good = td / "good.fits"
        synthetic_fits(good)
        bad = td / "bad.fits"
        synthetic_fits(bad, (10, 10))
        gsize = good.stat().st_size
        md = td / "meta"
        md.mkdir()

        def plan(rows):
            pd.DataFrame(rows, columns=["T_REC", "path", "size"]).to_csv(md / "DOWNLOAD_PLAN.csv", index=False)
            (md / "META.json").write_text("{}")
        script = {}

        def fake(target, dest, limit, expected, timeout):
            act = script[target].pop(0)
            if act == "ok":
                shutil.copyfile(good, dest)
                return 2, "https://jsoc1.stanford.edu" + target
            if act == "bad":
                shutil.copyfile(bad, dest)
                return 1, "http://jsoc.stanford.edu" + target
            Path(dest).write_bytes(b"x" * 100)                          # partial body, then failure
            raise TErr(act)
        plan([("r1", "/SUM/1", gsize), ("r2", "/SUM/2", None), ("r3", "/SUM/3", gsize)])
        script.update({"/SUM/1": ["ok"], "/SUM/2": ["http_500", "ok"], "/SUM/3": ["bad", "bad"]})
        led = td / "L.jsonl"
        run(md, td / "dest", td / "out1", fake, led, verify_upstream=False)
        man = pd.read_csv(td / "out1/MANIFEST.csv").set_index("T_REC")
        ok("ok file kept with its SHA; retry after a failure; invalid file refused after 2 attempts",
           man.at["r1", "status"] == "ok" and man.at["r2", "status"] == "ok" and int(man.at["r2", "attempts"]) == 2
           and man.at["r3", "status"] == "failed" and int(man.at["r3", "attempts"]) == 2 and man.at["r1", "sha256"] == sha(td / "dest" / file_name("r1")))
        t = LG.totals(led)
        ok("ledger: every attempt counted, failed bytes included, unknown size budgeted not as zero",
           t["files"] == 2 and t["bytes"] >= 2 * gsize + 100 and t["requests"] == 2 + 2 + 2 + 1 + 1 and t["open_attempts"] == 0, t)
        ok("no partial file left in the destination", not list((td / "dest").glob("*.part")))
        script.update({"/SUM/1": [], "/SUM/2": [], "/SUM/3": ["ok"]})
        run(md, td / "dest", td / "out2", fake, led, verify_upstream=False)
        man2 = pd.read_csv(td / "out2/MANIFEST.csv").set_index("T_REC")
        ok("resume: present files verified and kept (not downloaded again), missing one fetched",
           man2.at["r1", "status"] == "present" and man2.at["r2", "status"] == "present" and man2.at["r3", "status"] == "ok")
        plan([(f"s{k}", f"/SUM/s{k}", gsize) for k in range(3)])
        script.update({f"/SUM/s{k}": ["timeout", "timeout"] for k in range(3)})
        rc = run(md, td / "dest2", td / "out3", fake, td / "L2.jsonl", verify_upstream=False)
        meta = json.loads((td / "out3/META.json").read_text())
        ok("stop after 3 consecutive failures of the same class", rc == 2 and "consecutive" in meta["stopped"], meta["stopped"])
        big = td / "L3.jsonl"
        for k in range(116):                                          # 116 x 13 MB > 1.5e9
            i, _ = LG.reserve("fits", f"/x{k}", 13_000_000, big)
            LG.finish(i, "fits", 2, 13_000_000, "ok", path=big)
        plan([("z1", "/SUM/z1", gsize)])
        script.update({"/SUM/z1": ["ok"]})
        rc = run(md, td / "dest3", td / "out4", fake, big, verify_upstream=False)
        m4 = pd.read_csv(td / "out4/MANIFEST.csv")
        ok("cumulative byte cap refuses before any request", rc == 2 and m4.status.iloc[0].startswith("not_attempted"), m4.status.iloc[0])
        try:
            run(md, td / "dest", td / "out1", fake, led, verify_upstream=False)
            ok("refuses to overwrite the manifest", False)
        except SystemExit:
            ok("refuses to overwrite the manifest", True)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
