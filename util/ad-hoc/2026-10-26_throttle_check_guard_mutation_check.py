#!/usr/bin/env python3
"""Prove the ``throttle-check-never-inserts`` fork-drift guard is not vacuous (APD-ECO-015).

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (non-vacuity check for a new drift-gate guard)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-26
Status:      ad-hoc -- investigation; reads this checkout, fetches sibling files by SHA, writes only under $TMPDIR
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     APD-ECO-015, APD-ML-008; tests/test_service_fork_drift.py;
             notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md

The guard watches ``FailedAuthThrottle.check()`` in three copies: juniper-service-core (in this
repo), juniper-cascor and juniper-data. This script runs the REAL test module, with its cross-repo
arms switched on (``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1``), on a synthetic ecosystem root that holds
exactly the files the gate reads, and requires three things:

1. CONTROL. Every site at its current state passes, and nothing is skipped. Service-core is read
   from this checkout; each sibling is fetched at ``--main-ref`` (default ``main``).
2. PRE-FIX. Each copy's ``security.py`` at the parent of its fixing squash commit (juniper-ml#2187,
   juniper-cascor#710, juniper-data#476) fails the gate, and the only guard any failure names is this
   one, at that copy.
3. MARKER-PRESERVING MUTATIONS, the ``APD-ML-008`` class, each applied to each copy's current file.
   Every one must fail the gate the same way. The same marker matched over the WHOLE file -- the form
   the gate's other guards use -- is evaluated beside it and is expected to pass every one, which is
   the vacuity the scope exists to remove.

Sibling files are fetched by commit SHA with ``gh api``. No checkout is written.

Measured 2026-10-26, against juniper-cascor ``5b7d10dc``, juniper-data ``97c5aeb8`` and juniper-canopy
``da08414f``, under Python 3.12 and 3.14: the control passed (17 tests, none skipped); each of the three
pre-fix copies failed the gate, with this guard the only one named; all 21 mutations failed it; and the
whole-file form passed all 21. On the pre-fix copies the whole-file form fails too, because there
``record_failure()`` used the subscript as well -- the scope earns its keep on the half-reverts.

Usage: python3 util/ad-hoc/2026-10-26_throttle_check_guard_mutation_check.py [--main-ref main]
Exit 0 when every expectation holds, 1 otherwise.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_REL = Path("tests/test_service_fork_drift.py")
GUARD_ID = "throttle-check-never-inserts"
OWNER = "pcalnon"
SELF = "juniper-ml"

#: The squash commit that fixed each copy, and its PR. The commit's only parent is the pre-fix state.
FIXES = {
    "juniper-ml": ("3a6b39abdd2eb36e293c46b4cd33378ab2ac665f", "juniper-ml#2187"),
    "juniper-cascor": ("3d49f0f83930785109ef2b7f33ae4969eb4e5010", "juniper-cascor#710"),
    "juniper-data": ("1b48e1b7a406bcea8060af17804fdc48fbc84bbf", "juniper-data#476"),
}

# check()'s read and the two lines after it. record_failure() makes the same read, but follows it
# with a write, so these three lines occur once per file: in check().
CHECK_READ = "            count, window_start = self._failures.get(client_ip, (0, 0.0))\n            if now - window_start >= self._window:\n                return (False, 0)"
SUBSCRIPT_READ = CHECK_READ.replace("self._failures.get(client_ip, (0, 0.0))", "self._failures[client_ip]")
# The close of check()'s docstring and its first statement; record_failure() returns a bare None.
CHECK_DOC_CLOSE = '        """\n        if not self._enabled:\n            return (False, 0)\n'
PLAIN_DICT = "self._failures: dict[str, tuple[int, float]] = {}"
DEFAULTDICT = "self._failures: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))"
RECORD_FAILURE_DEF = "    def record_failure(self, client_ip: str) -> None:\n"


class AnchorError(ValueError):
    """A mutation's anchor did not occur exactly once, so the mutation was not applied."""


def _once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AnchorError(f"anchor occurs {count} times, expected 1: {old[:70]!r}")
    return text.replace(old, new)


def _with_defaultdict(text: str) -> str:
    """Restore the pre-fix ``defaultdict`` table, re-importing it where the fix dropped the import."""
    text = _once(text, PLAIN_DICT, DEFAULTDICT)
    if "from collections import defaultdict" not in text:
        text = _once(text, "\nimport time\n", "\nimport time\nfrom collections import defaultdict\n")
    return text


