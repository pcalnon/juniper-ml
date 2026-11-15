#!/usr/bin/env python3
"""
Prove the ``retry-after-rounds-up`` fork-drift guard is not vacuous (APD-ECO-016).

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Updated: 2026-11-15 -- findings 4, 12 and 13 of the round-1 review: forbidden-form mutations, attribution by scope, a
         scratch directory that is removed. The review is
         .claude/worktrees/toasty-prancing-karp/tmp/s1/guard_review_round1.md in the juniper-ml primary (gitignored;
         sha256 37508e487e0eda0068a749aea2528cdfe55066737311a4a20f7a7358aa8e9dc8), retained under the tmp/ retention rule
         until plan v1.15.16 archives it. A second review then asked for asserted totals (EXPECTED below).
Status: ad-hoc -- investigation; reads this checkout, reads sibling files from GitHub by SHA or from named local
        trees, writes only under a scratch directory
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-ECO-016, APD-SVCCORE-004, APD-ML-008; tests/test_service_fork_drift.py;
         notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md;
         util/ad-hoc/2026-10-26_throttle_check_guard_mutation_check.py (the pattern)

The guard reads three definitions in each copy of the service-tier security code -- ``RateLimiter._seconds_until_reset``,
``RateLimiter.check`` and ``FailedAuthThrottle.check`` -- in juniper-service-core (this repo), juniper-data and
juniper-cascor, and the first two in juniper-canopy, which has no throttle. This script runs the REAL test module, with
its cross-repo arms switched on (``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``), on a synthetic ecosystem root that holds exactly
the files the gate reads, and requires four things:

1. CONTROL. Every site at its current state passes, and nothing is skipped. Service-core is read from this checkout.
   Each sibling is read from GitHub at ``--main-ref`` (default ``main``), or from a local tree named with
   ``--tree REPO=DIR`` (how the guard was checked before the fork fixes had merged).
2. PRE-FIX. Each copy's ``security.py`` before its fix fails the gate, and every failure names this guard at that copy.
   No other guard is named, except for the parent of juniper-ml#1300: that file is from 2026-08-24 and predates two
   other guards' fixes, so the gate rightly names them too. The shared package has two pre-fix states, the parents of
   juniper-ml#1300 (the limiter) and of juniper-ml#2524 (the throttle). A sibling's pre-fix state is the commit named
   with ``--prefix REPO=SHA``.
3. MUTATIONS of each current copy (R, M and T). Each is a wrong rounding or a bypass a regression could plausibly write,
   except R3 and T4, which drop the floor of 1: no reachable result changes, because ``check`` rolls a window over
   before the remainder can reach 0, but the code is no longer the canonical formula the guard pins. Every one must fail
   the gate, attributed to this guard at that copy, and at the one scope the mutation edits. The same markers matched
   over the WHOLE file, the form the gate's unscoped guards use, are evaluated beside each and reported: wherever a copy
   has a throttle, a regression confined to the limiter keeps the throttle's ``max(1, math.ceil(`` text in the file,
   which is why the sites are scoped.
4. FORBIDDEN FORMS (F). For each of the guard's forbidden forms, in each scope of each copy, a mutation that keeps the
   scope's markers and adds a return through that form: in the helper and the throttle the marker survives in a branch
   that is never taken, and in ``check`` an extra early return rounds its own way. Before running the gate, each is
   checked in memory: the markers still hold, that form is the only forbidden one in the scope, and with that one entry
   removed from the list every site of the copy passes. The gate must then fail at that scope and name that form. So
   each entry of the list is shown to be load-bearing in each scope, where the markers alone catch nothing.

The run also requires the totals in ``EXPECTED``: 11 sites in 4 copies, 5 pre-fix copies, and 151 mutations, 88 of them
F. A site, copy or mutation that drops out therefore fails the run instead of shrinking its PASS line.

The scratch directory is a new temporary one, removed when the run ends, unless ``--scratch DIR`` names one to keep.
Either way its path is printed.

Usage
-----
    python3 util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py \
        --prefix juniper-data=SHA --prefix juniper-cascor=SHA --prefix juniper-canopy=SHA \
        [--main-ref main] [--tree REPO=DIR ...] [--scratch DIR]

Exit 0 when every expectation holds, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib.util
import os
import re
import subprocess  # nosec B404 -- runs gh and the unittest module in argv form, no shell
import sys
import tempfile
from pathlib import Path
from typing import Callable, NamedTuple

ROOT = Path(__file__).resolve().parents[2]
TEST_REL = Path("tests/test_service_fork_drift.py")
GUARD_ID = "retry-after-rounds-up"
OWNER = "pcalnon"
SELF = "juniper-ml"
HELPER_SCOPE = "RateLimiter._seconds_until_reset"
CHECK_SCOPE = "RateLimiter.check"
THROTTLE_SCOPE = "FailedAuthThrottle.check"

#: The totals a complete run reaches. Without them a dropped site, copy or mutation would only shrink the PASS line.
#: A real change to the guard (canopy gaining a throttle, say) must update them with it.
EXPECTED = {"sites": 11, "copies": 4, "pre-fix copies": 5, "mutations": 151, "forbidden-form mutations": 88}

#: The shared package's two fixing squash commits; each one's only parent is a pre-fix state. The third field says
#: whether this guard must be the ONLY one a failure names. It cannot be for the parent of juniper-ml#1300: that file
#: is from 2026-08-24 and predates two other guards' fixes, so the gate rightly names those as well.
SELF_FIXES = (
    ("4652afe380b789eaa62a26b922fa2d11eaee2c68", "juniper-ml#1300 (the limiter, APD-SVCCORE-004)", False),
    ("93fa1f66215fe7cb266585b448959d58c606bfe7", "juniper-ml#2524 (the throttle; first released in 0.7.2)", True),
)

# The four statements every fixed copy carries, byte for byte.
HELPER = "        return max(1, math.ceil(self._window - (now - window_start)))\n"
REJECT = "                return (False, 0, self._seconds_until_reset(now, window_start))\n"
ALLOW = "            return (True, self._limit - count - 1, self._seconds_until_reset(now, window_start))\n"
THROTTLE = "                return (True, max(1, math.ceil(remaining)))\n"
CHECK_DEF = "    def check(self, key: str) -> tuple[bool, int, int]:\n"
_TRUNCATED = "int(self._window - (now - window_start))"
_SHADOW = "    def _seconds_until_reset(self, now: float, window_start: float) -> int:\n        return " + _TRUNCATED + "\n\n"


class AnchorError(ValueError):
    """A mutation's anchor did not occur exactly once, so the mutation was not applied."""


