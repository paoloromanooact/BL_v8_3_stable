"""MDI pilot, phase 4a: JSOC metadata of mdi.fd_M_96m_lev182 around the 90 level-2 groups and choice of images A and B
(frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4). NETWORK: only with the user's explicit authorisation (--fetch).

Per level-2 group: one rs_list over [t_DPD - 10 h, t_DPD + 10 h] (TAI) with T_REC, T_OBS, QUALITY, INTERVAL,
MISSVALS, the geometry and the 'data' segment. The answers are kept UNFILTERED. Choice from metadata only, with the
frozen admissible set QUALITY in {0}:
  A = admissible record with T_OBS (UTC, fractional seconds kept) closest to t_DPD within +-6 h; ties -> earliest.
  B = first admissible record after A with numeric INTERVAL equal to A's within 4 h; else the first before A with the
      same conditions; else 'no_pair'. A missing INTERVAL never forms a pair.
For the decision on a possible blind amendment (before any FITS), the script also reports, WITHOUT changing groups or
days: QUALITY x INTERVAL composition by year, cell and cohort, and the counts of A and of A/B pairs obtainable with the
frozen set {0} and with {0, 0x200}. Only the frozen choice feeds the download plan.
Every request is recorded in the shared cumulative ledger (scripts/mdi_l2_ledger.py) before its outcome is used.

    .venv/bin/python scripts/mdi_fd_metadata.py --selftest
    .venv/bin/python scripts/mdi_fd_metadata.py --fetch      # only after code review AND user authorisation
"""
import argparse
import hashlib
import http.client
import importlib.util
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
FROZEN_ADMISSIBLE = (0,)
ALTERNATIVE_ADMISSIBLE = (0, 0x200)
HOST, PATH = "jsoc.stanford.edu", "/cgi-bin/ajax/jsoc_info"
_spec = importlib.util.spec_from_file_location("mdi_l2_ledger", ROOT / "scripts/mdi_l2_ledger.py")
LG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LG)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def tai_string(t_utc):
    t = Time(pd.Timestamp(t_utc).to_pydatetime(), scale="utc").tai.to_datetime()
    return t.strftime("%Y.%m.%d_%H:%M:%S_TAI")


def jsoc_to_utc(s):
    """'YYYY.MM.DD_hh:mm:ss[.fff][_TAI]' -> UTC Timestamp; fractional seconds kept; seconds = 60 as an interval;
    a string without '_TAI' is taken as UTC; None if unparsable."""
    try:
        s = str(s)
        d = s[:10].split(".")
        hh, mm, ss = s[11:].split("_")[0].split(":")
        t = pd.Timestamp(int(d[0]), int(d[1]), int(d[2]), int(hh), int(mm)) + timedelta(seconds=float(ss))
    except (ValueError, IndexError, TypeError):
        return None
    if s.endswith("_TAI"):
        return pd.Timestamp(Time(t.to_pydatetime(), scale="tai").utc.to_datetime())
    return t


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
    if doc.get("status") != 0:
        raise ValueError(f"rs_list status {doc.get('status')}")
    cols = {k["name"]: k["values"] for k in doc["keywords"]}
    n = int(doc.get("count", 0))
    if any(len(v) != n for v in cols.values()):
        raise ValueError("keyword lengths")
    seg = doc.get("segments") or []
    t = pd.DataFrame(cols).assign(path=seg[0]["values"] if seg else [None] * n)
    t["t_obs_utc"] = [jsoc_to_utc(x) for x in t.T_OBS]
    t["quality_int"] = [parse_quality(x) for x in t.QUALITY]
    t["interval_s"] = [parse_interval(x) for x in (t.INTERVAL if "INTERVAL" in t else [None] * n)]
    return t


