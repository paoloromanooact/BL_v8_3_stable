"""Descriptive outputs of §6 required before S1-S4 are read (Codex's second review, point 3), kept in a separate file
so that it can be written while the validation runs (the validation hashes scripts/t3_mwo_analysis.py at start and end).

To implement before the stability stage: DPD source next to the epochs of S1, S2 against P1 in 2010-2012, fraction of
groups excluded for non-isolation by activity tercile, d_WL of the 'all records' sensitivity for isolated and
non-isolated records. Until then the stability stage refuses to run.
"""
IMPLEMENTED = False


def extras(*args, **kwargs):
    raise NotImplementedError("descriptive outputs of §6 (S1 DPD sources, S2 vs P1, S4) not implemented yet")
