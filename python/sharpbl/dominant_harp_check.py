"""Controllo delle HARP dominanti (piano docs/DOMINANT_HARP_PLAN.md, registrato in f805c5a).

Descrittivo: segnalazioni, sensibilita' misurate e schede visive per 20 HARP dominanti + 10 di controllo per
ciclo x emisfero. Non modifica il catalogo e non produce verdetti. Legge catalogo P1, confini del ciclo,
PRIMARY_VS_CONTROL_BY_HARP.csv e i FITS (Br, bitmap) dei record primari scelti.

    .venv/bin/python python/sharpbl/dominant_harp_check.py                 # esecuzione (dopo la validazione P2f)
    .venv/bin/python python/sharpbl/dominant_harp_check.py --limit 2 --out /tmp/prova   # prova tecnica, output a parte
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import cycle as cyc, geometry as geo, measure, run_p2  # noqa: E402
from sharpbl.cycle_boundary import load_boundary  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PLAN = ROOT / "docs/DOMINANT_HARP_PLAN.md"
FITS = ROOT / "data/sharp/fits"
OUT = ROOT / "results/DOMINANT"
FIG = ROOT / "figures/DOMINANT"
GROUPS = [(24, "N"), (24, "S"), (25, "N"), (25, "S")]
N_DOM, N_CTRL, SEED = 20, 10, 20261111
VARIANTS = {"P1": (100.0, 33), "thr300": (300.0, 33), "bmap1": (100.0, 1)}   # (soglia G, bitmap minimo)
THR = dict(m2_flux_out=0.20, m3_components=3, m3_frac=0.10, p1_imbalance=0.5, c_tilt=10.0, c_d=0.20,
           r1_lon=30.0, r2_lo=0.5, r2_hi=2.0, priority_share=0.25)


def dtilt_mod180(a, b):
    """Differenza di tilt ridotta modulo 180 DOPO la sottrazione (piano §3)."""
    if not (np.isfinite(a) and np.isfinite(b)):
        return np.nan
    return ((a - b + 90.0) % 180.0) - 90.0


# ---------------------------------------------------------------- campione (piano §2)

def select_sample(cat):
    base = cat[(cat["role"] != "control") & (cat["valid_bl"] == 1)].copy()
    n_other_cycle = int((~base["cycle"].isin([24, 25])).sum())
    base = base[base["cycle"].isin([24, 25])].copy()
    base["hem"] = np.where(base["lat_mean_deg"] >= 0, "N", "S")
    base["abs_sbl"] = base["s_bl"].abs()
    in_s = set(run_p2.samples(cat)["S"]["HARPNUM"])
    rng = np.random.default_rng(SEED)
    rows = []
    for c, h in GROUPS:
        g = base[(base["cycle"] == c) & (base["hem"] == h)].sort_values(["abs_sbl", "HARPNUM"], ascending=[False, True])
        tot_abs, tot_net = float(g["abs_sbl"].sum()), float(g["s_bl"].sum())
        dom = g.head(N_DOM)
        rest = g.drop(dom.index).sort_values("HARPNUM")
        idx = rng.choice(len(rest), size=min(N_CTRL, len(rest)), replace=False)
        ctrl = rest.iloc[np.sort(idx)]
        for kind, part in (("dominante", dom), ("controllo", ctrl)):
            for rank, (_, r) in enumerate(part.iterrows(), 1):
                rows.append(dict(group=f"{c}{h}", cycle=c, hem=h, kind=kind, rank=rank if kind == "dominante" else np.nan,
                                 HARPNUM=int(r["HARPNUM"]), T_REC=r["T_REC"], in_S=int(r["HARPNUM"] in in_s),
                                 s_bl_P1=float(r["s_bl"]), abs_sbl=float(r["abs_sbl"]), share_abs=float(r["abs_sbl"] / tot_abs),
                                 group_n=len(g), group_sum_abs=tot_abs, group_sum_net=tot_net,
                                 NOAA_NUM=r["NOAA_NUM"], NOAA_ARS=r["NOAA_ARS"], lon_mean_stony=r["lon_mean_stony"],
                                 tilt_P1_cat=r["tilt_deg"], d_P1_cat=r["d_cm"], phi_P1_cat=r["phi_mx"], hale_sign_cat=r["hale_sign"]))
    sel = pd.DataFrame(rows)
    sel.attrs["n_base"] = len(base)
    sel.attrs["n_other_cycle"] = n_other_cycle
    return sel


# ---------------------------------------------------------------- misure su una HARP (piano §3)

def centroids_tilt(br, bm, header, threshold, bmap_min, uniform):
    """Centroidi di polarita' con pesi |Br| (come measure_v84) o uniformi; stessa maschera e geometria sferica."""
    m = measure.base_mask(br, bm, bmap_min, measure.MAX_ABS_BR_G)
    lon, lat = geo.lonlat_maps(header, br.shape)
    strong = m & (np.abs(br) >= threshold) & np.isfinite(lon) & np.isfinite(lat)
    pos, neg = strong & (br >= threshold), strong & (br <= -threshold)
    if not (pos.any() and neg.any()):
        return dict(possible=0)
    wp = np.ones(int(pos.sum())) if uniform else br[pos]
    wn = np.ones(int(neg.sum())) if uniform else -br[neg]
    lp, ln = geo.weighted_centroid(lon[pos], lat[pos], wp), geo.weighted_centroid(lon[neg], lat[neg], wn)
    d_cm = float(np.radians(geo.great_circle_deg(*lp, *ln)) * geo.rsun_cm(header))
    leading = 1 if abs(geo.tilt_deg(ln, lp)) < 90.0 else -1
    lead, follow = (lp, ln) if leading == 1 else (ln, lp)
    tilt = geo.tilt_deg(lead, follow)
    return dict(possible=1, lon_pos=lp[0], lat_pos=lp[1], lon_neg=ln[0], lat_neg=ln[1], d_cm=d_cm, tilt_deg=tilt, leading_sign=leading)


