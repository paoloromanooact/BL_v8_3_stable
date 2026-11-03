"""Protocolli P3, P3b e P3c: validazione esterna con BARD (coerenza delle misure).

Uso: .venv/bin/python python/sharpbl/run_p3.py [--skip-download]

Passi (P3 §2-§6, P3b):
1. convenzioni di BARD dalle verifiche interne (§2); se una e' indeterminata,
   i confronti che ne dipendono sono sospesi;
2. abbinamento BARD -> HARP con i metadati orari (±1 ora, ±3°, ±6°, uno a uno)
   e controllo con longitudini casuali (§4);
3. C1: download e misura v84 del record SHARP contemporaneo (§3);
4. C2: misure del catalogo P1 (solo se la serie P1 e' completa e validata);
5. statistiche con bootstrap per famiglie P1e, criteri operativi ed esito (§5, P3b).
Scrive results/P3/.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import cycle as cyc  # noqa: E402
from sharpbl import geometry as geo  # noqa: E402
from sharpbl import measure  # noqa: E402
from sharpbl.cycle_boundary import load_boundary  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

BARD = ROOT / "data/sharp/external/BARD"
FITS_P3 = ROOT / "data/sharp/fits_p3"
OUT = ROOT / "results/P3"
SEED_CTRL, SEED_BOOT = 20261107, 20261108
NREP_CTRL, NBOOT = 20, 2000
DT_MAX_H = 1.0
DLAT, DLON = 3.0, 6.0
R_CM = 6.96e10
PHI_MIN = 1e21
QUAL_OK = {0, 0x80}
BOOL_COLS = ["Hale", "AntiHale", "HH_24n", "AH_24n", "HH_24s", "AH_24s", "Cycle24n", "Cycle24s"]


def wrap(x):
    return (np.asarray(x, float) + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------- BARD

def load_bard(kind="HMI"):
    f = {"HMI": "BARD_2010-2016_HMI_tilts.csv", "MDI": "BARD_1996-2010_MDI_tilts.csv"}[kind]
    b = pd.read_csv(BARD / f)
    for c in BOOL_COLS:
        if c in b:
            b[c] = b[c].astype(str).str.strip('"').map({"True": True, "False": False})
    b["t"] = pd.to_datetime(dict(year=b.Year, month=b.Month, day=b.Day, hour=b.Hour, minute=b.Minute,
                                 second=b.Second.astype(float).astype(int)))
    b["row"] = np.arange(len(b))
    return b


def bard_geometry(b):
    """Grandezze BARD ricalcolate dai centroidi con la nostra definizione (P3 §5)."""
    out = []
    for r in b.itertuples(index=False):
        P, N = (r.PLongitude, r.PLatitude), (r.NLongitude, r.NLatitude)
        t_pn = geo.tilt_deg(N, P)  # |angolo| < 90 se la positiva e' a ovest
        lead_sign = 1 if abs(t_pn) < 90.0 else -1
        lead, foll = (P, N) if lead_sign == 1 else (N, P)
        tilt = geo.tilt_deg(lead, foll)
        sina = np.sin(np.radians(tilt))
        out.append(dict(b_leading_geom=lead_sign,
                        b_asin=float(np.degrees(np.arcsin(np.clip(sina, -1, 1)))),
                        b_gamma=float(np.sign(r.BMRLatitude) * np.degrees(np.arcsin(np.clip(sina, -1, 1)))),
                        b_sep_deg=geo.great_circle_deg(*P, *N)))
    return pd.concat([b.reset_index(drop=True), pd.DataFrame(out)], axis=1)


def conventions(b, meta_times):
    """P3 §2: verifiche interne; stato 'determinata' o 'indeterminata'."""
    rows = []
    lead_lon = np.where(b["LeadingPolarity"] > 0, b["PLongitude"], b["NLongitude"])
    foll_lon = np.where(b["LeadingPolarity"] > 0, b["NLongitude"], b["PLongitude"])
    f_dir = float((wrap(lead_lon - foll_lon) > 0).mean())
    rows.append(dict(convention="direzione longitudini", statistic="F_dir", value=f_dir,
                     result="ovest" if f_dir >= 0.90 else ("est" if f_dir <= 0.10 else "indeterminata")))
    m = pd.merge_asof(b.sort_values("t"), meta_times, on="t", direction="nearest",
                      tolerance=pd.Timedelta(hours=2))
    has = m["CRLN_OBS"].notna()
    d = np.abs(wrap(m.loc[has, "BMRLongitude"] - m.loc[has, "CRLN_OBS"]))
    f_car = float((d <= 90).mean())
    rows.append(dict(convention="riferimento longitudini", statistic=f"F_car (n={int(has.sum())})", value=f_car,
                     result="Carrington" if f_car >= 0.95 else "indeterminata"))
    # P3c §1: verifica A, Tilt_rel riproduce la formula piana
    lp = b["LeadingPolarity"] > 0
    lat_l = np.where(lp, b["PLatitude"], b["NLatitude"])
    lat_f = np.where(lp, b["NLatitude"], b["PLatitude"])
    dlon = np.abs(wrap(lead_lon - foll_lon))
    planar = np.degrees(np.arctan2(lat_l - lat_f, dlon * np.cos(np.radians(b["BMRLatitude"]))))
    f_a = float((np.abs(b["Tilt_rel"] - planar) <= 0.01).mean())
    rows.append(dict(convention="Tilt_rel formula piana (verifica A)", statistic="frazione entro 0,01°", value=f_a,
                     result="formula piana confermata" if f_a >= 0.99 else "non confermata"))
    # P3c §2: verifica B, compatibilita' con la formula sferica (non cieca, non validazione)
    d = np.abs(b["Tilt_rel"] + b["b_asin"])
    nonnull = np.abs(b["b_asin"]) >= 0.5
    f_sign = float((np.sign(b.loc[nonnull, "Tilt_rel"]) == -np.sign(b.loc[nonnull, "b_asin"])).mean()) if nonnull.any() else np.nan
    f_1deg = float((d <= 1.0).mean())
    q = np.percentile(d, [50, 90, 99, 100])
    rows.append(dict(convention="Tilt_rel compatibilita' sferica (verifica B)",
                     statistic=f"segno {f_sign:.4f}; entro 1° {f_1deg:.4f}; |diff| p50/p90/p99/max "
                               f"{q[0]:.3f}/{q[1]:.3f}/{q[2]:.3f}/{q[3]:.3f}",
                     value=min(f_sign, f_1deg),
                     result="compatibile" if (f_sign >= 0.99 and f_1deg >= 0.99) else "non compatibile"))
    exp24 = np.where(b["BMRLatitude"] > 0, -1, 1)
    f_hale = float((b["Hale"] == (b["LeadingPolarity"] == exp24)).mean())
    rows.append(dict(convention="significato Hale", statistic="accordo con leading attesa ciclo 24", value=f_hale,
                     result="Hale = leading attesa ciclo 24" if f_hale >= 0.99 else "indeterminata"))
    return pd.DataFrame(rows)


def suspensions(conv):
    """P3c §3: quali confronti sono sospesi, dagli esiti delle verifiche di un livello."""
    res = conv.set_index("convention")["result"]
    all_off = (res.get("direzione longitudini") == "indeterminata"
               or res.get("riferimento longitudini") == "indeterminata")
    return {"all": bool(all_off), "hale_published": bool(res.get("significato Hale") == "indeterminata")}


# ---------------------------------------------------------------- abbinamento

def candidates(b, meta, lon_shift=None):
    """Coppie ammesse (P3 §4): record orario piu' vicino entro ±1 h, stesso emisfero, ±3°, ±6°."""
    meta = meta.sort_values("t").reset_index(drop=True)
    tt = meta["t"].to_numpy()
    lonB = b["BMRLongitude"].to_numpy(float) + (0 if lon_shift is None else lon_shift)
    rows = []
    for k, r in enumerate(b.itertuples(index=False)):
        lo = np.searchsorted(tt, np.datetime64(r.t - pd.Timedelta(hours=DT_MAX_H)), "left")
        hi = np.searchsorted(tt, np.datetime64(r.t + pd.Timedelta(hours=DT_MAX_H)), "right")
        if hi <= lo:
            continue
        c = meta.iloc[lo:hi].copy()
        c["dt_h"] = (c["t"] - r.t).abs().dt.total_seconds() / 3600
        c = c.sort_values(["HARPNUM", "dt_h"]).groupby("HARPNUM").head(1)
        lat = c["LAT_FWT"].to_numpy(float)
        L = (c["LON_FWT"].to_numpy(float) + c["CRLN_OBS"].to_numpy(float)) % 360
        dlat = lat - r.BMRLatitude
        dlon = wrap(L - lonB[k])
        ok = (np.sign(lat) == np.sign(r.BMRLatitude)) & (np.abs(dlat) <= DLAT) & (np.abs(dlon) <= DLON)
        for j in np.where(ok)[0]:
            rows.append(dict(row=int(r.row), HARPNUM=int(c["HARPNUM"].iloc[j]), T_REC=c["T_REC"].iloc[j],
                             QUALITY=int(c["QUALITY"].iloc[j]), dt_h=float(c["dt_h"].iloc[j]),
                             dlat=float(dlat[j]), dlon=float(dlon[j]),
                             d=float(np.hypot(dlat[j] / DLAT, dlon[j] / DLON))))
    return pd.DataFrame(rows, columns=["row", "HARPNUM", "T_REC", "QUALITY", "dt_h", "dlat", "dlon", "d"])


