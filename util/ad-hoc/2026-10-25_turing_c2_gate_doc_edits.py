"""
Apply the C2 gate PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-25
Status: ad-hoc — landing helper (turing bring-up task C2's gate follow-up, owner ruling 2026-10-25)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18.2 C2 row; gate G-SEC);
         util/host_state_probe.bash; util/host_state_check.py; tests/test_host_state_check.py;
         util/ad-hoc/2026-10-25_turing_h4_usage_report_doc_edits.py (the shape this follows)

Why: the shared files take concurrent whole-file uploads, so each upload is built by running this against a
FRESH `origin/main` copy at upload time (the juniper-ml#2262 revert class). Every edit has a marker (skip
when present) and an anchor that must occur exactly once. The files: `docs/REFERENCE.md` and `CHANGELOG.md`.
The plan's record of the ruling is a separate PR.

Usage:
    python3 -I util/ad-hoc/2026-10-25_turing_c2_gate_doc_edits.py [--base DIR] [--check] --mutants N/M

`--mutants N/M` is the result of util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py to record
(for example `11/11`).

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
ANALYSIS = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md"
MUTATION = "util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py"
G1_MUTATION = "util/ad-hoc/2026-10-20_turing_g1_mutation_check.py"

# docs/REFERENCE.md, § Test Suite Reference: tests/test_host_state_check.py
REF_SUITE_COUNT_OLD = "There are 55 such cases, among them turing's own captures: SIP's custom configuration, en7 with no carrier"
REF_SUITE_COUNT_NEW = "There are 58 such cases, among them turing's own captures: SIP's custom configuration, the firewall off with block all disabled, en7 with no carrier"
REF_SUITE_TAIL_OLD = "with `conf/hosts/turing/conda-envs/` on the envs.\n"
# docs/REFERENCE.md, § Utility Script Reference: util/host_state_probe.bash and util/host_state_check.py
REF_PROBE_OLD = "power, security, tools, env, alias"
REF_PROBE_NEW = "power, security (with `socketfilterfw --getblockall` since 2026-10-25, for task C2), tools, env, alias"
REF_CHECK_OLD = "G-SEC; G-TOOLS (erratum E-D6"
REF_CHECK_NEW = "G-SEC (its firewall condition needs the firewall on and blocking all incoming connections: task C2's block-all form, owner ruling 2026-10-25); G-TOOLS (erratum E-D6"

CHANGELOG_MARKER = "**G-SEC's firewall condition follows C2's block-all form**"
CHANGELOG_ENTRY = (
    f"- {CHANGELOG_MARKER} (turing bring-up task C2, the §18.2 C2 row of\n"
    f"  `{PLAN}`; owner ruling 2026-10-25).\n"
    "  The owner chose to block all incoming connections while nothing inbound is needed, over per-app inbound\n"
    f"  denies (RR-11 of `{ANALYSIS}`).\n"
    "  The condition passed at `State = 1`, and its fix still said \"allowing signed software\".\n"
    "  - `util/host_state_probe.bash` also captures `socketfilterfw --getblockall` (`blockall` in the security section).\n"
    "  - `util/host_state_check.py` passes the firewall only when it is on and `--getblockall` reports block all. It\n"
    "    accepts both block-all sentences in the binary's strings, since turning block all on needs the owner's sudo.\n"
    "    An unknown or undefined state, or a probe without the capture, cannot be judged (exit 2 under `--check`),\n"
    "    unless the firewall is off, which fails anyway. The fix names only the missing `socketfilterfw` steps.\n"
    "    Stealth mode stays reported, not gated, as G1 designed it.\n"
    "  - `tests/test_host_state_check.py` gains 3 failure cases and a `FirewallTest` class of 5 tests (59 tests across\n"
    "    the two G1 suites), and `tests/test_host_state_probe.py` pins the capture.\n"
    f"    `{MUTATION}` kills @MUTANTS@ mutants, and the 57 of `{G1_MUTATION}` still apply.\n"
    "  - `conf/hosts/turing/expected.yaml`'s G-SEC comment follows. turing still fails the condition: its firewall is\n"
    "    off (`State = 0`), as it was on 2026-10-15.\n"
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
    ap.add_argument("--mutants", required=True, help="the C2 gate mutation result, N/M")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d+/\d+", args.mutants):
        print("--mutants must look like 11/11", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    base = Path(args.base)
    names = ("docs/REFERENCE.md", "CHANGELOG.md")
    texts = {name: (base / name).read_text(encoding="utf-8") for name in names}
    suite_tail = (
        "with `conf/hosts/turing/conda-envs/` on the envs. G-SEC's firewall condition follows task C2's block-all form (owner ruling"
        " 2026-10-25): it passes only when the firewall is on and `socketfilterfw --getblockall` reports block all, in either of the"
        " binary's two sentences. An unknown block-all state, or a probe without the capture, cannot be judged unless the firewall is"
        " off, which fails anyway; the fix names only the missing steps; stealth mode is reported, not gated (`FirewallTest`)."
        f" `{MUTATION}` kills {killed} of {total} mutants, and the 57 of `{G1_MUTATION}` still apply.\n"
    )
    try:
        ref = texts["docs/REFERENCE.md"]
        ref = replace_once(ref, REF_SUITE_COUNT_OLD, REF_SUITE_COUNT_NEW, "There are 58 such cases")
        ref = replace_once(ref, REF_SUITE_TAIL_OLD, suite_tail, "G-SEC's firewall condition follows task C2's block-all form")
        ref = replace_once(ref, REF_PROBE_OLD, REF_PROBE_NEW, "security (with `socketfilterfw --getblockall` since 2026-10-25")
        ref = replace_once(ref, REF_CHECK_OLD, REF_CHECK_NEW, "G-SEC (its firewall condition needs the firewall on and blocking all")
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
