#!/usr/bin/env python3
"""
Probe whether juniper-data's ``mnist`` schema reads from the PUBLISHED wheel without juniper-data's ``[mnist]`` extra.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (follow-up 3.4 of the recurrence x equities handoff; juniper-canopy#778)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_recurrence-equities-cascor-0-13-0-published-plan-v1-15-7.md
         (item 3.4, the question this answers); juniper-canopy#776 ("Left out, deliberately": mnist keeps the
         modal's Noise field); juniper-canopy#777 (the drift job); juniper-canopy#778 (the change this evidence supports);
         util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py (the exit-status pattern this follows)

Why this exists
---------------
canopy's restart modal renders a Noise field for ``mnist``, which juniper-data's ``MnistParams`` does not declare: the value
reaches juniper-data, which ignores unknown keys, so it is dropped without a word (the F-C3 class of juniper-canopy#736).
canopy closes that class per generator with a ``DECLARED_PARAM_DEFAULTS`` entry captured from juniper-data. canopy marks
``mnist`` as needing "juniper-data's optional dataset extra", which is juniper-data's ``[mnist]`` extra (it pulls
``datasets[vision]``). The question was whether canopy's capture tool and canopy#777's drift job, which install
``juniper-data[api]`` only, can read ``mnist``'s schema at all.

What it does
------------
1. Builds a throwaway venv from ``--python`` (the drift job runs Python 3.14), with the juniper-data wheel PyPI serves
   (its sha256 checked against PyPI's JSON) installed with ``[api]`` and nothing else. A venv is reused only when its
   completion marker names the requested version; every run re-checks the kept wheel against PyPI, and, inside the venv,
   the installed version and every RECORD-hashed ``juniper_data/`` file against the distribution's RECORD (RECORD hashes no
   ``.pyc``).
2. In that venv (``-I``), the absence control: no ``datasets`` distribution is installed, ``import datasets`` fails, and
   juniper-data agrees (``MnistGenerator.is_available()`` is False). These are one fact seen three ways, not three facts.
   Then it reads ``GENERATOR_REGISTRY["mnist"]["params_class"].model_json_schema()`` (JSON round-tripped, as
   ``GET /v1/generators`` serves it) and checks that ``flatten`` and ``n_samples`` are declared and ``noise`` is not, and
   that ``MnistParams(n_samples=500, noise=0.25)`` validates with ``noise`` absent from ``model_dump()`` (the silent drop).
3. Fetches canopy's drift check (``util/check_juniper_data_generator_schemas.py``) and tabular snapshot
   (``src/tests/fixtures/juniper_data_tabular_generator_schemas.json``) at the commit ``--canopy-ref`` resolves to, and
   writes two fixtures that hold ONLY an ``mnist`` entry, under the snapshot's provenance block: one with the schema as read,
   one with ``flatten``'s default flipped. So the verdict cannot depend on the snapshot's other generators.
4. Runs the drift check on each. The first must exit 0, print the "no drift" summary and report ``mnist`` ``ok``. The
   second is the control: it must exit 1, print the DRIFT summary, report ``mnist`` ``DRIFT`` and name
   ``field "flatten": default:``, which shows the check really compares the ``mnist`` entry.

The ``mnist`` entry is synthetic. It proves the mechanism, not a capture: a real capture goes through canopy's
``util/ad-hoc/2026-10-26_capture_published_generator_schemas.py``, which also verifies the wheel against the release tag
file by file and records that provenance.

    python3 -I util/ad-hoc/2026-10-29_probe_mnist_schema_without_mnist_extra.py --python /opt/miniforge3/envs/JuniperCascor1/bin/python

The venv and every fetched file live under ``--work`` (default: this checkout's ``tmp/2026-10-29-mnist-schema-probe/``).

Exit status: 0 when every check passes, 1 when a check ran and failed and nothing else went wrong, and 2 on anything
else: the venv cannot be built or does not match its wheel, a fetch fails or times out, the wheel's sha256 differs from
PyPI's, the in-venv probe or the drift check exits with anything but 0 or 1, crashes, or omits its summary line, or any
unexpected error. Failed checks recorded before such an error are still printed, in the venv and outside it. So 1 always
means a check ran and failed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess  # nosec B404
import sys
import urllib.error
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_WORK = REPO_ROOT / "tmp" / "2026-10-29-mnist-schema-probe"
PYPI_JSON = "https://pypi.org/pypi/juniper-data/{version}/json"
CANOPY_REPO = "pcalnon/juniper-canopy"
CHECK_TOOL = "util/check_juniper_data_generator_schemas.py"
TABULAR_FIXTURE = "src/tests/fixtures/juniper_data_tabular_generator_schemas.json"
FIXTURE_NAME = "juniper_data_tabular_generator_schemas.json"
MARKER = ".probe-complete"
MNIST_STATUS = re.compile(r"^mnist\s+\S+\s+(?P<status>\S+)$")

# Runs inside the throwaway venv. argv: <tabular snapshot> <output dir>. Exit 0 pass, 1 a failed check, 2 an error.
INNER_PROBE = r'''
import base64
import copy
import hashlib
import importlib.metadata as md
import json
import pathlib
import sys


def _record_check():
    """Return (files checked, files whose bytes differ from the installed distribution's RECORD) under juniper_data/."""
    checked, differing = 0, []
    for entry in md.files("juniper-data") or ():
        path = str(entry)
        if not path.startswith("juniper_data/") or entry.hash is None or entry.hash.mode != "sha256":
            continue
        checked += 1
        digest = base64.urlsafe_b64encode(hashlib.sha256(pathlib.Path(entry.locate()).read_bytes()).digest()).rstrip(b"=").decode()
        if digest != entry.hash.value:
            differing.append(path)
    return checked, differing


FAILURES = []


def _finish(failures):
    # The summary line is the outer probe's proof that exit 0 / 1 came from here, not from a stray sys.exit.
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"INNER-SUMMARY: {len(failures)} failed check(s)")
    return 1 if failures else 0


