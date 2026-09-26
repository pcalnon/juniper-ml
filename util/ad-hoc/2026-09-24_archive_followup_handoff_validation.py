#!/usr/bin/env python3
"""
Archive the consensus-validation reports of the round-42 follow-up lane's handoff, verbatim.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use archiver; reads local session transcripts, writes reports/
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Session bc31e993 validated its handoff
(prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md)
in background agents, whose final reports live only in the session's local transcript. This writes
each report into reports/2026-09-24_defect-register-round-42/ in the format the round's own
archiver uses, and it reuses that archiver's extraction and secret scan by importing it by path
(util/ad-hoc/2026-09-24_archive_round42_reports.py). The header reads "(final message)", so that
archiver's --check byte-verifies these files too.

Usage: python3 2026-09-24_archive_followup_handoff_validation.py [--check]
  --check  extract and scan only; write nothing
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUND42 = HERE / "2026-09-24_archive_round42_reports.py"

# Agent id -> report file name. All are bc31e993's agents.
REPORTS = {
    "a41961813422e6131": "handoff-followup-lane-round1-laneA-reprobe.md",
    "aebc684c555a675b4": "handoff-followup-lane-round1-laneB-amputation.md",
    "a3af4fedee198bd52": "handoff-followup-lane-round1-laneC-actionability.md",
    "a105b96f1f3471bb3": "handoff-followup-lane-round2-laneA-reprobe.md",
    "afe00e807f4117068": "handoff-followup-lane-round2-laneB-refute.md",
    "a395d3bc7b4186fe5": "handoff-followup-lane-round3-laneA-reprobe.md",
    "a7605941a055e6f60": "handoff-followup-lane-round3-laneB-refute.md",
    "af0a79cb3c9b8332d": "handoff-followup-lane-round4-laneA-reprobe.md",
    "acf72f155fbceaf05": "handoff-followup-lane-round4-laneB-refute.md",
    "aa10d6cb5ba1666b4": "handoff-followup-lane-round5-confirmation.md",
}
SESSION = "bc31e993"


def main(argv: "list[str]") -> int:
    check = "--check" in argv[1:]
    spec = importlib.util.spec_from_file_location("archive_round42_reports", ROUND42)
    if spec is None or spec.loader is None:
        print(f"cannot load the round's archiver from {ROUND42}")
        return 2
    round42 = importlib.util.module_from_spec(spec)
    sys.modules["archive_round42_reports"] = round42
    spec.loader.exec_module(round42)
    failed = False
    for aid, name in REPORTS.items():
        target = round42.OUT / name
        text = round42.last_report(round42.transcript(SESSION, aid))
        hits = [p.pattern for p in round42.SECRET_PATTERNS if p.search(text)]
        if hits:
            print(f"  REFUSE {name}: credential-shaped text ({', '.join(hits)})")
            failed = True
            continue
        if target.exists():
            print(f"  exists {name}: left alone")
            continue
        print(f"  {'would add' if check else 'add   '} {name}: {len(text)} chars from agent {aid}")
        if not check:
            target.write_text(round42.HEADER.format(aid=aid, session=SESSION) + text.rstrip("\n") + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
