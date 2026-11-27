"""BQ-HMI: export thinned draws of the S-ID sizing pilot (real T3 design, synthetic response) in the prototype format
BQ_SYNTHETIC_L1_POINTWISE_V1 and run Codex's independent dense recount on each bundle (MWO repository, separate
process). Development check of the production core at the full design size; no new draw.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_export_pilot_bundle.py --pilot reviews/BQ_SIZING_PILOT_20261127 \
        --out reviews/BQ_PILOT_BUNDLES_20261127 [--per-chain 5]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_export as E  # noqa: E402
import bq_sizing_pilot as SP  # noqa: E402

VERIFIER = Path("/home/gianluca/MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/BQ_DENSE_RECOUNT_20261127")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-chain", type=int, default=5)
    ap.add_argument("--cases", default="G1:0:0,G1:0:1", help="gen:rep:fit index list")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    meta = json.loads((Path(a.pilot) / "META.json").read_text())
    warm = int(meta["warm"])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    results = []
    for case in a.cases.split(","):
        gname, r, f = case.split(":")
        g, r, f = SP.GENS.index(gname), int(r), int(f)
        name, with_v, sv = SP.FITS[f]
        zs = [np.load(Path(a.pilot) / "CHAINS" / f"{gname}_r{r}_{name}_c{c}.npz") for c in range(4)]
        n = min(len(z["draws"]) for z in zs)
        thin = max(1, n // a.per_chain)
        chains = {f"c{c}": z["draws"][thin - 1:thin * a.per_chain:thin] for c, z in enumerate(zs)}
        D = SP.IP.design_arrays()
        y = SP.response(D, g, r)
        d = SP.make_design(D, with_v, sv)
        b = out / f"{gname}_r{r}_{name}"
        E.export_l1_bundle(b, d, y, np.arange(d.n), chains, warm, thin, head,
                           {"python/sharpbl/bq_core.py": ROOT / "python/sharpbl/bq_core.py", "python/sharpbl/bq_export.py": ROOT / "python/sharpbl/bq_export.py",
                            "scripts/bq_sizing_pilot.py": ROOT / "scripts/bq_sizing_pilot.py"},
                           dict(name=f"sizing pilot {gname} replicate {r}", seed=int(SP.SEED0 + 1000 * g + 100 * r + 99)))
        res = subprocess.run([sys.executable, "bundle_recount.py", "--bundle", str(b.resolve())], cwd=VERIFIER, capture_output=True, text=True)
        try:
            rj = json.loads(res.stdout)
        except ValueError:
            rj = dict(passed=False, reason=res.stderr[-400:])
        rj["case"] = case
        results.append(rj)
        print(case, rj.get("passed"), rj.get("maximum_absolute_errors", rj.get("reason")), flush=True)
    (out / "RECOUNT_RESULTS.json").write_text(json.dumps(results, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
