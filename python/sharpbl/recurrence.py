"""Ricomparse delle regioni da una rotazione alla successiva (protocollo P1d §1).

Usa solo tempi e posizioni dei record primari dai metadati SHARP (LAT_FWT,
LON_FWT + CRLN_OBS), nessuna polarita'. Restituisce, per ogni HARP:
recurrence_of (HARP precedente o NaN), family_id, family_rank.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DT_MIN, DT_MAX = 20.0, 34.0      # giorni
DLAT_MAX, DLON_MAX = 5.0, 10.0   # gradi
OMEGA_CARR = 14.1844             # gradi/giorno, siderale


def omega(lat_deg):
    """Rotazione differenziale delle strutture magnetiche (Snodgrass & Ulrich 1990), gradi/giorno."""
    s2 = np.sin(np.radians(lat_deg)) ** 2
    return 14.713 - 2.396 * s2 - 1.787 * s2 ** 2


def wrap(x):
    return (np.asarray(x, float) + 180.0) % 360.0 - 180.0


def candidate_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """df: HARPNUM, t (Timestamp), lat, lon_carr. Coppie (i -> j) che soddisfano P1d §1."""
    d = df.sort_values("t").reset_index(drop=True)
    tday = (d["t"] - pd.Timestamp("2010-01-01")).dt.total_seconds().to_numpy() / 86400.0
    lat = d["lat"].to_numpy()
    lon = d["lon_carr"].to_numpy()
    harp = d["HARPNUM"].to_numpy()
    rows = []
    lo = 0
    for j in range(len(d)):
        while tday[j] - tday[lo] > DT_MAX:
            lo += 1
        for i in range(lo, j):
            dt = tday[j] - tday[i]
            if dt < DT_MIN or np.sign(lat[i]) != np.sign(lat[j]):
                continue
            dlat = lat[j] - lat[i]
            if abs(dlat) > DLAT_MAX:
                continue
            lbar = 0.5 * (lat[i] + lat[j])
            lpred = lon[i] + (omega(lbar) - OMEGA_CARR) * dt
            dlon = float(wrap(lon[j] - lpred))
            if abs(dlon) > DLON_MAX:
                continue
            rows.append((harp[i], harp[j], dt, dlat, dlon, np.hypot(dlat / DLAT_MAX, dlon / DLON_MAX)))
    return pd.DataFrame(rows, columns=["harp_i", "harp_j", "dt_days", "dlat", "dlon", "dist"])


def assign(pairs: pd.DataFrame, harps) -> pd.DataFrame:
    """Assegnazione uno a uno in ordine di distanza crescente; famiglie dalle catene."""
    prev, used_i = {}, set()
    for r in pairs.sort_values(["dist", "harp_j", "harp_i"]).itertuples(index=False):
        if r.harp_j in prev or r.harp_i in used_i:
            continue
        prev[r.harp_j] = r.harp_i
        used_i.add(r.harp_i)
    out = []
    for h in harps:
        rank, root = 0, h
        while root in prev:
            root = prev[root]
            rank += 1
        out.append((h, prev.get(h, np.nan), root, rank))
    return pd.DataFrame(out, columns=["HARPNUM", "recurrence_of", "family_id", "family_rank"])


def recurrences(primary_meta: pd.DataFrame) -> pd.DataFrame:
    """primary_meta: HARPNUM, T_REC, LAT_FWT, LON_FWT, CRLN_OBS dei record primari."""
    d = pd.DataFrame({
        "HARPNUM": primary_meta["HARPNUM"].astype(int),
        "t": pd.to_datetime(primary_meta["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S"),
        "lat": primary_meta["LAT_FWT"].astype(float),
        "lon_carr": (primary_meta["LON_FWT"].astype(float) + primary_meta["CRLN_OBS"].astype(float)) % 360.0,
    })
    return assign(candidate_pairs(d), d["HARPNUM"].tolist())
