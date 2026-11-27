#!/usr/bin/env python3
"""Port juniper-cascor's swept one-artifact publish template (juniper-cascor#777) to a fresh juniper-data tree, every edit an anchor asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the one-artifact template sweep's port to juniper-data; brief tmp/ports/SWEEP_PORT_BRIEF.md)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py (the template's own sweep, juniper-cascor#777: this
         writer's model); util/ad-hoc/2026-11-26_juniper-cascor-client_one_artifact_sweep_port.py (the sweep's first
         port, juniper-cascor-client#206, whose method and swept test this follows);
         util/ad-hoc/2026-11-15_juniper-data_one_artifact_publish_port.py (this repository's first port,
         juniper-data#543); util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker the result
         must pass); util/ad-hoc/2026-11-24_publish_port_install_pins.json (the pinned install scripts: this port
         proposes its own pin, the INSTALL_LINES below); util/open_signed_pr.py (uploads the files this writes, whole)

Why
---
juniper-cascor#777 swept the one-artifact template (rulings 1 and 2 of 2026-11-16, ``PUBLISH_TAG_PREFIX``, the
comment corrections and the test hardening), and every port copies the swept text. This gives juniper-data's
single-package ``publish.yml`` the same shape as juniper-cascor's, its ``notify-consumers`` job unchanged:

- ``.github/workflows/publish.yml``: the install check leaves ``Publish to TestPyPI`` for a job of its own,
  ``Verify the TestPyPI install`` (``needs: testpypi``, ``contents: read`` alone, its ``setup-python`` and its step,
  which reads the release's tag through ``env: RELEASE_TAG``, installs and imports from ``$RUNNER_TEMP``, retries the
  install with the template's loop and lag error, and checks the package with ``importlib.util.find_spec`` (R4-5));
  ``Publish to TestPyPI`` drops its checkout and ``setup-python`` and holds ``id-token: write`` alone; ``Publish to
  PyPI`` needs both; the workflow ``env`` gains ``PUBLISH_TAG_PREFIX: v``; the header, the ``permissions`` comment, the
  ``env`` comment and the build guard's comment (SWEEP item 12) follow the template. Every template block and the
  republish job are cut out of juniper-cascor's ``publish.yml`` (``--template``, pinned by sha256) and put in place of
  this file's, never retyped, then cut out of the result again and compared. ``notify-consumers`` (``needs: pypi``) and
  its comment are left byte for byte: a republish dispatch still skips it.
- ``juniper_data/tests/unit/test_publish_one_artifact.py``: written whole (``TEST_MODULE``): #777's hardening and
  rehearsals ported to this publisher. This repository's test pins each template step and the republish job by the
  sha256 of the PARSED step (``json.dumps``, ``sort_keys``), not of raw text; SWEEP item G / 23 is applied to that form:
  each ``uses:`` value is reduced to its action's name before hashing, so a Dependabot bump needs no re-port.
- ``juniper_data/tests/unit/test_publish_docs_bounds.py``: new (``DOCS_BOUNDS_TEST_MODULE``), the port of #777's
  ``src/tests/unit/test_publish_docs_bounds.py``: the numbers the docs state (the JSON checks' polls, interval and
  timeouts; the install check's tries, wait and first wait) read from ``publish.yml``. Written only where no such file
  exists.
- ``juniper_data/tests/unit/test_testpypi_install_verify.py``: written whole (``INSTALL_TEST_MODULE``): its rehearsal
  of the install step's own shell follows the step into its job, reads the tag through ``RELEASE_TAG`` and the retry.
- The docs that describe the pipeline (``docs/ci_cd/CICD_MANUAL.md``, ``CICD_REFERENCE.md``, ``CICD_QUICK_START.md``,
  ``docs/DEVELOPER_CHEATSHEET.md``, ``docs/REFERENCE.md``), each with its version's patch bump and its date, and
  ``CHANGELOG.md`` (one ``[Unreleased]`` / ``### Fixed`` entry).

Both test modules are written only over the base they were derived from (``BASE_*_SHA256``): a test file ``main`` has
moved is refused, never reverted. The person-word: each file's is read at run time ("Overtoad" or "owner", as
cascor's writer reads it), every anchor that holds it is built from that value, and the new text names no person.

    python3 -I util/ad-hoc/2026-11-26_juniper-data_one_artifact_sweep_port.py --tree <fresh clone> \\
        --changelog-cases N --changelog-mutations M \\
        [--template <juniper-cascor .github/workflows/publish.yml at 5e3d9801>] [--date YYYY-MM-DD]

``--changelog-cases`` and ``--changelog-mutations`` are required, as positive whole numbers (125 and 51 reproduce this
port's pull request), and the entry is refused while it still holds a placeholder. ``--date`` (default: today,
UTC) is the day the edited docs' dates take. Exit status: 0 when every edit applied; 1 when an anchor did not match
exactly once, an input moved, or a post-condition failed (nothing is written then); 2 on a usage error.

Review follow-up (2026-11-26, the second commit of juniper-data#553; its review's R-1, R-2, R-3 and R-6): two test
comments copied from other repositories now say what holds here (the install check "installs the package TestPyPI
serves and inspects it"; "this repository's root holds juniper_data/") (R-1); ``OTHER_DIST_NAME`` is used in the two
parametrizations that spelled it out (R-2); the base's stricter ``assert "concurrency" not in wf`` stands alone, and
``_cancels``, whose only call could not fail, goes (R-3); the CHANGELOG entry names #543's entry, two entries below
(R-6). R-4 and R-5 are left, as dispositioned. Re-running this on a fresh clone of the same base yields the pull
request's whole content, both commits.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

try:
    import yaml
except ImportError:  # the post-conditions parse the result; without PyYAML they cannot, so nothing is written
    yaml = None

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Repo-specific: juniper-data
# ─────────────────────────────────────────────────────────────────────────────────────────────
REPO = "juniper-data"
PACKAGE = "juniper-data"
MODULE = "juniper_data"
WORKFLOW_PATH = ".github/workflows/publish.yml"
NOTIFY_PATH = ".github/workflows/notify-consumers.yml"
TEST_PATH = "juniper_data/tests/unit/test_publish_one_artifact.py"
INSTALL_TEST_PATH = "juniper_data/tests/unit/test_testpypi_install_verify.py"
DOCS_BOUNDS_TEST_PATH = "juniper_data/tests/unit/test_publish_docs_bounds.py"
CHANGELOG_PATH = "CHANGELOG.md"
#: juniper-cascor's publish.yml at main 5e3d9801, byte-identical to #777's merge f5ed3017: the template.
TEMPLATE_DEFAULT = Path(__file__).resolve().parents[2] / "tmp" / "ports" / "clones" / "juniper-cascor" / ".github" / "workflows" / "publish.yml"
TEMPLATE_SHA256 = "b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b"
#: The base this was derived from: juniper-data main 8e08d209 (2026-11-24). publish.yml is edited by anchors and may
#: have moved (a note is printed); the test modules are written whole, so only over this exact base.
BASE_WORKFLOW_SHA256 = "19814549aecb76a6c3844616d2418366a963c639ee10af49ad7b79a5d9fac459"
BASE_TEST_SHA256 = "ede6ac01b6cc7c11dd4c18bf1dc743c7d2633244c51d6344093732a46995677c"
BASE_INSTALL_TEST_SHA256 = "da22feb800bcea98e92a1e1c77ff24722139cf709f530d37cc6b97c8f9ebae47"
#: notify-consumers.yml, which this port must not change (juniper-ml's cross-repo checker pins it).
NOTIFY_SHA256 = "e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078"
WORDS = ("Overtoad", "owner")
INSTALL_JOB = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
INSTALL_STEP = "Verify TestPyPI install"
LAG_ERROR = "is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"
#: The install step's script, line by line: the pin this port proposes for (juniper-data, publish.yml, "Verify TestPyPI
#: install") in util/ad-hoc/2026-11-24_publish_port_install_pins.json. The seed's text (the round-2 port simulation's:
#: cd to $RUNNER_TEMP, the tag through RELEASE_TAG, the 30 s wait, the template's retry loop and lag error), plus R4-5's
#: package check and the repository's own comments: the sys.path note of juniper-cascor's step, the security note this
#: step carried in the TestPyPI job (its last sentence now names the retry), the template's lag line, and this step's
#: python-dotenv note, extended to the package check.
INSTALL_LINES = [
    f"# `python -c` puts its working directory first on sys.path, and this repository's root holds {MODULE}/,",
    "# so an import run inside a checkout of it can pass without the wheel. This job checks nothing out, and it still",
    "# installs and imports from the runner's temporary directory, outside any checkout.",
    'cd "${RUNNER_TEMP}"',
    'VERSION="${RELEASE_TAG#v}"',
    "sleep 30",
    "# NOTE (security): install with --no-deps against TestPyPI only. Do NOT add a",
    "# production-PyPI fallback index here — with --no-deps no deps are fetched, so a",
    "# fallback only risks resolving a squatted target package. The sleep above, and the",
    "# retry below, cover TestPyPI index lag.",
    "# TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.",
    "for attempt in 1 2 3 4 5; do",
    "  if pip install \\",
    "    --no-deps \\",
    "    --index-url https://test.pypi.org/simple/ \\",
    f'    "{PACKAGE}==${{VERSION}}"; then',
    "    break",
    "  fi",
    '  if [ "${attempt}" -eq 5 ]; then',
    f'    echo "::error::{PACKAGE} ${{VERSION}} {LAG_ERROR}"',
    "    exit 1",
    "  fi",
    '  echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
    "  sleep 10",
    "done",
    f"# {MODULE} imports python-dotenv at import time, which is absent under --no-deps, so the",
    "# package cannot be imported here; verify the published artifact via its installed metadata,",
    f"# and that the wheel holds the package: find_spec locates {MODULE} without running it,",
    "# and a missing package, or a bare directory with no origin, fails the step through",
    "# SystemExit, which PYTHONOPTIMIZE keeps (it would strip an assert statement).",
    f"""python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{MODULE}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{PACKAGE}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {MODULE} package')\"""",
]
#: The seed pin (util/ad-hoc/2026-11-24_publish_port_install_pins.json): this port's text keeps every one of its
#: commands, in order (asserted below), and adds only the package check's find_spec and comments.
SEED_PIN_SHA256 = "3783295d154721cb31708337a2bcb99cb60657bdeff953a8689e26882f843d4f"

# ─────────────────────────────────────────────────────────────────────────────────────────────
# publish.yml: the anchors on this repository's base, and the text taken from the template
# ─────────────────────────────────────────────────────────────────────────────────────────────


def old_one_artifact_note(word: str) -> str:
    return "".join(
        (
            f"#    ONE ARTIFACT (the {word}'s directive of 2026-11-15; a port of juniper-cascor#763 and #767). The build job builds\n",
            "#    the sdist and wheel once, records their sha256 in SHA256SUMS and hands both publish jobs that one artifact.\n",
            "#    TestPyPI takes it first and must then serve exactly those sha256; PyPI takes it only after TestPyPI's JSON is\n",
            "#    checked again, and must serve them too. Until then each publish job ran its own `python -m build`, so PyPI served\n",
            "#    a second build of every release (the 0.17.1 wheel: cce2c167... on PyPI, 3b8f1a84... on TestPyPI). Uses OIDC\n",
            "#    trusted publishing (no API tokens); only the jobs that upload hold id-token: write.\n",
        )
    )


def new_one_artifact_note(word: str) -> str:
    """The same paragraph with the install job in the pipeline's description, wrapped as the header wraps (118 columns)."""
    text = " ".join(
        (
            f"ONE ARTIFACT (the {word}'s directive of 2026-11-15; a port of juniper-cascor#763 and #767, and of its sweep,",
            "juniper-cascor#777). The build job builds the sdist and wheel once, records their sha256 in SHA256SUMS and hands",
            "both publish jobs that one artifact. TestPyPI takes it first and must then serve exactly those sha256; a job that",
            "cannot mint a credential installs it from TestPyPI; and PyPI takes it only after that install passed and",
            "TestPyPI's JSON is checked again, and must serve them too. Until then each publish job ran its own",
            "`python -m build`, so PyPI served a second build of every release (the 0.17.1 wheel: cce2c167... on PyPI,",
            "3b8f1a84... on TestPyPI). Uses OIDC trusted publishing (no API tokens); only the jobs that upload hold",
            "id-token: write.",
        )
    )
    return wrap_header(text)


def wrap_header(text: str) -> str:
    """TEXT as the header's ``#    `` lines, none longer than 118 columns, never breaking inside a backtick span or
    inside "id-token: write"."""
    held = re.sub(r"`[^`]*`|id-token: write", lambda span: span.group(0).replace(" ", "\x00"), text)
    lines = textwrap.wrap(held, width=118 - 5, break_long_words=False, break_on_hyphens=False)
    return "".join(f"#    {line}\n".replace("\x00", " ") for line in lines)


OLD_PARAMETERS_NOTE = "#    verbatim: they read nothing from this repository but the two `env` values below. The republish job is step 1 of\n"
NEW_PARAMETERS_NOTE = "#    verbatim: they read nothing from this repository but the three `env` values below. The republish job is step 1 of\n"
OLD_PERMISSIONS_COMMENT = "# Each job states what it needs. Only the jobs that upload hold id-token: write, so the build cannot mint a credential.\npermissions: {}\n"
OLD_ENV = "".join(
    (
        "env:\n",
        "  # The one-artifact publish template's two parameters: the distribution's name on PyPI and TestPyPI,\n",
        "  # and the directory the build writes the sdist and wheel to, relative to the workspace.\n",
        f"  PUBLISH_PACKAGE: {PACKAGE}\n",
        "  PUBLISH_DIST_DIR: dist\n",
    )
)
OLD_GUARD_LINES = (
    "Release-convention guard: every juniper-data release is tagged v<version> (all 15 to 2026-11-15), and",
    "publish-image.yml applies the same guard to the same release event. A dispatch has no release tag, so the",
    "republish dispatch builds nothing. Both publish jobs depend on this one, so this guard gates the whole pipeline.",
)
OLD_GUARD = "".join(f"    # {line}\n" for line in OLD_GUARD_LINES)
GUARD_IF = "    if: startsWith(github.event.release.tag_name, 'v')\n"
#: The template's two sentences on rc*/hf* tags (SWEEP item 12), as its guard comment states them, whitespace aside;
#: asserted to be the template's before they are wrapped into this guard's comment.
GUARD_SENTENCES = " ".join(
    (
        "The publish environments also admit `rc*` and `hf*` tags, kept for future release-candidate and hotfix conventions",
        "(D2 of juniper-ml's notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md). This guard",
        "skips them: a convention that adopts one must widen it, and PUBLISH_TAG_PREFIX with it.",
    )
)
OLD_TESTPYPI_HEAD = "".join(
    (
        "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n",
        "    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n",
        '    steps:\n      - uses: {checkout}\n\n      - uses: {setup_python}\n        with:\n          python-version: "3.12"\n\n',
    )
)
OLD_INSTALL_STEP = "".join(
    (
        "      - name: Verify TestPyPI install\n",
        "        run: |\n",
        '          VERSION="${{ github.event.release.tag_name }}"\n',
        '          VERSION="${VERSION#v}"\n',
        "          sleep 30\n",
        "          # NOTE (security): install with --no-deps against TestPyPI only. Do NOT add a\n",
        "          # production-PyPI fallback index here — with --no-deps no deps are fetched, so a\n",
        "          # fallback only risks resolving a squatted target package. The sleep above covers\n",
        "          # TestPyPI index lag.\n",
        "          pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-data==${VERSION}\n",
        "          # Version-only check: juniper_data imports python-dotenv at import time, which is\n",
        "          # absent under --no-deps; verify the published artifact via its installed metadata.\n",
        "          python -c \"import importlib.metadata as m; print('TestPyPI OK: v' + m.version('juniper-data'))\"\n",
        "\n",
    )
)
OLD_PYPI_HEAD = "  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n"
#: notify-consumers, its comment included: left byte for byte (a republish dispatch still skips it).
NOTIFY_JOB_START = "  # After PyPI serves the release, tell the repos that install juniper-data from PyPI, so their\n"
NOTIFY_JOB = {
    "name": "Notify consumer repos",
    "needs": "pypi",
    "permissions": {},
    "uses": "./.github/workflows/notify-consumers.yml",
    "with": {"version": "${{ github.event.release.tag_name }}"},
    "secrets": {"CROSS_REPO_DISPATCH_TOKEN": "${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}"},
}
TEMPLATE_COMMENT = "      # One-artifact publish template"
STEP_LINE = re.compile(r"^      (?:- |# )")
JOB_LINE = re.compile(r"^  [a-z][a-z0-9-]*:\s*$")


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


