"""MDI pilot, phase 4a: JSOC metadata of mdi.fd_M_96m_lev182 around the level-2 groups and choice of images A and B
(frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4). NETWORK: only with the user's explicit authorisation (--fetch).

Per level-2 group: one rs_list over [t_DPD - 6 h, t_DPD + 10 h] (TAI) with the keywords T_REC, T_OBS, QUALITY,
INTERVAL, MISSVALS and the geometry, plus the 'data' segment (path, size, online). Choice from metadata only:
  A = admissible record (QUALITY == 0) with T_OBS (UTC) closest to t_DPD within +-6 h; ties -> earliest; none -> 'no_magnetogram'.
  B = first admissible record after A with numeric INTERVAL equal to A's within 4 h; else the first before A with the
      same conditions; else 'no_pair'. A missing INTERVAL never forms a pair (A with unknown mode stays usable for Q2).
Discarded records and their causes are kept. No image is searched after a measurement failure.
Budget ledger: metadata requests count towards the shared level-2 caps (<= 600 requests, <= 220 files, <= 1.5 GB).

    .venv/bin/python scripts/mdi_fd_metadata.py --selftest
    .venv/bin/python scripts/mdi_fd_metadata.py --fetch      # only after code review AND user authorisation
"""
import argparse
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

import numpy as np
import pandas as pd
from astropy.time import Time

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
OUT = ROOT / "results/MDI_PILOT_L2_METADATA"
SERIES = "mdi.fd_M_96m_lev182"
KEYWORDS = ("T_REC", "T_OBS", "QUALITY", "INTERVAL", "MISSVALS", "CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CROTA2",
            "RSUN_OBS", "CRLT_OBS", "CRLN_OBS", "*size*", "*online*")
A_WINDOW_H, B_WINDOW_H = 6.0, 4.0
CAP_REQUESTS, CAP_FILES, CAP_BYTES = 600, 220, int(1.5e9)
HOST, PATH = "jsoc.stanford.edu", "/cgi-bin/ajax/jsoc_info"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tai_string(t_utc):
    t = Time(pd.Timestamp(t_utc).to_pydatetime(), scale="utc").tai.to_datetime()
    return t.strftime("%Y.%m.%d_%H:%M:%S_TAI")


def jsoc_to_utc(s):
    """'YYYY.MM.DD_hh:mm:ss[.f]_TAI' -> UTC Timestamp; seconds = 60 as an interval; None if unparsable."""
    try:
        d, h = s[:10].split("."), s[11:19].split(":")
        t = pd.Timestamp(int(d[0]), int(d[1]), int(d[2]), int(h[0]), int(h[1])) + timedelta(seconds=int(h[2]))
    except (ValueError, IndexError, TypeError):
        return None
    return pd.Timestamp(Time(t.to_pydatetime(), scale="tai").utc.to_datetime()) if str(s).endswith("_TAI") else t


def parse_quality(q):
    try:
        return int(str(q), 16) if str(q).lower().startswith("0x") else int(q)
    except (ValueError, TypeError):
        return None


def parse_interval(v):
    try:
        x = float(v)
    except (ValueError, TypeError):
        return None
    return x if np.isfinite(x) and x > 0 else None


def records_from_answer(doc):
    """rs_list JSON -> DataFrame of records (one row per record) with parsed T_OBS (UTC), QUALITY, INTERVAL."""
    if doc.get("status") != 0:
        raise ValueError(f"rs_list status {doc.get('status')}")
    cols = {k["name"]: k["values"] for k in doc["keywords"]}
    n = int(doc.get("count", 0))
    if any(len(v) != n for v in cols.values()):
        raise ValueError("keyword lengths")
    seg = doc.get("segments") or []
    path = seg[0]["values"] if seg else [None] * n
    t = pd.DataFrame(cols).assign(path=path)
    t["t_obs_utc"] = [jsoc_to_utc(x) for x in t.T_OBS]
    t["quality_int"] = [parse_quality(x) for x in t.QUALITY]
    t["interval_s"] = [parse_interval(x) for x in t.get("INTERVAL", [None] * n)]
    return t


