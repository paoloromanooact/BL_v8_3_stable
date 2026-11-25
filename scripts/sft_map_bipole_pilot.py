"""SFT map-bipole pilot (point 2), runner of the frozen protocol docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md (rev. 4).

Receipt docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_FREEZE.json (protocol SHA 380b7982...). Core numerics: python/sharpbl/sft_core.py.
Not run on observed maps before the Codex code review; --selftest uses a synthetic catalogue and synthetic CEA patches.

Steps (protocol section in brackets)
1. Gate: protocol text and receipt pinned, inputs of the receipt unchanged, clean tree, script equal to HEAD, new output dir.
2. Population and draw [§3]: primary records (role primary/both), valid_bl = 1, family_rank = 0; strata "un NOAA"
   (NOAA_NUM = 1) / "altro/ignoto" (flag NOAA_NUM = 0) x USFLUX terciles (numpy linear quantiles; 1 if x <= q1, 2 if
   q1 < x <= q2, 3 otherwise; records without finite USFLUX counted and left out) x |LAT_FWT| bands (<10, 10-20, >=20);
   canonical order HARPNUM, permutation default_rng(36_100_000) of the whole population, first 4 per cell; pi = n/N,
   weights N/n.
3. Map M [§4]: P1 mask (finite, |Br| <= 10000 G, bitmap >= 33, |Br| >= 100 G); polarities rescaled to phibar; linear
   deposit in s; out of the centre support -> status deposition_out_of_range. 300 G sensitivity: everything recomputed
   from the 300 G mask for M and for the point bipole.
4. Bipole B [§5]: point bipole at the P1-style centroids (|Br|-weighted unit-vector means, renormalised) with +-phibar;
   Gaussian sensitivities (area-equivalent sigma, 2 deg, 4 deg) with effective fluxes and centroids recorded.
5. Transport [§6]: SFT1D (N 400, hybrid advection, positivity-limited Crank-Nicolson), the four parameter sets of the
   2x2 grid (reference eta 466.8, Du 0.025, p 2.33); tau = 5 and 10 years as exp(-t/tau) factors on the reference.
6. Times [§7]: 0, 27 days, 0.5, 1, 3 Julian years; daily curves for the reference transport (M and point B, 100 G).
7. Products [§8]: SAMPLE.csv, REGIONS.csv, DIPOLES.csv (long), CURVES.csv.gz, SUMMARY.csv, CONVERGENCE.csv, META.json.
   Summaries weighted with N/n (lower weighted quantile: first sorted value whose cumulative normalised weight reaches q)
   and unweighted; ratio threshold 0.1 m(t), m(t) = weighted median of |D_M(t)| for M at 100 G with the reference
   transport, the same for every variant; if m(t) = 0 no ratio.
8. Convergence on the first 3 successful sampled regions (permutation order): N 800 and halved step against the
   reference, recorded with the criterion 1e-3 max(|D_fine|, 1e-6 D_scale) (a check of the fixed rule, no tuning).

    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_map_bipole_pilot.py --selftest
    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_map_bipole_pilot.py --run        # only after the code review
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo, measure, sft_core as C  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_FREEZE.json"
PIN = dict(protocol="380b79829fbac870479acc02797ef245623b689c09af9ff9f595ac5a81b61d38")
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
FITS = ROOT / "data/sharp/fits"
OUT = ROOT / "results/SFT_MAP_BIPOLE_PILOT"
SEED, PER_CELL = 36_100_000, 4
TIMES = (("0", 0.0), ("27d", 27 * C.DAY), ("0.5y", 0.5 * C.YEAR), ("1y", C.YEAR), ("3y", 3 * C.YEAR))
TAUS = ((5.0, "ref_tau5y"), (10.0, "ref_tau10y"))
TRANSPORTS = {f"eta{p['eta_km2s']:g}_du{p['du_kms']:g}": p for p in C.SENSITIVITY}
REF = f"eta{C.REFERENCE['eta_km2s']:g}_du{C.REFERENCE['du_kms']:g}"
THRESHOLDS = (100.0, 300.0)
CAT_COLS = ["HARPNUM", "T_REC", "role", "valid_bl", "family_rank", "NOAA_NUM", "USFLUX", "LAT_FWT", "d_axial_g", "d_axial_bal_g",
            "d_cm", "tilt_deg", "phi_pos_mx", "phi_neg_mx"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- gate

def gate():
    probs = []
    fz = json.loads(FREEZE.read_text())
    if not (sha(PROTOCOL) == fz.get("sha256") == PIN["protocol"]):
        probs.append("protocol text and receipt")
    if any(sha(ROOT / p) != h for p, h in fz.get("inputs_sha256", {}).items()):
        probs.append("inputs of the freeze receipt changed")
    if subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, capture_output=True, text=True).stdout.strip():
        probs.append("tracked tree not clean")
    head = subprocess.run(["git", "show", f"HEAD:scripts/{Path(__file__).name}"], cwd=ROOT, capture_output=True)
    if head.returncode != 0 or hashlib.sha256(head.stdout).hexdigest() != sha(__file__):
        probs.append("script differs from HEAD")
    if OUT.exists():
        probs.append("output directory exists (single run)")
    return probs


# ---------------------------------------------------------------- population and draw (§3)

def population(cat):
    p = cat[cat.role.isin(["primary", "both"]) & (cat.valid_bl == 1) & (cat.family_rank == 0)].copy()
    n_nan = int((~np.isfinite(p.USFLUX.astype(float))).sum())
    p = p[np.isfinite(p.USFLUX.astype(float))].sort_values("HARPNUM").reset_index(drop=True)
    q1, q2 = np.quantile(p.USFLUX.astype(float), [1 / 3, 2 / 3])
    u = p.USFLUX.astype(float)
    p["flux_class"] = np.where(u <= q1, 1, np.where(u <= q2, 2, 3))
    a = p.LAT_FWT.astype(float).abs()
    p["lat_band"] = np.where(a < 10, "<10", np.where(a < 20, "10-20", ">=20"))
    p["multiplicity"] = np.where(p.NOAA_NUM == 1, "un NOAA", "altro/ignoto")
    p["noaa_absent"] = p.NOAA_NUM == 0
    return p, dict(usflux_missing=n_nan, q1=float(q1), q2=float(q2))


def draw(pop, seed=SEED, per_cell=PER_CELL):
    perm = np.random.default_rng(seed).permutation(len(pop))
    pop = pop.assign(perm_rank=np.argsort(perm))                        # position of each row in the permutation
    keys = ["multiplicity", "flux_class", "lat_band"]
    N = pop.groupby(keys).size().rename("N_cell")
    s = pop.sort_values("perm_rank").groupby(keys, group_keys=False).head(per_cell)
    n = s.groupby(keys).size().rename("n_cell")
    s = s.merge(N, on=keys).merge(n, on=keys)
    s["pi"] = s.n_cell / s.N_cell
    s["weight"] = s.N_cell / s.n_cell
    return s.sort_values("perm_rank").reset_index(drop=True)


# ---------------------------------------------------------------- map ingredients (§4, §5)

def ingredients(br, bitmap, header, threshold):
    """P1-style selection at the threshold, fluxes, centroids, balanced pixel fluxes and their s."""
    m = measure.base_mask(br, bitmap, 33, measure.MAX_ABS_BR_G)
    area = geo.pixel_area_cm2(header)
    r = geo.rsun_cm(header)
    lon, lat = geo.lonlat_maps(header, br.shape)
    strong = m & (np.abs(br) >= threshold) & np.isfinite(lon) & np.isfinite(lat)
    pos, neg = strong & (br > 0), strong & (br < 0)
    out = dict(r_cm=r, n_pos=int(pos.sum()), n_neg=int(neg.sum()))
    if not (pos.any() and neg.any()):
        return dict(out, status="no_two_polarities")
    php, phn = float(br[pos].sum() * area), float(-br[neg].sum() * area)
    phibar = 0.5 * (php + phn)
    lp = geo.weighted_centroid(lon[pos], lat[pos], br[pos])
    ln = geo.weighted_centroid(lon[neg], lat[neg], -br[neg])
    k = 3.0 / (4.0 * np.pi * r * r)
    sl = np.sin(np.radians(lat))
    Fb = np.where(pos, br * area * phibar / php, np.where(neg, br * area * phibar / phn, 0.0))
    return dict(out, status="ok", phi_pos=php, phi_neg=phn, phibar=phibar, imbalance=(php - phn) / (php + phn),
                lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1],
                area_pos=float(pos.sum() * area), area_neg=float(neg.sum() * area),
                D_pix_raw=float(k * (br[strong] * area * sl[strong]).sum()), D_pix_bal=float(k * (Fb[strong] * sl[strong]).sum()),
                D_scale=3.0 * phibar / (4.0 * np.pi * r * r), s_pix=sl[strong], F_bal=Fb[strong])


def representations(ing, threshold, model):
    """Initial cell fluxes per representation: dict name -> (cell flux or None, status, extra fields)."""
    reps = {}
    cf, nout = C.deposit_linear(ing["s_pix"], ing["F_bal"], model.s)
    reps["M"] = (cf, "ok" if cf is not None else "deposition_out_of_range", dict(n_out=nout))
    sp, fp = C.point_bipole(ing["lat_pos"], ing["lat_neg"], ing["phibar"])
    cf, nout = C.deposit_linear(sp, fp, model.s)
    reps["B_point"] = (cf, "ok" if cf is not None else "deposition_out_of_range", dict(n_out=nout))
    if threshold == THRESHOLDS[0]:
        r = ing["r_cm"]
        sig_area = (math.degrees(math.sqrt(ing["area_pos"] / (2 * math.pi * r * r))), math.degrees(math.sqrt(ing["area_neg"] / (2 * math.pi * r * r))))
        for name, (sp_, sn_) in (("B_gauss_area", sig_area), ("B_gauss_2deg", (2.0, 2.0)), ("B_gauss_4deg", (4.0, 4.0))):
            g = C.gaussian_bipole((ing["lon_pos"], ing["lat_pos"]), (ing["lon_neg"], ing["lat_neg"]), sp_, sn_, ing["phibar"], r_cm=r)
            cf, nout = C.deposit_linear(np.sin(np.radians(g["lat"])), g["br"] * g["area"], model.s)
            e = g["effective"]
            reps[name] = (cf, "ok" if cf is not None else "deposition_out_of_range",
                          dict(n_out=nout, sigma_pos=sp_, sigma_neg=sn_, eff_phi_pos=e["phi_pos"], eff_phi_neg=e["phi_neg"],
                               eff_lon_pos=e["lon_pos"], eff_lat_pos=e["lat_pos"], eff_lon_neg=e["lon_neg"], eff_lat_neg=e["lat_neg"]))
    return reps


# ---------------------------------------------------------------- per region

def run_region(row, read_maps, models, curve_times):
    """Returns (region row, dipole rows, curve rows)."""
    base = {k: row[k] for k in ("HARPNUM", "T_REC", "multiplicity", "noaa_absent", "flux_class", "lat_band", "weight", "pi", "perm_rank")}
    base.update(D_P1=row["d_axial_g"], D_bal_P1=row["d_axial_bal_g"], sep_cm_P1=row["d_cm"], tilt_P1=row["tilt_deg"])
    try:
        br, bm, h = read_maps(row["HARPNUM"], row["T_REC"])
    except (OSError, ValueError, KeyError) as exc:
        return [dict(base, threshold=t, status=f"read_error:{type(exc).__name__}") for t in THRESHOLDS], [], []
    regions, dips, curves = [], [], []
    for thr in THRESHOLDS:
        ing = ingredients(br, bm, h, thr)
        reg = dict(base, threshold=thr, status=ing["status"], n_pos=ing["n_pos"], n_neg=ing["n_neg"])
        if ing["status"] != "ok":
            regions.append(reg)
            continue
        reg.update({k: ing[k] for k in ("phi_pos", "phi_neg", "phibar", "imbalance", "lon_pos", "lat_pos", "lon_neg", "lat_neg",
                                        "area_pos", "area_neg", "D_pix_raw", "D_pix_bal", "D_scale")})
        reps = representations(ing, thr, models[REF])
        for name, (cf, st, extra) in reps.items():
            reg.update({f"{name}_status": st, **{f"{name}_{k}": v for k, v in extra.items()}})
            if cf is None:
                continue
            for tname, mdl in models.items():
                b0 = mdl.profile(cf)
                outs = mdl.evolve(b0, [t for _, t in TIMES])
                for (tl, ts), b in zip(TIMES, outs):
                    dips.append(dict(HARPNUM=row["HARPNUM"], threshold=thr, representation=name, transport=tname, time=tl, t_s=ts,
                                     D=mdl.dipole(b)))
                if tname == REF:
                    for tau_y, lab in TAUS:
                        for (tl, ts), b in zip(TIMES, outs):
                            dips.append(dict(HARPNUM=row["HARPNUM"], threshold=thr, representation=name, transport=lab, time=tl, t_s=ts,
                                             D=mdl.dipole(b) * float(C.decay_factor(ts, tau_y * C.YEAR))))
                    if thr == THRESHOLDS[0] and name in ("M", "B_point") and curve_times is not None:
                        for ts, b in zip(curve_times, mdl.evolve(b0, curve_times)):
                            curves.append(dict(HARPNUM=row["HARPNUM"], representation=name, t_day=ts / C.DAY, D=mdl.dipole(b)))
        regions.append(reg)
    return regions, dips, curves


# ---------------------------------------------------------------- summaries (§8)

def wquantile(x, w, q):
    """Lower weighted quantile: first sorted value whose cumulative normalised weight reaches q."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    if len(x) == 0:
        return np.nan
    o = np.argsort(x, kind="mergesort")
    cw = np.cumsum(w[o]) / w.sum()
    return float(x[o][np.searchsorted(cw, q - 1e-12)])


