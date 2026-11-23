"""Offline independent recount of the MDI pilot level-2 metadata step (no network request).

Own code (not importing scripts/mdi_fd_metadata.py) rebuilds EVERY product from the preserved ANSWERS.jsonl and the
verified selection, and compares it in full (columns, keys, order, values; NaN = NaN):
CHOICES (frozen QUALITY {0}), GROUPS (frozen and {0, 0x200}), DISCARDED (records and causes), DOWNLOAD_PLAN (frozen only,
deduplicated, known/unknown sizes), QUALITY_INTERVAL (missing vs unparsable kept apart), ADMISSIBLE_ALTERNATIVES (all
selected groups in the denominators). It also rebuilds completeness, requests_ok and level2_groups of META; checks
answers (unique, belonging to level 2, every unit present, JSOC status and schema); verifies the selection provenance
(protocol, products and their hashes, strict receipt) before reading; and ties each answer to the preserved ledger
(one metadata start/end pair per request, same target, status and bytes). The receipt is complete only on the real path.

    .venv/bin/python scripts/mdi_fd_metadata_recount.py --selftest
    .venv/bin/python scripts/mdi_fd_metadata_recount.py --check
"""
import argparse
import hashlib
import json
import math
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.time import Time

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "results/MDI_PILOT_L2_METADATA"
REC = ROOT / "results/MDI_PILOT_L2_METADATA_RECOUNT"
SEL, SEL_REC = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
LEDGER = ROOT / "results/MDI_PILOT_L2_LEDGER/LEDGER.jsonl"
PROTOCOL, FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
PRODUCTS = {"ANSWERS.jsonl", "CHOICES.csv", "GROUPS.csv", "DISCARDED.csv", "DOWNLOAD_PLAN.csv", "QUALITY_INTERVAL.csv",
            "ADMISSIBLE_ALTERNATIVES.csv"}
CLS = ["act_class", "hemisphere", "area_class", "cohort"]
REQUIRED_KEYWORDS = {"T_REC", "T_OBS", "QUALITY", "INTERVAL"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def is_missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v))


def to_utc(s):
    try:
        s = str(s)
        y, mo, d = (int(x) for x in s[:10].split("."))
        hh, mm, ss = s[11:].split("_")[0].split(":")
        t = pd.Timestamp(y, mo, d, int(hh), int(mm)) + timedelta(seconds=float(ss))
    except (ValueError, IndexError, TypeError):
        return None
    return pd.Timestamp(Time(t.to_pydatetime(), scale="tai").utc.to_datetime()) if s.endswith("_TAI") else t


def quality(q):
    if is_missing(q) or str(q).strip() in ("", "MISSING", "nan", "None"):
        return None, "missing"
    s = str(q).strip()
    try:
        return (int(s, 16) if s.lower().startswith("0x") else int(s)), "ok"
    except ValueError:
        return None, "unparsable"


