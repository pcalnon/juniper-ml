#!/usr/bin/env python3
"""Independent before/after simulation of release proposals for the ml-propose carrier (validator's own scenarios).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507 (ReferenceCompatibilityMatrixTest); the ml-propose carrier (util/release_train/propose.py
         step 5b-v); juniper-ml#1991 (the series rule's precedent)

Written from scratch by the validator (the builder's prove script was not reused). For each scenario and each
variant ("main" = origin/main's propose.py; "carrier" = the carrier's four modified tracked files overlaid):

1. extract a subset of the base tree (``--tar``, a ``git archive`` of the base sha) into a fresh sandbox;
2. install #2507's tests/test_pyproject_extras.py (``--gate-file``, its head blob);
3. run the scenario's steps in order. A step is either a HAND edit (a Python function on the sandbox files) or a
   PROPOSAL (``build_proposal`` run in a child interpreter against the sandbox's OWN propose.py, the edits then
   written into the sandbox). After every step #2507's class is run test-by-test in a child interpreter, and the
   whole of test_pyproject_extras.py plus the AGENTS.md version / schema suites run as modules;
4. record each proposal's REFERENCE diff, its checklist lines that name docs/REFERENCE.md, and its edit paths.

Writes only under ``--out``. No git, no network.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv (this interpreter), no shell
import sys
import tarfile
import unittest
from pathlib import Path

GATE_CLASS = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest"
MODULE_SUITES = ("tests/test_pyproject_extras.py", "tests/test_agents_md_version_drift.py", "tests/test_agents_md_header_schema.py")
CARRIER_FILES = ("util/release_train/propose.py", "tests/test_release_train_propose.py", "docs/REFERENCE.md", "CHANGELOG.md")
SKIP_TOP = {"papers", "images", "resources", "reports", "prompts", "logs", "notes", "tmp", "juniper-ci-tools/tests", "juniper-doc-tools/tests"}
REF = "docs/REFERENCE.md"


# ── child modes ─────────────────────────────────────────────────────────────


def child_build(sandbox: Path, package: str, from_v: str, to_v: str, bump: str, date: str, out_json: Path) -> int:
    sys.path.insert(0, str(sandbox / "util" / "release_train"))
    import detect  # noqa: PLC0415 - imported from the sandbox on purpose
    import propose  # noqa: PLC0415

    entries = detect.load_registry(None)
    entry = {e.pypi_name: e for e in entries}[package]

    def read_file(ent, filename):
        target = detect.base_dir_for(ent, sandbox, sandbox.parent) / filename
        try:
            return target.read_text(encoding="utf-8")
        except OSError:
            return None

    sources = propose.ProposeSources(read_file=read_file, list_open_prs=lambda repo: [])
    pkg = {"pypi_name": package, "repo": entry.repo, "classification": "UNRELEASED_CHANGES", "released_version": from_v, "declared_version": from_v, "proposed_bump": bump, "proposed_version": to_v, "ship_evidence": []}
    prop = propose.build_proposal(entry, pkg, sources, sandbox, sandbox.parent, entries, date)
    paths = [e.path for e in prop.edits]
    ref_diff = ""
    for e in prop.edits:
        if e.path == REF:
            ref_diff = e.unified_diff()
        (sandbox / e.path).write_text(e.new_text, encoding="utf-8")
    payload = {
        "skipped_reason": prop.skipped_reason,
        "edit_paths": paths,
        "duplicate_paths": sorted({p for p in paths if paths.count(p) > 1}),
        "checklist": list(prop.co_change_checklist),
        "reference_checklist": [item for item in prop.co_change_checklist if "docs/REFERENCE.md" in item],
        "reference_diff": ref_diff,
        "pr_body_lists_reference": f"- `{REF}`" in (prop.pr_body or ""),
        "edits": {e.path: {"old": e.old_text, "new": e.new_text} for e in prop.edits},
    }
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
    return 0


def child_gate(sandbox: Path, out_json: Path) -> int:
    os.chdir(sandbox)
    sys.path.insert(0, str(sandbox))
    status: dict = {}
    try:
        suite = unittest.defaultTestLoader.loadTestsFromName(GATE_CLASS)
    except Exception as exc:  # noqa: BLE001 - report, do not raise
        status["<load>"] = f"ERROR {type(exc).__name__}: {exc}"
        suite = None
    if suite is not None:
        names: list = []

        def flatten(s):
            for t in s:
                if isinstance(t, unittest.TestSuite):
                    flatten(t)
                else:
                    names.append(t.id().rsplit(".", 1)[-1])

        flatten(suite)
        for n in names:
            status[n] = "ok"
        result = unittest.TestResult()
        suite.run(result)
        for kind, items in (("FAIL", result.failures), ("ERROR", result.errors)):
            for test, tb in items:
                tid = test.id()
                key = None
                for n in names:
                    if f".{n}" in tid or tid.endswith(n):
                        key = n
                if key is None:
                    key = tid
                last = [ln for ln in tb.strip().splitlines() if ln.strip()][-1][:300]
                status[key] = f"{kind}: {last}"
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=1)
    return 0


# ── hand edits (scenario pre-steps) ──────────────────────────────────────────


def _read(sb: Path, rel: str) -> str:
    return (sb / rel).read_text(encoding="utf-8")


def _write(sb: Path, rel: str, text: str) -> None:
    (sb / rel).write_text(text, encoding="utf-8")


def _replace_once(text: str, old: str, new: str, where: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"hand edit: expected exactly one {old!r} in {where}, found {n}")
    return text.replace(old, new)


def _replace_in_row(text: str, needle: str, old: str, new: str, where: str) -> str:
    lines = text.splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if needle in ln and old in ln]
    if len(hits) != 1:
        raise SystemExit(f"hand edit: expected one row with {needle!r} and {old!r} in {where}, found {len(hits)}")
    lines[hits[0]] = lines[hits[0]].replace(old, new, 1)
    return "".join(lines)


def hand_raise(sb: Path, req_old: str, req_new: str, compat_name: str, spec_old: str, spec_new: str) -> None:
    """A hand floor PR: the requirement string everywhere it is inline, and the split-column rows of README's
    compatibility table and REFERENCE's extras table. The REFERENCE matrix and prose are NOT touched here."""
    _write(sb, "pyproject.toml", _replace_once(_read(sb, "pyproject.toml"), f'"{req_old}"', f'"{req_new}"', "pyproject.toml"))
    t = _read(sb, "tests/test_pyproject_extras.py")
    _write(sb, "tests/test_pyproject_extras.py", _replace_once(t, f'\n        "{req_old}",\n', f'\n        "{req_new}",\n', "EXPECTED_EXTRAS"))
    for rel in ("AGENTS.md", "README.md", "docs/QUICK_START.md"):
        _write(sb, rel, _replace_once(_read(sb, rel), req_old, req_new, rel))
    _write(sb, "README.md", _replace_in_row(_read(sb, "README.md"), f"`{compat_name}`", f"`{spec_old}`", f"`{spec_new}`", "README compat row"))
    _write(sb, REF, _replace_in_row(_read(sb, REF), f"`{compat_name}`", f"`{spec_old}`", f"`{spec_new}`", "REFERENCE extras row"))


