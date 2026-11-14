"""External probe of the T5-D2 checker (cross review 2026-11-14), hand-built tables only.

Not part of the checker's registered selftest receipt: the checker code is unchanged.
Adds alterations not covered by the 77 registered tests and one group with an error row
whose expected values are computed by hand (comments below), not by recount_group.
Reads no T5-D2 output, uses no generator, RNG or fit. Prints results only.
"""
import copy
import hashlib
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "python"))
from sharpbl import t5_oracle_postcheck as C  # noqa: E402

base = C.fixture()
results = []


def failed(obj):
    return [x["check"] for x in C.audit_tables(*obj).checks if not x["passed"]]


def probe(name, i, mut, expect_reject=True):
    o = copy.deepcopy(base)
    mut(o[i])
    f = failed(o)
    results.append((name, bool(f) == expect_reject, f or "accepted"))


probe("baseline_fixture", 0, lambda x: None, expect_reject=False)
probe("summary_R_shift_1e-7_rel", 1, lambda x: x[0].update(R=float(x[0]["R"]) * (1 + 1e-7)))
probe("summary_R_shift_1e-11_rel_within_tolerance", 1, lambda x: x[0].update(R=float(x[0]["R"]) * (1 + 1e-11)), expect_reject=False)
probe("summary_quantile_sign_flip", 1, lambda x: x[0].update(z_q0125=-float(x[0]["z_q0125"])))
probe("summary_null_kind_to_empty", 1, lambda x: x[0].update(kind=""))
probe("raw_null_kind_to_NULL", 0, lambda x: [r.update(kind="NULL") for r in x if r["kind"] == "null"])
probe("paired_decided_count_plus_one", 2, lambda x: x[0].update(decided_in_A0_not_arm=x[0]["decided_in_A0_not_arm"] + 1))
probe("equivalent_effect_spelling_-0.20", 0, lambda x: [r.update(effect="-0.20") for r in x if r["kind"] == "effect"], expect_reject=False)


def a0_error_vs_valid_reference(x):
    r = next(r for r in x if r["arm"] == "A0" and r["verdict"] != "errore" and r["scenario"] == 7)
    r.update(verdict="errore", error="probe", se="", lo="", hi="", covered=0, below=0, above=0)


# Rejected, but through the generic input_structure_exception (reported as a low-severity finding).
probe("A0_error_vs_valid_reference", 0, a0_error_vs_valid_reference)

# One null group, four valid rows and one error row; values in units of eta0.
# r = [-1, 0, 2, 5], s = [1, 1, 2, 1]: mean r = 1.5, var(r, ddof=1) = 21/3 = 7, mean s^2 = 7/4 -> R = 0.25
# z = [-1, 0, 1, 5]: var(z, ddof=1) = 20.75/3; linear quantiles: 0.0125 -> -0.9625, 0.9875 -> 4.85
# only z = 5 > q: one "opposto"; covered 3 of 5 attempts (the error row is not covered)
E = C.ETA
rows = []
for rr, s in ((-1., 1.), (0., 1.), (2., 2.), (5., 1.)):
    b, se = rr * E, s * E
    lo, hi = b - C.Q * se, b + C.Q * se
    rows.append(dict(beta=b, beta_true=0., se=se, verdict="supportato" if hi < 0 else "opposto" if lo > 0 else "non deciso",
                     covered=int(lo <= 0 <= hi), below=int(lo > 0), above=int(hi < 0)))
rows.append(dict(beta=0., beta_true=0., se="", verdict="errore", covered=0, below=0, above=0))
got = C.recount_group(rows, "null")
exp = dict(n=5, errors=1, R=.25, sd_z=math.sqrt(20.75 / 3), z_q0125=-.9625, z_q9875=4.85, covered=3, below=1, above=0,
           coverage=.6, coverage_mc_se=math.sqrt(.6 * .4 / 5), false=1, false_frac=.2, false_mc_se=math.sqrt(.2 * .8 / 5),
           supported=0, opposite=1)
bad = {k: (got[k], v) for k, v in exp.items() if abs(got[k] - v) > 1e-12 + 1e-9 * abs(v)}
results.append(("hand_computed_group_with_error_row", not bad, bad or "all 16 fields equal"))

code = ROOT / "python/sharpbl/t5_oracle_postcheck.py"
print("checker_sha256", hashlib.sha256(code.read_bytes()).hexdigest())
for name, ok, detail in results:
    print(("PASS " if ok else "FAIL ") + name, detail)
print(f"{sum(r[1] for r in results)}/{len(results)} probes as expected")
sys.exit(0 if all(r[1] for r in results) else 1)
