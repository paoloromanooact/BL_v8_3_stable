"""Esecuzione del protocollo P1 (con P1b, P1c e P1d): catalogo S_BL per HARP e somme per CR.

Uso: .venv/bin/python python/sharpbl/run_p1.py [--workers 4] [--allow-missing]

Legge results/P1/P1_RECORD_SELECTION.csv, CYCLE_BOUNDARY_FITS.csv e i FITS in
data/sharp/fits/. Per ogni record calcola il metodo v84 e il metodo legacy
(v8.3). Scrive in results/P1/:
  P1_SBL_CATALOG_BY_HARP.csv   una riga per record (primario e controllo)
  P1_SBL_BY_CR_HEMISPHERE.csv  somme per CR, emisfero e variante (A, B, C, D, E, L)
  P1_LEGACY_VS_V84.csv         confronto per regione e per CR (P1 §7b)
  P1_CHECKS.csv                controlli (P1 §8, P1b §3, P1c §3, P1d §3-4)
Senza --allow-missing si ferma se manca qualche record (serie definitiva);
con --allow-missing usa i record presenti (solo per provare lo script).
Ogni output porta due flag: complete_series (tutti i record presenti) e
validation_passed (controlli obbligatori superati: il metodo legacy riproduce il
caso di prova di Paolo, i test sintetici passano). Se un controllo obbligatorio
fallisce lo script esce con codice 2; run_p2.py richiede entrambi i flag a 1.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import geometry as geo  # noqa: E402
from sharpbl import measure  # noqa: E402
from sharpbl.cycle_boundary import load_boundary  # noqa: E402
from sharpbl.download_records import complete, file_stem, record_dir  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402
from sharpbl.recurrence import recurrences  # noqa: E402
from sharpbl.select_records import load_metadata  # noqa: E402

OUT = ROOT / "results/P1"
FITS = ROOT / "data/sharp/fits"
SEED = 20261103
NBOOT = 2000
MANDATORY_CHECKS = ["1_legacy_reproduces_test_case", "2_synthetic_tests_pass"]
V84_COLS = ["phi_mx", "phi_pos_mx", "phi_neg_mx", "d_cm", "lat_mean_deg", "coslat", "lon_mean_stony",
            "lon_pos", "lat_pos", "lon_neg", "lat_neg", "tilt_deg", "tilt_reduced_deg", "sintilt",
            "leading_sign", "expected_leading_sign", "hale_sign", "cycle", "cycle_state", "p_new",
            "s_bl", "d_axial_g", "d_axial_bal_g", "nmask", "npos", "nneg", "quality_flag",
            "quality_string", "valid_bl", "diagnostic_reason", "suspicious_flag"]
LEG_COLS = ["phi_mx", "d_cm", "lat_mean_deg", "tilt_deg", "tilt_reduced_deg", "sintilt", "leading_sign",
            "hale_sign", "cycle", "s_bl", "valid_bl", "quality_string", "diagnostic_reason"]
KEY_COLS = ["CAR_ROT", "CRLN_OBS", "LAT_FWTPOS", "LON_FWTPOS", "LAT_FWTNEG", "LON_FWTNEG", "USFLUX"]

_BOUNDARY = None


def _init():
    global _BOUNDARY
    _BOUNDARY = load_boundary()


def measure_record(args):
    harp, t_rec = args
    folder = record_dir(FITS, t_rec)
    stem = file_stem(harp, t_rec)
    br, h = geo.read_sharp(folder / f"{stem}.Br.fits")
    bm, _ = geo.read_sharp(folder / f"{stem}.bitmap.fits")
    v = measure.measure_v84(br, bm, h, boundary=_BOUNDARY)
    leg = measure.measure_legacy(br, bm, h)
    row = {"HARPNUM": harp, "T_REC": t_rec}
    row.update({c: v[c] for c in V84_COLS})
    row.update({f"leg_{c}": leg[c] for c in LEG_COLS})
    row.update({f"key_{k}": h.get(k) for k in KEY_COLS})
    return row


def recurrence_table(sel):
    """P1d §1: ricomparse dai metadati dei record primari (tutti, anche quelli non scaricati)."""
    full = pd.read_csv(OUT / "P1_RECORD_SELECTION.csv")
    prim = full[full["role"] != "control"][["HARPNUM", "T_REC"]]
    meta = load_metadata(ROOT / "data/sharp/metadata")[["HARPNUM", "T_REC", "LAT_FWT", "LON_FWT", "CRLN_OBS"]]
    prim = prim.merge(meta, on=["HARPNUM", "T_REC"], how="left")
    return recurrences(prim)


def build_catalog(sel, workers):
    jobs = list(zip(sel["HARPNUM"].astype(int), sel["T_REC"]))
    with ProcessPoolExecutor(max_workers=workers, initializer=_init) as pool:
        rows = list(pool.map(measure_record, jobs, chunksize=20))
    cat = sel.drop(columns=[c for c in sel.columns if c.startswith(("sha256_", "git_"))]).merge(
        pd.DataFrame(rows), on=["HARPNUM", "T_REC"])
    cat = cat.merge(recurrence_table(sel), on="HARPNUM", how="left")
    cat["CR"] = np.floor(pd.to_numeric(cat["key_CAR_ROT"], errors="coerce")).astype("Int64")
    cat["hemisphere"] = np.where(cat["lat_mean_deg"] >= 0, "N", "S")
    cat.loc[~np.isfinite(cat["lat_mean_deg"]), "hemisphere"] = ""
    cat["leg_hemisphere"] = np.where(cat["leg_lat_mean_deg"] >= 0, "N", "S")
    cat.loc[~np.isfinite(cat["leg_lat_mean_deg"]), "leg_hemisphere"] = ""
    return cat


def variants(cat):
    prim = cat[cat["role"] != "control"]
    a = prim[prim["valid_bl"] == 1]
    v = {
        "A": a,
        "B": a[a["cycle_state"] != "AMBIGUOUS"],
        "C": a[a["NOAA_NUM"] == 1],
        "D": a[a["qual_0x80"] == 0],
        "E": a[a["family_rank"] == 0],
    }
    leg = prim[prim["leg_valid_bl"] == 1].copy()
    for c in ("s_bl", "phi_mx"):
        leg[c] = leg[f"leg_{c}"]
    leg["hemisphere"] = leg["leg_hemisphere"]
    leg["d_axial_g"] = np.nan  # il metodo v8.3 non calcola il dipolo
    leg["d_axial_bal_g"] = np.nan
    v["L"] = leg
    return v


def aggregate(cat):
    rng = np.random.default_rng(SEED)
    qty = {"s_bl": "sum_s_bl_mxcm", "d_axial_g": "sum_d_g", "d_axial_bal_g": "sum_d_bal_g", "phi_mx": "sum_phi_mx"}
    rows = []
    for name, df in variants(cat).items():
        df = df[df["hemisphere"] != ""]
        for (cr, hem), g in df.groupby(["CR", "hemisphere"], sort=True):
            n = len(g)
            row = {"variant": name, "CR": int(cr), "hemisphere": hem, "n_regions": n}
            idx = rng.integers(0, n, size=(NBOOT, n))
            for col, out in qty.items():
                x = g[col].to_numpy(float)
                row[out] = float(np.nansum(x)) if np.isfinite(x).any() else np.nan
                if np.isfinite(x).any():
                    b = np.nansum(x[idx], axis=1)
                    row[f"{out}_p16"], row[f"{out}_p84"] = np.percentile(b, [16, 84])
                else:
                    row[f"{out}_p16"] = row[f"{out}_p84"] = np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def legacy_vs_v84(cat, agg):
    prim = cat[cat["role"] != "control"]
    reg = pd.DataFrame({
        "level": "region", "HARPNUM": prim["HARPNUM"], "T_REC": prim["T_REC"], "CR": prim["CR"],
        "s_bl_v84": prim["s_bl"], "s_bl_legacy": prim["leg_s_bl"],
        "tilt_reduced_v84": prim["tilt_reduced_deg"], "tilt_reduced_legacy": prim["leg_tilt_reduced_deg"],
        "lat_v84": prim["lat_mean_deg"], "lat_legacy": prim["leg_lat_mean_deg"],
        "hale_v84": prim["hale_sign"], "hale_legacy": prim["leg_hale_sign"],
        "valid_v84": prim["valid_bl"], "valid_legacy": prim["leg_valid_bl"],
    })
    reg["hale_changed"] = ((reg["hale_v84"] != reg["hale_legacy"]) & (reg["hale_v84"] != 0)
                           & (reg["hale_legacy"] != 0)).astype(int)
    reg["valid_changed"] = (reg["valid_v84"] != reg["valid_legacy"]).astype(int)
    a = agg[agg["variant"] == "A"].set_index(["CR", "hemisphere"])
    lg = agg[agg["variant"] == "L"].set_index(["CR", "hemisphere"])
    idx = a.index.union(lg.index)
    crt = pd.DataFrame({
        "level": "CR",
        "CR": [i[0] for i in idx], "hemisphere": [i[1] for i in idx],
        "s_bl_v84": a.reindex(idx)["sum_s_bl_mxcm"].to_numpy(),
        "s_bl_legacy": lg.reindex(idx)["sum_s_bl_mxcm"].to_numpy(),
        "n_v84": a.reindex(idx)["n_regions"].to_numpy(),
        "n_legacy": lg.reindex(idx)["n_regions"].to_numpy(),
    })
    return pd.concat([reg, crt], ignore_index=True)


def wrap(x):
    return (x + 180.0) % 360.0 - 180.0


def checks(cat, sel):
    rows = []

    def add(name, value, note=""):
        rows.append({"check": name, "value": value, "note": note})

    # 1. legacy sul caso di prova di Paolo
    test = ROOT / "data/sharp/test_20240508"
    if test.exists():
        res = {}
        for f in sorted(test.glob("*.Br.fits")):
            br, h = geo.read_sharp(f)
            bm, _ = geo.read_sharp(Path(str(f).replace(".Br.", ".bitmap.")))
            res[int(h["HARPNUM"])] = measure.measure_legacy(br, bm, h)
        anti = sorted(k for k, r in res.items() if r["hale_sign"] == -1 and r["valid_bl"])
        invalid = sorted(k for k, r in res.items() if not r["valid_bl"])
        t11152 = res.get(11152, {}).get("tilt_reduced_deg", np.nan)
        ok = anti == [11150, 11152, 11192] and invalid == [11182, 11186, 11187, 11189] and abs(t11152 - 74.9) <= 0.1
        add("1_legacy_reproduces_test_case", int(ok), f"anti_hale={anti} invalid={invalid} tilt_11152={t11152:.2f}")
    else:
        add("1_legacy_reproduces_test_case", 0, "caso di prova non presente: controllo NON eseguito")
    # 2. test sintetici
    try:
        import pytest  # noqa: F401
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--color=no", "-p", "no:cacheprovider",
                            str(ROOT / "tests")], capture_output=True, text=True)
        add("2_synthetic_tests_pass", int(r.returncode == 0), r.stdout.strip().splitlines()[-1] if r.stdout else "")
    except ImportError:  # test non eseguiti: il controllo obbligatorio non e' superato
        add("2_synthetic_tests_pass", 0, "pytest non disponibile: test NON eseguiti")
    # 3. centroidi contro JSOC (LAT/LON_FWTPOS/NEG, longitudini di Stonyhurst)
    v = cat[cat["valid_bl"] == 1]
    crln = pd.to_numeric(v["key_CRLN_OBS"], errors="coerce")
    for pol in ("pos", "neg"):
        dlat = (v[f"lat_{pol}"] - pd.to_numeric(v[f"key_LAT_FWT{pol.upper()}"], errors="coerce")).abs()
        dlon = wrap(v[f"lon_{pol}"] - crln - pd.to_numeric(v[f"key_LON_FWT{pol.upper()}"], errors="coerce")).abs()
        for nm, d in (("lat", dlat), ("lon", dlon)):
            add(f"3_abs_d{nm}_{pol}_vs_jsoc_median_deg", float(d.median()))
            add(f"3_abs_d{nm}_{pol}_vs_jsoc_p95_deg", float(d.quantile(0.95)))
    # 4. Phi / USFLUX
    ratio = v["phi_mx"] / pd.to_numeric(v["key_USFLUX"], errors="coerce")
    add("4_phi_over_usflux_median", float(ratio.median()))
    add("4_phi_over_usflux_p16", float(ratio.quantile(0.16)))
    add("4_phi_over_usflux_p84", float(ratio.quantile(0.84)))
    # 5. frazioni e stati del ciclo
    prim = cat[cat["role"] != "control"]
    add("5_harp_with_primary", int(len(prim)))
    add("5_harp_without_primary", int(len(pd.read_csv(OUT / "P1_NO_CM_RECORD.csv"))))
    add("5_fraction_valid_bl_primary", float(prim["valid_bl"].mean()))
    for s, n in prim["cycle_state"].value_counts().items():
        add(f"5_cycle_state_{s}", int(n))
    # P1b §3
    q = prim[prim["qual_0x80"] == 1]
    month = q["T_REC"].str[:7]
    add("P1b_records_0x80_primary", int(len(q)))
    add("P1b_records_0x80_outside_2016-04_2017-03", int(((month < "2016.04") | (month > "2017.03")).sum()))
    for m, n in month.value_counts().sort_index().items():
        add(f"P1b_0x80_month_{m}", int(n))
    vq = cat[cat["valid_bl"] == 1]
    for flag in (0, 1):
        g = vq[vq["qual_0x80"] == flag]
        add(f"P1b_phi_over_usflux_median_qual0x80={flag}",
            float((g["phi_mx"] / pd.to_numeric(g["key_USFLUX"], errors="coerce")).median()))
        add(f"P1b_abs_tilt_reduced_median_qual0x80={flag}", float(g["tilt_reduced_deg"].abs().median()))
    # P1d §4: ricomparse
    add("P1d_recurrences", int((prim["family_rank"] > 0).sum()))
    add("P1d_families_with_recurrence", int(prim.loc[prim["family_rank"] > 0, "family_id"].nunique()))
    for r, n in prim["family_rank"].value_counts().sort_index().items():
        add(f"P1d_family_rank_{int(r)}", int(n))
    a = prim[prim["valid_bl"] == 1].copy()
    a["year"] = a["T_REC"].str[:4]
    for y, g in a.groupby("year"):
        add(f"P1d_flux_fraction_recurrent_{y}", float(g.loc[g["family_rank"] > 0, "phi_mx"].sum() / g["phi_mx"].sum()))
    # P1d §3: evoluzione tra record primario e di controllo
    pr = cat[cat["role"] == "primary"].set_index("HARPNUM")
    co = cat[cat["role"] == "control"].set_index("HARPNUM")
    both = pr.join(co, lsuffix="_p", rsuffix="_c", how="inner")
    both = both[(both["valid_bl_p"] == 1) & (both["valid_bl_c"] == 1)]
    if len(both):
        dtilt = ((both["tilt_reduced_deg_c"] - both["tilt_reduced_deg_p"] + 90) % 180) - 90
        ratio = both["s_bl_c"] / both["s_bl_p"]
        dstar_p = both["cycle_p"].map({24: 1, 25: -1}) * both["d_axial_bal_g_p"]
        dstar_c = both["cycle_c"].map({24: 1, 25: -1}) * both["d_axial_bal_g_c"]
        tp = pd.to_datetime(both["T_REC_p"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
        tc = pd.to_datetime(both["T_REC_c"].str.replace("_TAI", ""), format="%Y.%m.%d_%H:%M:%S")
        dt = (tc - tp).abs().dt.total_seconds() / 86400
        add("P1d_evolution_n", int(len(both)))
        for nm, x in (("dtilt_deg", dtilt), ("s_bl_ratio_control_over_primary", ratio), ("abs_dt_days", dt)):
            for q in (16, 50, 84):
                add(f"P1d_evolution_{nm}_p{q}", float(np.nanpercentile(x, q)))
        add("P1d_evolution_same_sign_dstar", float((np.sign(dstar_p) == np.sign(dstar_c)).mean()))
        add("P1d_evolution_same_hale_sign", float((both["hale_sign_p"] == both["hale_sign_c"]).mean()))
    # P1c §3
    tab = pd.read_csv(OUT / "CYCLE_BOUNDARY_FITS.csv")
    add("P1c_groups_latitude", int((tab["state"] == "LATITUDE").sum()))
    add("P1c_groups_changed_from_P1", int((tab["state"] != tab["state_p1"]).sum()))
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--allow-missing", action="store_true")
    args = ap.parse_args()

    sel = pd.read_csv(OUT / "P1_RECORD_SELECTION.csv")
    have = sel.apply(lambda r: complete(FITS, int(r["HARPNUM"]), r["T_REC"]), axis=1)
    if not have.all() and not args.allow_missing:
        print(f"record mancanti {int((~have).sum())}: download non completo (usare --allow-missing per provare)")
        return 1
    sel = sel[have].reset_index(drop=True)
    print(f"record da misurare {len(sel)}", flush=True)

    st = stamp(("P1", "P1b", "P1c", "P1d"))
    st["complete_series"] = int(not args.allow_missing or bool(have.all()))
    cat = build_catalog(sel, args.workers)
    agg = aggregate(cat)
    cmp_ = legacy_vs_v84(cat, agg)
    chk = checks(cat, sel)
    # controlli obbligatori (esito si'/no); gli altri di P1 §8 sono descrittivi
    mand = chk[chk["check"].isin(MANDATORY_CHECKS)]
    chk["mandatory"] = chk["check"].isin(MANDATORY_CHECKS).astype(int)
    st["validation_passed"] = int(len(mand) == len(MANDATORY_CHECKS) and (mand["value"] == 1).all())
    cat.assign(**st).to_csv(OUT / "P1_SBL_CATALOG_BY_HARP.csv", index=False)
    agg.assign(**st).to_csv(OUT / "P1_SBL_BY_CR_HEMISPHERE.csv", index=False)
    cmp_.assign(**st).to_csv(OUT / "P1_LEGACY_VS_V84.csv", index=False)
    chk.assign(**st).to_csv(OUT / "P1_CHECKS.csv", index=False)
    print(chk[["check", "value", "mandatory", "note"]].to_string(index=False))
    print(f"complete_series={st['complete_series']} validation_passed={st['validation_passed']}")
    if not st["validation_passed"]:
        print("CONTROLLI OBBLIGATORI FALLITI: la serie non e' validata e P2 non si esegue")
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
