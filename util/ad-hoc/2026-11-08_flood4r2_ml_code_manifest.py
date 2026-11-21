#!/usr/bin/env python3
"""
Assemble the ml-code carrier's manifest.json from the worktree's status and the recorded check and mutant runs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: BRIEF_COMMON_R2 DELIVERABLES (manifest.json shape).

Usage: python3 2026-11-08_flood4r2_ml_code_manifest.py <scratch dir> <checks.json>   (run from the worktree root)

The file list comes from `git status --porcelain` (tmp/ is gitignored, so scratch never appears); the
mutation rows come from <scratch dir>/swap2/swap_check.json; the carried rows and open questions are the
builder's, kept here verbatim so the manifest can be regenerated.
"""
import json
import subprocess
import sys
from pathlib import Path

HEADS = {
    2485: ("a185accfc76ffdcf2fe7dc07f049d803f7f48f45", "test(guard): pin gpg long-option abbreviations at 4 characters"),
    2493: ("3051f53e635aed7e5b6bc8f2ee16693a6b355004", "fix(guard): deny GnuPG abbreviations that actually sign"),
    2494: ("03db661f5ba0966917da6a9cbf0a22dcb33b920e", "docs(fleet): record shallow-cut, filter, and GIT_DIR rules for predict_merge"),
    2502: ("fd67bfe40b58fbca1b11b4d912ec61b9753df9a7", "fix(guard): deny git signing abbreviations that actually sign"),
    2504: ("796c91055555e2178289d9b6861d57a809bff5d6", "fix(launchers): refuse an empty prompt-file environment variable"),
    2505: ("699c176e0a514b2afbc85fceb2d82447da3f4c5c", "fix(launchers): a later unresolved prompt file does not send the earlier one"),
    2508: ("76da05c17af20b48cc1670a393c65478127c2923", "fix(guard): deny a signed push requested by a --signed prefix"),
    2513: ("08d00c523ce3f5cdd4da270d18a25b0281406bed", "fix(fleet-triage): drop inherited GIT_SHALLOW_FILE and GIT_GRAFT_FILE"),
}

