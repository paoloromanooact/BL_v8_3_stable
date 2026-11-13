"""Standalone T5-D2 technical audit; never imports the scientific producer.

--selftest --out NEW_DIR: deterministic hand-built tables only.
--check: requires the completed run, a matching selftest receipt and a NEW output
folder. This does not validate T5 or authorize its application to observations.
Contract: docs/T5_ORACLE_POSTCHECK_SPEC.md (registered before this code).
"""
from __future__ import annotations

import argparse
import copy
import csv
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SPEC = "docs/T5_ORACLE_POSTCHECK_SPEC.md"
INPUTS = "docs/T5_ORACLE_POSTCHECK_INPUTS_SHA256.csv"
PRODUCER = "2bf262f1b99d6a884ed72686047dc089911e5eff"
REFERENCE_PRODUCER = "5c3b664bb3e6bbdddd8a9502801163ed9873ce49"
ETA = 3.56e-25
Q = NormalDist().inv_cdf(.9875)
STATES = ("supportato", "opposto", "non deciso", "errore")
ARMS = ("A0", "A1a", "A1b", "A2", "A3", "A2p")
KEY = ("kind", "scenario", "effect", "k", "arm")
GROUP = ("kind", "scenario", "effect", "arm")
PROV_PATHS = {
    "sha256_P2": "docs/PROTOCOL_P2_QUENCHING.md",
    "sha256_P2d": "docs/PROTOCOL_P2D_SIMULATION_CALIBRATED_TEST.md",
    "sha256_P2e": "docs/PROTOCOL_P2E_ATTENUATION_CORRECTION.md",
    "sha256_PROTOCOL_T5_ORACLE": "docs/PROTOCOL_T5_ORACLE.md",
    "sha256_PROTOCOL_T5_ORACLE_A1": "docs/PROTOCOL_T5_ORACLE_A1.md",
    "sha256_PROTOCOL_P2F": "docs/PROTOCOL_P2F_VALIDATED_TEST.md",
    "sha256_VALIDATION_RAW": "results/P2F/VALIDATION_RAW.csv.gz",
}
STATUS = "diagnostica T5-D2, non cieca, nessun verdetto"
OUTPUTS = ("ORACLE_RAW.csv.gz", "ORACLE_SUMMARY.csv", "ORACLE_PAIRED_VS_A0.csv", "ORACLE_META.json")
COUNTS = {"n", "errors", "false", "supported", "opposite", "covered", "below", "above"}
SUMMARY_FIELDS = ("n", "errors", "R", "sd_z", "z_q0125", "z_q9875", "false", "false_frac",
                  "false_mc_se", "supported", "opposite", "covered", "coverage", "coverage_mc_se", "below", "above")
PAIR_FIELDS = ("n", "same", "decided_in_A0_not_arm", "decided_in_arm_not_A0")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def read_csv(path):
    """csv preserves literal 'null'; only explicit numeric fields are parsed."""
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt", newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames is None or len(set(rd.fieldnames)) != len(rd.fieldnames):
            raise ValueError("missing/duplicate CSV header")
        rows = list(rd)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise ValueError("ragged CSV row")
        return rows


def write_csv(path, rows):
    rows = list(rows)
    names = list(dict.fromkeys(k for r in rows for k in r)) or ["check", "passed"]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=names, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def number(x):
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("nonfinite number")
    return v


def integer(x):
    try:
        d = Decimal(str(x))
    except InvalidOperation as exc:
        raise ValueError("invalid integer") from exc
    if not d.is_finite() or d != d.to_integral_value():
        raise ValueError("not a finite integer")
    return int(d)


def effect(x):
    try:
        d = Decimal(str(x))
    except InvalidOperation as exc:
        raise ValueError("invalid effect") from exc
    if not d.is_finite():
        raise ValueError("nonfinite effect")
    return str(d.normalize()) if d else "0"


def key(r, fields=KEY):
    return tuple(integer(r[k]) if k in ("scenario", "k") else effect(r[k]) if k == "effect" else str(r[k]) for k in fields)


def missing(x):
    return str(x).strip().lower() in ("", "nan")


def near(a, b):
    return abs(number(a) - b) <= 1e-12 + 1e-9 * abs(b)


def relative(a, b, tol=1e-9):
    return number(a) == 0 if b == 0 else abs(number(a) / b - 1) <= tol


def quantile(values, p):
    v = sorted(values)
    x = (len(v) - 1) * p
    i = math.floor(x)
    return v[i] + (x - i) * (v[min(i + 1, len(v) - 1)] - v[i])


