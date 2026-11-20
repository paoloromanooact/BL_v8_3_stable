"""Independent recount of the T3-on-MWO measurement (delivery 1). Does not import scripts/t3_mwo_catalogue.py,
scripts/mwo_pilot_tilt.py nor the MWO pipeline.

Rebuilds from the raw inputs, with its own code: the DPD group rows and their isolation, the Fe I magnetogram list with
own header reader (float32 before BSCALE, as the pipeline), own filename dates, own ephemeris (Meeus, solar longitude
from astropy), the resolution class, the epoch, the choice of the magnetogram, the measurement (own geometry, BLANK
pixels excluded as in amendment A1), the first-success selection of both record sets and the main activity. Then it
compares, automatically, with the runner products: ATTEMPTS (status of every candidate day), DESIGN (every column it
rebuilds) and SEALED (tilt, gamma, leading sign). Only maxima of differences and counts of mismatches are printed:
no tilt value or tilt statistic is printed or written, so the seal is respected.

    .venv/bin/python scripts/t3_mwo_catalogue_recount.py --selftest
    .venv/bin/python scripts/t3_mwo_catalogue_recount.py --check
"""
import argparse
import hashlib
import json
import math
import re
import sys
import tarfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "results/T3_MWO_CATALOGUE_R2"            # corrected UTC-day grouping (Codex, 19530d6)
OUT = ROOT / "results/T3_MWO_CATALOGUE_R2_RECOUNT"
DPD = ROOT / "data/sharp/external_DPD_20261118"
MWO_DATA = Path("/storage/shared/gianluca/MWO_project/Desktop/MWO/data MWO")
WIN_LAT, WIN_LON, THR, BMAX, MU_MIN, RSUN = 6.0, 8.0, 50.0, 4000.0, 0.8, 6.96e10
CENLON_TOL, B0_TOL, BLANK_MAX = 18.0, 0.5, 0.05
BORDER_CEN, BORDER_B0 = 0.5, 0.05          # ephemeris decisions closer than this to the tolerance are 'borderline'
D0, D1 = "1974-01-01", "2013-01-01"


# ---------------------------------------------------------------- inputs (own parsers)

def groups(dpd=DPD):
    out = {}
    for y in range(1974, 2013):
        for line in (Path(dpd) / f"gDPD{y}.txt").read_text().splitlines():
            if not line.startswith("g "):
                continue
            f = line[59:65], line[66:72], line[73:79], line[53:58]
            try:
                lat, lon, lcm, area = float(f[0]), float(f[1]), float(f[2]), int(f[3])
                t = datetime.strptime(line[2:18], "%Y %m %d %H %M") + timedelta(seconds=int(line[19:21]))
            except ValueError:
                continue
            if max(lat, lon, lcm) > 900:
                continue
            k = (t.strftime("%Y-%m-%d"), line[22:28].strip())
            if k not in out or area > out[k]["area"]:       # ties: first row in file order
                out[k] = dict(day=k[0], noaa=k[1], t=t, lat=lat, lon=lon, lcm=lcm, area=area)
    return out


def isolation(gr):
    by_day = {}
    for (d, n), r in gr.items():
        by_day.setdefault(d, []).append(r)
    nb = {}
    for d, rs in by_day.items():
        for r in rs:
            nb[(d, r["noaa"])] = sum(o["noaa"] != r["noaa"] and abs(o["lat"] - r["lat"]) <= WIN_LAT
                                     and abs((o["lon"] - r["lon"] + 180) % 360 - 180) <= WIN_LON for o in rs)
    return nb


def header_and_data(buf):
    """Own primary-HDU reader; float32 before BSCALE/BZERO as the pipeline reader."""
    cards, pos = [], 0
    while True:
        block = buf[pos:pos + 2880]
        if len(block) < 2880:
            raise ValueError("truncated")
        pos += 2880
        cards += [block[i:i + 80].decode("ascii", "replace") for i in range(0, 2880, 80)]
        if any(c.startswith("END") for c in cards[-36:]):
            break
    h = {}
    for c in cards:
        if c.startswith("END"):
            break
        if c[8:10] == "= ":
            raw = c[10:80].split("/")[0].strip()
            try:
                h[c[:8].strip()] = float(raw)
            except ValueError:
                h[c[:8].strip()] = raw.strip("' ")
    n1, n2 = int(h["NAXIS1"]), int(h["NAXIS2"])
    dt = {16: ">i2", 32: ">i4", -32: ">f4", -64: ">f8"}[int(h["BITPIX"])]
    a = np.frombuffer(buf[pos:pos + n1 * n2 * np.dtype(dt).itemsize], dtype=dt).astype(np.float32).reshape(n2, n1)
    B = a * float(h.get("BSCALE", 1.0)) + float(h.get("BZERO", 0.0))
    blank = (a == np.float32(h["BLANK"])) if "BLANK" in h else np.zeros(a.shape, bool)
    return h, B, blank


