"""Schede anonime per il controllo morfologico HMI (docs/PROTOCOL_HMI_MORPHOLOGY.md, congelato in 21dfe6d, con A1 in 67f5e1a).

Genera, dagli stessi FITS e record del controllo dominanti, per 11 schede di riferimento (25S) e per le 90 HARP dei
gruppi 24N, 24S, 25N:
- `map_<codice>.png`: due viste fisse di Br (±1500 G e ±300 G) con il contorno della maschera P1 (bitmap ≥ 33);
- `cen_<codice>.png`: la stessa immagine con i soli marker dei centroidi di polarità (pesi |Br|, come P1).
Nessun numero di esito, flag, NOAA, data, gruppo o HARPNUM nelle immagini: solo il codice e il nome della vista.
La corrispondenza codice–HARPNUM è scritta in `CODE_MAP.csv` e non viene stampata.

    nice -n 10 .venv/bin/python python/sharpbl/morphology_sheets.py          # generazione (una volta)
    .venv/bin/python python/sharpbl/morphology_sheets.py --check              # verifiche automatiche
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import dominant_harp_check as DH, geometry as geo, measure  # noqa: E402
from sharpbl.download_records import file_stem, record_dir  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

PROTOCOL = ROOT / "docs/PROTOCOL_HMI_MORPHOLOGY.md"
AMEND = ROOT / "docs/PROTOCOL_HMI_MORPHOLOGY_A1.md"
SEL = ROOT / "results/DOMINANT/DOMINANT_HARP_SELECTION.csv"
OUT = ROOT / "results/MORPHOLOGY"
FIG = ROOT / "figures/MORPHOLOGY"
REFERENCES = {8950: "A", 9559: "A", 8206: "A", 7821: "A", 12623: "A",
              11786: "B", 11513: "B", 12094: "B", 11930: "B", 11248: "D (quasi unipolare)", 13169: "D (frammentata)"}
NEW_GROUPS = ("24N", "24S", "25N")
SEED_CODES, SEED_SUBSET, SEED_ORDER2 = 2026111301, 2026111302, 2026111303
VIEWS = ((1500.0, "vista ±1500 G"), (300.0, "vista ±300 G"))
FIG_W_IN, DPI = 14.0, 110          # risoluzione di uscita fissata qui (emendamento A1, punto 1)


def plan():
    sel = pd.read_csv(SEL).sort_values(["HARPNUM", "T_REC"]).reset_index(drop=True)
    ref = sel[sel["HARPNUM"].isin(REFERENCES)].sort_values("HARPNUM").reset_index(drop=True)
    assert len(ref) == 11 and set(ref["group"]) == {"25S"}
    ref = ref.assign(code=[f"R{i + 1:02d}" for i in range(11)], role="riferimento",
                     historical_class=[REFERENCES[h] for h in ref["HARPNUM"]])
    new = sel[sel["group"].isin(NEW_GROUPS)].sort_values(["HARPNUM", "T_REC"]).reset_index(drop=True)
    assert len(new) == 90
    perm = np.random.default_rng(SEED_CODES).permutation(len(new))
    new = new.iloc[perm].reset_index(drop=True).assign(code=[f"M{i + 1:03d}" for i in range(90)], role="nuova",
                                                       historical_class="")
    # seconda lettura: 10 per gruppo nuovo (7 dominanti, 3 controlli), senza reimmissione, ordine 24N, 24S, 25N
    rng = np.random.default_rng(SEED_SUBSET)
    sub = []
    for g in NEW_GROUPS:
        for kind, n in (("dominante", 7), ("controllo", 3)):
            pool = new[(new["group"] == g) & (new["kind"] == kind)].sort_values(["HARPNUM", "T_REC"])
            sub += list(pool.iloc[np.sort(rng.choice(len(pool), size=n, replace=False))]["code"])
    order2 = np.random.default_rng(SEED_ORDER2).permutation(len(sub))
    sub = [sub[i] for i in order2]
    return ref, new, sub


def centroid_pixels(br, bm, header):
    cb = DH.centroids_tilt(br, bm, header, 100.0, 33, uniform=False)
    if not cb.get("possible"):
        return None
    lon, lat = geo.lonlat_maps(header, br.shape)

    def pix(lo, la):
        dlon = (lon - lo + 180.0) % 360.0 - 180.0
        j = np.unravel_index(np.nanargmin(dlon ** 2 + (lat - la) ** 2), br.shape)
        return j[1], j[0]
    return pix(cb["lon_pos"], cb["lat_pos"]), pix(cb["lon_neg"], cb["lat_neg"])


def render(br, mask, code, path, markers=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h, w = br.shape
    fig, axes = plt.subplots(1, 2, figsize=(FIG_W_IN, FIG_W_IN / 2 * h / w + 0.6))
    for ax, (vmax, label) in zip(axes, VIEWS):
        ax.imshow(br, cmap="gray", vmin=-vmax, vmax=vmax, origin="lower", interpolation="nearest")
        ax.contour(mask.astype(int), levels=[0.5], colors="yellow", linewidths=0.7)
        if markers is not None:
            (xp, yp), (xn, yn) = markers
            ax.plot(xp, yp, "o", ms=7, mfc="none", mec="red", mew=1.6)
            ax.plot(xn, yn, "s", ms=7, mfc="none", mec="red", mew=1.6)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(label, fontsize=9)
    fig.suptitle(code, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, metadata={"Software": None})
    plt.close(fig)


def generate():
    if (OUT / "CODE_MAP.csv").exists():
        print("schede già generate: non si rigenera")
        return 2
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    ref, new, sub = plan()
    rows = []
    for _, r in pd.concat([ref, new]).iterrows():
        harp, t_rec = int(r["HARPNUM"]), r["T_REC"]
        folder, stem = record_dir(DH.FITS, t_rec), file_stem(harp, t_rec)
        fb, fm = folder / f"{stem}.Br.fits", folder / f"{stem}.bitmap.fits"
        br, hdr = geo.read_sharp(fb)
        bm, _ = geo.read_sharp(fm)
        assert str(hdr.get("T_REC")) == t_rec, f"record diverso per {r['code']}"
        mask = measure.base_mask(br, bm, 33, measure.MAX_ABS_BR_G)
        mk = centroid_pixels(br, bm, hdr)
        pm, pc = FIG / f"map_{r['code']}.png", FIG / f"cen_{r['code']}.png"
        render(br, mask, r["code"], pm)
        render(br, mask, r["code"], pc, markers=mk)
        rows.append(dict(code=r["code"], role=r["role"], HARPNUM=harp, T_REC=t_rec, group=r["group"], kind=r["kind"],
                         historical_class=r["historical_class"], centroids_possible=int(mk is not None),
                         sha256_Br=hashlib.sha256(fb.read_bytes()).hexdigest(), sha256_bitmap=hashlib.sha256(fm.read_bytes()).hexdigest(),
                         sha256_map_png=hashlib.sha256(pm.read_bytes()).hexdigest(), sha256_cen_png=hashlib.sha256(pc.read_bytes()).hexdigest()))
    st = stamp(("P1", "P1b", "P1c", "P1d", "P1e"))
    st["sha256_PROTOCOL_HMI_MORPHOLOGY"] = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    st["sha256_PROTOCOL_HMI_MORPHOLOGY_A1"] = hashlib.sha256(AMEND.read_bytes()).hexdigest()
    pd.DataFrame(rows).assign(**st).to_csv(OUT / "CODE_MAP.csv", index=False)          # non stampato
    # file per i lettori: solo codici, nessun HARPNUM
    pd.DataFrame(dict(code=ref["code"], historical_class=ref["historical_class"])).to_csv(OUT / "REFERENCE_SHEETS.csv", index=False)
    pd.DataFrame(dict(order=range(1, 91), code=new["code"])).to_csv(OUT / "READING_ORDER_READER1.csv", index=False)
    pd.DataFrame(dict(order=range(1, len(sub) + 1), code=sub)).to_csv(OUT / "READING_ORDER_READER2.csv", index=False)
    (OUT / "SHEETS_META.json").write_text(json.dumps(dict(fig_width_in=FIG_W_IN, dpi=DPI, views=[v[1] for v in VIEWS],
                                                          seeds=dict(codes=SEED_CODES, subset=SEED_SUBSET, order2=SEED_ORDER2),
                                                          n_reference=11, n_new=90, n_reader2=len(sub), **st), indent=2))
    print(f"generate {len(rows)} schede ({len(rows) * 2} immagini); corrispondenza in {OUT / 'CODE_MAP.csv'} (non stampata)")
    return 0


def check():
    """Verifiche automatiche senza guardare le immagini: conteggi, record, hash, assenza di testo extra e di metadati."""
    from PIL import Image
    cm = pd.read_csv(OUT / "CODE_MAP.csv")
    rows = []

    def add(name, value, ok):
        rows.append(dict(check=name, value=value, passed=bool(ok)))
    add("counts_11_ref_90_new", f"{(cm.role == 'riferimento').sum()}/{(cm.role == 'nuova').sum()}",
        (cm.role == "riferimento").sum() == 11 and (cm.role == "nuova").sum() == 90)
    sel = pd.read_csv(SEL)
    j = cm.merge(sel[["HARPNUM", "T_REC", "group", "kind"]], on=["HARPNUM", "T_REC"], suffixes=("", "_sel"))
    add("records_equal_selection", len(j), len(j) == 101 and (j["group"] == j["group_sel"]).all())
    add("new_cover_three_groups_30_each", cm[cm.role == "nuova"].groupby("group").size().to_dict(),
        cm[cm.role == "nuova"].groupby("group").size().to_dict() == {"24N": 30, "24S": 30, "25N": 30})
    bad_hash, bad_meta, sizes = 0, 0, set()
    for _, r in cm.iterrows():
        for col, pre in (("sha256_map_png", "map_"), ("sha256_cen_png", "cen_")):
            p = FIG / f"{pre}{r['code']}.png"
            bad_hash += int(hashlib.sha256(p.read_bytes()).hexdigest() != r[col])
            im = Image.open(p)
            bad_meta += int(any(k for k in im.info if k not in ("dpi",)))
            sizes.add(im.size[0])
    add("png_hashes_match", bad_hash, bad_hash == 0)
    add("png_no_text_metadata", bad_meta, bad_meta == 0)
    add("png_width_fixed", sorted(sizes), len(sizes) == 1)
    r2 = pd.read_csv(OUT / "READING_ORDER_READER2.csv").merge(cm, on="code")
    add("reader2_subset_7_3_per_group", r2.groupby(["group", "kind"]).size().to_dict(),
        r2.groupby(["group", "kind"]).size().to_dict() == {(g, k): n for g in NEW_GROUPS for k, n in (("controllo", 3), ("dominante", 7))})
    add("reader_files_without_harpnum", "", all("HARPNUM" not in pd.read_csv(OUT / f).columns
                                                 for f in ("REFERENCE_SHEETS.csv", "READING_ORDER_READER1.csv", "READING_ORDER_READER2.csv")))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "SHEETS_CHECKS.csv", index=False)
    print(res.to_string(index=False))
    return 0 if res["passed"].all() else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(check() if a.check else generate())
