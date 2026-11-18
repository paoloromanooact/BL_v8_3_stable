"""Offline chain for the second MDI-HMI sample: selector manifest -> availability parsing -> io.plan -> run_sample,
on the same manifest (Codex's review: the selector output must feed the next stages directly). No network."""
import csv
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mdi_hmi_availability as av  # noqa: E402
import mdi_hmi_patch_download as dl  # noqa: E402
import mdi_hmi_patch_io as io  # noqa: E402
import mdi_hmi_second_sample_select as sel  # noqa: E402


def arcs():
    out = []
    for i, st in enumerate(("N_central", "S_central")):
        out.append(dict(stratum=st, TARPNUM=str(100 + i), HARPNUM=str(200 + i), T_REC_smarp="2010.06.01_00:00:00_TAI",
                        T_REC_hmi="2010.06.01_00:00:00_TAI", component=f"C{i}", quality_mdi="0x00000200", certified=True,
                        npix_smarp="50", npix_hmi="500", abslon=3.0, abs_dt=10.0))
    return out


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def fake_doc(rows, side, key, segment, series):
    recs = [r[side + "_record"].split("|") for r in rows]
    return dict(status=0, count=len(recs), keywords=[dict(name=key, values=[i for i, _ in recs]),
                                                     dict(name="T_REC", values=[t for _, t in recs]),
                                                     dict(name="*online*", values=["Y"] * len(recs)),
                                                     dict(name="*size*", values=["5759"] * len(recs))],
                segments=[dict(name=segment, values=[f"/SUM9/D{j}{0 if side == 'smarp' else 1}/S00000/{segment}.fits" for j in range(len(recs))],
                               dims=["3x2"] * len(recs))])


@pytest.fixture
def chain(tmp_path, monkeypatch):
    chosen, _ = sel.select(arcs(), set())
    pairs_file = tmp_path / "selection/PAIRS.csv"
    write_csv(pairs_file, chosen)
    rows = list(csv.DictReader(pairs_file.open()))
    segments = []
    for side, key, names in av.SIDES:
        series = rows[0][side + "_series"]
        keys = {tuple(r[side + "_record"].split("|")): r["slot"] for r in rows}
        for s in names:
            segments += av.parse(fake_doc(rows, side, key, s, series), key, s, keys, series)
    seg_file = tmp_path / "availability/SEGMENTS.csv"
    write_csv(seg_file, segments)
    proto = tmp_path / "P.md"
    proto.write_text("frozen second-sample protocol")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    for name in ("BASE", "PROTOCOL", "PROTOCOL_HASH", "PAIR_HASH", "SEGMENT_HASH"):
        monkeypatch.setattr(io, name, getattr(io, name))
    io.use_sample(tmp_path, proto, sha(proto), sha(pairs_file), sha(seg_file))
    pairs, records = io.plan()
    return tmp_path, pairs, records


def fake_transport(target, dest, limit, expected, timeout):
    if expected:
        dest.write_bytes(b"SIMPLE  =" + b" " * (5760 - 9))
        return 2, "https://jsoc1.stanford.edu" + target
    dest.write_text(json.dumps({}))
    return 1, "http://jsoc.stanford.edu" + target


def test_selector_manifest_feeds_availability_plan_and_downloader(chain):
    tmp, pairs, records = chain
    assert len(pairs) == 2 and len(records) == 4
    assert all(set(f) == set(io.SEGMENTS[s]) for (s, _), f in records.items())
    m = dl.run_sample((pairs, records, {}, {}, 0, 0, 0), tmp / "dl", 200, 600, transport=fake_transport,
                      check_keys=lambda *a: None)
    assert len(m) == 2 * (2 + 5)
    man = json.loads((tmp / "dl/MANIFEST.json").read_text())
    assert man["status"] == "complete"


def test_byte_cap_counts_failed_attempts_and_resumes(chain):
    tmp, pairs, records = chain
    calls = []

    def failing(target, dest, limit, expected, timeout):
        calls.append(target)
        if expected:
            dest.write_bytes(b"x" * 5760)            # bytes received, then the attempt fails
            raise dl.TransportError(["length", "signature"][len(calls) % 2], "bad body")  # no systematic stop
        dest.write_text("{}")
        return 1, "x"
    with pytest.raises(ValueError, match="budget"):
        dl.run_sample((pairs, records, {}, {}, 0, 0, 0), tmp / "b", 500, 600, transport=failing,
                      check_keys=lambda *a: None, total_cap=3 * 5760)
    fits_calls = [c for c in calls if c.startswith("/SUM")]
    # with a cap of three bodies, received bytes of failed attempts stop the run before a fourth body
    assert len(fits_calls) <= 3
    led = json.loads((tmp / "b/LEDGER.json").read_text())
    assert sum(e["bytes"] for e in led["events"] if e["fits"]) <= 3 * 5760 + 5760