class Mutation(NamedTuple):
    """One edit of a current copy: the scope it breaks, and the forbidden form it adds (F mutations only)."""

    mutation_id: str
    name: str
    mutate: Callable[[str], str]
    scope: str
    forbidden: str | None = None


def _once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AnchorError(f"anchor occurs {count} times, expected 1: {old.strip()[:70]!r}")
    return text.replace(old, new)


def _swap(old: str, new: str):
    return lambda text: _once(text, old, new)


#: R, M and T: (id, what a regression would have written, the edit, the scope it breaks).
MUTATIONS = [
    Mutation("R1", "helper truncates (the defect)", _swap(HELPER, "        return " + _TRUNCATED + "\n"), HELPER_SCOPE),
    Mutation("R2", "helper: a floor of 1 over truncation", _swap(HELPER, "        return max(1, " + _TRUNCATED + ")\n"), HELPER_SCOPE),
    Mutation("R3", "helper: ceil without the floor", _swap(HELPER, "        return math.ceil(self._window - (now - window_start))\n"), HELPER_SCOPE),
    Mutation("R4", "helper: always add one", _swap(HELPER, "        return " + _TRUNCATED + " + 1\n"), HELPER_SCOPE),
    Mutation("R5", "helper: round to nearest", _swap(HELPER, "        return max(1, round(self._window - (now - window_start)))\n"), HELPER_SCOPE),
    Mutation("R6", "check: the rejection return truncates", _swap(REJECT, "                return (False, 0, " + _TRUNCATED + ")\n"), CHECK_SCOPE),
    Mutation("R7", "check: the allowed return truncates", _swap(ALLOW, "            return (True, self._limit - count - 1, " + _TRUNCATED + ")\n"), CHECK_SCOPE),
    Mutation("R8", "check: the rejection return skips the helper", _swap(REJECT, "                return (False, 0, self._window - (now - window_start))\n"), CHECK_SCOPE),
    Mutation("R9", "check: the allowed return skips the helper", _swap(ALLOW, "            return (True, self._limit - count - 1, self._window - (now - window_start))\n"), CHECK_SCOPE),
    Mutation("M1", "helper truncates, the formula left as a comment", _swap(HELPER, "        # return max(1, math.ceil(self._window - (now - window_start)))\n        return " + _TRUNCATED + "\n"), HELPER_SCOPE),
    Mutation("M2", "helper truncates, the formula left in dead code", _swap(HELPER, "        if False:\n            return max(1, math.ceil(self._window - (now - window_start)))\n        return " + _TRUNCATED + "\n"), HELPER_SCOPE),
    Mutation("M3", "a later _seconds_until_reset shadows the fixed one", _swap(CHECK_DEF, _SHADOW + CHECK_DEF), HELPER_SCOPE),
    Mutation("T1", "throttle: a floor of 1 over truncation (the old code)", _swap(THROTTLE, "                return (True, max(1, int(remaining)))\n"), THROTTLE_SCOPE),
    Mutation("T2", "throttle: always add one", _swap(THROTTLE, "                return (True, int(remaining) + 1)\n"), THROTTLE_SCOPE),
    Mutation("T3", "throttle: round to nearest", _swap(THROTTLE, "                return (True, max(1, round(remaining)))\n"), THROTTLE_SCOPE),
    Mutation("T4", "throttle: ceil without the floor", _swap(THROTTLE, "                return (True, math.ceil(remaining))\n"), THROTTLE_SCOPE),
    Mutation("T5", "throttle truncates, the formula left as a comment", _swap(THROTTLE, "                # return (True, max(1, math.ceil(remaining)))\n                return (True, max(1, int(remaining)))\n"), THROTTLE_SCOPE),
]

