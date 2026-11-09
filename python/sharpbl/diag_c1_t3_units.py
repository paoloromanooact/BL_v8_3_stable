"""Denominatori per il controllo della trasformazione di T3: regioni nei disegni T3 per scenario.

Rigenera i cataloghi di sviluppo (semi 40000 + k) e conta le unita' del disegno T3 (stesso filtro
di p2d.design_t3). Post hoc, nessun verdetto. Tabella: results/DIAGNOSTIC/C1_T3_UNITS.csv.

    OMP_NUM_THREADS=1 .venv/bin/python python/sharpbl/diag_c1_t3_units.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sharpbl import p2d, run_p2  # noqa: E402
from sharpbl.provenance import ROOT, stamp  # noqa: E402

_S = None


def one(args):
    global _S
    sc, k = args
    if _S is None:
        _S = run_p2.load_silso()
    d = run_p2.add_activity(run_p2.samples(p2d.synthetic_catalog_p2d(sc, 40000 + k, 0.0, 0.0))["S"], _S)
    return dict(scenario=sc, k=k, n_units_T3=int(np.isfinite(d["A_monthly"]).sum()))


def main() -> int:
    from multiprocessing import Pool
    with Pool(12) as pool:
        r = pd.DataFrame(pool.map(one, [(sc, k) for sc in p2d.SCENARIOS for k in range(2000)], chunksize=16))
    t = pd.read_csv(ROOT / "results/DIAGNOSTIC/C1_T3_TRANSFORM_BY_CATALOGUE.csv.gz", usecols=["scenario", "k", "n_wrap"])
    r = r.merge(t, on=["scenario", "k"])
    s = r.groupby("scenario").agg(catalogues=("k", "size"), catalogues_with_wrap=("n_wrap", lambda x: int((x > 0).sum())),
                                  regions_T3=("n_units_T3", "sum"), regions_wrapped=("n_wrap", "sum")).reset_index()
    s.loc[len(s)] = ["V0-V6", s["catalogues"].sum(), s["catalogues_with_wrap"].sum(), s["regions_T3"].sum(),
                     s["regions_wrapped"].sum()]
    st = stamp(("P2", "P2d", "P2e"))
    st["status"] = "controllo post hoc, nessun verdetto"
    s.assign(**st).to_csv(ROOT / "results/DIAGNOSTIC/C1_T3_UNITS.csv", index=False)
    print(s.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
