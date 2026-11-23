# S2 diagnosis R4 — attempt 1, refused by its own guard (no product written)

23 November 2026, from commit ed8f2f3. `--run` stopped at the frozen check "s2_fit on the rebuilt subset reproduces
STABILITY.json within 1e-9": beta identical, SE off by 1.7e-5 (kappa and sigma_x2 moved; the REML optimum of M is
flat in kappa).

Cause: the runner read WL_TILTS.csv and the release table with pandas' default (fast, not round-trip exact) float
parser, so d_WL differed from the in-memory values of the stability run by up to ~3e-14. Read with
float_precision="round_trip", s2_fit reproduces STABILITY.json exactly (all fields difference 0, deterministic).

Fix: round-trip parsing of those reads in runner and recount; rules, tolerances and the note are unchanged.
