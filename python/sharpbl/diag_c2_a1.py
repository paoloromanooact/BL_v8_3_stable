"""Riesecuzione del braccio C2 del controllo diagnostico C secondo l'emendamento A1.

Piano: docs/DIAGNOSTIC_C_PLAN.md (df63fd2) con docs/DIAGNOSTIC_C_PLAN_A1.md (f275f0d, non cieco,
scritto dopo l'ispezione della prima esecuzione). Sviluppo diagnostico, non validazione e non
verdetto. Per le unita' con E[e~^2] = 0 (celle con una sola unita') si aggiunge il termine
oracolo a_i sigma_i z_i da un generatore separato (semi 360000 + 2k, 360001 + 2k); la sequenza
casuale del braccio B resta intatta. Un valore non finito non produce mai un verdetto.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_c2_a1.py [--n 2000] [--workers 12]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import diag_c_individual as dc  # noqa: E402
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.diag_b_oracle import FALSE, null_sims, true_params  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLANS = (ROOT / "docs/DIAGNOSTIC_C_PLAN.md", ROOT / "docs/DIAGNOSTIC_C_PLAN_A1.md")
SCEN = ("V1", "V4")
ERROR = "errore (non finito)"
N_REPRO_SIMS, N_REPRO_VERDICTS = 10, 25


def unit_ok(up):
    eet2, ee2, sig = up["eet2"], up["ee2"], up["sig"]
    pos = eet2 > 0
    s = np.zeros_like(eet2)
    with np.errstate(divide="ignore", invalid="ignore"):
        s[pos] = np.sqrt(sig[pos] ** 2 / eet2[pos])
    ok = (np.isfinite(sig).all() and (sig > 0).all() and np.isfinite(ee2).all() and (ee2 >= 0).all()
          and np.isfinite(eet2).all() and (eet2 >= 0).all() and np.isfinite(s).all()
          and np.isfinite(up["lp"]["ge"]).all() and np.isfinite(up["a"]).all())
    return bool(ok), s, ~pos


def sims_a1(up, par, M, seed, seed2, s, zero, chunk=2000):
    rng = np.random.default_rng(seed)          # stessa sequenza del braccio B
    rng2 = np.random.default_rng(seed2)        # generatore separato per il termine oracolo
    lp = up["lp"]
    gi = lp["ge"] * s
    extra = up["a"][zero] * up["sig"][zero]
    out = np.empty(M)
    for a in range(0, M, chunk):
        m = min(chunk, M - a)
        U = p2d.simulate_ar1(par, m, rng)
        V = rng.choice([-1.0, 1.0], size=(m, len(gi)))
        x = lp["const"] + np.einsum("mgh,gh->m", U, lp["B"]) + V @ gi
        if zero.any():
            x = x + rng2.standard_normal((m, int(zero.sum()))) @ extra
        out[a:a + m] = x
    return out


def one(args):
    scenario, k, mode, M = args
    if dc._SILSO is None:
        dc._SILSO = run_p2.load_silso()
    p2d.ESTIMATOR = "p2e"
    d = dc.catalogue(scenario, k)
    out = []
    for t, test in enumerate(("T3", "T5")):
        up = dc.unit_pieces(scenario, d, test)
        par = dict(up["lp"]["par"])
        seed, seed2 = 60000 + 2 * k + t, 360000 + 2 * k + t
        ok, s, zero = unit_ok(up)
        a, s2 = up["a"], up["sig"] ** 2
        row = dict(scenario=scenario, k=k, test=test, mode=mode, applicable=int(par["applicable"]),
                   units_finite=int(ok), n_units=len(a), n_zero_units=int(zero.sum()),
                   share_true_ind_var_zero_units=float(np.sum(a[zero] ** 2 * s2[zero]) / np.sum(a ** 2 * s2)))
        if not par["applicable"]:
            row.update(verdict="non applicabile (P2d §3)", sims_finite=1)
        elif mode == "repro":
            par.update(true_params(scenario, test))
            mine = sims_a1(up, par, M, seed, seed2, np.ones_like(s), np.zeros_like(zero))
            ref, _ = null_sims(up["dz"], M, seed, true_params(scenario, test))
            row.update(sims_equal_B=int(np.array_equal(mine, ref)), sims_finite=int(np.isfinite(mine).all()),
                       verdict=p2d.decide(par["beta_obs"], mine)["verdict_p2d"])
        else:
            par.update(true_params(scenario, test))
            if not ok:
                row.update(verdict=ERROR, sims_finite=0)
            else:
                x = sims_a1(up, par, M, seed, seed2, s, zero)
                fin = bool(np.isfinite(x).all())
                row.update(sims_finite=int(fin), verdict=p2d.decide(par["beta_obs"], x)["verdict_p2d"] if fin else ERROR)
        out.append(row)
    return out


def counts(g):
    f = g["verdict"].isin(FALSE)
    app = g["applicable"] == 1
    p = f[app].mean()
    n = len(g)
    return dict(n=n, n_applicable=int(app.sum()), n_error=int((g["verdict"] == ERROR).sum()), false=int(f.sum()),
                false_cp_upper95=p2d.cp_upper(int(f.sum()), n), false_among_applicable=p,
                se=np.sqrt(p * (1 - p) / app.sum()), false_predicted_dir=int((g["verdict"] == FALSE[0]).sum()),
                false_opposite_dir=int((g["verdict"] == FALSE[1]).sum()),
                frac_catalogues_with_zero_units=float((g["n_zero_units"] > 0).mean()),
                share_true_ind_var_zero_units_median=float(g["share_true_ind_var_zero_units"].median()))


def main() -> int:
    from multiprocessing import Pool
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()
    M = p2d.M_MAIN
    st = stamp(("P2", "P2d", "P2e"))
    for pl in PLANS:
        st[f"sha256_{pl.stem}"] = hashlib.sha256(pl.read_bytes()).hexdigest()
    st["status"] = "sviluppo diagnostico, nessun verdetto"
    out = ROOT / "results/DIAGNOSTIC"
    tag = "" if args.n == 2000 else f"_N{args.n}"
    braw = pd.read_csv(out / "B_RAW.csv.gz")
    chk = []

    # controllo 5: analitica e C1 della prima esecuzione finite
    an1 = pd.read_csv(out / "C_ANALYTIC_BY_CATALOGUE_RUN1.csv.gz")
    c1 = pd.read_csv(out / "C_RAW_RUN1.csv.gz")
    c1 = c1[c1["arm"] == "C1"]
    num = an1.select_dtypes("number").drop(columns=["git_dirty", "R_ind"], errors="ignore")
    chk.append(dict(check="5_run1_analytic_finite", n=len(an1), n_fail=int((~np.isfinite(num)).any(axis=1).sum())))
    chk.append(dict(check="5_run1_C1_verdicts_valid", n=len(c1),
                    n_fail=int((~c1["verdict"].isin(FALSE + ["non deciso (P2d)", "non applicabile (P2d §3)"])).sum())))

    with Pool(args.workers) as pool:
        rep = pd.DataFrame([r for part in pool.imap_unordered(
            one, [(sc, k, "repro", M) for sc in SCEN for k in range(min(N_REPRO_VERDICTS, args.n))]) for r in part])
        rs = rep[rep["k"] < N_REPRO_SIMS]
        chk.append(dict(check="3_sims_equal_B_numerically", n=len(rs), n_fail=int((rs["sims_equal_B"] != 1).sum())))
        m = rep.merge(braw[["scenario", "k", "test", "verdict"]], on=["scenario", "k", "test"], suffixes=("", "_B"))
        chk.append(dict(check="3_verdicts_equal_B", n=len(m), n_fail=int((m["verdict"] != m["verdict_B"]).sum())))
        pre = pd.DataFrame(chk)
        if (pre["n_fail"] > 0).any():
            pre.assign(**st).to_csv(out / f"C2_A1_CHECKS{tag}.csv", index=False)
            print(pre.to_string(index=False))
            print("CONTROLLO OBBLIGATORIO FALLITO: la riesecuzione si ferma (A1 §4)")
            return 2
        print(pre.to_string(index=False), flush=True)
        res = pd.DataFrame([r for part in pool.imap_unordered(
            one, [(sc, k, "A1", M) for sc in SCEN for k in range(args.n)], chunksize=4) for r in part])

    res = res.sort_values(["scenario", "k", "test"]).reset_index(drop=True)
    chk.append(dict(check="1_units_finite", n=len(res), n_fail=int((res["units_finite"] != 1).sum())))
    chk.append(dict(check="2_sims_finite_no_error", n=len(res),
                    n_fail=int(((res["sims_finite"] != 1) | (res["verdict"] == ERROR)).sum())))
    run1 = pd.read_csv(out / "C_RAW_RUN1.csv.gz")
    r1 = run1[(run1["arm"] == "C2") & (run1["test"] == "T5")][["scenario", "k", "verdict"]]
    t5 = res[res["test"] == "T5"].merge(r1, on=["scenario", "k"], suffixes=("", "_run1"))
    t5_zero = int((t5["n_zero_units"] > 0).sum())
    chk.append(dict(check="4_T5_no_zero_units", n=len(t5), n_fail=t5_zero))
    chk.append(dict(check="4_T5_verdicts_equal_run1", n=len(t5),
                    n_fail=int((t5["verdict"] != t5["verdict_run1"]).sum()) if t5_zero == 0 else -1))
    c = pd.DataFrame(chk)
    c.assign(**st).to_csv(out / f"C2_A1_CHECKS{tag}.csv", index=False)
    res.assign(**st).to_csv(out / f"C2_A1_RAW{tag}.csv.gz", index=False)
    print(c.to_string(index=False))
    if (c["n_fail"] != 0).any():
        print("CONTROLLO OBBLIGATORIO FALLITO (A1 §4): output conservati, nessuna sintesi")
        return 2

    rows = []
    for (sc, test), g in res.groupby(["scenario", "test"]):
        r = dict(scenario=sc, test=test, **counts(g))
        b = braw[(braw["scenario"] == sc) & (braw["test"] == test)].set_index("k")["verdict"]
        gv = g.set_index("k")["verdict"]
        b = b.reindex(gv.index)
        fb, fc = b.isin(FALSE), gv.isin(FALSE)
        r.update(paired_both=int((fb & fc).sum()), paired_only_B=int((fb & ~fc).sum()),
                 paired_only_C2=int((~fb & fc).sum()), verdicts_changed=int((b != gv).sum()))
        c1g = c1[(c1["scenario"] == sc) & (c1["test"] == test)]
        fc1 = c1g["verdict"].isin(FALSE)
        p1 = fc1[c1g["applicable"] == 1].mean()
        r.update(C1_false_among_applicable=p1, C1_se=np.sqrt(p1 * (1 - p1) / (c1g["applicable"] == 1).sum()))
        rows.append(r)
    s = pd.DataFrame(rows)
    bs = pd.read_csv(out / "B_SUMMARY.csv")[["scenario", "test", "false_oracle_among_applicable", "se_oracle"]]
    s = s.merge(bs, on=["scenario", "test"], how="left")
    s.assign(**st).to_csv(out / f"C2_A1_SUMMARY{tag}.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(s.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
