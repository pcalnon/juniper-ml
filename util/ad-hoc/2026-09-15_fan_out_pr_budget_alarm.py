#!/usr/bin/env python3
"""2026-09-15_fan_out_pr_budget_alarm.py -- port pr-budget-alarm.yml to the other eight repos.

Project: juniper-ml
Sub-Project: fleet roll-out / open-PR budget detection
Application: ad-hoc automation (fleet workflow port)
Author: Paul Calnon
License: MIT License
Created: 2026-09-15
Status: ad-hoc -- migration (one fleet-wide workflow port)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1944; the eight roll-out PRs cascor#654, data#403, data-client#205,
    cascor-client#166, cascor-worker#187, canopy#635, deploy#218, recurrence#171

WHY

`.github/workflows/pr-budget-alarm.yml` was juniper-ml's alone. Cursor-fleet round 2 hit
FOUR repos -- ml, data, canopy, data-client -- so a resumption on the other three would have
been detected by nothing. The owner ruled 2026-09-15 that stale-at-scale documentation DOES
count as damage for the escalation trigger, which makes detection load-bearing rather than
advisory, and ruled the roll-out fleet-wide rather than just to the repos already hit.

WHY AN API SCRIPT AND NOT A CHECKOUT

Two constraints meet here. Commit signing is `required_signatures` fleet-wide and hangs in a
headless session, and a worktree-isolated session may not run git against sibling repos. An
API commit sidesteps both -- but only ONE of the APIs actually signs.

**The Contents API (`PUT /contents`) does NOT sign.** It commits as the authenticated user
and the result is `verified: false, reason: "unsigned"`. Measured 2026-09-15: the first run
of this script used it, and all eight PRs were unmergeable against `required_signatures` with
every required check green -- `mergeStateStatus: BLOCKED` and nothing naming the cause.

**GraphQL `createCommitOnBranch` DOES sign**: committer becomes `web-flow` and the commit is
`verified: true, reason: "valid"`. That is what this script uses. The fix for the eight
already-pushed branches was to force-reset each to base and re-commit through the mutation --
an unsigned commit ANYWHERE in the branch blocks the merge, so it has to leave history rather
than be buried under a signed one. A PR tracks its branch, not a commit, so it survives the
force-update.

ONE DEPARTURE FROM THE SOURCE, DELIBERATE

The source skips its Slack step SILENTLY when `SLACK_WEBHOOK_URL` is unset -- correct for
juniper-ml, which has the secret, and a trap everywhere else: a detector that cannot notify
looks exactly like a detector with nothing to report. None of the eight targets has that
secret today. So the ported copy adds a `::warning::` annotation on a WARN/ALARM breach with
no webhook configured, which surfaces in the Actions tab and on the run itself. The run still
does not fail -- the report-only contract is unchanged.

Usage:
    python3 util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py            # dry run (default)
    python3 util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py --execute  # create branch+PR
    python3 util/ad-hoc/2026-09-15_fan_out_pr_budget_alarm.py --repo juniper-data --execute
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess  # nosec B404 - fixed argv gh invocations, no shell
import sys
from pathlib import Path

OWNER = "pcalnon"
SOURCE = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pr-budget-alarm.yml"
TARGET_PATH = ".github/workflows/pr-budget-alarm.yml"
BRANCH = "chore/pr-budget-alarm-rollout"

# The ONLY commit path here that GitHub signs. See the module docstring.
COMMIT_MUTATION = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}
"""

TARGETS = [
    "juniper-cascor",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-canopy",
    "juniper-deploy",
    "juniper-recurrence",
]

# The silent-skip line in the source, and the loud replacement. Anchored on the exact source
# text so a source edit makes this script FAIL rather than silently ship an unported copy.
SILENT_SKIP = """          if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
            echo "SLACK_WEBHOOK_URL secret not set -- skipping Slack notification (non-blocking by design)."
            exit 0
          fi
"""

LOUD_SKIP = """          if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
            # Louder than juniper-ml's copy, on purpose. This repo has no webhook, so a
            # breach would otherwise be indistinguishable from a quiet week -- the exact
            # shape the alarm exists to rule out. Annotate the run; never fail it.
            echo "::warning title=PR budget ${LEVEL} with no Slack webhook::${TOTAL} open PR(s), ${CURSOR} on cursor/ branches (warn=${WARN} alarm=${ALARM}). SLACK_WEBHOOK_URL is not set on this repository, so no notification was sent. Set it to make this alarm reachable."
            echo "SLACK_WEBHOOK_URL secret not set -- annotated instead of notifying (non-blocking by design)."
            exit 0
          fi
"""

