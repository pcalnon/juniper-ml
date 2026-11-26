#!/usr/bin/env python3
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
