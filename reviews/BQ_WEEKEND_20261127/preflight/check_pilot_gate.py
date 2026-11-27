"""Allow a weekend likelihood to proceed only after both large-block pilots pass."""
import argparse
import csv
import json
import math
from pathlib import Path
import subprocess
import sys

cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument("kind", choices=("L2", "L3"))
cli.add_argument("m0", type=Path)
cli.add_argument("mq", type=Path)
args = cli.parse_args()
checker = Path(__file__).with_name("check_run.py")
problems = []

for model, directory in (("M0", args.m0), ("MQ", args.mq)):
    try:
        meta = json.loads((directory / "META.json").read_text())
        params = meta["args"]
        expected = ("G1", 0, args.kind, 8, model, "none")
        actual = tuple(params.get(k) for k in ("response", "response_rep", "kind", "block_id", "model", "v"))
        if actual != expected:
            raise ValueError(f"expected {expected}, got {actual}")
        if meta["status"] != "completed":
            raise ValueError(f"process status {meta['status']}")
        recount = subprocess.run([sys.executable, str(checker), str(directory)], capture_output=True, text=True)
        if recount.returncode:
            raise ValueError(recount.stderr.strip() or recount.stdout.strip() or "recount failed")
        quality = json.loads(recount.stdout)
        with (directory / "CHECKPOINTS.csv").open() as f:
            checkpoint = list(csv.DictReader(f))[-1]
        if quality["draws"] not in (120, 160, 200):
            problems.append(f"{model}: checkpoint {quality['draws']} outside the agreed gate")
        mcse = float(checkpoint["mcse"] or "nan")
        if not (quality["driver_status"] == "ok" and math.isfinite(mcse)
                and mcse <= 0.1 and quality["weight_ess"] >= 100):
            problems.append(f"{model}: predictive precision insufficient (MCSE {mcse}, ESS {quality['weight_ess']:.2f})")
        if quality["psi_coordinates_pass"] != quality["psi_coordinates_total"]:
            problems.append(f"{model}: {quality['psi_coordinates_pass']}/{quality['psi_coordinates_total']} training coordinates pass")
    except (OSError, ValueError, KeyError, IndexError) as error:
        problems.append(f"{model}: {error}")

print(json.dumps({"kind": args.kind, "ready": not problems, "problems": problems}, indent=2))
sys.exit(bool(problems))
