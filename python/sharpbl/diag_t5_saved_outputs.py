"""T5-D1: deterministic diagnosis of saved P2f simulations; no scientific imports.

Run --selftest on hand-built tables, then --run on the same clean commit.
The run repeats the tests before opening the frozen scientific inputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.stats import norm, spearmanr

ETA = 3.56e-25
Q = float(norm.ppf(0.9875))
ATOL, RTOL = 1e-12, 1e-9
PROTOCOL = "docs/PROTOCOL_T5_DIAGNOSTIC_SAVED_OUTPUTS.md"
INPUT_LIST = "docs/T5_DIAGNOSTIC_INPUTS_SHA256.csv"
SCRIPT_REL = "python/sharpbl/diag_t5_saved_outputs.py"
PROTOCOL_SHA = "53a05c1fd7c0315eca52b508472c59d6df485c29c8ef2b717e81264d3d600e5d"
INPUT_LIST_SHA = "b017967dff7d7ac35ebad6c09c210d69f990d984e3f936028fea2a289e217d06"
ORIGINAL_COMMIT = "5c3b664bb3e6bbdddd8a9502801163ed9873ce49"
ORIGINAL_PLAN_SHA = "8f030010ddedb28131a79ea72edd2fe6077c9a04dd236854a86fb170f1cb3ab1"
NULL_SCENARIOS = (0, 1, 2, 7, 10)
EFFECT_SCENARIOS = (1, 2, 7)
EFFECTS = ("-0.1", "-0.2", "-0.3", "-0.35")
PROBS = (0.005, 0.0125, 0.025, 0.05, 0.5, 0.95, 0.975, 0.9875, 0.995)
KEY = ["test", "kind", "scenario", "effect", "k"]
VALID_VERDICTS = {"supportato", "opposto", "non deciso", "errore"}
NUMERIC = ["beta_true", "beta", "se", "stat", "lo", "hi", "var_a", "var_b",
           "n_varfun", "n_zero_residuals", "phi", "kappa", "sigma_x2",
           "n_valid_starts", "sigma_x_at_lower", "neg_reml"]
FLAGS = ["covered", "below", "above"]
GROUP_KEYS = ["kind", "scenario", "effect"]


class DiagnosticError(RuntimeError):
    pass


def require(condition, message):
    if not bool(condition):
        raise DiagnosticError(message)


def close(a, b):
    return bool(np.allclose(a, b, atol=ATOL, rtol=RTOL, equal_nan=False))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_hash(path, expected):
    require(Path(path).is_file() and digest(path) == expected, f"hash mismatch: {path}")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def boolean(value):
    x = str(value).lower()
    require(x in {"true", "false", "0", "1"}, f"invalid boolean: {value!r}")
    return x in {"true", "1"}


def integer(value):
    try:
        d = Decimal(str(value))
        require(d.is_finite() and d == d.to_integral_value(), f"not an integer: {value}")
        return int(d)
    except InvalidOperation as exc:
        raise DiagnosticError(f"invalid integer: {value}") from exc


def effect_key(value):
    try:
        d = Decimal(str(value))
        require(d.is_finite(), "nonfinite effect key")
        return "0" if d == 0 else format(d.normalize(), "f")
    except InvalidOperation as exc:
        raise DiagnosticError(f"invalid effect key: {value}") from exc


def read_table(source):
    return pd.read_csv(source, dtype=str, keep_default_na=False)


def canonical(frame):
    require(set(KEY).issubset(frame.columns), "missing key columns")
    out = frame.copy()
    out["scenario"] = out["scenario"].map(integer)
    out["k"] = out["k"].map(integer)
    out["effect"] = out["effect"].map(effect_key)
    return out


def expected_keys():
    null = {("T5", "null", s, "0", k) for s in NULL_SCENARIOS for k in range(10000)}
    alt = {("T5", "effect", s, e, k) for s in EFFECT_SCENARIOS
           for e in EFFECTS for k in range(2000)}
    return null | alt


def verify_keys(frame, expected):
    require(not frame.duplicated(KEY).any(), "duplicate catalogue keys")
    actual = set(frame[KEY].itertuples(index=False, name=None))
    require(actual == expected, f"key mismatch: missing {len(expected-actual)}, extra {len(actual-expected)}")


def select_t5(raw):
    f = canonical(raw)
    mask = (f["test"] == "T5") & (
        ((f["kind"] == "null") & f["scenario"].isin(NULL_SCENARIOS) & (f["effect"] == "0")) |
        ((f["kind"] == "effect") & f["scenario"].isin(EFFECT_SCENARIOS) & f["effect"].isin(EFFECTS)))
    return f.loc[mask].copy()


def validate_rows(frame):
    require(set(NUMERIC + FLAGS + ["verdict", "error"]).issubset(frame.columns), "missing data columns")
    f = frame.copy()
    require(f["verdict"].isin(VALID_VERDICTS).all(), "unknown verdict")
    valid = f["verdict"] != "errore"
    for col in NUMERIC:
        f[col] = pd.to_numeric(f[col], errors="coerce")
    for col in FLAGS:
        f[col] = f[col].map(integer)
        require(f[col].isin([0, 1]).all(), f"invalid flag {col}")
    require(np.isfinite(f["beta_true"]).all(), "nonfinite beta_true")
    require(close(f["beta_true"] / ETA, f["effect"].astype(float)), "injected effect mismatch")
    v = f.loc[valid]
    require(np.isfinite(v[NUMERIC].to_numpy(dtype=float)).all(), "nonfinite successful row")
    require((v["se"] > 0).all(), "nonpositive standard error")
    require(close(v["stat"], v["beta"] / v["se"]), "saved stat mismatch")
    require(close((v["beta"] - v["lo"]) / v["se"], Q), "lower half interval mismatch")
    require(close((v["hi"] - v["beta"]) / v["se"], Q), "upper half interval mismatch")
    covered = (v["lo"] <= v["beta_true"]) & (v["beta_true"] <= v["hi"])
    below, above = v["lo"] > v["beta_true"], v["hi"] < v["beta_true"]
    for name, values in zip(FLAGS, [covered, below, above]):
        require(np.array_equal(v[name].to_numpy(), values.astype(int)), f"saved {name} mismatch")
    verdict = np.where(v["hi"] < 0, "supportato", np.where(v["lo"] > 0, "opposto", "non deciso"))
    require(np.array_equal(v["verdict"].to_numpy(), verdict), "saved verdict mismatch")
    require((f.loc[~valid, FLAGS].sum(axis=1) == 0).all(), "error row has coverage flag")
    require((f[FLAGS].sum(axis=1) + (~valid).astype(int) == 1).all(), "row partition mismatch")
    return f


def normalized(v):
    s = v["se"].to_numpy(dtype=float) / ETA
    r = (v["beta"].to_numpy(dtype=float) - v["beta_true"].to_numpy(dtype=float)) / ETA
    return r, s, r / s


def quintiles(v):
    order = v.sort_values(["se", "k"], kind="stable").index.to_numpy()
    return np.array_split(order, 5)


def rank_correlation(r, s):
    if np.ptp(np.abs(r)) == 0 or np.ptp(s) == 0:
        return math.nan
    return float(spearmanr(np.abs(r), s).statistic)


def mc_se(f, n):
    return float(math.sqrt(f * (1 - f) / n))


def summarize(f):
    groups, quant, bins, nuisance = [], [], [], []
    for (kind, scenario, effect), g in f.groupby(GROUP_KEYS, sort=True):
        base = dict(kind=kind, scenario=int(scenario), effect=effect)
        v = g[g["verdict"] != "errore"]
        n, m = len(g), len(v)
        require(m >= 5, "fewer than five successful rows")
        r, s, z = normalized(v)
        mean_r = float(np.mean(r))
        variance = float(np.var(r, ddof=1))
        require(variance > 0 and np.isfinite(variance), "nonpositive empirical variance")
        mse, mean_s2 = float(np.mean(r*r)), float(np.mean(s*s))
        require(close(mse, (m-1)/m * variance + mean_r**2), "MSE identity failed")
        u = (r - mean_r) / math.sqrt(variance)
        counts = dict(n=n, m=m, errors=n-m,
                      supported=int((g["verdict"] == "supportato").sum()),
                      opposite=int((g["verdict"] == "opposto").sum()),
                      non_decided=int((g["verdict"] == "non deciso").sum()),
                      covered=int(g["covered"].sum()), below=int(g["below"].sum()), above=int(g["above"].sum()))
        row = dict(**base, **counts, bias=mean_r, bias_mc_se=math.sqrt(variance/m),
                   v_emp=variance, mse=mse, mean_s2=mean_s2, median_s=float(np.median(s)), R=mean_s2/variance,
                   mean_z=float(np.mean(z)), sd_z=float(np.std(z, ddof=1)),
                   spearman_abs_r_s=rank_correlation(r, s))
        for name in ("errors", "supported", "opposite", "covered", "below", "above"):
            rate = counts[name] / n
            row[name + "_frac"] = rate
            row[name + "_mc_se"] = mc_se(rate, n)
        row["false"] = counts["supported"] + counts["opposite"] if kind == "null" else math.nan
        row["false_frac"] = row["false"] / n
        row["false_mc_se"] = mc_se(row["false_frac"], n) if kind == "null" else math.nan
        groups.append(row)
        for p in PROBS:
            quant.append(dict(**base, probability=p, normal=float(norm.ppf(p)),
                              z_quantile=float(np.quantile(z, p, method="linear")),
                              u_quantile=float(np.quantile(u, p, method="linear"))))
        for j, ix in enumerate(quintiles(v), 1):
            b = v.loc[ix]
            rb, sb, zb = normalized(b)
            bins.append(dict(**base, quintile=j, m_bin=len(b), min_s=float(sb.min()), max_s=float(sb.max()),
                             median_s=float(np.median(sb)), mean_r=float(rb.mean()), mean_abs_r=float(np.abs(rb).mean()),
                             mean_s2=float(np.mean(sb*sb)), mse=float(np.mean(rb*rb)),
                             z_above_q=int((zb > Q).sum()), z_below_minus_q=int((zb < -Q).sum()),
                             positive_tail_frac=float(np.mean(zb > Q)), negative_tail_frac=float(np.mean(zb < -Q))))
        nu = dict(**base, m=m, at_lower_frac=float(v["sigma_x_at_lower"].mean()))
        arrays = {c: v[c].to_numpy(dtype=float) for c in ("phi", "kappa", "var_b", "n_varfun", "n_zero_residuals")}
        arrays.update(sigma_x2_scaled=v["sigma_x2"].to_numpy(dtype=float)/ETA**2,
                      var_a_scaled=v["var_a"].to_numpy(dtype=float)-2*math.log(ETA))
        for name, a in arrays.items():
            nu.update({name+"_mean": float(np.mean(a)), name+"_median": float(np.median(a)),
                       name+"_p10": float(np.quantile(a, .1, method="linear")),
                       name+"_p90": float(np.quantile(a, .9, method="linear"))})
        for starts in range(1, 6):
            nu[f"n_starts_{starts}"] = int((v["n_valid_starts"] == starts).sum())
        nuisance.append(nu)
    return tuple(pd.DataFrame(x) for x in (groups, quant, bins, nuisance))


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, condition, observed="", expected=""):
        ok = bool(condition)
        self.rows.append(dict(check=name, observed=str(observed), expected=str(expected), passed=ok))
        require(ok, f"check failed: {name} ({observed}; expected {expected})")


def fixture(effect="0", n=10):
    rows = []
    for k in range(n):
        r = (k - (n-1)/2) / 10
        bt, se = float(effect) * ETA, .1 * ETA
        beta = bt + r * ETA
        lo, hi = beta-Q*se, beta+Q*se
        rows.append(dict(test="T5", kind="null" if effect == "0" else "effect", scenario="7", effect=effect,
                         k=str(k), beta_true=bt, beta=beta, se=se, stat=beta/se, lo=lo, hi=hi,
                         verdict="supportato" if hi<0 else ("opposto" if lo>0 else "non deciso"),
                         covered=int(lo<=bt<=hi), below=int(lo>bt), above=int(hi<bt), error="",
                         var_a=2*math.log(ETA), var_b=0, n_varfun=2375, n_zero_residuals=0,
                         phi=.5, kappa=0, sigma_x2=ETA**2, n_valid_starts=5, sigma_x_at_lower=0, neg_reml=1))
    return canonical(pd.DataFrame(rows))


def expect_failure(fn):
    try:
        fn()
    except DiagnosticError:
        return True
    return False


def selftests():
    c = Checks()
    def test(name, fn):
        try:
            ok = bool(fn())
        except Exception as exc:
            c.rows.append(dict(check="selftest_"+name, observed=repr(exc), expected="True", passed=False))
            return
        c.rows.append(dict(check="selftest_"+name, observed=str(ok), expected="True", passed=ok))
    test("null_text", lambda: read_table(io.StringIO("kind,x\nnull,1\n"))["kind"].iloc[0] == "null")
    test("false_text", lambda: not boolean("False"))
    test("invalid_bool", lambda: expect_failure(lambda: boolean("missing")))
    test("noninteger_key", lambda: expect_failure(lambda: integer("2.5")))
    test("effect_canonical", lambda: effect_key("-0.3500") == "-0.35")
    f = fixture()
    test("finite_fixture", lambda: len(validate_rows(f)) == 10)
    test("csv_roundtrip", lambda: len(validate_rows(canonical(read_table(io.StringIO(f.to_csv(index=False)))))) == 10)
    test("linear_quantile", lambda: close(np.quantile([0,1,2,3,4], .0125, method="linear"), .05))
    def error_case():
        g = f.copy();g.loc[0, "verdict"] = "errore";g.loc[0, "error"] = "handmade"
        g.loc[0, FLAGS] = 0;g.loc[0, [x for x in NUMERIC if x != "beta_true"]] = math.nan
        z = validate_rows(g);a, _, _, _ = summarize(z)
        return a.iloc[0]["n"] == 10 and a.iloc[0]["m"] == 9 and a.iloc[0]["errors_frac"] == .1
    test("error_denominator", error_case)
    def bad_finite():
        g=f.copy();g.loc[0,"beta"]=math.nan
        return expect_failure(lambda: validate_rows(g))
    test("nonfinite_refused", bad_finite)
    def bad_half():
        g=f.copy();g.loc[0,"hi"] += ETA
        return expect_failure(lambda: validate_rows(g))
    test("upper_half_checked", bad_half)
    def bad_lower():
        g=f.copy();g.loc[0,"lo"] -= ETA
        return expect_failure(lambda: validate_rows(g))
    test("lower_half_checked", bad_lower)
    def zero_se():
        g=f.copy();g.loc[0,"se"]=0
        return expect_failure(lambda: validate_rows(g))
    test("zero_se_refused", zero_se)
    def boundary():
        g=f.iloc[:1].copy();g.loc[0,"beta"]=Q*.1*ETA;g.loc[0,"lo"]=0.0
        g.loc[0,"hi"]=2*Q*.1*ETA;g.loc[0,"stat"]=Q;g.loc[0,"verdict"]="non deciso"
        g.loc[0,FLAGS]=[1,0,0]
        return int(validate_rows(g).iloc[0]["covered"]) == 1
    test("endpoint_equality", boundary)
    test("tail_directions", lambda: (validate_rows(f)["below"].sum() == 3 and validate_rows(f)["above"].sum() == 3))
    def under_effect():
        a=validate_rows(fixture("-0.3"));r,s,z=normalized(a)
        return close(z,r/s) and not close(z,a["stat"])
    test("centered_statistic", under_effect)
    def moments():
        a,_,_,_=summarize(validate_rows(f))
        return (close(a.iloc[0]["bias"],0) and close(a.iloc[0]["v_emp"],11/120)
                and close(a.iloc[0]["mse"],.0825) and close(a.iloc[0]["mean_s2"],.01))
    test("normalized_moments", moments)
    def partition():
        g=validate_rows(fixture(n=11));ix=quintiles(g)
        return [len(x) for x in ix]==[3,2,2,2,2] and np.array_equal(np.concatenate(ix),g.sort_values("k").index)
    test("quintile_ties", partition)
    test("undefined_correlation", lambda: math.isnan(rank_correlation(np.arange(5), np.ones(5))))
    keys=set(f[KEY].itertuples(index=False,name=None))
    test("exact_keys", lambda: (verify_keys(f,keys) is None))
    test("duplicate_refused", lambda: expect_failure(lambda: verify_keys(pd.concat([f,f.iloc[:1]]),keys)))
    test("missing_key_refused", lambda: expect_failure(lambda: verify_keys(f.iloc[1:],keys)))
    test("extra_key_refused", lambda: expect_failure(lambda: verify_keys(f, set(list(keys)[:-1]))))
    test("zero_variance_refused", lambda: expect_failure(lambda: summarize(validate_rows(pd.concat([fixture(n=11).iloc[[5]]]*5).reset_index(drop=True)))))
    def hash_test():
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x";p.write_bytes(b"abc")
            verify_hash(p, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            return expect_failure(lambda: verify_hash(p, "0"*64))
    test("sha_mismatch", hash_test)
    test("counts_expected", lambda: len(expected_keys())==74000)
    return c.rows


def verify_inputs(root, checks):
    checks.add("protocol_hash", digest(root/PROTOCOL)==PROTOCOL_SHA)
    checks.add("input_list_hash", digest(root/INPUT_LIST)==INPUT_LIST_SHA)
    records=read_table(root/INPUT_LIST)
    checks.add("input_list_unique", len(records)==8 and records["file"].is_unique)
    hashes={}
    for x in records.to_dict("records"):
        p=root/x["file"]
        checks.add("input_hash:"+x["file"], p.is_file() and digest(p)==x["sha256"])
        checks.add("reference_blob:"+x["file"], git(root,"rev-parse",x["reference_commit"]+":"+x["file"])==x["reference_blob"])
        checks.add("current_blob:"+x["file"], git(root,"hash-object","--",x["file"])==x["reference_blob"])
        hashes[x["file"]]=x["sha256"]
    post=read_table(root/"results/P2F/POST_CHECKS.csv")
    checks.add("prior_checks_passed", len(post)>0 and post["passed"].map(boolean).all())
    for name in ("VALIDATION_RAW", "VALIDATION_FALSE_VERDICTS", "VALIDATION_COVERAGE_POWER", "VALIDATION_DECISION"):
        suffix=".csv.gz" if name=="VALIDATION_RAW" else ".csv"
        checks.add("prior_hash:"+name, (post["sha256_"+name]==hashes["results/P2F/"+name+suffix]).all())
    checks.add("prior_protocol_hash", (post["sha256_PROTOCOL_P2F_checked"]==ORIGINAL_PLAN_SHA).all())
    return hashes, records.to_dict("records"), sorted(set(post["git_commit"]))


def check_provenance(table, label, checks):
    checks.add(label+":source_commit", (table["git_commit"]==ORIGINAL_COMMIT).all())
    checks.add(label+":source_clean", table["git_dirty"].map(integer).eq(0).all())
    checks.add(label+":source_protocol", (table["sha256_PROTOCOL_P2F"]==ORIGINAL_PLAN_SHA).all())


def verify_summaries(f, tables, originals, checks):
    groups,quant,bins,nuis=tables
    checks.add("output_row_counts", [len(x) for x in tables]==[17,153,85,17], [len(x) for x in tables], [17,153,85,17])
    fv,cp,dec=originals
    for row in groups.to_dict("records"):
        kind,s,e=row["kind"],row["scenario"],row["effect"]
        label=f"{kind}:{s}:{e}"
        g=f[(f["kind"]==kind)&(f["scenario"]==s)&(f["effect"]==e)]
        # Independent Python arithmetic, not the summary's numpy reductions.
        good=[r for r in g.to_dict("records") if r["verdict"]!="errore"]
        errors=[(r["beta"]-r["beta_true"])/ETA for r in good]
        se2=[(r["se"]/ETA)**2 for r in good]
        checks.add(label+":moments_independent", close(row["bias"],statistics.fmean(errors)) and
                   close(row["v_emp"],statistics.variance(errors)) and close(row["mse"],statistics.fmean(x*x for x in errors)) and
                   close(row["mean_s2"],statistics.fmean(se2)))
        checks.add(label+":partition", row["covered"]+row["below"]+row["above"]+row["errors"]==row["n"])
        bs=bins[(bins["kind"]==kind)&(bins["scenario"]==s)&(bins["effect"]==e)]
        checks.add(label+":quintile_partition", len(bs)==5 and int(bs["m_bin"].sum())==row["m"])
        orig=(fv if kind=="null" else cp)
        mask=(orig["test"]=="T5")&(orig["scenario"].map(integer)==s)
        if kind=="effect": mask &= orig["effect"].map(effect_key)==e
        subset=orig.loc[mask]
        checks.add(label+":one_summary", len(subset)==1)
        o=subset.iloc[0]
        names=["n","errors","false","supported","opposite"] if kind=="null" else ["n","errors","covered","below","above"]
        checks.add(label+":counts_match", all(integer(o[x])==row[x] for x in names))
        names=["false_frac","supported_frac","opposite_frac","error_frac"] if kind=="null" else ["coverage","below_frac","above_frac","power"]
        mapped={"error_frac":"errors_frac","coverage":"covered_frac","power":"supported_frac"}
        checks.add(label+":rates_match", all(close(float(o[x]),row[mapped.get(x,x)]) for x in names))
        if kind=="effect":
            checks.add(label+":coverage_mc_se", close(float(o["coverage_mc_se"]),row["covered_mc_se"]))
    historical=dec[dec["test"]=="T5"]
    checks.add("historical_T5_not_validated", len(historical)==1 and not boolean(historical.iloc[0]["validated"]))


def make_figures(csv_dir, figure_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure_dir.mkdir(parents=True,exist_ok=True)
    groups=pd.read_csv(csv_dir/"T5D_GROUPS.csv",keep_default_na=False)
    qs=pd.read_csv(csv_dir/"T5D_QUANTILES.csv",keep_default_na=False)
    bins=pd.read_csv(csv_dir/"T5D_SE_QUINTILES.csv",keep_default_na=False)
    labels=[f"{x.kind[0]}:{x.scenario}:{x.effect:g}" for x in groups.itertuples()]
    fig,ax=plt.subplots(2,1,figsize=(14,8),sharex=True)
    x=np.arange(len(groups))
    ax[0].errorbar(x,groups.bias,yerr=groups.bias_mc_se,fmt="o",capsize=3)
    ax[0].axhline(0,color="gray",lw=1);ax[0].set_ylabel("Bias / eta0 (barre: errore MC)")
    ax[1].plot(x,groups.R,"o");ax[1].axhline(1,color="gray",lw=1)
    ax[1].set_ylabel("media(SE²) / varianza empirica")
    ax[1].set_xticks(x,labels,rotation=60,ha="right")
    fig.suptitle("T5-D1 — bias e scala, condizionati agli esiti numerici validi")
    fig.tight_layout();fig.savefig(figure_dir/"t5d_bias_scale.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(16,12))
    for (kind,s,e),g in qs.groupby(GROUP_KEYS,sort=True):
        row=0 if kind=="null" else 1
        label=f"s{s}, effetto {float(e):g}"
        for col,key in enumerate(("z_quantile","u_quantile")):
            axes[row,col].plot(g.normal,g[key],"o-",ms=3,label=label)
    for i,axs in enumerate(axes):
        for j,a in enumerate(axs):
            a.plot([-2.6,2.6],[-2.6,2.6],color="gray",ls="--")
            a.set_xlabel("Quantile normale");a.set_ylabel("Quantile z" if j==0 else "Quantile u")
            a.set_title("Nulla" if i==0 else "Sotto effetto");a.legend(fontsize=7)
    fig.suptitle("Quantili 0,5–99,5%: z = errore/SE; u = errore centrato/scalato empiricamente")
    fig.tight_layout();fig.savefig(figure_dir/"t5d_quantiles.png",dpi=160);plt.close(fig)
    fig,axes=plt.subplots(4,5,figsize=(18,13),sharex=True)
    for ax,((kind,s,e),g) in zip(axes.flat,bins.groupby(GROUP_KEYS,sort=True)):
        ax.plot(g.quintile,g.positive_tail_frac,"o-",label="z > q")
        ax.plot(g.quintile,g.negative_tail_frac,"s--",label="z < -q")
        ax.axhline(.0125,color="gray",lw=1);ax.set_title(f"{kind}: s{s}, {float(e):g}")
        ax.set_xticks([1,2,3,4,5]);ax.set_xlabel("Quintile SE crescente");ax.legend(fontsize=7)
    for ax in list(axes.flat)[17:]: ax.set_visible(False)
    fig.suptitle("Code per quintile SE; denominatore: soli esiti numerici del quintile")
    fig.tight_layout();fig.savefig(figure_dir/"t5d_se_tails.png",dpi=160);plt.close(fig)
    return matplotlib.__version__


def run(root):
    checks=Checks();checks.rows.extend(selftests())
    out=root/"results/T5_DIAGNOSTIC";figs=root/"figures/T5_DIAGNOSTIC"
    require(not out.exists() and not figs.exists(), "output directory exists; refusing a second run")
    started=datetime.now(timezone.utc).isoformat()
    metadata={"started_utc":started,"status":"failed","protocol_sha256":PROTOCOL_SHA}
    stamp={}
    try:
        checks.add("selftests_passed", all(x["passed"] for x in checks.rows))
        commit=git(root,"rev-parse","HEAD")
        dirty=git(root,"status","--porcelain","--untracked-files=no")
        checks.add("diagnostic_clean_commit", not dirty, dirty, "clean tracked files")
        checks.add("running_tracked_script", Path(__file__).resolve() == root/SCRIPT_REL and
                   git(root,"hash-object","--",SCRIPT_REL) == git(root,"rev-parse","HEAD:"+SCRIPT_REL))
        stamp=dict(git_commit_diag=commit,git_dirty_diag=0,sha256_T5_D1=PROTOCOL_SHA,sha256_INPUT_LIST=digest(root/INPUT_LIST))
        hashes,refs,post_commits=verify_inputs(root,checks)
        metadata.update(git_commit_diag=commit,git_dirty_diag=0,sha256_INPUT_LIST=stamp["sha256_INPUT_LIST"],
                        input_references=refs,original_simulation_commit=ORIGINAL_COMMIT,
                        original_check_commits=post_commits,python=platform.python_version(),
                        numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,
                        script_sha256=digest(root/SCRIPT_REL))
        raw=read_table(root/"results/P2F/VALIDATION_RAW.csv.gz")
        checks.add("raw_rows", len(raw)==304000,len(raw),304000)
        check_provenance(raw,"raw",checks)
        selected=select_t5(raw)
        verify_keys(selected,expected_keys());checks.add("exact_selected_keys",True,len(selected),74000)
        f=validate_rows(selected);checks.add("row_values_and_decisions",True)
        tables=summarize(f)
        originals=[]
        for name in ("VALIDATION_FALSE_VERDICTS.csv","VALIDATION_COVERAGE_POWER.csv","VALIDATION_DECISION.csv"):
            table=read_table(root/"results/P2F"/name);check_provenance(table,name,checks);originals.append(table)
        verify_summaries(f,tables,originals,checks)
        for name,sha in hashes.items(): checks.add("unchanged_input:"+name,digest(root/name)==sha)
        out.mkdir(parents=True)
        names=("T5D_GROUPS.csv","T5D_QUANTILES.csv","T5D_SE_QUINTILES.csv","T5D_NUISANCE.csv")
        for name,table in zip(names,tables):table.assign(**stamp).to_csv(out/name,index=False)
        pd.DataFrame(checks.rows).assign(**stamp).to_csv(out/"T5D_CHECKS.csv",index=False)
        matplotlib_version=make_figures(out,figs)
        metadata.update(status="complete",matplotlib=matplotlib_version,groups=17,selected_rows=len(f),checks_passed=len(checks.rows),
                        outputs_sha256={str(p.relative_to(root)):digest(p) for p in sorted(list(out.glob("*.csv"))+list(figs.glob("*.png")))})
        print(f"T5-D1 complete: {len(checks.rows)}/{len(checks.rows)} checks passed; 17 groups; 74000 rows. No new simulations.")
        return 0
    except Exception as exc:
        checks.rows.append(dict(check="execution_exception",observed=repr(exc),expected="no exception",passed=False))
        out.mkdir(parents=True,exist_ok=True)
        pd.DataFrame(checks.rows).assign(**stamp).to_csv(out/"T5D_CHECKS.csv",index=False)
        metadata["error"]=repr(exc)
        print(f"T5-D1 stopped: {exc}",file=sys.stderr)
        return 2
    finally:
        metadata["finished_utc"]=datetime.now(timezone.utc).isoformat()
        (out/"T5D_META.json").write_text(json.dumps(metadata,indent=2,allow_nan=False)+"\n")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selftest",action="store_true")
    mode.add_argument("--run",action="store_true")
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[2])
    args=ap.parse_args()
    if args.selftest:
        rows=selftests();bad=[x for x in rows if not x["passed"]]
        print(json.dumps(dict(selftests=len(rows),passed=len(rows)-len(bad),failures=bad),indent=2))
        return 2 if bad else 0
    return run(args.root.resolve())


if __name__=="__main__":
    raise SystemExit(main())
