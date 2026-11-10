"""
Apply the host check wording PR's CHANGELOG entry, idempotently, against any copy of the file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-30
Status: ad-hoc — landing helper (turing bring-up, erratum E-H3: the host check's wording)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (erratum E-H3 of §18.3);
         util/host_state_check.py; tests/test_host_state_check.py;
         util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py;
         util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py (the shape this follows)

Why: CHANGELOG.md takes concurrent whole-file uploads, so the upload is built by running this against a FRESH
`origin/main` copy at upload time (the juniper-ml#2262 revert class). The entry's marker counts anywhere in the
file, so a release cut that moves the entry does not re-add it (erratum E-CUT). `docs/REFERENCE.md` needs no
edit: its entries for the check and its suite stay true. The plan's record is a separate PR.

Usage:
    python3 -I util/ad-hoc/2026-10-30_turing_check_wording_doc_edits.py [--base DIR] [--check] --mutants N/M --g1 N/M
    python3 -I util/ad-hoc/2026-10-30_turing_check_wording_doc_edits.py --self-test

`--mutants N/M` is the result of util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py to record (for
example `4/4`), and `--g1 N/M` that of util/ad-hoc/2026-10-20_turing_g1_mutation_check.py (for example `57/57`).
`--self-test` runs the placement cases on synthetic changelogs and touches no file.

Exit codes:

- 0: applied, nothing to do, or every self-test case passed;
- 1: `--check` found the entry pending, or a self-test case failed;
- 2: an anchor was missing or malformed, or a result was not N/M.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
MUTATION = "util/ad-hoc/2026-10-30_turing_check_wording_mutation_check.py"
G1_MUTATION = "util/ad-hoc/2026-10-20_turing_g1_mutation_check.py"

CHANGELOG_MARKER = "**G-TOOLS kubectl's fix names task D3, and G-MEM's memory message names the speculative pages its figure counts**"
CHANGELOG_ENTRY = (
    f"- {CHANGELOG_MARKER}\n"
    f"  (turing bring-up; erratum E-H3 of `{PLAN}`,\n"
    "  from task H3's `macos-host-sme` report). Neither changes a verdict.\n"
    "  - `util/host_state_check.py`'s kubectl fix said only \"task D4\". Docker Desktop installs its own\n"
    "    `/usr/local/bin/kubectl` (decision D7), and turing's v1.22.4 client is that link, so the fix now puts the\n"
    "    owner's Docker Desktop upgrade (task D3) first, then D4, which still needs re-planning under the D6 ruling\n"
    "    (erratum E-D6).\n"
    "  - The memory message said \"free + inactive\", but the figure also adds vm_stat's speculative pages, as\n"
    "    `util/macvm_ctl.bash` does (88 MiB of turing's 6161 MiB on 2026-10-27). It now reads \"free + speculative +\n"
    "    inactive\". `util/macvm_ctl.bash` keeps its label: its status block shows \"free\" as Pages free + Pages\n"
    "    speculative.\n"
    "  - `tests/test_host_state_check.py`: `FailureTest` gains 2 tests, which pin the kubectl fix exactly and the\n"
    "    memory figure's label on a pass and on a failure, and the failure table's memory case reads the new label (63\n"
    f"    tests across the two G1 suites). `{MUTATION}` (new)\n"
    f"    kills @MUTANTS@ mutants through the G1 engine, and `{G1_MUTATION}`\n"
    "    still kills @G1@.\n"
)


class AnchorError(Exception):
    pass


def add_changelog_entry(changelog: str, entry: str) -> str:
    """Append the entry to [Unreleased]'s Fixed subsection, opening one (above Security, or last) if needed."""
    if CHANGELOG_MARKER in changelog:
        return changelog  # anywhere: after a release cut the entry sits in the release section
    start = changelog.find("## [Unreleased]")
    if start < 0:
        raise AnchorError("CHANGELOG.md has no '## [Unreleased]' section")
    end = changelog.find("\n## [", start + 1)
    section = changelog[start : end if end >= 0 else len(changelog)]
    heading = "\n### Fixed\n\n"
    if section.count(heading) == 1:
        body = section.index(heading) + len(heading)
        later = section.find("\n### ", body)
        if later < 0:
            section = section.rstrip("\n") + "\n" + entry
        else:
            # the subsection's last entry, then the blank line that ends it, then the next heading
            section = section[:later].rstrip("\n") + "\n" + entry + section[later:]
    elif "\n### Fixed\n" in section:
        raise AnchorError("the Unreleased section's '### Fixed' heading is not followed by a blank line, or repeats")
    elif section.count("\n### Security\n") == 1:
        # Keep a Changelog's order: Added, Changed, Deprecated, Removed, Fixed, Security
        section = section.replace("\n### Security\n", f"\n### Fixed\n\n{entry}\n### Security\n", 1)
    else:
        # a release proposal leaves [Unreleased] empty: the entry's own newline ends it, and the next section starts
        # with one, so exactly one blank line separates them
        section = section.rstrip("\n") + f"\n\n### Fixed\n\n{entry}"
    return changelog[:start] + section + (changelog[end:] if end >= 0 else "")