def is_fe(name):
    low = name.lower()
    return "fe1" in low or Path(name).name.lower().startswith("mp00_5250")


def name_day(name, year):
    mo = re.search(r"(?i)(?:^|/)m(\d{2})(\d{2})(\d{2})_", "/" + name) or re.search(r"_0(\d{2})(\d{2})(\d{2})_", name)
    if not mo:
        return None
    yy, mm, dd = map(int, mo.groups())
    yyyy = min((1900 + yy, 2000 + yy), key=lambda v: abs(v - year))
    try:
        return datetime(yyyy, mm, dd)
    except ValueError:
        return None


def meeus(t):
    """Carrington longitude of the disc centre L0 and B0 (degrees), Meeus ch. 29, with the apparent solar ecliptic
    longitude from astropy."""
    from astropy.coordinates import GeocentricTrueEcliptic, get_sun
    from astropy.time import Time
    tt = Time(t, scale="utc")
    lam = get_sun(tt).transform_to(GeocentricTrueEcliptic(equinox=tt)).lon.deg
    jd = tt.jd
    I = math.radians(7.25)
    K = math.radians(73.6667 + 1.3958333 * (jd - 2396758.0) / 36525.0)
    theta = (jd - 2398220.0) * 360.0 / 25.38
    lk = math.radians(lam) - K
    B0 = math.degrees(math.asin(math.sin(lk) * math.sin(I)))
    eta = math.degrees(math.atan2(-math.sin(lk) * math.cos(I), -math.cos(lk)))
    return (eta - theta) % 360.0, B0


def res_class(dx, dy):
    if not (isinstance(dx, float) and isinstance(dy, float)):
        return "R0"
    for name, cond in (("R1", dx < 11 and dy < 15), ("R2", 11 <= dx <= 14 and dy >= 18),
                       ("R3", dx >= 13.5 and 15 <= dy <= 19)):
        if cond:
            return name
    return "R0"


def epoch(name, h, day):
    if Path(name).name.lower().startswith("mp00_5250"):
        m = h.get("MRKMOD")
        return {0: "E1", 256: "E2", 1280: "E3", 1281: "E4", 1282: "E5", 1283: "E6"}.get(int(m), "unassigned") \
            if isinstance(m, float) else "unassigned"
    return "E7" if day < datetime(1996, 4, 10) else "E8"


def magnetograms(archive=MWO_DATA, years=range(1974, 2014)):
    rows = []
    for y in years:
        p = Path(archive) / f"MWO_{y}.tar.gz"
        try:
            tf = tarfile.open(p)
        except (tarfile.TarError, OSError, EOFError):
            continue
        with tf:
            for m in tf:
                if not (m.isfile() and is_fe(m.name)):
                    continue
                d = name_day(m.name, y)
                if d is None:
                    continue
                try:
                    h, _, _ = header_and_data(tf.extractfile(m).read())
                except Exception:                                  # noqa: BLE001
                    continue
                if not isinstance(h.get("TAVG-UT"), float):
                    continue
                ot = d + timedelta(hours=h["TAVG-UT"])
                L0, B0 = meeus(ot)
                dcen = (h["CENLON"] - L0 + 180) % 360 - 180
                db0 = math.degrees(h["B0"]) - B0
                rows.append(dict(year=y, member=m.name, day=ot.strftime("%Y-%m-%d"), ot=ot, tavg=h["TAVG-UT"],
                                 dcen=dcen, db0=db0, eph=abs(dcen) <= CENLON_TOL and abs(db0) <= B0_TOL,
                                 border=abs(abs(dcen) - CENLON_TOL) < BORDER_CEN or abs(abs(db0) - B0_TOL) < BORDER_B0,
                                 cls=res_class(h.get("DXB_OBS"), h.get("DYB_OBS")), epoch=epoch(m.name, h, ot)))
    return rows


# ---------------------------------------------------------------- measurement (own geometry)

