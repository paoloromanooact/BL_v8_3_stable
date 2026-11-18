"""Independent scientific recount of prospective phase A (does not import scripts/prospective_phase_a.py).

Rebuilds E0 and every E1, E2 (f = 1) and E3 (f = 1) design realisation from the saved slot log SLOTS.csv.gz (donor
cell of each non-empty slot; with f = 1 every copied record is kept), with its own calendar, cycle transfer, cells,
matrices (normal equations, not pinv), proxy target and covariance; then compares targets and SE (model (a), k = 1,
AR(1) 0.5 and steps of 20 CR at the P2f scale) with RAW.csv.gz. Shared upstream only: run_p2 (catalogue sample S and
SILSO activity). Writes results/PROSPECTIVE_PHASE_A_RECOUNT/RECOUNT.csv and RECEIPT.json; refuses to overwrite.
"""
import ast
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import run_p2  # noqa: E402

D = ROOT / "results/PROSPECTIVE_PHASE_A"
OUT = ROOT / "results/PROSPECTIVE_PHASE_A_RECOUNT"
ETA, G0, SDE, SDX = 3.56e-25, 24.0, 15.0, 7.5
R_CM = 6.96e10
CPROXY = 3.0 / (8.0 * math.pi * R_CM ** 2)
MINIMA = [(22, pd.Timestamp("1985-08-01")), (23, pd.Timestamp("1996-08-01")),
          (24, pd.Timestamp("2008-12-01")), (25, pd.Timestamp("2019-12-01"))]
E1_OFFSET = 2317 - 2175          # amendment A1: CR 2317 + k <- CR 2175 + k


def cr_start(c):
    """Meeus ch. 29 (definition registered in amendment A1)."""
    m = math.radians(281.96 + 26.882476 * c)
    jde = 2398140.2270 + 27.2752316 * c + 0.1454 * math.sin(m) - 0.0085 * math.sin(2 * m) - 0.0141 * math.cos(2 * m)
    return pd.Timestamp("1970-01-01") + pd.Timedelta(days=jde - 2440587.5)


def cycle_at(ts):
    c = 22
    for k, m in MINIMA:
        if ts >= m:
            c = k
    return c


def records_s():
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    silso = run_p2.load_silso()
    S = run_p2.add_activity(run_p2.samples(cat)["S"], silso)
    S = S[np.isfinite(S["A_monthly"])].reset_index(drop=True)
    R = pd.DataFrame(dict(CR=S.CR.astype(int), hem=S.hemisphere, lat=S.lat, s=S.sinlat, phi=S.phi, cyc=S.cyc.astype(int),
                          A=S.A_monthly, gamma=S.gamma, hale=S.hale_sign, d_cm=S.d_cm, d_star=S.d_star, M=0))
    return R, silso["monthly"]


def build(R0, slots, act):
    parts = [R0]
    tc_donor = {}
    for row in slots.itertuples():
        if row.empty:
            continue
        dcr, dh = ast.literal_eval(row.donor)
        don = R0[(R0.CR == dcr) & (R0.hem == dh)].copy()
        if len(don) != row.n_copied or row.n_kept != row.n_copied:
            raise SystemExit(f"slot {row.CR}{row.hem}: donor size {len(don)} vs log {row.n_copied}/{row.n_kept}")
        tcd = tc_donor.setdefault((dcr, dh), cycle_at(cr_start(dcr)))
        src = row.CR - E1_OFFSET if row.CR > 2316 else row.CR
        tcs = cycle_at(cr_start(src)) + (1 if row.CR > 2316 else 0)
        don["cyc"] = tcs + (don.cyc - tcd)
        don["A"] = act.at[cr_start(src).strftime("%Y-%m"), row.hem]
        don["CR"], don["M"] = row.CR, row.M
        parts.append(don)
    return pd.concat(parts, ignore_index=True)


def row_for(X, w, j):
    A = X.T @ (w[:, None] * X)
    return np.linalg.solve(A, (X * w[:, None]).T)[j]


def kmat(cr, hem, form):
    lag = np.abs(cr[:, None] - cr[None, :]).astype(float)
    same = hem[:, None] == hem[None, :]
    return (0.5 ** lag if form == "ar1_05" else np.maximum(0.0, 1.0 - lag / 20.0)) * same


def design_cols(cyc, hem, M, scale):
    cols = {}
    for c in sorted(set(cyc)):
        for h in ("N", "S"):
            v = ((cyc == c) & (hem == h)) * scale
            if v.any():
                cols[f"I{c}{h}"] = v
    for h in ("N", "S"):
        v = M * ((cyc == 24) & (hem == h)) * scale
        if v.any():
            cols[f"M{h}"] = v
    return cols