def assign_one_to_one(pairs):
    """Ordine globale per d, poi numero HARP, poi riga BARD; ogni riga e ogni HARP al piu' una volta."""
    used_r, used_h, keep = set(), set(), []
    for i, p in pairs.sort_values(["d", "HARPNUM", "row"]).iterrows():
        if p["row"] in used_r or p["HARPNUM"] in used_h:
            continue
        used_r.add(p["row"])
        used_h.add(p["HARPNUM"])
        keep.append(i)
    return pairs.loc[keep].sort_values("row").reset_index(drop=True)


def random_control(b, meta):
    out = []
    for k in range(NREP_CTRL):
        rng = np.random.default_rng(SEED_CTRL + k)
        m = assign_one_to_one(candidates(b, meta, rng.uniform(0, 360, len(b))))
        out.append(dict(rep=k, n_bard=len(b), n_matched=len(m), fraction=len(m) / len(b)))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- statistiche (P3 §5, P3b)

def axial_delta(g1, g2):
    return np.abs(((np.asarray(g1, float) - np.asarray(g2, float) + 90.0) % 180.0) - 90.0)


def fisher_lee(g1, g2):
    """Correlazione circolare di Fisher & Lee sugli angoli raddoppiati; NaN se non definita (P3b §4)."""
    a = np.radians(2 * np.asarray(g1, float))
    b = np.radians(2 * np.asarray(g2, float))
    n = len(a)
    if n < 3:
        return np.nan
    A = (np.cos(a) * np.cos(b)).sum()
    B = (np.sin(a) * np.sin(b)).sum()
    C = (np.cos(a) * np.sin(b)).sum()
    D = (np.sin(a) * np.cos(b)).sum()
    E, F = np.cos(2 * a).sum(), np.sin(2 * a).sum()
    G, H = np.cos(2 * b).sum(), np.sin(2 * b).sum()
    d1, d2 = n * n - E * E - F * F, n * n - G * G - H * H
    if d1 <= 1e-12 or d2 <= 1e-12:
        return np.nan
    return float(4 * (A * B - C * D) / np.sqrt(d1 * d2))