def geom(h, shape):
    yy, xx = np.indices(shape, dtype=float)
    xi, eta = (xx + 1 - h["X0"]) / h["R0"], (yy + 1 - h["Y0"]) / h["R0"]
    r2 = xi ** 2 + eta ** 2
    mu = np.where(r2 < 0.999, np.sqrt(np.clip(1 - r2, 0, None)), np.nan)
    cb, sb = math.cos(h["B0"]), math.sin(h["B0"])
    lat = np.degrees(np.arcsin(np.clip(mu * sb + eta * cb, -1, 1)))
    lon = (h["CENLON"] + np.degrees(np.arctan2(xi, mu * cb - eta * sb))) % 360
    return lat, lon, mu


def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def centroid(lon, lat, w):
    v = (unit(lon, lat) * w[:, None]).sum(0)
    return math.degrees(math.atan2(v[1], v[0])) % 360, math.degrees(math.asin(v[2] / np.linalg.norm(v)))


def tilt_p1(cp, cn):
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import geometry as geo        # shared definition of the tilt angle (P1 convention)
    t = geo.tilt_deg(cn, cp)
    lead, foll = (cp, cn) if abs(t) < 90 else (cn, cp)
    return geo.tilt_deg(lead, foll), (1 if abs(t) < 90 else -1)


def measure(h, B, blank, g, lat0, lon0):
    lat, lon, mu = g
    win = np.isfinite(mu) & (np.abs(lat - lat0) <= WIN_LAT) & (np.abs((lon - lon0 + 180) % 360 - 180) <= WIN_LON)
    if not win.any():
        return dict(status="window_off_disk")
    if np.nanmin(mu[win]) < MU_MIN:
        return dict(status="window_outside_mu_domain")
    nb = int((blank & win).sum())
    if nb > BLANK_MAX * int(win.sum()):
        return dict(status="window_blank")
    br = np.where(blank, np.nan, B) / mu
    el = win & np.isfinite(br) & (np.abs(br) <= BMAX)
    pos, neg = el & (br >= THR), el & (br <= -THR)
    w = np.abs(br) * (RSUN / h["R0"]) ** 2 / mu
    if not (pos.any() and neg.any()):
        return dict(status="no_two_polarities")
    both = pos | neg
    cp, cn = centroid(lon[pos], lat[pos], w[pos]), centroid(lon[neg], lat[neg], w[neg])
    t, lead = tilt_p1(cp, cn)
    lat_bar = float((lat[both] * w[both]).sum() / w[both].sum())
    return dict(status="ok", tilt=t, lead=lead, lat_bar=lat_bar, phi=float(w[pos].sum() + w[neg].sum()), nb=nb)


def carrington_number(t):
    """Own Carrington rotation number of an instant: fraction of rotation from the Meeus longitude L0 of the disc
    centre (L0 = 360 at the start of a rotation, decreasing), integer from the mean synodic period."""
    from astropy.time import Time
    L0, _ = meeus(t)
    frac = ((360.0 - L0) % 360.0) / 360.0
    approx = (Time(t, scale="utc").jd - 2398140.2270) / 27.2752316
    return int(round(approx - frac)), min(L0, 360.0 - L0)


# ---------------------------------------------------------------- rebuild

def rebuild(dpd=DPD, archive=MWO_DATA, years=range(1974, 2014)):
    gr = groups(dpd)
    nbr = isolation(gr)
    mags = magnetograms(archive, years)
    by_day = {}
    for m in mags:
        by_day.setdefault(m["day"], []).append(m)
    rank = {"R1": 0, "R2": 1, "R3": 2, "R0": 3}
    att = {}
    for k, r in gr.items():
        if not (D0 <= r["day"] < D1 and r["area"] >= 1 and abs(r["lat"]) <= 45):
            continue
        ok = [m for m in by_day.get(r["day"], []) if m["eph"] and m["epoch"] != "unassigned"]
        best = min(ok, key=lambda m: (rank[m["cls"]], abs((m["ot"] - r["t"]).total_seconds()), m["tavg"], m["member"])) \
            if ok else None
        att[k] = dict(r, iso=nbr[k] == 0, nbr=nbr[k], mag=best, border=any(m["border"] for m in by_day.get(r["day"], [])))
    need = {}
    for k, a in att.items():
        if a["mag"]:
            need.setdefault((a["mag"]["year"], a["mag"]["member"]), []).append(k)
    for y in sorted({y for y, _ in need}):
        wanted = {m for yy, m in need if yy == y}
        with tarfile.open(Path(archive) / f"MWO_{y}.tar.gz") as tf:
            for m in tf:
                if m.name in wanted:
                    h, B, blank = header_and_data(tf.extractfile(m).read())
                    g = geom(h, B.shape)
                    for k in need[(y, m.name)]:
                        att[k]["m"] = measure(h, B, blank, g, att[k]["lat"], att[k]["lon"])
    recs = {}
    for set_name in ("isolated", "all"):
        per = {}
        for k, a in att.items():
            if a["mag"] and (set_name == "all" or a["iso"]):
                per.setdefault(a["noaa"], []).append(a)
        for noaa, lst in per.items():
            lst.sort(key=lambda a: (abs(a["lcm"]), a["day"]))
            for i, a in enumerate(lst, 1):
                if a["m"]["status"] == "ok":
                    recs[(set_name, noaa)] = dict(a, rank=i, n_cand=len(lst))
                    break
    return att, recs


