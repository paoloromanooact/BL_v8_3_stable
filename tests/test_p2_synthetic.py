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
    rng = np.random.default_rng(seed)
    silso = run_p2.load_silso()["monthly"]
    t = pd.to_datetime("2010-06-01") + pd.to_timedelta(rng.uniform(0, 16 * 365.25, n), unit="D")
    cyc = np.where(t < pd.Timestamp("2020-01-01"), 24, 25)
    tmin = np.where(cyc == 24, np.datetime64("2008-12-01"), np.datetime64("2019-12-01"))
    phase = (t.values - tmin).astype("timedelta64[D]").astype(float) / 365.25 / 11
    hem = rng.choice([1, -1], n)
    lat = hem * np.clip(28 - 20 * phase + rng.normal(0, 4, n), 2, 45)
    a = np.array([silso.at[m, "N" if h > 0 else "S"] for m, h in zip(t.strftime("%Y-%m"), hem)])
    s = np.sin(np.radians(np.abs(lat)))
    gamma = (GAMMA0 + beta_t_frac * GAMMA0 * (a - 1)) * s + rng.normal(0, 15, n)
    phi = 10 ** rng.normal(21.7, 0.4, n)
    dstar = phi * ETA0 * (1 + beta_eta_frac * (a - 1)) + rng.normal(0, 1, n) * phi * ETA0
    sc = np.where(cyc == 24, 1.0, -1.0)
    cr = (2096 + (t - pd.Timestamp("2010-06-01")).days / 27.2753).astype(int)
    sintilt = np.sin(np.radians(gamma)) * np.sign(lat)
    cat = pd.DataFrame({
        "HARPNUM": np.arange(n), "T_REC": t.strftime("%Y.%m.%d_%H:%M:%S_TAI"), "role": "both",
        "qual_0x80": 0, "NOAA_NUM": 1, "USFLUX": phi, "LAT_FWT": lat, "CR": cr,
        "valid_bl": 1, "npos": 100, "nneg": 100, "phi_mx": phi, "lat_mean_deg": lat, "cycle": cyc,
        "cycle_state": "DATE", "sintilt": sintilt, "d_axial_bal_g": dstar / sc,
        "s_bl": np.sign(lat) * dstar * 1e40, "diagnostic_reason": "NONE",
    })
    for c in ("valid_bl", "phi_mx", "lat_mean_deg", "cycle", "sintilt", "s_bl"):
        cat[f"leg_{c}"] = cat[c]
    return cat


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