def choose(t, t_dpd):
    """Choice of A and B from the records of one group. Returns (choice dict, discarded DataFrame)."""
    t_dpd = pd.Timestamp(t_dpd)
    t = t.copy()
    t["dt_h"] = [(x - t_dpd).total_seconds() / 3600.0 if x is not None else np.nan for x in t.t_obs_utc]
    reason = np.where(t.t_obs_utc.isna(), "t_obs_unparsable",
                      np.where(t.quality_int != 0, "quality_not_zero",
                               np.where(t.path.isna() | ~t.path.astype(str).str.startswith("/SUM"), "no_data_segment", "")))
    t["reason"] = reason
    adm = t[t.reason == ""]
    near = adm[adm.dt_h.abs() <= A_WINDOW_H]
    out = dict(status="no_magnetogram", A=None, B=None, A_dt_h=np.nan, B_dt_h=np.nan, pair_dt_min=np.nan, A_interval=None, pair_status="no_pair")
    if near.empty:
        return out, t[t.reason != ""]
    near = near.assign(_a=near.dt_h.abs()).sort_values(["_a", "t_obs_utc"], kind="stable")
    a = near.iloc[0]
    out.update(status="ok", A=a.T_REC, A_path=a.path, A_dt_h=a.dt_h, A_interval=a.interval_s, A_size=a.get("*size*"))
    if a.interval_s is None:
        out["pair_status"] = "no_pair_interval_unknown"
        return out, t[t.reason != ""]
    same = adm[(adm.interval_s == a.interval_s) & (adm.T_REC != a.T_REC)]
    cand = same.assign(_dt=(same.t_obs_utc - a.t_obs_utc).dt.total_seconds() / 3600.0)   # distance computed before filtering
    after = cand[(cand._dt > 0) & (cand._dt <= B_WINDOW_H)].sort_values(["_dt", "t_obs_utc"], kind="stable")
    before = cand[(cand._dt < 0) & (cand._dt >= -B_WINDOW_H)].assign(_a=lambda x: -x._dt).sort_values(["_a", "t_obs_utc"], kind="stable")
    b = after.iloc[0] if len(after) else (before.iloc[0] if len(before) else None)
    if b is not None:
        out.update(B=b.T_REC, B_path=b.path, B_dt_h=(b.t_obs_utc - t_dpd).total_seconds() / 3600.0,
                   pair_dt_min=(b.t_obs_utc - a.t_obs_utc).total_seconds() / 60.0, pair_status="after" if len(after) else "before",
                   B_size=b.get("*size*"))
    return out, t[t.reason != ""]


def plan(choices):
    """Deduplicated download plan of the A and B data segments."""
    rows = []
    for c in choices:
        for k in ("A", "B"):
            if c.get(f"{k}_path"):
                rows.append(dict(T_REC=c[k], path=c[f"{k}_path"], size=c.get(f"{k}_size")))
    p = pd.DataFrame(rows).drop_duplicates("path") if rows else pd.DataFrame(columns=["T_REC", "path", "size"])
    return p.reset_index(drop=True)


# ---------------------------------------------------------------- network (only with --fetch)

def http_json(query, timeout=30):
    conn = http.client.HTTPConnection(HOST, 80, timeout=timeout)
    try:
        conn.request("GET", PATH + "?" + urlencode(query), headers={"Accept-Encoding": "identity"})
        res = conn.getresponse()
        body = res.read(5_000_000)
        if res.status != 200:
            raise ValueError(f"HTTP {res.status}")
        return json.loads(body), len(body)
    finally:
        conn.close()


