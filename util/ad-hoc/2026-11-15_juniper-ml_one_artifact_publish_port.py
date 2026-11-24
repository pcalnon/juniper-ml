#!/usr/bin/env python3
"""Port juniper-cascor's one-artifact publish to juniper-ml's seven publishers in a fresh tree, every edit asserted once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port juniper-cascor#763 / #767's one-artifact publish to juniper-ml)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (the cascor edits, whose template_blocks(),
         republish_job() and DISPATCH_NEW this imports, so every copied step is byte-identical);
         util/ad-hoc/2026-11-15_publish_port_template_identity.py (the cross-repo identity check);
         notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md

Why
---
``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree that ``main`` has since moved past silently
reverts whatever merged in between. Every edit here is therefore an exact-once anchored replacement on a fresh clone of
``main``: re-clone, re-run this, upload the result. Nothing is written unless every edit applies. The edits:

- ``.github/workflows/publish.yml`` gets juniper-cascor ``publish.yml``'s single-package shape, keeping its plain
  dispatch re-fire, its tag assertion, its two-phase TestPyPI install check and ``attestations: true``: the workflow
  ``env`` parameters, ``permissions: {}`` and per-job permissions, the template steps and the republish job (extracted
  from cascor's file, never retyped), the ``republish_from_testpypi`` input, the reuse condition on every later build
  step, no ``skip-existing``, and a PyPI job that no longer checks out or sets up Python.
- The six ``publish-<pkg>.yml`` get cascor ``publish-cascor-model.yml``'s sub-package shape, keeping their guards'
  plain dispatch, concurrency, environment URLs, ``verbose`` uploads and install checks (their PyPI jobs hold
  ``id-token: write`` alone: none checks out).
- ``tests/test_publish_one_artifact.py`` and the negative control
  ``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`` are copied in; the old pins in
  ``tests/test_publish_subpackage_workflows.py`` and ``tests/test_publish_testpypi_verify.py`` are updated;
  ``ci.yml`` and the ``main-verify.yml`` battery invoke the new suite.
- ``CHANGELOG.md``, ``AGENTS.md`` (suite count and date), ``docs/REFERENCE.md``, ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md``,
  the PyPI publish procedure and the release-train runbook state the contract and the Overtoad's recovery ladder.

The review of juniper-ml#2593 (2026-11-15) moved the base to ``main`` at 6541b2cc (juniper-ml#2592 merged) and added:
the ladder's precondition (rungs 1 and 2 only after a TestPyPI job, install check included, that succeeded or failed
only for a transient index lag; a broken package is a new patch version, never rung 1) wherever the ladder is stated,
and the real responses in the runbook's ``testpypi-verify-failed`` / ``build-failed`` rows, its ``HALT_BUILD`` /
``HALT_TESTPYPI`` terminals and §5.3; the cheatsheet's plain re-fire row replaced by the ladder; and the NITs (cascor's
publishers never set ``skip-existing``; model-core's install check reads ``_version.py``; §10.2 names the 2026-11-15
amendment). The follow-up commit is this script's output on that base with ``--date`` the push's UTC date and
``--workflow-date 2026-11-15`` (the workflows did not change again, so their header keeps the port's date).

    python3 -I util/ad-hoc/2026-11-15_juniper-ml_one_artifact_publish_port.py --tree <fresh juniper-ml clone> \\
        --template <juniper-cascor publish.yml at 675884888f5a> --test-file <test_publish_one_artifact.py> \\
        --verify-script <the negative control> [--date YYYY-MM-DD] [--workflow-date YYYY-MM-DD] [--cases N] [--mutations M]

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once or a pinned input moved (nothing
written).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CASCOR_EDITS = HERE / "2026-11-15_cascor_one_artifact_publish_edits.py"
#: The cascor edits script whose template_blocks(), republish_job() and DISPATCH_NEW are imported (its carried sha256).
CASCOR_EDITS_SHA256 = "d5e1de3fa13ddc78dc481ec2d2701ec92f9edb8d9002882e6e12b9e07e09f38f"
#: juniper-cascor's .github/workflows/publish.yml at main 675884888f5a (#767's merge): the template's source.
TEMPLATE_SHA256 = "c5bdcf4894c0903534d754de44d45dd51c491e8b3d7d004e70a37abe5c242803"
#: sha256 of each file at juniper-ml main 6541b2cc (2026-11-15; edea2eb1 plus juniper-ml#2592), the base this applies
#: to. A moved file is still edited by its anchors; the note says the result needs a second look. The runbook's
#: HALT rows this edits are #2592's, so the script no longer applies to edea2eb1.
BASE_SHA256 = {
    ".github/workflows/publish.yml": "f6da48c408acc6695f20db45f719aa2113ebb5da6d62f583b8cdd388e1436654",
    ".github/workflows/publish-ci-tools.yml": "c059f8b8e716331095279c1ea1a29b3a16fd849f16e330b1d01609fa4a185c46",
    ".github/workflows/publish-config-tools.yml": "5cfec12229a2602847b4a218a340022db3788b303bd0e21c01e10b12d048bb5b",
    ".github/workflows/publish-doc-tools.yml": "34400db57a802e87d354207308aa0412cb4ef246bea4471daaccedaf775edcd3",
    ".github/workflows/publish-model-core.yml": "569b3efb3430518be4dc03ba4ad405e4cc626d3cbb8f2fd437b7b2897a9921a1",
    ".github/workflows/publish-observability.yml": "9bc2fbc82c4bf02a9bb575c0b4e2f8538a0801f84e0923cf1abb558f4a182534",
    ".github/workflows/publish-service-core.yml": "fc0d8414441898f3f6294da9574ddc75e21be00d56ba6a869306ed57edec53d3",
    ".github/workflows/ci.yml": "788ce486b3539e26a9faf1c5d7962521b2dbb4822c3ba10c2496e1d7ac9c0c6c",
    ".github/workflows/main-verify.yml": "d696c10b8eb79c2779d54d2a79b6dec67d131b25163709ef72d98ab07c4322fe",
    "tests/test_publish_subpackage_workflows.py": "d5bf018156744e553935fd87a5460f9d858706f8d5e2b3ea4f2358ef81ba36e8",
    "tests/test_publish_testpypi_verify.py": "1357781c2f08326e20e9d10779d9b5613df9bf6ac64adbfe95517362893d9b4f",
    "CHANGELOG.md": "401e2fde2a2ae54f3bf3bd15d0c6344b2beeb9757337155ad3be6e69a527f11d",
    "AGENTS.md": "4e91a43a056ca5d5478e1e8373c512ddd4814eb9c96c98682562a2279afc99e7",
    "docs/REFERENCE.md": "69059b350412d32907b6cd2c16b8783fdf690832432baf57fe60c4e518875282",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md": "11d9f4fe9304b122b433152369a0e2e4f22dc00c9f1478030284900caf63d395",
    "notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md": "86d20ee54c56b2073fee0b0dddf1ed3be61580c76c0db451eed80b9ec004beb5",
    "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md": "9046a0ecb76505d3db84fabdd7314ad61d21545896ea07a0852e0a70e3d35c2d",
}
#: The ladder's precondition (the review of juniper-ml#2593, 2026-11-15), one wording wherever the ladder is stated.
LADDER_PRECONDITION = "Rungs 1 and 2 apply only when the release run's TestPyPI job, install check included, succeeded, or failed only for a transient index lag (TestPyPI not yet serving the upload)."
LADDER_BROKEN = 'A real install-check failure means a broken package: fix it and cut a new patch version, never rung 1, which would copy the broken files to PyPI. A failed build published nothing: "Re-run failed jobs" if the failure was transient, otherwise fix it and cut a new patch version.'
PROCEDURE_LADDER_LINK = "[PyPI publish procedure §11.8](JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md#118-one-artifact-and-recovering-a-release-that-did-not-reach-pypi)"
TEST_PATH = "tests/test_publish_one_artifact.py"
VERIFY_PATH = "util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py"
#: (file suffix, package, the dispatch block it has today, its TestPyPI skip-existing lines, its PyPI skip-existing lines)
SKIP_PLAIN = "          skip-existing: true  # tolerate an already-uploaded immutable artifact (re-run / overlap)\n"
DISPATCH_BARE = "    types: [published]\n  workflow_dispatch:\n"
SUB_PACKAGES = (
    ("ci-tools", DISPATCH_BARE, SKIP_PLAIN, SKIP_PLAIN),
    ("config-tools", DISPATCH_BARE, SKIP_PLAIN, SKIP_PLAIN),
    ("doc-tools", DISPATCH_BARE, SKIP_PLAIN, SKIP_PLAIN),
    ("model-core", DISPATCH_BARE, SKIP_PLAIN, SKIP_PLAIN),
    ("observability", "  # Manual dispatch so operators can re-fire a publish against any tag.\n  workflow_dispatch:\n", SKIP_PLAIN, SKIP_PLAIN),
    (
        "service-core",
        "  # Manual dispatch so operators can re-fire a publish (e.g. after a transient failure).\n  workflow_dispatch:\n",
        "          # Tolerate an already-uploaded version on the immutable index (a re-run, or a duplicate\n          # trigger): skip the existing file instead of failing the publish.\n          skip-existing: true\n",
        "          # Defense-in-depth: a re-run after a partial promote is a no-op rather than a 400.\n          skip-existing: true\n",
    ),
)
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
SETUP_PYTHON = "      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n"
DOWNLOAD = "      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2\n"
UPLOAD = "        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2\n"
PUBLISH_STEP = "      - name: Publish to {index}\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n"
PYPI_PERMISSIONS = "    # P4: OIDC minting lives here, not at workflow level. The job uploads the build job's artifact and checks out\n    # nothing, so it holds no `contents: read`.\n    permissions:\n      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n"
ENV_COMMENT_SUB = "  # The one-artifact publish template's two parameters (see publish.yml): the distribution's name on PyPI and\n  # TestPyPI, and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
ENV_COMMENT_META = "  # The one-artifact publish template's two parameters: the distribution's name on PyPI and TestPyPI,\n  # and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
META_GUARD = "(github.event_name == 'release' && startsWith(github.event.release.tag_name, 'v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)"
CASCOR_MANUAL = "https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md"
OWNER_DIRECTIVE = '"deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again."'


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(data: "str | bytes") -> str:
    return hashlib.sha256(data.encode("utf-8") if isinstance(data, str) else data).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:100]!r}")
    return text.replace(old, new)


def replace_n(text: str, old: str, new: str, n: int, where: str) -> str:
    count = text.count(old)
    if count != n:
        raise Refused(f"{where}: anchor matched {count} times, expected {n}: {old[:100]!r}")
    return text.replace(old, new)


def bump_version(text: str, field: str, count: int, where: str) -> tuple[str, str, str]:
    """Raise the patch number of a ``field`` line (e.g. ``**Version:** 0.6.76``) that must occur ``count`` times, all
    with one value. Returns (text, old version, new version): derived, so a ``main`` that moved still applies."""
    pattern = re.compile(rf"^{re.escape(field)} (\d+)\.(\d+)\.(\d+)$", re.M)
    found = {m.group(0) for m in pattern.finditer(text)}
    hits = len(pattern.findall(text))
    if hits != count or len(found) != 1:
        raise Refused(f"{where}: {hits} {field!r} lines with {len(found)} distinct values, expected {count} with one")
    major, minor, patch = pattern.search(text).groups()  # type: ignore[union-attr]
    old, new = f"{major}.{minor}.{patch}", f"{major}.{minor}.{int(patch) + 1}"
    return pattern.sub(f"{field} {new}", text), old, new


def set_date(text: str, field: str, count: int, date: str, where: str) -> str:
    """Set every ``field`` line (e.g. ``**Last Updated:** 2026-11-15``) to ``date``; exactly ``count`` must exist."""
    pattern = re.compile(rf"^{re.escape(field)} \d{{4}}-\d{{2}}-\d{{2}}$", re.M)
    if len(pattern.findall(text)) != count:
        raise Refused(f"{where}: {len(pattern.findall(text))} {field!r} lines, expected {count}")
    return pattern.sub(f"{field} {date}", text)


def insert_after_line(text: str, prefix: str, new_lines: str, where: str) -> str:
    """Insert ``new_lines`` after the one line that starts with ``prefix``."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(at) != 1:
        raise Refused(f"{where}: {len(at)} lines start with {prefix[:80]!r}, expected 1")
    return "".join(lines[: at[0] + 1]) + new_lines + "".join(lines[at[0] + 1 :])