def indicators(df):
    """Indicatori di P3 §5 / P3b su un insieme di coppie."""
    out = {"n": len(df)}
    if len(df) == 0:
        return out
    delta = axial_delta(df["gamma"], df["b_gamma"])
    out["median_axial_delta_deg"] = float(np.median(delta))
    out["rho_fisher_lee"] = fisher_lee(df["gamma"], df["b_gamma"])
    out["spearman_tilt_fixed"] = float(spearmanr(df["gamma"], df["b_gamma"]).statistic) if len(df) > 2 else np.nan
    out["frac_leading_equal"] = float((df["leading_sign"] == df["b_leading_geom"]).mean())
    out["frac_hale_recomputed_equal"] = float((df["hale_ours_rec"] == df["hale_bard_rec"]).mean())
    out["frac_hale_published_equal"] = float(((df["hale_sign"] == 1) == df["Hale"]).mean())
    out["spearman_separation"] = float(spearmanr(df["sep_deg"], df["b_sep_deg"]).statistic) if len(df) > 2 else np.nan
    out["median_separation_ratio"] = float(np.median(df["sep_deg"] / df["b_sep_deg"]))
    out["median_abs_dlat_deg"] = float(np.median(np.abs(df["lat_mean_deg"] - df["BMRLatitude"])))
    out["median_flux_ratio"] = float(np.median(df["phi_mx"] / (df["PFlux"] + df["NFlux"].abs())))
    return out


