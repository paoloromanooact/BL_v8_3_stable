"""Selection of the second MDI-HMI sample (draft docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE_DRAFT.md, §2).

Prepared before the freeze and NOT runnable on the real pool until the frozen protocol exists: --run refuses unless
docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE.md is committed and its SHA-256 is passed with --protocol-sha. --selftest uses
synthetic arcs only. Rules: certified arcs (certificate 1, run r2) of the revision-2 audit, NPIX finite and > 0 on both
records, G10 components of the first sample excluded; per pair and stratum the arc with minimum |HMI longitude|, then
|dT_OBS|, then earliest T_REC, then keys; pairs ordered by SHA-256 of 'MDI_HMI_PILOT_V2|TARPNUM|HARPNUM'; round robin
N central, S central, N lateral, S lateral; at most 5 per stratum; one pair per component; no filling across strata.

    .venv/bin/python scripts/mdi_hmi_second_sample_select.py --selftest
    .venv/bin/python scripts/mdi_hmi_second_sample_select.py --run --protocol-sha <sha> --out <dir>   # after the freeze
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

ORDER = ("N_central", "S_central", "N_lateral", "S_lateral")
CAP = 5
PREFIX = "MDI_HMI_PILOT_V2"
FROZEN = ROOT / "docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE.md"
CERT = ROOT / "results/MDI_SMARP_INVENTORY_REVIEW/footprint_mu_20261118_r2/ARC_CERTIFICATES.csv.gz"
FIRST = ROOT / "data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/selection/PAIRS.csv"
FIRST_SHA = "b9128d9b1f14b39d6bf6992b6f567de826d1ce495b740b0e34da3f1c28759d48"


def pair_key(t, h):
    return hashlib.sha256(f"{PREFIX}|{int(t)}|{int(h)}".encode("ascii")).hexdigest()


def npix_ok(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(x) and x > 0


def select(arcs, excluded_components):
    """arcs: dicts with stratum, TARPNUM, HARPNUM, T_REC_smarp, T_REC_hmi, component, certified (bool), npix_smarp,
    npix_hmi, abslon, abs_dt. Returns (chosen, decisions)."""
    decisions, pool = [], {}
    for a in arcs:
        why = []
        if not a["certified"]:
            why.append("not_certified")
        if not npix_ok(a["npix_smarp"]):
            why.append("npix_smarp")
        if not npix_ok(a["npix_hmi"]):
            why.append("npix_hmi")
        if a["component"] in excluded_components:
            why.append("component_in_first_sample")
        decisions.append(dict(a, reason="|".join(why) or "eligible"))
        if not why:
            pool.setdefault((a["stratum"], a["TARPNUM"], a["HARPNUM"]), []).append(a)
    best = {k: min(v, key=lambda x: (x["abslon"], x["abs_dt"], min(x["T_REC_smarp"], x["T_REC_hmi"]),
                                     (x["T_REC_smarp"], x["T_REC_hmi"], x["TARPNUM"], x["HARPNUM"])))
            for k, v in pool.items()}
    pairs = sorted({(t, h) for _, t, h in pool}, key=lambda th: pair_key(*th))
    used, chosen, taken, cursor = set(), [], {s: 0 for s in ORDER}, {s: 0 for s in ORDER}
    progress = True
    while progress:
        progress = False
        for s in ORDER:
            if taken[s] >= CAP:
                continue
            while cursor[s] < len(pairs):
                t, h = pairs[cursor[s]]
                cursor[s] += 1
                b = best.get((s, t, h))
                if b is None or b["component"] in used:
                    continue
                used.add(b["component"])
                taken[s] += 1
                chosen.append(dict(b, slot=len(chosen) + 1, pair_sha256=pair_key(t, h)))
                progress = True
                break
    return chosen, decisions


def real_arcs():
    """The revision-2 audit arcs with certificate, NPIX and tie-break fields (same inputs as the first sample)."""
    import mdi_hmi_footprint_mu as fm
    arcs = fm.audit_arcs()
    with gzip.open(CERT, "rt") as f:
        cert = {(r["TARPNUM"], r["HARPNUM"], r["T_REC_smarp"], r["T_REC_hmi"]): r for r in csv.DictReader(f)}
    sm = {(x["TARPNUM"], fm.normtime(x["T_REC"])): x for x in fm.rows(fm.SAVED / "RECORDS_smarp_overlap.csv.gz")
          if x["edge"] == "0"}
    hm = {(x["HARPNUM"], fm.normtime(x["T_REC"])): x for x in fm.rows(fm.SAVED / "RECORDS_hmi_overlap.csv.gz")
          if x["edge"] == "0"}
    dts = {(c["TARPNUM"], c["HARPNUM"], fm.normtime(c["smarp_id"].split("|")[1]), fm.normtime(c["hmi_id"].split("|")[1])):
           c["dt_obs_s"] for c in fm.rows(fm.ANALYSIS / "OVERLAP_CANDIDATES.csv.gz")}
    out = []
    for a in arcs:
        k = (a["TARPNUM"], a["HARPNUM"], a["smarp"][2], a["hmi"][2])
        h = hm[(a["HARPNUM"], a["hmi"][2])]
        s = sm[(a["TARPNUM"], a["smarp"][2])]
        lon = (float(h["CRVAL1"]) - float(h["CRLN_OBS"]) + 180) % 360 - 180
        out.append(dict(stratum=a["stratum"], TARPNUM=a["TARPNUM"], HARPNUM=a["HARPNUM"], T_REC_smarp=a["smarp"][2],
                        T_REC_hmi=a["hmi"][2], component=a["component"], quality_mdi=a["quality_mdi"],
                        certified=cert[k]["category"] == "certified_both", npix_smarp=s["NPIX"], npix_hmi=h["NPIX"],
                        abslon=abs(lon), abs_dt=abs(float(dts[k]))))
    return out


def run(out, protocol_sha):
    if not FROZEN.exists() or hashlib.sha256(FROZEN.read_bytes()).hexdigest() != protocol_sha:
        sys.exit("frozen protocol missing or SHA-256 differs: selection not allowed before the freeze")
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(FROZEN)], cwd=ROOT, capture_output=True).returncode:
        sys.exit("frozen protocol not committed")
    out = Path(out)
    if out.exists():
        sys.exit("refusing to overwrite")
    if hashlib.sha256(FIRST.read_bytes()).hexdigest() != FIRST_SHA:
        sys.exit("first-sample manifest changed")
    excluded = {r["component"] for r in csv.DictReader(open(FIRST))}
    chosen, decisions = select(real_arcs(), excluded)
    out.mkdir(parents=True)
    for name, rows in (("PAIRS.csv", chosen), ("ARC_DECISIONS.csv", decisions)):
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    meta = dict(protocol_sha256=protocol_sha, first_sample_sha256=FIRST_SHA, cap=CAP, prefix=PREFIX,
                per_stratum={s: sum(c["stratum"] == s for c in chosen) for s in ORDER}, n=len(chosen),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out / "RECEIPT.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=1))
    return 0


def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")

    def arc(st, t, h, comp, **kw):
        a = dict(stratum=st, TARPNUM=str(t), HARPNUM=str(h), T_REC_smarp="2010.06.01_00:00:00_TAI",
                 T_REC_hmi="2010.06.01_00:00:00_TAI", component=comp, quality_mdi="0x00000200", certified=True,
                 npix_smarp="100", npix_hmi="1000", abslon=5.0, abs_dt=10.0)
        a.update(kw)
        return a
    arcs = [arc(s, 100 + i, 200 + i, f"C{s}{i}") for s in ORDER for i in range(8)]
    ch, dec = select(arcs, set())
    ok("five per stratum, round robin order", [c["stratum"] for c in ch[:4]] == list(ORDER)
       and all(sum(c["stratum"] == s for c in ch) == 5 for s in ORDER), len(ch))
    ok("one pair per component", len({c["component"] for c in ch}) == len(ch))
    bad = [arc("N_central", 1, 2, "X", npix_smarp="MISSING"), arc("N_central", 3, 4, "Y", npix_hmi="0"),
           arc("N_central", 5, 6, "Z", npix_hmi="nan"), arc("N_central", 7, 8, "W", certified=False),
           arc("N_central", 9, 10, "OLD")]
    ch2, dec2 = select(bad, {"OLD"})
    ok("NPIX missing/zero/NaN, uncertified and first-sample components excluded with reasons",
       ch2 == [] and [d["reason"] for d in dec2] == ["npix_smarp", "npix_hmi", "npix_hmi", "not_certified",
                                                    "component_in_first_sample"])
    shared = [arc("N_central", 1, 2, "S"), arc("S_central", 1, 2, "S"), arc("S_central", 3, 4, "T")]
    ch3, _ = select(shared, set())
    ok("a component taken in one stratum is skipped in the next",
       [(c["stratum"], c["component"]) for c in ch3] == [("N_central", "S"), ("S_central", "T")])
    tie = [arc("N_lateral", 1, 2, "U", abslon=20.0, T_REC_smarp="2010.06.02_00:00:00_TAI", T_REC_hmi="2010.06.02_00:00:00_TAI"),
           arc("N_lateral", 1, 2, "U", abslon=16.0, abs_dt=200.0), arc("N_lateral", 1, 2, "U", abslon=16.0, abs_dt=20.0)]
    ch4, _ = select(tie, set())
    ok("arc choice: min |lon|, then |dT|", ch4[0]["abslon"] == 16.0 and ch4[0]["abs_dt"] == 20.0)
    ok("SHA order uses the V2 prefix", pair_key(1, 2) == hashlib.sha256(b"MDI_HMI_PILOT_V2|1|2").hexdigest()
       and pair_key("007", "02") == pair_key(7, 2))
    ok("empty stratum leaves places empty (no filling)", all(sum(c["stratum"] == s for c in
       select([arc("N_central", i, i + 50, f"K{i}") for i in range(9)], set())[0]) == (5 if s == "N_central" else 0)
       for s in ORDER))
    ok("--run refuses before the freeze", not FROZEN.exists())
    # real pool counted without ordering or selecting (no pair is revealed): must match the draft §2
    excluded = {r["component"] for r in csv.DictReader(open(FIRST))}
    _, dec = select([], set())
    real = real_arcs()
    elig = [a for a in real if a["certified"] and npix_ok(a["npix_smarp"]) and npix_ok(a["npix_hmi"])
            and a["component"] not in excluded]
    ok("real eligible pool = draft §2 (1217 arcs, 47 pairs, 47 components)",
       (len(elig), len({(a["TARPNUM"], a["HARPNUM"]) for a in elig}), len({a["component"] for a in elig})) == (1217, 47, 47),
       (len(elig), len({a["component"] for a in elig})))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--protocol-sha")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.run and a.out and a.protocol_sha:
        if not selftest():
            return 1
        return run(a.out, a.protocol_sha)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
