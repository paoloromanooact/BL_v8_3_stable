"""Analytic precision of a T3-like slope on the Debrecen DPD design (no tilt read), as in prospective phase A (A1).

Choices fixed in docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md §7 before running. Inputs: gDPD<year>.txt and
dailyDPD1974_2016.txt in data/sharp/external_DPD_20261118 (SHA256SUMS.txt). Output: results/T3_DPD_FEASIBILITY/.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/t3_dpd_feasibility.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/t3_dpd_feasibility.py --run
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import diag_t5_oracle as D, p2d  # noqa: E402

_spec = importlib.util.spec_from_file_location("prospective_phase_a", ROOT / "scripts/prospective_phase_a.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

DATA = ROOT / "data/sharp/external_DPD_20261118"
OUT = ROOT / "results/T3_DPD_FEASIBILITY_R2"   # run 1 (results/T3_DPD_FEASIBILITY) put 1974-1976-02 in cycle 21
NOTE = ROOT / "docs/T3_LONG_CATALOGUE_FEASIBILITY_DRAFT.md"
MINIMA = [(21, "1976-03-01"), (22, "1986-09-01"), (23, "1996-08-01"), (24, "2008-12-01")]
GAMMA0, SD_X, Z = 24.0, 7.5, A.Z
LCM_MAX, LAT_MAX, AREA_SENS = 60.0, 45.0, 50


def read_groups():
    rows = []
    for y in range(1974, 2017):
        for line in (DATA / f"gDPD{y}.txt").read_text().splitlines():
            if not line.startswith("g "):
                continue
            try:
                lat, lcm = float(line[59:65]), float(line[73:79])
            except ValueError:
                continue
            if lat > 900 or lcm > 900:          # intermittent phase (999999)
                continue
            rows.append(dict(date=f"{line[2:6]}-{line[7:9]}-{line[10:12]}", noaa=line[22:28].strip(),
                             area=int(line[53:58]), lat=lat, lcm=lcm))
    g = pd.DataFrame(rows)
    g["date"] = pd.to_datetime(g["date"])
    return g


def activity(g):
    """Monthly mean over observation days of the daily hemispheric sum of corrected WS area, normalised to 1974-2016."""
    days = sorted({pd.Timestamp(f"{l[2:6]}-{l[7:9]}-{l[10:12]}") for l in (DATA / "dailyDPD1974_2016.txt").read_text().splitlines()
                   if l.startswith("d ")})
    g = g.assign(hem=np.where(g.lat >= 0, "N", "S"))
    daily = g.groupby(["date", "hem"]).area.sum().unstack(fill_value=0).reindex(days, fill_value=0)
    monthly = daily.groupby(daily.index.to_period("M")).mean()
    return monthly / monthly.mean()


def cr_of(dates):
    jd = dates.map(lambda t: t.to_julian_date()).to_numpy()
    c = np.floor((jd - 2398140.227) / 27.2752316).astype(int)
    starts = lambda x: A.cr_start(x).map(lambda t: t.to_julian_date()).to_numpy()  # noqa: E731
    for _ in range(3):
        c = np.where(starts(c) > jd, c - 1, c)
        c = np.where(starts(c + 1) <= jd, c + 1, c)
    return c


def cycle_of(dates):
    """Cycle of time: 20 before the 1976-03 minimum (fix after Codex's review: dates before 1976-03 were cycle 21)."""
    c = np.full(len(dates), 20)
    for k, m in MINIMA:
        c = np.where(dates >= pd.Timestamp(m), k, c)
    return c


def design(g, act, area_min=1, period=None):
    g = g[(g.area >= max(area_min, 1)) & (g.lcm.abs() <= LCM_MAX) & (g.lat.abs() <= LAT_MAX)].copy()
    g = g.loc[g.groupby("noaa").lcm.apply(lambda s: s.abs().idxmin())]
    if period:
        g = g[(g.date >= pd.Timestamp(period[0])) & (g.date < pd.Timestamp(period[1]))]
    g["hem"] = np.where(g.lat >= 0, "N", "S")
    g["CR"] = cr_of(g.date)
    g["cyc"] = cycle_of(g.date)
    per = g.date.dt.to_period("M")
    g["A"] = [act.at[p, h] for p, h in zip(per, g.hem)]
    g["s"] = np.sin(np.radians(g.lat.abs()))
    return g.reset_index(drop=True)


def precision(g):
    s, hem, cyc = g.s.to_numpy(), g.hem.to_numpy(), g.cyc.to_numpy()
    cols = A.ch_cols(cyc, hem, s)
    cols["x3"] = (g.A.to_numpy() - 1) * s
    w = g.area.to_numpy(float)
    X, names, _ = A._finish(cols, w, "x3")
    a = p2d.wls_row(X, w, names.index("x3"))
    codes, uniq = pd.factorize(pd.MultiIndex.from_arrays([g.CR.to_numpy(), hem]))
    abar = pd.Series(g.A.to_numpy()).groupby(codes).transform("mean").to_numpy()
    lo, hi = np.quantile(abar, [0.05, 0.95])
    dg = -0.2 * np.clip((abar - lo) / (hi - lo), 0, 1) * GAMMA0 * s
    target = float(a @ dg)
    b = np.bincount(codes, weights=a)
    cr = np.array([c for c, _ in uniq])
    hh = (np.array([h for _, h in uniq]) == "S").astype(int)
    out = []
    for sd_e in (15.0, 25.0):
        for form, scen, xs in A.NOISE:
            var = (SD_X * xs) ** 2 * float(b @ D.k_true(cr - cr.min(), hh, scen) @ b) + sd_e ** 2 * float(np.sum(a ** 2))
            se = math.sqrt(var)
            out.append(dict(sd_e=sd_e, form=form, x_scale=xs, se=se, target=target, se_over_target=se / abs(target),
                            recognition=float(norm.cdf(-Z - target / se)), halfwidth_deg=Z * se,
                            halfwidth_gamma0=Z * se / GAMMA0))
    return out, dict(n_records=len(g), n_cells=len(uniq), n_cr=int(len(set(cr))), A_lo=lo, A_hi=hi)


def selftest():
    g = read_groups()
    ok1 = len(g) > 50000 and g.lat.abs().max() <= 90
    act = activity(g)
    ok2 = abs(act.mean().mean() - 1) < 1e-12 and act.index.min().year == 1974 and act.index.max().year == 2016
    d = design(g, act)
    crs = d.CR.to_numpy()
    st = A.cr_start(crs)
    ok3 = bool(((d.date >= st.normalize()) & (d.date < A.cr_start(crs + 1) + pd.Timedelta(days=1))).all())
    ok4 = d.noaa.is_unique and set(d.cyc) <= {20, 21, 22, 23, 24} and (d[d.date < '1976-03-01'].cyc == 20).all() and (d[(d.date >= '1976-03-01') & (d.date < '1986-09-01')].cyc == 21).all()
    for n, c in (("group rows parsed", ok1), ("activity normalised, 1974-2016", ok2), ("record dates in their CR", ok3),
                 ("one record per group, cycles 20-24, 1974-1976-02 in cycle 20", ok4)):
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    return ok1 and ok2 and ok3 and ok4


def run():
    if OUT.exists():
        sys.exit("refusing to overwrite")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                      text=True).stdout.strip():
        sys.exit("clean tree required")
    if not selftest():
        return 1
    g = read_groups()
    act = activity(g)
    rows, info = [], []
    for label, kw in (("DPD all", {}), ("DPD area>=50", dict(area_min=AREA_SENS)),
                      ("DPD 1974-1996", dict(period=("1974-01-01", "1996-08-01"))),
                      ("DPD 1996-2016", dict(period=("1996-08-01", "2017-01-01")))):
        dz = design(g, act, **kw)
        r, i = precision(dz)
        rows += [dict(design=label, **x) for x in r]
        info.append(dict(design=label, **i))
    raw = pd.read_csv(ROOT / "results/PROSPECTIVE_PHASE_A/RAW.csv.gz")
    e0 = raw[(raw.ext == "E0") & (raw.test == "T3") & (raw.family == "A") & (raw.model == "a")]
    for x in e0.itertuples():
        rows.append(dict(design="HMI E0 (phase A)", sd_e=15.0, form=x.form, x_scale=x.x_scale, se=x.se, target=x.target_020,
                         se_over_target=x.se / abs(x.target_020), recognition=float(norm.cdf(-Z - x.target_020 / x.se)),
                         halfwidth_deg=Z * x.se, halfwidth_gamma0=Z * x.se / GAMMA0))
    OUT.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(OUT / "PRECISION.csv", index=False)
    pd.DataFrame(info).to_csv(OUT / "DESIGNS.csv", index=False)
    meta = dict(note_sha256=hashlib.sha256(NOTE.read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                data_sha256=hashlib.sha256((DATA / "SHA256SUMS.txt").read_bytes()).hexdigest(),
                git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(pd.DataFrame(info).to_string(index=False))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) else (run() if a.run else 1))
