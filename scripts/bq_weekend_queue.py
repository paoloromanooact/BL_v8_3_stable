"""BQ-HMI synthetic weekend queue (programme of 27 Nov 2026, Codex): pilot only by default.
With --extend, run the manifest jobs of each likelihood that passed. Synthetic responses only (draft protocol, nothing frozen).

1) Pilot: block 8, G1, M0 and MQ without v, for L2 and L3 (4 runs, concurrent). When both models of a likelihood have
   ended, the manifest's check_pilot_gate.py decides (training diagnostics, MCSE <= 0.1, weights ESS >= 100, provenance
   recounted by check_run.py); only --extend and a passing gate admit the other manifest jobs. A failed likelihood
   stops there (no automatic correction: the cause is decided by hand).
2) Jobs of the admitted likelihoods in manifest order (block_order, generator, model); the pilot runs are reused.
   Every run ends with check_run.py (manifest, provenance, recomputed score).
3) Limits: no new run after --no-new-after; every run gets the driver's internal --deadline and an external `timeout`
   to the hard deadline, so all processes end by then. Concurrency from the file PROCS in the output directory (read at
   every loop, default --procs), so it can be changed without a restart. A run whose directory already exists is not
   started again (the queue can be restarted after an interruption).
Driver arguments common to every run: --chains 4 --warm 300 --keep 1500 --thin 6 --particles 1000 --smc-reps 1
--repeat-every 10 --extra-reps 1 --checkpoints 40,80,120,160,200 --budget-draws 200 --stop-when-established 120.

    OMP_NUM_THREADS=1 setsid nohup .venv/bin/python -u scripts/bq_weekend_queue.py --manifest <preflight dir> --out <dir> &
"""
from __future__ import annotations

import argparse
import csv
import datetime as dtm
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ["--chains", "4", "--warm", "300", "--keep", "1500", "--thin", "6", "--particles", "1000", "--smc-reps", "1",
          "--repeat-every", "10", "--extra-reps", "1", "--checkpoints", "40,80,120,160,200", "--budget-draws", "200",
          "--budget-hours", "40", "--stop-when-established", "120"]


