"""Descriptive homogeneity check of the DPD activity series for the T3-on-MWO draft (docs/PROTOCOL_T3_MWO_DRAFT.md §3).

Uses only DPD daily/group rows (no tilt) and SILSO. For each year 1974-2012: share of DPD observation days by source
observatory (daily rows, columns 23-26), number of observed days, annual mean of the daily corrected WS area, annual mean
of the total SILSO number on the same months, their ratio; for 1992-2012 the hemispheric correlation of the monthly DPD
activity with SILSO hemispheric. Output: results/DPD_ACTIVITY_HOMOGENEITY/. No decision depends on it (descriptive).

    .venv/bin/python scripts/dpd_activity_homogeneity.py --run
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DPD = ROOT / "data/sharp/external_DPD_20261118"
SILSO_TOT = ROOT / "ancillary/SILSO_TOT/SN_m_tot_V2.0.txt"
SILSO_HEM = ROOT / "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv"
OUT = ROOT / "results/DPD_ACTIVITY_HOMOGENEITY"


def daily():
    rows = []
    for line in (DPD / "dailyDPD1974_2016.txt").read_text().splitlines():
        if not line.startswith("d "):
            continue
        t = line.split()
        if len(t) < 12:                       # day without observation
            continue
        # fields from the end: corrected WS area, Julian date, P, B0; source code after the time when present
        rows.append(dict(date=pd.Timestamp(f"{t[1]}-{t[2]}-{t[3]}"), obs=t[7] if t[7].isalpha() else "(none)",
                         ws_corr=int(t[-4])))
    d = pd.DataFrame(rows)
    return d[(d.date >= "1974-01-01") & (d.date < "2013-01-01")]


def hemispheric_monthly():
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("feas", ROOT / "scripts/t3_dpd_feasibility.py")
    F = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(F)
    g = F.read_groups()
    days = sorted(set(daily().date))
    g = g.assign(hem=np.where(g.lat >= 0, "N", "S"))
    dd = g.groupby(["date", "hem"]).area.sum().unstack(fill_value=0).reindex(days, fill_value=0)
    return dd.groupby(dd.index.to_period("M")).mean()


def run():
    if OUT.exists():
        sys.exit("refusing to overwrite")
    d = daily()
    d["year"] = d.date.dt.year
    share = pd.crosstab(d.year, d.obs, normalize="index")
    days = d.groupby("year").size().rename("observed_days")
    s = pd.read_csv(SILSO_TOT, sep=r"\s+", header=None, usecols=[0, 1, 3], names=["y", "m", "sn"])
    s["ym"] = pd.PeriodIndex(year=s.y, month=s.m, freq="M")
    s = s.set_index("ym").sn
    dm = d.groupby(d.date.dt.to_period("M")).ws_corr.mean()
    sm = s.reindex(dm.index)
    ann = pd.DataFrame(dict(dpd_area=dm.groupby(dm.index.year).mean(), silso=sm.groupby(sm.index.year).mean()))
    ann["ratio_area_per_sn"] = ann.dpd_area / ann.silso
    ann = ann.join(days)
    ann["main_source"] = share.idxmax(axis=1)
    ann["main_source_share"] = share.max(axis=1)
    hm = hemispheric_monthly()
    h = pd.read_csv(SILSO_HEM, sep=";", header=None).iloc[:, [0, 1, 4, 5]]
    h.columns = ["y", "m", "N", "S"]
    h.index = pd.PeriodIndex(year=h.y, month=h.m, freq="M")
    h = h[["N", "S"]].replace(-1.0, np.nan)
    common = hm.index.intersection(h.index)
    common = common[(common >= pd.Period("1992-01", "M")) & (common <= pd.Period("2012-12", "M"))]
    corr = {k: float(np.corrcoef(hm.loc[common, k], h.loc[common, k])[0, 1]) for k in ("N", "S")}
    OUT.mkdir(parents=True)
    ann.to_csv(OUT / "ANNUAL.csv")
    share.to_csv(OUT / "SOURCE_SHARE_BY_YEAR.csv")
    meta = dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                inputs_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (DPD / "dailyDPD1974_2016.txt", SILSO_TOT, SILSO_HEM)},
                hemispheric_monthly_corr_1992_2012=corr, n_months_common=len(common),
                git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(ann.round(3).to_string())
    print(json.dumps(corr))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    sys.exit(run() if ap.parse_args().run else 1)
