"""Frozen small-comparison inputs, FITS decoding and record-specific CEA geometry."""
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.time import Time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import geometry
from mdi_overlap_kernels import parse_quality32, patch_membership, viewing_geometry

INVENTORY = ROOT / "data/sharp/metadata_inventory_mdi"
BASE = INVENTORY / "small_comparison_6d6fd12"
GEOM = ROOT / "results/MDI_SMARP_INVENTORY_REVIEW/geometry_windows_20261118"
PROTOCOL = ROOT / "docs/PROTOCOL_MDI_HMI_SMALL_COMPARISON.md"
PROTOCOL_HASH = "3713236fe12815dcd07f5149677ed97b5ece5803a57136f8fa3530936056b910"
SEGMENT_HASH = "9fca779a77c3b8e28e641684cc6988f108754382d55360969071c5a8f8585ce1"
PAIR_HASH = "b9128d9b1f14b39d6bf6992b6f567de826d1ce495b740b0e34da3f1c28759d48"
MDI = "mdi.smarp_cea_96m"
HMI = "hmi.sharp_cea_720s"
SEGMENTS = {MDI: ("bitmap", "magnetogram"), HMI: ("bitmap", "Br", "Bt", "Bp", "magnetogram")}
ID = {MDI: "TARPNUM", HMI: "HARPNUM"}
NUMERIC = ("CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2", "CROTA2",
           "DSUN_OBS", "RSUN_REF", "CRLN_OBS", "CRLT_OBS")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(path, expected):
    if sha(path) != expected:
        raise ValueError(f"SHA-256 mismatch: {path}")


def readjson(path):
    return json.loads(path.read_text())


def tai(value):
    match = re.fullmatch(r"(\d{4})\.(\d{2})\.(\d{2})_(\d\d:\d\d:\d\d(?:\.\d+)?)_TAI", str(value))
    if not match:
        raise ValueError(f"Expected JSOC time in TAI: {value}")
    year, month, day, clock = match.groups()
    return Time(f"{year}-{month}-{day}T{clock}", format="isot", scale="tai")


def plan():
    verify(PROTOCOL, PROTOCOL_HASH)
    pf = BASE / "selection/PAIRS.csv"
    sf = BASE / "availability/SEGMENTS.csv"
    verify(pf, PAIR_HASH)
    verify(sf, SEGMENT_HASH)
    with pf.open() as f:
        pairs = list(csv.DictReader(f))
    with sf.open() as f:
        rows = list(csv.DictReader(f))
    records = defaultdict(dict)
    for r in rows:
        series, name = r["series"], r["segment"]
        if (name not in SEGMENTS[series] or r["online"] != "Y" or r["status"] != "online_metadata"
                or not re.fullmatch(r"/SUM\d+(?:/D\d+)+/S\d+/" + name + r"\.fits", r["path"])):
            raise ValueError("Unexpected archive segment")
        key = (series, r["record"])
        if name in records[key]:
            raise ValueError("Duplicate segment")
        records[key][name] = r
    for p in pairs:
        for side in ("smarp", "hmi"):
            series, key = p[side+"_series"], p[side+"_record"]
            files = records[series, key]
            if set(files) != set(SEGMENTS[series]) or any(f["slot"] != p["slot"] for f in files.values()):
                raise ValueError("Segments disagree with selected pair")
    return pairs, records


def reference_inputs():
    """Certified minima and documented units, independent of subsequent FITS transfers."""
    geom = GEOM / "RECORD_GEOMETRY.csv"
    verify(geom, "ebdb75730aaa75f699ef1c4745d115532c82b7c511c9797f0102d2c1641d3783")
    with geom.open() as f:
        cert = {(r["series"], r["identity"]): r for r in csv.DictReader(f)}
    schemas = {}
    for series, digest in [(MDI, "0aebc245f9129cd4800c4c9ba55fc7b13395f416a124663afca25a073ef5eb1a"),
                           (HMI, "4352151dc2f779829e200f081e6308f03e2dbc06406840492f6366e3420e457b")]:
        path = INVENTORY / "schema_20261116_http_ac06138" / f"SCHEMA_{series}.json"
        verify(path, digest)
        schemas[series] = readjson(path)
    return cert, schemas


