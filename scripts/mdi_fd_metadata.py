"""MDI pilot, phase 4a: JSOC metadata of mdi.fd_M_96m_lev182 around the 90 level-2 groups and choice of images A and B
(frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4). NETWORK: only with the user's explicit authorisation (--fetch).

Before any request: strict provenance gate (frozen protocol, selection products and their hashes, strict selection
receipt bound to the selection META, protocol of the selection, unique level-2 units equal in number to the cells'
n2, clean tracked tree on the real path). The whole run holds the ledger RunLock; each request reserves its budget
atomically (5 MB) and the actual bytes received are recorded also when the request fails (HTTP status, read or JSON).

Per level-2 group: one rs_list over [t_DPD - 10 h, t_DPD + 10 h] (TAI). Answers and per-group outcomes are written
progressively (ANSWERS.jsonl) before any derived product. Choice from metadata only, frozen admissible QUALITY {0}:
  A = admissible record with T_OBS (UTC, fractional seconds kept) closest to t_DPD within +-6 h; ties -> earliest.
  B = first admissible record after A with numeric INTERVAL equal to A's within 4 h; else the first before A with the
      same conditions; else 'no_pair'. A missing / unparsable INTERVAL (None or NaN) never forms a pair.
  QUALITY missing or not interpretable is NOT zero: such a record is not admissible (cause recorded).
Decision material for a possible blind amendment (without changing groups or days): QUALITY x INTERVAL composition and
counts of A and A/B pairs under {0} and under {0, 0x200}, for ALL selected groups: a failed request is 'not
determined', kept in the denominators and never counted as evidence for either rule. Only the frozen choice feeds the
download plan. All products are always written with complete schemas and an explicit completeness state.

    .venv/bin/python scripts/mdi_fd_metadata.py --selftest
    .venv/bin/python scripts/mdi_fd_metadata.py --fetch      # only after code review AND user authorisation
"""
import argparse
import hashlib
import http.client
import importlib.util
import json
import math
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
CLS = ["act_class", "hemisphere", "area_class", "cohort"]
CHOICE_COLS = ["noaa", "day", "t_dpd", "request_status", "n_records", "status", "A", "A_path", "A_size", "A_dt_h", "A_quality",
               "A_interval", "B", "B_path", "B_size", "B_dt_h", "pair_dt_min", "pair_status", "error"]
GROUP_COLS = ["noaa", "day", "year"] + CLS + ["request_status", "status_frozen", "pair_frozen", "status_alt", "pair_alt"]
COMP_COLS = ["year"] + CLS + ["quality", "interval", "n_records_10h", "n_records_6h"]
ALT_COLS = CLS + ["n_groups", "n_requests_ok", "n_not_determined", "A_frozen", "pair_frozen", "A_alt", "pair_alt"]
PLAN_COLS = ["T_REC", "path", "size"]
DISC_COLS = ["noaa", "day", "T_REC", "T_OBS", "QUALITY", "INTERVAL", "reason"]
_spec = importlib.util.spec_from_file_location("mdi_l2_ledger", ROOT / "scripts/mdi_l2_ledger.py")
LG = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LG)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


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
    """(value or None, state) with state in ok / missing / unparsable; a missing QUALITY is never zero."""
    if missing(q) or str(q).strip() in ("", "MISSING", "nan", "None"):
        return None, "missing"
    try:
        s = str(q).strip()
        return (int(s, 16) if s.lower().startswith("0x") else int(s)), "ok"
    except (ValueError, TypeError):
        return None, "unparsable"


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
    for c in ("T_REC", "T_OBS", "QUALITY", "INTERVAL"):
        if c not in t:
            t[c] = None
    t["t_obs_utc"] = [jsoc_to_utc(x) for x in t.T_OBS]
    q = [parse_quality(x) for x in t.QUALITY]
    t["quality_int"] = pd.array([v for v, _ in q], dtype="Int64")
    t["quality_state"] = [s for _, s in q]
    t["interval_s"] = pd.array([parse_interval(x) for x in t.INTERVAL], dtype="Float64")
    return t


