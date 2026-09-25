#!/usr/bin/env python3
"""
Complete the defect-register round-42 report archive, and verify the part already archived.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use archiver; reads local session transcripts, writes reports/
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Round 42 of the defect-register arc ran its validation and fix work in background agents of session
bc31e993 (worktree `happy-skipping-hollerith`). A subagent's final report lives only in that
session's local transcript, `<session>/subagents/agent-<id>.jsonl`, which is unversioned and goes
with the machine.

juniper-ml#2072 archived eight of those reports (plus three stubs of agents stopped mid-flight) in
reports/2026-09-24_defect-register-round-42/. It left out the round's EARLIER rounds: ml#2032
rounds 1 and 2, canopy#660 round 1, data#428 round 1 and cascor#678's pre-merge validation. This
adds those seven in the same format, and every later report of the round as its lanes finish (the
post-merge rounds run in session 8f86dec2). It also re-extracts every report already in the
directory to check that its body is still identical to its agent's last message. A file adds only
the header, a blank line after it and a final newline.

The task notification the orchestrator received is NOT a source: it HTML-escapes `<`, `>` and `&`
(memory: reference_subagents_killed_by_session_limit_resume_with_sendmessage.md). A report that
carries credential-shaped text or the owner's email address is refused.

Usage: python3 2026-09-24_archive_round42_reports.py [--check]
  --check  extract, verify and scan only; write nothing
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/2026-09-24_defect-register-round-42"
HEADER = "<!-- Archived verbatim 2026-09-24 from subagent {aid} of session {session} (final message). -->\n\n"
HEADER_RE = re.compile(r"^<!-- Archived verbatim \S+ from subagent (a[0-9a-f]{16}) of session ([0-9a-f]{8}) \(final message\)\. -->\n\n")

# Session id (8 hex) -> the session's full id. bc31e993 ran rounds 1-2 and the fix agents; 8f86dec2
# (worktree `hazy-beaming-map`) ran the post-merge rounds of 2026-09-24; 2fba4397 (worktree
# `fizzy-hugging-dream`) took over from it the same day.
#
# The transcripts are found by the session's id, never by a fixed path. This held a fixed
# `<project>/<session>/subagents` path per session until 2026-09-24, and --check crashed with
# FileNotFoundError on every 8f86dec2 report the same day: when a session leaves its worktree, its
# transcripts move from the worktree's project directory
# (`-home-...-juniper-ml--claude-worktrees-hazy-beaming-map/`) to the main checkout's
# (`-home-...-juniper-ml/`), so the path is a property of the moment, not of the session.
PROJECTS = Path.home() / ".claude/projects"
SESSION_IDS = {
    "bc31e993": "bc31e993-97b0-4a01-ae04-cb39593eb647",
    "8f86dec2": "8f86dec2-21ea-43f2-911a-bb2314a822ec",
    "2fba4397": "2fba4397-7d9b-4929-8ca2-375b8168e1c8",
}


def subagents_dir(session: str) -> Path:
    """The session's subagents directory, wherever its project directory is now."""
    if session not in SESSION_IDS:
        raise SystemExit(f"session {session}: not in SESSION_IDS; add its full id before archiving or checking its reports")
    hits = sorted(PROJECTS.glob(f"*/{SESSION_IDS[session]}/subagents"))
    if len(hits) != 1:
        raise SystemExit(f"session {session}: expected one subagents directory under {PROJECTS}, found {len(hits)}: {hits}")
    return hits[0]


def transcript(session: str, aid: str) -> Path:
    """An agent's transcript, refused with a message (not a bare FileNotFoundError) when it is not there."""
    path = subagents_dir(session) / f"agent-{aid}.jsonl"
    if not path.is_file():
        raise SystemExit(f"session {session}: no transcript for agent {aid} at {path}; check the id in MISSING or the report's header")
    return path


