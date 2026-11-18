"""Download for the second MDI-HMI sample (frozen protocol bbd719c §3): A1 transport, every HTTP request counted
(availability included), at most 450 requests, 512 MiB, 32 MiB per file, two attempts per item, stop after three
consecutive failures of the same class, no overall time limit.

    .venv/bin/python scripts/mdi_hmi_second_sample_fetch.py
"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mdi_hmi_patch_download as dl  # noqa: E402
import mdi_hmi_patch_io as io  # noqa: E402

BASE = io.INVENTORY / "second_sample_bbd719c"
PROTOCOL = ROOT / "docs/PROTOCOL_MDI_HMI_SECOND_SAMPLE.md"
PROTOCOL_SHA = "b7860445ce4e83b5fb8933797f6f9024ee419cd9c941bcb6299e3711e98d4839"
REQUESTS_CAP = 450


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    io.use_sample(BASE, PROTOCOL, PROTOCOL_SHA, sha(BASE / "selection/PAIRS.csv"), sha(BASE / "availability/SEGMENTS.csv"))
    req = json.loads((BASE / "availability/REQUESTS.json").read_text())
    prior_n = len(req["requests"])
    prior_s = sum(r["seconds"] for r in req["requests"])
    prepared = dl.preflight_sample(prior_n, prior_s, REQUESTS_CAP)
    print(f"{len(prepared[0])} pairs; {len(prepared[1])} records; FITS estimate {prepared[-1]} bytes; prior requests {prior_n}")
    m = dl.run_sample(prepared, BASE / "patch_download", REQUESTS_CAP, 1e9)   # no overall time limit (finite for JSON)
    print(f"verified {len(m)} FITS")
    return 0 if len(m) == sum(map(len, prepared[1].values())) else 1


if __name__ == "__main__":
    sys.exit(main())
