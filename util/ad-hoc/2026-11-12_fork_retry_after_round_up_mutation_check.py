#!/usr/bin/env python3
"""
Mutation-check the Retry-After round-up tests added to juniper-data, juniper-cascor and juniper-canopy (APD-ECO-016).

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off verifier for the three fork fixes (owner ruling 2026-11-09, "Row + fix all three")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md (APD-ECO-016; APD-SVCCORE-004);
         juniper-service-core/juniper_service_core/security.py (the reference: ``RateLimiter._seconds_until_reset``
         and ``FailedAuthThrottle.check``); util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py (H-14, applied here)

Why
---
Each fork's ``RateLimiter.check`` reported ``int(window - elapsed)`` and each ``FailedAuthThrottle.check``
``max(1, int(window - elapsed))``. The fix ports juniper-service-core's ``max(1, math.ceil(...))`` to both limiter
paths (and to the throttle in juniper-data and juniper-cascor; juniper-canopy has none). This script shows that the
new test module in each fork fails for every wrong rounding it could meet, and for the fork's own pre-fix file.

For one ``--target`` it runs the new module against:

* **baseline**: the fixed source -> every test must PASS, none skipped; its test count is the one every later run
  must repeat;
* **pre-fix**: the source file as ``origin/main`` has it -> must FAIL (the tests detect the defect itself);
* **R1 truncate**, **R2 floor-over-truncate**, **R3 ceil-no-floor**, **R4 always-add-one**, **R5 round-half**:
  five wrong bodies for ``RateLimiter._seconds_until_reset`` -> each must FAIL;
* **R6 rejection-path-truncates**, **R7 allowed-path-truncates**: one ``check`` return reverted -> each must FAIL;
* **R8** to **R12**: five more wrong bodies, each of which agrees with ``ceil`` at 9.4, 6.0 and 60.0 (add 0.7 and
  truncate, add 0.4 and round, ``ceil`` of 0.3 less, add a half and round, bump only above a quarter) -> each must
  FAIL. The first version of the tests held only those three remainders above a second, and an independent review
  showed that all five passed it;
* **W1** to **W6**: the value is right in ``check`` and wrong on the wire -> each must FAIL. ``__call__`` answers 1
  whatever the wait, or names a wait one second short in the message, in ``Retry-After`` or in
  ``X-RateLimit-Reset``; the middleware replaces the 429's ``Retry-After`` with 1; the middleware sends
  ``X-RateLimit-Reset: 0`` on an allowed response in the window's last second. W5 and W6 mutate the fork's
  middleware file, and are skipped for a target that names none (juniper-data here);
* **T1 truncate-floor** (the old throttle code), **T2 always-add-one**, **T3 round-half**, and **T5** to **T7** (the
  throttle's forms of R8, R10 and R11) -> each must FAIL (data and cascor only);
* **T4 ceil-no-floor** is reported only: the throttle's remainder is positive wherever the line is reached, so the
  floor of 1 changes no reachable result there (the source comment says so).

A mutant counts as KILLED only when the run exits 1 with at least one test FAILED on an assertion, no failure of any
other kind, no ERROR, and the baseline's number of tests: a mutant that breaks the import, or makes the code raise,
is not a kill. (The pre-fix file is allowed one other failure, by name: ``test_the_floor_holds_at_the_exact_boundary``
calls the new helper directly and meets an ``AttributeError`` there.) Each mutant is written over its file, run in a fresh
interpreter with bytecode writing off and its own ``PYTHONPYCACHEPREFIX``, and the original bytes are put back after
every run and checked by sha256 at the end. Do not upload from the tree while this runs.

Usage
-----
    python3 util/ad-hoc/2026-11-12_fork_retry_after_round_up_mutation_check.py --target data|cascor|canopy \
        --repo-root /path/to/the/fork/worktree [--python /path/to/python] [--test MODULE] [--scratch DIR]

Exit 0 when the baseline passes and every required mutant is killed; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import signal
import subprocess  # nosec B404 -- runs pytest and git in argv form, no shell
import tempfile
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 -- parses only the JUnit reports this script's own pytest runs write

SIX = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")

_X = "self._window - (now - window_start)"
HELPER = f"        return max(1, math.ceil({_X}))\n"
REJECT = "                return (False, 0, self._seconds_until_reset(now, window_start))\n"
ALLOW = "            return (True, self._limit - count - 1, self._seconds_until_reset(now, window_start))\n"
THROTTLE = "                return (True, max(1, math.ceil(remaining)))\n"
CALL_GUARD = "        request.state.rate_limit_reset = reset_in\n\n        if not allowed:\n"
CALL_DETAIL = '                detail=f"Rate limit exceeded. Try again in {reset_in} seconds.",\n'
CALL_RESET = '                    "X-RateLimit-Reset": str(reset_in),\n'
CALL_RETRY = '                    "Retry-After": str(reset_in),\n'
MIDDLEWARE_RERAISE = "                headers=exc.headers,\n"
MIDDLEWARE_RESET = "str(request.state.rate_limit_reset)"

#: name -> (which file: "source" or "middleware", the text replaced, its replacement, must the mutant be killed?)
LIMITER_MUTANTS = dict(
    [
        ("R1 truncate", ("source", HELPER, f"        return int({_X})\n", True)),
        ("R2 floor-over-truncate", ("source", HELPER, f"        return max(1, int({_X}))\n", True)),
        ("R3 ceil-no-floor", ("source", HELPER, f"        return math.ceil({_X})\n", True)),
        ("R4 always-add-one", ("source", HELPER, f"        return int({_X}) + 1\n", True)),
        ("R5 round-half", ("source", HELPER, f"        return max(1, round({_X}))\n", True)),
        ("R6 rejection-path-truncates", ("source", REJECT, f"                return (False, 0, int({_X}))\n", True)),
        ("R7 allowed-path-truncates", ("source", ALLOW, f"            return (True, self._limit - count - 1, int({_X}))\n", True)),
        # R8 to R12 agree with ceil at 9.4, 6.0 and 60.0, the only remainders above a second the first version of the
        # tests held. An independent review found that all five passed it (round 1, lane B).
        ("R8 add-0.7-then-truncate", ("source", HELPER, f"        return max(1, int({_X} + 0.7))\n", True)),
        ("R9 add-0.4-then-round", ("source", HELPER, f"        return max(1, round({_X} + 0.4))\n", True)),
        ("R10 ceil-of-0.3-less", ("source", HELPER, f"        return max(1, math.ceil({_X} - 0.3))\n", True)),
        ("R11 add-half-then-round", ("source", HELPER, f"        return max(1, round({_X} + 0.5))\n", True)),
        ("R12 bump-above-a-quarter", ("source", HELPER, f"        return max(1, int({_X}) + (1 if ({_X}) % 1 > 0.25 else 0))\n", True)),
    ]
)
#: The value is right in ``check`` and wrong by the time a caller reads it: ``__call__`` or the middleware changes it.
WIRE_MUTANTS = dict(
    [
        ("W1 call-answers-one", ("source", CALL_GUARD, CALL_GUARD + "            reset_in = 1\n", True)),
        ("W2 detail-one-short", ("source", CALL_DETAIL, '                detail=f"Rate limit exceeded. Try again in {max(1, reset_in - 1)} seconds.",\n', True)),
        ("W3 retry-after-one-short", ("source", CALL_RETRY, '                    "Retry-After": str(max(1, reset_in - 1)),\n', True)),
        ("W4 reset-header-one-short", ("source", CALL_RESET, '                    "X-RateLimit-Reset": str(max(1, reset_in - 1)),\n', True)),
        ("W5 middleware-answers-one", ("middleware", MIDDLEWARE_RERAISE, '                headers={**(exc.headers or {}), **({"Retry-After": "1"} if exc.status_code == 429 else {})},\n', True)),
        ("W6 allowed-header-zero-in-last-second", ("middleware", MIDDLEWARE_RESET, "str(request.state.rate_limit_reset if request.state.rate_limit_reset > 1 else 0)", True)),
    ]
)
THROTTLE_MUTANTS = dict(
    [
        ("T1 truncate-floor", ("source", THROTTLE, "                return (True, max(1, int(remaining)))\n", True)),
        ("T2 always-add-one", ("source", THROTTLE, "                return (True, int(remaining) + 1)\n", True)),
        ("T3 round-half", ("source", THROTTLE, "                return (True, max(1, round(remaining)))\n", True)),
        ("T4 ceil-no-floor", ("source", THROTTLE, "                return (True, math.ceil(remaining))\n", False)),
        ("T5 add-0.7-then-truncate", ("source", THROTTLE, "                return (True, max(1, int(remaining + 0.7)))\n", True)),
        ("T6 ceil-of-0.3-less", ("source", THROTTLE, "                return (True, max(1, math.ceil(remaining - 0.3)))\n", True)),
        ("T7 add-half-then-round", ("source", THROTTLE, "                return (True, max(1, round(remaining + 0.5)))\n", True)),
    ]
)

#: ``middleware`` is None where this script does not know the fork's middleware lines: W5 and W6 are then skipped.
TARGETS = dict(
    data=dict(
        source="juniper_data/api/security.py",
        middleware=None,
        test="juniper_data/tests/unit/test_retry_after_rounds_up.py",
        marker="unit and not slow",
        python="/opt/miniforge3/envs/JuniperData/bin/python",
        throttle=True,
        unset=[],
        set=dict(),
    ),
    cascor=dict(
        source="src/api/security.py",
        middleware="src/api/middleware.py",
        test="src/tests/unit/api/test_retry_after_rounds_up.py",
        marker="unit and not slow",
        python="/opt/miniforge3/envs/JuniperCascor1/bin/python",
        throttle=True,
        unset=["JUNIPER_CASCOR_LOG_DIR"],
        set=dict(),
    ),
    canopy=dict(
        source="src/security.py",
        middleware="src/middleware.py",
        test="src/tests/unit/test_retry_after_rounds_up.py",
        marker="not requires_cascor and not requires_server and not slow",
        python="/opt/miniforge3/envs/JuniperCanopy1/bin/python",
        throttle=False,
        unset=[],
        set=dict(LIBTORCH="", LD_LIBRARY_PATH=""),
    ),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, name: str) -> str:
    """``text`` with its ONE occurrence of ``old`` replaced; anything else is a script error, not a survivor."""
    if text.count(old) != 1:
        raise SystemExit(f"{name}: expected exactly one occurrence of {old.strip()!r}, found {text.count(old)}")
    return text.replace(old, new)


def is_assertion(message: str) -> bool:
    """Whether a JUnit failure message is a TEST's failed ``assert``.

    pytest writes ``assert ...`` or ``AssertionError: assert ...`` for one. A bare ``AssertionError: text`` is
    something the code under test raised, and is not counted.
    """
    return message.startswith(("assert ", "AssertionError: assert "))


#: The one failure the pre-fix file may show that is not an assertion: this test calls the new helper directly, and
#: the pre-fix file has no helper. (test name, the exception its JUnit message starts with)
PRE_FIX_ALLOWED = ("test_the_floor_holds_at_the_exact_boundary", "AttributeError")


def run_tests(python: str, repo_root: Path, target: dict, scratch: Path, label: str) -> tuple[int, dict[str, int], list[str], list[tuple[str, str]], str]:
    """(exit code, JUnit totals, names of failed or errored tests, the (name, message) of each failure that is not an assertion, output).

    The totals carry one key beyond JUnit's own: ``other``, the failures that are NOT assertions. pytest reports any
    exception raised in a test body as a failure, so a mutant that makes the code raise ``NameError`` would otherwise
    read as killed by the tests.
    """
    env = dict(os.environ)
    for name in SIX:
        env[name] = ""
    for name in target["unset"]:
        env.pop(name, None)
    env.update(target["set"])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # A label such as "pre-fix (origin/main)" must not become a nested path.
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-")
    env["PYTHONPYCACHEPREFIX"] = str(scratch / f"pycache-{safe}")
    report = scratch / f"junit-{safe}.xml"
    report.unlink(missing_ok=True)
    command = [python, "-B", "-m", "pytest", "-m", target["marker"], target["test"], "-rs", "-p", "no:cacheprovider", "--no-cov", f"--junitxml={report}"]
    done = subprocess.run(command, cwd=repo_root, env=env, capture_output=True, text=True, check=False)  # nosec B603
    names = ("tests", "failures", "errors", "skipped")
    totals = dict.fromkeys((*names, "other"), -1)
    failed: list[str] = []
    others: list[tuple[str, str]] = []
    try:
        root = ElementTree.parse(report).getroot()  # nosec B314
    except (OSError, ElementTree.ParseError):
        return done.returncode, totals, failed, others, done.stdout + done.stderr
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is not None:
        totals = dict((name, int(suite.get(name, "-1"))) for name in names)
        totals["other"] = 0
        for case in suite.iter("testcase"):
            failure = case.find("failure")
            if failure is not None or case.find("error") is not None:
                failed.append(case.get("name", "?"))
            if failure is not None and not is_assertion(failure.get("message", "")):
                totals["other"] += 1
                others.append((case.get("name", "?"), failure.get("message", "")))
    return done.returncode, totals, failed, others, done.stdout + done.stderr


def tally(seen: dict[str, int]) -> str:
    return f"tests={seen['tests']} failures={seen['failures']} (not assertions: {seen['other']}) errors={seen['errors']} skipped={seen['skipped']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--python", help="interpreter (default: the target's conda environment)")
    parser.add_argument("--test", help="the test module, relative to --repo-root (default: the target's)")
    parser.add_argument("--scratch", help="scratch directory (default: a new one under $TMPDIR)")
    args = parser.parse_args(argv)

    target = dict(TARGETS[args.target])
    if args.test:
        target["test"] = args.test
    python = args.python or target["python"]
    repo_root = Path(args.repo_root)
    # Every file a mutant may be written over, by key, with the bytes to put back.
    paths = dict(source=repo_root / target["source"])
    if target["middleware"]:
        paths["middleware"] = repo_root / target["middleware"]
    originals = dict((key, path.read_bytes()) for key, path in paths.items())
    texts = dict((key, data.decode("utf-8")) for key, data in originals.items())
    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="retry-after-mut-"))
    scratch.mkdir(parents=True, exist_ok=True)

    # A SIGTERM or SIGHUP (a tool timeout, a stopped session) ends Python WITHOUT running ``finally``, which would
    # leave whichever mutant is on disk in the tree. Raising from the handler unwinds through the ``finally`` blocks
    # below, which put the original bytes back. The copies in the scratch directory cover a SIGKILL, which nothing
    # can handle: ``cp <scratch>/original-<key>.bytes <file>`` restores by hand.
    def stop(signum: int, frame: object) -> None:
        raise SystemExit(128 + signum)

    for number in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, stop)
    for key, data in originals.items():
        (scratch / f"original-{key}.bytes").write_bytes(data)
        print(f"original {key} saved: {scratch / f'original-{key}.bytes'}")

    mutants = dict(LIMITER_MUTANTS)
    mutants.update(WIRE_MUTANTS)
    if target["throttle"]:
        mutants.update(THROTTLE_MUTANTS)
    elif THROTTLE in texts["source"]:
        raise SystemExit("this target is configured without a throttle, but its source carries the throttle line")
    prefix = subprocess.run(["git", "show", f"origin/main:{target['source']}"], cwd=repo_root, capture_output=True, check=True)  # nosec B603 B607
    if prefix.stdout == originals["source"]:
        raise SystemExit("the source file equals origin/main's: there is no fix here to check")

    failures: list[str] = []
    print(f"target={args.target} source={paths['source']} sha256={sha256(originals['source'])[:16]} python={python}")
    code, seen, failed, others, output = run_tests(python, repo_root, target, scratch, "baseline")
    # The module's size is read from the baseline, not written here: every later run must then run the same number.
    expected_tests = seen["tests"]
    baseline_ok = code == 0 and expected_tests >= 1 and seen == dict(tests=expected_tests, failures=0, errors=0, skipped=0, other=0)
    print(f"  {'baseline':40s}exit={code}  [{tally(seen)}]  {'OK' if baseline_ok else 'NOT OK'}")
    if not baseline_ok:
        failures.append("baseline did not pass in full")
        print(output[-3000:])

    try:
        cases: list[tuple[str, str, bytes, bool]] = [("pre-fix (origin/main)", "source", prefix.stdout, True)]
        for name, (key, old, new, must_fail) in mutants.items():
            if key not in texts:
                print(f"  {name:40s}SKIPPED: this target names no {key} file")
                continue
            cases.append((name, key, replace_once(texts[key], old, new, name).encode("utf-8"), must_fail))
        for name, key, mutated, must_fail in cases:
            paths[key].write_bytes(mutated)
            try:
                code, seen, failed, others, output = run_tests(python, repo_root, target, scratch, name)
            finally:
                paths[key].write_bytes(originals[key])
            # Killed means a test FAILED on an assertion with every test still running: an error (a broken import, say) is
            # not a kill, and neither is a mutant whose only failures are other exceptions. The pre-fix file is the one
            # case allowed such a failure beside its assertions: the test that calls the new helper directly finds no
            # helper there.
            assertions = seen["failures"] - seen["other"]
            allowed = PRE_FIX_ALLOWED if name.startswith("pre-fix") else None
            unexplained = [item for item in others if not (allowed and item[0] == allowed[0] and item[1].startswith(allowed[1]))]
            killed = code == 1 and assertions >= 1 and not unexplained and seen["errors"] == 0 and seen["tests"] == expected_tests
            verdict = "KILLED" if killed else "SURVIVED"
            note = "" if must_fail else "  (reported only)"
            print(f"  {name:40s}exit={code}  [{tally(seen)}]  {verdict}{note}")
            for test_name in failed:
                print(f"      failed: {test_name}")
            if must_fail and not killed:
                failures.append(f"mutant {name} survived")
                print(output[-2000:])
    finally:
        for key, path in paths.items():
            path.write_bytes(originals[key])
    for key, path in paths.items():
        restored = sha256(path.read_bytes()) == sha256(originals[key])
        print(f"restored {key}: {restored} (sha256 {sha256(path.read_bytes())[:16]})")
        if not restored:
            failures.append(f"the {key} file was not restored")

    for item in failures:
        print(f"FAIL  {item}")
    print(f"result: {'OK' if not failures else 'FAILED'} ({len(failures)} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
