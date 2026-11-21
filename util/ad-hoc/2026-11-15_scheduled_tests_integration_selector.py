#!/usr/bin/env python3
"""Point `scheduled-tests.yml` at `-m integration` in the three repos that register no `slow` marker.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-15
Status:      ad-hoc -- one-off (a pre-existing defect found by the Python 3.15 migration arc; not a 3.15 change)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     notes/templates/ci/scheduled-tests.yml (the template; its TODO 2 names the selector rule);
             prompts/thread-handoff_automated-prompts/
             HANDOFF_2026-11-15_python-3-15-phase-2-deploy-precommit-required-h5py-prs.md (Remaining work, item 4)

Why this exists
---------------
juniper-data-client, juniper-cascor-client and juniper-cascor-worker copied the template and kept its default
selector, `-m "slow or integration"`, although the template's TODO 2 says a repo without `slow` markers should use
just `integration`. None of the three registers `slow`, and all three run pytest with `--strict-markers`. pytest
9.2.0 made an unregistered marker in a `-m` expression a usage error under `--strict-markers`, so from the nightly
run of 2026-10-28 (the first to install 9.2.0) every leg exited 4 with
`ERROR: Unknown marker(s) in '-m' expression: slow`. pytest 9.1.1 accepted the same expression. Both were measured
on 2026-11-15 against a two-test project.

What it does, and refuses to do
-------------------------------
* `.github/workflows/scheduled-tests.yml`: replaces the selector with `-m integration` and explains why in the step's
  comment. In the two client repos it also rewords the step's exit-5 comment and notice, which named `slow`. Every
  replacement must match EXACTLY once, or nothing is written.
* `CHANGELOG.md`: inserts this repo's entry at the top of `[Unreleased]` / `### Fixed`. The anchor must lie inside
  `[Unreleased]`, before the first released heading.
* Afterwards it re-parses the workflow and checks that the step's `run` selects `-m integration` and no longer names
  `slow or integration`, and that no other step changed.

Usage
-----
    python3 util/ad-hoc/2026-11-15_scheduled_tests_integration_selector.py --repo juniper-data-client --worktree <wt>
    python3 util/ad-hoc/2026-11-15_scheduled_tests_integration_selector.py --repo <repo> --worktree <wt> --check

Exit 0 = applied (or, with --check, already applied); 1 = refused (a replacement did not match exactly once).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/scheduled-tests.yml")
CHANGELOG = Path("CHANGELOG.md")
STEP_ID = "run-slow-integration-tests"

WHY = """\
        # The selector is ``integration`` alone, as the template's TODO 2
        # says for a repo without ``slow`` markers. This repo registers no
        # ``slow`` marker, and from pytest 9.2.0 an unregistered marker in
        # a ``-m`` expression is a usage error under ``--strict-markers``
        # (exit 4): ``-m "slow or integration"`` failed every leg of every
        # nightly run from 2026-10-28.
"""

CLIENT_COMMENT_OLD = """\
        # P-12/P-13 fix: this repo currently has no tests decorated
        # ``@pytest.mark.slow`` or ``@pytest.mark.integration``, so
        # ``pytest -m "slow or integration"`` exits with code 5 ("no
        # tests collected") and fails the workflow. Once this repo grows
        # such tests, the gate will exercise them automatically; until
        # then, treat exit-5 as success so the schedule stays green and
        # genuinely-failing tests still surface (any other non-zero
        # exit is preserved as failure).
"""

CLIENT_COMMENT_NEW = (
    """\
        # P-12/P-13 fix: this repo currently has no tests decorated
        # ``@pytest.mark.integration``, so ``pytest -m integration``
        # exits with code 5 ("no tests collected") and fails the
        # workflow. Once this repo grows such tests, the gate will
        # exercise them automatically; until then, treat exit-5 as
        # success so the schedule stays green and genuinely-failing
        # tests still surface (any other non-zero exit is preserved as
        # failure).
"""
    + WHY
)

SELECTOR_OLD = '            -m "slow or integration" \\\n'
SELECTOR_NEW = "            -m integration \\\n"
NOTICE_OLD = "No slow/integration tests collected"
NOTICE_NEW = "No integration tests collected"

WORKER_STEP_OLD = """\
        id: run-slow-integration-tests
        continue-on-error: ${{ matrix.experimental == true }}
        run: |
"""
WORKER_STEP_NEW = (
    """\
        id: run-slow-integration-tests
        continue-on-error: ${{ matrix.experimental == true }}
"""
    + WHY
    + """\
        run: |
"""
)

ENTRY_HEAD = """\
- **The nightly `scheduled-tests.yml` lane runs again under pytest 9.2.0: it selects `-m integration`.** The workflow
  came from juniper-ml's `notes/templates/ci/scheduled-tests.yml` and kept the template's default selector,
  `-m "slow or integration"`, although the template's TODO 2 says a repo without `slow` markers should use just
  `integration`. This repo registers no `slow` marker and runs pytest with `--strict-markers`. From pytest 9.2.0 an
  unregistered marker in a `-m` expression is a usage error under `--strict-markers`, so every leg exited 4
  (`ERROR: Unknown marker(s) in '-m' expression: slow`) on every nightly run from 2026-10-28, the first to install
  9.2.0, through 2026-11-15. pytest 9.1.1 had accepted the same expression (both measured on 2026-11-15 against a
  two-test project).
  - The selector is now `integration`. It selects what the old one did, since `--strict-markers` already refused any
    test marked `slow`.
