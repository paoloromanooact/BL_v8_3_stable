"""T3 on the MWO magnetic catalogue 1974-2012: measurement runner (delivery 1 of docs/PROTOCOL_T3_MWO.md, §2-§4 and §7
'Ordine e sigillo'; amendment A1 on BLANK pixels).

Builds the candidate days of every DPD group (area >= 1, |lat| <= 45, same-UT-day Fe I magnetogram passing the ephemeris
checks, isolation), chooses the magnetogram of each candidate day (resolution class, then time from the DPD row, then
lowest TAVG-UT), measures every candidate day with the pilot measurement (window 6/8 deg, 50-4000 G, mu >= 0.8), and keeps
per group the first day in |LCM| order where the measurement succeeds. Two record sets: 'isolated' (main) and 'all'
(sensitivity, no isolation condition).

Outputs (results/T3_MWO_CATALOGUE/):
  DESIGN.csv        one row per record, no tilt and no polarity sign (read by the validation);
  SEALED.csv.gz     tilt, gamma, leading sign, centroids per record: NOT to be read before the validation is read;
  ATTEMPTS.csv.gz   every candidate day with its status (no tilt);
  MAGNETOGRAMS.csv.gz  header table of every Fe I magnetogram (epoch, resolution class, ephemeris check);
  LOSSES.csv, COVERAGE.json, META.json.

    .venv/bin/python scripts/t3_mwo_catalogue.py --selftest
    .venv/bin/python scripts/t3_mwo_catalogue.py --run --protocol-sha <SHA> --amendment-sha <SHA>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import cycle as cyc_mod  # noqa: E402
from sharpbl import geometry as geo  # noqa: E402

_spec = importlib.util.spec_from_file_location("mwo_pilot_tilt", ROOT / "scripts/mwo_pilot_tilt.py")
P = importlib.util.module_from_spec(_spec)
sys.modules["mwo_pilot_tilt"] = P
_spec.loader.exec_module(P)
MP = P.MP                                     # frozen MWO pipeline module (reader, dates, ephemeris functions)

PROTOCOL = ROOT / "docs/PROTOCOL_T3_MWO.md"
AMENDMENT = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A1.md"
AMENDMENT2 = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A2.md"
A2_LIST = ROOT / "docs/PROTOCOL_T3_MWO_AMENDMENT_A2_EXCLUDED_FITS.csv"   # 18 files with field x100, saturated
DPD_DIR = ROOT / "data/sharp/external_DPD_20261118"
SILSO_TOT = ROOT / "ancillary/SILSO_TOT/SN_m_tot_V2.0.txt"
SILSO_HEM = ROOT / "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv"
MWO_DATA = P.MWO_DATA
OUT = ROOT / "results/T3_MWO_CATALOGUE_R3"   # R1 (f718114): filename day; R2 (566122f): before amendment A2

START, END = pd.Timestamp("1974-01-01"), pd.Timestamp("2013-01-01")      # DPD dates, UT
ARCHIVE_YEARS = range(1974, 2014)                                          # 2013 archive may hold 2012-12-31 files
MINIMA = [(21, "1976-03-01"), (22, "1986-09-01"), (23, "1996-08-01"), (24, "2008-12-01")]
MAX_ABS_LAT, MIN_AREA = 45.0, 1
BLANK_FRAC_MAX = 0.05                                                      # amendment A1
MODERN_SPLIT = datetime(1996, 4, 10)                                       # PSEPMA jump between 1996-04-08 and 04-13
EPOCH_OF_MRKMOD = {0: "E1", 256: "E2", 1280: "E3", 1281: "E4", 1282: "E5", 1283: "E6"}
CLASS_RANK = {"R1": 0, "R2": 1, "R3": 2, "R0": 3}
COVERAGE_MIN, COVERAGE_CYCLE_HEM = 3000, 300
OWN_SOURCES = ("GYUL", "DEBR")


# ---------------------------------------------------------------- small rules (§2, §4)

def res_class(dx, dy):
    """Resolution class from both observing dimensions (§2), assigned in the order R1, R2, R3."""
    try:
        dx, dy = float(dx), float(dy)
    except (TypeError, ValueError):
        return "R0"
    if not (np.isfinite(dx) and np.isfinite(dy)):
        return "R0"
    if dx < 11 and dy < 15:
        return "R1"
    if 11 <= dx <= 14 and dy >= 18:
        return "R2"
    if dx >= 13.5 and 15 <= dy <= 19:
        return "R3"
    return "R0"


def epoch_of(member, h, day):
    """Epoch table of §4: MRKMOD for legacy files, date split for modern fe1 files."""
    base = Path(member).name.lower()
    if base.startswith("mp00_5250"):
        try:
            return EPOCH_OF_MRKMOD.get(int(float(h.get("MRKMOD"))), "unassigned")
        except (TypeError, ValueError):
            return "unassigned"
    if "fe1" in base:
        return "E7" if day < MODERN_SPLIT else "E8"
    return "unassigned"


def cycle_of(t):
    c = 20
    for k, m in MINIMA:
        if t >= pd.Timestamp(m):
            c = k
    return c


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------- DPD groups, candidate days, isolation

def dpd_groups(dpd_dir=DPD_DIR, years=range(1974, 2013)):
    """All DPD group rows with valid positions; duplicates of (date, NOAA) keep the largest corrected area."""
    rows = []
    for y in years:
        for line in (Path(dpd_dir) / f"gDPD{y}.txt").read_text().splitlines():
            if not line.startswith("g "):
                continue
            try:
                lat, lon, lcm, area = float(line[59:65]), float(line[66:72]), float(line[73:79]), int(line[53:58])
                # seconds = 60 occur in DPD (75 group rows 1974-2012): added as an interval, never dropped
                t = datetime(int(line[2:6]), int(line[7:9]), int(line[10:12]), int(line[13:15]), int(line[16:18])) \
                    + timedelta(seconds=int(line[19:21]))
            except ValueError:
                continue
            if lat > 900 or lon > 900 or lcm > 900:
                continue
            rows.append(dict(day=t.strftime("%Y-%m-%d"), t_dpd=t, noaa=line[22:28].strip(), area=area, lat=lat,
                             lon=lon, lcm=lcm))
    g = pd.DataFrame(rows)
    g = g.sort_values(["day", "noaa", "area"], ascending=[True, True, False], kind="stable").drop_duplicates(["day", "noaa"])
    return g.reset_index(drop=True)


def add_isolation(g):
    """isolated = no other DPD group of the same day has its centre inside the measurement window (§2)."""
    iso = np.ones(len(g), bool)
    nb = np.zeros(len(g), int)
    for _, idx in g.groupby("day").indices.items():
        lat, lon = g.lat.to_numpy()[idx], g.lon.to_numpy()[idx]
        inside = (np.abs(lat[:, None] - lat[None, :]) <= P.WIN_LAT) & (np.abs(wrap(lon[:, None] - lon[None, :])) <= P.WIN_LON)
        np.fill_diagonal(inside, False)
        nb[idx] = inside.sum(1)
        iso[idx] = nb[idx] == 0
    return g.assign(isolated=iso, n_neighbours=nb)


def eligible(g):
    d = pd.to_datetime(g.day)
    return g[(d >= START) & (d < END) & (g.area >= MIN_AREA) & (g.lat.abs() <= MAX_ABS_LAT)].copy()


# ---------------------------------------------------------------- magnetograms

def a2_list(path=A2_LIST):
    """{member: SHA-256 of the member content} of the files excluded by amendment A2."""
    t = pd.read_csv(path)
    return dict(zip(t.member, t.sha256))


def magnetogram_table(archive_dir=MWO_DATA, years=ARCHIVE_YEARS, excluded=None):
    """Header table of every Fe I magnetogram. day is the UTC date of obs_time.

    TAVG-UT can exceed 24 hours: filename_day is the observing-session date and
    is kept separately; it must not be used for same-UTC-day DPD matching.
    """
    rows = []
    for y in years:
        path = Path(archive_dir) / f"MWO_{y}.tar.gz"
        if not path.exists():
            continue
        try:
            tf = tarfile.open(path)
        except (tarfile.TarError, OSError, EOFError):
            continue                                   # placeholder archives (1979, 1980)
        with tf:
            for m in tf:
                if not m.isfile() or MP._detect_line(m.name, ("FE",)) != "FE":
                    continue
                day = MP.filename_date(m.name, y)
                if day is None:
                    rows.append(dict(archive_year=y, member=m.name, status="no_filename_date"))
                    continue
                blob = tf.extractfile(m).read()
                if excluded and m.name in excluded:     # amendment A2: never a candidate, identity verified
                    got = hashlib.sha256(blob).hexdigest()
                    if got != excluded[m.name]:
                        raise SystemExit(f"amendment A2: SHA-256 of {m.name} differs from the frozen list")
                    rows.append(dict(archive_year=y, member=m.name, day=day.strftime("%Y-%m-%d"), status="excluded_A2"))
                    continue
                try:
                    h, _ = MP.parse_fits_bytes(blob)
                except Exception as e:                  # noqa: BLE001
                    rows.append(dict(archive_year=y, member=m.name, status=f"unreadable:{type(e).__name__}"))
                    continue
                ot = P.obs_time(h, m.name, y)
                if ot is None:
                    rows.append(dict(archive_year=y, member=m.name, day=day.strftime("%Y-%m-%d"), status="no_tavg"))
                    continue
                good, dcen, db0 = P.ephemeris_ok(h, ot)
                rows.append(dict(archive_year=y, member=m.name, day=ot.strftime("%Y-%m-%d"),
                                 filename_day=day.strftime("%Y-%m-%d"), obs_time=ot,
                                 tavg=float(h["TAVG-UT"]), eph_ok=bool(good), dcenlon=dcen, db0=db0,
                                 dxb=h.get("DXB_OBS"), dyb=h.get("DYB_OBS"), mrkmod=h.get("MRKMOD"),
                                 psepma=h.get("PSEPMA"), bscale=h.get("BSCALE"), blank=h.get("BLANK"),
                                 res_class=res_class(h.get("DXB_OBS"), h.get("DYB_OBS")),
                                 epoch=epoch_of(m.name, h, ot), status="ok"))
    return pd.DataFrame(rows)


def choose(mags, t_dpd):
    """Same-day magnetogram for one candidate day: ephemeris checks passed, then class R1 > R2 > R3 > R0, then
    |TAVG time - DPD time|, then the lowest TAVG-UT, then the member name (deterministic)."""
    ok = [m for m in mags if m["eph_ok"] and m["epoch"] != "unassigned"]
    if not ok:
        return None
    return min(ok, key=lambda m: (CLASS_RANK[m["res_class"]], abs((m["obs_time"] - t_dpd).total_seconds()),
                                  m["tavg"], m["member"]))


# ---------------------------------------------------------------- measurement (pilot rule + amendment A1)

def blank_mask(h, B):
    """BLANK pixels as produced by the pipeline reader: float32(BLANK)*BSCALE + BZERO with the reader's operations."""
    if "BLANK" not in h:
        return np.zeros(B.shape, bool)
    v = np.array([float(h["BLANK"])], dtype=np.float32) * float(h.get("BSCALE", 1.0)) + float(h.get("BZERO", 0.0))
    return B == v[0]


