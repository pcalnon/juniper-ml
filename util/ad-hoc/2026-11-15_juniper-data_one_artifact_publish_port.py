#!/usr/bin/env python3
"""Port juniper-cascor's one-artifact publish to a fresh juniper-data tree, every edit asserted to match exactly once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port juniper-cascor#763 / #767's one-artifact publish fix to juniper-data)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (template_blocks, republish_job and replace_once,
         which this loads); util/ad-hoc/2026-11-15_publish_port_template_identity.py (the cross-repo identity check);
         util/open_signed_pr.py (uploads the files this writes, whole);
         notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md

Why
---
juniper-data's ``publish.yml`` ran ``python -m build`` in its TestPyPI job and again in its PyPI job, so PyPI served a
second build of every release (0.17.1's wheel: ``cce2c167...`` on PyPI, ``3b8f1a84...`` on TestPyPI). The Overtoad's
directive of 2026-11-15 asks for one artifact and a sha256 check; juniper-cascor's ``publish.yml`` (main 675884888f5a,
after #763 and #767) is the template. ``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree that
``main`` has since moved past silently reverts whatever merged in between. Every edit here is therefore replayable on a
fresh clone, and anchored: each ``replace_once`` must match exactly once, or nothing is written.

- ``.github/workflows/publish.yml`` gets the single-package shape of the template: ``workflow_dispatch`` with the
  ``republish_from_testpypi`` input, ``permissions: {}``, the two ``env`` parameters, a ``build`` job (the template's
  reuse step, the repo's own build commands each gated on it, the record and upload steps), the TestPyPI and PyPI jobs
  rewired onto the artifact, and the republish job appended last. ``notify-consumers`` keeps its trigger semantics
  (``needs: pypi``); only a comment above it is added. Every template step and the republish job are extracted from
  ``--template`` as raw text (comments included), never retyped, and checked byte-identical after the edit.
- ``juniper_data/tests/unit/test_publish_one_artifact.py`` is copied from ``--test-file`` (refused if it exists).
- ``juniper_data/tests/unit/test_testpypi_install_verify.py`` gets a comment on its tag-without-``v`` case, which the new
  build guard keeps from reaching the install check in a release run (juniper-data#543's review, item 5).
- ``CHANGELOG.md`` gets one ``[Unreleased]`` / ``### Fixed`` entry, at the top (this changelog lists newest first).
- ``docs/ci_cd/CICD_MANUAL.md``, ``docs/ci_cd/CICD_REFERENCE.md``, ``docs/REFERENCE.md``,
  ``docs/ci_cd/CICD_QUICK_START.md`` and ``docs/DEVELOPER_CHEATSHEET.md`` get the contract, the recovery ladder and the
  manual consumer re-send, each with its stamp bumped once.

juniper-data#543 landed this in two commits: the first as written on 2026-11-15, the second after its independent
review (exact step lists pinned, the cascor snapshot named, four docs passages corrected, the install-verify note).
This script writes the final state of both from ``main`` at fefd1895.

    python3 -I util/ad-hoc/2026-11-15_juniper-data_one_artifact_publish_port.py --tree <fresh juniper-data clone> \\
        --template <juniper-cascor publish.yml> --test-file <new test file> \\
        [--changelog-cases N] [--changelog-mutations M] [--dry-run]

Exit status: 0 when every edit applied (or would, under --dry-run); 1 when an anchor did not match exactly once or a
self-check failed (nothing written).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

#: sha256 of juniper-data's publish.yml at main fefd1895 (2026-11-15), the base these anchors were written against.
BASE_SHA256 = "4cd9fafa60602b1d54d5a5d79638993f228ec94354d5976e4b3aaa4e1e6b0649"
WORKFLOW = ".github/workflows/publish.yml"
NOTIFY = ".github/workflows/notify-consumers.yml"
TEST_PATH = "juniper_data/tests/unit/test_publish_one_artifact.py"
INSTALL_VERIFY_PATH = "juniper_data/tests/unit/test_testpypi_install_verify.py"
CASCOR_EDITS = Path(__file__).resolve().parent / "2026-11-15_cascor_one_artifact_publish_edits.py"
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
SETUP_PYTHON = '      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n        with:\n          python-version: "3.12"\n'
PYPA = "        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n"


def _load_cascor_edits():
    """The cascor writer's template_blocks / republish_job / replace_once / Refused, loaded from its file."""
    spec = importlib.util.spec_from_file_location("cascor_one_artifact_publish_edits", CASCOR_EDITS)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {CASCOR_EDITS}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EDITS = _load_cascor_edits()
Refused = EDITS.Refused
replace_once = EDITS.replace_once


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def between(text: str, start: str, end: str, where: str) -> str:
    """The text from ``start`` (included) to ``end`` (excluded); each must occur exactly once, start before end."""
    for marker in (start, end):
        if text.count(marker) != 1:
            raise Refused(f"{where}: marker matched {text.count(marker)} times, expected 1: {marker[:90]!r}")
    i, j = text.index(start), text.index(end)
    if j <= i:
        raise Refused(f"{where}: {end[:60]!r} does not follow {start[:60]!r}")
    return text[i:j]


def once(text: str, fragment: str, where: str) -> str:
    """Return ``fragment`` after checking it occurs exactly once in ``text``."""
    if text.count(fragment) != 1:
        raise Refused(f"{where}: fragment matched {text.count(fragment)} times, expected 1: {fragment[:90]!r}")
    return fragment


# ── publish.yml ────────────────────────────────────────────────────────────────────────────────────────────────────

