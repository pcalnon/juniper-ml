#!/usr/bin/env python3
"""Port juniper-cascor's one-artifact publish fix to a fresh copy of juniper-cascor-client's tree, every edit asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port of juniper-cascor#763 and #767, "publish one artifact to TestPyPI and PyPI", to juniper-cascor-client)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (template_blocks / republish_job / replace_once, used here);
         util/ad-hoc/2026-11-15_publish_port_template_identity.py (the cross-repo check the result must pass);
         util/ad-hoc/2026-11-15_juniper-data-client_one_artifact_publish_port.py and
         util/ad-hoc/2026-11-15_juniper-cascor-worker_one_artifact_publish_port.py (the same port; their shared section is this one's);
         util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
juniper-cascor-client's ``publish.yml`` built the sdist and wheel in its TestPyPI job and again in its PyPI job, so PyPI
served a second build of every release (0.8.0's wheel is ``1333cd49...`` on PyPI and ``839a547f...`` on TestPyPI). The
owner's directive of 2026-11-15 asks that PyPI get the artifact TestPyPI got, checked by sha256, and the fix-scope ruling
asks for the shared build and the hash check in every publish workflow. juniper-cascor's ``publish.yml`` at main
``675884888f5a`` (after #763 and #767) is the template; this gives juniper-cascor-client its SINGLE-PACKAGE shape:

- ``.github/workflows/publish.yml``: the canonical file header; cascor's triggers (``release: published`` plus the
  ``workflow_dispatch`` input ``republish_from_testpypi``), ``permissions: {}`` and ``env`` comment, with this package's
  ``PUBLISH_PACKAGE``; a ``build`` job (``Build and Validate``) holding the repo's own build commands, each gated on the
  reuse step, between cascor's template steps; the TestPyPI job keeps its checkout, setup-python and install check (the
  requirement now quoted, which clears actionlint's SC2086 there), the PyPI job checks out nothing, and cascor's
  republish job is appended. Every template step and the republish job are
  cut out of cascor's file by ``template_blocks`` / ``republish_job``, never retyped, and re-cut from the result to prove
  them byte-identical.
- ``tests/test_publish_one_artifact.py``: copied from ``--test-file`` (the port of cascor's test, reviewed separately).
- ``CHANGELOG.md``: one ``[Unreleased]`` / ``### Fixed`` entry. ``docs/REFERENCE.md``: the ``publish.yml`` subsection
  of § CI/CD Pipeline Reference states the contract and the owner's recovery ladder, with when its first rung applies
  and why a broken package means a new patch version; its ``**Version:**`` moves 0.1.5 -> 0.1.6 and its
  ``**Last Updated:**`` to the day this runs (UTC), header and footer, as each of its recent edits did. AGENTS.md is
  left alone: it only names the file, and it sits 145 characters under its memory budget.

Review follow-up (2026-11-16, the second commit of juniper-cascor-client#199): the ladder's first-rung condition and the
broken-package rule, the REFERENCE.md version and date, and the test's exact pins (``--test-file``). Re-running this on
a fresh clone of the same base yields the pull request's whole content, both commits.

``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree ``main`` has moved past would silently revert
what merged in between. Re-apply on a fresh clone instead:

    python3 -I util/ad-hoc/2026-11-15_juniper-cascor-client_one_artifact_publish_port.py --tree <fresh clone> \\
        --template <juniper-cascor publish.yml at 675884888f5a> --test-file <the ported test> [--changelog-cases N]

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once, an input moved, or a template block
came out different (nothing is written then); 2 on a usage error.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Repo-specific: juniper-cascor-client
# ─────────────────────────────────────────────────────────────────────────────────────────────
REPO = "juniper-cascor-client"
PACKAGE = "juniper-cascor-client"
APPLICATION = "juniper_cascor_client"
DATE_CREATED = "2026-02-21"  # the commit that added publish.yml (a0e50ddb, "ci: Add GitHub Actions CI/CD workflows")
#: sha256 of publish.yml at juniper-cascor-client main e8aa7361 (2026-11-15), the base this was written on.
BASE_SHA256 = "88d849318ddc9219becfc91b8b9f38cd64c9debb8d2cbd3e0365dcf6d5663c93"
#: The TestPyPI upload's inputs today, and after: packages-dir added; skip-existing dropped where it was set.
TESTPYPI_WITH_OLD = "          repository-url: https://test.pypi.org/legacy/\n"
TESTPYPI_WITH_NEW = "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n"
#: The PyPI upload's inputs today (none), and after.
PYPI_WITH_OLD = ""
PYPI_WITH_NEW = "        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n"
#: The install check's one change: its requirement quoted, which clears actionlint's SC2086 (info), on main too.
INSTALL_LINE_OLD = "          pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor-client==${VERSION}\n"
INSTALL_LINE_NEW = '          pip install --no-deps --index-url https://test.pypi.org/simple/ "juniper-cascor-client==${VERSION}"\n'
TEST_PATH = "tests/test_publish_one_artifact.py"

REFERENCE_PATH = "docs/REFERENCE.md"
REFERENCE_OLD = """\
#### `publish.yml` — PyPI Publishing

