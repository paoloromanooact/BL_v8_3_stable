"""Analisi descrittive esplorative per l'articolo (docs/EXPLORATORY_PLAN.md §4).

ESPLORATIVO, serie gia' osservata: nessuna analisi produce verdetti.

Uso: .venv/bin/python python/sharpbl/exploratory.py
Legge results/EXPLORATORY/FACTORIAL_BY_RECORD.csv.gz (solo se la riproduzione e' superata),
results/P1/P1_SBL_CATALOG_BY_HARP.csv, results/P3/P3_BARD_MATCHES.csv; scrive results/EXPLORATORY/.
"""
from __future__ import annotations

import hashlib
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl.provenance import ROOT, stamp  # noqa: E402

OUT = ROOT / "results/EXPLORATORY"
STATUS = "esplorativo, serie gia' osservata"
R_CM = 6.96e10
CODE = {"M": {1: -1, 33: 1}, "G": {"legacy": -1, "v84": 1}, "C": {"date": -1, "p1c": 1}}
EXTREME_OLD = (1, "legacy", "date")
EXTREME_NEW = (33, "v84", "p1c")


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def axial(a, b):
    return ((np.asarray(a, float) - np.asarray(b, float) + 90.0) % 180.0) - 90.0


# ---------------------------------------------------------------- 1. fattoriale: effetti

def wide(fac, col):
    w = fac.pivot_table(index=["HARPNUM", "T_REC"], columns=["M", "G", "C"], values=col, aggfunc="first")
    return w


def contrasts():
    """Coefficienti dei contrasti del disegno 2^3 (effetto = media(+) - media(-))."""
    combos = list(product((1, 33), ("legacy", "v84"), ("date", "p1c")))
    terms = {"M": ("M",), "G": ("G",), "C": ("C",), "MxG": ("M", "G"), "MxC": ("M", "C"), "GxC": ("G", "C"),
             "MxGxC": ("M", "G", "C")}
    coef = {}
    for t, fs in terms.items():
        v = []
        for m, g, c in combos:
            lev = {"M": CODE["M"][m], "G": CODE["G"][g], "C": CODE["C"][c]}
            v.append(np.prod([lev[f] for f in fs]))
        coef[t] = np.array(v) / 4.0
    return combos, coef


def effects_per_record(fac, quantities):
    """Effetti principali e interazioni per record, sul campione valido in tutte le 8 combinazioni."""
    combos, coef = contrasts()
    valid = wide(fac, "valid_bl")[combos]
    common = valid.index[(valid == 1).all(axis=1)]
    rows = []
    for q, kind in quantities.items():
        W = wide(fac, q)[combos].loc[common].to_numpy(float)
        if kind == "axial":   # tilt: differenze rispetto alla combinazione nuova, poi contrasti
            ref = W[:, combos.index(EXTREME_NEW)][:, None]
            W = axial(W, ref)
        if kind == "relative":
            scale = np.abs(W[:, combos.index(EXTREME_NEW)])[:, None]
            W = W / np.where(scale > 0, scale, np.nan)
        for t, cf in coef.items():
            e = W @ cf
            rows.append(dict(quantity=q, kind=kind, term=t, n=int(np.isfinite(e).sum()),
                             mean=float(np.nanmean(e)), median=float(np.nanmedian(e)),
                             median_abs=float(np.nanmedian(np.abs(e))), p90_abs=float(np.nanpercentile(np.abs(e), 90))))
    return pd.DataFrame(rows), common


