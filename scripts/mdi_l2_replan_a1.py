"""MDI pilot level 2: new download plan under amendment A1, offline from the preserved answers (no JSOC request).

Frozen amendment docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md (SHA in its FREEZE record): admissible QUALITY exactly
{0, 0x200}; A/B rules unchanged. Main assignments use {0, 0x200}; the ORIGINAL assignments ({0}) are kept for the
secondary table. Plan = union of the main A/B files and of the original A/B files not in the main set (supplementary,
labelled), expected 159 + 2 = 161 unique files, no new group or day. Products in results/MDI_PILOT_L2_PLAN_A1/:
CHOICES_A1.csv (with QUALITY of A and B and the QUALITY transition flag of the pair), CHOICES_ORIGINAL.csv (equal to
the original metadata CHOICES assignments), PLAN.csv (roles per file), COVERAGE.csv, META.json. Gate before reading:
protocol and A1 freeze, metadata products and hashes, strict metadata recount receipt, selection products.

    .venv/bin/python scripts/mdi_l2_replan_a1.py --selftest
    .venv/bin/python scripts/mdi_l2_replan_a1.py --run
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

ROOT = Path(__file__).resolve().parents[1]
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
MD, MD_REC = ROOT / "results/MDI_PILOT_L2_METADATA", ROOT / "results/MDI_PILOT_L2_METADATA_RECOUNT"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
OUT = ROOT / "results/MDI_PILOT_L2_PLAN_A1"
A1_SET, ORIGINAL_SET = (0, 0x200), (0,)
CLS = ["act_class", "hemisphere", "area_class", "cohort"]
_s = importlib.util.spec_from_file_location("mdi_fd_metadata", ROOT / "scripts/mdi_fd_metadata.py")
MDM = importlib.util.module_from_spec(_s)
_s.loader.exec_module(MDM)
MD_PRODUCTS = {"ANSWERS.jsonl", "CHOICES.csv", "GROUPS.csv", "DISCARDED.csv", "DOWNLOAD_PLAN.csv", "QUALITY_INTERVAL.csv",
               "ADMISSIBLE_ALTERNATIVES.csv"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gate(md=MD, md_rec=MD_REC, sel=SEL, a1=A1, a1_freeze=A1_FREEZE):
    probs = []
    fz = json.loads(Path(a1_freeze).read_text())
    if sha(a1) != fz.get("sha256") or tuple(fz.get("admissible_quality", [])) != A1_SET:
        probs.append("A1 freeze")
    m = json.loads((Path(md) / "META.json").read_text())
    if fz.get("parent_sha256") != m.get("protocol_sha256"):
        probs.append("protocol of the metadata")
    ps = m.get("products_sha256", {})
    if set(ps) != MD_PRODUCTS or any(sha(Path(md) / n) != h for n, h in ps.items()):
        probs.append("metadata products")
    if sha(Path(md) / "META.json") != fz.get("source_metadata_meta_sha256"):
        probs.append("metadata META differs from the one named by A1")
    if not MDM.strict_receipt(Path(md_rec) / "RECEIPT.json", "metadata_meta_sha256", Path(md) / "META.json"):
        probs.append("metadata recount receipt")
    if m.get("selection_meta_sha256") != sha(Path(sel) / "META.json"):
        probs.append("selection link")
    return probs


def quality_of(recs, trec):
    r = recs[recs.T_REC == trec]
    return None if r.empty or pd.isna(r.quality_int.iloc[0]) else f"0x{int(r.quality_int.iloc[0]):08x}"


def build(answers, l2):
    by = {(a["noaa"], a["day"]): a for a in answers}
    main, orig = [], []
    for r in l2.itertuples():
        a = by[(r.noaa, r.day)]
        base = dict(noaa=r.noaa, day=r.day, **{k: getattr(r, k) for k in CLS})
        if a["request_status"] != "ok":
            main.append(dict(base, status="not_determined"))
            orig.append(dict(base, status="not_determined"))
            continue
        recs = MDM.records_from_answer(a["doc"])
        for store, aset in ((main, A1_SET), (orig, ORIGINAL_SET)):
            c, _ = MDM.choose(recs, r.t_dpd, aset)
            qa = quality_of(recs, c["A"]) if c["A"] else None
            qb = quality_of(recs, c["B"]) if c["B"] else None
            store.append(dict(base, status=c["status"], A=c["A"], A_path=c["A_path"], A_quality=qa, A_interval=c["A_interval"],
                              A_dt_h=c["A_dt_h"], B=c["B"], B_path=c["B_path"], B_quality=qb, B_dt_h=c["B_dt_h"],
                              pair_dt_min=c["pair_dt_min"], pair_status=c["pair_status"],
                              quality_transition=bool(qa and qb and qa != qb)))
    M, O = pd.DataFrame(main), pd.DataFrame(orig)
    files = {}
    for df, tag in ((M, "main"), (O, "original")):
        for row in df.itertuples():
            for k in ("A", "B"):
                p = getattr(row, f"{k}_path", None)
                if isinstance(p, str) and p:
                    f = files.setdefault(p, dict(path=p, T_REC=getattr(row, k), main_A=0, main_B=0, original_A=0, original_B=0))
                    f[f"{tag}_{k}"] += 1
    P = pd.DataFrame(list(files.values()), columns=["path", "T_REC", "main_A", "main_B", "original_A", "original_B"])
    P["in_main"] = (P.main_A + P.main_B) > 0
    P["supplementary_original_only"] = ~P.in_main
    P["size"] = None                                      # unknown in the metadata (empty or 'NA'): never zero
    P = P.sort_values(["supplementary_original_only", "path"], kind="stable").reset_index(drop=True)
    cov = []
    for df, tag in ((M, "A1"), (O, "original")):
        for keys, g in df.groupby(CLS):
            cov.append(dict(rule=tag, **dict(zip(CLS, keys)), n_groups=len(g), A=int((g.status == "ok").sum()),
                            pairs=int(g.pair_status.isin(["after", "before"]).sum()) if "pair_status" in g else 0,
                            A_quality_0=int((g.get("A_quality") == "0x00000000").sum()) if "A_quality" in g else 0,
                            A_quality_200=int((g.get("A_quality") == "0x00000200").sum()) if "A_quality" in g else 0,
                            A_interval_30=int((g.get("A_interval") == 30.0).sum()) if "A_interval" in g else 0,
                            A_interval_300=int((g.get("A_interval") == 300.0).sum()) if "A_interval" in g else 0,
                            quality_transitions=int(g.get("quality_transition", pd.Series(dtype=bool)).fillna(False).sum())))
    return M, O, P, pd.DataFrame(cov)


def run(out=OUT, **paths):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    probs = gate(**paths)
    if probs:
        sys.exit("gate: " + "; ".join(probs))
    md, sel = Path(paths.get("md", MD)), Path(paths.get("sel", SEL))
    samp = pd.read_csv(sel / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    answers = [json.loads(x) for x in (md / "ANSWERS.jsonl").read_text().splitlines() if x.strip()]
    M, O, P, C = build(answers, l2)
    oc = pd.read_csv(md / "CHOICES.csv", dtype={"noaa": str}, keep_default_na=False, na_values=[""])
    same = (list(oc.A.fillna("")) == list(O.get("A", pd.Series([""] * len(O))).fillna("")) and
            list(oc.B.fillna("")) == list(O.get("B", pd.Series([""] * len(O))).fillna("")))
    if not same:
        sys.exit("original assignments differ from the preserved metadata CHOICES")
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        M.to_csv(tmp / "CHOICES_A1.csv", index=False)
        O.to_csv(tmp / "CHOICES_ORIGINAL.csv", index=False)
        P.to_csv(tmp / "PLAN.csv", index=False)
        C.to_csv(tmp / "COVERAGE.csv", index=False)
        fz = json.loads(Path(paths.get("a1_freeze", A1_FREEZE)).read_text())
        meta = dict(a1_sha256=fz["sha256"], protocol_sha256=fz["parent_sha256"], script_sha256=sha(__file__),
                    metadata_meta_sha256=sha(md / "META.json"), metadata_recount_receipt_sha256=sha(Path(paths.get("md_rec", MD_REC)) / "RECEIPT.json"),
                    files_main=int(P.in_main.sum()), files_supplementary=int(P.supplementary_original_only.sum()), files_total=len(P),
                    expected_total=fz.get("expected_union_files"), network=False,
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps({k: meta[k] for k in ("files_main", "files_supplementary", "files_total", "expected_total")}))
    return 0 if len(P) == fz.get("expected_union_files") else 2


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    R = MDM.rec
    t_dpd = "2000-06-01 10:00:00"
    recs = [R("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00_TAI", q="0x00000200", path="/SUM/x1"),
            R("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", q="0x00000000", path="/SUM/x2", interval="30"),
            R("2000.06.01_12:48:00_TAI", "2000.06.01_12:49:00_TAI", q="0x00000200", path="/SUM/x3"),
            R("2000.06.01_08:00:00_TAI", "2000.06.01_08:01:00_TAI", q="0x00000201", path="/SUM/x4")]
    l2 = pd.DataFrame(dict(noaa=["1", "2"], day=["2000-06-01"] * 2, t_dpd=[t_dpd] * 2, act_class=[1, 2], hemisphere=["N", "S"],
                           area_class=[1, 3], cohort=["M1", "U"]))
    answers = [dict(noaa="1", day="2000-06-01", request_status="ok", doc=MDM.answer(recs)),
               dict(noaa="2", day="2000-06-01", request_status="failed_http", error="x")]
    M, O, P, C = build(answers, l2)
    m0 = M.iloc[0]
    ok("A1 admits 0x200 (A = closest record), 0x201 excluded", m0.A == "2000.06.01_09:36:00_TAI" and m0.A_quality == "0x00000200"
       and "/SUM/x4" not in set(P.path))
    o0 = O.iloc[0]
    ok("original assignment kept with {0}", o0.A == "2000.06.01_11:12:00_TAI" and o0.A_quality == "0x00000000")
    ok("A1 pair with the same INTERVAL (B = x3, 0x200), no QUALITY transition here", m0.B == "2000.06.01_12:48:00_TAI" and not bool(m0.quality_transition))
    recs2 = [R("2000.06.01_09:36:00_TAI", "2000.06.01_09:37:00_TAI", q="0x00000200", path="/SUM/y1"),
             R("2000.06.01_11:12:00_TAI", "2000.06.01_11:13:00_TAI", q="0x00000000", path="/SUM/y2")]
    Mq, _, _, _ = build([dict(noaa="1", day="2000-06-01", request_status="ok", doc=MDM.answer(recs2))], l2.iloc[:1])
    ok("QUALITY transition flagged when the pair mixes 0x200 and 0 at the same INTERVAL", bool(Mq.iloc[0].quality_transition))
    sup = P[P.supplementary_original_only]
    ok("plan = union, original-only files labelled supplementary, sizes unknown", set(P.path) == {"/SUM/x1", "/SUM/x2", "/SUM/x3"}
       and list(sup.path) == ["/SUM/x2"] and P["size"].isna().all(), list(P.path))
    ok("failed request kept as not determined in both rules", M.iloc[1].status == O.iloc[1].status == "not_determined")
    c = C.set_index(["rule", "cohort"])
    ok("coverage counts per rule", c.loc[("A1", "M1"), "A"] == 1 and c.loc[("original", "M1"), "A"] == 1 and c.loc[("A1", "U"), "A"] == 0)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