HEADER_BODY = """\
# Project:       Juniper
# Sub-Project:   JuniperData
# File Name:     publish.yml
# Author:        Paul Calnon
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:   Publish the juniper-data package to TestPyPI, then PyPI, from a published `v*` GitHub Release.
#
#    ONE ARTIFACT (the Overtoad's directive of 2026-11-15; a port of juniper-cascor#763 and #767). The build job builds
#    the sdist and wheel once, records their sha256 in SHA256SUMS and hands both publish jobs that one artifact.
#    TestPyPI takes it first and must then serve exactly those sha256; PyPI takes it only after TestPyPI's JSON is
#    checked again, and must serve them too. Until then each publish job ran its own `python -m build`, so PyPI served
#    a second build of every release (the 0.17.1 wheel: cce2c167... on PyPI, 3b8f1a84... on TestPyPI). Uses OIDC
#    trusted publishing (no API tokens); only the jobs that upload hold id-token: write.
#
#    The steps marked "one-artifact publish template", and the republish job, are juniper-cascor's publish.yml copied
#    verbatim: they read nothing from this repository but the two `env` values below. The republish job is step 1 of
#    the Overtoad's recovery ladder for a release that did not reach PyPI (docs/ci_cd/CICD_MANUAL.md § Recovering a
#    release that did not reach PyPI). notify-consumers runs after the PyPI job of a release run only: a republish
#    dispatch skips it, and notify-consumers.yml's own workflow_dispatch re-sends.
"""

BUILD_HEAD = """\
  build:
    name: Build and Validate
    # Release-convention guard: every juniper-data release is tagged v<version> (all 15 to 2026-11-15), and
    # publish-image.yml applies the same guard to the same release event. A dispatch has no release tag, so the
    # republish dispatch builds nothing. Both publish jobs depend on this one, so this guard gates the whole pipeline.
    if: startsWith(github.event.release.tag_name, 'v')
    runs-on: ubuntu-latest
"""

OLD_TOP = "name: Publish to PyPI\n\non:\n  release:\n    types: [published]\n\npermissions:\n  id-token: write\n\njobs:\n"
OLD_BUILD_STEPS = (
    CHECKOUT
    + "\n"
    + SETUP_PYTHON
    + "\n"
    + "      - name: Install build tools\n        run: pip install build twine\n\n"
    + "      - name: Build package\n        run: python -m build\n\n"
    + "      - name: Check package\n        run: twine check dist/*\n"
)
OLD_TESTPYPI = "  testpypi:\n    name: Publish to TestPyPI\n    runs-on: ubuntu-latest\n    environment: testpypi\n    steps:\n" + OLD_BUILD_STEPS + "\n" + "      - name: Publish to TestPyPI\n" + PYPA + "        with:\n          repository-url: https://test.pypi.org/legacy/\n\n"
OLD_PYPI = "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n    runs-on: ubuntu-latest\n    environment: pypi\n    steps:\n" + OLD_BUILD_STEPS + "\n" + "      - name: Publish to PyPI\n" + PYPA
OLD_NOTIFY_COMMENT = (
    "  # After PyPI serves the release, tell the repos that install juniper-data from PyPI, so their\n"
    "  # CI runs against it instead of waiting for someone to touch their paths (juniper-recurrence#178).\n"
    "  # A separate job: the pypi job's status is the publish verdict, and a failed dispatch shows here.\n"
)
NEW_NOTIFY_COMMENT = OLD_NOTIFY_COMMENT + (
    "  # A republish dispatch skips this job: it needs pypi, which a dispatch skips, and its version is the release's\n"
    "  # tag, which a dispatch lacks. After a republish, re-send with notify-consumers.yml's own workflow_dispatch\n"
    "  # (docs/ci_cd/CICD_MANUAL.md § Recovering a release that did not reach PyPI).\n"
)
OLD_TAIL = "    secrets:\n      CROSS_REPO_DISPATCH_TOKEN: ${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}\n"


def gate_on_reuse(steps: str) -> str:
    """Add the reuse condition under the first line of every step (``      - ...``), as the template's build job has it."""
    out = []
    for line in steps.splitlines(keepends=True):
        out.append(line)
        if line.startswith("      - "):
            out.append(REUSE_IF)
    return "".join(out)


