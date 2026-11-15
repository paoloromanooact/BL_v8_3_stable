"""T5: deterministic sensitivity of the compact-pair dipole proxy to a prescribed additive shift of the Joy
component (docs/T5_PROXY_SENSITIVITY_NOTE.md, frozen in d47073c, SHA-256 4c2b8ad8...).

Not a test and not an estimate of solar quenching: it computes the slope Delta_beta that the prescribed
perturbation would inject, in T5 units, on the fixed catalogue. The real T5 slope g @ eta_c is NOT computed.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_proxy_sensitivity.py --selftest   # note §6.1, synthetic only
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t5_proxy_sensitivity.py --run        # single run, note §6.2 + §5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import cycle as cyc, geometry as geo, p2d, p2f_pilot as P, run_p2  # noqa: E402

NOTE = ROOT / "docs/T5_PROXY_SENSITIVITY_NOTE.md"
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
OUT = ROOT / "results/T5_PROXY_SENSITIVITY"

R_CM = geo.RSUN_CM_DEFAULT                 # note §3: nominal radius, declared assumption
C = 3.0 / (8.0 * np.pi * R_CM ** 2)       # G per Mx
GAMMA0 = P.GAMMA0                         # note §4: 24 deg, P2f reference, not re-estimated
ETA_BAR = 3.56e-25                        # note §5: scale of the P2f / T5-D2 simulations (G/Mx)
DELTA_MAX = (0.10, 0.20)                  # note §4: illustrative amplitudes
Q_LO, Q_HI = 0.05, 0.95                   # note §4: quantiles of cell activity replicated on T5 records
EXPECTED = (2375, 318)                    # note §2: records, cells
ID_RTOL = 1e-12                           # note §6.2


class TechnicalError(Exception):
    """Non-finite value or failed technical check: never counted as a passed check (note §6.1)."""


def require_finite(name, *arrays):
    for a in arrays:
        if not np.all(np.isfinite(np.asarray(a, float))):
            raise TechnicalError(f"non-finite values in {name}")


# ---------------------------------------------------------------- proxy and scenario (note §3, §4, §5)

def gamma_joy(lat_deg, sintilt):
    """Joy variable of run_p2.prepare: sign(lat) * degrees(arcsin(sintilt)); 0 at lat = 0 (note §3)."""
    return np.sign(lat_deg) * np.degrees(np.arcsin(np.clip(sintilt, -1.0, 1.0)))


def proxy(hale, phi, lat_deg, d_cm, gamma_deg):
    """P*(gamma) = hale * C * Phi * cos(lambda) * (d/R) * sin(gamma), in G (note §3)."""
    return hale * C * phi * np.cos(np.radians(lat_deg)) * (d_cm / R_CM) * np.sin(np.radians(gamma_deg))


def ramp(a_cell, a_lo, a_hi, delta_max):
    """delta(A) = delta_max * clip((A - A_lo)/(A_hi - A_lo), 0, 1) (note §4)."""
    if not a_hi > a_lo:
        raise TechnicalError("A_hi must exceed A_lo")
    return delta_max * np.clip((np.asarray(a_cell, float) - a_lo) / (a_hi - a_lo), 0.0, 1.0)


def shifted_gamma(gamma_deg, lat_deg, delta):
    """gamma' = gamma - delta * gamma0 * sin|lambda| (note §4)."""
    return gamma_deg - delta * GAMMA0 * np.sin(np.radians(np.abs(lat_deg)))


def delta_d(hale, phi, lat_deg, d_cm, gamma_deg, gamma_new_deg):
    """Delta_D = P*(gamma') - P*(gamma) as a direct difference of sines: no ratio, no singularity."""
    base = hale * C * phi * np.cos(np.radians(lat_deg)) * (d_cm / R_CM)
    return base * (np.sin(np.radians(gamma_new_deg)) - np.sin(np.radians(gamma_deg)))


def cell_sum(k_of_i, values, n_cells):
    out = np.zeros(n_cells)
    np.add.at(out, k_of_i, values)
    return out


def wls_fit(X, w, y):
    """Separate WLS solution (lstsq on sqrt(w)-scaled rows): coefficients and residual."""
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return coef, y - X @ coef


def rms_w(x, w):
    return float(np.sqrt(np.sum(w * x * x) / np.sum(w)))