def variance(values):
    m = math.fsum(values) / len(values)
    return math.fsum((x - m) ** 2 for x in values) / (len(values) - 1)


def jobs_spec():
    return ([("null", s, "0", k) for s, n in ((7, 10000), (10, 10000), (1, 2000), (2, 2000)) for k in range(n)]
            + [("effect", 7, e, k) for e in ("-0.1", "-0.2", "-0.3", "-0.35") for k in range(2000)])


def arms(s):
    return ARMS if s in (7, 10) else ARMS[:-1]


class StopAudit(Exception):
    pass


class Audit:
    def __init__(self):
        self.checks = []
        self.discrepancies = []
        self.recounts = []
        self.pairs = []
        self.transitions = []
        self.a0_missing_beta = 0

    def add(self, name, ok, detail=""):
        self.checks.append(dict(check=name, passed=bool(ok), detail=str(detail)))

    def gate(self):
        if not all(r["passed"] for r in self.checks):
            raise StopAudit()

    def attempt(self, name, fun):
        try:
            ok, detail = fun()
            self.add(name, ok, detail)
        except (ValueError, KeyError, TypeError, OverflowError, ZeroDivisionError) as exc:
            self.add(name, False, type(exc).__name__ + ": " + str(exc))


def indexed(rows, fields, expected):
    idx = {key(r, fields): r for r in rows}
    return idx, len(idx) == len(rows) and set(idx) == set(expected)


def check_provenance(a, name, rows, expected):
    a.add(name, bool(rows) and all(all(str(r.get(k, "")) == str(v) for k, v in expected.items()) for r in rows))


def check_metadata(a, meta, prov, n):
    check_provenance(a, "metadata_provenance", [meta], prov)
    a.attempt("metadata_values", lambda: (
        set(meta) == set(prov) | {"phi_star", "kappa_star", "sx2_true", "sig2_true", "n_jobs"}
        and integer(meta["n_jobs"]) == n
        and meta["phi_star"] == {"7": .9106, "10": .8657}
        and meta["kappa_star"] == {"7": 0.0, "10": .98}
        and relative(meta["sx2_true"], (.5 * ETA) ** 2, 1e-12)
        and relative(meta["sig2_true"], ETA ** 2, 1e-12), "constants and job count"))


def verify_raw(a, rows, jobs):
    expected = {j + (arm,) for j in jobs for arm in arms(j[1])}
    idx, good = indexed(rows, KEY, expected)
    a.add("raw_keys_exact", good, f"rows={len(rows)}, expected={len(expected)}")
    raw_fields = set(KEY) | {"beta", "beta_true", "verdict", "error", "se", "lo", "hi", "covered", "below", "above"}
    prov_fields = set(PROV_PATHS) | {"git_commit", "git_dirty", "status"}
    a.add("raw_schema", bool(rows) and all(set(r) == raw_fields | prov_fields for r in rows))
    a.gate()
    problems = defaultdict(list)
    betas = defaultdict(set)
    a3 = defaultdict(list)
    for k, r in idx.items():
        kind, s, e, kk, arm = k
        try:
            b, bt = number(r["beta"]), number(r["beta_true"])
            true = float(e) * ETA
            if not relative(bt, true, 1e-12):
                problems["raw_truth"].append(k)
            betas[k[:-1]].add(b)
            v = r["verdict"]
            flags = tuple(integer(r[t]) for t in ("covered", "below", "above"))
            if any(t not in (0, 1) for t in flags):
                problems["raw_binary_flags"].append(k)
            if v not in STATES:
                problems["raw_states"].append(k)
            elif v == "errore":
                if flags != (0, 0, 0) or not str(r.get("error", "")).strip() or any(not missing(r.get(t, "")) for t in ("se", "lo", "hi")):
                    problems["raw_error_rows"].append(k)
                if arm == "A3":
                    problems["raw_A3_no_error"].append(k)
            else:
                se, lo, hi = (number(r[t]) for t in ("se", "lo", "hi"))
                if not (se > 0 and lo <= b <= hi):
                    problems["raw_finite_intervals"].append(k)
                if se <= 0 or abs((b - lo) / se - Q) > 1e-9 or abs((hi - b) / se - Q) > 1e-9:
                    problems["raw_half_widths"].append(k)
                actual = "supportato" if hi < 0 else "opposto" if lo > 0 else "non deciso"
                if v != actual:
                    problems["raw_verdicts"].append(k)
                if flags != (int(lo <= bt <= hi), int(lo > bt), int(hi < bt)):
                    problems["raw_coverage_tails"].append(k)
                if not missing(r.get("error", "")):
                    problems["raw_error_rows"].append(k)
                if arm == "A3":
                    a3[s].append(se)
        except (ValueError, KeyError, OverflowError, ZeroDivisionError):
            problems["raw_numeric_fields"].append(k)
    names = ("raw_numeric_fields", "raw_truth", "raw_binary_flags", "raw_states", "raw_error_rows", "raw_A3_no_error",
             "raw_finite_intervals", "raw_half_widths", "raw_verdicts", "raw_coverage_tails")
    for name in names:
        a.add(name, not problems[name], f"bad rows={len(problems[name])}; examples={problems[name][:2]}")
    a.add("raw_beta_equal_across_arms", all(len(v) == 1 for v in betas.values()))
    a.add("raw_A3_SE_fixed_by_scenario", all(all(relative(x, v[0]) for x in v) for v in a3.values()))
    a.gate()
    return idx


