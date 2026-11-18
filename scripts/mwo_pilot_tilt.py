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
    ok("--run refuses before the pilot protocol exists", not FROZEN.exists())
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.run:
        if not FROZEN.exists():
            sys.exit("no frozen pilot protocol: the pilot cannot run")
        sys.exit("pilot run to be written against the frozen protocol (matching with P1 and DPD, outputs, recount)")
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