def projection(g, Xf, W, d_eta):
    """Delta_beta = g @ Delta_eta, WLS residual on the full model, RMS_W and its ratio (note §5)."""
    d_beta = float(g @ d_eta)
    _, r = wls_fit(Xf, W, d_eta)
    num = rms_w(r, W)
    centred = d_eta - np.sum(W * d_eta) / np.sum(W)
    den = rms_w(centred, W)
    ratio = num / den if den > 0 else None
    return d_beta, num, den, ratio, ("" if den > 0 else "denominatore nullo: Delta_eta costante")


def counts(gamma, gamma_new, p_old, p_new, d_d):
    s_old, s_new = np.sign(p_old), np.sign(p_new)
    both = (s_old != 0) & (s_new != 0)
    return dict(n_gamma_zero_crossings=int((np.sign(gamma_new) != np.sign(gamma)).sum()),
                n_abs_gamma_new_gt_90=int((np.abs(gamma_new) > 90.0).sum()),
                n_delta_d_pos=int((d_d > 0).sum()), n_delta_d_neg=int((d_d < 0).sum()),
                n_delta_d_zero=int((d_d == 0).sum()),
                n_proxy_sign_changes=int((both & (s_old != s_new)).sum()),
                n_proxy_zero_before=int((s_old == 0).sum()), n_proxy_zero_after=int((s_new == 0).sum()))


def weighted_pearson(x, y, w):
    mx, my = np.sum(w * x) / np.sum(w), np.sum(w * y) / np.sum(w)
    cov = np.sum(w * (x - mx) * (y - my))
    return float(cov / np.sqrt(np.sum(w * (x - mx) ** 2) * np.sum(w * (y - my) ** 2)))


def proxy_quality(p_obs, d_star, k_of_i, phi_cell, eta_cell):
    """Descriptive only (note §5): per record (uniform weights) and per cell (weights W_c)."""
    nz = d_star != 0
    both = (np.sign(p_obs) != 0) & (np.sign(d_star) != 0)
    n_cells = len(phi_cell)
    p_cell = cell_sum(k_of_i, p_obs, n_cells) / phi_cell
    return dict(
        record_pearson=float(np.corrcoef(p_obs, d_star)[0, 1]),
        record_rms_diff_G=float(np.sqrt(np.mean((p_obs - d_star) ** 2))),
        record_median_ratio_P_over_dstar=float(np.median(p_obs[nz] / d_star[nz])),
        record_n_dstar_zero=int((~nz).sum()),
        record_frac_sign_concordant=float((np.sign(p_obs[both]) == np.sign(d_star[both])).mean()),
        record_n_proxy_zero=int((np.sign(p_obs) == 0).sum()),
        record_n_dstar_sign_zero=int((np.sign(d_star) == 0).sum()),
        cell_weighted_pearson=weighted_pearson(p_cell, eta_cell, phi_cell),
        cell_weighted_rms_diff_G_per_Mx=rms_w(p_cell - eta_cell, phi_cell))


# ---------------------------------------------------------------- design (note §2)

def load_design():
    cat = pd.read_csv(CATALOGUE, low_memory=False)
    d = run_p2.add_activity(run_p2.samples(cat)["S"], run_p2.load_silso())
    del cat
    dz = p2d.design_t5(d)
    # same filters as p2d.design_t5, to keep the per-record columns needed by the proxy
    r = d[np.isfinite(d["A_monthly"]) & np.isfinite(d["d_star"])].copy()
    r["cell"] = list(zip(r["CR"].astype(float), r["hemisphere"]))
    r = r[r.groupby("cell")["phi"].transform("size") >= 3].copy()
    c = run_p2.cells(r, "A_monthly", "d_star")
    keys = list(zip(c["CR"].astype(float), c["hemisphere"]))
    idx = {k: j for j, k in enumerate(keys)}
    r = r[r["cell"].isin(idx)]
    k_of_i = r["cell"].map(idx).to_numpy()
    if not (np.array_equal(k_of_i, dz["k_of_i"]) and np.array_equal(r["phi"].to_numpy(float), dz["phi"])):
        raise TechnicalError("record rows do not match p2d.design_t5")
    return r.reset_index(drop=True), dz


# ---------------------------------------------------------------- selftest (note §6.1): synthetic only

