"""Independent recount of the T3-on-MWO statistics (delivery 2, Codex's review point 5). Does not import
scripts/t3_mwo_analysis.py nor any function that produced the decisions.

  --check-design      rebuilds from DESIGN.csv the columns, the identifiability of beta3, the reduced matrix, the true
                      values of the ramp (10 %, 20 %) and, from the DPD spot rows with own parser, the white-light
                      availability and C; compares with results/T3_MWO_DESIGN_CHECK_R3.
  --check-validation  from RAW.csv.gz: own grid, validity of every row, SE of every successful row recomputed from its
                      saved parameters of M, frequencies, the 15-deg acceptance; compares with SUMMARY and ACCEPTANCE.

Receipts: results/T3_MWO_DESIGN_CHECK_R3_RECOUNT/RECEIPT.json, results/T3_MWO_VALIDATION_R3_RECOUNT/RECEIPT.json, each bound
to the SHA-256 of the META it recounts.

    .venv/bin/python scripts/t3_mwo_analysis_recount.py --selftest
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "results/T3_MWO_CATALOGUE_R3"
CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK_R3"
VAL = ROOT / "results/T3_MWO_VALIDATION_R3"
OUT_CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK_R3_RECOUNT"
OUT_VAL = ROOT / "results/T3_MWO_VALIDATION_R3_RECOUNT"
SDPD = ROOT / "data/sharp/external_sDPD_20261118"
GDPD = ROOT / "data/sharp/external_DPD_20261118"
Z = float(norm.ppf(1 - 0.0125))
G0, SDE, SDX = 24.0, 15.0, 7.5
ORDER = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")


def h256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- design (own construction)

def matrix(d):
    """Columns of §3 in the frozen order, the target column, after the removal of redundant columns."""
    s = d.sinlat.to_numpy()
    cols, names = [], []
    for c in sorted(d.cycle.unique()):
        for h in "NS":
            m = ((d.cycle == c) & (d.hemisphere == h)).to_numpy()
            if m.any():
                cols.append(s * m)
                names.append(f"k_{c}{h}")
    for h in "NS":
        e_h = d[d.hemisphere == h].epoch.value_counts()
        ref = sorted(e_h.index, key=lambda e: (-e_h[e], ORDER.index(e)))[0] if len(e_h) else None
        d.attrs[f"ref_{h}"] = ref
    for e in ORDER:
        for h in "NS":
            m = ((d.epoch == e) & (d.hemisphere == h)).to_numpy()
            if m.any() and e != d.attrs.get(f"ref_{h}"):
                cols.append(s * m)
                names.append(f"d_{e}{h}")
    x3 = (d.A_main.to_numpy() - 1.0) * s
    w = d.phi_mwo.to_numpy(float)
    sw = np.sqrt(w)[:, None]
    Zm = np.column_stack(cols)
    rank = lambda M: np.linalg.matrix_rank(M * sw) if M.shape[1] else 0      # noqa: E731
    ident = rank(np.column_stack([Zm, x3])) == rank(Zm) + 1
    kept, cur = [], np.zeros((len(d), 0))
    for j, n in enumerate(names):
        t = np.column_stack([cur, Zm[:, j]])
        if Zm[:, j].any() and rank(t) > cur.shape[1]:
            kept.append(n)
            cur = t
    return ident, kept, np.column_stack([cur, x3]), w


def projection(X, w):
    """Row of beta3 of the WLS solution, by QR of the weighted matrix (own computation)."""
    sw = np.sqrt(w)
    Q, R = np.linalg.qr(X * sw[:, None])
    return (np.linalg.solve(R, Q.T)[-1]) * sw


def ramp_true(d, g, e):
    ab = d.groupby(["CR", "hemisphere"]).A_main.transform("mean").to_numpy()
    q5, q95 = np.quantile(ab, [0.05, 0.95])
    return float(g @ (-e * G0 * np.clip((ab - q5) / (q95 - q5), 0, 1) * d.sinlat.to_numpy()))


def wl_available(d, gdpd=GDPD, sdpd=SDPD):
    """Own parsing: group row kept (largest area, first in file order), its spot rows (same instant string),
    availability = two or more spots, positive area, both halves around the area-weighted centroid non-empty."""
    best = {}
    for y in range(1974, 2013):
        p = Path(gdpd) / f"gDPD{y}.txt"
        if p.exists():
            for ln in p.read_text().splitlines():
                if ln.startswith("g "):
                    try:
                        f = [float(ln[a:b]) for a, b in ((59, 65), (66, 72), (73, 79))]
                        ar = int(ln[53:58])
                    except ValueError:
                        continue
                    if max(f) > 900:
                        continue
                    k = (f"{ln[2:6]}-{ln[7:9]}-{ln[10:12]}", ln[22:28].strip())
                    if k not in best or ar > best[k][0]:
                        best[k] = (ar, ln[2:21])
    want = {(best[(r.day, r.noaa)][1], r.noaa) for r in d.itertuples() if (r.day, r.noaa) in best}
    spots = {}
    for y in sorted({int(t[:4]) for t, _ in want}):
        for ln in (Path(sdpd) / f"sDPD{y}.txt").read_text().splitlines():
            k = (ln[2:21], ln[22:29].strip())
            if ln.startswith("s ") and k in want:
                try:
                    la, lo, ar = float(ln[59:65]), float(ln[66:72]), int(ln[53:58])
                except ValueError:
                    continue
                if la < 900 and lo < 900:
                    spots.setdefault(k, []).append((lo, ar))
    out = []
    for r in d.itertuples():
        k = (best[(r.day, r.noaa)][1], r.noaa) if (r.day, r.noaa) in best else None
        sp = spots.get(k) if k else None
        if not sp or len(sp) < 2:
            out.append(False)
            continue
        lo = np.array([x[0] for x in sp])
        w = np.array([max(x[1], 0) for x in sp], float)
        if w.sum() <= 0:
            out.append(False)
            continue
        ref = lo[np.argmax(w)]
        c = ref + np.sum(w * ((lo - ref + 180) % 360 - 180)) / w.sum()
        rel = (lo - c + 180) % 360 - 180
        out.append(bool(((rel > 0) & (w > 0)).any() and ((rel <= 0) & (w > 0)).any()))
    return np.array(out)


def check_design(cat=CAT, check=CHECK, out=OUT_CHECK, gdpd=GDPD, sdpd=SDPD, write=True):
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    meta = json.loads((Path(check) / "META.json").read_text())
    ok("design-check product hashes", all(h256(Path(check) / n) == h for n, h in meta["products_sha256"].items()))
    ok("design check bound to the catalogue META", meta.get("catalogue_meta_sha256") == h256(Path(cat) / "META.json"))
    d = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    d = d[d.record_set == "isolated"].reset_index(drop=True)
    ident, kept, X, w = matrix(d)
    saved = json.loads((Path(check) / "IDENTIFIABILITY.json").read_text())["joy"]
    ok("identifiability and kept columns", ident == saved["identifiable"] and kept == saved["kept"], (ident, len(kept)))
    tg = json.loads((Path(check) / "TARGETS.json").read_text())
    if ident:
        g = projection(X, w)
        t10, t20 = ramp_true(d, g, 0.1), ramp_true(d, g, 0.2)
        ok("true values of the ramp (10 %, 20 %)", abs(t10 - tg["delta_beta_10"]) < 1e-9 * max(1, abs(t10))
           and abs(t20 - tg["delta_beta_20"]) < 1e-9 * max(1, abs(t20)), (t10, t20))
    av = wl_available(d, gdpd, sdpd)
    sv = pd.read_csv(Path(check) / "WL_AVAILABILITY.csv", dtype={"noaa": str})
    ok("white-light availability of every record", (sv.noaa.tolist() == d.noaa.tolist())
       and ((sv.wl_status == "ok").to_numpy() == av).all(), f"{int(av.sum())} available of {len(d)}")
    sub = d[av].reset_index(drop=True)
    C = None
    if len(sub):
        i_s, _, Xs, ws = matrix(sub)
        C = 0.5 * abs(ramp_true(sub, projection(Xs, ws), 0.2)) if i_s else None
    ok("margin C on the subset", (C is None and tg["C"] is None) or (C is not None and tg["C"] is not None
                                                                     and abs(C - tg["C"]) < 1e-9 * max(1, abs(C))), C)
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(checks=res, passed=sum(r["ok"] for r in res), total=len(res),
                                                                design_check_meta_sha256=h256(Path(check) / "META.json")),
                                                           indent=2) + "\n")
    return all(r["ok"] for r in res)


# ---------------------------------------------------------------- validation

def grid():
    g = [(s, 15.0, 0.0, 10_000) for s in (0, 1, 2, 7, 9)]
    g += [(s, 15.0, e, 2000) for s in (1, 2, 7, 9) for e in (0.1, 0.2)]
    g += [(s, 25.0, 0.0, 2000) for s in (0, 1, 2, 7, 9)]
    return g


def se_from_saved(r, d, g, codes, cr, hh, logphi_c):
    """SE of M from the saved parameters: sigma_x2 b'K b + sum g^2 sig2_i, K AR(1) bivariate (phi, kappa)."""
    sig2 = np.exp(r.var_a + r.var_b * logphi_c)
    b = np.bincount(codes, weights=g)
    lag = np.abs(cr[:, None] - cr[None, :])
    K = np.where(hh[:, None] == hh[None, :], 1.0, r.kappa) * r.phi ** lag
    return math.sqrt(r.sigma_x2 * float(b @ K @ b) + float(np.sum(g ** 2 * sig2)))