def publish_workflow(text: str, template: str, notify_yml: str) -> str:
    """Return juniper-data's new publish.yml: the template's single-package shape around the repo's own steps."""
    where = WORKFLOW
    blocks = EDITS.template_blocks(template)
    republish = EDITS.republish_job(template)
    # Verbatim from the template: the dispatch trigger (with its comment), the workflow permissions, the env block and
    # each job's permissions. Only the env's package name changes.
    dispatch = between(template, "  # Recovery only, never a publish of new files:", "\n# Each job states what it needs.", "template dispatch")
    permissions = between(template, "# Each job states what it needs.", "\nenv:\n", "template permissions")
    env = between(template, "env:\n  # The one-artifact publish template's two parameters", "\njobs:\n", "template env")
    env = replace_once(env, "  PUBLISH_PACKAGE: juniper-cascor\n", "  PUBLISH_PACKAGE: juniper-data\n", "template env")
    build_permissions = once(template, "    permissions:\n      contents: read\n      actions: read  # the reuse step lists this run's artifacts\n", "template build permissions")
    testpypi_permissions = once(template, "    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n", "template TestPyPI permissions")
    pypi_permissions = once(template, "    permissions:\n      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n", "template PyPI permissions")
    # The header rule is notify-consumers.yml's, so the two release workflows match.
    rule = notify_yml.splitlines(keepends=True)[0]
    if set(rule.strip()) != {"#"}:
        raise Refused(f"{NOTIFY}: its first line is not a rule of '#': {rule[:40]!r}")

    build = (
        BUILD_HEAD
        + build_permissions
        + "    steps:\n"
        + blocks["build/Reuse an earlier attempt's artifact"]
        + "\n"
        + gate_on_reuse(OLD_BUILD_STEPS)
        + "\n"
        + blocks["build/Record SHA256SUMS"]
        + "\n"
        + blocks["build/Upload dist artifacts"]
    )
    new_top = rule + HEADER_BODY + rule + "\n" + "name: Publish to PyPI\n\non:\n  release:\n    types: [published]\n" + dispatch + "\n" + permissions + "\n" + env + "\njobs:\n" + build + "\n"
    text = replace_once(text, OLD_TOP, new_top, where)

    testpypi = (
        "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n"
        + testpypi_permissions
        + "    steps:\n"
        + CHECKOUT
        + "\n"
        + SETUP_PYTHON
        + "\n"
        + blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + "      - name: Publish to TestPyPI\n"
        + PYPA
        + "        with:\n          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n"
        + blocks["testpypi/Verify TestPyPI serves exactly these files"]
        + "\n"
    )
    text = replace_once(text, OLD_TESTPYPI, testpypi, where)

    pypi = (
        "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n    runs-on: ubuntu-latest\n    environment: pypi\n"
        + pypi_permissions
        + "    steps:\n"
        + blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + "      - name: Publish to PyPI\n"
        + PYPA
        + "        with:\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
    )
    text = replace_once(text, OLD_PYPI, pypi, where)
    text = replace_once(text, OLD_NOTIFY_COMMENT, NEW_NOTIFY_COMMENT, where)
    if not text.endswith(OLD_TAIL):
        raise Refused(f"{where}: notify-consumers is not the file's last job, so the republish job has no place to go")
    text = text + "\n" + republish

    # Self-checks: every template block and the republish job are the template's, byte for byte; the YAML parses; the
    # dispatch input is the template's.
    if EDITS.template_blocks(text) != blocks:
        raise Refused(f"{where}: a template block differs from the template after the edit")
    if EDITS.republish_job(text) != republish:
        raise Refused(f"{where}: the republish job differs from the template after the edit")
    import yaml  # noqa: PLC0415 - only the self-check needs it

    parsed, source = yaml.safe_load(text), yaml.safe_load(template)
    if parsed.get(True, {}).get("workflow_dispatch") != source.get(True, {}).get("workflow_dispatch"):
        raise Refused(f"{where}: the workflow_dispatch trigger is not the template's")
    if sorted(parsed["jobs"]) != ["build", "notify-consumers", "pypi", "republish", "testpypi"]:
        raise Refused(f"{where}: jobs are {sorted(parsed['jobs'])}")
    return text


# ── CHANGELOG.md ───────────────────────────────────────────────────────────────────────────────────────────────────

CHANGELOG_ENTRY = """\
- **PyPI now receives the files TestPyPI took: `publish.yml` builds once, and the run checks every upload by sha256
  against TestPyPI** (the Overtoad's directive of 2026-11-15: "deploy to pypi should send the same artifact that was
  already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy,
  might also be helpful here to prevent this from slipping through the cracks again."). The `testpypi` and `pypi` jobs
  each ran `python -m build`, so PyPI served a second build of every release: the 0.17.1 wheel is `cce2c167…` on PyPI
  and `3b8f1a84…` on TestPyPI, 0.17.0's `680c37b5…` against `2842d5b1…`, and 0.16.0's `8560d60c…` against
  `ead4708d…`, and each of those sdists differs too (both indexes' JSON, read on 2026-11-15). A port of
  juniper-cascor#763 and #767, whose template steps it copies verbatim.
  - **Build once.** A new job, `Build and Validate`, runs the commands both publish jobs ran (`pip install build
    twine`, `python -m build`, `twine check dist/*`) once, records `SHA256SUMS`, and uploads `dist/` and `SHA256SUMS`
    as one artifact, `juniper-data-dist`, kept 90 days so it outlives the `pypi` gate (at most 30 days) and the 30-day
    re-run window. Its guard, `startsWith(github.event.release.tag_name, 'v')`, matches all 15 juniper-data release
    tags and the guard `publish-image.yml` applies to the same release event; a dispatch has no release tag, so it
    builds nothing. On a re-run attempt its first step, `Reuse an earlier attempt's artifact`, finds the run's
    artifact and skips every later step: download-artifact takes the newest artifact of a name, so a rebuild would
    become the file PyPI receives.
  - **TestPyPI.** `Publish to TestPyPI` checks the downloaded files against `SHA256SUMS`, uploads them, and requires
    TestPyPI's JSON for the version to list exactly those files with those sha256. It polls up to 20 times, 15 s
    apart, while a file is missing, and fails at once on another sha256 or a file the run did not build. The install
    check follows, unchanged.
  - **PyPI.** `Publish to PyPI` keeps its `pypi` environment and gate and no longer checks out or builds anything. It
    checks the same artifact against `SHA256SUMS`, checks TestPyPI's JSON again, uploads, and checks PyPI's JSON.
  - **Only the jobs that upload hold `id-token: write`.** The workflow-level grant becomes `permissions: {}`.
    `Build and Validate` gets `contents: read` and `actions: read`, `Publish to TestPyPI` `contents: read` and
    `id-token: write`, and `Publish to PyPI` `id-token: write`, so the build, which runs the build backend, can mint no
    OIDC token.
  - **Recovery, in the Overtoad's order (ruling of 2026-11-15).** A `workflow_dispatch` from the release tag with
    `republish_from_testpypi` runs only the new job `Republish the tested files (dispatch only)`, behind the same
    `pypi` gate. It builds nothing: it downloads the version's files from TestPyPI, checks each against TestPyPI's JSON
    and, while the release run's artifact exists, against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. If
    that fails, within 30 days of the release run, "Re-run failed jobs" on it; after that, cut a new patch version.
    Never "Re-run all jobs". A dispatch runs the workflow file at its tag, so a tag cut before this change has no
    republish dispatch.
  - **`notify-consumers` is unchanged** and still runs only after the `pypi` job of a release run. A republish
    dispatch skips it, because it needs `pypi` and sends the release's tag; `docs/ci_cd/CICD_MANUAL.md` gives the
    `gh workflow run notify-consumers.yml` command that re-sends it.
  - Unchanged too: the `release: published` trigger (no `push: tags`), the `testpypi` and `pypi` environments, the job
    names `Publish to TestPyPI` and `Publish to PyPI` (juniper-ml's release-train ceremony tells the publish jobs apart
    by them), the build commands, the install check, and `publish-image.yml`. A build failure now fails
    `Build and Validate` rather than `Publish to TestPyPI`.
  - **Pins**: the new `juniper_data/tests/unit/test_publish_one_artifact.py` ({cases} cases), ported from
    juniper-cascor's. The static cases pin the wiring, each job's exact steps in order, what the workflow kept, and
    each template step and the republish job, by digest, to juniper-cascor's `publish.yml` at `675884888f5a`. That is
    a snapshot: a template change in juniper-cascor must be re-ported here and the digests updated with it. The
    rehearsals run each template step's own Python, extracted from `publish.yml`, against a stand-in index and GitHub
    API on 127.0.0.1. {mutations} mutations of the workflow, applied one at a time, each fail it.
    `test_notify_consumers_dispatch.py` passes unchanged. `test_testpypi_install_verify.py` passes too, and gains a
    comment on its tag-without-`v` case: the build's guard now keeps such a tag from a release run's install check,
    and the case stays because it pins the step's own `${VERSION#v}`, which strips at most one `v` and needs none.
  - Docs: `docs/ci_cd/CICD_MANUAL.md` (0.4.9) § One artifact, checked against TestPyPI and § Recovering a release that
    did not reach PyPI; `docs/ci_cd/CICD_REFERENCE.md` (0.4.8), `docs/REFERENCE.md` (0.4.12),
    `docs/ci_cd/CICD_QUICK_START.md` (0.4.6) and `docs/DEVELOPER_CHEATSHEET.md` (0.4.8).

"""