def interval(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def expected_query(t_dpd):
    """Own reconstruction of the authorised series and symmetric +/-10 h UTC window, serialized in TAI."""
    t = pd.Timestamp(t_dpd)
    def tai(dt):
        return Time(dt.to_pydatetime(), scale="utc").tai.to_datetime().strftime("%Y.%m.%d_%H:%M:%S_TAI")
    return f"mdi.fd_M_96m_lev182[{tai(t-pd.Timedelta(hours=10))}-{tai(t+pd.Timedelta(hours=10))}]"


def records(doc):
    kw = {k["name"]: k["values"] for k in doc["keywords"]}
    n = int(doc["count"])
    paths = doc["segments"][0]["values"] if doc.get("segments") else [None] * n
    out = []
    for j in range(n):
        g = lambda k: kw[k][j] if k in kw else None                    # noqa: E731
        q, qs = quality(g("QUALITY"))
        out.append(dict(T_REC=g("T_REC"), T_OBS=g("T_OBS"), QUALITY=g("QUALITY"), INTERVAL=g("INTERVAL"), t=to_utc(g("T_OBS")),
                        q=q, qs=qs, iv=interval(g("INTERVAL")), path=paths[j], size=g("*size*")))
    return out


def reason(r, adm_set):
    if r["t"] is None:
        return "t_obs_unparsable"
    if r["qs"] != "ok":
        return f"quality_{r['qs']}"
    if r["q"] not in adm_set:
        return "quality_not_admissible"
    if r["path"] is None or not str(r["path"]).startswith("/SUM"):
        return "no_data_segment"
    return ""


def pick(recs, t_dpd, adm_set):
    t0 = pd.Timestamp(t_dpd)
    hours = lambda t: (t - t0).total_seconds() / 3600.0                # noqa: E731
    adm = [r for r in recs if reason(r, adm_set) == ""]
    near = sorted([r for r in adm if abs(hours(r["t"])) <= 6.0], key=lambda r: (abs(hours(r["t"])), r["t"]))
    o = dict(status="no_magnetogram", A=None, A_path=None, A_size=None, A_dt_h=np.nan, A_quality=None, A_interval=None,
             B=None, B_path=None, B_size=None, B_dt_h=np.nan, pair_dt_min=np.nan, pair_status="no_pair")
    if not near:
        return o
    a = near[0]
    o.update(status="ok", A=a["T_REC"], A_path=a["path"], A_size=a["size"], A_dt_h=hours(a["t"]), A_quality=f"0x{a['q']:08x}",
             A_interval=a["iv"])
    if a["iv"] is None:
        o["pair_status"] = "no_pair_interval_unknown"
        return o
    d = lambda r: (r["t"] - a["t"]).total_seconds() / 3600.0           # noqa: E731
    same = [r for r in adm if r["iv"] is not None and r["iv"] == a["iv"] and r["T_REC"] != a["T_REC"]]
    after = sorted([r for r in same if 0 < d(r) <= 4.0], key=lambda r: (d(r), r["t"]))
    before = sorted([r for r in same if -4.0 <= d(r) < 0], key=lambda r: (-d(r), r["t"]))
    b = after[0] if after else (before[0] if before else None)
    if b:
        o.update(B=b["T_REC"], B_path=b["path"], B_size=b["size"], B_dt_h=hours(b["t"]), pair_dt_min=d(b) * 60.0,
                 pair_status="after" if after else "before")
    return o


def size_value(x):
    try:
        v = int(str(x))
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def frames_equal(a, b, tol=1e-12):
    if list(a.columns) != list(b.columns):
        return False, f"columns {list(a.columns)} vs {list(b.columns)}"
    if len(a) != len(b):
        return False, f"rows {len(a)} vs {len(b)}"
    for c in a.columns:
        x, y = a[c].reset_index(drop=True), b[c].reset_index(drop=True)
        xn, yn = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
        numeric = ((xn.notna() | x.isna()).all() and (yn.notna() | y.isna()).all())
        if numeric:
            if not np.allclose(xn.to_numpy(float), yn.to_numpy(float), rtol=tol, atol=tol, equal_nan=True):
                return False, c
        else:
            nm = lambda s: s.map(lambda v: "" if is_missing(v) or str(v) in ("nan", "None", "NaN") else str(v))   # noqa: E731
            if not (nm(x).to_numpy() == nm(y).to_numpy()).all():
                return False, c
    return True, ""


def strict_receipt(path, key, meta):
    try:
        r = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return False
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    si = lambda x: isinstance(x, int) and not isinstance(x, bool)          # noqa: E731
    return (si(p) and si(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False and r.get(key) == sha(meta))


def rebuild(answers, l2):
    """Own reconstruction of every product (same columns as the runner)."""
    by = {(a["noaa"], a["day"]): a for a in answers}
    ch, gr, di, comp, plan, seen = [], [], [], [], [], set()
    for r in l2.itertuples():
        a = by.get((r.noaa, r.day), dict(request_status="not_attempted"))
        cls = {k: getattr(r, k) for k in CLS}
        base = dict(noaa=r.noaa, day=r.day, t_dpd=str(r.t_dpd), request_status=a["request_status"])
        if a["request_status"] != "ok":
            ch.append(dict(base, n_records=np.nan, status="not_determined", pair_status="not_determined", error=a.get("error", "")))
            gr.append(dict(noaa=r.noaa, day=r.day, year=str(r.day)[:4], **cls, request_status=a["request_status"],
                           status_frozen="not_determined", pair_frozen="not_determined", status_alt="not_determined", pair_alt="not_determined"))
            continue
        recs = records(a["doc"])
        f, g = pick(recs, r.t_dpd, (0,)), pick(recs, r.t_dpd, (0, 0x200))
        ch.append(dict(base, n_records=len(recs), **f, error=""))
        gr.append(dict(noaa=r.noaa, day=r.day, year=str(r.day)[:4], **cls, request_status="ok", status_frozen=f["status"],
                       pair_frozen=f["pair_status"], status_alt=g["status"], pair_alt=g["pair_status"]))
        t0 = pd.Timestamp(r.t_dpd)
        for x in recs:
            rs = reason(x, (0,))
            if rs:
                di.append(dict(noaa=r.noaa, day=r.day, T_REC=x["T_REC"], T_OBS=x["T_OBS"], QUALITY=x["QUALITY"], INTERVAL=x["INTERVAL"], reason=rs))
            dt = (x["t"] - t0).total_seconds() / 3600.0 if x["t"] is not None else np.nan
            comp.append(dict(year=str(r.day)[:4], **cls, quality=f"0x{x['q']:08x}" if x["qs"] == "ok" else x["qs"],
                             interval="missing" if x["iv"] is None else f"{x['iv']:g}", in6=bool(np.isfinite(dt) and abs(dt) <= 6.0)))
        if f["status"] == "ok":
            for k in ("A", "B"):
                if f[f"{k}_path"] and f[f"{k}_path"] not in seen:
                    seen.add(f[f"{k}_path"])
                    plan.append(dict(T_REC=f[k], path=f[f"{k}_path"], size=size_value(f[f"{k}_size"])))
    CH = pd.DataFrame(ch).reindex(columns=["noaa", "day", "t_dpd", "request_status", "n_records", "status", "A", "A_path", "A_size",
                                           "A_dt_h", "A_quality", "A_interval", "B", "B_path", "B_size", "B_dt_h", "pair_dt_min",
                                           "pair_status", "error"])
    GR = pd.DataFrame(gr, columns=["noaa", "day", "year"] + CLS + ["request_status", "status_frozen", "pair_frozen", "status_alt", "pair_alt"])
    DI = pd.DataFrame(di, columns=["noaa", "day", "T_REC", "T_OBS", "QUALITY", "INTERVAL", "reason"])
    PL = pd.DataFrame(plan, columns=["T_REC", "path", "size"])
    keys = ["year"] + CLS + ["quality", "interval"]
    cq = pd.DataFrame(comp, columns=keys + ["in6"])
    QI = (cq.groupby(keys).agg(n_records_10h=("in6", "size"), n_records_6h=("in6", "sum")).reset_index()
          if len(cq) else pd.DataFrame(columns=keys + ["n_records_10h", "n_records_6h"]))
    alt = []
    for kk, g in GR.groupby(CLS):
        okr = g.request_status == "ok"
        alt.append(dict(zip(CLS, kk), n_groups=len(g), n_requests_ok=int(okr.sum()), n_not_determined=int((~okr).sum()),
                        A_frozen=int((okr & (g.status_frozen == "ok")).sum()), pair_frozen=int((okr & g.pair_frozen.isin(["after", "before"])).sum()),
                        A_alt=int((okr & (g.status_alt == "ok")).sum()), pair_alt=int((okr & g.pair_alt.isin(["after", "before"])).sum())))
    AL = pd.DataFrame(alt, columns=CLS + ["n_groups", "n_requests_ok", "n_not_determined", "A_frozen", "pair_frozen", "A_alt", "pair_alt"])
    n_ok = int((CH.request_status == "ok").sum())
    return {"CHOICES.csv": CH, "GROUPS.csv": GR, "DISCARDED.csv": DI, "DOWNLOAD_PLAN.csv": PL, "QUALITY_INTERVAL.csv": QI,
            "ADMISSIBLE_ALTERNATIVES.csv": AL}, n_ok


def check(md=MD, sel=SEL, sel_rec=SEL_REC, ledger=LEDGER, protocol=PROTOCOL, freeze=FREEZE, write=True, rec_dir=REC, synthetic=False):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    md, sel = Path(md), Path(sel)
    meta = json.loads((md / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("metadata products: exact set and actual hashes before reading", set(ps) == PRODUCTS and all(sha(md / n) == h for n, h in ps.items()))
    fr = json.loads(Path(freeze).read_text())
    sm = json.loads((sel / "META.json").read_text())
    sel_ok = (sha(protocol) == fr.get("sha256") == sm.get("protocol_sha256") == meta.get("protocol_sha256")
              and set(sm.get("products_sha256", {})) == {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}
              and all(sha(sel / n) == h for n, h in sm["products_sha256"].items())
              and strict_receipt(Path(sel_rec) / "RECEIPT.json", "selection_meta_sha256", sel / "META.json")
              and meta.get("selection_meta_sha256") == sha(sel / "META.json"))
    ok("selection provenance: protocol, products and hashes, strict receipt, link", sel_ok)
    samp = pd.read_csv(sel / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    answers = [json.loads(x) for x in (md / "ANSWERS.jsonl").read_text().splitlines() if x.strip()]
    keys = [(a["noaa"], a["day"]) for a in answers]
    l2k = list(zip(l2.noaa, l2.day))
    schema_ok = all(a.get("request_status") != "ok" or (a["doc"].get("status") == 0 and REQUIRED_KEYWORDS <= {k["name"] for k in a["doc"]["keywords"]}
                                                        and all(len(k["values"]) == int(a["doc"]["count"]) for k in a["doc"]["keywords"]))
                    for a in answers)
    ok("answers: unique, every level-2 unit present once, none extra, JSOC status and schema", len(set(keys)) == len(keys)
       and set(keys) == set(l2k) and len(keys) == len(l2k) and schema_ok, (len(keys), len(l2k)))
    expected = {(r.noaa, r.day): (pd.Timestamp(r.t_dpd), expected_query(r.t_dpd)) for r in l2.itertuples()}
    query_ok = True
    for a in answers:
        key = (a["noaa"], a["day"])
        query_ok &= (key in expected and pd.Timestamp(a.get("t_dpd")) == expected[key][0]
                     and a.get("ds") == expected[key][1])
    ok("queries: authorised series, selected DPD instant and exact +/-10 h window independently rebuilt", query_ok)
    own, n_ok = rebuild(answers, l2)
    for name, df in own.items():
        # keep JSOC's literal "NA" (unavailable size) as a string: only empty fields are missing
        g, why = frames_equal(pd.read_csv(md / name, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip"), df)
        ok(f"{name}: every column, key and value", g, why)
    complete = n_ok == len(l2) and not meta.get("stopped") and not meta.get("derivation_errors")
    ok("META completeness, requests_ok and level2_groups rebuilt", meta.get("completeness") == ("complete" if complete else "incomplete")
       and meta.get("requests_ok") == n_ok and meta.get("level2_groups") == len(l2), (meta.get("completeness"), meta.get("requests_ok")))
    ledger_bytes = Path(ledger).read_bytes() if Path(ledger).exists() else b""
    ent = [json.loads(x) for x in ledger_bytes.splitlines() if x.strip()]
    starts = [e for e in ent if e["phase"] == "start" and e["kind"] == "metadata"]
    ends = {e["id"]: e for e in ent if e["phase"] == "end" and e["kind"] == "metadata"}
    # answers are matched IN ORDER with the metadata starts of the ledger (several groups of the same day share the
    # same DPD time, hence the same request target); each ledger start is consumed once
    led_ok, ptr = True, 0
    for a in answers:
        if a["request_status"] == "not_attempted":
            continue
        while ptr < len(starts) and starts[ptr]["target"] != a["ds"]:
            ptr += 1
        if ptr >= len(starts):
            led_ok = False
            break
        e = ends.get(starts[ptr]["id"])
        led_ok &= e is not None and int(e["bytes"]) == int(a.get("bytes", -1)) and (e["status"] == "ok") == (a["request_status"] == "ok")
        ptr += 1
    ok("ledger: each request matched in order to one start/end with the same target, status and bytes", led_ok)
    passed = sum(c["ok"] for c in checks)
    real = not synthetic
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, metadata_meta_sha256=sha(md / "META.json"),
                   coverage=f"{n_ok}/{len(l2)} level-2 units answered", completeness=meta.get("completeness"),
                   ledger_prefix_sha256=hashlib.sha256(ledger_bytes).hexdigest(), ledger_prefix_lines=len(ledger_bytes.splitlines()),
                   script_sha256=sha(__file__))
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    check.last_receipt = receipt
    return passed == len(checks)


def selftest():
    import contextlib
    import importlib.util
    import io
    import tempfile
    spec = importlib.util.spec_from_file_location("mdm", ROOT / "scripts/mdi_fd_metadata.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    res = []

    def quiet(fn, *a, **k):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*a, **k)
    base = [M.rec("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", path="/SUM1/a", size="NA"),     # chosen record with JSOC "NA" size
            M.rec("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00.5_TAI", path="/SUM1/b", q="0x00000200"),
            M.rec("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", path="/SUM1/c"),
            M.rec("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", path="/SUM1/d", interval="MISSING", q=None),
            M.rec("2000.06.01_13:00:00_TAI", "2000.06.01_13:00:32_TAI", path="/SUM1/e", q="zz", size="NA")]
    empty = dict(status=0, count=0, keywords=[dict(name=n, values=[]) for n in ("T_REC", "T_OBS", "QUALITY", "INTERVAL")],
                 segments=[dict(name="data", values=[])])
    with tempfile.TemporaryDirectory() as td:
        fx = M.fixture(td, n=4)
        n = {"k": 0}

        def tr(qy, timeout=30):
            n["k"] += 1
            if n["k"] == 2:
                raise M.TransportFailure("read", "reset", 77)
            if n["k"] == 3:
                return empty, 50, 1
            return M.answer(base), 900, 1
        led = Path(td) / "L.jsonl"
        quiet(M.fetch, Path(td) / "out", tr, led, **fx)
        kw = dict(sel=fx["sel"], sel_rec=fx["sel_rec"], ledger=led, protocol=fx["protocol"], freeze=fx["freeze"], write=False, synthetic=True)
        base_ok = quiet(check, Path(td) / "out", **kw)
        res.append(base_ok and check.last_receipt["partial"] is True)
        print("[OK]" if res[-1] else "[FALLITO]", "base: failed request, empty answer, missing and unparsable QUALITY, unknown size reproduced; partial")
        if not base_ok:
            check(Path(td) / "out", **kw)
        out = Path(td) / "out"

        def tamper(name, fn, f, js=False):
            p = out / f
            orig = p.read_text()
            if js:
                j = json.loads(orig)
                fn(j)
                p.write_text(json.dumps(j))
            else:
                t = pd.read_csv(p, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")
                fn(t).to_csv(p, index=False)
            m = json.loads((out / "META.json").read_text())
            m["products_sha256"] = {k: sha(out / k) for k in m["products_sha256"]}
            (out / "META.json").write_text(json.dumps(m))
            bad = not quiet(check, out, **kw)
            res.append(bad)
            print("[OK]" if bad else "[FALLITO]", f"refused with updated hashes: {name}")
            p.write_text(orig)
            if f != "META.json":
                m = json.loads((out / "META.json").read_text())
                m["products_sha256"] = {k: sha(out / k) for k in m["products_sha256"]}
                (out / "META.json").write_text(json.dumps(m))
        first = lambda t, c, v: t.assign(**{c: t[c].astype(object).where(t.index != 0, v)})     # noqa: E731
        tamper("DOWNLOAD_PLAN size = 1 (Codex)", lambda t: first(t, "size", 1), "DOWNLOAD_PLAN.csv")
        tamper("CHOICES A_path = /SUMevil/wrong (Codex)", lambda t: first(t, "A_path", "/SUMevil/wrong"), "CHOICES.csv")
        tamper("CHOICES A_dt_h = 100 (Codex)", lambda t: first(t, "A_dt_h", 100.0), "CHOICES.csv")
        tamper("META completeness incomplete, requests_ok 0 (Codex)", lambda j: j.update(completeness="complete", requests_ok=0), "META.json", js=True)
        tamper("a DISCARDED reason changed", lambda t: first(t, "reason", "quality_missing"), "DISCARDED.csv")
        tamper("unparsable QUALITY reported as missing", lambda t: t.assign(quality=t.quality.replace("unparsable", "missing")), "QUALITY_INTERVAL.csv")
        tamper("an alternative count changed", lambda t: first(t, "A_alt", 99), "ADMISSIBLE_ALTERNATIVES.csv")
        tamper("a group status changed", lambda t: first(t, "status_alt", "no_magnetogram"), "GROUPS.csv")
        tamper("a pair status changed", lambda t: first(t, "pair_status", "after"), "CHOICES.csv")
        ans = (out / "ANSWERS.jsonl").read_text()
        (out / "ANSWERS.jsonl").write_text(ans + ans.splitlines()[0] + "\n")
        m = json.loads((out / "META.json").read_text())
        m["products_sha256"]["ANSWERS.jsonl"] = sha(out / "ANSWERS.jsonl")
        (out / "META.json").write_text(json.dumps(m))
        res.append(not quiet(check, out, **kw))
        print("[OK]" if res[-1] else "[FALLITO]", "refused: a duplicated answer")
        (out / "ANSWERS.jsonl").write_text(ans)
        m["products_sha256"]["ANSWERS.jsonl"] = sha(out / "ANSWERS.jsonl")
        (out / "META.json").write_text(json.dumps(m))
        led_text = led.read_text()
        led.write_text(led_text.replace('"bytes": 900', '"bytes": 901', 1))
        res.append(not quiet(check, out, **kw))
        print("[OK]" if res[-1] else "[FALLITO]", "refused: ledger bytes differ from the answer")
        led.write_text(led_text)
        # A wrong query copied consistently into answer and ledger must still fail against the selection.
        query_answers = (out / "ANSWERS.jsonl").read_text()
        changed = [json.loads(x) for x in query_answers.splitlines()]
        wrong_ds = "mdi.fd_M_96m_lev182[1999.01.01_00:00:00_TAI-1999.01.01_01:00:00_TAI]"
        changed[0]["ds"] = wrong_ds
        (out / "ANSWERS.jsonl").write_text("".join(json.dumps(x)+"\n" for x in changed))
        entries = [json.loads(x) for x in led_text.splitlines()]
        entries[0]["target"] = wrong_ds
        led.write_text("".join(json.dumps(x)+"\n" for x in entries))
        mm = json.loads((out / "META.json").read_text())
        mm["products_sha256"]["ANSWERS.jsonl"] = sha(out / "ANSWERS.jsonl")
        (out / "META.json").write_text(json.dumps(mm))
        res.append(not quiet(check, out, **kw))
        print("[OK]" if res[-1] else "[FALLITO]", "refused: wrong query consistent in answer and ledger")
        (out / "ANSWERS.jsonl").write_text(query_answers)
        led.write_text(led_text)
        mm["products_sha256"]["ANSWERS.jsonl"] = sha(out / "ANSWERS.jsonl")
        (out / "META.json").write_text(json.dumps(mm))
        rc = json.loads((fx["sel_rec"] / "RECEIPT.json").read_text())
        (fx["sel_rec"] / "RECEIPT.json").write_text(json.dumps(dict(rc, partial=True)))
        res.append(not quiet(check, out, **kw))
        print("[OK]" if res[-1] else "[FALLITO]", "refused: selection receipt partial")
        try:
            check(out, **dict(kw, write=True, rec_dir=Path(td) / "rec"))
            res.append(False)
        except SystemExit:
            res.append(not (Path(td) / "rec").exists())
        print("[OK]" if res[-1] else "[FALLITO]", "no receipt written on a synthetic path")
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
