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
