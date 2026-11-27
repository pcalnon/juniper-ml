#!/usr/bin/env python3
"""Port juniper-cascor's swept one-artifact publish template (juniper-cascor#777) to a fresh juniper-data-client tree, every edit asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the one-artifact template sweep, ported to juniper-data-client; the orchestrating session's brief tmp/ports/SWEEP_PORT_BRIEF.md)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py (the template's sweep, juniper-cascor#777, the model for this writer);
         util/ad-hoc/2026-11-15_juniper-data-client_one_artifact_publish_port.py (the port this one follows, juniper-data-client#264);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker the result passes);
         util/ad-hoc/2026-11-24_publish_port_install_pins.json (the pinned install scripts: this port proposes its own pin);
         util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
juniper-cascor#777 swept the one-artifact publish template that juniper-data-client#264 copied: rulings 1 and 2 of
2026-11-16, a third template parameter and the corrections the reviews of the ports collected. This gives
juniper-data-client's ``publish.yml`` the swept template, with its tests, docs and changelog:

- Ruling 2 (SWEEP items 6, 10): the install check leaves ``Publish to TestPyPI`` for a job of its own,
  ``Verify the TestPyPI install`` (``contents: read`` alone, no environment), which ``Publish to PyPI`` needs. Its steps
  move with it: ``setup-python``, a sparse checkout of ``pyproject.toml`` that keeps no credential (the version is read
  from it, by its path under ``$GITHUB_WORKSPACE``), and the install check, now run from ``$RUNNER_TEMP``, with the
  template's 5 tries, 10 s apart, and its lag error. R4-5: its post-install check also requires
  ``importlib.util.find_spec("juniper_data_client")`` to find the package with an origin, failing through
  ``SystemExit``. The TestPyPI job drops its checkout and ``setup-python`` and holds ``id-token: write`` alone.
- Ruling 1, ``PUBLISH_TAG_PREFIX`` and the comment corrections: every template block and the republish job are cut out
  of juniper-cascor's ``publish.yml`` (``--template``) and put in place of this file's copies, never retyped, then cut
  out of the result again to prove them byte-identical; the workflow ``env`` takes the template's comment and
  ``PUBLISH_TAG_PREFIX: v``; the build guard's comment the template's note on ``rc*`` / ``hf*`` tags.
- ``tests/test_publish_docs_bounds.py``: new, ``DOCS_TEST`` (the install check's bounds and lag error, which
  ``docs/REFERENCE.md`` now states, read from the workflow and required in the doc), refused if the base has one.
- ``tests/test_publish_one_artifact.py``: replaced whole by ``NEW_TEST`` (the port of #777's test changes, item E's
  hardening, B's and C's rehearsals, and item G: the template blocks' digests are pinned NORMALIZED, each ``uses:``
  line reduced to its action's name), refused unless the base file is the one it was derived from.
- ``docs/REFERENCE.md`` § Publishing and Recovery and its workflow row; its ``**Version:**`` patch moves by one and its
  ``**Last Updated:**`` takes ``--date``, header and footer, as its recent edits did. ``CHANGELOG.md``: one entry at the
  end of ``[Unreleased]`` / ``### Fixed``. ``AGENTS.md`` and ``README.md`` do not describe the publish pipeline.

Wording: the new text names no person. The person-word the base already uses is read at run time (``publish.yml``'s
republish banner, ``docs/REFERENCE.md``'s ladder line), so the anchors that hold it match on either base, and no file
may name it more often than before (the template's own text, which carries the rename, is what it is).

Revision 2 (2026-11-26), for the independent review of juniper-data-client#274 and its one fix-up commit:
- F1: ``docs/REFERENCE.md`` tells a failed ``Verify PyPI serves exactly these files``'s two causes apart, as
  juniper-cascor's ``docs/ci_cd/MANUAL.md`` does. A mismatch needs a new patch version. A check that gave up waiting is
  index lag: Re-run failed jobs uploads the same bytes again.
- F2: the docs, the CHANGELOG entry and a test comment say the install job INSTALLS the package. Its check reads
  metadata and ``find_spec`` alone, so it runs none of the package's code, and the old TestPyPI job never ran it either.
  The workflow's banner comments stay as the template has them.
- F3: the post-install check prints juniper-cascor's neutral line (``publish-protocol.yml``), ``'TestPyPI install'``,
  with no "OK" before the check passes; ``NEW_TEST``'s pins and expected output move with it.
- The writer's own string constants concatenate explicitly (a leading ``+``): revision 1 relied on implicit
  concatenation in 39 places, against the sweep's rule. Every module constant compares equal across the change, and the
  output is byte-identical.
Run on a fresh clone of main, revision 2 writes the whole tree the fix-up pushes.

``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree ``main`` has since moved past would silently
revert what merged in between. Re-apply on a fresh clone instead:

    python3 -I util/ad-hoc/2026-11-26_juniper-data-client_one_artifact_sweep_port.py --tree <fresh clone> \\
        [--template <juniper-cascor .github/workflows/publish.yml>] [--date YYYY-MM-DD]

``--template`` defaults to ``<tree>/../juniper-cascor/.github/workflows/publish.yml`` (a sibling clone), and must hash
to juniper-cascor's at #777's merge ``f5ed3017`` (main ``5e3d9801`` holds it unchanged). ``--date`` (default: today,
UTC) is the day ``publish.yml``'s ``Last Modified`` and ``docs/REFERENCE.md``'s ``Last Updated`` take.

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once, an input moved, or a post-condition
failed (nothing is written then); 2 on a usage error.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import re
import sys
from pathlib import Path

REPO = "juniper-data-client"
PACKAGE = "juniper-data-client"
IMPORT_NAME = "juniper_data_client"
WORKFLOW_PATH = ".github/workflows/publish.yml"
TEST_PATH = "tests/test_publish_one_artifact.py"
DOCS_TEST_PATH = "tests/test_publish_docs_bounds.py"
REFERENCE_PATH = "docs/REFERENCE.md"
CHANGELOG_PATH = "CHANGELOG.md"
#: juniper-cascor's .github/workflows/publish.yml at f5ed3017 (#777's merge), unchanged at main 5e3d9801: the template.
TEMPLATE_SHA256 = "b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b"
TEMPLATE_PACKAGE = "juniper-cascor"
#: tests/test_publish_one_artifact.py at juniper-data-client main 5c329a39 (2026-11-25), the base NEW_TEST replaces.
BASE_TEST_SHA256 = "9f8b0107fda613c1fbf8e87845a289ac30a0f4049bc6e360bd30ad6037928e80"
WORDS = ("Overtoad", "owner")
INSTALL_JOB = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
INSTALL_STEP = "Verify TestPyPI install"

#: The template's step blocks, keyed <job>/<step name> (the 11-15 tooling's cutting rule).
TEMPLATE_COMMENT = "      # One-artifact publish template"
STEP_LINE = re.compile(r"^      (?:- |# )")
JOB_LINE = re.compile(r"^  [a-z][a-z0-9-]*:\s*$")
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


def replace_each(text: str, old: str, new: str, count: int, where: str) -> str:
    """``replace_once`` for an anchor the file holds exactly ``count`` times (a header line its footer repeats)."""
    found = text.count(old)
    if found != count:
        raise Refused(f"{where}: anchor matched {found} times, expected {count}: {old[:90]!r}")
    return text.replace(old, new)


def once_in(text: str, piece: str, where: str) -> str:
    """PIECE, asserted to occur in TEXT exactly once (a text this writer takes from the template, never retypes)."""
    if text.count(piece) != 1:
        raise Refused(f"{where}: expected exactly one {piece[:90]!r}, found {text.count(piece)}")
    return piece


def detect_word(text: str, line: str, where: str) -> str:
    """The person-word the base uses in LINE (a format string with ``{word}``): exactly one of WORDS must fit."""
    found = [word for word in WORDS if line.format(word=word) in text]
    if len(found) != 1:
        raise Refused(f"{where}: {line!r} holds {found or 'neither'} of {WORDS}")
    return found[0]


def action_pin(text: str, action: str, where: str) -> str:
    """The one ``<action>@<sha>  # vX.Y.Z`` pin a workflow uses (Dependabot bumps every copy in a file together)."""
    pins = set(re.findall(rf"{re.escape(action)}@[0-9a-f]{{40}}  # v[0-9][0-9.]*", text))
    if len(pins) != 1:
        raise Refused(f"{where}: {len(pins)} distinct {action} pins, expected 1: {sorted(pins)}")
    return pins.pop()


def block_spans(text: str, where: str) -> dict[str, tuple[int, int]]:
    """Each template block's (first line, end line) in TEXT, keyed <job>/<step name>: from its "One-artifact publish
    template" comment to the end of its step, comments included. Run-script lines are indented deeper than any
    step-level line, so they never end a block early."""
    lines = text.splitlines(keepends=True)
    spans: dict[str, tuple[int, int]] = {}
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
            # A block ends at its step's last non-blank line: the blank lines between steps are not the template's.
            while end > first + 1 and not lines[end - 1].strip():
                end -= 1
            key = f"{job}/{name}"
            if key in spans:
                raise Refused(f"{where}: two template blocks for {key}")
            spans[key] = (i, end)
            i = end
            continue
        i += 1
    if set(spans) != WANT_BLOCKS:
        raise Refused(f"{where}: template blocks found {sorted(spans)}, expected {sorted(WANT_BLOCKS)}")
    return spans


def template_blocks(text: str, where: str) -> dict[str, str]:
    lines = text.splitlines(keepends=True)
    return {key: "".join(lines[a:b]) for key, (a, b) in block_spans(text, where).items()}


def republish_start(text: str, where: str) -> int:
    """The offset of the republish job's comment banner; the job runs from there to the end of the file."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == "  republish:\n"]
    if len(at) != 1:
        raise Refused(f"{where}: {len(at)} republish jobs")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    return sum(len(line) for line in lines[:start])


def republish_job(text: str, where: str) -> str:
    return text[republish_start(text, where) :].rstrip("\n") + "\n"


# ─────────────────────────────────────────────────────────────────────────────────────────────
# .github/workflows/publish.yml
# ─────────────────────────────────────────────────────────────────────────────────────────────
#: The header's description, as juniper-cascor#763 wrote it here, and as #777 rewrote it (taken from the template).
DESCRIPTION_OLD = (
    "#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both jobs the\n"
    + "#    same artifact: TestPyPI takes it first and must then serve exactly those sha256, and PyPI takes\n"
    + "#    it only after TestPyPI is checked again. Uses OIDC trusted publishing (no API tokens).\n"
)
DESCRIPTION_NEW = (
    "#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both publish jobs\n"
    + "#    the same artifact: TestPyPI takes it first and must then serve exactly those sha256, a job that\n"
    + "#    cannot mint a credential installs it from TestPyPI, and PyPI takes it only after that install\n"
    + "#    passed and TestPyPI is checked again. Uses OIDC trusted publishing (no API tokens).\n"
)
#: The header's account of the copies: the digest pins it names are normalized now (item G), and it names no person.
COPIES_OLD = (
    "#    The steps marked \"One-artifact publish template\", and the republish job, are verbatim copies of\n"
    + "#    juniper-cascor's publish.yml (juniper-cascor#763, #767). tests/test_publish_one_artifact.py pins\n"
    + "#    them to juniper-cascor's sha256: change them there first, then copy them here. The republish job\n"
    + "#    is step 1 of the {word}'s recovery ladder for a release that never reached PyPI.\n"
)
COPIES_NEW = (
    "#    The steps marked \"One-artifact publish template\", and the republish job, are verbatim copies of\n"
    + "#    juniper-cascor's publish.yml (juniper-cascor#763, #767, #777): they read nothing from this repository\n"
    + "#    but the three `env` values below. tests/test_publish_one_artifact.py pins them to juniper-cascor's\n"
    + "#    text, each `uses:` line reduced to its action's name, so a Dependabot bump of an action needs no\n"
    + "#    re-port: change them there first, then copy them here. The republish job is step 1 of the recovery\n"
    + "#    ladder (ruling of 2026-11-15) for a release that never reached PyPI.\n"
)
LAST_MODIFIED = re.compile(r"^# Last Modified: \d{4}-\d{2}-\d{2}\n", re.MULTILINE)
PERMISSIONS_OLD = "# Each job states what it needs. Only the jobs that upload hold id-token: write, so the build cannot mint a credential.\n"
PERMISSIONS_NEW = "# Each job states what it needs. Only the jobs that upload hold id-token: write, so neither the build nor the install\n# check can mint a credential.\n"
ENV_OLD = (
    "env:\n"
    + "  # The one-artifact publish template's two parameters: the distribution's name on PyPI and TestPyPI,\n"
    + "  # and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
    + f"  PUBLISH_PACKAGE: {PACKAGE}\n"
    + "  PUBLISH_DIST_DIR: dist\n"
)
#: SWEEP item 12, in the template's words: the guard skips the rc* and hf* tags the publish environments admit
#: (juniper-data-client's testpypi and pypi environments admit v*, rc*, hf* and juniper-*-v*/-rc*/-hf* tags).
GUARD_OLD = (
    "    # Both publish jobs depend on this job, so this guard gates the whole release pipeline.\n"
    + "    if: startsWith(github.event.release.tag_name, 'v')\n"
)
GUARD_NEW = (
    "    # Both publish jobs depend on this job, so this guard gates the whole release pipeline. The publish environments\n"
    + "    # also admit `rc*` and `hf*` tags, kept for future release-candidate and hotfix conventions (D2 of juniper-ml's\n"
    + "    # notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md). This guard skips them: a\n"
    + "    # convention that adopts one must widen it, and PUBLISH_TAG_PREFIX with it.\n"
    + "    if: startsWith(github.event.release.tag_name, 'v')\n"
)
TESTPYPI_HEAD = "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n    permissions:\n"
PYPI_HEAD_OLD = "\n  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n"
PYPI_HEAD_NEW = f"\n  pypi:\n    name: Publish to PyPI\n    needs: [testpypi, {INSTALL_JOB}]\n"
INSTALL_JOB_PERMISSIONS = "    permissions:\n      contents: read  # the sparse checkout below, and nothing else: this job runs the package TestPyPI serves\n"
SPARSE_COMMENT = "      # A sparse checkout, for the file the version is read from: nothing runs from it, and it keeps no credential.\n"
#: The install step, as #264 left it in the TestPyPI job, and as it runs in its own job: from $RUNNER_TEMP, the version
#: read by its path under the workspace, the template's retry loop and lag error, and R4-5's find_spec check.
INSTALL_RUN_OLD = (
    "        run: |\n"
    + "          VERSION=$(python -c \"import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])\")\n"
    + "          sleep 30\n"
)
INSTALL_RUN_NEW = (
    "        run: |\n"
    + "          # `python -c` puts its working directory first on sys.path, and this repository's root holds\n"
    + "          # juniper_data_client/, so an import run inside a checkout of it can pass without the wheel. This job's\n"
    + "          # checkout is sparse, for the pyproject.toml the version is read from, and the step still installs and\n"
    + "          # imports from the runner's temporary directory, outside the checkout.\n"
    + "          cd \"${RUNNER_TEMP}\"\n"
    + "          VERSION=$(python -c \"import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])\")\n"
    + "          sleep 30\n"
)
INSTALL_LINE_OLD = (
    "          # fallback only risks resolving a squatted target package. The sleep above covers\n"
    + "          # TestPyPI index lag.\n"
    + f"          pip install --no-deps --index-url https://test.pypi.org/simple/ \"{PACKAGE}==${{VERSION}}\"\n"
)
LAG_COMMENT = "          # TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.\n"
INSTALL_LINE_NEW = (
    "          # fallback only risks resolving a squatted target package.\n"
    + LAG_COMMENT
    + "          for attempt in 1 2 3 4 5; do\n"
    + "            if pip install \\\n"
    + "              --no-deps \\\n"
    + "              --index-url https://test.pypi.org/simple/ \\\n"
    + f"              \"{PACKAGE}==${{VERSION}}\"; then\n"
    + "              break\n"
    + "            fi\n"
    + "            if [ \"${attempt}\" -eq 5 ]; then\n"
    + f"              echo \"::error::{PACKAGE} ${{VERSION}} is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats\"\n"
    + "              exit 1\n"
    + "            fi\n"
    + "            echo \"TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)\"\n"
    + "            sleep 10\n"
    + "          done\n"
)
CHECK_OLD = (
    "          # Version-only check: juniper_data_client imports numpy/requests at import time, which\n"
    + "          # are absent under --no-deps; verify the published artifact via its installed metadata.\n"
    + f"          python -c \"import importlib.metadata as m; print('TestPyPI OK: v' + m.version('{PACKAGE}'))\"\n"
)
CHECK_NEW = (
    "          # No import: juniper_data_client imports numpy/requests at import time, which are absent under\n"
    + "          # --no-deps. Verify the published artifact via its installed metadata, and that the wheel holds the\n"
    + "          # package: find_spec locates it without running it. SystemExit fails the step: PYTHONOPTIMIZE would\n"
    + "          # strip an assert statement.\n"
    + f"          python -c \"import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{IMPORT_NAME}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{PACKAGE}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {IMPORT_NAME} package')\"\n"
)


def publish_workflow(text: str, template: str, today: str) -> str:
    """Give publish.yml the swept template: the install check's own job, the template's blocks and republish job, the
    third parameter and the comments; keep the repository's own build commands, guard and install check."""
    where = WORKFLOW_PATH
    word = detect_word(text, "  # The {word}'s recovery ladder, step 1 (2026-11-15)", where)
    checkout = action_pin(text, "actions/checkout", where)
    setup_python = action_pin(text, "actions/setup-python", where)
    if action_pin(template, "actions/checkout", "the template") != checkout or action_pin(template, "actions/setup-python", "the template") != setup_python:
        raise Refused(f"{where}: its checkout or setup-python pin differs from the template's: re-derive the port")
    # The header: the day it was edited, the template's description, and the copies' account.
    if len(LAST_MODIFIED.findall(text)) != 1:
        raise Refused(f"{where}: expected one '# Last Modified:' header line")
    text = LAST_MODIFIED.sub(f"# Last Modified: {today}\n", text)
    once_in(template, DESCRIPTION_NEW, "the template's description")
    text = replace_once(text, DESCRIPTION_OLD, DESCRIPTION_NEW, where)
    text = replace_once(text, COPIES_OLD.format(word=word), COPIES_NEW, where)
    text = replace_once(text, PERMISSIONS_OLD, once_in(template, PERMISSIONS_NEW, "the template's permissions comment"), where)
    # The workflow env: the template's three parameters, with this package's name.
    template_env = template[template.index("\nenv:\n") + 1 : template.index("\njobs:\n")]
    new_env = replace_once(template_env, f"  PUBLISH_PACKAGE: {TEMPLATE_PACKAGE}\n", f"  PUBLISH_PACKAGE: {PACKAGE}\n", "the template's env")
    text = replace_once(text, ENV_OLD, new_env, where)
    text = replace_once(text, GUARD_OLD, GUARD_NEW, where)
    # The TestPyPI job: the template's head (id-token: write alone), with no checkout and no setup-python.
    template_head = template[template.index(TESTPYPI_HEAD) : template.index("    steps:\n", template.index(TESTPYPI_HEAD)) + len("    steps:\n")]
    setup = f"      - uses: {setup_python}\n        with:\n          python-version: \"3.12\"\n"
    old_head = TESTPYPI_HEAD + "      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n" + f"    steps:\n      - uses: {checkout}\n\n" + setup + "\n"
    text = replace_once(text, old_head, template_head, where)
    # The install check's own job, after the TestPyPI job: the template's comment and head, this job's setup-python,
    # the sparse checkout its version is read from, and its install step.
    start = "      - name: Verify TestPyPI install\n"
    for anchor in (start, PYPI_HEAD_OLD):
        if text.count(anchor) != 1:
            raise Refused(f"{where}: anchor matched {text.count(anchor)} times, expected 1: {anchor[:90]!r}")
    a, b = text.index(start), text.index(PYPI_HEAD_OLD)
    if a >= b:
        raise Refused(f"{where}: the install step does not come before the PyPI job")
    install = text[a:b]
    install = replace_once(install, INSTALL_RUN_OLD, INSTALL_RUN_NEW, where + " install check")
    install = replace_once(install, INSTALL_LINE_OLD, INSTALL_LINE_NEW, where + " install check")
    install = replace_once(install, CHECK_OLD, CHECK_NEW, where + " install check")
    job_comment_start = template.index("  # Ruling 2 of 2026-11-16: the install check runs in a job of its own")
    job_comment = template[job_comment_start : template.index(f"  {INSTALL_JOB}:\n", job_comment_start)]
    job_head = once_in(template, f"  {INSTALL_JOB}:\n    name: {INSTALL_NAME}\n    needs: testpypi\n    runs-on: ubuntu-latest\n", "the template's install job")
    sparse = f"      - uses: {checkout}\n        with:\n          sparse-checkout: |\n            pyproject.toml\n          persist-credentials: false\n"
    job = job_comment + job_head + INSTALL_JOB_PERMISSIONS + "    steps:\n" + setup + "\n" + SPARSE_COMMENT + sparse + "\n" + install
    # The TestPyPI job now ends at its JSON check; the install job follows it.
    before = text[:a].rstrip("\n") + "\n\n"
    text = before + job + text[b:]
    text = replace_once(text, PYPI_HEAD_OLD, PYPI_HEAD_NEW, where)
    # The template's blocks and its republish job, in place of this file's copies.
    want_blocks = template_blocks(template, "the template")
    want_republish = republish_job(template, "the template")
    text = text[: republish_start(text, where)] + want_republish
    lines = text.splitlines(keepends=True)
    for key, (first, end) in sorted(block_spans(text, where).items(), key=lambda item: item[1][0], reverse=True):
        if not key.startswith("republish/"):
            lines[first:end] = [want_blocks[key]]
    text = "".join(lines)
    if template_blocks(text, where) != want_blocks:
        raise Refused(f"{where}: a template block of the result differs from the template's")
    if republish_job(text, where) != want_republish:
        raise Refused(f"{where}: the result's republish job differs from the template's")
    return text


