"""
Show that the G1 suites kill a mutant for each way G-SEC's block-all firewall condition (task C2) can regress.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — investigation (suite strength evidence for C2's gate follow-up, owner ruling 2026-10-25)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2 C2 row, gate G-SEC of §9.3);
         util/host_state_probe.bash; util/host_state_check.py; tests/test_host_state_probe.py;
         tests/test_host_state_check.py; util/ad-hoc/2026-10-20_turing_g1_mutation_check.py (the engine this
         follows; its 57 mutants still apply, C12 among them)

The owner chose C2's block-all form on 2026-10-25: the application firewall on, blocking all incoming connections
while nothing inbound is needed. G-SEC's firewall condition used to pass at State = 1. It now also needs the probe's
new `socketfilterfw --getblockall` capture to report block all. Each mutant re-introduces one regression into a COPY
of the probe or the check: the pre-ruling condition, the disabled sentence read as on, an unknown state passing or
failing instead of going unjudged, an off firewall turned into an error, an on firewall passing an unreadable
capture, the --getblockall sentence not recognised, the old remediation text, an on firewall told to turn it on
again, the capture dropped from the probe, and stealth mode gated, which the design only reports. The G1 engine's
behavioural classes plus FirewallTest then run against that copy, in a scratch tree that mirrors the repo layout.

A mutant is KILLED when the suites fail; the report names the tests that failed. The unmutated control must pass,
or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once. Nothing in the
repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (a script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py [--jobs N] [--only ID[,ID...]]
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
PROBE = "util/host_state_probe.bash"
CHECK = "util/host_state_check.py"
STAGED = (PROBE, CHECK, "util/macvm_ctl.bash", "tests/test_host_state_probe.py", "tests/test_host_state_check.py", "tests/redacted_env.py")
CLASSES = (
    "tests.test_host_state_probe.UsageTest",
    "tests.test_host_state_probe.DocumentTest",
    "tests.test_host_state_probe.CaptureTest",
    "tests.test_host_state_probe.SecurityTest",
    "tests.test_host_state_probe.ToolsTest",
    "tests.test_host_state_probe.TextModeTest",
    "tests.test_host_state_check.GreenHostTest",
    "tests.test_host_state_check.FailureTest",
    "tests.test_host_state_check.FirewallTest",
    "tests.test_host_state_check.SectionTest",
    "tests.test_host_state_check.ExpectedValidationTest",
    "tests.test_host_state_check.ProbeDocumentTest",
    "tests.test_host_state_check.ParserTest",
    "tests.test_host_state_check.MacvmParityTest",
    "tests.test_host_state_check.ProbeContractTest",
)
SUITE_TIMEOUT = 900

UNKNOWN_RAISE = '    raise DataError(f"socketfilterfw --getblockall: no block-all state in {first_line(text)!r}")\n'
OFF_GUARD = "        if int(state) != 0:\n            raise\n"
ON_FIX = '_C2_FIX.format(steps="--setblockall on")'

# (mutant id, file, regression re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("B1", CHECK, "the pre-ruling condition: a firewall that is on passes without block all", [('        if blocks_all:\n            return Condition("firewall", "pass", message)\n', '        if True:\n            return Condition("firewall", "pass", message)\n')]),
    ("B2", CHECK, "the disabled sentence reads as block all", [("    if _BLOCKALL_OFF in text:\n        return False\n", "    if _BLOCKALL_OFF in text:\n        return True\n")]),
    ("B3", CHECK, "an unknown block-all state passes", [(UNKNOWN_RAISE, "    return True\n")]),
    ("B4", CHECK, "an unknown block-all state fails instead of going unjudged", [(UNKNOWN_RAISE, "    return False\n")]),
    ("B5", CHECK, "an off firewall errors when block all cannot be read", [(OFF_GUARD, "        raise\n")]),
    ("B6", CHECK, "a firewall that is on fails, not errors, when block all cannot be read", [(OFF_GUARD, "        pass\n")]),
    ("B7", CHECK, "--getblockall's own on-sentence is not recognised", [('r"(?:is set to block|is blocking) all non-essential incoming connections"', 'r"is blocking all non-essential incoming connections"')]),
    ("B8", CHECK, "the remediation keeps the pre-ruling wording", [('_C2_FIX = "task C2 (owner): sudo /usr/libexec/ApplicationFirewall/socketfilterfw {steps}', '_C2_FIX = "task C2 (owner): turn the application firewall on, with stealth mode, allowing signed software{steps}')]),
    ("B9", CHECK, "a firewall that is on is told to turn it on again", [(ON_FIX, '_C2_FIX.format(steps="--setglobalstate on, then --setblockall on and --setstealthmode on")')]),
    ("B10", PROBE, "the probe no longer captures --getblockall", [('    capture blockall "$SOCKETFILTERFW" --getblockall\n', "")]),
    ("B11", CHECK, "stealth mode is gated, which the design only reports", [('    message = "; ".join(parts)\n', '    message = "; ".join(parts)\n    if "stealth mode is off" in message:\n        return Condition("firewall", "fail", message, "stealth")\n')]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, rel: str | None = None, text: str | None = None) -> None:
    """Mirror the files the suites need; optionally replace one of them with a mutant."""
    for path in STAGED:
        dest = tree / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / path, dest)
    if rel is not None and text is not None:
        (tree / rel).write_text(text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(rel: str | None, text: str | None) -> tuple[bool, list[str], str]:
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw).resolve()
        stage(tree, rel, text)
        proc = subprocess.run([sys.executable, "-m", "unittest", *CLASSES], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
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
    originals = {rel: (REPO / rel).read_text(encoding="utf-8") for rel in (PROBE, CHECK)}
    mutated: dict[str, str] = {}
    for mid, rel, _, edits in chosen:
        text = mutate(originals[rel], edits)
        if text is None or text == originals[rel]:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {rel}; update the mutant")
            return 2
        mutated[mid] = text

    passed, failures, output = run_suite(None, None)
    if not passed:
        print(f"VOID   control: the suites fail on the unmutated scripts: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {len(CLASSES)} classes pass on the unmutated {PROBE} and {CHECK}")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, run_suite(mutant[1], mutated[mutant[0]])), chosen))

    killed = 0
    for (mid, _, defect, _), (survived, failures, _) in results:
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