def metadata(doc, series, record, files):
    """Preserve the original JSON separately. Bind one keyword set to its exact segment paths."""
    if doc.get("status") != 0 or doc.get("count") != 1:
        raise ValueError("Expected one exact record")
    def scalar(item):
        value, = item["values"]
        return value
    kw = {i["name"]: scalar(i) for i in doc["keywords"]}
    num, t = record.split("|")
    if len(kw) != len(doc["keywords"]) or int(kw[ID[series]]) != int(num) or tai(kw["T_REC"]) != tai(t):
        raise ValueError("Keyword identity mismatch")
    segments = {i["name"]: i for i in doc["segments"]}
    if len(segments) != len(doc["segments"]) or segments.keys() != files.keys():
        raise ValueError("Segment list changed")
    for name, r in files.items():
        if scalar(segments[name]) != r["path"] or segments[name]["dims"] != [r["dims"]]:
            raise ValueError("Segment path or dimensions changed")
    return kw


def physical_header(kw, series, quality, shape, schema):
    """Build the same Carrington CEA system as the crop certificate."""
    nx, ny = shape[::-1]
    if parse_quality32(kw["QUALITY"]) != parse_quality32(quality):
        raise ValueError("QUALITY differs from selection")
    tel = str(kw["TELESCOP"]).upper()
    if (series == MDI and ("SOHO" not in tel or "MDI" not in str(kw["INSTRUME"]).upper())
            or series == HMI and "SDO" not in tel):
        raise ValueError("Unexpected observer")
    header = fits.Header()
    for axis, ctype in ((1, "CRLN-CEA"), (2, "CRLT-CEA")):
        if kw[f"CTYPE{axis}"] != ctype or kw[f"CUNIT{axis}"].lower() not in ("deg", "degree"):
            raise ValueError("Unexpected Carrington CEA axes")
        header[f"CTYPE{axis}"] = ctype
        header[f"CUNIT{axis}"] = "deg"
    keywords = {k["name"]: k for k in schema["keywords"]}
    for key in NUMERIC:
        raw = float(kw[key])
        value = float(np.float32(raw)) if keywords[key]["type"] == "float" else raw
        if not np.isfinite(value):
            raise ValueError("Nonfinite "+key)
        header[key] = value
    # A non-default transform would require matching the certified WCS and P1 area formula.
    for key, default in (("PC1_1", 1), ("PC1_2", 0), ("PC2_1", 0), ("PC2_2", 1), ("PV2_1", 1)):
        if key in kw and float(kw[key]) != default:
            raise ValueError("Unexpected WCS parameter "+key)
    if any(key in kw for key in ("CD1_1", "CD1_2", "CD2_1", "CD2_2")):
        raise ValueError("Unexpected CD matrix")
    if (header["CRPIX1"] != (nx+1)/2 or header["CRPIX2"] != (ny+1)/2
            or min(header["CDELT1"], header["CDELT2"]) <= 0 or header["CROTA2"] != 0):
        raise ValueError("Inconsistent certified grid")
    for key in ("DSUN_OBS", "RSUN_REF"):
        if keywords[key]["units"] not in ("m", "meters"):
            raise ValueError("Observer distance/radius unit")
    header["T_REC"] = kw["T_REC"].replace(".000000_TAI", "_TAI")
    for key in ("TELESCOP", "INSTRUME", "QUALITY", "T_OBS"):
        header[key] = kw[key]
    tai(header["T_REC"])
    tai(header["T_OBS"])
    return header


def image(path, shape, unit, header, series, record):
    """Read exactly one image HDU, including Rice compression and native FITS scaling."""
    with fits.open(path, memmap=False) as hdus:
        images = [h for h in hdus if h.is_image and h.header.get("NAXIS") == 2]
        if len(images) != 1 or images[0].shape != shape:
            raise ValueError("Wrong FITS image count or shape")
        hdu = images[0]
        hdr = hdu.header
        for key in NUMERIC:
            if key in hdr and float(hdr[key]) != header[key]:
                raise ValueError(f"FITS/metadata disagree on {key}")
        for key in ("TELESCOP", "INSTRUME"):
            if key in hdr and str(hdr[key]).strip().upper() != str(header[key]).strip().upper():
                raise ValueError("Native FITS and record spacecraft/instrument disagree")
        if "QUALITY" in hdr and parse_quality32(hdr["QUALITY"]) != parse_quality32(header["QUALITY"]):
            raise ValueError("Native FITS and record QUALITY disagree")
        for axis in (1, 2):
            key = f"CUNIT{axis}"
            if key in hdr and hdr[key].lower() not in ("degree", "deg"):
                raise ValueError("FITS angular units disagree")
        for key in hdr:
            if re.fullmatch(r"(CD|PC)[12]_[12]|PV[12]_\d+", key):
                identity = {"PC1_1": 1, "PC2_2": 1, "PC1_2": 0, "PC2_1": 0, "PV2_1": 1}
                if key not in identity or hdr[key] != identity[key]:
                    raise ValueError("Unsupported native FITS transform: "+key)
        for key in ("CTYPE1", "CTYPE2", "T_REC", "T_OBS", ID[series]):
            if key not in hdr:
                continue
            if key in ("T_REC", "T_OBS"):
                same = tai(hdr[key]) == tai(header[key])
            elif key == ID[series]:
                same = int(hdr[key]) == int(record.split("|")[0])
            else:
                same = hdr[key] == header[key]
            if not same:
                raise ValueError(f"FITS/metadata disagree on {key}")
        if "BUNIT" in hdr and str(hdr["BUNIT"]).strip().lower() not in unit:
            raise ValueError("Conflicting FITS BUNIT")
        return np.array(hdu.data, dtype=float, copy=True)


