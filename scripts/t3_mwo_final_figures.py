"""Final figures of T3 on MWO and of the catalogue release (prepared before the tilts are unsealed; tested only on
synthetic inputs). The real run reads only the reviewed products: the release (results/MWO_TILT_CATALOGUE_RELEASE),
which exists only after the estimate and its recount, and the estimate (results/T3_MWO_ESTIMATE_R4).

Figures (results/T3_MWO_FINAL_FIGURES/):
  fig_beta3_summary.png    beta3 with its nominal interval, main analysis and sensitivities, with 0 and the projected
                           ramp targets (10 %, 20 %); validated vs descriptive stated in the title from FINAL.json
  fig_joy_by_cycle.png     descriptive Joy coefficient per cycle and hemisphere (weighted and unweighted), partial cycles
                           marked
  fig_wl_by_epoch.png      S1: a_{e,h} - abar_h with bootstrap interval per epoch and hemisphere, +-2.4 deg band
  fig_p1_comparison.png    S2-P1: histogram of gamma_MWO - gamma_HMI (axial) in 2010-2012
  fig_hale_by_epoch.png    S3: Hale agreement per epoch and hemisphere

    .venv/bin/python scripts/t3_mwo_final_figures.py --selftest
    .venv/bin/python scripts/t3_mwo_final_figures.py --run
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE"
EST = ROOT / "results/T3_MWO_ESTIMATE_R4"
OUT = ROOT / "results/T3_MWO_FINAL_FIGURES"
EPOCHS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")


def fig_beta3(est_tab, final, out):
    t = est_tab.copy()
    t = t[t.state == "stimato"] if "state" in t else t
    y = np.arange(len(t))[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.35 * len(t) + 1.6))
    ax.errorbar(t.beta, y, xerr=[t.beta - t.lo, t.hi - t.beta], fmt="o", color="k", capsize=3)
    ax.axvline(0, color="grey", lw=0.8)
    tg = final.get("targets") or {}
    for key, ls in (("delta_beta_10", ":"), ("delta_beta_20", "--")):
        if key in tg:
            ax.axvline(tg[key], color="tab:red", ls=ls, lw=1, label=f"ramp {key[-2:]} %: {tg[key]:.2f}")
    ax.set_yticks(y)
    ax.set_yticklabels(t.analysis)
    ax.set_xlabel("beta3 (deg of Joy coefficient per unit of activity), nominal 97.5 % interval")
    status = {"verdetto": "validated: verdict allowed", "descrittivo": "descriptive (no verdict)",
              "non concludente": "non-conclusive"}.get(final.get("outcome"), str(final.get("outcome")))
    ax.set_title(f"T3 on MWO 1974-2012 - {status}")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "fig_beta3_summary.png", dpi=150)
    plt.close(fig)


def fig_joy(joy, out):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    off = {("N", True): -0.15, ("S", True): -0.05, ("N", False): 0.05, ("S", False): 0.15}
    for (h, w), g in joy.groupby(["hemisphere", "weighted"]):
        x = g.cycle.to_numpy() + off[(h, bool(w))]
        ax.errorbar(x, g.k_deg, yerr=[g.k_deg - g.lo, g.hi - g.k_deg], fmt="o" if w else "s", capsize=2,
                    label=f"{h}, {'flux-weighted' if w else 'unweighted'}", mfc="none" if not w else None)
        for xi, pc in zip(x, g.partial_cycle):
            if pc:
                ax.annotate("partial", (xi, ax.get_ylim()[0]), fontsize=6, ha="center")
    ax.set_xlabel("cycle")
    ax.set_ylabel("k in gamma = k sin|lat| (deg)")
    ax.set_title("Joy's law per cycle (descriptive)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_joy_by_cycle.png", dpi=150)
    plt.close(fig)


def fig_wl(s1, out):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    for h, mk, dx in (("N", "o", -0.1), ("S", "s", 0.1)):
        g = s1[s1.hemisphere == h]
        x = np.array([EPOCHS.index(e) for e in g.epoch]) + dx
        ax.errorbar(x, g["diff"], yerr=[g["diff"] - g.lo, g.hi - g["diff"]], fmt=mk, capsize=2, label=h)
    ax.axhspan(-2.4, 2.4, color="grey", alpha=0.15, label="+-2.4 deg (10 % of gamma0)")
    ax.set_xticks(range(len(EPOCHS)))
    ax.set_xticklabels(EPOCHS)
    ax.set_ylabel("a(e,h) - mean, deg")
    ax.set_title("S1: MWO - white-light Joy coefficient by epoch (relative)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_wl_by_epoch.png", dpi=150)
    plt.close(fig)


def fig_p1(matched, out):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.hist(matched.d_p1, bins=np.arange(-90, 91, 5), color="tab:blue")
    ax.axvline(np.median(matched.d_p1), color="k", ls="--", label=f"median {np.median(matched.d_p1):.2f} deg")
    ax.set_xlabel("gamma_MWO - gamma_HMI, axial (deg)")
    ax.set_ylabel("regions")
    ax.set_title(f"S2-P1: same region and day, 2010-2012 (n = {len(matched)})")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_p1_comparison.png", dpi=150)
    plt.close(fig)


def fig_hale(s3, out):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for h, mk in (("N", "o"), ("S", "s")):
        g = s3[s3.hemisphere == h]
        ax.plot([EPOCHS.index(e) for e in g.epoch], g["mean"], mk + "-", label=h)
    ax.set_xticks(range(len(EPOCHS)))
    ax.set_xticklabels(EPOCHS)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("fraction agreeing with Hale")
    ax.set_title("S3: Hale agreement by epoch")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_hale_by_epoch.png", dpi=150)
    plt.close(fig)


def make_all(rel, est, out):
    out.mkdir(parents=True, exist_ok=False)
    fig_beta3(pd.read_csv(est / "ESTIMATE.csv"), json.loads((est / "FINAL.json").read_text()), out)
    fig_joy(pd.read_csv(rel / "JOY_BY_CYCLE.csv"), out)
    c = rel / "COMPARISONS"
    if (c / "S1_TABLE.csv").exists() and (c / "S1_TABLE.csv").stat().st_size > 1:
        fig_wl(pd.read_csv(c / "S1_TABLE.csv"), out)
    if (c / "S2_P1_MATCHED.csv").exists():
        fig_p1(pd.read_csv(c / "S2_P1_MATCHED.csv"), out)
    if (c / "S3_HALE.csv").exists():
        fig_hale(pd.read_csv(c / "S3_HALE.csv"), out)
    meta = dict(release_meta_sha256=hashlib.sha256((rel / "META.json").read_bytes()).hexdigest(),
                estimate_meta_sha256=hashlib.sha256((est / "META.json").read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                products_sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.iterdir())})
    (out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    return sorted(f.name for f in out.iterdir())


def run():
    if not (REL / "META.json").exists() or not (EST / "META.json").exists():
        sys.exit("release or estimate missing: final figures come after the estimate, its recount and the export")
    print(make_all(REL, EST, OUT))
    return 0


def selftest():
    import tempfile
    rng = np.random.default_rng(4)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rel, est = td / "rel", td / "est"
        (rel / "COMPARISONS").mkdir(parents=True)
        est.mkdir()
        names = ["main", "additive epoch terms", "no epoch terms", "weights = DPD area"]
        b = rng.normal(0, 1, len(names))
        pd.DataFrame(dict(analysis=names, state="stimato", beta=b, lo=b - 4, hi=b + 4)).to_csv(est / "ESTIMATE.csv", index=False)
        (est / "FINAL.json").write_text(json.dumps(dict(outcome="descrittivo", targets=dict(delta_beta_10=-0.53, delta_beta_20=-1.06))))
        (est / "META.json").write_text("{}")
        rows = [dict(cycle=c, hemisphere=h, weighted=w, k_deg=24 + rng.normal(0, 2), lo=20, hi=28, partial_cycle=c in (20, 24))
                for c in (20, 21, 22, 23, 24) for h in "NS" for w in (True, False)]
        pd.DataFrame(rows).to_csv(rel / "JOY_BY_CYCLE.csv", index=False)
        pd.DataFrame([dict(epoch=e, hemisphere=h, diff=rng.normal(0, 1), lo=-2, hi=2) for e in EPOCHS[1:] for h in "NS"]).to_csv(
            rel / "COMPARISONS/S1_TABLE.csv", index=False)
        pd.DataFrame(dict(d_p1=rng.normal(0, 6, 200))).to_csv(rel / "COMPARISONS/S2_P1_MATCHED.csv", index=False)
        pd.DataFrame([dict(epoch=e, hemisphere=h, size=50, mean=0.9) for e in EPOCHS for h in "NS"]).to_csv(
            rel / "COMPARISONS/S3_HALE.csv", index=False)
        (rel / "META.json").write_text("{}")
        made = make_all(rel, est, td / "out")
    want = {"fig_beta3_summary.png", "fig_joy_by_cycle.png", "fig_wl_by_epoch.png", "fig_p1_comparison.png",
            "fig_hale_by_epoch.png", "META.json"}
    good = want == set(made)
    print(f"[{'OK' if good else 'FALLITO'}] five final figures from synthetic release and estimate", made)
    print(f"selftest: {int(good)}/1 superati")
    return good


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (run() if a.run else 1))
