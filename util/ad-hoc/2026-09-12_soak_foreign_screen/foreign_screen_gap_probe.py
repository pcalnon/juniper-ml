#!/usr/bin/env python3
"""Does the contamination screen credit a SIBLING repo's docs/REFERENCE.md as retrieval?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-12
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 10a

Why
---
`util/soak_run_probe.py` guards the `foreign` mechanism (a sibling repo ships its own
docs/REFERENCE.md -- 7 of 8 do) per occurrence, ratified in ml#1855 + its re-fix.
`util/ad-hoc/2026-08-21_soak_probe_evidence.py::scan` does NOT: `dest_hits` and `via_output` are
bare `DEST in blob` substring tests, and `retrieved = (dest_hits + via_output) > 0`.

MEASURE BEFORE CLAIMING, AND COUNT CORPUS OCCURRENCES BEFORE PROPOSING A FIX. The previous
attempt in this arc (the ledger guard, withdrawn 2026-09-12) fixed a shape with ZERO occurrences
in 49 transcripts. This probe reports both:

  (a) synthetic -- does the screen mis-score a pure sibling-repo transcript?
  (b) corpus    -- how many real transcripts contain a sibling-repo occurrence?

Read-only. Writes nothing; builds synthetic transcripts under a caller-supplied scratch dir.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCREEN = ROOT / "util" / "ad-hoc" / "2026-08-21_soak_probe_evidence.py"
DEST = "docs/REFERENCE.md"
SIBLINGS = ("juniper-deploy", "juniper-canopy", "juniper-cascor", "juniper-data")


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def tool_use(cmd: str) -> str:
    return json.dumps(
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}}
    )


def tool_result(text: str) -> str:
    return json.dumps(
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "content": text}]}}
    )


def main() -> int:
    scratch = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    scratch.mkdir(parents=True, exist_ok=True)
    screen = load(SCREEN, "evscreen")

    print("=== (a) SYNTHETIC: does the screen credit a sibling's copy? ===\n")
    cases = [
        ("ONLY a sibling read, tool_use",
         [tool_use("cd /home/u/Juniper/juniper-deploy && grep -rn 3001 docs/REFERENCE.md")],
         False),
        ("ONLY a sibling read, tool_result content",
         [tool_result("/home/u/Juniper/juniper-deploy/docs/REFERENCE.md:88:Grafana 3001")],
         False),
        ("OUR copy, tool_use (control -- must stay retrieved)",
         [tool_use("sed -n '1,20p' docs/REFERENCE.md")],
         True),
        ("OUR copy via ecosystem parent (control)",
         [tool_use("cd /home/u/Juniper && sed -n '1,5p' juniper-ml/docs/REFERENCE.md")],
         True),
        ("sibling AND ours in one run (control -- must stay retrieved)",
         [tool_use("grep -rn x /home/u/Juniper/juniper-canopy/docs/REFERENCE.md"),
          tool_use("sed -n '1,5p' docs/REFERENCE.md")],
         True),
    ]
    wrong = 0
    for label, lines, should in cases:
        p = scratch / (label.replace(" ", "_").replace("/", "_")[:60] + ".jsonl")
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        r = screen.scan(p)
        got = r["retrieved"]
        ok = got == should
        if not ok:
            wrong += 1
        print(f"  retrieved={str(got):<5} should={str(should):<5} "
              f"{'ok' if ok else 'MIS-SCORED'}   {label}")
    print(f"\n  {wrong} synthetic case(s) mis-scored.\n")

    print("=== (b) CORPUS: how many real transcripts carry a sibling occurrence? ===\n")
    binder = load(ROOT / "util" / "ad-hoc" / "2026-09-08_soak_label_to_transcript.py", "binder")
    try:
        transcripts = binder.discover_transcripts()
    except Exception as exc:                                  # noqa: BLE001
        print(f"  could not enumerate transcripts: {exc!r}")
        return 0

    seen = set()
    for runs in transcripts.values():
        for run in runs:
            p = run.get("path") if isinstance(run, dict) else None
            if p:
                seen.add(pathlib.Path(p))
    print(f"  transcripts discovered: {len(seen)}")

    sib_only = 0
    sib_any = 0
    for p in sorted(seen):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if DEST not in text:
            continue
        has_sib = any(f"{s}/docs/REFERENCE.md" in text for s in SIBLINGS)
        if has_sib:
            sib_any += 1
            # DEFECT IN THE FIRST VERSION OF THIS PROBE, 2026-09-12, fixed here.
            # It read:
            #     own = (... or any(<expr> for _ in (0,)))
            # which is just <expr> evaluated once -- a generator over a 1-tuple, not a
            # scan of anything. Since the loop has already established `DEST in text`,
            # a quoted or space-prefixed occurrence is near-certain, so `own` was
            # near-always True and the `sib_only` column was structurally pinned to 0.
            # It could not have reported any other number: a vacuous-pass check, in the
            # probe written to find vacuous checks. The column is now stated as
            # UNRESOLVED rather than given a number this instrument cannot produce --
            # deciding whether a transcript ALSO read our copy is exactly the
            # per-occurrence classification `2026-09-08_soak_label_to_transcript.py`
            # exists to do, and it should be used instead of a substring heuristic.
            _ = sib_only        # intentionally not incremented; see above
    print(f"  transcripts naming a SIBLING's docs/REFERENCE.md : {sib_any}")
    print("  ...of those, with no own-repo occurrence at all  : UNRESOLVED "
          "(see comment; needs per-occurrence classification, not a substring test)")
    print("\n  (Sec 4 of the recovery note records exactly one such row: soak-A-P24,")
    print("   2026-08-22T21:41:09 -- a sibling hit and nothing else.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
