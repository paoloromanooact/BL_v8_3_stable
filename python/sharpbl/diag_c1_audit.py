"""Verifica di coerenza di C1: generatore, distribuzione nulla e p-value (post hoc, nessuna simulazione nuova).

Usa solo output esistenti (A_BY_CATALOGUE, C_RAW_RUN1). Documento: docs/DIAGNOSTIC_C1_AUDIT.md.
Non preregistrata: verifica d'implementazione, nessun verdetto.

    .venv/bin/python python/sharpbl/diag_c1_audit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kstest, norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

FALSE = ["quenching supportato (P2d)", "segno opposto (P2d)"]
Z = norm.ppf(1 - p2d.ALPHA_SIDE)
# gruppi di scenari con le stesse estrazioni casuali (stessi semi; cr_component consuma lo stesso
# numero di normali negli AR(1), nessuna in V0, un numero diverso in V5 e V6)
GROUPS = {"V0": "G0", "V1": "G1", "V2": "G1", "V3": "G1", "V4": "G1", "V5": "G5", "V6": "G6"}


def main() -> int:
    out = ROOT / "results/DIAGNOSTIC"
    st = stamp(("P2", "P2d", "P2e"))
    st["status"] = "verifica post hoc, nessun verdetto"
    a = pd.read_csv(out / "A_BY_CATALOGUE.csv.gz")
    a["z"] = (a["beta_obs"] - a["mu_true"]) / np.sqrt(a["v_true"])
    a["exact_false"] = a["z"].abs() > Z

    rows = []
    for (sc, test), g in a.groupby(["scenario", "test"]):
        p = g["exact_false"].mean()
        rows.append(dict(scenario=sc, test=test, group=GROUPS[sc], n=len(g), var_z=g["z"].var(), mean_z=g["z"].mean(),
                         se_var_z=np.sqrt(2 / (len(g) - 1)), exact_false_frac=p, se=np.sqrt(p * (1 - p) / len(g)),
                         ks_p=kstest(g["z"], "norm").pvalue))
    pd.DataFrame(rows).assign(**st).to_csv(out / "AUDIT_C1_Z_BY_SCENARIO.csv", index=False)

    corr = []
    for test in ("T3", "T5"):
        w = a[a["test"] == test].pivot(index="k", columns="scenario", values="z")
        c = w.corr()
        for i in c.index:
            for j in c.columns:
                if i < j:
                    corr.append(dict(test=test, scenario_1=i, scenario_2=j, corr_z=c.loc[i, j]))
    pd.DataFrame(corr).assign(**st).to_csv(out / "AUDIT_C1_Z_CORR.csv", index=False)

    # un rappresentante per gruppo di realizzazioni del rumore (stesso disegno: stessi semi dei cataloghi)
    # e test; errore raggruppato per catalogo k (i 2000 cataloghi sono le unita' indipendenti)
    rep = a[a["scenario"].isin(["V0", "V1", "V5", "V6"])]
    rows = []
    for test, g in list(rep.groupby("test")) + [("T3+T5", rep)]:
        p = g["exact_false"].mean()
        per_k = g.groupby("k")["exact_false"].mean()
        rows.append(dict(test=test, groups="V0, V1 (per V1-V4), V5, V6", n_indicators=len(g), n_catalogues=len(per_k),
                         exact_false_frac=p, se_binomial_naive=np.sqrt(p * (1 - p) / len(g)),
                         se_clustered_by_catalogue=per_k.std(ddof=1) / np.sqrt(len(per_k))))
    pd.DataFrame(rows).assign(**st).to_csv(out / "AUDIT_C1_POOLED_GROUPS.csv", index=False)

    c = pd.read_csv(out / "C_RAW_RUN1.csv.gz")
    c1 = c[c["arm"] == "C1"].merge(a[["scenario", "k", "test", "z", "exact_false"]], on=["scenario", "k", "test"])
    c1["mc_false"] = c1["verdict"].isin(FALSE)
    rows = []
    for (sc, test), g in c1.groupby(["scenario", "test"]):
        rows.append(dict(scenario=sc, test=test, n=len(g), mc_false=int(g["mc_false"].sum()),
                         exact_false=int(g["exact_false"].sum()), concordant=int((g["mc_false"] == g["exact_false"]).sum()),
                         discordant_max_abs_z_margin=float((g.loc[g["mc_false"] != g["exact_false"], "z"].abs() - Z)
                                                           .abs().max()) if (g["mc_false"] != g["exact_false"]).any() else 0.0))
    pd.DataFrame(rows).assign(**st).to_csv(out / "AUDIT_C1_MC_VS_EXACT.csv", index=False)
    for f in sorted(out.glob("AUDIT_C1_*.csv")):
        d = pd.read_csv(f)
        print(f.name)
        print(d.drop(columns=[x for x in d.columns if x.startswith("sha256") or x in ("git_commit", "git_dirty", "status")])
              .round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
