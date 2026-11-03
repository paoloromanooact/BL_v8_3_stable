"""Selezione di un record primario e di uno di controllo per HARP (P1 §4, P1b §1).

Uso: .venv/bin/python python/sharpbl/select_records.py
Legge data/sharp/metadata/*.csv, scrive results/P1/P1_RECORD_SELECTION.csv
(una riga per record da scaricare, con ruolo primary/control/both) e
results/P1/P1_NO_CM_RECORD.csv (HARP senza record primario).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl.provenance import ROOT, stamp  # noqa: E402

QUAL_OK = {0, 0x80}
LON_PRIMARY = 30.0
LON_CONTROL = 60.0


def load_metadata(folder: Path) -> pd.DataFrame:
    files = sorted(folder.glob("sharp_meta_*.csv"))
    df = pd.concat((pd.read_csv(f) for f in files if f.stat().st_size > 10), ignore_index=True)
    df["t"] = pd.to_datetime(df["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    return df


def select(df: pd.DataFrame):
    cand = df[df["QUALITY"].isin(QUAL_OK) & (df["USFLUX"] > 0)].copy()
    cand["abs_lon"] = cand["LON_FWT"].abs()
    p = cand[cand["abs_lon"] <= LON_PRIMARY]
    prim = p.sort_values(["HARPNUM", "abs_lon", "t"]).groupby("HARPNUM").head(1)
    c = cand[(cand["abs_lon"] <= LON_CONTROL) & cand["HARPNUM"].isin(prim["HARPNUM"])]
    ctrl = c.sort_values(["HARPNUM", "USFLUX", "t"], ascending=[True, False, True]).groupby("HARPNUM").head(1)
    prim = prim.assign(role="primary")
    ctrl = ctrl.assign(role="control")
    both = pd.concat([prim, ctrl])
    roles = both.groupby(["HARPNUM", "T_REC"])["role"].agg(lambda r: "both" if len(r) > 1 else r.iloc[0])
    recs = both.drop_duplicates(["HARPNUM", "T_REC"]).drop(columns="role")
    recs = recs.merge(roles.rename("role").reset_index(), on=["HARPNUM", "T_REC"])
    recs["qual_0x80"] = (recs["QUALITY"] == 0x80).astype(int)
    no_cm = df.groupby("HARPNUM").agg(t_first=("t", "min"), t_last=("t", "max"),
                                      max_usflux=("USFLUX", "max"), noaa_num=("NOAA_NUM", "max"))
    no_cm = no_cm[~no_cm.index.isin(prim["HARPNUM"])].reset_index()
    return recs.sort_values(["t", "HARPNUM"]).reset_index(drop=True), no_cm


def main() -> int:
    df = load_metadata(ROOT / "data/sharp/metadata")
    recs, no_cm = select(df)
    out = ROOT / "results/P1"
    out.mkdir(parents=True, exist_ok=True)
    st = stamp()
    cols = ["HARPNUM", "T_REC", "role", "QUALITY", "qual_0x80", "LON_FWT", "LAT_FWT", "USFLUX",
            "NOAA_NUM", "NOAA_AR", "NOAA_ARS", "CRPIX1", "CRPIX2"]
    recs[cols].assign(**st).to_csv(out / "P1_RECORD_SELECTION.csv", index=False)
    no_cm.assign(**st).to_csv(out / "P1_NO_CM_RECORD.csv", index=False)
    print(f"HARP nei metadati {df['HARPNUM'].nunique()}, con primario "
          f"{(recs['role'] != 'control').sum()}, senza {len(no_cm)}; record {len(recs)} "
          f"(both {(recs['role'] == 'both').sum()}); qual_0x80 {recs['qual_0x80'].sum()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
