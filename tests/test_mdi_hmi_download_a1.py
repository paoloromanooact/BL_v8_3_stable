"""Offline checks of amendment A1 transport: one allowed redirect, request accounting, systematic stop."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mdi_hmi_patch_download as dl  # noqa: E402

P = "/SUM4/D1406327134/S00000/bitmap.fits"


@pytest.mark.parametrize("loc,ok", [
    ("https://jsoc1.stanford.edu" + P, True),                 # the diagnosed redirect
    ("http://jsoc2.stanford.edu/prefix" + P, True),           # server prefix, same tail
    ("https://evil.example.org" + P, False),                  # other host
    ("https://jsoc1.stanford.edu/SUM4/D1/S00000/Br.fits", False),   # other file
    ("ftp://jsoc1.stanford.edu" + P, False),
    ("https://jsoc1.stanford.edu" + P + "?x=1", False),
    ("https://user@jsoc1.stanford.edu" + P, False),
    ("", False)])
def test_follow_location(loc, ok):
    assert (dl.follow_location(loc, P) is not None) == ok


class Res:
    def __init__(self, status, body=b"", location=None, length=True):
        self.status, self._b, self.chunked = status, body, False
        self.h = {"Location": location, "Content-Length": str(len(body)) if length else None}

    def getheader(self, k, d=None):
        v = self.h.get(k)
        return d if v is None else v

    def read1(self, n):
        out, self._b = self._b[:n], self._b[n:]
        return out


class Conn:
    def close(self):
        pass


def opener_from(seq):
    calls = []

    def op(scheme, host, port, path, timeout):
        calls.append((scheme, host, path))
        r = seq[len(calls) - 1]
        return r.status, r.h["Location"], r, Conn()
    return op, calls


def test_one_redirect_followed_and_counted(tmp_path):
    body = b"SIMPLE  =" + b" " * (2880 - 9)
    op, calls = opener_from([Res(302, b"x", "https://jsoc1.stanford.edu" + P), Res(200, body)])
    side = tmp_path / "s.json"
    dl.receive_a1(P, tmp_path / "f.fits", 2881, (2880, 2881), 10, side, opener=op)
    info = json.loads(side.read_text())
    assert info["requests"] == 2 and info["final_url"] == "https://jsoc1.stanford.edu" + P
    assert calls[1][0] == "https" and (tmp_path / "f.fits").read_bytes() == body


def test_second_redirect_and_bad_host_refused(tmp_path):
    op, _ = opener_from([Res(302, b"", "https://jsoc1.stanford.edu" + P), Res(302, b"", "https://jsoc2.stanford.edu" + P)])
    with pytest.raises(dl.TransportError) as e:
        dl.receive_a1(P, tmp_path / "a.fits", 2881, (2880,), 10, tmp_path / "a.json", opener=op)
    assert e.value.kind == "redirect" and json.loads((tmp_path / "a.json").read_text())["requests"] == 2
    op, _ = opener_from([Res(302, b"", "https://evil.example.org" + P)])
    with pytest.raises(dl.TransportError) as e:
        dl.receive_a1(P, tmp_path / "b.fits", 2881, (2880,), 10, tmp_path / "b.json", opener=op)
    assert e.value.kind == "redirect"


def test_length_disagreeing_with_manifest_refused(tmp_path):
    op, _ = opener_from([Res(302, b"", "https://jsoc1.stanford.edu" + P), Res(200, b"SIMPLE  =" + b" " * 100)])
    with pytest.raises(dl.TransportError) as e:
        dl.receive_a1(P, tmp_path / "c.fits", 2881, (2880, 2881), 10, tmp_path / "c.json", opener=op)
    assert e.value.kind == "length"


def _prepared(n_files=5):
    rec = {}
    for i in range(n_files):
        rec[(dl.io.MDI, f"{i}|T")] = {"bitmap": dict(slot=str(i + 1), path=f"/SUM1/D{i}/S00000/bitmap.fits",
                                                      reported_bytes="2880", dims="3x2", series=dl.io.MDI,
                                                      record=f"{i}|T", segment="bitmap")}
    return ([], rec, {}, {}, 0, 0, 0)


def _old_ledger(tmp_path):
    old = tmp_path / "old"
    old.mkdir()
    (old / "LEDGER.json").write_text(json.dumps(dict(protocol=dl.io.PROTOCOL_HASH, pairs=dl.io.PAIR_HASH,
                                                     segments=dl.io.SEGMENT_HASH, events=[])))
    return old


def test_stop_after_three_consecutive_same_failures(tmp_path):
    calls = []

    def bad(target, dest, limit, expected, timeout):
        calls.append(target)
        raise dl.TransportError("tls", "handshake")
    with pytest.raises(ValueError, match="consecutive 'tls'"):
        dl.run_a1(_prepared(5), old=_old_ledger(tmp_path), out=tmp_path / "new", transport=bad)
    assert len(calls) == 3
    man = json.loads((tmp_path / "new/MANIFEST.json").read_text())
    assert man["status"] == "partial" and man["stopped"].startswith("systematic")


def test_success_accounting_and_resume(tmp_path):
    def good(target, dest, limit, expected, timeout):
        dest.write_bytes(b"SIMPLE  =" + b" " * (2880 - 9))
        return 2, "https://jsoc1.stanford.edu" + target
    old = _old_ledger(tmp_path)
    m = dl.run_a1(_prepared(3), old=old, out=tmp_path / "new", transport=good)
    assert len(m) == 3
    led = json.loads((tmp_path / "new/LEDGER.json").read_text())
    assert sum(e["requests"] for e in led["events"]) == 6 and all(e["state"] == "ok" for e in led["events"])

    def never(*a):
        raise AssertionError("no new request on resume")
    assert len(dl.run_a1(_prepared(3), old=old, out=tmp_path / "new", transport=never)) == 3


# ---------------------------------------------------------------- second-sample fresh acquisition (run_sample)

def _prepared_sample(n_pairs=2):
    pairs, rec = [], {}
    for i in range(n_pairs):
        slot = str(i + 1)
        p = dict(slot=slot, smarp_series=dl.io.MDI, smarp_record=f"{100 + i}|T", hmi_series=dl.io.HMI,
                 hmi_record=f"{200 + i}|T", quality_mdi="0x00000200", quality_hmi="0x00000000")
        pairs.append(p)
        for series, r, segs in ((dl.io.MDI, p["smarp_record"], ("bitmap", "magnetogram")),
                                (dl.io.HMI, p["hmi_record"], ("bitmap", "Br"))):
            rec[(series, r)] = {s: dict(slot=slot, path=f"/SUM1/D{i}{series[:3]}/S00000/{s}.fits", reported_bytes="2880",
                                        dims="3x2", series=series, record=r, segment=s) for s in segs}
    return (pairs, rec, {}, {}, 10, 5.0, 0)


def _fake(fail_fits=None):
    calls = []

    def tr(target, dest, limit, expected, timeout):
        calls.append(target)
        if expected:
            if fail_fits:
                raise dl.TransportError(fail_fits, "boom")
            dest.write_bytes(b"SIMPLE  =" + b" " * (2880 - 9))
            return 2, "https://jsoc1.stanford.edu" + target
        dest.write_text("{}")
        return 1, "http://jsoc.stanford.edu" + target
    return tr, calls


def test_run_sample_counts_requests_and_resumes(tmp_path):
    tr, calls = _fake()
    m = dl.run_sample(_prepared_sample(2), tmp_path / "s", 100, 600, transport=tr, check_keys=lambda *a: None)
    assert len(m) == 8 and len(calls) == 4 + 8
    led = json.loads((tmp_path / "s/LEDGER.json").read_text())
    assert sum(e["requests"] for e in led["events"]) == 4 * 1 + 8 * 2
    man = json.loads((tmp_path / "s/MANIFEST.json").read_text())
    assert man["status"] == "complete" and man["requests_used"] == 10 + 20

    def never(*a):
        raise AssertionError("resume must not request")
    assert len(dl.run_sample(_prepared_sample(2), tmp_path / "s", 100, 600, transport=never,
                             check_keys=lambda *a: None)) == 8


def test_run_sample_stops_on_systematic_errors(tmp_path):
    tr, calls = _fake(fail_fits="tls")
    with pytest.raises(ValueError, match="consecutive 'tls'"):
        dl.run_sample(_prepared_sample(2), tmp_path / "s", 100, 600, transport=tr, check_keys=lambda *a: None)
    assert sum(1 for c in calls if c.startswith("/SUM")) == 3


def test_run_sample_budget_and_bad_keys(tmp_path):
    tr, _ = _fake()
    with pytest.raises(ValueError, match="budget"):
        dl.run_sample(_prepared_sample(2), tmp_path / "b", 14, 600, transport=tr, check_keys=lambda *a: None)

    def bad_keys(path, series, rec, files):
        raise ValueError("Keyword identity mismatch")
    with pytest.raises(ValueError, match="consecutive 'validation'"):
        dl.run_sample(_prepared_sample(2), tmp_path / "k", 100, 600, transport=tr, check_keys=bad_keys)