def family_bootstrap(df, nboot=NBOOT, seed=SEED_BOOT):
    """Bootstrap per famiglie P1e (P3 §5): IC 95% di ogni indicatore; repliche degeneri di rho_FL contate."""
    fams = df["family_id"].to_numpy()
    u = np.unique(fams)
    idx_by_f = {f: np.where(fams == f)[0] for f in u}
    rng = np.random.default_rng(seed)
    reps = []
    for _ in range(nboot):
        pick = rng.integers(0, len(u), len(u))
        rows = np.concatenate([idx_by_f[u[k]] for k in pick])
        reps.append(indicators(df.iloc[rows]))
    reps = pd.DataFrame(reps)
    res = {"n_families": int(len(u)), "n_boot": nboot}
    for c in reps.columns:
        if c == "n":
            continue
        v = reps[c].to_numpy(float)
        ok = np.isfinite(v)
        res[f"{c}_n_degenerate"] = int((~ok).sum())
        res[f"{c}_ci95_lo"], res[f"{c}_ci95_hi"] = (np.percentile(v[ok], [2.5, 97.5]) if ok.any()
                                                    else (np.nan, np.nan))
    return res


def outcome(ind, boot):
    """Criteri operativi di P3 §5 come modificati da P3b; tutti richiesti."""
    crit = []
    deg = boot.get("rho_fisher_lee_n_degenerate", 0) / max(boot.get("n_boot", 1), 1)
    fl_eval = np.isfinite(ind.get("rho_fisher_lee", np.nan)) and deg <= 0.01
    crit.append(("tilt: mediana delta <= 10", ind.get("median_axial_delta_deg", np.inf) <= 10,
                 boot.get("median_axial_delta_deg_ci95_hi", np.inf) <= 10))
    crit.append(("tilt: IC95 rho_FL inferiore > 0" + ("" if fl_eval else " (non valutabile)"),
                 bool(fl_eval and boot.get("rho_fisher_lee_ci95_lo", -1) > 0),
                 bool(fl_eval and boot.get("rho_fisher_lee_ci95_lo", -1) > 0)))
    crit.append(("leading >= 0.90", ind.get("frac_leading_equal", 0) >= 0.90,
                 boot.get("frac_leading_equal_ci95_lo", 0) >= 0.90))
    crit.append(("Hale ricalcolato >= 0.90", ind.get("frac_hale_recomputed_equal", 0) >= 0.90,
                 boot.get("frac_hale_recomputed_equal_ci95_lo", 0) >= 0.90))
    crit.append(("separazione Spearman >= 0.7", ind.get("spearman_separation", -1) >= 0.7,
                 boot.get("spearman_separation_ci95_lo", -1) >= 0.7))
    crit.append(("latitudine mediana |dlat| <= 1", ind.get("median_abs_dlat_deg", np.inf) <= 1,
                 boot.get("median_abs_dlat_deg_ci95_hi", np.inf) <= 1))
    tab = pd.DataFrame(crit, columns=["criterion", "point_estimate_ok", "ci95_within"])
    failed = tab.loc[~tab["point_estimate_ok"], "criterion"].tolist()
    verdict = "coerente con BARD (livello 1)" if not failed else "da investigare: " + "; ".join(failed)
    return tab, verdict, deg


