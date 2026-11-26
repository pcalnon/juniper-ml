#!/usr/bin/env python3
"""
Build the r23w claims lens's fixes.json and check every fix against the post-code-lens texts, in order.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14 claims lens r23w-val-claims, run in session 15 on 2026-11-26 UTC)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23);
         util/ad-hoc/2026-11-25_flood4_s14_fixpass.py (which applies the result)

What it does
------------
FIXES below is the lens's list ({"id", "severity", "file", "old", "new", "why"}). --work is a directory laid out like
the repository holding the carrier's files with the code lens's fixes applied, plus texts/; --extra lists further
repo-relative files to read from --extra-root when --work lacks them (a file the carrier does not carry yet). Each fix's
old text must occur exactly once in its file as it stands at its turn (the fixes apply in list order, as the fix pass
applies them); the script reports each one and writes --out only when all pass. It never writes into --work.

Usage
-----
    python3 -I <this file> --work DIR --extra-root CLONE --out fixes.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SC = "juniper-service-core"
SC_CL = f"{SC}/CHANGELOG.md"
REF = "docs/REFERENCE.md"
CHEAT = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
ROOT_CL = "CHANGELOG.md"
MGR = f"{SC}/juniper_service_core/websocket/manager.py"
N4_TEST = f"{SC}/tests/test_websocket_broadcast_drop_close.py"
PR = "texts/pr_body.txt"
CB = "texts/commit_body.txt"

K1_WHY = (
    "Measured: with the default caps (max_connections_per_ip 5, max_connections 50) a reconnect from the dropped socket's "
    "address is ADMITTED while the dropped socket is still open -- HTTP 101 on uvicorn 0.54.0 under websockets, "
    "websockets-sansio and wsproto, connection_established data.connections 2 (probe/wire_fix_<impl>_cap5.json), and "
    "accepted in process under TestClient, connections 2 (probe/testclient_fix_py3.13.json c_defaults). Only a reconnect "
    "that would exceed a cap waits (cap 1: HTTP 403, probe/wire_fix_<impl>_cap1.json). Extends the code lens's C4 "
    "sentences, which give the length of the wait but not when it applies."
)

FIXES: list[dict] = [
    # ---------------------------------------------------------------- K1 MAJOR: the cost applies only at a full cap
    {
        "id": "K1a",
        "severity": "MAJOR",
        "file": PR,
        "old": "- **The cost of holding the slot, measured.** A reconnect from the address of a dropped socket waits until that socket is gone: at once with a client that takes the close. With a client that has stopped reading, as long as the ASGI server keeps the connection, since the handler's drain has no time bound of its own (N-4's remaining known limit, \"A close that never completes\"). On uvicorn 0.54.0 the second socket got HTTP 403 while the first was open in all three implementations.",
        "new": "- **The cost of holding the slot, measured.** A dropped socket keeps its slots until it is gone, so a reconnect from its address waits for that only when it would exceed a cap: the address's `max_connections_per_ip`, which counts the dropped socket, or the server's `max_connections`. One under both caps is admitted at once: with the default per-IP cap of 5, a client that reconnects once is not held up. The old socket is gone at once with a client that takes the close. With a client that has stopped reading, as long as the ASGI server keeps the connection, since the handler's drain has no time bound of its own (N-4's remaining known limit, \"A close that never completes\"). On uvicorn 0.54.0, with `max_connections_per_ip=1`, the second socket got HTTP 403 while the first was open in all three implementations; with the default of 5 it got HTTP 101, and its `connection_established` counted 2 connections.",
        "why": K1_WHY + " The bullet's later sentences (C4d's included) stay as they are: they are the cap-1 measurement, which this now names.",
    },
    {
        "id": "K1b",
        "severity": "MAJOR",
        "file": CB,
        "old": "  transport_stats() gains dropped_connections. The cost: a reconnect from that address waits until the\n  old socket is gone, which with a client that has stopped reading lasts as long as the ASGI server\n  keeps the connection.",
        "new": "  transport_stats() gains dropped_connections. The cost: a reconnect from that address that would\n  exceed a cap (max_connections_per_ip counts the dropped socket) waits until the old socket is gone;\n  one under both caps is admitted at once. With a client that has stopped reading, the old socket lasts\n  as long as the ASGI server keeps the connection: under uvicorn 0.54.0's websockets-sansio (what\n  ws=\"auto\" selects) and wsproto, until the client's connection goes, past uvicorn's own keepalive\n  timeout.",
        "why": K1_WHY + " The code lens's fixes do not touch the commit body: this also carries C4's correction (held 180 s in its measurement, 75 s in mine, past the 20 s + 20 s keepalive: probe/wire_fix_<impl>_cap1_hold75.json).",
    },
    {
        "id": "K1c",
        "severity": "MAJOR",
        "file": ROOT_CL,
        "old": "  (`transport_stats()[\"dropped_connections\"]`), and a socket from that address is refused 1013 meanwhile.\n  - The cost: a reconnect from the address of a dropped socket waits until that socket is gone; with a client that has\n    stopped reading, as long as the ASGI server keeps the connection (29.5 s under uvicorn 0.54.0's `websockets`",
        "new": "  (`transport_stats()[\"dropped_connections\"]`), and meanwhile a socket from that address past\n  `max_connections_per_ip` is refused 1013 (HTTP 403 under uvicorn).\n  - The cost: a reconnect from the address of a dropped socket that would exceed a cap waits until that socket is gone\n    (one under both caps is admitted at once); with a client that has stopped reading, as long as the ASGI server\n    keeps the connection (29.5 s under uvicorn 0.54.0's `websockets`",
        "why": K1_WHY + " Also names the HTTP 403 a uvicorn client sees instead of the 1013 (measured: probe/wire_fix_<impl>_cap1.json). Leaves C4a's text after it unchanged.",
    },
    {
        "id": "K1d",
        "severity": "MAJOR",
        "file": SC_CL,
        "old": "    releases both slots. Neither cap is exceeded: meanwhile a socket from the same address is refused\n    **1013** `Per-IP connection limit reached`, and one past the global cap **1013** `Maximum\n    connections reached`",
        "new": "    releases both slots. Neither cap is exceeded: meanwhile a socket from the same address past\n    `max_connections_per_ip` is refused **1013** `Per-IP connection limit reached`, and one past the\n    global cap **1013** `Maximum connections reached`",
        "why": K1_WHY,
    },
    {
        "id": "K1e",
        "severity": "MAJOR",
        "file": SC_CL,
        "old": "  - **What it costs.** A reconnect from the address of a dropped socket waits until that socket is\n    gone: at once with a client that takes the close, and with one that has stopped reading for as long\n    as the ASGI server keeps the connection, since the handler's drain has no time bound of its own\n    (the 29.5 s above; under `websockets-sansio` and `wsproto`, until the client's connection goes).",
        "new": "  - **What it costs.** A reconnect from the address of a dropped socket that would exceed a cap (the\n    per-IP cap counts the dropped socket) waits until that socket is gone, while one under both caps is\n    admitted at once, as before. The old socket is gone at once with a client that takes the close; with\n    one that has stopped reading it lasts as long as the ASGI server keeps the connection, since the\n    handler's drain has no time bound of its own (the 29.5 s above; under `websockets-sansio` and\n    `wsproto`, until the client's connection goes).",
        "why": K1_WHY,
    },
    {
        "id": "K1f",
        "severity": "MAJOR",
        "file": REF,
        "old": "so neither cap is exceeded while the socket closes, and a reconnect from its address waits until the old socket is gone. Releasing them at the drop again",
        "new": "so neither cap is exceeded while the socket closes, and a reconnect from its address that would exceed either cap waits until the old socket is gone. Releasing them at the drop again",
        "why": K1_WHY + " (Shared Service-Core Contracts bullet.)",
    },
    {
        "id": "K1g",
        "severity": "MAJOR",
        "file": REF,
        "old": "its close never written, and a reconnect from its address was refused all that time.",
        "new": "its close never written, and, with `max_connections_per_ip=1`, a reconnect from its address was refused all that time.",
        "why": K1_WHY + " (\"What the close does not fix\"; the paragraph as the code lens's C4b leaves it names no cap.)",
    },
    {
        "id": "K1h",
        "severity": "MAJOR",
        "file": REF,
        "old": "Meanwhile a socket from the same address is refused **1013** `Per-IP connection limit reached`, and one past the global cap **1013** `Maximum connections reached` (uvicorn answers both with HTTP 403); once the old socket is gone, the next is admitted.",
        "new": "Meanwhile a socket from the same address past `max_connections_per_ip`, which counts the dropped socket, is refused **1013** `Per-IP connection limit reached`, and one past the global cap **1013** `Maximum connections reached` (uvicorn answers both with HTTP 403); once the old socket is gone, the next is admitted. A socket under both caps is admitted at once, as before.",
        "why": K1_WHY + " (the fixed-list bullet)",
    },
    {
        "id": "K1i",
        "severity": "MAJOR",
        "file": REF,
        "old": "The cost: a reconnect from that address waits until the old socket is gone. Measured on uvicorn 0.54.0, with a cap of 1,",
        "new": "The cost: a reconnect from that address that would exceed a cap waits until the old socket is gone; with the default cap of 5, the second socket below was admitted (HTTP 101) and its `connection_established` counted 2 connections. Measured on uvicorn 0.54.0, with a cap of 1,",
        "why": K1_WHY + " (the fixed-list bullet)",
    },
    {
        "id": "K1j",
        "severity": "MAJOR",
        "file": REF,
        "old": "| The dropped socket keeps its connection and per-IP slots until its handler returns, so the old socket has to be gone first:",
        "new": "| The dropped socket keeps its connection and per-IP slots until its handler returns, so while its address is at `max_connections_per_ip` (the dropped socket counts) the old socket has to be gone first:",
        "why": K1_WHY + " (troubleshooting row \"A reconnect from the same address is refused\")",
    },
    {
        "id": "K1k",
        "severity": "MAJOR",
        "file": REF,
        "old": "(new key `dropped_connections`; a reconnect from its address waits until it is gone)",
        "new": "(new key `dropped_connections`; a reconnect from its address that would exceed a cap waits until it is gone)",
        "why": K1_WHY + " (the 0.6.85 Version History row)",
    },
    {
        "id": "K1l",
        "severity": "MAJOR",
        "file": CHEAT,
        "old": "so neither cap is exceeded while it closes and a reconnect from its address is refused **1013** until the old socket is gone;",
        "new": "so neither cap is exceeded while it closes: a reconnect from its address past `max_connections_per_ip` (the dropped socket counts) is refused **1013** (HTTP 403 on uvicorn) until the old socket is gone, and one under both caps is admitted at once;",
        "why": K1_WHY + " The cheatsheet tip is the most categorical of the eight sites.",
    },
    # ---------------------------------------------------------------- K2 MINOR: counts the code lens's C1/C2 left stale
    {
        "id": "K2a",
        "severity": "MINOR",
        "file": SC_CL,
        "old": "  - **Tests**: `tests/test_websocket_unsendable_late_frame_and_slot.py` (23 tests) pins all three over\n    a real Starlette `WebSocket` bound to an in-memory ASGI peer that encodes text as UTF-8. Against\n    the previous `manager.py` and `control_stream.py` 18 of them fail; the other 5 are controls:",
        "new": "  - **Tests**: `tests/test_websocket_unsendable_late_frame_and_slot.py` (28 tests) pins all three over\n    a real Starlette `WebSocket` bound to an in-memory ASGI peer that encodes text as UTF-8. Against\n    the previous `manager.py` and `control_stream.py` 23 of them fail; the other 5 are controls:",
        "why": "After the code lens's C1 (4 parametrised cases) and C2-test (1) the file collects 28 tests; against main's manager.py and control_stream.py 23 fail and the same 5 controls pass (logs/newtests_main_py3.13.log; collect: 28). The code lens asked for these counts to be updated but its fixes.json does not do it.",
    },
    {
        "id": "K2b",
        "severity": "MINOR",
        "file": ROOT_CL,
        "old": "(23 tests): 18 fail without\n    this change, 5 are controls.",
        "new": "(28 tests): 23 fail without\n    this change, 5 are controls.",
        "why": "As K2a.",
    },
    {
        "id": "K2c",
        "severity": "MINOR",
        "file": REF,
        "old": "`tests/test_websocket_unsendable_late_frame_and_slot.py` (28 tests, the same in-memory peer",
        "new": "`tests/test_websocket_unsendable_late_frame_and_slot.py` (28 tests, the same in-memory peer",
        "why": "PLACEHOLDER (replaced below)",
    },
    {
        "id": "K2d",
        "severity": "MINOR",
        "file": REF,
        "old": "`test_a_command_still_running_when_the_heartbeat_closes_is_not_acknowledged`, `test_the_idle_timeout_after_a_heartbeat_close_does_not_close_again`",
        "new": "`test_a_command_still_running_when_the_heartbeat_closes_is_not_acknowledged`, `test_a_command_running_at_the_heartbeat_close_is_not_acknowledged_however_it_ends` (its result, a rejection, an unexpected error, a timeout), `test_the_idle_timeout_after_a_heartbeat_close_does_not_close_again`",
        "why": "The gate line lists every test in the file; the code lens's C1 adds this one (b8-b11 die only to it: r23w-val-code mut/mutants_prop_py3.13.json, killed 4/4).",
    },
    {
        "id": "K2e",
        "severity": "MINOR",
        "file": REF,
        "old": "`test_close_all_forgets_a_dropped_socket`, and the controls",
        "new": "`test_close_all_forgets_a_dropped_socket`, `test_close_all_leaves_no_address_charged`, and the controls",
        "why": "As K2d, for the code lens's C2-test.",
    },
    {
        "id": "K2f",
        "severity": "MINOR",
        "file": CB,
        "old": "tests/test_websocket_unsendable_late_frame_and_slot.py: 23 tests, 18 of which fail against main's\nmanager.py and control_stream.py; 5 are controls.",
        "new": "tests/test_websocket_unsendable_late_frame_and_slot.py: 28 tests, 23 of which fail against main's\nmanager.py and control_stream.py; 5 are controls.",
        "why": "As K2a.",
    },
    {
        "id": "K2g",
        "severity": "MINOR",
        "file": PR,
        "old": "All runs were on this change at `main` `82ccd7c5` on 2026-11-25 (UTC), in a fresh clone; a local unsigned probe commit was made only for the sequence-safety screens.",
        "new": "The runs below are on two sets of bytes, each in a fresh clone. \"Built\" is this change as first built, at `main` `82ccd7c5` on 2026-11-25 (UTC); a local unsigned probe commit was made only for the sequence-safety screens. \"Final\" adds the validators' fixes (two more tests in the new file, 28 in all; `close_all()` clearing the per-IP counts; one docstring in `test_websocket_broadcast_drop_close.py`; docstrings and texts), at `main` `b9442e3c`, whose two commits since `82ccd7c5` touch none of these files. A result not marked final is on the built bytes.",
        "why": "After the code lens's fixes (and these) the Testing section's \"Every result above is on the final bytes\" is false: its numbers are the built bytes'. Final-bytes runs: logs/ci_final_py3.1{2,3,5}.*, logs/newtests_main_py3.13.log, logs/mutants_builder_helper_py3.13.log, the code lens's logs/flakes_prop_py3.13.txt (test file sha 38485b8b, the final one).",
    },
    {
        "id": "K2h",
        "severity": "MINOR",
        "file": PR,
        "old": "  | Python | this change | `main` | total coverage | per-file gate |\n  |--------|-------------|--------|----------------|---------------|\n  | 3.12.11 | 1262 passed | not run | 99% | PASS |\n  | 3.13.13 | 1262 passed | 1239 passed | 99% | PASS |\n  | 3.14.7 | 1262 passed | not run | 99% | PASS |\n\n  1262 = 1239 + 23. `manager.py` (362 statements) and `control_stream.py` (177) have no missed statement.",
        "new": "  | Python | final | built | `main` | total coverage | per-file gate |\n  |--------|-------|-------|--------|----------------|---------------|\n  | 3.12.11 | 1267 passed | 1262 passed | not run | 99% | PASS |\n  | 3.13.13 | 1267 passed | 1262 passed | 1239 passed | 99% | PASS |\n  | 3.15.2 (CI's informational leg) | 1267 passed | 1262 passed | not run | 99% | PASS |\n  | 3.14.7 (not a CI leg) | not run | 1262 passed | not run | 99% | PASS |\n\n  1267 = 1239 + 28 (built: 1262 = 1239 + 23). On the final bytes `manager.py` (363 statements) and `control_stream.py` (177) have no missed statement.",
        "why": "Final bytes measured: 1267 passed, TOTAL 99%, gate PASS on 3.12.11, 3.13.13 and 3.15.2; manager.py 363 stmts 0 missed (270->exit), control_stream.py 177/0 (206->211) (logs/ci_final_py3.1{2,3,5}.*). ci-service-core.yml's legs are 3.12 and 3.13 (blocking) and 3.15 (informational), not 3.14 (the code lens's C6). Built 3.15.2 = the code lens's run.",
    },
    {
        "id": "K2i",
        "severity": "MINOR",
        "file": PR,
        "old": "- **Failing first.** The new file against `main`'s `manager.py` and `control_stream.py`: 18 failed and 5 passed (the controls), on 3.12, 3.13 and 3.14.",
        "new": "- **Failing first.** The new file against `main`'s `manager.py` and `control_stream.py`: built, 18 failed and 5 passed (the controls) on 3.12, 3.13 and 3.14; final, 23 failed and the same 5 passed, on 3.13.",
        "why": "logs/newtests_main_py3.13.log (the final file in a copy of main's tree, main's venv): 23 FAILED, 5 PASSED, the 5 being the named controls.",
    },
    {
        "id": "K2j",
        "severity": "MINOR",
        "file": PR,
        "old": "  - All 27 are killed by a test they name, on 3.12 and on 3.13. A canary arm fails, the unmutated copy passes its 43 tests, and the tree's sha256 is the same before and after.",
        "new": "  - All 27 are killed by a test they name, on 3.12 and on 3.13, and again on the final bytes (3.13). A canary arm fails, the unmutated copy passes its 43 tests (48 on the final bytes), and the tree's sha256 is the same before and after.\n  - The four acknowledgments `_handle_command_message` sends after a command has run (its result, a timeout, a rejection, an unexpected error) are each pinned by `test_a_command_running_at_the_heartbeat_close_is_not_acknowledged_however_it_ends`: a mutant that sends any one of them unguarded fails it, and passes every other test.",
        "why": "logs/mutants_builder_helper_py3.13.log on the final tree: 27 killed, canary failed, control 48 passed, tree unchanged. The four ack mutants (b8-b11) are the code lens's: r23w-val-code mut/mutants_py3.13.json (survive without C1) and mut/mutants_prop_py3.13.json (killed 4/4 with it).",
    },
    {
        "id": "K2k",
        "severity": "MINOR",
        "file": PR,
        "old": "- **Flakiness.** The new file ran 50 times on each of 3.12, 3.13 and 3.14, each run in a fresh process: 150 of 150 passed all 23 tests.",
        "new": "- **Flakiness.** Built: the new file ran 50 times on each of 3.12, 3.13 and 3.14, each run in a fresh process: 150 of 150 passed all 23 tests. Final: 50 of 50 fresh-process runs passed all 28, on 3.13.",
        "why": "The code lens's 50 runs (r23w-val-code logs/flakes_prop_py3.13.txt: run 1-50 exit=0) used the test file whose sha256 is 38485b8b..., the final one (logs/work_post_codelens_sha256.txt).",
    },
    {
        "id": "K2l",
        "severity": "MINOR",
        "file": PR,
        "old": "On the first run the Ruff lint hook turned one `getattr(module, \"name\")` in the new test into attribute access. Every result above is on the final bytes, and a second run changed nothing.",
        "new": "On the first run the Ruff lint hook turned one `getattr(module, \"name\")` in the new test into attribute access, and a second run changed nothing. On the final bytes, run on the 12 files: exit 0, and no file changed.",
        "why": "\"Every result above is on the final bytes\" is false once the validators' fixes are applied. pre-commit on the final bytes: logs/precommit_final.log.",
    },
    {
        "id": "K2n",
        "severity": "MINOR",
        "file": PR,
        "old": "juniper-ml#2547 recorded both failing the same way on a clean `main`.",
        "new": "juniper-ml#2547 recorded both failing the same way on a clean `main`. On the final bytes, the same 112 suites run the same way: 3,522 tests, 110 suites pass, and the same two fail with the same tests.",
        "why": "logs/reader_final.json (115 files: 112 suites ci.yml invokes + 3 helper modules, py3.14.7, 3 jobs): 3522 tests, 110 pass; test_e2e_f037_render_census (1) and test_replay_redrive_stack_refusal (13) fail with failing-test sets identical to the code lens's clean-main run (logs/reader_{final,main}_*_fails*.txt).",
    },
    {
        "id": "K2o",
        "severity": "MINOR",
        "file": PR,
        "old": "- **Docs.** `util/ad-hoc/2026-09-05_markdown_structure_check.py` finds 0 problems in the 4 changed `.md` files.",
        "new": "- **Docs.** `util/ad-hoc/2026-09-05_markdown_structure_check.py` finds 0 problems in the 4 changed `.md` files, built and final.",
        "why": "Final bytes: structural problems 0, examined 4 of 4 (logs/markdown_structure_final.log).",
    },
    {
        "id": "K2p",
        "severity": "MINOR",
        "file": PR,
        "old": "- **Sequence safety**, on a local unsigned probe commit: `juniper-symbol-loss-check`",
        "new": "- **Sequence safety**, on a local unsigned probe commit, built and final: `juniper-symbol-loss-check`",
        "why": "Final bytes, unsigned local probe commit df1e93d over origin/main b9442e3c: symbol-loss files_screened=4 findings=0; docs-additions files_screened=2 findings=15 (small-deletion) fail=0 (logs/seqsafety_{symbol,docs}_final.txt).",
    },
    {
        "id": "K2q",
        "severity": "MINOR",
        "file": PR,
        "old": "Its `--known-answer` check passes.",
        "new": "Its `--known-answer` check passes. On the final bytes the four changed package and test files predict the same one alert.",
        "why": "logs/codeql_prescreen_final.log: control_stream.py:388 empty-except, 1 predicted alert in 4 files (manager.py, control_stream.py, the new test file, test_websocket_broadcast_drop_close.py).",
    },
    {
        "id": "K2m",
        "severity": "NIT",
        "file": PR,
        "old": "- Not run: macOS, hypercorn, daphne. The code lens ran the two this list used to name: CI's informational Python 3.15 leg (3.15.2: 1262 passed, 99%, per-file gate PASS) and uvicorn 0.29.0, the `[test]` extra's floor,",
        "new": "- Not run: macOS, hypercorn, daphne. Python 3.15 is in the Testing table. uvicorn 0.29.0, the `[test]` extra's floor, was run",
        "why": "Replaces part of the code lens's C6: its 3.15 result (built bytes) is now a row of the Testing table, beside the final bytes' 1267 (K2h); the rest of C6's sentence stays.",
    },
    # ---------------------------------------------------------------- K3 MINOR: close_all() now changes (code lens C2-code)
    {
        "id": "K3a",
        "severity": "MINOR",
        "file": SC_CL,
        "old": "every close code and reason, `close_all()`\n    (it forgets a dropped socket with the rest and does not close it again), and `training_stream.py`.",
        "new": "every close code and reason, and `training_stream.py`.\n  - **`close_all()`** forgets a dropped socket with the rest and does not close it again, and it now\n    clears the per-IP counts: the handlers' later `disconnect()` finds no record to release, so before,\n    every address with a socket open at `close_all()` stayed charged against `max_connections_per_ip`\n    for good.",
        "why": "The code lens's C2-code makes close_all() clear _per_ip_counts, so \"Unchanged ... close_all()\" is false (its measurement: inproc/{main,fix}_py3.13.json close_all_per_ip; pinned by C2-test, which fails on main: logs/newtests_main_py3.13.log).",
    },
    {
        "id": "K3b",
        "severity": "MINOR",
        "file": PR,
        "old": "and `close_all()` forgets `_dropped` with the rest.",
        "new": "and `close_all()` forgets `_dropped` with the rest and clears the per-IP counts, which its handlers' later `disconnect()` cannot release once their records are gone.",
        "why": "As K3a (The fixes).",
    },
    {
        "id": "K3c",
        "severity": "MINOR",
        "file": PR,
        "old": "None of the shipped handlers uses `connect()`.\n- **Unchanged**:",
        "new": "None of the shipped handlers uses `connect()`.\n- **After `close_all()`** no address stays charged. Before, the handlers' later `disconnect()` found no record to release, so every address with a socket open at `close_all()` stayed charged against `max_connections_per_ip` for good.\n- **Unchanged**:",
        "why": "As K3a: a client-visible admission change the code lens's C2-code adds (What changes for a client).",
    },
    {
        "id": "K3d",
        "severity": "MINOR",
        "file": REF,
        "old": "A broadcast's drop does not: the dropped socket keeps both until its handler's `disconnect()` (unreleased, 0.8.0; through 0.7.2 the drop returned both at once).",
        "new": "A broadcast's drop does not: the dropped socket keeps both until its handler's `disconnect()` (unreleased, 0.8.0; through 0.7.2 the drop returned both at once). `close_all()` clears every per-IP count, since the handlers' later `disconnect()` finds no record to release (unreleased, 0.8.0; through 0.7.2 an address with a socket open at `close_all()` stayed charged).",
        "why": "As K3a (the caps paragraph).",
    },
    {
        "id": "K3e",
        "severity": "MINOR",
        "file": REF,
        "old": "the caps paragraph counts dropped sockets,",
        "new": "the caps paragraph counts dropped sockets and says `close_all()` clears the per-IP counts,",
        "why": "Keeps the 0.6.85 Version History row in step with K3d.",
    },
    # ---------------------------------------------------------------- K4 MINOR: a stale troubleshooting sentence
    {
        "id": "K4a",
        "severity": "MINOR",
        "file": REF,
        "old": "If every resume stops at the same seq, that frame may be one the transport cannot serialise (Starlette's `send_json` has no `default=`): it also failed every live send. ",
        "new": "A frame the transport cannot serialise no longer causes it: such a broadcast is refused before it takes a seq, so it never enters the replay (ERROR `Broadcast refused`, two rows below). ",
        "why": "Row \"Training socket closed 1011 Resume replay incomplete after resume_ok\" (unreleased, 0.8.0) still describes the old behaviour as current: on the fix an unsendable broadcast takes no seq and a resume across it is continuous (probe/testclient_fix_py3.13.json a_unsendable.resume: resume_ok then seq 2; main: resume_ok then 1011 Resume replay incomplete). The carrier rewrote the next row's matching sentence, not this one.",
    },
    {
        "id": "K4b",
        "severity": "MINOR",
        "file": REF,
        "old": "troubleshooting gains two rows and rewrites one sentence;",
        "new": "troubleshooting gains two rows and rewrites two sentences;",
        "why": "Keeps the 0.6.85 Version History row in step with K4a.",
    },
    {
        "id": "K4c",
        "severity": "MINOR",
        "file": PR,
        "old": "troubleshooting (one sentence and two rows)",
        "new": "troubleshooting (two sentences and two rows)",
        "why": "Keeps the Changed list in step with K4a.",
    },
    # ---------------------------------------------------------------- K5 MINOR: N-4's test docstring states the old timing
    {
        "id": "K5a",
        "severity": "MINOR",
        "file": N4_TEST,
        "old": "    \"\"\"Forgotten by the broadcast, then disconnected again by its own handler: one release, not two.\n\n    Only end states are asserted, so this does not fix *when* the slot is released (at the drop, today).\n    \"\"\"",
        "new": "    \"\"\"Dropped by the broadcast, then disconnected by its own handler: one release, not two.\n\n    Only end states are asserted, so this does not fix *when* the slot is released: when the handler's\n    ``disconnect()`` runs, which ``test_websocket_unsendable_late_frame_and_slot.py`` pins.\n    \"\"\"",
        "why": "main's juniper-service-core/tests/test_websocket_broadcast_drop_close.py:485-487 (not in the carrier) says the slot is released \"at the drop, today\", which this change makes false (probe/testclient_fix_py3.13.json c_per_ip_1: per_ip {testclient: 1} at the drop, {} after the handler returned). docs/REFERENCE.md's gate line was rewritten for the same test; its docstring was not. The file must be added to the carrier (copy main's) before this applies; K5b names it.",
    },
    {
        "id": "K5b",
        "severity": "MINOR",
        "file": PR,
        "old": "- `juniper-service-core/tests/test_websocket_unsendable_late_frame_and_slot.py` (new)\n",
        "new": "- `juniper-service-core/tests/test_websocket_unsendable_late_frame_and_slot.py` (new)\n- `juniper-service-core/tests/test_websocket_broadcast_drop_close.py`: the docstring of `test_a_dropped_sockets_per_ip_slot_is_released_once`, which said the slot is released at the drop\n",
        "why": "Names K5a's file in the Changed list.",
    },
    # ---------------------------------------------------------------- K6 MINOR: "forgets" meant disconnect() in N-4's entry
    {
        "id": "K6a",
        "severity": "MINOR",
        "file": SC_CL,
        "old": "  - `broadcast` now forgets every failed socket, then closes each **1011** `Broadcast send failed\n    or timed out`:",
        "new": "  - `broadcast` now takes every failed socket out of the fan-out, then closes each **1011**\n    `Broadcast send failed or timed out`:",
        "why": "N-4's entry defines \"forgets\" as disconnect() (its first sentence: \"with `disconnect()` alone, which forgets a socket but never closes it\"), so \"now forgets every failed socket\" says the drop releases the slots, contradicting the new entry in the same [Unreleased] notes. The carrier rewrote manager.py's own \"Every socket is forgotten\" to \"leaves the fan-out\" for the same reason.",
    },
    {
        "id": "K6b",
        "severity": "MINOR",
        "file": REF,
        "old": "`_drop` forgets every failed socket before it closes any,",
        "new": "`_drop` takes every failed socket out of the fan-out before it closes any,",
        "why": "As K6a, in the Shared Service-Core Contracts bullet, whose next sentences now say the drop holds the slots.",
    },
    # ---------------------------------------------------------------- NITs
    {
        "id": "K7",
        "severity": "NIT",
        "file": MGR,
        "old": "- Monotonically increasing sequence numbers on broadcasts -- every broadcast, whether or not a\n  client is connected, so a gap in the numbering is a gap in what the client received.",
        "new": "- Monotonically increasing sequence numbers on broadcasts -- every broadcast, whether or not a\n  client is connected (one refused because no socket could be sent it takes none), so a gap in the\n  numbering is a gap in what the client received.",
        "why": "manager.py's module docstring says every broadcast is numbered; a refused one is not (probe/testclient_fix_py3.13.json a_unsendable: current_seq stays 1).",
    },
    {
        "id": "K8a",
        "severity": "NIT",
        "file": CB,
        "old": "- /ws/control after the server's close. A frame arriving after the heartbeat's 1011 close ended\n  control_stream_handler with Starlette's RuntimeError, and a late command was executed before its\n  acknowledgment raised.",
        "new": "- /ws/control after the server's close. A frame arriving after the heartbeat's 1011 close ended\n  control_stream_handler with Starlette's RuntimeError (in process, and under uvicorn's websockets\n  implementation; its websockets-sansio and wsproto report the disconnect first), and a late command\n  was executed before its acknowledgment raised. A command still running when the heartbeat closed\n  ended the handler the same way under all three, at its acknowledgment.",
        "why": "The code lens's C3a-C3d qualify this in the PR body and both CHANGELOGs, not in the commit body. Measured: probe/testclient_main_py3.13.json b_late_command / b_inflight_command (both raise in process); the code lens's wire/main/probe313/b_hb_inflight_<impl>.json (raised, 1 ASGI exception, under all three).",
    },
    {
        "id": "K8b",
        "severity": "NIT",
        "file": PR,
        "old": "  - The handler no longer raises: no `Exception in ASGI application` under uvicorn's `websockets` implementation.",
        "new": "  - The handler no longer raises: no `Exception in ASGI application`, for a late frame under uvicorn's `websockets` implementation, and for a command running at the close under every implementation.",
        "why": "After the code lens's C3a the gaps section says the in-flight command crashed main under all three implementations; this client-change line still named only `websockets`.",
    },
    {
        "id": "K9a",
        "severity": "NIT",
        "file": PR,
        "old": "This logs only the frame's `type` and the exception's class, so no value from the message is printed.",
        "new": "This logs only the message's `type` (as its `repr`, so a lone surrogate there is printed escaped) and the exception's class, so no other value from the message is printed.",
        "why": "The ERROR line prints repr(message['type']): for {'type': 'm' + a lone surrogate} it printed \"a 'm\\udc80' message\" (probe/testclient_fix_py3.13.json a_unsendable.surrogate_in_type), so \"no value from the message is printed\" is not quite true; and it is the message's type (message.get('type') in _refuse_unsendable), not the failing frame's (a chunk's is chunked_message).",
    },
    {
        "id": "K9b",
        "severity": "NIT",
        "file": MGR,
        "old": "ERROR, since the producer is at fault: the frame's ``type`` when it is a string, and the\n        exception's class, never a value from the message.",
        "new": "ERROR, since the producer is at fault: the message's ``type`` (its ``repr``) when it is a string,\n        and the exception's class, never another value from the message.",
        "why": "As K9a, in _refuse_unsendable's docstring.",
    },
    {
        "id": "K10",
        "severity": "NIT",
        "file": ROOT_CL,
        "old": "`util/ad-hoc/2026-11-25_flood4_s14_r23w_probe.py` reproduces all three on a tree without\n    the fix, in process and under real uvicorn.",
        "new": "`util/ad-hoc/2026-11-25_flood4_s14_r23w_probe.py` reproduces all three on a tree without\n    the fix in process, and the second and third under real uvicorn.",
        "why": "The builder's probe has no uvicorn scenario for gap (a): its uvicorn mode takes --scenario {late_pong, late_command, stall} (its header).",
    },
    {
        "id": "K11",
        "severity": "NIT",
        "file": PR,
        "old": "the send timeout itself is unchanged.",
        "new": "the send timeout itself is unchanged.\n- References JR-ML-WS-112 (GAP-WS-27: per-IP connection caps and DoS protection in cascor's `WebSocketManager`; `notes/requirements/by-area/WS.md`). The per-IP cap now also holds while a dropped socket closes.",
        "why": "notes/requirements/by-area/WS.md:1253 (status proposed); gap (c) is the per-IP cap, as relevant as JR-ML-WS-061 is to the drop.",
    },
    {
        "id": "K12",
        "severity": "NIT",
        "file": SC_CL,
        "old": "(the Fixed entry \"A dropped socket keeps its\n  connection and per-IP slots until its handler returns\")",
        "new": "(the Fixed entry \"The three WebSocket gaps\n  beside the broadcast drop-and-close are fixed\")",
        "why": "No entry has the quoted title; it is the last clause of the new Fixed entry's title, which the other two cross-references in this file cite by its first words.",
    },
    {
        "id": "K13",
        "severity": "NIT",
        "file": PR,
        "old": "it took no seq, and no socket was sent it or closed`.\n- **`/ws/control` after the heartbeat's **1011** close.**",
        "new": "it took no seq, and no socket was sent it or closed`.\n- **In process, under Starlette's `TestClient`** (which does not encode text as UTF-8), a broadcast holding a lone surrogate was delivered and is now refused like the rest; a real ASGI server could not send it.\n- **`/ws/control` after the heartbeat's **1011** close.**",
        "why": "Measured: probe/testclient_main_py3.13.json a_unsendable.lone_surrogate (delivered as seq 1) vs probe/testclient_fix_py3.13.json (refused, UnicodeEncodeError, no seq). A test-visible change the list omits.",
    },
    {
        "id": "K14",
        "severity": "NIT",
        "file": MGR,
        "old": "one that has stopped reading, it is as long as the ASGI server takes to give up on the\n        connection. Through",
        "new": "one that has stopped reading, as long as its connection lasts, which uvicorn's\n        ``websockets-sansio`` and ``wsproto`` keep until the client goes. Through",
        "why": "_drop's docstring: under uvicorn 0.54.0's default implementation and wsproto the server does not give up while the client lives (held 75 s here, past the 20 s + 20 s keepalive: probe/wire_fix_<impl>_cap1_hold75.json; 180 s in the code lens's C4). training_stream.py's _drain_until_disconnect has the same phrase (findings K14; no fix proposed, the PR states that file unchanged).",
    },
    {
        "id": "K15",
        "severity": "NIT",
        "file": SC_CL,
        "old": "    is the same file. The receive\n    loop now checks `application_state` before each `receive_text()`, after each one returns and when\n    the idle timeout fires.",
        "new": "    is the same file. The receive loop now checks `application_state` before each `receive_text()`,\n    after each one returns and when the idle timeout fires.",
        "why": "Reflows the short line the code lens's C3b leaves (\"is the same file. The receive\"); text unchanged.",
    },
]

# K2c: the gate line's count. Built here so the old text is the post-code-lens one (23 tests).
FIXES[[f["id"] for f in FIXES].index("K2c")] = {
    "id": "K2c",
    "severity": "MINOR",
    "file": REF,
    "old": "`tests/test_websocket_unsendable_late_frame_and_slot.py` (23 tests, the same in-memory peer",
    "new": "`tests/test_websocket_unsendable_late_frame_and_slot.py` (28 tests, the same in-memory peer",
    "why": "As K2a (the \"Gaps beside the drop\" gate line).",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--extra-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    texts: dict[str, str] = {}
    bad = 0
    for fix in FIXES:
        rel = fix["file"]
        if rel not in texts:
            path = args.work / rel
            if not path.is_file():
                path = args.extra_root / rel
            texts[rel] = path.read_text(encoding="utf-8")
        n = texts[rel].count(fix["old"])
        if n == 1:
            texts[rel] = texts[rel].replace(fix["old"], fix["new"], 1)
            verdict = "OK"
        else:
            verdict = "MISSING" if n == 0 else f"AMBIGUOUS({n})"
            bad += 1
        print(f"{verdict:<12} {fix['id']:<5} {fix['severity']:<6} {rel}")
    if bad:
        print(f"{bad} fix(es) do not apply; nothing written", file=sys.stderr)
        return 1
    args.out.write_text(json.dumps(FIXES, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(FIXES)} fixes to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