**Trigger**: GitHub release published

1. Build and publish to TestPyPI, verify installation
2. Build and publish to production PyPI (trusted publishing / OIDC)
"""
REFERENCE_NEW = """\
#### `publish.yml` — PyPI Publishing

**Triggers**: GitHub release published (the build job admits `v*` tags only); `workflow_dispatch` from a release tag, which only republishes (below)

1. `Build and Validate` builds the sdist and wheel once (`python -m build`, `twine check`), records their sha256 in `SHA256SUMS` and uploads both as one artifact, `juniper-cascor-client-dist`, kept 90 days; a re-run attempt reuses that artifact instead of building again
2. `Publish to TestPyPI` checks the files against `SHA256SUMS`, uploads them, requires TestPyPI's JSON to list exactly those sha256, then verifies the install (`--no-deps`, TestPyPI index only)
3. `Publish to PyPI`, behind the `pypi` approval, checks the same files against `SHA256SUMS` and TestPyPI's JSON again, uploads them (trusted publishing / OIDC), then checks PyPI's JSON. Only the jobs that upload hold `id-token: write`

The steps marked `One-artifact publish template`, and the `republish` job, are verbatim copies of juniper-cascor's `publish.yml` (juniper-cascor#763, #767); `tests/test_publish_one_artifact.py` pins them to its sha256, so change them there first. The contract: juniper-cascor's [`docs/ci_cd/MANUAL.md` § One Artifact, Checked Against TestPyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi).

**A release that did not reach PyPI**: the owner's recovery ladder (ruling of 2026-11-15), in this order ([§ Recovering a Release That Did Not Reach PyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#recovering-a-release-that-did-not-reach-pypi)):

1. **Republish TestPyPI's files**: `gh workflow run publish.yml --repo pcalnon/juniper-cascor-client --ref v<version> -f republish_from_testpypi=true`. Only `Republish the tested files (dispatch only)` runs, behind the `pypi` gate; it builds nothing, and only a tag cut after this job landed carries it.
   It copies TestPyPI's files whatever the release run's jobs concluded, so use it only when that run's `Publish to TestPyPI` succeeded, or failed on index lag alone (a JSON check or the install check that gave up waiting).
2. **If that fails, within 30 days of the release run**: **Re-run failed jobs** on the release run, which reuses the run's artifact.
3. **Otherwise**: cut a new patch version.

