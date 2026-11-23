#!/usr/bin/env python3
"""Apply juniper-cascor's one-artifact publish template to juniper-recurrence's three PyPI publishers, every edit asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (port of juniper-cascor#763 and #767, "publish one artifact to TestPyPI and PyPI", to
        juniper-recurrence)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (the template's extraction, ``template_blocks`` and
         ``republish_job``, and the sub-package rewrite this adapts); util/ad-hoc/2026-11-15_publish_port_template_identity.py
         (the cross-repo identity check); util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree that ``main`` has since moved past silently
reverts whatever merged in between. Every edit here is therefore replayable on a fresh clone of juniper-recurrence's
``main``, and each one is an exact-once anchored replacement: when an anchor does not match exactly once, this refuses and
writes nothing. The template steps and the republish job are never retyped: they are extracted from juniper-cascor's
``publish.yml`` by the cascor script's own ``template_blocks`` and ``republish_job``, so the copies are byte-identical.

The edits, on a juniper-recurrence tree:

- ``.github/workflows/publish-recurrence-app.yml``, ``-client.yml`` and ``-model.yml`` get juniper-cascor's SUB-PACKAGE
  shape (its ``publish-cascor-model.yml``): the ``republish_from_testpypi`` dispatch input (a plain dispatch still re-fires
  the whole publish); top-level ``permissions: contents: read`` and per-job permissions (``id-token: write`` only on the
  three uploading jobs); the two template parameters in the workflow ``env``; a build guard that a republish dispatch does
  not pass; the reuse step first in the build job and the reuse condition on every later step but the push-only
  release gate; ``Record SHA256SUMS`` and the one artifact, kept 90 days (was 7); the dist check before each upload;
  TestPyPI's JSON after the TestPyPI upload (the sparse checkout and the install check follow it) and before the PyPI
  upload, and PyPI's after; ``skip-existing`` dropped from both uploads; the republish job. The concurrency comment, which
  said ``skip-existing`` made an overlapping run a no-op, now says what an overlapping run does instead.
- ``.github/workflows/ci-recurrence-app.yml``: the change filter (``on.push.paths`` and the ``changes`` job) also names the
  three publish workflows, so the new test runs on a pull request that edits only one of them.
- ``juniper-recurrence/tests/test_publish_one_artifact.py`` is copied from ``--test-file`` (the port of juniper-cascor's
  ``src/tests/unit/test_publish_one_artifact.py``); it must not exist yet.
- ``juniper-recurrence/CHANGELOG.md`` gets one ``[Unreleased]`` / ``### Fixed`` entry (repo-wide changes are recorded
  there); ``juniper-recurrence/README.md`` § Publishing gets the contract and the owner's recovery ladder with the three
  dispatch commands; the root ``AGENTS.md`` (under a 20,000-character budget) and ``juniper-recurrence-client/AGENTS.md``
  get a sentence each pointing at it.
- After the review of juniper-recurrence#236 (its second commit): the README also says what a plain dispatch is for and
  how to recover once one has reached TestPyPI, and what to do for a tag cut before this change; the root ``AGENTS.md``
  no longer says the publishers are "path-scoped so they never cross-fire" (every Release fires all three; the tag
  guard skips a sibling's), on line 122 or in the layout tree; the client ``AGENTS.md`` header takes the package's own
  version from ``_version.py``.

    python3 -I util/ad-hoc/2026-11-15_juniper-recurrence_one_artifact_publish_port.py --tree <fresh juniper-recurrence clone> \\
        --template <juniper-cascor clone>/.github/workflows/publish.yml --test-file <ported test file> \\
        [--cascor-edits <path to 2026-11-15_cascor_one_artifact_publish_edits.py>] [--last-updated YYYY-MM-DD] [--check]

``--check`` computes every edit and reports, writing nothing. Exit status: 0 when every edit applied (or would apply);
1 when an anchor did not match exactly once, the test file exists already, or the root AGENTS.md would pass its budget
(nothing is written).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path

#: The cascor script whose template extraction and anchors this reuses (it sits beside this one in util/ad-hoc/).
CASCOR_EDITS = Path(__file__).resolve().with_name("2026-11-15_cascor_one_artifact_publish_edits.py")
#: workflow file -> its package: the PyPI name (PUBLISH_PACKAGE), its tag prefix, and the directory it builds in.
WORKFLOWS = {
    ".github/workflows/publish-recurrence-app.yml": "juniper-recurrence",
    ".github/workflows/publish-recurrence-client.yml": "juniper-recurrence-client",
    ".github/workflows/publish-recurrence-model.yml": "juniper-recurrence-model",
}
TEST_PATH = "juniper-recurrence/tests/test_publish_one_artifact.py"
CI_APP = ".github/workflows/ci-recurrence-app.yml"
CHANGELOG = "juniper-recurrence/CHANGELOG.md"
README = "juniper-recurrence/README.md"
AGENTS = "AGENTS.md"
CLIENT_AGENTS = "juniper-recurrence-client/AGENTS.md"
#: conf/memory_budget.json's ceiling for the root AGENTS.md, in characters (a required check fails above it).
AGENTS_CEILING = 20000
SKIP_EXISTING = "          skip-existing: true  # tolerate an already-uploaded immutable artifact (re-run)\n"
MANUAL = "https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md"


def load_cascor_edits(path: Path):
    """Import the cascor script by path (registered in sys.modules first, as a path-loaded module must be)."""
    spec = importlib.util.spec_from_file_location("cascor_one_artifact_publish_edits", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CONCURRENCY_OLD = (
    "  # Belt-and-suspenders serialization keyed on the ref. The primary dedupe is the single\n"
    "  # `release: published` trigger above; `skip-existing` on the publish steps makes any residual\n"
    "  # overlap (e.g. a manual dispatch during a release) a no-op rather than an immutable-upload race.\n"
)
CONCURRENCY_NEW = (
    "  # Belt-and-suspenders serialization keyed on the ref. The primary dedupe is the single\n"
    "  # `release: published` trigger above; this group serializes any residual overlap (e.g. a manual\n"
    "  # dispatch during a release). No upload skips an existing file any more (the one-artifact publish,\n"
    "  # 2026-11-15), so a later run cannot replace what an earlier one uploaded: its TestPyPI upload fails.\n"
)
GUARD_COMMENT_OLD = "workflow_dispatch always runs."
GUARD_COMMENT_NEW = "A dispatch runs it, unless it asks for the republish job."


def env_block(package: str) -> str:
    return (
        "env:\n"
        "  # The one-artifact publish template's two parameters (the template's source is juniper-cascor's publish.yml): the\n"
        "  # distribution's name on PyPI and TestPyPI, and the directory the build writes the sdist and wheel to, relative to\n"
        "  # the workspace.\n"
        f"  PUBLISH_PACKAGE: {package}\n"
        f"  PUBLISH_DIST_DIR: {package}/dist\n"
        "\n"
    )


def port_workflow(c, text: str, package: str, blocks: dict[str, str], republish: str, where: str) -> str:
    """juniper-cascor's ``sub_package_workflow``, adapted: these publishers also drop ``skip-existing`` from both uploads,
    and their guard and concurrency comments differ from cascor's."""
    replace_once = c.replace_once
    text = replace_once(text, c.DISPATCH_OLD, c.DISPATCH_NEW, where)
    text = replace_once(text, "permissions:\n  id-token: write\n  contents: read\n", "# Each job adds what it needs to this; only the jobs that upload add id-token: write.\npermissions:\n  contents: read\n", where)
    text = replace_once(text, CONCURRENCY_OLD, CONCURRENCY_NEW, where)
    text = replace_once(text, "  cancel-in-progress: false\n\njobs:\n", "  cancel-in-progress: false\n\n" + env_block(package) + "jobs:\n", where)
    text = replace_once(text, GUARD_COMMENT_OLD, GUARD_COMMENT_NEW, where)
    text = replace_once(
        text,
        f"    if: github.event_name != 'release' || startsWith(github.event.release.tag_name, '{package}-v')\n",
        f"    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
        where,
    )
    build_head_old = f"    runs-on: ubuntu-latest\n    defaults:\n      run:\n        working-directory: {package}\n    steps:\n" + c.CHECKOUT + "\n"
    build_head_new = (
        "    runs-on: ubuntu-latest\n"
        "    permissions:\n"
        "      contents: read\n"
        "      actions: read  # the reuse step lists this run's artifacts\n"
        f"    defaults:\n      run:\n        working-directory: {package}\n    steps:\n"
        + blocks["build/Reuse an earlier attempt's artifact"]
        + "\n"
        + c.CHECKOUT
        + c.REUSE_IF
        + "\n"
    )
    text = replace_once(text, build_head_old, build_head_new, where)
    for step in (
        "      - uses: actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0  # v7.1.0\n",
        "      - name: Install build tools\n",
        "      - name: Build sdist + wheel\n",
        "      - name: Validate distribution metadata\n",
    ):
        text = replace_once(text, step, step + c.REUSE_IF, where)
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
    old_testpypi = old_download + c.PUBLISH_STEP.format(index="TestPyPI") + "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: dist/\n          verbose: true\n" + SKIP_EXISTING + "\n"
    new_testpypi = (
        blocks["testpypi/Download dist artifacts"]
        + "\n"
        + blocks["testpypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + c.PUBLISH_STEP.format(index="TestPyPI")
        + "          repository-url: https://test.pypi.org/legacy/\n          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n\n"
        + blocks["testpypi/Verify TestPyPI serves exactly these files"]
        + "\n"
    )
    text = replace_once(text, old_testpypi, new_testpypi, where)
    old_pypi = old_download + c.PUBLISH_STEP.format(index="PyPI") + "          packages-dir: dist/\n          verbose: true\n" + SKIP_EXISTING
    new_pypi = (
        blocks["pypi/Download dist artifacts"]
        + "\n"
        + blocks["pypi/Verify the dist against SHA256SUMS"]
        + "\n"
        + blocks["pypi/Verify TestPyPI still serves exactly these files"]
        + "\n"
        + c.PUBLISH_STEP.format(index="PyPI")
        + "          packages-dir: ${{ env.PUBLISH_DIST_DIR }}/\n          verbose: true\n\n"
        + blocks["pypi/Verify PyPI serves exactly these files"]
    )
    if not text.endswith(old_pypi):
        raise c.Refused(f"{where}: the PyPI job's download and upload are not the file's last steps")
    text = replace_once(text, old_pypi, new_pypi, where)
    if "skip-existing" in text:
        raise c.Refused(f"{where}: skip-existing survives the edit")
    return text + "\n" + republish


CI_PUSH_OLD = '      - "juniper-recurrence/**"\n      - ".github/workflows/ci-recurrence-app.yml"\n  pull_request:\n'
CI_PUSH_NEW = (
    '      - "juniper-recurrence/**"\n'
    '      - ".github/workflows/ci-recurrence-app.yml"\n'
    "      # tests/test_publish_one_artifact.py reads the three PyPI publish workflows.\n"
    '      - ".github/workflows/publish-recurrence-app.yml"\n'
    '      - ".github/workflows/publish-recurrence-client.yml"\n'
    '      - ".github/workflows/publish-recurrence-model.yml"\n'
    "  pull_request:\n"
)
CI_FILTER_OLD = (
    "          # path-filters, and a push has no base ref to diff against.\n"
    '          if [[ "${EVENT_NAME}" != "pull_request" ]]; then\n'
    "            changed=true\n"
    '          elif git diff --name-only "origin/${BASE_REF}...HEAD" \\\n'
    "               | grep -qE '^(juniper-recurrence/|\\.github/workflows/ci-recurrence-app\\.yml$)'; then\n"
)
CI_FILTER_NEW = (
    "          # path-filters, and a push has no base ref to diff against. The three PyPI publish workflows count as\n"
    "          # the app's: tests/test_publish_one_artifact.py reads them, and must run on a PR that edits only one.\n"
    '          if [[ "${EVENT_NAME}" != "pull_request" ]]; then\n'
    "            changed=true\n"
    '          elif git diff --name-only "origin/${BASE_REF}...HEAD" \\\n'
    "               | grep -qE '^(juniper-recurrence/|\\.github/workflows/(ci-recurrence-app|publish-recurrence-(app|client|model))\\.yml$)'; then\n"
)

CHANGELOG_ANCHOR = "### Fixed\n\n- **A failing informational Python 3.15 leg no longer shows as a failed check**"
CHANGELOG_ENTRY = """\
### Fixed

- **Each PyPI publish sends TestPyPI and PyPI the same files, and checks them by sha256** (repo-wide:
  `publish-recurrence-app.yml`, `publish-recurrence-client.yml` and `publish-recurrence-model.yml`; recorded here, as
  repo-wide CI changes are). The port of juniper-cascor#763 and #767, after the owner's directive of 2026-11-15:
  "deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the
  artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping
  through the cracks again." These publishers already built once and gave both publish jobs one artifact, and every
  release so far is byte-identical on the two indexes (26 versions compared on 2026-11-15), but nothing checked it:
  both uploads set `skip-existing`, which silently keeps an earlier file under the same name; the artifact expired
  after 7 days while the `pypi` gate may wait 30; and "Re-run all jobs" re-ran the build, whose artifact every later
  download takes. juniper-ml's run 38045867684 published a second build of juniper-ci-tools 0.9.1 to PyPI that way.
  - The build job records `SHA256SUMS` and uploads it with the dist as one artifact, kept 90 days. A re-run attempt
    finds that artifact and builds nothing.
  - Each publish job checks the downloaded files against `SHA256SUMS` before it uploads. TestPyPI's JSON must list
    exactly those files and sha256 after the TestPyPI upload, before the install check (whose sparse checkout now
    follows it), and again before the PyPI upload; PyPI's JSON must do the same after the PyPI upload. Neither
    upload sets `skip-existing`.
  - Only the three uploading jobs hold `id-token: write`; it was workflow-level, so the build, which runs the package's
    build backend, could mint an OIDC token. The workflow level is `contents: read`.
  - A dispatch from a release tag with `-f republish_from_testpypi=true` runs a new job alone, `Republish the tested
    files (dispatch only)`: behind the `pypi` gate, it copies TestPyPI's files for that version to PyPI, each checked
    by sha256, and builds nothing. It is the first rung of the owner's recovery ladder (the README's Publishing
    section). A dispatch without the input still re-fires the whole publish.
  - The template steps and the republish job are verbatim copies of juniper-cascor's, applied by juniper-ml's
    `util/ad-hoc/2026-11-15_juniper-recurrence_one_artifact_publish_port.py`. `tests/test_publish_one_artifact.py`
    pins the wiring and what each workflow kept, and runs each template step's own Python against a stand-in index
    and GitHub API on 127.0.0.1. `ci-recurrence-app.yml`'s change filter now names the three publish workflows, so it
    runs on a pull request that edits only one of them.

- **A failing informational Python 3.15 leg no longer shows as a failed check**"""

README_ANCHOR = """\
```bash
# Cut a GitHub Release on a juniper-recurrence-v* tag (the ecosystem convention — not a
# bare `git push <tag>`); the Release drives publish-recurrence-app.yml (TestPyPI → PyPI).
gh release create juniper-recurrence-v0.2.0 --generate-notes
```

## Ecosystem
"""
README_NEW = f"""\
```bash
# Cut a GitHub Release on a juniper-recurrence-v* tag (the ecosystem convention — not a
# bare `git push <tag>`); the Release drives publish-recurrence-app.yml (TestPyPI → PyPI).
gh release create juniper-recurrence-v0.2.0 --generate-notes
```

The client (`juniper-recurrence-client`) publishes the same way on `juniper-recurrence-client-v*` tags, each package
from its own workflow. Each run builds once, and both indexes get those same files: the build records their sha256 in
`SHA256SUMS`, each publish job checks the files against it before uploading, and TestPyPI's JSON must list exactly
those sha256 after the TestPyPI upload and again before the PyPI upload, and PyPI's after it. The steps are a verbatim
copy of juniper-cascor's template:
[One Artifact, Checked Against TestPyPI]({MANUAL}#one-artifact-checked-against-testpypi).

### A release that did not reach PyPI

The owner's recovery ladder (2026-11-15), in this order. Every rung publishes the files TestPyPI took, or nothing
([juniper-cascor's account]({MANUAL}#recovering-a-release-that-did-not-reach-pypi)).

1. **Republish TestPyPI's files.** Dispatch the package's workflow from its release tag. Only the job
   `Republish the tested files (dispatch only)` runs: it waits at the `pypi` gate (an approval, then the 5-minute
   timer), builds nothing, and copies TestPyPI's files for that version to PyPI, each checked by sha256.

   ```bash
   gh workflow run publish-recurrence-app.yml --repo pcalnon/juniper-recurrence --ref juniper-recurrence-v<version> -f republish_from_testpypi=true
   gh workflow run publish-recurrence-model.yml --repo pcalnon/juniper-recurrence --ref juniper-recurrence-model-v<version> -f republish_from_testpypi=true
   gh workflow run publish-recurrence-client.yml --repo pcalnon/juniper-recurrence --ref juniper-recurrence-client-v<version> -f republish_from_testpypi=true
   ```

2. **If that fails, within 30 days of the release run: Re-run failed jobs** on that run. The re-run reuses the run's
   artifact, kept 90 days, and waits at the gate again.
3. **Otherwise, cut a new patch version.**

**Never "Re-run all jobs"** on a publish run, nor `gh run rerun <id>` without `--failed`. Dispatch from the tag: both
publish environments admit tags only.

**A dispatch without `republish_from_testpypi` is only for a release that never reached TestPyPI.** It re-fires the
whole publish and builds again. If that re-fire puts its own files on TestPyPI and its PyPI job then fails, the ladder
above targets the wrong run: while the release run's artifact exists, rung 1 refuses, because that run's `SHA256SUMS`
disagree with TestPyPI's files, and rung 2 on the release run re-uploads a build TestPyPI rejects. Use **Re-run failed
jobs** on the dispatch run instead, within 30 days of it.

**The ladder holds only for a tag cut after the one-artifact publish change of 2026-11-15 merged.** An older tag's
workflow is the old one: no republish job, `skip-existing` on both uploads, no sha256 check, a rebuild on every
dispatch, and a 7-day artifact. Never dispatch such a tag: a plain dispatch would rebuild, skip the TestPyPI upload,
test TestPyPI's original files and then push the rebuild to PyPI (the juniper-ci-tools 0.9.1 defect, which "Re-run all
jobs" caused there). For such a tag, use **Re-run failed jobs** on its release run within 7 days of it; otherwise cut a
new patch version.

## Ecosystem
"""

# Review of #236: "path-scoped so they never cross-fire" was wrong. Every Release fires all three publishers, and each
# build job's tag-prefix guard skips a sibling's tag (runs 40417897955 and 41935261293 concluded `skipped`).
AGENTS_OLD = "(path-scoped so they never cross-fire). TestPyPI-first, then PyPI, via OIDC trusted publishing.\n"
AGENTS_NEW = (
    "(every Release fires all three publishers; each build job's tag-prefix guard skips a sibling's tag). TestPyPI-first,"
    " then PyPI, via OIDC trusted publishing. Each run builds once; both indexes get those files, checked by sha256. Never"
    " \"Re-run all jobs\" on a publish run; recovery ladder: `juniper-recurrence/README.md` § Publishing.\n"
)
AGENTS_TREE_OLD = "# per-package CI + publish (path-scoped) + repo-wide gates and nets\n"
AGENTS_TREE_NEW = "# per-package CI (path-scoped) + publish (tag-guarded) + repo-wide gates and nets\n"
CLIENT_VERSION_PY = "juniper-recurrence-client/juniper_recurrence_client/_version.py"
CLIENT_AGENTS_OLD = "mirroring the model and app publish workflows. Bump `_version.py` + cut the `[Unreleased]`\nCHANGELOG section in the release PR.\n"
CLIENT_AGENTS_NEW = (
    "mirroring the model and app publish workflows. Bump `_version.py` + cut the `[Unreleased]`\n"
    "CHANGELOG section in the release PR.\n"
    "\n"
    "Each run builds once, and TestPyPI and PyPI get those same files, checked by sha256 against each index's JSON\n"
    "(juniper-cascor's one-artifact template). A release that did not reach PyPI, in this order: dispatch\n"
    "`gh workflow run publish-recurrence-client.yml --repo pcalnon/juniper-recurrence --ref juniper-recurrence-client-v<version> -f republish_from_testpypi=true`,\n"
    "which copies TestPyPI's files to PyPI and builds nothing; if that fails, within 30 days of the release run,\n"
    "**Re-run failed jobs** on it; otherwise cut a new patch version. Never \"Re-run all jobs\" on a publish run. The\n"
    "full ladder, and what to do for a tag cut before this change or after a plain dispatch reached TestPyPI:\n"
    "`juniper-recurrence/README.md` § Publishing.\n"
)


def header_version(text: str, version: str, where: str, c) -> str:
    """Set the single ``**Version**:`` header line to the package's own ``__version__`` (review of #236: it said 0.3.0
    while ``_version.py`` and PyPI were 0.3.1)."""
    lines = [line for line in text.splitlines(keepends=True) if line.startswith("**Version**: ")]
    if len(lines) != 1:
        raise c.Refused(f"{where}: {len(lines)} '**Version**:' lines")
    return text.replace(lines[0], f"**Version**: {version}\n", 1)


def package_version(path: Path, c) -> str:
    found = re.findall(r'^__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if len(found) != 1:
        raise c.Refused(f"{path}: {len(found)} __version__ assignments")
    return found[0]


def last_updated(text: str, date: str, where: str, c) -> str:
    lines = [line for line in text.splitlines(keepends=True) if line.startswith("**Last Updated**: ")]
    if len(lines) != 1:
        raise c.Refused(f"{where}: {len(lines)} '**Last Updated**:' lines")
    return text.replace(lines[0], f"**Last Updated**: {date}\n", 1)


def apply(tree: Path, template_yml: str, test_file: str, date: str, c) -> dict[str, str]:
    """Every file to write, by repo-relative path, computed in memory; raises c.Refused before anything is written."""
    blocks = c.template_blocks(template_yml)
    republish = c.republish_job(template_yml)
    out: dict[str, str] = {}
    for rel, package in WORKFLOWS.items():
        out[rel] = port_workflow(c, (tree / rel).read_text(encoding="utf-8"), package, blocks, republish, rel)
    ci = (tree / CI_APP).read_text(encoding="utf-8")
    ci = c.replace_once(ci, CI_PUSH_OLD, CI_PUSH_NEW, CI_APP)
    out[CI_APP] = c.replace_once(ci, CI_FILTER_OLD, CI_FILTER_NEW, CI_APP)
    if (tree / TEST_PATH).exists():
        raise c.Refused(f"{TEST_PATH} exists already")
    out[TEST_PATH] = test_file
    out[CHANGELOG] = c.replace_once((tree / CHANGELOG).read_text(encoding="utf-8"), CHANGELOG_ANCHOR, CHANGELOG_ENTRY, CHANGELOG)
    out[README] = c.replace_once((tree / README).read_text(encoding="utf-8"), README_ANCHOR, README_NEW, README)
    agents = c.replace_once((tree / AGENTS).read_text(encoding="utf-8"), AGENTS_OLD, AGENTS_NEW, AGENTS)
    agents = c.replace_once(agents, AGENTS_TREE_OLD, AGENTS_TREE_NEW, AGENTS)
    out[AGENTS] = last_updated(agents, date, AGENTS, c)
    if len(out[AGENTS]) > AGENTS_CEILING:
        raise c.Refused(f"{AGENTS} would hold {len(out[AGENTS])} characters, over its {AGENTS_CEILING} budget")
    client = c.replace_once((tree / CLIENT_AGENTS).read_text(encoding="utf-8"), CLIENT_AGENTS_OLD, CLIENT_AGENTS_NEW, CLIENT_AGENTS)
    client = header_version(client, package_version(tree / CLIENT_VERSION_PY, c), CLIENT_AGENTS, c)
    out[CLIENT_AGENTS] = last_updated(client, date, CLIENT_AGENTS, c)
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh clone of juniper-recurrence's main")
    parser.add_argument("--template", required=True, type=Path, help="juniper-cascor's .github/workflows/publish.yml (the template's source)")
    parser.add_argument("--test-file", required=True, type=Path, help="the ported test_publish_one_artifact.py")
    parser.add_argument("--cascor-edits", type=Path, default=CASCOR_EDITS, help="util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py")
    parser.add_argument("--last-updated", default="2026-11-15", help="the **Last Updated** date for the two AGENTS.md files")
    parser.add_argument("--check", action="store_true", help="compute every edit and report; write nothing")
    args = parser.parse_args(argv)
    c = load_cascor_edits(args.cascor_edits)
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.test_file.read_text(encoding="utf-8"), args.last_updated, c)
    except c.Refused as exc:
        print(f"REFUSED (nothing written): {exc}")
        return 1
    for rel, text in sorted(out.items()):
        before = (args.tree / rel).read_text(encoding="utf-8") if (args.tree / rel).exists() else ""
        print(f"{'would write' if args.check else 'wrote'} {rel}: {len(before)} -> {len(text)} chars, sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}")
    if not args.check:
        for rel, text in out.items():
            (args.tree / rel).parent.mkdir(parents=True, exist_ok=True)
            (args.tree / rel).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
