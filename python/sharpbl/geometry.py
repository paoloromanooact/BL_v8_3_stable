"""Geometria delle mappe SHARP CEA.

Le mappe hmi.sharp_cea_720s sono proiezioni CEA oblique centrate sulla patch
(CTYPE CRLN-CEA / CRLT-CEA con CRVAL2 != 0): le righe della mappa non sono
paralleli di latitudine costante. Qui longitudine e latitudine di ogni pixel si
ricavano dalla WCS completa (astropy), e distanze e angoli si calcolano sulla
sfera con vettori unitari, senza una scala unica in pixel.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning

RSUN_CM_DEFAULT = 6.96e10  # RSUN_REF delle mappe SHARP, in cm


def read_sharp(path):
    """Restituisce (data, header) dall'ultima HDU del file (CompImageHDU).

    Per i file scaricati "as-is" (download_records.py) le keyword DRMS stanno in
    <nome>.keys.json accanto al FITS e vengono aggiunte all'header.
    """
    path = Path(path)
    with fits.open(path) as hl:
        hdu = hl[-1]
        data, header = np.asarray(hdu.data, dtype=float), hdu.header.copy()
    stem = path.name.rsplit(".", 2)[0]  # toglie .<segmento>.fits
    kpath = path.with_name(stem + ".keys.json")
    if kpath.exists():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # keyword lunghe -> HIERARCH
            for k, v in json.loads(kpath.read_text()).items():
                if v is None or k in header or len(k) > 68:
                    continue
                if isinstance(v, str) and len(v) > 60:
                    continue
                header[k] = v
    return data, header


def rsun_cm(header) -> float:
    r = header.get("RSUN_REF")
    return float(r) * 100.0 if r else RSUN_CM_DEFAULT


def lonlat_maps(header, shape):
    """Longitudine di Carrington e latitudine (gradi) di ogni pixel, shape (ny, nx)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FITSFixedWarning)
        w = WCS(header)
    ny, nx = shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    lon, lat = w.wcs_pix2world(xx, yy, 0)
    return np.asarray(lon, float), np.asarray(lat, float)


def pixel_area_cm2(header) -> float:
    """Area di un pixel: costante in una proiezione CEA (equivalente), R^2 dphi dmu."""
    r = rsun_cm(header)
    d1 = np.radians(abs(float(header["CDELT1"])))
    d2 = np.radians(abs(float(header["CDELT2"])))
    return r * r * d1 * d2


def unit_vectors(lon_deg, lat_deg):
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    c = np.cos(lat)
    return np.stack([c * np.cos(lon), c * np.sin(lon), np.sin(lat)], axis=-1)


def to_lonlat(v):
    v = np.asarray(v, float)
    v = v / np.linalg.norm(v)
    return float(np.degrees(np.arctan2(v[1], v[0]))), float(np.degrees(np.arcsin(np.clip(v[2], -1, 1))))


def weighted_centroid(lon_deg, lat_deg, weights):
    """Centroide pesato sulla sfera: media pesata dei vettori unitari, rinormalizzata."""
    w = np.asarray(weights, float)
    if w.size == 0 or not np.isfinite(w).all() or w.sum() <= 0:
        return np.nan, np.nan
    v = (unit_vectors(lon_deg, lat_deg) * w[:, None]).sum(axis=0)
    if np.linalg.norm(v) == 0:
        return np.nan, np.nan
    return to_lonlat(v)


def great_circle_deg(lon1, lat1, lon2, lat2):
    a = unit_vectors(lon1, lat1)
    b = unit_vectors(lon2, lat2)
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), np.dot(a, b))))


def tilt_deg(lead, follow):
    """Angolo del vettore leading -> following nel piano tangente al punto medio.

    Stessa convenzione della v8.3 (atan2(dy, dx) con x verso ovest = longitudine
    di Carrington crescente, y verso nord): sin(alpha) > 0 se la following e' a
    nord della leading.
    """
    a = unit_vectors(*lead)
    b = unit_vectors(*follow)
    m = a + b
    if np.linalg.norm(m) == 0:
        return np.nan
    m = m / np.linalg.norm(m)
    west = np.array([-m[1], m[0], 0.0])  # direzione di longitudine crescente
    if np.linalg.norm(west) == 0:
        return np.nan
    west /= np.linalg.norm(west)
    north = np.cross(m, west)
    v = b - a
    return float(np.degrees(np.arctan2(np.dot(v, north), np.dot(v, west))))


def reduce_tilt_deg(t):
    """Come sharp_reduce_tilt_deg della v8.3: riporta l'angolo in (-90, 90]."""
    if not np.isfinite(t):
        return np.nan
    a = (t + 180.0) % 360.0 - 180.0
    if a == -180.0:
        a = 180.0
    if a > 90.0:
        a -= 180.0
    if a < -90.0:
        a += 180.0
    return a
