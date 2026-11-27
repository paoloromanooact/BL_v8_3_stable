"""SFT map-bipole pilot (point 2), runner of the frozen protocol docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md (rev. 4).

Receipt docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_FREEZE.json (protocol SHA 380b7982...). Core numerics: python/sharpbl/sft_core.py.
Amendment A1 (numerical; draft docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_DRAFT.md) must be frozen before --run.
Not run on observed maps before the Codex code review; --selftest uses a synthetic catalogue and synthetic CEA patches.

Steps (protocol section in brackets)
1. Gate: protocol text and receipt pinned, receipt inputs (exact set) unchanged, amendment A1 frozen with the SHA of
   sft_core.py, clean tree, script equal to HEAD, new output dir.
2. Population and draw [§3]: primary records (role primary/both), valid_bl = 1, family_rank = 0; strata "un NOAA"
   (NOAA_NUM = 1) / "altro/ignoto" (flag NOAA_NUM = 0) x USFLUX terciles (numpy linear quantiles; 1 if x <= q1, 2 if
   q1 < x <= q2, 3 otherwise; records without finite USFLUX counted and left out) x |LAT_FWT| bands (<10, 10-20, >=20);
   canonical order HARPNUM, permutation default_rng(36_100_000) of the whole population, first 4 per cell; pi = n/N,
   weights N/n.
3. Map M [§4]: P1 mask (finite, |Br| <= 10000 G, bitmap >= 33, |Br| >= 100 G); polarities rescaled to phibar; linear
   deposit in s; out of the centre support -> status deposition_out_of_range. 300 G sensitivity: everything recomputed
   from the 300 G mask for M and for the point bipole.
4. Bipole B [§5]: point bipole at the P1-style centroids (|Br|-weighted unit-vector means, renormalised) with +-phibar;
   Gaussian sensitivities (area-equivalent sigma, 2 deg, 4 deg): each component on its own 8-sigma cap (step sigma/10)
   for the deposit; effective fluxes and centroids of the summed field on a common cap around the midpoint
   (implementation choice, declared).
5. Transport [§6 as amended by A1]: SFT1D (N from the A1 preflight, hybrid advection, positivity-limited Crank-Nicolson), the four parameter sets of the
   2x2 grid (reference eta 466.8, Du 0.025, p 2.33); tau = 5 and 10 years as exp(-t/tau) factors on the reference.
6. Times [§7]: 0, 27 days, 0.5, 1, 3 Julian years; daily curves for the reference transport (M and point B, 100 G).
7. Products [§8]: SAMPLE.csv, CELLS.csv, REGIONS.csv, DIPOLES.csv.gz (long), CURVES.csv.gz, SUMMARY.csv (groups incl.
   the 18 cells), DENOMINATORS.csv, MANIFEST.csv (Br/bitmap/keys with SHA-256 and T_OBS), CONVERGENCE.csv, PREFLIGHT.csv,
   META.json. A region that raises inside the processing gets the status technical_error:<type>.
   Summaries weighted with N/n (lower weighted quantile: first sorted value whose cumulative normalised weight reaches q)
   and unweighted; ratio threshold 0.1 m(t), m(t) = weighted median of |D_M(t)| for M at 100 G with the reference
   transport, the same for every variant; if m(t) = 0 no ratio.
8. Convergence (A1 §2), a requirement: synthetic preflight before any map (N 400 -> 800 -> 1600, else technical stop);
   then the first 3 regions (permutation order) with M and point B deposited, four transports, 2N and halved step,
   criterion 1e-3 max(|D_fine|, CONV_FLOOR D_scale). A failure gives convergence_failed: products kept, run not valid
   (exit code 3).

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
from scipy.linalg import solve_banded

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo, measure, sft_core as C  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_FREEZE.json"
PIN = dict(protocol="380b79829fbac870479acc02797ef245623b689c09af9ff9f595ac5a81b61d38",
           receipt="a5f289876fef388b86be17e813e2c3d8578bdb170cb51392e7eb40a8a3f9f849")
CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
FITS = ROOT / "data/sharp/fits"
OUT = ROOT / "results/SFT_MAP_BIPOLE_PILOT"
SEED, PER_CELL = 36_100_000, 4
TIMES = (("0", 0.0), ("27d", 27 * C.DAY), ("0.5y", 0.5 * C.YEAR), ("1y", C.YEAR), ("3y", 3 * C.YEAR))
TAUS = ((5.0, "ref_tau5y"), (10.0, "ref_tau10y"))
TRANSPORTS = {f"eta{p['eta_km2s']:g}_du{p['du_kms']:g}": p for p in C.SENSITIVITY}
REF = f"eta{C.REFERENCE['eta_km2s']:g}_du{C.REFERENCE['du_kms']:g}"
THRESHOLDS = (100.0, 300.0)
A1 = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md"
A1_FREEZE = ROOT / "docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_FREEZE.json"
INPUTS_EXPECTED = frozenset({"results/P1/P1_SBL_CATALOG_BY_HARP.csv", "python/sharpbl/geometry.py", "python/sharpbl/measure.py",
                             "python/sharpbl/cycle.py", "docs/BL_SFT_HMI_INVENTORY.md"})
CONV_TOL, N_CHOICES = 1e-3, (400, 800, 1600)
RATIO_RES = 0.01             # A1 §2ter: maximum ratio difference between grid levels for a resolved ratio
LEVELS = (("N", "D"), ("2N", "D_2N"), ("4N", "D_4N"), ("dt_half", "D_dthalf"))
CONV_FLOOR = 1e-2           # A1 §2 (draft, to be decided by the review): floor of the criterion as a fraction of D_scale (parent: 1e-6)
CAT_COLS = ["HARPNUM", "T_REC", "role", "valid_bl", "family_rank", "NOAA_NUM", "USFLUX", "LAT_FWT", "d_axial_g", "d_axial_bal_g",
            "d_cm", "tilt_deg", "phi_pos_mx", "phi_neg_mx"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- gate

def gate():
    """Provenance before any map is read (Codex review aaf3d6f §4): parent protocol and its receipt pinned, exact input
    set with current hashes, frozen amendment A1 present with its receipt, and the transport code equal to the SHA
    recorded in the A1 receipt."""
    probs = []
    fz = json.loads(FREEZE.read_text())
    if not (sha(PROTOCOL) == fz.get("sha256") == PIN["protocol"]):
        probs.append("protocol text and receipt")
    if sha(FREEZE) != PIN["receipt"]:
        probs.append("freeze receipt file differs from the pinned one")
    ins = fz.get("inputs_sha256")
    if not (isinstance(ins, dict) and set(ins) == INPUTS_EXPECTED and all(sha(ROOT / p) == h for p, h in ins.items())):
        probs.append("inputs of the freeze receipt: exact set and current hashes")
    if not (A1.exists() and A1_FREEZE.exists()):
        probs.append("amendment A1 not frozen")
    else:
        a1 = json.loads(A1_FREEZE.read_text())
        if not (sha(A1) == a1.get("sha256") and a1.get("parent_sha256") == PIN["protocol"]
                and a1.get("sft_core_sha256") == sha(ROOT / "python/sharpbl/sft_core.py")):
            probs.append("amendment A1 text, parent or transport code")
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
    reps["M"] = (cf, "ok" if cf is not None else "deposition_out_of_range", dict(n_out=nout), (ing["s_pix"], ing["F_bal"]))
    sp, fp = C.point_bipole(ing["lat_pos"], ing["lat_neg"], ing["phibar"])
    cf, nout = C.deposit_linear(sp, fp, model.s)
    reps["B_point"] = (cf, "ok" if cf is not None else "deposition_out_of_range", dict(n_out=nout), (sp, fp))
    if threshold == THRESHOLDS[0]:
        r = ing["r_cm"]
        sig_area = (math.degrees(math.sqrt(ing["area_pos"] / (2 * math.pi * r * r))), math.degrees(math.sqrt(ing["area_neg"] / (2 * math.pi * r * r))))
        for name, (sp_, sn_) in (("B_gauss_area", sig_area), ("B_gauss_2deg", (2.0, 2.0)), ("B_gauss_4deg", (4.0, 4.0))):
            # deposit: one 8-sigma cap per component (protocol §5); effective quantities of the summed field on the common
            # cap around the midpoint (implementation choice: the protocol requires them but does not fix their grid)
            lp_, fp_ = C.gaussian_component_cells((ing["lon_pos"], ing["lat_pos"]), sp_, ing["phibar"], r_cm=r)
            ln_, fn_ = C.gaussian_component_cells((ing["lon_neg"], ing["lat_neg"]), sn_, -ing["phibar"], r_cm=r)
            src = (np.sin(np.radians(np.r_[lp_, ln_])), np.r_[fp_, fn_])
            cf, nout = C.deposit_linear(*src, model.s)
            e = C.gaussian_bipole((ing["lon_pos"], ing["lat_pos"]), (ing["lon_neg"], ing["lat_neg"]), sp_, sn_, ing["phibar"], r_cm=r)["effective"]
            reps[name] = (cf, "ok" if cf is not None else "deposition_out_of_range",
                          dict(n_out=nout, sigma_pos=sp_, sigma_neg=sn_, eff_phi_pos=e["phi_pos"], eff_phi_neg=e["phi_neg"],
                               eff_lon_pos=e["lon_pos"], eff_lat_pos=e["lat_pos"], eff_lon_neg=e["lon_neg"], eff_lat_neg=e["lat_neg"]), src)
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
    try:
        return _region(base, row, br, bm, h, models, curve_times)
    except Exception as exc:                                  # recorded, never a silent disappearance or a crash of the run
        return [dict(base, threshold=t, status=f"technical_error:{type(exc).__name__}") for t in THRESHOLDS], [], []


def _region(base, row, br, bm, h, models, curve_times):
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
        for name, (cf, st, extra, src) in reps.items():
            reg.update({f"{name}_status": st, **{f"{name}_{k}": v for k, v in extra.items()}})
            if cf is None:
                continue
            n = models[REF].n
            for tname, mdl in models.items():
                b0 = mdl.profile(cf)
                outs = mdl.evolve(b0, [t for _, t in TIMES])
                lev = level_dipoles(src, n, tname)
                rows = [dict(HARPNUM=row["HARPNUM"], threshold=thr, representation=name, transport=tname, time=tl, t_s=ts,
                             D=mdl.dipole(b), **{c: lev[k][j] for k, c in LEVELS[1:]})
                        for j, ((tl, ts), b) in enumerate(zip(TIMES, outs))]
                dips += rows
                if tname == REF:
                    for tau_y, lab in TAUS:
                        for r in rows:
                            f = float(C.decay_factor(r["t_s"], tau_y * C.YEAR))
                            dips.append(dict(r, transport=lab, **{c: r[c] * f for _, c in LEVELS}))
                    if thr == THRESHOLDS[0] and name in ("M", "B_point") and curve_times is not None:
                        for ts, b in zip(curve_times, mdl.evolve(b0, curve_times)):
                            curves.append(dict(HARPNUM=row["HARPNUM"], representation=name, t_day=ts / C.DAY, D=mdl.dipole(b)))
        regions.append(reg)
    return regions, dips, curves


# ---------------------------------------------------------------- grid levels for the ratio resolution (A1 §2ter)

_ADJ, _GRIDS = {}, {}


def _adjoint_step(m, dt):
    """Transpose of one Crank-Nicolson step S = (I - hL)^-1 (I + hL): S^T g = (I + hL)^T (I - hL)^-T g."""
    h = 0.5 * dt
    ab = np.zeros((3, m.n))
    ab[0, 1:] = -h * m.lo[1:]                     # (A^T)[j, j+1] = A[j+1, j]
    ab[1] = 1.0 - h * m.di
    ab[2, :-1] = -h * m.up[:-1]                   # (A^T)[j+1, j] = A[j, j+1]

    def step(g):
        x = solve_banded((1, 1), ab, g)
        out = x + h * m.di * x
        out[1:] += h * m.up[:-1] * x[:-1]
        out[:-1] += h * m.lo[1:] * x[1:]
        return out
    return step


def adjoint_weights(n, transport, half=False):
    """Rows g_j with D(t_j) = g_j . b0 for the exact step sequence of SFT1D.evolve at TIMES (same step rule, counts
    and remainders), obtained by applying the transposed steps backwards to the dipole weights 1.5 s ds."""
    key = (n, transport, half)
    if key not in _ADJ:
        m = C.SFT1D(n=n, **TRANSPORTS[transport])
        dt = min(C.DAY, m.dt_max)                     # the step SFT1D.evolve uses at this N
        if half:
            dt = 0.5 * dt                             # halved step: half of the effective step (A1 §2)
        plan, t = [], 0.0
        for _, target in TIMES:
            k = int(np.floor((target - t) / dt * (1 + 1e-12)))
            rem = target - (t + k * dt)
            plan.append((k, rem if rem > 1e-9 * dt else 0.0))
            t = target
        full = _adjoint_step(m, dt)
        G = []
        for j in range(len(TIMES)):
            g = 1.5 * m.s * m.ds
            for k, rem in reversed(plan[:j + 1]):
                if rem:
                    g = _adjoint_step(m, rem)(g)
                for _ in range(k):
                    g = full(g)
            G.append(g)
        _ADJ[key] = np.array(G)
    return _ADJ[key]


def grid(n):
    if n not in _GRIDS:
        _GRIDS[n] = C.SFT1D(n=n)
    return _GRIDS[n]


def level_dipoles(src, n, transport):
    """D at TIMES on 2N, 4N and N with the halved step, from the deposit inputs (s, flux) of a representation;
    NaN where the deposit is out of the support (it cannot fail on a finer grid if it succeeded on N)."""
    out = {}
    for lab, nn, half in (("2N", 2 * n, False), ("4N", 4 * n, False), ("dt_half", n, True)):
        g = grid(nn)
        cf, _ = C.deposit_linear(src[0], src[1], g.s)
        out[lab] = adjoint_weights(nn, transport, half) @ g.profile(cf) if cf is not None else np.full(len(TIMES), np.nan)
    return out


# ---------------------------------------------------------------- summaries (§8)

def wquantile(x, w, q):
    """Lower weighted quantile: first sorted value whose cumulative normalised weight reaches q."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    if len(x) == 0:
        return np.nan
    o = np.argsort(x, kind="mergesort")
    cw = np.cumsum(w[o]) / w.sum()
    return float(x[o][np.searchsorted(cw, q - 1e-12)])


