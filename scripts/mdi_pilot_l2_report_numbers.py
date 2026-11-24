"""Reading-time numbers of docs/MDI_PILOT_L2_RESULTS.md that are not in the reviewed analysis code.

Read-only and descriptive: it reads the preserved products of the level-2 analysis (4249b72) and of the level-1
analysis (eda3515), writes nothing, makes no new choice and computes no interval. It is not pre-registered analysis
code and not part of the 10/10 recount. Descriptive thresholds used in the report: |d_ax| > 45 deg (all comparisons),
> 10 deg (Q2 list), > 5 deg or a leading-polarity change (A - B list); the separation edge is the first level-2
CLASS_EDGES value (3.97 deg).

For each threshold the matched comparison joins the level-2 Q3FD pairs with the level-1 synoptic - MWO pairs of the
same threshold on (noaa, day), one to one, and checks that the MWO record (time, tilt, leading sign, flux) is the same.

    .venv/bin/python scripts/mdi_pilot_l2_report_numbers.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
L2, L1 = ROOT / "results/MDI_PILOT_ANALYSIS_L2", ROOT / "results/MDI_PILOT_ANALYSIS_L1"
TAGS = ("main", "sens100")


def rd(p):
    return pd.read_csv(p, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")


def dispersion(p):
    a = p.d_ax.abs()
    return dict(n=len(p), median_abs_d_ax=a.median(), p90_abs_d_ax=a.quantile(0.9), n_over_45=int((a > 45).sum()),
                leading_changes=int((~p.leading_agree.astype(bool)).sum()),
                flux_ratio_p10_p50_p90=p.flux_ratio.quantile([0.1, 0.5, 0.9]).tolist(),
                abs_dt_h_median_min_max=[p.abs_dt_h.median(), p.abs_dt_h.min(), p.abs_dt_h.max()])


def matched(tag):
    fd, syn = rd(L2 / f"Q3FD_PAIRS_A1_{tag}.csv"), rd(L1 / f"Q3_PAIRS_{tag}.csv")
    m = fd.merge(syn, on=["noaa", "day"], suffixes=("_fd", "_syn"), how="inner", validate="one_to_one")
    same = ((m.mwo_time_utc_fd == m.mwo_time_utc_syn) & np.isclose(m.t2_deg, m.mwo_tilt_deg, rtol=0, atol=1e-9)
            & (m.lead2 == m.mwo_leading_sign) & np.isclose(m.flux2_mx, m.mwo_flux_mx, rtol=1e-12, atol=0))
    if not same.all():
        raise SystemExit(f"{tag}: MWO record differs between the two files for {int((~same).sum())} pairs")
    row = lambda d, g, a, lead, fl: dict(median_d_ax=d.median(), median_d_gamma=g.median(), median_abs_d_ax=a.median(),  # noqa: E731
                                          p90_abs_d_ax=a.quantile(0.9), n_over_45=int((a > 45).sum()),
                                          leading_agree=lead.astype(bool).mean(), median_flux_ratio=fl.median())
    out = dict(n_q3fd=len(fd), n_common=len(m),
               fd_minus_mwo=row(m.d_ax_fd, m.d_gamma_fd, m.d_ax_fd.abs(), m.leading_agree_fd, m.flux_ratio_fd),
               syn_minus_mwo=row(m.d_ax_syn, m.d_gamma_syn, m.d_ax_syn.abs(), m.leading_agree_syn, m.flux_ratio_syn),
               spearman_abs=m.d_ax_fd.abs().corr(m.d_ax_syn.abs(), method="spearman"),
               n_fd_smaller=int((m.d_ax_fd.abs() < m.d_ax_syn.abs()).sum()))
    return out


def main():
    edge = json.loads((L2 / "CLASS_EDGES.json").read_text())["separation_main_l1_ok"][0]
    res = {"separation_edge_1": edge}
    for k in ("Q2", "REPEAT", "Q3FD"):
        for t in TAGS:
            res[f"{k}_{t}"] = dispersion(rd(L2 / f"{k}_PAIRS_A1_{t}.csv"))
    q2, rp = rd(L2 / "Q2_PAIRS_A1_main.csv"), rd(L2 / "REPEAT_PAIRS_A1_main.csv")
    big = q2[q2.d_ax.abs() > 10]
    rbig = rp[(rp.d_ax.abs() > 5) | ~rp.leading_agree.astype(bool)]
    res["Q2_main_abs_d_ax_over_10"] = dict(n=len(big), n_sep1_below_edge=int((big.sep1_deg < edge).sum()),
                                           groups=[f"{a} {b}" for a, b in zip(big.noaa, big.day)])
    res["REPEAT_main_abs_d_ax_over_5_or_leading_change"] = dict(
        n=len(rbig), groups=[f"{a} {b}" for a, b in zip(rbig.noaa, rbig.day)],
        all_in_Q2_list=bool(set(zip(rbig.noaa, rbig.day)) <= set(zip(big.noaa, big.day))))
    res["REPEAT_main_pair_dt_min_counts"] = {str(k): int(v) for k, v in rp.pair_dt_min.value_counts().sort_index().items()}
    for t in TAGS:
        res[f"matched_{t}"] = matched(t)
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
