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


# ---------------------------------------------------------------- P1e (bozza, sostituisce P1d §1)
P1E_DLAT, P1E_DLON, LIMB = 3.0, 6.0, 60.0


def candidate_pairs_p1e(df: pd.DataFrame, life: pd.DataFrame) -> pd.DataFrame:
    """Coppie di P1e §1: finestre ±3°/±6° e criterio del lembo.

    df: HARPNUM, t, lat, lon_carr (record primari); life: indice HARPNUM,
    colonne lon_first, lon_last (LON_FWT del primo e ultimo record della HARP).
    """
    global DLAT_MAX, DLON_MAX
    saved = DLAT_MAX, DLON_MAX
    DLAT_MAX, DLON_MAX = P1E_DLAT, P1E_DLON
    try:
        p = candidate_pairs(df)
    finally:
        DLAT_MAX, DLON_MAX = saved
    p["dist"] = np.hypot(p["dlat"] / P1E_DLAT, p["dlon"] / P1E_DLON)
    p = p.merge(life, left_on="harp_i", right_index=True).merge(
        life, left_on="harp_j", right_index=True, suffixes=("_i", "_j"))
    return p[(p["lon_last_i"] >= LIMB) & (p["lon_first_j"] <= -LIMB)]


def primary_frame(primary_meta):
    return pd.DataFrame({
        "HARPNUM": primary_meta["HARPNUM"].astype(int).to_numpy(),
        "t": pd.to_datetime(primary_meta["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S").to_numpy(),
        "lat": primary_meta["LAT_FWT"].astype(float).to_numpy(),
        "lon_carr": ((primary_meta["LON_FWT"].astype(float) + primary_meta["CRLN_OBS"].astype(float)) % 360.0).to_numpy(),
    })


def recurrences_p1e(primary_meta, life):
    d = primary_frame(primary_meta)
    return assign(candidate_pairs_p1e(d, life), d["HARPNUM"].tolist())


def random_control_p1e(primary_meta, life, reps=20, seed0=20261106):
    """P1e §2: frequenza di associazioni con longitudini casuali (stesse HARP, stessi tempi)."""
    out = []
    for k in range(reps):
        rng = np.random.default_rng(seed0 + k)
        d = primary_frame(primary_meta)
        d["lon_carr"] = (d["lon_carr"] + rng.uniform(0, 360, len(d))) % 360.0
        r = assign(candidate_pairs_p1e(d, life), d["HARPNUM"].tolist())
        r["year"] = pd.to_datetime(d.set_index("HARPNUM").loc[r["HARPNUM"], "t"].to_numpy()).year
        r["rep"] = k
        out.append(r)
    return pd.concat(out, ignore_index=True)