RATIO_COLS = ["HARPNUM", "threshold", "representation", "transport", "time"]


def ratio_table(regions, dips):
    """Per row (B representation, threshold, transport, time): dipoles of B and M on the four grid levels, the ratio
    threshold 0.1 m(t) recomputed on each level (same population: M at 100 G, reference transport, weights N/n),
    eligibility, ratios, ratio status, dD/D_scale numerical indicator and the sign status (A1 §2ter)."""
    reg = regions[["HARPNUM", "threshold", "D_scale", "weight", "multiplicity", "flux_class", "lat_band"]]
    d = dips.merge(reg, on=["HARPNUM", "threshold"], how="left")
    mcols = [c for _, c in LEVELS]
    M = d[d.representation == "M"][RATIO_COLS[:2] + RATIO_COLS[3:] + mcols].rename(columns={c: c + "_M" for c in mcols})
    B = d[d.representation != "M"].merge(M, on=["HARPNUM", "threshold", "transport", "time"], how="inner")
    ref_m = d[(d.representation == "M") & (d.threshold == THRESHOLDS[0]) & (d.transport == REF)]
    for lev, c in LEVELS:
        thr = {t: 0.1 * wquantile(g[c].abs(), g.weight, 0.5) for t, g in ref_m.groupby("time")}
        B[f"thr_{lev}"] = B.time.map(thr)
        B[f"elig_{lev}"] = (B[f"thr_{lev}"] > 0) & (B[c + "_M"].abs() >= B[f"thr_{lev}"])
        B[f"r_{lev}"] = (B[c] - B[c + "_M"]) / B[c + "_M"].abs()
    finite = np.isfinite(B[[c for _, c in LEVELS] + [c + "_M" for _, c in LEVELS]].to_numpy(float)).all(axis=1)
    el = B[[f"elig_{lev}" for lev, _ in LEVELS]].to_numpy(bool)
    diffs = np.column_stack([(B.r_2N - B.r_N).abs(), (B.r_4N - B.r_2N).abs(), (B.r_dt_half - B.r_N).abs()])
    B["dr_max"] = np.where(el.all(axis=1), diffs.max(axis=1), np.nan)
    B["ratio_status"] = np.where(~finite, "ratio_unresolved", np.where(~el.any(axis=1), "below_ratio_threshold",
                                 np.where(el.all(axis=1) & (diffs <= RATIO_RES).all(axis=1), "ratio_resolved", "ratio_unresolved")))
    B["ratio"] = np.where(B.ratio_status == "ratio_resolved", B.r_N, np.nan)
    B["dD"] = B.D - B.D_M
    B["dD_scaled"] = B.dD / B.D_scale
    B["dD_numdiff"] = np.max(np.column_stack([((B[c] - B[c + "_M"]) - B.dD).abs() for _, c in LEVELS[1:]]), axis=1) / B.D_scale
    sb = np.sign(B[[c for _, c in LEVELS]].to_numpy(float))
    sm = np.sign(B[[c + "_M" for _, c in LEVELS]].to_numpy(float))
    B["sign_resolved"] = finite & (sb == sb[:, :1]).all(axis=1) & (sm == sm[:, :1]).all(axis=1) & (sb[:, 0] != 0) & (sm[:, 0] != 0)
    B["same_sign"] = np.sign(B.D) == np.sign(B.D_M)
    B["cell"] = B.multiplicity + "|" + B.flux_class.astype(int).astype(str) + "|" + B.lat_band
    return B


