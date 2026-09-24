#!/usr/bin/env python
"""Print chosen records of a Claude Code session transcript, redacted: the owner's answer to the sweeper question.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9 ("Who");
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round5.md (Lane R5-B's
         finding 1, which located the exchange at lines 4227 and 4260 of session bc31e993's transcript)

Round 5's Lane R5-B found that the owner answered the ledger's owner question in another session four minutes
after the round's artifact was frozen. This prints only the records asked for, by line number: timestamp,
record type, role, text blocks, tool_use names and inputs, and tool results, each cut to a bound, with e-mail
addresses (also %40-encoded) and these token shapes redacted: GitHub (ghp_, gho_, ghu_, ghs_, ghr_,
github_pat_), AWS access key ids, sk- keys (sk-ant-, sk-proj-), Hugging Face hf_, Slack xox?-, PyPI pypi-, age
secret keys, PEM private-key headers and JWTs. A shape not in that list is printed. Nothing else from the
transcript is printed.

Usage:
    python3 util/ad-hoc/2026-09-24_owner_answer_extract.py <transcript.jsonl> <line> [<line> ...]
"""

import json
import re
import sys

# Widened in round 6 (Lane R6-B): the first version missed sk-ant-/sk-proj- keys (a hyphen after "sk-"), hf_,
# xox?-, pypi- and PEM private-key headers, and a %40-encoded address.
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[._%+-]*[A-Za-z0-9][A-Za-z0-9._%+-]*(?:@|%40)[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
SECRET_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}|AGE-SECRET-KEY-\S*|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
BOUND = 2500


def red(s: str) -> str:
    return SECRET_RE.sub("<secret>", EMAIL_RE.sub("<email>", s))[:BOUND]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
    for n in map(int, sys.argv[2:]):
        rec = json.loads(lines[n - 1])
        msg = rec.get("message") or {}
        print(f"=== line {n} ts={rec.get('timestamp')} type={rec.get('type')} role={msg.get('role')}")
        content = msg.get("content")
        blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text":
                print("TEXT:", red(b.get("text", "")))
            elif b.get("type") == "tool_use":
                print("TOOL_USE", b.get("name"), red(json.dumps(b.get("input"), ensure_ascii=False)))
            elif b.get("type") == "tool_result":
                c = b.get("content")
                print("TOOL_RESULT:", red(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)))
        if rec.get("toolUseResult") is not None:
            print("toolUseResult:", red(json.dumps(rec.get("toolUseResult"), ensure_ascii=False)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
