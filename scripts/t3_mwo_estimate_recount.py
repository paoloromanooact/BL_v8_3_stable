"""Independent recount of the T3-on-MWO estimate (step 11), required before the catalogue release (Codex, 20 Nov).
Does not import scripts/t3_mwo_analysis.py; reuses only the independent helpers of t3_mwo_analysis_recount.py
(QR projection, SE from saved parameters of M).

For the main analysis and each sensitivity of the protocol §3 it rebuilds, with its own code: the record subset (set,
filters, finite activity), the columns (cycle x hemisphere Joy terms, epoch x hemisphere shifts in Joy or additive form or
none, activity column), the reduction of redundant columns, beta3 from the own projection, SE from the saved parameters
of M, bounds and verdict; explicit states (empty sample, not identifiable) must match. FINAL: outcome from the recounted
stability rule (STABILITY.json, whose own recount receipt must be complete and bound), 'non concludente' when the main
beta3 is not estimated, verdict only for 'verdetto'. Receipt bound to the estimate META:
results/T3_MWO_ESTIMATE_R4_RECOUNT/RECEIPT.json.

    .venv/bin/python scripts/t3_mwo_estimate_recount.py --selftest
    .venv/bin/python scripts/t3_mwo_estimate_recount.py --check
"""
import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("t3_rc", ROOT / "scripts/t3_mwo_analysis_recount.py")
RC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(RC)
CAT = ROOT / "results/T3_MWO_CATALOGUE_R4"
STAB = ROOT / "results/T3_MWO_STABILITY_R4"
STAB_RC = ROOT / "results/T3_MWO_STABILITY_R4_RECOUNT"
EST = ROOT / "results/T3_MWO_ESTIMATE_R4"
OUT = ROOT / "results/T3_MWO_ESTIMATE_R4_RECOUNT"
CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK_R4"
VAL = ROOT / "results/T3_MWO_VALIDATION_R4"
VAL_READ = ROOT / "results/T3_MWO_VALIDATION_R4_READING"
ORDER = RC.ORDER
MINIMA = ("1976-03-01", "1986-09-01", "1996-08-01", "2008-12-01")
ANALYSES = {  # own definition of protocol §3 (main and sensitivities)
    "main": {}, "additive epoch terms": dict(form="additive"), "no epoch terms": dict(form="none"),
    "weights = DPD area": dict(weights="dpd_area"), "all records": dict(set_name="all"), "R1 only": dict(filt="R1"),
    "first candidate day only": dict(filt="rank1"), "before 2010-05": dict(filt="pre_hmi"),
    "excluding +-1 yr from minima": dict(filt="minima"), "activity (a) Gyula/Debrecen": dict(act="A_own"),
    "activity (b) SILSO hemispheric": dict(act="A_silso_hem"), "activity (c) SILSO split": dict(act="A_silso_split")}