#: Each forbidden form, spelled so that it is the only entry of the guard's forbidden list its return holds: the two
#: forms that name their operand sit inside a list display, where no space or parenthesis precedes ``int(``.
#: ``_check`` compares the list here with the gate's, so a form added to the gate without a mutation fails the run.
FORBIDDEN_FORMS = (
    ("int(self._window", "[int(self._window - (now - window_start))][0]"),
    ("int(remaining", "[int(remaining)][0]"),
    (" int(", "max(1, int(left))"),
    ("(int(", "max(1, abs(int(left)))"),
    ("//", "max(1, left // 1)"),
    ("math.floor(", "max(1, math.floor(left))"),
    ("math.trunc(", "max(1, math.trunc(left))"),
    ("round(", "max(1, round(left))"),
)


def _forbidden_form_mutations() -> list[Mutation]:
    """F: in each scope, the markers kept beside a return through one forbidden form."""
    out: list[Mutation] = []
    for number, (form, wrong) in enumerate(FORBIDDEN_FORMS, start=1):
        # The local the scope rounds. The throttle already has ``remaining``; the helper and ``check`` define it when the
        # form names it, and ``left`` otherwise, so that no other entry of the list is spelled by accident.
        local = "remaining" if "remaining" in wrong else "left"
        helper = f"        {local} = self._window - (now - window_start)\n        if {local} <= 0:\n            return max(1, math.ceil({local}))\n        return {wrong}\n"
        check = f"                {local} = self._window - (now - window_start)\n                if {local} > 1:\n                    return (False, 0, {wrong})\n" + REJECT
        throttle = f"                left = remaining\n                if left <= 0:\n                    return (True, max(1, math.ceil(left)))\n                return (True, {wrong})\n"
        out.append(Mutation(f"FH{number}", f"helper: the marker in a branch never taken, returns {form!r}", _swap(HELPER, helper), HELPER_SCOPE, form))
        out.append(Mutation(f"FC{number}", f"check: an early rejection return through {form!r}", _swap(REJECT, check), CHECK_SCOPE, form))
        out.append(Mutation(f"FT{number}", f"throttle: the marker in a branch never taken, returns {form!r}", _swap(THROTTLE, throttle), THROTTLE_SCOPE, form))
    return out


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout  # nosec B603 B607


def _commit_sha(repo: str, ref: str) -> str:
    return _gh("api", f"repos/{OWNER}/{repo}/commits/{ref}", "--jq", ".sha").strip()


def _parents(repo: str, sha: str) -> list[str]:
    return _gh("api", f"repos/{OWNER}/{repo}/commits/{sha}", "--jq", ".parents[].sha").split()


def _file_at(repo: str, path: str, sha: str) -> str:
    return _gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{repo}/contents/{path}?ref={sha}")


def _load_gate():
    # Loading the module would otherwise leave a tests/__pycache__/*.pyc in this checkout, outside the scratch directory.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("service_fork_drift_gate", ROOT / TEST_REL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # @dataclass resolves its module through sys.modules
    spec.loader.exec_module(module)
    return module