A broken package is neither case: when `Publish to TestPyPI` failed after its upload for a real reason (the install check refused the package, say for its `Requires-Python`), TestPyPI already holds those files, and neither rung 1 nor "Re-run failed jobs" can change them, so cut a new patch version.
Never "Re-run all jobs" on a publish run, nor `gh run rerun <id>` without `--failed`.
"""
#: The file's version and dates, header and footer: each of its recent edits moved both (0.1.3 -> 0.1.4 -> 0.1.5).
REFERENCE_VERSION_OLD = "**Version:** 0.1.5\n"
REFERENCE_VERSION_NEW = "**Version:** 0.1.6\n"
REFERENCE_DATE_PREFIX = "**Last Updated:** "


def replace_each(text: str, old: str, new: str, count: int, where: str) -> str:
    """``replace_once`` for an anchor the file holds exactly ``count`` times (a header line its footer repeats)."""
    found = text.count(old)
    if found != count:
        raise Refused(f"{where}: anchor matched {found} times, expected {count}: {old[:90]!r}")
    return text.replace(old, new)


def docs_edits(read) -> dict[str, str]:
    """This repository's documentation edits, {repo path: new text}; ``read(rel)`` returns the base's text. The date is
    the day this runs, in UTC, written as the file writes it ("November 16, 2026")."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    text = replace_once(read(REFERENCE_PATH), REFERENCE_OLD, REFERENCE_NEW, REFERENCE_PATH)
    text = replace_each(text, REFERENCE_VERSION_OLD, REFERENCE_VERSION_NEW, 2, REFERENCE_PATH)
    dated = sorted({line for line in text.splitlines(keepends=True) if line.startswith(REFERENCE_DATE_PREFIX)})
    if len(dated) != 1:
        raise Refused(f"{REFERENCE_PATH}: its '{REFERENCE_DATE_PREFIX}' lines disagree or are missing: {dated}")
    text = replace_each(text, dated[0], f"{REFERENCE_DATE_PREFIX}{today:%B} {today.day}, {today.year}\n", 2, REFERENCE_PATH)
    return {REFERENCE_PATH: text}


