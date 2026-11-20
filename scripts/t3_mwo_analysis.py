"""T3 on the MWO magnetic catalogue: statistical analysis (delivery 2 of docs/PROTOCOL_T3_MWO.md, §3, §6-§9).

Stages, in the frozen order (each refuses to run before the previous one is preserved in Git):

  --design-check  identifiability of beta3 and reduced full-rank matrix X_r (§3), true values of the ramp effects
                  Delta-beta_e (§7) and margin C of S2 on the subset with a white-light tilt available (§6); reads
                  DESIGN.csv and the DPD spot rows only for availability (no tilt of any kind is computed).
  --validate      P2f generator on the MWO design, procedure M, criteria of §7 (15 deg individual noise decides;
                  25 deg reported without criterion); reads DESIGN.csv only.
  --stability     opens the seal (only after the validation is preserved in Git): white-light tilts from sDPD,
                  S1-S4 of §6 and the rule on beta3.
  --estimate      beta3 once (main model) and the sensitivities of §3, after the stability outputs are preserved.

    .venv/bin/python scripts/t3_mwo_analysis.py --selftest
    .venv/bin/python scripts/t3_mwo_analysis.py --design-check --protocol-sha <SHA> --amendment-sha <SHA>
    (then --validate, --stability, --estimate with the same arguments)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2d, p2f_pilot as P, p2f_validation as V  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_T3_MWO.md"
AMENDMENT = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A1.md"
CAT = ROOT / "results/T3_MWO_CATALOGUE_R2"
SDPD = ROOT / "data/sharp/external_sDPD_20261118"
GDPD = ROOT / "data/sharp/external_DPD_20261118"
OUT_CHECK = ROOT / "results/T3_MWO_DESIGN_CHECK"
OUT_VAL = ROOT / "results/T3_MWO_VALIDATION"
OUT_STAB = ROOT / "results/T3_MWO_STABILITY"
OUT_EST = ROOT / "results/T3_MWO_ESTIMATE"

GAMMA0, SD_E, SD_X = V.GAMMA0, V.SD_E, V.SD_X          # 24 deg, 15 deg, 7.5 deg (P2f)
SD_E_SENS = 25.0
EPOCHS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")
SCEN, EFF_SCEN, EFFECTS = (0, 1, 2, 7, 9), (1, 2, 7, 9), (0.1, 0.2)
N0, N1, NS = 10_000, 2000, 2000
LIM_FALSE, LIM_SIDE, LIM_ERR, LIM_COV, LIM_TAIL = 0.030, 0.0175, 0.01, 0.965, 0.020
N_PROC = 5
SEED_BASE, SEED_S1 = 60_000_000, 69_000_001
USED = [tuple(r) for r in P.USED] + [(3_000_000, 5_001_000), (6_000_000, 9_002_000), (20_000_000, 20_001_000),
                                     (28_000_000, 28_400_000), (29_500_000, 29_500_011), (31_000_000, 33_200_000),
                                     (34_000_000, 34_240_000), (34_900_000, 34_901_000), (40_000_000, 43_600_000)]
MIN_EPOCH_HEM, MAX_UNVERIFIABLE = 50, 0.20
S1_THRESHOLD, S1_BLOCK, S1_REPS, S1_MAX_SINGULAR = 0.1 * GAMMA0, 6, 2000, 0.05
SUBSET_LIMIT = 0.70
MINIMA = (("1976-03-01", 21), ("1986-09-01", 22), ("1996-08-01", 23), ("2008-12-01", 24))


# ---------------------------------------------------------------- design, columns, identifiability (§3)

def load_design(set_name="isolated", cat=CAT):
    d = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    d = d[d.record_set == set_name].reset_index(drop=True)
    for c in ("sinlat", "phi_mwo", "A_main", "CR", "cycle"):
        if not np.isfinite(d[c].to_numpy(float)).all():
            raise ValueError(f"non-finite {c} in the design")
    return d


def reference_epochs(d):
    """Per hemisphere, the epoch with the most records (ties: the earliest)."""
    ref = {}
    for h in ("N", "S"):
        cnt = d[d.hemisphere == h].epoch.value_counts()
        ref[h] = min(cnt.index, key=lambda e: (-cnt[e], EPOCHS.index(e)))
    return ref


def columns(d, act="A_main", form="joy"):
    """Ordered candidate columns Z (cycle x hemisphere intercepts times sin|lat|, then epoch x hemisphere shifts in time
    order, N before S) and the target column x3 = (A - 1) sin|lat|. form: 'joy' (shifts times sin|lat|), 'additive'
    (constant shifts) or 'none' (no epoch terms)."""
    s, cyc, hem, ep = d.sinlat.to_numpy(), d.cycle.to_numpy(), d.hemisphere.to_numpy(), d.epoch.to_numpy()
    names, cols = [], []
    for c in sorted(set(cyc)):
        for h in ("N", "S"):
            m = (cyc == c) & (hem == h)
            if m.any():
                names.append(f"k_{c}{h}")
                cols.append(s * m)
    if form != "none":
        ref = reference_epochs(d)
        for e in EPOCHS:
            for h in ("N", "S"):
                m = (ep == e) & (hem == h)
                if m.any() and e != ref[h]:
                    names.append(f"{'d' if form == 'joy' else 'b'}_{e}{h}")
                    cols.append((s if form == "joy" else 1.0) * m)
    Z = np.column_stack(cols) if cols else np.zeros((len(d), 0))
    return names, Z, (d[act].to_numpy(float) - 1.0) * s


def reduce(names, Z, x3, w):
    """Identifiability of beta3 and removal of redundant columns of Z in their fixed order (§3)."""
    sw = np.sqrt(w)[:, None]
    rk = lambda M: int(np.linalg.matrix_rank(M * sw)) if M.shape[1] else 0          # noqa: E731
    rz = rk(Z)
    ident = rk(np.column_stack([Z, x3])) == rz + 1
    keep, dropped, cur = [], [], np.zeros((len(x3), 0))
    for j, n in enumerate(names):
        trial = np.column_stack([cur, Z[:, j]])
        if not np.any(Z[:, j] != 0):
            dropped.append(dict(column=n, reason="empty"))
        elif rk(trial) > cur.shape[1]:
            keep.append(j)
            cur = trial
        else:
            dropped.append(dict(column=n, reason="redundant"))
    Xr = np.column_stack([Z[:, keep], x3])
    cond = float(np.linalg.cond(Xr * sw)) if ident else float("inf")
    return dict(identifiable=bool(ident), rank_Z=rz, kept=[names[j] for j in keep], dropped=dropped, cond=cond), Xr


def g_row(Xr, w):
    return p2d.wls_row(Xr, w, Xr.shape[1] - 1)


def cell_codes(d):
    return P.cell_keys(d.CR.to_numpy().astype(int), d.hemisphere.to_numpy())


def ramp(d, e, act="A_main"):
    """Ramp effect of §7 on gamma: -e gamma0 clip((Abar_cell - q5)/(q95 - q5), 0, 1) sin|lat| (quantiles over records)."""
    abar = d.groupby(["CR", "hemisphere"])[act].transform("mean").to_numpy()
    q5, q95 = np.quantile(abar, [0.05, 0.95])
    return -e * GAMMA0 * np.clip((abar - q5) / (q95 - q5), 0.0, 1.0) * d.sinlat.to_numpy(), (float(q5), float(q95))


def analytic_se(d, Xr, w, scen=1):
    """SE of beta3 under the P2f generator (individual 15 deg, temporal 7.5 deg, AR(1) of the scenario)."""
    g = g_row(Xr, w)
    codes, uniq = cell_codes(d)
    b = np.bincount(codes, weights=g)
    cr = np.array([c for c, _ in uniq])
    hh = (np.array([h for _, h in uniq]) == "S").astype(int)
    spec = V.SCENARIOS[scen]
    K = P.ar1_k(cr - cr.min(), hh, spec.get("phi", 0.0), spec.get("kappa", 0.0)) if spec["kind"] == "ar1" else np.eye(len(b))
    return math.sqrt(SD_X ** 2 * float(b @ K @ b) + SD_E ** 2 * float(np.sum(g ** 2)))


# ---------------------------------------------------------------- white-light tilts from sDPD (§5)

def dpd_group_times(gdpd=GDPD, years=range(1974, 2013)):
    """(day, NOAA) -> timestamp string 'YYYY MM DD HH MM SS' of the group row kept by the catalogue (largest area,
    first row in file order on ties)."""
    best = {}
    for y in years:
        p = Path(gdpd) / f"gDPD{y}.txt"
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if not line.startswith("g "):
                continue
            try:
                lat, lon, lcm, area = float(line[59:65]), float(line[66:72]), float(line[73:79]), int(line[53:58])
            except ValueError:
                continue
            if max(lat, lon, lcm) > 900:
                continue
            k = (f"{line[2:6]}-{line[7:9]}-{line[10:12]}", line[22:28].strip())
            if k not in best or area > best[k][0]:
                best[k] = (area, line[2:21])
    return {k: v[1] for k, v in best.items()}


def spot_rows(wanted, sdpd=SDPD):
    """{(timestamp string, NOAA): [(lat, lon, corrected WS area), ...]} for the wanted keys."""
    years = sorted({int(t[:4]) for t, _ in wanted})
    out = {}
    for y in years:
        for line in (Path(sdpd) / f"sDPD{y}.txt").read_text().splitlines():
            if not line.startswith("s "):
                continue
            k = (line[2:21], line[22:29].strip())
            if k not in wanted:
                continue
            try:
                lat, lon, area = float(line[59:65]), float(line[66:72]), int(line[53:58])
            except ValueError:
                continue
            if lat > 900 or lon > 900:
                continue
            out.setdefault(k, []).append((lat, lon, area))
    return out


def wl_tilt(spots):
    """Bozza DPD §3: area weights (negative or zero corrected WS area -> weight 0), area-weighted centroid, head = spots
    west of the centroid, alpha = atan2(lat_head - lat_tail, (L_head - L_tail) cos(lat_bar)), Joy variable
    gamma = -sign(lat_bar) alpha. Returns (gamma, status)."""
    if spots is None or len(spots) < 2:
        return np.nan, "wl_fewer_than_two_spots"
    lat = np.array([s[0] for s in spots])
    lon = np.array([s[1] for s in spots])
    w = np.array([max(s[2], 0) for s in spots], float)
    if w.sum() <= 0:
        return np.nan, "wl_no_positive_area"
    ref = lon[np.argmax(w)]
    rel = (lon - ref + 180.0) % 360.0 - 180.0
    lc, latc = ref + np.sum(w * rel) / w.sum(), np.sum(w * lat) / w.sum()
    rel_c = (lon - lc + 180.0) % 360.0 - 180.0
    head, tail = (rel_c > 0) & (w > 0), (rel_c <= 0) & (w > 0)
    if not head.any() or not tail.any():
        return np.nan, "wl_one_side_empty"
    lh, lt = np.sum(w[head] * lat[head]) / w[head].sum(), np.sum(w[tail] * lat[tail]) / w[tail].sum()
    Lh, Lt = np.sum(w[head] * rel_c[head]) / w[head].sum(), np.sum(w[tail] * rel_c[tail]) / w[tail].sum()
    alpha = math.degrees(math.atan2(lh - lt, (Lh - Lt) * math.cos(math.radians(latc))))
    return -math.copysign(1.0, latc) * alpha, "ok"


def wl_for_records(d, gdpd=GDPD, sdpd=SDPD, tilt=True):
    """Per design record: white-light availability (always) and gamma_WL (only if tilt=True, i.e. after the seal)."""
    times = dpd_group_times(gdpd)
    keys = [(times.get((r.day, r.noaa)), r.noaa) for r in d.itertuples()]
    rows = spot_rows({k for k in keys if k[0]}, sdpd)
    gam, st = [], []
    for k in keys:
        g, s_ = wl_tilt(rows.get(k)) if k[0] else (np.nan, "wl_no_group_row")
        gam.append(g if tilt else np.nan)
        st.append(s_)
    return np.array(gam), np.array(st)


def axial(x):
    return (np.asarray(x) + 90.0) % 180.0 - 90.0


# ---------------------------------------------------------------- validation (§7): generator and one catalogue

def configs():
    c = [dict(role="main", scenario=s, sd_e=SD_E, effect=0.0, n=N0) for s in SCEN]
    c += [dict(role="main", scenario=s, sd_e=SD_E, effect=e, n=N1) for s in EFF_SCEN for e in EFFECTS]
    c += [dict(role="sensitivity", scenario=s, sd_e=SD_E_SENS, effect=0.0, n=NS) for s in SCEN]
    for i, x in enumerate(c):
        x["cfg"] = i
    return c


def seed(cfg, k):
    return SEED_BASE + 100_000 * cfg + k


def grid_seeds():
    return [seed(c["cfg"], k) for c in configs() for k in range(c["n"])]


def seeds_ok():
    s = grid_seeds()
    return (len(set(s)) == len(s) and not any(lo <= x < hi for x in s for lo, hi in USED)
            and SEED_S1 not in set(s) and not any(lo <= SEED_S1 < hi for lo, hi in USED))


def generate(d, scen, rng, sd_e, delta):
    """P2f responses on the MWO design: gamma0 sin|lat| + ramp + individual noise + temporal cell component."""
    spec = V.SCENARIOS[scen]
    lo = int(d.CR.min())
    G = int(d.CR.max()) - lo + 1
    x = V.gen_x(spec, G, rng)[d.CR.astype(int).to_numpy() - lo, (d.hemisphere == "S").to_numpy().astype(int)]
    n = len(d)
    e = rng.standard_t(4, n) / math.sqrt(2.0) if spec.get("t4") else rng.standard_normal(n)
    phi = d.phi_mwo.to_numpy()
    c = (phi / np.median(phi)) ** -0.25 if spec.get("hetero") else np.ones(n)
    return GAMMA0 * d.sinlat.to_numpy() + delta + sd_e * c * e + spec.get("x_scale", 1.0) * SD_X * x


def m_unit(d, Xr, w, g, y, codes, uniq):
    coef = P.wls(Xr, w, y)
    return dict(test="T3", y=y, w=w, Xf=Xr, a_row=g, beta=float(g @ y), r=y - Xr @ coef, codes=codes, uniq=uniq,
                phi=w, n_check=(len(y), len(uniq)))


def m_verdict(u, truth):
    try:
        r = V.procedure_m(u)
    except V.CandidateError as exc:
        return dict(verdict="errore", error=str(exc))
    return dict(beta=r["beta"], se=r["se"], lo=r["lo"], hi=r["hi"],
                verdict="supportato" if r["hi"] < 0 else ("opposto" if r["lo"] > 0 else "non deciso"),
                covered=int(r["lo"] <= truth <= r["hi"]), lo_above=int(r["lo"] > truth), hi_below=int(r["hi"] < truth))


_W = {}


def _init(cat=None):
    d = load_design(cat=cat or CAT)
    names, Z, x3 = columns(d)
    w = d.phi_mwo.to_numpy(float)
    info, Xr = reduce(names, Z, x3, w)
    g = g_row(Xr, w)
    codes, uniq = cell_codes(d)
    deltas = {e: ramp(d, e)[0] for e in EFFECTS}
    _W.update(d=d, Xr=Xr, w=w, g=g, codes=codes, uniq=uniq, deltas=deltas,
              truth={e: float(g @ deltas[e]) for e in EFFECTS})


def unit(task):
    cfg, k = task
    c = configs()[cfg]
    rng = np.random.default_rng(seed(cfg, k))
    delta = _W["deltas"][c["effect"]] if c["effect"] else 0.0
    truth = _W["truth"][c["effect"]] if c["effect"] else 0.0
    y = generate(_W["d"], c["scenario"], rng, c["sd_e"], delta)
    out = m_verdict(m_unit(_W["d"], _W["Xr"], _W["w"], _W["g"], y, _W["codes"], _W["uniq"]), truth)
    return dict(cfg=cfg, k=k, seed=seed(cfg, k), truth=truth, **{x: c[x] for x in ("role", "scenario", "sd_e", "effect")},
                **out)


def summarise(raw):
    rows, problems = [], []
    expected = {c["cfg"]: c for c in configs()}
    if raw.duplicated(["cfg", "k"]).any() or raw.seed.duplicated().any():
        problems.append("duplicated rows or seeds")
    if set(raw.cfg) - set(expected):
        problems.append("unexpected configurations")
    for cfg, c in expected.items():
        g = raw[raw.cfg == cfg]
        n = len(g)
        complete = bool(n == c["n"] and sorted(g.k) == list(range(c["n"])) and (g.seed == seed(cfg, g.k)).all()
                        and all((g[x] == c[x]).all() for x in ("scenario", "sd_e", "effect")))
        if not complete:
            problems.append(f"configuration {cfg} incomplete ({n}/{c['n']})")
        err = int((g.verdict == "errore").sum())
        sup, opp = int((g.verdict == "supportato").sum()), int((g.verdict == "opposto").sum())
        good = g[g.verdict != "errore"]
        r = dict(c, n_rows=n, complete=complete, errors=err, frac_errors=err / c["n"], supportato=sup / c["n"],
                 opposto=opp / c["n"], false_total=(sup + opp) / c["n"] if c["effect"] == 0 else np.nan,
                 coverage=float(good.covered.sum()) / c["n"], exclusion_tail=float(good.lo_above.sum()) / c["n"],
                 power=sup / c["n"] if c["effect"] else np.nan)
        if c["effect"] == 0:
            r["criteria_ok"] = bool(complete and r["false_total"] <= LIM_FALSE and r["supportato"] <= LIM_SIDE
                                    and r["opposto"] <= LIM_SIDE and r["frac_errors"] <= LIM_ERR)
        else:
            r["criteria_ok"] = bool(complete and r["coverage"] >= LIM_COV and r["exclusion_tail"] <= LIM_TAIL)
        rows.append(r)
    tab = pd.DataFrame(rows)
    accepted = bool(not problems and tab[tab.role == "main"].criteria_ok.all())
    return tab, accepted, problems


# ---------------------------------------------------------------- S1-S4 (§6)

def epoch_verifiable(d_full):
    cnt = d_full.groupby(["epoch", "hemisphere"]).size()
    return {(e, h): int(cnt.get((e, h), 0)) >= MIN_EPOCH_HEM for e in EPOCHS for h in ("N", "S")}


def s1_fit(sub):
    """a_{e,h} (Joy-coefficient difference) and b_{e,h} (additive) for every present (epoch, hemisphere)."""
    keys = sorted({(e, h) for e, h in zip(sub.epoch, sub.hemisphere)}, key=lambda k: (EPOCHS.index(k[0]), k[1]))
    s = sub.sinlat.to_numpy()
    cols = []
    for e, h in keys:
        m = ((sub.epoch == e) & (sub.hemisphere == h)).to_numpy()
        cols += [s * m, 1.0 * m]
    X = np.column_stack(cols)
    w = sub.phi_mwo.to_numpy(float)
    if np.linalg.matrix_rank(X * np.sqrt(w)[:, None]) < X.shape[1]:
        return None
    coef = np.linalg.lstsq(X * np.sqrt(w)[:, None], sub.d_wl.to_numpy() * np.sqrt(w), rcond=None)[0]
    return {k: (coef[2 * i], coef[2 * i + 1]) for i, k in enumerate(keys)}


def s1_differences(fit, sub, verif):
    """a_{e,h} - abar_h over verifiable (e,h), abar_h weighted by the sum of Phi of each epoch."""
    out = {}
    for h in ("N", "S"):
        ks = [k for k in fit if k[1] == h and verif.get(k)]
        if not ks:
            continue
        wts = np.array([sub.phi_mwo[(sub.epoch == e) & (sub.hemisphere == h)].sum() for e, _ in ks])
        abar = float(np.sum(wts * np.array([fit[k][0] for k in ks])) / wts.sum())
        out.update({k: fit[k][0] - abar for k in ks})
    return out


def s1(sub, verif, reps=S1_REPS, rng_seed=SEED_S1):
    fit = s1_fit(sub)
    if fit is None:
        return dict(status="non determinato", reason="singular fit"), pd.DataFrame()
    diff = s1_differences(fit, sub, verif)
    rng = np.random.default_rng(rng_seed)
    blocks = {}
    for e in EPOCHS:
        se = sub[sub.epoch == e]
        if len(se):
            first = int(se.CR.min())
            b = ((se.CR.astype(int) - first) // S1_BLOCK).to_numpy()
            blocks[e] = [se.index[b == j] for j in np.unique(b)]
    boot, singular = {k: [] for k in diff}, 0
    for _ in range(reps):
        idx = np.concatenate([np.concatenate([bl[i] for i in rng.integers(0, len(bl), len(bl))]) for bl in blocks.values()])
        f = s1_fit(sub.loc[idx].reset_index(drop=True))
        if f is None or any(k not in f for k in diff):
            singular += 1
            continue
        dd = s1_differences(f, sub.loc[idx].reset_index(drop=True), verif)
        for k in diff:
            boot[k].append(dd.get(k, np.nan))
    rows = []
    for k, v in diff.items():
        arr = np.array(boot[k])
        lo, hi = np.nanquantile(arr, [0.025, 0.975]) if len(arr) else (np.nan, np.nan)
        rows.append(dict(epoch=k[0], hemisphere=k[1], a=fit[k][0], b=fit[k][1], diff=v, lo=lo, hi=hi,
                         flag=bool((lo > 0 or hi < 0) and abs(v) > S1_THRESHOLD)))
    tab = pd.DataFrame(rows)
    if singular > S1_MAX_SINGULAR * reps:
        status = "non determinato"
    elif len(tab) and tab.flag.any():
        status = "instabile"
    else:
        status = "stabile fra epoche"
    return dict(status=status, singular=singular, reps=reps, seed=rng_seed), tab


def s2_outcome(lo, hi, C):
    """Precedence of §6: contained (also when distinguishable from zero), else activity-dependent, else undetermined."""
    if -C <= lo and hi <= C:
        return "scarto contenuto", bool(lo > 0 or hi < 0)
    if lo > 0 or hi < 0:
        return "dipendente dall'attività", True
    return "stabilità non determinata", False


def final_rule(s1_status, s2_status, unverifiable_share, validation_ok, identifiable, coverage_ok):
    if not coverage_ok:
        return "non concludente", "copertura del §2 non raggiunta"
    if not identifiable:
        return "non concludente", "beta3 non identificabile"
    reasons = []
    if not validation_ok:
        reasons.append("validazione a 15 gradi non superata")
    if s1_status != "stabile fra epoche":
        reasons.append(f"S1 {s1_status}")
    if s2_status != "scarto contenuto":
        reasons.append(f"S2 {s2_status}")
    if unverifiable_share > MAX_UNVERIFIABLE:
        reasons.append(f"epoche non verificabili {unverifiable_share:.1%} > 20 %")
    return ("descrittivo", "; ".join(reasons)) if reasons else ("verdetto", "")


def verdict_of(lo, hi):
    return "supportato" if hi < 0 else ("opposto" if lo > 0 else "non deciso")


# ---------------------------------------------------------------- gates and stages

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def committed(path):
    """True if the directory exists, all its files are tracked and unchanged in Git."""
    p = Path(path)
    if not p.exists():
        return False
    files = [f for f in p.rglob("*") if f.is_file()]
    tracked = set(git("ls-files", str(p.relative_to(ROOT))).splitlines())
    return bool(files) and all(str(f.relative_to(ROOT)) in tracked for f in files) and \
        not git("status", "--porcelain", str(p.relative_to(ROOT)))


def gate_problem(protocol_sha, amendment_sha, stage, root_paths=None):
    rp = root_paths or {}
    for f, sha, name in ((rp.get("protocol", PROTOCOL), protocol_sha, "protocol"),
                         (rp.get("amendment", AMENDMENT), amendment_sha, "amendment A1")):
        if not Path(f).exists() or hashlib.sha256(Path(f).read_bytes()).hexdigest() != sha:
            return f"frozen {name} missing or SHA-256 differs"
    if git("status", "--porcelain", "--untracked-files=no"):
        return "clean tree required"
    need = {"design-check": [rp.get("cat", CAT)], "validate": [rp.get("cat", CAT), rp.get("check", OUT_CHECK)],
            "stability": [rp.get("cat", CAT), rp.get("check", OUT_CHECK), rp.get("val", OUT_VAL)],
            "estimate": [rp.get("cat", CAT), rp.get("check", OUT_CHECK), rp.get("val", OUT_VAL),
                         rp.get("stab", OUT_STAB)]}[stage]
    for p in need:
        if not committed(p):
            return f"{Path(p).name} not preserved in Git: stage '{stage}' refused (frozen order)"
    return None


def read_sealed(cat=CAT, val=OUT_VAL):
    """The only reader of SEALED.csv.gz: refuses unless the validation is preserved in Git (§7 seal)."""
    if not committed(val):
        raise PermissionError("seal: the validation is not preserved in Git")
    return pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})


def write_out(out, frames, meta):
    tmp = Path(out).with_name(Path(out).name + f".partial_{os.getpid()}")
    tmp.mkdir(parents=True)
    for name, obj in frames.items():
        if isinstance(obj, pd.DataFrame):
            obj.to_csv(tmp / name, index=False)
        else:
            (tmp / name).write_text(json.dumps(obj, indent=2, default=str) + "\n")
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(tmp.iterdir())}
    os.rename(tmp, out)
    (Path(out) / "META.json").write_text(json.dumps(dict(meta, products_sha256=hashes, git_commit=git("rev-parse", "HEAD"),
                                                         script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                                                    indent=2, default=str) + "\n")


def design_check(protocol_sha, amendment_sha):
    why = gate_problem(protocol_sha, amendment_sha, "design-check")
    if why:
        sys.exit(why)
    if OUT_CHECK.exists():
        sys.exit("design check exists")
    cov = json.loads((CAT / "COVERAGE.json").read_text())
    d = load_design()
    w = d.phi_mwo.to_numpy(float)
    out = {}
    for form in ("joy", "additive", "none"):
        names, Z, x3 = columns(d, form=form)
        info, Xr = reduce(names, Z, x3, w)
        out[form] = dict(info, n=len(d), se_analytic_scen1=analytic_se(d, Xr, w) if info["identifiable"] else None)
    names, Z, x3 = columns(d)
    info, Xr = reduce(names, Z, x3, w)
    targets = {}
    if info["identifiable"]:
        g = g_row(Xr, w)
        for e in EFFECTS:
            delta, q = ramp(d, e)
            targets[f"delta_beta_{int(e * 100)}"] = float(g @ delta)
        targets.update(q5=q[0], q95=q[1])
    _, st = wl_for_records(d, tilt=False)          # availability only: no white-light tilt is kept
    sub = d[st == "ok"].reset_index(drop=True)
    names_s, Zs, x3s = columns(sub)
    info_s, Xrs = reduce(names_s, Zs, x3s, sub.phi_mwo.to_numpy(float))
    C = None
    if info_s["identifiable"]:
        C = 0.5 * abs(float(g_row(Xrs, sub.phi_mwo.to_numpy(float)) @ ramp(sub, 0.2)[0]))
    avail = pd.DataFrame(dict(noaa=d.noaa, wl_status=st))
    cover = dict(n_design=len(d), n_with_wl=int(len(sub)), share=len(sub) / len(d) if len(d) else 0.0,
                 below_70=bool(len(sub) < SUBSET_LIMIT * len(d)), wl_status=pd.Series(st).value_counts().to_dict(),
                 losses_by=wl_losses(d, st))
    write_out(OUT_CHECK, {"IDENTIFIABILITY.json": out, "TARGETS.json": dict(targets, C=C, subset_identifiable=info_s),
                          "WL_AVAILABILITY.csv": avail, "WL_COVERAGE.json": cover},
              dict(protocol_sha256=protocol_sha, amendment_a1_sha256=amendment_sha, coverage=cov))
    print(json.dumps(dict(identifiable=info["identifiable"], dropped=info["dropped"], targets=targets, C=C,
                          wl_share=cover["share"]), indent=2, default=str))
    return 0


def wl_losses(d, st):
    d = d.assign(has=(st == "ok"))
    q = np.quantile(d.A_main, [1 / 3, 2 / 3])
    d["A_tercile"] = np.searchsorted(q, d.A_main, side="right") + 1
    return {dim: d.groupby(dim).has.agg(["size", "mean"]).reset_index().to_dict("records")
            for dim in ("cycle", "epoch", "hemisphere", "A_tercile")}


def benchmark(n=40):
    _init()
    t0 = time.time()
    tk = [(c["cfg"], k) for c in configs()[:1] for k in range(n)]
    with Pool(N_PROC, initializer=_init) as pool:
        t1 = time.time()
        list(pool.imap_unordered(unit, tk * N_PROC, chunksize=2))
        dt = time.time() - t1
    total = len(grid_seeds())
    hours = total * dt / (n * N_PROC) / 3600
    print(f"benchmark: start-up {t1 - t0:.0f} s; {n * N_PROC} units in {dt:.0f} s on {N_PROC} processes; "
          f"predicted {hours:.2f} h for {total} units (no duration limit)", flush=True)
    return hours


def validate(protocol_sha, amendment_sha):
    why = gate_problem(protocol_sha, amendment_sha, "validate")
    if why:
        sys.exit(why)
    if OUT_VAL.exists():
        sys.exit("validation output exists")
    if not (selftest() and seeds_ok()):
        return 1
    start = git("rev-parse", "HEAD")
    hours = benchmark()
    t0, rows = time.time(), []
    tk = [(c["cfg"], k) for c in configs() for k in range(c["n"])]
    with Pool(N_PROC, initializer=_init) as pool:
        for i, r in enumerate(pool.imap_unordered(unit, tk, chunksize=16)):
            rows.append(r)
            if (i + 1) % 5000 == 0:
                print(f"{i + 1}/{len(tk)} units, {(time.time() - t0) / 3600:.2f} h", flush=True)
    raw = pd.DataFrame(rows).sort_values(["cfg", "k"])
    tab, accepted, problems = summarise(raw)
    write_out(OUT_VAL, {"RAW.csv.gz": raw, "SUMMARY.csv": tab,
                        "ACCEPTANCE.json": dict(accepted_15deg=accepted, problems=problems)},
              dict(protocol_sha256=protocol_sha, amendment_a1_sha256=amendment_sha, start_commit=start,
                   predicted_hours=hours, hours=(time.time() - t0) / 3600, truth=_W.get("truth")))
    print(tab.to_string(index=False))
    print("accepted (15 deg):", accepted, problems)
    return 0


def stability(protocol_sha, amendment_sha):
    why = gate_problem(protocol_sha, amendment_sha, "stability")
    if why:
        sys.exit(why)
    if OUT_STAB.exists():
        sys.exit("stability output exists")
    sealed = read_sealed()
    d = load_design()
    sx = sealed[sealed.record_set == "isolated"].set_index("noaa")
    d["gamma_mwo"] = sx.loc[d.noaa, "gamma_deg"].to_numpy()
    d["lead"] = sx.loc[d.noaa, "leading_sign"].to_numpy()
    d["hale"] = sx.loc[d.noaa, "hale_expected"].to_numpy()
    gwl, st = wl_for_records(d)
    d["gamma_wl"], d["wl_status"] = gwl, st
    d["d_wl"] = axial(d.gamma_mwo - d.gamma_wl)
    sub = d[d.wl_status == "ok"].reset_index(drop=True)
    verif = epoch_verifiable(d)
    unver = float(np.mean([not verif[(e, h)] for e, h in zip(d.epoch, d.hemisphere)]))
    s1_res, s1_tab = s1(sub, verif)
    names, Z, x3 = columns(sub)
    w = sub.phi_mwo.to_numpy(float)
    info, Xr = reduce(names, Z, x3, w)
    targets = json.loads((OUT_CHECK / "TARGETS.json").read_text())
    C = targets["C"]
    codes, uniq = cell_codes(sub)
    r2 = m_verdict(m_unit(sub, Xr, w, g_row(Xr, w), sub.d_wl.to_numpy(), codes, uniq), 0.0)
    s2_status, s2_nonzero = s2_outcome(r2["lo"], r2["hi"], C) if r2["verdict"] != "errore" else ("stabilità non determinata", False)
    s2_hem = {}
    for h in ("N", "S"):
        sh = sub[sub.hemisphere == h].reset_index(drop=True)
        n_, Z_, x_ = columns(sh)
        i_, X_ = reduce(n_, Z_, x_, sh.phi_mwo.to_numpy(float))
        if i_["identifiable"]:
            c_, u_ = cell_codes(sh)
            s2_hem[h] = m_verdict(m_unit(sh, X_, sh.phi_mwo.to_numpy(float), g_row(X_, sh.phi_mwo.to_numpy(float)),
                                         sh.d_wl.to_numpy(), c_, u_), 0.0)
    s3 = d.assign(agree=(d.lead == d.hale)).groupby(["epoch", "hemisphere"]).agree.agg(["size", "mean"]).reset_index()
    val = json.loads((OUT_VAL / "ACCEPTANCE.json").read_text())
    cov = json.loads((CAT / "COVERAGE.json").read_text())
    idf = json.loads((OUT_CHECK / "IDENTIFIABILITY.json").read_text())["joy"]["identifiable"]
    rule = final_rule(s1_res["status"], s2_status, unver, val["accepted_15deg"], idf, cov["outcome"] == "informativo")
    s4 = s4_table(d)
    res = dict(S1=s1_res, S2=dict(r2, C=C, status=s2_status, distinguishable_from_zero=s2_nonzero, by_hemisphere=s2_hem),
               unverifiable_share=unver, verifiable=[f"{e}{h}" for (e, h), v in verif.items() if v],
               subset=dict(n=len(sub), share=len(sub) / len(d)), rule=dict(outcome=rule[0], reasons=rule[1]))
    write_out(OUT_STAB, {"STABILITY.json": res, "S1_TABLE.csv": s1_tab, "S3_HALE.csv": s3, "S4.csv": s4,
                         "WL_TILTS.csv": d[["noaa", "day", "epoch", "hemisphere", "wl_status", "gamma_wl", "d_wl"]]},
              dict(protocol_sha256=protocol_sha, amendment_a1_sha256=amendment_sha))
    print(json.dumps(dict(S1=s1_res["status"], S2=s2_status, rule=rule), indent=2))
    return 0


def s4_table(d):
    q = np.quantile(d.A_main, [1 / 3, 2 / 3])
    t = d.assign(A_tercile=np.searchsorted(q, d.A_main, side="right") + 1)
    return t.groupby("A_tercile").agg(n=("noaa", "size"), mean_rank=("rank", "mean"), mean_abs_lcm=("abs_lcm", "mean"),
                                      mean_neighbours_day=("n_neighbours", "mean")).reset_index()


SENSITIVITIES = (("additive epoch terms", dict(form="additive")), ("no epoch terms", dict(form="none")),
                 ("weights = DPD area", dict(weights="dpd_area")), ("all records", dict(set_name="all")),
                 ("R1 only", dict(filt="R1")), ("first candidate day only", dict(filt="rank1")),
                 ("before 2010-05", dict(filt="pre_hmi")), ("excluding +-1 yr from minima", dict(filt="minima")),
                 ("activity (a) Gyula/Debrecen", dict(act="A_own")), ("activity (b) SILSO hemispheric", dict(act="A_silso_hem")),
                 ("activity (c) SILSO split", dict(act="A_silso_split")))


def fit_beta3(d, form="joy", weights="phi_mwo", act="A_main"):
    d = d[np.isfinite(d[act])].reset_index(drop=True)
    w = d[weights].to_numpy(float)
    names, Z, x3 = columns(d, act=act, form=form)
    info, Xr = reduce(names, Z, x3, w)
    if not info["identifiable"]:
        return dict(n=len(d), identifiable=False)
    codes, uniq = cell_codes(d)
    r = m_verdict(m_unit(d, Xr, w, g_row(Xr, w), d.gamma_mwo.to_numpy(), codes, uniq), 0.0)
    return dict(n=len(d), identifiable=True, **{k: r.get(k) for k in ("beta", "se", "lo", "hi", "verdict", "error")})


def filtered(d, filt):
    if filt == "R1":
        return d[d.res_class == "R1"]
    if filt == "rank1":
        return d[d["rank"] == 1]
    if filt == "pre_hmi":
        return d[d.day < "2010-05-01"]
    if filt == "minima":
        t = pd.to_datetime(d.day)
        far = np.ones(len(d), bool)
        for m, _ in MINIMA:
            far &= (t - pd.Timestamp(m)).abs() > pd.Timedelta(days=365)
        return d[far]
    return d


def estimate(protocol_sha, amendment_sha):
    why = gate_problem(protocol_sha, amendment_sha, "estimate")
    if why:
        sys.exit(why)
    if OUT_EST.exists():
        sys.exit("estimate exists")
    sealed = read_sealed()
    rows = []
    for name, opt in (("main", {}),) + SENSITIVITIES:
        d = load_design(opt.get("set_name", "isolated"))
        sx = sealed[sealed.record_set == opt.get("set_name", "isolated")].set_index("noaa")
        d["gamma_mwo"] = sx.loc[d.noaa, "gamma_deg"].to_numpy()
        d = filtered(d, opt.get("filt")).reset_index(drop=True)
        rows.append(dict(analysis=name, **fit_beta3(d, opt.get("form", "joy"), opt.get("weights", "phi_mwo"),
                                                    opt.get("act", "A_main"))))
    tab = pd.DataFrame(rows)
    stab = json.loads((OUT_STAB / "STABILITY.json").read_text())
    main = tab.iloc[0]
    outcome = stab["rule"]["outcome"]
    final = dict(outcome=outcome, reasons=stab["rule"]["reasons"], beta3=main.beta, se=main.se, lo=main.lo, hi=main.hi,
                 verdict=verdict_of(main.lo, main.hi) if outcome == "verdetto" else None,
                 targets=json.loads((OUT_CHECK / "TARGETS.json").read_text()))
    write_out(OUT_EST, {"ESTIMATE.csv": tab, "FINAL.json": final},
              dict(protocol_sha256=protocol_sha, amendment_a1_sha256=amendment_sha))
    print(tab.to_string(index=False))
    print(json.dumps(final, indent=2, default=str))
    return 0


# ---------------------------------------------------------------- selftest (synthetic data only)

def synthetic_design(n_per=60, seed_=7):
    rng = np.random.default_rng(seed_)
    rows = []
    cr0 = 1610
    for i, (ep, cyc) in enumerate((("E2", 21), ("E3", 21), ("E4", 22), ("E5", 22), ("E8", 23), ("E8", 24))):
        for j in range(n_per):
            for h in ("N", "S"):
                cr = cr0 + 40 * i + j % 40
                lat = rng.uniform(5, 35) * (1 if h == "N" else -1)
                rows.append(dict(record_set="isolated", noaa=f"{i}{j}{h}", day=f"{1976 + 6 * i}-0{1 + j % 9}-15",
                                 CR=cr, hemisphere=h, sinlat=math.sin(math.radians(abs(lat))), lat_bar=lat,
                                 phi_mwo=float(rng.lognormal(48, 1)), dpd_area=float(rng.integers(20, 500)),
                                 A_main=float(rng.lognormal(0, 0.5)), A_own=1.0, A_silso_hem=np.nan,
                                 A_silso_split=1.0, cycle=cyc, epoch=ep, res_class="R1", rank=1, abs_lcm=5.0,
                                 n_neighbours=0))
    return pd.DataFrame(rows)


def selftest():
    import tempfile
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    ok("seeds: grid unique, outside every registered range, S1 seed 69000001 not in the grid",
       seeds_ok() and SEED_S1 not in set(grid_seeds()) and len(grid_seeds()) == 76_000, len(grid_seeds()))
    d = synthetic_design()
    w = d.phi_mwo.to_numpy()
    names, Z, x3 = columns(d)
    info, Xr = reduce(names, Z, x3, w)
    # in the synthetic design cycle 21 = epochs E2 + E3 and cycle 22 = E4 + E5: one epoch column per pair is redundant
    red = [x["column"] for x in info["dropped"]]
    ok("identifiable synthetic design; reference epoch E8 excluded; the true redundancies (one epoch per cycle pair) dropped",
       info["identifiable"] and not any(n.startswith("d_E8") for n in names)
       and red == ["d_E3N", "d_E3S", "d_E5N", "d_E5S"], red)
    # a redundant column (duplicate of an existing direction) is dropped; beta3 unchanged
    Z2 = np.column_stack([Z, Z[:, 0] + Z[:, 1]])
    info2, Xr2 = reduce(names + ["dup"], Z2, x3, w)
    y = 24 * d.sinlat.to_numpy() + np.random.default_rng(1).normal(0, 15, len(d))
    b1, b2 = float(g_row(Xr, w) @ y), float(g_row(Xr2, w) @ y)
    pinv_b = float((np.linalg.pinv(np.column_stack([Z2, x3]) * np.sqrt(w)[:, None]) @ (y * np.sqrt(w)))[-1])
    ok("redundant column removed in fixed order; beta3 = minimum-norm solution of the full matrix",
       info2["dropped"][-1] == dict(column="dup", reason="redundant") and abs(b1 - b2) < 1e-9 and abs(b1 - pinv_b) < 1e-8,
       (round(b1, 6), round(pinv_b, 6)))
    # non-identifiable: x3 in the span of Z
    info3, _ = reduce(names, Z, Z[:, 0] * 2.0 + Z[:, 3], w)
    ok("beta3 not identifiable when x3 lies in the span of the other columns", not info3["identifiable"])
    ok("empty columns reported as empty", reduce(["e"] + names, np.column_stack([np.zeros(len(d)), Z]), x3, w)[0]["dropped"][0]
       == dict(column="e", reason="empty"))
    for form in ("additive", "none"):
        nf, Zf, _ = columns(d, form=form)
        ok(f"form '{form}': epoch columns {'constant' if form == 'additive' else 'absent'}",
           (form == "none" and not any(n.startswith(("d_", "b_")) for n in nf))
           or (form == "additive" and any(n.startswith("b_") for n in nf)
               and set(np.unique(Zf[:, nf.index(next(n for n in nf if n.startswith('b_')))])) <= {0.0, 1.0}))
    delta, q = ramp(d, 0.2)
    g = g_row(Xr, w)
    t20, t10 = float(g @ delta), float(g @ ramp(d, 0.1)[0])
    ok("ramp target: projection on the full reduced matrix, linear in e, negative", t20 < 0 and abs(t20 - 2 * t10) < 1e-9,
       round(t20, 4))
    # validation unit on synthetic design: mean estimate close to the target under the effect
    _W.update(d=d, Xr=Xr, w=w, g=g, codes=cell_codes(d)[0], uniq=cell_codes(d)[1],
              deltas={e: ramp(d, e)[0] for e in EFFECTS}, truth={e: float(g @ ramp(d, e)[0]) for e in EFFECTS})
    cfg_eff = next(c["cfg"] for c in configs() if c["effect"] == 0.2 and c["scenario"] == 1)
    est = [unit((cfg_eff, k)) for k in range(60)]
    mb = np.mean([e["beta"] for e in est if e["verdict"] != "errore"])
    ok("generator + procedure M: mean estimate under the 20 % ramp near the projected target (60 catalogues)",
       abs(mb - t20) < 4 * np.std([e["beta"] for e in est]) / math.sqrt(len(est)) + 0.05, (round(mb, 3), round(t20, 3)))
    u0 = unit((0, 0))
    ok("null unit: truth 0, a verdict or 'errore'", u0["truth"] == 0.0 and u0["verdict"] in ("supportato", "opposto", "non deciso", "errore"))
    raw = pd.DataFrame([dict(cfg=c["cfg"], k=k, seed=seed(c["cfg"], k), role=c["role"], scenario=c["scenario"],
                             sd_e=c["sd_e"], effect=c["effect"], verdict="non deciso", covered=1, lo_above=0, hi_below=0)
                        for c in configs() for k in range(c["n"])])
    tab, acc, pr = summarise(raw)
    ok("summary: complete clean grid accepted", acc and not pr)
    raw2 = raw.copy()
    raw2.loc[raw2.cfg == 0, "verdict"] = np.where(np.arange((raw2.cfg == 0).sum()) < 200, "supportato", "non deciso")
    ok("summary: one side at 2 % in a null scenario refused", not summarise(raw2)[1])
    ok("summary: a missing catalogue refused", not summarise(raw.iloc[1:])[1])
    raw3 = raw.copy()
    raw3.loc[raw3.cfg == configs()[-1]["cfg"], "verdict"] = "supportato"
    ok("summary: 25 deg sensitivity does not decide acceptance", summarise(raw3)[1])
    # white-light tilt
    north = [(10.5, 100.0 + 3, 300), (11.5, 100.0 - 3, 200), (11.0, 100.0 - 2.5, -1)]
    gN, sN = wl_tilt(north)
    ok("white-light tilt: head closer to the equator in the north gives positive Joy variable", sN == "ok" and gN > 0, round(gN, 2))
    south = [(-10.5, 359.0 + 2, 300), (-11.5, 359.0 - 2, 200)]
    gS, _ = wl_tilt(south)
    ok("white-light tilt: south, head closer to the equator, positive; across 0/360", gS > 0, round(gS, 2))
    ok("white-light tilt: one side empty or single spot refused", wl_tilt([(10, 100, 50)])[1] == "wl_fewer_than_two_spots"
       and wl_tilt([(10, 100, 50), (11, 100.2, 0)])[1] in ("wl_one_side_empty", "ok"))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "gDPD1980.txt").write_text("g 1980 05 01 09 00 60   2400          10   200    10   400  10.00 100.00   5.00 100.00 0.1000\n")
        (td / "sDPD1980.txt").write_text(
            "s 1980 05 01 09 00 60   2400     1     5   100     5   300  10.50 103.00   8.00 100.00 0.1000\n"
            "s 1980 05 01 09 00 60   2400     2     5   100     5   200  11.50  97.00   2.00 100.00 0.1000\n")
        dd = pd.DataFrame([dict(day="1980-05-01", noaa="2400")])
        g_, st_ = wl_for_records(dd, gdpd=td, sdpd=td)
        g0, st0 = wl_for_records(dd, gdpd=td, sdpd=td, tilt=False)
    ok("records -> spot rows of the kept group row (seconds = 60), tilt only when allowed", st_[0] == "ok" and g_[0] > 0
       and st0[0] == "ok" and np.isnan(g0[0]))
    ok("axial difference in (-90, 90]", np.allclose(axial([100.0, -100.0, 30.0]), [-80.0, 80.0, 30.0]))
    # S1 on synthetic differences: stable without a step, unstable with a 6 deg Joy step in one epoch
    sub = d.copy()
    rng = np.random.default_rng(3)
    sub["d_wl"] = rng.normal(0, 0.5, len(sub))
    verif = epoch_verifiable(sub)
    r_st, t_st = s1(sub, verif, reps=200)
    sub2 = sub.copy()
    m = (sub2.epoch == "E4").to_numpy()
    sub2.loc[m, "d_wl"] += 8.0 * sub2.sinlat[m] / sub2.sinlat[m].mean()
    r_in, _ = s1(sub2, verif, reps=200)
    ok("S1: stable without a step, unstable with a Joy-coefficient step in one epoch", r_st["status"] == "stabile fra epoche"
       and r_in["status"] == "instabile", (r_st["status"], r_in["status"]))
    ok("S1: bootstrap seed fixed (same table twice)", s1(sub, verif, reps=50)[1].equals(s1(sub, verif, reps=50)[1]))
    ok("S2 precedence: contained (also non-zero), activity-dependent, undetermined",
       s2_outcome(0.1, 0.4, 0.5) == ("scarto contenuto", True) and s2_outcome(-0.2, 0.3, 0.5) == ("scarto contenuto", False)
       and s2_outcome(0.2, 0.9, 0.5) == ("dipendente dall'attività", True)
       and s2_outcome(-0.9, 0.3, 0.5) == ("stabilità non determinata", False))
    ok("final rule: verdict only when everything passes; 'non determinato' S1 and >20 % unverifiable block the verdict",
       final_rule("stabile fra epoche", "scarto contenuto", 0.1, True, True, True) == ("verdetto", "")
       and final_rule("non determinato", "scarto contenuto", 0.1, True, True, True)[0] == "descrittivo"
       and final_rule("stabile fra epoche", "scarto contenuto", 0.25, True, True, True)[0] == "descrittivo"
       and final_rule("stabile fra epoche", "scarto contenuto", 0.1, True, False, True)[0] == "non concludente"
       and final_rule("stabile fra epoche", "scarto contenuto", 0.1, True, True, False)[0] == "non concludente")
    with tempfile.TemporaryDirectory() as td:
        try:
            read_sealed(cat=td, val=Path(td) / "no_validation")
            ok("seal: SEALED cannot be read before the validation is preserved", False)
        except PermissionError:
            ok("seal: SEALED cannot be read before the validation is preserved", True)
    src = Path(__file__).read_text()
    body = src.split("def selftest():")[0]
    opens = body.count('"SEALED.csv.gz"')
    ok("seal: SEALED.csv.gz is opened only inside read_sealed()", opens == 1
       and body.index('"SEALED.csv.gz"') > body.index("def read_sealed") > body.rfind("def ", 0, body.index('"SEALED.csv.gz"')) - 1)
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for f in ("selftest", "design-check", "validate", "stability", "estimate"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--protocol-sha")
    ap.add_argument("--amendment-sha")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    for flag, fn in (("design_check", design_check), ("validate", validate), ("stability", stability),
                     ("estimate", estimate)):
        if getattr(a, flag):
            if not (a.protocol_sha and a.amendment_sha):
                sys.exit("--protocol-sha and --amendment-sha required")
            return fn(a.protocol_sha, a.amendment_sha)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