COMMIT_MESSAGE = """ci(pr-budget): port the open-PR budget alarm from juniper-ml

Cursor-fleet round 2 hit four repos; the alarm existed on one. The owner ruled
2026-09-15 that stale-at-scale documentation counts as damage for the escalation
trigger, which makes detection load-bearing, and ruled the roll-out fleet-wide.

Report-only and read-only: `contents: read` + `pull-requests: read`, daily at
14:00 UTC plus workflow_dispatch, and the run never fails. Thresholds come from
the optional repo variables PR_BUDGET_WARN (default 15) and PR_BUDGET_ALARM
(default 30).

Differs from juniper-ml's copy in one way, deliberately: a WARN/ALARM breach with
no SLACK_WEBHOOK_URL configured emits a ::warning:: annotation rather than
skipping in silence. This repository has no webhook today, and a detector that
cannot notify must not look like a detector with nothing to report.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01N1jj3JGh1eVe7213j9j77p"""

PR_BODY = """## Summary

Ports `.github/workflows/pr-budget-alarm.yml` from `juniper-ml`, where it has run since
2026-07-30. Owner-ruled fleet-wide roll-out, 2026-09-15.

**Why here.** Cursor-fleet round 2 ran against **four** repos (ml, data, canopy, data-client)
and the detector existed on **one**. The owner has now ruled that stale-at-scale documentation
*does* count as damage for the staged-escalation trigger, which makes detection load-bearing
rather than advisory -- an escalation rule cannot fire on a repo whose PR count nothing reads.

## What it does

Counts open PRs daily at 14:00 UTC (plus `workflow_dispatch`), writes a job-summary table, and
notifies Slack on a WARN/ALARM breach.

- **Report-only.** The run never fails and gates no PR.
- **Read-only.** `contents: read` + `pull-requests: read`; no job elevates above it.
- **Thresholds are optional repo variables** -- `PR_BUDGET_WARN` (default 15),
  `PR_BUDGET_ALARM` (default 30).
- **No new required check**, no ruleset change.

## One deliberate difference from juniper-ml's copy

juniper-ml skips the Slack step *silently* when `SLACK_WEBHOOK_URL` is unset. That is correct
there -- it has the secret. Here it would be a trap: **a detector that cannot notify looks
exactly like a detector with nothing to report.**

So a breach with no webhook configured emits a `::warning::` annotation instead, visible on the
run and in the Actions tab. The run still does not fail.

## Owner follow-up

This repository has **no `SLACK_WEBHOOK_URL` secret**, so until one is added the alarm reports
to the Actions tab only. Adding the secret is what makes it reachable; nothing else is needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01N1jj3JGh1eVe7213j9j77p"""


def gh(args: list[str], stdin: str | None = None, timeout: int = 120):
    return subprocess.run(  # nosec B603 - fixed argv
        ["gh", *args], input=stdin, capture_output=True, text=True, timeout=timeout, check=False
    )


def api(path: str, method: str = "GET", payload: dict | None = None):
    """Call the GitHub API. Returns (ok, parsed-json-or-raw-stderr)."""
    args = ["api", "-X", method, path]
    stdin = None
    if payload is not None:
        args += ["--input", "-"]
        stdin = json.dumps(payload)
    proc = gh(args, stdin=stdin)
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    try:
        return True, json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        return True, proc.stdout


def probe(path: str) -> str:
    """'present' | 'absent' | 'error' for a GET that may legitimately 404.

    `api()` collapses every failure into False, which reads a transport timeout as "the file
    is not there" -- FAIL-OPEN, and the way a re-run duplicates a roll-out. Observed live on
    2026-09-15: two repos timed out mid-run and reported "would create" for files that
    existed, and a third reported "no open PR" for an open one. Only an explicit HTTP 404 is
    absence; anything else is unknown and the caller must refuse rather than assume.
    """
    proc = gh(["api", path, "--jq", ".name"])
    if proc.returncode == 0:
        return "present"
    return "absent" if "HTTP 404" in proc.stderr else "error"


def port_source(repo: str) -> str:
    """The source workflow, retitled for `repo` and with the silent skip made loud."""
    text = SOURCE.read_text(encoding="utf-8")
    if "# Application:   juniper-ml" not in text:
        raise SystemExit("source header line '# Application:   juniper-ml' not found -- re-check SOURCE")
    text = text.replace("# Application:   juniper-ml", f"# Application:   {repo}")
    if SILENT_SKIP not in text:
        raise SystemExit(
            "the silent-skip block was not found verbatim in the source. It has been edited; "
            "re-derive LOUD_SKIP against the new text rather than shipping an unported copy."
        )
    return text.replace(SILENT_SKIP, LOUD_SKIP)


