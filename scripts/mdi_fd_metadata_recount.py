"""Offline independent recount of the MDI pilot level-2 metadata step (no network request).

From the preserved ANSWERS.jsonl and the verified selection, own code (not importing scripts/mdi_fd_metadata.py)
rebuilds the A/B choices under the frozen QUALITY {0} and under {0, 0x200}, the per-group outcomes (failed requests
'not determined'), the QUALITY x INTERVAL composition, the alternative counts and the deduplicated download plan, and
compares them with the products. Strict receipt (partial outside the real path).

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
SEL = ROOT / "results/MDI_PILOT_SELECTION"
PRODUCTS = {"ANSWERS.jsonl", "CHOICES.csv", "GROUPS.csv", "DISCARDED.csv", "DOWNLOAD_PLAN.csv", "QUALITY_INTERVAL.csv",
            "ADMISSIBLE_ALTERNATIVES.csv"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def utc(s):
    try:
        s = str(s)
        y, mo, d = (int(x) for x in s[:10].split("."))
        hh, mm, ss = s[11:].split("_")[0].split(":")
        t = pd.Timestamp(y, mo, d, int(hh), int(mm)) + timedelta(seconds=float(ss))
    except (ValueError, IndexError, TypeError):
        return None
    return pd.Timestamp(Time(t.to_pydatetime(), scale="tai").utc.to_datetime()) if s.endswith("_TAI") else t


def qual(q):
    if q is None or (isinstance(q, float) and math.isnan(q)) or str(q).strip() in ("", "MISSING", "nan", "None"):
        return None
    try:
        return int(str(q), 0) if str(q).lower().startswith("0x") else int(str(q))
    except ValueError:
        return None


def ival(v):
    try:
        x = float(v)
        return x if math.isfinite(x) and x > 0 else None
    except (TypeError, ValueError):
        return None


def own_choice(doc, t_dpd, adm_set):
    kw = {k["name"]: k["values"] for k in doc["keywords"]}
    n = int(doc["count"])
    paths = doc["segments"][0]["values"] if doc.get("segments") else [None] * n
    t0 = pd.Timestamp(t_dpd)
    recs = []
    for j in range(n):
        g = lambda k: kw.get(k, [None] * n)[j]                              # noqa: E731
        t = utc(g("T_OBS"))
        q = qual(g("QUALITY"))
        recs.append(dict(trec=g("T_REC"), t=t, q=q, iv=ival(g("INTERVAL")), path=paths[j], size=g("*size*"),
                         dt=(t - t0).total_seconds() / 3600 if t is not None else None))
    adm = [r for r in recs if r["t"] is not None and r["q"] is not None and r["q"] in adm_set and str(r["path"]).startswith("/SUM")]
    near = sorted([r for r in adm if abs(r["dt"]) <= 6.0], key=lambda r: (abs(r["dt"]), r["t"]))
    if not near:
        return dict(status="no_magnetogram", A=None, B=None, pair="no_pair"), recs
    a = near[0]
    if a["iv"] is None:
        return dict(status="ok", A=a["trec"], A_path=a["path"], A_size=a["size"], B=None, pair="no_pair_interval_unknown"), recs
    same = [r for r in adm if r["iv"] == a["iv"] and r["trec"] != a["trec"]]
    d = lambda r: (r["t"] - a["t"]).total_seconds() / 3600                  # noqa: E731
    after = sorted([r for r in same if 0 < d(r) <= 4.0], key=lambda r: (d(r), r["t"]))
    before = sorted([r for r in same if -4.0 <= d(r) < 0], key=lambda r: (-d(r), r["t"]))
    b = after[0] if after else (before[0] if before else None)
    return dict(status="ok", A=a["trec"], A_path=a["path"], A_size=a["size"], B=b["trec"] if b else None,
                B_path=b["path"] if b else None, B_size=b["size"] if b else None,
                pair=("after" if after else "before") if b else "no_pair"), recs


def check(md=MD, sel=SEL, write=True, rec_dir=REC, real=True):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(md) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("products: exact set and actual hashes before reading", set(ps) == PRODUCTS and all(sha(Path(md) / n) == h for n, h in ps.items()))
    ok("linked to the current selection", meta.get("selection_meta_sha256") == sha(Path(sel) / "META.json"))
    samp = pd.read_csv(Path(sel) / "SAMPLE.csv", dtype={"noaa": str})
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    ans = {(x["noaa"], x["day"]): x for x in map(json.loads, (Path(md) / "ANSWERS.jsonl").read_text().splitlines())}
    ch = pd.read_csv(Path(md) / "CHOICES.csv", dtype={"noaa": str})
    gr = pd.read_csv(Path(md) / "GROUPS.csv", dtype={"noaa": str})
    ok("one choice and one group row per level-2 unit, in order", list(zip(ch.noaa, ch.day)) == list(zip(l2.noaa, l2.day))
       and list(zip(gr.noaa, gr.day)) == list(zip(l2.noaa, l2.day)))
    good, plan_rows, comp, rows_alt = True, [], [], []
    for r, c, g in zip(l2.itertuples(), ch.itertuples(), gr.itertuples()):
        a = ans.get((r.noaa, r.day), {})
        if a.get("request_status") != "ok":
            good &= c.status == "not_determined" and g.status_frozen == "not_determined" and g.request_status == a.get("request_status", "not_attempted")
            rows_alt.append((r.act_class, r.hemisphere, r.area_class, r.cohort, False, None, None, None, None))
            continue
        f, recs = own_choice(a["doc"], r.t_dpd, (0,))
        al, _ = own_choice(a["doc"], r.t_dpd, (0, 0x200))
        nz = lambda v: None if (v is None or (isinstance(v, float) and math.isnan(v))) else v      # noqa: E731
        good &= c.status == f["status"] and nz(c.A) == f["A"] and nz(c.B) == f.get("B") and c.pair_status == f["pair"]
        good &= g.status_frozen == f["status"] and g.pair_frozen == f["pair"] and g.status_alt == al["status"] and g.pair_alt == al["pair"]
        for k in ("A", "B"):
            if f.get(f"{k}_path"):
                plan_rows.append((f[k], f[f"{k}_path"]))
        for x in recs:
            comp.append(dict(year=str(r.day)[:4], act_class=r.act_class, hemisphere=r.hemisphere, area_class=r.area_class, cohort=r.cohort,
                             quality=f"0x{x['q']:08x}" if x["q"] is not None else ("missing" if str(x.get("q")) == "None" else "unparsable"),
                             interval="missing" if x["iv"] is None else f"{x['iv']:g}", in6=x["dt"] is not None and abs(x["dt"]) <= 6.0))
        rows_alt.append((r.act_class, r.hemisphere, r.area_class, r.cohort, True, f["status"], f["pair"], al["status"], al["pair"]))
    ok("choices under the frozen set and under {0, 0x200} reproduced; failed requests not determined", good)
    P = pd.read_csv(Path(md) / "DOWNLOAD_PLAN.csv")
    seen, dedup = set(), []
    for t, p in plan_rows:
        if p not in seen:
            seen.add(p)
            dedup.append((t, p))
    ok("download plan: frozen choice only, deduplicated, same order", list(zip(P.T_REC, P.path)) == dedup)
    A = pd.read_csv(Path(md) / "ADMISSIBLE_ALTERNATIVES.csv")
    al = pd.DataFrame(rows_alt, columns=["act_class", "hemisphere", "area_class", "cohort", "req", "sf", "pf", "sa", "pa"])
    agg = al.groupby(["act_class", "hemisphere", "area_class", "cohort"]).apply(lambda x: pd.Series(dict(
        n_groups=len(x), n_requests_ok=int(x.req.sum()), n_not_determined=int((~x.req).sum()),
        A_frozen=int((x.req & (x.sf == "ok")).sum()), pair_frozen=int((x.req & x.pf.isin(["after", "before"])).sum()),
        A_alt=int((x.req & (x.sa == "ok")).sum()), pair_alt=int((x.req & x.pa.isin(["after", "before"])).sum())))).reset_index()
    m = A.merge(agg, on=["act_class", "hemisphere", "area_class", "cohort"], how="outer", suffixes=("", "_o"), indicator=True)
    ok("alternative counts with all selected groups in the denominators", (m._merge == "both").all() and all(
        (m[c] == m[f"{c}_o"]).all() for c in ("n_groups", "n_requests_ok", "n_not_determined", "A_frozen", "pair_frozen", "A_alt", "pair_alt")))
    Q = pd.read_csv(Path(md) / "QUALITY_INTERVAL.csv", dtype={"quality": str, "interval": str, "hemisphere": str, "cohort": str, "year": str})
    cq = pd.DataFrame(comp)
    if len(cq):
        k = ["year", "act_class", "hemisphere", "area_class", "cohort", "quality", "interval"]
        own = cq.groupby(k).agg(n_records_10h=("in6", "size"), n_records_6h=("in6", "sum")).reset_index()
        mm = Q.merge(own, on=k, how="outer", suffixes=("", "_o"), indicator=True)
        ok("QUALITY x INTERVAL composition", (mm._merge == "both").all() and (mm.n_records_10h == mm.n_records_10h_o).all()
           and (mm.n_records_6h == mm.n_records_6h_o).all())
    else:
        ok("QUALITY x INTERVAL composition (no answered request)", len(Q) == 0)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, metadata_meta_sha256=sha(Path(md) / "META.json"),
                   completeness=meta.get("completeness"))
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


def selftest():
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("mdm", ROOT / "scripts/mdi_fd_metadata.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    res = []
    base = [M.rec("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", path="/SUM1/a"),
            M.rec("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00.5_TAI", path="/SUM1/b", q="0x00000200"),
            M.rec("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", path="/SUM1/c"),
            M.rec("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", path="/SUM1/d", interval="MISSING", q=None)]
    with tempfile.TemporaryDirectory() as td:
        fx = M.fixture(td, n=3)
        n = {"k": 0}

        def tr(qy, timeout=30):
            n["k"] += 1
            if n["k"] == 2:
                raise M.TransportFailure("read", "reset", 77)
            return M.answer(base), 900, 1
        M.fetch(Path(td) / "out", tr, Path(td) / "L.jsonl", **fx)
        res.append(check(Path(td) / "out", fx["sel"], write=False, real=False))
        print("[OK]" if res[-1] else "[FALLITO]", "recount reproduces a synthetic metadata run (one request failed)")
        c = pd.read_csv(Path(td) / "out/CHOICES.csv", dtype={"noaa": str})
        c.loc[0, "B"] = "2000.06.01_12:48:00_TAI"                       # a different record
        c.to_csv(Path(td) / "out/CHOICES.csv", index=False)
        m = json.loads((Path(td) / "out/META.json").read_text())
        m["products_sha256"]["CHOICES.csv"] = sha(Path(td) / "out/CHOICES.csv")
        (Path(td) / "out/META.json").write_text(json.dumps(m))
        res.append(not check(Path(td) / "out", fx["sel"], write=False, real=False))
        print("[OK]" if res[-1] else "[FALLITO]", "refused: a B choice changed with updated hashes")
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