# ---------------------------------------------------------------- misure SHARP

def our_side(pairs, cat, boundary, on=("HARPNUM", "T_REC")):
    """Colonne del nostro lato da un catalogo di misure v84 (C1 o C2) e Hale ricalcolato comune."""
    df = pairs.merge(cat, on=list(on), how="inner", suffixes=("", "_cat"))
    df["gamma"] = np.sign(df["lat_mean_deg"]) * np.degrees(np.arcsin(np.clip(df["sintilt"], -1, 1)))
    df["sep_deg"] = np.degrees(df["d_cm"] / R_CM)
    c_common = [cyc.assign_cycle(t.to_pydatetime(), lat, boundary)[0] for t, lat in zip(df["t"], df["BMRLatitude"])]
    exp = [cyc.expected_leading_sign(int(c), lat) for c, lat in zip(c_common, df["BMRLatitude"])]
    df["cycle_common"] = c_common
    df["hale_ours_rec"] = (df["leading_sign"].to_numpy() == np.array(exp)).astype(int)
    df["hale_bard_rec"] = (df["b_leading_geom"].to_numpy() == np.array(exp)).astype(int)
    return df


def measure_c1(records, boundary):
    from sharpbl.download_records import file_stem, record_dir
    rows = []
    for h, t in records:
        folder = record_dir(FITS_P3, t)
        stem = file_stem(h, t)
        try:
            br, hd = geo.read_sharp(folder / f"{stem}.Br.fits")
            bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
        except FileNotFoundError:
            continue
        v = measure.measure_v84(br, bm, hd, boundary=boundary)
        v.update(HARPNUM=h, T_REC=t)
        rows.append(v)
    return pd.DataFrame(rows)


def download_c1(records, workers=2):
    import drms
    from sharpbl.download_records import complete, do_batch
    todo = [(h, t) for h, t in records if not complete(FITS_P3, h, t)]
    client = drms.Client()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i in range(0, len(todo), 50):
            for attempt in range(4):
                try:
                    do_batch(client, todo[i:i + 50], FITS_P3, pool)
                    break
                except Exception as exc:  # rete o DRMS
                    print(f"C1 blocco {i // 50 + 1} tentativo {attempt + 1}: {exc!r}", flush=True)
    return sum(not complete(FITS_P3, h, t) for h, t in records)


# ---------------------------------------------------------------- esecuzione

def families():
    """Famiglie P1e delle HARP con record primario; le altre HARP sono famiglie da sole."""
    from sharpbl.recurrence import recurrences_p1e
    from sharpbl.run_p1 import primary_metadata
    pm, life = primary_metadata()
    return recurrences_p1e(pm, life)[["HARPNUM", "family_id"]]