def changelog(text: str, cases: str, mutations: str) -> str:
    """Put the entry first under ``[Unreleased]``'s ``### Fixed`` (creating the heading if a release emptied it)."""
    if text.count("## [Unreleased]\n") != 1:
        raise Refused("CHANGELOG.md: no single '## [Unreleased]' heading")
    start = text.index("## [Unreleased]\n")
    end = text.find("\n## [", start + 1)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    entry = CHANGELOG_ENTRY.replace("{cases}", cases).replace("{mutations}", mutations)
    if section.count("\n### Fixed\n\n") == 1:
        new_section = section.replace("\n### Fixed\n\n", "\n### Fixed\n\n" + entry, 1)
    elif "\n### Fixed\n" not in section:
        new_section = section.rstrip("\n") + "\n\n### Fixed\n\n" + entry
    else:
        raise Refused("CHANGELOG.md: '### Fixed' under [Unreleased] is not followed by one blank line")
    return text[:start] + new_section + text[end:]


# ── docs ───────────────────────────────────────────────────────────────────────────────────────────────────────────

MANUAL_LADDER_LINK = "[Recovering a release that did not reach PyPI](#recovering-a-release-that-did-not-reach-pypi)"
CASCOR_MANUAL = "https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md"
REPUBLISH_COMMAND = "gh workflow run publish.yml --repo pcalnon/juniper-data --ref v<version> -f republish_from_testpypi=true"
NOTIFY_COMMAND = "gh workflow run notify-consumers.yml --repo pcalnon/juniper-data --ref v<version> -f version=<version>"

MANUAL_STAGE_0 = """\
#### Stage 0: Build and Validate

1. On a re-run attempt, `Reuse an earlier attempt's artifact` looks for this run's `juniper-data-dist` and, when it finds one, skips every later step: a re-run does not rebuild once an artifact exists (a first attempt that failed before its upload leaves none, and its re-run builds)
2. Build package with `python -m build` and validate with `twine check dist/*`
3. `Record SHA256SUMS`, then `Upload dist artifacts`: `dist/` and `SHA256SUMS` as one artifact, `juniper-data-dist`, kept 90 days (the `pypi` gate may wait 30)

No environment and no `id-token`, so the build cannot mint a publishing token. Its guard, `startsWith(github.event.release.tag_name, 'v')`, gates the whole pipeline: every juniper-data release tag is `v<version>`, and a dispatch has no release tag, so it builds nothing.

"""

