"""Test di run_p3 su dati costruiti (nessun abbinamento con dati reali)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from sharpbl import run_p3  # noqa: E402


def test_axial_delta_is_periodic():
    assert run_p3.axial_delta([89.0], [-89.0])[0] == pytest.approx(2.0)
    assert run_p3.axial_delta([10.0], [-10.0])[0] == pytest.approx(20.0)
    assert run_p3.axial_delta([0.0], [90.0])[0] == pytest.approx(90.0)


def test_fisher_lee_branch_invariant_and_undefined():
    rng = np.random.default_rng(1)
    g1 = rng.uniform(-90, 90, 200)
    g2 = g1 + rng.normal(0, 10, 200)
    g2w = ((g2 + 90) % 180) - 90
    assert run_p3.fisher_lee(g1, g2) == pytest.approx(run_p3.fisher_lee(g1, g2w))
    assert run_p3.fisher_lee(g1, g2) > 0.8
    assert np.isnan(run_p3.fisher_lee([1.0, 2.0], [1.0, 2.0]))          # n < 3
    assert np.isnan(run_p3.fisher_lee([5.0] * 10, list(range(10))))    # tutti gli assi uguali


def test_degenerate_replicates_counted_and_criterion_not_evaluable():
    n = 30
    df = pd.DataFrame({"gamma": np.r_[np.full(n - 3, 5.0), [10.0, 20.0, 30.0]],
                       "b_gamma": np.r_[np.full(n - 3, 5.0), [12.0, 18.0, 33.0]],
                       "family_id": np.r_[np.zeros(n - 3), [1, 2, 3]]})
    for c, v in (("leading_sign", 1), ("b_leading_geom", 1), ("hale_ours_rec", 1), ("hale_bard_rec", 1),
                 ("hale_sign", 1), ("Hale", True), ("sep_deg", 5.0), ("b_sep_deg", 5.0),
                 ("lat_mean_deg", 20.0), ("BMRLatitude", 20.0), ("phi_mx", 1e22), ("PFlux", 5e21), ("NFlux", -5e21)):
        df[c] = v
    df["sep_deg"] = np.linspace(3, 8, n)
    df["b_sep_deg"] = np.linspace(3, 8, n)
    boot = run_p3.family_bootstrap(df, nboot=400, seed=3)
    assert boot["rho_fisher_lee_n_degenerate"] > 4   # famiglia grande uguale estratta da sola spesso
    ind = run_p3.indicators(df)
    tab, verdict, deg = run_p3.outcome(ind, boot)
    assert deg > 0.01
    assert "non valutabile" in " ".join(tab["criterion"])
    assert verdict.startswith("da investigare")


def test_one_to_one_global_order_and_ties():
    pairs = pd.DataFrame({"row": [0, 0, 1, 1], "HARPNUM": [10, 11, 10, 12], "T_REC": ["a"] * 4,
                          "QUALITY": 0, "dt_h": 0.0, "dlat": 0.0, "dlon": 0.0, "d": [0.5, 0.6, 0.2, 0.9]})
    m = run_p3.assign_one_to_one(pairs).set_index("row")
    assert m.loc[1, "HARPNUM"] == 10 and m.loc[0, "HARPNUM"] == 11   # (1,10) d=0.2 prima, poi 0 prende 11
    tie = pd.DataFrame({"row": [0, 1], "HARPNUM": [10, 10], "T_REC": ["a", "a"], "QUALITY": 0,
                        "dt_h": 0.0, "dlat": 0.0, "dlon": 0.0, "d": [0.3, 0.3]})
    assert run_p3.assign_one_to_one(tie)["row"].tolist() == [0]      # a parita': HARP, poi riga BARD minore


def test_conventions_on_constructed_catalogue():
    t = pd.date_range("2012-01-01", periods=50, freq="7D")
    lat = np.where(np.arange(50) % 2, 15.0, -15.0)
    lon_c = (np.arange(50) * 37.0) % 360
    b = pd.DataFrame({"t": t, "BMRLatitude": lat, "BMRLongitude": lon_c,
                      "PLatitude": lat, "NLatitude": lat + np.sign(lat) * 2,
                      "PLongitude": lon_c + np.where(lat > 0, -3, 3), "NLongitude": lon_c + np.where(lat > 0, 3, -3),
                      "LeadingPolarity": np.where(lat > 0, -1, 1)})
    b["Hale"] = True
    b = run_p3.bard_geometry(b)
    b["Tilt_rel"] = -b["b_asin"]
    meta_times = pd.DataFrame({"t": t, "CRLN_OBS": lon_c + 20})
    conv = run_p3.conventions(b, meta_times).set_index("convention")["result"]
    assert conv["direzione longitudini"] == "ovest"
    assert conv["riferimento longitudini"] == "Carrington"
    assert conv["segno Tilt_rel"] == "Tilt_rel = -asin(sin a)"
    assert conv["significato Hale"] == "Hale = leading attesa ciclo 24"
