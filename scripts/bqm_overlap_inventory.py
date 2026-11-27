"""BQ-M preparation: inventory of the records shared between instruments (metadata only; no tilt, Joy or difference
column is read). Plan docs/BL_WORK_PLAN.md §3bis, assigned to Claude.

Reads only identity/status columns:
- MWO R4 isolated catalogue (noaa, day, CR, cycle, hemisphere, epoch, resolution class);
- the white-light bridge status of the MWO records (WL_TILTS.csv: wl_status only);
- the MWO-HMI matched records of the T3-MWO comparison S2 (S2_P1_MATCHED.csv: noaa, day, epoch, hemisphere only);
- the HMI T3 design (p2f_pilot.build_design, design columns) with NOAA_AR from the P1 catalogue;
- MDI: pilot L2 records (rule, noaa, day, status only) and the MDI-MWO identity check rows (status columns only).

    .venv/bin/python scripts/bqm_overlap_inventory.py --out reviews/BQM_OVERLAP_INVENTORY_20261125
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
R4 = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
WL = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/COMPARISONS/WL_TILTS.csv"
S2 = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/COMPARISONS/S2_P1_MATCHED.csv"
P1 = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
MDI_L2 = ROOT / "results/MDI_PILOT_L2/L2_RECORDS.csv"
MDI_ID = ROOT / "results/MDI_PILOT_MWO_IDENTITY/ROWS.csv"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def noaa_num(x):
    """Numeric part of a NOAA label (R4 stores strings, some with a letter suffix such as '11620p'); NaN if none."""
    return pd.to_numeric(pd.Series(x, dtype=str).str.extract(r"^(\d+)")[0], errors="coerce")


def run():
    out = {}
    r4 = pd.read_csv(R4, usecols=["noaa", "day_utc", "carrington_rotation", "cycle", "hemisphere", "epoch", "resolution_class"], dtype={"noaa": str})
    suffix = r4.noaa.str.extract(r"^\d+(\D*)$")[0]
    r4["noaa_n"] = noaa_num(r4.noaa).to_numpy()
    out["mwo_r4_isolated"] = dict(records=len(r4), first_day=str(r4.day_utc.min()), last_day=str(r4.day_utc.max()),
                                  by_cycle_hemisphere={f"{c}{h}": int(n) for (c, h), n in r4.groupby(["cycle", "hemisphere"]).size().items()},
                                  by_epoch={str(k): int(v) for k, v in r4.epoch.value_counts().sort_index().items()},
                                  by_resolution={str(k): int(v) for k, v in r4.resolution_class.value_counts().items()},
                                  noaa_label_suffixes={str(k): int(v) for k, v in suffix.fillna("unparsed").value_counts().items()})
    wl = pd.read_csv(WL, usecols=["noaa", "day", "epoch", "hemisphere", "wl_status"], dtype={"noaa": str})
    m = wl.merge(r4.rename(columns={"day_utc": "day"})[["noaa", "day", "cycle"]], on=["noaa", "day"], how="left", validate="one_to_one")
    out["white_light_bridge"] = dict(status={k: int(v) for k, v in wl.wl_status.value_counts().items()},
                                     ok_by_cycle={str(int(k)): int(v) for k, v in m[m.wl_status == "ok"].cycle.value_counts().sort_index().items()},
                                     unmatched_to_r4=int(m.cycle.isna().sum()))
    s2 = pd.read_csv(S2, usecols=["noaa", "day", "epoch", "hemisphere"])
    out["mwo_hmi_matched_S2"] = dict(records=len(s2), first_day=str(s2.day.min()), last_day=str(s2.day.max()),
                                     by_hemisphere={k: int(v) for k, v in s2.hemisphere.value_counts().items()},
                                     distinct_noaa=int(s2.noaa.nunique()))
    from sharpbl import p2f_pilot as P
    d = P.build_design()
    noaa = pd.read_csv(P1, usecols=["HARPNUM", "NOAA_AR"], low_memory=False).drop_duplicates("HARPNUM")
    d = d.merge(noaa, on="HARPNUM", how="left", validate="one_to_one")
    in_mwo = d.NOAA_AR.isin(set(r4.noaa_n.dropna()))
    in_s2 = d.NOAA_AR.isin(set(noaa_num(s2.noaa).dropna()))
    out["hmi_T3_design_vs_mwo"] = dict(design_records=len(d), with_noaa=int((d.NOAA_AR > 0).sum()),
                                       noaa_in_mwo_r4=int(in_mwo.sum()), noaa_in_S2_matched=int(in_s2.sum()),
                                       by_cycle_in_mwo={str(int(k)): int(v) for k, v in d[in_mwo].cyc.value_counts().sort_index().items()})
    l2 = pd.read_csv(MDI_L2, usecols=["rule", "noaa", "day", "status", "main_status"])
    ident = pd.read_csv(MDI_ID, usecols=["source", "noaa", "status", "identical", "epoch", "hemisphere"])
    out["mdi"] = dict(full_catalogue="not built (decision pending after Q4)", pilot_L2_records=len(l2),
                      pilot_L2_status={str(k): int(v) for k, v in l2.status.value_counts().items()},
                      pilot_L2_main_status={str(k): int(v) for k, v in l2.main_status.value_counts().items()},
                      pilot_noaa_in_mwo_r4=int(noaa_num(l2.noaa).isin(set(r4.noaa_n.dropna())).sum()),
                      mwo_identity_rows={str(k): int(v) for k, v in ident.source.value_counts().items()})
    out["inputs_sha256"] = {str(p.relative_to(ROOT)): sha(p) for p in (R4, WL, S2, P1, MDI_L2, MDI_ID)}
    out["script_sha256"] = sha(__file__)
    out["note"] = "metadata/status columns only; counts of shared records, not estimates"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    res = run()
    a.out.mkdir(parents=True)
    (a.out / "INVENTORY.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "inputs_sha256"}, indent=1))
