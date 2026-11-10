#!/usr/bin/env python3
"""
Append the owner's 2026-10-30 correction row to the experiments index: run ``20261003T091414Z-4ba6`` is ``failed``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — one owner-ruled correction to ``~/.local/state/juniper-experiments/index.jsonl``
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0.md
         (item 2, "the index.jsonl correction row ... Ask the owner"); notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md
         (v1.7.23 :711 / :972 record row 482, and :712 leaves `failed` vs `degraded` to the owner)

Why this exists
---------------
Row 477 of the index records run ``20261003T091414Z-4ba6`` (E-H cell ``c001-0d8782ae``) as ``succeeded``, which was false:
its crossval failed with HTTP 422 because the artifact lacked ``X_full`` (F-E1). On 2026-10-26 the owner ruled that a
correction row be appended and the original kept; the session that appended it (row 482) recorded ``degraded``, the outcome
today's ``util/experiments/run_experiment.py`` assigns when train and predict succeed and crossval fails, where the owner's
option named ``failed``. On 2026-10-30 the owner ruled: append one more correction row, correcting row 482, with outcome
``failed``. Rows 477 and 482 are never rewritten. The index is append-only; no reader in ``util/experiments/`` interprets
``corrects`` (they are annotations for a human or a later tool), so this row changes no aggregate.

What it does
------------
Checks the preconditions, then appends exactly one line with a single ``O_APPEND`` write, and re-reads the file:

* line 477 is run ``20261003T091414Z-4ba6`` with outcome ``succeeded``;
* line 482 is the same run with outcome ``degraded`` and ``corrects == {"line": 477, "outcome": "succeeded"}``;
* no row already corrects line 482 (a second run reports "already applied" and exits 0, appending nothing);
* after the append, the file has one more line, and its last line parses back to the row written.

``--check`` appends nothing: it exits 0 when exactly one row corrects line 482 with outcome ``failed``, else 1.
``--index PATH`` points it at a copy, for testing.

    python3 -I util/ad-hoc/2026-10-30_index_correction_row_failed.py            # append (once)
    python3 -I util/ad-hoc/2026-10-30_index_correction_row_failed.py --check    # verify

Exit status: 0 appended, already applied, or ``--check`` passed; 1 a precondition or ``--check`` failed (nothing
appended); 2 any other error.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sys

DEFAULT_INDEX = pathlib.Path.home() / ".local" / "state" / "juniper-experiments" / "index.jsonl"
RUN_ID = "20261003T091414Z-4ba6"
SUITE_ID = "e-h-recurrence-real-data-20261003T091356Z"
CELL_ID = "c001-0d8782ae"
ORIGINAL_LINE = 477
CORRECTED_LINE = 482
SESSION = "recurrence-equities-mnist-schema-probe-canopy-778-parent-agents-cascor-0-13-0"


class PreconditionError(Exception):
    """A precondition failed: nothing was appended."""


def read_rows(index: pathlib.Path) -> list[dict]:
    rows = []
    with index.open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise PreconditionError(f"line {lineno} is not JSON: {exc}") from exc
    return rows


def row_at(rows: list[dict], lineno: int) -> dict:
    if len(rows) < lineno:
        raise PreconditionError(f"the index has {len(rows)} lines; line {lineno} does not exist")
    return rows[lineno - 1]


def corrections_of(rows: list[dict], lineno: int) -> list[tuple[int, dict]]:
    return [(i, row) for i, row in enumerate(rows, 1) if isinstance(row.get("corrects"), dict) and row["corrects"].get("line") == lineno]


def check_base(rows: list[dict]) -> None:
    original = row_at(rows, ORIGINAL_LINE)
    if original.get("run_id") != RUN_ID or original.get("outcome") != "succeeded":
        raise PreconditionError(f"line {ORIGINAL_LINE} is not run {RUN_ID} / succeeded: {original!r}")
    corrected = row_at(rows, CORRECTED_LINE)
    if corrected.get("run_id") != RUN_ID or corrected.get("outcome") != "degraded":
        raise PreconditionError(f"line {CORRECTED_LINE} is not run {RUN_ID} / degraded: {corrected!r}")
    if corrected.get("corrects") != {"line": ORIGINAL_LINE, "outcome": "succeeded"}:
        raise PreconditionError(f"line {CORRECTED_LINE} does not correct line {ORIGINAL_LINE}: {corrected.get('corrects')!r}")


def build_row(run_dir: str) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "suite_id": SUITE_ID,
        "cell_id": CELL_ID,
        "run_id": RUN_ID,
        "outcome": "failed",
        "run_dir": run_dir,
        "corrects": {"line": CORRECTED_LINE, "outcome": "degraded"},
        "reason": (
            "The owner's 2026-10-26 option named failed; row 482 recorded degraded, the outcome today's run_experiment.py "
            "assigns when train and predict succeed and crossval fails (here HTTP 422: the NPZ artifact lacks the required "
            "key 'X_full', F-E1). The owner ruled on 2026-10-30 that failed stands. Rows 477 and 482 stay as written."
        ),
        "corrected_at": now,
        "corrected_by": f"owner ruling 2026-10-30 (session {SESSION}): append a correction row with outcome failed; never rewrite rows 477 or 482",
    }


def do_check(rows: list[dict]) -> int:
    check_base(rows)
    hits = corrections_of(rows, CORRECTED_LINE)
    failed = [(i, row) for i, row in hits if row.get("run_id") == RUN_ID and row.get("outcome") == "failed"]
    if len(hits) == 1 and len(failed) == 1:
        print(f"PASS: line {failed[0][0]} corrects line {CORRECTED_LINE} with outcome failed (corrected_at {failed[0][1].get('corrected_at')})")
        return 0
    print(f"FAIL: {len(hits)} row(s) correct line {CORRECTED_LINE}, {len(failed)} of them run {RUN_ID} / failed")
    return 1


def do_append(index: pathlib.Path, rows: list[dict]) -> int:
    check_base(rows)
    hits = corrections_of(rows, CORRECTED_LINE)
    if hits:
        if len(hits) == 1 and hits[0][1].get("outcome") == "failed":
            print(f"already applied: line {hits[0][0]} corrects line {CORRECTED_LINE} with outcome failed; appended nothing")
            return 0
        raise PreconditionError(f"line(s) {[i for i, _ in hits]} already correct line {CORRECTED_LINE}, not as this ruling says")
    row = build_row(row_at(rows, CORRECTED_LINE)["run_dir"])
    payload = (json.dumps(row) + "\n").encode("utf-8")
    with index.open("rb") as handle:
        size = handle.seek(0, os.SEEK_END)
        if size:
            handle.seek(size - 1)
            if handle.read(1) != b"\n":
                raise PreconditionError("the index does not end with a newline; refusing to append onto a partial line")
    fd = os.open(index, os.O_WRONLY | os.O_APPEND)
    try:
        written = os.write(fd, payload)
    finally:
        os.close(fd)
    if written != len(payload):
        print(f"ERROR: short write: {written} of {len(payload)} bytes", file=sys.stderr)
        return 2
    after = read_rows(index)
    position = next((i for i, r in enumerate(after, 1) if r == row), None)
    if position is None:
        print("ERROR: the appended row does not read back", file=sys.stderr)
        return 2
    print(f"appended line {position} of {len(after)} (was {len(rows)}): {json.dumps(row)}")
    if len(after) != len(rows) + 1:
        print(f"NOTE: the index grew by {len(after) - len(rows)} lines: another writer appended concurrently")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--index", type=pathlib.Path, default=DEFAULT_INDEX)
    parser.add_argument("--check", action="store_true", help="verify only; append nothing")
    args = parser.parse_args()
    try:
        rows = read_rows(args.index)
        return do_check(rows) if args.check else do_append(args.index, rows)
    except PreconditionError as exc:
        print(f"FAIL: {exc}; appended nothing")
        return 1
    except Exception as exc:  # noqa: BLE001 -- exit 2 on anything that is not a failed precondition
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
