"""
Show that the B7 suite kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up B7 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task B7;
         regressions R-B7a, R-B7b; decision D11); util/headless_signing_preflight.bash;
         tests/test_headless_signing_preflight.py

Each mutant re-introduces one defect into a COPY of the preflight: an unpinned signing key that
passes, a curses pinentry that passes, a skipped socket test, an ignored D11 override, and so on.
The suite then runs against that copy in a scratch tree that mirrors the repo layout (the suite
locates the script relative to its own file). A mutant is KILLED when the suite fails. Each mutant
also names its pin: the test written for that defect, which must kill the mutant on its own, so a
regression id (R-B7a, R-B7b) is not carried by some other case. The unmutated control must pass,
or the run is void.

Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes: 0 every mutant killed, by the suite and by its pin, and the control passed; 1 a mutant
survived either, or the control failed; 2 a mutant's anchor text was not found exactly once (the
script changed; update the mutant).

Usage:
    python3 util/ad-hoc/2026-10-17_turing_b7_mutation_check.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/headless_signing_preflight.bash"
SUITE = "tests/test_headless_signing_preflight.py"

# (mutant id, defect re-introduced, pin test, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("B1", "R-B7a: an unpinned user.signingkey passes", "SigningKeyTest.test_r_b7a_signingkey_without_the_pin_fails", [("    elif [[ \"$key\" != *'!' ]]; then", "    elif false; then")]),
    ("B2", "the signing key is read from the global config only", "SigningKeyTest.test_repository_config_overrides_a_pinned_global_key", [("config --get user.signingkey", "config --global --get user.signingkey")]),
    ("B3", "R-B7b: a curses pinentry passes", "PinentryTest.test_r_b7b_terminal_pinentries_fail", [('    case "$base" in\n        curses | tty | emacs)', '    case "$base" in\n        tty | emacs)')]),
    ("B4", "R-B7b: a GUI build that falls back to curses passes", "PinentryTest.test_gui_build_that_falls_back_to_curses_fails", [('    case "$fallback" in', '    case "" in')]),
    ("B5", "the pinentry is looked up on PATH, which gpg-agent never searches", "PinentryTest.test_unset_pinentry_program_uses_gnupgs_default_not_path", [('    if [[ -n "$PINENTRY" ]]; then\n        prog="$PINENTRY"', '    if prog="$(command -v pinentry)"; then\n        prog="${prog}"')]),
    ("B6", "the probe asks for a PIN", "HappyPathTest.test_probe_sends_only_getinfo_flavor_and_bye", [(r"printf 'GETINFO flavor\nBYE\n'", r"printf 'GETINFO flavor\nGETPIN\nBYE\n'")]),
    ("B7", "the probe is not bounded by --timeout", "PinentryTest.test_a_hanging_pinentry_is_stopped_by_the_timeout", [('        if [[ "$ticks" -ge "$limit" ]]; then', "        if false; then")]),
    ("B8", "the socket test is skipped", "AgentSocketTest.test_missing_socket_fails", [('    if [[ -S "$AGENT_SOCKET" ]]; then', "    if true; then")]),
    ("B9", "a regular file passes as the agent socket", "AgentSocketTest.test_a_regular_file_is_not_a_socket", [('    if [[ -S "$AGENT_SOCKET" ]]; then', '    if [[ -e "$AGENT_SOCKET" ]]; then')]),
    ("B10", "a commented-out conf line counts", "ExternalCacheTest.test_commented_out_line_does_not_count", [('{ sub(/\\r$/, ""); sub(/^[ \\t]+/, "") }', '{ sub(/\\r$/, ""); sub(/^[ \\t#]+/, "") }')]),
    ("B11", "the first pinentry-program line wins", "PinentryTest.test_configuration_parsing", [("            val = v\n", "            if (!hit) val = v\n")]),
    ("B12", "D11: the GIT_CONFIG_COUNT override is ignored", "CommitGpgsignTest.test_d11_override_fails_with_the_d11_message", [('    if [[ -n "$override" ]]; then\n        report FAIL commit-gpgsign', '    if false; then\n        report FAIL commit-gpgsign')]),
    ("B13", "an unset commit.gpgsign passes", "CommitGpgsignTest.test_commit_gpgsign_not_true_fails_without_the_d11_message", [('    elif [[ "$effective" == "true" ]]; then', '    elif [[ "$effective" != "false" ]]; then')]),
    ("B14", "GNUPGHOME is ignored in favour of gpgconf", "HomedirTest.test_gnupghome_wins_over_gpgconf", [('if [[ -n "${GNUPGHOME:-}" ]]; then', "if false; then")]),
    ("B15", "--require-signed-head has no effect", "HeadSignatureTest.test_require_signed_head_fails_an_unsigned_head", [("        REQUIRE_SIGNED_HEAD=1\n", "        REQUIRE_SIGNED_HEAD=0\n")]),
    ("B16", "the run stops at the first failure", "AllFailuresListedTest.test_every_failure_is_reported_and_listed", [('            FAILURES+=("$2: $3")\n', '            FAILURES+=("$2: $3")\n            echo "RESULT: FAILED -- ${#FAILURES[@]} of ${CHECKS} checks failed:" >&2\n            exit 1\n')]),
    ("B17", "a failed check still exits 0", "AllFailuresListedTest.test_every_failure_is_reported_and_listed", [("} >&2\nexit 1\n", "} >&2\nexit 0\n")]),
    ("B18", "an unknown option is ignored", "UsageAndEnvironmentTest.test_bad_arguments_exit_2_before_any_tool_runs", [('            die_usage "unknown option: $1"', "            shift")]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)
SUITE_MODULE = SUITE.removesuffix(".py").replace("/", ".")


def stage(tmp: Path) -> None:
    """Mirror the files the suite needs: the suite, the env helper and the script."""
    for rel in (SCRIPT, SUITE, "tests/redacted_env.py"):
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, target: str) -> tuple[bool, str]:
    """(passed, first failing test) for a suite path or a dotted test id. Fail-fast: one failure kills."""
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-f", target],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=900,
    )
    match = FIRST_FAILURE.search(proc.stderr)
    # unittest names a failure "test_x (tests.test_module.SomeTest.test_x)"; keep "SomeTest.test_x".
    first = f"{match.group(3).split('.')[-2]}.{match.group(2)}" if match else "-"
    return proc.returncode == 0, first


def main() -> int:
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    for mid, _, _, edits in MUTANTS:
        for anchor, _ in edits:
            if original.count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {original.count(anchor)} times in {SCRIPT} (need exactly 1)")
                return 2

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        passed, first = run_tests(tmp, SUITE)
        if not passed:
            print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT} (first failure: {first})")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}")

        survivors = 0
        pins_missed = 0
        for mid, defect, pin, edits in MUTANTS:
            mutated = original
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / SCRIPT).write_text(mutated, encoding="utf-8")
            try:
                suite_passed, first = run_tests(tmp, SUITE)
                pin_passed, _ = run_tests(tmp, f"{SUITE_MODULE}.{pin}")
            finally:
                (tmp / SCRIPT).write_text(original, encoding="utf-8")
            survivors += 1 if suite_passed else 0
            pins_missed += 1 if pin_passed else 0
            verdict = "SURVIVED" if suite_passed else "KILLED"
            pin_note = "PIN MISSED" if pin_passed else "pin kills it"
            print(f"{verdict:8} {mid:4} {defect}\n                first failure: {first}; {pin_note}: {pin}")

    total = len(MUTANTS)
    print(f"\n{total - survivors} of {total} mutants killed by the suite; {total - pins_missed} of {total} by their own pin test alone")
    return 0 if survivors == 0 and pins_missed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
