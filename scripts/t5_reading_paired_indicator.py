"""Descriptive paired indicator for the T5-D2 reading (added 2026-11-15 after review).

Not pre-registered and not a test: no threshold is applied. For each arm and
group, the catalogues are paired with A0 on the same key. Under the null, an
"event" is a decided verdict (supportato or opposto); under an effect, it is
non-coverage (errors count as non-coverage, as in the convention). b = event
in A0 only, c = event in the arm only. The difference of the two frequencies
is (c - b)/N and its paired Monte Carlo error is sqrt(b + c)/N (McNemar-type
approximation, conditional on the discordant pairs).

Reads results/T5_ORACLE/ORACLE_RAW.csv.gz (unchanged) and writes
results/T5_ORACLE_READING/PAIRED_INDICATOR.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results/T5_ORACLE/ORACLE_RAW.csv.gz"
OUT = ROOT / "results/T5_ORACLE_READING/PAIRED_INDICATOR.csv"
KEY = ["kind", "scenario", "effect", "k"]


def main():
    raw = pd.read_csv(RAW, keep_default_na=False,
                      usecols=KEY + ["arm", "verdict", "covered"])
    a0 = raw[raw.arm == "A0"].set_index(KEY)
    rows = []
    for arm in ["A1a", "A1b", "A2", "A3", "A2p"]:
        x = raw[raw.arm == arm].set_index(KEY).join(a0, rsuffix="_A0", how="inner")
        for (kind, scen, eff), d in x.groupby(level=[0, 1, 2]):
            if kind == "null":
                ev = d.verdict.isin(["supportato", "opposto"])
                ev0 = d.verdict_A0.isin(["supportato", "opposto"])
                event = "decided"
            else:
                ev = d.covered.astype(str) != "1"
                ev0 = d.covered_A0.astype(str) != "1"
                event = "not_covered"
            b, c, n = int((ev0 & ~ev).sum()), int((~ev0 & ev).sum()), len(d)
            se = np.sqrt(b + c) / n
            rows.append(dict(kind=kind, scenario=scen, effect=eff, arm=arm, event=event,
                             n=n, event_A0_only=b, event_arm_only=c,
                             diff_frac=(c - b) / n, paired_mc_se=se,
                             diff_over_se=(c - b) / np.sqrt(b + c) if b + c else 0.0))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"written {OUT.relative_to(ROOT)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