def verify_a0(a, idx, reference, jobs, ref_prov):
    wanted = set(jobs)
    refs = [r for r in reference if r.get("test") == "T5" and key(r, KEY[:-1]) in wanted]
    ri, good = indexed(refs, KEY[:-1], wanted)
    a.add("A0_reference_keys_exact", good, f"matched={len(refs)}, expected={len(jobs)}")
    check_provenance(a, "A0_reference_provenance", refs, ref_prov)
    a.gate()
    bad = Counter()
    for j in jobs:
        x, y = idx[j + ("A0",)], ri[j]
        if x["verdict"] != y["verdict"]:
            bad["state"] += 1
        if missing(y.get("beta", "")):
            a.a0_missing_beta += 1
            if y["verdict"] != "errore":
                bad["beta_missing_on_valid"] += 1
        elif not relative(x["beta"], number(y["beta"])):
            bad["beta"] += 1
        if not relative(x["beta_true"], number(y["beta_true"]), 1e-12):
            bad["truth"] += 1
        if y["verdict"] != "errore":
            if not relative(x["se"], number(y["se"])):
                bad["se"] += 1
            scale = abs(number(y["beta"])) + Q * number(y["se"])
            if any(abs(number(x[t]) - number(y[t])) > 1e-9 * scale for t in ("lo", "hi")):
                bad["interval"] += 1
    a.add("A0_reproduces_reference", not bad, dict(bad))
    a.add("A0_missing_reference_beta_declared", True, a.a0_missing_beta)
    a.gate()


def recount_group(g, kind):
    valid = [r for r in g if r["verdict"] != "errore"]
    n, m = len(g), len(valid)
    if m < 2:
        raise ValueError("fewer than two valid rows")
    r = [(number(x["beta"]) - number(x["beta_true"])) / ETA for x in valid]
    se = [number(x["se"]) / ETA for x in valid]
    z = [x / y for x, y in zip(r, se)]
    v = variance(r)
    if v <= 0:
        raise ValueError("zero variance of slopes")
    out = dict(n=n, errors=n-m, R=math.fsum(x*x for x in se) / m / v, sd_z=math.sqrt(variance(z)),
               z_q0125=quantile(z, .0125), z_q9875=quantile(z, .9875))
    for t in ("covered", "below", "above"):
        out[t] = sum(integer(x[t]) for x in g)
    out["coverage"] = out["covered"] / n
    out["coverage_mc_se"] = math.sqrt(out["coverage"] * (1-out["coverage"]) / n)
    if kind == "null":
        out["supported"] = sum(x["verdict"] == "supportato" for x in g)
        out["opposite"] = sum(x["verdict"] == "opposto" for x in g)
        out["false"] = out["supported"] + out["opposite"]
        out["false_frac"] = out["false"] / n
        out["false_mc_se"] = math.sqrt(out["false_frac"] * (1-out["false_frac"]) / n)
    return out


def compare_fields(a, name, original, expected, fields, ints):
    bad = 0
    for f in fields:
        try:
            ok = missing(original.get(f, "")) if f not in expected else integer(original[f]) == expected[f] if f in ints else near(original[f], expected[f])
        except (ValueError, KeyError, TypeError, OverflowError):
            ok = False
        if not ok:
            bad += 1
            a.discrepancies.append(dict(table=name, key=str(key(original, GROUP)), column=f,
                                        original=original.get(f, "<missing>"), recounted=expected.get(f, "<not applicable>")))
    return bad


