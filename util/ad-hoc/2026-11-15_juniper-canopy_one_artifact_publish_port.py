#!/usr/bin/env python3
"""Port juniper-cascor's one-artifact publish to a fresh copy of juniper-canopy's tree, every edit asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the juniper-canopy port of juniper-cascor#763 / #767: one artifact for TestPyPI and PyPI,
        checked by sha256, and the owner's recovery ladder)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (template_blocks, republish_job, replace_once:
         the template is extracted with them, never retyped); util/ad-hoc/2026-11-15_publish_port_template_identity.py
         (the cross-repo check the edited workflow must pass); util/open_signed_pr.py (uploads the files this writes,
         whole); tmp/ports/BRIEF.md (the port brief, 2026-11-15)

Why
---
The owner's directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to testpypi.
an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to
prevent this from slipping through the cracks again." juniper-canopy's publish.yml already built once and handed both
publish jobs one artifact, so this port is the template's checks: the build job's reuse step, ``SHA256SUMS`` and a
90-day artifact; the dist check before each upload; TestPyPI's JSON after the TestPyPI upload and again before the
PyPI one, and PyPI's after; ``skip-existing`` dropped; per-job permissions; and the republish dispatch (rung 1 of the
owner's recovery ladder). Its own build commands, import smoke test, install check and attestations stay; the install
check's requirement is quoted, which clears actionlint's one finding there (SC2086, info, reported on main too), and
(after the review of juniper-canopy#823) its import runs from $RUNNER_TEMP, so the checkout's juniper_canopy/ can no
longer stand in for the wheel.

``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree ``main`` has since moved past silently reverts
whatever merged in between. Every edit here is therefore replayable: clone canopy's ``main`` afresh, re-run this, and
upload the result. Each anchor must match exactly once, or nothing is written. The edits:

- ``.github/workflows/publish.yml``: the template steps and the whole republish job, copied text-for-text out of
  juniper-cascor's publish.yml (``--template``, which must hash to TEMPLATE_SHA256: cascor ``main`` at
  ``675884888f5a``); the workflow head (dispatch input, ``permissions: {}``, ``env``) cut from the same file; the build
  guard, per-job permissions, the reuse condition on every build step after the reuse step, and the install check's
  requirement quoted and its import moved out of the checkout.
- ``src/tests/unit/test_publish_one_artifact.py`` and
  ``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`` are copied from ``--test-file`` and
  ``--verify-script``.
- ``CHANGELOG.md`` gets one ``[Unreleased]`` / ``### Fixed`` entry; ``AGENTS.md`` (the workflow table row, and the
  ``**Last Updated**:`` line set to ``--date``), ``docs/ci_cd/CICD_REFERENCE.md``, ``docs/ci_cd/CICD_MANUAL.md`` and
  ``docs/ci_cd/CICD_ENVIRONMENT_SETUP.md`` get the docs, each doc's version bumped once.

    python3 -I util/ad-hoc/2026-11-15_juniper-canopy_one_artifact_publish_port.py --tree <fresh canopy tree> \\
        --template <juniper-cascor .github/workflows/publish.yml> --test-file <new test file> \\
        --verify-script <new negative control> --changelog-cases N --changelog-mutations M [--date YYYY-MM-DD]

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once, the template moved, or a new file
already exists (nothing written).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

#: juniper-cascor's publish.yml at main 675884888f5a (2026-11-15, after #763 and #767): the template's source.
TEMPLATE_SHA256 = "c5bdcf4894c0903534d754de44d45dd51c491e8b3d7d004e70a37abe5c242803"
#: sha256 of each file this edits, at juniper-canopy main 4f59aeb0 (2026-11-15), the base these anchors were written on.
BASE_SHA256 = {
    ".github/workflows/publish.yml": "d592aa15dd0114832221bd116780dc53b3fcd96954a29d24f35a3f58e508c63a",
}
PUBLISH = ".github/workflows/publish.yml"
TEST_PATH = "src/tests/unit/test_publish_one_artifact.py"
VERIFY_PATH = "util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py"
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
SETUP_PYTHON = "      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n"
PUBLISH_ACTION = "        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n"
OLD_DOWNLOAD = "      - name: Download dist artifacts\n        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2\n        with:\n          name: dist\n          path: dist/\n"
#: Cut from the template and asserted to occur there exactly once: the per-job permissions.
BUILD_PERMS = "    permissions:\n      contents: read\n      actions: read  # the reuse step lists this run's artifacts\n"
TESTPYPI_PERMS = "    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n"
PYPI_PERMS = "    permissions:\n      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n"
TEMPLATE_HEAD = "on:\n  release:\n    types: [published]\n"


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:90]!r}")
    return text.replace(old, new)


def cascor_edits():
    """juniper-cascor's edits script, beside this one: its template_blocks() and republish_job() cut the template."""
    path = Path(__file__).with_name("2026-11-15_cascor_one_artifact_publish_edits.py")
    spec = importlib.util.spec_from_file_location("cascor_one_artifact_publish_edits", path)
    if spec is None or spec.loader is None:
        raise Refused(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def template_head(template: str) -> str:
    """The template's workflow head, from ``on:`` to ``jobs:`` (dispatch input, permissions, env), for this package."""
    for anchor in (TEMPLATE_HEAD, "\njobs:\n", BUILD_PERMS, TESTPYPI_PERMS, PYPI_PERMS):
        if template.count(anchor) != 1:
            raise Refused(f"template: {anchor[:60]!r} occurs {template.count(anchor)} times, expected 1")
    start = template.index(TEMPLATE_HEAD)
    head = template[start : template.index("\njobs:\n") + 1]
    return replace_once(head, "  PUBLISH_PACKAGE: juniper-cascor\n", "  PUBLISH_PACKAGE: juniper-canopy\n", "template head")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# publish.yml
# ─────────────────────────────────────────────────────────────────────────────────────────────
HEADER_OLD = "# Version:       0.1.0\n#\n# Date Created:  2026-02-26\n# Last Modified: 2026-02-26\n"
HEADER_NEW = "# Version:       0.2.0\n#\n# Date Created:  2026-02-26\n# Last Modified: {date}\n"
DESCRIPTION_OLD = (
    "# Description:\n"
    "#    GitHub Actions publish pipeline for juniper-canopy.\n"
    "#    Triggered by GitHub release. Publishes to TestPyPI first (with install\n"
    "#    verification), then to PyPI. Uses OIDC trusted publishing (no API tokens).\n"
    "#\n"
)
DESCRIPTION_NEW = (
    "# Description:\n"
    "#    GitHub Actions publish pipeline for juniper-canopy, triggered by a published `v*` Release.\n"
    "#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both jobs the\n"
    "#    same artifact: TestPyPI takes it first and must then serve exactly those sha256 (then the\n"
    "#    install check), and PyPI takes it only after TestPyPI is checked again. Uses OIDC trusted\n"
    "#    publishing (no API tokens).\n"
    "#\n"
    "#    The steps marked \"one-artifact publish template\", and the republish job, are juniper-cascor's\n"
    "#    publish.yml template, copied verbatim (juniper-cascor docs/ci_cd/MANUAL.md § One Artifact,\n"
    "#    Checked Against TestPyPI). The republish job is step 1 of the owner's recovery ladder for a\n"
    "#    release that never reached PyPI (docs/ci_cd/CICD_MANUAL.md § Runbook: Release publishing).\n"
    "#\n"
)
WORKFLOW_HEAD_OLD = TEMPLATE_HEAD + "\npermissions:\n  id-token: write\n  contents: read\n\njobs:\n"
BUILD_OLD = (
    "  build:\n"
    "    name: Build and Validate\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    + CHECKOUT
    + "\n"
    + SETUP_PYTHON
    + '        with:\n          python-version: "3.14"\n\n'
    "      - name: Install build tools\n        run: pip install build twine\n\n"
    "      - name: Build package\n        run: python -m build\n\n"
    "      - name: Check package\n        run: twine check dist/*\n\n"
)
BUILD_GUARD = (
    "    # Release guard: build only for a published `v*` Release (every juniper-canopy release tag is one, and\n"
    "    # publish-image.yml guards its release build the same way). A workflow_dispatch carries no release, so it builds\n"
    "    # nothing: the dispatch exists for the republish job alone. Both publish jobs depend on this one, so this guard\n"
    "    # gates the whole pipeline.\n"
    "    if: startsWith(github.event.release.tag_name, 'v')\n"
)
SMOKE_OLD = "      - name: Import smoke test (built wheel, nothing from the checkout)\n        run: |\n"
#: The install check's two changes. Its requirement is quoted, which clears actionlint's SC2086 (info), reported on main
#: too. And its import runs from $RUNNER_TEMP (the review of juniper-canopy#823): from the checkout's root, `python -c`
#: puts the working directory first on sys.path, so it imported the checkout's juniper_canopy/, not the wheel.
INSTALL_LINE_OLD = (
    "          pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-canopy==${VERSION}\n"
    "          python -c \"from juniper_canopy import __version__; print(f'TestPyPI OK: v{__version__}')\"\n"
)
INSTALL_LINE_NEW = (
    '          pip install --no-deps --index-url https://test.pypi.org/simple/ "juniper-canopy==${VERSION}"\n'
    "          # `python -c` puts the working directory first on sys.path, and the checkout's root holds juniper_canopy/,\n"
    "          # which would shadow the wheel just installed: import it from outside the checkout.\n"
    '          cd "${RUNNER_TEMP}"\n'
    "          python -c \"from juniper_canopy import __version__; print(f'TestPyPI OK: v{__version__}')\"\n"
)
UPLOAD_OLD = "      - name: Upload dist artifacts\n        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2\n        with:\n          name: dist\n          path: dist/\n          retention-days: 7\n"
TESTPYPI_HEAD = "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n"
TESTPYPI_OLD = OLD_DOWNLOAD + "\n      - name: Publish to TestPyPI\n" + PUBLISH_ACTION + "        with:\n          repository-url: https://test.pypi.org/legacy/\n          attestations: true\n          skip-existing: true\n\n"
PYPI_HEAD = "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n    runs-on: ubuntu-latest\n    environment: pypi\n"
PYPI_OLD = (
    PYPI_HEAD
    + "    steps:\n"
    + CHECKOUT
    + "\n"
    + SETUP_PYTHON
    + '        with:\n          # python-version: ["3.12", "3.13", "3.14"]\n          python-version: "3.14"\n\n'
    + OLD_DOWNLOAD
    + "\n      - name: Publish to PyPI\n"
    + PUBLISH_ACTION
    + "        with:\n          attestations: true\n"
)


def publish_workflow(text: str, template: str, blocks: dict, republish: str, date: str) -> str:
    """Give publish.yml the template's head, steps and republish job; keep its build, smoke test and install check."""
    where = PUBLISH
    text = replace_once(text, HEADER_OLD, HEADER_NEW.format(date=date), where)
    text = replace_once(text, DESCRIPTION_OLD, DESCRIPTION_NEW, where)
    text = replace_once(text, WORKFLOW_HEAD_OLD, template_head(template) + "jobs:\n", where)
    build_new = (
        "  build:\n"
        "    name: Build and Validate\n"
        + BUILD_GUARD
        + "    runs-on: ubuntu-latest\n"
        + BUILD_PERMS
        + "    steps:\n"
        + blocks["build/Reuse an earlier attempt's artifact"]
        + "\n"
        + CHECKOUT
        + REUSE_IF
        + "\n"
        + SETUP_PYTHON
        + REUSE_IF
        + '        with:\n          python-version: "3.14"\n\n'
        "      - name: Install build tools\n" + REUSE_IF + "        run: pip install build twine\n\n"
        "      - name: Build package\n" + REUSE_IF + "        run: python -m build\n\n"
        "      - name: Check package\n" + REUSE_IF + "        run: twine check dist/*\n\n"
    )
    text = replace_once(text, BUILD_OLD, build_new, where)
    text = replace_once(text, SMOKE_OLD, SMOKE_OLD.replace("\n        run: |\n", "\n" + REUSE_IF + "        run: |\n"), where)
    text = replace_once(text, UPLOAD_OLD, blocks["build/Record SHA256SUMS"] + "\n" + blocks["build/Upload dist artifacts"], where)
    text = replace_once(text, TESTPYPI_HEAD + "    steps:\n", TESTPYPI_HEAD + TESTPYPI_PERMS + "    steps:\n", where)
    testpypi_new = (
        blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + "      - name: Publish to TestPyPI\n"
        + PUBLISH_ACTION
        + "        with:\n          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          attestations: true\n\n"
        + blocks["testpypi/Verify TestPyPI serves exactly these files"]
        + "\n"
    )
    text = replace_once(text, TESTPYPI_OLD, testpypi_new, where)
    text = replace_once(text, INSTALL_LINE_OLD, INSTALL_LINE_NEW, where)
    if not text.endswith(PYPI_OLD):
        raise Refused(f"{where}: the PyPI job is not the file's last job, as written")
    pypi_new = (
        PYPI_HEAD
        + PYPI_PERMS
        + "    steps:\n"
        + blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + "      - name: Publish to PyPI\n"
        + PUBLISH_ACTION
        + "        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          attestations: true\n\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
        + "\n"
        + republish
    )
    return replace_once(text, PYPI_OLD, pypi_new, where)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# CHANGELOG.md
# ─────────────────────────────────────────────────────────────────────────────────────────────
CHANGELOG_ENTRY = """\
- **PyPI receives only the files TestPyPI took, checked by sha256: `publish.yml` drops `skip-existing` and checks
  every upload against TestPyPI's and PyPI's JSON** (the owner's directive of 2026-11-15: "deploy to pypi should send
  the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy
  and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again."; the
  port of juniper-cascor#763 and #767). This workflow already built once and handed both publish jobs one artifact, and
  0.5.0 through 0.10.0 serve the same sha256 on both indexes. But nothing compared a sha256 with either index, and the
  TestPyPI upload set `skip-existing: true`, which keeps an earlier file under the same name. TestPyPI took 0.3.0's
  files at 09:24Z on 2026-02-27, before that release's only publish run (22481348704) started at 09:52Z, so its
  TestPyPI upload could only skip them and its install check installed TestPyPI's files, while PyPI serves other files
  under both names: the wheel is `ce2a0482…` on PyPI and `30b1cdb1…` on TestPyPI, the sdist `d206f2f2…` against
  `06b04725…`. The artifact was also kept 7 days, while the `pypi` gate may wait 30.
  - **The template.** The steps marked `One-artifact publish template`, and the republish job, are juniper-cascor's
    `publish.yml` (its `main` at `675884888f5a`), copied verbatim. The workflow `env` sets their two parameters,
    `PUBLISH_PACKAGE: juniper-canopy` and `PUBLISH_DIST_DIR: dist`.
  - **Build once, and reuse it on a re-run.** `Build and Validate` keeps its commands and the import smoke test, then
    `Record SHA256SUMS` hashes the files, and `Upload dist artifacts` uploads `dist/` and `SHA256SUMS` as one artifact,
    `juniper-canopy-dist` (was `dist`), kept 90 days (was 7). Its new first step, `Reuse an earlier attempt's artifact`,
    skips every later step on a re-run attempt whose run already holds that artifact, because download-artifact takes
    the newest artifact of a name. Its new guard, `startsWith(github.event.release.tag_name, 'v')`, keeps the new
    dispatch from building; every juniper-canopy release tag starts with `v`.
  - **TestPyPI.** `Publish to TestPyPI` checks the downloaded files against `SHA256SUMS`, uploads them (attestations
    kept, `skip-existing` gone), and `Verify TestPyPI serves exactly these files` then requires TestPyPI's JSON for
    the version to list exactly those files with those sha256. The install check follows. Its requirement is now
    quoted (which clears actionlint's one finding, SC2086), and its import now runs from `$RUNNER_TEMP`: run from the
    checkout's root, `python -c` put the checkout's `juniper_canopy/` first on `sys.path`, so a broken wheel passed it.
  - **PyPI.** `Publish to PyPI` no longer checks out or sets up Python. It checks the files against `SHA256SUMS`, and
    TestPyPI's JSON again, before its upload (attestations kept), and PyPI's JSON after it.
  - **Only the jobs that upload hold `id-token: write`.** The workflow's `permissions` is `{}`: `Build and Validate`
    gets `contents: read` and `actions: read`, `Publish to TestPyPI` `contents: read` and `id-token: write`, and
    `Publish to PyPI` `id-token: write`.
  - **Recovery, in the owner's order (ruling of 2026-11-15).** A `workflow_dispatch` from the release tag with
    `republish_from_testpypi` runs only the new job `Republish the tested files (dispatch only)`, behind the same
    `pypi` gate. It builds nothing: it copies TestPyPI's files for the version to PyPI, each checked against TestPyPI's
    JSON and, while the release run's artifact exists, its `SHA256SUMS`. If that fails, within 30 days of the release
    run, "Re-run failed jobs" on it; after that, cut a new patch version. Never "Re-run all jobs".
  - Unchanged: the `release: published` trigger (no `push: tags`), the `testpypi` and `pypi` environments, the job
    names juniper-ml's release-train ceremony reads, the build commands, the import smoke test, and
    `publish-image.yml`.
  - New `src/tests/unit/test_publish_one_artifact.py` ({cases} cases), ported from juniper-cascor's: the wiring, what
    this workflow kept, and rehearsals that run each template step's own Python, extracted from `publish.yml`, against
    a stand-in index and GitHub API on 127.0.0.1. Beyond cascor's copy it pins every job's exact steps, in order, no
    `continue-on-error` on a job or a step, an `if:` only where the template gates a step, the install check's
    commands, and more build front ends than `python -m build`. The unit lane selects it.
    `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py` makes {mutations} mutations to a
    copy of the workflow, one at a time, and the tests catch each. CI does not run it.
  - Docs: `docs/ci_cd/CICD_MANUAL.md` (§ Runbook: Release publishing, with the recovery ladder; 0.29.4),
    `docs/ci_cd/CICD_REFERENCE.md` (§ `publish.yml` and the workflow inventory; 0.30.5),
    `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md` (the workflow permissions; 0.28.6) and `AGENTS.md` (the workflow table)."""


def changelog(text: str, cases: str, mutations: str) -> str:
    """Append the entry to the end of ``[Unreleased]``'s ``### Fixed``, keeping the blank lines that close the section."""
    if text.count("## [Unreleased]\n") != 1:
        raise Refused("CHANGELOG.md: no single '## [Unreleased]' heading")
    start = text.find("## [Unreleased]\n")
    end = text.find("\n## [", start + 1)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    fixed = section.find("\n### Fixed\n")
    if fixed < 0:
        raise Refused("CHANGELOG.md: [Unreleased] has no '### Fixed' (re-derive the entry's place)")
    after = section.find("\n### ", fixed + 1)
    cut = len(section) if after < 0 else after + 1
    body = section[:cut].rstrip("\n")
    closing = section[len(body) : cut]
    entry = CHANGELOG_ENTRY.replace("{cases}", cases).replace("{mutations}", mutations)
    return text[:start] + body + "\n" + entry + closing + section[cut:] + text[end:]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# AGENTS.md and docs/ci_cd/
# ─────────────────────────────────────────────────────────────────────────────────────────────
AGENTS_ROW_OLD = "| Publish | `publish.yml` | Release publishing automation |\n"
AGENTS_ROW_NEW = "| Publish | `publish.yml` | PyPI publish on a `v*` Release: one build; TestPyPI, then PyPI, each upload checked by sha256 against the index's JSON; a tag dispatch can republish TestPyPI's files ([runbook](docs/ci_cd/CICD_MANUAL.md#runbook-release-publishing)) |\n"

REFERENCE_ROW_OLD = "| `.github/workflows/publish.yml`             | release published                                                    | Build + TestPyPI + PyPI publish                      |\n"
REFERENCE_ROW_NEW = "| `.github/workflows/publish.yml`             | release published; `workflow_dispatch` from a tag (republish only)   | One build to TestPyPI, then PyPI, sha256-checked against both |\n"
REFERENCE_SECTION_OLD = """\
### `publish.yml`

- Trigger: GitHub release published
- `id-token: write` for trusted publishing
- Stages:
  1. Build + `twine check`
  2. Publish to TestPyPI + install verification
  3. Publish to PyPI
"""
REFERENCE_SECTION_NEW = """\
### `publish.yml`

- Trigger: GitHub release published; the build job's guard is `startsWith(github.event.release.tag_name, 'v')`. A `workflow_dispatch` from a release tag with the boolean input `republish_from_testpypi` runs the republish job alone: no other job runs on a dispatch. No `push: tags` (juniper-ml#555's double-fire).
- Permissions: `permissions: {}` at the top. `Build and Validate` holds `contents: read` and `actions: read`; `Publish to TestPyPI` `contents: read` and `id-token: write`; `Publish to PyPI` `id-token: write`; `Republish the tested files (dispatch only)` `actions: read` and `id-token: write`. Only the jobs that upload can mint the OIDC token for trusted publishing.
- Stages:
  1. `Build and Validate`, once: `pip install build twine`, `python -m build`, `twine check dist/*`, the import smoke test, `Record SHA256SUMS`, and `Upload dist artifacts`, which uploads `dist/` and `SHA256SUMS` as one artifact, `juniper-canopy-dist`, kept 90 days. Its first step, `Reuse an earlier attempt's artifact`, runs on attempt 2 and later: when the run already holds that artifact, every later step skips.
  2. `Publish to TestPyPI`: `Verify the dist against SHA256SUMS`, the upload (`attestations: true`, no `skip-existing`), `Verify TestPyPI serves exactly these files` (TestPyPI's JSON for the version lists exactly those files and sha256), then the install verification, which imports from `$RUNNER_TEMP` so the checkout's `juniper_canopy/` cannot stand in for the wheel.
  3. `Publish to PyPI`: the dist check, `Verify TestPyPI still serves exactly these files`, the upload (`attestations: true`), and `Verify PyPI serves exactly these files`. It checks out and builds nothing.
- The steps marked `One-artifact publish template`, and the republish job, are juniper-cascor's, copied verbatim; its manual's [One Artifact, Checked Against TestPyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi) is the contract.
  A JSON check polls up to 20 times, 15 s apart, while the index does not list a file yet, and fails at once on a file listed with another sha256 or one the run did not build. Pinned by `src/tests/unit/test_publish_one_artifact.py`. Recovery: [Runbook: Release publishing](CICD_MANUAL.md#runbook-release-publishing).
"""

MANUAL_RUNBOOK_OLD = """\
### Runbook: Release publishing

`publish.yml` is release-triggered (`release: published`) and uses OIDC:

1. Build and `twine check`
2. Publish to TestPyPI (`environment: testpypi`)
3. Verify installation from TestPyPI
4. Publish to PyPI (`environment: pypi`)

Do not bypass TestPyPI stage; production publish is intentionally downstream.
"""
MANUAL_RUNBOOK_NEW = """\
### Runbook: Release publishing

`publish.yml` is release-triggered (`release: published`, a `v*` tag) and uses OIDC. It builds once, and both publish jobs upload that one artifact (`dist/` and `SHA256SUMS`), so PyPI receives exactly the files TestPyPI took and the install check tested:

1. Build and `twine check`, then the import smoke test, once; `SHA256SUMS` records the files
2. Publish to TestPyPI (`environment: testpypi`); TestPyPI's JSON must then list exactly those files and sha256
3. Verify installation from TestPyPI; the import runs from `$RUNNER_TEMP`, outside the checkout, so it loads the installed wheel
4. Publish to PyPI (`environment: pypi`), after TestPyPI's JSON is checked again; PyPI's JSON is checked after the upload

Do not bypass TestPyPI stage; production publish is intentionally downstream. The contract: [`CICD_REFERENCE.md` § `publish.yml`](CICD_REFERENCE.md#publishyml), and juniper-cascor's [One Artifact, Checked Against TestPyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi), whose template steps this workflow copies verbatim.

A release that did not reach PyPI follows the owner's ladder (ruling of 2026-11-15), in this order. Every rung publishes the files TestPyPI took, or nothing ([juniper-cascor's manual](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#recovering-a-release-that-did-not-reach-pypi)):

1. Republish TestPyPI's files: dispatch this workflow from the release's tag.

   ```bash
   gh workflow run publish.yml --repo pcalnon/juniper-canopy --ref v<version> -f republish_from_testpypi=true
   ```

   Only `Republish the tested files (dispatch only)` runs. It waits at the `pypi` gate like the release run (a fresh approval, then the 5-minute timer), builds nothing, downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON.
   Both publish environments admit tags only, so dispatch from the tag, never a branch. A tag cut before this change does not carry the job.
2. If that fails, within 30 days of the release run: **Re-run failed jobs** on the release run. The re-run reuses the run's artifact and waits at the gate again. GitHub refuses a re-run after 30 days.
3. Otherwise, cut a new patch version.

When `Publish to TestPyPI` failed after its upload (at `Verify TestPyPI serves exactly these files`, or at the install check), find out why before taking any rung. TestPyPI already holds the files, and the republish job never reads that job's result: it publishes whatever TestPyPI holds.

- The install check failed on index lag: its one `pip install` runs 30 seconds after the upload, and TestPyPI's simple index can be slower. The files are fine. Rung 1 publishes them; rung 2's re-run uploads the same files again (TestPyPI answers a byte-identical file with 200 and keeps the one it holds) and repeats both checks.
- The install check failed because the package is broken (it does not install, or does not import): publish these files by no rung. Fix the package and cut a new patch version.
- `Verify TestPyPI serves exactly these files` failed: TestPyPI holds other files for this version. Do not publish them. While the release run's artifact exists, the republish job refuses them too, because they disagree with its `SHA256SUMS`.

Never use "Re-run all jobs" on a publish run, nor `gh run rerun <id>` without `--failed`. download-artifact takes the newest artifact of a name, so a rebuild would become the files every later job uploads; the build job's `Reuse an earlier attempt's artifact` step skips such a rebuild, but a tag cut before this change lacks the step. That older workflow also uploads to TestPyPI with `skip-existing: true`, so there the rebuild passes unnoticed: TestPyPI keeps its files, and PyPI receives the rebuild.
"""

ENVIRONMENT_PERMISSIONS_OLD = "- `publish.yml`: `id-token: write` for OIDC trusted publishing\n"
ENVIRONMENT_PERMISSIONS_NEW = "- `publish.yml`: `permissions: {}` at the top, then per job: `Build and Validate` `contents: read` and `actions: read` (its reuse step lists the run's artifacts), `Publish to TestPyPI` `contents: read` and `id-token: write`, `Publish to PyPI` `id-token: write` (it checks out nothing), and `Republish the tested files (dispatch only)` `actions: read` and `id-token: write`. Only the jobs that upload hold `id-token: write`, for OIDC trusted publishing\n"

#: doc -> (version before, version after, how many header blocks carry the version and date: CICD_REFERENCE.md repeats
#: them in its footer, and juniper-canopy#822 bumped both).
DOC_VERSIONS = {
    "docs/ci_cd/CICD_REFERENCE.md": ("0.30.4", "0.30.5", 2),
    "docs/ci_cd/CICD_MANUAL.md": ("0.29.3", "0.29.4", 1),
    "docs/ci_cd/CICD_ENVIRONMENT_SETUP.md": ("0.28.5", "0.28.6", 1),
}


def replace_n(text: str, old: str, new: str, count: int, where: str) -> str:
    found = text.count(old)
    if found != count:
        raise Refused(f"{where}: anchor matched {found} times, expected {count}: {old[:90]!r}")
    return text.replace(old, new)


def dated(text: str, line: re.Pattern, prefix: str, date: str, count: int, where: str) -> str:
    """Set every header date line matching ``line`` (``count`` of them, all equal) to ``date``; unchanged if they read it."""
    found = line.findall(text)
    if len(found) != count or len(set(found)) != 1:
        raise Refused(f"{where}: date lines {found}, expected {count} equal ones")
    return replace_n(text, found[0], f"{prefix}{date}\n", count, where) if found[0] != f"{prefix}{date}\n" else text


def doc_header(text: str, rel: str, date: str) -> str:
    old, new, count = DOC_VERSIONS[rel]
    text = replace_n(text, f"**Version:** {old}\n", f"**Version:** {new}\n", count, f"{rel} version")
    return dated(text, re.compile(r"^\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}\n", re.M), "**Last Updated:** ", date, count, f"{rel} date")


def apply(tree: Path, template: str, test_file: str, verify_script: str, date: str, cases: str, mutations: str) -> dict[str, str]:
    """Return {repo path: new text} for every file the change writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    if sha256(template) != TEMPLATE_SHA256:
        raise Refused(f"the template hashes to {sha256(template)[:12]}, not cascor 675884888f5a's {TEMPLATE_SHA256[:12]}: re-check the port against the new template")
    edits = cascor_edits()
    try:
        blocks = edits.template_blocks(template)
        republish = edits.republish_job(template)
    except edits.Refused as exc:
        raise Refused(f"template: {exc}") from exc
    out: dict[str, str] = {}
    current = read(PUBLISH)
    if sha256(current) != BASE_SHA256[PUBLISH]:
        print(f"note: {PUBLISH} moved since 4f59aeb0; applying by anchors")
    out[PUBLISH] = publish_workflow(current, template, blocks, republish, date)
    for rel, text in ((TEST_PATH, test_file), (VERIFY_PATH, verify_script)):
        if (tree / rel).exists():
            raise Refused(f"{rel} already exists on this base")
        out[rel] = text
    out["CHANGELOG.md"] = changelog(read("CHANGELOG.md"), cases, mutations)
    agents = replace_once(read("AGENTS.md"), AGENTS_ROW_OLD, AGENTS_ROW_NEW, "AGENTS.md workflow table")
    out["AGENTS.md"] = dated(agents, re.compile(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}\n", re.M), "**Last Updated**: ", date, 1, "AGENTS.md date")
    reference = doc_header(read("docs/ci_cd/CICD_REFERENCE.md"), "docs/ci_cd/CICD_REFERENCE.md", date)
    reference = replace_once(reference, REFERENCE_ROW_OLD, REFERENCE_ROW_NEW, "CICD_REFERENCE.md workflow inventory")
    out["docs/ci_cd/CICD_REFERENCE.md"] = replace_once(reference, REFERENCE_SECTION_OLD, REFERENCE_SECTION_NEW, "CICD_REFERENCE.md § publish.yml")
    manual = doc_header(read("docs/ci_cd/CICD_MANUAL.md"), "docs/ci_cd/CICD_MANUAL.md", date)
    out["docs/ci_cd/CICD_MANUAL.md"] = replace_once(manual, MANUAL_RUNBOOK_OLD, MANUAL_RUNBOOK_NEW, "CICD_MANUAL.md § Runbook: Release publishing")
    environment = doc_header(read("docs/ci_cd/CICD_ENVIRONMENT_SETUP.md"), "docs/ci_cd/CICD_ENVIRONMENT_SETUP.md", date)
    out["docs/ci_cd/CICD_ENVIRONMENT_SETUP.md"] = replace_once(environment, ENVIRONMENT_PERMISSIONS_OLD, ENVIRONMENT_PERMISSIONS_NEW, "CICD_ENVIRONMENT_SETUP.md workflow permissions")
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh copy of juniper-canopy's tree (edited in place)")
    parser.add_argument("--template", required=True, type=Path, help="juniper-cascor's .github/workflows/publish.yml at 675884888f5a")
    parser.add_argument("--test-file", required=True, type=Path, help=f"the new {TEST_PATH}")
    parser.add_argument("--verify-script", required=True, type=Path, help=f"the new {VERIFY_PATH}")
    parser.add_argument("--changelog-cases", required=True, help="the case count the CHANGELOG entry states")
    parser.add_argument("--changelog-mutations", required=True, help="the mutation count the CHANGELOG entry states")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat(), help="the date for the headers' Last Updated / Last Modified (default: today, UTC)")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        print(f"REFUSED: --date {args.date!r} is not YYYY-MM-DD")
        return 1
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.verify_script.read_text(encoding="utf-8"), args.date, args.changelog_cases, args.changelog_mutations)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    for rel, text in sorted(out.items()):
        target = args.tree / rel
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(text, encoding="utf-8")
        print(f"wrote {rel} ({sha256(before)[:12] if before else 'new'} -> {sha256(text)[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
