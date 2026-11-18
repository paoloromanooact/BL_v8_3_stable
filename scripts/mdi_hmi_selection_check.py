"""Independent re-derivation of the 12 MDI-HMI pairs from the frozen protocol (6d6fd12, §3) and Claude's certificate
run r2; written without reading Codex's select_pairs.py, then compared with its manifest. Local only, no network.

    .venv/bin/python scripts/mdi_hmi_selection_check.py
"""
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mdi_hmi_footprint_mu as fm  # noqa: E402

CERT = ROOT / "results/MDI_SMARP_INVENTORY_REVIEW/footprint_mu_20261118_r2/ARC_CERTIFICATES.csv.gz"
ORDER = ("N_central", "S_central", "N_lateral", "S_lateral")


def sha_key(t, h):
    return hashlib.sha256(f"MDI_HMI_PILOT_V1|{int(t)}|{int(h)}".encode("ascii")).hexdigest()


def main():
    arcs = fm.audit_arcs()
    with gzip.open(CERT, "rt") as f:
        cert = {(r["TARPNUM"], r["HARPNUM"], r["T_REC_smarp"], r["T_REC_hmi"]): r for r in csv.DictReader(f)}
    # recompute HMI Stonyhurst longitude and dT_OBS for the tie-break (same saved inputs as the audit)
    meta = json.loads((fm.ANALYSIS / "META.json").read_text())
    hm = {(x["HARPNUM"], fm.normtime(x["T_REC"])): x for x in fm.rows(fm.SAVED / "RECORDS_hmi_overlap.csv.gz")
          if x["edge"] == "0"}
    cands = {(p["smarp_id"], p["hmi_id"]): p for p in fm.rows(fm.ANALYSIS / "OVERLAP_CANDIDATES.csv.gz")}
    assert meta  # inputs already hash-checked by audit_arcs
    pool = {}       # (stratum, T, H) -> list of certified arcs
    for a in arcs:
        k = (a["TARPNUM"], a["HARPNUM"], a["smarp"][2], a["hmi"][2])
        if cert[k]["category"] != "certified_both":
            continue
        h = hm[(a["HARPNUM"], a["hmi"][2])]
        lon = (float(h["CRVAL1"]) - float(h["CRLN_OBS"]) + 180) % 360 - 180
        p = [c for (sid, hid), c in cands.items()
             if c["TARPNUM"] == a["TARPNUM"] and c["HARPNUM"] == a["HARPNUM"]
             and fm.normtime(sid.split("|")[1]) == a["smarp"][2] and fm.normtime(hid.split("|")[1]) == a["hmi"][2]]
        assert len(p) == 1
        dt = abs(float(p[0]["dt_obs_s"]))
        pool.setdefault((a["stratum"], a["TARPNUM"], a["HARPNUM"]), []).append(
            dict(arc=a, abslon=abs(lon), dt=dt, key=(a["smarp"][2], a["hmi"][2], a["TARPNUM"], a["HARPNUM"])))
    best = {}
    for k, lst in pool.items():
        best[k] = min(lst, key=lambda x: (x["abslon"], x["dt"], min(x["key"][0], x["key"][1]), x["key"]))
    pairs = sorted({(t, h) for _, t, h in pool}, key=lambda th: sha_key(*th))
    used, chosen, taken = set(), [], {s: 0 for s in ORDER}
    cursor = {s: 0 for s in ORDER}
    progress = True
    while progress:
        progress = False
        for s in ORDER:
            if taken[s] >= 3:
                continue
            while cursor[s] < len(pairs):
                t, h = pairs[cursor[s]]
                cursor[s] += 1
                if (s, t, h) not in best:
                    continue
                comp = best[(s, t, h)]["arc"]["component"]
                if comp in used:
                    continue
                used.add(comp)
                b = best[(s, t, h)]
                chosen.append(dict(stratum=s, TARPNUM=t, HARPNUM=h, T_REC_smarp=b["key"][0], T_REC_hmi=b["key"][1],
                                   component=comp, quality_mdi=b["arc"]["quality_mdi"], abslon=round(b["abslon"], 4)))
                taken[s] += 1
                progress = True
                break
    for c in chosen:
        print(c)
    print(json.dumps(dict(per_stratum=taken, n=len(chosen), distinct_components=len(used))))
    return chosen


if __name__ == "__main__":
    main()
