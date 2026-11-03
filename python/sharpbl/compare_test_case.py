"""Confronto v8.3 (legacy) e v8.4 sul caso di prova 2024-05-08 03:12 TAI.

Uso: .venv/bin/python python/sharpbl/compare_test_case.py [cartella_fits]
Scrive output/test_20240508_compare.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import geometry as geo  # noqa: E402
from sharpbl import measure  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COLS = ["phi_mx", "d_cm", "lat_mean_deg", "tilt_reduced_deg", "sintilt", "hale_sign",
        "s_bl", "valid_bl", "diagnostic_reason"]


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/sharp/test_20240508"
    rows = []
    for f in sorted(src.glob("*.Br.fits")):
        br, h = geo.read_sharp(f)
        bm, _ = geo.read_sharp(Path(str(f).replace(".Br.", ".bitmap.")))
        runs = {
            "legacy": measure.measure_legacy(br, bm, h),
            "v84_bmap1": measure.measure_v84(br, bm, h, bmap_min=1),
            "v84_bmap33": measure.measure_v84(br, bm, h, bmap_min=33),
        }
        row = {"harpnum": h["HARPNUM"], "noaa_ars": h.get("NOAA_ARS", "")}
        for name, out in runs.items():
            for c in COLS:
                row[f"{name}:{c}"] = out[c]
        row["v84_bmap33:d_axial_bal_g"] = runs["v84_bmap33"]["d_axial_bal_g"]
        rows.append(row)
    df = pd.DataFrame(rows)
    out = ROOT / "output/test_20240508_compare.csv"
    df.to_csv(out, index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    for c in ["s_bl", "tilt_reduced_deg", "lat_mean_deg", "d_cm", "phi_mx", "diagnostic_reason"]:
        print(f"\n== {c}")
        print(df[["harpnum"] + [f"{n}:{c}" for n in ("legacy", "v84_bmap1", "v84_bmap33")]]
              .to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nscritto {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