def summarise(regions, dips):
    B = ratio_table(regions, dips)
    rows = []
    groups = [("all", None)] + [(c, c) for c in ("multiplicity", "flux_class", "lat_band", "cell")]
    for (rep, thr, tr, tm), g in B.groupby(["representation", "threshold", "transport", "time"], sort=True):
        for gname, col in groups:
            parts = [("all", g)] if col is None else [(f"{col}={v}", x) for v, x in g.groupby(col)]
            for label, x in parts:
                w = x.weight.to_numpy(float)
                res = (x.ratio_status == "ratio_resolved").to_numpy()
                r = dict(representation=rep, threshold=thr, transport=tr, time=tm, group=label, n=len(x),
                         n_below_ratio_threshold=int((x.ratio_status == "below_ratio_threshold").sum()),
                         n_ratio_unresolved=int((x.ratio_status == "ratio_unresolved").sum()), n_ratio_resolved=int(res.sum()),
                         ratio_threshold=float(x.thr_N.iloc[0]))
                for st in ("below_ratio_threshold", "ratio_unresolved", "ratio_resolved"):
                    r[f"w_share_{st}"] = float((w * (x.ratio_status == st).to_numpy()).sum() / w.sum())
                for key, vals, ww in (("dD_scaled", x.dD_scaled, w), ("abs_dD", x.dD.abs(), w), ("ratio", x.ratio[res], w[res])):
                    for q, lab in ((0.1, "q10"), (0.5, "median"), (0.9, "q90")):
                        r[f"{key}_{lab}_w"] = wquantile(vals, ww, q)
                    r[f"{key}_median_unw"] = float(np.median(vals)) if len(vals) else np.nan
                r["dD_numdiff_median_w"] = wquantile(x.dD_numdiff, w, 0.5)
                r["dD_numdiff_max"] = float(x.dD_numdiff.max())
                if tm == "3y":
                    sr = x.sign_resolved.to_numpy(bool)
                    same, ws = x.same_sign.to_numpy(bool)[sr], w[sr]
                    r["n_sign_unresolved"] = int((~sr).sum())
                    r["same_sign_w"] = float((ws * same).sum() / ws.sum()) if sr.any() else np.nan
                    r["same_sign_unw"] = float(same.mean()) if sr.any() else np.nan
                rows.append(r)
    keep = RATIO_COLS + [c for _, c in LEVELS] + [c + "_M" for _, c in LEVELS] + \
        [f"{p}_{lev}" for lev, _ in LEVELS for p in ("thr", "elig", "r")] + ["dr_max", "ratio_status", "dD_numdiff", "sign_resolved"]
    return pd.DataFrame(rows), B[keep].sort_values(RATIO_COLS).reset_index(drop=True)