def choose(t, t_dpd, admissible=FROZEN_ADMISSIBLE):
    t_dpd = pd.Timestamp(t_dpd)
    t = t.copy()
    t["dt_h"] = [(x - t_dpd).total_seconds() / 3600.0 if x is not None else np.nan for x in t.t_obs_utc]
    adm_q = [st == "ok" and int(v) in admissible for v, st in zip(t.quality_int, t.quality_state)]
    t["reason"] = np.where(t.t_obs_utc.isna(), "t_obs_unparsable",
                           np.where(t.quality_state != "ok", "quality_" + t.quality_state.astype(str),
                                    np.where(~np.array(adm_q), "quality_not_admissible",
                                             np.where(t.path.isna() | ~t.path.astype(str).str.startswith("/SUM"), "no_data_segment", ""))))
    adm = t[t.reason == ""]
    out = dict(status="no_magnetogram", A=None, B=None, A_path=None, B_path=None, A_size=None, B_size=None, A_dt_h=np.nan,
               B_dt_h=np.nan, pair_dt_min=np.nan, A_interval=None, A_quality=None, pair_status="no_pair")
    near = adm[adm.dt_h.abs() <= A_WINDOW_H]
    if near.empty:
        return out, t[t.reason != ""]
    a = near.assign(_a=near.dt_h.abs()).sort_values(["_a", "t_obs_utc"], kind="stable").iloc[0]
    a_int = None if pd.isna(a.interval_s) else float(a.interval_s)
    out.update(status="ok", A=a.T_REC, A_path=a.path, A_dt_h=a.dt_h, A_interval=a_int, A_size=a.get("*size*"),
               A_quality=f"0x{int(a.quality_int):08x}")
    if a_int is None:
        out["pair_status"] = "no_pair_interval_unknown"
        return out, t[t.reason != ""]
    same = adm[adm.interval_s.notna() & (adm.interval_s == a_int) & (adm.T_REC != a.T_REC)]
    cand = same.assign(_dt=(same.t_obs_utc - a.t_obs_utc).dt.total_seconds() / 3600.0)
    after = cand[(cand._dt > 0) & (cand._dt <= B_WINDOW_H)].sort_values(["_dt", "t_obs_utc"], kind="stable")
    before = cand[(cand._dt < 0) & (cand._dt >= -B_WINDOW_H)].assign(_b=lambda x: -x._dt).sort_values(["_b", "t_obs_utc"], kind="stable")
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
    rows = [dict(T_REC=c[k], path=c[f"{k}_path"], size=size_or_none(c.get(f"{k}_size"))) for c in choices for k in ("A", "B")
            if c.get(f"{k}_path")]
    return pd.DataFrame(rows, columns=PLAN_COLS).drop_duplicates("path").reset_index(drop=True)


def composition(recs):
    if recs is None or recs.empty:
        return pd.DataFrame(columns=COMP_COLS)
    q = [f"0x{int(v):08x}" if st == "ok" else st for v, st in zip(recs.quality_int, recs.quality_state)]
    iv = ["missing" if pd.isna(v) else f"{float(v):g}" for v in recs.interval_s]
    r = recs.assign(quality=q, interval=iv, in6=recs.dt_h.abs() <= A_WINDOW_H)
    keys = ["year"] + CLS + ["quality", "interval"]
    a = r.groupby(keys).size().rename("n_records_10h")
    b = r[r.in6].groupby(keys).size().rename("n_records_6h")
    return pd.concat([a, b], axis=1).fillna(0).astype(int).reset_index()[COMP_COLS]


def alternatives(groups):
    rows = []
    for keys, g in groups.groupby(CLS):
        okr = g.request_status == "ok"
        r = dict(zip(CLS, keys), n_groups=len(g), n_requests_ok=int(okr.sum()), n_not_determined=int((~okr).sum()))
        for tag in ("frozen", "alt"):
            r[f"A_{tag}"] = int((okr & (g[f"status_{tag}"] == "ok")).sum())
            r[f"pair_{tag}"] = int((okr & g[f"pair_{tag}"].isin(["after", "before"])).sum())
        rows.append(r)
    return pd.DataFrame(rows, columns=ALT_COLS)


# ---------------------------------------------------------------- provenance gate

