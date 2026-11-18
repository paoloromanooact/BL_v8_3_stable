"""Independent recount of the MWO tilt pilot (does not import scripts/mwo_pilot_tilt.py nor the MWO pipeline).

Re-reads every evaluable magnetogram from the MWO archives, rebuilds the heliographic mapping from the documented
convention (xi = (x+1-X0)/R0, eta = (y+1-Y0)/R0, n = (mu cos B0 - eta sin B0, xi, mu sin B0 + eta cos B0)), the window,
the B_r cuts, the polarity centroids (unit vectors) and the P1 tilt convention, then recomputes the differences with P1,
the summaries and the criterion from ROWS.csv. Writes results/MWO_PILOT_RECOUNT/RECEIPT.json.

    .venv/bin/python scripts/mwo_pilot_recount.py --selftest
    .venv/bin/python scripts/mwo_pilot_recount.py --check
"""
import argparse
import hashlib
import json
import math
import sys
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "results/MWO_PILOT"
OUT = ROOT / "results/MWO_PILOT_RECOUNT"
MWO_DATA = Path("/storage/shared/gianluca/MWO_project/Desktop/MWO/data MWO")
WIN_LAT, WIN_LON, THR, BMAX, MU_MIN, RSUN = 6.0, 8.0, 50.0, 4000.0, 0.8, 6.96e10


