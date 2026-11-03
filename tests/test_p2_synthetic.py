"""Verifica di run_p2 su cataloghi sintetici con quenching noto (nessun dato vero di P1).

L'attivita' e' quella reale di SILSO; tilt, latitudini, flussi e dipolo sono sintetici.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from sharpbl import run_p2  # noqa: E402

GAMMA0 = 30.0   # gradi: gamma = gamma0 sin|lat|
ETA0 = 2.0e-24  # G/Mx


def synthetic_catalog(beta_t_frac, beta_eta_frac, n=6000, seed=1):
    return run_p2.synthetic_catalog(beta_t_frac, beta_eta_frac, n=n, seed=seed)


@pytest.fixture(scope="module")
def with_quenching():
    return run_p2.run(synthetic_catalog(-0.3, -0.3), do_t0=False)


@pytest.fixture(scope="module")
def without_quenching():
    return run_p2.run(synthetic_catalog(0.0, 0.0, seed=2), do_t0=False)


def main_row(tabs, test, quantity="D*"):
    t = tabs[test]
    m = t[(t["variant"] == "S") & (t["activity"] == "A_monthly")]
    if test == "T5":
        m = m[m["quantity"] == quantity]
    return m.iloc[0]


def test_joy_recovered(with_quenching):
    g = with_quenching["T1"]
    r = g[(g["variant"] == "S") & (g["group"] == "all")].iloc[0]
    assert r["ci95_lo"] > 0 and r["estimate"] == pytest.approx(GAMMA0, abs=4)


def test_t3_detects_injected_tilt_quenching(with_quenching):
    r = main_row(with_quenching, "T3")
    assert r["verdict"] == "quenching supportato"
    assert r["ci95_lo"] <= -0.3 * GAMMA0 <= r["ci95_hi"]


def test_t5_detects_injected_efficiency_quenching(with_quenching):
    r = main_row(with_quenching, "T5")
    assert r["verdict"] == "quenching supportato"
    assert r["ci95_lo"] <= -0.3 * ETA0 <= r["ci95_hi"]


def test_no_false_detection(without_quenching):
    for test in ("T3", "T5"):
        r = main_row(without_quenching, test)
        assert r["verdict"] == "non deciso"


def test_summary_and_robustness(with_quenching):
    s = with_quenching["SUMMARY"].set_index("test")
    assert s.loc["T3", "verdict"] == "quenching supportato"
    assert s.loc["T3", "robust"] == 1


def test_t0_power(monkeypatch):
    monkeypatch.setattr(run_p2, "NREAL_T0", 20)
    cat = synthetic_catalog(0.0, 0.0, n=3000, seed=3)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    t0 = run_p2.t0(d).set_index("beta_over_gamma0")
    assert t0.loc[-0.3, "detection_fraction"] >= t0.loc[-0.1, "detection_fraction"]
    assert abs(t0.loc[-0.3, "bias"]) < 0.1 * GAMMA0


def test_p2b_moving_blocks_and_acf(with_quenching):
    mb = with_quenching["P2B_MOVING_BLOCKS"]
    assert sorted(mb["block_length"].unique()) == [3, 6, 13]
    s = with_quenching["SUMMARY"].set_index("test")
    assert s.loc["T3", "verdict_p2b"] == "quenching supportato"
    acf = with_quenching["P2B_RESIDUAL_ACF"]
    assert set(acf["test"]) == {"T3", "T5"} and acf["lag"].max() == 13


def test_ar1_residuals_show_in_acf():
    cat = run_p2.synthetic_catalog(0.0, 0.0, seed=7, rho=0.8)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    acf = run_p2.p2b_residual_acf(d)
    lag1 = acf[(acf["test"] == "T3") & (acf["lag"] == 1)].iloc[0]
    assert lag1["acf"] > lag1["band"]


def _good_catalog():
    from sharpbl.provenance import PROTOCOLS, ROOT, sha256
    cat = pd.DataFrame({"complete_series": [1, 1], "validation_passed": [1, 1]})
    for n in ("P1", "P1b", "P1c", "P1d", "P1e"):
        cat[f"sha256_{n}"] = sha256(ROOT / PROTOCOLS[n])
    return cat


GOOD_CHECKS = pd.DataFrame({"check": ["1_legacy_reproduces_test_case", "2_synthetic_tests_pass", "3_x"],
                            "value": [1, 1, 0.07], "mandatory": [1, 1, 0]})


def test_gate_accepts_good_catalog():
    assert run_p2.gate_problems(_good_catalog(), GOOD_CHECKS) == []


@pytest.mark.parametrize("case", ["flag_absent", "flag_inconsistent", "flag_zero", "hash_wrong",
                                  "hash_absent", "check_failed", "check_not_run", "checks_file_absent",
                                  "no_mandatory_column"])
def test_gate_rejects(case):
    cat, chk = _good_catalog(), GOOD_CHECKS.copy()
    if case == "flag_absent":
        cat = cat.drop(columns="validation_passed")
    elif case == "flag_inconsistent":
        cat["complete_series"] = [1, 0]
    elif case == "flag_zero":
        cat["validation_passed"] = 0
    elif case == "hash_wrong":
        cat["sha256_P1c"] = "0" * 64
    elif case == "hash_absent":
        cat = cat.drop(columns="sha256_P1d")
    elif case == "check_failed":
        chk.loc[1, "value"] = 0
    elif case == "check_not_run":
        chk = chk[chk["check"] != "1_legacy_reproduces_test_case"]
    elif case == "no_mandatory_column":
        chk = chk.drop(columns="mandatory")
    if case == "checks_file_absent":
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            real_root = run_p2.ROOT
            run_p2.ROOT = Path(tmp)  # nessun results/P1/P1_CHECKS.csv qui
            try:
                probs = run_p2.gate_problems(cat, None)
            finally:
                run_p2.ROOT = real_root
        assert "P1_CHECKS.csv assente" in probs
    else:
        probs = run_p2.gate_problems(cat, chk)
    assert probs, case


def test_mandatory_checks_fail_when_not_executed(monkeypatch, tmp_path):
    """Caso di prova assente o pytest assente: i controlli obbligatori valgono 0, non -1 o 'saltato'."""
    from sharpbl import run_p1
    monkeypatch.setattr(run_p1, "ROOT", tmp_path)  # nessun data/sharp/test_20240508 qui
    (tmp_path / "results/P1").mkdir(parents=True)
    pd.DataFrame({"HARPNUM": [1]}).to_csv(tmp_path / "results/P1/P1_NO_CM_RECORD.csv", index=False)
    pd.DataFrame({"state": ["DATE_IN_WINDOW"], "state_p1": ["DATE_IN_WINDOW"]}).to_csv(
        tmp_path / "results/P1/CYCLE_BOUNDARY_FITS.csv", index=False)
    monkeypatch.setattr(run_p1, "OUT", tmp_path / "results/P1")
    import builtins
    real_import = builtins.__import__

    def no_pytest(name, *a, **k):
        if name == "pytest":
            raise ImportError
        return real_import(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", no_pytest)
    cat = run_p2.synthetic_catalog(0, 0, n=200).assign(
        family_rank=0, family_id=0, first_seen_on_disk=1, tilt_reduced_deg=0.0, hale_sign=1, quality_string="OK",
        key_CRLN_OBS=0.0, key_USFLUX=1e21, lon_pos=0.0, lat_pos=0.0, lon_neg=0.0, lat_neg=0.0,
        key_LAT_FWTPOS=0.0, key_LON_FWTPOS=0.0, key_LAT_FWTNEG=0.0, key_LON_FWTNEG=0.0)
    chk = run_p1.checks(cat, None).set_index("check")
    assert chk.loc["1_legacy_reproduces_test_case", "value"] == 0
    assert chk.loc["2_synthetic_tests_pass", "value"] == 0
    assert "NON eseguiti" in chk.loc["2_synthetic_tests_pass", "note"]


def test_moving_blocks_are_consecutive_calendar_crs_with_gaps():
    """Blocchi di L numeri di CR consecutivi: le CR assenti occupano posto ma non contano."""
    u = np.array([2100, 2101, 2102, 2110, 2111, 2130])
    for L in (3, 6, 13):
        c = run_p2.boot_counts(u, ("moving", L), seed=5, nboot=4000)
        assert c.shape == (4000, len(u))
        # numero di blocchi = ceil(span / L) con span = 2130 - 2100 + 1 = 31
        nb = int(np.ceil(31 / L))
        # ogni CR presente compare al massimo nb volte; la somma per riga <= nb * L
        assert (c.sum(axis=1) <= nb * L).all()
        # due CR nello stesso ricampionamento con distanza >= L non possono venire dallo stesso blocco:
        # verifica diretta ricostruendo i blocchi dalla stessa estrazione
        rng = np.random.default_rng(5)
        starts = rng.integers(2100, 2130 - L + 1 + 1, size=(4000, nb))
        expect = ((starts[:, :, None] <= u) & (starts[:, :, None] + L - 1 >= u)).sum(axis=1)
        assert np.array_equal(c, expect)
    # con L = 3, 2102 e 2110 (8 CR di distanza) non sono mai nello stesso blocco
    rng = np.random.default_rng(5)
    starts = rng.integers(2100, 2128 + 1, size=(4000, 11))
    same = ((starts <= 2102) & (starts + 2 >= 2102) & (starts <= 2110) & (starts + 2 >= 2110)).any()
    assert not same


def test_hemispheres_of_a_cr_resampled_together():
    """Le righe N e S della stessa CR ricevono sempre lo stesso peso nel ricampionamento."""
    cr = np.array([2100, 2100, 2101, 2101, 2105, 2105])
    X = np.ones((6, 1))
    for scheme in (("cr",), ("moving", 3)):
        run_p2.SCHEME = scheme
        try:
            m = run_p2.BlockWLS(X, np.ones(6), cr, nboot=500)
        finally:
            run_p2.SCHEME = ("cr",)
        row_counts = m.counts[:, m.g]  # peso di ogni riga = conteggio della sua CR
        assert np.array_equal(row_counts[:, 0], row_counts[:, 1])
        assert np.array_equal(row_counts[:, 4], row_counts[:, 5])


def test_fallback_removes_verdicts(with_quenching):
    tabs = {k: v.copy() for k, v in with_quenching.items()}
    cat = run_p2.synthetic_catalog(-0.3, -0.3)
    smp = {k: run_p2.add_activity(v, run_p2.load_silso()) for k, v in run_p2.samples(cat).items()}
    out = run_p2.apply_fallback(tabs, smp, {"T3": False, "T5": False}).get("SUMMARY").set_index("test")
    assert out.loc["T3", "verdict_final"] == "descrittivo (ripiego P2d §6)"
    assert out.loc["T5", "verdict_final"] == "descrittivo (ripiego P2d §6)"
    assert set(tabs["P2D_TESTS"]["test"]) == {"T3", "T5"}