CARRIED = {
    2493: {
        "taken": ["util/claude_agent_guard.py: GPG_MIN_ABBREV 4 -> 2 with its comment, and the _gpg_option docstring (own hunks, verbatim)", "tests/test_claude_agent_guard.py: the six GPG_CASES rows (verbatim)"],
        "fixes": ["the GPG-SIGN rule description now names the two-letter prefixes (--cl, --ls)", "a self-test case (gpg --cl)", "re-derived on GnuPG 2.4.8: --cl, --cle, --ls, --lsi and --det give stderr identical to clear-sign / lsign-key / detach-sign, and every one-letter prefix of a denied option is ambiguous"],
        "dropped": [],
        "outcome": "carried",
        "reason": "6 GPG_CASES rows fail on main; the claims hold on GnuPG 2.4.8",
    },
    2485: {
        "taken": ["the floor-pinning intent: one letter allowed, two letters denied, --export allowed exactly, --expo denied, --list=keys / --LIST / --clea denied (13 rows in GPG_CASES of tests/test_claude_agent_guard.py)"],
        "fixes": ["rewritten for the two-letter floor: as submitted it asserted gpg --cle / --lis / --exp allowed; GnuPG 2.4.8 runs --cle as clear-sign"],
        "dropped": ["tests/test_claude_agent_guard_gpg_abbrev.py (its own subprocess harness duplicated GuardHarness; no new suite)", "its ci.yml and docs/REFERENCE.md registration hunks (no suite to register)"],
        "outcome": "rewritten",
        "reason": "the pins it wanted, at the floor #2493 sets and re-derived on GnuPG 2.4.8",
    },
    2502: {
        "taken": ["util/claude_agent_guard.py: _git_long_abbrev and the commit/tag call sites (own hunks)", "tests/test_claude_agent_guard_git_sign_abbrev.py (head blob)", "ci.yml registration comment"],
        "fixes": ["version claims: re-derived on git 2.53.0 (the draft cites 2.43)", "git tag --si= moved out of TAG_SIGNING into DENIED_NOT_RUN: git refuses it (option `sign' takes no value); cherry-pick / revert --gpg added there (git 2.53 prints the usage)", "docstring: the signing program is called (stub), not 'writes a signature'; rebase/am/pull/commit-tree named", "a docs/REFERENCE.md Test Suite Reference entry (the draft registered the suite without one)", "a self-test case (git commit --g)"],
        "dropped": ["CHANGELOG and REFERENCE stamp hunks (rebuilt on main)"],
        "outcome": "carried-with-fix",
        "reason": "21 of its cases (19 as drafted + 2 added) fail on main; claims hold on git 2.53.0 except tag --si=",
    },
    2508: {
        "taken": ["util/claude_agent_guard.py: _PUSH_SIGNED_OFF, _git_push_requests_signature, the push call site and the rule description (own hunks)", "tests/test_claude_agent_guard_push_signed_abbrev.py (head blob)", "the two self-test cases"],
        "fixes": [
            "unified with #2502: _git_push_requests_signature is a thin value check over _git_long_abbrev(text, 'signed', 2), dropping the draft's casefold "
            + "of the option NAME (git 2.53 calls --SIGNED and --Si unknown options) and its redundant bare-flag clause (an equivalent mutant survived on it)",
            "--signed=, --si= and --signed=00 (git pushes WITHOUT a certificate) and --signed=falsehood (git refuses it) moved out of PUSH_SIGNING into "
            + "DENIED_NOT_SIGNED; the docstring no longer calls them signing requests by git",
            "--SIGNED / --Si pinned allowed",
            "black (one blank line)",
            "version claims re-derived on git 2.53.0",
            "rule description extended to the commit/tag/gpg prefixes",
        ],
        "dropped": ["CHANGELOG and REFERENCE stamp hunks (rebuilt on main)"],
        "outcome": "carried-with-fix",
        "reason": "9 cases fail on main; one helper serves both drafts",
    },
    2504: {
        "taken": ["scripts/claude_interactive.bash hunk (verbatim)", "tests/test_claudey_empty_prompt_file_env.py (head blob)", "ci.yml and main-verify.yml registrations"],
        "fixes": ["mypy arg-type at :49: _run takes env_values as an explicit dict, so **env_values can no longer bind extra_args"],
        "dropped": ["CHANGELOG and REFERENCE stamp hunks (rebuilt on main)"],
        "outcome": "carried-with-fix",
        "reason": "5 cases fail on main",
    },
    2505: {
        "taken": ["scripts/wake_the_claude.bash hunks (verbatim)", "tests/test_prompt_file_later_flag.py (head blob)", "ci.yml and main-verify.yml registrations"],
        "fixes": ["black (the triage's finding): one string's quotes normalized at line 40 of the test; applied by the pinned hook in pre-commit run 1, which still reported Passed because the file is untracked"],
        "dropped": ["CHANGELOG and REFERENCE stamp hunks (rebuilt on main)"],
        "outcome": "carried-with-fix",
        "reason": "6 cases fail on main",
    },
    2513: {
        "taken": ["util/fleet_triage/predict_merge.py hunk (verbatim)", "tests/test_predict_merge_inherited_git_env.py (head blob)", "docs/REFERENCE.md fleet-triage step-1 sentence and Test Suite Reference entry", "ci.yml and main-verify.yml registrations"],
        "fixes": ["CodeQL prescreen: `from unittest import mock` beside `import unittest` (import-and-import-from) -> `import unittest.mock as mock`", "the Test Suite Reference entry is placed after test_predict_merge.py's indented sub-bullet (the draft inserted it between them, re-parenting the sub-bullet)"],
        "dropped": ["CHANGELOG and REFERENCE stamp hunks (rebuilt on main)"],
        "outcome": "carried-with-fix",
        "reason": "on main the shallow-file case errors and the graft case reports MERGE-CLEAN",
    },
    2494: {
        "taken": ["util/fleet_triage/predict_merge.py: the docstring hunk of its own commit 03db661f (module docstring (a)/(b) and simulate_merge's first line)"],
        "fixes": ["extended to name #2513's GIT_SHALLOW_FILE and GIT_GRAFT_FILE; both behavioural sentences verified against main (predict_merge.py:413-429)"],
        "dropped": [".claude/agents/fleet-supervisor.md, CHANGELOG.md and the four docs files (the ml-docs carrier's)", "its first two commits (47b19f9d, 21a9dabc): main already carries them as #2474 (the diff of 03db661f^ against main on predict_merge.py and tests/test_predict_merge.py is empty)"],
        "outcome": "carried-with-fix",
        "reason": "docstring hunk only, by the orchestrator's split",
    },
}