def h256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def committed(path):
    p = Path(path)
    rel = str(p.relative_to(ROOT))
    files = [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
    tracked = set(subprocess.run(["git", "ls-files", rel], cwd=ROOT, capture_output=True, text=True).stdout.split())
    dirty = subprocess.run(["git", "status", "--porcelain", rel], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return bool(files) and all(str(f.relative_to(ROOT)) in tracked for f in files) and not dirty


def subset(d, filt):
    if filt == "R1":
        return d[d.res_class == "R1"]
    if filt == "rank1":
        return d[d["rank"] == 1]
    if filt == "pre_hmi":
        return d[d.day < "2010-05-01"]
    if filt == "minima":
        t = pd.to_datetime(d.day)
        keep = np.ones(len(d), bool)
        for m in MINIMA:
            keep &= ((t - pd.Timestamp(m)).abs() > pd.Timedelta(days=365)).to_numpy()
        return d[keep]
    return d


def design_matrix(d, act, form, wcol):
    """Own construction: k_{c,h} sin|lat|, epoch shifts (reference = most numerous epoch per hemisphere, ties earliest)
    in Joy (sin|lat|) or additive form, target (A - 1) sin|lat|; redundant columns dropped in the frozen order."""
    s = d.sinlat.to_numpy()
    cols = []
    for c in sorted(d.cycle.unique()):
        for h in "NS":
            m = ((d.cycle == c) & (d.hemisphere == h)).to_numpy()
            if m.any():
                cols.append(s * m)
    if form != "none":
        ref = {}
        for h in "NS":
            v = d[d.hemisphere == h].epoch.value_counts()
            if len(v):
                ref[h] = sorted(v.index, key=lambda e: (-v[e], ORDER.index(e)))[0]
        for e in ORDER:
            for h in "NS":
                m = ((d.epoch == e) & (d.hemisphere == h)).to_numpy()
                if m.any() and e != ref.get(h):
                    cols.append((s if form == "joy" else 1.0) * m)
    x3 = (d[act].to_numpy(float) - 1.0) * s
    w = d[wcol].to_numpy(float)
    sw = np.sqrt(w)[:, None]
    Z = np.column_stack(cols) if cols else np.zeros((len(d), 0))
    rank = lambda M: np.linalg.matrix_rank(M * sw) if M.shape[1] else 0     # noqa: E731
    ident = rank(np.column_stack([Z, x3])) == rank(Z) + 1
    cur = np.zeros((len(d), 0))
    for j in range(Z.shape[1]):
        t = np.column_stack([cur, Z[:, j]])
        if Z[:, j].any() and rank(t) > cur.shape[1]:
            cur = t
    return ident, np.column_stack([cur, x3]), w


def recount_row(d, saved):
    if len(d) == 0:
        return saved.get("state") == "campione vuoto", "campione vuoto"
    opt = ANALYSES[saved["analysis"]]
    ident, X, w = design_matrix(d, opt.get("act", "A_main"), opt.get("form", "joy"), opt.get("weights", "phi_mwo"))
    if not ident:
        return saved.get("state") == "beta3 non identificabile", "non identificabile"
    if saved.get("state") == "errore di M":
        return True, "errore di M"
    if saved.get("state") != "stimato":
        return False, "stato inatteso"
    try:
        par = {k: float(saved[k]) for k in ("var_a", "var_b", "phi", "kappa", "sigma_x2", "beta", "se", "lo", "hi")}
    except (KeyError, TypeError, ValueError):
        return False, "parametri mancanti"
    if not (all(math.isfinite(v) for v in par.values()) and 0 <= par["phi"] <= 0.98 and abs(par["kappa"]) <= 0.98
            and par["sigma_x2"] > 0 and par["se"] > 0):
        return False, "parametri fuori dominio"
    g = RC.projection(X, w)
    beta = float(g @ d.gamma_mwo.to_numpy())
    key = pd.MultiIndex.from_arrays([d.CR.astype(int).to_numpy(), d.hemisphere.to_numpy()])
    codes, uniq = pd.factorize(key)
    cr = np.array([c for c, _ in uniq])
    lp = np.log(w)
    se = RC.se_from_saved(SimpleNamespace(**par), d, g, codes, cr - cr.min(), np.array([h for _, h in uniq]), lp - lp.mean())
    lo, hi = beta - RC.Z * se, beta + RC.Z * se
    verdict = "supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso")
    good = (int(saved["n"]) == len(d) and abs(beta - par["beta"]) <= 1e-9 * max(1, abs(beta))
            and abs(se / par["se"] - 1) < 1e-6 and abs(lo - par["lo"]) <= 1e-9 * max(1, abs(lo))
            and abs(hi - par["hi"]) <= 1e-9 * max(1, abs(hi)) and saved.get("verdict") == verdict)
    return good, "stimato"


def receipt_complete(path, key, meta_path):
    """Same semantics as the other receipts of the chain: positive integer counts (not booleans), passed == total,
    exactly `total` checks all passed, not partial, bound to the SHA-256 of the META it recounted."""
    r = json.loads(Path(path).read_text())
    p_, t_, c = r.get("passed"), r.get("total"), r.get("checks")
    is_int = lambda x: isinstance(x, int) and not isinstance(x, bool)     # noqa: E731
    return (is_int(p_) and is_int(t_) and t_ > 0 and p_ == t_ and isinstance(c, list) and len(c) == t_
            and all(isinstance(x, dict) and x.get("ok") is True for x in c) and r.get("partial") is False
            and r.get(key) == h256(meta_path))


def products_match(directory):
    """Every product listed in META exists and has its declared SHA-256, and no product is unlisted."""
    m = json.loads((Path(directory) / "META.json").read_text())
    listed = m.get("products_sha256", {})
    present = {f.name for f in Path(directory).iterdir() if f.is_file() and f.name not in ("META.json", "RUN.log")}
    return bool(listed) and set(listed) == present and all(h256(Path(directory) / n) == h for n, h in listed.items())


def upstream_problems(cat, check_dir, val, val_read, stab, stab_rc, est):
    """Before SEALED is read (Codex, cb41c53): actual products of catalogue, design check, validation, stability and
    estimate match their META; stability links to the current catalogue, design check, validation and reading; the
    stability recount receipt has the full semantics."""
    out = [f"{Path(d).name}: products do not match META" for d in (cat, check_dir, val, stab, est) if not products_match(d)]
    sm = json.loads((Path(stab) / "META.json").read_text())
    for key, meta in (("catalogue_meta_sha256", Path(cat) / "META.json"),
                      ("design_check_meta_sha256", Path(check_dir) / "META.json"),
                      ("validation_meta_sha256", Path(val) / "META.json"), ("reading_sha256", Path(val_read) / "READ.json")):
        if sm.get(key) != h256(meta):
            out.append(f"stability META not bound to the current {key}")
    if not receipt_complete(Path(stab_rc) / "RECEIPT.json", "stability_meta_sha256", Path(stab) / "META.json"):
        out.append("stability recount receipt not complete or not bound")
    return out


def check(cat=CAT, stab=STAB, stab_rc=STAB_RC, est=EST, out=OUT, write=True, require_git=True, check_dir=CHECK,
          val=VAL, val_read=VAL_READ):
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    if require_git:
        for p in (cat, check_dir, val, val_read, stab, stab_rc, est):
            if not committed(p):
                sys.exit(f"{Path(p).name} not preserved in Git")
    up = upstream_problems(cat, check_dir, val, val_read, stab, stab_rc, est) if require_git else \
        [f"{Path(d).name}: products do not match META" for d in (stab, est) if not products_match(d)]
    ok("upstream chain before SEALED: products match META, stability bound, stability receipt complete", not up, up)
    if up:
        if write:
            Path(out).mkdir(parents=True, exist_ok=False)
            (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(checks=res, passed=0, total=len(res), partial=True,
                                                                    reason=up), indent=2) + "\n")
        return False                              # never proceed to SEALED when a prerequisite fails
    meta = json.loads((Path(est) / "META.json").read_text())
    ok("estimate product hashes; estimate bound to the stability and catalogue META",
       all(h256(Path(est) / n) == h for n, h in meta["products_sha256"].items())
       and meta.get("stability_meta_sha256") == h256(Path(stab) / "META.json")
       and meta.get("catalogue_meta_sha256") == h256(Path(cat) / "META.json"))
    tab = pd.read_csv(Path(est) / "ESTIMATE.csv")
    ok("every analysis of the protocol present once", sorted(tab.analysis) == sorted(ANALYSES) and not tab.analysis.duplicated().any())
    design = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    sealed = pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})
    states = {}
    for r in tab.to_dict("records"):
        opt = ANALYSES.get(r["analysis"], {})
        set_name = opt.get("set_name", "isolated")
        d = design[design.record_set == set_name].reset_index(drop=True)
        sx = sealed[sealed.record_set == set_name].set_index("noaa")
        d["gamma_mwo"] = sx.loc[d.noaa, "gamma_deg"].to_numpy()
        d = subset(d, opt.get("filt")).reset_index(drop=True)
        act = opt.get("act", "A_main")
        d = d[np.isfinite(d[act].to_numpy(float))].reset_index(drop=True)
        good, st = recount_row(d, r)
        states[r["analysis"]] = st
        ok(f"{r['analysis']}: subset, state, beta, SE, bounds, verdict", good, st)
    stab_rule = json.loads((Path(stab) / "STABILITY.json").read_text())["rule"]["outcome"]
    main = tab[tab.analysis == "main"].iloc[0]
    outcome = stab_rule if states.get("main") == "stimato" else "non concludente"
    fin = json.loads((Path(est) / "FINAL.json").read_text())
    stab_reasons = json.loads((Path(stab) / "STABILITY.json").read_text())["rule"]["reasons"]
    verdict = None
    if outcome == "verdetto":
        verdict = "supportato" if main.hi < 0 else ("opposto" if main.lo > 0 else "non deciso")

    def same(a, b):
        if a is None or b is None or (isinstance(a, float) and not math.isfinite(a)):
            return (a is None or (isinstance(a, float) and not math.isfinite(a))) and \
                (b is None or (isinstance(b, float) and not math.isfinite(b)))
        return abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(b)))
    nums = all(same(fin.get(k), (getattr(main, c) if states.get("main") == "stimato" else None))
               for k, c in (("beta3", "beta"), ("se", "se"), ("lo", "lo"), ("hi", "hi")))
    targets_cur = json.loads((Path(check_dir) / "TARGETS.json").read_text()) if (Path(check_dir) / "TARGETS.json").exists() else None
    ok("FINAL: outcome, verdict, reasons, main state, beta3/SE/bounds and targets equal to the recounted values",
       fin.get("outcome") == outcome and fin.get("verdict") == verdict and nums
       and fin.get("main_state") == main.state and fin.get("targets") == targets_cur
       and fin.get("reasons") == stab_reasons, (outcome, verdict))
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
            checks=res, passed=sum(x["ok"] for x in res), total=len(res), partial=not require_git,
            estimate_meta_sha256=h256(Path(est) / "META.json"), recounted_outcome=outcome, recounted_verdict=verdict),
            indent=2) + "\n")
    return all(x["ok"] for x in res)