def choose(t, t_dpd, admissible=FROZEN_ADMISSIBLE):
    """Choice of A and B for one group. Returns (choice dict, discarded records with their cause)."""
    t_dpd = pd.Timestamp(t_dpd)
    t = t.copy()
    t["dt_h"] = [(x - t_dpd).total_seconds() / 3600.0 if x is not None else np.nan for x in t.t_obs_utc]
    t["reason"] = np.where(t.t_obs_utc.isna(), "t_obs_unparsable",
                           np.where(~t.quality_int.isin(admissible), "quality_not_admissible",
                                    np.where(t.path.isna() | ~t.path.astype(str).str.startswith("/SUM"), "no_data_segment", "")))
    adm = t[t.reason == ""]
    out = dict(status="no_magnetogram", A=None, B=None, A_path=None, B_path=None, A_size=None, B_size=None, A_dt_h=np.nan, B_dt_h=np.nan,
               pair_dt_min=np.nan, A_interval=None, A_quality=None, pair_status="no_pair")
    near = adm[adm.dt_h.abs() <= A_WINDOW_H]
    if near.empty:
        return out, t[t.reason != ""]
    a = near.assign(_a=near.dt_h.abs()).sort_values(["_a", "t_obs_utc"], kind="stable").iloc[0]
    out.update(status="ok", A=a.T_REC, A_path=a.path, A_dt_h=a.dt_h, A_interval=a.interval_s, A_size=a.get("*size*"), A_quality=a.quality_int)
    if a.interval_s is None:
        out["pair_status"] = "no_pair_interval_unknown"
        return out, t[t.reason != ""]
    same = adm[(adm.interval_s == a.interval_s) & (adm.T_REC != a.T_REC)]
    cand = same.assign(_dt=(same.t_obs_utc - a.t_obs_utc).dt.total_seconds() / 3600.0)
    after = cand[(cand._dt > 0) & (cand._dt <= B_WINDOW_H)].sort_values(["_dt", "t_obs_utc"], kind="stable")
    before = cand[(cand._dt < 0) & (cand._dt >= -B_WINDOW_H)].assign(_a=lambda x: -x._dt).sort_values(["_a", "t_obs_utc"], kind="stable")
    b = after.iloc[0] if len(after) else (before.iloc[0] if len(before) else None)
    if b is not None:
        out.update(B=b.T_REC, B_path=b.path, B_dt_h=(b.t_obs_utc - t_dpd).total_seconds() / 3600.0,
                   pair_dt_min=(b.t_obs_utc - a.t_obs_utc).total_seconds() / 60.0, pair_status="after" if len(after) else "before",
                   B_size=b.get("*size*"))
    return out, t[t.reason != ""]


def size_or_none(x):
    try:
        v = int(str(x))
        return v if v > 0 else None
    except (ValueError, TypeError):
        return None


def plan(choices):
    """Deduplicated download plan of the A and B data segments (frozen choice only); unknown sizes kept as unknown."""
    rows = [dict(T_REC=c[k], path=c[f"{k}_path"], size=size_or_none(c.get(f"{k}_size"))) for c in choices for k in ("A", "B")
            if c.get(f"{k}_path")]
    p = pd.DataFrame(rows, columns=["T_REC", "path", "size"]).drop_duplicates("path").reset_index(drop=True)
    return p


def composition(recs):
    """QUALITY x INTERVAL counts by year, cell and cohort, inside +-10 h and inside the A window +-6 h."""
    r = recs.assign(quality=recs.quality_int.map(lambda q: f"0x{q:08x}" if q is not None and q == q else "unparsable"),
                    interval=recs.interval_s.map(lambda v: "missing" if v is None or v != v else f"{v:g}"),
                    in_a_window=recs.dt_h.abs() <= A_WINDOW_H)
    keys = ["year", "act_class", "hemisphere", "area_class", "cohort", "quality", "interval"]
    allw = r.groupby(keys).size().rename("n_records_10h")
    aw = r[r.in_a_window].groupby(keys).size().rename("n_records_6h")
    return pd.concat([allw, aw], axis=1).fillna(0).astype(int).reset_index()