def validity_effects(fac):
    combos, _ = contrasts()
    valid = wide(fac, "valid_bl")[combos]
    rows = [dict(item=f"validi in {c}", value=int((valid[c] == 1).sum())) for c in combos]
    rows.append(dict(item="validi in tutte le 8", value=int((valid == 1).all(axis=1).sum())))
    rows.append(dict(item="validi in nessuna", value=int((valid == 0).all(axis=1).sum())))
    for f, idx in (("M", 0), ("G", 1), ("C", 2)):
        changed = 0
        for c in combos:
            if (f == "M" and c[0] == 1) or (f == "G" and c[1] == "legacy") or (f == "C" and c[2] == "date"):
                other = list(c)
                other[idx] = {0: 33, 1: "v84", 2: "p1c"}[idx]
                changed += int((valid[c] != valid[tuple(other)]).sum())
        rows.append(dict(item=f"cambi di validita' commutando {f} (somma sulle 4 coppie)", value=changed))
    old, new = valid[EXTREME_OLD], valid[EXTREME_NEW]
    rows += [dict(item="v8.3 valido -> v8.4 non valido", value=int(((old == 1) & (new == 0)).sum())),
             dict(item="v8.3 non valido -> v8.4 valido", value=int(((old == 0) & (new == 1)).sum()))]
    return pd.DataFrame(rows)


def sbl_sums(fac, cat, common):
    """Somme di S_BL per CR ed emisfero, 8 combinazioni: (a) campione comune, (b) validita' propria."""
    prim = cat[cat["role"] != "control"][["HARPNUM", "T_REC", "CR"]]
    f = fac.merge(prim, on=["HARPNUM", "T_REC"])
    f["hem"] = np.where(f["lat_mean_deg"] >= 0, "N", "S")
    out = []
    common_set = set(common)
    f["in_common"] = [k in common_set for k in zip(f["HARPNUM"], f["T_REC"])]
    for sample, sub in (("comune (valido in tutte le 8)", f[f["in_common"]]), ("validita' propria", f[f["valid_bl"] == 1])):
        s = sub.groupby(["M", "G", "C", "CR", "hem"])["s_bl"].sum().reset_index()
        tot = s.groupby(["M", "G", "C"]).agg(sum_net=("s_bl", "sum"), sum_abs_cells=("s_bl", lambda x: x.abs().sum()),
                                             n_cells=("s_bl", "size")).reset_index()
        tot["sample"] = sample
        out.append(tot)
        w = s.pivot_table(index=["CR", "hem"], columns=["M", "G", "C"], values="s_bl", aggfunc="first").fillna(0.0)
        combos, coef = contrasts()
        W = w[combos].to_numpy(float)
        scale = np.median(np.abs(W[:, combos.index(EXTREME_NEW)]))
        for t, cf in coef.items():
            e = W @ cf
            out.append(pd.DataFrame([dict(sample=sample, term=t, median_abs_effect_cells=float(np.median(np.abs(e))),
                                          ratio_to_median_abs_cell=float(np.median(np.abs(e)) / scale),
                                          effect_on_total=float(e.sum()))]))
    return pd.concat(out, ignore_index=True)


def tilt_simple_effects(fac):
    """Effetti semplici assiali sul tilt: differenza modulo 180° tra due combinazioni che
    differiscono per un solo fattore (gli altri fissi). Evita medie di angoli assiali per livello."""
    combos, _ = contrasts()
    valid = wide(fac, "valid_bl")[combos]
    common = valid.index[(valid == 1).all(axis=1)]
    T = wide(fac, "tilt_reduced_deg")[combos].loc[common]
    lv = {0: (1, 33), 1: ("legacy", "v84"), 2: ("date", "p1c")}
    rows = []
    for idx, f in enumerate("MGC"):
        for c in combos:
            if c[idx] != lv[idx][0]:
                continue
            c2 = list(c)
            c2[idx] = lv[idx][1]
            d = np.abs(axial(T[tuple(c2)], T[c]))
            fixed = ", ".join(f"{'MGC'[k]}={c[k]}" for k in range(3) if k != idx)
            rows.append(dict(factor=f, fixed=fixed, n=len(d), median_abs_deg=float(np.median(d)),
                             p90_abs_deg=float(np.percentile(d, 90)), frac_gt_10deg=float(np.mean(d > 10))))
    return pd.DataFrame(rows)


