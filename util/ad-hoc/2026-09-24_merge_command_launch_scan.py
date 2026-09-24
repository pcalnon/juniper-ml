#!/usr/bin/env python
"""List the Claude Code tool calls on this host, in a window, whose command matches a pattern of PR-arming commands.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 ledger validation, round 2: who readied and armed canopy#676)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-24_host_session_activity_window.py (tool-call COUNTS in a window);
         notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9, "The merge, out of order"

WHY. ``2026-09-24_host_session_activity_window.py`` counts tool calls made INSIDE a window. A process launched
BEFORE the window keeps acting after its session is rate-limited or idle, and round 2 of the ledger's
validation found one that did (a background shepherd updated ml#2058's branch at 21:43:55Z). So the question
"could a Claude Code process have readied or armed a PR at time T" needs the LAUNCHES before T, of anything
that can do it, whatever PR number the command line names. The earlier scan grepped for commands naming
the PR, which misses a driver invoked as ``--pr 676`` or over a PR list.

WHAT IT PRINTS. For each tool_use that carries a shell command (Bash, Monitor, ...) matching MERGE_CAPABLE,
with its timestamp in [--start, --end]: timestamp, session id (8 chars), BG or fg (a non-Bash tool counts as
BG), the tool's name, and the command whitespace-joined and cut to 220 characters, with token shapes and
e-mail addresses redacted. Nothing else from the transcript is printed.

IT IS A PATTERN, NOT A PROOF. A push to a PR branch, a script run by a path the pattern does not name, and a
command form it does not match are all outside it. Rounds 3 and 4 of the ledger's validation found forms it
first missed. Most were added (the comments above MERGE_CAPABLE list them), and each re-scan was checked
against the counts the ledger states. Still NOT matched (round 5, Lane R5-A): a REST merge path built by an
f-string or printf (`pulls/{n}/merge`, `pulls/%s/merge`), an argv list in inline Python
(`["gh", "pr", "merge", ...]`), and any tool whose input has no `command` field, which scan() does not read.

Usage:
    python3 util/ad-hoc/2026-09-24_merge_command_launch_scan.py --start 2026-09-23T18:00:00Z --end 2026-09-23T22:52:00Z
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Widened 2026-09-24 after round 3 (Lane R3-A) found forms the first pattern missed: the converge driver's
# update-branch loop, `gh pr -R <repo> <verb>`, a `$PR` merge path, GraphQL `updatePullRequestBranch` and
# check-suite re-requests, and GraphQL read from a file (whose mutation the command line cannot show).
# It is still a PATTERN, not a proof: a script invoked by a path it does not name, or a push to a PR branch,
# is outside it.
# Round 4 (Lanes R4-A and R4-B) added: `gh run -R <repo> rerun`, `--repo=` and `-R<repo>` forms, a quoted `$PR`
# merge path, GraphQL read with --field/-F query=@ or --input, and bot_pr_converge (its update-branch loop).
_REPO_FLAG = r"(?:(?:-R|--repo)(?:\s+|=)\S+\s+|-R\S+\s+)?"
MERGE_CAPABLE = re.compile(
    r"safe_merge|fleet_merge_train|merge_shepherd|shepherd_automerge|bot_pr_merge_sweep|bot_pr_converge|release_train|converge_pr"
    rf"|gh\s+pr\s+{_REPO_FLAG}(?:ready|merge)|update-branch|pulls/\"?(?:\d+|\$\{{?\w+\}}?)\"?/merge\b|/merges\b"
    rf"|gh\s+run\s+{_REPO_FLAG}rerun|/rerun|rerequest"
    r"|enablePullRequestAutoMerge|disablePullRequestAutoMerge|markPullRequestReadyForReview|convertPullRequestToDraft"
    r"|mergePullRequest|updatePullRequestBranch|graphql\s.*(?:-F\s*query=@|--field\s+query=@|--input\b)"
)
# Every GitHub token prefix (ghp_ gho_ ghu_ ghs_ ghr_), fine-grained PATs, AWS keys, sk- keys, age keys and JWTs;
# widened 2026-09-24 after round 3 (Lane R3-B) found gho_/ghs_ and JWTs passing. E-mail addresses are redacted too.
# Widened in round 6 (Lane R6-B found the gap in the answer extractor, which shared it): sk-ant-/sk-proj- keys
# (a hyphen after "sk-"), hf_, xox?-, pypi- and PEM private-key headers.
SECRET_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}|AGE-SECRET-KEY-\S+|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
# A local part needs at least one alphanumeric anywhere (so "_lead@example.org" is caught, and a diff's
# "+@pytest.mark.unit" is not). Round 4 (Lane R4-B) found the first form, alphanumeric-first, missed the former.
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[._%+-]*[A-Za-z0-9][A-Za-z0-9._%+-]*(?:@|%40)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")


def scan(root: Path, start: str, end: str):
    for path in root.rglob("*.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for raw in lines:
            if '"tool_use"' not in raw or '"command"' not in raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp") or ""
            if not (start <= ts <= end):
                continue
            msg = rec.get("message") or {}
            for block in msg.get("content") or []:
                # Any tool whose input carries a shell command (Bash, Monitor, ...), not only Bash.
                if not isinstance(block, dict) or block.get("type") != "tool_use" or not isinstance((block.get("input") or {}).get("command"), str):
                    continue
                cmd = str((block.get("input") or {}).get("command") or "")
                if not MERGE_CAPABLE.search(cmd.replace("\\\n", " ")):  # join backslash-newline continuations
                    continue
                bg = bool((block.get("input") or {}).get("run_in_background")) or block.get("name") != "Bash"
                first = EMAIL_RE.sub("<email>", SECRET_RE.sub("<redacted>", " ".join(cmd.split())))[:220]
                yield ts, str(rec.get("sessionId") or path.stem)[:8], bg, f"[{block.get('name')}] {first}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path.home() / ".claude/projects"))
    ap.add_argument("--start", required=True, help="ISO UTC, e.g. 2026-09-23T18:00:00Z")
    ap.add_argument("--end", required=True)
    args = ap.parse_args()
    rows = sorted(scan(Path(args.root), args.start, args.end))
    for ts, sid, bg, cmd in rows:
        print(f"{ts}  {sid}  {'BG' if bg else 'fg'}  {cmd}")
    print(f"{len(rows)} tool calls matching the merge-capable pattern in [{args.start}, {args.end}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
