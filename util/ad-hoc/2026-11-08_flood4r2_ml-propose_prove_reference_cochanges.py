#!/usr/bin/env python3
"""Show that juniper-ml#2507's tests fail on an unextended propose.py's proposals and pass on the extended one's.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507 (Cursor draft: pin docs/REFERENCE.md's compatibility record to pyproject.toml);
         Overtoad ruling "Carry + extend propose.py"; util/release_train/propose.py (step 5b-v);
         util/ad-hoc/2026-10-21_simulate_release_proposal.py (the simulator this adapts)

Why this exists
---------------
#2507 adds ``ReferenceCompatibilityMatrixTest`` to ``tests/test_pyproject_extras.py``. It pins four
docs/REFERENCE.md sites to ``pyproject.toml``: the Package Overview Version cell, the "`juniper-ml` X.Y.Z
declares the following pins" sentence, the current series' matrix row, and the [recurrence] "sets them to"
clause. ``util/release_train/propose.py`` on ``main`` edits none of them, so with those tests carried every
juniper-ml release proposal would fail CI until someone edited REFERENCE by hand. The Overtoad ruled that the
generator be extended. This script is the evidence for that ruling, in both directions.

It materializes ``--base-ref`` with ``git archive`` into two trees:

* UNEXTENDED: the base as it is;
* EXTENDED: the base with each ``--carrier-file`` copied over from ``--carrier-root`` (the carrier's tree).

Both get #2507's ``tests/test_pyproject_extras.py``, the head blob of ``--gate-ref``. The script refuses unless
the base's copy of that file equals the copy at the merge base of the two refs, so the blob is exactly the base
plus the draft's own hunks. Nothing from #2507 is carried; it is only run.

Four scenarios, each on a fresh copy of each tree:

* ``patch``: the meta-package's next patch (0.11.4 -> 0.11.5 on the 2026-11-08 base);
* ``minor``: its next minor (-> 0.12.0), the first proposal of a new series;
* ``recurrence-raise``: a hand PR raises the ``juniper-recurrence`` floor by one patch, with its lockstep
  surfaces (pyproject, the EXPECTED_EXTRAS membership, the four extras tables and README's compatibility row,
  moved with propose.py's own editors, as juniper-ml#2473 did), and then the next patch is proposed. The
  recurrence pins have no matrix column, so the clause is their only record in REFERENCE. #2507's tests refuse
  this raise on its own (its "before" state fails them), so no green merge reaches it;
* ``recurrence-raise-mergeable`` (added 2026-11-09, after round-2 validation): the same raise, which also moves
  the pin inside REFERENCE's "sets them to" clause and nowhere else in the paragraph. That is the floor raise
  #2507's tests let merge, so its "before" state must pass them.

For each, the copy's OWN ``propose.build_proposal`` builds the proposal in a child process (so the two modules
never share an interpreter), the proposal's edits are written into the copy, and the suites run before and
after: #2507's test class verbosely (each test's result is recorded), then every suite in ``SUITES`` one
process each. ``--repo-root``-style safety: nothing outside ``--sim-dir`` and ``--log-dir`` is written, and
``--sim-dir`` must be new or carry this script's marker.

Usage
-----
    python3 util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py \\
        --base-ref origin/main --gate-ref refs/flood4r2/pr/2507 --carrier-root . \\
        --carrier-file util/release_train/propose.py --carrier-file tests/test_release_train_propose.py \\
        --sim-dir tmp/flood4r2/ml-propose/sim --log-dir tmp/flood4r2/ml-propose/logs

Exit codes: 0 when every expectation holds (after each proposal #2507's class fails on UNEXTENDED and passes on
EXTENDED, and no suite that passed before an EXTENDED proposal fails after it); 1 when one does not; 2 on an
invocation error.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv (git, this interpreter), no shell
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

_MARKER = ".flood4r2-prove-reference-sim"
GATE_FILE = "tests/test_pyproject_extras.py"
GATE_CLASS = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest"
#: util/ad-hoc/2026-10-21_simulate_release_proposal.py's DEFAULT_SUITES, plus propose.py's own suite.
SUITES = (
    "tests/test_pyproject_extras.py",
    "tests/test_agents_md_version_drift.py",
    "tests/test_agents_md_header_schema.py",
    "tests/test_agents_md_touch_up.py",
    "tests/test_service_core_drift.py",
    "tests/test_model_core_drift.py",
    "tests/test_doc_tools_drift.py",
    "tests/test_ci_tools_drift.py",
    "tests/test_template_library_drift.py",
    "tests/test_coverage_gap_mapper_drift.py",
    "tests/test_env_floor_drift_check.py",
    "tests/test_env_drift_check_drift.py",
    "tests/test_editable_install_drift_check.py",
    "tests/test_publish_testpypi_verify.py",
    "tests/test_release_train_registry.py",
    "tests/test_release_train_workflow_guard.py",
    "tests/test_global_text_search.py",
    "tests/test_release_train_propose.py",
)
# ``unittest -v`` prints each test's name line, then -- for a test with a docstring -- the docstring's first line, and
# only then "... ok". So every name is read from its own line, and a failure from the FAIL:/ERROR: header.
_GATE_NAME = re.compile(r"^(test_\w+) \(tests\.test_pyproject_extras\.ReferenceCompatibilityMatrixTest\.\1\)")
_GATE_FAILED = re.compile(r"^(FAIL|ERROR): (test_\w+) \(")
_GATE_RAN = re.compile(r"^Ran (\d+) tests? in ")
# REFERENCE's "X.Y.Z sets them to `pin`, `pin` and `pin`" clause, read here rather than through propose.py so the
# hand raise is the same edit in both trees.
_CLAUSE = re.compile(r"\d+\.\d+\.\d+ sets them to (?:`[^`]+`(?:, | and )?)+")


def _git(root: Path, *args: str, binary: bool = False):
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)  # nosec B603,B607 - fixed argv
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: git {' '.join(args)} failed: {proc.stderr.decode(errors='replace').strip()}")
    return proc.stdout if binary else proc.stdout.decode("utf-8").strip()


def _fresh(path: Path) -> None:
    if path.exists():
        if not (path / _MARKER).is_file():
            raise SystemExit(f"ERROR: {path} exists and has no {_MARKER} marker -- refusing to wipe it")
        shutil.rmtree(path)
    path.mkdir(parents=True)
    (path / _MARKER).write_text("scratch tree of util/ad-hoc/2026-11-08_flood4r2_ml-propose_prove_reference_cochanges.py\n", encoding="utf-8")


def _import_release_train(tree: Path):
    sys.path.insert(0, str(tree / "util" / "release_train"))
    import detect  # noqa: E402,PLC0415 - the tree's own release-train modules are the code under test
    import propose  # noqa: E402,PLC0415

    return detect, propose


def _child_raise(tree: Path, package: str, old_req: str, new_req: str, rewrite_clause: bool = False) -> int:
    """The hand floor raise, with every lockstep surface tests/test_pyproject_extras.py holds the pin to.

    ``rewrite_clause`` also moves the pin inside REFERENCE's "sets them to" clause (only there): the raise
    ReferenceCompatibilityMatrixTest lets merge, since the clause must name pyproject's [recurrence] pins."""
    _, propose = _import_release_train(tree)
    changed = []
    for rel in ("pyproject.toml", "tests/test_pyproject_extras.py"):
        path = tree / rel
        text = path.read_text(encoding="utf-8")
        new = propose.apply_pin_pairs_exact(text, [(old_req, new_req)])
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(rel)
    for rel, heading in propose._INLINE_EXTRAS_TABLES:
        path = tree / rel
        text = path.read_text(encoding="utf-8")
        new = propose.apply_pin_edits_agents_table(text, package, new_req, heading)
        if rel == propose._README_REL:
            new = propose.apply_pin_edits_reference_table(new, package, new_req, propose._README_COMPAT_HEADING)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(rel)
    path = tree / propose._REFERENCE_EXTRAS_REL
    text = path.read_text(encoding="utf-8")
    new = propose.apply_pin_edits_reference_table(text, package, new_req)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed.append(propose._REFERENCE_EXTRAS_REL)
    if rewrite_clause:
        text = path.read_text(encoding="utf-8")
        clauses = list(_CLAUSE.finditer(text))
        needle = f"`{old_req}`"
        if len(clauses) != 1 or text.count(needle, clauses[0].start(), clauses[0].end()) != 1:
            print(json.dumps({"refused": f"expected one 'sets them to' clause naming {needle} once"}))
            return 2
        m = clauses[0]
        path.write_text(text[: m.start()] + m.group(0).replace(needle, f"`{new_req}`") + text[m.end() :], encoding="utf-8")
        changed.append(f"{propose._REFERENCE_EXTRAS_REL} (the 'sets them to' clause)")
    print(json.dumps({"raised": f"{old_req} -> {new_req}", "changed": changed}))
    return 0