def compact_pair(lat_p, lon_p, lat_n, lon_n, cycle, phi=1e22):
    """Measure a two-point region with the conventions of measure.measure_v84 (equal fluxes)."""
    lp, ln = (lon_p, lat_p), (lon_n, lat_n)
    d_cm = math.radians(geo.great_circle_deg(*lp, *ln)) * R_CM
    leading = 1 if abs(geo.tilt_deg(ln, lp)) < 90.0 else -1
    lead, follow = (lp, ln) if leading == 1 else (ln, lp)
    sintilt = math.sin(math.radians(geo.tilt_deg(lead, follow)))
    lat_m = geo.weighted_centroid(np.array([lon_p, lon_n]), np.array([lat_p, lat_n]), np.array([1.0, 1.0]))[1]
    hale = 1 if leading == cyc.expected_leading_sign(cycle, lat_m) else -1
    d_bal = C * phi * (math.sin(math.radians(lat_p)) - math.sin(math.radians(lat_n)))
    d_star = run_p2.S_CYCLE[cycle] * d_bal
    g = gamma_joy(lat_m, sintilt)
    return dict(p=float(proxy(hale, phi, lat_m, d_cm, g)), d_star=d_star, hale=hale, lat=lat_m, d_cm=d_cm, gamma=g)


