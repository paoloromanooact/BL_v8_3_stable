"""Controlli del pilota P2f (docs/P2F_PILOT_IMPLEMENTATION_NOTE.md): nessun risultato nuovo, nessun verdetto.

    .venv/bin/python python/sharpbl/p2f_checks.py design   # conteggi del disegno congelato -> DESIGN_CHECKS.csv (prima degli esiti)
    .venv/bin/python python/sharpbl/p2f_checks.py raw      # finitezza e riconteggio indipendente di PILOT_RAW.csv.gz -> POST_CHECKS.csv
    .venv/bin/python python/sharpbl/p2f_checks.py diag     # diagnostica descrittiva (parametri di M, errori, cluster di B), non entra nella scelta
    .venv/bin/python python/sharpbl/p2f_checks.py vraw     # validazione P2f: controllo indipendente di results/P2F/VALIDATION_RAW.csv.gz -> POST_CHECKS.csv

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

import hashlib

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
    # `kind` vale "null" per i cataloghi nulli: non va letto come mancante (pandas lo farebbe per default)
    raw = pd.read_csv(P.OUT / "PILOT_RAW.csv.gz", low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
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


def diagnostics():
    """Diagnostica descrittiva delle candidate (non entra nella scelta): parametri stimati di M, errori, cluster di B."""
    raw = pd.read_csv(P.OUT / "PILOT_RAW.csv.gz", low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
    st = P.provenance()
    m = raw[raw["cand"] == "M"]
    rows = []
    for (test, kind, s, e), g in m.groupby(["test", "kind", "scenario", "effect"]):
        ok = g[g["verdict"] != "errore"]
        r = dict(test=test, kind=kind, scenario=s, effect=e, n=len(g), errors=int((g["verdict"] == "errore").sum()))
        for col in ("phi", "kappa", "sigma_x2", "var_a", "var_b", "n_valid_starts", "n_zero_residuals", "n_varfun"):
            q = ok[col].quantile([0.1, 0.5, 0.9])
            r.update({f"{col}_q10": q.iloc[0], f"{col}_median": q.iloc[1], f"{col}_q90": q.iloc[2], f"{col}_mean": ok[col].mean()})
        r["frac_sigma_x_at_lower"] = ok["sigma_x_at_lower"].mean()
        rows.append(r)
    pd.DataFrame(rows).assign(**st).to_csv(P.OUT / "PILOT_DIAGNOSTICS_M.csv", index=False)
    err = raw[raw["verdict"] == "errore"].groupby(["test", "cand", "kind", "scenario", "effect", "error"]).size().reset_index(name="n")
    err.assign(**st).to_csv(P.OUT / "PILOT_ERRORS.csv", index=False)
    b = raw[raw["cand"] == "B"].groupby("test")["n_clusters"].agg(["min", "max"]).reset_index()
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(pd.DataFrame(rows)[["test", "kind", "scenario", "effect", "n", "errors", "phi_median", "kappa_median", "sigma_x2_median",
                                  "frac_sigma_x_at_lower", "var_b_mean", "n_valid_starts_mean", "n_zero_residuals_mean"]].round(4).to_string(index=False))
        print(err.to_string(index=False))
        print(b.to_string(index=False))
    return 0


# ---------------------------------------------------------------- validazione P2f (protocollo §5, §6.3): controllo indipendente

V_OUT = P.ROOT / "results/P2F"
V_COMMIT = "5c3b664"        # commit della provenienza della validazione (HANDOFF 2026-11-11); non il nuovo HEAD
V_PROTO_SHA = "8f030010"    # SHA-256 (inizio) del protocollo congelato in 500c56a
THR = dict(false=0.03, side=0.0175, err=0.01, cov=0.965, below=0.02)


def v_recount(raw):
    """Riconteggio con le regole del protocollo §5, scritto a parte (non usa p2f_validation.summarize)."""
    fv = []
    for (test, s), g in raw[raw["kind"] == "null"].groupby(["test", "scenario"]):
        n = len(g)
        sup, opp, err = [int((g["verdict"] == v).sum()) for v in ("supportato", "opposto", "errore")]
        fv.append(dict(test=test, scenario=s, n=n, false=sup + opp, supported=sup, opposite=opp, errors=err,
                       scenario_ok=bool((sup + opp) <= THR["false"] * n and sup <= THR["side"] * n and opp <= THR["side"] * n
                                        and err <= THR["err"] * n)))
    fv = pd.DataFrame(fv)
    cp = []
    for (test, s, e), g in raw[raw["kind"] == "effect"].groupby(["test", "scenario", "effect"]):
        n = len(g)
        cov, below, above, err = int(g["covered"].sum()), int(g["below"].sum()), int(g["above"].sum()), int((g["verdict"] == "errore").sum())
        cp.append(dict(test=test, scenario=s, effect=e, n=n, covered=cov, below=below, above=above, errors=err,
                       power=float((g["verdict"] == "supportato").mean()),
                       combo_ok=bool(cov >= THR["cov"] * n and below <= THR["below"] * n)))
    cp = pd.DataFrame(cp)
    dec = []
    for test in ("T3", "T5"):
        f, c = fv[fv["test"] == test], cp[cp["test"] == test]
        dec.append(dict(test=test, n_null=len(f), null_ok=bool(len(f) == 12 and f["scenario_ok"].all()), n_combo=len(c),
                        effect_ok=bool(len(c) == 16 and c["combo_ok"].all()),
                        validated=bool(len(f) == 12 and f["scenario_ok"].all() and len(c) == 16 and c["combo_ok"].all())))
    return fv, cp, pd.DataFrame(dec)


def validation_checks():
    from scipy.stats import norm
    from sharpbl import p2f_validation as V
    raw = pd.read_csv(V_OUT / "VALIDATION_RAW.csv.gz", low_memory=False, keep_default_na=False, na_values=["", "nan", "NaN"])
    rows = []

    def add(name, value, passed):
        rows.append(dict(check=name, value=value, passed=bool(passed)))

    n_exp = 12 * V.N_NULL * 2 + 16 * V.N_EFF * 2
    add("rows", len(raw), len(raw) == n_exp)
    key = ["kind", "scenario", "effect", "k", "test"]
    add("keys_unique", int(raw.duplicated(key).sum()), not raw.duplicated(key).any())
    gn = raw[raw["kind"] == "null"].groupby(["test", "scenario"]).size()
    ge = raw[raw["kind"] == "effect"].groupby(["test", "scenario", "effect"]).size()
    add("null_groups_24_of_10000", f"{len(gn)} gruppi, min {gn.min()}, max {gn.max()}", len(gn) == 24 and (gn == V.N_NULL).all())
    add("effect_groups_32_of_2000", f"{len(ge)} gruppi, min {ge.min()}, max {ge.max()}", len(ge) == 32 and (ge == V.N_EFF).all())
    expected = {("null", s, 0.0, k, t) for s in V.SCENARIOS for k in range(V.N_NULL) for t in ("T3", "T5")}
    expected |= {("effect", s, e, k, t) for s in V.EFFECT_SCENARIOS for e in V.EFFECTS for k in range(V.N_EFF) for t in ("T3", "T5")}
    got = set(zip(raw["kind"], raw["scenario"].astype(int), raw["effect"].astype(float), raw["k"].astype(int), raw["test"]))
    add("keys_equal_expected_set", f"mancanti {len(expected - got)}, inattese {len(got - expected)}", got == expected)
    add("git_commit_is_5c3b664", raw["git_commit"].iloc[0][:7], raw["git_commit"].nunique() == 1 and raw["git_commit"].iloc[0].startswith(V_COMMIT))
    add("git_dirty_0", int(raw["git_dirty"].iloc[0]), (raw["git_dirty"] == 0).all())
    sha_now = hashlib.sha256(V.PROTOCOL.read_bytes()).hexdigest()
    add("sha256_protocol_8f030010_and_unchanged", raw["sha256_PROTOCOL_P2F"].iloc[0][:8],
        (raw["sha256_PROTOCOL_P2F"] == sha_now).all() and sha_now.startswith(V_PROTO_SHA))
    valid = raw["verdict"] != "errore"
    err = raw["verdict"] == "errore"
    add("error_rows", int(err.sum()), True)
    ident = raw["covered"] + raw["below"] + raw["above"] + err.astype(int)
    add("identity_cov+below+above+err=1_per_row", int((ident == 1).sum()), (ident == 1).all())
    fin_cols = ["beta", "se", "stat", "lo", "hi", "var_a", "var_b", "phi", "kappa", "sigma_x2"]
    fin = np.isfinite(raw.loc[valid, fin_cols]).all(axis=1)
    add("finite_in_rows_with_outcome", int(fin.sum()), fin.all())
    add("se_positive_lo_lt_hi", int(((raw.loc[valid, "se"] > 0) & (raw.loc[valid, "lo"] < raw.loc[valid, "hi"])).sum()),
        ((raw.loc[valid, "se"] > 0) & (raw.loc[valid, "lo"] < raw.loc[valid, "hi"])).all())
    Zf = float(norm.ppf(1 - 0.0125))
    v = raw[valid]
    dlo = np.abs((v["beta"] - v["lo"]) / v["se"] - Zf)
    dhi = np.abs((v["hi"] - v["beta"]) / v["se"] - Zf)
    add("lower_half_width_(beta-lo)/se=z", float(dlo.max()), (dlo <= 1e-9).all())
    add("upper_half_width_(hi-beta)/se=z", float(dhi.max()), (dhi <= 1e-9).all())
    ds = np.abs(v["stat"] - v["beta"] / v["se"])
    add("stat_equals_beta_over_se", float(ds.max()), (ds <= 1e-9 * np.maximum(1, np.abs(v["stat"]))).all())
    vr = np.where(v["hi"] < 0, "supportato", np.where(v["lo"] > 0, "opposto", "non deciso"))
    add("verdict_recomputed_from_interval", int((vr == v["verdict"]).sum()), (vr == v["verdict"]).all())
    cr = ((v["lo"] <= v["beta_true"]) & (v["beta_true"] <= v["hi"])).astype(int)
    br = (v["lo"] > v["beta_true"]).astype(int)
    ar = (v["hi"] < v["beta_true"]).astype(int)
    add("tails_recomputed_from_interval", int(((cr == v["covered"]) & (br == v["below"]) & (ar == v["above"])).sum()),
        ((cr == v["covered"]) & (br == v["below"]) & (ar == v["above"])).all())
    bt = raw["effect"] * np.where(raw["test"] == "T3", V.GAMMA0, V.ETA_BAR)
    add("beta_true_consistent", float(np.max(np.abs(raw["beta_true"] - bt) / np.maximum(np.abs(bt), 1e-300))),
        (np.abs(raw["beta_true"] - bt) <= 1e-12 * np.maximum(np.abs(bt), 1e-300)).all() and (raw.loc[raw["kind"] == "null", "beta_true"] == 0).all())
    add("errors_have_zero_tails", int(((raw.loc[err, ["covered", "below", "above"]] == 0).all(axis=1)).sum()),
        (raw.loc[err, ["covered", "below", "above"]] == 0).all().all())
    nonfin = raw[valid & ~fin.reindex(raw.index, fill_value=True)]
    nonfin.to_csv(V_OUT / "POST_CHECKS_NONFINITE_ROWS.csv", index=False)
    add("rows_with_outcome_but_nonfinite", len(nonfin), True)
    fv, cp, dec = v_recount(raw)
    fv0 = pd.read_csv(V_OUT / "VALIDATION_FALSE_VERDICTS.csv")
    cp0 = pd.read_csv(V_OUT / "VALIDATION_COVERAGE_POWER.csv")
    dc0 = pd.read_csv(V_OUT / "VALIDATION_DECISION.csv")
    j = fv.merge(fv0, on=["test", "scenario"], suffixes=("", "_v"))
    add("false_verdicts_recount_equal", len(j), len(j) == 24 and (j["false"] == j["false_v"]).all() and (j["supported"] == j["supported_v"]).all()
        and (j["opposite"] == j["opposite_v"]).all() and (j["errors"] == j["errors_v"]).all() and (j["scenario_ok"] == j["scenario_ok_v"]).all())
    jc = cp.merge(cp0, on=["test", "scenario", "effect"], suffixes=("", "_v"))
    add("coverage_recount_equal", len(jc), len(jc) == 32 and (jc["covered"] == jc["covered_v"]).all() and (jc["below"] == jc["below_v"]).all()
        and (jc["above"] == jc["above_v"]).all() and (jc["errors"] == jc["errors_v"]).all() and np.isclose(jc["power"], jc["power_v"]).all()
        and (jc["combo_ok"] == jc["combo_ok_v"]).all())
    jd = dec.merge(dc0, on="test", suffixes=("", "_v"))
    add("decision_recount_equal", "|".join(f"{t}:{v}" for t, v in zip(jd["test"], jd["validated"])),
        len(jd) == 2 and (jd["validated"] == jd["validated_v"]).all() and (jd["null_ok"] == jd["null_ok_v"]).all() and (jd["effect_ok"] == jd["effect_ok_v"]).all())
    st = P.provenance()
    for f in ("VALIDATION_RAW.csv.gz", "VALIDATION_FALSE_VERDICTS.csv", "VALIDATION_COVERAGE_POWER.csv", "VALIDATION_DECISION.csv"):
        st[f"sha256_{f.split('.')[0]}"] = hashlib.sha256((V_OUT / f).read_bytes()).hexdigest()
    st["sha256_PROTOCOL_P2F_checked"] = sha_now
    out = pd.DataFrame(rows).assign(**st)
    out.to_csv(V_OUT / "POST_CHECKS.csv", index=False)
    fv.assign(**st).to_csv(V_OUT / "POST_CHECKS_FALSE_VERDICTS_RECOUNT.csv", index=False)
    cp.assign(**st).to_csv(V_OUT / "POST_CHECKS_COVERAGE_RECOUNT.csv", index=False)
    dec.assign(**st).to_csv(V_OUT / "POST_CHECKS_DECISION_RECOUNT.csv", index=False)
    with pd.option_context("display.width", 200):
        print(out[["check", "value", "passed"]].to_string(index=False))
    return 0 if out["passed"].all() else 2


if __name__ == "__main__":
    cmd = sys.argv[1:]
    sys.exit(design_checks() if cmd == ["design"] else raw_checks() if cmd == ["raw"] else diagnostics() if cmd == ["diag"]
             else validation_checks() if cmd == ["vraw"] else 2)
