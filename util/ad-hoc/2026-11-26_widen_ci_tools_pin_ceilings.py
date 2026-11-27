#!/usr/bin/env python3
"""
Widen juniper-ml's own pins on juniper-ci-tools to admit a new minor, the fix-up a ci-tools release proposal needs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- one-off (juniper-ml#2684's fix-up), kept for the next ci-tools minor
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2684 (fix-up ed8a3271), 7668ad30 (the 0.7.0 precedent: ceilings only)

Why this exists
---------------
The release train's ``util/release_train/propose.py`` moves juniper-ci-tools' version, ``_version.py`` and
the CHANGELOG, but not juniper-ml's own pins on the package. When the proposal is a new minor, the
pins' ceiling excludes the version the proposal creates. Two suites then fail on the proposal PR:

- ``tests/test_env_drift_check_drift.py``'s ``test_ml_own_workflow_pins_admit_current`` ("pin upper bound
  0.10.0 excludes current 0.10.0 -- widen the ceiling in the same PR as the ci-tools bump"), for the
  workflows it names. #2684 failed it for ci.yml, lockfile-update.yml and docs-full-check.yml.
- ``tests/test_python_version_matrix_drift.py``, once ci.yml moves, because it holds the juniper-ml recipe
  in ``conf/python_versions.yaml`` equal to ci.yml's ``Install test dependencies``.

This rewrites ``juniper-ci-tools>=FLOOR,<OLD`` to ``juniper-ci-tools>=FLOOR,<NEW``:

- in every ``.github/workflows/*.yml`` (all of them, as 7668ad30 did, not only the three the test names);
- in the juniper-ml recipe's ``install`` commands in ``conf/python_versions.yaml``, and nowhere else in that
  file. Its juniper-cascor-worker and juniper-data recipes mirror those repos' own CI, which keep their pins.

The floor never moves. It refuses unless the counts match ``--expect-workflows`` and ``--expect-recipe``.

Usage (from the checkout root; dry run by default):
    python3 util/ad-hoc/2026-11-26_widen_ci_tools_pin_ceilings.py --floor 0.9.0 --old 0.10.0 --new 0.11.0
    python3 util/ad-hoc/2026-11-26_widen_ci_tools_pin_ceilings.py --floor 0.9.0 --old 0.10.0 --new 0.11.0 --write

As run for #2684 (14 pins in 10 workflows, plus the recipe's one line): the defaults below.
Exit: 0 when the counts match (and, with --write, the files are rewritten); 1 when they do not; 2 on usage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

CONF = Path("conf") / "python_versions.yaml"
RECIPE = "juniper-ml"


def recipe_commands(conf_text: str, old: str) -> list[str]:
    """The juniper-ml recipe's install commands that carry the old pin."""
    install = ((yaml.safe_load(conf_text) or {}).get("repos") or {}).get(RECIPE, {}).get("install") or []
    return [command for command in install if isinstance(command, str) and old in command]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--root", default=".", help="the juniper-ml checkout (default: the current directory)")
    parser.add_argument("--floor", default="0.9.0")
    parser.add_argument("--old", default="0.10.0", help="the ceiling the pins carry now")
    parser.add_argument("--new", default="0.11.0", help="the ceiling they get")
    parser.add_argument("--expect-workflows", type=int, default=14, help="pins expected across .github/workflows/*.yml")
    parser.add_argument("--expect-recipe", type=int, default=1, help="recipe install commands expected to carry the pin")
    parser.add_argument("--write", action="store_true", help="rewrite the files (default: report only)")
    args = parser.parse_args()

    root = Path(args.root)
    old, new = f"juniper-ci-tools>={args.floor},<{args.old}", f"juniper-ci-tools>={args.floor},<{args.new}"
    if old == new:
        print("--old and --new are the same ceiling", file=sys.stderr)
        return 2

    edits: dict[Path, str] = {}
    total = 0
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        count = text.count(old)
        if count:
            edits[path] = text.replace(old, new)
            total += count
            print(f"{count}  {path.relative_to(root)}")

    conf = root / CONF
    conf_text = conf.read_text(encoding="utf-8")
    commands = recipe_commands(conf_text, old)
    for command in commands:
        if conf_text.count(command) != 1:
            print(f"{CONF}: the {RECIPE} command {command!r} occurs {conf_text.count(command)} times; refusing", file=sys.stderr)
            return 1
        conf_text = conf_text.replace(command, command.replace(old, new))
    if commands:
        edits[conf] = conf_text
        print(f"{len(commands)}  {CONF} ({RECIPE} recipe)")

    if total != args.expect_workflows or len(commands) != args.expect_recipe:
        print(f"found {total} workflow pins (expected {args.expect_workflows}) and {len(commands)} recipe commands (expected {args.expect_recipe}); nothing written", file=sys.stderr)
        return 1
    if args.write:
        for path, text in edits.items():
            path.write_text(text, encoding="utf-8")
    print(f"{'widened' if args.write else 'would widen'} {total} workflow pins and {len(commands)} recipe command(s): <{args.old} -> <{args.new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
