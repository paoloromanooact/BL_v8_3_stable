"""Independent check and recount of the single T5 power-sensitivity run (outputs preserved in 0a6853a) before any
interpretation. Does not import scripts/t5_power_sensitivity.py or the sharpbl modules: it re-derives every number
from RAW.csv.gz with pandas and compares it with SUMMARY.csv, PAIRED_LS.csv and PAIRED_METHODS.csv.

Plan docs/T5_POWER_SENSITIVITY_PLAN.md (4b67632) with A1 (8dc6d48) and A2 (6024237).

    .venv/bin/python scripts/t5_power_check.py
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
import traceback
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/T5_POWER_SENSITIVITY"
OUT = ROOT / "results/T5_POWER_SENSITIVITY_CHECK"
RUN_COMMIT = "44633cb0a65390496c67ac3d32224d199d50df5b"
SHA = {"docs/T5_POWER_SENSITIVITY_PLAN.md": "fac76b1ab60d0aba003bd3c895d03d2ecf9e894281a3465c175549b8d41a3fcd",
       "docs/T5_POWER_SENSITIVITY_PLAN_A1.md": "603237898eed6b45b3102e1b7fdcf247fe2dfa8990107be7812095e9c6dab262",
       "docs/T5_POWER_SENSITIVITY_PLAN_A2.md": "df4912c0f351a4a6d6d1e224e6dfb00c866265ec2f749cc99790d9d57a28e857"}
ETA = 3.56e-25
E_L = {"L1": -0.051494066951105075, "S1": -0.051494066951105075, "L2": -0.10305075387820256,
       "S2": -0.10305075387820256, "N": 0.0}
ALPHA = 0.0125
NOISE = [(f, xs) for f in ("ar1_05", "ar1_09", "steps20") for xs in (0.5, 1.0, 2.0)]
SIGNALS, METHODS = ("N", "L1", "L2", "S1", "S2"), ("M", "G", "B", "O")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a):
    p = subprocess.run(["git", *a], cwd=ROOT, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)} failed")
    return p.stdout


def close(a, b, rel=1e-12, abs_=0.0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    both_nan = np.isnan(a) & np.isnan(b)
    return bool(np.all(both_nan | (np.abs(a - b) <= rel * np.maximum(np.abs(a), np.abs(b)) + abs_)))


def main():
    t0 = time.time()
    res = []

    def ok(name, cond, value=""):
        res.append(dict(check=name, passed=bool(cond), value=str(value)))
        print(("PASS " if cond else "FAIL ") + name + (f"  [{value}]" if value != "" else ""), flush=True)
    meta = dict(mode="independent check and recount", outcome="non riuscito")
    code = 1
    rel = str(Path(__file__).resolve().relative_to(ROOT))
    clean = (not git("status", "--porcelain", "--untracked-files=no").strip()
             and subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, capture_output=True).returncode == 0)
    head = git("rev-parse", "HEAD").decode().strip()
    out = OUT / head[:12] if clean else None
    try:
        meta.update(git_commit=head, git_dirty=0 if clean else 1, script_sha256=sha(__file__))
        # 1. provenance
        m = json.loads((RUN / "META.json").read_text())
        ok("META: outcome eseguita, commit 44633cb, git_dirty 0", m["outcome"] == "eseguita" and m["git_commit"] == RUN_COMMIT
           and m["git_dirty"] == 0, m["git_commit"][:12])
        ok("frozen plan, A1, A2: SHA-256 of the files = META = frozen values",
           all(sha(ROOT / p) == h for p, h in SHA.items()) and m["sha256_plan"] == SHA["docs/T5_POWER_SENSITIVITY_PLAN.md"]
           and m["sha256_A1"] == SHA["docs/T5_POWER_SENSITIVITY_PLAN_A1.md"]
           and m["sha256_A2"] == SHA["docs/T5_POWER_SENSITIVITY_PLAN_A2.md"], "")
        run_script = hashlib.sha256(git("show", f"{RUN_COMMIT}:scripts/t5_power_sensitivity.py")).hexdigest()
        ok("script SHA-256 in META = script at the run commit", m["sha256_script"] == run_script, run_script[:16])
        ok("SUMMARY.csv SHA-256 = META", sha(RUN / "SUMMARY.csv") == m["sha256_SUMMARY"], "")
        rec_ok = all((ROOT / p).exists() and json.loads((ROOT / p).read_text())["sha256_script"] == run_script
                     for p in m["receipts"].values())
        ok("the three preliminary receipts exist and are bound to the same script", rec_ok and set(m["receipts"]) ==
           {"SELFTEST", "GATE", "BENCHMARK"}, ", ".join(sorted(m["receipts"])))
        # 2. completeness and seeds
        raw = pd.read_csv(RUN / "RAW.csv.gz", float_precision="round_trip", keep_default_na=False,
                          na_values=["", "nan", "NaN"], low_memory=False)
        ok("RAW: 180000 rows, unique (n, k, signal, method)", len(raw) == 180000 and not raw.duplicated(
            ["n", "k", "signal", "method"]).any(), len(raw))
        g = raw.groupby(["n", "k"]).size()
        ok("RAW: 9 configurations x 1000 replicas x 20 responses", len(g) == 9000 and (g == 20).all()
           and set(raw["n"]) == set(range(9)) and set(raw["k"]) == set(range(1000)), "")
        ok("seeds: base 31000000 + 100000 n + k, bootstrap 32000000 + 100000 n + k",
           (raw["seed_base"] == 31_000_000 + 100_000 * raw["n"] + raw["k"]).all()
           and (raw["seed_boot"] == 32_000_000 + 100_000 * raw["n"] + raw["k"]).all(), "")
        fx = raw.groupby("n")[["form", "x_scale"]].first()
        ok("noise configuration n -> (form, x_scale) as in the plan", all(tuple(fx.loc[n]) == NOISE[n] for n in range(9)), "")
        # 3. technical errors, boundary cases, states
        tech = (RUN / "TECHNICAL_ERRORS.csv").read_text().strip()
        bnd = (RUN / "BOUNDARY_CASES.csv").read_text().strip()
        ok("no technical errors and no boundary cases (files empty)", tech == "" and bnd == "", "")
        st = raw["state"].value_counts().to_dict()
        ok("states only 'ok' or 'errore previsto'", set(st) <= {"ok", "errore previsto"}, json.dumps(st))
        er = raw[raw["state"] != "ok"]
        ok("every expected error has verdict 'errore' and a reason", (er["verdict"] == "errore").all()
           and (er["reason"].astype(str).str.len() > 0).all(), len(er))
        ok("O never in error (known variance)", (raw.loc[raw["method"] == "O", "state"] == "ok").all(), "")
        # 4. invariants
        tgt = raw["signal"].map(E_L) * ETA
        ok("target = e_L * eta_bar exactly (0 for N)", (raw["target"] == tgt).all(), "")
        w = raw.pivot_table(index=["n", "k", "signal"], columns="method", values="beta_wls", aggfunc="first")
        ok("beta_WLS identical across the four methods of a response", all((w[mm] == w["M"]).all() for mm in METHODS), "")
        bw = raw[raw["method"] == "M"].set_index(["n", "k", "signal"])["beta_wls"].unstack("signal")
        dev = {}
        for sgl in SIGNALS[1:]:
            tau = 1e-12 * abs(E_L[sgl] * ETA) + 1e-38
            dev[sgl] = float(((bw[sgl] - bw["N"]) - E_L[sgl] * ETA).abs().max() / tau)
        for L, S in (("L1", "S1"), ("L2", "S2")):
            tau = 1e-12 * abs(E_L[L] * ETA) + 1e-38
            dev[L + S] = float((bw[L] - bw[S]).abs().max() / tau)
        ok("A1 identities recomputed: beta_WLS(signal) - beta_WLS(N) = Delta_beta and L = S within tau_beta",
           max(dev.values()) <= 1.0, json.dumps({k: round(v, 5) for k, v in dev.items()}))
        o = raw[raw["method"] == "O"].set_index(["n", "k", "signal"])["se"].unstack("signal")
        ok("O: SE identical across the five signals (design only) within 1e-12", all(close(o[sg], o["N"]) for sg in SIGNALS), "")
        for mm in ("M", "B", "O"):
            sub = raw[(raw["method"] == mm) & (raw["state"] == "ok")]
            ok(f"{mm}: beta = beta_WLS", (sub["beta"] == sub["beta_wls"]).all(), len(sub))
        okr = raw[(raw["state"] == "ok") & raw["method"].isin(["M", "G", "O"])]
        v = np.where(okr["hi"] < 0, "supportato", np.where(okr["lo"] > 0, "opposto", "non deciso"))
        ok("M, G, O: verdict consistent with the interval; SE > 0", (okr["verdict"].to_numpy() == v).all()
           and (okr["se"] > 0).all(), "")
        cov = ((okr["lo"] <= okr["target"]) & (okr["target"] <= okr["hi"])).astype(int)
        ok("M, G, O: coverage, below, above flags consistent with lo, hi, target",
           (okr["covered"] == cov).all() and (okr["below"] == (okr["lo"] > okr["target"]).astype(int)).all()
           and (okr["above"] == (okr["hi"] < okr["target"]).astype(int)).all(), "")
        b = raw[(raw["method"] == "B") & (raw["state"] == "ok")]
        vb = np.where(b["p_low"] <= ALPHA, "supportato", np.where(b["p_high"] <= ALPHA, "opposto", "non deciso"))
        ok("B: verdict from p_low/p_high with ALPHA 0.0125; p in (0, 1]; clusters >= 2",
           (b["verdict"].to_numpy() == vb).all() and b["p_low"].between(1e-12, 1).all() and b["p_high"].between(1e-12, 1).all()
           and (b["n_cluster"] >= 2).all(), sorted(b["n_cluster"].unique().tolist()))
        gg = raw[(raw["method"] == "G") & (raw["state"] == "ok")]
        ok("G: beta_G - beta_WLS column = beta - beta_WLS", close(gg["beta_g_minus_wls"], gg["beta"] - gg["beta_wls"]), "")
        mm_ = raw[raw["method"] == "M"].set_index(["n", "k", "signal"])["state"]
        gm = raw[raw["method"] == "G"].set_index(["n", "k", "signal"])["state"]
        ok("G in error whenever M is in error", ((mm_ != "ok") <= (gm != "ok")).all(), int((mm_ != "ok").sum()))
        idd = pd.read_csv(RUN / "IDENTITY_DIAGNOSTICS.csv")
        ok("identity diagnostics: 9000 units, every deviation <= its tolerance",
           len(idd) == 9000 and float(idd.drop(columns=["n", "k"]).max().max()) <= 1.0,
           f"max {float(idd.drop(columns=['n', 'k']).max().max()):.4f}")
        # 5. recount of SUMMARY.csv
        summ = pd.read_csv(RUN / "SUMMARY.csv", float_precision="round_trip", keep_default_na=False,
                           na_values=["", "nan", "NaN"], low_memory=False)
        rows = []
        for (n, sgl, mt), gr in raw.groupby(["n", "signal", "method"]):
            N = len(gr)
            okg = gr[gr["state"] == "ok"]
            r = dict(n=n, signal=sgl, method=mt, N=N)
            for vv in ("supportato", "opposto", "non deciso", "errore"):
                c = int((gr["verdict"] == vv).sum())
                r[f"n_{vv.replace(' ', '_')}"] = c
                r[f"frac_{vv.replace(' ', '_')}"] = c / N
                r[f"mcse_{vv.replace(' ', '_')}"] = math.sqrt(c / N * (1 - c / N) / N)
            if sgl == "N":
                f = r["n_supportato"] + r["n_opposto"]
                r.update(false_total=f, false_frac=f / N)
            if mt != "B":
                r["covered"] = int(gr["covered"].fillna(0).sum())
                vb_ = float(np.var(okg["beta"], ddof=1))
                r.update(n_valid=len(okg), mean_beta=float(okg["beta"].mean()), sd_beta=math.sqrt(vb_),
                         mean_se=float(okg["se"].mean()), R=float(np.mean(okg["se"] ** 2) / vb_))
                if mt == "G":
                    r["bias_G"] = r["mean_beta"] - float(gr["target"].iloc[0])
                    r["mean_G_minus_WLS"] = float(okg["beta_g_minus_wls"].mean())
            ms = raw[(raw["n"] == n) & (raw["signal"] == sgl) & (raw["method"] == "M")]["beta_wls"]
            r.update(n_constructed=len(ms), mean_beta_wls_all=float(ms.mean()), sd_beta_wls_all=float(ms.std(ddof=1)))
            rows.append(r)
        mine = pd.DataFrame(rows).set_index(["n", "signal", "method"]).sort_index()
        theirs = summ.set_index(["n", "signal", "method"]).sort_index()
        ok("SUMMARY: same 180 groups (9 x 5 x 4)", len(theirs) == 180 and mine.index.equals(theirs.index), len(theirs))
        bad = []
        for col in mine.columns:
            a = mine[col]
            bcol = pd.to_numeric(theirs[col], errors="coerce") if col in theirs else None
            if bcol is None:
                bad.append(f"{col} missing")
                continue
            sel = a.notna()
            if col.startswith(("n_", "N", "false_total", "covered", "n_valid", "n_constructed")):
                if not (a[sel].astype(float) == bcol[sel]).all():
                    bad.append(col)
            elif not close(a[sel], bcol[sel], rel=1e-10, abs_=1e-300):
                bad.append(col)
        ok("SUMMARY: every recomputed count exact and every statistic within 1e-10 relative", not bad, ", ".join(bad))
        # 6. recount of the paired tables (T5-D2 §6.5 formula)
        def pse(bb, cc, N):
            return math.sqrt((bb + cc - (cc - bb) ** 2 / N) / (N * (N - 1)))
        pls = pd.read_csv(RUN / "PAIRED_LS.csv", float_precision="round_trip")
        vv = raw.set_index(["n", "k", "method", "signal"])["verdict"].unstack("signal")
        badp = 0
        for _, r in pls.iterrows():
            S, L = r["pair"].split("-")
            sub = vv.xs(r["method"], level="method").xs(r["n"], level="n")
            eL, eS = sub[L] == "supportato", sub[S] == "supportato"
            bb, cc, N = int((eL & ~eS).sum()), int((eS & ~eL).sum()), len(sub)
            badp += not (bb == r["b_only_L"] and cc == r["c_only_S"] and N == r["N"] and (cc - bb) / N == r["delta"]
                         and abs(pse(bb, cc, N) - r["se_paired"]) <= 1e-12)
        ok("PAIRED_LS recomputed (b, c, delta, paired SE)", badp == 0 and len(pls) == 9 * 4 * 2, f"{len(pls)} rows")
        pm = pd.read_csv(RUN / "PAIRED_METHODS.csv", float_precision="round_trip")
        vm = raw.set_index(["n", "k", "signal", "method"])["verdict"].unstack("method")
        badm = 0
        for _, r in pm.iterrows():
            sub = vm.xs(r["n"], level="n").xs(r["signal"], level="signal")
            ev = (lambda x: x == "supportato") if r["event"] == "supportato" else (lambda x: x.isin(["supportato", "opposto"]))
            e1, e2 = ev(sub[r["method_1"]]), ev(sub[r["method_2"]])
            bb, cc, N = int((e1 & ~e2).sum()), int((e2 & ~e1).sum()), len(sub)
            badm += not (bb == r["b_only_1"] and cc == r["c_only_2"] and N == r["N"]
                         and abs(pse(bb, cc, N) - r["se_paired"]) <= 1e-12)
        exp_rows = 9 * (5 + 1) * len(list(combinations(METHODS, 2)))
        ok("PAIRED_METHODS recomputed (6 method pairs, 'supportato' for 5 signals + false verdicts under N)",
           badm == 0 and len(pm) == exp_rows, f"{len(pm)} rows")
        n_ok = sum(r["passed"] for r in res)
        meta.update(n_checks=len(res), n_passed=n_ok, outcome="superato" if n_ok == len(res) else "non superato")
        code = 0 if n_ok == len(res) else 1
        print(f"{n_ok}/{len(res)} passed")
    except Exception as exc:                      # noqa: BLE001
        meta.update(exception_type=type(exc).__name__, exception=str(exc), traceback=traceback.format_exc())
        print(traceback.format_exc())
    finally:
        meta["duration_s"] = time.time() - t0
        if out is None:
            print("tree not clean or script not committed: results printed only, no receipt written")
        else:
            out.mkdir(parents=True, exist_ok=False)
            pd.DataFrame(res, columns=["check", "passed", "value"]).to_csv(out / "CHECKS.csv", index=False,
                                                                           lineterminator="\n")
            (out / "META.json").write_text(json.dumps(meta, indent=2, default=str))
            print(f"receipt: {out.relative_to(ROOT)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
