"""Controlli del pilota P2f (docs/P2F_PILOT_IMPLEMENTATION_NOTE.md): nessun risultato nuovo, nessun verdetto.

    .venv/bin/python python/sharpbl/p2f_checks.py design   # conteggi del disegno congelato -> DESIGN_CHECKS.csv (prima degli esiti)
    .venv/bin/python python/sharpbl/p2f_checks.py raw      # finitezza e riconteggio indipendente di PILOT_RAW.csv.gz -> POST_CHECKS.csv

`design` non legge risposte reali (usa `p2f_pilot.build_design`) e genera risposte sintetiche con il seme
5 000 950 (intervallo dei test preliminari, mai usato) solo per costruire le unita'. `raw` ricalcola i
verdetti dalle statistiche, verifica che siano finite in ogni riga con esito, applica la regola `errore` alle
eventuali righe non finite e riconta falsi verdetti, potenza e scelta con le regole del piano §5 e A1 §4,
confrontandoli con le tabelle scritte dal pilota. Gli output del pilota non vengono modificati: il riconteggio e le
righe riclassificate sono salvati a parte (POST_CHECKS_*_RECOUNT.csv, POST_CHECKS_NONFINITE_ROWS.csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2f_pilot as P  # noqa: E402

SEED_DESIGN = 5_000_950


def design_checks():
    d = P.build_design()
    dd = P.responses(d, 0, np.random.default_rng(SEED_DESIGN))
    u3, u5 = P.test_units(dd, "T3"), P.test_units(dd, "T5")
    c3, _ = P.cell_keys(u3["cr"], u3["hem"])
    sz3 = np.bincount(c3)
    rows = [("design_regions", len(d)), ("design_first_CR", int(d["CR"].min())), ("design_last_CR", int(d["CR"].max())),
            ("design_n_CR", int(d["CR"].nunique())),
            ("T3_regions", len(u3["y"])), ("T3_cells", len(sz3)), ("T3_singleton_cells", int((sz3 == 1).sum())),
            ("T3_first_CR", int(u3["cr"].min())), ("T3_last_CR", int(u3["cr"].max())),
            ("T5_cells", len(u5["W_c"])), ("T5_regions", len(u5["y"])), ("T5_n_CR", int(len(np.unique(u5["cell_cr"])))),
            ("T5_first_CR", int(u5["cell_cr"].min())), ("T5_last_CR", int(u5["cell_cr"].max())),
            ("sinlat_min", float(d["sinlat"].min())), ("sinlat_max", float(d["sinlat"].max())),
            ("phi_median_design", float(np.median(d["phi"]))), ("phi_median_T5_regions", float(np.median(u5["phi"]))),
            ("m_logphi_T3", float(np.mean(np.log(u3["phi"])))), ("m_logphi_T5", float(np.mean(np.log(u5["phi"]))))]
    for name, u in (("T3", u3), ("T5", u5)):
        _, _, _, _, cr = P.b_units(u)
        cl = (cr - cr.min()) // P.BLOCK
        rows.append((f"{name}_blocks_with_data_code_partition", int(len(np.unique(cl)))))
        rows.append((f"{name}_blocks_with_data_from_design_first_CR", int(len(np.unique((cr - int(d["CR"].min())) // P.BLOCK)))))
        rows.append((f"{name}_block_origin_CR_code", int(cr.min())))
    # celle T3 con regioni di due cicli (A1 §2: due elementi non nulli nella riga aggregata)
    Xc = P.cell_level(u3, np.ones(len(u3["y"])))[1]
    rows.append(("T3_cells_two_cycles", int(((Xc != 0).sum(axis=1) > 1).sum())))
    out = pd.DataFrame(rows, columns=["quantity", "value"]).assign(seed_synthetic=SEED_DESIGN, **P.provenance())
    out.to_csv(P.OUT / "DESIGN_CHECKS.csv", index=False)
    print(out[["quantity", "value"]].to_string(index=False))
    return 0


def recount(raw):
    """Riconteggio indipendente con le regole del piano §5 e A1 §4 (stessa logica, scritta a parte)."""
    null = raw[raw["kind"] == "null"]
    fv = []
    for (test, cand, s), g in null.groupby(["test", "cand", "scenario"]):
        false = int(g["verdict"].isin(["supportato", "opposto"]).sum())
        err = int((g["verdict"] == "errore").sum())
        fv.append(dict(test=test, cand=cand, scenario=s, n=len(g), false=false, errors=err,
                       scenario_ok=bool(false <= 40 and err / len(g) <= 0.02)))
    fv = pd.DataFrame(fv)
    pw = []
    for (test, cand, s, e), g in raw[raw["kind"] == "power"].groupby(["test", "cand", "scenario", "effect"]):
        pw.append(dict(test=test, cand=cand, scenario=s, effect=e, n=len(g), power=float((g["verdict"] == "supportato").mean())))
    pw = pd.DataFrame(pw)
    ch = []
    for test in ("T3", "T5"):
        kept = {c: bool(fv[(fv["test"] == test) & (fv["cand"] == c)]["scenario_ok"].all()) and
                len(fv[(fv["test"] == test) & (fv["cand"] == c)]) == 9 for c in ("M", "B")}
        pm = {c: float(pw[(pw["test"] == test) & (pw["cand"] == c) & np.isclose(pw["effect"], -0.2)]["power"].mean())
              for c in ("M", "B")}
        if kept["M"] and kept["B"]:
            pick = "M" if pm["M"] > pm["B"] + 0.02 else "B"
        elif kept["M"]:
            pick = "M"
        elif kept["B"]:
            pick = "B"
        else:
            pick = "nessuna"
        ch.append(dict(test=test, kept_M=kept["M"], kept_B=kept["B"], power_M=pm["M"], power_B=pm["B"], choice=pick))
    return fv, pw, pd.DataFrame(ch)


def raw_checks():
    raw = pd.read_csv(P.OUT / "PILOT_RAW.csv.gz")
    rows = []

    def add(name, value, passed):
        rows.append(dict(check=name, value=value, passed=bool(passed)))

    n_exp = 9 * P.N_NULL * 4 + 2 * 3 * P.N_POWER * 4
    add("rows", len(raw), len(raw) == n_exp)
    add("git_commit", raw["git_commit"].iloc[0], raw["git_commit"].nunique() == 1)
    add("git_dirty", int(raw["git_dirty"].iloc[0]), (raw["git_dirty"] == 0).all())
    st = P.provenance()
    for pl in P.PLANS:
        col = f"sha256_{pl.stem}"
        add(col, raw[col].iloc[0][:16], (raw[col] == st[col]).all())
    valid = raw["verdict"] != "errore"
    m, b = valid & (raw["cand"] == "M"), valid & (raw["cand"] == "B")
    add("M_stat_finite_in_rows_with_outcome", int(np.isfinite(raw.loc[m, "stat"]).sum()), np.isfinite(raw.loc[m, "stat"]).all())
    for col in ("var_a", "var_b", "phi", "kappa", "sigma_x2"):
        add(f"M_{col}_finite", int(np.isfinite(raw.loc[m, col]).sum()), np.isfinite(raw.loc[m, col]).all())
    add("B_stat_finite_in_rows_with_outcome", int(np.isfinite(raw.loc[b, "stat"]).sum()), np.isfinite(raw.loc[b, "stat"]).all())
    pb = raw.loc[b, ["p_low", "p_high"]]
    add("B_pvalues_in_(0,1]", int(((pb > 0) & (pb <= 1)).all(axis=1).sum()), ((pb > 0) & (pb <= 1)).all().all())
    vm = np.where(raw.loc[m, "stat"] < -P.Z, "supportato", np.where(raw.loc[m, "stat"] > P.Z, "opposto", "non deciso"))
    add("M_verdict_recomputed_from_stat", int((vm == raw.loc[m, "verdict"]).sum()), (vm == raw.loc[m, "verdict"]).all())
    vb = np.where(raw.loc[b, "p_low"] <= P.ALPHA, "supportato", np.where(raw.loc[b, "p_high"] <= P.ALPHA, "opposto", "non deciso"))
    add("B_verdict_recomputed_from_pvalues", int((vb == raw.loc[b, "verdict"]).sum()), (vb == raw.loc[b, "verdict"]).all())
    err_rows = raw[valid & ~np.isfinite(raw["stat"])]
    add("rows_with_outcome_but_nonfinite_stat", len(err_rows), True)
    err_rows.to_csv(P.OUT / "POST_CHECKS_NONFINITE_ROWS.csv", index=False)
    # regola errore applicata alle righe non finite (A1 §4/§5), poi riconteggio e confronto con le tabelle del pilota
    raw2 = raw.copy()
    raw2.loc[valid & ~np.isfinite(raw2["stat"]), "verdict"] = "errore"
    fv, pw, ch = recount(raw2)
    fv0 = pd.read_csv(P.OUT / "PILOT_FALSE_VERDICTS.csv")
    pw0 = pd.read_csv(P.OUT / "PILOT_POWER.csv")
    ch0 = pd.read_csv(P.OUT / "PILOT_CHOICE.csv")
    key = ["test", "cand", "scenario"]
    j = fv.merge(fv0, on=key, suffixes=("", "_pilot"))
    add("false_verdicts_recount_equal", int((j["false"] == j["false_pilot"]).sum()),
        len(j) == 36 and (j["false"] == j["false_pilot"]).all() and (j["errors"] == j["errors_pilot"]).all()
        and (j["scenario_ok"] == j["scenario_ok_pilot"]).all())
    jp = pw.merge(pw0, on=key + ["effect"], suffixes=("", "_pilot"))
    add("power_recount_equal", int(np.isclose(jp["power"], jp["power_pilot"]).sum()),
        len(jp) == 24 and np.isclose(jp["power"], jp["power_pilot"]).all())
    jc = ch.merge(ch0, on="test", suffixes=("", "_pilot"))
    add("choice_recount_equal", "|".join(jc["choice"]), (jc["choice"] == jc["choice_pilot"]).all()
        and (jc["kept_M"] == jc["kept_M_pilot"]).all() and (jc["kept_B"] == jc["kept_B_pilot"]).all())
    out = pd.DataFrame(rows).assign(**st)
    out.to_csv(P.OUT / "POST_CHECKS.csv", index=False)
    fv.assign(**st).to_csv(P.OUT / "POST_CHECKS_FALSE_VERDICTS_RECOUNT.csv", index=False)
    pw.assign(**st).to_csv(P.OUT / "POST_CHECKS_POWER_RECOUNT.csv", index=False)
    ch.assign(**st).to_csv(P.OUT / "POST_CHECKS_CHOICE_RECOUNT.csv", index=False)
    print(out[["check", "value", "passed"]].to_string(index=False))
    return 0 if out["passed"].all() else 2


if __name__ == "__main__":
    sys.exit(design_checks() if sys.argv[1:] == ["design"] else raw_checks() if sys.argv[1:] == ["raw"] else 2)