def verify_summary_pairs(a, idx, summary, paired):
    groups = defaultdict(list)
    for k, r in idx.items():
        groups[k[:3] + (k[4],)].append(r)
    si, sg = indexed(summary, GROUP, groups)
    wantpairs = {k for k in groups if k[-1] != "A0"}
    pi, pg = indexed(paired, GROUP, wantpairs)
    a.add("summary_keys_exact", sg)
    a.add("paired_keys_exact", pg)
    # No unknown payload column can silently escape a comparison.
    prov_names = set(PROV_PATHS) | {"git_commit", "git_dirty", "status"}
    a.add("summary_schema", bool(summary) and set(summary[0]) == set(GROUP) | set(SUMMARY_FIELDS) | prov_names)
    a.add("paired_schema", bool(paired) and set(paired[0]) == set(GROUP) | set(PAIR_FIELDS) | prov_names)
    a.gate()
    sbad = pbad = 0
    no_reversal = True
    for k in sorted(groups):
        g = sorted(groups[k], key=lambda x: integer(x["k"]))
        rec = recount_group(g, k[0])
        sbad += compare_fields(a, "summary", si[k], rec, SUMMARY_FIELDS, COUNTS)
        a.recounts.append(dict(zip(GROUP, k), **rec, valid_n=rec["n"]-rec["errors"]))
        if k[-1] == "A0":
            continue
        transitions = Counter((idx[key(r)[:-1] + ("A0",)]["verdict"], r["verdict"]) for r in g)
        n = len(g)
        pr = dict(n=n, same=sum(transitions[v, v] for v in STATES),
                  decided_in_A0_not_arm=sum(transitions[v, "non deciso"] for v in STATES[:2]),
                  decided_in_arm_not_A0=sum(transitions["non deciso", v] for v in STATES[:2]))
        pbad += compare_fields(a, "paired", pi[k], pr, PAIR_FIELDS, set(PAIR_FIELDS))
        a.pairs.append(dict(zip(GROUP, k), **pr, both_valid_n=sum(v for (x,y),v in transitions.items() if x != "errore" and y != "errore")))
        for x in STATES:
            for y in STATES:
                a.transitions.append(dict(zip(GROUP, k), A0_verdict=x, arm_verdict=y, n=transitions[x,y]))
        no_reversal &= transitions["supportato", "opposto"] + transitions["opposto", "supportato"] == 0
        if sum(transitions.values()) != n:
            raise ValueError("incomplete transitions")
    a.add("summary_all_fields_recounted", sbad == 0, f"mismatched fields={sbad}")
    a.add("paired_all_fields_recounted", pbad == 0, f"mismatched fields={pbad}")
    a.add("paired_no_sign_reversal", no_reversal)
    a.add("paired_full_transition_count", len(a.transitions) == 16 * len(wantpairs))
    a.gate()


def audit_tables(raw, summary, paired, meta, reference, jobs, prov, ref_prov):
    a = Audit()
    try:
        for name, rows in (("raw", raw), ("summary", summary), ("paired", paired)):
            check_provenance(a, name+"_provenance", rows, prov)
        check_metadata(a, meta, prov, len(jobs))
        a.gate()
        idx = verify_raw(a, raw, jobs)
        verify_a0(a, idx, reference, jobs, ref_prov)
        verify_summary_pairs(a, idx, summary, paired)
    except StopAudit:
        pass
    except (ValueError, KeyError, TypeError, OverflowError, ZeroDivisionError) as exc:
        a.add("input_structure_exception", False, type(exc).__name__ + ": " + str(exc))
    return a


def finished(log):
    # Inspect only the completion marker, never emit or interpret log tables.
    return any(line.strip() == "fatto" for line in log.read_text().splitlines())


def receipt_ok(path, code_sha, spec_sha):
    x = json.loads(path.read_text())
    return (x.get("all_passed") is True and integer(x.get("tests", 0)) >= 30
            and x.get("code_sha256") == code_sha and x.get("spec_sha256") == spec_sha
            and x.get("selftest_sha256") == sha(path.parent / "SELFTEST.csv"))