def alternative_counts(per_group):
    """Per cell x cohort: groups with an A and with an A/B pair under the frozen set and under {0, 0x200}."""
    rows = []
    for keys, g in per_group.groupby(["act_class", "hemisphere", "area_class", "cohort"]):
        r = dict(zip(["act_class", "hemisphere", "area_class", "cohort"], keys), n_groups=len(g))
        for tag in ("frozen", "alt"):
            r[f"A_{tag}"] = int((g[f"status_{tag}"] == "ok").sum())
            r[f"pair_{tag}"] = int(g[f"pair_{tag}"].isin(["after", "before"]).sum())
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- network (only with --fetch)

def http_json(query, timeout=30):
    """Plain HTTP GET of jsoc_info (no redirect followed). Returns (doc, bytes, requests)."""
    conn = http.client.HTTPConnection(HOST, 80, timeout=timeout)
    try:
        conn.request("GET", PATH + "?" + urlencode(query), headers={"Accept-Encoding": "identity"})
        res = conn.getresponse()
        body = res.read(5_000_000)
        if res.status != 200:
            raise ValueError(f"HTTP {res.status} ({len(body)} bytes)")
        return json.loads(body), len(body), 1
    finally:
        conn.close()


def fetch(out=OUT, transport=http_json, ledger=None):
    ledger = ledger or LG.LEDGER
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    choices, groups, discarded, recs_all, answers = [], [], [], [], {}
    for r in l2.itertuples():
        t0 = pd.Timestamp(r.t_dpd)
        half = pd.Timedelta(hours=A_WINDOW_H + B_WINDOW_H)                  # symmetric: B may precede A by 4 h
        ds = f"{SERIES}[{tai_string(t0 - half)}-{tai_string(t0 + half)}]"
        okc, why = LG.can_start("metadata", 0, ledger)
        if not okc:
            sys.exit(f"ledger cap reached before {r.noaa} {r.day}: {why}")
        i = LG.start("metadata", ds, ledger)
        try:
            doc, nbytes, nreq = transport(dict(op="rs_list", ds=ds, key=",".join(KEYWORDS), seg="data"))
            LG.finish(i, "metadata", nreq, nbytes, "ok", path=ledger)
        except Exception as exc:                                         # recorded, never retried silently
            LG.finish(i, "metadata", 1, 0, "failed", f"{type(exc).__name__}: {exc}", path=ledger)
            choices.append(dict(noaa=r.noaa, day=r.day, t_dpd=r.t_dpd, status="metadata_failed", error=f"{type(exc).__name__}: {exc}"))
            continue
        answers[f"{r.noaa}_{r.day}"] = doc
        t = records_from_answer(doc)
        c, disc = choose(t, r.t_dpd, FROZEN_ADMISSIBLE)
        c_alt, _ = choose(t, r.t_dpd, ALTERNATIVE_ADMISSIBLE)
        choices.append(dict(noaa=r.noaa, day=r.day, t_dpd=r.t_dpd, n_records=len(t), **c))
        cls = dict(act_class=r.act_class, hemisphere=r.hemisphere, area_class=r.area_class, cohort=r.cohort, year=str(r.day)[:4])
        groups.append(dict(noaa=r.noaa, day=r.day, **cls, status_frozen=c["status"], pair_frozen=c["pair_status"],
                           status_alt=c_alt["status"], pair_alt=c_alt["pair_status"]))
        tt = t.assign(dt_h=[(x - t0).total_seconds() / 3600.0 if x is not None else np.nan for x in t.t_obs_utc])
        recs_all.append(tt.assign(noaa=r.noaa, day=r.day, **cls))
        discarded.append(disc.assign(noaa=r.noaa, day=r.day))
    ch = pd.DataFrame(choices)
    pl = plan([c for c in choices if c.get("status") == "ok"])
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        (tmp / "ANSWERS.json").write_text(json.dumps(answers) + "\n")
        ch.to_csv(tmp / "CHOICES.csv", index=False)
        (pd.concat(discarded) if discarded else pd.DataFrame()).to_csv(tmp / "DISCARDED.csv", index=False)
        pl.to_csv(tmp / "DOWNLOAD_PLAN.csv", index=False)
        if recs_all:
            composition(pd.concat(recs_all)).to_csv(tmp / "QUALITY_INTERVAL.csv", index=False)
            alternative_counts(pd.DataFrame(groups)).to_csv(tmp / "ADMISSIBLE_ALTERNATIVES.csv", index=False)
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), ledger_module_sha256=sha(ROOT / "scripts/mdi_l2_ledger.py"),
                    selection_meta_sha256=sha(SEL / "META.json"), ledger_totals_after=LG.totals(ledger),
                    planned_files=len(pl), planned_bytes_known=int(pl["size"].dropna().sum()) if len(pl) else 0,
                    planned_files_size_unknown=int(pl["size"].isna().sum()) if len(pl) else 0,
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps(dict(ledger=LG.totals(ledger), statuses=ch.status.value_counts().to_dict(), planned_files=len(pl)), indent=1))
    return 0


