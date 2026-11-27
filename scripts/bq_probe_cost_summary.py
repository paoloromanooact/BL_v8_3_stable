"""Cost summary of a psi-averaged SMC probe (bq_cv_psi_smc.py outputs): fit seconds, the main evaluations and the
control replicates kept apart, seconds per single SMC evaluation, score and MC SE at every checkpoint.

The SMC loop records only the cumulative seconds after each evaluated draw (DRAWS.csv, column `seconds`); a draw of the
repeated subset carries n_main + n_extra SMC runs. The time of one draw is the difference of consecutive cumulative
values; dividing it by the number of SMC runs of that draw gives the seconds per single evaluation (the runs of one draw
share the state, so the split assumes equal cost per run: stated, not measured).

    .venv/bin/python scripts/bq_probe_cost_summary.py <probe dir with one sub-directory per likelihood> [--out SUMMARY.csv]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def summarise(run):
    run = Path(run)
    meta = json.loads((run / "META.json").read_text())
    d = pd.read_csv(run / "DRAWS.csv")
    dt = np.diff(np.r_[0.0, d.seconds.to_numpy(float)])
    runs = (d.n_main + d.n_extra).to_numpy(float)
    per = dt / runs
    main_s = float((per * d.n_main).sum())
    extra_s = float((per * d.n_extra).sum())
    cp = pd.read_csv(run / "CHECKPOINTS.csv") if (run / "CHECKPOINTS.csv").exists() else pd.DataFrame()
    return dict(likelihood=run.name, records=meta.get("records"), training_records=meta.get("training_records"),
                fit_seconds=meta.get("fit_seconds"), fit_seconds_per_chain_mean=float(np.mean(meta.get("fit_seconds_per_chain") or [np.nan])),
                draws=int(len(d)), main_evaluations=int(d.n_main.sum()), control_evaluations=int(d.n_extra.sum()),
                main_seconds=main_s, control_seconds=extra_s, smc_seconds=float(d.seconds.iloc[-1]) if len(d) else np.nan,
                seconds_per_evaluation_mean=float(np.average(per, weights=runs)) if len(d) else np.nan,
                seconds_per_evaluation_min=float(per.min()) if len(d) else np.nan, seconds_per_evaluation_max=float(per.max()) if len(d) else np.nan,
                score_status=meta.get("score_status"), stop_reason=meta.get("stop_reason"),
                checkpoints=";".join(f"{int(r.draws)}:{r.score:.3f}±{r.mcse:.3f} (ESSw {r.ess_weights:.0f})" for r in cp.itertuples()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("probe")
    ap.add_argument("--out")
    a = ap.parse_args()
    rows = [summarise(p) for p in sorted(Path(a.probe).iterdir()) if p.is_dir() and (p / "DRAWS.csv").exists()]
    s = pd.DataFrame(rows)
    if a.out:
        s.to_csv(a.out, index=False)
    with pd.option_context("display.width", 250, "display.max_colwidth", 120):
        print(s.T.to_string())


if __name__ == "__main__":
    main()