MANUAL_SECTIONS = f"""\

#### One artifact, checked against TestPyPI

Until 2026-11-15 the `testpypi` and `pypi` jobs each ran `python -m build`, so PyPI served a second build of every release: the 0.17.1 wheel is `cce2c167…` on PyPI and `3b8f1a84…` on TestPyPI, 0.17.0's `680c37b5…` against `2842d5b1…`, and 0.16.0's `8560d60c…` against `ead4708d…`; their sdists differ too. The Overtoad's directive (2026-11-15): "deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again."

Now both publish jobs upload the build job's artifact, and each checks it against `SHA256SUMS` first. TestPyPI's JSON must list exactly those files and sha256 after the TestPyPI upload, before the install check, and again before the PyPI upload; PyPI's JSON must list them after the PyPI upload. An index never takes a second file under a name it already holds, so TestPyPI's record witnesses what the install check tested. Only the jobs that upload hold `id-token: write`: the workflow grants nothing (`permissions: {{}}`), `Build and Validate` holds `contents: read` and `actions: read`, `Publish to TestPyPI` `contents: read` and `id-token: write`, `Publish to PyPI` `id-token: write`, the republish job `actions: read` and `id-token: write`, and `notify-consumers` nothing.

The steps marked `One-artifact publish template`, and the whole `republish` job, are juniper-cascor's `publish.yml` copied verbatim (juniper-cascor#763 and #767). They read nothing from this repository but the workflow `env` values `PUBLISH_PACKAGE` (`juniper-data`) and `PUBLISH_DIST_DIR` (`dist`), each JSON check's `INDEX_URL`, and the runner's own variables. `juniper_data/tests/unit/test_publish_one_artifact.py` pins the wiring and each job's exact steps, rehearses each template step's own Python, and pins each template step and the republish job, by digest, to juniper-cascor's `publish.yml` at `675884888f5a`, the commit this port copied. Those digests are a snapshot, not a link: a template change in juniper-cascor must be re-ported here and the digests updated with it. The contract in full: juniper-cascor's [MANUAL § One Artifact, Checked Against TestPyPI]({CASCOR_MANUAL}#one-artifact-checked-against-testpypi).

#### Recovering a release that did not reach PyPI

The Overtoad's ladder (ruling of 2026-11-15), in this order. Every rung publishes the files TestPyPI took, or nothing:

1. **Republish TestPyPI's files.** Dispatch `publish.yml` from the release tag:

   ```bash
   {REPUBLISH_COMMAND}
   ```

   Only `Republish the tested files (dispatch only)` runs, behind the same `pypi` gate (a fresh approval, then the 5-minute timer). It builds nothing: it downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It works only from a tag whose `publish.yml` carries the job, so not from a tag cut before this change.
2. **If that fails, within 30 days of the release run: "Re-run failed jobs"** on the release run. The re-run reuses the run's artifact and waits at the gate again. GitHub refuses a re-run after 30 days.
3. **Otherwise, cut a new patch version.**

**Never "Re-run all jobs"** on a publish run, nor `gh run rerun <id>` without `--failed`. download-artifact takes the newest artifact of a name, so a re-run build became the file every later job uploaded: juniper-ml's run 38045867684 published a rebuild of juniper-ci-tools 0.9.1 that way. The build job's reuse step now skips such a rebuild, but a tag cut before this change lacks it. The ladder in full: juniper-cascor's [MANUAL § Recovering a Release That Did Not Reach PyPI]({CASCOR_MANUAL}#recovering-a-release-that-did-not-reach-pypi).

**A republish does not notify consumers.** `notify-consumers` needs the `pypi` job, which a dispatch skips, and sends the release event's tag, which a dispatch lacks. Once the republish run's `Verify PyPI serves exactly these files` passes, re-send from the same tag, so the payload's `sha` is the tag's commit, as a release run's would be:

```bash
{NOTIFY_COMMAND}
```
"""

MANUAL_TROUBLE = f"""\
**A publish sha256 check fails**: `Verify the dist against SHA256SUMS` means the downloaded `dist/` holds a file the build did not record, or misses or alters one: re-run the failed jobs, and if it fails again do not publish that artifact. `Verify TestPyPI serves exactly these files` (TestPyPI job) or `Verify TestPyPI still serves exactly these files` (PyPI job, before its upload) failing at once means TestPyPI lists a file this run did not build, or one with another sha256, usually an earlier upload of the same version: nothing has reached PyPI, so do not publish this version from this run. `Verify PyPI serves exactly these files` runs after the PyPI upload, so when it fails the files are already on PyPI: compare PyPI's JSON for the version with the run's `SHA256SUMS` (TestPyPI's JSON holds the same digests), and if they differ, cut a new patch version, since PyPI never takes a file name twice. A JSON check that gives up after 20 attempts is index lag (19 sleeps of 15 seconds, plus up to 20 request timeouts of 30 seconds): use **Re-run failed jobs**, since an index accepts a re-upload of identical files. See {MANUAL_LADDER_LINK}.

"""


