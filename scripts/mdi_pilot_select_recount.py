"""Independent recount of the MDI pilot selection (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §2-3).

Own code for: the gDPD reader (fixed columns, seconds = 60 as an interval, duplicates keep the largest area),
isolation, the period/area/latitude filters, the chosen day, A_main (monthly mean over observed DPD days of the daily
hemispheric area, normalised per hemisphere over 1974-2012), tercile classes, MWO cohorts from the release keys, and
the stratified draw replayed with the same generator. Compares POPULATION, SAMPLE, CELLS and META; strict receipt.

    .venv/bin/python scripts/mdi_pilot_select_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_select_recount.py --check
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "results/MDI_PILOT_SELECTION"
REC = ROOT / "results/MDI_PILOT_SELECTION_RECOUNT"
DPD = ROOT / "data/sharp/external_DPD_20261118"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
SEED, N1, N2 = 71_000_001, {"M1": 15, "U": 15}, {"M1": 3, "U": 2}
PRODUCTS = {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read_gdpd(dpd=DPD, years=range(1974, 2013)):
    rows = []
    for y in years:
        for ln in (Path(dpd) / f"gDPD{y}.txt").read_text().splitlines():
            if ln[:2] != "g ":
                continue
            try:
                t0 = datetime(int(ln[2:6]), int(ln[7:9]), int(ln[10:12]), int(ln[13:15]), int(ln[16:18]))
                t = t0 + timedelta(seconds=int(ln[19:21]))
                la, lo, lc, ar = float(ln[59:65]), float(ln[66:72]), float(ln[73:79]), int(ln[53:58])
            except ValueError:
                continue
            if max(la, lo, lc) > 900:
                continue
            rows.append((t.strftime("%Y-%m-%d"), t, ln[22:28].strip(), ar, la, lo, lc))
    g = pd.DataFrame(rows, columns=["day", "t_dpd", "noaa", "area", "lat", "lon", "lcm"])
    g = g.sort_values(["day", "noaa", "area"], ascending=[True, True, False], kind="mergesort")
    return g.drop_duplicates(["day", "noaa"], keep="first").reset_index(drop=True)


def isolation(g, dlat=6.0, dlon=8.0):
    iso = np.zeros(len(g), bool)
    for day, idx in g.groupby("day").indices.items():
        la, lo = g.lat.to_numpy()[idx], g.lon.to_numpy()[idx]
        dl = np.abs((lo[:, None] - lo[None, :] + 180.0) % 360.0 - 180.0)
        n = ((np.abs(la[:, None] - la[None, :]) <= dlat) & (dl <= dlon)).sum(1) - 1
        iso[idx] = n == 0
    return iso


def observed_days(dpd=DPD):
    out = set()
    for ln in (Path(dpd) / "dailyDPD1974_2016.txt").read_text().splitlines():
        t = ln.split()
        if ln.startswith("d ") and len(t) >= 12:
            out.add(f"{t[1]}-{t[2]}-{t[3]}")
    return out


def a_main(g, days):
    days = sorted(d for d in days if "1974-01-01" <= d < "2013-01-01")
    x = g[g.day.isin(days)].assign(h=np.where(g.lat >= 0, "N", "S")[g.day.isin(days).to_numpy()])
    daily = x.pivot_table(index="day", columns="h", values="area", aggfunc="sum").reindex(index=days, columns=["N", "S"]).fillna(0.0)
    month = daily.groupby(pd.PeriodIndex(daily.index, freq="M")).mean()
    return month / month.mean()


def own_population(dpd=DPD, release=RELEASE):
    g = read_gdpd(dpd)
    act = a_main(g, observed_days(dpd))
    g = g.assign(isolated=isolation(g))
    p = g[(g.day >= "1996-05-01") & (g.day <= "2010-10-31") & (g.area >= 1) & (g.lat.abs() <= 45.0) & g.isolated].copy()
    p["abs_lcm"] = p.lcm.abs()
    p = p.sort_values(["noaa", "abs_lcm", "day"], kind="mergesort").groupby("noaa", sort=False).head(1)
    p["hemisphere"] = np.where(p.lat >= 0, "N", "S")
    p["A_main"] = [act.at[pd.Period(d[:7], "M"), h] for d, h in zip(p.day, p.hemisphere)]
    rel = pd.read_csv(release, dtype={"noaa": str}, usecols=["noaa", "day_utc"])
    keys, names = set(zip(rel.noaa, rel.day_utc)), set(rel.noaa)
    for col, src in (("act_class", "A_main"), ("area_class", "area")):
        q = np.quantile(p[src].to_numpy(float), [1 / 3, 2 / 3])
        v = p[src].to_numpy(float)
        p[col] = np.where(v < q[0], 1, np.where(v < q[1], 2, 3))
    m1 = np.array([(n, d) in keys for n, d in zip(p.noaa, p.day)])
    p["cohort"] = np.where(m1, "M1", "U")
    p["mwo_label"] = np.where(m1, "M1", np.where(p.noaa.isin(names), "M2", "M0"))
    return p.reset_index(drop=True)


def own_draw(p):
    num = pd.to_numeric(p.noaa.str.extract(r"^(\d+)")[0], errors="coerce").fillna(-1).astype(int)
    p = p.assign(_n=num.to_numpy()).sort_values(["_n", "noaa", "day"], kind="mergesort")
    rng = np.random.default_rng(SEED)
    sample, cells = [], []
    for a in (1, 2, 3):
        for h in ("N", "S"):
            for s in (1, 2, 3):
                for c in ("M1", "U"):
                    u = p[(p.act_class == a) & (p.hemisphere == h) & (p.area_class == s) & (p.cohort == c)]
                    perm = rng.permutation(len(u))
                    k1 = min(N1[c], len(u))
                    k2 = min(N2[c], k1)
                    for j, i in enumerate(perm[:k1]):
                        sample.append((u.noaa.iloc[i], u.day.iloc[i], a, h, s, c, j, j < k2))
                    cells.append((a, h, s, c, len(u), k1, k2))
    return (pd.DataFrame(sample, columns=["noaa", "day", "act_class", "hemisphere", "area_class", "cohort", "perm_rank", "level2"]),
            pd.DataFrame(cells, columns=["act_class", "hemisphere", "area_class", "cohort", "N", "n1", "n2"]))


PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
SAMPLE_COLS = ["noaa", "day", "t_dpd", "lat", "lon", "lcm", "area", "A_main", "act_class", "hemisphere", "area_class",
               "cohort", "mwo_label", "perm_rank", "level2", "pi1", "pi2", "w1", "w2"]
POP_COLS = ["noaa", "day", "t_dpd", "lat", "lon", "lcm", "area", "A_main", "hemisphere", "act_class", "area_class",
            "cohort", "mwo_label"]
CELL_COLS = ["act_class", "hemisphere", "area_class", "cohort", "N", "n1", "n2", "shortfall1", "shortfall2", "pi1", "pi2"]


def own_full(pop_own):
    """Own sample and cells with every column of the products."""
    s_own, c_own = own_draw(pop_own)
    c_own["shortfall1"] = [N1[c] - k for c, k in zip(c_own.cohort, c_own.n1)]
    c_own["shortfall2"] = [N2[c] - k for c, k in zip(c_own.cohort, c_own.n2)]
    c_own["pi1"] = np.where(c_own.N > 0, c_own.n1 / c_own.N.where(c_own.N > 0, 1), np.nan)
    c_own["pi2"] = np.where(c_own.N > 0, c_own.n2 / c_own.N.where(c_own.N > 0, 1), np.nan)
    m = s_own.merge(pop_own[POP_COLS], on=["noaa", "day", "act_class", "hemisphere", "area_class", "cohort"], how="left",
                    validate="one_to_one")
    m = m.merge(c_own[["act_class", "hemisphere", "area_class", "cohort", "N", "n1", "n2"]],
                on=["act_class", "hemisphere", "area_class", "cohort"], how="left", validate="many_to_one")
    m["pi1"] = m.n1 / m.N
    m["pi2"] = np.where(m.level2, m.n2 / m.N, np.nan)
    m["w1"] = 1.0 / m.pi1
    m["w2"] = np.where(m.level2, 1.0 / m.pi2, np.nan)
    return m[SAMPLE_COLS], c_own[CELL_COLS]


def same_frame(a, b, cols, keys):
    """Column-by-column equality with NaN = NaN; times compared as timestamps; exact key coverage and uniqueness."""
    if list(a.columns[: len(cols)]) != cols and not set(cols) <= set(a.columns):
        return False, "columns"
    if a.duplicated(keys).any() or b.duplicated(keys).any():
        return False, "duplicate keys"
    if len(a) != len(b) or not (a[keys].astype(str).to_numpy() == b[keys].astype(str).to_numpy()).all():
        return False, "keys or order"
    for c in cols:
        x, y = a[c], b[c]
        if c == "t_dpd":
            if not (pd.to_datetime(x.astype(str), format="ISO8601").to_numpy() == pd.to_datetime(y.astype(str), format="ISO8601").to_numpy()).all():
                return False, c
        elif pd.api.types.is_numeric_dtype(y) and c not in ("level2",):
            xv, yv = pd.to_numeric(x, errors="coerce").to_numpy(float), y.to_numpy(float)
            if not np.allclose(xv, yv, rtol=1e-12, atol=0, equal_nan=True):
                return False, c
        elif not (x.astype(str).str.replace("^nan$", "", regex=True).to_numpy() == y.astype(str).str.replace("^nan$", "", regex=True).to_numpy()).all():
            return False, c
    return True, ""


def check(sel=SEL, write=True, rec=REC, pop_own=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:160]}")

    meta = json.loads((Path(sel) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("products match META (exact set, actual hashes before reading)", set(ps) == PRODUCTS and all(sha(Path(sel) / n) == h for n, h in ps.items()))
    real = pop_own is None
    if real:
        fr = json.loads(FREEZE.read_text())
        ok("frozen protocol unchanged and equal to the one of the selection", sha(PROTOCOL) == fr["sha256"] == meta.get("protocol_sha256"))
        ok("DPD files and MWO release unchanged since the selection", all(sha(DPD / n) == h for n, h in meta["dpd_sha256"].items())
           and meta["mwo_release_sha256"] == sha(RELEASE))
        pop_own = own_population()
    pop = pd.read_csv(Path(sel) / "POPULATION.csv", dtype={"noaa": str}, float_precision="round_trip")
    samp = pd.read_csv(Path(sel) / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    cells = pd.read_csv(Path(sel) / "CELLS.csv")
    po = pop_own.assign(_k=pd.to_numeric(pop_own.noaa.str.extract(r"^(\d+)")[0], errors="coerce").fillna(-1)).sort_values(["_k", "noaa", "day"])
    pa = pop.assign(_k=pd.to_numeric(pop.noaa.str.extract(r"^(\d+)")[0], errors="coerce").fillna(-1)).sort_values(["_k", "noaa", "day"])
    g, why = same_frame(pa.reset_index(drop=True), po[POP_COLS].reset_index(drop=True), POP_COLS, ["noaa", "day"])
    ok("population: every column (positions, t_DPD, LCM, area, A_main, classes, cohorts, labels)", g, why)
    s_own, c_own = own_full(pop_own)
    g, why = same_frame(samp.reset_index(drop=True), s_own.reset_index(drop=True), SAMPLE_COLS, ["noaa", "day"])
    ok("sample: every column, replayed draw, probabilities and weights (NaN where undefined)", g, why)
    g, why = same_frame(cells.reset_index(drop=True), c_own.reset_index(drop=True), CELL_COLS, ["act_class", "hemisphere", "area_class", "cohort"])
    ok("cells: labels, N, n1, n2, shortfalls and probabilities", g, why)
    passed = sum(c["ok"] for c in checks)
    receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, selection_meta_sha256=sha(Path(sel) / "META.json"))
    if write:
        if not real:
            sys.exit("a receipt is written only on the real path")
        if Path(rec).exists():
            sys.exit("receipt exists")
        Path(rec).mkdir(parents=True)
        (Path(rec) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"recount: {passed}/{len(checks)} (partial {not real})")
    return passed == len(checks)


def selftest():
    import importlib.util
    import tempfile
    spec = importlib.util.spec_from_file_location("sel", ROOT / "scripts/mdi_pilot_select.py")
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    res = []

    def ok(name, cond):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name}")

    pop, edges = S.synthetic_population()
    samp, ctab = S.draw(pop)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "sel"
        d.mkdir()
        pop.to_csv(d / "POPULATION.csv", index=False)
        samp.to_csv(d / "SAMPLE.csv", index=False)
        ctab.to_csv(d / "CELLS.csv", index=False)
        (d / "META.json").write_text(json.dumps(dict(products_sha256={n: sha(d / n) for n in PRODUCTS})))
        ok("recount passes on a synthetic selection (own draw replay)", check(d, write=False, pop_own=pop))

        def mutate(name, fn, target="SAMPLE.csv"):
            t0 = pd.read_csv(d / target, dtype={"noaa": str}, float_precision="round_trip") if target != "CELLS.csv" else pd.read_csv(d / target)
            t1 = fn(t0.copy())
            t1.to_csv(d / target, index=False)
            (d / "META.json").write_text(json.dumps(dict(products_sha256={n: sha(d / n) for n in PRODUCTS})))
            ok(f"refused with updated hashes: {name}", not check(d, write=False, pop_own=pop))
            t0.to_csv(d / target, index=False)
            (d / "META.json").write_text(json.dumps(dict(products_sha256={n: sha(d / n) for n in PRODUCTS})))
        l2 = samp.index[samp.level2][0]
        mutate("lat of a level-2 row", lambda t: t.assign(lat=t.lat.where(t.index != l2, t.lat + 0.01)))
        mutate("lon of a level-2 row", lambda t: t.assign(lon=t.lon.where(t.index != l2, t.lon + 0.01)))
        mutate("t_dpd of a level-2 row", lambda t: t.assign(t_dpd=t.t_dpd.astype(str).where(t.index != l2, "1999-01-01 00:00:01")))
        mutate("A_main of a level-2 row", lambda t: t.assign(A_main=t.A_main.where(t.index != l2, t.A_main + 0.1)))
        mutate("w2 of a level-2 row", lambda t: t.assign(w2=t.w2.where(t.index != l2, t.w2 * 1.01)))
        mutate("a sampled unit", lambda t: t.assign(noaa=t.noaa.where(t.index != 0, "99999")))
        mutate("a duplicated sample row", lambda t: pd.concat([t, t.iloc[[0]]]))
        mutate("a cell label", lambda t: t.assign(hemisphere=t.hemisphere.where(t.index != 0, "S")), "CELLS.csv")
        mutate("a population LCM", lambda t: t.assign(lcm=t.lcm.where(t.index != 5, t.lcm + 1)), "POPULATION.csv")
    def line(y, mo, d, hh, mm, ss, noaa, area, lat, lon, lcm):
        b = [" "] * 80
        for (i, j), v in (((0, 2), "g "), ((2, 6), f"{y:4d}"), ((7, 9), f"{mo:02d}"), ((10, 12), f"{d:02d}"), ((13, 15), f"{hh:02d}"),
                          ((16, 18), f"{mm:02d}"), ((19, 21), f"{ss:02d}"), ((22, 28), f"{noaa:>6}"), ((53, 58), f"{area:5d}"),
                          ((59, 65), f"{lat:6.2f}"), ((66, 72), f"{lon:6.2f}"), ((73, 79), f"{lcm:6.2f}")):
            b[i:j] = list(v)
        return "".join(b)
    with tempfile.TemporaryDirectory() as td:
        lines = [line(2000, 1, 1, 10, 0, 60, "8001", 100, 15.0, 120.0, -3.0), line(2000, 1, 1, 10, 0, 0, "8001", 50, 15.0, 120.0, -3.0),
                 line(2000, 1, 2, 9, 30, 0, "8002", 7, -20.5, 999.0, 4.0), "d 2000 01 01 ignored"]
        for y in range(1974, 2013):
            (Path(td) / f"gDPD{y}.txt").write_text("\n".join(lines) + "\n" if y == 2000 else "")
        g = read_gdpd(td)
        ok("own gDPD reader: seconds = 60 as an interval, duplicates keep the largest area, invalid positions dropped",
           len(g) == 1 and g.area.iloc[0] == 100 and g.t_dpd.iloc[0] == datetime(2000, 1, 1, 10, 1, 0))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