def selection_counts(b, meta, pairs, m, df, label):
    """P3 §3: conteggi ed esclusioni per motivo; righe a parte per le regioni con D > 90° o senza CRLN_OBS."""
    tt = np.sort(meta["t"].to_numpy())
    has_rec = np.array([np.searchsorted(tt, np.datetime64(t + pd.Timedelta(hours=DT_MAX_H)), "right")
                        > np.searchsorted(tt, np.datetime64(t - pd.Timedelta(hours=DT_MAX_H)), "left")
                        for t in b["t"]])
    mt = meta[["t", "CRLN_OBS"]].drop_duplicates("t").sort_values("t")
    mm = pd.merge_asof(b[["row", "t", "BMRLongitude"]].sort_values("t"), mt, on="t", direction="nearest",
                       tolerance=pd.Timedelta(hours=2)).set_index("row").loc[b["row"]]
    far = (np.abs(wrap(mm["BMRLongitude"] - mm["CRLN_OBS"])) > 90).to_numpy() & mm["CRLN_OBS"].notna().to_numpy()
    no_crln = mm["CRLN_OBS"].isna().to_numpy()
    matched_rows = set(m["row"])
    ok_q = m[m["QUALITY"].isin(QUAL_OK)]
    meas = df if df is not None else pd.DataFrame(columns=["valid_bl", "phi_mx"])
    rows = [
        ("regioni BARD", len(b)),
        ("escluse: nessun record SHARP entro ±1 h", int((~has_rec).sum())),
        ("escluse: nessuna HARP in posizione (±3°, ±6°, stesso emisfero)", int(has_rec.sum() - pairs["row"].nunique())),
        ("escluse: non assegnate nell'abbinamento uno a uno", int(pairs["row"].nunique() - len(m))),
        ("abbinate uno a uno", len(m)),
        ("escluse: QUALITY non in {0, 0x80}", int(len(m) - len(ok_q))),
        ("escluse: misura non disponibile", int(len(ok_q) - len(meas))),
        ("escluse: valid_bl = 0", int((meas["valid_bl"] != 1).sum())),
        ("escluse: Phi < 1e21 Mx", int(((meas["valid_bl"] == 1) & (meas["phi_mx"] < PHI_MIN)).sum())),
        ("usate nel campione principale", int(((meas["valid_bl"] == 1) & (meas["phi_mx"] >= PHI_MIN)).sum())),
        ("a parte: regioni con D > 90° (convenzione Carrington)", int(far.sum())),
        ("a parte: di queste, abbinate", int(sum(1 for r, f in zip(b["row"], far) if f and r in matched_rows))),
        ("a parte: regioni senza CRLN_OBS entro 2 h", int(no_crln.sum())),
    ]
    return pd.DataFrame(rows, columns=["step", "count"]).assign(set=label)


