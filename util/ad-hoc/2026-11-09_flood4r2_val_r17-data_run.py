"""
Run juniper-data's pytest in a given tree with a chosen test ORDER, under the interpreter that runs this file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, Cursor flood-4 round 2)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 ("data: 44 unrun tests"); independent validation of the r17-data-unit-marks carrier

Usage (run it WITH the interpreter under test; everything after ``--`` goes to pytest verbatim):
  <python> 2026-11-09_flood4r2_val_r17-data_run.py --tree T --order ORDER [--ids F] -- <pytest args>

ORDER is one of:
  default        pytest's own collection order (what CI runs)
  reversed       the selected items in reverse
  shuffle:SEED   the selected items shuffled with random.Random(SEED)
  front          the node ids listed in --ids run FIRST (their own order kept), every other item after
  end            every other item first, the node ids in --ids LAST

The reorder hook runs ``trylast``, after pytest's ``-m`` deselection, so only the selected items move.
juniper-data has no random-order plugin, so CI's order is the collection order; these orders probe for
state leaking between the newly selected tests and the rest of the lane in either direction.
"""

import argparse
import os
import random
import sys
from pathlib import Path

import pytest


class Reorder:
    """A pytest plugin object that reorders the selected items once collection is done."""

    def __init__(self, order: str, ids: list[str]) -> None:
        self.order = order
        self.ids = ids
        self.first: list[str] = []
        self.last: list[str] = []
        self.moved = 0

    @pytest.hookimpl(trylast=True)  # after the marker plugin has deselected by ``-m``
    def pytest_collection_modifyitems(self, session, config, items) -> None:  # noqa: ARG002 - pytest hook signature
        if self.order == "reversed":
            items.reverse()
        elif self.order.startswith("shuffle:"):
            random.Random(int(self.order.split(":", 1)[1])).shuffle(items)  # nosec B311 - test ordering, not crypto
        elif self.order in ("front", "end"):
            wanted = set(self.ids)
            chosen = [item for item in items if item.nodeid in wanted]
            rest = [item for item in items if item.nodeid not in wanted]
            self.moved = len(chosen)
            items[:] = chosen + rest if self.order == "front" else rest + chosen
        self.first = [item.nodeid for item in items[:3]]
        self.last = [item.nodeid for item in items[-3:]]


def main() -> int:
    argv = sys.argv[1:]
    if "--" not in argv:
        print("usage: ... --tree T --order ORDER [--ids F] -- <pytest args>", file=sys.stderr)
        return 2
    split = argv.index("--")
    parser = argparse.ArgumentParser(description="ordered pytest run")
    parser.add_argument("--tree", required=True)
    parser.add_argument("--order", default="default")
    parser.add_argument("--ids", default=None)
    args = parser.parse_args(argv[:split])
    pytest_args = argv[split + 1 :]
    sys.dont_write_bytecode = True
    ids: list[str] = []
    if args.ids:
        ids = [line.strip() for line in Path(args.ids).read_text(encoding="utf-8").splitlines() if line.strip()]
    tree = Path(args.tree).resolve()
    os.chdir(tree)
    plugin = Reorder(args.order, ids)
    rc = pytest.main(["-p", "no:cacheprovider", *pytest_args], plugins=[plugin])
    mod = sys.modules.get("juniper_data")
    print(f"[run] python={sys.version.split()[0]} gil={getattr(sys, '_is_gil_enabled', lambda: True)()} pytest={pytest.__version__}")
    print(f"[run] juniper_data={getattr(mod, '__file__', None)}")
    print(f"[run] order={args.order} moved={plugin.moved} first={plugin.first} last={plugin.last}")
    print(f"[run] exit={int(rc)}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
