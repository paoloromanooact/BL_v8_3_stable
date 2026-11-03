"""Assegnazione del ciclo e polarita' leading attesa (legge di Hale).

Fuori dalle finestre di sovrapposizione il ciclo si ricava dalla data. Dentro
le finestre decide la latitudine, tramite una tabella di separazione ricavata
dalle sole latitudini delle regioni (mai dalle polarita'), vedi
docs/PROTOCOL_P1_SBL_SERIES.md. Senza tabella la regione resta "UNRESOLVED".
"""
from __future__ import annotations

from datetime import datetime

import numpy as np

# Finestre di sovrapposizione [inizio, fine) e coppia (ciclo vecchio, ciclo nuovo)
OVERLAP_WINDOWS = [
    (datetime(2010, 1, 1), datetime(2012, 1, 1), 23, 24),
    (datetime(2017, 1, 1), datetime(2022, 1, 1), 24, 25),
]


def cycle_by_date(t: datetime) -> int:
    """Regola della v8.3, estesa al ciclo 23: inizio ciclo 24 a 2008-12, ciclo 25 a 2019-12."""
    if t >= datetime(2019, 12, 1):
        return 25
    if t >= datetime(2008, 12, 1):
        return 24
    return 23


def overlap_window(t: datetime):
    for a, b, old, new in OVERLAP_WINDOWS:
        if a <= t < b:
            return a, b, old, new
    return None


def assign_cycle(t: datetime, lat_deg: float, boundary=None):
    """Restituisce (ciclo, p_new, stato).

    boundary: funzione (t, |lat|) -> probabilita' che la regione appartenga al
    ciclo nuovo, ricavata dalle latitudini (protocollo P1). stato e' "DATE"
    fuori dalle finestre, "LATITUDE", "AMBIGUOUS" o "DATE_IN_WINDOW" dentro, "UNRESOLVED" se manca
    la tabella.
    """
    w = overlap_window(t)
    if w is None:
        return cycle_by_date(t), np.nan, "DATE"
    _, _, old, new = w
    if boundary is None or not np.isfinite(lat_deg):
        return cycle_by_date(t), np.nan, "UNRESOLVED"
    p = float(boundary(t, abs(lat_deg)))
    if not np.isfinite(p):  # gruppo di un solo ciclo (P1 §5, punto 4): decide la data
        return cycle_by_date(t), np.nan, "DATE_IN_WINDOW"
    cyc = new if p >= 0.5 else old
    state = "AMBIGUOUS" if 0.2 < p < 0.8 else "LATITUDE"
    return cyc, p, state


def expected_leading_sign(cycle: int, lat_deg: float) -> int:
    """Cicli dispari: leading positiva a nord; pari: negativa a nord (Hale)."""
    hemi = 1 if lat_deg >= 0 else -1
    return hemi if cycle % 2 == 1 else -hemi
