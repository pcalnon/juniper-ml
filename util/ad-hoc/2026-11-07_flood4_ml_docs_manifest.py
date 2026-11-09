#!/usr/bin/env python3
"""
Write the Cursor flood-4 juniper-ml docs carrier's manifest.json from the per-draft dispositions recorded here.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs-carrier build)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_extract.py (extract_summary.json: heads, titles),
         util/ad-hoc/2026-11-07_flood4_ml_docs_fixes.py (fixes.json: every correction, with its evidence)

Usage: 2026-11-07_flood4_ml_docs_manifest.py <work dir> <checks.json> <base_sha> <worktree> <out manifest.json>
  <work dir> holds extract_summary.json and fixes_all.json (every fix layer: rounds 1-2, then the post-rebase
  round-3 and round-4 layers), falling back to fixes.json; checks.json is {"checks": [...], "files": [...],
  "open_questions": [...]}. Entries with pr 0 (corrections of main's own wording, and of this carrier's CHANGELOG
  entry and history row) are listed under "main_text_fixes"; the rest under their draft.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

F4 = ["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/DOCUMENTATION_OVERVIEW.md", "docs/QUICK_START.md", "docs/REFERENCE.md"]
STD_DROP = "its Version History row and every version/date stamp hunk (the carrier bumps each doc once and adds one row)"
SUITE_DROP = "its one line under REFERENCE.md '## Test Suite Reference' (that block belongs to the tests carrier)"

# outcome, reason, taken (None = the four docs), extra dropped
DISPOSITIONS: dict[int, tuple[str, str, list[str] | None, list[str]]] = {
    2409: ("carried-with-fix", "config-tools alias pitfalls and the py.typed history verified (code, PyPI wheels, tags); two false statements fixed", F4 + ["juniper-config-tools/README.md"], []),
    2412: ("carried-with-fix", "E-H3 wording verified against host_state_check.py and macvm_ctl.bash; three false sentences and one unsupported sentence fixed", None, []),
    2417: ("carried-with-fix", "zero handling verified by probe (summary, plot, columns, theta); the column scope, -inf, theta 0.0 and fixture sentences fixed, and the section moved out of the Eval scalars section it had split", None, []),
    2418: ("carried-with-fix", "drop-in and key-writer contract verified line by line; the reset-list, LoadCredential, wrapper, NONE and symlink sentences fixed", None, []),
    2422: ("carried-with-fix", "failed-auth cap mechanics verified by probe; the 255-address test description and the 10,000 peak wording fixed, and the expiry-test sentences name #2419's cap test (tests carrier)", F4 + ["juniper-service-core/README.md"], []),
    2424: ("not-carried", "same claim as #2426, which is better grounded: #2424 has two false statements, drops still-true util-entry text, puts its section just before Version History, and edits a Test Suite Reference line", [], ["the whole draft; its claim is carried once, through #2426"]),
    2426: ("carried-with-fix", "G-SEC getblockall gate verified (decision table confirmed by probe); the State-0 message sentence fixed and the State-1 sentence qualified", None, []),
    2428: ("carried-with-fix", "MERGED-line SHA semantics verified; the --repo owner/repo consequence (measured), the exit-3 stream, the squash-only 'Expected' and the net-row label fixed", None, []),
    2432: ("carried-with-fix", "_read_stats/_row_metrics verified by probe; the overview scope and the /1 re-derivation exception fixed, and the section moved below the jq block it had swallowed", None, [SUITE_DROP]),
    2433: ("carried-with-fix", "token-bucket maths verified by probe; HandshakeCooldown scoped to /ws/control, the cleanup-pass timing, the rate-0 refusal and the test path fixed, and the section moved below the symptom table it had swallowed", None, []),
    2437: ("carried-with-fix", "save path verified (operation_id branch, failed phase, degraded exit 1); the cheatsheet symptom label and the overview row's dropped text fixed, and the cheatsheet Tip moved below the line it had split", None, []),
    2440: ("not-carried", "carries #2438's pre-squash commit and conflicts in five files; its launcher docs describe the scripts before #2468, whose own cheatsheet text (DEVELOPER_CHEATSHEET 173-188 on main) is current; its one still-true correction (the -- in the --fork-session example) is carried once, through #2452", [], ["the whole draft"]),
    2442: ("carried-with-fix", "anomaly detector bounds, duplicate window and accept-with-warning verified by probe; the duplicate-rule sentence fixed, windows 0, 1 and 2 and total_results stated as the code computes them (security.py:239-247, :263), and the section moved out of the REFERENCE footer", None, []),
    2444: ("carried-with-fix", "replay continuity, chunking and connection caps verified by probe; the out-of-range sentence, the 60000 framing and three pre-accept-close rows fixed", None, []),
    2446: ("carried-with-fix", "burst, Origin and cooldown edges verified by probe; the retry_after path and four sentences claiming a log carries the close code fixed (uvicorn logs only the 403)", None, []),
    2449: ("carried-with-fix", "heartbeat None-versus-zero contract verified by probe; seven rows or sentences fixed (idle pool at equality, clock clamp, StatisticsError on 3.12 only, a zero is not idle, a raising source)", None, []),
    2452: ("carried-with-fix", "only its still-true correction is carried: main's --fork-session example comment now shows the -- that wake_the_claude.bash:342 sends before the prompt (tests/test_wake_the_claude.py:1331); the rest of its launcher page predates #2468, whose own cheatsheet text is current", ["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md (one line: the --fork-session example's forwarded-argv comment)"], ["everything else: the REFERENCE 'Local Claude Launcher' page and its links, written against wake 1.0.0 / claudey 0.1.1"]),
    2456: ("carried-with-fix", "body-cap equality verified by probe; the table scoped to the ASGI layer (under uvicorn the parser answers a bad Content-Length first), the worker binary-frame cap given as 100 MiB (worker_stream.py:72), and one sentence added naming the boundary suite the tests carrier lands first", None, []),
    2457: ("carried-with-fix", "0.8.0 + model-core 0.2.0 crossval 500 verified at the tags; remedy rewritten: 0.8.1 on PyPI since 2026-11-06 09:35Z, and juniper-ml 0.11.4 floors [recurrence] at >=0.8.1", None, []),
    2460: ("carried-with-fix", "replay clamps and paused completion verified by probe; the router-mount sentence and the 'this checkout' provenance sentence fixed", None, []),
    2462: ("carried-with-fix", "65536-character equality verified (code points, not bytes); the 100 MiB total cap, the receive() path and the JSON-object qualifier fixed, and the boundary suite named", None, []),
    2464: ("carried-with-fix", "strict > at the reassignment timeout verified by probe; the late-result, tail-dispatch and ~130 s sentences fixed", None, []),
    2465: ("carried-with-fix", "the root settings.local.json is not a Claude Code settings file (repo files, and the code.claude.com settings pages re-fetched 2026-11-07); #2271's closed state and the worktree nuance fixed", None, []),
}


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(__doc__)
        return 2
    work = Path(argv[1])
    with open(work / "extract_summary.json", encoding="utf-8") as fh:
        summary = {e["pr"]: e for e in json.load(fh)}
    fixes_path = work / "fixes_all.json"
    if not fixes_path.is_file():
        fixes_path = work / "fixes.json"
    with open(fixes_path, encoding="utf-8") as fh:
        fixes = json.load(fh)
    with open(argv[2], encoding="utf-8") as fh:
        extra = json.load(fh)
    carried = []
    pending = []
    for pr in sorted(DISPOSITIONS):
        outcome, reason, taken, dropped = DISPOSITIONS[pr]
        if outcome == "PENDING":
            pending.append(pr)
        own = [f"{f['path']}: {'block moved' if 'move' in f else repr(f['old'][:60]) + ' rewritten'} -- {f['why']}" for f in fixes if f["pr"] == pr]
        carried.append(
            {
                "pr": pr,
                "head_sha": summary[pr]["head_sha"],
                "title": summary[pr]["title"],
                "taken": list(F4) if taken is None else taken,
                "fixes": own,
                "dropped": ([] if outcome == "not-carried" else [STD_DROP]) + dropped,
                "outcome": outcome,
                "reason": reason,
            }
        )
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "docs",
        "base_sha": argv[3],
        "worktree": argv[4],
        "files": extra["files"],
        "carried": carried,
        "fix_layers": fixes_path.name,
        "main_text_fixes": [f"{f['path']}: {repr(f['old'][:60])} rewritten -- {f['why']}" for f in fixes if f["pr"] == 0 and "move" not in f],
        "checks": extra["checks"],
        "mutations": extra.get("mutations", []),
        "open_questions": extra["open_questions"],
        "validator_findings": extra.get("validator_findings", []),
    }
    with open(argv[5], "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    counts: dict[str, int] = {}
    for c in carried:
        counts[c["outcome"]] = counts.get(c["outcome"], 0) + 1
    print(f"manifest: {len(carried)} drafts {counts}; pending={pending}")
    return 1 if pending else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