def geometry(h, shape):
    return P.heliographic(h, shape)


def measure(h, B, geom, lat0, lon0):
    """Pilot measurement (mwo_pilot_tilt.measure) on cached geometry, with BLANK pixels set to NaN (A1), the
    window BLANK fraction rule and the flux-weighted mean latitude of the measured pixels."""
    lat, lon, cmd, mu = geom
    blank = blank_mask(h, B)
    Bn = np.where(blank, np.nan, B)
    dlon = (lon - lon0 + 180.0) % 360.0 - 180.0
    win = np.isfinite(mu) & (np.abs(lat - lat0) <= P.WIN_LAT) & (np.abs(dlon) <= P.WIN_LON)
    if not win.any():
        return dict(status="window_off_disk", n_blank_win=0)
    n_blank = int((blank & win).sum())
    if np.nanmin(mu[win]) < P.MU_MIN:
        return dict(status="window_outside_mu_domain", mu_min=float(np.nanmin(mu[win])), n_blank_win=n_blank)
    if n_blank > BLANK_FRAC_MAX * int(win.sum()):
        return dict(status="window_blank", n_blank_win=n_blank, n_win=int(win.sum()))
    br = Bn / mu
    elig = win & np.isfinite(br) & (np.abs(br) <= P.MAX_G)
    pos, neg = elig & (br >= P.THRESH_G), elig & (br <= -P.THRESH_G)
    pix_cm2 = (P.RSUN_CM / float(h["R0"])) ** 2
    wgt = np.abs(br) * pix_cm2 / mu
    out = dict(status="ok", npos=int(pos.sum()), nneg=int(neg.sum()), flux_pos_mx=float(wgt[pos].sum()),
               flux_neg_mx=float(wgt[neg].sum()), mu_min=float(np.nanmin(mu[win])), n_blank_win=n_blank,
               n_win=int(win.sum()))
    if not (pos.any() and neg.any()):
        out["status"] = "no_two_polarities"
        return out
    both = pos | neg
    out["lat_bar"] = float((lat[both] * wgt[both]).sum() / wgt[both].sum())
    cp = geo.weighted_centroid(lon[pos], lat[pos], wgt[pos])
    cn = geo.weighted_centroid(lon[neg], lat[neg], wgt[neg])
    t_np = geo.tilt_deg(cn, cp)
    lead, follow = (cp, cn) if abs(t_np) < 90 else (cn, cp)
    out.update(lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1], leading_sign=1 if abs(t_np) < 90 else -1,
               tilt_deg=geo.tilt_deg(lead, follow), sep_deg=geo.great_circle_deg(*cp, *cn))
    return out