def name(j):
    return f"b{j['block_id']}_{j['generator']}_r{j['response_rep']}_{j['likelihood']}_{j['model']}_{j['v']}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extend", action="store_true", help="run additional manifest jobs after a passing pilot")
    ap.add_argument("--blocks", default="", help="with --extend: committed blocks, in this order (default: the whole manifest)")
    ap.add_argument("--next", type=int, help="with --extend: block admitted after --blocks only if it fits entirely")
    ap.add_argument("--reserve", type=int, help="with --extend: block admitted instead of --next if --next does not fit")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--hard-deadline", default="2026-11-30T09:00")
    ap.add_argument("--no-new-after", default="2026-11-30T06:00")
    ap.add_argument("--margin-min", type=float, default=15.0)
    ap.add_argument("--driver-extra", default="", help="extra driver arguments (smoke tests only; later values override)")
    a = ap.parse_args()
    man, out = Path(a.manifest).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    hard = dtm.datetime.fromisoformat(a.hard_deadline).timestamp()
    no_new = dtm.datetime.fromisoformat(a.no_new_after).timestamp()
    driver_deadline = dtm.datetime.fromtimestamp(hard - 60 * a.margin_min).strftime("%Y-%m-%dT%H:%M")
    jobs = list(csv.DictReader((man / "JOBS.csv").open()))
    pilot = {k: [j for j in jobs if j["block_id"] == "8" and j["generator"] == "G1" and j["response_rep"] == "0" and j["likelihood"] == k
                 and j["v"] == "none"] for k in ("L2", "L3")}
    assert all(len(v) == 2 for v in pilot.values()), "manifest without the four pilot jobs"

    def log(msg):
        with (out / "queue.log").open("a") as f:
            f.write(f"{dtm.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")

    def status(row):
        p = out / "STATUS.csv"
        new = not p.exists()
        with p.open("a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)

    def procs():
        try:
            return max(1, int((out / "PROCS").read_text().strip()))
        except (OSError, ValueError):
            return a.procs

    committed = [int(b) for b in a.blocks.split(",") if b.strip()] or None
    decided = a.next is None and a.reserve is None

    def block_jobs(k, blocks):
        """Manifest jobs of likelihood k in the given blocks (block order as given, then manifest order); pilots excluded."""
        sel = [j for j in jobs if j["likelihood"] == k and j not in pilot[k]]
        if blocks is None:
            return sel
        return [j for b in blocks for j in sel if int(j["block_id"]) == b]

    def cost_hours(block):
        """Worst-case hours of a whole block for the admitted likelihoods, from the runs completed so far: seconds per SMC
        evaluation per verification record and fit seconds measured per likelihood, cap of 200 draws + 10 % controls."""
        tot = 0.0
        for k in [k for k, v in gate.items() if v]:
            sec = ev = 0.0
            fits = []
            for d in out.iterdir():
                m = d / "META.json"
                if not (d.is_dir() and m.exists()):
                    continue
                meta = json.loads(m.read_text())
                if meta.get("status") != "completed" or meta.get("args", {}).get("kind") != k or not (d / "DRAWS.csv").exists():
                    continue
                rows = list(csv.DictReader((d / "DRAWS.csv").open()))
                sec += float(meta["smc_seconds"])
                ev += sum(int(r["n_main"]) + int(r["n_extra"]) for r in rows) * int(meta["records"])
                fits.append(float(meta["fit_seconds"]))
            rate, fit = sec / ev, sum(fits) / len(fits)
            for j in block_jobs(k, [block]):
                tot += (1.1 * 200 * rate * int(j["n_verify"]) + fit) / 3600
        return tot

    def done(j):
        m = out / name(j) / "META.json"
        return m.exists() and json.loads(m.read_text()).get("status") == "completed"

    log(f"start; HEAD {subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()}; "
        f"driver deadline {driver_deadline}; no new run after {a.no_new_after}")
    queue = [j for k in ("L2", "L3") for j in pilot[k]]
    running, gate = {}, {}
    while True:
        now = time.time()
        # finished runs
        for key, (proc, j, t0) in list(running.items()):
            if proc.poll() is None:
                continue
            del running[key]
            chk = subprocess.run([sys.executable, str(man / "check_run.py"), str(out / key)], cwd=ROOT, capture_output=True, text=True)
            status(dict(run=key, exit=proc.returncode, start=time.strftime("%H:%M:%S", time.localtime(t0)),
                        end=time.strftime("%H:%M:%S"), check_exit=chk.returncode, check=(chk.stdout or chk.stderr).strip().replace("\n", " ")))
            log(f"end {key} exit {proc.returncode}; check exit {chk.returncode}")
        # pilot gates
        for k in ("L2", "L3"):
            if k in gate or not all(done(j) for j in pilot[k]) or any(name(j) in running for j in pilot[k]):
                continue
            m0 = next(j for j in pilot[k] if j["model"] == "M0")
            mq = next(j for j in pilot[k] if j["model"] == "MQ")
            g = subprocess.run([sys.executable, str(man / "check_pilot_gate.py"), k, str(out / name(m0)), str(out / name(mq))],
                               cwd=ROOT, capture_output=True, text=True)
            gate[k] = g.returncode == 0
            (out / f"GATE_{k}.json").write_text(g.stdout or g.stderr)
            log(f"gate {k}: {'READY' if gate[k] else 'NOT READY'} {(g.stdout or g.stderr).strip()[:300]}")
            if gate[k] and a.extend:
                queue += block_jobs(k, committed)
            elif gate[k]:
                log(f"{k}: pilot complete; further jobs require --extend")
        # pilot runs that could not complete (exit without META completed) also close the gate
        for k in ("L2", "L3"):
            if k not in gate and all((out / name(j)).exists() for j in pilot[k]) and not any(name(j) in running for j in pilot[k]) \
                    and not all(done(j) for j in pilot[k]) and not any(j in queue for j in pilot[k]):
                gate[k] = False
                log(f"gate {k}: NOT READY (a pilot run did not complete)")
        # launches
        while queue and len(running) < procs() and time.time() < no_new and hard - time.time() > 60 * a.margin_min:
            j = queue.pop(0)
            key = name(j)
            if (out / key).exists():
                log(f"skip {key}: directory exists")
                continue
            secs = int(hard - time.time())
            cmd = ["timeout", "--kill-after=60s", str(secs), str(ROOT / ".venv/bin/python"), "-u", str(ROOT / "scripts/bq_cv_psi_smc.py"),
                   "--kind", j["likelihood"], "--model", j["model"], "--v", j["v"], "--block-id", j["block_id"], "--response", j["generator"],
                   "--response-rep", j["response_rep"], "--deadline", driver_deadline, "--deadline-margin-min", str(a.margin_min),
                   "--out", str(out / key)] + COMMON + a.driver_extra.split()
            lf = (out / f"{key}.log").open("w")
            running[key] = (subprocess.Popen(cmd, cwd=ROOT, stdout=lf, stderr=subprocess.STDOUT, env=dict(os.environ, OMP_NUM_THREADS="1")), j,
                            time.time())
            log(f"launch {key} (running {len(running)}/{procs()})")
        pilots_open = any(k not in gate for k in ("L2", "L3"))
        if not running and not queue and not pilots_open and a.extend and not decided and any(gate.values()):
            decided = True                                     # after the committed blocks: time and status only, never scores
            left = (no_new - time.time()) / 3600
            for b in [x for x in (a.next, a.reserve) if x is not None]:
                need = cost_hours(b)
                log(f"block {b}: worst case {need:.1f} h, {left:.1f} h left before the last start")
                if need <= left:
                    queue += [j for k in ("L2", "L3") if gate.get(k) for j in block_jobs(k, [b])]
                    log(f"block {b} admitted")
                    break
            else:
                log("no further block fits entirely: stop")
            continue
        if not running and not queue and not pilots_open:
            break
        if not running and (time.time() >= no_new or hard - time.time() <= 60 * a.margin_min):
            log(f"time limit: {len(queue)} jobs not started")
            break
        time.sleep(30)
    log(f"queue completed; gates {gate}")


if __name__ == "__main__":
    main()
