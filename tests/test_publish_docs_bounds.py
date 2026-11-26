#!/usr/bin/env python3
"""Pin the publish docs' numbers to the publish workflows: the bounds the docs state are the bounds the steps run.

``docs/REFERENCE.md`` and ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`` give an operator the numbers that decide whether
a failed install check was index lag: how many times each install check tries, how long it waits between tries, and
the error it stops with after its last try. Each is read here from the seven publishers and required in the docs, so a
change to either side alone fails. A module of its own, as juniper-cascor#777 made its own: the one-artifact module
(``tests/test_publish_one_artifact.py``) reads the workflows alone. The docs state none of the JSON checks' bounds, so
none is pinned here.

Run: python3 -m unittest -v tests/test_publish_docs_bounds.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-11-26
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github" / "workflows"
DOCS = REPO / "docs"
#: The install check's own job (ruling 2 of 2026-11-16), in every publisher.
INSTALL = "verify-testpypi-install"
META = "publish.yml"
SUB_PACKAGES = ("publish-ci-tools.yml", "publish-config-tools.yml", "publish-doc-tools.yml", "publish-model-core.yml", "publish-observability.yml", "publish-service-core.yml")
#: workflow -> its install check's step name
INSTALL_STEPS = dict.fromkeys(SUB_PACKAGES, "Verify install from TestPyPI") | {META: "Verify TestPyPI install", "publish-model-core.yml": "Verify install from TestPyPI (no-deps, version-only import)"}
LAG_ERROR = "is not installable from TestPyPI after {tries} tries (index lag?): Re-run failed jobs; a real failure repeats"


def _run(workflow: str) -> str:
    jobs = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))["jobs"]
    found = [s for s in jobs[INSTALL].get("steps") or [] if s.get("name") == INSTALL_STEPS[workflow]]
    if len(found) != 1:
        raise AssertionError(f"{workflow}: expected exactly one step named {INSTALL_STEPS[workflow]!r} in {INSTALL}")
    return str(found[0]["run"])


def _doc(name: str) -> str:
    """The doc's text with each run of whitespace made one space: a rewrapped paragraph states the same bounds."""
    return " ".join((DOCS / name).read_text(encoding="utf-8").split())


def _retry(workflow: str) -> tuple[int, list[int]]:
    """The install check's (tries, the waits inside its loop), read from its commands."""
    commands = [line.strip() for line in _run(workflow).splitlines() if line.strip() and not line.strip().startswith("#")]
    loops = [i for i, c in enumerate(commands) if re.fullmatch(r"for attempt in [0-9 ]+; do", c)]
    if len(loops) != 1:
        raise AssertionError(f"{workflow}: expected one retry loop")
    start, end = loops[0], commands.index("done", loops[0])
    tries = len(commands[start].split()[3:-1])
    waits = [int(c.split()[1]) for c in commands[start:end] if re.fullmatch(r"sleep [0-9]+", c)]
    return tries, waits


class TestPublishDocsStateTheBounds(unittest.TestCase):
    def test_the_install_checks_retry(self) -> None:
        found = {workflow: _retry(workflow) for workflow in INSTALL_STEPS}
        tries, waits = found.pop(META)
        # The six sub-package checks retry alike: one loop, one wait between tries.
        self.assertEqual(len({repr(value) for value in found.values()}), 1, found)
        sub_tries, sub_waits = found[SUB_PACKAGES[0]]
        self.assertEqual((len(waits), len(sub_waits)), (1, 1))
        reference, cheatsheet = _doc("REFERENCE.md"), _doc("DEVELOPER_CHEATSHEET_JUNIPER-ML.md")
        # The meta-package's provenance poll and the sub-packages' retry, as each doc states them.
        self.assertIn(f"{tries} attempts × {waits[0]}s", reference)
        self.assertIn(f"{tries}×{waits[0]}s", cheatsheet)
        self.assertIn(f"{sub_tries}×{sub_waits[0]}s", reference)
        self.assertIn(f"{sub_tries}×{sub_waits[0]}s", cheatsheet)

    def test_each_install_check_stops_with_the_lag_error_the_docs_quote(self) -> None:
        # The error each check stops with after its last try, as each step prints it and as the reference quotes it.
        reference = _doc("REFERENCE.md")
        for workflow in INSTALL_STEPS:
            with self.subTest(workflow=workflow):
                tries, _ = _retry(workflow)
                error = LAG_ERROR.format(tries=tries)
                self.assertEqual(_run(workflow).count(error), 1)
                self.assertIn(error, reference)


if __name__ == "__main__":
    unittest.main()
