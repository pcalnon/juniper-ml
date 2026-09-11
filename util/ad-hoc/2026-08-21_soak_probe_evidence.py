#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc
Author:      Paul Calnon
License:     MIT License

Extract RETRIEVAL EVIDENCE from a subagent transcript for the pointer-follow soak
(``notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md`` §7).

Why this exists
---------------
The protocol scores a probe run on whether the session *demonstrably retrieved*
the fact before acting -- "a correct answer reached without consulting the fact
is still a miss". The evidence for that is the session's tool log, not its final
prose: an agent can state a fact confidently from parametric memory, and that is
a MISS, not a follow.

Reading a transcript into a scoring agent's context would both overflow it and
contaminate the scorer. This prints COUNTS AND PATHS ONLY -- never message text
-- so the scorer sees which files were opened and nothing else.

Usage:
    python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py <agent-id> [<agent-id> ...]
    python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py --path <transcript.jsonl>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# The pilot's transcripts live under the PRIMARY project directory, not the
# worktree-suffixed one this list named until 2026-09-08. Only that component
# was wrong -- the session UUID under it was always correct -- but the screen
# resolved no transcript at all, so every invocation reported nothing and the
# 8 output-scored rows went un-re-audited for 17 days. The stale entry is kept,
# last, for a host that still has the old worktree.
SUBAGENT_DIRS = [
    Path.home() / ".claude/projects"
    / "-home-pcalnon-Development-python-Juniper-juniper-ml"
    / "bf50124e-6fde-4314-bdca-0ca7876b8efb" / "subagents",
    Path.home() / ".claude/projects"
    / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-giggly-marinating-backus"
    / "bf50124e-6fde-4314-bdca-0ca7876b8efb" / "subagents",
]

# The relocation destination. Opening this is the retrieval event under test.
DEST = "docs/REFERENCE.md"

# THE ANSWER KEY. conf/soak_probes.json carries each probe's `fact` and
# `discriminator` verbatim, and it lives inside the repo the subject is
# searching -- so a keyword grep for the probe's own subject matter (e.g.
# "per_run_timeout_seconds") surfaces the answer sheet. Any run that touched it
# is CONTAMINATED and must not be scored as a clean observation. Discovered on
# run 2 of the pilot, by this scorer.
ANSWER_KEY = "conf/soak_probes.json"
# The protocol document also names every fact and the whole measurement design.
PROTOCOL_DOC = "POINTER-FOLLOW-SOAK-LEDGER"

# THE LEDGER IS AN ANSWER SHEET TOO, and neither marker above covers it.
# `reports/soak/pointer_follow_soak.jsonl` records, per observation, the probe's
# `pointer`, its scored `outcome`, and a `note` restating the answer in prose --
# so an unscoped `grep -rn <term> .` from the repo root can show a subject the
# previous run's answer AND its scoring. Observed once, on
# P18-health-interval-non-positive (2026-08-22T21:41:09Z).
#
# This violates the authoring rule the soak's own protocol states at
# `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` --
# "identifier-shaped facts must be stored in a form the subject's own grep
# cannot hit" -- in the instrument's own record. (Quoted, not line-pinned: that
# rule sat at :672 when the 09-09 handoff cited it and at :693 two days later,
# after ml#1883 inserted above it. Grep the sentence.)
LEDGER_FILE = "pointer_follow_soak"

# CONTENT vs FILENAME, and the distinction is load-bearing rather than fussy.
# Re-derived 2026-09-10 over all 43 valid rows: 8 runs TOUCHED the ledger and
# exactly ONE read its contents. The other seven saw the filename in a porcelain
# status line, a diff stat, an `ls -t reports/soak/`, or a `grep -l` list. Flagging
# all eight would overstate the exposure 8x on the number that feeds owner decision
# 8 -- whether the leak invalidates its runs -- which changes the DENOMINATOR of
# every rate in the arc.
#
# These keys exist in a ledger RECORD and in no directory listing, so they cannot
# be produced by seeing the filename. The filename stem is deliberately NOT among
# them: `util/ad-hoc/2026-09-08_soak_label_to_transcript.py`'s LEDGER_MARKERS does
# include it, which is why its `ledger=N` column cannot be read as a content count.
LEDGER_CONTENT_KEYS = ('"obs_id"', '"scored_by"', '"discriminator_ok"', '"miss_class"')

# THESE MARKERS FIRE ON ANY FILE THAT QUOTES A RECORD, NOT ONLY ON THE LEDGER, AND
# THAT IS INTENDED. Measured 2026-09-10: `"obs_id"` also appears in
# `notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`,
# which quotes a full record -- `note` (the prose answer), `obs_id`, `outcome` and
# `pointer` -- in a fenced block. A subject that greps `notes/` and gets that chunk
# back has seen the answer sheet exactly as if it had read the ledger, so scoring it
# as a content read is right. The leak propagated into a second file; screening only
# the ledger's own path would have missed it, which is the same shape as the gap this
# whole check closes.

PATH_RE = re.compile(r"[\w./-]+\.(?:md|py|bash|sh|yml|yaml|json|toml|cfg|ini)")


def find_transcript(agent_id: str) -> Path | None:
    for d in SUBAGENT_DIRS:
        p = d / f"agent-{agent_id}.jsonl"
        if p.exists():
            return p
        if d.exists():
            for cand in d.glob(f"*{agent_id}*.jsonl"):
                return cand
    return None