def geometry_effect_vs_intensity(fac):
    """Effetto di G su S_BL per decile di |S_BL| v8.4: in mediane globali e relativo alla propria |S_BL|."""
    from scipy.stats import spearmanr
    combos, coef = contrasts()
    valid = wide(fac, "valid_bl")[combos]
    common = valid.index[(valid == 1).all(axis=1)]
    S = wide(fac, "s_bl")[combos].loc[common].to_numpy(float)
    P = wide(fac, "phi_mx")[combos].loc[common].to_numpy(float)
    new = combos.index(EXTREME_NEW)
    eG = np.abs(S @ coef["G"])
    absS, phi = np.abs(S[:, new]), P[:, new]
    med = np.median(absS)
    dec = pd.qcut(absS, 10, labels=False)
    t = pd.DataFrame({"decile_abs_sbl": dec, "eG_global": eG / med,
                      "eG_rel_own": eG / np.where(absS > 0, absS, np.nan)})
    out = t.groupby("decile_abs_sbl").agg(median_eG_in_global_medians=("eG_global", "median"),
                                          p90_eG_in_global_medians=("eG_global", lambda x: np.percentile(x, 90)),
                                          median_eG_relative_to_own=("eG_rel_own", "median")).reset_index()
    tail = eG / med > np.percentile(eG / med, 90)
    out.attrs = {}
    extra = pd.DataFrame([dict(decile_abs_sbl="riepilogo",
                               median_eG_in_global_medians=float(spearmanr(eG, absS).statistic),
                               p90_eG_in_global_medians=float(spearmanr(eG, phi).statistic),
                               median_eG_relative_to_own=float(np.mean(dec[tail] == 9)))])
    extra["note"] = ("colonne del riepilogo: Spearman(|eff G|, |S_BL|); Spearman(|eff G|, Phi); "
                     "frazione della coda (eff G > p90) nel decile piu' alto di |S_BL|")
    return pd.concat([out, extra], ignore_index=True)


# ---------------------------------------------------------------- 2. transizioni Hale

def hale_transitions(fac, cat):
    combos, _ = contrasts()
    prim = cat[cat["role"] != "control"][["HARPNUM", "T_REC"]]
    f = fac.merge(prim, on=["HARPNUM", "T_REC"])
    hale = wide(f, "hale_sign")[combos]
    valid = wide(f, "valid_bl")[combos]
    sbl = wide(f, "s_bl")[combos]
    old_ok = (valid[EXTREME_OLD] == 1) & hale[EXTREME_OLD].isin([1, -1])
    new_ok = (valid[EXTREME_NEW] == 1) & hale[EXTREME_NEW].isin([1, -1])
    den = old_ok & new_ok
    ho, hn = hale[EXTREME_OLD], hale[EXTREME_NEW]
    changed = den & (ho != hn)
    all8 = (valid == 1).all(axis=1) & hale.isin([1, -1]).all(axis=1)

    def attribute(row):
        v = {c: row[c] for c in combos}
        dep = []
        for name, idx in (("M", 0), ("G", 1), ("C", 2)):
            groups = {}
            for c, val in v.items():
                key = tuple(x for i, x in enumerate(c) if i != idx)
                groups.setdefault(key, set()).add((c[idx], val))
            if any(len({val for _, val in g}) > 1 for g in groups.values()):
                dep.append(name)
        return "+".join(dep) if dep else "nessuno"

    attr = pd.Series("non attribuibile (validita' o Hale non definiti in tutte le 8)", index=hale.index)
    attr[all8] = hale[all8].apply(attribute, axis=1)
    rows = [dict(item="denominatore: primari validi con Hale definito in v8.3 e v8.4", value=int(den.sum())),
            dict(item="Hale cambiato", value=int(changed.sum())),
            dict(item="Hale -> anti-Hale (v8.3 +1, v8.4 -1)", value=int((changed & (ho == 1)).sum())),
            dict(item="anti-Hale -> Hale (v8.3 -1, v8.4 +1)", value=int((changed & (ho == -1)).sum()))]
    for a, n in attr[changed].value_counts().items():
        rows.append(dict(item=f"attribuzione: dipende da {a}", value=int(n)))
    tot_new = sbl[EXTREME_NEW][new_ok].sum()
    rows.append(dict(item="S_BL v8.4 delle regioni con Hale cambiato / somma netta v8.4 dei primari validi",
                     value=float(sbl[EXTREME_NEW][changed].sum() / tot_new)))
    rows.append(dict(item="|S_BL| v8.4 delle regioni con Hale cambiato / somma |S_BL| v8.4",
                     value=float(sbl[EXTREME_NEW][changed].abs().sum() / sbl[EXTREME_NEW][new_ok].abs().sum())))
    per = pd.DataFrame({"hale_v83": ho[changed], "hale_v84": hn[changed], "attribution": attr[changed],
                        "s_bl_v83": sbl[EXTREME_OLD][changed], "s_bl_v84": sbl[EXTREME_NEW][changed]}).reset_index()
    return pd.DataFrame(rows), per


