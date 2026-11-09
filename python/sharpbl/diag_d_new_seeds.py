"""Controllo diagnostico D: livello della decisione al 2,5% sotto il modello nullo del generatore, cataloghi nuovi.

Piano registrato prima di questo codice: docs/DIAGNOSTIC_D_PLAN.md (ef56df9) con l'emendamento
docs/DIAGNOSTIC_D_PLAN_A1.md (cfddaee). Sviluppo diagnostico, non validazione di P2f e non verdetto.
Una sola esecuzione sui semi nuovi. L'opzione --dev usa i cataloghi di sviluppo (semi 40000 + k)
solo per provare il codice: i suoi output hanno il suffisso _DEV e non si interpretano.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_d_new_seeds.py [--workers 12]
"""
from __future__ import annotations

import argparse
import hashlib
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

PLANS = (ROOT / "docs/DIAGNOSTIC_D_PLAN.md", ROOT / "docs/DIAGNOSTIC_D_PLAN_A1.md")
SCEN = {"V0": 0, "V1": 1, "V2": 2, "V3": 3, "V4": 4}
MAIN = ("V1", "V4")
N_NEW = 10000
N_MC = 100
Z = norm.ppf(1 - p2d.ALPHA_SIDE)
USED = [(30000, 32000), (40000, 42000), (50000, 54000), (60000, 64002), (70000, 72000), (100000, 100500),
        (140000, 140500), (260000, 264002), (360000, 364002), (20261103, 20261113), (20261106, 20271107)]


def cat_seed(s, k, dev):
    return 40000 + k if dev else 1_000_000 + 100_000 * s + k


def mc_seed(s, k, t, dev):
    return 260000 + 2 * k + t if dev else 1_900_000 + 10_000 * s + 2 * k + t


def seeds_ok(n, dev):
    if dev:
        return True
    seeds = [cat_seed(s, k, False) for s in SCEN.values() for k in range(n)]
    seeds += [mc_seed(SCEN[sc], k, t, False) for sc in MAIN for k in range(N_MC) for t in (0, 1)]
    clash = any(lo <= x < hi for x in seeds for lo, hi in USED)
    return (not clash) and len(set(seeds)) == len(seeds)


def truth(scenario, cat, d, test):
    """a, y, mu, V_true come nel controllo A (stesse formule e funzioni)."""
    spec = p2d.SCENARIOS[scenario]
    dz = p2d.design_t3(d) if test == "T3" else p2d.design_t5(d)
    lp = p2d.linear_pieces(dz)
    par = lp["par"]
    if test == "T3":
        a = p2d.wls_row(dz["Xf"], dz["w"])
        y, wphi = dz["y"], dz["w"]
        dd = d[np.isfinite(d[da.ACT])]
        mu = float(a @ (da.GAMMA0 * dd["sinlat"].to_numpy()))
        sd_e, sd_x = da.SD_T, 0.5 * da.SD_T
    else:
        a = p2d.wls_row(dz["Xf_c"], dz["W_c"])[dz["k_of_i"]] * dz["agg"]
        y, wphi = dz["z"], dz["phi"]
        mu = float(da.ETA0 * a.sum())
        sd_e, sd_x = da.ETA0, 0.5 * da.ETA0
    med = float(np.median(cat["USFLUX"]))
    c = (wphi / med) ** -0.25 if spec.get("hetero") else np.ones_like(wphi)
    grid = par["lo"] + np.arange(par["grid_len"])
    v_true = float(sd_e ** 2 * np.sum(a ** 2 * c ** 2)) + sd_x ** 2 * da.quad(
        lp["B"], da.k_true(spec, grid, int(cat["CR"].min())))
    return float(a @ y), mu, v_true


def one(args):
    scenario, k, dev, mc = args
    if dc._SILSO is None:
        dc._SILSO = run_p2.load_silso()
    da._SILSO = dc._SILSO
    p2d.ESTIMATOR = "p2e"
    s = SCEN[scenario]
    cat = p2d.synthetic_catalog_p2d(scenario, cat_seed(s, k, dev), 0.0, 0.0)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], dc._SILSO)
    d.attrs["med_phi"] = float(np.median(cat["USFLUX"]))
    out = []
    for t, test in enumerate(("T3", "T5")):
        beta, mu, v = truth(scenario, cat, d, test)
        z = (beta - mu) / np.sqrt(v) if v > 0 else np.nan
        row = dict(scenario=scenario, k=k, test=test, beta=beta, mu_true=mu, v_true=v, z=z,
                   finite=int(np.isfinite([beta, mu, v, z]).all() and v > 0),
                   mean_small=int(abs(mu) <= 1e-6 * np.sqrt(v)) if v > 0 else 0,
                   false_analytic=int(abs(z) > Z) if np.isfinite(z) else -1)
        if mc:
            up = dc.unit_pieces(scenario, d, test)
            par = dict(up["lp"]["par"])
            par.update(true_params(scenario, test))
            x = dc.simulate(up, par, p2d.M_MAIN, mc_seed(s, k, t, dev), "C1")
            ok = bool(np.isfinite(x).all())
            row.update(mc_finite=int(ok), false_mc=int(p2d.decide(par["beta_obs"], x)["verdict_p2d"] in FALSE) if ok else -1)
        out.append(row)
    return out


def clustered(g):
    m = g.groupby(["scenario", "k"])["false_analytic"].mean()
    f = g["false_analytic"].mean()
    se = m.std(ddof=1) / np.sqrt(len(m))
    return f, se, len(m), len(g)