def m_check_reverted(text: str) -> str:
    """check() alone goes back to the pre-fix defaultdict subscript; record_failure() keeps .get()."""
    return _once(_with_defaultdict(text), CHECK_READ, SUBSCRIPT_READ)


def m_setdefault(text: str) -> str:
    """The table stays a plain dict, read with setdefault() -- which inserts as the defaultdict did."""
    return _once(text, CHECK_READ, CHECK_READ.replace(".get(client_ip, (0, 0.0))", ".setdefault(client_ip, (0, 0.0))"))


def m_get_kept_then_written(text: str) -> str:
    """check() keeps its .get() read, so the marker stays, and writes the entry straight back."""
    first, rest = CHECK_READ.split("\n", 1)
    return _once(text, CHECK_READ, first + "\n            self._failures[client_ip] = (count, window_start)\n" + rest)


def m_marker_in_docstring(text: str) -> str:
    """The pre-fix subscript, with the .get() marker moved into check()'s docstring."""
    text = _once(_with_defaultdict(text), CHECK_READ, SUBSCRIPT_READ)
    return _once(text, CHECK_DOC_CLOSE, "        Reads self._failures.get(client_ip, (0, 0.0)).\n" + CHECK_DOC_CLOSE)


def m_marker_in_comment(text: str) -> str:
    """The pre-fix subscript, with the .get() read left above it as a comment."""
    return _once(_with_defaultdict(text), CHECK_READ, "            # count, window_start = self._failures.get(client_ip, (0, 0.0))\n" + SUBSCRIPT_READ)


def m_get_in_dead_code(text: str) -> str:
    """The .get() read survives in an unreachable branch; the live read is the pre-fix subscript."""
    first, rest = SUBSCRIPT_READ.split("\n", 1)
    dead = "            if False:\n                count, window_start = self._failures.get(client_ip, (0, 0.0))\n"
    return _once(_with_defaultdict(text), CHECK_READ, dead + first + "\n" + rest)


def m_shadowing_check(text: str) -> str:
    """A second check() defined below the fixed one; Python binds the later definition."""
    shadow = "    def check(self, client_ip: str) -> tuple[bool, int]:\n        count, window_start = self._failures[client_ip]\n        return (count >= self._max_failures, 0)\n\n"
    return _once(_with_defaultdict(text), RECORD_FAILURE_DEF, shadow + RECORD_FAILURE_DEF)


MUTATIONS = (
    ("M1", "check() reverted, record_failure() kept", m_check_reverted),
    ("M2", "setdefault() on a plain dict", m_setdefault),
    ("M3", ".get() kept, entry written back", m_get_kept_then_written),
    ("M4", "marker moved into the docstring", m_marker_in_docstring),
    ("M5", "marker left as a comment", m_marker_in_comment),
    ("M6", ".get() left in dead code", m_get_in_dead_code),
    ("M7", "a later check() shadows the fixed one", m_shadowing_check),
)


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _commit_sha(repo: str, ref: str) -> str:
    return _gh("api", f"repos/{OWNER}/{repo}/commits/{ref}", "--jq", ".sha").strip()


def _parents(repo: str, sha: str) -> list[str]:
    return _gh("api", f"repos/{OWNER}/{repo}/commits/{sha}", "--jq", ".parents[].sha").split()


def _file_at(repo: str, path: str, sha: str) -> str:
    return _gh("api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{repo}/contents/{path}?ref={sha}")