CHANGELOG_ENTRY = """\
- **PyPI now receives the files TestPyPI took: `publish.yml` builds once, and the run checks every upload by sha256
  against TestPyPI** (the owner's directive of 2026-11-15: "deploy to pypi should send the same artifact that was
  already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy,
  might also be helpful here to prevent this from slipping through the cracks again."). `publish.yml` ran
  `python -m build` in its TestPyPI job and again in its PyPI job, so PyPI served a second build of every release:
  0.8.0's wheel is `1333cd49…` on PyPI and `839a547f…` on TestPyPI, and its sdist `d8f9abef…` against `8e89be1f…`;
  0.7.0's files differ the same way. This ports juniper-cascor's fix (juniper-cascor#763, #767), template verbatim.
  - **Build once.** A new `build` job, `Build and Validate`, runs the same commands once (`pip install build twine`,
    `python -m build`, `twine check dist/*`, Python 3.12), records the files' sha256 in `SHA256SUMS` and uploads
    `dist/` and `SHA256SUMS` as one artifact, `juniper-cascor-client-dist`, kept 90 days so it outlives the `pypi`
    gate (at most 30 days) and the 30-day re-run window. On a re-run attempt its first step,
    `Reuse an earlier attempt's artifact`, finds that artifact and skips the rest of the job. It carries the guard
    `startsWith(github.event.release.tag_name, 'v')`; every release of this repository is tagged `v<version>`.
  - **TestPyPI.** `Publish to TestPyPI` downloads the artifact, checks it against `SHA256SUMS`, uploads it, and
    requires TestPyPI's JSON for the version to list exactly those files with those sha256 (polled up to 20 times,
    15 s apart, for CDN lag; another sha256 fails at once). Its checkout, setup-python and install check stay; the
    install check now quotes its requirement, which clears actionlint's SC2086 (info) there.
  - **PyPI.** `Publish to PyPI` keeps its `pypi` environment and gate, no longer checks out or builds anything, and
    uploads the same artifact after checking it against `SHA256SUMS` and TestPyPI's JSON again; PyPI's JSON is
    checked after the upload.
  - **Only the jobs that upload hold `id-token: write`.** The workflow's `permissions` is `{}`: `Build and Validate`
    gets `contents: read` and `actions: read`, `Publish to TestPyPI` `contents: read` and `id-token: write`, and
    `Publish to PyPI` `id-token: write`.
  - **Recovery, in the owner's order (ruling of 2026-11-15).** A `workflow_dispatch` from the release tag with
    `republish_from_testpypi` runs only `Republish the tested files (dispatch only)`, behind the same `pypi` gate: it
    copies TestPyPI's files for the version to PyPI, each checked against TestPyPI's JSON and, while it exists, the
    release run's `SHA256SUMS`, and builds nothing. It copies those files whatever the release run concluded, so it
    applies only when that run's TestPyPI job succeeded or failed on index lag alone. If that fails, within 30 days
    of the release run use "Re-run failed jobs" on it; otherwise cut a new patch version, which is also the only fix
    for a broken package (a TestPyPI job that failed after its upload for a real reason). Never "Re-run all jobs".
    `docs/REFERENCE.md` § CI/CD Pipeline Reference carries the ladder and the dispatch command.
  - Pinned by the new `tests/test_publish_one_artifact.py` ({cases} cases), ported from juniper-cascor's: the wiring,
    what this workflow kept, each job's exact step list, no `continue-on-error`, the install check's script and the
    uploads' inputs exactly, every template block and the republish job byte-identical to juniper-cascor's, and
    rehearsals that run each template step's own Python against a stand-in index and GitHub API on 127.0.0.1.
"""

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Shared by the three ports (juniper-cascor-client, juniper-data-client, juniper-cascor-worker): keep identical
# ─────────────────────────────────────────────────────────────────────────────────────────────
WORKFLOW_PATH = ".github/workflows/publish.yml"
#: The carried cascor edit script (its sha256 in tmp/ports/carried_scripts.sha256) and juniper-cascor's publish.yml at
#: main 675884888f5a, after #763 and #767: the template every port copies.
EDIT_SCRIPT = Path(__file__).resolve().parent / "2026-11-15_cascor_one_artifact_publish_edits.py"
EDIT_SCRIPT_SHA256 = "d5e1de3fa13ddc78dc481ec2d2701ec92f9edb8d9002882e6e12b9e07e09f38f"
TEMPLATE_SHA256 = "c5bdcf4894c0903534d754de44d45dd51c491e8b3d7d004e70a37abe5c242803"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
SETUP_PYTHON = '      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n        with:\n          python-version: "3.12"\n'
PUBLISH_ACTION = "        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n"
#: The repo's own build steps, as its TestPyPI and PyPI jobs each ran them; the build job keeps them, reuse-gated.
BUILD_STEPS = (
    CHECKOUT,
    SETUP_PYTHON,
    "      - name: Install build tools\n        run: pip install build twine\n",
    "      - name: Build package\n        run: python -m build\n",
    "      - name: Check package\n        run: twine check dist/*\n",
)
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
OLD_PREAMBLE = "name: Publish to PyPI\n\non:\n  release:\n    types: [published]\n\npermissions:\n  id-token: write\n\njobs:\n"
OLD_TESTPYPI_HEAD = "  testpypi:\n    name: Publish to TestPyPI\n    runs-on: ubuntu-latest\n    environment: testpypi\n    steps:\n"
OLD_PYPI_HEAD = "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n    runs-on: ubuntu-latest\n    environment: pypi\n    steps:\n"
#: Lifted from the template unchanged (each asserted to occur in it once): the job heads and permissions.
BUILD_PERMISSIONS = "    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n      actions: read  # the reuse step lists this run's artifacts\n    steps:\n"
NEW_TESTPYPI_HEAD = "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n    steps:\n"
NEW_PYPI_HEAD = "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n    runs-on: ubuntu-latest\n    environment: pypi\n    permissions:\n      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n    steps:\n"
BUILD_GUARD = (
    "    # Release-convention guard: build, and so publish, only for a published `v*` Release (every release of this\n"
    "    # repository is tagged v<version>). A dispatch carries no release tag, so the republish dispatch builds nothing.\n"
    "    # Both publish jobs depend on this job, so this guard gates the whole release pipeline.\n"
    "    if: startsWith(github.event.release.tag_name, 'v')\n"
)
HEADER = """\
---
{banner}
# Project:       Juniper
# Sub-Project:   {repo}
# Application:   {application}
# File Name:     publish.yml
# Author:        Paul Calnon
#
# Date Created:  {created}
# Last Modified: 2026-11-15
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    GitHub Actions publish pipeline for {repo}, triggered by a published `v*` Release.
#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both jobs the
#    same artifact: TestPyPI takes it first and must then serve exactly those sha256, and PyPI takes
#    it only after TestPyPI is checked again. Uses OIDC trusted publishing (no API tokens).
#
#    The steps marked "One-artifact publish template", and the republish job, are verbatim copies of
#    juniper-cascor's publish.yml (juniper-cascor#763, #767). tests/test_publish_one_artifact.py pins
#    them to juniper-cascor's sha256: change them there first, then copy them here. The republish job
#    is step 1 of the owner's recovery ladder for a release that never reached PyPI.
#
# References:
#    - https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi
#    - https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#recovering-a-release-that-did-not-reach-pypi
{banner}

"""


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:90]!r}")
    return text.replace(old, new)