def check_validation(cat=CAT, check=CHECK, val=VAL, out=OUT_VAL, write=True, se_rows=None):
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    meta = json.loads((Path(val) / "META.json").read_text())
    ok("validation product hashes", all(h256(Path(val) / n) == h for n, h in meta["products_sha256"].items()))
    ok("validation bound to the design check", meta.get("design_check_meta_sha256") == h256(Path(check) / "META.json"))
    ok("provenance unchanged during the run", meta.get("provenance_start") == meta.get("provenance_end"))
    raw = pd.read_csv(Path(val) / "RAW.csv.gz")
    tg = json.loads((Path(check) / "TARGETS.json").read_text())
    truth = {0.1: tg["delta_beta_10"], 0.2: tg["delta_beta_20"]}
    exp = []
    for i, (s, sd, e, n) in enumerate(grid()):
        exp += [(i, k, 60_000_000 + 100_000 * i + k, s, sd, e) for k in range(n)]
    ex = pd.DataFrame(exp, columns=["cfg", "k", "seed", "scenario", "sd_e", "effect"])
    mg = ex.merge(raw, on=["cfg", "k"], how="outer", suffixes=("", "_r"), indicator=True)
    complete = bool((mg._merge == "both").all() and len(raw) == len(ex) and (mg.seed == mg.seed_r).all()
                    and (mg.scenario == mg.scenario_r).all() and np.allclose(mg.sd_e, mg.sd_e_r)
                    and np.allclose(mg.effect, mg.effect_r))
    ok("grid complete: configurations, replicas, seeds", complete, f"{len(raw)} rows, {len(ex)} expected")
    okr = raw.verdict != "errore"
    t = raw.effect.map(lambda e: 0.0 if e == 0 else truth[e])
    num = raw[["beta", "se", "lo", "hi", "truth"]].astype(float)
    par = raw[["var_a", "var_b", "phi", "kappa", "sigma_x2"]].astype(float)
    valid = raw.verdict.isin(["supportato", "opposto", "non deciso", "errore"])
    good = (np.isfinite(num).all(axis=1) & np.isfinite(par).all(axis=1) & (par.phi >= 0) & (par.phi <= 0.98)
            & (par.kappa.abs() <= 0.98) & (par.sigma_x2 > 0) & (num.se > 0) & (num.lo < num.hi)
            & (np.abs(num.lo - num.beta + Z * num.se) <= 1e-9 * num.se) & (np.abs(num.hi - num.beta - Z * num.se) <= 1e-9 * num.se)
            & (np.abs(num.truth - t) <= 1e-12 * np.maximum(1, np.abs(t)))
            & (raw.verdict == np.where(num.hi < 0, "supportato", np.where(num.lo > 0, "opposto", "non deciso")))
            & (raw.covered == ((num.lo <= num.truth) & (num.truth <= num.hi)).astype(int))
            & (raw.lo_above == (num.lo > num.truth).astype(int)) & (raw.hi_below == (num.hi < num.truth).astype(int)))
    bad = ~valid | (okr & ~good)
    ok("every row valid (finite, SE > 0, bounds = beta -/+ z SE, verdict and indicators, true value)", not bad.any(),
       f"{int(bad.sum())} invalid")
    d = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    d = d[d.record_set == "isolated"].reset_index(drop=True)
    _, _, X, w = matrix(d)
    g = projection(X, w)
    key = pd.MultiIndex.from_arrays([d.CR.astype(int).to_numpy(), d.hemisphere.to_numpy()])
    codes, uniq = pd.factorize(key)
    cr = np.array([c for c, _ in uniq])
    cr = cr - cr.min()
    hh = np.array([h for _, h in uniq])
    lp = np.log(w)
    lp_c = lp - lp.mean()
    rows = raw[okr & ~bad]                     # invalid rows are already failed above; they stay in the denominators
    partial = se_rows is not None              # a test run on a subset of rows can never give a complete receipt
    if partial:
        rows = rows.iloc[:se_rows]
    dev = []
    for r in rows.itertuples():
        try:
            dev.append(abs(se_from_saved(r, d, g, codes, cr, hh, lp_c) / r.se - 1))
        except (ValueError, OverflowError, ZeroDivisionError):
            dev.append(np.nan)
    dev = np.array(dev, float)
    ok("SE recomputed from the saved parameters of M (every reconstruction finite)",
       len(dev) == int((okr & ~bad).sum()) - (0 if not partial else int((okr & ~bad).sum()) - len(dev))
       and np.isfinite(dev).all() and (dev < 1e-6).all(),
       f"{len(dev)} rows, non-finite {int((~np.isfinite(dev)).sum())}, max rel {np.nanmax(dev) if len(dev) else 0:.1e}")
    acc, worst_f = True, 0.0
    summ = pd.read_csv(Path(val) / "SUMMARY.csv")
    for i, (s, sd, e, n) in enumerate(grid()):
        gg = raw[raw.cfg == i]
        er = (gg.verdict == "errore").sum() / n
        sp, op = (gg.verdict == "supportato").sum() / n, (gg.verdict == "opposto").sum() / n
        cov = gg[gg.verdict != "errore"].covered.sum() / n
        tail = gg[gg.verdict != "errore"].lo_above.sum() / n
        sr = summ[summ.cfg == i].iloc[0]
        worst_f = max(worst_f, abs(sr.supportato - sp), abs(sr.opposto - op), abs(sr.frac_errors - er),
                      abs(sr.coverage - cov), abs(sr.exclusion_tail - tail))
        if sd == 15.0:
            acc &= bool((sp + op <= 0.030 and sp <= 0.0175 and op <= 0.0175 and er <= 0.01) if e == 0
                        else (cov >= 0.965 and tail <= 0.020))
    technical = complete and not bad.any() and meta.get("provenance_start") == meta.get("provenance_end")
    acc = bool(acc and technical)
    ok("frequencies of every configuration", worst_f < 1e-12, f"max abs {worst_f:.1e}")
    saved = json.loads((Path(val) / "ACCEPTANCE.json").read_text())
    ok("15-deg acceptance recounted", acc == saved["accepted_15deg"] and (not technical) == bool(saved["problems"]),
       dict(recounted=acc, saved=saved["accepted_15deg"]))
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
            checks=res, passed=sum(r["ok"] for r in res), total=len(res), partial=partial, recounted_acceptance=acc,
            technical_ok=technical,
            validation_meta_sha256=h256(Path(val) / "META.json")), indent=2) + "\n")
    return all(r["ok"] for r in res)


