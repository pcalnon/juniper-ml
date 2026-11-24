#!/usr/bin/env python3
"""
Re-run the builder's four "pass both of main's lanes" mutants (its M1-M4), all at once, against today's main's two
pull-request lanes: a tree with the carrier laid over main 3cf8867c and the 137 newly selected tests deselected.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: finishing the d2-unrun-tests validation after VF was cut off)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_d2-data_mutants.py (the builder's M1-M4, copied here line for line),
         util/ad-hoc/2026-11-12_flood4r2_val_d2-data_run_lane.py (the lane runner this calls)

Why: the carrier's CHANGELOG entry says that with each of the four breaks in place, main's unit and integration
lanes pass ("only the newly run tests see them"). The builder measured that on main c68e6b4c; the carrier lands on
3cf8867c, which adds 47 unit tests (juniper-data#537). This run measures it on the main the text will describe.

Each mutant replaces exactly one line, named by number, whose text must equal the builder's ``old`` before it is
changed (so the line numbers cannot drift silently); every touched file is restored in ``finally`` and re-hashed.

Usage: 2026-11-14_flood4r2_val_d2-data_builder_mutants_on_main.py --tree <V1> --python <venv python>
           --deselect-unit <file> --deselect-integration <file> --out <dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN_LANE = Path(__file__).with_name("2026-11-12_flood4r2_val_d2-data_run_lane.py")
BUILDER_MUTANTS = (
    ("M1", "juniper_data/api/app.py", 191, "            MetricsAuthMiddleware(get_prometheus_app(), settings.metrics_trusted_ips),\n", "            get_prometheus_app(),\n", "the /metrics mount loses its trusted-IP wrapper (SEC-16)"),
    ("M2", "juniper_data/storage/local_fs.py", 54, '    if ".." in dataset_id:\n', '    if "..." in dataset_id:\n', "_validate_dataset_id stops refusing a parent reference inside an id (JD-SEC-01)"),
    ("M3", "juniper_data/storage/local_fs.py", 249, "        self._invalidate_metadata_cache()\n", "        pass\n", "LocalFSDatasetStore.save stops invalidating the metadata cache"),
    ("M4", "juniper_data/api/app.py", 194, "    @app.exception_handler(RequestValidationError)\n", "    # mutant: the handler below is defined and never registered\n", "the RequestValidationError handler is never registered (APD-DATA-013)"),
)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_all(tree: Path) -> dict[str, bytes]:
    """Apply every mutant; on any surprise restore what was changed and stop."""
    originals: dict[str, bytes] = {}
    try:
        for mutant_id, name, line, old, new, _what in BUILDER_MUTANTS:
            path = tree / name
            originals.setdefault(name, path.read_bytes())
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            if lines[line - 1] != old:
                raise SystemExit(f"{mutant_id}: line {line} of {name} is {lines[line - 1]!r}, not the builder's {old!r}")
            lines[line - 1] = new
            path.write_text("".join(lines), encoding="utf-8")
    except (Exception, SystemExit, KeyboardInterrupt):
        restore(tree, originals)
        raise
    return originals


def restore(tree: Path, originals: dict[str, bytes]) -> None:
    for name, data in originals.items():
        (tree / name).write_bytes(data)


def run_lane(python: str, tree: Path, out: Path, lane: str, extra: list[str]) -> dict:
    subprocess.run([sys.executable, str(RUN_LANE), "--python", python, "--tree", str(tree), "--out", str(out), "--lane", lane, *extra], capture_output=True, text=True, check=False)
    return json.loads((out / "result.json").read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    for option in ("tree", "python", "deselect-unit", "deselect-integration", "out"):
        parser.add_argument(f"--{option}", required=True)
    ns = parser.parse_args()
    tree, out = Path(ns.tree), Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    names = sorted({row[1] for row in BUILDER_MUTANTS})
    before = {name: sha256_of(tree / name) for name in names}
    originals = apply_all(tree)
    try:
        during = {name: sha256_of(tree / name) for name in names}
        unit = run_lane(ns.python, tree, out / "unit", "unit", ["--no-cov", "--deselect-file", ns.deselect_unit])
        integration = run_lane(ns.python, tree, out / "integration", "integration", ["--deselect-file", ns.deselect_integration])
    finally:
        restore(tree, originals)
    after = {name: sha256_of(tree / name) for name in names}
    report = {
        "tree": str(tree),
        "python": ns.python,
        "mutants_applied_at_once": {row[0]: f"{row[1]}:{row[2]}: {row[5]}" for row in BUILDER_MUTANTS},
        "sha256_before": before,
        "sha256_with_mutants": during,
        "sha256_after": after,
        "restored_byte_for_byte": after == before,
        "main_unit_lane": {"exit": unit["steps"]["pytest"]["exit"], "summary": unit["steps"]["pytest"]["summary"], "failed": unit["junit"].get("failed_or_error", []), "deselected_by_file": unit["deselected_by_file"], "probe": unit.get("probe")},
        "main_integration_lane": {"exit": integration["steps"]["pytest"]["exit"], "summary": integration["steps"]["pytest"]["summary"], "failed": integration["junit"].get("failed_or_error", []), "deselected_by_file": integration["deselected_by_file"]},
    }
    (out / "lanes.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"builder mutants at once: {list(report['mutants_applied_at_once'])}")
    print(f"main unit lane:        exit={report['main_unit_lane']['exit']} | {report['main_unit_lane']['summary']} | failed {report['main_unit_lane']['failed']}")
    print(f"main integration lane: exit={report['main_integration_lane']['exit']} | {report['main_integration_lane']['summary']} | failed {report['main_integration_lane']['failed']}")
    print(f"restored byte for byte: {report['restored_byte_for_byte']}")
    return 0 if report["restored_byte_for_byte"] else 3


if __name__ == "__main__":
    sys.exit(main())