def load_edit_script():
    """The cascor edit script's template_blocks / republish_job, loaded only if it is the carried, reviewed copy."""
    actual = hashlib.sha256(EDIT_SCRIPT.read_bytes()).hexdigest()
    if actual != EDIT_SCRIPT_SHA256:
        raise Refused(f"{EDIT_SCRIPT.name} hashes to {actual}, not the carried {EDIT_SCRIPT_SHA256}")
    spec = importlib.util.spec_from_file_location("cascor_one_artifact_publish_edits", EDIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def gate(step: str) -> str:
    """A build step that the reuse step can skip: the reuse condition goes right after the step's first line."""
    first, _, rest = step.partition("\n")
    return first + "\n" + REUSE_IF + rest


def publish_workflow(text: str, template: str, edits) -> str:
    """Give the repo's publish.yml the template's single-package shape; keep its own build commands and install check."""
    for piece in (BUILD_PERMISSIONS, NEW_TESTPYPI_HEAD, NEW_PYPI_HEAD, "\non:\n  release:\n", "\n  PUBLISH_PACKAGE: juniper-cascor\n"):
        if template.count(piece) != 1:
            raise Refused(f"the template does not hold this exactly once: {piece[:90]!r}")
    blocks = cut(edits.template_blocks, template)
    republish = cut(edits.republish_job, template)
    banner = template.splitlines()[1]
    if set(banner) != {"#"}:
        raise Refused("the template's second line is not its header banner")
    # The triggers, the top-level permissions and the env comment are the template's, word for word.
    shared = template[template.index("\non:\n  release:\n") + 1 : template.index("\n  PUBLISH_PACKAGE: juniper-cascor\n") + 1]
    preamble = HEADER.format(banner=banner, repo=REPO, application=APPLICATION, created=DATE_CREATED) + "name: Publish to PyPI\n\n" + shared + f"  PUBLISH_PACKAGE: {PACKAGE}\n  PUBLISH_DIST_DIR: dist\n\njobs:\n"
    text = replace_once(text, OLD_PREAMBLE, preamble, "preamble")
    old_steps = "\n".join(BUILD_STEPS)
    build_job = (
        "  build:\n    name: Build and Validate\n"
        + BUILD_GUARD
        + BUILD_PERMISSIONS
        + blocks["build/Reuse an earlier attempt's artifact"]
        + "\n"
        + "\n".join(gate(step) for step in BUILD_STEPS)
        + "\n"
        + blocks["build/Record SHA256SUMS"]
        + "\n"
        + blocks["build/Upload dist artifacts"]
        + "\n"
    )
    old_testpypi = OLD_TESTPYPI_HEAD + old_steps + "\n      - name: Publish to TestPyPI\n" + PUBLISH_ACTION + "        with:\n" + TESTPYPI_WITH_OLD + "\n"
    new_testpypi = (
        build_job
        + NEW_TESTPYPI_HEAD
        + CHECKOUT
        + "\n"
        + SETUP_PYTHON
        + "\n"
        + blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + "      - name: Publish to TestPyPI\n"
        + PUBLISH_ACTION
        + "        with:\n"
        + TESTPYPI_WITH_NEW
        + "\n"
        + blocks["testpypi/Verify TestPyPI serves exactly these files"]
        + "\n"
    )
    text = replace_once(text, old_testpypi, new_testpypi, "TestPyPI job")
    text = replace_once(text, INSTALL_LINE_OLD, INSTALL_LINE_NEW, "install check")
    old_pypi =OLD_PYPI_HEAD + old_steps + "\n      - name: Publish to PyPI\n" + PUBLISH_ACTION + PYPI_WITH_OLD
    if not text.endswith(old_pypi):
        raise Refused("the PyPI job is not the file's last job, as written")
    new_pypi = (
        NEW_PYPI_HEAD
        + blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + "      - name: Publish to PyPI\n"
        + PUBLISH_ACTION
        + PYPI_WITH_NEW
        + "\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
        + "\n"
        + republish
    )
    text = replace_once(text, old_pypi, new_pypi, "PyPI job")
    # Re-cut the result: every template block and the republish job must come out byte-identical to the template's.
    if cut(edits.template_blocks, text) != blocks:
        raise Refused("a template block of the result differs from the template's")
    if cut(edits.republish_job, text) != republish:
        raise Refused("the result's republish job differs from the template's")
    return text


def cut(function, text: str):
    """Call one of the edit script's cutters, reporting its refusal as this script's own."""
    module = sys.modules[function.__module__]
    try:
        return function(text)
    except module.Refused as exc:
        raise Refused(f"{function.__name__}: {exc}") from exc


def changelog(text: str, entry: str) -> str:
    """Append the entry to the end of ``[Unreleased]``'s ``### Fixed`` (creating the heading if a release emptied it)."""
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise Refused("CHANGELOG.md: no single '## [Unreleased]' heading")
    end = text.find("\n## [", start + 1)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    fixed = section.find("\n### Fixed\n")
    if fixed < 0:
        new_section = section.rstrip("\n") + "\n\n### Fixed\n\n" + entry + "\n"
    else:
        after = section.find("\n### ", fixed + 1)
        cut = len(section) if after < 0 else after + 1
        new_section = section[:cut].rstrip("\n") + "\n" + entry + "\n" + section[cut:]
    return text[:start] + new_section + text[end:]


def apply(tree: Path, template: str, test_file: str, cases: str) -> dict[str, str]:
    """Return {repo path: new text} for every file the port writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    if sha256(template) != TEMPLATE_SHA256:
        raise Refused(f"the template hashes to {sha256(template)}, not juniper-cascor 675884888f5a's publish.yml: re-derive the port")
    edits = load_edit_script()
    out: dict[str, str] = {}
    current = read(WORKFLOW_PATH)
    if sha256(current) != BASE_SHA256:
        print(f"note: {WORKFLOW_PATH} moved since the base this was written on; applying by anchors")
    out[WORKFLOW_PATH] = publish_workflow(current, template, edits)
    if (tree / TEST_PATH).exists():
        raise Refused(f"{TEST_PATH} already exists on this base")
    out[TEST_PATH] = test_file
    out["CHANGELOG.md"] = changelog(read("CHANGELOG.md"), CHANGELOG_ENTRY.replace("{cases}", cases))
    out.update(docs_edits(read))
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help=f"a fresh clone of {REPO}'s main (edited in place)")
    parser.add_argument("--template", required=True, type=Path, help="juniper-cascor's .github/workflows/publish.yml at main 675884888f5a")
    parser.add_argument("--test-file", required=True, type=Path, help=f"the new {TEST_PATH}")
    parser.add_argument("--changelog-cases", default="{cases}", help="the case count the CHANGELOG entry states")
    args = parser.parse_args(argv)
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.changelog_cases)
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
