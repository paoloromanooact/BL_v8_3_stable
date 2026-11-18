"""Independent check of results/PROSPECTIVE_PHASE_A (read-only): hashes, counts, E0 identities, zero-offset frequencies
recomputed from RAW with separate code, phase B selection. Writes results/PROSPECTIVE_PHASE_A_CHECK/RECEIPT.json."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "results/PROSPECTIVE_PHASE_A"
OUT = ROOT / "results/PROSPECTIVE_PHASE_A_CHECK"


def main():
    if OUT.exists():
        sys.exit("refusing to overwrite the check receipt")
    m = json.loads((D / "META.json").read_text())
    raw = pd.read_csv(D / "RAW.csv.gz")
    fr = pd.read_csv(D / "FREQUENCIES.csv.gz")
    b = pd.read_csv(D / "B_SELECTION.csv")
    z = norm.ppf(1 - 0.0125)
    res = []

    def ok(name, cond, value=""):
        res.append(dict(name=name, ok=bool(cond), value=str(value)))
        print(("OK " if cond else "FALLITO ") + name, value)
    ok("product hashes equal to META", all(hashlib.sha256((D / k).read_bytes()).hexdigest() == v
                                           for k, v in m["products_sha256"].items()))
    ok("outcome eseguita and selftest all passed", m["outcome"] == "eseguita" and all(s["ok"] for s in m["selftest"]))
    exp = 6 * 9 + 20 * 6 * 9 + 3 * 60 * 6 * 9 * 3      # E0, E1, then E2/E3/E4 with 3 f x 20 r x 3 k
    ok("RAW rows (6 matrices x 9 noise; k only with MDI)", len(raw) == exp, (len(raw), exp))
    ok("realisations 0..19 for every (ext, f)", all(sorted(g.r.unique()) == list(range(20))
                                                    for _, g in raw[raw.ext != "E0"].groupby(["ext", "f"])))
    e0 = raw[raw.ext == "E0"]
    ok("E0 T5 target -0.10305075 eta_bar", np.allclose(e0[e0.test == "T5"].target_020 / 3.56e-25,
                                                      -0.10305075387820256, rtol=1e-9))
    ok("E0 T3 target -1.60265 deg (Codex's separate WLS)", np.allclose(e0[e0.test == "T3"].target_020, -1.60265, atol=5e-6))
    sel = fr[(fr.c0 == 0) & (fr.c1 == 0) & (fr.c2 == 0)]
    keys = ["ext", "f", "test", "family", "model", "noise", "k"]
    rc = raw.groupby(keys, dropna=False).apply(
        lambda g: pd.Series(dict(sup=np.median(norm.sf(z + g.target_020 / g.se)),
                                 excl=np.median(norm.sf(z + g.target_020 / g.se)))), include_groups=False).reset_index()
    mm = sel.merge(rc, on=keys, how="inner")
    ok("zero-offset recognition medians recomputed from RAW", len(mm) == len(sel)
       and np.allclose(mm.sup_scen_020_median, mm.sup, atol=1e-12), len(mm))
    ok("zero-offset exclusion under null equals recognition (no bias)", np.allclose(mm.excl_null_020_median, mm.excl, atol=1e-12))
    ok("no bias: 'supportato' under null 1.25 %", np.allclose(sel.sup_null_median, 0.0125, atol=1e-12))
    inb = b[b.in_band == 1]
    ok("phase B: 114 candidates; selected = in band (<= 24)", len(b) == 114 and len(inb) <= 24
       and set(b[b.selected == 1].order) == set(inb.order), int(b.selected.sum()))
    OUT.mkdir(parents=True)
    rec = dict(checks=res, passed=sum(r["ok"] for r in res), total=len(res),
               meta_sha256=hashlib.sha256((D / "META.json").read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / "RECEIPT.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(f"{rec['passed']}/{rec['total']}")
    return 0 if rec["passed"] == rec["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