def hand_remove_worker(sb: Path) -> None:
    t = _read(sb, "pyproject.toml")
    _write(sb, "pyproject.toml", _replace_once(t, '    "juniper-cascor-worker>=0.4.0",\n', "", "pyproject.toml"))


def ref_edit(sb: Path, old: str, new: str) -> None:
    _write(sb, REF, _replace_once(_read(sb, REF), old, new, REF))


def ref_matrix_row_inplace(sb: Path, series: str, old_cell: str, new_cell: str) -> None:
    text = _read(sb, REF)
    _write(sb, REF, _replace_in_row(text, f"| {series} ", f" {old_cell} ", f" {new_cell} ", f"REFERENCE {series} row"))


def ref_duplicate_row(sb: Path, series: str, new_label: "str | None" = None) -> None:
    lines = _read(sb, REF).splitlines(keepends=True)
    hits = [i for i, ln in enumerate(lines) if ln.startswith(f"| {series} ")]
    if len(hits) != 1:
        raise SystemExit(f"duplicate row: {len(hits)} rows for {series}")
    row = lines[hits[0]]
    if new_label is not None:
        if len(new_label) != len(series):
            raise SystemExit("duplicate row: the synthetic label must keep the label width")
        row = row.replace(f"| {series} ", f"| {new_label} ", 1)
    lines.insert(hits[0] + 1, row)
    _write(sb, REF, "".join(lines))


def add_unreleased(sb: Path, rel: str) -> None:
    t = _read(sb, rel)
    _write(sb, rel, _replace_once(t, "## [Unreleased]\n", "## [Unreleased]\n\n### Fixed\n\n- A simulated change for the validator's proposal.\n", rel))


DATA_RAISE = ("juniper-data[api]>=0.17.1", "juniper-data[api]>=0.18.0", "juniper-data[api]", ">=0.17.1", ">=0.18.0")
DATA_LOWER = ("juniper-data[api]>=0.17.1", "juniper-data[api]>=0.17.0", "juniper-data[api]", ">=0.17.1", ">=0.17.0")
REC_RAISE = ("juniper-recurrence>=0.8.1,<0.9.0", "juniper-recurrence>=0.8.2,<0.9.0", "juniper-recurrence", ">=0.8.1,<0.9.0", ">=0.8.2,<0.9.0")
META_PATCH = ("propose", "juniper-ml", "0.11.4", "0.11.5", "patch")
META_MINOR = ("propose", "juniper-ml", "0.11.4", "0.12.0", "minor")


