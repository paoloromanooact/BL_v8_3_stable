"""Check a weekend output against the planned job and recompute its score."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path.cwd() / "python"))
from sharpbl import bq_diag

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("run", type=Path)
parser.add_argument("--probe", action="store_true", help="allow pilot jobs outside the weekend manifesto")
args = parser.parse_args()
meta = json.loads((args.run / "META.json").read_text())
if meta["status"] != "completed":
    print(json.dumps({"directory": str(args.run), "status": meta["status"]}))
    sys.exit(0)

run = meta["args"]
manifest = Path(__file__).with_name("JOBS.csv")
criteria = {
    "block_id": str(run.get("block_id")),
    "model": run.get("model"),
    "v": run.get("v"),
    "generator": run.get("response"),
    "response_rep": str(run.get("response_rep")),
    "likelihood": run["kind"],
}
if not args.probe:
    with manifest.open() as f:
        matched = [r for r in csv.DictReader(f) if all(r[k] == v for k, v in criteria.items())]
    if len(matched) != 1:
        raise SystemExit(f"run outside the manifesto: {criteria}")
    expected = matched[0]
    if (meta["records"], meta["training_records"], meta["response_seed"]) != (
        int(expected["n_verify"]), int(expected["n_train"]), int(expected["response_seed"])
    ):
        raise SystemExit("record counts or response seed differ from the manifesto")
    if meta.get("sources_unchanged") is not True:
        raise SystemExit("run sources changed")

with (args.run / "DRAWS.csv").open() as f:
    rows = list(csv.DictReader(f))
if not rows or len(rows) != meta.get("draws_scored", len(rows)):
    raise SystemExit("inconsistent number of scored draws")
draw_keys = [(int(r["chain"]), int(r["iteration"])) for r in rows]
if len(draw_keys) != len(set(draw_keys)):
    raise SystemExit("duplicate chain/iteration")
chains = sorted({c for c, _ in draw_keys})
counts = [sum(c == k for c, _ in draw_keys) for k in chains]
if chains != list(range(run["chains"])) or len(set(counts)) != 1:
    raise SystemExit("unbalanced score contributions")

def log_mean_exp(numbers):
    peak = max(numbers)
    return peak + math.log(math.fsum(math.exp(x - peak) for x in numbers) / len(numbers))


terms = [float(r["log_density"]) for r in rows]
for r, logged in zip(rows, terms):
    values = json.loads(r["log_density_all"])
    main = int(r["n_main"])
    if main < 1 or len(values) != main + int(r["n_extra"]):
        raise SystemExit("invalid SMC replicate counts")
    if not math.isclose(log_mean_exp(values[:main]), logged, rel_tol=0, abs_tol=1e-10):
        raise SystemExit("score contribution differs from the main SMC replicates")
if not all(map(math.isfinite, terms)):
    raise SystemExit("non-finite score contribution")
m = max(terms)
w = [math.exp(x - m) for x in terms]
score = m + math.log(math.fsum(w) / len(w))
ess = math.fsum(w) ** 2 / math.fsum(x * x for x in w)
def batch_mcse(weights, keys):
    by_chain = {}
    for (chain, iteration), weight in zip(keys, weights):
        by_chain.setdefault(chain, []).append((iteration, weight))
    centered = []
    mean = math.fsum(weights) / len(weights)
    for keyed in by_chain.values():
        ordered = [value for _, value in sorted(keyed)]
        n_batches = min(10, len(ordered) // 2)
        if n_batches < 2:
            return math.nan
        width, extra = divmod(len(ordered), n_batches)
        offset = 0
        for index in range(n_batches):
            size = width + (index < extra)
            batch_sum = math.fsum(ordered[offset:offset + size])
            centered.append((batch_sum - size * mean) / len(weights))
            offset += size
    n = len(centered)
    return math.sqrt(n / (n - 1) * math.fsum(x * x for x in centered)) / mean


mcse = batch_mcse(w, draw_keys)
with (args.run / "CHECKPOINTS.csv").open() as f:
    last = list(csv.DictReader(f))[-1]
if not (int(last["draws"]) == len(rows)
        and math.isclose(score, float(last["score"]), rel_tol=0, abs_tol=1e-10)
        and math.isclose(ess, float(last["ess_weights"]), rel_tol=0, abs_tol=1e-9)):
    raise SystemExit("score checkpoint disagrees with the draws")
logged_mcse = float(last["mcse"] or "nan")
same_mcse = (math.isnan(mcse) and math.isnan(logged_mcse)) or math.isclose(mcse, logged_mcse, rel_tol=0, abs_tol=1e-10)
if not same_mcse:
    raise SystemExit("MCSE checkpoint disagrees with the draws")

with np.load(args.run / "TRAINING.npz") as fit:
    saved = set(zip(fit["chain"], fit["iteration"]))
    if not set(draw_keys) <= saved:
        raise SystemExit("a scored draw is absent from the saved training draws")
    psi = [fit["psi"][fit["chain"] == c] for c in chains]
    diagnostic = [bq_diag.diagnose(np.stack(psi)[:, :, p]) for p in range(psi[0].shape[1])]

print(json.dumps({
    "job": criteria, "draws": len(rows), "log_score": score, "weight_ess": ess, "mcse": mcse if math.isfinite(mcse) else None,
    "driver_status": meta["score_status"],
    "psi_coordinates_pass": sum(d["passes"] for d in diagnostic),
    "psi_coordinates_total": len(diagnostic),
    "tested_on_thinned_training_draws": run["thin"] > 1,
}))