def result_of(value: str | None, name: str) -> str:
    if value is None or not re.fullmatch(r"\d+/\d+", value):
        raise ValueError(f"{name} must look like 4/4, not {value!r}")
    killed, total = value.split("/")
    return f"{killed} of {total}"


def self_test() -> int:
    head = "# Changelog\n\n## [Unreleased]\n\n"
    release = "## [0.11.3] - 2026-10-26\n\n### Fixed\n\n- old\n"
    entry = "- NEW\n  more\n"
    cases = [
        ("Fixed is the last subsection", head + "### Changed\n\n- c\n\n### Fixed\n\n- a\n- b\n\n" + release, head + "### Changed\n\n- c\n\n### Fixed\n\n- a\n- b\n- NEW\n  more\n\n" + release),
        ("Security follows Fixed", head + "### Fixed\n\n- a\n\n### Security\n\n- s\n\n" + release, head + "### Fixed\n\n- a\n- NEW\n  more\n\n### Security\n\n- s\n\n" + release),
        ("no Fixed, Security present", head + "### Changed\n\n- c\n\n### Security\n\n- s\n\n" + release, head + "### Changed\n\n- c\n\n### Fixed\n\n- NEW\n  more\n\n### Security\n\n- s\n\n" + release),
        ("only Changed", head + "### Changed\n\n- c\n\n" + release, head + "### Changed\n\n- c\n\n### Fixed\n\n- NEW\n  more\n\n" + release),
        ("an empty Unreleased after a cut", head + release, head + "### Fixed\n\n- NEW\n  more\n\n" + release),
        ("no release below Unreleased", head + "### Fixed\n\n- a\n", head + "### Fixed\n\n- a\n- NEW\n  more\n"),
        ("the marker sits in a release section", head + release.replace("- old", f"- {CHANGELOG_MARKER}"), head + release.replace("- old", f"- {CHANGELOG_MARKER}")),
        ("a Fixed heading with no blank line", head + "### Fixed\n- a\n\n" + release, AnchorError),
        ("no Unreleased section", "# Changelog\n\n" + release, AnchorError),
    ]
    passed = 0
    for name, text, want in cases:
        marked = entry.replace("- NEW", f"- {CHANGELOG_MARKER} NEW")
        want_text = want.replace("- NEW", f"- {CHANGELOG_MARKER} NEW") if isinstance(want, str) else want
        try:
            have = add_changelog_entry(text, marked)
            ok = have == want_text and add_changelog_entry(have, marked) == have
        except AnchorError:
            ok = want is AnchorError
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    print(f"self-test: {passed} of {len(cases)} passed")
    return 0 if passed == len(cases) else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mutants", help="this change's mutation result, N/M")
    ap.add_argument("--g1", help="the G1 mutation result, N/M")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        entry = CHANGELOG_ENTRY.replace("@MUTANTS@", result_of(args.mutants, "--mutants")).replace("@G1@", result_of(args.g1, "--g1"))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    path = Path(args.base) / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    try:
        new = add_changelog_entry(text, entry)
    except AnchorError as exc:
        print(f"ANCHOR: {exc}", file=sys.stderr)
        return 2
    if new == text:
        print("nothing to do: the entry is already present")
        return 0
    print(f"{'would change' if args.check else 'changed'}: CHANGELOG.md")
    if not args.check:
        path.write_text(new, encoding="utf-8")
    return 1 if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
