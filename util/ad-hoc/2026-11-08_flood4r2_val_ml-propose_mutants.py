#!/usr/bin/env python3
"""The validator's OWN one-line mutants of the ml-propose carrier's new propose.py code, run against its tests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; the ml-propose carrier (util/release_train/propose.py step 5b-v)

Distinct from the builder's 26 mutants: at least two per new site helper, plus the composer, the pin reader, the
checklist and the build_proposal wiring. For each mutant the script replaces ONE exact substring (it must occur
exactly once) in ``<worktree>/util/release_train/propose.py``, deletes every ``__pycache__`` under util/ and tests/,
runs the whole ``tests/test_release_train_propose.py`` suite in a child interpreter, records killed / survived
and the failing test names, and restores the file byte-for-byte (sha256 checked after every mutant and at the end).
A control run on the unmutated file must pass first.

Run it ONLY against the validator's own worktree (``--worktree``); it writes propose.py there and restores it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
from pathlib import Path

TARGET = "util/release_train/propose.py"
SUITE = "tests/test_release_train_propose.py"

MUTANTS = [
    # set_reference_version_cell
    ("VM1", "set_reference_version_cell: an already-current cell reports old=None", "    if old == new_version:\n        return text, old\n    raw[2] = _fit_cell", "    if old == new_version:\n        return text, None\n    raw[2] = _fit_cell"),
    ("VM2", "set_reference_version_cell: the cell loses its width", '    raw[2] = _fit_cell(raw[2], f"`{new_version}`")', '    raw[2] = f" `{new_version}` "'),
    ("VM3", "set_reference_version_cell: a cell with extra text is a candidate (fullmatch -> search)", '        m = re.fullmatch(r"`([^`]+)`", raw[2].strip())', '        m = re.search(r"`([^`]+)`", raw[2].strip())'),
    ("VM4", "set_reference_version_cell: the row's newline is dropped", '    lines[i] = "|".join(raw) + lines[i][len(_row_body(lines[i])) :]\n    return "".join(lines), old', '    lines[i] = "|".join(raw)\n    return "".join(lines), old'),
    # set_reference_declares_version
    ("DM1", "set_reference_declares_version: off-by-one splice", "    return text[: m.start(2)] + new_version + text[m.end(2) :], m.group(2)", "    return text[: m.start(2)] + new_version + text[m.end(2) - 1 :], m.group(2)"),
    ("DM2", "set_reference_declares_version: a doubled sentence edits the first", "    matches = list(_REFERENCE_DECLARES.finditer(text))", "    matches = list(_REFERENCE_DECLARES.finditer(text))[:1]"),
    ("DM3", "_REFERENCE_DECLARES: the sentence's period is optional", r"( declares the following pins\.)", r"( declares the following pins)"),
    # set_reference_recurrence_clause
    ("CM1", "set_reference_recurrence_clause: keeps the clause's old release", '    return text[: m.start()] + f"{new_version} sets them to {_join_backticked(pins)}" + text[m.end() :], old_pins', '    return text[: m.start()] + f"{m.group(1)} sets them to {_join_backticked(pins)}" + text[m.end() :], old_pins'),
    ("CM2", "set_reference_recurrence_clause: reports the NEW pins as the old ones", '    old_pins = re.findall(r"`([^`]+)`", m.group(2))', "    old_pins = list(pins)"),
    ("CM3", "_REFERENCE_SETS_THEM: no lookbehind (a version inside a longer number matches)", 'r"(?<![0-9.])(\\d+\\.\\d+\\.\\d+) sets them to ("', 'r"(\\d+\\.\\d+\\.\\d+) sets them to ("'),
    ("CM4", "set_reference_recurrence_clause: one unreadable pin among readable ones is written (any -> all)", "    if not pins or any(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):", "    if not pins or all(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):"),
    # set_reference_matrix_row
    ("RM1", "set_reference_matrix_row: reports edited but returns the original text", '        lines[i] = "|".join(raw) + lines[i][len(_row_body(lines[i])) :]\n        return "".join(lines), "edited"', '        return text, "edited"'),
    ("RM2", "set_reference_matrix_row: compares padded cells (every row 'moves')", "            if raw[k].strip() != value:", "            if raw[k] != value:"),
    ("RM3", "set_reference_matrix_row: the new row goes after the FIRST row", "    last = rows[-1] if rows else header_idx + 1", "    last = rows[0] if rows else header_idx + 1"),
    ("RM4", "set_reference_matrix_row: a non-N.N.x label no longer refuses", "        if lm is None or (int(lm.group(1)), int(lm.group(2))) >= new_key:", "        if lm is not None and (int(lm.group(1)), int(lm.group(2))) >= new_key:"),
    ("RM5", "set_reference_matrix_row: a row WIDER than the header is edited", "        if len(raw) != len(header) + 2:", "        if len(raw) < len(header) + 2:"),
    # composer, pin reader, checklist, wiring
    ("KM1", "apply_reference_compat_cochanges: the matrix is rendered over the ORIGINAL text", '    candidate, report["matrix_row"] = set_reference_matrix_row(new_text, version, specs)', '    candidate, report["matrix_row"] = set_reference_matrix_row(text, version, specs)'),
    ("KM2", "apply_reference_compat_cochanges: the clause status is always current", '    report["recurrence"] = _site_status(old_pins, candidate, new_text)', '    report["recurrence"] = _site_status(old_pins, candidate, candidate)'),
    ("PM1", "meta_reference_pins: the recurrence pins in reverse file order", '    recurrence = [req.strip() for req in extras.get("recurrence") or [] if isinstance(req, str)]', '    recurrence = [req.strip() for req in reversed(extras.get("recurrence") or []) if isinstance(req, str)]'),
    ("LM1", "_reference_compat_items: a sub-package bump flags every absent site REQUIRED", '(meta_bump and report.get(key) not in ("edited", "added", "current"))', '(True and report.get(key) not in ("edited", "added", "current"))'),
    ("WM1", "build_proposal: a phantom REFERENCE edit when nothing moved", "        if ref_text is not None and ref_new != ref_text:", "        if ref_text is not None:"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(root: Path) -> None:
    for base in (root / "util", root / "tests"):
        for cache in base.rglob("__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)


def run_suite(root: Path) -> dict:
    clear_pycache(root)
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", SUITE], cwd=str(root), capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    err = proc.stderr or ""
    failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", err, re.MULTILINE)))
    summary = [ln for ln in err.strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    kinds = sorted(set(re.findall(r"^(FAIL|ERROR): ", err, re.MULTILINE)))
    return {"rc": proc.returncode, "summary": summary, "failing": failing, "kinds": kinds}


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = Path(args.worktree)
    target = root / TARGET
    original = target.read_bytes()
    before = sha(target)
    results = {"sha256_before": before, "control": run_suite(root), "mutants": []}
    if results["control"]["rc"] != 0:
        print("control FAILED", results["control"])
        return 2
    try:
        for mid, desc, old, new in MUTANTS:
            text = original.decode("utf-8")
            n = text.count(old)
            if n != 1:
                results["mutants"].append({"id": mid, "desc": desc, "status": f"NOT APPLIED ({n} matches)"})
                continue
            target.write_text(text.replace(old, new), encoding="utf-8")
            r = run_suite(root)
            target.write_bytes(original)
            if sha(target) != before:
                raise SystemExit(f"restore failed after {mid}")
            status = "killed" if r["rc"] != 0 else "SURVIVED"
            results["mutants"].append({"id": mid, "desc": desc, "status": status, **r})
            print(mid, status, r["summary"], r["failing"][:6], flush=True)
    finally:
        target.write_bytes(original)
        clear_pycache(root)
    results["sha256_after"] = sha(target)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1)
    print("sha256 before", before, "after", results["sha256_after"], "identical", before == results["sha256_after"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