OPEN_QUESTIONS = [
    "Brace cap cost (owner ruling 'Fail closed' implemented literally: ANY word past 64 alternatives is refused, ranges and products included). Census over the 200 newest juniper-ml transcripts: 21 of 44,660 Bash commands (0.047%) would be refused; 19 of the 21 overflow in a word that carries quoting (python3 -c code, JSON), text bash never brace-expands, because the guard's lexer strips quotes before expanding. A quote-aware expansion would remove most false refusals without reopening the bypass. Ask the owner whether to follow up.",
    "NEW DEFECT on main AND in this carrier (not fixed: outside the ruling's wording): the guard does not model bash's increment range {x..y..n}. `cat ~/.{r..t..1}sh/config` (bash: .rsh .ssh .tsh) and `ls ~/.{f..h..1}nupg` pass with no hit. A 3-line fail-closed patch (refuse any {x..y..n}) is validated on a scratch copy: tmp/flood4r2/ml-code/proposed/increment_range_fail_closed.diff.txt and increment_range_probe.txt. Carry it here, or as its own PR?",
    "Guard version: bumped 1.2.0 -> 1.3.0 (every earlier behaviour change bumped it; the owner must re-run util/install_claude_agent_guard.bash --apply). Keep, or make it 1.2.1?",
    "The drafts cite git 2.43; this host runs git 2.53.0 and every claim was re-derived there. macOS turing's git version was not probed.",
    "main-verify.yml: the three non-guard suites were added as the drafts did; the two guard suites were not (main-verify carries neither guard suite today).",
    "Trap for the validators: pre-commit detects a hook's edits through git, so it cannot see edits to UNTRACKED files. Pre-commit run 1 reformatted two new suites with black and still printed Passed. The final state was proven with sha256 before/after a further run (all 13 new files byte-identical).",
]


def main(argv: list) -> int:
    scratch = Path(argv[1]).resolve()
    checks = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    root = Path.cwd()
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=True).stdout  # nosec B603 B607
    base = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    files = []
    for line in status.splitlines():
        code, path = line[:2], line[3:]
        files.append({"path": path, "status": "added" if code.strip() == "??" else ("deleted" if "D" in code else "modified")})
    swap = json.loads((scratch / "swap2" / "swap_check.json").read_text(encoding="utf-8"))
    mutations = []
    for row in swap["mutants"]:
        targets = ", ".join(r["target"] for r in row["results"])
        mutations.append({"test_file": targets, "mutant": "%s: %r -> %r" % (row["file"], row["old"], row["new"]), "result": row["verdict"], "log": str(scratch / "swap2" / (row["id"] + ".log"))})
    for row in swap["baselines"]:
        checks.append({"what": "carrier tests against origin/main's %s (the fix must be shown to fix)" % row["file"], "command": "python3 util/ad-hoc/2026-11-08_flood4r2_ml_code_swap_check.py tmp/flood4r2/ml-code/swap2", "result": "pass" if row["any_failed"] else "fail", "log": str(scratch / "swap2" / (row["id"] + ".log")), "detail": "; ".join("%s: %s" % (r["target"], r["failed_summary"] or "ok") for r in row["results"])})
    carried = []
    for pr, (head, title) in HEADS.items():
        carried.append(dict({"pr": pr, "head_sha": head, "title": title}, **CARRIED[pr]))
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "ml-code",
        "base_sha": base,
        "worktree": str(root),
        "files": files,
        "carried": carried,
        "checks": checks,
        "mutations": mutations,
        "open_questions": OPEN_QUESTIONS,
    }
    (scratch / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("files: %d; carried: %d; checks: %d; mutations: %d (%d killed)" % (len(files), len(carried), len(checks), len(mutations), sum(m["result"] == "killed" for m in mutations)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