def check_workflow(text: str) -> None:
    """Post-conditions: the file parses, with the new wiring, and the install job runs the check this port wrote."""
    try:
        import yaml  # noqa: PLC0415 -- the checker and the repository's tests read it too
    except ImportError as exc:
        raise Refused("PyYAML is not importable: run this with an interpreter that has it, since the post-condition parses the workflow") from exc
    data = yaml.safe_load(text)
    jobs = data["jobs"]
    if data["env"] != {"PUBLISH_PACKAGE": PACKAGE, "PUBLISH_DIST_DIR": "dist", "PUBLISH_TAG_PREFIX": "v"}:
        raise Refused(f"{WORKFLOW_PATH}: env is {data['env']}")
    if sorted(jobs) != sorted(["build", "testpypi", INSTALL_JOB, "pypi", "republish"]):
        raise Refused(f"{WORKFLOW_PATH}: jobs are {sorted(jobs)}")
    install = jobs[INSTALL_JOB]
    if install.get("name") != INSTALL_NAME or install.get("needs") != "testpypi" or install.get("permissions") != {"contents": "read"} or "environment" in install:
        raise Refused(f"{WORKFLOW_PATH}: the install job is {install}")
    if jobs["pypi"].get("needs") != ["testpypi", INSTALL_JOB] or jobs["testpypi"].get("permissions") != {"id-token": "write"} or jobs["pypi"].get("permissions") != {"id-token": "write"}:
        raise Refused(f"{WORKFLOW_PATH}: the PyPI job needs {jobs['pypi'].get('needs')} and holds {jobs['pypi'].get('permissions')}, the TestPyPI job holds {jobs['testpypi'].get('permissions')}")
    if [step.get("name") for step in jobs["testpypi"]["steps"]][-1] != "Verify TestPyPI serves exactly these files":
        raise Refused(f"{WORKFLOW_PATH}: the TestPyPI job does not end at its JSON check")
    if any("pip install" in str(step.get("run") or "") or str(step.get("uses") or "").startswith(("actions/checkout@", "actions/setup-python@")) for step in jobs["testpypi"]["steps"]):
        raise Refused(f"{WORKFLOW_PATH}: the TestPyPI job still checks out, sets up Python or installs")
    steps = install["steps"]
    if [str(step.get("uses") or step.get("name")).split("@", 1)[0] for step in steps] != ["actions/setup-python", "actions/checkout", INSTALL_STEP]:
        raise Refused(f"{WORKFLOW_PATH}: the install job's steps are {steps}")
    if steps[1].get("with") != {"sparse-checkout": "pyproject.toml\n", "persist-credentials": False}:
        raise Refused(f"{WORKFLOW_PATH}: the install job's checkout is not a sparse checkout of pyproject.toml alone, without a kept credential")
    run = str(steps[2].get("run") or "")
    commands = [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]
    if commands[0] != 'cd "${RUNNER_TEMP}"' or run.count("pip install") != 1 or run.count("is not installable from TestPyPI after 5 tries (index lag?)") != 1 or "${{" in run or f"u.find_spec('{IMPORT_NAME}')" not in commands[-1]:
        raise Refused(f"{WORKFLOW_PATH}: the install step does not leave for $RUNNER_TEMP first, lacks its one retried install, its lag error or its find_spec check, or reads an expression")
    if set(steps[2]) != {"name", "run"}:
        raise Refused(f"{WORKFLOW_PATH}: the install step carries {sorted(steps[2])}")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# docs/REFERENCE.md and CHANGELOG.md
# ─────────────────────────────────────────────────────────────────────────────────────────────
REFERENCE_ROW_OLD = "| `publish.yml` | GitHub Release (`v*` tags); `workflow_dispatch` from a release tag, republish only | Builds once; TestPyPI, then PyPI, upload that one artifact, each checked by sha256 against TestPyPI's JSON; install verification from TestPyPI; trusted publishing (OIDC); build attestations. See [Publishing and Recovery](#publishing-and-recovery) |\n"
REFERENCE_ROW_NEW = "| `publish.yml` | GitHub Release (`v*` tags); `workflow_dispatch` from a release tag, republish only | Builds once; TestPyPI, then PyPI, upload that one artifact, each checked by sha256 against TestPyPI's JSON; install verification from TestPyPI, in a job of its own that cannot mint a credential; trusted publishing (OIDC); build attestations. The dispatch republishes TestPyPI's files once the release run passed its TestPyPI jobs. See [Publishing and Recovery](#publishing-and-recovery) |\n"
REFERENCE_SECTION_START = "### Publishing and Recovery\n"
REFERENCE_SECTION_END = "\n### Pre-Commit Hooks\n"
#: The section as juniper-data-client#264 wrote it (the person-word filled in from the base), and as this port rewrites it.
REFERENCE_SECTION_OLD = """\
### Publishing and Recovery

`publish.yml` builds once and hands both publish jobs one artifact:

1. `Build and Validate` builds the sdist and wheel (`python -m build`, `twine check`), records their sha256 in `SHA256SUMS` and uploads both as one artifact, `juniper-data-client-dist`, kept 90 days; a re-run attempt reuses that artifact instead of building again. It runs for a published `v*` Release only
2. `Publish to TestPyPI` checks the files against `SHA256SUMS`, uploads them (`attestations`, `verbose`; never `skip-existing`), requires TestPyPI's JSON to list exactly those sha256, then verifies the install (`--no-deps`, TestPyPI index only, the version read from `pyproject.toml`)
3. `Publish to PyPI`, behind the `pypi` approval, checks the same files against `SHA256SUMS` and TestPyPI's JSON again, uploads them (`attestations`; trusted publishing / OIDC), then checks PyPI's JSON. Only the jobs that upload hold `id-token: write`

The steps marked `One-artifact publish template`, and the `republish` job, are verbatim copies of juniper-cascor's `publish.yml` (juniper-cascor#763, #767); `tests/test_publish_one_artifact.py` pins them to its sha256, so change them there first. The contract: juniper-cascor's [`docs/ci_cd/MANUAL.md` § One Artifact, Checked Against TestPyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi).

**A release that did not reach PyPI**: the {word}'s recovery ladder (ruling of 2026-11-15), in this order ([§ Recovering a Release That Did Not Reach PyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#recovering-a-release-that-did-not-reach-pypi)):

1. **Republish TestPyPI's files**: `gh workflow run publish.yml --repo pcalnon/juniper-data-client --ref v<version> -f republish_from_testpypi=true`. Only `Republish the tested files (dispatch only)` runs, behind the `pypi` gate; it builds nothing, and only a tag cut after this job landed carries it.
   It copies TestPyPI's files whatever the release run's jobs concluded, so use it only when that run's `Publish to TestPyPI` succeeded, or failed on index lag alone (a JSON check or the install check that gave up waiting).
2. **If that fails, within 30 days of the release run**: **Re-run failed jobs** on the release run, which reuses the run's artifact.
3. **Otherwise**: cut a new patch version.

A broken package is neither case: when `Publish to TestPyPI` failed after its upload for a real reason (the install check refused the package, say for its `Requires-Python`), TestPyPI already holds those files, and neither rung 1 nor "Re-run failed jobs" can change them, so cut a new patch version.
Never "Re-run all jobs" on a publish run, nor `gh run rerun <id>` without `--failed`.
"""
REFERENCE_SECTION_NEW = """\
### Publishing and Recovery

`publish.yml` builds once and hands both publish jobs one artifact:

1. `Build and Validate` builds the sdist and wheel (`python -m build`, `twine check`), records their sha256 in `SHA256SUMS` and uploads both as one artifact, `juniper-data-client-dist`, kept 90 days; a re-run attempt reuses that artifact instead of building again. It runs for a published `v*` Release only
2. `Publish to TestPyPI` checks the files against `SHA256SUMS`, uploads them (`attestations`, `verbose`; never `skip-existing`) and requires TestPyPI's JSON to list exactly those sha256. It holds `id-token: write` alone: it checks nothing out and runs no install check
3. `Verify the TestPyPI install`, a job of its own after it (ruling 2 of 2026-11-16), verifies the install (`--no-deps`, TestPyPI index only, the version read from a sparse checkout of `pyproject.toml`) from `$RUNNER_TEMP`, outside any checkout, and requires the wheel to hold the `juniper_data_client` package (`importlib.util.find_spec`, which does not run it). It installs the package TestPyPI serves, so it holds `contents: read` alone, with no environment and no `id-token`. It makes 5 tries, 10 s apart, after a 30 s wait, and then fails with an error that names index lag
4. `Publish to PyPI`, behind the `pypi` approval, needs both TestPyPI jobs. It checks the same files against `SHA256SUMS` and TestPyPI's JSON again, uploads them (`attestations`; trusted publishing / OIDC), then checks PyPI's JSON. Only the jobs that upload hold `id-token: write`

The steps marked `One-artifact publish template`, and the `republish` job, are verbatim copies of juniper-cascor's `publish.yml` (juniper-cascor#763, #767, #777). They read only the workflow `env` values `PUBLISH_PACKAGE`, `PUBLISH_DIST_DIR` and `PUBLISH_TAG_PREFIX`, the prefix of this package's release tags, `v`; the build job's guard repeats it, since a job-level `if:` cannot read `env`. `tests/test_publish_one_artifact.py` pins them to juniper-cascor's text, each `uses:` line compared by its action's name, so a Dependabot bump of an action needs no re-port; change them there first. The contract: juniper-cascor's [`docs/ci_cd/MANUAL.md` § One Artifact, Checked Against TestPyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#one-artifact-checked-against-testpypi).

**A release that did not reach PyPI**: the {word}'s recovery ladder (ruling of 2026-11-15), in this order ([§ Recovering a Release That Did Not Reach PyPI](https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md#recovering-a-release-that-did-not-reach-pypi)):

1. **Republish TestPyPI's files**: `gh workflow run publish.yml --repo pcalnon/juniper-data-client --ref v<version> -f republish_from_testpypi=true`. Only `Republish the tested files (dispatch only)` runs, behind the `pypi` gate; it builds nothing. It refuses unless the tag's newest release run exists and both its TestPyPI jobs, `Publish to TestPyPI` and `Verify the TestPyPI install`, concluded success in their latest attempt (ruling 1 of 2026-11-16). It takes the version from the tag after `v`, so a tag that is not `v` and the exact version (`v0.3.1-beta`, which shipped 0.3.1's files) cannot be republished, and the job fails without publishing.
2. **If that fails, within 30 days of the release run**: **Re-run failed jobs** on the release run, which reuses the run's artifact.
3. **Otherwise**: cut a new patch version.

When rung 1 refuses, or a release run failed before PyPI:

- **A TestPyPI job failed on index lag** (a JSON check gave up, or the install check stopped after its last try with `… is not installable from TestPyPI after 5 tries (index lag?)`): within 30 days, **Re-run failed jobs** on the release run. A re-run `Publish to TestPyPI` uploads the same bytes from the run's artifact, which the index accepts, and both checks run again.
- **The install check failed for real** (the package does not install, or the wheel lacks the package, and a re-run fails the same way): cut a new patch version. Neither a re-run nor a same-version re-cut can fix it: the index refuses new bytes under a file name it already holds.
- **A Release that was re-cut**: never delete a Release and publish it again to retry. The re-cut's run builds again, TestPyPI refuses its files, and that failed run is then the tag's newest, so rung 1 refuses the tag for good. Rung 2 still applies to the original release run, within 30 days of it; then rung 3.

A failed `Verify PyPI serves exactly these files` comes after the upload, so the run's files are already on PyPI, and what it needs depends on why it failed:

- **PyPI lists a file this run did not build, or one with another sha256**: another upload put it there. Compare PyPI's JSON for the version with TestPyPI's to find which upload did; only a new patch version ships tested files under a clean version.
- **The check gave up waiting** (PyPI's JSON did not list the files in time): index lag, not a wrong file. **Re-run failed jobs** on that run: the job uploads the same bytes again, which the index accepts, and the check runs again. Re-running the job needs a fresh `pypi` approval.

Each rung acts on the workflow file as of the tag: a tag cut before juniper-data-client#264 merged (2026-11-16), every release up to `v0.6.0` included, has no rung 1, and one cut before this change runs rung 1 without the check of the release run's TestPyPI jobs.
Never "Re-run all jobs" on a publish run, nor `gh run rerun <id>` without `--failed`.
"""
VERSION_LINE = re.compile(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)\n", re.MULTILINE)
DATE_PREFIX = "**Last Updated:** "