# The seven reports juniper-ml#2072 did not archive: agent id -> file name (its naming style).
# Deliberately NOT archived: a636d9155e8d8883f and a62c802ad61b85d03 are the canopy#660 and
# cascor#678 BUILDERS (their work is the PRs; #2072 archives the cascor one's implementation report),
# and the three C-A forks afab1a407fc2743f6, a8d71bd0256c706db, a80074753d6ce9ade died at launch.
MISSING = {
    # 8f86dec2: the post-merge round-3 lanes on data#428 (validated at `3a76a4c`).
    "a5e53dde657452894": ("8f86dec2", "data428-round3-laneA1-security.md"),
    "a40325befd1022f04": ("8f86dec2", "data428-round3-laneA2-claims.md"),
    "ada46055013dac0d6": ("8f86dec2", "data428-round3-laneB-refute.md"),
    # 8f86dec2: round 4 of juniper-ml#2032 (its round-3 corrections) together with juniper-ml#2059.
    "a9498cdd07e19a630": ("8f86dec2", "ml2032-2059-round4-laneA-reprobe.md"),
    "af44b0238ad7dfe0c": ("8f86dec2", "ml2032-2059-round4-laneB-refute.md"),
    # 8f86dec2: round 1 of the API primer's artifact-validator correction (Appendix E, v1).
    "a9d3743d17bb6ab8d": ("8f86dec2", "primer-correction-round1-laneA-reprobe.md"),
    "a256e7aa15a92fe2d": ("8f86dec2", "primer-correction-round1-laneB-refute.md"),
    # 8f86dec2: the post-merge validation of juniper-ml#2074, this round's own register PR.
    "a990ab20a1bd18405": ("8f86dec2", "ml2074-round1-laneA-reprobe.md"),
    "a69df29a8e3cd7134": ("8f86dec2", "ml2074-round1-laneB-refute.md"),
    # 8f86dec2: round 2 of the API primer's correction (v2, juniper-ml#2075).
    "a7631c36ca821d652": ("8f86dec2", "primer-correction-round2-laneA-reprobe.md"),
    "ad32dacf1c456fe8b": ("8f86dec2", "primer-correction-round2-laneB-refute.md"),
    # 8f86dec2: round 1 of juniper-data#438, the fix-forward of #428's round 3.
    "a66ebaf4cc1925e56": ("8f86dec2", "data438-round1-laneA-reprobe.md"),
    "a48b63fe2cf4ce38b": ("8f86dec2", "data438-round1-laneB-refute.md"),
    # 8f86dec2: the post-merge validation of juniper-ml#2080 (register fix-forward) and #2075 v3 (primer).
    "a3212838e6d1674b7": ("8f86dec2", "ml2080-round1-laneA-reprobe.md"),
    "a833573c5bbdf2a36": ("8f86dec2", "ml2080-round1-laneB-refute.md"),
    # 2fba4397: the PRE-PR validation of the second fix-forward (branch docs/register-round-42-second-fixforward,
    # validated at e2f87aae before any PR existed, because the owner's sweeper merges an open PR once green).
    "a0511a4be64379a82": ("2fba4397", "register-fixforward2-round1-laneA-reprobe.md"),
    "a4ae44a7ce58056a9": ("2fba4397", "register-fixforward2-round1-laneB-refute.md"),
    # 2fba4397: round 2 of the same pre-PR validation, on the round-1 corrections (990ef3f9).
    "aa5b6a0674e3d3218": ("2fba4397", "register-fixforward2-round2-laneA-reprobe.md"),
    "aee68ba42bd222c6e": ("2fba4397", "register-fixforward2-round2-laneB-refute.md"),
    # 2fba4397: the PRE-PR validation of juniper-data#438's fix-forward (branch
    # fix/conditional-requests-round4-followups, validated at d1c66a11 before any PR existed).
    "a6afb722d69732ae5": ("2fba4397", "data438-fixforward-round1-laneA-reprobe.md"),
    "a641405b9532742e6": ("2fba4397", "data438-fixforward-round1-laneB-refute.md"),
    # 2fba4397: the executor that fixed those two reports' findings and pushed 94ce8b1f (its disposition report).
    "a46e715a6801b98ca": ("2fba4397", "data438-fixforward-round1-fix-report.md"),
    # 2fba4397: round 1 of the consensus validation of this session's own handoff
    # (HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md).
    "ac06b2699a8d933a3": ("2fba4397", "handoff-2fba4397-round1-laneF-reprobe.md"),
    "a6a7b815d4ecf1415": ("2fba4397", "handoff-2fba4397-round1-laneO-amputation.md"),
    "a6664729992745f8d": ("2fba4397", "handoff-2fba4397-round1-laneP-fresh-session.md"),
    # 2fba4397: round 2 of the same validation, on the corrected handoff.
    "ad4c472203a4c4b54": ("2fba4397", "handoff-2fba4397-round2-laneF-reprobe.md"),
    "a75082d40b77328f3": ("2fba4397", "handoff-2fba4397-round2-laneO-amputation.md"),
    "aeb3e0b56825ec0c0": ("2fba4397", "handoff-2fba4397-round2-laneP-fresh-session.md"),
    # 2fba4397: round 3, on round 2's corrections (frozen at sha256 c9ef84f352a82857).
    "a55bb97b3f211dde1": ("2fba4397", "handoff-2fba4397-round3-laneF-reprobe.md"),
    "a315e24f7bb56eba5": ("2fba4397", "handoff-2fba4397-round3-laneP-fresh-session.md"),
    # 2fba4397: round 1 of the consensus validation of the CONSOLIDATED handoff
    # (HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md,
    # frozen at sha256 96c1b58f52fb5377), which merges the handoff above with the follow-up lane's and their predecessor.
    "a597cb4528bceda28": ("2fba4397", "handoff-consolidated-round1-laneF-reprobe.md"),
    "a6d7859ac840b7748": ("2fba4397", "handoff-consolidated-round1-laneO-amputation.md"),
    "a7ae702d3f586d2e0": ("2fba4397", "handoff-consolidated-round1-laneP-fresh-session.md"),
    # 2fba4397: round 2 of the same validation (frozen at sha256 79c0abb4b7dbdf15).
    "aac2e54444043de31": ("2fba4397", "handoff-consolidated-round2-laneF-reprobe.md"),
    "a8db50d2bc385a75e": ("2fba4397", "handoff-consolidated-round2-laneO-amputation.md"),
    "ae082bd285e35f93b": ("2fba4397", "handoff-consolidated-round2-laneP-fresh-session.md"),
    # 2fba4397: round 3 (frozen at sha256 cab844827349c45f).
    "ac5d48c366111b92f": ("2fba4397", "handoff-consolidated-round3-laneF-reprobe.md"),
    "abc3fd42a271ebb61": ("2fba4397", "handoff-consolidated-round3-laneP-fresh-session.md"),
    # 2fba4397: round 4, a delta round on round 3's corrections (frozen at sha256 6a052d09a1d2db6e).
    "ae1e0162ef5d928bd": ("2fba4397", "handoff-consolidated-round4-laneF-reprobe.md"),
    "a620da6fbd3c0217f": ("2fba4397", "handoff-consolidated-round4-laneO-amputation.md"),
    # bc31e993: the earlier rounds juniper-ml#2072 did not archive.
    "a6a4a26ed6b92d6e5": ("bc31e993", "ml2032-round1-laneA-reprobe.md"),
    "ab4b18fe07b799e1b": ("bc31e993", "ml2032-round1-laneB-attack.md"),
    "ad656809d6e1f3e92": ("bc31e993", "ml2032-round2-validation.md"),
    "aef8ba5499762289f": ("bc31e993", "canopy660-round1-validation.md"),
    "acbd22465744eb9e5": ("bc31e993", "data428-round1-laneA-reprobe.md"),
    "a58faf1967ffc6372": ("bc31e993", "data428-round1-laneB-attack.md"),
    "a4b7e2601c9990ad3": ("bc31e993", "cascor678-premerge-validation.md"),
}

SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{30,}"),
    # A PyPI token is "pypi-" plus a base64url macaroon, whose v2 serialization always opens "AgE".
    # The bare "pypi-[A-Za-z0-9_-]{40,}" matched a handoff FILENAME on 2026-09-25
    # ("…-on-pypi-and-pinned-the-stack-generates-…"), refusing a report that holds no token.
    re.compile(r"pypi-Ag[A-Za-z0-9_-]{40,}"),
    # A pypi.org macaroon body without its prefix. The bare "AgEIcHlwaS" matched a report that quoted
    # this very pattern in backticks (2026-09-25); a real token body runs on for hundreds of characters.
    re.compile(r"AgEIcHlwaS[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"gho_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[abpr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def _owner_email_pattern() -> "re.Pattern[str] | None":
    """The committer's own address, read at run time so that this file never embeds it."""
    try:
        email = subprocess.run(["git", "config", "user.email"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return re.compile(re.escape(email), re.IGNORECASE) if email else None


_OWNER = _owner_email_pattern()
if _OWNER is not None:
    SECRET_PATTERNS.append(_OWNER)


def last_report(path: Path) -> str:
    # split("\n"), never splitlines(): a transcript line may carry U+0085 / U+2028 inside a JSON
    # string (the canopy#678 reports quote U+0085 literally), and splitlines() cuts the record there.
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
    msgs = [r for r in rows if r.get("type") == "assistant"]
    if not msgs:
        raise SystemExit(f"{path.name}: no assistant message")
    return "\n".join(b.get("text", "") for b in msgs[-1]["message"]["content"] if b.get("type") == "text")


def main(argv: "list[str]") -> int:
    check = "--check" in argv[1:]
    failed = False

    # 1. Verify what is already archived: every file whose header names an agent must equal
    #    that agent's last message, byte for byte (after the header).
    existing = sorted(OUT.glob("*.md"))
    for f in existing:
        text = f.read_text(encoding="utf-8")
        m = HEADER_RE.match(text)
        if not m:
            print(f"  skip   {f.name}: no agent header")
            continue
        body = text[m.end():]
        again = last_report(transcript(m.group(2), m.group(1)))
        same = body.rstrip("\n") == again.rstrip("\n")
        failed |= not same
        print(f"  {'OK    ' if same else 'DIFFER'} {f.name}: archived body {'==' if same else '!='} agent {m.group(1)}'s last message")

    # 2. Add the missing reports.
    for aid, (session, name) in MISSING.items():
        target = OUT / name
        text = last_report(transcript(session, aid))
        # Name the owner's address by a label, never by its pattern: the pattern IS the address.
        hits = ["owner-email" if p is _OWNER else p.pattern for p in SECRET_PATTERNS if p.search(text)]
        if hits:
            print(f"  REFUSE {name}: credential-shaped text ({', '.join(hits)})")
            failed = True
            continue
        if target.exists():
            print(f"  exists {name}: left alone")
            continue
        print(f"  {'would add' if check else 'add   '} {name}: {len(text)} chars from agent {aid}")
        if not check:
            target.write_text(HEADER.format(aid=aid, session=session) + text.rstrip("\n") + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
