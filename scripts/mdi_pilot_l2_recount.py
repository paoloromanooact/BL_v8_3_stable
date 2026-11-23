"""Independent recount of the MDI pilot level-2 measurement (frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md and frozen
amendment A1). Own code, importing neither python/sharpbl/tilt_window.py nor scripts/mdi_fd_adapter.py nor the runner:
  - own keyword parsing of the preserved rs_list answers (geometry, QUALITY, INTERVAL; the same T_REC must carry the
    same keywords in every answer);
  - own FITS read (last HDU, BSCALE and BLANK by astropy) after the SHA-256 is recomputed against the checkpoint;
  - own orthographic geometry written as a rotation of the observer frame (disc cut rho^2 < 0.999, an implementation
    constant shared with the adapter and declared), own pixel area, own B_r = B_LOS / mu;
  - own window, mu >= 0.8 rule and QUALITY rule per assignment (A1 {0, 0x200}; original {0});
  - measurement with the own functions of the level-1 recount (scripts/mdi_pilot_l1_recount.py: thresholds, missing
    pixels, minimum pixels, spherical centroids, P1 tilt, leading polarity, separation, lat_bar, areas);
  - own quiet windows (same-day DPD centres from the own gDPD reader of the selection recount, mu, finite fraction,
    scaled MAD, mean of the valid sides);
  - rows: exactly one per level-2 group x rule x image, in order; choice status, T_REC, Delta t and INTERVAL from the
    recounted plan; 'fits_missing' only for paths without a completed checkpoint entry.
The receipt is complete (partial false) only on the real path; injected data gives partial true and writes nothing.

    .venv/bin/python scripts/mdi_pilot_l2_recount.py --selftest
    .venv/bin/python scripts/mdi_pilot_l2_recount.py --check
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[1]
L2 = ROOT / "results/MDI_PILOT_L2"
REC = ROOT / "results/MDI_PILOT_L2_RECOUNT"
SEL, MD = ROOT / "results/MDI_PILOT_SELECTION", ROOT / "results/MDI_PILOT_L2_METADATA"
PLAN, PLAN_REC = ROOT / "results/MDI_PILOT_L2_PLAN_A1", ROOT / "results/MDI_PILOT_L2_PLAN_A1_RECOUNT"
A1, A1_FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1.md", ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_AMENDMENT_A1_FREEZE.json"
STATE, DEST = ROOT / "results/MDI_PILOT_L2_FITS", ROOT / "data/sharp/mdi_pilot_l2"
R_CM, DISC = 6.96e10, 0.999
THR = {"main": 50.0, "sens100": 100.0}
ADM = {"A1": {0, 0x200}, "original": {0}}
GEO = ("CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CROTA2", "RSUN_OBS", "CRLT_OBS", "CRLN_OBS")
TOL_ANG, TOL_REL = 1e-6, 1e-9


def _mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


R1 = _mod("l1rec", "scripts/mdi_pilot_l1_recount.py")              # own measurement functions of the L1 recount
RC = _mod("mdrec", "scripts/mdi_fd_metadata_recount.py")            # own strict receipt


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- own keywords, geometry, quality

def own_keywords(answers):
    """T_REC -> keywords; (table, conflicts) where conflicts lists T_REC given with different values."""
    out, conflicts = {}, []
    for a in answers:
        if a.get("request_status") != "ok":
            continue
        cols = {c["name"]: c["values"] for c in a["doc"]["keywords"]}
        for j in range(int(a["doc"]["count"])):
            v = {n: cols[n][j] for n in GEO + ("QUALITY", "INTERVAL") if n in cols}
            t = cols["T_REC"][j]
            if t in out and out[t] != v:
                conflicts.append(t)
            out[t] = v
    return out, conflicts


def own_quality(v):
    s = "" if v is None else str(v).strip()
    if s in ("", "MISSING", "nan", "None"):
        return None, "missing"
    try:
        return int(s, 0) if s[:2].lower() == "0x" else int(s), "ok"
    except ValueError:
        return None, "unparsable"


def own_geometry(k, shape):
    """Image plane (arcsec, rotated by CROTA2 to solar north up) -> unit vector in the observer frame (x west,
    y north, z towards the observer) -> rotation by B0 about the x axis -> Carrington latitude and longitude."""
    f = {n: float(k[n]) for n in GEO}
    j, i = np.indices(shape, dtype=float)
    u = (i + 1.0 - f["CRPIX1"]) * f["CDELT1"] / f["RSUN_OBS"]
    w = (j + 1.0 - f["CRPIX2"]) * f["CDELT2"] / f["RSUN_OBS"]
    c, s = math.cos(math.radians(f["CROTA2"])), math.sin(math.radians(f["CROTA2"]))
    x, y = c * u - s * w, s * u + c * w
    rho2 = x * x + y * y
    on = rho2 < DISC
    z = np.where(on, np.sqrt(np.where(on, 1.0 - rho2, 0.0)), np.nan)
    b = math.radians(f["CRLT_OBS"])
    rot = np.array([[1.0, 0.0, 0.0], [0.0, math.cos(b), math.sin(b)], [0.0, -math.sin(b), math.cos(b)]])
    v = np.einsum("ab,bij->aij", rot, np.stack([x, y, z]))        # solar frame: (west, north, towards L0)
    lat = np.degrees(np.arcsin(np.clip(v[1], -1.0, 1.0)))
    lon = np.mod(f["CRLN_OBS"] + np.degrees(np.arctan2(v[0], v[2])), 360.0)
    return lat, lon, z, f


def own_window(geo, lat0, lon0, dlat=6.0, dlon=8.0):
    lat, lon, mu, _ = geo
    return np.isfinite(mu) & (np.abs(lat - lat0) <= dlat) & (np.abs(np.mod(lon - lon0 + 180.0, 360.0) - 180.0) <= dlon)


def own_image(path, k, lat0, lon0, adm, dpd_day):
    q, qs = own_quality(k.get("QUALITY"))
    try:
        [float(k[n]) for n in GEO]
    except (KeyError, TypeError, ValueError):
        return dict(main_status="geometry_keywords_unparsable")
    with fits.open(path) as h:
        d = np.asarray(h[-1].data, dtype=float)
    geo = own_geometry(k, d.shape)
    lat, lon, mu, f = geo
    out = {}
    w = own_window(geo, lat0, lon0)
    for tag, bmin in THR.items():
        if qs != "ok":
            m = dict(status=f"quality_{qs}")
        elif q not in adm:
            m = dict(status="quality_not_zero" if adm == {0} else "quality_not_admissible")
            out[f"{tag}_quality_rejected"] = "0x%08x" % q
        elif not w.any():
            m = dict(status="window_off_disk")
        elif mu[w].min() < 0.8:
            m = dict(status="window_outside_mu_domain", mu_min=float(mu[w].min()))
        else:
            area = abs(f["CDELT1"] * f["CDELT2"]) * (R_CM / f["RSUN_OBS"]) ** 2 / mu[w]
            m = R1.own_measure(lat[w], lon[w], d[w] / mu[w], area, bmin)
            m.pop("sep_lonsteps", None)
        out.update({f"{tag}_{a}": b for a, b in m.items()})
    for side, tag in ((-1, "qm"), (1, "qp")):
        lq = np.mod(lon0 + 30.0 * side, 360.0)
        out[f"{tag}_lon"] = lq
        near = (np.abs(dpd_day.lat.to_numpy() - lat0) <= 12.0) & (np.abs(np.mod(dpd_day.lon.to_numpy() - lq + 180.0, 360.0) - 180.0) <= 16.0)
        wq = own_window(geo, lat0, lq)
        if near.any():
            out[f"{tag}_status"] = "dpd_group_inside"
        elif not wq.any():
            out[f"{tag}_status"] = "window_off_disk"
        elif mu[wq].min() < 0.8:
            out[f"{tag}_status"] = "window_outside_mu_domain"
        else:
            br = d[wq] / mu[wq]
            out[f"{tag}_finite_frac"] = float(np.isfinite(br).sum() / br.size)
            if out[f"{tag}_finite_frac"] < 0.5:
                out[f"{tag}_status"] = "finite_below_50pct"
            else:
                x = br[np.isfinite(br)]
                out[f"{tag}_status"], out[f"{tag}_mad_g"] = "ok", float(1.4826 * np.median(np.abs(x - np.median(x))))
    good = [out[f"{t}_mad_g"] for t in ("qm", "qp") if out[f"{t}_status"] == "ok"]
    out["quiet_mad_g"] = float(np.mean(good)) if good else np.nan
    return out


# ---------------------------------------------------------------- comparison

INT_KEYS = ("npos", "nneg", "n_win", "n_missing_win", "leading_sign")
MEAS_KEYS = ("npos", "nneg", "flux_pos_mx", "flux_neg_mx", "area_pos_msh", "area_neg_msh", "lat_bar", "lon_pos", "lat_pos", "lon_neg",
             "lat_neg", "leading_sign", "tilt_deg", "sep_deg", "n_win", "n_missing_win", "mu_min", "quality_rejected")


def missing(v):
    return v is None or (isinstance(v, float) and math.isnan(v)) or str(v) in ("", "nan", "None")


def own_interval(v):
    """Seconds, or None when missing or not interpretable (never zero)."""
    try:
        x = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def exact_int(theirs, mine):
    try:
        x = float(theirs)
    except (TypeError, ValueError):
        return False
    return math.isfinite(x) and x.is_integer() and int(x) == int(mine)


def value_ok(k, mine, theirs):
    if isinstance(mine, str):
        return str(theirs) == mine
    if missing(theirs):
        return isinstance(mine, float) and math.isnan(mine)
    if k.endswith(INT_KEYS):
        return exact_int(theirs, mine) and (not k.endswith("leading_sign") or int(mine) in (-1, 1))
    try:
        if not math.isfinite(float(theirs)):
            return False
    except (TypeError, ValueError):
        return False
    if k.endswith(("_lon", "lon_pos", "lon_neg")):
        return abs(np.mod(float(mine) - float(theirs) + 180.0, 360.0) - 180.0) <= TOL_ANG
    rel = any(s in k for s in ("flux", "area", "mad_g", "finite_frac"))
    return R1.close(mine, theirs, TOL_REL if rel else TOL_ANG, rel=rel)


BASE = ("rule", "noaa", "day", "image", "choice_status", "pair_status", "T_REC", "status", "file", "sha256", "quality", "interval_s", "dt_h")


def expected_rows(samp, choices, kw, checkpoint, dest, dpd):
    """Own list of (key, expected base fields, own measurement or None). Every base field is set on every row."""
    done = {e["path"]: e for e in checkpoint if e["status"] == "ok"}
    lv2 = samp[samp.level2.astype(str) == "True"]
    pos = {(r.noaa, r.day): (float(r.lat), float(r.lon)) for r in lv2.itertuples()}
    rows, bad_sha = [], []
    for rule in ("A1", "original"):
        ch = choices[rule]
        if [(r.noaa, r.day) for r in ch.itertuples()] != list(pos):
            raise SystemExit(f"{rule} choices do not cover the level-2 groups in order")
        for c in ch.to_dict("records"):
            lat0, lon0 = pos[(c["noaa"], c["day"])]
            for img in ("A", "B"):
                key = (rule, c["noaa"], c["day"], img)
                trec = c.get(img)
                exp = dict(choice_status=c["status"], pair_status=c.get("pair_status"), T_REC=None if missing(trec) else trec,
                           file=None, sha256=None, quality=None, interval_s=None, dt_h=None)
                if c["status"] != "ok":
                    rows.append((key, dict(exp, status=c["status"]), None))
                    continue
                if missing(trec):
                    rows.append((key, dict(exp, status="no_image"), None))
                    continue
                e = done.get(c[f"{img}_path"])
                if e is None:
                    rows.append((key, dict(exp, status="fits_missing"), None))
                    continue
                fp = Path(dest) / e["file"]
                if not fp.exists() or sha(fp) != e["sha256"]:
                    bad_sha.append(e["file"])
                    rows.append((key, dict(exp, status="fits_sha_mismatch"), None))
                    continue
                k = kw[trec]
                m = own_image(fp, k, lat0, lon0, ADM[rule], dpd[dpd.day == c["day"]])
                exp.update(file=e["file"], sha256=e["sha256"], quality=k.get("QUALITY"), status=m["main_status"],
                           interval_s=own_interval(kw[c["A"]].get("INTERVAL")), dt_h=c.get(f"{img}_dt_h"))   # INTERVAL of the pair (A)
                rows.append((key, exp, m))
    return rows, bad_sha


def compare(t, rows, choices):
    """Every exported column of every row; returns the list of (row index, reason) that differ."""
    keys = [(r["rule"], r["noaa"], r["day"], r["image"]) for r in t.to_dict("records")]
    if keys != [k for k, _, _ in rows]:
        return [(-1, "row set or order")]
    produced = set(BASE).union(*[set(m) for _, _, m in rows if m is not None])
    if set(t.columns) != produced:
        return [(-1, f"columns: unexpected {sorted(set(t.columns) - produced)[:4]}, missing {sorted(produced - set(t.columns))[:4]}")]
    a_int = {(rule, c["noaa"], c["day"]): c.get("A_interval") for rule, ch in choices.items() for c in ch.to_dict("records")}
    bad = []
    for i, (r, (key, exp, m)) in enumerate(zip(t.to_dict("records"), rows)):
        for k in BASE[4:]:
            v, x = exp[k], r.get(k)
            if k == "interval_s":
                if m is not None and not R1.close(np.nan if v is None else v, a_int[key[:3]], 0.0):
                    bad.append((i, "interval_s vs plan"))
                good = missing(x) if v is None else R1.close(v, x, 0.0)
            elif k == "dt_h":
                good = missing(x) if missing(v) else R1.close(v, x, 1e-12)
            else:
                good = missing(x) if missing(v) else str(x) == str(v)
            if not good:
                bad.append((i, k))
        for k in t.columns:
            if k in BASE:
                continue
            if m is not None and k in m:
                if not value_ok(k, m[k], r.get(k)):
                    bad.append((i, k))
            elif not missing(r.get(k)):
                bad.append((i, f"value not produced by the recount: {k}"))
    return bad


def own_upstream(meta, l2):
    """Own upstream checks on the real path; [(name, ok, info)], evaluated before any FITS is opened."""
    out = []

    def add(name, f):
        try:
            out.append((name, bool(f()), ""))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            out.append((name, False, type(exc).__name__))

    fr = json.loads((ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json").read_text())
    fz = json.loads(A1_FREEZE.read_text())
    pm, mm, sm = (json.loads((d / "META.json").read_text()) for d in (PLAN, MD, SEL))
    add("protocol and A1 texts equal to their freezes, linked to the run", lambda: sha(ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md") == fr["sha256"]
        == fz["parent_sha256"] == meta["protocol_sha256"] and sha(A1) == fz["sha256"] == meta["a1_sha256"] == pm["a1_sha256"])
    add("selection products and strict selection recount receipt", lambda: set(sm["products_sha256"]) == {"POPULATION.csv", "SAMPLE.csv", "CELLS.csv"}
        and all(sha(SEL / n) == h for n, h in sm["products_sha256"].items()) and meta["selection_meta_sha256"] == sha(SEL / "META.json")
        and RC.strict_receipt(ROOT / "results/MDI_PILOT_SELECTION_RECOUNT/RECEIPT.json", "selection_meta_sha256", SEL / "META.json"))
    add("metadata products and strict metadata recount receipt, linked to A1 and the run",
        lambda: all(sha(MD / n) == h for n, h in mm["products_sha256"].items()) and meta["metadata_meta_sha256"] == sha(MD / "META.json")
        == fz["source_metadata_meta_sha256"] == pm["metadata_meta_sha256"]
        and RC.strict_receipt(ROOT / "results/MDI_PILOT_L2_METADATA_RECOUNT/RECEIPT.json", "metadata_meta_sha256", MD / "META.json"))
    add("plan products and strict plan recount receipt, linked to the run", lambda: all(sha(PLAN / n) == h for n, h in pm["products_sha256"].items())
        and RC.strict_receipt(PLAN_REC / "RECEIPT.json", "plan_meta_sha256", PLAN / "META.json") and meta["plan_meta_sha256"] == sha(PLAN / "META.json"))
    ck_path = STATE / "CHECKPOINT.jsonl"
    ck = [json.loads(x) for x in ck_path.read_text().splitlines() if x.strip()]
    plan = pd.read_csv(PLAN / "PLAN.csv", keep_default_na=False, na_values=[""])
    trec = dict(zip(plan.path, plan.T_REC))
    done = [e for e in ck if e.get("status") == "ok"]
    add("checkpoint: linked to the run and the plan; completed lines with planned path, same T_REC, own file name, one per path",
        lambda: meta["checkpoint_sha256"] == sha(ck_path) and all(e.get("plan_meta_sha256") == sha(PLAN / "META.json") for e in ck)
        and all(e["path"] in trec and e["T_REC"] == trec[e["path"]]
                and e["file"] == "mdi.fd_M_96m_lev182." + e["T_REC"].replace(":", "").replace(".", "") + ".data.fits" for e in done)
        and len({e["path"] for e in done}) == len(done))
    dpd_dir = ROOT / "data/sharp/external_DPD_20261118"
    used = {"SAMPLE.csv": SEL / "SAMPLE.csv", "CHOICES_A1.csv": PLAN / "CHOICES_A1.csv", "CHOICES_ORIGINAL.csv": PLAN / "CHOICES_ORIGINAL.csv",
            "PLAN.csv": PLAN / "PLAN.csv", "ANSWERS.jsonl": MD / "ANSWERS.jsonl", "CHECKPOINT.jsonl": ck_path,
            **{f"gDPD{y}.txt": dpd_dir / f"gDPD{y}.txt" for y in range(1995, 2012)}}
    add("inputs recorded by the run equal to the inputs read here", lambda: meta["inputs_sha256"] == {n: sha(f) for n, f in used.items()})
    return out, ck


def check(l2=L2, rec_dir=REC, write=True, env=None):
    checks = []

    def ok(name, cond, info=""):
        checks.append(dict(name=name, ok=bool(cond), info=str(info)[:300]))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {str(info)[:200]}")

    def finish():
        passed = sum(c["ok"] for c in checks)
        receipt = dict(passed=passed, total=len(checks), partial=not real, checks=checks, l2_meta_sha256=sha(Path(l2) / "META.json"))
        if write:
            if not real:
                sys.exit("a receipt is written only on the real path")
            if Path(rec_dir).exists():
                sys.exit("receipt exists")
            Path(rec_dir).mkdir(parents=True)
            (Path(rec_dir) / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"recount: {passed}/{len(checks)} (partial {not real})")
        return passed == len(checks)

    real = env is None
    meta = json.loads((Path(l2) / "META.json").read_text())
    ps = meta.get("products_sha256", {})
    ok("L2 products: exact set and actual hashes before reading", set(ps) == {"L2_RECORDS.csv"} and all(sha(Path(l2) / n) == h for n, h in ps.items()))
    if real:
        up, ck = own_upstream(meta, l2)
        for name, g, info in up:
            ok(name, g, info)
    if not all(c["ok"] for c in checks):
        print("prerequisites not met: stop before any FITS")
        return finish()
    if real:
        samp = pd.read_csv(SEL / "SAMPLE.csv", dtype={"noaa": str}, float_precision="round_trip")
        rd = lambda n: pd.read_csv(PLAN / n, dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")  # noqa: E731
        choices = {"A1": rd("CHOICES_A1.csv"), "original": rd("CHOICES_ORIGINAL.csv")}
        answers = [json.loads(x) for x in (MD / "ANSWERS.jsonl").read_text().splitlines() if x.strip()]
        S = _mod("selrec", "scripts/mdi_pilot_select_recount.py")
        dpd = S.read_gdpd(years=range(1995, 2012))
        dest = DEST
    else:
        samp, choices, answers, ck, dest, dpd = (env[k] for k in ("samp", "choices", "answers", "checkpoint", "dest", "dpd"))
    kw, conflicts = own_keywords(answers)
    ok("keywords: every T_REC with one set of values across the answers", not conflicts, conflicts[:3])
    t = pd.read_csv(Path(l2) / "L2_RECORDS.csv", dtype={"noaa": str}, keep_default_na=False, na_values=[""], float_precision="round_trip")
    rows, bad_sha = expected_rows(samp, choices, kw, ck, dest, dpd)
    ok("FITS read only with SHA-256 equal to the checkpoint", not bad_sha, bad_sha[:3])
    bad = compare(t, rows, choices)
    ok("every row and every exported column reproduced: keys and order, choice, pair and status, files and SHA, QUALITY, INTERVAL, "
       "Delta t, exact integer counts, fluxes, areas, centroids, tilts, separation, lat_bar, mu_min, quiet windows",
       not bad, f"{len(rows) - len({i for i, _ in bad})}/{len(rows)} first bad {bad[:4]}")
    n_meas = sum(m is not None for _, _, m in rows)
    ok("measured rows: at least one (an empty run is not a recount)", n_meas > 0, n_meas)
    if real:
        ok("number of FITS read recorded by the run", meta.get("n_fits_read") == n_meas, (meta.get("n_fits_read"), n_meas))
    return finish()


# ---------------------------------------------------------------- selftest

def selftest():
    import contextlib
    import io
    import tempfile
    M = _mod("mdi_pilot_measure_l2", "scripts/mdi_pilot_measure_l2.py")      # runner only to produce the synthetic run
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    with tempfile.TemporaryDirectory() as td:
        env = M.synthetic_env(td)
        t = M.build(env["samp"], env["choices"], env["answers"], env["checkpoint"], env["dest"], env["dpd"])
        kw, _ = own_keywords(env["answers"])
        g = own_geometry(kw[env["checkpoint"][3]["T_REC"]], (1024, 1024))
        ga = M.AD.geometry(kw[env["checkpoint"][3]["T_REC"]], (1024, 1024))
        fin = np.isfinite(ga[2])
        ok("own geometry equal to the adapter's (CROTA2 = 180 image): disc, lat, lon, mu",
           (np.isfinite(g[2]) == fin).all() and np.allclose(g[0][fin], ga[0][fin], atol=1e-9)
           and np.allclose(np.mod(g[1][fin] - ga[1][fin] + 180, 360) - 180, 0, atol=1e-9) and np.allclose(g[2][fin], ga[2][fin], atol=1e-12))

        def run(tab, name, expect, ck=None):
            d = Path(td) / name.replace(" ", "_")
            d.mkdir()
            tab.to_csv(d / "L2_RECORDS.csv", index=False)
            (d / "META.json").write_text(json.dumps(dict(products_sha256={"L2_RECORDS.csv": sha(d / "L2_RECORDS.csv")})))
            e = dict(env, checkpoint=ck) if ck is not None else env
            with contextlib.redirect_stdout(io.StringIO()):
                got = check(d, write=False, env=e)
            res.append(got == expect)
            print(f"[{'OK' if got == expect else 'FALLITO'}] {'accepted' if expect else 'refused with updated hashes'}: {name}")

        run(t, "synthetic run", True)
        i_ok = t.index[(t.rule == "A1") & (t.status == "ok")][0]
        run(t.assign(main_tilt_deg=t.main_tilt_deg.where(t.index != i_ok, t.main_tilt_deg + 1e-4)), "a tilt moved by 1e-4 deg", False)
        run(t.assign(sens100_npos=t.sens100_npos.where(t.index != i_ok, t.sens100_npos + 1)), "a pixel count at 100 G", False)
        run(t.assign(main_flux_neg_mx=t.main_flux_neg_mx.where(t.index != i_ok, t.main_flux_neg_mx * (1 + 1e-7))), "a flux", False)
        run(t.assign(qm_status=t.qm_status.where(t.index != i_ok, "dpd_group_inside")), "a quiet status", False)
        run(t.assign(quiet_mad_g=t.quiet_mad_g.where(t.index != i_ok, 1.0)), "a quiet dispersion", False)
        i_o = t.index[(t.rule == "original") & (t.image == "A") & (t.noaa == "9001")][0]
        run(t.assign(status=t.status.where(t.index != i_o, "ok")), "a QUALITY rejection turned into ok", False)
        run(t.assign(quality=t.quality.where(t.index != i_ok, "0x00000000")), "a QUALITY value", False)
        run(t.assign(interval_s=t.interval_s.where(t.index != i_ok, 30.0)), "an INTERVAL", False)
        run(t.drop(index=len(t) - 1), "a row dropped", False)
        run(pd.concat([t.iloc[[1]], t.drop(index=1)]), "two rows swapped", False)
        i_m = t.index[(t.rule == "original") & (t.noaa == "9002")][0]
        run(t.assign(main_tilt_deg=t.main_tilt_deg.where(t.index != i_m, 10.0)), "a value on a row without measurement", False)
        ck3 = [e for e in env["checkpoint"] if e["path"] != "/SUM/9002/B"]
        t3 = M.build(env["samp"], env["choices"], env["answers"], ck3, env["dest"], env["dpd"])
        run(t3, "run with a file not completed (fits_missing) against its checkpoint", True, ck=ck3)
        run(t3, "fits_missing although the checkpoint has the file", False)
        run(t.assign(pair_status=t.pair_status.where(t.index != 0, "invented_pair")), "a pair_status invented", False)
        run(t.assign(main_npos=t.main_npos.where(t.index != i_ok, t.main_npos + 0.4)), "a fractional pixel count (+0.4)", False)
        run(t.assign(main_leading_sign=t.main_leading_sign.where(t.index != i_ok, t.main_leading_sign * 2)), "a leading sign outside +-1", False)
        run(t.assign(extra_col=1.0), "an exported column the recount does not produce", False)
        run(t.assign(sha256=t.sha256.where(t.index != i_m, "a" * 64)), "a SHA on a row without measurement", False)
        # unknown INTERVAL: A valid, B absent, full path runner -> CSV -> recount
        e5 = dict(env, choices={r: c.copy() for r, c in env["choices"].items()},
                  answers=json.loads(json.dumps(env["answers"])))
        for r in ("A1", "original"):
            c = e5["choices"][r]
            j = c.index[c.noaa == "9002"][0]
            c.loc[j, ["A_interval", "B", "B_path", "B_dt_h"]] = [np.nan, None, None, np.nan]
            c.loc[j, "pair_status"] = "no_pair"
        kwd = {k["name"]: k for k in e5["answers"][0]["doc"]["keywords"]}
        kwd["INTERVAL"]["values"][kwd["T_REC"]["values"].index(e5["choices"]["A1"].A.iloc[1])] = "MISSING"
        t5 = M.build(e5["samp"], e5["choices"], e5["answers"], e5["checkpoint"], e5["dest"], e5["dpd"])
        row = t5[(t5.rule == "A1") & (t5.noaa == "9002")]
        ok("unknown INTERVAL: runner measures A, B is 'no_image', interval_s missing (never zero)",
           list(row.status) == ["ok", "no_image"] and row.interval_s.isna().all(), list(row.status))
        env, saved_env = e5, env
        run(t5, "unknown INTERVAL with A valid and B absent", True)
        j5 = t5.index[(t5.rule == "A1") & (t5.noaa == "9002") & (t5.image == "A")][0]
        run(t5.assign(interval_s=t5.interval_s.where(t5.index != j5, 0.0)), "unknown INTERVAL written as zero", False)
        env = saved_env
        # invalid L2 product hash: stop before any FITS reconstruction
        d = Path(td) / "bad_product"
        d.mkdir()
        t.to_csv(d / "L2_RECORDS.csv", index=False)
        (d / "META.json").write_text(json.dumps(dict(products_sha256={"L2_RECORDS.csv": "0" * 64})))
        g, called = globals(), []
        real_er = g["expected_rows"]
        g["expected_rows"] = lambda *a, **k: called.append(1)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                refused = not check(d, write=False, env=env)
        finally:
            g["expected_rows"] = real_er
        ok("invalid L2 product hash: refused and stopped before reading any FITS", refused and not called)
        ck4 = [dict(e) for e in env["checkpoint"]]
        ck4[0]["sha256"] = "f" * 64
        run(t, "FITS whose SHA differs from the checkpoint", False, ck=ck4)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else (0 if check() else 1))
