"""Independent recount of the A1 level-2 plan (offline). Own record parsing and A/B choice come from the metadata
recount (scripts/mdi_fd_metadata_recount.py), not from the runner scripts/mdi_fd_metadata.py.
Rebuilds and compares in full CHOICES_A1, CHOICES_ORIGINAL (also equal to the preserved metadata CHOICES assignments),
PLAN (union, roles, supplementary labels, sizes unknown, order) and COVERAGE; checks the A1 freeze, the metadata
products and recount receipt, the plan META links and the expected 161 files. Strict receipt.

    .venv/bin/python scripts/mdi_l2_replan_a1_recount.py --check
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "results/MDI_PILOT_L2_PLAN_A1"
REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
MD, MD_REC, SEL = ROOT / "results/MDI_PILOT_L2_METADATA", ROOT / "results/MDI_PILOT_L2_METADATA_RECOUNT", ROOT / "results/MDI_PILOT_SELECTION"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
CLS = ["act_class", "hemisphere", "area_class", "cohort"]
_s = importlib.util.spec_from_file_location("mrc", ROOT / "scripts/mdi_fd_metadata_recount.py")
RC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(RC)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def own(answers, l2):
    by = {(a["noaa"], a["day"]): a for a in answers}
    out = {"A1": [], "original": []}
    for r in l2.itertuples():
        a = by[(r.noaa, r.day)]
        base = dict(noaa=r.noaa, day=r.day, **{k: getattr(r, k) for k in CLS})
        if a["request_status"] != "ok":
            for k in out:
                out[k].append(dict(base, status="not_determined"))
            continue
        recs = RC.records(a["doc"])
        q_of = {x["T_REC"]: (f"0x{x['q']:08x}" if x["qs"] == "ok" else None) for x in recs}
        for k, aset in (("A1", (0, 0x200)), ("original", (0,))):
            c = RC.pick(recs, r.t_dpd, aset)
            qa, qb = (q_of.get(c["A"]) if c["A"] else None), (q_of.get(c["B"]) if c["B"] else None)
            out[k].append(dict(base, status=c["status"], A=c["A"], A_path=c["A_path"], A_quality=qa, A_interval=c["A_interval"],
                               A_dt_h=c["A_dt_h"], B=c["B"], B_path=c["B_path"], B_quality=qb, B_dt_h=c["B_dt_h"],
                               pair_dt_min=c["pair_dt_min"], pair_status=c["pair_status"], quality_transition=bool(qa and qb and qa != qb)))
    M, O = pd.DataFrame(out["A1"]), pd.DataFrame(out["original"])
    files = {}
    for df, tag in ((M, "main"), (O, "original")):
        for row in df.to_dict("records"):
            for k in ("A", "B"):
                p = row.get(f"{k}_path")
                if isinstance(p, str) and p:
                    f = files.setdefault(p, dict(path=p, T_REC=row[k], main_A=0, main_B=0, original_A=0, original_B=0))
                    f[f"{tag}_{k}"] += 1
    P = pd.DataFrame(list(files.values()), columns=["path", "T_REC", "main_A", "main_B", "original_A", "original_B"])
    P["in_main"] = (P.main_A + P.main_B) > 0
    P["supplementary_original_only"] = ~P.in_main
    P["size"] = None
    P = P.sort_values(["supplementary_original_only", "path"], kind="stable").reset_index(drop=True)
    cov = []
    for df, tag in ((M, "A1"), (O, "original")):
        for keys, g in df.groupby(CLS):
            okq = lambda c, v: int((g[c] == v).sum()) if c in g else 0      # noqa: E731
            cov.append(dict(rule=tag, **dict(zip(CLS, keys)), n_groups=len(g), A=int((g.status == "ok").sum()),
                            pairs=int(g.pair_status.isin(["after", "before"]).sum()) if "pair_status" in g else 0,
                            A_quality_0=okq("A_quality", "0x00000000"), A_quality_200=okq("A_quality", "0x00000200"),
                            A_interval_30=okq("A_interval", 30.0), A_interval_300=okq("A_interval", 300.0),
                            quality_transitions=int(g["quality_transition"].fillna(False).sum()) if "quality_transition" in g else 0))
    return M, O, P, pd.DataFrame(cov)


def check(plan=PLAN, write=True, rec_dir=REC):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(plan) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("plan products: exact set and actual hashes before reading", set(ps) == {"CHOICES_A1.csv", "CHOICES_ORIGINAL.csv", "PLAN.csv", "COVERAGE.csv"}
       and all(sha(Path(plan) / n) == h for n, h in ps.items()))
    fz = json.loads(A1_FREEZE.read_text())
    mm = json.loads((MD / "META.json").read_text())
    ok("A1 freeze, metadata products, metadata recount receipt and links", sha(A1) == fz["sha256"] == meta.get("a1_sha256")
       and tuple(fz["admissible_quality"]) == (0, 0x200) and sha(MD / "META.json") == fz["source_metadata_meta_sha256"] == meta.get("metadata_meta_sha256")
       and all(sha(MD / n) == h for n, h in mm["products_sha256"].items())
       and RC.strict_receipt(MD_REC / "RECEIPT.json", "metadata_meta_sha256", MD / "META.json")
       and meta.get("metadata_recount_receipt_sha256") == sha(MD_REC / "RECEIPT.json"))
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    l2 = samp[samp.level2.astype(str) == "True"].reset_index(drop=True)
    answers = [json.loads(x) for x in (MD / "ANSWERS.jsonl").read_text().splitlines() if x.strip()]
    M, O, P, C = own(answers, l2)
    rd = lambda n: pd.read_csv(Path(plan) / n, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")  # noqa: E731
    for name, df in (("CHOICES_A1.csv", M), ("CHOICES_ORIGINAL.csv", O), ("PLAN.csv", P), ("COVERAGE.csv", C)):
        g, why = RC.frames_equal(rd(name), df)
        ok(f"{name}: every column, key and value", g, why)
    oc = pd.read_csv(MD / "CHOICES.csv", dtype={"noaa": str}, keep_default_na=False, na_values=[""])
    norm = lambda s: ["" if RC.is_missing(v) else str(v) for v in s]    # noqa: E731
    ok("original assignments equal to the preserved metadata CHOICES (A, B, status)", norm(oc.A) == norm(O.get("A", [])) and norm(oc.B) == norm(O.get("B", []))
       and list(oc.status) == list(O.status))
    ok("161 unique files = main + supplementary, as frozen in A1", len(P) == fz["expected_union_files"] == meta.get("files_total")
       and int(P.in_main.sum()) == fz["main_files_from_metadata"] and int(P.supplementary_original_only.sum()) == fz["original_baseline_supplementary_files"],
       (len(P), int(P.in_main.sum()), int(P.supplementary_original_only.sum())))
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=False, checks=checks, plan_meta_sha256=sha(Path(plan) / "META.json"))
    if write:
        if Path(rec_dir).exists():
            sys.exit("receipt exists")
        Path(rec_dir).mkdir(parents=True)
        (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)}")
    return passed == len(checks)


def selftest():
    """Tamperings of copies of the preserved plan (offline, no receipt written)."""
    import contextlib
    import io
    import shutil
    import tempfile
    res = []
    with tempfile.TemporaryDirectory() as td:
        def mutate(name, f, fn):
            d = Path(td) / name.replace(" ", "_")
            shutil.copytree(PLAN, d)
            t = pd.read_csv(d / f, dtype={"noaa": str}, keep_default_na=False, na_values=[""])
            fn(t).to_csv(d / f, index=False)
            m = json.loads((d / "META.json").read_text())
            m["products_sha256"][f] = sha(d / f)
            (d / "META.json").write_text(json.dumps(m))
            with contextlib.redirect_stdout(io.StringIO()):
                bad = not check(d, write=False)
            res.append(bad)
            print("[OK]" if bad else "[FALLITO]", f"refused with updated hashes: {name}")
        with contextlib.redirect_stdout(io.StringIO()):
            res.append(check(PLAN, write=False))
        print("[OK]" if res[-1] else "[FALLITO]", "preserved plan accepted")
        mutate("supplementary flag flipped", "PLAN.csv", lambda t: t.assign(supplementary_original_only=t.supplementary_original_only.where(t.index != 0, True)))
        mutate("a plan path changed", "PLAN.csv", lambda t: t.assign(path=t.path.where(t.index != 0, "/SUMevil")))
        mutate("a plan row dropped", "PLAN.csv", lambda t: t.drop(index=0))
        mutate("an A1 B choice changed", "CHOICES_A1.csv", lambda t: t.assign(B=t.B.where(t.index != t.B.first_valid_index(), "x")))
        mutate("a QUALITY of A changed", "CHOICES_A1.csv", lambda t: t.assign(A_quality=t.A_quality.where(t.A_quality.isna(), "0x00000201")))
        mutate("a coverage count changed", "COVERAGE.csv", lambda t: t.assign(A=t.A + (t.index == 0)))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
