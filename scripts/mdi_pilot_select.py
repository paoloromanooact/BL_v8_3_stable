"""MDI pilot, phase 2: eligible population and stratified sample (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md
§2-3). Metadata only: DPD groups (same reader, corrections and isolation as the MWO catalogue), A_main with the MWO
DESIGN code, keys (NOAA, day) of the verified MWO release. No tilt is read, no MDI data is touched.

Population: DPD groups 1996-05-01 -> 2010-10-31, corrected area >= 1, |lat| <= 45 deg, with at least one isolated
day; chosen day = isolated day with minimum |LCM|, ties -> earliest UTC day. Classes on the population: terciles of
A_main and of the DPD area (linear NumPy quantiles, searchsorted right + 1). Cohorts: M1 = MWO isolated record on the
chosen day; U = the others (labels M2 = group in MWO on another day, M0 = absent). Cells: activity 1->3, hemisphere
N->S, area 1->3; within a cell M1 then U; units sorted by (numeric NOAA, NOAA, day). One default_rng(71 000 001),
one permutation per cell x cohort in that order; level 1 = first n1 (15/15), level 2 = first n2 of the same
permutation (3 for M1, 2 for U). pi1 = n1/N, pi2 = n2/N; no transfer, no replacement.

    .venv/bin/python scripts/mdi_pilot_select.py --selftest
    .venv/bin/python scripts/mdi_pilot_select.py --run        # after the code review
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
OUT = ROOT / "results/MDI_PILOT_SELECTION"
START, END = pd.Timestamp("1996-05-01"), pd.Timestamp("2010-10-31")
SEED = 71_000_001
N1 = {"M1": 15, "U": 15}
N2 = {"M1": 3, "U": 2}
COHORTS = ("M1", "U")


def load_cat():
    spec = importlib.util.spec_from_file_location("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["t3_mwo_catalogue"] = m
    spec.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def noaa_key(s):
    num = pd.to_numeric(pd.Series(s).str.extract(r"^(\d+)")[0], errors="coerce").fillna(-1).astype(int)
    return num.to_numpy()


# ---------------------------------------------------------------- population (pure functions)

def chosen_days(g):
    """g: DPD rows with isolation, already restricted to the period, area and latitude. One row per group: the isolated
    day with minimum |LCM|, ties -> earliest day."""
    iso = g[g.isolated].assign(abs_lcm=lambda x: x.lcm.abs())
    iso = iso.sort_values(["noaa", "abs_lcm", "day"], kind="stable")
    return iso.groupby("noaa", sort=False).head(1).reset_index(drop=True)


def tercile_edges(x):
    return np.quantile(np.asarray(x, float), [1 / 3, 2 / 3])


def tercile_class(x, edges):
    return np.searchsorted(edges, np.asarray(x, float), side="right") + 1


def add_classes(pop, mwo_keys, mwo_noaa):
    pop = pop.copy()
    pop["hemisphere"] = np.where(pop.lat >= 0, "N", "S")
    e_act, e_area = tercile_edges(pop.A_main), tercile_edges(pop.area)
    pop["act_class"] = tercile_class(pop.A_main, e_act)
    pop["area_class"] = tercile_class(pop.area, e_area)
    m1 = np.array([(n, d) in mwo_keys for n, d in zip(pop.noaa, pop.day)])
    m2 = ~m1 & pop.noaa.isin(mwo_noaa).to_numpy()
    pop["cohort"] = np.where(m1, "M1", "U")
    pop["mwo_label"] = np.where(m1, "M1", np.where(m2, "M2", "M0"))
    return pop, dict(A_main=[float(v) for v in e_act], area=[float(v) for v in e_area])


def cells():
    return [(a, h, s) for a in (1, 2, 3) for h in ("N", "S") for s in (1, 2, 3)]


def draw(pop, seed=SEED, n1=N1, n2=N2):
    """Returns (sample, cells_table). pop must have act_class, hemisphere, area_class, cohort, noaa, day."""
    rng = np.random.default_rng(seed)
    pop = pop.assign(_k=noaa_key(pop.noaa)).sort_values(["_k", "noaa", "day"], kind="stable")
    rows, ctab = [], []
    for a, h, s in cells():
        for c in COHORTS:
            u = pop[(pop.act_class == a) & (pop.hemisphere == h) & (pop.area_class == s) & (pop.cohort == c)]
            N = len(u)
            perm = rng.permutation(N)
            k1, k2 = min(n1[c], N), min(n2[c], min(n1[c], N))
            for rank, i in enumerate(perm[:k1]):
                r = u.iloc[i]
                rows.append(dict(noaa=r.noaa, day=r.day, act_class=a, hemisphere=h, area_class=s, cohort=c,
                                 mwo_label=r.mwo_label, perm_rank=rank, level2=rank < k2,
                                 pi1=k1 / N, pi2=(k2 / N) if rank < k2 else np.nan,
                                 w1=N / k1, w2=(N / k2) if rank < k2 else np.nan))
            ctab.append(dict(act_class=a, hemisphere=h, area_class=s, cohort=c, N=N, n1=k1, n2=k2,
                             shortfall1=n1[c] - k1, shortfall2=n2[c] - k2,
                             pi1=(k1 / N) if N else np.nan, pi2=(k2 / N) if N else np.nan))
    samp = pd.DataFrame(rows).merge(pop.drop(columns="_k"), on=["noaa", "day", "act_class", "hemisphere", "area_class",
                                                                  "cohort", "mwo_label"], how="left", validate="one_to_one")
    return samp, pd.DataFrame(ctab)


# ---------------------------------------------------------------- real population

def population(cat=None, release=RELEASE):
    cat = cat or load_cat()
    allg = cat.dpd_groups()                                     # 1974-2012, as the MWO catalogue
    acts = cat.activity_tables(allg)["A_main"]                  # MWO DESIGN code, normalised over 1974-2012
    g = cat.add_isolation(allg)
    d = pd.to_datetime(g.day)
    g = g[(d >= START) & (d <= END) & (g.area >= cat.MIN_AREA) & (g.lat.abs() <= cat.MAX_ABS_LAT)]
    pop = chosen_days(g)
    hem = np.where(pop.lat >= 0, "N", "S")
    per = pd.PeriodIndex(pop.day.str[:7], freq="M")
    pop["A_main"] = [float(acts.at[p, h]) if p in acts.index else np.nan for p, h in zip(per, hem)]
    if pop.A_main.isna().any():
        raise ValueError("A_main missing for some groups")
    rel = pd.read_csv(release, dtype={"noaa": str}, usecols=["noaa", "day_utc"])
    return add_classes(pop, set(zip(rel.noaa, rel.day_utc)), set(rel.noaa))


def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True,
                      text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    cat = load_cat()
    (pop, edges) = population(cat)
    samp, ctab = draw(pop)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        cols = ["noaa", "day", "t_dpd", "lat", "lon", "lcm", "area", "A_main", "hemisphere", "act_class", "area_class",
                "cohort", "mwo_label"]
        pop[cols].to_csv(tmp / "POPULATION.csv", index=False)
        samp[["noaa", "day", "t_dpd", "lat", "lon", "lcm", "area", "A_main", "act_class", "hemisphere", "area_class",
              "cohort", "mwo_label", "perm_rank", "level2", "pi1", "pi2", "w1", "w2"]].to_csv(tmp / "SAMPLE.csv", index=False)
        ctab.to_csv(tmp / "CELLS.csv", index=False)
        dpd = sorted(Path(cat.DPD_DIR).glob("gDPD*.txt")) + sorted(Path(cat.DPD_DIR).glob("dailyDPD*.txt"))
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), seed=SEED, n1=N1, n2=N2, edges=edges,
                    period=[str(START.date()), str(END.date())], population=len(pop), level1=int(len(samp)),
                    level2=int(samp.level2.sum()), mwo_release_sha256=sha(RELEASE),
                    dpd_sha256={p.name: sha(p) for p in dpd},
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                    tilts_read=False, mdi_data_read=False)
        meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps({k: meta[k] for k in ("population", "level1", "level2", "edges")}, indent=1))
    return 0


# ---------------------------------------------------------------- selftest (synthetic only)

def synthetic_population(n=3000, seed=5):
    rng = np.random.default_rng(seed)
    days = pd.date_range("1999-01-01", periods=n, freq="D").strftime("%Y-%m-%d")
    pop = pd.DataFrame(dict(noaa=[str(8000 + i) for i in range(n)], day=days, t_dpd=days, lat=rng.uniform(-40, 40, n),
                            lon=rng.uniform(0, 360, n), lcm=rng.uniform(-30, 30, n), area=rng.integers(1, 600, n),
                            A_main=np.round(rng.uniform(0.2, 3.0, n), 1)))
    keys = {(pop.noaa[i], pop.day[i]) for i in range(0, n, 7)}
    other = set(pop.noaa[3::11])
    return add_classes(pop, keys, other | {k[0] for k in keys})


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    g = pd.DataFrame(dict(noaa=["1", "1", "1", "2", "2"], day=["2000-01-01", "2000-01-02", "2000-01-03", "2000-01-01", "2000-01-02"],
                          lcm=[-5.0, 2.0, -2.0, 10.0, 1.0], isolated=[True, True, True, True, False]))
    ch = chosen_days(g)
    ok("chosen day: minimum |LCM| among isolated days, ties -> earliest; non-isolated days ignored",
       dict(zip(ch.noaa, ch.day)) == {"1": "2000-01-02", "2": "2000-01-01"})
    x = np.array([1, 1, 1, 1, 2, 2, 3, 3, 3.0])
    c = tercile_class(x, tercile_edges(x))
    ok("terciles: equal values never split", all(len(set(c[x == v])) == 1 for v in set(x)))
    (pop, edges) = synthetic_population()
    s1, t1 = draw(pop)
    s2, t2 = draw(pop)
    ok("draw reproducible from the seed", s1[["noaa", "day"]].equals(s2[["noaa", "day"]]))
    ok("18 cells x 2 cohorts in the declared order", len(t1) == 36 and list(t1.cohort[:2]) == ["M1", "U"]
       and list(zip(t1.act_class, t1.hemisphere, t1.area_class))[::2] == cells())
    good = True
    for _, r in t1.iterrows():
        sel = s1[(s1.act_class == r.act_class) & (s1.hemisphere == r.hemisphere) & (s1.area_class == r.area_class) & (s1.cohort == r.cohort)]
        good &= len(sel) == r.n1 == min(N1[r.cohort], r.N) and int(sel.level2.sum()) == r.n2 == min(N2[r.cohort], r.n1)
        if len(sel):
            good &= np.allclose(sel.pi1, r.n1 / r.N) and np.allclose(sel[sel.level2].pi2, r.n2 / r.N)
    ok("per cell x cohort: n1 = min(target, N), n2 = min(target, n1), pi1 = n1/N, pi2 = n2/N", good)
    ok("level 2 is the head of the level-1 permutation (independent of any level-1 outcome)",
       (s1[s1.level2].perm_rank < s1[s1.level2].apply(lambda r: N2[r.cohort], axis=1)).all()
       and (s1[~s1.level2].perm_rank >= s1[~s1.level2].apply(lambda r: N2[r.cohort], axis=1)).all())
    ok("no duplicates, sampled units belong to their cell and cohort", not s1.duplicated(["noaa", "day"]).any()
       and (s1.cohort == np.where(s1.mwo_label == "M1", "M1", "U")).all())
    small = pop[~((pop.act_class == 1) & (pop.hemisphere == "N") & (pop.area_class == 1) & (pop.cohort == "M1"))]
    small = pd.concat([small, pop[(pop.act_class == 1) & (pop.hemisphere == "N") & (pop.area_class == 1) & (pop.cohort == "M1")].head(2)])
    s3, t3 = draw(small)
    r = t3[(t3.act_class == 1) & (t3.hemisphere == "N") & (t3.area_class == 1) & (t3.cohort == "M1")].iloc[0]
    ok("shortfall: N < target takes all, declared, no transfer", r.N == 2 and r.n1 == 2 and r.shortfall1 == 13 and r.n2 == 2
       and len(s3) == len(s1) - 13)
    empty = pop[~((pop.act_class == 3) & (pop.hemisphere == "S") & (pop.area_class == 3) & (pop.cohort == "U"))]
    s4, t4 = draw(empty)
    r = t4[(t4.act_class == 3) & (t4.hemisphere == "S") & (t4.area_class == 3) & (t4.cohort == "U")].iloc[0]
    ok("empty cohort: N = 0, n = 0, probability undefined", r.N == 0 and r.n1 == 0 and np.isnan(r.pi1))
    spec = importlib.util.spec_from_file_location("an", ROOT / "scripts/t3_mwo_analysis.py")
    an = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(an)
    ok("seed 71 000 001 not in the MWO grid, USED, S1, Joy, S2 diagnosis", SEED not in set(an.grid_seeds())
       and not any(lo <= SEED < hi for lo, hi in an.USED) and SEED not in (an.SEED_S1, 69_500_001, 69_600_001))
    src = Path(__file__).read_text().split("def selftest")[0]
    ok("no tilt column read from the release (keys only)", 'usecols=["noaa", "day_utc"]' in src and "tilt_deg" not in src)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
