#!/usr/bin/env python3
"""
Land the flood-4 "ml-tests" carrier on the main of the day: rebuild it there and re-derive every count, stamp and date.

The carrier is an uncommitted tree built on one commit of main. Other pull requests land before it and move the
files it shares with them (ci.yml's suite list, docs/REFERENCE.md and its stamp, AGENTS.md's count, CHANGELOG.md),
and a landing can slip past midnight UTC. So nothing is typed at the landing; this is the one command for it.

In --dest, a worktree whose HEAD is the main the pull request will be based on, and whose working tree is clean:

  1. every file of the carrier's manifest is checked against the sha256 the manifest recorded (a carrier that
     changed since its last proof is refused);
  2. the five shared files are left at --dest's own copies, and every other file is COPIED when main has not
     changed it since the carrier's base, or rebuilt THREE-WAY (`git merge-file`: carrier / base / main) when it
     has; a conflict stops the landing;
  3. the registrations are re-derived by the carrier's own tools, run in --dest: the wiring tool from the
     carrier's spec.json, then the shared-edits tool (suite count = main's + the carrier's; docs/REFERENCE.md
     version = main's plus one patch; every date = --landing-date; the macOS list's totals from the files);
  4. the texts are rendered from the carrier's templates with those values, and the CHANGELOG entry is inserted;
  5. the result is checked: the list-drift tool, the wiring-drift suite, the macOS list gate, and --dest's change
     list against the manifest's paths.

The version-control tool is run in --dest only, never in the carrier: the carrier's base commit is read from
--dest's object store (every worktree of one repository shares it), so the carrier may be a tree this session
may only read.

--ml-propose-pr N writes the number of the ml-propose carrier's pull request where the templates leave the token
<ML-PROPOSE-PR> (the CHANGELOG entry, the pull request body, the commit body). Without it the token stays, and the
report lists every place it stands in --dest.

--keep PATH (repeatable) names a helper that --dest already holds in a version newer than the carrier's: it may be
changed before the landing, and the landing leaves it alone. It exists for one use, the rebuild of this carrier
from the tree a stopped builder left; a landing for a pull request passes none. --templates and --spec name the
texts' templates and the wiring spec when they are not the carrier's own.

--render-only renders the texts for the carrier's own tree (values from its derived.json) and writes nothing else;
run it from inside the carrier.

Usage:
    python3 <carrier>/util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_land.py --carrier <carrier worktree>
        --dest <landing worktree> --landing-date <UTC date, YYYY-MM-DD> --out <scratch dir> [--ml-propose-pr N]
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_land.py --carrier . --render-only --out <dir>

Exit 0 only when the rebuild has no conflict and every check holds.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py (the ml-propose carrier's, the model for this one)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRATCH_REL = "tmp/flood4r2/ml-tests/r2"
AD_HOC = "util/ad-hoc/"
WIRE = AD_HOC + "2026-11-09_flood4r2_ml-tests_wire.py"
SHARED_EDITS = AD_HOC + "2026-11-12_flood4r2_ml-tests-r2_shared_edits.py"
CHANGELOG_TOOL = AD_HOC + "2026-11-12_flood4r2_ml-tests-r2_changelog.py"
DRIFT = AD_HOC + "2026-09-10_agents_md_test_list_drift.py"
TEMPLATES = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt")
ML_PROPOSE_TOKEN = "<ML-PROPOSE-PR>"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def _run(argv: list, cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)


def _blob(root: Path, rev: str, path: str):
    done = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=str(root), capture_output=True, check=False)
    return done.stdout if done.returncode == 0 else None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "absent"


def _values(derived: dict, main_sha: str) -> dict:
    return {
        "SUITE_COUNT": derived["suite_count"],
        "MAIN_SUITE_COUNT": derived["main_suite_count"],
        "REF_VERSION": derived["docs/REFERENCE.md"]["version"],
        "MAIN_REF_VERSION": derived["docs/REFERENCE.md"]["main_version"],
        "DATE": derived["date"],
        "HOST_TOOLING_TOTAL": derived["host_tooling"]["total"],
        "GUARD_SUITES_ON_DISK": derived["host_tooling"]["guard_suites_on_disk"],
        "MAIN_SHA": main_sha[:8],
    }


def _render(templates: Path, values: dict, out: Path, ml_propose_pr: str) -> list:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name in TEMPLATES:
        text = (templates / name).read_text(encoding="utf-8")
        for key, value in values.items():
            text = text.replace(f"@{key}@", str(value))
        if ml_propose_pr:
            text = text.replace(ML_PROPOSE_TOKEN, ml_propose_pr)
        left = sorted(set(re.findall(r"@[A-Z][A-Z_]*@", text)))
        if left:
            raise SystemExit(f"{name}: unrendered tokens {left}")
        (out / name).write_text(text, encoding="utf-8")
        written.append(str(out / name))
    return written


def _token_places(root: Path, paths: list) -> list:
    """Where the token stands in the landed files; the helpers under util/ad-hoc/ name it as code and are not text."""
    places = []
    for path in paths:
        target = root / path
        if path.startswith(AD_HOC) or not target.is_file():
            continue
        for number, line in enumerate(target.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ML_PROPOSE_TOKEN in line:
                places.append(f"{path}:{number}")
    return places


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carrier", required=True, type=Path)
    ap.add_argument("--dest", type=Path)
    ap.add_argument("--landing-date")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--render-only", action="store_true")
    ap.add_argument("--ml-propose-pr", default="", help="the ml-propose pull request's number, written where the templates leave <ML-PROPOSE-PR>")
    ap.add_argument("--templates", type=Path, help="default: the carrier's tmp/flood4r2/ml-tests/r2/templates")
    ap.add_argument("--spec", type=Path, help="default: the carrier's tmp/flood4r2/ml-tests/r2/spec.json")
    ap.add_argument("--keep", action="append", default=[], help="a path --dest already holds in a newer version; left alone (the rebuild from a stopped builder's tree only)")
    args = ap.parse_args()
    if args.ml_propose_pr and not re.fullmatch(r"[1-9][0-9]*", args.ml_propose_pr):
        raise SystemExit("--ml-propose-pr must be a pull request number")
    carrier, out = args.carrier.resolve(), args.out.resolve()
    scratch = carrier / SCRATCH_REL
    templates = args.templates.resolve() if args.templates else scratch / "templates"
    spec = args.spec.resolve() if args.spec else scratch / "spec.json"
    out.mkdir(parents=True, exist_ok=True)
    if args.render_only:
        if carrier != Path.cwd().resolve():
            raise SystemExit("--render-only: run it from inside the carrier (--carrier .)")
        with open(scratch / "derived.json", encoding="utf-8") as fh:
            derived = json.load(fh)
        head = _run(["git", "rev-parse", "HEAD"], carrier).stdout.strip()
        print("\n".join(_render(templates, _values(derived, head), out, args.ml_propose_pr)))
        return 0
    if args.dest is None or not args.landing_date:
        raise SystemExit("--dest and --landing-date are required for a landing")
    dest = args.dest.resolve()
    with open(scratch / "manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    base, files = manifest["base_sha"], manifest["files"]
    keep = sorted(set(args.keep))
    problems, rows = [], []
    for entry in files:
        actual = _sha(carrier / entry["path"])
        if actual != entry["sha256"]:
            problems.append(f"{entry['path']}: the carrier's file is {actual[:12]}, its manifest recorded {entry['sha256'][:12]}")
    main_sha = _run(["git", "rev-parse", "HEAD"], dest).stdout.strip()
    if _run(["git", "cat-file", "-e", f"{base}^{{commit}}"], dest).returncode != 0:
        problems.append(f"the carrier's base {base} is not in --dest's object store")
    dirty = sorted(line[3:] for line in _run(["git", "status", "--porcelain", "--untracked-files=all"], dest).stdout.splitlines())
    unexpected = [path for path in dirty if path not in keep]
    if unexpected:
        problems.append("--dest is not clean:\n" + "\n".join(unexpected))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    work = out / "merge"
    work.mkdir(parents=True, exist_ok=True)
    for entry in files:
        path, how = entry["path"], entry["how"]
        row = {"path": path, "carrier_how": how}
        if path in keep:
            row["landing"] = "kept: --dest's own, newer copy (--keep)"
        elif how == "re-derived":
            row["landing"] = "left at main's copy for the tools"
        else:
            base_blob, main_blob = _blob(dest, base, path), _blob(dest, "HEAD", path)
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if base_blob == main_blob:
                shutil.copyfile(carrier / path, target)
                row["landing"] = "copied (main has not changed it since the carrier's base)"
            else:
                flat = path.replace("/", "__")
                (work / f"{flat}.base").write_bytes(base_blob or b"")
                (work / f"{flat}.main").write_bytes(main_blob or b"")
                merged = subprocess.run(["git", "merge-file", "-p", "-L", "carrier", "-L", "base", "-L", "main", str(carrier / path), str(work / f"{flat}.base"), str(work / f"{flat}.main")], capture_output=True, check=False)
                (work / f"{flat}.merged").write_bytes(merged.stdout)
                row["landing"] = f"three-way, {merged.returncode} conflict(s)"
                if merged.returncode != 0:
                    problems.append(f"{path}: {merged.returncode} conflict(s) in the three-way rebuild; resolve by hand from {work}")
                else:
                    target.write_bytes(merged.stdout)
        rows.append(row)
    steps = []
    if not problems:
        chain = (
            ("wire", [sys.executable, "-B", WIRE, "--spec", str(spec)]),
            ("shared edits", [sys.executable, "-B", SHARED_EDITS, "--date", args.landing_date, "--out", str(out / "derived.json")]),
        )
        for name, argv in chain:
            done = _run(argv, dest)
            (out / f"{name.replace(' ', '_')}.log").write_text(done.stdout + done.stderr, encoding="utf-8")
            steps.append({"step": name, "rc": done.returncode})
            if done.returncode != 0:
                problems.append(f"{name}: exit {done.returncode}: {(done.stdout + done.stderr).strip()[-400:]}")
                break
    derived, token_places = {}, []
    if not problems:
        with open(out / "derived.json", encoding="utf-8") as fh:
            derived = json.load(fh)
        _render(templates, _values(derived, main_sha), out / "texts", args.ml_propose_pr)
        checks = (
            ("changelog entry", [sys.executable, "-B", CHANGELOG_TOOL, str(out / "texts" / "changelog_entry.txt")]),
            ("list drift", [sys.executable, "-B", DRIFT]),
            ("wiring drift suite", [sys.executable, "-B", "-m", "unittest", "tests/test_ci_test_wiring_drift.py"]),
            ("macOS list gate", [sys.executable, "-B", "-m", "unittest", "tests/test_ci_host_tooling_macos.py"]),
        )
        for name, argv in checks:
            done = _run(argv, dest)
            (out / f"{name.replace(' ', '_')}.log").write_text(done.stdout + done.stderr, encoding="utf-8")
            steps.append({"step": name, "rc": done.returncode})
            if done.returncode != 0:
                problems.append(f"{name}: exit {done.returncode}: {(done.stdout + done.stderr).strip()[-400:]}")
        changed = sorted(line[3:] for line in _run(["git", "status", "--porcelain", "--untracked-files=all"], dest).stdout.splitlines())
        expected = sorted({entry["path"] for entry in files} | set(keep))
        if changed != expected:
            problems.append(f"--dest's change list differs from the manifest's paths: only there {sorted(set(changed) - set(expected))}, missing there {sorted(set(expected) - set(changed))}")
        token_places = _token_places(dest, changed) + [f"{out / 'texts' / name} (rendered text)" for name in TEMPLATES if ML_PROPOSE_TOKEN in (out / "texts" / name).read_text(encoding="utf-8")]
        if args.ml_propose_pr and token_places:
            problems.append(f"--ml-propose-pr was given, but {ML_PROPOSE_TOKEN} still stands at {token_places}")
    report = {
        "carrier": str(carrier),
        "carrier_base": base,
        "dest": str(dest),
        "main_sha": main_sha,
        "landing_date": args.landing_date,
        "ml_propose_pr": args.ml_propose_pr or None,
        "ml_propose_token_stands_at": token_places,
        "kept": keep,
        "templates": str(templates),
        "spec": str(spec),
        "files": rows,
        "steps": steps,
        "derived": derived,
        "problems": problems,
    }
    (out / "landing_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['landing']:<62} {row['path']}")
    print(json.dumps(derived, indent=1))
    print(f"{ML_PROPOSE_TOKEN} stands at: {token_places or 'nowhere'}")
    print("OK" if not problems else "PROBLEMS:\n" + "\n".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
