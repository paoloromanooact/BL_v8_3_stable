"""Independent recount of the T3-on-MWO stability stage (S1-S4 of docs/PROTOCOL_T3_MWO.md §6) before beta3 is
estimated. Does not import scripts/t3_mwo_analysis.py nor scripts/t3_mwo_stability_extras.py; reuses only the
independent recount helpers of scripts/t3_mwo_analysis_recount.py (columns, QR projection, SE from saved parameters).

Requires the stability outputs preserved in Git (they exist only after the seal was opened by the chain). Rebuilds:
white-light tilts and d_WL; S1 (fit, differences, block bootstrap with the frozen seed 69 000 001, percentile intervals,
flags, status); S2 (beta from the own projection, SE from the saved parameters of M, interval, precedence with C);
S2 by hemisphere when estimated; S3 (Hale agreement); S4 (selection table, non-isolation fraction, d_WL of the 'all'
set); the DPD sources by epoch; S2 against P1 (count and median); the final rule. Receipt bound to the SHA-256 of the
stability META: results/T3_MWO_STABILITY_R4_RECOUNT/RECEIPT.json.

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

CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK_R4"
VAL = ROOT / "results/T3_MWO_VALIDATION_R4"
STAB = ROOT / "results/T3_MWO_STABILITY_R4"
OUT = ROOT / "results/T3_MWO_STABILITY_R4_RECOUNT"
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


# ---------------------------------------------------------------- chain of the seal (own reader of the metadata)

CHAIN = dict(cat=CAT, cat_recount=ROOT / "results/T3_MWO_CATALOGUE_R4_RECOUNT", check=CHECK,
             check_recount=ROOT / "results/T3_MWO_DESIGN_CHECK_R4_RECOUNT", val=VAL,
             val_recount=ROOT / "results/T3_MWO_VALIDATION_R4_RECOUNT", val_read=ROOT / "results/T3_MWO_VALIDATION_R4_READING")


def receipt_complete(path, key, meta):
    r = json.loads(Path(path).read_text())
    p_, t_, c = r.get("passed"), r.get("total"), r.get("checks")
    return (isinstance(p_, int) and isinstance(t_, int) and t_ > 0 and p_ == t_ and isinstance(c, list)
            and len(c) == t_ and all(isinstance(x, dict) and x.get("ok") is True for x in c)
            and r.get("partial", False) is False and r.get(key) == h256(meta))


def chain_problems(stab, ch=None):
    """Prerequisites of the seal and the links recorded by the stability writer (Codex's review, point 3)."""
    ch = dict(CHAIN, **(ch or {}))
    out = []
    for k in ("cat", "cat_recount", "check", "check_recount", "val", "val_recount", "val_read"):
        if not committed(ch[k]):
            out.append(f"{k} not preserved in Git")
    if out:
        return out
    for rec, key, meta in (("cat_recount", "catalogue_meta_sha256", Path(ch["cat"]) / "META.json"),
                           ("check_recount", "design_check_meta_sha256", Path(ch["check"]) / "META.json"),
                           ("val_recount", "validation_meta_sha256", Path(ch["val"]) / "META.json")):
        if not receipt_complete(Path(ch[rec]) / "RECEIPT.json", key, meta):
            out.append(f"{rec} receipt not complete or not bound")
    if json.loads((Path(ch["check"]) / "META.json").read_text()).get("catalogue_meta_sha256") != h256(Path(ch["cat"]) / "META.json"):
        out.append("design check not bound to the current catalogue")
    if json.loads((Path(ch["val"]) / "META.json").read_text()).get("design_check_meta_sha256") != h256(Path(ch["check"]) / "META.json"):
        out.append("validation not bound to the current design check")
    if json.loads((Path(ch["val"]) / "ACCEPTANCE.json").read_text()).get("problems"):
        out.append("validation technically invalid: no opening (a negative but valid validation is allowed)")
    rd = json.loads((Path(ch["val_read"]) / "READ.json").read_text())
    if rd.get("acceptance_sha256") != h256(Path(ch["val"]) / "ACCEPTANCE.json") or \
            rd.get("recount_receipt_sha256") != h256(Path(ch["val_recount"]) / "RECEIPT.json"):
        out.append("reading record not bound")
    sm = json.loads((Path(stab) / "META.json").read_text())
    for key, meta in (("catalogue_meta_sha256", Path(ch["cat"]) / "META.json"),
                      ("design_check_meta_sha256", Path(ch["check"]) / "META.json"),
                      ("validation_meta_sha256", Path(ch["val"]) / "META.json"),
                      ("reading_sha256", Path(ch["val_read"]) / "READ.json")):
        if sm.get(key) != h256(meta):
            out.append(f"stability META not bound to the current {key}")
    return out


# ---------------------------------------------------------------- P1 (own reader of the catalogue)

P1_CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
PHI_MIN, NPIX_MIN = 1e21, 20            # sample S of P2 §2 (checked against run_p2 in the selftest)


def p1_records(path=P1_CATALOGUE):
    from astropy.time import Time
    c = pd.read_csv(path, low_memory=False)
    c = c[c.cycle.isin([24, 25]) & (c.role != "control") & (c.valid_bl == 1) & (c.npos >= NPIX_MIN)
          & (c.nneg >= NPIX_MIN) & (c.phi_mx >= PHI_MIN) & (c.cycle_state != "AMBIGUOUS")]
    c = c[pd.to_numeric(c.NOAA_AR, errors="coerce") > 0].copy()
    t = pd.to_datetime(c.T_REC.str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    utc = Time(list(np.array(t.dt.to_pydatetime())), scale="tai").utc.to_datetime()
    c["day"] = [u.strftime("%Y-%m-%d") for u in utc]
    c["noaa"] = c.NOAA_AR.astype(float).astype(int).astype(str)
    c["gamma"] = np.sign(c.lat_mean_deg) * np.degrees(np.arcsin(np.clip(c.sintilt, -1, 1)))
    return c[["noaa", "day", "gamma"]].drop_duplicates(["noaa", "day"])


# ---------------------------------------------------------------- S2-type fit recomputed from saved parameters

def s2_recompute(sub, saved, C=None):
    """beta (own projection), SE (saved parameters of M), bounds; state consistency; status with C when given."""
    from types import SimpleNamespace
    if len(sub) == 0:
        return saved.get("state") == "campione vuoto", dict(state="campione vuoto")
    ident, _, X, w = RC.matrix(sub.copy())
    if not ident:
        return saved.get("state") == "non identificabile", dict(state="non identificabile")
    if saved.get("state") == "errore di M":
        return True, dict(state="errore di M")            # an M failure cannot be recomputed without M: explicit state
    if saved.get("state") != "stimato":
        return False, dict(state="?")
    try:                                        # frozen REML domain of M (P2f) and finite saved quantities (Codex)
        par_v = {k: float(saved[k]) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2", "se", "lo", "hi", "beta")}
    except (KeyError, TypeError, ValueError):
        return False, dict(state="parametri mancanti")
    if not (all(math.isfinite(v) for v in par_v.values()) and 0.0 <= par_v["phi"] <= 0.98
            and abs(par_v["kappa"]) <= 0.98 and par_v["sigma_x2"] > 0 and par_v["se"] > 0):
        return False, dict(state="parametri fuori dominio o non finiti")
    g = RC.projection(X, w)
    beta = float(g @ sub.d_wl.to_numpy())
    key = pd.MultiIndex.from_arrays([sub.CR.astype(int).to_numpy(), sub.hemisphere.to_numpy()])
    codes, uniq = pd.factorize(key)
    cr = np.array([c for c, _ in uniq])
    hh = np.array([h for _, h in uniq])
    lp = np.log(w)
    par = SimpleNamespace(**{k: float(saved[k]) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2")})
    se = RC.se_from_saved(par, sub, g, codes, cr - cr.min(), hh, lp - lp.mean())
    if not (math.isfinite(se) and se > 0):
        return False, dict(state="SE ricostruito non finito")
    lo, hi = beta - RC.Z * se, beta + RC.Z * se
    out = dict(state="stimato", n=len(sub), beta=beta, se=se, lo=lo, hi=hi)
    good = (int(saved.get("n", -1)) == len(sub) and all(abs(out[k] - float(saved[k])) <= 1e-9 * max(1.0, abs(out[k]))
                                                         for k in ("beta", "lo", "hi")) and abs(se / float(saved["se"]) - 1) < 1e-6)
    if C is not None:
        if -C <= lo and hi <= C:
            out["status"] = "scarto contenuto"
        elif lo > 0 or hi < 0:
            out["status"] = "dipendente dall'attività"
        else:
            out["status"] = "stabilità non determinata"
        out["distinguishable"] = bool(lo > 0 or hi < 0)
    return good, out


def same_table(a, b, keys, num, exact=()):
    """Same keys in the same order, numeric columns equal within 1e-9 (NaN equal), exact columns identical."""
    if len(a) != len(b) or list(a[keys].astype(str).itertuples(index=False)) != list(b[keys].astype(str).itertuples(index=False)):
        return False
    if num and not np.allclose(a[num].to_numpy(float), b[num].to_numpy(float), rtol=1e-9, atol=1e-9, equal_nan=True):
        return False
    return all((a[c].astype(str).to_numpy() == b[c].astype(str).to_numpy()).all() for c in exact)


def terc(x):
    q = np.nanquantile(x, [1 / 3, 2 / 3])
    return np.searchsorted(q, x, side="right") + 1


# ---------------------------------------------------------------- check

def check(cat=CAT, check_dir=CHECK, val=VAL, stab=STAB, out=OUT, gdpd=GDPD, sdpd=SDPD, write=True, reps=REPS,
          require_git=True, chain=None, p1=None, s1_cache=None):
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    if require_git:
        cp = chain_problems(stab, dict(chain or {}, cat=cat, check=check_dir, val=val))
        ok("seal chain: prerequisites committed, receipts complete and bound, stability bound to current inputs", not cp, cp)
        if cp:
            sys.exit(f"seal chain not satisfied: {cp}")
    meta = json.loads((Path(stab) / "META.json").read_text())
    ok("stability product hashes", all(h256(Path(stab) / n) == h for n, h in meta["products_sha256"].items()))
    st = json.loads((Path(stab) / "STABILITY.json").read_text())
    d = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    sealed = pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})      # after the chain check above
    iso = d[d.record_set == "isolated"].reset_index(drop=True)
    al = d[d.record_set == "all"].reset_index(drop=True)
    sx = sealed[sealed.record_set == "isolated"].set_index("noaa")
    iso["gamma_mwo"] = sx.loc[iso.noaa, "gamma_deg"].to_numpy()
    iso["gamma_wl"] = wl_gamma(iso, gdpd, sdpd)
    iso["d_wl"] = axial(iso.gamma_mwo - iso.gamma_wl)
    w0 = pd.read_csv(Path(stab) / "WL_TILTS.csv", dtype={"noaa": str})
    m = np.isfinite(iso.gamma_wl.to_numpy())
    ok("white-light tilts, status and d_WL of every record", (w0.noaa.tolist() == iso.noaa.tolist())
       and ((w0.wl_status == "ok").to_numpy() == m).all()
       and np.allclose(w0.gamma_wl.to_numpy(float)[m], iso.gamma_wl.to_numpy()[m], atol=1e-9)
       and np.allclose(w0.d_wl.to_numpy(float)[m], iso.d_wl.to_numpy()[m], atol=1e-9), f"{int(m.sum())} available")
    sub = iso[m].reset_index(drop=True)
    cnt = iso.groupby(["epoch", "hemisphere"]).size()
    verif = {(e, h): int(cnt.get((e, h), 0)) >= MINEH for e in ORDER for h in "NS"}
    unver = float(np.mean([not verif[(e, h)] for e, h in zip(iso.epoch, iso.hemisphere)]))
    ok("verifiable epochs, unverifiable share, subset size", abs(unver - st["unverifiable_share"]) < 1e-12
       and sorted(f"{e}{h}" for (e, h), v in verif.items() if v) == sorted(st["verifiable"])
       and st["subset"]["n"] == len(sub), unver)
    s1_status, s1_tab, sing = s1_cache if s1_cache is not None else s1_own(sub, verif, reps)
    p1t = Path(stab) / "S1_TABLE.csv"
    saved_s1 = pd.read_csv(p1t) if p1t.stat().st_size > 1 else pd.DataFrame(columns=s1_tab.columns)
    ok("S1: every (epoch, hemisphere) with a, b, diff, bounds and flag; status; singular count; reps and seed",
       same_table(s1_tab, saved_s1, ["epoch", "hemisphere"], ["a", "b", "diff", "lo", "hi"], ["flag"])
       and s1_status == st["S1"]["status"] and sing == st["S1"].get("singular") and st["S1"].get("reps") == reps
       and st["S1"].get("seed") == SEED, (s1_status, sing))
    C = None
    if len(sub):
        i_s, _, Xs, ws = RC.matrix(sub.copy())
        C = 0.5 * abs(RC.ramp_true(sub, RC.projection(Xs, ws), 0.2)) if i_s else None
    tg = json.loads((Path(check_dir) / "TARGETS.json").read_text())
    same_c = lambda x: (x is None and C is None) or (x is not None and C is not None and abs(x - C) <= 1e-9 * max(1, C))  # noqa: E731
    ok("C recomputed on the white-light subset, equal to TARGETS and to STABILITY", same_c(tg.get("C"))
       and same_c(st["S2"].get("C")), C)
    s2 = st["S2"]
    good, own = s2_recompute(sub, s2, C)
    own_status = own.get("status", "stabilità non determinata") if own["state"] == "stimato" else "stabilità non determinata"
    if C is None:
        own_status = "stabilità non determinata"
    ok("S2: state, n, beta, SE, bounds; status and 'distinguishable from zero' from the recomputed C",
       good and own_status == s2["status"] and (own["state"] != "stimato"
                                                or bool(own.get("distinguishable")) == bool(s2.get("distinguishable_from_zero"))),
       (own.get("state"), own_status))
    hem_ok = []
    for h in "NS":
        g_, _ = s2_recompute(sub[sub.hemisphere == h].reset_index(drop=True), s2.get("by_hemisphere", {}).get(h, {}))
        hem_ok.append(g_)
    ok("S2 by hemisphere: state, n, beta, SE, bounds", all(hem_ok), hem_ok)
    lead = sx.loc[iso.noaa, "leading_sign"].to_numpy()
    hale = sx.loc[iso.noaa, "hale_expected"].to_numpy()
    s3 = iso.assign(agree=(lead == hale)).groupby(["epoch", "hemisphere"]).agree.agg(["size", "mean"]).reset_index()
    ok("S3: Hale agreement with its (epoch, hemisphere) labels", same_table(s3, pd.read_csv(Path(stab) / "S3_HALE.csv"),
                                                                            ["epoch", "hemisphere"], ["size", "mean"]))
    q = np.nanquantile(iso.A_main, [1 / 3, 2 / 3])
    s4 = iso.assign(A_tercile=np.searchsorted(q, iso.A_main, side="right") + 1).groupby("A_tercile").agg(
        n=("noaa", "size"), mean_rank=("rank", "mean"), mean_abs_lcm=("abs_lcm", "mean"),
        mean_neighbours_day=("n_neighbours", "mean")).reset_index()
    ok("S4 selection table", same_table(s4, pd.read_csv(Path(stab) / "S4.csv"), ["A_tercile"],
                                        ["n", "mean_rank", "mean_abs_lcm", "mean_neighbours_day"]))
    need = ("S1_DPD_SOURCES.csv", "S2_P1.json", "S2_P1_MATCHED.csv", "S4_ISOLATION.csv", "S4_DWL_ALL.csv")
    present = [f for f in need if (Path(stab) / f).exists()]
    ok("descriptive outputs of §6 present (all five)", len(present) == 5, present)
    if len(present) == 5:
        src = {}
        for ln in (Path(gdpd) / "dailyDPD1974_2016.txt").read_text().splitlines():
            t = ln.split()
            if ln.startswith("d ") and len(t) >= 12:
                src[f"{t[1]}-{t[2]}-{t[3]}"] = t[7] if t[7].isalpha() else "(none)"
        sb = iso.assign(source=[src.get(x, "(missing)") for x in iso.day]).groupby(["epoch", "source"]).size().rename("n").reset_index()
        sb["share"] = sb.n / sb.groupby("epoch").n.transform("sum")
        sb = sb.sort_values(["epoch", "n"], ascending=[True, False], kind="stable").reset_index(drop=True)
        sv = pd.read_csv(Path(stab) / "S1_DPD_SOURCES.csv")
        ok("DPD sources by epoch: labels, counts and shares", same_table(sb.sort_values(["epoch", "source"]).reset_index(drop=True),
                                                                         sv.sort_values(["epoch", "source"]).reset_index(drop=True),
                                                                         ["epoch", "source"], ["n", "share"]))
        s4i = al.assign(A_tercile=terc(al.A_main.to_numpy()), iso_rec=al.noaa.isin(set(iso.noaa))).groupby("A_tercile").agg(
            n_groups=("noaa", "size"), frac_not_isolated=("iso_rec", lambda v: 1 - v.mean()), mean_rank=("rank", "mean"),
            mean_abs_lcm=("abs_lcm", "mean")).reset_index()
        ok("S4: non-isolation fraction, rank and |LCM| by activity tercile",
           same_table(s4i, pd.read_csv(Path(stab) / "S4_ISOLATION.csv"), ["A_tercile"],
                      ["n_groups", "frac_not_isolated", "mean_rank", "mean_abs_lcm"]))
        sa = sealed[sealed.record_set == "all"].set_index("noaa")
        al["d_wl"] = axial(sa.loc[al.noaa, "gamma_deg"].to_numpy() - wl_gamma(al, gdpd, sdpd))
        x = al[np.isfinite(al.d_wl)].copy()
        x["A_tercile"] = terc(x.A_main.to_numpy())
        rows = []
        for (iv, tt), g in [((i, "all"), x[x.isolated == i]) for i in (True, False)] + \
                [((i, k), x[(x.isolated == i) & (x.A_tercile == k)]) for i in (True, False) for k in (1, 2, 3)]:
            v = g.d_wl.to_numpy(float)
            rows.append(dict(isolated=str(iv), A_tercile=str(tt), n=len(v), median=float(np.median(v)) if len(v) else np.nan,
                             mean=float(v.mean()) if len(v) else np.nan,
                             s_over_sqrt_n=float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else np.nan))
        own_d = pd.DataFrame(rows)
        sd = pd.read_csv(Path(stab) / "S4_DWL_ALL.csv", dtype={"isolated": str, "A_tercile": str})
        ok("S4: d_WL of the 'all' set by isolation and tercile (n, median, mean, s/sqrt n)",
           same_table(own_d, sd, ["isolated", "A_tercile"], ["n", "median", "mean", "s_over_sqrt_n"]))
        p1r = p1_records() if p1 is None else p1
        xm = iso[(iso.day >= "2010-05-01") & (iso.day < "2013-01-01")].merge(p1r, on=["noaa", "day"], how="inner")
        xm["d_wl"] = axial(xm.gamma_mwo - xm.gamma)
        mt = pd.read_csv(Path(stab) / "S2_P1_MATCHED.csv", dtype={"noaa": str})
        sp = json.loads((Path(stab) / "S2_P1.json").read_text())
        okm = (mt[["noaa", "day"]].astype(str).values.tolist() == xm[["noaa", "day"]].astype(str).values.tolist()
               and np.allclose(mt.d_p1.to_numpy(float), xm.d_wl.to_numpy(float), atol=1e-9))
        okp = sp["n_matched"] == len(xm) and ((len(xm) == 0 and sp["median_d"] is None)
                                              or (len(xm) and abs(sp["median_d"] - float(np.median(xm.d_wl))) < 1e-9))
        gp, _ = s2_recompute(xm.reset_index(drop=True), sp["fit"]) if len(xm) else (sp["fit"].get("state") == "campione vuoto", None)
        ok("S2 against P1: matched pairs (own P1 reader), differences, count, median and fit", okm and okp and gp,
           (len(xm), okm, okp, gp))
    val_acc = json.loads((Path(val) / "ACCEPTANCE.json").read_text())["accepted_15deg"]
    cov = json.loads((Path(cat) / "COVERAGE.json").read_text())["outcome"] == "informativo"
    idf = json.loads((Path(check_dir) / "IDENTIFIABILITY.json").read_text())["joy"]["identifiable"]
    if not cov or not idf:
        outcome = "non concludente"
    elif not val_acc or s1_status != "stabile fra epoche" or own_status != "scarto contenuto" or unver > MAXUNV:
        outcome = "descrittivo"
    else:
        outcome = "verdetto"
    ok("final rule from the recomputed S1, S2 and C", outcome == st["rule"]["outcome"], outcome)
    partial = (reps != REPS) or (not require_git) or (s1_cache is not None)
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
            checks=res, passed=sum(r["ok"] for r in res), total=len(res), partial=partial,
            stability_meta_sha256=h256(Path(stab) / "META.json"), recounted_outcome=outcome), indent=2) + "\n")
    return all(r["ok"] for r in res)


