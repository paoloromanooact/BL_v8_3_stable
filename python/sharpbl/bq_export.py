"""BQ-HMI: export of saved L1 draws in Codex's prototype interchange format BQ_SYNTHETIC_L1_POINTWISE_V1 (synthetic only;
not the frozen format of a production run). The bundle lets the independent recount (Codex, reviews/
BQ_DENSE_RECOUNT_20261127/bundle_recount.py in the MWO repository) re-evaluate, with its own dense reference, the
log-likelihood, the log-prior, the conditional mean and covariance of the coefficients and log p(beta = 0 | psi, y) of
every saved draw.

Files: design.npz (record_id, t, h, s, a, lphi, cell, fam, y), chains.npz (psi, iteration, log_lik, log_prior,
coef_mean, coef_cov[, log_beta_zero]), run.json (exact fields), manifest.json (format and SHA-256 of the three).
Iteration convention: the saved draw k (0-based) of a chain is iteration warmup + thin (k + 1).
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from . import bq_core as B

FORMAT = "BQ_SYNTHETIC_L1_POINTWISE_V1"


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def export_l1_bundle(path, d: B.Design, y, record_id, chains, warmup, thin, source_commit, source_files, generator):
    """chains: dict chain_id -> array (n_saved, dim) of psi draws (same n_saved for every chain), already thinned with
    `thin` from a saved phase that starts after `warmup`. source_files: dict repo-relative path -> Path. generator: dict
    with at least 'name'. The destination must not exist."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists")
    ids = list(chains)
    n_saved = {len(v) for v in chains.values()}
    if len(n_saved) != 1 or not ids:
        raise ValueError("every chain needs the same number of saved draws")
    n_saved = n_saved.pop()
    y = np.asarray(y, float)
    path.mkdir(parents=True)
    np.savez(path / "design.npz", record_id=np.asarray(record_id, np.int64), t=d.t.astype(np.int64), h=d.h.astype(np.int64), s=d.s.astype(float),
             a=d.a.astype(float), lphi=d.lphi.astype(float), cell=d.cell.astype(np.int64), fam=np.asarray(d.fam, np.int64), y=y)
    out = {k: [] for k in ("psi", "log_lik", "log_prior", "coef_mean", "coef_cov")}
    if d.with_beta:
        out["log_beta_zero"] = []
    for cid in ids:
        rows = {k: [] for k in out}
        for x in np.asarray(chains[cid], float):
            ll, m, c = B.loglik(d, x, y, return_post=True)
            rows["psi"].append(x)
            rows["log_lik"].append(ll)
            rows["log_prior"].append(B.log_prior(d, x))
            rows["coef_mean"].append(m)
            rows["coef_cov"].append(c)
            if d.with_beta:
                v = c[-1, -1]
                rows["log_beta_zero"].append(-0.5 * math.log(2 * math.pi * v) - 0.5 * m[-1] ** 2 / v)
        for k in out:
            out[k].append(rows[k])
    it = np.tile(warmup + thin * (np.arange(n_saved) + 1), (len(ids), 1)).astype(np.int64)
    np.savez(path / "chains.npz", iteration=it, **{k: np.asarray(v, float) for k, v in out.items()})
    meta = dict(synthetic=True, likelihood="L1", with_beta=bool(d.with_beta), with_v=bool(d.with_v), n_t=int(d.n_t), n_cell=int(d.n_cell),
                prior={k: float(v) for k, v in d.prior.items()}, parameter_names=d.names(), chain_ids=[str(c) for c in ids], n_saved=int(n_saved),
                warmup=int(warmup), thin=int(thin), source_commit=str(source_commit),
                source_sha256={k: _sha_bytes(Path(p).read_bytes()) for k, p in source_files.items()}, generator=dict(generator))
    (path / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    files = ("design.npz", "chains.npz", "run.json")
    (path / "manifest.json").write_text(json.dumps(dict(format=FORMAT, sha256={f: _sha_bytes((path / f).read_bytes()) for f in files}), indent=2) + "\n")
    return meta