def selftest():
    """Synthetic design and sealed response; the analysis module's fit_beta3 (as patched: with saved M parameters)
    produces ESTIMATE rows in a subprocess; the recount must pass, then refuse tampered rows and outcome."""
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
d['A_own'] = d.A_main * 1.1; d['A_silso_split'] = d.A_main * 0.9; d['A_silso_hem'] = d.A_main
d['res_class'] = np.where(np.arange(len(d)) % 3, 'R1', 'R2'); d['rank'] = np.where(np.arange(len(d)) % 4, 1, 2)
d['dpd_area'] = d.dpd_area.astype(float)
rng = np.random.default_rng(5)
g = 24 * d.sinlat + rng.normal(0, 15, len(d))
al = d.assign(record_set='all'); dd = pd.concat([d, al], ignore_index=True)
(td / 'cat').mkdir(); dd.to_csv(td / 'cat/DESIGN.csv', index=False); (td / 'cat/META.json').write_text('{{}}')
sealed = pd.DataFrame(dict(record_set=dd.record_set, noaa=dd.noaa, gamma_deg=np.concatenate([g, g])))
sealed.to_csv(td / 'cat/SEALED.csv.gz', index=False)
(td / 'stab').mkdir(); (td / 'stab/STABILITY.json').write_text(json.dumps(dict(rule=dict(outcome='descrittivo', reasons='S2 x'))))
(td / 'stab/META.json').write_text(json.dumps(dict(products_sha256={{'STABILITY.json': hashlib.sha256((td / 'stab/STABILITY.json').read_bytes()).hexdigest()}})))
(td / 'chk').mkdir(); (td / 'chk/TARGETS.json').write_text(json.dumps(dict(delta_beta_20=-1.0, C=0.5)))
rows = []
for name, opt in (('main', {{}}),) + A.SENSITIVITIES:
    x = dd[dd.record_set == opt.get('set_name', 'isolated')].reset_index(drop=True)
    x['gamma_mwo'] = sealed[sealed.record_set == opt.get('set_name', 'isolated')].gamma_deg.to_numpy()
    x = A.filtered(x, opt.get('filt')).reset_index(drop=True)
    r = A.fit_beta3(x, opt.get('form', 'joy'), opt.get('weights', 'phi_mwo'), opt.get('act', 'A_main'))
    rows.append(dict(analysis=name, **r))