def summarise(regions, dips):
    reg = regions[["HARPNUM", "threshold", "status", "D_scale", "weight", "multiplicity", "flux_class", "lat_band"]]
    d = dips.merge(reg, on=["HARPNUM", "threshold"], how="left")
    M = d[d.representation == "M"][["HARPNUM", "threshold", "transport", "time", "D"]].rename(columns={"D": "D_M"})
    B = d[d.representation != "M"].merge(M, on=["HARPNUM", "threshold", "transport", "time"], how="inner")
    B["dD"] = B.D - B.D_M
    B["dD_scaled"] = B.dD / B.D_scale
    ref_m = d[(d.representation == "M") & (d.threshold == THRESHOLDS[0]) & (d.transport == REF)]
    thr_t = {t: 0.1 * wquantile(g.D.abs(), g.weight, 0.5) for t, g in ref_m.groupby("time")}
    B["ratio_threshold"] = B.time.map(thr_t)
    B["ratio"] = np.where((B.ratio_threshold > 0) & (B.D_M.abs() >= B.ratio_threshold), B.dD / B.D_M.abs(), np.nan)
    rows = []
    groups = [("all", None)] + [(c, c) for c in ("multiplicity", "flux_class", "lat_band")]
    for (rep, thr, tr, tm), g in B.groupby(["representation", "threshold", "transport", "time"], sort=True):
        for gname, col in groups:
            parts = [("all", g)] if col is None else [(f"{col}={v}", x) for v, x in g.groupby(col)]
            for label, x in parts:
                w = x.weight.to_numpy(float)
                defined = x.ratio.notna().to_numpy()
                r = dict(representation=rep, threshold=thr, transport=tr, time=tm, group=label, n=len(x), n_ratio=int(defined.sum()),
                         ratio_threshold=thr_t.get(tm, np.nan))
                for key, vals, ww in (("dD_scaled", x.dD_scaled, w), ("abs_dD", x.dD.abs(), w), ("ratio", x.ratio[defined], w[defined])):
                    for q, lab in ((0.1, "q10"), (0.5, "median"), (0.9, "q90")):
                        r[f"{key}_{lab}_w"] = wquantile(vals, ww, q)
                    r[f"{key}_median_unw"] = float(np.median(vals)) if len(vals) else np.nan
                if tm == "3y":
                    same = (np.sign(x.D) == np.sign(x.D_M)).to_numpy()
                    r["same_sign_w"] = float((w * same).sum() / w.sum()) if len(x) else np.nan
                    r["same_sign_unw"] = float(same.mean()) if len(x) else np.nan
                rows.append(r)
    return pd.DataFrame(rows), B