def _run_gate(parent: Path, files: dict[tuple[str, str], str], test_source: str) -> tuple[int, str]:
    """Lay ``files`` out as an ecosystem root under ``parent`` and run the real gate in it."""
    eco = parent / "eco"
    for (repo, path), text in files.items():
        target = eco / repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    ml_root = eco / SELF
    (ml_root / TEST_REL).parent.mkdir(parents=True, exist_ok=True)
    (ml_root / TEST_REL).write_text(test_source, encoding="utf-8")
    env = dict(os.environ, JUNIPER_DRIFT_TEST_FORCE_LOCAL="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-m", "unittest", "-v", str(TEST_REL)], cwd=ml_root, env=env, capture_output=True, text=True, check=False)  # nosec B603
    return result.returncode, result.stdout + result.stderr


def _verdict(output: str) -> str:
    ran = re.findall(r"^Ran (\d+) tests?", output, flags=re.MULTILINE)
    tail = re.findall(r"^(OK.*|FAILED \(.*\))$", output, flags=re.MULTILINE)
    return f"ran {ran[-1] if ran else '?'}, {tail[-1] if tail else 'no verdict line'}"


def _failing_scopes(output: str, repo: str) -> set[str | None]:
    """The scopes of this guard's failing subtests at ``repo``, read from unittest's ``FAIL:`` / ``ERROR:`` headers.

    The gate's site loops key each subtest by guard, repo and scope (finding 13 of the round-1 review named in the module
    docstring, ``guard_review_round1.md``), so a header reads
    ``FAIL: test_... (...) (guard='...', repo='...', scope='...')``. ``SharedPackageGuardTest``'s subtests carry no repo
    key, because every site they read is the shared package's.
    """
    scopes: set[str | None] = set()
    for line in output.splitlines():
        if not line.startswith(("FAIL: ", "ERROR: ")):
            continue
        params = dict(re.findall(r"(\w+)=('[^']*'|None)", line))
        if params.get("guard") != repr(GUARD_ID) or params.get("repo", repr(SELF)) != repr(repo):
            continue
        scopes.add(ast.literal_eval(params.get("scope", "None")))
    return scopes


def _caught(code: int, output: str, repo: str, path: str, exclusive: bool = True, scope: str | None = None, forbidden: str | None = None) -> tuple[bool, str]:
    """The run failed, nothing skipped, this guard named at this copy, and (when ``exclusive``) no other guard named.

    With ``scope``, this guard's failures at this copy must be at that scope and no other. With ``forbidden``, the
    gate's message must name that form, and only it, as the forbidden code it found there.
    """
    named = set(re.findall(r"Guard '([a-z0-9-]+)'", output))
    at_site = [line for line in output.splitlines() if f"Guard '{GUARD_ID}'" in line and (f"{repo}/{path}" in line or (repo == SELF and f"shared package's {path}" in line))]
    if code == 0:
        return False, "gate PASSED"
    if "skipped" in _verdict(output):
        return False, f"skips present ({_verdict(output)})"
    if GUARD_ID not in named or (exclusive and named != {GUARD_ID}):
        return False, f"guards named: {sorted(named)}"
    if not at_site:
        return False, "failure does not name this copy"
    if scope is not None:
        failing = _failing_scopes(output, repo)
        if failing != {scope}:
            return False, f"failing scopes {sorted(str(s) for s in failing)}, expected only {scope}"
    if forbidden is not None:
        message = f"the code of {scope} contains {[forbidden]!r}, which the guard forbids there"
        if not any(message in line for line in at_site):
            return False, f"no failure names {[forbidden]!r} as the forbidden code at {scope}"
    others = sorted(named - {GUARD_ID})
    return True, _verdict(output) + (f" at {scope}" if scope else "") + (f"; also named, as that file predates them: {others}" if others else "")


def _whole_file_form(gate, text: str, sites: list) -> bool:
    """Would the same markers, matched over the whole file with no scope and nothing forbidden, still pass?"""
    return all(gate.guard_is_present(text, gate.ForkSite(site.repo, site.path, site.markers)) for site in sites)


