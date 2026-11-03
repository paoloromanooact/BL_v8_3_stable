"""Fattoriale esplorativo 2x2x2: maschera (M), geometria (G), ciclo (C) sugli stessi record.

ESPLORATIVO, serie gia' osservata (docs/EXPLORATORY_PLAN.md §2-§3).

Uso: .venv/bin/python python/sharpbl/factorial.py [--workers 8]
Scrive in results/EXPLORATORY/:
  FACTORIAL_BY_RECORD.csv.gz     una riga per record e combinazione (8 x 14195)
  FACTORIAL_REPRODUCTION.csv     confronto delle combinazioni estreme con il catalogo P1 su disco
Fattori: M in {1, 33} (bitmap minima), G in {legacy, v84} (measure_legacy / measure_v84),
C in {date, p1c} (cycle_mode). (1, legacy, date) = metodo v8.3; (33, v84, p1c) = metodo v8.4.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import geometry as geo  # noqa: E402
from sharpbl import measure  # noqa: E402
from sharpbl.cycle_boundary import load_boundary  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

OUT = ROOT / "results/EXPLORATORY"
FITS = ROOT / "data/sharp/fits"
STATUS = "esplorativo, serie gia' osservata"
COMBOS = [(m, g, c) for m in (1, 33) for g in ("legacy", "v84") for c in ("date", "p1c")]
FIELDS = ["valid_bl", "quality_string", "diagnostic_reason", "phi_mx", "d_cm", "lat_mean_deg", "tilt_deg",
          "tilt_reduced_deg", "sintilt", "leading_sign", "expected_leading_sign", "hale_sign", "cycle",
          "cycle_state", "s_bl", "nmask", "npos", "nneg"]
_B = None


def _init():
    global _B
    _B = load_boundary()


def one_record(args):
    harp, t_rec = args
    folder = record_dir(FITS, t_rec)
    stem = file_stem(harp, t_rec)
    br, h = geo.read_sharp(folder / f"{stem}.Br.fits")
    bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
    rows = []
    for m, g, c in COMBOS:
        if g == "legacy":
            r = measure.measure_legacy(br, bm, h, bmap_min=m, cycle_mode=c, boundary=_B)
        else:
            r = measure.measure_v84(br, bm, h, bmap_min=m, boundary=_B, cycle_mode=c)
        row = {"HARPNUM": harp, "T_REC": t_rec, "M": m, "G": g, "C": c}
        row.update({k: r.get(k, np.nan) for k in FIELDS})
        rows.append(row)
    return rows


# ---------------------------------------------------------------- riproduzione esatta (piano §3)

FLAG_COLS = ["valid_bl", "quality_string", "diagnostic_reason", "leading_sign", "hale_sign", "cycle"]
NUM_SCALE = {"phi_mx": 1.0, "d_cm": 1.0, "lat_mean_deg": 1.0, "tilt_reduced_deg": 1.0, "sintilt": 1e-3, "s_bl": 1.0}


def compare(new, ref, flags, nums):
    res = []
    for c in flags:
        a, b = new[c], ref[c]
        same = (a.astype(str) == b.astype(str)) | (a.isna() & b.isna())
        res.append(dict(column=c, kind="flag", n=len(a), n_mismatch=int((~same).sum()), max_rel=np.nan))
    for c, scale in nums.items():
        a, b = new[c].astype(float), ref[c].astype(float)
        both_nan = a.isna() & b.isna()
        tol = 1e-9 * np.maximum(np.maximum(a.abs(), b.abs()), scale)
        ok = both_nan | ((a - b).abs() <= tol)
        rel = ((a - b).abs() / np.maximum(np.maximum(a.abs(), b.abs()), scale))[~both_nan]
        res.append(dict(column=c, kind="numeric", n=len(a), n_mismatch=int((~ok).sum()),
                        max_rel=float(rel.max()) if len(rel) else 0.0))
    return pd.DataFrame(res)


def reproduction(fac, cat):
    """(1, legacy, date) contro le colonne leg_* e (33, v84, p1c) contro le colonne v8.4 del catalogo su disco."""
    key = ["HARPNUM", "T_REC"]
    leg = fac[(fac.M == 1) & (fac.G == "legacy") & (fac.C == "date")].merge(cat, on=key, suffixes=("", "_cat"))
    ref_leg = pd.DataFrame({c: leg[f"leg_{c}"] for c in ["valid_bl", "quality_string", "diagnostic_reason",
                                                         "leading_sign", "hale_sign", "cycle", "phi_mx", "d_cm",
                                                         "lat_mean_deg", "tilt_reduced_deg", "sintilt", "s_bl"]})
    t1 = compare(leg, ref_leg, FLAG_COLS, NUM_SCALE).assign(combination="(1, legacy, date) vs leg_* del catalogo")
    v = fac[(fac.M == 33) & (fac.G == "v84") & (fac.C == "p1c")].merge(cat, on=key, suffixes=("", "_cat"))
    ref_v = pd.DataFrame({c: v[f"{c}_cat"] for c in FLAG_COLS + ["cycle_state"] + list(NUM_SCALE)})
    t2 = compare(v, ref_v, FLAG_COLS + ["cycle_state"], NUM_SCALE).assign(
        combination="(33, v84, p1c) vs colonne v8.4 del catalogo")
    return pd.concat([t1, t2], ignore_index=True)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    st = stamp(("P1", "P1b", "P1c", "P1d", "P1e"))
    if st.get("git_dirty"):
        print("modifiche non committate: il fattoriale registra il commit e richiede un albero pulito")
        return 2
    cat_path = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
    st.update(status=STATUS, input_catalogue_sha256=sha_file(cat_path))
    cat = pd.read_csv(cat_path, low_memory=False)
    jobs = list(zip(cat["HARPNUM"].astype(int), cat["T_REC"]))
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init) as pool:
        rows = [r for part in pool.map(one_record, jobs, chunksize=20) for r in part]
    fac = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    fac.assign(**st).to_csv(OUT / "FACTORIAL_BY_RECORD.csv.gz", index=False)
    rep = reproduction(fac, cat)
    rep.assign(**st).to_csv(OUT / "FACTORIAL_REPRODUCTION.csv", index=False)
    print(rep.to_string(index=False))
    ok = int(rep["n_mismatch"].sum() == 0)
    print("RIPRODUZIONE ESATTA:", "superata" if ok else "NON superata")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
