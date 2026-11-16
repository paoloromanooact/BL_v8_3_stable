"""Descriptive supplement to the gate diagnostic (docs/T5_POWER_SENSITIVITY_PLAN_A2.md §2), fixed before running.

Same three paths and the same 20 catalogues (scenario 2, effect -0.1) as scripts/t5_power_gate_diagnostic.py:
  A  original P2f path (V.responses with beta_frac = -0.1);
  B  injection path of the power script (noise catalogue + linear mean added afterwards);
  P  path A with every d_star multiplied by (1 + 1e-15).
Records, besides beta and SE of M, the two optimisations inside M separately: variance function (var_a, var_b,
maximum relative difference of the rebuilt individual variances vs A) and REML (phi, kappa, sigma_x2, neg_reml),
and G (beta_G, SE_G, verdict) with differences vs A. Descriptive only: no tolerance, no decision, no change to
any gate outcome.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_gate_diagnostic_v2.py
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import t5_power_sensitivity as T  # noqa: E402

V = T.V
REML = ["phi", "kappa", "sigma_x2", "neg_reml", "n_valid_starts", "sigma_x_at_lower"]


def paths(design, st, seed):
    ddA = V.responses(design, 2, np.random.default_rng(seed), -0.1)
    uA = V.units(ddA, "T5")
    uB, _ = T.build_units(st, T.noise_catalogue(design, 4, seed), st.linear(-0.1))
    uP = V.units(ddA.assign(d_star=ddA["d_star"].to_numpy() * (1.0 + 1e-15)), "T5")
    return dict(A=uA, B=uB, P=uP)


def main():
    if not T.guard_start():
        return 2
    design, dinfo = T.load_design()
    commit = T.head_commit()
    out = T.PRELIM / f"GATE_DIAGNOSTIC_V2_{commit[:12]}"
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(mode="gate diagnostic supplement (A2 §2, descriptive, no tolerance)", outcome="non riuscito",
                sha256_diagnostic_script=T.sha(__file__))
    meta.update(T.provenance(dinfo["design_fingerprint"]), **dinfo)
    rows, code, t0 = [], 1, time.time()
    try:
        T.check_inputs()
        st = T.Statics(design)
        for k in range(20):
            seed = V.seed_effect(2, -0.1, k)
            us = paths(design, st, seed)
            row = dict(k=k, seed=seed)
            sigA = None
            for tag, u in us.items():
                try:
                    rm = T.method_m(u)
                except T.ExpectedError as exc:
                    row[f"{tag}_M_error"] = str(exc)
                    continue
                sig2 = T.g_sig2(u, rm)
                if tag == "A":
                    sigA = sig2
                row.update({f"{tag}_M_beta": rm["beta"], f"{tag}_M_se": rm["se"], f"{tag}_M_verdict": rm["verdict"],
                            f"{tag}_var_a": rm["var_a"], f"{tag}_var_b": rm["var_b"],
                            **{f"{tag}_{c}": rm[c] for c in REML}})
                if sigA is not None:
                    row[f"{tag}_max_rel_sig2_vs_A"] = float(np.max(np.abs(sig2 - sigA) / sigA))
                try:
                    rg = T.method_g(u, rm)
                    row.update({f"{tag}_G_beta": rg["beta"], f"{tag}_G_se": rg["se"], f"{tag}_G_verdict": rg["verdict"]})
                except T.ExpectedError as exc:
                    row[f"{tag}_G_error"] = str(exc)
            for tag in ("B", "P"):
                for q in ("M_se", "G_se", "G_beta"):
                    a, b = row.get(f"A_{q}"), row.get(f"{tag}_{q}")
                    if a is not None and b is not None:
                        row[f"{tag}_rel_{q}_vs_A"] = abs(b - a) / abs(a)
                for q in ("var_a", "var_b", "phi", "kappa", "neg_reml"):
                    row[f"{tag}_d_{q}_vs_A"] = row[f"{tag}_{q}"] - row[f"A_{q}"]
                row[f"{tag}_rel_sigma_x2_vs_A"] = abs(row[f"{tag}_sigma_x2"] - row["A_sigma_x2"]) / row["A_sigma_x2"]
            rows.append(row)
            print(f"k{k}: M se B {row['B_rel_M_se_vs_A']:.1e} P {row['P_rel_M_se_vs_A']:.1e} | varfun sig2 B "
                  f"{row['B_max_rel_sig2_vs_A']:.1e} P {row['P_max_rel_sig2_vs_A']:.1e} | sigma_x2 B "
                  f"{row['B_rel_sigma_x2_vs_A']:.1e} P {row['P_rel_sigma_x2_vs_A']:.1e} | G se B "
                  f"{row['B_rel_G_se_vs_A']:.1e} P {row['P_rel_G_se_vs_A']:.1e} | G beta B {row['B_rel_G_beta_vs_A']:.1e} "
                  f"P {row['P_rel_G_beta_vs_A']:.1e}", flush=True)
        d = pd.DataFrame(rows)
        summ = {}
        for tag in ("B", "P"):
            for q in ("rel_M_se_vs_A", "max_rel_sig2_vs_A", "rel_sigma_x2_vs_A", "rel_G_se_vs_A", "rel_G_beta_vs_A"):
                c = f"{tag}_{q}"
                summ[c] = dict(max=float(d[c].max()), n_nonzero=int((d[c] != 0).sum()))
            for m in ("M", "G"):
                summ[f"{tag}_{m}_verdicts_equal_A"] = int((d[f"{tag}_{m}_verdict"] == d[f"A_{m}_verdict"]).sum())
        meta.update(n=len(d), summary=summ, outcome="eseguita")
        code = 0
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        print(traceback.format_exc())
    finally:
        pd.DataFrame(rows).to_csv(out / "GATE_DIAGNOSTIC_V2.csv", index=False)
        code = T.finish(out, "GATE_DIAGNOSTIC_V2_META.json", meta, code, t0, ("outcome", "n", "summary"))
    return code


if __name__ == "__main__":
    sys.exit(main())