PREFLIGHT_CENTRES = (5.0, 15.0, 30.0, 60.0)


_PROFILE_CACHE = {}


def preflight_profiles(model):
    if model.n not in _PROFILE_CACHE:
        _PROFILE_CACHE[model.n] = _preflight_profiles(model)
    return _PROFILE_CACHE[model.n]


def _preflight_profiles(model):
    """Synthetic cases of A1 §2.1 at each centre: point bipole (separation 2 deg, tilt 10 deg, following negative north),
    Gaussian bipoles sigma 2 and 4 deg, an impulse; returns name -> (cell flux, D_scale, single-polarity flag)."""
    out = {}
    for c in PREFLIGHT_CENTRES:
        dl = math.sin(math.radians(10.0))
        lp, ln = c - dl, c + dl
        out[f"point_{c:g}"] = (C.deposit_linear(*C.point_bipole(lp, ln, 1e22), model.s)[0], 3e22 / (4 * math.pi * C.RSUN_CM ** 2), False)
        for sg in (2.0, 4.0):
            zp, fp = C.gaussian_component_cells((1.0, lp), sg, 1e22)
            zn, fn = C.gaussian_component_cells((-1.0, ln), sg, -1e22)
            out[f"gauss{sg:g}_{c:g}"] = (C.deposit_linear(np.sin(np.radians(np.r_[zp, zn])), np.r_[fp, fn], model.s)[0],
                                         3e22 / (4 * math.pi * C.RSUN_CM ** 2), False)
            out[f"gauss{sg:g}_pos_{c:g}"] = (C.deposit_linear(np.sin(np.radians(zp)), fp, model.s)[0], 3e22 / (4 * math.pi * C.RSUN_CM ** 2), True)
        imp = np.zeros(model.n)
        imp[int(np.argmin(np.abs(model.s - math.sin(math.radians(c)))))] = 1e22
        out[f"impulse_{c:g}"] = (imp, 3e22 / (4 * math.pi * C.RSUN_CM ** 2), True)
    return out


