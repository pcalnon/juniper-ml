"""
Show that tests/test_mcp_setup.py kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up H4 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H4, decision D10);
         util/mcp_setup.bash; tests/test_mcp_setup.py;
         util/ad-hoc/2026-10-20_turing_h2_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of util/mcp_setup.bash: the audit's A2-F1 entry (no --project), an
unpinned source, a short sha or a context path or a fork or another host's pin accepted, an unresolved checkout path,
a directory without .git accepted, a missing pin no longer refused, no backup or one backup overwriting another, an
invalid .mcp.json overwritten, a symlinked one followed, other servers dropped, the old mode lost, a dry run or a
second run that writes, a --check that passes a mismatch, and a --remove that drops the other servers. The suite then
runs against that copy, in a scratch tree that mirrors the files it reads (it locates them relative to its own file).

A mutant is KILLED when the suite fails; the report names the tests that failed. The unmutated control must pass, or
the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once. Nothing in the repository
is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (the script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-21_turing_h4_mutation_check.py [--jobs N] [--only ID[,ID...]]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/mcp_setup.bash"
STAGED = (SCRIPT, "tests/test_mcp_setup.py", "tests/redacted_env.py", "conf/hosts/turing/mcp.json", ".serena/project.yml", ".gitignore")
SUITE = "tests.test_mcp_setup"
SUITE_TIMEOUT = 600

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("M1", "the A2-F1 entry: no --project", [('        "--project",\n        checkout,\n', "")]),
    ("M2", "an unpinned source", [('        "%s@%s" % (SOURCE, commit),\n', "        SOURCE,\n")]),
    ("M3", "a short sha passes as a pin", [('re.fullmatch(r"[0-9a-f]{40}", commit)', 're.fullmatch(r"[0-9a-f]{7,40}", commit)')]),
    ("M4", "a context path passes", [('re.fullmatch(r"[a-z0-9][a-z0-9-]*", context)', 're.fullmatch(r".+", context)')]),
    ("M5", "a fork passes as the source", [('if pin.get("source") != SOURCE:', "if False:")]),
    ("M6", "another host's pin is used", [('if conf.get("host") != host:', "if False:")]),
    ("M7", "the checkout path is not resolved", [('CHECKOUT="$(cd "$CHECKOUT" && pwd -P)"', 'CHECKOUT="$(cd "$CHECKOUT" && pwd -L)"')]),
    ("M8", "a directory without .git counts as a checkout", [('[[ -e "${CHECKOUT}/.git" ]] || die_env', "true || die_env")]),
    ("M9", "a missing pin is not refused by name", [('[[ -f "$CONF" ]] || die_env', "true || die_env")]),
    ("M10", "a changed file is not backed up", [("    shutil.copy2(target, backup)\n", "    pass\n")]),
    ("M11", "a second backup in one second overwrites the first", [("    while os.path.lexists(backup):", "    while False:")]),
    ("M12", "an invalid .mcp.json is overwritten", [('        fail(2, "%s is not valid JSON (%s); refusing to overwrite it" % (target, exc))\n', "        doc = {}\n")]),
    ("M13", "a symlinked .mcp.json is followed", [("    if os.path.islink(target) or not os.path.isfile(target):", "    if not os.path.isfile(target):")]),
    ("M14", "other servers are dropped", [('    servers["serena"] = entry\n    doc["mcpServers"] = servers\n', '    doc["mcpServers"] = {"serena": entry}\n')]),
    ("M15", "a rewritten file loses its mode", [("        shutil.copymode(target, tmp)\n", "        pass\n")]),
    ("M16", "a dry run writes", [("if dry_run:\n", "if False:\n")]),
    ("M17", "a second run rewrites the file", [("if new_text == existing_text:\n", "if False:\n")]),
    ("M18", "--check passes a mismatched entry", [("    if current != entry:\n", "    if False:\n")]),
    ("M19", "--remove drops the other servers too", [('    del servers["serena"]\n', "    servers = {}\n")]),
    ("M20", "the dashboard opens at every session start", [('        "--open-web-dashboard",\n        "False",\n', "")]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, text: str | None = None) -> None:
    """Mirror the files the suite reads (and a .git, so the tree is a checkout); optionally install a mutant."""
    for path in STAGED:
        dest = tree / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / path, dest)
    (tree / ".git").mkdir()
    if text is not None:
        (tree / SCRIPT).write_text(text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(text: str | None) -> tuple[bool, list[str], str]:
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw).resolve()
        stage(tree, text)
        proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, failed_tests(output), output


def mutate(original: str, edits: list[tuple[str, str]]) -> str | None:
    mutated = original
    for anchor, replacement in edits:
        if mutated.count(anchor) != 1:
            return None
        mutated = mutated.replace(anchor, replacement)
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="mutants to run at once (default: up to 4)")
    parser.add_argument("--only", help="run only these mutant ids, comma-separated")
    args = parser.parse_args()

    chosen = MUTANTS
    if args.only:
        wanted = set(args.only.split(","))
        chosen = [m for m in MUTANTS if m[0] in wanted]
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    mutated: dict[str, str] = {}
    for mid, _, edits in chosen:
        text = mutate(original, edits)
        if text is None or text == original:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {SCRIPT}; update the mutant")
            return 2
        mutated[mid] = text

    passed, failures, output = run_suite(None)
    if not passed:
        print(f"VOID   control: the suite fails on the unmutated script: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, run_suite(mutated[mutant[0]])), chosen))

    killed = 0
    for (mid, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {defect}")
            continue
        killed += 1
        shown = ", ".join(failures[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {defect} -- {len(failures)} failing test(s): {shown}")

    print(f"\n{killed} of {len(chosen)} mutants killed")
    return 0 if killed == len(chosen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
