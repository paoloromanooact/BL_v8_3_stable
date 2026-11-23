"""MDI pilot, phase 5: measurement on the level-2 full-disk magnetograms (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md
§4-5 and frozen amendment A1). Offline: reads the FITS already downloaded and verified by the fetch checkpoint.

For every level-2 group and for both assignments (A1 main, original secondary), for images A and B:
  - geometry and QUALITY from the JSOC keywords of the record (preserved ANSWERS.jsonl), admissible set of the rule
    (A1 {0, 0x200}; original {0});
  - FITS taken only from the checkpoint with SHA verified before reading (a mismatch stops the run); a file not
    completed in the checkpoint gives 'fits_missing' (no substitution, no other image searched);
  - tilt_window measure through the full-disk adapter: 50 G (main) and 100 G (sensitivity), 4000 G cap, >= 10 pixels per
    polarity, missing > 5 % fails, mu >= 0.8 over the whole window;
  - observed field dispersion (scaled MAD of B_r, not instrumental noise) in two quiet windows centred at L_DPD +- 30 deg
    at the DPD latitude: a side is dropped if the box enlarged by +-6/+-8 deg contains the centre of a DPD group of the
    same day, if the window violates mu >= 0.8, or if < 50 % of its pixels are finite.
Output results/MDI_PILOT_L2/L2_RECORDS.csv (one row per group x rule x image) and META.json; refuses to overwrite.

    .venv/bin/python scripts/mdi_pilot_measure_l2.py --selftest
    .venv/bin/python scripts/mdi_pilot_measure_l2.py --run      # after the FITS step and the code review
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
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import tilt_window as tw  # noqa: E402

SEL = ROOT / "results/MDI_PILOT_SELECTION"
MD = ROOT / "results/MDI_PILOT_L2_METADATA"
PLAN, PLAN_REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1", ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
STATE, DEST = ROOT / "results/MDI_PILOT_L2_FITS", ROOT / "data/sharp/mdi_pilot_l2"
OUT = ROOT / "results/MDI_PILOT_L2"
THRESHOLDS = {"main": 50.0, "sens100": 100.0}
BMAX, MIN_PIX, MISSING_MAX = 4000.0, 10, 0.05
QUIET_OFFSET, QUIET_LAT_BOX, QUIET_LON_BOX, QUIET_MIN_FINITE = 30.0, 12.0, 16.0, 0.5
RULES = {"A1": (0, 0x200), "original": (0,)}
KEYS = ("status", "npos", "nneg", "flux_pos_mx", "flux_neg_mx", "area_pos_msh", "area_neg_msh", "lat_bar", "lon_pos", "lat_pos",
        "lon_neg", "lat_neg", "leading_sign", "tilt_deg", "sep_deg", "n_win", "n_missing_win", "mu_min")
GEOM_KEYS = ("CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CROTA2", "RSUN_OBS", "CRLT_OBS", "CRLN_OBS", "QUALITY")


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, m)
    spec.loader.exec_module(m)
    return m


AD = _load("mdi_fd_adapter", "scripts/mdi_fd_adapter.py")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def keywords_by_trec(answers):
    """T_REC -> dict of the record keywords (geometry and QUALITY), from the preserved rs_list answers."""
    out = {}
    for a in answers:
        if a.get("request_status") != "ok":
            continue
        kw = {k["name"]: k["values"] for k in a["doc"]["keywords"]}
        for j, t in enumerate(kw.get("T_REC", [])):
            out[t] = {k: kw[k][j] for k in GEOM_KEYS if k in kw}
    return out


def mad_scaled(x):
    x = x[np.isfinite(x)]
    return float(1.4826 * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


def quiet(data, geom, lat0, lon0, dpd_day):
    lat, lon, mu = geom
    out, vals = {}, []
    for side, tag in ((-1, "qm"), (1, "qp")):
        lq = (lon0 + side * QUIET_OFFSET) % 360.0
        out[f"{tag}_lon"] = lq
        win = tw.window_mask(lat, lon, lat0, lq, valid=np.isfinite(mu))
        hit = ((dpd_day.lat - lat0).abs() <= QUIET_LAT_BOX) & (((dpd_day.lon - lq + 180.0) % 360.0 - 180.0).abs() <= QUIET_LON_BOX)
        if hit.any():                                    # order of the reasons as in the protocol (Q1)
            out[f"{tag}_status"] = "dpd_group_inside"
        elif not win.any():
            out[f"{tag}_status"] = "window_off_disk"
        elif np.nanmin(mu[win]) < AD.MU_MIN:
            out[f"{tag}_status"] = "window_outside_mu_domain"
        else:
            br = (data / mu)[win]
            fin = float(np.isfinite(br).mean())
            out[f"{tag}_finite_frac"] = fin
            if fin < QUIET_MIN_FINITE:
                out[f"{tag}_status"] = "finite_below_50pct"
            else:
                out[f"{tag}_status"], out[f"{tag}_mad_g"] = "ok", mad_scaled(br)
                vals.append(out[f"{tag}_mad_g"])
    out["quiet_mad_g"] = float(np.mean(vals)) if vals else np.nan
    return out


def measure_image(path, k, lat0, lon0, admissible, dpd_day):
    try:
        [float(k[x]) for x in AD.KEYS]
    except (KeyError, TypeError, ValueError):
        return dict(main_status="geometry_keywords_unparsable")
    data = AD.read_data(path)
    geom = AD.geometry(k, data.shape)
    row = {}
    for tag, bmin in THRESHOLDS.items():
        m = AD.measure(data, k, lat0, lon0, bmin, BMAX, MIN_PIX, MISSING_MAX, geom=geom, admissible=admissible)
        row.update({f"{tag}_{x}": m[x] for x in KEYS if x in m})
        if "quality" in m:
            row[f"{tag}_quality_rejected"] = m["quality"]
    row.update(quiet(data, geom, lat0, lon0, dpd_day))
    return row


def build(samp, choices, answers, checkpoint, dest, dpd):
    """Rows: one per level-2 group x rule x image."""
    kw = keywords_by_trec(answers)
    done = {e["path"]: e for e in checkpoint if e["status"] == "ok"}
    l2 = samp[samp.level2.astype(str) == "True"].set_index(["noaa", "day"])
    rows = []
    for rule, ch in choices.items():
        for c in ch.to_dict("records"):
            g = l2.loc[(c["noaa"], c["day"])]
            dpd_day = dpd[dpd.day == c["day"]]
            for img in ("A", "B"):
                base = dict(rule=rule, noaa=c["noaa"], day=c["day"], image=img, choice_status=c["status"],
                            pair_status=c.get("pair_status"), T_REC=c.get(img))
                if c["status"] != "ok" or not isinstance(c.get(img), str):
                    rows.append(dict(base, status="no_image" if c["status"] == "ok" else c["status"]))
                    continue
                path = c.get(f"{img}_path")
                e = done.get(path)
                if e is None:
                    rows.append(dict(base, status="fits_missing"))
                    continue
                f = Path(dest) / e["file"]
                if not f.exists() or sha(f) != e["sha256"]:
                    raise SystemExit(f"FITS {e['file']} missing or SHA differs from the checkpoint: stop")
                k = kw.get(c[img])
                if k is None:
                    raise SystemExit(f"no keywords for {c[img]}")
                r = measure_image(f, k, float(g.lat), float(g.lon), RULES[rule], dpd_day)
                rows.append(dict(base, file=e["file"], sha256=e["sha256"], quality=k.get("QUALITY"),
                                 interval_s=c.get("A_interval"), dt_h=c.get(f"{img}_dt_h"), status=r["main_status"], **r))
    return pd.DataFrame(rows)


def run(out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        sys.exit("tracked tree not clean")
    FE = _load("mdi_fd_fetch", "scripts/mdi_fd_fetch.py")
    probs = FE.gate()
    if probs:
        sys.exit("gate: " + "; ".join(probs))
    md = json.loads((MD / "META.json").read_text())
    if any(sha(MD / n) != h for n, h in md["products_sha256"].items()):
        sys.exit("metadata products differ from their META")
    plan_sha = sha(PLAN / "META.json")
    ck = FE.read_checkpoint(STATE / "CHECKPOINT.jsonl")
    if not ck or any(e.get("plan_meta_sha256") != plan_sha for e in ck):
        sys.exit("checkpoint missing or bound to another plan")
    samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
    rd = lambda n: pd.read_csv(PLAN / n, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")  # noqa: E731
    choices = {"A1": rd("CHOICES_A1.csv"), "original": rd("CHOICES_ORIGINAL.csv")}
    answers = [json.loads(x) for x in (MD / "ANSWERS.jsonl").read_text().splitlines() if x.strip()]
    CAT = _load("t3_mwo_catalogue", "scripts/t3_mwo_catalogue.py")
    dpd = CAT.dpd_groups(years=range(1995, 2012))
    t = build(samp, choices, answers, ck, DEST, dpd)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        t.to_csv(tmp / "L2_RECORDS.csv", index=False)
        fz = json.loads(A1_FREEZE.read_text())
        meta = dict(a1_sha256=fz["sha256"], protocol_sha256=fz["parent_sha256"], script_sha256=sha(__file__),
                    adapter_sha256=sha(ROOT / "scripts/mdi_fd_adapter.py"), module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"),
                    plan_meta_sha256=plan_sha, metadata_meta_sha256=sha(MD / "META.json"), checkpoint_sha256=sha(STATE / "CHECKPOINT.jsonl"),
                    selection_meta_sha256=sha(SEL / "META.json"),
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
        meta["products_sha256"] = {"L2_RECORDS.csv": sha(tmp / "L2_RECORDS.csv")}
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(t.groupby(["rule", "image"]).status.value_counts().to_string())
    return 0


# ---------------------------------------------------------------- synthetic environment (also used by the recount)

def synthetic_env(td, tilt=10.0):
    """Two level-2 groups, synthetic full-disk FITS with a bipole of known tilt drawn at the DPD position, keywords
    in rs_list form, a checkpoint with SHAs, and DPD rows of the day (one contaminating the +30 deg quiet window)."""
    from astropy.io import fits
    td = Path(td)
    dest = td / "fits"
    dest.mkdir(parents=True)
    k = dict(CRPIX1=512.5, CRPIX2=512.5, CDELT1=1.98, CDELT2=1.98, CROTA2=0.0, RSUN_OBS=960.0, CRLT_OBS=5.0, CRLN_OBS=100.0)
    groups = [("9001", "2000-06-01", 15.0, 105.0), ("9002", "2000-06-01", -18.0, 92.0)]
    recs, ck, ch = [], [], []
    for n, (noaa, day, lat0, lon0) in enumerate(groups):
        for img, q in (("A", "0x00000200"), ("B", "0x00000000")):
            trec = f"2000.06.01_1{n}:{'00' if img == 'A' else '36'}:00_TAI"
            kk = dict(k, QUALITY=q, CROTA2=180.0 if (n, img) == (1, "B") else 0.0)   # SOHO flipped: CROTA2 = 180
            lat, lon, mu = AD.geometry(kk, (1024, 1024))
            t = np.radians(tilt * (1 if lat0 > 0 else -1))
            cl = np.cos(np.radians(lat0))
            lead = (lat0 - 2 * np.sin(t), lon0 + 2 * np.cos(t) / cl)
            foll = (lat0 + 2 * np.sin(t), lon0 - 2 * np.cos(t) / cl)
            br = np.zeros(lat.shape)
            for s, (la, lo) in ((1.0, lead), (-1.0, foll)):
                dl = ((lon - lo + 180) % 360 - 180) * cl
                br += s * 800.0 * np.exp(-((lat - la) ** 2 + dl ** 2) / (2 * 0.8 ** 2))
            rng = np.random.default_rng(n * 2 + (img == "B"))
            data = np.where(np.isfinite(mu), (br + rng.normal(0, 5, br.shape)) * mu, np.nan).astype(np.float32)
            name = f"f_{noaa}_{img}.fits"
            fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data)]).writeto(dest / name)
            path = f"/SUM/{noaa}/{img}"
            ck.append(dict(path=path, T_REC=trec, status="ok", file=name, sha256=sha(dest / name)))
            recs.append(dict(T_REC=trec, INTERVAL="300", **{x: str(v) for x, v in kk.items()}))
        ch.append(dict(noaa=noaa, day=day, status="ok", A=recs[-2]["T_REC"], A_path=f"/SUM/{noaa}/A", A_interval=300.0, A_dt_h=-0.5,
                       B=recs[-1]["T_REC"], B_path=f"/SUM/{noaa}/B", B_dt_h=1.1, pair_status="after"))
    doc = dict(status=0, count=len(recs), keywords=[dict(name=x, values=[r[x] for r in recs]) for x in recs[0]],
               segments=[dict(name="data", values=["/SUM"] * len(recs))])
    answers = [dict(noaa="9001", day="2000-06-01", request_status="ok", doc=doc)]
    samp = pd.DataFrame(dict(noaa=[g[0] for g in groups], day=[g[1] for g in groups], lat=[g[2] for g in groups],
                             lon=[g[3] for g in groups], level2=[True, True]))
    dpd = pd.DataFrame(dict(day=["2000-06-01"] * 3, lat=[15.0, -18.0, 15.0], lon=[105.0, 92.0, 135.0]))
    choices = {"A1": pd.DataFrame(ch), "original": pd.DataFrame([dict(c, status="no_magnetogram", A=None, B=None) if i == 1 else c
                                                                 for i, c in enumerate(ch)])}
    return dict(samp=samp, choices=choices, answers=answers, checkpoint=ck, dest=dest, dpd=dpd)


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    with tempfile.TemporaryDirectory() as td:
        env = synthetic_env(td)
        t = build(env["samp"], env["choices"], env["answers"], env["checkpoint"], env["dest"], env["dpd"])
        a1 = t[t.rule == "A1"]
        ok("A1: four images measured (A with QUALITY 0x200 admitted, B with 0)", (a1.status == "ok").all() and len(a1) == 4, list(a1.status))
        n = a1[a1.noaa == "9001"].iloc[0]
        s = a1[a1.noaa == "9002"].iloc[0]
        ok("tilt recovered in both hemispheres (P1 convention: leading -> following, ~180 -/+ tilt)",
           abs(tw.diff_ax(n.main_tilt_deg, 170.0)) < 1.0 and abs(tw.diff_ax(s.main_tilt_deg, -170.0)) < 1.0, (n.main_tilt_deg, s.main_tilt_deg))
        o = t[t.rule == "original"]
        ok("original rule: the 0x200 image A is rejected for QUALITY, B (0) measured; a group without choice kept",
           o[(o.noaa == "9001") & (o.image == "A")].status.iloc[0] == "quality_not_zero"
           and o[(o.noaa == "9001") & (o.image == "B")].status.iloc[0] == "ok" and (o[o.noaa == "9002"].status == "no_magnetogram").all())
        ok("quiet windows: +30 deg side dropped for a DPD group of the same day, other side gives the noise scale",
           n.qp_status == "dpd_group_inside" and n.qm_status == "ok" and 4.0 < n.quiet_mad_g < 6.0, (n.qp_status, n.qm_status, n.quiet_mad_g))
        ok("quiet windows: group at CMD -8 deg -> both sides reach mu < 0.8 and the dispersion is 'not available'",
           s.qm_status == s.qp_status == "window_outside_mu_domain" and np.isnan(s.quiet_mad_g), (s.qm_status, s.qp_status))
        f = env["dest"] / env["checkpoint"][0]["file"]
        kk = keywords_by_trec(env["answers"])[env["checkpoint"][0]["T_REC"]]
        d = AD.read_data(f)
        g = AD.geometry(kk, d.shape)
        d[(np.abs(g[0] - 15.0) <= 4.0) & (np.abs(g[1] - 75.0) <= 9.0)] = np.nan
        q = quiet(d, g, 15.0, 105.0, env["dpd"].iloc[:0])
        ok("quiet windows: < 50 % finite pixels drops the side (the other side fails mu)",
           q["qm_status"] == "finite_below_50pct" and q["qp_status"] == "window_outside_mu_domain", (q["qm_status"], q["qp_status"]))
        ck2 = [dict(e) for e in env["checkpoint"]]
        ck2[0]["sha256"] = "0" * 64
        try:
            build(env["samp"], env["choices"], env["answers"], ck2, env["dest"], env["dpd"])
            ok("SHA differing from the checkpoint stops the run", False)
        except SystemExit:
            ok("SHA differing from the checkpoint stops the run", True)
        ck3 = [e for e in env["checkpoint"] if e["path"] != "/SUM/9002/B"]
        t3 = build(env["samp"], env["choices"], env["answers"], ck3, env["dest"], env["dpd"])
        ok("a file not completed in the checkpoint -> fits_missing, no substitution",
           t3[(t3.rule == "A1") & (t3.noaa == "9002") & (t3.image == "B")].status.iloc[0] == "fits_missing")
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