def load_cascor_edits():
    """Import the cascor edits script by path, after checking it is the carried copy (a mutant would copy wrong text)."""
    if sha256(CASCOR_EDITS.read_bytes()) != CASCOR_EDITS_SHA256:
        raise Refused(f"{CASCOR_EDITS.name} is not the carried copy (sha256 {sha256(CASCOR_EDITS.read_bytes())})")
    spec = importlib.util.spec_from_file_location("cascor_one_artifact_publish_edits", CASCOR_EDITS)
    if spec is None or spec.loader is None:
        raise Refused(f"cannot load {CASCOR_EDITS}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The workflows
# ─────────────────────────────────────────────────────────────────────────────────────────────
def meta_workflow(text: str, cascor, blocks: dict[str, str], republish: str, date: str) -> str:
    """publish.yml: cascor's single-package shape, keeping the plain dispatch re-fire and juniper-ml's own steps."""
    where = "publish.yml"
    text = replace_once(text, "# Version:       0.3.0\n#\n# Date Created:  2026-02-23\n# Last Modified: 2026-08-09\n", f"# Version:       0.4.0\n#\n# Date Created:  2026-02-23\n# Last Modified: {date}\n", where)
    text = replace_once(
        text,
        "#    GitHub Actions publish pipeline for juniper-ml meta-package.\n#    Triggered by GitHub release. Publishes TestPyPI first (with two-phase\n#    install verification), then PyPI. Uses OIDC trusted publishing (no\n#    API tokens).\n",
        "#    GitHub Actions publish pipeline for juniper-ml meta-package.\n"
        "#    Triggered by GitHub release. Builds the sdist and wheel ONCE, records\n"
        "#    their sha256 in SHA256SUMS and hands both publish jobs that one\n"
        "#    artifact: TestPyPI takes it first and must then serve exactly those\n"
        "#    sha256 before the two-phase install verification runs, and PyPI takes\n"
        "#    it only after TestPyPI is checked again. Uses OIDC trusted publishing\n"
        "#    (no API tokens).\n"
        "#\n"
        "#    The steps marked \"one-artifact publish template\", and the republish\n"
        "#    job, are juniper-cascor's publish.yml copied verbatim (juniper-cascor#763\n"
        "#    and #767): they read nothing from this repository but the two `env`\n"
        "#    values below. The republish job is step 1 of the Overtoad's recovery ladder\n"
        "#    for a release that never reached PyPI (docs/REFERENCE.md § Independent\n"
        "#    Sibling Package Publish Pipelines).\n",
        where,
    )
    example = "  #   gh workflow run publish.yml --repo pcalnon/juniper-ml --ref v<version> -f republish_from_testpypi=true\n"
    dispatch = replace_once(cascor.DISPATCH_NEW, "builds nothing.\n  workflow_dispatch:\n", "builds nothing:\n" + example + "  workflow_dispatch:\n", "DISPATCH_NEW")
    text = replace_once(
        text,
        "  # Allow manual dispatch so operators can re-fire a publish against any tag\n  # (useful when a release-triggered run failed and the release is immutable\n  # or the original run is non-retriable). Run via:\n  #   gh workflow run publish.yml --repo pcalnon/juniper-ml --ref <tag>\n  workflow_dispatch:\n",
        dispatch,
        where,
    )
    text = replace_once(
        text,
        "# P4 (juniper-ml#357): `id-token: write` is scoped to the two publish jobs\n# below, NOT granted workflow-wide. The build job compiles untrusted-ish tree\n# content and has no business being able to mint a PyPI OIDC credential.\npermissions:\n  contents: read\n\njobs:\n",
        "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15): each job states what it needs, and only the\n"
        "# jobs that upload hold `id-token: write`. The build job compiles untrusted-ish tree content and has no business being\n"
        "# able to mint a PyPI OIDC credential.\n"
        "permissions: {}\n"
        "\n"
        "env:\n" + ENV_COMMENT_META + "  PUBLISH_PACKAGE: juniper-ml\n  PUBLISH_DIST_DIR: dist\n\njobs:\n",
        where,
    )
    text = replace_once(
        text,
        "    # workflow_dispatch is the manual escape hatch.\n    if: github.event_name == 'workflow_dispatch' || startsWith(github.event.release.tag_name, 'v')\n    runs-on: ubuntu-latest\n    steps:\n" + CHECKOUT + "\n",
        "    # workflow_dispatch is the manual escape hatch: a dispatch from the release tag re-fires the whole\n"
        "    # publish, unless it asks for the republish job. Both publish jobs depend on this one, so this guard\n"
        "    # gates the whole pipeline.\n"
        f"    if: {META_GUARD}\n"
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
        "      actions: read  # the reuse step lists this run's artifacts\n"
        "    steps:\n" + blocks["build/Reuse an earlier attempt's artifact"] + "\n" + CHECKOUT + REUSE_IF + "\n",
        where,
    )
    old_build_rest = (
        SETUP_PYTHON + '        with:\n          python-version: "3.12"\n\n'
        "      - name: Install build tools\n        run: pip install build twine\n\n"
        "      - name: Build package\n        run: python -m build\n\n"
        "      - name: Check package\n        run: twine check dist/*\n\n"
        "      # P3 (juniper-ml#357/#358): prove we are building a TAG, and that the tag's\n"
        "      # version matches the wheel actually built. Defense in depth -- the\n"
        "      # environment tag policy is the real control (it survives a workflow edit;\n"
        "      # this step does not), but this fails earlier and names the reason.\n"
        "      - name: Assert release tag matches built version\n"
        "        run: |\n"
        "          util/assert_release_tag.bash \\\n"
        '            --ref "${{ github.ref }}" \\\n'
        "            --dist-dir dist \\\n"
        "            --expect-prefix v\n\n"
        "      - name: Upload dist artifacts\n" + UPLOAD + "        with:\n          name: dist\n          path: dist/\n          retention-days: 7\n"
    )
    new_build_rest = (
        SETUP_PYTHON + REUSE_IF + '        with:\n          python-version: "3.12"\n\n'
        "      - name: Install build tools\n" + REUSE_IF + "        run: pip install build twine\n\n"
        "      - name: Build package\n" + REUSE_IF + "        run: python -m build\n\n"
        "      - name: Check package\n" + REUSE_IF + "        run: twine check dist/*\n\n"
        "      # P3 (juniper-ml#357/#358): prove we are building a TAG, and that the tag's\n"
        "      # version matches the wheel actually built. Defense in depth -- the\n"
        "      # environment tag policy is the real control (it survives a workflow edit;\n"
        "      # this step does not), but this fails earlier and names the reason.\n"
        "      - name: Assert release tag matches built version\n" + REUSE_IF + "        run: |\n"
        "          util/assert_release_tag.bash \\\n"
        '            --ref "${{ github.ref }}" \\\n'
        "            --dist-dir dist \\\n"
        "            --expect-prefix v\n\n" + blocks["build/Record SHA256SUMS"] + "\n" + blocks["build/Upload dist artifacts"]
    )
    text = replace_once(text, old_build_rest, new_build_rest, where)
    old_testpypi = (
        "      - name: Download dist artifacts\n" + DOWNLOAD.replace("      - uses:", "        uses:") + "        with:\n          name: dist\n          path: dist/\n\n"
        + PUBLISH_STEP.format(index="TestPyPI")
        + "          repository-url: https://test.pypi.org/legacy/\n"
        "          attestations: true\n"
        "          # TestPyPI uploads are immutable, and a re-cut Release republishes a version\n"
        "          # that already exists there (e.g. the v0.7.0 recut after the merged-namespace\n"
        "          # verify failure). Tolerate it so the rehearsal leg is a no-op instead of an\n"
        "          # immutable-upload 400 — matching the sibling publish-*.yml contract. The PyPI\n"
        "          # leg below deliberately stays STRICT: a duplicate production upload is a real\n"
        "          # error the Overtoad must see.\n"
        "          skip-existing: true\n\n"
        "      - name: Verify TestPyPI install\n"
    )
    new_testpypi = (
        blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + PUBLISH_STEP.format(index="TestPyPI")
        + "          repository-url: https://test.pypi.org/legacy/\n"
        "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n"
        "          attestations: true\n"
        "          # No skip-existing (the one-artifact publish, 2026-11-15). It made a re-cut Release a no-op here, but it\n"
        "          # kept an earlier build under the same file name silently, so the install check below could test a file\n"
        "          # PyPI would never receive. A re-cut that builds new files for a version TestPyPI holds now fails here;\n"
        "          # the republish dispatch finishes such a release.\n\n" + blocks["testpypi/Verify TestPyPI serves exactly these files"] + "\n"
        "      - name: Verify TestPyPI install\n"
    )
    text = replace_once(text, old_testpypi, new_testpypi, where)
    old_pypi = (
        "    # P4: OIDC minting lives here, not at workflow level.\n    permissions:\n      id-token: write\n      contents: read\n    environment: pypi\n    steps:\n"
        + CHECKOUT
        + "\n"
        + SETUP_PYTHON
        + '        with:\n          python-version: "3.12"\n\n'
        "      - name: Download dist artifacts\n" + DOWNLOAD.replace("      - uses:", "        uses:") + "        with:\n          name: dist\n          path: dist/\n\n"
        + PUBLISH_STEP.format(index="PyPI")
        + "          attestations: true\n"
    )
    if not text.endswith(old_pypi):
        raise Refused(f"{where}: the PyPI job's steps are not the file's last lines")
    new_pypi = (
        PYPI_PERMISSIONS
        + "    environment: pypi\n    steps:\n"
        + blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + PUBLISH_STEP.format(index="PyPI")
        + "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          attestations: true\n\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
    )
    text = replace_once(text, old_pypi, new_pypi, where)
    return text + "\n" + republish


def sub_workflow(text: str, suffix: str, dispatch_old: str, skip_testpypi: str, skip_pypi: str, cascor, blocks: dict[str, str], republish: str) -> str:
    """publish-<pkg>.yml: cascor's sub-package shape, keeping the plain dispatch re-fire and the package's own steps."""
    package = f"juniper-{suffix}"
    where = f"publish-{suffix}.yml"
    new_dispatch = cascor.DISPATCH_NEW if dispatch_old != DISPATCH_BARE else "    types: [published]\n" + cascor.DISPATCH_NEW
    text = replace_once(text, dispatch_old, new_dispatch, where)
    text = replace_once(
        text,
        "# P4 (juniper-ml#357): `id-token: write` is scoped to the two publish jobs\n# below, NOT granted workflow-wide. The build job has no business being able\n# to mint a PyPI OIDC credential.\npermissions:\n  contents: read\n",
        "# P4 (juniper-ml#357), narrowed by the one-artifact publish (2026-11-15): each job adds what it needs to this, and only\n"
        "# the jobs that upload add `id-token: write`. The build job has no business being able to mint a PyPI OIDC credential.\n"
        "permissions:\n  contents: read\n",
        where,
    )
    text = replace_once(
        text,
        "  # Belt-and-suspenders serialization keyed on the ref. The primary dedupe is the single\n  # `release: published` trigger above; `skip-existing` on the publish steps makes any residual\n  # overlap (e.g. a manual dispatch during a release) a no-op rather than an immutable-upload race.\n",
        "  # Belt-and-suspenders serialization keyed on the ref. The primary dedupe is the single\n"
        "  # `release: published` trigger above (dropping `push: tags` removes the #555 double-fire\n"
        "  # at the source); this group additionally serializes any residual overlap (e.g. a manual dispatch\n"
        "  # during a release) so two runs never race the immutable TestPyPI upload concurrently.\n",
        where,
    )
    env = "env:\n" + ENV_COMMENT_SUB + f"  PUBLISH_PACKAGE: {package}\n  PUBLISH_DIST_DIR: {package}/dist\n\n"
    text = replace_once(text, "  cancel-in-progress: false\n\njobs:\n", "  cancel-in-progress: false\n\n" + env + "jobs:\n", where)
    text = replace_once(
        text,
        "    # Run for a tag push (filtered above) or workflow_dispatch; for a `release` event, only when the\n"
        "    # release is THIS package's tag -- a release for another package (or the meta `v*` release) also\n"
        "    # fires this workflow and must be skipped. Downstream jobs `needs: build`, so this one guard\n"
        "    # gates the whole pipeline.\n"
        f"    if: github.event_name != 'release' || startsWith(github.event.release.tag_name, '{package}-v')\n",
        "    # For a `release` event, run only when the release is THIS package's tag -- a release for another\n"
        "    # package (or the meta `v*` release) also fires this workflow and must be skipped. A dispatch runs it,\n"
        "    # unless it asks for the republish job. Downstream jobs `needs: build`, so this one guard gates the\n"
        "    # whole pipeline.\n"
        f"    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
        where,
    )
    build_head_old = f"    runs-on: ubuntu-latest\n    defaults:\n      run:\n        working-directory: {package}\n    steps:\n" + CHECKOUT + "\n"
    build_head_new = (
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
        "      actions: read  # the reuse step lists this run's artifacts\n"
        f"    defaults:\n      run:\n        working-directory: {package}\n    steps:\n" + blocks["build/Reuse an earlier attempt's artifact"] + "\n" + CHECKOUT + REUSE_IF + "\n"
    )
    text = replace_once(text, build_head_old, build_head_new, where)
    for step in (SETUP_PYTHON, "      - name: Install build tools\n", "      - name: Build sdist + wheel\n", "      - name: Validate distribution metadata\n", "      - name: Assert release tag matches built version\n"):
        text = replace_once(text, step, step + REUSE_IF, where)
    old_upload = "      - name: Upload build artifacts\n" + UPLOAD + f"        with:\n          name: {package}-dist\n          path: {package}/dist/\n          if-no-files-found: error\n          retention-days: 7\n"
    text = replace_once(text, old_upload, blocks["build/Record SHA256SUMS"] + "\n" + blocks["build/Upload dist artifacts"], where)
    text = replace_once(
        text,
        "  publish-pypi:\n    name: Publish to PyPI\n    needs: publish-testpypi\n    runs-on: ubuntu-latest\n    # P4: OIDC minting lives here, not at workflow level.\n    permissions:\n      id-token: write\n      contents: read\n",
        "  publish-pypi:\n    name: Publish to PyPI\n    needs: publish-testpypi\n    runs-on: ubuntu-latest\n" + PYPI_PERMISSIONS,
        where,
    )
    old_download = DOWNLOAD + f"        with:\n          name: {package}-dist\n          path: dist/\n\n"
    old_testpypi = old_download + PUBLISH_STEP.format(index="TestPyPI") + "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: dist/\n          verbose: true\n" + skip_testpypi + "\n"
    new_testpypi = (
        blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + PUBLISH_STEP.format(index="TestPyPI")
        + "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n\n"
        + blocks["testpypi/Verify TestPyPI serves exactly these files"]
        + "\n"
    )
    text = replace_once(text, old_testpypi, new_testpypi, where)
    old_pypi = old_download + PUBLISH_STEP.format(index="PyPI") + "          packages-dir: dist/\n          verbose: true\n" + skip_pypi
    if not text.endswith(old_pypi):
        raise Refused(f"{where}: the PyPI job's download and upload are not the file's last steps")
    new_pypi = (
        blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + PUBLISH_STEP.format(index="PyPI")
        + "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
    )
    text = replace_once(text, old_pypi, new_pypi, where)
    return text + "\n" + republish


def check_workflow(rel: str, text: str, blocks: dict[str, str], republish: str) -> None:
    """Every template block and the republish job are in the file byte for byte, and the file parses."""
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise Refused(f"{rel}: the edited workflow does not parse: {exc}") from exc
    wanted = {
        "build/Reuse an earlier attempt's artifact": 1,
        "build/Record SHA256SUMS": 1,
        "build/Upload dist artifacts": 1,
        "testpypi/Verify TestPyPI serves exactly these files": 1,
        "pypi/Verify TestPyPI still serves exactly these files": 1,
    }
    for key, count in wanted.items():
        if text.count(blocks[key]) != count:
            raise Refused(f"{rel}: {key} appears {text.count(blocks[key])} times, expected {count}")
    if text.count(republish) != 1 or not text.endswith(republish):
        raise Refused(f"{rel}: the republish job is not the file's verbatim tail")
    if "skip-existing" in text.replace("No skip-existing", ""):
        raise Refused(f"{rel}: skip-existing survived")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# CI wiring and the old pins
# ─────────────────────────────────────────────────────────────────────────────────────────────
CI_SUITE = (
    "          # tests/test_publish_one_artifact.py: the one-artifact publish (the port of\n"
    "          # juniper-cascor#763 / #767; the Overtoad's directive of 2026-11-15). All 7 publishers\n"
    "          # build once and hand both publish jobs one artifact (dist + SHA256SUMS, 90 days),\n"
    "          # reused on a re-run; the dist is checked against SHA256SUMS before every upload,\n"
    "          # TestPyPI's JSON after the TestPyPI upload and again before the PyPI one, and\n"
    "          # PyPI's after; no skip-existing; id-token only on the uploading jobs; and the\n"
    "          # republish job, rung 1 of the recovery ladder. Every template step is byte-identical\n"
    "          # to the others and to juniper-cascor's; the rehearsals run each step's own Python\n"
    "          # against a stand-in index and GitHub API on 127.0.0.1. PyYAML (installed above).\n"
    "          python3 -m unittest -v tests/test_publish_one_artifact.py\n"
)


def ci_yml(text: str) -> str:
    where = "ci.yml"
    anchor = "          python3 -m unittest -v tests/test_publish_release_only_trigger.py\n"
    text = replace_once(text, anchor, anchor + CI_SUITE, where)
    return replace_once(text, "          # (tag-prefix guard, no push:tags #555 race, skip-existing, --no-deps\n", "          # (tag-prefix guard, no push:tags #555 race, no skip-existing, --no-deps\n", where)


def main_verify(text: str) -> str:
    anchor = "          python3 -m unittest -v tests/test_publish_subpackage_workflows.py\n"
    return replace_once(text, anchor, anchor + "          # One-artifact publish, all 7 publishers (mirror ci.yml).\n          python3 -m unittest -v tests/test_publish_one_artifact.py\n", "main-verify.yml")


def invoked_suites(ci_text: str) -> list[str]:
    """The suites ci.yml's regression step invokes, as tests/test_ci_test_wiring_drift.py extracts them."""
    steps = yaml.safe_load(ci_text)["jobs"]["tests"]["steps"]
    run = next(s["run"] for s in steps if s.get("name") == "Run Python regression tests")
    pattern = re.compile(r"(?<![A-Za-z0-9_./-])tests/(test_[A-Za-z0-9_]+\.py)\b")
    found = []
    for line in run.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "-m unittest" not in stripped:
            continue
        found += pattern.findall(stripped.split("#", 1)[0])
    return found


SUBPKG_DOC_OLD = "  * **skip-existing** — residual overlap (manual dispatch during a release) must\n    be a no-op, not an immutable-upload 400.\n"
SUBPKG_DOC_NEW = (
    "  * **no skip-existing** — both uploads set it until 2026-11-15, so a residual\n"
    "    overlap was a no-op; but on TestPyPI it kept an earlier build under the same\n"
    "    file name silently, and the install check tested that file. juniper-ci-tools\n"
    "    0.9.1's re-run (run 38045867684) passed TestPyPI on the first build's files and\n"
    "    sent PyPI a second build. The one-artifact checks that replace it are pinned by\n"
    "    ``tests/test_publish_one_artifact.py``.\n"
)
SUBPKG_VERIFY_OLD = "    steps = (doc.get(\"jobs\") or {}).get(\"publish-testpypi\", {}).get(\"steps\") or []\n    step = next((s for s in steps if \"Verify\" in str(s.get(\"name\") or \"\") and \"run\" in s), None)\n"
SUBPKG_VERIFY_NEW = (
    "    # The install check, by name: the one-artifact template's own \"Verify ...\" steps run Python before it.\n"
    "    steps = (doc.get(\"jobs\") or {}).get(\"publish-testpypi\", {}).get(\"steps\") or []\n"
    "    step = next((s for s in steps if str(s.get(\"name\") or \"\").startswith(\"Verify install from TestPyPI\") and \"run\" in s), None)\n"
)
SUBPKG_PERMISSIONS_OLD = '''    def test_permissions_are_oidc_plus_contents_read(self) -> None:
        """OIDC is scoped to the publish jobs; the workflow block grants only reads.

        P4 (juniper-ml#357) moved ``id-token: write`` off the workflow block --
        the build job compiles the tree and must not be able to mint a PyPI
        credential.  Job-level ``permissions`` REPLACE the workflow block rather
        than merging with it, so each publish job restates ``contents: read``.
        """
        for pkg, info in self.loaded.items():
            doc = info["doc"]
            jobs = doc.get("jobs") or {}
            with self.subTest(pkg=pkg):
                self.assertEqual(doc.get("permissions"), {"contents": "read"}, f"{pkg}: workflow-level permissions must NOT grant id-token; scope it to the publish jobs")
                for job_name in ("publish-testpypi", "publish-pypi"):
                    self.assertEqual(
                        (jobs.get(job_name) or {}).get("permissions"),
                        {"id-token": "write", "contents": "read"},
                        f"{pkg}: {job_name} must carry its own OIDC grant",
                    )
                self.assertNotIn("permissions", jobs.get("build") or {}, f"{pkg}: the build job must not be granted OIDC minting rights")
'''
SUBPKG_PERMISSIONS_NEW = '''    def test_permissions_are_oidc_plus_contents_read(self) -> None:
        """OIDC is scoped to the jobs that upload; the workflow block grants only reads.

        P4 (juniper-ml#357) moved ``id-token: write`` off the workflow block --
        the build job compiles the tree and must not be able to mint a PyPI
        credential.  Job-level ``permissions`` REPLACE the workflow block rather
        than merging with it, so each job states its own.  Since the one-artifact
        publish (2026-11-15): the build ``contents: read`` and ``actions: read``
        (its reuse step lists the run's artifacts), the TestPyPI job
        ``contents: read`` for its sparse checkout, the PyPI job, which checks
        nothing out, ``id-token: write`` alone, and the republish job
        ``actions: read`` for the release run's artifact.
        """
        expected = {
            "build": {"contents": "read", "actions": "read"},
            "publish-testpypi": {"id-token": "write", "contents": "read"},
            "publish-pypi": {"id-token": "write"},
            "republish": {"actions": "read", "id-token": "write"},
        }
        for pkg, info in self.loaded.items():
            doc = info["doc"]
            jobs = doc.get("jobs") or {}
            with self.subTest(pkg=pkg):
                self.assertEqual(doc.get("permissions"), {"contents": "read"}, f"{pkg}: workflow-level permissions must NOT grant id-token; scope it to the publish jobs")
                for job_name, permissions in expected.items():
                    self.assertEqual(
                        (jobs.get(job_name) or {}).get("permissions"),
                        permissions,
                        f"{pkg}: {job_name} must carry its own grant, and only a job that uploads may mint OIDC",
                    )
                self.assertNotIn("id-token", (jobs.get("build") or {}).get("permissions") or {}, f"{pkg}: the build job must not be granted OIDC minting rights")
'''
SUBPKG_ARTIFACT_OLD = '''    def test_artifact_path_under_subdirectory(self) -> None:
        for _suffix, pkg, subdir in SHARED_PACKAGES:
            doc = self.loaded[pkg]["doc"]
            steps = ((doc.get("jobs") or {}).get("build") or {}).get("steps") or []
            upload = next((s for s in steps if "upload-artifact" in str(s.get("uses") or "")), None)
            with self.subTest(pkg=pkg):
                self.assertIsNotNone(upload)
                with_ = upload.get("with") or {}
                self.assertEqual(with_.get("name"), f"{pkg}-dist")
                self.assertEqual(with_.get("path"), f"{subdir}/dist/")
                self.assertEqual(with_.get("if-no-files-found"), "error")
'''
SUBPKG_ARTIFACT_NEW = '''    def test_artifact_path_under_subdirectory(self) -> None:
        # The one-artifact template's upload names the artifact and its path through the workflow env (2026-11-15), so
        # resolve them: still `<pkg>-dist`, still the package subdirectory's dist/, now beside SHA256SUMS.
        for _suffix, pkg, subdir in SHARED_PACKAGES:
            doc = self.loaded[pkg]["doc"]
            env = doc.get("env") or {}
            steps = ((doc.get("jobs") or {}).get("build") or {}).get("steps") or []
            upload = next((s for s in steps if "upload-artifact" in str(s.get("uses") or "")), None)
            with self.subTest(pkg=pkg):
                self.assertIsNotNone(upload)
                self.assertEqual(env.get("PUBLISH_PACKAGE"), pkg)
                self.assertEqual(env.get("PUBLISH_DIST_DIR"), f"{subdir}/dist")
                with_ = upload.get("with") or {}
                self.assertEqual(with_.get("name"), "${{ env.PUBLISH_PACKAGE }}-dist")
                paths = [p.strip() for p in str(with_.get("path") or "").splitlines() if p.strip()]
                self.assertEqual(paths, ["${{ env.PUBLISH_DIST_DIR }}/", "SHA256SUMS"])
                self.assertEqual(paths[0].replace("${{ env.PUBLISH_DIST_DIR }}", str(env.get("PUBLISH_DIST_DIR"))), f"{subdir}/dist/")
                self.assertEqual(with_.get("if-no-files-found"), "error")
'''
SUBPKG_SKIP_OLD = '''    def test_skip_existing_on_both_publish_steps(self) -> None:
        for pkg, info in self.loaded.items():
            jobs = info["doc"].get("jobs") or {}
            with self.subTest(pkg=pkg):
                for job_name in ("publish-testpypi", "publish-pypi"):
                    pubs = _pypi_publish_steps(jobs[job_name])
                    self.assertEqual(len(pubs), 1, f"{pkg}/{job_name}: expected one pypi-publish action")
                    with_ = pubs[0].get("with") or {}
                    self.assertIs(with_.get("skip-existing"), True, f"{pkg}/{job_name}: skip-existing required (#555 residual)")
'''
SUBPKG_SKIP_NEW = '''    def test_no_skip_existing_on_either_publish_step(self) -> None:
        # The one-artifact publish (2026-11-15) dropped skip-existing from both uploads. On TestPyPI it kept an earlier
        # build under the same file name silently and the install check tested that file: juniper-ci-tools 0.9.1's
        # re-run (run 38045867684, attempt 2) passed TestPyPI on the first build's files and sent PyPI the second build.
        for pkg, info in self.loaded.items():
            jobs = info["doc"].get("jobs") or {}
            with self.subTest(pkg=pkg):
                for job_name in ("publish-testpypi", "publish-pypi"):
                    pubs = _pypi_publish_steps(jobs[job_name])
                    self.assertEqual(len(pubs), 1, f"{pkg}/{job_name}: expected one pypi-publish action")
                    with_ = pubs[0].get("with") or {}
                    self.assertNotIn("skip-existing", with_, f"{pkg}/{job_name}: skip-existing would keep an earlier upload silently")
                    self.assertNotIn("skip_existing", with_, f"{pkg}/{job_name}: the deprecated alias is the same switch")
'''
SUBPKG_LEGACY_OLD = '''    def test_testpypi_publish_targets_testpypi_legacy(self) -> None:
        for pkg, info in self.loaded.items():
            pubs = _pypi_publish_steps(info["doc"]["jobs"]["publish-testpypi"])
            with self.subTest(pkg=pkg):
                with_ = pubs[0].get("with") or {}
                self.assertEqual(with_.get("repository-url"), "https://test.pypi.org/legacy/")
                self.assertEqual(with_.get("packages-dir"), "dist/")
'''
SUBPKG_LEGACY_NEW = '''    def test_testpypi_publish_targets_testpypi_legacy(self) -> None:
        for _suffix, pkg, subdir in SHARED_PACKAGES:
            doc = self.loaded[pkg]["doc"]
            pubs = _pypi_publish_steps(doc["jobs"]["publish-testpypi"])
            with self.subTest(pkg=pkg):
                with_ = pubs[0].get("with") or {}
                self.assertEqual(with_.get("repository-url"), "https://test.pypi.org/legacy/")
                # The artifact restores into the workspace since 2026-11-15, so the files sit in the package's own dist/.
                self.assertEqual(with_.get("packages-dir"), "${{ env.PUBLISH_DIST_DIR }}/")
                self.assertEqual((doc.get("env") or {}).get("PUBLISH_DIST_DIR"), f"{subdir}/dist")
'''


def subpackage_test(text: str) -> str:
    where = "tests/test_publish_subpackage_workflows.py"
    for old, new in ((SUBPKG_DOC_OLD, SUBPKG_DOC_NEW), (SUBPKG_VERIFY_OLD, SUBPKG_VERIFY_NEW), (SUBPKG_PERMISSIONS_OLD, SUBPKG_PERMISSIONS_NEW), (SUBPKG_ARTIFACT_OLD, SUBPKG_ARTIFACT_NEW), (SUBPKG_SKIP_OLD, SUBPKG_SKIP_NEW), (SUBPKG_LEGACY_OLD, SUBPKG_LEGACY_NEW)):
        text = replace_once(text, old, new, where)
    return text


META_DOC_OLD = "     TestPyPI upload ``skip-existing`` (PyPI stays strict), the ``pypi needs: testpypi``\n"
META_DOC_NEW = "     no ``skip-existing`` on either upload (the one-artifact publish), the ``pypi needs: testpypi``\n"
META_OIDC_OLD = '''    def test_testpypi_environment_and_oidc(self) -> None:
        """Environments are declared, and OIDC is scoped to the publish jobs only.

        P4 (juniper-ml#357) moved ``id-token: write`` off the workflow block and
        onto the two publish jobs.  The build job compiles the tree and must not
        be able to mint a PyPI credential; job-level ``permissions`` REPLACE the
        workflow block rather than merging with it, so each publish job restates
        ``contents: read`` for its checkout.
        """
        self.assertEqual(self.doc["jobs"]["testpypi"].get("environment"), "testpypi")
        self.assertEqual(self.doc["jobs"]["pypi"].get("environment"), "pypi")

        self.assertEqual(self.doc.get("permissions"), {"contents": "read"}, "workflow-level permissions must NOT grant id-token; scope it to the publish jobs")

        for job in ("testpypi", "pypi"):
            with self.subTest(job=job):
                self.assertEqual(self.doc["jobs"][job].get("permissions"), {"id-token": "write", "contents": "read"})

        self.assertNotIn("permissions", self.doc["jobs"]["build"], "the build job must not be granted OIDC minting rights")
'''
META_OIDC_NEW = '''    def test_testpypi_environment_and_oidc(self) -> None:
        """Environments are declared, and OIDC is scoped to the jobs that upload.

        P4 (juniper-ml#357) moved ``id-token: write`` off the workflow block and
        onto the publish jobs.  The build job compiles the tree and must not be
        able to mint a PyPI credential; job-level ``permissions`` REPLACE the
        workflow block rather than merging with it.  Since the one-artifact
        publish (2026-11-15) the workflow block is ``{}`` and each job states its
        own: the build ``contents: read`` and ``actions: read`` (its reuse step
        lists the run's artifacts), the TestPyPI job ``contents: read`` for its
        checkout, the PyPI job, which checks nothing out, ``id-token: write``
        alone, and the republish job ``actions: read`` for the release run's
        artifact.
        """
        self.assertEqual(self.doc["jobs"]["testpypi"].get("environment"), "testpypi")
        self.assertEqual(self.doc["jobs"]["pypi"].get("environment"), "pypi")
        self.assertEqual(self.doc["jobs"]["republish"].get("environment"), "pypi")

        self.assertEqual(self.doc.get("permissions"), {}, "workflow-level permissions must grant nothing; each job states its own")

        expected = {
            "build": {"contents": "read", "actions": "read"},
            "testpypi": {"id-token": "write", "contents": "read"},
            "pypi": {"id-token": "write"},
            "republish": {"actions": "read", "id-token": "write"},
        }
        for job, permissions in expected.items():
            with self.subTest(job=job):
                self.assertEqual(self.doc["jobs"][job].get("permissions"), permissions)

        self.assertNotIn("id-token", self.doc["jobs"]["build"].get("permissions") or {}, "the build job must not be granted OIDC minting rights")
'''
META_SKIP_OLD = '''    def test_testpypi_upload_skips_existing_but_pypi_stays_strict(self) -> None:
        # A re-cut Release republishes a version TestPyPI already holds (immutable upload).
        # TestPyPI tolerates it; production PyPI must NOT silently swallow a duplicate.
        tp_steps = self.doc["jobs"]["testpypi"]["steps"]
        tp_pub = next(s for s in tp_steps if str(s.get("uses", "")).startswith("pypa/gh-action-pypi-publish"))
        self.assertIs(
            (tp_pub.get("with") or {}).get("skip-existing"),
            True,
            "TestPyPI upload must set skip-existing: true so a Release recut is a no-op, not a 400.",
        )
'''
META_SKIP_NEW = '''    def test_neither_upload_skips_existing(self) -> None:
        # Until 2026-11-15 the TestPyPI upload set skip-existing so a re-cut Release was a no-op. It kept an earlier
        # build under the same file name silently, and Gate 1 then verified that file rather than the one PyPI would
        # receive. The one-artifact publish dropped it: both uploads take the build job's artifact, and a re-cut that
        # builds new files for a version TestPyPI holds now fails at the upload. Production PyPI stays STRICT, as before.
        tp_steps = self.doc["jobs"]["testpypi"]["steps"]
        tp_pub = next(s for s in tp_steps if str(s.get("uses", "")).startswith("pypa/gh-action-pypi-publish"))
        self.assertNotIn(
            "skip-existing",
            (tp_pub.get("with") or {}),
            "TestPyPI upload must not skip an existing file: the install check would then test an earlier build.",
        )
'''


def meta_test(text: str) -> str:
    where = "tests/test_publish_testpypi_verify.py"
    for old, new in ((META_DOC_OLD, META_DOC_NEW), (META_OIDC_OLD, META_OIDC_NEW), (META_SKIP_OLD, META_SKIP_NEW)):
        text = replace_once(text, old, new, where)
    return text


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The docs
# ─────────────────────────────────────────────────────────────────────────────────────────────
CHANGELOG_ENTRY = """\
- **PyPI now receives the files TestPyPI took, checked by sha256, in all seven publishers** (`publish.yml` and the six
  `publish-<pkg>.yml`; the port of juniper-cascor#763 and #767). The Overtoad's directive of 2026-11-15: "deploy to pypi
  should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after
  testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks
  again." Each publisher handed both publish jobs one artifact, but nothing checked it, and a re-run broke it:
  juniper-ci-tools 0.9.1's run 38045867684, attempt 1, failed at `Publish to PyPI`'s download on day 11, because the
  7-day artifact had expired before the `pypi` gate was approved; attempt 2 ("Re-run all jobs") built again, its
  TestPyPI upload passed under `skip-existing` while TestPyPI kept the first build, and PyPI took the second. PyPI
  serves that wheel as `1dc8e01e…`, TestPyPI as `ade363e8…`.
  - **juniper-cascor's template, copied verbatim.** The steps marked `One-artifact publish template` and the whole
    `republish` job are byte-identical to juniper-cascor's `publish.yml` at `675884888f5a`. They read only the workflow
    `env` values `PUBLISH_PACKAGE` and `PUBLISH_DIST_DIR`, a step's `INDEX_URL`, and the runner's own variables.
  - **Build once, and reuse it on a re-run.** `Build and Validate` keeps its build, check and tag-assertion steps,
    then records `SHA256SUMS` and uploads it with the dist directory as one artifact, `<package>-dist` (the
    meta-package's was `dist`, which nothing else reads), kept 90 days instead of 7: longer than the `pypi` gate's
    30-day cap and the 30-day re-run window. Its new first step, `Reuse an earlier attempt's artifact`, skips every
    later build step when the run already holds that artifact, so "Re-run all jobs" can no longer make a rebuild the
    file both publish jobs take.
  - **The checks.** Each publish job checks the files against `SHA256SUMS` before it uploads them. After the TestPyPI
    upload, TestPyPI's JSON for the version must list exactly those files with those sha256, before the install check
    runs; the PyPI job checks TestPyPI's JSON again before its own upload, and PyPI's after. No upload sets
    `skip-existing`: on TestPyPI it kept an earlier build silently, and the install check tested that file.
  - **Permissions.** Only the jobs that upload hold `id-token: write`. `publish.yml`'s workflow block is now `{}`; the
    sub-packages' stays `contents: read`. The build holds `contents: read` and `actions: read`, the TestPyPI job
    `contents: read` and `id-token: write`, every PyPI job `id-token: write` alone (none checks out; `publish.yml`'s
    no longer checks out or sets up Python), and the republish job `actions: read` and `id-token: write`.
  - **The Overtoad's recovery ladder (2026-11-15)** for a release that did not reach PyPI: (1) dispatch its workflow from
    the release tag with `-f republish_from_testpypi=true`, which runs only `Republish the tested files (dispatch
    only)`: behind the same `pypi` gate it copies TestPyPI's files for the version to PyPI, checked against TestPyPI's
    JSON and the release run's `SHA256SUMS`, and builds nothing; (2) if that fails, within 30 days of the release run,
    "Re-run failed jobs" on it, never "Re-run all jobs"; (3) otherwise, a new patch version. Rungs 1 and 2 apply only
    when the release run's TestPyPI job, install check included, succeeded or failed only for a transient index lag; a
    real install-check failure means a broken package, which ships fixed as a new patch version and never through
    rung 1. A dispatch without the input still re-fires the whole publish from the tag; it builds again, so it works
    only while TestPyPI does not hold the version yet.
  - Unchanged: the `release: published` trigger and the tag guards, the workflow names (each ends in "to PyPI", which
    the ceremony's monitor requires since juniper-ml#2592), the job names `Publish to TestPyPI` and `Publish to PyPI`
    (`util/release_train/ceremony.py` tells the jobs apart by them; the republish job's name carries no "pypi", so a
    republish dispatch, which the monitor also reads since juniper-ml#2592, is classified by its run's status alone),
    the environments, `publish.yml`'s two-phase install check and `attestations: true`, and the sub-packages'
    concurrency groups, environment URLs, `verbose` uploads and install checks.
  - Pins: `tests/test_publish_one_artifact.py` (new, {cases} cases, unittest; wired into `ci.yml` and the
    `main-verify.yml` battery) pins that wiring in all seven workflows, each job's exact steps and conditions (no
    `if:` beyond the template's, no `continue-on-error`), the 90-day artifact, the workflow and job names the release
    train reads, that `publish*.yml` holds no eighth publisher, what each workflow kept, and every template step
    byte-identical to the others and to juniper-cascor's. Its rehearsals run each template step's own Python against a
    stand-in index and GitHub API on 127.0.0.1. The old pins in `tests/test_publish_subpackage_workflows.py` and
    `tests/test_publish_testpypi_verify.py` now pin no `skip-existing` and the per-job permissions. The negative
    control, `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`, makes {mutations}
    mutations of a copy of the workflows, each undoing one property (two add an eighth publisher), and the tests catch
    every one.
  - Docs: `docs/REFERENCE.md` (§ Meta-Package Publish Pipeline and § Independent Sibling Package Publish Pipelines, with
    each workflow's republish command), `notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md` (§10.3
    and the new §11.8: the contract and the ladder for every Juniper repository),
    `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md` (§5.5, and the responses in §4,
    §4.1 and §5.3, which said to fix and re-cut: a transient failure is "Re-run failed jobs", a broken package a new
    patch version), and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (the ladder replaces its plain re-fire row).
"""


def changelog(text: str, cases: str, mutations: str) -> str:
    """Append the entry to the end of ``[Unreleased]``'s ``### Fixed`` (creating the heading if a release emptied it)."""
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise Refused("CHANGELOG.md: no single '## [Unreleased]' heading")
    end = text.find("\n## [", start + 1)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    entry = CHANGELOG_ENTRY.replace("{cases}", cases).replace("{mutations}", mutations)
    fixed = section.find("\n### Fixed\n")
    if fixed < 0:
        new_section = section.rstrip("\n") + "\n\n### Fixed\n\n" + entry + "\n"
    else:
        after = section.find("\n### ", fixed + 1)
        cut = len(section) if after < 0 else after + 1
        new_section = section[:cut].rstrip("\n") + "\n\n" + entry + "\n" + section[cut:]
    return text[:start] + new_section + text[end:]


def agents_md(text: str, old_count: int, new_count: int, date: str) -> str:
    text = replace_once(text, f"the full ordered list of {old_count} `python3 -m unittest`", f"the full ordered list of {new_count} `python3 -m unittest`", "AGENTS.md")
    return set_date(text, "**Last Updated**:", 1, date, "AGENTS.md")


LADDER_COMMANDS = """\
   ```bash
   gh workflow run publish.yml               --repo pcalnon/juniper-ml --ref v<version>                       -f republish_from_testpypi=true
   gh workflow run publish-ci-tools.yml      --repo pcalnon/juniper-ml --ref juniper-ci-tools-v<version>      -f republish_from_testpypi=true
   gh workflow run publish-config-tools.yml  --repo pcalnon/juniper-ml --ref juniper-config-tools-v<version>  -f republish_from_testpypi=true
   gh workflow run publish-doc-tools.yml     --repo pcalnon/juniper-ml --ref juniper-doc-tools-v<version>     -f republish_from_testpypi=true
   gh workflow run publish-model-core.yml    --repo pcalnon/juniper-ml --ref juniper-model-core-v<version>    -f republish_from_testpypi=true
   gh workflow run publish-observability.yml --repo pcalnon/juniper-ml --ref juniper-observability-v<version> -f republish_from_testpypi=true
   gh workflow run publish-service-core.yml  --repo pcalnon/juniper-ml --ref juniper-service-core-v<version>  -f republish_from_testpypi=true
   ```
"""

REFERENCE_LADDER = (
    "#### One artifact, and recovering a release that did not reach PyPI\n"
    "\n"
    "All seven publishers carry juniper-cascor's one-artifact template (juniper-cascor#763 and #767, ported 2026-11-15; the Overtoad's directive of 2026-11-15: " + OWNER_DIRECTIVE + "). "
    "The steps marked `One-artifact publish template` and the whole `republish` job are byte-identical to juniper-cascor's `publish.yml`, and read only the workflow `env` values `PUBLISH_PACKAGE` and `PUBLISH_DIST_DIR`. "
    f"The contract: [juniper-cascor `MANUAL.md` § One Artifact, Checked Against TestPyPI]({CASCOR_MANUAL}#one-artifact-checked-against-testpypi).\n"
    "\n"
    "- **Build once.** The build job records `SHA256SUMS` and uploads the dist directory and `SHA256SUMS` as one artifact, `<pkg>-dist`, kept 90 days, longer than the `pypi` gate's 30-day cap. On a re-run attempt its first step, `Reuse an earlier attempt's artifact`, skips every later build step while the run holds that artifact.\n"
    "- **Check every upload.** Each publish job checks the files against `SHA256SUMS` before it uploads them. TestPyPI's JSON must list exactly those files with those sha256 after the TestPyPI upload, before the install check, and again before the PyPI upload; PyPI's JSON after it.\n"
    "- **No `skip-existing`, and `id-token: write` only on the uploading jobs.** A TestPyPI upload that skips an existing file lets the install check test an earlier build than the one PyPI takes.\n"
    "\n"
    "Why: juniper-ci-tools 0.9.1's run 38045867684. Its 7-day artifact expired before the `pypi` gate was approved on day 11, so `Publish to PyPI` failed at its download; \"Re-run all jobs\" then built again, the `skip-existing` TestPyPI upload kept the first build, and PyPI took the second (`1dc8e01e…` on PyPI, `ade363e8…` on TestPyPI).\n"
    "\n"
    f"A release that did not reach PyPI is recovered by the Overtoad's ladder (ruling of 2026-11-15; [juniper-cascor `MANUAL.md` § Recovering a Release That Did Not Reach PyPI]({CASCOR_MANUAL}#recovering-a-release-that-did-not-reach-pypi)). **" + LADDER_PRECONDITION + "** " + LADDER_BROKEN + " The ladder, in this order:\n"
    "\n"
    "1. **Republish TestPyPI's files.** Dispatch the release's own workflow from its tag with `republish_from_testpypi`. Only `Republish the tested files (dispatch only)` runs: it waits at the `pypi` gate (a fresh approval, then the 5-minute timer), builds nothing, downloads the version's files from TestPyPI, checks each against TestPyPI's JSON and, while the release run's artifact exists, its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It needs a tag cut after this change merged.\n"
    "\n" + LADDER_COMMANDS + "\n"
    "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run (`gh run rerun <run-id> --repo pcalnon/juniper-ml --failed`). The re-run reuses the run's artifact and waits at the `pypi` gate again. GitHub refuses a re-run after 30 days.\n"
    "3. **Otherwise, cut a new patch version.**\n"
    "\n"
    "**Never \"Re-run all jobs\"** on a publish run, nor `gh run rerun <run-id>` without `--failed`. A dispatch without the input (`gh workflow run <workflow> --repo pcalnon/juniper-ml --ref <tag>`) re-fires the whole publish and builds new files, so it is only for a failure before TestPyPI took the version: TestPyPI refuses a different build under a file name it holds. Every dispatch runs from the release tag; both environments admit release tags only.\n"
)

REFERENCE_SUITE = (
    "- `tests/test_publish_one_artifact.py` -- The one-artifact publish in all seven publishers (the port of juniper-cascor#763 / #767; the Overtoad's directive of 2026-11-15): PyPI takes exactly the files TestPyPI took, checked by sha256.\n"
    "  - Static cases pin, in every workflow: one build, in `Build and Validate`, with no environment and no `id-token`; the job chain, and the workflow name (`... to PyPI`) and two job names `util/release_train/ceremony.py` reads; per-job permissions (only the uploading jobs mint OIDC; no PyPI job checks out); the reuse step first, and every later build step skipped when it reuses; the dist check before every upload; TestPyPI's JSON after the TestPyPI upload and before the install check, again before the PyPI upload, and PyPI's after; no `skip-existing`; the `<pkg>-dist` artifact (dist directory and `SHA256SUMS`, kept 90 days, longer than the 30-day gate); each job's exact steps, with no `if:` beyond the template's and no `continue-on-error` on any job or step; and the republish job's trigger, gate, steps and name, which carries no \"pypi\". Every `publish*.yml`, and every workflow that uploads to an index, must be one of the seven, so an eighth publisher cannot go unchecked.\n"
    "  - `TestUnchanged` pins what each workflow kept: triggers, tag guards (a plain dispatch still re-fires the whole publish), build commands and the tag assertion, `publish.yml`'s checkout before the download, two-phase install check and `attestations: true`, and the sub-packages' concurrency, environment URLs, `verbose` uploads and sparse-checkout install check.\n"
    "  - `TestTemplate` holds every copy of a template step byte-identical to the others and, by sha256, to juniper-cascor's `publish.yml` at `675884888f5a`: a fix to the template is made there and copied here.\n"
    "  - The rehearsals run each template step's own Python, extracted from `publish.yml`, against a stand-in index, file host and GitHub API on 127.0.0.1. Negative control: `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py` ({mutations} mutations, each caught).\n"
)


def reference(text: str, suites: int, date: str, mutations: str) -> str:
    where = "docs/REFERENCE.md"
    text, old_version, new_version = bump_version(text, "**Version:**", 2, where)
    text = set_date(text, "**Last Updated:**", 2, date, where)
    text = replace_once(text, "(the port of juniper-data#530). The drift script above counts", f"(the port of juniper-data#530), **{suites}** on {date} with the one-artifact publish's `tests/test_publish_one_artifact.py` (the port of juniper-cascor#763 / #767). The drift script above counts", where)
    anchor = "python3 -m unittest -v tests/test_publish_release_only_trigger.py\n"
    text = replace_once(text, anchor, anchor + "python3 -m unittest -v tests/test_publish_one_artifact.py\n", where)
    text = replace_once(text, ", the `v*` tag guard, TestPyPI `skip-existing` vs strict PyPI, and `pypi needs: testpypi`.", ", the `v*` tag guard, no `skip-existing` on either upload (the one-artifact publish), the per-job permissions, and `pypi needs: testpypi`.", where)
    anchor = "  `workflow_dispatch` stays as the deliberate escape hatch.\n"
    text = replace_once(text, anchor, anchor + REFERENCE_SUITE.replace("{mutations}", mutations), where)
    text = insert_after_line(text, "│   ├── test_publish_release_only_trigger.py # Glob gate", "│   ├── test_publish_one_artifact.py      # Structural + rehearsal: all 7 publishers build once, sha256-check every upload against SHA256SUMS + TestPyPI/PyPI JSON, reuse on re-run, republish job (cascor#763/#767)\n", where)
    anchor = "Triggered on GitHub release published. Uses OIDC trusted publishing (no API tokens). Publishes to TestPyPI first, then PyPI (`pypi needs: testpypi`).\n"
    text = replace_once(text, anchor, anchor + "Since 2026-11-15 the build runs once and both publish jobs upload its one artifact, checked by sha256 against `SHA256SUMS` and against TestPyPI's and PyPI's JSON; a dispatch from the tag with `-f republish_from_testpypi=true` republishes TestPyPI's files ([§ Meta-Package Publish Pipeline](#meta-package-publish-pipeline)).\n", where)
    text = replace_once(
        text,
        "The `build` job skips `juniper-<pkg>-v*` tags. Gates: `tests/test_publish_testpypi_verify.py` (verify shape + poll) and `tests/test_publish_release_only_trigger.py` (trigger IS the release-convention gate).\n",
        "The `build` job skips `juniper-<pkg>-v*` tags. Gates: `tests/test_publish_testpypi_verify.py` (verify shape + poll), `tests/test_publish_release_only_trigger.py` (trigger IS the release-convention gate) and `tests/test_publish_one_artifact.py` (one artifact, its sha256 checks and the republish job).\n",
        where,
    )
    text = replace_once(
        text,
        "3. **P4 job-scoped `id-token`** — `id-token: write` sits on the two publish jobs, never the workflow block, so the build job cannot mint a PyPI credential at all. Job-level `permissions` **replace** the workflow block rather than merging, so each publish job restates `contents: read` for its checkout.\n",
        "3. **P4 job-scoped `id-token`** — `id-token: write` sits only on the jobs that upload (TestPyPI, PyPI and, since 2026-11-15, the republish job), never the workflow block, so the build job cannot mint a PyPI credential at all. Job-level `permissions` **replace** the workflow block rather than merging, so each job states its own: the build `contents: read` and `actions: read`, the TestPyPI job `contents: read` for its checkout, the PyPI job `id-token: write` alone, since it checks nothing out. `publish.yml`'s workflow block is `{}`, the sub-packages' `contents: read`.\n",
        where,
    )
    text = replace_once(
        text,
        "  The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher.\n",
        "  The `build` job is tag-guarded to `v*` Releases so a `juniper-<pkg>-v*` Release cannot fire the meta publisher; a plain dispatch from the tag re-fires it, and a dispatch with `-f republish_from_testpypi=true` runs only the republish job.\n"
        "  Built once (juniper-cascor#763 / #767's one-artifact template, 2026-11-15): both publish jobs upload the build job's `juniper-ml-dist` artifact (`dist/` and `SHA256SUMS`, 90 days), checked against `SHA256SUMS` before each upload, TestPyPI's JSON after the TestPyPI upload and again before the PyPI one, and PyPI's after; no upload sets `skip-existing`.\n",
        where,
    )
    text = replace_once(text, "  Gates: `tests/test_publish_testpypi_verify.py`, `tests/test_publish_release_only_trigger.py`. Operator surface:", "  Gates: `tests/test_publish_testpypi_verify.py`, `tests/test_publish_release_only_trigger.py`, `tests/test_publish_one_artifact.py`. Operator surface:", where)
    text = replace_once(
        text,
        "  Each build job is gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`, with a `--no-deps` TestPyPI-only verify (5×10s retry) and `skip-existing: true` on both publish steps.\n",
        "  Each build job is gated on its own `startsWith(github.event.release.tag_name, '<pkg>-v')`, or a dispatch that does not ask for the republish job, with a `--no-deps` TestPyPI-only verify (5×10s retry).\n"
        "  Since 2026-11-15 they carry the same one-artifact template as `publish.yml`: the `<pkg>-dist` artifact, the sha256 checks around every upload, no `skip-existing`, and the republish job.\n",
        where,
    )
    text = replace_once(
        text,
        "It runs when a GitHub Release is published and also supports manual `workflow_dispatch` reruns against a tag:\n\n```bash\ngh workflow run publish.yml --repo pcalnon/juniper-ml --ref <tag>\n```\n",
        "It runs when a GitHub Release is published. A `workflow_dispatch` from the release tag re-fires the whole publish (it builds again, so it works only while TestPyPI does not hold the version yet); with `-f republish_from_testpypi=true` it runs only the republish job, rung 1 of the [recovery ladder](#one-artifact-and-recovering-a-release-that-did-not-reach-pypi):\n"
        "\n"
        "```bash\n"
        "gh workflow run publish.yml --repo pcalnon/juniper-ml --ref v<version>                                  # full re-fire\n"
        "gh workflow run publish.yml --repo pcalnon/juniper-ml --ref v<version> -f republish_from_testpypi=true  # republish TestPyPI's files\n"
        "```\n",
        where,
    )
    text = replace_once(
        text,
        "1. **Build and Validate** -- checks out the tag, installs `build` and `twine`, runs `python -m build`, validates with `twine check dist/*`, and uploads the `dist/` artifact.\n",
        "1. **Build and Validate** -- checks out the tag, installs `build` and `twine`, runs `python -m build`, validates with `twine check dist/*`, asserts the tag matches the built version, records `SHA256SUMS`, and uploads `dist/` and `SHA256SUMS` as one artifact, `juniper-ml-dist`, kept 90 days. Its first step, `Reuse an earlier attempt's artifact`, skips all of that on a re-run attempt while the run holds the artifact.\n",
        where,
    )
    text = replace_once(
        text,
        "2. **Publish to TestPyPI** -- downloads the artifact, publishes to TestPyPI with OIDC trusted publishing, and enables PyPI attestations.\n",
        "2. **Publish to TestPyPI** -- checks out the tag (the verify reads `pyproject.toml`), downloads the artifact, checks it against `SHA256SUMS`, publishes to TestPyPI with OIDC trusted publishing and attestations, and then requires TestPyPI's JSON for the version to list exactly those files with those sha256.\n",
        where,
    )
    text = replace_once(
        text,
        "4. **Publish to PyPI** (`needs: testpypi`) -- runs only after Gate 1 succeeds and publishes the same artifact with OIDC trusted publishing and attestations enabled.\n",
        "4. **Publish to PyPI** (`needs: testpypi`) -- runs only after Gate 1 succeeds and the Overtoad approves the `pypi` environment. It checks out nothing: it downloads the same artifact, checks it against `SHA256SUMS` and TestPyPI's JSON again, publishes it with OIDC trusted publishing and attestations, and then requires PyPI's JSON to list exactly those files with those sha256.\n",
        where,
    )
    text = replace_once(
        text,
        "**Tag guard:** the `build` job runs only for `workflow_dispatch` or a Release whose tag starts with `v`, so a shared-package Release (`juniper-<pkg>-v*`) cannot fire the meta publisher.",
        "**Tag guard:** the `build` job runs only for a Release whose tag starts with `v`, or a `workflow_dispatch` that does not ask for the republish job, so a shared-package Release (`juniper-<pkg>-v*`) cannot fire the meta publisher.",
        where,
    )
    text = replace_once(
        text,
        "**Upload strictness:** the TestPyPI upload sets `skip-existing: true` so re-cutting a Release for a version TestPyPI already holds is a no-op rather than an immutable-upload 400; the production PyPI upload deliberately stays strict.\n",
        "**Upload strictness:** neither upload sets `skip-existing` (since 2026-11-15). On TestPyPI it kept an earlier build under the same file name silently, so Gate 1 could verify a file PyPI would never receive. Re-cutting a Release for a version TestPyPI already holds therefore fails at the TestPyPI upload: use the [recovery ladder](#one-artifact-and-recovering-a-release-that-did-not-reach-pypi) instead. The one-artifact checks and the republish job are pinned by `tests/test_publish_one_artifact.py`.\n",
        where,
    )
    text = replace_once(
        text,
        "| **Build-job tag-prefix guard** | `release: published` fires *every* `publish-*.yml`, so each build job gates on `startsWith(github.event.release.tag_name, '<pkg>-v')` to keep package A's Release from publishing package B. |\n",
        "| **Build-job tag-prefix guard** | `release: published` fires *every* `publish-*.yml`, so each build job gates on `startsWith(github.event.release.tag_name, '<pkg>-v')` to keep package A's Release from publishing package B. A `workflow_dispatch` runs it too, unless it asks for the republish job (`republish_from_testpypi`). |\n",
        where,
    )
    text = replace_once(
        text,
        "| **`skip-existing: true`** on both publish steps | Residual overlap (a manual dispatch during a Release) is a no-op instead of an immutable-upload 400. |\n",
        "| **One artifact, checked by sha256** (2026-11-15) | The build uploads `<pkg>-dist` once and a re-run reuses it; every upload is checked against `SHA256SUMS`, and TestPyPI's and PyPI's JSON against it. **No `skip-existing`**: it kept an earlier TestPyPI build silently. See [below](#one-artifact-and-recovering-a-release-that-did-not-reach-pypi). |\n",
        where,
    )
    text = replace_once(
        text,
        "| **OIDC + concurrency** | `permissions: {id-token: write, contents: read}`; `concurrency.group: publish-<suffix>-${{ github.ref_name }}` with `cancel-in-progress: false`; environments `testpypi` then `pypi`. |\n",
        "| **OIDC + concurrency** | Workflow `permissions: contents: read`, and only the uploading jobs add `id-token: write` (build: `contents` and `actions: read`; TestPyPI: `contents: read` and `id-token`; PyPI: `id-token` alone; republish: `actions: read` and `id-token`); `concurrency.group: publish-<suffix>-${{ github.ref_name }}` with `cancel-in-progress: false`; environments `testpypi` then `pypi`. |\n",
        where,
    )
    text = replace_once(text, "Retry a stuck publish without re-cutting a Release:\n\n```bash\ngh workflow run publish-ci-tools.yml --repo pcalnon/juniper-ml --ref juniper-ci-tools-vX.Y.Z\n```\n", REFERENCE_LADDER, where)
    text = replace_once(
        text,
        "1. **Build and Validate** -- the build job sets `defaults.run.working-directory` to the package subdirectory (so every step is subdir-relative without repeating the path), runs `python -m build --sdist --wheel`, validates with `twine check dist/*`, and uploads that subdirectory's `dist/` artifact with `if-no-files-found: error` so a silently empty build fails here instead of surfacing as a confusing publish-step error.\n",
        "1. **Build and Validate** -- the build job sets `defaults.run.working-directory` to the package subdirectory (so every step is subdir-relative without repeating the path), runs `python -m build --sdist --wheel`, validates with `twine check dist/*`, asserts the tag matches the built version, records `SHA256SUMS`, and uploads that subdirectory's `dist/` with `SHA256SUMS` as one artifact (`<pkg>-dist`, 90 days) with `if-no-files-found: error` so a silently empty build fails here instead of surfacing as a confusing publish-step error. A re-run attempt reuses that artifact.\n",
        where,
    )
    text = replace_once(
        text,
        "2. **Publish to TestPyPI** -- downloads the artifact into `dist/`, publishes with `packages-dir: dist/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body.\n",
        "2. **Publish to TestPyPI** -- downloads the artifact into the workspace (`<pkg>/dist/` and `SHA256SUMS`), checks it against `SHA256SUMS`, publishes with `packages-dir: ${{ env.PUBLISH_DIST_DIR }}/`, `repository-url: https://test.pypi.org/legacy/`, and `verbose: true` so trusted-publisher or upload errors include the server response body, and then requires TestPyPI's JSON to list exactly those files with those sha256.\n",
        where,
    )
    text = replace_once(text, "3. **Verify TestPyPI Install** -- sparse-checks out the package `pyproject.toml`,", "3. **Verify TestPyPI Install** -- after that check, sparse-checks out the file the package version is read from (`<pkg>/pyproject.toml`, or `juniper-model-core/juniper_model_core/_version.py` for model-core),", where)
    text = replace_once(
        text,
        "4. **Publish to PyPI** -- runs only after TestPyPI install verification and publishes the same artifact with `packages-dir: dist/` and `verbose: true`.\n",
        "4. **Publish to PyPI** -- runs only after TestPyPI install verification and the `pypi` approval. It checks the same artifact against `SHA256SUMS` and TestPyPI's JSON again, publishes it with `packages-dir: ${{ env.PUBLISH_DIST_DIR }}/` and `verbose: true`, and then checks PyPI's JSON.\n",
        where,
    )
    row = f"| {new_version:<7} | {date} | The one-artifact publish (the port of juniper-cascor#763 / #767; the Overtoad's directive and recovery ruling of 2026-11-15): § Meta-Package Publish Pipeline and § Independent Sibling Package Publish Pipelines describe the one artifact, its sha256 checks, the reuse step, no `skip-existing`, the per-job permissions and the recovery ladder, with its precondition (rungs 1 and 2 only after a TestPyPI job, install check included, that succeeded or failed only for a transient index lag; a broken package is a new patch version) and each workflow's republish command; the CI/CD inventory, § Publishing (`publish.yml`) and the `tests/test_publish_one_artifact.py` entry ({suites} suites) follow, and the sibling pipeline's step 3 names model-core's `_version.py` |\n"
    return insert_after_line(text, f"| {old_version:<7} | ", row, where)


CHEATSHEET_TIP = (
    "Tip: all seven publishers build once and check by sha256 (juniper-cascor#763 / #767's one-artifact template): both publish jobs upload the build job's artifact (dist and `SHA256SUMS`, 90 days), TestPyPI's JSON must list exactly those sha256 after the TestPyPI upload and again before the PyPI one, and PyPI's after; no `skip-existing`; only the uploading jobs hold `id-token: write`.\n"
    "A release that did not reach PyPI, after a TestPyPI job (install check included) that passed or failed only for a transient index lag: dispatch its workflow from the tag with `-f republish_from_testpypi=true` (copies TestPyPI's files, builds nothing); if that fails, within 30 days **Re-run failed jobs**, never \"Re-run all jobs\"; otherwise cut a new patch version. A real install-check failure is a broken package: cut a new patch version, never republish it. See [REFERENCE — One artifact, and recovering a release that did not reach PyPI](REFERENCE.md#one-artifact-and-recovering-a-release-that-did-not-reach-pypi).\n"
    "\n"
)
#: The CI/CD table's plain re-fire row: it builds again, so it fails once TestPyPI holds the version (the review of
#: juniper-ml#2593). The ladder replaces it.
CHEATSHEET_RETRY_OLD = "| Retry shared publish   | `gh workflow run publish-<pkg>.yml --repo pcalnon/juniper-ml --ref juniper-<pkg>-vX.Y.Z`    |\n"
CHEATSHEET_RETRY_NEW = (
    "| Recover a publish      | Only after a TestPyPI job (install check included) that passed or failed only for index lag: (1) `gh workflow run publish-<pkg>.yml --repo pcalnon/juniper-ml --ref juniper-<pkg>-vX.Y.Z -f republish_from_testpypi=true` (meta: `publish.yml`, `--ref vX.Y.Z`); (2) within 30 days, `gh run rerun <run-id> --repo pcalnon/juniper-ml --failed`, never \"Re-run all jobs\"; (3) a new patch version. [REFERENCE — the ladder](REFERENCE.md#one-artifact-and-recovering-a-release-that-did-not-reach-pypi) |\n"
)


def cheatsheet(text: str, date: str) -> str:
    where = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
    text, _, new_version = bump_version(text, "**Version**:", 1, where)
    # The footer carries the version too. juniper-ml#2592 raised the header to 1.0.70 and left the footer at 1.0.69,
    # so the footer is set to the header's new value rather than bumped from its own.
    footer = re.compile(r"^\*\*Version:\*\* \d+\.\d+\.\d+$", re.M)
    if len(footer.findall(text)) != 1:
        raise Refused(f"{where}: {len(footer.findall(text))} '**Version:**' footer lines, expected 1")
    text = footer.sub(f"**Version:** {new_version}", text)
    text = set_date(text, "**Date**:", 1, date, where)
    text = set_date(text, "**Last Updated:**", 1, date, where)
    text = replace_once(text, "Each is tag-prefix-guarded, with a `--no-deps` TestPyPI-only 5×10s verify and `skip-existing: true`. Do not resurrect", "Each is tag-prefix-guarded, with a `--no-deps` TestPyPI-only 5×10s verify. Do not resurrect", where)
    text = replace_once(text, CHEATSHEET_RETRY_OLD, CHEATSHEET_RETRY_NEW, where)
    anchor = "Tip: shared-package `ci-*.yml` (six sub-packages)"
    if text.count(anchor) != 1:
        raise Refused(f"{where}: anchor matched {text.count(anchor)} times, expected 1: {anchor!r}")
    return text.replace(anchor, CHEATSHEET_TIP + anchor)


PROCEDURE_AMENDMENT = (
    "\n"
    "> **2026-11-15 amendment (the one-artifact publish).** PyPI must receive exactly the files TestPyPI took, and the run proves it by sha256: the build runs once, both publish jobs upload its one artifact, and TestPyPI's and PyPI's JSON are checked against it. The contract, every repository's port and the Overtoad's recovery ladder are in [§11.8](#118-one-artifact-and-recovering-a-release-that-did-not-reach-pypi).\n"
)
PROCEDURE_SECTION = (
    "\n"
    "### 11.8 One artifact, and recovering a release that did not reach PyPI\n"
    "\n"
    "**The one-artifact contract (2026-11-15).** The Overtoad's directive: " + OWNER_DIRECTIVE + " Every Juniper publish workflow is to carry juniper-cascor's one-artifact template ([juniper-cascor#763](https://github.com/pcalnon/juniper-cascor/pull/763) and [#767](https://github.com/pcalnon/juniper-cascor/pull/767)), copied verbatim:\n"
    "\n"
    "- the build job builds once, records `SHA256SUMS`, and uploads the dist directory and `SHA256SUMS` as one artifact, `<package>-dist`, kept 90 days, longer than the `pypi` gate's 30-day cap and the 30-day re-run window; on a re-run attempt its first step reuses that artifact instead of building again;\n"
    "- each publish job checks the files against `SHA256SUMS` before it uploads them;\n"
    "- after the TestPyPI upload, TestPyPI's JSON for the version must list exactly those files with those sha256, before the install check; the PyPI job checks TestPyPI's JSON again before its upload, and PyPI's JSON after it;\n"
    "- no upload sets `skip-existing`, and only the jobs that upload hold `id-token: write`.\n"
    "\n"
    f"The contract and the template's steps: [juniper-cascor `docs/ci_cd/MANUAL.md` § One Artifact, Checked Against TestPyPI]({CASCOR_MANUAL}#one-artifact-checked-against-testpypi). juniper-cascor's three publishers carry it since juniper-cascor#763 and juniper-cascor#767, and juniper-ml's seven since 2026-11-15 ([`docs/REFERENCE.md` § Independent Sibling Package Publish Pipelines](../docs/REFERENCE.md#independent-sibling-package-publish-pipelines)). Each other repository gets its own port. Until a repository's publisher carries the `republish` job, rung 1 below does not exist there, and the publisher may still rebuild in its PyPI job or skip existing files.\n"
    "\n"
    "Why: juniper-cascor 0.13.0's and 0.14.0's wheels differ between PyPI and TestPyPI (`eda26e26…` against `f5dbc1b6…`, and `b70f3d39…` against `c5c9a5dc…`), because its PyPI job built again. juniper-ci-tools 0.9.1's do too (`1dc8e01e…` on PyPI, `ade363e8…` on TestPyPI): run 38045867684's PyPI job failed at its download on day 11, after the 7-day artifact expired, and its second attempt (\"Re-run all jobs\") built again, while the `skip-existing` TestPyPI upload kept the first build.\n"
    "\n"
    f"**Recovering a release that did not reach PyPI.** The Overtoad's ladder (ruling of 2026-11-15). Every rung publishes the files TestPyPI took, or nothing ([juniper-cascor `docs/ci_cd/MANUAL.md` § Recovering a Release That Did Not Reach PyPI]({CASCOR_MANUAL}#recovering-a-release-that-did-not-reach-pypi)). **" + LADDER_PRECONDITION + "** " + LADDER_BROKEN + " The ladder, in this order:\n"
    "\n"
    "1. **Republish TestPyPI's files.** Dispatch the release's own publish workflow from its release tag:\n"
    "\n"
    "   ```bash\n"
    "   gh workflow run <publish workflow> --repo pcalnon/<repo> --ref <release tag> -f republish_from_testpypi=true\n"
    "   # e.g. gh workflow run publish.yml --repo pcalnon/juniper-ml --ref v<version> -f republish_from_testpypi=true\n"
    "   ```\n"
    "\n"
    "   Only `Republish the tested files (dispatch only)` runs. It waits at the `pypi` gate, builds nothing, downloads the version's files from TestPyPI, checks each against TestPyPI's JSON and, while the release run's artifact exists, against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It needs a tag whose workflow carries the job.\n"
    "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run (`gh run rerun <run-id> --repo pcalnon/<repo> --failed`). The re-run reuses the run's artifact and waits at the `pypi` gate again. GitHub refuses a re-run after 30 days.\n"
    "3. **Otherwise, cut a new patch version.**\n"
    "\n"
    "**Never \"Re-run all jobs\"** on a publish run, nor `gh run rerun <run-id>` without `--failed`, and do not re-cut the Release: a new build of a version TestPyPI already holds is refused at the TestPyPI upload. Each repository's commands: juniper-ml's seven in [`docs/REFERENCE.md`](../docs/REFERENCE.md#one-artifact-and-recovering-a-release-that-did-not-reach-pypi); juniper-cascor's in its `MANUAL.md` section above.\n"
)


def procedure(text: str) -> str:
    where = "notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md"
    text = replace_once(
        text,
        "| Rebuild in the `pypi` job instead of passing artifacts | **Historical.** Live workflows upload a `dist/` artifact from `build` and download it in the publish jobs. |\n",
        "| Rebuild in the `pypi` job instead of passing artifacts | **Historical.** Live workflows build once, in `build`, and both publish jobs upload that one artifact, checked by sha256 against `SHA256SUMS` and TestPyPI's and PyPI's JSON (the one-artifact contract, 2026-11-15; §11.8). |\n",
        where,
    )
    text = replace_once(
        text,
        "| `id-token: write` at the top level | **Historical.** P4 (juniper-ml#357) scopes `id-token: write` to the two publish jobs only; the build job restates `contents: read`. |\n",
        "| `id-token: write` at the top level | **Historical.** P4 (juniper-ml#357) scopes `id-token: write` to the jobs that upload (TestPyPI, PyPI and, since 2026-11-15, the republish job); the build job holds `contents: read` and `actions: read`. |\n",
        where,
    )
    anchor = "Re-measured 2026-08-24: 12 tags exist with no Release and none of them published.\n"
    text = replace_once(text, anchor + "\n### 10.4 GitHub environment setup\n", anchor + PROCEDURE_AMENDMENT + "\n### 10.4 GitHub environment setup\n", where)
    text = replace_once(text, "not the live workflow — see the 2026-08-08 and 2026-08-24 amendments after §10.3. Live contract:", "not the live workflow — see the 2026-08-08, 2026-08-24 and 2026-11-15 amendments after §10.3. Live contract:", where)
    text = replace_once(
        text,
        "Or visit **Actions** tab in the repository.\n",
        "Or visit **Actions** tab in the repository.\n\n"
        "If the run fails, or the `pypi` approval does not come in time, do not re-cut the Release and never \"Re-run all jobs\": follow [§11.8](#118-one-artifact-and-recovering-a-release-that-did-not-reach-pypi). "
        "Its first two rungs need a TestPyPI job, install check included, that succeeded or failed only for a transient index lag; a real install-check failure means a broken package, which ships fixed as a new patch version.\n",
        where,
    )
    anchor = "(`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md` §10).\n"
    text = replace_once(text, anchor + "\n---\n\n## 12. Troubleshooting\n", anchor + PROCEDURE_SECTION + "\n---\n\n## 12. Troubleshooting\n", where)
    return replace_once(
        text,
        "PyPI does not allow re-uploading the same version, even if the previous upload was deleted. Bump the version number (e.g., `0.1.0` -> `0.1.1`).\n",
        "PyPI does not allow re-uploading the same version, even if the previous upload was deleted. Bump the version number (e.g., `0.1.0` -> `0.1.1`).\n\nAn index accepts an upload of a file it already holds with the same content, and refuses one with other content under the same name. So in a publish workflow carrying the one-artifact template, this error at the TestPyPI upload means the run built new files for a version TestPyPI already holds (a re-fired or re-cut publish). Do not force it through: follow [§11.8](#118-one-artifact-and-recovering-a-release-that-did-not-reach-pypi).\n",
        where,
    )


#: The runbook's responses to a failed build or TestPyPI job, as juniper-ml#2592 left them ("fix; re-cut"), and the
#: real ones (the review of juniper-ml#2593): a re-cut builds the version again, which TestPyPI refuses once it holds it.
RUNBOOK_RESPONSES = (
    (
        "| The run is not healthy — inspect the publish run's TestPyPI job; fix and re-cut is idempotent. |\n",
        "| The run is not healthy — open the publish run's TestPyPI job and read its failed step. Transient (TestPyPI not yet serving the upload, a network error): \"Re-run failed jobs\" on the run, within 30 days, never \"Re-run all jobs\". A broken package (a real install-check failure): fix it and cut a new patch version, never the republish dispatch, which would copy the broken files to PyPI. Do not re-cut the Release (" + PROCEDURE_LADDER_LINK + "). |\n",
    ),
    (
        "| The run is not healthy — inspect the build job; fix and re-cut is idempotent. |\n",
        "| The run is not healthy — open the build job and read its failed step. Transient (a network or runner error): \"Re-run failed jobs\" on the run, within 30 days. Otherwise fix it and cut a new patch version. |\n",
    ),
    (
        "| Inspect the build job; fix; re-cut (idempotent). |\n",
        "| Inspect the build job's failed step. Transient: \"Re-run failed jobs\" on the run, within 30 days. Otherwise fix it and cut a new patch version. |\n",
    ),
    (
        "| Inspect the TestPyPI job's failed step; fix; re-cut (idempotent). |\n",
        "| Inspect the TestPyPI job's failed step. Transient (TestPyPI not yet serving the upload): \"Re-run failed jobs\" on the run, within 30 days. A broken package (a real install-check failure): fix it and cut a new patch version, never the republish dispatch (procedure §11.8). |\n",
    ),
    (
        "- Deleting the Release + tag also lets a corrected re-run start clean: the ceremony is idempotent and\n"
        "  re-computes state from PyPI/Release truth (plan §8 last row; `ceremony.py:53-56`).\n",
        "- Deleting the Release + tag lets a corrected re-run start clean only while TestPyPI does not hold the\n"
        "  version: the ceremony is idempotent and re-computes state from PyPI/Release truth (plan §8 last row;\n"
        "  `ceremony.py:plan_ceremony`). Once TestPyPI holds it, a rebuild under the same file names is refused there\n"
        "  (or, where a publisher still skips existing files, never uploaded), so the correction ships as a new patch\n"
        "  version (" + PROCEDURE_LADDER_LINK + ").\n",
    ),
)


def runbook(text: str, date: str) -> str:
    where = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
    text, _, _ = bump_version(text, "**Version**:", 1, where)
    text = set_date(text, "**Last Updated**:", 1, date, where)
    for old, new in RUNBOOK_RESPONSES:
        text = replace_once(text, old, new, where)
    return replace_once(
        text,
        "**PyPI and TestPyPI files are immutable**, and the publish steps use `skip-existing: true`\n(plan §8 \"Idempotent re-entry\", citing `publish-service-core.yml:139,185`). Consequences for recovery:\n",
        "**PyPI and TestPyPI files are immutable.** The publish steps used `skip-existing: true`\n"
        "(plan §8 \"Idempotent re-entry\", citing `publish-service-core.yml:139,185`) until the one-artifact publish dropped\n"
        "it: in juniper-ml's seven publishers on 2026-11-15, and in each other repository's as its port lands. juniper-cascor's\n"
        "publishers, whose #763 / #767 are the template, never set it. A TestPyPI upload that skips an existing file lets the\n"
        "install check test an earlier build than the one PyPI takes. A release that did not reach PyPI follows the Overtoad's\n"
        "recovery ladder: the republish dispatch, then (within 30 days) \"Re-run failed jobs\", then a new patch version. The\n"
        "first two rungs apply only when the release run's TestPyPI job, install check included, succeeded or failed only for\n"
        "a transient index lag; a real install-check failure is a broken package, which ships fixed as a new patch version and\n"
        "is never republished (" + PROCEDURE_LADDER_LINK + ").\n"
        "Consequences for recovery:\n",
        where,
    )


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────────────────────
def apply(tree: Path, template: str, test_file: str, verify_script: str, date: str, cases: str, mutations: str, workflow_date: "str | None" = None) -> dict[str, str]:
    """Return {repo path: new text} for every file the port writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    if sha256(template) != TEMPLATE_SHA256:
        raise Refused(f"the template is not juniper-cascor's publish.yml at 675884888f5a (sha256 {sha256(template)})")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise Refused(f"--date {date!r} is not YYYY-MM-DD")
    workflow_date = workflow_date or date
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", workflow_date):
        raise Refused(f"--workflow-date {workflow_date!r} is not YYYY-MM-DD")
    for rel, digest in BASE_SHA256.items():
        if sha256(read(rel)) != digest:
            print(f"note: {rel} moved since edea2eb1; applying by anchors (read the result again)")
    cascor = load_cascor_edits()
    blocks = cascor.template_blocks(template)
    republish = cascor.republish_job(template)
    out: dict[str, str] = {}
    rel = ".github/workflows/publish.yml"
    out[rel] = meta_workflow(read(rel), cascor, blocks, republish, workflow_date)
    for suffix, dispatch_old, skip_testpypi, skip_pypi in SUB_PACKAGES:
        rel = f".github/workflows/publish-{suffix}.yml"
        out[rel] = sub_workflow(read(rel), suffix, dispatch_old, skip_testpypi, skip_pypi, cascor, blocks, republish)
    for rel, text in out.items():
        check_workflow(rel, text, blocks, republish)
    before = invoked_suites(read(".github/workflows/ci.yml"))
    out[".github/workflows/ci.yml"] = ci_yml(read(".github/workflows/ci.yml"))
    after = invoked_suites(out[".github/workflows/ci.yml"])
    if len(set(after)) != len(set(before)) + 1 or "test_publish_one_artifact.py" not in after or len(after) != len(set(after)):
        raise Refused(f"ci.yml: {len(set(before))} suites before, {len(set(after))} after; expected one more, the new suite, invoked once")
    out[".github/workflows/main-verify.yml"] = main_verify(read(".github/workflows/main-verify.yml"))
    for rel, text in ((TEST_PATH, test_file), (VERIFY_PATH, verify_script)):
        if (tree / rel).exists():
            raise Refused(f"{rel} already exists on this base")
        out[rel] = text
    out["tests/test_publish_subpackage_workflows.py"] = subpackage_test(read("tests/test_publish_subpackage_workflows.py"))
    out["tests/test_publish_testpypi_verify.py"] = meta_test(read("tests/test_publish_testpypi_verify.py"))
    out["CHANGELOG.md"] = changelog(read("CHANGELOG.md"), cases, mutations)
    out["AGENTS.md"] = agents_md(read("AGENTS.md"), len(set(before)), len(set(after)), date)
    out["docs/REFERENCE.md"] = reference(read("docs/REFERENCE.md"), len(set(after)), date, mutations)
    out["docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"] = cheatsheet(read("docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"), date)
    rel = "notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md"
    out[rel] = procedure(read(rel))
    rel = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
    out[rel] = runbook(read(rel), date)
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh juniper-ml clone of main (edited in place)")
    parser.add_argument("--template", required=True, type=Path, help="juniper-cascor's .github/workflows/publish.yml at 675884888f5a")
    parser.add_argument("--test-file", required=True, type=Path, help=f"the new {TEST_PATH}")
    parser.add_argument("--verify-script", required=True, type=Path, help=f"the new {VERIFY_PATH}")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"), help="the UTC date the docs and AGENTS.md carry (default: today, UTC)")
    parser.add_argument("--workflow-date", default=None, help="the date publish.yml's header carries as Last Modified (default: --date)")
    parser.add_argument("--cases", default="{cases}", help="the case count the CHANGELOG entry states")
    parser.add_argument("--mutations", default="{mutations}", help="the negative control's mutation count the docs state")
    args = parser.parse_args(argv)
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.verify_script.read_text(encoding="utf-8"), args.date, args.cases, args.mutations, args.workflow_date)
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
