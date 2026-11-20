#!/usr/bin/env python3
"""Mutation-check the flood-4 round-2 "ml-propose" carrier: every new propose.py helper must be killed by its tests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; Overtoad ruling "Carry + extend propose.py"; util/release_train/propose.py step 5b-v;
         util/ad-hoc/2026-11-07_flood4_ml_tests_mutation_check.py (round 1's helper, which this adapts);
         auto-memory reference_mutation_check_stale_pyc_and_piped_exit.md

For each one-line mutant in ``MUTANTS`` (``helper``, ``old``, ``new``) of ``util/release_train/propose.py``:

1. the selection is the carrier's own tests -- the two new classes and the two existing tests whose assertions the
   carrier changed or added -- so a kill is credited to them, not to the rest of the suite;
2. the selection must pass on the real code first (``python3 -B -m unittest``, rc 0);
3. ``old`` must occur exactly once in propose.py; it is replaced by ``new``, the ``__pycache__`` next to propose.py
   and next to the tests is deleted, and the selection re-runs in a fresh process: rc 1 = killed, rc 0 = survived;
4. propose.py is restored byte for byte, and its sha256 is compared with the original (a mismatch aborts the run).

Writes ``<out-dir>/mutation_results.json`` and one log per mutant. Exit 0 when every mutant is killed.

Revised 2026-11-09 after round-2 validation: L1 follows the REVIEW gate's new form (``meta_bump or done``); CM4,
RM5, VM3, DM3 and LM1 are the code-lens validator's survivors (util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_mutants.py),
now killed by the tests that round added; L3-L9 cover the round-2 checklist code (the REVIEW gate, the previous-row
note, the renamed-clause note, the release it names, and the "included" line's wording).

Usage: python3 util/ad-hoc/2026-11-08_flood4r2_ml-propose_mutation_check.py <out-dir>   (run from the worktree root)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "util" / "release_train" / "propose.py"
TESTS = ROOT / "tests" / "test_release_train_propose.py"
SELECTION = (
    "tests.test_release_train_propose.ReferenceCompatHelperTest",
    "tests.test_release_train_propose.BuildProposalReferenceCompatTest",
    "tests.test_release_train_propose.BuildProposalConsumerPinTest.test_meta_self_bump_moves_the_readme_compat_lead_in",
    "tests.test_release_train_propose.BuildProposalConsumerPinTest.test_escaping_minor_bump_emits_all_three_cochanges",
)

#: (id, helper, old, new): ``old`` must occur exactly once in propose.py.
MUTANTS = (
    ("V1", "set_reference_version_cell", "    if len(hits) != 1:\n        return text, None\n    i, raw, old = hits[0]", "    if len(hits) < 1:\n        return text, None\n    i, raw, old = hits[0]"),
    ("V2", "set_reference_version_cell", '        if len(raw) < 4 or raw[1].strip() != "**Version**":', "        if len(raw) < 4:"),
    ("V3", "set_reference_version_cell", '    for i, line in enumerate(lines):\n        if not line.startswith("|"):\n            continue\n        raw = _row_body(line).split("|")', '    for i, line in enumerate(lines):\n        if not line.lstrip().startswith("|"):\n            continue\n        raw = _row_body(line).split("|")'),
    ("D1", "set_reference_declares_version", "    matches = list(_REFERENCE_DECLARES.finditer(text))\n    if len(matches) != 1:", "    matches = list(_REFERENCE_DECLARES.finditer(text))\n    if len(matches) < 1:"),
    ("D2", "set_reference_declares_version", "    return text[: m.start(2)] + new_version + text[m.end(2) :], m.group(2)", "    return text[: m.start(2)] + new_version + text[m.end(2) :], None"),
    ("C1", "set_reference_recurrence_clause", "    if not pins or any(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):", "    if not pins:"),
    ("C2", "set_reference_recurrence_clause", "    matches = list(_REFERENCE_SETS_THEM.finditer(text))\n    if len(matches) != 1:", "    matches = list(_REFERENCE_SETS_THEM.finditer(text))\n    if len(matches) < 1:"),
    ("C3", "set_reference_recurrence_clause (_join_backticked)", '    return quoted[0] if len(quoted) == 1 else ", ".join(quoted[:-1]) + " and " + quoted[-1]', '    return quoted[0] if len(quoted) == 1 else ", ".join(quoted)'),
    ("R1", "set_reference_matrix_row", '    lines.insert(last + 1, "|"', '    lines.insert(last, "|"'),
    ("R2", "set_reference_matrix_row", "    if len(labelled) > 1:", "    if len(labelled) > 2:"),
    ("R3", "set_reference_matrix_row", "        for k, value in enumerate(values, start=2):", "        for k, value in enumerate(values, start=1):"),
    ("R4", "set_reference_matrix_row", "    if series is None or any(value is None for value in values):", "    if series is None:"),
    ("R5", "set_reference_matrix_row", "        if lm is None or (int(lm.group(1)), int(lm.group(2))) >= new_key:", "        if lm is None:"),
    ("R6", "set_reference_matrix_row (_reference_matrix)", '            return None  # the next heading closed the section before any matrix', "            continue  # mutant: a later section's table counts"),
    ("R7", "set_reference_matrix_row (_reference_matrix)", '            if not sep.startswith("|") or set(_row_body(sep).replace("|", "").strip()) - set("-: ") or "-" not in sep:', '            if not sep.startswith("|"):'),
    ("R8", "set_reference_matrix_row (_fit_cell)", '    rendered = f" {content} "', '    rendered = f" {content}"'),
    ("P1", "meta_reference_pins", '        if extra_name == "all":\n            continue\n        for req in reqs or []:\n            m = _META_REQ_SPEC', '        if extra_name == "al":\n            continue\n        for req in reqs or []:\n            m = _META_REQ_SPEC'),
    ("P2", "meta_reference_pins", "            specs[pkg] = spec if specs.get(pkg, spec) == spec else None", "            specs[pkg] = spec"),
    ("P3", "meta_reference_pins (_META_REQ_SPEC)", '_META_REQ_SPEC = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\\[[^\\]]*\\])?(?P<spec>[<>=!~].*)$")', '_META_REQ_SPEC = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?P<spec>[<>=!~].*)$")'),
    ("K1", "apply_reference_compat_cochanges", '    report["recurrence_moved"] = old_pins is not None and set(old_pins) != set(recurrence)', '    report["recurrence_moved"] = old_pins is not None and set(old_pins) == set(recurrence)'),
    ("K2", "apply_reference_compat_cochanges", '        report["moved"] = [f"{pkg}: {cell} -> {after.get(pkg)}" for pkg, cell in before.items() if cell != after.get(pkg)]', '        report["moved"] = [f"{pkg}: {cell} -> {after.get(pkg)}" for pkg, cell in before.items() if cell == after.get(pkg)]'),
    ("L1", "_reference_compat_items", "    if meta_bump or done:\n        notes = [", "    if meta_bump:\n        notes = ["),
    ("L2", "_reference_compat_items", '(meta_bump and report.get(key) not in ("edited", "added", "current"))', '(meta_bump and report.get(key) not in ("edited", "added", "current", "absent"))'),
    ("W1", "build_proposal step 5b-v", '        final_root = next((e.new_text for e in reversed(prop.edits) if e.path == "pyproject.toml"), root_pyproject)', "        final_root = root_pyproject"),
    ("W2", "build_proposal step 5b-v", "        elif entry.pypi_name == notes_render.META_PACKAGE:\n            reference_compat = _reference_compat_report(unreadable=True)", '        elif entry.pypi_name == "never":\n            reference_compat = _reference_compat_report(unreadable=True)'),
    ("W3", "build_proposal step 5b-ii (REFERENCE composed once)", "                    ref_new = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)", "                    _ = apply_pin_edits_reference_table(ref_new, entry.pypi_name, cochanges[0].new_req)"),
    # Round 2 (2026-11-09): the code-lens validator's survivors, then the round-2 checklist code.
    ("CM4", "set_reference_recurrence_clause (one unreadable pin among readable ones)", "    if not pins or any(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):", "    if not pins or all(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):"),
    ("RM5", "set_reference_matrix_row (a series row wider than the header)", "        if len(raw) != len(header) + 2:", "        if len(raw) < len(header) + 2:"),
    ("VM3", "set_reference_version_cell (a cell holding more than the version)", '        m = re.fullmatch(r"`([^`]+)`", raw[2].strip())', '        m = re.search(r"`([^`]+)`", raw[2].strip())'),
    ("DM3", "set_reference_declares_version (_REFERENCE_DECLARES: the sentence's period)", r"( declares the following pins\.)", r"( declares the following pins)"),
    ("LM1", "_reference_compat_items (a sub-package bump owes no release site)", '(meta_bump and report.get(key) not in ("edited", "added", "current"))', '(True and report.get(key) not in ("edited", "added", "current"))'),
    ("L3", "_reference_compat_items (REVIEW whenever a site moved, code F7)", "    if meta_bump or done:\n        notes = [", '    if meta_bump or report.get("matrix_row") == "edited":\n        notes = ['),
    ("L4", "_reference_compat_items (the previous-row note, code F1)", '        if report.get("matrix_row") == "added":\n            notes.append("the previous series', '        if report.get("matrix_row") == "never":\n            notes.append("the previous series'),
    ("L5", "_reference_compat_items (the previous-row note on every proposal)", '        if report.get("matrix_row") == "added":\n            notes.append("the previous series', '        if True:\n            notes.append("the previous series'),
    ("L6", "_reference_compat_items (the renamed-clause note, code F5)", '        if report.get("recurrence") == "edited":\n            named', '        if report.get("recurrence") == "never":\n            named'),
    ("L7", "_reference_compat_items (the renamed-clause note on every proposal)", '        if report.get("recurrence") == "edited":\n            named', "        if True:\n            named"),
    ("L8", "apply_reference_compat_cochanges (the release the clause note names)", '    report["version"] = version\n', '    report["version"] = None\n'),
    ("L9", "_reference_compat_items (the included line vouches for the older rows, code F1)", "(the older rows are not touched)", "(the older rows stay: they describe published releases)"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache() -> None:
    for cache in (TARGET.parent / "__pycache__", TESTS.parent / "__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def _run(log: Path, label: str) -> int:
    argv = [sys.executable, "-B", "-m", "unittest", *SELECTION]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False, timeout=900)  # nosec B603 - fixed argv
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"===== {label}: {' '.join(argv)}\nrc={proc.returncode}\n{proc.stdout[-4000:]}\n{proc.stderr[-8000:]}\n")
    return proc.returncode


def main() -> int:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    original = TARGET.read_bytes()
    original_sha = _sha(TARGET)
    results = []
    _clear_pycache()
    control_log = out / "mut_control.log"
    control_log.write_text("", encoding="utf-8")
    control_rc = _run(control_log, "control (unmutated)")
    print(f"control: rc {control_rc}")
    if control_rc != 0:
        print("ERROR: the selection does not pass on the real code", file=sys.stderr)
        return 2
    for mid, helper, old, new in MUTANTS:
        log = out / f"mut_{mid}.log"
        log.write_text("", encoding="utf-8")
        row = {"id": mid, "helper": helper, "file": "util/release_train/propose.py", "old": old, "new": new, "log": str(log)}
        count = original.count(old.encode())
        if count != 1:
            row["result"] = f"error: old string occurs {count} times"
            results.append(row)
            print(f"{mid} {helper}: {row['result']}")
            continue
        try:
            TARGET.write_bytes(original.replace(old.encode(), new.encode(), 1))
            _clear_pycache()
            rc = _run(log, f"mutant {mid}")
        finally:
            TARGET.write_bytes(original)
            _clear_pycache()
        restored = _sha(TARGET)
        row.update({"mutant_rc": rc, "sha256_before": original_sha, "sha256_after": restored, "restored": restored == original_sha})
        if restored != original_sha:
            print(f"RESTORE FAILED for {TARGET}", file=sys.stderr)
            results.append(row)
            break
        row["result"] = "killed" if rc == 1 else ("survived" if rc == 0 else f"error: mutant rc {rc}")
        results.append(row)
        print(f"{mid} {helper}: {row['result']}")
    with open(out / "mutation_results.json", "w", encoding="utf-8") as fh:
        json.dump({"control_rc": control_rc, "target_sha256": original_sha, "selection": SELECTION, "mutants": results}, fh, indent=2)
    return 0 if all(r.get("result") == "killed" for r in results) and len(results) == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