def read_fits(buf):
    """Minimal primary-HDU reader (own implementation)."""
    cards, pos = [], 0
    while True:
        block = buf[pos:pos + 2880]
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
    n1, n2, bp = int(h["NAXIS1"]), int(h["NAXIS2"]), int(h["BITPIX"])
    dt = {16: ">i2", 32: ">i4", -32: ">f4", -64: ">f8"}[bp]
    a = np.frombuffer(buf[pos:pos + n1 * n2 * abs(bp) // 8], dtype=dt).astype(float).reshape(n2, n1)
    return h, a * h.get("BSCALE", 1.0) + h.get("BZERO", 0.0)


def unit(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def centroid(lon, lat, w):
    v = (unit(lon, lat) * w[:, None]).sum(0)
    return math.degrees(math.atan2(v[1], v[0])) % 360, math.degrees(math.asin(v[2] / np.linalg.norm(v)))


def measure(h, B, lat0, lon0):
    yy, xx = np.indices(B.shape, dtype=float)
    xi, eta = (xx + 1 - h["X0"]) / h["R0"], (yy + 1 - h["Y0"]) / h["R0"]
    r2 = xi ** 2 + eta ** 2
    mu = np.where(r2 < 0.999, np.sqrt(np.clip(1 - r2, 0, None)), np.nan)
    cb, sb = math.cos(h["B0"]), math.sin(h["B0"])
    lat = np.degrees(np.arcsin(np.clip(mu * sb + eta * cb, -1, 1)))
    lon = (h["CENLON"] + np.degrees(np.arctan2(xi, mu * cb - eta * sb))) % 360
    dl = (lon - lon0 + 180) % 360 - 180
    win = np.isfinite(mu) & (np.abs(lat - lat0) <= WIN_LAT) & (np.abs(dl) <= WIN_LON)
    if not win.any() or np.nanmin(mu[win]) < MU_MIN:
        return None
    br = B / mu
    el = win & np.isfinite(br) & (np.abs(br) <= BMAX)
    pos, neg = el & (br >= THR), el & (br <= -THR)
    if not (pos.any() and neg.any()):
        return None
    w = np.abs(br) * (RSUN / h["R0"]) ** 2 / mu
    cp, cn = centroid(lon[pos], lat[pos], w[pos]), centroid(lon[neg], lat[neg], w[neg])
    return dict(cp=cp, cn=cn, flux=float(w[pos].sum() + w[neg].sum()))


def p1_tilt_convention(cp, cn):
    """Leading = westernmost polarity (|tilt(neg->pos)| < 90 means positive leads), as in P1."""
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import geometry as geo   # shared definition of the tilt angle (P1 convention)
    t_np = geo.tilt_deg(cn, cp)
    lead, follow = (cp, cn) if abs(t_np) < 90 else (cn, cp)
    return geo.tilt_deg(lead, follow), (1 if abs(t_np) < 90 else -1)


def check():
    rows = pd.read_csv(PILOT / "ROWS.csv")
    meta = json.loads((PILOT / "META.json").read_text())
    res = []

    def ok(n, c, v=""):
        res.append(dict(name=n, ok=bool(c), value=str(v)))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {v}")
    ok("pilot product hashes", all(hashlib.sha256((PILOT / n).read_bytes()).hexdigest() == h
                                   for n, h in meta["products_sha256"].items()))
    ev = rows[rows.status == "ok"].copy()
    worst_t, worst_f, n = 0.0, 0.0, 0
    for year, g in ev.groupby(ev.member.str.slice(0, 4)):
        names = set(g.member)
        with tarfile.open(MWO_DATA / f"MWO_{year}.tar.gz") as tf:
            blobs = {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.name in names}
        for r in g.itertuples():
            h, B = read_fits(blobs[r.member])
            m = measure(h, B, r.dpd_lat, r.dpd_lon)
            if m is None:
                worst_t = 999.0
                continue
            t, lead = p1_tilt_convention(m["cp"], m["cn"])
            worst_t = max(worst_t, abs(((t - r.mwo_tilt_deg) + 180) % 360 - 180))
            worst_f = max(worst_f, abs(m["flux"] / (r.mwo_flux_pos_mx + r.mwo_flux_neg_mx) - 1))
            n += 1
    ok("every evaluable record re-measured from its FITS with own geometry", worst_t < 1e-6 and worst_f < 1e-9,
       f"{n} records, max |dtilt| {worst_t:.1e} deg, max rel flux {worst_f:.1e}")
    d = rows.dropna(subset=["d_gamma"])
    dax = ((d.mwo_tilt_deg - d.p1_tilt) + 90) % 180 - 90
    ok("d_ax and d_gamma recomputed", np.allclose(dax, d.d_ax, atol=1e-9) and
       np.allclose(np.sign(d.p1_lat) * dax, d.d_gamma, atol=1e-9))
    summ = pd.read_csv(PILOT / "SUMMARY.csv").set_index("group")
    for grp, sub in (("all", d), ("N", d[d.hemisphere == "N"]), ("S", d[d.hemisphere == "S"])):
        ok(f"summary {grp}: n, median d_gamma, median |d_ax|, leading agreement",
           summ.loc[grp, "n"] == len(sub) and abs(summ.loc[grp, "d_gamma_median"] - np.median(sub.d_gamma)) < 1e-12
           and abs(summ.loc[grp, "abs_d_ax_median"] - np.median(np.abs(sub.d_ax))) < 1e-12
           and abs(summ.loc[grp, "leading_agree"] - sub.leading_agree.mean()) < 1e-12)
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "RECEIPT.json").write_text(json.dumps(dict(checks=res, passed=sum(r["ok"] for r in res), total=len(res)),
                                                 indent=2) + "\n")
    return all(r["ok"] for r in res)


def selftest():
    # own reader and mapping against a synthetic disk: centre pixel at (B0, CENLON)
    h = dict(X0=256.5, Y0=256.5, R0=240.0, B0=math.radians(5), CENLON=100.0, NAXIS1=512, NAXIS2=512)
    yy, xx = np.indices((512, 512), dtype=float)
    xi, eta = (xx + 1 - h["X0"]) / h["R0"], (yy + 1 - h["Y0"]) / h["R0"]
    j, i = 255, 255
    mu0 = math.sqrt(1 - xi[j, i] ** 2 - eta[j, i] ** 2)
    lat0 = math.degrees(math.asin(mu0 * math.sin(h["B0"]) + eta[j, i] * math.cos(h["B0"])))
    c1 = abs(lat0 - 5) < 0.3
    # FITS reader round trip
    from astropy.io import fits
    import io
    buf = io.BytesIO()
    hd = fits.Header()
    hd["X0"] = 256.5
    fits.PrimaryHDU(np.arange(6, dtype=np.float32).reshape(2, 3), hd).writeto(buf)
    hh, a = read_fits(buf.getvalue())
    c2 = hh["X0"] == 256.5 and a.shape == (2, 3) and a[1, 2] == 5
    for n, c in (("own mapping: disk centre at latitude B0", c1), ("own FITS reader round trip", c2)):
        print(f"[{'OK' if c else 'FALLITO'}] {n}")
    return c1 and c2


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if (a.selftest and selftest()) or (a.check and check()) else 1)
