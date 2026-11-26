#!/usr/bin/env python3
"""Pin the publish docs' numbers to the publish workflows: the bounds the docs state are the bounds the steps run.

``docs/REFERENCE.md`` and ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`` give an operator the numbers that decide whether
a failed install check was index lag: how many times each install check tries, how long it waits between tries, how
many waits that makes and how long they come to, and the error it stops with after its last try. Each is read here
from the seven publishers and required in the docs, so a change to either side alone fails. A module of its own, as
juniper-cascor#777 made its own: the one-artifact module (``tests/test_publish_one_artifact.py``) reads the workflows
alone. The docs state none of the JSON checks' bounds, so none is pinned here.

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


def _retry(workflow: str) -> tuple[int, int, int]:
    """The install check's (tries, the wait between tries in seconds, the waits a run whose every try fails makes).

    Read from its commands. A loop that stops with its lag error inside the loop, before its wait, on its last try (the
    sub-packages') waits once fewer than it tries; one that waits after every failed try and stops after the loop (the
    meta-package's) waits as often as it tries."""
    commands = [line.strip() for line in _run(workflow).splitlines() if line.strip() and not line.strip().startswith("#")]
    loops = [i for i, c in enumerate(commands) if re.fullmatch(r"for attempt in [0-9 ]+; do", c)]
    if len(loops) != 1:
        raise AssertionError(f"{workflow}: expected one retry loop")
    start = loops[0]
    body = commands[start + 1 : commands.index("done", start)]
    tries = len(commands[start].split()[3:-1])
    sleeps = [i for i, c in enumerate(body) if re.fullmatch(r"sleep [0-9]+", c)]
    if len(sleeps) != 1:
        raise AssertionError(f"{workflow}: expected one wait inside the retry loop, found {len(sleeps)}")
    stops = [i for i, c in enumerate(body) if c == "exit 1"]
    if not stops:
        return tries, int(body[sleeps[0]].split()[1]), tries
    # The stop inside the loop must be the last try's, and come before the wait.
    if len(stops) != 1 or stops[0] > sleeps[0] or f'if [ "${{attempt}}" -eq {tries} ]; then' not in body[: stops[0]]:
        raise AssertionError(f"{workflow}: the retry loop stops other than on its last try, before its wait")
    return tries, int(body[sleeps[0]].split()[1]), tries - 1


class TestPublishDocsStateTheBounds(unittest.TestCase):
    def test_the_install_checks_retry(self) -> None:
        found = {workflow: _retry(workflow) for workflow in INSTALL_STEPS}
        tries, wait, waits = found.pop(META)
        # The six sub-package checks retry alike: one loop, one wait between tries, the same stop.
        self.assertEqual(len(set(found.values())), 1, found)
        sub_tries, sub_wait, sub_waits = found[SUB_PACKAGES[0]]
        reference, cheatsheet = _doc("REFERENCE.md"), _doc("DEVELOPER_CHEATSHEET_JUNIPER-ML.md")
        # The meta-package's provenance poll: its tries, its wait, and the waits' total, where each doc states them.
        self.assertIn(f"{tries} attempts × {wait}s, ~{waits * wait}s ceiling", reference)
        self.assertIn(f"{tries}×{wait}s `pip download` poll (~{waits * wait}s)", reference)
        self.assertIn(f"{tries}×{wait}s (~{waits * wait}s ceiling)", cheatsheet)
        # The sub-packages' retry: its tries, its wait, how many waits it makes and their total.
        self.assertIn(f"{sub_tries}×{sub_wait}s retry around `pip install` ({sub_waits} waits, ~{sub_waits * sub_wait}s)", reference)
        self.assertIn(f"up to {sub_tries} times with a {sub_wait}s interval ({sub_waits} waits, then the template's lag error", reference)
        self.assertIn(f"{sub_tries}×{sub_wait}s", cheatsheet)

    def test_each_install_check_stops_with_the_lag_error_the_docs_quote(self) -> None:
        # The error each check stops with after its last try, as each step prints it and as the reference quotes it.
        reference = _doc("REFERENCE.md")
        for workflow in INSTALL_STEPS:
            with self.subTest(workflow=workflow):
                tries, _, _ = _retry(workflow)
                error = LAG_ERROR.format(tries=tries)
                self.assertEqual(_run(workflow).count(error), 1)
                self.assertIn(error, reference)


if __name__ == "__main__":
    unittest.main()