SEALED_KEYS = ("tilt_deg", "leading_sign", "lon_pos", "lat_pos", "lon_neg", "lat_neg", "sep_deg")


def measure_all(attempts, mags, archive_dir=MWO_DATA):
    """Pass 2: stream the archives once, measure every attempt on its chosen magnetogram."""
    by_member = {}
    for i, a in enumerate(attempts):
        if a.get("member"):
            by_member.setdefault((a["archive_year"], a["member"]), []).append(i)
    years = sorted({y for y, _ in by_member})
    for y in years:
        wanted = {m for yy, m in by_member if yy == y}
        with tarfile.open(Path(archive_dir) / f"MWO_{y}.tar.gz") as tf:
            for m in tf:
                if m.name not in wanted:
                    continue
                h, B = MP.parse_fits_bytes(tf.extractfile(m).read())
                geom = geometry(h, B.shape)
                for i in by_member[(y, m.name)]:
                    a = attempts[i]
                    r = measure(h, B, geom, a["dpd_lat"], a["dpd_lon"])
                    a["status"] = r.pop("status")
                    a["sealed"] = {k: r.pop(k) for k in SEALED_KEYS if k in r}
                    a.update(r)
        print(f"measured {y}: {sum(len(by_member[k]) for k in by_member if k[0] == y)} attempts", flush=True)
    return attempts


# ---------------------------------------------------------------- activity (§3)

def daily_sources(dpd_dir=DPD_DIR):
    src = {}
    for line in (Path(dpd_dir) / "dailyDPD1974_2016.txt").read_text().splitlines():
        if not line.startswith("d "):
            continue
        t = line.split()
        if len(t) < 12:
            continue
        src[f"{t[1]}-{t[2]}-{t[3]}"] = t[7] if t[7].isalpha() else "(none)"
    return src


