#!/usr/bin/env python3
"""Port juniper-cascor's swept one-artifact publish template (juniper-cascor#777) to a fresh juniper-ml tree, all seven publishers, every edit an anchor asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the one-artifact template sweep's port to juniper-ml; brief tmp/ports/SWEEP_PORT_BRIEF.md)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py (the template's own sweep, juniper-cascor#777: this
         writer's model); util/ad-hoc/2026-11-15_juniper-ml_one_artifact_publish_port.py (this repository's first port,
         juniper-ml#2593); util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker the result
         must pass); util/ad-hoc/2026-11-24_publish_port_install_pins.json (the pinned install scripts: this port
         proposes its seven, the INSTALL_LINES below); util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
juniper-cascor#777 swept the one-artifact template (rulings 1 and 2 of 2026-11-16, ``PUBLISH_TAG_PREFIX``, the
comment corrections and the test hardening), and every port copies the swept text. juniper-ml has seven publishers
that carry the template (juniper-ml#2593): the meta-package's ``publish.yml`` and the six sub-packages'
``publish-<pkg>.yml``. This gives all seven the swept shape, in one change:

- Each workflow: the install check leaves the TestPyPI job for a job of its own, ``Verify the TestPyPI install``
  (``needs`` the TestPyPI job, ``contents: read`` alone, a sparse checkout of the one file its version is read from with
  ``persist-credentials: false``, and its step, which installs from ``$RUNNER_TEMP`` and reads the version under
  ``$GITHUB_WORKSPACE``; ``publish.yml``'s keeps its setup-python 3.12). The TestPyPI job drops its checkout (and
  ``publish.yml``'s its setup-python) and holds ``id-token: write`` alone; the PyPI job needs both. The ``env`` block
  gains ``PUBLISH_TAG_PREFIX`` (``v``, or ``<package>-v``) and each build guard's dispatch branch
  ``startsWith(github.ref_name, '<prefix>')``. Every template block and the republish job are cut out of
  juniper-cascor's ``publish.yml`` (``--template-dir``, pinned by sha256 with ``publish-protocol.yml``, whose
  sub-package banner the sub-packages take) and put in place of this tree's, never retyped, then cut out of the result
  again and compared. The install scripts are rebuilt from ``INSTALL_LINES`` (the pins this port proposes): the
  template's lag error after the last try, ``publish.yml``'s flag-form fetch and its ``ls -la`` without ``|| true``,
  ``python -c`` last in config-tools and doc-tools, and R4-5's ``find_spec`` for ci-tools and observability, which read
  metadata alone. Each result is parsed and its jobs, steps and permissions checked before anything is written.
- ``tests/test_publish_one_artifact.py``: written whole (``EMBED_TEST_PUBLISH_ONE_ARTIFACT``): #777's hardening and
  rehearsals ported to the seven publishers, the template digests pinned NORMALIZED (SWEEP item G / 23). Written only
  over the base it was derived from (``BASE_ONE_ARTIFACT_SHA256``): a test file ``main`` has moved is refused, never
  reverted. ``tests/test_publish_docs_bounds.py`` is new (it pins the bounds and lag errors the docs state), wired into
  ``ci.yml`` and the ``main-verify.yml`` battery. ``tests/test_publish_testpypi_verify.py`` and
  ``tests/test_publish_subpackage_workflows.py`` take anchored edits: the install check read from its job, a step or
  workflow not found a failure rather than a skip (R4-1), the TestPyPI job's pinned permissions ``id-token: write``.
- ``docs/REFERENCE.md`` (its ``Version`` patch-bumped and its ``Last Updated`` the ``--date``, header and footer, the
  suite count and list, the suite entries and both publish sections), ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``,
  ``AGENTS.md`` (the suite count, and ``Last Updated``, same length), ``CHANGELOG.md`` (one ``[Unreleased]`` / ``###
  Fixed`` entry, after the first port's, whose two superseded statements it marks) and
  ``notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md`` (§11.8's amendment of 2026-11-26).

The person-word: each workflow's is read at run time ("Overtoad" or "owner", as cascor's writer reads it), every
anchor that holds it is built from that value, and the new text names no person.

    python3 -I util/ad-hoc/2026-11-26_juniper-ml_one_artifact_sweep_port.py --tree <fresh clone> \\
        --changelog-cases N --changelog-mutations M \\
        [--template-dir <juniper-cascor .github/workflows at 5e3d9801>] [--date YYYY-MM-DD]

``--changelog-cases`` and ``--changelog-mutations`` are required, as positive whole numbers (92 and 55 reproduce
juniper-ml#2673, all three commits). ``--date`` (default: today, UTC) is the day the edited docs and ``publish.yml``'s
``Last Modified`` take; ``AGENTS.md``'s must be the UTC day CI runs ``Verify AGENTS.md Last Updated``. Exit status: 0
when every edit applied; 1 when an anchor did not match exactly once, an input moved, or a post-condition failed
(nothing is written then); 2 on a usage error. A second run on a tree it already ported refuses, as its anchors are
gone, and writes nothing.

The pull request's later commits, each also this writer's output:

- The second (CI's Python 3.12 lane): the package-check rehearsal's bare-directory case holds the wheel's metadata and
  an empty package directory, and both refusing cases assert the exact output. Its substring assertion had passed on
  3.13 and later only because their tracebacks quote the ``-c`` source.
- The third (the independent review's F1-F3 and N1-N5, 2026-11-26): what "Re-run failed jobs" does after a lag
  failure of either TestPyPI job (F1, REFERENCE and the notes); the waits and totals the docs state, in digits and
  pinned from each loop by ``tests/test_publish_docs_bounds.py`` (F2); the one-artifact module's docstring names no
  person (F3); the package check's "nothing" case asserts exit 1, no output and ``PackageNotFoundError`` (N1);
  cascor MANUAL's sentence for a version a plain dispatch published (N2); #777's date (N3); ``publish.yml``'s upload
  comment (N4) and its header's ``Last Modified`` (N5).

Landed with plan v1.15.18 on 2026-11-26 with five unused tuple targets renamed ``_`` (CodeQL's unused-local:
``package`` in ``install_job()``; ``package``, ``prod_id`` and ``step_name`` in ``install_step_old()``; ``step_name`` in
``workflow_edit()``), its output unchanged.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # the post-conditions parse the result; without PyYAML they cannot, so nothing is written
    yaml = None

# ─────────────────────────────────────────────────────────────────────────────────────────────
# The seven publishers
# ─────────────────────────────────────────────────────────────────────────────────────────────
INSTALL_JOB = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
META = "publish.yml"
#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job, PUBLISH_TAG_PREFIX, install step name, sparse path)
PUBLISHERS = {
    META: ("juniper-ml", "dist", "testpypi", "pypi", "v", "Verify TestPyPI install", "pyproject.toml"),
    "publish-ci-tools.yml": ("juniper-ci-tools", "juniper-ci-tools/dist", "publish-testpypi", "publish-pypi", "juniper-ci-tools-v", "Verify install from TestPyPI", "juniper-ci-tools/pyproject.toml"),
    "publish-config-tools.yml": ("juniper-config-tools", "juniper-config-tools/dist", "publish-testpypi", "publish-pypi", "juniper-config-tools-v", "Verify install from TestPyPI", "juniper-config-tools/pyproject.toml"),
    "publish-doc-tools.yml": ("juniper-doc-tools", "juniper-doc-tools/dist", "publish-testpypi", "publish-pypi", "juniper-doc-tools-v", "Verify install from TestPyPI", "juniper-doc-tools/pyproject.toml"),
    "publish-model-core.yml": ("juniper-model-core", "juniper-model-core/dist", "publish-testpypi", "publish-pypi", "juniper-model-core-v", "Verify install from TestPyPI (no-deps, version-only import)", "juniper-model-core/juniper_model_core/_version.py"),
    "publish-observability.yml": ("juniper-observability", "juniper-observability/dist", "publish-testpypi", "publish-pypi", "juniper-observability-v", "Verify install from TestPyPI", "juniper-observability/pyproject.toml"),
    "publish-service-core.yml": ("juniper-service-core", "juniper-service-core/dist", "publish-testpypi", "publish-pypi", "juniper-service-core-v", "Verify install from TestPyPI", "juniper-service-core/pyproject.toml"),
}
SUB_PACKAGES = tuple(name for name in PUBLISHERS if name != META)
WORKFLOW_DIR = ".github/workflows"

# The template: juniper-cascor main 5e3d9801 (its three publishers byte-identical to juniper-cascor#777's merge f5ed3017).
TEMPLATE_DEFAULT = Path(__file__).resolve().parents[2] / "tmp" / "ports" / "clones" / "juniper-cascor" / ".github" / "workflows"
TEMPLATE_SHA256 = {
    "publish.yml": "b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b",
    "publish-protocol.yml": "f37c3ef60ffc65a9c4abd16ac5894575fc60075dfc1e551db303d7bb7189cfbb",
}
TEMPLATE_COMMENT = "      # One-artifact publish template"
STEP_LINE = re.compile(r"^      (?:- |# )")
JOB_LINE = re.compile(r"^  [a-z][a-z0-9-]*:\s*$")
USES_LINE = re.compile(r"^(\s*(?:- )?uses: )([^@\s]+)@\S+(?:\s+#\s*v\S*)?$")
ACTIONS = ("actions/checkout", "actions/setup-python", "actions/upload-artifact", "actions/download-artifact", "pypa/gh-action-pypi-publish")
LAG_LINE = "# TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so."
LAG_ERROR = "is not installable from TestPyPI after {tries} tries (index lag?): Re-run failed jobs; a real failure repeats"
CD = 'cd "${RUNNER_TEMP}"'
CD_IMPORT = [
    "# `python -c` puts its working directory first on sys.path: install and import from the runner's temporary",
    "# directory, outside the sparse checkout the version is read from.",
]
CD_INSPECT = [
    "# `python -c` puts its working directory first on sys.path: install and inspect the package from the runner's",
    "# temporary directory, outside the sparse checkout the version is read from.",
]


def sub_loop(package: str) -> list[str]:
    """The sub-package publishers' retry, as juniper-cascor's sub-package template runs it: five tries, 10 s apart, and
    after the fifth failure the template's lag error."""
    return [
        LAG_LINE,
        "for attempt in 1 2 3 4 5; do",
        "  if pip install \\",
        "    --no-deps \\",
        "    --index-url https://test.pypi.org/simple/ \\",
        f'    "{package}==${{version}}"; then',
        "    break",
        "  fi",
        '  if [ "${attempt}" -eq 5 ]; then',
        f'    echo "::error::{package} ${{version}} {LAG_ERROR.format(tries=5)}"',
        "    exit 1",
        "  fi",
        '  echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
        "  sleep 10",
        "done",
    ]


def pyproject_version(package: str) -> str:
    return f"""version=$(grep '^version' "${{GITHUB_WORKSPACE}}/{package}/pyproject.toml" | head -1 | sed -E 's/version = "(.+)"/\\1/')"""


SECURITY_NOTE = [
    "# NOTE (security): install with --no-deps against TestPyPI only. Do NOT add a",
    "# production-PyPI fallback index here — with --no-deps no deps are fetched, so a",
    "# fallback only risks resolving a squatted target package. The retry loop below",
    "# covers TestPyPI index lag.",
]
FIND_SPEC_NOTE = [
    "# Metadata alone passes a wheel that lacks the package, so find_spec must also locate it, which runs none of",
    "# its code. SystemExit fails the step: PYTHONOPTIMIZE would strip an assert statement.",
]


def package_check(package: str, module: str) -> str:
    """R4-5: juniper-cascor's protocol check, its neutral line (no "OK" before the verdict), for PACKAGE and MODULE."""
    return f"""python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{module}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{package}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {module} package')\""""


#: workflow -> its install step's final script, line by line: the pin this port proposes (pins.proposed.json).
INSTALL_LINES = {
    META: [
        *CD_IMPORT,
        CD,
        """VERSION=$(python -c "import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])")""",
        "# ── TWO-PHASE VERIFICATION (2026-08-08 amendment, owner-approved) ────────────",
        "# pip has NO index priority. --index-url plus --extra-index-url form ONE merged",
        "# namespace and pip picks the HIGHEST version found across both. That is a",
        "# dependency-confusion vector: a TestPyPI squatter outranks the real package.",
        "# Live failure -- TestPyPI `fastapi 1.0` (a broken sdist) beat production",
        "# fastapi 0.141.1 and killed the v0.7.0 verify (run 31281873275).",
        "# Splitting the phases removes the merged namespace entirely while still",
        "# exercising genuine extras/dependency resolution.",
        "#",
        "# PHASE 1 -- artifact provenance. Fetch the juniper-ml artifact from TestPyPI",
        "# and ONLY TestPyPI, at the exact version this Release built, so the thing we",
        "# go on to install is provably the artifact just uploaded. --no-deps keeps this",
        "# phase about provenance alone: no dependency is resolved here, so there is no",
        "# namespace to confuse.",
        'DOWNLOAD_DIR="$(mktemp -d)"',
        "# TestPyPI's simple index is CDN-fronted and lags an upload by ~5-30s, so the",
        "# first fetch of a just-published version can 404. This was an unconditional",
        "# `sleep 30` -- 77% of a measured 39s step, paid in full on EVERY publish even",
        "# when the index was already warm, and still a coin-flip if propagation ran",
        "# long. A bounded poll is better in both directions: it returns as soon as the",
        "# artifact is servable (usually the first attempt), and tolerates a slow CDN",
        "# instead of failing the release. ~60s ceiling, then a real error.",
        "# The fetch stays on ONE line and outside any `if` condition: it is the",
        "# provenance phase tests/test_publish_testpypi_verify.py parses, and that",
        "# parser matches `^pip download` against the STRIPPED line. A literal attempt",
        "# list rather than $(seq ...) keeps the loop free of an external command. A",
        "# fetch that fails on the left of `&&` does not stop the step under `bash -e`,",
        "# so the loop retries it without `set +e`; after the tenth failure the step",
        "# fails with the template's lag error.",
        "FETCHED=0",
        "for attempt in 1 2 3 4 5 6 7 8 9 10; do",
        '  pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}" && { FETCHED=1; break; }',
        '  echo "TestPyPI has not served juniper-ml==${VERSION} yet (attempt ${attempt}/10) -- retrying in 6s"',
        "  sleep 6",
        "done",
        'if [ "${FETCHED}" -ne 1 ]; then',
        f'  echo "::error::juniper-ml ${{VERSION}} {LAG_ERROR.format(tries=10)}"',
        "  exit 1",
        "fi",
        'WHEEL="${DOWNLOAD_DIR}/juniper_ml-${VERSION}-py3-none-any.whl"',
        'if [ ! -f "${WHEEL}" ]; then',
        '  echo "::error::TestPyPI did not serve the expected wheel: ${WHEEL}"',
        '  ls -la "${DOWNLOAD_DIR}"',
        "  exit 1",
        "fi",
        'echo "Phase 1 OK: fetched ${WHEEL} from TestPyPI"',
        "# PHASE 2 -- dependency resolution from ONE index (production PyPI). The install",
        "# target is the LOCAL TestPyPI wheel, so PyPI can never serve the target itself;",
        "# every dependency and extra resolves from production PyPI alone. Deliberately",
        "# NO --no-deps: extras resolution is genuinely exercised, which is the whole",
        "# point of this gate. Local-wheel-with-extras (`<wheel>[extra]`) is standard pip",
        "# requirement syntax and does resolve the extra's dependencies.",
        "#",
        "# Step 1: bare install. Confirms the downloaded artifact installs and",
        "# importlib.metadata sees the expected version.",
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}"',
        """python -c "import importlib.metadata; print(f'TestPyPI bare OK: juniper-ml v{importlib.metadata.version(\\"juniper-ml\\")}')\"""",
        "# Step 2: [clients] extras-resolution install. Exercises the",
        "# [project.optional-dependencies] surface against the published",
        "# metadata so a broken extras declaration (mistyped name, missing",
        "# roll-up into [all], dangling self-reference) fails the publish",
        "# rather than landing on PyPI silently. [clients] is one of two",
        "# light extras (data-client + cascor-client, no torch); it walks",
        "# the full resolver path. Both deps come from production PyPI.",
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}[clients]"',
        """python -c "import juniper_data_client, juniper_cascor_client; print(f'TestPyPI extras OK: [clients] resolved data-client={juniper_data_client.__version__ if hasattr(juniper_data_client, \\"__version__\\") else \\"?\\"}, cascor-client={juniper_cascor_client.__version__ if hasattr(juniper_cascor_client, \\"__version__\\") else \\"?\\"}')\"""",
        "# Step 3: [tools] extras-resolution install. Pairs with step 2",
        "# to cover both light extras at publish time -- if [tools] were",
        "# broken, step 2 would still pass and ship. juniper-ci-tools,",
        "# juniper-doc-tools, juniper-observability are all small and",
        "# already on production PyPI; no torch involved.",
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}[tools]"',
        """python -c "import juniper_ci_tools, juniper_doc_tools, juniper_observability; print(f'TestPyPI extras OK: [tools] resolved ci-tools={juniper_ci_tools.__version__ if hasattr(juniper_ci_tools, \\"__version__\\") else \\"?\\"}, doc-tools={juniper_doc_tools.__version__ if hasattr(juniper_doc_tools, \\"__version__\\") else \\"?\\"}, observability={juniper_observability.__version__ if hasattr(juniper_observability, \\"__version__\\") else \\"?\\"}')\"""",
    ],
    "publish-ci-tools.yml": [
        "set -euo pipefail",
        *CD_INSPECT,
        CD,
        pyproject_version("juniper-ci-tools"),
        *SECURITY_NOTE,
        *sub_loop("juniper-ci-tools"),
        "# --no-deps leaves runtime deps (PyYAML, packaging) absent, so importing the package",
        "# or running its console scripts (which import juniper_ci_tools.generate_dep_docs -> yaml)",
        "# fails here. Read the installed version from dist-info METADATA instead (imports no",
        "# package code); the full import / console-script exercise runs in the package's CI tests.",
        *FIND_SPEC_NOTE,
        package_check("juniper-ci-tools", "juniper_ci_tools"),
    ],
    "publish-config-tools.yml": [
        "set -euo pipefail",
        *CD_IMPORT,
        CD,
        pyproject_version("juniper-config-tools"),
        *sub_loop("juniper-config-tools"),
        "python -m juniper_config_tools --version",
        """python -c "import juniper_config_tools; print('TestPyPI install OK', juniper_config_tools.__version__)\"""",
    ],
    "publish-doc-tools.yml": [
        "set -euo pipefail",
        *CD_IMPORT,
        CD,
        pyproject_version("juniper-doc-tools"),
        *sub_loop("juniper-doc-tools"),
        "juniper-check-doc-links --version",
        "python -m juniper_doc_tools --version",
        """python -c "import juniper_doc_tools; print('TestPyPI install OK', juniper_doc_tools.__version__)\"""",
    ],
    "publish-model-core.yml": [
        "set -euo pipefail",
        *CD_IMPORT,
        CD,
        """version=$(grep -E '^__version__' "${GITHUB_WORKSPACE}/juniper-model-core/juniper_model_core/_version.py" | sed -E 's/.*"(.+)".*/\\1/')""",
        *sub_loop("juniper-model-core"),
        """python -c "import juniper_model_core; print('TestPyPI install OK', juniper_model_core.__version__)\"""",
    ],
    "publish-observability.yml": [
        "set -euo pipefail",
        *CD_INSPECT,
        CD,
        pyproject_version("juniper-observability"),
        *SECURITY_NOTE,
        *sub_loop("juniper-observability"),
        "# --no-deps leaves runtime deps (pydantic, starlette) absent, so importing the package",
        "# fails here (juniper_observability.__init__ -> health.models -> pydantic). Read the",
        "# installed version from dist-info METADATA instead (imports no package code); the full",
        "# import exercise runs in the package's CI tests.",
        *FIND_SPEC_NOTE,
        package_check("juniper-observability", "juniper_observability"),
    ],
    "publish-service-core.yml": [
        "set -euo pipefail",
        *CD_IMPORT,
        CD,
        pyproject_version("juniper-service-core"),
        *SECURITY_NOTE,
        *sub_loop("juniper-service-core"),
        """python -c "import juniper_service_core; print('OK', juniper_service_core.__version__)\"""",
    ],
}
#: workflow -> the base install step's commands (comment and blank lines dropped), in order: each new script keeps every
#: one of them, in order, and adds only what INSTALL_ADDED names. Read from the base file, so a base that moved is refused.
INSTALL_ADDED = {
    META: "the cd, the version path, the flag-form fetch, the lag error and ls without || true (R5-F5)",
    "publish-ci-tools.yml": "the cd, the version path, the lag error, the find_spec check (R4-5)",
    "publish-observability.yml": "the cd, the version path, the lag error, the find_spec check (R4-5)",
}

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Helpers (the method of util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py)
# ─────────────────────────────────────────────────────────────────────────────────────────────
class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:100]!r}")
    return text.replace(old, new)


def between(text: str, start: str, end: str, where: str) -> str:
    """The text from START (included) to END (excluded), each matching exactly once, START first."""
    for anchor in (start, end):
        if text.count(anchor) != 1:
            raise Refused(f"{where}: anchor matched {text.count(anchor)} times, expected 1: {anchor[:100]!r}")
    a, b = text.index(start), text.index(end)
    if a >= b:
        raise Refused(f"{where}: {start[:40]!r} does not come before {end[:40]!r}")
    return text[a:b]


def line_of(text: str, prefix: str, where: str) -> str:
    """The one whole line (with its newline) of TEXT that starts with PREFIX."""
    found = [line for line in text.splitlines(keepends=True) if line.startswith(prefix)]
    if len(found) != 1:
        raise Refused(f"{where}: {len(found)} lines start with {prefix[:80]!r}, expected 1")
    return found[0]


def action_pin(text: str, action: str, where: str) -> str:
    """The one ``<action>@<sha>  # vX.Y.Z`` pin a workflow uses (Dependabot bumps every copy in a file together)."""
    pins = set(re.findall(rf"{re.escape(action)}@[0-9a-f]{{40}}  # v[0-9][0-9.]*", text))
    if len(pins) != 1:
        raise Refused(f"{where}: {len(pins)} distinct {action} pins, expected 1: {sorted(pins)}")
    return pins.pop()


def template_blocks(text: str, where: str) -> "list[tuple[str, int, int]]":
    """Each template block as (``<job>/<step name>``, first line, end line): from its "One-artifact publish template"
    comment to the end of its step, comments included (the rule the repository's test cuts them by)."""
    lines = text.splitlines(keepends=True)
    found: list[tuple[str, int, int]] = []
    job = ""
    i = 0
    while i < len(lines):
        if JOB_LINE.match(lines[i]):
            job = lines[i].strip().rstrip(":")
        if lines[i].startswith(TEMPLATE_COMMENT):
            first = next((j for j in range(i, len(lines)) if lines[j].startswith("      - ")), None)
            if first is None:
                raise Refused(f"{where}: a template comment at line {i + 1} has no step after it")
            name = re.sub(r"^      - name:\s*", "", lines[first]).strip()
            end = first + 1
            while end < len(lines) and not STEP_LINE.match(lines[end]) and not (lines[end].strip() and len(lines[end]) - len(lines[end].lstrip(" ")) <= 2):
                end += 1
            # A block ends at its step's last non-blank line: the blank lines after it belong to the file's layout.
            while end > first + 1 and not lines[end - 1].strip():
                end -= 1
            found.append((f"{job}/{name}", i, end))
            i = end
            continue
        i += 1
    keys = [key for key, _, _ in found]
    if len(set(keys)) != len(keys):
        raise Refused(f"{where}: two template blocks share a key: {keys}")
    return found


def roles(keys: "list[str]", test_id: str, prod_id: str) -> "list[str]":
    """Block keys with the job ids read as their roles, so a sub-package's publish-testpypi/... is the template's
    testpypi/... ."""
    named = {test_id: "testpypi", prod_id: "pypi"}
    return [f"{named.get(key.split('/', 1)[0], key.split('/', 1)[0])}/{key.split('/', 1)[1]}" for key in keys]


def block_texts(text: str, where: str, test_id: str = "testpypi", prod_id: str = "pypi") -> "dict[str, str]":
    lines = text.splitlines(keepends=True)
    found = template_blocks(text, where)
    return dict(zip(roles([key for key, _, _ in found], test_id, prod_id), ("".join(lines[a:b]) for _, a, b in found)))


def republish_start(text: str, where: str) -> int:
    """The republish job's first character: its comment banner. It must be the file's last job."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == "  republish:\n"]
    if len(at) != 1:
        raise Refused(f"{where}: {len(at)} republish jobs")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    if any(JOB_LINE.match(line) for line in lines[at[0] + 1 :]):
        raise Refused(f"{where}: the republish job is not the file's last job")
    return sum(len(line) for line in lines[:start])


def normalized(block: str) -> str:
    """BLOCK with every ``uses:`` line reduced to its action's name (the digests the test module pins, item G)."""
    return "".join(USES_LINE.sub(r"\1\2", line) + "\n" for line in block.splitlines())


def indented(lines: "list[str]", indent: str) -> str:
    return "".join(f"{indent}{line}\n" if line else "\n" for line in lines)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The workflow edits