def selftest():
    """Synthetic design and products written here (no import of the analysis module); the analysis module is run in a
    subprocess only to produce the products to recount."""
    import subprocess
    import tempfile
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        code = f"""
import sys, json, hashlib, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
sys.argv = ['x']
s = importlib.util.spec_from_file_location('a', {str(ROOT / 'scripts/t3_mwo_analysis.py')!r})
A = importlib.util.module_from_spec(s); s.loader.exec_module(A)
td = Path({str(td)!r})
d = A.synthetic_design(n_per=60)
(td / 'cat').mkdir(); d.to_csv(td / 'cat/DESIGN.csv', index=False); (td / 'cat/META.json').write_text('{{}}')
st = A.design_state(td / 'cat')
w = st['w']; names, Z, x3 = A.columns(d); info, Xr = A.reduce(names, Z, x3, w)
targets = {{'delta_beta_10': st['truth'][0.1], 'delta_beta_20': st['truth'][0.2], 'C': None}}
(td / 'chk').mkdir()
(td / 'chk/IDENTIFIABILITY.json').write_text(json.dumps({{'joy': dict(info, n=len(d))}}))
(td / 'chk/TARGETS.json').write_text(json.dumps(targets))
pd.DataFrame(dict(noaa=d.noaa, wl_status='wl_no_group_row')).to_csv(td / 'chk/WL_AVAILABILITY.csv', index=False)
h = {{f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (td / 'chk').iterdir()}}
(td / 'chk/META.json').write_text(json.dumps(dict(products_sha256=h, catalogue_meta_sha256=hashlib.sha256(b'{{}}').hexdigest())))
A._W.update(st)
cfgs = A.configs()
for c in cfgs: c['n'] = 3
A.configs = lambda: cfgs
rows = [A.unit((c['cfg'], k)) for c in cfgs for k in range(3)]
raw = pd.DataFrame(rows)
tab, acc, pr = A.summarise(raw, st['truth'])
(td / 'val').mkdir(); raw.to_csv(td / 'val/RAW.csv.gz', index=False); tab.to_csv(td / 'val/SUMMARY.csv', index=False)
(td / 'val/ACCEPTANCE.json').write_text(json.dumps(dict(accepted_15deg=acc, problems=pr)))
h = {{f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (td / 'val').iterdir()}}
(td / 'val/META.json').write_text(json.dumps(dict(products_sha256=h, provenance_start=1, provenance_end=1,
    design_check_meta_sha256=hashlib.sha256((td / 'chk/META.json').read_bytes()).hexdigest())))
"""
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok("analysis module run on a synthetic design (subprocess)", r.returncode == 0, r.stderr[-400:])
        if r.returncode:
            return False
        for y in range(1974, 2013):
            (td / f"gDPD{y}.txt").write_text("")
        ok("check_design passes on the analysis products", check_design(td / "cat", td / "chk", td / "o1", td, td, write=False))
        global grid
        g0 = grid
        grid = lambda: [(s, sd, e, 3) for s, sd, e, _ in g0()]          # noqa: E731
        try:
            good = check_validation(td / "cat", td / "chk", td / "val", td / "o2", write=False)
            ok("check_validation passes on the analysis products (3 replicas per configuration)", good)
            raw = pd.read_csv(td / "val/RAW.csv.gz")
            i = raw.index[raw.verdict != "errore"][0]
            raw.loc[i, "se"] = raw.loc[i, "se"] * 1.01
            raw.to_csv(td / "val/RAW.csv.gz", index=False)
            m = json.loads((td / "val/META.json").read_text())
            m["products_sha256"]["RAW.csv.gz"] = h256(td / "val/RAW.csv.gz")
            (td / "val/META.json").write_text(json.dumps(m))
            ok("check_validation fails on a tampered SE", not check_validation(td / "cat", td / "chk", td / "val", td / "o3",
                                                                              write=False))
            raw.loc[i, "se"] = raw.loc[i, "se"] / 1.01
            j = raw.index[raw.verdict != "errore"][1]
            raw.loc[j, "sigma_x2"] = np.nan
            raw.to_csv(td / "val/RAW.csv.gz", index=False)
            m["products_sha256"]["RAW.csv.gz"] = h256(td / "val/RAW.csv.gz")
            (td / "val/META.json").write_text(json.dumps(m))
            ok("check_validation fails on a NaN variance parameter of M (second row)",
               not check_validation(td / "cat", td / "chk", td / "val", td / "o4", write=False))
        finally:
            grid = g0
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-design", action="store_true")
    ap.add_argument("--check-validation", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check_design and check_design())
             or (a.check_validation and check_validation()) else 1)