def adapt_record(series, record, files, paths, kw, quality, cert, schema):
    """Adapt downloaded segments for one branch. R0 can request only HMI Br and bitmap.

    paths maps segment to (path, committed download digest). No measurement or cross-instrument
    subtraction here. Native LOS is positive towards each spacecraft (no sign flip).
    """
    if "bitmap" not in paths or not paths.keys() <= files.keys():
        raise ValueError("Missing footprint or unknown segment")
    nx, ny = map(int, cert["dims"].split("x"))
    if cert["state"] != "certified" or any(f["dims"] != cert["dims"] for f in files.values()):
        raise ValueError("Uncertified dimensions")
    if str(kw[ID[series]]) != record.split("|")[0] or tai(kw["T_REC"]) != tai(record.split("|")[1]):
        raise ValueError("Record identity")
    shape = ny, nx
    hdr = physical_header(kw, series, quality, shape, schema)
    segments = {s["name"]: s for s in schema["segments"]}
    arrays = {}
    for name, (path, digest) in paths.items():
        verify(path, digest)
        units = {"enumerated"} if name == "bitmap" else {"gauss", "g", "mx/cm^2", "mx/cm2"}
        if segments[name]["units"].lower() not in units:
            raise ValueError("Unexpected schema units")
        arrays[name] = image(path, shape, units, hdr, series, record)
    lon, lat = geometry.lonlat_maps(hdr, shape)
    view = viewing_geometry(lon, lat, observer_lon_deg=hdr["CRLN_OBS"], observer_lat_deg=hdr["CRLT_OBS"],
                            distance_m=hdr["DSUN_OBS"], radius_m=hdr["RSUN_REF"])
    mu_min = float(view["mu"].min())
    if mu_min < .8 or abs(mu_min-float(cert["min_mu"])) > 1e-9:
        raise ValueError("Geometry differs from the certified pixel minimum")
    mask = patch_membership(arrays["bitmap"], instrument="HMI" if series == HMI else "MDI")
    return dict(arrays=arrays, header=hdr, lon=lon, lat=lat, footprint=mask, geometry=view,
                area_cm2=geometry.pixel_area_cm2(hdr), radius_cm=geometry.rsun_cm(hdr))

def load_selected(slot, series, names):
    """Load one selected record from verified receipts, with an explicit subset for R0."""
    pairs, records = plan()
    certificates, schemas = reference_inputs()
    p, = (p for p in pairs if int(p["slot"]) == slot)
    side, q = ("hmi", "quality_hmi") if series == HMI else ("smarp", "quality_mdi")
    record = p[side+"_record"]
    files = records[series, record]
    directory = BASE/"patch_download"
    ledger = readjson(directory/"LEDGER.json")
    if (ledger["protocol"], ledger["pairs"], ledger["segments"]) != (PROTOCOL_HASH, PAIR_HASH, SEGMENT_HASH):
        raise ValueError("Unexpected acquisition provenance")
    events = {e["key"]: e for e in ledger["events"] if e["state"] == "ok"}
    tag = f"{slot:02d}_{side}"
    def body(key):
        e = events[key]
        name = e["body"]
        if Path(name).name != name or not name.endswith("_"+key+(".fits" if e["fits"] else ".json")):
            raise ValueError("Unexpected receipt filename")
        return directory/name, e["sha256"]
    meta, digest = body(tag+"_keys")
    verify(meta, digest)
    kw = metadata(readjson(meta), series, record, files)
    paths = {}
    for name in names:
        key = tag+"_"+name
        if events[key]["url"] != "http://jsoc.stanford.edu"+files[name]["path"]:
            raise ValueError("Receipt disagrees with archive path")
        paths[name] = body(key)
    return adapt_record(series, record, files, paths, kw, p[q], certificates[side,record], schemas[series])