def git_info(root):
    def run(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()
    return dict(checker_commit=run("rev-parse", "HEAD"), checker_git_dirty=int(bool(run("status", "--porcelain", "--untracked-files=no"))))


def actual_check(root, out, receipt):
    # This wrapper is deliberately never used by --selftest.
    code = Path(__file__).resolve()
    if out.resolve() == (root / "results/T5_ORACLE").resolve() or out.exists():
        raise ValueError("output directory exists or is the producer directory")
    if not receipt_ok(receipt, sha(code), sha(root / SPEC)):
        raise ValueError("missing/stale/failed selftest receipt")
    run = root / "results/T5_ORACLE"
    if not finished(root / "logs/t5_oracle.log") or not all((run / f).is_file() for f in OUTPUTS):
        raise ValueError("run incomplete: no scientific output opened")
    # Only now may actual scientific files be opened, after explicit --check.
    out.mkdir(parents=True)
    meta = dict(code_sha256=sha(code), spec_sha256=sha(root / SPEC), inputs_manifest_sha256=sha(root / INPUTS),
                selftest_receipt_sha256=sha(receipt), producer_commit_expected=PRODUCER, **git_info(root))
    a = Audit()
    before = {}
    try:
        a.add("checker_tracked_tree_clean", meta["checker_git_dirty"] == 0)
        manifest = read_csv(root / INPUTS)
        fm = {r["file"]: r for r in manifest}
        a.add("input_manifest_unique", len(fm) == len(manifest) == 18)
        a.gate()
        for p, r in fm.items():
            a.add("input_hash:"+p, sha(root / p) == r["sha256"])
        a.gate()
        prov = {k: fm[p]["sha256"] for k, p in PROV_PATHS.items()}
        prov.update(git_commit=PRODUCER, git_dirty="0", status=STATUS)
        prelim = read_csv(run / "PRELIM_TESTS.csv")
        a.add("preliminary_ten_passed", len(prelim) == 10 and all(r["passed"] == "True" for r in prelim))
        check_provenance(a, "preliminary_provenance", prelim, prov)
        a.gate()
        before = {f: sha(run / f) for f in OUTPUTS}
        meta["input_output_hashes_before"] = before
        ref_prov = {k: v for k, v in prov.items() if k in ("sha256_P2", "sha256_P2d", "sha256_P2e", "sha256_PROTOCOL_P2F")}
        ref_prov.update(git_commit=REFERENCE_PRODUCER, git_dirty="0")
        result = audit_tables(read_csv(run / OUTPUTS[0]), read_csv(run / OUTPUTS[1]), read_csv(run / OUTPUTS[2]),
                              json.loads((run / OUTPUTS[3]).read_text()), read_csv(root / PROV_PATHS["sha256_VALIDATION_RAW"]),
                              jobs_spec(), prov, ref_prov)
        a.checks += result.checks
        a.recounts, a.pairs, a.transitions, a.discrepancies = result.recounts, result.pairs, result.transitions, result.discrepancies
        meta["A0_missing_reference_beta"] = result.a0_missing_beta
    except StopAudit:
        pass
    except (OSError, ValueError, KeyError, TypeError, OverflowError, ZeroDivisionError) as exc:
        a.add("audit_exception", False, type(exc).__name__ + ": " + str(exc))
    finally:
        if before:
            after = {f: sha(run / f) if (run / f).is_file() else "missing" for f in OUTPUTS}
            meta["input_output_hashes_after"] = after
            a.add("outputs_unchanged_while_reading", before == after)
        meta.update(all_passed=bool(a.checks) and all(r["passed"] for r in a.checks),
                    checks=len(a.checks), meaning="technical audit only; T5 remains descriptive")
        for name, rows in (("CHECKS", a.checks), ("RECOUNTS", a.recounts), ("PAIR_RECOUNTS", a.pairs),
                           ("PAIRED_TRANSITIONS", a.transitions), ("DISCREPANCIES", a.discrepancies)):
            write_csv(out / (name+".csv"), rows)
        (out / "META.json").write_text(json.dumps(meta, indent=2)+"\n")
    failed = [r["check"] for r in a.checks if not r["passed"]]
    print(f"Technical checks: {len(a.checks)-len(failed)}/{len(a.checks)} passed")
    if failed:
        print("Failed: " + ", ".join(failed))
    return 0 if meta["all_passed"] else 2


# Hand-built examples and adversarial changes; no production files, RNG or model fits.
def fixture():
    jobs = [(kind, s, effect(e), k) for kind,s,e in (("null",1,0),("null",7,0),("effect",7,-.2),("null",10,0)) for k in range(8)]
    prov = {k: "fixture_"+k for k in PROV_PATHS}
    prov.update(git_commit=PRODUCER, git_dirty="0", status=STATUS)
    refprov = {"git_commit": REFERENCE_PRODUCER, "git_dirty": "0"}
    raw = []
    for j in jobs:
        kind,s,e,k = j
        bt = float(e)*ETA
        # Includes exact zero and both decision directions, differing interval widths.
        b = bt + (-4., -1., -.2, 0., .1, .8, 3., 5.)[k]*ETA
        for arm in arms(s):
            se = (1. if arm == "A3" else .65 + .1*ARMS.index(arm) + .025*k)*ETA
            lo,hi = b-Q*se,b+Q*se
            r = dict(zip(KEY,j+(arm,)), beta=b,beta_true=bt,se=se,lo=lo,hi=hi,
                     verdict="supportato" if hi < 0 else "opposto" if lo > 0 else "non deciso",
                     error="", covered=int(lo <= bt <= hi),below=int(lo > bt),above=int(hi < bt),**prov)
            if k == 1 and arm in ("A0", "A1a") or k == 4 and arm == "A2":
                r.update(verdict="errore",error="hand-built failure",se="",lo="",hi="",covered=0,below=0,above=0)
            raw.append(r)
    # Fixture construction uses the pure recounter only to obtain file layout;
    # numerical formulas and quantiles are separately checked against known values.
    groups=defaultdict(list)
    for r in raw:
        groups[key(r,GROUP)].append(r)
    summary=[dict(zip(GROUP,k),**{f:"" for f in SUMMARY_FIELDS},**prov) for k in sorted(groups)]
    for r in summary:
        r.update(recount_group(groups[key(r,GROUP)],r["kind"]))
    paired=[]
    idx={key(r):r for r in raw}
    for g in sorted(groups):
        if g[-1]=="A0":continue
        x=groups[g]; y=[idx[key(r)[:-1]+("A0",)] for r in x]
        paired.append(dict(zip(GROUP,g),n=len(x),same=sum(a["verdict"]==b["verdict"] for a,b in zip(x,y)),
            decided_in_A0_not_arm=sum(b["verdict"] in STATES[:2] and a["verdict"]=="non deciso" for a,b in zip(x,y)),
            decided_in_arm_not_A0=sum(a["verdict"] in STATES[:2] and b["verdict"]=="non deciso" for a,b in zip(x,y)),**prov))
    refs=[dict(r,test="T5",**refprov) for r in raw if r["arm"]=="A0"]
    for r in refs:
        if r["verdict"]=="errore":r["beta"]=""
    meta=dict(phi_star={"7":.9106,"10":.8657}, kappa_star={"7":0.,"10":.98},sx2_true=(.5*ETA)**2,sig2_true=ETA**2,n_jobs=len(jobs),**prov)
    return raw,summary,paired,meta,refs,jobs,prov,refprov


def selftest(out):
    if out.exists():raise ValueError("selftest output directory exists")
    out.mkdir(parents=True)
    tests=[]
    def add(name,ok,detail=""):
        tests.append(dict(test=name,passed=bool(ok),detail=str(detail)))
    base=fixture()
    a=audit_tables(*base)
    add("valid_handbuilt_tables",all(x["passed"] for x in a.checks),[x for x in a.checks if not x["passed"]])
    add("missing_beta_on_error_is_declared",a.a0_missing_beta==4)
    add("full_transition_matrix",len(a.transitions)==16*19)
    add("normal_quantile_full_precision",abs(Q-2.241402727604947)<1e-13)
    add("known_quantile_low",abs(quantile([0,1,2,3],.0125)-.0375)<1e-15)
    add("known_quantile_high",abs(quantile([0,1,2,3],.9875)-2.9625)<1e-15)
    add("known_variance_ddof1",abs(variance([0,1,2,3])-5/3)<1e-15)
    add("equivalent_decimal_keys",effect("-0.20")==effect("-2E-1"))
    add("nearby_effects_not_equal",effect("-0.200000000001")!=effect("-.2"))
    known = []
    for k in range(4):
        b = k * ETA
        known.append(dict(beta=b, beta_true=0, se=ETA, verdict="opposto" if k == 3 else "non deciso",
                          covered=int(k < 3), below=int(k == 3), above=0))
    known_r = recount_group(known, "null")
    add("known_R_and_SD", near(known_r["R"], .6) and near(known_r["sd_z"], math.sqrt(5/3)))
    add("known_rates_and_MCSE", known_r["false"] == 1 and known_r["covered"] == 3
        and near(known_r["coverage"], .75) and near(known_r["false_frac"], .25)
        and near(known_r["coverage_mc_se"], math.sqrt(.75*.25/4))
        and near(known_r["false_mc_se"], math.sqrt(.75*.25/4)))
    # A3 remains deterministic by scenario; corrupt it coherently to isolate this guard.
    obj = copy.deepcopy(base)
    r = next(x for x in obj[0] if x["arm"] == "A3")
    b = r["beta"]; r.update(se=2*ETA, lo=b-Q*2*ETA, hi=b+Q*2*ETA, verdict="non deciso", covered=1, below=0, above=0)
    check = audit_tables(*obj)
    add("A3_fixed_variance_guard", any(x["check"] == "raw_A3_SE_fixed_by_scenario" and not x["passed"] for x in check.checks))
    obj = copy.deepcopy(base)
    r = next(x for x in obj[0] if x["arm"] == "A3")
    r.update(verdict="errore", error="deliberate", se="", lo="", hi="", covered=0, below=0, above=0)
    check = audit_tables(*obj)
    add("A3_never_error_guard", any(x["check"] == "raw_A3_no_error" and not x["passed"] for x in check.checks))
    add("fixture_has_error_transitions", any(r["n"] > 0 and (r["A0_verdict"] == "errore" or r["arm_verdict"] == "errore") for r in a.transitions))
    for v in ("1.1","NaN","Infinity"):
        try:integer(v);ok=False
        except ValueError:ok=True
        add("reject_integer_"+v,ok)
    mutations=[
      ("duplicate_key",0,lambda x:x.append(copy.deepcopy(x[0])),"raw_keys_exact"),
      ("missing_key",0,lambda x:x.pop(),"raw_keys_exact"),
      ("unexpected_effect",0,lambda x:x[0].update(effect="-.0000000001"),"raw_keys_exact"),
      ("fractional_k",0,lambda x:x[0].update(k=".5"),"input_structure_exception"),
      ("wrong_truth",0,lambda x:x[0].update(beta_true=ETA),"raw_truth"),
      ("nonfinite_error_beta",0,lambda x:x[5].update(beta="nan"),"raw_numeric_fields"),
      ("flag_not_binary",0,lambda x:x[0].update(covered=2),"raw_binary_flags"),
      ("wrong_coverage",0,lambda x:x[0].update(covered=1,below=0,above=0),"raw_coverage_tails"),
      ("wrong_tail",0,lambda x:x[0].update(below=1,above=0),"raw_coverage_tails"),
      ("wrong_verdict",0,lambda x:x[0].update(verdict="non deciso"),"raw_verdicts"),
      ("unknown_state",0,lambda x:x[0].update(verdict="supported"),"raw_states"),
      ("asymmetric_interval",0,lambda x:x[0].update(hi=number(x[0]["hi"])+ETA),"raw_half_widths"),
      ("negative_se",0,lambda x:x[0].update(se=-ETA),"raw_finite_intervals"),
      ("wrong_error_payload",0,lambda x:next(r for r in x if r["verdict"]=="errore").update(se=ETA),"raw_error_rows"),
      ("error_reason_missing",0,lambda x:next(r for r in x if r["verdict"]=="errore").update(error=""),"raw_error_rows"),
      ("beta_differs_across_arms",0,lambda x:x[0].update(beta=number(x[0]["beta"])+ETA),"raw_beta_equal_across_arms"),
      ("wrong_producer",0,lambda x:x[0].update(git_commit="different"),"raw_provenance"),
      ("dirty_producer",1,lambda x:x[0].update(git_dirty=1),"summary_provenance"),
      ("wrong_amendment_hash",2,lambda x:x[0].update(sha256_PROTOCOL_T5_ORACLE_A1="wrong"),"paired_provenance"),
      ("metadata_job_count",3,lambda x:x.update(n_jobs=999),"metadata_values"),
      ("metadata_covariance",3,lambda x:x.update(sig2_true=2*ETA**2),"metadata_values"),
      ("metadata_producer",3,lambda x:x.update(git_commit="wrong"),"metadata_provenance"),
      ("A0_reference_verdict",4,lambda x:x[0].update(verdict="non deciso"),"A0_reproduces_reference"),
      ("A0_reference_beta",4,lambda x:x[0].update(beta=ETA),"A0_reproduces_reference"),
      ("A0_reference_se",4,lambda x:x[0].update(se=ETA),"A0_reproduces_reference"),
      ("A0_reference_interval",4,lambda x:x[0].update(lo=ETA),"A0_reproduces_reference"),
      ("A0_reference_missing_key",4,lambda x:x.pop(),"A0_reference_keys_exact"),
      ("summary_duplicate",1,lambda x:x.append(copy.deepcopy(x[0])),"summary_keys_exact"),
      ("summary_extra_column",1,lambda x:x[0].update(unchecked=1),"summary_schema"),
      ("paired_missing_group",2,lambda x:x.pop(),"paired_keys_exact"),
      ("paired_wrong_count",2,lambda x:x[0].update(same=123),"paired_all_fields_recounted"),
    ]
    for col in SUMMARY_FIELDS:
        mutations.append(("summary_column_"+col,1,lambda x,c=col:x[0].update({c:123}),"summary_all_fields_recounted"))
    for name,i,mut,target in mutations:
        obj=copy.deepcopy(base);mut(obj[i]);bad=audit_tables(*obj)
        add(name,any(x["check"]==target and not x["passed"] for x in bad.checks),[x["check"] for x in bad.checks if not x["passed"]])
    # Valid coverage endpoints are closed; verdict boundaries at zero are undecided.
    for which in ("lo","hi"):
        raw=copy.deepcopy(base[0]);r=next(x for x in raw if x["arm"]=="A3")
        b=number(r["beta_true"])+(Q*number(r["se"]) if which=="lo" else -Q*number(r["se"]))
        # Set the endpoint explicitly to avoid pretending subtraction rounds exactly.
        r.update(beta=b,lo=number(r["beta_true"]) if which=="lo" else b-Q*number(r["se"]),
                 hi=number(r["beta_true"]) if which=="hi" else b+Q*number(r["se"]))
        add("closed_coverage_"+which,number(r["lo"])<=number(r["beta_true"])<=number(r["hi"]))
    with tempfile.TemporaryDirectory() as td:
        t=Path(td);p=t/"table.csv"
        write_csv(p,[dict(kind="null",beta="0",note="")]);add("csv_preserves_null",read_csv(p)[0]["kind"]=="null")
        p=t/"log";p.write_text("2000/32000 cataloghi\n")
        add("unfinished_log_rejected_without_output_read",not finished(p))
        p.write_text("32000/32000 cataloghi\nfatto\n");add("finished_marker_accepted",finished(p))
        p=t/"receipt.json";write_csv(t/"SELFTEST.csv",[dict(test="fixture",passed=True)])
        p.write_text(json.dumps(dict(all_passed=True,tests=50,code_sha256="wrong",spec_sha256="spec",selftest_sha256=sha(t/"SELFTEST.csv"))))
        add("stale_selftest_code_rejected",not receipt_ok(p,"code","spec"))
        add("stale_selftest_spec_rejected",not receipt_ok(p,"wrong","different"))
        (t/"docs").mkdir(); (t/SPEC).write_text("hand-built specification")
        (t/"logs").mkdir(); (t/"logs/t5_oracle.log").write_text("2000/32000 cataloghi\n")
        run=t/"results/T5_ORACLE"; run.mkdir(parents=True)
        for f in OUTPUTS: (run/f).write_text("invalid CSV/JSON sentinel: must not be opened")
        p.write_text(json.dumps(dict(all_passed=True,tests=50,code_sha256=sha(Path(__file__)),
            spec_sha256=sha(t/SPEC),selftest_sha256=sha(t/"SELFTEST.csv"))))
        try:
            actual_check(t,t/"audit",p); refused=False
        except ValueError as exc:
            refused="run incomplete" in str(exc)
        add("incomplete_actual_wrapper_refuses_before_read",refused and not (t/"audit").exists())
        (t/"SELFTEST.csv").write_text("tampered receipt table")
        add("selftest_table_hash_guard", not receipt_ok(p,sha(Path(__file__)),sha(t/SPEC)))
    write_csv(out/"SELFTEST.csv",tests)
    receipt=dict(all_passed=all(x["passed"] for x in tests),tests=len(tests),code_sha256=sha(Path(__file__)),
                 spec_sha256=sha(ROOT/SPEC),selftest_sha256=sha(out/"SELFTEST.csv"),
                 fixture="hand-built only; no production outputs read; no RNG or optimizer",**git_info(ROOT))
    (out/"SELFTEST_META.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(f"Selftest: {sum(x['passed'] for x in tests)}/{len(tests)} passed")
    for x in tests:
        if not x["passed"]:print("FAILED: "+x["test"]+" "+x["detail"])
    return 0 if receipt["all_passed"] else 2


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--selftest",action="store_true");modes.add_argument("--check",action="store_true")
    ap.add_argument("--out",type=Path)
    ap.add_argument("--receipt",type=Path,default=ROOT/"results/T5_ORACLE_POSTCHECK_SELFTEST/SELFTEST_META.json")
    a=ap.parse_args()
    try:
        if a.selftest:
            return selftest(a.out or ROOT/"results/T5_ORACLE_POSTCHECK_SELFTEST")
        return actual_check(ROOT,a.out or ROOT/"results/T5_ORACLE_POSTCHECK",a.receipt)
    except (OSError,ValueError,KeyError) as exc:
        print("Refused: "+str(exc),file=sys.stderr);return 2


if __name__=="__main__":
    sys.exit(main())
