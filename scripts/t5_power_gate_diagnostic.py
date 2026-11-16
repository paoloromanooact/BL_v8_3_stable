"""Diagnostic of the failed compatibility gate of scripts/t5_power_sensitivity.py (receipt GATE_b769892ffdd6).

Not pre-registered, not a reclassification: the gate stays 'non superata' and its receipt is not modified.
Question: where does the SE difference (3e-6 to 1.5e-5 relative, beta within 1.6e-15) on 4 of the 20 catalogues of
scenario 2 at effect -0.1 come from? For each of the 20 catalogues:
  A  original P2f path: V.responses(design, 2, rng, beta_frac=-0.1) -> V.units -> V.procedure_m, against VALIDATION_RAW;
  B  power-script path: noise catalogue (beta_frac=0) + linear mean phi*eta*(-0.1)*abar added afterwards -> M;
  the cell responses of A and B (floating-point order of the injection only), REML optimum of A and B;
  P  probe: path A with every d_star multiplied by (1 + 1e-15) -> M (sensitivity of M to rounding-level inputs).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_power_gate_diagnostic.py
"""
from __future__ import annotations

import json
import os
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
GATE = T.PRELIM / "GATE_b769892ffdd6/GATE.csv"
REML_COLS = ["phi", "kappa", "sigma_x2", "neg_reml", "n_valid_starts", "sigma_x_at_lower"]


def m_row(u, tag):
    r = V.procedure_m(u)
    return {f"{tag}_{k}": r[k] for k in ["beta", "se", "verdict"] + REML_COLS}


def main():
    if not T.guard_start():
        return 2
    commit = T.head_commit()
    out = T.PRELIM / f"GATE_DIAGNOSTIC_{commit[:12]}"
    out.mkdir(parents=True, exist_ok=False)
    meta = dict(mode="gate diagnostic (not pre-registered, no reclassification)", outcome="non riuscito",
                gate_receipt=str(GATE.relative_to(ROOT)), sha256_gate_csv=T.sha(GATE))
    rows, code, t0 = [], 1, time.time()
    try:
        meta.update(T.provenance())
        meta["sha256_diagnostic_script"] = T.sha(__file__)
        if T.sha(T.VALIDATION_RAW) != T.SHA_VALIDATION_RAW:
            raise T.TechnicalError("VALIDATION_RAW.csv.gz SHA-256 differs")
        design, _ = T.load_design()
        st = T.Statics(design)
        vr = pd.read_csv(T.VALIDATION_RAW, float_precision="round_trip", keep_default_na=False,
                         na_values=["", "nan", "NaN"], low_memory=False,
                         usecols=["test", "kind", "scenario", "effect", "k", "beta", "se", "verdict"] + REML_COLS)
        vr = vr[(vr["test"] == "T5") & (vr["kind"] == "effect") & (vr["scenario"] == 2) & (vr["effect"] == -0.1)]
        gate = pd.read_csv(GATE, float_precision="round_trip")
        for k in range(20):
            ref = vr[vr["k"] == k].iloc[0]
            seed = V.seed_effect(2, -0.1, k)
            ddA = V.responses(design, 2, np.random.default_rng(seed), -0.1)
            uA = V.units(ddA, "T5")
            uB, _ = T.build_units(st, T.noise_catalogue(design, 4, seed), st.linear(-0.1))
            ddP = ddA.assign(d_star=ddA["d_star"].to_numpy() * (1.0 + 1e-15))
            uP = V.units(ddP, "T5")
            row = dict(k=k, seed=seed, gate_passed=bool(gate.loc[gate["k"] == k, "passed"].iloc[0]),
                       ref_se=ref["se"], ref_neg_reml=ref["neg_reml"], ref_phi=ref["phi"], ref_kappa=ref["kappa"],
                       ref_sigma_x2=ref["sigma_x2"],
                       max_abs_d_eta_AB_over_eta=float(np.max(np.abs(uA["eta_c"] - uB["eta_c"]))) / T.ETA,
                       n_cells_d_eta_AB_nonzero=int((uA["eta_c"] != uB["eta_c"]).sum()))
            row.update(m_row(uA, "A"), **m_row(uB, "B"), **m_row(uP, "P"))
            for tag in ("A", "B", "P"):
                row[f"{tag}_rel_se_vs_ref"] = abs(row[f"{tag}_se"] - ref["se"]) / ref["se"]
                row[f"{tag}_d_neg_reml_vs_ref"] = row[f"{tag}_neg_reml"] - ref["neg_reml"]
                row[f"{tag}_d_phi_vs_ref"] = row[f"{tag}_phi"] - ref["phi"]
            rows.append(row)
            print(f"k{k}: gate {'PASS' if row['gate_passed'] else 'FAIL'}  A rel se {row['A_rel_se_vs_ref']:.2e}  "
                  f"B {row['B_rel_se_vs_ref']:.2e}  P {row['P_rel_se_vs_ref']:.2e}  "
                  f"max|d eta|/eta {row['max_abs_d_eta_AB_over_eta']:.1e} ({row['n_cells_d_eta_AB_nonzero']} cells)  "
                  f"d negREML B {row['B_d_neg_reml_vs_ref']:.2e}", flush=True)
        d = pd.DataFrame(rows)
        meta.update(n=len(d), A_max_rel_se=float(d["A_rel_se_vs_ref"].max()), B_max_rel_se=float(d["B_rel_se_vs_ref"].max()),
                    P_max_rel_se=float(d["P_rel_se_vs_ref"].max()), n_P_rel_se_gt_1e9=int((d["P_rel_se_vs_ref"] > 1e-9).sum()),
                    n_B_rel_se_gt_1e9=int((d["B_rel_se_vs_ref"] > 1e-9).sum()),
                    max_abs_d_eta_AB_over_eta=float(d["max_abs_d_eta_AB_over_eta"].max()),
                    verdicts_equal_A_B_P_ref=bool(((d["A_verdict"] == d["B_verdict"]) & (d["B_verdict"] == d["P_verdict"])).all()),
                    outcome="eseguita")
        code = 0
    except Exception as exc:                        # noqa: BLE001
        meta.update(outcome="non riuscito", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        print(traceback.format_exc())
    finally:
        meta["duration_s"] = time.time() - t0
        pd.DataFrame(rows).to_csv(out / "GATE_DIAGNOSTIC.csv", index=False)
        if not T.write_meta(out / "GATE_DIAGNOSTIC_META.json", meta):
            code = 1
        print(json.dumps({k: meta.get(k) for k in ("outcome", "A_max_rel_se", "B_max_rel_se", "P_max_rel_se",
                                                   "n_B_rel_se_gt_1e9", "n_P_rel_se_gt_1e9", "max_abs_d_eta_AB_over_eta",
                                                   "verdicts_equal_A_B_P_ref")}))
        print(f"receipt: {out.relative_to(ROOT)}")
    return code


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    sys.exit(main())