# ─────────────────────────────────────────────────────────────────────────────────────────────
DISPATCH_OLD_HEAD = "".join(
    (
        "  # Manual dispatch, from the release TAG (both publish environments admit tags only). Without the input it re-fires\n",
        "  # the whole publish: it builds again, so it works only while TestPyPI does not hold the version yet. With\n",
    )
)
DISPATCH_OLD_META = DISPATCH_OLD_HEAD + "  # republish_from_testpypi it runs the republish job alone, which copies TestPyPI's files to PyPI and builds nothing:\n"
DISPATCH_OLD_SUB = DISPATCH_OLD_HEAD + "  # republish_from_testpypi it runs the republish job alone, which copies TestPyPI's files to PyPI and builds nothing.\n"
DISPATCH_NEW_META = "".join(
    (
        "  # Manual dispatch, from the release TAG (both publish environments admit tags only). Without the input it re-fires\n",
        "  # the whole publish, from a `v` tag only: it builds again, so it works only while TestPyPI does not hold the\n",
        "  # version yet. With republish_from_testpypi it runs the republish job alone, which builds nothing and copies\n",
        "  # TestPyPI's files to PyPI only when the tag's newest release run passed its TestPyPI jobs (ruling 1 of 2026-11-16):\n",
    )
)
DISPATCH_NEW_SUB = "".join(
    (
        "  # Manual dispatch, from the release TAG (both publish environments admit tags only). Without the input it re-fires\n",
        "  # the whole publish, from this package's own tag only: it builds again, so it works only while TestPyPI does not\n",
        "  # hold the version yet. With republish_from_testpypi it runs the republish job alone, which builds nothing and\n",
        "  # copies TestPyPI's files to PyPI only when the tag's newest release run passed its TestPyPI jobs (ruling 1 of\n",
        "  # 2026-11-16).\n",
    )
)
META_HEADER_OLD = "".join(
    (
        "#    Triggered by GitHub release. Builds the sdist and wheel ONCE, records\n",
        "#    their sha256 in SHA256SUMS and hands both publish jobs that one\n",
        "#    artifact: TestPyPI takes it first and must then serve exactly those\n",
        "#    sha256 before the two-phase install verification runs, and PyPI takes\n",
        "#    it only after TestPyPI is checked again. Uses OIDC trusted publishing\n",
        "#    (no API tokens).\n",
        "#\n",
        "#    The steps marked \"one-artifact publish template\", and the republish\n",
        "#    job, are juniper-cascor's publish.yml copied verbatim (juniper-cascor#763\n",
        "#    and #767): they read nothing from this repository but the two `env`\n",
        "#    values below. The republish job is step 1 of the {word}'s recovery ladder\n",
        "#    for a release that never reached PyPI (docs/REFERENCE.md § Independent\n",
        "#    Sibling Package Publish Pipelines).\n",
    )
)
META_HEADER_NEW = "".join(
    (
        "#    Triggered by GitHub release. Builds the sdist and wheel ONCE, records\n",
        "#    their sha256 in SHA256SUMS and hands both publish jobs that one\n",
        "#    artifact: TestPyPI takes it first and must then serve exactly those\n",
        "#    sha256, a job that cannot mint a credential runs the two-phase install\n",
        "#    verification against TestPyPI's wheel, and PyPI takes it only after\n",
        "#    that install passed and TestPyPI is checked again. Uses OIDC trusted\n",
        "#    publishing (no API tokens).\n",
        "#\n",
        "#    The steps marked \"one-artifact publish template\", and the republish\n",
        "#    job, are juniper-cascor's publish.yml copied verbatim (juniper-cascor#763,\n",
        "#    #767 and #777): they read nothing from this repository but the three\n",
        "#    `env` values below. The republish job is step 1 of the recovery ladder\n",
        "#    of 2026-11-15 for a release that never reached PyPI (docs/REFERENCE.md\n",
        "#    § Independent Sibling Package Publish Pipelines).\n",
    )
)
META_PERMISSIONS_OLD = "".join(
    (
        "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15): each job states what it needs, and only the\n",
        "# jobs that upload hold `id-token: write`. The build job compiles untrusted-ish tree content and has no business being\n",
        "# able to mint a PyPI OIDC credential.\n",
    )
)
META_PERMISSIONS_NEW = "".join(
    (
        "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15): each job states what it needs, and only the\n",
        "# jobs that upload hold `id-token: write`. The build job compiles untrusted-ish tree content and has no business being\n",
        "# able to mint a PyPI OIDC credential, and neither has the install check (ruling 2 of 2026-11-16), which installs\n",
        "# what TestPyPI serves.\n",
    )
)
SUB_PERMISSIONS_OLD = "".join(
    (
        "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15): each job adds what it needs to this, and only\n",
        "# the jobs that upload add `id-token: write`. The build job has no business being able to mint a PyPI OIDC credential.\n",
    )
)
SUB_PERMISSIONS_TAIL = "# The build job and the install check have no business being able to mint a PyPI OIDC credential.\n"
META_GUARD_OLD = "".join(
    (
        "    # Release-convention guard: publish juniper-ml only for meta-package `v*` releases, NOT for a\n",
        "    # shared/sub-package `juniper-<pkg>-v*` release (which also fires this release-triggered workflow).\n",
        "    # workflow_dispatch is the manual escape hatch: a dispatch from the release tag re-fires the whole\n",
        "    # publish, unless it asks for the republish job. Both publish jobs depend on this one, so this guard\n",
        "    # gates the whole pipeline.\n",
        "    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, 'v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
    )
)
#: The template's rc*/hf* sentences (SWEEP item 12), as juniper-cascor's guard comment words them; here the note is this
#: repository's own, so "juniper-ml's " goes.
GUARD_SENTENCES = "".join(
    (
        "The publish environments also admit `rc*` and `hf*` tags, kept for future release-candidate and hotfix conventions ",
        "(D2 of juniper-ml's notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md). This guard skips ",
        "them: a convention that adopts one must widen it, and PUBLISH_TAG_PREFIX with it.",
    )
)
META_GUARD_NEW = "".join(
    (
        "    # Release-convention guard: publish juniper-ml only for meta-package `v*` releases, NOT for a\n",
        "    # shared/sub-package `juniper-<pkg>-v*` release (which also fires this release-triggered workflow).\n",
        "    # workflow_dispatch is the manual escape hatch: a dispatch from a `v` release tag re-fires the whole\n",
        "    # publish, unless it asks for the republish job; from another package's tag it builds nothing, since it\n",
        "    # would publish the meta-package's files under that tag's run. Both publish jobs depend on this one, so\n",
        "    # this guard gates the whole pipeline. The publish environments also admit `rc*` and `hf*` tags, kept for\n",
        "    # future release-candidate and hotfix conventions (D2 of\n",
        "    # notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md). This guard skips them: a\n",
        "    # convention that adopts one must widen it, and PUBLISH_TAG_PREFIX with it.\n",
        "    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, 'v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, 'v'))\n",
    )
)
SUB_GUARD_OLD = "".join(
    (
        "    # For a `release` event, run only when the release is THIS package's tag -- a release for another\n",
        "    # package (or the meta `v*` release) also fires this workflow and must be skipped. A dispatch runs it,\n",
        "    # unless it asks for the republish job. Downstream jobs `needs: build`, so this one guard gates the\n",
        "    # whole pipeline.\n",
        "    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
    )
)
SUB_GUARD_NEW = "".join(
    (
        "    # For a `release` event, run only when the release is THIS package's tag -- a release for another\n",
        "    # package (or the meta `v*` release) also fires this workflow and must be skipped. A dispatch runs it only\n",
        "    # from this package's own tag, and only when it does not ask for the republish job: from another\n",
        "    # package's tag it would publish this package's files under that tag's run. Downstream jobs\n",
        "    # `needs: build`, so this one guard gates the whole pipeline.\n",
        "    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))\n",
    )
)
META_TESTPYPI_OLD = "".join(
    (
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  # TestPyPI: Publish and verify install\n",
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  testpypi:\n",
        "    name: Publish to TestPyPI\n",
        "    needs: build\n",
        "    runs-on: ubuntu-latest\n",
        "    # P4: OIDC minting lives here, not at workflow level.\n",
        "    permissions:\n",
        "      id-token: write\n",
        "      contents: read\n",
        "    environment: testpypi\n",
        "    steps:\n",
        "      - uses: {checkout}\n",
        "\n",
        "      - uses: {setup_python}\n",
        "        with:\n",
        "          python-version: \"3.12\"\n",
        "\n",
    )
)
META_TESTPYPI_NEW = "".join(
    (
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  # TestPyPI: Publish, then verify the install in a job of its own\n",
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  testpypi:\n",
        "    name: Publish to TestPyPI\n",
        "    needs: build\n",
        "    runs-on: ubuntu-latest\n",
        "    # P4: OIDC minting lives here, not at workflow level.\n",
        "    permissions:\n",
        "{permission}",
        "    environment: testpypi\n",
        "    steps:\n",
    )
)
SUB_TESTPYPI_OLD = "".join(
    (
        "    # P4: OIDC minting lives here, not at workflow level.\n",
        "    permissions:\n",
        "      id-token: write\n",
        "      contents: read\n",
        "    environment:\n",
        "      name: testpypi\n",
    )
)
SUB_TESTPYPI_NEW = "".join(
    (
        "    # P4: OIDC minting lives here, not at workflow level.\n",
        "    permissions:\n",
        "{permission}",
        "    environment:\n",
        "      name: testpypi\n",
    )
)
META_UPLOAD_COMMENT_OLD = "".join(
    (
        "          # No skip-existing (the one-artifact publish, 2026-11-15). It made a re-cut Release a no-op here, but it\n",
        "          # kept an earlier build under the same file name silently, so the install check below could test a file\n",
        "          # PyPI would never receive. A re-cut that builds new files for a version TestPyPI holds now fails here;\n",
        "          # the republish dispatch finishes such a release.\n",
    )
)
META_UPLOAD_COMMENT_NEW = "".join(
    (
        "          # No skip-existing (the one-artifact publish, 2026-11-15). It made a re-cut Release a no-op here, but it\n",
        "          # kept an earlier build under the same file name silently, so the install check could test a file PyPI\n",
        "          # would never receive. A re-cut that builds new files for a version TestPyPI holds now fails here, and\n",
        "          # its run becomes the tag's newest release run, which the republish dispatch then refuses (ruling 1 of\n",
        "          # 2026-11-16): finish a release whose version TestPyPI holds with the republish dispatch, before any re-cut.\n",
    )
)
META_PYPI_BANNER = "".join(
    (
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  # PyPI: Publish after TestPyPI verification\n",
        "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n",
        "  pypi:\n",
        "    name: Publish to PyPI\n",
        "    needs: testpypi\n",
    )
)
SUB_PYPI_HEAD = "  publish-pypi:\n    name: Publish to PyPI\n    needs: publish-testpypi\n"


def install_job(workflow: str, template: str, protocol: str, setup_python: str) -> str:
    """The new job, ``Verify the TestPyPI install``: juniper-cascor's job comment and head (``publish-protocol.yml``'s, whose
    permission comment names the sparse checkout every juniper-ml publisher needs), this publisher's setup and checkout,
    and its install step running INSTALL_LINES."""
    _, _, test_id, _, _, step_name, sparse = PUBLISHERS[workflow]
    head = between(protocol, "  # Ruling 2 of 2026-11-16: the install check runs in a job of its own", "      # A sparse checkout, for the file the version is read from", "publish-protocol.yml")
    if between(template, "  # Ruling 2 of 2026-11-16: the install check runs in a job of its own", "  verify-testpypi-install:\n", "the template") not in head:
        raise Refused("the template's install-job comment differs between its publish.yml and publish-protocol.yml")
    head = replace_once(head, "    needs: publish-testpypi\n", f"    needs: {test_id}\n", "the install job's head")
    checkout = between(protocol, "      # A sparse checkout, for the file the version is read from", "      - name: Verify install from TestPyPI\n", "publish-protocol.yml")
    checkout = replace_once(checkout, "            juniper-cascor-protocol/pyproject.toml\n", f"            {sparse}\n", "the install job's checkout")
    steps = ""
    if workflow == META:
        # The meta-package's check ran in a job with setup-python 3.12; it keeps it, before the checkout, as the template's
        # own install job starts with it.
        steps = f"      - uses: {setup_python}\n        with:\n          python-version: \"3.12\"\n\n"
    step = f"      - name: {step_name}\n        run: |\n" + indented(INSTALL_LINES[workflow], "          ")
    return head + steps + checkout + step + "\n"


def install_step_old(text: str, workflow: str, where: str) -> str:
    """The base's install check in the TestPyPI job (with a sub-package's sparse checkout before it), to its job's end."""
    _, _, _, _, _, _, _ = PUBLISHERS[workflow]
    if workflow == META:
        return between(text, "      - name: Verify TestPyPI install\n", META_PYPI_BANNER, where)
    start = "      - uses: " + action_pin(text, "actions/checkout", where) + "\n        with:\n          sparse-checkout: |\n"
    return between(text, start, SUB_PYPI_HEAD, where)


def base_commands(old_step: str) -> "list[str]":
    run = old_step.split("        run: |\n", 1)[1]
    return [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]


def check_install_lines(workflow: str, old_step: str) -> None:
    """Each new script keeps the base's commands in order, changed only where this port says (INSTALL_ADDED), and takes
    the template's lag error after its last try. No `||`, `set +e` or `assert` can switch a failure off."""
    old = base_commands(old_step)
    new = [line.strip() for line in INSTALL_LINES[workflow] if line.strip() and not line.strip().startswith("#")]
    text = "\n".join(new)
    if "||" in text or "set +e" in text or "assert " in text or "${{" in text:
        raise Refused(f"{workflow}: the new install script lets a failure pass, or pastes an expression")
    if new.count(CD) != 1 or new[: 2 if new[0] == "set -euo pipefail" else 1][-1] != CD:
        raise Refused(f"{workflow}: the new install script does not start in $RUNNER_TEMP")
    tries = 10 if workflow == META else 5
    if sum(LAG_ERROR.format(tries=tries) in line for line in new) != 1:
        raise Refused(f"{workflow}: the new install script does not hold the template's lag error once")
    if workflow == META:
        # The simulation's three edits (R5-F5): the flag-form fetch for the `set +e` block, `ls -la` without `|| true`,
        # the template's lag error for the old one; and the cd, with the version read under $GITHUB_WORKSPACE.
        swaps = {
            'pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}"': 'pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}" && { FETCHED=1; break; }',
            'ls -la "${DOWNLOAD_DIR}" || true': 'ls -la "${DOWNLOAD_DIR}"',
            'echo "::error::TestPyPI never served juniper-ml==${VERSION} within ~60s of upload"': f'echo "::error::juniper-ml ${{VERSION}} {LAG_ERROR.format(tries=10)}"',
            """VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")""": INSTALL_LINES[META][3],
        }
        dropped = ["set +e", "DL_RC=$?", "set -e", 'if [ "${DL_RC}" -eq 0 ]; then', "FETCHED=1", 'echo "TestPyPI served juniper-ml==${VERSION} on attempt ${attempt}"', "break", "fi"]
        expect = [CD]
        skip = list(dropped)
        for command in old:
            if skip and command == skip[0] and command in dropped:
                skip.pop(0)
                continue
            expect.append(swaps.get(command, command))
        if expect != new or skip:
            raise Refused(f"{workflow}: the new install script is not the base's with the three edits (R5-F5), the cd and the workspace path")
        return
    package = PUBLISHERS[workflow][0]
    module = package.replace("-", "_")
    if old[0] != "set -euo pipefail":
        raise Refused(f"{workflow}: the base's install step no longer starts with set -euo pipefail")
    # The cd first, then the version line, read under $GITHUB_WORKSPACE.
    sparse = PUBLISHERS[workflow][6]
    if new[2] != old[1].replace(f" {sparse} ", f' "${{GITHUB_WORKSPACE}}/{sparse}" ', 1) or new[2] == old[1]:
        raise Refused(f"{workflow}: the new version line is not the base's, read under $GITHUB_WORKSPACE: {old[1]!r}")
    expect = [old[0], CD, new[2]] + old[2:]
    # The template's lag branch, before the loop's retry message: after the fifth failed try, the lag error and exit 1.
    retry = next(i for i, c in enumerate(expect) if c.startswith('echo "TestPyPI index lag'))
    expect[retry:retry] = ['if [ "${attempt}" -eq 5 ]; then', f'echo "::error::{package} ${{version}} {LAG_ERROR.format(tries=5)}"', "exit 1", "fi"]
    if workflow in ("publish-config-tools.yml", "publish-doc-tools.yml"):
        # The reorder variant: the `python -c` check runs last.
        done = expect.index("done")
        checks = expect[done + 1 :]
        expect = expect[: done + 1] + [c for c in checks if not c.startswith("python -c ")] + [c for c in checks if c.startswith("python -c ")]
    if workflow in ("publish-ci-tools.yml", "publish-observability.yml"):
        # R4-5: the metadata-only check gains juniper-cascor's find_spec check, in its neutral form.
        expect[-1] = package_check(package, module)
    if expect != new:
        raise Refused(f"{workflow}: the new install script is not the base's commands with this port's changes: {[c for c in new if c not in expect] or [c for c in expect if c not in new]}")


def workflow_edit(workflow: str, text: str, template: str, protocol: str, date: str) -> str:
    """One publisher swept: the template's blocks and republish job, PUBLISH_TAG_PREFIX, the install check's own job, and
    the comments the sweep corrects. Every anchor must match once."""
    where = f"{WORKFLOW_DIR}/{workflow}"
    package, dist, test_id, prod_id, prefix, _, sparse = PUBLISHERS[workflow]
    for action in ACTIONS:
        if action_pin(text, action, where) != action_pin(template, action, "the template"):
            raise Refused(f"{where}: {action} is pinned at another ref than the template's: re-port only after the refs agree")
    checkout = action_pin(text, "actions/checkout", where)
    setup_python = action_pin(text, "actions/setup-python", where)
    word = "Overtoad" if "  # The Overtoad's recovery ladder, step 1 (2026-11-15)" in text else "owner"
    sub = workflow != META
    # The dispatch comment: a plain dispatch builds only from this package's tag; the republish needs the release run.
    text = replace_once(text, DISPATCH_OLD_SUB if sub else DISPATCH_OLD_META, DISPATCH_NEW_SUB if sub else DISPATCH_NEW_META, where)
    if sub:
        # The sweep's comment correction: a job's own permissions REPLACE this block (juniper-cascor's words).
        perm = between(protocol, "# A job's own `permissions` replace this block rather than add to it", "permissions:\n  contents: read\n", "publish-protocol.yml")
        text = replace_once(text, SUB_PERMISSIONS_OLD, "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15).\n" + perm + SUB_PERMISSIONS_TAIL, where)
        env_comment = between(protocol, "  # The one-artifact publish template's three parameters (see publish.yml)", "  PUBLISH_PACKAGE: juniper-cascor-protocol\n", "publish-protocol.yml")
        text = replace_once(text, "  # The one-artifact publish template's two parameters (see publish.yml): the distribution's name on PyPI and\n  # TestPyPI, and the directory the build writes the sdist and wheel to, relative to the workspace.\n", env_comment, where)
        text = replace_once(text, SUB_GUARD_OLD.replace("{prefix}", prefix), SUB_GUARD_NEW.replace("{prefix}", prefix), where)
    else:
        text = replace_once(text, "# Version:       0.4.0\n", "# Version:       0.5.0\n", where)
        text = replace_once(text, "# Last Modified: 2026-11-15\n", f"# Last Modified: {date}\n", where)
        text = replace_once(text, META_HEADER_OLD.replace("{word}", word), META_HEADER_NEW, where)
        text = replace_once(text, META_PERMISSIONS_OLD, META_PERMISSIONS_NEW, where)
        env_comment = between(template, "  # The one-artifact publish template's three parameters:", "  PUBLISH_PACKAGE: juniper-cascor\n", "the template")
        text = replace_once(text, "  # The one-artifact publish template's two parameters: the distribution's name on PyPI and TestPyPI,\n  # and the directory the build writes the sdist and wheel to, relative to the workspace.\n", env_comment, where)
        guard_comment = between(template, "    # Release-convention guard: publish juniper-cascor only", "    if: startsWith(github.event.release.tag_name, 'v')\n", "the template")
        if GUARD_SENTENCES not in " ".join(line.strip().lstrip("#").strip() for line in guard_comment.splitlines()):
            raise Refused("the template's guard comment no longer says GUARD_SENTENCES")
        text = replace_once(text, META_GUARD_OLD, META_GUARD_NEW, where)
        text = replace_once(text, META_UPLOAD_COMMENT_OLD, META_UPLOAD_COMMENT_NEW, where)
    text = replace_once(text, f"  PUBLISH_PACKAGE: {package}\n  PUBLISH_DIST_DIR: {dist}\n\n", f"  PUBLISH_PACKAGE: {package}\n  PUBLISH_DIST_DIR: {dist}\n  PUBLISH_TAG_PREFIX: {prefix}\n\n", where)
    # The TestPyPI job: id-token: write alone, the template's comment; no checkout, setup or install check left in it.
    permission = line_of(template, "      id-token: write  # trusted publishing to TestPyPI", "the template")
    if sub:
        text = replace_once(text, SUB_TESTPYPI_OLD, SUB_TESTPYPI_NEW.replace("{permission}", permission), where)
    else:
        text = replace_once(text, META_TESTPYPI_OLD.replace("{checkout}", checkout).replace("{setup_python}", setup_python), META_TESTPYPI_NEW.replace("{permission}", permission), where)
    old_step = install_step_old(text, workflow, where)
    check_install_lines(workflow, old_step)
    if sub and f"            {sparse}\n" not in old_step:
        raise Refused(f"{where}: the base's sparse checkout does not hold {sparse}")
    text = replace_once(text, old_step, "", where)
    # The install check's own job, before the PyPI job, which needs both.
    pypi_head = META_PYPI_BANNER if not sub else SUB_PYPI_HEAD
    new_head = pypi_head.replace(f"    needs: {test_id}\n", f"    needs: [{test_id}, {INSTALL_JOB}]\n")
    text = replace_once(text, pypi_head, install_job(workflow, template, protocol, setup_python) + new_head, where)
    # Every template block and the republish job: the template's, in place of this file's.
    want = block_texts(template, "the template")
    have = template_blocks(text, where)
    if roles([key for key, _, _ in have], test_id, prod_id) != list(want):
        raise Refused(f"{where}: its template blocks are {[key for key, _, _ in have]}, the template's {list(want)}")
    lines = text.splitlines(keepends=True)
    for (key, a, b), role in reversed(list(zip(have, want))):
        lines[a:b] = [want[role]]
    text = "".join(lines)
    text = text[: republish_start(text, where)] + template[republish_start(template, "the template") :]
    # Post-conditions: the blocks and the republish job cut from the result are the template's, byte for byte.
    if block_texts(text, where, test_id, prod_id) != want:
        raise Refused(f"{where}: a template block of the result differs from the template's")
    if text[republish_start(text, where) :] != template[republish_start(template, "the template") :]:
        raise Refused(f"{where}: the result's republish job differs from the template's")
    return text