def manual(text: str) -> str:
    where = "docs/ci_cd/CICD_MANUAL.md"
    text = replace_once(text, "**Version:** 0.4.8\n**Status:** Active\n**Last Updated:** November 15, 2026\n", "**Version:** 0.4.9\n**Status:** Active\n**Last Updated:** November 15, 2026\n", where)
    text = replace_once(
        text,
        "| `publish.yml`         | No                   | No                  | No            | No                  | Yes     | No     |\n",
        "| `publish.yml`         | No                   | No                  | No            | No                  | Yes     | Republish only, from a release tag |\n",
        where,
    )
    text = replace_once(
        text,
        "Two-stage publishing triggered by GitHub Release creation.\n",
        "Triggered by a published GitHub Release whose tag starts with `v`. The package is built once, and TestPyPI and then production PyPI publish that one artifact, each upload checked by sha256: see [One artifact, checked against TestPyPI](#one-artifact-checked-against-testpypi). A `workflow_dispatch` from a release tag only republishes TestPyPI's files: see " + MANUAL_LADDER_LINK + ".\n",
        where,
    )
    text = replace_once(text, "#### Stage 1: TestPyPI\n", MANUAL_STAGE_0 + "#### Stage 1: TestPyPI\n", where)
    text = replace_once(
        text,
        "1. Build package with `python -m build`\n2. Validate with `twine check dist/*`\n3. Publish to TestPyPI via `pypa/gh-action-pypi-publish` (OIDC trusted publishing)\n",
        "1. Download `juniper-data-dist` and check `dist/` against `SHA256SUMS`: exactly the recorded files, with their sha256\n"
        "2. Publish to TestPyPI via `pypa/gh-action-pypi-publish` (OIDC trusted publishing), with no `skip-existing`\n"
        "3. `Verify TestPyPI serves exactly these files`: TestPyPI's JSON for the version must list exactly those files with those sha256. A file not listed yet is index lag, polled up to 20 times 15 seconds apart; a file listed with another sha256, or one this run did not build, fails at once\n",
        where,
    )
    text = replace_once(
        text,
        "Builds and checks the package again, then publishes to production PyPI. There is no install check.\n",
        "Downloads the same `juniper-data-dist`, checks it against `SHA256SUMS`, checks TestPyPI's JSON again (`Verify TestPyPI still serves exactly these files`), publishes to production PyPI, then checks PyPI's JSON (`Verify PyPI serves exactly these files`). It checks out and builds nothing. There is no install check.\n",
        where,
    )
    text = replace_once(text, "the build takes it from `pyproject.toml`.\n", "the build takes it from `pyproject.toml`, and the sha256 checks from the file names in `SHA256SUMS`.\n", where)
    text = replace_once(
        text,
        "The `notify-consumers` job runs only after `pypi` succeeds. A failed notification does not unpublish the release. See the next section.\n",
        "The `notify-consumers` job runs only after `pypi` succeeds, so a republish dispatch never runs it. A failed notification does not unpublish the release. See [notify-consumers.yml -- Consumer release notification](#notify-consumersyml----consumer-release-notification).\n" + MANUAL_SECTIONS,
        where,
    )
    text = replace_once(
        text,
        "3. **TestPyPI stage**: Build, verify, publish, install-test (no environment wait; the job sleeps 30 seconds before the install check)\n4. **PyPI stage**: Same process, requires manual reviewer approval\n",
        "3. **Build, then TestPyPI stage**: `Build and Validate` builds once and uploads `juniper-data-dist` with its `SHA256SUMS`; the TestPyPI job checks the artifact, publishes it, requires TestPyPI's JSON to list exactly those sha256, then install-tests (no environment wait; the job sleeps 30 seconds before the install check)\n"
        "4. **PyPI stage**: requires manual reviewer approval, then publishes the same artifact after checking TestPyPI's JSON again, and checks PyPI's JSON. Nothing is rebuilt. If it never succeeds, follow " + MANUAL_LADDER_LINK + "\n",
        where,
    )
    anchor = "`import juniper_data` is the wrong check (`dotenv` is not installed). See [TestPyPI install check](../REFERENCE.md#testpypi-install-check).\n\n"
    text = replace_once(text, anchor, anchor + MANUAL_TROUBLE, where)
    return text


CICD_REFERENCE_JOBS_OLD = (
    "| `testpypi` | -- | `testpypi` | Publish to TestPyPI, then install `juniper-data==<version>` from `https://test.pypi.org/simple/` only (`--no-deps`). The next line prints installed metadata; it does not compare it with the tag. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check) |\n"
    "| `pypi` | testpypi | `pypi` | Publish to production PyPI |\n"
    "| `notify-consumers` | pypi | -- (`permissions: {}`) | Call `notify-consumers.yml` with the release tag |\n"
)
CICD_REFERENCE_JOBS_NEW = (
    "| `build` | -- | -- | `Build and Validate`: build once (`python -m build`, `twine check`), record `SHA256SUMS`, upload `dist/` and `SHA256SUMS` as `juniper-data-dist` (kept 90 days). Runs only for a release tag starting with `v`, so a dispatch builds nothing; a re-run attempt reuses the run's artifact |\n"
    "| `testpypi` | build | `testpypi` | Check the artifact against `SHA256SUMS`, publish it to TestPyPI, require TestPyPI's JSON to list exactly those sha256, then install `juniper-data==<version>` from `https://test.pypi.org/simple/` only (`--no-deps`). The next line prints installed metadata; it does not compare it with the tag. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check) |\n"
    "| `pypi` | testpypi | `pypi` | Publish the same artifact to production PyPI: check it against `SHA256SUMS`, check TestPyPI's JSON again, upload, check PyPI's JSON. Builds nothing |\n"
    "| `notify-consumers` | pypi | -- (`permissions: {}`) | Call `notify-consumers.yml` with the release tag. A republish dispatch skips it |\n"
    "| `republish` | -- (dispatch only) | `pypi` | `Republish the tested files (dispatch only)`: on a `workflow_dispatch` from a release tag with `republish_from_testpypi`, copy TestPyPI's files for the version to PyPI, then check PyPI's JSON. Builds nothing. See [Recovering a release that did not reach PyPI](CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) |\n"
)


