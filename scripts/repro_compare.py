"""Comparatore di riproducibilità, fase 1 (docs/REPRO_PHASE1_PLAN.md, congelato in 0f51e61).

Confronta un CSV rigenerato con il riferimento distribuito secondo docs/REPRO_COMPARISON_RULES.md §2–4 e le
righe delle tabelle REPRO_COMPARISON_KEYS_DRAFT.csv / REPRO_COMPARISON_SCALES_DRAFT.csv lette dal commit di
congelamento. Non rilancia nulla.

    .venv/bin/python scripts/repro_compare.py --selftest           # prove sintetiche (prima di ogni rilancio)
    .venv/bin/python scripts/repro_compare.py --phase1 <dir_rilancio> --out <dir_rapporto>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FREEZE = "0f51e61"
NA = ["", "nan", "NaN"]


def git_show(commit, path):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout


def read_csv_bytes(b):
    return pd.read_csv(io.BytesIO(b), dtype=str, keep_default_na=False, na_values=NA)


def policy_for(file, scales_df):
    p = scales_df[scales_df["file"] == file]
    return {r["column"]: r for _, r in p.iterrows()}


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def compare(ref, new, key, policy):
    """Restituisce (righe di esito per colonna, dict di sintesi). ref e new: DataFrame letti come testo."""
    summ = dict(schema_equal=list(ref.columns) == list(new.columns), rows_ref=len(ref), rows_new=len(new),
                key=";".join(key), problems=[])
    if not summ["schema_equal"]:
        summ["problems"].append(f"schema diverso: rif {list(ref.columns)} / nuovo {list(new.columns)}")
    missing_policy = [c for c in ref.columns if c not in policy]
    if missing_policy:
        summ["problems"].append(f"colonne senza regola: {missing_policy}")
    for name, d in (("riferimento", ref), ("rilancio", new)):
        if not all(k in d.columns for k in key):
            summ["problems"].append(f"chiave assente nel {name}")
            return [], summ
        if d[key].isna().any().any():
            summ["problems"].append(f"chiave mancante nel {name}")
        if d.duplicated(key).any():
            summ["problems"].append(f"chiave duplicata nel {name}: {int(d.duplicated(key).sum())}")
    if summ["problems"] and any(p.startswith(("chiave", "schema")) for p in summ["problems"]):
        return [], summ
    kr = set(map(tuple, ref[key].to_numpy())); kn = set(map(tuple, new[key].to_numpy()))
    if kr != kn:
        summ["problems"].append(f"insieme delle chiavi diverso: mancanti {len(kr - kn)}, inattese {len(kn - kr)}")
        return [], summ
    r = ref.set_index(key).sort_index(); n = new.set_index(key).sort_index().loc[r.index]
    rows = []
    for col in r.columns:
        pol = policy.get(col)
        mode = pol["mode"] if pol is not None else "exact"
        a_txt, b_txt = n[col], r[col]
        a_na, b_na = a_txt.isna(), b_txt.isna()
        na_mismatch = int((a_na != b_na).sum())
        if mode == "scaled":
            S = float(pol["scale_S"]); atol = float(pol["normalized_atol"]); rtol = float(pol["rtol"])
            a, b = _num(a_txt).to_numpy(float), _num(b_txt).to_numpy(float)
            both = ~a_na.to_numpy() & ~b_na.to_numpy()
            nonnum = int(both.sum() - (np.isfinite(a) | np.isinf(a))[both].sum()) + int(both.sum() - (np.isfinite(b) | np.isinf(b))[both].sum())
            inf_bad = int((both & (np.isinf(a) | np.isinf(b)) & ~(a == b)).sum())
            fin = both & np.isfinite(a) & np.isfinite(b)
            diff = np.abs(a[fin] - b[fin])
            tol = atol * S + rtol * np.maximum(np.abs(a[fin]), np.abs(b[fin]))
            out = int((diff > tol).sum())
            identical = int((a[fin] == b[fin]).sum())
            rows.append(dict(column=col, mode=mode, S=S, n=len(r), na_mismatch=na_mismatch, nonnumeric=nonnum,
                             inf_mismatch=inf_bad, n_finite=int(fin.sum()), n_identical=identical, n_out_of_tol=out,
                             max_abs_diff=float(diff.max()) if diff.size else 0.0,
                             max_norm_diff=float((diff / S).max()) if diff.size else 0.0,
                             ok=bool(na_mismatch == 0 and nonnum == 0 and inf_bad == 0 and out == 0)))
        else:  # exact, provenance: valori letti uguali (numeri come numeri, testo come testo)
            an, bn = _num(a_txt), _num(b_txt)
            numeric = an.notna() & bn.notna()
            eq_num = (an == bn) | (np.isnan(an) & np.isnan(bn))
            eq = (a_na & b_na) | (~a_na & ~b_na & ((numeric & eq_num) | (~numeric & (a_txt == b_txt))))
            mism = int((~eq).sum())
            rows.append(dict(column=col, mode=mode, n=len(r), na_mismatch=na_mismatch, n_mismatch=mism, ok=bool(mism == 0)))
    return rows, summ


def verdict(rows, summ):
    return bool(not summ["problems"] and rows and all(r["ok"] for r in rows))


# ---------------------------------------------------------------- prove sintetiche (piano: prima del rilancio)

def selftest():
    pol = {
        "id": {"mode": "exact_key"}, "n": {"mode": "exact"}, "x": {"mode": "scaled", "scale_S": 1.0, "normalized_atol": 1e-12, "rtol": 1e-9},
        "eta": {"mode": "scaled", "scale_S": 3.56e-25, "normalized_atol": 1e-12, "rtol": 1e-9},
        "git_commit": {"mode": "provenance"}, "status": {"mode": "exact"},
    }
    base = pd.DataFrame(dict(id=["1", "2", "3"], n=["5", "6", "7"], x=["1.0", "nan", "inf"], eta=["1e-25", "2e-25", "3e-25"],
                             git_commit=["abc"] * 3, status=["ok"] * 3))
    to_txt = lambda d: read_csv_bytes(d.to_csv(index=False).encode())  # noqa: E731
    cases = []

    def case(name, new, expect_ok, key=("id",)):
        rows, s = compare(to_txt(base), to_txt(new), list(key), pol)
        got = verdict(rows, s)
        cases.append(dict(case=name, expected_ok=expect_ok, got_ok=got, passed=got == expect_ok, problems="; ".join(s["problems"])))

    case("identico", base.copy(), True)
    case("righe permutate", base.iloc[[2, 0, 1]], True)
    case("x entro tolleranza (1e-10 relativo)", base.assign(x=["1.0000000001", "nan", "inf"]), True)
    case("x fuori tolleranza", base.assign(x=["1.00001", "nan", "inf"]), False)
    case("NaN contro numero", base.assign(x=["1.0", "2.0", "inf"]), False)
    case("inf di segno opposto", base.assign(x=["1.0", "nan", "-inf"]), False)
    case("T5 minuscolo 1e-25 contro 9e-25", base.assign(eta=["9e-25", "2e-25", "3e-25"]), False)
    case("T5 minuscolo entro tolleranza", base.assign(eta=["1.00000000001e-25", "2e-25", "3e-25"]), True)
    case("conteggio alterato", base.assign(n=["5", "6", "8"]), False)
    case("provenienza alterata", base.assign(git_commit=["abc", "abc", "abd"]), False)
    case("metadato scientifico alterato (status)", base.assign(status=["ok", "ok", "ko"]), False)
    case("chiave mancante", base.drop(index=2), False)
    case("chiave duplicata", pd.concat([base, base.iloc[[0]]]), False)
    case("chiave vuota", base.assign(id=["1", "", "3"]), False)
    case("schema diverso (colonna in più)", base.assign(extra=["a", "b", "c"]), False)
    case("schema diverso (ordine)", base[["n", "id", "x", "eta", "git_commit", "status"]], False)
    t = pd.DataFrame(cases)
    print(t.to_string(index=False))
    return t


def sha(b):
    return hashlib.sha256(b).hexdigest()


def phase1(run_dir: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    files = read_csv_bytes(git_show(FREEZE, "docs/REPRO_PHASE1_FILES.csv"))
    keys = read_csv_bytes(git_show(FREEZE, "docs/REPRO_COMPARISON_KEYS_DRAFT.csv"))
    scales = read_csv_bytes(git_show(FREEZE, "docs/REPRO_COMPARISON_SCALES_DRAFT.csv"))
    scales_num = scales.copy()
    rep_rows, col_rows = [], []
    for _, f in files[files["role"] == "reference"].iterrows():
        path = f["file"]
        ref_b = git_show(f["commit"], path)
        new_p = run_dir / path
        row = dict(file=path, reference_commit=f["commit"][:7], reference_sha256=sha(ref_b),
                   reference_sha256_expected=f["sha256"], reference_hash_ok=sha(ref_b) == f["sha256"])
        if not new_p.exists():
            row.update(regenerated="mancante", byte_identical=False, values_ok=False, problems="output mancante")
            rep_rows.append(row); continue
        new_b = new_p.read_bytes()
        key = keys.loc[keys["file"] == path, "key"].iloc[0].split(";")
        rows, s = compare(read_csv_bytes(ref_b), read_csv_bytes(new_b), key, policy_for(path, scales_num))
        for r in rows:
            col_rows.append(dict(file=path, **r))
        row.update(regenerated_sha256=sha(new_b), byte_identical=sha(new_b) == sha(ref_b), rows_ref=s["rows_ref"],
                   rows_new=s["rows_new"], schema_equal=s["schema_equal"], key=s["key"], values_ok=verdict(rows, s),
                   problems="; ".join(s["problems"]))
        rep_rows.append(row)
    rep = pd.DataFrame(rep_rows); cols = pd.DataFrame(col_rows)
    rep.to_csv(out / "PHASE1_FILES_REPORT.csv", index=False)
    cols.to_csv(out / "PHASE1_COLUMNS_REPORT.csv", index=False)
    meta = dict(freeze_commit=FREEZE, comparator_sha256=sha(Path(__file__).read_bytes()),
                plan_sha256=sha(git_show(FREEZE, "docs/REPRO_PHASE1_PLAN.md")),
                rules_sha256=sha(git_show(FREEZE, "docs/REPRO_COMPARISON_RULES.md")),
                keys_sha256=sha(git_show(FREEZE, "docs/REPRO_COMPARISON_KEYS_DRAFT.csv")),
                scales_sha256=sha(git_show(FREEZE, "docs/REPRO_COMPARISON_SCALES_DRAFT.csv")),
                files_sha256=sha(git_show(FREEZE, "docs/REPRO_PHASE1_FILES.csv")),
                passed=bool(len(rep) == 5 and rep["values_ok"].all() and rep["reference_hash_ok"].all()))
    (out / "PHASE1_META.json").write_text(json.dumps(meta, indent=2))
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(rep.drop(columns=["reference_sha256", "reference_sha256_expected", "regenerated_sha256"], errors="ignore").to_string(index=False))
        print(cols.to_string(index=False))
    print(json.dumps(meta, indent=2))
    return 0 if meta["passed"] else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--phase1")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        t = selftest()
        if a.out:
            Path(a.out).mkdir(parents=True, exist_ok=True)
            t.to_csv(Path(a.out) / "COMPARATOR_SELFTEST.csv", index=False)
        return 0 if t["passed"].all() else 2
    if a.phase1 and a.out:
        return phase1(Path(a.phase1), Path(a.out))
    return 2


if __name__ == "__main__":
    sys.exit(main())