"""

ENTRY_TAIL = {
    "juniper-data-client": """\
  - The step's comment says why, and its exit-5 comment and notice no longer mention `slow`. This repo still has no
    `@pytest.mark.integration` test (the last green run, on 2026-10-27, deselected all 531), so each leg ends on that
    notice until it grows one.
""",
    "juniper-cascor-client": """\
  - The step's comment says why, and its exit-5 comment and notice no longer mention `slow`. This repo still has no
    `@pytest.mark.integration` test (the last green run, on 2026-10-27, deselected all 573), so each leg ends on that
    notice until it grows one.
""",
    "juniper-cascor-worker": """\
  - A comment on the step says why. Each leg runs the integration tests the lane ran before the break (the last clean
    run, on 2026-10-26: `5 passed, 511 deselected`).
""",
}

WORKFLOW_EDITS = {
    "juniper-data-client": [(CLIENT_COMMENT_OLD, CLIENT_COMMENT_NEW), (SELECTOR_OLD, SELECTOR_NEW), (NOTICE_OLD, NOTICE_NEW)],
    "juniper-cascor-client": [(CLIENT_COMMENT_OLD, CLIENT_COMMENT_NEW), (SELECTOR_OLD, SELECTOR_NEW), (NOTICE_OLD, NOTICE_NEW)],
    "juniper-cascor-worker": [(WORKER_STEP_OLD, WORKER_STEP_NEW), (SELECTOR_OLD, SELECTOR_NEW)],
}


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"REFUSED: {label}: expected exactly one match, found {count}: {old.splitlines()[0]!r}")
    return text.replace(old, new)


def insert_entry(text: str, entry: str) -> str:
    unreleased = text.find("## [Unreleased]")
    if unreleased < 0:
        raise SystemExit("REFUSED: CHANGELOG has no [Unreleased] section")
    released = text.find("\n## [", unreleased + 1)
    head = "### Fixed\n\n"
    anchor = text.find(head, unreleased)
    if anchor < 0 or (0 <= released < anchor):
        raise SystemExit("REFUSED: no ### Fixed heading inside [Unreleased]")
    at = anchor + len(head)
    return text[:at] + entry + "\n" + text[at:]


def steps(workflow_text: str) -> dict[str, dict]:
    doc = yaml.safe_load(workflow_text)
    job = doc["jobs"]["slow-or-integration-tests"]
    return {s.get("id", s.get("name")): s for s in job["steps"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, choices=sorted(WORKFLOW_EDITS))
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="verify the edits are present; write nothing")
    args = ap.parse_args()
    wf_path = args.worktree / WORKFLOW
    cl_path = args.worktree / CHANGELOG
    wf_old = wf_path.read_text(encoding="utf-8")
    cl_old = cl_path.read_text(encoding="utf-8")
    entry = ENTRY_HEAD + ENTRY_TAIL[args.repo]

    if args.check:
        ok = SELECTOR_NEW in wf_old and SELECTOR_OLD not in wf_old and entry in cl_old
        print(f"{args.repo}: {'applied' if ok else 'NOT applied'}")
        return 0 if ok else 1

    wf_new = wf_old
    for old, new in WORKFLOW_EDITS[args.repo]:
        wf_new = replace_once(wf_new, old, new, f"{args.repo} {WORKFLOW}")
    cl_new = insert_entry(cl_old, entry)

    before, after = steps(wf_old), steps(wf_new)
    if list(before) != list(after):
        raise SystemExit("REFUSED: the step list changed")
    changed = [k for k in before if before[k] != after[k]]
    if changed != [STEP_ID]:
        raise SystemExit(f"REFUSED: expected only {STEP_ID} to change, got {changed}")
    run = after[STEP_ID]["run"]
    if "-m integration" not in run or "slow or integration" in run:
        raise SystemExit("REFUSED: the step's run does not select -m integration alone")
    # Whole-document check: with the one changed step swapped back, the two parses must be equal, so no trigger,
    # matrix, permission or other job moved. (PyYAML reads the `on:` key as boolean True; comparing whole documents
    # needs no key names.)
    doc_old, doc_new = yaml.safe_load(wf_old), yaml.safe_load(wf_new)
    new_steps = doc_new["jobs"]["slow-or-integration-tests"]["steps"]
    for i, s in enumerate(new_steps):
        if s.get("id") == STEP_ID:
            new_steps[i] = before[STEP_ID]
    if doc_old != doc_new:
        raise SystemExit("REFUSED: something other than the selector step changed")

    wf_path.write_text(wf_new, encoding="utf-8")
    cl_path.write_text(cl_new, encoding="utf-8")
    print(f"ok: {args.repo}: {WORKFLOW} (only step {STEP_ID} changed) and {CHANGELOG} (+{len(entry.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
