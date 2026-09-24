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

# Widened 2026-09-24 (Phase 9 ledger, round 7, Lane R7-B): the first version passed sk-ant-/sk-proj- keys, gho_/
# ghs_/ghu_/ghr_, hf_, xox?-, pypi- and JWT shapes in the reports it archives verbatim.
SECRET_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}|(?<![A-Za-z0-9])hf_[A-Za-z0-9]{20,}|(?<![A-Za-z0-9])pypi-[A-Za-z0-9_-]{50,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}|AGE-SECRET-KEY-|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
# Two SECRET_RE shapes match only a PREFIX, so an allowed literal equal to one would also pass a real key. Key
# material is therefore refused whatever --allow-shape says. Round 7's form ("a header, whitespace, base64")
# missed a JSON-escaped body, a blockquote, numbered lines, a backticked header, an encrypted PEM's Proc-Type
# lines and a post-quantum age identity (round 8, Lanes R8-A and R8-B), so round 8's 40-character window does not
# depend on separators. Round 7's form, kept below for 20-39-character bodies, still needs whitespace after the
# header (Lane R10-B).
PEM_HEADER_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PEM_END_RE = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")
# Round 7's form, kept in round 9 (Lane R9-B): round 8 had replaced it, so a header, whitespace and a 20-39
# character body passed.
PEM_BODY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----\s*[A-Za-z0-9+/=]{20,}")
BASE64_RUN_RE = re.compile(r"[A-Za-z0-9+/]{40,}")
AGE_KEY_RE = re.compile(r"AGE-SECRET-KEY-[0-9A-Z-]*1[0-9A-Z]{10,}")
KEY_WINDOW = 400


def key_material(text: str) -> list:
    """Return key material in ``text``: any PEM END line; a PEM header followed by whitespace and 20 or more
    base64 characters; any base64 run of 40 or more characters within KEY_WINDOW characters after a PEM header;
    and any age identity with a body (classic or post-quantum)."""
    found = [m.group(0) for m in PEM_END_RE.finditer(text)] + [m.group(0) for m in AGE_KEY_RE.finditer(text)]
    found += [m.group(0) for m in PEM_BODY_RE.finditer(text)]
    for m in PEM_HEADER_RE.finditer(text):
        found += BASE64_RUN_RE.findall(text[m.end() : m.end() + KEY_WINDOW])
    return found


def unreviewed_shapes(text: str, aid: str, allows: list) -> list:
    """Return the secret-shaped strings in ``text`` that no reviewed allow covers.

    An allow is ``AGENT_ID=LITERAL``: that exact matched text, allowed in that agent's report only. Key material
    (see ``key_material``) is always returned.
    """
    allowed = {lit for agent, _, lit in (a.partition("=") for a in allows) if agent == aid}
    return key_material(text) + [m.group(0) for m in SECRET_RE.finditer(text) if m.group(0) not in allowed]


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
    # Added 2026-09-24 (Phase 9 ledger, round 6): a report may QUOTE a shape without holding a secret, as Lane
    # R6-B's did when it named the PEM header its fake-value test used. Scoped in round 7 (Lane R7-B): an allow
    # names the agent whose report it covers, and key material (key_material(), widened in rounds 8 and 9) refuses regardless
    # (see unreviewed_shapes). Any other match still refuses.
    ap.add_argument("--allow-shape", action="append", default=[], help="AGENT_ID=LITERAL: exact matched text to ignore in that agent's report, after review (repeatable)")
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
        unreviewed = unreviewed_shapes(text, aid, args.allow_shape)
        if unreviewed:
            print(f"REFUSED: {len(unreviewed)} secret-shaped string(s) in {aid}'s report; archive by hand after review", file=sys.stderr)
            return 1
        hits = len(SECRET_RE.findall(text))
        if hits:
            print(f"{aid}: {hits} match(es), each an --allow-shape literal for this agent")
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
