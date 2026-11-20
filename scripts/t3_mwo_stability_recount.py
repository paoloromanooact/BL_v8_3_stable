"""Independent recount of the T3-on-MWO stability stage (S1-S4 of docs/PROTOCOL_T3_MWO.md §6) before beta3 is
estimated. Does not import scripts/t3_mwo_analysis.py nor scripts/t3_mwo_stability_extras.py; reuses only the
independent recount helpers of scripts/t3_mwo_analysis_recount.py (columns, QR projection, SE from saved parameters).

Requires the stability outputs preserved in Git (they exist only after the seal was opened by the chain). Rebuilds:
white-light tilts and d_WL; S1 (fit, differences, block bootstrap with the frozen seed 69 000 001, percentile intervals,
flags, status); S2 (beta from the own projection, SE from the saved parameters of M, interval, precedence with C);
S2 by hemisphere when estimated; S3 (Hale agreement); S4 (selection table, non-isolation fraction, d_WL of the 'all'
set); the DPD sources by epoch; S2 against P1 (count and median); the final rule. Receipt bound to the SHA-256 of the
stability META: results/T3_MWO_STABILITY_RECOUNT/RECEIPT.json.

    .venv/bin/python scripts/t3_mwo_stability_recount.py --selftest
    .venv/bin/python scripts/t3_mwo_stability_recount.py --check
"""
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

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("t3_rc", ROOT / "scripts/t3_mwo_analysis_recount.py")
RC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(RC)

CAT = ROOT / "results/T3_MWO_CATALOGUE_R2"
CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK"
VAL = ROOT / "results/T3_MWO_VALIDATION"
STAB = ROOT / "results/T3_MWO_STABILITY"
OUT = ROOT / "results/T3_MWO_STABILITY_RECOUNT"
GDPD, SDPD = RC.GDPD, RC.SDPD
DAILY = GDPD / "dailyDPD1974_2016.txt"
ORDER = RC.ORDER
SEED, BLOCK, REPS, THR, MAXSING, MINEH, MAXUNV = 69_000_001, 6, 2000, 2.4, 0.05, 50, 0.20