def ledger_exposure(blob: str) -> str:
    """Classify one payload's exposure to the soak ledger: content, filename, or none.

    A payload that carries a record key has had the ledger's CONTENT returned to it
    -- the previous run's pointer, outcome and prose answer. A payload that carries
    only the path has seen the file exist. Those are different events and only the
    first contaminates.

    The transcript's content is itself JSON, so ``json.dumps`` escapes the record's
    inner quotes and ``"obs_id"`` arrives as ``\"obs_id\"``. Dropping backslashes
    before the test costs nothing and catches both forms -- the same correction
    ``2026-09-08_soak_label_to_transcript.py`` had to make.
    """
    flat = blob.replace("\\", "")
    if any(k in flat for k in LEDGER_CONTENT_KEYS):
        return "content"
    if LEDGER_FILE in flat:
        return "filename"
    return "none"


def scan(path: Path) -> dict:
    """Walk the transcript, collecting only tool names and file paths."""
    tools: Counter = Counter()
    files: Counter = Counter()
    dest_hits = 0
    records = 0
    contaminated = [0]
    via_output = [0]
    ledger_content = [0]
    ledger_filename = [0]

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        records += 1
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Walk the record for tool_use blocks without materialising message text.
        stack = [rec]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if node.get("type") == "tool_use":
                    name = node.get("name") or "?"
                    tools[name] += 1
                    blob = json.dumps(node.get("input") or {})
                    for m in PATH_RE.findall(blob):
                        m = m.lstrip("./")
                        if m.startswith("docs/") or m.startswith("util/") \
                           or m.startswith("tests/") or m.startswith("conf/") \
                           or m.startswith(".github/") or m.endswith("AGENTS.md") \
                           or m.endswith("CLAUDE.md"):
                            files[m] += 1
                    if DEST in blob:
                        dest_hits += 1
                    if ANSWER_KEY in blob or PROTOCOL_DOC in blob:
                        contaminated[0] += 1
                    exposure = ledger_exposure(blob)
                    if exposure == "content":
                        ledger_content[0] += 1
                    elif exposure == "filename":
                        ledger_filename[0] += 1
                elif node.get("type") == "tool_result":
                    # Scanning only tool INPUTS was a false negative: a
                    # directory-wide `grep -rn <term> docs/` retrieves
                    # REFERENCE.md content without the literal path ever
                    # appearing in the command. Found 2026-08-21 when two runs
                    # cited REFERENCE.md line numbers while the scorer reported
                    # zero refs. tool_result is still tool-layer evidence, NOT
                    # model prose -- an agent merely *mentioning* the file in its
                    # answer must never count as having retrieved it.
                    blob = json.dumps(node.get("content") or "")
                    if DEST in blob:
                        via_output[0] += 1
                    # PROTOCOL_DOC is deliberately NOT tested here, and the
                    # asymmetry with the tool_use branch above is REAL but is not
                    # item F''s to close. Widening it was attempted 2026-09-10 and
                    # reverted: `PROTOCOL_DOC` is a notes FILENAME stem, so every
                    # occurrence is filename-shaped, and flagging it in a result
                    # would score a `grep -l` listing as having read the protocol
                    # document -- the exact false positive the ledger split below
                    # exists to avoid. Doing it properly needs a content rule for
                    # this marker (a `path:NNN:` form proves content came back; a
                    # `Read` result does not carry one), which is unvalidated.
                    # `tests/test_soak_probe_evidence.py`
                    # `test_protocol_doc_in_tool_result_is_currently_invisible`
                    # pins the current behaviour and is what caught the attempt.
                    if ANSWER_KEY in blob:
                        contaminated[0] += 1
                    exposure = ledger_exposure(blob)
                    if exposure == "content":
                        ledger_content[0] += 1
                    elif exposure == "filename":
                        ledger_filename[0] += 1
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    return {
        "records": records,
        "tool_calls": sum(tools.values()),
        "tools": dict(tools),
        "dest_hits": dest_hits,
        "dest_via_output": via_output[0],
        "retrieved": (dest_hits + via_output[0]) > 0,
        "contaminated": contaminated[0] > 0,
        "contamination_hits": contaminated[0],
        # Reported SEPARATELY from `contaminated`, not folded into it. Whether a
        # ledger read invalidates its run is owner decision 8 of the 09-09 handoff
        # and is NOT settled; a screen that silently rolled it into the existing
        # flag would decide it by implementation. The measurement is here either
        # way, which is what the decision needs.
        "ledger_content_hits": ledger_content[0],
        "ledger_filename_hits": ledger_filename[0],
        "ledger_content_read": ledger_content[0] > 0,
        "ledger_touched": (ledger_content[0] + ledger_filename[0]) > 0,
        "files": files.most_common(12),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("agent_ids", nargs="*")
    ap.add_argument("--path", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    targets: list[tuple[str, Path]] = []
    if args.path:
        targets.append((args.path.stem, args.path))
    for aid in args.agent_ids:
        p = find_transcript(aid)
        if p is None:
            print(f"{aid}: TRANSCRIPT NOT FOUND", file=sys.stderr)
            continue
        targets.append((aid, p))

    out = {}
    for label, p in targets:
        r = scan(p)
        out[label] = r
        if args.json:
            continue
        verdict = "RETRIEVED docs/REFERENCE.md" if r["retrieved"] else "did NOT open docs/REFERENCE.md"
        flag = "  *** CONTAMINATED: touched the answer key ***" if r["contaminated"] else ""
        if r["ledger_content_read"]:
            flag += "  *** READ THE LEDGER'S CONTENTS (prior answer + scoring) ***"
        elif r["ledger_touched"]:
            flag += "  [saw the ledger FILENAME only -- not a content read]"
        print(f"=== {label[:12]} ==={flag}")
        print(f"  records {r['records']}  tool_calls {r['tool_calls']}  -> {verdict} "
              f"(opened={r['dest_hits']} via-search-output={r['dest_via_output']})")
        print(f"  tools {r['tools']}")
        for f, n in r["files"]:
            print(f"    {n:>3}x {f}")
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
