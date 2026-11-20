"""Descriptive outputs of §6 required before S1-S4 are read (Codex's second review, point 3), kept in a separate file
so that it could be written while the validation ran (the validation hashes scripts/t3_mwo_analysis.py at start and
end). Called by the stability stage of scripts/t3_mwo_analysis.py, after the seal has been opened by read_sealed();
no function here reads SEALED.csv.gz itself.

  sources_by_epoch   DPD source observatory of the record days, per epoch (next to S1: a DPD source change must not
                     be attributed to MWO; SOHO/MDI dominates DPD in 2006-2007 and 2010, inside E8)
  s2_p1              S2 repeated against P1 (HMI) in 2010-05 -> 2012-12: same NOAA region, same UTC day; d_P1 =
                     axial(gamma_MWO - gamma_P1); procedure M on the main model when identifiable (descriptive)
  s4_isolation       per activity tercile of the 'all' set: fraction of groups that are not isolated (record only in
                     the 'all' set), mean rank of the chosen day, mean |LCM|
  s4_dwl_all         d_WL of the 'all records' sensitivity, isolated against non-isolated records, overall and by
                     activity tercile (descriptive)

Not yet wired into the stability stage (that file must not change while the validation runs): IMPLEMENTED stays
False until the call is added and reviewed.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTED = False
DAILY = ROOT / "data/sharp/external_DPD_20261118/dailyDPD1974_2016.txt"
P1_CAT = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"


def daily_sources(path=DAILY):
    src = {}
    for line in Path(path).read_text().splitlines():
        t = line.split()
        if line.startswith("d ") and len(t) >= 12:
            src[f"{t[1]}-{t[2]}-{t[3]}"] = t[7] if t[7].isalpha() else "(none)"
    return src


def sources_by_epoch(d, path=DAILY):
    src = daily_sources(path)
    s = d.assign(source=[src.get(x, "(missing)") for x in d.day])
    tab = s.groupby(["epoch", "source"]).size().rename("n").reset_index()
    tab["share"] = tab.n / tab.groupby("epoch").n.transform("sum")
    return tab.sort_values(["epoch", "n"], ascending=[True, False]).reset_index(drop=True)


def terciles(x):
    q = np.nanquantile(x, [1 / 3, 2 / 3])
    return np.searchsorted(q, x, side="right") + 1


def s4_isolation(d_all, d_iso):
    a = d_all.assign(A_tercile=terciles(d_all.A_main.to_numpy()), isolated_record=d_all.noaa.isin(set(d_iso.noaa)))
    return a.groupby("A_tercile").agg(n_groups=("noaa", "size"),
                                      frac_not_isolated=("isolated_record", lambda v: 1 - v.mean()),
                                      mean_rank=("rank", "mean"), mean_abs_lcm=("abs_lcm", "mean")).reset_index()


def s4_dwl_all(d_all_with_dwl):
    """d_all_with_dwl: the 'all' set with columns d_wl, wl_status and isolated (record-level flag)."""
    x = d_all_with_dwl[d_all_with_dwl.wl_status == "ok"].copy()
    x["A_tercile"] = terciles(x.A_main.to_numpy())
    groups = [((i, "all"), x[x.isolated == i]) for i in (True, False)]
    groups += [((i, k), x[(x.isolated == i) & (x.A_tercile == k)]) for i in (True, False) for k in (1, 2, 3)]
    rows = []
    for (iso, t), g in groups:
        v = g.d_wl.to_numpy(float)
        rows.append(dict(isolated=iso, A_tercile=t, n=len(v), median=float(np.median(v)) if len(v) else np.nan,
                         mean=float(v.mean()) if len(v) else np.nan,
                         s_over_sqrt_n=float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else np.nan))
    return pd.DataFrame(rows)


def p1_records():
    """P1 sample S records with a NOAA number, T_REC (TAI) converted to the UTC day, gamma in the P1 convention."""
    import sys
    from astropy.time import Time
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import run_p2
    cat = pd.read_csv(P1_CAT, low_memory=False)
    S = run_p2.samples(cat)["S"]
    S = S[pd.to_numeric(S["NOAA_AR"], errors="coerce") > 0].copy()
    utc = Time(list(np.array(S["t"].dt.to_pydatetime())), scale="tai").utc.to_datetime()
    S["day"] = [u.strftime("%Y-%m-%d") for u in utc]
    S["noaa"] = S["NOAA_AR"].astype(float).astype(int).astype(str)
    return S[["noaa", "day", "gamma"]].drop_duplicates(["noaa", "day"])


def s2_p1(d_iso_with_gamma, s2_fit, axial, p1=None):
    """d_iso_with_gamma: isolated records with gamma_mwo. Returns (summary dict, matched table)."""
    p1 = p1_records() if p1 is None else p1
    x = d_iso_with_gamma[(d_iso_with_gamma.day >= "2010-05-01") & (d_iso_with_gamma.day < "2013-01-01")]
    m = x.merge(p1, on=["noaa", "day"], how="inner")
    m["d_wl"] = axial(m.gamma_mwo - m.gamma)            # s2_fit reads the response from the column d_wl
    fit = s2_fit(m.reset_index(drop=True)) if len(m) else dict(state="campione vuoto")
    summ = dict(n_matched=len(m), median_d=float(np.median(m.d_wl)) if len(m) else None,
                fit={k: v for k, v in fit.items() if k in ("state", "beta", "se", "lo", "hi", "n", "error", "var_a", "var_b",
                                                           "phi", "kappa", "sigma_x2")})
    return summ, m[["noaa", "day", "epoch", "hemisphere", "d_wl"]].rename(columns={"d_wl": "d_p1"})


def extras(A, d_iso, sealed, d_all):
    """All descriptive outputs; A is the analysis module (its s2_fit, axial, wl_for_records are reused).
    d_iso must already carry gamma_mwo; d_all is the 'all' design set."""
    sx_all = sealed[sealed.record_set == "all"].set_index("noaa")
    da = d_all.copy()
    da["gamma_mwo"] = sx_all.loc[da.noaa, "gamma_deg"].to_numpy()
    gwl, st = A.wl_for_records(da)
    da["gamma_wl"], da["wl_status"] = gwl, st
    da["d_wl"] = A.axial(da.gamma_mwo - da.gamma_wl)
    s2p1, matched = s2_p1(d_iso, A.s2_fit, A.axial)
    return {"S1_DPD_SOURCES.csv": sources_by_epoch(d_iso), "S2_P1.json": s2p1, "S2_P1_MATCHED.csv": matched,
            "S4_ISOLATION.csv": s4_isolation(d_all, d_iso), "S4_DWL_ALL.csv": s4_dwl_all(da)}


def selftest():
    import tempfile
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    d = pd.DataFrame(dict(noaa=["1", "2", "3", "4"], day=["1990-05-01", "1990-05-02", "2006-03-01", "2006-03-02"],
                          epoch=["E5", "E5", "E8", "E8"], A_main=[0.5, 1.0, 1.5, 2.0], rank=[1, 2, 1, 1],
                          abs_lcm=[5.0, 10.0, 3.0, 1.0]))
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "daily.txt"
        f.write_text("d 1990 05 01 09 00 00 GYUL 1 2 3 4 0 0 0\nd 1990 05 02 09 00 00 DEBR 1 2 3 4 0 0 0\n"
                     "d 2006 03 01 09 00 00 SOHO 1 2 3 4 0 0 0\nd 2006 03 02 09 00 00 SOHO 1 2 3 4 0 0 0\n")
        sb = sources_by_epoch(d, f)
    ok("DPD sources by epoch", sb[sb.epoch == "E8"].source.tolist() == ["SOHO"]
       and np.isclose(sb[sb.epoch == "E5"].share.sum(), 1.0))
    s4 = s4_isolation(d, d.iloc[[0, 2]])
    ok("fraction not isolated by tercile", set(s4.columns) >= {"frac_not_isolated", "mean_rank", "mean_abs_lcm"}
       and s4.n_groups.sum() == 4 and np.isclose((s4.frac_not_isolated * s4.n_groups).sum(), 2))
    da = d.assign(wl_status="ok", d_wl=[1.0, 2.0, 3.0, 5.0], isolated=[True, False, True, False])
    t = s4_dwl_all(da)
    ok("d_WL of the 'all' set by isolation", t[(t.isolated) & (t.A_tercile == "all")].n.iloc[0] == 2
       and np.isclose(t[(~t.isolated.astype(bool)) & (t.A_tercile == "all")]["mean"].iloc[0], 3.5))
    di = d.assign(day=["2010-06-01", "2011-01-01", "2012-02-02", "2009-01-01"], gamma_mwo=[10.0, 5.0, -3.0, 4.0],
                  hemisphere="N")
    p1 = pd.DataFrame(dict(noaa=["1", "2", "4"], day=["2010-06-01", "2011-01-01", "2009-01-01"], gamma=[8.0, 95.0, 4.0]))
    summ, mt = s2_p1(di, lambda m: dict(state="stimato", n=len(m), beta=0.0),
                     lambda x: (np.asarray(x) + 90) % 180 - 90, p1)
    ok("S2 vs P1: only 2010-05 -> 2012-12, same NOAA and day; axial difference",
       summ["n_matched"] == 2 and sorted(mt.d_p1.round(6).tolist()) == [-90.0, 2.0], mt.d_p1.tolist())
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    import sys
    sys.exit(0 if selftest() else 1)