def activities(dpd=DPD, silso_tot=ROOT / "ancillary/SILSO_TOT/SN_m_tot_V2.0.txt",
               silso_hem=ROOT / "ancillary/SILSO_HEMI/SN_m_hem_V2.0.csv"):
    """Own monthly hemispheric activities, normalised by their mean: A_main (DPD group areas over observed days, all
    group rows with valid positions), A_own (only Gyula/Debrecen days), A_silso_hem (1992-2012), A_silso_split (SILSO
    total times the DPD area fraction of the month, 0.5 when the month has no area)."""
    days, src = [], {}
    for line in (Path(dpd) / "dailyDPD1974_2016.txt").read_text().splitlines():
        t = line.split()
        if line.startswith("d ") and len(t) >= 12:
            d = f"{t[1]}-{t[2]}-{t[3]}"
            if D0 <= d < D1:
                days.append(d)
                src[d] = t[7]
    tot = {d: {"N": 0.0, "S": 0.0} for d in days}
    for (d, _), r in groups(dpd).items():
        if d in tot:
            tot[d]["N" if r["lat"] >= 0 else "S"] += r["area"]
    df = pd.DataFrame.from_dict(tot, orient="index")[["N", "S"]]
    df.index = pd.to_datetime(df.index)
    m = df.groupby(df.index.to_period("M")).mean()
    own = df[[src[d.strftime("%Y-%m-%d")] in ("GYUL", "DEBR") for d in df.index]]
    mo = own.groupby(own.index.to_period("M")).mean().reindex(m.index)
    sn = {}
    for line in Path(silso_tot).read_text().splitlines():
        f = line.split()
        if len(f) >= 4:
            sn[pd.Period(f"{int(f[0])}-{int(f[1]):02d}", "M")] = float(f[3])
    snm = pd.Series(sn).reindex(m.index)
    t_ = m.N + m.S
    fn = (m.N / t_).where(t_ > 0, 0.5)
    split = pd.DataFrame({"N": snm * fn, "S": snm * (1 - fn)})
    hem = {}
    for line in Path(silso_hem).read_text().splitlines():
        f = line.split(";")
        if len(f) >= 6:
            per = pd.Period(f"{int(f[0])}-{int(f[1]):02d}", "M")
            if pd.Period("1992-01", "M") <= per <= pd.Period("2012-12", "M"):
                hem[per] = {"N": float(f[4]), "S": float(f[5])}
    h = pd.DataFrame.from_dict(hem, orient="index").replace(-1.0, np.nan)
    return dict(A_main=m / m.mean(), A_own=mo / mo.mean(), A_silso_hem=(h / h.mean()).reindex(m.index),
                A_silso_split=split / split.mean())


# ---------------------------------------------------------------- comparison with the runner products