CHANGELOG_ENTRY = """\
- **The republish job copies nothing a release run did not pass, and the install check can mint no credential**
  (rulings 1 and 2 of 2026-11-16, on the one-artifact publish above). This ports juniper-cascor's sweep of the
  template (juniper-cascor#777) to `publish.yml`, template verbatim.
  - **The install check has a job of its own** (ruling 2). `Verify the TestPyPI install` needs `Publish to TestPyPI`,
    and `Publish to PyPI` needs both. It installs the package TestPyPI serves, so it holds `contents: read` alone: no
    environment and no `id-token`. Until now it ran in the TestPyPI job, so pip installed the package TestPyPI serves
    in a job that held `id-token: write` (the check read its metadata alone, so none of its code ran). Its steps
    moved with it: `setup-python` 3.12, a sparse checkout of `pyproject.toml` that keeps no credential
    (`persist-credentials: false`) in place of the full checkout, and the same `--no-deps` install from TestPyPI
    alone, now run from `$RUNNER_TEMP`, with the version read from `${GITHUB_WORKSPACE}/pyproject.toml`. The
    TestPyPI job drops its checkout and `setup-python` and holds `id-token: write` alone, so the job that can mint
    runs only the template steps and the upload. The new job's name holds "TestPyPI", so juniper-ml's release-train
    ceremony reads its failure as `HALT_TESTPYPI`.
  - **The install check makes 5 tries, 10 s apart, then names the lag.** After its 30 s wait it had one try. After
    the fifth failed install it fails with "… is not installable from TestPyPI after 5 tries (index lag?): Re-run
    failed jobs; a real failure repeats". Its post-install check also requires the wheel to hold the
    `juniper_data_client` package (`importlib.util.find_spec`, which finds it without running it), so a wheel that
    lacks the package no longer passes on its metadata alone; it fails through `SystemExit`, which
    `PYTHONOPTIMIZE` keeps. The line it prints before that check is juniper-cascor's neutral one,
    `TestPyPI install <version> package at <origin>`, in place of `TestPyPI OK: v<version>`, so a refusal's log
    says no "OK".
  - **The republish job refuses unless the tag's release run passed its TestPyPI jobs** (ruling 1).
    `Find the release run's artifact` takes the tag's newest release run, whether or not its artifact has expired,
    and refuses unless each of its jobs whose name holds "TestPyPI" concluded success in its latest attempt
    (`GET actions/runs/{id}/jobs?filter=all`, each job's record with the highest attempt). It refuses as well when
    the tag has no release run. Rung 1 of the recovery ladder could otherwise copy files whose install check had
    failed, or never ran.
  - **`PUBLISH_TAG_PREFIX: v`**, the template's third parameter. The republish job takes the version from the tag
    only after it, so `publish.yml` refuses a `juniper-data-client-v<version>` tag before any request. The build
    guard repeats it, since a job-level `if:` cannot read `env`, and its comment notes that a future `rc*` or `hf*`
    tag convention must widen it.
  - **Comments**, the template's: the republish job's no longer says the ceremony never reads a dispatch run (since
    juniper-ml#2592 its monitor reads them and classifies a republish run by the run's own status), and the PyPI
    job's says TestPyPI's record witnesses the files the run built, whose wheel the install check installed.
  - **Docs**: `docs/REFERENCE.md` § Publishing and Recovery (0.5.5) describes the install job and its bounds, and
    when rung 1 refuses: a TestPyPI job that failed on index lag is re-run ("Re-run failed jobs" uploads the same
    bytes, which the index accepts), a failed install check needs a new patch version, a re-cut Release leaves the
    tag with no run rung 1 accepts, a failed `Verify PyPI serves exactly these files` comes after the upload (a
    mismatch needs a new patch version; a check that gave up waiting is index lag, which "Re-run failed jobs"
    repeats), and each rung acts on the workflow file as of the tag.
  - **Pins**, in `tests/test_publish_one_artifact.py` ({cases} cases, 69 before): the new job's name, `needs`,
    permissions, steps and lack of an environment; the PyPI job needing both TestPyPI jobs; each job's keys, runner
    and exact steps, as (name, action); no `continue-on-error` and no `if:` beyond the listed ones; no `PIP_*`
    variable in any `env`; each build step's command; the install step's exact script and commands, run from
    `$RUNNER_TEMP`; no `skip_existing` and no `attestations: false`; retention of exactly 90 days; the workflow's
    name ending in "to PyPI", which juniper-ml's monitor requires; the tag prefix with its guard; and each action
    pinned to one ref. The template blocks' and the republish job's digests are now taken with each `uses:` line
    reduced to its action's name, so a Dependabot bump of an action's pin needs no re-port; juniper-ml's
    cross-repository check of the ports still compares each `uses:` with the template's exact SHA. The rehearsals
    run the new find step against the stand-in GitHub API (no release run, a failed upload, a failed or unfinished
    install check, a failed build, a job a re-run carried over, a failure a re-run repaired, a "Re-run all jobs"
    whose second attempt failed, each listing order, a listing over two pages, an older run that passed behind a
    newer one that failed, and both tag prefixes), the fetch step against a release run and a TestPyPI that name
    different files, the install step's own shell against stand-in `pip`, `python` and `sleep`, and its
    post-install check against a stand-in installed wheel, with and without the package. A new module,
    `tests/test_publish_docs_bounds.py`, reads the install check's tries, waits and lag error from the workflow and
    requires `docs/REFERENCE.md` to state them, whitespace aside. Each of {mutations} edits to a copy of the
    workflow or its doc, one at a time, fails the tests, and a Dependabot-style bump of every pin of one action
    passes them.
"""


def reference(text: str, today: str) -> str:
    """docs/REFERENCE.md: the workflow row, § Publishing and Recovery, the version (patch + 1) and the date."""
    where = REFERENCE_PATH
    word = detect_word(text, "**A release that did not reach PyPI**: the {word}'s recovery ladder", where)
    text = replace_once(text, REFERENCE_ROW_OLD, REFERENCE_ROW_NEW, where)
    text = replace_once(text, REFERENCE_SECTION_OLD.replace("{word}", word), REFERENCE_SECTION_NEW.replace("{word}", word), where)
    versions = set(VERSION_LINE.findall(text))
    if len(VERSION_LINE.findall(text)) != 2 or len(versions) != 1:
        raise Refused(f"{where}: expected its '**Version:**' line twice, with one value: {sorted(versions)}")
    major, minor, patch = versions.pop()
    text = replace_each(text, f"**Version:** {major}.{minor}.{patch}\n", f"**Version:** {major}.{minor}.{int(patch) + 1}\n", 2, where)
    dated = sorted({line for line in text.splitlines(keepends=True) if line.startswith(DATE_PREFIX)})
    if len(dated) != 1:
        raise Refused(f"{where}: its '{DATE_PREFIX}' lines disagree or are missing: {dated}")
    day = datetime.date.fromisoformat(today)
    return replace_each(text, dated[0], f"{DATE_PREFIX}{day:%B} {day.day}, {day.year}\n", 2, where)


def changelog(text: str, entry: str) -> str:
    """Append the entry to the end of ``[Unreleased]``'s ``### Fixed`` (creating the heading if a release emptied it)."""
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise Refused(f"{CHANGELOG_PATH}: no single '## [Unreleased]' heading")
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


