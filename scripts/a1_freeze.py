"""Freeze of amendment A1 of the SFT map-bipole pilot (prepared 27 Nov 2026; NOT executed without the go-ahead).

Default: dry run, writes nothing. It checks the prepared final text (reviews/A1_FREEZE_PREP_20261127/) against the SHA
recorded in its README, the parent protocol and receipt against the pins of the runner, and prints the receipt that
would be written.
  --execute text     write docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md (refused if it exists); then commit it.
  --execute receipt  after that commit: write docs/PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1_FREEZE.json with sha256,
                     parent_sha256, parent_receipt_sha256, sft_core_sha256, freeze_commit (= HEAD, which must hold the
                     A1 text with the same SHA; tracked tree clean) and not_blind, ONLY if the runner's own A1 checks
                     pass on the receipt before it is written; otherwise stop with nothing written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
import sft_map_bipole_pilot as RN  # noqa: E402  (pins, paths and the gate's A1 checks)

PREP = ROOT / "reviews/A1_FREEZE_PREP_20261127"
TEXT = PREP / "PROTOCOL_SFT_MAP_BIPOLE_PILOT_AMENDMENT_A1.md"
NOT_BLIND = ("Non cieco rispetto alle prove sintetiche dell'upwind, del preflight e delle patch sintetiche del selftest "
             "(§0, §2bis): nessuna mappa osservata è stata letta per scrivere o decidere questo emendamento.")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


def prepared_sha():
    for line in (PREP / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("- Testo finale proposto:"):
            return line.rsplit("SHA ", 1)[1].strip()
    raise SystemExit("README without the prepared SHA")


def checks():
    probs = []
    if sha(TEXT) != prepared_sha():
        probs.append("prepared text differs from the SHA in its README")
    fz = json.loads(RN.FREEZE.read_text())
    if not (sha(RN.PROTOCOL) == fz.get("sha256") == RN.PIN["protocol"]):
        probs.append("parent protocol text and receipt differ from the pin")
    if sha(RN.FREEZE) != RN.PIN["receipt"]:
        probs.append("parent receipt file differs from the pin")
    return probs


def receipt(head):
    return dict(sha256=sha(TEXT), parent_sha256=RN.PIN["protocol"], parent_receipt_sha256=RN.PIN["receipt"],
                sft_core_sha256=sha(ROOT / "python/sharpbl/sft_core.py"), freeze_commit=head, not_blind=NOT_BLIND)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", choices=("text", "receipt"))
    a = ap.parse_args()
    probs = checks()
    if probs:
        sys.exit("refused: " + "; ".join(probs))
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    if a.execute is None:
        print("dry run: prepared text, parent protocol and receipt pins verified; nothing written")
        print("final text exists:", RN.A1.exists(), "| receipt exists:", RN.A1_FREEZE.exists())
        print(json.dumps(receipt("<commit that adds the final text>"), indent=2, ensure_ascii=False))
        return
    if a.execute == "text":
        if RN.A1.exists():
            sys.exit("refused: final A1 text exists")
        RN.A1.write_bytes(TEXT.read_bytes())
        print(f"written {RN.A1.relative_to(ROOT)} (SHA {sha(RN.A1)}); commit it, then run --execute receipt")
        return
    if RN.A1_FREEZE.exists():
        sys.exit("refused: receipt exists")
    if not RN.A1.exists() or sha(RN.A1) != sha(TEXT):
        sys.exit("refused: final A1 text missing or different from the prepared one")
    blob = git("show", f"HEAD:docs/{RN.A1.name}")
    if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != sha(TEXT):
        sys.exit("refused: HEAD does not hold the final A1 text (commit it first)")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        sys.exit("refused: tracked tree not clean")
    r = receipt(head)
    # validate BEFORE writing (Codex, 27 Nov): the runner's own A1 checks and the gate's text/parent/core conditions
    left = list(RN.a1_receipt_problems(r))
    if not (sha(RN.A1) == r["sha256"] and r["parent_sha256"] == RN.PIN["protocol"]
            and r["sft_core_sha256"] == sha(ROOT / "python/sharpbl/sft_core.py")):
        left.append("A1 text, parent or transport code")
    if left:
        sys.exit("refused, nothing written: " + "; ".join(left))
    RN.A1_FREEZE.write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
    print(f"written {RN.A1_FREEZE.relative_to(ROOT)} after the runner's A1 checks passed; commit the receipt")


if __name__ == "__main__":
    main()
