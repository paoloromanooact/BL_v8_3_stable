"""Coverage tables and figures of the MWO tilt catalogue R4 from METADATA ONLY (DESIGN, ATTEMPTS, LOSSES,
MAGNETOGRAMS): no tilt, no polarity sign, SEALED.csv.gz is never opened. Prepared while the validation runs.

Outputs results/T3_MWO_COVERAGE_R4/:
  RECORDS_BY_CYCLE_HEMISPHERE.csv, RECORDS_BY_EPOCH_HEMISPHERE.csv, RESOLUTION_BY_EPOCH.csv,
  ATTEMPT_STATUS_BY_EPOCH.csv, SELECTION_BY_ACTIVITY.csv, MAGNETOGRAM_STATUS.csv,
  fig_records_in_time.png (record latitude vs time, isolated set), fig_records_per_year_epoch.png,
  fig_selection_vs_activity.png, fig_resolution_by_epoch.png, fig_flux_by_epoch.png, META.json.

    .venv/bin/python scripts/t3_mwo_coverage_figures.py --selftest
    .venv/bin/python scripts/t3_mwo_coverage_figures.py --run
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
OUT = ROOT / "results/T3_MWO_COVERAGE_R4"
EPOCHS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")
EPOCH_SPANS = (("E1", "1974-01-02", "1974-07-09"), ("E2", "1974-07-11", "1981-12-08"), ("E3", "1982-01-03", "1984-09-08"),
               ("E4", "1984-09-06", "1989-04-11"), ("E5", "1989-04-11", "1993-09-23"), ("E6", "1993-09-22", "1994-12-30"),
               ("E7", "1995-03-25", "1996-04-08"), ("E8", "1996-04-13", "2012-12-07"))


def tables(design, attempts, losses, mags):
    iso = design[design.record_set == "isolated"]
    t = {}
    t["RECORDS_BY_CYCLE_HEMISPHERE.csv"] = pd.crosstab([design.record_set, design.cycle], design.hemisphere).reset_index()
    t["RECORDS_BY_EPOCH_HEMISPHERE.csv"] = pd.crosstab([design.record_set, design.epoch], design.hemisphere).reset_index()
    t["RESOLUTION_BY_EPOCH.csv"] = pd.crosstab(iso.epoch, iso.res_class).reset_index()
    a = attempts.assign(epoch=attempts.epoch.fillna("(none)"))
    t["ATTEMPT_STATUS_BY_EPOCH.csv"] = pd.crosstab(a.epoch, a.status).reset_index()
    sel = losses[losses.dimension == "A_tercile"].copy()
    cols = [c for c in ("record", "all_attempts_failed", "no_candidate_day") if c in sel]
    sel["groups"] = sel[cols].sum(axis=1)
    sel["fraction_with_record"] = sel.record / sel.groups
    t["SELECTION_BY_ACTIVITY.csv"] = sel.reset_index(drop=True)
    t["MAGNETOGRAM_STATUS.csv"] = mags.status.value_counts().rename_axis("status").reset_index(name="n")
    return t


def figures(design, tabs, out):
    iso = design[design.record_set == "isolated"].copy()
    iso["t"] = pd.to_datetime(iso.day)
    made = []
    fig, ax = plt.subplots(figsize=(10, 4))
    for e, a, b in EPOCH_SPANS:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), alpha=0.08 if EPOCHS.index(e) % 2 else 0.0, color="k")
    sc = ax.scatter(iso.t, iso.lat_bar, s=2, c=np.log10(iso.phi_mwo), cmap="viridis")
    fig.colorbar(sc, ax=ax, label="log10 window flux (Mx)")
    ax.set_ylabel("flux-weighted latitude (deg)")
    ax.set_title(f"MWO tilt catalogue R4, isolated records (n = {len(iso)}); shading = instrumental epochs")
    fig.tight_layout()
    fig.savefig(out / "fig_records_in_time.png", dpi=150)
    plt.close(fig)
    made.append("fig_records_in_time.png")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    yr = iso.assign(year=iso.t.dt.year).groupby(["year", "epoch"]).size().unstack(fill_value=0).reindex(columns=EPOCHS, fill_value=0)
    yr.plot(kind="bar", stacked=True, ax=ax, width=0.9, colormap="tab10")
    ax.set_ylabel("isolated records")
    ax.legend(ncol=8, fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_records_per_year_epoch.png", dpi=150)
    plt.close(fig)
    made.append("fig_records_per_year_epoch.png")
    sel = tabs["SELECTION_BY_ACTIVITY.csv"]
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for rs, g in sel.groupby("record_set"):
        ax.plot(g.value.astype(str), g.fraction_with_record, "o-", label=rs)
    ax.set_xlabel("activity tercile (at the eligible day with minimum |LCM|)")
    ax.set_ylabel("fraction of DPD groups with a record")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "fig_selection_vs_activity.png", dpi=150)
    plt.close(fig)
    made.append("fig_selection_vs_activity.png")
    rb = tabs["RESOLUTION_BY_EPOCH.csv"].set_index("epoch")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    (rb.div(rb.sum(axis=1), axis=0)).plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("share of isolated records")
    fig.tight_layout()
    fig.savefig(out / "fig_resolution_by_epoch.png", dpi=150)
    plt.close(fig)
    made.append("fig_resolution_by_epoch.png")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    data = [np.log10(iso.phi_mwo[iso.epoch == e]) for e in EPOCHS if (iso.epoch == e).any()]
    ax.boxplot(data, labels=[e for e in EPOCHS if (iso.epoch == e).any()], showfliers=False)
    ax.set_ylabel("log10 window flux (Mx)")
    ax.set_title("boxes without outliers (outliers kept in the data, not excluded)", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "fig_flux_by_epoch.png", dpi=150)
    plt.close(fig)
    made.append("fig_flux_by_epoch.png")
    return made


def run(cat=CAT, out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    design = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    attempts = pd.read_csv(Path(cat) / "ATTEMPTS.csv.gz", dtype={"noaa": str}, low_memory=False)
    losses = pd.read_csv(Path(cat) / "LOSSES.csv")
    mags = pd.read_csv(Path(cat) / "MAGNETOGRAMS.csv.gz", low_memory=False)
    tabs = tables(design, attempts, losses, mags)
    Path(out).mkdir(parents=True)
    for n, t in tabs.items():
        t.to_csv(Path(out) / n, index=False)
    figures(design, tabs, Path(out))
    meta = dict(catalogue_meta_sha256=hashlib.sha256((Path(cat) / "META.json").read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), sealed_opened=False,
                git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                products_sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(Path(out).iterdir())})
    (Path(out) / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    return 0


def selftest():
    import tempfile
    rng = np.random.default_rng(2)
    n = 300
    d = pd.DataFrame(dict(record_set=np.where(np.arange(n) < 200, "isolated", "all"), noaa=[str(i) for i in range(n)],
                          day=pd.date_range("1975-01-01", periods=n, freq="40D").strftime("%Y-%m-%d"),
                          epoch=rng.choice(EPOCHS, n), res_class=rng.choice(["R1", "R2"], n), hemisphere=rng.choice(["N", "S"], n),
                          lat_bar=rng.uniform(-35, 35, n), phi_mwo=10 ** rng.uniform(20, 22.5, n), cycle=rng.choice([21, 22, 23], n)))
    a = pd.DataFrame(dict(epoch=rng.choice(list(EPOCHS) + [None], 500), status=rng.choice(["ok", "no_magnetogram"], 500)))
    loss = pd.DataFrame([dict(record_set=rs, dimension="A_tercile", value=k, record=10 * k, all_attempts_failed=20,
                              no_candidate_day=5) for rs in ("isolated", "all") for k in (1, 2, 3)])
    m = pd.DataFrame(dict(status=["ok"] * 10 + ["excluded_A2"] * 2))
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "cat").mkdir()
        d.to_csv(Path(td) / "cat/DESIGN.csv", index=False)
        a.to_csv(Path(td) / "cat/ATTEMPTS.csv.gz", index=False)
        loss.to_csv(Path(td) / "cat/LOSSES.csv", index=False)
        m.to_csv(Path(td) / "cat/MAGNETOGRAMS.csv.gz", index=False)
        (Path(td) / "cat/META.json").write_text("{}")
        (Path(td) / "cat/SEALED.csv.gz").write_text("must never be read")
        run(Path(td) / "cat", Path(td) / "out")
        made = sorted(f.name for f in (Path(td) / "out").iterdir())
        sel = pd.read_csv(Path(td) / "out/SELECTION_BY_ACTIVITY.csv")
    good = len([f for f in made if f.endswith(".png")]) == 5 and len([f for f in made if f.endswith(".csv")]) == 6 \
        and np.allclose(sel.fraction_with_record, sel.record / (sel.record + 25))
    src = Path(__file__).read_text().split("def selftest")[0]
    print(f"[{'OK' if good else 'FALLITO'}] tables and figures from metadata on a synthetic catalogue", made)
    print(f"[{'OK' if 'SEALED' not in src.replace('SEALED.csv.gz is never opened', '') else 'FALLITO'}] SEALED never read")
    ok2 = "SEALED" not in src.replace("SEALED.csv.gz is never opened", "")
    print(f"selftest: {int(good) + int(ok2)}/2 superati")
    return good and ok2


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (run() if a.run else 1))