def activity_tables(groups_all, dpd_dir=DPD_DIR, silso_tot=SILSO_TOT, silso_hem=SILSO_HEM):
    """Monthly hemispheric activity, normalised per hemisphere: main (DPD area, all observed days), (a) DPD area on
    Gyula/Debrecen days, (b) SILSO hemispheric 1992-2012, (c) SILSO total split with the DPD area fractions."""
    src = daily_sources(dpd_dir)
    days = sorted(d for d in src if START <= pd.Timestamp(d) < END)
    g = groups_all[groups_all.day.isin(days)].assign(hem=lambda x: np.where(x.lat >= 0, "N", "S"))
    daily = g.groupby(["day", "hem"]).area.sum().unstack(fill_value=0).reindex(days, fill_value=0)
    daily = daily.reindex(columns=["N", "S"], fill_value=0)
    daily.index = pd.to_datetime(daily.index)
    per = daily.index.to_period("M")
    main = daily.groupby(per).mean()
    own = daily[[src[d.strftime("%Y-%m-%d")] in OWN_SOURCES for d in daily.index]]
    a_own = own.groupby(own.index.to_period("M")).mean().reindex(main.index)
    s = pd.read_csv(silso_tot, sep=r"\s+", header=None, usecols=[0, 1, 3], names=["y", "m", "sn"])
    s.index = pd.PeriodIndex.from_fields(year=s.y, month=s.m, freq="M")
    tot = main.N + main.S
    frac_n = np.where(tot > 0, main.N / tot.where(tot > 0, 1), 0.5)
    c = pd.DataFrame({"N": s.sn.reindex(main.index) * frac_n, "S": s.sn.reindex(main.index) * (1 - frac_n)},
                     index=main.index)
    h = pd.read_csv(silso_hem, sep=";", header=None).iloc[:, [0, 1, 4, 5]]
    h.columns = ["y", "m", "N", "S"]
    h.index = pd.PeriodIndex.from_fields(year=h.y, month=h.m, freq="M")
    h = h[["N", "S"]].replace(-1.0, np.nan)
    hb = h.loc[(h.index >= pd.Period("1992-01", "M")) & (h.index <= pd.Period("2012-12", "M"))]
    norm = lambda x: x / x.mean()   # noqa: E731
    return dict(A_main=norm(main), A_own=norm(a_own), A_silso_hem=norm(hb).reindex(main.index), A_silso_split=norm(c))


# ---------------------------------------------------------------- selection of the records

def select(attempts, set_name):
    """Per group: candidate days (isolated ones for 'isolated'), ordered by |LCM| then date; first 'ok' is the record."""
    df = pd.DataFrame([{k: v for k, v in a.items() if k != "sealed"} for a in attempts])
    cand = df[df.has_magnetogram] if set_name == "all" else df[df.has_magnetogram & df.isolated]
    cand = cand.assign(abs_lcm=cand.lcm.abs()).sort_values(["noaa", "abs_lcm", "day"], kind="stable")
    cand["rank"] = cand.groupby("noaa").cumcount() + 1
    cand["n_cand"] = cand.groupby("noaa").noaa.transform("size")
    okc = cand[cand.status == "ok"]
    first = okc.groupby("noaa").head(1)
    return first.assign(record_set=set_name), cand


def build(groups_all, mags, archive_dir=MWO_DATA, dpd_dir=DPD_DIR, silso_tot=SILSO_TOT, silso_hem=SILSO_HEM):
    """Everything except writing: attempts, the two record sets, design, sealed, losses, coverage."""
    g = eligible(add_isolation(groups_all))
    good = mags[mags.status == "ok"]
    by_day = {d: x.to_dict("records") for d, x in good.groupby("day")}
    attempts = []
    for r in g.itertuples():
        ch = choose(by_day.get(r.day, []), r.t_dpd)
        a = dict(noaa=r.noaa, day=r.day, t_dpd=r.t_dpd, dpd_lat=r.lat, dpd_lon=r.lon, lcm=r.lcm, dpd_area=r.area,
                 isolated=bool(r.isolated), n_neighbours=int(r.n_neighbours), has_magnetogram=ch is not None,
                 status="no_magnetogram" if ch is None else "pending")
        if ch is not None:
            a.update(archive_year=int(ch["archive_year"]), member=ch["member"], obs_time=ch["obs_time"],
                     res_class=ch["res_class"], epoch=ch["epoch"],
                     n_same_day=len(by_day.get(r.day, [])))
        attempts.append(a)
    attempts = measure_all(attempts, mags, archive_dir)
    sealed_of = {(a["noaa"], a["day"]): a.get("sealed", {}) for a in attempts}
    acts = activity_tables(groups_all, dpd_dir, silso_tot, silso_hem)
    design, sealed, cands = [], [], {}
    for set_name in ("isolated", "all"):
        rec, cand = select(attempts, set_name)
        cands[set_name] = cand
        for r in rec.itertuples():
            s = sealed_of[(r.noaa, r.day)]
            hem = "N" if r.lat_bar >= 0 else "S"
            t = pd.Timestamp(r.obs_time)
            cycle = cycle_of(pd.Timestamp(r.day))
            per = pd.Period(r.day[:7], "M")
            row = dict(record_set=set_name, noaa=r.noaa, day=r.day, obs_time=t.isoformat(), member=r.member,
                       epoch=r.epoch, res_class=r.res_class, hemisphere=hem, lat_bar=r.lat_bar,
                       sinlat=math.sin(math.radians(abs(r.lat_bar))), phi_mwo=r.flux_pos_mx + r.flux_neg_mx,
                       dpd_area=r.dpd_area, dpd_lat=r.dpd_lat, dpd_lon=r.dpd_lon, lcm=r.lcm, abs_lcm=abs(r.lcm),
                       cycle=cycle, isolated=r.isolated, n_neighbours=r.n_neighbours, rank=int(r.rank),
                       n_cand=int(r.n_cand), n_blank_win=r.n_blank_win)
            for k, tab in acts.items():
                row[k] = float(tab.at[per, hem]) if per in tab.index and np.isfinite(tab.at[per, hem]) else np.nan
            design.append(row)
            gamma = math.copysign(1.0, r.lat_bar) * math.degrees(math.asin(math.sin(math.radians(s["tilt_deg"]))))
            sealed.append(dict(record_set=set_name, noaa=r.noaa, day=r.day, gamma_deg=gamma,
                               hale_expected=cyc_mod.expected_leading_sign(cycle, r.lat_bar), **s))
    design = pd.DataFrame(design)
    design["CR"] = cr_of(parse_times(design.obs_time))
    sealed = pd.DataFrame(sealed)
    att = pd.DataFrame([{k: v for k, v in a.items() if k != "sealed"} for a in attempts])
    return att, design, sealed, losses(g, cands, design, acts), coverage(design)


