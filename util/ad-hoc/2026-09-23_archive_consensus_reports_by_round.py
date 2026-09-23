#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Archive validator reports VERBATIM, per ROUND, from resumed subagent transcripts.

``2026-09-22_archive_consensus_reports_canopy.py`` takes each agent's LAST assistant text. That is
wrong once an agent is resumed for a second round with ``SendMessage``: the resumed agent appends to
the same ``agent-<id>.jsonl``, so its round-1 report stops being the last text and the round-1
evidence silently becomes the round-2 progress line. This splits each transcript at the first USER
record containing one of the ``--marker`` strings (the round-2 brief) and takes:

  round 1: the last assistant text block BEFORE that record;
  round 2: the last assistant text block AFTER it (a progress line while the agent still runs --
           the status column says so).

An agent with no marker in its transcript was not resumed; its last text is its round-1 report, and it
has no round-2 section. A report is scanned for obvious secret shapes, and the script refuses to write
if one is found.

Usage:
    python3 util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py --round 1 \\
        --session-dir ~/.claude/projects/<slug>/<session> --title "..." --intro "..." \\
        --marker "Round 2 of the canopy#670 review" --marker "Lane A2 resumes" \\
        --out reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_round1.md \\
        a734684513e7f8d2f="Lane B - adversarial review" ...
"""

import argparse
import json
import re
import sys
from pathlib import Path

SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,}|AGE-SECRET-KEY-)")


def _texts(content) -> list:
    blocks = content if isinstance(content, list) else [{"type": "text", "text": content}] if isinstance(content, str) else []
    return [b.get("text") or "" for b in blocks if isinstance(b, dict) and b.get("type") == "text"]


def split_reports(jsonl: Path, markers: list) -> dict:
    """Return {"split": bool, "r1": (text, status), "r2": (text, status) | None}."""
    records = []
    for raw in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") if isinstance(rec, dict) else None
        if isinstance(msg, dict):
            records.append((msg.get("role"), _texts(msg.get("content"))))
    cut = next((i for i, (role, texts) in enumerate(records) if role == "user" and any(m in t for t in texts for m in markers)), None)

    def last_assistant(rs):
        found = ("", "no-assistant-text")
        for role, texts in rs:
            if role == "assistant":
                for t in texts:
                    if t.strip():
                        found = (t, "last-assistant-text")
        return found

    if cut is None:
        return {"split": False, "r1": last_assistant(records), "r2": None}
    return {"split": True, "r1": last_assistant(records[:cut]), "r2": last_assistant(records[cut + 1 :])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session-dir", required=True)
    # Round N >= 2: pass the round-N brief's text as --marker; the report is the last text after it.
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--marker", action="append", required=True, help="text unique to the round-2 brief (repeatable)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--intro", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("agents", nargs="+", help='AGENT_ID="role label"')
    args = ap.parse_args()

    sub = Path(args.session_dir).expanduser() / "subagents"
    parts = ["<!-- markdownlint-disable -->", "", f"# {args.title}", "", args.intro, ""]
    for spec in args.agents:
        aid, _, label = spec.partition("=")
        path = sub / f"agent-{aid}.jsonl"
        if not path.exists():
            print(f"REFUSED: no transcript for {aid} at {path}", file=sys.stderr)
            return 1
        got = split_reports(path, args.marker)
        pick = got["r1"] if args.round == 1 else got["r2"]
        if pick is None:
            print(f"{aid}: not resumed -- no round-{args.round} report; skipped ({label})")
            continue
        text, status = pick
        if SECRET_RE.search(text):
            print(f"REFUSED: a secret-shaped string in {aid}'s report; archive by hand after review", file=sys.stderr)
            return 1
        where = "before its round-2 brief" if got["split"] and args.round == 1 else f"after its round-{args.round} brief" if args.round >= 2 else "not resumed"
        parts += [f"## {label or aid}", "", f"*agent `{aid}` · round {args.round} · {status} ({where}) · {len(text)} chars*", "", text.strip(), "", "---", ""]
        print(f"{aid}: round {args.round} {status} ({where}), {len(text)} chars -- {label}")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
