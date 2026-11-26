#!/usr/bin/env python3
"""
Add one required status check to a repository ruleset, and prove nothing else in the ruleset changed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout: the Overtoad ruled on 2026-11-26 (AskUserQuestion) to make
        juniper-recurrence's "Local test runner suite" a required check in ruleset juniper-recurrent-rules
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)

A ruleset is replaced whole by PUT, so this reads it, appends ``{"context": CONTEXT, "integration_id": ID}`` to its
``required_status_checks`` rule (the integration id the existing entries use, unless ``--integration-id`` names one),
PUTs back only the writable fields, and re-reads it: the result must equal the old ruleset plus that one entry, or
it says so and exits 1. Without ``--execute`` it prints the change and sends nothing. The ruleset before the change is
saved to ``--save`` (a JSON file) first, so the edit can be undone by hand.

Usage: python3 util/ad-hoc/2026-11-26_add_required_check_to_ruleset.py --repo R --ruleset ID --context NAME --save FILE [--execute]
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess  # nosec B404 - gh with a fixed argv
import sys
from pathlib import Path

WRITABLE = ("name", "target", "enforcement", "conditions", "rules", "bypass_actors")


def gh(*args: str, payload: dict | None = None) -> dict:
    proc = subprocess.run(["gh", "api", *args, *(["--input", "-"] if payload is not None else [])], input=json.dumps(payload) if payload is not None else None, capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"gh api {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)


def checks_rule(ruleset: dict) -> dict:
    found = [rule for rule in ruleset.get("rules") or [] if rule.get("type") == "required_status_checks"]
    if len(found) != 1:
        raise SystemExit(f"expected one required_status_checks rule, found {len(found)}")
    return found[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--owner", default="pcalnon")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ruleset", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--integration-id", type=int)
    parser.add_argument("--save", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    path = f"repos/{args.owner}/{args.repo}/rulesets/{args.ruleset}"
    before = gh(path)
    args.save.write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    checks = checks_rule(before)["parameters"]["required_status_checks"]
    if any(check.get("context") == args.context for check in checks):
        print(f"{args.context!r} is already required in {before['name']}: nothing to do")
        return 0
    ids = sorted({check.get("integration_id") for check in checks if check.get("integration_id") is not None})
    integration = args.integration_id if args.integration_id is not None else (ids[0] if len(ids) == 1 else None)
    entry = {"context": args.context, **({"integration_id": integration} if integration is not None else {})}
    wanted = copy.deepcopy({key: before[key] for key in WRITABLE if key in before})
    checks_rule(wanted)["parameters"]["required_status_checks"].append(entry)
    print(f"{before['name']} ({path}): add {entry} to {len(checks)} required check(s); saved the old ruleset to {args.save}")
    if not args.execute:
        print("dry run: nothing sent (--execute sends it)")
        return 0
    gh("-X", "PUT", path, payload=wanted)
    after = gh(path)
    expected = {key: wanted[key] for key in WRITABLE if key in wanted}
    got = {key: after.get(key) for key in WRITABLE if key in wanted}
    if json.dumps(got, sort_keys=True) != json.dumps(expected, sort_keys=True):
        print("MISMATCH: the ruleset GitHub holds is not the old one plus the new check:")
        print(json.dumps({"expected": expected, "got": got}, indent=2))
        return 1
    print(f"done: {args.context!r} is required; every other field of the ruleset is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