def h256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def committed(path):
    p = Path(path)
    if not p.exists():
        return False
    rel = str(p.relative_to(ROOT))
    tracked = set(subprocess.run(["git", "ls-files", rel], cwd=ROOT, capture_output=True, text=True).stdout.split())
    dirty = subprocess.run(["git", "status", "--porcelain", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    files = [f for f in p.rglob("*") if f.is_file()]
    return bool(files) and all(str(f.relative_to(ROOT)) in tracked for f in files) and not dirty


# ---------------------------------------------------------------- white light (own)

def wl_gamma(d, gdpd=GDPD, sdpd=SDPD):
    best = {}
    for y in range(1974, 2013):
        p = Path(gdpd) / f"gDPD{y}.txt"
        if not p.exists():
            continue
        for ln in p.read_text().splitlines():
            if not ln.startswith("g "):
                continue
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
                    spots.setdefault(k, []).append((la, lo, ar))
    out = []
    for r in d.itertuples():
        sp = spots.get((best[(r.day, r.noaa)][1], r.noaa)) if (r.day, r.noaa) in best else None
        if not sp or len(sp) < 2:
            out.append(np.nan)
            continue
        la = np.array([x[0] for x in sp])
        lo = np.array([x[1] for x in sp])
        w = np.array([max(x[2], 0) for x in sp], float)
        if w.sum() <= 0:
            out.append(np.nan)
            continue
        ref = lo[np.argmax(w)]
        c = ref + np.sum(w * ((lo - ref + 180) % 360 - 180)) / w.sum()
        rel = (lo - c + 180) % 360 - 180
        hd, tl = (rel > 0) & (w > 0), (rel <= 0) & (w > 0)
        if not hd.any() or not tl.any():
            out.append(np.nan)
            continue
        latc = np.sum(w * la) / w.sum()
        a = math.degrees(math.atan2(np.sum(w[hd] * la[hd]) / w[hd].sum() - np.sum(w[tl] * la[tl]) / w[tl].sum(),
                                    (np.sum(w[hd] * rel[hd]) / w[hd].sum() - np.sum(w[tl] * rel[tl]) / w[tl].sum())
                                    * math.cos(math.radians(latc))))
        out.append(-math.copysign(1.0, latc) * a)
    return np.array(out)


def axial(x):
    return (np.asarray(x) + 90.0) % 180.0 - 90.0


# ---------------------------------------------------------------- S1 (own implementation of §6)

def fit_eh(sub):
    keys = sorted({(e, h) for e, h in zip(sub.epoch, sub.hemisphere)}, key=lambda k: (ORDER.index(k[0]), k[1]))
    s = sub.sinlat.to_numpy()
    X = np.column_stack([c for e, h in keys for m in [((sub.epoch == e) & (sub.hemisphere == h)).to_numpy()]
                         for c in (s * m, 1.0 * m)])
    sw = np.sqrt(sub.phi_mwo.to_numpy(float))
    if np.linalg.matrix_rank(X * sw[:, None]) < X.shape[1]:
        return None
    coef = np.linalg.lstsq(X * sw[:, None], sub.d_wl.to_numpy() * sw, rcond=None)[0]
    return {k: (coef[2 * i], coef[2 * i + 1]) for i, k in enumerate(keys)}


def diffs(fit, sub, verif):
    out = {}
    for h in "NS":
        ks = [k for k in fit if k[1] == h and verif.get(k)]
        if ks:
            wt = np.array([sub.phi_mwo[(sub.epoch == e) & (sub.hemisphere == h)].sum() for e, _ in ks])
            ab = float(np.sum(wt * np.array([fit[k][0] for k in ks])) / wt.sum())
            out.update({k: fit[k][0] - ab for k in ks})
    return out


def s1_own(sub, verif, reps=REPS):
    fit = fit_eh(sub)
    if fit is None:
        return "non determinato", pd.DataFrame(), 0
    df = diffs(fit, sub, verif)
    rng = np.random.default_rng(SEED)
    blocks = []
    for e in ORDER:
        se = sub[sub.epoch == e]
        if len(se):
            b = ((se.CR.astype(int) - int(se.CR.min())) // BLOCK).to_numpy()
            blocks.append([se.index[b == j] for j in np.unique(b)])
    boot, sing = {k: [] for k in df}, 0
    for _ in range(reps):
        idx = np.concatenate([np.concatenate([bl[i] for i in rng.integers(0, len(bl), len(bl))]) for bl in blocks])
        rs = sub.loc[idx].reset_index(drop=True)
        f = fit_eh(rs)
        if f is None or any(k not in f for k in df):
            sing += 1
            continue
        dd = diffs(f, rs, verif)
        for k in df:
            boot[k].append(dd.get(k, np.nan))
    rows = []
    for k, v in df.items():
        arr = np.array(boot[k])
        lo, hi = np.nanquantile(arr, [0.025, 0.975]) if len(arr) else (np.nan, np.nan)
        rows.append(dict(epoch=k[0], hemisphere=k[1], a=fit[k][0], b=fit[k][1], diff=v, lo=lo, hi=hi,
                         flag=bool((lo > 0 or hi < 0) and abs(v) > THR)))
    t = pd.DataFrame(rows)
    st = "non determinato" if sing > MAXSING * reps else ("instabile" if len(t) and t.flag.any() else "stabile fra epoche")
    return st, t, sing


# ---------------------------------------------------------------- check

def check(cat=CAT, check_dir=CHECK, val=VAL, stab=STAB, out=OUT, gdpd=GDPD, sdpd=SDPD, write=True, reps=REPS,
          require_git=True):
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    if require_git and not committed(stab):
        sys.exit("stability outputs not preserved in Git: no recount")
    meta = json.loads((Path(stab) / "META.json").read_text())
    ok("stability product hashes", all(h256(Path(stab) / n) == h for n, h in meta["products_sha256"].items()))
    st = json.loads((Path(stab) / "STABILITY.json").read_text())
    d = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    sealed = pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})      # allowed: the seal is already open
    iso = d[d.record_set == "isolated"].reset_index(drop=True)
    sx = sealed[sealed.record_set == "isolated"].set_index("noaa")
    iso["gamma_mwo"] = sx.loc[iso.noaa, "gamma_deg"].to_numpy()
    iso["gamma_wl"] = wl_gamma(iso, gdpd, sdpd)
    iso["d_wl"] = axial(iso.gamma_mwo - iso.gamma_wl)
    saved_wl = pd.read_csv(Path(stab) / "WL_TILTS.csv", dtype={"noaa": str})
    same_av = (np.isfinite(iso.gamma_wl.to_numpy()) == (saved_wl.wl_status == "ok").to_numpy()).all()
    m = np.isfinite(iso.gamma_wl.to_numpy())
    dev = np.abs(iso.d_wl.to_numpy()[m] - saved_wl.d_wl.to_numpy()[m])
    ok("white-light tilts and d_WL of every record", same_av and (saved_wl.noaa == iso.noaa).all()
       and (dev.max() if len(dev) else 0) < 1e-9, f"{int(m.sum())} available")
    sub = iso[m].reset_index(drop=True)
    cnt = iso.groupby(["epoch", "hemisphere"]).size()
    verif = {(e, h): int(cnt.get((e, h), 0)) >= MINEH for e in ORDER for h in "NS"}
    unver = float(np.mean([not verif[(e, h)] for e, h in zip(iso.epoch, iso.hemisphere)]))
    ok("verifiable epochs and unverifiable share", abs(unver - st["unverifiable_share"]) < 1e-12
       and sorted(f"{e}{h}" for (e, h), v in verif.items() if v) == sorted(st["verifiable"]), unver)
    s1_status, s1_tab, sing = s1_own(sub, verif, reps)
    saved_s1 = pd.read_csv(Path(stab) / "S1_TABLE.csv") if (Path(stab) / "S1_TABLE.csv").stat().st_size > 1 else pd.DataFrame()
    same_tab = len(s1_tab) == len(saved_s1) and (len(s1_tab) == 0 or np.allclose(
        s1_tab[["a", "b", "diff", "lo", "hi"]].to_numpy(float), saved_s1[["a", "b", "diff", "lo", "hi"]].to_numpy(float),
        rtol=1e-9, atol=1e-9, equal_nan=True))
    ok("S1: fit, differences, bootstrap intervals (seed 69 000 001), status", same_tab and s1_status == st["S1"]["status"]
       and sing == st["S1"].get("singular", sing), (s1_status, sing))
    s2 = st["S2"]
    C = s2.get("C")
    if s2.get("state") == "stimato":
        ident, _, X, w = RC.matrix(sub.copy())
        g = RC.projection(X, w)
        beta = float(g @ sub.d_wl.to_numpy())
        key = pd.MultiIndex.from_arrays([sub.CR.astype(int).to_numpy(), sub.hemisphere.to_numpy()])
        codes, uniq = pd.factorize(key)
        cr = np.array([c for c, _ in uniq])
        hh = np.array([h for _, h in uniq])
        lp = np.log(w)
        from types import SimpleNamespace
        se = RC.se_from_saved(SimpleNamespace(**{k: s2[k] for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2")}),
                              sub, g, codes, cr - cr.min(), hh, lp - lp.mean())
        lo, hi = beta - RC.Z * se, beta + RC.Z * se
        if C is not None and -C <= lo and hi <= C:
            status = "scarto contenuto"
        elif lo > 0 or hi < 0:
            status = "dipendente dall'attività"
        else:
            status = "stabilità non determinata"
        ok("S2: beta, SE from the saved parameters, interval and precedence with C",
           ident and abs(beta - s2["beta"]) < 1e-9 * max(1, abs(beta)) and abs(se / s2["se"] - 1) < 1e-6
           and status == s2["status"], (round(beta, 6), status))
    else:
        ok("S2: explicit non-estimated state carried to 'stabilità non determinata'",
           s2["status"] == "stabilità non determinata", s2.get("state"))
    lead = sx.loc[iso.noaa, "leading_sign"].to_numpy()
    hale = sx.loc[iso.noaa, "hale_expected"].to_numpy()
    s3 = iso.assign(agree=(lead == hale)).groupby(["epoch", "hemisphere"]).agree.agg(["size", "mean"]).reset_index()
    s3s = pd.read_csv(Path(stab) / "S3_HALE.csv")
    ok("S3: Hale agreement by epoch and hemisphere", len(s3) == len(s3s) and np.allclose(s3["mean"], s3s["mean"])
       and (s3["size"].to_numpy() == s3s["size"].to_numpy()).all())
    ext = [f for f in ("S1_DPD_SOURCES.csv", "S2_P1.json", "S4_ISOLATION.csv", "S4_DWL_ALL.csv") if (Path(stab) / f).exists()]
    ok("descriptive outputs of §6 present", len(ext) == 4, ext)
    if len(ext) == 4:
        src = {}
        for ln in Path(DAILY if gdpd == GDPD else Path(gdpd) / "dailyDPD1974_2016.txt").read_text().splitlines():
            t = ln.split()
            if ln.startswith("d ") and len(t) >= 12:
                src[f"{t[1]}-{t[2]}-{t[3]}"] = t[7] if t[7].isalpha() else "(none)"
        own = iso.assign(source=[src.get(x, "(missing)") for x in iso.day]).groupby(["epoch", "source"]).size()
        sv = pd.read_csv(Path(stab) / "S1_DPD_SOURCES.csv").set_index(["epoch", "source"]).n
        ok("DPD sources by epoch", own.sort_index().equals(sv.sort_index().astype(own.dtype)))
        al = d[d.record_set == "all"].reset_index(drop=True)
        q = np.nanquantile(al.A_main, [1 / 3, 2 / 3])
        terc = np.searchsorted(q, al.A_main, side="right") + 1
        fr = pd.Series(~al.noaa.isin(set(iso.noaa))).groupby(terc).mean()
        s4i = pd.read_csv(Path(stab) / "S4_ISOLATION.csv")
        ok("S4: non-isolation fraction by activity tercile", np.allclose(fr.to_numpy(), s4i.frac_not_isolated.to_numpy()))
        sa = sealed[sealed.record_set == "all"].set_index("noaa")
        al["d_wl"] = axial(sa.loc[al.noaa, "gamma_deg"].to_numpy() - wl_gamma(al, gdpd, sdpd))
        x = al[np.isfinite(al.d_wl)]
        s4d = pd.read_csv(Path(stab) / "S4_DWL_ALL.csv")
        mi = s4d[(s4d.A_tercile.astype(str) == "all")].set_index("isolated")["mean"]
        own_m = x.groupby("isolated").d_wl.mean()
        ok("S4: d_WL of the 'all' set, isolated vs non-isolated", all(abs(own_m.get(k, np.nan) - mi.get(k, np.nan)) < 1e-9
                                                                       for k in own_m.index), own_m.round(4).to_dict())
    val_acc = json.loads((Path(val) / "ACCEPTANCE.json").read_text())["accepted_15deg"]
    cov = json.loads((Path(cat) / "COVERAGE.json").read_text())["outcome"] == "informativo"
    idf = json.loads((Path(check_dir) / "IDENTIFIABILITY.json").read_text())["joy"]["identifiable"]
    if not cov or not idf:
        outcome = "non concludente"
    elif (not val_acc or s1_status != "stabile fra epoche" or st["S2"]["status"] != "scarto contenuto"
          or unver > MAXUNV):
        outcome = "descrittivo"
    else:
        outcome = "verdetto"
    ok("final rule (verdict possible / descriptive / non concludente)", outcome == st["rule"]["outcome"], outcome)
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
            checks=res, passed=sum(r["ok"] for r in res), total=len(res), partial=reps != REPS,
            stability_meta_sha256=h256(Path(stab) / "META.json"), recounted_outcome=outcome), indent=2) + "\n")
    return all(r["ok"] for r in res)


