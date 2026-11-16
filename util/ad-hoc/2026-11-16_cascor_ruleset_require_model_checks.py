#!/usr/bin/env python3
"""Require juniper-cascor's `Model required checks` context (ci-cascor-model.yml) in ruleset 15081045.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-16
Status:      ad-hoc -- one-off (Python 3.15 migration arc, owner question 1 of the phase-2 handoff; not a 3.15 change)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_deploy_ruleset_require_unit_tests_legs.py (the same full-replacement PUT, which
             this copies with only the repo, ruleset, anchor and context changed);
             prompts/thread-handoff_automated-prompts/
             HANDOFF_2026-11-15_python-3-15-phase-2-complete-dill-drift-nightly-markers-cleanup.md (Open owner question 1)

Why this exists
---------------
`ci-cascor-model.yml`'s `Test (Python 3.12)` caught juniper-cascor#687's drift on 2026-09-24, but no ruleset required
it, so `main` stayed red for seven weeks. The owner ruled on 2026-11-16 to require a check from that workflow using
juniper-recurrence's pattern: the workflow runs on every PR, a `changes` job scopes the package jobs, and an
always-reporting `Model required checks` job is the required context (juniper-cascor#771). This adds that context.

What it does, and refuses to do
-------------------------------
* Reads the ruleset LIVE and builds a full-replacement PUT from that JSON: name, target, enforcement, conditions,
  bypass_actors and every rule are sent back as read. Only the `required_status_checks` list changes, and only by
  appending the one context.
* Every existing context keeps its own `integration_id`, as read. A hard-coded id once made five repos unmergeable
  (juniper-ml memory `project_branch_protection_headless_merge_2026-08-12.md`). The new context takes the id of the
  existing `Quality Gate` context, which is GitHub Actions'; the context's own check-run on `main` must come from the
  same app, or the script stops.
* Refuses when the context is already present (exit 0, "nothing to do"), when `main` has not posted it green, or when
  the GET lacks `bypass_actors`: a PUT built without them could not be shown to preserve them.
* Afterwards it re-reads the ruleset and checks: one context more; no surviving context's id drifted; everything else
  unchanged. Before, PUT-body and after JSON go to --out-dir.

Usage
-----
    python3 util/ad-hoc/2026-11-16_cascor_ruleset_require_model_checks.py --out-dir <dir>            # dry run
    python3 util/ad-hoc/2026-11-16_cascor_ruleset_require_model_checks.py --out-dir <dir> --execute

Rollback: the same PUT with the context removed, built from the saved `before` JSON.
Exit codes: 0 done / nothing to do / dry run OK; 1 a precondition or the post-check failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys
from pathlib import Path

OWNER = "pcalnon"
REPO = "juniper-cascor"
RULESET_ID = 15081045
ANCHOR = "Quality Gate"
NEW_CONTEXTS = ("Model required checks",)
PUT_FIELDS = ("name", "target", "enforcement", "conditions", "bypass_actors", "rules")


def gh_json(args: list[str], stdin: str | None = None) -> object:
    out = subprocess.run(["gh", "api", *args], input=stdin, capture_output=True, text=True, check=False)  # nosec B603 B607
    if out.returncode != 0:
        raise SystemExit(f"gh api {' '.join(args)} failed ({out.returncode}): {out.stderr.strip()}")
    return json.loads(out.stdout) if out.stdout.strip() else {}


def rsc_rule(ruleset: dict) -> dict:
    found = [r for r in ruleset["rules"] if r["type"] == "required_status_checks"]
    if len(found) != 1:
        raise SystemExit(f"expected one required_status_checks rule, found {len(found)}")
    return found[0]


def contexts(ruleset: dict) -> dict[str, object]:
    return {c["context"]: c.get("integration_id") for c in rsc_rule(ruleset)["parameters"]["required_status_checks"]}


def main_check_runs() -> dict[str, tuple[str | None, int | None]]:
    sha = gh_json([f"repos/{OWNER}/{REPO}/commits/main"])["sha"]
    runs = gh_json([f"repos/{OWNER}/{REPO}/commits/{sha}/check-runs?per_page=100"])["check_runs"]
    print(f"main head: {sha[:12]}")
    return {r["name"]: (r["conclusion"], (r.get("app") or {}).get("id")) for r in runs}


def without_rsc_list(ruleset: dict) -> str:
    """Everything the PUT sends, minus the one list it is allowed to change, canonically serialised."""
    body = {k: ruleset.get(k) for k in PUT_FIELDS}
    body["rules"] = [
        {**r, "parameters": {k: v for k, v in r["parameters"].items() if k != "required_status_checks"}} if r["type"] == "required_status_checks" else r
        for r in ruleset["rules"]
    ]
    return json.dumps(body, sort_keys=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out-dir", required=True, type=Path, help="where the before/after JSON is written (a repo tmp/ dir)")
    ap.add_argument("--execute", action="store_true", help="perform the PUT (default: dry run)")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    before = gh_json([f"repos/{OWNER}/{REPO}/rulesets/{RULESET_ID}"])
    (args.out_dir / "ruleset-before.json").write_text(json.dumps(before, indent=2) + "\n", encoding="utf-8")
    if "bypass_actors" not in before:
        print("REFUSE: the GET returned no bypass_actors, so a full-replacement PUT could not preserve them")
        return 1
    have = contexts(before)
    print(f"ruleset {RULESET_ID} '{before['name']}': {len(have)} required contexts")
    if all(c in have for c in NEW_CONTEXTS):
        print("nothing to do: the context is already required")
        return 0
    if any(c in have for c in NEW_CONTEXTS):
        print(f"REFUSE: only some of {NEW_CONTEXTS} are present; inspect by hand")
        return 1
    if ANCHOR not in have:
        print(f"REFUSE: the anchor context {ANCHOR!r} is not required, so there is no id to copy")
        return 1
    actions_id = have[ANCHOR]

    posted = main_check_runs()
    for c in (ANCHOR, *NEW_CONTEXTS):
        conclusion, app_id = posted.get(c, (None, None))
        print(f"  main posts {c!r}: conclusion={conclusion} app={app_id}")
        if conclusion != "success":
            print(f"REFUSE: main has not posted {c!r} green")
            return 1
        if app_id != actions_id:
            print(f"REFUSE: {c!r} on main comes from app {app_id}, but {ANCHOR!r} is required from {actions_id}")
            return 1

    body = {k: before[k] for k in PUT_FIELDS}
    rsc = rsc_rule(body)
    rsc["parameters"]["required_status_checks"] = [
        *rsc["parameters"]["required_status_checks"],
        *({"context": c, "integration_id": actions_id} for c in NEW_CONTEXTS),
    ]
    (args.out_dir / "ruleset-put-body.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    print(f"PUT body: {len(have)} -> {len(have) + len(NEW_CONTEXTS)} contexts, new one with integration_id {actions_id}")
    if not args.execute:
        print("dry run: nothing sent (re-run with --execute)")
        return 0

    gh_json(["-X", "PUT", f"repos/{OWNER}/{REPO}/rulesets/{RULESET_ID}", "--input", "-"], stdin=json.dumps(body))
    after = gh_json([f"repos/{OWNER}/{REPO}/rulesets/{RULESET_ID}"])
    (args.out_dir / "ruleset-after.json").write_text(json.dumps(after, indent=2) + "\n", encoding="utf-8")
    now = contexts(after)
    problems = []
    if len(now) != len(have) + len(NEW_CONTEXTS):
        problems.append(f"context count {len(have)} -> {len(now)}, want +{len(NEW_CONTEXTS)}")
    problems += [f"{c!r} id drifted {i!r} -> {now.get(c)!r}" for c, i in have.items() if now.get(c) != i]
    problems += [f"{c!r} missing or wrong id: {now.get(c)!r}" for c in NEW_CONTEXTS if now.get(c) != actions_id]
    if without_rsc_list(before) != without_rsc_list(after):
        problems.append("something other than the required-context list changed")
    for p in problems:
        print(f"POST-CHECK FAILED: {p}")
    if problems:
        return 1
    print(f"OK: {len(now)} required contexts; no existing id drifted; nothing else changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
