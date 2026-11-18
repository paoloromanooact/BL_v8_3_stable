"""Independent recount of the MDI-HMI small comparison (frozen protocol 6d6fd12, §4-§5).

Written by Claude without using Codex's kernels (scripts/mdi_overlap_kernels.py) or downloader: own LOS geometry,
masks, domain check, measures, differences and summaries. Shared definitions only: P1 geometry (WCS, tilt and centroid
conventions of python/sharpbl/geometry.py) and, for R0, the frozen P1 function measure_v84. Keywords (WCS, observer)
come from the saved geometry responses, so FITS headers are not needed; arrays are read from the FITS files.

    .venv/bin/python scripts/mdi_hmi_comparison_recount.py --selftest
    .venv/bin/python scripts/mdi_hmi_comparison_recount.py --maps DIR --out results/...   # after the download

Files are found under DIR by the JSOC default name <series>.<id>.<YYYYMMDD_HHMMSS>_TAI.<segment>.fits, or listed in
--files CSV (path, series, record, segment). Nothing is downloaded here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import geometry as geo, measure as P1  # noqa: E402

SEL = ROOT / "data/sharp/metadata_inventory_mdi/small_comparison_6d6fd12/selection/PAIRS.csv"
PROTOCOL_LABEL = {str(SEL): "6d6fd12",
                  str(ROOT / "data/sharp/metadata_inventory_mdi/second_sample_bbd719c/selection/PAIRS.csv"): "bbd719c"}
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
MU_MIN, THR, BMAX, FLAG_DEG = 0.8, 100.0, 10000.0, 2.107
HMI, MDI = "hmi.sharp_cea_720s", "mdi.smarp_cea_96m"
STRATA = ("N_central", "S_central", "N_lateral", "S_lateral")


# ---------------------------------------------------------------- geometry (own implementation)

def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def los_geometry(lon, lat, kw):
    """mu = e_r . u and the LOS projections of e_theta (south) and e_phi (west), finite observer."""
    R, Dist = float(kw["RSUN_REF"]), float(kw["DSUN_OBS"])
    o = unit(float(kw["CRLN_OBS"]), float(kw["CRLT_OBS"]))
    er = unit(lon, lat)
    u = Dist * o - R * er
    u /= np.linalg.norm(u, axis=-1, keepdims=True)
    lo, la = np.radians(lon), np.radians(lat)
    e_south = np.stack([np.sin(la) * np.cos(lo), np.sin(la) * np.sin(lo), -np.cos(la)], axis=-1)
    e_west = np.stack([-np.sin(lo), np.cos(lo), np.zeros_like(lo)], axis=-1)
    return (er * u).sum(-1), (e_south * u).sum(-1), (e_west * u).sum(-1)


def wcs_header(kw):
    return dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="deg", CUNIT2="deg",
                **{k: float(kw[k]) for k in ("CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CDELT1", "CDELT2")})


# ---------------------------------------------------------------- measures (own implementation, P1 conventions)

def centroid(lon, lat, w):
    v = (unit(lon, lat) * w[:, None]).sum(0)
    return math.degrees(math.atan2(v[1], v[0])), math.degrees(math.asin(np.clip(v[2] / np.linalg.norm(v), -1, 1)))


def measure(B, mask, lon, lat, mu, area_cm2, R_cm):
    """Strict branch measure: every mask pixel must be finite and inside mu >= 0.8, else unavailable."""
    if not mask.any():
        return dict(status="empty_mask")
    bad_dom = mask & ~(mu >= MU_MIN)
    bad_fin = mask & ~np.isfinite(B)
    if bad_dom.any() or bad_fin.any():
        return dict(status="unavailable", n_mu_out=int(bad_dom.sum()), n_nonfinite=int(bad_fin.sum()),
                    mu_min_mask=float(np.nanmin(np.where(mask, mu, np.nan))))
    elig = mask & (np.abs(B) <= BMAX)
    pos, neg = elig & (B >= THR), elig & (B <= -THR)
    strong = pos | neg
    out = dict(status="ok", n_mask=int(mask.sum()), npos=int(pos.sum()), nneg=int(neg.sum()),
               n_over_max=int((mask & ~elig).sum()), mu_min_mask=float(mu[mask].min()))
    pp, pn = float(B[pos].sum() * area_cm2), float(-B[neg].sum() * area_cm2)
    out.update(phi_pos=pp, phi_neg=pn, phi=pp + pn)
    k = 3.0 / (4.0 * math.pi * R_cm ** 2)
    if strong.any():
        out["D"] = float(k * (B[strong] * np.sin(np.radians(lat[strong])) * area_cm2).sum())
        out["lon_mean"], out["lat_mean"] = centroid(lon[strong], lat[strong], np.abs(B[strong]))
    if not (pos.any() and neg.any()):
        out["status"] = "no_two_polarities"
        return out
    cp = centroid(lon[pos], lat[pos], B[pos])
    cn = centroid(lon[neg], lat[neg], -B[neg])
    out.update(lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1])
    t_np = geo.tilt_deg(cn, cp)
    lead, follow = (cp, cn) if abs(t_np) < 90 else (cn, cp)
    out["leading_sign"] = 1 if abs(t_np) < 90 else -1
    out["tilt"] = geo.tilt_deg(lead, follow)
    out["d_deg"] = geo.great_circle_deg(*cp, *cn)
    msp = float((B[pos] * np.sin(np.radians(lat[pos]))).sum() / B[pos].sum())
    msn = float((B[neg] * np.sin(np.radians(lat[neg]))).sum() / B[neg].sum())
    out["D_bal"] = k * 0.5 * (pp + pn) * (msp - msn)
    if not all(np.isfinite([out["tilt"], out["d_deg"], out["D_bal"]])):
        out["status"] = "degenerate"
    return out


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def differences(ref, cand):
    if ref.get("status") != "ok" or cand.get("status") != "ok":
        return dict(diff_status="not_comparable")
    d = cand["tilt"] - ref["tilt"]
    d_ax = (d + 90.0) % 180.0 - 90.0
    lam = ref["lat_mean"]
    out = dict(diff_status="ok", d=d, d_ax=d_ax, abs_d_ax=abs(d_ax), lambda_ref=lam,
               d_gamma=(math.copysign(1.0, lam) * d_ax if lam != 0 else float("nan")),
               leading_ref=ref["leading_sign"], leading_cand=cand["leading_sign"])
    for q in ("phi", "phi_pos", "phi_neg", "D", "D_bal", "lat_pos", "lat_neg", "lat_mean"):
        out[f"delta_{q}"] = cand[q] - ref[q]
    for q in ("lon_pos", "lon_neg", "lon_mean"):
        out[f"delta_{q}"] = wrap180(cand[q] - ref[q])
    out["ratio_phi"] = cand["phi"] / ref["phi"] if ref["phi"] != 0 else float("nan")
    return out


def summary(values):
    v = np.array([x for x in values if np.isfinite(x)], float)
    n = len(v)
    if n == 0:
        return dict(n=0)
    out = dict(n=n, median=float(np.median(v)), min=float(v.min()), max=float(v.max()), mean=float(v.mean()))
    out["s_over_sqrt_n"] = float(v.std(ddof=1) / math.sqrt(n)) if n >= 2 else float("nan")
    return out


def summarise(rows):
    """Protocol §5: d_gamma, d, d_ax summaries overall, per hemisphere and stratum; flag on B."""
    out = []
    for comp in ("A1", "A2", "B"):
        R = [r for r in rows if r["comparison"] == comp]
        groups = [("all", R)] + [(h, [r for r in R if r["stratum"].startswith(h)]) for h in ("N", "S")] \
            + [(s, [r for r in R if r["stratum"] == s]) for s in STRATA]
        for gname, G in groups:
            ok = [r for r in G if r.get("diff_status") == "ok"]
            row = dict(comparison=comp, group=gname, n_selected=len(G), n_evaluable=len(ok))
            for q in ("d_gamma", "d", "d_ax"):
                row.update({f"{q}_{k}": v for k, v in summary([r[q] for r in ok]).items()})
            row["abs_d_ax_median"] = float(np.median([r["abs_d_ax"] for r in ok])) if ok else float("nan")
            if comp == "B" and gname in ("all", "N", "S"):
                med = row.get("d_gamma_median", float("nan"))
                row["flag_2107"] = int(np.isfinite(med) and abs(med) >= FLAG_DEG)
            out.append(row)
    return out


# ---------------------------------------------------------------- I/O

def read_map(path):
    data, _ = geo.read_sharp(path)
    return data


def locate(root, series, rid, trec, seg, listing):
    if listing is not None:
        return listing.get((series, f"{rid}|{trec}", seg))
    stamp = trec.replace(".", "").replace(":", "").replace("_TAI", "")[:15]
    hits = list(Path(root).rglob(f"{series}.{rid}.{stamp}_TAI.{seg}.fits"))
    return hits[0] if len(hits) == 1 else None


def branch_maps(kw, shape):
    lon, lat = geo.lonlat_maps(wcs_header(kw), shape)
    mu, cs, cw = los_geometry(lon, lat, kw)
    area = float(kw["RSUN_REF"]) ** 2 * 1e4 * math.radians(abs(float(kw["CDELT1"]))) * math.radians(abs(float(kw["CDELT2"])))
    return lon, lat, mu, cs, cw, area, float(kw["RSUN_REF"]) * 100.0


def run(maps, out, files_csv=None, pairs=SEL):
    import mdi_hmi_footprint_mu as fm
    import pandas as pd
    out = Path(out)
    if out.exists():
        sys.exit("refusing to overwrite the recount")
    table, conflict, _, _ = fm.load_geometry()
    listing = None
    if files_csv:
        listing = {(r["series"], r["record"], r["segment"]): Path(r["path"]) for r in csv.DictReader(open(files_csv))}
    cat = pd.read_csv(CATALOGUE, low_memory=False)
    rows, r0, missing = [], [], []
    for p in csv.DictReader(open(pairs)):
        st = p["stratum"]
        recs = {}
        for series, rec in ((HMI, p["hmi_record"]), (MDI, p["smarp_record"])):
            rid, trec = rec.split("|")
            kw = table[(series, rid, fm.normtime(trec))]
            segs = ("bitmap", "magnetogram") + (("Br", "Bt", "Bp") if series == HMI else ())
            arr = {}
            for s in segs:
                f = locate(maps, series, rid, trec, s, listing)
                if f is None:
                    missing.append((series, rec, s))
                    continue
                arr[s] = read_map(f)
            nx, ny = (int(v) for v in kw["dims"].split("x"))
            if any(a.shape != (ny, nx) for a in arr.values()):
                sys.exit(f"shape differs from certificate dims for {series} {rec}")
            recs[series] = (rid, trec, kw, arr)
        hrid, htrec, hkw, h = recs[HMI]
        mrid, mtrec, mkw, m = recs[MDI]
        res = {}
        if {"bitmap", "Br"} <= set(h):
            lon, lat, mu, cs, cw, area, Rcm = branch_maps(hkw, h["bitmap"].shape)
            hmask_A = np.isin(h["bitmap"], (33, 34))
            res["Br"] = measure(h["Br"], hmask_A, lon, lat, mu, area, Rcm)
            hdr = dict(wcs_header(hkw), T_REC=htrec, RSUN_REF=float(hkw["RSUN_REF"]), CRLN_OBS=float(hkw["CRLN_OBS"]))
            v = P1.measure_v84(h["Br"], h["bitmap"], hdr)
            hist = cat[(cat.HARPNUM == int(hrid)) & (cat.T_REC == htrec)]
            r0row = dict(HARPNUM=hrid, T_REC=htrec, p1_phi=v["phi_mx"], p1_tilt=v["tilt_deg"], p1_dbal=v["d_axial_bal_g"],
                         own_minus_p1_phi=(res["Br"].get("phi", np.nan) - v["phi_mx"]),
                         historical=int(len(hist) == 1))
            if len(hist) == 1:
                hr = hist.iloc[0]
                r0row.update(hist_phi=hr["phi_mx"], hist_tilt=hr["tilt_deg"], hist_dbal=hr["d_axial_bal_g"],
                             rel_phi=abs(v["phi_mx"] / hr["phi_mx"] - 1), abs_tilt=abs(v["tilt_deg"] - hr["tilt_deg"]))
            r0.append(r0row)
            if {"Bt", "Bp"} <= set(h):
                los = h["Br"] * mu + h["Bt"] * cs + h["Bp"] * cw
                with np.errstate(divide="ignore", invalid="ignore"):
                    res["A1"] = measure(los / mu, hmask_A, lon, lat, mu, area, Rcm)
            if "magnetogram" in h:
                with np.errstate(divide="ignore", invalid="ignore"):
                    res["A2"] = measure(h["magnetogram"] / mu, hmask_A, lon, lat, mu, area, Rcm)
                    res["HMI_LOS"] = measure(h["magnetogram"] / mu, (h["bitmap"].astype(np.int64) & 32) != 0,
                                             lon, lat, mu, area, Rcm)
        if {"bitmap", "magnetogram"} <= set(m):
            lon, lat, mu, cs, cw, area, Rcm = branch_maps(mkw, m["bitmap"].shape)
            with np.errstate(divide="ignore", invalid="ignore"):
                res["MDI_LOS"] = measure(m["magnetogram"] / mu, (m["bitmap"].astype(np.int64) & 32) != 0,
                                         lon, lat, mu, area, Rcm)
        for comp, ref, cand in (("A1", "Br", "A1"), ("A2", "Br", "A2"), ("B", "HMI_LOS", "MDI_LOS")):
            a, b = res.get(ref, dict(status="missing_map")), res.get(cand, dict(status="missing_map"))
            rows.append(dict(comparison=comp, stratum=st, TARPNUM=p["TARPNUM"], HARPNUM=p["HARPNUM"],
                             ref_status=a["status"], cand_status=b["status"],
                             **{f"ref_{k}": v for k, v in a.items() if k != "status"},
                             **{f"cand_{k}": v for k, v in b.items() if k != "status"}, **differences(a, b)))
    summ = summarise(rows)
    out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(out / "PAIR_ROWS.csv", index=False)
    pd.DataFrame(summ).to_csv(out / "SUMMARY.csv", index=False)
    pd.DataFrame(r0).to_csv(out / "R0.csv", index=False)
    (out / "META.json").write_text(json.dumps(dict(missing_files=missing, protocol=PROTOCOL_LABEL.get(str(pairs), "6d6fd12"),
                                                   pairs_sha256=hashlib.sha256(Path(pairs).read_bytes()).hexdigest(),
                                                   note="independent recount"),
                                              indent=2, default=str))
    print(json.dumps(dict(missing=len(missing), rows=len(rows)), indent=1))
    return 0


# ---------------------------------------------------------------- selftest

def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    kw = dict(RSUN_REF=6.96e8, DSUN_OBS=1.5e11, CRLN_OBS=100.0, CRLT_OBS=5.0)
    lon = np.array([[100.0, 120.0], [90.0, 100.0]])
    lat = np.array([[0.0, 10.0], [-15.0, 20.0]])
    mu, cs, cw = los_geometry(lon, lat, kw)
    ok("unit LOS vector: mu^2 + cs^2 + cw^2 = 1", np.allclose(mu ** 2 + cs ** 2 + cw ** 2, 1, atol=1e-14))
    Br = np.array([[300.0, -200.0], [150.0, -500.0]])
    los = Br * mu
    ok("radial field: LOS/mu returns Br", np.allclose(los / mu, Br, rtol=1e-14))
    ok("west field at a western pixel points away from the observer", cw[0, 1] < 0)
    ok("south field seen from a northern observer (B0 = +5) points away", cs[0, 0] < 0)
    r = 6.96e8 / 1.5e11
    l, b, B0 = math.radians(20), 0.0, math.radians(5)
    q = math.sin(b) * math.sin(B0) + math.cos(b) * math.cos(B0) * math.cos(l)
    mu1 = los_geometry(np.array([120.0]), np.array([0.0]), kw)[0][0]
    ok("finite-observer mu = closed form of the protocol", abs(mu1 - (q - r) / math.sqrt(1 + r * r - 2 * r * q)) < 1e-12)
    ok("axial wrap: d = 170 -> d_ax = -10", abs(((170 + 90) % 180) - 90 + 10) < 1e-12)
    refN = dict(status="ok", tilt=10.0, lat_mean=15.0, leading_sign=1, **{k: 1.0 for k in
               ("phi", "phi_pos", "phi_neg", "D", "D_bal", "lat_pos", "lat_neg", "lon_pos", "lon_neg", "lon_mean")})
    candN = dict(refN, tilt=6.0)
    refS, candS = dict(refN, tilt=-10.0, lat_mean=-15.0), dict(refN, tilt=-6.0, lat_mean=-15.0)
    dN, dS = differences(refN, candN), differences(refS, candS)
    ok("Joy shrink gives the same sign of d_gamma in both hemispheres", dN["d_gamma"] == -4.0 and dS["d_gamma"] == -4.0,
       (dN["d_ax"], dS["d_ax"]))
    s0, s1 = summary([]), summary([2.0])
    ok("summaries: n = 0 empty, n = 1 without s/sqrt(n)", s0 == dict(n=0) and s1["n"] == 1 and math.isnan(s1["s_over_sqrt_n"]))
    rows = [dict(comparison="B", stratum=s, diff_status="ok", d_gamma=g, d=g, d_ax=g, abs_d_ax=abs(g))
            for s, g in (("N_central", 3.0), ("N_lateral", 2.5), ("S_central", -0.5), ("S_lateral", 0.1))]
    sm = {(x["comparison"], x["group"]): x for x in summarise(rows)}
    ok("flag on |median d_gamma| >= 2.107 per hemisphere", sm[("B", "N")]["flag_2107"] == 1 and sm[("B", "S")]["flag_2107"] == 0
       and sm[("B", "all")]["flag_2107"] == 0)
    # domain and finiteness make the branch unavailable, no silent trimming
    m = np.ones((2, 2), bool)
    lon2, lat2 = np.array([[100.0, 101.0], [100.0, 101.0]]), np.array([[0.0, 0.0], [1.0, 1.0]])
    mu2 = los_geometry(lon2, lat2, kw)[0]
    ok("mu below 0.8 on one mask pixel -> unavailable",
       measure(Br, m, lon2, lat2, np.where([[True, False], [True, True]], mu2, 0.5), 1.0, 7e10)["status"] == "unavailable")
    ok("NaN on one mask pixel -> unavailable",
       measure(np.where(m, Br, Br) * np.array([[1, np.nan], [1, 1]]), m, lon2, lat2, mu2, 1.0, 7e10)["status"] == "unavailable")
    # own Br measure equals frozen P1 on the local HMI test maps (no NaN in the mask)
    import glob
    worst, n = 0.0, 0
    for fb in sorted(glob.glob(str(ROOT / "data/sharp/test_20240508/*.Br.fits")))[:6]:
        br, hdr = geo.read_sharp(fb)
        bm, _ = geo.read_sharp(fb.replace(".Br.", ".bitmap."))
        mask = np.isin(bm, (33, 34))
        if not np.isfinite(br[mask]).all():
            continue
        lon_, lat_ = geo.lonlat_maps(hdr, br.shape)
        own = measure(br, mask, lon_, lat_, np.ones_like(br), geo.pixel_area_cm2(hdr), geo.rsun_cm(hdr))
        v = P1.measure_v84(br, bm, hdr)
        if own["status"] != "ok":
            continue
        n += 1
        for a, b in (("phi", "phi_mx"), ("tilt", "tilt_deg"), ("D", "d_axial_g"), ("D_bal", "d_axial_bal_g"),
                     ("lat_mean", "lat_mean_deg")):
            worst = max(worst, abs(own[a] - v[b]) / max(abs(v[b]), 1e-30))
    ok("own Br measure = frozen P1 measure_v84 on local HMI maps (mu check disabled)", n >= 3 and worst < 1e-9,
       f"{n} maps, max rel {worst:.1e}")
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--maps", type=Path)
    ap.add_argument("--files", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--pairs", type=Path, default=SEL)
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.out and (a.maps or a.files):
        if not selftest():
            return 1
        return run(a.maps, a.out, a.files, a.pairs)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
