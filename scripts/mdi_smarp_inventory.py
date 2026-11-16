"""Limited MDI/SMARP metadata inventory (docs/MDI_SMARP_METADATA_INVENTORY_PLAN.md, frozen in 9269c10,
SHA-256 a31de02a..., receipt docs/MDI_SMARP_METADATA_INVENTORY_FREEZE.json in b276502).

Catalogue metadata only: no export, no staging, no FITS or map download, no new measurement. Network phases are
refused before the end of the T5 grid, on a dirty tracked tree, without a verified plan hash, and (for records)
without a registered field map.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/mdi_smarp_inventory.py --selftest              # §8, offline only
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase schema   --run-id RUN             # §3 (network)
    .venv/bin/python scripts/mdi_smarp_inventory.py --register-map   --run-id RUN --verified-by WHO   # offline
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase counts   --run-id RUN             # §4.2 (network)
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase overlap  --run-id RUN             # §4.3 (network)
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase history  --run-id RUN             # §4.2-4.3 (network)
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase aux      --run-id RUN             # §4.3 (network)
    .venv/bin/python scripts/mdi_smarp_inventory.py --phase continuum --run-id RUN            # §4.2, optional, last
    .venv/bin/python scripts/mdi_smarp_inventory.py --analyze        --run-id RUN             # §5-§7, offline

Implementation choices (not new rules; listed for the code review):
- Transport: http.client over HTTPS to jsoc.stanford.edu/cgi-bin/ajax/jsoc_info only, ops series_struct,
  rs_summary, rs_list; Accept-Encoding identity; body read with read1() so that the byte cap and the absolute
  deadline are checked on every received block; the socket timeout is min(45 s, remaining time) before every
  read. At most one redirect is followed, and only to the same allowed endpoint; it counts as an attempt.
- Requests per logical request: at most 3 attempts with waits of 5 and 15 s; at least 1 s between attempts;
  Retry-After honoured only within the remaining time. HTTP 4xx other than 429 are not retried.
- One persistent registry (REGISTRY.json) holds attempts, bytes, distinct accepted rows and cumulative wall time
  of invocations; it is written after every attempt and never reset. A lock file prevents two instances.
- Record sets are written in the real primekey order from the saved schema; the time key gets an inclusive DRMS
  range [start-end] and every response is filtered locally on the half-open window; rows at the excluded end are
  recorded as edge rows before deduplication. Identity = series + all primekeys.
- Budget decisions (§4.2): 'full' if used + lists still needed + 400 reserved attempts (200 aux + 200 retries or
  splits) <= 1000 and expected rows <= 2 000 000; otherwise 'overlap_only' if the overlap fits the same rule;
  otherwise 'stop'. The payload projection of §4.2 is applied before the historical lists.
- T5: network is refused while a process matching 't5_power_sensitivity.py --run' exists or while
  results/T5_POWER_SENSITIVITY/META.json is missing; the content of that file is not read.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import hashlib
import http.client
import io
import json
import math
import os
import platform
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/MDI_SMARP_METADATA_INVENTORY_PLAN.md"
FREEZE = ROOT / "docs/MDI_SMARP_METADATA_INVENTORY_FREEZE.json"
SHA_PLAN = "a31de02a064b08584281930f4a7c7e0fc4216ab83cc7f69c8ee793ea5bce3be0"
RAW_BASE = ROOT / "data/sharp/metadata_inventory_mdi"
RES_BASE = ROOT / "results/MDI_SMARP_INVENTORY"
SELFTEST_BASE = ROOT / "results/MDI_SMARP_INVENTORY_SELFTEST"
T5_META = ROOT / "results/T5_POWER_SENSITIVITY/META.json"

HOST, PATH = "jsoc.stanford.edu", "/cgi-bin/ajax/jsoc_info"
OPS = ("series_struct", "rs_summary", "rs_list")

SMARP, SMARP_LEV, FD, HMI, IC = ("mdi.smarp_cea_96m", "mdi.smarp_96m", "mdi.fd_M_96m_lev182",
                                 "hmi.sharp_cea_720s", "mdi.fd_Ic_interp")
SERIES = (SMARP, FD, HMI, SMARP_LEV, IC)
PROFILES = ("smarp_min", "smarp_overlap", "fd_min", "hmi_overlap")
PROFILE_SERIES = {"smarp_min": SMARP, "smarp_overlap": SMARP, "fd_min": FD, "hmi_overlap": HMI}

# §4.1 caps
CAP_ATTEMPTS = 1000
CAP_ROWS = 2_000_000
CAP_BYTES = 1 << 30
CAP_WALL_S = 90 * 60
RESERVE_AUX, RESERVE_RETRY = 200, 200
MAX_TRIES, WAITS = 3, (5.0, 15.0)
IDLE_TIMEOUT, MIN_SPACING = 45.0, 1.0
SPLIT_LIMIT = 25_000
AUX_BATCH = 100
# §2 and §6 windows (TAI, naive datetimes are TAI)
T0, T1 = datetime(1996, 1, 1), datetime(2010, 10, 29)
OV0, OV1 = datetime(2010, 5, 1), datetime(2010, 10, 29)
MARGIN = timedelta(seconds=360)
HMI0, HMI1 = OV0 - MARGIN, OV1 + MARGIN
TIME_TOL_S = 360.0
SOURCE_TIME_TOL_S = 1.0
RADII = (5.0, 10.0)
EDGE_POINTS = 65


class TechnicalError(Exception):
    """Failure that prevents certifying a result (identity conflict, count/list mismatch, bad hash...)."""


class BudgetStop(Exception):
    """A cap of §4.1 would be exceeded: stop with a partial inventory."""


class RequestFailed(Exception):
    """A logical request failed after its allowed attempts (kept, never skipped)."""


# ---------------------------------------------------------------- small helpers

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path, data: bytes):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_json(path, obj):
    atomic_write(path, json.dumps(obj, indent=2, sort_keys=True, allow_nan=False, default=str).encode())


def tai_str(t: datetime):
    return t.strftime("%Y.%m.%d_%H:%M:%S_TAI")


_TRE = re.compile(r"^(\d{4})[.-](\d{2})[.-](\d{2})(?:[_T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?)?(?:_?(TAI|UTC|Z))?$")


def parse_time(s):
    """JSOC time string -> (TAI datetime or None, status). UTC is converted with astropy leap seconds."""
    if s is None:
        return None, "missing"
    s = str(s).strip()
    if s == "" or s.upper() in ("MISSING", "NAN", "INVALID KEY"):
        return None, "missing"
    m = _TRE.match(s)
    if not m:
        return None, "invalid"
    y, mo, d, hh, mm, ss, frac, scale = m.groups()
    try:
        t = datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0), int(ss or 0))
    except ValueError:
        return None, "invalid"
    if frac:
        t += timedelta(seconds=float("0." + frac))
    if scale in (None, ""):
        return None, "no_time_scale"
    if scale == "TAI":
        return t, "ok"
    from astropy.time import Time
    tt = Time(t, scale="utc").tai.to_datetime()
    return tt, "ok_from_utc"


def to_float(s):
    """String -> (float or None, status) keeping invalid distinct from missing."""
    if s is None:
        return None, "missing"
    s = str(s).strip()
    if s == "" or s.upper() in ("MISSING", "INVALID KEY"):
        return None, "missing"
    try:
        v = float(s)
    except ValueError:
        return None, "invalid"
    if not math.isfinite(v):
        return None, "nonfinite"
    return v, "ok"


def parse_quality(s):
    """QUALITY string -> (int or None, normalized 32-bit hex or '', status)."""
    if s is None or str(s).strip() == "":
        return None, "", "missing"
    t = str(s).strip()
    try:
        v = int(t, 16) if t.lower().startswith(("0x", "-0x")) else int(t)
    except ValueError:
        try:
            f = float(t)
        except ValueError:
            return None, "", "invalid"
        if not (math.isfinite(f) and f == int(f)):
            return None, "", "invalid"
        v = int(f)
    if not -(1 << 31) <= v < (1 << 32):
        return v, "", "out_of_32bit"
    return v, f"0x{v & 0xFFFFFFFF:08X}", "ok"


# ---------------------------------------------------------------- registry (§4.1): persistent, never reset

class Registry:
    def __init__(self, path, caps=None, min_spacing=MIN_SPACING):
        self.path = Path(path)
        self.min_spacing = min_spacing
        self.caps = caps or dict(attempts=CAP_ATTEMPTS, rows=CAP_ROWS, bytes=CAP_BYTES, wall_s=CAP_WALL_S)
        if self.path.exists():
            self.d = json.loads(self.path.read_text())
        else:
            self.d = dict(attempts=0, aux_attempts=0, bytes=0, rows=0, wall_s_completed=0.0, invocations=[],
                          last_attempt_monotonic=None, created_utc=now_utc(), caps=self.caps)
        if self.d.get("caps") != self.caps:
            raise TechnicalError("registry caps differ from the frozen caps")
        self.t_start = time.monotonic()
        self.inv = dict(start_utc=now_utc(), phase=None)
        self._last = 0.0

    def used_wall(self):
        return self.d["wall_s_completed"] + (time.monotonic() - self.t_start)

    def remaining_time(self):
        return self.caps["wall_s"] - self.used_wall()

    def check(self, what, n_attempts=0, n_bytes=0, n_rows=0):
        if self.remaining_time() <= 0:
            raise BudgetStop(f"time cap before {what}")
        if self.d["attempts"] + n_attempts > self.caps["attempts"]:
            raise BudgetStop(f"attempt cap before {what}")
        if self.d["bytes"] + n_bytes > self.caps["bytes"]:
            raise BudgetStop(f"byte cap before {what}")
        if self.d["rows"] + n_rows > self.caps["rows"]:
            raise BudgetStop(f"row cap before {what}")

    def spacing(self):
        """At least MIN_SPACING seconds between attempts (also across a resume within the same process)."""
        dt = time.monotonic() - self._last
        if self._last and dt < self.min_spacing:
            self.sleep(self.min_spacing - dt)

    def sleep(self, s):
        if s >= self.remaining_time():
            raise BudgetStop("time cap during a wait")
        time.sleep(max(0.0, s))

    def add_attempt(self, aux=False):
        self.check("attempt", n_attempts=1)
        self.d["attempts"] += 1
        if aux:
            self.d["aux_attempts"] += 1
        self._last = time.monotonic()
        self.save()

    def add_bytes(self, n):
        self.d["bytes"] += n

    def add_rows(self, n):
        self.d["rows"] += n
        self.save()

    def save(self):
        d = dict(self.d)
        d["wall_s_live"] = self.used_wall()
        write_json(self.path, d)

    def close(self, phase, outcome):
        self.d["wall_s_completed"] += time.monotonic() - self.t_start
        self.inv.update(phase=phase, end_utc=now_utc(), outcome=outcome)
        self.d["invocations"].append(self.inv)
        self.t_start = time.monotonic()
        write_json(self.path, self.d)


# ---------------------------------------------------------------- transport (§4.1)

class Transport:
    """Bounded HTTP(S) GET for jsoc_info; everything logged and saved, nothing silently retried."""

    def __init__(self, reg: Registry, raw_dir, scheme="https", host=HOST, port=None, path=PATH, waits=WAITS):
        self.reg, self.raw_dir = reg, Path(raw_dir)
        self.scheme, self.host, self.port, self.path, self.waits = scheme, host, port, path, waits
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.log = self.raw_dir / "QUERY_LOG.jsonl"

    def url(self, params):
        if params.get("op") not in OPS:
            raise TechnicalError(f"operation not allowed: {params.get('op')!r}")
        return f"{self.path}?{urlencode(params)}"

    def _allowed_redirect(self, loc):
        u = urlsplit(loc)
        host_ok = u.hostname in (self.host,) and (u.scheme or self.scheme) == self.scheme
        q = parse_qs(u.query)
        return host_ok and u.path == self.path and q.get("op", [None])[0] in OPS

    def _write_log(self, entry):
        with open(self.log, "a") as f:
            f.write(json.dumps(entry, sort_keys=True, default=str) + "\n")

    def _one(self, target, tag, aux):
        """One attempt. Returns (status, headers, body, outcome)."""
        reg = self.reg
        reg.spacing()
        reg.add_attempt(aux=aux)
        rem = reg.remaining_time()
        to = max(0.001, min(IDLE_TIMEOUT, rem))
        cls = http.client.HTTPSConnection if self.scheme == "https" else http.client.HTTPConnection
        conn = cls(self.host, self.port, timeout=to)
        body = bytearray()
        status, headers, outcome = None, {}, "ok"
        deadline = time.monotonic() + rem
        try:
            conn.request("GET", target, headers={"Accept-Encoding": "identity", "User-Agent": "sharpbl-mdi-inventory"})
            resp = conn.getresponse()
            status, headers = resp.status, {k.lower(): v for k, v in resp.getheaders()}
            enc = headers.get("content-encoding", "identity").strip().lower()
            if enc not in ("", "identity"):
                outcome = "unexpected_encoding"
            else:
                while True:
                    left = deadline - time.monotonic()
                    if left <= 0:
                        outcome = "deadline"
                        break
                    if conn.sock is not None:
                        conn.sock.settimeout(max(0.001, min(IDLE_TIMEOUT, left)))
                    chunk = resp.read1(65536)
                    if not chunk:
                        break
                    room = reg.caps["bytes"] - reg.d["bytes"]
                    if len(chunk) > room:
                        body.extend(chunk[:max(0, room)])
                        reg.add_bytes(max(0, room))
                        outcome = "truncated_by_budget"
                        break
                    body.extend(chunk)
                    reg.add_bytes(len(chunk))
                    if time.monotonic() > deadline:
                        outcome = "deadline"
                        break
        except (socket.timeout, TimeoutError):
            outcome = "idle_timeout"
        except (OSError, http.client.HTTPException) as exc:
            outcome = f"transport_error: {type(exc).__name__}: {exc}"
        finally:
            conn.close()
        raw = bytes(body)
        fname = f"{tag}_a{reg.d['attempts']:04d}.body"
        atomic_write(self.raw_dir / fname, raw)
        self._write_log(dict(utc=now_utc(), tag=tag, attempt_global=reg.d["attempts"], target=target, status=status,
                             outcome=outcome, bytes=len(raw), sha256=sha_bytes(raw), file=fname,
                             content_encoding=headers.get("content-encoding"), retry_after=headers.get("retry-after")))
        reg.save()
        return status, headers, raw, outcome, fname

    def get(self, params, tag, aux=False):
        """Logical request: up to MAX_TRIES attempts; returns (parsed JSON dict, file name)."""
        target = self.url(params)
        last = None
        for i in range(MAX_TRIES):
            status, headers, raw, outcome, fname = self._one(target, f"{tag}_t{i + 1}", aux)
            if outcome == "truncated_by_budget":
                raise BudgetStop(f"byte cap reached while receiving {tag} (prefix kept in {fname})")
            if outcome == "deadline":
                raise BudgetStop(f"time cap reached while receiving {tag} (prefix kept in {fname})")
            if outcome == "unexpected_encoding":
                raise RequestFailed(f"{tag}: unexpected content encoding {headers.get('content-encoding')!r}")
            if outcome == "ok" and status in (301, 302, 303, 307, 308):
                loc = headers.get("location", "")
                if not self._allowed_redirect(loc):
                    raise RequestFailed(f"{tag}: redirect to a non-allowed destination {loc!r}")
                u = urlsplit(loc)
                target = u.path + ("?" + u.query if u.query else "")
                last = f"redirect {status}"
                continue
            if outcome == "ok" and status == 200:
                try:
                    data = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, ValueError) as exc:
                    raise RequestFailed(f"{tag}: invalid JSON ({exc})") from None
                if not isinstance(data, dict):
                    raise RequestFailed(f"{tag}: JSON is not an object")
                st = data.get("status", 0)
                if st not in (0, "0"):
                    raise RequestFailed(f"{tag}: DRMS status {st!r}: {data.get('error')!r}")
                return data, fname
            last = f"{outcome} status {status}"
            if status is not None and 400 <= status < 500 and status != 429:
                raise RequestFailed(f"{tag}: HTTP {status}")
            if i + 1 < MAX_TRIES:
                wait = self.waits[i]
                ra = headers.get("retry-after")
                if ra is not None:
                    try:
                        wait = max(wait, float(ra))
                    except ValueError:
                        pass
                self.reg.sleep(wait)
        raise RequestFailed(f"{tag}: failed after {MAX_TRIES} attempts ({last})")


# ---------------------------------------------------------------- windows (§2, §4.2)

def add_month(t):
    return datetime(t.year + (t.month == 12), t.month % 12 + 1, 1)


def months(a, b):
    out, t = [], datetime(a.year, a.month, 1)
    while t < b:
        out.append((max(t, a), min(add_month(t), b)))
        t = add_month(t)
    return out


def years(a, b):
    return [(max(datetime(y, 1, 1), a), min(datetime(y + 1, 1, 1), b)) for y in range(a.year, b.year + 1)
            if datetime(y, 1, 1) < b]


def steps(a, b, d):
    out, t = [], a
    while t < b:
        out.append((t, min(t + d, b)))
        t += d
    return out


def split_window(a, b, level):
    """Deterministic children: year -> months -> 7-day -> days -> 96-min intervals (§4.2)."""
    if level == "year":
        return [(x, y, "month") for x, y in months(a, b)]
    if level == "month":
        return [(x, y, "week") for x, y in steps(a, b, timedelta(days=7))]
    if level == "week":
        return [(x, y, "day") for x, y in steps(a, b, timedelta(days=1))]
    if level == "day":
        return [(x, y, "slot96") for x, y in steps(a, b, timedelta(minutes=96))]
    return []


def initial_windows():
    """(part, series, profile, start, end, level) in the fixed order of §4.3: overlap first."""
    w = []
    sm = months(T0, T1)
    fdy = years(T0, T1)
    hm = steps(HMI0, HMI1, timedelta(days=7))
    ov_months = [x for x in sm if x[0] >= OV0]
    w += [("overlap", SMARP, "smarp_overlap", a, b, "month") for a, b in ov_months]
    w += [("overlap", HMI, "hmi_overlap", a, b, "week") for a, b in hm]
    w += [("overlap", FD, "fd_min", a, b, "year") for a, b in fdy if a.year == 2010]
    w += [("history", SMARP, "smarp_min", a, b, "month") for a, b in sm if a < OV0]
    w += [("history", FD, "fd_min", a, b, "year") for a, b in fdy if a.year < 2010]
    return w


def base_budget():
    """§4.2 table: 356 + 30 + 52 + 15 + 15 = 468."""
    n_sm, n_fd, n_hmi = len(months(T0, T1)), len(years(T0, T1)), len(steps(HMI0, HMI1, timedelta(days=7)))
    return dict(smarp=2 * n_sm, fd=2 * n_fd, hmi=2 * n_hmi, continuum=len(years(T0, T1)), schema=15,
                total=2 * n_sm + 2 * n_fd + 2 * n_hmi + len(years(T0, T1)) + 15)


# ---------------------------------------------------------------- schema (§3)

def parse_schema(js):
    """series_struct JSON -> primekeys, keywords {name: dict}, links, segments, epoch/step of the time key."""
    pk = js.get("primekeys") or []
    if isinstance(pk, str):
        pk = [x.strip() for x in pk.split(",") if x.strip()]
    kws = {k.get("name"): k for k in (js.get("keywords") or []) if isinstance(k, dict) and k.get("name")}
    info = {}
    for k in pk:
        ep, stp = kws.get(f"{k}_epoch"), kws.get(f"{k}_step")
        info[k] = dict(epoch=(ep or {}).get("defval"), step=(stp or {}).get("defval"),
                       step_unit=(kws.get(f"{k}_unit") or {}).get("defval"),
                       type=(kws.get(k) or {}).get("type"))
    for e in js.get("primekeysinfo") or []:
        if isinstance(e, dict) and e.get("name") in info:
            for a in ("epoch", "step"):
                if e.get(a) is not None and info[e["name"]][a] is None:
                    info[e["name"]][a] = e.get(a)
    return dict(primekeys=list(pk), keywords=kws, links=js.get("links") or [], segments=js.get("segments") or [],
                primekeyinfo=info)


def time_key(schema):
    """The slotted time primekey (T_REC expected); None if not identifiable."""
    for k in schema["primekeys"]:
        if k.upper().startswith("T_") and (schema["primekeyinfo"].get(k, {}).get("type") or "").lower() == "time":
            return k
    return "T_REC" if "T_REC" in schema["primekeys"] else None


ROLE_CANDIDATES = {
    "time_obs": ["T_OBS"], "quality": ["QUALITY"],
    "noaa_ar": ["NOAA_AR"], "noaa_ars": ["NOAA_ARS"], "noaa_num": ["NOAA_NUM"],
    "naxis1": ["NAXIS1"], "naxis2": ["NAXIS2"], "crpix1": ["CRPIX1"], "crpix2": ["CRPIX2"],
    "crval1": ["CRVAL1"], "crval2": ["CRVAL2"], "cdelt1": ["CDELT1"], "cdelt2": ["CDELT2"],
    "ctype1": ["CTYPE1"], "ctype2": ["CTYPE2"], "cunit1": ["CUNIT1"], "cunit2": ["CUNIT2"],
    "crota2": ["CROTA2"], "pc1_1": ["PC1_1"], "pc1_2": ["PC1_2"], "pc2_1": ["PC2_1"], "pc2_2": ["PC2_2"],
    "pv2_1": ["PV2_1"], "crln_obs": ["CRLN_OBS"], "crlt_obs": ["CRLT_OBS"],
    "usflux": ["USFLUXL", "USFLUX"], "area": ["AREA", "AREA_ACR"], "npix": ["NPIX"],
    "lat_fwt": ["LAT_FWT"], "lon_fwt": ["LON_FWT"],
}
PROFILE_ROLES = {
    "smarp_min": ["time_obs", "quality"],
    "fd_min": ["time_obs", "quality"],
    "smarp_overlap": None, "hmi_overlap": None,          # None = every role of ROLE_CANDIDATES
}
PROVENANCE_HINT = re.compile(r"(SOURCE|MAGNETOGRAM|ORIGIN|INTERVAL|EXPTIME|EXPOSURE|DATAVALS|INSTRUME|"
                             r"PROC|VERSION|DATE$|CODEVER|OBS_MODE)", re.I)


def propose_field_map(schemas):
    """FIELD_MAP proposal from saved schemas; a human/reviewer verifies it before any record query (§3)."""
    rows = []
    for prof in PROFILES:
        s = PROFILE_SERIES[prof]
        sc = schemas.get(s)
        if sc is None:
            rows.append(dict(profile=prof, series=s, role="schema", name="", status="schema_not_verified",
                             type="", unit="", definition_ref="", normalization="", depends_on=""))
            continue
        for k in sc["primekeys"]:
            kw = sc["keywords"].get(k, {})
            rows.append(dict(profile=prof, series=s, role="primekey", name=k, status="present", type=kw.get("type", ""),
                             unit=kw.get("units", ""), definition_ref=f"series_struct {s}", normalization="string",
                             depends_on="identity"))
        roles = PROFILE_ROLES[prof] or list(ROLE_CANDIDATES)
        for r in roles:
            name = next((c for c in ROLE_CANDIDATES[r] if c in sc["keywords"]), "")
            kw = sc["keywords"].get(name, {})
            rows.append(dict(profile=prof, series=s, role=r, name=name, status="present" if name else "not_exposed",
                             type=kw.get("type", ""), unit=kw.get("units", ""),
                             definition_ref=(f"series_struct {s}: " + str(kw.get("note", ""))[:120]) if name else "",
                             normalization="", depends_on=""))
        for name, kw in sorted(sc["keywords"].items()):
            if PROVENANCE_HINT.search(name) and name not in [x["name"] for x in rows if x["series"] == s]:
                rows.append(dict(profile=prof, series=s, role="provenance_candidate", name=name, status="present",
                                 type=kw.get("type", ""), unit=kw.get("units", ""),
                                 definition_ref=f"series_struct {s}: " + str(kw.get("note", ""))[:120],
                                 normalization="", depends_on="to be confirmed by the reviewer"))
    return rows


FIELD_COLS = ["profile", "series", "role", "name", "status", "type", "unit", "definition_ref", "normalization",
              "depends_on"]


def write_csv(path, rows, cols):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def profile_keys(field_map, prof):
    """Requested keywords of a profile: primekeys + present roles + confirmed provenance."""
    keys = []
    for r in field_map:
        if r["profile"] != prof or not r["name"] or r["status"] != "present":
            continue
        if r["role"] == "provenance_candidate" and r.get("depends_on", "") != "confirmed":
            continue
        if r["name"] not in keys:
            keys.append(r["name"])
    return keys


def role_name(field_map, prof, role):
    for r in field_map:
        if r["profile"] == prof and r["role"] == role and r["status"] == "present" and r["name"]:
            return r["name"]
    return None


# ---------------------------------------------------------------- record sets and responses (§4.3)

def recset(series, schema, a, b, extra=None):
    """series[...][...] in the real primekey order; the time key gets an inclusive DRMS range, others are open."""
    tk = time_key(schema)
    if tk is None:
        raise TechnicalError(f"{series}: no time primekey in the schema")
    parts = []
    for k in schema["primekeys"]:
        if k == tk:
            parts.append(f"[{tai_str(a)}-{tai_str(b)}]")
        elif extra and k in extra:
            parts.append(f"[{extra[k]}]")
        else:
            parts.append("[]")
    return series + "".join(parts)


def rows_from_rs_list(js):
    """rs_list JSON -> list of dicts of original strings; consistency of the lengths is checked."""
    kws = js.get("keywords")
    if not isinstance(kws, list):
        raise TechnicalError("rs_list without a keywords list")
    cols = {}
    for k in kws:
        vals = k.get("values")
        if not isinstance(vals, list):
            raise TechnicalError(f"rs_list keyword {k.get('name')!r} without values")
        cols[k.get("name")] = vals
    lens = {len(v) for v in cols.values()}
    if len(lens) > 1:
        raise TechnicalError("rs_list keyword columns of different lengths")
    n = lens.pop() if lens else 0
    cnt = js.get("count")
    if cnt is not None and int(cnt) != n:
        raise TechnicalError(f"rs_list count {cnt} differs from the {n} rows received")
    return [{name: (None if v[i] is None else str(v[i])) for name, v in cols.items()} for i in range(n)]


def filter_window(rows, tk, a, b):
    """Half-open local filter on the time key; returns kept, edge rows (t >= b or < a), unparsable."""
    kept, edge, bad = [], [], []
    for r in rows:
        t, st = parse_time(r.get(tk))
        if t is None:
            bad.append((r, st))
        elif a <= t < b:
            kept.append(r)
        else:
            edge.append(r)
    return kept, edge, bad


def identity(series, schema, r):
    return (series,) + tuple(str(r.get(k)) for k in schema["primekeys"])


# ---------------------------------------------------------------- run directory, guards and phases

class Run:
    def __init__(self, run_id, raw_base=RAW_BASE, res_base=RES_BASE):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", run_id):
            raise TechnicalError("run id must be 1-64 characters [A-Za-z0-9_.-]")
        self.id = run_id
        self.raw = Path(raw_base) / run_id
        self.res = Path(res_base) / run_id
        self.raw.mkdir(parents=True, exist_ok=True)

    def p(self, name):
        return self.raw / name

    def schemas(self):
        out = {}
        for s in SERIES:
            f = self.p(f"SCHEMA_{s}.json")
            if f.exists():
                out[s] = parse_schema(json.loads(f.read_text()))
        return out


def git(*a):
    p = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise TechnicalError(f"git {' '.join(a)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def script_committed():
    """The running script must be tracked and identical to HEAD (untracked files escape 'git status')."""
    rel = str(Path(__file__).resolve().relative_to(ROOT))
    p = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        return False
    return subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT).returncode == 0


def t5_running():
    p = subprocess.run(["pgrep", "-f", "t5_power_sensitivity.py --run"], capture_output=True, text=True)
    return p.returncode == 0 and p.stdout.strip() != ""


def check_plan():
    if sha_file(PLAN) != SHA_PLAN:
        raise TechnicalError("frozen plan SHA-256 differs")
    fr = json.loads(FREEZE.read_text())
    if fr.get("plan_sha256") != SHA_PLAN:
        raise TechnicalError("freeze receipt SHA-256 differs from the plan")
    return fr


def network_guard():
    """§4: no network before the end of the T5 grid, on a dirty tree or with a different plan."""
    check_plan()
    if git("status", "--porcelain", "--untracked-files=no"):
        raise TechnicalError("tracked tree not clean")
    if not script_committed():
        raise TechnicalError("collector script not committed")
    if t5_running():
        raise TechnicalError("T5 grid still running: network refused")
    if not T5_META.exists():
        raise TechnicalError("T5 grid META.json missing: network refused (content not read)")


@contextlib.contextmanager
def lock(run):
    f = run.p("LOCK")
    try:
        fd = os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise TechnicalError(f"another instance holds {f}") from None
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(f)


def provenance():
    import drms
    import astropy
    return dict(git_commit=git("rev-parse", "HEAD"), git_dirty=0, plan_sha256=SHA_PLAN,
                freeze_commit=json.loads(FREEZE.read_text()).get("freeze_commit"),
                script_sha256=sha_file(__file__),
                env=dict(python=platform.python_version(), drms=drms.__version__, astropy=astropy.__version__))


def registered_map(run):
    reg = run.p("FIELD_MAP_REGISTRATION.json")
    fm = run.p("FIELD_MAP.csv")
    if not (reg.exists() and fm.exists()):
        raise TechnicalError("field map not registered: record queries refused (§3)")
    r = json.loads(reg.read_text())
    if r.get("field_map_sha256") != sha_file(fm):
        raise TechnicalError("FIELD_MAP.csv differs from its registration")
    rules = run.p("PRODUCT_RULES.json")
    if rules.exists() and r.get("product_rules_sha256") != sha_file(rules):
        raise TechnicalError("PRODUCT_RULES.json differs from its registration")
    return read_csv(fm), (json.loads(rules.read_text()) if rules.exists() else {})


def phase_schema(run, tr):
    for s in SERIES:
        js, fname = tr.get({"op": "series_struct", "ds": s}, f"schema_{s}")
        atomic_write(run.p(f"SCHEMA_{s}.json"), json.dumps(js, indent=1, sort_keys=True).encode())
    rows = propose_field_map(run.schemas())
    write_csv(run.p("FIELD_MAP_PROPOSED.csv"), rows, FIELD_COLS)
    return dict(n_schemas=len(run.schemas()), field_map_proposed_sha256=sha_file(run.p("FIELD_MAP_PROPOSED.csv")))


def register_map(run, verified_by):
    """Offline: the reviewer edits FIELD_MAP.csv (copied from the proposal) and its SHA-256 is registered."""
    fm = run.p("FIELD_MAP.csv")
    if not fm.exists():
        raise TechnicalError("copy FIELD_MAP_PROPOSED.csv to FIELD_MAP.csv and verify it first")
    rows = read_csv(fm)
    if not rows or set(rows[0]) != set(FIELD_COLS):
        raise TechnicalError("FIELD_MAP.csv columns differ from the expected ones")
    out = dict(field_map_sha256=sha_file(fm), verified_by=verified_by, registered_utc=now_utc(),
               plan_sha256=SHA_PLAN)
    rules = run.p("PRODUCT_RULES.json")
    if rules.exists():
        json.loads(rules.read_text())
        out["product_rules_sha256"] = sha_file(rules)
    reg = run.p("FIELD_MAP_REGISTRATION.json")
    if reg.exists():
        raise TechnicalError("field map already registered: a change needs a new run id")
    write_json(reg, out)
    return out


def count_window(tr, series, schema, a, b, tag, aux=False):
    t0 = time.monotonic()
    js, fname = tr.get({"op": "rs_summary", "ds": recset(series, schema, a, b)}, tag, aux=aux)
    c = js.get("count")
    try:
        c = int(c)
    except (TypeError, ValueError):
        raise TechnicalError(f"{tag}: rs_summary without an integer count ({c!r})") from None
    return c, time.monotonic() - t0, fname


def phase_counts(run, tr, schemas):
    """Counts only, overlap first, with deterministic splits above SPLIT_LIMIT (§4.2)."""
    leaves, tmax, used0 = [], 0.0, tr.reg.d["attempts"]
    stack = [(part, s, prof, a, b, lev) for part, s, prof, a, b, lev in initial_windows()]
    i = 0
    while i < len(stack):
        part, s, prof, a, b, lev = stack[i]
        i += 1
        c, dt, fname = count_window(tr, s, schemas[s], a, b, f"count_{s}_{tai_str(a)}")
        tmax = max(tmax, dt)
        if c > SPLIT_LIMIT:
            ch = split_window(a, b, lev)
            if not ch:
                leaves.append(dict(part=part, series=s, profile=prof, start=tai_str(a), end=tai_str(b), level=lev,
                                   count=c, status="too_large_minimal_block"))
                continue
            stack[i:i] = [(part, s, prof, x, y, l2) for x, y, l2 in ch]
            continue
        leaves.append(dict(part=part, series=s, profile=prof, start=tai_str(a), end=tai_str(b), level=lev, count=c,
                           status="ok"))
    write_csv(run.p("COUNT_LEAVES.csv"), leaves, ["part", "series", "profile", "start", "end", "level", "count",
                                                   "status"])
    return budget_counts(run, tr.reg, leaves, tmax, tr.reg.d["attempts"] - used0)


def budget_counts(run, reg, leaves, tmax, used_counts):
    too_large = [x for x in leaves if x["status"] != "ok"]
    rows = {p: sum(int(x["count"]) for x in leaves if x["part"] == p) for p in ("overlap", "history")}
    lists = {p: sum(1 for x in leaves if x["part"] == p and int(x["count"]) > 0 and x["status"] == "ok")
             for p in ("overlap", "history")}
    used = reg.d["attempts"]
    full = used + lists["overlap"] + lists["history"] + RESERVE_AUX + RESERVE_RETRY
    ov = used + lists["overlap"] + RESERVE_AUX + RESERVE_RETRY
    if too_large:
        decision = "overlap_only" if not any(x["part"] == "overlap" for x in too_large) and ov <= CAP_ATTEMPTS \
            and rows["overlap"] <= CAP_ROWS else "stop"
    elif full <= CAP_ATTEMPTS and rows["overlap"] + rows["history"] <= CAP_ROWS:
        decision = "full"
    elif ov <= CAP_ATTEMPTS and rows["overlap"] <= CAP_ROWS:
        decision = "overlap_only"
    else:
        decision = "stop"
    out = dict(attempts_used=used, count_attempts=used_counts, t_count_max_s=tmax, leaves=len(leaves),
               expected_rows=rows, lists_needed=lists, reserves=dict(aux=RESERVE_AUX, retry_split=RESERVE_RETRY),
               projected_attempts_full=full, projected_attempts_overlap=ov, too_large_blocks=len(too_large),
               decision=decision, history_status="not_started_budget" if decision != "full" else "allowed",
               caps=reg.caps, base_budget_table=base_budget())
    write_json(run.p("BUDGET_COUNTS.json"), out)
    return out


class Store:
    """Accepted rows per series with identity checks; edge and unparsable rows recorded separately."""

    def __init__(self, run, schemas):
        self.run, self.schemas = run, schemas
        self.ids = {}
        self.conflicts = []

    def accept(self, series, prof, window, rows, reg):
        sc = self.schemas[series]
        new, dup_same = [], 0
        for r in rows:
            key = identity(series, sc, r)
            if key in self.ids:
                if self.ids[key] != r:
                    self.conflicts.append(dict(series=series, identity="|".join(key[1:]), window=window))
                else:
                    dup_same += 1
                continue
            self.ids[key] = r
            new.append(r)
        if self.conflicts:
            raise TechnicalError(f"identity conflict in {series} ({len(self.conflicts)} so far)")
        reg.check("accept rows", n_rows=len(new))
        reg.add_rows(len(new))
        return new, dup_same


def list_leaf(tr, store, leaf, schemas, field_map, run, measure=None):
    s, prof = leaf["series"], leaf["profile"]
    sc = schemas[s]
    keys = profile_keys(field_map, prof)
    for k in sc["primekeys"]:
        if k not in keys:
            keys.insert(0, k)
    a, _ = parse_time(leaf["start"])
    b, _ = parse_time(leaf["end"])
    rs = recset(s, sc, a, b)
    tr.reg.check("list", n_rows=0)
    t0 = time.monotonic()
    b0 = tr.reg.d["bytes"]
    tag = f"list_{prof}_{leaf['start']}"
    js, fname = tr.get({"op": "rs_list", "ds": rs, "key": ",".join(keys)}, tag)
    rows = rows_from_rs_list(js)
    if len(rows) != int(leaf["count"]):
        # count and list on the same record set must agree
        raise TechnicalError(f"{tag}: count {leaf['count']} but list returned {len(rows)} rows")
    tk = time_key(sc)
    kept, edge, bad = filter_window(rows, tk, a, b)
    new, dup = store.accept(s, prof, f"{leaf['start']}/{leaf['end']}", kept, tr.reg)
    dt = time.monotonic() - t0
    path = run.p(f"RECORDS_{prof}.csv.gz")
    first = not path.exists()
    with gzip.open(path, "at", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if first:
            w.writerow(["window", "edge"] + keys)
        for r in new:
            w.writerow([f"{leaf['start']}/{leaf['end']}", 0] + [r.get(k) for k in keys])
        for r in edge:
            w.writerow([f"{leaf['start']}/{leaf['end']}", 1] + [r.get(k) for k in keys])
        for r, st in bad:
            w.writerow([f"{leaf['start']}/{leaf['end']}", f"unparsable_time:{st}"] + [r.get(k) for k in keys])
    rec = dict(window=f"{leaf['start']}/{leaf['end']}", series=s, profile=prof, count_server=int(leaf["count"]),
               received=len(rows), kept=len(kept), new=len(new), duplicates_same=dup, edge=len(edge), bad_time=len(bad),
               bytes=tr.reg.d["bytes"] - b0, seconds=dt, file=fname, status="complete")
    with open(run.p("LIST_RECEIPTS.jsonl"), "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    if measure is not None and prof not in measure and len(rows) > 0:
        measure[prof] = dict(bytes=rec["bytes"], rows=len(rows), seconds=dt, window=rec["window"])
    return rec


def done_windows(run):
    f = run.p("LIST_RECEIPTS.jsonl")
    if not f.exists():
        return set()
    return {(json.loads(x)["profile"], json.loads(x)["window"]) for x in f.read_text().splitlines() if x.strip()}


def restore_store(run, schemas):
    """On resume, rebuild accepted identities from saved records (never re-queried for a better answer)."""
    st = Store(run, schemas)
    for prof in PROFILES:
        path = run.p(f"RECORDS_{prof}.csv.gz")
        if not path.exists():
            continue
        s = PROFILE_SERIES[prof]
        with gzip.open(path, "rt", newline="") as f:
            rd = csv.DictReader(f)
            for r in rd:
                if r["edge"] != "0":
                    continue
                vals = {k: v for k, v in r.items() if k not in ("window", "edge")}
                st.ids[identity(s, schemas[s], vals)] = vals
    return st


def phase_lists(run, tr, schemas, field_map, part):
    bc = json.loads(run.p("BUDGET_COUNTS.json").read_text())
    if part == "overlap" and bc["decision"] == "stop":
        raise BudgetStop("BUDGET_COUNTS decision is 'stop'")
    if part == "history" and bc["decision"] != "full":
        raise BudgetStop(f"history not allowed by BUDGET_COUNTS ({bc['decision']})")
    leaves = [x for x in read_csv(run.p("COUNT_LEAVES.csv")) if x["part"] == part and x["status"] == "ok"
              and int(x["count"]) > 0]
    done = done_windows(run)
    store = restore_store(run, schemas)
    mfile = run.p("PROFILE_MEASURES.json")
    measure = json.loads(mfile.read_text()) if mfile.exists() else {}
    out = []
    if part == "history" and not run.p("BUDGET_PAYLOAD.json").exists():
        # first non-empty historical block of the minimal SMARP profile, then the payload projection (§4.2)
        first = next((x for x in leaves if x["profile"] == "smarp_min"), None)
        if first is not None and (first["profile"], f"{first['start']}/{first['end']}") not in done:
            out.append(list_leaf(tr, store, first, schemas, field_map, run, measure))
            write_json(mfile, measure)
            done = done_windows(run)
        bp = budget_payload(run, tr.reg, measure, bc)
        if not bp["within_caps"]:
            raise BudgetStop("payload projection exceeds the caps: history stopped, overlap kept")
    for leaf in leaves:
        if (leaf["profile"], f"{leaf['start']}/{leaf['end']}") in done:
            continue
        out.append(list_leaf(tr, store, leaf, schemas, field_map, run, measure))
        write_json(mfile, measure)
    return dict(lists=len(out), rows_new=sum(x["new"] for x in out))


def budget_payload(run, reg, measure, bc):
    """§4.2: bytes_used + 2 * sum_p (b_p/N_p) N_rest,p and T_used + 2 sum_p (t_p/N_p) N_rest,p + R_rest (1 s + t_c)."""
    leaves = [x for x in read_csv(run.p("COUNT_LEAVES.csv")) if x["status"] == "ok" and int(x["count"]) > 0]
    done = done_windows(run)
    rest = [x for x in leaves if (x["profile"], f"{x['start']}/{x['end']}") not in done]
    n_rest = {p: sum(int(x["count"]) for x in rest if x["profile"] == p) for p in PROFILES}
    missing = [p for p in PROFILES if n_rest[p] > 0 and p not in measure]
    b_proj = reg.d["bytes"] + 2 * sum(measure[p]["bytes"] / measure[p]["rows"] * n_rest[p]
                                      for p in PROFILES if n_rest[p] > 0 and p in measure)
    t_proj = reg.used_wall() + 2 * sum(measure[p]["seconds"] / measure[p]["rows"] * n_rest[p]
                                       for p in PROFILES if n_rest[p] > 0 and p in measure) \
        + len(rest) * (MIN_SPACING + bc["t_count_max_s"])
    r_proj = reg.d["attempts"] + len(rest)
    rows_proj = reg.d["rows"] + sum(n_rest.values())
    ok = (not missing and b_proj <= reg.caps["bytes"] and t_proj <= reg.caps["wall_s"]
          and r_proj <= reg.caps["attempts"] and rows_proj <= reg.caps["rows"])
    out = dict(bytes_used=reg.d["bytes"], wall_used_s=reg.used_wall(), attempts_used=reg.d["attempts"],
               rows_used=reg.d["rows"], measures=measure, rows_remaining=n_rest, requests_remaining=len(rest),
               t_count_max_s=bc["t_count_max_s"], projected_bytes=b_proj, projected_wall_s=t_proj,
               projected_attempts=r_proj, projected_rows=rows_proj, unmeasured_profiles=missing, factor=2,
               within_caps=bool(ok))
    write_json(run.p("BUDGET_PAYLOAD.json"), out)
    return out


def phase_aux(run, tr, schemas, rules):
    """Grouped lookups of documented sources (§4.3); only if PRODUCT_RULES declares a lookup."""
    lk = (rules or {}).get("smarp_source_lookup")
    if not lk:
        write_json(run.p("AUX_STATUS.json"), dict(status="not_needed_or_not_documented"))
        return dict(status="not_needed_or_not_documented")
    series, key_tarp, key_t = lk["series"], lk.get("tarp_key", "TARPNUM"), lk.get("time_key", "T_REC")
    if series not in SERIES:
        raise TechnicalError("lookup series not allowed")
    keys = lk["keywords"]
    recs = []
    for prof in ("smarp_overlap", "smarp_min"):
        path = run.p(f"RECORDS_{prof}.csv.gz")
        if path.exists():
            with gzip.open(path, "rt", newline="") as f:
                recs += [(prof, r) for r in csv.DictReader(f) if r["edge"] == "0"]
    groups = {}
    for prof, r in recs:
        groups.setdefault(r[key_tarp], []).append(r[key_t])
    out, cache = [], {}
    for tarp in sorted(groups, key=lambda x: (len(x), x)):
        times = sorted(set(groups[tarp]))
        for i in range(0, len(times), AUX_BATCH):
            if tr.reg.d["aux_attempts"] + 1 > RESERVE_AUX:
                write_json(run.p("AUX_STATUS.json"), dict(status="unknown_budget", done=len(out)))
                return dict(status="unknown_budget", done=len(out))
            batch = times[i:i + AUX_BATCH]
            ds = f"{series}[{tarp}][{','.join(batch)}]"
            js, fname = tr.get({"op": "rs_list", "ds": ds, "key": ",".join([key_tarp, key_t] + keys)},
                               f"aux_{tarp}_{i}", aux=True)
            for r in rows_from_rs_list(js):
                cache[(r.get(key_tarp), r.get(key_t))] = r
            out.append(dict(tarp=tarp, n=len(batch), file=fname))
    with gzip.open(run.p("AUX_RECORDS.csv.gz"), "wt", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([key_tarp, key_t] + keys)
        for (tp, t), r in sorted(cache.items()):
            w.writerow([tp, t] + [r.get(k) for k in keys])
    write_json(run.p("AUX_STATUS.json"), dict(status="complete", requests=len(out)))
    return dict(status="complete", requests=len(out))


def phase_continuum(run, tr, schemas):
    sc = schemas.get(IC)
    if sc is None:
        return dict(status="schema_not_verified")
    rows = []
    for a, b in years(T0, T1):
        c, dt, fname = count_window(tr, IC, sc, a, b, f"count_{IC}_{a.year}")
        rows.append(dict(year=a.year, start=tai_str(a), end=tai_str(b), count=c))
    write_csv(run.p("CONTINUUM_COUNTS.csv"), rows, ["year", "start", "end", "count"])
    return dict(status="complete", years=len(rows))


def run_phase(args):
    run = Run(args.run_id)
    network_guard()
    reg = Registry(run.p("REGISTRY.json"))
    tr = Transport(reg, run.p("raw"))
    meta = dict(phase=args.phase, outcome="non riuscito", start_utc=now_utc())
    code = 1
    with lock(run):
        try:
            meta.update(provenance())
            schemas = run.schemas()
            if args.phase == "schema":
                meta["result"] = phase_schema(run, tr)
            else:
                field_map, rules = registered_map(run)
                for s in (SMARP, FD, HMI):
                    if s not in schemas:
                        raise TechnicalError(f"schema of {s} not acquired")
                if args.phase == "counts":
                    meta["result"] = phase_counts(run, tr, schemas)
                elif args.phase in ("overlap", "history"):
                    meta["result"] = phase_lists(run, tr, schemas, field_map, args.phase)
                elif args.phase == "aux":
                    meta["result"] = phase_aux(run, tr, schemas, rules)
                elif args.phase == "continuum":
                    meta["result"] = phase_continuum(run, tr, schemas)
            meta["outcome"] = "eseguita"
            code = 0
        except BudgetStop as exc:
            meta.update(outcome="parziale: tetto o preventivo", reason=str(exc))
            code = 3
        except (RequestFailed, TechnicalError) as exc:
            meta.update(outcome="parziale: errore", exception_type=type(exc).__name__, reason=str(exc))
            code = 1
        except Exception as exc:                  # noqa: BLE001
            meta.update(outcome="errore tecnico", exception_type=type(exc).__name__, reason=str(exc),
                        traceback=traceback.format_exc())
            code = 1
        finally:
            reg.close(args.phase, meta["outcome"])
            meta.update(end_utc=now_utc(), registry=dict((k, reg.d[k]) for k in ("attempts", "aux_attempts", "bytes",
                                                                                 "rows", "wall_s_completed")))
            write_json(run.p(f"PHASE_{args.phase}_{len(reg.d['invocations']):03d}.json"), meta)
            print(json.dumps({k: meta.get(k) for k in ("phase", "outcome", "reason", "registry")}, default=str))
    return code


# ---------------------------------------------------------------- analysis (§5, §6), offline

def great_circle(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h))))


GEOM_ROLES = ("naxis1", "naxis2", "crpix1", "crpix2", "crval1", "crval2", "cdelt1", "cdelt2", "ctype1", "ctype2",
              "cunit1", "cunit2", "crota2", "pc1_1", "pc1_2", "pc2_1", "pc2_2", "pv2_1")
FITS_NAME = {"naxis1": "NAXIS1", "naxis2": "NAXIS2", "crpix1": "CRPIX1", "crpix2": "CRPIX2", "crval1": "CRVAL1",
             "crval2": "CRVAL2", "cdelt1": "CDELT1", "cdelt2": "CDELT2", "ctype1": "CTYPE1", "ctype2": "CTYPE2",
             "cunit1": "CUNIT1", "cunit2": "CUNIT2", "crota2": "CROTA2", "pc1_1": "PC1_1", "pc1_2": "PC1_2",
             "pc2_1": "PC2_1", "pc2_2": "PC2_2", "pv2_1": "PV2_1"}
REQUIRED_GEOM = ("naxis1", "naxis2", "crpix1", "crpix2", "crval1", "crval2", "cdelt1", "cdelt2", "ctype1", "ctype2")


def wcs_from(vals):
    """Header dict -> astropy WCS (CRPIX kept with FITS origin 1); None with reason if not assessable."""
    from astropy.wcs import WCS
    hdr = {}
    for role in GEOM_ROLES:
        v = vals.get(role)
        if v is None or str(v).strip() == "":
            if role in REQUIRED_GEOM:
                return None, None, f"missing {FITS_NAME[role]}"
            continue
        if role.startswith(("ctype", "cunit")):
            hdr[FITS_NAME[role]] = str(v).strip()
        else:
            f, st = to_float(v)
            if f is None:
                return None, None, f"{FITS_NAME[role]} {st}"
            hdr[FITS_NAME[role]] = f
    nx, ny = int(hdr.pop("NAXIS1")), int(hdr.pop("NAXIS2"))
    if nx <= 0 or ny <= 0:
        return None, None, "non-positive NAXIS"
    hdr.update(NAXIS=2, NAXIS1=nx, NAXIS2=ny)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            w = WCS(hdr)
        if not w.has_celestial:
            return None, None, "WCS without a celestial pair"
    except Exception as exc:                      # noqa: BLE001
        return None, None, f"WCS error {type(exc).__name__}"
    return w, (nx, ny), "ok"


def center_lonlat(w, shape):
    """Centre ((nx-1)/2, (ny-1)/2) with pixel origin 0; equivalence check with origin 1 (§6.2)."""
    nx, ny = shape
    lon, lat = w.wcs_pix2world([[(nx - 1) / 2, (ny - 1) / 2]], 0)[0]
    lon1, lat1 = w.wcs_pix2world([[(nx - 1) / 2 + 1, (ny - 1) / 2 + 1]], 1)[0]
    if not (math.isfinite(lon) and math.isfinite(lat)):
        return None, "non-finite centre"
    if great_circle(lon, lat, lon1, lat1) > 1e-10:
        raise TechnicalError("pixel-origin equivalence failed")
    return (lon % 360.0, lat), "ok"


def envelope(w, shape, center_lon):
    """Approximate lon/lat envelope from EDGE_POINTS per side of the outer pixel boundary (§6.2)."""
    nx, ny = shape
    xs = [-0.5 + (nx) * i / (EDGE_POINTS - 1) for i in range(EDGE_POINTS)]
    ys = [-0.5 + (ny) * i / (EDGE_POINTS - 1) for i in range(EDGE_POINTS)]
    pts = [(x, -0.5) for x in xs] + [(x, ny - 0.5) for x in xs] + [(-0.5, y) for y in ys] + [(nx - 0.5, y) for y in ys]
    out = w.wcs_pix2world(pts, 0)
    lons, lats = [], []
    for lo, la in out:
        if not (math.isfinite(lo) and math.isfinite(la)):
            return None, "non-finite boundary point"
        lons.append(center_lon + ((lo - center_lon + 180.0) % 360.0 - 180.0))
        lats.append(la)
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    if lo1 - lo0 >= 180.0:
        return None, "longitude width >= 180"
    return (lo0, lo1, la0, la1), "ok"


def sph_area(lo0, lo1, la0, la1):
    return max(0.0, math.radians(lo1 - lo0)) * max(0.0, math.sin(math.radians(la1)) - math.sin(math.radians(la0)))


def envelope_overlap(e1, e2):
    """Intersection on the circle of longitudes (shifts of 360) and in latitude; fractions and IoU."""
    a1, a2 = sph_area(*e1), sph_area(*e2)
    la0, la1 = max(e1[2], e2[2]), min(e1[3], e2[3])
    best = 0.0
    for sh in (-360.0, 0.0, 360.0):
        lo0, lo1 = max(e1[0], e2[0] + sh), min(e1[1], e2[1] + sh)
        if lo1 > lo0 and la1 > la0:
            best = max(best, sph_area(lo0, lo1, la0, la1))
    union = a1 + a2 - best
    return dict(inter=best, frac1=best / a1 if a1 > 0 else None, frac2=best / a2 if a2 > 0 else None,
                iou=best / union if union > 0 else None)


def geom_of(rec, fmap, prof):
    vals = {r: rec.get(role_name(fmap, prof, r)) if role_name(fmap, prof, r) else None for r in GEOM_ROLES}
    w, shape, why = wcs_from(vals)
    if w is None:
        return dict(status="not_assessable", reason=why)
    c, why = center_lonlat(w, shape)
    if c is None:
        return dict(status="not_assessable", reason=why)
    env, why_e = envelope(w, shape, c[0])
    return dict(status="ok", lon=c[0], lat=c[1], env=env, env_reason=why_e)


def match_overlap(smarp, hmi, fmap):
    """§6.1-6.3: nearest HMI record per HARPNUM within 360 s; G5/G10 degrees; completeness; box_only."""
    by_time = {}
    for h in hmi:
        by_time.setdefault(h["HARPNUM"], []).append(h)
    for v in by_time.values():
        v.sort(key=lambda r: r["_t"])
    pairs = []
    for s in smarp:
        for harp, lst in by_time.items():
            best = None
            for h in lst:
                d = abs((h["_t"] - s["_t"]).total_seconds())
                if d <= TIME_TOL_S and (best is None or d < best[0] or (d == best[0] and h["_t"] < best[1]["_t"])):
                    best = (d, h)
            if best is not None:
                pairs.append(dict(s=s, h=best[1], dt=(best[1]["_t"] - s["_t"]).total_seconds()))
    for p in pairs:
        gs, gh = p["s"]["_geom"], p["h"]["_geom"]
        if gs["status"] == "ok" and gh["status"] == "ok":
            p["dist"] = great_circle(gs["lon"], gs["lat"], gh["lon"], gh["lat"])
            p["ov"] = envelope_overlap(gs["env"], gh["env"]) if gs["env"] and gh["env"] else None
        else:
            p["dist"], p["ov"] = None, None
    graphs = {}
    for R in RADII:
        arcs = [p for p in pairs if p["dist"] is not None and p["dist"] <= R]
        deg_s, deg_h = {}, {}
        for p in arcs:
            deg_s[p["s"]["_id"]] = deg_s.get(p["s"]["_id"], 0) + 1
            deg_h[p["h"]["_id"]] = deg_h.get(p["h"]["_id"], 0) + 1
        graphs[R] = dict(arcs=arcs, deg_s=deg_s, deg_h=deg_h)
    rows = []
    for p in pairs:
        r = dict(smarp_id=p["s"]["_id"], hmi_id=p["h"]["_id"], TARPNUM=p["s"].get("TARPNUM"), HARPNUM=p["h"]["HARPNUM"],
                 dt_s=p["dt"], dist_deg=p["dist"], smarp_geom=p["s"]["_geom"]["status"], hmi_geom=p["h"]["_geom"]["status"],
                 iou=(p["ov"] or {}).get("iou"), inter_sr=(p["ov"] or {}).get("inter"))
        for R in RADII:
            g = graphs[R]
            inn = p["dist"] is not None and p["dist"] <= R
            r[f"in_G{int(R)}"] = int(inn)
            r[f"unique_in_G{int(R)}"] = int(inn and g["deg_s"][p["s"]["_id"]] == 1 and g["deg_h"][p["h"]["_id"]] == 1)
        r["ambiguous_on_widening"] = int(r["unique_in_G5"] == 1 and r["unique_in_G10"] == 0)
        r["box_only"] = int(p["dist"] is not None and p["dist"] > 10.0 and (p["ov"] or {}).get("inter", 0) > 0)
        rows.append(r)
    states = []
    for s in smarp:
        cand = [p for p in pairs if p["s"]["_id"] == s["_id"]]
        n_na = sum(1 for p in cand if p["h"]["_geom"]["status"] != "ok")
        st = {"smarp_id": s["_id"], "n_temporal_candidates": len(cand), "n_temporal_not_assessable": n_na}
        for R in RADII:
            if s["_geom"]["status"] != "ok":
                st[f"state_G{int(R)}"] = "not_assessable"
            else:
                st[f"state_G{int(R)}"] = "has_candidate" if graphs[R]["deg_s"].get(s["_id"], 0) else "no_candidate"
        st["geometry_complete_competitors"] = int(n_na == 0)
        states.append(st)
    comps = {}
    for R in RADII:
        parent = {}

        def find(x):
            while parent.setdefault(x, x) != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        for p in graphs[R]["arcs"]:
            a, b = find(("T", p["s"].get("TARPNUM"))), find(("H", p["h"]["HARPNUM"]))
            if a != b:
                parent[a] = b
        roots = {find(x) for x in list(parent)}
        comps[R] = len(roots)
    return rows, states, comps


def load_records(run, prof, fmap):
    path = run.p(f"RECORDS_{prof}.csv.gz")
    if not path.exists():
        return []
    s = PROFILE_SERIES[prof]
    sc = run.schemas()[s]
    tk = time_key(sc)
    out = []
    with gzip.open(path, "rt", newline="") as f:
        for r in csv.DictReader(f):
            r = dict(r)
            r["_t"], r["_tstatus"] = parse_time(r.get(tk))
            r["_id"] = "|".join(str(r.get(k)) for k in sc["primekeys"])
            out.append(r)
    return out


def analyze(run):
    fmap, rules = registered_map(run)
    run.res.mkdir(parents=True, exist_ok=True)
    checks = []

    def chk(name, ok, value=""):
        checks.append(dict(check=name, passed=bool(ok), value=value))
    receipts = [json.loads(x) for x in run.p("LIST_RECEIPTS.jsonl").read_text().splitlines()] \
        if run.p("LIST_RECEIPTS.jsonl").exists() else []
    chk("every listed window: count_server = received", all(r["count_server"] == r["received"] for r in receipts),
        f"{len(receipts)} windows")
    # coverage per series/profile and month
    cov = []
    for prof in PROFILES:
        recs = [r for r in load_records(run, prof, fmap) if r["edge"] == "0"]
        if not recs:
            continue
        keyp = "TARPNUM" if prof.startswith("smarp") else ("HARPNUM" if prof == "hmi_overlap" else None)
        months_ = {}
        for r in recs:
            if r["_t"] is None:
                continue
            m = r["_t"].strftime("%Y-%m")
            months_.setdefault(m, []).append(r)
        for m, lst in sorted(months_.items()):
            margin = sum(1 for r in lst if prof == "hmi_overlap" and not (OV0 <= r["_t"] < OV1))
            cov.append(dict(profile=prof, series=PROFILE_SERIES[prof], month=m, records=len(lst),
                            records_margin=margin, distinct_times=len({r["_t"] for r in lst}),
                            distinct_patches=len({r.get(keyp) for r in lst}) if keyp else "",
                            first=min(r["_t"] for r in lst).isoformat(), last=max(r["_t"] for r in lst).isoformat()))
    write_csv(run.res / "COVERAGE_MONTHLY.csv", cov, ["profile", "series", "month", "records", "records_margin",
                                                      "distinct_times", "distinct_patches", "first", "last"])
    # full-disk gaps on the native grid if epoch/step are documented
    sc = run.schemas()[FD]
    info = sc["primekeyinfo"].get(time_key(sc), {})
    gaps = []
    fd = sorted({r["_t"] for r in load_records(run, "fd_min", fmap) if r["edge"] == "0" and r["_t"]})
    step = parse_step(info.get("step"))
    epoch, _ = parse_time(info.get("epoch")) if info.get("epoch") else (None, "missing")
    if fd and step and epoch:
        present = set(fd)
        complete = {(r["window"]) for r in receipts if r["profile"] == "fd_min" and r["status"] == "complete"}
        for wdw in sorted(complete):
            a, _ = parse_time(wdw.split("/")[0])
            b, _ = parse_time(wdw.split("/")[1])
            k0 = math.ceil((a - epoch).total_seconds() / step)
            t = epoch + timedelta(seconds=k0 * step)
            run_start, n = None, 0
            while t < b:
                if t not in present:
                    run_start = run_start or t
                    n += 1
                elif run_start is not None:
                    gaps.append(dict(start=run_start.isoformat(), slots=n, hours=n * step / 3600, window=wdw))
                    run_start, n = None, 0
                t += timedelta(seconds=step)
            if run_start is not None:
                gaps.append(dict(start=run_start.isoformat(), slots=n, hours=n * step / 3600, window=wdw))
        chk("full-disk gaps on the documented native grid", True, f"step {step} s, {len(gaps)} gap runs")
    else:
        chk("full-disk native grid documented (epoch and step)", False, "gaps reported only as observed intervals")
        for t0_, t1_ in zip(fd, fd[1:]):
            gaps.append(dict(start=t0_.isoformat(), slots="", hours=(t1_ - t0_).total_seconds() / 3600, window="observed"))
    write_csv(run.res / "GAPS.csv", gaps, ["start", "slots", "hours", "window"])
    # quality
    qrows = []
    for prof in PROFILES:
        qn = role_name(fmap, prof, "quality")
        recs = [r for r in load_records(run, prof, fmap) if r["edge"] == "0"]
        dist = {}
        for r in recs:
            v, hx, st = parse_quality(r.get(qn)) if qn else (None, "", "not_exposed")
            dist[(st, hx)] = dist.get((st, hx), 0) + 1
        for (st, hx), n in sorted(dist.items()):
            qrows.append(dict(profile=prof, status=st, quality_hex=hx, n=n))
    write_csv(run.res / "QUALITY_SUMMARY.csv", qrows, ["profile", "status", "quality_hex", "n"])
    # products 1/5 min (§5.3)
    prows = product_states(run, fmap, rules)
    write_csv(run.res / "PRODUCT_SUMMARY.csv", prows, ["level", "state", "reason", "n"])
    # overlap (§6)
    sm = [r for r in load_records(run, "smarp_overlap", fmap) if r["edge"] == "0" and r["_t"]]
    hm = [r for r in load_records(run, "hmi_overlap", fmap) if r["edge"] == "0" and r["_t"]]
    for r in sm:
        r["_geom"] = geom_of(r, fmap, "smarp_overlap")
    for r in hm:
        r["_geom"] = geom_of(r, fmap, "hmi_overlap")
    rows, states, comps = match_overlap([r for r in sm if OV0 <= r["_t"] < OV1], hm, fmap)
    with gzip.open(run.res / "OVERLAP_CANDIDATES.csv.gz", "wt", newline="") as f:
        cols = list(rows[0]) if rows else ["smarp_id"]
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summ = dict(smarp_records=len(states), temporal_pairs=len(rows), components_G5=comps[5.0], components_G10=comps[10.0])
    for R in RADII:
        k = f"state_G{int(R)}"
        for stt in ("has_candidate", "no_candidate", "not_assessable"):
            summ[f"{k}_{stt}"] = sum(1 for s in states if s[k] == stt)
        summ[f"arcs_G{int(R)}"] = sum(r[f"in_G{int(R)}"] for r in rows)
        summ[f"unique_G{int(R)}"] = sum(r[f"unique_in_G{int(R)}"] for r in rows)
        summ[f"distinct_pairs_G{int(R)}"] = len({(r["TARPNUM"], r["HARPNUM"]) for r in rows if r[f"in_G{int(R)}"]})
    summ["ambiguous_on_widening"] = sum(r["ambiguous_on_widening"] for r in rows)
    summ["box_only"] = sum(r["box_only"] for r in rows)
    summ["records_with_incomplete_geometry_competitors"] = sum(1 for s in states if not s["geometry_complete_competitors"])
    dts = [abs(r["dt_s"]) for r in rows]
    summ["abs_dt_zero"] = sum(1 for d in dts if d == 0)
    summ["abs_dt_max"] = max(dts) if dts else None
    write_json(run.res / "OVERLAP_SUMMARY.json", summ)
    chk("record states partition the SMARP overlap records", all(
        sum(summ[f"state_G{int(R)}_{x}"] for x in ("has_candidate", "no_candidate", "not_assessable")) == len(states)
        for R in RADII), str(len(states)))
    write_csv(run.res / "CHECKS.csv", checks, ["check", "passed", "value"])
    prov = provenance()
    prov.update(field_map_sha256=sha_file(run.p("FIELD_MAP.csv")), registry=json.loads(run.p("REGISTRY.json").read_text())
                if run.p("REGISTRY.json").exists() else None)
    write_json(run.res / "PROVENANCE.json", prov)
    return dict(checks=len(checks), passed=sum(c["passed"] for c in checks), overlap=summ)


def parse_step(s):
    if s is None:
        return None
    m = re.fullmatch(r"\s*([0-9.]+)\s*([smhd]?)\s*", str(s))
    if not m:
        return None
    v = float(m.group(1))
    return v * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]


def product_states(run, fmap, rules):
    """documented_1min / documented_5min / unknown / conflict with reasons, per source epoch and per patch."""
    rule = (rules or {}).get("fd_product")
    fd = [r for r in load_records(run, "fd_min", fmap) if r["edge"] == "0"]
    fd_state = {}
    for r in fd:
        if not rule:
            fd_state[r["_id"]] = ("unknown", "not_documented")
            continue
        v = r.get(rule["keyword"])
        cls = rule["map"].get(str(v).strip()) if v is not None else None
        fd_state[r["_id"]] = (cls, "rule") if cls in ("documented_1min", "documented_5min") else ("unknown", "value_not_mapped")
    by_time = {}
    for r in fd:
        if r["_t"] is not None:
            by_time.setdefault(r["_t"], []).append(r["_id"])
    out = {}
    for rid, (stt, why) in fd_state.items():
        out[("source_epoch", stt, why)] = out.get(("source_epoch", stt, why), 0) + 1
    src = (rules or {}).get("smarp_source_time")
    for prof in ("smarp_overlap", "smarp_min"):
        for r in load_records(run, prof, fmap):
            if r["edge"] != "0":
                continue
            if not src:
                stt, why = "unknown", "source_not_documented"
            else:
                t, st = parse_time(r.get(src["keyword"]))
                cands = [i for tt, ids in by_time.items() if t and abs((tt - t).total_seconds()) <= SOURCE_TIME_TOL_S
                         for i in ids] if t else []
                if not cands:
                    stt, why = "unknown", "source_unresolved"
                else:
                    cl = {fd_state[i][0] for i in cands}
                    if len(cands) > 1 and len(cl) > 1:
                        stt, why = "conflict", "several_sources"
                    elif len(cands) > 1:
                        stt, why = "unknown", "source_not_unique"
                    else:
                        stt, why = fd_state[cands[0]][0], "time_link_1s"
            out[("patch_record", stt, why)] = out.get(("patch_record", stt, why), 0) + 1
    return [dict(level=k[0], state=k[1], reason=k[2], n=n) for k, n in sorted(out.items())]


# ---------------------------------------------------------------- selftest (§8), offline only

class FakeJSOC:
    """Local HTTP server answering jsoc_info with scripted behaviours (selftest only)."""

    def __init__(self):
        import http.server
        self.calls = []
        self.behaviour = {}
        outer = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                u = urlsplit(self.path)
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                outer.calls.append(q)
                ds = q.get("ds", "")
                beh = next((v for k, v in outer.behaviour.items() if k in ds), None)
                if beh is None:
                    beh = outer.default(q)
                kind = beh[0]
                if kind == "json":
                    body = json.dumps(beh[1]).encode()
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif kind == "status":
                    self.send_response(beh[1])
                    for hk, hv in (beh[2] if len(beh) > 2 else {}).items():
                        self.send_header(hk, hv)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif kind == "gzip":
                    body = gzip.compress(b'{"status":0,"count":1}')
                    self.send_response(200)
                    self.send_header("Content-Encoding", "gzip")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif kind == "drip":
                    self.send_response(200)
                    self.send_header("Content-Length", "100000")
                    self.end_headers()
                    try:
                        for _ in range(1000):
                            self.wfile.write(b" ")
                            self.wfile.flush()
                            time.sleep(0.05)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                elif kind == "big":
                    body = b'{"status":0,"x":"' + b"a" * beh[1] + b'"}'
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                        self.wfile.write(body)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.port = self.srv.server_address[1]
        self.th = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.th.start()

    catalog = None

    def default(self, q):
        if self.catalog is None:
            return ("json", {"status": 0, "count": 0})
        return ("json", self.catalog.answer(q))

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


def _transport(tmp, fake, caps=None, waits=(0.01, 0.02), path=None):
    reg = Registry(Path(path) if path else Path(tmp) / "REGISTRY.json", caps, min_spacing=0.0)
    return Transport(reg, Path(tmp) / "raw", scheme="http", host="127.0.0.1", port=fake.port, waits=waits), reg


def _raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return True
    return False


def synth_cea(lon0, lat0, nx, ny, dpx=0.03, crpix=None, ctype=("CRLN-CEA", "CRLT-CEA")):
    cp = crpix or ((nx + 1) / 2, (ny + 1) / 2)
    return dict(naxis1=nx, naxis2=ny, crpix1=cp[0], crpix2=cp[1], crval1=lon0, crval2=lat0, cdelt1=dpx, cdelt2=dpx,
                ctype1=ctype[0], ctype2=ctype[1], cunit1="deg", cunit2="deg")


def selftest_checks(ok):
    # windows and budget table
    bb = base_budget()
    ok("§4.2 base budget 356 + 30 + 52 + 15 + 15 = 468", bb["total"] == 468 and bb["smarp"] == 356 and bb["fd"] == 30
       and bb["hmi"] == 52, json.dumps(bb))
    w = initial_windows()
    ok("§4.3 order: overlap windows first (6 SMARP months, 26 HMI weeks, FD 2010), then history",
       [x[0] for x in w[:33]] == ["overlap"] * 33 and w[33][0] == "history"
       and sum(1 for x in w if x[2] == "smarp_overlap") == 6 and sum(1 for x in w if x[1] == HMI) == 26, "")
    hm = [x for x in w if x[1] == HMI]
    ok("§2/§6 HMI margins: first start 2010-04-30 23:54, last end 2010-10-29 00:06, consecutive <= 7 days",
       hm[0][3] == datetime(2010, 4, 30, 23, 54) and hm[-1][4] == datetime(2010, 10, 29, 0, 6)
       and all(x[4] - x[3] <= timedelta(days=7) for x in hm) and all(a[4] == b[3] for a, b in zip(hm, hm[1:])), "")
    sm = months(T0, T1)
    ok("windows: 178 SMARP months, last [2010-10-01, 2010-10-29); 15 FD years, last ends 2010-10-29",
       len(sm) == 178 and sm[-1] == (datetime(2010, 10, 1), datetime(2010, 10, 29)) and len(years(T0, T1)) == 15
       and years(T0, T1)[-1][1] == datetime(2010, 10, 29), "")
    ch = split_window(datetime(2001, 1, 1), datetime(2002, 1, 1), "year")
    ch2 = split_window(datetime(2001, 1, 1), datetime(2001, 2, 1), "month")
    ch3 = split_window(datetime(2001, 1, 1), datetime(2001, 1, 2), "day")
    ok("§4.2 deterministic splits: year->12 months, month->5 weeks (last 3 days), day->15 slots of 96 min",
       len(ch) == 12 and len(ch2) == 5 and ch2[-1][1] - ch2[-1][0] == timedelta(days=3) and len(ch3) == 15, "")
    # times
    t, st = parse_time("2010.05.01_00:00:00_TAI")
    t2, st2 = parse_time("2009.01.01_00:00:00_UTC")
    ok("TAI parsed as is; UTC converted with leap seconds (2009-01-01 UTC = +34 s TAI)",
       t == datetime(2010, 5, 1) and st == "ok" and t2 == datetime(2009, 1, 1, 0, 0, 34) and st2 == "ok_from_utc", "")
    ok("time without scale, invalid and missing are distinct states",
       parse_time("2010.05.01_00:00:00")[1] == "no_time_scale" and parse_time("garbage")[1] == "invalid"
       and parse_time("")[1] == "missing", "")
    sc = parse_schema(dict(primekeys=["TARPNUM", "T_REC"], keywords=[
        dict(name="TARPNUM", type="int"), dict(name="T_REC", type="time"),
        dict(name="T_REC_epoch", defval="1993.01.01_00:00:00_TAI"), dict(name="T_REC_step", defval="5760")]))
    ok("schema: primekey order kept, epoch/step from constants, record set in primekey order",
       sc["primekeys"] == ["TARPNUM", "T_REC"] and parse_step(sc["primekeyinfo"]["T_REC"]["step"]) == 5760.0
       and recset(SMARP, sc, datetime(2010, 5, 1), datetime(2010, 6, 1)) ==
       "mdi.smarp_cea_96m[][2010.05.01_00:00:00_TAI-2010.06.01_00:00:00_TAI]", "")
    ep, _ = parse_time("1993.01.01_00:00:00_TAI")
    ok("96 min = 8 x 12 min: epoch phase modulo 720 s computable", (datetime(2010, 5, 1) - ep).total_seconds() % 720 == 0
       and 5760 % 720 == 0, "")
    # half-open filter and edges
    rows = [{"T_REC": "2010.05.31_22:24:00_TAI"}, {"T_REC": "2010.06.01_00:00:00_TAI"}, {"T_REC": "bad"}]
    kept, edge, bad = filter_window(rows, "T_REC", datetime(2010, 5, 1), datetime(2010, 6, 1))
    ok("§4.3 half-open local filter: end-slot row kept as edge, unparsable time kept apart",
       len(kept) == 1 and len(edge) == 1 and len(bad) == 1, "")
    # rs_list parsing
    js = dict(status=0, count=2, keywords=[dict(name="T_REC", values=["a", "b"]), dict(name="QUALITY", values=["0", "x"])])
    ok("rs_list: columns to rows, original strings kept", rows_from_rs_list(js)[1] == {"T_REC": "b", "QUALITY": "x"}, "")
    ok("rs_list: count differing from rows -> technical error",
       _raises(lambda: rows_from_rs_list(dict(js, count=3)), TechnicalError), "")
    ok("rs_list: columns of different lengths -> technical error", _raises(lambda: rows_from_rs_list(dict(status=0, keywords=[
        dict(name="A", values=["1"]), dict(name="B", values=[])])), TechnicalError), "")
    # QUALITY
    ok("QUALITY: decimal, hex, signed, missing and invalid distinct; 32-bit normalized hex",
       parse_quality("0") == (0, "0x00000000", "ok") and parse_quality("0x80") == (128, "0x00000080", "ok")
       and parse_quality("-2147483648")[1] == "0x80000000" and parse_quality("")[2] == "missing"
       and parse_quality("abc")[2] == "invalid", "")
    # identity and duplicates
    with tempfile.TemporaryDirectory() as tmp:
        run = Run("t", raw_base=tmp, res_base=tmp)
        reg = Registry(Path(tmp) / "R.json")
        stx = Store(run, {SMARP: sc})
        new, dup = stx.accept(SMARP, "smarp_min", "w", [{"TARPNUM": "1", "T_REC": "x", "Q": "0"},
                                                         {"TARPNUM": "1", "T_REC": "x", "Q": "0"}], reg)
        ok("identity = series + all primekeys; identical duplicates counted, not kept twice", len(new) == 1 and dup == 1, "")
        ok("conflicting duplicate -> technical error (no keep-last)", _raises(lambda: stx.accept(
            SMARP, "smarp_min", "w2", [{"TARPNUM": "1", "T_REC": "x", "Q": "4"}], reg), TechnicalError), "")
    # transport against a local fake server
    fake = FakeJSOC()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tr, reg = _transport(tmp, fake)
            fake.behaviour = {"ZERO": ("json", {"status": 0, "count": 0}), "ERR": ("json", {"status": 4, "error": "bad"})}
            js, _ = tr.get({"op": "rs_summary", "ds": "ZERO"}, "z")
            ok("zero rows with a successful answer is a result (count 0)", js["count"] == 0, "")
            ok("DRMS error status is a failed request, not zero rows",
               _raises(lambda: tr.get({"op": "rs_summary", "ds": "ERR"}, "e"), RequestFailed), "")
            ok("export/download operations refused before any network use",
               _raises(lambda: tr.get({"op": "exp_request", "ds": "X"}, "x"), TechnicalError)
               and _raises(lambda: tr.url({"op": "jsoc_fetch"}), TechnicalError), "")
            fake.behaviour = {"GZ": ("gzip",)}
            ok("unexpected compression stopped without decompression",
               _raises(lambda: tr.get({"op": "rs_summary", "ds": "GZ"}, "g"), RequestFailed), "")
            n0 = reg.d["attempts"]
            fake.behaviour = {"S503": ("status", 503, {"Retry-After": "0"})}
            ok("retries: 3 attempts with waits, then failed; every attempt counted",
               _raises(lambda: tr.get({"op": "rs_summary", "ds": "S503"}, "r"), RequestFailed) and reg.d["attempts"] - n0 == 3, "")
            n0 = reg.d["attempts"]
            fake.behaviour = {"S404": ("status", 404)}
            ok("HTTP 404 not retried", _raises(lambda: tr.get({"op": "rs_summary", "ds": "S404"}, "n"), RequestFailed)
               and reg.d["attempts"] - n0 == 1, "")
            fake.behaviour = {"REDIR": ("status", 302, {"Location": "http://evil.example/cgi-bin/ajax/jsoc_info?op=rs_summary"})}
            ok("redirect to a non-allowed destination refused",
               _raises(lambda: tr.get({"op": "rs_summary", "ds": "REDIR"}, "rd"), RequestFailed), "")
            loc = f"http://127.0.0.1:{fake.port}{PATH}?op=rs_summary&ds=ZERO"
            fake.behaviour = {"GOOD_REDIR": ("status", 302, {"Location": loc}), "ZERO": ("json", {"status": 0, "count": 0})}
            n0 = reg.d["attempts"]
            js, _ = tr.get({"op": "rs_summary", "ds": "GOOD_REDIR"}, "gr")
            ok("allowed redirect followed once and counted as a new attempt", js["count"] == 0 and reg.d["attempts"] - n0 == 2, "")
            lines = (Path(tmp) / "raw" / "QUERY_LOG.jsonl").read_text().splitlines()
            ok("every attempt logged with SHA-256 and saved body", len(lines) == reg.d["attempts"]
               and all(json.loads(x)["sha256"] for x in lines), f"{len(lines)} attempts")
        with tempfile.TemporaryDirectory() as tmp:
            caps = dict(attempts=CAP_ATTEMPTS, rows=CAP_ROWS, bytes=CAP_BYTES, wall_s=2.0)
            tr, reg = _transport(tmp, fake, caps)
            fake.behaviour = {"DRIP": ("drip",)}
            t0 = time.monotonic()
            r = _raises(lambda: tr.get({"op": "rs_list", "ds": "DRIP", "key": "T_REC"}, "d"), BudgetStop)
            ok("slow but continuous sender stopped by the absolute deadline (not by the idle timeout)",
               r and time.monotonic() - t0 < 6.0, f"{time.monotonic() - t0:.1f} s")
        with tempfile.TemporaryDirectory() as tmp:
            caps = dict(attempts=CAP_ATTEMPTS, rows=CAP_ROWS, bytes=5000, wall_s=CAP_WALL_S)
            tr, reg = _transport(tmp, fake, caps)
            fake.behaviour = {"BIG": ("big", 20000)}
            r = _raises(lambda: tr.get({"op": "rs_list", "ds": "BIG", "key": "x"}, "b"), BudgetStop)
            body = [p for p in (Path(tmp) / "raw").glob("b_*.body")]
            ok("byte cap applied during reception: prefix kept, marked truncated, never more than the cap",
               r and reg.d["bytes"] == 5000 and body and body[0].stat().st_size == 5000
               and "truncated_by_budget" in (Path(tmp) / "raw" / "QUERY_LOG.jsonl").read_text(), "")
        with tempfile.TemporaryDirectory() as tmp:
            caps = dict(attempts=3, rows=CAP_ROWS, bytes=CAP_BYTES, wall_s=CAP_WALL_S)
            tr, reg = _transport(tmp, fake, caps)
            fake.behaviour = {"ZERO": ("json", {"status": 0, "count": 0})}
            for i in range(3):
                tr.get({"op": "rs_summary", "ds": "ZERO"}, f"c{i}")
            r = _raises(lambda: tr.get({"op": "rs_summary", "ds": "ZERO"}, "c4"), BudgetStop)
            reg.close("t", "x")
            reg2 = Registry(Path(tmp) / "REGISTRY.json", caps)
            ok("attempt cap enforced; counters survive a resume (not reset)", r and reg2.d["attempts"] == 3
               and _raises(lambda: reg2.check("x", n_attempts=1), BudgetStop), "")
        with tempfile.TemporaryDirectory() as tmp:
            reg = Registry(Path(tmp) / "R.json", dict(attempts=10, rows=5, bytes=10, wall_s=100))
            ok("row cap enforced before accepting rows", _raises(lambda: reg.check("rows", n_rows=6), BudgetStop), "")
            ok("registry with different caps refused", _raises(lambda: Registry(Path(tmp) / "R.json"), TechnicalError)
               if (reg.save() or True) else False, "")
    finally:
        fake.close()
    # budget decisions
    with tempfile.TemporaryDirectory() as tmp:
        run = Run("b", raw_base=tmp, res_base=tmp)
        reg = Registry(run.p("REGISTRY.json"))
        reg.d["attempts"] = 400
        leaves = [dict(part="overlap", series=SMARP, profile="smarp_overlap", start="", end="", level="month", count=10,
                       status="ok")] * 30 + [dict(part="history", series=SMARP, profile="smarp_min", start="", end="",
                                                  level="month", count=10, status="ok")] * 190
        bc = budget_counts(run, reg, leaves, 0.5, 400)
        ok("BUDGET_COUNTS: full does not fit (400 + 220 + 400 > 1000) -> overlap_only, history not started",
           bc["decision"] == "overlap_only" and bc["history_status"] == "not_started_budget", json.dumps(bc["projected_attempts_full"]))
        reg.d["attempts"] = 600
        ok("BUDGET_COUNTS: even overlap does not fit -> stop", budget_counts(run, reg, leaves, 0.5, 0)["decision"] == "stop", "")
        reg.d["attempts"] = 100
        ok("BUDGET_COUNTS: fits -> full", budget_counts(run, reg, leaves, 0.5, 0)["decision"] == "full", "")
        write_csv(run.p("COUNT_LEAVES.csv"), [dict(part="history", series=SMARP, profile="smarp_min", start="a", end="b",
                                                   level="month", count=1000, status="ok")],
                  ["part", "series", "profile", "start", "end", "level", "count", "status"])
        reg.d["bytes"] = 0
        bp = budget_payload(run, reg, {"smarp_min": dict(bytes=1000, rows=10, seconds=1.0)}, dict(t_count_max_s=0.5))
        ok("BUDGET_PAYLOAD: projected bytes = used + 2 x (b/N) x N_rest; time formula with latency term",
           bp["projected_bytes"] == 2 * 100 * 1000 and abs(bp["projected_wall_s"] - (reg.used_wall() + 2 * 0.1 * 1000 + 1.5)) < 0.5, "")
        bp2 = budget_payload(run, reg, {}, dict(t_count_max_s=0.5))
        ok("BUDGET_PAYLOAD: an unmeasured profile with remaining rows blocks the history", not bp2["within_caps"]
           and bp2["unmeasured_profiles"] == ["smarp_min"], "")
    # WCS geometry
    g = synth_cea(100.0, 0.0, 201, 101)
    wv, shape, why = wcs_from(g)
    c, _ = center_lonlat(wv, shape)
    ok("WCS CEA: centre of a patch with CRPIX at the centre equals CRVAL", why == "ok" and abs(c[0] - 100.0) < 1e-9
       and abs(c[1]) < 1e-9, "")
    g2 = synth_cea(100.0, 0.0, 201, 101, crpix=(1.0, 1.0))
    wv2, shape2, _ = wcs_from(g2)
    c2, _ = center_lonlat(wv2, shape2)
    lat_exp = math.degrees(math.asin(math.radians(0.03 * 50)))
    ok("WCS CEA: CRPIX far from the centre (FITS origin 1); centre analytic lon 100 + 0.03*100, lat asin(0.03*50 rad)",
       abs(c2[0] - 103.0) < 1e-9 and abs(c2[1] - lat_exp) < 1e-9, f"{c2[0]:.6f}, {c2[1]:.6f}")
    ok("WCS: missing CRPIX or non-numeric value -> not_assessable, never zero",
       wcs_from({k: v for k, v in g.items() if k != "crpix1"})[0] is None and wcs_from(dict(g, cdelt1="abc"))[0] is None, "")
    e1, _ = envelope(wv, shape, c[0])
    ok("envelope from 65 points per side: width 201*0.03 deg in longitude", abs((e1[1] - e1[0]) - 201 * 0.03) < 1e-9, "")
    ga = synth_cea(359.0, 0.0, 101, 101)
    gb = synth_cea(1.0, 0.0, 101, 101)
    wa, sa, _ = wcs_from(ga)
    wb, sb, _ = wcs_from(gb)
    ca, _ = center_lonlat(wa, sa)
    cb, _ = center_lonlat(wb, sb)
    ea, _ = envelope(wa, sa, ca[0])
    eb, _ = envelope(wb, sb, cb[0])
    ov = envelope_overlap(ea, eb)
    ok("longitudes across 0/360: distance 2 deg, envelopes overlap (width 3.03 deg each)",
       abs(great_circle(ca[0], ca[1], cb[0], cb[1]) - 2.0) < 1e-9 and ov["inter"] > 0 and 0 < ov["iou"] < 1, f"iou {ov['iou']:.3f}")
    far = synth_cea(200.0, 0.0, 101, 101)
    wf, sf, _ = wcs_from(far)
    ef, _ = envelope(wf, sf, center_lonlat(wf, sf)[0][0])
    ok("disjoint envelopes have zero intersection; contact has zero area", envelope_overlap(ea, ef)["inter"] == 0.0
       and envelope_overlap((0, 1, 0, 1), (1, 2, 0, 1))["inter"] == 0.0, "")
    # matching, graphs, uniqueness, completeness
    fmap = [dict(profile=p, series=PROFILE_SERIES[p], role=r, name=FITS_NAME[r], status="present", type="", unit="",
                 definition_ref="", normalization="", depends_on="") for p in ("smarp_overlap", "hmi_overlap") for r in GEOM_ROLES]

    def rec(idp, t, g_, **kw):
        r = {FITS_NAME[k]: str(v) for k, v in g_.items()} if g_ else {}
        r.update(kw)
        r["_t"], r["_id"] = t, idp
        return r
    t = datetime(2010, 6, 1, 1, 36)
    s1 = rec("S1", t, synth_cea(100.0, 10.0, 51, 51, 0.12), TARPNUM="1")
    h1 = rec("H1", t + timedelta(seconds=0), synth_cea(101.0, 10.0, 201, 201), HARPNUM="10")
    h1b = rec("H1b", t + timedelta(seconds=720), synth_cea(101.0, 10.0, 201, 201), HARPNUM="10")
    h2 = rec("H2", t - timedelta(seconds=360), synth_cea(107.0, 10.0, 201, 201), HARPNUM="20")
    h3 = rec("H3", t + timedelta(seconds=360), synth_cea(107.0, 10.0, 201, 201), HARPNUM="30")
    h4 = rec("H4", t, None, HARPNUM="40")
    for r in (s1, h1, h1b, h2, h3, h4):
        r["_geom"] = geom_of(r, fmap, "smarp_overlap" if r["_id"].startswith("S") else "hmi_overlap")
    rows, states, comps = match_overlap([s1], [h1, h1b, h2, h3, h4], fmap)
    by = {r["HARPNUM"]: r for r in rows}
    ok("temporal: nearest HMI record per HARPNUM within 360 s (exact match preferred to +720 s)",
       by["10"]["hmi_id"] == "H1" and set(by) == {"10", "20", "30", "40"}, "")
    ok("ties at +-360 s accepted (<= 360 s) for different HARPs; tie rule within a HARP picks the earlier record",
       by["20"]["dt_s"] == -360 and by["30"]["dt_s"] == 360, "")
    h5a = rec("H5a", t - timedelta(seconds=300), synth_cea(101.0, 10.0, 51, 51), HARPNUM="50")
    h5b = rec("H5b", t + timedelta(seconds=300), synth_cea(101.0, 10.0, 51, 51), HARPNUM="50")
    for r in (h5a, h5b):
        r["_geom"] = geom_of(r, fmap, "hmi_overlap")
    rows5, _, _ = match_overlap([s1], [h5a, h5b], fmap)
    ok("equal time distance within one HARP -> the earlier record", rows5[0]["hmi_id"] == "H5a", "")
    ok("G5 unique arc for HARP 10 becomes ambiguous in G10 (HARPs 20, 30 at ~6 deg)",
       by["10"]["unique_in_G5"] == 1 and by["10"]["unique_in_G10"] == 0 and by["10"]["ambiguous_on_widening"] == 1
       and by["20"]["in_G5"] == 0 and by["20"]["in_G10"] == 1, f"dist 20: {by['20']['dist_deg']:.2f}")
    ok("candidate without coordinates: not_assessable, no arc, and the SMARP record flags incomplete competitors",
       by["40"]["hmi_geom"] == "not_assessable" and by["40"]["in_G10"] == 0 and states[0]["n_temporal_not_assessable"] == 1
       and states[0]["geometry_complete_competitors"] == 0, "")
    ok("one-to-many: record state has_candidate in both graphs; components counted per graph",
       states[0]["state_G5"] == "has_candidate" and comps[5.0] == 1 and comps[10.0] == 1, json.dumps(comps))
    s_far = rec("S2", t, synth_cea(100.0, 10.0, 301, 301, 0.12), TARPNUM="2")
    h_far = rec("H9", t, synth_cea(112.0, 10.0, 201, 201), HARPNUM="90")
    for r in (s_far, h_far):
        r["_geom"] = geom_of(r, fmap, "smarp_overlap" if r["_id"].startswith("S") else "hmi_overlap")
    rr, _, _ = match_overlap([s_far], [h_far], fmap)
    ok("box_only: centres > 10 deg apart but envelopes intersect; kept outside the angular graphs",
       rr[0]["box_only"] == 1 and rr[0]["in_G10"] == 0, f"dist {rr[0]['dist_deg']:.1f}")
    # field map, profiles and registration
    sch = {SMARP: sc, FD: parse_schema(dict(primekeys=["T_REC"], keywords=[dict(name="T_REC", type="time"),
                                                                          dict(name="QUALITY", type="int")])),
           HMI: parse_schema(dict(primekeys=["HARPNUM", "T_REC"], keywords=[dict(name="HARPNUM"), dict(name="T_REC", type="time"),
                                                                           dict(name="CRPIX1"), dict(name="QUALITY")]))}
    fmp = propose_field_map(sch)
    ok("field map proposal: minimal profiles carry only identity, time, QUALITY (+ confirmed provenance)",
       set(profile_keys(fmp, "fd_min")) == {"T_REC", "QUALITY"} and "CRPIX1" in profile_keys(fmp, "hmi_overlap")
       and "CRPIX1" not in profile_keys(fmp, "smarp_min"), "")
    ok("absent optional field = not_exposed", any(r["role"] == "noaa_ar" and r["status"] == "not_exposed" for r in fmp), "")
    with tempfile.TemporaryDirectory() as tmp:
        run = Run("m", raw_base=tmp, res_base=tmp)
        ok("record queries refused without a registered field map", _raises(lambda: registered_map(run), TechnicalError), "")
        write_csv(run.p("FIELD_MAP.csv"), fmp, FIELD_COLS)
        register_map(run, "selftest")
        ok("registered map accepted; a later edit is detected", registered_map(run)[0] and (
            run.p("FIELD_MAP.csv").write_text(run.p("FIELD_MAP.csv").read_text() + "\n") or True)
           and _raises(lambda: registered_map(run), TechnicalError), "")
    # products
    with tempfile.TemporaryDirectory() as tmp:
        run = Run("p", raw_base=tmp, res_base=tmp)
        for s_, js_ in ((SMARP, dict(primekeys=["TARPNUM", "T_REC"], keywords=[dict(name="TARPNUM"), dict(name="T_REC", type="time")])),
                        (FD, dict(primekeys=["T_REC"], keywords=[dict(name="T_REC", type="time")]))):
            run.p(f"SCHEMA_{s_}.json").write_text(json.dumps(js_))
        with gzip.open(run.p("RECORDS_fd_min.csv.gz"), "wt", newline="") as f:
            wr = csv.writer(f, lineterminator="\n")
            wr.writerow(["window", "edge", "T_REC", "MODE"])
            wr.writerow(["w", 0, "2001.01.01_00:00:00_TAI", "5"])
            wr.writerow(["w", 0, "2001.01.01_01:36:00_TAI", "?"])
        with gzip.open(run.p("RECORDS_smarp_min.csv.gz"), "wt", newline="") as f:
            wr = csv.writer(f, lineterminator="\n")
            wr.writerow(["window", "edge", "TARPNUM", "T_REC", "SRC"])
            wr.writerow(["w", 0, "1", "2001.01.01_00:00:00_TAI", "2001.01.01_00:00:00_TAI"])
            wr.writerow(["w", 0, "2", "2001.01.01_00:00:00_TAI", "2001.01.01_00:00:05_TAI"])
        p0 = product_states(run, [], {})
        ok("without documented rules every source and patch is unknown with its reason (no inference from cadence)",
           all(x["state"] == "unknown" for x in p0) and {x["reason"] for x in p0} == {"not_documented", "source_not_documented"}, "")
        p1 = product_states(run, [], {"fd_product": {"keyword": "MODE", "map": {"5": "documented_5min", "1": "documented_1min"}},
                                      "smarp_source_time": {"keyword": "SRC"}})
        d = {(x["level"], x["state"], x["reason"]): x["n"] for x in p1}
        ok("documented rule: 5-min source resolved by time within 1 s; 5 s offset unresolved; unmapped value unknown",
           d.get(("source_epoch", "documented_5min", "rule")) == 1 and d.get(("source_epoch", "unknown", "value_not_mapped")) == 1
           and d.get(("patch_record", "documented_5min", "time_link_1s")) == 1
           and d.get(("patch_record", "unknown", "source_unresolved")) == 1, json.dumps({"|".join(k): v for k, v in d.items()}))
    # plan and guards
    ok("frozen plan SHA-256 and freeze receipt verified", check_plan().get("plan_sha256") == SHA_PLAN, "")


class SynthCatalog:
    """Tiny synthetic JSOC catalogue for the end-to-end offline test (no real data)."""
    GEO = ["NAXIS1", "NAXIS2", "CRPIX1", "CRPIX2", "CRVAL1", "CRVAL2", "CDELT1", "CDELT2", "CTYPE1", "CTYPE2",
           "CUNIT1", "CUNIT2"]

    def __init__(self):
        kw = lambda names: [dict(name=n, type=("time" if n.startswith("T_") else "string")) for n in names]  # noqa: E731
        ep = [dict(name="T_REC_epoch", defval="1993.01.01_00:00:00_TAI")]
        self.schemas = {
            SMARP: dict(status=0, primekeys=["TARPNUM", "T_REC"], keywords=kw(["TARPNUM", "T_REC", "T_OBS", "QUALITY",
                        "NOAA_AR"] + self.GEO) + ep + [dict(name="T_REC_step", defval="5760")], links=[], segments=[]),
            FD: dict(status=0, primekeys=["T_REC"], keywords=kw(["T_REC", "T_OBS", "QUALITY"]) + ep
                     + [dict(name="T_REC_step", defval="5760")], links=[], segments=[]),
            HMI: dict(status=0, primekeys=["HARPNUM", "T_REC"], keywords=kw(["HARPNUM", "T_REC", "T_OBS", "QUALITY",
                      "NOAA_AR"] + self.GEO) + ep + [dict(name="T_REC_step", defval="720")], links=[], segments=[]),
            SMARP_LEV: dict(status=0, primekeys=["TARPNUM", "T_REC"], keywords=kw(["TARPNUM", "T_REC"]), links=[], segments=[]),
            IC: dict(status=0, primekeys=["T_REC"], keywords=kw(["T_REC"]), links=[], segments=[]),
        }
        g = lambda lon, n, d: dict(NAXIS1=n, NAXIS2=n, CRPIX1=(n + 1) / 2, CRPIX2=(n + 1) / 2, CRVAL1=lon,  # noqa: E731
                                   CRVAL2=12.0, CDELT1=d, CDELT2=d, CTYPE1="CRLN-CEA", CTYPE2="CRLT-CEA",
                                   CUNIT1="deg", CUNIT2="deg")
        s96 = timedelta(minutes=96)
        self.rec = {SMARP: [], FD: [], HMI: [], SMARP_LEV: [], IC: []}
        for k in range(5):
            self.rec[SMARP].append(dict(TARPNUM=7, T_REC=datetime(2001, 3, 10) + k * s96, QUALITY=0, **g(150.0, 31, 0.12)))
        for k in range(4):
            self.rec[SMARP].append(dict(TARPNUM=8, T_REC=datetime(2010, 6, 1) + k * s96, QUALITY=0, **g(150.0, 31, 0.12)))
        self.rec[SMARP].append(dict(TARPNUM=8, T_REC=datetime(2010, 7, 1), QUALITY=0, **g(150.0, 31, 0.12)))
        for k in range(10):
            if k != 5:
                self.rec[FD].append(dict(T_REC=datetime(2001, 3, 10) + k * s96, QUALITY="0x00000000"))
        for k in range(4):
            self.rec[FD].append(dict(T_REC=datetime(2010, 6, 1) + k * s96, QUALITY=0))
        for j in range(41):
            t = datetime(2010, 6, 1) + j * timedelta(minutes=12)
            self.rec[HMI].append(dict(HARPNUM=100, T_REC=t, QUALITY=0, **g(151.0, 101, 0.03)))
            self.rec[HMI].append(dict(HARPNUM=200, T_REC=t, QUALITY=0, **g(157.0, 101, 0.03)))
            self.rec[HMI].append(dict(HARPNUM=300, T_REC=t, QUALITY=0))

    def select(self, ds):
        m = re.match(r"^([\w.]+)((?:\[[^\]]*\])*)$", ds)
        series, br = m.group(1), re.findall(r"\[([^\]]*)\]", m.group(2))
        tb = next(x for x in br if "_TAI-" in x)
        a, _ = parse_time(tb.split("-")[0])
        b, _ = parse_time(tb.split("-")[1])
        return [r for r in self.rec[series] if a <= r["T_REC"] <= b]          # DRMS-like inclusive range

    def answer(self, q):
        op = q["op"]
        if op == "series_struct":
            return self.schemas[q["ds"]]
        rows = self.select(q["ds"])
        if op == "rs_summary":
            return dict(status=0, count=len(rows))
        keys = q["key"].split(",")
        cols = []
        for k in keys:
            vals = []
            for r in rows:
                v = r.get(k, "")
                vals.append(tai_str(v) if isinstance(v, datetime) else str(v))
            cols.append(dict(name=k, values=vals))
        return dict(status=0, count=len(rows), keywords=cols)


def selftest_end_to_end(ok):
    """Schema -> field map registration -> counts -> overlap -> history -> analysis on a synthetic catalogue."""
    fake = FakeJSOC()
    fake.catalog = SynthCatalog()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            run = Run("e2e", raw_base=Path(tmp) / "raw", res_base=Path(tmp) / "res")
            tr, reg = _transport(tmp, fake, path=run.p("REGISTRY.json"))
            phase_schema(run, tr)
            ok("e2e schema: five series saved, field map proposed", len(run.schemas()) == 5
               and run.p("FIELD_MAP_PROPOSED.csv").exists(), "")
            run.p("FIELD_MAP.csv").write_bytes(run.p("FIELD_MAP_PROPOSED.csv").read_bytes())
            register_map(run, "selftest e2e")
            fmap, rules = registered_map(run)
            sch = run.schemas()
            bc = phase_counts(run, tr, sch)
            n_counts = reg.d["attempts"] - 5
            ok("e2e counts: one count per initial window (178 + 15 + 26 = 219), decision full",
               n_counts == 219 and bc["decision"] == "full", f"{n_counts} counts, {bc['lists_needed']}")
            r1 = phase_lists(run, tr, sch, fmap, "overlap")
            rc = [json.loads(x) for x in run.p("LIST_RECEIPTS.jsonl").read_text().splitlines()]
            june = next(x for x in rc if x["profile"] == "smarp_overlap" and x["window"].startswith("2010.06"))
            ok("e2e overlap: inclusive server range gives one edge row at the month end, kept apart",
               june["count_server"] == 5 and june["kept"] == 4 and june["edge"] == 1, json.dumps(r1))
            r2 = phase_lists(run, tr, sch, fmap, "history")
            bp = json.loads(run.p("BUDGET_PAYLOAD.json").read_text())
            ok("e2e history: payload projection written before the historical lists, within caps",
               bp["within_caps"] and set(bp["measures"]) == {"smarp_overlap", "hmi_overlap", "fd_min", "smarp_min"}, json.dumps(r2))
            n_before = reg.d["attempts"]
            r3 = phase_lists(run, tr, sch, fmap, "history")
            ok("e2e resume: completed windows are not queried again", r3["lists"] == 0 and reg.d["attempts"] == n_before, "")
            ok("e2e rows: distinct accepted rows = 5 + 5 + 13 + 123 + 0 edge", reg.d["rows"] == 5 + 5 + 13 + 123,
               str(reg.d["rows"]))
            res = analyze(run)
            ov = res["overlap"]
            ok("e2e analysis: G5 unique arcs 4, all ambiguous on widening to 10 deg (second HARP ~6.9 deg)",
               ov["unique_G5"] == 4 and ov["unique_G10"] == 0 and ov["ambiguous_on_widening"] == 4, json.dumps(ov))
            ok("e2e analysis: July record without HMI coverage is no_candidate; HARP without WCS makes competitors "
               "incomplete; exact time coincidences", ov["state_G5_no_candidate"] == 1 and ov["state_G5_has_candidate"] == 4
               and ov["records_with_incomplete_geometry_competitors"] == 4 and ov["abs_dt_zero"] == ov["temporal_pairs"], "")
            gaps = read_csv(run.res / "GAPS.csv")
            ok("e2e full-disk gaps on the native 96-min grid include the missing slot 2001-03-10 08:00",
               any(g_["start"] == "2001-03-10T08:00:00" and g_["slots"] == "1" for g_ in gaps), f"{len(gaps)} gap runs")
            chk = read_csv(run.res / "CHECKS.csv")
            ok("e2e analysis checks all passed", all(c["passed"] == "True" for c in chk), f"{len(chk)} checks")
    finally:
        fake.close()


def selftest():
    out_ok = True
    res = []

    def ok(name, cond, value=""):
        nonlocal out_ok
        res.append(dict(check=name, passed=bool(cond), value=value))
        out_ok &= bool(cond)
        print(("PASS " if cond else "FAIL ") + name + (f"  [{value}]" if value else ""), flush=True)
    t0 = time.time()
    meta = dict(mode="selftest", plan="§8 offline checks, no network, no real magnetic data", outcome="non riuscito")
    code = 1
    clean = git("status", "--porcelain", "--untracked-files=no") == "" and script_committed()
    out = SELFTEST_BASE / (git("rev-parse", "HEAD")[:12] if clean else "dirty_tree_not_a_receipt")
    try:
        selftest_checks(ok)
        selftest_end_to_end(ok)
        meta.update(n_checks=len(res), n_passed=sum(r["passed"] for r in res))
        meta["outcome"] = "superato" if out_ok else "non superato"
        code = 0 if out_ok else 1
        print(f"{meta['n_passed']}/{meta['n_checks']} passed")
    except Exception as exc:                      # noqa: BLE001
        meta.update(exception_type=type(exc).__name__, exception=str(exc), traceback=traceback.format_exc())
        print(traceback.format_exc())
    finally:
        meta["duration_s"] = time.time() - t0
        if clean:
            out.mkdir(parents=True, exist_ok=False)
            meta.update(provenance())
            write_csv(out / "SELFTEST.csv", res, ["check", "passed", "value"])
            write_json(out / "SELFTEST_META.json", meta)
            print(f"receipt: {out.relative_to(ROOT)}")
        else:
            print("tree not clean or script not committed: results printed only, no receipt written")
    return code


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--phase", choices=("schema", "counts", "overlap", "history", "aux", "continuum"))
    g.add_argument("--register-map", action="store_true")
    g.add_argument("--analyze", action="store_true")
    ap.add_argument("--run-id")
    ap.add_argument("--verified-by")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.run_id:
        ap.error("--run-id is required")
    if a.phase:
        sys.exit(run_phase(a))
    if a.register_map:
        if not a.verified_by:
            ap.error("--verified-by is required")
        print(json.dumps(register_map(Run(a.run_id), a.verified_by), indent=2))
        sys.exit(0)
    if a.analyze:
        print(json.dumps(analyze(Run(a.run_id)), indent=2, default=str))
        sys.exit(0)