def fetch(out=OUT, transport=http_json):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2].reset_index(drop=True)
    ledger = dict(requests=0, bytes=0, failures=0)
    choices, discarded, answers = [], [], {}
    for r in l2.itertuples():
        t0 = pd.Timestamp(r.t_dpd)
        ds = f"{SERIES}[{tai_string(t0 - pd.Timedelta(hours=A_WINDOW_H))}-{tai_string(t0 + pd.Timedelta(hours=A_WINDOW_H + B_WINDOW_H))}]"
        if ledger["requests"] >= CAP_REQUESTS:
            sys.exit("request cap reached")
        ledger["requests"] += 1
        try:
            doc, nbytes = transport(dict(op="rs_list", ds=ds, key=",".join(KEYWORDS), seg="data"))
            ledger["bytes"] += nbytes
        except Exception as exc:                                       # recorded, never retried silently
            ledger["failures"] += 1
            choices.append(dict(noaa=r.noaa, day=r.day, status="metadata_failed", error=f"{type(exc).__name__}: {exc}"))
            continue
        answers[f"{r.noaa}_{r.day}"] = doc
        t = records_from_answer(doc)
        c, disc = choose(t, r.t_dpd)
        choices.append(dict(noaa=r.noaa, day=r.day, t_dpd=r.t_dpd, n_records=len(t), **c))
        discarded.append(disc.assign(noaa=r.noaa, day=r.day))
    ch = pd.DataFrame(choices)
    pl = plan(choices)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        (tmp / "ANSWERS.json").write_text(json.dumps(answers) + "\n")
        ch.to_csv(tmp / "CHOICES.csv", index=False)
        (pd.concat(discarded) if discarded else pd.DataFrame()).to_csv(tmp / "DISCARDED.csv", index=False)
        pl.to_csv(tmp / "DOWNLOAD_PLAN.csv", index=False)
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), selection_meta_sha256=sha(SEL / "META.json"),
                    ledger=ledger, planned_files=len(pl), planned_bytes=float(pd.to_numeric(pl["size"], errors="coerce").sum()),
                    caps=dict(requests=CAP_REQUESTS, files=CAP_FILES, bytes=CAP_BYTES),
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps(dict(ledger=ledger, statuses=ch.status.value_counts().to_dict(), planned_files=len(pl)), indent=1))
    return 0


# ---------------------------------------------------------------- selftest (offline: recorded and synthetic answers)

def answer(rows):
    keys = list(rows[0])
    return dict(status=0, count=len(rows), keywords=[dict(name=k, values=[r[k] for r in rows]) for k in keys if k != "path"],
                segments=[dict(name="data", values=[r["path"] for r in rows])])


