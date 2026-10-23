"""
Record H5's landing in the turing bring-up plan, idempotently (plan v1.4.4).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — one-off (the H5 record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§18, §18.2, §18.3);
         juniper-ml#2300 (H5: notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md);
         util/ad-hoc/2026-10-20_turing_g1_g4_record.py (the pattern)

Why: the plan is a shared file, so the edits are anchored on text and re-run on a fresh origin/main copy before the
upload (E-LAND-2). Each edit reports `present`, `applied` or `MISSING`; if any anchor is missing, nothing is written.

    python3 -I util/ad-hoc/2026-10-21_turing_h5_record.py [--root DIR] [--dry-run]

The edits, all in the plan:
  1. the Version line, 1.4.3 -> 1.4.4. Only from 1.4.3: another version is reported and left alone;
  2. §18's opening paragraph names the session H5 landed in and its handoff;
  3. §18.2's H5 row (landed; the owner's decision pending);
  4. §18.3 gains erratum E-H5 (D10's "disabled until audited", against what the audit found).

Exit 0 = every edit is present or applied (or would be, under --dry-run); 1 = an anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
HANDOFF_DIR = "prompts/thread-handoff_automated-prompts/"
PREVIOUS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h2-h4-landed-c9-next.md"
THIS_HANDOFF = HANDOFF_DIR + "HANDOFF_2026-10-21_turing-h5-audit-landed-owner-decides.md"
AUDIT = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md"
EVIDENCE = "util/ad-hoc/2026-10-21_turing_h5_mcp_server_inventory.py"
H5_PR, H5_SHA = "juniper-ml#2300", "2f831b60"

VERSION_OLD = "- **Version**: 1.4.3 — v1.4.2 plus H2's and H4's landing"
VERSION_NEW = (
    "- **Version**: 1.4.4 — v1.4.3 plus H5's landing (§18.2's H5 row; erratum E-H5 in §18.3; 2026-10-21). v1.4.3 was "
    "v1.4.2 plus H2's and H4's landing"
)

INTRO_OLD = f"H2 and H4 landed in the session after that (v1.4.3), whose handoff is `{PREVIOUS_HANDOFF}`."
INTRO_NEW = (
    f"{INTRO_OLD} H5 landed alongside them, in the \"mac dev\" session (v1.4.4), whose handoff is `{THIS_HANDOFF}`."
)

H5_PREFIX = '| H5 | with the "mac dev" session |'
H5_ROW = (
    f"| H5 | landed; **the owner's decision is pending** | {H5_PR} (`{H5_SHA}`), in the \"mac dev\" session (E-SPLIT). "
    f"The `auditor` agent's static audit, `{AUDIT}`, with its read-only evidence script `{EVIDENCE}`, which compares "
    "each tree with its upstream at HEAD blob by blob (305 of 305 and 33 of 33 identical). 25 findings: 3 blocker, 9 "
    "major and 13 minor. **It recommends removing both.** adaptive-graph-of-thoughts: its one standard-MCP entry point, "
    "the DXT Node server, builds its results from `Math.random()` (AGOT-A1); the Python server's default HTTP mode binds "
    "`0.0.0.0:8000` with fail-open Basic auth (AGOT-A3); and a tracked `.claude/settings.local.json` pre-approves "
    "interpreters (AGOT-A2). agi-mcp-server: its `origin` and its documented `npx -y github:` launch point into the "
    "squatted `cognitivecomputations` namespace (AGI-P1), and its 24 tools are a cross-session memory store (AGI-A1). "
    "Neither exposes a file-writing or command-running tool, so C9 does not attach; their database and network tools "
    "would still run outside C8 (H5-X1). Neither is configured in any client config checked, and neither is running. "
    "The owner's commands for each choice are in the audit's §8 (E-H5) |"
)

ERRATA_ANCHOR = "\n\n## 19. Commit signing for the terminal and the IDEs"
ERRATA = (
    "\n- **E-H5 (D10's \"disabled until audited\", against H5's findings).** D10 and §10 treat the two trees as "
    "dormant until audited, and H0 checked only whether they were configured.\n"
    "  - **They had already run.** On 2026-03-01, before this plan, an `npm install` in agi-mcp-server ran three "
    "esbuild postinstall hooks, each of which executed a native binary from npm, and a CPython 3.13 imported two "
    "adaptive-graph-of-thoughts modules (AGI-H1, AGOT-H1). The audit dates both from the trees' own files.\n"
    "  - **An unconfigured clone can still act.** adaptive-graph-of-thoughts tracks a `.claude/settings.local.json` "
    "whose 41 allow rules (interpreters, `rm`, `claude mcp add`) apply to any Claude Code session opened in the tree "
    "(AGOT-A2). Never open Claude Code inside an untrusted clone.\n"
    "  - **So can a pull.** agi-mcp-server's `origin` names an organization that upstream calls squatted. GitHub's "
    "redirect to `QuixiAI` lasts only until the holder creates a repository of that name (AGI-P1).\n"
    "  - **C9 judges paths, not every write.** A server whose tools write a database or call out without taking a "
    "path, as both of these do, needs `permissions.deny` rules on `mcp__<server>__<tool>` instead (H5-X1)."
)


def edit(text: str, old: str, new: str, done_mark: str, label: str, report: list) -> str:
    if done_mark in text:
        report.append(f"present  {label}")
        return text
    if text.count(old) != 1:
        report.append(f"MISSING  {label}: anchor found {text.count(old)} times")
        return text
    report.append(f"applied  {label}")
    return text.replace(old, new)


def replace_row(text: str, prefix: str, new_row: str, label: str, report: list) -> str:
    if new_row in text:
        report.append(f"present  {label}")
        return text
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        report.append(f"MISSING  {label}: {len(hits)} rows start with {prefix!r}")
        return text
    lines[hits[0]] = new_row
    report.append(f"applied  {label}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if H5_SHA == "PENDING":
        print(f"H5_SHA is not set: fill in {H5_PR}'s merge sha first")
        return 1
    path = args.root / PLAN
    text = original = path.read_text(encoding="utf-8")
    report: list[str] = []
    if "- **Version**: 1.4.4 —" in text:
        report.append("present  Version line 1.4.4")
    elif VERSION_OLD in text:
        text = text.replace(VERSION_OLD, VERSION_NEW)
        report.append("applied  Version line 1.4.4")
    else:
        report.append("MISSING  Version line: the plan is at neither 1.4.3 nor 1.4.4")
    text = edit(text, INTRO_OLD, INTRO_NEW, THIS_HANDOFF, "§18 opening paragraph: H5's session", report)
    text = replace_row(text, H5_PREFIX, H5_ROW, "§18.2 H5 row", report)
    text = edit(text, ERRATA_ANCHOR, ERRATA + ERRATA_ANCHOR, "- **E-H5 (D10's", "§18.3 erratum E-H5", report)
    print("\n".join(report))
    if any(line.startswith("MISSING") for line in report):
        print("nothing written")
        return 1
    changed = text != original
    if changed and not args.dry_run:
        path.write_text(text, encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {int(changed)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