def selftest():
    """S1 on synthetic data against the analysis module's S1 (subprocess, same seed): identical tables and status."""
    import tempfile
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    with tempfile.TemporaryDirectory() as td:
        code = f"""
import sys, importlib.util, json
sys.argv = ['x']
s = importlib.util.spec_from_file_location('a', {str(ROOT / 'scripts/t3_mwo_analysis.py')!r})
A = importlib.util.module_from_spec(s); s.loader.exec_module(A)
import numpy as np
d = A.synthetic_design()
rng = np.random.default_rng(3)
d['d_wl'] = rng.normal(0, 0.5, len(d))
m = (d.epoch == 'E4').to_numpy(); d.loc[m, 'd_wl'] += 8.0 * d.sinlat[m] / d.sinlat[m].mean()
r, t = A.s1(d, A.epoch_verifiable(d), reps=200)
d.to_csv({td!r} + '/design.csv', index=False)
t.to_csv({td!r} + '/table.csv', index=False)
print(json.dumps(r))
"""
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok("analysis S1 run on a synthetic design (subprocess)", r.returncode == 0, r.stderr[-300:])
        if r.returncode == 0:
            ref = json.loads(r.stdout.strip().splitlines()[-1])
            d = pd.read_csv(Path(td) / "design.csv")
            t_ref = pd.read_csv(Path(td) / "table.csv")
            cnt = d.groupby(["epoch", "hemisphere"]).size()
            verif = {(e, h): int(cnt.get((e, h), 0)) >= MINEH for e in ORDER for h in "NS"}
            st, t, sing = s1_own(d, verif, reps=200)
            ok("own S1 equals the analysis S1 (table, status, singular count)", st == ref["status"]
               and sing == ref["singular"] and np.allclose(t[["a", "b", "diff", "lo", "hi"]].to_numpy(float),
                                                           t_ref[["a", "b", "diff", "lo", "hi"]].to_numpy(float),
                                                           rtol=1e-12, atol=1e-12), (st, ref["status"]))
    ok("axial difference in (-90, 90]", np.allclose(axial([100.0, -100.0, 30.0]), [-80.0, 80.0, 30.0]))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
