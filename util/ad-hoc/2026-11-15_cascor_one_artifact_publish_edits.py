#!/usr/bin/env python3
"""Apply juniper-cascor's one-artifact publish change to a fresh copy of its tree, every edit asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763, "publish one artifact to TestPyPI and PyPI", as amended by its review)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_publish_workflow_artifact_audit.py (the audit that classified every publisher);
         util/open_signed_pr.py and util/push_signed_commit.py (upload the files this writes, whole);
         notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md

Why
---
``util/open_signed_pr.py`` and ``util/push_signed_commit.py`` upload WHOLE files, so an edit made on a tree that ``main``
has since moved past silently reverts whatever merged in between. Every edit here is therefore replayable: re-extract
cascor's ``main`` tarball (or the pull request's base), re-run this, and upload the result. The edits are:

- ``.github/workflows/publish.yml`` is replaced by ``--publish-yml`` (the reviewed new file), but only when the tree's
  copy still hashes to the base it was written against; otherwise this refuses, because that file must be re-derived.
- ``publish-cascor-model.yml`` and ``publish-protocol.yml`` get the template steps and the whole republish job, copied
  text-for-text out of the new ``publish.yml`` (so the copies cannot drift); the two template parameters in their
  workflow ``env``; per-job permissions; the ``republish_from_testpypi`` dispatch input; and the reuse condition on
  every build step after the reuse step.
- ``src/tests/unit/test_publish_one_artifact.py`` is copied from ``--test-file``, and its negative control,
  ``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py``, from ``--verify-script``.
- ``CHANGELOG.md`` gets one ``[Unreleased]`` / ``### Fixed`` entry; ``AGENTS.md``, ``docs/ci_cd/MANUAL.md``,
  ``docs/ci_cd/REFERENCE.md``, ``docs/ci_cd/QUICK_START.md`` and ``docs/DEVELOPER_CHEATSHEET.md`` get the docs.

    python3 -I util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py --tree <fresh cascor tree> \\
        --publish-yml <new publish.yml> --test-file <new test file> --verify-script <new negative control> \\
        [--changelog-cases N] [--changelog-mutations M]

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once or a base moved (nothing written).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

#: sha256 of each workflow at juniper-cascor main f5ffefb7 / 683eed44 (2026-11-15), the base the new publish.yml was written on.
BASE_SHA256 = {
    ".github/workflows/publish.yml": "6a3c407490a7b59b97cb02aba0fd4e6f6eaca295db0bd23117c1b8365ac58ef8",
    ".github/workflows/publish-cascor-model.yml": "0f82bbf49f66e8b7fe308926dbc8848d185f2e6dde561b3d130ab57ec7500e85",
    ".github/workflows/publish-protocol.yml": "02ee250bd88ea9c070a10001916da6799396c5cffe343e44d062d626e78e8c59",
}
TEST_PATH = "src/tests/unit/test_publish_one_artifact.py"
VERIFY_PATH = "util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py"
#: A step-level line: a new step, or a comment between steps. Run-script lines are indented deeper.
STEP_LINE = re.compile(r"^      (?:- |# )")
REUSE_IF = "        if: steps.reuse.outputs.reuse != 'true'\n"
CHECKOUT = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1\n"
PUBLISH_STEP = "      - name: Publish to {index}\n        uses: pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086  # v1.14.3\n        with:\n"
WANT_BLOCKS = {
    "build/Reuse an earlier attempt's artifact",
    "build/Record SHA256SUMS",
    "build/Upload dist artifacts",
    "testpypi/Download dist artifacts",
    "testpypi/Verify the dist against SHA256SUMS",
    "testpypi/Verify TestPyPI serves exactly these files",
    "pypi/Download dist artifacts",
    "pypi/Verify the dist against SHA256SUMS",
    "pypi/Verify TestPyPI still serves exactly these files",
    "pypi/Verify PyPI serves exactly these files",
    "republish/Find the release run's artifact",
    "republish/Download TestPyPI's files and verify them",
    "republish/Verify the dist against SHA256SUMS",
    "republish/Verify PyPI serves exactly these files",
}


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:90]!r}")
    return text.replace(old, new)


def template_blocks(publish_yml: str) -> dict[str, str]:
    """Return the raw YAML of each template step of the new publish.yml, keyed by job and step name, comments included.

    A block starts at its ``# One-artifact publish template`` comment and runs to the next step-level line after its
    ``- name:`` line. Run-script lines are indented deeper than any step-level line, so they never end a block early.
    """
    lines = publish_yml.splitlines(keepends=True)
    blocks: dict[str, str] = {}
    job = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^  [a-z][a-z0-9-]*:\s*$", line):
            job = line.strip().rstrip(":")
        if line.startswith("      # One-artifact publish template"):
            start = i
            first = next(j for j in range(i, len(lines)) if lines[j].startswith("      - "))
            name = re.sub(r"^      - name:\s*", "", lines[first]).strip()
            end = first + 1
            while end < len(lines) and not STEP_LINE.match(lines[end]) and not (lines[end].strip() and len(lines[end]) - len(lines[end].lstrip(" ")) <= 2):
                end += 1
            block = "".join(lines[start:end]).rstrip("\n") + "\n"
            key = f"{job}/{name}"
            if key in blocks:
                raise Refused(f"publish.yml: two template blocks for {key}")
            blocks[key] = block
            i = end
            continue
        i += 1
    if set(blocks) != WANT_BLOCKS:
        raise Refused(f"publish.yml: template blocks found {sorted(blocks)}, expected {sorted(WANT_BLOCKS)}")
    return blocks


def republish_job(publish_yml: str) -> str:
    """The whole republish job of the new publish.yml, from the comment banner above it to the end of the file."""
    lines = publish_yml.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == "  republish:\n"]
    if len(at) != 1:
        raise Refused(f"publish.yml: {len(at)} republish jobs")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    return "".join(lines[start:]).rstrip("\n") + "\n"


DISPATCH_OLD = "  # Manual dispatch so operators can re-fire a publish (e.g. after a transient failure).\n  workflow_dispatch:\n"
DISPATCH_NEW = (
    "  # Manual dispatch, from the release TAG (both publish environments admit tags only). Without the input it re-fires\n"
    "  # the whole publish: it builds again, so it works only while TestPyPI does not hold the version yet. With\n"
    "  # republish_from_testpypi it runs the republish job alone, which copies TestPyPI's files to PyPI and builds nothing.\n"
    "  workflow_dispatch:\n"
    "    inputs:\n"
    "      republish_from_testpypi:\n"
    "        description: \"Copy TestPyPI's files for this tag's version to PyPI (run from the release tag; nothing is built)\"\n"
    "        type: boolean\n"
    "        default: false\n"
)


def sub_package_workflow(text: str, package: str, blocks: dict[str, str], republish: str, where: str) -> str:
    """Give a sub-package publisher the template parameters, permissions, steps and republish job; keep its own build,
    install check, guard and concurrency."""
    text = replace_once(text, DISPATCH_OLD, DISPATCH_NEW, where)
    text = replace_once(text, "permissions:\n  id-token: write\n  contents: read\n", "# Each job adds what it needs to this; only the jobs that upload add id-token: write.\npermissions:\n  contents: read\n", where)
    env = (
        "env:\n"
        "  # The one-artifact publish template's two parameters (see publish.yml): the distribution's name on PyPI and\n"
        "  # TestPyPI, and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
        f"  PUBLISH_PACKAGE: {package}\n"
        f"  PUBLISH_DIST_DIR: {package}/dist\n"
        "\n"
    )
    text = replace_once(text, "  cancel-in-progress: false\n\njobs:\n", "  cancel-in-progress: false\n\n" + env + "jobs:\n", where)
    text = replace_once(text, "    # also fires this workflow and must be skipped. workflow_dispatch always runs. Downstream jobs\n", "    # also fires this workflow and must be skipped. A dispatch runs it, unless it asks for the republish job. Downstream jobs\n", where)
    text = replace_once(
        text,
        f"    if: github.event_name != 'release' || startsWith(github.event.release.tag_name, '{package}-v')\n",
        f"    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
        where,
    )
    build_head_old = f"    runs-on: ubuntu-latest\n    defaults:\n      run:\n        working-directory: {package}\n    steps:\n" + CHECKOUT + "\n"
    build_head_new = (
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
        "      actions: read  # the reuse step lists this run's artifacts\n"
        f"    defaults:\n      run:\n        working-directory: {package}\n    steps:\n"
        + blocks["build/Reuse an earlier attempt's artifact"]
        + "\n"
        + CHECKOUT
        + REUSE_IF
        + "\n"
    )
    text = replace_once(text, build_head_old, build_head_new, where)
    for step in (
        "      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n",
        "      - name: Install build tools\n",
        "      - name: Build sdist + wheel\n",
        "      - name: Validate distribution metadata\n",
    ):
        text = replace_once(text, step, step + REUSE_IF, where)
    old_upload = (
        "      - name: Upload build artifacts\n"
        "        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2\n"
        "        with:\n"
        f"          name: {package}-dist\n"
        f"          path: {package}/dist/\n"
        "          if-no-files-found: error\n"
        "          retention-days: 7\n"
    )
    text = replace_once(text, old_upload, blocks["build/Record SHA256SUMS"] + "\n" + blocks["build/Upload dist artifacts"], where)
    for job, need, index in (("publish-testpypi", "build", "TestPyPI"), ("publish-pypi", "publish-testpypi", "PyPI")):
        head = f"  {job}:\n    name: Publish to {index}\n    needs: {need}\n    runs-on: ubuntu-latest\n"
        text = replace_once(text, head, head + f"    permissions:\n      contents: read\n      id-token: write  # trusted publishing to {index}\n", where)
    old_download = (
        "      - uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333  # v8.0.2\n"
        "        with:\n"
        f"          name: {package}-dist\n"
        "          path: dist/\n"
        "\n"
    )
    old_testpypi = old_download + PUBLISH_STEP.format(index="TestPyPI") + "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: dist/\n          verbose: true\n\n"
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
    old_pypi = old_download + PUBLISH_STEP.format(index="PyPI") + "          packages-dir: dist/\n          verbose: true\n"
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
    if not text.endswith(old_pypi):
        raise Refused(f"{where}: the PyPI job's download and upload are not the file's last steps")
    text = replace_once(text, old_pypi, new_pypi, where)
    return text + "\n" + republish


CHANGELOG_ENTRY = """\
- **PyPI now receives the files TestPyPI took: `publish.yml` builds once, and the run checks every upload by sha256
  against TestPyPI** (the Overtoad's directive of 2026-11-15: "deploy to pypi should send the same artifact that was
  already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy,
  might also be helpful here to prevent this from slipping through the cracks again."). `publish.yml` ran
  `python -m build` in its TestPyPI job and again in its PyPI job, so PyPI served a second build of each release. For
  0.13.0 the wheel's sha256 is `eda26e26…` on PyPI and `f5dbc1b6…` on TestPyPI, and the sdist's `25ae6898…` against
  `701e9f33…`; for 0.14.0 they are `b70f3d39…` against `c5c9a5dc…` and `79cc0da3…` against `92f0b146…`. Each job ran
  an unpinned `pip install build twine`, so a long `pypi` gate could also change the build backend between the build
  TestPyPI verified and the one PyPI took.
  - **Build once.** A new `build` job, `Build and Validate`, runs the same commands once (`pip install build twine`,
    `python -m build`, `twine check dist/*`). Its `Record SHA256SUMS` step hashes the files, and
    `Upload dist artifacts` uploads `dist/` and `SHA256SUMS` as one artifact, `juniper-cascor-dist`, kept 90 days so
    it outlives the `pypi` gate (at most 30 days) and the 30-day re-run window. The `v*` tag guard moved to this job;
    both publish jobs depend on it, so a sub-package Release still skips all three.
  - **A re-run reuses the first build.** download-artifact takes the newest artifact of a name, so "Re-run all jobs"
    would make a rebuild the file every later job uploads. juniper-ml's run 38045867684 did exactly that to
    juniper-ci-tools 0.9.1, whose PyPI files (`1dc8e01e…`) are not TestPyPI's (`ade363e8…`). On any attempt after the
    first, the build job's new first step, `Reuse an earlier attempt's artifact`, lists the run's artifacts and, when
    `juniper-cascor-dist` is there, skips every later step of the job; the jobs after it download that artifact.
  - **TestPyPI.** `Publish to TestPyPI` downloads the artifact and checks the files against `SHA256SUMS` before it
    uploads them. `Verify TestPyPI serves exactly these files` then requires TestPyPI's JSON for the version to list
    exactly those files with those sha256. It polls up to 20 times, 15 s apart, while the version or a file is
    missing (CDN lag), and fails at once on a file listed with another sha256 or one the run did not build. The
    install check follows, unchanged.
  - **PyPI.** `Publish to PyPI` keeps its `pypi` environment and gate, and no longer checks out or builds anything.
    It downloads the same artifact, checks it against `SHA256SUMS`, checks TestPyPI's JSON again before it uploads,
    and checks PyPI's JSON after. An index never takes a second file under a name it already holds, so TestPyPI's
    record cannot change after the TestPyPI job: it witnesses what the install check tested.
  - **Only the jobs that upload hold `id-token: write`**, as the pypa action's README at the pinned SHA asks. The
    workflow's `permissions` is now `{}`: `Build and Validate` gets `contents: read` and `actions: read`,
    `Publish to TestPyPI` `contents: read` and `id-token: write`, and `Publish to PyPI` `id-token: write`. So the
    build, which runs the package's build backend, can mint no OIDC token and holds no environment.
  - **Recovery, in the Overtoad's order (ruling of 2026-11-15).** A `workflow_dispatch` from the release tag with
    `republish_from_testpypi` runs only the new job `Republish the tested files (dispatch only)`, behind the same
    `pypi` gate. It builds nothing: it downloads the version's files from TestPyPI, checks each file's bytes against
    TestPyPI's JSON and, while the release run's artifact exists, against its `SHA256SUMS`, uploads them, and checks
    PyPI's JSON. If that fails, within 30 days of the release run, "Re-run failed jobs" on it; after that, cut a new
    patch version. The job's name carries no "pypi", so juniper-ml's release-train ceremony, which tells the publish
    jobs apart by that substring and reads release-event runs only, never counts it.
  - `publish-cascor-model.yml` and `publish-protocol.yml` already handed both jobs one artifact. They gain the same
    checks, the reuse step, per-job permissions (`contents: read` at the top) and the republish job, and their
    artifact's retention rises from 7 days to 90: juniper-ci-tools 0.9.1's PyPI job, approved on day 11, failed at its
    download because its 7-day artifact had expired. A dispatch without the new input still re-fires the whole
    publish, as before.
  - **A template.** Every new step reads only the workflow `env` values `PUBLISH_PACKAGE` and `PUBLISH_DIST_DIR`, a
    step's `INDEX_URL`, and the runner's own variables, so the other Juniper publishers can copy them verbatim, the
    republish job whole. The version comes from the file names in `SHA256SUMS`, or, in the republish job, from the
    tag.
  - Unchanged: the `release: published` trigger (no `push: tags`), the `testpypi` and `pypi` environments, the job
    names `Publish to TestPyPI` and `Publish to PyPI` (juniper-ml's release-train ceremony finds the two jobs by
    them), the sub-package publishers' `concurrency`, and `publish-image.yml`. A build failure now fails
    `Build and Validate` rather than `Publish to TestPyPI`, so the ceremony reports it as `HALT_PUBLISH` rather than
    `HALT_TESTPYPI`; both stop the train.
  - **Pins**, in the new `src/tests/unit/test_publish_one_artifact.py` ({cases} cases). The static ones read the three
    workflows: one build, in a job without an environment or `id-token`; the job chain, names and per-job
    permissions; the reuse step first in the build job and guarding every later step; each upload after the dist
    check; TestPyPI's JSON checked after the TestPyPI upload, before the install check and before the PyPI upload,
    and PyPI's after; no `skip-existing`; the artifact's name, paths and retention; the republish job's trigger, gate,
    steps and name; the triggers and tag guards; and every copy of a template step byte-identical. The rehearsals run
    each template step's own Python, extracted from `publish.yml`, in a scratch workspace, against a stand-in index and
    a stand-in GitHub API on 127.0.0.1. `util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py`
    makes {mutations} edits to a copy of the workflows, one at a time, each undoing one property, and the tests catch
    each.
  - Docs: `docs/ci_cd/MANUAL.md` (0.3.22) § One Artifact, Checked Against TestPyPI and § Recovering a Release That
    Did Not Reach PyPI, `docs/ci_cd/REFERENCE.md` § One-Artifact Contract, `docs/ci_cd/QUICK_START.md`,
    `docs/DEVELOPER_CHEATSHEET.md` (1.0.12) and `AGENTS.md`.
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
        new_section = section[:cut].rstrip("\n") + "\n" + entry + "\n" + section[cut:]
    return text[:start] + new_section + text[end:]


AGENTS_ROWS = (
    (
        "| Publish | `.github/workflows/publish.yml` | Release (`v*`) | PyPI publish for `juniper-cascor` (TestPyPI → verify → PyPI) |\n",
        "| Publish | `.github/workflows/publish.yml` | Release (`v*`) + `workflow_dispatch` (republish only, from the tag) | PyPI publish for `juniper-cascor`: built once; TestPyPI → sha256 check against TestPyPI's JSON → install verify → PyPI, after TestPyPI's sha256 are checked again → sha256 check against PyPI's JSON. The dispatch republishes TestPyPI's files (one-artifact template and recovery ladder, `docs/ci_cd/MANUAL.md`) |\n",
    ),
    (
        "| Publish protocol | `.github/workflows/publish-protocol.yml` | Release (`juniper-cascor-protocol-v*`) + `workflow_dispatch` | PyPI publish for `juniper-cascor-protocol` |\n",
        "| Publish protocol | `.github/workflows/publish-protocol.yml` | Release (`juniper-cascor-protocol-v*`) + `workflow_dispatch` | PyPI publish for `juniper-cascor-protocol` (the same one-artifact template and republish job) |\n",
    ),
    (
        "| Publish model | `.github/workflows/publish-cascor-model.yml` | Release (`juniper-cascor-model-v*`) + `workflow_dispatch` | PyPI publish for `juniper-cascor-model` |\n",
        "| Publish model | `.github/workflows/publish-cascor-model.yml` | Release (`juniper-cascor-model-v*`) + `workflow_dispatch` | PyPI publish for `juniper-cascor-model` (the same one-artifact template and republish job) |\n",
    ),
)

MANUAL_GUARD_ROWS = (
    (
        "| `publish.yml` | `juniper-cascor` (repo root) | `startsWith(..., 'v')` — e.g. `v0.7.0` | No (`release` only) |\n",
        "| `publish.yml` | `juniper-cascor` (repo root) | `startsWith(..., 'v')` — e.g. `v0.7.0` | Republish only (`workflow_dispatch` from the tag with `republish_from_testpypi`) |\n",
    ),
    (
        "| `publish-protocol.yml` | `juniper-cascor-protocol/` | `juniper-cascor-protocol-v*` | Yes (`workflow_dispatch`) |\n",
        "| `publish-protocol.yml` | `juniper-cascor-protocol/` | `juniper-cascor-protocol-v*` | Yes (`workflow_dispatch` from the tag: a full re-fire, or `republish_from_testpypi`) |\n",
    ),
    (
        "| `publish-cascor-model.yml` | `juniper-cascor-model/` | `juniper-cascor-model-v*` | Yes (`workflow_dispatch`) |\n",
        "| `publish-cascor-model.yml` | `juniper-cascor-model/` | `juniper-cascor-model-v*` | Yes (`workflow_dispatch` from the tag: a full re-fire, or `republish_from_testpypi`) |\n",
    ),
)

MANUAL_OLD_SHAPE = """\
```
Release published (matching tag)
        │
        ▼
   build + twine check
        │
        ▼
   Publish to TestPyPI  (environment: testpypi, id-token: write)
        │
        ▼
   Verify install from TestPyPI ONLY
   (--no-deps, --index-url https://test.pypi.org/simple/)
        │
        ▼
   Publish to PyPI      (environment: pypi, needs: testpypi)
```
"""

MANUAL_NEW_SHAPE = """\
```
Release published (matching tag)
        │
        ▼
   Build and Validate: build + twine check, ONCE (a re-run reuses it)
   SHA256SUMS recorded; dist + SHA256SUMS uploaded as ONE artifact
        │
        ▼
   Publish to TestPyPI  (environment: testpypi, id-token: write)
   download → check against SHA256SUMS → upload
        │
        ▼
   TestPyPI's JSON must list exactly those files and sha256
        │
        ▼
   Verify install from TestPyPI ONLY
   (--no-deps, --index-url https://test.pypi.org/simple/)
        │
        ▼
   Publish to PyPI      (environment: pypi, id-token: write, needs: testpypi)
   download → check against SHA256SUMS → TestPyPI's JSON again → upload
        │
        ▼
   PyPI's JSON must list exactly those files and sha256
```
"""

MANUAL_SECTION = """\
### One Artifact, Checked Against TestPyPI

**Intent:** PyPI receives exactly the files TestPyPI took and the install check tested, and the run proves it. Until 2026-11-15 `publish.yml` ran `python -m build` in each publish job, so PyPI served a second build of every release: the 0.13.0 wheel is `eda26e26…` on PyPI and `f5dbc1b6…` on TestPyPI, and the 0.14.0 wheel `b70f3d39…` against `c5c9a5dc…` (their sdists differ too). Each job also ran an unpinned `pip install build twine`, so a long `pypi` gate could change the build backend between the two builds.

Now the `build` job writes the sdist and wheel once, records their sha256 in `SHA256SUMS`, and uploads both as one artifact; on a re-run attempt it reuses that artifact instead of building again. Each publish job downloads it and checks the files against `SHA256SUMS` before it uploads them. After the TestPyPI upload, TestPyPI's JSON for the version must list exactly those files with those sha256. The PyPI job checks TestPyPI's JSON again before its own upload, and PyPI's after it. An index never takes a second file under a name it already holds, so TestPyPI's record cannot change once the TestPyPI job has run: it witnesses what the install check tested. Only the jobs that upload hold `id-token: write`, so the build cannot mint a credential. The step-by-step contract is in [`REFERENCE.md` § One-Artifact Contract](REFERENCE.md#one-artifact-contract).

**Copying the template into another publish workflow.** The steps marked `One-artifact publish template`, and the whole `republish` job, read nothing but the workflow `env` values `PUBLISH_PACKAGE` (the distribution's name on the index) and `PUBLISH_DIST_DIR` (where the build writes, relative to the workspace), each JSON check's `INDEX_URL`, and the runner's own variables. Copy them verbatim, set the two values, and point every upload's `packages-dir` at `${{ env.PUBLISH_DIST_DIR }}/`. Keep the order:

1. first in the build job, `Reuse an earlier attempt's artifact`, and `if: steps.reuse.outputs.reuse != 'true'` on every later step of that job;
2. after the build: `Record SHA256SUMS`, then `Upload dist artifacts`;
3. in each publish job: `Download dist artifacts`, then `Verify the dist against SHA256SUMS`, before the upload;
4. TestPyPI's JSON after the TestPyPI upload and before the install check, and again before the PyPI upload;
5. PyPI's JSON after the PyPI upload;
6. the `republish` job and the `workflow_dispatch` input `republish_from_testpypi`, in the same workflow file: PyPI's trusted publisher names that file and the `pypi` environment.

Give the workflow `permissions: {}` (or `contents: read`) and each job its own: the build `contents: read` and `actions: read`; each uploading job `id-token: write`, plus `contents: read` where it checks out; the republish job `actions: read` and `id-token: write`. If the build job already runs on a dispatch, exclude the republish dispatch from its `if:`, as the sub-package publishers do. A checkout empties the workspace, so none may run between a job's download and its last template step. Never set `skip-existing` on the TestPyPI upload: an earlier file under the same name would be kept silently, and the install check would test that file.

### Recovering a Release That Did Not Reach PyPI

The Overtoad's ladder (ruling of 2026-11-15), in this order. Every rung publishes the files TestPyPI took, or nothing.

1. **Republish TestPyPI's files.** Dispatch the release's own workflow from its tag:

   ```bash
   gh workflow run publish.yml --repo pcalnon/juniper-cascor --ref v<version> -f republish_from_testpypi=true
   # sub-packages: publish-cascor-model.yml --ref juniper-cascor-model-v<version>,
   #               publish-protocol.yml --ref juniper-cascor-protocol-v<version>
   ```

   Only `Republish the tested files (dispatch only)` runs. It waits at the `pypi` gate like the release run (a fresh approval, then the 5-minute timer), builds nothing, downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It does not depend on the release run's age, only on TestPyPI still holding the files, and it works only from a tag whose workflow carries the job: tags cut before this change merged do not.
2. **If that fails, within 30 days of the release run: "Re-run failed jobs"** on the release run. The re-run reuses the run's artifact and waits at the gate again (a fresh approval, then the 5-minute timer). GitHub refuses a re-run after 30 days.
3. **Otherwise, cut a new patch version.**

The usual case is a PyPI job that failed after waiting 30 days for approval, GitHub's cap on a deployment's wait: the run is then past its 30-day re-run window, and rung 1 is the way back. While the artifact exists, `gh run download <run-id> --repo pcalnon/juniper-cascor -n juniper-cascor-dist` fetches the exact files that run built, for inspection.

**Never "Re-run all jobs"** on a publish run, nor `gh run rerun <id>` without `--failed`: use **Re-run failed jobs**. download-artifact takes the newest artifact of a name, so a re-run build became the file every later job uploaded. juniper-ml's run 38045867684 published a rebuild of juniper-ci-tools 0.9.1 that way: PyPI serves `1dc8e01e…`, TestPyPI `ade363e8…`. The build job's `Reuse an earlier attempt's artifact` step now skips such a rebuild, but a tag cut before it lacks the step.

"""

MANUAL_OLD_REFIRE_BLOCK = "```bash\n# After fixing a transient TestPyPI/PyPI failure for protocol or model:\ngh workflow run publish-protocol.yml\n# or\ngh workflow run publish-cascor-model.yml\n```\n"
MANUAL_NEW_REFIRE_BLOCK = (
    "```bash\n"
    "# A full re-fire builds again: only for a failure BEFORE TestPyPI took the version. Always from the release tag.\n"
    "gh workflow run publish-protocol.yml --repo pcalnon/juniper-cascor --ref juniper-cascor-protocol-vX.Y.Z\n"
    "# or\n"
    "gh workflow run publish-cascor-model.yml --repo pcalnon/juniper-cascor --ref juniper-cascor-model-vX.Y.Z\n"
    "```\n"
)
MANUAL_OLD_REFIRE = "`publish.yml` (main package) has no `workflow_dispatch` — create a new Release or re-run the failed jobs from the Actions UI for that release run.\n"
MANUAL_NEW_REFIRE = (
    "Dispatch from the release tag: both publish environments admit tag refs only, so a dispatch from a branch fails at `Publish to TestPyPI`. A full re-fire builds new files, so it works only while TestPyPI does not hold the version yet. Once TestPyPI took it, follow [Recovering a Release That Did Not Reach PyPI](#recovering-a-release-that-did-not-reach-pypi), which `-f republish_from_testpypi=true` starts.\n"
    "\n"
    "`publish.yml` (main package) has a `workflow_dispatch` for the republish job only; a dispatch without the input runs nothing. Otherwise use **Re-run failed jobs** on the release run, never \"Re-run all jobs\". A new Release is a new run, which TestPyPI refuses for a version it already holds.\n"
)
MANUAL_TROUBLE_ANCHOR = "| TestPyPI verify can't find the version | Index lag | Protocol/model retry 5× with 10s sleep; main package sleeps 30s once — re-run the verify step if lag exceeds that |\n"
MANUAL_TROUBLE_ROWS = (
    "| `Verify TestPyPI serves exactly these files` or `Verify PyPI serves exactly these files` fails: the index lists a file this run did not build, or with another sha256 | The index already held other files for this version (an earlier run's build), or the artifact is not what the build recorded | Do not publish this version from this run; find which upload put the other file there. When the TestPyPI check failed, the run stopped before the PyPI upload |\n"
    "| `Verify TestPyPI still serves exactly these files` fails in the PyPI job, before its upload | TestPyPI did not answer within the bound, or its JSON no longer matches the artifact | Nothing reached PyPI. A TestPyPI outage has no override: once TestPyPI answers, use Re-run failed jobs (a fresh approval, then the 5-minute timer). A mismatch means the artifact is not what TestPyPI took: do not publish it |\n"
    "| A JSON check gives up after 20 attempts | The index never listed the version or a file within the bound: 19 sleeps of 15 s (285 s) plus up to 20 request timeouts of 30 s, about 15 minutes at worst | Re-run failed jobs: the index accepts a re-upload of identical files, and the check runs again. Re-running the PyPI job needs a fresh approval and waits the 5-minute timer again |\n"
    "| `Verify the dist against SHA256SUMS` fails | The downloaded directory holds a file the build did not record, or misses or alters one | Re-run failed jobs; if it fails again, the artifact is wrong: do not publish it |\n"
    "| PyPI's files differ from TestPyPI's after a re-run | \"Re-run all jobs\" (or `gh run rerun <id>` without `--failed`) on a tag cut before the reuse step: the rebuild became the newest `<pkg>-dist` | Use Re-run failed jobs. The reuse step in `Build and Validate` skips such a rebuild |\n"
    "| The PyPI job failed after waiting 30 days for approval, or `Download dist artifacts` finds no artifact | The gate's 30-day cap passed, which also puts the run past GitHub's 30-day re-run window; or the artifact expired (90 days) | Follow [the recovery ladder](#recovering-a-release-that-did-not-reach-pypi): the republish dispatch copies TestPyPI's files without the artifact |\n"
    "| `Republish the tested files` fails at `Download TestPyPI's files and verify them` | A file's bytes do not hash to TestPyPI's JSON, the JSON lists a file that is not this package and version, or the release run's `SHA256SUMS` disagrees with TestPyPI | Do not publish TestPyPI's files: within 30 days of the release run, use Re-run failed jobs on it; otherwise cut a new patch version |\n"
)

REFERENCE_WORKFLOW_ROW_OLD = "| `publish.yml` | `juniper-cascor` | `release: published` | `startsWith(tag, 'v')` | `testpypi` → `pypi` | `pypa/gh-action-pypi-publish` (SHA-pinned) |\n"
REFERENCE_WORKFLOW_ROW_NEW = "| `publish.yml` | `juniper-cascor` | `release: published` + `workflow_dispatch` (republish only) | `startsWith(tag, 'v')` | `testpypi` → `pypi` | `pypa/gh-action-pypi-publish` (SHA-pinned) |\n"
REFERENCE_SECTION = """\
### One-Artifact Contract

All three publishers build once and hand both publish jobs one artifact, `<PUBLISH_PACKAGE>-dist`: the dist directory and `SHA256SUMS`, kept 90 days so it outlives the `pypi` gate. The steps that carry it are a template: they read only the workflow `env` values `PUBLISH_PACKAGE` and `PUBLISH_DIST_DIR`, a JSON check's `INDEX_URL`, and the runner's own variables ([`MANUAL.md` § One Artifact, Checked Against TestPyPI](MANUAL.md#one-artifact-checked-against-testpypi)).

| Step | Job | What it checks |
|------|-----|----------------|
| `Reuse an earlier attempt's artifact` | build, first; runs on attempt 2 and later | Lists the run's artifacts; when an unexpired `<PUBLISH_PACKAGE>-dist` is there, every later build step is skipped (`if: steps.reuse.outputs.reuse != 'true'`), so a re-run cannot make a rebuild the newest artifact. An API failure fails the job |
| `Record SHA256SUMS` | build | The dist directory holds only wheels and sdists; writes `<sha256>  <file>` lines (check by hand: `cd dist && sha256sum -c ../SHA256SUMS`) |
| `Upload dist artifacts` | build | Uploads the dist directory and `SHA256SUMS` as one artifact (`if-no-files-found: error`, `retention-days: 90`) |
| `Download dist artifacts` | both publish jobs | Restores both into the workspace; no checkout may run after it before the job's last template step |
| `Verify the dist against SHA256SUMS` | before every upload | The directory holds exactly the listed files, with their sha256 |
| `Verify TestPyPI serves exactly these files` | TestPyPI job, after the upload | `https://test.pypi.org/pypi/<package>/<version>/json` lists exactly those files and sha256 |
| `Verify TestPyPI still serves exactly these files` | PyPI job, before the upload | The same, again |
| `Verify PyPI serves exactly these files` | PyPI and republish jobs, after the upload | The same, on `https://pypi.org` |
| `Find the release run's artifact` | republish (dispatch only), first | The version from the tag (`v<version>` or `<package>-v<version>`; anything else is refused); the newest release run for that tag still holding `<PUBLISH_PACKAGE>-dist` |
| `Download TestPyPI's files and verify them` | republish | Every file TestPyPI's JSON lists for the version: each file's bytes against the JSON's sha256, only this package and version, and the release run's `SHA256SUMS` while it exists; writes `SHA256SUMS`. Nothing is built |

The JSON checks poll up to 20 times, 15 s apart (`HASH_CHECK_ATTEMPTS`, `HASH_CHECK_INTERVAL`), while the version is not served yet or a file is missing (CDN lag): 285 s of sleep, plus up to 20 request timeouts of 30 s. A file listed with another sha256, or one the run did not build, fails at once. The version comes from the file names in `SHA256SUMS`, not from the tag. The republish job is step 1 of the recovery ladder: [`MANUAL.md` § Recovering a Release That Did Not Reach PyPI](MANUAL.md#recovering-a-release-that-did-not-reach-pypi). Pinned by `src/tests/unit/test_publish_one_artifact.py`.

"""
REFERENCE_PERMISSIONS_OLD = "| `permissions.id-token` | `write` | OIDC token for Trusted Publishing |\n| `permissions.contents` | `read` (protocol/model) | Checkout / sparse-checkout for version verify |\n"
REFERENCE_PERMISSIONS_NEW = (
    "| workflow `permissions` | `{}` (`publish.yml`); `contents: read` (protocol/model) | No job inherits `id-token: write` |\n"
    "| build job | `contents: read`, `actions: read` | Checkout; the reuse step lists the run's artifacts. No `id-token`, so the build backend cannot mint a token |\n"
    "| TestPyPI job | `contents: read`, `id-token: write` | Checkout / sparse-checkout for the install check; OIDC token for Trusted Publishing |\n"
    "| PyPI job | `id-token: write` (`publish.yml`); plus `contents: read` (protocol/model) | OIDC token for Trusted Publishing |\n"
    "| republish job | `actions: read`, `id-token: write` | Find and download the release run's artifact; OIDC token for Trusted Publishing |\n"
)
REFERENCE_CONSTRAINT_ANCHOR = "- Do not add `push: tags` next to `release: published` (double-fire race; juniper-ml#555).\n"
REFERENCE_CONSTRAINTS = (
    "- No `skip-existing` on a TestPyPI upload: an earlier file under the same name would be kept silently and the install check would test it. The sha256 check after the upload would fail the run instead.\n"
    "- A release that did not reach PyPI: the republish dispatch, then (within 30 days) **Re-run failed jobs**, then a new patch version ([`MANUAL.md`](MANUAL.md#recovering-a-release-that-did-not-reach-pypi)). Never \"Re-run all jobs\", nor `gh run rerun <id>` without `--failed`.\n"
)

QUICK_START_OLD = "Pipeline shape for every package: build/`twine check` → TestPyPI → install verify (`--no-deps`, TestPyPI index only) → PyPI.\n"
QUICK_START_NEW = "Pipeline shape for every package: build/`twine check` once, with `SHA256SUMS` → TestPyPI → TestPyPI's JSON must list exactly those sha256 → install verify (`--no-deps`, TestPyPI index only) → TestPyPI's JSON checked again → PyPI → PyPI's JSON checked. Both publish jobs upload the build job's one artifact ([`MANUAL.md` § One Artifact, Checked Against TestPyPI](MANUAL.md#one-artifact-checked-against-testpypi)). A release that did not reach PyPI: [§ Recovering a Release That Did Not Reach PyPI](MANUAL.md#recovering-a-release-that-did-not-reach-pypi).\n"

CHEATSHEET_OLD = "TestPyPI verify uses `--no-deps` and TestPyPI index only. Keep"
CHEATSHEET_NEW = "TestPyPI verify uses `--no-deps` and TestPyPI index only. Every publisher builds once: both publish jobs upload the build job's artifact (the dist directory and `SHA256SUMS`), TestPyPI's JSON must list exactly those sha256 after the TestPyPI upload and again before the PyPI one, and PyPI's after; only the uploading jobs hold `id-token: write`. A release that did not reach PyPI: dispatch its workflow from the tag with `-f republish_from_testpypi=true` (copies TestPyPI's files, builds nothing); if that fails, within 30 days use **Re-run failed jobs** (never \"Re-run all jobs\", nor `gh run rerun` without `--failed`); otherwise cut a new patch version. Keep"


def apply(tree: Path, publish_yml: str, test_file: str, verify_script: str, cases: str, mutations: str) -> dict[str, str]:
    """Return {repo path: new text} for every file the change writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    out: dict[str, str] = {}
    current = read(".github/workflows/publish.yml")
    if sha256(current) != BASE_SHA256[".github/workflows/publish.yml"]:
        raise Refused("publish.yml moved since f5ffefb7: re-derive the new file against the new base before re-running")
    out[".github/workflows/publish.yml"] = publish_yml
    blocks = template_blocks(publish_yml)
    republish = republish_job(publish_yml)
    for rel, package in ((".github/workflows/publish-cascor-model.yml", "juniper-cascor-model"), (".github/workflows/publish-protocol.yml", "juniper-cascor-protocol")):
        text = read(rel)
        if sha256(text) != BASE_SHA256[rel]:
            print(f"note: {rel} moved since f5ffefb7; applying by anchors")
        out[rel] = sub_package_workflow(text, package, blocks, republish, rel)
    for rel, text in ((TEST_PATH, test_file), (VERIFY_PATH, verify_script)):
        if (tree / rel).exists():
            raise Refused(f"{rel} already exists on this base")
        out[rel] = text
    out["CHANGELOG.md"] = changelog(read("CHANGELOG.md"), cases, mutations)
    agents = read("AGENTS.md")
    for old, new in AGENTS_ROWS:
        agents = replace_once(agents, old, new, "AGENTS.md")
    out["AGENTS.md"] = agents
    manual = read("docs/ci_cd/MANUAL.md")
    manual = replace_once(manual, "**Version**: 0.3.21  \n", "**Version**: 0.3.22  \n", "MANUAL.md version")
    for old, new in MANUAL_GUARD_ROWS:
        manual = replace_once(manual, old, new, "MANUAL.md tag-guard table")
    manual = replace_once(manual, MANUAL_OLD_SHAPE, MANUAL_NEW_SHAPE, "MANUAL.md pipeline shape")
    manual = replace_once(manual, "### Operator Constraints\n", MANUAL_SECTION + "### Operator Constraints\n", "MANUAL.md sections")
    manual = replace_once(manual, MANUAL_OLD_REFIRE_BLOCK, MANUAL_NEW_REFIRE_BLOCK, "MANUAL.md re-firing commands")
    manual = replace_once(manual, MANUAL_OLD_REFIRE, MANUAL_NEW_REFIRE, "MANUAL.md re-firing")
    manual = replace_once(manual, MANUAL_TROUBLE_ANCHOR, MANUAL_TROUBLE_ANCHOR + MANUAL_TROUBLE_ROWS, "MANUAL.md troubleshooting")
    out["docs/ci_cd/MANUAL.md"] = manual
    reference = read("docs/ci_cd/REFERENCE.md")
    reference = replace_once(reference, REFERENCE_WORKFLOW_ROW_OLD, REFERENCE_WORKFLOW_ROW_NEW, "REFERENCE.md workflow row")
    reference = replace_once(reference, "### Permissions and Concurrency\n", REFERENCE_SECTION + "### Permissions and Concurrency\n", "REFERENCE.md section")
    reference = replace_once(reference, REFERENCE_PERMISSIONS_OLD, REFERENCE_PERMISSIONS_NEW, "REFERENCE.md permissions")
    reference = replace_once(reference, REFERENCE_CONSTRAINT_ANCHOR, REFERENCE_CONSTRAINT_ANCHOR + REFERENCE_CONSTRAINTS, "REFERENCE.md constraints")
    out["docs/ci_cd/REFERENCE.md"] = reference
    out["docs/ci_cd/QUICK_START.md"] = replace_once(read("docs/ci_cd/QUICK_START.md"), QUICK_START_OLD, QUICK_START_NEW, "QUICK_START.md pipeline shape")
    cheatsheet = read("docs/DEVELOPER_CHEATSHEET.md")
    cheatsheet = replace_once(cheatsheet, "**Version**: 1.0.11  |  **Date**: 2026-11-13  |", "**Version**: 1.0.12  |  **Date**: 2026-11-15  |", "DEVELOPER_CHEATSHEET.md header")
    cheatsheet = replace_once(cheatsheet, CHEATSHEET_OLD, CHEATSHEET_NEW, "DEVELOPER_CHEATSHEET.md publish line")
    out["docs/DEVELOPER_CHEATSHEET.md"] = cheatsheet
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh copy of juniper-cascor's tree (edited in place)")
    parser.add_argument("--publish-yml", required=True, type=Path, help="the new .github/workflows/publish.yml")
    parser.add_argument("--test-file", required=True, type=Path, help="the new src/tests/unit/test_publish_one_artifact.py")
    parser.add_argument("--verify-script", required=True, type=Path, help=f"the new {VERIFY_PATH}")
    parser.add_argument("--changelog-cases", default="{cases}", help="the case count the CHANGELOG entry states")
    parser.add_argument("--changelog-mutations", default="{mutations}", help="the mutation count the CHANGELOG entry states")
    args = parser.parse_args(argv)
    try:
        out = apply(args.tree, args.publish_yml.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.verify_script.read_text(encoding="utf-8"), args.changelog_cases, args.changelog_mutations)
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