def parse_times(s):
    """ISO strings with and without fractional seconds (TAVG-UT is fractional): first run of 19 Nov 07:40 failed here."""
    return pd.to_datetime(s, format="ISO8601")


def cr_of(times):
    spec = importlib.util.spec_from_file_location("t3_dpd_feasibility", ROOT / "scripts/t3_dpd_feasibility.py")
    F = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(F)
    # full instant of the measurement (no truncation to midnight: Codex's review)
    return F.cr_of(pd.Series(pd.DatetimeIndex(times), index=range(len(times))))


def losses(g, cands, design, acts):
    """Per group with an eligible day: outcome per record set, by cycle, hemisphere (DPD), date-epoch, activity tercile;
    computed at the eligible day with minimum |LCM|."""
    ref = g.assign(abs_lcm=g.lcm.abs()).sort_values(["noaa", "abs_lcm", "day"]).groupby("noaa").head(1)
    ref = ref.assign(hem=np.where(ref.lat >= 0, "N", "S"), cycle=[cycle_of(pd.Timestamp(d)) for d in ref.day])
    ref["date_epoch"] = [date_epoch(pd.Timestamp(d)) for d in ref.day]
    a = acts["A_main"]
    ref["A"] = [a.at[pd.Period(d[:7], "M"), h] if pd.Period(d[:7], "M") in a.index else np.nan
                for d, h in zip(ref.day, ref.hem)]
    q = np.nanquantile(ref.A, [1 / 3, 2 / 3])
    ref["A_tercile"] = np.searchsorted(q, ref.A, side="right") + 1
    rows = []
    for set_name, cand in cands.items():
        got = set(design.loc[design.record_set == set_name, "noaa"])
        has_cand = set(cand.noaa)
        out = np.where(ref.noaa.isin(got), "record", np.where(ref.noaa.isin(has_cand), "all_attempts_failed",
                                                               "no_candidate_day"))
        r = ref.assign(outcome=out)
        for dim in ("cycle", "hem", "date_epoch", "A_tercile"):
            t = r.groupby([dim, "outcome"]).size().unstack(fill_value=0)
            for k, row in t.iterrows():
                rows.append(dict(record_set=set_name, dimension=dim, value=str(k), **row.to_dict()))
    return pd.DataFrame(rows).fillna(0)


def date_epoch(t):
    """Epoch by date only (for losses of groups without a magnetogram): header boundaries of the §4 table."""
    for e, end in (("E1", "1974-07-10"), ("E2", "1982-01-01"), ("E3", "1984-09-06"), ("E4", "1989-04-11"),
                   ("E5", "1993-09-22"), ("E6", "1995-01-01"), ("E7", "1996-04-10")):
        if t < pd.Timestamp(end):
            return e
    return "E8"


def coverage(design):
    d = design[design.record_set == "isolated"]
    per = d.groupby(["cycle", "hemisphere"]).size()
    need = {f"{c}{h}": int(per.get((c, h), 0)) for c in (21, 22, 23) for h in ("N", "S")}
    ok = len(d) >= COVERAGE_MIN and all(v >= COVERAGE_CYCLE_HEM for v in need.values())
    return dict(n_isolated_records=int(len(d)), per_cycle_hemisphere=need,
                outcome="informativo" if ok else "non concludente")


# ---------------------------------------------------------------- gate and run

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def gate_problem(protocol_sha, amendment_sha, protocol=None, amendment=None, amendment2_sha=None, amendment2=None):
    files = ((Path(protocol or PROTOCOL), protocol_sha, "protocol"), (Path(amendment or AMENDMENT), amendment_sha, "amendment A1"))
    if amendment2_sha is not None or amendment2 is not None:
        files += ((Path(amendment2 or AMENDMENT2), amendment2_sha, "amendment A2"),)
    for f, sha, name in files:
        if not f.exists():
            return f"frozen {name} missing"
        if hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            return f"frozen {name} SHA-256 differs"
    for f, sha, name in files:
        if subprocess.run(["git", "ls-files", "--error-unmatch", str(f)], cwd=ROOT, capture_output=True).returncode:
            return f"frozen {name} not committed"
    if git("status", "--porcelain", "--untracked-files=no"):
        return "clean tree required"
    return None


