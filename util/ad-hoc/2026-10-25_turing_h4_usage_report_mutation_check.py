"""
Show that tests/test_mcp_setup.py kills a mutant for each way the H4 entry's usage-report opt-out can regress.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — investigation (suite strength evidence for the H4 usage-report opt-out, erratum E-H6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H4, erratum E-H6);
         notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md (SER-E1);
         util/mcp_setup.bash; tests/test_mcp_setup.py; conf/hosts/turing/mcp.json;
         util/ad-hoc/2026-10-21_turing_h4_mutation_check.py (the pattern this follows; its 20 mutants still apply)

Serena v1.7.0 reports usage to oraios-software.de at every start unless SERENA_USAGE_REPORTING is exactly "false"
(src/serena/agent.py:724-737 at 949a27ef). util/mcp_setup.bash now writes that variable into the entry's env. Each
mutant re-introduces one regression into a COPY of the staged files: an empty env, the env dropped, a capitalised
value (which Serena treats as "report"), a misnamed variable, a --check that ignores env, a write that keeps an older
entry's env, and a pin that no longer records the check made at its commit. The suite then runs against that copy, in
a scratch tree that mirrors the files it reads (it locates them relative to its own file).

A mutant is KILLED when the suite fails; the report names the tests that failed. The unmutated control must pass, or
the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once. Nothing in the repository
is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (a file changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py [--jobs N] [--only ID[,ID...]]
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
PIN = "conf/hosts/turing/mcp.json"
STAGED = (SCRIPT, "tests/test_mcp_setup.py", "tests/redacted_env.py", PIN, ".serena/project.yml", ".gitignore")
SUITE = "tests.test_mcp_setup"
SUITE_TIMEOUT = 600

ENV_LINE = '    "env": {"SERENA_USAGE_REPORTING": "false"},  # exactly "false": the only value Serena compares against\n'

# (mutant id, regression re-introduced, [(staged file, anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("U1", "the usage report is on: the entry's env is empty", [(SCRIPT, ENV_LINE, '    "env": {},\n')]),
    ("U2", "the entry has no env at all", [(SCRIPT, ENV_LINE, "")]),
    ("U3", "the value is capitalised, which Serena still treats as report", [(SCRIPT, '{"SERENA_USAGE_REPORTING": "false"},  #', '{"SERENA_USAGE_REPORTING": "False"},  #')]),
    ("U4", "the variable is misnamed", [(SCRIPT, '{"SERENA_USAGE_REPORTING": "false"},  #', '{"SERENA_USAGE_REPORT": "false"},  #')]),
    ("U5", "--check ignores env", [(SCRIPT, "    if current != entry:\n", '    if {k: v for k, v in current.items() if k != "env"} != {k: v for k, v in entry.items() if k != "env"}:\n')]),
    ("U6", "a write keeps an older entry's env", [(SCRIPT, '    servers["serena"] = entry\n', '    servers["serena"] = dict(entry, env=(servers.get("serena") or {}).get("env", entry["env"]))\n')]),
    ("U7", "the pin no longer records the usage-report check", [(PIN, "SERENA_USAGE_REPORTING is exactly the string false", "the report is off")]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, texts: dict[str, str] | None = None) -> None:
    """Mirror the files the suite reads (and a .git, so the tree is a checkout); optionally install a mutant."""
    for path in STAGED:
        dest = tree / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / path, dest)
    (tree / ".git").mkdir()
    for path, text in (texts or {}).items():
        (tree / path).write_text(text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(texts: dict[str, str] | None) -> tuple[bool, list[str], str]:
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw).resolve()
        stage(tree, texts)
        proc = subprocess.run([sys.executable, "-m", "unittest", SUITE], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, failed_tests(output), output


def mutate(originals: dict[str, str], edits: list[tuple[str, str, str]]) -> dict[str, str] | None:
    """The mutated text of each file an edit touches, or None when an anchor does not occur exactly once."""
    mutated: dict[str, str] = {}
    for path, anchor, replacement in edits:
        text = mutated.get(path, originals[path])
        if text.count(anchor) != 1:
            return None
        mutated[path] = text.replace(anchor, replacement)
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
    originals = {path: (REPO / path).read_text(encoding="utf-8") for path in (SCRIPT, PIN)}
    mutated: dict[str, dict[str, str]] = {}
    for mid, _, edits in chosen:
        texts = mutate(originals, edits)
        if texts is None or all(texts[path] == originals[path] for path in texts):
            print(f"ANCHOR {mid}: an anchor does not occur exactly once; update the mutant")
            return 2
        mutated[mid] = texts

    passed, failures, output = run_suite(None)
    if not passed:
        print(f"VOID   control: the suite fails on the unmutated files: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT} and {PIN}")

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
