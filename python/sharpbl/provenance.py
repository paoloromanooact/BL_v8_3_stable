"""SHA-256 dei protocolli e commit git, da registrare negli output."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOLS = {
    "P1": "docs/PROTOCOL_P1_SBL_SERIES.md",
    "P1b": "docs/PROTOCOL_P1B_QUALITY_0x80.md",
    "P1c": "docs/PROTOCOL_P1C_CYCLE_RULE.md",
    "P1d": "docs/PROTOCOL_P1D_RECURRENCE_EVOLUTION.md",
    "P2b": "docs/PROTOCOL_P2B_TEMPORAL_DEPENDENCE.md",
    "P1e": "docs/PROTOCOL_P1E_CANDIDATE_RECURRENCES.md",
    "P2c": "docs/PROTOCOL_P2C_P2B_CLARIFICATIONS.md",
    "P3": "docs/PROTOCOL_P3_EXTERNAL_VALIDATION.md",
    "P3b": "docs/PROTOCOL_P3B_AXIAL_TILT_STATISTICS.md",
    "P3c": "docs/PROTOCOL_P3C_BARD_TILT_CONVENTION.md",
    "P2d": "docs/PROTOCOL_P2D_SIMULATION_CALIBRATED_TEST.md",
    "P2e": "docs/PROTOCOL_P2E_ATTENUATION_CORRECTION.md",
    "P2": "docs/PROTOCOL_P2_QUENCHING.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(names=("P1", "P1b", "P1c")) -> dict:
    out = {f"sha256_{n}": sha256(ROOT / PROTOCOLS[n]) for n in names}
    try:
        out["git_commit"] = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                           capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, check=True).stdout.strip()
        out["git_dirty"] = int(bool(dirty))
    except (OSError, subprocess.CalledProcessError):
        out["git_commit"], out["git_dirty"] = "unknown", -1
    return out
