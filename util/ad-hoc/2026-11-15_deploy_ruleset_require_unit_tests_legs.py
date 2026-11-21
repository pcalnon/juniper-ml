#!/usr/bin/env python3
"""Require juniper-deploy's `Unit Tests (Python 3.13)` and `(Python 3.14)` contexts in ruleset 14715370.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc operations tooling
Author:      Paul Calnon
License:     MIT License
Created:     2026-11-15
Status:      ad-hoc -- one-off (Python 3.15 migration arc; this is not a 3.15 change)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     util/ad-hoc/2026-11-15_deploy_ruleset_require_precommit_legs.py (the same change for the Pre-commit
             legs, which this copies with only the anchor and the two context names changed);
             prompts/thread-handoff_automated-prompts/
             HANDOFF_2026-11-15_python-3-15-phase-2-deploy-precommit-required-h5py-prs.md (Open Overtoad question 2)

Why this exists
---------------
juniper-deploy#274 gave the `tests` job a 3.12-3.15 matrix. Its 3.12 leg keeps posting the required `Unit Tests`
through an expression name; the 3.13 and 3.14 legs block only through the required Quality Gate, which fails when
`needs.tests.result` is not success. The question "should they become required contexts too?" was carried through
three handoffs. The Overtoad answered it on 2026-11-15: "Require both".

What it does, and refuses to do
-------------------------------
* Reads the ruleset LIVE and builds a full-replacement PUT from that JSON: name, target, enforcement, conditions,
  bypass_actors and every rule are sent back as read. Only the `required_status_checks` list changes, and only by
  appending the two contexts.
* Every existing context keeps its own `integration_id`, as read. A hard-coded id once made five repos unmergeable
  (juniper-ml memory `project_branch_protection_headless_merge_2026-08-12.md`). The two new contexts take the id of
  the existing `Unit Tests` context. That context is GitHub Actions', and the leg's own check-run on `main` must
  come from the same app, or the script stops.
* Refuses when either context is already present (exit 0, "nothing to do"), when `main` has not posted both green,
  or when the GET lacks `bypass_actors`: a PUT built without them could not be shown to preserve them.
* Afterwards it re-reads the ruleset and checks: two contexts more; no surviving context's id drifted; everything
  else unchanged. Before and after JSON go to --out-dir.

Usage
-----
    python3 util/ad-hoc/2026-11-15_deploy_ruleset_require_unit_tests_legs.py --out-dir <dir>            # dry run
    python3 util/ad-hoc/2026-11-15_deploy_ruleset_require_unit_tests_legs.py --out-dir <dir> --execute

Rollback: the same PUT with the two contexts removed, built from the saved `before` JSON.
Exit codes: 0 done / nothing to do / dry run OK; 1 a precondition or the post-check failed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

OWNER = "pcalnon"
REPO = "juniper-deploy"
RULESET_ID = 14715370
ANCHOR = "Unit Tests"
NEW_CONTEXTS = ("Unit Tests (Python 3.13)", "Unit Tests (Python 3.14)")
PUT_FIELDS = ("name", "target", "enforcement", "conditions", "bypass_actors", "rules")


def gh_json(args: list[str], stdin: str | None = None) -> object:
    out = subprocess.run(["gh", "api", *args], input=stdin, capture_output=True, text=True, check=False)
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
        print("nothing to do: both contexts are already required")
        return 0
    if any(c in have for c in NEW_CONTEXTS):
        print(f"REFUSE: only one of {NEW_CONTEXTS} is present; inspect by hand")
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
    print(f"PUT body: {len(have)} -> {len(have) + len(NEW_CONTEXTS)} contexts, new ones with integration_id {actions_id}")
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
