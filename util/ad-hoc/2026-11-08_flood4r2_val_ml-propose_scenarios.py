#!/usr/bin/env python3
"""Validate the flood-4 round-2 "ml-propose" carrier's claims on the release shapes its own proof did not run.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (adversarial validation, claims/docs/conventions lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507 (Cursor draft: pin docs/REFERENCE.md's compatibility record to pyproject.toml);
         Overtoad ruling "Carry + extend propose.py"; util/release_train/propose.py step 5b-v (the carrier);
         util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py (the builder's proof, which
         covers patch, minor and an UNMERGEABLE hand recurrence raise)

Why this exists
---------------
Under #2507's ``ReferenceCompatibilityMatrixTest`` a hand floor raise that leaves REFERENCE alone is red, and
Regression Tests is a required check, so it cannot merge. The MERGEABLE hand raise must also rewrite REFERENCE:
the "sets them to" clause's pins (a [recurrence] floor) or the current series' row in place (a column floor),
still naming the published version. This script builds those mergeable shapes and then runs the carrier's
``build_proposal``, to see what the generated proposal and its co-change checklist say.

Scenarios, each on a fresh copy of ``--tree`` (the carrier's files on main) with #2507's test file installed:

* ``rec-raise-mergeable``: a hand PR raises ``juniper-recurrence`` by one patch with every lockstep surface AND
  the clause's pins (still "0.11.4 sets them to"); then the meta's next patch is proposed.
* ``col-raise-then-minor``: a hand PR raises ``juniper-data[api]`` to the next minor floor with every lockstep
  surface AND the 0.11.x row in place; then the meta's next minor is proposed.
* ``doc-tools-escape``: the juniper-doc-tools minor that escapes ``<0.2.0`` is proposed (its empty
  ``[Unreleased]`` gets one simulated ``Added`` bullet in the copy, or the CHANGELOG move refuses);
* ``doc-tools-escape-then-meta-minor``: on that same tree, the meta's next minor is proposed -- two generated
  proposals in a row, with no hand edit between them.

Simulation limit: ``_hand_raise`` uses propose.py's editors, whose inline-table editor does not match an
extras-marker pin (``juniper-data[api]``), so scenario 2's hand PR leaves AGENTS.md / README / QUICK_START
stale; read only #2507's class there, and note its fixture literal collides with ``apply_pin_pairs_exact``.

For each: #2507's class and the whole ``tests/test_pyproject_extras.py`` run after the hand PR and after the
proposal; the proposal's docs/REFERENCE.md checklist lines and the compatibility paragraph are recorded.
Nothing outside ``--sim-dir`` is written; ``--tree`` is only read.

Usage
-----
    python3 -B util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_scenarios.py --tree <carrier copy> \\
        --gate-file <#2507's tests/test_pyproject_extras.py> --sim-dir <scratch>/scen --out <scratch>/scen.json
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

_MARKER = ".flood4r2-val-ml-propose-scenarios"
GATE_CLASS = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest"


def _fresh(path: Path) -> None:
    if path.exists():
        if not (path / _MARKER).is_file():
            raise SystemExit(f"ERROR: {path} exists without {_MARKER}; refusing to wipe it")
        shutil.rmtree(path)
    path.mkdir(parents=True)
    (path / _MARKER).write_text("scratch of 2026-11-08_flood4r2_val_ml-propose_scenarios.py\n", encoding="utf-8")


def _copy(tree: Path, dest: Path, gate_file: Path) -> Path:
    shutil.copytree(tree, dest, symlinks=True, ignore=shutil.ignore_patterns(".git", "tmp", "__pycache__", "logs", "reports"))
    shutil.copyfile(gate_file, dest / "tests" / "test_pyproject_extras.py")
    return dest


def _run(tree: Path, target: str) -> dict:
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", target], cwd=tree, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    tail = [ln for ln in proc.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:", "Ran ", "OK", "FAILED", "AssertionError"))]
    return {"exit": proc.returncode, "summary": tail[-12:]}


def _paragraph(text: str) -> str:
    m = re.search(r"^`juniper-ml` \S+ declares the following pins\..*$", text, re.MULTILINE)
    return m.group(0) if m else "<no paragraph>"


def _rows(text: str) -> list:
    return [ln for ln in text.splitlines() if re.match(r"^\| \d+\.\d+\.x ", ln)]


def _hand_raise(pr, tree: Path, package: str, old_req: str, new_req: str) -> list:
    changed = []
    for rel in ("pyproject.toml", "tests/test_pyproject_extras.py"):
        path = tree / rel
        text = path.read_text(encoding="utf-8")
        new = pr.apply_pin_pairs_exact(text, [(old_req, new_req)])
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(rel)
    for rel, heading in pr._INLINE_EXTRAS_TABLES:
        path = tree / rel
        text = path.read_text(encoding="utf-8")
        new = pr.apply_pin_edits_agents_table(text, package, new_req, heading)
        if rel == pr._README_REL:
            new = pr.apply_pin_edits_reference_table(new, package, new_req, pr._README_COMPAT_HEADING)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(rel)
    path = tree / pr._REFERENCE_EXTRAS_REL
    text = path.read_text(encoding="utf-8")
    new = pr.apply_pin_edits_reference_table(text, package, new_req)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed.append(pr._REFERENCE_EXTRAS_REL + " (extras table)")
    return changed


def _propose(detect, pr, tree: Path, package: str, from_version: str, to_version: str, bump: str) -> dict:
    entries = detect.load_registry(None)
    entry = {e.pypi_name: e for e in entries}[package]
    no_siblings = tree.parent / "no-siblings"

    def read_file(e, filename):
        try:
            return (detect.base_dir_for(e, tree, no_siblings) / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    pkg = {"pypi_name": package, "repo": entry.repo, "released_version": from_version, "declared_version": from_version, "classification": pr.PROPOSABLE, "proposed_bump": bump, "proposed_version": to_version, "ship_evidence": [], "changelog_conflict": None}
    sources = pr.ProposeSources(read_file=read_file, list_open_prs=lambda repo: [])
    prop = pr.build_proposal(entry, pkg, sources, tree, no_siblings, entries, datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    if prop.skipped:
        return {"refused": prop.skipped_reason}
    for edit in prop.edits:
        target = (tree / edit.path).resolve()
        if tree.resolve() not in target.parents:
            return {"refused": f"{edit.path} resolves outside the copy"}
        target.write_text(edit.new_text, encoding="utf-8")
    return {"edits": [e.path for e in prop.edits], "reference_checklist": [i for i in prop.co_change_checklist if "docs/REFERENCE.md" in i]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--gate-file", required=True)
    ap.add_argument("--sim-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tree = Path(args.tree).resolve()
    gate_file = Path(args.gate_file).resolve()
    sim = Path(args.sim_dir).resolve()
    _fresh(sim)
    sys.path.insert(0, str(tree / "util" / "release_train"))
    import detect  # noqa: E402,PLC0415 - the carrier's own modules are the code under test
    import propose as pr  # noqa: E402,PLC0415

    live = (tree / "pyproject.toml").read_text(encoding="utf-8")
    version = tomllib.loads(live)["project"]["version"]
    major, minor, patch = (int(p) for p in version.split("."))
    results: dict = {"tree": str(tree), "from_version": version}

    # 1. a MERGEABLE hand [recurrence] raise (clause pins rewritten, published version kept), then a patch
    t = _copy(tree, sim / "rec-raise-mergeable", gate_file)
    m = re.search(r'"(juniper-recurrence>=(\d+)\.(\d+)\.(\d+)(,[^"]*)?)"', live)
    old_req, new_req = m.group(1), f"juniper-recurrence>={m.group(2)}.{m.group(3)}.{int(m.group(4)) + 1}{m.group(5) or ''}"
    changed = _hand_raise(pr, t, "juniper-recurrence", old_req, new_req)
    ref_path = t / "docs" / "REFERENCE.md"
    ref = ref_path.read_text(encoding="utf-8")
    _, _, recurrence = pr.meta_reference_pins((t / "pyproject.toml").read_text(encoding="utf-8"))
    ref_new, old_pins = pr.set_reference_recurrence_clause(ref, version, recurrence)
    ref_path.write_text(ref_new, encoding="utf-8")
    hand_gate = _run(t, GATE_CLASS)
    hand_suite = _run(t, "tests/test_pyproject_extras.py")
    out = _propose(detect, pr, t, "juniper-ml", version, f"{major}.{minor}.{patch + 1}", "patch")
    final = ref_path.read_text(encoding="utf-8")
    results["rec-raise-mergeable"] = {"raised": f"{old_req} -> {new_req}", "hand_changed": changed + ["docs/REFERENCE.md (clause pins, still naming " + version + ")"], "clause_before_hand": old_pins, "gate_after_hand": hand_gate, "suite_after_hand": hand_suite, "proposal": out, "gate_after_proposal": _run(t, GATE_CLASS), "paragraph_after_proposal": _paragraph(final)}

    # 2. a MERGEABLE hand column-floor raise (0.11.x row rewritten in place), then the next minor
    t = _copy(tree, sim / "col-raise-then-minor", gate_file)
    m = re.search(r'"(juniper-data\[api\]>=(\d+)\.(\d+)\.(\d+))"', live)
    old_req, new_req = m.group(1), f"juniper-data[api]>={m.group(2)}.{int(m.group(3)) + 1}.0"
    changed = _hand_raise(pr, t, "juniper-data", old_req, new_req)
    ref_path = t / "docs" / "REFERENCE.md"
    ref = ref_path.read_text(encoding="utf-8")
    rows_before = _rows(ref)
    _, specs, _ = pr.meta_reference_pins((t / "pyproject.toml").read_text(encoding="utf-8"))
    ref_new, status = pr.set_reference_matrix_row(ref, version, specs)
    ref_path.write_text(ref_new, encoding="utf-8")
    hand_gate = _run(t, GATE_CLASS)
    hand_suite = _run(t, "tests/test_pyproject_extras.py")
    out = _propose(detect, pr, t, "juniper-ml", version, f"{major}.{minor + 1}.0", "minor")
    final = ref_path.read_text(encoding="utf-8")
    results["col-raise-then-minor"] = {"raised": f"{old_req} -> {new_req}", "hand_changed": changed + [f"docs/REFERENCE.md (current row: {status})"], "rows_on_main": rows_before, "gate_after_hand": hand_gate, "suite_after_hand": hand_suite, "proposal": out, "gate_after_proposal": _run(t, GATE_CLASS), "rows_after_proposal": _rows(final), "paragraph_after_proposal": _paragraph(final)}

    # 3. the juniper-doc-tools minor that escapes the <0.2.0 ceiling
    t = _copy(tree, sim / "doc-tools-escape", gate_file)
    clog = t / "juniper-doc-tools" / "CHANGELOG.md"
    clog_text = clog.read_text(encoding="utf-8")
    if "## [Unreleased]\n\n## [" in clog_text:  # an empty [Unreleased] refuses the move: give it one Added entry
        clog.write_text(clog_text.replace("## [Unreleased]\n\n## [", "## [Unreleased]\n\n### Added\n\n- A simulated feature (validation scratch only).\n\n## [", 1), encoding="utf-8")
    dt = tomllib.loads((t / "juniper-doc-tools" / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    dmaj, dmin, _ = (int(p) for p in dt.split("."))
    out = _propose(detect, pr, t, "juniper-doc-tools", dt, f"{dmaj}.{dmin + 1}.0", "minor")
    final = (t / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    results["doc-tools-escape"] = {"from": dt, "proposal": out, "gate_after_proposal": _run(t, GATE_CLASS), "suite_after_proposal": _run(t, "tests/test_pyproject_extras.py"), "rows_after_proposal": _rows(final), "paragraph_after_proposal": _paragraph(final)}

    # 4. ... and then the meta's next minor, on the same tree: two GENERATED proposals in a row, no hand edit
    out = _propose(detect, pr, t, "juniper-ml", version, f"{major}.{minor + 1}.0", "minor")
    final = (t / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    results["doc-tools-escape-then-meta-minor"] = {"proposal": out, "gate_after_proposal": _run(t, GATE_CLASS), "rows_after_proposal": _rows(final), "paragraph_after_proposal": _paragraph(final)}

    Path(args.out).write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    for name in ("rec-raise-mergeable", "col-raise-then-minor", "doc-tools-escape", "doc-tools-escape-then-meta-minor"):
        r = results[name]
        print(f"{name}: hand gate={r.get('gate_after_hand', {}).get('exit', '-')} proposal gate={r['gate_after_proposal']['exit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
