"""Fake interpreters and synthetic envs for the W0.2 recurrence env preflight tests.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (helpers for util/recurrence_env_preflight.bash)
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

Shared by ``tests/test_recurrence_env_preflight.py`` (the script itself) and the two launcher
suites, ``tests/test_experiment_stack_script.py`` and ``tests/test_isolated_stack_script.py``
(the ``recurrence_up`` call site). Two kinds of double, because they prove different things:

- ``write_fake_python`` -- an executable bash ``python`` that answers exactly the preflight's
  three calls with canned text: ``-s -m pip check``, the version-pin probe, and the
  ``derive_full_split`` import. Deterministic and fast; it drives every branch of the script,
  including ones a real env cannot produce on demand (a probe that crashes, pip that will not
  run). It refuses any call that does not pass ``-s`` FIRST, so dropping ``-s`` -- the flag
  that stops a ``~/.local`` package masking a gap in the env -- fails the tests, and it records
  each call's argv head, working directory and ``LD_LIBRARY_PATH``.
- ``make_synthetic_venv`` -- a REAL venv, built offline: ``python -m venv --without-pip``, the
  test interpreter's own ``pip`` symlinked in, hand-written ``*.dist-info/METADATA`` for the
  distributions in play, and a stub ``juniper_recurrence_model`` package. ``pip check``, the
  pin probe and the import then run for real, so the script is checked against pip's actual
  output and the probe's actual Python -- the parts a fake can only imitate. This is the
  "synthetic stale env" the plan's W0.2 acceptance names.

The canned lines are the ones the 2026-10-03 audit recorded for JuniperCascor1, and a real
``pip check`` over the synthetic stale venv prints the same three conflict lines byte for byte.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT_SCRIPT = REPO_ROOT / "util" / "recurrence_env_preflight.bash"

#: F-E1, verbatim: the app's pins, violated.
MODEL_PIN_LINE = "juniper-recurrence 0.5.0 has requirement juniper-recurrence-model<0.4.0,>=0.3.0, but you have juniper-recurrence-model 0.1.5."
SERVICE_CORE_PIN_LINE = "juniper-recurrence 0.5.0 has requirement juniper-service-core<0.8.0,>=0.6.0, but you have juniper-service-core 0.5.0."
#: The unrelated noise in the same env's pip check -- must never refuse.
CUDA_BINDINGS_LINE = "cuda-python 13.4.1 has requirement cuda-bindings~=13.4.1, but you have cuda-bindings 13.4.1a0."
CUDA_CORE_LINE = "cuda-python 13.4.1 has requirement cuda-core~=1.2.0, but you have cuda-core 1.0.1."
IMPORT_ERROR_LINE = "ImportError: cannot import name 'derive_full_split' from 'juniper_recurrence_model.data' (/opt/fake-env/lib/python3.14/site-packages/juniper_recurrence_model/data.py)"

IMPORT_PROBE = "from juniper_recurrence_model.data import derive_full_split"
#: The first line of the script's pin probe; the fake recognises the call by it.
PIN_PROBE_MARKER = "recurrence_env_preflight version-pin probe"

#: Canned pin-probe protocol lines (see PIN_PROBE in the script).
PINS_OK = ("APP 0.5.0 packaging", "OK juniper-recurrence-model 0.3.0 <0.4.0,>=0.3.0", "OK juniper-service-core 0.7.0 <0.8.0,>=0.6.0")
PINS_STALE = ("APP 0.5.0 packaging", "BAD juniper-recurrence-model 0.1.5 <0.4.0,>=0.3.0", "BAD juniper-service-core 0.5.0 <0.8.0,>=0.6.0")

SKIP_MARKER = "WARNING: ENV PREFLIGHT SKIPPED —"


def _heredoc(tag: str, lines: Sequence[str]) -> str:
    """A quoted heredoc body (no expansion), refusing a line that would end it early."""
    for line in lines:
        if line == tag:
            raise ValueError(f"canned line collides with heredoc tag {tag!r}")
    return "".join(f"{line}\n" for line in lines) + f"{tag}\n"


def write_fake_python(path: Path, *, pip_check: Sequence[str] = (), pip_check_rc: "int | None" = None, pins: Sequence[str] = PINS_OK, pins_rc: int = 0, import_error: "str | None" = None, calls_log: "Path | None" = None) -> Path:
    """Write an executable fake ``python`` at ``path`` that answers the preflight's three calls.

    ``pip_check`` lines are printed by ``-s -m pip check``, which exits ``pip_check_rc`` --
    by default 1 when there are lines (pip's own convention) and 0 with "No broken
    requirements found." when there are none. ``pins`` is the pin probe's protocol output
    (exit ``pins_rc``). ``import_error`` makes the import probe fail with a traceback ending
    in that line. ``calls_log`` receives one line per call: the first three argv entries
    (newlines escaped), the working directory and ``LD_LIBRARY_PATH``.
    """
    rc = (1 if pip_check else 0) if pip_check_rc is None else pip_check_rc
    pip_lines = list(pip_check) if pip_check else (["No broken requirements found."] if rc == 0 else [])
    record = ""
    if calls_log is not None:
        record = f"""{{
    printf 'call:'
    for arg in "${{@:1:3}}"; do
        arg="${{arg//$'\\n'/\\\\n}}"
        printf ' [%s]' "${{arg:0:60}}"
    done
    printf ' cwd=%s LD_LIBRARY_PATH=%s\\n' "$PWD" "${{LD_LIBRARY_PATH-__UNSET__}}"
}} >>"{calls_log}"
"""
    if import_error is None:
        import_arm = "exit 0"
    else:
        import_arm = "printf 'Traceback (most recent call last):\\n  File \"<string>\", line 1, in <module>\\n' >&2\n" "            cat >&2 <<'__FAKE_IMPORT_ERROR__'\n" + _heredoc("__FAKE_IMPORT_ERROR__", [import_error]) + "            exit 1"
    body = f"""#!/usr/bin/env bash
{record}if [[ "${{1-}}" != "-s" ]]; then
    echo "fake python: every preflight call must pass -s first; got: $*" >&2
    exit 97
fi
shift
if [[ "${{1-}}" == "-m" && "${{2-}}" == "pip" && "${{3-}}" == "check" ]]; then
    cat <<'__FAKE_PIP_CHECK__'
{_heredoc("__FAKE_PIP_CHECK__", pip_lines)}    exit {rc}
fi
if [[ "${{1-}}" == "-c" ]]; then
    case "${{2-}}" in
        *"{PIN_PROBE_MARKER}"*)
            cat <<'__FAKE_PINS__'
{_heredoc("__FAKE_PINS__", list(pins))}            exit {pins_rc}
            ;;
        "{IMPORT_PROBE}")
            {import_arm}
            ;;
    esac
