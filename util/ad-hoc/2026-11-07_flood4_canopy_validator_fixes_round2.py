#!/usr/bin/env python3
"""
Apply the round-2 validator findings confirmed on the canopy flood-4 carriers (wording and quantifier fixes).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation; tmp/flood4/canopy/val-round2/findings.json (F2, F3, F4, F5)

Usage: 2026-11-07_flood4_canopy_validator_fixes_round2.py <worktree> tests|docs

Exact single-occurrence replacements; nothing is written unless every old text occurs exactly once.
  tests F2: the test comment says the coreutils FORM, which GNU and uutils both accept (no host-only fact);
            the CHANGELOG says macOS ran the coreutils form, and that only the fixture's git calls pass -c.
  docs  F4: main's comment at src/tests/regression/test_gitleaks_config.py:92 carried D-F1's false premise
            (comment only; the assertion message beside it, "gitleaks would load no default rule", is true).
  docs  F5: "any pull request" -> a pull request from a branch of this repository; a fork's gets no secrets
            (canopy is public and allows forking).
  docs  F3/F6: the CHANGELOG counts four false draft claims, lists the third comment, and cites the
            documented minor-bump rule.
"""

import sys
from pathlib import Path

EDITS = {
    "tests": {
        "src/tests/regression/test_lockfile_regen_empty_payload.py": [
            (
                "# The step runs on ubuntu-latest and encodes with coreutils ``base64 -w0 FILE`` (GNU or\n"
                "# uutils; this host's is uutils 0.10.0, and both take the form). BSD/macOS base64\n",
                "# The step runs on ubuntu-latest and encodes with the coreutils form ``base64 -w0 FILE``,\n"
                "# which GNU and uutils coreutils both accept. BSD/macOS base64\n",
            ),
        ],
        "CHANGELOG.md": [
            (
                "#792 ran coreutils `base64 -w0 FILE` (GNU or uutils) on the required macOS\n"
                "  leg, where BSD `base64` refuses the file operand (5 failures);",
                "#792 ran the coreutils form `base64 -w0 FILE` on the required macOS leg,\n"
                "  whose BSD `base64` refuses the file operand (5 failures);",
            ),
            (
                "Its git calls and the step it runs now set\n"
                "  `GIT_CONFIG_GLOBAL` to the null device and `GIT_CONFIG_NOSYSTEM=1`, and pass `-c commit.gpgsign=false\n"
                "  -c tag.gpgsign=false`. Test-only.",
                "Its git calls now pass\n"
                "  `-c commit.gpgsign=false -c tag.gpgsign=false`, and they and the step it runs set `GIT_CONFIG_GLOBAL` to the\n"
                "  null device and `GIT_CONFIG_NOSYSTEM=1`. Test-only.",
            ),
        ],
    },
    "docs": {
        "src/tests/regression/test_gitleaks_config.py": [
            (
                "    # Without this table gitleaks loads only this file's [[rules]]: the zero-rule config that passed every scan.\n",
                "    # Without this table gitleaks loads only .gitleaks.toml's own [[rules]]. Its one entry has no regex or path, so\n"
                "    # gitleaks 8.24.3 refuses the config (\"Failed to load config\") and the scan fails. Before 2026-10-25 the file had\n"
                "    # no [[rules]] entry either, and that zero-rule config passed every scan.\n",
            ),
        ],
        "docs/ci_cd/CICD_MANUAL.md": [
            (
                # split at sentence boundaries: the qualified sentence pushed the paragraph line past 512 (MD013)
                " A refused upload on any pull request is therefore a token problem to investigate, not an expected refusal. Leave `fail_ci_if_error` false:",
                "\nA refused upload on a pull request from a branch of this repository, Dependabot's included, is therefore a token problem to investigate, not an expected refusal. A pull request from a fork gets no secrets, so its upload is tokenless by design.\nLeave `fail_ci_if_error` false:",
            ),
        ],
        "docs/ci_cd/CICD_QUICK_START.md": [
            (
                "so a refusal is a token problem on any pull request.",
                "so a refusal is a token problem on a pull request from a branch of this repository, Dependabot's included (a fork's pull request gets no secrets, so its upload is tokenless).",
            ),
        ],
        "CHANGELOG.md": [
            (
                "Claims were re-checked against `main`, and three the drafts got wrong are\n  corrected.",
                "Claims were re-checked against `main`, and four the drafts got wrong are\n  corrected.",
            ),
            (
                "  echoes the staged config in `data`. The two false claims are also corrected in comments on `main`\n"
                "  (`.gitleaks.toml`, `.github/workflows/ci.yml`), with no logic change.",
                "  echoes the staged config in `data`. A test module directly in `src/tests/` fails the unit lane\n"
                "  (`TestNoTestModuleSitsAtTheTopOfTheTestTree`) rather than silently never running. The first two false claims\n"
                "  are also corrected in comments on `main` (`.gitleaks.toml`, `.github/workflows/ci.yml`,\n"
                "  `src/tests/regression/test_gitleaks_config.py`), with no logic change.",
            ),
            (
                "  each file is bumped once (minor where it gains a section); the eight lines over markdownlint's 512-character\n"
                "  limit are wrapped",
                "  each file is bumped once (minor where it gains a section, as `docs/DOCUMENTATION_OVERVIEW.md` prescribes); the\n"
                "  eight lines over markdownlint's 512-character limit are wrapped",
            ),
        ],
    },
}


def main(argv: list[str]) -> int:
    root, role = Path(argv[1]).resolve(), argv[2]
    staged = {}
    for rel, edits in EDITS[role].items():
        text = (root / rel).read_text(encoding="utf-8")
        for old, new in edits:
            n = text.count(old)
            if n != 1:
                print(f"ABORT {rel}: old text occurs {n} times: {old[:90]!r}")
                return 1
            text = text.replace(old, new)
        staged[rel] = text
        print(f"{role} {rel}: {len(edits)} edit(s)")
    for rel, text in staged.items():
        (root / rel).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
