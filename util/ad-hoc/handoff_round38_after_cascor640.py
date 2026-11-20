#!/usr/bin/env python3
"""
Bring the archived round-38 handoff up to date once juniper-cascor#640 merged.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (companion to util/ad-hoc/register_close_cascor640.py; refuses until #640 is MERGED)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#640; util/ad-hoc/register_close_cascor640.py

An archived handoff is normally left alone. This one is edited because it was archived while its
last piece of work was still in flight, and it carries three statements that the merge falsifies:
the register counts in its header and §1, an instruction telling the successor NOT to build the
CLI-flag item, and a §2 row plus a checklist line describing the PR as unbuilt. A handoff whose
"verify starting state" block prints the wrong numbers is worse than one that is merely incomplete.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = ROOT / "prompts" / "thread-handoff_automated-prompts" / (
    "HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md"
)

state = json.loads(
    subprocess.run(
        ["gh", "pr", "view", "640", "--repo", "pcalnon/juniper-cascor", "--json", "state,mergedAt,mergeCommit"],
        check=True, capture_output=True, text=True,
    ).stdout
)
if state["state"] != "MERGED":
    sys.exit(f"REFUSED: cascor#640 is {state['state']}, not MERGED")
sha = state["mergeCommit"]["oid"][:7]
merged = state["mergedAt"]

text = DOC.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n} for:\n---\n{old[:200]}\n---")
    text = text.replace(old, new)
    print(f"  ok  {label}")


sub("**112 rows, 82\nfixed, 30 open**", "**112 rows, 85\nfixed, 27 open**", "header counts")
sub("Open splits 17\nprimer (16 parked, `APD-DATA-019` unparked) + 13 post-primer.",
    "Open splits 17\nprimer (16 parked, `APD-DATA-019` unparked) + 10 post-primer.", "header split")
sub("Expected: FIXED rows **82**; **`112 rows | 82 fixed | 30 open`**; cross-check **82 / 82 / 82,\nAGREE**; the archive test **passes**.",
    "Expected: FIXED rows **85**; **`112 rows | 85 fixed | 27 open`**; cross-check **85 / 85 / 85,\nAGREE**; the archive test **passes**.", "§1 expected values")

sub(
    "2. **cascor partial-data follow-ups — a PR was in flight when this was written; confirm its state\n"
    "   before rebuilding anything.**",
    f"2. **cascor partial-data follow-ups — DONE: juniper-cascor#640, merged {merged} as `{sha}`.**\n"
    "   Register rows `APD-CASCOR-009` / `-010` / `-012` are closed against it. Left below for the\n"
    "   record of what it covered:",
    "§0.2 heading",
)
sub(
    "   **Do not include the CLI-flag item**: register row `APD-CASCOR-011` is **parked** as a design\n"
    "   question, and an earlier draft of this section told the successor to build it anyway.\n",
    "   `APD-CASCOR-011` (the CLI flag) is **still open and still parked**: #640 took a third path —\n"
    "   the flag is kept, and its `--help`, a WARNING on use and the operator docs now say what it does\n"
    "   and does not affect — so the inertness is no longer silent, but the parked question is *drop it\n"
    "   or rewire the path* and that is still owed a ruling.\n"
    "   **One correction was needed on review before that PR merged**, and it is the reusable part: the\n"
    "   PR explained the flag's inertness by saying `main.py` trains an in-process spiral problem,\n"
    "   synthesised locally, that never contacts juniper-data. `main.py` health-checks `/v1/health` and\n"
    "   refuses to start when the service is unreachable. The true reason is that the generator is\n"
    "   hardcoded `spiral`, which juniper-data always delivers in full and which is not truncatable. A\n"
    "   test had pinned the wrong wording by asserting the phrase \"two-spiral\" appeared in the warning;\n"
    "   it now asserts the reason instead. **A test that pins prose pins whatever the prose got wrong.**\n",
    "§0.2 CLI-flag instruction",
)

sub(
    "| **juniper-cascor (follow-ups)** | in flight at write time | §0.2. Confirm before rebuilding. |",
    f"| **juniper-cascor#640** | MERGED {merged}, `{sha}` | The four follow-ups (§0.2): auto-start forwards the stance, annotates and records its failure; `get_metrics()` carries the shortfall; the CLI flag says what it does; the operator docs name the knob. Closes `APD-CASCOR-009` / `-010` / `-012`. |",
    "§2 table row",
)
sub(
    "- [ ] cascor follow-ups PR — in flight at write time (§0.2)",
    f"- [x] cascor follow-ups PR — juniper-cascor#640, MERGED `{sha}`; three register rows closed (§0.2)",
    "§8 checklist",
)

DOC.write_text(text)
print("\nhandoff updated")
long = [(n, len(ln)) for n, ln in enumerate(text.splitlines(), 1) if len(ln) > 512]
print("over-length lines:", long or "none")