def main():
    snapshot, out_dir, expected = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
    if md.version("juniper-data") != expected:
        print(f"ERROR: the venv holds juniper-data {md.version('juniper-data')}, not {expected}")
        return 2
    checked, differing = _record_check()
    if not checked or differing:
        print(f"ERROR: the installed juniper-data does not match its RECORD ({checked} hashed files checked; differing: {differing[:5]})")
        return 2
    import juniper_data

    print(f"juniper-data {expected} from {pathlib.Path(juniper_data.__file__).parent}; its {checked} RECORD-hashed files match (RECORD hashes no .pyc)")
    failures = FAILURES
    # The absence control: one fact (the [mnist] extra's `datasets` is not installed), seen three ways.
    try:
        md.distribution("datasets")
        failures.append("control: a `datasets` distribution is installed")
    except md.PackageNotFoundError:
        print("control ok: no `datasets` distribution is installed")
    try:
        import datasets  # noqa: F401

        failures.append("control: `datasets` is importable")
    except ImportError as exc:
        print(f"control ok: import datasets -> {type(exc).__name__}")
    except (Exception, SystemExit) as exc:  # noqa: BLE001 -- a module that exists but fails to import is present, not absent
        failures.append(f"control: `datasets` is present (its import raised {type(exc).__name__})")
    from juniper_data.api.routes.generators import GENERATOR_REGISTRY
    from juniper_data.generators.mnist import MnistGenerator, MnistParams

    if MnistGenerator.is_available():
        failures.append("control: MnistGenerator.is_available() is True")
    else:
        print("control ok: MnistGenerator.is_available() is False")
    print(f"registry: {len(GENERATOR_REGISTRY)} generators")
    info = GENERATOR_REGISTRY.get("mnist")
    if info is None:
        failures.append("mnist is not in GENERATOR_REGISTRY")
        return _finish(failures)
    schema = json.loads(json.dumps(info["params_class"].model_json_schema()))
    props = schema.get("properties") or {}
    print(f"mnist {info['version']}: {len(props)} properties: " + ", ".join(f"{k}={v.get('default')!r}" for k, v in props.items()))
    if not props:
        failures.append("mnist's schema has no properties")
    for field in ("flatten", "n_samples"):
        if field not in props:
            failures.append(f"mnist's schema does not declare {field}")
    if "noise" in props:
        failures.append("mnist's schema declares noise, so there is no undeclared Noise to drop")
    else:
        print("ok: mnist declares no noise")
        try:
            dumped = MnistParams(n_samples=500, noise=0.25).model_dump()
        except Exception as exc:  # noqa: BLE001 -- a refusal is this check's negative outcome, not an error
            failures.append(f"MnistParams refused an undeclared noise key ({type(exc).__name__}), so it is not silently dropped")
        else:
            if "noise" in dumped:
                failures.append("MnistParams kept an undeclared noise key")
            else:
                print("ok: MnistParams(n_samples=500, noise=0.25) validates and drops noise (the silent drop)")
    flatten = props.get("flatten")
    if not isinstance(flatten, dict) or not isinstance(flatten.get("default"), bool):
        failures.append("mnist's flatten has no boolean default to flip, so the control fixture cannot be built")
        return _finish(failures)
    provenance = json.loads(snapshot.read_text(encoding="utf-8"))["_provenance"]
    entry = {"name": "mnist", "version": info["version"], "schema": schema}
    for sub, flip in (("fx_ok", False), ("fx_drift", True)):
        added = copy.deepcopy(entry)
        if flip:
            added["schema"]["properties"]["flatten"]["default"] = not flatten["default"]
        target = out_dir / sub / snapshot.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"_provenance": provenance, "generators": [added]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {target} (mnist only{', flatten flipped' if flip else ''})")
    return _finish(failures)