def check(cat=CAT, out=OUT, dpd=DPD, archive=MWO_DATA, years=range(1974, 2014), write=True, **act_kw):
    design = pd.read_csv(Path(cat) / "DESIGN.csv", dtype={"noaa": str})
    attempts = pd.read_csv(Path(cat) / "ATTEMPTS.csv.gz", dtype={"noaa": str})
    sealed = pd.read_csv(Path(cat) / "SEALED.csv.gz", dtype={"noaa": str})
    meta = json.loads((Path(cat) / "META.json").read_text())
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    ok("product hashes", all(hashlib.sha256((Path(cat) / n).read_bytes()).hexdigest() == h
                             for n, h in meta["products_sha256"].items()))
    ok("multiplicity: one attempt per (day, group), one design and one sealed row per (set, group), same keys",
       not attempts.duplicated(["day", "noaa"]).any() and not design.duplicated(["record_set", "noaa"]).any()
       and not sealed.duplicated(["record_set", "noaa"]).any()
       and set(zip(design.record_set, design.noaa)) == set(zip(sealed.record_set, sealed.noaa)))
    required_design = ("lat_bar", "sinlat", "phi_mwo", "dpd_lat", "dpd_lon", "lcm", "abs_lcm", "CR", "cycle",
                       "rank", "n_cand", "n_neighbours", "dpd_area", "n_blank_win")
    required_sealed = ("tilt_deg", "gamma_deg", "leading_sign", "lon_pos", "lat_pos", "lon_neg", "lat_neg",
                       "sep_deg", "hale_expected")
    finite = (np.isfinite(design[list(required_design)].to_numpy(dtype=float)).all()
              and np.isfinite(sealed[list(required_sealed)].to_numpy(dtype=float)).all())
    ok("mandatory numeric design and sealed fields are finite", finite)
    if not finite:
        if write:
            Path(out).mkdir(parents=True, exist_ok=False)
            (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
                checks=res, passed=sum(r["ok"] for r in res), total=len(res), partial=True,
                reason="non-finite mandatory measurement"), indent=2) + "\n")
        return False
    same_day = (pd.to_datetime(design.obs_time, format="ISO8601").dt.strftime("%Y-%m-%d") == design.day)
    am = attempts[attempts.member.notna()]
    same_day_att = (pd.to_datetime(am.obs_time, format="ISO8601").dt.strftime("%Y-%m-%d") == am.day)
    ok("same UTC day: MWO instant and DPD day coincide for every record and every attempt with a magnetogram",
       same_day.all() and same_day_att.all(), f"{int((~same_day).sum())} records, {int((~same_day_att).sum())} attempts differ")
    att, recs = rebuild(dpd, archive, years)
    border = {k for k, a in att.items() if a["border"]}
    mine = {k: ("no_magnetogram" if a["mag"] is None else a["m"]["status"]) for k, a in att.items()}
    theirs = {(r.day, r.noaa): r.status for r in attempts.itertuples()}
    diff = {k for k in set(mine) | set(theirs) if mine.get(k) != theirs.get(k)}
    ok("candidate days and status of every attempt", not diff and len(mine) == len(theirs),
       f"{len(mine)} mine, {len(theirs)} runner, {len(diff)} differ ({len(diff & border)} on ephemeris-borderline days)")
    mem = {(r.day, r.noaa): r.member for r in attempts.itertuples() if isinstance(r.member, str)}
    nbw = {(r.day, r.noaa): r.n_blank_win for r in attempts.itertuples()}
    dm = {k for k, a in att.items() if a["mag"] and mem.get(k) != a["mag"]["member"]}
    ok("chosen magnetogram of every candidate day", not dm, f"{len(dm)} differ ({len(dm & border)} borderline)")
    keys_r = {(r.record_set, r.noaa) for r in design.itertuples()}
    ok("record sets (isolated, all): same groups", keys_r == set(recs), f"runner {len(keys_r)}, mine {len(recs)}")
    acts = activities(dpd, **act_kw)
    worst = dict(lat=0.0, sinlat=0.0, phi=0.0, tilt=0.0, gamma=0.0, A=0.0, pos=0.0)
    bad = {c: 0 for c in ("categorical", "CR", "cycle", "blank", "time", "activity_nan")}
    cr_border, bad_lead, n, bad_keys = 0, 0, 0, set()
    sx = sealed.set_index(["record_set", "noaa"])
    for r in design.itertuples():
        k = (r.record_set, r.noaa)
        if k not in recs:
            continue
        a = recs[k]
        m = a["m"]
        hem = "N" if m["lat_bar"] >= 0 else "S"
        cat_mine = (a["day"], a["mag"]["member"], a["mag"]["epoch"], a["mag"]["cls"], hem, a["rank"], a["n_cand"],
                    bool(a["iso"]), a["nbr"], a["area"])
        cat_run = (r.day, r.member, r.epoch, r.res_class, r.hemisphere, r.rank, r.n_cand, bool(r.isolated),
                   r.n_neighbours, r.dpd_area)
        if cat_mine != cat_run:
            bad["categorical"] += 1
            bad_keys.add((a["day"], a["noaa"]))
        cyc = 20
        for c_, d_ in ((21, "1976-03-01"), (22, "1986-09-01"), (23, "1996-08-01"), (24, "2008-12-01")):
            if a["day"] >= d_:
                cyc = c_
        bad["cycle"] += int(cyc != r.cycle)
        crn, dist = carrington_number(a["mag"]["ot"])
        if crn != r.CR:
            if dist < 0.1:                         # within ~11 minutes of a rotation start: reported as borderline
                cr_border += 1
            else:
                bad["CR"] += 1
        bad["blank"] += int(m["nb"] != r.n_blank_win or nbw.get((a["day"], a["noaa"])) != r.n_blank_win)
        bad["time"] += int(pd.Timestamp(r.obs_time) != pd.Timestamp(a["mag"]["ot"]))
        worst["lat"] = max(worst["lat"], abs(m["lat_bar"] - r.lat_bar))
        worst["sinlat"] = max(worst["sinlat"], abs(math.sin(math.radians(abs(m["lat_bar"]))) - r.sinlat))
        worst["phi"] = max(worst["phi"], abs(m["phi"] / r.phi_mwo - 1))
        worst["pos"] = max(worst["pos"], abs(a["lat"] - r.dpd_lat), abs((a["lon"] - r.dpd_lon + 180) % 360 - 180),
                           abs(a["lcm"] - r.lcm), abs(abs(a["lcm"]) - r.abs_lcm))
        per = pd.Period(r.day[:7], "M")
        for name, tab in acts.items():
            v = tab.at[per, hem] if per in tab.index else np.nan
            w = getattr(r, name)
            if np.isfinite(v) != np.isfinite(w):
                bad["activity_nan"] += 1
            elif np.isfinite(v):
                worst["A"] = max(worst["A"], abs(v - w))
        s_ = sx.loc[k]
        worst["tilt"] = max(worst["tilt"], abs((m["tilt"] - s_.tilt_deg + 180) % 360 - 180))
        g = math.copysign(1.0, m["lat_bar"]) * math.degrees(math.asin(math.sin(math.radians(m["tilt"]))))
        worst["gamma"] = max(worst["gamma"], abs(g - s_.gamma_deg))
        bad_lead += int(m["lead"] != s_.leading_sign)
        n += 1
    ok("design: day, member, epoch, class, hemisphere, rank, candidates, isolation, neighbours, DPD area",
       bad["categorical"] == 0, f"{bad['categorical']} rows differ of {n}")
    ok("design: Carrington rotation of the full instant, cycle, observation time, BLANK count",
       bad["CR"] == 0 and bad["cycle"] == 0 and bad["time"] == 0 and bad["blank"] == 0,
       f"CR {bad['CR']} (+{cr_border} within 0.1 deg of a rotation start), cycle {bad['cycle']}, time {bad['time']}, "
       f"BLANK {bad['blank']}")
    ok("design: lat_bar, sin|lat|, flux, DPD position and LCM",
       worst["lat"] < 1e-6 and worst["sinlat"] < 1e-9 and worst["phi"] < 1e-9 and worst["pos"] < 1e-9,
       f"max |dlat| {worst['lat']:.1e}, |dsin| {worst['sinlat']:.1e}, rel flux {worst['phi']:.1e}, pos {worst['pos']:.1e}")
    ok("design: main activity and the three sensitivity activities", worst["A"] < 1e-12 and bad["activity_nan"] == 0,
       f"max |dA| {worst['A']:.1e}, missing-value mismatches {bad['activity_nan']}")
    ok("sealed tilt, gamma and leading sign (compared automatically, values not shown)",
       worst["tilt"] < 1e-6 and worst["gamma"] < 1e-6 and bad_lead == 0,
       f"max |dtilt| {worst['tilt']:.1e}, max |dgamma| {worst['gamma']:.1e}, leading mismatches {bad_lead}")
    unresolved = len(diff & border) + len(dm & border) + cr_border
    ok("no unresolved difference on ephemeris-borderline days or at rotation starts", unresolved == 0,
       f"{unresolved} (if not zero, this receipt is a PARTIAL check)")
    partial = unresolved > 0
    if write:
        Path(out).mkdir(parents=True, exist_ok=False)
        (Path(out) / "RECEIPT.json").write_text(json.dumps(dict(
            checks=res, passed=sum(r["ok"] for r in res), total=len(res), partial=partial,
            catalogue_meta_sha256=hashlib.sha256((Path(cat) / "META.json").read_bytes()).hexdigest(),
            n_borderline_days=len(border), n_unresolved_borderline=unresolved), indent=2) + "\n")
    return all(r["ok"] for r in res)


