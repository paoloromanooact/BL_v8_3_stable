"""Regola del ciclo nelle finestre di sovrapposizione (P1 §5 con P1c), dalle sole latitudini.

Uso: .venv/bin/python python/sharpbl/cycle_boundary.py
Legge results/P1/P1_RECORD_SELECTION.csv (record primari: |LAT_FWT| e T_REC dai
metadati, nessuna polarita'), scrive results/P1/CYCLE_BOUNDARY_FITS.csv.
Il modulo espone anche load_boundary() per measure/cycle.assign_cycle.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl.cycle import OVERLAP_WINDOWS  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

MIN_GROUP = 15
MIN_WEIGHT = 0.05
MIN_SEPARATION = 5.0       # P1 §5
# P1c: un gruppo e' di due cicli solo se il vecchio e' basso e il nuovo alto
P1C_MAX_MU_OLD = 12.0
P1C_MIN_MU_NEW = 18.0
P1C_MIN_SEPARATION = 8.0
OUT = ROOT / "results/P1/CYCLE_BOUNDARY_FITS.csv"


def semesters(a: datetime, b: datetime):
    out = []
    y, h = a.year, 0 if a.month <= 6 else 1
    while True:
        s = datetime(y, 1 + 6 * h, 1)
        e = datetime(y + h, 7 if h == 0 else 1, 1)
        if s >= b:
            return out
        out.append([s, e])
        y, h = (y, 1) if h == 0 else (y + 1, 0)


def merge_small(groups, counts):
    """Unisce i gruppi con meno di MIN_GROUP HARP al vicino con meno HARP."""
    groups = [list(g) for g in groups]
    counts = list(counts)
    while len(groups) > 1 and min(counts) < MIN_GROUP:
        i = int(np.argmin(counts))
        nbrs = [j for j in (i - 1, i + 1) if 0 <= j < len(groups)]
        j = min(nbrs, key=lambda k: (counts[k], k))
        a, b = sorted((i, j))
        groups[a] = [groups[a][0], groups[b][1]]
        counts[a] += counts[b]
        del groups[b], counts[b]
    return groups, counts


def gmm2(x, mu=(10.0, 25.0), sd=(5.0, 5.0), w=(0.5, 0.5), iters=500, tol=1e-9):
    x = np.asarray(x, float)
    mu, sd, w = np.array(mu, float), np.array(sd, float), np.array(w, float)
    ll_old = -np.inf
    for _ in range(iters):
        dens = w / (sd * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x[:, None] - mu) / sd) ** 2)
        tot = dens.sum(axis=1) + 1e-300
        r = dens / tot[:, None]
        nk = r.sum(axis=0)
        w = nk / len(x)
        mu = (r * x[:, None]).sum(axis=0) / np.maximum(nk, 1e-12)
        sd = np.sqrt((r * (x[:, None] - mu) ** 2).sum(axis=0) / np.maximum(nk, 1e-12))
        sd = np.maximum(sd, 0.5)
        ll = np.log(tot).sum()
        if abs(ll - ll_old) < tol:
            break
        ll_old = ll
    order = np.argsort(mu)  # componente con media maggiore = ciclo nuovo
    return w[order], mu[order], sd[order], ll


def p_new(lat_abs, row):
    def comp(k):
        return row[f"w_{k}"] / row[f"sd_{k}"] * np.exp(-0.5 * ((lat_abs - row[f"mu_{k}"]) / row[f"sd_{k}"]) ** 2)
    o, n = comp("old"), comp("new")
    return float(n / (o + n)) if (o + n) > 0 else np.nan


def boundary_lat(row):
    """|lat| a cui p_new = 0,5 tra le due medie (solo descrittivo)."""
    grid = np.linspace(row["mu_old"], row["mu_new"], 2001)
    p = np.array([p_new(g, row) for g in grid])
    k = np.where(np.diff(np.sign(p - 0.5)) != 0)[0]
    return float(grid[k[0]]) if len(k) else np.nan


def fit(sel: pd.DataFrame) -> pd.DataFrame:
    prim = sel[sel["role"] != "control"].copy()
    prim["t"] = pd.to_datetime(prim["T_REC"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    prim["lat_abs"] = prim["LAT_FWT"].abs()
    rows = []
    for a, b, old, new in OVERLAP_WINDOWS:
        sem = semesters(a, b)
        counts = [int(((prim.t >= s) & (prim.t < e)).sum()) for s, e in sem]
        groups, counts = merge_small(sem, counts)
        for (s, e), n in zip(groups, counts):
            x = prim.loc[(prim.t >= s) & (prim.t < e), "lat_abs"].to_numpy()
            w, mu, sd, ll = gmm2(x)
            single_p1 = (w.min() < MIN_WEIGHT) or (mu[1] - mu[0] < MIN_SEPARATION)
            single = (w.min() < MIN_WEIGHT or mu[0] > P1C_MAX_MU_OLD or mu[1] < P1C_MIN_MU_NEW
                      or mu[1] - mu[0] < P1C_MIN_SEPARATION)
            row = dict(window=f"{old}/{new}", cycle_old=old, cycle_new=new,
                       start=s.date().isoformat(), end=e.date().isoformat(), n_harp=n,
                       w_old=w[0], mu_old=mu[0], sd_old=sd[0], w_new=w[1], mu_new=mu[1], sd_new=sd[1],
                       loglik=ll, state_p1="DATE_IN_WINDOW" if single_p1 else "LATITUDE",
                       state="DATE_IN_WINDOW" if single else "LATITUDE")
            row["lat_p50"] = np.nan if single else boundary_lat(row)
            rows.append(row)
    return pd.DataFrame(rows)


def load_boundary(path: Path = OUT):
    """Funzione (t, |lat|) -> p_new; NaN nei gruppi di un solo ciclo o fuori dalle finestre."""
    tab = pd.read_csv(path)
    tab["s"] = pd.to_datetime(tab["start"])
    tab["e"] = pd.to_datetime(tab["end"])

    def boundary(t, lat_abs):
        t = pd.Timestamp(t)
        m = tab[(tab.s <= t) & (t < tab.e)]
        if m.empty or m.iloc[0]["state"] != "LATITUDE":
            return np.nan
        return p_new(lat_abs, m.iloc[0])
    return boundary


def main() -> int:
    sel = pd.read_csv(ROOT / "results/P1/P1_RECORD_SELECTION.csv")
    tab = fit(sel)
    tab.assign(**stamp(("P1", "P1b", "P1c"))).to_csv(OUT, index=False)
    pd.set_option("display.width", 200)
    print(tab[["window", "start", "end", "n_harp", "w_old", "mu_old", "sd_old", "w_new", "mu_new",
               "sd_new", "lat_p50", "state_p1", "state"]].to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
