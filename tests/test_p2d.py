"""Verifica che l'implementazione di P2d coincida con il protocollo (solo dati sintetici)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from sharpbl import p2d, run_p2  # noqa: E402


@pytest.fixture(scope="module")
def sample():
    cat = p2d.synthetic_catalog_p2d("V3", seed=11)
    return run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())


@pytest.mark.parametrize("test", ["T3", "T5"])
def test_linear_shortcut_equals_direct_refit(sample, test):
    """beta* dalla scorciatoia lineare = beta ricalcolato con la stessa regressione di P2 sui dati simulati."""
    dz = p2d.design_t3(sample) if test == "T3" else p2d.design_t5(sample)
    lp = p2d.linear_pieces(dz)
    rng = np.random.default_rng(0)
    U = rng.standard_normal((lp["par"]["grid_len"], 2))
    V = rng.choice([-1.0, 1.0], len(lp["ge"]))
    fast = lp["const"] + (U * lp["B"]).sum() + V @ lp["ge"]
    ystar = lp["mean"] + U[lp["t_idx"], lp["h_idx"]] + lp["e"] * V
    if test == "T3":
        X, w = dz["Xf"], dz["w"]
        direct = (np.linalg.pinv(X.T @ (w[:, None] * X)) @ (X.T @ (w * ystar)))[-1]
    else:
        eta = np.bincount(dz["k_of_i"], weights=dz["agg"] * ystar, minlength=len(dz["W_c"]))
        X, w = dz["Xf_c"], dz["W_c"]
        direct = (np.linalg.pinv(X.T @ (w[:, None] * X)) @ (X.T @ (w * eta)))[-1]
    assert fast == pytest.approx(direct, rel=1e-9, abs=1e-12)


@pytest.mark.parametrize("test", ["T3", "T5"])
def test_observed_beta_equals_p2(sample, test):
    lp = p2d.linear_pieces(p2d.design_t3(sample) if test == "T3" else p2d.design_t5(sample))
    ref = run_p2.t3(sample, "S", "A_monthly", False)[0] if test == "T3" else \
        run_p2.t5(sample, "S", "A_monthly", "d_star", False, "D*")[0]
    assert lp["par"]["beta_obs"] == pytest.approx(ref["estimate"], rel=1e-9)


def test_temporal_estimation_recovers_parameters():
    rng = np.random.default_rng(3)
    par = dict(phi=0.8, sigma_u2=1.0, kappa=0.6, grid_len=3000, lo=0)
    U = p2d.simulate_ar1(par, 1, rng)[0]
    idx = pd.MultiIndex.from_arrays([np.repeat(np.arange(3000), 2).astype(float), np.tile(["N", "S"], 3000)])
    u = pd.Series(U.reshape(-1), index=idx)
    W = pd.Series(1.0, index=idx)
    s2 = pd.Series(0.0, index=idx)
    est = p2d.estimate_temporal(u, W, s2)
    assert est["phi"] == pytest.approx(0.8, abs=0.03)
    assert est["kappa"] == pytest.approx(0.6, abs=0.05)
    assert est["sigma_u2"] == pytest.approx(1.0, rel=0.15)
    assert est["applicable"] == 1


def test_not_estimable_gives_fallback_not_zero(sample):
    few = sample[sample["CR"] < sample["CR"].min() + 15]          # meno di 30 CR
    r = p2d.p2d_test(few, "T3", M=200, seed=1)
    assert r["verdict_p2d"] == "non applicabile (P2d §3)"
    assert r["too_few_cr"] == 1


def test_p_value_finite_correction_and_ties():
    sims = np.zeros(999)
    d = p2d.decide(0.0, sims)                 # tutti pareggi: contano a sfavore
    assert d["p_low"] == 1.0 and d["p_high"] == 1.0 and d["verdict_p2d"] == "non deciso (P2d)"
    d = p2d.decide(-5.0, np.linspace(-1, 1, 999))
    assert d["p_low"] == pytest.approx(1 / 1000) and d["verdict_p2d"] == "quenching supportato (P2d)"
    d = p2d.decide(5.0, np.linspace(-1, 1, 999))
    assert d["verdict_p2d"] == "segno opposto (P2d)"


def test_one_outer_smoke():
    rows = p2d.one_outer(("V1", 0, 0.0, 300))
    assert {r["test"] for r in rows} == {"T3", "T5"}
    assert all(r["verdict"] for r in rows)


def test_acceptance_rule_threshold():
    assert p2d.cp_upper(65, 2000) <= 0.04 < p2d.cp_upper(66, 2000)