def selftest():
    """End to end: run the runner's own selftest archive builder is not available here (independence), so a small
    synthetic archive is built here, the runner is executed on it in a subprocess, and check() must pass; then a
    tampered sealed file must fail."""
    import io
    import subprocess
    import tempfile
    from astropy.io import fits
    res = []

    def ok(n, c, v=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    L0, B0 = meeus(datetime(2011, 6, 1, 18))
    ok("own ephemeris: Carrington longitude and B0 in range", 0 <= L0 < 360 and abs(B0) <= 7.26, (round(L0, 2), round(B0, 3)))
    ok("own classes and epochs", [res_class(9.6, 13.1), res_class(12.9, 20.1), res_class(14.0, 17.4), res_class(None, 1.0)]
       == ["R1", "R2", "R3", "R0"] and epoch("x/MP00_5250078_a.fits", {"MRKMOD": 1283.0}, datetime(1994, 1, 1)) == "E6"
       and epoch("x/m960413_0fe1.fits", {}, datetime(1996, 4, 13)) == "E8")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        days = [datetime(1990, 5, d, 18) for d in (1, 2, 3)]
        lcm = {1: -18.0, 2: -10.0, 3: 2.0}
        lines, files = [], []
        for d in days:
            L0, B0 = meeus(d)
            lon0 = (L0 + lcm[d.day]) % 360
            n, R = 512, 240.0
            h = dict(X0=256.5, Y0=256.5, R0=R, B0=math.radians(B0), CENLON=L0)
            lat, lon, mu = geom(h, (n, n))
            B = np.zeros((n, n))
            for dl, db, sg in ((3.0, -0.4, 1.0), (-3.0, 0.4, -1.0)):
                lo, la = lon0 + dl / math.cos(math.radians(12)), 12.0 + db
                dd = np.degrees(np.arccos(np.clip(np.sin(np.radians(lat)) * math.sin(math.radians(la)) + np.cos(np.radians(lat))
                                                  * math.cos(math.radians(la)) * np.cos(np.radians(lon - lo)), -1, 1)))
                B += sg * 800 * np.exp(-0.5 * (dd / 1.2) ** 2)
            B = np.nan_to_num(B * mu)
            if d.day == 3:
                B = np.abs(B)
            raw = np.round(B / 0.1).clip(-32767, 32767).astype(np.int16)
            hdr = fits.Header()
            for k, v in dict(h, MRKMOD=1282, DXB_OBS=9.6, DYB_OBS=13.0).items():
                hdr[k] = v
            hdr["TAVG-UT"] = 18.0
            hdu = fits.PrimaryHDU(raw, hdr)
            hdu.header["BSCALE"], hdu.header["BZERO"], hdu.header["BLANK"] = 0.1, 0.0, -32768
            buf = io.BytesIO()
            hdu.writeto(buf)
            files.append((f"1990/MP00_5250078_00_09005{d.day:02d}_1800.fits", buf.getvalue()))
            for noaa, dlat, dlon in (("6000", 0.0, 0.0), ("6001", 3.0, 4.0)):
                if noaa == "6001" and d.day != 2:
                    continue
                ln = list(" " * 93)
                for col, txt in ((0, f"g {d:%Y %m %d} 09 00 00"), (22, f"{noaa:>6}"), (53, f"{150:5d}"),
                                 (59, f"{12.0 + dlat:6.2f}"), (66, f"{(lon0 + dlon) % 360:6.2f}"), (73, f"{lcm[d.day] + dlon:6.2f}")):
                    ln[col:col + len(txt)] = list(txt)
                lines.append("".join(ln))
        with tarfile.open(td / "MWO_1990.tar.gz", "w:gz") as tf:
            for name, data in files:
                ti = tarfile.TarInfo(name)
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
        for y in range(1974, 2013):
            (td / f"gDPD{y}.txt").write_text("\n".join(lines) + "\n" if y == 1990 else "")
        (td / "dailyDPD1974_2016.txt").write_text("".join(f"d {d:%Y %m %d} 09 00 00 GYUL   10  100   10  100 0 0 0\n" for d in days))
        (td / "tot.txt").write_text("1990 04 1990.288  100.0  9.0  400 1\n1990 05 1990.371  140.0 10.0  500 1\n")
        (td / "hem.csv").write_text("1990;05;1990.371;140.0;80.0;60.0;1;1;1;9;9;9;1\n1993;05;1993.371;60.0;30.0;30.0;1;1;1;9;9;9;1\n")
        code = f"""
import sys, json, hashlib, importlib.util
from pathlib import Path
sys.argv = ['x']
s = importlib.util.spec_from_file_location('c', {str(ROOT / 'scripts/t3_mwo_catalogue.py')!r})
C = importlib.util.module_from_spec(s); s.loader.exec_module(C)
td = Path({str(td)!r}); out = td / 'cat'; out.mkdir()
ga = C.dpd_groups(td); mg = C.magnetogram_table(td, years=[1990])
att, design, sealed, loss, cov = C.build(ga, mg, archive_dir=td, dpd_dir=td, silso_tot=td / 'tot.txt', silso_hem=td / 'hem.csv')
design.to_csv(out / 'DESIGN.csv', index=False); sealed.to_csv(out / 'SEALED.csv.gz', index=False)
att.to_csv(out / 'ATTEMPTS.csv.gz', index=False)
h = {{f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()}}
(out / 'META.json').write_text(json.dumps(dict(products_sha256=h)))
"""
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok("runner executed on the synthetic archive", r.returncode == 0, r.stderr[-300:] if r.returncode else "")
        if r.returncode == 0:
            kw = dict(silso_tot=td / "tot.txt", silso_hem=td / "hem.csv")
            good = check(td / "cat", td / "r1", dpd=td, archive=td, years=[1990], write=False, **kw)
            ok("check() passes on the runner outputs", good)
            s = pd.read_csv(td / "cat/SEALED.csv.gz", dtype={"noaa": str})
            s.loc[0, "tilt_deg"] += 0.5
            s.to_csv(td / "cat/SEALED.csv.gz", index=False)
            meta = json.loads((td / "cat/META.json").read_text())
            meta["products_sha256"]["SEALED.csv.gz"] = hashlib.sha256((td / "cat/SEALED.csv.gz").read_bytes()).hexdigest()
            (td / "cat/META.json").write_text(json.dumps(meta))
            ok("check() fails on a tampered sealed tilt", not check(td / "cat", td / "r2", dpd=td, archive=td, years=[1990],
                                                                   write=False, **kw))
            s.loc[0, "tilt_deg"] -= 0.5
            s.to_csv(td / "cat/SEALED.csv.gz", index=False)
            clean = pd.read_csv(td / "cat/DESIGN.csv", dtype={"noaa": str})
            for col, delta in (("CR", 1), ("cycle", 1), ("sinlat", 0.01), ("n_blank_win", 3), ("A_own", 0.1),
                               ("A_silso_split", 0.1)):
                d2 = clean.copy()
                d2.loc[0, col] = d2.loc[0, col] + delta
                d2.to_csv(td / "cat/DESIGN.csv", index=False)
                meta["products_sha256"]["DESIGN.csv"] = hashlib.sha256((td / "cat/DESIGN.csv").read_bytes()).hexdigest()
                meta["products_sha256"]["SEALED.csv.gz"] = hashlib.sha256((td / "cat/SEALED.csv.gz").read_bytes()).hexdigest()
                (td / "cat/META.json").write_text(json.dumps(meta))
                ok(f"check() fails on a tampered design column {col}",
                   not check(td / "cat", td / "r3", dpd=td, archive=td, years=[1990], write=False, **kw))
            clean.to_csv(td / "cat/DESIGN.csv", index=False)
            clean_sealed = pd.read_csv(td / "cat/SEALED.csv.gz", dtype={"noaa": str})
            for filename, column, value in (("DESIGN.csv", "sinlat", np.nan),
                                            ("DESIGN.csv", "phi_mwo", np.inf),
                                            ("SEALED.csv.gz", "gamma_deg", np.nan),
                                            ("SEALED.csv.gz", "tilt_deg", np.inf)):
                clean.to_csv(td / "cat/DESIGN.csv", index=False)
                clean_sealed.to_csv(td / "cat/SEALED.csv.gz", index=False)
                altered = (clean if filename == "DESIGN.csv" else clean_sealed).copy()
                altered.loc[0, column] = value
                altered.to_csv(td / "cat" / filename, index=False)
                # Recompute the hashes so this tests the independent numeric check.
                for name in ("DESIGN.csv", "SEALED.csv.gz"):
                    meta["products_sha256"][name] = hashlib.sha256((td / "cat" / name).read_bytes()).hexdigest()
                (td / "cat/META.json").write_text(json.dumps(meta))
                ok(f"check() rejects non-finite {column} in {filename}",
                   not check(td / "cat", td / "r4", dpd=td, archive=td, years=[1990], write=False, **kw))
                if column == "sinlat":
                    failed = not check(td / "cat", td / "nonfinite_receipt", dpd=td, archive=td,
                                       years=[1990], write=True, **kw)
                    receipt = json.loads((td / "nonfinite_receipt/RECEIPT.json").read_text())
                    ok("non-finite measurements produce a failed partial receipt",
                       failed and receipt["partial"] and receipt["passed"] < receipt["total"])
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