def _load_bearing(gate, text: str, sites: list, scope: str, form: str) -> tuple[bool, str]:
    """For an F mutation: the scope's markers hold, ``form`` is its only forbidden form, and without it every site passes."""
    target = next((site for site in sites if site.scope == scope), None)
    if target is None:
        return False, f"no site at {scope}"
    code = gate.site_code(text, target)
    if code is None:
        return False, f"{scope} not found, or the file does not parse"
    missing = [marker for marker in target.markers if marker not in code]
    if missing:
        return False, f"markers missing at {scope}, so they would catch it themselves: {missing}"
    present = [marker for marker in target.forbidden if marker in code]
    if present != [form]:
        return False, f"forbidden forms present at {scope}: {present}, expected only {[form]!r}"
    relaxed = [dataclasses.replace(site, forbidden=tuple(entry for entry in site.forbidden if entry != form)) for site in sites]
    if not all(gate.guard_is_present(text, site) for site in relaxed):
        return False, f"still caught with {form!r} removed from the list"
    return True, f"only {form!r} catches it"


def _pairs(items: list[str], flag: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        name, sep, value = item.partition("=")
        if not sep or not name or not value:
            raise SystemExit(f"{flag} wants REPO=VALUE, got {item!r}")
        out[name] = value
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").strip().split("\n", 1)[0])
    parser.add_argument("--main-ref", default="main", help="ref of each sibling repo to treat as current (default: main)")
    parser.add_argument("--tree", action="append", default=[], metavar="REPO=DIR", help="read this sibling's current files from a local tree instead of GitHub")
    parser.add_argument("--prefix", action="append", default=[], metavar="REPO=SHA", help="the commit holding this sibling's PRE-FIX security.py (required for every sibling)")
    parser.add_argument("--scratch", help="scratch directory to use and KEEP (default: a new temporary one, removed at the end)")
    args = parser.parse_args(argv)
    trees, prefixes = _pairs(args.tree, "--tree"), _pairs(args.prefix, "--prefix")

    gate = _load_gate()
    guard = next(g for g in gate.GUARDS if g.guard_id == GUARD_ID)
    copies: dict[tuple[str, str], list] = {}
    for site in guard.sites:
        copies.setdefault((site.repo, site.path), []).append(site)
    reads = sorted({(site.repo, site.path) for g in gate.GUARDS for site in g.sites})
    siblings = sorted({repo for repo, _ in reads if repo != SELF})
    missing = [repo for repo in sorted({repo for repo, _ in copies if repo != SELF}) if repo not in prefixes]
    if missing:
        parser.error(f"--prefix is required for: {', '.join(missing)}")
    shas = {repo: _commit_sha(repo, args.main_ref) for repo in siblings if repo not in trees}

    def current_file(repo: str, path: str) -> str:
        if repo == SELF:
            return (ROOT / path).read_text(encoding="utf-8")
        if repo in trees:
            return (Path(trees[repo]) / path).read_text(encoding="utf-8")
        return _file_at(repo, path, shas[repo])

    current = {(repo, path): current_file(repo, path) for repo, path in reads}
    test_source = (ROOT / TEST_REL).read_text(encoding="utf-8")
    print(f"gate under test: {ROOT / TEST_REL}")
    print("current state: " + ", ".join([f"{SELF} = this checkout"] + [f"{repo} = {trees[repo]}" if repo in trees else f"{repo} @ {shas[repo][:8]}" for repo in siblings]))
    print(f"guard '{GUARD_ID}': {len(guard.sites)} sites in {len(copies)} copies")

    if args.scratch:
        scratch = Path(args.scratch)
        scratch.mkdir(parents=True, exist_ok=True)
        print(f"scratch: {scratch} (kept)")
        return _check(gate, copies, current, test_source, prefixes, scratch)
    with tempfile.TemporaryDirectory(prefix="retry-after-guard-") as tmp:
        print(f"scratch: {tmp} (removed when the run ends)")
        return _check(gate, copies, current, test_source, prefixes, Path(tmp))


def _check(gate, copies: dict[tuple[str, str], list], current: dict[tuple[str, str], str], test_source: str, prefixes: dict[str, str], scratch: Path) -> int:
    problems: list[str] = []
    for what, found in (("sites", sum(len(sites) for sites in copies.values())), ("copies", len(copies))):
        if found != EXPECTED[what]:
            problems.append(f"the guard has {found} {what}, EXPECTED {EXPECTED[what]}")
    site_forms = {form for sites in copies.values() for site in sites for form in site.forbidden}
    script_forms = {form for form, _ in FORBIDDEN_FORMS}
    if script_forms != site_forms or script_forms != set(gate._WRONG_ROUNDINGS):
        problems.append(f"the F mutations cover {sorted(script_forms)}, but the guard's sites forbid {sorted(site_forms)}")

    code, output = _run_gate(scratch / "control", current, test_source)
    control_ok = code == 0 and _verdict(output).endswith(", OK")
    print(f"\nCONTROL (every site current): {'PASS' if control_ok else 'FAIL'} -- {_verdict(output)}")
    if not control_ok:
        problems.append("control did not pass cleanly")
        print(output[-3000:])

    print("\nPRE-FIX COPIES -- expected FAIL, attributed to the guard")
    prefix_cases: list[tuple[str, str, str, str, bool]] = []
    for (repo, path), _sites in sorted(copies.items()):
        if repo == SELF:
            for fix_sha, label, exclusive in SELF_FIXES:
                parents = _parents(repo, fix_sha)
                if len(parents) != 1:
                    problems.append(f"{label}: {fix_sha[:8]} has {len(parents)} parents, expected a squash commit")
                    continue
                prefix_cases.append((repo, path, parents[0], f"{label}^", exclusive))
        else:
            prefix_cases.append((repo, path, prefixes[repo], "--prefix", True))
    for repo, path, sha, label, exclusive in prefix_cases:
        before = _file_at(repo, path, sha)
        if before == current[(repo, path)]:
            problems.append(f"pre-fix {repo} @ {sha[:8]}: {path} equals the current copy")
            continue
        code, output = _run_gate(scratch / f"prefix-{repo}-{sha[:8]}", {**current, (repo, path): before}, test_source)
        ok, why = _caught(code, output, repo, path, exclusive)
        whole = _whole_file_form(gate, before, copies[(repo, path)])
        print(f"  {repo:15} @ {sha[:8]} ({label}): {'FAIL (caught)' if ok else 'NOT CAUGHT'} -- {why}; failing scopes: {sorted(str(s) for s in _failing_scopes(output, repo))}; whole-file form: {'PASS' if whole else 'FAIL'}")
        if not ok:
            problems.append(f"pre-fix {repo} @ {sha[:8]}: {why}")

    print("\nMUTATIONS of each current copy -- the gate must FAIL at the scope mutated; the whole-file form is shown beside it")
    print("(F: each forbidden form beside the kept markers; the gate must also name the form, and the list must need it)")
    ran = vacuous = forbidden_runs = 0
    for mutation in MUTATIONS + _forbidden_form_mutations():
        for (repo, path), sites in sorted(copies.items()):
            if not any(site.scope == mutation.scope for site in sites):
                continue
            label = f"  {mutation.mutation_id:4} {mutation.name:62} {repo:15}"
            try:
                mutated = mutation.mutate(current[(repo, path)])
            except AnchorError as exc:
                problems.append(f"{mutation.mutation_id} {repo}: {exc}")
                print(f"{label} ANCHOR-MISMATCH -- {exc}")
                continue
            bearing = ""
            if mutation.forbidden is not None:
                needed, why_needed = _load_bearing(gate, mutated, sites, mutation.scope, mutation.forbidden)
                bearing = f"; load-bearing: {'yes' if needed else 'NO'} ({why_needed})"
                if not needed:
                    problems.append(f"{mutation.mutation_id} {repo}: {why_needed}")
            code, output = _run_gate(scratch / f"{mutation.mutation_id}-{repo}", {**current, (repo, path): mutated}, test_source)
            ok, why = _caught(code, output, repo, path, scope=mutation.scope, forbidden=mutation.forbidden)
            whole = _whole_file_form(gate, mutated, sites)
            ran += 1
            vacuous += 1 if whole else 0
            forbidden_runs += 1 if mutation.forbidden is not None else 0
            print(f"{label} gate: {'FAIL (caught)' if ok else 'NOT CAUGHT'} -- {why}{bearing}; whole-file form: {'PASS (vacuous)' if whole else 'FAIL'}")
            if not ok:
                problems.append(f"{mutation.mutation_id} {repo}: {why}")

    for what, found in (("pre-fix copies", len(prefix_cases)), ("mutations", ran), ("forbidden-form mutations", forbidden_runs)):
        if found != EXPECTED[what]:
            problems.append(f"{found} {what} ran, EXPECTED {EXPECTED[what]}")
    if problems:
        print("\nFAIL:\n  " + "\n  ".join(problems))
        return 1
    print(f"\nPASS: control green; {len(prefix_cases)} pre-fix copies each caught and attributed to '{GUARD_ID}' at that copy, and {ran} mutations each caught at the one scope it edits; in {forbidden_runs} of the mutations a forbidden form beside the kept markers was the only thing that caught it, once per form per scope per copy; the whole-file form would have passed {vacuous} of the {ran} mutations; every total as EXPECTED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