if __name__ == "__main__":
    try:
        code = main()
    except (Exception, SystemExit) as exc:  # noqa: BLE001 -- anything but a failed check (a stray sys.exit included) is an error
        for failure in FAILURES:
            print(f"FAIL (before the error): {failure}")
        print(f"ERROR: {type(exc).__name__}: {exc}")
        code = 2
    sys.exit(code)
'''


class ProbeError(Exception):
    """Anything that stops the probe from running its checks (exit 2)."""


def _run(argv: list[str], timeout: int = 300, env: dict | None = None) -> subprocess.CompletedProcess:
    try:
        # Every argv here is a fixed list built in this file; no shell is involved.
        return subprocess.run(argv, capture_output=True, text=True, check=False, timeout=timeout, env=env)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(f"{' '.join(argv[:4])}: {type(exc).__name__}: {exc}") from exc


def _tail(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).strip()[-600:]


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _pypi_wheel(version: str) -> dict:
    url = PYPI_JSON.format(version=version)
    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310
            files = json.load(response)["urls"]
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        raise ProbeError(f"{url}: {type(exc).__name__}: {exc}") from exc
    wheels = [f for f in files if f["filename"].endswith(".whl")]
    if len(wheels) != 1:
        raise ProbeError(f"{url} lists {len(wheels)} wheels, expected 1")
    return wheels[0]


def _python_version(python: str) -> str:
    proc = _run([python, "-I", "-c", "import sys; print('%d.%d' % sys.version_info[:2])"], timeout=60)
    if proc.returncode != 0:
        raise ProbeError(f"{python} does not run: {_tail(proc)}")
    return proc.stdout.strip()


def _venv(python: str | None, work: pathlib.Path, version: str) -> pathlib.Path:
    """Return the venv's interpreter, building the venv when no complete one holds ``version``."""
    venv = work / "venv"
    vpy = venv / "bin" / "python"
    marker = venv / MARKER
    pip_env = dict(os.environ, TMPDIR=str(work / "pip-tmp"), PIP_DISABLE_PIP_VERSION_CHECK="1")
    (work / "pip-tmp").mkdir(parents=True, exist_ok=True)
    wheel_info = _pypi_wheel(version)
    wheel = work / "wheel" / wheel_info["filename"]
    if marker.exists() and marker.read_text(encoding="utf-8").strip() == f"{version} {wheel_info['digests']['sha256']}" and wheel.exists():
        if python is not None and _python_version(python) != _python_version(str(vpy)):
            raise ProbeError(f"{venv} runs Python {_python_version(str(vpy))}, but --python is {_python_version(python)}; pass another --work")
        print(f"venv: reusing {venv} (Python {_python_version(str(vpy))}, juniper-data {version})")
    else:
        if venv.exists():
            print(f"venv: {venv} is incomplete or holds another build; rebuilding it")
            shutil.rmtree(venv)
        builder = python or sys.executable
        print(f"venv: building {venv} from {builder} (Python {_python_version(builder)})")
        for argv in ([builder, "-m", "venv", str(venv)], [str(vpy), "-m", "pip", "install", "--quiet", "--no-cache-dir", "--upgrade", "pip>=26.1.1"]):
            proc = _run(argv, timeout=900, env=pip_env)
            if proc.returncode != 0:
                raise ProbeError(f"{' '.join(argv[:4])} failed: {_tail(proc)}")
        if wheel.exists():
            wheel.unlink()
        proc = _run([str(vpy), "-m", "pip", "download", "--quiet", "--no-cache-dir", "--no-deps", "--only-binary=:all:", f"juniper-data=={version}", "-d", str(wheel.parent)], timeout=900, env=pip_env)
        if proc.returncode != 0 or not wheel.exists():
            raise ProbeError(f"pip download juniper-data=={version} failed: {_tail(proc)}")
    if _sha256(wheel) != wheel_info["digests"]["sha256"]:
        raise ProbeError(f"{wheel.name}: sha256 {_sha256(wheel)} differs from PyPI's {wheel_info['digests']['sha256']}")
    print(f"wheel: {wheel.name} sha256 {wheel_info['digests']['sha256']} = PyPI's (uploaded {wheel_info['upload_time_iso_8601']})")
    if not marker.exists():
        proc = _run([str(vpy), "-m", "pip", "install", "--quiet", "--no-cache-dir", f"{wheel}[api]"], timeout=900, env=pip_env)
        if proc.returncode != 0:
            raise ProbeError(f"pip install {wheel.name}[api] failed: {_tail(proc)}")
        marker.write_text(f"{version} {wheel_info['digests']['sha256']}\n", encoding="utf-8")
    return vpy


def _fetch_canopy(ref: str, work: pathlib.Path) -> str:
    proc = _run(["gh", "api", f"repos/{CANOPY_REPO}/commits/{ref}", "--jq", ".sha"], timeout=120)
    sha = proc.stdout.strip()
    if proc.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ProbeError(f"gh api commits/{ref} failed: {_tail(proc)}")
    for path, local in ((CHECK_TOOL, work / "check_juniper_data_generator_schemas.py"), (TABULAR_FIXTURE, work / FIXTURE_NAME)):
        # Fetched by the resolved sha, not the ref name, so both files come from the commit printed below.
        proc = _run(["gh", "api", f"repos/{CANOPY_REPO}/contents/{path}?ref={sha}", "-H", "Accept: application/vnd.github.raw"], timeout=120)
        if proc.returncode != 0 or not proc.stdout:
            raise ProbeError(f"gh api contents/{path}@{sha[:8]} failed: {_tail(proc)}")
        local.write_text(proc.stdout, encoding="utf-8")
    print(f"canopy {ref} = {sha}; fetched {CHECK_TOOL} and {TABULAR_FIXTURE}")
    return sha


def classify_check(sub: str, proc: subprocess.CompletedProcess) -> tuple[bool, str]:
    """Judge one drift-check run. Return (passed, account); raise ProbeError when the run is not a check result at all."""
    if proc.returncode not in (0, 1):
        raise ProbeError(f"the drift check on {sub} exited {proc.returncode}, which is neither a result (0, 1) nor its own refusal: {_tail(proc)}")
    if "Traceback (most recent call last)" in proc.stderr:
        raise ProbeError(f"the drift check on {sub} crashed (exit {proc.returncode}): {_tail(proc)}")
    lines = [line.strip() for line in proc.stdout.splitlines()]
    summary = "no drift:" if proc.returncode == 0 else "DRIFT:"
    if not any(line.startswith(summary) for line in lines):
        raise ProbeError(f"the drift check on {sub} exited {proc.returncode} without its {summary!r} summary line: {_tail(proc)}")
    statuses = [m["status"] for m in map(MNIST_STATUS.match, lines) if m]
    flatten_drift = any(line.startswith('field "flatten": default:') for line in lines)
    account = f"exit {proc.returncode}; mnist status {statuses or 'absent'}; flatten drift line {'present' if flatten_drift else 'absent'}"
    if sub == "fx_ok":
        return proc.returncode == 0 and statuses == ["ok"] and not flatten_drift, account
    return proc.returncode == 1 and statuses == ["DRIFT"] and flatten_drift, account


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "mnist schema probe").strip().splitlines()[0])
    parser.add_argument("--python", default=None, help="interpreter to build the venv from (default: this one); the drift job runs 3.14")
    parser.add_argument("--juniper-data-version", default="0.17.1", help="the published juniper-data to probe")
    parser.add_argument("--canopy-ref", default="main", help="the canopy ref whose drift check and snapshot are used")
    parser.add_argument("--work", type=pathlib.Path, default=DEFAULT_WORK, help="where the venv and fetched files live")
    args = parser.parse_args(argv)
    failures: list[str] = []
    try:
        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        vpy = _venv(args.python, work, args.juniper_data_version)
        _fetch_canopy(args.canopy_ref, work)
        for stale in ("fx_ok", "fx_drift"):
            shutil.rmtree(work / stale, ignore_errors=True)
        inner = work / "inner_probe.py"
        inner.write_text(INNER_PROBE, encoding="utf-8")
        proc = _run([str(vpy), "-I", str(inner), str(work / FIXTURE_NAME), str(work), args.juniper_data_version], timeout=300)
        print(proc.stdout.rstrip())
        if proc.returncode not in (0, 1):
            raise ProbeError(f"the in-venv probe could not run (exit {proc.returncode}): {proc.stderr.strip()[-600:]}")
        summary = re.search(r"^INNER-SUMMARY: (\d+) failed check\(s\)$", proc.stdout, re.MULTILINE)
        if summary is None or (int(summary.group(1)) > 0) != (proc.returncode == 1):
            raise ProbeError(f"the in-venv probe exited {proc.returncode} without a matching summary line, so its status is not a check result: {_tail(proc)}")
        if proc.returncode == 1:
            failures.append(f"the in-venv checks failed ({summary.group(1)} FAIL line(s) above)")
        for sub, what in (("fx_ok", "reports mnist ok"), ("fx_drift", "the control: reports mnist's flatten drift")):
            fixture = work / sub / FIXTURE_NAME
            if not fixture.exists():
                failures.append(f"{sub}: no fixture was written, so the drift check did not run on it")
                continue
            proc = _run([str(vpy), "-I", str(work / "check_juniper_data_generator_schemas.py"), "--expected-version", args.juniper_data_version, "--fixture", str(fixture)], timeout=300)
            passed, account = classify_check(sub, proc)
            print(f"drift check on {sub}: {account}")
            if passed:
                print(f"PASS: {sub} {what}")
            else:
                failures.append(f"{sub}: expected a check that {what}; got {account}")
    except Exception as exc:  # noqa: BLE001 -- anything but a failed check (a ProbeError included) is an error, never a fail
        for failure in failures:
            print(f"FAIL (before the error): {failure}")
        print(f"ERROR: {exc if isinstance(exc, ProbeError) else f'{type(exc).__name__}: {exc}'}")
        return 2
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"{'PASS' if not failures else 'FAIL'}: juniper-data {args.juniper_data_version}, {len(failures)} failed check(s)")
    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, Exception) as exc:  # noqa: BLE001 -- an interrupt or anything outside main's guard is an error, never a fail
        print(f"ERROR: {type(exc).__name__}: {exc}")
        sys.exit(2)
