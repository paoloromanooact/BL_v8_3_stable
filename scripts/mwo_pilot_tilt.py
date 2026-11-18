"""MWO magnetic tilt pilot (variant §8b of docs/PROTOCOL_T3_DPD_DRAFT.md): tilt of a sunspot group from a Mount Wilson
full-disk magnetogram, at the DPD group position, compared with P1 on the same NOAA region (2010-2013 overlap).

Prepared before any protocol for the pilot exists: --selftest uses synthetic MWO-like magnetograms only; --run refuses
without a frozen pilot protocol. Geometry, FITS reader, dates and ephemeris checks are imported unchanged from the frozen
MWO pipeline of the polar-flux project (SHA-256 recorded at run time). Parameters below are PROPOSALS for the protocol.

    .venv/bin/python scripts/mwo_pilot_tilt.py --selftest

Method (per region): DPD group record of the same UT day (NOAA, Carrington L, latitude B) -> Fe I 5250 MWO magnetogram of
that day closest in time to the P1 record (TAVG-UT), passing the ephemeris checks of the MWO pipeline -> pixels with
heliographic position inside a fixed window around the DPD centre -> B_r = B_LOS / mu, |B_r| >= threshold, |B_r| <=
maximum, mu >= MU_MIN -> flux-weighted centroids of each polarity on the sphere (pixel area on the sphere = image pixel
area / mu) -> P1 tilt convention (leading = westernmost polarity; python/sharpbl/geometry.tilt_deg) and leading sign.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import math
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry as geo  # noqa: E402

MWO_PIPELINE = Path("/home/gianluca/MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/src/MWO_and_inputs/"
                    "MWO_PIPELINE_CLEAN_ALLDATA_STRICT_REPAIRED_QC.py")
MWO_DATA = Path("/storage/shared/gianluca/MWO_project/Desktop/MWO/data MWO")
FROZEN = ROOT / "docs/PROTOCOL_MWO_PILOT.md"
DPD_DIR = ROOT / "data/sharp/external_DPD_20261118"
OUT = ROOT / "results/MWO_PILOT"
FLAG_DEG, LEAD_MIN, DAX_MAX, MIN_EVAL, MIN_HEM = 2.107, 0.90, 5.0, 150, 50

# proposed parameters (to be fixed by the pilot protocol)
WIN_LAT, WIN_LON = 6.0, 8.0       # half-window around the DPD centre, degrees
THRESH_G, MAX_G = 50.0, 4000.0    # |B_r| cuts (MWO fields are diluted by ~13"x20" resolution)
MU_MIN = 0.8
CENLON_TOL, B0_TOL = 18.0, 0.5    # ephemeris checks as in the MWO pipeline strict QC
RSUN_CM = 6.96e10                 # P1 nominal radius; flux = sum |B_r| * (R_sun / R0)^2 / mu  (Codex's review)

_spec = importlib.util.spec_from_file_location("mwo_pipeline", MWO_PIPELINE)
MP = importlib.util.module_from_spec(_spec)
sys.modules["mwo_pipeline"] = MP          # dataclasses need the module registered
_spec.loader.exec_module(MP)


def heliographic(h, shape):
    """Exact mapping of the frozen MWO pipeline: (lat, Carrington lon, cmd, mu) per pixel, NaN off disk."""
    yy, xx = np.indices(shape, dtype=float)
    xi = (xx + 1.0 - float(h["X0"])) / float(h["R0"])
    eta = (yy + 1.0 - float(h["Y0"])) / float(h["R0"])
    r2 = xi * xi + eta * eta
    disk = r2 < 0.999
    mu = np.full(shape, np.nan)
    mu[disk] = np.sqrt(1.0 - r2[disk])
    B0 = float(h["B0"])
    nx = mu * math.cos(B0) - eta * math.sin(B0)
    nz = mu * math.sin(B0) + eta * math.cos(B0)
    lat = np.degrees(np.arcsin(np.clip(nz, -1.0, 1.0)))
    cmd = np.degrees(np.arctan2(xi, nx))
    lon = (float(h["CENLON"]) + cmd) % 360.0
    return lat, lon, cmd, mu


def ephemeris_ok(h, dt):
    """Strict-QC style checks of CENLON and B0 against the date (functions of the MWO pipeline)."""
    cen = MP.cenlon_from_carrington_cont(MP.carrington_continuous_from_date(dt))
    dcen = MP.circular_diff_deg(float(h["CENLON"]), cen)
    db0 = math.degrees(float(h["B0"])) - MP.solar_B0_expected_deg(dt)
    return abs(dcen) <= CENLON_TOL and abs(db0) <= B0_TOL, dcen, db0


def obs_time(h, member, year):
    day = MP.filename_date(member, year)
    if day is None or "TAVG-UT" not in h:
        return None
    return day.replace(hour=0) + timedelta(hours=float(h["TAVG-UT"]))


def measure(h, B, lat0, lon0):
    """Tilt at the DPD centre (lat0, Carrington lon0); returns a dict with status."""
    lat, lon, cmd, mu = heliographic(h, B.shape)
    dlon = (lon - lon0 + 180.0) % 360.0 - 180.0
    win = np.isfinite(mu) & (np.abs(lat - lat0) <= WIN_LAT) & (np.abs(dlon) <= WIN_LON)
    if not win.any():
        return dict(status="window_off_disk")
    if np.nanmin(mu[win]) < MU_MIN:
        return dict(status="window_outside_mu_domain", mu_min=float(np.nanmin(mu[win])))
    br = B / mu
    elig = win & np.isfinite(br) & (np.abs(br) <= MAX_G)
    pos, neg = elig & (br >= THRESH_G), elig & (br <= -THRESH_G)
    pix_cm2 = (RSUN_CM / float(h["R0"])) ** 2   # plane-of-sky pixel area; on the sphere divided by mu
    wgt = np.abs(br) * pix_cm2 / mu            # |B_r| dA on the sphere, in Mx per pixel
    out = dict(status="ok", npos=int(pos.sum()), nneg=int(neg.sum()), flux_pos_mx=float(wgt[pos].sum()),
               flux_neg_mx=float(wgt[neg].sum()), mu_min=float(np.nanmin(mu[win])))
    if not (pos.any() and neg.any()):
        out["status"] = "no_two_polarities"
        return out
    cp = geo.weighted_centroid(lon[pos], lat[pos], wgt[pos])
    cn = geo.weighted_centroid(lon[neg], lat[neg], wgt[neg])
    t_np = geo.tilt_deg(cn, cp)
    lead, follow = (cp, cn) if abs(t_np) < 90 else (cn, cp)
    out.update(lon_pos=cp[0], lat_pos=cp[1], lon_neg=cn[0], lat_neg=cn[1], leading_sign=1 if abs(t_np) < 90 else -1,
               tilt_deg=geo.tilt_deg(lead, follow), sep_deg=geo.great_circle_deg(*cp, *cn))
    return out


def fe_members(year):
    """Fe I 5250 magnetogram members of the MWO archive of a year (line detection of the MWO pipeline)."""
    with tarfile.open(MWO_DATA / f"MWO_{year}.tar.gz") as tf:
        return [m.name for m in tf.getmembers() if m.isfile() and MP._detect_line(m.name, ("FE",)) == "FE"]


# ---------------------------------------------------------------- pilot pipeline (§1-§4 of the draft)

def p1_candidates(end="2014-01-01"):
    """P1 sample S records before `end` with a numeric NOAA number."""
    import pandas as pd
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import run_p2
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    S = run_p2.samples(cat)["S"]
    S = S[S["t"] < pd.Timestamp(end)].copy()
    S["noaa"] = pd.to_numeric(S["NOAA_AR"], errors="coerce")
    S = S[S["noaa"] > 0]
    return [dict(HARPNUM=int(r.HARPNUM), T_REC=r.T_REC, t=r.t.to_pydatetime(), noaa=str(int(r.noaa)),
                 hemisphere=r.hemisphere, p1_tilt=r.tilt_deg, p1_lat=r.lat_mean_deg, p1_phi=r.phi_mx,
                 p1_leading=r.leading_sign) for r in S.itertuples()]


def dpd_rows(years, dpd_dir=DPD_DIR):
    """DPD group rows: {(date, NOAA string): (lat, Carrington L, corrected WS area)} keeping the largest area."""
    out = {}
    for y in years:
        for line in (Path(dpd_dir) / f"gDPD{y}.txt").read_text().splitlines():
            if not line.startswith("g "):
                continue
            try:
                lat, lon, area = float(line[59:65]), float(line[66:72]), int(line[53:58])
            except ValueError:
                continue
            if lat > 900 or lon > 900:
                continue
            key = (f"{line[2:6]}-{line[7:9]}-{line[10:12]}", line[22:28].strip())
            if key not in out or area > out[key][2]:
                out[key] = (lat, lon, area)
    return out


def read_members(year, wanted, archive_dir):
    with tarfile.open(Path(archive_dir) / f"MWO_{year}.tar.gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.name in wanted}


def process(cands, archive_dir=MWO_DATA, dpd_dir=DPD_DIR):
    """One row per candidate: MWO measurement at the DPD centre on the closest same-day Fe magnetogram passing the
    ephemeris checks, and the differences with P1. Every exclusion keeps its cause."""
    years = sorted({c["t"].year for c in cands})
    dpd = dpd_rows(years, dpd_dir)
    by_day = {}
    for y in years:
        with tarfile.open(Path(archive_dir) / f"MWO_{y}.tar.gz") as tf:
            names = [m.name for m in tf.getmembers() if m.isfile() and MP._detect_line(m.name, ("FE",)) == "FE"]
        for n in names:
            d = MP.filename_date(n, y)
            if d is not None:
                by_day.setdefault(d.date(), []).append((y, n))
    need = {}
    for c in cands:
        for y, n in by_day.get(c["t"].date(), []):
            need.setdefault(y, set()).add(n)
    blobs = {}
    for y, names in need.items():
        blobs.update(read_members(y, names, archive_dir))
    rows = []
    for c in cands:
        row = dict({k: v for k, v in c.items() if k != "t"}, t=c["t"].isoformat())
        key = (c["t"].strftime("%Y-%m-%d"), c["noaa"])
        if key not in dpd:
            rows.append(dict(row, status="no_dpd_group"))
            continue
        lat0, lon0, _ = dpd[key]
        opts = []
        for y, n in by_day.get(c["t"].date(), []):
            h, B = MP.parse_fits_bytes(blobs[n])
            ot = obs_time(h, n, y)
            if ot is not None:
                opts.append((abs((ot - c["t"]).total_seconds()), n, h, B, ot))
        if not opts:
            rows.append(dict(row, status="no_mwo_magnetogram"))
            continue
        chosen = None
        for dt_s, n, h, B, ot in sorted(opts, key=lambda x: (x[0], x[1])):
            good, dcen, db0 = ephemeris_ok(h, ot)
            if good:
                chosen = (dt_s, n, h, B, ot, dcen, db0)
                break
        if chosen is None:
            rows.append(dict(row, status="ephemeris_check_failed"))
            continue
        dt_s, n, h, B, ot, dcen, db0 = chosen
        m = measure(h, B, lat0, lon0)
        row.update(member=n, mwo_time=ot.isoformat(), dt_s=dt_s, dpd_lat=lat0, dpd_lon=lon0, dcenlon=dcen, db0=db0,
                   **{f"mwo_{k}": v for k, v in m.items()})
        row["status"] = m["status"]
        if m["status"] == "ok" and np.isfinite(c["p1_tilt"]):
            d = m["tilt_deg"] - c["p1_tilt"]
            dax = (d + 90.0) % 180.0 - 90.0
            row.update(d=d, d_ax=dax, abs_d_ax=abs(dax), d_gamma=math.copysign(1.0, c["p1_lat"]) * dax,
                       leading_agree=int(m["leading_sign"] == c["p1_leading"]),
                       flux_ratio=(m["flux_pos_mx"] + m["flux_neg_mx"]) / c["p1_phi"] if c["p1_phi"] else np.nan)
        elif m["status"] == "ok":
            row["status"] = "p1_tilt_missing"
        rows.append(row)
    return rows


def summarise(rows):
    """§3 summaries and the §4 criterion (with the minimum coverage)."""
    import pandas as pd
    df = pd.DataFrame(rows)
    ev = df[df.get("d_gamma", pd.Series(dtype=float)).notna()] if "d_gamma" in df else df.iloc[0:0]
    tert = np.quantile(ev.p1_phi, [1 / 3, 2 / 3]) if len(ev) >= 3 else [np.nan, np.nan]

    def stats(g, name):
        v = g.d_gamma.to_numpy(float)
        n = len(v)
        return dict(group=name, n=n, d_gamma_median=float(np.median(v)) if n else np.nan,
                    d_gamma_mean=float(v.mean()) if n else np.nan,
                    s_over_sqrt_n=float(v.std(ddof=1) / math.sqrt(n)) if n > 1 else np.nan,
                    abs_d_ax_median=float(np.median(g.abs_d_ax)) if n else np.nan,
                    leading_agree=float(g.leading_agree.mean()) if n else np.nan,
                    flux_ratio_median=float(np.median(g.flux_ratio)) if n else np.nan)
    groups = [stats(ev, "all")] + [stats(ev[ev.hemisphere == h], h) for h in ("N", "S")]
    if len(ev) >= 3:
        cls = np.searchsorted(tert, ev.p1_phi, side="right")
        groups += [stats(ev[cls == i], f"P1 flux tercile {i + 1}") for i in range(3)]
    tab = pd.DataFrame(groups)
    causes = df.status.value_counts().to_dict()
    g = {r["group"]: r for r in groups}
    coverage = len(ev) >= MIN_EVAL and all(g[h]["n"] >= MIN_HEM for h in ("N", "S"))

    def passes(r):
        return bool(r["n"] and r["leading_agree"] >= LEAD_MIN and abs(r["d_gamma_median"]) < FLAG_DEG
                    and r["abs_d_ax_median"] <= DAX_MAX)
    overall = coverage and passes(g["all"]) and all(abs(g[h]["d_gamma_median"]) < FLAG_DEG for h in ("N", "S"))
    verdict = ("pilota non concludente" if not coverage else
               "variante MWO utilizzabile" if overall else
               ("utilizzabile con soglia di flusso (fallisce solo il terzile basso)"
                if len(groups) == 6 and passes(g["P1 flux tercile 2"]) and passes(g["P1 flux tercile 3"])
                and not passes(g["P1 flux tercile 1"]) else "variante MWO non utilizzabile"))
    return tab, causes, verdict


# ---------------------------------------------------------------- selftest (synthetic only)

def synthetic(B0_deg=5.0, cenlon=100.0, lat0=15.0, lon0=110.0, tilt=10.0, sep=6.0, n=512, R=240.0):
    """MWO-like magnetogram with a bipole of known tilt at (lat0, lon0): leading (west) positive."""
    h = dict(X0=256.5, Y0=256.5, R0=R, B0=math.radians(B0_deg), CENLON=cenlon)
    lat, lon, cmd, mu = heliographic(h, (n, n))
    t = math.radians(tilt)
    # leading west of the centre and, for positive Joy tilt in the north, closer to the equator
    dl, db = 0.5 * sep * math.cos(t), 0.5 * sep * math.sin(t)
    lead = (lon0 + dl / math.cos(math.radians(lat0)), lat0 - db)
    foll = (lon0 - dl / math.cos(math.radians(lat0)), lat0 + db)
    B = np.zeros((n, n))
    for (lo, la), sgn in ((lead, 1.0), (foll, -1.0)):
        dd = np.degrees(np.arccos(np.clip(np.sin(np.radians(lat)) * math.sin(math.radians(la)) + np.cos(np.radians(lat))
                                          * math.cos(math.radians(la)) * np.cos(np.radians(lon - lo)), -1, 1)))
        B += sgn * 800.0 * np.exp(-0.5 * (dd / 1.2) ** 2)
    return h, np.where(np.isfinite(mu), B * mu, np.nan)   # LOS of a radial field


def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    h, B = synthetic()
    lat, lon, cmd, mu = heliographic(h, B.shape)
    j, i = np.unravel_index(np.nanargmax(np.where(np.isfinite(mu), mu, -1)), mu.shape)
    ok("disk centre at the image centre, at latitude B0 and longitude CENLON",
       abs(lat[j, i] - 5.0) < 0.5 and abs(((lon[j, i] - 100.0 + 180) % 360) - 180) < 0.5, (lat[j, i], lon[j, i]))
    ok("+x is west (Carrington longitude increases with x)", lon[256, 300] > lon[256, 200])
    r = measure(h, B, 15.0, 110.0)
    exp = geo.tilt_deg((110 + 3 * math.cos(math.radians(10)) / math.cos(math.radians(15)), 15 - 3 * math.sin(math.radians(10))),
                       (110 - 3 * math.cos(math.radians(10)) / math.cos(math.radians(15)), 15 + 3 * math.sin(math.radians(10))))
    ok("synthetic bipole: tilt recovered within 1 deg (P1 convention), leading positive",
       r["status"] == "ok" and abs(r["tilt_deg"] - exp) < 1.0 and r["leading_sign"] == 1, (round(r.get("tilt_deg", np.nan), 2), round(exp, 2)))
    h2, B2 = synthetic(tilt=-20.0, lat0=-12.0, lon0=95.0)
    r2 = measure(h2, B2, -12.0, 95.0)
    exp2 = geo.tilt_deg((95 + 3 * math.cos(math.radians(-20)) / math.cos(math.radians(-12)), -12 - 3 * math.sin(math.radians(-20))),
                        (95 - 3 * math.cos(math.radians(-20)) / math.cos(math.radians(-12)), -12 + 3 * math.sin(math.radians(-20))))
    ok("southern bipole: tilt recovered within 1 deg", r2["status"] == "ok" and abs(r2["tilt_deg"] - exp2) < 1.0,
       (round(r2.get("tilt_deg", np.nan), 2), round(exp2, 2)))
    ok("window near the limb refused (mu domain)", measure(h, B, 15.0, 160.0)["status"] in
       ("window_outside_mu_domain", "window_off_disk"))
    ok("unipolar window -> no_two_polarities", measure(h, np.abs(B), 15.0, 110.0)["status"] == "no_two_polarities")
    # flux in Mx: a uniform radial field of 100 G over the window must give 100 G x the spherical window area
    hu = dict(X0=256.5, Y0=256.5, R0=240.0, B0=0.0, CENLON=100.0)
    lat_u, lon_u, cmd_u, mu_u = heliographic(hu, (512, 512))
    Bu = np.where(np.isfinite(mu_u), 100.0 * mu_u, np.nan)
    Bu[(np.abs(lat_u) < 1)] *= -1                         # a negative strip, so both polarities exist
    ru = measure(hu, Bu, 5.0, 100.0)
    lat1, lat2 = np.radians(5.0 - WIN_LAT), np.radians(5.0 + WIN_LAT)
    area = RSUN_CM ** 2 * np.radians(2 * WIN_LON) * (np.sin(lat2) - np.sin(lat1))
    tot = ru.get("flux_pos_mx", 0) + ru.get("flux_neg_mx", 0)
    ok("flux in Mx: uniform 100 G over the window = 100 G x spherical area within 3 %", abs(tot / (100 * area) - 1) < 0.03,
       round(tot / (100 * area), 4))
    dt = datetime(2011, 6, 1, 18)
    cen = MP.cenlon_from_carrington_cont(MP.carrington_continuous_from_date(dt))
    hb = dict(CENLON=cen, B0=math.radians(MP.solar_B0_expected_deg(dt)))
    ok("ephemeris check accepts consistent header, refuses a 1 deg B0 error",
       ephemeris_ok(hb, dt)[0] and not ephemeris_ok(dict(hb, B0=hb["B0"] + math.radians(1.0)), dt)[0])
    ok("real archive readable: Fe members found for 2011 (listing only, no data read)", len(fe_members(2011)) > 100,
       len(fe_members(2011)))
    # end-to-end on a synthetic archive: two same-day magnetograms, the closer one with a wrong CENLON (must be skipped)
    import tempfile, io as _io
    from astropy.io import fits
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ot = datetime(2011, 6, 1, 18, 0)
        cen = MP.cenlon_from_carrington_cont(MP.carrington_continuous_from_date(ot))
        b0 = MP.solar_B0_expected_deg(ot)
        lat0, lon0, tilt = 12.0, (cen + 10.0) % 360, 12.0
        hs, Bs = synthetic(B0_deg=b0, cenlon=cen, lat0=lat0, lon0=lon0, tilt=tilt)
        with tarfile.open(td / "MWO_2011.tar.gz", "w:gz") as tf:
            for name, hour, cenlon in (("2011/MP00_5250078_00_0110601_1800.fits", 18.0, cen),
                                       ("2011/MP00_5250078_00_0110601_1815.fits", 18.25, (cen + 30) % 360)):
                hdr = fits.Header()
                for k, v in dict(X0=256.5, Y0=256.5, R0=240.0, B0=math.radians(b0), CENLON=cenlon).items():
                    hdr[k] = v
                hdr["TAVG-UT"] = hour
                buf = _io.BytesIO()
                fits.PrimaryHDU(np.nan_to_num(Bs).astype(np.float32), hdr).writeto(buf)
                ti = tarfile.TarInfo(name)
                ti.size = len(buf.getvalue())
                tf.addfile(ti, _io.BytesIO(buf.getvalue()))
        line = list(" " * 93)
        for col, txt in ((0, "g 2011 06 01 08 00 00"), (22, f"{'11222':>6}"), (53, f"{120:5d}"), (59, f"{lat0:6.2f}"),
                         (66, f"{lon0:6.2f}")):
            line[col:col + len(txt)] = list(txt)
        (td / "gDPD2011.txt").write_text("".join(line) + "\n")
        lead = (lon0 + 3 * math.cos(math.radians(tilt)) / math.cos(math.radians(lat0)), lat0 - 3 * math.sin(math.radians(tilt)))
        foll = (lon0 - 3 * math.cos(math.radians(tilt)) / math.cos(math.radians(lat0)), lat0 + 3 * math.sin(math.radians(tilt)))
        p1t = geo.tilt_deg(lead, foll)
        cand = [dict(HARPNUM=1, T_REC="2011.06.01_18:12:00_TAI", t=datetime(2011, 6, 1, 18, 12), noaa="11222",
                     hemisphere="N", p1_tilt=p1t, p1_lat=lat0, p1_phi=1e21, p1_leading=1)]
        rows = process(cand, archive_dir=td, dpd_dir=td)
        r = rows[0]
    ok("end to end: closer magnetogram with wrong CENLON skipped, tilt agrees with P1 within 1 deg, leading agrees",
       r["status"] == "ok" and r["member"].endswith("_1800.fits") and abs(r["d_ax"]) < 1.0 and r["leading_agree"] == 1,
       (r.get("status"), r.get("member", "")[-9:], round(r.get("d_ax", np.nan), 3)))
    tab, causes, verdict = summarise(rows)
    ok("summary on one record: coverage rule gives 'pilota non concludente'", verdict == "pilota non concludente", verdict)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "P.md"
        g1 = gate_problem("x" * 64, f)
        f.write_text("frozen")
        g2, g3 = gate_problem("y" * 64, f), gate_problem(hashlib.sha256(b"frozen").hexdigest(), f)
    ok("gate refuses missing, wrong-SHA and uncommitted protocol (temporary files)",
       (g1, g2, g3) == ("frozen protocol missing", "frozen protocol SHA-256 differs", "frozen protocol not committed"))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def git(*a):
    import subprocess
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def gate_problem(protocol_sha, frozen=None):
    import subprocess
    frozen = Path(frozen) if frozen else FROZEN
    if not frozen.exists():
        return "frozen protocol missing"
    if hashlib.sha256(frozen.read_bytes()).hexdigest() != protocol_sha:
        return "frozen protocol SHA-256 differs"
    if subprocess.run(["git", "ls-files", "--error-unmatch", str(frozen)], cwd=ROOT, capture_output=True).returncode:
        return "frozen protocol not committed"
    if git("status", "--porcelain", "--untracked-files=no"):
        return "clean tree required"
    return None


def run(protocol_sha):
    import json
    import os
    import pandas as pd
    why = gate_problem(protocol_sha)
    if why:
        sys.exit(why)
    if OUT.exists():
        sys.exit("pilot output exists")
    commit = git("rev-parse", "HEAD")
    rows = process(p1_candidates())
    tab, causes, verdict = summarise(rows)
    tmp = OUT.with_name(OUT.name + f".partial_{os.getpid()}")
    tmp.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(tmp / "ROWS.csv", index=False)
    tab.to_csv(tmp / "SUMMARY.csv", index=False)
    (tmp / "CAUSES.json").write_text(json.dumps(causes, indent=2) + "\n")
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in tmp.iterdir()}
    os.rename(tmp, OUT)
    meta = dict(protocol_sha256=protocol_sha, git_commit=commit, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                mwo_pipeline_sha256=hashlib.sha256(MWO_PIPELINE.read_bytes()).hexdigest(),
                dpd_sha256sums=hashlib.sha256((DPD_DIR / "SHA256SUMS.txt").read_bytes()).hexdigest(),
                n_candidates=len(rows), verdict=verdict, products_sha256=hashes)
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(tab.to_string(index=False))
    print(causes, verdict)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--protocol-sha")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.run and a.protocol_sha:
        if not selftest():
            return 1
        return run(a.protocol_sha)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
