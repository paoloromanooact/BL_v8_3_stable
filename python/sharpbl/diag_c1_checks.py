"""Controlli diretti su C1 richiesti dalla revisione (post hoc, nessun verdetto).

1. Finitezza degli ingressi della simulazione C1 in tutti i cataloghi (V1, V4; T3, T5):
   a_i, sigma_i, B, const, parametri veri.
2. Riesecuzione di C1 con gli stessi semi (260000 + 2k + t) sui primi 100 cataloghi di V1 e V4:
   simulazioni tutte finite e verdetti uguali a quelli di C_RAW_RUN1.
3. Esattezza di T3 rispetto alla trasformazione gamma -> sin(gamma) -> gamma (non vale per
   |gamma| > 90 gradi): per ogni catalogo di V0-V6, stima con gamma del generatore (senza
   trasformazione) contro stima osservata, e decisione |z| > z_0,0125 (soglia normale a precisione
   completa) con ciascuna. Copertura: ingressi su tutti i cataloghi, simulazioni rigenerate solo sui
   primi 100 per scenario (verifica campionaria).

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_c1_checks.py [--workers 12]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import diag_a_variance as da  # noqa: E402
from sharpbl import diag_c_individual as dc  # noqa: E402
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.diag_b_oracle import FALSE, true_params  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

Z = norm.ppf(1 - p2d.ALPHA_SIDE)
N_RESIM = 100


def init():
    if dc._SILSO is None:
        dc._SILSO = run_p2.load_silso()
    da._SILSO = dc._SILSO
    p2d.ESTIMATOR = "p2e"


def inputs_and_resim(args):
    scenario, k, M = args
    init()
    d = dc.catalogue(scenario, k)
    out = []
    for t, test in enumerate(("T3", "T5")):
        up = dc.unit_pieces(scenario, d, test)
        lp = up["lp"]
        par = dict(lp["par"])
        par.update(true_params(scenario, test))
        fin = bool(np.isfinite(up["a"]).all() and np.isfinite(up["sig"]).all() and (up["sig"] > 0).all()
                   and np.isfinite(lp["B"]).all() and np.isfinite(lp["const"])
                   and all(np.isfinite(par[x]) for x in ("phi", "kappa", "sigma_u2")))
        row = dict(scenario=scenario, k=k, test=test, inputs_finite=int(fin))
        if k < N_RESIM and par["applicable"]:
            x = dc.simulate(up, par, M, 260000 + 2 * k + t, "C1")
            ok = bool(np.isfinite(x).all())
            row.update(resim_finite=int(ok),
                       resim_verdict=p2d.decide(par["beta_obs"], x)["verdict_p2d"] if ok else "errore (non finito)")
        out.append(row)
    return out


def t3_transform(args):
    scenario, k = args
    init()
    cat = p2d.synthetic_catalog_p2d(scenario, 40000 + k, 0.0, 0.0)
    gamma_gen, _, _ = da.generator_gamma(scenario, 40000 + k)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], dc._SILSO)
    dz = p2d.design_t3(d)
    a = p2d.wls_row(dz["Xf"], dz["w"])
    dd = d[np.isfinite(d[da.ACT])]
    g = gamma_gen[dd["HARPNUM"].to_numpy()]
    return dict(scenario=scenario, k=k, n_wrap=int((np.abs(g) > 90).sum()), beta_obs=float(a @ dz["y"]),
                beta_gen=float(a @ g), max_abs_y_minus_gamma=float(np.max(np.abs(dz["y"] - g))))


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--n", type=int, default=2000)
    args = ap.parse_args()
    st = stamp(("P2", "P2d", "P2e"))
    st["status"] = "controllo post hoc, nessun verdetto"
    out = ROOT / "results/DIAGNOSTIC"
    with Pool(args.workers) as pool:
        r1 = pd.DataFrame([r for part in pool.imap_unordered(
            inputs_and_resim, [(sc, k, p2d.M_MAIN) for sc in ("V1", "V4") for k in range(args.n)], chunksize=4)
            for r in part])
        r3 = pd.DataFrame(pool.map(t3_transform, [(sc, k) for sc in p2d.SCENARIOS for k in range(args.n)],
                                   chunksize=8))
    c1 = pd.read_csv(out / "C_RAW_RUN1.csv.gz")
    c1 = c1[c1["arm"] == "C1"][["scenario", "k", "test", "verdict"]]
    r1 = r1.merge(c1, on=["scenario", "k", "test"], how="left")
    rs = r1[r1["resim_verdict"].notna()] if "resim_verdict" in r1 else r1.iloc[0:0]
    checks = pd.DataFrame([
        dict(check="1_C1_inputs_finite", n=len(r1), n_fail=int((r1["inputs_finite"] != 1).sum())),
        dict(check="2_C1_resim_finite", n=len(rs), n_fail=int((rs["resim_finite"] != 1).sum())),
        dict(check="2_C1_resim_verdict_equal_run1", n=len(rs), n_fail=int((rs["resim_verdict"] != rs["verdict"]).sum())),
    ])
    a = pd.read_csv(out / "A_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "test", "beta_obs", "mu_true", "v_true"])
    a = a[a["test"] == "T3"].rename(columns={"beta_obs": "beta_obs_A"})
    r3 = r3.merge(a, on=["scenario", "k"])
    r3["z_obs"] = (r3["beta_obs"] - r3["mu_true"]) / np.sqrt(r3["v_true"])
    r3["z_gen"] = (r3["beta_gen"] - r3["mu_true"]) / np.sqrt(r3["v_true"])
    r3["false_obs"] = r3["z_obs"].abs() > Z
    r3["false_gen"] = r3["z_gen"].abs() > Z
    checks = pd.concat([checks, pd.DataFrame([dict(check="3_beta_obs_equal_A", n=len(r3),
                                                   n_fail=int((~np.isclose(r3["beta_obs"], r3["beta_obs_A"], rtol=1e-9,
                                                                           atol=0)).sum()))])])
    checks.assign(**st).to_csv(out / "C1_CHECKS_DIRECT.csv", index=False)
    r3["beta_diff"] = r3["beta_gen"] - r3["beta_obs"]
    r3["beta_diff_over_sd"] = r3["beta_diff"] / np.sqrt(r3["v_true"])
    r3.assign(**st).to_csv(out / "C1_T3_TRANSFORM_BY_CATALOGUE.csv.gz", index=False)
    r1.assign(**st).to_csv(out / "C1_INPUTS_RESIM_BY_CATALOGUE.csv.gz", index=False)
    rows = []
    for sc, g in r3.groupby("scenario"):
        w = g["n_wrap"] > 0
        dw = g.loc[w, "beta_diff_over_sd"].abs()
        rows.append(dict(scenario=sc, n=len(g), catalogues_with_wrap=int(w.sum()), regions_wrapped=int(g["n_wrap"].sum()),
                         max_abs_beta_diff_deg=float(g["beta_diff"].abs().max()),
                         median_abs_beta_diff_over_sd_if_wrap=float(dw.median()) if len(dw) else 0.0,
                         max_abs_beta_diff_over_sd=float(g["beta_diff_over_sd"].abs().max()),
                         max_abs_z_gen_minus_obs=float((g["z_gen"] - g["z_obs"]).abs().max()),
                         false_exact_obs=int(g["false_obs"].sum()), false_exact_gen=int(g["false_gen"].sum()),
                         decisions_changed=int((g["false_obs"] != g["false_gen"]).sum()),
                         var_z_obs=g["z_obs"].var(), var_z_gen=g["z_gen"].var()))
    pd.DataFrame(rows).assign(**st).to_csv(out / "C1_T3_TRANSFORM.csv", index=False)
    print(checks.to_string(index=False))
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    if (checks["n_fail"] > 0).any():
        print("CONTROLLO FALLITO: vedi C1_CHECKS_DIRECT.csv")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