def refined_dipoles(cf_fn, n, half_step, transport):
    m = C.SFT1D(n=n, **transport)
    if half_step:
        m.dt_max = 0.5 * min(C.DAY, m.dt_max)          # half of the effective step min(1 day, dt_max) (A1 §2)
    cf = cf_fn(m)
    outs = m.evolve(m.profile(cf), [t for _, t in TIMES])
    return [m.dipole(b) for b in outs], outs


def preflight():
    """A1 §2.1-2.2: synthetic cases, four transports, all times, N -> 2N and half step; positivity and mass. Returns
    (chosen N or None, table)."""
    rows = []
    for n in N_CHOICES:
        base_model = C.SFT1D(n=n)
        cases = list(preflight_profiles(base_model))
        all_ok = True
        for tname, par in TRANSPORTS.items():
            for case in cases:
                def cf_for(m, case=case):
                    return preflight_profiles(m)[case][0]
                dsc, single = preflight_profiles(base_model)[case][1:]
                if cf_for(base_model) is None or cf_for(C.SFT1D(n=2 * n)) is None:
                    # a component cap reaching beyond the outermost cell centre (sigma 4 deg at 60 deg): recorded, outside
                    # the requirement, as the same status in the observed run (A1 §2.1)
                    rows.append(dict(N=n, transport=tname, case=case, refinement="deposit", time="all", criterion=np.nan, passes=np.nan,
                                     status="deposition_out_of_range"))
                    continue
                d0, outs0 = refined_dipoles(cf_for, n, False, par)
                prof0 = base_model.profile(cf_for(base_model))
                if single:
                    mx = float(np.max(np.abs(prof0)))
                    neg = min(float(o.min()) for o in outs0)
                    mass = max(abs(float(o.sum() - prof0.sum())) for o in outs0) / float(np.abs(prof0).sum())
                    good = neg >= -C.POS_TOL * mx and mass <= 1e-12
                    rows.append(dict(N=n, transport=tname, case=case, refinement="positivity", time="all", criterion=max(-neg / mx, mass), passes=good,
                                     status="ok"))
                    all_ok &= good
                    continue
                for ref, (nn, half) in (("N_double", (2 * n, False)), ("dt_half", (n, True))):
                    d1, _ = refined_dipoles(cf_for, nn, half, par)
                    for (tl, _), a, b in zip(TIMES, d0, d1):
                        c_ = abs(b - a) / max(abs(b), CONV_FLOOR * dsc)
                        rows.append(dict(N=n, transport=tname, case=case, refinement=ref, time=tl, D_ref=a, D_fine=b, D_scale=dsc, criterion=c_,
                                         passes=bool(c_ <= CONV_TOL), status="ok"))
                        all_ok &= c_ <= CONV_TOL
        if all_ok:
            return n, pd.DataFrame(rows)
    return None, pd.DataFrame(rows)


