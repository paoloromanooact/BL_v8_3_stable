"""Controllo diagnostico C: componente individuale e correzione per la leva (V1, V4; analitico anche V2, V3).

Piano registrato prima di questo codice: docs/DIAGNOSTIC_C_PLAN.md (commit df63fd2).
Sviluppo diagnostico, non validazione e non verdetto. Parametri temporali veri in tutti i
bracci simulati (come B). C1: componente individuale vera (normale); C2: wild bootstrap di B
con ogni termine riscalato perche' la sua varianza attesa sia quella vera (stessi semi di B).

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_c_individual.py [--n 2000] [--workers 12]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.diag_b_oracle import FALSE, true_params  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLAN = ROOT / "docs/DIAGNOSTIC_C_PLAN.md"
SIM_SCEN = ("V1", "V4")
AN_SCEN = ("V1", "V2", "V3", "V4")
SD_T, ETA0 = 15.0, 2.0e-24
N_REPRO = 25
_SILSO = None


def unit_pieces(scenario, d, test):
    """a_i, sigma_i veri, h_i, E[e~_i^2] e i pezzi lineari della procedura P2e."""
    dz = p2d.design_t3(d) if test == "T3" else p2d.design_t5(d)
    lp = p2d.linear_pieces(dz)
    if test == "T3":
        a = p2d.wls_row(dz["Xf"], dz["w"])
        w = dz["w"]
        sd0 = SD_T
    else:
        a = p2d.wls_row(dz["Xf_c"], dz["W_c"])[dz["k_of_i"]] * dz["agg"]
        w = dz["phi"]
        sd0 = ETA0
    spec = p2d.SCENARIOS[scenario]
    med = d.attrs["med_phi"]
    c = (w / med) ** -0.25 if spec.get("hetero") else np.ones_like(w)
    sig2 = (sd0 * c) ** 2
    key = pd.MultiIndex.from_arrays([dz["cr"], dz["hem"]])
    W = pd.Series(w, index=key).groupby(level=[0, 1]).transform("sum").to_numpy()
    h = w / W
    sum_h2s2 = pd.Series(h ** 2 * sig2, index=key).groupby(level=[0, 1]).transform("sum").to_numpy()
    ee2 = sig2 * (1 - 2 * h) + sum_h2s2
    one_minus = np.maximum(1 - h, 0.05)
    return dict(dz=dz, lp=lp, a=a, sig=np.sqrt(sig2), h=h, eet2=ee2 / one_minus, ee2=ee2)


def catalogue(scenario, k):
    cat = p2d.synthetic_catalog_p2d(scenario, 40000 + k, 0.0, 0.0)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], _SILSO)
    d.attrs["med_phi"] = float(np.median(cat["USFLUX"]))
    return d


def simulate(up, par, M, seed, arm, chunk=2000):
    rng = np.random.default_rng(seed)
    lp = up["lp"]
    if arm == "C1":
        gi = up["a"] * up["sig"]
    elif arm == "C2":
        gi = lp["ge"] * np.sqrt(up["sig"] ** 2 / up["eet2"])
    else:  # "B": riproduzione di B (s_i = 1)
        gi = lp["ge"]
    sims = np.empty(M)
    for s in range(0, M, chunk):
        m = min(chunk, M - s)
        U = p2d.simulate_ar1(par, m, rng)
        V = rng.standard_normal((m, len(gi))) if arm == "C1" else rng.choice([-1.0, 1.0], size=(m, len(gi)))
        sims[s:s + m] = lp["const"] + np.einsum("mgh,gh->m", U, lp["B"]) + V @ gi
    return sims


def one_sim(args):
    global _SILSO
    scenario, k, arm, M = args
    if _SILSO is None:
        _SILSO = run_p2.load_silso()
    p2d.ESTIMATOR = "p2e"
    d = catalogue(scenario, k)
    out = []
    for test in ("T3", "T5"):
        up = unit_pieces(scenario, d, test)
        par = dict(up["lp"]["par"])
        seed = (260000 if arm == "C1" else 60000) + 2 * k + (0 if test == "T3" else 1)
        if not par["applicable"]:
            verdict = "non applicabile (P2d §3)"
        else:
            par.update(true_params(scenario, test))
            sims = simulate(up, par, M, seed, arm)
            verdict = p2d.decide(par["beta_obs"], sims)["verdict_p2d"]
        out.append(dict(scenario=scenario, k=k, test=test, arm=arm, verdict=verdict,
                        applicable=int(par["applicable"])))
    return out


def one_analytic(args):
    global _SILSO
    scenario, k = args
    if _SILSO is None:
        _SILSO = run_p2.load_silso()
    p2d.ESTIMATOR = "p2e"
    d = catalogue(scenario, k)
    out = []
    for test in ("T3", "T5"):
        up = unit_pieces(scenario, d, test)
        a, s2 = up["a"], up["sig"] ** 2
        v_true = float(np.sum(a ** 2 * s2))
        v_exp = float(np.sum(a ** 2 * up["eet2"]))
        big = up["h"] > 0.3
        out.append(dict(scenario=scenario, k=k, test=test, applicable=int(up["lp"]["par"]["applicable"]),
                        R_ind_expected=v_exp / v_true, sum_a2_ee2=float(np.sum(a ** 2 * up["ee2"])),
                        share_true_var_h_gt_03=float(np.sum(a[big] ** 2 * s2[big]) / v_true),
                        frac_units_h_gt_03=float(big.mean())))
    return out


def counts(g, n):
    f = g["verdict"].isin(FALSE)
    app = g["applicable"] == 1
    p = f[app].mean()
    return dict(n=n, n_applicable=int(app.sum()), frac_not_applicable=1 - app.mean(), false=int(f.sum()),
                false_frac=f.sum() / n, false_cp_upper95=p2d.cp_upper(int(f.sum()), n),
                false_among_applicable=p, se=np.sqrt(p * (1 - p) / app.sum()),
                false_predicted_dir=int((g["verdict"] == FALSE[0]).sum()),
                false_opposite_dir=int((g["verdict"] == FALSE[1]).sum()))


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    M = p2d.M_MAIN
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_DIAGNOSTIC_C_PLAN"] = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    st["status"] = "sviluppo diagnostico, nessun verdetto"
    out = ROOT / "results/DIAGNOSTIC"
    tag = "" if args.n == 2000 else f"_N{args.n}"
    braw = pd.read_csv(out / "B_RAW.csv.gz")
    chk = []
    with Pool(args.workers) as pool:
        # controllo 1: C2 con s_i = 1 riproduce B
        rep = pd.DataFrame([r for part in pool.imap_unordered(
            one_sim, [(sc, k, "B", M) for sc in SIM_SCEN for k in range(min(N_REPRO, args.n))]) for r in part])
        m = rep.merge(braw[["scenario", "k", "test", "verdict"]], on=["scenario", "k", "test"], suffixes=("", "_B"))
        chk.append(dict(check="1_reproduce_B_with_s_equal_1", n=len(m), n_fail=int((m["verdict"] != m["verdict_B"]).sum())))
        # parte analitica
        an = pd.DataFrame([r for part in pool.imap_unordered(
            one_analytic, [(sc, k) for sc in AN_SCEN for k in range(args.n)], chunksize=8) for r in part])
        v1 = an[(an["scenario"] == "V1") & (an["applicable"] == 1)]
        ok2 = np.isfinite(v1["sum_a2_ee2"]) & (v1["sum_a2_ee2"] > 0)
        chk.append(dict(check="2_sum_a2_Ee2_finite_positive_V1", n=len(v1), n_fail=int((~ok2).sum())))
        c = pd.DataFrame(chk)
        c.assign(**st).to_csv(out / f"C_CHECKS{tag}.csv", index=False)
        print(c.to_string(index=False), flush=True)
        if (c["n_fail"] > 0).any():
            print("CONTROLLO OBBLIGATORIO FALLITO: C si ferma (piano §5)")
            return 2
        sims = pd.DataFrame([r for part in pool.imap_unordered(
            one_sim, [(sc, k, arm, M) for arm in ("C1", "C2") for sc in SIM_SCEN for k in range(args.n)],
            chunksize=4) for r in part])

    # sintesi analitica
    a_cat = pd.read_csv(out / "A_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "test", "applicable", "R_ind"])
    an = an.merge(a_cat, on=["scenario", "k", "test", "applicable"], how="left")
    an.assign(**st).to_csv(out / f"C_ANALYTIC_BY_CATALOGUE{tag}.csv.gz", index=False)
    rows = []
    for (sc, test), g in an[an["applicable"] == 1].groupby(["scenario", "test"]):
        rows.append(dict(scenario=sc, test=test, n=len(g),
                         R_ind_expected_median=g["R_ind_expected"].median(),
                         R_ind_expected_p10=g["R_ind_expected"].quantile(0.1),
                         R_ind_expected_p90=g["R_ind_expected"].quantile(0.9),
                         R_ind_A_median=g["R_ind"].median(), R_ind_A_p10=g["R_ind"].quantile(0.1),
                         R_ind_A_p90=g["R_ind"].quantile(0.9),
                         diff_median=g["R_ind_expected"].median() - g["R_ind"].median(),
                         share_true_var_h_gt_03_median=g["share_true_var_h_gt_03"].median(),
                         frac_units_h_gt_03_median=g["frac_units_h_gt_03"].median()))
    pd.DataFrame(rows).assign(**st).to_csv(out / f"C_ANALYTIC{tag}.csv", index=False)

    # sintesi dei bracci simulati, con confronto appaiato C2-B
    sims = sims.sort_values(["arm", "scenario", "k", "test"]).reset_index(drop=True)
    sims.assign(**st).to_csv(out / f"C_RAW{tag}.csv.gz", index=False)
    rows = []
    for (arm, sc, test), g in sims.groupby(["arm", "scenario", "test"]):
        r = dict(arm=arm, scenario=sc, test=test, **counts(g, len(g)))
        if arm == "C2":
            b = braw[(braw["scenario"] == sc) & (braw["test"] == test)].set_index("k")["verdict"]
            gv = g.set_index("k")["verdict"]
            b = b.reindex(gv.index)
            fb, fc = b.isin(FALSE), gv.isin(FALSE)
            r.update(paired_both=int((fb & fc).sum()), paired_only_B=int((fb & ~fc).sum()),
                     paired_only_C2=int((~fb & fc).sum()), verdicts_changed=int((b != gv).sum()))
        rows.append(r)
    s = pd.DataFrame(rows)
    bs = pd.read_csv(out / "B_SUMMARY.csv")[["scenario", "test", "false_oracle_among_applicable", "se_oracle"]]
    s = s.merge(bs, on=["scenario", "test"], how="left")
    s.assign(**st).to_csv(out / f"C_SUMMARY{tag}.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(pd.DataFrame(rows).round(4).to_string(index=False))
        print(pd.read_csv(out / f"C_ANALYTIC{tag}.csv").drop(columns=list(st)).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