def roll_out(repo: str, execute: bool) -> str:
    ok, meta = api(f"repos/{OWNER}/{repo}")
    if not ok:
        return f"FAIL   {repo}: cannot read repo ({meta[:90]})"
    base = meta.get("default_branch", "main")

    # Idempotence has to look in BOTH places. Checking only the default branch was wrong
    # while the roll-out was in flight: the file lives on the roll-out branch until its PR
    # merges, so a re-run reported "would create" for all eight and an --execute would have
    # failed its PUT (the Contents API needs the existing blob's `sha` to overwrite).
    on_default = probe(f"repos/{OWNER}/{repo}/contents/{TARGET_PATH}")
    if on_default == "error":
        return f"FAIL   {repo}: cannot determine whether {TARGET_PATH} exists on {base} -- refusing"
    if on_default == "present":
        return f"SKIP   {repo}: {TARGET_PATH} already on {base}"

    on_branch = probe(f"repos/{OWNER}/{repo}/contents/{TARGET_PATH}?ref={BRANCH}")
    if on_branch == "error":
        return f"FAIL   {repo}: cannot determine whether {BRANCH} already carries it -- refusing"
    if on_branch == "present":
        ok_pr, prs = api(f"repos/{OWNER}/{repo}/pulls?head={OWNER}:{BRANCH}&state=open")
        if not ok_pr:
            return f"SKIP   {repo}: already on {BRANCH}; PR lookup failed, check by hand"
        where = f"PR #{prs[0]['number']}" if prs else f"branch {BRANCH} (no open PR)"
        return f"SKIP   {repo}: already rolled out on {where}"

    body = port_source(repo)
    if not execute:
        return f"DRY    {repo}: would create {TARGET_PATH} on {BRANCH} (base {base}), {len(body)} chars"

    ok, ref = api(f"repos/{OWNER}/{repo}/git/ref/heads/{base}")
    if not ok:
        return f"FAIL   {repo}: cannot resolve {base} ({ref[:90]})"
    sha = ref["object"]["sha"]

    ok, res = api(
        f"repos/{OWNER}/{repo}/git/refs", "POST",
        {"ref": f"refs/heads/{BRANCH}", "sha": sha},
    )
    if not ok and "Reference already exists" not in str(res):
        return f"FAIL   {repo}: cannot create branch ({str(res)[:90]})"

    # createCommitOnBranch, NOT `PUT /contents` -- the Contents API does not sign, and
    # `required_signatures` then blocks the PR with every check green and nothing saying why.
    headline, _, msg_body = COMMIT_MESSAGE.partition("\n\n")
    variables = {
        "input": {
            "branch": {"repositoryNameWithOwner": f"{OWNER}/{repo}", "branchName": BRANCH},
            "message": {"headline": headline, "body": msg_body},
            "fileChanges": {
                "additions": [
                    {"path": TARGET_PATH, "contents": base64.b64encode(body.encode()).decode("ascii")}
                ]
            },
            "expectedHeadOid": sha,
        }
    }
    proc = gh(
        ["api", "graphql", "-f", f"query={COMMIT_MUTATION}", "--input", "-"],
        stdin=json.dumps({"query": COMMIT_MUTATION, "variables": variables}),
    )
    if proc.returncode != 0:
        return f"FAIL   {repo}: createCommitOnBranch ({proc.stderr.strip()[:120]})"

    # Never assume the signature: an unsigned commit is exactly the failure this path exists
    # to avoid, and it is invisible until the PR refuses to merge.
    ok, commit = api(f"repos/{OWNER}/{repo}/commits/{BRANCH}")
    if not ok or not commit.get("commit", {}).get("verification", {}).get("verified"):
        reason = (commit.get("commit", {}).get("verification", {}) or {}).get("reason", "unknown")
        return f"FAIL   {repo}: commit is NOT verified (reason={reason}) -- would be unmergeable"

    ok, pr = api(
        f"repos/{OWNER}/{repo}/pulls", "POST",
        {
            "title": "ci(pr-budget): port the open-PR budget alarm from juniper-ml",
            "head": BRANCH,
            "base": base,
            "body": PR_BODY,
        },
    )
    if not ok:
        return f"PARTIAL {repo}: file written on {BRANCH} but PR not opened ({str(pr)[:110]})"
    return f"OK     {repo}: {pr.get('html_url')}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", action="append", help="limit to this repo (repeatable)")
    ap.add_argument("--execute", action="store_true", help="actually create branches and PRs")
    args = ap.parse_args()

    repos = args.repo or TARGETS
    unknown = [r for r in repos if r not in TARGETS]
    if unknown:
        print(f"not roll-out targets: {', '.join(unknown)}", file=sys.stderr)
        return 2

    if not SOURCE.is_file():
        print(f"source workflow missing: {SOURCE}", file=sys.stderr)
        return 2

    print(f"{'DRY RUN -- pass --execute to act' if not args.execute else 'EXECUTING'}")
    print(f"source: {SOURCE}")
    print()
    results = [roll_out(r, args.execute) for r in repos]
    for line in results:
        print(line)

    print()
    failed = [line for line in results if line.startswith(("FAIL", "PARTIAL"))]
    print(f"{len(results) - len(failed)} ok/skipped/dry, {len(failed)} failed")
    if failed:
        print("\nNOTE: a PARTIAL left a branch behind. Re-running is safe -- the branch is")
        print("reused and the file write is idempotent -- but check for an existing PR first.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