# ─────────────────────────────────────────────────────────────────────────────────────────────
# tests/test_publish_one_artifact.py, replaced whole (its base's sha256 is BASE_TEST_SHA256)
# ─────────────────────────────────────────────────────────────────────────────────────────────
#: The new module's case count (pytest --collect-only on the result), and the mutation proof's edit count.
TEST_CASES = "118"
MUTATIONS = "38"
# BEGIN DOCS_TEST
DOCS_TEST = r'''"""Pin the publish docs' numbers to the publish workflow: the bounds the docs state are the bounds the steps run.

``docs/REFERENCE.md`` § Publishing and Recovery gives an operator the numbers that decide whether a failed install check
was index lag: how many times the check tries, how far apart, how long it waits first, and the error it stops with. Each
is read here from ``publish.yml`` and required in the doc, so a change to either side alone fails. A module of its own, as
juniper-cascor's is (juniper-cascor#777): ``test_publish_one_artifact.py`` reads the workflow alone.

Project: juniper-data-client
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# ci.yml's unit lane runs ``pytest tests/`` with no marker filter, so this module runs there; the mark files it with
# the unit tests, and the integration lane (``-m integration``) leaves it out. Module-level, so it covers tests added later.
pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".github" / "workflows" / "publish.yml"
DOC = REPO / "docs" / "REFERENCE.md"
INSTALL = "verify-testpypi-install"
INSTALL_STEP = "Verify TestPyPI install"


def _doc() -> str:
    """The doc's text with each run of whitespace made one space: a rewrapped paragraph states the same bounds."""
    return " ".join(DOC.read_text(encoding="utf-8").split())


def _install_run() -> str:
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"][INSTALL]["steps"]
    found = [s for s in steps if s.get("name") == INSTALL_STEP]
    assert len(found) == 1, f"expected exactly one step named {INSTALL_STEP!r}"
    return str(found[0]["run"])


def _retry() -> tuple[int, list[int], list[int]]:
    """The install check's (tries, the waits inside its loop, the waits before it), read from its commands."""
    commands = [line.strip() for line in _install_run().splitlines() if line.strip() and not line.strip().startswith("#")]
    loops = [i for i, c in enumerate(commands) if re.fullmatch(r"for attempt in [0-9 ]+; do", c)]
    assert len(loops) == 1, "expected one retry loop"
    start, end = loops[0], commands.index("done", loops[0])
    tries = len(commands[start].split()[3:-1])
    waits = [int(c.split()[1]) for c in commands[start:end] if re.fullmatch(r"sleep [0-9]+", c)]
    before = [int(c.split()[1]) for c in commands[:start] if re.fullmatch(r"sleep [0-9]+", c)]
    return tries, waits, before


class TestPublishDocsStateTheBounds:
    def test_the_install_checks_retry(self):
        tries, waits, before = _retry()
        # One loop: its tries, a wait between them and none after the last; and one wait before the first try.
        assert len(waits) == 1
        assert len(before) == 1
        doc = _doc()
        assert f"It makes {tries} tries, {waits[0]} s apart, after a {before[0]} s wait" in doc
        # The error the check stops with after its last try, as the step prints it and as the doc quotes it.
        error = f"is not installable from TestPyPI after {tries} tries (index lag?)"
        assert error in _install_run()
        assert error in doc
'''
# END DOCS_TEST
# BEGIN NEW_TEST
NEW_TEST = r'''"""Pin the one-artifact publish: PyPI takes exactly the files TestPyPI took, and the run checks it by sha256.

The owner's directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to testpypi.
an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to
prevent this from slipping through the cracks again." ``publish.yml`` ran ``python -m build`` in its TestPyPI job and
again in its PyPI job, so PyPI served a second build of each release: the juniper-data-client 0.6.0 wheel is
``bf9028fd...`` on PyPI and ``b4d134e1...`` on TestPyPI, and the 0.5.0 wheel ``66f1c744...`` against ``022a65bd...``.
Its TestPyPI upload also set ``skip-existing``, which keeps an earlier file under the same name, so the install
check could test a file this run did not build; the port drops it and keeps ``attestations`` and ``verbose``.

This ports juniper-cascor's fix (juniper-cascor#763 and #767) and its sweep (juniper-cascor#777). ``publish.yml`` now
builds once and hands both publish jobs one artifact, the dist directory plus ``SHA256SUMS``. A re-run attempt reuses
that artifact rather than build again, because download-artifact takes the newest artifact of a name. Only the jobs
that upload hold ``id-token: write``. A dispatch from the release tag runs the republish job, the first step of the
owner's recovery ladder (2026-11-15): it copies TestPyPI's files for the version to PyPI and builds nothing, and only
once the tag's newest release run passed its TestPyPI jobs in their latest attempt (ruling 1 of 2026-11-16). The
template steps and the republish job are juniper-cascor's, copied verbatim: they read only ``PUBLISH_PACKAGE``,
``PUBLISH_DIST_DIR`` and ``PUBLISH_TAG_PREFIX`` from the workflow ``env``, a step's ``INDEX_URL``, and the runner's own
variables.

The static cases pin the wiring: one build, in a job without an environment or ``id-token``; the job chain and the job
names juniper-ml's release-train ceremony reads, the workflow's own name among them; per-job permissions; each job's
keys, runner and exact steps, with no ``if:`` but the listed ones and no ``continue-on-error``; each build step's
commands; the reuse step first in the build job and guarding every later step; each upload preceded by the dist check;
TestPyPI's JSON checked after the TestPyPI upload and again before the PyPI one, and PyPI's after; no ``skip-existing``
and no ``attestations: false``; an artifact kept 90 days, past the 30-day ``pypi`` gate; the install check in a job of
its own, which cannot mint a credential, runs exactly its script from outside any checkout, and is needed by the PyPI
job (ruling 2 of 2026-11-16); the republish job's trigger, gate, steps and name; the triggers, tag guard and tag
prefix, build commands, upload inputs and install check this workflow kept; and every template block, and the
republish job, juniper-cascor's byte for byte once each ``uses:`` line is reduced to its action's name, with each action
pinned to one ref. The rehearsals run each template step's own Python, extracted from ``publish.yml``, in a scratch
workspace, against a stand-in index and a stand-in GitHub API on 127.0.0.1, the republish job's refusal among them;
the install check's own shell, against stand-in ``pip``, ``python`` and ``sleep`` commands; and its post-install
check's own Python, against a stand-in installed wheel.

Project: juniper-data-client
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import re
import shlex
import shutil
import subprocess  # nosec B404 - runs the workflow's OWN extracted step scripts with a fixed argv
import sys
import threading
from pathlib import Path

import pytest
import yaml

# ci.yml's unit lane runs ``pytest tests/`` with no marker filter, so this module runs there; the mark files it with
# the unit tests, and the integration lane (``-m integration``) leaves it out. Module-level, so it covers tests added later.
pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github" / "workflows"
#: This repository's distribution, its file-name form (also its import name), and another distribution whose name this
#: one's starts with.
PACKAGE = "juniper-data-client"
DIST_NAME = "juniper_data_client"
OTHER_DIST_NAME = "juniper_data"
#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build``, an install check and a ``republish`` job.
PUBLISHERS = {
    "publish.yml": (PACKAGE, "dist", "testpypi", "pypi"),
}
#: workflow -> (top-level permissions, the PyPI job's). The build, TestPyPI, install-check and republish jobs hold the same in every publisher.
PERMISSIONS = {
    "publish.yml": ({}, {"id-token": "write"}),
}
#: workflow -> PUBLISH_TAG_PREFIX, what the package's release tags start with (the version is the rest): ``v`` in a
#: single-package publisher, ``<package>-v`` in a sub-package one.
TAG_PREFIXES = {"publish.yml": "v"}
#: workflow -> its ``name:``. juniper-ml's release-train monitor drops every run of a workflow whose name does not end in
#: "to PyPI" (``PYPI_PUBLISHER_NAME_SUFFIX`` in ``util/release_train/ceremony.py``), so a renamed publisher fails quietly.
WORKFLOW_NAMES = {"publish.yml": "Publish to PyPI"}
#: Ruling 2 of 2026-11-16: the install check runs in a job of its own, which holds no ``id-token``. Its name holds
#: "TestPyPI", so the release-train ceremony counts it with the TestPyPI job and reads its failure as HALT_TESTPYPI.
INSTALL = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
#: workflow -> the install check's step name, kept from the TestPyPI job it moved out of.
INSTALL_STEPS = {"publish.yml": "Verify TestPyPI install"}
#: The template's sub-package build jobs carry this release-convention gate. It runs on ``push`` alone, an event no
#: publisher subscribes to, so it never runs: it is the one build step exempt from the reuse condition, and it is exempt
#: by its name. This repository's build job has no such step (its exact step list is in ``STEPS``).
RELEASE_GATE = "Require a GitHub Release for this tag"
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
INDEX_CHECKS = {TESTPYPI_AFTER: "https://test.pypi.org", TESTPYPI_BEFORE: "https://test.pypi.org", PYPI_AFTER: "https://pypi.org"}
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
#: The template is juniper-cascor's: the sha256 of each template block (raw, from its "One-artifact publish template"
#: comment to the end of its step) and of the republish job (from its banner to the end of the job) in juniper-cascor's
#: .github/workflows/publish.yml at f5ed3017 (juniper-cascor#777; main 5e3d9801 holds it unchanged), each taken of the
#: text with every ``uses:`` line reduced to its action's name (``_normalized``). Change the template there first, then
#: copy it here.
TEMPLATE_SOURCE = "juniper-cascor .github/workflows/publish.yml at f5ed3017"
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
#: A ``uses:`` line: its action's name, then the ``@ref`` and the ``# vX.Y.Z`` comment Dependabot moves together.
USES_REF = re.compile(r"^(\s*(?:- )?uses: )([^@\s]+)@\S+(?:[ \t]+#[^\n]*)?$", re.MULTILINE)
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
BUILD_COMMAND = re.compile(r"\bpython3?\s+-m\s+build\b|\bpip3?\s+wheel\b|\buv\s+build\b|\bsetup\.py\s+(?:sdist|bdist_wheel)\b")
#: GitHub lets a deployment wait this many days for its reviewer: the PyPI job may start that late, and needs the artifact.
GATE_APPROVAL_DAYS = 30
#: The artifact's retention, as docs/REFERENCE.md states it: past the gate's 30 days and the 30-day re-run window.
RETENTION_DAYS = 90
ARTIFACT = "${{ env.PUBLISH_PACKAGE }}-dist"
ARTIFACT_NAME = f"{PACKAGE}-dist"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
WHEEL = f"{DIST_NAME}-9.9.9-py3-none-any.whl"
SDIST = f"{DIST_NAME}-9.9.9.tar.gz"
BUILT = {WHEEL: b"wheel bytes", SDIST: b"sdist bytes"}
JSON_PATH = f"/pypi/{PACKAGE}/9.9.9/json"
REPOSITORY = f"pcalnon/{PACKAGE}"
#: The actions the publisher uses, by name: a step is compared with its ``@ref`` dropped, so a Dependabot bump of a pin
#: changes nothing here (``test_each_action_is_pinned_to_one_ref_in_every_publisher`` holds each to one ref).
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
STEPS = {
    "build": [(REUSE, None), (None, CHECKOUT), (None, SETUP_PYTHON), ("Install build tools", None), ("Build package", None), ("Check package", None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)],
    "testpypi": TESTPYPI_STEPS,
    # The setup-python the TestPyPI job ran, the sparse checkout of the pyproject.toml the version is read from, then the check.
    INSTALL: [(None, SETUP_PYTHON), (None, CHECKOUT), (INSTALL_STEPS["publish.yml"], None)],
    "pypi": PYPI_STEPS,
    REPUBLISH: REPUBLISH_STEPS,
}
#: The TestPyPI upload's inputs and the PyPI upload's, exactly: a misspelled input (``skip_existing``) or a value turned
#: off (``attestations: false``) would pass a check of named keys.
UPLOAD_INPUTS = ({"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT, "verbose": True, "attestations": True}, {"packages-dir": DIST_INPUT, "attestations": True})
#: Every key the workflow and each of its jobs carries. An ``env`` on a job (``PIP_EXTRA_INDEX_URL``,
#: ``HASH_CHECK_ATTEMPTS``), a container, a matrix or another runner would change what a check runs, or against what.
WORKFLOW_KEYS = {"name", "on", "permissions", "env", "jobs"}
BUILD_JOB_KEYS = {"name", "if", "runs-on", "permissions", "steps"}
PUBLISH_JOB_KEYS = {"name", "needs", "runs-on", "environment", "permissions", "steps"}
INSTALL_JOB_KEYS = {"name", "needs", "runs-on", "permissions", "steps"}
REPUBLISH_JOB_KEYS = {"name", "if", "runs-on", "environment", "permissions", "steps"}
#: The keys the template lets a repository add, none of which changes what a check runs: the workflow's ``run-name``,
#: which names the run, and a ``concurrency`` group that never cancels a run in progress (this workflow sets none, which
#: TestUnchanged pins); a job's ``timeout-minutes``, which stops it sooner, so nothing after it runs. The republish job is
#: compared with juniper-cascor's whole, so it takes none here. No job takes a ``concurrency`` group: by default
#: (``queue: single``) GitHub keeps one pending job per group and cancels the older one when another queues, so a group
#: on the PyPI job could stop a run between its two uploads.
OPTIONAL_WORKFLOW_KEYS = {"run-name", "concurrency"}
OPTIONAL_JOB_KEYS = {"timeout-minutes"}
#: workflow -> each build step's command: the build, and the check of what it built.
BUILD_RUNS = {"publish.yml": {"Install build tools": "pip install build twine", "Build package": "python -m build", "Check package": "twine check dist/*"}}
#: The install check's bounded retry: this many tries, this many seconds apart, after one wait before the first.
INSTALL_TRIES = 5
INSTALL_RETRY_SECONDS = 10
INSTALL_FIRST_WAIT_SECONDS = 30
LAG_ERROR = "is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"
#: The install check's script, exactly, comments included: a check of its parts would pass a ``|| true`` on the pip line.
#: juniper-ml's cross-repository check pins the same text (util/ad-hoc/2026-11-24_publish_port_install_pins.json).
INSTALL_CHECK_RUN = """\
# `python -c` puts its working directory first on sys.path, and this repository's root holds
# juniper_data_client/, so an import run inside a checkout of it can pass without the wheel. This job's
# checkout is sparse, for the pyproject.toml the version is read from, and the step still installs and
# imports from the runner's temporary directory, outside the checkout.
cd "${RUNNER_TEMP}"
VERSION=$(python -c "import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])")
sleep 30
# NOTE (security): install with --no-deps against TestPyPI only. Do NOT add a
# production-PyPI fallback index here — with --no-deps no deps are fetched, so a
# fallback only risks resolving a squatted target package.
# TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.
for attempt in 1 2 3 4 5; do
  if pip install \\
    --no-deps \\
    --index-url https://test.pypi.org/simple/ \\
    "juniper-data-client==${VERSION}"; then
    break
  fi
  if [ "${attempt}" -eq 5 ]; then
    echo "::error::juniper-data-client ${VERSION} is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"
    exit 1
  fi
  echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"
  sleep 10
done
# No import: juniper_data_client imports numpy/requests at import time, which are absent under
# --no-deps. Verify the published artifact via its installed metadata, and that the wheel holds the
# package: find_spec locates it without running it. SystemExit fails the step: PYTHONOPTIMIZE would
# strip an assert statement.
python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('juniper_data_client'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('juniper-data-client'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no juniper_data_client package')"
"""


def _retried_install(package: str, version: str) -> list[str]:
    """The install the check runs: five tries, 10 s apart, and after the fifth failure an error that names index lag,
    rather than a check that fails as if the package were broken."""
    return [
        "for attempt in 1 2 3 4 5; do",
        "if pip install \\",
        "--no-deps \\",
        "--index-url https://test.pypi.org/simple/ \\",
        f'"{package}==${{{version}}}"; then',
        "break",
        "fi",
        'if [ "${attempt}" -eq 5 ]; then',
        f'echo "::error::{package} ${{{version}}} {LAG_ERROR}"',
        "exit 1",
        "fi",
        'echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
        "sleep 10",
        "done",
    ]


#: The post-install check: the installed metadata's version, and the package found with an origin, without running it
#: (an import would load numpy and requests, absent under --no-deps): the metadata alone would pass a wheel that lacks the
#: package. It fails through SystemExit, which PYTHONOPTIMIZE keeps, where it strips an assert statement. Its line is
#: juniper-cascor's neutral one (publish-protocol.yml), printed before the check: it says no "OK".
POST_INSTALL_CHECK = f"import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{DIST_NAME}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{PACKAGE}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {DIST_NAME} package')"
#: workflow -> its install step's commands, exactly, comment and blank lines dropped: no ``exit 0``, ``trap``, earlier
#: install or second VERSION can be added and none dropped, while a comment may change freely (``INSTALL_CHECK_RUN``
#: pins those too).
INSTALL_COMMANDS = {
    "publish.yml": [
        'cd "${RUNNER_TEMP}"',
        """VERSION=$(python -c "import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])")""",
        f"sleep {INSTALL_FIRST_WAIT_SECONDS}",
        *_retried_install(PACKAGE, "VERSION"),
        f'python -c "{POST_INSTALL_CHECK}"',
    ],
}
#: workflow -> the install step's keys beyond its name and script: none, since the version comes from pyproject.toml.
INSTALL_STEP_EXTRA = {"publish.yml": {}}
#: The variable the reuse and find steps read the runner's API credential from, the expression that fills it, and the
#: stand-in value the rehearsals pass. Bandit's B105 reads a string under a name like the first as a hardcoded password.
API_CREDENTIAL_ENV = "GH_TOKEN"
RUNNER_CREDENTIAL = "${{ github.token }}"
FAKE_API_CREDENTIAL = "stand-in-credential"


def _workflow(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) reads the bare `on:` key as boolean True.
    data["on"] = data.pop(True, data.get("on"))
    return data


def _names(job: dict) -> list[str]:
    return [str(s.get("name") or s.get("uses") or "") for s in job.get("steps") or []]


def _index(job: dict, name: str) -> int:
    names = _names(job)
    assert names.count(name) == 1, f"expected exactly one step named {name!r}, found {names.count(name)} in {names}"
    return names.index(name)


def _step(job: dict, name: str) -> dict:
    return job["steps"][_index(job, name)]


def _uploads(job: dict) -> list[int]:
    return [i for i, s in enumerate(job.get("steps") or []) if str(s.get("uses") or "").startswith(PUBLISH_ACTION)]


def _environment(job: dict) -> str:
    env = job.get("environment")
    return str(env.get("name") if isinstance(env, dict) else env)


def _assert_no_checkout_between(job: dict, start: int, end: int) -> None:
    """A checkout empties the workspace, so one between the download and the last template step would lose the files."""
    between = [str(s.get("uses") or "") for s in job["steps"][start:end]]
    assert not [u for u in between if u.startswith("actions/checkout@")], f"a checkout runs between steps {start} and {end}: {between}"


def _steps(job: dict) -> list[tuple[str | None, str | None]]:
    """Each step as (its name, the action it uses with the ``@ref`` dropped)."""
    return [(s.get("name"), str(s["uses"]).split("@", 1)[0] if s.get("uses") else None) for s in job.get("steps") or []]


def _allowed_if(job_id: str, index: int, step: dict) -> str | None:
    """The one ``if:`` a step may carry: the reuse step's own, the reuse condition on every later build step but the
    template's push-only release gate (exempt by its name), and the republish job's download of the release run's
    artifact. Any other ``if:`` could skip a check."""
    if job_id == "build":
        if index == 0:
            return "github.run_attempt != '1'"
        return "github.event_name == 'push'" if step.get("name") == RELEASE_GATE else REUSE_IF
    if job_id == REPUBLISH and step.get("name") == FETCH_ORIGINAL:
        return "steps.original.outputs.run-id != ''"
    return None


def _template_scripts() -> dict[str, str]:
    """The template steps' Python, as ``publish.yml`` runs it; every copy elsewhere must equal these."""
    jobs = _workflow("publish.yml")["jobs"]
    return {
        REUSE: _step(jobs["build"], REUSE)["run"],
        RECORD: _step(jobs["build"], RECORD)["run"],
        VERIFY_DIST: _step(jobs["testpypi"], VERIFY_DIST)["run"],
        "index": _step(jobs["testpypi"], TESTPYPI_AFTER)["run"],
        FIND: _step(jobs[REPUBLISH], FIND)["run"],
        FETCH: _step(jobs[REPUBLISH], FETCH)["run"],
    }


def _template_blocks(text: str) -> dict[str, str]:
    """Each template block of a workflow, keyed ``<job>/<step name>``: raw text, from its "One-artifact publish template"
    comment to the end of its step, comments included. Run-script lines are indented deeper than any step-level line,
    so they never end a block early."""
    lines = text.splitlines(keepends=True)
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
            key = f"{job}/{name}"
            assert key not in blocks, f"two template blocks for {key}"
            blocks[key] = "".join(lines[i:end]).rstrip("\n") + "\n"
            i = end
            continue
        i += 1
    return blocks


def _republish_job(text: str) -> str:
    """The republish job, raw: from the comment banner above it to the last line before the next job, if any."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == f"  {REPUBLISH}:\n"]
    assert len(at) == 1, f"expected one {REPUBLISH} job, found {len(at)}"
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    end = at[0] + 1
    while end < len(lines) and not (lines[end].strip() and len(lines[end]) - len(lines[end].lstrip(" ")) <= 2):
        end += 1
    return "".join(lines[start:end]).rstrip("\n") + "\n"


def _normalized(block: str) -> str:
    """BLOCK with every ``uses:`` line reduced to its action's name, its ``@ref`` and trailing ``# vX.Y.Z`` dropped, so a
    Dependabot bump of an action's pin needs no re-port (the template sweep, juniper-cascor#777), and every other byte
    is still compared. juniper-ml's cross-repository check of the ports compares each ``uses:`` with the template's
    exact SHA."""
    return USES_REF.sub(r"\1\2", block)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script(kind: str, tmp_path: Path) -> Path:
    path = tmp_path / f"{re.sub(r'[^a-z]+', '_', kind.lower())}.py"
    path.write_text(_template_scripts()[kind], encoding="utf-8")
    return path


def _run(script: Path, workspace: Path, cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess[str]:
    """Run an extracted step as the runner does (``python3 {0}``), with a minimal environment rather than a copy of ours."""
    child = {"PATH": os.environ.get("PATH", ""), "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": PACKAGE, "PUBLISH_DIST_DIR": "dist", "PUBLISH_TAG_PREFIX": "v"}
    child.update(env)
    return subprocess.run([sys.executable, "-I", str(script)], cwd=cwd or workspace, env=child, capture_output=True, text=True, timeout=120, check=False)  # nosec B603 - fixed argv: this interpreter and an extracted step


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / "dist").mkdir(parents=True)
    for name, data in BUILT.items():
        (root / "dist" / name).write_bytes(data)
    return root


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
        stand = self.server
        stand.requests.append((self.path, dict(self.headers.items())))
        answers = stand.routes.get(self.path) or [(404, {"message": "Not Found"})]
        status, body = answers.pop(0) if len(answers) > 1 else answers[0]
        payload = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        """Quiet: the cases read the requests the step made, not the server's log."""
        return


@pytest.fixture
def stand():
    started: list[_Stand] = []

    def start(routes: dict[str, list[tuple[int, object]]]) -> _Stand:
        server = _Stand(routes)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        started.append(server)
        return server

    yield start
    for server in started:
        server.shutdown()
        server.server_close()


def _release(files: dict[str, str], base: str = "https://test-files.example") -> dict:
    return {"info": {"name": PACKAGE, "version": "9.9.9"}, "urls": [{"filename": name, "url": f"{base}/files/{name}", "digests": {"sha256": digest, "md5": "0" * 32}} for name, digest in files.items()]}


NOT_FOUND = (404, {"message": "Not Found"})
SERVED = {name: _sha(data) for name, data in BUILT.items()}


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Wiring: one build, one artifact, a check before every upload, and the names the release train reads
# ─────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
class TestWiring:
    def test_the_template_parameters_name_this_package(self, workflow):
        package, dist_dir, _, _ = PUBLISHERS[workflow]
        wf = _workflow(workflow)
        assert wf["env"] == {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist_dir, "PUBLISH_TAG_PREFIX": TAG_PREFIXES[workflow]}
        # A single-package publisher's tags are v<version>; a sub-package publisher's are <package>-v<version>.
        assert TAG_PREFIXES[workflow] == ("v" if dist_dir == "dist" else f"{package}-v")
        # A job-level if: cannot read env, so the build job's tag guard repeats the prefix: the two must agree.
        assert f"startsWith(github.event.release.tag_name, '{TAG_PREFIXES[workflow]}')" in wf["jobs"]["build"]["if"]

    def test_the_workflow_name_ends_in_to_pypi_as_the_release_train_monitor_requires(self, workflow):
        name = _workflow(workflow)["name"]
        assert name == WORKFLOW_NAMES[workflow]
        assert name.lower().endswith("to pypi")

    def test_only_the_build_job_builds_and_it_holds_no_environment(self, workflow):
        jobs = _workflow(workflow)["jobs"]
        builders = sorted(job_id for job_id, job in jobs.items() if any(BUILD_COMMAND.search(str(s.get("run") or "")) for s in job.get("steps") or []))
        assert builders == ["build"]
        assert jobs["build"]["name"] == "Build and Validate"
        assert "environment" not in jobs["build"]
        assert not _uploads(jobs["build"])

    def test_the_publish_jobs_chain_on_the_build_under_the_names_the_release_train_reads(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        assert sorted(jobs) == sorted(["build", test_id, INSTALL, prod_id, REPUBLISH])
        assert jobs[test_id]["needs"] == "build"
        assert jobs[INSTALL]["needs"] == test_id
        # PyPI waits for both TestPyPI jobs: the upload with its checks, and the install check.
        assert jobs[prod_id]["needs"] == [test_id, INSTALL]
        # juniper-ml's util/release_train/ceremony.py tells the jobs apart by name: "testpypi" (both TestPyPI jobs) and "pypi".
        assert jobs[test_id]["name"] == "Publish to TestPyPI"
        assert jobs[INSTALL]["name"] == INSTALL_NAME
        assert jobs[prod_id]["name"] == "Publish to PyPI"
        assert _environment(jobs[test_id]) == "testpypi"
        assert _environment(jobs[prod_id]) == "pypi"

    def test_only_the_jobs_that_upload_hold_id_token_write(self, workflow):
        wf = _workflow(workflow)
        jobs = wf["jobs"]
        top, prod = PERMISSIONS[workflow]
        assert wf["permissions"] == top
        uploading = sorted(job_id for job_id, job in jobs.items() if _uploads(job))
        minting = sorted(job_id for job_id, job in jobs.items() if (job.get("permissions") or {}).get("id-token") == "write")
        assert uploading == minting == sorted(PUBLISHERS[workflow][2:] + (REPUBLISH,))
        assert jobs["build"]["permissions"] == {"contents": "read", "actions": "read"}
        # The job that can mint runs the template steps and the upload alone: it checks out nothing and installs nothing.
        assert jobs[PUBLISHERS[workflow][2]]["permissions"] == {"id-token": "write"}
        # The install check installs the package TestPyPI serves: it may read the repository, and nothing more.
        assert jobs[INSTALL]["permissions"] == {"contents": "read"}
        assert jobs[PUBLISHERS[workflow][3]]["permissions"] == prod
        assert jobs[REPUBLISH]["permissions"] == {"actions": "read", "id-token": "write"}

    def test_a_re_run_reuses_the_first_attempts_artifact_instead_of_building(self, workflow):
        build = _workflow(workflow)["jobs"]["build"]
        reuse = build["steps"][0]
        assert reuse.get("name") == REUSE
        assert reuse.get("id") == "reuse"
        assert reuse.get("if") == "github.run_attempt != '1'"
        # It runs before the checkout, so it names the workspace rather than a job default directory a checkout creates.
        assert reuse.get("working-directory") == "${{ github.workspace }}"
        assert reuse.get("shell") == "python3 {0}"
        assert reuse.get("env") == {API_CREDENTIAL_ENV: RUNNER_CREDENTIAL}
        # Every later step is skipped once the reuse step finds the artifact, except the template's release-convention
        # gate, which runs on `push` alone, an event no publisher subscribes to. It is exempt by its name: an exemption by
        # its `if:` text would let any build step trade the reuse condition for the push condition.
        for step in build["steps"][1:]:
            if step.get("name") == RELEASE_GATE:
                assert step.get("if") == "github.event_name == 'push'"
                continue
            assert step.get("if") == REUSE_IF, f"{step.get('name') or step.get('uses')} would run on a re-run that reuses the artifact"
        for name in (RECORD, UPLOAD):
            assert _step(build, name).get("if") == REUSE_IF

    def test_the_testpypi_job_checks_the_dist_uploads_then_checks_testpypi_before_the_install_check(self, workflow):
        _, _, test_id, _ = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        job = jobs[test_id]
        uploads = _uploads(job)
        assert len(uploads) == 1
        assert job["steps"][uploads[0]]["with"]["repository-url"] == "https://test.pypi.org/legacy/"
        assert _index(job, DOWNLOAD) < _index(job, VERIFY_DIST) < uploads[0] < _index(job, TESTPYPI_AFTER)
        # The job ends at the sha256 check that vouches for what the install check installs, in the job that needs it.
        assert _index(job, TESTPYPI_AFTER) == len(job["steps"]) - 1
        assert not [s for s in job["steps"] if "pip install" in str(s.get("run") or "")], "the job that can mint runs an install check"
        installs = [s for s in jobs[INSTALL]["steps"] if "pip install" in str(s.get("run") or "")]
        assert installs, "the TestPyPI install check is gone"
        assert jobs[INSTALL]["needs"] == test_id, "the install check must come after the sha256 check that vouches for what it installs"
        _assert_no_checkout_between(job, 0, len(job["steps"]))

    def test_the_pypi_job_rechecks_testpypi_before_its_upload_and_pypi_after(self, workflow):
        _, _, _, prod_id = PUBLISHERS[workflow]
        job = _workflow(workflow)["jobs"][prod_id]
        uploads = _uploads(job)
        assert len(uploads) == 1
        assert "repository-url" not in (job["steps"][uploads[0]].get("with") or {})
        assert _index(job, DOWNLOAD) < _index(job, VERIFY_DIST) < _index(job, TESTPYPI_BEFORE) < uploads[0] < _index(job, PYPI_AFTER)
        _assert_no_checkout_between(job, _index(job, DOWNLOAD), _index(job, PYPI_AFTER))

    def test_the_republish_job_runs_only_on_its_dispatch_behind_the_pypi_gate_and_builds_nothing(self, workflow):
        wf = _workflow(workflow)
        job = wf["jobs"][REPUBLISH]
        assert job["name"] == REPUBLISH_NAME
        # The ceremony counts a job as the TestPyPI or the PyPI job by those substrings; this one must be neither.
        assert "pypi" not in job["name"].lower()
        assert job["if"] == REPUBLISH_IF
        assert "needs" not in job
        assert _environment(job) == "pypi"
        assert wf["on"]["workflow_dispatch"]["inputs"] == {"republish_from_testpypi": {"description": "Copy TestPyPI's files for this tag's version to PyPI (run from the release tag; nothing is built)", "type": "boolean", "default": False}}
        uploads = _uploads(job)
        assert len(uploads) == 1
        assert job["steps"][uploads[0]].get("with") == {"packages-dir": DIST_INPUT}
        assert _index(job, FIND) < _index(job, FETCH_ORIGINAL) < _index(job, FETCH) < _index(job, VERIFY_DIST) < uploads[0] < _index(job, PYPI_AFTER)
        _assert_no_checkout_between(job, 0, len(job["steps"]))
        assert _step(job, FIND).get("id") == "original"
        assert _step(job, FIND).get("env") == {API_CREDENTIAL_ENV: RUNNER_CREDENTIAL}
        assert _step(job, FETCH_ORIGINAL)["if"] == "steps.original.outputs.run-id != ''"
        assert _step(job, FETCH_ORIGINAL)["with"] == {"name": ARTIFACT, "run-id": "${{ steps.original.outputs.run-id }}", "github-token": RUNNER_CREDENTIAL, "path": "${{ runner.temp }}/release-run"}
        assert _step(job, FETCH)["env"] == {"INDEX_URL": "https://test.pypi.org", "VERSION": "${{ steps.original.outputs.version }}", "RELEASE_RUN_SUMS": "${{ runner.temp }}/release-run/SHA256SUMS"}
        assert _step(job, PYPI_AFTER)["env"] == {"INDEX_URL": "https://pypi.org"}

    def test_every_upload_takes_the_downloaded_dist_and_none_skips_an_existing_file(self, workflow):
        for job in _workflow(workflow)["jobs"].values():
            for i in _uploads(job):
                inputs = job["steps"][i].get("with") or {}
                assert inputs.get("packages-dir") == DIST_INPUT
                # skip-existing would keep an earlier file under the same name, and the install check would test it. The
                # action still reads its older spelling too.
                assert "skip-existing" not in inputs
                assert "skip_existing" not in inputs
                # Attestations stay on, the action's default.
                assert inputs.get("attestations", True) is True

    def test_one_artifact_carries_the_dist_and_sha256sums_and_outlives_the_pypi_gate(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        upload = _step(jobs["build"], UPLOAD)["with"]
        assert upload["name"] == ARTIFACT
        assert [p.strip() for p in upload["path"].splitlines() if p.strip()] == [DIST_INPUT, "SHA256SUMS"]
        assert upload["if-no-files-found"] == "error"
        # Exactly the documented 90 days, which outlive the gate's 30 days and the 30-day re-run window.
        assert upload["retention-days"] == RETENTION_DAYS
        assert RETENTION_DAYS > GATE_APPROVAL_DAYS
        assert _index(jobs["build"], RECORD) < _index(jobs["build"], UPLOAD)
        for job_id in (test_id, prod_id):
            assert _step(jobs[job_id], DOWNLOAD)["with"] == {"name": ARTIFACT, "path": "${{ github.workspace }}"}

    def test_each_json_check_reads_its_own_index_and_keeps_the_default_bounds(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        for job_id, name in ((test_id, TESTPYPI_AFTER), (prod_id, TESTPYPI_BEFORE), (prod_id, PYPI_AFTER)):
            assert _step(jobs[job_id], name)["env"] == {"INDEX_URL": INDEX_CHECKS[name]}

    def test_every_job_carries_only_its_listed_keys_and_runs_on_a_hosted_runner(self, workflow):
        # A job-level env (PIP_EXTRA_INDEX_URL, or HASH_CHECK_ATTEMPTS over a JSON check's bounds), a container, a matrix
        # or a self-hosted runner would change what a check runs, or against what. The workflow's run-name and a
        # concurrency group that never cancels, and a job's timeout-minutes, change no check, so the template admits
        # them (OPTIONAL_*_KEYS). A job's own concurrency group is refused: by default (queue: single) it cancels the
        # group's pending job when another queues.
        wf = _workflow(workflow)
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        assert WORKFLOW_KEYS <= set(wf) <= WORKFLOW_KEYS | OPTIONAL_WORKFLOW_KEYS, f"workflow keys {sorted(wf)}"
        want = {"build": BUILD_JOB_KEYS, test_id: PUBLISH_JOB_KEYS, INSTALL: INSTALL_JOB_KEYS, prod_id: PUBLISH_JOB_KEYS, REPUBLISH: REPUBLISH_JOB_KEYS}
        assert {job_id: set(job) - OPTIONAL_JOB_KEYS for job_id, job in wf["jobs"].items()} == want
        assert {job_id: job["runs-on"] for job_id, job in wf["jobs"].items()} == dict.fromkeys(want, "ubuntu-latest")

    def test_no_env_points_pip_elsewhere(self, workflow):
        # PIP_INDEX_URL or PIP_EXTRA_INDEX_URL in any env would send the install check, or the build tools, to another index.
        wf = _workflow(workflow)
        envs = [wf.get("env") or {}] + [job.get("env") or {} for job in wf["jobs"].values()] + [step.get("env") or {} for job in wf["jobs"].values() for step in job.get("steps") or []]
        assert not [key for env in envs for key in env if str(key).upper().startswith("PIP_")]

    def test_the_build_steps_run_exactly_their_commands(self, workflow):
        # `|| true` after twine check, or a build without its sdist, would ship what the build job no longer checks.
        build = _workflow(workflow)["jobs"]["build"]
        assert {name: str(_step(build, name)["run"]).strip() for name in BUILD_RUNS[workflow]} == BUILD_RUNS[workflow]


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Ruling 2 of 2026-11-16: the install check runs in a job of its own, which cannot mint a credential
# ─────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
class TestInstallCheckJob:
    def test_it_runs_after_the_testpypi_job_with_contents_read_alone_and_pypi_needs_it(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        job = jobs[INSTALL]
        assert job["name"] == INSTALL_NAME
        # juniper-ml's release-train ceremony counts every job whose name holds "testpypi" as a TestPyPI job: a failure
        # here reads HALT_TESTPYPI, and the train stops.
        assert "testpypi" in job["name"].lower()
        assert job["needs"] == test_id
        assert job["runs-on"] == "ubuntu-latest"
        assert job["permissions"] == {"contents": "read"}
        assert "environment" not in job
        assert "if" not in job
        assert not _uploads(job)
        assert jobs[prod_id]["needs"] == [test_id, INSTALL]

    def test_the_testpypi_job_keeps_only_the_template_steps_and_the_upload(self, workflow):
        _, _, test_id, _ = PUBLISHERS[workflow]
        job = _workflow(workflow)["jobs"][test_id]
        assert job["permissions"] == {"id-token": "write"}
        assert _steps(job) == TESTPYPI_STEPS
        assert not [s for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]

    def test_it_installs_and_imports_from_outside_any_checkout(self, workflow):
        job = _workflow(workflow)["jobs"][INSTALL]
        assert "defaults" not in job
        step = _step(job, INSTALL_STEPS[workflow])
        assert "working-directory" not in step
        commands = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")]
        # `python -c` puts its working directory first on sys.path, and this repository's root holds juniper_data_client/:
        # an import run inside a checkout could pass without the wheel. So the first command leaves for the runner's
        # temporary directory, and no command moves elsewhere.
        assert commands[0] == 'cd "${RUNNER_TEMP}"'
        assert [c for c in commands if c.split()[0] in ("cd", "pushd", "popd")] == ['cd "${RUNNER_TEMP}"']
        assert [c for c in commands if "pip install" in c]
        assert [c for c in commands if c.startswith("python -c ")]
        # The version is read from a sparse checkout, by its path under the workspace, and nothing runs from it. It keeps
        # no credential in the workspace while the package TestPyPI serves runs.
        checkouts = [s.get("with") for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]
        assert checkouts == [{"sparse-checkout": "pyproject.toml\n", "persist-credentials": False}]
        assert [c for c in commands if "pyproject.toml" in c] == [c for c in commands if "'${GITHUB_WORKSPACE}/pyproject.toml'" in c]

    def test_the_install_step_runs_exactly_its_commands(self, workflow):
        # Exactly these commands, in this order, comment and blank lines dropped: no `exit 0`, trap, earlier install or
        # second VERSION can be added, and none dropped, while a comment may change freely. The step carries its name and
        # script alone: no expression is pasted into the script.
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        assert [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")] == INSTALL_COMMANDS[workflow]
        assert {key: value for key, value in step.items() if key not in ("name", "run")} == INSTALL_STEP_EXTRA[workflow]
        assert "${{" not in step["run"]

    def test_the_install_check_cannot_be_switched_off(self, workflow):
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        commands = "\n".join(line for line in step["run"].splitlines() if not line.strip().startswith("#"))
        # A failed install or check must fail the job: no `|| true` (nor any `||`), no `set +e`, the runner's default
        # shell, and neither continue-on-error nor if:.
        assert "||" not in commands
        assert "set +e" not in commands
        assert "shell" not in step
        assert "continue-on-error" not in step
        assert "if" not in step
        # TestPyPI alone, with no pypi.org fallback that a same-name squatter could answer (juniper-ml#384).
        assert "--index-url https://test.pypi.org/simple/" in commands
        assert "--extra-index-url" not in commands


def _run_install(workflow: str, tmp_path: Path, pip_failures: int, python_status: int = 0, decoy: bool = False) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run WORKFLOW's install step as the runner runs a ``run:`` without a ``shell:`` (``bash -e {0}``), against stand-in
    ``pip``, ``python`` and ``sleep`` commands that log each call (the command, its directory, its arguments): ``pip``
    fails its first PIP_FAILURES calls; ``python`` runs this interpreter for the step's version read (its
    ``import tomllib``), and exits with PYTHON_STATUS for every other call, the post-install check. The workspace's
    ``pyproject.toml`` holds version 1.2.3; with DECOY, the runner's temporary directory holds one that says 6.6.6."""
    bin_dir, runner_temp, workspace = tmp_path / "bin", tmp_path / "runner-temp", tmp_path / "workspace"
    for directory in (bin_dir, runner_temp, workspace):
        directory.mkdir(parents=True)
    (workspace / "pyproject.toml").write_text('[project]\nname = "stand-in"\nversion = "1.2.3"\n', encoding="utf-8")
    if decoy:
        (runner_temp / "pyproject.toml").write_text('[project]\nname = "decoy"\nversion = "6.6.6"\n', encoding="utf-8")
    log = tmp_path / "calls.log"
    stubs = {
        "pip": 'test "$(grep -c "^pip" "$STUB_LOG")" -gt "$STUB_PIP_FAILURES"\n',
        "python": 'case "$2" in "import tomllib;"*) exec "$STUB_REAL_PYTHON" "$@" ;; esac\nexit "$STUB_PYTHON_STATUS"\n',
        "sleep": "",
    }
    for name, body in stubs.items():
        stub = bin_dir / name
        stub.write_text(f'#!/bin/sh\nprintf "%s\\t%s\\t%s\\n" "{name}" "$(pwd -P)" "$*" >> "$STUB_LOG"\n{body}', encoding="utf-8")
        stub.chmod(0o700)
    script = tmp_path / "install.sh"
    script.write_text(_step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])["run"], encoding="utf-8")
    bash = shutil.which("bash")
    assert bash, "the install check runs under bash"
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "RUNNER_TEMP": str(runner_temp), "GITHUB_WORKSPACE": str(workspace), "STUB_LOG": str(log), "STUB_PIP_FAILURES": str(pip_failures), "STUB_PYTHON_STATUS": str(python_status), "STUB_REAL_PYTHON": sys.executable}
    proc = subprocess.run([bash, "-e", str(script)], cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=60, check=False)  # nosec B603 - fixed argv: bash and the workflow's own extracted step
    calls = [line.split("\t", 2) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return proc, calls


def _post_install_check(workflow: str) -> str:
    """The Python the install step's last command, the post-install check, hands to ``python -c``."""
    step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
    commands = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")]
    argv = shlex.split(commands[-1])
    assert argv[:2] == ["python", "-c"], commands[-1]
    assert len(argv) == 3, commands[-1]
    return argv[2]


#: A stand-in installed wheel's metadata, as pip writes it beside the package: its name and version alone.
INSTALLED_METADATA = {f"{DIST_NAME}-1.2.3.dist-info/METADATA": f"Metadata-Version: 2.1\nName: {PACKAGE}\nVersion: 1.2.3\n"}


def _run_check(code: str, tmp_path: Path, files: dict[str, str], optimize: bool = False) -> subprocess.CompletedProcess[str]:
    """Run CODE as the step's ``python -c`` runs it, from an empty directory, with a stand-in site directory holding
    FILES first on ``sys.path`` and no site-packages (``-S``; ``-E`` ignores PYTHON* variables), so only the stand-in
    wheel can answer. ``-O`` is the flag form of PYTHONOPTIMIZE, which strips an assert statement."""
    site, cwd = tmp_path / "site", tmp_path / "cwd"
    for directory in (site, cwd):
        directory.mkdir()
    for rel, text in files.items():
        (site / rel).parent.mkdir(parents=True, exist_ok=True)
        (site / rel).write_text(text, encoding="utf-8")
    runner = f"import sys; sys.path.insert(0, {str(site)!r}); exec(compile({code!r}, '<post-install check>', 'exec'))"
    flags = ["-S", "-E", *(["-O"] if optimize else [])]
    return subprocess.run([sys.executable, *flags, "-c", runner], cwd=cwd, capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv: this interpreter and the workflow's own extracted check


class TestInstallCheckScript:
    """The install step's own shell, run as the runner runs it, against stand-in ``pip``, ``python`` and ``sleep``; and its
    post-install check's own Python, run against a stand-in installed wheel."""

    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_index_lag_that_outlasts_every_try_fails_naming_the_lag_and_never_imports(self, workflow, tmp_path):
        proc, calls = _run_install(workflow, tmp_path, pip_failures=INSTALL_TRIES)
        assert proc.returncode == 1
        assert f"::error::{PUBLISHERS[workflow][0]} 1.2.3 {LAG_ERROR}" in proc.stdout
        # The version read, then every try; the post-install check never runs.
        assert [call[0] for call in calls if call[0] != "sleep"] == ["python"] + ["pip"] * INSTALL_TRIES
        assert calls[0][2].startswith("-c import tomllib;")
        # One wait before the first try, a wait between tries, and none after the last.
        assert [call[2] for call in calls if call[0] == "sleep"] == [str(INSTALL_FIRST_WAIT_SECONDS)] + [str(INSTALL_RETRY_SECONDS)] * (INSTALL_TRIES - 1)

    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_a_try_that_installs_ends_the_retries_and_the_check_runs_from_runner_temp(self, workflow, tmp_path):
        package = PUBLISHERS[workflow][0]
        proc, calls = _run_install(workflow, tmp_path, pip_failures=2)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert [call[2] for call in calls if call[0] == "pip"] == [f"install --no-deps --index-url https://test.pypi.org/simple/ {package}==1.2.3"] * 3
        assert [call[0] for call in calls][-1] == "python"
        assert {call[1] for call in calls} == {str((tmp_path / "runner-temp").resolve())}
        assert "::error::" not in proc.stdout

    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_a_check_that_fails_after_the_install_fails_the_step(self, workflow, tmp_path):
        proc, calls = _run_install(workflow, tmp_path, pip_failures=0, python_status=1)
        assert proc.returncode != 0
        assert [call[0] for call in calls if call[0] != "sleep"] == ["python", "pip", "python"]

    def test_the_version_is_read_from_the_workspace_not_the_runner_temp_directory(self, tmp_path):
        # The step leaves for $RUNNER_TEMP first, so a relative path would read a pyproject.toml found there: the version
        # comes from the sparse checkout's, by its path under the workspace.
        proc, calls = _run_install("publish.yml", tmp_path, pip_failures=0, decoy=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert [call[2] for call in calls if call[0] == "pip"] == [f"install --no-deps --index-url https://test.pypi.org/simple/ {PACKAGE}==1.2.3"]

    def test_the_post_install_check_is_the_one_pinned(self):
        assert _post_install_check("publish.yml") == POST_INSTALL_CHECK

    def test_the_post_install_check_finds_the_installed_package_without_running_it(self, tmp_path):
        # The stand-in package fails if anything runs it: under --no-deps an import would fail on numpy and requests.
        files = {**INSTALLED_METADATA, f"{DIST_NAME}/__init__.py": 'raise SystemExit("the post-install check ran the package")\n'}
        proc = _run_check(_post_install_check("publish.yml"), tmp_path, files)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout == f"TestPyPI install 1.2.3 package at {tmp_path / 'site' / DIST_NAME / '__init__.py'}\n"

    @pytest.mark.parametrize("optimize", [False, True], ids=["plain", "PYTHONOPTIMIZE"])
    @pytest.mark.parametrize("package_files", [{}, {f"{DIST_NAME}/README.txt": "not a package\n"}], ids=["no-package", "a-namespace-directory"])
    def test_the_post_install_check_refuses_a_wheel_that_lacks_the_package(self, tmp_path, optimize, package_files):
        # The metadata alone would pass a wheel that lacks the package: find_spec must find it, with an origin (a
        # directory without an __init__.py is a namespace package, which has none). The refusal is a SystemExit, which
        # -O (PYTHONOPTIMIZE) keeps, where it strips an assert statement.
        proc = _run_check(_post_install_check("publish.yml"), tmp_path, {**INSTALLED_METADATA, **package_files}, optimize=optimize)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert proc.stderr == f"the installed wheel holds no {DIST_NAME} package\n"
        # The line printed before the check says no "OK": the log of a refusal must not read as a pass.
        assert "OK" not in proc.stdout
        assert proc.stdout == "TestPyPI install 1.2.3 package at None\n"


class TestUnchanged:
    # The permissions are not here: they changed, and TestWiring pins them per job.
    def test_publish_yml_still_publishes_on_a_published_release_alone_without_concurrency(self):
        wf = _workflow("publish.yml")
        assert set(wf["on"]) == {"release", "workflow_dispatch"}
        assert wf["on"]["release"] == {"types": ["published"]}
        assert "concurrency" not in wf
        # The build carries juniper-cascor's release-convention guard. Every release of this repository is tagged
        # v<version>, and a dispatch has no release tag, so the republish dispatch builds nothing.
        assert wf["jobs"]["build"]["if"] == "startsWith(github.event.release.tag_name, 'v')"
        assert "if" not in wf["jobs"]["testpypi"]
        assert "if" not in wf["jobs"][INSTALL]
        assert "if" not in wf["jobs"]["pypi"]

    def test_publish_yml_builds_with_the_commands_and_the_python_it_used_before(self):
        build = _workflow("publish.yml")["jobs"]["build"]
        runs = [str(s.get("run") or "").strip() for s in build["steps"]]
        assert runs.index("pip install build twine") < runs.index("python -m build") < runs.index("twine check dist/*")
        setups = [s for s in build["steps"] if str(s.get("uses") or "").startswith("actions/setup-python@")]
        assert [s.get("with") for s in setups] == [{"python-version": "3.12"}]

    def test_the_install_job_runs_the_setup_and_the_install_check_the_testpypi_job_ran(self):
        job = _workflow("publish.yml")["jobs"][INSTALL]
        # The setup-python the TestPyPI job ran moved here with the install check, first; a sparse checkout of the
        # pyproject.toml the version is read from took the place of its full checkout.
        assert str(job["steps"][0].get("uses")).startswith("actions/setup-python@")
        assert job["steps"][0].get("with") == {"python-version": "3.12"}
        assert str(job["steps"][1].get("uses")).startswith("actions/checkout@")
        assert job["steps"][1].get("with") == {"sparse-checkout": "pyproject.toml\n", "persist-credentials": False}
        install = job["steps"][-1]
        assert install["name"] == "Verify TestPyPI install"
        run = install["run"]
        # The version comes from pyproject.toml, read by its path under the workspace, and pip reads TestPyPI alone, with
        # --no-deps (juniper-ml#384); the check reads the installed metadata and finds the package without importing it.
        assert """VERSION=$(python -c "import tomllib; print(tomllib.load(open('${GITHUB_WORKSPACE}/pyproject.toml','rb'))['project']['version'])")""" in run
        assert "--no-deps" in run
        assert "--index-url https://test.pypi.org/simple/" in run
        assert f'"{PACKAGE}==${{VERSION}}"' in run
        assert "extra-index-url" not in run
        assert f"m.version('{PACKAGE}')" in run
        assert f"u.find_spec('{DIST_NAME}')" in run


class TestExactly:
    """What the order and key checks above would let through: an extra step, a failure let pass, an install check that
    cannot fail, an upload input misspelled or turned off."""

    def test_each_job_runs_exactly_these_steps_in_this_order(self):
        # As (name, action): a named step that used another action, a rebuild slipped into a publish job, or a step that
        # writes into the dist directory before Record SHA256SUMS each fails here.
        jobs = _workflow("publish.yml")["jobs"]
        assert {job_id: _steps(job) for job_id, job in jobs.items()} == STEPS

    def test_no_job_and_no_step_lets_a_failure_pass(self):
        # A job or step that continues on error is a check that no longer blocks, and an if: can skip one. The build and
        # republish jobs' own if: are pinned to their exact text elsewhere; no other job may carry one (`always()` on the
        # PyPI job would publish after a failed install check), and no step an if: but its listed one (_allowed_if).
        for job_id, job in _workflow("publish.yml")["jobs"].items():
            assert "continue-on-error" not in job, f"job {job_id} sets continue-on-error"
            if job_id not in ("build", REPUBLISH):
                assert "if" not in job, f"job {job_id} carries if: {job.get('if')!r}"
            for index, step in enumerate(job.get("steps") or []):
                label = f"{job_id}: {step.get('name') or step.get('uses')}"
                assert "continue-on-error" not in step, f"{label} sets continue-on-error"
                assert step.get("if") == _allowed_if(job_id, index, step), f"{label} carries if: {step.get('if')!r}"

    def test_the_install_check_runs_exactly_this(self):
        assert _step(_workflow("publish.yml")["jobs"][INSTALL], INSTALL_STEPS["publish.yml"]) == {"name": INSTALL_STEPS["publish.yml"], "run": INSTALL_CHECK_RUN}

    def test_the_uploads_take_exactly_these_inputs(self):
        jobs = _workflow("publish.yml")["jobs"]
        inputs = tuple(jobs[job_id]["steps"][_uploads(jobs[job_id])[0]].get("with") for job_id in ("testpypi", "pypi"))
        assert inputs == UPLOAD_INPUTS


class TestTemplate:
    def test_every_copy_of_a_template_step_is_byte_identical(self):
        copies: dict[str, list[str]] = {REUSE: [], RECORD: [], VERIFY_DIST: [], "index": [], FIND: [], FETCH: []}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    kind = "index" if step.get("name") in INDEX_CHECKS else step.get("name")
                    if kind in copies:
                        assert step.get("shell") == "python3 {0}"
                        copies[kind].append(step["run"])
        # Per workflow: one reuse step and one record step; a dist check before each of three uploads; three JSON checks
        # in the release jobs and one in the republish job; one of each republish step.
        assert {kind: len(runs) for kind, runs in copies.items()} == {REUSE: 1, RECORD: 1, VERIFY_DIST: 3, "index": 4, FIND: 1, FETCH: 1}
        assert {kind: len(set(runs)) for kind, runs in copies.items()} == {REUSE: 1, RECORD: 1, VERIFY_DIST: 1, "index": 1, FIND: 1, FETCH: 1}

    def test_every_template_block_is_juniper_cascors_byte_for_byte(self):
        # One publisher here, so the copies above cannot drift apart from each other unseen, but they could drift from
        # the template together: each block, comments included, must hash to juniper-cascor's, byte for byte once each
        # `uses:` line is reduced to its action's name (_normalized), so a Dependabot bump of an action's pin needs no
        # re-port. test_each_action_is_pinned_to_one_ref_in_every_publisher holds each action to one ref.
        text = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
        assert {key: _sha(_normalized(block).encode("utf-8")) for key, block in _template_blocks(text).items()} == CASCOR_TEMPLATE_SHA256, f"a template block differs from {TEMPLATE_SOURCE}"

    def test_the_republish_job_is_juniper_cascors_byte_for_byte(self):
        text = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
        assert _sha(_normalized(_republish_job(text)).encode("utf-8")) == CASCOR_REPUBLISH_SHA256, f"the republish job differs from {TEMPLATE_SOURCE}"

    def test_the_digests_drop_an_actions_ref_and_nothing_else(self):
        # The normalization the two cases above hash through: a Dependabot bump (a new SHA and its # vX.Y.Z) leaves a
        # block's normalized text as it was, and any other edit, its retention say, changes it.
        block = _template_blocks((WORKFLOWS / "publish.yml").read_text(encoding="utf-8"))["build/Upload dist artifacts"]
        bumped = re.sub(r"(uses: actions/upload-artifact@)[0-9a-f]{40}  # v[0-9.]+", r"\g<1>" + "f" * 40 + "  # v99.0.0", block)
        assert bumped != block
        assert _normalized(bumped) == _normalized(block)
        assert "        uses: actions/upload-artifact\n" in _normalized(block)
        assert _normalized(block.replace("retention-days: 90", "retention-days: 30")) != _normalized(block)

    def test_each_action_is_pinned_to_one_ref_in_every_publisher(self):
        # Dependabot bumps an action in every copy in a file at once; a hand edit that bumps one copy fails here.
        refs: dict[str, set[str]] = {}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    if step.get("uses"):
                        name, _, ref = str(step["uses"]).partition("@")
                        refs.setdefault(name, set()).add(ref)
        assert {name: len(found) for name, found in refs.items()} == dict.fromkeys(refs, 1), refs

    def test_the_template_reads_nothing_but_its_parameters(self):
        for kind, run in _template_scripts().items():
            assert "${{" not in run, f"{kind}: an expression would tie the step to one workflow"
            read = set(re.findall(r"os\.environ(?:\.get\(|\[)[\"']([A-Z_]+)[\"']", run))
            assert read, kind
            assert read <= TEMPLATE_ENV, f"{kind} reads {sorted(read - TEMPLATE_ENV)}"

    def test_the_json_check_polls_a_bounded_number_of_times(self):
        run = _template_scripts()["index"]
        attempts = re.search(r'"HASH_CHECK_ATTEMPTS", "(\d+)"', run)
        interval = re.search(r'"HASH_CHECK_INTERVAL", "(\d+(?:\.\d+)?)"', run)
        assert attempts and interval
        # Long enough for a CDN to catch up after an upload, and bounded; each request is bounded too.
        assert 60 <= int(attempts.group(1)) * float(interval.group(1)) <= 900
        assert "urllib.request.urlopen(request, timeout=30)" in run
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    assert not {"HASH_CHECK_ATTEMPTS", "HASH_CHECK_INTERVAL"} & set(step.get("env") or {}), f"{workflow}: {step.get('name')} overrides the bounds"


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Rehearsals: the template steps' own Python, run as the runner runs it
# ─────────────────────────────────────────────────────────────────────────────────────────────
class TestRecordSha256sums:
    def test_it_hashes_every_distribution_in_sha256sum_format(self, workspace, tmp_path):
        proc = _run(_script(RECORD, tmp_path), workspace)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (workspace / "SHA256SUMS").read_text(encoding="utf-8") == "".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items()))

    def test_sha256sum_checks_what_it_writes(self, workspace, tmp_path):
        binary = shutil.which("sha256sum")
        if binary is None:
            pytest.skip("no sha256sum on PATH")
        assert _run(_script(RECORD, tmp_path), workspace).returncode == 0
        check = subprocess.run([binary, "--check", "--strict", str(workspace / "SHA256SUMS")], cwd=workspace / "dist", capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv
        assert check.returncode == 0, check.stdout + check.stderr

    @pytest.mark.parametrize("stray", ["notes.txt", f"{DIST_NAME}-9.9.9.zip"])
    def test_it_refuses_anything_but_wheels_and_sdists(self, workspace, tmp_path, stray):
        (workspace / "dist" / stray).write_bytes(b"x")
        proc = _run(_script(RECORD, tmp_path), workspace)
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert not (workspace / "SHA256SUMS").exists()

    def test_it_refuses_an_empty_or_a_missing_dist_directory(self, tmp_path):
        root = tmp_path / "empty"
        (root / "dist").mkdir(parents=True)
        script = _script(RECORD, tmp_path)
        assert _run(script, root).returncode == 1
        assert _run(script, root, PUBLISH_DIST_DIR="nowhere").returncode == 1

    def test_it_leaves_out_dotfiles_as_the_upload_does(self, workspace, tmp_path):
        (workspace / "dist" / ".gitignore").write_text("*\n", encoding="utf-8")
        assert _run(_script(RECORD, tmp_path), workspace).returncode == 0
        assert ".gitignore" not in (workspace / "SHA256SUMS").read_text(encoding="utf-8")

    def test_a_nested_dist_directory_resolves_from_the_workspace_not_the_working_directory(self, tmp_path):
        # The template's other layout: juniper-cascor's sub-package publishers build in the package directory
        # (defaults.run.working-directory) and set PUBLISH_DIST_DIR to <package>/dist.
        root = tmp_path / "workspace"
        package_dir = root / "juniper-cascor-model"
        (package_dir / "dist").mkdir(parents=True)
        (package_dir / "dist" / "juniper_cascor_model-1.0.0-py3-none-any.whl").write_bytes(b"model wheel")
        proc = _run(_script(RECORD, tmp_path), root, cwd=package_dir, PUBLISH_PACKAGE="juniper-cascor-model", PUBLISH_DIST_DIR="juniper-cascor-model/dist")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (root / "SHA256SUMS").read_text(encoding="utf-8") == f"{_sha(b'model wheel')}  juniper_cascor_model-1.0.0-py3-none-any.whl\n"


class TestVerifyDist:
    @staticmethod
    def _recorded(workspace: Path, tmp_path: Path) -> Path:
        assert _run(_script(RECORD, tmp_path), workspace).returncode == 0
        return _script(VERIFY_DIST, tmp_path)

    def test_it_passes_on_the_files_the_build_recorded(self, workspace, tmp_path):
        proc = _run(self._recorded(workspace, tmp_path), workspace)
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_it_ignores_dotfiles_as_the_upload_does(self, workspace, tmp_path):
        script = self._recorded(workspace, tmp_path)
        (workspace / "dist" / ".gitignore").write_text("*\n", encoding="utf-8")
        proc = _run(script, workspace)
        assert proc.returncode == 0, proc.stdout + proc.stderr

    def test_it_fails_when_a_file_changed(self, workspace, tmp_path):
        script = self._recorded(workspace, tmp_path)
        (workspace / "dist" / WHEEL).write_bytes(b"another build")
        assert _run(script, workspace).returncode == 1

    def test_it_fails_on_a_file_the_build_did_not_record(self, workspace, tmp_path):
        script = self._recorded(workspace, tmp_path)
        (workspace / "dist" / f"{DIST_NAME}-9.9.9-py2.py3-none-any.whl").write_bytes(b"x")
        assert _run(script, workspace).returncode == 1

    def test_it_fails_when_a_recorded_file_is_missing(self, workspace, tmp_path):
        script = self._recorded(workspace, tmp_path)
        (workspace / "dist" / SDIST).unlink()
        assert _run(script, workspace).returncode == 1

    @pytest.mark.parametrize(
        "sums",
        ["", f"nothex  {WHEEL}\n", f"{'a' * 64} {WHEEL}\n", f"{'a' * 64}  {WHEEL}\n{'a' * 64}  {WHEEL}\n"],
        ids=["empty", "not-a-sha256", "one-space", "listed-twice"],
    )
    def test_it_fails_on_a_sha256sums_it_cannot_read(self, workspace, tmp_path, sums):
        (workspace / "SHA256SUMS").write_text(sums, encoding="utf-8")
        assert _run(_script(VERIFY_DIST, tmp_path), workspace).returncode == 1


class TestIndexCheck:
    @staticmethod
    def _ready(workspace: Path, tmp_path: Path) -> Path:
        assert _run(_script(RECORD, tmp_path), workspace).returncode == 0
        return _script("index", tmp_path)

    @staticmethod
    def _check(script: Path, workspace: Path, server: _Stand, attempts: int = 4) -> subprocess.CompletedProcess[str]:
        return _run(script, workspace, INDEX_URL=server.url, HASH_CHECK_ATTEMPTS=str(attempts), HASH_CHECK_INTERVAL="0")

    def test_an_exact_match_passes_at_the_first_answer(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, _release(SERVED))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert server.paths() == [JSON_PATH]

    def test_it_polls_through_a_version_the_index_does_not_serve_yet(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [NOT_FOUND, NOT_FOUND, (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert len(server.paths()) == 3

    def test_it_polls_through_a_file_the_index_does_not_list_yet(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, _release({WHEEL: SERVED[WHEEL]})), (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert len(server.paths()) == 2

    def test_it_polls_through_an_answer_it_cannot_read(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, b"<html>busy</html>"), (503, b""), (200, {"info": {}}), (200, _release(SERVED))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server, attempts=5)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert len(server.paths()) == 4

    def test_an_index_that_lists_no_files_never_passes(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, _release({}))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server, attempts=3)
        assert proc.returncode == 1
        assert "after 3 attempts" in proc.stdout
        assert len(server.paths()) == 3

    def test_a_file_with_another_sha256_fails_at_once(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, _release({**SERVED, WHEEL: _sha(b"another build")}))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert len(server.paths()) == 1

    def test_a_file_this_run_did_not_build_fails_at_once(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [(200, _release({**SERVED, f"{DIST_NAME}-9.9.9-py2.py3-none-any.whl": "b" * 64}))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 1
        assert len(server.paths()) == 1

    def test_it_gives_up_after_its_bounded_attempts(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [NOT_FOUND]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server, attempts=3)
        assert proc.returncode == 1
        assert "after 3 attempts" in proc.stdout
        assert len(server.paths()) == 3

    @pytest.mark.parametrize("extra", [f"{OTHER_DIST_NAME}-9.9.9-py3-none-any.whl", f"{DIST_NAME}-9.9.8.tar.gz", f"{DIST_NAME}-9.9.9.zip"], ids=["another-package", "another-version", "not-a-distribution"])
    def test_it_refuses_a_sha256sums_it_cannot_vouch_for_before_asking_the_index(self, workspace, tmp_path, stand, extra):
        script = self._ready(workspace, tmp_path)
        with (workspace / "SHA256SUMS").open("a", encoding="utf-8") as sums:
            sums.write(f"{'c' * 64}  {extra}\n")
        server = stand({JSON_PATH: [(200, _release(SERVED))]})
        proc = self._check(script, workspace, server)
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert server.paths() == []


def _github_env(tmp_path: Path, server: _Stand, **extra: str) -> dict[str, str]:
    output = tmp_path / "github_output"
    output.touch()
    env = {"GITHUB_API_URL": server.url, "GITHUB_REPOSITORY": REPOSITORY, API_CREDENTIAL_ENV: FAKE_API_CREDENTIAL, "GITHUB_OUTPUT": str(output)}
    env.update(extra)
    return env


def _outputs(tmp_path: Path) -> dict[str, str]:
    text = (tmp_path / "github_output").read_text(encoding="utf-8")
    return dict(line.split("=", 1) for line in text.splitlines() if line)


RUN_ARTIFACTS = f"/repos/{REPOSITORY}/actions/runs/4242/artifacts?name={ARTIFACT_NAME}&per_page=100"


class TestReuseStep:
    @staticmethod
    def _env(tmp_path: Path, server: _Stand) -> dict[str, str]:
        return _github_env(tmp_path, server, GITHUB_RUN_ID="4242", GITHUB_RUN_ATTEMPT="2")

    def test_an_unexpired_artifact_from_an_earlier_attempt_is_reused(self, workspace, tmp_path, stand):
        server = stand({RUN_ARTIFACTS: [(200, {"artifacts": [{"id": 7, "name": ARTIFACT_NAME, "expired": False}]})]})
        proc = _run(_script(REUSE, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"reuse": "true"}
        path, headers = server.requests[0]
        assert path == RUN_ARTIFACTS
        assert headers.get("Authorization") == f"Bearer {FAKE_API_CREDENTIAL}"

    @pytest.mark.parametrize(
        "artifacts",
        [[], [{"id": 7, "name": ARTIFACT_NAME, "expired": True}], [{"id": 8, "name": "coverage-report", "expired": False}]],
        ids=["none", "expired", "another-name"],
    )
    def test_without_a_usable_artifact_the_attempt_builds(self, workspace, tmp_path, stand, artifacts):
        server = stand({RUN_ARTIFACTS: [(200, {"artifacts": artifacts})]})
        proc = _run(_script(REUSE, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {}

    def test_an_api_failure_fails_the_job_rather_than_rebuild(self, workspace, tmp_path, stand):
        server = stand({RUN_ARTIFACTS: [(500, {"message": "boom"})]})
        proc = _run(_script(REUSE, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode != 0
        assert _outputs(tmp_path) == {}


def _runs_path(tag: str, workflow: str = "publish.yml") -> str:
    return f"/repos/{REPOSITORY}/actions/workflows/{workflow}/runs?event=release&branch={tag}&per_page=30"


def _artifacts_path(run_id: int, package: str = PACKAGE) -> str:
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


LIVE_ARTIFACT = [{"id": 7, "name": ARTIFACT_NAME, "expired": False}]


class TestFindReleaseRun:
    @staticmethod
    def _env(tmp_path: Path, server: _Stand, tag: str = "v9.9.9", ref_type: str = "tag", workflow: str = "publish.yml") -> dict[str, str]:
        return _github_env(tmp_path, server, GITHUB_REF_NAME=tag, GITHUB_REF_TYPE=ref_type, GITHUB_REF=f"refs/{'tags' if ref_type == 'tag' else 'heads'}/{tag}", GITHUB_WORKFLOW_REF=f"{REPOSITORY}/.github/workflows/{workflow}@refs/tags/{tag}")

    @staticmethod
    def _serve(stand, jobs: list[dict], artifacts: list[dict] | None = None, tag: str = "v9.9.9", workflow: str = "publish.yml", package: str = PACKAGE) -> _Stand:
        """The stand-in GitHub API for TAG's one release run, 4242: its job records and its artifacts."""
        return stand(
            {
                _runs_path(tag, workflow): [(200, {"workflow_runs": [{"id": 4242, "head_branch": tag}]})],
                _jobs_path(4242): [_listing(*jobs)],
                _artifacts_path(4242, package): [(200, {"artifacts": LIVE_ARTIFACT if artifacts is None else artifacts})],
            }
        )

    def test_the_newest_release_run_is_the_one_checked_and_its_artifact_is_found(self, workspace, tmp_path, stand):
        runs = [{"id": 111, "head_branch": "v9.9.9"}, {"id": 333, "head_branch": "v9.9.9"}, {"id": 222, "head_branch": "v9.9.9"}, {"id": 444, "head_branch": "v9.9.99"}]
        server = stand({_runs_path("v9.9.9"): [(200, {"workflow_runs": runs})], _jobs_path(333): [_listing(*_attempt(1, 100))], _artifacts_path(333): [(200, {"artifacts": LIVE_ARTIFACT})]})
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "333"}
        # The newest run of THIS tag, whether or not it still holds its artifact: never an older run, nor another tag's.
        assert server.paths() == [_runs_path("v9.9.9"), _jobs_path(333), _artifacts_path(333)]
        assert all(headers.get("Authorization") == f"Bearer {FAKE_API_CREDENTIAL}" for _, headers in server.requests)

    def test_a_release_run_whose_artifact_expired_is_still_checked_and_testpypi_is_the_only_record(self, workspace, tmp_path, stand):
        server = self._serve(stand, _attempt(1, 100), artifacts=[{"id": 7, "name": ARTIFACT_NAME, "expired": True}])
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": ""}
        assert "::warning::" in proc.stdout

    def test_without_a_release_run_for_the_tag_nothing_is_republished(self, workspace, tmp_path, stand):
        server = stand({_runs_path("v9.9.9"): [(200, {"workflow_runs": [{"id": 5, "head_branch": "v9.9.99"}]})]})
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert "no release run for v9.9.9" in proc.stdout
        assert server.paths() == [_runs_path("v9.9.9")]
        assert _outputs(tmp_path) == {}

    @pytest.mark.parametrize(
        ("testpypi", "install"),
        [("failure", "skipped"), ("success", "failure"), ("cancelled", "skipped"), ("success", None)],
        ids=["the-upload-failed", "the-install-check-failed", "the-upload-was-cancelled", "the-install-check-still-runs"],
    )
    def test_a_release_run_whose_testpypi_jobs_did_not_both_pass_is_refused(self, workspace, tmp_path, stand, testpypi, install):
        server = self._serve(stand, _attempt(1, 100, testpypi=testpypi, install=install))
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        # Each TestPyPI job is named with its conclusion, or with its status while it has none.
        assert f"  Publish to TestPyPI: {testpypi} (attempt 1)" in proc.stdout
        assert f"  {INSTALL_NAME}: {install or 'in_progress'} (attempt 1)" in proc.stdout
        assert _artifacts_path(4242) not in server.paths()
        assert _outputs(tmp_path) == {}

    def test_a_job_that_re_run_failed_jobs_carried_over_counts_with_its_earlier_success(self, workspace, tmp_path, stand):
        # Attempt 1 passed both TestPyPI jobs and failed at PyPI; "Re-run failed jobs" ran the PyPI job alone again. This
        # listing leaves out the copies GitHub makes of the jobs it carries over (the next case has them): neither TestPyPI
        # job has a record of attempt 2, and each still counts with its earlier success.
        server = self._serve(stand, _attempt(1, 100) + [_job(203, "Publish to PyPI", "failure", attempt=2)])
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "4242"}

    @pytest.mark.parametrize(("install", "passes"), [("success", True), ("failure", False)], ids=["the-re-run-install-check-passed", "it-failed-again"])
    def test_re_run_failed_jobs_copies_the_jobs_it_carries_over_into_the_new_attempt(self, workspace, tmp_path, stand, install, passes):
        # As GitHub lists it (juniper-canopy run 43135960676): attempt 1's install check failed on lag, and "Re-run failed
        # jobs" gave EVERY job a record in attempt 2, the build and the upload as copies (a new id, run_attempt 2, attempt
        # 1's conclusion), the install check and the PyPI job as new runs.
        first = _attempt(1, 100, install="failure", pypi="skipped")
        second = _attempt(2, 200, install=install, pypi="failure" if passes else "skipped")
        server = self._serve(stand, first + second)
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        if passes:
            assert proc.returncode == 0, proc.stdout + proc.stderr
            assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "4242"}
            assert "release run 4242: Publish to TestPyPI concluded success in the latest attempt (2)" in proc.stdout
            assert f"release run 4242: {INSTALL_NAME} concluded success in the latest attempt (2)" in proc.stdout
        else:
            assert proc.returncode == 1
            assert f"  {INSTALL_NAME}: failure (attempt 2)" in proc.stdout
            assert _outputs(tmp_path) == {}

    @pytest.mark.parametrize("newest_first", [False, True], ids=["oldest-first", "newest-first"])
    @pytest.mark.parametrize(("first", "second", "passes"), [("success", "failure", False), ("failure", "success", True)], ids=["the-second-attempt-failed", "the-second-attempt-passed"])
    def test_the_highest_attempt_wins_in_whatever_order_the_listing_gives(self, workspace, tmp_path, stand, newest_first, first, second, passes):
        # GitHub does not document the order of filter=all: the step takes each job's record with the highest
        # (run_attempt, id), not the first or the last one listed.
        records = _attempt(1, 100, testpypi=first, install="success" if first == "success" else "skipped", pypi="skipped") + _attempt(2, 200, testpypi=second, install="success" if second == "success" else "skipped", pypi="skipped")
        server = self._serve(stand, list(reversed(records)) if newest_first else records)
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert (proc.returncode == 0) is passes, proc.stdout + proc.stderr
        if not passes:
            assert "  Publish to TestPyPI: failure (attempt 2)" in proc.stdout

    def test_a_release_run_whose_build_failed_so_both_testpypi_jobs_were_skipped_is_refused(self, workspace, tmp_path, stand):
        # A skipped TestPyPI job never ran its check. GitHub records it as completed, with the conclusion "skipped".
        records = [_job(100, "Build and Validate", "failure"), _job(101, "Publish to TestPyPI", "skipped"), _job(102, INSTALL_NAME, "skipped"), _job(103, "Publish to PyPI", "skipped"), _job(104, REPUBLISH_NAME, "skipped")]
        server = self._serve(stand, records)
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "  Publish to TestPyPI: skipped (attempt 1)" in proc.stdout
        assert f"  {INSTALL_NAME}: skipped (attempt 1)" in proc.stdout
        assert _outputs(tmp_path) == {}

    def test_an_older_release_run_that_passed_does_not_vouch_for_a_newer_one_that_failed(self, workspace, tmp_path, stand):
        # Ruling 1 reads the tag's NEWEST release run: a Release published again starts another run, which TestPyPI then
        # refuses, and from then on the tag has no run that vouches for its files.
        runs = [{"id": 4243, "head_branch": "v9.9.9"}, {"id": 4242, "head_branch": "v9.9.9"}]
        server = stand(
            {
                _runs_path("v9.9.9"): [(200, {"workflow_runs": runs})],
                _jobs_path(4243): [_listing(*_attempt(1, 300, testpypi="failure", install="skipped", pypi="skipped"))],
                _jobs_path(4242): [_listing(*_attempt(1, 100))],
                _artifacts_path(4242): [(200, {"artifacts": LIVE_ARTIFACT})],
            }
        )
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "  Publish to TestPyPI: failure (attempt 1)" in proc.stdout
        assert _jobs_path(4242) not in server.paths()
        assert _outputs(tmp_path) == {}

    def test_a_testpypi_job_that_failed_and_then_passed_on_a_re_run_counts_as_passed(self, workspace, tmp_path, stand):
        rerun = [_job(201, "Publish to TestPyPI", "success", attempt=2), _job(202, INSTALL_NAME, "success", attempt=2), _job(203, "Publish to PyPI", "failure", attempt=2)]
        server = self._serve(stand, _attempt(1, 100, testpypi="failure", install="skipped", pypi="skipped") + rerun)
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "4242"}

    def test_re_run_all_jobs_whose_second_attempt_failed_is_refused_although_the_first_passed(self, workspace, tmp_path, stand):
        server = self._serve(stand, _attempt(1, 100) + _attempt(2, 200, testpypi="failure", install="skipped", pypi="skipped"))
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "  Publish to TestPyPI: failure (attempt 2)" in proc.stdout
        assert _outputs(tmp_path) == {}

    def test_the_latest_attempt_is_read_across_every_page_of_the_listing(self, workspace, tmp_path, stand):
        # 105 records: 95 other jobs and attempt 1, whose upload failed, on page 1; attempt 2, all green, on page 2.
        page_1 = [_job(1000 + i, f"Unrelated job {i}", "success") for i in range(95)] + _attempt(1, 100, testpypi="failure", install="skipped", pypi="skipped")
        server = self._serve(stand, [])
        server.routes[_jobs_path(4242, 1)] = [_listing(*page_1, total=105)]
        server.routes[_jobs_path(4242, 2)] = [_listing(*_attempt(2, 200), total=105)]
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _jobs_path(4242, 2) in server.paths()
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "4242"}

    def test_a_release_run_without_a_testpypi_job_is_refused(self, workspace, tmp_path, stand):
        server = self._serve(stand, [_job(100, "Build and Validate", "success"), _job(101, "Publish to PyPI", "failure")])
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 1
        assert "the run has no such job" in proc.stdout
        assert _outputs(tmp_path) == {}

    def test_a_sub_package_tag_names_its_version(self, workspace, tmp_path, stand):
        # The template's other tag form, <package>-v<version>, which juniper-cascor's sub-package releases use.
        tag = "juniper-cascor-model-v1.2.3"
        server = self._serve(stand, _attempt(1, 100), artifacts=[], tag=tag, workflow="publish-cascor-model.yml", package="juniper-cascor-model")
        proc = _run(_script(FIND, tmp_path), workspace, PUBLISH_PACKAGE="juniper-cascor-model", PUBLISH_TAG_PREFIX="juniper-cascor-model-v", **self._env(tmp_path, server, tag=tag, workflow="publish-cascor-model.yml"))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "1.2.3", "run-id": ""}
        assert "::warning::" in proc.stdout

    @pytest.mark.parametrize(
        ("tag", "ref_type"),
        [("v9.9.9", "branch"), ("main", "branch"), ("juniper-cascor-model-v1.2.3", "tag"), ("juniper-data-client-v9.9.9", "tag"), ("v", "tag")],
        ids=["branch-named-like-a-tag", "branch", "another-packages-tag", "a-package-named-tag-in-a-single-package-publisher", "a-prefix-without-a-version"],
    )
    def test_it_refuses_anything_but_a_release_tag_of_this_package(self, workspace, tmp_path, stand, tag, ref_type):
        server = stand({})
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server, tag=tag, ref_type=ref_type))
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert server.requests == []
        assert _outputs(tmp_path) == {}

    @pytest.mark.parametrize("tag", ["v1.2.3", "juniper-cascor-protocol-v1.2.3", "juniper-cascor-model-1.2.3"], ids=["the-meta-packages-v-tag", "a-sibling-sub-packages-tag", "a-tag-without-the-v"])
    def test_a_sub_package_publisher_refuses_every_tag_but_its_own_prefix(self, workspace, tmp_path, stand, tag):
        # The template's step as a sub-package publisher runs it, with that publisher's parameters.
        server = stand({})
        proc = _run(_script(FIND, tmp_path), workspace, PUBLISH_PACKAGE="juniper-cascor-model", PUBLISH_TAG_PREFIX="juniper-cascor-model-v", **self._env(tmp_path, server, tag=tag, workflow="publish-cascor-model.yml"))
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        # Refused before any request: a sub-package's republish never reads the release run of another package's tag.
        assert server.requests == []
        assert _outputs(tmp_path) == {}

    @pytest.mark.parametrize("failing", ["runs", "jobs", "artifacts"])
    def test_an_api_failure_fails_the_job_rather_than_skip_the_check(self, workspace, tmp_path, stand, failing):
        server = self._serve(stand, _attempt(1, 100))
        server.routes[{"runs": _runs_path("v9.9.9"), "jobs": _jobs_path(4242), "artifacts": _artifacts_path(4242)}[failing]] = [(502, {"message": "bad gateway"})]
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode != 0
        assert _outputs(tmp_path) == {}


class TestFetchTestPyPIFiles:
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

    def _serve(self, stand, files: dict[str, bytes], digests: dict[str, str] | None = None) -> _Stand:
        server = stand({})
        server.routes.update(self._routes(server.url, files, digests))
        return server

    def test_it_downloads_testpypis_files_and_records_them(self, tmp_path, stand):
        root = tmp_path / "workspace"
        root.mkdir()
        server = self._serve(stand, BUILT)
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, tmp_path / "absent" / "SHA256SUMS"))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert {p.name: p.read_bytes() for p in (root / "dist").iterdir()} == BUILT
        assert (root / "SHA256SUMS").read_text(encoding="utf-8") == "".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items()))
        assert "::warning::" in proc.stdout

    def test_a_file_whose_bytes_differ_from_the_index_json_is_refused(self, tmp_path, stand):
        root = tmp_path / "workspace"
        root.mkdir()
        server = self._serve(stand, {**BUILT, WHEEL: b"tampered bytes"}, digests=SERVED)
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, tmp_path / "absent" / "SHA256SUMS"))
        assert proc.returncode == 1
        assert "hashes to" in proc.stdout
        assert not (root / "SHA256SUMS").exists()

    def test_the_release_runs_sha256sums_is_checked_while_it_exists(self, tmp_path, stand):
        root = tmp_path / "workspace"
        root.mkdir()
        sums = tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text("".join(f"{_sha(data)}  {name}\n" for name, data in sorted(BUILT.items())), encoding="utf-8")
        server = self._serve(stand, BUILT)
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, sums))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "::warning::" not in proc.stdout

    def test_testpypi_files_the_release_run_did_not_build_are_refused(self, tmp_path, stand):
        root = tmp_path / "workspace"
        root.mkdir()
        sums = tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text(f"{_sha(b'the first build')}  {WHEEL}\n{_sha(BUILT[SDIST])}  {SDIST}\n", encoding="utf-8")
        server = self._serve(stand, BUILT)
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, sums))
        assert proc.returncode == 1
        assert "disagree" in proc.stdout
        assert not [p for p, _ in server.requests if p.startswith("/files/")]

    @pytest.mark.parametrize("which", ["the-release-run-lists-more", "testpypi-lists-more"])
    def test_testpypi_and_the_release_runs_sha256sums_must_name_the_same_files(self, tmp_path, stand, which):
        # A file one of them names and the other does not is refused, in either direction, before any file is fetched.
        root = tmp_path / "workspace"
        root.mkdir()
        extra = f"{DIST_NAME}-9.9.9-py2.py3-none-any.whl"
        recorded = dict(SERVED) | ({extra: _sha(b"another wheel")} if which == "the-release-run-lists-more" else {})
        served = dict(BUILT) | ({extra: b"another wheel"} if which == "testpypi-lists-more" else {})
        sums = tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(recorded.items())), encoding="utf-8")
        server = self._serve(stand, served)
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, sums))
        assert proc.returncode == 1
        assert "disagree" in proc.stdout
        assert not [p for p, _ in server.requests if p.startswith("/files/")]

    @pytest.mark.parametrize(
        "listed",
        [{}, {**SERVED, f"{OTHER_DIST_NAME}-9.9.9-py3-none-any.whl": "d" * 64}, {**SERVED, f"{DIST_NAME}-9.9.8.tar.gz": "d" * 64}],
        ids=["no-files", "another-package", "another-version"],
    )
    def test_an_index_listing_it_cannot_vouch_for_is_refused(self, tmp_path, stand, listed):
        root = tmp_path / "workspace"
        root.mkdir()
        server = stand({})
        server.routes[JSON_PATH] = [(200, _release(listed, base=server.url))]
        proc = _run(_script(FETCH, tmp_path), root, **self._env(server, tmp_path / "absent" / "SHA256SUMS"))
        assert proc.returncode == 1
        assert "::error::" in proc.stdout
        assert not [p for p, _ in server.requests if p.startswith("/files/")]

    def test_it_refuses_a_dist_directory_that_already_holds_files(self, workspace, tmp_path, stand):
        server = self._serve(stand, BUILT)
        proc = _run(_script(FETCH, tmp_path), workspace, **self._env(server, tmp_path / "absent" / "SHA256SUMS"))
        assert proc.returncode == 1
        assert server.requests == []
'''
# END NEW_TEST