def _child_propose(tree: Path, package: str, from_version: str, to_version: str, bump: str) -> int:
    detect, propose = _import_release_train(tree)
    entries = detect.load_registry(None)
    entry = {e.pypi_name: e for e in entries}[package]
    no_siblings = tree.parent / "no-siblings"

    def read_file(e, filename):
        try:
            return (detect.base_dir_for(e, tree, no_siblings) / filename).read_text(encoding="utf-8")
        except OSError:
            return None

    pkg = {"pypi_name": package, "repo": entry.repo, "released_version": from_version, "declared_version": from_version, "classification": propose.PROPOSABLE, "proposed_bump": bump, "proposed_version": to_version, "ship_evidence": [], "changelog_conflict": None}
    sources = propose.ProposeSources(read_file=read_file, list_open_prs=lambda repo: [])
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    prop = propose.build_proposal(entry, pkg, sources, tree, no_siblings, entries, date)
    if prop.skipped:
        print(json.dumps({"refused": prop.skipped_reason}))
        return 2
    for edit in prop.edits:
        target = (tree / edit.path).resolve()
        if tree.resolve() not in target.parents:
            print(json.dumps({"refused": f"{edit.path} resolves outside the copy"}))
            return 2
        target.write_text(edit.new_text, encoding="utf-8")
    reference_items = [item for item in prop.co_change_checklist if "docs/REFERENCE.md" in item]
    print(json.dumps({"edits": [e.path for e in prop.edits], "reference_checklist": reference_items}))
    return 0