def convergence(sample_ok, read_maps):
    rows = []
    for _, row in sample_ok.head(3).iterrows():
        br, bm, h = read_maps(row["HARPNUM"], row["T_REC"])
        ing = ingredients(br, bm, h, THRESHOLDS[0])
        for rep in ("M", "B_point"):
            res = {}
            for lab, n, dt in (("ref", 400, C.DAY), ("N800", 800, C.DAY), ("dt_half", 400, None)):
                mdl = C.SFT1D(n=n, **C.REFERENCE)
                if dt is None:
                    mdl.dt_max = 0.5 * mdl.dt_max
                    dt = C.DAY
                cf = C.deposit_linear(ing["s_pix"], ing["F_bal"], mdl.s)[0] if rep == "M" else \
                    C.deposit_linear(*C.point_bipole(ing["lat_pos"], ing["lat_neg"], ing["phibar"]), mdl.s)[0]
                res[lab] = [mdl.dipole(b) for b in mdl.evolve(mdl.profile(cf), [t for _, t in TIMES], dt_s=dt)]
            for fine in ("N800", "dt_half"):
                for (tl, _), dc, df in zip(TIMES, res["ref"], res[fine]):
                    crit = abs(df - dc) / max(abs(df), 1e-6 * ing["D_scale"])
                    rows.append(dict(HARPNUM=row["HARPNUM"], representation=rep, refinement=fine, time=tl, D_ref=dc, D_fine=df,
                                     criterion=crit, passes=bool(crit <= 1e-3)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- build and run

def fits_reader(base=FITS):
    def read(harp, t_rec):
        folder = record_dir(base, t_rec)
        stem = file_stem(int(harp), t_rec)
        br, h = geo.read_sharp(folder / f"{stem}.Br.fits")
        bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
        return br, bm, h
    return read


def build(cat, read_maps, curves=True):
    pop, info = population(cat)
    sample = draw(pop)
    models = {k: C.SFT1D(**p) for k, p in TRANSPORTS.items()}
    curve_times = [d * C.DAY for d in range(0, 1096)] + [3 * C.YEAR] if curves else None
    regs, dips, curv = [], [], []
    for _, row in sample.iterrows():
        a, b, c = run_region(row, read_maps, models, curve_times)
        regs += a
        dips += b
        curv += c
    regions, dipoles = pd.DataFrame(regs), pd.DataFrame(dips)
    summary, _ = summarise(regions, dipoles)
    ok100 = regions[(regions.threshold == THRESHOLDS[0]) & (regions.status == "ok")].sort_values("perm_rank")
    conv = convergence(ok100, read_maps)
    cells = pop.groupby(["multiplicity", "flux_class", "lat_band"]).size().rename("N_cell").reset_index()
    return dict(SAMPLE=sample, CELLS=cells, REGIONS=regions, DIPOLES=dipoles, CURVES=pd.DataFrame(curv), SUMMARY=summary,
                CONVERGENCE=conv), dict(info, population=len(pop), sample=len(sample))


def run():
    probs = gate()
    if probs:
        sys.exit("gate: " + "; ".join(probs))
    cat = pd.read_csv(CATALOGUE, usecols=CAT_COLS, low_memory=False)
    prods, info = build(cat, fits_reader())
    tmp = Path(tempfile.mkdtemp(prefix=".SFT_MAP_BIPOLE_PILOT.tmp-", dir=OUT.parent))
    for k, v in prods.items():
        v.to_csv(tmp / (f"{k}.csv.gz" if k in ("DIPOLES", "CURVES") else f"{k}.csv"), index=False)
    fz = json.loads(FREEZE.read_text())
    meta = dict(protocol_sha256=sha(PROTOCOL), freeze_receipt_sha256=sha(FREEZE), freeze_commit=fz["freeze_commit"],
                script_sha256=sha(__file__), sft_core_sha256=sha(ROOT / "python/sharpbl/sft_core.py"), catalogue_sha256=sha(CATALOGUE),
                git_head=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                seed=SEED, per_cell=PER_CELL, transports=TRANSPORTS, reference=REF, times=[list(t) for t in TIMES], **info)
    meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
    (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    tmp.rename(OUT)
    print(f"written {OUT}")
    return 0


# ---------------------------------------------------------------- synthetic environment (also used by the recount)

def synthetic_env(td, n_harp=60, seed=11):
    """Synthetic catalogue (P1 columns) and CEA patches (Br, bitmap, keys.json) with one bipole each; HARP 1 is placed
    at 89.9 deg (deposition out of range expected) and HARP 2 has a single polarity."""
    from astropy.io import fits
    rng = np.random.default_rng(seed)
    td = Path(td)
    rows = []
    for i in range(1, n_harp + 1):
        lat0 = (1 if i % 2 else -1) * float(rng.uniform(3, 32))
        if i == 1:
            lat0 = 88.5
        lon0 = float(rng.uniform(0, 360))
        t_rec = f"2014.{1 + i % 12:02d}.{1 + i % 27:02d}_12:00:00_TAI"
        h = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="degree", CRPIX1=100.5, CRPIX2=60.5, CRVAL1=lon0,
                 CRVAL2=lat0, CDELT1=0.03, CDELT2=0.03, CROTA2=0.0, RSUN_REF=696000000, T_REC=t_rec, CRLN_OBS=lon0, CRLT_OBS=0.0)
        hdr = fits.Header()
        for k, v in h.items():
            hdr[k] = v
        lon, lat = geo.lonlat_maps(hdr, (119, 199))
        dl = (lon - lon0 + 180) % 360 - 180
        sep, tilt = rng.uniform(1.0, 2.5), np.radians(rng.uniform(-20, 40))
        br = np.zeros(lon.shape)
        pols = ((1.0, 0.5), (-1.0, -0.5)) if i != 2 else ((1.0, 0.0),)
        for sg, f in pols:
            br += sg * rng.uniform(600, 1200) * np.exp(-((dl - f * sep * np.cos(tilt)) ** 2 + (lat - lat0 - f * sep * np.sin(tilt)) ** 2) / (2 * 0.35 ** 2))
        br += rng.normal(0, 10, br.shape)
        bm = np.full(br.shape, 34.0)
        bm[:, :5] = 1.0
        folder = record_dir(td / "fits", t_rec)
        folder.mkdir(parents=True, exist_ok=True)
        stem = file_stem(i, t_rec)
        fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(br.astype(np.float32))]).writeto(folder / f"{stem}.Br.fits", overwrite=True)
        fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(bm.astype(np.float32))]).writeto(folder / f"{stem}.bitmap.fits", overwrite=True)
        (folder / f"{stem}.keys.json").write_text(json.dumps(h))
        rows.append(dict(HARPNUM=i, T_REC=t_rec, role="primary" if i % 7 else "both", valid_bl=0 if i % 23 == 0 else 1,
                         family_rank=1 if i % 19 == 0 else 0, NOAA_NUM=int(rng.choice([0, 1, 1, 2])), USFLUX=float(rng.uniform(1e21, 1e23)),
                         LAT_FWT=lat0, d_axial_g=np.nan, d_axial_bal_g=np.nan, d_cm=np.nan, tilt_deg=np.nan, phi_pos_mx=np.nan, phi_neg_mx=np.nan))
        rows.append(dict(rows[-1], role="control"))
    return pd.DataFrame(rows), fits_reader(td / "fits")


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    with tempfile.TemporaryDirectory() as td:
        cat, reader = synthetic_env(td)
        prods, info = build(cat, reader, curves=False)
        S, R, D, Su = prods["SAMPLE"], prods["REGIONS"], prods["DIPOLES"], prods["SUMMARY"]
        pop, _ = population(cat)
        ok("population: primary/both, valid_bl 1, family_rank 0, finite USFLUX; ordered by HARPNUM",
           set(pop.HARPNUM) == set(cat[cat.role.isin(["primary", "both"]) & (cat.valid_bl == 1) & (cat.family_rank == 0)].HARPNUM)
           and pop.HARPNUM.is_monotonic_increasing)
        perm = np.random.default_rng(SEED).permutation(len(pop))
        exp = []
        for idx in perm:
            key = tuple(pop.loc[idx, ["multiplicity", "flux_class", "lat_band"]])
            if sum(1 for e in exp if e[0] == key) < PER_CELL:
                exp.append((key, int(pop.loc[idx, "HARPNUM"])))
        ok("draw: first 4 per cell in the order of default_rng(36_100_000).permutation; weights N/n, pi n/N",
           [h for _, h in exp] == list(S.HARPNUM) and np.allclose(S.weight * S.pi, 1.0))
        r1 = R[(R.HARPNUM == 1) & (R.threshold == 100.0)]
        r2 = R[(R.HARPNUM == 2) & (R.threshold == 100.0)]
        ok("near-pole patch: M deposition_out_of_range (no clipping); single polarity: no_two_polarities; both kept in REGIONS",
           (r1.empty or (r1.M_status == "deposition_out_of_range").all()) and (r2.empty or (r2.status == "no_two_polarities").all()),
           f"in sample: {int(1 in set(S.HARPNUM))}, {int(2 in set(S.HARPNUM))}")
        okr = R[(R.status == "ok") & (R.M_status == "ok")]
        d0 = D[(D.representation == "M") & (D.time == "0") & (D.transport == REF)].merge(okr[["HARPNUM", "threshold", "D_pix_bal", "D_scale"]])
        ok("D_M(0) of the deposited profile = D of the balanced pixels (1e-12 of D_scale)", len(d0) > 0
           and (np.abs(d0.D - d0.D_pix_bal) <= 1e-12 * d0.D_scale).all())
        p0 = D[(D.representation == "B_point") & (D.time == "0") & (D.transport == REF)].merge(okr)
        form = [C.point_bipole_dipole(a, b, c, r) for a, b, c, r in zip(p0.lat_pos, p0.lat_neg, p0.phibar, [C.RSUN_CM] * len(p0))]
        ok("B_point(0) = 3 phibar/(4 pi R^2)(sin lat+ - sin lat-) (1e-12 of D_scale)", len(p0) > 0 and (np.abs(p0.D - form) <= 1e-12 * p0.D_scale).all())
        g = okr[okr.threshold == 100.0]
        ok("Gaussian sensitivities recorded with effective fluxes and centroids; only at 100 G",
           g[["B_gauss_area_eff_phi_pos", "B_gauss_2deg_eff_lat_pos", "B_gauss_4deg_eff_lon_neg"]].notna().all().all()
           and set(D[D.threshold == 300.0].representation) == {"M", "B_point"})
        r300 = okr[okr.threshold == 300.0].set_index("HARPNUM")
        r100 = okr[okr.threshold == 100.0].set_index("HARPNUM")
        common = r300.index.intersection(r100.index)
        ok("300 G sensitivity recomputes the ingredients (fluxes differ from 100 G)", len(common) > 0
           and (r300.loc[common, "phi_pos"] < r100.loc[common, "phi_pos"]).all())
        t = D[(D.transport == "ref_tau5y") & (D.representation == "M")].merge(
            D[(D.transport == REF) & (D.representation == "M")], on=["HARPNUM", "threshold", "time", "representation"], suffixes=("", "_ref"))
        ok("tau = 5 years as the factor exp(-t/tau) on the reference", len(t) > 0
           and np.allclose(t.D, t.D_ref * np.exp(-t.t_s / (5 * C.YEAR)), rtol=1e-14, atol=0))
        ok("every transport and time present for every successful representation",
           D.groupby(["HARPNUM", "threshold", "representation"]).size().eq(len(TIMES) * (len(TRANSPORTS) + len(TAUS))).all())
        x, w = np.array([3.0, 1.0, 2.0, 4.0]), np.array([1.0, 1.0, 1.0, 5.0])
        ok("weighted quantile (lower): hand example", wquantile(x, w, 0.5) == 4.0 and wquantile(x, w, 0.1) == 1.0 and wquantile(x, np.ones(4), 0.5) == 2.0)
        a = Su[(Su.group == "all") & (Su.representation == "B_point") & (Su.threshold == 100.0) & (Su.transport == REF)]
        ok("summary: one 'all' row per time with n, weighted quantiles and the ratio threshold; same-sign fraction at 3 years",
           len(a) == len(TIMES) and a.ratio_threshold.notna().all() and a[a.time == "3y"].same_sign_w.notna().all())
        cv = prods["CONVERGENCE"]
        ok("convergence on the first 3 successful regions: N800 and halved step at all times, criterion recorded",
           len(cv) == 3 * 2 * 2 * len(TIMES) and cv.criterion.notna().all(), f"max {cv.criterion.max():.1e}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
