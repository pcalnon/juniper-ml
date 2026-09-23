#!/usr/bin/env python3
"""
Archive the CI-budget re-evaluation's consensus-round reports VERBATIM from the session transcript.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consensus provenance)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- single-use archiver; reads a local session transcript, writes reports/
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

A subagent's final report lives only in the local session transcript, which is unversioned and
goes with the machine. This copies each lane's final message -- the text between <result> and
</result> in its task notification -- into reports/2026-09-22_ci-budget-reeval-consensus/, one
file per lane, under a short header. Nothing inside a report is edited.

It refuses to write anything that matches a credential pattern, and it lists every markdown link
a report contains, since the required link checker resolves them from reports/.

Usage: python3 archive_round_reports.py <session transcript .jsonl> [--check]
  --check  extract and scan only; write nothing
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports/2026-09-22_ci-budget-reeval-consensus"
PROCEDURE = "notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md"

FROZEN = {1: "ml#2017 at `53d05121`", 2: "ml#2017 at `d873aed6`", 3: "ml#2017 at `f0b3cc73`", 4: "ml#2035 at `0ffe15dc`"}

# task id -> (round, file stem, lane title)
LANES = {
    "a4c03471f975e5d97": (1, "round1-laneA1", "Lane A1 -- history and timelines (git, PR and Actions history only)"),
    "a630518bcfa77b960": (1, "round1-laneA2", "Lane A2 -- the CI spans, re-measured by an independent instrument"),
    "a51898e0b59d3e7bb": (1, "round1-laneA3", "Lane A3 -- file content and execution"),
    "a00dc7d680714925e": (1, "round1-laneB1", "Lane B1 -- omission and executability"),
    "acb8f68b031b3423a": (1, "round1-laneB2", "Lane B2 -- argue HOLD on the budget re-pin"),
    "ab32cf5baa3c99646": (1, "round1-laneB3", "Lane B3 -- argue SHIP, and attack the soak verdict"),
    "a0eabba82bdad5ac0": (1, "round1-rubric", "Rubric -- prompt-validator, iteration 1"),
    "ad50ffaaf0de39210": (2, "round2-laneA", "Lane A -- re-derive the new figures"),
    "a1dd0303402f7936f": (2, "round2-laneB", "Lane B -- find what the round-1 fixes broke"),
    "aae415ade99f5851f": (2, "round2-rubric", "Rubric -- prompt-validator, iteration 2"),
    "a6d9c1af2cd92d9b7": (3, "round3-laneA", "Lane A -- re-derive the new figures"),
    "a439dc7976511b401": (3, "round3-laneB", "Lane B -- find what the round-2 fixes broke"),
    "aac48611fe50d5651": (3, "round3-rubric", "Rubric -- prompt-validator, iteration 3"),
    "a59ca4c4e0176fbea": (4, "round4-laneA", "Lane A -- re-derive the round-3 claims"),
    "a27dd7f08afbeb72a": (4, "round4-laneB", "Lane B -- find what the round-3 fixes broke"),
}

SECRET = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{32,}|AGE-SECRET-KEY-1[0-9A-Z]{20,})")
LINK = re.compile(r"\]\(([^)\s]+)\)")
NUMBERED = re.compile(r"^\s*\d+\t")


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)


def extract(transcript: Path) -> dict:
    found: dict = {}
    with transcript.open(encoding="utf-8") as f:
        for line in f:
            if "<task-notification>" not in line or "<result>" not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for s in strings(rec):
                for tid in LANES:
                    anchor = s.find(f"<task-id>{tid}</task-id>")
                    if anchor < 0:
                        continue
                    end = s.find("</task-notification>", anchor)
                    seg = s[anchor : end if end > 0 else len(s)]
                    i, j = seg.find("<result>"), seg.find("</result>")
                    if i < 0 or j < i:
                        continue
                    body = seg[i + len("<result>") : j].strip("\n")
                    # The transcript also holds the orchestrator's own READS of a saved report,
                    # rendered with "   221\t" line numbers -- longer than the original, so a
                    # longest-copy rule would archive the rendering. Only an unnumbered copy is
                    # the report as delivered.
                    lines = [ln for ln in body.splitlines() if ln.strip()]
                    if lines and sum(1 for ln in lines if NUMBERED.match(ln)) > len(lines) // 2:
                        continue
                    if len(body) > len(found.get(tid, "")):
                        found[tid] = body
    return found


def header(rnd: int, title: str) -> str:
    return (
        f"# CI-budget re-evaluation -- consensus round {rnd}, {title}\n"
        "\n"
        f"- **Procedure**: [`{PROCEDURE}`](../../{PROCEDURE})\n"
        f"- **Document under test**: [`{HANDOFF.split('/')[-1]}`](../../{HANDOFF}) and the PR carrying it\n"
        f"- **Frozen at**: {FROZEN[rnd]}\n"
        "- **Archived**: the lane's final report, copied verbatim from the session transcript on\n"
        "  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's\n"
        "  § Validation record 2026-09-22.\n"
        "\n"
        "---\n"
        "\n"
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    check_only = "--check" in sys.argv[2:]
    found = extract(Path(sys.argv[1]))
    rc = 0
    for tid, (rnd, stem, title) in LANES.items():
        body = found.get(tid)
        if body is None:
            print(f"  missing  {stem}: no final report in the transcript (yet)")
            continue
        hits = SECRET.findall(body)
        if hits:
            print(f"  REFUSED  {stem}: {len(hits)} credential-shaped string(s); nothing written for it")
            rc = 1
            continue
        links = LINK.findall(body)
        print(f"  ok       {stem}: {len(body)} chars; markdown links: {links[:5]}{' ...' if len(links) > 5 else ''}")
        text = body.rstrip()
        if text.startswith("{"):
            # A bare JSON verdict renders as prose, and its quoted `[x](y)` strings then read as
            # links the required link checker cannot resolve. Fence it; the content is unchanged.
            text = "```json\n" + text + "\n```"
        if not check_only:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{stem}.md").write_text(header(rnd, title) + text + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())
