#!/usr/bin/env python3
"""
Mutation-check the FastAPI native-telemetry opt-out tests ported to juniper-cascor and juniper-canopy.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off verifier for the two telemetry ports (owner ruling 2026-11-09, "Port to both now")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#454 (the change ported); the telemetry PRs in juniper-cascor and juniper-canopy;
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (R-OBS-SC-2's follow-ups);
         util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py (H-14, applied here too)

Why
---
The ported test ``importorskip``s ``fastapi.telemetry``, and this host's conda environments hold FastAPI 0.137, where
that module does not exist. Run there, the test skips, and a skip proves nothing. This script runs it against the
FastAPI the consumer's lock pins (an overlay directory given with ``--overlay``, built with
``pip install --target DIR -c requirements.lock fastapi starlette opentelemetry-api``) and then shows the test can fail:

* **baseline**: the test must PASS (one test passed, none skipped) and the run must report the overlay's FastAPI;
* **no-kwarg**: the whole ``telemetry={...}`` argument removed -> must FAIL;
* **flip-<key>**, for each of the five keys: that key set to ``True`` -> must FAIL;
* **drop-<key>**, for the four keys FastAPI defaults to on: that key's line removed -> must FAIL;
* **drop-auto_configure** is reported, not required to fail: FastAPI 0.162 defaults it from
  ``FASTAPI_OTEL_AUTO_CONFIGURE``, which this script sets to ``true`` for every run so that the default is "on" and a
  dropped key is visible.

Each mutant is written over the source file, run in a fresh interpreter with bytecode writing off and its own
``PYTHONPYCACHEPREFIX``, and the original bytes are restored in ``finally`` and checked by sha256. Do not upload from
the tree while this runs.

Usage
-----
    python3 util/ad-hoc/2026-11-12_fastapi_telemetry_opt_out_mutation_check.py --target cascor \
        --repo-root /path/to/juniper-cascor-worktree --python /opt/miniforge3/envs/JuniperCascor1/bin/python \
        --overlay /path/to/overlay [--expect-fastapi 0.162.2] [--scratch DIR]

A mutant counts as killed only when the one test FAILS on an assertion: pytest reports any exception raised in a
test body as a failure, so a failure of another kind (a mutant that makes the code raise) is not counted.

Exit 0 when the baseline passes (on ``--expect-fastapi``'s version, when given) and every required mutant fails; 1
otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import signal
import subprocess  # nosec B404 -- runs pytest in argv form, no shell
import tempfile
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 -- parses only the JUnit report this script's own pytest run writes

SIX = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
KEYS = ("tracing", "metrics", "logs", "operation_spans", "auto_configure")
DEFAULT_ON = ("tracing", "metrics", "logs", "operation_spans")

TARGETS = dict(
    cascor=dict(
        source="src/api/app.py",
        pytest_args=["-m", "unit and not slow", "src/tests/unit/api/test_api_app.py", "-k", "test_create_app_disables_fastapi_native_telemetry"],
        unset=["JUNIPER_CASCOR_LOG_DIR"],
        set=dict(),
    ),
    canopy=dict(
        source="src/main.py",
        pytest_args=["-m", "not requires_cascor and not requires_server and not slow", "src/tests/unit/test_main_import_and_lifespan.py", "-k", "test_app_disables_fastapi_native_telemetry"],
        unset=[],
        set=dict(LIBTORCH="", LD_LIBRARY_PATH=""),
    ),
)

PROBE_PLUGIN = '''"""Scratch pytest plugin: print the FastAPI version the run imported."""
import sys


def pytest_sessionfinish(session, exitstatus):
    print("\\nMUT-PROBE fastapi=" + str(getattr(sys.modules.get("fastapi"), "__version__", None)))
'''


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def telemetry_block(text: str) -> tuple[int, int]:
    """The [start, end) character span of the one ``telemetry={ ... },`` argument, whole lines."""
    matches = list(re.finditer(r"^[ \t]*telemetry=\{\n(?:[ \t]*\"[a-z_]+\": (?:True|False),\n)+[ \t]*\},\n", text, flags=re.MULTILINE))
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one telemetry={{...}} argument, found {len(matches)}")
    return matches[0].start(), matches[0].end()


def mutants(text: str) -> list[tuple[str, str, bool]]:
    """(name, mutated text, must_fail) for every mutant."""
    start, end = telemetry_block(text)
    block = text[start:end]
    out: list[tuple[str, str, bool]] = [("no-kwarg", text[:start] + text[end:], True)]
    for key in KEYS:
        line = re.search(rf"^[ \t]*\"{key}\": False,\n", block, flags=re.MULTILINE)
        if line is None:
            raise SystemExit(f"key {key!r} is not in the telemetry argument as False")
        flipped = block[: line.start()] + line.group(0).replace("False", "True") + block[line.end() :]
        out.append((f"flip-{key}", text[:start] + flipped + text[end:], True))
        dropped = block[: line.start()] + block[line.end() :]
        out.append((f"drop-{key}", text[:start] + dropped + text[end:], key in DEFAULT_ON))
    return out


def is_assertion(message: str) -> bool:
    """Whether a JUnit failure message is a TEST's failed ``assert``.

    pytest writes ``assert ...`` or ``AssertionError: assert ...`` for one. A bare ``AssertionError: text`` is
    something the code under test raised, and is not counted.
    """
    return message.startswith(("assert ", "AssertionError: assert "))


def run_pytest(python: str, repo_root: Path, target: dict, overlay: str, scratch: Path, label: str) -> tuple[int, str, dict[str, int]]:
    env = dict(os.environ)
    for name in SIX:
        env[name] = ""
    for name in target["unset"]:
        env.pop(name, None)
    env.update(target["set"])
    # Make "auto_configure" default to on, so that dropping the key is observable (see the module docstring).
    env["FASTAPI_OTEL_AUTO_CONFIGURE"] = "true"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPYCACHEPREFIX"] = str(scratch / f"pycache-{label}")
    plugin_dir = scratch / "plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "mut_probe_plugin.py").write_text(PROBE_PLUGIN, encoding="utf-8")
    parts = [str(plugin_dir), overlay]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    report = scratch / f"junit-{label}.xml"
    report.unlink(missing_ok=True)
    command = [python, "-B", "-m", "pytest", *target["pytest_args"], "-rs", "-p", "no:cacheprovider", "--no-cov", "-p", "mut_probe_plugin", f"--junitxml={report}"]
    done = subprocess.run(command, cwd=repo_root, env=env, capture_output=True, text=True, check=False)  # nosec B603
    return done.returncode, done.stdout + done.stderr, counts(report)


def counts(report: Path) -> dict[str, int]:
    """tests / failures / errors / skipped from a JUnit report, and ``other``: the failures that are not assertions.

    All -1 when the report is missing or unreadable. pytest reports any exception raised in a test body as a failure,
    so without ``other`` a mutant that makes the code raise ``NameError`` would read as killed by the test.
    """
    names = ("tests", "failures", "errors", "skipped")
    try:
        root = ElementTree.parse(report).getroot()  # nosec B314 -- a report this script's own pytest run just wrote
    except (OSError, ElementTree.ParseError):
        return dict.fromkeys((*names, "other"), -1)
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return dict.fromkeys((*names, "other"), -1)
    seen = dict((name, int(suite.get(name, "-1"))) for name in names)
    seen["other"] = sum(1 for failure in suite.iter("failure") if not is_assertion(failure.get("message", "")))
    return seen


def tally(seen: dict[str, int]) -> str:
    return f"tests={seen['tests']} failures={seen['failures']} (not assertions: {seen['other']}) errors={seen['errors']} skipped={seen['skipped']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--overlay", required=True, help="directory holding the lock's FastAPI (pip install --target)")
    parser.add_argument("--expect-fastapi", help="the FastAPI version the baseline run must report, e.g. 0.162.2 (default: any that runs the test un-skipped)")
    parser.add_argument("--scratch", help="scratch directory (default: a new one under $TMPDIR)")
    args = parser.parse_args(argv)

    target = TARGETS[args.target]
    repo_root = Path(args.repo_root)
    source = repo_root / target["source"]
    original = source.read_bytes()
    text = original.decode("utf-8")
    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="telemetry-mut-"))
    scratch.mkdir(parents=True, exist_ok=True)

    # A SIGTERM or SIGHUP (a tool timeout, a stopped session) ends Python WITHOUT running ``finally``, which would
    # leave whichever mutant is on disk in the tree. Raising from the handler unwinds through the ``finally`` below,
    # which puts the original bytes back. The copy in the scratch directory covers a SIGKILL, which nothing can
    # handle: ``cp <scratch>/original-source.bytes <file>`` restores by hand.
    def stop(signum: int, frame: object) -> None:
        raise SystemExit(128 + signum)

    for number in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, stop)
    (scratch / "original-source.bytes").write_bytes(original)
    print(f"original saved: {scratch / 'original-source.bytes'}")

    failures: list[str] = []
    print(f"target={args.target} source={source} sha256={sha256(original)[:16]}")
    code, output, seen = run_pytest(args.python, repo_root, target, args.overlay, scratch, "baseline")
    probe = re.search(r"MUT-PROBE fastapi=(\S+)", output)
    # One test ran, it passed, and it did not skip: a skip would be the vacuous pass this script exists to rule out.
    baseline_ok = code == 0 and seen == dict(tests=1, failures=0, errors=0, skipped=0, other=0)
    reported = probe.group(1) if probe else "?"
    print(f"  {'baseline':22s}exit={code}  fastapi={reported}  [{tally(seen)}]  {'OK' if baseline_ok else 'NOT OK'}")
    if not baseline_ok:
        failures.append("baseline did not pass un-skipped")
        print(output[-3000:])
    if args.expect_fastapi and reported != args.expect_fastapi:
        failures.append(f"the run imported FastAPI {reported}, not the expected {args.expect_fastapi}")

    try:
        for name, mutated, must_fail in mutants(text):
            source.write_bytes(mutated.encode("utf-8"))
            code, output, seen = run_pytest(args.python, repo_root, target, args.overlay, scratch, name)
            # Killed means the one test ran and FAILED on an assertion: an error (a broken import, say) is not a kill, and
            # neither is a failure on any other exception (a mutant that makes the code raise).
            killed = code == 1 and seen == dict(tests=1, failures=1, errors=0, skipped=0, other=0)
            verdict = "KILLED" if killed else "SURVIVED"
            note = "" if must_fail else "  (reported only)"
            print(f"  {name:22s}exit={code}  [{tally(seen)}]  {verdict}{note}")
            if must_fail and not killed:
                failures.append(f"mutant {name} survived")
                print(output[-2000:])
    finally:
        source.write_bytes(original)
    restored = sha256(source.read_bytes()) == sha256(original)
    print(f"restored: {restored} (sha256 {sha256(source.read_bytes())[:16]})")
    if not restored:
        failures.append("the source file was not restored")

    for item in failures:
        print(f"FAIL  {item}")
    print(f"result: {'OK' if not failures else 'FAILED'} ({len(failures)} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
