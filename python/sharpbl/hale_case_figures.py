"""Diagnostiche di casi rappresentativi delle transizioni Hale v8.3 -> v8.4 (ESPLORATIVO).

Per ogni caso: Br con il contorno della maschera bitmap >= 1 e >= 33, i centroidi di polarita'
in coordinate pixel (geometria v8.3, maschera >= 1) e della v8.4 (maschera >= 33). Nessuna delle
due classificazioni e' considerata corretta per definizione.
Uso: .venv/bin/python python/sharpbl/hale_case_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import geometry as geo  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402
from sharpbl.provenance import ROOT  # noqa: E402

OUT = ROOT / "figures/EXPLORATORY"
FITS = ROOT / "data/sharp/fits"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"


def pixel_centroids(br, mask, thr=100.0):
    yy, xx = np.mgrid[0:br.shape[0], 0:br.shape[1]]
    out = {}
    for sgn, name in ((1, "pos"), (-1, "neg")):
        sel = mask & (sgn * br >= thr)
        if sel.any():
            w = np.abs(br[sel])
            out[name] = ((xx[sel] * w).sum() / w.sum(), (yy[sel] * w).sum() / w.sum())
    return out


def main() -> int:
    per = pd.read_csv(ROOT / "results/EXPLORATORY/HALE_TRANSITIONS_BY_RECORD.csv")
    picks = []
    for (attr, v83), g in per.groupby(["attribution", "hale_v83"]):
        g = g.reindex(g["s_bl_v84"].abs().sort_values(ascending=False).index)
        picks.append(g.head(2))
    picks = pd.concat(picks).head(8)
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 4, figsize=(13, 6.4))
    rows = []
    for ax, (_, r) in zip(axes.ravel(), picks.iterrows()):
        folder = record_dir(FITS, r["T_REC"])
        stem = file_stem(int(r["HARPNUM"]), r["T_REC"])
        br, _ = geo.read_sharp(folder / f"{stem}.Br.fits")
        bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
        ok = np.isfinite(br) & (np.abs(br) <= 1e4)
        ax.imshow(np.clip(br, -1000, 1000), origin="lower", cmap="gray", vmin=-1000, vmax=1000)
        ax.contour((bm >= 1) & ok, levels=[0.5], colors=[ORANGE], linewidths=0.7)
        ax.contour((bm >= 33) & ok, levels=[0.5], colors=[BLUE], linewidths=0.9)
        for mask, col, mk in (((bm >= 1) & ok, ORANGE, "o"), ((bm >= 33) & ok, BLUE, "s")):
            c = pixel_centroids(br, mask)
            for name in ("pos", "neg"):
                if name in c:
                    ax.plot(*c[name], mk, mfc="white" if name == "neg" else col, mec=col, ms=7, mew=1.5)
        ax.set_title(f"HARP {int(r['HARPNUM'])} {r['T_REC'][:10]}\nHale {int(r['hale_v83']):+d}→{int(r['hale_v84']):+d}; "
                     f"dipende da {r['attribution']}", fontsize=7.5)
        ax.set_xticks([])
        ax.set_yticks([])
        rows.append(r)
    fig.suptitle("Casi rappresentativi di Hale cambiato (v8.3→v8.4). Arancio: maschera bitmap ≥ 1 e centroidi; "
                 "blu: bitmap ≥ 33. Pieno = positiva, vuoto = negativa. ESPLORATIVO", fontsize=8.5)
    fig.text(0.01, 0.005, "Br in scala di grigi ±1000 G. Nessuna classificazione è assunta corretta per definizione.",
             fontsize=7, color=GRAY)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(OUT / "hale_transition_cases.png", dpi=170)
    (OUT / "data").mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "data/hale_transition_cases.csv", index=False)
    print("figura scritta")
    return 0


if __name__ == "__main__":
    sys.exit(main())