def convergence(regions, read_maps, n):
    """A1 §2.3: first three successful regions (permutation order) with M and B_point deposited; four transports; 2N and
    half step. Returns (table, numerical status)."""
    ok = regions[(regions.threshold == THRESHOLDS[0]) & (regions.status == "ok") & (regions.get("M_status") == "ok")
                 & (regions.get("B_point_status") == "ok")].sort_values("perm_rank").head(3)
    rows = []
    for _, row in ok.iterrows():
        br, bm, h = read_maps(row["HARPNUM"], row["T_REC"])
        ing = ingredients(br, bm, h, THRESHOLDS[0])
        for rep in ("M", "B_point"):
            def cf_for(m, rep=rep):
                return C.deposit_linear(ing["s_pix"], ing["F_bal"], m.s)[0] if rep == "M" else \
                    C.deposit_linear(*C.point_bipole(ing["lat_pos"], ing["lat_neg"], ing["phibar"]), m.s)[0]
            for tname, par in TRANSPORTS.items():
                d0, _ = refined_dipoles(cf_for, n, False, par)
                for ref, (nn, half) in (("N_double", (2 * n, False)), ("dt_half", (n, True))):
                    d1, _ = refined_dipoles(cf_for, nn, half, par)
                    for (tl, _), a, b in zip(TIMES, d0, d1):
                        c_ = abs(b - a) / max(abs(b), CONV_FLOOR * ing["D_scale"])
                        rows.append(dict(HARPNUM=row["HARPNUM"], representation=rep, transport=tname, refinement=ref, time=tl, D_ref=a, D_fine=b,
                                         criterion=c_, passes=bool(c_ <= CONV_TOL)))
    t = pd.DataFrame(rows, columns=["HARPNUM", "representation", "transport", "refinement", "time", "D_ref", "D_fine", "criterion", "passes"])
    if len(ok) == 0:
        return t, "no_usable_convergence_case"
    if not t.passes.all():
        return t, "convergence_failed"
    return t, ("ok" if len(ok) == 3 else f"ok_with_{len(ok)}_cases")


def denominators(sample, regions):
    reg = regions.copy()
    reg["cell"] = reg.multiplicity + "|" + reg.flux_class.astype(int).astype(str) + "|" + reg.lat_band
    rows = []
    for (cell, thr), g in reg.groupby(["cell", "threshold"]):
        r = dict(cell=cell, threshold=thr, selected=int(len(g)), region_ok=int((g.status == "ok").sum()))
        for st, k in g.status.value_counts().items():
            if st != "ok":
                r[f"failed_{st}"] = int(k)
        for rep in ("M", "B_point", "B_gauss_area", "B_gauss_2deg", "B_gauss_4deg"):
            col = f"{rep}_status"
            if col in g:
                r[f"{rep}_ok"] = int((g[col] == "ok").sum())
                r[f"{rep}_out_of_range"] = int((g[col] == "deposition_out_of_range").sum())
        rows.append(r)
    return pd.DataFrame(rows).fillna(0)