def rec(trec, tobs, q="0x00000000", interval="300", path="/SUM1/D1/S0/data.fits"):
    return {"T_REC": trec, "T_OBS": tobs, "QUALITY": q, "INTERVAL": interval, "MISSVALS": "0", "*size*": "2000000", "path": path}


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    ok("TAI -> UTC (32 s in 2000) and seconds = 60 as an interval",
       jsoc_to_utc("2000.01.01_00:00:32_TAI") == pd.Timestamp("2000-01-01 00:00:00")
       and jsoc_to_utc("2000.01.01_00:00:60_TAI") == pd.Timestamp("2000-01-01 00:00:28"))
    ok("QUALITY parsed from hex strings", parse_quality("0x00000200") == 512 and parse_quality("0x00000000") == 0)
    t_dpd = pd.Timestamp("2000-06-01 10:00:00")
    base = [rec("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", path="/SUM1/a"),
            rec("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00_TAI", path="/SUM1/b"),
            rec("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", path="/SUM1/c"),
            rec("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", path="/SUM1/d", interval="30")]
    c, disc = choose(records_from_answer(answer(base)), t_dpd)
    ok("A = admissible record with T_OBS closest to t_DPD; B = first after with the same INTERVAL",
       c["A"] == "2000.06.01_09:36:00_TAI" and c["B"] == "2000.06.01_11:12:00_TAI" and c["pair_status"] == "after", (c["A"], c["B"]))
    q = [dict(r, QUALITY="0x00000200") if r["path"] == "/SUM1/b" else r for r in base]
    c, disc = choose(records_from_answer(answer(q)), t_dpd)
    ok("QUALITY != 0 discarded with its cause; A moves to the next admissible", c["A"] == "2000.06.01_11:12:00_TAI"
       and (disc.reason == "quality_not_zero").sum() == 1)
    nob = [dict(r, INTERVAL="30") if r["path"] == "/SUM1/c" else r for r in base]
    c, _ = choose(records_from_answer(answer(nob)), t_dpd)
    ok("B before A when no later record has the same INTERVAL", c["B"] == "2000.06.01_08:00:00_TAI" and c["pair_status"] == "before", (c["B"], c["pair_status"]))
    none = [dict(r, INTERVAL="30") for r in base if r["path"] != "/SUM1/b"] + [r for r in base if r["path"] == "/SUM1/b"]
    c, _ = choose(records_from_answer(answer(none)), t_dpd)
    ok("no other record with the same INTERVAL within 4 h -> no_pair, no phantom row", c["B"] is None and c["pair_status"] == "no_pair", (c["B"], c["pair_status"]))
    nonadm = [rec("2000.06.01_09:00:00_TAI", "2000.06.01_09:00:32_TAI", path="/x")]
    c, d2 = choose(records_from_answer(answer(nonadm)), t_dpd)
    ok("a record without a /SUM data path is discarded with its cause", c["status"] == "no_magnetogram" and (d2.reason == "no_data_segment").all())
    miss = [dict(r, INTERVAL="MISSING") for r in base]
    c, _ = choose(records_from_answer(answer(miss)), t_dpd)
    ok("missing INTERVAL: A kept, no repeatability pair", c["status"] == "ok" and c["pair_status"] == "no_pair_interval_unknown" and c["B"] is None)
    far = [rec("2000.06.01_18:00:00_TAI", "2000.06.01_18:01:00_TAI")]
    c, _ = choose(records_from_answer(answer(far)), t_dpd)
    ok("no admissible record within 6 h -> no_magnetogram (no search elsewhere)", c["status"] == "no_magnetogram")
    tie = [rec("2000.06.01_09:00:00_TAI", "2000.06.01_09:00:32_TAI", path="/SUM9/x"), rec("2000.06.01_11:00:00_TAI", "2000.06.01_11:00:32_TAI", path="/SUM9/y")]
    c, _ = choose(records_from_answer(answer(tie)), t_dpd)
    ok("tie at equal distance -> earliest", c["A"] == "2000.06.01_09:00:00_TAI")
    p = plan([dict(A="r1", A_path="/p1", A_size="1", B="r2", B_path="/p2", B_size="1"), dict(A="r2", A_path="/p2", A_size="1")])
    ok("download plan deduplicated", len(p) == 2)
    led = {"n": 0}

    def fake(q, timeout=30):
        led["n"] += 1
        raise ConnectionError("offline test")
    try:
        with tempfile.TemporaryDirectory() as td:
            g = globals()
            saved = g["SEL"]
            g["SEL"] = Path(td)
            pd.DataFrame(dict(noaa=["1", "2"], day=["2000-06-01", "2000-06-02"], t_dpd=["2000-06-01 10:00:00", "2000-06-02 10:00:00"],
                              level2=[True, True])).to_csv(Path(td) / "SAMPLE.csv", index=False)
            (Path(td) / "META.json").write_text("{}")
            fetch(Path(td) / "out", transport=fake)
            ch = pd.read_csv(Path(td) / "out/CHOICES.csv")
            g["SEL"] = saved
        ok("transport failures recorded per group, never retried silently, ledger counts them",
           led["n"] == 2 and (ch.status == "metadata_failed").all())
    except SystemExit as e:
        ok("offline fetch with a failing transport", False, e)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else fetch())
