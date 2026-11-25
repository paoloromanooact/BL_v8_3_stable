"""BQ-HMI preparation: design counts only (no response is read).

Frozen T3 design (p2f_pilot.build_design: 2485 regions, design columns only, asserts no response column) plus the P1e
family_id of each HARP. Counts for the cross review of docs/PROTOCOL_BQ_HMI_DRAFT.md:
- CR span (all integer CRs from first to last), cells CR x hemisphere, singleton cells;
- families in the sample: singletons and replicated ones (members in the sample), latent dimension for Woodbury
  (2 N_CR for u, + 2 N_CR with v, + replicated families; singleton families go on the diagonal);
- 10 contiguous CR blocks (lengths differ by at most one, remainder to the first blocks) with buffers 11 and 22:
  verification records, training records after buffer and removal of every family member of the verification,
  cycle x hemisphere support and activity range of the training.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_design_counts.py --out reviews/BQ_DESIGN_COUNTS_20261125
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import p2f_pilot as P  # noqa: E402

CATALOGUE = ROOT / "results/P1/P1_SBL_CATALOG_BY_HARP.csv"
N_BLOCKS, BUFFERS = 10, (11, 22)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def blocks(cr_min, cr_max, k=N_BLOCKS):
    n = cr_max - cr_min + 1
    base, rem = divmod(n, k)
    out, lo = [], cr_min
    for i in range(k):
        ln = base + (1 if i < rem else 0)
        out.append((lo, lo + ln - 1))
        lo += ln
    return out


def counts():
    d = P.build_design()
    fam = pd.read_csv(CATALOGUE, usecols=["HARPNUM", "family_id"], low_memory=False).drop_duplicates()
    if fam.HARPNUM.duplicated().any():
        raise SystemExit("family_id not unique per HARP")
    d = d.merge(fam, on="HARPNUM", how="left", validate="one_to_one")
    if d.family_id.isna().any():
        raise SystemExit("HARP without family_id")
    d["CR"] = d.CR.astype(int)
    cr0, cr1 = int(d.CR.min()), int(d.CR.max())
    n_cr = cr1 - cr0 + 1
    cells = d.groupby(["CR", "hemisphere"]).size()
    fsize = d.groupby("family_id").size()
    rep = fsize[fsize >= 2]
    out = dict(records=len(d), harps=int(d.HARPNUM.nunique()), cr_first=cr0, cr_last=cr1, n_cr_span=n_cr,
               cr_with_records=int(d.CR.nunique()), cells=int(len(cells)), singleton_cells=int((cells == 1).sum()),
               families=int(len(fsize)), singleton_families=int((fsize == 1).sum()), replicated_families=int(len(rep)),
               records_in_replicated_families=int(rep.sum()), max_family_size=int(fsize.max()),
               latent_dim_u=2 * n_cr + int(len(rep)), latent_dim_u_v=4 * n_cr + int(len(rep)),
               records_by_cycle_hemisphere={f"{c}{h}": int(n) for (c, h), n in d.groupby(["cyc", "hemisphere"]).size().items()},
               catalogue_sha256=sha(CATALOGUE), script_sha256=sha(__file__))
    rows = []
    for buf in BUFFERS:
        for i, (lo, hi) in enumerate(blocks(cr0, cr1)):
            ver = (d.CR >= lo) & (d.CR <= hi)
            fams = set(d.family_id[ver])
            train = ~ver & ~((d.CR >= lo - buf) & (d.CR <= hi + buf)) & ~d.family_id.isin(fams)
            t = d[train]
            sup = {f"{c}{h}": int(n) for (c, h), n in t.groupby(["cyc", "hemisphere"]).size().items()}
            rows.append(dict(buffer=buf, block=i, cr_lo=lo, cr_hi=hi, verification=int(ver.sum()),
                             training=int(train.sum()), removed_buffer=int((~ver & (d.CR >= lo - buf) & (d.CR <= hi + buf)).sum()),
                             removed_family_outside_buffer=int((~ver & ~((d.CR >= lo - buf) & (d.CR <= hi + buf)) & d.family_id.isin(fams)).sum()),
                             verification_cycles="/".join(sorted({f"{c}{h}" for c, h in zip(d.cyc[ver], d.hemisphere[ver])})),
                             **{f"train_{k}": sup.get(k, 0) for k in ("24N", "24S", "25N", "25S")},
                             train_act_min=float(t.A_monthly.min()), train_act_max=float(t.A_monthly.max()),
                             ver_act_min=float(d.A_monthly[ver].min()) if ver.any() else np.nan,
                             ver_act_max=float(d.A_monthly[ver].max()) if ver.any() else np.nan))
    return out, pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit("output exists")
    summary, table = counts()
    a.out.mkdir(parents=True)
    (a.out / "COUNTS.json").write_text(json.dumps(summary, indent=2) + "\n")
    table.to_csv(a.out / "CV_BLOCKS.csv", index=False)
    print(json.dumps(summary, indent=2))
    print(table.to_string(index=False))