def t5(R, alo=None, ahi=None):
    R = R[np.isfinite(R.d_star)]
    R = R[R.groupby(["CR", "hem"]).phi.transform("size") >= 3].copy()
    key = list(zip(R.CR, R.hem))
    R["cell"] = pd.factorize(pd.Series(key))[0]
    g = R.groupby("cell")
    W = g.phi.sum().to_numpy()
    abar = g.A.mean().to_numpy()
    cyc = R.groupby(["cell", "cyc"]).phi.sum().unstack().idxmax(axis=1).to_numpy().astype(int)
    hem = g.hem.first().to_numpy()
    cr = g.CR.first().to_numpy()
    M = g.M.first().to_numpy()
    if alo is None:
        alo, ahi = np.quantile(abar[R.cell.to_numpy()], [0.05, 0.95])
    cols = design_cols(cyc, hem, M, 1.0)
    cols["x"] = abar - 1
    X = np.column_stack(list(cols.values()))
    gr = row_for(X, W, X.shape[1] - 1)
    delta = 0.2 * np.clip((abar[R.cell.to_numpy()] - alo) / (ahi - alo), 0, 1)
    gam = R.gamma.to_numpy()
    lat = R.lat.to_numpy()
    gnew = gam - delta * G0 * np.sin(np.radians(np.abs(lat)))
    dd = R.hale * CPROXY * R.phi * np.cos(np.radians(lat)) * (R.d_cm / R_CM) * (np.sin(np.radians(gnew)) - np.sin(np.radians(gam)))
    deta = np.bincount(R.cell, weights=dd.to_numpy()) / W
    agg = R.phi.to_numpy() / W[R.cell.to_numpy()]
    vc = np.bincount(R.cell, weights=agg ** 2 * ETA ** 2)
    out = dict(target=float(gr @ deta), alo=alo, ahi=ahi)
    for form in ("ar1_05", "steps20"):
        out[form] = math.sqrt((0.5 * ETA) ** 2 * gr @ kmat(cr, hem, form) @ gr + np.sum(gr ** 2 * vc))
    return out


def t3(R, alo, ahi):
    R = R.copy()
    R["cell"] = pd.factorize(pd.Series(list(zip(R.CR, R.hem))))[0]
    s = R.s.to_numpy()
    cols = design_cols(R.cyc.to_numpy(), R.hem.to_numpy(), R.M.to_numpy(), s)
    cols["x"] = (R.A.to_numpy() - 1) * s
    X = np.column_stack(list(cols.values()))
    a = row_for(X, R.phi.to_numpy(), X.shape[1] - 1)
    abar = R.groupby("cell").A.transform("mean").to_numpy()
    dg = -0.2 * np.clip((abar - alo) / (ahi - alo), 0, 1) * G0 * s
    b = np.bincount(R.cell, weights=a)
    g = R.groupby("cell")
    cr, hem = g.CR.first().to_numpy(), g.hem.first().to_numpy()
    out = dict(target=float(a @ dg))
    for form in ("ar1_05", "steps20"):
        out[form] = math.sqrt(SDX ** 2 * b @ kmat(cr, hem, form) @ b + SDE ** 2 * np.sum(a ** 2))
    return out


def main():
    if OUT.exists():
        sys.exit("refusing to overwrite the recount")
    R0, act = records_s()
    raw = pd.read_csv(D / "RAW.csv.gz")
    slots = pd.read_csv(D / "SLOTS.csv.gz")
    base5 = t5(R0)
    alo, ahi = base5["alo"], base5["ahi"]
    jobs = [("E0", np.nan, 0, R0)]
    for ext in ("E1", "E2", "E3"):
        for r in range(20):
            sl = slots[(slots.ext == ext) & (slots.f == 1.0) & (slots.r == r)]
            jobs.append((ext, 1.0, r, build(R0, sl, act)))
    recs = []
    for ext, f, r, R in jobs:
        res = {"T5": t5(R, alo, ahi), "T3": t3(R, alo, ahi)}
        for test, fam in (("T5", "F5"), ("T3", "A")):
            for n, form in ((1, "ar1_05"), (7, "steps20")):
                sel = (raw.ext == ext) & (raw.r == r) & (raw.test == test) & (raw.family == fam) & (raw.model == "a") \
                    & (raw.noise == n) & (raw.k == 1.0)
                sel &= raw.f.isna() if ext == "E0" else (raw.f == f)
                x = raw[sel]
                if len(x) != 1:
                    sys.exit(f"RAW row not unique: {ext} {r} {test} {n} ({len(x)})")
                x = x.iloc[0]
                recs.append(dict(ext=ext, r=r, test=test, form=form, n_records=len(R), target_raw=x.target_020,
                                 target_recount=res[test]["target"], se_raw=x.se, se_recount=res[test][form],
                                 rel_target=abs(res[test]["target"] / x.target_020 - 1),
                                 rel_se=abs(res[test][form] / x.se - 1), n_records_raw=x.n_records))
    df = pd.DataFrame(recs)
    worst_t, worst_s = df.rel_target.max(), df.rel_se.max()
    passed = bool(worst_t <= 1e-8 and worst_s <= 1e-8)
    OUT.mkdir(parents=True)
    df.to_csv(OUT / "RECOUNT.csv", index=False)
    rec = dict(passed=passed, designs=len(jobs), rows=len(df), max_rel_target=worst_t, max_rel_se=worst_s, tol=1e-8,
               A_lo=alo, A_hi=ahi, scope="model (a), k = 1, f = 1, AR(1) 0.5 and steps20 at the P2f scale",
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               raw_sha256=hashlib.sha256((D / "RAW.csv.gz").read_bytes()).hexdigest(),
               slots_sha256=hashlib.sha256((D / "SLOTS.csv.gz").read_bytes()).hexdigest())
    (OUT / "RECEIPT.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(rec, indent=1))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
