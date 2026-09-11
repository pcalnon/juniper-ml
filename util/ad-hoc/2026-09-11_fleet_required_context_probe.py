#!/usr/bin/env python3
"""2026-09-11_fleet_required_context_probe.py -- which contexts does each repo's ruleset REQUIRE?

Project: juniper-ml
Sub-Project: CI documentation integrity (cross-repo)
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

The 2026-09-09 cursor-fleet handoff's item 6a asserts that `Sequence Safety` is a REQUIRED
context in all eight sibling repos while all eight workflows call it "ADVISORY ... never
blocks a merge". The comment half of that is measured -- grep finds the phrasing in all
eight files. The ruleset half was never checked in any sibling; it was checked in juniper-ml
alone (ml#1849 / ml#1856) and generalised.

That generalisation is exactly the move this arc keeps paying for. A comment and a ruleset
are different authorities, and the whole point of the drift class is that the two disagree.
If `Sequence Safety` is genuinely advisory in the siblings, their comments are CORRECT and
there is no fan-out to do -- editing them would introduce the defect rather than fix it.

So this asks the ruleset directly, per repo, and prints what it finds rather than what was
expected. `util/ad-hoc/2026-09-09_required_check_comment_drift.py` answers the same question
for juniper-ml only and hard-codes both the ruleset id and the API path.

WHAT IT REPORTS

Per repo: every ruleset that targets the default branch, and the required status-check
contexts it names. `--context NAME` narrows the verdict line to one context and prints
REQUIRED / not-required per repo, which is the form item 6a needs.

EXIT CODES

  * 0 -- every repo answered;
  * 1 -- at least one repo could not be read (named, with the error). NOT folded into 0:
    a repo that failed to answer is not a repo that answered "no", and the difference is
    the entire finding.
  * 2 -- `gh` missing, or no repos to probe.

Usage:
    python3 util/ad-hoc/2026-09-11_fleet_required_context_probe.py
    python3 util/ad-hoc/2026-09-11_fleet_required_context_probe.py --context "Sequence Safety"
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404 -- fixed argv gh invocations, no shell
import sys

OWNER = "pcalnon"

# Same roster as util/ad-hoc/2026-08-20_require_context_safely.py TARGETS. juniper-ml is
# included deliberately: it is the repo the generalisation was made FROM, so its row is the
# control that shows what a genuine "required" answer looks like.
REPOS = [
    "juniper-ml",
    "juniper-cascor",
    "juniper-canopy",
    "juniper-data",
    "juniper-data-client",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-deploy",
    "juniper-recurrence",
]


def _gh_json(path: str):
    p = subprocess.run(  # nosec B603 B607 -- fixed argv, no shell
        ["gh", "api", path], capture_output=True, text=True, timeout=180
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[:200] or f"gh api {path} failed")
    return json.loads(p.stdout)


def _required_contexts(repo: str) -> tuple:
    """(contexts, ruleset_names) for every ACTIVE ruleset on `repo`'s default branch."""
    rulesets = _gh_json(f"repos/{OWNER}/{repo}/rulesets")
    contexts: list = []
    names: list = []
    for rs in rulesets:
        detail = _gh_json(f"repos/{OWNER}/{repo}/rulesets/{rs['id']}")
        if detail.get("enforcement") != "active":
            continue
        found_here: list = []
        for rule in detail.get("rules", []):
            if rule.get("type") == "required_status_checks":
                found_here += [
                    c["context"]
                    for c in rule.get("parameters", {}).get("required_status_checks", [])
                ]
        if found_here:
            names.append(f"{detail.get('name')} (id {rs['id']}, {len(found_here)} ctx)")
            contexts += found_here
    return sorted(set(contexts)), names


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--context", help="report REQUIRED / not-required for this one context")
    ap.add_argument("--repos", nargs="*", default=REPOS)
    args = ap.parse_args(argv)

    if not args.repos:
        print("no repos to probe", file=sys.stderr)
        return 2

    failures: list = []
    rows: list = []
    for repo in args.repos:
        try:
            contexts, names = _required_contexts(repo)
        except Exception as exc:  # noqa: BLE001 -- the message is the finding
            failures.append(f"{repo}: {exc}")
            rows.append((repo, None, []))
            continue
        rows.append((repo, contexts, names))

    if args.context:
        print(f"Is {args.context!r} a REQUIRED status check?\n")
        for repo, contexts, _names in rows:
            if contexts is None:
                verdict = "UNKNOWN (read failed)"
            else:
                verdict = "REQUIRED" if args.context in contexts else "not required"
            print(f"  {repo:24} {verdict}")
    else:
        for repo, contexts, names in rows:
            if contexts is None:
                print(f"=== {repo} === READ FAILED")
                continue
            print(f"=== {repo} === {len(contexts)} required context(s)")
            for n in names:
                print(f"    ruleset: {n}")
            for c in contexts:
                print(f"      - {c}")

    if failures:
        print(f"\n{len(failures)} repo(s) could not be read:", file=sys.stderr)
        for f in failures:
            print(f"    {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
