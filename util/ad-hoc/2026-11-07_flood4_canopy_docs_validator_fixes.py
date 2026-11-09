#!/usr/bin/env python3
"""
Apply the validator findings confirmed on the canopy flood-4 docs carrier (D-F1..D-F3, D-F5, D-F6, D-F8, D-F9, main's two comments).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier; tmp/flood4/canopy/val-docs/findings.json

Usage: 2026-11-07_flood4_canopy_docs_validator_fixes.py <docs worktree>

Every edit is an exact replacement whose old text must occur exactly once (else nothing is written).
Evidence for each, re-derived on 2026-11-07:
  D-F1  gitleaks 8.24.3 without [extend]: exit 1, "Failed to load config ... generic-api-key: both |regex|
        and |path| are empty"; with [[rules]] also removed: exit 0, no leaks (the pre-#764 file held only
        [allowlist]); gitleaks-action e0c47f4f: any exit other than 0/2 -> "Unexpected exit code".
  D-F2  gh api repos/pcalnon/juniper-canopy/dependabot/secrets: CODECOV_TOKEN created 2026-11-04T11:18:47Z.
  D-F3  main.py returns the backend's `data`; cascor POST /v1/training/dataset returns
        success_response({"status": "staged", "config": cfg}) with cfg = body.model_dump(exclude_none=True);
        the client returns the whole envelope; demo/recurrence return data={"status": "staged", "config": ...}.
  D-F5  test_ci_lane_wiring.py TestNoTestModuleSitsAtTheTopOfTheTestTree fails the unit lane; the scheduled
        lane walks testpaths under -m "slow or integration".
  D-F6  docs/DOCUMENTATION_OVERVIEW.md: Minor = new sections; the 7 docs below gain headings.
  D-F8  CICD_MANUAL's sibling troubleshooting label becomes a heading like its new neighbour.
  D-F9  main.py StageDatasetRequest has typed Optional fields, so FastAPI answers 422 on a bad type.
"""

import re
import sys
from pathlib import Path

