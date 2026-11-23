"""POST-HOC DIAGNOSIS (not in the frozen protocol, changes no outcome): why S1 of stability R4 is 'non determinato'.

Replays the S1 block bootstrap (same seed, same blocks, same order of draws as s1() in t3_mwo_analysis.py) on the
subset rebuilt from DESIGN.csv and the preserved WL_TILTS.csv (SEALED.csv.gz is not read), checks that the singular
count equals the one in STABILITY.json, and records for each singular replicate the (epoch, hemisphere) cells
responsible: a cell whose two columns (sin|lat|, constant) are collinear after resampling, or a verifiable cell
missing from the replicate. Outputs results/T3_MWO_STABILITY_R4_S1_DIAGNOSIS/ (refuses to overwrite).

    .venv/bin/python scripts/t3_mwo_s1_singular_diagnosis.py
"""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STAB = ROOT / "results/T3_MWO_STABILITY_R4"
OUT = ROOT / "results/T3_MWO_STABILITY_R4_S1_DIAGNOSIS"


def cell_problems(sub, keys_needed):
    """Cells making the S1 design rank deficient, and needed cells that are absent."""
    bad = []
    for (e, h), g in sub.groupby(["epoch", "hemisphere"]):
        X = np.column_stack([g.sinlat.to_numpy(), np.ones(len(g))]) * np.sqrt(g.phi_mwo.to_numpy(float))[:, None]
        if np.linalg.matrix_rank(X) < 2:
            bad.append(f"{e}{h}:collinear(n={len(g)},distinct={g.noaa.nunique()})")
    present = set(zip(sub.epoch, sub.hemisphere))
    bad += [f"{e}{h}:absent" for e, h in keys_needed if (e, h) not in present]
    return bad


def main():
    if OUT.exists():
        sys.exit("refusing to overwrite")
    spec = importlib.util.spec_from_file_location("an", ROOT / "scripts/t3_mwo_analysis.py")
    an = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(an)
    d = an.load_design()
    wl = pd.read_csv(STAB / "WL_TILTS.csv", dtype={"noaa": str})
    assert (wl.noaa.to_numpy() == d.noaa.to_numpy()).all()
    d["d_wl"], d["wl_status"] = wl.d_wl.to_numpy(), wl.wl_status.to_numpy()
    sub = d[d.wl_status == "ok"].reset_index(drop=True)
    verif = an.epoch_verifiable(d)
    fit = an.s1_fit(sub)
    diff = an.s1_differences(fit, sub, verif)
    rng = np.random.default_rng(an.SEED_S1)
    blocks = {}
    for e in an.EPOCHS:
        se = sub[sub.epoch == e]
        if len(se):
            b = ((se.CR.astype(int) - int(se.CR.min())) // an.S1_BLOCK).to_numpy()
            blocks[e] = [se.index[b == j] for j in np.unique(b)]
    singular, causes, per_rep = 0, Counter(), []
    for r in range(an.S1_REPS):
        idx = np.concatenate([np.concatenate([bl[i] for i in rng.integers(0, len(bl), len(bl))]) for bl in blocks.values()])
        s = sub.loc[idx].reset_index(drop=True)
        f = an.s1_fit(s)
        if f is None or any(k not in f for k in diff):
            singular += 1
            bad = cell_problems(s, list(diff))
            per_rep.append(dict(rep=r, cells=";".join(bad)))
            causes.update(c.split(":")[0] + ":" + c.split(":")[1].split("(")[0] for c in bad)
    saved = json.loads((STAB / "STABILITY.json").read_text())["S1"]["singular"]
    cells = sub.groupby(["epoch", "hemisphere"]).agg(n=("noaa", "size"), n_blocks=("CR", lambda c: c.nunique()))
    cells["blocks_in_epoch"] = [len(blocks[e]) for e, _ in cells.index]
    cells["verifiable"] = [bool(verif.get(k)) for k in cells.index]
    OUT.mkdir(parents=True)
    pd.DataFrame(per_rep).to_csv(OUT / "SINGULAR_REPLICATES.csv", index=False)
    pd.Series(causes).rename_axis("cell_cause").reset_index(name="replicates").sort_values("replicates", ascending=False) \
        .to_csv(OUT / "SINGULAR_CAUSES.csv", index=False)
    cells.reset_index().rename(columns={"n_blocks": "n_distinct_CR"}).to_csv(OUT / "S1_CELLS.csv", index=False)
    meta = dict(post_hoc=True, changes_outcome=False, singular_replayed=singular, singular_saved=saved,
                replay_matches=singular == saved, stability_meta_sha256=hashlib.sha256((STAB / "META.json").read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), sealed_read=False)
    (OUT / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    print(pd.read_csv(OUT / "SINGULAR_CAUSES.csv").to_string(index=False))
    return 0 if singular == saved else 1


if __name__ == "__main__":
    sys.exit(main())
