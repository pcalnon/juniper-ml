#!/usr/bin/env python3
"""P3-07 mutation check: each new test kills the mutant it targets, and the old suite did not.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use verification)
Author:      Paul Calnon
Version:     0.2.0
License:     MIT License

For each mutant, the package directory (``juniper-observability`` or ``juniper-service-core``)
is copied into ``--scratch``, exact text substitutions are applied to its source (each refused
unless its old text occurs exactly once), and the package's suite is run against the copy, which
``PYTHONPATH`` puts ahead of any editable install. Each run first proves the copy is what gets
imported. Every mutant runs twice:

- against the NEW tests (this branch): it must FAIL. A mutant with ``seeds`` runs once per
  ``PYTHONHASHSEED`` in it, and must fail under every one: those mutants walk the key set in an
  order that the hash seed decides, which is how a test can kill them in one run and miss them
  in the next.
- against the OLD tests (``--old-obs-test`` / ``--old-sc-test``, the test files as they are on
  ``main`` without P3-07): it must PASS for the mutants marked ``survived_old=True``. That is what
  makes each new test necessary, not decorative. The mark records a measurement, made by one of:

  - the round-42 validation (2026-09-24): the bytes ``==``, the ``break`` and UTF-16-LE;
  - P3-07's round-1 validation (2026-11-08): CM07, SM02/SM03, SM21/SM22 and SM26, each of which
    also passed that round's NEW suite;
  - P3-07's round-2 validation (2026-11-08): BS, S6 and S7, which passed that round's NEW suite;
  - this script's own runs (2026-11-08): O1-O3 and O5-O10, ``any()``, ``namereplace``, and
    SM06/SM07 (round 1 ran those two against its spy test alone, which they passed under 8 and
    12 of 30 hash seeds; it never ran the old suite on them), and O4, whose expectation the
    first run corrected.

  A passing OLD row shows only that ``main``'s tests miss the mutant. Which new test kills it
  is not recorded here; run the NEW suite on its copy without ``-x`` to see.

An unmutated copy runs first under both suites and must PASS, or nothing below means anything.

Exit status: 0 when every row matches its expectation, 1 when a row does not, 2 on a usage or
setup error (an interpreter that is missing or will not run, a mutant's text not found exactly
once, the copy not the module imported, pytest exiting with anything but 0 or 1).

Usage (from the juniper-ml worktree root):
    python3 util/ad-hoc/2026-11-08_p3_07_mutation_check.py --scratch <dir> \\
        --obs-python <venv>/bin/python --sc-python <venv>/bin/python \\
        --old-obs-test <file> --old-sc-test <file>
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_OBS = "juniper-observability"
_SC = "juniper-service-core"
_SENTRY = "juniper_observability/sentry.py"
_SECURITY = "juniper_service_core/security.py"

_SPY_TEST = "test_validate_compares_every_configured_key_through_compare_digest_as_bytes"
_MATRIX_TEST = "test_validate_matches_exactly_when_the_strings_are_equal"
_HASH_SEEDS = tuple(range(10))


class SetupError(Exception):
    """The check could not run as designed; no verdict below it would mean anything."""


@dataclasses.dataclass(frozen=True)
class Mutant:
    mutant_id: str
    package: str
    source: str  # path inside the package directory
    edits: tuple[tuple[str, str], ...]  # (old, new) pairs, applied in order
    targets: str  # the finding or fix it stands for
    survived_old: bool  # True: a measurement says the OLD suite passes it (see the module docstring)
    select: tuple[str, ...] = ()  # optional ``-k`` names for a narrower NEW run
    seeds: tuple[int, ...] = ()  # run the NEW suite once per PYTHONHASHSEED; every run must fail


_TXN_HOOK = "        before_send_transaction=_strip_sensitive_headers,\n"
_EVENT_HOOK = "        before_send=_strip_sensitive_headers,\n"
_COOKIE_DICT = '                request_data["cookies"] = dict.fromkeys(cookies, "[Filtered]")\n'
_COOKIE_DROP = '            del request_data["cookies"]\n'
_FRAME_GUARD = "                if isinstance(frame, dict):\n"

_ENCODE_BLOCK = (
    '        presented = api_key.encode("utf-8", "surrogatepass")\n'
    "        matched = False\n"
    "        for candidate in self._api_keys:\n"
    '            if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")):\n'
)
_COMPARE = '            if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")):\n'
_WALK = "        for candidate in self._api_keys:\n" + _COMPARE + "                matched = True\n"
_KEY_SET = "        self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str) and k.strip()}\n"


def _encoded_with(encoding: str, errors: str) -> tuple[tuple[str, str], ...]:
    return ((_ENCODE_BLOCK, _ENCODE_BLOCK.replace('"utf-8", "surrogatepass"', f'"{encoding}", "{errors}"')),)


MUTANTS = [
    # --- juniper-observability: sentry.py
    Mutant("O1-no-transaction-hook", _OBS, _SENTRY, ((_TXN_HOOK, ""),), "F2", True),
    Mutant("CM07-transaction-hook-only-when-rate-above-zero", _OBS, _SENTRY, ((_TXN_HOOK, "        before_send_transaction=_strip_sensitive_headers if traces_sample_rate else None,\n"),), "F2 at traces_sample_rate=0.0 (parent-sampled)", True),
    Mutant("BS-error-hook-only-when-rate-above-zero", _OBS, _SENTRY, ((_EVENT_HOOK, "        before_send=_strip_sensitive_headers if traces_sample_rate else None,\n"),), "SEC-10 at traces_sample_rate=0.0 (round-2 MAJOR)", True),
    Mutant("O2-no-cookie-redaction", _OBS, _SENTRY, ((_COOKIE_DICT, "                pass\n"),), "cookies (found 2026-11-08)", True),
    Mutant("O5-dict-cookies-only", _OBS, _SENTRY, ((_COOKIE_DROP, "            pass\n"),), "cookies of another shape", True),
    Mutant("O6-cookies-a-bare-string", _OBS, _SENTRY, ((_COOKIE_DICT, '                request_data["cookies"] = "[Filtered]"\n'),), "cookie shape (round-1 security NIT)", True),
    Mutant("O9-cookies-redacted-only-when-two", _OBS, _SENTRY, (("            if cookies:\n", "            if len(cookies) > 1:\n"),), "a single cookie (round-2 NIT)", True),
    Mutant(
        "O10-cookie-step-needs-dict-headers",
        _OBS,
        _SENTRY,
        (('    if isinstance(request_data, dict):\n        cookies = request_data.get("cookies")\n', '    if isinstance(request_data, dict) and isinstance(headers, dict):\n        cookies = request_data.get("cookies")\n'),),
        "cookies whatever the headers' shape (round-1 OM08, round-2 NIT)",
        True,
    ),
    Mutant("O7-header-set-without-sec-websocket-protocol", _OBS, _SENTRY, (('        "sec-websocket-protocol",\n', ""),), "owner ruling: the four header names", True),
    Mutant("O8-header-set-without-proxy-authorization", _OBS, _SENTRY, (('        "proxy-authorization",\n', ""),), "owner ruling: the four header names", True),
    Mutant("O3-skip-library-frames", _OBS, _SENTRY, ((_FRAME_GUARD, '                if isinstance(frame, dict) and frame.get("in_app") is not False:\n'),), "F6", True),
    # The OLD suite already killed O4: its wire tests' frames are application code (``in_app: True``,
    # under the project root), so skipping them left ``vars`` on the wire. Measured by this script's
    # first run (2026-11-08), where expecting survival MISMATCHED.
    Mutant("O4-skip-application-frames", _OBS, _SENTRY, ((_FRAME_GUARD, '                if isinstance(frame, dict) and frame.get("in_app") is not True:\n'),), "F6 (the other half)", False),
    # --- juniper-service-core: security.py (APIKeyAuth.validate)
    Mutant("S1-bytes-equality", _SC, _SECURITY, ((_COMPARE, '            if presented == candidate.encode("utf-8", "surrogatepass"):\n'),), "F3", True),
    Mutant(
        "S6-compare-or-bytes-equality",
        _SC,
        _SECURITY,
        ((_COMPARE, '            if hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")) or presented == candidate.encode("utf-8", "surrogatepass"):\n'),),
        "F3 beside compare_digest (round-2 MINOR)",
        True,
    ),
    Mutant(
        "S7-bytes-equality-decides",
        _SC,
        _SECURITY,
        ((_COMPARE, '            if [hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass"))] and presented == candidate.encode("utf-8", "surrogatepass"):\n'),),
        "F3 with compare_digest a decoy (round-2 MINOR)",
        True,
    ),
    Mutant("S2-break-after-match", _SC, _SECURITY, (("                matched = True\n", "                matched = True\n                break\n"),), "F8", True),
    Mutant(
        "S3-any-short-circuit",
        _SC,
        _SECURITY,
        ((_WALK + "        return matched\n", '        matched = any(hmac.compare_digest(presented, candidate.encode("utf-8", "surrogatepass")) for candidate in self._api_keys)\n        return matched\n'),),
        "APD-CASCOR-005 / F8",
        True,
    ),
    Mutant("SM06-sorted-walk-and-break", _SC, _SECURITY, ((_WALK, _WALK.replace("self._api_keys:", "sorted(self._api_keys):") + "                break\n"),), "F8 under any walk order", True, (_SPY_TEST,), _HASH_SEEDS),
    Mutant(
        "SM07-configured-order-walk-and-break",
        _SC,
        _SECURITY,
        (
            (_KEY_SET, _KEY_SET + "        self._ordered = [k for k in (api_keys or []) if isinstance(k, str) and k.strip()]\n"),
            (_WALK, _WALK.replace("self._api_keys:", "self._ordered:") + "                break\n"),
        ),
        "F8 under any walk order",
        True,
        (_SPY_TEST,),
        _HASH_SEEDS,
    ),
    Mutant("S4-utf16le-surrogatepass", _SC, _SECURITY, _encoded_with("utf-16-le", "surrogatepass"), "F5 (matrix only)", True, (_MATRIX_TEST,)),
    Mutant("SM21-utf8-backslashreplace", _SC, _SECURITY, _encoded_with("utf-8", "backslashreplace"), "encoding probes (matrix only)", True, (_MATRIX_TEST,)),
    Mutant("SM21b-utf8-namereplace", _SC, _SECURITY, _encoded_with("utf-8", "namereplace"), "encoding probes (matrix only)", True, (_MATRIX_TEST,)),
    Mutant("SM22-utf8-xmlcharrefreplace", _SC, _SECURITY, _encoded_with("utf-8", "xmlcharrefreplace"), "encoding probes (matrix only)", True, (_MATRIX_TEST,)),
    Mutant("SM02-compare-first-16-bytes", _SC, _SECURITY, ((_COMPARE, '            if hmac.compare_digest(presented[:16], candidate.encode("utf-8", "surrogatepass")[:16]):\n'),), "encoding probes (matrix only)", True, (_MATRIX_TEST,)),
    Mutant("SM03-compare-first-32-bytes", _SC, _SECURITY, ((_COMPARE, '            if hmac.compare_digest(presented[:32], candidate.encode("utf-8", "surrogatepass")[:32]):\n'),), "encoding probes (matrix only)", True, (_MATRIX_TEST,)),
    Mutant(
        "SM26-case-folded-compare",
        _SC,
        _SECURITY,
        ((_ENCODE_BLOCK, _ENCODE_BLOCK.replace("api_key.encode(", "api_key.lower().encode(").replace("candidate.encode(", "candidate.lower().encode(")),),
        "encoding probes (matrix only)",
        True,
        (_MATRIX_TEST,),
    ),
    Mutant("S5-str-compare", _SC, _SECURITY, ((_COMPARE, "            if hmac.compare_digest(api_key, candidate):\n"),), "the 0.7.1 fix itself (instrument control)", False),
]

_IMPORT_NAME = {_OBS: "juniper_observability", _SC: "juniper_service_core"}
_TEST_FILE = {_OBS: "tests/test_sentry.py", _SC: "tests/test_security.py"}


def _copy_package(package: str, dest_root: Path) -> Path:
    dest = dest_root / package
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(REPO_ROOT / package, dest, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "build", "dist"))
    return dest


def _apply(copy: Path, mutant: Mutant) -> None:
    target = copy / mutant.source
    text = target.read_text(encoding="utf-8")
    for old, new in mutant.edits:
        count = text.count(old)
        if count != 1:
            raise SetupError(f"{mutant.mutant_id}: an edit's old text occurs {count} times in {mutant.source}, not once")
        text = text.replace(old, new, 1)
    target.write_text(text, encoding="utf-8")


def _env(copy: Path, seed: int | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(copy)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if seed is not None:
        env["PYTHONHASHSEED"] = str(seed)
    for name in ("SENTRY_DSN", "SENTRY_SDK_DSN", "JUNIPER_DATA_SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"):
        env[name] = ""
    return env


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """``subprocess.run``, with an interpreter that cannot be started reported as a setup error."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)
    except OSError as exc:
        raise SetupError(f"cannot run {cmd[0]}: {exc}") from exc


