#!/usr/bin/env python3
"""Run juniper-data-client's lockfile commit-step suite against any copy of the step, with nothing written to the system temp directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — investigation (flood-3 backlog rows B / E / H verification)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4 (the base64 row);
         juniper-data-client#244 (which moves the suite's own system-temp-directory writes into a scratch dir)

Why this exists
---------------
``tests/test_lockfile_signed_commit.py`` on juniper-data-client ``main`` runs the workflow step's own
shell, and that shell writes ``lockfile-commit.json`` and ``lockfile-commit-result.json`` in the system temp directory.
Nothing may be written to the system temp directory on this host (owner directive 2026-10-26). Until #244 lands, the
suite can only be run here with the step's temp-directory prefix rewritten to a scratch directory, which is
what this harness does (the same rewrite #244 makes inside the suite). A suite that already carries
#244's ``RUNNER_TMP`` relocation is run as-is.

It also answers two questions the suite cannot answer on Linux by itself:

* ``--workflow``: run the suite against a different copy of ``lockfile-update.yml`` -- the OLD step from
  ``main`` -- to prove the new encode tests fail there (non-vacuous).
* ``--simulate-bsd {empty,reject}``: behave like the macOS unit-test leg. ``_gnu_base64_available`` is
  forced False, and a fake host ``base64`` sits between the test's ``bin`` dir and ``/usr/bin`` on the
  step's PATH: ``empty`` exits 0 printing nothing, ``reject`` exits 64 on ``-w``.

Usage:
    2026-10-26_flood3_backlog_lockfile_test_harness.py --test-file T --workflow W [--simulate-bsd MODE] [-k SUBSTR]

Exit status is 0 when every selected test passed (skips allowed), 1 otherwise, 2 on a usage error, and
3 if a file appeared in the system temp directory at either of the two paths the step names.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER_PATHS = (Path("/tmp/lockfile-commit.json"), Path("/tmp/lockfile-commit-result.json"))  # nosec B108 - only checked, never written; tmp-path-literal: allow

FAKE_BSD_BASE64 = {
    "empty": "#!/bin/sh\nexit 0\n",
    "reject": "#!/bin/sh\necho 'base64: invalid option -- w' >&2\nexit 64\n",
}


def _load_module(test_file: Path):
    name = "flood3_backlog_lockfile_suite"
    spec = importlib.util.spec_from_file_location(name, test_file)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {test_file}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test-file", required=True, type=Path)
    parser.add_argument("--workflow", required=True, type=Path, help="the lockfile-update.yml copy the suite should extract its step from")
    parser.add_argument("--simulate-bsd", choices=sorted(FAKE_BSD_BASE64), default=None)
    parser.add_argument("-k", dest="pattern", default=None, help="run only tests whose id contains this substring")
    args = parser.parse_args(argv)

    before = {p: p.exists() for p in RUNNER_PATHS}
    scratch = Path(tempfile.mkdtemp(prefix="flood3-backlog-harness-"))
    try:
        fake_root = scratch / "root"
        (fake_root / ".github" / "workflows").mkdir(parents=True)
        shutil.copyfile(args.workflow, fake_root / ".github" / "workflows" / "lockfile-update.yml")

        mod = _load_module(args.test_file.resolve())
        mod._repo_root = lambda: fake_root

        if hasattr(mod, "RUNNER_TMP"):
            print("suite relocates its own /tmp writes (RUNNER_TMP present): run as-is")  # tmp-path-literal: allow
        else:
            step_tmp = scratch / "step-tmp"
            step_tmp.mkdir()
            original_load = mod._load_step

            def _relocated_load():
                doc, step, script = original_load()
                if "/tmp/" not in script:  # tmp-path-literal: allow
                    raise AssertionError("the step no longer writes under /tmp/; this harness's rewrite is stale")  # tmp-path-literal: allow
                return doc, step, script.replace("/tmp/", f"{step_tmp}/")  # tmp-path-literal: allow

            mod._load_step = _relocated_load
            mod.COMMIT_JSON = step_tmp / "lockfile-commit.json"
            mod.RESULT_JSON = step_tmp / "lockfile-commit-result.json"
            print(f"relocated the step's /tmp/ to {step_tmp}")  # tmp-path-literal: allow

        if args.simulate_bsd:
            fake_host = scratch / "fake-host-bin"
            fake_host.mkdir()
            (fake_host / "base64").write_text(FAKE_BSD_BASE64[args.simulate_bsd], encoding="utf-8")
            (fake_host / "base64").chmod(0o700)
            mod._gnu_base64_available = lambda: False
            original_env = mod._child_env

            def _env_with_fake_host(bin_dir, **overrides):
                env = original_env(bin_dir, **overrides)
                marker = f"{os.pathsep}/usr/bin"
                if marker not in env["PATH"]:
                    raise AssertionError(f"unexpected step PATH shape: {env['PATH']}")
                env["PATH"] = env["PATH"].replace(marker, f"{os.pathsep}{fake_host}{marker}", 1)
                return env

            mod._child_env = _env_with_fake_host
            print(f"simulating a BSD host base64 ({args.simulate_bsd}) at {fake_host}")

        suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
        if args.pattern:
            selected = unittest.TestSuite()
            for case in _iter_cases(suite):
                if args.pattern in case.id():
                    selected.addTest(case)
            suite = selected
        result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    leaked = [str(p) for p in RUNNER_PATHS if p.exists() and not before[p]]
    if leaked:
        print(f"WROTE UNDER /tmp: {leaked}")  # tmp-path-literal: allow
        return 3
    print(f"tests run={result.testsRun} failures={len(result.failures)} errors={len(result.errors)} skipped={len(result.skipped)}")
    return 0 if result.wasSuccessful() else 1


def _iter_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_cases(item)
        else:
            yield item


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
