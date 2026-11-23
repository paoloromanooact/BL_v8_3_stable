"""Deposit package of the MWO tilt catalogue 1974-2012 (local; NOT a publication).

Builds results/MWO_TILT_CATALOGUE_DEPOSIT_V1 from the verified release (results/MWO_TILT_CATALOGUE_RELEASE, check
115/115) without touching it:
  - every release product copied byte for byte, except its short README, kept as README_RELEASE_SHORT.md;
  - README.md = docs/MWO_TILT_CATALOGUE_README.md (committed, unchanged);
  - RELEASE_META.json = the release META, unchanged;
  - META.json (package metadata: file hashes, links to the release META and to its check receipt, commit);
  - SHA256SUMS.txt for `sha256sum -c`.
Refuses unless the release check receipt is strict, complete and bound to the current release META, and every release
product matches its declared hash. Atomic write, no overwrite. Licence, authors and repository: to be agreed.

    .venv/bin/python scripts/mwo_catalogue_deposit_package.py --selftest
    .venv/bin/python scripts/mwo_catalogue_deposit_package.py --build
    .venv/bin/python scripts/mwo_catalogue_deposit_package.py --check
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE"
REL_REC = ROOT / "results/MWO_TILT_CATALOGUE_RELEASE_RECOUNT"
README = ROOT / "docs/MWO_TILT_CATALOGUE_README.md"
OUT = ROOT / "results/MWO_TILT_CATALOGUE_DEPOSIT_V1"
RENAMED = {"README.md": "README_RELEASE_SHORT.md"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def release_problems(rel=REL, rec=REL_REC):
    probs = []
    try:
        m = json.loads((Path(rel) / "META.json").read_text())
        r = json.loads((Path(rec) / "RECEIPT.json").read_text())
    except (OSError, ValueError) as exc:
        return [f"release or receipt unreadable ({type(exc).__name__})"]
    p, t, ch = r.get("passed"), r.get("total"), r.get("checks")
    strict = lambda x: isinstance(x, int) and not isinstance(x, bool)          # noqa: E731
    if not (strict(p) and strict(t) and t > 0 and p == t and isinstance(ch, list) and len(ch) == t
            and all(isinstance(c, dict) and c.get("ok") is True for c in ch) and r.get("partial") is False):
        probs.append("release receipt not strict or not complete")
    if r.get("release_meta_sha256") != sha(Path(rel) / "META.json"):
        probs.append("release receipt not bound to the current release META")
    ps = m.get("products_sha256")
    if not isinstance(ps, dict) or not ps:
        return probs + ["release manifest empty"]
    on_disk = {str(f.relative_to(rel)) for f in Path(rel).rglob("*") if f.is_file()} - {"META.json", "RUN.log"}
    if on_disk != set(ps):
        probs.append("release files differ from its manifest")
    for n, h in ps.items():
        try:
            if sha(Path(rel) / n) != h:
                probs.append(f"{n}: hash differs from the release META")
        except OSError:
            probs.append(f"{n}: missing")
    return probs


def build(out=OUT, rel=REL, rec=REL_REC, readme=README, require_git=True):
    if Path(out).exists():
        sys.exit("refusing to overwrite")
    probs = release_problems(rel, rec)
    if probs:
        sys.exit("release problems: " + "; ".join(probs))
    commit = ""
    if require_git:
        git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)  # noqa: E731
        if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
            sys.exit("tracked tree not clean")
        if not git("ls-files", str(Path(readme).relative_to(ROOT))).stdout.strip():
            sys.exit("README not committed")
        commit = git("rev-parse", "HEAD").stdout.strip()
    rel_meta = json.loads((Path(rel) / "META.json").read_text())
    readme_sha = sha(readme)
    tmp = Path(tempfile.mkdtemp(prefix=f".{Path(out).name}.tmp-", dir=Path(out).parent))
    try:
        mapping = {}
        for n in sorted(rel_meta["products_sha256"]):
            dst = RENAMED.get(n, n)
            (tmp / dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(rel) / n, tmp / dst)
            mapping[dst] = n
        shutil.copyfile(readme, tmp / "README.md")
        shutil.copyfile(Path(rel) / "META.json", tmp / "RELEASE_META.json")
        files = sorted(str(f.relative_to(tmp)) for f in tmp.rglob("*") if f.is_file())
        meta = dict(status="local deposit package, NOT published; licence, authors and repository to be agreed",
                    release_meta_sha256=sha(Path(rel) / "META.json"), release_receipt_sha256=sha(Path(rec) / "RECEIPT.json"),
                    readme_source="docs/MWO_TILT_CATALOGUE_README.md", readme_sha256=readme_sha,
                    copied_from_release=mapping, git_commit=commit, script_sha256=sha(__file__),
                    files_sha256={f: sha(tmp / f) for f in files})
        (tmp / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
        sums = {f: sha(tmp / f) for f in files + ["META.json"]}
        (tmp / "SHA256SUMS.txt").write_text("".join(f"{h}  {f}\n" for f, h in sorted(sums.items())))
        if sha(readme) != readme_sha or release_problems(rel, rec):
            sys.exit("README or release changed during the build: nothing written")
        os.rename(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    print(f"written {out}")
    return 0


def check(out=OUT, rel=REL, rec=REL_REC, readme=README):
    res = []

    def ok(name, cond, info=""):
        res.append(dict(name=name, ok=bool(cond)))
        print(f"[{'OK' if cond else 'FALLITO'}] {name} {info}")

    out = Path(out)
    meta = json.loads((out / "META.json").read_text())
    lines = [l.split("  ", 1) for l in (out / "SHA256SUMS.txt").read_text().splitlines()]
    sums = {f: h for h, f in lines}
    files = {str(f.relative_to(out)) for f in out.rglob("*") if f.is_file()} - {"SHA256SUMS.txt"}
    ok("SHA256SUMS covers exactly the package files and matches", set(sums) == files and len(sums) == len(lines)
       and all(sha(out / f) == h for f, h in sums.items()), len(sums))
    ok("META file hashes match", all(sha(out / f) == h for f, h in meta["files_sha256"].items())
       and set(meta["files_sha256"]) == files - {"META.json"})
    rel_meta = json.loads((Path(rel) / "META.json").read_text())
    ok("release still verified (strict receipt, products, binding)", not release_problems(rel, rec))
    ok("package bound to the current release META and receipt", meta["release_meta_sha256"] == sha(Path(rel) / "META.json")
       and meta["release_receipt_sha256"] == sha(Path(rec) / "RECEIPT.json")
       and sha(out / "RELEASE_META.json") == sha(Path(rel) / "META.json"))
    ok("every release product copied byte for byte (README kept as README_RELEASE_SHORT.md)",
       set(meta["copied_from_release"].values()) == set(rel_meta["products_sha256"])
       and all(sha(out / dst) == rel_meta["products_sha256"][src] for dst, src in meta["copied_from_release"].items()))
    ok("README.md is the committed final README", sha(out / "README.md") == meta["readme_sha256"] == sha(readme))
    print(f"check: {sum(r['ok'] for r in res)}/{len(res)}")
    return all(r["ok"] for r in res)


def selftest():
    res = []

    def ok(name, cond):
        res.append(bool(cond))
        print(f"[{'OK' if cond else 'FALLITO'}] {name}")

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rel, rec, readme = td / "rel", td / "rec", td / "README_FINAL.md"
        (rel / "COMPARISONS").mkdir(parents=True)
        rec.mkdir()
        for n in ("A.csv", "README.md", "COMPARISONS/S.csv"):
            (rel / n).write_text(n * 3)
        (rel / "META.json").write_text(json.dumps({"products_sha256": {n: sha(rel / n) for n in ("A.csv", "README.md", "COMPARISONS/S.csv")}}))
        readme.write_text("final readme")

        def receipt(**kw):
            r = dict(passed=2, total=2, partial=False, checks=[dict(ok=True), dict(ok=True)], release_meta_sha256=sha(rel / "META.json"))
            r.update(kw)
            (rec / "RECEIPT.json").write_text(json.dumps(r))

        receipt()
        out = td / "pkg"
        build(out, rel, rec, readme, require_git=False)
        ok("package built and checked on a synthetic release", check(out, rel, rec, readme))
        ok("short README kept, final README in place", (out / "README_RELEASE_SHORT.md").read_text() == "README.md" * 3
           and (out / "README.md").read_text() == "final readme")
        ok("no temporary folder left", not list(td.glob(".pkg.tmp-*")))
        try:
            build(out, rel, rec, readme, require_git=False)
            ok("refuses to overwrite", False)
        except SystemExit:
            ok("refuses to overwrite", True)
        for label, kw in (("partial receipt", dict(partial=True)), ("0/0 receipt", dict(passed=0, total=0, checks=[])),
                          ("boolean counts", dict(passed=True, total=True, checks=[dict(ok=True)])),
                          ("receipt not bound", dict(release_meta_sha256="0" * 64))):
            receipt(**kw)
            try:
                build(td / f"p_{label.replace(' ', '_')}", rel, rec, readme, require_git=False)
                ok(f"refused: {label}", False)
            except SystemExit:
                ok(f"refused: {label}", True)
        receipt()
        (rel / "A.csv").write_text("changed")
        try:
            build(td / "p_changed", rel, rec, readme, require_git=False)
            ok("refused: release product changed", False)
        except SystemExit:
            ok("refused: release product changed", True)
        ok("check fails after a release product changed", not check(out, rel, rec, readme))
        (rel / "A.csv").write_text("A.csv" * 3)
        (out / "COMPARISONS/S.csv").write_text("tampered")
        ok("check fails on a tampered package file", not check(out, rel, rec, readme))
    print(f"selftest: {sum(res)}/{len(res)} superati")
    return all(res)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--build", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    sys.exit(build() if a.build else (0 if check() else 1))
