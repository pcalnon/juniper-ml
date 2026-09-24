#!/usr/bin/env python3
"""Run, baseline and mutation-check the bytes-compare + Sentry-locals fix in its four copies.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#683 (the validation that found it); owner ruling "Fix everywhere now"
    (2026-09-24); the three PRs "fix(security): a non-ASCII API key is a 401, not a 500 that
    hands Sentry the real key" in juniper-ml, juniper-data and juniper-cascor.

WHAT IS BEING CHECKED
---------------------
``hmac.compare_digest`` raises ``TypeError`` on a ``str`` holding any non-ASCII character, and
Starlette decodes header bytes as latin-1, so an anonymous ``X-API-Key: \\xa0`` made every
``APIKeyAuth.validate`` copy raise: a 500, and under Sentry's default
``include_local_variables=True`` an error event carrying the loop's ``candidate`` -- the real
configured key. The fix compares UTF-8 (``surrogatepass``) bytes in all three service copies and
turns local-variable capture off in ``juniper-observability``'s ``configure_sentry``, with a
``before_send`` backstop that drops frame ``vars``.

SUBCOMMANDS
-----------
``run``       the suite against the working tree (``--ci-lane`` adds the CI marker expression).
``baseline``  the same suite against ``origin/main`` (``git archive``), for the before/after count.
``mutate``    for each mutation: copy the tree to scratch, apply ONE exact-text edit (it must match
              exactly the number of times declared, or the mutation is refused), run the
              suite's targeted tests IN THE CI LANE, and check that every expected test FAILED.
              A deselected test is absent from the results, so an unmarked test reads as NOT
              CAUGHT rather than passing unseen. An unmutated copy is run first; if it does not
              pass, the harness itself is broken and nothing after it means anything.

Scratch copies are deleted as soon as each run finishes (the session's /tmp is inode-bound).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

CASCOR_PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
DATA_PY = "/opt/miniforge3/envs/JuniperData/bin/python"


@dataclass(frozen=True)
class Mutation:
    mutation_id: str
    summary: str
    path: str
    edits: tuple[tuple[str, str, int], ...]  # (old, new, expected occurrence count)
    # "all:<substr>" -> every collected test whose node id contains <substr> must fail.
    # "any:<substr>" -> at least one such test must fail.
    expect: tuple[str, ...]
    # Substrings at least one failure message must contain (e.g. the 500 a caller would see).
    expect_messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class Suite:
    copy: tuple[str, ...]
    cwd: str
    python: str
    pythonpath: tuple[str, ...]
    targeted: tuple[str, ...]
    full: tuple[str, ...]
    unset_env: tuple[str, ...] = ()
    # The owning repo's CI marker expression, when its CI selects by marker. ``mutate`` always
    # applies it, so a CAUGHT verdict also proves the tests are in the lane CI actually runs
    # (an unmarked test there is silently deselected); ``run`` / ``baseline`` apply it on
    # ``--ci-lane``.
    ci_marker: str | None = None
    # ``baseline`` extracts the whole repo instead of ``copy`` (the full suites read files
    # outside the package, e.g. juniper-data's test_memory_budget_check.py loads util/).
    baseline_whole_tree: bool = False
    mutations: tuple[Mutation, ...] = field(default_factory=tuple)


# Never let a test run initialise the REAL Sentry. The session shell exports SENTRY_SDK_DSN,
# and cascor's src/main.py initialises sentry_sdk from it at import time -- which several of
# its unit tests trigger -- so a plain run tries to send test events to the live project.
_SENTRY_DSN_VARS = ("SENTRY_DSN", "SENTRY_SDK_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


_STR_COMPARE = 'if hmac.compare_digest(api_key, candidate):'
_BYTES_COMPARE = 'if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")):'

_NON_ASCII_UNIT_EXPECT = (
    "all:test_non_ascii_presented_key_is_a_mismatch_not_an_exception",
    "any:test_validate_matches_exactly_when_the_strings_are_equal",
    "all:test_call_raises_401_on_a_non_ascii_header",
)


def _service_mutations(path: str, app_expect: tuple[str, ...]) -> tuple[Mutation, ...]:
    return (
        Mutation("REVERT", "the str compare that raised TypeError", path, ((_BYTES_COMPARE, _STR_COMPARE, 1),), _NON_ASCII_UNIT_EXPECT + app_expect, ("500",)),
        Mutation(
            "ESCAPE",
            "surrogateescape in place of surrogatepass (raises on a lone high surrogate; collides e-acute with its escape twin)",
            path,
            (('"surrogatepass"', '"surrogateescape"', 2),),
            ("any:test_validate_matches_exactly_when_the_strings_are_equal",),
        ),
        Mutation(
            "STRICT",
            "strict UTF-8 (raises on any lone surrogate)",
            path,
            (('.encode("utf-8", "surrogatepass")', '.encode("utf-8")', 2),),
            ("any:test_validate_matches_exactly_when_the_strings_are_equal",),
        ),
    )


_OBS = "juniper_observability/sentry.py"
_DROP_OPTION = ("        include_local_variables=False,\n", "", 1)
_DROP_BACKSTOP = ("    _strip_frame_local_variables(event)\n    return event", "    return event", 1)

SUITES: dict[str, Suite] = {
    "observability": Suite(
        copy=("juniper-observability",),
        cwd="juniper-observability",
        python=CASCOR_PY,
        pythonpath=("juniper-observability",),
        targeted=("tests/test_sentry.py",),
        full=("tests",),
        mutations=(
            Mutation("NO-OPTION", "include_local_variables=False removed", "juniper-observability/" + _OBS, (_DROP_OPTION,), ("all:test_local_variables_are_never_captured", "all:test_the_option_alone_keeps_the_secret_out")),
            Mutation(
                "NO-BACKSTOP",
                "before_send no longer drops frame vars",
                "juniper-observability/" + _OBS,
                (_DROP_BACKSTOP,),
                (
                    "all:test_drops_vars_from_every_exception_in_a_chain",
                    "all:test_drops_vars_from_thread_stacktraces",
                    "all:test_drops_vars_from_a_top_level_stacktrace",
                    "all:test_scrubs_headers_and_frames_in_the_same_event",
                    "all:test_the_before_send_hook_alone_keeps_the_secret_out",
                ),
            ),
            Mutation("NEITHER", "both layers removed: the finding's configuration", "juniper-observability/" + _OBS, (_DROP_OPTION, _DROP_BACKSTOP), ("all:test_a_captured_exception_never_carries_a_secret_local",)),
            Mutation("NO-THREADS", "thread stacktraces not walked", "juniper-observability/" + _OBS, (('("exception", "threads")', '("exception",)', 1),), ("all:test_drops_vars_from_thread_stacktraces",)),
            Mutation("NO-TOPLEVEL", "top-level stacktrace not walked", "juniper-observability/" + _OBS, (('stacktraces = [event.get("stacktrace")]', "stacktraces = []", 1),), ("all:test_drops_vars_from_a_top_level_stacktrace",)),
        ),
    ),
    "service-core": Suite(
        copy=("juniper-service-core", "juniper-model-core"),
        cwd=".",
        python=CASCOR_PY,
        pythonpath=("juniper-service-core", "juniper-model-core"),
        targeted=("juniper-service-core/tests/test_security.py", "juniper-service-core/tests/test_middleware.py", "juniper-service-core/tests/test_t2_websocket.py"),
        full=("juniper-service-core/tests",),
        mutations=_service_mutations(
            "juniper-service-core/juniper_service_core/security.py",
            ("all:test_security_middleware_401_not_500_on_a_non_ascii_key", "all:test_non_ascii_key_failures_are_counted_by_the_throttle", "all:test_ws_authenticate_closes_4001_on_a_non_ascii_key"),
        ),
    ),
    "data": Suite(
        copy=("juniper_data", "pyproject.toml"),
        cwd=".",
        python=DATA_PY,
        pythonpath=(),
        targeted=("juniper_data/tests/unit/test_security.py",),
        full=("juniper_data/tests/unit",),
        ci_marker="unit and not slow",
        baseline_whole_tree=True,
        mutations=_service_mutations("juniper_data/api/security.py", ("all:test_http_request_is_401_not_500", "all:test_failed_attempts_reach_the_throttle")),
    ),
    "cascor": Suite(
        copy=("src", "conf", "pyproject.toml"),
        cwd="src",
        python=CASCOR_PY,
        pythonpath=(),
        targeted=("tests/unit/api/test_api_security.py", "tests/unit/test_main_sentry_no_local_variables.py"),
        full=("tests/unit/api",),
        unset_env=("JUNIPER_CASCOR_LOG_DIR",),
        ci_marker="unit and not slow",
        baseline_whole_tree=True,
        mutations=(
            *_service_mutations("src/api/security.py", ("all:test_http_request_is_401_not_500", "all:test_failed_attempts_reach_the_throttle", "all:test_websocket_handshake_closes_4001")),
            Mutation("MAIN-LOCALS", "src/main.py's bootstrap sentry_sdk.init loses include_local_variables=False", "src/main.py", (("            include_local_variables=False,\n", "", 1),), ("all:test_every_bootstrap_sentry_init_turns_local_variables_off",)),
            Mutation("MAIN-LOCALS-TRUE", "... or passes True", "src/main.py", (("            include_local_variables=False,\n", "            include_local_variables=True,\n", 1),), ("all:test_every_bootstrap_sentry_init_turns_local_variables_off",)),
        ),
    ),
}


def _env(tree: Path, suite: Suite) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in suite.unset_env and k not in _SENTRY_DSN_VARS}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if suite.pythonpath:
        env["PYTHONPATH"] = os.pathsep.join(str(tree / p) for p in suite.pythonpath)
    else:
        env.pop("PYTHONPATH", None)
    return env


def _pytest(tree: Path, suite: Suite, selection: tuple[str, ...], junit: Path, log: Path, *, ci_lane: bool) -> int:
    marker = ("-m", suite.ci_marker) if ci_lane and suite.ci_marker else ()
    cmd = [suite.python, "-m", "pytest", "-p", "no:cacheprovider", f"--junitxml={junit}", *marker, *selection]
    with log.open("w") as fh:
        return subprocess.run(cmd, cwd=tree / suite.cwd, env=_env(tree, suite), stdout=fh, stderr=subprocess.STDOUT, check=False).returncode


def _results(junit: Path) -> dict[str, tuple[str, str]]:
    """node id -> (outcome, message). Outcome is passed / failed / skipped."""
    out: dict[str, tuple[str, str]] = {}
    for case in ET.parse(junit).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        outcome, message = "passed", ""
        for tag in ("failure", "error"):
            element = case.find(tag)
            if element is not None:
                outcome, message = "failed", (element.get("message") or "") + "\n" + (element.text or "")
        if case.find("skipped") is not None:
            outcome = "skipped"
        out[node] = (outcome, message)
    return out


def _summary(results: dict[str, tuple[str, str]]) -> str:
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    for outcome, _message in results.values():
        counts[outcome] += 1
    return f"{counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped ({len(results)} collected)"


def _copy_tree(root: Path, suite: Suite, dest: Path) -> None:
    for rel in suite.copy:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, dest / rel, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))
        else:
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel)


def _apply(tree: Path, mutation: Mutation) -> None:
    target = tree / mutation.path
    text = target.read_text(encoding="utf-8")
    for old, new, count in mutation.edits:
        found = text.count(old)
        if found != count:
            raise SystemExit(f"REFUSED {mutation.mutation_id}: expected {count} occurrence(s) of {old!r} in {mutation.path}, found {found}")
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")


def _check(mutation: Mutation, results: dict[str, tuple[str, str]]) -> list[str]:
    problems = []
    for spec in mutation.expect:
        mode, substr = spec.split(":", 1)
        matching = {node: r for node, r in results.items() if substr in node}
        if not matching:
            problems.append(f"no collected test matches {substr!r}")
            continue
        failed = [node for node, (outcome, _m) in matching.items() if outcome == "failed"]
        if mode == "all" and len(failed) != len(matching):
            problems.append(f"{substr}: only {len(failed)}/{len(matching)} failed")
        if mode == "any" and not failed:
            problems.append(f"{substr}: none of {len(matching)} failed")
    messages = "\n".join(m for outcome, m in results.values() if outcome == "failed")
    for needle in mutation.expect_messages:
        if needle not in messages:
            problems.append(f"no failure message mentions {needle!r}")
    return problems


def cmd_run(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    root = Path(args.root).resolve()
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    selection = tuple(args.select) if args.select else suite.full
    lane = "-ci" if args.ci_lane else ""
    junit, log = scratch / f"run-{args.suite}{lane}.xml", scratch / f"run-{args.suite}{lane}.log"
    rc = _pytest(root, suite, selection, junit, log, ci_lane=args.ci_lane)
    marker = f" -m {suite.ci_marker!r}" if args.ci_lane and suite.ci_marker else ""
    print(f"[run {args.suite}] {root} {' '.join(selection)}{marker} -> exit {rc}: {_summary(_results(junit))} (log {log})")
    return rc


def cmd_baseline(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    root = Path(args.root).resolve()
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix=f"base-{args.suite}-") as tmp:
        tree = Path(tmp)
        paths = () if suite.baseline_whole_tree else suite.copy
        archive = subprocess.run(["git", "-C", str(root), "archive", args.ref, *paths], check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(tree)], input=archive, check=True)
        selection = tuple(args.select) if args.select else suite.full
        lane = "-ci" if args.ci_lane else ""
        junit, log = scratch / f"baseline-{args.suite}{lane}.xml", scratch / f"baseline-{args.suite}{lane}.log"
        rc = _pytest(tree, suite, selection, junit, log, ci_lane=args.ci_lane)
        marker = f" -m {suite.ci_marker!r}" if args.ci_lane and suite.ci_marker else ""
        print(f"[baseline {args.suite}] {args.ref} {' '.join(selection)}{marker} -> exit {rc}: {_summary(_results(junit))} (log {log})")
    return rc


def cmd_mutate(args: argparse.Namespace) -> int:
    suite = SUITES[args.suite]
    root = Path(args.root).resolve()
    scratch = Path(args.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    verdicts = []
    for mutation in (None, *suite.mutations):
        label = "UNMUTATED" if mutation is None else mutation.mutation_id
        with tempfile.TemporaryDirectory(dir=scratch, prefix=f"mut-{args.suite}-") as tmp:
            tree = Path(tmp)
            _copy_tree(root, suite, tree)
            if mutation is not None:
                _apply(tree, mutation)
            junit, log = scratch / f"mut-{args.suite}-{label}.xml", scratch / f"mut-{args.suite}-{label}.log"
            rc = _pytest(tree, suite, suite.targeted, junit, log, ci_lane=True)
            results = _results(junit)
        if mutation is None:
            ok = rc == 0 and all(outcome != "failed" for outcome, _m in results.values())
            print(f"[{args.suite}] UNMUTATED copy -> exit {rc}: {_summary(results)} -> {'OK' if ok else 'HARNESS BROKEN'}")
            if not ok:
                return 2
            continue
        problems = _check(mutation, results)
        verdicts.append(not problems)
        state = "CAUGHT" if not problems else "NOT CAUGHT: " + "; ".join(problems)
        print(f"[{args.suite}] {mutation.mutation_id} ({mutation.summary}) -> exit {rc}: {_summary(results)} -> {state}")
    return 0 if all(verdicts) else 1


def cmd_markers(args: argparse.Namespace) -> int:
    """Apply the fork-drift gate's OWN matcher to the given checkouts, not the ecosystem root's.

    Run with ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``, ``tests/test_service_fork_drift.py`` reads the
    sibling repos from the directory it finds by walking UP from juniper-ml -- the primary
    checkouts, on ``main`` -- so it cannot see a branch's edits in a task worktree. This loads the
    gate's ``GUARDS`` and ``guard_is_present`` and points each site at the checkout named here.
    """
    import importlib.util

    ml_root = Path(args.ml_root).resolve()
    roots = {"juniper-ml": ml_root}
    for repo, value in (("juniper-data", args.data_root), ("juniper-cascor", args.cascor_root), ("juniper-canopy", args.canopy_root)):
        if value:
            roots[repo] = Path(value).resolve()
    spec = importlib.util.spec_from_file_location("service_fork_drift_gate", ml_root / "tests" / "test_service_fork_drift.py")
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(gate)
    missing = 0
    for guard in gate.GUARDS:
        for site in guard.sites:
            if site.repo not in roots:
                continue
            source = (roots[site.repo] / site.path).read_text(encoding="utf-8")
            present = gate.guard_is_present(source, site)
            missing += 0 if present else 1
            state = "PRESENT" if present else "MISSING"
            print(f"{state:8} {guard.status:9} {guard.guard_id:28} {site.repo}/{site.path}  {list(site.markers)}")
    return 1 if missing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    markers = sub.add_parser("markers", help="check the fork-drift gate's markers in the named checkouts")
    markers.add_argument("--ml-root", required=True)
    markers.add_argument("--data-root")
    markers.add_argument("--cascor-root")
    markers.add_argument("--canopy-root")
    markers.set_defaults(func=cmd_markers)
    for name, func in (("run", cmd_run), ("baseline", cmd_baseline), ("mutate", cmd_mutate)):
        p = sub.add_parser(name)
        p.add_argument("--suite", required=True, choices=sorted(SUITES))
        p.add_argument("--root", required=True, help="checkout holding the suite (the repo root; juniper-ml's for observability and service-core)")
        p.add_argument("--scratch", required=True, help="directory for scratch copies, junit XML and logs")
        if name != "mutate":
            p.add_argument("--select", nargs="*", help="override the suite's test selection")
            p.add_argument("--ci-lane", action="store_true", help="apply the owning repo's CI marker expression (data, cascor)")
        if name == "baseline":
            p.add_argument("--ref", default="origin/main")
        p.set_defaults(func=func)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