def harp_checks(br, bm, header, boundary):
    area = geo.pixel_area_cm2(header)
    out = {}
    v = {}
    for name, (thr, bmin) in VARIANTS.items():
        v[name] = measure.measure_v84(br, bm, header, threshold=thr, bmap_min=bmin, boundary=boundary)
    p1 = v["P1"]
    # M1: maschera >= 33 sul bordo del riquadro
    m33 = measure.base_mask(br, bm, 33, measure.MAX_ABS_BR_G)
    m1 = measure.base_mask(br, bm, 1, measure.MAX_ABS_BR_G)
    border = int(m33[0, :].sum() + m33[-1, :].sum() + m33[1:-1, 0].sum() + m33[1:-1, -1].sum())
    out.update(M1_border_pixels=border, M1_flag=int(border > 0))
    # M2: flusso sopra soglia fuori della maschera >= 33 ma dentro bitmap >= 1
    strong = np.abs(br) >= VARIANTS["P1"][0]
    flux_in = float(np.abs(br[m33 & strong]).sum() * area)
    flux_out = float(np.abs(br[m1 & ~m33 & strong]).sum() * area)
    out.update(M2_flux_in=flux_in, M2_flux_out=flux_out, M2_ratio=flux_out / flux_in if flux_in > 0 else np.nan,
               M2_flag=int(flux_in > 0 and flux_out / flux_in > THR["m2_flux_out"]), M2_evaluable=int(flux_in > 0))
    # M3: componenti connesse (8-connettivita') per polarita' con >= 10 % del flusso di quella polarita'
    comps = {}
    for sgn, name in ((1, "pos"), (-1, "neg")):
        sel = m33 & (sgn * br >= VARIANTS["P1"][0])
        lab, n = ndimage.label(sel, structure=np.ones((3, 3)))
        tot = float(np.abs(br[sel]).sum())
        big = 0
        if n and tot > 0:
            fl = ndimage.sum(np.abs(br), lab, index=np.arange(1, n + 1))
            big = int((np.asarray(fl) / tot >= THR["m3_frac"]).sum())
        comps[name] = (int(n), big)
    out.update(M3_components_pos=comps["pos"][0], M3_big_pos=comps["pos"][1], M3_components_neg=comps["neg"][0], M3_big_neg=comps["neg"][1],
               M3_flag=int(max(comps["pos"][1], comps["neg"][1]) >= THR["m3_components"]))
    # P1: bilancio
    tot = p1["phi_pos_mx"] + p1["phi_neg_mx"]
    imb = abs(p1["phi_pos_mx"] - p1["phi_neg_mx"]) / tot if tot > 0 else np.nan
    out.update(P1_imbalance=imb, P1_flag=int(np.isfinite(imb) and imb > THR["p1_imbalance"]), P1_evaluable=int(tot > 0))
    # P2: leading robusto tra varianti (solo tra varianti con entrambe le polarita')
    leads = {k: int(v[k]["leading_sign"]) for k in VARIANTS if v[k]["leading_sign"] != 0}
    out.update(P2_leading_P1=leads.get("P1", 0), P2_leading_thr300=leads.get("thr300", 0), P2_leading_bmap1=leads.get("bmap1", 0),
               P2_n_comparable=len(leads), P2_flag=int(len(leads) >= 2 and len(set(leads.values())) > 1))
    # P3: Hale
    out.update(P3_hale_sign=int(p1["hale_sign"]), P3_flag=int(p1["hale_sign"] != 1))
    # C1: pesi uniformi contro |Br| (100 G, >= 33); controllo di riproduzione del ramo |Br| contro measure_v84
    cb = centroids_tilt(br, bm, header, *VARIANTS["P1"], uniform=False)
    cu = centroids_tilt(br, bm, header, *VARIANTS["P1"], uniform=True)
    if cb.get("possible") and np.isfinite(p1["tilt_deg"]):
        out["C1_repro_abs_dtilt_vs_measure"] = abs(dtilt_mod180(cb["tilt_deg"], p1["tilt_deg"]))
        out["C1_repro_rel_dd_vs_measure"] = abs(cb["d_cm"] / p1["d_cm"] - 1) if p1["d_cm"] > 0 else np.nan
    if cu.get("possible") and cb.get("possible") and p1["d_cm"] > 0:
        dt, dd = dtilt_mod180(cu["tilt_deg"], p1["tilt_deg"]), (cu["d_cm"] - p1["d_cm"]) / p1["d_cm"]
        out.update(C1_possible=1, C1_dtilt=dt, C1_dd_rel=dd, C1_flag=int(abs(dt) > THR["c_tilt"] or abs(dd) > THR["c_d"]),
                   C1_tilt_uniform=cu["tilt_deg"], C1_d_uniform=cu["d_cm"], C1_leading_uniform=cu["leading_sign"])
    else:
        out.update(C1_possible=0, C1_flag=0)
    # C2: soglia 300 contro 100 (pesi |Br|, >= 33)
    v3 = v["thr300"]
    if v3["leading_sign"] != 0 and np.isfinite(p1["tilt_deg"]) and p1["d_cm"] > 0:
        dt, dd = dtilt_mod180(v3["tilt_deg"], p1["tilt_deg"]), (v3["d_cm"] - p1["d_cm"]) / p1["d_cm"]
        out.update(C2_possible=1, C2_dtilt=dt, C2_dd_rel=dd, C2_flag=int(abs(dt) > THR["c_tilt"] or abs(dd) > THR["c_d"]))
    else:
        out.update(C2_possible=0, C2_flag=0)
    # valori per variante (sensibilita' misurate, piano §4)
    for k in VARIANTS:
        out.update({f"{k}_phi": v[k]["phi_mx"], f"{k}_d": v[k]["d_cm"], f"{k}_tilt": v[k]["tilt_deg"], f"{k}_s_bl": v[k]["s_bl"],
                    f"{k}_possible": int(v[k]["leading_sign"] != 0)})
    if cu.get("possible") and np.isfinite(p1["coslat"]):
        exp_lead = cyc.expected_leading_sign(int(p1["cycle"]), p1["lat_mean_deg"])
        hale_u = 1 if cu["leading_sign"] == exp_lead else -1
        out["uniform_s_bl"] = hale_u * p1["phi_mx"] * cu["d_cm"] * p1["coslat"] * float(np.sin(np.radians(cu["tilt_deg"])))
        out["uniform_possible"] = 1
    else:
        out["uniform_possible"] = 0
    out["P1_repro_s_bl"] = p1["s_bl"]
    out["P1_repro_cycle"] = p1["cycle"]
    return out, v, cb, cu, m33, m1