def scenarios() -> dict:
    return {
        "noop": [],
        "patch": [META_PATCH],
        "minor": [META_MINOR],
        "minor_after_data_raise_ref_untouched": [("hand", "raise juniper-data, REFERENCE matrix untouched", lambda sb: hand_raise(sb, *DATA_RAISE)), META_MINOR],
        "minor_after_data_raise_row_inplace": [
            ("hand", "raise juniper-data + rewrite the 0.11.x row in place (what #2507 forces on a hand PR)", lambda sb: (hand_raise(sb, *DATA_RAISE), ref_matrix_row_inplace(sb, "0.11.x", ">=0.17.1    ", ">=0.18.0    "))),
            META_MINOR,
        ],
        "patch_after_data_raise": [("hand", "raise juniper-data, REFERENCE matrix untouched", lambda sb: hand_raise(sb, *DATA_RAISE)), META_PATCH],
        "recurrence_raise_alone_then_subpkg_patch": [
            ("hand", "raise juniper-recurrence only, no version bump, clause untouched", lambda sb: hand_raise(sb, *REC_RAISE)),
            ("hand", "ci-tools unreleased entry", lambda sb: add_unreleased(sb, "juniper-ci-tools/CHANGELOG.md")),
            ("propose", "juniper-ci-tools", "0.9.1", "0.9.2", "patch"),
        ],
        "recurrence_raise_then_meta_patch": [("hand", "raise juniper-recurrence only", lambda sb: hand_raise(sb, *REC_RAISE)), META_PATCH],
        "patch_row_not_last": [
            ("hand", "a 0.12.x row after 0.11.x (synthetic)", lambda sb: ref_duplicate_row(sb, "0.11.x", "0.12.x")),
            ("hand", "raise juniper-data, REFERENCE matrix untouched", lambda sb: hand_raise(sb, *DATA_RAISE)),
            META_PATCH,
        ],
        "minor_with_newer_row_present": [("hand", "a 0.13.x row after 0.11.x (synthetic)", lambda sb: ref_duplicate_row(sb, "0.11.x", "0.13.x")), META_MINOR],
        "patch_after_lowering_a_floor": [("hand", "lower juniper-data to >=0.17.0", lambda sb: hand_raise(sb, *DATA_LOWER)), META_PATCH],
        "patch_after_removing_a_pin": [("hand", "remove juniper-cascor-worker from [worker] (pyproject only)", hand_remove_worker), META_PATCH],
        "patch_declares_anchor_missing": [("hand", "declares sentence reworded", lambda sb: ref_edit(sb, "`juniper-ml` 0.11.4 declares the following pins.", "`juniper-ml` 0.11.4 declares these pins.")), META_PATCH],
        "patch_version_cell_doubled": [("hand", "a second Version cell", lambda sb: ref_edit(sb, "| **Importable Modules** | None         |\n", "| **Importable Modules** | None         |\n| **Version**            | `0.11.4`     |\n")), META_PATCH],
        "patch_clause_doubled": [("hand", "a second sets-them clause", lambda sb: ref_edit(sb, "(see the extras table above): it raises", "(see the extras table above). 0.11.4 sets them to `juniper-recurrence>=0.8.1,<0.9.0` too: it raises")), META_PATCH],
        "minor_heading_missing": [("hand", "Ecosystem Compatibility heading renamed", lambda sb: ref_edit(sb, "\n## Ecosystem Compatibility\n", "\n## Ecosystem Compatibility Matrix\n")), META_MINOR],
        "patch_row_doubled_with_raise": [
            ("hand", "duplicate the 0.11.x row", lambda sb: ref_duplicate_row(sb, "0.11.x")),
            ("hand", "raise juniper-data", lambda sb: hand_raise(sb, *DATA_RAISE)),
            META_PATCH,
        ],
        "subpkg_doc_tools_minor_then_meta_minor": [
            ("hand", "doc-tools unreleased entry", lambda sb: add_unreleased(sb, "juniper-doc-tools/CHANGELOG.md")),
            ("propose", "juniper-doc-tools", "0.1.2", "0.2.0", "minor"),
            META_MINOR,
        ],
        "subpkg_service_core_minor": [
            ("hand", "service-core unreleased entry", lambda sb: add_unreleased(sb, "juniper-service-core/CHANGELOG.md")),
            ("propose", "juniper-service-core", "0.7.2", "0.8.0", "minor"),
        ],
    }