fi
echo "fake python: unexpected call: $*" >&2
exit 98
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(0o755)
    return path


def read_calls(calls_log: Path) -> "list[str]":
    """The calls a fake recorded, one string each (empty when it was never run)."""
    if not calls_log.exists():
        return []
    return [line for line in calls_log.read_text().splitlines() if line.startswith("call:")]


# --- real synthetic venvs ----------------------------------------------------------------------


def host_pip_dir() -> "Path | None":
    """The test interpreter's own ``pip`` package directory, or None when it has no pip."""
    try:
        import pip
    except ImportError:
        return None
    return Path(pip.__file__).resolve().parent


def host_packaging_dir() -> "Path | None":
    """The test interpreter's ``packaging`` package directory, or None."""
    try:
        import packaging
    except ImportError:
        return None
    return Path(packaging.__file__).resolve().parent


def _write_dist(site: Path, name: str, version: str, requires: Sequence[str] = ()) -> None:
    dist_info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir()
    lines = ["Metadata-Version: 2.1", f"Name: {name}", f"Version: {version}", *(f"Requires-Dist: {req}" for req in requires)]
    (dist_info / "METADATA").write_text("\n".join(lines) + "\n")


#: The real juniper-recurrence 0.5.0's pins on the two distributions, plus extra-gated lines of the
#: shape the installed metadata carries (`juniper-recurrence-model[torch]...; extra == "torch"`),
#: which neither pip check nor the probe may count. The gated model pin is deliberately
#: UNSATISFIABLE: a probe that counted it would report a violation the env does not have, so the
#: repaired-env test fails on exactly that mistake instead of passing because the specifiers agree.
APP_REQUIRES = (
    "juniper-recurrence-model<0.4.0,>=0.3.0",
    "juniper-service-core<0.8.0,>=0.6.0",
    'juniper-recurrence-model[torch]>=99; extra == "torch"',
    'pytest>=8.0; extra == "test"',
)


def make_synthetic_venv(root: Path, *, model_version: str, service_core_version: str, derive_full_split: bool, cuda_noise: bool = True, top_level_packaging: bool = False) -> Path:
    """Build a real, offline venv holding the given recurrence closure; return its ``python``.

    Raises ``RuntimeError`` when the test interpreter has no ``pip`` to lend the venv (callers
    skip on that, by name). ``top_level_packaging`` also lends ``packaging``, so the pin probe
    takes its primary import instead of pip's vendored copy.
    """
    pip_dir = host_pip_dir()
    if pip_dir is None:
        raise RuntimeError("the test interpreter has no pip to lend the synthetic venv")
    venv_dir = root / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv_dir)], check=True, capture_output=True, timeout=120)
    python = venv_dir / "bin" / "python"
    site = Path(subprocess.run([str(python), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], check=True, capture_output=True, text=True, timeout=60).stdout.strip())
    (site / "pip").symlink_to(pip_dir, target_is_directory=True)
    if top_level_packaging:
        packaging_dir = host_packaging_dir()
        if packaging_dir is None:
            raise RuntimeError("the test interpreter has no packaging to lend the synthetic venv")
        (site / "packaging").symlink_to(packaging_dir, target_is_directory=True)
    _write_dist(site, "juniper-recurrence", "0.5.0", APP_REQUIRES)
    _write_dist(site, "juniper-recurrence-model", model_version)
    _write_dist(site, "juniper-service-core", service_core_version)
    if cuda_noise:
        _write_dist(site, "cuda-python", "13.4.1", ("cuda-bindings~=13.4.1",))
        _write_dist(site, "cuda-bindings", "13.4.1a0")
    package = site / "juniper_recurrence_model"
    package.mkdir()
    (package / "__init__.py").write_text("")
    data = "def load_sequence_data(*args, **kwargs):\n    return None\n"
    if derive_full_split:
        data += "\n\ndef derive_full_split(*args, **kwargs):\n    return None\n"
    (package / "data.py").write_text(data)
    return python
