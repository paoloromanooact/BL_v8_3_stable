"""BQ-HMI: sensitivity of the MC SE of the psi-averaged block score to the batch length (Codex, 27 Nov). Reads the
TERMS.csv of scripts/bq_psi_average_check.py (terms kept in chain order) and, per block, recomputes log mean exp(term)
and its MC SE by batch means WITHIN each chain on the rescaled densities exp(term - max), for several numbers of
batches per chain (hence batch lengths). No new draw.

    .venv/bin/python scripts/bq_psi_mcse_batches.py reviews/BQ_PSI_AVERAGE_20261127
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BATCHES = (2, 4, 5, 10, 20, 25)


def mcse(e, chain, nb):
    bm = []
    for c in np.unique(chain):
        ec = e[chain == c]
        size = len(ec) // nb
        if size < 1:
            return np.nan, 0
        bm += [ec[i * size:(i + 1) * size].mean() for i in range(nb)]
    return float(np.std(bm, ddof=1) / math.sqrt(len(bm)) / e.mean()), size


def main():
    d = Path(sys.argv[1])
    t = pd.read_csv(d / "TERMS.csv")
    rows = []
    for (blk, n), g in t.groupby(["block", "records"], sort=False):
        g = g.sort_values(["chain", "iteration"], kind="mergesort")
        v, ch = g.term.to_numpy(), g.chain.to_numpy()
        e = np.exp(v - v.max())
        est = v.max() + math.log(e.mean())
        iid = float(e.std(ddof=1) / math.sqrt(len(e)) / e.mean())
        for nb in BATCHES:
            se, size = mcse(e, ch, nb)
            rows.append(dict(block=blk, records=n, draws=len(v), score=est, batches_per_chain=nb, batch_length=size, mcse=se, mcse_iid=iid))
    out = pd.DataFrame(rows)
    out.to_csv(d / "MCSE_BY_BATCH_LENGTH.csv", index=False)
    print(out.pivot_table(index="records", columns="batch_length", values="mcse").to_string(float_format=lambda x: f"{x:.4f}"))
    print(out.groupby("records").mcse_iid.first().to_string(float_format=lambda x: f"{x:.4f}"))


if __name__ == "__main__":
    main()
