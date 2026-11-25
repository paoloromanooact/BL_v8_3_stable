"""Read-only recomputation of the numbers of docs/MDI_PILOT_Q4_RESULTS.md from results/MDI_Q4_PROSPECTIVE/.

Reads only the preserved Q4 products (after the recount receipt 8924285) and prints the paired ratios (median, min,
max over the 20 realisations), the sensitivities, the absolute precisions, the product shift, the tolerances, the
designs and the deterministic yields used in the report. Not pre-registered; it writes nothing.

    .venv/bin/python scripts/mdi_q4_report_numbers.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/MDI_Q4_PROSPECTIVE"
FORMS = ((1, 1.0), (2, 1.0), (7, 1.0))


def main():
    raw = pd.read_csv(OUT / "RAW.csv.gz", low_memory=False)
    ok = raw[raw.status == "ok"]

    def h(design, variant, th, model, si, sm, sc, xs):
        q = ok[(ok.design == design) & (ok.model == model) & (ok.sigma_int == si) & (ok.scen == sc) & (ok.x_scale == xs)]
        if design == "H":
            return q[q.sigma_m == 0.0].h_gamma0.iloc[0]
        return q[(q.variant == variant) & (q.threshold == th) & (q.sigma_m == sm)].set_index("r").h_gamma0

    def ratio(num, den="H", vnum="ref", vden="ref", th="main", model="a", si=15.0, sm=2.0, forms=FORMS):
        out = []
        for sc, xs in forms:
            q = h(num, vnum, th, model, si, sm, sc, xs) / h(den, vden, th, "a" if den == "H" else model, si, sm, sc, xs)
            out.append(f"{q.median():.3f} ({q.min():.3f}-{q.max():.3f})")
        return " · ".join(out)

    print("== criteria (median (min-max) over realisations; forms phi 0.5 · phi 0.9 · steps 20)")
    for th in ("main", "sens100"):
        print(f"[{th}] MS+H/H {ratio('MS+H', th=th)}")
        print(f"[{th}] MS+H/H (30,10) {ratio('MS+H', th=th, si=30.0, sm=10.0)}")
        print(f"[{th}] MS/H {ratio('MS', th=th)}")
        print(f"[{th}] MF/H {ratio('MF', th=th)}")
        print(f"[{th}] MF+H/MS+H cohort {ratio('MF+H', 'MS+H', th=th)}")
        print(f"[{th}] MF+H/MS+H cohort x act {ratio('MF+H', 'MS+H', vnum='mf_pool_cohort_act', th=th)}")
        for m in ("bJ", "bA"):
            print(f"[{th}] protected {m} MS+H/H {ratio('MS+H', th=th, model=m)}")
    print("== sensitivities of MS+H/H (main)")
    for si in (15.0, 25.0, 30.0):
        for sm in (0.0, 2.0, 10.0):
            print(f"sigma_int {si} sigma_m {sm}: {ratio('MS+H', si=si, sm=sm)}")
    for v in ("w_x0.5", "w_x2", "w_norm", "cov_zero_cross", "flux_nolat"):
        print(f"{v}: {ratio('MS+H', vnum=v)}")
    for sc in (3, 4):
        print(f"scenario {sc} x 0.5/1/2: {ratio('MS+H', forms=((sc, 0.5), (sc, 1.0), (sc, 2.0)))}")
    print(f"main forms x 0.5: {ratio('MS+H', forms=tuple((s, 0.5) for s, _ in FORMS))}")
    print(f"main forms x 2: {ratio('MS+H', forms=tuple((s, 2.0) for s, _ in FORMS))}")
    for v in ("mf_pool_cohort_area", "avail_0.8", "avail_0.6", "flux_mf_rho"):
        print(f"MF+H({v})/MS+H: {ratio('MF+H', 'MS+H', vnum=v)}")
    print("== absolute precision (main, reference; medians)")
    for d in ("H", "MS", "MF", "MS+H", "MF+H"):
        for sc, xs in FORMS:
            q = ok[(ok.design == d) & (ok.variant == "ref") & (ok.model == "a") & (ok.sigma_int == 15.0) & (ok.scen == sc) & (ok.x_scale == xs)
                   & (ok.sigma_m == (0.0 if d == "H" else 2.0)) & (ok.threshold.isin(["main", "-"]))]
            print(f"{d} scen {sc}: n_records {q.n_records.median():.0f} h/g0 {q.h_gamma0.median():.3f} SE/|t| {q.se_over_target_020.median():.2f} "
                  f"recognition {q.recognition_020.median():.4f} (qd {q.recognition_qd_020.median():.4f})")
    q = ok[(ok.variant == "ref") & (ok.model == "a") & (ok.sigma_int == 15.0) & (ok.sigma_m == 2.0) & (ok.scen == 1) & (ok.x_scale == 1.0) & (ok.threshold == "main")]
    ms, msh = q[q.design == "MS"], q[q.design == "MS+H"]
    print(f"== product shift: MS m_prod {ms.m_prod.median():.3f}, /target {ms.m_prod_over_target_020.median():.2f} "
          f"({ms.m_prod_over_target_020.min():.2f} to {ms.m_prod_over_target_020.max():.2f}); MS+H /target {msh.m_prod_over_target_020.median():.2f}")
    print(f"== tolerances MS+H model a: A {msh.tol_units_A_020.median():.3f}, J {msh.tol_units_J_020.median():.3f}; null worst "
          f"A C0.25 {msh['sup_null_worst_A_C0.25'].median():.3f} C0.5 {msh['sup_null_worst_A_C0.5'].median():.3f}, "
          f"J C0.25 {msh['sup_null_worst_J_C0.25'].median():.3f} C0.5 {msh['sup_null_worst_J_C0.5'].median():.3f}")
    d = pd.read_csv(OUT / "DESIGNS.csv")
    x = d[(d.variant == "ref") & (d.threshold == "main")]
    print("== designs (main, reference; medians)")
    print(x.groupby("design")[["n_domain", "n_included", "expected_yield", "lat_dist_median", "lat_dist_p90"]].median().round(3).to_string())
    print("design statuses:", d.status.value_counts().to_dict(), "; NOT_COMPUTABLE rows:", len(pd.read_csv(OUT / "NOT_COMPUTABLE.csv")))
    print("== yields (main)")
    print(pd.read_csv(OUT / "YIELD_EFFECTS.csv").query("threshold == 'main'")[["design", "step_order", "step", "value"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
