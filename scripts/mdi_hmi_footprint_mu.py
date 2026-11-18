"""Offline certificate 1 of PROTOCOL_MDI_HMI_SMALL_COMPARISON_DRAFT §8: minimum mu over every pixel centre of the CEA
cutout, per record, from the saved geometry-only rs_list responses. No network, no maps, no selection.

The arcs are those of the revision-2 audit (unique in G5 and G10, proposed QUALITY, |dT_OBS| <= 360 s, centres within
the limits, same hemisphere; 877/390/880/455 arcs). A record is certified if min mu >= 0.8 over its whole cutout; the
cutout contains every remapped bitmap pixel (findPosition, sharp.c/smarp.c), so this is a lower bound for the mask.
mu < 0.8 means only that the cutout reaches below the limit, not that the mask does.

    .venv/bin/python scripts/mdi_hmi_footprint_mu.py --selftest
    .venv/bin/python scripts/mdi_hmi_footprint_mu.py --run --out results/MDI_SMARP_INVENTORY_REVIEW/footprint_mu_20261118
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import geometry as geo  # noqa: E402
from mdi_overlap_kernels import parse_quality32, viewing_geometry  # noqa: E402

BASE = ROOT / "data/sharp/metadata_inventory_mdi"
SAVED = BASE / "schema_20261116_http_ac06138"
GEOM = BASE / "geometry_windows_20261118"
PROBE = BASE / "geometry_probe_20261118/RECEIPT.json"
ANALYSIS = ROOT / "results/MDI_SMARP_INVENTORY/schema_20261116_http_ac06138/overlap_only/198785bb3002"
MU_MIN = 0.8
STRATA = ("N_central", "S_central", "N_lateral", "S_lateral")
EXPECTED_ARCS = {"N_central": 877, "S_central": 390, "N_lateral": 880, "S_lateral": 455}
KEY = {"mdi.smarp_cea_96m": "TARPNUM", "hmi.sharp_cea_720s": "HARPNUM"}
NEEDED = ("CRVAL1", "CRVAL2", "CRPIX1", "CRPIX2", "CDELT1", "CDELT2", "CROTA2", "CRLN_OBS", "CRLT_OBS",
          "DSUN_OBS", "RSUN_REF")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rows(p):
    with (gzip.open(p, "rt", newline="") if str(p).endswith(".gz") else open(p, newline="")) as f:
        return list(csv.DictReader(f))


def normtime(t):
    return re.sub(r"\.0+_TAI$", "_TAI", t)


def fnum(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


# ---------------------------------------------------------------- arcs (same rules as mdi_overlap_metadata_review.py)

def audit_arcs():
    meta = json.loads((ANALYSIS / "META.json").read_text())
    saved = {}
    for prof in ("smarp_overlap", "hmi_overlap"):
        name = f"RECORDS_{prof}.csv.gz"
        if sha(SAVED / name) != meta["source_sha256"][name]:
            raise SystemExit(f"saved source changed: {name}")
        saved[prof] = [x for x in rows(SAVED / name) if x["edge"] == "0"]
    sm = {x["TARPNUM"] + "|" + x["T_REC"]: x for x in saved["smarp_overlap"]}
    hm = {x["HARPNUM"] + "|" + x["T_REC"]: x for x in saved["hmi_overlap"]}
    cands = rows(ANALYSIS / "OVERLAP_CANDIDATES.csv.gz")
    # G10 components over patches (all in_G10 arcs), for the per-stratum component counts
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for p in cands:
        if p["in_G10"] == "1":
            a, b = find("T" + p["TARPNUM"]), find("H" + p["HARPNUM"])
            if a != b:
                parent[a] = b
    arcs = []
    for p in cands:
        if p["unique_in_G5"] != "1" or p["unique_in_G10"] != "1":
            continue
        s, h = sm[p["smarp_id"]], hm[p["hmi_id"]]
        if parse_quality32(s["QUALITY"]) not in (0, 512) or parse_quality32(h["QUALITY"]) != 0:
            continue
        dt = fnum(p["dt_obs_s"])
        if dt is None or abs(dt) > 360:
            continue
        slat, hlat, hlon, obs = (fnum(s["CRVAL2"]), fnum(h["CRVAL2"]), fnum(h["CRVAL1"]), fnum(h["CRLN_OBS"]))
        if any(v is None for v in (slat, hlat, hlon, obs)):
            continue
        if slat * hlat <= 0 or max(abs(slat), abs(hlat)) > 30:
            continue
        lon = (hlon - obs + 180) % 360 - 180
        if abs(lon) > 30:
            continue
        st = ("N" if hlat > 0 else "S") + ("_central" if abs(lon) <= 15 else "_lateral")
        arcs.append(dict(stratum=st, TARPNUM=p["TARPNUM"], HARPNUM=p["HARPNUM"],
                         smarp=("mdi.smarp_cea_96m", p["TARPNUM"], normtime(s["T_REC"])),
                         hmi=("hmi.sharp_cea_720s", p["HARPNUM"], normtime(h["T_REC"])),
                         component=find("T" + p["TARPNUM"]), quality_mdi=f"0x{parse_quality32(s['QUALITY']):08X}"))
    return arcs


# ---------------------------------------------------------------- saved geometry responses

def load_geometry():
    led = json.loads((GEOM / "ACQUISITION.json").read_text())
    if not led.get("complete") or len(led["requests"]) != 32 or any(r["state"] != "ok" for r in led["requests"]):
        raise SystemExit("geometry acquisition not complete")
    if len({(r["series"], r["window"]) for r in led["requests"]}) != 32:
        raise SystemExit("duplicated geometry windows")
    table, dup = {}, Counter()
    for r in led["requests"]:
        p = GEOM / f"{r['tag']}.json"
        if sha(p) != r["sha256"]:
            raise SystemExit(f"hash differs for {p.name}")
        js = json.loads(p.read_text())
        if js["status"] != 0 or js["count"] != r["rows"]:
            raise SystemExit(f"status or count differs for {p.name}")
        c = {k["name"]: k["values"] for k in js["keywords"]}
        [seg] = js["segments"]
        if seg["name"] != "bitmap" or len(seg["dims"]) != js["count"]:
            raise SystemExit(f"bitmap dims missing in {p.name}")
        key = KEY[r["series"]]
        for i in range(js["count"]):
            k = (r["series"], str(int(float(c[key][i]))), normtime(c["T_REC"][i]))
            dup[k] += 1
            table[k] = dict({n: c[n][i] for n in NEEDED}, dims=seg["dims"][i], window=r["tag"])
    return table, {k for k, n in dup.items() if n > 1}, led


# ---------------------------------------------------------------- certificate 1

def mu_min_cutout(g):
    """Minimum mu over every pixel centre of the CEA cutout, or (None, reason)."""
    v = {n: fnum(g.get(n)) for n in NEEDED}
    missing = [n for n, x in v.items() if x is None]
    if missing:
        return None, "missing:" + "|".join(missing)
    m = re.fullmatch(r"(\d+)x(\d+)", str(g.get("dims", "")))
    if not m:
        return None, f"dims not interpretable: {g.get('dims')}"
    nx, ny = int(m.group(1)), int(m.group(2))
    if nx <= 0 or ny <= 0:
        return None, "dims not positive"
    if v["CROTA2"] != 0:
        return None, "CEA rotation not zero"
    if abs(v["CRPIX1"] - (nx + 1) / 2) > 1e-6 or abs(v["CRPIX2"] - (ny + 1) / 2) > 1e-6:
        return None, "CRPIX inconsistent with dims"
    if not 0 < v["RSUN_REF"] < v["DSUN_OBS"]:
        return None, "observer distance not valid"
    hdr = dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="deg", CUNIT2="deg", CRVAL1=v["CRVAL1"],
               CRVAL2=v["CRVAL2"], CRPIX1=v["CRPIX1"], CRPIX2=v["CRPIX2"], CDELT1=v["CDELT1"], CDELT2=v["CDELT2"])
    lon, lat = geo.lonlat_maps(hdr, (ny, nx))
    if not (np.isfinite(lon).all() and np.isfinite(lat).all()):
        return None, "WCS undefined on some pixel"
    gm = viewing_geometry(lon, lat, observer_lon_deg=v["CRLN_OBS"], observer_lat_deg=v["CRLT_OBS"],
                          distance_m=v["DSUN_OBS"], radius_m=v["RSUN_REF"])
    return float(gm["mu"].min()), f"{nx}x{ny}"


def classify(arc, table, dups):
    out = {}
    for inst in ("smarp", "hmi"):
        k = arc[inst]
        if k in dups:
            out[inst] = (None, "duplicated record in responses")
        elif k not in table:
            out[inst] = (None, "record absent from responses")
        else:
            out[inst] = mu_min_cutout(table[k])
    if any(m is None for m, _ in out.values()):
        cat = "missing_or_not_interpretable"
    elif all(m >= MU_MIN for m, _ in out.values()):
        cat = "certified_both"
    else:
        cat = "insufficient_coverage"
    return cat, out


def run(out_dir):
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise SystemExit("refusing to overwrite the output folder")
    t0 = time.time()
    registry = BASE / "INVENTORY_REGISTRY.json"
    reg0 = sha(registry)
    arcs = audit_arcs()
    n = Counter(a["stratum"] for a in arcs)
    if dict(n) != EXPECTED_ARCS:
        raise SystemExit(f"arcs differ from the revision-2 audit: {dict(n)}")
    table, dups, led = load_geometry()
    cache, recs = {}, []
    for a in arcs:
        cat, res = classify(a, table, dups)
        recs.append(dict(stratum=a["stratum"], TARPNUM=a["TARPNUM"], HARPNUM=a["HARPNUM"], T_REC_smarp=a["smarp"][2],
                         T_REC_hmi=a["hmi"][2], component=a["component"], quality_mdi=a["quality_mdi"], category=cat,
                         mu_min_smarp=res["smarp"][0], info_smarp=res["smarp"][1],
                         mu_min_hmi=res["hmi"][0], info_hmi=res["hmi"][1]))
    strata = []
    for st in STRATA:
        R = [r for r in recs if r["stratum"] == st]
        row = dict(stratum=st, arcs=len(R), distinct_pairs=len({(r["TARPNUM"], r["HARPNUM"]) for r in R}))
        for cat in ("certified_both", "insufficient_coverage", "missing_or_not_interpretable"):
            C = [r for r in R if r["category"] == cat]
            row[f"{cat}_arcs"] = len(C)
            row[f"{cat}_pairs"] = len({(r["TARPNUM"], r["HARPNUM"]) for r in C})
        ins = [r for r in R if r["category"] == "insufficient_coverage"]
        row["insufficient_smarp_only"] = sum(r["mu_min_smarp"] < MU_MIN <= r["mu_min_hmi"] for r in ins)
        row["insufficient_hmi_only"] = sum(r["mu_min_hmi"] < MU_MIN <= r["mu_min_smarp"] for r in ins)
        row["insufficient_both"] = sum(r["mu_min_hmi"] < MU_MIN and r["mu_min_smarp"] < MU_MIN for r in ins)
        cert = {r["component"] for r in R if r["category"] == "certified_both"}
        row["g10_components_with_certified_arc"] = len(cert)
        row["certified_arcs_mdi_quality_0x0"] = sum(r["category"] == "certified_both" and r["quality_mdi"] == "0x00000000"
                                                    for r in R)
        strata.append(row)
    comp_strata = defaultdict(set)
    for r in recs:
        if r["category"] == "certified_both":
            comp_strata[r["component"]].add(r["stratum"])
    shared = sum(len(v) > 1 for v in comp_strata.values())
    reasons = Counter(r[f"info_{i}"] for r in recs for i in ("smarp", "hmi") if r[f"mu_min_{i}"] is None)
    if sha(registry) != reg0:
        raise SystemExit("inventory registry changed")
    out_dir.mkdir(parents=True)
    with gzip.open(out_dir / "ARC_CERTIFICATES.csv.gz", "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(recs)
    with open(out_dir / "STRATA_CERTIFIED.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(strata[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(strata)
    meta = dict(scope="certificate 1 only (CEA cutout), counts before any selection; no network, no maps",
                mu_min=MU_MIN, script_sha256=sha(__file__), acquisition_sha256=sha(GEOM / "ACQUISITION.json"),
                probe_sha256=sha(PROBE), registry_unchanged_sha256=reg0,
                g10_components_certified_in_more_than_one_stratum=shared,
                g10_components_certified_total=len(comp_strata), not_interpretable_reasons=dict(reasons),
                duplicated_records_in_responses=len(dups), seconds=round(time.time() - t0, 1),
                products_sha256={p.name: sha(p) for p in sorted(out_dir.iterdir())},
                limitations=["mu < 0.8 on the cutout does not show that the mask leaves the domain",
                             "code revisions of findPosition/jsoc_info are not proven identical to production",
                             "LAT/LON_MIN/MAX not used as a certificate"])
    (out_dir / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(dict(strata=strata, shared_components=shared, reasons=dict(reasons)), indent=1))
    return 0


# ---------------------------------------------------------------- selftest (synthetic + probe fixture)

def selftest():
    res = []

    def ok(name, cond, value=""):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {value}")
    base = dict(CRVAL1="100", CRVAL2="10", CDELT1="0.03", CDELT2="0.03", CROTA2="0", CRLN_OBS="100", CRLT_OBS="0",
                DSUN_OBS="1.5e11", RSUN_REF="6.96e8")
    g = dict(base, dims="11x9", CRPIX1="6", CRPIX2="5")
    m, info = mu_min_cutout(g)
    r = 6.96e8 / 1.5e11
    lon, lat = geo.lonlat_maps(dict(CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA", CUNIT1="deg", CUNIT2="deg", CRVAL1=100.,
                                    CRVAL2=10., CRPIX1=6., CRPIX2=5., CDELT1=.03, CDELT2=.03), (9, 11))
    q = np.sin(np.radians(lat)) * 0 + np.cos(np.radians(lat)) * np.cos(np.radians(lon - 100))
    ref = ((q - r) / np.sqrt(1 + r * r - 2 * r * q)).min()
    ok("mu minimum = closed form of §8 over all pixel centres", abs(m - ref) < 1e-12, (m, ref))
    ok("minimum is at the edge, below the centre value", m < (math.cos(math.radians(10)) - r) / math.sqrt(1 + r * r - 2 * r * math.cos(math.radians(10))))
    ok("non-square cutout keeps (nx, ny) order", info == "11x9")
    ok("CRPIX inconsistent with dims -> not interpretable", mu_min_cutout(dict(g, CRPIX1="5"))[0] is None)
    ok("swapped axes detected through CRPIX", mu_min_cutout(dict(g, dims="9x11"))[0] is None)
    ok("missing observer distance -> not interpretable", mu_min_cutout(dict(g, DSUN_OBS=""))[0] is None)
    ok("rotation not zero -> not interpretable", mu_min_cutout(dict(g, CROTA2="180"))[0] is None)
    ok("bad dims string -> not interpretable", mu_min_cutout(dict(g, dims="NA"))[0] is None)
    far = dict(base, CRVAL1="140", dims="11x9", CRPIX1="6", CRPIX2="5")
    ok("cutout at 40 deg from the observer (mu about 0.75) is not certified", mu_min_cutout(far)[0] < MU_MIN)
    pr = json.loads(PROBE.read_text())
    ok("probe fixture: dims (77,70) and (388,285) match CRPIX convention (n+1)/2",
       all(abs(a["crpix"][0] - (a["dims"][0] + 1) / 2) < 1e-9 and abs(a["crpix"][1] - (a["dims"][1] + 1) / 2) < 1e-9
           for a in pr["attempts"]))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if a.run and a.out:
        if not selftest():
            return 1
        return run(a.out)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