# ── driver ───────────────────────────────────────────────────────────────────


def extract(tar_path: Path, dest: Path) -> None:
    with tarfile.open(tar_path) as tf:
        members = []
        for m in tf.getmembers():
            name = m.name
            top = name.split("/", 1)[0]
            two = "/".join(name.split("/", 2)[:2])
            if top in SKIP_TOP and not name.startswith("notes/templates"):
                continue
            if two in SKIP_TOP:
                continue
            members.append(m)
        tf.extractall(dest, members=members, filter="data")


def run_child(script: Path, *args: str) -> None:
    proc = subprocess.run([sys.executable, "-B", str(script), *args], capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    if proc.returncode != 0:
        raise SystemExit(f"child {args[:2]} failed: {proc.stderr[-2000:]}")


def run_module(sb: Path, suite: str) -> dict:
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", suite], cwd=str(sb), capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    tail = [ln for ln in (proc.stderr or "").strip().splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", proc.stderr or "", re.MULTILINE)))
    return {"rc": proc.returncode, "summary": tail, "failing": [f"{a} ({b})" for a, b in fails]}


def gate(script: Path, sb: Path, out_json: Path) -> dict:
    run_child(script, "gate", str(sb), str(out_json))
    return json.loads(out_json.read_text(encoding="utf-8"))


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("drive", "build", "gate"))
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--tar")
    ap.add_argument("--carrier-root")
    ap.add_argument("--gate-file")
    ap.add_argument("--out")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--date", default="2026-11-09")
    args = ap.parse_args(argv)
    script = Path(__file__).resolve()
    if args.mode == "build":
        sb, package, from_v, to_v, bump, date, out_json = args.rest
        return child_build(Path(sb), package, from_v, to_v, bump, date, Path(out_json))
    if args.mode == "gate":
        sb, out_json = args.rest
        return child_gate(Path(sb), Path(out_json))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    carrier_root = Path(args.carrier_root)
    summary: dict = {}
    for name, steps in scenarios().items():
        if args.only and name not in args.only:
            continue
        for variant in ("main", "carrier"):
            sb = out / "sim" / name / variant / "juniper-ml"
            if sb.parent.exists():
                shutil.rmtree(sb.parent)
            sb.mkdir(parents=True)
            extract(Path(args.tar), sb)
            if variant == "carrier":
                for rel in CARRIER_FILES:
                    shutil.copyfile(carrier_root / rel, sb / rel)
            shutil.copyfile(args.gate_file, sb / "tests" / "test_pyproject_extras.py")
            log: list = []
            log.append({"step": "initial", "gate": gate(script, sb, sb.parent / "gate_0.json")})
            for k, step in enumerate(steps, start=1):
                if step[0] == "hand":
                    step[2](sb)
                    rec = {"step": f"hand: {step[1]}"}
                else:
                    _, package, from_v, to_v, bump = step
                    pj = sb.parent / f"proposal_{k}.json"
                    ref_before = (sb / REF).read_text(encoding="utf-8")
                    run_child(script, "build", str(sb), package, from_v, to_v, bump, args.date, str(pj))
                    p = json.loads(pj.read_text(encoding="utf-8"))
                    ref_after = (sb / REF).read_text(encoding="utf-8")
                    rec = {
                        "step": f"propose {package} {from_v}->{to_v} ({bump})",
                        "skipped_reason": p["skipped_reason"],
                        "edit_paths": p["edit_paths"],
                        "duplicate_paths": p["duplicate_paths"],
                        "reference_checklist": p["reference_checklist"],
                        "pr_body_lists_reference": p["pr_body_lists_reference"],
                        "reference_changed_lines": [ln[:400] for ln in difflib.unified_diff(ref_before.splitlines(), ref_after.splitlines(), lineterm="", n=0) if ln[:1] in "+-" and not ln.startswith(("+++", "---"))],
                    }
                rec["gate"] = gate(script, sb, sb.parent / f"gate_{k}.json")
                log.append(rec)
            log.append({"step": "final modules", "modules": {s: run_module(sb, s) for s in MODULE_SUITES}})
            with open(sb.parent / "log.json", "w", encoding="utf-8") as fh:
                json.dump(log, fh, indent=1)
            summary.setdefault(name, {})[variant] = [
                {"step": r["step"], "gate_failing": sorted(k for k, v in (r.get("gate") or {}).items() if v != "ok")} for r in log if "gate" in r
            ] + [{"modules": {s: (m["rc"], m["failing"]) for s, m in log[-1]["modules"].items()}}]
            print(name, variant, json.dumps(summary[name][variant][-2]["gate_failing"]), flush=True)
    with open(out / ("summary.json" if not args.only else "summary_only.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