def selftest():
    res = []

    def ok(name, cond):
        res.append((name, bool(cond)))

    # orientation, lat != 0: all combinations of hemisphere, cycle, which polarity leads, poleward/equatorward
    hales = set()
    good = True
    for hem in (1, -1):
        for cycle in (24, 25):
            for pos_west in (True, False):
                for pos_poleward in (True, False):
                    base, dl = 15.0 * hem, 1.0 * hem
                    lat_p = base + (dl if pos_poleward else -dl)
                    lat_n = base - (dl if pos_poleward else -dl)
                    lon_p, lon_n = (101.0, 99.0) if pos_west else (99.0, 101.0)
                    x = compact_pair(lat_p, lon_p, lat_n, lon_n, cycle)
                    hales.add(x["hale"])
                    rel = abs(x["p"] - x["d_star"]) / abs(x["d_star"])
                    good &= np.sign(x["p"]) == np.sign(x["d_star"]) and rel < 1e-2
    ok("orientation: sign(P*) = sign(S_CYCLE*D_bal) and |rel diff| < 1e-2, 16 configurations", good)
    x = compact_pair(16.0, 101.0, 14.0, 99.0, 24)
    flipped = proxy(-x["hale"], 1e22, x["lat"], x["d_cm"], x["gamma"])
    ok("orientation test is sensitive: inverting hale gives the wrong sign", np.sign(flipped) != np.sign(x["d_star"]))
    ok("orientation: both Hale and anti-Hale covered", hales == {1, -1})
    # tilt zero: polarities at the same latitude
    z = compact_pair(15.0, 101.0, 15.0, 99.0, 24)
    ok("tilt zero: D_bal = 0 and |P*| negligible", z["d_star"] == 0.0 and abs(z["p"]) <= 1e-12 * C * 1e22)
    # lat = 0: degenerate convention (note §3); polarities at +/-theta have D_bal != 0, but gamma = P* = Delta_D = 0
    g0 = gamma_joy(0.0, 0.5)
    ok("lat = 0: gamma = 0", g0 == 0.0)
    ok("lat = 0: P* = 0", proxy(1, 1e22, 0.0, 1e10, g0) == 0.0)
    ok("lat = 0: mu = 0 so Delta_D = 0",
       delta_d(1, 1e22, 0.0, 1e10, g0, shifted_gamma(g0, 0.0, 0.2)) == 0.0)
    eq = compact_pair(1.0, 100.0, -1.0, 100.0, 24)
    ok("lat = 0 example: D_bal of +/-theta pair is non-zero (limit declared, not reproduced)", eq["d_star"] != 0.0)
    # Delta_D by hand (math module, independent of numpy path)
    hale, phi, lat, dcm, gam, dl = -1, 2e22, 20.0, 3e9, 10.0, 0.2
    mu = 24.0 * math.sin(math.radians(20.0))
    by_hand = -1 * (3 / (8 * math.pi * R_CM ** 2)) * 2e22 * math.cos(math.radians(20.0)) * (3e9 / R_CM) * (
        math.sin(math.radians(10.0 - 0.2 * mu)) - math.sin(math.radians(10.0)))
    got = float(delta_d(hale, phi, lat, dcm, gam, shifted_gamma(gam, lat, dl)))
    ok("Delta_D by hand", abs(got - by_hand) <= 1e-12 * abs(by_hand))
    ok("shift preserves gamma - mu: gamma' - (1-delta) mu = gamma - mu",
       abs((float(shifted_gamma(gam, lat, dl)) - (1 - dl) * mu) - (gam - mu)) < 1e-12)
    # ramp
    r = ramp(np.array([-1.0, 0.5, 1.5, 2.5, 9.0]), 0.5, 2.5, 0.2)
    ok("ramp: 0 below and at A_lo, half at mid, delta_max at and above A_hi",
       np.allclose(r, [0.0, 0.0, 0.1, 0.2, 0.2], rtol=0, atol=1e-15))
    try:
        ramp([1.0], 2.0, 1.0, 0.1)
        ok("ramp: A_hi <= A_lo rejected", False)
    except TechnicalError:
        ok("ramp: A_hi <= A_lo rejected", True)
    # projection on a synthetic design: 4 cycle-hemisphere groups + activity column
    rng = np.random.default_rng(12345)
    n = 60
    grp = np.repeat(np.arange(4), n // 4)
    Xn = np.column_stack([(grp == j).astype(float) for j in range(4)])
    a = rng.uniform(0.2, 3.0, n)
    Xf = np.column_stack([Xn, a - 1.0])
    W = rng.uniform(1.0, 5.0, n)
    g = p2d.wls_row(Xf, W)
    sel = np.zeros(Xf.shape[1]); sel[-1] = 1.0
    ok("projection: g @ Xf selects the activity column", np.allclose(g @ Xf, sel, rtol=0, atol=1e-10))
    y = Xf @ np.array([1.0, -2.0, 0.5, 3.0, -0.7]) + rng.normal(0, 0.3, n)
    coef, resid = wls_fit(Xf, W, y)
    ok("projection: g @ y equals a separate WLS slope", abs(float(g @ y) - coef[-1]) < 1e-10)
    d_beta, num, den, ratio, why = projection(g, Xf, W, y)
    ok("projection: residual RMS equals the separate WLS residual", abs(num - rms_w(resid, W)) < 1e-12)
    zero = np.zeros(n)
    db0, num0, den0, ratio0, why0 = projection(g, Xf, W, zero)
    ok("delta_max = 0: Delta_beta = 0 and residual ratio NA with reason",
       db0 == 0.0 and ratio0 is None and why0 != "")
    dd0 = delta_d(np.ones(5), np.full(5, 1e22), np.full(5, 15.0), np.full(5, 1e9), np.full(5, 7.0),
                  shifted_gamma(np.full(5, 7.0), np.full(5, 15.0), ramp(np.linspace(0, 3, 5), 0.5, 2.5, 0.0)))
    ok("delta_max = 0: Delta_D = 0", np.all(dd0 == 0.0))
    # non-finite values are technical errors
    for bad in (np.nan, np.inf):
        try:
            require_finite("x", np.array([1.0, bad]))
            ok(f"non-finite {bad} rejected", False)
        except TechnicalError:
            ok(f"non-finite {bad} rejected", True)
    # counts on a hand case
    c = counts(np.array([1.0, -1.0, 0.0, 80.0]), np.array([-1.0, -2.0, 0.0, 95.0]),
               np.array([1.0, -1.0, 0.0, 2.0]), np.array([-1.0, -2.0, 0.0, 3.0]), np.array([-2.0, -1.0, 0.0, 1.0]))
    ok("counts by hand", c == dict(n_gamma_zero_crossings=1, n_abs_gamma_new_gt_90=1, n_delta_d_pos=1,
                                   n_delta_d_neg=2, n_delta_d_zero=1, n_proxy_sign_changes=1,
                                   n_proxy_zero_before=1, n_proxy_zero_after=1))
    # end-to-end compute() on a synthetic design (no catalogue)
    rs, dzs = synthetic_design(np.random.default_rng(7))
    meta = {}
    rows, cells, quality, info = compute(rs, dzs, meta)
    hand_g = p2d.wls_row(dzs["Xf_c"], dzs["W_c"])
    first = rows[0]
    a_rec = (dzs["Xf_c"][:, -1] + 1.0)[dzs["k_of_i"]]
    dd = delta_d(rs.hale_sign.to_numpy(), rs.phi.to_numpy(), rs.lat.to_numpy(), rs.d_cm.to_numpy(), rs.gamma.to_numpy(),
                 shifted_gamma(rs.gamma.to_numpy(), rs.lat.to_numpy(), ramp(a_rec, info["a_lo"], info["a_hi"], DELTA_MAX[0])))
    d_eta = cell_sum(dzs["k_of_i"], dd, len(dzs["W_c"])) / dzs["W_c"]
    ok("end-to-end: identity passes on synthetic records", meta["identity_n_fail"] == 0)
    ok("end-to-end: Delta_beta equals g @ Delta_eta recomputed", abs(first["delta_beta_G_per_Mx"] - float(hand_g @ d_eta)) <= 1e-12 * abs(first["delta_beta_G_per_Mx"]))
    ok("end-to-end: two scenarios, finite outputs", len(rows) == 2 and all(np.isfinite(rw["delta_beta_G_per_Mx"]) for rw in rows))
    ok("end-to-end: proxy quality finite", all(np.isfinite(v) for v in quality.values()))
    rs_bad = rs.copy(); rs_bad.loc[3, "s_star"] *= 1.0 + 1e-9
    try:
        compute(rs_bad, dzs, {})
        ok("end-to-end: broken identity is a technical error", False)
    except TechnicalError:
        ok("end-to-end: broken identity is a technical error", True)
    regression_tests(ok)
    for name, cond in res:
        print(("PASS " if cond else "FAIL ") + name)
    n_ok = sum(c for _, c in res)
    print(f"{n_ok}/{len(res)} passed")
    return n_ok == len(res)


# ---------------------------------------------------------------- computation (note §5, §6.2)

def compute(r, dz, meta):
    """Everything after the design: §6.2 identity, quantiles, scenarios, counts, proxy quality."""
    n_cell = len(dz["W_c"])
    hale = r["hale_sign"].to_numpy(float)
    phi = r["phi"].to_numpy(float)
    lat = r["lat"].to_numpy(float)
    dcm = r["d_cm"].to_numpy(float)
    gam = r["gamma"].to_numpy(float)
    s_star = r["s_star"].to_numpy(float)
    d_star = r["d_star"].to_numpy(float)
    sintilt = r["sintilt"].to_numpy(float)
    # inputs checked before any transformation (np.clip would turn inf into 1)
    require_finite("record inputs", hale, phi, lat, dcm, gam, s_star, d_star, sintilt)
    if np.any(np.abs(sintilt) > 1.0):
        raise TechnicalError("sintilt outside [-1, 1]")
    if not np.allclose(gam, gamma_joy(lat, sintilt), rtol=0, atol=1e-12):
        raise TechnicalError("gamma column differs from the Joy variable definition")
    k = np.asarray(dz["k_of_i"])
    Xf, W = np.asarray(dz["Xf_c"], float), np.asarray(dz["W_c"], float)
    require_finite("design", Xf, W, dz["cell_eta"])
    if np.any(W <= 0):
        raise TechnicalError("cell weights must be strictly positive")
    if len(k) != len(r) or k.min() < 0 or k.max() >= len(W) or len(np.unique(k)) != len(W):
        raise TechnicalError("record-to-cell map inconsistent with the design")
    a_cell = Xf[:, -1] + 1.0
    # §6.2 identity on the catalogue, no activity used
    p_obs = proxy(hale, phi, lat, dcm, gam)
    ref = 3.0 * s_star / (8.0 * np.pi * R_CM ** 3)
    scale = np.maximum(np.abs(p_obs), np.abs(ref))
    bad = np.where(scale == 0, p_obs != ref, np.abs(p_obs - ref) > ID_RTOL * scale)
    rel = np.where(scale > 0, np.abs(p_obs - ref) / np.where(scale > 0, scale, 1.0), 0.0)
    meta.update(identity_n_fail=int(bad.sum()), identity_max_rel=float(rel.max()), n_lat_zero=int((lat == 0).sum()))
    if bad.any():
        raise TechnicalError(f"proxy identity failed on {int(bad.sum())} records")
    # quantiles of cell activity replicated on the T5 records (note §4)
    a_rec = a_cell[k]
    a_lo, a_hi = (float(v) for v in np.quantile(a_rec, [Q_LO, Q_HI]))
    meta.update(A_lo=repr(a_lo), A_hi=repr(a_hi))
    g = p2d.wls_row(Xf, W)
    rows, cells = [], dict(cell=np.arange(n_cell), A_cell=a_cell, W_c=W)
    for dmax in DELTA_MAX:
        delta = ramp(a_rec, a_lo, a_hi, dmax)
        gnew = shifted_gamma(gam, lat, delta)
        dd = delta_d(hale, phi, lat, dcm, gam, gnew)
        require_finite("Delta_D", dd)
        d_eta = cell_sum(k, dd, n_cell) / W
        d_beta, num, den, ratio, why = projection(g, Xf, W, d_eta)
        rows.append(dict(delta_max=dmax, delta_beta_G_per_Mx=d_beta, e_ref=d_beta / ETA_BAR,
                         rms_w_resid=num, rms_w_centred=den,
                         resid_ratio=("NA" if ratio is None else ratio), resid_ratio_reason=why,
                         **counts(gam, gnew, p_obs, proxy(hale, phi, lat, dcm, gnew), dd)))
        cells[f"delta_eta_dmax_{dmax:.2f}"] = d_eta
    quality = proxy_quality(p_obs, d_star, k, W, dz["cell_eta"])
    validate_outputs(rows, cells, quality, a_lo, a_hi)
    return rows, cells, quality, dict(g=g, a_lo=a_lo, a_hi=a_hi)


def validate_outputs(rows, cells, quality, a_lo, a_hi):
    """Every reported number must be finite; the only allowed non-number is the residual ratio 'NA' with its
    reason (note §5). Anything else is a technical error, never a silent success."""
    require_finite("quantiles", [a_lo, a_hi])
    for row in rows:
        for key, v in row.items():
            if key == "resid_ratio_reason":
                continue
            if key == "resid_ratio" and v == "NA":
                if not row["resid_ratio_reason"]:
                    raise TechnicalError("residual ratio NA without a reason")
                continue
            require_finite(f"summary {key}", [v])
    for key, v in cells.items():
        require_finite(f"cells {key}", v)
    for key, v in quality.items():
        require_finite(f"proxy quality {key}", [v])


def synthetic_design(rng, n_cell=24, per_cell=4):
    """Synthetic records and design with the same structure as p2d.design_t5 (selftest only)."""
    k = np.repeat(np.arange(n_cell), per_cell)
    n = len(k)
    hem = np.where(np.arange(n_cell) % 2 == 0, 1.0, -1.0)[k]
    lat = hem * rng.uniform(5.0, 30.0, n)
    sintilt = rng.uniform(-0.6, 0.9, n)
    phi = rng.uniform(1e21, 1e22, n)
    dcm = rng.uniform(1e9, 1e10, n)
    hale = rng.choice([-1.0, 1.0], n, p=[0.1, 0.9])
    gam = gamma_joy(lat, sintilt)
    s_bl = hale * phi * dcm * np.cos(np.radians(lat)) * sintilt
    r = pd.DataFrame(dict(hale_sign=hale, phi=phi, lat=lat, d_cm=dcm, gamma=gam, sintilt=sintilt,
                          s_star=np.sign(lat) * s_bl, d_star=proxy(hale, phi, lat, dcm, gam) * rng.uniform(0.8, 1.2, n)))
    W = cell_sum(k, phi, n_cell)
    grp = np.arange(n_cell) % 4
    a_cell = rng.uniform(0.2, 3.0, n_cell)
    Xf = np.column_stack([(grp == j).astype(float) for j in range(4)] + [a_cell - 1.0])
    eta = cell_sum(k, r["d_star"].to_numpy(), n_cell) / W
    return r, dict(k_of_i=k, Xf_c=Xf, W_c=W, cell_eta=eta)


# ---------------------------------------------------------------- run (note §5, §6.2, §8)

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a, runner=subprocess.run):
    """Run git and fail loudly: a failed command is never read as an empty (clean) answer."""
    p = runner(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise TechnicalError(f"git {' '.join(a)} failed ({p.returncode}): {p.stderr.strip()}")
    return p.stdout.strip()


def head_commit(git_fn=git):
    h = git_fn("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", h):
        raise TechnicalError(f"invalid HEAD commit {h!r}")
    return h


def finite_json(obj):
    """Replace non-finite floats with strings so that META can always be written (allow_nan=False)."""
    if isinstance(obj, dict):
        return {k: finite_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [finite_json(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return f"non-finite: {obj!r}"
    return obj


def run(out_dir=OUT, catalogue=CATALOGUE, loader=load_design, git_fn=git, expected=EXPECTED):
    try:
        if git_fn("status", "--porcelain", "--untracked-files=no"):
            print("tracked tree not clean: refusing to run")
            return 2
    except TechnicalError as exc:
        print(f"refusing to run: {exc}")
        return 2
    out_dir.mkdir(parents=True, exist_ok=False)     # never overwrite an attempt
    meta = dict(note=str(NOTE.relative_to(ROOT)), outcome="errore tecnico", real_slope_computed=False)
    code = 1
    try:
        meta.update(sha256_note=sha(NOTE), sha256_script=sha(__file__), git_commit=head_commit(git_fn),
                    sha256_catalogue_before=sha(catalogue),
                    design_source="run_p2.samples(cat)['S'] + run_p2.add_activity(load_silso()) + p2d.design_t5",
                    R_cm=R_CM, C_G_per_Mx=C, gamma0_deg=GAMMA0, eta_bar=ETA_BAR, delta_max=list(DELTA_MAX),
                    quantiles=[Q_LO, Q_HI], quantile_method="numpy.quantile linear, unit weight per T5 record",
                    env=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
        r, dz = loader()
        n_rec, n_cell = len(r), len(dz["W_c"])
        meta.update(n_records=n_rec, n_cells=n_cell)
        if (n_rec, n_cell) != tuple(expected):
            raise TechnicalError(f"sample size {(n_rec, n_cell)} differs from expected {tuple(expected)}")
        rows, cells, quality, info = compute(r, dz, meta)
        pd.DataFrame(rows).to_csv(out_dir / "SUMMARY.csv", index=False)
        pd.DataFrame(cells).to_csv(out_dir / "CELLS.csv", index=False)
        pd.DataFrame([quality]).to_csv(out_dir / "PROXY_QUALITY.csv", index=False)
        meta.update(proxy_quality=quality, outcome="eseguita")
        code = 0
    except Exception as exc:                        # every failure recorded with type and message
        meta.update(outcome="errore tecnico", exception_type=type(exc).__name__, exception=str(exc),
                    traceback=traceback.format_exc())
        code = 1
    finally:
        try:
            meta["sha256_catalogue_after"] = sha(catalogue)
            if "sha256_catalogue_before" in meta and meta["sha256_catalogue_after"] != meta["sha256_catalogue_before"]:
                meta["outcome"], code = "errore tecnico: catalogo cambiato", 1
        except Exception as exc2:                   # does not hide the original error
            meta["sha256_catalogue_after_error"] = f"{type(exc2).__name__}: {exc2}"
            if code == 0:
                meta["outcome"], code = "errore tecnico: hash finale non calcolabile", 1
        try:
            text = json.dumps(meta, indent=2, default=str, allow_nan=False)
        except ValueError:
            meta = finite_json(meta)
            meta["outcome"], code = "errore tecnico: valori non finiti in META", 1
            text = json.dumps(meta, indent=2, default=str, allow_nan=False)
        (out_dir / "META.json").write_text(text)
        print(json.dumps({k: meta.get(k) for k in ("outcome", "n_records", "n_cells", "identity_n_fail",
                                                   "exception_type", "exception")}, default=str))
        print("fatto")
    return code


# ---------------------------------------------------------------- regression tests for the review of 86bd31c

class _Proc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def regression_tests(ok):
    rs, dzs = synthetic_design(np.random.default_rng(11))
    # 1. non-finite values
    bad = dict(dzs, cell_eta=dzs["cell_eta"].copy()); bad["cell_eta"][2] = np.nan
    ok("regression: NaN in cell_eta is a technical error", _raises(lambda: compute(rs, bad, {})))
    r_inf = rs.copy(); r_inf.loc[0, "sintilt"] = np.inf
    r_inf.loc[0, "gamma"] = gamma_joy(r_inf.loc[0, "lat"], 1.0)
    ok("regression: sintilt = inf rejected before the clip", _raises(lambda: compute(r_inf, dzs, {})))
    w0 = dict(dzs, W_c=dzs["W_c"].copy()); w0["W_c"][1] = 0.0
    ok("regression: zero cell weight rejected", _raises(lambda: compute(rs, w0, {})))
    ok("regression: NaN in a summary value rejected",
       _raises(lambda: validate_outputs([dict(delta_beta_G_per_Mx=np.nan, resid_ratio="NA", resid_ratio_reason="x")],
                                        {}, {}, 0.5, 2.5)))
    ok("regression: residual ratio NA without reason rejected",
       _raises(lambda: validate_outputs([dict(resid_ratio="NA", resid_ratio_reason="")], {}, {}, 0.5, 2.5)))
    # 2. git failures
    fail = lambda *a, **k: _Proc(128, "", "fatal: not a git repository")
    ok("regression: failed git command raises", _raises(lambda: git("status", runner=fail)))
    ok("regression: empty HEAD rejected", _raises(lambda: head_commit(lambda *a: "")))
    ok("regression: non-hex HEAD rejected", _raises(lambda: head_commit(lambda *a: "HEAD")))

    def git_ok(*a):
        return "" if a[0] == "status" else "0123456789abcdef0123456789abcdef01234567"

    def git_dirty(*a):
        return " M x" if a[0] == "status" else "0123456789abcdef0123456789abcdef01234567"

    def git_bad(*a):
        raise TechnicalError("git status failed (128)")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cat = tmp / "catalogue.csv"; cat.write_text("synthetic\n")
        quiet = _quiet
        ok("regression: git failure refuses to run (code 2, no output dir)",
           quiet(lambda: run(tmp / "o1", cat, lambda: (rs, dzs), git_bad, (len(rs), len(dzs["W_c"])))) == 2
           and not (tmp / "o1").exists())
        ok("regression: dirty tree refuses to run",
           quiet(lambda: run(tmp / "o1b", cat, lambda: (rs, dzs), git_dirty, (len(rs), len(dzs["W_c"])))) == 2)
        # 3. META always written, exceptions recorded
        c = quiet(lambda: run(tmp / "o2", tmp / "missing.csv", lambda: (rs, dzs), git_ok, (len(rs), len(dzs["W_c"]))))
        m = json.loads((tmp / "o2/META.json").read_text())
        ok("regression: missing catalogue -> META written, exception recorded, code != 0",
           c != 0 and m["exception_type"] == "FileNotFoundError" and m["outcome"].startswith("errore"))

        def loader_keyerror():
            raise KeyError("hale_sign")
        c = quiet(lambda: run(tmp / "o3", cat, loader_keyerror, git_ok, (len(rs), len(dzs["W_c"]))))
        m = json.loads((tmp / "o3/META.json").read_text())
        ok("regression: KeyError in loader recorded with type and message", c != 0 and m["exception_type"] == "KeyError"
           and "hale_sign" in m["exception"])
        c = quiet(lambda: run(tmp / "o4", cat, lambda: (rs, bad), git_ok, (len(rs), len(dzs["W_c"]))))
        m = json.loads((tmp / "o4/META.json").read_text())
        ok("regression: NaN in design through run -> code != 0, not 'eseguita'", c != 0 and m["outcome"] != "eseguita")
        c = quiet(lambda: run(tmp / "o5", cat, lambda: (rs, dzs), git_ok, (0, 0)))
        ok("regression: wrong sample size -> code != 0", c != 0)
        c = quiet(lambda: run(tmp / "o6", cat, lambda: (rs, dzs), git_ok, (len(rs), len(dzs["W_c"]))))
        m = json.loads((tmp / "o6/META.json").read_text())
        files = sorted(p.name for p in (tmp / "o6").iterdir())
        ok("regression: valid synthetic run -> code 0, 'eseguita', four files, valid HEAD recorded",
           c == 0 and m["outcome"] == "eseguita" and files == ["CELLS.csv", "META.json", "PROXY_QUALITY.csv", "SUMMARY.csv"]
           and re.fullmatch(r"[0-9a-f]{40}", m["git_commit"]) is not None)
        ok("regression: existing output dir is never overwritten",
           _raises(lambda: quiet(lambda: run(tmp / "o6", cat, lambda: (rs, dzs), git_ok, (len(rs), len(dzs["W_c"])))),
                   FileExistsError))
    ok("regression: finite_json makes non-finite META serializable",
       json.dumps(finite_json({"a": float("nan"), "b": [1.0, float("inf")]}), allow_nan=False) is not None)


def _raises(fn, exc=TechnicalError):
    try:
        fn()
    except exc:
        return True
    return False


def _quiet(fn):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return fn()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.run:
        sys.exit(run())
