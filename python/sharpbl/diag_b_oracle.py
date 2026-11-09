"""Controllo diagnostico B: procedura P2e con i parametri temporali veri (oracolo), V1-V4.

Piano registrato prima di questo codice: docs/DIAGNOSTIC_B_PLAN.md (commit 7d40b9b).
Sviluppo diagnostico, non validazione e non verdetto. Stessi cataloghi (semi 40000 + k) e
stessi semi della calibrazione interna della validazione P2e (60000 + 2k, 60001 + 2k): il
confronto con P2e e' appaiato. Unica sostituzione: phi, kappa, sigma_u^2 della simulazione nulla.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_b_oracle.py [--n 2000] [--workers 12]
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
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLAN = ROOT / "docs/DIAGNOSTIC_B_PLAN.md"
SCEN = ("V1", "V2", "V3", "V4")
SIGMA2_TRUE = {"T3": (0.5 * 15.0) ** 2, "T5": (0.5 * 2.0e-24) ** 2}
N_REPRO = 25
FALSE = ["quenching supportato (P2d)", "segno opposto (P2d)"]
_SILSO = None


def true_params(scenario, test):
    s = p2d.SCENARIOS[scenario]
    return dict(phi=s["phi"], kappa=s.get("kappa", 0.0), sigma_u2=SIGMA2_TRUE[test])


def null_sims(dz, M, seed, override=None, chunk=2000):
    """Copia di p2d.null_distribution con la sola sostituzione dei parametri temporali (piano §2)."""
    rng = np.random.default_rng(seed)
    lp = p2d.linear_pieces(dz)
    par = dict(lp["par"])
    if not par["applicable"]:
        return None, par
    if override is not None:
        par.update(override)
    sims = np.empty(M)
    for a in range(0, M, chunk):
        m = min(chunk, M - a)
        U = p2d.simulate_ar1(par, m, rng)
        V = rng.choice([-1.0, 1.0], size=(m, len(lp["ge"])))
        sims[a:a + m] = lp["const"] + np.einsum("mgh,gh->m", U, lp["B"]) + V @ lp["ge"]
    return sims, par


def one(args):
    global _SILSO
    scenario, k, mode, M = args
    if _SILSO is None:
        _SILSO = run_p2.load_silso()
    p2d.ESTIMATOR = "p2e"
    cat = p2d.synthetic_catalog_p2d(scenario, 40000 + k, 0.0, 0.0)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], _SILSO)
    out = []
    for test, seed in (("T3", 60000 + 2 * k), ("T5", 60001 + 2 * k)):
        dz = p2d.design_t3(d) if test == "T3" else p2d.design_t5(d)
        ov = true_params(scenario, test) if mode == "oracle" else None
        sims, par = null_sims(dz, M, seed, ov)
        verdict = "non applicabile (P2d §3)" if sims is None else p2d.decide(par["beta_obs"], sims)["verdict_p2d"]
        out.append(dict(scenario=scenario, k=k, test=test, mode=mode, verdict=verdict,
                        applicable=int(par["applicable"]), phi_used=par["phi"], kappa_used=par["kappa"],
                        sigma_u2_used=par["sigma_u2"]))
    return out


def cp_upper(x, n):
    return p2d.cp_upper(int(x), int(n))


def summarize(b, raw, a_sum):
    rows = []
    for (sc, test), g in b.groupby(["scenario", "test"]):
        o = raw[(raw["scenario"] == sc) & (raw["test"] == test)].set_index("k")
        g = g.set_index("k")
        fb = g["verdict"].isin(FALSE)
        fo = o.loc[g.index, "verdict"].isin(FALSE)
        app = g["applicable"] == 1
        n, n_app = len(g), int(app.sum())
        pb = fb[app].mean()
        se_b = np.sqrt(pb * (1 - pb) / n_app)
        po = fo[app].mean()
        se_o = np.sqrt(po * (1 - po) / n_app)
        a = a_sum[(a_sum["scenario"] == sc) & (a_sum["test"] == test)].iloc[0]
        rows.append(dict(
            scenario=sc, test=test, n=n, n_applicable=n_app, frac_not_applicable=1 - n_app / n,
            false_oracle=int(fb.sum()), false_oracle_frac=fb.sum() / n, false_oracle_cp_upper95=cp_upper(fb.sum(), n),
            false_oracle_among_applicable=pb, se_oracle=se_b,
            false_oracle_predicted_dir=int((g["verdict"] == FALSE[0]).sum()),
            false_oracle_opposite_dir=int((g["verdict"] == FALSE[1]).sum()),
            false_p2e=int(fo.sum()), false_p2e_among_applicable=po, se_p2e=se_o,
            paired_both=int((fb & fo).sum()), paired_only_p2e=int((~fb & fo).sum()),
            paired_only_oracle=int((fb & ~fo).sum()),
            A_p_oracle=a["p_oracle_mean"], oracle_minus_A_in_se=(pb - a["p_oracle_mean"]) / se_b,
            A_p_pred=a["p_pred_mean"], p2e_minus_A_in_se=(po - a["p_pred_mean"]) / se_o))
    return pd.DataFrame(rows)


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--M", type=int, default=p2d.M_MAIN)
    args = ap.parse_args()
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_DIAGNOSTIC_B_PLAN"] = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    st["status"] = "sviluppo diagnostico, nessun verdetto"
    out = ROOT / "results/DIAGNOSTIC"
    tag = "" if args.n == 2000 and args.M == p2d.M_MAIN else f"_N{args.n}_M{args.M}"
    raw = pd.read_csv(ROOT / "results/P2/P2E_VALIDATION_RAW.csv.gz")
    raw = raw[raw["beta_frac"] == 0]

    with Pool(args.workers) as pool:
        rep = pd.DataFrame([r for part in pool.imap_unordered(
            one, [(sc, k, "original", args.M) for sc in SCEN for k in range(min(N_REPRO, args.n))]) for r in part])
        m = rep.merge(raw[["scenario", "k", "test", "verdict"]], on=["scenario", "k", "test"], suffixes=("", "_raw"))
        n_diff = int((m["verdict"] != m["verdict_raw"]).sum())
        chk = [dict(check="1_reproduce_original_verdicts", n=len(m), n_fail=n_diff if args.M == p2d.M_MAIN else -1)]
        if args.M == p2d.M_MAIN and n_diff > 0:
            pd.DataFrame(chk).assign(**st).to_csv(out / f"B_CHECKS{tag}.csv", index=False)
            print(m[m["verdict"] != m["verdict_raw"]].to_string())
            print("CONTROLLO OBBLIGATORIO FALLITO: B si ferma (piano §4)")
            return 2
        print(f"riproduzione: {len(m)} confronti, {n_diff} differenze", flush=True)
        b = pd.DataFrame([r for part in pool.imap_unordered(
            one, [(sc, k, "oracle", args.M) for sc in SCEN for k in range(args.n)], chunksize=4) for r in part])

    b = b.sort_values(["scenario", "k", "test"]).reset_index(drop=True)
    app = b["applicable"] == 1
    exp = b[app].apply(lambda r: true_params(r["scenario"], r["test"]), axis=1, result_type="expand")
    bad = ((b.loc[app, "phi_used"] != exp["phi"]) | (b.loc[app, "kappa_used"] != exp["kappa"])
           | (b.loc[app, "sigma_u2_used"] != exp["sigma_u2"])).sum()
    chk.append(dict(check="2_oracle_parameters_used", n=int(app.sum()), n_fail=int(bad)))
    pd.DataFrame(chk).assign(**st).to_csv(out / f"B_CHECKS{tag}.csv", index=False)
    b.assign(**st).to_csv(out / f"B_RAW{tag}.csv.gz", index=False)
    if bad:
        print("CONTROLLO OBBLIGATORIO FALLITO: parametri oracolo non usati (piano §4)")
        return 2
    a_sum = pd.read_csv(out / "A_SUMMARY.csv")
    s = summarize(b, raw, a_sum)
    s.assign(**st).to_csv(out / f"B_SUMMARY{tag}.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(s.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
