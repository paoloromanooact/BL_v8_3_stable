"""Applicazione ai dati reali della procedura M validata (protocollo P2f §7, docs/PROTOCOL_P2F_VALIDATED_TEST.md).

Una sola esecuzione per test. Rifiuta se manca `results/P2F/VALIDATION_DECISION.csv`, se il test non e'
validato o se i suoi risultati esistono gia'. Le risposte reali sono lette solo con `--real`.
Le sensibilita' (A_smooth13, A_usflux, campioni S1-S6) usano le stesse formule ma sono NON VALIDATE,
anche negli intervalli, e non hanno verdetto.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_apply.py --selftest          # su dati sintetici, output scartati
    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/p2f_apply.py --test T3 --real    # dati reali (solo se T3 validato)
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, p2f_validation as V, run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

DELTAS = (0.1, 0.2, 0.3, 0.35)
SCALE = {"T3": V.GAMMA0, "T5": V.ETA_BAR}
ACT_SENS = ("A_smooth13", "A_usflux")
SAMPLE_SENS = ("S1", "S2", "S3", "S4", "S5", "S6")


class Refused(Exception):
    pass


CHECKED = ("VALIDATION_RAW.csv.gz", "VALIDATION_FALSE_VERDICTS.csv", "VALIDATION_COVERAGE_POWER.csv", "VALIDATION_DECISION.csv")


def check_allowed(out_dir: Path, test: str):
    """Permesso solo se: decisione presente e test validato; controllo indipendente presente, tutto superato e
    riferito agli stessi output (SHA-256 dei quattro file) e allo stesso protocollo; nessun risultato gia' scritto."""
    dec = out_dir / "VALIDATION_DECISION.csv"
    if not dec.exists():
        raise Refused("manca VALIDATION_DECISION.csv: la validazione non e' stata eseguita")
    d = pd.read_csv(dec)
    row = d[d["test"] == test]
    if len(row) != 1 or not bool(row["validated"].iloc[0]):
        raise Refused(f"{test} non validato: il test resta descrittivo")
    pc = out_dir / "POST_CHECKS.csv"
    if not pc.exists():
        raise Refused("manca POST_CHECKS.csv: il controllo indipendente non e' stato eseguito")
    c = pd.read_csv(pc)
    if not c["passed"].all():
        raise Refused("controllo indipendente non superato: " + ", ".join(c.loc[~c["passed"], "check"]))
    for f in CHECKED:
        col = f"sha256_{f.split('.')[0]}"
        if col not in c or not (out_dir / f).exists() or c[col].iloc[0] != hashlib.sha256((out_dir / f).read_bytes()).hexdigest():
            raise Refused(f"il controllo indipendente non si riferisce all'attuale {f}")
    if c["sha256_PROTOCOL_P2F_checked"].iloc[0] != hashlib.sha256(V.PROTOCOL.read_bytes()).hexdigest():
        raise Refused("il controllo indipendente si riferisce a un altro protocollo")
    if (out_dir / f"REAL_{test}.csv").exists():
        raise Refused(f"REAL_{test}.csv esiste gia': una sola esecuzione per test")
    return d


def load_real_samples():
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    sel = pd.read_csv(ROOT / "results/P1/P1_RECORD_SELECTION.csv")
    sel = sel.merge(cat[["HARPNUM", "T_REC", "CR"]], on=["HARPNUM", "T_REC"], how="left")
    silso = run_p2.load_silso()
    return {k: run_p2.add_activity(v, silso, sel) for k, v in run_p2.samples(cat).items()}


def apply_once(d, test, act="A_monthly", expected=True):
    """Procedura M su un campione; `act` e' copiato in A_monthly perche' la procedura usa quella colonna."""
    dd = d.copy()
    if act != "A_monthly":
        dd["A_monthly"] = dd[act]
    dd = dd[np.isfinite(dd["A_monthly"])]
    if len(dd) < 10:
        return dict(verdict="errore", error=f"attivita' {act} non disponibile ({len(dd)} unita' con valore finito)")
    try:
        u = V.units(dd, test)
        if expected and u["n_check"] != V.EXPECTED[test]:
            raise Refused(f"disegno diverso da quello validato: {u['n_check']} contro {V.EXPECTED[test]}")
        r = V.procedure_m(u)
        r.update(n_units=u["n_check"][0], n_second=u["n_check"][1])
        return r
    except V.CandidateError as exc:
        return dict(verdict="errore", error=str(exc))


def excluded_deltas(r, test):
    if r.get("verdict") == "errore":
        return ""
    return ";".join(str(dl) for dl in DELTAS if r["lo"] > -dl * SCALE[test])


def run(test, smp, out_dir: Path, dec_df):
    st = stamp(("P2", "P2d", "P2e"))
    st["sha256_PROTOCOL_P2F"] = hashlib.sha256(V.PROTOCOL.read_bytes()).hexdigest()
    st["validation_git_commit"] = dec_df["git_commit"].iloc[0]
    st["sha256_VALIDATION_DECISION"] = hashlib.sha256((out_dir / "VALIDATION_DECISION.csv").read_bytes()).hexdigest()
    main = apply_once(smp["S"], test)
    main.update(test=test, sample="S", activity="A_monthly", validated=True, scale=SCALE[test],
                excluded_deltas=excluded_deltas(main, test), interval_label="livello nominale 97,5 %; criteri di validazione superati negli scenari provati")
    pd.DataFrame([main]).assign(**st).to_csv(out_dir / f"REAL_{test}.csv", index=False)
    sens = []
    for act in ACT_SENS:
        r = apply_once(smp["S"], test, act=act, expected=False)
        r.update(test=test, sample="S", activity=act)
        sens.append(r)
    for name in SAMPLE_SENS:
        if name not in smp:
            continue
        r = apply_once(smp[name], test, expected=False)
        r.update(test=test, sample=name, activity="A_monthly")
        sens.append(r)
    sd = pd.DataFrame(sens)
    sd["validated"] = False
    sd["verdict"] = np.where(sd["verdict"] == "errore", "errore", "nessun verdetto (sensibilita' non validata)")
    sd["interval_label"] = "intervallo NON validato (sensibilita')"
    sd.assign(**st).to_csv(out_dir / f"REAL_{test}_SENSITIVITY.csv", index=False)
    return main, sd