def run_level(kind, meta, boundary, fam, skip_download, p1_cat):
    b = bard_geometry(load_bard(kind))
    if kind == "MDI":
        b = b[b["t"] >= pd.Timestamp("2010-05-01")].reset_index(drop=True)
        b["row"] = np.arange(len(b))
    meta_times = meta[["t", "CRLN_OBS"]].drop_duplicates("t").sort_values("t")
    conv = conventions(b, meta_times).assign(set=kind)
    susp = suspensions(conv)
    if susp["all"]:
        return dict(conv=conv, suspended=True)
    pairs = candidates(b, meta)
    m = assign_one_to_one(pairs).merge(b, on="row")
    ctrl = random_control(b, meta).assign(set=kind)
    ok = m[m["QUALITY"].isin(QUAL_OK)]
    records = sorted(set(zip(ok["HARPNUM"].astype(int), ok["T_REC"])))
    missing = 0 if skip_download else download_c1(records)
    c1 = measure_c1(records, boundary)
    res = dict(conv=conv, ctrl=ctrl, suspended=False, missing_c1=missing)
    out_sets = {}
    if len(c1):
        df = our_side(ok, c1, boundary).merge(fam, on="HARPNUM", how="left")
        df["family_id"] = df["family_id"].fillna(df["HARPNUM"])
        out_sets["C1"] = df
    if p1_cat is not None:
        for role in ("control", "primary"):
            sub = p1_cat[p1_cat["role"].isin([role, "both"])].drop(columns=["T_REC"]).copy()
            sub["T_REC_record"] = p1_cat.loc[sub.index, "T_REC"]
            df = our_side(ok.drop(columns=["T_REC"]), sub, boundary, on=("HARPNUM",))
            t_rec = pd.to_datetime(df["T_REC_record"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
            df["abs_dt_days"] = (t_rec - df["t"]).abs().dt.total_seconds() / 86400
            df = df.merge(fam, on="HARPNUM", how="left")
            df["family_id"] = df["family_id"].fillna(df["HARPNUM"])
            out_sets[f"C2_{role}"] = df
    summ, matches, sel = [], [], []
    for name, df in out_sets.items():
        main = df[(df["valid_bl"] == 1) & (df["phi_mx"] >= PHI_MIN)]
        ind = indicators(main)
        boot = family_bootstrap(main) if len(main) else {}
        if susp["hale_published"]:  # P3c §3: sospeso solo "Hale pubblicato"
            ind["frac_hale_published_equal"] = np.nan
            boot = {k: (np.nan if k.startswith("frac_hale_published_equal") else v) for k, v in boot.items()}
        row = dict(set=kind, comparison=name, **ind, **boot)
        if kind == "HMI" and name == "C1":
            tab, verdict, deg = outcome(ind, boot)
            row.update(outcome=verdict, rho_fl_degenerate_fraction=deg)
            res["criteria"] = tab
        else:
            row["outcome"] = "solo riportato"
        summ.append(row)
        matches.append(df.assign(set=kind, comparison=name))
        sel.append(selection_counts(b, meta, pairs, m, df, f"{kind}:{name}"))
    res.update(summary=pd.DataFrame(summ), matches=pd.concat(matches) if matches else pd.DataFrame(),
               selection=pd.concat(sel) if sel else selection_counts(b, meta, pairs, m, None, kind))
    return res


def main() -> int:
    from sharpbl.select_records import load_metadata
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()
    meta = load_metadata(ROOT / "data/sharp/metadata")[["HARPNUM", "T_REC", "t", "LAT_FWT", "LON_FWT",
                                                         "CRLN_OBS", "QUALITY"]]
    boundary = load_boundary()
    fam = families()
    p1_cat = None
    cat_path = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
    if cat_path.exists():
        c = pd.read_csv(cat_path, low_memory=False)
        if (c.get("complete_series", 0) == 1).all() and (c.get("validation_passed", 0) == 1).all():
            p1_cat = c
    if p1_cat is None:
        print("C2 non eseguito: catalogo P1 completo e validato non disponibile")
    OUT.mkdir(parents=True, exist_ok=True)
    st = stamp(("P1", "P1b", "P1c", "P1d", "P1e", "P3", "P3b", "P3c"))
    results = {k: run_level(k, meta, boundary, fam, args.skip_download, p1_cat) for k in ("HMI", "MDI")}
    pd.concat([r["conv"] for r in results.values()]).assign(**st).to_csv(OUT / "P3_BARD_CONVENTIONS.csv", index=False)
    for k, r in results.items():
        if r["suspended"]:
            print(f"livello {k}: direzione o riferimento delle longitudini indeterminati, confronti sospesi (P3c §3)")
    results = {k: r for k, r in results.items() if not r["suspended"]}
    if not results:
        return 3
    pd.concat([r["ctrl"] for r in results.values()]).assign(**st).to_csv(OUT / "P3_RANDOM_CONTROL.csv", index=False)
    pd.concat([r["selection"] for r in results.values()]).assign(**st).to_csv(OUT / "P3_BARD_SELECTION.csv", index=False)
    pd.concat([r["matches"] for r in results.values()]).assign(**st).to_csv(OUT / "P3_BARD_MATCHES.csv", index=False)
    summ = pd.concat([r["summary"] for r in results.values()])
    summ.assign(**st).to_csv(OUT / "P3_BARD_SUMMARY.csv", index=False)
    if "criteria" in results["HMI"]:
        results["HMI"]["criteria"].assign(**st).to_csv(OUT / "P3_BARD_CRITERIA.csv", index=False)
    print(summ[["set", "comparison", "n", "outcome"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
