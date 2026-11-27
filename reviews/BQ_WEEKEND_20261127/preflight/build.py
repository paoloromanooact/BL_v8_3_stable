"""Build the BQ synthetic weekend manifest without fitting a model."""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np

root = Path.cwd()
out = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "scripts"))
import bq_cv_psi_smc as probe
import bq_woodbury_benchmark as metadata

block_order = (5, 6, 3, 8, 0, 1, 2, 4, 7, 9)
buffer = 11
response_rep = 0
models = ("M0", "MQ")
likelihoods = ("L2", "L3")
generators = ("G0", "G1")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def csv_out(name, columns, rows):
    with (out / name).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


frame = metadata.design()
harps = frame.HARPNUM.to_numpy()
assert len(set(harps)) == len(harps)
pairs = {}
for generator, kind in itertools.product(generators, likelihoods):
    kwargs = dict(kind=kind, v="none", block_id=8, response=generator,
                  response_rep=response_rep, synthetic_design=False)
    first = probe.setup(SimpleNamespace(model="M0", **kwargs))
    second = probe.setup(SimpleNamespace(model="MQ", **kwargs))
    d0, block, tr0, ve0, y0 = first
    d1, block1, tr1, ve1, y1 = second
    assert not d0.with_beta and d1.with_beta and not (d0.with_v or d1.with_v)
    assert block == block1 and len(y0) == len(harps)
    assert all(np.array_equal(x, y) for x, y in ((tr0, tr1), (ve0, ve1), (y0, y1)))
    assert np.array_equal(d0.t, frame.CR.to_numpy() - frame.CR.min())
    pairs[generator, kind] = y0
for generator in generators:
    assert np.array_equal(pairs[generator, "L3"], probe.fold(pairs[generator, "L2"]))

jobs, membership = [], []
counts = []
seen = np.zeros(len(harps), dtype=int)
for i, bid in enumerate(block_order):
    lo, hi = probe.CV.cv_blocks(d0.n_t)[bid]
    tr, ve = probe.CV.cv_masks(d0, (lo, hi), buffer)
    good_families = set(d0.fam[ve])
    independent_train = np.array([
        (t < lo - buffer or t > hi + buffer) and fam not in good_families
        for t, fam in zip(d0.t, d0.fam)
    ])
    assert np.array_equal(tr, independent_train) and not np.any(tr & ve)
    seen += ve
    counts.append((bid, int(ve.sum())))
    mask_hash = sha(np.column_stack((tr, ve)).astype("uint8").tobytes())
    for pos, harp in enumerate(harps):
        membership.append((bid, int(harp), int(frame.CR.iloc[pos]), int(tr[pos]), int(ve[pos])))
    for generator, kind, model in itertools.product(generators, likelihoods, models):
        y = pairs[generator, kind]
        jobs.append((i+1, "initial" if i < 4 else "extension", bid, lo, hi, buffer,
                     int(tr.sum()), int(ve.sum()), generator, response_rep,
                     probe.SEED_RESP + 1000 * probe.GENS.index(generator), kind, model, "none",
                     mask_hash, sha(np.asarray(y, dtype="<f8").tobytes())))
assert np.all(seen == 1) and counts[:4] == [(5, 22), (6, 102), (3, 236), (8, 395)]
assert len(jobs) == 80 and sum(j[1] == "initial" for j in jobs) == 32
csv_out("JOBS.csv", ("block_order", "stage", "block_id", "calendar_index_min",
                    "calendar_index_max", "buffer_cr", "n_train", "n_verify",
                    "generator", "response_rep", "response_seed", "likelihood", "model", "v",
                    "mask_sha256", "response_sha256"), jobs)
csv_out("MASKS_BY_HARP.csv", ("block_id", "HARPNUM", "CR", "training", "verification"), membership)
sources = ("scripts/bq_cv_psi_smc.py", "python/sharpbl/bq_cv.py",
           "scripts/bq_identifiability_pilot.py", "scripts/bq_woodbury_benchmark.py")
meta = {"git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "inputs": "T3 metadata and generated G0/G1 responses",
        "sources_sha256": {f: sha((root / f).read_bytes()) for f in sources},
        "products_sha256": {f: sha((out / f).read_bytes()) for f in ("JOBS.csv", "MASKS_BY_HARP.csv")},
        "runs_started": 0}
(out / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
print(f"{len(jobs)} jobs listed, {len(membership)} mask rows, {len(harps)} distinct records")
print(counts)
