"""Comparisons A1, A2, B of the frozen protocol (6d6fd12, amendment A1) with Codex's adapter and kernels.

Inputs: patch_download_a1 receipts through mdi_hmi_patch_io.load_selected (SHA-256, identity, WCS, observer and the
certified minimum of mu checked there); measures with mdi_overlap_kernels (strict: a non-finite or out-of-domain mask
pixel makes the branch unavailable). Writes PAIR_ROWS.csv, SUMMARY.csv and META.json; refuses to overwrite.

    cd scripts && ../.venv/bin/python mdi_hmi_comparison_run.py --out ../results/MDI_HMI_COMPARISON/run_<commit>
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

import mdi_hmi_patch_io as io
import mdi_overlap_kernels as K

MU_MIN, FLAG = 0.8, 2.107


def branch(r, field):
    if not r["footprint"].any():
        return dict(status="empty_footprint")
    prox = K.radial_proxy(field, r["geometry"]["mu"], r["footprint"], mu_min=MU_MIN)
    if prox["status"] != "ok":
        return dict(status=prox["status"], n_bad=prox["n_bad"])
    return K.measure_field(prox["field_g"], r["footprint"], r["lon"], r["lat"], r["area_cm2"], radius_cm=r["radius_cm"])


def row(comp, p, ref, cand):
    d = K.paired_differences(ref, cand)
    out = dict(comparison=comp, slot=int(p["slot"]), stratum=p["stratum"], TARPNUM=p["TARPNUM"], HARPNUM=p["HARPNUM"],
               quality_mdi=p["quality_mdi"], ref_status=ref.get("status"), cand_status=cand.get("status"),
               diff_status=d["status"])
    for side, m in (("ref", ref), ("cand", cand)):
        for k in ("phi_mx", "phi_pos_mx", "phi_neg_mx", "tilt_deg", "lat_mean_deg", "lon_mean_deg", "d_axial_g",
                  "d_axial_bal_g", "d_cm", "npos", "nneg", "leading_sign"):
            out[f"{side}_{k}"] = m.get(k, np.nan)
    if d["status"] == "ok":
        lam = ref["lat_mean_deg"]
        out.update(d=d["delta_tilt_deg"], d_ax=d["delta_tilt_axial_deg"], abs_d_ax=abs(d["delta_tilt_axial_deg"]),
                   lambda_ref=lam, d_gamma=(math.copysign(1, lam) * d["delta_tilt_axial_deg"] if lam != 0 else np.nan),
                   ratio_phi=1 + d["relative_flux"],
                   **{k: v for k, v in d.items() if k.startswith(("delta_", "centroid_")) and not k.startswith("delta_tilt")})
    return out


def stats(v):
    v = np.asarray([x for x in v if np.isfinite(x)], float)
    if not len(v):
        return dict(n=0)
    s = dict(n=len(v), median=float(np.median(v)), min=float(v.min()), max=float(v.max()), mean=float(v.mean()))
    s["s_over_sqrt_n"] = float(v.std(ddof=1) / math.sqrt(len(v))) if len(v) > 1 else np.nan
    return s


def summarise(df):
    rows = []
    for comp, g0 in df.groupby("comparison", sort=False):
        groups = [("all", g0)] + [(h, g0[g0.stratum.str.startswith(h)]) for h in "NS"] + \
                 [(s, g0[g0.stratum == s]) for s in ("N_central", "S_central", "N_lateral", "S_lateral")]
        for name, g in groups:
            ok = g[g.diff_status == "ok"]
            r = dict(comparison=comp, group=name, n_selected=len(g), n_evaluable=len(ok))
            for q in ("d_gamma", "d", "d_ax"):
                r.update({f"{q}_{k}": v for k, v in stats(ok.get(q, pd.Series(dtype=float))).items()})
            r["abs_d_ax_median"] = float(ok.abs_d_ax.median()) if len(ok) else np.nan
            if comp == "B" and name in ("all", "N", "S"):
                r["flag_2107"] = int(np.isfinite(r.get("d_gamma_median", np.nan)) and abs(r["d_gamma_median"]) >= FLAG)
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit("refusing to overwrite")
    D = io.BASE / "patch_download_a1"
    pairs, _ = io.plan()
    rows = []
    for p in pairs:
        s = int(p["slot"])
        # a record the adapter refuses (e.g. undocumented bitmap codes) is unavailable, never substituted
        loaded = {}
        for series, segs in ((io.HMI, ["bitmap", "Br", "Bt", "Bp", "magnetogram"]), (io.MDI, ["bitmap", "magnetogram"])):
            try:
                loaded[series] = io.load_selected(s, series, segs, directory=D)
            except ValueError as exc:
                loaded[series] = dict(error=f"adapter_refused: {exc}")
        h, m = loaded[io.HMI], loaded[io.MDI]
        bad = lambda r: dict(status=r["error"])  # noqa: E731
        ref_br = bad(h) if "error" in h else branch(h, h["arrays"]["Br"])
        if "error" in h:
            a1 = a2 = hl = bad(h)
        else:
            with np.errstate(divide="ignore", invalid="ignore"):
                los_vec = K.vector_to_los(h["arrays"]["Br"], h["arrays"]["Bt"], h["arrays"]["Bp"], h["geometry"])
            a1, a2 = branch(h, los_vec), branch(h, h["arrays"]["magnetogram"])
            hl = a2
        rows.append(row("A1", p, ref_br, a1))
        rows.append(row("A2", p, ref_br, a2))
        rows.append(row("B", p, hl, bad(m) if "error" in m else branch(m, m["arrays"]["magnetogram"])))
    df = pd.DataFrame(rows)
    a.out.mkdir(parents=True)
    df.to_csv(a.out / "PAIR_ROWS.csv", index=False)
    summarise(df).to_csv(a.out / "SUMMARY.csv", index=False)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=io.ROOT, capture_output=True, text=True).stdout.strip()
    meta = dict(protocol=io.PROTOCOL_HASH, amendment="42ca9d3c802079c4b16ef45b5639a812c25c34596c1b821216d511cd86162778",
                git_commit=commit, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                manifest_sha256=io.sha(D / "MANIFEST.json"),
                products_sha256={f.name: io.sha(f) for f in sorted(a.out.iterdir())})
    (a.out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(df.groupby("comparison")[["ref_status", "cand_status", "diff_status"]].agg(lambda x: x.value_counts().to_dict()))


if __name__ == "__main__":
    main()