def outcome(f, se):
    zz = (f - 0.025) / se
    if zz > 2:
        return "eccesso rilevato nella nuova prova secondo il criterio fissato"
    if zz < -2:
        return "sotto il nominale nella nuova prova secondo il criterio fissato"
    return "compatibile con il 2,5% nella nuova prova"


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dev", action="store_true", help="prova del codice sui cataloghi di sviluppo (non si interpreta)")
    ap.add_argument("--n", type=int, default=N_NEW)
    args = ap.parse_args()
    dev = args.dev
    if not dev and args.n != N_NEW:
        print("la numerosita' e' fissata dal piano (10 000): --n solo con --dev")
        return 1
    tag = "_DEV" if dev else ""
    st = stamp(("P2", "P2d", "P2e"))
    for pl in PLANS:
        st[f"sha256_{pl.stem}"] = hashlib.sha256(pl.read_bytes()).hexdigest()
    st["status"] = "prova del codice, non interpretare" if dev else "sviluppo diagnostico, nessun verdetto"
    out = ROOT / "results/DIAGNOSTIC"
    chk = [dict(check="3_seeds_new_distinct", n=1, n_fail=int(not seeds_ok(args.n, dev)))]

    # controllo 1: codice invariato rispetto ad A sul catalogo di sviluppo k = 0 (semi 40000)
    a_ref = pd.read_csv(out / "A_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "test", "beta_obs", "mu_true", "v_true"])
    a_ref = a_ref[a_ref["k"] == 0].rename(columns={"beta_obs": "beta_A", "mu_true": "mu_A", "v_true": "v_A"})
    ref = pd.DataFrame([r for sc in MAIN for r in one((sc, 0, True, False))]).merge(a_ref, on=["scenario", "k", "test"])
    bad = (~np.isclose(ref["beta"], ref["beta_A"], rtol=1e-9, atol=0)
           | ~np.isclose(ref["v_true"], ref["v_A"], rtol=1e-9, atol=0)
           | (np.abs(ref["mu_true"] - ref["mu_A"]) > 1e-9 * np.sqrt(ref["v_A"])))
    chk.append(dict(check="1_code_unchanged_vs_A", n=len(ref), n_fail=int(bad.sum()) if len(ref) == 4 else 4))
    if any(c["n_fail"] for c in chk):
        pd.DataFrame(chk).assign(**st).to_csv(out / f"D_CHECKS{tag}.csv", index=False)
        print(pd.DataFrame(chk).to_string(index=False))
        print("CONTROLLO OBBLIGATORIO FALLITO: D si ferma (piano §6)")
        return 2

    jobs = [(sc, k, dev, sc in MAIN and k < N_MC) for sc in SCEN for k in range(args.n)]
    with Pool(args.workers) as pool:
        res = pd.DataFrame([r for part in pool.imap_unordered(one, jobs, chunksize=8) for r in part])
    res = res.sort_values(["scenario", "k", "test"]).reset_index(drop=True)
    res.assign(**st).to_csv(out / f"D_BY_CATALOGUE{tag}.csv.gz", index=False)

    chk.append(dict(check="2_finite", n=len(res), n_fail=int((res["finite"] != 1).sum())))
    chk.append(dict(check="2_mean_small", n=len(res), n_fail=int((res["mean_small"] != 1).sum())))
    mc = res[res["false_mc"].notna()] if "false_mc" in res else res.iloc[0:0]
    disc = mc[(mc["false_mc"] != mc["false_analytic"])]
    chk.append(dict(check="4_mc_sims_finite", n=len(mc), n_fail=int((mc["mc_finite"] != 1).sum())))
    chk.append(dict(check="4_mc_vs_analytic_concordant_except_near_threshold", n=len(mc),
                    n_fail=int((np.abs(disc["z"].abs() - Z) >= 0.05).sum())))
    c = pd.DataFrame(chk)
    c.assign(**st).to_csv(out / f"D_CHECKS{tag}.csv", index=False)
    print(c.to_string(index=False))
    if (c["n_fail"] > 0).any():
        print("CONTROLLO OBBLIGATORIO FALLITO: D si ferma (piano §6); risultati non interpretati")
        return 2

    rows = []
    for (sc, test), g in res.groupby(["scenario", "test"]):
        n = len(g)
        f = g["false_analytic"].mean()
        se = np.sqrt(f * (1 - f) / n)
        rows.append(dict(scenario=sc, test=test, n=n, false=int(g["false_analytic"].sum()), f=f, se=se,
                         z_vs_nominal=(f - 0.025) / se if se > 0 else np.nan,
                         var_z=g["z"].var(), se_var_z=np.sqrt(2 / (n - 1)), mean_z=g["z"].mean(),
                         n_mc=int(g["false_mc"].notna().sum()) if "false_mc" in g else 0,
                         mc_discordant=int((g["false_mc"].notna() & (g["false_mc"] != g["false_analytic"])).sum())
                         if "false_mc" in g else 0))
    pd.DataFrame(rows).assign(**st).to_csv(out / f"D_SUMMARY{tag}.csv", index=False)
    crit = []
    for name, scs in (("D1", MAIN), ("D2", tuple(SCEN))):
        f, se, G, n_ind = clustered(res[res["scenario"].isin(scs)])
        crit.append(dict(criterion=name, scenarios=", ".join(scs), tests="T3, T5", n_indicators=n_ind,
                         n_catalogues=G, f=f, se_clustered=se, statistic=(f - 0.025) / se, outcome=outcome(f, se)))
    pd.DataFrame(crit).assign(**st).to_csv(out / f"D_CRITERIA{tag}.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(pd.DataFrame(rows).round(4).to_string(index=False))
        print(pd.DataFrame(crit).round(5).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
