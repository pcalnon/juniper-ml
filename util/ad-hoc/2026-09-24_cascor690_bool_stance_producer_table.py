#!/usr/bin/env python
"""Derive juniper-data's reading of ``allow_truncation`` from its REAL params classes, and check cascor's against it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#690 (fix-forward of #688's validation). Its report found that
         ``TrainingLifecycleManager._as_bool_stance`` read "f" / "n" as True -- ``bool("f")`` -- while
         juniper-data reads them as False. The fixup makes the two agree; this script is how the
         producer's rule was measured, and how the fixed reader was checked against it.

usage:
  2026-09-24_cascor690_bool_stance_producer_table.py table <juniper-data-tree> [--out FILE]
      Run with juniper-data's interpreter (e.g. /opt/miniforge3/envs/JuniperData/bin/python).
      Validates every candidate value through EquitiesParams, EquitiesSeqParams and CsvImportParams --
      each declares ``allow_truncation: bool | None`` -- and prints what each makes of it: True, False,
      None (null), or REJECT (juniper-data answers that request 400). Refuses if the three disagree.
      ``--out`` also writes the table as JSON for the ``compare`` step.
  2026-09-24_cascor690_bool_stance_producer_table.py compare <table.json> <cascor-tree>
      Run with cascor's interpreter. Feeds the same candidates to that tree's ``_as_bool_stance`` and
      prints every value it reads differently from the producer. A REJECT must read as None: a
      value juniper-data refuses is no stance. Exit 1 on any mismatch.

The candidates are JSON values only -- bool, null, numbers, strings, arrays, objects -- because JSON is
the wire on every path a stance takes to juniper-data (the staging routes, auto-start's
``JUNIPER_CASCOR_AUTO_DATASET_PARAMS``, and juniper-data-client's request body). NaN and the
infinities are included although a JSON encoder normally refuses them.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Tuple

SPELLINGS = ["0", "off", "f", "false", "n", "no", "1", "on", "t", "true", "y", "yes"]


def _case_variants(word: str) -> List[str]:
    """``true`` -> ``true``, ``TRUE``, ``True``, ``tRUE``: every casing class the producer might treat differently."""
    return sorted({word, word.upper(), word.capitalize(), word.capitalize().swapcase()})


def candidates() -> List[Tuple[str, Any]]:
    """``(label, value)`` pairs; the label is stable across interpreters so the two steps can join on it."""
    out: List[Tuple[str, Any]] = [("null", None), ("bool True", True), ("bool False", False)]
    for i in (0, 1, 2, -1, 10):
        out.append((f"int {i}", i))
    for x in (0.0, 1.0, -0.0, 0.5, 1.5, 2.0, -1.0, float("nan"), float("inf"), float("-inf")):
        out.append((f"float {x!r}", x))
    for word in SPELLINGS:
        for variant in _case_variants(word):
            out.append((f"str {variant!r}", variant))
    for padded in (" true", "true ", "\ttrue", "true\n", " 1", "0 ", " f", "no "):
        out.append((f"str {padded!r}", padded))
    for other in ("", "  ", "maybe", "2", "-1", "1.0", "0.0", "tru", "truee", "yes!", "none", "null", "None", "nil", "enable", "disabled", "ok", "ｔｒｕｅ", "ｆ", "trüe", "ＹＥＳ"):
        out.append((f"str {other!r}", other))
    for container in ([], [True], {}, {"a": 1}):
        out.append((f"json {json.dumps(container)}", container))
    return out


def _verdict(cls: Any, base: Dict[str, Any], value: Any) -> Any:
    from pydantic import ValidationError

    try:
        return cls(**base, allow_truncation=value).allow_truncation
    except ValidationError as exc:
        locs = {tuple(err.get("loc", ())) for err in exc.errors()}
        if ("allow_truncation",) not in locs:
            raise RuntimeError(f"{cls.__name__} rejected something other than allow_truncation: {exc}") from exc
        return "REJECT"


def table(tree: str, out: str | None) -> int:
    sys.path.insert(0, tree)
    import pydantic
    import pydantic_core
    from juniper_data.generators.csv_import.params import CsvImportParams
    from juniper_data.generators.equities.params import EquitiesParams
    from juniper_data.generators.equities_seq.params import EquitiesSeqParams

    classes = [(EquitiesParams, {}), (EquitiesSeqParams, {}), (CsvImportParams, {"file_path": "x.csv"})]
    print(f"pydantic {pydantic.VERSION}, pydantic-core {pydantic_core.__version__}; tree {tree}")
    for cls, _ in classes:
        field = cls.model_fields["allow_truncation"]
        print(f"  {cls.__name__}.allow_truncation: {field.annotation} = {field.default!r}; model_config={dict(cls.model_config)}")
    rows: Dict[str, Any] = {}
    disagreements = 0
    for label, value in candidates():
        verdicts = {cls.__name__: _verdict(cls, base, value) for cls, base in classes}
        distinct = {json.dumps(v) for v in verdicts.values()}
        if len(distinct) != 1:
            disagreements += 1
            print(f"  DISAGREE {label}: {verdicts}")
        rows[label] = next(iter(verdicts.values()))
        print(f"  {label:24s} -> {rows[label]}")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, sort_keys=True)
        print(f"wrote {out}")
    return 1 if disagreements else 0


def compare(table_path: str, tree: str) -> int:
    sys.path.insert(0, os.path.join(tree, "src"))
    from api.lifecycle.manager import TrainingLifecycleManager

    with open(table_path, encoding="utf-8") as fh:
        rows = json.load(fh)
    mismatches = 0
    for label, value in candidates():
        producer = rows[label]
        expected = None if producer == "REJECT" else producer
        got = TrainingLifecycleManager._as_bool_stance(value)
        ok = got is expected
        mismatches += not ok
        if not ok:
            print(f"  MISMATCH {label:24s} producer={producer!s:7s} cascor={got!r}")
    print(f"{len(rows)} candidates, {mismatches} mismatch(es) against the producer's table")
    return 1 if mismatches else 0


def main(argv: List[str]) -> int:
    if len(argv) >= 2 and argv[0] == "table":
        out = argv[argv.index("--out") + 1] if "--out" in argv else None
        return table(argv[1], out)
    if len(argv) == 3 and argv[0] == "compare":
        return compare(argv[1], argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
