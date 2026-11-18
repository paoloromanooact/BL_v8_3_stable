"""Independent re-derivation of the second-sample selection (frozen protocol bbd719c §2), written separately from
scripts/mdi_hmi_second_sample_select.py (pandas, own eligibility, own round robin); compares with the manifest.

    .venv/bin/python scripts/mdi_hmi_second_sample_check.py <selection dir>
"""
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mdi_hmi_footprint_mu as fm  # noqa: E402  (arc audit and saved inputs, shared with the first-sample check)

CERT = ROOT / "results/MDI_SMARP_INVENTORY_REVIEW/footprint_mu_20261118_r2/ARC_CERTIFICATES.csv.gz"
FIRST = ROOT / "data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/selection/PAIRS.csv"
ORDER = ["N_central", "S_central", "N_lateral", "S_lateral"]


def main(seldir):
    arcs = pd.DataFrame([dict(stratum=a["stratum"], T=a["TARPNUM"], H=a["HARPNUM"], ts=a["smarp"][2], th=a["hmi"][2],
                              comp=a["component"]) for a in fm.audit_arcs()])
    cert = pd.read_csv(CERT, dtype=str)
    cert = cert[cert.category == "certified_both"][["TARPNUM", "HARPNUM", "T_REC_smarp", "T_REC_hmi"]]
    cert.columns = ["T", "H", "ts", "th"]
    arcs = arcs.merge(cert, on=["T", "H", "ts", "th"])
    sm = pd.DataFrame(fm.rows(fm.SAVED / "RECORDS_smarp_overlap.csv.gz"))
    hm = pd.DataFrame(fm.rows(fm.SAVED / "RECORDS_hmi_overlap.csv.gz"))
    sm = sm[sm.edge == "0"].assign(ts=lambda x: x.T_REC.map(fm.normtime))[["TARPNUM", "ts", "NPIX"]].rename(columns={"TARPNUM": "T", "NPIX": "ns"})
    hm = hm[hm.edge == "0"].assign(th=lambda x: x.T_REC.map(fm.normtime))[["HARPNUM", "th", "NPIX", "CRVAL1", "CRLN_OBS"]].rename(columns={"HARPNUM": "H", "NPIX": "nh"})
    arcs = arcs.merge(sm, on=["T", "ts"]).merge(hm, on=["H", "th"])
    num = lambda s: pd.to_numeric(s, errors="coerce")  # noqa: E731
    arcs = arcs[(num(arcs.ns) > 0) & (num(arcs.nh) > 0)]
    used = set(pd.read_csv(FIRST, dtype=str).component)
    arcs = arcs[~arcs.comp.isin(used)]
    cand = pd.DataFrame(fm.rows(fm.ANALYSIS / "OVERLAP_CANDIDATES.csv.gz"))
    cand["ts"] = cand.smarp_id.str.split("|").str[1].map(fm.normtime)
    cand["th"] = cand.hmi_id.str.split("|").str[1].map(fm.normtime)
    arcs = arcs.merge(cand[["TARPNUM", "HARPNUM", "ts", "th", "dt_obs_s"]].rename(columns={"TARPNUM": "T", "HARPNUM": "H"}),
                      on=["T", "H", "ts", "th"])
    arcs["alon"] = ((num(arcs.CRVAL1) - num(arcs.CRLN_OBS) + 180) % 360 - 180).abs()
    arcs["adt"] = num(arcs.dt_obs_s).abs()
    arcs["tmin"] = arcs[["ts", "th"]].min(axis=1)
    best = arcs.sort_values(["alon", "adt", "tmin", "ts", "th", "T", "H"]).groupby(["stratum", "T", "H"]).head(1)
    keyhash = lambda t, h: hashlib.sha256(f"MDI_HMI_PILOT_V2|{int(t)}|{int(h)}".encode()).hexdigest()  # noqa: E731
    order = sorted({(t, h) for t, h in zip(best["T"], best["H"])}, key=lambda p: keyhash(*p))
    bidx = {(r.stratum, r.T, r.H): r for r in best.itertuples()}
    used_c, picks, pos, took = set(), [], {s: 0 for s in ORDER}, {s: 0 for s in ORDER}
    moved = True
    while moved:
        moved = False
        for s in ORDER:
            while took[s] < 5 and pos[s] < len(order):
                t, h = order[pos[s]]
                pos[s] += 1
                r = bidx.get((s, t, h))
                if r is None or r.comp in used_c:
                    continue
                used_c.add(r.comp)
                took[s] += 1
                picks.append((s, t, h, r.ts, r.th, r.comp))
                moved = True
                break
    man = pd.read_csv(Path(seldir) / "PAIRS.csv", dtype=str)
    mine = [(s, t, h, ts, th, c) for s, t, h, ts, th, c in picks]
    theirs = [(r.stratum, r.TARPNUM, r.HARPNUM, r.smarp_record.split("|")[1], r.hmi_record.split("|")[1], r.component)
              for r in man.itertuples()]
    res = dict(same_set=set(mine) == set(theirs), same_order=mine == theirs, n_mine=len(mine), n_manifest=len(theirs),
               per_stratum=took, manifest_sha256=hashlib.sha256((Path(seldir) / "PAIRS.csv").read_bytes()).hexdigest())
    print(json.dumps(res, indent=1))
    return 0 if res["same_set"] and res["same_order"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
