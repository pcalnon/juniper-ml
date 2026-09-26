#!/usr/bin/env python3
"""
Rebuild the 00:21Z draft of round 42's follow-up-lane handoff, which one archived validation report cites by line.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

`reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round2-laneO-amputation.md` cites a draft of
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`
(document 2, shipped in juniper-ml#2097) as "PEER L<n>", by its sha256 prefix 62f9b2bf. That draft was on
tmpfs and is gone; no file on disk has that hash. Session bc31e993, which wrote document 2, still has it in
its transcript: this replays every Write and Edit that session made to document 2, in order, and writes the
content whose sha256 starts 62f9b2bf to reports/2026-09-24_defect-register-round-42/handoff-frozen/.

It refuses unless the replay is faithful: its final state must hash to 4ebd0143, the blob juniper-ml#2097
carries at 2e4917c2, and no Edit may miss its old_string. The transcript ages out after about 30 days, so
run it before then. `--check` rebuilds in memory and writes nothing.

Usage: python3 util/ad-hoc/2026-09-24_rebuild_round42_doc2_draft_0021z.py [--check]
"""

import glob
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "reports/2026-09-24_defect-register-round-42/handoff-frozen/doc2-draft-0021z.md"
DOC2 = "HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md"
SESSION = "bc31e993-97b0-4a01-ae04-cb39593eb647"
WANT = "62f9b2bf"  # the draft the report cites
FINAL = "4ebd0143"  # document 2 as juniper-ml#2097 carries it at 2e4917c2


def records(path: str) -> "list[dict]":
    out = []
    with open(path, "rb") as fh:
        for raw in fh.read().split(b"\n"):
            if raw.strip():
                try:
                    out.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
    return out


def main() -> int:
    found = glob.glob(f"/home/pcalnon/.claude/projects/*/{SESSION}.jsonl")
    if len(found) != 1:
        raise SystemExit(f"expected one transcript for session {SESSION}, found {len(found)}")
    recs = records(found[0])
    errored = set()
    for r in recs:
        if r.get("type") == "user" and isinstance(r.get("message", {}).get("content"), list):
            for x in r["message"]["content"]:
                if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
                    errored.add(x.get("tool_use_id"))
    content, wanted, steps = None, None, 0
    for r in recs:
        if r.get("type") != "assistant":
            continue
        for x in r.get("message", {}).get("content", []) or []:
            if not (isinstance(x, dict) and x.get("type") == "tool_use" and x.get("name") in ("Write", "Edit")):
                continue
            inp = x.get("input", {})
            if not str(inp.get("file_path", "")).endswith(DOC2) or x.get("id") in errored:
                continue
            steps += 1
            if x["name"] == "Write":
                content = inp["content"]
            elif content is not None:
                old, new = inp["old_string"], inp["new_string"]
                if inp.get("replace_all"):
                    content = content.replace(old, new)
                elif content.count(old) != 1:
                    raise SystemExit(f"replay diverged at step {steps} ({r.get('timestamp')}): old_string found {content.count(old)} times")
                else:
                    content = content.replace(old, new, 1)
            if content is not None and hashlib.sha256(content.encode("utf-8")).hexdigest().startswith(WANT):
                wanted = content
    if content is None or not hashlib.sha256(content.encode("utf-8")).hexdigest().startswith(FINAL):
        raise SystemExit(f"replay of {steps} steps does not end at {FINAL}; nothing written")
    if wanted is None:
        raise SystemExit(f"no replay step hashes to {WANT}; nothing written")
    print(f"{steps} steps replayed; final state {FINAL} (juniper-ml#2097 at 2e4917c2); draft {WANT}: {len(wanted.encode('utf-8'))} bytes")
    if "--check" in sys.argv[1:]:
        return 0
    OUT.write_bytes(wanted.encode("utf-8"))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