def strict_receipt(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    si = lambda x: isinstance(x, int) and not isinstance(x, bool)          # noqa: E731
    return (si(p) and si(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False and r.get(key) == sha(meta))


def gate_problems(sel=None, sel_rec=None, protocol=None, freeze=None, require_clean=True):
    sel, sel_rec = Path(sel or SEL), Path(sel_rec or SEL_REC)
    protocol, freeze = Path(protocol or PROTOCOL), Path(freeze or FREEZE)
    probs = []
    try:
        fr = json.loads(freeze.read_text())
        m = json.loads((sel / "META.json").read_text())
    except (OSError, ValueError) as exc:
        return [f"unreadable ({type(exc).__name__})"]
    if sha(protocol) != fr.get("sha256") or m.get("protocol_sha256") != fr.get("sha256"):
        probs.append("protocol")
    ps = m.get("products_sha256", {})
    if set(ps) != {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"} or any(sha(sel / n) != h for n, h in ps.items()):
        probs.append("selection products")
    if not strict_receipt(sel_rec / "RECEIPT.json", "selection_meta_sha256", sel / "META.json"):
        probs.append("selection receipt")
    if not probs:
        s = pd.read_csv(sel / "SAMPLE.csv", dtype={"noaa": str})
        c = pd.read_csv(sel / "CELLS.csv")
        l2 = s[s.level2.astype(str) == "True"]
        if l2.duplicated(["noaa", "day"]).any() or len(l2) != int(c.n2.sum()):
            probs.append("level-2 units")
    if require_clean and subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                                        capture_output=True, text=True).stdout.strip():
        probs.append("tracked tree not clean")
    return probs


# ---------------------------------------------------------------- network

class TransportFailure(Exception):
    def __init__(self, stage, msg, nbytes, requests=1):
        super().__init__(f"{stage}: {msg}")
        self.stage, self.nbytes, self.requests = stage, nbytes, requests


def http_json(query, timeout=30):
    """Plain HTTP GET of jsoc_info (no redirect followed). Returns (doc, bytes, requests); failures carry the bytes."""
    conn = http.client.HTTPConnection(HOST, 80, timeout=timeout)
    body = b""
    try:
        conn.request("GET", PATH + "?" + urlencode(query), headers={"Accept-Encoding": "identity"})
        res = conn.getresponse()
        try:
            while len(body) < LG.METADATA_CAP_BYTES:
                chunk = res.read1(65536)
                if not chunk:
                    break
                body += chunk
        except Exception as exc:
            raise TransportFailure("read", f"{type(exc).__name__}: {exc}", len(body)) from exc
        if res.status != 200:
            raise TransportFailure("http", f"HTTP {res.status}", len(body))
        try:
            return json.loads(body), len(body), 1
        except ValueError as exc:
            raise TransportFailure("json", str(exc), len(body)) from exc
    except TransportFailure:
        raise
    except Exception as exc:
        raise TransportFailure("connect", f"{type(exc).__name__}: {exc}", len(body)) from exc
    finally:
        conn.close()


def fetch(out=OUT, transport=http_json, ledger=None, sel=None, sel_rec=None, protocol=None, freeze=None, require_clean=True):
    ledger = ledger or LG.LEDGER
    sel = Path(sel or SEL)
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    probs = gate_problems(sel, sel_rec, protocol, freeze, require_clean)
    if probs:
        sys.exit("provenance gate: " + "; ".join(probs))
    samp = pd.read_csv(sel / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    fr = json.loads(Path(freeze or FREEZE).read_text())
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    stopped, errors = "", []
    with LG.RunLock(ledger):
        try:
            with (tmp / "ANSWERS.jsonl").open("w") as fa:
                for r in l2.itertuples():
                    t0 = pd.Timestamp(r.t_dpd)
                    half = pd.Timedelta(hours=A_WINDOW_H + B_WINDOW_H)
                    ds = f"{SERIES}[{tai_string(t0 - half)}-{tai_string(t0 + half)}]"
                    rec = dict(noaa=r.noaa, day=r.day, t_dpd=str(r.t_dpd), ds=ds)
                    i, why = LG.reserve("metadata", ds, LG.METADATA_CAP_BYTES, ledger)
                    if i is None:
                        stopped = f"ledger refused: {why}"
                        rec.update(request_status="not_attempted", error=stopped)
                        fa.write(json.dumps(rec) + "\n")
                        continue
                    try:
                        doc, nbytes, nreq = transport(dict(op="rs_list", ds=ds, key=",".join(KEYWORDS), seg="data"))
                        LG.finish(i, "metadata", nreq, nbytes, "ok", path=ledger)
                        rec.update(request_status="ok", bytes=nbytes, doc=doc)
                    except TransportFailure as exc:
                        LG.finish(i, "metadata", exc.requests, exc.nbytes, "failed", str(exc), exc.stage, path=ledger)
                        rec.update(request_status=f"failed_{exc.stage}", bytes=exc.nbytes, error=str(exc))
                    except Exception as exc:
                        LG.finish(i, "metadata", 1, 0, "failed", f"{type(exc).__name__}: {exc}", "unknown", path=ledger)
                        rec.update(request_status="failed_unknown", bytes=0, error=f"{type(exc).__name__}: {exc}")
                    fa.write(json.dumps(rec) + "\n")
                    fa.flush()
            prods = derive(tmp / "ANSWERS.jsonl", l2)
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            prods = derive_empty()
        for name, df in prods.items():
            df.to_csv(tmp / name, index=False)
        ch = prods["CHOICES.csv"]
        n_ok = int((ch.request_status == "ok").sum()) if len(ch) else 0
        complete = not stopped and not errors and n_ok == len(l2)
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), ledger_module_sha256=sha(ROOT / "scripts/mdi_l2_ledger.py"),
                    selection_meta_sha256=sha(sel / "META.json"), level2_groups=len(l2), requests_ok=n_ok,
                    completeness="complete" if complete else "incomplete", stopped=stopped, derivation_errors=errors,
                    ledger_totals_after=LG.totals(ledger),
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    print(json.dumps(dict(completeness=meta["completeness"], requests_ok=n_ok, ledger=LG.totals(ledger)), indent=1))
    return 0 if complete else 2


def derive_empty():
    return {"CHOICES.csv": pd.DataFrame(columns=CHOICE_COLS), "GROUPS.csv": pd.DataFrame(columns=GROUP_COLS),
            "DISCARDED.csv": pd.DataFrame(columns=DISC_COLS), "DOWNLOAD_PLAN.csv": pd.DataFrame(columns=PLAN_COLS),
            "QUALITY_INTERVAL.csv": pd.DataFrame(columns=COMP_COLS), "ADMISSIBLE_ALTERNATIVES.csv": pd.DataFrame(columns=ALT_COLS)}


def derive(answers_path, l2):
    """All derived products from the preserved answers (also used by the offline recount)."""
    lines = [json.loads(x) for x in Path(answers_path).read_text().splitlines() if x.strip()]
    by = {(x["noaa"], x["day"]): x for x in lines}
    choices, groups, disc, recs = [], [], [], []
    for r in l2.itertuples():
        x = by.get((r.noaa, r.day), dict(request_status="not_attempted"))
        cls = dict(act_class=r.act_class, hemisphere=r.hemisphere, area_class=r.area_class, cohort=r.cohort)
        base = dict(noaa=r.noaa, day=r.day, t_dpd=str(r.t_dpd), request_status=x["request_status"], error=x.get("error", ""))
        if x["request_status"] != "ok":
            choices.append(dict(base, status="not_determined", pair_status="not_determined"))
            groups.append(dict(noaa=r.noaa, day=r.day, year=str(r.day)[:4], **cls, request_status=x["request_status"],
                               status_frozen="not_determined", pair_frozen="not_determined", status_alt="not_determined", pair_alt="not_determined"))
            continue
        t = records_from_answer(x["doc"])
        c, d = choose(t, r.t_dpd, FROZEN_ADMISSIBLE)
        c2, _ = choose(t, r.t_dpd, ALTERNATIVE_ADMISSIBLE)
        choices.append(dict(base, n_records=len(t), **c))
        groups.append(dict(noaa=r.noaa, day=r.day, year=str(r.day)[:4], **cls, request_status="ok", status_frozen=c["status"],
                           pair_frozen=c["pair_status"], status_alt=c2["status"], pair_alt=c2["pair_status"]))
        disc.append(d.assign(noaa=r.noaa, day=r.day))
        t0 = pd.Timestamp(r.t_dpd)
        recs.append(t.assign(dt_h=[(v - t0).total_seconds() / 3600.0 if v is not None else np.nan for v in t.t_obs_utc],
                             year=str(r.day)[:4], **cls))
    ch = pd.DataFrame(choices).reindex(columns=CHOICE_COLS)
    gr = pd.DataFrame(groups, columns=GROUP_COLS)
    di = pd.concat(disc).reindex(columns=DISC_COLS) if disc else pd.DataFrame(columns=DISC_COLS)
    return {"CHOICES.csv": ch, "GROUPS.csv": gr, "DISCARDED.csv": di,
            "DOWNLOAD_PLAN.csv": plan([c for c in choices if c.get("status") == "ok"]),
            "QUALITY_INTERVAL.csv": composition(pd.concat(recs) if recs else None), "ADMISSIBLE_ALTERNATIVES.csv": alternatives(gr)}


# ---------------------------------------------------------------- selftest (offline)

def answer(rows):
    keys = list(rows[0])
    return dict(status=0, count=len(rows), keywords=[dict(name=k, values=[r[k] for r in rows]) for k in keys if k != "path"],
                segments=[dict(name="data", values=[r["path"] for r in rows])])


def rec(trec, tobs, q="0x00000000", interval="300", path="/SUM1/D1/S0/data.fits", size="2000000"):
    return {"T_REC": trec, "T_OBS": tobs, "QUALITY": q, "INTERVAL": interval, "MISSVALS": "0", "*size*": size, "path": path}


def fixture(td, n=2, receipt_ok=True):
    """Consistent synthetic selection (products, META, strict receipt, protocol, freeze) for the gate."""
    td = Path(td)
    sel, rec_d = td / "sel", td / "selrec"
    sel.mkdir(parents=True)
    rec_d.mkdir()
    (td / "prot.md").write_text("frozen")
    (td / "freeze.json").write_text(json.dumps(dict(sha256=sha(td / "prot.md"))))
    s = pd.DataFrame(dict(noaa=[str(k + 1) for k in range(n)], day=["2000-06-01"] * n, t_dpd=["2000-06-01 10:00:00"] * n,
                          level2=[True] * n, act_class=[1] * n, hemisphere=["N"] * n, area_class=[1] * n, cohort=["M1"] * n))
    s.to_csv(sel / "SAMPLE.csv", index=False)
    pd.DataFrame(dict(act_class=[1], hemisphere=["N"], area_class=[1], cohort=["M1"], n2=[n])).to_csv(sel / "CELLS.csv", index=False)
    (sel / "POPULATION.csv").write_text("x\n")
    (sel / "META.json").write_text(json.dumps(dict(protocol_sha256=sha(td / "prot.md"),
                                                   products_sha256={k: sha(sel / k) for k in ("POPULATION.csv", "SAMPLE.csv", "CELLS.csv")})))
    rc = dict(passed=1, total=1, partial=not receipt_ok, checks=[dict(ok=True)], selection_meta_sha256=sha(sel / "META.json"))
    (rec_d / "RECEIPT.json").write_text(json.dumps(rc))
    return dict(sel=sel, sel_rec=rec_d, protocol=td / "prot.md", freeze=td / "freeze.json", require_clean=False)


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    ok("times: TAI -> UTC, seconds = 60 as interval, fractional seconds kept, UTC string kept",
       jsoc_to_utc("2000.01.01_00:00:32_TAI") == pd.Timestamp("2000-01-01 00:00:00")
       and jsoc_to_utc("2000.01.01_00:00:60_TAI") == pd.Timestamp("2000-01-01 00:00:28")
       and jsoc_to_utc("2000.01.01_00:00:32.75_TAI") == pd.Timestamp("2000-01-01 00:00:00.75")
       and jsoc_to_utc("2000.01.01_00:00:05.5") == pd.Timestamp("2000-01-01 00:00:05.5"))
    ok("QUALITY: hex parsed; missing and unparsable are not zero", parse_quality("0x00000200") == (512, "ok")
       and parse_quality(None) == (None, "missing") and parse_quality(float("nan"))[1] == "missing" and parse_quality("zz") == (None, "unparsable"))
    t_dpd = pd.Timestamp("2000-06-01 10:00:00")
    base = [rec("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", path="/SUM1/a"),
            rec("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00_TAI", path="/SUM1/b"),
            rec("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", path="/SUM1/c"),
            rec("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", path="/SUM1/d", interval="30")]
    c, _ = choose(records_from_answer(answer(base)), t_dpd)
    ok("A closest; B first after with the same INTERVAL", c["A"] == "2000.06.01_09:36:00_TAI" and c["B"] == "2000.06.01_11:12:00_TAI")
    mixq = [dict(r, QUALITY=None) if r["path"] == "/SUM1/b" else r for r in base]
    t = records_from_answer(answer(mixq))
    c, d = choose(t, t_dpd)
    comp = composition(t.assign(dt_h=0.0, year="2000", act_class=1, hemisphere="N", area_class=1, cohort="M1"))
    ok("valid + missing QUALITY: nullable integer, missing record not admissible, composition does not fail",
       str(t.quality_int.dtype) == "Int64" and c["A"] == "2000.06.01_11:12:00_TAI" and (d.reason == "quality_missing").sum() == 1
       and "missing" in set(comp.quality))
    mixi = [dict(r, INTERVAL="MISSING") if r["path"] == "/SUM1/b" else r for r in base]
    c, _ = choose(records_from_answer(answer(mixi)), t_dpd)
    ok("A with missing INTERVAL while others are numeric -> no_pair_interval_unknown (NaN handled)", c["pair_status"] == "no_pair_interval_unknown")
    edge = [rec("2000.06.01_04:00:00_TAI", "2000.06.01_04:00:32_TAI", path="/SUM2/a"), rec("2000.06.01_00:00:00_TAI", "2000.06.01_00:00:32_TAI", path="/SUM2/b")]
    c, _ = choose(records_from_answer(answer(edge)), t_dpd)
    ok("edges: A at -6 h and B 4 h before A accepted", c["A"] == "2000.06.01_04:00:00_TAI" and c["B"] == "2000.06.01_00:00:00_TAI")
    import tempfile as tf
    with tf.TemporaryDirectory() as td:
        fx = fixture(td)
        calls = {"n": 0}

        def flaky(qy, timeout=30):
            calls["n"] += 1
            if calls["n"] == 1:
                raise TransportFailure("http", "HTTP 500", 1234)
            return answer([dict(r, QUALITY="0x00000200") for r in base]), 800, 1
        led = Path(td) / "L.jsonl"
        rc = fetch(Path(td) / "out", flaky, led, **fx)
        meta = json.loads((Path(td) / "out/META.json").read_text())
        alt = pd.read_csv(Path(td) / "out/ADMISSIBLE_ALTERNATIVES.csv")
        ok("bytes of a failed request counted: ledger 1234 + 800", LG.totals(led)["bytes"] == 2034, LG.totals(led))
        ok("failed group kept in the denominator as not determined; run marked incomplete",
           rc == 2 and meta["completeness"] == "incomplete" and int(alt.n_groups.sum()) == 2 and int(alt.n_not_determined.sum()) == 1
           and int(alt.A_frozen.sum()) == 0 and int(alt.A_alt.sum()) == 1)
        ok("answers preserved progressively (one line per group)", len((Path(td) / "out/ANSWERS.jsonl").read_text().splitlines()) == 2)
    with tf.TemporaryDirectory() as td:
        fx = fixture(td)

        def broken(qy, timeout=30):
            raise TransportFailure("json", "invalid JSON", 4321)
        rc = fetch(Path(td) / "out", broken, Path(td) / "L.jsonl", **fx)
        names = {f.name for f in (Path(td) / "out").iterdir()}
        ok("all requests failed: complete schemas written, explicit incomplete state, bytes of invalid JSON counted",
           rc == 2 and {"CHOICES.csv", "GROUPS.csv", "QUALITY_INTERVAL.csv", "ADMISSIBLE_ALTERNATIVES.csv", "DOWNLOAD_PLAN.csv"} <= names
           and LG.totals(Path(td) / "L.jsonl")["bytes"] == 2 * 4321)
    with tf.TemporaryDirectory() as td:
        fx = fixture(td, receipt_ok=False)
        called = {"n": 0}

        def spy(qy, timeout=30):
            called["n"] += 1
            return answer(base), 1, 1
        try:
            fetch(Path(td) / "out", spy, Path(td) / "L.jsonl", **fx)
            ok("partial selection receipt -> refused before any request", False)
        except SystemExit:
            ok("partial selection receipt -> refused before any request", called["n"] == 0)
        fx = fixture(Path(td) / "b")
        (fx["sel"] / "SAMPLE.csv").write_text("noaa,day\n1,2000-06-01\n")
        try:
            fetch(Path(td) / "out2", spy, Path(td) / "L.jsonl", **fx)
            ok("SAMPLE changed after its META -> refused before any request", False)
        except SystemExit:
            ok("SAMPLE changed after its META -> refused before any request", called["n"] == 0)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else fetch())