def between(text: str, start: str, end: str, where: str) -> str:
    """The text from START (included) to END (excluded), each matching exactly once, START first."""
    for anchor in (start, end):
        if text.count(anchor) != 1:
            raise Refused(f"{where}: anchor matched {text.count(anchor)} times, expected 1: {anchor[:90]!r}")
    a, b = text.index(start), text.index(end)
    if a >= b:
        raise Refused(f"{where}: {start[:40]!r} does not come before {end[:40]!r}")
    return text[a:b]


def head_of(text: str, start: str, end: str, where: str) -> str:
    """The text from START (matching exactly once, included) to the first END after it (excluded)."""
    if text.count(start) != 1:
        raise Refused(f"{where}: anchor matched {text.count(start)} times, expected 1: {start[:90]!r}")
    a = text.index(start)
    b = text.find(end, a + len(start))
    if b < 0:
        raise Refused(f"{where}: nothing matches {end[:40]!r} after {start[:40]!r}")
    return text[a:b]


def detect_word(text: str, pattern: str, where: str) -> str:
    """The person-word TEXT uses in PATTERN (a format string with ``{word}``): exactly one of WORDS must fit."""
    found = [word for word in WORDS if pattern.format(word=word) in text]
    if len(found) != 1:
        raise Refused(f"{where}: {pattern!r} fits {found or 'neither'} of {WORDS}")
    return found[0]


def action_pin(text: str, action: str, where: str) -> str:
    """The one ``<action>@<sha>  # vX.Y.Z`` pin a workflow uses (Dependabot bumps every copy in a file together)."""
    pins = set(re.findall(rf"{re.escape(action)}@[0-9a-f]{{40}}  # v[0-9][0-9.]*", text))
    if len(pins) != 1:
        raise Refused(f"{where}: {len(pins)} distinct {action} pins, expected 1: {sorted(pins)}")
    return pins.pop()


def template_blocks(text: str, where: str) -> "list[tuple[str, int, int]]":
    """Each template block as (``<job>/<step name>``, first line, end line): from its "One-artifact publish template"
    comment to the end of its step, comments included."""
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


def block_texts(text: str, where: str) -> "dict[str, str]":
    lines = text.splitlines(keepends=True)
    return {key: "".join(lines[a:b]) for key, a, b in template_blocks(text, where)}


def republish_span(text: str, where: str) -> "tuple[int, int]":
    """The republish job's character span: from the comment banner above it to the end of the file, where it must be."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == "  republish:\n"]
    if len(at) != 1:
        raise Refused(f"{where}: {len(at)} republish jobs")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    if any(JOB_LINE.match(line) for line in lines[at[0] + 1 :]):
        raise Refused(f"{where}: the republish job is not the file's last job")
    return sum(len(line) for line in lines[:start]), len(text)


def notify_span(text: str, where: str) -> str:
    """notify-consumers, from its comment to the republish job's banner: the text this port must leave unchanged."""
    a = head_of(text, NOTIFY_JOB_START, "  # ═══", where)
    if "  notify-consumers:\n" not in a:
        raise Refused(f"{where}: no notify-consumers job after its comment")
    return a


def wrap_comment(text: str, indent: str, width: int) -> str:
    """TEXT as ``# `` comment lines at INDENT, none longer than WIDTH."""
    return "".join(f"{indent}# {line}\n" for line in textwrap.wrap(text, width=width - len(indent) - 2, break_long_words=False, break_on_hyphens=False))


def publish_workflow(text: str, template: str) -> str:
    """The new publish.yml: this repository's header, build commands, install check and notify-consumers, around the template's blocks."""
    where = WORKFLOW_PATH
    word = detect_word(text, "  # The {word}'s recovery ladder, step 1 (2026-11-15)", where)
    checkout = action_pin(text, "actions/checkout", where)
    setup_python = action_pin(text, "actions/setup-python", where)
    for action in ("actions/checkout", "actions/setup-python", "actions/upload-artifact", "actions/download-artifact", "pypa/gh-action-pypi-publish"):
        if action_pin(text, action, where) != action_pin(template, action, "the template"):
            raise Refused(f"{where}: {action} is pinned at another ref than the template's: re-port only after the refs agree")
    notify_before = notify_span(text, where)
    # The header: the install job in the pipeline's description, and the template's three parameters.
    text = replace_once(text, old_one_artifact_note(word), new_one_artifact_note(word), where)
    text = replace_once(text, OLD_PARAMETERS_NOTE, NEW_PARAMETERS_NOTE, where)
    # The permissions comment and the env block (its comment names the three parameters), taken from the template.
    text = replace_once(text, OLD_PERMISSIONS_COMMENT, between(template, "# Each job states what it needs.", "\nenv:\n", "the template"), where)
    env_comment = between(template, "env:\n  # The one-artifact publish template's three parameters", "  PUBLISH_PACKAGE: juniper-cascor\n", "the template")
    if "  PUBLISH_PACKAGE: juniper-cascor\n  PUBLISH_DIST_DIR: dist\n  PUBLISH_TAG_PREFIX: v\n" not in template:
        raise Refused("the template's env block moved")
    text = replace_once(text, OLD_ENV, env_comment + f"  PUBLISH_PACKAGE: {PACKAGE}\n  PUBLISH_DIST_DIR: dist\n  PUBLISH_TAG_PREFIX: v\n", where)
    # The build guard's comment gains the template's rc*/hf* note (item 12), checked against the template's words.
    guard_comment = between(template, "    # Release-convention guard: publish juniper-cascor only", GUARD_IF, "the template")
    if GUARD_SENTENCES not in " ".join(line.strip().lstrip("#").strip() for line in guard_comment.splitlines()):
        raise Refused("the template's guard comment no longer says GUARD_SENTENCES")
    old_text = " ".join(OLD_GUARD_LINES)
    text = replace_once(text, OLD_GUARD + GUARD_IF, wrap_comment(f"{old_text} {GUARD_SENTENCES}", "    ", 120) + GUARD_IF, where)
    # The TestPyPI job: the template's head (id-token: write alone), without the checkout and setup-python it ran.
    new_testpypi_head = head_of(template, "  testpypi:\n", "      # One-artifact publish template, step 3.", "the template")
    text = replace_once(text, OLD_TESTPYPI_HEAD.format(checkout=checkout, setup_python=setup_python), new_testpypi_head, where)
    # The install check leaves the TestPyPI job for its own, the template's job head and setup-python around it.
    text = replace_once(text, OLD_INSTALL_STEP, "", where)
    install_job = between(template, "  # Ruling 2 of 2026-11-16: the install check runs in a job of its own", "      - name: Verify TestPyPI install\n", "the template")
    release_tag_env = between(template, "        env:\n          # The tag reaches the script as a variable", "        run: |\n          # `python -c` puts its working directory first", "the template")
    install_step = "      - name: Verify TestPyPI install\n" + release_tag_env + "        run: |\n" + "".join(f"          {line}\n" for line in INSTALL_LINES) + "\n"
    text = replace_once(text, "\n" + OLD_PYPI_HEAD, "\n" + install_job + install_step + OLD_PYPI_HEAD.replace("needs: testpypi", f"needs: [testpypi, {INSTALL_JOB}]"), where)
    if f"    needs: [testpypi, {INSTALL_JOB}]\n" not in template:
        raise Refused("the template's PyPI job no longer needs both TestPyPI jobs")
    # Every template block and the republish job: the template's, in place of this file's.
    want = block_texts(template, "the template")
    have = template_blocks(text, where)
    if [key for key, _, _ in have] != list(want):
        raise Refused(f"{where}: its template blocks are {[key for key, _, _ in have]}, the template's {list(want)}")
    lines = text.splitlines(keepends=True)
    for key, a, b in reversed(have):
        lines[a:b] = [want[key]]
    text = "".join(lines)
    a, _ = republish_span(text, where)
    t, _ = republish_span(template, "the template")
    text = text[:a] + template[t:]
    # Post-conditions: the blocks and the republish job cut from the result are the template's; notify-consumers is
    # this file's, byte for byte.
    if block_texts(text, where) != want:
        raise Refused("a template block of the result differs from the template's")
    if text[republish_span(text, where)[0] :] != template[t:]:
        raise Refused("the result's republish job differs from the template's")
    if notify_span(text, where) != notify_before:
        raise Refused("notify-consumers changed")
    header = text[: text.index("\nname: Publish to PyPI\n")]
    if max(len(line) for line in header.splitlines() if line.startswith("#    ")) > 120:
        raise Refused("a header comment line is longer than 120 characters")
    return text


