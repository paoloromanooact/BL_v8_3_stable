"""Q4 preparatory counts (non-blind preparation of revision 2 of docs/MDI_PILOT_Q4_NOTE_DRAFT.md).

Rules fixed before counting in docs/MDI_Q4_PREP_COUNTS_RULES.md (C1-C7); its SHA-256 is recorded in META.json.
Counts and checks on preserved pilot files only: no tilt column is read (L1/L2 records are read with an explicit
column list of identifiers, statuses, maps and rotations), no prospective precision, no simulation, no new data.

    .venv/bin/python scripts/mdi_q4_prep_counts.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs/MDI_Q4_PREP_COUNTS_RULES.md"
SEL = ROOT / "results/MDI_PILOT_SELECTION"
L1 = ROOT / "results/MDI_PILOT_L1/L1_RECORDS.csv"
L2 = ROOT / "results/MDI_PILOT_L2/L2_RECORDS.csv"
AN1 = ROOT / "results/MDI_PILOT_ANALYSIS_L1/Q1_YIELD_PROJECTED.csv"
AN2 = ROOT / "results/MDI_PILOT_ANALYSIS_L2/YIELD_A1.csv"
AUDIT = ROOT / "results/MDI_SYNOPTIC_AUDIT/FILES.csv"
OUT = ROOT / "results/MDI_Q4_PREP_COUNTS"
KEYS = ["act_class", "hemisphere", "area_class", "cohort"]
L1_COLS = ["noaa", "day", "N", "N_ephemeris", "maps", "status", "sens100_status"]     # no tilt column
L2_COLS = ["rule", "noaa", "day", "image", "status"]                                  # no tilt column
END_DATE = pd.Timestamp("2010-04-30")
CR_H = 2096
GAP = (pd.Timestamp("1998-06-01"), pd.Timestamp("1998-11-01"))
DLON = 8.0
N_MIN, FRAC_LT, K_NN, DLAT_MAX = 5, 0.90, 5, 5.0
TOL = 1e-12


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


A = _load("mdi_synoptic_adapter", "scripts/mdi_synoptic_adapter.py")
PA = _load("prospective_phase_a", "scripts/prospective_phase_a.py")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def required_maps(ct_g):
    return sorted({int(np.floor(c / 360.0)) + 1 for c in (ct_g - DLON, ct_g, ct_g + DLON)})


def cr_of_time(ts):
    """CR(t) = max{c : cr_start(c) <= t}, Meeus calendar of phase A."""
    c0 = int(np.floor((pd.Timestamp(ts) - pd.Timestamp("1853-11-09")).days / 27.2753)) + 1
    cands = np.arange(c0 - 3, c0 + 4)
    st = PA.cr_start(cands)
    return int(cands[np.asarray(st <= pd.Timestamp(ts))].max())


def kish(w):
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum()) if len(w) else 0.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((SEL / "META.json").read_text())
    pop = pd.read_csv(SEL / "POPULATION.csv")
    samp = pd.read_csv(SEL / "SAMPLE.csv")
    cells = pd.read_csv(SEL / "CELLS.csv")
    l1 = pd.read_csv(L1, usecols=L1_COLS, dtype={"maps": str})
    l2 = pd.read_csv(L2, usecols=L2_COLS)
    checks = []

    def check(name, cond, value=""):
        checks.append(dict(check=name, ok=bool(cond), value=str(value)))

    # ---------------------------------------------------------------- C1
    ea, es = np.array(meta["edges"]["A_main"]), np.array(meta["edges"]["area"])
    act = np.searchsorted(ea, pop.A_main.to_numpy(float), side="right") + 1
    ar = np.searchsorted(es, pop.area.to_numpy(float), side="right") + 1
    check("C1 act_class from META edges.A_main", (act != pop.act_class).sum() == 0, int((act != pop.act_class).sum()))
    check("C1 area_class from META edges.area", (ar != pop.area_class).sum() == 0, int((ar != pop.area_class).sum()))

    # ---------------------------------------------------------------- C2
    inv = set(pd.read_csv(AUDIT, usecols=["CAR_ROT"]).CAR_ROT.astype(int))
    missing = sorted(c for c in range(min(inv), max(inv) + 1) if c not in inv)
    rot = [A.group_rotation(r.t_dpd, r.lon, r.lcm) for r in pop.itertuples()]
    pop["N"] = [x[0] for x in rot]
    pop["N_eph"] = [x[2] for x in rot]
    pop["req_maps"] = [required_maps(x[1]) for x in rot]
    pop["map_missing"] = [bool(set(m) & set(missing)) for m in pop.req_maps]
    pop["N_ambiguous"] = pop.N != pop.N_eph
    m1 = l1.merge(pop[["noaa", "day", "N", "N_eph", "req_maps", "map_missing"]], on=["noaa", "day"], how="left",
                  validate="one_to_one", suffixes=("", "_pop"))
    check("C2 every L1 record matched in POPULATION", m1.N_pop.notna().all())
    check("C2 N recomputed = N recorded (L1)", (m1.N == m1.N_pop).all(), int((m1.N != m1.N_pop).sum()))
    check("C2 N_ephemeris recomputed = recorded (L1)", (m1.N_ephemeris == m1.N_eph).all())
    rec_maps = [sorted(int(v) for v in s.split(";")) if isinstance(s, str) and s else [] for s in m1["maps"]]
    mm = (m1.status == "map_missing").to_numpy()
    check("C2 map_missing records: required maps = recorded maps",
          all(r == q for r, q, f in zip(rec_maps, m1.req_maps, mm) if f), int(mm.sum()))
    check("C2 other records: recorded maps within required maps",
          all(set(r) <= set(q) for r, q, f in zip(rec_maps, m1.req_maps, mm) if not f and r))
    check("C2 L1 records flagged map_missing by the rule = status map_missing",
          (m1.map_missing.to_numpy() == mm).all(), int((m1.map_missing.to_numpy() != mm).sum()))
    check("C2 no successful L1 record has a missing required map", not (m1.map_missing & (m1.status == "ok")).any())
    c2 = dict(missing_maps=missing, population_map_missing=int(pop.map_missing.sum()),
              population_N_ambiguous=int(pop.N_ambiguous.sum()))

    # ---------------------------------------------------------------- C3, C4
    t = pd.to_datetime(pop.t_dpd)
    pop["CR_t"] = [cr_of_time(x) for x in t]
    f_date = t.dt.normalize() <= END_DATE
    f_cr = pop.CR_t < CR_H
    pop["in_MF"] = f_date & f_cr
    pop["in_MS"] = pop.in_MF & ~pop.map_missing & ~pop.N_ambiguous
    pop["cyc"] = [PA.cycle_of_time(PA.cr_start(c))[0] for c in pop.CR_t]
    c3 = dict(population=len(pop), excl_date=int((~f_date).sum()), excl_cr_after_date=int((f_date & ~f_cr).sum()),
              MF=int(pop.in_MF.sum()), excl_MS_map_missing=int((pop.in_MF & pop.map_missing).sum()),
              excl_MS_N_ambiguous=int((pop.in_MF & ~pop.map_missing & pop.N_ambiguous).sum()), MS=int(pop.in_MS.sum()),
              gap_1998_06_10_groups=int(((t >= GAP[0]) & (t < GAP[1])).sum()),
              gap_1998_06_10_groups_in_MF=int((pop.in_MF & (t >= GAP[0]) & (t < GAP[1])).sum()),
              last_t_MF=str(t[pop.in_MF].max()), first_t_MF=str(t[pop.in_MF].min()),
              last_CR_MF=int(pop.CR_t[pop.in_MF].max()), first_CR_MF=int(pop.CR_t[pop.in_MF].min()))
    cyc = []
    for d in ("MF", "MS"):
        g = pop[pop[f"in_{d}"]].groupby(["cyc", "hemisphere"]).size()
        for (c, h), n in g.items():
            cyc.append(dict(design=d, cyc=int(c), hemisphere=h, n_groups=int(n), ge50=int(n >= 50)))
    cyc = pd.DataFrame(cyc)

    # ---------------------------------------------------------------- C5
    s = samp.merge(l1[["noaa", "day", "status", "sens100_status"]], on=["noaa", "day"], how="left", validate="one_to_one")
    check("C5 every L1 sample unit has a record", s.status.notna().all())
    s["ok"], s["ok100"] = s.status == "ok", s.sens100_status == "ok"
    Nc = pop.groupby(KEYS).size().rename("N_pop")
    cc = cells.set_index(KEYS).join(Nc)
    check("C5 CELLS.N = population count per cell", (cc.N == cc.N_pop.fillna(0)).all())
    check("C5 sum N = 5401", int(cells.N.sum()) == len(pop) == 5401)
    check("C5 n1 = 530, n2 = 90", len(s) == 530 and int(samp.level2.sum()) == 90)
    sc = s.merge(cells[KEYS + ["N", "n1", "n2"]], on=KEYS, how="left")
    check("C5 w1 = N/n1 per unit", np.allclose(sc.w1, sc.N / sc.n1, rtol=TOL, atol=0))
    check("C5 unique (noaa, day) in SAMPLE", not samp.duplicated(["noaa", "day"]).any())
    pub1 = pd.read_csv(AN1)
    rep = []

    def proj_rows(df, wcol, okcols, by_list, level, pub, pub_map):
        for by in by_list:
            groups = [("all", df)] if by is None else [(f"{by}={v}", g) for v, g in df.groupby(by)]
            for name, g in groups:
                w = g[wcol].to_numpy(float)
                pname = pub_map(name)
                pr = pub[pub.group == pname]
                for okc, pcol in okcols:
                    val = float((w * g[okc]).sum() / w.sum())
                    pv = float(pr[pcol].iloc[0]) if len(pr) else np.nan
                    rep.append(dict(level=level, group=name, column=pcol, n=len(g), ok=int(g[okc].sum()),
                                    sum_w=float(w.sum()), projected=val, published=pv,
                                    rel_diff=abs(val - pv) / abs(pv) if pv else abs(val - pv)))

    proj_rows(s, "w1", [("ok", "projected_yield"), ("ok100", "projected_yield_100")],
              (None, "act_class", "area_class", "hemisphere", "cohort"), "L1", pub1, lambda x: x)
    # cell formula for the whole population (union of cells)
    agg = s.groupby(KEYS).agg(n=("ok", "size"), r=("ok", "sum")).join(cells.set_index(KEYS).N)
    cellf = float((agg.N * agg.r / agg.n).sum() / agg.N.sum())
    check("C5 L1 cell formula = unit formula (all)", abs(cellf - pub1[pub1.group == "all"].projected_yield.iloc[0]) < TOL * cellf)
    a = l2[(l2.rule == "A1") & (l2.image == "A")]
    check("C5 L2 A1 image A: one record per level-2 unit", len(a) == 90 and not a.duplicated(["noaa", "day"]).any())
    s2 = samp[samp.level2].merge(a[["noaa", "day", "status"]], on=["noaa", "day"], how="left", validate="one_to_one")
    s2["ok"] = s2.status == "ok"
    s2 = s2.merge(cells[KEYS + ["N", "n2"]], on=KEYS, how="left")
    check("C5 w2 = N/n2 per unit", np.allclose(s2.w2, s2.N / s2.n2, rtol=TOL, atol=0))
    s2["activity"], s2["area"], s2["year"] = s2.act_class, s2.area_class, s2.day.str[:4]
    pub2 = pd.read_csv(AN2)
    pub2 = pub2[pub2.image == "A"]
    proj_rows(s2, "w2", [("ok", "projected_yield")], (None, "activity", "area", "hemisphere", "cohort", "year"),
              "L2_A1_A", pub2, lambda x: x)
    rep = pd.DataFrame(rep)
    check("C5 every reproduced group has a published value", rep.published.notna().all(),
          rep[rep.published.isna()].group.tolist())
    check("C5 all projected yields reproduced within 1e-12 relative", (rep.rel_diff <= TOL).all(), float(rep.rel_diff.max()))

    # ---------------------------------------------------------------- C6
    s = s.merge(pop[["noaa", "day", "map_missing"]], on=["noaa", "day"], how="left", validate="one_to_one")
    check("C6 no successful L1 unit among map-missing units", not (s.map_missing & s.ok).any())
    ms = s[~s.map_missing].groupby(KEYS).agg(n=("ok", "size"), ok=("ok", "sum"), ok100=("ok100", "sum"))
    ms = cells.set_index(KEYS)[["N"]].join(ms).fillna(0).astype({"n": int, "ok": int, "ok100": int}).reset_index()
    ms["removed_map_missing"] = (cells.set_index(KEYS).n1.to_numpy() - ms.n.to_numpy())
    pools = []
    s2["w"] = s2.N / s2.n2
    for lev, by in (("cell", KEYS), ("cohort x area", ["cohort", "area_class"]), ("cohort x activity", ["cohort", "act_class"]),
                    ("cohort x hemisphere", ["cohort", "hemisphere"]), ("cohort", ["cohort"])):
        for k, g in s2.groupby(by):
            k = k if isinstance(k, tuple) else (k,)
            cn = cells.merge(pd.DataFrame([dict(zip(by, k))]), on=by)
            pools.append(dict(level=lev, key="|".join(f"{b}={v}" for b, v in zip(by, k)), n2=len(g), ok=int(g.ok.sum()),
                              sum_N=int(cn.N.sum()), projected=float((g.w * g.ok).sum() / g.w.sum()),
                              n_eff_kish=kish(g.w), lt5=int(len(g) < N_MIN)))
    pools = pd.DataFrame(pools)

    # ---------------------------------------------------------------- C7
    don = s[["noaa", "day", "ok", "ok100"] + KEYS].merge(pop[["noaa", "day", "lat"]], on=["noaa", "day"])
    don["alat"] = don.lat.abs()
    tg = pop[pop.in_MS].copy()
    tg["alat"] = tg.lat.abs()
    q = np.quantile(tg.alat, [1 / 3, 2 / 3])
    tg["lclass"] = np.searchsorted(q, tg.alat, side="right") + 1
    don["lclass"] = np.searchsorted(q, don.alat, side="right") + 1
    out7, res7 = [], {}
    for thr, okc in (("main", "ok"), ("sens100", "ok100")):
        d = don[don[okc]].sort_values(["noaa", "day"])
        lt = d.groupby(KEYS + ["lclass"]).size().rename("n_don")
        tt = tg.join(lt, on=KEYS + ["lclass"]).fillna({"n_don": 0})
        frac_lt = float((tt.n_don >= N_MIN).mean())
        cell_n = d.groupby(KEYS).size()
        dist = []
        for key, g in tg.groupby(KEYS):
            dd = d.set_index(KEYS).loc[[key]] if key in cell_n.index else None
            nd = 0 if dd is None else len(dd)
            for x in g.alat:
                if nd >= K_NN:
                    dl = np.abs(dd.alat.to_numpy() - x)
                    order = np.lexsort((np.arange(nd), dl))       # distance, then (noaa, day) order of d
                    dist.append(dl[order[:K_NN]].max())
                else:
                    dist.append(np.inf)
        dist = np.array(dist)
        cells_short = [dict(zip(KEYS, k)) for k, g in tg.groupby(KEYS) if cell_n.get(k, 0) < K_NN]
        p90 = float(np.quantile(dist, 0.9))
        res7[thr] = dict(lat_tercile_edges=[float(v) for v in q], frac_targets_LT_ge5=frac_lt,
                         LT_adopted=frac_lt >= FRAC_LT, cells_with_targets_lt5_donors=cells_short,
                         nn_p90_max_dlat=p90, nn_median_max_dlat=float(np.median(dist)),
                         LNN_adopted=(frac_lt < FRAC_LT) and not cells_short and p90 <= DLAT_MAX)
        res7[thr]["rule"] = "L-T" if res7[thr]["LT_adopted"] else ("L-NN" if res7[thr]["LNN_adopted"] else "amendment")
        for (k, n) in lt.items():
            out7.append(dict(threshold=thr, **dict(zip(KEYS + ["lclass"], k)), n_donors=int(n)))
    donors = pd.DataFrame(out7)

    # ---------------------------------------------------------------- write
    pd.DataFrame(checks).to_csv(OUT / "CHECKS.csv", index=False)
    cyc.to_csv(OUT / "C4_CYCLE_HEMISPHERE.csv", index=False)
    rep.to_csv(OUT / "C5_YIELD_REPRODUCTION.csv", index=False)
    ms.to_csv(OUT / "C6_MS_CELLS.csv", index=False)
    pools.to_csv(OUT / "C6_MF_POOLS.csv", index=False)
    donors.to_csv(OUT / "C7_DONORS_CELL_LATCLASS.csv", index=False)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "scripts", "docs", "results/MDI_PILOT_SELECTION",
                            "results/MDI_PILOT_L1", "results/MDI_PILOT_L2", "results/MDI_PILOT_ANALYSIS_L1",
                            "results/MDI_PILOT_ANALYSIS_L2", "results/MDI_SYNOPTIC_AUDIT"],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()
    out = dict(rules_sha256=sha(RULES), script_sha256=sha(__file__), git_head=head, dirty_paths=dirty,
               inputs={str(p.relative_to(ROOT)): sha(p) for p in (SEL / "META.json", SEL / "POPULATION.csv",
                       SEL / "SAMPLE.csv", SEL / "CELLS.csv", L1, L2, AN1, AN2, AUDIT)},
               columns_read=dict(L1=L1_COLS, L2=L2_COLS), C2=c2, C3=c3, C7=res7,
               checks_passed=int(sum(c["ok"] for c in checks)), checks_total=len(checks))
    (OUT / "META.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("C2", "C3", "C7", "checks_passed", "checks_total")}, indent=1, default=str))
    for c in checks:
        if not c["ok"]:
            print("FAILED:", c)


if __name__ == "__main__":
    main()
