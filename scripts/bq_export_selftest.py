"""Selftest of python/sharpbl/bq_export.py on synthetic designs only: bundles from short REAL slice chains (u and u+v)
are verified by Codex's independent reader (bundle_recount.py with its dense reference, MWO repository, run as a
separate process: declared external dependency), and a tampered bundle is refused.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/bq_export_selftest.py
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "scripts"))
from sharpbl import bq_core as B, bq_export as E  # noqa: E402
from bq_core_selftest import synth_design  # noqa: E402

VERIFIER = Path("/home/gianluca/MWO-HMI-MDI-Polar-Flux-Signed-Sunspots/reviews/BQ_DENSE_RECOUNT_20261127")
SEED = 36_400_991
res = []


def ok(name, cond, info=""):
    res.append(bool(cond))
    print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")


def verify(bundle):
    r = subprocess.run([sys.executable, "bundle_recount.py", "--bundle", str(bundle)], cwd=VERIFIER, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return dict(passed=False, reason=r.stderr[-300:])


def main():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        for with_v in (False, True):
            d = synth_design(np.random.default_rng(SEED), n_t=20, n=60, with_v=with_v)
            y = np.random.default_rng(SEED + 1).normal(0, 20, d.n)
            x0 = np.array([math.log(15), -0.3, math.log(3), 0.5, 0.2, math.log(3)] + ([math.log(3), 0.5, 0.1] if with_v else []))
            warm, keep, thin = 20, 40, 10
            chains = {}
            for c in range(2):
                dr, _, _, _ = B.slice_chain(lambda z: B.log_post(d, z, y), x0, warm, keep, np.random.default_rng(SEED + 10 + c))
                chains[f"c{c}"] = dr[thin - 1::thin]                    # iterations warm + thin, warm + 2 thin, ...
            bdir = Path(td) / f"bundle_v{int(with_v)}"
            E.export_l1_bundle(bdir, d, y, np.arange(d.n) + 1000, chains, warm, thin, head,
                               {"python/sharpbl/bq_core.py": ROOT / "python/sharpbl/bq_core.py", "python/sharpbl/bq_export.py": ROOT / "python/sharpbl/bq_export.py"},
                               dict(name="synth_design of bq_core_selftest, Gaussian response", seed=SEED))
            r = verify(bdir)
            ok(f"{'u+v' if with_v else 'u'}: bundle from real slice chains verified by the independent dense recount (Codex)",
               r.get("passed") is True and r.get("complete") is False,
               f"max abs errors {r.get('maximum_absolute_errors')}" if r.get("passed") else r.get("reason"))
        # tampered: one log-likelihood moved, manifest refreshed (a consistent but wrong product)
        z = dict(np.load(bdir / "chains.npz"))
        z["log_lik"] = z["log_lik"].copy()
        z["log_lik"][0, 0] += 1e-6
        np.savez(bdir / "chains.npz", **z)
        import hashlib
        m = json.loads((bdir / "manifest.json").read_text())
        m["sha256"]["chains.npz"] = hashlib.sha256((bdir / "chains.npz").read_bytes()).hexdigest()
        (bdir / "manifest.json").write_text(json.dumps(m, indent=2) + "\n")
        r = verify(bdir)
        ok("refused by the independent recount: one log-likelihood moved by 1e-6 (manifest refreshed)", r.get("passed") is False,
           r.get("reason", "")[:120])
        try:
            E.export_l1_bundle(bdir, d, y, np.arange(d.n), chains, warm, thin, head, {}, dict(name="x"))
            again = False
        except FileExistsError:
            again = True
        ok("existing destination refused", again)
    print(f"selftest: {sum(res)}/{len(res)}")
    return all(res)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
