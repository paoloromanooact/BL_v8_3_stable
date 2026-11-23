"""MDI pilot, phase 1: identity of the shared window measurement (python/sharpbl/tilt_window.py) with MWO.

Frozen protocol docs/PROTOCOL_MDI_TILT_PILOT.md §4: with the MWO reader, geometry, thresholds (50/4000 G), pixel
area and reading precision (not the MDI 10-pixel filter), the shared module must reproduce
  - the MWO pilot records already measured (results/MWO_PILOT/ROWS.csv; pilot rule: no BLANK handling), and
  - a deterministic R4 subset of the verified release: per epoch x hemisphere the two records with the lowest NOAA,
    plus up to three with n_blank_window > 0 if present (none in R4: the absence is declared),
within tilt/angles 1e-6 deg, flux 1e-9 relative, exact counts and statuses. MWO FITS are read from the archives;
no MWO source or product is modified. MWO-specific pieces (reader, geometry, BLANK value) are imported read-only.

    .venv/bin/python scripts/mdi_pilot_mwo_identity.py --selftest
    .venv/bin/python scripts/mdi_pilot_mwo_identity.py --run
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import tilt_window as tw  # noqa: E402

_spec = importlib.util.spec_from_file_location("t3_mwo_catalogue", ROOT / "scripts/t3_mwo_catalogue.py")
CAT = importlib.util.module_from_spec(_spec)
sys.modules["t3_mwo_catalogue"] = CAT
_spec.loader.exec_module(CAT)
P, MP = CAT.P, CAT.MP

PROTOCOL = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT.md"
FREEZE = ROOT / "docs/PROTOCOL_MDI_TILT_PILOT_FREEZE.json"
PILOT_ROWS = ROOT / "results/MWO_PILOT/ROWS.csv"
RELEASE = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE/MWO_TILT_CATALOGUE_ISOLATED_1974_2012.csv"
ATTEMPTS = ROOT / "results/T3_MWO_CATALOGUE_R4/ATTEMPTS.csv.gz"
OUT = ROOT / "results/MDI_PILOT_MWO_IDENTITY"
TOL_ANG, TOL_FLUX = 1e-6, 1e-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def measure_mwo(h, B, lat0, lon0, blank_rule):
    """MWO adapter around the shared body: disc and mu checks as MWO, then tilt_window.measure."""
    lat, lon, cmd, mu = P.heliographic(h, B.shape)
    win = tw.window_mask(lat, lon, lat0, lon0, P.WIN_LAT, P.WIN_LON, valid=np.isfinite(mu))
    if not win.any():
        return dict(status="window_off_disk")
    if np.nanmin(mu[win]) < P.MU_MIN:
        return dict(status="window_outside_mu_domain", mu_min=float(np.nanmin(mu[win])))
    if blank_rule:                                   # catalogue R4 (amendment A1)
        blank = CAT.blank_mask(h, B)
        br = np.where(blank, np.nan, B) / mu
        r = tw.measure(lat, lon, br, (P.RSUN_CM / float(h["R0"])) ** 2 / mu, win, bmin=P.THRESH_G, bmax=P.MAX_G,
                       missing=blank, missing_max_frac=CAT.BLANK_FRAC_MAX)
    else:                                            # MWO pilot rule: no BLANK handling
        br = B / mu
        r = tw.measure(lat, lon, br, (P.RSUN_CM / float(h["R0"])) ** 2 / mu, win, bmin=P.THRESH_G, bmax=P.MAX_G,
                       missing=np.zeros(B.shape, bool), missing_max_frac=None)
    r["status"] = {"window_missing": "window_blank"}.get(r["status"], r["status"])
    return r


def r4_subset(release=RELEASE, attempts=ATTEMPTS):
    rel = pd.read_csv(release, dtype={"noaa": str}, float_precision="round_trip")
    rel["noaa_num"] = pd.to_numeric(rel.noaa.str.extract(r"^(\d+)")[0])
    rel = rel.sort_values(["epoch", "hemisphere", "noaa_num", "noaa"])
    sub = rel.groupby(["epoch", "hemisphere"]).head(2)
    blank = rel[rel.n_blank_window > 0].sort_values(["noaa_num", "noaa"]).head(3)
    sub = pd.concat([sub.assign(reason="epoch_hemisphere"), blank.assign(reason="blank")])
    att = pd.read_csv(attempts, dtype={"noaa": str}, usecols=["noaa", "day", "member", "archive_year"], low_memory=False)
    att = att.dropna(subset=["member"]).drop_duplicates(["noaa", "day", "member"])
    sub = sub.merge(att, left_on=["noaa", "day_utc", "mwo_file"], right_on=["noaa", "day", "member"], how="left",
                    validate="one_to_one")
    if sub.archive_year.isna().any():
        raise ValueError("R4 subset rows without archive year")
    return sub.reset_index(drop=True), int(len(blank))


def pilot_rows(path=PILOT_ROWS):
    p = pd.read_csv(path, dtype={"noaa": str}, float_precision="round_trip")
    return p[p.member.notna()].reset_index(drop=True)


def read_members(wanted, archive_dir):
    """wanted: {(archive_year, member)}; returns {(year, member): (h, B)} streaming each archive once."""
    out = {}
    for y in sorted({y for y, _ in wanted}):
        names = {m for yy, m in wanted if yy == y}
        with tarfile.open(Path(archive_dir) / f"MWO_{y}.tar.gz") as tf:
            for m in tf:
                if m.name in names:
                    out[(y, m.name)] = MP.parse_fits_bytes(tf.extractfile(m).read())
    return out


def close(a, b, tol, rel=False):
    a, b = float(a), float(b)
    if np.isnan(a) and np.isnan(b):
        return True
    return abs(a - b) <= (tol * max(abs(b), 1e-300) if rel else tol)


def compare_pilot(r, row):
    if r["status"] != row.mwo_status:
        return False, f"status {r['status']} vs {row.mwo_status}"
    if r["status"] == "window_outside_mu_domain":
        return close(r["mu_min"], row.mwo_mu_min, 1e-12), "mu_min"
    good = int(r["npos"]) == int(row.mwo_npos) and int(r["nneg"]) == int(row.mwo_nneg) \
        and close(r["flux_pos_mx"], row.mwo_flux_pos_mx, TOL_FLUX, True) and close(r["flux_neg_mx"], row.mwo_flux_neg_mx, TOL_FLUX, True)
    if r["status"] == "ok":
        good &= all(close(r[k], row[f"mwo_{k}"], TOL_ANG) for k in ("lon_pos", "lat_pos", "lon_neg", "lat_neg", "tilt_deg", "sep_deg")) \
            and int(r["leading_sign"]) == int(row.mwo_leading_sign)
    return good, "values"


def compare_r4(r, row):
    if r["status"] != "ok":
        return False, f"status {r['status']}"
    good = close(r["tilt_deg"], row.tilt_deg, TOL_ANG) and int(r["leading_sign"]) == int(row.leading_polarity_sign) \
        and all(close(r[a], row[b], TOL_ANG) for a, b in (("lon_pos", "lon_pos_deg"), ("lat_pos", "lat_pos_deg"),
                                                         ("lon_neg", "lon_neg_deg"), ("lat_neg", "lat_neg_deg"),
                                                         ("sep_deg", "separation_deg"), ("lat_bar", "lat_flux_weighted_deg"))) \
        and close(r["flux_pos_mx"] + r["flux_neg_mx"], row.flux_window_mx, TOL_FLUX, True) \
        and int(r["n_missing_win"]) == int(row.n_blank_window)
    return good, "values"


def run(archive_dir=None, out=OUT):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    fr = json.loads(FREEZE.read_text())
    if sha(PROTOCOL) != fr["sha256"]:
        sys.exit("frozen protocol changed")
    archive_dir = archive_dir or CAT.MWO_DATA
    pil = pilot_rows()
    sub, n_blank = r4_subset()
    wanted = {(int(m[:4]), m) for m in pil.member} | {(int(y), m) for y, m in zip(sub.archive_year, sub.mwo_file)}
    data = read_members(wanted, archive_dir)
    missing = sorted(wanted - set(data))
    if missing:                                        # a member may sit in the following year's archive
        data.update(read_members({(y + 1, m) for y, m in missing}, archive_dir))
    rows = []
    for _, row in pil.iterrows():
        y = int(row.member[:4])
        h, B = data.get((y, row.member)) or data[(y + 1, row.member)]
        r = measure_mwo(h, B, row.dpd_lat, row.dpd_lon, blank_rule=False)
        good, why = compare_pilot(r, row)
        rows.append(dict(source="MWO pilot", noaa=row.noaa, member=row.member, ref_status=row.mwo_status,
                         status=r["status"], identical=good, check=why, tilt_new=r.get("tilt_deg"),
                         tilt_ref=row.mwo_tilt_deg))
    for _, row in sub.iterrows():
        h, B = data[(int(row.archive_year), row.mwo_file)]
        r = measure_mwo(h, B, row.dpd_lat_deg, row.dpd_carrington_lon_deg, blank_rule=True)
        good, why = compare_r4(r, row)
        rows.append(dict(source=f"R4 {row.reason}", noaa=row.noaa, member=row.mwo_file, ref_status="ok",
                         status=r["status"], identical=good, check=why, tilt_new=r.get("tilt_deg"), tilt_ref=row.tilt_deg,
                         epoch=row.epoch, hemisphere=row.hemisphere))
    t = pd.DataFrame(rows)
    summ = dict(pilot_rows=int((t.source == "MWO pilot").sum()), pilot_identical=int(t[t.source == "MWO pilot"].identical.sum()),
                r4_rows=int(t.source.str.startswith("R4").sum()), r4_identical=int(t[t.source.str.startswith("R4")].identical.sum()),
                r4_blank_records_available=n_blank, r4_blank_note="no R4 record has n_blank_window > 0" if n_blank == 0 else "",
                all_identical=bool(t.identical.all()), tolerances=dict(angle_deg=TOL_ANG, flux_rel=TOL_FLUX))
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        t.to_csv(tmp / "ROWS.csv", index=False)
        (tmp / "SUMMARY.json").write_text(json.dumps(summ, indent=2) + "\n")
        meta = dict(protocol_sha256=fr["sha256"], script_sha256=sha(__file__), module_sha256=sha(ROOT / "python/sharpbl/tilt_window.py"),
                    inputs_sha256={str(p.relative_to(ROOT)): sha(p) for p in (PILOT_ROWS, RELEASE, ATTEMPTS)},
                    git_commit=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                    products_sha256={f.name: sha(f) for f in sorted(tmp.iterdir())})
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(json.dumps(summ, indent=1))
    return 0 if summ["all_identical"] else 1


def selftest():
    res = []

    def ok(n, c, info=""):
        res.append(bool(c))
        print(f"[{'OK' if c else 'FALLITO'}] {n} {info}")

    h, B = P.synthetic()
    if True:
        r_new = measure_mwo(h, B, 15.0, 110.0, blank_rule=False)
        r_old = P.measure(h, B, 15.0, 110.0)
        same = r_new["status"] == r_old["status"] and all(
            close(r_new[k], r_old[k], 0.0) for k in ("tilt_deg", "lon_pos", "lat_neg", "sep_deg", "flux_pos_mx") if k in r_old)
        ok("synthetic MWO magnetogram: shared body equals the pilot measure exactly", same, (r_new.get("tilt_deg"), r_old.get("tilt_deg")))
        r_cat = CAT.measure(h, B, P.heliographic(h, B.shape), 15.0, 110.0)
        r_new2 = measure_mwo(h, B, 15.0, 110.0, blank_rule=True)
        # lat_bar may differ in the last bit: the catalogue multiplies (|B_r| pix) / mu, the module |B_r| (pix / mu)
        ok("synthetic MWO magnetogram: shared body equals the catalogue measure (A1 rule; tilt exact, lat_bar within "
           "the protocol tolerance)", r_new2["status"] == r_cat["status"] and close(r_new2["tilt_deg"], r_cat["tilt_deg"], 0.0)
           and close(r_new2["lat_bar"], r_cat["lat_bar"], TOL_ANG), abs(r_new2["lat_bar"] - r_cat["lat_bar"]))
        hb = h.copy()
        hb["BLANK"] = -32768
        Bb = B.copy()
        v = np.float32(-32768) * float(hb.get("BSCALE", 1.0)) + float(hb.get("BZERO", 0.0))
        lat, lon, _, mu = P.heliographic(hb, B.shape)
        win = tw.window_mask(lat, lon, 15.0, 110.0, P.WIN_LAT, P.WIN_LON, valid=np.isfinite(mu))
        for frac, exp in ((0.03, "ok"), (0.08, "window_blank")):
            Bx = Bb.copy()
            idx = np.flatnonzero(win & (np.abs(B) < 1))
            Bx.flat[idx[: int(frac * win.sum())]] = v
            a, b = measure_mwo(hb, Bx, 15.0, 110.0, True), CAT.measure(hb, Bx, P.heliographic(hb, Bx.shape), 15.0, 110.0)
            ok(f"synthetic BLANK pixels at {frac:.0%} of the window: status {exp}, equal to the catalogue",
               a["status"] == b["status"] == exp and a.get("n_missing_win") == b["n_blank_win"])
    sub, n_blank = r4_subset()
    ok("R4 subset: two per epoch x hemisphere, BLANK records declared", len(sub) == 2 * sub.groupby(["epoch", "hemisphere"]).ngroups + n_blank
       and n_blank == 0, (len(sub), n_blank))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if selftest() else 1) if a.selftest else sys.exit(run())