# ---------------------------------------------------------------- 3. concentrazione e cancellazione

def concentration(cat):
    a = cat[(cat["role"] != "control") & (cat["valid_bl"] == 1)].copy()
    rows = []
    groups = [("tutti", a)] + [(f"ciclo {c} {h}", g) for (c, h), g in a.groupby(["cycle", "hemisphere"])]
    for name, g in groups:
        s = g["s_bl"].to_numpy(float)
        order = np.argsort(-np.abs(s))
        n = len(s)
        base = dict(group=name, n=n, sum_pos=float(s[s > 0].sum()), sum_neg=float(s[s < 0].sum()),
                    sum_net=float(s.sum()), sum_abs=float(np.abs(s).sum()))
        for q in (0.01, 0.05, 0.10):
            k = max(1, int(round(q * n)))
            top = s[order[:k]]
            rows.append(dict(**base, top_fraction=q, k=k, top_share_of_abs=float(np.abs(top).sum() / np.abs(s).sum()),
                             top_net=float(top.sum()), net_without_top=float(s.sum() - top.sum()),
                             net_without_top_over_net=float((s.sum() - top.sum()) / s.sum()) if s.sum() else np.nan))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 4. primario contro controllo

def primary_vs_control(cat):
    p = cat[cat["role"] == "primary"].set_index("HARPNUM")
    c = cat[cat["role"] == "control"].set_index("HARPNUM")
    both = cat[cat["role"] == "both"]
    j = p.join(c, lsuffix="_p", rsuffix="_c", how="inner")
    j = j[(j["valid_bl_p"] == 1) & (j["valid_bl_c"] == 1)]
    tp = pd.to_datetime(j["T_REC_p"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    tc = pd.to_datetime(j["T_REC_c"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
    d = pd.DataFrame({
        "dt_days": (tc - tp).dt.total_seconds() / 86400,
        "abs_lon_primary": j["LON_FWT_p"].abs(), "abs_lon_control": j["LON_FWT_c"].abs(),
        "dlog10_phi": np.log10(j["phi_mx_c"] / j["phi_mx_p"]),
        "dsep_rel": j["d_cm_c"] / j["d_cm_p"] - 1,
        "dtilt_axial_deg": axial(j["tilt_reduced_deg_c"], j["tilt_reduced_deg_p"]),
        "hale_same": (j["hale_sign_c"] == j["hale_sign_p"]).astype(int),
        "s_bl_ratio": j["s_bl_c"] / j["s_bl_p"],
        "s_bl_same_sign": (np.sign(j["s_bl_c"]) == np.sign(j["s_bl_p"])).astype(int)})
    rows = [dict(item="HARP con primario e controllo distinti, entrambi validi", value=len(d)),
            dict(item="HARP in cui i due record coincidono (role = both)", value=len(both))]
    for col in d.columns:
        if col in ("hale_same", "s_bl_same_sign"):
            rows.append(dict(item=f"{col} (frazione)", value=f"{d[col].mean():.4f}"))
            continue
        q = np.nanpercentile(d[col], [16, 50, 84])
        rows.append(dict(item=f"{col} p16/p50/p84", value=f"{q[0]:.4g} / {q[1]:.4g} / {q[2]:.4g}"))
    return pd.DataFrame(rows), d.reset_index()


# ---------------------------------------------------------------- 5. C1/C2 sul sottoinsieme comune

def c1_c2_common():
    sys.path.insert(0, str(ROOT / "python"))
    from sharpbl import run_p3
    m = pd.read_csv(ROOT / "results/P3/P3_BARD_MATCHES.csv", low_memory=False)
    m = m[(m["set"] == "HMI") & (m["valid_bl"] == 1) & (m["phi_mx"] >= run_p3.PHI_MIN)]
    sets = {k: set(g["row"]) for k, g in m.groupby("comparison")}
    common = sets.get("C1", set()) & sets.get("C2_control", set()) & sets.get("C2_primary", set())
    rows = []
    for k in ("C1", "C2_control", "C2_primary"):
        g = m[(m["comparison"] == k) & m["row"].isin(common)]
        ind = run_p3.indicators(g)
        boot = run_p3.family_bootstrap(g)
        rows.append(dict(comparison=k, n_common=len(g), **{x: ind.get(x) for x in (
            "median_axial_delta_deg", "rho_fisher_lee", "frac_leading_equal", "spearman_separation",
            "median_abs_dlat_deg", "median_flux_ratio")},
            **{f"{x}_ci95": f"[{boot.get(x + '_ci95_lo', np.nan):.3g}; {boot.get(x + '_ci95_hi', np.nan):.3g}]"
               for x in ("median_axial_delta_deg", "rho_fisher_lee", "frac_leading_equal")}))
    return pd.DataFrame(rows)


def main() -> int:
    rep = pd.read_csv(OUT / "FACTORIAL_REPRODUCTION.csv")
    if rep["n_mismatch"].sum() != 0:
        print("riproduzione esatta non superata: il fattoriale non si analizza")
        return 2
    st = stamp(("P1", "P1b", "P1c", "P1d", "P1e"))
    cat_path = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
    st.update(status=STATUS, input_catalogue_sha256=sha_file(cat_path),
              input_factorial_sha256=sha_file(OUT / "FACTORIAL_BY_RECORD.csv.gz"))
    cat = pd.read_csv(cat_path, low_memory=False)
    fac = pd.read_csv(OUT / "FACTORIAL_BY_RECORD.csv.gz", low_memory=False)
    fac["d_cm"] = fac["d_cm"].astype(float)
    eff, common = effects_per_record(fac, {"phi_mx": "relative", "d_cm": "relative", "lat_mean_deg": "absolute",
                                           "tilt_reduced_deg": "axial", "s_bl": "relative"})
    out = {
        "FACTORIAL_EFFECTS_BY_RECORD_SUMMARY": eff,
        "FACTORIAL_VALIDITY": validity_effects(fac),
        "FACTORIAL_SBL_SUMS": sbl_sums(fac, cat, common),
        "FACTORIAL_TILT_SIMPLE_EFFECTS": tilt_simple_effects(fac),
        "FACTORIAL_G_EFFECT_BY_INTENSITY": geometry_effect_vs_intensity(fac),
    }
    ht, per = hale_transitions(fac, cat)
    out["HALE_TRANSITIONS"] = ht
    out["HALE_TRANSITIONS_BY_RECORD"] = per
    out["SBL_CONCENTRATION"] = concentration(cat)
    pvc, pvc_rec = primary_vs_control(cat)
    out["PRIMARY_VS_CONTROL"] = pvc
    out["PRIMARY_VS_CONTROL_BY_HARP"] = pvc_rec
    out["P3_C1_C2_COMMON_SUBSET"] = c1_c2_common()
    for name, df in out.items():
        df.assign(**st).to_csv(OUT / f"{name}.csv", index=False)
        print(f"== {name}")
        print(df.head(40).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