def cicd_reference(text: str) -> str:
    where = "docs/ci_cd/CICD_REFERENCE.md"
    text = replace_once(text, "**Version:** 0.4.7\n**Status:** Active\n**Last Updated:** November 14, 2026\n", "**Version:** 0.4.8\n**Status:** Active\n**Last Updated:** November 15, 2026\n", where)
    text = replace_once(text, "**Last Updated:** November 14, 2026\n**Version:** 0.4.7\n", "**Last Updated:** November 15, 2026\n**Version:** 0.4.8\n", where)
    text = replace_once(
        text,
        "| `.github/workflows/publish.yml` | PyPI publishing | GitHub Release published |\n",
        "| `.github/workflows/publish.yml` | PyPI publishing: one build, uploaded to TestPyPI then PyPI and checked by sha256 against each | GitHub Release published; `workflow_dispatch` from a release tag (republish only) |\n",
        where,
    )
    text = replace_once(text, CICD_REFERENCE_JOBS_OLD, CICD_REFERENCE_JOBS_NEW, where)
    text = replace_once(
        text,
        "`notify-consumers.yml`, `pr-base-branch-guard.yml` and `pr-budget-alarm.yml` use no action.\n",
        "`notify-consumers.yml`, `pr-base-branch-guard.yml` and `pr-budget-alarm.yml` use no action. On 2026-11-15 `publish.yml` began using `actions/upload-artifact` and `actions/download-artifact`, at the pins those rows already held (the one-artifact publish).\n",
        where,
    )
    text = replace_once(text, "`ci.yml`, `main-verify.yml`, `publish-image.yml`, `scheduled-tests.yml`, `security-scan.yml`, `sequence-safety.yml` |\n", "`ci.yml`, `main-verify.yml`, `publish-image.yml`, `publish.yml`, `scheduled-tests.yml`, `security-scan.yml`, `sequence-safety.yml` |\n", where)
    text = replace_once(text, "| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` | `publish-image.yml` |\n", "| `actions/download-artifact` | v8.0.2 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` | `publish-image.yml`, `publish.yml` |\n", where)
    text = replace_once(
        text,
        "| publish.yml | -- | `id-token: write` (OIDC) |\n",
        "| publish.yml | `{}` | Per job: `build` `contents: read`, `actions: read`; `testpypi` `contents: read`, `id-token: write` (OIDC); `pypi` `id-token: write`; `republish` `actions: read`, `id-token: write`; `notify-consumers` `{}` |\n",
        where,
    )
    text = replace_once(
        text,
        "| `pypi` | 5 minutes | Yes (the Overtoad) | The same six tag patterns | Production PyPI publishing |\n",
        "| `pypi` | 5 minutes | Yes (the Overtoad) | The same six tag patterns | Production PyPI publishing: the `pypi` job, and the `republish` job on its dispatch from a release tag |\n",
        where,
    )
    text = replace_once(
        text,
        "The one wait in that job is the `sleep 30` in `publish.yml` before the install check, for index lag.",
        "The waits in that job are for index lag: `Verify TestPyPI serves exactly these files` polls TestPyPI's JSON (up to 20 times, 15 seconds apart), then `publish.yml` sleeps 30 seconds before the install check.",
        where,
    )
    return text


def reference(text: str) -> str:
    where = "docs/REFERENCE.md"
    ladder = "[Recovering a release that did not reach PyPI](ci_cd/CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi)"
    text = replace_once(text, "**Version:** 0.4.11\n**Status:** Active\n", "**Version:** 0.4.12\n**Status:** Active\n", where)
    text = replace_once(text, "**Last Updated:** November 15, 2026\n**Version:** 0.4.11\n", "**Last Updated:** November 15, 2026\n**Version:** 0.4.12\n", where)
    text = replace_once(
        text,
        "| **Publish to PyPI** | `publish.yml` | GitHub release `published` | Build and `twine check`; TestPyPI (`testpypi` environment) and an install check; then PyPI (`pypi` environment: the Overtoad's review plus a 5-minute wait). Both by Trusted Publishing (OIDC). Then [notify consumers](#consumer-release-notification) | None |\n",
        "| **Publish to PyPI** | `publish.yml` | GitHub release `published`; manual (`workflow_dispatch` from a release tag with `republish_from_testpypi`: republish only) | `Build and Validate` builds once and records `SHA256SUMS`; TestPyPI (`testpypi` environment) takes that artifact, its JSON must list exactly those sha256, and an install check follows; then PyPI (`pypi` environment: the Overtoad's review plus a 5-minute wait) takes the same artifact after TestPyPI's JSON is checked again, and PyPI's JSON is checked. Both by Trusted Publishing (OIDC). Then [notify consumers](#consumer-release-notification). The dispatch republishes TestPyPI's files: " + ladder + " | None |\n",
        where,
    )
    text = replace_once(
        text,
        "`publish.yml`'s `testpypi` job ends with `Verify TestPyPI install`. The production `pypi` job waits on that job.",
        "`publish.yml`'s `testpypi` job ends with `Verify TestPyPI install`, after `Verify TestPyPI serves exactly these files` has matched TestPyPI's files to the sha256 the build recorded. The production `pypi` job waits on that job.",
        where,
    )
    text = replace_once(
        text,
        "The `pypi` job builds and publishes again. It does not install the package.\n",
        "The `pypi` job builds nothing: it publishes the build job's artifact, the files this check installed from, after checking TestPyPI's JSON again ([One artifact, checked against TestPyPI](ci_cd/CICD_MANUAL.md#one-artifact-checked-against-testpypi)). It does not install the package.\n",
        where,
    )
    text = replace_once(
        text,
        "| `github.event.release.tag_name`, leading `v` stripped | Does not run unless the production PyPI job succeeded |\n",
        "| `github.event.release.tag_name`, leading `v` stripped | Does not run unless the production PyPI job succeeded, so `publish.yml`'s republish dispatch never runs it: re-send with `workflow_dispatch` (" + ladder + ") |\n",
        where,
    )
    text = replace_once(
        text,
        "Both the caller job and the reusable workflow set `permissions: {}`; the workflow-level `id-token: write` on `publish.yml` is not granted here.\n",
        "Both the caller job and the reusable workflow set `permissions: {}`. `publish.yml` grants nothing at the workflow level, and `id-token: write` only to the three jobs that upload.\n",
        where,
    )
    return text


QUICK_START_ENTRY = (
    "**A release did not reach PyPI**: dispatch `publish.yml` from the release tag with `-f republish_from_testpypi=true`. It copies TestPyPI's files to PyPI behind the same approval and builds nothing. A dispatch runs the workflow file at its tag, so a tag cut before this change (2026-11-15) has no republish dispatch. If that fails, within 30 days of the release run use **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version. A republish does not notify consumers. See [Recovering a release that did not reach PyPI](CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi).\n"
    "\n"
)