def manifest(sample, paths_fn):
    """Exact Br/bitmap/keys files of the sampled records with SHA-256 and T_OBS (recorded before processing)."""
    rows = []
    for _, r in sample.iterrows():
        for kind, p in zip(("Br", "bitmap", "keys"), paths_fn(r["HARPNUM"], r["T_REC"])):
            ok = Path(p).exists()
            t_obs = json.loads(Path(p).read_text()).get("T_OBS") if (ok and kind == "keys") else None
            rows.append(dict(HARPNUM=r["HARPNUM"], T_REC=r["T_REC"], kind=kind, path=str(p), exists=ok, sha256=sha(p) if ok else "",
                             T_OBS=t_obs))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- build and run

def fits_reader(base=FITS):
    def paths(harp, t_rec):
        folder, stem = record_dir(base, t_rec), file_stem(int(harp), t_rec)
        return folder / f"{stem}.Br.fits", folder / f"{stem}.bitmap.fits", folder / f"{stem}.keys.json"

    def read(harp, t_rec):
        pb, pm, _ = paths(harp, t_rec)
        br, h = geo.read_sharp(pb)
        bm, _ = geo.read_sharp(pm)
        return br, bm, h
    read.paths = paths
    return read


def build(cat, read_maps, curves=True, n_cells=None):
    """n_cells: grid size; None runs the A1 preflight to choose it (technical stop if no N passes)."""
    if n_cells is None:
        n_cells, pre = preflight()
        if n_cells is None:
            raise SystemExit("A1 preflight failed up to N = 1600: technical stop, no product")
    else:
        pre = pd.DataFrame()
    pop, info = population(cat)
    sample = draw(pop)
    man0 = manifest(sample, read_maps.paths)
    models = {k: C.SFT1D(n=n_cells, **p) for k, p in TRANSPORTS.items()}
    curve_times = [d * C.DAY for d in range(0, 1096)] + [3 * C.YEAR] if curves else None
    regs, dips, curv = [], [], []
    for _, row in sample.iterrows():
        a, b, c = run_region(row, read_maps, models, curve_times)
        regs += a
        dips += b
        curv += c
    regions, dipoles = pd.DataFrame(regs), pd.DataFrame(dips)
    summary, ratios = summarise(regions, dipoles)
    conv, num_status = convergence(regions, read_maps, n_cells)
    man1 = manifest(sample, read_maps.paths)
    manifest_ok = man0[["path", "exists", "sha256"]].equals(man1[["path", "exists", "sha256"]])
    cells = pop.groupby(["multiplicity", "flux_class", "lat_band"]).size().rename("N_cell").reset_index()
    valid = (num_status.startswith("ok")) and manifest_ok
    return dict(SAMPLE=sample, CELLS=cells, REGIONS=regions, DIPOLES=dipoles, CURVES=pd.DataFrame(curv, columns=["HARPNUM", "representation", "t_day", "D"]),
                SUMMARY=summary, RATIOS=ratios, CONVERGENCE=conv, PREFLIGHT=pre, MANIFEST=man0, DENOMINATORS=denominators(sample, regions)), \
        dict(info, population=len(pop), sample=len(sample), n_cells=n_cells, numerical_status=num_status, manifest_unchanged=manifest_ok,
             run_valid=bool(valid))