def _load_gate():
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
    result = subprocess.run([sys.executable, "-m", "unittest", "-v", str(TEST_REL)], cwd=ml_root, env=env, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout + result.stderr


def _verdict(output: str) -> str:
    ran = re.findall(r"^Ran (\d+) tests?", output, flags=re.MULTILINE)
    tail = re.findall(r"^(OK.*|FAILED \(.*\))$", output, flags=re.MULTILINE)
    return f"ran {ran[-1] if ran else '?'}, {tail[-1] if tail else 'no verdict line'}"


def _caught(code: int, output: str, repo: str, path: str) -> tuple[bool, str]:
    """The run failed, nothing skipped, only this guard named, and named at this copy."""
    named = set(re.findall(r"Guard '([a-z0-9-]+)'", output))
    at_site = [line for line in output.splitlines() if f"Guard '{GUARD_ID}'" in line and (f"{repo}/{path}" in line or (repo == SELF and f"shared package's {path}" in line))]
    if code == 0:
        return False, "gate PASSED"
    if "skipped" in _verdict(output):
        return False, f"skips present ({_verdict(output)})"
    if named != {GUARD_ID}:
        return False, f"guards named: {sorted(named)}"
    if not at_site:
        return False, "failure does not name this copy"
    return True, _verdict(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    parser.add_argument("--main-ref", default="main", help="ref of each sibling repo to treat as current (default: main)")
    args = parser.parse_args(argv)

    gate = _load_gate()
    guard = next(g for g in gate.GUARDS if g.guard_id == GUARD_ID)
    watched = [(site.repo, site.path, site.markers) for site in guard.sites]
    reads = sorted({(site.repo, site.path) for g in gate.GUARDS for site in g.sites})
    siblings = sorted({repo for repo, _ in reads if repo != SELF})
    shas = {repo: _commit_sha(repo, args.main_ref) for repo in siblings}
    current = {(repo, path): (ROOT / path).read_text(encoding="utf-8") if repo == SELF else _file_at(repo, path, shas[repo]) for repo, path in reads}
    test_source = (ROOT / TEST_REL).read_text(encoding="utf-8")
    print(f"gate under test: {ROOT / TEST_REL}")
    print("current state: " + ", ".join([f"{SELF} = this checkout"] + [f"{repo} @ {shas[repo][:8]}" for repo in siblings]))

    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="throttle-guard-nonvacuity-") as scratch:
        code, output = _run_gate(Path(scratch) / "control", current, test_source)
        control_ok = code == 0 and _verdict(output).endswith(", OK")
        print(f"\nCONTROL (every site current): {'PASS' if control_ok else 'FAIL'} -- {_verdict(output)}")
        if not control_ok:
            problems.append("control did not pass cleanly")
            print(output[-3000:])

        print("\nPRE-FIX COPIES (parent of each fixing squash commit) -- expected FAIL, attributed to the guard")
        for repo, path, markers in watched:
            fix_sha, pr = FIXES[repo]
            parents = _parents(repo, fix_sha)
            if len(parents) != 1:
                problems.append(f"{pr}: {fix_sha[:8]} has {len(parents)} parents, expected a squash commit")
                continue
            before = _file_at(repo, path, parents[0])
            if before == _file_at(repo, path, fix_sha):
                problems.append(f"{pr}: {path} is identical before and after {fix_sha[:8]}")
                continue
            code, output = _run_gate(Path(scratch) / f"prefix-{repo}", {**current, (repo, path): before}, test_source)
            ok, why = _caught(code, output, repo, path)
            whole_file = gate.guard_is_present(before, gate.ForkSite(repo, path, markers))
            print(f"  {repo:15} {path:58} @ {parents[0][:8]} ({pr}^): {'FAIL (caught)' if ok else 'NOT CAUGHT'} -- {why}; whole-file form: {'PASS' if whole_file else 'FAIL'}")
            if not ok:
                problems.append(f"pre-fix {repo}: {why}")

        print("\nMARKER-PRESERVING MUTATIONS of each current copy -- the gate must FAIL; the whole-file form is shown beside it")
        for mutation_id, name, mutate in MUTATIONS:
            for repo, path, markers in watched:
                label = f"  {mutation_id} {name:40} {repo:15}"
                try:
                    mutated = mutate(current[(repo, path)])
                except AnchorError as exc:
                    problems.append(f"{mutation_id} {repo}: {exc}")
                    print(f"{label} ANCHOR-MISMATCH -- {exc}")
                    continue
                code, output = _run_gate(Path(scratch) / f"{mutation_id}-{repo}", {**current, (repo, path): mutated}, test_source)
                ok, why = _caught(code, output, repo, path)
                whole_file = gate.guard_is_present(mutated, gate.ForkSite(repo, path, markers))
                print(f"{label} gate: {'FAIL (caught)' if ok else 'NOT CAUGHT'} -- {why}; whole-file form: {'PASS (vacuous)' if whole_file else 'FAIL'}")
                if not ok:
                    problems.append(f"{mutation_id} {repo}: {why}")
                if not whole_file:
                    problems.append(f"{mutation_id} {repo}: the whole-file form caught it too, so the mutation does not show what the scope adds")

    if problems:
        print("\nFAIL:\n  " + "\n  ".join(problems))
        return 1
    print(f"\nPASS: control green; {len(watched)} pre-fix copies and {len(MUTATIONS) * len(watched)} mutations each caught and attributed to '{GUARD_ID}'; the whole-file form passed every mutation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