def figure(harp, br, header, p1, cb, cu, m33, m1, path, info):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    lon, lat = geo.lonlat_maps(header, br.shape)
    fig, ax = plt.subplots(figsize=(8, 5))
    vmax = min(1500.0, float(np.nanpercentile(np.abs(br), 99.5)) or 1.0)
    ax.imshow(br, cmap="gray", vmin=-vmax, vmax=vmax, origin="lower")
    ax.contour(m1.astype(int), levels=[0.5], colors="cyan", linewidths=0.6)
    ax.contour(m33.astype(int), levels=[0.5], colors="yellow", linewidths=0.8)

    def pix(lo, la):
        dlon = (lon - lo + 180.0) % 360.0 - 180.0          # i centroidi sono in (-180, 180], la mappa in [0, 360)
        j = np.unravel_index(np.nanargmin(dlon ** 2 + (lat - la) ** 2), br.shape)
        return j[1], j[0]
    for c, col, lab in ((cb, "red", "|Br|"), (cu, "lime", "uniformi")):
        if c.get("possible"):
            xp, yp = pix(c["lon_pos"], c["lat_pos"]); xn, yn = pix(c["lon_neg"], c["lat_neg"])
            ax.plot([xn, xp], [yn, yp], "-", color=col, lw=1.2, label=f"centroidi {lab}")
            ax.plot(xp, yp, "o", color=col, ms=5); ax.plot(xn, yn, "s", color=col, ms=5)
    ax.legend(loc="upper right", fontsize=7)
    ax.set_title(f"HARP {harp}  {header.get('T_REC', '')}  {info}", fontsize=8)
    ax.set_xlabel("Phi %.2e Mx  d %.2e cm  tilt %.1f deg  S_BL %.2e" % (p1["phi_mx"], p1["d_cm"], p1["tilt_deg"], p1["s_bl"]), fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- sintesi (piano §4)

MEAS_FLAGS = ["M1_flag", "M2_flag", "M3_flag", "P2_flag", "C1_flag", "C2_flag"]
ALL_FLAGS = MEAS_FLAGS + ["P1_flag", "P3_flag", "N1_flag", "R1_flag", "R2_flag"]


def summarize(tab):
    rows, var_rows = [], []
    for grp, g in tab.groupby("group", sort=False):
        tot_abs, tot_net = float(g["group_sum_abs"].iloc[0]), float(g["group_sum_net"].iloc[0])
        r = dict(group=grp, n_group=int(g["group_n"].iloc[0]), sum_abs=tot_abs, sum_net=tot_net,
                 share_examined_dominant=float(g.loc[g["kind"] == "dominante", "abs_sbl"].sum() / tot_abs))
        for f in ALL_FLAGS:
            r[f"{f}_dominante"] = int(g.loc[g["kind"] == "dominante", f].sum())
            r[f"{f}_controllo"] = int(g.loc[g["kind"] == "controllo", f].sum())
        anym = g[MEAS_FLAGS].max(axis=1) == 1
        share = float(g.loc[anym, "abs_sbl"].sum() / tot_abs)
        r.update(share_abs_with_measurement_flag=share, priority=int(share > THR["priority_share"]))
        rows.append(r)
        for vname in ("thr300", "bmap1", "uniform"):
            ok = g[f"{vname}_possible"] == 1
            diff = (g.loc[ok, f"{vname}_s_bl"] - g.loc[ok, "s_bl_P1"])
            var_rows.append(dict(group=grp, variant=vname, n_examined=len(g), n_comparable=int(ok.sum()),
                                 share_abs_comparable=float(g.loc[ok, "abs_sbl"].sum() / tot_abs),
                                 delta_sum=float(diff.sum()), delta_rel_sum_abs=float(diff.sum() / tot_abs),
                                 delta_rel_sum_net=float(diff.sum() / tot_net) if tot_net != 0 else np.nan,
                                 max_abs_delta_rel_sum_abs=float(diff.abs().max() / tot_abs) if ok.any() else np.nan))
    return pd.DataFrame(rows), pd.DataFrame(var_rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="prova tecnica: solo le prime N HARP")
    ap.add_argument("--out", default=None, help="cartella di output alternativa (prova tecnica)")
    a = ap.parse_args()
    out = Path(a.out) if a.out else OUT
    fig_dir = out / "figures" if a.out else FIG
    out.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    cat = pd.read_csv(ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv", low_memory=False)
    boundary = load_boundary()
    pvc = pd.read_csv(ROOT / "results/EXPLORATORY/PRIMARY_VS_CONTROL_BY_HARP.csv").set_index("HARPNUM")
    sel = select_sample(cat)
    st = stamp(("P1", "P1b", "P1c", "P1d", "P1e"))
    st["sha256_DOMINANT_HARP_PLAN"] = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    st["n_base_primary_valid"] = sel.attrs["n_base"]
    st["n_excluded_other_cycle"] = sel.attrs["n_other_cycle"]
    st["status"] = "controllo descrittivo, nessun verdetto"
    sel.assign(**st).to_csv(out / "DOMINANT_HARP_SELECTION.csv", index=False)
    todo = sel.head(a.limit) if a.limit else sel
    rows, fits_rows = [], []
    for _, r in todo.iterrows():
        harp, t_rec = int(r["HARPNUM"]), r["T_REC"]
        folder, stem = record_dir(FITS, t_rec), file_stem(harp, t_rec)
        paths = [folder / f"{stem}.Br.fits", folder / f"{stem}.bitmap.fits"]
        for p in paths:
            fits_rows.append(dict(HARPNUM=harp, file=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        br, h = geo.read_sharp(paths[0])
        bm, _ = geo.read_sharp(paths[1])
        chk, v, cb, cu, m33, m1 = harp_checks(br, bm, h, boundary)
        row = dict(r)
        row.update(chk)
        row["N1_flag"] = int(pd.notna(r["NOAA_NUM"]) and r["NOAA_NUM"] >= 2)
        row["R1_flag"] = int(np.isfinite(r["lon_mean_stony"]) and abs(r["lon_mean_stony"]) > THR["r1_lon"])
        if harp in pvc.index:
            q = pvc.loc[harp]
            ratio, same = float(q["s_bl_ratio"]), int(q["s_bl_same_sign"])
            if r["s_bl_P1"] == 0 or not np.isfinite(ratio):
                row.update(R2_status="non valutabile", R2_ratio=np.nan, R2_flag=0)
            else:
                row.update(R2_status="valutato", R2_ratio=ratio, R2_same_sign=same,
                           R2_flag=int(ratio < THR["r2_lo"] or ratio > THR["r2_hi"] or same == 0))
        else:
            row.update(R2_status="non disponibile", R2_ratio=np.nan, R2_flag=0)
        row["repro_s_bl_rel_diff"] = abs(chk["P1_repro_s_bl"] / r["s_bl_P1"] - 1) if r["s_bl_P1"] != 0 else np.nan
        flags = [f for f in ALL_FLAGS if row.get(f) == 1]
        figure(harp, br, h, v["P1"], cb, cu, m33, m1, fig_dir / f"{harp}.png", f"{r['group']} {r['kind']}  flag: {' '.join(flags) or 'nessuno'}")
        rows.append(row)
        print(f"{r['group']} {r['kind']:9s} HARP {harp:5d}  flag: {' '.join(flags) or '-'}", flush=True)
    tab = pd.DataFrame(rows)
    tab.assign(**st).to_csv(out / "DOMINANT_HARP_CHECKS.csv", index=False)
    pd.DataFrame(fits_rows).assign(**st).to_csv(out / "DOMINANT_HARP_FITS_SHA256.csv", index=False)
    if not a.limit:
        summ, var = summarize(tab)
        summ.assign(**st).to_csv(out / "DOMINANT_HARP_SUMMARY.csv", index=False)
        var.assign(**st).to_csv(out / "DOMINANT_HARP_VARIANTS.csv", index=False)
        with pd.option_context("display.width", 250, "display.max_columns", 40):
            print(summ.round(3).to_string(index=False))
            print(var.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