def _fixture(td):
    """Synthetic catalogue, DPD files and stability outputs, built as in scripts/t3_mwo_stability_recount_review_probe.py
    (Codex), with the P1 records injected. Returns (kwargs for check, frames, save function, P1 records)."""
    from types import SimpleNamespace

    def load(n):
        sp = importlib.util.spec_from_file_location(n, ROOT / "scripts" / f"{n}.py")
        mod = importlib.util.module_from_spec(sp)
        sys.modules[n] = mod
        sp.loader.exec_module(mod)
        return mod
    A, EX = load("t3_mwo_analysis"), load("t3_mwo_stability_extras")

    def line(kind, day, noaa, lat, lon, area):
        z = list(" " * 96)
        for at, txt in ((0, f"{kind} {day:%Y %m %d} 12 00 00"), (22, f"{noaa:>6}"), (53, f"{area:5d}"), (59, f"{lat:6.2f}"),
                        (66, f"{lon:6.2f}"), (73, f"{0.:6.2f}")):
            z[at:at + len(txt)] = txt
        return "".join(z)
    cat, chk, val, stab, data = (td / x for x in ("cat", "check", "val", "stab", "dpd"))
    for q in (cat, chk, val, stab, data):
        q.mkdir()
    rows, groups, spots, daily = [], [], [], []
    for i in range(124):
        day = pd.Timestamp("2011-01-01") + pd.Timedelta(days=i)
        hem = "N" if i % 2 == 0 else "S"
        lat = (1 if hem == "N" else -1) * (10 + i % 7)
        sg = 1 if hem == "N" else -1
        noaa = str(10000 + i)
        groups.append(line("g", day, noaa, lat, 100., 200))
        spots += [line("s", day, noaa, lat - sg * .5, 103., 100), line("s", day, noaa, lat + sg * .5, 97., 100)]
        daily.append(f"d {day:%Y %m %d} 12 00 00 GYUL 1 2 3 4 0 0 0")
        rows.append(dict(record_set="all", noaa=noaa, day=day.strftime("%Y-%m-%d"), cycle=24, epoch="E8", hemisphere=hem,
                         CR=2106 + i // 10, A_main=.5 + (i // 10) / 6, sinlat=math.sin(math.radians(abs(lat))),
                         phi_mwo=1e21 * (1 + (i % 5) / 10), isolated=i < 120, n_neighbours=0 if i < 120 else 1, rank=1,
                         abs_lcm=4.))
    al = pd.DataFrame(rows)
    iso = al.iloc[:120].copy().assign(record_set="isolated").reset_index(drop=True)
    pd.concat([iso, al], ignore_index=True).to_csv(cat / "DESIGN.csv", index=False)
    (cat / "COVERAGE.json").write_text(json.dumps({"outcome": "informativo"}))
    for y in range(1974, 2013):
        (data / f"gDPD{y}.txt").write_text("\n".join(groups) if y == 2011 else "")
    (data / "sDPD2011.txt").write_text("\n".join(spots))
    (data / "dailyDPD1974_2016.txt").write_text("\n".join(daily))
    wl = A.wl_for_records
    A.wl_for_records = lambda frame: wl(frame, gdpd=data, sdpd=data)
    ident, _, X, w = RC.matrix(iso)
    g = RC.projection(X, w)
    C = .5 * abs(RC.ramp_true(iso, g, .2))
    (chk / "IDENTIFIABILITY.json").write_text(json.dumps({"joy": {"identifiable": bool(ident)}}))
    (chk / "TARGETS.json").write_text(json.dumps({"C": C, "delta_beta_20": -2 * C}))
    (val / "ACCEPTANCE.json").write_text(json.dumps({"accepted_15deg": True}))
    gwl, st = A.wl_for_records(iso)
    gall, _ = A.wl_for_records(al)
    beta = 2 * C
    iso["gamma_mwo"] = gwl + beta * (iso.A_main - 1) * iso.sinlat
    iso["gamma_wl"], iso["wl_status"] = gwl, st
    iso["d_wl"] = A.axial(iso.gamma_mwo - iso.gamma_wl)
    al["gamma_mwo"] = gall + beta * (al.A_main - 1) * al.sinlat
    sealed = pd.DataFrame([dict(record_set=lab, noaa=r.noaa, gamma_deg=r.gamma_mwo, leading_sign=1, hale_expected=1)
                           for lab, fr in (("isolated", iso), ("all", al)) for r in fr.itertuples()])
    sealed.to_csv(cat / "SEALED.csv.gz", index=False)
    pars = dict(var_a=math.log(.0001), var_b=0., phi=.5, kappa=.1, sigma_x2=.0001)

    def fit(fr):
        _, _, xh, wh = RC.matrix(fr.copy())
        gh = RC.projection(xh, wh)
        kh = pd.MultiIndex.from_arrays([fr.CR, fr.hemisphere])
        ch, uh = pd.factorize(kh)
        crh = np.array([x for x, _ in uh])
        lph = np.log(wh)
        seh = RC.se_from_saved(SimpleNamespace(**pars), fr, gh, ch, crh - crh.min(), np.array([h for _, h in uh]),
                               lph - lph.mean())
        bh = float(gh @ fr.d_wl.to_numpy())
        return dict(state="stimato", n=len(fr), beta=bh, se=seh, lo=bh - RC.Z * seh, hi=bh + RC.Z * seh, **pars)
    s2 = fit(iso)
    status, nonzero = A.s2_outcome(s2["lo"], s2["hi"], C)
    s2.update(status=status, distinguishable_from_zero=nonzero, C=C,
              by_hemisphere={h: fit(iso[iso.hemisphere == h].reset_index(drop=True)) for h in "NS"})
    vr = A.epoch_verifiable(iso)
    s1, t1 = A.s1(iso, vr, reps=REPS)
    rule = A.final_rule(s1["status"], status, 0.0, True, True, True)
    result = dict(S1=s1, S2=s2, unverifiable_share=0.0, verifiable=sorted(f"{e}{h}" for (e, h), v in vr.items() if v),
                  subset={"n": len(iso), "share": 1.}, rule={"outcome": rule[0], "reasons": rule[1]})
    p1 = pd.DataFrame({"noaa": [iso.noaa.iloc[0]], "day": [iso.day.iloc[0]], "gamma": [iso.gamma_mwo.iloc[0] - .3]})
    EX.daily_sources = lambda path: dict(zip(al.day, ["GYUL"] * len(al)))
    EX.p1_records = lambda: p1
    frames = {"STABILITY.json": result, "S1_TABLE.csv": t1,
              "S3_HALE.csv": iso.assign(agree=True).groupby(["epoch", "hemisphere"]).agree.agg(["size", "mean"]).reset_index(),
              "S4.csv": A.s4_table(iso), "WL_TILTS.csv": iso[["noaa", "day", "epoch", "hemisphere", "wl_status", "gamma_wl", "d_wl"]],
              **EX.extras(A, iso, sealed, al)}

    def save():
        for name, obj in frames.items():
            if isinstance(obj, pd.DataFrame):
                obj.to_csv(stab / name, index=False)
            else:
                (stab / name).write_text(json.dumps(obj, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
        (stab / "META.json").write_text(json.dumps({"products_sha256": {q.name: h256(q) for q in stab.iterdir()
                                                                         if q.name != "META.json"}}))
    save()
    kw = dict(cat=cat, check_dir=chk, val=val, stab=stab, gdpd=data, sdpd=data, require_git=False, p1=p1, write=False)
    return kw, frames, save, iso, vr


def selftest():
    """Baseline of Codex's synthetic fixture passes; each of Codex's mutations, and more, is refused."""
    import tempfile
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import run_p2
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    ok("own P1 sample S constants equal run_p2", (PHI_MIN, NPIX_MIN) == (run_p2.PHI_MIN, run_p2.NPIX_MIN))
    with tempfile.TemporaryDirectory() as td:
        kw, fr, save, iso, vr = _fixture(Path(td))
        sub = iso[np.isfinite(iso.gamma_wl)].reset_index(drop=True)
        cache = s1_own(sub.drop(columns=["gamma_mwo", "gamma_wl", "wl_status"]).assign(d_wl=sub.d_wl), vr, REPS)
        ok("baseline (synthetic, Git disabled -> partial receipt) passes", check(**kw, s1_cache=cache))
        st = fr["STABILITY.json"]
        snap = json.loads(json.dumps(st, default=lambda x: x.item() if hasattr(x, "item") else str(x)))

        def restore():
            st.clear()
            st.update(json.loads(json.dumps(snap)))

        def mut(label, change, back):
            change()
            save()
            refused = not check(**kw, s1_cache=cache)
            back()
            save()
            ok(f"mutation refused: {label}", refused)
        mut("C inflated so that S2 becomes contained and the rule a verdict",
            lambda: (st["S2"].update(C=100 * st["S2"]["C"], status="scarto contenuto"),
                     st["rule"].update(outcome="verdetto", reasons="")), restore)
        mut("S2 bounds", lambda: st["S2"].update(lo=999., hi=1000.), restore)
        mut("S2 'distinguishable from zero'", lambda: st["S2"].update(distinguishable_from_zero=not st["S2"]["distinguishable_from_zero"]),
            restore)
        mut("S2 hemisphere beta", lambda: st["S2"]["by_hemisphere"]["N"].update(beta=999.), restore)
        p1 = fr["S2_P1.json"]
        p1s = json.loads(json.dumps(p1))
        mut("P1 count and median", lambda: p1.update(n_matched=999, median_d=999.), lambda: (p1.clear(), p1.update(p1s)))
        t = fr["S4_DWL_ALL.csv"]
        o = t["median"].copy()
        mut("S4 medians", lambda: t.__setitem__("median", 999.), lambda: t.__setitem__("median", o))
        t3 = fr["S3_HALE.csv"]
        e3 = t3.epoch.copy()
        mut("S3 epoch labels", lambda: t3.__setitem__("epoch", "E1"), lambda: t3.__setitem__("epoch", e3))
        t1 = fr["S1_TABLE.csv"]
        f1 = t1.flag.copy()
        mut("S1 flags", lambda: t1.__setitem__("flag", ~f1.astype(bool)), lambda: t1.__setitem__("flag", f1))
        t4 = fr["S4_ISOLATION.csv"]
        f4 = t4.frac_not_isolated.copy()
        mut("S4 non-isolation fraction", lambda: t4.__setitem__("frac_not_isolated", f4 + .1),
            lambda: t4.__setitem__("frac_not_isolated", f4))
        sb = fr["S1_DPD_SOURCES.csv"]
        sh = sb["share"].copy()
        mut("DPD source shares", lambda: sb.__setitem__("share", sh * .5), lambda: sb.__setitem__("share", sh))
        mm = fr["S2_P1_MATCHED.csv"]
        dm = mm.d_p1.copy()
        mut("P1 matched differences", lambda: mm.__setitem__("d_p1", dm + 1), lambda: mm.__setitem__("d_p1", dm))
        mut("rule outcome alone", lambda: st["rule"].update(outcome="verdetto"), restore)
        for k, v in (("phi", -0.1), ("phi", 0.99), ("kappa", 0.99), ("sigma_x2", 0.0), ("var_b", float("nan"))):
            mut(f"S2 variance parameter {k}={v} outside the frozen domain (SE and bounds left coherent)",
                lambda k=k, v=v: st["S2"].update({k: v}), restore)
        mut("S2 hemisphere parameter phi=-0.1", lambda: st["S2"]["by_hemisphere"]["S"].update(phi=-0.1), restore)
        (Path(td) / "stab/S2_P1_MATCHED.csv").unlink()
        meta = json.loads((Path(td) / "stab/META.json").read_text())
        meta["products_sha256"].pop("S2_P1_MATCHED.csv")
        (Path(td) / "stab/META.json").write_text(json.dumps(meta))
        ok("mutation refused: S2_P1_MATCHED.csv missing", not check(**kw, s1_cache=cache))
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ch = {k: td / k for k in ("cat", "cat_recount", "check", "check_recount", "val", "val_recount", "val_read")}
        stb = td / "stab"
        for q in list(ch.values()) + [stb]:
            q.mkdir()
        put = lambda k, f, x: (ch[k] / f).write_text(json.dumps(x))                       # noqa: E731
        full = lambda key, meta: {"passed": 2, "total": 2, "partial": False, key: h256(meta),  # noqa: E731
                                  "checks": [{"ok": True}, {"ok": True}]}

        def build(val_bound=True, problems=()):
            put("cat", "META.json", {"r": 1})
            put("check", "META.json", {"catalogue_meta_sha256": h256(ch["cat"] / "META.json")})
            put("val", "META.json", {"design_check_meta_sha256": h256(ch["check"] / "META.json") if val_bound else "old"})
            put("val", "ACCEPTANCE.json", {"accepted_15deg": False, "problems": list(problems)})
            put("cat_recount", "RECEIPT.json", full("catalogue_meta_sha256", ch["cat"] / "META.json"))
            put("check_recount", "RECEIPT.json", full("design_check_meta_sha256", ch["check"] / "META.json"))
            put("val_recount", "RECEIPT.json", full("validation_meta_sha256", ch["val"] / "META.json"))
            put("val_read", "READ.json", {"acceptance_sha256": h256(ch["val"] / "ACCEPTANCE.json"),
                                          "recount_receipt_sha256": h256(ch["val_recount"] / "RECEIPT.json")})
            (stb / "META.json").write_text(json.dumps({k: h256(m) for k, m in (
                ("catalogue_meta_sha256", ch["cat"] / "META.json"), ("design_check_meta_sha256", ch["check"] / "META.json"),
                ("validation_meta_sha256", ch["val"] / "META.json"), ("reading_sha256", ch["val_read"] / "READ.json"))}))
        with patch(f"{__name__}.committed", return_value=True):
            build()
            c_ok = chain_problems(stb, ch)
            build(val_bound=False, problems=["incomplete grid"])
            c_bad = chain_problems(stb, ch)
            build(problems=["incomplete grid"])
            c_tech = chain_problems(stb, ch)
    ok("seal chain: negative but valid validation accepted (descriptive path)", c_ok == [], c_ok)
    ok("seal chain: validation bound to an old design check and technically incomplete refused",
       any("old" in x or "design check" in x for x in c_bad) and any("technically" in x for x in c_bad), c_bad)
    ok("seal chain: technically invalid validation refused even when bound", any("technically" in x for x in c_tech), c_tech)
    ok("axial difference in (-90, 90]", np.allclose(axial([100.0, -100.0, 30.0]), [-80.0, 80.0, 30.0]))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
