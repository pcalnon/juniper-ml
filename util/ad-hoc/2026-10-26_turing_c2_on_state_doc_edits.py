"""
Apply the C2 on-state PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-26
Status: ad-hoc — landing helper (turing bring-up task C2: the gate reads the block-all sentence turing printed)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2 C2 row; erratum
         E-C2-GATE); util/host_state_check.py; tests/test_host_state_check.py;
         util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py (the shape this follows, and whose markers these
         edits leave in place, so its --check still prints "nothing to do")

Why: the shared files take concurrent whole-file uploads, so each upload is built by running this against a
FRESH `origin/main` copy at upload time (the juniper-ml#2262 revert class). Every edit has a marker (skip
when present) and an anchor that must occur exactly once. The files: `docs/REFERENCE.md` and `CHANGELOG.md`.
The CHANGELOG marker counts anywhere in the file, so a release cut that moves the entry does not re-add it
(erratum E-CUT). The plan's record is a separate PR.

Usage:
    python3 -I util/ad-hoc/2026-10-26_turing_c2_on_state_doc_edits.py [--base DIR] [--check] --mutants N/M

`--mutants N/M` is the result of util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py to record
(for example `12/12`).

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
MUTATION = "util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py"
G1_MUTATION = "util/ad-hoc/2026-10-20_turing_g1_mutation_check.py"

# docs/REFERENCE.md, § Test Suite Reference: tests/test_host_state_check.py
REF_SENTENCE_OLD = "reports block all, in either of the binary's two sentences. An unknown block-all state, or a probe without the capture,"
REF_SENTENCE_NEW = (
    "reports block all, in the sentence turing's getter printed once the owner applied C2 (2026-10-26; its on-state captures are"
    " pinned). An unknown block-all state, `--setblockall`'s confirmation sentence (which juniper-ml#2338 took for the getter's),"
    " or a probe without the capture,"
)
REF_SENTENCE_MARKER = "in the sentence turing's getter printed once the owner applied C2"
REF_MUTANTS_OLD = f"`{MUTATION}` kills 11 of 11 mutants, and the 57"

CHANGELOG_MARKER = "**G-SEC's firewall condition reads the block-all sentence turing printed**"
CHANGELOG_ENTRY = (
    f"- {CHANGELOG_MARKER} (turing bring-up task C2; the §18.2\n"
    f"  C2 row and erratum E-C2-GATE of `{PLAN}`).\n"
    "  The owner applied C2's block-all form on 2026-10-26, so the on-state captures exist: `--getglobalstate` prints\n"
    "  \"Firewall is blocking all non-essential incoming connections. (State = 2)\", `--getblockall` \"Firewall is blocking\n"
    "  all non-essential incoming connections.\" and `--getstealthmode` \"Firewall stealth mode is on\".\n"
    "  - `util/host_state_check.py` accepts only the getter's sentence. \"Firewall is set to block all non-essential\n"
    "    incoming connections\", which juniper-ml#2338 took for the getter's, sits beside \"Block all DISABLED!\" in the\n"
    "    binary's strings, the shape of `--setblockall`'s confirmations. A capture holding it cannot be judged (exit 2\n"
    "    under `--check`), unless the firewall is off, which fails anyway.\n"
    "  - `tests/test_host_state_check.py` pins turing's on-state captures and the setter's sentence: `FirewallTest`\n"
    "    gains 2 tests (61 across the two G1 suites). B7 of\n"
    f"    `{MUTATION}` now re-accepts the setter's sentence, and B12\n"
    "    re-introduces the #2338 premise; it kills @MUTANTS@ mutants, and the 57 of\n"
    f"    `{G1_MUTATION}` still apply.\n"
    "  - turing's firewall condition passes. G-SEC still fails, on SIP (task C1) and the key exports (task C3).\n"
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
    if CHANGELOG_MARKER in changelog:
        return changelog  # anywhere: after a release cut the entry sits in the release section
    start = changelog.find("## [Unreleased]")
    if start < 0:
        raise AnchorError("CHANGELOG.md has no '## [Unreleased]' section")
    end = changelog.find("\n## [", start + 1)
    section = changelog[start : end if end >= 0 else len(changelog)]
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
            # a release proposal leaves [Unreleased] empty, or holds only Added: append the subsection. The entry's
            # own newline ends it, and the next section starts with one, so exactly one blank line separates them.
            section = section.rstrip("\n") + f"\n\n### Changed\n\n{entry}"
    return changelog[:start] + section + (changelog[end:] if end >= 0 else "")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mutants", required=True, help="the C2 gate mutation result, N/M")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d+/\d+", args.mutants):
        print("--mutants must look like 12/12", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    base = Path(args.base)
    names = ("docs/REFERENCE.md", "CHANGELOG.md")
    texts = {name: (base / name).read_text(encoding="utf-8") for name in names}
    ref_mutants_new = f"`{MUTATION}` kills {killed} of {total} mutants, and the 57"
    try:
        ref = texts["docs/REFERENCE.md"]
        ref = replace_once(ref, REF_SENTENCE_OLD, REF_SENTENCE_NEW, REF_SENTENCE_MARKER)
        ref = replace_once(ref, REF_MUTANTS_OLD, ref_mutants_new, ref_mutants_new)
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
