"""
Show that G1's two suites kill a mutant for each defect class they claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up G1 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1, the gates of §9.3,
         regression R-G1); util/host_state_probe.bash and tests/test_host_state_probe.py; util/host_state_check.py and
         tests/test_host_state_check.py; util/ad-hoc/2026-10-20_turing_g5_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of the probe or the checker. On the probe side the
classes are:
- JSON escaping that keeps a backslash, tab, CR or control character raw;
- a timeout that never fires, and a missing program that reads as exit 1 (bash 3.2);
- a key-material or loose-mode listing that misses a class of file;
- a capture that prints key contents;
- an ignored ``--section`` or ``--vm``;
- a skipped capture with an exit code, and a failed command that aborts the probe.
On the checker side they are:
- status precedence;
- the exit codes;
- every boundary in G-MEM, and G-MEM drifting from util/macvm_ctl.bash's arithmetic;
- the kubectl skew;
- a ``~/.local/bin`` check that a lookalike path passes;
- the D11 failure line being judged;
- a null hash or address that passes;
- the MAC, host and unknown-key guards;
- path-only conda env names;
- ``--section``, and the argv the probe gets.

The behavioural test classes then run in a scratch tree that mirrors the repo layout, because each suite
locates its script relative to its own file. The static classes are left out (the probe's StaticTest,
the checker's CommittedExpectedTest and ScriptTest), so a mutant cannot be "killed" by shellcheck or a
docstring needle alone.

A mutant is KILLED when its suite fails; the report names the failing tests. Both unmutated controls
must pass, or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at
once. Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate. Run it on
macOS: mutant P6 is a bash 3.2 defect, and the probe suite runs under ``/bin/bash``.

Exit codes:
    0  every mutant was killed and both controls passed
    1  a mutant survived, or a control failed
    2  a mutant's anchor text did not occur exactly once (the script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-20_turing_g1_mutation_check.py [--jobs N] [--only ID ...]
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
PROBE_SUITE = ("tests/test_host_state_probe.py", ("JsonContractTest", "FailureCaptureTest", "CredentialSafetyTest", "ToolchainTest", "OptionsTest"))
CHECK_SUITE = (
    "tests/test_host_state_check.py",
    ("TuringTodayTest", "AliasGateTest", "SignGateTest", "SecGateTest", "ToolsGateTest", "EnvGateTest", "NetGateTest", "MemGateTest", "MacvmCtlAgreementTest", "CommandLineTest", "ProbeRunTest"),
)
STAGED_GLOBS = (
    PROBE,
    CHECK,
    "util/macvm_ctl.bash",
    "tests/test_host_state_probe.py",
    "tests/test_host_state_check.py",
    "tests/redacted_env.py",
    "conf/hosts/turing/*.yml",
    "conf/hosts/turing/*.yaml",
    "conf/hosts/turing/conda-envs/*.yml",
    "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md",
)
SUITE_TIMEOUT = 900

# (mutant id, file, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("P1", PROBE, "a backslash is not escaped", [(r'if (c == "\\") printf "%s", "\\\\"', r'if (c == "\\") printf "%s", c')]),
    ("P2", PROBE, "C0 control characters are kept raw", [(r'else if (c >= " ") printf "%s", c', r'else printf "%s", c')]),
    ("P3", PROBE, "a tab is not escaped", [(r'else if (c == "\t") printf "%s", "\\t"', r'else if (c == "\t") printf "%s", c')]),
    ("P4", PROBE, "a CR is not escaped", [(r'else if (c == "\r") printf "%s", "\\r"', r'else if (c == "\r") printf "%s", c')]),
    ("P5", PROBE, "the timeout never fires", [('        if [[ "$waited" -ge "$limit" ]]; then\n', "        if false; then\n")]),
    ("P6", PROBE, "a missing program reads as exit 1 (bash 3.2)", [('    if ! command -v "$1" >/dev/null 2>&1; then\n', "    if false; then\n")]),
    ("P7", PROBE, "recovery-code files are not listed", [(' -o -iname "*recovery*"', "")]),
    ("P8", PROBE, "*.pub files count as loose keys", [('! -name "*.pub" ', "")]),
    ("P9", PROBE, "group bits are ignored", [("-perm -040 -o -perm -020 -o -perm -010 -o ", "")]),
    ("P10", PROBE, "key-material-names prints file contents", [('"(" -name "*.asc" -o -iname "*recovery*" ")" -print', '"(" -name "*.asc" -o -iname "*recovery*" ")" -exec head -c 64 {} +')]),
    ("P11", PROBE, "--section is ignored", [('    if [[ -z "$WANT" ]]; then\n        SECTIONS=', "    if true; then\n        SECTIONS=")]),
    ("P12", PROBE, "a skipped capture carries exit code 0", [('\'"exit_code": null, "timed_out": false, "skipped": %s, \'', '\'"exit_code": 0, "timed_out": false, "skipped": %s, \'')]),
    ("P13", PROBE, "a usage error exits 1", [('    echo "Run with --help for usage." >&2\n    exit 2\n', '    echo "Run with --help for usage." >&2\n    exit 1\n')]),
    ("P14", PROBE, "--tool duplicates are kept", [('        *" $t "*) ;;\n', '        *" $t "*) TOOLS="$TOOLS $t" ;;\n')]),
    ("P15", PROBE, "--vm is ignored", [('showvminfo "$VM" --machinereadable', "showvminfo juniper-macvm --machinereadable")]),
    ("P16", PROBE, "a failing command aborts the probe", [('    wait "$pid" 2>/dev/null || rc=$?\n', '    wait "$pid" 2>/dev/null\n')]),
    ("P17", PROBE, "stderr is dropped", [('    err="$(<"${TMP_DIR}/err")"\n', '    err=""\n')]),
    ("C1", CHECK, "an unknown outranks a known failure", [('for status in ("fail", "unknown", "operator"):', 'for status in ("unknown", "fail", "operator"):')]),
    ("C2", CHECK, "--check exits 1 on an unknown gate", [('    if counts["unknown"]:\n        return 2\n', '    if counts["unknown"]:\n        return 1\n')]),
    ("C3", CHECK, "report mode exits 1 on a failure", [("    if not check:\n        return 0\n", '    if not check:\n        return 1 if counts["fail"] else 0\n')]),
    ("C4", CHECK, "vm-fits fails at exact fit (R-G1 boundary)", [("if vm_mib + reserve_mib > memsize_mib:", "if vm_mib + reserve_mib >= memsize_mib:")]),
    ("C5", CHECK, "memory fails at exact need", [("if avail_mib >= need_mib else", "if avail_mib > need_mib else")]),
    ("C6", CHECK, "swap rounds down", [("return math.ceil(mib), token", "return math.floor(mib), token")]),
    ("C7", CHECK, "a larger configured VM is ignored", [("if conf and int(conf.group(1)) > vm_mib:", "if False:")]),
    ("C8", CHECK, "pgrep's 'no match' reads as an error", [('elif cap["exit_code"] != 1:', 'elif cap["exit_code"] != 0:')]),
    ("C9", CHECK, "kubectl one minor off fails", [('skew <= want["max_skew"]', 'skew < want["max_skew"]')]),
    ("C10", CHECK, "a lookalike tool outside ~/.local/bin passes", [("elif os.path.normpath(path) != want:", "elif os.path.basename(path) != tool:")]),
    ("C11", CHECK, "the D11 commit-gpgsign line is judged", [('PREFLIGHT_JUDGED = ("pinentry", "agent-socket", "external-cache")', 'PREFLIGHT_JUDGED = ("pinentry", "agent-socket", "external-cache", "commit-gpgsign")')]),
    ("C12", CHECK, "an unrecorded parent hash passes", [('    if want is None:\n        return Condition("parent-agents-md", "fail"', '    if want is None:\n        return Condition("parent-agents-md", "pass"')]),
    ("C13", CHECK, "an unrecorded reserved address passes", [('if net["reserved_ip"] is None:\n        conditions.append(Condition("address", "fail"', 'if net["reserved_ip"] is None:\n        conditions.append(Condition("address", "pass"')]),
    ("C14", CHECK, "the bridge NIC's MAC is not checked", [('if ether != nic["mac"].lower():', "if False:")]),
    ("C15", CHECK, "absent key directories read as unknown", [("        return Condition(label, \"pass\", absent)\n", "        return Condition(label, \"unknown\", absent)\n")]),
    ("C16", CHECK, "firewall State 2 fails", [("elif int(match.group(1)) >= 1:", "elif int(match.group(1)) == 1:")]),
    ("C17", CHECK, "a probe from another host is accepted", [("if probe_host and probe_host != host:", "if False:")]),
    ("C18", CHECK, "an unknown expected.yaml key is accepted", [("    if set(doc) - allowed:\n", "    if False:\n")]),
    ("C19", CHECK, "a path-only conda env is not counted", [('if os.path.basename(parent) == "envs" and base:', "if False:")]),
    ("C20", CHECK, "--section is ignored", [("specs = [spec for spec in GATES if args.section is None or spec in args.section]", "specs = list(GATES)")]),
    ("C21", CHECK, "SIP's custom configuration passes", [('Condition("sip", "pass" if value == "enabled" else "fail"', 'Condition("sip", "pass" if value != "disabled" else "fail"')]),
    ("C22", CHECK, "the probe gets no --tool", [('        argv += ["--tool", tool]\n', "        pass\n")]),
    ("C23", CHECK, "the probe gets no --section", [('        argv += ["--section", section]\n', "        pass\n")]),
    ("C24", CHECK, "G-MEM's arithmetic drifts from macvm_ctl.bash", [("avail_mib = (free + spec + inactive) * size // MIB", "avail_mib = (free + 2 * spec + inactive) * size // MIB")]),
    ("C25", CHECK, "the owner's fix is dropped from a G2 failure", [("fix = f\" -- fix: {verdict['remediation']}\" if verdict.get(\"remediation\") else \"\"", 'fix = ""')]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, rel: str | None = None, text: str | None = None) -> None:
    """Mirror the files the suites need; optionally replace one file with a mutant."""
    for pattern in STAGED_GLOBS:
        for src in sorted(REPO.glob(pattern)):
            dest = tree / src.relative_to(REPO)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    if rel is not None:
        (tree / rel).write_text(text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(suite: tuple[str, tuple[str, ...]], rel: str | None = None, text: str | None = None) -> tuple[bool, list[str], str]:
    path, classes = suite
    module = path[:-3].replace("/", ".")
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw)
        stage(tree, rel, text)
        proc = subprocess.run([sys.executable, "-m", "unittest", *(f"{module}.{cls}" for cls in classes)], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
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
    parser.add_argument("--only", nargs="+", metavar="ID", help="run only these mutants")
    args = parser.parse_args()

    chosen = [m for m in MUTANTS if not args.only or m[0] in args.only]
    mutated: dict[str, str] = {}
    for mid, rel, _, edits in chosen:
        original = (REPO / rel).read_text(encoding="utf-8")
        text = mutate(original, edits)
        if text is None or text == original:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {rel}; update the mutant")
            return 2
        mutated[mid] = text

    for suite in (PROBE_SUITE, CHECK_SUITE):
        passed, failures, output = run_suite(suite)
        if not passed:
            print(f"VOID   control: {suite[0]} fails unmutated: {', '.join(failures) or 'see output'}")
            print(output[-4000:])
            return 1
        print(f"OK     control: {suite[0]} ({len(suite[1])} classes) passes unmutated")

    def one(mutant):
        mid, rel, _, _ = mutant
        return mutant, run_suite(PROBE_SUITE if rel == PROBE else CHECK_SUITE, rel, mutated[mid])

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(one, chosen))

    killed = 0
    for (mid, rel, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {Path(rel).name}: {defect}")
            continue
        killed += 1
        shown = ", ".join(failures[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {Path(rel).name}: {defect} -- {len(failures)} failing test(s): {shown}")

    print(f"\n{killed} of {len(chosen)} mutants killed")
    return 0 if killed == len(chosen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
