#!/usr/bin/env python3
"""
Build rulings_15_48.json for the flood-4 record update from the extracted dialogs, the PR states and the census.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- assembles the per-ruling ledger the record update's section 8 rests on
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8;
         util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py (--dialogs), ..._record_prs.py (--prs),
         ..._record_census.py (the snapshots under --census)

Why
---
Each ruling's date, labels and outcome in the record are to be traceable. Nothing here is typed in by hand except the
map from a ruling number to its dialog question (session prefix, the call's asked time, the question's header), a
one-sentence question summary, the outcome PR numbers and the citation locations. The times, the verbatim labels
(chosen by matching each option label against the answer, so a label containing a comma survives) and every PR's
state, merge time and merge commit are read from the inputs, and each citation line is re-read from the snapshot
and must contain its expected text.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_rulings_json.py --dialogs <dialogs.json> --prs <prs.json> \\
        --census <census dir> --out <rulings_15_48.json>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

D1 = ("d0da1827", "2026-11-09T01:32:18")
D2 = ("aee58c29", "2026-11-09T11:12:26")
D3 = ("f2b4e7c3", "2026-11-12T23:24:23")
D4 = ("f2b4e7c3", "2026-11-12T23:29:29")
D5 = ("f2b4e7c3", "2026-11-12T23:34:18")
D6 = ("db29e0f6", "2026-11-13T02:07:53")
D7 = ("bd3400f6", "2026-11-14T23:46:52")
D8 = ("9a23c563", "2026-11-15T11:34:05")
D9 = ("9a23c563", "2026-11-15T11:42:14")
D10 = ("9a23c563", "2026-11-15T12:10:13")
D11 = ("9a23c563", "2026-11-15T22:06:15")
D12 = ("9a23c563", "2026-11-16T09:29:09")
D13 = ("90e102f7", "2026-11-23T22:01:55")

ML, DATA, DC, CAS, CC, CW, CAN = "juniper-ml", "juniper-data", "juniper-data-client", "juniper-cascor", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy"

# number: (session, [(dialog, header)], question summary, [(repo, number, role)])
RULINGS: dict[int, tuple] = {
    15: (3, [(D1, "Guard bypass")], "A brace sequence with a step (cat ~/.{r..t..1}sh/config) passed the agent guard on main: does the ml-code carrier carry the fix?", [(ML, 2554, "fix (guard 1.3.0)"), (ML, 2552, "first cut, closed and re-cut")]),
    16: (3, [(D1, "Brace cap")], "Ruling 8's fail-closed brace cap would refuse 21 of 44,660 recent commands, 19 inside quoted text: what about those false refusals?", [(ML, 2554, "shipped strict"), (ML, 2625, "quoted lists no longer counted (guard 1.4.0)")]),
    17: (3, [(D1, "New defects")], "Which of four more defects that no ruling covered does the arc fix now, each in its own validated, signed PR?", [(DATA, 529, "data: 44 unrun tests"), (CAS, 756, "cascor: stop-then-start"), (CAN, 815, "canopy: tests hit :8050"), (CAN, 814, "canopy: dead error path")]),
    18: (4, [(D2, "Escape gap")], "Where does the fix for the guard's escape gap (cat ~/.ss{h,b\\}c}/config) go?", [(ML, 2625, "guard 1.4.0")]),
    19: (6, [(D3, "N-2 design")], "Which design lands for service-core's stop-then-start fix (N-2): a 409 until the old thread ends, a bounded wait, or per-run fencing?", [(ML, 2557, "N-2")]),
    20: (6, [(D3, "Guard F3/F4")], "Where are guard bypasses F3 and F4, already on main, fixed?", [(ML, 2625, "closed in guard 1.4.0")]),
    21: (6, [(D3, "Spellings")], "Do the two open bypasses' exact spellings stay in ml-code's public texts?", [(ML, 2554, "landed as written")]),
    22: (6, [(D3, "Cascor design")], "Which design lands in juniper-cascor's stop-then-start fix: per-run fence-and-queue, or a 409 like service-core's?", [(CAS, 756, "fence-and-queue")]),
    23: (6, [(D4, "SC follow-ups")], "Which defects found beside N-2, N-4 and cascor's resume fix get a follow-up service-core PR?", [(CAS, 776, "follow-up 3 (D-14), with rulings 30-31"), (ML, 2618, "follow-up 3 (D-14), with rulings 30-31")]),
    24: (6, [(D4, "macOS guard")], "Where are the agent guard's suites wired into juniper-ml's macOS host-tooling job?", [(ML, 2581, "ml-tests")]),
    25: (6, [(D4, "Data tests")], "What happens to juniper-data's remaining 137 unrun tests and 41 benchmarks?", [(DATA, 539, "the 137 tests")]),
    26: (6, [(D4, "Lockfile print")], "Is canopy#814's unreachable lockfile print fixed in five sibling repositories, and canopy's wrong [dependabot skip] docs line?", []),
    27: (6, [(D5, "Canopy :8100")], "What is done about the 124 canopy unit tests that still connect to :8100?", []),
    28: (6, [(D5, "Canopy flake")], "What is done about canopy's load-sensitive test_relay_cascade_add_does_not_block_the_loop?", []),
    29: (6, [(D5, "Scan gap issue")], "Open a juniper-data issue for the PR-commit scan's force-push gap?", [(DATA, 536, "the issue")]),
    30: (7, [(D6, "D14 approach")], "How does service-core answer malformed /ws/training resume frames, which it answers differently from juniper-cascor on 131 of 240 cases?", [(CAS, 776, "shared table"), (ML, 2618, "four rules + shared table")]),
    31: (7, [(D6, "Negative seq")], "If service-core follows cascor, how is a negative last_seq answered?", [(ML, 2618, "read as 0")]),
    32: (7, [(D6, "#756 effect")], "What happens about juniper-cascor#756's side effect (a pause just before a stop and a start freezes the new run)?", [(CAS, 764, "documented as known, not fixed"), (CAS, 769, "fixed (rulings 39-41)")]),
    33: (8, [(D7, "Benchmarks")], "Which lane do juniper-data's 41 benchmarks get?", [(DATA, 540, "daily smoke run")]),
    34: (8, [(D7, "main-verify")], "Does the ml-tests carrier mirror its new suites into main-verify.yml's Regression Battery?", [(ML, 2581, "all fifteen mirrored")]),
    35: (8, [(D7, "Data pins")], "Back-port the pilot port's blocking-wiring pins to juniper-data's own Gitleaks test?", [(DATA, 542, "the pins")]),
    36: (9, [(D8, "Guard N1-N7")], "How are seven more ways past the agent guard (N1-N7) handled, given juniper-ml is public?", [(ML, 2625, "closed in guard 1.4.0")]),
    37: (9, [(D8, "Worker lane"), (D9, "Sched. lane"), (D10, "Worker lock")], "What fixes the scheduled-tests lanes that pytest 9.2.0 broke (Unknown marker slow): first asked for the worker alone, then re-asked for three repositories, then a worker-only follow-up?", [(CW, 231, "overtaken: not this arc's"), (DC, 263, "overtaken: not this arc's"), (CC, 198, "overtaken: not this arc's")]),
    39: (9, [(D11, "Pause 409")], "In juniper-cascor's pause fix, does a pause that loses its race with a stop keep the 409?", [(CAS, 769, "fix")]),
    40: (9, [(D11, "Swap pause")], "What does the fix do with a pause after a live swap whose join timed out?", [(CAS, 769, "fix")]),
    41: (9, [(D11, "Fix scope")], "Which scope does the pause fix take?", [(CAS, 769, "fix")]),
    42: (9, [(D11, "Round 3")], "What happens to round 3's #2404 and #2406?", [(ML, 2404, "closed"), (ML, 2406, "closed")]),
    43: (9, [(D12, "Drift gate")], "Does the D-14 drift gate fail or skip when a juniper-cascor checkout has no copy of the shared table?", [(ML, 2618, "D-14")]),
    44: (9, [(D12, "Helpers")], "Where do the D-14 builder's provenance scripts land?", [(ML, 2618, "D-14")]),
    45: (9, [(D12, "Test deps")], "Do uvicorn and websockets stay in service-core's [test] extra, and capped or not?", [(ML, 2618, "D-14")]),
    46: (10, [(D13, "Guard gap")], "How does guard 1.4.0 proceed while printing substitutions still pass it?", [(ML, 2625, "guard 1.4.0")]),
    47: (10, [(D13, "Time cap")], "Keep guard 1.4.0's 3 s analysis cap?", [(ML, 2625, "guard 1.4.0")]),
    48: (10, [(D13, "R55 check")], "Add a check that the paragraph above docs/REFERENCE.md's compatibility table states the rule its tests enforce?", [(ML, 2631, "the check")]),
}

RULING_38 = {
    "number": 38,
    "session": 9,
    "source": "text",
    "transcript": "9a23c563",
    "answered_at": None,  # filled from --text38 when given
    "log": "humming-stargazing-papert/tmp/flood4/session9/STATE_S9.txt:213-217",
    "question": "How should the parked guard PR proceed after a safety classifier stopped its first builder?",
    "text_phrase": "let's verify that agent guard fix is reworded as necessary",
    "outcome": [(ML, 2625, "un-parked; guard 1.4.0")],
}

# (repo snapshot dir under --census, path, line, regex the line must match); "tags" entries are files under census/tags
CITATIONS: dict[int, list[tuple[str, str, int, str]]] = {
    15: [(ML, "CHANGELOG.md", 832, r"Carry in ml-code"), (ML, "docs/REFERENCE.md", 4231, r"Carry in ml-code"), (ML, "docs/REFERENCE.md", 4481, r"Carry in ml-code")],
    16: [(ML, "CHANGELOG.md", 468, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 4231, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 4486, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 9959, r"rulings 16 and 18"), (ML, "tests/test_claude_agent_guard_brace_cap.py", 383, r"rulings 16")],
    17: [
        (DATA, "CHANGELOG.md", 393, r"ruling 17 of 2026-11-09"),
        (CAS, "CHANGELOG.md", 490, r"ruling 17 \(2026-11-09\)"),
        (CAS, "CHANGELOG.md", 612, r"ruling 17 \(2026-11-09\)"),
        (CAS, "src/tests/unit/api/test_lifecycle_stop_then_start.py", 26, r"ruling 17 \(2026-11-09"),
        (CAS, "util/ad-hoc/2026-11-08_stop_then_start_race_repro.py", 9, r"ruling 17 \(2026-11-09"),
        (CAN, "CHANGELOG.md", 317, r"ruling 17 of 2026-11-09"),
        (CAN, "CHANGELOG.md", 382, r"ruling 17 \(2026-11-09\)"),
        ("tags", "juniper-cascor_v0.14.0_CHANGELOG.md", 122, r"ruling 17 \(2026-11-09\)"),
        ("tags", "juniper-cascor_v0.14.0_CHANGELOG.md", 244, r"ruling 17 \(2026-11-09\)"),
        ("tags", "juniper-canopy_v0.10.0_CHANGELOG.md", 156, r"ruling 17 of 2026-11-09"),
        ("tags", "juniper-canopy_v0.10.0_CHANGELOG.md", 221, r"ruling 17 \(2026-11-09\)"),
        (ML, "notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md", 137, r"ruling 17"),
        (ML, "notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md", 257, r"ruling 17"),
        (ML, "notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md", 164, r"ruling 17"),
        (ML, "notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md", 229, r"ruling 17"),
        (ML, "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md", 121, r"ruling 17"),
        (ML, "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md", 1158, r"ruling 17\" is one ruling over four fixes"),
    ],
    18: [(ML, "CHANGELOG.md", 468, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 4231, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 4486, r"rulings 16 and 18"), (ML, "docs/REFERENCE.md", 9959, r"rulings 16 and 18"), (ML, "tests/test_claude_agent_guard_brace_cap.py", 384, r"and 18 \(2026-11-09")],
    19: [(ML, "CHANGELOG.md", 962, r"ruling of 2026-11-12 accepts the refusal"), (ML, "juniper-service-core/CHANGELOG.md", 161, r"ruling of 2026-11-12 accepts it")],
    20: [(ML, "CHANGELOG.md", 469, r"ruling of 2026-11-12"), (ML, "docs/REFERENCE.md", 4486, r"ruling of 2026-11-12"), (ML, "docs/REFERENCE.md", 9959, r"ruling of 2026-11-12")],
    22: [(CAS, "CHANGELOG.md", 490, r"ruled on 2026-11-12 to keep"), (CAS, "CHANGELOG.md", 612, r"ruled on 2026-11-12 to keep"), (CAS, "src/tests/unit/api/test_lifecycle_stop_then_start.py", 28, r"ruled on 2026-11-12 to keep"), ("tags", "juniper-cascor_v0.14.0_CHANGELOG.md", 244, r"ruled on 2026-11-12 to keep"), (ML, "notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md", 257, r"ruled on 2026-11-12 to keep")],
    23: [
        (ML, "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md", 1150, r"2026-11-12 23:34:04Z"),
        (ML, "notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md", 113, r"2026-11-12 23:34:04Z"),
        (ML, "CHANGELOG.md", 257, r"rulings of 2026-11-12 and"),
        (ML, "juniper-service-core/CHANGELOG.md", 73, r"Match cascor's resume answers"),
        (ML, "juniper-service-core/tests/test_websocket_resume_continuity.py", 893, r"rulings of 2026-11-12"),
        (ML, "docs/REFERENCE.md", 9958, r"rulings of 2026-11-12 and 2026-11-13"),
    ],
    24: [(ML, "CHANGELOG.md", 174, r"ruling of 2026-11-12"), (ML, "docs/REFERENCE.md", 4254, r"ruling of 2026-11-12"), (ML, "docs/REFERENCE.md", 5040, r"ruling of 2026-11-12")],
    30: [(CAS, "CHANGELOG.md", 34, r"Four rules \+ shared table"), (ML, "juniper-service-core/CHANGELOG.md", 73, r"Four rules \+ shared"), (ML, "docs/REFERENCE.md", 9958, r"2026-11-13")],
    34: [(ML, "CHANGELOG.md", 153, r"Add all fifteen")],
    36: [(ML, "CHANGELOG.md", 469, r"ruling of"), (ML, "docs/REFERENCE.md", 4486, r"ruling of 2026-11-15"), (ML, "docs/REFERENCE.md", 9959, r"ruling of 2026-11-15")],
}


def find_dialog(dialogs: list[dict], key: tuple[str, str]) -> dict:
    hits = [d for d in dialogs if d["session"].startswith(key[0]) and (d["asked_at"] or "").startswith(key[1])]
    if len(hits) != 1:
        raise SystemExit(f"dialog {key}: expected one, found {len(hits)}")
    return hits[0]


def answer_for(dialog: dict, question: str) -> str:
    """The answer string the result text gives for one question ("<question>"="<answer>")."""
    marker = '"' + question + '"="'
    text = dialog["answer"] or ""
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"no answer for question {question[:60]!r}")
    start += len(marker)
    return text[start : text.index('"', start)]


def labels_chosen(question: dict, answer: str) -> tuple[list[str], str]:
    """Option labels found in the answer, verbatim (with any "(Recommended)"), and the leftover typed text."""
    found = [o["label"] for o in question.get("options", []) if o["label"] in answer]
    rest = answer
    for label in found:
        rest = rest.replace(label, "")
    note = re.sub(r"^[\s,]+|[\s,]+$", "", rest)
    return found, note


def pr_row(prs: list[dict], repo: str, number: int) -> dict:
    for row in prs:
        if row["repo"] == repo and row["number"] == number:
            return row
    raise SystemExit(f"{repo}#{number} not in --prs")


def check_citation(census: Path, repo: str, path: str, line: int, pattern: str) -> bool:
    base = census / "tags" if repo == "tags" else census / repo
    try:
        lines = (base / path).read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return False
    return 0 < line <= len(lines) and re.search(pattern, lines[line - 1]) is not None


def outcome_rows(prs: list[dict], spec: list[tuple]) -> list[dict]:
    out = []
    for repo, number, role in spec:
        row = pr_row(prs, repo, number)
        out.append({"repo": repo, "pr": number, "kind": row["kind"], "role": role, "state": row["state"], "mergedAt": row["mergedAt"], "mergeCommit8": row["mergeCommit8"], "closedAt": row["closedAt"], "createdAt": row["createdAt"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dialogs", required=True)
    ap.add_argument("--prs", required=True)
    ap.add_argument("--census", required=True)
    ap.add_argument("--text38", default=None, help="the --text output (JSON) that holds ruling 38's typed message")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.dialogs, encoding="utf-8") as fh:
        dialogs = json.load(fh)
    with open(args.prs, encoding="utf-8") as fh:
        prs = json.load(fh)
    census = Path(args.census)

    rows: list[dict] = []
    failures: list[str] = []
    for number in range(15, 49):
        if number == 38:
            rec = dict(RULING_38)
            if args.text38:
                with open(args.text38, encoding="utf-8") as fh:
                    hits = [h for h in json.load(fh) if h["session"].startswith(rec["transcript"]) and rec["text_phrase"] in h["text"]]
                if len(hits) == 1:
                    rec["answered_at"] = hits[0]["timestamp"]
                    body = hits[0]["text"]
                    rec["labels"] = [" ".join(body[body.index(rec["text_phrase"]) :].split())]
            rec["outcome"] = outcome_rows(prs, RULING_38["outcome"])
            rec["citations"] = []
            del rec["text_phrase"]
            rows.append(rec)
            continue
        session, refs, summary, outcome = RULINGS[number]
        answers = []
        for key, header in refs:
            dialog = find_dialog(dialogs, key)
            question = next(q for q in dialog["questions"] if q.get("header") == header)
            raw = answer_for(dialog, question["question"])
            found, note = labels_chosen(question, raw)
            if not found:
                failures.append(f"ruling {number}: no option label found in {raw!r}")
            answers.append(
                {
                    "transcript": dialog["session"][:8],
                    "tool_use_id": dialog["tool_use_id"],
                    "asked_at": dialog["asked_at"],
                    "answered_at": dialog["answered_at"],
                    "header": header,
                    "multiSelect": question.get("multiSelect"),
                    "labels_verbatim": found,
                    "labels": [label.replace(" (Recommended)", "") for label in found],
                    "typed_note": note or None,
                    "advised": [o["label"].replace(" (Recommended)", "") for o in question.get("options", []) if o["label"].endswith("(Recommended)")],
                }
            )
        cites = []
        for repo, path, line, pattern in CITATIONS.get(number, []):
            ok = check_citation(census, repo, path, line, pattern)
            if not ok:
                failures.append(f"ruling {number}: citation {repo}:{path}:{line} does not match /{pattern}/")
            cites.append({"repo": repo if repo != "tags" else path.split("_v")[0], "path": path if repo != "tags" else "CHANGELOG.md @ " + path.split("_")[1], "line": line, "verified": ok})
        rows.append(
            {
                "number": number,
                "session": session,
                "source": "dialog",
                "answers": answers,
                "question": summary,
                "labels": [label for a in answers for label in a["labels"]],
                "outcome": outcome_rows(prs, outcome),
                "citations": cites,
            }
        )
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
    print(f"{len(rows)} ruling(s) -> {args.out}; {len(failures)} failure(s)")
    for f in failures:
        print("FAIL:", f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