def run():
    probs = gate()
    if probs:
        sys.exit("gate: " + "; ".join(probs))
    cat = pd.read_csv(CATALOGUE, usecols=CAT_COLS, low_memory=False)
    prods, info = build(cat, fits_reader())
    tmp = Path(tempfile.mkdtemp(prefix=".SFT_MAP_BIPOLE_PILOT.tmp-", dir=OUT.parent))
    for k, v in prods.items():
        v.to_csv(tmp / (f"{k}.csv.gz" if k in ("DIPOLES", "CURVES", "RATIOS") else f"{k}.csv"), index=False)
    fz = json.loads(FREEZE.read_text())
    meta = dict(protocol_sha256=sha(PROTOCOL), freeze_receipt_sha256=sha(FREEZE), freeze_commit=fz["freeze_commit"],
                script_sha256=sha(__file__), sft_core_sha256=sha(ROOT / "python/sharpbl/sft_core.py"), catalogue_sha256=sha(CATALOGUE),
                git_head=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                seed=SEED, per_cell=PER_CELL, transports=TRANSPORTS, reference=REF, times=[list(t) for t in TIMES], **info)
    meta.update(a1_sha256=sha(A1), a1_freeze_receipt_sha256=sha(A1_FREEZE))
    meta["products_sha256"] = {f.name: sha(f) for f in sorted(tmp.iterdir())}
    (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    tmp.rename(OUT)
    print(f"written {OUT}; numerical status {info['numerical_status']}; manifest unchanged {info['manifest_unchanged']}; "
          f"run valid {info['run_valid']}")
    return 0 if info["run_valid"] else 3


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
        prods, info = build(cat, reader, curves=False, n_cells=800)
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
        Ra = prods["RATIOS"]
        b0 = np.random.default_rng(3).normal(size=800)
        m8 = C.SFT1D(n=800, **TRANSPORTS[REF])
        fwd = np.array([m8.dipole(b) for b in m8.evolve(b0, [t for _, t in TIMES])])
        ok("A1 §2ter: adjoint weights reproduce the forward step sequence (N 800, reference; 1e-10 relative)",
           np.max(np.abs(adjoint_weights(800, REF) @ b0 - fwd)) <= 1e-10 * np.max(np.abs(fwd)))
        tsum = Su.n_below_ratio_threshold + Su.n_ratio_unresolved + Su.n_ratio_resolved
        taus = Ra[Ra.transport.isin([lab for _, lab in TAUS])].merge(Ra[Ra.transport == REF], on=["HARPNUM", "threshold", "representation", "time"],
                                                                         suffixes=("", "_ref"))
        ok("A1 §2ter: every B row has a ratio status; counts add up to n; levels 2N/4N/dt_half present; tau rows keep the ratios",
           Ra.ratio_status.isin(["below_ratio_threshold", "ratio_unresolved", "ratio_resolved"]).all() and (tsum == Su.n).all()
           and Ra[["D_2N", "D_4N", "D_dthalf"]].notna().all().all() and np.allclose(taus.r_N, taus.r_N_ref, rtol=1e-12, equal_nan=True),
           f"statuses {Ra.ratio_status.value_counts().to_dict()}")
        cv = prods["CONVERGENCE"]
        ok("convergence (A1 §2.3): 3 regions x M/B_point x 4 transports x 2 refinements x all times; status ok and run valid",
           len(cv) == 3 * 2 * 4 * 2 * len(TIMES) and info["numerical_status"] == "ok" and info["run_valid"], f"max {cv.criterion.max():.1e}")
        dn = prods["DENOMINATORS"]
        ok("denominators per cell and threshold: selected = sample size; failures by cause; cell summaries present",
           all(int(dn[dn.threshold == t].selected.sum()) == len(S) for t in THRESHOLDS) and any(c.startswith("failed_") for c in dn.columns)
           and Su.group.str.startswith("cell=").any())
        mf = prods["MANIFEST"]
        ok("manifest: Br, bitmap and keys of every sampled record, with SHA-256; unchanged at the end", len(mf) == 3 * len(S)
           and mf.exists.all() and info["manifest_unchanged"])
        # a file altered after the start is detected
        p0 = Path(mf.path.iloc[0])
        before = manifest(S.head(1), reader.paths)
        p0.write_bytes(p0.read_bytes() + b"x")
        ok("manifest detects a map changed during the run", not before[["sha256"]].equals(manifest(S.head(1), reader.paths)[["sha256"]]))
        # convergence requirement failing -> run not valid
        global CONV_TOL
        saved = CONV_TOL
        CONV_TOL = 1e-15
        try:
            t_bad, st_bad = convergence(R, reader, 800)
        finally:
            CONV_TOL = saved
        ok("convergence criterion not met -> status convergence_failed (run not valid)", st_bad == "convergence_failed")
        # technical error inside a region is recorded, not a crash
        g_ing = globals()["ingredients"]
        globals()["ingredients"] = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthetic"))
        try:
            rr, _, _ = run_region(S.iloc[0], reader, {REF: C.SFT1D()}, None)
        finally:
            globals()["ingredients"] = g_ing
        ok("technical error in a region recorded as technical_error:<type>, the run continues",
           all(r["status"] == "technical_error:RuntimeError" for r in rr))
        npre, pre = preflight()
        po = pre[pre.status == "ok"]
        ok("A1 preflight on the actual code: N 400 fails on point bipoles, N 800 passes every synthetic case, transport, time; positivity and mass",
           npre == 800 and not po[po.N == 400].passes.astype(bool).all() and po[po.N == 800].passes.astype(bool).all() and set(pre.refinement) == {"N_double", "dt_half", "positivity", "deposit"}
           and set(pre[pre.status != "ok"].case) == {"gauss4_60", "gauss4_pos_60"},
           f"max criterion at N 800 {po[(po.N == 800) & po.refinement.isin(['N_double', 'dt_half'])].criterion.max():.1e}")
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit((0 if selftest() else 1) if a.selftest else run())