def _prove_copy_is_imported(python: str, copy: Path, package: str) -> None:
    """The copy, not an editable install, is what the suite imports.

    Runs ``python -c`` with ``cwd`` = the copy and the same environment as the pytest run below.
    ``-c`` and ``-m`` both put the working directory first on ``sys.path``, so this resolves the
    import exactly as ``python -m pytest`` there does.
    """
    module = _IMPORT_NAME[package]
    probe = _run([python, "-c", f"import {module}; print({module}.__file__)"], cwd=copy, env=_env(copy))
    imported = Path(probe.stdout.strip()).resolve()
    if probe.returncode != 0 or copy.resolve() not in imported.parents:
        raise SetupError(f"{module} imports from {imported or probe.stderr.strip()}, not from the copy {copy}")


def _run_suite(python: str, copy: Path, select: tuple[str, ...], seed: int | None = None) -> int:
    """pytest's exit status: 0 (all passed) or 1 (a test failed). Anything else is a setup error.

    Exit 5 (nothing collected) or 2 (a collection error) would otherwise read as "the mutant was
    killed" and make an expected-fail row pass vacuously.
    """
    cmd = [python, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests"]
    if select:
        cmd += ["-k", " or ".join(select)]
    result = _run(cmd, cwd=copy, env=_env(copy, seed))
    if result.returncode not in (0, 1):
        tail = "\n".join(result.stdout.splitlines()[-15:])
        raise SetupError(f"pytest exited {result.returncode} in {copy}\n{tail}")
    return result.returncode


def _verdict(expected_pass: bool, returncode: int) -> str:
    return "OK" if (returncode == 0) == expected_pass else "MISMATCH"


def _check(args: argparse.Namespace) -> list[tuple]:
    python_for = {_OBS: args.obs_python, _SC: args.sc_python}
    old_test_for = {_OBS: args.old_obs_test, _SC: args.old_sc_test}
    for path in old_test_for.values():
        if not path.is_file():
            raise SetupError(f"{path} is not a file")
    for python in python_for.values():
        if shutil.which(python) is None:  # a path, or a name found on PATH, that can be executed
            raise SetupError(f"{python} is not an executable interpreter")
    args.scratch.mkdir(parents=True, exist_ok=True)

    rows = []
    for package in (_OBS, _SC):
        for suite in ("new", "old"):
            copy = _copy_package(package, args.scratch / f"control-{suite}")
            if suite == "old":
                shutil.copyfile(old_test_for[package], copy / _TEST_FILE[package])
            _prove_copy_is_imported(python_for[package], copy, package)
            rc = _run_suite(python_for[package], copy, ())
            rows.append((f"CONTROL-{package}", suite, "pass", rc, _verdict(True, rc)))

    for mutant in MUTANTS:
        python = python_for[mutant.package]
        for suite in ("new", "old"):
            copy = _copy_package(mutant.package, args.scratch / f"{mutant.mutant_id}-{suite}")
            _apply(copy, mutant)
            if suite == "old":
                shutil.copyfile(old_test_for[mutant.package], copy / _TEST_FILE[mutant.package])
            _prove_copy_is_imported(python, copy, mutant.package)
            select = mutant.select if suite == "new" else ()
            expected_pass = suite == "old" and mutant.survived_old
            label = f"{mutant.mutant_id} [{mutant.targets}]" + (f" -k {' or '.join(select)}" if select else "")
            for seed in mutant.seeds if suite == "new" and mutant.seeds else (None,):
                rc = _run_suite(python, copy, select, seed)
                rows.append((label + ("" if seed is None else f" PYTHONHASHSEED={seed}"), suite, "pass" if expected_pass else "fail", rc, _verdict(expected_pass, rc)))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scratch", required=True, type=Path, help="an empty-or-reusable scratch directory (the repo's tmp/, never the system temp dir)")
    parser.add_argument("--obs-python", required=True, help="python of a venv with juniper-observability[test]")
    parser.add_argument("--sc-python", required=True, help="python of a venv with juniper-service-core[test]")
    parser.add_argument("--old-obs-test", required=True, type=Path, help="tests/test_sentry.py as it is on main without P3-07")
    parser.add_argument("--old-sc-test", required=True, type=Path, help="tests/test_security.py as it is on main without P3-07")
    args = parser.parse_args(argv)

    try:
        rows = _check(args)
    except SetupError as exc:
        print(f"setup error: {exc}", file=sys.stderr)
        return 2

    print("mutant\tsuite\texpected\texit\tverdict")
    for row in rows:
        print("\t".join(str(cell) for cell in row))
    mismatches = sum(1 for row in rows if row[-1] != "OK")
    print(f"RESULT: {len(rows) - mismatches}/{len(rows)} rows as expected")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