def check_workflow(workflow: str, text: str) -> None:
    """The result's shape, read as YAML: the jobs and their wiring, and the install step equal to INSTALL_LINES."""
    if yaml is None:
        raise Refused("PyYAML is not importable here, so the result cannot be checked: run with an interpreter that has it")
    package, dist, test_id, prod_id, prefix, step_name, sparse = PUBLISHERS[workflow]
    wf = yaml.safe_load(text)
    jobs = wf["jobs"]
    install = jobs.get(INSTALL_JOB) or {}
    steps = install.get("steps") or []
    want_steps = ([None] if workflow == META else []) + [None, step_name]
    checkouts = [s for s in steps if str(s.get("uses") or "").startswith("actions/checkout@")]
    guard = f"(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))"
    checks = {
        "jobs": list(jobs) == ["build", test_id, INSTALL_JOB, prod_id, "republish"],
        "env": wf["env"] == {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist, "PUBLISH_TAG_PREFIX": prefix},
        "guard": jobs["build"]["if"] == guard,
        "install job name": install.get("name") == INSTALL_NAME,
        "install job needs": install.get("needs") == test_id,
        "install job permissions": install.get("permissions") == {"contents": "read"},
        "install job keys": set(install) == {"name", "needs", "runs-on", "permissions", "steps"},
        "install steps": [s.get("name") for s in steps] == want_steps,
        "install checkout": [s.get("with") for s in checkouts] == [{"sparse-checkout": f"{sparse}\n", "persist-credentials": False}],
        "install script": bool(steps) and steps[-1].get("run") == "\n".join(INSTALL_LINES[workflow]) + "\n",
        "install step keys": bool(steps) and set(steps[-1]) == {"name", "run"},
        "testpypi permissions": jobs[test_id].get("permissions") == {"id-token": "write"},
        "testpypi steps": [s.get("name") for s in jobs[test_id]["steps"]] == ["Download dist artifacts", "Verify the dist against SHA256SUMS", "Publish to TestPyPI", "Verify TestPyPI serves exactly these files"],
        "pypi needs": jobs[prod_id].get("needs") == [test_id, INSTALL_JOB],
        "pypi permissions": jobs[prod_id].get("permissions") == {"id-token": "write"},
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise Refused(f"{WORKFLOW_DIR}/{workflow}: the result fails {failed}")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# The tests: the one-artifact module written whole, the docs-bounds module new, two suites retargeted (R4-1)
# ─────────────────────────────────────────────────────────────────────────────────────────────
ONE_ARTIFACT_TEST = "tests/test_publish_one_artifact.py"
DOCS_BOUNDS_TEST = "tests/test_publish_docs_bounds.py"
TESTPYPI_VERIFY_TEST = "tests/test_publish_testpypi_verify.py"
SUBPACKAGE_TEST = "tests/test_publish_subpackage_workflows.py"
#: The base the one-artifact module was derived from (juniper-ml main bceac63c): a module main has moved is refused, never
#: overwritten, so a change merged meanwhile is re-derived rather than reverted.
BASE_ONE_ARTIFACT_SHA256 = "434b9cbc724e584c36cf51230c544e08c53a43fba7b6f093a01421cfe531daf5"
EMBED_TEST_PUBLISH_ONE_ARTIFACT = r'''#!/usr/bin/env python3
"""Pin the one-artifact publish: PyPI takes exactly the files TestPyPI took, and the run checks it by sha256.

The directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to
testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be
helpful here to prevent this from slipping through the cracks again." juniper-ml's seven publishers handed both
publish jobs one artifact, but nothing checked it, and a re-run broke it. juniper-ci-tools 0.9.1's run 38045867684:
attempt 1's ``Publish to PyPI``, approved on day 11, failed at its download because the 7-day artifact had expired;
attempt 2 ("Re-run all jobs") built again, its TestPyPI upload passed under ``skip-existing`` while TestPyPI kept the
first build, and PyPI took the second. PyPI serves the wheel as ``1dc8e01e...``, TestPyPI as ``ade363e8...``.

Every publisher carries juniper-cascor's one-artifact template (juniper-cascor#763 and #767, swept by #777), copied
verbatim. The build job records ``SHA256SUMS`` and uploads it with the dist directory as one artifact, kept 90 days,
and a re-run attempt reuses that artifact instead of building again. Each publish job checks the files against
``SHA256SUMS`` before it uploads them. TestPyPI's JSON must list exactly those sha256 after the TestPyPI upload and
again before the PyPI one, and PyPI's after it. No upload sets ``skip-existing``, and only the jobs that upload hold
``id-token: write``. The template's steps read only ``PUBLISH_PACKAGE``, ``PUBLISH_DIST_DIR`` and
``PUBLISH_TAG_PREFIX`` from the workflow ``env``, a step's ``INDEX_URL``, and the runner's own variables.

The sweep (juniper-cascor#777) adds the rulings of 2026-11-16. Ruling 2: the install check runs in a job of its own,
``Verify the TestPyPI install``, which holds ``contents: read`` alone, installs from the runner's temporary directory
and is needed by the PyPI job; the TestPyPI job keeps the template steps and the upload, and holds ``id-token: write``
alone. Ruling 1: a dispatch from the release tag with ``republish_from_testpypi`` runs the republish job, the first
rung of the recovery ladder (2026-11-15), which copies TestPyPI's files for the version to PyPI and builds nothing,
and refuses unless the tag's newest release run passed its TestPyPI jobs in their latest attempt.

The static cases pin, in all seven workflows: the wiring; each job's keys, runner and exact steps, with no ``if:`` but
the listed ones and no ``continue-on-error``; each build step's commands; the install job's exact commands, from
outside any checkout, which nothing can switch off; the workflow and job names the release train reads; what each
workflow kept (``TestUnchanged``); and every template block juniper-cascor's byte for byte, once each ``uses:`` line
is reduced to its action's name, with each action pinned to one ref. Every ``publish*.yml``, and every workflow that
uploads to an index, must be one of the seven, so an eighth publisher cannot go unchecked. The rehearsals run each
template step's own Python, extracted from ``publish.yml``, in a scratch workspace, against a stand-in index and a
stand-in GitHub API on 127.0.0.1, the republish job's refusal among them, and each install check's own shell under
``bash -e`` against stand-in ``pip``, ``python`` and ``sleep``. (The bounds the docs state are pinned in
``tests/test_publish_docs_bounds.py``: this module reads the workflows alone.) Negative controls:
``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`` (the first port's), and the mutation
table of the pull request that ported juniper-cascor#777 here.

Run: python3 -m unittest -v tests/test_publish_one_artifact.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-11-15
"""

from __future__ import annotations

import functools
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs the workflow's OWN extracted step scripts with a fixed argv
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, cast

import yaml

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github" / "workflows"
META = "publish.yml"
#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build``, an install-check
#: and a ``republish`` job.
PUBLISHERS = {
    META: ("juniper-ml", "dist", "testpypi", "pypi"),
    "publish-ci-tools.yml": ("juniper-ci-tools", "juniper-ci-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-config-tools.yml": ("juniper-config-tools", "juniper-config-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-doc-tools.yml": ("juniper-doc-tools", "juniper-doc-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-model-core.yml": ("juniper-model-core", "juniper-model-core/dist", "publish-testpypi", "publish-pypi"),
    "publish-observability.yml": ("juniper-observability", "juniper-observability/dist", "publish-testpypi", "publish-pypi"),
    "publish-service-core.yml": ("juniper-service-core", "juniper-service-core/dist", "publish-testpypi", "publish-pypi"),
}
SUB_PACKAGES = tuple(name for name in sorted(PUBLISHERS) if name != META)
#: workflow -> (top-level permissions, the PyPI job's). No PyPI job checks anything out, so none holds ``contents: read``.
PERMISSIONS = {
    META: ({}, {"id-token": "write"}),
    **{name: ({"contents": "read"}, {"id-token": "write"}) for name in SUB_PACKAGES},
}
#: workflow -> PUBLISH_TAG_PREFIX, what the package's release tags start with (the version is the rest): ``v`` for the
#: meta-package, ``<package>-v`` for a sub-package.
TAG_PREFIXES = {META: "v", **{name: f"{PUBLISHERS[name][0]}-v" for name in SUB_PACKAGES}}
#: workflow -> its ``name:``. The release-train monitor drops every run of a workflow whose name does not end in "to PyPI"
#: (``PYPI_PUBLISHER_NAME_SUFFIX`` in ``util/release_train/ceremony.py``), so a renamed publisher would fail quietly.
WORKFLOW_NAMES = {META: "Publish to PyPI", **{name: f"Publish {PUBLISHERS[name][0]} to PyPI" for name in SUB_PACKAGES}}
#: Ruling 2 of 2026-11-16: the install check runs in a job of its own, which holds no ``id-token``. Its name holds
#: "TestPyPI", so the release-train ceremony counts it with the TestPyPI job and reads its failure as HALT_TESTPYPI.
INSTALL = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
MODEL_CORE = "publish-model-core.yml"
#: workflow -> the install check's step name, kept from the TestPyPI job it moved out of.
INSTALL_STEPS = dict.fromkeys(SUB_PACKAGES, "Verify install from TestPyPI") | {META: "Verify TestPyPI install", MODEL_CORE: "Verify install from TestPyPI (no-deps, version-only import)"}
#: workflow -> the one file its install job checks out, sparsely: the file its version is read from.
SPARSE_PATHS = {name: f"{PUBLISHERS[name][0]}/pyproject.toml" for name in SUB_PACKAGES} | {META: "pyproject.toml", MODEL_CORE: "juniper-model-core/juniper_model_core/_version.py"}
#: The two install checks that read the package's metadata alone, which a wheel without the package also passes, so each
#: also finds the package (R4-5 of the sweep's review): workflow -> the import name.
FIND_SPEC = {"publish-ci-tools.yml": "juniper_ci_tools", "publish-observability.yml": "juniper_observability"}
REPUBLISH = "republish"
REPUBLISH_NAME = "Republish the tested files (dispatch only)"
REPUBLISH_IF = "github.event_name == 'workflow_dispatch' && inputs.republish_from_testpypi"
REUSE = "Reuse an earlier attempt's artifact"
REUSE_IF = "steps.reuse.outputs.reuse != 'true'"
RECORD = "Record SHA256SUMS"
UPLOAD = "Upload dist artifacts"
DOWNLOAD = "Download dist artifacts"
VERIFY_DIST = "Verify the dist against SHA256SUMS"
TESTPYPI_AFTER = "Verify TestPyPI serves exactly these files"
TESTPYPI_BEFORE = "Verify TestPyPI still serves exactly these files"
PYPI_AFTER = "Verify PyPI serves exactly these files"
FIND = "Find the release run's artifact"
FETCH_ORIGINAL = "Download the release run's artifact"
FETCH = "Download TestPyPI's files and verify them"
ASSERT_TAG = "Assert release tag matches built version"
INDEX_CHECKS = {TESTPYPI_AFTER: "https://test.pypi.org", TESTPYPI_BEFORE: "https://test.pypi.org", PYPI_AFTER: "https://pypi.org"}
#: The template is juniper-cascor's: the sha256 of each template block (from its "One-artifact publish template" comment
#: to the end of its step, comments included) and of the republish job (from its banner to the end of the job) in
#: juniper-cascor's .github/workflows/publish.yml at main 5e3d9801, byte-identical to juniper-cascor#777's merge
#: f5ed3017. Each is taken with every ``uses:`` line reduced to the action's name, its ``@ref`` and trailing
#: ``# vX.Y.Z`` dropped, so a Dependabot bump of an action moves no digest here; TestTemplate pins each action to one ref
#: across the seven files, and juniper-ml's cross-repository checker pins every ref to the template's. The keys name
#: each block by its job's role, so a sub-package's ``publish-testpypi/...`` block is the template's ``testpypi/...``.
#: Change the template there first, then copy it here.
CASCOR_TEMPLATE_SHA256 = {
    "build/Reuse an earlier attempt's artifact": "314735b37d6e5184540b5a0a9c4e2070426c7458613e7cd147baa8eb340679f9",
    "build/Record SHA256SUMS": "951a5b5af500f705a5fa42cd7c62370d7336c93f94a6c15d39caebf0db8bc25a",
    "build/Upload dist artifacts": "f329f5c9598b01d7dc289d99f0c633d84a199ab80d394af089636d2fae8fa43d",
    "testpypi/Download dist artifacts": "0fba9dba65661e36ace092465b68567a22bfce24d668d00bd7fe02ffe9b3b651",
    "testpypi/Verify the dist against SHA256SUMS": "2cc6ed8720f9ce64905e37c3dc6ff939f3c33c183058f61f76bb8404628ff1e8",
    "testpypi/Verify TestPyPI serves exactly these files": "fdbaf48a208841c8ebf58b404cc6ed9293cbb23be04be13e176d5f3942091b88",
    "pypi/Download dist artifacts": "0fba9dba65661e36ace092465b68567a22bfce24d668d00bd7fe02ffe9b3b651",
    "pypi/Verify the dist against SHA256SUMS": "2cc6ed8720f9ce64905e37c3dc6ff939f3c33c183058f61f76bb8404628ff1e8",
    "pypi/Verify TestPyPI still serves exactly these files": "65d6cdfa8e2493cb78c983ca639d9dda33a1236ae980ece534e9556abb346213",
    "pypi/Verify PyPI serves exactly these files": "19a278f81b1fa626c0841908fd4c2ebd4a55264897e121bd96387aafb7bb26ac",
    "republish/Find the release run's artifact": "63436e38b52bb60d6a6bccc94327e87b7d69c52d5be09370a7557c46dc5dc681",
    "republish/Download TestPyPI's files and verify them": "9470f00aeeb58ad73e9fed6404da042d75143553e30c0e4ef59a350e110d803f",
    "republish/Verify the dist against SHA256SUMS": "2cc6ed8720f9ce64905e37c3dc6ff939f3c33c183058f61f76bb8404628ff1e8",
    "republish/Verify PyPI serves exactly these files": "19a278f81b1fa626c0841908fd4c2ebd4a55264897e121bd96387aafb7bb26ac",
}
CASCOR_REPUBLISH_SHA256 = "a9f020fd629890c8cc96b59eac208c90ca3480466f547136e2e56edb7a789ffd"
TEMPLATE_COMMENT = "      # One-artifact publish template"
#: A step-level line: a new step, or a comment between steps. Run-script lines are indented deeper.
STEP_LINE = re.compile(r"^      (?:- |# )")
JOB_LINE = re.compile(r"^  [a-z][a-z0-9-]*:\s*$")
#: A ``uses:`` line: its prefix, the action's name, and the ``@ref`` with the ``# vX.Y.Z`` comment Dependabot moves with it.
USES_LINE = re.compile(r"^(\s*(?:- )?uses: )([^@\s]+)@\S+(?:\s+#\s*v\S*)?$")
#: Everything a template step may read from its environment: the three parameters, a step's own inputs, the runner's variables.
TEMPLATE_ENV = {
    "PUBLISH_PACKAGE",
    "PUBLISH_DIST_DIR",
    "PUBLISH_TAG_PREFIX",
    "INDEX_URL",
    "HASH_CHECK_ATTEMPTS",
    "HASH_CHECK_INTERVAL",
    "VERSION",
    "RELEASE_RUN_SUMS",
    "GH_TOKEN",
    "GITHUB_WORKSPACE",
    "GITHUB_API_URL",
    "GITHUB_REPOSITORY",
    "GITHUB_RUN_ID",
    "GITHUB_RUN_ATTEMPT",
    "GITHUB_OUTPUT",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_REF_TYPE",
    "GITHUB_WORKFLOW_REF",
}
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
BUILD_COMMAND = re.compile(r"\bpython3?\s+-m\s+build\b|\bpip3?\s+wheel\b|\buv\s+build\b|\bsetup\.py\s+(?:sdist|bdist_wheel)\b")
#: GitHub lets a deployment wait this many days for its reviewer: the PyPI job may start that late, and needs the artifact.
GATE_APPROVAL_DAYS = 30
#: The artifact's retention, as the docs state it: past the gate's 30 days and the 30-day re-run window.
ARTIFACT_RETENTION_DAYS = 90
#: Every publish workflow is found by these globs (tests/test_publish_release_only_trigger.py uses the first), and every
#: workflow that uploads to an index by this pattern: each must be one of PUBLISHERS, or no case here would read it.
PUBLISH_GLOBS = ("publish*.yml", "publish*.yaml")
UPLOAD_STEP = re.compile(r"^\s*(?:-\s+)?uses:\s*pypa/gh-action-pypi-publish@", re.M)
#: The one conditional step of the republish job: it downloads the release run's artifact only when the find step found one.
FETCH_ORIGINAL_IF = "steps.original.outputs.run-id != ''"
ARTIFACT = "${{ env.PUBLISH_PACKAGE }}-dist"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
#: The build job's guard: a release of this package's tag, or a dispatch from it that does not ask for the republish
#: job. A job-level ``if:`` cannot read ``env``, so it repeats PUBLISH_TAG_PREFIX.
GUARD = "(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))"
WHEEL = "juniper_ml-9.9.9-py3-none-any.whl"
SDIST = "juniper_ml-9.9.9.tar.gz"
BUILT = {WHEEL: b"wheel bytes", SDIST: b"sdist bytes"}
JSON_PATH = "/pypi/juniper-ml/9.9.9/json"
REPOSITORY = "pcalnon/juniper-ml"
#: The variable the reuse and find steps read the runner's API credential from, the expression that fills it, and the
#: stand-in value the rehearsals pass. Bandit's B105 reads a string under a name like the first as a hardcoded password.
API_CREDENTIAL_ENV = "GH_TOKEN"
RUNNER_CREDENTIAL = "${{ github.token }}"
FAKE_API_CREDENTIAL = "stand-in-credential"
#: The actions the publishers use, by name: a step is compared with its ``@ref`` dropped, so a Dependabot bump of a pin
#: changes nothing here.
CHECKOUT = "actions/checkout"
SETUP_PYTHON = "actions/setup-python"
UPLOAD_ACTION = "actions/upload-artifact"
DOWNLOAD_ACTION = "actions/download-artifact"
PYPI_PUBLISH = "pypa/gh-action-pypi-publish"
#: Each job's steps, in order, as (name, action). Nothing may be added, dropped or moved unnoticed: neither a rebuild
#: slipped into a publish job nor a step that writes into the dist directory before ``Record SHA256SUMS``.
TESTPYPI_STEPS = [(DOWNLOAD, DOWNLOAD_ACTION), (VERIFY_DIST, None), ("Publish to TestPyPI", PYPI_PUBLISH), (TESTPYPI_AFTER, None)]
PYPI_STEPS = [(DOWNLOAD, DOWNLOAD_ACTION), (VERIFY_DIST, None), (TESTPYPI_BEFORE, None), ("Publish to PyPI", PYPI_PUBLISH), (PYPI_AFTER, None)]
REPUBLISH_STEPS = [(FIND, None), (FETCH_ORIGINAL, DOWNLOAD_ACTION), (FETCH, None), (VERIFY_DIST, None), ("Publish to PyPI", PYPI_PUBLISH), (PYPI_AFTER, None)]
SUB_PACKAGE_BUILD_STEPS = [(REUSE, None), (None, CHECKOUT), (None, SETUP_PYTHON), ("Install build tools", None), ("Build sdist + wheel", None), ("Validate distribution metadata", None), (ASSERT_TAG, None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)]
BUILD_STEPS = {
    META: [(REUSE, None), (None, CHECKOUT), (None, SETUP_PYTHON), ("Install build tools", None), ("Build package", None), ("Check package", None), (ASSERT_TAG, None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)],
    **dict.fromkeys(SUB_PACKAGES, SUB_PACKAGE_BUILD_STEPS),
}
#: The install-check job: the sparse checkout each publisher reads its version from (after setup-python 3.12 in the
#: meta-package's, as its TestPyPI job had it), then the check.
INSTALL_JOB_STEPS = {META: [(None, SETUP_PYTHON), (None, CHECKOUT), (INSTALL_STEPS[META], None)], **{name: [(None, CHECKOUT), (INSTALL_STEPS[name], None)] for name in SUB_PACKAGES}}
#: workflow -> the exact inputs of its TestPyPI and its PyPI upload: no ``skip-existing`` (nor the action's older spelling
#: ``skip_existing``), no ``attestations: false``, and the downloaded dist directory as the only source.
TESTPYPI_INPUTS = {"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT}
UPLOAD_INPUTS = {
    META: ({**TESTPYPI_INPUTS, "attestations": True}, {"packages-dir": DIST_INPUT, "attestations": True}),
    **dict.fromkeys(SUB_PACKAGES, ({**TESTPYPI_INPUTS, "verbose": True}, {"packages-dir": DIST_INPUT, "verbose": True})),
}
#: Every key the workflow and each of its jobs carries. An ``env`` on a job (``PIP_EXTRA_INDEX_URL``,
#: ``HASH_CHECK_ATTEMPTS``), a container, a matrix or another runner would change what a check runs, or against what.
WORKFLOW_KEYS = {"name", "on", "permissions", "env", "jobs"}
BUILD_JOB_KEYS = {"name", "if", "runs-on", "permissions", "steps"}
PUBLISH_JOB_KEYS = {"name", "needs", "runs-on", "environment", "permissions", "steps"}
INSTALL_JOB_KEYS = {"name", "needs", "runs-on", "permissions", "steps"}
REPUBLISH_JOB_KEYS = {"name", "if", "runs-on", "environment", "permissions", "steps"}
#: The keys a publisher may add, none of which changes what a check runs: the workflow's ``run-name`` and a
#: ``concurrency`` group that never cancels a run in progress (the sub-packages carry one), and a job's
#: ``timeout-minutes``. No job takes a ``concurrency`` group: by default (``queue: single``) GitHub keeps one pending job
#: per group and cancels the older one when another queues, so a group on the PyPI job could stop a run between its two
#: uploads.
OPTIONAL_WORKFLOW_KEYS = {"run-name", "concurrency"}
OPTIONAL_JOB_KEYS = {"timeout-minutes"}
#: workflow -> each build step's commands: the build, the check of what it built, and the tag assertion.
SUB_PACKAGE_BUILD_RUNS = {"Install build tools": "pip install --upgrade build twine", "Build sdist + wheel": "python -m build --sdist --wheel", "Validate distribution metadata": "twine check dist/*"}
BUILD_RUNS = {
    META: {"Install build tools": "pip install build twine", "Build package": "python -m build", "Check package": "twine check dist/*", ASSERT_TAG: 'util/assert_release_tag.bash --ref "${{ github.ref }}" --dist-dir dist --expect-prefix v'},
    **{name: SUB_PACKAGE_BUILD_RUNS | {ASSERT_TAG: f'../util/assert_release_tag.bash --ref "${{{{ github.ref }}}}" --dist-dir dist --expect-prefix {TAG_PREFIXES[name]}'} for name in SUB_PACKAGES},
}
#: The install checks' bounded retry. The sub-packages': five tries, 10 s apart, none after the last. The meta-package's
#: provenance fetch: ten tries, each failure followed by a 6 s wait. After the last failed try, the template's lag error.
INSTALL_TRIES = {META: 10, **dict.fromkeys(SUB_PACKAGES, 5)}
INSTALL_WAITS = {META: [6] * 10, **dict.fromkeys(SUB_PACKAGES, [10] * 4)}
LAG_ERROR = "is not installable from TestPyPI after {tries} tries (index lag?): Re-run failed jobs; a real failure repeats"
CD = 'cd "${RUNNER_TEMP}"'


def _retried_install(package: str) -> list[str]:
    """The install every sub-package check runs: five tries, 10 s apart, and after the fifth failure an error that names
    index lag, rather than a check that fails as if the package were broken."""
    return [
        "for attempt in 1 2 3 4 5; do",
        "if pip install \\",
        "--no-deps \\",
        "--index-url https://test.pypi.org/simple/ \\",
        f'"{package}==${{version}}"; then',
        "break",
        "fi",
        'if [ "${attempt}" -eq 5 ]; then',
        f'echo "::error::{package} ${{version}} {LAG_ERROR.format(tries=5)}"',
        "exit 1",
        "fi",
        'echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
        "sleep 10",
        "done",
    ]


def _version_from_pyproject(package: str) -> str:
    return f"""version=$(grep '^version' "${{GITHUB_WORKSPACE}}/{package}/pyproject.toml" | head -1 | sed -E 's/version = "(.+)"/\\1/')"""


def _package_check(package: str, module: str) -> str:
    """R4-5: the metadata check also finds the package, which runs none of its code; it prints juniper-cascor's neutral
    line, with no "OK" before the verdict, and fails through SystemExit, which PYTHONOPTIMIZE keeps."""
    return f"""python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{module}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{package}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {module} package')\""""


def _sub_install(package: str, checks: list[str], version: str | None = None) -> list[str]:
    return ["set -euo pipefail", CD, version or _version_from_pyproject(package), *_retried_install(package), *checks]


#: workflow -> its install step's commands, exactly, comment and blank lines dropped: no ``exit 0``, ``trap``, earlier
#: install or second version can be added and none dropped, while a comment may change freely (juniper-ml's
#: cross-repository checker pins the whole script, comments included).
INSTALL_COMMANDS = {
    META: [
        CD,
        """VERSION=$(python -c "import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])")""",
        'DOWNLOAD_DIR="$(mktemp -d)"',
        "FETCHED=0",
        "for attempt in 1 2 3 4 5 6 7 8 9 10; do",
        'pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}" && { FETCHED=1; break; }',
        'echo "TestPyPI has not served juniper-ml==${VERSION} yet (attempt ${attempt}/10) -- retrying in 6s"',
        "sleep 6",
        "done",
        'if [ "${FETCHED}" -ne 1 ]; then',
        f'echo "::error::juniper-ml ${{VERSION}} {LAG_ERROR.format(tries=10)}"',
        "exit 1",
        "fi",
        'WHEEL="${DOWNLOAD_DIR}/juniper_ml-${VERSION}-py3-none-any.whl"',
        'if [ ! -f "${WHEEL}" ]; then',
        'echo "::error::TestPyPI did not serve the expected wheel: ${WHEEL}"',
        'ls -la "${DOWNLOAD_DIR}"',
        "exit 1",
        "fi",
        'echo "Phase 1 OK: fetched ${WHEEL} from TestPyPI"',
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}"',
        """python -c "import importlib.metadata; print(f'TestPyPI bare OK: juniper-ml v{importlib.metadata.version(\\"juniper-ml\\")}')\"""",
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}[clients]"',
        """python -c "import juniper_data_client, juniper_cascor_client; print(f'TestPyPI extras OK: [clients] resolved data-client={juniper_data_client.__version__ if hasattr(juniper_data_client, \\"__version__\\") else \\"?\\"}, cascor-client={juniper_cascor_client.__version__ if hasattr(juniper_cascor_client, \\"__version__\\") else \\"?\\"}')\"""",
        'pip install --index-url https://pypi.org/simple/ "${WHEEL}[tools]"',
        """python -c "import juniper_ci_tools, juniper_doc_tools, juniper_observability; print(f'TestPyPI extras OK: [tools] resolved ci-tools={juniper_ci_tools.__version__ if hasattr(juniper_ci_tools, \\"__version__\\") else \\"?\\"}, doc-tools={juniper_doc_tools.__version__ if hasattr(juniper_doc_tools, \\"__version__\\") else \\"?\\"}, observability={juniper_observability.__version__ if hasattr(juniper_observability, \\"__version__\\") else \\"?\\"}')\"""",
    ],
    "publish-ci-tools.yml": _sub_install("juniper-ci-tools", [_package_check("juniper-ci-tools", "juniper_ci_tools")]),
    "publish-config-tools.yml": _sub_install("juniper-config-tools", ["python -m juniper_config_tools --version", """python -c "import juniper_config_tools; print('TestPyPI install OK', juniper_config_tools.__version__)\""""]),
    "publish-doc-tools.yml": _sub_install("juniper-doc-tools", ["juniper-check-doc-links --version", "python -m juniper_doc_tools --version", """python -c "import juniper_doc_tools; print('TestPyPI install OK', juniper_doc_tools.__version__)\""""]),
    MODEL_CORE: _sub_install(
        "juniper-model-core",
        ["""python -c "import juniper_model_core; print('TestPyPI install OK', juniper_model_core.__version__)\""""],
        version="""version=$(grep -E '^__version__' "${GITHUB_WORKSPACE}/juniper-model-core/juniper_model_core/_version.py" | sed -E 's/.*"(.+)".*/\\1/')""",
    ),
    "publish-observability.yml": _sub_install("juniper-observability", [_package_check("juniper-observability", "juniper_observability")]),
    "publish-service-core.yml": _sub_install("juniper-service-core", ["""python -c "import juniper_service_core; print('OK', juniper_service_core.__version__)\""""]),
}


@functools.lru_cache(maxsize=None)
def _text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


@functools.lru_cache(maxsize=None)
def _workflow(name: str) -> dict:
    """The parsed workflow, read once per process. Every case only reads it."""
    data = yaml.safe_load(_text(name))
    # PyYAML (YAML 1.1) reads the bare `on:` key as boolean True.
    data["on"] = data.pop(True, data.get("on"))
    return data


def _names(job: dict) -> list[str]:
    return [str(s.get("name") or s.get("uses") or "") for s in job.get("steps") or []]


def _step_list(job: dict) -> list[tuple[str | None, str | None]]:
    """Each step as (its name, the action it uses with the ``@ref`` dropped), so a bump of a pinned action moves nothing."""
    return [(s.get("name"), str(s["uses"]).split("@", 1)[0] if s.get("uses") else None) for s in job.get("steps") or []]


def _expected_steps(workflow: str) -> dict[str, list[tuple[str | None, str | None]]]:
    """Each job's steps, in order. A step added between a check and the upload it vouches for (one that rewrites the
    dist after its sha256 check, say) leaves every order pin true; so does a dropped step that no case names."""
    _, _, test_id, prod_id = PUBLISHERS[workflow]
    return {"build": BUILD_STEPS[workflow], test_id: TESTPYPI_STEPS, INSTALL: INSTALL_JOB_STEPS[workflow], prod_id: PYPI_STEPS, REPUBLISH: REPUBLISH_STEPS}


def _index(job: dict, name: str) -> int:
    names = _names(job)
    if names.count(name) != 1:
        raise AssertionError(f"expected exactly one step named {name!r}, found {names.count(name)} in {names}")
    return names.index(name)


def _step(job: dict, name: str) -> dict:
    return job["steps"][_index(job, name)]


def _uploads(job: dict) -> list[int]:
    return [i for i, s in enumerate(job.get("steps") or []) if str(s.get("uses") or "").startswith(PUBLISH_ACTION)]


def _uses(job: dict, prefix: str) -> list[int]:
    return [i for i, s in enumerate(job.get("steps") or []) if str(s.get("uses") or "").startswith(prefix)]


def _environment(job: dict) -> str:
    env = job.get("environment")
    return str(env.get("name") if isinstance(env, dict) else env)


def _commands(run: str) -> list[str]:
    """A shell step's commands: each line stripped, comment and blank lines dropped."""
    return [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]


def _install_step(workflow: str) -> dict:
    return _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])


def _by_action(value):
    """VALUE with every ``uses:`` reduced to the action's name, the ``@ref`` dropped."""
    if isinstance(value, dict):
        return {k: (str(v).split("@", 1)[0] if k == "uses" else _by_action(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_by_action(v) for v in value]
    return value


def _template_scripts() -> dict[str, str]:
    """The template steps' Python, as ``publish.yml`` runs it; every copy elsewhere must equal these."""
    jobs = _workflow(META)["jobs"]
    return {
        REUSE: _step(jobs["build"], REUSE)["run"],
        RECORD: _step(jobs["build"], RECORD)["run"],
        VERIFY_DIST: _step(jobs["testpypi"], VERIFY_DIST)["run"],
        "index": _step(jobs["testpypi"], TESTPYPI_AFTER)["run"],
        FIND: _step(jobs[REPUBLISH], FIND)["run"],
        FETCH: _step(jobs[REPUBLISH], FETCH)["run"],
    }


def _template_blocks(text: str, test_id: str = "testpypi", prod_id: str = "pypi") -> dict[str, str]:
    """Each template block of a workflow, keyed ``<job role>/<step name>``: raw text, from its "One-artifact publish
    template" comment to the end of its step's last non-blank line, comments included. Run-script lines are indented
    deeper than any step-level line, so they never end a block early."""
    lines = text.splitlines(keepends=True)
    roles = {test_id: "testpypi", prod_id: "pypi"}
    blocks: dict[str, str] = {}
    job = ""
    i = 0
    while i < len(lines):
        if JOB_LINE.match(lines[i]):
            job = lines[i].strip().rstrip(":")
        if lines[i].startswith(TEMPLATE_COMMENT):
            first = next(j for j in range(i, len(lines)) if lines[j].startswith("      - "))
            name = re.sub(r"^      - name:\s*", "", lines[first]).strip()
            end = first + 1
            while end < len(lines) and not STEP_LINE.match(lines[end]) and not (lines[end].strip() and len(lines[end]) - len(lines[end].lstrip(" ")) <= 2):
                end += 1
            while end > first + 1 and not lines[end - 1].strip():
                end -= 1
            key = f"{roles.get(job, job)}/{name}"
            if key in blocks:
                raise AssertionError(f"two template blocks for {key}")
            blocks[key] = "".join(lines[i:end])
            i = end
            continue
        i += 1
    return blocks


def _republish_job(text: str) -> str:
    """The republish job, raw: from the comment banner above it to the end of the file, where it must be."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == f"  {REPUBLISH}:\n"]
    if len(at) != 1:
        raise AssertionError(f"expected one {REPUBLISH} job, found {len(at)}")
    if [line for line in lines[at[0] + 1 :] if JOB_LINE.match(line)]:
        raise AssertionError("the republish job must be the file's last job")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    return "".join(lines[start:])


def _normalized(block: str) -> str:
    """BLOCK with every ``uses:`` line reduced to the action's name: its ``@ref`` and the trailing ``# vX.Y.Z`` dropped,
    every other line kept byte for byte."""
    return "".join(USES_LINE.sub(r"\1\2", line) + "\n" for line in block.splitlines())


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script(kind: str, tmp_path: Path) -> Path:
    path = tmp_path / f"{re.sub(r'[^a-z]+', '_', kind.lower())}.py"
    path.write_text(_template_scripts()[kind], encoding="utf-8")
    return path


def _run(script: Path, workspace: Path, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run an extracted step as the runner does (``python3 {0}``), with a minimal environment rather than a copy of ours."""
    child = {"PATH": os.environ.get("PATH", ""), "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": "juniper-ml", "PUBLISH_DIST_DIR": "dist", "PUBLISH_TAG_PREFIX": "v"}
    child.update(env or {})
    return subprocess.run([sys.executable, "-I", str(script)], cwd=cwd or workspace, env=child, capture_output=True, text=True, timeout=120, check=False)  # nosec B603 - fixed argv: this interpreter and an extracted step


def _release(files: dict[str, str], base: str = "https://test-files.example") -> dict:
    return {"info": {"name": "juniper-ml", "version": "9.9.9"}, "urls": [{"filename": name, "url": f"{base}/files/{name}", "digests": {"sha256": digest, "md5": "0" * 32}} for name, digest in files.items()]}


NOT_FOUND: tuple[int, object] = (404, {"message": "Not Found"})
SERVED = {name: _sha(data) for name, data in BUILT.items()}


class _Stand(http.server.ThreadingHTTPServer):
    """A stand-in for an index's JSON API and file host, or for the GitHub API: each GET of a path gets that path's next
    scripted answer (the last one repeats), and an unscripted path gets a 404. Every request's path and headers are kept."""

    def __init__(self, routes: dict[str, list[tuple[int, object]]]) -> None:
        super().__init__(("127.0.0.1", 0), _StandHandler)
        self.routes = {path: list(answers) for path, answers in routes.items()}
        self.requests: list[tuple[str, dict[str, str]]] = []

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"

    def paths(self, path: str | None = None) -> list[str]:
        return [p for p, _ in self.requests if path is None or p == path]


class _StandHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        stand = cast(_Stand, self.server)
        stand.requests.append((self.path, dict(self.headers.items())))
        answers = stand.routes.get(self.path) or [NOT_FOUND]
        status, body = answers.pop(0) if len(answers) > 1 else answers[0]
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet: the cases read the requests the step made, not the server's log."""
        return


class _Scratch(unittest.TestCase):
    """Per case: a scratch directory (``tmp_path``), workspaces holding the built files, and stand-in servers."""

    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.tmp_path = Path(scratch.name)

    def workspace(self, name: str = "workspace") -> Path:
        root = self.tmp_path / name
        (root / "dist").mkdir(parents=True)
        for file_name, data in BUILT.items():
            (root / "dist" / file_name).write_bytes(data)
        return root

    def stand(self, routes: dict[str, list[tuple[int, object]]]) -> _Stand:
        server = _Stand(routes)
        # A short poll interval: shutdown() waits for the serving loop's next poll, once per server.
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Wiring: one build, one artifact, a check before every upload, and the names the release train reads
# ─────────────────────────────────────────────────────────────────────────────────────────────
class TestWiring(unittest.TestCase):
    def test_every_publish_workflow_is_one_of_the_seven(self) -> None:
        # Every case here reads the workflows PUBLISHERS names, so an eighth publisher would be checked by none of them:
        # add it to PUBLISHERS (and give it the template), or rename it if it is not a publisher.
        found = sorted({path.name for pattern in PUBLISH_GLOBS for path in WORKFLOWS.glob(pattern)})
        self.assertEqual(found, sorted(PUBLISHERS), "a publish*.yml that no case here reads")
        uploading = sorted(path.name for path in WORKFLOWS.iterdir() if path.is_file() and path.suffix in (".yml", ".yaml") and UPLOAD_STEP.search(path.read_text(encoding="utf-8")))
        self.assertEqual(uploading, sorted(PUBLISHERS), "a workflow that uploads to an index and that no case here reads")

    def test_the_template_parameters_name_this_package(self) -> None:
        for workflow, (package, dist_dir, _, _) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                wf = _workflow(workflow)
                self.assertEqual(wf["env"], {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist_dir, "PUBLISH_TAG_PREFIX": TAG_PREFIXES[workflow]})
                # The meta-package's tags are v<version>; a sub-package's are <package>-v<version>.
                self.assertEqual(TAG_PREFIXES[workflow], "v" if workflow == META else f"{package}-v")
                # A job-level if: cannot read env, so the build job's tag guard repeats the prefix: the two must agree.
                self.assertEqual(wf["jobs"]["build"]["if"], GUARD.format(prefix=TAG_PREFIXES[workflow]))

    def test_the_workflow_name_ends_in_to_pypi_as_the_release_train_monitor_requires(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                name = _workflow(workflow)["name"]
                self.assertEqual(name, WORKFLOW_NAMES[workflow])
                self.assertTrue(name.lower().endswith("to pypi"), name)

    def test_only_the_build_job_builds_and_it_holds_no_environment(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                builders = sorted(job_id for job_id, job in jobs.items() if any(BUILD_COMMAND.search(str(s.get("run") or "")) for s in job.get("steps") or []))
                self.assertEqual(builders, ["build"])
                self.assertEqual(jobs["build"]["name"], "Build and Validate")
                self.assertNotIn("environment", jobs["build"])
                self.assertEqual(_uploads(jobs["build"]), [])

    def test_the_publish_jobs_chain_on_the_build_under_the_names_the_release_train_reads(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                self.assertEqual(sorted(jobs), sorted(["build", test_id, INSTALL, prod_id, REPUBLISH]))
                self.assertEqual(jobs[test_id]["needs"], "build")
                self.assertEqual(jobs[INSTALL]["needs"], test_id)
                # PyPI waits for both TestPyPI jobs: the upload with its checks, and the install check.
                self.assertEqual(jobs[prod_id]["needs"], [test_id, INSTALL])
                # util/release_train/ceremony.py tells the jobs apart by name: "testpypi" (both TestPyPI jobs) and "pypi".
                self.assertEqual(jobs[test_id]["name"], "Publish to TestPyPI")
                self.assertEqual(jobs[INSTALL]["name"], INSTALL_NAME)
                self.assertEqual(jobs[prod_id]["name"], "Publish to PyPI")
                self.assertEqual(_environment(jobs[test_id]), "testpypi")
                self.assertEqual(_environment(jobs[prod_id]), "pypi")

    def test_each_job_runs_exactly_its_steps(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                self.assertEqual({job_id: _step_list(job) for job_id, job in jobs.items()}, _expected_steps(workflow))

    def test_nothing_runs_on_a_condition_beyond_the_templates_and_nothing_continues_on_error(self) -> None:
        # A check that can be skipped (`if:`), or can fail without failing its job (`continue-on-error`), vouches for
        # nothing; an upload or a publish job on another condition (`always()` on the PyPI job would publish after a
        # failed install check) can run without the checks before it.
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                for job_id, job in jobs.items():
                    self.assertNotIn("continue-on-error", job, f"job {job_id}")
                    for step in job.get("steps") or []:
                        self.assertNotIn("continue-on-error", step, f"{job_id}: {step.get('name') or step.get('uses')}")
                # The build's tag guard is pinned above and the republish job's below; no other job carries an if:.
                self.assertEqual(sorted(job_id for job_id, job in jobs.items() if "if" in job), sorted(["build", REPUBLISH]))
                self.assertEqual(jobs[REPUBLISH]["if"], REPUBLISH_IF)
                steps = _expected_steps(workflow)
                expected: dict[str, list[str | None]] = {job_id: [None] * len(names) for job_id, names in steps.items()}
                expected["build"] = ["github.run_attempt != '1'"] + [REUSE_IF] * (len(steps["build"]) - 1)
                expected[REPUBLISH] = [None, FETCH_ORIGINAL_IF, None, None, None, None]
                self.assertEqual({job_id: [step.get("if") for step in job.get("steps") or []] for job_id, job in jobs.items()}, expected)

    def test_only_the_jobs_that_upload_hold_id_token_write(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                wf = _workflow(workflow)
                jobs = wf["jobs"]
                top, prod = PERMISSIONS[workflow]
                self.assertEqual(wf["permissions"], top)
                uploading = sorted(job_id for job_id, job in jobs.items() if _uploads(job))
                minting = sorted(job_id for job_id, job in jobs.items() if (job.get("permissions") or {}).get("id-token") == "write")
                self.assertEqual(uploading, sorted([test_id, prod_id, REPUBLISH]))
                self.assertEqual(minting, uploading)
                self.assertEqual(jobs["build"]["permissions"], {"contents": "read", "actions": "read"})
                # The job that can mint runs the template steps and the upload alone: it checks out nothing, installs nothing.
                self.assertEqual(jobs[test_id]["permissions"], {"id-token": "write"})
                # The install check installs the package TestPyPI serves: it may read the repository, and nothing more.
                self.assertEqual(jobs[INSTALL]["permissions"], {"contents": "read"})
                self.assertEqual(jobs[prod_id]["permissions"], prod)
                self.assertEqual(jobs[REPUBLISH]["permissions"], {"actions": "read", "id-token": "write"})
                # A job that holds no contents: read must not check anything out.
                for job_id in (test_id, prod_id, REPUBLISH):
                    self.assertEqual(_uses(jobs[job_id], "actions/checkout@"), [], job_id)

    def test_a_re_run_reuses_the_first_attempts_artifact_instead_of_building(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                build = _workflow(workflow)["jobs"]["build"]
                reuse = build["steps"][0]
                self.assertEqual(reuse.get("name"), REUSE)
                self.assertEqual(reuse.get("id"), "reuse")
                self.assertEqual(reuse.get("if"), "github.run_attempt != '1'")
                # It runs before the checkout, so a job default directory (the sub-package publishers set one) does not exist yet.
                self.assertEqual(reuse.get("working-directory"), "${{ github.workspace }}")
                self.assertEqual(reuse.get("shell"), "python3 {0}")
                self.assertEqual(reuse.get("env"), {API_CREDENTIAL_ENV: RUNNER_CREDENTIAL})
                # Every later step is skipped once the reuse step finds the artifact. juniper-ml's publishers carry no
                # step gated on a push event (tests/test_publish_release_only_trigger.py), so none is exempt, by its
                # name or by its if: text: an exemption by if: text would let any build step trade the reuse condition
                # for the push condition.
                for step in build["steps"][1:]:
                    self.assertEqual(step.get("if"), REUSE_IF, f"{step.get('name') or step.get('uses')} would run on a re-run that reuses the artifact")
                for name in (RECORD, UPLOAD):
                    self.assertEqual(_step(build, name).get("if"), REUSE_IF)

    def test_the_testpypi_job_checks_the_dist_uploads_then_checks_testpypi_before_the_install_check(self) -> None:
        for workflow, (_, _, test_id, _) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                job = jobs[test_id]
                uploads = _uploads(job)
                self.assertEqual(len(uploads), 1)
                self.assertEqual(job["steps"][uploads[0]]["with"]["repository-url"], "https://test.pypi.org/legacy/")
                self.assertLess(_index(job, DOWNLOAD), _index(job, VERIFY_DIST))
                self.assertLess(_index(job, VERIFY_DIST), uploads[0])
                self.assertLess(uploads[0], _index(job, TESTPYPI_AFTER))
                # The job ends at the sha256 check that vouches for what the install check installs, in the job that needs it.
                self.assertEqual(_index(job, TESTPYPI_AFTER), len(job["steps"]) - 1)
                self.assertEqual([s for s in job["steps"] if "pip " in str(s.get("run") or "")], [], "the job that can mint runs an install check")
                self.assertTrue([s for s in jobs[INSTALL]["steps"] if "pip " in str(s.get("run") or "")], "the TestPyPI install check is gone")
                self.assertEqual(jobs[INSTALL]["needs"], test_id, "the install check must come after the sha256 check that vouches for what it installs")
                # A checkout empties the workspace, so one in this job would lose the downloaded files.
                self.assertEqual(_uses(job, "actions/checkout@"), [], "a checkout runs in the TestPyPI job")

    def test_the_pypi_job_rechecks_testpypi_before_its_upload_and_pypi_after(self) -> None:
        for workflow, (_, _, _, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                job = _workflow(workflow)["jobs"][prod_id]
                uploads = _uploads(job)
                self.assertEqual(len(uploads), 1)
                self.assertNotIn("repository-url", job["steps"][uploads[0]].get("with") or {})
                order = [_index(job, DOWNLOAD), _index(job, VERIFY_DIST), _index(job, TESTPYPI_BEFORE), uploads[0], _index(job, PYPI_AFTER)]
                self.assertEqual(order, sorted(order))
                self.assertEqual(len(set(order)), len(order))
                self.assertEqual(_uses(job, "actions/checkout@"), [])

    def test_the_republish_job_runs_only_on_its_dispatch_behind_the_pypi_gate_and_builds_nothing(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                wf = _workflow(workflow)
                job = wf["jobs"][REPUBLISH]
                self.assertEqual(job["name"], REPUBLISH_NAME)
                # The ceremony counts a job as the TestPyPI or the PyPI job by those substrings; this one must be neither.
                self.assertNotIn("pypi", job["name"].lower())
                self.assertEqual(job["if"], REPUBLISH_IF)
                self.assertNotIn("needs", job)
                self.assertEqual(_environment(job), "pypi")
                self.assertEqual(wf["on"]["workflow_dispatch"]["inputs"], {"republish_from_testpypi": {"description": "Copy TestPyPI's files for this tag's version to PyPI (run from the release tag; nothing is built)", "type": "boolean", "default": False}})
                uploads = _uploads(job)
                self.assertEqual(len(uploads), 1)
                self.assertEqual(job["steps"][uploads[0]].get("with"), {"packages-dir": DIST_INPUT})
                order = [_index(job, FIND), _index(job, FETCH_ORIGINAL), _index(job, FETCH), _index(job, VERIFY_DIST), uploads[0], _index(job, PYPI_AFTER)]
                self.assertEqual(order, sorted(order))
                self.assertEqual(_uses(job, "actions/checkout@"), [])
                self.assertEqual(_step(job, FIND).get("id"), "original")
                self.assertEqual(_step(job, FIND).get("env"), {API_CREDENTIAL_ENV: RUNNER_CREDENTIAL})
                self.assertEqual(_step(job, FETCH_ORIGINAL)["if"], FETCH_ORIGINAL_IF)
                self.assertEqual(_step(job, FETCH_ORIGINAL)["with"], {"name": ARTIFACT, "run-id": "${{ steps.original.outputs.run-id }}", "github-token": RUNNER_CREDENTIAL, "path": "${{ runner.temp }}/release-run"})
                self.assertEqual(_step(job, FETCH)["env"], {"INDEX_URL": "https://test.pypi.org", "VERSION": "${{ steps.original.outputs.version }}", "RELEASE_RUN_SUMS": "${{ runner.temp }}/release-run/SHA256SUMS"})
                self.assertEqual(_step(job, PYPI_AFTER)["env"], {"INDEX_URL": "https://pypi.org"})

    def test_every_upload_takes_the_downloaded_dist_and_none_skips_an_existing_file(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                for job in jobs.values():
                    for i in _uploads(job):
                        inputs = job["steps"][i].get("with") or {}
                        self.assertEqual(inputs.get("packages-dir"), DIST_INPUT)
                        # skip-existing would keep an earlier file under the same name, and the install check would test
                        # it; the action still reads its older spelling too.
                        self.assertNotIn("skip-existing", inputs)
                        self.assertNotIn("skip_existing", inputs)
                        # Attestations stay on, the action's default.
                        self.assertIs(inputs.get("attestations", True), True)
                for job_id, inputs in zip((test_id, prod_id), UPLOAD_INPUTS[workflow]):
                    self.assertEqual([jobs[job_id]["steps"][i].get("with") for i in _uploads(jobs[job_id])], [inputs], job_id)

    def test_one_artifact_carries_the_dist_and_sha256sums_and_outlives_the_pypi_gate(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                upload = _step(jobs["build"], UPLOAD)["with"]
                self.assertEqual(upload["name"], ARTIFACT)
                self.assertEqual([p.strip() for p in upload["path"].splitlines() if p.strip()], [DIST_INPUT, "SHA256SUMS"])
                self.assertEqual(upload["if-no-files-found"], "error")
                # Exactly the documented 90 days, which outlive the gate's 30 days and the 30-day re-run window.
                self.assertIs(type(upload["retention-days"]), int)
                self.assertEqual(upload["retention-days"], ARTIFACT_RETENTION_DAYS)
                self.assertGreater(ARTIFACT_RETENTION_DAYS, GATE_APPROVAL_DAYS)
                self.assertLess(_index(jobs["build"], RECORD), _index(jobs["build"], UPLOAD))
                for job_id in (test_id, prod_id):
                    self.assertEqual(_step(jobs[job_id], DOWNLOAD)["with"], {"name": ARTIFACT, "path": "${{ github.workspace }}"})

    def test_each_json_check_reads_its_own_index_and_keeps_the_default_bounds(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                for job_id, name in ((test_id, TESTPYPI_AFTER), (prod_id, TESTPYPI_BEFORE), (prod_id, PYPI_AFTER)):
                    self.assertEqual(_step(jobs[job_id], name)["env"], {"INDEX_URL": INDEX_CHECKS[name]})

    def test_every_job_carries_only_its_listed_keys_and_runs_on_a_hosted_runner(self) -> None:
        # A job-level env (PIP_EXTRA_INDEX_URL, or HASH_CHECK_ATTEMPTS over a JSON check's bounds), a container, a matrix
        # or a self-hosted runner would change what a check runs, or against what. The workflow's run-name, a workflow
        # concurrency group that never cancels, and a job's timeout-minutes change no check (OPTIONAL_*_KEYS).
        for workflow, (package, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                wf = _workflow(workflow)
                sub = workflow != META
                required = WORKFLOW_KEYS | ({"concurrency"} if sub else set())
                self.assertTrue(required <= set(wf) <= required | OPTIONAL_WORKFLOW_KEYS, f"workflow keys {sorted(wf)}")
                want = {"build": BUILD_JOB_KEYS | ({"defaults"} if sub else set()), test_id: PUBLISH_JOB_KEYS, INSTALL: INSTALL_JOB_KEYS, prod_id: PUBLISH_JOB_KEYS, REPUBLISH: REPUBLISH_JOB_KEYS}
                self.assertEqual({job_id: set(job) - OPTIONAL_JOB_KEYS for job_id, job in wf["jobs"].items()}, want)
                self.assertEqual({job_id: job["runs-on"] for job_id, job in wf["jobs"].items()}, dict.fromkeys(want, "ubuntu-latest"))
                if sub:
                    self.assertEqual(wf["jobs"]["build"]["defaults"], {"run": {"working-directory": package}})

    def test_no_env_points_pip_elsewhere(self) -> None:
        # PIP_INDEX_URL or PIP_EXTRA_INDEX_URL in any env would send the install check, or the build tools, to another index.
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                wf = _workflow(workflow)
                envs = [wf.get("env") or {}] + [job.get("env") or {} for job in wf["jobs"].values()] + [step.get("env") or {} for job in wf["jobs"].values() for step in job.get("steps") or []]
                self.assertEqual([key for env in envs for key in env if str(key).upper().startswith("PIP_")], [])

    def test_the_build_steps_run_exactly_their_commands(self) -> None:
        # `|| true` after twine check, a build without its sdist, or a tag assertion against another prefix would ship
        # what the build job no longer checks.
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                build = _workflow(workflow)["jobs"]["build"]
                runs = {name: " ".join(line.strip().rstrip("\\").strip() for line in str(_step(build, name)["run"]).strip().splitlines()) for name in BUILD_RUNS[workflow]}
                self.assertEqual(runs, BUILD_RUNS[workflow])


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Ruling 2 of 2026-11-16: the install check runs in a job of its own, which cannot mint a credential
# ─────────────────────────────────────────────────────────────────────────────────────────────
class TestInstallCheckJob(unittest.TestCase):
    def test_it_runs_after_the_testpypi_job_with_contents_read_alone_and_pypi_needs_it(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                job = jobs[INSTALL]
                self.assertEqual(job["name"], INSTALL_NAME)
                # The release-train ceremony counts every job whose name holds "testpypi" as a TestPyPI job: a failure
                # here reads HALT_TESTPYPI, and the train stops.
                self.assertIn("testpypi", job["name"].lower())
                self.assertEqual(job["needs"], test_id)
                self.assertEqual(job["runs-on"], "ubuntu-latest")
                self.assertEqual(job["permissions"], {"contents": "read"})
                self.assertNotIn("environment", job)
                self.assertNotIn("if", job)
                self.assertEqual(_uploads(job), [])
                self.assertEqual(jobs[prod_id]["needs"], [test_id, INSTALL])

    def test_the_testpypi_job_keeps_only_the_template_steps_and_the_upload(self) -> None:
        for workflow, (_, _, test_id, _) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                job = _workflow(workflow)["jobs"][test_id]
                self.assertEqual(job["permissions"], {"id-token": "write"})
                self.assertEqual(_step_list(job), TESTPYPI_STEPS)
                self.assertEqual(_uses(job, f"{CHECKOUT}@") + _uses(job, f"{SETUP_PYTHON}@"), [])

    def test_it_installs_and_imports_from_outside_any_checkout(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                job = _workflow(workflow)["jobs"][INSTALL]
                self.assertNotIn("defaults", job)
                step = _install_step(workflow)
                self.assertNotIn("working-directory", step)
                commands = _commands(step["run"])
                if commands[0] == "set -euo pipefail":
                    commands = commands[1:]
                # `python -c` puts its working directory first on sys.path: a check run inside the checkout could pass
                # without the wheel. So the first command leaves for the runner's temporary directory, and none moves elsewhere.
                self.assertEqual(commands[0], CD)
                self.assertEqual([c for c in commands if c.split()[0] in ("cd", "pushd", "popd")], [CD])
                self.assertTrue([c for c in commands if "pip install" in c or "pip download" in c])
                self.assertTrue([c for c in commands if c.startswith("python -c ")])
                # Every publisher reads its version from a sparse checkout of the one file that holds it, and nothing runs
                # from it. It keeps no credential in the workspace while the package TestPyPI serves is installed.
                checkouts = [s.get("with") for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]
                self.assertEqual(checkouts, [{"sparse-checkout": f"{SPARSE_PATHS[workflow]}\n", "persist-credentials": False}])
                self.assertIn(f"${{GITHUB_WORKSPACE}}/{SPARSE_PATHS[workflow]}", step["run"])

    def test_the_install_step_runs_exactly_its_commands(self) -> None:
        # Exactly these commands, in this order, comment and blank lines dropped: no `exit 0`, trap, earlier install or
        # second version can be added, and none dropped, while a comment may change freely. The step carries its name
        # and script alone: its version comes from the checkout, so no tag reaches it, and no expression is pasted in.
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                step = _install_step(workflow)
                self.assertEqual(_commands(step["run"]), INSTALL_COMMANDS[workflow])
                self.assertEqual(set(step), {"name", "run"})
                self.assertNotIn("${{", step["run"])
                setups = [s.get("with") for s in _workflow(workflow)["jobs"][INSTALL]["steps"] if str(s.get("uses") or "").startswith(f"{SETUP_PYTHON}@")]
                self.assertEqual(setups, [{"python-version": "3.12"}] if workflow == META else [])

    def test_the_install_check_cannot_be_switched_off(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                step = _install_step(workflow)
                commands = "\n".join(_commands(step["run"]))
                # A failed install or check must fail the job: no `|| true` (nor any `||`), no `set +e`, the runner's
                # default shell, and neither continue-on-error nor if:.
                self.assertNotIn("||", commands)
                self.assertNotIn("set +e", commands)
                self.assertNotIn("shell", step)
                self.assertNotIn("continue-on-error", step)
                self.assertNotIn("if", step)
                # TestPyPI alone for the package itself, with no pypi.org fallback that a same-name squatter could answer
                # (juniper-ml#384); the meta-package resolves only its extras from production PyPI, from the local wheel.
                self.assertEqual(sum("--index-url https://test.pypi.org/simple/" in line for line in commands.splitlines()), 1)
                self.assertNotIn("--extra-index-url", commands)

    def test_a_metadata_check_also_finds_the_package_and_fails_through_systemexit(self) -> None:
        # R4-5: a check that reads metadata alone passes a wheel that lacks the package; find_spec locates it without
        # running it, and the step fails through SystemExit, which PYTHONOPTIMIZE keeps (it strips an assert).
        for workflow, module in sorted(FIND_SPEC.items()):
            with self.subTest(workflow=workflow):
                check = _commands(_install_step(workflow)["run"])[-1]
                self.assertEqual(check, _package_check(PUBLISHERS[workflow][0], module))
                self.assertNotIn("assert ", check)
        for workflow in sorted(set(PUBLISHERS) - set(FIND_SPEC)):
            with self.subTest(workflow=workflow):
                # Every other check imports its package, or runs it, which a wheel without it fails.
                self.assertTrue([c for c in _commands(_install_step(workflow)["run"]) if c.startswith(('python -c "import juniper_', "python -m juniper_"))])


def _stub(path: Path, body: str) -> None:
    path.write_text(f'#!/bin/sh\nprintf "%s\\t%s\\t%s\\n" "{path.name}" "$(pwd -P)" "$*" >> "$STUB_LOG"\n{body}', encoding="utf-8")
    path.chmod(0o700)


def _run_install(workflow: str, tmp_path: Path, pip_failures: int, python_status: int = 0, decoy: bool = False) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run WORKFLOW's install step as the runner runs a ``run:`` without a ``shell:`` (``bash -e {0}``), against stand-in
    ``pip``, ``python``, ``sleep`` and ``mktemp`` commands that log each call (the command, its directory, its
    arguments): ``pip`` fails its first PIP_FAILURES calls, and a ``pip download`` that succeeds writes the wheel the
    meta-package's check expects into ``--dest``; ``python`` reads a pyproject through the real interpreter (the
    meta-package's version probe) and otherwise exits with PYTHON_STATUS. The workspace's version file says 1.2.3; with
    DECOY, the runner's temporary directory holds a version file saying 6.6.6, which must not be read."""
    bin_dir, runner_temp, workspace = tmp_path / "bin", tmp_path / "runner-temp", tmp_path / "workspace"
    for directory in (bin_dir, runner_temp, workspace):
        directory.mkdir(parents=True)
    for root, version in ((workspace, "1.2.3"),) + (((runner_temp, "6.6.6"),) if decoy else ()):
        target = root / SPARSE_PATHS[workflow]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'__version__ = "{version}"\n' if target.name == "_version.py" else f'[project]\nname = "stand-in"\nversion = "{version}"\n', encoding="utf-8")
    log = tmp_path / "calls.log"
    pip_body = "".join(
        (
            'test "$(grep -c "^pip" "$STUB_LOG")" -gt "$STUB_PIP_FAILURES" || exit 1\n',
            'if [ "$1" = download ]; then\n',
            '  dest=""; prev=""\n',
            '  for a in "$@"; do if [ "$prev" = --dest ]; then dest="$a"; fi; prev="$a"; done\n',
            '  version="${STUB_VERSION}"\n',
            '  : > "$dest/juniper_ml-$version-py3-none-any.whl"\n',
            "fi\n",
        )
    )
    python_body = 'case "$*" in *tomllib*) exec "$STUB_REAL_PYTHON" "$@" ;; esac\nexit "$STUB_PYTHON_STATUS"\n'
    mktemp_body = 'mkdir -p "$STUB_MKTEMP_DIR"\nprintf "%s\\n" "$STUB_MKTEMP_DIR"\n'
    for name, body in {"pip": pip_body, "python": python_body, "sleep": "", "mktemp": mktemp_body, "juniper-check-doc-links": ""}.items():
        _stub(bin_dir / name, body)
    script = tmp_path / "install.sh"
    script.write_text(_install_step(workflow)["run"], encoding="utf-8")
    bash = shutil.which("bash")
    if not bash:
        raise AssertionError("the install checks run under bash")
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "RUNNER_TEMP": str(runner_temp),
        "GITHUB_WORKSPACE": str(workspace),
        "STUB_LOG": str(log),
        "STUB_PIP_FAILURES": str(pip_failures),
        "STUB_PYTHON_STATUS": str(python_status),
        "STUB_REAL_PYTHON": sys.executable,
        "STUB_MKTEMP_DIR": str(tmp_path / "download"),
        "STUB_VERSION": "1.2.3",
    }
    proc = subprocess.run([bash, "-e", str(script)], cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=60, check=False)  # nosec B603 - fixed argv: bash and the workflow's own extracted step
    calls = [line.split("\t", 2) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return proc, calls


class TestInstallCheckScript(unittest.TestCase):
    """Each install step's own shell, run as the runner runs it, against stand-in ``pip``, ``python`` and ``sleep``."""

    def setUp(self) -> None:
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)

    def case(self, name: str) -> Path:
        path = self.root / re.sub(r"[^a-z0-9]+", "-", name.lower())
        path.mkdir()
        return path

    def test_index_lag_that_outlasts_every_try_fails_naming_the_lag_and_never_runs_the_check(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                proc, calls = _run_install(workflow, self.case(workflow), pip_failures=INSTALL_TRIES[workflow])
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn(f"::error::{package} 1.2.3 {LAG_ERROR.format(tries=INSTALL_TRIES[workflow])}", proc.stdout)
                # The meta-package's version probe runs first; no check runs after the last failed try.
                probe = [["python"]] if workflow == META else []
                self.assertEqual([call[:1] for call in calls if call[0] in ("pip", "python")], probe + [["pip"]] * INSTALL_TRIES[workflow])
                self.assertEqual([int(call[2]) for call in calls if call[0] == "sleep"], INSTALL_WAITS[workflow])

    def test_a_try_that_installs_ends_the_retries_and_the_check_runs_from_runner_temp(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                case = self.case(workflow)
                proc, calls = _run_install(workflow, case, pip_failures=2)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                pips = [call[2] for call in calls if call[0] == "pip"]
                if workflow == META:
                    fetch = f"download --no-deps --index-url https://test.pypi.org/simple/ --dest {case / 'download'} juniper-ml==1.2.3"
                    wheel = case / "download" / "juniper_ml-1.2.3-py3-none-any.whl"
                    self.assertEqual(pips, [fetch] * 3 + [f"install --index-url https://pypi.org/simple/ {wheel}{extra}" for extra in ("", "[clients]", "[tools]")])
                else:
                    self.assertEqual(pips, [f"install --no-deps --index-url https://test.pypi.org/simple/ {package}==1.2.3"] * 3)
                self.assertEqual([call[0] for call in calls][-1], "python")
                # Every command, the version probe included, runs in the runner's temporary directory.
                self.assertEqual({call[1] for call in calls}, {str((case / "runner-temp").resolve())})
                self.assertNotIn("::error::", proc.stdout)

    def test_a_check_that_fails_after_the_install_fails_the_step(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                proc, calls = _run_install(workflow, self.case(workflow), pip_failures=0, python_status=1)
                self.assertNotEqual(proc.returncode, 0)
                ran = [call[0] for call in calls if call[0] not in ("sleep", "mktemp")]
                # The first check that fails stops the step: nothing after it runs.
                self.assertEqual(ran[-1], "python")
                self.assertEqual(ran.count("python"), 2 if workflow == META else 1)

    def test_the_version_is_read_from_the_workspace_not_the_runner_temp_directory(self) -> None:
        # The check runs from $RUNNER_TEMP, and reads its version under $GITHUB_WORKSPACE: a version file beside it there
        # is never the one read.
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                proc, calls = _run_install(workflow, self.case(workflow), pip_failures=0, decoy=True)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                first = next(call[2] for call in calls if call[0] == "pip")
                self.assertTrue(first.endswith(f"{PUBLISHERS[workflow][0]}==1.2.3"), first)
                self.assertNotIn("6.6.6", "".join(call[2] for call in calls))

    def test_the_package_check_finds_a_wheels_package_without_running_it_and_refuses_one_without_it(self) -> None:
        # The check's own python -c, run by a real interpreter with -S (the environment's site-packages, which may hold
        # the real package, stay off sys.path) against a stand-in site directory, from an empty working directory. The
        # site holds the package and its metadata ("package"), the metadata alone ("metadata-only"), the metadata and an
        # empty directory in the package's place, a namespace package with no origin ("bare-directory"), or nothing.
        for workflow, module in sorted(FIND_SPEC.items()):
            package = PUBLISHERS[workflow][0]
            check = _commands(_install_step(workflow)["run"])[-1]
            code = check[len('python -c "') : -1]
            for kind in ("package", "metadata-only", "bare-directory", "nothing"):
                for optimize in ("", "1", "2"):
                    with self.subTest(workflow=workflow, kind=kind, optimize=optimize):
                        case = self.case(f"{workflow}-{kind}-{optimize or 'plain'}")
                        site, cwd = case / "site", case / "cwd"
                        cwd.mkdir()
                        site.mkdir()
                        if kind != "nothing":
                            info = site / f"{module}-1.2.3.dist-info"
                            info.mkdir()
                            (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {package}\nVersion: 1.2.3\n", encoding="utf-8")
                        if kind in ("package", "bare-directory"):
                            (site / module).mkdir()
                        if kind == "package":
                            # Its __init__ raises: the check must find the package without running it.
                            (site / module / "__init__.py").write_text("raise RuntimeError('the check ran the package')\n", encoding="utf-8")
                        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(site)}
                        if optimize:
                            env["PYTHONOPTIMIZE"] = optimize
                        proc = subprocess.run([sys.executable, "-S", "-c", code], cwd=cwd, env=env, capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv: this interpreter and the workflow's own check
                        if kind == "package":
                            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                            self.assertIn(f"TestPyPI install 1.2.3 package at {site / module / '__init__.py'}", proc.stdout)
                        elif kind == "nothing":
                            # No metadata: the version lookup itself fails the step, before the check prints anything.
                            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                            self.assertEqual(proc.stdout, "")
                            self.assertIn("PackageNotFoundError", proc.stderr)
                        else:
                            # The metadata alone passes the version lookup; the package check then fails through
                            # SystemExit with its own message and nothing else: no traceback (a traceback of 3.13 and
                            # later quotes the -c source, the message included, so a substring test would pass on it).
                            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                            self.assertEqual(proc.stdout, "TestPyPI install 1.2.3 package at None\n")
                            self.assertEqual(proc.stderr, f"the installed wheel holds no {module} package\n")


class TestUnchanged(unittest.TestCase):
    """What each publisher kept. The permissions changed: TestWiring pins them per job."""

    def test_publish_yml_builds_on_its_release_or_a_plain_dispatch_and_keeps_its_tag_guard(self) -> None:
        wf = _workflow(META)
        self.assertEqual(set(wf["on"]), {"release", "workflow_dispatch"})
        self.assertEqual(wf["on"]["release"], {"types": ["published"]})
        self.assertNotIn("concurrency", wf)
        # A plain dispatch from a `v` tag still re-fires the whole publish (it builds); the republish dispatch runs the
        # republish job alone.
        self.assertEqual(wf["jobs"]["build"]["if"], GUARD.format(prefix="v"))
        for job_id in ("testpypi", INSTALL, "pypi"):
            self.assertNotIn("if", wf["jobs"][job_id], job_id)

    def test_publish_yml_builds_with_the_commands_it_used_before_and_asserts_the_tag(self) -> None:
        build = _workflow(META)["jobs"]["build"]
        runs = [str(s.get("run") or "").strip() for s in build["steps"]]
        self.assertLess(runs.index("pip install build twine"), runs.index("python -m build"))
        self.assertLess(runs.index("python -m build"), runs.index("twine check dist/*"))
        assert_tag = _step(build, ASSERT_TAG)["run"]
        for token in ("util/assert_release_tag.bash", '--ref "${{ github.ref }}"', "--dist-dir dist", "--expect-prefix v"):
            self.assertIn(token, assert_tag)
        self.assertLess(runs.index("twine check dist/*"), _index(build, ASSERT_TAG))
        self.assertLess(_index(build, ASSERT_TAG), _index(build, RECORD))

    def test_publish_yml_runs_its_two_phase_install_check_in_the_install_job_with_the_testpypi_jobs_python(self) -> None:
        jobs = _workflow(META)["jobs"]
        job = jobs[INSTALL]
        # The install check reads the version from pyproject.toml, so the job checks that one file out, after the
        # setup-python 3.12 the TestPyPI job ran it with.
        setup, checkout = _uses(job, f"{SETUP_PYTHON}@"), _uses(job, f"{CHECKOUT}@")
        self.assertEqual((len(setup), len(checkout)), (1, 1))
        self.assertLess(setup[0], checkout[0])
        self.assertLess(checkout[0], _index(job, INSTALL_STEPS[META]))
        self.assertEqual(job["steps"][setup[0]]["with"], {"python-version": "3.12"})
        verify = _install_step(META)["run"]
        self.assertIn("tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version']", verify)
        self.assertIn('pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}"', verify)
        self.assertEqual(_uses(jobs["testpypi"], f"{CHECKOUT}@") + _uses(jobs["testpypi"], f"{SETUP_PYTHON}@"), [])

    def test_publish_yml_keeps_attestations_on_both_uploads_and_its_pypi_job_sets_up_nothing(self) -> None:
        jobs = _workflow(META)["jobs"]
        test_upload = jobs["testpypi"]["steps"][_uploads(jobs["testpypi"])[0]]["with"]
        prod_upload = jobs["pypi"]["steps"][_uploads(jobs["pypi"])[0]]["with"]
        self.assertEqual(test_upload, {"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT, "attestations": True})
        self.assertEqual(prod_upload, {"packages-dir": DIST_INPUT, "attestations": True})
        self.assertEqual(_uses(jobs["pypi"], "actions/setup-python@"), [])
        self.assertEqual(_uses(jobs["pypi"], "actions/checkout@"), [])

    def test_the_sub_package_publishers_keep_their_triggers_and_concurrency_and_build_on_their_release_or_a_plain_dispatch(self) -> None:
        for workflow in SUB_PACKAGES:
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                wf = _workflow(workflow)
                self.assertEqual(set(wf["on"]), {"release", "workflow_dispatch"})
                self.assertEqual(wf["on"]["release"], {"types": ["published"]})
                suffix = workflow[len("publish-") : -len(".yml")]
                self.assertEqual(wf["concurrency"], {"group": f"publish-{suffix}-${{{{ github.ref_name }}}}", "cancel-in-progress": False})
                # A plain dispatch still re-fires the whole publish, from the package's own tag alone (another tag's would
                # publish this package's files under that tag's run); the republish dispatch runs the republish job alone.
                self.assertEqual(wf["jobs"]["build"]["if"], GUARD.format(prefix=f"{package}-v"))
                self.assertEqual(wf["jobs"]["build"]["defaults"], {"run": {"working-directory": package}})

    def test_the_sub_package_publishers_build_with_the_commands_they_used_before_and_assert_the_tag(self) -> None:
        for workflow in SUB_PACKAGES:
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                build = _workflow(workflow)["jobs"]["build"]
                runs = [str(s.get("run") or "").strip() for s in build["steps"]]
                self.assertLess(runs.index("pip install --upgrade build twine"), runs.index("python -m build --sdist --wheel"))
                self.assertLess(runs.index("python -m build --sdist --wheel"), runs.index("twine check dist/*"))
                assert_tag = _step(build, ASSERT_TAG)["run"]
                for token in ("../util/assert_release_tag.bash", '--ref "${{ github.ref }}"', "--dist-dir dist", f"--expect-prefix {package}-v"):
                    self.assertIn(token, assert_tag)
                self.assertLess(_index(build, ASSERT_TAG), _index(build, RECORD))

    def test_the_sub_package_publishers_keep_their_environment_urls_verbose_uploads_and_install_check(self) -> None:
        for workflow in SUB_PACKAGES:
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                jobs = _workflow(workflow)["jobs"]
                test_job, prod_job = jobs["publish-testpypi"], jobs["publish-pypi"]
                self.assertEqual(test_job["environment"], {"name": "testpypi", "url": f"https://test.pypi.org/p/{package}"})
                self.assertEqual(prod_job["environment"], {"name": "pypi", "url": f"https://pypi.org/p/{package}"})
                self.assertEqual(test_job["steps"][_uploads(test_job)[0]]["with"], {"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT, "verbose": True})
                self.assertEqual(prod_job["steps"][_uploads(prod_job)[0]]["with"], {"packages-dir": DIST_INPUT, "verbose": True})
                # The sparse checkout the install check reads its version from moved with it, to the install job.
                install = jobs[INSTALL]
                checkout = _uses(install, "actions/checkout@")
                self.assertEqual(len(checkout), 1)
                self.assertLess(checkout[0], _index(install, INSTALL_STEPS[workflow]))
                self.assertIn(f"{package}/", install["steps"][checkout[0]]["with"]["sparse-checkout"])
                run = _install_step(workflow)["run"]
                for token in ("--no-deps", "--index-url https://test.pypi.org/simple/", f'"{package}==${{version}}"'):
                    self.assertIn(token, run)


class TestTemplate(unittest.TestCase):
    def test_every_copy_of_a_template_step_is_byte_identical(self) -> None:
        copies: dict[str, list[str]] = {REUSE: [], RECORD: [], VERIFY_DIST: [], "index": [], FIND: [], FETCH: []}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    kind = "index" if step.get("name") in INDEX_CHECKS else step.get("name")
                    if kind in copies:
                        self.assertEqual(step.get("shell"), "python3 {0}")
                        copies[kind].append(step["run"])
        # Per workflow: one reuse step and one record step; a dist check before each of three uploads; three JSON checks
        # in the release jobs and one in the republish job; one of each republish step. Seven workflows.
        self.assertEqual({kind: len(runs) for kind, runs in copies.items()}, {REUSE: 7, RECORD: 7, VERIFY_DIST: 21, "index": 28, FIND: 7, FETCH: 7})
        self.assertEqual({kind: len(set(runs)) for kind, runs in copies.items()}, {REUSE: 1, RECORD: 1, VERIFY_DIST: 1, "index": 1, FIND: 1, FETCH: 1})

    def test_the_template_steps_are_juniper_cascors_byte_for_byte(self) -> None:
        # Each template block, comments included, equals juniper-cascor's byte for byte once each uses: line is reduced to
        # its action's name; the refs are pinned to one per action in the next cases.
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                blocks = _template_blocks(_text(workflow), test_id, prod_id)
                self.assertEqual({key: _sha(_normalized(block).encode("utf-8")) for key, block in blocks.items()}, CASCOR_TEMPLATE_SHA256)

    def test_the_republish_job_is_juniper_cascors_byte_for_byte(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                self.assertEqual(_sha(_normalized(_republish_job(_text(workflow))).encode("utf-8")), CASCOR_REPUBLISH_SHA256)

    def test_the_republish_job_is_byte_identical_in_every_publisher(self) -> None:
        # Compared with each action's @ref dropped: the next case pins each action to one ref in every publisher, so a
        # partial bump fails there, once, rather than here as a template difference.
        jobs = [_by_action(_workflow(workflow)["jobs"][REPUBLISH]) for workflow in sorted(PUBLISHERS)]
        for job in jobs[1:]:
            self.assertEqual(job, jobs[0])

    def test_each_action_is_pinned_to_one_ref_in_every_publisher(self) -> None:
        # Dependabot bumps an action in all seven files at once; a hand edit that bumps one copy fails here, wherever it is.
        refs: dict[str, set[str]] = {}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    if step.get("uses"):
                        name, _, ref = str(step["uses"]).partition("@")
                        refs.setdefault(name, set()).add(ref)
        self.assertEqual({name: len(found) for name, found in refs.items()}, dict.fromkeys(refs, 1), refs)
        self.assertEqual(sorted(refs), sorted([CHECKOUT, SETUP_PYTHON, UPLOAD_ACTION, DOWNLOAD_ACTION, PYPI_PUBLISH]))

    def test_the_normalized_digest_drops_only_the_ref_of_a_uses_line(self) -> None:
        block = "      - name: X\n        uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567  # v7.0.2\n        with:\n          name: x  # v1\n"
        self.assertEqual(_normalized(block), "      - name: X\n        uses: actions/upload-artifact\n        with:\n          name: x  # v1\n")
        self.assertEqual(_normalized("      - uses: actions/checkout@v7\n"), "      - uses: actions/checkout\n")
        # Any other line, a comment's version among them, is kept as it is.
        self.assertEqual(_normalized("      # uses: actions/checkout@v7\n"), "      # uses: actions/checkout@v7\n")

    def test_the_template_reads_nothing_but_its_parameters(self) -> None:
        for kind, run in _template_scripts().items():
            with self.subTest(kind=kind):
                self.assertNotIn("${{", run, f"{kind}: an expression would tie the step to one workflow")
                read = set(re.findall(r"os\.environ(?:\.get\(|\[)[\"']([A-Z_]+)[\"']", run))
                self.assertTrue(read, kind)
                self.assertLessEqual(read, TEMPLATE_ENV, f"{kind} reads {sorted(read - TEMPLATE_ENV)}")

    def test_the_json_check_polls_a_bounded_number_of_times(self) -> None:
        run = _template_scripts()["index"]
        attempts = re.search(r'"HASH_CHECK_ATTEMPTS", "(\d+)"', run)
        interval = re.search(r'"HASH_CHECK_INTERVAL", "(\d+(?:\.\d+)?)"', run)
        if attempts is None or interval is None:
            self.fail("the JSON check no longer reads its bounds from HASH_CHECK_ATTEMPTS / HASH_CHECK_INTERVAL with defaults")
        # Long enough for a CDN to catch up after an upload, and bounded; each request is bounded too.
        self.assertTrue(60 <= int(attempts.group(1)) * float(interval.group(1)) <= 900)
        self.assertIn("urllib.request.urlopen(request, timeout=30)", run)
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    self.assertFalse({"HASH_CHECK_ATTEMPTS", "HASH_CHECK_INTERVAL"} & set(step.get("env") or {}), f"{workflow}: {step.get('name')} overrides the bounds")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Rehearsals: the template steps' own Python, run as the runner runs it
# ─────────────────────────────────────────────────────────────────────────────────────────────
class TestRecordSha256sums(_Scratch):
    def test_it_hashes_every_distribution_in_sha256sum_format(self) -> None:
        workspace = self.workspace()
        proc = _run(_script(RECORD, self.tmp_path), workspace)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((workspace / "SHA256SUMS").read_text(encoding="utf-8"), "".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items())))

    def test_sha256sum_checks_what_it_writes(self) -> None:
        binary = shutil.which("sha256sum")
        if binary is None:
            self.skipTest("no sha256sum on PATH")
        workspace = self.workspace()
        self.assertEqual(_run(_script(RECORD, self.tmp_path), workspace).returncode, 0)
        check = subprocess.run([binary, "--check", "--strict", str(workspace / "SHA256SUMS")], cwd=workspace / "dist", capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_it_refuses_anything_but_wheels_and_sdists(self) -> None:
        for stray in ("notes.txt", "juniper_ml-9.9.9.zip"):
            with self.subTest(stray=stray):
                workspace = self.workspace(f"workspace-{stray}")
                (workspace / "dist" / stray).write_bytes(b"x")
                proc = _run(_script(RECORD, self.tmp_path), workspace)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                self.assertFalse((workspace / "SHA256SUMS").exists())

    def test_it_refuses_an_empty_or_a_missing_dist_directory(self) -> None:
        root = self.tmp_path / "empty"
        (root / "dist").mkdir(parents=True)
        script = _script(RECORD, self.tmp_path)
        self.assertEqual(_run(script, root).returncode, 1)
        self.assertEqual(_run(script, root, env={"PUBLISH_DIST_DIR": "nowhere"}).returncode, 1)

    def test_it_leaves_out_dotfiles_as_the_upload_does(self) -> None:
        workspace = self.workspace()
        (workspace / "dist" / ".gitignore").write_text("*\n", encoding="utf-8")
        self.assertEqual(_run(_script(RECORD, self.tmp_path), workspace).returncode, 0)
        self.assertNotIn(".gitignore", (workspace / "SHA256SUMS").read_text(encoding="utf-8"))

    def test_a_nested_dist_directory_resolves_from_the_workspace_not_the_working_directory(self) -> None:
        root = self.tmp_path / "nested"
        package_dir = root / "juniper-ci-tools"
        (package_dir / "dist").mkdir(parents=True)
        (package_dir / "dist" / "juniper_ci_tools-1.0.0-py3-none-any.whl").write_bytes(b"ci-tools wheel")
        # The sub-package build jobs run every step in the package directory (defaults.run.working-directory).
        proc = _run(_script(RECORD, self.tmp_path), root, cwd=package_dir, env={"PUBLISH_PACKAGE": "juniper-ci-tools", "PUBLISH_DIST_DIR": "juniper-ci-tools/dist"})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual((root / "SHA256SUMS").read_text(encoding="utf-8"), f"{_sha(b'ci-tools wheel')}  juniper_ci_tools-1.0.0-py3-none-any.whl\n")


class TestVerifyDist(_Scratch):
    def _recorded(self, workspace: Path) -> Path:
        self.assertEqual(_run(_script(RECORD, self.tmp_path), workspace).returncode, 0)
        return _script(VERIFY_DIST, self.tmp_path)

    def test_it_passes_on_the_files_the_build_recorded(self) -> None:
        workspace = self.workspace()
        proc = _run(self._recorded(workspace), workspace)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_it_ignores_dotfiles_as_the_upload_does(self) -> None:
        workspace = self.workspace()
        script = self._recorded(workspace)
        (workspace / "dist" / ".gitignore").write_text("*\n", encoding="utf-8")
        proc = _run(script, workspace)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_it_fails_when_a_file_changed(self) -> None:
        workspace = self.workspace()
        script = self._recorded(workspace)
        (workspace / "dist" / WHEEL).write_bytes(b"another build")
        self.assertEqual(_run(script, workspace).returncode, 1)

    def test_it_fails_on_a_file_the_build_did_not_record(self) -> None:
        workspace = self.workspace()
        script = self._recorded(workspace)
        (workspace / "dist" / "juniper_ml-9.9.9-py2.py3-none-any.whl").write_bytes(b"x")
        self.assertEqual(_run(script, workspace).returncode, 1)

    def test_it_fails_when_a_recorded_file_is_missing(self) -> None:
        workspace = self.workspace()
        script = self._recorded(workspace)
        (workspace / "dist" / SDIST).unlink()
        self.assertEqual(_run(script, workspace).returncode, 1)

    def test_it_fails_on_a_sha256sums_it_cannot_read(self) -> None:
        workspace = self.workspace()
        cases = {"empty": "", "not-a-sha256": f"nothex  {WHEEL}\n", "one-space": f"{'a' * 64} {WHEEL}\n", "listed-twice": f"{'a' * 64}  {WHEEL}\n{'a' * 64}  {WHEEL}\n"}
        for case, sums in cases.items():
            with self.subTest(case=case):
                (workspace / "SHA256SUMS").write_text(sums, encoding="utf-8")
                self.assertEqual(_run(_script(VERIFY_DIST, self.tmp_path), workspace).returncode, 1)


class TestIndexCheck(_Scratch):
    def _ready(self, workspace: Path) -> Path:
        self.assertEqual(_run(_script(RECORD, self.tmp_path), workspace).returncode, 0)
        return _script("index", self.tmp_path)

    @staticmethod
    def _check(script: Path, workspace: Path, server: _Stand, attempts: int = 4) -> subprocess.CompletedProcess[str]:
        return _run(script, workspace, env={"INDEX_URL": server.url, "HASH_CHECK_ATTEMPTS": str(attempts), "HASH_CHECK_INTERVAL": "0"})

    def test_an_exact_match_passes_at_the_first_answer(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, _release(SERVED))]})
        proc = self._check(self._ready(workspace), workspace, server)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(server.paths(), [JSON_PATH])

    def test_it_polls_through_a_version_the_index_does_not_serve_yet(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [NOT_FOUND, NOT_FOUND, (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace), workspace, server)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(server.paths()), 3)

    def test_it_polls_through_a_file_the_index_does_not_list_yet(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, _release({WHEEL: SERVED[WHEEL]})), (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace), workspace, server)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(server.paths()), 2)

    def test_it_polls_through_an_answer_it_cannot_read(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, b"<html>busy</html>"), (503, b""), (200, {"info": {}}), (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace), workspace, server, attempts=5)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(len(server.paths()), 4)

    def test_an_index_that_lists_no_files_never_passes(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, _release({}))]})
        proc = self._check(self._ready(workspace), workspace, server, attempts=3)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("after 3 attempts", proc.stdout)
        self.assertEqual(len(server.paths()), 3)

    def test_a_file_with_another_sha256_fails_at_once(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, _release({**SERVED, WHEEL: _sha(b"another build")}))]})
        proc = self._check(self._ready(workspace), workspace, server)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("::error::", proc.stdout)
        self.assertEqual(len(server.paths()), 1)

    def test_a_file_this_run_did_not_build_fails_at_once(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [(200, _release({**SERVED, "juniper_ml-9.9.9-py2.py3-none-any.whl": "b" * 64}))]})
        proc = self._check(self._ready(workspace), workspace, server)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(len(server.paths()), 1)

    def test_it_gives_up_after_its_bounded_attempts(self) -> None:
        workspace = self.workspace()
        server = self.stand({JSON_PATH: [NOT_FOUND]})
        proc = self._check(self._ready(workspace), workspace, server, attempts=3)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("after 3 attempts", proc.stdout)
        self.assertEqual(len(server.paths()), 3)

    def test_it_refuses_a_sha256sums_it_cannot_vouch_for_before_asking_the_index(self) -> None:
        extras = {"another-package": "juniper_ci_tools-9.9.9-py3-none-any.whl", "another-version": "juniper_ml-9.9.8.tar.gz", "not-a-distribution": "juniper_ml-9.9.9.zip"}
        for case, extra in extras.items():
            with self.subTest(case=case):
                workspace = self.workspace(f"workspace-{case}")
                script = self._ready(workspace)
                with (workspace / "SHA256SUMS").open("a", encoding="utf-8") as sums:
                    sums.write(f"{'c' * 64}  {extra}\n")
                server = self.stand({JSON_PATH: [(200, _release(SERVED))]})
                proc = self._check(script, workspace, server)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                self.assertEqual(server.paths(), [])


def _github_env(case_dir: Path, server: _Stand, **extra: str) -> dict[str, str]:
    case_dir.mkdir(parents=True, exist_ok=True)
    output = case_dir / "github_output"
    output.touch()
    env = {"GITHUB_API_URL": server.url, "GITHUB_REPOSITORY": REPOSITORY, API_CREDENTIAL_ENV: FAKE_API_CREDENTIAL, "GITHUB_OUTPUT": str(output)}
    env.update(extra)
    return env


def _outputs(case_dir: Path) -> dict[str, str]:
    text = (case_dir / "github_output").read_text(encoding="utf-8")
    return dict(line.split("=", 1) for line in text.splitlines() if line)


RUN_ARTIFACTS = f"/repos/{REPOSITORY}/actions/runs/4242/artifacts?name=juniper-ml-dist&per_page=100"


class TestReuseStep(_Scratch):
    @staticmethod
    def _env(case_dir: Path, server: _Stand) -> dict[str, str]:
        return _github_env(case_dir, server, GITHUB_RUN_ID="4242", GITHUB_RUN_ATTEMPT="2")

    def test_an_unexpired_artifact_from_an_earlier_attempt_is_reused(self) -> None:
        workspace = self.workspace()
        server = self.stand({RUN_ARTIFACTS: [(200, {"artifacts": [{"id": 7, "name": "juniper-ml-dist", "expired": False}]})]})
        proc = _run(_script(REUSE, self.tmp_path), workspace, env=self._env(self.tmp_path, server))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path), {"reuse": "true"})
        path, headers = server.requests[0]
        self.assertEqual(path, RUN_ARTIFACTS)
        self.assertEqual(headers.get("Authorization"), f"Bearer {FAKE_API_CREDENTIAL}")

    def test_without_a_usable_artifact_the_attempt_builds(self) -> None:
        workspace = self.workspace()
        cases = {"none": [], "expired": [{"id": 7, "name": "juniper-ml-dist", "expired": True}], "another-name": [{"id": 8, "name": "coverage-report", "expired": False}]}
        for case, artifacts in cases.items():
            with self.subTest(case=case):
                case_dir = self.tmp_path / case
                server = self.stand({RUN_ARTIFACTS: [(200, {"artifacts": artifacts})]})
                proc = _run(_script(REUSE, self.tmp_path), workspace, env=self._env(case_dir, server))
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertEqual(_outputs(case_dir), {})

    def test_an_api_failure_fails_the_job_rather_than_rebuild(self) -> None:
        workspace = self.workspace()
        server = self.stand({RUN_ARTIFACTS: [(500, {"message": "boom"})]})
        proc = _run(_script(REUSE, self.tmp_path), workspace, env=self._env(self.tmp_path, server))
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(_outputs(self.tmp_path), {})


def _runs_path(tag: str, workflow: str = META) -> str:
    return f"/repos/{REPOSITORY}/actions/workflows/{workflow}/runs?event=release&branch={tag}&per_page=30"


def _artifacts_path(run_id: int, package: str = "juniper-ml") -> str:
    return f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?name={package}-dist&per_page=100"


def _jobs_path(run_id: int, page: int = 1) -> str:
    return f"/repos/{REPOSITORY}/actions/runs/{run_id}/jobs?filter=all&per_page=100&page={page}"


def _job(job_id: int, name: str, conclusion: str | None, attempt: int = 1) -> dict:
    """A job record as ``GET actions/runs/{id}/jobs?filter=all`` lists it: each attempt that ran a job has its own."""
    return {"id": job_id, "name": name, "run_attempt": attempt, "status": "completed" if conclusion else "in_progress", "conclusion": conclusion}


def _attempt(attempt: int, first_id: int, testpypi: str | None = "success", install: str | None = "success", pypi: str | None = "failure") -> list[dict]:
    """One attempt of a release run: the build, both TestPyPI jobs, the PyPI job, and the republish job, which every
    release run skips. The PyPI job fails by default, as when its gate's 30 days ran out: the case rung 1 is for."""
    jobs = (("Build and Validate", "success"), ("Publish to TestPyPI", testpypi), (INSTALL_NAME, install), ("Publish to PyPI", pypi), (REPUBLISH_NAME, "skipped"))
    return [_job(first_id + i, name, conclusion, attempt) for i, (name, conclusion) in enumerate(jobs)]


def _listing(*records: dict, total: int | None = None) -> tuple[int, dict]:
    return (200, {"total_count": len(records) if total is None else total, "jobs": list(records)})


LIVE_ARTIFACT = [{"id": 7, "name": "juniper-ml-dist", "expired": False}]


class TestFindReleaseRun(_Scratch):
    @staticmethod
    def _env(case_dir: Path, server: _Stand, tag: str = "v9.9.9", ref_type: str = "tag", workflow: str = META) -> dict[str, str]:
        return _github_env(case_dir, server, GITHUB_REF_NAME=tag, GITHUB_REF_TYPE=ref_type, GITHUB_REF=f"refs/{'tags' if ref_type == 'tag' else 'heads'}/{tag}", GITHUB_WORKFLOW_REF=f"{REPOSITORY}/.github/workflows/{workflow}@refs/tags/{tag}")

    def _serve(self, jobs: list[dict], artifacts: list[dict] | None = None, tag: str = "v9.9.9", workflow: str = META, package: str = "juniper-ml") -> _Stand:
        """The stand-in GitHub API for TAG's one release run, 4242: its job records and its artifacts."""
        return self.stand(
            {
                _runs_path(tag, workflow): [(200, {"workflow_runs": [{"id": 4242, "head_branch": tag}]})],
                _jobs_path(4242): [_listing(*jobs)],
                _artifacts_path(4242, package): [(200, {"artifacts": LIVE_ARTIFACT if artifacts is None else artifacts})],
            }
        )

    def _find(self, server: _Stand, case_dir: Path, **extra: str) -> subprocess.CompletedProcess[str]:
        return _run(_script(FIND, self.tmp_path), self.workspace(f"workspace-{case_dir.name}"), env=self._env(case_dir, server, **extra))

    def test_the_newest_release_run_is_the_one_checked_and_its_artifact_is_found(self) -> None:
        runs = [{"id": 111, "head_branch": "v9.9.9"}, {"id": 333, "head_branch": "v9.9.9"}, {"id": 222, "head_branch": "v9.9.9"}, {"id": 444, "head_branch": "v9.9.99"}]
        server = self.stand({_runs_path("v9.9.9"): [(200, {"workflow_runs": runs})], _jobs_path(333): [_listing(*_attempt(1, 100))], _artifacts_path(333): [(200, {"artifacts": LIVE_ARTIFACT})]})
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path / "case"), {"version": "9.9.9", "run-id": "333"})
        # The newest run of THIS tag, whether or not it still holds its artifact: never an older run, nor another tag's.
        self.assertEqual(server.paths(), [_runs_path("v9.9.9"), _jobs_path(333), _artifacts_path(333)])
        self.assertTrue(all(headers.get("Authorization") == f"Bearer {FAKE_API_CREDENTIAL}" for _, headers in server.requests))

    def test_a_release_run_whose_artifact_expired_is_still_checked_and_testpypi_is_the_only_record(self) -> None:
        server = self._serve(_attempt(1, 100), artifacts=[{"id": 7, "name": "juniper-ml-dist", "expired": True}])
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path / "case"), {"version": "9.9.9", "run-id": ""})
        self.assertIn("::warning::", proc.stdout)

    def test_without_a_release_run_for_the_tag_nothing_is_republished(self) -> None:
        server = self.stand({_runs_path("v9.9.9"): [(200, {"workflow_runs": [{"id": 5, "head_branch": "v9.9.99"}]})]})
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("::error::", proc.stdout)
        self.assertIn("no release run for v9.9.9", proc.stdout)
        self.assertEqual(server.paths(), [_runs_path("v9.9.9")])
        self.assertEqual(_outputs(self.tmp_path / "case"), {})

    def test_a_release_run_whose_testpypi_jobs_did_not_both_pass_is_refused(self) -> None:
        cases = {"the-upload-failed": ("failure", "skipped"), "the-install-check-failed": ("success", "failure"), "the-upload-was-cancelled": ("cancelled", "skipped"), "the-install-check-still-runs": ("success", None)}
        for case, (testpypi, install) in cases.items():
            with self.subTest(case=case):
                server = self._serve(_attempt(1, 100, testpypi=testpypi, install=install))
                proc = self._find(server, self.tmp_path / case)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                # Each TestPyPI job is named with its conclusion, or with its status while it has none.
                self.assertIn(f"  Publish to TestPyPI: {testpypi} (attempt 1)", proc.stdout)
                self.assertIn(f"  {INSTALL_NAME}: {install or 'in_progress'} (attempt 1)", proc.stdout)
                self.assertNotIn(_artifacts_path(4242), server.paths())
                self.assertEqual(_outputs(self.tmp_path / case), {})

    def test_a_job_that_re_run_failed_jobs_carried_over_counts_with_its_earlier_success(self) -> None:
        # Attempt 1 passed both TestPyPI jobs and failed at PyPI; "Re-run failed jobs" ran the PyPI job alone again. This
        # listing leaves out the copies GitHub makes of the jobs it carries over (the next case has them): neither TestPyPI
        # job has a record of attempt 2, and each still counts with its earlier success.
        server = self._serve(_attempt(1, 100) + [_job(203, "Publish to PyPI", "failure", attempt=2)])
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path / "case"), {"version": "9.9.9", "run-id": "4242"})

    def test_re_run_failed_jobs_copies_the_jobs_it_carries_over_into_the_new_attempt(self) -> None:
        # As GitHub lists it (juniper-canopy run 43135960676): attempt 1's install check failed on lag, and "Re-run failed
        # jobs" gave EVERY job a record in attempt 2, the build and the upload as copies (a new id, run_attempt 2, attempt
        # 1's conclusion), the install check and the PyPI job as new runs.
        for case, (install, passes) in {"the-re-run-install-check-passed": ("success", True), "it-failed-again": ("failure", False)}.items():
            with self.subTest(case=case):
                first = _attempt(1, 100, install="failure", pypi="skipped")
                second = _attempt(2, 200, install=install, pypi="failure" if passes else "skipped")
                server = self._serve(first + second)
                proc = self._find(server, self.tmp_path / case)
                if passes:
                    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                    self.assertEqual(_outputs(self.tmp_path / case), {"version": "9.9.9", "run-id": "4242"})
                    self.assertIn("release run 4242: Publish to TestPyPI concluded success in the latest attempt (2)", proc.stdout)
                    self.assertIn(f"release run 4242: {INSTALL_NAME} concluded success in the latest attempt (2)", proc.stdout)
                else:
                    self.assertEqual(proc.returncode, 1)
                    self.assertIn(f"  {INSTALL_NAME}: failure (attempt 2)", proc.stdout)
                    self.assertEqual(_outputs(self.tmp_path / case), {})

    def test_the_highest_attempt_wins_in_whatever_order_the_listing_gives(self) -> None:
        # GitHub does not document the order of filter=all: the step takes each job's record with the highest
        # (run_attempt, id), not the first or the last one listed.
        for newest_first in (False, True):
            for first, second, passes in (("success", "failure", False), ("failure", "success", True)):
                case = f"{'newest' if newest_first else 'oldest'}-first-{second}-second"
                with self.subTest(case=case):
                    records = _attempt(1, 100, testpypi=first, install="success" if first == "success" else "skipped", pypi="skipped") + _attempt(2, 200, testpypi=second, install="success" if second == "success" else "skipped", pypi="skipped")
                    server = self._serve(list(reversed(records)) if newest_first else records)
                    proc = self._find(server, self.tmp_path / case)
                    self.assertIs(proc.returncode == 0, passes, proc.stdout + proc.stderr)
                    if not passes:
                        self.assertIn("  Publish to TestPyPI: failure (attempt 2)", proc.stdout)

    def test_a_release_run_whose_build_failed_so_both_testpypi_jobs_were_skipped_is_refused(self) -> None:
        # A skipped TestPyPI job never ran its check. GitHub records it as completed, with the conclusion "skipped".
        records = [_job(100, "Build and Validate", "failure"), _job(101, "Publish to TestPyPI", "skipped"), _job(102, INSTALL_NAME, "skipped"), _job(103, "Publish to PyPI", "skipped"), _job(104, REPUBLISH_NAME, "skipped")]
        server = self._serve(records)
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("  Publish to TestPyPI: skipped (attempt 1)", proc.stdout)
        self.assertIn(f"  {INSTALL_NAME}: skipped (attempt 1)", proc.stdout)
        self.assertEqual(_outputs(self.tmp_path / "case"), {})

    def test_an_older_release_run_that_passed_does_not_vouch_for_a_newer_one_that_failed(self) -> None:
        # Ruling 1 reads the tag's NEWEST release run: a Release published again starts another run, which TestPyPI then
        # refuses, and from then on the tag has no run that vouches for its files.
        runs = [{"id": 4243, "head_branch": "v9.9.9"}, {"id": 4242, "head_branch": "v9.9.9"}]
        server = self.stand(
            {
                _runs_path("v9.9.9"): [(200, {"workflow_runs": runs})],
                _jobs_path(4243): [_listing(*_attempt(1, 300, testpypi="failure", install="skipped", pypi="skipped"))],
                _jobs_path(4242): [_listing(*_attempt(1, 100))],
                _artifacts_path(4242): [(200, {"artifacts": LIVE_ARTIFACT})],
            }
        )
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("  Publish to TestPyPI: failure (attempt 1)", proc.stdout)
        self.assertNotIn(_jobs_path(4242), server.paths())
        self.assertEqual(_outputs(self.tmp_path / "case"), {})

    def test_a_testpypi_job_that_failed_and_then_passed_on_a_re_run_counts_as_passed(self) -> None:
        rerun = [_job(201, "Publish to TestPyPI", "success", attempt=2), _job(202, INSTALL_NAME, "success", attempt=2), _job(203, "Publish to PyPI", "failure", attempt=2)]
        server = self._serve(_attempt(1, 100, testpypi="failure", install="skipped", pypi="skipped") + rerun)
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path / "case"), {"version": "9.9.9", "run-id": "4242"})

    def test_re_run_all_jobs_whose_second_attempt_failed_is_refused_although_the_first_passed(self) -> None:
        server = self._serve(_attempt(1, 100) + _attempt(2, 200, testpypi="failure", install="skipped", pypi="skipped"))
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("  Publish to TestPyPI: failure (attempt 2)", proc.stdout)
        self.assertEqual(_outputs(self.tmp_path / "case"), {})

    def test_the_latest_attempt_is_read_across_every_page_of_the_listing(self) -> None:
        # 105 records: 95 other jobs and attempt 1, whose upload failed, on page 1; attempt 2, all green, on page 2.
        page_1 = [_job(1000 + i, f"Unrelated job {i}", "success") for i in range(95)] + _attempt(1, 100, testpypi="failure", install="skipped", pypi="skipped")
        server = self._serve([])
        server.routes[_jobs_path(4242, 1)] = [_listing(*page_1, total=105)]
        server.routes[_jobs_path(4242, 2)] = [_listing(*_attempt(2, 200), total=105)]
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(_jobs_path(4242, 2), server.paths())
        self.assertEqual(_outputs(self.tmp_path / "case"), {"version": "9.9.9", "run-id": "4242"})

    def test_a_release_run_without_a_testpypi_job_is_refused(self) -> None:
        server = self._serve([_job(100, "Build and Validate", "success"), _job(101, "Publish to PyPI", "failure")])
        proc = self._find(server, self.tmp_path / "case")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("the run has no such job", proc.stdout)
        self.assertEqual(_outputs(self.tmp_path / "case"), {})

    def test_a_sub_package_tag_names_its_version(self) -> None:
        tag = "juniper-ci-tools-v1.2.3"
        server = self._serve(_attempt(1, 100), artifacts=[], tag=tag, workflow="publish-ci-tools.yml", package="juniper-ci-tools")
        case = self.tmp_path / "case"
        proc = _run(_script(FIND, self.tmp_path), self.workspace(), env={"PUBLISH_PACKAGE": "juniper-ci-tools", "PUBLISH_TAG_PREFIX": "juniper-ci-tools-v", **self._env(case, server, tag=tag, workflow="publish-ci-tools.yml")})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(case), {"version": "1.2.3", "run-id": ""})
        self.assertIn("::warning::", proc.stdout)

    def test_it_refuses_anything_but_a_release_tag_of_this_package(self) -> None:
        cases = {"branch-named-like-a-tag": ("v9.9.9", "branch"), "branch": ("main", "branch"), "another-packages-tag": ("juniper-ci-tools-v1.2.3", "tag"), "a-package-named-tag-in-the-meta-publisher": ("juniper-ml-v9.9.9", "tag"), "a-prefix-without-a-version": ("v", "tag")}
        for case, (tag, ref_type) in cases.items():
            with self.subTest(case=case):
                server = self.stand({})
                proc = self._find(server, self.tmp_path / case, tag=tag, ref_type=ref_type)
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                self.assertEqual(server.requests, [])
                self.assertEqual(_outputs(self.tmp_path / case), {})

    def test_a_sub_package_publisher_refuses_every_tag_but_its_own_prefix(self) -> None:
        for case, tag in {"the-meta-packages-v-tag": "v1.2.3", "a-sibling-sub-packages-tag": "juniper-doc-tools-v1.2.3", "a-tag-without-the-v": "juniper-ci-tools-1.2.3"}.items():
            with self.subTest(case=case):
                server = self.stand({})
                case_dir = self.tmp_path / case
                proc = _run(_script(FIND, self.tmp_path), self.workspace(f"workspace-{case}"), env={"PUBLISH_PACKAGE": "juniper-ci-tools", "PUBLISH_TAG_PREFIX": "juniper-ci-tools-v", **self._env(case_dir, server, tag=tag, workflow="publish-ci-tools.yml")})
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                # Refused before any request: a sub-package's republish never reads the release run of another package's tag.
                self.assertEqual(server.requests, [])
                self.assertEqual(_outputs(case_dir), {})

    def test_an_api_failure_fails_the_job_rather_than_skip_the_check(self) -> None:
        for failing in ("runs", "jobs", "artifacts"):
            with self.subTest(failing=failing):
                server = self._serve(_attempt(1, 100))
                server.routes[{"runs": _runs_path("v9.9.9"), "jobs": _jobs_path(4242), "artifacts": _artifacts_path(4242)}[failing]] = [(502, {"message": "bad gateway"})]
                proc = self._find(server, self.tmp_path / failing)
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(_outputs(self.tmp_path / failing), {})


class TestFetchTestPyPIFiles(_Scratch):
    @staticmethod
    def _env(server: _Stand, sums: Path) -> dict[str, str]:
        return {"INDEX_URL": server.url, "VERSION": "9.9.9", "RELEASE_RUN_SUMS": str(sums)}

    @staticmethod
    def _routes(server_url: str, files: dict[str, bytes], digests: dict[str, str] | None = None) -> dict[str, list[tuple[int, object]]]:
        listed = digests or {name: _sha(data) for name, data in files.items()}
        routes: dict[str, list[tuple[int, object]]] = {JSON_PATH: [(200, _release(listed, base=server_url))]}
        for name, data in files.items():
            routes[f"/files/{name}"] = [(200, data)]
        return routes

    def _serve(self, files: dict[str, bytes], digests: dict[str, str] | None = None) -> _Stand:
        server = self.stand({})
        server.routes.update(self._routes(server.url, files, digests))
        return server

    def _root(self, name: str = "fresh") -> Path:
        root = self.tmp_path / name
        root.mkdir()
        return root

    def test_it_downloads_testpypis_files_and_records_them(self) -> None:
        root = self._root()
        server = self._serve(BUILT)
        proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, self.tmp_path / "absent" / "SHA256SUMS"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in (root / "dist").iterdir()}, BUILT)
        self.assertEqual((root / "SHA256SUMS").read_text(encoding="utf-8"), "".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items())))
        self.assertIn("::warning::", proc.stdout)

    def test_a_file_whose_bytes_differ_from_the_index_json_is_refused(self) -> None:
        root = self._root()
        server = self._serve({**BUILT, WHEEL: b"tampered bytes"}, digests=SERVED)
        proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, self.tmp_path / "absent" / "SHA256SUMS"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("hashes to", proc.stdout)
        self.assertFalse((root / "SHA256SUMS").exists())

    def test_the_release_runs_sha256sums_is_checked_while_it_exists(self) -> None:
        root = self._root()
        sums = self.tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text("".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items())), encoding="utf-8")
        server = self._serve(BUILT)
        proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, sums))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("::warning::", proc.stdout)

    def test_testpypi_files_the_release_run_did_not_build_are_refused(self) -> None:
        root = self._root()
        sums = self.tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text(f"{_sha(b'the first build')}  {WHEEL}\n{_sha(BUILT[SDIST])}  {SDIST}\n", encoding="utf-8")
        server = self._serve(BUILT)
        proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, sums))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("disagree", proc.stdout)
        self.assertEqual([p for p, _ in server.requests if p.startswith("/files/")], [])

    def test_testpypi_and_the_release_runs_sha256sums_must_name_the_same_files(self) -> None:
        # A file one of them names and the other does not is refused, in either direction, before any file is fetched.
        extra = "juniper_ml-9.9.9-py2.py3-none-any.whl"
        for which in ("the-release-run-lists-more", "testpypi-lists-more"):
            with self.subTest(which=which):
                root = self._root(which)
                recorded = dict(SERVED) | ({extra: _sha(b"another wheel")} if which == "the-release-run-lists-more" else {})
                served = dict(BUILT) | ({extra: b"another wheel"} if which == "testpypi-lists-more" else {})
                sums = self.tmp_path / f"release-run-{which}" / "SHA256SUMS"
                sums.parent.mkdir()
                sums.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(recorded.items())), encoding="utf-8")
                server = self._serve(served)
                proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, sums))
                self.assertEqual(proc.returncode, 1)
                self.assertIn("disagree", proc.stdout)
                self.assertEqual([p for p, _ in server.requests if p.startswith("/files/")], [])

    def test_an_index_listing_it_cannot_vouch_for_is_refused(self) -> None:
        cases = {"no-files": {}, "another-package": {**SERVED, "juniper_ci_tools-9.9.9-py3-none-any.whl": "d" * 64}, "another-version": {**SERVED, "juniper_ml-9.9.8.tar.gz": "d" * 64}}
        for case, listed in cases.items():
            with self.subTest(case=case):
                root = self._root(case)
                server = self.stand({})
                server.routes[JSON_PATH] = [(200, _release(listed, base=server.url))]
                proc = _run(_script(FETCH, self.tmp_path), root, env=self._env(server, self.tmp_path / "absent" / "SHA256SUMS"))
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                self.assertEqual([p for p, _ in server.requests if p.startswith("/files/")], [])

    def test_it_refuses_a_dist_directory_that_already_holds_files(self) -> None:
        workspace = self.workspace()
        server = self._serve(BUILT)
        proc = _run(_script(FETCH, self.tmp_path), workspace, env=self._env(server, self.tmp_path / "absent" / "SHA256SUMS"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(server.requests, [])


if __name__ == "__main__":
    unittest.main()
'''
EMBED_TEST_PUBLISH_DOCS_BOUNDS = r'''#!/usr/bin/env python3
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
'''

#: R4-1 of the sweep's review (MAJOR): the verify step is looked up in the job named `Verify the TestPyPI install`, a
#: step or workflow not found is a failure (never a skip), and the TestPyPI job's permissions are `id-token: write`
#: alone. R5-F5: the lag pin (old line 477) moves to the template's lag error. The rehearsal runs from the runner's
#: two directories, set by the test, under `bash -e`, and gains the flag-form fetch's retry and lag cases.
TESTPYPI_VERIFY_EDITS = [
    (
        r'''This unittest:
  1. Structurally pins both phases: the download phase's TestPyPI-only index +
     ``--no-deps`` + exact ``==${VERSION}``, the three install phases' PyPI-only index
     + local-wheel target + extras + absence of ``--no-deps``, the tomllib version read,
     no ``skip-existing`` on either upload (the one-artifact publish), the ``pypi needs: testpypi``
     gate, and the ``v*`` release-tag guard.
''',
        r'''Since the one-artifact template's sweep (juniper-cascor#777; ruling 2 of 2026-11-16) the verify runs in a job of
its own, ``Verify the TestPyPI install`` (``contents: read`` alone, from ``$RUNNER_TEMP``), which the PyPI job needs
as well as the TestPyPI job. A verify this module cannot find is a failure, never a skip: a skipped pin is no pin.

This unittest:
  1. Structurally pins both phases: the download phase's TestPyPI-only index +
     ``--no-deps`` + exact ``==${VERSION}``, the three install phases' PyPI-only index
     + local-wheel target + extras + absence of ``--no-deps``, the tomllib version read
     under ``$GITHUB_WORKSPACE``, no ``skip-existing`` on either upload (the one-artifact
     publish), the PyPI job needing both TestPyPI jobs, and the ``v*`` release-tag guard.
''',
    ),
    (
        r'''  3. Extracts the verify shell and runs it hermetically with PATH stubs for
     ``sleep`` / ``mktemp`` / ``pip`` / ``python`` so a rewrite that drops a phase, swaps
     the index URLs, or stops walking extras fails in CI without hitting the network --
     including a negative arm proving the missing-wheel guard aborts before any install.
''',
        r'''  3. Extracts the verify shell and runs it hermetically, under ``bash -e`` as the runner
     does, with PATH stubs for ``sleep`` / ``mktemp`` / ``pip`` / ``python`` so a rewrite
     that drops a phase, swaps the index URLs, or stops walking extras fails in CI without
     hitting the network -- including a negative arm proving the missing-wheel guard aborts
     before any install, and the provenance fetch's retry and its lag error.
''',
    ),
    (
        'VERIFY_STEP_NAME = "Verify TestPyPI install"\n',
        'VERIFY_STEP_NAME = "Verify TestPyPI install"\n#: The verify\'s own job since the one-artifact sweep (ruling 2 of 2026-11-16): its id, and the name it is found by.\nINSTALL_JOB = "verify-testpypi-install"\nINSTALL_JOB_NAME = "Verify the TestPyPI install"\n#: The template\'s lag error, after the provenance fetch\'s tenth failed try (R5-F5 of the sweep\'s review).\nLAG_ERROR = "is not installable from TestPyPI after 10 tries (index lag?): Re-run failed jobs; a real failure repeats"\n',
    ),
    (
        r'''def _verify_step_run(doc: dict) -> str:
    steps = (doc.get("jobs") or {}).get("testpypi", {}).get("steps") or []
    step = next((s for s in steps if s.get("name") == VERIFY_STEP_NAME), None)
    if step is None or "run" not in step:
        raise unittest.SkipTest(f"could not locate {VERIFY_STEP_NAME!r} in {WORKFLOW_NAME}")
    return step["run"]
''',
        r'''def _verify_step_run(doc: dict) -> str:
    """The verify's script: the one step named VERIFY_STEP_NAME in the one job named INSTALL_JOB_NAME.

    Since the one-artifact sweep the verify runs in a job of its own, not in the TestPyPI job. Not finding it is a
    failure, never a skip: a skipped pin is no pin.
    """
    jobs = [job for job in (doc.get("jobs") or {}).values() if isinstance(job, dict) and job.get("name") == INSTALL_JOB_NAME]
    if len(jobs) != 1:
        raise AssertionError(f"expected one job named {INSTALL_JOB_NAME!r} in {WORKFLOW_NAME}, found {len(jobs)}")
    steps = [s for s in jobs[0].get("steps") or [] if s.get("name") == VERIFY_STEP_NAME and "run" in s]
    if len(steps) != 1:
        raise AssertionError(f"expected one {VERIFY_STEP_NAME!r} step in {INSTALL_JOB_NAME!r} of {WORKFLOW_NAME}, found {len(steps)}")
    return steps[0]["run"]
''',
    ),
    (
        r'''        if not cls.workflow_path.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {cls.workflow_path}")
''',
        r'''        if not cls.workflow_path.is_file():
            raise AssertionError(f"{WORKFLOW_NAME} not present at {cls.workflow_path}: a missing publisher fails, it is never skipped")
''',
    ),
    (
        '        for name in ("build", "testpypi", "pypi"):\n',
        '        for name in ("build", "testpypi", INSTALL_JOB, "pypi"):\n',
    ),
    (
        r'''        self.assertIn("startsWith(github.event.release.tag_name, 'v')", build_if)
''',
        r'''        self.assertIn("startsWith(github.event.release.tag_name, 'v')", build_if)
        # A dispatch builds only from a `v` tag: from a sub-package's tag it would publish the meta-package's files.
        self.assertIn("startsWith(github.ref_name, 'v')", build_if)
''',
    ),
    (
        r'''    def test_pypi_needs_testpypi(self) -> None:
        needs = self.doc["jobs"]["pypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertIn("testpypi", needs, "PyPI publish must wait on TestPyPI verify (Gate 1).")
''',
        r'''    def test_pypi_needs_testpypi(self) -> None:
        # Both TestPyPI jobs: the upload with its sha256 checks, and the verify (Gate 1), which runs in a job of its own.
        needs = self.doc["jobs"]["pypi"].get("needs")
        needs = [needs] if isinstance(needs, str) else (needs or [])
        self.assertEqual(needs, ["testpypi", INSTALL_JOB], "PyPI publish must wait on the TestPyPI upload and its verify (Gate 1).")
        self.assertEqual(self.doc["jobs"][INSTALL_JOB].get("needs"), "testpypi", "the verify must run after the TestPyPI upload's sha256 check")
''',
    ),
    (
        r'''        self.assertIn("['project']['version']", self.script)
''',
        r'''        self.assertIn("['project']['version']", self.script)
        # Read under the workspace: the verify runs from $RUNNER_TEMP, outside the sparse checkout that holds the file.
        self.assertIn("open('${GITHUB_WORKSPACE}/pyproject.toml','rb')", self.script)
        self.assertEqual(_command_lines(self.script)[0], 'cd "${RUNNER_TEMP}"')
''',
    ),
    (
        r'''        own: the build ``contents: read`` and ``actions: read`` (its reuse step
        lists the run's artifacts), the TestPyPI job ``contents: read`` for its
        checkout, the PyPI job, which checks nothing out, ``id-token: write``
        alone, and the republish job ``actions: read`` for the release run's
        artifact.
        """
''',
        r'''        own: the build ``contents: read`` and ``actions: read`` (its reuse step
        lists the run's artifacts), the TestPyPI job, which checks nothing out
        since the one-artifact sweep, and the PyPI job ``id-token: write``
        alone, the verify's own job ``contents: read`` alone, for its sparse
        checkout, and the republish job ``actions: read`` for the release run's
        artifact.
        """
''',
    ),
    (
        '            "testpypi": {"id-token": "write", "contents": "read"},\n            "pypi": {"id-token": "write"},\n',
        '            "testpypi": {"id-token": "write"},\n            INSTALL_JOB: {"contents": "read"},\n            "pypi": {"id-token": "write"},\n',
    ),
    (
        r'''        if not wf.is_file():
            raise unittest.SkipTest(f"{WORKFLOW_NAME} not present at {wf}")
''',
        r'''        if not wf.is_file():
            raise AssertionError(f"{WORKFLOW_NAME} not present at {wf}: a missing publisher fails, it is never skipped")
''',
    ),
    (
        r'''        self._write_exec(bindir / "pip", f'#!/bin/bash\nprintf "%s\\n" "$*" >> "{pip_log}"\n{make_wheel}exit 0\n')
''',
        r'''        # A `pip download` fails while the downloads so far, this one included, number STUB_DOWNLOAD_FAILURES or fewer.
        fail_download = f'if [[ "$1" == \'download\' ]] && [ "$(grep -c \'^download\' "{pip_log}")" -le "${{STUB_DOWNLOAD_FAILURES:-0}}" ]; then exit 1; fi\n'
        self._write_exec(bindir / "pip", f'#!/bin/bash\nprintf "%s\\n" "$*" >> "{pip_log}"\n{fail_download}{make_wheel}exit 0\n')
''',
    ),
    (
        r'''    def _run_verify(self, *, create_wheel: bool = True) -> tuple[int, list[str], str]:
''',
        r'''    def _run_verify(self, *, create_wheel: bool = True, download_failures: int = 0) -> tuple[int, list[str], str]:
''',
    ),
    (
        r'''            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            # Keep cwd at the temp tree (script opens pyproject.toml relative to CWD).
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
                ["bash", str(script_path)],
''',
        r'''            (tdp / "runner-temp").mkdir()
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            # The runner's own two directories: the verify reads pyproject.toml under GITHUB_WORKSPACE and runs from
            # RUNNER_TEMP. Set here, so a CI runner's own values never reach the rehearsal.
            env["GITHUB_WORKSPACE"] = str(tdp)
            env["RUNNER_TEMP"] = str(tdp / "runner-temp")
            env["STUB_DOWNLOAD_FAILURES"] = str(download_failures)
            # As the runner runs a `run:` without a `shell:`: bash -e.
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
                ["bash", "-e", str(script_path)],
''',
    ),
    (
        r'''        self.assertIn("::error::", out)

    def test_sleep_is_invoked_but_stubbed_not_blocking(self) -> None:
''',
        r'''        self.assertIn("::error::", out)

    def test_a_failed_fetch_is_retried_and_the_verify_goes_on_once_one_succeeds(self) -> None:
        # The flag-form fetch (`pip download ... && { FETCHED=1; break; }`): a failed try does not stop the step under
        # `bash -e`, and needs no `set +e`; the try that succeeds ends the loop.
        rc, lines, out = self._run_verify(download_failures=2)
        self.assertEqual(rc, 0, out)
        self.assertEqual([ln.split()[0] for ln in lines], ["download"] * 3 + ["install"] * 3)

    def test_index_lag_that_outlasts_every_try_fails_with_the_templates_lag_error(self) -> None:
        rc, lines, out = self._run_verify(download_failures=10)
        self.assertEqual(rc, 1, out)
        self.assertEqual(len(lines), 10, lines)
        self.assertTrue(all(ln.startswith("download ") for ln in lines), lines)
        self.assertIn(f"::error::juniper-ml {REHEARSAL_VERSION} {LAG_ERROR}", out)

    def test_sleep_is_invoked_but_stubbed_not_blocking(self) -> None:
''',
    ),
    (
        r'''        # A failure to ever fetch must be a real error, never a silent fall-through
        # into the install phases with an empty download dir.
        self.assertIn("never served", self.script)
''',
        r'''        # A failure to ever fetch must be a real error, never a silent fall-through
        # into the install phases with an empty download dir: the template's lag
        # error, the operator signature the docs quote (R5-F5 of the sweep's review).
        self.assertIn(f'echo "::error::juniper-ml ${{VERSION}} {LAG_ERROR}"', _command_lines(self.script))
''',
    ),
]

#: R4-1 for the six sub-package publishers: the verify step is looked up in the job named `Verify the TestPyPI install`,
#: a step or workflow not found is a failure, the TestPyPI job holds `id-token: write` alone, and the rehearsal sets the
#: runner's two directories. R4-5: a metadata check must also find the package.
SUBPACKAGE_EDITS = [
    (
        r'''This unittest:
  1. Structurally pins the shared contracts across all six ``publish-*.yml`` files.
''',
        r'''Since the one-artifact template's sweep (juniper-cascor#777; ruling 2 of 2026-11-16) each Verify-install step runs
in a job of its own, ``Verify the TestPyPI install`` (``contents: read`` alone, from ``$RUNNER_TEMP``), which the PyPI
job needs as well as the TestPyPI job. A step this module cannot find, or a workflow it cannot read, is a failure,
never a skip: a skipped pin is no pin.

This unittest:
  1. Structurally pins the shared contracts across all six ``publish-*.yml`` files.
''',
    ),
    (
        r'''def _verify_step_run(doc: dict) -> tuple[str, str]:
    # The install check, by name: the one-artifact template's own "Verify ..." steps run Python before it.
    steps = (doc.get("jobs") or {}).get("publish-testpypi", {}).get("steps") or []
    step = next((s for s in steps if str(s.get("name") or "").startswith("Verify install from TestPyPI") and "run" in s), None)
    if step is None:
        raise unittest.SkipTest("could not locate Verify install step in publish-testpypi")
    return str(step["name"]), step["run"]
''',
        r'''#: The install check's own job since the one-artifact sweep (ruling 2 of 2026-11-16): its id, and the name it is found by.
INSTALL_JOB = "verify-testpypi-install"
INSTALL_JOB_NAME = "Verify the TestPyPI install"


def _verify_step_run(doc: dict) -> tuple[str, str]:
    """The install check, by name, in the one job named INSTALL_JOB_NAME, where it runs since the one-artifact sweep.

    Not finding it is a failure, never a skip: a skipped pin is no pin.
    """
    jobs = [job for job in (doc.get("jobs") or {}).values() if isinstance(job, dict) and job.get("name") == INSTALL_JOB_NAME]
    if len(jobs) != 1:
        raise AssertionError(f"expected one job named {INSTALL_JOB_NAME!r}, found {len(jobs)}")
    steps = [s for s in jobs[0].get("steps") or [] if str(s.get("name") or "").startswith("Verify install from TestPyPI") and "run" in s]
    if len(steps) != 1:
        raise AssertionError(f"expected one Verify install step in {INSTALL_JOB_NAME!r}, found {len(steps)}")
    return str(steps[0]["name"]), steps[0]["run"]
''',
    ),
    (
        r'''            path = cls.workflows_dir / f"publish-{suffix}.yml"
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.name}")
''',
        r'''            path = cls.workflows_dir / f"publish-{suffix}.yml"
            if not path.is_file():
                raise AssertionError(f"missing {path.name}: a missing publisher fails, it is never skipped")
''',
    ),
    (
        r'''            path = cls.repo_root / ".github" / "workflows" / f"publish-{suffix}.yml"
            if not path.is_file():
                raise unittest.SkipTest(f"missing {path.name}")
''',
        r'''            path = cls.repo_root / ".github" / "workflows" / f"publish-{suffix}.yml"
            if not path.is_file():
                raise AssertionError(f"missing {path.name}: a missing publisher fails, it is never skipped")
''',
    ),
    (
        r'''        (its reuse step lists the run's artifacts), the TestPyPI job
        ``contents: read`` for its sparse checkout, the PyPI job, which checks
        nothing out, ``id-token: write`` alone, and the republish job
        ``actions: read`` for the release run's artifact.
        """
        expected = {
            "build": {"contents": "read", "actions": "read"},
            "publish-testpypi": {"id-token": "write", "contents": "read"},
            "publish-pypi": {"id-token": "write"},
''',
        r'''        (its reuse step lists the run's artifacts), the TestPyPI job, which
        checks nothing out since the one-artifact sweep, and the PyPI job
        ``id-token: write`` alone, the install check's own job
        ``contents: read`` alone, for its sparse checkout, and the republish job
        ``actions: read`` for the release run's artifact.
        """
        expected = {
            "build": {"contents": "read", "actions": "read"},
            "publish-testpypi": {"id-token": "write"},
            INSTALL_JOB: {"contents": "read"},
            "publish-pypi": {"id-token": "write"},
''',
    ),
    (
        r'''                expected = f"startsWith(github.event.release.tag_name, '{pkg}-v')"
                self.assertIn(expected, build_if)
''',
        r'''                expected = f"startsWith(github.event.release.tag_name, '{pkg}-v')"
                self.assertIn(expected, build_if)
                # A dispatch builds only from this package's own tag: another tag's would publish this package under it.
                self.assertIn(f"startsWith(github.ref_name, '{pkg}-v')", build_if)
''',
    ),
    (
        r'''                self.assertIn("build", needs_tp)
                self.assertIn("publish-testpypi", needs_py)
''',
        r'''                self.assertIn("build", needs_tp)
                # The PyPI job needs both TestPyPI jobs: the upload with its checks, and the install check after it.
                self.assertEqual(needs_py, ["publish-testpypi", INSTALL_JOB])
                self.assertEqual((jobs.get(INSTALL_JOB) or {}).get("needs"), "publish-testpypi")
''',
    ),
    (
        r'''                if pkg == "juniper-model-core":
                    self.assertIn("juniper-model-core/juniper_model_core/_version.py", script)
                    self.assertIn("__version__", script)
                else:
                    self.assertIn(f"{pkg}/pyproject.toml", script)
                    self.assertIn("grep '^version'", script)
                # Post-install must prove the package landed — either importlib.metadata
                # (deps-heavy packages that cannot import under --no-deps) or a direct import.
                has_metadata = "importlib.metadata" in script and f"m.version('{pkg}')" in script
                has_import = f"import {pkg.replace('-', '_')}" in script
                self.assertTrue(
                    has_metadata or has_import,
                    f"{pkg}: verify must prove install via importlib.metadata or package import",
                )
''',
        r'''                # Read under $GITHUB_WORKSPACE: the check runs from $RUNNER_TEMP, outside the sparse checkout.
                if pkg == "juniper-model-core":
                    self.assertIn('"${GITHUB_WORKSPACE}/juniper-model-core/juniper_model_core/_version.py"', script)
                    self.assertIn("__version__", script)
                else:
                    self.assertIn(f'"${{GITHUB_WORKSPACE}}/{pkg}/pyproject.toml"', script)
                    self.assertIn("grep '^version'", script)
                # Post-install must prove the package landed: a direct import, or, for the deps-heavy packages that
                # cannot import under --no-deps, importlib.metadata AND importlib.util.find_spec. Metadata alone passes
                # a wheel that lacks the package (R4-5 of the one-artifact sweep's review), so the metadata check must
                # also find it, with an origin, and fail through SystemExit, which PYTHONOPTIMIZE keeps. Read from the
                # commands alone: a comment may name an import that never runs.
                module = pkg.replace("-", "_")
                commands = "\n".join(ln.strip() for ln in script.splitlines() if ln.strip() and not ln.strip().startswith("#"))
                has_metadata = "importlib.metadata" in commands and f"m.version('{pkg}')" in commands
                has_import = f"import {module}" in commands
                self.assertTrue(
                    has_metadata or has_import,
                    f"{pkg}: verify must prove install via importlib.metadata or package import",
                )
                if has_metadata and not has_import:
                    self.assertIn(f"u.find_spec('{module}')", commands, f"{pkg}: a metadata check must also find the package")
                    self.assertIn("raise SystemExit(0 if origin else", commands)
                    self.assertNotIn("assert ", commands)
''',
    ),
    (
        r'''            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
''',
        r'''            (tdp / "runner-temp").mkdir()
            env = RedactedEnv(os.environ)
            env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
            # The runner's own two directories: each verify reads its version under GITHUB_WORKSPACE and runs from
            # RUNNER_TEMP. Set here, so a CI runner's own values never reach the rehearsal.
            env["GITHUB_WORKSPACE"] = str(tdp)
            env["RUNNER_TEMP"] = str(tdp / "runner-temp")
            proc = subprocess.run(  # nosec B603,B607 - workflow's own shell, fixed argv
''',
    ),
]


def apply_edits(text: str, edits: "list[tuple[str, str]]", where: str) -> str:
    for old, new in edits:
        text = replace_once(text, old, new, where)
    return text


def test_edits(read) -> "dict[str, str]":
    """The four test modules: the one-artifact module whole (over its base only), the docs-bounds module new, and the
    two suites R4-1 retargets."""
    out: dict[str, str] = {}
    base = read(ONE_ARTIFACT_TEST)
    if sha256(base) != BASE_ONE_ARTIFACT_SHA256:
        raise Refused(f"{ONE_ARTIFACT_TEST} hashes to {sha256(base)}, not the base this port was derived from ({BASE_ONE_ARTIFACT_SHA256}): main moved it, so re-derive the module rather than overwrite that change")
    out[ONE_ARTIFACT_TEST] = EMBED_TEST_PUBLISH_ONE_ARTIFACT
    try:
        read(DOCS_BOUNDS_TEST)
    except Refused:
        out[DOCS_BOUNDS_TEST] = EMBED_TEST_PUBLISH_DOCS_BOUNDS
    else:
        raise Refused(f"{DOCS_BOUNDS_TEST} exists already: main added it, so re-derive this port")
    out[TESTPYPI_VERIFY_TEST] = apply_edits(read(TESTPYPI_VERIFY_TEST), TESTPYPI_VERIFY_EDITS, TESTPYPI_VERIFY_TEST)
    out[SUBPACKAGE_TEST] = apply_edits(read(SUBPACKAGE_TEST), SUBPACKAGE_EDITS, SUBPACKAGE_TEST)
    for rel in (TESTPYPI_VERIFY_TEST, SUBPACKAGE_TEST):
        if "SkipTest" in out[rel]:
            raise Refused(f"{rel}: a SkipTest is left: R4-1 makes every not-found a failure")
    return out


def check_test_digests(test_text: str, template: str) -> None:
    """The digests the one-artifact module pins are the template's blocks' and republish job's, each normalized."""
    pinned = dict(re.findall(r'^    "([^"\n]+/[^"\n]+)": "([0-9a-f]{64})",$', test_text, flags=re.MULTILINE))
    want = {key: sha256(normalized(block)) for key, block in block_texts(template, "the template").items()}
    if pinned != want:
        raise Refused(f"{ONE_ARTIFACT_TEST}: its CASCOR_TEMPLATE_SHA256 is not the template's normalized blocks: {sorted(set(pinned.items()) ^ set(want.items()))}")
    republish = re.search(r'^CASCOR_REPUBLISH_SHA256 = "([0-9a-f]{64})"$', test_text, flags=re.MULTILINE)
    if not republish or republish.group(1) != sha256(normalized(template[republish_start(template, "the template") :])):
        raise Refused(f"{ONE_ARTIFACT_TEST}: its CASCOR_REPUBLISH_SHA256 is not the template's normalized republish job")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# CI wiring, AGENTS.md's suite count, and the docs
# ─────────────────────────────────────────────────────────────────────────────────────────────
CI = ".github/workflows/ci.yml"
MAIN_VERIFY = ".github/workflows/main-verify.yml"
AGENTS = "AGENTS.md"
REFERENCE = "docs/REFERENCE.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
CHANGELOG = "CHANGELOG.md"
PROCEDURE = "notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md"
MANUAL = "https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md"
LADDER = "(REFERENCE.md#one-artifact-and-recovering-a-release-that-did-not-reach-pypi)"
ONE_ARTIFACT_RUN = "          python3 -m unittest -v tests/test_publish_one_artifact.py\n"
CI_ONE_ARTIFACT_COMMENT_OLD = "          # PyPI's after; no skip-existing; id-token only on the uploading jobs; and the\n          # republish job, rung 1 of the recovery ladder. Every template step is byte-identical\n"
CI_ONE_ARTIFACT_COMMENT_NEW = "".join(
    (
        "          # PyPI's after; no skip-existing; id-token only on the uploading jobs; the install\n",
        "          # check in a job of its own that cannot mint (ruling 2 of 2026-11-16); and the\n",
        "          # republish job, rung 1 of the recovery ladder, which refuses unless the tag's\n",
        "          # newest release run passed its TestPyPI jobs (ruling 1). Every template block is byte-identical\n",
    )
)
CI_DOCS_BOUNDS = "".join(
    (
        "          # tests/test_publish_docs_bounds.py: the install checks' bounds the docs state (the tries,\n",
        "          # the wait between them, the lag error after the last) are the bounds the seven publishers'\n",
        "          # steps run (the port of juniper-cascor#777's docs pins; a module of its own, since the\n",
        "          # one-artifact module reads the workflows alone). PyYAML (installed above).\n",
        "          python3 -m unittest -v tests/test_publish_docs_bounds.py\n",
    )
)


def replace_line(text: str, prefix: str, new: str, where: str, holds: "tuple[str, ...]" = ()) -> str:
    """Replace the one whole line that starts with PREFIX (and holds each of HOLDS) by NEW, which ends in a newline."""
    lines = text.splitlines(keepends=True)
    found = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(found) != 1:
        raise Refused(f"{where}: {len(found)} lines start with {prefix[:80]!r}, expected 1")
    if not all(part in lines[found[0]] for part in holds):
        raise Refused(f"{where}: the line starting {prefix[:60]!r} no longer holds {[p for p in holds if p not in lines[found[0]]]}")
    if not new.endswith("\n"):
        raise Refused(f"{where}: a replacement line must end in a newline")
    lines[found[0]] = new
    return "".join(lines)


def bump_patch(version: str) -> str:
    head, _, patch = version.rpartition(".")
    return f"{head}.{int(patch) + 1}"


# ── docs/REFERENCE.md ───────────────────────────────────────────────────────────────────────
def reference_row(version: str, date: str, cases: int) -> str:
    text = " ".join(
        (
            "The one-artifact template's sweep (the port of juniper-cascor#777; rulings 1 and 2 of 2026-11-16):",
            "§ Meta-Package Publish Pipeline and § Independent Sibling Package Publish Pipelines describe the install check's own job",
            "(`Verify the TestPyPI install`, `contents: read` alone, from `$RUNNER_TEMP`; the PyPI job needs both TestPyPI jobs),",
            "the TestPyPI job's `id-token: write` alone, `PUBLISH_TAG_PREFIX` and each build guard's dispatch branch, the template's lag error,",
            "and the ladder's new facts (rung 1 refuses unless the tag's newest release run passed its TestPyPI jobs in their latest attempt;",
            "an index-lag failure is \"Re-run failed jobs\", a failed install check a new patch version; never a re-cut; a failed",
            "`Verify PyPI serves exactly these files` has two causes; the tags the ladder covers; rung 2 after a plain dispatch);",
            "the CI/CD Pipeline Reference, the workflow inventory, the Test Suite Reference",
            f"(`tests/test_publish_one_artifact.py`, {cases} cases; `tests/test_publish_testpypi_verify.py`; the new `tests/test_publish_docs_bounds.py`),",
            "[Running every suite](#running-every-suite) and the repository tree follow",
        )
    )
    return f"| {version:<7} | {date} | {text} |\n"


REF_TESTPYPI_VERIFY = "".join(
    (
        "  Pins the two-phase verify (TestPyPI-only `pip download --no-deps` provenance, then three PyPI-only local-wheel installs of bare / `[clients]` / `[tools]`, never `--extra-index-url`, never the heavy extras), the `v*` tag guard (a dispatch builds only from a `v` tag), no `skip-existing` on either upload (the one-artifact publish), the per-job permissions, and the PyPI job needing both TestPyPI jobs.\n",
        "  Since the one-artifact sweep (juniper-cascor#777) the verify runs in its own job, `Verify the TestPyPI install`, where this suite reads it; a verify it cannot find fails, never skips.\n",
    )
)
REF_TESTPYPI_POLL = "  Since juniper-ml#1310, the index-lag buffer is a **bounded poll** (no unconditional `sleep 30`; remaining `sleep` values are poll intervals `<=10s`; exhausting the loop is the template's lag error, not a silent fall-through, and a failed try is retried without `set +e`).\n"
REF_ONE_ARTIFACT = "".join(
    (
        "- `tests/test_publish_one_artifact.py` -- The one-artifact publish in all seven publishers (the port of juniper-cascor#763 / #767, swept by #777; the Overtoad's directive of 2026-11-15 and rulings 1 and 2 of 2026-11-16): PyPI takes exactly the files TestPyPI took, checked by sha256.\n",
        "  - Static cases pin, in every workflow: one build, in `Build and Validate`, with no environment and no `id-token`; the job chain, and the workflow name (`... to PyPI`) and job names `util/release_train/ceremony.py` reads; per-job permissions (only the uploading jobs mint OIDC; the TestPyPI job holds `id-token: write` alone and checks nothing out); each job's keys, runner and exact steps, with no `if:` beyond the template's and no `continue-on-error`; each build step's commands; the reuse step first, and every later build step skipped when it reuses; the dist check before every upload; TestPyPI's JSON after the TestPyPI upload, again before the PyPI upload, and PyPI's after; no `skip-existing` and no `attestations: false`; the `<pkg>-dist` artifact (dist directory and `SHA256SUMS`, kept exactly 90 days); `PUBLISH_TAG_PREFIX` agreeing with each build guard; and the republish job's trigger, gate, steps and name, which carries neither \"testpypi\" nor \"pypi\". Every `publish*.yml`, and every workflow that uploads to an index, must be one of the seven, so an eighth publisher cannot go unchecked.\n",
        "  - `TestInstallCheckJob` pins ruling 2: `Verify the TestPyPI install` needs the TestPyPI job, holds `contents: read` alone, sparse-checks out its version file without credentials, runs exactly its commands from `$RUNNER_TEMP`, cannot be switched off, and is needed by the PyPI job; ci-tools' and observability's metadata checks also find the package (`importlib.util.find_spec`, failing through `SystemExit`). `TestInstallCheckScript` runs each check's own shell under `bash -e` against stand-in `pip`, `python` and `sleep`, and the `find_spec` check against a real interpreter.\n",
        "  - `TestUnchanged` pins what each workflow kept: triggers, tag guards (a plain dispatch from the package's own tag still re-fires the whole publish), build commands and the tag assertion, `publish.yml`'s two-phase install check (now in the install job, with its setup-python 3.12) and `attestations: true`, and the sub-packages' concurrency, environment URLs, `verbose` uploads and sparse-checkout install check.\n",
        "  - `TestTemplate` holds every copy of a template step byte-identical to the others, and every template block and the republish job, comments included, to juniper-cascor's `publish.yml` at `5e3d9801` by sha256 once each `uses:` line is reduced to its action's name; each action is pinned to one ref across the seven files (juniper-ml's cross-repository checker pins the refs to the template's).\n",
        "  - The rehearsals run each template step's own Python, extracted from `publish.yml`, against a stand-in index, file host and GitHub API on 127.0.0.1, the republish job's refusal among them (ruling 1: the tag's newest release run, its TestPyPI jobs' latest attempt, across every page of the listing). Negative controls: `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py` (65 mutations of the first port, each caught) and the sweep port's mutation table (its pull request).\n",
        "- `tests/test_publish_docs_bounds.py` -- The install checks' bounds the docs state are the bounds the seven publishers run (the port of juniper-cascor#777's docs pins): `publish.yml`'s 10 attempts × 6s provenance poll and the sub-packages' 5×10s retry, with the waits each makes and their total, as this file and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` state them (read from each loop: a sub-package's check stops before its last wait, the meta-package's waits after every failed try), and each check's lag error after its last try, as this file quotes it. A module of its own: `tests/test_publish_one_artifact.py` reads the workflows alone. The docs state none of the JSON checks' bounds, so none is pinned.\n",
    )
)
REF_TREE_ONE_ARTIFACT = "│   ├── test_publish_one_artifact.py      # Structural + rehearsal: all 7 publishers build once, sha256-check every upload against SHA256SUMS + TestPyPI/PyPI JSON, reuse on re-run, the install check in a job that cannot mint, the republish job and its gate (cascor#763/#767/#777)\n│   ├── test_publish_docs_bounds.py       # The install checks' bounds the docs state (tries, waits, the lag error) are the workflows' (cascor#777)\n"
REF_PUBLISHING_1 = "Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first, then PyPI (`pypi` needs both TestPyPI jobs: `testpypi` and `verify-testpypi-install`).\n"
REF_PUBLISHING_2 = "Since 2026-11-15 the build runs once and both publish jobs upload its one artifact, checked by sha256 against `SHA256SUMS` and against TestPyPI's and PyPI's JSON; a dispatch from the tag with `-f republish_from_testpypi=true` republishes TestPyPI's files, once the tag's newest release run passed its TestPyPI jobs ([§ Meta-Package Publish Pipeline](#meta-package-publish-pipeline)). Since the template's sweep (juniper-cascor#777, ported 2026-11-26) Gate 1 runs in a job of its own, `Verify the TestPyPI install`, which cannot mint a credential.\n"
REF_PUBLISHING_GATES = "The `build` job skips `juniper-<pkg>-v*` tags. Gates: `tests/test_publish_testpypi_verify.py` (verify shape + poll), `tests/test_publish_release_only_trigger.py` (trigger IS the release-convention gate), `tests/test_publish_one_artifact.py` (one artifact, its sha256 checks, the install job and the republish job) and `tests/test_publish_docs_bounds.py` (the docs' install-check bounds).\n"
REF_P4 = "3. **P4 job-scoped `id-token`** — `id-token: write` sits only on the jobs that upload (TestPyPI, PyPI and, since 2026-11-15, the republish job), never the workflow block, so the build job cannot mint a PyPI credential at all, nor, since the template's sweep (juniper-cascor#777), the install check. Job-level `permissions` **replace** the workflow block rather than merging, so each job states its own: the build `contents: read` and `actions: read`, the TestPyPI and PyPI jobs `id-token: write` alone, since they check nothing out, and `Verify the TestPyPI install` `contents: read` alone, for its sparse checkout. `publish.yml`'s workflow block is `{}`, the sub-packages' `contents: read`.\n"
REF_INV_META_1 = "- `.github/workflows/publish.yml` -- Meta PyPI publish: TestPyPI **Gate 1** two-phase verify (TestPyPI-only download, then local-wheel bare -> `[clients]` -> `[tools]` against PyPI only; never `--no-deps` on the installs, never `--extra-index-url`, never the heavy extras; provenance fetch is a 10×6s poll, not `sleep 30`), in a job of its own since the template's sweep (`Verify the TestPyPI install`, `contents: read` alone), then PyPI (`needs` both TestPyPI jobs, OIDC).\n"
REF_INV_META_2 = "  The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher; a plain dispatch from a `v` tag re-fires it, and a dispatch with `-f republish_from_testpypi=true` runs only the republish job, which refuses unless the tag's newest release run passed its TestPyPI jobs.\n"
REF_INV_META_4 = "  Gates: `tests/test_publish_testpypi_verify.py`, `tests/test_publish_release_only_trigger.py`, `tests/test_publish_one_artifact.py`, `tests/test_publish_docs_bounds.py`. Operator surface: [`docs/REFERENCE.md` § Meta-Package Publish Pipeline](#meta-package-publish-pipeline).\n"
REF_INV_SUB_2 = "  Each build job is gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`, or a dispatch from its own tag that does not ask for the republish job, with a `--no-deps` TestPyPI-only verify (5×10s retry) in the install check's own job.\n"
REF_INV_SUB_3 = "  Since 2026-11-15 they carry the same one-artifact template as `publish.yml`: the `<pkg>-dist` artifact, the sha256 checks around every upload, no `skip-existing`, and the republish job; since the template's sweep (juniper-cascor#777) the install check's own job, `PUBLISH_TAG_PREFIX` and the republish job's refusal too.\n"
REF_META_INTRO = "The `.github/workflows/publish.yml` workflow publishes the `juniper-ml` meta-package. It runs when a GitHub Release is published. A `workflow_dispatch` from a `v` release tag re-fires the whole publish (it builds again, so it works only while TestPyPI does not hold the version yet); with `-f republish_from_testpypi=true` it runs only the republish job, rung 1 of the [recovery ladder](#one-artifact-and-recovering-a-release-that-did-not-reach-pypi), which refuses unless the tag's newest release run passed its TestPyPI jobs:\n"
REF_META_STEP_2 = "2. **Publish to TestPyPI** -- checks out nothing and holds `id-token: write` alone: it downloads the artifact, checks it against `SHA256SUMS`, publishes to TestPyPI with OIDC trusted publishing and attestations, and then requires TestPyPI's JSON for the version to list exactly those files with those sha256.\n"
REF_META_STEP_3 = "3. **Verify the TestPyPI install (Gate 1)** -- a job of its own since the template's sweep (ruling 2 of 2026-11-16; `contents: read` alone and no environment, so nothing it installs can mint a credential). It sets up Python 3.12, sparse-checks out `pyproject.toml` (`persist-credentials: false`), and from `$RUNNER_TEMP` reads `[project].version` under `$GITHUB_WORKSPACE`, then **polls** TestPyPI for the just-uploaded wheel (10 attempts × 6s, ~60s ceiling — not an unconditional `sleep 30`; juniper-ml#1310), then verifies in **two phases**.\n"
REF_META_STEP_3_PROVENANCE = "   1. **Provenance** -- `pip download --no-deps --index-url https://test.pypi.org/simple/ --dest <tmp> \"juniper-ml==${VERSION}\"` inside the poll loop. The artifact comes from TestPyPI and **only** TestPyPI, at the exact built version; a missing `juniper_ml-${VERSION}-py3-none-any.whl` fails the step rather than handing pip a bogus path. The fetch stays on **one line and outside any `if`** — `tests/test_publish_testpypi_verify.py` matches `^pip download` against the stripped line — and a failed try is retried as `pip download … && { FETCHED=1; break; }`, which `bash -e` does not stop at, so the loop needs no `set +e`.\n"
REF_META_STEP_4 = "4. **Publish to PyPI** (`needs: [testpypi, verify-testpypi-install]`) -- runs only after both TestPyPI jobs succeed and the `pypi` environment is approved. It checks out nothing: it downloads the same artifact, checks it against `SHA256SUMS` and TestPyPI's JSON again, publishes it with OIDC trusted publishing and attestations, and then requires PyPI's JSON to list exactly those files with those sha256.\n"
REF_META_GUARD = "**Tag guard:** the `build` job runs only for a Release whose tag starts with `v`, or a `workflow_dispatch` from a `v` tag that does not ask for the republish job, so a shared-package Release or tag (`juniper-<pkg>-v*`) cannot fire the meta publisher. Always-on gate for the two-phase verify (including the anti-regression check that no verify command may carry `--extra-index-url` or name both index URLs), the bounded poll, the tag guard, and the PyPI job needing both TestPyPI jobs: `tests/test_publish_testpypi_verify.py`.\n"
REF_META_LAG = "The poll returns as soon as the artifact is servable (usually the first attempt) and, if the ceiling is hit, fails with the template's lag error, `::error::juniper-ml ${VERSION} is not installable from TestPyPI after 10 tries (index lag?): Re-run failed jobs; a real failure repeats`. Do not restore `sleep 30`.\n"
REF_SIB_GUARD = "| **Build-job tag-prefix guard** | `release: published` fires *every* `publish-*.yml`, so each build job gates on `startsWith(github.event.release.tag_name, '<pkg>-v')` to keep package A's Release from publishing package B. A `workflow_dispatch` runs it too, only from the package's own tag (`startsWith(github.ref_name, '<pkg>-v')`) and only when it does not ask for the republish job (`republish_from_testpypi`). Each workflow `env` names that prefix as `PUBLISH_TAG_PREFIX`; a job-level `if:` cannot read `env`, so the guard repeats it. |\n"
REF_SIB_VERIFY = "| **`--no-deps` TestPyPI-only verify** | With `--no-deps`, no dependencies are fetched, so adding an `--extra-index-url` to production PyPI would only risk resolving a squatted *target* package during TestPyPI index lag. Sibling verify must not add a PyPI fallback. Index lag is a 5×10s retry around `pip install` (4 waits, ~40s), then the template's lag error, distinct from the meta publisher's 10×6s `pip download` poll (~60s). It runs in the install check's own job, from `$RUNNER_TEMP`. |\n"
REF_SIB_OIDC = "| **OIDC + concurrency** | Workflow `permissions: contents: read`, and only the uploading jobs hold `id-token: write`: job-level `permissions` replace that block (build: `contents` and `actions: read`; TestPyPI and PyPI: `id-token` alone; `Verify the TestPyPI install`: `contents: read` alone; republish: `actions: read` and `id-token`); `concurrency.group: publish-<suffix>-${{ github.ref_name }}` with `cancel-in-progress: false`; environments `testpypi` then `pypi`. |\n"
REF_ONE_INTRO = f"All seven publishers carry juniper-cascor's one-artifact template (juniper-cascor#763 and #767, ported 2026-11-15, and its sweep, #777, ported 2026-11-26; the Overtoad's directive of 2026-11-15: \"deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again.\"). The steps marked `One-artifact publish template` and the whole `republish` job are byte-identical to juniper-cascor's `publish.yml`, and read only the workflow `env` values `PUBLISH_PACKAGE`, `PUBLISH_DIST_DIR` and `PUBLISH_TAG_PREFIX` (`v`, or `<pkg>-v`). The contract: [juniper-cascor `MANUAL.md` § One Artifact, Checked Against TestPyPI]({MANUAL}#one-artifact-checked-against-testpypi).\n"
REF_ONE_CHECKS = "- **Check every upload.** Each publish job checks the files against `SHA256SUMS` before it uploads them. TestPyPI's JSON must list exactly those files with those sha256 after the TestPyPI upload, before the install check, and again before the PyPI upload; PyPI's JSON after it.\n- **The install check runs in a job of its own** (ruling 2 of 2026-11-16). `Verify the TestPyPI install` needs the TestPyPI job, holds `contents: read` alone (no environment, no `id-token`), sparse-checks out the one file the version is read from (`persist-credentials: false`) and installs from `$RUNNER_TEMP`; the PyPI job needs both TestPyPI jobs. The TestPyPI job keeps the template steps and the upload, and holds `id-token: write` alone.\n"
REF_LADDER_INTRO = "".join(
    (
        f"A release that did not reach PyPI is recovered by the ladder of 2026-11-15 ([juniper-cascor `MANUAL.md` § Recovering a Release That Did Not Reach PyPI]({MANUAL}#recovering-a-release-that-did-not-reach-pypi)). ",
        "**Rung 1 runs only after the release run's TestPyPI jobs, the upload and the install check, succeeded in their latest attempt**: the republish job reads the tag's newest release run and refuses unless both concluded success, and refuses when the tag has no release run (ruling 1 of 2026-11-16). ",
        "A TestPyPI job that failed on index lag is re-run instead (\"Re-run failed jobs\" on the release run, within 30 days): it runs the failed job and those after it again. ",
        "A re-run `Publish to TestPyPI` uploads the same bytes, which the index accepts, and repeats its JSON check; the install check then runs again. When only `Verify the TestPyPI install` failed, nothing is uploaded again and only the install check repeats. ",
        "A real install-check failure means a broken package: fix it and cut a new patch version, since a re-cut of the same version cannot work (the index refuses new bytes under file names it holds). ",
        "A failed build published nothing: \"Re-run failed jobs\" if the failure was transient, otherwise fix it and cut a new patch version. The ladder, in this order:\n",
    )
)
REF_RUNG_1 = "1. **Republish TestPyPI's files.** Dispatch the release's own workflow from its tag with `republish_from_testpypi`. Only `Republish the tested files (dispatch only)` runs: it waits at the `pypi` gate (a fresh approval, then the 5-minute timer), checks the tag's newest release run as above, builds nothing, downloads the version's files from TestPyPI, checks each against TestPyPI's JSON and, while the release run's artifact exists, its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It takes the version from the tag, which must be the workflow's `PUBLISH_TAG_PREFIX` followed by the exact version; any other tag fails safe.\n"
REF_RUNG_2 = "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run (`gh run rerun <run-id> --repo pcalnon/juniper-ml --failed`). The re-run reuses the run's artifact and waits at the `pypi` gate again. GitHub refuses a re-run after 30 days. For a version that a plain `workflow_dispatch` re-fire published, no release run of its tag passed its TestPyPI jobs, so rung 1 refuses it, and rung 2 applies to that dispatch run, within 30 days of it.\n"
REF_NEVER = "".join(
    (
        "**Never \"Re-run all jobs\"** on a publish run, nor `gh run rerun <run-id>` without `--failed`. A dispatch without the input (`gh workflow run <workflow> --repo pcalnon/juniper-ml --ref <tag>`) re-fires the whole publish and builds new files, so it is only for a failure before TestPyPI took the version: TestPyPI refuses a different build under a file name it holds. ",
        "Never re-cut the Release either: the re-cut's run becomes the tag's newest release run, TestPyPI refuses its files, and rung 1 then refuses the tag. Every dispatch runs from the release tag; both environments admit release tags only.\n",
        "\n",
        "**A failed `Verify PyPI serves exactly these files`** comes after the upload, so the files are already on PyPI. It has two causes. A mismatch (PyPI lists a file this run did not build, or with another sha256): only a new patch version ships tested files under a clean version. ",
        "A check that gave up waiting (PyPI's JSON did not list the files in time): index lag; \"Re-run failed jobs\" on the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run, uploads the same bytes again, which the index accepts, and repeats the check (re-running a PyPI or republish job needs a fresh `pypi` approval).\n",
        "\n",
        "**Which tags the ladder covers.** A dispatch runs the workflow as of the tag. Rung 1 as written here holds for tags cut after this sweep merged; a tag cut from 2026-11-16 (juniper-ml#2593) until then runs the first republish job, which reads no job of the release run, and a tag cut before 2026-11-16 has no republish job.\n",
    )
)
REF_SIB_STEP_3 = "3. **Verify the TestPyPI install** -- a job of its own after the TestPyPI job (`contents: read` alone): it sparse-checks out the file the package version is read from (`<pkg>/pyproject.toml`, or `juniper-model-core/juniper_model_core/_version.py` for model-core; `persist-credentials: false`), and from `$RUNNER_TEMP` reads the version under `$GITHUB_WORKSPACE`, retries `pip install --no-deps --index-url https://test.pypi.org/simple/` up to 5 times with a 10s interval (4 waits, then the template's lag error, `::error::<pkg> <version> is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats`), then confirms the install: an `import` of the package or a run of its CLI, or, for ci-tools and observability, whose imports need dependencies `--no-deps` leaves out, `importlib.metadata` and `importlib.util.find_spec`, which finds the package without running it.\n"
REF_SIB_STEP_4 = "4. **Publish to PyPI** -- runs only after both TestPyPI jobs succeed and the `pypi` approval. It checks the same artifact against `SHA256SUMS` and TestPyPI's JSON again, publishes it with `packages-dir: ${{ env.PUBLISH_DIST_DIR }}/` and `verbose: true`, and then checks PyPI's JSON.\n"


def reference_edits(text: str, date: str, cases: int) -> "tuple[str, int]":
    """docs/REFERENCE.md: the publish sections, the test entries, the suite list, the tree, the version row and lines.
    Returns the new text and the suite count after this port."""
    where = REFERENCE
    versions = re.findall(r"^\*\*Version:\*\* (\d+\.\d+\.\d+)$", text, flags=re.MULTILINE)
    if len(versions) != 2 or versions[0] != versions[1]:
        raise Refused(f"{where}: its header and footer **Version:** lines are {versions}")
    new_version = bump_patch(versions[0])
    text = re.sub(r"^\*\*Version:\*\* \d+\.\d+\.\d+$", f"**Version:** {new_version}", text, flags=re.MULTILINE)
    if len(re.findall(r"^\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}$", text, flags=re.MULTILINE)) != 2:
        raise Refused(f"{where}: expected a header and a footer **Last Updated:** line")
    text = re.sub(r"^\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}$", f"**Last Updated:** {date}", text, flags=re.MULTILINE)
    rows = [m for m in re.finditer(rf"^\| {re.escape(versions[0])} +\| [^\n]*\n", text, flags=re.MULTILINE)]
    if len(rows) != 1:
        raise Refused(f"{where}: {len(rows)} version-history rows for {versions[0]}")
    text = text[: rows[0].end()] + reference_row(new_version, date, cases) + text[rows[0].end() :]
    # Running every suite: the count sentence and the ordered list.
    para = line_of(text, "The complete ordered list, generated from `.github/workflows/ci.yml`'s", where)
    counts = [int(n) for n in re.findall(r"\*\*(\d+)\*\* on", para)]
    tail = ". The drift script above counts, so re-run it rather than trusting this figure."
    if not counts or para.count(tail) != 1:
        raise Refused(f"{where}: the suite-count sentence moved")
    total = max(counts) + 1
    text = replace_once(text, para, para.replace(tail, f", **{total}** on {date} with the one-artifact sweep's docs pins, `tests/test_publish_docs_bounds.py` (the port of juniper-cascor#777){tail}"), where)
    text = replace_once(text, "python3 -m unittest -v tests/test_publish_one_artifact.py\n", "python3 -m unittest -v tests/test_publish_one_artifact.py\npython3 -m unittest -v tests/test_publish_docs_bounds.py\n", where)
    # The Test Suite Reference.
    text = replace_line(text, "  Pins the two-phase verify (TestPyPI-only `pip download --no-deps` provenance", REF_TESTPYPI_VERIFY, where, ("and `pypi needs: testpypi`.",))
    text = replace_line(text, "  Since juniper-ml#1310, the index-lag buffer is a **bounded poll**", REF_TESTPYPI_POLL, where, ("not a silent fall-through",))
    start = "- `tests/test_publish_one_artifact.py` -- The one-artifact publish in all seven publishers"
    old = between(text, start, "- `tests/test_publish_env_policy_drift.py` -- ", where)
    if old.count("\n") != 5:
        raise Refused(f"{where}: the one-artifact suite's entry is not the base's five lines")
    text = replace_once(text, old, REF_ONE_ARTIFACT, where)
    text = replace_line(text, "│   ├── test_publish_one_artifact.py      # ", REF_TREE_ONE_ARTIFACT, where, ("(cascor#763/#767)",))
    # The CI/CD Pipeline Reference and the publish-path authorization layers.
    text = replace_line(text, "Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first", REF_PUBLISHING_1, where, ("(`pypi needs: testpypi`).",))
    text = replace_line(text, "Since 2026-11-15 the build runs once and both publish jobs upload its one artifact", REF_PUBLISHING_2, where, ("republishes TestPyPI's files (",))
    text = replace_line(text, "The `build` job skips `juniper-<pkg>-v*` tags. Gates:", REF_PUBLISHING_GATES, where)
    text = replace_line(text, "3. **P4 job-scoped `id-token`**", REF_P4, where, ("the TestPyPI job `contents: read` for its checkout",))
    # The CI/CD Workflow Inventory.
    text = replace_line(text, "- `.github/workflows/publish.yml` -- Meta PyPI publish:", REF_INV_META_1, where, ("then PyPI (`needs: testpypi`, OIDC).",))
    text = replace_line(text, "  The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher;", REF_INV_META_2, where)
    text = replace_line(text, "  Gates: `tests/test_publish_testpypi_verify.py`, `tests/test_publish_release_only_trigger.py`, `tests/test_publish_one_artifact.py`.", REF_INV_META_4, where)
    text = replace_line(text, "  Each build job is gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`", REF_INV_SUB_2, where)
    text = replace_line(text, "  Since 2026-11-15 they carry the same one-artifact template as `publish.yml`:", REF_INV_SUB_3, where)
    # § Meta-Package Publish Pipeline.
    text = replace_line(text, "The `.github/workflows/publish.yml` workflow publishes the `juniper-ml` meta-package.", REF_META_INTRO, where)
    text = replace_line(text, "2. **Publish to TestPyPI** -- checks out the tag (the verify reads `pyproject.toml`)", REF_META_STEP_2, where)
    text = replace_line(text, "3. **Verify TestPyPI Install (Gate 1)** -- reads `[project].version`", REF_META_STEP_3, where)
    text = replace_line(text, "   1. **Provenance** -- `pip download --no-deps", REF_META_STEP_3_PROVENANCE, where)
    text = replace_line(text, "4. **Publish to PyPI** (`needs: testpypi`) -- runs only after Gate 1 succeeds", REF_META_STEP_4, where)
    text = replace_line(text, "**Tag guard:** the `build` job runs only for a Release whose tag starts with `v`", REF_META_GUARD, where)
    text = replace_line(text, "The poll returns as soon as the artifact is servable", REF_META_LAG, where, ("never served juniper-ml",))
    # § Independent Sibling Package Publish Pipelines.
    text = replace_line(text, "| **Build-job tag-prefix guard** |", REF_SIB_GUARD, where)
    text = replace_line(text, "| **`--no-deps` TestPyPI-only verify** |", REF_SIB_VERIFY, where, ("(~50s)",))
    text = replace_line(text, "| **OIDC + concurrency** |", REF_SIB_OIDC, where, ("TestPyPI: `contents: read` and `id-token`",))
    text = replace_line(text, "All seven publishers carry juniper-cascor's one-artifact template", REF_ONE_INTRO, where)
    text = replace_line(text, "- **Check every upload.** Each publish job checks the files against `SHA256SUMS`", REF_ONE_CHECKS, where)
    text = replace_line(text, "A release that did not reach PyPI is recovered by the Overtoad's ladder", REF_LADDER_INTRO, where)
    text = replace_line(text, "1. **Republish TestPyPI's files.** Dispatch the release's own workflow from its tag", REF_RUNG_1, where, ("It needs a tag cut after this change merged.",))
    text = replace_line(text, "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run (`gh run rerun <run-id> --repo pcalnon/juniper-ml --failed`)", REF_RUNG_2, where)
    text = replace_line(text, "**Never \"Re-run all jobs\"** on a publish run, nor `gh run rerun <run-id>` without `--failed`.", REF_NEVER, where, ("Every dispatch runs from the release tag",))
    text = replace_line(text, "3. **Verify TestPyPI Install** -- after that check, sparse-checks out", REF_SIB_STEP_3, where, ("(~50s ceiling)",))
    text = replace_line(text, "4. **Publish to PyPI** -- runs only after TestPyPI install verification and the `pypi` approval.", REF_SIB_STEP_4, where)
    return text, total


# ── docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md ───────────────────────────────────────────────
CHEAT_RETRY = "| Retry publish | A plain `workflow_dispatch` of `.github/workflows/publish-observability.yml` from its own tag rebuilds, so only before TestPyPI took the version; after that, the recovery ladder ([REFERENCE — the ladder]" + LADDER + ") |\n"
CHEAT_FLOW = "Publish flow: build uploads `juniper-observability-dist` (90 days), TestPyPI downloads and publishes it with OIDC, `Verify the TestPyPI install` (a job that cannot mint a credential) retries the `--no-deps` install 5×10s for index lag and finds the package (`find_spec`), then PyPI downloads the same artifact after both TestPyPI jobs succeed.\n"
CHEAT_RECOVER = "| Recover a publish      | (1) after both TestPyPI jobs passed (the republish refuses otherwise): `gh workflow run publish-<pkg>.yml --repo pcalnon/juniper-ml --ref juniper-<pkg>-vX.Y.Z -f republish_from_testpypi=true` (meta: `publish.yml`, `--ref vX.Y.Z`); (2) if that fails, or a TestPyPI job failed on index lag: within 30 days, `gh run rerun <run-id> --repo pcalnon/juniper-ml --failed`, never \"Re-run all jobs\"; (3) otherwise, and for a failed install check, a new patch version. [REFERENCE — the ladder]" + LADDER + " |\n"
CHEAT_TIP = "Tip: all seven publishers build once and check by sha256 (juniper-cascor#763 / #767's one-artifact template, swept by #777): both publish jobs upload the build job's artifact (dist and `SHA256SUMS`, 90 days), TestPyPI's JSON must list exactly those sha256 after the TestPyPI upload and again before the PyPI one, and PyPI's after; no `skip-existing`; only the uploading jobs hold `id-token: write`. The install check runs in its own job, `Verify the TestPyPI install` (`contents: read` alone), which PyPI needs; each workflow `env` names `PUBLISH_TAG_PREFIX`, and a plain dispatch builds only from the workflow's own tag.\n"
CHEAT_LADDER = "A release that did not reach PyPI: dispatch its workflow from the tag with `-f republish_from_testpypi=true` (copies TestPyPI's files, builds nothing, and refuses unless the tag's newest release run passed both TestPyPI jobs); if that fails, or a TestPyPI job failed on index lag, within 30 days **Re-run failed jobs**, never \"Re-run all jobs\"; otherwise, and for a failed install check, cut a new patch version, never a re-cut. A failed `Verify PyPI serves exactly these files` means the files are already on PyPI: a mismatch needs a new patch version, a check that gave up waiting **Re-run failed jobs** on the run whose check gave up. See [REFERENCE — One artifact, and recovering a release that did not reach PyPI]" + LADDER + ".\n"


def cheatsheet_edits(text: str, date: str) -> str:
    where = CHEATSHEET
    version = re.findall(r"^\*\*Version\*\*: (\d+\.\d+\.\d+)$", text, flags=re.MULTILINE)
    if len(version) != 1:
        raise Refused(f"{where}: {len(version)} **Version** lines")
    text = replace_once(text, f"**Version**: {version[0]}\n", f"**Version**: {bump_patch(version[0])}\n", where)
    text = re.sub(r"^\*\*Date\*\*: \d{4}-\d{2}-\d{2}$", f"**Date**: {date}", text, count=1, flags=re.MULTILINE)
    text = replace_line(text, "| Retry publish | Use `workflow_dispatch` on `.github/workflows/publish-observability.yml` against the existing tag |", CHEAT_RETRY, where)
    text = replace_line(text, "Publish flow: build uploads `juniper-observability-dist` for seven days", CHEAT_FLOW, where)
    text = replace_line(text, "| Recover a publish      | Only after a TestPyPI job (install check included)", CHEAT_RECOVER, where)
    text = replace_line(text, "Tip: all seven publishers build once and check by sha256 (juniper-cascor#763 / #767's one-artifact template):", CHEAT_TIP, where)
    text = replace_line(text, "A release that did not reach PyPI, after a TestPyPI job (install check included)", CHEAT_LADDER, where)
    return text


# ── The ecosystem publish procedure, § 11.8 ───────────────────────────────────────────────
PROCEDURE_AMENDMENT = "".join(
    (
        "**2026-11-26 amendment (the template's sweep, [juniper-cascor#777](https://github.com/pcalnon/juniper-cascor/pull/777); rulings 1 and 2 of 2026-11-16).** ",
        "juniper-cascor's three publishers carry it since #777 and juniper-ml's seven since its port; each other repository's as its port lands. In a publisher that carries it:\n",
        "\n",
        "- the install check runs in a job of its own, `Verify the TestPyPI install` (`contents: read` alone, from `$RUNNER_TEMP`), which the PyPI job needs, and the TestPyPI job holds `id-token: write` alone;\n",
        "- rung 1 refuses unless the tag's newest release run exists and its TestPyPI jobs, the upload and the install check, concluded success in their latest attempt, so it can no longer copy files whose install check failed;\n",
        "- a TestPyPI job that failed on index lag goes to \"Re-run failed jobs\" on the release run, within 30 days, which runs the failed job and those after it again: a re-run `Publish to TestPyPI` uploads the same bytes, which the index accepts, and repeats its JSON check, and the install check then runs again; when only `Verify the TestPyPI install` failed, nothing is uploaded again and only the install check repeats; a failed install check goes to a new patch version;\n",
        "- a re-cut's run becomes the tag's newest release run, TestPyPI refuses its files, and rung 1 then refuses the tag;\n",
        "- the republish takes the version from the tag, the workflow's `PUBLISH_TAG_PREFIX` followed by the exact version, so any other tag fails safe; for a version that a plain dispatch published, no release run of its tag passed its TestPyPI jobs, so rung 1 refuses it, and rung 2 applies to that dispatch run, within 30 days of it;\n",
        "- a failed `Verify PyPI serves exactly these files` (the files are already on PyPI) has two causes: a mismatch, which only a new patch version repairs, or a check that gave up waiting, index lag, which \"Re-run failed jobs\" on the run whose check gave up (the release run, or the republish's dispatch run) repairs within 30 days of that run;\n",
        "- the ladder holds only for tags cut after the publisher carries the job: a dispatch runs the workflow as of the tag.\n",
        "\n",
    )
)


def procedure_edits(text: str) -> str:
    anchor = "**Never \"Re-run all jobs\"** on a publish run, nor `gh run rerun <run-id>` without `--failed`, and do not re-cut the Release:"
    line = line_of(text, anchor, PROCEDURE)
    return replace_once(text, line + "\n---\n\n## 12. Troubleshooting\n", line + "\n" + PROCEDURE_AMENDMENT + "---\n\n## 12. Troubleshooting\n", PROCEDURE)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# CHANGELOG.md: one [Unreleased] / ### Fixed entry, after the first port's, whose superseded statements it marks
# ─────────────────────────────────────────────────────────────────────────────────────────────
#: The first port's entry (juniper-ml#2593) ships beside this one in the next release's notes: the two statements the
#: sweep makes false say so, in place (as juniper-cascor#777 corrected its own earlier entry).
FIRST_ENTRY_EDITS = [
    (
        "the TestPyPI job\n    `contents: read` and `id-token: write`, every PyPI job",
        "the TestPyPI job\n    `contents: read` and `id-token: write` (`id-token: write` alone since the sweep, the next entry), every PyPI job",
    ),
    (
        "JSON and the release run's `SHA256SUMS`, and builds nothing; (2)",
        "JSON and the release run's `SHA256SUMS`, and builds nothing (since the sweep, the next entry, only once the tag's\n    newest release run passed its TestPyPI jobs); (2)",
    ),
]
NEXT_ENTRY = "- **The agent guard also reads each Bash command as bash 5.3 builds its words"


def changelog_entry(cases: int, mutations: int) -> str:
    return "".join(
        (
            "- **The one-artifact publish, swept: the install check runs in a job that cannot mint a credential, the republish\n",
            "  job refuses unless the release run passed its TestPyPI jobs, and `PUBLISH_TAG_PREFIX`, in all seven publishers**\n",
            "  (`publish.yml` and the six `publish-<pkg>.yml`; the port of juniper-cascor#777, rulings 1 and 2 of 2026-11-16).\n",
            "  - **Ruling 2, the install check's own job.** `Verify the TestPyPI install` needs the TestPyPI job, holds\n",
            "    `contents: read` alone (no environment, no `id-token`), sparse-checks out the one file the version is read from\n",
            "    (`persist-credentials: false`), and installs from `$RUNNER_TEMP`, reading the version under `$GITHUB_WORKSPACE`;\n",
            "    `publish.yml`'s keeps its setup-python 3.12. The PyPI job needs both TestPyPI jobs. `Publish to TestPyPI` keeps\n",
            "    the template steps and the upload, checks out nothing, and holds `id-token: write` alone. Until now the check ran\n",
            "    in the TestPyPI job, so pip and the check ran with that job's OIDC token-request variables in their environment.\n",
            "  - **The install scripts.** Each stops with the template's lag error after its last try. `publish.yml`'s provenance\n",
            "    fetch is `pip download … && { FETCHED=1; break; }` in place of its `set +e` block, its `ls -la` drops `|| true`,\n",
            "    and its error after the tenth try is `juniper-ml <version> is not installable from TestPyPI after 10 tries (index\n",
            "    lag?): Re-run failed jobs; a real failure repeats`, in place of \"TestPyPI never served … within ~60s of upload\".\n",
            "    The six sub-packages' loops gain the same error after their fifth try. `publish-ci-tools.yml` and\n",
            "    `publish-observability.yml`, whose checks read metadata alone, which a wheel without the package also passes,\n",
            "    find the package with `importlib.util.find_spec` too (none of its code runs) and fail through `SystemExit`, which\n",
            "    `PYTHONOPTIMIZE` keeps; `publish-config-tools.yml` and `publish-doc-tools.yml` run their `python -c` check last.\n",
            "  - **Ruling 1, the republish gate.** `Find the release run's artifact` reads the tag's newest release run, refuses\n",
            "    when there is none, and refuses unless each of its jobs whose name holds \"testpypi\" (the upload and the install\n",
            "    check) concluded success in its latest attempt (`filter=all`, each name's record with the highest\n",
            "    `(run_attempt, id)`); that run's artifact, while it exists, still checks TestPyPI's files.\n",
            "  - **`PUBLISH_TAG_PREFIX`**, the template's third parameter: `v` in `publish.yml`, `<package>-v` in a sub-package's.\n",
            "    The republish accepts only that prefix followed by the version, so a sub-package publisher dispatched from the\n",
            "    meta `v` tag refuses before any request. Each build guard repeats the prefix (a job-level `if:` cannot read\n",
            "    `env`), and its dispatch branch gains `startsWith(github.ref_name, '<prefix>')`: a plain dispatch builds only\n",
            "    from the workflow's own tag.\n",
            "  - **Comments.** The template's: the republish banner (the monitor reads dispatch runs since juniper-ml#2592), the\n",
            "    witness comment, the `env` comment, and the rc*/hf* note on `publish.yml`'s guard. The sub-packages' permissions\n",
            "    comment now says a job's own `permissions` replace the workflow block; `publish.yml`'s TestPyPI upload comment no\n",
            "    longer says the republish dispatch finishes a re-cut release.\n",
            "  - **Unchanged:** the triggers, the workflow and job names the release train reads (`util/release_train/ceremony.py`\n",
            "    counts both TestPyPI jobs by \"testpypi\", so a failed install check still reads `HALT_TESTPYPI`, with no ceremony\n",
            "    change), the environments, the build steps, and each install check's commands beyond those above.\n",
            f"  - Pins: `tests/test_publish_one_artifact.py` ({cases} cases, 60 before) ports #777's hardening: each job's keys, runner\n",
            "    and exact steps; the install job's wiring, exact commands, and the shell that cannot switch it off; retention\n",
            "    exactly 90; no `skip_existing` or `attestations: false`; the workflow names; `PUBLISH_TAG_PREFIX` against each\n",
            "    guard; the template blocks pinned by sha256 NORMALIZED (each `uses:` line by its action's name, so a Dependabot\n",
            "    bump moves no digest) and each action at one ref; and the rehearsals of the republish gate (no release run, a\n",
            "    failed upload or install check, a carried-over job, a re-run that passed or failed, either listing order, two\n",
            "    pages, an older run behind a newer failed one), of the tag prefix, and of each install check's shell under\n",
            "    `bash -e`. `tests/test_publish_testpypi_verify.py` and `tests/test_publish_subpackage_workflows.py` read the install\n",
            "    check from its job, and a step or workflow they cannot find fails them rather than skipping (R4-1 of the sweep's\n",
            "    review); the TestPyPI job's pinned permissions are `id-token: write` alone. New\n",
            "    `tests/test_publish_docs_bounds.py` pins the install checks' bounds the docs state (the tries, the wait, how many\n",
            "    waits each makes and their total, read from each loop) and their lag errors, wired into\n",
            f"    `ci.yml` and the `main-verify.yml` battery. Each of {mutations} edits to a copy of the workflows and the docs, each\n",
            "    undoing one property, fails the tests, and a bump of one action in all seven publishers at once passes them.\n",
            "  - Docs: `docs/REFERENCE.md` (§ Meta-Package Publish Pipeline and § Independent Sibling Package Publish Pipelines:\n",
            "    the install job, the republish gate, `PUBLISH_TAG_PREFIX`, and the ladder's new facts: an index-lag failure is\n",
            "    \"Re-run failed jobs\", a failed install check a new patch version, never a re-cut, the two causes of a failed\n",
            "    `Verify PyPI serves exactly these files`, rung 2 after a plain dispatch, and the tags the ladder covers),\n",
            "    `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` and\n",
            "    `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§11.8's amendment of 2026-11-26).\n",
            "\n",
        )
    )


def changelog_edits(text: str, cases: int, mutations: int) -> str:
    where = CHANGELOG
    unreleased = text.index("## [Unreleased]") if text.count("## [Unreleased]") == 1 else -1
    first = text.find("- **PyPI now receives the files TestPyPI took, checked by sha256, in all seven publishers**")
    following = text.find(NEXT_ENTRY, first)
    released = text.find("\n## [", unreleased + 1)
    if unreleased < 0 or first < unreleased or following < first or not first < following < released:
        raise Refused(f"{where}: the first port's [Unreleased] entry, and the entry after it, moved")
    entry = text[first:following]
    for old, new in FIRST_ENTRY_EDITS:
        entry = replace_once(entry, old, new, f"{where} (the first port's entry)")
    return text[:first] + entry + changelog_entry(cases, mutations) + text[following:]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# All the files beyond the workflows
# ─────────────────────────────────────────────────────────────────────────────────────────────
def extra_edits(read, template: str, date: str, cases: int, mutations: int) -> "dict[str, str]":
    out = test_edits(read)
    check_test_digests(out[ONE_ARTIFACT_TEST], template)
    ci = replace_once(read(CI), CI_ONE_ARTIFACT_COMMENT_OLD, CI_ONE_ARTIFACT_COMMENT_NEW, CI)
    out[CI] = replace_once(ci, ONE_ARTIFACT_RUN, ONE_ARTIFACT_RUN + CI_DOCS_BOUNDS, CI)
    out[MAIN_VERIFY] = replace_once(read(MAIN_VERIFY), ONE_ARTIFACT_RUN, ONE_ARTIFACT_RUN + "          python3 -m unittest -v tests/test_publish_docs_bounds.py\n", MAIN_VERIFY)
    out[REFERENCE], total = reference_edits(read(REFERENCE), date, cases)
    # AGENTS.md: the suite count, and the day CI's `Verify AGENTS.md Last Updated` compares (the UTC day at upload).
    agents = read(AGENTS)
    found = re.findall(r"the full ordered list of (\d+) `python3 -m unittest`", agents)
    if found != [str(total - 1)]:
        raise Refused(f"{AGENTS}: its suite count is {found}, not the reference's {total - 1}")
    agents = replace_once(agents, f"the full ordered list of {total - 1} `python3 -m unittest`", f"the full ordered list of {total} `python3 -m unittest`", AGENTS)
    out[AGENTS] = re.sub(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {date}", agents, count=1, flags=re.MULTILINE)
    if out[AGENTS].count(f"**Last Updated**: {date}") != 1 or len(out[AGENTS]) != len(read(AGENTS)):
        raise Refused(f"{AGENTS}: the Last Updated line moved, or the edit changed its size (the memory budget)")
    out[CHEATSHEET] = cheatsheet_edits(read(CHEATSHEET), date)
    out[CHANGELOG] = changelog_edits(read(CHANGELOG), cases, mutations)
    out[PROCEDURE] = procedure_edits(read(PROCEDURE))
    return out

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Main: read the tree, apply every edit in memory, check the result, then write it all (or nothing)
# ─────────────────────────────────────────────────────────────────────────────────────────────
def read_template(template_dir: Path) -> "tuple[str, str]":
    texts = []
    for name, want in TEMPLATE_SHA256.items():
        path = template_dir / name
        if not path.is_file():
            raise Refused(f"the template {path} is missing")
        text = path.read_text(encoding="utf-8")
        if sha256(text) != want:
            raise Refused(f"the template {path} hashes to {sha256(text)}, not juniper-cascor main 5e3d9801's {want}")
        texts.append(text)
    return texts[0], texts[1]


def build(tree: Path, template_dir: Path, date: str, cases: int, mutations: int) -> "dict[str, str]":
    """Every file this port writes, as (repo-relative path -> new text), computed from the tree and the template."""
    template, protocol = read_template(template_dir)

    def read(rel: str) -> str:
        path = tree / rel
        if not path.is_file():
            raise Refused(f"{rel} is missing from {tree}")
        return path.read_text(encoding="utf-8")

    out: dict[str, str] = {}
    for workflow in PUBLISHERS:
        rel = f"{WORKFLOW_DIR}/{workflow}"
        out[rel] = workflow_edit(workflow, read(rel), template, protocol, date)
        check_workflow(workflow, out[rel])
    out.update(extra_edits(read, template, date, cases, mutations))
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh clone of juniper-ml main")
    parser.add_argument("--template-dir", type=Path, default=TEMPLATE_DEFAULT, help="juniper-cascor's .github/workflows at main 5e3d9801 (pinned by sha256)")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat(), help="the UTC day the edited docs take (default: today, UTC)")
    parser.add_argument("--changelog-cases", required=True, type=int, help="the new case count of tests/test_publish_one_artifact.py, for the CHANGELOG entry")
    parser.add_argument("--changelog-mutations", required=True, type=int, help="the mutation proof's count, for the CHANGELOG entry")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error(f"--date {args.date!r} is not YYYY-MM-DD")
    if args.changelog_cases <= 0 or args.changelog_mutations <= 0:
        parser.error("--changelog-cases and --changelog-mutations must be positive whole numbers")
    tree = args.tree.resolve()
    if not (tree / ".git").exists() or not (tree / WORKFLOW_DIR / META).is_file():
        parser.error(f"--tree {tree} is not a juniper-ml checkout")
    try:
        out = build(tree, args.template_dir.resolve(), args.date, args.changelog_cases, args.changelog_mutations)
    except Refused as exc:
        print(f"REFUSED (nothing written): {exc}", file=sys.stderr)
        return 1
    for rel, text in out.items():
        path = tree / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {rel} (sha256 {sha256(text)[:12]})")
        else:
            print(f"unchanged {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