def run(protocol_sha, amendment_sha, amendment2_sha):
    why = gate_problem(protocol_sha, amendment_sha, amendment2_sha=amendment2_sha)
    if why:
        sys.exit(why)
    if OUT.exists():
        sys.exit("catalogue output exists")
    commit = git("rev-parse", "HEAD")
    groups_all = dpd_groups()
    excl = a2_list()
    mags = magnetogram_table(excluded=excl)
    if int((mags.status == "excluded_A2").sum()) != len(excl):
        sys.exit("amendment A2: not every listed file was found in the archives")
    print(f"magnetograms: {len(mags)} Fe I headers", flush=True)
    att, design, sealed, loss, cov = build(groups_all, mags)
    tmp = OUT.with_name(OUT.name + f".partial_{os.getpid()}")
    tmp.mkdir(parents=True)
    design.to_csv(tmp / "DESIGN.csv", index=False)
    sealed.to_csv(tmp / "SEALED.csv.gz", index=False)
    att.to_csv(tmp / "ATTEMPTS.csv.gz", index=False)
    mags.to_csv(tmp / "MAGNETOGRAMS.csv.gz", index=False)
    loss.to_csv(tmp / "LOSSES.csv", index=False)
    (tmp / "COVERAGE.json").write_text(json.dumps(cov, indent=2) + "\n")
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(tmp.iterdir())}
    os.rename(tmp, OUT)
    meta = dict(protocol_sha256=protocol_sha, amendment_a1_sha256=amendment_sha, amendment_a2_sha256=amendment2_sha,
                a2_list_sha256=hashlib.sha256(A2_LIST.read_bytes()).hexdigest(), git_commit=commit,
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                pilot_script_sha256=hashlib.sha256((ROOT / "scripts/mwo_pilot_tilt.py").read_bytes()).hexdigest(),
                mwo_pipeline_sha256=hashlib.sha256(P.MWO_PIPELINE.read_bytes()).hexdigest(),
                dpd_sha256sums=hashlib.sha256((DPD_DIR / "SHA256SUMS.txt").read_bytes()).hexdigest(),
                silso_tot_sha256=hashlib.sha256(SILSO_TOT.read_bytes()).hexdigest(),
                silso_hem_sha256=hashlib.sha256(SILSO_HEM.read_bytes()).hexdigest(),
                n_attempts=int(len(att)), n_records=design.groupby("record_set").size().to_dict(),
                coverage=cov, products_sha256=hashes,
                sealed_note="SEALED.csv.gz is not to be read before the validation is preserved, recounted and read")
    (OUT / "META.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    # deliberately no print of SEALED content
    print(json.dumps(dict(n_attempts=meta["n_attempts"], n_records=meta["n_records"], coverage=cov), indent=2))
    return 0


# ---------------------------------------------------------------- selftest (synthetic data only)

def selftest():
    import io
    import tempfile
    from astropy.io import fits
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")

    ok("resolution classes on both dimensions, order R1 R2 R3, missing -> R0",
       [res_class(*x) for x in ((9.6, 13.1), (12.9, 20.1), (14.0, 17.4), (13.8, 18.5), (None, 13), (12, 16))]
       == ["R1", "R2", "R3", "R2", "R0", "R0"])
    ok("epochs from MRKMOD and the 1996-04-10 split",
       [epoch_of("1974/MP00_5250MWO_x.fits", {"MRKMOD": 0}, datetime(1974, 2, 1)),
        epoch_of("1990/MP00_5250078_x.fits", {"MRKMOD": 1282}, datetime(1990, 2, 1)),
        epoch_of("1993/MP00_5250078_x.fits", {"MRKMOD": 1283}, datetime(1993, 12, 1)),
        epoch_of("1996/m960408_1630_0fe1.fits", {}, datetime(1996, 4, 8)),
        epoch_of("1996/m960413_2273_0fe1.fits", {}, datetime(1996, 4, 13)),
        epoch_of("1990/MP00_5250078_x.fits", {"MRKMOD": 1284}, datetime(1990, 2, 1))] == ["E1", "E5",
                                                                                           "E6", "E7", "E8", "unassigned"])
    spec = importlib.util.spec_from_file_location("ppa", ROOT / "scripts/prospective_phase_a.py")
    PA = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(PA)
    tb = PA.cr_start(1800)
    crs = cr_of([tb - pd.Timedelta(hours=1), tb + pd.Timedelta(hours=1), pd.Timestamp("1988-03-15 07:52")])
    ok("Carrington rotation from the full instant: one hour before / after the start of CR 1800, and 1988-03-15 07:52",
       list(crs) == [1799, 1800, 1800] and tb < pd.Timestamp("1988-03-15 07:52"), (str(tb), list(crs)))
    pt = parse_times(pd.Series(["1990-05-01T18:00:00", "1990-05-01T18:13:22.800000"]))
    ok("observation times with and without fractional seconds parsed together",
       pt.iloc[1] == pd.Timestamp("1990-05-01 18:13:22.8") and pt.iloc[0] == pd.Timestamp("1990-05-01 18:00"))
    ok("cycle by date (20 before 1976-03)", [cycle_of(pd.Timestamp(x)) for x in
                                             ("1975-12-31", "1976-03-01", "1996-07-31", "2008-12-01")] == [20, 21, 22, 24])
    t0 = datetime(1990, 5, 1, 9)
    mags = [dict(member="b", eph_ok=True, epoch="E5", res_class="R2", obs_time=t0, tavg=9.0),
            dict(member="a", eph_ok=True, epoch="E5", res_class="R1", obs_time=t0 + timedelta(hours=8), tavg=17.0),
            dict(member="c", eph_ok=True, epoch="E5", res_class="R1", obs_time=t0 + timedelta(hours=7), tavg=16.0),
            dict(member="d", eph_ok=False, epoch="E5", res_class="R1", obs_time=t0, tavg=9.0)]
    ok("choice: ephemeris failures skipped, finest class first, then closest time", choose(mags, t0)["member"] == "c")
    ok("choice: no valid magnetogram -> None", choose([mags[3]], t0) is None)
    g = pd.DataFrame([dict(day="1990-05-01", noaa="1", lat=10.0, lon=100.0), dict(day="1990-05-01", noaa="2", lat=14.0, lon=106.0),
                      dict(day="1990-05-01", noaa="3", lat=-20.0, lon=359.0), dict(day="1990-05-01", noaa="4", lat=-22.0, lon=5.0),
                      dict(day="1990-05-02", noaa="5", lat=10.0, lon=100.0)])
    gi = add_isolation(g)
    ok("isolation: neighbour centre inside the window (also across 0/360), other days ignored",
       gi.isolated.tolist() == [False, False, False, False, True])
    with tempfile.TemporaryDirectory() as td:
        line = "g 1977 03 09 08 55 60    790          13    84     7    47  16.99 202.17  11.52 335.04 0.4534"
        for y in range(1974, 2013):
            (Path(td) / f"gDPD{y}.txt").write_text(line + "\r\n" if y == 1977 else "")
        gg = dpd_groups(td)
    ok("DPD group row with seconds = 60 kept (time 08:56:00), not dropped",
       len(gg) == 1 and gg.t_dpd.iloc[0] == datetime(1977, 3, 9, 8, 56, 0) and gg.noaa.iloc[0] == "790")
    # measurement on a synthetic magnetogram: equals the pilot measurement without BLANK, BLANK pixels excluded
    h, B = P.synthetic(lat0=15.0, lon0=110.0, tilt=10.0)
    h = dict(h, BLANK=-32768, BSCALE=0.1, BZERO=0.0)
    B = B.astype(np.float32)
    geom = geometry(h, B.shape)
    m0, mp = measure(h, B, geom, 15.0, 110.0), P.measure(h, B, 15.0, 110.0)
    ok("measure equals the pilot measurement when there are no BLANK pixels",
       m0["status"] == "ok" and abs(m0["tilt_deg"] - mp["tilt_deg"]) < 1e-9 and m0["flux_pos_mx"] == mp["flux_pos_mx"]
       and m0["leading_sign"] == mp["leading_sign"])
    lat, lon, _, mu = geom
    hole = (np.abs(lat - 16.0) < 0.6) & (np.abs(((lon - 108.0 + 180) % 360) - 180) < 0.6)
    Bb = B.copy()
    Bb[hole] = np.float32(-32768) * 0.1
    mb, mpb = measure(h, Bb, geom, 15.0, 110.0), P.measure(h, Bb, 15.0, 110.0)
    ok("BLANK pixels: excluded (tilt as without them within 0.5 deg), counted; the pilot reader alone is biased",
       mb["status"] == "ok" and mb["n_blank_win"] == int(hole.sum()) and abs(mb["tilt_deg"] - m0["tilt_deg"]) < 0.5
       and abs(mpb["tilt_deg"] - m0["tilt_deg"]) > abs(mb["tilt_deg"] - m0["tilt_deg"]),
       (mb["n_blank_win"], round(mb["tilt_deg"] - m0["tilt_deg"], 3), round(mpb["tilt_deg"] - m0["tilt_deg"], 3)))
    win = (np.abs(lat - 15.0) <= 6) & (np.abs(((lon - 110.0 + 180) % 360) - 180) <= 8) & np.isfinite(mu)
    Bw = B.copy()
    Bw[win & (lat > 15.0)] = np.float32(-32768) * 0.1
    ok("window with more than 5 % BLANK pixels -> window_blank", measure(h, Bw, geom, 15.0, 110.0)["status"] == "window_blank")
    ok("lat_bar is the flux-weighted latitude of the measured pixels (near the bipole centre)",
       abs(m0["lat_bar"] - 15.0) < 1.0, round(m0["lat_bar"], 3))
    # end to end on a synthetic archive and DPD files: candidate order, first success, isolation, sets, sealed split
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        days = [datetime(1990, 5, d, 18) for d in (1, 2, 3)]
        lcm = {1: -18.0, 2: -10.0, 3: 2.0}
        dpd_lines, members = [], []
        for d in days:
            cen = MP.cenlon_from_carrington_cont(MP.carrington_continuous_from_date(d))
            b0 = MP.solar_B0_expected_deg(d)
            lon0 = (cen + lcm[d.day]) % 360
            hs, Bs = P.synthetic(B0_deg=b0, cenlon=cen, lat0=12.0, lon0=lon0, tilt=8.0)
            if d.day == 3:
                Bs = np.abs(Bs)                    # the closest-to-meridian day fails (one polarity)
            for k, v in dict(X0=256.5, Y0=256.5, R0=240.0, B0=math.radians(b0), CENLON=cen, MRKMOD=1282, DXB_OBS=9.6,
                             DYB_OBS=13.0, BSCALE=0.1, BZERO=0.0, BLANK=-32768).items():
                hs[k] = v
            members.append((f"1990/MP00_5250078_00_09005{d.day:02d}_1800.fits", hs, Bs))
            for noaa, lat0, dl in (("6000", 12.0, 0.0), ("6001", 12.0 + 3.0, 4.0)):
                if noaa == "6001" and d.day != 2:
                    continue
                line = list(" " * 93)
                for col, txt in ((0, f"g {d:%Y %m %d} 09 00 00"), (22, f"{noaa:>6}"), (53, f"{150:5d}"), (59, f"{lat0:6.2f}"),
                                 (66, f"{(lon0 + dl) % 360:6.2f}"), (73, f"{lcm[d.day] + dl:6.2f}")):
                    line[col:col + len(txt)] = list(txt)
                dpd_lines.append("".join(line))
        with tarfile.open(td / "MWO_1990.tar.gz", "w:gz") as tf:
            for name, hs, Bs in members:
                hdr = fits.Header()
                for k, v in hs.items():
                    hdr[k] = v
                hdr["TAVG-UT"] = 18.0 if "0900501" in name else 18.2230    # fractional seconds on days 2 and 3
                raw = np.round(np.nan_to_num(Bs) / 0.1).clip(-32767, 32767).astype(np.int16)
                buf = io.BytesIO()
                hdu = fits.PrimaryHDU(raw, hdr)
                hdu.header["BSCALE"], hdu.header["BZERO"], hdu.header["BLANK"] = 0.1, 0.0, -32768
                hdu.writeto(buf)
                ti = tarfile.TarInfo(name)
                ti.size = len(buf.getvalue())
                tf.addfile(ti, io.BytesIO(buf.getvalue()))
        for y in range(1974, 2013):
            (td / f"gDPD{y}.txt").write_text("\n".join(dpd_lines) + "\n" if y == 1990 else "")
        (td / "dailyDPD1974_2016.txt").write_text("".join(f"d {d:%Y %m %d} 09 00 00 GYUL   10  100   10  100 0 0 0\n"
                                                          for d in days))
        ga = dpd_groups(td)
        with tarfile.open(td / "MWO_1990.tar.gz") as tf_:
            m3 = next(x for x in tf_.getmembers() if "0900503" in x.name)
            sha3 = hashlib.sha256(tf_.extractfile(m3).read()).hexdigest()
        mg_x = magnetogram_table(td, years=[1990], excluded={m3.name: sha3})
        try:
            magnetogram_table(td, years=[1990], excluded={m3.name: "0" * 64})
            bad_sha_refused = False
        except SystemExit:
            bad_sha_refused = True
        mg = magnetogram_table(td, years=[1990])
        att, design, sealed, loss, cov = build(ga, mg, archive_dir=td, dpd_dir=td)
    iso = design[design.record_set == "isolated"].set_index("noaa")
    al = design[design.record_set == "all"].set_index("noaa")
    ok("end to end: day 3 fails (one polarity), isolated record of 6000 on day 1 (day 2 not isolated), rank 2",
       iso.loc["6000", "day"] == "1990-05-01" and int(iso.loc["6000", "rank"]) == 2, iso.get("day", pd.Series()).to_dict())
    ok("end to end: 'all' set takes day 2 for 6000 (|LCM| 10 < 18); 6001 has no isolated day",
       al.loc["6000", "day"] == "1990-05-02" and "6001" not in iso.index and "6001" in al.index)
    sx = sealed[(sealed.record_set == "isolated") & (sealed.noaa == "6000")].iloc[0]
    ok("end to end: sealed gamma = Joy convention of the synthetic tilt (8 deg) within 1 deg; design has no tilt column",
       abs(sx.gamma_deg - 8.0) < 1.0 and not ({"tilt_deg", "gamma_deg", "leading_sign"} & set(design.columns)),
       round(sx.gamma_deg, 2))
    ok("end to end: epoch E5, class R1, activity filled, coverage 'non concludente'",
       iso.loc["6000", "epoch"] == "E5" and iso.loc["6000", "res_class"] == "R1" and np.isfinite(iso.loc["6000", "A_main"])
       and cov["outcome"] == "non concludente")
    ok("amendment A2: listed member marked excluded_A2 and never a candidate; wrong SHA-256 refused",
       (mg_x.set_index("member").loc[m3.name, "status"] == "excluded_A2") and choose(
           mg_x[(mg_x.status == "ok") & (mg_x.day == "1990-05-03")].to_dict("records"), datetime(1990, 5, 3, 9)) is None
       and bad_sha_refused)
    ok("end to end: attempts table has no tilt and keeps every candidate day with its status",
       len(att) == 4 and "tilt_deg" not in att.columns and set(att.status) == {"ok", "no_two_polarities"})
    with tempfile.TemporaryDirectory() as td:
        f1, f2 = Path(td) / "P.md", Path(td) / "A.md"
        g1 = gate_problem("x" * 64, "y" * 64, f1, f2)
        f1.write_text("frozen")
        g2 = gate_problem("x" * 64, "y" * 64, f1, f2)
        g3 = gate_problem(hashlib.sha256(b"frozen").hexdigest(), "y" * 64, f1, f2)
        f2.write_text("amend")
        g4 = gate_problem(hashlib.sha256(b"frozen").hexdigest(), hashlib.sha256(b"amend").hexdigest(), f1, f2)
    ok("gate refuses missing, wrong-SHA and uncommitted protocol or amendment",
       (g1, g2, g3, g4) == ("frozen protocol missing", "frozen protocol SHA-256 differs", "frozen amendment A1 missing",
                            "frozen protocol not committed"), (g1, g2, g3, g4))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--protocol-sha")
    ap.add_argument("--amendment-sha")
    ap.add_argument("--amendment2-sha")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.run and a.protocol_sha and a.amendment_sha and a.amendment2_sha:
        if not selftest():
            return 1
        return run(a.protocol_sha, a.amendment_sha, a.amendment2_sha)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