tab = pd.DataFrame(rows); main = tab.iloc[0]
(td / 'est').mkdir(); tab.to_csv(td / 'est/ESTIMATE.csv', index=False)
(td / 'est/FINAL.json').write_text(json.dumps(dict(outcome='descrittivo', reasons='S2 x', beta3=float(main.beta), se=float(main.se),
    lo=float(main.lo), hi=float(main.hi), main_state=main.state, verdict=None, targets=dict(delta_beta_20=-1.0, C=0.5))))
h = {{f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (td / 'est').iterdir()}}
(td / 'est/META.json').write_text(json.dumps(dict(products_sha256=h,
    stability_meta_sha256=hashlib.sha256((td / 'stab/META.json').read_bytes()).hexdigest(),
    catalogue_meta_sha256=hashlib.sha256((td / 'cat/META.json').read_bytes()).hexdigest())))
"""
        # the estimate stage saves the M parameters only with the wiring patch: apply it to a temporary copy
        (td / "scripts").mkdir()
        (td / "python").symlink_to(ROOT / "python")          # the copy finds sharpbl as from the repository
        tmp_src = td / "scripts/t3_mwo_analysis.py"
        tmp_src.write_text((ROOT / "scripts/t3_mwo_analysis.py").read_text())
        pr = subprocess.run(["patch", "-s", str(tmp_src)], input=(ROOT / "patches/T3_MWO_STABILITY_WIRING.patch").read_text()
                            .split("--- a/scripts/t3_mwo_stability_extras.py")[0], text=True, capture_output=True)
        code = code.replace(repr(str(ROOT / "scripts/t3_mwo_analysis.py")), repr(str(tmp_src)))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok("patched analysis module produced the synthetic estimate (subprocess)", pr.returncode == 0 and r.returncode == 0,
           (pr.stderr + r.stderr)[-300:])
        if r.returncode == 0:
            kw = dict(cat=td / "cat", stab=td / "stab", est=td / "est", write=False, require_git=False, check_dir=td / "chk")
            ok("recount passes on the synthetic estimate", check(**kw))
            tab = pd.read_csv(td / "est/ESTIMATE.csv")
            meta = json.loads((td / "est/META.json").read_text())

            def tamper(fn):
                t = tab.copy()
                fn(t)
                t.to_csv(td / "est/ESTIMATE.csv", index=False)
                meta["products_sha256"]["ESTIMATE.csv"] = h256(td / "est/ESTIMATE.csv")
                (td / "est/META.json").write_text(json.dumps(meta))
                refused = not check(**kw)
                tab.to_csv(td / "est/ESTIMATE.csv", index=False)
                meta["products_sha256"]["ESTIMATE.csv"] = h256(td / "est/ESTIMATE.csv")
                (td / "est/META.json").write_text(json.dumps(meta))
                return refused
            ok("refused: main beta changed", tamper(lambda t: t.__setitem__("beta", t.beta + np.r_[1.0, np.zeros(len(t) - 1)])))
            ok("refused: a sensitivity SE changed", tamper(lambda t: t.__setitem__("se", t.se * np.r_[1.0, 1.1, np.ones(len(t) - 2)])))
            ok("refused: phi outside the REML domain", tamper(lambda t: t.__setitem__("phi", np.r_[-0.1, t.phi.to_numpy()[1:]])))
            ok("refused: a sensitivity missing", tamper(lambda t: t.drop(index=len(t) - 1, inplace=True)))
            fin = json.loads((td / "est/FINAL.json").read_text())
            (td / "est/FINAL.json").write_text(json.dumps(dict(fin, outcome="verdetto", verdict="non deciso")))
            meta["products_sha256"]["FINAL.json"] = h256(td / "est/FINAL.json")
            (td / "est/META.json").write_text(json.dumps(meta))
            ok("refused: FINAL turned into a verdict against the stability rule", not check(**kw))
            for k, v in (("se", fin["se"] * 2), ("lo", fin["lo"] - 1), ("hi", fin["hi"] + 1), ("main_state", "errore di M"),
                         ("targets", dict(delta_beta_20=-9.0, C=0.5)), ("reasons", "altro")):
                (td / "est/FINAL.json").write_text(json.dumps(dict(fin, **{k: v})))
                meta["products_sha256"]["FINAL.json"] = h256(td / "est/FINAL.json")
                (td / "est/META.json").write_text(json.dumps(meta))
                ok(f"refused: FINAL {k} altered (hash updated)", not check(**kw))
            (td / "est/FINAL.json").write_text(json.dumps(fin))
            meta["products_sha256"]["FINAL.json"] = h256(td / "est/FINAL.json")
            (td / "est/META.json").write_text(json.dumps(meta))
            st = json.loads((td / "stab/STABILITY.json").read_text())
            (td / "stab/STABILITY.json").write_text(json.dumps(dict(rule=dict(outcome="verdetto", reasons=""))))
            (td / "est/FINAL.json").write_text(json.dumps(dict(fin, outcome="verdetto", reasons="", verdict="non deciso")))
            meta["products_sha256"]["FINAL.json"] = h256(td / "est/FINAL.json")
            (td / "est/META.json").write_text(json.dumps(meta))
            ok("refused: stability product changed with its META unchanged (FINAL following the change)", not check(**kw))
            (td / "stab/STABILITY.json").write_text(json.dumps(st))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "m.json").write_text("{}")
        base = dict(passed=1, total=1, partial=False, stability_meta_sha256=h256(td / "m.json"))
        cases = [dict(base, checks=[{"ok": False}]), dict(base, checks=[]), dict(base, passed=True, total=True,
                 checks=[{"ok": True}]), dict(base, checks=[{"ok": True}], partial=True), dict(base, checks=[{"ok": True}])]
        out = []
        for c in cases:
            (td / "r.json").write_text(json.dumps(c))
            out.append(receipt_complete(td / "r.json", "stability_meta_sha256", td / "m.json"))
    ok("stability receipt: failed check, missing checks, boolean counts, partial refused; complete accepted",
       out == [False, False, False, False, True], out)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