def quick_start(text: str) -> str:
    where = "docs/ci_cd/CICD_QUICK_START.md"
    text = replace_once(text, "**Version:** 0.4.5\n**Status:** Active\n**Last Updated:** November 12, 2026\n", "**Version:** 0.4.6\n**Status:** Active\n**Last Updated:** November 15, 2026\n", where)
    text = replace_once(text, "**Last Updated:** November 12, 2026\n**Version:** 0.4.5\n", "**Last Updated:** November 15, 2026\n**Version:** 0.4.6\n", where)
    anchor = "Re-send with `workflow_dispatch`; do not republish. See [Consumer release notification](../REFERENCE.md#consumer-release-notification).\n\n"
    text = replace_once(text, anchor, anchor + QUICK_START_ENTRY, where)
    return text


CHEATSHEET_ROWS = (
    f"| A release did not reach PyPI (its PyPI job failed, or its approval waited past 30 days) | `Publish to PyPI` never succeeded for the version | In this order: `{REPUBLISH_COMMAND}` (copies TestPyPI's files, builds nothing; a tag cut before this change, 2026-11-15, has no republish dispatch); if that fails, within 30 days of the release run, **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version. A republish does not notify consumers: then `{NOTIFY_COMMAND}`. See [Recovering a release that did not reach PyPI](ci_cd/CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) |\n"
    "| A publish sha256 check fails | An index lists a file this run did not build, or one with another sha256; or the downloaded `dist/` is not what the build recorded | A TestPyPI check (before the PyPI upload) or the dist check failed: nothing reached PyPI, so do not publish that version from that run. `Verify PyPI serves exactly these files` runs after the PyPI upload, so the files are already on PyPI: compare PyPI's JSON with the run's `SHA256SUMS`, and if they differ, cut a new patch version. A JSON check that gives up after 20 attempts is index lag: **Re-run failed jobs**. See [One artifact, checked against TestPyPI](ci_cd/CICD_MANUAL.md#one-artifact-checked-against-testpypi) |\n"
)


def cheatsheet(text: str) -> str:
    where = "docs/DEVELOPER_CHEATSHEET.md"
    text = replace_once(text, "**Version**: 0.4.7 | **Date**: 2026-11-13 |", "**Version**: 0.4.8 | **Date**: 2026-11-15 |", where)
    anchor = "then `workflow_dispatch` the same `X.Y.Z`. Do not cut another release. See [Consumer release notification](REFERENCE.md#consumer-release-notification). |\n"
    text = replace_once(text, anchor, anchor + CHEATSHEET_ROWS, where)
    return text


INSTALL_VERIFY_OLD = '        ("v0.17.1", "0.17.1"),\n        ("0.17.1", "0.17.1"),\n'
INSTALL_VERIFY_NEW = (
    '        ("v0.17.1", "0.17.1"),\n'
    "        # No release run reaches this step with a tag that lacks the `v`: since 2026-11-15 publish.yml's build job runs\n"
    "        # only for startsWith(tag, 'v'), and every later job needs it. The case stays because it pins the step's own\n"
    "        # `${VERSION#v}`, which strips at most one `v` and needs none, should the guard or the tag convention change.\n"
    '        ("0.17.1", "0.17.1"),\n'
)


def install_verify(text: str) -> str:
    """A comment on the tag-without-``v`` case (#543's review, item 5); a comment only, so the test's AST is unchanged."""
    return replace_once(text, INSTALL_VERIFY_OLD, INSTALL_VERIFY_NEW, INSTALL_VERIFY_PATH)


def apply(tree: Path, template: str, test_file: str, cases: str, mutations: str) -> dict[str, str]:
    """Return {repo path: new text} for every file the change writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    out: dict[str, str] = {}
    current = read(WORKFLOW)
    if sha256(current) != BASE_SHA256:
        print(f"note: {WORKFLOW} moved since fefd1895; applying by anchors")
    out[WORKFLOW] = publish_workflow(current, template, read(NOTIFY))
    if (tree / TEST_PATH).exists():
        raise Refused(f"{TEST_PATH} already exists on this base")
    out[TEST_PATH] = test_file
    out[INSTALL_VERIFY_PATH] = install_verify(read(INSTALL_VERIFY_PATH))
    out["CHANGELOG.md"] = changelog(read("CHANGELOG.md"), cases, mutations)
    out["docs/ci_cd/CICD_MANUAL.md"] = manual(read("docs/ci_cd/CICD_MANUAL.md"))
    out["docs/ci_cd/CICD_REFERENCE.md"] = cicd_reference(read("docs/ci_cd/CICD_REFERENCE.md"))
    out["docs/REFERENCE.md"] = reference(read("docs/REFERENCE.md"))
    out["docs/ci_cd/CICD_QUICK_START.md"] = quick_start(read("docs/ci_cd/CICD_QUICK_START.md"))
    out["docs/DEVELOPER_CHEATSHEET.md"] = cheatsheet(read("docs/DEVELOPER_CHEATSHEET.md"))
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh clone of juniper-data (edited in place)")
    parser.add_argument("--template", required=True, type=Path, help="juniper-cascor's .github/workflows/publish.yml (the template's source)")
    parser.add_argument("--test-file", required=True, type=Path, help=f"the new {TEST_PATH}")
    parser.add_argument("--changelog-cases", default="{cases}", help="the case count the CHANGELOG entry states")
    parser.add_argument("--changelog-mutations", default="{mutations}", help="the mutation count the CHANGELOG entry states")
    parser.add_argument("--dry-run", action="store_true", help="apply every edit in memory and run the self-checks, but write nothing")
    args = parser.parse_args(argv)
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.changelog_cases, args.changelog_mutations)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    for rel, text in sorted(out.items()):
        target = args.tree / rel
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        if not args.dry_run:
            target.write_text(text, encoding="utf-8")
        print(f"{'would write' if args.dry_run else 'wrote'} {rel} ({sha256(before)[:12] if before else 'new'} -> {sha256(text)[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
