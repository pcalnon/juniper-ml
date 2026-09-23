#!/usr/bin/env python3
"""
Archive the CI-budget re-evaluation's consensus-round reports VERBATIM from the session transcripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consensus provenance)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- single-use archiver; reads local session transcripts, writes reports/
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

A subagent's final report lives only in local session transcripts, which are unversioned and go
with the machine. This copies each lane's final message into
reports/2026-09-22_ci-budget-reeval-consensus/, one file per lane, under a short header. Nothing
inside a report is edited.

SOURCE: the lane's OWN transcript, `<session>/subagents/agent-<id>.jsonl` -- the text of its last
assistant message. The task notification the orchestrator received is a second copy, and it is
not verbatim: it HTML-escapes `<`, `>` and `&` (round 5 found 13 of 15 archived reports carrying
`&lt;` and `&amp;amp;` inside code spans). So each notification copy is unescaped and must equal
the lane's own message, or nothing is written for that lane.

The orchestrator's own READS of a saved report are also in the transcript, rendered with
"   221\t" line numbers and longer than the original; those copies are ignored.

It refuses credential-shaped text, and lists every markdown link a report contains, since the
required link checker resolves them from reports/.

Usage: python3 archive_round_reports.py <main session transcript .jsonl> [--check]
  --check  extract, cross-check and scan only; write nothing
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "reports/2026-09-22_ci-budget-reeval-consensus"
PROCEDURE = "notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md"

FROZEN = {1: "ml#2017 at `53d05121`", 2: "ml#2017 at `d873aed6`", 3: "ml#2017 at `f0b3cc73`", 4: "ml#2035 at `0ffe15dc`", 5: "ml#2035 at `bdd60b20`"}

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
    "a17cc8a20cd51e529": (5, "round5", "one reviewer -- re-derive the round-4 claims and find what the corrections broke"),
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


def own_final_message(agent_log: Path) -> str | None:
    """The text of the lane's LAST assistant message, from its own transcript."""
    last = None
    if not agent_log.is_file():
        return None
    with agent_log.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "assistant":
                continue
            content = (rec.get("message") or {}).get("content")
            if isinstance(content, list):
                text = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
                if text.strip():
                    last = text
    return last.strip("\n") if last is not None else None


def notification_copies(transcript: Path) -> dict:
    """Each lane's <result> as the orchestrator received it, unescaped; numbered renderings skipped."""
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
                    lines = [ln for ln in body.splitlines() if ln.strip()]
                    if lines and sum(1 for ln in lines if NUMBERED.match(ln)) > len(lines) // 2:
                        continue
                    if len(body) > len(found.get(tid, "")):
                        found[tid] = body
    return {tid: html.unescape(body) for tid, body in found.items()}


def header(rnd: int, title: str) -> str:
    return (
        f"# CI-budget re-evaluation -- consensus round {rnd}, {title}\n"
        "\n"
        f"- **Procedure**: [`{PROCEDURE}`](../../{PROCEDURE})\n"
        f"- **Document under test**: [`{HANDOFF.split('/')[-1]}`](../../{HANDOFF}) and the PR carrying it\n"
        f"- **Frozen at**: {FROZEN[rnd]}\n"
        "- **Archived**: the lane's final message, copied verbatim from its own session transcript\n"
        "  on 2026-09-23 and cross-checked against the task notification. Nothing below the rule\n"
        "  is edited; the reconciliation is the handoff's § Validation record 2026-09-22.\n"
        "\n"
        "---\n"
        "\n"
    )


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    transcript = Path(sys.argv[1])
    check_only = "--check" in sys.argv[2:]
    agents = transcript.with_suffix("") / "subagents"
    notes = notification_copies(transcript)
    rc = 0
    for tid, (rnd, stem, title) in LANES.items():
        own = own_final_message(agents / f"agent-{tid}.jsonl")
        note = notes.get(tid)
        if own is None:
            print(f"  missing  {stem}: no final message in {agents.name}/agent-{tid}.jsonl")
            rc = 1
            continue
        if note is not None and note.strip() != own.strip():
            print(f"  REFUSED  {stem}: the notification copy differs from the lane's own message ({len(note)} vs {len(own)} chars)")
            rc = 1
            continue
        hits = SECRET.findall(own)
        if hits:
            print(f"  REFUSED  {stem}: {len(hits)} credential-shaped string(s); nothing written for it")
            rc = 1
            continue
        links = LINK.findall(own)
        agree = "cross-checked" if note is not None else "no notification copy to cross-check"
        print(f"  ok       {stem}: {len(own)} chars, {agree}; markdown links: {links[:5]}{' ...' if len(links) > 5 else ''}")
        text = own.rstrip()
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
