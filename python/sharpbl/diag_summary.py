"""Tabelle della diagnosi di P2d/P2e e del quadro delle sensibilita' (sviluppo diagnostico, nessun verdetto).

Legge solo file gia' prodotti (validazione P2e, test P2, catalogo P1, somme P1) e scrive in
results/DIAGNOSTIC/. Non esegue simulazioni e non modifica risultati esistenti.
Documenti: docs/DIAGNOSTIC_P2E.md, docs/P2E_V0_APPLICABILITY_DISCREPANCY.md,
docs/SENSITIVITY_SUMMARY.md.

    .venv/bin/python python/sharpbl/diag_summary.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

FALSE = ["quenching supportato (P2d)", "segno opposto (P2d)"]
TRUE_PAR = {  # valori veri degli scenari (P2d §5; p2d.SCENARIOS); sigma_u^2 vero T3 = (0,5 * 15)^2, T5 = (0,5 * eta0)^2
    "V0": dict(phi_true=0.0, kappa_true=np.nan), "V1": dict(phi_true=0.5, kappa_true=0.0),
    "V2": dict(phi_true=0.8, kappa_true=0.0), "V3": dict(phi_true=0.8, kappa_true=0.6),
    "V4": dict(phi_true=0.8, kappa_true=0.0),
    "V5": dict(phi_true=0.5 / (1 - 0.3), kappa_true=0.0),   # AR(2): autocorrelazione al ritardo 1
    "V6": dict(phi_true=np.nan, kappa_true=0.0),
}
SIGMA2_TRUE = {"T3": 7.5 ** 2, "T5": (0.5 * 2.0e-24) ** 2}


def diag_p2e(out, st):
    p2 = ROOT / "results/P2"
    val = pd.read_csv(p2 / "P2E_VALIDATION.csv")
    par = pd.read_csv(p2 / "P2E_VALIDATION_PARAMETERS.csv")
    keep = ["scenario", "test", "n", "n_applicable", "false_total", "false_frac_total", "false_cp_upper95",
            "false_among_applicable", "false_predicted_direction", "false_opposite_direction", "accepted_rule"]
    t = val[keep].merge(par[["scenario", "test", "phi_hat_mean", "phi_hat_std", "kappa_hat_mean", "kappa_hat_std",
                             "sigma_u2_hat_mean", "sigma_u2_hat_std"]], on=["scenario", "test"])
    t = t.merge(pd.DataFrame([dict(scenario=k, **v) for k, v in TRUE_PAR.items()]), on="scenario")
    t["sigma_u2_true"] = t["test"].map(SIGMA2_TRUE).where(t["scenario"] != "V0", 0.0)
    t["sigma_u2_hat_over_true"] = t["sigma_u2_hat_mean"] / t["sigma_u2_true"].replace(0, np.nan)
    t.assign(**st).to_csv(out / "DIAG_P2E_SCENARIOS.csv", index=False)

    raw = pd.read_csv(p2 / "P2E_VALIDATION_RAW.csv.gz")
    raw = raw[raw["beta_frac"] == 0].copy()
    raw["false"] = raw["verdict"].isin(FALSE)
    raw["na"] = raw["applicable"] == 0
    rows = []
    for (sc, test), g in raw[~raw["na"]].groupby(["scenario", "test"]):
        q = pd.qcut(g["phi_hat"].rank(method="first"), 3, labels=["basso", "medio", "alto"])
        for lab, h in g.groupby(q, observed=True):
            p = h["false"].mean()
            rows.append(dict(scenario=sc, test=test, phi_tercile=lab, n=len(h), phi_hat_mean=h["phi_hat"].mean(),
                             false_frac=p, se=np.sqrt(p * (1 - p) / len(h))))
    pd.DataFrame(rows).assign(**st).to_csv(out / "DIAG_P2E_PHI_TERCILES.csv", index=False)

    rows = []
    for (sc, test), g in raw.groupby(["scenario", "test"]):
        c0_le0 = g["sigma_u_at_boundary"] == 1          # P2e §2: c0 <= 0
        rows.append(dict(scenario=sc, test=test, n=len(g), n_not_applicable=int(g["na"].sum()),
                         na_with_c0_le_0=int((g["na"] & c0_le0).sum()),
                         c0_le_0_total=int(c0_le0.sum()),
                         na_with_c0_gt_0=int((g["na"] & ~c0_le0).sum()),
                         false_among_applicable=g.loc[~g["na"], "false"].mean()))
    pd.DataFrame(rows).assign(**st).to_csv(out / "DIAG_P2E_APPLICABILITY.csv", index=False)

    w = raw.pivot_table(index=["scenario", "k"], columns="test", values="phi_hat")
    corr = w.groupby("scenario").apply(lambda g: g["T3"].corr(g["T5"]))
    corr.rename("corr_phi_hat_T3_T5").reset_index().assign(**st).to_csv(
        out / "DIAG_P2E_T3_T5_PHI_CORR.csv", index=False)

    real = pd.read_csv(p2 / "P2D_TESTS.csv")
    cols = [c for c in ["test", "verdict_p2d", "applicable", "c0", "c1", "nbar", "phi", "phi_raw", "sigma_u2",
                        "sigma_u_at_boundary", "sw2_N", "sw2_S", "kappa", "kappa_raw", "n_cr", "n_pairs_phi",
                        "n_cr_kappa", "kappa_not_estimable"] if c in real.columns]
    real[cols].assign(**st).to_csv(out / "DIAG_P2_REAL_FLAGS.csv", index=False)


def sens_tests(out, st, cat):
    """T3, T4, T5 per S, S5 (controllo), S8 (senza ricomparse candidate); T5 normalizzato in due modi."""
    p2 = ROOT / "results/P2"
    sil = run_p2.load_silso()
    S = run_p2.samples(cat)
    eta = {}
    for v in ("S", "S5", "S8"):
        c = run_p2.cells(run_p2.add_activity(S[v], sil), "A_monthly", "d_star")
        eta[v] = dict(eta_bar=float((c["eta"] * c["phi"]).sum() / c["phi"].sum()), n_cells_check=len(c))
    rows = []
    for f, test in (("P2_T3_TILT_QUENCHING.csv", "T3"), ("P2_T4_LATITUDE_QUENCHING.csv", "T4"),
                    ("P2_T5_EFFICIENCY.csv", "T5")):
        d = pd.read_csv(p2 / f)
        d = d[(d["activity"] == "A_monthly") & d["variant"].isin(["S", "S5", "S8"])]
        if test == "T5":
            d = d[d["quantity"] == "D*"]
        for _, r in d.iterrows():
            row = dict(test=test, variant=r["variant"], estimate=r["estimate"], ci95_lo=r["ci95_lo"],
                       ci95_hi=r["ci95_hi"], n_regions=int(r["n"]), n_cr=int(r["n_cr"]))
            if test == "T5":
                row.update(n_cells=int(r["n_cells"]), eta_bar_own=eta[r["variant"]]["eta_bar"],
                           eta_bar_S=eta["S"]["eta_bar"],
                           rel_own=r["estimate"] / eta[r["variant"]]["eta_bar"],
                           rel_S=r["estimate"] / eta["S"]["eta_bar"],
                           rel_S_ci95_lo=r["ci95_lo"] / eta["S"]["eta_bar"],
                           rel_S_ci95_hi=r["ci95_hi"] / eta["S"]["eta_bar"])
            rows.append(row)
    pd.DataFrame(rows).assign(**st).to_csv(out / "SENS_TESTS.csv", index=False)


def sens_sums(out, st, cat):
    """Somme per ciclo ed emisfero: A (primario), E (A senza ricomparse candidate), controllo; nette e assolute."""
    c = cat[cat["valid_bl"] == 1].copy()
    c["hem"] = np.where(c["lat_mean_deg"] >= 0, "N", "S")
    prim = c[c["role"].isin(["primary", "both"])]
    ctrl = c[c["role"].isin(["control", "both"])]
    common = set(prim["HARPNUM"]) & set(ctrl["HARPNUM"])
    sets = {
        "A_primario": prim,
        "E_primario_senza_ricomparse": prim[prim["family_rank"] == 0],
        "ricomparse_candidate": prim[prim["family_rank"] > 0],
        "controllo_campione_proprio": ctrl,
        "A_primario_HARP_comuni": prim[prim["HARPNUM"].isin(common)],
        "controllo_HARP_comuni": ctrl[ctrl["HARPNUM"].isin(common)],
    }
    rows = []
    for name, d in sets.items():
        for (cyc, h), g in d.groupby(["cycle", "hem"]):
            rows.append(dict(set=name, cycle=int(cyc), hemisphere=h, n=len(g),
                             sum_s_bl=g["s_bl"].sum(), sum_abs_s_bl=g["s_bl"].abs().sum(),
                             sum_pos_s_bl=g["s_bl"].clip(lower=0).sum(), sum_neg_s_bl=g["s_bl"].clip(upper=0).sum(),
                             sum_d_bal=g["d_axial_bal_g"].sum(), sum_abs_d_bal=g["d_axial_bal_g"].abs().sum(),
                             sum_phi=g["phi_mx"].sum()))
    t = pd.DataFrame(rows)
    t.assign(**st).to_csv(out / "SENS_SUMS.csv", index=False)

    key = ["cycle", "hemisphere"]
    base = {"A_primario": "A_primario", "E_primario_senza_ricomparse": "A_primario",
            "ricomparse_candidate": "A_primario", "controllo_campione_proprio": "A_primario",
            "controllo_HARP_comuni": "A_primario_HARP_comuni"}
    rat = []
    for name, ref in base.items():
        if name == ref:
            continue
        a = t[t["set"] == name].set_index(key)
        b = t[t["set"] == ref].set_index(key)
        r = pd.DataFrame({"set": name, "reference": ref, "n": a["n"], "n_reference": b["n"]})
        for q in ("sum_s_bl", "sum_abs_s_bl", "sum_d_bal", "sum_abs_d_bal", "sum_phi"):
            r[f"ratio_{q}"] = a[q] / b[q]
        rat.append(r.reset_index())
    pd.concat(rat).assign(**st).to_csv(out / "SENS_SUMS_RATIOS.csv", index=False)

    s = pd.read_csv(ROOT / "results/P1/P1_SBL_BY_CR_HEMISPHERE.csv").set_index(["variant", "CR", "hemisphere"])
    rows = []
    for q in ("sum_s_bl_mxcm", "sum_d_bal_g", "sum_phi_mx"):
        A = s.loc["A"][q]
        E = s.loc["E"][q].reindex(A.index)
        diff = (E.fillna(0) - A).abs()
        rows.append(dict(quantity=q, n_cells_A=len(A), n_cells_changed=int((diff > 0).sum()),
                         median_abs_diff_over_median_abs_A=float(diff.median() / A.abs().median()),
                         median_abs_diff_changed_over_median_abs_A=float(diff[diff > 0].median() / A.abs().median())))
    tot_a = s.loc["A"]["sum_s_bl_mxcm"].sum()
    tot_cat = sets["A_primario"]["s_bl"].sum()
    rows.append(dict(quantity="check_total_s_bl_A_cells_vs_catalogue", n_cells_A=len(s.loc["A"]),
                     n_cells_changed=0, median_abs_diff_over_median_abs_A=float(tot_a / tot_cat - 1),
                     median_abs_diff_changed_over_median_abs_A=np.nan))
    pd.DataFrame(rows).assign(**st).to_csv(out / "SENS_SUMS_CELLS_E_VS_A.csv", index=False)
    print("varianti delle somme P1 disponibili:", sorted(s.index.get_level_values(0).unique()))


def main() -> int:
    out = ROOT / "results/DIAGNOSTIC"
    out.mkdir(parents=True, exist_ok=True)
    st = stamp(("P1", "P1d", "P1e", "P2", "P2d", "P2e"))
    st["status"] = "diagnostico, nessun verdetto"
    diag_p2e(out, st)
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    sens_tests(out, st, cat)
    sens_sums(out, st, cat)
    for f in sorted(out.glob("*.csv")):
        print(f.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