def _run_gate(tree: Path) -> dict:
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", GATE_CLASS], cwd=tree, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    results: dict = {}
    ran = None
    for line in (proc.stderr or "").splitlines():
        name = _GATE_NAME.match(line)
        failed = _GATE_FAILED.match(line)
        count = _GATE_RAN.match(line)
        if name:
            results.setdefault(name.group(1), "ok")
        if failed:
            results[failed.group(2)] = failed.group(1)
        if count:
            ran = int(count.group(1))
    complete = ran is not None and ran == len(results) and ran > 0
    return {"exit": proc.returncode, "passed": proc.returncode == 0 and complete, "ran": ran, "tests": results, "output": proc.stderr}


def _run_suites(tree: Path) -> dict:
    out = {}
    for suite in SUITES:
        if not (tree / suite).is_file():
            out[suite] = None
            continue
        proc = subprocess.run([sys.executable, "-B", "-m", "unittest", suite], cwd=tree, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
        out[suite] = proc.returncode == 0
    return out


def _child(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--package", required=True)
    ap.add_argument("--raise-from")
    ap.add_argument("--raise-to")
    ap.add_argument("--from-version")
    ap.add_argument("--to-version")
    ap.add_argument("--bump")
    ap.add_argument("--rewrite-clause", action="store_true")
    args = ap.parse_args(argv)
    tree = Path(args.tree).resolve()
    if args.raise_from:
        return _child_raise(tree, args.package, args.raise_from, args.raise_to, args.rewrite_clause)
    return _child_propose(tree, args.package, args.from_version, args.to_version, args.bump)


def _recurrence_raise(pyproject_text: str) -> tuple:
    """The base's ``juniper-recurrence`` pin and the same pin with its floor's patch raised by one."""
    m = re.search(r'"(juniper-recurrence>=(\d+)\.(\d+)\.(\d+)(,[^"]*)?)"', pyproject_text)
    if m is None:
        raise SystemExit("ERROR: the base pyproject.toml has no juniper-recurrence>=X.Y.Z pin")
    old = m.group(1)
    return old, f"juniper-recurrence>={m.group(2)}.{m.group(3)}.{int(m.group(4)) + 1}{m.group(5) or ''}"


def main() -> int:
    if sys.argv[1:2] == ["--child"]:
        return _child(sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-ref", required=True, help="the tree both variants start from (e.g. origin/main)")
    ap.add_argument("--gate-ref", required=True, help="the draft head carrying #2507's tests/test_pyproject_extras.py")
    ap.add_argument("--carrier-root", required=True, help="the carrier's checkout (the git repo the refs resolve in)")
    ap.add_argument("--git-root", help="the checkout git runs in (default: --carrier-root); any worktree of the same repository resolves the refs")
    ap.add_argument("--carrier-file", action="append", required=True, help="a carrier file copied into the EXTENDED tree (repeatable)")
    ap.add_argument("--sim-dir", required=True, help="scratch directory for the trees (wiped and rebuilt)")
    ap.add_argument("--log-dir", required=True, help="where the per-run logs and the JSON summary go")
    args = ap.parse_args()

    root = Path(args.carrier_root).resolve()
    git_root = Path(args.git_root).resolve() if args.git_root else root
    sim = Path(args.sim_dir).resolve()
    logs = Path(args.log_dir).resolve()
    logs.mkdir(parents=True, exist_ok=True)
    base_sha = _git(git_root, "rev-parse", args.base_ref)
    gate_sha = _git(git_root, "rev-parse", args.gate_ref)
    merge_base = _git(git_root, "merge-base", base_sha, gate_sha)
    base_blob = _git(git_root, "rev-parse", f"{base_sha}:{GATE_FILE}")
    fork_blob = _git(git_root, "rev-parse", f"{merge_base}:{GATE_FILE}")
    if base_blob != fork_blob:
        print(f"ERROR: {GATE_FILE} moved on the base since the draft forked ({fork_blob} -> {base_blob}); re-apply its own hunks instead", file=sys.stderr)
        return 2
    gate_text = _git(git_root, "show", f"{gate_sha}:{GATE_FILE}", binary=True)

    _fresh(sim)
    trees = {}
    archive = _git(git_root, "archive", "--format=tar", base_sha, binary=True)
    for variant in ("unextended", "extended"):
        tree = sim / variant
        tree.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(tree, filter="data")
        if variant == "extended":
            for rel in args.carrier_file:
                src = (root / rel).resolve()
                if root not in src.parents:
                    print(f"ERROR: --carrier-file {rel} resolves outside --carrier-root", file=sys.stderr)
                    return 2
                shutil.copyfile(src, tree / rel)
        (tree / GATE_FILE).write_bytes(gate_text)
        trees[variant] = tree

    import tomllib  # noqa: PLC0415

    pyproject = (trees["unextended"] / "pyproject.toml").read_text(encoding="utf-8")
    from_version = tomllib.loads(pyproject)["project"]["version"]
    major, minor, patch = (int(p) for p in from_version.split("."))
    raise_from, raise_to = _recurrence_raise(pyproject)
    # (to_version, bump, the hand raise or None, whether that raise also moves the clause's pin)
    scenarios = {
        "patch": (f"{major}.{minor}.{patch + 1}", "patch", None, False),
        "minor": (f"{major}.{minor + 1}.0", "minor", None, False),
        "recurrence-raise": (f"{major}.{minor}.{patch + 1}", "patch", (raise_from, raise_to), False),
        "recurrence-raise-mergeable": (f"{major}.{minor}.{patch + 1}", "patch", (raise_from, raise_to), True),
    }

    summary = {"base_ref": args.base_ref, "base_sha": base_sha, "gate_ref": args.gate_ref, "gate_sha": gate_sha, "gate_blob": _git(git_root, "rev-parse", f"{gate_sha}:{GATE_FILE}"), "merge_base": merge_base, "carrier_files": args.carrier_file, "from_version": from_version, "runs": {}}
    failures = []
    for scenario, (to_version, bump, raised, rewrite_clause) in scenarios.items():
        for variant in ("unextended", "extended"):
            name = f"{variant}-{scenario}"
            tree = sim / name
            shutil.copytree(trees[variant], tree, symlinks=True)
            log = [f"# {name}: juniper-ml {from_version} -> {to_version} [{bump}] on {base_sha} ({variant})"]
            if raised:
                proc = subprocess.run([sys.executable, "-B", __file__, "--child", "--tree", str(tree), "--package", "juniper-recurrence", "--raise-from", raised[0], "--raise-to", raised[1], *(["--rewrite-clause"] if rewrite_clause else [])], capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
                log += ["## hand floor raise", proc.stdout.strip(), proc.stderr.strip()]
                if proc.returncode != 0:
                    failures.append(f"{name}: the hand raise failed")
            before_gate = _run_gate(tree)
            before_suites = _run_suites(tree)
            proc = subprocess.run([sys.executable, "-B", __file__, "--child", "--tree", str(tree), "--package", "juniper-ml", "--from-version", from_version, "--to-version", to_version, "--bump", bump], capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
            log += ["## proposal (the tree's own propose.build_proposal)", proc.stdout.strip(), proc.stderr.strip()]
            if proc.returncode != 0:
                failures.append(f"{name}: the proposal was refused")
            after_gate = _run_gate(tree)
            after_suites = _run_suites(tree)
            regressed = sorted(s for s in SUITES if before_suites.get(s) and after_suites.get(s) is False)
            log += ["## #2507's class before the proposal", before_gate["output"], "## #2507's class after the proposal", after_gate["output"]]
            log += ["## suites (before -> after)"] + [f"{s}: {before_suites.get(s)} -> {after_suites.get(s)}" for s in SUITES]
            (logs / f"prove_{name}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
            summary["runs"][name] = {"to_version": to_version, "gate_ran": after_gate["ran"], "gate_before": before_gate["tests"], "gate_before_passed": before_gate["passed"], "gate_after": after_gate["tests"], "gate_after_passed": after_gate["passed"], "suites_before": before_suites, "suites_after": after_suites, "regressed": regressed}
            if after_gate["ran"] != len(after_gate["tests"]):
                failures.append(f"{name}: unittest ran {after_gate['ran']} of #2507's tests but {len(after_gate['tests'])} were recorded")
            want = variant == "extended"
            if after_gate["passed"] != want:
                failures.append(f"{name}: #2507's class {'passed' if after_gate['passed'] else 'failed'} after the proposal; expected it to {'pass' if want else 'fail'}")
            if variant == "extended" and regressed:
                failures.append(f"{name}: the proposal regressed {regressed}")
            if rewrite_clause and not before_gate["passed"]:
                failures.append(f"{name}: #2507's class failed BEFORE the proposal; the mergeable raise must leave it green")
            failing = sorted(t for t, r in after_gate["tests"].items() if r != "ok")
            print(f"{name:28s} #2507 ({after_gate['ran']} tests) before={'PASS' if before_gate['passed'] else 'FAIL'} after={'PASS' if after_gate['passed'] else 'FAIL'}  failing after: {failing or '-'}  regressed suites: {regressed or '-'}")
    summary["failures"] = failures
    (logs / "prove_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for failure in failures:
        print(f"UNEXPECTED: {failure}")
    print("every expectation holds" if not failures else f"{len(failures)} expectation(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
