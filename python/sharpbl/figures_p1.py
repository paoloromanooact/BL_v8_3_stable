"""Figure della serie P1. I valori tracciati vanno in figures/P1/data/*.csv.

Uso: .venv/bin/python python/sharpbl/figures_p1.py
  fig1_butterfly.png       diagramma a farfalla delle regioni (variante A), colore = segno di D*
  fig2_series_by_cr.png    somme per CR ed emisfero di S_BL e D_bal, e D_bal cumulato
  fig3_legacy_vs_v84.png   confronto v8.3 / v8.4: S_BL per CR e differenza di tilt per regione
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
from sharpbl.provenance import ROOT  # noqa: E402

RES = ROOT / "results/P1"
FIG = ROOT / "figures/P1"
DATA = FIG / "data"
# palette validata (dataviz): blu/arancio per N/S, blu/rosso divergente per il segno
BLUE, ORANGE, RED, GRAY = "#2a78d6", "#eb6834", "#e34948", "#8a8984"
TEXT, TEXT2 = "#0b0b0b", "#52514e"
S_CYCLE = {24: 1.0, 25: -1.0}

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": TEXT2, "axes.labelcolor": TEXT, "xtick.color": TEXT2,
    "ytick.color": TEXT2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.6, "lines.linewidth": 1.5,
    "legend.frameon": False, "savefig.dpi": 200,
})


def cr_to_date(cr):
    return pd.Timestamp("1853-11-09") + pd.to_timedelta((np.asarray(cr, float) - 1) * 27.2753, unit="D")


def footer(fig, cat):
    full = int(cat["complete_series"].iloc[0]) if "complete_series" in cat else 0
    note = "" if full else "  —  PROVA PARZIALE (serie incompleta)"
    fig.text(0.01, 0.005, f"SHARP BL v8.4, protocollo P1/P1b/P1c, commit {str(cat['git_commit'].iloc[0])[:7]}{note}",
             fontsize=6.5, color=TEXT2)


def fig1(cat):
    a = cat[(cat["role"] != "control") & (cat["valid_bl"] == 1)].copy()
    a["t"] = pd.to_datetime(a["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    a["d_star"] = a["cycle"].map(S_CYCLE) * a["d_axial_bal_g"]
    a = a[np.isfinite(a["d_star"])]
    a[["HARPNUM", "T_REC", "lat_mean_deg", "phi_mx", "cycle", "d_star"]].to_csv(DATA / "fig1_butterfly.csv", index=False)
    size = 4 + 40 * (a["phi_mx"] / a["phi_mx"].quantile(0.99)).clip(0, 1)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    for mask, col, lab in ((a["d_star"] >= 0, BLUE, "D* ≥ 0 (segno atteso dal ciclo)"),
                           (a["d_star"] < 0, RED, "D* < 0 (segno opposto)")):
        ax.scatter(a.loc[mask, "t"], a.loc[mask, "lat_mean_deg"], s=size[mask], c=col, alpha=0.55,
                   linewidths=0.3, edgecolors="white", label=f"{lab}: {int(mask.sum())}")
    ax.axhline(0, color=GRAY, lw=0.8)
    ax.set_ylabel("latitudine (gradi)")
    ax.set_title("Regioni (record primari validi): contributo al dipolo D* = s_ciclo · D_bal; area ∝ Φ",
                 loc="left", fontsize=9)
    ax.legend(loc="upper right", fontsize=7.5, markerscale=1.2)
    footer(fig, cat)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "fig1_butterfly.png")
    plt.close(fig)


def fig2(cat, agg):
    a = agg[agg["variant"] == "A"].copy()
    a["date"] = cr_to_date(a["CR"])
    a.to_csv(DATA / "fig2_series_by_cr.csv", index=False)
    fig, axes = plt.subplots(3, 1, figsize=(7.5, 7.2), sharex=True)
    for ax, q, lab in ((axes[0], "sum_s_bl_mxcm", "Σ S_BL per CR (Mx·cm)"),
                       (axes[1], "sum_d_bal_g", "Σ D_bal per CR (G)")):
        for hem, col in (("N", BLUE), ("S", ORANGE)):
            h = a[a["hemisphere"] == hem].sort_values("CR")
            ax.fill_between(h["date"], h[f"{q}_p16"], h[f"{q}_p84"], color=col, alpha=0.18, lw=0)
            ax.plot(h["date"], h[q], color=col, label="nord" if hem == "N" else "sud")
        ax.axhline(0, color=GRAY, lw=0.8)
        ax.set_ylabel(lab)
        ax.legend(loc="upper right", fontsize=7.5)
    axes[0].set_title("Variante A: somme per rotazione di Carrington; banda = bootstrap 16–84%", loc="left", fontsize=9)
    tot = a.groupby("CR")["sum_d_bal_g"].sum().sort_index()
    cum = tot.cumsum()
    pd.DataFrame({"CR": cum.index, "date": cr_to_date(cum.index), "cum_d_bal_g": cum.to_numpy()}).to_csv(
        DATA / "fig2_cumulative_d_bal.csv", index=False)
    axes[2].plot(cr_to_date(cum.index), cum.to_numpy(), color=BLUE)
    axes[2].axhline(0, color=GRAY, lw=0.8)
    axes[2].set_ylabel("Σ cumulata D_bal, N+S (G)")
    footer(fig, cat)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "fig2_series_by_cr.png")
    plt.close(fig)


def fig3(cat, cmp_):
    cr = cmp_[cmp_["level"] == "CR"].dropna(subset=["s_bl_v84", "s_bl_legacy"])
    reg = cmp_[cmp_["level"] == "region"].copy()
    reg["dtilt"] = ((reg["tilt_reduced_v84"] - reg["tilt_reduced_legacy"] + 90) % 180) - 90
    both = reg[(reg["valid_v84"] == 1) & (reg["valid_legacy"] == 1)]
    cr.to_csv(DATA / "fig3a_s_bl_by_cr.csv", index=False)
    both[["HARPNUM", "T_REC", "tilt_reduced_v84", "tilt_reduced_legacy", "dtilt", "hale_changed"]].to_csv(
        DATA / "fig3b_tilt_difference.csv", index=False)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.4))
    for hem, col in (("N", BLUE), ("S", ORANGE)):
        h = cr[cr["hemisphere"] == hem]
        ax1.scatter(h["s_bl_legacy"], h["s_bl_v84"], s=12, c=col, alpha=0.7, linewidths=0.3,
                    edgecolors="white", label="nord" if hem == "N" else "sud")
    lim = np.nanmax(np.abs(cr[["s_bl_legacy", "s_bl_v84"]].to_numpy())) * 1.05 if len(cr) else 1
    ax1.plot([-lim, lim], [-lim, lim], color=GRAY, lw=0.8)
    ax1.set_xlim(-lim, lim)
    ax1.set_ylim(-lim, lim)
    ax1.set_xlabel("Σ S_BL per CR, v8.3 (Mx·cm)")
    ax1.set_ylabel("Σ S_BL per CR, v8.4 (Mx·cm)")
    ax1.legend(loc="upper left", fontsize=7.5)
    ax2.hist(both["dtilt"].dropna(), bins=np.arange(-90, 91, 5), color=BLUE, edgecolor="white", linewidth=0.6)
    ax2.set_xlabel("tilt ridotto v8.4 − v8.3 (gradi)")
    ax2.set_ylabel("regioni")
    n_h = int(reg["hale_changed"].sum())
    n_v = int(reg["valid_changed"].sum())
    ax2.set_title(f"segno Hale cambiato: {n_h}; validità cambiata: {n_v}", loc="left", fontsize=8)
    footer(fig, cat)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG / "fig3_legacy_vs_v84.png")
    plt.close(fig)


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    cat = pd.read_csv(RES / "P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    agg = pd.read_csv(RES / "P1_SBL_BY_CR_HEMISPHERE.csv")
    cmp_ = pd.read_csv(RES / "P1_LEGACY_VS_V84.csv", low_memory=False)
    fig1(cat)
    fig2(cat, agg)
    fig3(cat, cmp_)
    print(f"figure in {FIG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