EDITS = {
    "docs/ci_cd/CICD_MANUAL.md": [
        (
            "This file's only rule entry merges an allowlist into the built-in `generic-api-key` rule and defines no regex of its own, so an omitted `[extend]` table leaves the step with nothing to fire.\n"
            "The step then exits 0 on every `push`, `pull_request`, and `workflow_dispatch`. That was the config until 2026-10-25 (the same empty-ruleset defect as juniper-ml#2203). Leave the table in place.\n",
            "This file's only rule entry merges an allowlist into the built-in `generic-api-key` rule and has no `regex` or `path` of its own.\n"
            "Without `[extend]`, gitleaks 8.24.3 therefore refuses the config (`Failed to load config`: `generic-api-key: both |regex| and |path| are empty`) and exits 1, and the Gitleaks step fails with `Unexpected exit code [1]`.\n"
            "The silent pass needs the `[[rules]]` entry gone as well: a file with neither loads zero rules and exits 0 on every `push`, `pull_request`, and `workflow_dispatch`. That was the file until 2026-10-25, which held only an `[allowlist]` (the same empty-ruleset defect as juniper-ml#2203). Leave the table in place.\n",
        ),
        (
            "- `test_config_extends_the_default_ruleset` fails when `[extend] useDefault = true` is missing. A green Gitleaks step beside that failure scanned with an empty ruleset.\n",
            "- `test_config_extends_the_default_ruleset` fails when `[extend] useDefault = true` is missing. The Gitleaks step in the same run then fails too (`Failed to load config`), because the `generic-api-key` entry has nothing to extend. A green Gitleaks step beside that failure means the `[[rules]]` entry was removed as well, and the step ran with zero rules.\n",
        ),
        (
            "A Dependabot pull request reads the Dependabot secret store, which does not hold `CODECOV_TOKEN`. That upload stays tokenless, is refused, and still does not fail the job. Leave `fail_ci_if_error` false. Setting it true would turn that expected refusal into a red required check.\n",
            "Both secret stores hold `CODECOV_TOKEN`: the Actions store, and since 2026-11-04 the Dependabot store, which a Dependabot pull request reads. A refused upload on any pull request is therefore a token problem to investigate, not an expected refusal. Leave `fail_ci_if_error` false: coverage is gated inside the job by `--cov-fail-under`, and the upload only reports it, so a Codecov outage should not turn a required check red.\n",
        ),
        ("**Coverage report missing files:**\n", "##### Coverage report missing files\n"),
    ],
    "docs/ci_cd/CICD_REFERENCE.md": [
        (
            "That entry merges an allowlist into `generic-api-key` and defines no rule, so the step exits 0.\n",
            "That entry merges an allowlist into `generic-api-key` and has no `regex` or `path`, so gitleaks 8.24.3 refuses the config (`Failed to load config`) and the step fails with `Unexpected exit code [1]`. Only a file with no `[[rules]]` either, as before 2026-10-25, loads zero rules and exits 0.\n",
        ),
        (
            "Dependabot's secret store does not hold the token, so that refusal is expected on a Dependabot pull request.\n",
            "Dependabot's secret store has held the token too since 2026-11-04, so a refusal on a Dependabot pull request is not expected either.\n",
        ),
        (
            "A `test_*.py` directly in `src/tests/` is on no path list.\n",
            "A `test_*.py` directly in `src/tests/` is on none of the pull-request lanes' path lists; the scheduled lane reaches it only when it is marked `slow` or `integration`.\n",
        ),
    ],
    "docs/ci_cd/CICD_QUICK_START.md": [
        (
            "  `[extend] useDefault = true` is what loads the built-in ruleset. Without that table the Gitleaks step exits 0 with nothing to fire.",
            "  `[extend] useDefault = true` is what loads the built-in ruleset. Removing that table alone turns the Gitleaks step red (`Failed to load config`: the `generic-api-key` entry has no `regex` or `path`). A green step with the table gone means the `[[rules]]` entry went too, and gitleaks ran with zero rules.",
        ),
        (
            "A Dependabot pull request does not have `CODECOV_TOKEN`.",
            "Both the Actions and the Dependabot secret stores hold `CODECOV_TOKEN`, so a refusal is a token problem on any pull request.",
        ),
        (
            "- A new `test_*.py` directly in `src/tests/` never runs in CI:\n  The unit job names four subdirectories and does not collect the top of that tree.",
            "- A new `test_*.py` directly in `src/tests/` fails `Unit Tests + Coverage`, and its own tests run in no pull-request lane:\n  `TestNoTestModuleSitsAtTheTopOfTheTestTree` fails the unit lane, because the unit job names four subdirectories and does not collect the top of that tree.",
        ),
    ],
    "docs/ci_cd/CICD_ENVIRONMENT_SETUP.md": [
        (
            "It is an Actions repository secret. Without it Codecov refuses the upload (`Token required - not valid tokenless upload`) and the step stays green (`fail_ci_if_error: false`). Dependabot's secret store does not hold this token, so a Dependabot pull request's upload stays tokenless.",
            "It is an Actions repository secret, and the Dependabot secret store has held it too since 2026-11-04, so a Dependabot pull request's upload carries it. Without it Codecov refuses the upload (`Token required - not valid tokenless upload`) and the step stays green (`fail_ci_if_error: false`).",
        ),
    ],
    "docs/api/API_REFERENCE.md": [
        (
            '```json\n{"status": "success", "data": {}}\n```\n\n'
            "`data` is the `data` object the backend returned. For the cascor adapter that is the service response's `data`, which is empty when the service sent none. The staged config itself is not echoed here.\n",
            '```json\n{"status": "success", "data": {"status": "staged", "config": {"dataset_type": "mnist", "params": {"flatten": true}}}}\n```\n\n'
            "`data` is the `data` object the backend returned. On the cascor service path that is cascor's envelope `data`, `{\"status\": \"staged\", \"config\": ...}`, and `config` is the body cascor recorded after canopy's shaping (cascor drops `None` fields), so it shows what was forwarded.\n"
            "Demo mode and the recurrence backend echo the canopy body they were given instead (`main.py` drops `None` fields and `nn_model` before the call), and recurrence adds `dataset_ref`.\n",
        ),
        (
            "- `422 Unprocessable Entity` - `nn_model` is unknown, or the dataset is incompatible with that model.\n",
            "- `422 Unprocessable Entity` - A field fails request validation (FastAPI's `detail` list, for example a non-integer `nn_dataset_elements`), `nn_model` is unknown, or the dataset is incompatible with that model.\n",
        ),
    ],
    ".gitleaks.toml": [
        (
            "# Removing this table silently empties the ruleset again (see the header).\n",
            "# Removing this table no longer passes silently: the [[rules]] entry below has no regex or\n"
            "# path of its own, so gitleaks 8.24.3 refuses the config (\"Failed to load config ... both\n"
            "# |regex| and |path| are empty\") and the Gitleaks step fails. Removing that entry too would\n"
            "# bring back the zero-rule pass the header describes.\n",
        ),
    ],
    ".github/workflows/ci.yml": [
        (
            "      # secret store, which does not hold the token, so its upload is still tokenless.\n",
            "      # secret store, which has held the token too since 2026-11-04, so its upload carries it.\n",
        ),
    ],
}

# D-F6: minor for the docs that gain sections (canopy's DOCUMENTATION_OVERVIEW convention), still once from main.
MINOR = {
    "docs/ci_cd/CICD_MANUAL.md": ("0.27.3", "0.28.0"),
    "docs/ci_cd/CICD_REFERENCE.md": ("0.29.1", "0.30.0"),
    "docs/DEVELOPER_CHEATSHEET.md": ("1.0.6", "1.1.0"),
    "docs/QUICK_START.md": ("0.25.5", "0.26.0"),
    "docs/REFERENCE.md": ("0.25.5", "0.26.0"),
    "docs/USER_MANUAL.md": ("0.26.4", "0.27.0"),
    "docs/api/API_REFERENCE.md": ("1.4.4", "1.5.0"),
}
VERSION = re.compile(r"^(\*\*Version(?::\*\*|\*\*:)\s*)(\d+\.\d+\.\d+)(\s*)$", re.M)


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve()
    staged: dict[str, str] = {}
    for rel, edits in EDITS.items():
        text = staged.get(rel, (root / rel).read_text(encoding="utf-8"))
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                print(f"ABORT {rel}: old text occurs {n} times: {old[:90]!r}")
                return 1
            text = text.replace(old, new)
        staged[rel] = text
        print(f"{rel}: {len(edits)} edit(s)")
    for rel, (cur, new) in MINOR.items():
        text = staged.get(rel, (root / rel).read_text(encoding="utf-8"))
        found = [m.group(2) for m in VERSION.finditer(text)]
        if not found or set(found) != {cur}:
            print(f"ABORT {rel}: version stamps {found}, expected all {cur}")
            return 1
        staged[rel] = VERSION.sub(lambda m: f"{m.group(1)}{new}{m.group(3)}", text)
        print(f"{rel}: version {cur} -> {new} ({len(found)} stamp line(s))")
    for rel, text in staged.items():
        (root / rel).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
