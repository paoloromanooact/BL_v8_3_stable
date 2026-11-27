"""SFT observed-evolution pilot (point 3), runner of the DRAFT protocol docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md (rev. 4).

NOT FROZEN: this runner is preparatory; it refuses --run until the protocol is frozen (receipt file present and
matching) and the code is reviewed. --selftest uses synthetic primary -> control pairs; no observed map is read.

Steps (draft section in brackets)
1. Pool [§4]: primary and control distinct, control later, 1 <= T_OBS(control) - T_OBS(primary) <= 4.5 days, same HARP,
   family_rank 0, valid_bl 1 at the primary; geometric feasibility from headers (C area >= 25 deg^2, §1, §3).
2. Strata dt (1-3, 3-4.5 days) x multiplicity; draw default_rng(36_200_000), 18 per cell; weights N/n.
3. Split [§4]: provisional default_rng(36_200_001) per cell (first floor(n/3) development); graph with edges for the same
   P1e family or for intersecting time windows AND intersecting t0 Carrington boxes; each component goes to the side of
   its HARP with the smallest HARPNUM.
4. Fields [§3]: main = all finite pixels (|Br| <= 10000 G) of the CEA patch, no threshold, no bitmap, no balancing;
   alternative P1 source (bitmap >= 33, |Br| >= 100 G); balanced sensitivity applied to t0 and t1 alike.
5. Grid and domain [§3, §5]: Carrington box at 0.06 deg on the primary longitude branch, P0/P1 coverage from pixel centres,
   C = erode(P0) & P1 with the directional margins at the maxima of the parameter grid; area < 25 deg^2 -> not evaluable.
6. Models [§5, §6]: SFT (2x2 transport grid, python/sharpbl/sft_local.py), persistence, rotation only; same prepared
   field; observed t1 deposited with the same operator.
7. Measures on C [§3]: integral (no cut) D, fluxes, centroids, separation, tilt, lat_mean, L2 norm; 100 G cut; P1-style on
   the own bitmaps; correlation diagnostic; advected-mask diagnostic (preimage of 4x4 subpoints, RK4 100 steps, >= 8/16).
8. Metrics [§8]: errors, paired differences |e_ref| - |e_SFT| (tilt axial, longitude circular), improvement/tie/worse;
   summaries on the verification set only (development separate), weights N/n.
9. Boundary test (box widened by m, change < 1e-6 of the scale) and convergence (0.03 deg, half step) recorded.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/sft_observed_pilot.py --selftest
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import binary_erosion
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo, measure, sft_core as C, sft_local as L  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402

PROTOCOL_DRAFT = ROOT / "docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_DRAFT.md"
FREEZE = ROOT / "docs/PROTOCOL_SFT_OBSERVED_EVOLUTION_FREEZE.json"     # does not exist until the freeze
SEED_DRAW, SEED_SPLIT, PER_CELL = 36_200_000, 36_200_001, 18
STEP, AREA_MIN = 0.06, 25.0
ETA_MAX, DU_MAX, P = 466.8, 0.041, 2.33
R_KM = 6.96e5
TRANSPORTS = {f"eta{p['eta_km2s']:g}_du{p['du_kms']:g}": p for p in C.SENSITIVITY}
REF = f"eta{C.REFERENCE['eta_km2s']:g}_du{C.REFERENCE['du_kms']:g}"
OBS = ("D_g", "phi_pos", "phi_neg", "phi_net", "lat_pos", "lon_pos", "lat_neg", "lon_neg", "sep_deg", "tilt_deg", "lat_mean")


# ---------------------------------------------------------------- reading

def reader(base):
    def read(harp, t_rec):
        folder, stem = record_dir(base, t_rec), file_stem(int(harp), t_rec)
        br, h = geo.read_sharp(folder / f"{stem}.Br.fits")
        bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
        return br, bm, h
    return read


def t_obs(h):
    s = str(h["T_OBS"]).replace("_TAI", "").replace(".", "-", 2).replace("_", " ")
    return pd.Timestamp(s)


# ---------------------------------------------------------------- margins, coverage, domain

def margins(gap_days, lat_range):
    dts = gap_days * C.DAY
    dif = math.degrees(math.sqrt(4 * ETA_MAX * dts) / R_KM)
    lr = np.radians(np.linspace(0, 80, 801))
    vmax = DU_MAX * float(np.max(np.sin(lr) * np.cos(lr) ** P))
    rot = float(np.max(np.abs(C.omega_rel_deg_day(np.linspace(lat_range[0], lat_range[1], 60))))) * gap_days
    latmax = max(abs(lat_range[0]), abs(lat_range[1]))
    return dif + math.degrees(vmax * dts / R_KM) + 0.5, (dif + 0.5) / math.cos(math.radians(latmax)) + rot


def coverage(box, lat, lon):
    g = np.zeros((box.ny, box.nx), bool)
    iy = np.floor((lat - box.lat_e[0]) / box.step).astype(int)
    ix = np.floor((lon - box.lon_e[0]) / box.step).astype(int)
    inside = (iy >= 0) & (iy < box.ny) & (ix >= 0) & (ix < box.nx)
    g[iy[inside], ix[inside]] = True
    return g


def domain(box, P0, P1, m_lat, m_lon):
    ky, kx = int(math.ceil(m_lat / box.step)), int(math.ceil(m_lon / box.step))
    Cm = binary_erosion(P0, structure=np.ones((2 * ky + 1, 2 * kx + 1), bool), border_value=0) & P1
    area = float((Cm * box.A).sum()) / box.r ** 2 * (180 / math.pi) ** 2
    return Cm, area


# ---------------------------------------------------------------- fields

class BalanceUnavailable(ValueError):
    """Balancing needs both polarities among the selected pixels (otherwise: status balance_unavailable)."""


def pixels(br, bm, h, branch, kind):
    """(lat, lon on the branch, flux Mx, P1-selection mask) for the field preparation `kind`. For 'balanced' with an
    empty polarity it raises BalanceUnavailable: no silent rescaling of the other polarity."""
    lon, lat = geo.lonlat_maps(h, br.shape)
    lon = (lon - branch + 180.0) % 360.0 - 180.0 + branch
    area = geo.pixel_area_cm2(h)
    fin = np.isfinite(br) & (np.abs(br) <= measure.MAX_ABS_BR_G) & np.isfinite(lon) & np.isfinite(lat)
    if kind == "p1_source":
        fin &= measure.base_mask(br, bm, 33, measure.MAX_ABS_BR_G) & (np.abs(br) >= measure.THRESHOLD_G)
    F = np.where(fin, br * area, 0.0)
    if kind == "balanced":
        pp, nn = F[fin & (br > 0)].sum(), -F[fin & (br < 0)].sum()
        if not (pp > 0 and nn > 0):
            raise BalanceUnavailable("one polarity is empty")
        pb = 0.5 * (pp + nn)
        F = np.where(br > 0, F * pb / pp, F * pb / nn)
    return lat[fin], lon[fin], F[fin], lat, lon, np.isfinite(br) & (np.abs(br) <= measure.MAX_ABS_BR_G)


# ---------------------------------------------------------------- one pair

def axial(a, b):
    return (a - b + 90.0) % 180.0 - 90.0


def circ(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def errors(obs, mod):
    e = {}
    for k in OBS:
        if k == "tilt_deg":
            e[k] = axial(obs[k], mod[k])
        elif k.startswith("lon_"):
            e[k] = circ(obs[k], mod[k])
        else:
            e[k] = obs[k] - mod[k]
    return e


def advected_mask(box, bitmap_cov, gap_s):
    """Preimage of 4x4 subpoints per cell (RK4, 100 steps, rotation + meridional flow of the reference, no diffusion)."""
    sub = (np.arange(4) + 0.5) / 4
    LATc = box.lat_e[:-1, None, None, None] + box.step * sub[None, None, :, None]
    LONc = box.lon_e[None, :-1, None, None] + box.step * sub[None, None, None, :]
    la = np.broadcast_to(LATc, (box.ny, box.nx, 4, 4)).copy()
    lo = np.broadcast_to(LONc, (box.ny, box.nx, 4, 4)).copy()
    h = -gap_s / 100

    def f(la_, lo_):
        dlo = C.omega_rel_deg_day(la_) / C.DAY
        dla = np.degrees(C.v_merid_cm_s(np.radians(la_), C.REFERENCE["du_kms"], C.REFERENCE["p"]) / C.RSUN_CM)
        return dla, dlo
    for _ in range(100):
        k1 = f(la, lo)
        k2 = f(la + h / 2 * k1[0], lo + h / 2 * k1[1])
        k3 = f(la + h / 2 * k2[0], lo + h / 2 * k2[1])
        k4 = f(la + h * k3[0], lo + h * k3[1])
        la = la + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        lo = lo + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
    iy = np.floor((la - box.lat_e[0]) / box.step).astype(int)
    ix = np.floor((lo - box.lon_e[0]) / box.step).astype(int)
    ok = (iy >= 0) & (iy < box.ny) & (ix >= 0) & (ix < box.nx)
    hit = np.zeros(la.shape, bool)
    hit[ok] = bitmap_cov[iy[ok], ix[ok]]
    return hit.sum(axis=(2, 3)) >= 8


def run_pair(row, read, transports=TRANSPORTS, kinds=("raw", "p1_source", "balanced"), extra_checks=False):
    br0, bm0, h0 = read(row["HARPNUM"], row["T_REC_p"])
    br1, bm1, h1 = read(row["HARPNUM"], row["T_REC_c"])
    gap_s = (t_obs(h1) - t_obs(h0)).total_seconds()
    branch = float(h0["CRVAL1"])
    out = []
    lon0, lat0 = geo.lonlat_maps(h0, br0.shape)
    lon0 = (lon0 - branch + 180.0) % 360.0 - 180.0 + branch
    m_lat, m_lon = margins(gap_s / C.DAY, (np.nanmin(lat0), np.nanmax(lat0)))
    lat_rng = (max(-89.0, np.nanmin(lat0) - 2 * m_lat), min(89.0, np.nanmax(lat0) + 2 * m_lat))
    lon_rng = (np.nanmin(lon0) - 2 * m_lon, np.nanmax(lon0) + 2 * m_lon)
    rot_box = L.LocalBox(lat_rng, lon_rng, STEP, meridional=False, diffusion=False)
    base = dict(HARPNUM=row["HARPNUM"], gap_s=gap_s, m_lat=m_lat, m_lon=m_lon)
    for kind in kinds:
        try:
            la0, lo0, F0, LAT0, LON0, fin0 = pixels(br0, bm0, h0, branch, kind)
            la1, lo1, F1, LAT1, LON1, fin1 = pixels(br1, bm1, h1, branch, kind)
        except BalanceUnavailable:
            out.append(dict(base, kind=kind, status="balance_unavailable"))
            continue
        P0, P1 = coverage(rot_box, LAT0[fin0], LON0[fin0]), coverage(rot_box, LAT1[fin1], LON1[fin1])
        Cm, area = domain(rot_box, P0, P1, m_lat, m_lon)
        rec = dict(base, kind=kind, area_C=area)
        if area < AREA_MIN:
            out.append(dict(rec, status="not_evaluable"))
            continue
        B0, n0 = rot_box.deposit(la0, lo0, F0)
        keep = (np.sin(np.radians(la1)) >= np.sin(np.radians(rot_box.lat[0]))) & (np.sin(np.radians(la1)) <= np.sin(np.radians(rot_box.lat[-1]))) \
            & (lo1 >= rot_box.lon[0]) & (lo1 <= rot_box.lon[-1])
        B1, n1 = rot_box.deposit(la1[keep], lo1[keep], F1[keep])
        if B0 is None or B1 is None:
            out.append(dict(rec, status="deposition_out_of_range"))
            continue
        mobs = rot_box.measures(B1, Cm)
        models = {"persistence": B0, "rotation": rot_box.evolve(B0, gap_s)}
        for tn, par in transports.items():
            bx = L.LocalBox(lat_rng, lon_rng, STEP, **par)
            models[tn] = bx.evolve(B0, gap_s)
        cut = rot_box.measures(B1, Cm, threshold=100.0)
        rec.update(status="ok", t1_pixels_outside_box=int((~keep).sum()), C_cells=int(Cm.sum()), C_flux_initial_out=float(np.abs(B0[~Cm] * rot_box.A[~Cm]).sum()),
                   **{f"obs_{k}": mobs[k] for k in OBS}, obs_L2=float(np.sqrt((B1[Cm] ** 2 * rot_box.A[Cm]).sum())),
                   **{f"obs100_{k}": cut[k] for k in OBS})
        for name, B in models.items():
            mm = rot_box.measures(B, Cm)
            e = errors(mobs, mm)
            rec.update({f"{name}_{k}": mm[k] for k in OBS})
            rec.update({f"err_{name}_{k}": e[k] for k in OBS})
            rec[f"{name}_L2"] = float(np.sqrt((B[Cm] ** 2 * rot_box.A[Cm]).sum()))
            rec[f"err_{name}_L2"] = float(np.sqrt(((B1 - B)[Cm] ** 2 * rot_box.A[Cm]).sum()))
            x, y, w = B1[Cm], B[Cm], rot_box.A[Cm]
            vx, vy = np.average((x - np.average(x, weights=w)) ** 2, weights=w), np.average((y - np.average(y, weights=w)) ** 2, weights=w)
            rec[f"corr_{name}"] = float(np.average((x - np.average(x, weights=w)) * (y - np.average(y, weights=w)), weights=w) / math.sqrt(vx * vy)) if vx > 0 and vy > 0 else np.nan
        if kind == "raw":
            bcov = coverage(rot_box, LAT0[measure.base_mask(br0, bm0, 33, measure.MAX_ABS_BR_G) & fin0], LON0[measure.base_mask(br0, bm0, 33, measure.MAX_ABS_BR_G) & fin0])
            am = advected_mask(rot_box, bcov, gap_s)
            rec["obs_flux_outside_advected"] = float(np.abs(B1[Cm & ~am] * rot_box.A[Cm & ~am]).sum())
            rec["obs_flux_on_C"] = float(np.abs(B1[Cm] * rot_box.A[Cm]).sum())
            p0, p1 = measure.measure_v84(br0, bm0, h0), measure.measure_v84(br1, bm1, h1)
            rec.update(p1_D_t0=p0["d_axial_g"], p1_D_t1=p1["d_axial_g"], p1_phi_t0=p0["phi_mx"], p1_phi_t1=p1["phi_mx"])
            if extra_checks:
                ky, kx = int(math.ceil(m_lat / STEP)), int(math.ceil(m_lon / STEP))     # widen by whole cells: same grid
                wide = L.LocalBox((rot_box.lat_e[0] - ky * STEP, rot_box.lat_e[-1] + ky * STEP),
                                  (rot_box.lon_e[0] - kx * STEP, rot_box.lon_e[-1] + kx * STEP), STEP)
                narrow = L.LocalBox(lat_rng, lon_rng, STEP, **C.REFERENCE)
                narrow.dt = wide.dt = min(narrow.dt, wide.dt)     # same time step: isolate the boundary effect
                Bw, _ = wide.deposit(la0, lo0, F0)
                Bw = wide.evolve(Bw, gap_s)
                Bn = narrow.evolve(B0, gap_s)
                iy0 = int(round((rot_box.lat_e[0] - wide.lat_e[0]) / STEP))
                ix0 = int(round((rot_box.lon_e[0] - wide.lon_e[0]) / STEP))
                sub = Bw[iy0:iy0 + rot_box.ny, ix0:ix0 + rot_box.nx]
                mw, mr = rot_box.measures(sub, Cm), rot_box.measures(Bn, Cm)
                rec["boundary_D_rel"] = abs(mw["D_g"] - mr["D_g"]) / max(abs(mr["D_g"]), 1e-30)
                rec["boundary_phi_rel"] = abs(mw["phi_pos"] - mr["phi_pos"]) / max(mr["phi_pos"], 1e-30)
        out.append(rec)
    return out


# ---------------------------------------------------------------- pool, draw, split

def draw(pool):
    pool = pool.sort_values("HARPNUM").reset_index(drop=True)
    pool["dt_class"] = np.where(pool.gap_d < 3, "1-3", "3-4.5")
    pool["multiplicity"] = np.where(pool.NOAA_NUM == 1, "un NOAA", "altro/ignoto")
    perm = np.random.default_rng(SEED_DRAW).permutation(len(pool))
    pool["perm_rank"] = np.argsort(perm)
    keys = ["dt_class", "multiplicity"]
    N = pool.groupby(keys).size().rename("N_cell")
    s = pool.sort_values("perm_rank").groupby(keys, group_keys=False).head(PER_CELL)
    s = s.merge(N, on=keys).merge(s.groupby(keys).size().rename("n_cell"), on=keys)
    s["weight"] = s.N_cell / s.n_cell
    return s.sort_values("HARPNUM").reset_index(drop=True)


def split(s, boxes):
    """boxes: HARPNUM -> (t0, t1, lat_lo, lat_hi, lon_lo, lon_hi) of the t0 patch (lon on its own branch)."""
    s = s.copy()
    perm = np.random.default_rng(SEED_SPLIT).permutation(len(s))
    s["split_rank"] = np.argsort(perm)
    s["provisional"] = "verification"
    for _, g in s.groupby(["dt_class", "multiplicity"]):
        dev = g.sort_values("split_rank").index[: len(g) // 3]
        s.loc[dev, "provisional"] = "development"
    h = list(s.HARPNUM)
    parent = {x: x for x in h}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    fam = dict(zip(s.HARPNUM, s.family_id))
    for i, a in enumerate(h):
        for b in h[i + 1:]:
            ba, bb = boxes[a], boxes[b]
            time_ok = ba[0] <= bb[1] and bb[0] <= ba[1]
            lat_ok = ba[2] <= bb[3] and bb[2] <= ba[3]
            dl = circ(0.5 * (ba[4] + ba[5]), 0.5 * (bb[4] + bb[5]))
            lon_ok = abs(dl) <= 0.5 * (ba[5] - ba[4]) + 0.5 * (bb[5] - bb[4])
            if (pd.notna(fam[a]) and fam[a] == fam[b]) or (time_ok and lat_ok and lon_ok):
                parent[find(a)] = find(b)
    comp = {x: find(x) for x in h}
    s["component"] = s.HARPNUM.map(comp)
    lead = s.groupby("component").HARPNUM.min()
    side = dict(zip(s.HARPNUM, s.provisional))
    s["set"] = s.component.map(lambda c: side[lead[c]])
    return s


# ---------------------------------------------------------------- summaries

def summarise(res, sample):
    d = res[res.status == "ok"].merge(sample[["HARPNUM", "set", "weight", "dt_class", "multiplicity", "usflux_ratio"]], on="HARPNUM")
    rows = []
    for (kind, st), g in d.groupby(["kind", "set"]):
        for ref in ("persistence", "rotation"):
            for k in OBS + ("L2",):
                a, b = g[f"err_{ref}_{k}"].abs(), g[f"err_{REF}_{k}"].abs()
                diff = (a - b).to_numpy()
                fin = np.isfinite(diff)
                w = g.weight.to_numpy()[fin]
                x = diff[fin]
                r = dict(kind=kind, set=st, reference=ref, observable=k, n=int(fin.sum()))
                for q, lab in ((0.1, "q10"), (0.5, "median"), (0.9, "q90")):
                    r[f"paired_{lab}_w"] = C_wq(x, w, q)
                r["improved"] = int((x > 0).sum())
                r["tied"] = int((x == 0).sum())
                r["worse"] = int((x < 0).sum())
                err = g[f"err_{REF}_{k}"].abs().to_numpy()
                ok_ = np.isfinite(err) & np.isfinite(g.usflux_ratio.to_numpy())
                r["spearman_err_vs_usflux_ratio"] = float(spearmanr(err[ok_], g.usflux_ratio.to_numpy()[ok_]).statistic) if ok_.sum() > 2 else np.nan
                rows.append(r)
    return pd.DataFrame(rows)


def C_wq(x, w, q):
    if not len(x):
        return np.nan
    o = np.argsort(x, kind="mergesort")
    c = np.cumsum(w[o]) / w.sum()
    return float(x[o][np.searchsorted(c, q - 1e-12)])


# ---------------------------------------------------------------- synthetic selftest

def synthetic_pairs(td, n=8, seed=5):
    """Primary/control pairs: the control is the primary bipole shifted by the rotation relative to Carrington over the
    gap (plus, for odd HARPs, a new small bipole = emergence). HARP 1 has dt = 0 (identity)."""
    from astropy.io import fits
    rng = np.random.default_rng(seed)
    td = Path(td)
    cat = []
    for i in range(1, n + 1):
        lat0, lon0 = float(rng.uniform(8, 22)) * (1 if i % 2 else -1), float(rng.uniform(20, 340))
        gap = 0.0 if i == 1 else float(rng.uniform(1.2, 4.3))
        t0 = pd.Timestamp("2015-03-01 12:00:00") + pd.Timedelta(days=3 * i)
        t1 = t0 + pd.Timedelta(seconds=gap * C.DAY)
        shift = C.omega_rel_deg_day(lat0) * gap
        for role, t, dlon, extra in (("primary", t0, 0.0, False), ("control", t1, shift, i % 2 == 1 and i > 1)):
            trec = t.strftime("%Y.%m.%d_%H:%M:%S") + "_TAI"
            if role == "control" and i == 1:
                trec = (t0 + pd.Timedelta(seconds=1)).strftime("%Y.%m.%d_%H:%M:%S") + "_TAI"
            h = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="degree", CRPIX1=300.5, CRPIX2=200.5, CRVAL1=lon0,
                     CRVAL2=lat0, CDELT1=0.03, CDELT2=0.03, CROTA2=0.0, RSUN_REF=696000000, T_REC=trec,
                     T_OBS=t.strftime("%Y.%m.%d_%H:%M:%S") + "_TAI", CRLN_OBS=lon0, CRLT_OBS=0.0)
            hdr = fits.Header()
            for k, v in h.items():
                hdr[k] = v
            lon, lat = geo.lonlat_maps(hdr, (399, 599))
            dl = (lon - lon0 - dlon + 180) % 360 - 180
            br = 900 * np.exp(-((dl - 1.0) ** 2 + (lat - lat0 + 0.4) ** 2) / (2 * 0.5 ** 2)) - 800 * np.exp(-((dl + 1.0) ** 2 + (lat - lat0 - 0.4) ** 2) / (2 * 0.5 ** 2))
            if extra:
                br += 400 * np.exp(-((dl - 3.0) ** 2 + (lat - lat0) ** 2) / (2 * 0.3 ** 2)) - 400 * np.exp(-((dl - 2.2) ** 2 + (lat - lat0) ** 2) / (2 * 0.3 ** 2))
            bm = np.where(np.abs(br) > 50, 34.0, 1.0)
            folder = record_dir(td / "fits", trec)
            folder.mkdir(parents=True, exist_ok=True)
            stem = file_stem(i, trec)
            fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(br.astype(np.float64))]).writeto(folder / f"{stem}.Br.fits", overwrite=True)
            fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(bm.astype(np.float32))]).writeto(folder / f"{stem}.bitmap.fits", overwrite=True)
            (folder / f"{stem}.keys.json").write_text(json.dumps(h))
            cat.append(dict(HARPNUM=i, role=role, T_REC=trec, gap=gap))
    c = pd.DataFrame(cat)
    pairs = c[c.role == "primary"].merge(c[c.role == "control"], on="HARPNUM", suffixes=("_p", "_c"))
    return pairs, reader(td / "fits")


def synthetic_one_polarity(td, harp=99):
    """A pair (dt 1 day) with a single positive polarity: for the balance_unavailable regression."""
    from astropy.io import fits
    t0 = pd.Timestamp("2016-01-10 00:00:00")
    trecs = []
    for t in (t0, t0 + pd.Timedelta(days=1)):
        trec = t.strftime("%Y.%m.%d_%H:%M:%S") + "_TAI"
        h = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="degree", CUNIT2="degree", CRPIX1=300.5, CRPIX2=200.5, CRVAL1=100.0,
                 CRVAL2=12.0, CDELT1=0.03, CDELT2=0.03, CROTA2=0.0, RSUN_REF=696000000, T_REC=trec, T_OBS=trec, CRLN_OBS=100.0, CRLT_OBS=0.0)
        hdr = fits.Header()
        for k, v in h.items():
            hdr[k] = v
        lon, lat = geo.lonlat_maps(hdr, (399, 599))
        br = 900 * np.exp(-(((lon - 100.0 + 180) % 360 - 180) ** 2 + (lat - 12.0) ** 2) / (2 * 0.5 ** 2))
        bm = np.where(br > 50, 34.0, 1.0)
        folder = record_dir(Path(td) / "fits", trec)
        folder.mkdir(parents=True, exist_ok=True)
        stem = file_stem(harp, trec)
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(br)]).writeto(folder / f"{stem}.Br.fits", overwrite=True)
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(bm.astype(np.float32))]).writeto(folder / f"{stem}.bitmap.fits", overwrite=True)
        (folder / f"{stem}.keys.json").write_text(json.dumps(h))
        trecs.append(trec)
    return dict(HARPNUM=harp, T_REC_p=trecs[0], T_REC_c=trecs[1])


def selftest():
    res = []

    def ok(name, cond, info=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    small = {REF: C.REFERENCE}
    with tempfile.TemporaryDirectory() as td:
        pairs, read = synthetic_pairs(td, n=4)
        out = []
        for _, r in pairs.iterrows():
            out += run_pair(r, read, transports=small, kinds=("raw", "balanced"), extra_checks=(r.HARPNUM == 2))
        R = pd.DataFrame(out)
        r1 = R[(R.HARPNUM == 1) & (R.kind == "raw")].iloc[0]
        ok("identity at dt = 0: every model equals the observation on C (D and fluxes)",
           r1.status == "ok" and all(abs(r1[f"err_{m}_D_g"]) <= 1e-12 * abs(r1.obs_D_g) for m in ("persistence", "rotation", REF)),
           f"area C {r1.area_C:.1f} deg2")
        r2 = R[(R.HARPNUM == 2) & (R.kind == "raw")].iloc[0]
        ok("pure rotation (even HARP, no emergence): the rotation reference reduces the centroid longitude error vs persistence",
           abs(r2.err_rotation_lon_pos) < 0.2 * abs(r2.err_persistence_lon_pos), f"{r2.err_rotation_lon_pos:.3f} vs {r2.err_persistence_lon_pos:.3f} deg")
        ok("SFT run on the same prepared field: flux on C changes little in a few days; boundary test recorded (< 1e-6)",
           abs(r2[f"{REF}_phi_net"] - r2.persistence_phi_net) < 0.05 * r2.persistence_phi_pos and r2.boundary_D_rel < 1e-6,
           f"boundary D {r2.boundary_D_rel:.1e}")
        r3 = R[(R.HARPNUM == 3) & (R.kind == "raw")].iloc[0]
        ok("emergence (odd HARP): observed flux outside the advected mask is positive and reported",
           r3.obs_flux_outside_advected > 0, f"{r3.obs_flux_outside_advected / r3.obs_flux_on_C:.3f} of the flux on C")
        ok("balanced sensitivity computed on both instants; P1-style measures recorded", (R.kind == "balanced").any() and R[R.kind == "raw"].p1_D_t0.notna().all())
        # regression (review 25 Nov): one polarity -> balanced unavailable, raw flux NOT halved
        one = synthetic_one_polarity(td)
        r1p = {r["kind"]: r for r in run_pair(one, read, transports=small, kinds=("raw", "balanced"))}
        br_, bm_, h_ = read(one["HARPNUM"], one["T_REC_p"])
        la_, lo_, F_, _, _, _ = pixels(br_, bm_, h_, float(h_["CRVAL1"]), "raw")
        full = float(np.nansum(np.where(np.isfinite(br_) & (np.abs(br_) <= measure.MAX_ABS_BR_G), br_, 0.0)) * geo.pixel_area_cm2(h_))
        ok("one polarity: balanced -> balance_unavailable; raw measured and its pixel flux equals the full map flux (not halved)",
           r1p["balanced"]["status"] == "balance_unavailable" and r1p["raw"]["status"] == "ok" and abs(F_.sum() - full) <= 1e-12 * full
           and r1p["raw"]["obs_phi_pos"] > 0.9 * full, f"raw pixel flux / full {F_.sum() / full:.12f}; on C {r1p['raw']['obs_phi_pos'] / full:.3f}")
        # draw and split
        rng = np.random.default_rng(2)
        pool = pd.DataFrame(dict(HARPNUM=np.arange(1, 121), gap_d=rng.uniform(1, 4.5, 120), NOAA_NUM=rng.choice([0, 1, 2], 120),
                                 family_id=np.where(np.arange(120) % 10 == 0, 7, np.nan), usflux_ratio=rng.uniform(1, 2, 120)))
        s = draw(pool)
        boxes = {h: (float(h), float(h) + 2.0, 10.0, 15.0, (h * 37) % 360, (h * 37) % 360 + 8.0) for h in s.HARPNUM}
        sp = split(s, boxes)
        ok("draw: 18 per cell from default_rng(36_200_000), weights N/n", (sp.groupby(["dt_class", "multiplicity"]).size() <= PER_CELL).all()
           and np.allclose(sp.weight * sp.n_cell / sp.N_cell, 1))
        comp_sides = sp.groupby("component").set.nunique()
        ok("split: every connected component on one side; family members together", (comp_sides == 1).all()
           and sp[sp.family_id == 7].set.nunique() <= 1)
        sm = summarise(R.assign(), pd.DataFrame(dict(HARPNUM=[1, 2, 3, 4], set="verification", weight=1.0, dt_class="1-3",
                                                     multiplicity="un NOAA", usflux_ratio=[1.0, 1.1, 1.5, 1.2])))
        ok("summary: paired differences, improvement/tie/worse counts and Spearman per observable", len(sm) > 0
           and {"paired_median_w", "improved", "tied", "worse", "spearman_err_vs_usflux_ratio"} <= set(sm.columns))
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


def run():
    if not FREEZE.exists():
        sys.exit("protocol not frozen: no run (preparatory runner)")
    sys.exit("run path to be completed after the freeze and the code review")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
