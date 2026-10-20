"""
Show that the G1 suites kill a mutant for each defect class they claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up G1 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1, gates of §9.3,
         regression R-G1); util/host_state_probe.bash; util/host_state_check.py; tests/test_host_state_probe.py;
         tests/test_host_state_check.py; util/ad-hoc/2026-10-20_turing_g5_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of the probe or the check. The probe defects include a
hung command that is never killed, stderr dropped, raw control characters in the JSON, a missing program
reported as found, an unbounded or symlink-blind key-export search, and public keys counted as loose.
The check defects include R-G1 dropped or off by one, an error that no longer wins over a failure,
G-MEM's arithmetic drifting from util/macvm_ctl.bash, a shadowed or dangling tool passing, another
machine's probe evaluated, and a failing probe trusted. Both suites' behavioural classes then run
against that copy, in a scratch tree that mirrors the repo layout (the suites locate the scripts
relative to their own files). The check suite imports the probe suite's harness and runs the real
probe, so both suites run for every mutant.

The classes that read this checkout's committed files (ThisCheckoutTest) or need real macOS tools
(RealHostTest) are left out: every mutant must be killed by the behavioural classes alone.

A mutant is KILLED when the suites fail; the report names the tests that failed. The unmutated control
must pass, or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at
once. Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate. M-P1 takes
about a minute: its hung stub runs until the suite's own limit.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (a script changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-20_turing_g1_mutation_check.py [--jobs N] [--only ID[,ID...]]
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
    "tests.test_host_state_check.SectionTest",
    "tests.test_host_state_check.ExpectedValidationTest",
    "tests.test_host_state_check.ProbeDocumentTest",
    "tests.test_host_state_check.ParserTest",
    "tests.test_host_state_check.MacvmParityTest",
    "tests.test_host_state_check.ProbeContractTest",
)
SUITE_TIMEOUT = 900

LOOSE_JSON = "run_capture \"$FIND\" \"$ssh_dir\" -maxdepth 1 -type f ! -name '*.pub' ! -name 'known_hosts*' ! -name 'authorized_keys*' \\( -perm -040 -o -perm -020 -o -perm -010 -o -perm -004 -o -perm -002 -o -perm -001 \\) -print"
EXPORTS_JSON = "run_capture \"$FIND\" \"${dirs[@]}\" -maxdepth 4 \\( -type f -o -type l \\) \\( -iname '*.asc' -o -iname '*recovery*' \\) -print"

# (mutant id, file, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("P1", PROBE, "a hung command is never killed", [('        if [[ "$ticks" -ge "$limit" ]]; then\n', "        if false; then\n")]),
    ("P2", PROBE, "a command's stderr is not captured", [('"$@" </dev/null >"$CAP_OUT" 2>"$CAP_ERR" &', '"$@" </dev/null >"$CAP_OUT" 2>/dev/null &')]),
    ("P3", PROBE, "control characters reach the JSON raw", [("s=\"$(tr -d '\\000-\\010\\013\\014\\016-\\037' <\"$1\"; printf X)\"", 's="$(cat "$1"; printf X)"')]),
    ("P4", PROBE, "backslashes are not escaped", [("    s=${s//\\\\/\\\\\\\\}\n", "")]),
    ("P5", PROBE, "a missing program counts as found", [('    if ! program_found "$1"; then\n', "    if false; then\n")]),
    ("P6", PROBE, "sections follow the command line, not the canonical order", [('    for name in "${ALL_SECTIONS[@]}"; do\n        case " ${WANT_SECTIONS[*]} " in', '    for name in "${WANT_SECTIONS[@]}"; do\n        case " ${WANT_SECTIONS[*]} " in')]),
    ("P7", PROBE, "a symlinked key export is missed", [(EXPORTS_JSON, EXPORTS_JSON.replace("\\( -type f -o -type l \\)", "-type f"))]),
    ("P8", PROBE, "the key-export search descends without limit", [(EXPORTS_JSON, EXPORTS_JSON.replace("-maxdepth 4 ", ""))]),
    ("P9", PROBE, "public keys count as loose", [(LOOSE_JSON, LOOSE_JSON.replace("! -name '*.pub' ", ""))]),
    ("P10", PROBE, "known_hosts counts as loose", [(LOOSE_JSON, LOOSE_JSON.replace("! -name 'known_hosts*' ", ""))]),
    ("P11", PROBE, "the other-execute bit is ignored", [(LOOSE_JSON, LOOSE_JSON.replace(" -o -perm -001", ""))]),
    ("P12", PROBE, "a dangling link counts as executable", [('        if [[ -f "$entry" && -x "$entry" ]]; then\n', '        if [[ -e "$entry" || -L "$entry" ]]; then\n')]),
    ("P13", PROBE, "a repeated tool is resolved twice", [('        *" ${tool} "*) ;;\n', "")]),
    ("P14", PROBE, "--tool takes any string", [("    [[ \"$tool\" =~ $tool_re ]] || die_usage \"not a tool name: '${tool}'\"\n", "    :\n")]),
    ("P15", PROBE, "the alias check is not given the root", [('capture check "$PYTHON" "$ALIAS_CHECK" --json --root "$ROOT"', 'capture check "$PYTHON" "$ALIAS_CHECK" --json')]),
    ("P16", PROBE, "the preflight checks the caller's directory", [('capture preflight "${BASH:-bash}" "$SIGNING_PREFLIGHT" --repo "$REPO_DIR"', 'capture preflight "${BASH:-bash}" "$SIGNING_PREFLIGHT"')]),
    ("P17", PROBE, "an unresolved tool path prints as an empty string", [("    if [[ -n \"$1\" ]]; then json_string \"$1\"; else printf 'null'; fi\n", '    json_string "$1"\n')]),
    ("P18", PROBE, "a missing program reports exit 0", [("    printf '%s' \"${CAP_RC:-null}\"\n", "    printf '%s' \"${CAP_RC:-0}\"\n")]),
    ("P19", PROBE, "bash's kill notice reaches stderr", [("    } 2>/dev/null\n}\n", "    }\n}\n")]),
    ("P20", PROBE, "an unset HOME is not refused", [('[[ -n "${HOME:-}" ]] || die_env "HOME is not set"\n', ":\n")]),
    ("P21", PROBE, "--timeout has no upper bound", [('[[ "$TIMEOUT" =~ $timeout_re ]] && [[ "$TIMEOUT" -le 3600 ]] ||', '[[ "$TIMEOUT" =~ $timeout_re ]] ||')]),
    ("P22", PROBE, "a capture drops its trailing newlines", [('    json_string "${s%X}"\n', "    json_string \"$(printf '%s' \"${s%X}\")\"\n")]),
    ("P23", PROBE, "the vm section ignores --vm", [('capture showvminfo "$VBOXMANAGE" showvminfo "$VM" --machinereadable', 'capture showvminfo "$VBOXMANAGE" showvminfo juniper-macvm --machinereadable')]),
    ("C1", CHECK, "R-G1 refuses a VM that exactly fills the headroom", [("    if (mem_gib + reserve) * GIB > memsize:\n", "    if (mem_gib + reserve) * GIB >= memsize:\n")]),
    ("C2", CHECK, "R-G1's memory check is gone", [("    if (mem_gib + reserve) * GIB > memsize:\n", "    if False:\n")]),
    ("C3", CHECK, "R-G1's vCPU check is gone", [("    if vcpus > physical:\n", "    if False:\n")]),
    ("C4", CHECK, "an error no longer wins over a failure", [('    if "error" in statuses:\n        return 2\n    if "fail" in statuses:\n        return 1\n    return 0\n\n\ndef summary_line', '    if "fail" in statuses:\n        return 1\n    if "error" in statuses:\n        return 2\n    return 0\n\n\ndef summary_line')]),
    ("C5", CHECK, "the report exits non-zero on a failure", [("    if not check:\n        return 0\n    statuses = {c.status", "    statuses = {c.status")]),
    ("C6", CHECK, "speculative pages are not counted", [("avail = (free + spec + inactive) * page // MIB", "avail = (free + inactive) * page // MIB")]),
    ("C7", CHECK, "exactly enough memory fails", [("        if avail >= need:\n", "        if avail > need:\n")]),
    ("C8", CHECK, "swap rounds down", [("return math.ceil(value * factor), token", "return math.floor(value * factor), token")]),
    ("C9", CHECK, "swap at the limit fails", [("        if used <= limit:\n", "        if used < limit:\n")]),
    ("C10", CHECK, "pgrep's no-match counts as running", [('            if cap.get("rc") == 0:\n                running.append', '            if cap.get("rc") in (0, 1):\n                running.append')]),
    ("C11", CHECK, "the registered VM's larger memory is ignored", [("    if conf and int(conf.group(1)) > mib:\n", "    if False:\n")]),
    ("C12", CHECK, "a firewall in state 1 fails", [("    if int(state) >= 1:\n", "    if int(state) >= 2:\n")]),
    ("C13", CHECK, "SIP's custom configuration passes", [('    if word == "enabled":\n        return Condition("sip"', '    if word in ("enabled", "unknown"):\n        return Condition("sip"')]),
    ("C14", CHECK, "key exports at rest pass", [('    if not paths:\n        return Condition("key-exports", "pass"', '    if True:\n        return Condition("key-exports", "pass"')]),
    ("C15", CHECK, "a tool shadowed on PATH passes", [('        elif rec.get("path") != entry:\n', "        elif False:\n")]),
    ("C16", CHECK, "a dangling local-bin link passes", [('        elif not lb.get("executable"):\n', "        elif False:\n")]),
    ("C17", CHECK, "kubectl ahead of the cluster passes", [("    if abs(gap) <= skew:\n", "    if gap <= skew:\n")]),
    ("C18", CHECK, "an unnamed conda env goes unnamed", [('        if path.parent.name == "envs":\n', "        if False:\n")]),
    ("C19", CHECK, "a drifted parent AGENTS.md passes", [("    if digest != want:\n", "    if False:\n")]),
    ("C20", CHECK, "another adapter on the interface passes", [('    if mac and iface.get("ether") != mac:\n', "    if False:\n")]),
    ("C21", CHECK, "a link below the expected media passes", [('    if iface.get("status") == "active" and cfg["media"] in (iface.get("media") or ""):\n', '    if iface.get("status") == "active":\n')]),
    ("C22", CHECK, "a missing I-SIGN record file passes", [('    if not (ctx.record_base / rec["record"]).is_file():\n        return Condition("integration"', '    if False:\n        return Condition("integration"')]),
    ("C23", CHECK, "another machine's probe is evaluated", [("    if wrong:\n        raise IdentityError", "    if False:\n        raise IdentityError")]),
    ("C24", CHECK, "the agent-session preflight (exit 1) is an error", [('text = stdout_of(cap, "util/headless_signing_preflight.bash", (0, 1))', 'text = stdout_of(cap, "util/headless_signing_preflight.bash", (0,))')]),
    ("C25", CHECK, "an origin rewritten by --fix fails", [('            if status in ("pass", "fixed"):\n', '            if status == "pass":\n')]),
    ("C26", CHECK, "a saved probe without the section is evaluated", [('    if missing:\n        raise ProbeError(f"{source} lacks', '    if False:\n        raise ProbeError(f"{source} lacks')]),
    ("C27", CHECK, "--section is case-sensitive", [("    name = value.strip().upper()\n", "    name = value.strip()\n")]),
    ("C28", CHECK, "an unknown expected.yaml key passes", [("    if unknown:\n        raise ExpectedError", "    if False:\n        raise ExpectedError")]),
    ("C29", CHECK, "a boolean counts as a number", [("if not isinstance(value, int) or isinstance(value, bool) or value < minimum:", "if not isinstance(value, int) or value < minimum:")]),
    ("C30", CHECK, "a record path may climb out of the repository", [('if path.startswith("/") or ".." in Path(path).parts:', 'if path.startswith("/"):')]),
    ("C31", CHECK, "the probe is not told the tools", [('    for tool in tools:\n        argv += ["--tool", tool]\n', "    for tool in tools:\n        pass\n")]),
    ("C32", CHECK, "a failing probe is trusted", [("    if proc.returncode != 0:\n        err = first_line", "    if False:\n        err = first_line")]),
    ("C33", CHECK, "a preflight FAIL line passes", [('            elif lines[cid][0] == "PASS":\n', '            elif lines[cid][0] in ("PASS", "FAIL"):\n')]),
    ("C34", CHECK, "an unrecorded hash reads as a mismatch", [('    if want is None:\n        return Condition("parent-agents-md", "fail"', '    if False:\n        return Condition("parent-agents-md", "fail"')]),
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
