#!/usr/bin/env python3
"""
Show the ml-code carrier's tests fail on main's code, and that every new deny rule and carried test file kills a mutant.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: BRIEF_COMMON_R2 rule 12 (non-vacuous tests; a code fix must be shown to fix);
         reference_mutation_check_stale_pyc_and_piped_exit.md (stale __pycache__, piped exit codes).

Usage: python3 2026-11-08_flood4r2_ml_code_swap_check.py <out dir> [--main-dir=DIR] [RUN_ID ...]
       (run from the worktree root)

Each run swaps ONE file: a BASELINE installs origin/main's copy (the carrier's tests then run against main's
code and must fail), a MUTANT replaces one exact string of the carrier's copy (it must occur once). With
--main-dir, main's copy of each file is read from DIR/<repo path> (saved with `git show <base>:<path>` from
another checkout) instead of `git show origin/main:<path>` here. Before
and after each run every __pycache__ under tests/ and util/ is deleted, and the test processes run with
PYTHONDONTWRITEBYTECODE=1, so no stale bytecode can mask a mutant. The file is restored byte-for-byte
in a finally block and its sha256 is compared with the original. Each unittest target is its own process;
the exit status is read from the process itself, never through a pipe.

Writes <out dir>/<run id>.log per run and <out dir>/swap_check.json.

Round 2 (2026-11-09, owner ruling "Carry in ml-code"): the s1-s14 mutants pin the brace sequence handling,
g11-g13 are re-anchored on the rewritten brace code, and base-guard also runs the credential-path and
privilege tables, which gained sequence rows. Run nothing else against the worktree meanwhile: the swap
edits the worktree's own files, and the older guard mutation checks re-read util/claude_agent_guard.py per
mutant.

Round 3 (2026-11-11): the brace scan became one pass (_brace_closes) and the words are counted before they are
built, so g11 and g13 are re-anchored on ``count * len(tack)`` and s13 on the pass's ``}`` step (a top-level
``}`` met before any separator ends the scan). util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_mutants.py runs this
list, the validator's and the scan's own in a COPY of the tree, so the worktree is never edited.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

GUARD = "util/claude_agent_guard.py"
CLAUDEY = "scripts/claude_interactive.bash"
WAKE = "scripts/wake_the_claude.bash"
PM = "util/fleet_triage/predict_merge.py"
GPG_TABLE = "tests.test_claude_agent_guard.BashRuleTests.test_gpg_secret_and_signing"
CRED_TABLE = "tests.test_claude_agent_guard.BashRuleTests.test_credential_paths_and_the_component_boundary"
PRIV_TABLE = "tests.test_claude_agent_guard.BashRuleTests.test_ssh_privilege_and_defaults"
GIT_ABBREV = "tests/test_claude_agent_guard_git_sign_abbrev.py"
PUSH_ABBREV = "tests/test_claude_agent_guard_push_signed_abbrev.py"
BRACE = "tests/test_claude_agent_guard_brace_cap.py"
EMPTY_ENV = "tests/test_claudey_empty_prompt_file_env.py"
LATER_FLAG = "tests/test_prompt_file_later_flag.py"
EFFORT_TRUE = "tests.test_wake_the_claude.WakeTheClaudeSecurityTests.test_effort_true_sends_the_max_default"
EFFORT_AUTO = "tests.test_wake_the_claude.WakeTheClaudeSecurityTests.test_effort_auto_sends_no_effort_flag"
PM_ENV = "tests/test_predict_merge_inherited_git_env.py"

BASELINES = [
    ("base-guard", GUARD, [BRACE, GIT_ABBREV, PUSH_ABBREV, GPG_TABLE, CRED_TABLE, PRIV_TABLE]),
    ("base-claudey", CLAUDEY, [EMPTY_ENV]),
    ("base-wake", WAKE, [LATER_FLAG, EFFORT_TRUE, EFFORT_AUTO]),
    ("base-predict-merge", PM, [PM_ENV]),
]

MUTANTS = [
    ("g1-gpg-floor-3", GUARD, "GPG_MIN_ABBREV = 2", "GPG_MIN_ABBREV = 3", [GPG_TABLE]),
    ("g2-gpg-floor-1", GUARD, "GPG_MIN_ABBREV = 2", "GPG_MIN_ABBREV = 1", [GPG_TABLE]),
    ("g3-gpg-sign-min-4", GUARD, '_git_long_abbrev(text, "gpg-sign", 1)', '_git_long_abbrev(text, "gpg-sign", 4)', [GIT_ABBREV]),
    ("g4-tag-sign-min-3", GUARD, '_git_long_abbrev(text, "sign", 2) or', '_git_long_abbrev(text, "sign", 3) or', [GIT_ABBREV]),
    ("g5-tag-local-user-min-3", GUARD, '_git_long_abbrev(text, "local-user", 2)', '_git_long_abbrev(text, "local-user", 3)', [GIT_ABBREV]),
    ("g7-push-min-1", GUARD, '_git_long_abbrev(text, "signed", 2)', '_git_long_abbrev(text, "signed", 1)', [PUSH_ABBREV]),
    ("g8-push-min-3", GUARD, '_git_long_abbrev(text, "signed", 2)', '_git_long_abbrev(text, "signed", 3)', [PUSH_ABBREV]),
    ("g9-push-value-case", GUARD, 'text.partition("=")[2].casefold() not in _PUSH_SIGNED_OFF', 'text.partition("=")[2] not in _PUSH_SIGNED_OFF', [PUSH_ABBREV]),
    # g10 was 'return separator == "" or ...' -> '== "x"': it SURVIVED as an equivalent mutant (a bare flag's value
    # is "", never an off value), so the redundant clause was removed from the guard and this mutant replaces it.
    ("g10-push-off-list-drops-0", GUARD, '_PUSH_SIGNED_OFF = ("false", "no", "off", "0")', '_PUSH_SIGNED_OFF = ("false", "no", "off")', [PUSH_ABBREV]),
    # g11-g13 re-anchored in round 2: brace_expand became bash 5.3's recursive expansion (_brace_words), and
    # _brace_range counts the terms of a stepped sequence.
    ("g11-brace-list-cap-plus-1", GUARD, "if count * len(tack) > limit:", "if count * len(tack) > limit + 1:", [BRACE]),
    ("g12-brace-range-off-by-one", GUARD, "if count > MAX_BRACE_ALTERNATIVES:", "if count > MAX_BRACE_ALTERNATIVES + 1:", [BRACE]),
    ("g13-brace-ignores-earlier-groups", GUARD, "if count * len(tack) > limit:", "if len(tack) > limit:", [BRACE]),
    # Round 2: brace sequence expressions (owner ruling "Carry in ml-code"). One mutant per new deny or refusal.
    ("s1-step-never-parsed", GUARD, r'(?:\.\.([+-]?[0-9]+))?")', r'(?:\.\.(x))?")', [BRACE, CRED_TABLE, PRIV_TABLE, GPG_TABLE]),
    ("s2-step-sign-kept", GUARD, "size = abs(int(step)) if step else 1", "size = int(step) if step else 1", [BRACE]),
    ("s3-zero-step-is-two", GUARD, "size = size or 1", "size = size or 2", [BRACE]),
    ("s4-no-zero-padding", GUARD, "width = max(len(lo), len(hi)) if padded else 0", "width = 0", [BRACE]),
    ("s5-minus-zero-pads-nothing", GUARD, '(len(side) > 2 and side[:2] == "-0")', '(len(side) > 3 and side[:2] == "-0")', [BRACE]),
    ("s6-plus-sign-not-a-number", GUARD, r"(?:([+-]?[0-9]+)\.\.([+-]?[0-9]+)|", r"(?:(-?[0-9]+)\.\.(-?[0-9]+)|", [BRACE]),
    ("s7-nested-sequence-not-refused", GUARD, 'if "{" in amble.replace("${", ""):', 'if "{{" in amble.replace("${", ""):', [BRACE]),
    ("s8-backslash-not-refused", GUARD, 'if "\\\\" in terms or "`" in terms:', 'if "`" in terms:', [BRACE]),
    ("s9-backtick-not-refused", GUARD, 'if "\\\\" in terms or "`" in terms:', 'if "\\\\" in terms:', [BRACE]),
    ("s10-operand-limit-plus-1", GUARD, "if any(abs(v) > BRACE_SEQ_OPERAND_LIMIT for v in numbers):", "if any(abs(v) > BRACE_SEQ_OPERAND_LIMIT + 1 for v in numbers):", [BRACE]),
    ("s11-intmax-plus-1-is-a-number", GUARD, "if any(v < -_INTMAX - 1 or v > _INTMAX for v in numbers):", "if any(v < -_INTMAX - 1 or v > _INTMAX + 1 for v in numbers):", [BRACE]),
    ("s12-step-not-counted", GUARD, "count = abs(b - a) // size + 1", "count = abs(b - a) + 1", [BRACE]),
    ("s13-first-brace-closes", GUARD, "shut, comma = j, False  # found stands", "shut, comma, found = j, False, None  # found stands", [BRACE]),
    ("s14-no-depth-guard", GUARD, "if depth > limit:  #", "if depth > limit * 1000:  #", [BRACE]),
    ("c1-empty-file-env", CLAUDEY, '"${CLAUDE_PROMPT_FILE+x}" == "x"', '"${CLAUDE_PROMPT_FILE+x}" == "y"', [EMPTY_ENV]),
    ("c2-empty-path-env", CLAUDEY, '"${CLAUDE_PROMPT_PATH+x}" == "x"', '"${CLAUDE_PROMPT_PATH+x}" == "y"', [EMPTY_ENV]),
    ("w1-later-file-keeps-prompt", WAKE, "--file good.md --file missing.md otherwise sent good.md and exited 0.\n            PROMPT_FILE=\"\"\n", "--file good.md --file missing.md otherwise sent good.md and exited 0.\n", [LATER_FLAG]),
    ("w2-later-path-keeps-prompt", WAKE, "--path good.md --path emptydir otherwise sent good.md and exited 0.\n                PROMPT_FILE=\"\"\n", "--path good.md --path emptydir otherwise sent good.md and exited 0.\n", [LATER_FLAG]),
    ("w3-effort-default-auto", WAKE, 'EFFORT_DEFAULT="${EFFORT_MAX}"', 'EFFORT_DEFAULT="${EFFORT_AUTO}"', [EFFORT_TRUE]),
    ("w4-auto-sends-flag", WAKE, '== "${EFFORT_AUTO}" ) ]]; then', '== "${EFFORT_AUTO}x" ) ]]; then', [EFFORT_AUTO]),
    ("w5-auto-case-sensitive", WAKE, '"${CLAUDE_EFFORT_VALUE[1],,}" == "${EFFORT_AUTO}"', '"${CLAUDE_EFFORT_VALUE[1]}" == "${EFFORT_AUTO}"', [EFFORT_AUTO]),
    ("p1-shallow-file-kept", PM, '"GIT_SHALLOW_FILE", "GIT_GRAFT_FILE",', '"GIT_GRAFT_FILE",', [PM_ENV]),
    ("p2-graft-file-kept", PM, '"GIT_SHALLOW_FILE", "GIT_GRAFT_FILE",', '"GIT_SHALLOW_FILE",', [PM_ENV]),
    ("p3-index-file-kept", PM, '"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",', '"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR",', [PM_ENV]),
]

_FAILED_RE = re.compile(r"^FAILED \((.*)\)$", re.MULTILINE)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clear_pycache(root: Path) -> None:
    for base in (root / "tests", root / "util"):
        for cache in base.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)


def run_targets(root: Path, targets: list, log) -> list:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    results = []
    for target in targets:
        proc = subprocess.run([sys.executable, "-m", "unittest", target], cwd=str(root), env=env, capture_output=True, text=True, timeout=1200, check=False)  # nosec B603 -- fixed argv
        text = proc.stdout + proc.stderr
        failed = _FAILED_RE.search(text)
        fail_lines = [line for line in text.splitlines() if line.startswith(("FAIL:", "ERROR:"))]
        log.write("=== %s (exit %d)\n%s\n" % (target, proc.returncode, text))
        results.append({"target": target, "exit": proc.returncode, "failed_summary": failed.group(1) if failed else "", "failing_cases": len(fail_lines), "first_failures": fail_lines[:6]})
    return results


def swap_run(root: Path, out: Path, run_id: str, rel: str, new_bytes: bytes, targets: list) -> dict:
    path = root / rel
    original = path.read_bytes()
    before = sha256(original)
    with open(out / (run_id + ".log"), "w", encoding="utf-8") as log:
        try:
            clear_pycache(root)
            path.write_bytes(new_bytes)
            results = run_targets(root, targets, log)
        finally:
            path.write_bytes(original)
            clear_pycache(root)
    after = sha256(path.read_bytes())
    if after != before:
        raise SystemExit("RESTORE FAILED for %s: %s != %s" % (rel, after, before))
    return {"id": run_id, "file": rel, "sha256_before": before, "sha256_after": after, "restored": True, "results": results, "any_failed": any(r["exit"] != 0 for r in results)}


def main(argv: list) -> int:
    root = Path.cwd().resolve()
    out = Path(argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    main_dirs = [arg.split("=", 1)[1] for arg in argv[2:] if arg.startswith("--main-dir=")]
    main_dir = Path(main_dirs[-1]).resolve() if main_dirs else None
    only = {arg for arg in argv[2:] if not arg.startswith("--main-dir=")}  # optional run ids: re-run just these (the report then holds only them)
    report = {"baselines": [], "mutants": [], "main_dir": str(main_dir) if main_dir else None}
    for run_id, rel, targets in BASELINES:
        if only and run_id not in only:
            continue
        if main_dir is not None:
            main_bytes = (main_dir / rel).read_bytes()
        else:
            main_bytes = subprocess.run(["git", "-C", str(root), "show", "origin/main:" + rel], capture_output=True, check=True).stdout  # nosec B603 B607
        row = swap_run(root, out, run_id, rel, main_bytes, targets)
        row["expect"] = "the carrier's tests FAIL against main's file"
        report["baselines"].append(row)
        print("%-30s %s  %s" % (run_id, "FAILS on main (fix shown)" if row["any_failed"] else "PASSES on main (NOT shown)", "; ".join("%s: %s" % (r["target"].split("/")[-1], r["failed_summary"] or "ok") for r in row["results"])))
    for run_id, rel, old, new, targets in MUTANTS:
        if only and run_id not in only:
            continue
        text = (root / rel).read_text(encoding="utf-8")
        if text.count(old) != 1:
            report["mutants"].append({"id": run_id, "file": rel, "error": "mutation anchor occurs %d times" % text.count(old)})
            print("%-30s ANCHOR COUNT %d (not run)" % (run_id, text.count(old)))
            continue
        row = swap_run(root, out, run_id, rel, text.replace(old, new).encode("utf-8"), targets)
        row.update({"old": old, "new": new, "verdict": "killed" if row["any_failed"] else "survived"})
        report["mutants"].append(row)
        print("%-30s %-8s %s" % (run_id, row["verdict"], "; ".join("%s: %s" % (r["target"].split("/")[-1], r["failed_summary"] or "ok") for r in row["results"])))
    (out / ("swap_check%s.json" % ("_partial" if only else ""))).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    survived = [m["id"] for m in report["mutants"] if m.get("verdict") != "killed"]
    shown = [b["id"] for b in report["baselines"] if not b["any_failed"]]
    ran = len(report["mutants"])
    print("mutants: %d run, %d killed; survived or not run: %s; baselines not shown: %s" % (ran, ran - len(survived), survived or "none", shown or "none"))
    return 0 if not survived and not shown else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