def selftest():
    """Su dati sintetici (P2d V1, seme 20 000 950), in una cartella temporanea: logica di rifiuto e percorso completo."""
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        cat = p2d.synthetic_catalog_p2d("V1", 20_000_950, 0.0, 0.0)
        smp = {"S": run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())}
        for name in SAMPLE_SENS:
            try:
                smp[name] = run_p2.add_activity(run_p2.samples(cat)[name], run_p2.load_silso())
            except KeyError:
                pass
        # 1: senza decisione -> rifiuto
        try:
            check_allowed(out, "T3"); ok = False; print("FAIL: accettato senza decisione")
        except Refused as e:
            print("ok rifiuto 1:", e)
        # 2: non validato -> rifiuto
        pd.DataFrame([dict(test="T3", validated=False, git_commit="x"), dict(test="T5", validated=True, git_commit="x")]).to_csv(out / "VALIDATION_DECISION.csv", index=False)
        try:
            check_allowed(out, "T3"); ok = False; print("FAIL: accettato T3 non validato")
        except Refused as e:
            print("ok rifiuto 2:", e)
        # 2b: validato ma senza controllo indipendente -> rifiuto; con controllo fallito -> rifiuto; con hash diverso -> rifiuto
        try:
            check_allowed(out, "T5"); ok = False; print("FAIL: accettato senza POST_CHECKS")
        except Refused as e:
            print("ok rifiuto 2b:", e)
        for f in CHECKED:
            (out / f).write_text("x") if not (out / f).exists() else None
        hashes = {f"sha256_{f.split('.')[0]}": hashlib.sha256((out / f).read_bytes()).hexdigest() for f in CHECKED}
        hashes["sha256_PROTOCOL_P2F_checked"] = hashlib.sha256(V.PROTOCOL.read_bytes()).hexdigest()
        pd.DataFrame([dict(check="a", passed=False, **hashes)]).to_csv(out / "POST_CHECKS.csv", index=False)
        try:
            check_allowed(out, "T5"); ok = False; print("FAIL: accettato con controllo fallito")
        except Refused as e:
            print("ok rifiuto 2c:", e)
        bad = dict(hashes); bad["sha256_VALIDATION_RAW"] = "0" * 64
        pd.DataFrame([dict(check="a", passed=True, **bad)]).to_csv(out / "POST_CHECKS.csv", index=False)
        try:
            check_allowed(out, "T5"); ok = False; print("FAIL: accettato con hash diverso")
        except Refused as e:
            print("ok rifiuto 2d:", e)
        pd.DataFrame([dict(check="a", passed=True, **hashes)]).to_csv(out / "POST_CHECKS.csv", index=False)
        # 3: validato e controllato -> esecuzione (disegno sintetico: nessun controllo sul disegno reale)
        dec = check_allowed(out, "T5")
        m = apply_once(smp["S"], "T5", expected=False)
        print("ok esecuzione 3:", {k: m[k] for k in ("verdict", "beta", "lo", "hi") if k in m})
        ok &= m.get("verdict") in ("supportato", "opposto", "non deciso", "errore")
        # percorso completo (scrive nella cartella temporanea) con disegno sintetico
        V.EXPECTED_BACKUP = dict(V.EXPECTED)
        try:
            u = V.units(smp["S"][np.isfinite(smp["S"]["A_monthly"])], "T5")
            V.EXPECTED["T5"] = u["n_check"]
            main, sd = run("T5", smp, out, dec)
            print("ok percorso completo:", main["verdict"], "delta esclusi:", repr(main["excluded_deltas"]), "sensibilita':", len(sd))
            ok &= (out / "REAL_T5.csv").exists() and (sd["validated"] == False).all()  # noqa: E712
        finally:
            V.EXPECTED.update(V.EXPECTED_BACKUP)
        # 4: seconda esecuzione -> rifiuto
        try:
            check_allowed(out, "T5"); ok = False; print("FAIL: accettata seconda esecuzione")
        except Refused as e:
            print("ok rifiuto 4:", e)
    print("SELFTEST", "OK" if ok else "FALLITO", "(output scartati)")
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--test", choices=("T3", "T5"))
    ap.add_argument("--real", action="store_true", help="legge le risposte reali (obbligatorio per l'applicazione)")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.test and a.real):
        print("servono --test T3|T5 e --real (oppure --selftest)")
        return 2
    try:
        dec = check_allowed(V.OUT, a.test)
    except Refused as e:
        print("RIFIUTATO:", e)
        return 3
    smp = load_real_samples()
    main_row, sd = run(a.test, smp, V.OUT, dec)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(pd.DataFrame([main_row])[["test", "verdict", "beta", "se", "lo", "hi", "excluded_deltas", "phi", "kappa", "sigma_x2", "var_b"]].to_string(index=False))
        print(sd[["sample", "activity", "verdict", "beta", "lo", "hi"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
