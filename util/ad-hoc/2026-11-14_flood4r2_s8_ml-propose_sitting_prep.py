#!/usr/bin/env python3
"""
Prepare the ml-propose carrier's landing on the juniper-ml main of the sitting, in one call, and print one line per step.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, landing)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: the ml-propose + ml-tests sitting)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-propose-r3b-quick-s7/REPORT.txt section 6 F.5 (the procedure, measured end to end);
         tmp/flood4/session8/STATE_S8.txt 2026-11-15 00:07Z (the same steps run by hand on 16f2512b)

Why: F.5 is nine commands, each already run once by hand on 16f2512b. main moved twice since, and will again before
the sitting. This runs them unchanged against a fresh landing worktree (--dest, a detached worktree of origin/main
made by the caller) so a re-run after a move is one command, and it prints a compact summary instead of logs.

Steps (each logged in full under --out):
  1 land.py --dry-run           expect exit 1 and exactly one PROBLEM line, the CHANGELOG one (or exit 0)
  2 land.py                     writes the 22 files into --dest
  3 the s8 changelog helper     the entry to the end of the top [Unreleased]'s existing "### Fixed"
  4 landing_check.py            exit 0, no PROBLEM; every --since commit's added lines kept but stamps
  5 the propose suite           188 OK on /opt/miniforge3/bin/python3.12 and the env's python3.14
  6 the simulator               landed--patch / --minor: gate OK, class OK, propose OK; main--* fail 3 and 4 of 8
  7 make_freeze + sequence-safety probe   both screens exit 0
  8 the pinned pre-commit on the 22 paths, sha256 unchanged
Exit 0 = every step as expected; 1 = a step was not (the summary says which; stop and read its log).

Usage: python3 <this> --dest <fresh landing worktree> --out <dir> --landing-date YYYY-MM-DD --gate <tests file>
       --sims <new dir under Juniper/worktrees> [--since <sha> ...]
Run it through tmp/flood4/session8/runenv.bash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv lists: the arc's own helpers, run in the caller's own trees
import sys
from pathlib import Path

O = Path(__file__).resolve().parents[2]
CARRIER = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-a211deee35ec85ad3")
LAND = CARRIER / "util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py"
CHANGELOG_HELPER = O / "util/ad-hoc/2026-11-14_flood4r2_s8_changelog_into_unreleased_group.py"
CHECK = O / "util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_landing_check.py"
SIM = O / "util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_simulate.py"
FREEZE = O / "util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_make_freeze.py"
PROBE = O / "util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py"
PY312 = "/opt/miniforge3/bin/python3.12"
PY314 = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"
PRECOMMIT = "/opt/miniforge3/bin/pre-commit"


def run(argv: list[str], log: Path, cwd: "Path | None" = None, timeout: int = 1800) -> "tuple[int, str]":
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)  # nosec B603
    text = "$ " + " ".join(argv) + "\n" + proc.stdout + proc.stderr
    log.write_text(text, encoding="utf-8")
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dest", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--landing-date", required=True)
    parser.add_argument("--gate", required=True)
    parser.add_argument("--sims", required=True)
    parser.add_argument("--since", action="append", default=[])
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    dest = args.dest.resolve()
    ok = True
    summary: dict = {}

    def report(step: str, good: bool, detail: str) -> None:
        nonlocal ok
        ok &= good
        summary[step] = {"ok": good, "detail": detail}
        print(f"{'OK  ' if good else 'FAIL'} {step}: {detail}")

    base = [sys.executable, str(LAND), "--carrier", str(CARRIER), "--dest", str(dest), "--landing-date", args.landing_date]
    rc, text = run(base + ["--out", str(out / "dry"), "--dry-run"], out / "1_dry.log")
    problems = [line for line in text.splitlines() if line.startswith("PROBLEM")]
    stamps = [line for line in text.splitlines() if line.startswith("stamp ")]
    good = (rc == 0 and not problems) or (rc == 1 and len(problems) == 1 and problems[0].startswith("PROBLEM CHANGELOG.md"))
    report("1 dry run", good, f"rc={rc}, {len(problems)} PROBLEM line(s); " + "; ".join(s[6:120] for s in stamps[:3]))
    if not good:
        return 1
    rc, text = run(base + ["--out", str(out / "land")], out / "2_land.log")
    oks = sum(1 for line in text.splitlines() if line.startswith("ok "))
    report("2 land", oks == 22 and rc in (0, 1), f"rc={rc}, {oks} ok lines")
    rc, text = run([sys.executable, str(CHANGELOG_HELPER), "--tree", str(dest), "--entry", str(out / "land/texts/changelog_entry.txt"), "--group", "### Fixed"], out / "3_changelog.log")
    report("3 changelog", rc == 0, text.strip().splitlines()[-1][:200] if text.strip() else f"rc={rc}")
    since = []
    for sha in args.since:
        since += ["--since", sha]
    rc, text = run([sys.executable, str(CHECK), "--landed", str(dest), "--out", str(out / "check")] + since, out / "4_check.log")
    removed = [line[:200] for line in text.splitlines() if line.startswith("since ") and "removed lines it added: []" not in line]
    report("4 landing check", rc == 0 and "PROBLEM" not in text, f"rc={rc}; since-lines with removals: {len(removed)} " + " | ".join(r[-90:] for r in removed))
    for label, py in (("5a propose 3.12", PY312), ("5b propose 3.14", PY314)):
        rc, text = run([py, "-B", "-m", "unittest", "tests/test_release_train_propose.py"], out / f"{label[:2]}_propose.log", cwd=dest)
        ran = re.findall(r"^Ran (\d+) tests", text, re.MULTILINE)
        report(label, rc == 0 and ran == ["188"], f"rc={rc}, Ran {ran}")
    rc, text = run([sys.executable, str(SIM), "--make", "--landed", str(dest), "--gate", args.gate, "--sims", args.sims, "--out", str(out / "sim"), "--patch-version", "0.11.6", "--minor-version", "0.12.0"], out / "6_sim.log", timeout=2400)
    lines = [line for line in text.splitlines() if line.startswith(("main--", "landed--"))]
    landed_ok = all("after gate OK (20), class OK (8)" in line and "propose suite OK (188)" in line for line in lines if line.startswith("landed--") and "pristine" not in line)
    main_fail = [re.search(r"class FAILED \(failures=(\d+)\)", line) for line in lines if line.startswith(("main--patch", "main--minor"))]
    report("6 simulator", rc == 0 and landed_ok and [m.group(1) if m else None for m in main_fail] == ["3", "4"], " | ".join(line[:70] for line in lines))
    rc, text = run([sys.executable, str(FREEZE), "--landed", str(dest), "--out", str(out / "freeze")], out / "7a_freeze.log")
    report("7a make_freeze", rc == 0, text.strip().splitlines()[-1][:160] if text.strip() else f"rc={rc}")
    rc, text = run([sys.executable, str(PROBE), "--freeze", str(out / "freeze"), "--title", str(out / "land/texts/pr_title.txt"), "--body", str(out / "land/texts/commit_body.txt"), "--out", str(out / "seqsafety"), "--scope", "tests/*.py", "--scope", "util/**/*.py", "--scope", "util/**/*.bash", "--repo-dir", str(dest), "--main-ref", "HEAD"], out / "7b_seqsafety.log")
    screens = [line.strip() for line in text.splitlines() if "files_screened=" in line or "screen exit=" in line]
    report("7b sequence safety", rc == 0, " | ".join(screens))
    paths = json.loads((out / "freeze" / "plan.json").read_text(encoding="utf-8")) if (out / "freeze" / "plan.json").is_file() else None
    plist = [line.split(" ", 1)[1] for line in (out / "freeze" / "paths.txt").read_text(encoding="utf-8").splitlines() if line.startswith("add ")]
    before = {p: hashlib.sha256((dest / p).read_bytes()).hexdigest() for p in plist}
    rc, text = run([PRECOMMIT, "run", "--files", *plist], out / "8_precommit.log", cwd=dest)
    after = {p: hashlib.sha256((dest / p).read_bytes()).hexdigest() for p in plist}
    report("8 pre-commit", rc == 0 and before == after, f"rc={rc}, {text.count('Passed')} Passed, {text.count('Skipped')} Skipped, {sum(before[p] != after[p] for p in plist)} file(s) rewritten")
    (out / "summary.json").write_text(json.dumps({"dest": str(dest), "plan": bool(paths), "steps": summary}, indent=1) + "\n", encoding="utf-8")
    print("ALL AS EXPECTED" if ok else "NOT ALL AS EXPECTED: read the step's log")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