# ---------------------------------------------------------------- selftest (offline)

def answer(rows):
    keys = list(rows[0])
    return dict(status=0, count=len(rows), keywords=[dict(name=k, values=[r[k] for r in rows]) for k in keys if k != "path"],
                segments=[dict(name="data", values=[r["path"] for r in rows])])


def rec(trec, tobs, q="0x00000000", interval="300", path="/SUM1/D1/S0/data.fits", size="2000000"):
    return {"T_REC": trec, "T_OBS": tobs, "QUALITY": q, "INTERVAL": interval, "MISSVALS": "0", "*size*": size, "path": path}


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    ok("TAI -> UTC (32 s in 2000), seconds = 60 as an interval, fractional seconds kept, UTC string kept",
       jsoc_to_utc("2000.01.01_00:00:32_TAI") == pd.Timestamp("2000-01-01 00:00:00")
       and jsoc_to_utc("2000.01.01_00:00:60_TAI") == pd.Timestamp("2000-01-01 00:00:28")
       and jsoc_to_utc("2000.01.01_00:00:32.75_TAI") == pd.Timestamp("2000-01-01 00:00:00.75")
       and jsoc_to_utc("2000.01.01_00:00:05.5") == pd.Timestamp("2000-01-01 00:00:05.5"))
    ok("QUALITY parsed from hex strings", parse_quality("0x00000200") == 512 and parse_quality("0x00000000") == 0)
    t_dpd = pd.Timestamp("2000-06-01 10:00:00")
    base = [rec("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", path="/SUM1/a"),
            rec("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00_TAI", path="/SUM1/b"),
            rec("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", path="/SUM1/c"),
            rec("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", path="/SUM1/d", interval="30")]
    c, _ = choose(records_from_answer(answer(base)), t_dpd)
    ok("A closest to t_DPD; B first after with the same INTERVAL", c["A"] == "2000.06.01_09:36:00_TAI" and c["B"] == "2000.06.01_11:12:00_TAI"
       and c["pair_status"] == "after")
    q = [dict(r, QUALITY="0x00000200") if r["path"] == "/SUM1/b" else r for r in base]
    c, disc = choose(records_from_answer(answer(q)), t_dpd)
    c2, _ = choose(records_from_answer(answer(q)), t_dpd, ALTERNATIVE_ADMISSIBLE)
    ok("QUALITY 0x200 discarded under the frozen set, admitted under {0, 0x200} (counts only)", c["A"] == "2000.06.01_11:12:00_TAI"
       and (disc.reason == "quality_not_admissible").sum() == 1 and c2["A"] == "2000.06.01_09:36:00_TAI")
    nob = [dict(r, INTERVAL="30") if r["path"] == "/SUM1/c" else r for r in base]
    c, _ = choose(records_from_answer(answer(nob)), t_dpd)
    ok("B before A when no later record has the same INTERVAL", c["B"] == "2000.06.01_08:00:00_TAI" and c["pair_status"] == "before")
    edge = [rec("2000.06.01_04:00:00_TAI", "2000.06.01_04:00:32_TAI", path="/SUM2/a"),          # A at exactly -6 h
            rec("2000.06.01_00:00:00_TAI", "2000.06.01_00:00:32_TAI", path="/SUM2/b")]          # B at -10 h (4 h before A)
    c, _ = choose(records_from_answer(answer(edge)), t_dpd)
    ok("edges: A at exactly -6 h accepted, B exactly 4 h before A (t_DPD - 10 h) accepted", c["A"] == "2000.06.01_04:00:00_TAI"
       and c["B"] == "2000.06.01_00:00:00_TAI", (c["A"], c["B"]))
    out6 = [rec("2000.06.01_03:59:00_TAI", "2000.06.01_03:59:31_TAI", path="/SUM2/c")]
    c, _ = choose(records_from_answer(answer(out6)), t_dpd)
    ok("edge: A 1 s beyond 6 h refused", c["status"] == "no_magnetogram")
    none = [dict(r, INTERVAL="30") for r in base if r["path"] != "/SUM1/b"] + [r for r in base if r["path"] == "/SUM1/b"]
    c, _ = choose(records_from_answer(answer(none)), t_dpd)
    ok("no other record with the same INTERVAL within 4 h -> no_pair, no phantom row", c["B"] is None and c["pair_status"] == "no_pair")
    miss = [dict(r, INTERVAL="MISSING") for r in base]
    c, _ = choose(records_from_answer(answer(miss)), t_dpd)
    ok("missing INTERVAL: A kept, no repeatability pair", c["status"] == "ok" and c["pair_status"] == "no_pair_interval_unknown")
    tie = [rec("2000.06.01_09:00:00_TAI", "2000.06.01_09:00:32_TAI", path="/SUM9/x"), rec("2000.06.01_11:00:00_TAI", "2000.06.01_11:00:32_TAI", path="/SUM9/y")]
    c, _ = choose(records_from_answer(answer(tie)), t_dpd)
    ok("tie at equal distance -> earliest", c["A"] == "2000.06.01_09:00:00_TAI")
    p = plan([dict(A="r1", A_path="/p1", A_size="1", B="r2", B_path="/p2", B_size="MISSING"), dict(A="r2", A_path="/p2", A_size="1")])
    ok("download plan deduplicated; unknown size kept as unknown, not zero", len(p) == 2 and p["size"].isna().sum() == 1)
    with tempfile.TemporaryDirectory() as td:
        g = globals()
        saved = g["SEL"]
        try:
            g["SEL"] = Path(td)
            pd.DataFrame(dict(noaa=["1", "2"], day=["2000-06-01", "2000-06-01"], t_dpd=["2000-06-01 10:00:00", "2000-06-01 10:00:00"],
                              level2=[True, True], act_class=[1, 2], hemisphere=["N", "S"], area_class=[1, 3], cohort=["M1", "U"])).to_csv(Path(td) / "SAMPLE.csv", index=False)
            (Path(td) / "META.json").write_text("{}")
            calls = {"n": 0}

            def fake(qy, timeout=30):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise ConnectionError("offline test failure")
                return answer([dict(r, QUALITY="0x00000200") for r in base]), 1234, 1
            led = Path(td) / "LEDGER.jsonl"
            fetch(Path(td) / "out", transport=fake, ledger=led)
            ch = pd.read_csv(Path(td) / "out/CHOICES.csv")
            alt = pd.read_csv(Path(td) / "out/ADMISSIBLE_ALTERNATIVES.csv")
            qi = pd.read_csv(Path(td) / "out/QUALITY_INTERVAL.csv")
            tot = LG.totals(led)
        finally:
            g["SEL"] = saved
        ok("offline fetch: failure recorded and not retried; ledger counts both requests and the bytes received",
           calls["n"] == 2 and list(ch.status) == ["metadata_failed", "no_magnetogram"] and tot["requests"] == 2 and tot["bytes"] == 1234)
        ok("alternative counts and QUALITY x INTERVAL composition reported without changing the frozen choice",
           int(alt.A_frozen.sum()) == 0 and int(alt.A_alt.sum()) == 1 and set(qi.quality) == {"0x00000200"} and int(qi.n_records_10h.sum()) == 4)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else fetch())