def apply(tree: Path, template: str, today: str) -> dict[str, str]:
    """Return {repo path: new text} for every file the port writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    if sha256(template) != TEMPLATE_SHA256:
        raise Refused(f"the template hashes to {sha256(template)}, not juniper-cascor f5ed3017's publish.yml: re-derive the port")
    out: dict[str, str] = {WORKFLOW_PATH: publish_workflow(read(WORKFLOW_PATH), template, today)}
    check_workflow(out[WORKFLOW_PATH])
    if not NEW_TEST:
        raise Refused("NEW_TEST is empty: splice the new test module in first")
    if sha256(read(TEST_PATH)) != BASE_TEST_SHA256:
        raise Refused(f"{TEST_PATH} hashes to {sha256(read(TEST_PATH))}, not the base NEW_TEST was derived from: re-derive the test port")
    out[TEST_PATH] = NEW_TEST
    if not DOCS_TEST:
        raise Refused("DOCS_TEST is empty: splice the new docs-bounds module in first")
    if (tree / DOCS_TEST_PATH).exists():
        raise Refused(f"{DOCS_TEST_PATH} exists already: this port creates it")
    out[DOCS_TEST_PATH] = DOCS_TEST
    for rel in (TEST_PATH, DOCS_TEST_PATH):
        try:
            ast.parse(out[rel])
        except SyntaxError as exc:
            raise Refused(f"{rel}: the new module does not parse: {exc}") from exc
    out[REFERENCE_PATH] = reference(read(REFERENCE_PATH), today)
    out[CHANGELOG_PATH] = changelog(read(CHANGELOG_PATH), CHANGELOG_ENTRY.replace("{cases}", TEST_CASES).replace("{mutations}", MUTATIONS))
    # The new text names no person: no file may name the person-word more often than before.
    grown = {rel: delta for rel, text in out.items() if (delta := sum(text.count(w) for w in WORDS) - sum((read(rel) if (tree / rel).exists() else "").count(w) for w in WORDS)) > 0}
    if grown:
        raise Refused(f"the new text names the person-word: {grown}")
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help=f"a fresh clone of {REPO}'s main (edited in place)")
    parser.add_argument("--template", type=Path, help="juniper-cascor's .github/workflows/publish.yml (default: <tree>/../juniper-cascor/.github/workflows/publish.yml)")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat(), help="the edited files' date, YYYY-MM-DD (default: today, UTC)")
    args = parser.parse_args(argv)
    try:
        datetime.date.fromisoformat(args.date)
    except ValueError:
        parser.error(f"--date {args.date!r} is not YYYY-MM-DD")
    template_path = args.template or args.tree.resolve().parent / "juniper-cascor" / ".github" / "workflows" / "publish.yml"
    try:
        out = apply(args.tree, template_path.read_text(encoding="utf-8"), args.date)
    except (Refused, OSError) as exc:
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