def check_workflow(text: str) -> None:
    """The result's shape, read as YAML: the jobs and their wiring, and the install step equal to INSTALL_LINES."""
    if yaml is None:
        raise Refused("PyYAML is not importable here, so the result cannot be checked: run with an interpreter that has it")
    wf = yaml.safe_load(text)
    jobs = wf["jobs"]
    if list(jobs) != ["build", "testpypi", INSTALL_JOB, "pypi", "notify-consumers", "republish"]:
        raise Refused(f"jobs {list(jobs)}")
    if wf["env"] != {"PUBLISH_PACKAGE": PACKAGE, "PUBLISH_DIST_DIR": "dist", "PUBLISH_TAG_PREFIX": "v"}:
        raise Refused(f"env {wf['env']}")
    install = jobs[INSTALL_JOB]
    checks = {
        "install job name": install.get("name") == INSTALL_NAME,
        "install job needs": install.get("needs") == "testpypi",
        "install job permissions": install.get("permissions") == {"contents": "read"},
        "install job keys": set(install) == {"name", "needs", "runs-on", "permissions", "steps"},
        "install step": [s.get("name") for s in install["steps"]] == [None, INSTALL_STEP],
        "install script": install["steps"][1].get("run") == "\n".join(INSTALL_LINES) + "\n",
        "install env": install["steps"][1].get("env") == {"RELEASE_TAG": "${{ github.event.release.tag_name }}"},
        "testpypi permissions": jobs["testpypi"].get("permissions") == {"id-token": "write"},
        "testpypi steps": [s.get("name") for s in jobs["testpypi"]["steps"]] == ["Download dist artifacts", "Verify the dist against SHA256SUMS", "Publish to TestPyPI", "Verify TestPyPI serves exactly these files"],
        "pypi needs": jobs["pypi"].get("needs") == ["testpypi", INSTALL_JOB],
        "notify-consumers": jobs["notify-consumers"] == NOTIFY_JOB,
        "build guard": jobs["build"].get("if") == "startsWith(github.event.release.tag_name, 'v')",
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise Refused(f"{WORKFLOW_PATH}: the result fails {failed}")


def check_install_lines() -> None:
    """INSTALL_LINES keep the seed pin's commands, in order, and add only the package check and comments."""
    commands = [line.strip() for line in INSTALL_LINES if not line.strip().startswith("#")]
    seed = [
        'cd "${RUNNER_TEMP}"',
        'VERSION="${RELEASE_TAG#v}"',
        "sleep 30",
        "for attempt in 1 2 3 4 5; do",
        "if pip install \\",
        "--no-deps \\",
        "--index-url https://test.pypi.org/simple/ \\",
        f'"{PACKAGE}==${{VERSION}}"; then',
        "break",
        "fi",
        'if [ "${attempt}" -eq 5 ]; then',
        f'echo "::error::{PACKAGE} ${{VERSION}} {LAG_ERROR}"',
        "exit 1",
        "fi",
        'echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
        "sleep 10",
        "done",
    ]
    if commands[: len(seed)] != seed or len(commands) != len(seed) + 1 or not commands[-1].startswith("python -c "):
        raise Refused("INSTALL_LINES no longer hold the seed pin's commands, in order, then the package check alone")
    if "|| true" in "\n".join(commands) or "assert " in commands[-1]:
        raise Refused("INSTALL_LINES let a failure pass")
    # The seed's own last command is the metadata check this replaces: its version lookup stays, with find_spec added.
    if f"m.version('{PACKAGE}')" not in commands[-1] or f"u.find_spec('{MODULE}')" not in commands[-1] or "raise SystemExit(0 if origin else " not in commands[-1]:
        raise Refused("the package check lost its version lookup, its find_spec or its SystemExit")


#: The template steps juniper_data/tests/unit/test_publish_one_artifact.py pins by digest, by name, with the constant
#: each is pinned under there; and the job whose whole digest it pins.
DIGEST_STEPS = {
    "REUSE": ("build", "Reuse an earlier attempt's artifact"),
    "RECORD": ("build", "Record SHA256SUMS"),
    "UPLOAD": ("build", "Upload dist artifacts"),
    "DOWNLOAD": ("testpypi", "Download dist artifacts"),
    "VERIFY_DIST": ("testpypi", "Verify the dist against SHA256SUMS"),
    "TESTPYPI_AFTER": ("testpypi", "Verify TestPyPI serves exactly these files"),
    "TESTPYPI_BEFORE": ("pypi", "Verify TestPyPI still serves exactly these files"),
    "PYPI_AFTER": ("pypi", "Verify PyPI serves exactly these files"),
}


def normalized_value(value: object) -> object:
    """A parsed step or job with every ``uses:`` reduced to its action's name (the test's ``_normalized``)."""
    if isinstance(value, dict):
        return {key: (str(item).split("@", 1)[0] if key == "uses" else normalized_value(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [normalized_value(item) for item in value]
    return value


def value_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(normalized_value(value), sort_keys=True).encode("utf-8")).hexdigest()


def template_digests(template: str) -> "dict[str, str]":
    """{constant: digest} for each step DIGEST_STEPS names, and REPUBLISH, read from the template as the test reads them;
    every copy of a step of that name in the template must give the same digest."""
    if yaml is None:
        raise Refused("PyYAML is not importable here, so the template's digests cannot be taken")
    jobs = yaml.safe_load(template)["jobs"]
    out: dict[str, str] = {}
    for constant, (job_id, name) in DIGEST_STEPS.items():
        copies = {value_digest(step) for job in jobs.values() for step in job.get("steps") or [] if step.get("name") == name}
        here = [value_digest(step) for step in jobs[job_id]["steps"] if step.get("name") == name]
        if len(copies) != 1 or len(here) != 1:
            raise Refused(f"the template's {name!r} copies give {len(copies)} digests ({len(here)} in {job_id})")
        out[constant] = here[0]
    out["REPUBLISH"] = value_digest(jobs["republish"])
    return out


def digest_lines(template: str) -> str:
    """The body of the test's TEMPLATE_SHA256, one ``    CONSTANT: "digest",`` line each."""
    return "".join(f'    {constant}: "{digest}",\n' for constant, digest in template_digests(template).items())


#: A ``uses:`` line: its prefix, the action's name, and the ``@ref`` with the ``# vX.Y.Z`` comment Dependabot moves with it.
USES_LINE = re.compile(r"^(\s*(?:- )?uses: )([^@\s]+)@\S+(?:\s+#\s*v\S*)?$")


def normalized_text(block: str) -> str:
    """BLOCK with every ``uses:`` line reduced to its action's name (the test's ``_normalized_text``, SWEEP item 23)."""
    return "".join(USES_LINE.sub(r"\1\2", line) + "\n" for line in block.splitlines())


def check_test_digests(test_text: str, template: str) -> None:
    """The digests TEST_MODULE pins are the template's: each parsed step normalized (TEMPLATE_SHA256), and each block's
    text and the republish job's text normalized (CASCOR_TEMPLATE_SHA256, CASCOR_REPUBLISH_SHA256)."""
    pinned = dict(re.findall(r'^    ([A-Z_]+): "([0-9a-f]{64})",$', test_text, flags=re.MULTILINE))
    want = template_digests(template)
    if pinned != want:
        raise Refused(f"{TEST_PATH}: TEMPLATE_SHA256 is not the template's normalized digests: {sorted(set(pinned.items()) ^ set(want.items()))}")
    if 'TEMPLATE_COMMIT = "f5ed30177766"\n' not in test_text:
        raise Refused(f"{TEST_PATH}: TEMPLATE_COMMIT is not #777's merge")
    pinned_text = dict(re.findall(r'^    "([^"\n]+/[^"\n]+)": "([0-9a-f]{64})",$', test_text, flags=re.MULTILINE))
    want_text = {key: sha256(normalized_text(block)) for key, block in block_texts(template, "the template").items()}
    if pinned_text != want_text:
        raise Refused(f"{TEST_PATH}: CASCOR_TEMPLATE_SHA256 is not the template's normalized block digests: {sorted(set(pinned_text.items()) ^ set(want_text.items()))}")
    t, _ = republish_span(template, "the template")
    found = re.findall(r'^CASCOR_REPUBLISH_SHA256 = "([0-9a-f]{64})"$', test_text, flags=re.MULTILINE)
    if found != [sha256(normalized_text(template[t:].rstrip("\n") + "\n"))]:
        raise Refused(f"{TEST_PATH}: CASCOR_REPUBLISH_SHA256 is not the template's republish job's normalized digest")
#: The new juniper_data/tests/unit/test_publish_one_artifact.py, whole: this repository's test as juniper-data#543
#: left it, with juniper-cascor#777's hardening and rehearsals ported to this publisher (by way of
#: juniper-cascor-client#206's port) and the template digests pinned normalized (SWEEP item 23). Installed only over
#: BASE_TEST_SHA256.
TEST_MODULE = r'''"""Pin the one-artifact publish: PyPI takes exactly the files TestPyPI took, and the run checks it by sha256.

The Overtoad's directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to testpypi.
an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to
prevent this from slipping through the cracks again." ``publish.yml`` ran ``python -m build`` in its TestPyPI job and
again in its PyPI job, so PyPI served a second build of each release: the juniper-data 0.17.1 wheel is
``cce2c167...`` on PyPI and ``3b8f1a84...`` on TestPyPI, 0.17.0's ``680c37b5...`` against ``2842d5b1...``, and
0.16.0's ``8560d60c...`` against ``ead4708d...``.

``publish.yml`` now builds once and hands both publish jobs one artifact, the dist directory plus ``SHA256SUMS``. A
re-run attempt reuses that artifact rather than build again, because download-artifact takes the newest artifact of a
name. Only the jobs that upload hold ``id-token: write``. The install check runs in a job of its own, ``Verify the
TestPyPI install``, which cannot mint a credential, installs and checks the package from outside any checkout, and is
needed by the PyPI job (ruling 2 of 2026-11-16). A dispatch from the release tag runs the republish job, the first step
of the recovery ladder (ruling of 2026-11-15): it copies TestPyPI's files for the version to PyPI and builds nothing,
and it refuses unless the tag's newest release run passed its TestPyPI jobs in their latest attempt (ruling 1 of
2026-11-16). The steps are juniper-cascor's one-artifact publish template (juniper-cascor#763 and #767, swept by #777),
copied verbatim: they read only ``PUBLISH_PACKAGE``, ``PUBLISH_DIST_DIR`` and ``PUBLISH_TAG_PREFIX`` from the workflow
``env``, a step's ``INDEX_URL``, and the runner's own variables. ``notify-consumers`` still runs only after the PyPI job
of a release run.

The static cases pin the wiring: one build, in a job without an environment or ``id-token``; the job chain and the job
names juniper-ml's release-train ceremony and monitor read; per-job permissions; each job's keys, runner and exact
steps, in order, with no ``if:`` but the listed ones and no ``continue-on-error``; each build step's commands; the
reuse step first in the build job and guarding every later step; each upload preceded by the dist check; TestPyPI's
JSON checked after the TestPyPI upload and again before the PyPI one, and PyPI's after; no ``skip-existing`` and no
``attestations: false``; an artifact kept 90 days, past the 30-day ``pypi`` gate; the install check's job, its exact
script and commands, which cannot be switched off; the republish job's trigger, gate, steps and name; the triggers, the
build's tag guard and the tag prefix, and what the workflow kept; and every template step and the republish job equal
to juniper-cascor's ``publish.yml`` at TEMPLATE_COMMIT, the snapshot this port copied, each compared by the digest of
the parsed step and by the sha256 of its text, comments included, with every ``uses:`` reduced to its action's name,
while each action stays pinned to one ref. The
rehearsals run each template step's own Python, extracted from ``publish.yml``, in a scratch workspace, against a
stand-in index and a stand-in GitHub API on 127.0.0.1, the republish job's refusals among them, and the install check's
package check against a real interpreter (``test_testpypi_install_verify.py`` runs its shell).
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

# CI collects ``-m "unit and not slow"`` with ``--strict-markers`` and does not auto-mark, so an unmarked test is
# collected and then silently DESELECTED. Module-level, so it covers tests added later.
pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]
WORKFLOWS = REPO / ".github" / "workflows"
#: This repository's distribution, its file-name form, its import name, and another distribution whose name starts with this one's.
PACKAGE = "juniper-data"
DIST_NAME = "juniper_data"
MODULE = "juniper_data"
OTHER_DIST_NAME = "juniper_data_client"
#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build``, an install check and a ``republish`` job.
PUBLISHERS = {
    "publish.yml": (PACKAGE, "dist", "testpypi", "pypi"),
}
#: workflow -> its jobs that are neither the build, a publish job, the install check nor the republish job: here a call of a
#: reusable workflow, which runs no step of its own (TestUnchanged pins it whole).
OTHER_JOBS = {
    "publish.yml": ("notify-consumers",),
}
#: workflow -> (top-level permissions, the PyPI job's). The build, TestPyPI, install-check and republish jobs hold the same in every publisher.
PERMISSIONS: dict[str, tuple[dict[str, str], dict[str, str]]] = {
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
#: The template's sub-package build jobs carry a release-convention gate that runs on ``push`` alone, an event no
#: publisher subscribes to, so it never runs: it is the one build step exempt from the reuse condition, and it is exempt
#: by its name. This publisher has no such step, so here every build step after the first carries the reuse condition.
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
#: The juniper-cascor commit whose publish.yml this port copied: #777's merge, the template's sweep (juniper-cascor main
#: 5e3d9801 holds its publishers byte for byte).
TEMPLATE_COMMIT = "f5ed30177766"
#: sha256 of ``json.dumps(<parsed step>, sort_keys=True)`` for each template step, and of the whole republish job, in
#: juniper-cascor's publish.yml at TEMPLATE_COMMIT, each taken with every ``uses:`` reduced to its action's name, its
#: ``@ref`` dropped (SWEEP item 23): a Dependabot bump of an action, which moves every copy in a file at once, moves no
#: digest here, and TestTemplate pins each action to one ref across the file (juniper-ml's cross-repo checker pins every
#: ref to the template's). They are a snapshot: a template change in juniper-cascor does not reach this file by itself.
#: Re-port it here and update these digests with it.
TEMPLATE_SHA256 = {
    REUSE: "2c141c4f84715aa7b9fac417232107920cac12e5eb7d6fc90e370cb0137c299c",
    RECORD: "3248631341796f842a49d1ae5ff001f7130c040f8b7ddf71adb2d02919ed3b6e",
    UPLOAD: "c529c9c77228b4a75521a7b8222bde1a11e11ab4d6d33c1219485aba72ce2ea8",
    DOWNLOAD: "507a2f2d565e94a7962a25794409de79e18ed77a5247845a58a54bd511236dda",
    VERIFY_DIST: "19d53f0b99a231edaed82cde64aae91cab6be2c7988576a6a2473ec328deea7c",
    TESTPYPI_AFTER: "aae4b6706105e98e97172598bcbed81d6673bed02c17a25075da46cf9bc26b6e",
    TESTPYPI_BEFORE: "ac904eaffc1dfe7ab3e232400d74bb61287c544164aeb5a9cfa78f65ecbcec07",
    PYPI_AFTER: "af43fe1a202e383ff39d05a7d1e2aa05d64338c8d1e2e32c60686ecd5a6c320d",
    REPUBLISH: "cb7ad4b86bf6e9909c1a3325a5b13e8df6ca4954391a9314f9e8ecf6ef7a983a",
}
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
#: The template's TEXT, beside the parsed digests above, which cannot see a YAML comment outside a run script (nor can
#: juniper-ml's cross-repo checker, which compares parsed YAML): the sha256 of each template block (from its
#: "One-artifact publish template" comment to the end of its step) and of the republish job (from its banner to the end
#: of the job) in juniper-cascor's
#: .github/workflows/publish.yml at main 5e3d9801, byte-identical to juniper-cascor#777's merge f5ed3017. Each is taken
#: with every ``uses:`` line reduced to the action's name, its ``@ref`` and trailing ``# vX.Y.Z`` dropped (SWEEP item 23),
#: so a Dependabot bump of an action moves no digest here; TestTemplate pins each action to one ref across the file, and
#: juniper-ml's cross-repo checker pins every ref to the template's. Change the template there first, then copy it here.
TEMPLATE_SOURCE = "juniper-cascor .github/workflows/publish.yml at 5e3d9801 (juniper-cascor#777's merge f5ed3017), each uses: line by its action's name"
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
PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
#: The front ends that build an sdist or a wheel: build's module and console script, pip, uv, setup.py, and the build
#: commands of hatch, poetry, pdm and flit. STEPS pins every step regardless; this keeps a build out of the other jobs.
BUILD_COMMAND = re.compile(r"\bpython3?\s+-m\s+build\b|\bpyproject-build\b|\bpip3?\s+wheel\b|\buv\s+build\b|\bsetup\.py\s+(?:sdist|bdist_wheel)\b|\b(?:hatch|poetry|pdm|flit)\s+build\b")
#: GitHub lets a deployment wait this many days for its reviewer: the PyPI job may start that late, and needs the artifact.
GATE_APPROVAL_DAYS = 30
#: The artifact's retention, as the docs state it: past the gate's 30 days and the 30-day re-run window.
RETENTION_DAYS = 90
ARTIFACT = "${{ env.PUBLISH_PACKAGE }}-dist"
ARTIFACT_NAME = f"{PACKAGE}-dist"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
RELEASE_TAG = "${{ github.event.release.tag_name }}"
WHEEL = "juniper_data-9.9.9-py3-none-any.whl"
SDIST = "juniper_data-9.9.9.tar.gz"
BUILT = {WHEEL: b"wheel bytes", SDIST: b"sdist bytes"}
JSON_PATH = f"/pypi/{PACKAGE}/9.9.9/json"
REPOSITORY = f"pcalnon/{PACKAGE}"
#: The actions the publisher uses, by name: a step is compared with its ``@ref`` dropped, so a Dependabot bump of a pin
#: changes nothing here.
CHECKOUT = "actions/checkout"
SETUP_PYTHON = "actions/setup-python"
UPLOAD_ACTION = "actions/upload-artifact"
DOWNLOAD_ACTION = "actions/download-artifact"
PYPI_PUBLISH = "pypa/gh-action-pypi-publish"
#: Each job's steps, in order, as (name, action). Nothing may be added, dropped or moved unnoticed: neither a rebuild
#: slipped into a publish job nor a step that writes into the dist directory before ``Record SHA256SUMS``.
STEPS = {
    "build": [(REUSE, None), (None, CHECKOUT), (None, SETUP_PYTHON), ("Install build tools", None), ("Build package", None), ("Check package", None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)],
    "testpypi": [(DOWNLOAD, DOWNLOAD_ACTION), (VERIFY_DIST, None), ("Publish to TestPyPI", PYPI_PUBLISH), (TESTPYPI_AFTER, None)],
    INSTALL: [(None, SETUP_PYTHON), (INSTALL_STEPS["publish.yml"], None)],
    "pypi": [(DOWNLOAD, DOWNLOAD_ACTION), (VERIFY_DIST, None), (TESTPYPI_BEFORE, None), ("Publish to PyPI", PYPI_PUBLISH), (PYPI_AFTER, None)],
    "notify-consumers": [],
    REPUBLISH: [(FIND, None), (FETCH_ORIGINAL, DOWNLOAD_ACTION), (FETCH, None), (VERIFY_DIST, None), ("Publish to PyPI", PYPI_PUBLISH), (PYPI_AFTER, None)],
}
#: The TestPyPI upload's inputs and the PyPI upload's, exactly: a misspelled input (``skip_existing``) or a value turned
#: off (``attestations: false``) would pass a check of named keys.
UPLOAD_INPUTS = ({"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT}, {"packages-dir": DIST_INPUT})
#: Every key the workflow and each of its jobs carries. An ``env`` on a job (``PIP_EXTRA_INDEX_URL``,
#: ``HASH_CHECK_ATTEMPTS``), a container, a matrix or another runner would change what a check runs, or against what.
WORKFLOW_KEYS = {"name", "on", "permissions", "env", "jobs"}
BUILD_JOB_KEYS = {"name", "if", "runs-on", "permissions", "steps"}
PUBLISH_JOB_KEYS = {"name", "needs", "runs-on", "environment", "permissions", "steps"}
INSTALL_JOB_KEYS = {"name", "needs", "runs-on", "permissions", "steps"}
REPUBLISH_JOB_KEYS = {"name", "if", "runs-on", "environment", "permissions", "steps"}
#: A job that calls a reusable workflow (notify-consumers): it names the workflow, its inputs and secrets, and runs nothing here.
CALLER_JOB_KEYS = {"name", "needs", "permissions", "uses", "with", "secrets"}
#: The keys a repository may add, none of which changes what a check runs. The workflow's: ``run-name``, which names the
#: run, and a ``concurrency`` group that never cancels a run in progress (the run it holds pending, and cancels when a
#: newer one queues, has run nothing yet). A job's: ``timeout-minutes``, which stops it sooner, and a job stopped so
#: fails, so nothing after it runs; the republish job stays identical to juniper-cascor's, so it takes one only there
#: first. No job takes a ``concurrency`` group: by default (``queue: single``) GitHub keeps one pending job per group
#: and cancels the older one when another queues, so a group on the PyPI job could stop a run between its two uploads.
OPTIONAL_WORKFLOW_KEYS = {"run-name", "concurrency"}
OPTIONAL_JOB_KEYS = {"timeout-minutes"}
#: Each build step's command: the build, and the check of what it built.
BUILD_RUNS = {"Install build tools": "pip install build twine", "Build package": "python -m build", "Check package": "twine check dist/*"}
#: The install check's bounded retry: this many tries, this many seconds apart, after one wait before the first.
INSTALL_TRIES = 5
INSTALL_RETRY_SECONDS = 10
INSTALL_FIRST_WAIT_SECONDS = 30
LAG_ERROR = "is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"
#: The package check the install step ends with (R4-5 of the sweep's review): the published version from the metadata,
#: and the package itself found by ``importlib.util.find_spec``, which locates it without running it (an import would
#: need ``python-dotenv``, which ``juniper_data`` imports at import time, absent under ``--no-deps``). It must be found with an
#: origin, so a bare directory, which loads as a namespace package, fails too, and it fails through ``SystemExit``,
#: which ``PYTHONOPTIMIZE`` keeps, where it would strip an ``assert`` statement. It prints juniper-cascor's neutral line
#: (``publish-protocol.yml``'s), with no "OK" before the check has passed (#206's review, R5).
PACKAGE_CHECK = f"""python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('{MODULE}'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('{PACKAGE}'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no {MODULE} package')\""""
#: The install check's script, exactly, line by line (the text juniper-ml's cross-repo checker pins for this step): a
#: check of its parts would pass a ``|| true`` on the pip line.
INSTALL_CHECK_LINES = [
    f"# `python -c` puts its working directory first on sys.path, and this repository's root holds {MODULE}/,",
    "# so an import run inside a checkout of it can pass without the wheel. This job checks nothing out, and it still",
    "# installs and imports from the runner's temporary directory, outside any checkout.",
    'cd "${RUNNER_TEMP}"',
    'VERSION="${RELEASE_TAG#v}"',
    "sleep 30",
    "# NOTE (security): install with --no-deps against TestPyPI only. Do NOT add a",
    "# production-PyPI fallback index here — with --no-deps no deps are fetched, so a",
    "# fallback only risks resolving a squatted target package. The sleep above, and the",
    "# retry below, cover TestPyPI index lag.",
    "# TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.",
    "for attempt in 1 2 3 4 5; do",
    "  if pip install \\",
    "    --no-deps \\",
    "    --index-url https://test.pypi.org/simple/ \\",
    f'    "{PACKAGE}==${{VERSION}}"; then',
    "    break",
    "  fi",
    '  if [ "${attempt}" -eq 5 ]; then',
    f'    echo "::error::{PACKAGE} ${{VERSION}} {LAG_ERROR}"',
    "    exit 1",
    "  fi",
    '  echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"',
    "  sleep 10",
    "done",
    f"# {MODULE} imports python-dotenv at import time, which is absent under --no-deps, so the",
    "# package cannot be imported here; verify the published artifact via its installed metadata,",
    f"# and that the wheel holds the package: find_spec locates {MODULE} without running it,",
    "# and a missing package, or a bare directory with no origin, fails the step through",
    "# SystemExit, which PYTHONOPTIMIZE keeps (it would strip an assert statement).",
    PACKAGE_CHECK,
]
INSTALL_CHECK_RUN = "\n".join(INSTALL_CHECK_LINES) + "\n"
#: The install step's keys beyond its name and script: it reads the release's tag through ``env``, so no expression is
#: pasted into the script's text.
INSTALL_STEP_ENV = {"RELEASE_TAG": "${{ github.event.release.tag_name }}"}
#: The variable the reuse and find steps read the runner's API credential from, the expression that fills it, and the
#: stand-in value the rehearsals pass. Bandit's B105 reads a string under a name like the first as a hardcoded password.
API_CREDENTIAL_ENV = "GH_TOKEN"
RUNNER_CREDENTIAL = "${{ github.token }}"
FAKE_API_CREDENTIAL = "stand-in-credential"


def _retried_install(package: str, version: str) -> list[str]:
    """The install the check runs: five tries, 10 s apart, and after the fifth failure an error that names index lag,
    rather than a package check that fails as if the package were broken."""
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


#: The install step's commands, exactly, comment and blank lines dropped: no ``exit 0``, ``trap``, earlier install or
#: second VERSION can be added and none dropped, whatever its comments say.
INSTALL_COMMANDS = ['cd "${RUNNER_TEMP}"', 'VERSION="${RELEASE_TAG#v}"', "sleep 30", *_retried_install(PACKAGE, "VERSION"), PACKAGE_CHECK]


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
    """The one ``if:`` a step may carry: the reuse step's own, the reuse condition on every later build step but a
    push-only release gate (exempt by its name; this publisher has none), and the republish job's download of the
    release run's artifact. Any other ``if:`` could skip a check."""
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


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _normalized(value: object) -> object:
    """VALUE, a parsed step or job, with every ``uses:`` reduced to its action's name, the ``@ref`` dropped (SWEEP item
    23), and every other key and value kept as it is: the form TEMPLATE_SHA256 hashes."""
    if isinstance(value, dict):
        return {key: (str(item).split("@", 1)[0] if key == "uses" else _normalized(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    return value


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


def _normalized_text(block: str) -> str:
    """BLOCK with every ``uses:`` line reduced to the action's name: its ``@ref`` and the trailing ``# vX.Y.Z`` dropped,
    every other line kept byte for byte (SWEEP item 23)."""
    return "".join(USES_LINE.sub(r"\1\2", line) + "\n" for line in block.splitlines())


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
        assert isinstance(stand, _Stand)
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
    return {"info": {"name": "juniper-data", "version": "9.9.9"}, "urls": [{"filename": name, "url": f"{base}/files/{name}", "digests": {"sha256": digest, "md5": "0" * 32}} for name, digest in files.items()]}


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
        # A single-package publisher's tags are v<version>: the republish job takes the version from after the prefix.
        assert TAG_PREFIXES[workflow] == "v"
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

    def test_the_build_reads_the_release_tag_so_the_republish_dispatch_builds_nothing(self, workflow):
        jobs = _workflow(workflow)["jobs"]
        # A dispatch has no release, so this reads an empty tag and the build, and every job after it, is skipped. Every
        # juniper-data release tag is v<version>, and publish-image.yml applies the same guard to the same release event.
        assert jobs["build"]["if"] == "startsWith(github.event.release.tag_name, 'v')"
        # The guard repeats the tag prefix the republish job reads from env: a job-level if: cannot read env.
        assert jobs["build"]["if"] == f"startsWith(github.event.release.tag_name, '{TAG_PREFIXES[workflow]}')"
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        assert "if" not in jobs[test_id]
        assert "if" not in jobs[INSTALL]
        assert "if" not in jobs[prod_id]

    def test_the_publish_jobs_chain_on_the_build_under_the_names_the_release_train_reads(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        assert sorted(jobs) == sorted(["build", test_id, INSTALL, prod_id, REPUBLISH, *OTHER_JOBS[workflow]])
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

    def test_each_job_runs_exactly_these_steps_in_this_order(self, workflow):
        # The order cases below allow other steps between the ones they name, so a step added anywhere -- a rebuild
        # before an upload, or one writing into the dist directory before Record SHA256SUMS, say -- or one dropped, such
        # as the install job's setup-python, is caught only here. Each step is its name and the action it uses, the
        # @ref dropped, so a Dependabot bump keeps the list while a named step that changes its action does not.
        jobs = _workflow(workflow)["jobs"]
        assert {job_id: _steps(job) for job_id, job in jobs.items()} == STEPS

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
        # The install check installs the package TestPyPI serves and inspects it: it may read the repository, and nothing more.
        assert jobs[INSTALL]["permissions"] == {"contents": "read"}
        assert jobs[PUBLISHERS[workflow][3]]["permissions"] == prod
        assert jobs[REPUBLISH]["permissions"] == {"actions": "read", "id-token": "write"}

    def test_a_re_run_reuses_the_first_attempts_artifact_instead_of_building(self, workflow):
        build = _workflow(workflow)["jobs"]["build"]
        reuse = build["steps"][0]
        assert reuse.get("name") == REUSE
        assert reuse.get("id") == "reuse"
        assert reuse.get("if") == "github.run_attempt != '1'"
        # It runs before the checkout, so a job default directory (a sub-package publisher sets one) does not exist yet.
        assert reuse.get("working-directory") == "${{ github.workspace }}"
        assert reuse.get("shell") == "python3 {0}"
        assert reuse.get("env") == {API_CREDENTIAL_ENV: RUNNER_CREDENTIAL}
        # Every later step is skipped once the reuse step finds the artifact. The template exempts one step, by its NAME:
        # the sub-package publishers' push-only release gate, which never runs. An exemption by its `if:` text would let
        # any build step trade the reuse condition for the push condition.
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
        # workflow concurrency group that never cancels, and a job's timeout-minutes, change no check, so a repository
        # may add them (OPTIONAL_*_KEYS). A job's own concurrency group is refused: by default (queue: single) it cancels
        # the group's pending job when another queues.
        wf = _workflow(workflow)
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        assert WORKFLOW_KEYS <= set(wf) <= WORKFLOW_KEYS | OPTIONAL_WORKFLOW_KEYS, f"workflow keys {sorted(wf)}"
        want = {"build": BUILD_JOB_KEYS, test_id: PUBLISH_JOB_KEYS, INSTALL: INSTALL_JOB_KEYS, prod_id: PUBLISH_JOB_KEYS, REPUBLISH: REPUBLISH_JOB_KEYS}
        # A job that calls a reusable workflow runs on none of its own: it holds no runs-on and no steps.
        callers = dict.fromkeys(OTHER_JOBS[workflow], CALLER_JOB_KEYS)
        assert {job_id: set(job) - OPTIONAL_JOB_KEYS for job_id, job in wf["jobs"].items()} == {**want, **callers}
        assert {job_id: job.get("runs-on") for job_id, job in wf["jobs"].items()} == {**dict.fromkeys(want, "ubuntu-latest"), **dict.fromkeys(callers)}

    def test_no_env_points_pip_elsewhere(self, workflow):
        # PIP_INDEX_URL or PIP_EXTRA_INDEX_URL in any env would send the install check, or the build tools, to another index.
        wf = _workflow(workflow)
        envs = [wf.get("env") or {}] + [job.get("env") or {} for job in wf["jobs"].values()] + [step.get("env") or {} for job in wf["jobs"].values() for step in job.get("steps") or []]
        assert not [key for env in envs for key in env if str(key).upper().startswith("PIP_")]

    def test_the_build_steps_run_exactly_their_commands(self, workflow):
        # `|| true` after twine check, or a build without its sdist, would ship what the build job no longer checks.
        build = _workflow(workflow)["jobs"]["build"]
        assert {name: str(_step(build, name)["run"]).strip() for name in BUILD_RUNS} == BUILD_RUNS


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
        assert _steps(job) == STEPS[test_id]
        assert not [s for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]

    def test_it_installs_and_imports_from_outside_any_checkout(self, workflow):
        job = _workflow(workflow)["jobs"][INSTALL]
        assert "defaults" not in job
        step = _step(job, INSTALL_STEPS[workflow])
        assert "working-directory" not in step
        commands = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")]
        # `python -c` puts its working directory first on sys.path, and this repository's root holds juniper_data/:
        # a check run inside a checkout could pass without the wheel. So the first command leaves for the runner's
        # temporary directory, and no command moves elsewhere.
        assert commands[0] == 'cd "${RUNNER_TEMP}"'
        assert [c for c in commands if c.split()[0] in ("cd", "pushd", "popd")] == ['cd "${RUNNER_TEMP}"']
        assert [c for c in commands if "pip install" in c]
        assert [c for c in commands if c.startswith("python -c ")]
        # The version comes from the release's tag, so the job checks nothing out: no workspace for the package to run in.
        assert not [s for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]

    def test_the_install_step_runs_exactly_its_commands(self, workflow):
        # Exactly these commands, in this order, comment and blank lines dropped: no `exit 0`, trap, earlier install or
        # second VERSION can be added, and none dropped. The step carries its name, its script, and the release's tag
        # through env: no expression is pasted into the script.
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        assert [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")] == INSTALL_COMMANDS
        assert {key: value for key, value in step.items() if key not in ("name", "run")} == {"env": INSTALL_STEP_ENV}
        assert "${{" not in step["run"]

    def test_the_install_check_cannot_be_switched_off(self, workflow):
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        commands = "\n".join(line for line in step["run"].splitlines() if not line.strip().startswith("#"))
        # A failed install or package check must fail the job: no `|| true` (nor any `||`), no `set +e`, the runner's
        # default shell, and neither continue-on-error nor if:.
        assert "||" not in commands
        assert "set +e" not in commands
        assert "shell" not in step
        assert "continue-on-error" not in step
        assert "if" not in step
        # TestPyPI alone, with no pypi.org fallback that a same-name squatter could answer (juniper-ml#384).
        assert "--index-url https://test.pypi.org/simple/" in commands
        assert "--extra-index-url" not in commands

    def test_the_package_check_finds_the_package_and_fails_through_systemexit(self, workflow):
        # R4-5: a metadata check alone passes for a wheel that lacks the package. find_spec locates it without importing
        # it; the check needs an origin (a bare directory loads as a namespace package, with none), and it fails through
        # SystemExit, never an assert, which PYTHONOPTIMIZE strips.
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        last = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")][-1]
        assert last == PACKAGE_CHECK
        code = shlex.split(last)[2]
        assert f"u.find_spec('{MODULE}')" in code
        assert "raise SystemExit(0 if origin else" in code
        assert "assert" not in code


def _run_install(tmp_path: Path, pip_failures: int, python_status: int = 0, tag: str = "v1.2.3") -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run the install step as the runner runs a ``run:`` without a ``shell:`` (``bash -e {0}``), against stand-in
    ``pip``, ``python`` and ``sleep`` commands that log each call (the command, its directory, its arguments): ``pip``
    fails its first PIP_FAILURES calls, and ``python`` exits with PYTHON_STATUS."""
    bin_dir, runner_temp, workspace = tmp_path / "bin", tmp_path / "runner-temp", tmp_path / "workspace"
    for directory in (bin_dir, runner_temp, workspace):
        directory.mkdir(parents=True)
    log = tmp_path / "calls.log"
    stubs = {"pip": 'test "$(grep -c "^pip" "$STUB_LOG")" -gt "$STUB_PIP_FAILURES"\n', "python": 'exit "$STUB_PYTHON_STATUS"\n', "sleep": ""}
    for name, body in stubs.items():
        stub = bin_dir / name
        stub.write_text(f'#!/bin/sh\nprintf "%s\\t%s\\t%s\\n" "{name}" "$(pwd -P)" "$*" >> "$STUB_LOG"\n{body}', encoding="utf-8")
        stub.chmod(0o700)
    script = tmp_path / "install.sh"
    script.write_text(_step(_workflow("publish.yml")["jobs"][INSTALL], INSTALL_STEPS["publish.yml"])["run"], encoding="utf-8")
    bash = shutil.which("bash")
    assert bash, "the install check runs under bash"
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "RUNNER_TEMP": str(runner_temp), "GITHUB_WORKSPACE": str(workspace), "RELEASE_TAG": tag, "STUB_LOG": str(log), "STUB_PIP_FAILURES": str(pip_failures), "STUB_PYTHON_STATUS": str(python_status)}
    proc = subprocess.run([bash, "-e", str(script)], cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=60, check=False)  # nosec B603 - fixed argv: bash and the workflow's own extracted step
    calls = [line.split("\t", 2) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return proc, calls


def _run_package_check(tmp_path: Path, wheel: str, **env: str) -> subprocess.CompletedProcess[str]:
    """Run the install step's own ``python -c`` with this interpreter from an empty directory, as the step runs it from
    ``$RUNNER_TEMP``, against a site directory standing in for the install: WHEEL is "package" (the package and its
    metadata), "metadata-only" (the metadata alone), "bare-directory" (the metadata and an empty package directory) or
    "nothing". ``-S`` keeps this interpreter's own site-packages, which may hold the real package, off ``sys.path``."""
    site, cwd = tmp_path / "site", tmp_path / "runner-temp"
    for directory in (site, cwd):
        directory.mkdir(parents=True)
    if wheel != "nothing":
        info = site / f"{DIST_NAME}-1.2.3.dist-info"
        info.mkdir()
        (info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {PACKAGE}\nVersion: 1.2.3\n", encoding="utf-8")
    if wheel in ("package", "bare-directory"):
        (site / MODULE).mkdir()
    if wheel == "package":
        (site / MODULE / "__init__.py").write_text("raise ImportError('the check must find the package without running it')\n", encoding="utf-8")
    step = _step(_workflow("publish.yml")["jobs"][INSTALL], INSTALL_STEPS["publish.yml"])
    last = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")][-1]
    argv = shlex.split(last)
    assert argv[:2] == ["python", "-c"] and len(argv) == 3, argv
    child = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": str(site), **env}
    return subprocess.run([sys.executable, "-S", "-c", argv[2]], cwd=cwd, env=child, capture_output=True, text=True, timeout=60, check=False)  # nosec B603 - fixed argv: this interpreter and the step's own check


class TestInstallCheckScript:
    """The install step's own shell, run as the runner runs it, against stand-in ``pip``, ``python`` and ``sleep``; and
    its package check, run by a real interpreter."""

    def test_index_lag_that_outlasts_every_try_fails_naming_the_lag_and_never_imports(self, tmp_path):
        proc, calls = _run_install(tmp_path, pip_failures=INSTALL_TRIES)
        assert proc.returncode == 1
        assert f"::error::{PACKAGE} 1.2.3 {LAG_ERROR}" in proc.stdout
        assert [call[0] for call in calls if call[0] != "sleep"] == ["pip"] * INSTALL_TRIES
        # One wait before the first try, a wait between tries, and none after the last.
        assert [call[2] for call in calls if call[0] == "sleep"] == [str(INSTALL_FIRST_WAIT_SECONDS)] + [str(INSTALL_RETRY_SECONDS)] * (INSTALL_TRIES - 1)

    def test_a_try_that_installs_ends_the_retries_and_the_check_runs_from_runner_temp(self, tmp_path):
        proc, calls = _run_install(tmp_path, pip_failures=2)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert [call[2] for call in calls if call[0] == "pip"] == [f"install --no-deps --index-url https://test.pypi.org/simple/ {PACKAGE}==1.2.3"] * 3
        assert [call[0] for call in calls][-1] == "python"
        assert {call[1] for call in calls} == {str((tmp_path / "runner-temp").resolve())}
        assert "::error::" not in proc.stdout

    def test_a_check_that_fails_after_the_install_fails_the_step(self, tmp_path):
        proc, calls = _run_install(tmp_path, pip_failures=0, python_status=1)
        assert proc.returncode != 0
        assert [call[0] for call in calls if call[0] != "sleep"] == ["pip", "python"]

    def test_the_release_tag_is_read_as_data_never_run_as_script(self, tmp_path):
        # The tag reaches the check through env: text in it that a shell would run, if pasted into the script, is only a
        # version that does not install.
        proc, calls = _run_install(tmp_path, pip_failures=0, tag="v1.2.3$(touch pasted)")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert [call[2] for call in calls if call[0] == "pip"] == [f"install --no-deps --index-url https://test.pypi.org/simple/ {PACKAGE}==1.2.3$(touch pasted)"]
        assert not list(tmp_path.rglob("pasted"))

    def test_the_package_check_passes_for_a_wheel_that_holds_the_package_without_running_it(self, tmp_path):
        proc = _run_package_check(tmp_path, "package")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert proc.stdout.startswith("TestPyPI install 1.2.3 package at ")
        assert proc.stdout.strip().endswith(str(tmp_path / "site" / MODULE / "__init__.py"))

    @pytest.mark.parametrize("optimize", ["", "1", "2"], ids=["plain", "PYTHONOPTIMIZE=1", "PYTHONOPTIMIZE=2"])
    @pytest.mark.parametrize("wheel", ["metadata-only", "bare-directory"])
    def test_the_package_check_fails_for_a_wheel_without_the_package_even_optimized(self, tmp_path, wheel, optimize):
        proc = _run_package_check(tmp_path, wheel, **({"PYTHONOPTIMIZE": optimize} if optimize else {}))
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert f"the installed wheel holds no {MODULE} package" in proc.stderr
        # The line it prints first says what it found, and no "OK": the log never reads as a pass before the verdict.
        assert proc.stdout.startswith("TestPyPI install 1.2.3 package at None")
        assert "OK" not in proc.stdout

    def test_the_package_check_fails_when_nothing_is_installed(self, tmp_path):
        proc = _run_package_check(tmp_path, "nothing")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert "PackageNotFoundError" in proc.stderr


class TestUnchanged:
    # The permissions are not here: they changed, and TestWiring pins them per job. So is the build's tag guard, which
    # is new here: before this change publish.yml had no job guard.
    def test_publish_yml_still_publishes_on_a_published_release_alone(self):
        wf = _workflow("publish.yml")
        # workflow_dispatch is new, for the republish job alone: TestWiring pins its one input and that job's gate.
        assert set(wf["on"]) == {"release", "workflow_dispatch"}
        assert wf["on"]["release"] == {"types": ["published"]}
        assert "concurrency" not in wf

    def test_publish_yml_builds_with_the_commands_it_used_before(self):
        build = _workflow("publish.yml")["jobs"]["build"]
        runs = [str(s.get("run") or "").strip() for s in build["steps"]]
        assert runs.index("pip install build twine") < runs.index("python -m build") < runs.index("twine check dist/*")
        setup = [s for s in build["steps"] if str(s.get("uses") or "").startswith("actions/setup-python@")]
        assert [s.get("with") for s in setup] == [{"python-version": "3.12"}]

    def test_the_install_job_keeps_the_testpypi_jobs_python_and_its_install_check(self):
        job = _workflow("publish.yml")["jobs"][INSTALL]
        # The setup-python the TestPyPI job ran moved with the install check, before it; the checkout did not.
        assert str(job["steps"][0].get("uses")).startswith("actions/setup-python@")
        assert job["steps"][0].get("with") == {"python-version": "3.12"}
        install = job["steps"][-1]
        assert install["name"] == "Verify TestPyPI install"
        run = install["run"]
        # The version comes from the release tag, now through env, and pip reads TestPyPI alone, with --no-deps (juniper-ml#384).
        assert install["env"] == INSTALL_STEP_ENV
        assert 'VERSION="${RELEASE_TAG#v}"' in run
        assert f'"{PACKAGE}==${{VERSION}}"' in run
        assert "--no-deps" in run
        assert "extra-index-url" not in run
        assert f"m.version('{PACKAGE}')" in run

    def test_notify_consumers_still_follows_the_pypi_job_alone_so_a_republish_dispatch_skips_it(self):
        # A dispatch skips `pypi` (it needs the build, which reads a release tag), so this job is skipped too: no `if:`
        # may make it run without that job's success. Its version comes from the release event, which a dispatch lacks.
        job = _workflow("publish.yml")["jobs"]["notify-consumers"]
        assert job == {
            "name": "Notify consumer repos",
            "needs": "pypi",
            "permissions": {},
            "uses": "./.github/workflows/notify-consumers.yml",
            "with": {"version": RELEASE_TAG},
            "secrets": {"CROSS_REPO_DISPATCH_TOKEN": "${{ secrets.CROSS_REPO_DISPATCH_TOKEN }}"},
        }


class TestExactly:
    """What the order and key checks above would let through: a failure let pass, an install check that cannot fail,
    an upload input misspelled or turned off. (An extra step: TestWiring's exact step list.)"""

    def test_no_job_and_no_step_lets_a_failure_pass(self):
        for job_id, job in _workflow("publish.yml")["jobs"].items():
            # A job or step that continues on error is a check that no longer blocks, and an if: can skip one. The build
            # and republish jobs' own if: are pinned to their exact text elsewhere; no other job may carry one (`always()`
            # on the PyPI job would publish after a failed install check).
            assert "continue-on-error" not in job, f"job {job_id} sets continue-on-error"
            if job_id not in ("build", REPUBLISH):
                assert "if" not in job, f"{job_id} carries if: {job.get('if')!r}"
            for index, step in enumerate(job.get("steps") or []):
                label = f"{job_id}: {step.get('name') or step.get('uses')}"
                assert "continue-on-error" not in step, f"{label} sets continue-on-error"
                assert step.get("if") == _allowed_if(job_id, index, step), f"{label} carries if: {step.get('if')!r}"

    def test_the_install_check_runs_exactly_this(self):
        assert _step(_workflow("publish.yml")["jobs"][INSTALL], "Verify TestPyPI install") == {"name": "Verify TestPyPI install", "env": INSTALL_STEP_ENV, "run": INSTALL_CHECK_RUN}

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
        # One reuse step and one record step; a dist check before each of three uploads; three JSON checks in the release
        # jobs and one in the republish job; one of each republish step.
        assert {kind: len(runs) for kind, runs in copies.items()} == {REUSE: 1, RECORD: 1, VERIFY_DIST: 3, "index": 4, FIND: 1, FETCH: 1}
        assert {kind: len(set(runs)) for kind, runs in copies.items()} == {REUSE: 1, RECORD: 1, VERIFY_DIST: 1, "index": 1, FIND: 1, FETCH: 1}

    def test_the_template_steps_and_the_republish_job_equal_juniper_cascor_at_f5ed30177766(self):
        """Each copy of a template step, and the republish job, equals juniper-cascor's publish.yml at TEMPLATE_COMMIT.

        A port has one publisher, so comparing its copies with each other cannot catch the template drifting as a whole.
        This pins a snapshot, not the template's current state: when juniper-cascor changes the template, re-port the
        changed steps here verbatim and take the new digests (and TEMPLATE_COMMIT) from that commit. Each is compared
        with every ``uses:`` reduced to its action's name, so a Dependabot bump of an action needs no re-port; the next
        case pins the refs.
        """
        assert TEMPLATE_COMMIT == "f5ed30177766", "this case's name names the snapshot: rename it with TEMPLATE_COMMIT"
        for workflow in PUBLISHERS:
            jobs = _workflow(workflow)["jobs"]
            assert _digest(_normalized(jobs[REPUBLISH])) == TEMPLATE_SHA256[REPUBLISH], f"{workflow}: the republish job is not juniper-cascor's at {TEMPLATE_COMMIT}"
            seen: list[str] = []
            for job_id, job in jobs.items():
                if job_id == REPUBLISH:
                    continue
                for step in job.get("steps") or []:
                    name = step.get("name")
                    if name in TEMPLATE_SHA256:
                        assert _digest(_normalized(step)) == TEMPLATE_SHA256[name], f"{workflow}: {job_id}'s {name!r} is not juniper-cascor's template step at {TEMPLATE_COMMIT}"
                        seen.append(name)
            # The build job's reuse, record and upload steps; each publish job's download and dist check; the three JSON
            # checks. The republish job's own copies are inside its digest.
            assert sorted(seen) == sorted([REUSE, RECORD, UPLOAD, DOWNLOAD, VERIFY_DIST, TESTPYPI_AFTER, DOWNLOAD, VERIFY_DIST, TESTPYPI_BEFORE, PYPI_AFTER])

    def test_each_action_is_pinned_to_one_ref_in_every_publisher(self):
        # The digests above drop each action's ref, so that a Dependabot bump of a pin, which moves every copy in a file
        # at once, needs no re-port. A hand edit that moves one copy fails here, wherever it is.
        refs: dict[str, set[str]] = {}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    if step.get("uses"):
                        name, _, ref = str(step["uses"]).partition("@")
                        refs.setdefault(name, set()).add(ref)
        assert {name: len(found) for name, found in refs.items()} == dict.fromkeys(refs, 1), refs
        assert set(refs) == {CHECKOUT, SETUP_PYTHON, UPLOAD_ACTION, DOWNLOAD_ACTION, PYPI_PUBLISH}
        assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for found in refs.values() for ref in found), refs

    def test_the_normalized_digest_drops_only_the_ref_of_a_uses_value(self):
        # The normalization is what the digests above stand on: it drops a uses: value's @ref, and nothing else, so an
        # action's NAME, every other key and value, and the order of a job's steps still count.
        step = {"name": UPLOAD, "uses": "actions/upload-artifact@0123456789abcdef0123456789abcdef01234567", "with": {"retention-days": 90}}
        assert _normalized(step) == {"name": UPLOAD, "uses": "actions/upload-artifact", "with": {"retention-days": 90}}
        assert _digest(_normalized({**step, "uses": "actions/upload-artifact@fedcba9876543210fedcba9876543210fedcba98"})) == _digest(_normalized(step))
        assert _digest(_normalized({**step, "uses": "actions/upload-artefact@0123456789abcdef0123456789abcdef01234567"})) != _digest(_normalized(step))
        assert _digest(_normalized({**step, "with": {"retention-days": 30}})) != _digest(_normalized(step))
        job = {"steps": [step, {"name": RECORD, "run": "x"}]}
        assert _digest(_normalized({"steps": job["steps"][::-1]})) != _digest(_normalized(job))

    def test_every_template_block_is_juniper_cascors_byte_for_byte(self):
        # One publisher here, so the copies above cannot drift apart from each other unseen, but they could drift from
        # the template together: each block, comments included, must hash to juniper-cascor's, byte for byte once each
        # uses: line is reduced to its action's name (test_each_action_is_pinned_to_one_ref_in_every_publisher pins the refs).
        text = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
        assert {key: _sha(_normalized_text(block).encode("utf-8")) for key, block in _template_blocks(text).items()} == CASCOR_TEMPLATE_SHA256, f"a template block differs from {TEMPLATE_SOURCE}"

    def test_the_republish_job_is_juniper_cascors_byte_for_byte(self):
        text = (WORKFLOWS / "publish.yml").read_text(encoding="utf-8")
        assert _sha(_normalized_text(_republish_job(text)).encode("utf-8")) == CASCOR_REPUBLISH_SHA256, f"the republish job differs from {TEMPLATE_SOURCE}"

    def test_the_normalized_text_drops_only_the_ref_of_a_uses_line(self):
        # The text normalization is what the raw digests stand on: it drops a uses: line's @ref and its # vX.Y.Z, and
        # nothing else, so an action's NAME, and every other line, still count byte for byte.
        block = "        uses: actions/upload-artifact@0123456789abcdef0123456789abcdef01234567  # v7.0.2\n          retention-days: 90\n"
        assert _normalized_text(block) == "        uses: actions/upload-artifact\n          retention-days: 90\n"
        assert _normalized_text(block.replace("actions/upload-artifact", "actions/upload-artefact")) != _normalized_text(block)
        assert _normalized_text(block.replace("90", "30")) != _normalized_text(block)
        assert _normalized_text(block.replace("0123456789abcdef", "fedcba9876543210").replace("v7.0.2", "v7.0.3")) == _normalized_text(block)

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

    @pytest.mark.parametrize("stray", ["notes.txt", "juniper_data-9.9.9.zip"])
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
        root = tmp_path / "workspace"
        package_dir = root / "sub-package"
        (package_dir / "dist").mkdir(parents=True)
        (package_dir / "dist" / "sub_package-1.0.0-py3-none-any.whl").write_bytes(b"sub-package wheel")
        # A publisher whose build steps run in a package directory (juniper-cascor's sub-package publishers set
        # defaults.run.working-directory) still names its dist directory from the workspace.
        proc = _run(_script(RECORD, tmp_path), root, cwd=package_dir, PUBLISH_PACKAGE="sub-package", PUBLISH_DIST_DIR="sub-package/dist")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (root / "SHA256SUMS").read_text(encoding="utf-8") == f"{_sha(b'sub-package wheel')}  sub_package-1.0.0-py3-none-any.whl\n"


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
        (workspace / "dist" / "juniper_data-9.9.9-py2.py3-none-any.whl").write_bytes(b"x")
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
        server = stand({JSON_PATH: [(200, _release({**SERVED, "juniper_data-9.9.9-py2.py3-none-any.whl": "b" * 64}))]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server)
        assert proc.returncode == 1
        assert len(server.paths()) == 1

    def test_it_gives_up_after_its_bounded_attempts(self, workspace, tmp_path, stand):
        server = stand({JSON_PATH: [NOT_FOUND]})
        proc = self._check(self._ready(workspace, tmp_path), workspace, server, attempts=3)
        assert proc.returncode == 1
        assert "after 3 attempts" in proc.stdout
        assert len(server.paths()) == 3

    @pytest.mark.parametrize("extra", [f"{OTHER_DIST_NAME}-9.9.9-py3-none-any.whl", "juniper_data-9.9.8.tar.gz", "juniper_data-9.9.9.zip"], ids=["another-package", "another-version", "not-a-distribution"])
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
    outputs: dict[str, str] = {}
    for line in (tmp_path / "github_output").read_text(encoding="utf-8").splitlines():
        if line:
            key, value = line.split("=", 1)
            outputs[key] = value
    return outputs


RUN_ARTIFACTS = f"/repos/{REPOSITORY}/actions/runs/4242/artifacts?name=juniper-data-dist&per_page=100"


class TestReuseStep:
    @staticmethod
    def _env(tmp_path: Path, server: _Stand) -> dict[str, str]:
        return _github_env(tmp_path, server, GITHUB_RUN_ID="4242", GITHUB_RUN_ATTEMPT="2")

    def test_an_unexpired_artifact_from_an_earlier_attempt_is_reused(self, workspace, tmp_path, stand):
        server = stand({RUN_ARTIFACTS: [(200, {"artifacts": [{"id": 7, "name": "juniper-data-dist", "expired": False}]})]})
        proc = _run(_script(REUSE, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"reuse": "true"}
        path, headers = server.requests[0]
        assert path == RUN_ARTIFACTS
        assert headers.get("Authorization") == f"Bearer {FAKE_API_CREDENTIAL}"

    @pytest.mark.parametrize(
        "artifacts",
        [[], [{"id": 7, "name": "juniper-data-dist", "expired": True}], [{"id": 8, "name": "coverage-report", "expired": False}]],
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


def _artifacts_path(run_id: int, package: str = "juniper-data") -> str:
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
        [("v9.9.9", "branch"), ("main", "branch"), ("juniper-cascor-model-v1.2.3", "tag"), (f"{PACKAGE}-v9.9.9", "tag"), ("v", "tag")],
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
        # The template's step as a sub-package publisher runs it (PUBLISH_TAG_PREFIX <package>-v): the other half of the
        # prefix rule, which this repository's single-package publisher never exercises.
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
        [{}, {**SERVED, f"{OTHER_DIST_NAME}-9.9.9-py3-none-any.whl": "d" * 64}, {**SERVED, "juniper_data-9.9.8.tar.gz": "d" * 64}],
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
#: The new juniper_data/tests/unit/test_testpypi_install_verify.py, whole: its rehearsal of the install step's own
#: shell, moved with the step into its job. Installed only over BASE_INSTALL_TEST_SHA256.
INSTALL_TEST_MODULE = r'''"""Rehearse the TestPyPI install check in ``publish.yml``.

Production publish (``jobs.pypi``) waits on ``verify-testpypi-install``, the job the install check has run in since
the one-artifact template's sweep (juniper-cascor#777; ruling 2 of 2026-11-16): it needs ``testpypi`` and holds
``contents: read`` alone, so nothing it runs can mint a credential. Its last step installs the release just uploaded
to TestPyPI, pinned to the tag's version by pip's ``juniper-data==<version>``, reads the installed version from its
metadata, and finds the package with ``importlib.util.find_spec``. It does not compare that version with the tag; the
pin does. Two ways that step can go green without proving the upload:

* a second index (``--extra-index-url`` or a production PyPI fallback) can
  resolve a different ``juniper-data`` than the one just published, and with
  ``--no-deps`` that fallback fetches nothing else — it only widens which
  copy of this package pip will accept;
* ``pip`` or the package check exiting non-zero has to fail the step. A
  ``|| true``, or a ``continue-on-error`` on the step, lets ``pypi`` publish
  after a verify that did not succeed. The install is tried five times, 10 s
  apart, for TestPyPI's index lag, and the fifth failure fails the step with
  an error that names the lag.

The check reads installed metadata and locates the package without running it. ``juniper_data`` imports
``python-dotenv`` at import time, and ``--no-deps`` does not install it, so ``import juniper_data`` would fail a good
publish.

The step reads the release tag from its own ``env`` (``RELEASE_TAG``, which GitHub fills from
``${{ github.event.release.tag_name }}``), so no expression is pasted into the script, and GitHub runs a ``run:`` step
that names no ``shell:`` under ``bash -e``. This test sets that variable and the runner's ``RUNNER_TEMP`` and then
executes the workflow's own ``run:`` block. Stand-ins for ``sleep``, ``pip`` and ``python`` record their arguments, so
neither the 30 s TestPyPI lag wait nor a retry's 10 s is actually slept.
"""

from __future__ import annotations

import os
import re
import subprocess  # nosec B404 - runs the workflow's own extracted shell (fixed argv)
from pathlib import Path
from typing import Any

import pytest
import yaml

pytestmark = [pytest.mark.unit]

_WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "publish.yml"
_INSTALL_JOB = "verify-testpypi-install"
_STEP_NAME = "Verify TestPyPI install"
_TAG_EXPR = "${{ github.event.release.tag_name }}"
_TEST_INDEX = "https://test.pypi.org/simple/"
_TAG = re.compile(r"[A-Za-z0-9._-]+")
_LAG_ERROR = "is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"


def _workflow() -> dict[str, Any]:
    data = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) reads the bare `on:` key as boolean True.
    if True in data and "on" not in data:
        data["on"] = data.pop(True)
    return data


def _step() -> dict[str, Any]:
    return next(s for s in _workflow()["jobs"][_INSTALL_JOB]["steps"] if s.get("name") == _STEP_NAME)


def _script() -> str:
    step = _step()
    script = step["run"]
    assert isinstance(script, str)
    # The tag reaches the script through the step's env, never as an expression pasted into its text.
    assert step.get("env") == {"RELEASE_TAG": _TAG_EXPR}
    assert "${{" not in script
    return script


def _code(script: str) -> str:
    """The step with comment lines removed, so a warning in a comment is not the command."""
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


def _run(tmp_path: Path, tag: str, *, pip_rc: int = 0, python_rc: int = 0) -> tuple[subprocess.CompletedProcess[str], list[str], list[str] | None, list[str] | None]:
    """Run the step's shell. ``sleep`` records its argument and returns immediately; ``python`` records where it ran."""
    assert _TAG.fullmatch(tag), tag
    script = _script()

    bindir = tmp_path / "bin"
    bindir.mkdir()
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    trace = tmp_path / "trace.txt"
    pip_argv = tmp_path / "pip-argv.txt"
    python_argv = tmp_path / "python-argv.txt"
    (bindir / "sleep").write_text('#!/bin/sh\nprintf \'sleep %s\\n\' "$*" >> "$TRACE"\nexit 0\n', encoding="utf-8")
    (bindir / "pip").write_text('#!/bin/sh\nprintf \'pip\\n\' >> "$TRACE"\nprintf \'%s\\n\' "$@" > "$PIP_ARGV"\nexit "${PIP_RC:-0}"\n', encoding="utf-8")
    (bindir / "python").write_text('#!/bin/sh\nprintf \'python\\n\' >> "$TRACE"\npwd > "$PYTHON_ARGV"\nprintf \'%s\\n\' "$@" >> "$PYTHON_ARGV"\nexit "${PYTHON_RC:-0}"\n', encoding="utf-8")
    for name in ("sleep", "pip", "python"):
        (bindir / name).chmod(0o755)

    env = {
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
        "HOME": str(tmp_path),
        "LANG": "C",
        "RELEASE_TAG": tag,
        "RUNNER_TEMP": str(runner_temp),
        "TRACE": str(trace),
        "PIP_ARGV": str(pip_argv),
        "PYTHON_ARGV": str(python_argv),
        "PIP_RC": str(pip_rc),
        "PYTHON_RC": str(python_rc),
    }
    proc = subprocess.run(  # nosec B603 B607 - workflow shell, fixed argv, stubs are written above
        ["bash", "-e", "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        encoding="utf-8",
        check=False,
        timeout=15,
    )
    trace_lines = trace.read_text(encoding="utf-8").splitlines() if trace.exists() else []
    pip_args = pip_argv.read_text(encoding="utf-8").splitlines() if pip_argv.exists() else None
    python_args = python_argv.read_text(encoding="utf-8").splitlines() if python_argv.exists() else None
    if python_args is not None:
        # The check runs from the runner's temporary directory, outside any checkout: its first line is where.
        assert python_args[0] == str(runner_temp), python_args[0]
        python_args = python_args[1:]
    return proc, trace_lines, pip_args, python_args


def test_production_publish_waits_on_a_verify_step_that_can_fail() -> None:
    """A swallowed verify still lets ``pypi`` publish: it ``needs`` this job."""
    doc = _workflow()
    needs = doc["jobs"]["pypi"]["needs"]
    if not isinstance(needs, list):
        needs = [needs]
    assert "testpypi" in needs
    assert _INSTALL_JOB in needs
    assert doc["jobs"]["testpypi"]["environment"] == "testpypi"
    assert doc["jobs"]["testpypi"]["name"] == "Publish to TestPyPI"
    job = doc["jobs"][_INSTALL_JOB]
    assert job["name"] == "Verify the TestPyPI install"
    assert job["needs"] == "testpypi"
    assert job["permissions"] == {"contents": "read"}
    assert "environment" not in job
    assert "continue-on-error" not in job

    step = _step()
    assert "shell" not in step, "a named shell replaces GitHub's bash -e {0}, which this rehearsal reproduces (shell: bash adds pipefail; a custom template such as 'bash {0}' would drop -e and let a failing pip pass)"
    assert "continue-on-error" not in step
    assert set(step) == {"name", "env", "run"}

    code = _code(_script())
    assert "--no-deps" in code
    assert "--extra-index-url" not in code
    assert "https://pypi.org" not in code
    assert "|| true" not in code
    assert _TEST_INDEX in code
    assert "importlib.metadata" in code
    assert "import juniper_data" not in code
    assert "u.find_spec('juniper_data')" in code


@pytest.mark.parametrize(
    ("tag", "version"),
    [
        ("v0.17.1", "0.17.1"),
        # No release run reaches this step with a tag that lacks the `v`: since 2026-11-15 publish.yml's build job runs
        # only for startsWith(tag, 'v'), and every later job needs it. The case stays because it pins the step's own
        # `${RELEASE_TAG#v}`, which strips at most one `v` and needs none, should the guard or the tag convention change.
        ("0.17.1", "0.17.1"),
        ("v1.2.3-rc.1", "1.2.3-rc.1"),
    ],
)
def test_installs_the_stripped_version_from_testpypi_only(tmp_path: Path, tag: str, version: str) -> None:
    """One leading ``v`` comes off. The suffix stays. Nothing is added to the index list."""
    proc, trace, pip_args, python_args = _run(tmp_path, tag)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert trace == ["sleep 30", "pip", "python"]
    assert pip_args == ["install", "--no-deps", "--index-url", _TEST_INDEX, f"juniper-data=={version}"]
    assert python_args is not None
    assert python_args[0] == "-c"
    check = python_args[1]
    assert "importlib.metadata" in check
    assert "m.version('juniper-data')" in check
    assert "u.find_spec('juniper_data')" in check
    assert "import juniper_data" not in check


def test_a_failed_install_fails_before_the_version_check(tmp_path: Path) -> None:
    """An install that never succeeds is tried five times, 10 s apart, then fails naming index lag; the check never runs."""
    proc, trace, pip_args, python_args = _run(tmp_path, "v0.17.1", pip_rc=1)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, combined
    assert trace == ["sleep 30", "pip", "sleep 10", "pip", "sleep 10", "pip", "sleep 10", "pip", "sleep 10", "pip"]
    assert pip_args is not None and pip_args[0] == "install"
    assert python_args is None
    assert f"::error::juniper-data 0.17.1 {_LAG_ERROR}" in proc.stdout


def test_a_failed_version_check_fails_the_step(tmp_path: Path) -> None:
    """A non-zero exit from the installed-package check fails the step, after pip has run."""
    proc, trace, _pip_args, python_args = _run(tmp_path, "v0.17.1", python_rc=1)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert trace == ["sleep 30", "pip", "python"]
    assert python_args is not None
'''
#: The new juniper_data/tests/unit/test_publish_docs_bounds.py, whole: the port of juniper-cascor#777's
#: src/tests/unit/test_publish_docs_bounds.py. Written only where no such file exists.
DOCS_BOUNDS_TEST_MODULE = r'''"""Pin the publish docs' numbers to ``publish.yml``: the bounds the docs state are the bounds the steps run.

``docs/ci_cd/CICD_MANUAL.md``, ``docs/ci_cd/CICD_REFERENCE.md``, ``docs/REFERENCE.md`` and
``docs/DEVELOPER_CHEATSHEET.md`` give an operator the numbers that decide whether a failed check was index lag: how
often and how far apart the JSON checks poll, how long each request may take, how many times the install check tries,
how far apart, and how long it waits first. Each is read here from the workflow and required in the docs, so a change
to either side alone fails. A module of its own, as juniper-cascor#777's ``src/tests/unit/test_publish_docs_bounds.py``
is (this is its port): ``test_publish_one_artifact.py`` reads the workflows alone.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# CI collects ``-m "unit and not slow"`` with ``--strict-markers`` and does not auto-mark, so an unmarked test is
# collected and then silently DESELECTED. Module-level, so it covers tests added later.
pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]
WORKFLOW = REPO / ".github" / "workflows" / "publish.yml"
DOCS = REPO / "docs"
#: The JSON check every copy of the template runs; its first copy, in the TestPyPI job, is read here.
INDEX_CHECK = "Verify TestPyPI serves exactly these files"
INSTALL = "verify-testpypi-install"
INSTALL_STEP = "Verify TestPyPI install"
MANUAL = "ci_cd/CICD_MANUAL.md"
CICD_REFERENCE = "ci_cd/CICD_REFERENCE.md"
REFERENCE = "REFERENCE.md"
CHEATSHEET = "DEVELOPER_CHEATSHEET.md"


def _jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _run(job: dict, name: str) -> str:
    found = [s for s in job.get("steps") or [] if s.get("name") == name]
    assert len(found) == 1, f"expected exactly one step named {name!r}"
    return str(found[0]["run"])


def _doc(name: str) -> str:
    """The doc's text with each run of whitespace made one space: a rewrapped paragraph states the same bounds."""
    return " ".join((DOCS / name).read_text(encoding="utf-8").split())


def _retry() -> tuple[int, list[int], list[int]]:
    """The install check's (tries, the waits inside its loop, the waits before it), read from its commands."""
    run = _run(_jobs()[INSTALL], INSTALL_STEP)
    commands = [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]
    loops = [i for i, c in enumerate(commands) if re.fullmatch(r"for attempt in [0-9 ]+; do", c)]
    assert len(loops) == 1, "expected one retry loop"
    start, end = loops[0], commands.index("done", loops[0])
    tries = len(commands[start].split()[3:-1])
    waits = [int(c.split()[1]) for c in commands[start:end] if re.fullmatch(r"sleep [0-9]+", c)]
    before = [int(c.split()[1]) for c in commands[:start] if re.fullmatch(r"sleep [0-9]+", c)]
    return tries, waits, before


class TestPublishDocsStateTheBounds:
    def test_the_json_checks_bounds(self):
        run = _run(_jobs()["testpypi"], INDEX_CHECK)
        attempts_match = re.search(r'"HASH_CHECK_ATTEMPTS", "(\d+)"', run)
        interval_match = re.search(r'"HASH_CHECK_INTERVAL", "(\d+)"', run)
        timeout_match = re.search(r"urllib\.request\.urlopen\(request, timeout=(\d+)\)", run)
        assert attempts_match and interval_match and timeout_match
        attempts, interval, timeout = int(attempts_match.group(1)), int(interval_match.group(1)), int(timeout_match.group(1))
        manual = _doc(MANUAL)
        # The poll, and the worst case: every sleep, and every request running to its timeout.
        assert f"polled up to {attempts} times {interval} seconds apart" in manual
        assert f"A JSON check that gives up after {attempts} attempts is index lag ({attempts - 1} sleeps of {interval} seconds, plus up to {attempts} request timeouts of {timeout} seconds)" in manual
        assert f"PyPI's JSON did not list the files within its {attempts} attempts" in manual
        assert f"A JSON check that gives up after {attempts} attempts is index lag" in _doc(CHEATSHEET)

    def test_the_install_checks_retry(self):
        tries, waits, before = _retry()
        # One loop: its tries, one wait between them, and one wait before the first.
        assert len(waits) == 1
        assert len(before) == 1
        wait, first = waits[0], before[0]
        manual = _doc(MANUAL)
        assert f"Wait {first} seconds for index sync" in manual
        assert f"up to {tries} tries {wait} seconds apart" in manual
        assert f"it sleeps {first} seconds, then tries the install up to {tries} times" in manual
        assert f"up to {tries} tries, {wait} s apart" in _doc(CICD_REFERENCE)
        reference = _doc(REFERENCE)
        assert f"sleep {first} for attempt in {' '.join(str(n) for n in range(1, tries + 1))}; do" in reference
        assert f"fi sleep {wait} done" in reference
        # The error the check stops with after its last try, as the step prints it and as the docs quote it.
        error = f"is not installable from TestPyPI after {tries} tries (index lag?)"
        assert error in _run(_jobs()[INSTALL], INSTALL_STEP)
        for name in (MANUAL, REFERENCE):
            assert error in _doc(name), name
'''
# ─────────────────────────────────────────────────────────────────────────────────────────────
# Docs and changelog: each edit an exact-once anchor; each doc's version gets a patch bump and its date the --date
# ─────────────────────────────────────────────────────────────────────────────────────────────
MANUAL_PATH = "docs/ci_cd/CICD_MANUAL.md"
CICD_REFERENCE_PATH = "docs/ci_cd/CICD_REFERENCE.md"
QUICK_START_PATH = "docs/ci_cd/CICD_QUICK_START.md"
CHEATSHEET_PATH = "docs/DEVELOPER_CHEATSHEET.md"
REFERENCE_PATH = "docs/REFERENCE.md"
CASCOR_MANUAL = "https://github.com/pcalnon/juniper-cascor/blob/main/docs/ci_cd/MANUAL.md"
LAG_QUOTE = "`… is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats`"

MANUAL_EDITS = (
    (
        "Triggered by a published GitHub Release whose tag starts with `v`. The package is built once, and TestPyPI and then production PyPI publish that one artifact, each upload checked by sha256: see [One artifact, checked against TestPyPI](#one-artifact-checked-against-testpypi). A `workflow_dispatch` from a release tag only republishes TestPyPI's files: see [Recovering a release that did not reach PyPI](#recovering-a-release-that-did-not-reach-pypi).\n",
        "Triggered by a published GitHub Release whose tag starts with `v`. The package is built once, and TestPyPI and then production PyPI publish that one artifact, each upload checked by sha256, with the install check between them in a job that cannot mint a credential: see [One artifact, checked against TestPyPI](#one-artifact-checked-against-testpypi). A `workflow_dispatch` from a release tag only republishes TestPyPI's files, and only for a release run whose TestPyPI jobs passed: see [Recovering a release that did not reach PyPI](#recovering-a-release-that-did-not-reach-pypi).\n",
    ),
    (
        "4. Wait 30 seconds for index sync\n5. Install from TestPyPI only (`--index-url https://test.pypi.org/simple/`, `--no-deps`, `juniper-data==<version>` with one leading `v` stripped from the tag) and print the installed version from its metadata. The print does not compare that version with the tag; the pip pin does. `import juniper_data` would fail a good publish, because `dotenv` is imported at import time and `--no-deps` does not install it. A second index does not fetch dependencies under `--no-deps`; it only widens which `juniper-data` pip will accept. A non-zero `pip` or `python` fails the step. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check).\n\n**Environment**: `testpypi` (no wait timer and no reviewer; deployments only from a release tag matching `v*`, `rc*`, `hf*`, `juniper-*-v*`, `juniper-*-rc*` or `juniper-*-hf*`)\n",
        "\n".join(
            (
                "",
                "The job holds `id-token: write` alone, and runs these steps alone: it checks nothing out and runs no install check.",
                "",
                "**Environment**: `testpypi` (no wait timer and no reviewer; deployments only from a release tag matching `v*`, `rc*`, `hf*`, `juniper-*-v*`, `juniper-*-rc*` or `juniper-*-hf*`)",
                "",
                "#### Stage 1b: Verify the TestPyPI install",
                "",
                "`Verify the TestPyPI install` is a job of its own (ruling 2 of 2026-11-16). It needs `Publish to TestPyPI` and holds `contents: read` alone, with no environment and no `id-token`, so nothing it installs or runs can mint a credential. It sets up Python 3.12, checks nothing out, and runs every command from `$RUNNER_TEMP`, outside any checkout (`python -c` puts its working directory first on `sys.path`, and this repository's root holds `juniper_data/`):",
                "",
                "1. Wait 30 seconds for index sync",
                f"2. Install from TestPyPI only (`--index-url https://test.pypi.org/simple/`, `--no-deps`, `juniper-data==<version>` with one leading `v` stripped from the tag, which the step reads through its `env`, `RELEASE_TAG`), up to 5 tries 10 seconds apart. The fifth failure fails the step with {LAG_QUOTE}",
                "3. Print the installed version from its metadata, and find the package with `importlib.util.find_spec`, which locates `juniper_data` without running it: the step fails, through `SystemExit`, unless the package is found with an origin, so a wheel that holds the metadata alone fails. The print does not compare that version with the tag; the pip pin does. `import juniper_data` would fail a good publish, because `dotenv` is imported at import time and `--no-deps` does not install it. A second index does not fetch dependencies under `--no-deps`; it only widens which `juniper-data` pip will accept. A non-zero `pip` (five times) or `python` fails the step. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check).",
                "",
                "Its name holds `TestPyPI`, so juniper-ml's release-train ceremony reads its failure as `HALT_TESTPYPI`, as it reads the TestPyPI job's.",
                "",
            )
        ),
    ),
    (
        "Downloads the same `juniper-data-dist`, checks it against `SHA256SUMS`, checks TestPyPI's JSON again (`Verify TestPyPI still serves exactly these files`), publishes to production PyPI, then checks PyPI's JSON (`Verify PyPI serves exactly these files`). It checks out and builds nothing. There is no install check.\n",
        "Needs both TestPyPI jobs, `Publish to TestPyPI` and `Verify the TestPyPI install`. Downloads the same `juniper-data-dist`, checks it against `SHA256SUMS`, checks TestPyPI's JSON again (`Verify TestPyPI still serves exactly these files`), publishes to production PyPI, then checks PyPI's JSON (`Verify PyPI serves exactly these files`). It checks out and builds nothing. There is no install check in it.\n",
    ),
    (
        "An index never takes a second file under a name it already holds, so TestPyPI's record witnesses what the install check tested. Only the jobs that upload hold `id-token: write`: the workflow grants nothing (`permissions: {}`), `Build and Validate` holds `contents: read` and `actions: read`, `Publish to TestPyPI` `contents: read` and `id-token: write`, `Publish to PyPI` `id-token: write`, the republish job `actions: read` and `id-token: write`, and `notify-consumers` nothing.\n",
        "An index never takes a second file under a name it already holds, so TestPyPI's record witnesses the files this run built and TestPyPI took: the install check installed their wheel; no check installs the sdist. Only the jobs that upload hold `id-token: write`: the workflow grants nothing (`permissions: {}`), `Build and Validate` holds `contents: read` and `actions: read`, `Publish to TestPyPI` `id-token: write` alone, `Verify the TestPyPI install` `contents: read` alone, `Publish to PyPI` `id-token: write`, the republish job `actions: read` and `id-token: write`, and `notify-consumers` nothing. So the job that can mint runs only the template steps and the upload, and the job that installs the package TestPyPI serves can mint nothing.\n",
    ),
    (
        "The steps marked `One-artifact publish template`, and the whole `republish` job, are juniper-cascor's `publish.yml` copied verbatim (juniper-cascor#763 and #767). They read nothing from this repository but the workflow `env` values `PUBLISH_PACKAGE` (`juniper-data`) and `PUBLISH_DIST_DIR` (`dist`), each JSON check's `INDEX_URL`, and the runner's own variables. `juniper_data/tests/unit/test_publish_one_artifact.py` pins the wiring and each job's exact steps, rehearses each template step's own Python, and pins each template step and the republish job, by digest, to juniper-cascor's `publish.yml` at `675884888f5a`, the commit this port copied. Those digests",
        "The steps marked `One-artifact publish template`, and the whole `republish` job, are juniper-cascor's `publish.yml` copied verbatim (juniper-cascor#763 and #767, swept by #777). They read nothing from this repository but the workflow `env` values `PUBLISH_PACKAGE` (`juniper-data`), `PUBLISH_DIST_DIR` (`dist`) and `PUBLISH_TAG_PREFIX` (`v`: every juniper-data release tag is `v<version>`, and the republish job takes the version from the rest of the tag; the build job's guard repeats the prefix, since a job-level `if:` cannot read `env`), each JSON check's `INDEX_URL`, and the runner's own variables. `juniper_data/tests/unit/test_publish_one_artifact.py` pins the wiring and each job's exact steps, rehearses each template step's own Python, and pins each template step and the republish job, by digest, to juniper-cascor's `publish.yml` at `f5ed30177766` (#777's merge), the commit this port copied: by the digest of each parsed step and, since this change, by the sha256 of each block's text, comments included, which the parsed digests cannot see. Each digest is taken with every `uses:` reduced to its action's name, so a Dependabot bump of an action needs no re-port (the test pins each action to one ref). Those digests",
    ),
    (
        "   Only `Republish the tested files (dispatch only)` runs, behind the same `pypi` gate (a fresh approval, then the 5-minute timer). It builds nothing: it downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It works only from a tag whose `publish.yml` carries the job, so not from a tag cut before this change.\n",
        "   Only `Republish the tested files (dispatch only)` runs, behind the same `pypi` gate (a fresh approval, then the 5-minute timer). Its first step then refuses unless the tag's newest release run of `publish.yml` exists and each of its jobs whose name holds `TestPyPI`, `Publish to TestPyPI` and `Verify the TestPyPI install`, concluded success in its latest attempt (ruling 1 of 2026-11-16). A re-run gives every job a record in the new attempt: one it runs again gets its new result, and one \"Re-run failed jobs\" carries over gets a copy of its earlier one, so each job counts with its newest result. Then it builds nothing: it downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. Once the artifact has expired, TestPyPI's JSON is the only record the files are checked against. It needs neither the release run's artifact nor its re-run window: only the run's record and TestPyPI still holding the files.\n",
    ),
    (
        "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run. The re-run reuses the run's artifact and waits at the gate again. GitHub refuses a re-run after 30 days.\n3. **Otherwise, cut a new patch version.**\n",
        "\n".join(
            (
                "2. **If that fails, within 30 days of the release run: \"Re-run failed jobs\"** on the release run. The re-run reuses the run's artifact and waits at the gate again (a fresh approval, then the 5-minute timer). GitHub refuses a re-run after 30 days.",
                "3. **Otherwise, cut a new patch version.**",
                "",
                "**When rung 1 refuses, or a release run failed before PyPI:**",
                "",
                "- **A TestPyPI job failed on index lag** (a JSON check gave up, or the install check stopped with `… is not installable from TestPyPI after 5 tries (index lag?)`, before TestPyPI served the version): within 30 days, \"Re-run failed jobs\" on the release run. It runs the failed job and those after it again. A re-run `Publish to TestPyPI` uploads the same bytes, from the run's artifact, which the index accepts (HTTP 200 for a byte-identical file), and repeats its JSON check; the install check then runs again. Once both pass, the PyPI job waits at the gate as usual, and rung 1 has a release run to accept.",
                "- **The install check failed for real** (the package does not install, or its check fails, and a re-run fails the same way): cut a new patch version. If unsure, Re-run failed jobs first: index lag passes on a re-run, and a real failure repeats. Neither a re-run nor a same-version re-cut can fix a real failure, because the index refuses new bytes under a file name it already holds.",
                "- **A Release that was re-cut**: never delete a Release and publish it again to retry; use \"Re-run failed jobs\". A re-cut starts a new release run, which builds again. Once TestPyPI holds the version, it refuses the new run's files (it holds those file names), and that failed run is then the tag's newest release run, so rung 1 refuses the tag for good: what is left is \"Re-run failed jobs\" on the original release run, within 30 days of it, then a new patch version.",
                "- **A tag that is not `v` followed by the exact version**: the republish takes the version from the tag (`PUBLISH_TAG_PREFIX`, then the version), so such a tag cannot be republished, and the job fails without publishing.",
                "",
                "A failed `Verify PyPI serves exactly these files` is not in that list: the step runs after the upload, so this run's files are already on PyPI. It has two causes, and only one needs a new version. If PyPI lists a file this run did not build, or one with another sha256, find which upload put it there; only a new patch version ships tested files under a clean version. If the check gave up waiting (PyPI's JSON did not list the files within its 20 attempts), that is index lag: \"Re-run failed jobs\" on the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run, uploads the same bytes again, which the index accepts, and repeats the check; re-running a job behind the `pypi` gate needs a fresh approval, then the 5-minute timer. The PyPI job's `Verify TestPyPI still serves exactly these files` giving up waiting, before the upload, takes the same re-run, on the release run.",
                "",
                "Each rung acts on the workflow file as of the tag: a tag cut before juniper-data#543 merged (2026-11-16) has no rung 1, and one cut before this change runs rung 1 without the check of the release run's TestPyPI jobs.",
                "",
            )
        ),
    ),
    (
        "The build job's reuse step now skips such a rebuild, but a tag cut before this change lacks it.",
        "The build job's reuse step now skips such a rebuild, but a tag cut before juniper-data#543 lacks it.",
    ),
    (
        "then install-tests (no environment wait; the job sleeps 30 seconds before the install check)\n4. **PyPI stage**: requires manual reviewer approval,",
        "then `Verify the TestPyPI install`, a job of its own with `contents: read` alone, install-tests it (no environment wait; it sleeps 30 seconds, then tries the install up to 5 times)\n4. **PyPI stage**: needs both TestPyPI jobs and requires manual reviewer approval,",
    ),
    (
        "A JSON check that gives up after 20 attempts is index lag (19 sleeps of 15 seconds, plus up to 20 request timeouts of 30 seconds): use **Re-run failed jobs**, since an index accepts a re-upload of identical files.",
        "A JSON check that gives up after 20 attempts is index lag (19 sleeps of 15 seconds, plus up to 20 request timeouts of 30 seconds): use **Re-run failed jobs** on the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run, since an index accepts a re-upload of identical files.",
    ),
    (
        "The install check uses only `https://test.pypi.org/simple/` and `--no-deps`. Do not add a second index. The following Python line prints installed metadata; it does not compare it with the tag, and `import juniper_data` is the wrong check (`dotenv` is not installed).",
        "The install check (`Verify the TestPyPI install`, a job of its own) uses only `https://test.pypi.org/simple/` and `--no-deps`. Do not add a second index. Its Python line prints installed metadata and finds the package with `importlib.util.find_spec`, without running it; it does not compare the version with the tag, and `import juniper_data` is the wrong check (`dotenv` is not installed).",
    ),
)

CICD_REFERENCE_EDITS = (
    (
        "| `testpypi` | build | `testpypi` | Check the artifact against `SHA256SUMS`, publish it to TestPyPI, require TestPyPI's JSON to list exactly those sha256, then install `juniper-data==<version>` from `https://test.pypi.org/simple/` only (`--no-deps`). The next line prints installed metadata; it does not compare it with the tag. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check) |\n| `pypi` | testpypi | `pypi` |",
        "| `testpypi` | build | `testpypi` | Check the artifact against `SHA256SUMS`, publish it to TestPyPI, require TestPyPI's JSON to list exactly those sha256. Holds `id-token: write` alone: it checks nothing out and runs no install check |\n"
        "| `verify-testpypi-install` | testpypi | -- (`contents: read` alone) | `Verify the TestPyPI install` (ruling 2 of 2026-11-16): from `$RUNNER_TEMP`, outside any checkout, install `juniper-data==<version>` from `https://test.pypi.org/simple/` only (`--no-deps`; up to 5 tries, 10 s apart, then an error naming index lag), print the installed metadata and find the package with `importlib.util.find_spec`, failing unless it is found with an origin. It does not compare the version with the tag. No `id-token`, so nothing it runs can mint a credential. See [TestPyPI install check](../REFERENCE.md#testpypi-install-check) |\n"
        "| `pypi` | testpypi, verify-testpypi-install | `pypi` |",
    ),
    (
        "copy TestPyPI's files for the version to PyPI, then check PyPI's JSON. Builds nothing. See [Recovering a release that did not reach PyPI](CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) |",
        "copy TestPyPI's files for the version to PyPI, then check PyPI's JSON, and only once the tag's newest release run passed both TestPyPI jobs in their latest attempt (ruling 1 of 2026-11-16). Builds nothing. See [Recovering a release that did not reach PyPI](CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) |",
    ),
    (
        "`testpypi` `contents: read`, `id-token: write` (OIDC); `pypi` `id-token: write`;",
        "`testpypi` `id-token: write` (OIDC); `verify-testpypi-install` `contents: read`; `pypi` `id-token: write`;",
    ),
)

QUICK_START_EDITS = (
    (
        "It copies TestPyPI's files to PyPI behind the same approval and builds nothing. A dispatch runs the workflow file at its tag, so a tag cut before this change (2026-11-15) has no republish dispatch. If that fails, within 30 days of the release run use **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version.",
        "It copies TestPyPI's files to PyPI behind the same approval and builds nothing, and it refuses unless the tag's newest release run passed both its TestPyPI jobs (`Publish to TestPyPI` and `Verify the TestPyPI install`) in their latest attempt. A dispatch runs the workflow file at its tag, so a tag cut before juniper-data#543 merged (2026-11-16) has no republish dispatch. If that fails, within 30 days of the release run use **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version. A TestPyPI job that failed on index lag takes **Re-run failed jobs** too; an install check that fails for real takes a new patch version.",
    ),
)

CHEATSHEET_EDITS = (
    (
        "A JSON check that gives up after 20 attempts is index lag: **Re-run failed jobs**.",
        "A JSON check that gives up after 20 attempts is index lag: **Re-run failed jobs** on the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run.",
    ),
    (
        "Keep `--index-url https://test.pypi.org/simple/` and `juniper-data==<version>`. The step prints metadata; it does not compare that version with the tag.",
        "Keep `--index-url https://test.pypi.org/simple/` and `juniper-data==<version>`. The step prints metadata and finds the package with `find_spec`; it does not compare that version with the tag.",
    ),
    (
        "(copies TestPyPI's files, builds nothing; a tag cut before this change, 2026-11-15, has no republish dispatch); if that fails, within 30 days of the release run, **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version.",
        "(copies TestPyPI's files, builds nothing, and refuses unless the tag's newest release run passed both TestPyPI jobs; a tag cut before juniper-data#543, 2026-11-16, has no republish dispatch); if that fails, within 30 days of the release run, **Re-run failed jobs** on it (never \"Re-run all jobs\"); otherwise cut a new patch version. A TestPyPI job that failed on index lag: **Re-run failed jobs**; an install check that fails for real: a new patch version.",
    ),
)

REFERENCE_EDITS = (
    (
        "its JSON must list exactly those sha256, and an install check follows; then PyPI",
        "its JSON must list exactly those sha256, and an install check follows, in a job of its own that cannot mint a credential; then PyPI",
    ),
    (
        "The dispatch republishes TestPyPI's files: [Recovering a release that did not reach PyPI](ci_cd/CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) | None |",
        "The dispatch republishes TestPyPI's files, once the release run passed both TestPyPI jobs: [Recovering a release that did not reach PyPI](ci_cd/CICD_MANUAL.md#recovering-a-release-that-did-not-reach-pypi) | None |",
    ),
    (
        "`publish.yml`'s `testpypi` job ends with `Verify TestPyPI install`, after `Verify TestPyPI serves exactly these files` has matched TestPyPI's files to the sha256 the build recorded. The production `pypi` job waits on that job. The step names no `shell:` and no `continue-on-error`.\n\nThe release tag is stripped of one leading `v`, then:\n\n```bash\nsleep 30\npip install --no-deps --index-url https://test.pypi.org/simple/ juniper-data==${VERSION}\npython -c \"import importlib.metadata as m; print('TestPyPI OK: v' + m.version('juniper-data'))\"\n```\n\n`sleep 30` is the wait for TestPyPI index lag. The pip requirement is what selects the released version. The Python line only reads the installed distribution's metadata and prints it. It does not compare that string with the tag.",
        "\n".join(
            (
                "`publish.yml`'s `verify-testpypi-install` job, `Verify the TestPyPI install`, runs `Verify TestPyPI install` after the `testpypi` job, whose `Verify TestPyPI serves exactly these files` has matched TestPyPI's files to the sha256 the build recorded (ruling 2 of 2026-11-16). The job holds `contents: read` alone, with no environment and no `id-token`, so nothing it installs or runs can mint a credential, and it checks nothing out. The production `pypi` job needs both jobs. The step names no `shell:` and no `continue-on-error`.",
                "",
                "The step reads the release tag through its `env`, `RELEASE_TAG`, so no expression is pasted into the script, and strips one leading `v`. It runs from `$RUNNER_TEMP`, outside any checkout: `python -c` puts its working directory first on `sys.path`, and this repository's root holds `juniper_data/`. Its commands, the pip line joined and the retry's message left out (the workflow is the source; `juniper_data/tests/unit/test_publish_one_artifact.py` pins it line by line):",
                "",
                "```bash",
                'cd "${RUNNER_TEMP}"',
                'VERSION="${RELEASE_TAG#v}"',
                "sleep 30",
                "for attempt in 1 2 3 4 5; do",
                '  if pip install --no-deps --index-url https://test.pypi.org/simple/ "juniper-data==${VERSION}"; then',
                "    break",
                "  fi",
                '  if [ "${attempt}" -eq 5 ]; then',
                '    echo "::error::juniper-data ${VERSION} is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"',
                "    exit 1",
                "  fi",
                "  sleep 10",
                "done",
                "python -c \"import importlib.metadata as m, importlib.util as u; spec = u.find_spec('juniper_data'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('juniper-data'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no juniper_data package')\"",
                "```",
                "",
                "`sleep 30` is the wait for TestPyPI index lag, and the five tries cover TestPyPI's simple index lagging behind its JSON. The pip requirement is what selects the released version. The Python line reads the installed distribution's metadata and prints it, and `importlib.util.find_spec` locates `juniper_data` without running it: the step fails, through `SystemExit` (which `PYTHONOPTIMIZE` keeps, where it would strip an `assert`), unless the package is found with an origin, so a wheel that holds the metadata alone, or a bare directory, fails. It does not compare the version with the tag.",
            )
        ),
    ),
    (
        "A non-zero `pip` or `python` fails the step, so `pypi` does not start.",
        "A `pip` that fails five times, or a non-zero `python`, fails the step, so `pypi` does not start.",
    ),
)

DOC_EDITS = {
    MANUAL_PATH: MANUAL_EDITS,
    CICD_REFERENCE_PATH: CICD_REFERENCE_EDITS,
    QUICK_START_PATH: QUICK_START_EDITS,
    CHEATSHEET_PATH: CHEATSHEET_EDITS,
    REFERENCE_PATH: REFERENCE_EDITS,
}
#: How many times each doc states its version and its date (a header, and a footer where it has one).
DOC_STAMPS = {MANUAL_PATH: 1, CICD_REFERENCE_PATH: 2, QUICK_START_PATH: 2, REFERENCE_PATH: 2}


def bump_stamps(text: str, rel: str, date: datetime.date) -> str:
    """A patch bump of the doc's version, and the date, in each place the doc states them (all of them must agree)."""
    if rel == CHEATSHEET_PATH:
        found = re.findall(r"^\*\*Version\*\*: (\d+)\.(\d+)\.(\d+) \| \*\*Date\*\*: (\d{4}-\d{2}-\d{2}) \|", text, flags=re.MULTILINE)
        if len(found) != 1:
            raise Refused(f"{rel}: its version-and-date line is missing or repeated")
        major, minor, patch, day = found[0]
        return replace_once(text, f"**Version**: {major}.{minor}.{patch} | **Date**: {day} |", f"**Version**: {major}.{minor}.{int(patch) + 1} | **Date**: {date.isoformat()} |", rel)
    count = DOC_STAMPS[rel]
    versions = sorted(set(re.findall(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)$", text, flags=re.MULTILINE)))
    if len(versions) != 1:
        raise Refused(f"{rel}: its **Version:** lines disagree or are missing: {versions}")
    major, minor, patch = versions[0]
    text = replace_each(text, f"**Version:** {major}.{minor}.{patch}\n", f"**Version:** {major}.{minor}.{int(patch) + 1}\n", count, rel)
    dated = sorted({line for line in text.splitlines(keepends=True) if line.startswith("**Last Updated:** ")})
    if len(dated) != 1:
        raise Refused(f"{rel}: its '**Last Updated:** ' lines disagree or are missing: {dated}")
    return replace_each(text, dated[0], f"**Last Updated:** {date:%B} {date.day}, {date.year}\n", count, rel)


def docs_edits(read, date: datetime.date) -> "dict[str, str]":
    """Each doc's edits, then its version's patch bump and its date. The new text names no person."""
    out: dict[str, str] = {}
    for rel, edits in DOC_EDITS.items():
        text = read(rel)
        for old, new in edits:
            if any(word in new and word not in old for word in WORDS):
                raise Refused(f"{rel}: an edit's new text names the person: {new[:80]!r}")
            text = replace_once(text, old, new, rel)
        out[rel] = bump_stamps(text, rel, date)
    return out


CHANGELOG_ENTRY = """\
- **The republish job copies nothing a release run did not pass, and the install check can mint no credential**
  (rulings 1 and 2 of 2026-11-16; the port of juniper-cascor#777, the one-artifact template's sweep, to
  juniper-data#543's entry below, template verbatim).
  - **The install check has a job of its own** (ruling 2). `Verify the TestPyPI install` needs `Publish to TestPyPI`,
    and `Publish to PyPI` needs both. It installs the package TestPyPI serves, so it holds `contents: read` alone: no
    environment and no `id-token`. Until now the check ran in the TestPyPI job, so pip and the check ran with that
    job's OIDC token-request variables in their environment (the check read only the package's metadata). It keeps its
    `setup-python` (3.12), its `--no-deps` install from TestPyPI alone and its metadata check, now run from
    `$RUNNER_TEMP`; it reads the release's tag through the step's `env`, never pasted into the script by an expression,
    and it checks nothing out. `Publish to TestPyPI` drops its checkout and `setup-python` and holds `id-token: write`
    alone, so the job that can mint runs only the template steps and the upload. The new job's name holds "TestPyPI",
    so juniper-ml's release-train ceremony reads its failure as `HALT_TESTPYPI`.
  - **The install retries, then names index lag.** After its 30 s wait it makes the template's 5 tries, 10 s apart,
    and after the fifth failed install fails with "… is not installable from TestPyPI after 5 tries (index lag?):
    Re-run failed jobs; a real failure repeats".
  - **The check finds the package, not only its metadata** (R4-5 of the sweep's review). `importlib.util.find_spec`
    locates `juniper_data` without running it (an import needs `python-dotenv`, absent under `--no-deps`), and the
    check fails unless it is found with an origin, through `SystemExit`, which `PYTHONOPTIMIZE` keeps where it would
    strip an `assert`. A wheel that held the metadata alone passed before. The line it prints names the version and
    where the package was found, with no "OK" before the check has passed.
  - **The republish job refuses unless the tag's release run passed its TestPyPI jobs** (ruling 1).
    `Find the release run's artifact` takes the tag's newest release run, whether or not its artifact has expired, and
    refuses unless `Publish to TestPyPI` and `Verify the TestPyPI install` concluded success in their latest attempt
    (`GET actions/runs/{id}/jobs?filter=all`, each job's record with the highest attempt); it refuses as well when the
    tag has no release run. Until now it copied TestPyPI's files whatever the release run's jobs concluded.
  - **`PUBLISH_TAG_PREFIX: v`**, the template's third parameter: the republish job takes the version from a tag only
    after it, so a `juniper-data-v<version>` tag is refused before any request. The build guard repeats the prefix,
    since a job-level `if:` cannot read `env`, and its comment notes that a future `rc*` or `hf*` tag convention must
    widen it.
  - **Comments**, from the template: the republish job's no longer says the ceremony never reads a dispatch run (since
    juniper-ml#2592 its monitor does), and the PyPI job's says TestPyPI's record witnesses the files the run built,
    whose wheel the install check installed.
  - **`notify-consumers` is unchanged** (`needs: pypi`) and `notify-consumers.yml` is not touched: a republish dispatch
    still skips it, and `docs/ci_cd/CICD_MANUAL.md` gives the `gh workflow run notify-consumers.yml` command that
    re-sends it once the republish's `Verify PyPI serves exactly these files` passes.
  - **Docs.** `docs/ci_cd/CICD_MANUAL.md` (0.4.10), `docs/ci_cd/CICD_REFERENCE.md` (0.4.10), `docs/REFERENCE.md`
    (0.4.13), `docs/ci_cd/CICD_QUICK_START.md` (0.4.7) and `docs/DEVELOPER_CHEATSHEET.md` (0.4.9) state the install
    job and the republish job's gate, and the ladder's new facts: when rung 1 refuses; that a TestPyPI job which failed
    on index lag is re-run ("Re-run failed jobs" uploads the same bytes, which the index accepts) while a failed
    install check needs a new patch version; that a failed `Verify PyPI serves exactly these files` comes after the
    upload, where a mismatch needs a new patch version and a check that gave up waiting takes "Re-run failed jobs" on
    the run whose check gave up (the release run, or the republish's dispatch run), within 30 days of that run; and
    which tags the ladder covers.
  - **Pins**, in `juniper_data/tests/unit/test_publish_one_artifact.py` ({cases} cases, 67 before): the new job's
    name, `needs`, permissions and lack of an environment; the PyPI job needing both TestPyPI jobs; each job's keys,
    runner and exact steps, each by its name and action; no `continue-on-error` and no `if:` beyond the listed ones;
    no `PIP_*` variable in any `env`; each build step's command; the install step's exact script and commands, run from
    `$RUNNER_TEMP`; no `skip_existing` and no `attestations: false`; retention of exactly 90 days; the workflow's name
    ending in "to PyPI"; and the prefix with its guard. The template steps and the republish job are pinned, as
    before, by the digest of each parsed step, now taken at `f5ed30177766` (#777's merge), and, new, by the sha256 of
    each block's text, comments included: a YAML comment outside a run script was invisible to the parsed digests and
    to juniper-ml's cross-repo checker, which compares parsed YAML. Both are taken with every `uses:` reduced to its
    action's name (SWEEP item 23), so a Dependabot bump of an action needs no re-port, and a new case pins each action
    to one ref. The rehearsals run the new find step against the stand-in GitHub API (no release run, a failed
    upload, a failed or unfinished install check, a failed build, a job a re-run carried over, with and without
    GitHub's copies, a failure a re-run repaired, a "Re-run all jobs" whose second attempt failed, each listing order,
    a listing over two pages, an older run that passed behind a newer one that failed, and both prefixes), the fetch
    step against a release run and a TestPyPI that name different files, the install step's own shell against stand-in
    `pip`, `python` and `sleep`, and its package check against a real interpreter, `PYTHONOPTIMIZE` set or not.
    The new `juniper_data/tests/unit/test_publish_docs_bounds.py` (2 cases), the port of #777's, reads the JSON
    checks' polls, interval and request timeout and the install check's tries and waits from `publish.yml`, and
    requires the docs to state them. `test_testpypi_install_verify.py` follows the step into its job: the tag
    through `RELEASE_TAG`, the check run from `$RUNNER_TEMP`, and five failed installs before the lag error. Each of
    {mutations} edits to a copy of the workflow (five of them to a copy of a doc), one at a time, fails the tests.
"""


def changelog(text: str, entry: str) -> str:
    """Insert the entry first under ``[Unreleased]``'s ``### Fixed``, which lists the newest first (creating it if a
    release emptied it)."""
    start = text.find("## [Unreleased]\n")
    if start < 0 or text.count("## [Unreleased]\n") != 1:
        raise Refused(f"{CHANGELOG_PATH}: no single '## [Unreleased]' heading")
    end = text.find("\n## [", start + 1)
    end = len(text) if end < 0 else end + 1
    section = text[start:end]
    fixed = section.find("\n### Fixed\n\n")
    if fixed < 0:
        new_section = section.rstrip("\n") + "\n\n### Fixed\n\n" + entry + "\n"
    else:
        cut = fixed + len("\n### Fixed\n\n")
        new_section = section[:cut] + entry + "\n" + section[cut:]
    return text[:start] + new_section + text[end:]


def test_module(base: str, path: str, want_sha: str, module: str) -> str:
    """A test module written whole, over the base it was derived from only."""
    if sha256(base) != want_sha:
        raise Refused(f"{path} hashes to {sha256(base)}, not the base this port was derived from ({want_sha}): main moved it, so re-derive the test module rather than overwrite that change")
    return module


def apply(tree: Path, template: str, date: datetime.date, cases: str, mutations: str) -> "dict[str, str]":
    """Return {repo path: new text} for every file the port writes; raise Refused if any edit does not apply."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    if sha256(template) != TEMPLATE_SHA256:
        raise Refused(f"the template hashes to {sha256(template)}, not juniper-cascor 5e3d9801's publish.yml: re-derive the port")
    if sha256(read(NOTIFY_PATH)) != NOTIFY_SHA256:
        raise Refused(f"{NOTIFY_PATH} is not the file juniper-ml's checker pins ({NOTIFY_SHA256}): re-derive the port")
    check_install_lines()
    out: dict[str, str] = {}
    current = read(WORKFLOW_PATH)
    if sha256(current) != BASE_WORKFLOW_SHA256:
        print(f"note: {WORKFLOW_PATH} moved since the base this was derived on (8e08d209); applying by anchors")
    out[WORKFLOW_PATH] = publish_workflow(current, template)
    check_workflow(out[WORKFLOW_PATH])
    out[TEST_PATH] = test_module(read(TEST_PATH), TEST_PATH, BASE_TEST_SHA256, TEST_MODULE)
    check_test_digests(out[TEST_PATH], template)
    out[INSTALL_TEST_PATH] = test_module(read(INSTALL_TEST_PATH), INSTALL_TEST_PATH, BASE_INSTALL_TEST_SHA256, INSTALL_TEST_MODULE)
    if (tree / DOCS_BOUNDS_TEST_PATH).exists():
        raise Refused(f"{DOCS_BOUNDS_TEST_PATH} exists already: main added one, so re-derive the port rather than overwrite it")
    out[DOCS_BOUNDS_TEST_PATH] = DOCS_BOUNDS_TEST_MODULE
    # #206's review, R7: both counts are given, as numbers, and no placeholder is left in the entry.
    for label, value in (("--changelog-cases", cases), ("--changelog-mutations", mutations)):
        if not re.fullmatch(r"[1-9][0-9]*", value):
            raise Refused(f"{label} must be a positive whole number, not {value!r}")
    if CHANGELOG_ENTRY.count("{cases}") != 1 or CHANGELOG_ENTRY.count("{mutations}") != 1:
        raise Refused("CHANGELOG_ENTRY does not hold each placeholder once")
    entry = CHANGELOG_ENTRY.replace("{cases}", cases).replace("{mutations}", mutations)
    leftover = [placeholder for placeholder in ("{cases}", "{mutations}") if placeholder in entry]
    if leftover:
        raise Refused(f"{CHANGELOG_PATH}: the entry still holds {leftover}")
    if any(word in entry for word in WORDS):
        raise Refused(f"{CHANGELOG_PATH}: the entry names the person")
    out[CHANGELOG_PATH] = changelog(read(CHANGELOG_PATH), entry)
    out.update(docs_edits(read, date))
    for rel, text in out.items():
        if rel != DOCS_BOUNDS_TEST_PATH and text == read(rel):
            raise Refused(f"{rel}: the port changes nothing (a second run on a ported tree?)")
    return out


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help=f"a fresh clone of {REPO}'s main (edited in place)")
    parser.add_argument("--template", type=Path, default=TEMPLATE_DEFAULT, help="juniper-cascor's .github/workflows/publish.yml at main 5e3d9801 (default: the sweep's clone)")
    parser.add_argument("--date", type=datetime.date.fromisoformat, default=datetime.datetime.now(datetime.timezone.utc).date(), help="the day the edited docs' dates take (default: today, UTC)")
    # #206's review, R7: required, so a replay can never write a placeholder into CHANGELOG.md.
    parser.add_argument("--changelog-cases", required=True, help="the case count of test_publish_one_artifact.py the CHANGELOG entry states")
    parser.add_argument("--changelog-mutations", required=True, help="the mutation count the CHANGELOG entry states")
    args = parser.parse_args(argv)
    try:
        out = apply(args.tree, args.template.read_text(encoding="utf-8"), args.date, args.changelog_cases, args.changelog_mutations)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    for rel, text in sorted(out.items()):
        target = args.tree / rel
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(text, encoding="utf-8")
        print(f"wrote {rel} ({sha256(before)[:12]} -> {sha256(text)[:12]})")
    print(f"install step pin: sha256 {sha256(chr(10).join(INSTALL_LINES))} ({len(INSTALL_LINES)} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
