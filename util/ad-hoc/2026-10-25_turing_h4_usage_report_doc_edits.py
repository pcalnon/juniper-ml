"""
Apply the H4 usage-report PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — landing helper (turing bring-up task H4, erratum E-H6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.3, erratum E-H6);
         notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md (SER-E1);
         util/mcp_setup.bash; tests/test_mcp_setup.py; conf/hosts/turing/mcp.json;
         util/ad-hoc/2026-10-25_turing_c9_guard_doc_edits.py (the shape this follows)

Why: the shared files take concurrent whole-file uploads, so each upload is built by running this against a
FRESH `origin/main` copy at upload time (the juniper-ml#2262 revert class). Every edit has a marker (skip
when present) and an anchor that must occur exactly once. The files: `docs/REFERENCE.md` and `CHANGELOG.md`.
The plan's record of the change is a separate PR.

Usage:
    python3 -I util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py [--base DIR] [--check] --mutants N/M

`--mutants N/M` is the result of util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py to record
(for example `7/7`).

Exit codes:

- 0: applied, or nothing to do;
- 1: `--check` found pending edits;
- 2: an anchor was missing or not unique.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
AUDIT = "notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md"
MUTATION = "util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py"
H4_MUTATION = "util/ad-hoc/2026-10-21_turing_h4_mutation_check.py"
ENTRY_CMD = "`uvx --from git+https://github.com/oraios/serena@<commit> serena start-mcp-server --context <context> --project <checkout> --open-web-dashboard False`"

# docs/REFERENCE.md, § Utility Script Reference: util/mcp_setup.bash
REF_UTIL_RUNS_OLD = f"The entry runs {ENTRY_CMD}."
REF_UTIL_RUNS_NEW = (
    f"The entry runs {ENTRY_CMD}, with `SERENA_USAGE_REPORTING=false` in its `env`: Serena v1.7.0 reports usage to"
    " `oraios-software.de` at every start unless that variable is exactly `false` (SER-E1 of"
    f" `{AUDIT}`; owner ruling 2026-10-25)."
)
REF_UTIL_BUMP_OLD = "A pin bump must re-read the context's `excluded_tools` at the new commit."
REF_UTIL_BUMP_NEW = "A pin bump must re-read the context's `excluded_tools`, and the usage-report check, at the new commit."
REF_UTIL_CHECK_OLD = "`--check` exits 1 on a missing, unpinned, unbound or rebound entry."
REF_UTIL_CHECK_NEW = "`--check` exits 1 on a missing, unpinned, unbound or rebound entry, or one that leaves the usage report on."

# docs/REFERENCE.md, § Test Suite Reference: tests/test_mcp_setup.py
REF_SUITE_ENTRY_OLD = "--open-web-dashboard False`; a worktree's `.git` file counts."
REF_SUITE_ENTRY_NEW = "--open-web-dashboard False`, with `\"env\": {\"SERENA_USAGE_REPORTING\": \"false\"}`; a worktree's `.git` file counts."
REF_SUITE_DEFECTS_OLD = "The three defects it fixes each fail `--check` and are each replaced by a write:"
REF_SUITE_DEFECTS_NEW = "The four defects it fixes each fail `--check` and are each replaced by a write:"
REF_SUITE_D10_OLD = "and an unpinned source (D10). Other servers"
REF_SUITE_D10_NEW = (
    "an unpinned source (D10), and an entry that leaves Serena's usage report on (SER-E1): an empty `env`, as H4 wrote"
    " before 2026-10-25, or a capitalised value, since v1.7.0 compares the exact string `false`. Other servers"
)
REF_SUITE_PIN_OLD = "The committed `conf/hosts/turing/mcp.json` drives the script, "
REF_SUITE_PIN_NEW = "The committed `conf/hosts/turing/mcp.json` drives the script and records both checks made at its commit, "
REF_SUITE_TAIL_OLD = f"`{H4_MUTATION}` kills 20 of 20 mutants.\n"

CHANGELOG_MARKER = "**H4's Serena entry turns Serena's usage report off**"
CHANGELOG_ENTRY = (
    f"- {CHANGELOG_MARKER} (turing bring-up, erratum E-H6 of\n"
    f"  `{PLAN}`; owner ruling 2026-10-25).\n"
    "  Serena v1.7.0 sends the OS, the dashboard flag, the version, the backend and the context name to\n"
    "  `oraios-software.de` at every start unless `SERENA_USAGE_REPORTING` is exactly `false`\n"
    f"  (`src/serena/agent.py:724-737` at `949a27ef`; SER-E1 of `{AUDIT}`).\n"
    "  `util/mcp_setup.bash` wrote `\"env\": {}`.\n"
    "  - `util/mcp_setup.bash` now writes `\"env\": {\"SERENA_USAGE_REPORTING\": \"false\"}`. `False` or `0` would still\n"
    "    report, so the value is the exact string. An entry written before this fails `--check`, and the next write\n"
    "    replaces it, backing up the old file first. No checkout on turing had an entry yet: H4's live check still\n"
    "    waits on E-H4-WHEEL.\n"
    "  - `conf/hosts/turing/mcp.json`'s `verified` record adds the check made at the pin, so a pin bump re-reads it.\n"
    "  - `tests/test_mcp_setup.py` gains 3 tests (38 in all) and pins the exact value.\n"
    f"    `{MUTATION}` kills @MUTANTS@ mutants, and the 20 of `{H4_MUTATION}` still apply.\n"
)


class AnchorError(Exception):
    pass


def replace_once(text: str, old: str, new: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(old) != 1:
        raise AnchorError(f"text occurs {text.count(old)} times (need 1): {old[:80]!r}")
    return text.replace(old, new)


def add_changelog_entry(changelog: str, entry: str) -> str:
    """Put the entry at the top of [Unreleased]'s Changed subsection, opening one above Fixed or Security if needed."""
    start = changelog.find("## [Unreleased]")
    if start < 0:
        raise AnchorError("CHANGELOG.md has no '## [Unreleased]' section")
    end = changelog.find("\n## [", start + 1)
    section = changelog[start : end if end >= 0 else len(changelog)]
    if CHANGELOG_MARKER in section:
        return changelog
    if section.count("\n### Changed\n\n") == 1:
        section = section.replace("\n### Changed\n\n", "\n### Changed\n\n" + entry + "\n", 1)
    elif "\n### Changed\n" in section:
        raise AnchorError("the Unreleased section's '### Changed' heading is not followed by a blank line")
    else:
        # Keep a Changelog's order: Added, Changed, Deprecated, Removed, Fixed, Security
        for later in ("### Deprecated", "### Removed", "### Fixed", "### Security"):
            if section.count(f"\n{later}\n") == 1:
                section = section.replace(f"\n{later}\n", f"\n### Changed\n\n{entry}\n{later}\n", 1)
                break
        else:
            # a release proposal leaves [Unreleased] empty, or holds only Added: append the subsection
            section = section.rstrip("\n") + f"\n\n### Changed\n\n{entry}\n"
    return changelog[:start] + section + (changelog[end:] if end >= 0 else "")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mutants", required=True, help="the usage-report mutation result, N/M")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d+/\d+", args.mutants):
        print("--mutants must look like 7/7", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    base = Path(args.base)
    names = ("docs/REFERENCE.md", "CHANGELOG.md")
    texts = {name: (base / name).read_text(encoding="utf-8") for name in names}
    suite_tail = (
        f"`{H4_MUTATION}` kills 20 of 20 mutants, and `{MUTATION}` kills {killed} of {total} more: an empty or missing `env`, a"
        " capitalised value, a misnamed variable, a `--check` that ignores `env`, a write that keeps an older entry's `env`, and a"
        " pin that no longer records the check.\n"
    )
    try:
        ref = texts["docs/REFERENCE.md"]
        ref = replace_once(ref, REF_UTIL_RUNS_OLD, REF_UTIL_RUNS_NEW, "with `SERENA_USAGE_REPORTING=false` in its `env`")
        ref = replace_once(ref, REF_UTIL_BUMP_OLD, REF_UTIL_BUMP_NEW, "`excluded_tools`, and the usage-report check, at the new commit")
        ref = replace_once(ref, REF_UTIL_CHECK_OLD, REF_UTIL_CHECK_NEW, "rebound entry, or one that leaves the usage report on")
        ref = replace_once(ref, REF_SUITE_ENTRY_OLD, REF_SUITE_ENTRY_NEW, '`"env": {"SERENA_USAGE_REPORTING": "false"}`; a worktree')
        ref = replace_once(ref, REF_SUITE_DEFECTS_OLD, REF_SUITE_DEFECTS_NEW, "The four defects it fixes each fail `--check`")
        ref = replace_once(ref, REF_SUITE_D10_OLD, REF_SUITE_D10_NEW, "an entry that leaves Serena's usage report on (SER-E1)")
        ref = replace_once(ref, REF_SUITE_PIN_OLD, REF_SUITE_PIN_NEW, "drives the script and records both checks made at its commit")
        ref = replace_once(ref, REF_SUITE_TAIL_OLD, suite_tail, f"`{MUTATION}` kills")
        new = {"docs/REFERENCE.md": ref, "CHANGELOG.md": add_changelog_entry(texts["CHANGELOG.md"], CHANGELOG_ENTRY.replace("@MUTANTS@", f"{killed} of {total}"))}
    except AnchorError as exc:
        print(f"ANCHOR: {exc}", file=sys.stderr)
        return 2
    changed = [name for name in names if new[name] != texts[name]]
    for name in changed:
        print(f"{'would change' if args.check else 'changed'}: {name}")
        if not args.check:
            (base / name).write_text(new[name], encoding="utf-8")
    if not changed:
        print("nothing to do: every edit is already present")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
