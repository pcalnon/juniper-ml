#!/usr/bin/env python3
"""Apply the one-artifact template sweep to a fresh juniper-cascor tree, every edit an anchor asserted to match once.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (the one-artifact template sweep, juniper-cascor first; brief tmp/ports/SWEEP_BRIEF.md)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py (juniper-cascor#763 / #767, the template this sweeps);
         util/ad-hoc/2026-11-23_publish_port_template_identity.py (the cross-repo checker the swept template passes);
         notes/JUNIPER_2026-06-18_JUNIPER-ECOSYSTEM_PYPI-PUBLISH-PROCEDURE.md

Why
---
``util/open_signed_pr.py`` uploads WHOLE files, so an edit made on a tree that ``main`` has since moved past silently
reverts whatever merged in between. Every edit here is therefore replayable on a fresh tree, and refuses (writing
nothing) when its anchor does not match exactly once. It has to apply both to juniper-cascor ``main`` before and after
juniper-cascor#772, which renames the person-word in comments and docs: the word is read from ``publish.yml`` at run
time ("The Overtoad's recovery ladder" or "The owner's recovery ladder"), every anchor that contains it is built from
that value, and the new text avoids it. The edits:

- Ruling 2 of 2026-11-16 (SWEEP items 6 and 10): the install check leaves the TestPyPI job for a job of its own,
  ``Verify the TestPyPI install`` (``contents: read`` alone; it installs and imports from ``$RUNNER_TEMP``), which the
  PyPI job needs. The TestPyPI job keeps the template steps and the upload, and holds ``id-token: write`` alone.
- Ruling 1 of 2026-11-16 (items 11, 21, 26): the republish job's ``Find the release run's artifact`` refuses unless
  the tag's newest release run exists and its TestPyPI jobs concluded success in their latest attempt.
- ``PUBLISH_TAG_PREFIX`` (items 3, 22), the comment corrections (items 1, 2, 12), the test hardening (items 4, 5, 8,
  9, 14, 17, 19), the docs (items 7, 11, 15, 20, 21, 26) and one ``[Unreleased]`` CHANGELOG entry.
- The review round of 2026-11-23 (tmp/sweep/REVIEW_DISPOSITIONS.md): the workflow lens's M1 (each install check makes
  5 tries, 10 s apart, then fails naming index lag; publish.yml gets the loop), M2 (the find step's comment and log
  describe the copies "Re-run failed jobs" makes), M3 and N7 (docs), M4 (a sub-package's plain dispatch builds only
  from its own tag), M6 (the protocol check finds the package), N1 (publish.yml reads the tag through ``env``), N2
  (the sparse checkout keeps no credential), N3 (a comment) and N4 (every PyPI job holds ``id-token: write`` alone);
  and the test lens's pins (exact install commands, job keys and runners, build commands, one ref per action, and the
  find, fetch and install rehearsals it asked for), with the docs' bounds in a new module, ``test_publish_docs_bounds.py``
  (``DOCS_TEST``, written whole). M5 and N6 are deferred (SWEEP items 28, 29).
- The round-2 review (the same file, § Round-2 review): F5, F8a and F8d (the MANUAL's dispatch and re-cut sentences
  say when they hold), F8b (the protocol check fails through ``SystemExit``, which ``PYTHONOPTIMIZE`` keeps), F8e
  (TestPyPI's record witnesses the files; the install check installs their wheel), F6 (the docs pins compare text
  with whitespace normalized) and F7 (the key pins admit ``run-name``, ``timeout-minutes`` and a ``concurrency``
  group without ``cancel-in-progress``).
- The round-4 review (the same file, § Round-4 review): R4-4 (a ``concurrency`` group is admitted at the workflow
  level alone: by default a job's group cancels a pending job of its own when another queues, which could stop a run
  between its two uploads), and the NITs (the key pins' comments say the republish job stays identical in every publisher; the
  CHANGELOG entry's wording; #767's entry corrected in place, ``CHANGELOG_767_*``).
- The round-5 review (the same file, § Round-5 review): its NIT 8 (a workflow ``concurrency`` group still cancels an
  older PENDING run when a newer one queues, so the CHANGELOG says "without ``cancel-in-progress``", which is what the
  pins admit, instead of "never cancels a run").

    python3 -I util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py --tree <fresh cascor tree> \\
        [--date YYYY-MM-DD] [--changelog-cases N] [--changelog-mutations M]

``--date`` (default: today, UTC) is the day the edited docs' ``Last Updated`` / ``Date`` lines take; the MANUAL and
cheatsheet versions are bumped from whatever the tree holds. The test file's edits (``TEST_EDITS``) were derived hunk
by hunk from the reviewed new file, each widened by whole lines until it matched exactly once on both bases.

Exit status: 0 when every edit applied; 1 when an anchor did not match exactly once or a post-condition failed
(nothing written).
"""

from __future__ import annotations

import argparse
import ast
import datetime
import hashlib
import re
import sys
from pathlib import Path

PUBLISH = ".github/workflows/publish.yml"
MODEL = ".github/workflows/publish-cascor-model.yml"
PROTOCOL = ".github/workflows/publish-protocol.yml"
#: workflow -> (PUBLISH_PACKAGE, the TestPyPI job's id, the PyPI job's id, PUBLISH_TAG_PREFIX)
PUBLISHERS = {
    PUBLISH: ("juniper-cascor", "testpypi", "pypi", "v"),
    MODEL: ("juniper-cascor-model", "publish-testpypi", "publish-pypi", "juniper-cascor-model-v"),
    PROTOCOL: ("juniper-cascor-protocol", "publish-testpypi", "publish-pypi", "juniper-cascor-protocol-v"),
}
INSTALL_JOB = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
TEST_PATH = "src/tests/unit/test_publish_one_artifact.py"
WORDS = ("Overtoad", "owner")


class Refused(Exception):
    """An edit could not be applied exactly; nothing is written."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_once(text: str, old: str, new: str, where: str) -> str:
    count = text.count(old)
    if count != 1:
        raise Refused(f"{where}: anchor matched {count} times, expected 1: {old[:90]!r}")
    return text.replace(old, new)


def detect_word(publish_yml: str) -> str:
    """The person-word the base uses: "Overtoad" once juniper-cascor#772 merged, else "owner"."""
    found = [word for word in WORDS if f"  # The {word}'s recovery ladder, step 1 (2026-11-15)" in publish_yml]
    if len(found) != 1:
        raise Refused(f"publish.yml: the republish banner names {found or 'neither'} of {WORDS}")
    return found[0]


def action_pin(text: str, action: str, where: str) -> str:
    """The one ``<action>@<sha>  # vX.Y.Z`` pin a workflow uses (Dependabot bumps every copy in a file together)."""
    pins = set(re.findall(rf"{re.escape(action)}@[0-9a-f]{{40}}  # v[0-9][0-9.]*", text))
    if len(pins) != 1:
        raise Refused(f"{where}: {len(pins)} distinct {action} pins, expected 1: {sorted(pins)}")
    return pins.pop()


def republish_job(text: str, where: str) -> str:
    """The whole republish job, from the comment banner above it to the end of the file."""
    lines = text.splitlines(keepends=True)
    at = [i for i, line in enumerate(lines) if line == "  republish:\n"]
    if len(at) != 1:
        raise Refused(f"{where}: {len(at)} republish jobs")
    start = at[0]
    while start > 0 and lines[start - 1].startswith("  #"):
        start -= 1
    return "".join(lines[start:]).rstrip("\n") + "\n"


# ─────────────────────────────────────────────────────────────────────────────────────────────
# The template: the republish job's comment (item 1) and its first step (ruling 1, PUBLISH_TAG_PREFIX), in all three
# ─────────────────────────────────────────────────────────────────────────────────────────────
REPUBLISH_COMMENT_OLD = """\
    # No "pypi" in this name, on purpose: juniper-ml's release-train ceremony tells a run's publish jobs apart by the
    # substrings "testpypi" and "pypi" in their names, and this job is skipped in every release run, so it must count
    # as neither. A dispatch run is not a release-event run, and the ceremony never reads one.
"""
REPUBLISH_COMMENT_NEW = """\
    # No "testpypi" or "pypi" in this name, on purpose: juniper-ml's release-train ceremony tells a run's publish jobs
    # apart by those substrings in their names, and this job is skipped in every release run, so it must count as
    # neither: counted as a PyPI job, its skipped record would keep the ceremony's check for a PyPI job parked at the
    # gate from ever passing. Since juniper-ml#2592 the ceremony's monitor also reads this workflow's dispatch runs on
    # the tag, and it classifies a republish run by the run's own status: waiting, success or failure.
"""

FIND_OLD = r"""      # One-artifact publish template, republish step 1: the version from the tag, and the release run's artifact.
      - name: Find the release run's artifact
        id: original
        shell: python3 {0}
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # One-artifact publish template (juniper-cascor publish.yml): copy verbatim; it reads PUBLISH_PACKAGE and the
          # runner's GITHUB_* variables. The dispatch runs on the release tag, v<version> or <package>-v<version> (the
          # pypi environment admits tags only), and the version comes from it. The newest release run of this workflow
          # for that tag that still holds an unexpired <package>-dist made the files: its SHA256SUMS is checked against
          # TestPyPI's JSON as well. An API failure fails the job rather than skip that check unannounced.
          import json
          import os
          import sys
          import urllib.parse
          import urllib.request

          package = os.environ["PUBLISH_PACKAGE"]
          tag = os.environ["GITHUB_REF_NAME"]
          version = ""
          if os.environ.get("GITHUB_REF_TYPE") == "tag" and tag.startswith(f"{package}-v"):
              version = tag[len(package) + 2 :]
          elif os.environ.get("GITHUB_REF_TYPE") == "tag" and tag.startswith("v"):
              version = tag[1:]
          if not version:
              print(f"::error::run this dispatch from a release tag of {package} (v<version> or {package}-v<version>), not {os.environ.get('GITHUB_REF')}")
              sys.exit(1)
          api = f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}"
          workflow = os.environ["GITHUB_WORKFLOW_REF"].split("@", 1)[0].rsplit("/", 1)[-1]
          headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {os.environ['GH_TOKEN']}", "X-GitHub-Api-Version": "2022-11-28"}


          def get(path):
              with urllib.request.urlopen(urllib.request.Request(f"{api}/{path}", headers=headers), timeout=30) as response:
                  return json.load(response)


          name = f"{package}-dist"
          found = ""
          runs = get(f"actions/workflows/{workflow}/runs?" + urllib.parse.urlencode({"event": "release", "branch": tag, "per_page": 30}))["workflow_runs"]
          for run in sorted((r for r in runs if r["head_branch"] == tag), key=lambda r: r["id"], reverse=True):
              artifacts = get(f"actions/runs/{run['id']}/artifacts?" + urllib.parse.urlencode({"name": name, "per_page": 100}))["artifacts"]
              if any(a["name"] == name and not a["expired"] for a in artifacts):
                  found = str(run["id"])
                  break
          with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
              output.write(f"version={version}\nrun-id={found}\n")
          if found:
              print(f"{package} {version}: release run {found} still holds {name}, so its SHA256SUMS is checked against TestPyPI's too")
          else:
              print(f"::warning::{package} {version}: no release run of {workflow} for {tag} still holds {name} (kept 90 days), so TestPyPI's JSON is the only record the files are checked against")
"""

FIND_NEW = r"""      # One-artifact publish template, republish step 1: the version from the tag; the tag's newest release run, which
      # must have passed its TestPyPI jobs (ruling 1 of 2026-11-16); and that run's artifact, while it exists.
      - name: Find the release run's artifact
        id: original
        shell: python3 {0}
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # One-artifact publish template (juniper-cascor publish.yml): copy verbatim; it reads PUBLISH_PACKAGE,
          # PUBLISH_TAG_PREFIX and the runner's GITHUB_* variables. The dispatch runs on the release tag (the pypi
          # environment admits tags only): PUBLISH_TAG_PREFIX, then the version. Anything else is refused before any
          # request. Ruling 1 of 2026-11-16: the newest release run of this workflow for that tag must exist, and each of
          # its jobs whose name holds "testpypi" (the upload, and the install check) must have concluded success in its
          # latest attempt, so this job never copies files whose checks failed or never ran. That run's <package>-dist,
          # while it exists, is checked against TestPyPI's JSON as well. An API failure fails the job.
          import json
          import os
          import sys
          import urllib.parse
          import urllib.request

          package = os.environ["PUBLISH_PACKAGE"]
          prefix = os.environ["PUBLISH_TAG_PREFIX"]
          tag = os.environ["GITHUB_REF_NAME"]
          version = ""
          if os.environ.get("GITHUB_REF_TYPE") == "tag" and prefix and tag.startswith(prefix):
              version = tag[len(prefix) :]
          if not version:
              print(f"::error::run this dispatch from a release tag of {package}, {prefix}<version>, not {os.environ.get('GITHUB_REF')}")
              sys.exit(1)
          api = f"{os.environ['GITHUB_API_URL']}/repos/{os.environ['GITHUB_REPOSITORY']}"
          workflow = os.environ["GITHUB_WORKFLOW_REF"].split("@", 1)[0].rsplit("/", 1)[-1]
          headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {os.environ['GH_TOKEN']}", "X-GitHub-Api-Version": "2022-11-28"}


          def get(path):
              with urllib.request.urlopen(urllib.request.Request(f"{api}/{path}", headers=headers), timeout=30) as response:
                  return json.load(response)


          runs = get(f"actions/workflows/{workflow}/runs?" + urllib.parse.urlencode({"event": "release", "branch": tag, "per_page": 30}))["workflow_runs"]
          ids = [r["id"] for r in runs if r["head_branch"] == tag]
          if not ids:
              print(f"::error::{workflow} has no release run for {tag}, so no run vouches for TestPyPI's {package} {version}: nothing is republished")
              sys.exit(1)
          run_id = max(ids)
          jobs = []
          page = 1
          while True:
              listing = get(f"actions/runs/{run_id}/jobs?" + urllib.parse.urlencode({"filter": "all", "per_page": 100, "page": page}))
              jobs.extend(listing["jobs"])
              if not listing["jobs"] or len(jobs) >= listing["total_count"]:
                  break
              page += 1
          # filter=all lists each attempt's record of each job, and a job's latest attempt is its record with the highest
          # (run_attempt, id). "Re-run failed jobs" gives every job a record in the new attempt: a job it runs again gets
          # its new result, and one it carries over gets a COPY of its earlier one (a new id, the new run_attempt, the
          # earlier conclusion). So each job counts with its newest result, whichever attempt produced it.
          latest = {}
          for job in jobs:
              if job["name"] not in latest or (job["run_attempt"], job["id"]) > (latest[job["name"]]["run_attempt"], latest[job["name"]]["id"]):
                  latest[job["name"]] = job
          checks = sorted((job for job in latest.values() if "testpypi" in job["name"].lower()), key=lambda job: job["name"])
          if not checks or any(job["conclusion"] != "success" for job in checks):
              print(f"::error::release run {run_id} of {workflow} for {tag}: each job whose name holds 'testpypi' must have concluded success in its latest attempt, so TestPyPI's {package} {version} is not republished")
              for job in checks:
                  print(f"  {job['name']}: {job['conclusion'] or job['status']} (attempt {job['run_attempt']})")
              if not checks:
                  print("  the run has no such job")
              sys.exit(1)
          for job in checks:
              print(f"release run {run_id}: {job['name']} concluded success in the latest attempt ({job['run_attempt']})")
          name = f"{package}-dist"
          artifacts = get(f"actions/runs/{run_id}/artifacts?" + urllib.parse.urlencode({"name": name, "per_page": 100}))["artifacts"]
          found = str(run_id) if any(a["name"] == name and not a["expired"] for a in artifacts) else ""
          with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
              output.write(f"version={version}\nrun-id={found}\n")
          if found:
              print(f"{package} {version}: release run {found} still holds {name}, so its SHA256SUMS is checked against TestPyPI's too")
          else:
              print(f"::warning::{package} {version}: release run {run_id} of {workflow} for {tag} no longer holds {name} (kept 90 days), so TestPyPI's JSON is the only record the files are checked against")
"""


# N3 of the review (2026-11-23): the install check no longer runs in the TestPyPI job. F8e of the round-2 review: it
# installs the wheel alone, so the record witnesses the files, not a test of each.
WITNESS_OLD = "      # (a file name can never be uploaded twice), so it stands as the witness to what the TestPyPI job tested.\n"
WITNESS_NEW = (
    "      # (a file name can never be uploaded twice), so it stands as the witness to the files this run built and\n"
    "      # TestPyPI took: the install check installed their wheel; no check installs the sdist.\n"
)


def template_edits(text: str, where: str) -> str:
    text = replace_once(text, WITNESS_OLD, WITNESS_NEW, where)
    text = replace_once(text, REPUBLISH_COMMENT_OLD, REPUBLISH_COMMENT_NEW, where)
    return replace_once(text, FIND_OLD, FIND_NEW, where)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Each publisher's own parts: the parameters, the TestPyPI job, and the install check's new job
# ─────────────────────────────────────────────────────────────────────────────────────────────
def env_block(package: str, dist_dir: str, prefix: str, sub_package: bool) -> tuple[str, str]:
    """(old, new) workflow ``env``: the third template parameter, PUBLISH_TAG_PREFIX, and a comment naming all three."""
    if sub_package:
        old_comment = "  # The one-artifact publish template's two parameters (see publish.yml): the distribution's name on PyPI and\n  # TestPyPI, and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
        new_comment = (
            "  # The one-artifact publish template's three parameters (see publish.yml): the distribution's name on PyPI and\n"
            "  # TestPyPI; the directory the build writes the sdist and wheel to, relative to the workspace; and the prefix of\n"
            "  # this package's release tags, whose remainder is the version. A job-level `if:` cannot read `env`, so the build\n"
            "  # job's tag guard repeats the prefix.\n"
        )
    else:
        old_comment = "  # The one-artifact publish template's two parameters: the distribution's name on PyPI and TestPyPI,\n  # and the directory the build writes the sdist and wheel to, relative to the workspace.\n"
        new_comment = (
            "  # The one-artifact publish template's three parameters: the distribution's name on PyPI and TestPyPI; the\n"
            "  # directory the build writes the sdist and wheel to, relative to the workspace; and the prefix of this package's\n"
            "  # release tags, whose remainder is the version. A job-level `if:` cannot read `env`, so the build job's tag guard\n"
            "  # repeats the prefix.\n"
        )
    values = f"  PUBLISH_PACKAGE: {package}\n  PUBLISH_DIST_DIR: {dist_dir}\n"
    return "env:\n" + old_comment + values, "env:\n" + new_comment + values + f"  PUBLISH_TAG_PREFIX: {prefix}\n"


INSTALL_JOB_COMMENT = (
    "  # Ruling 2 of 2026-11-16: the install check runs in a job of its own, after the TestPyPI job. It executes the\n"
    "  # package TestPyPI serves, so it holds no environment and no id-token: nothing it runs can mint a credential. The\n"
    "  # PyPI job needs it, and its name holds \"TestPyPI\", so juniper-ml's release-train ceremony reads its failure as\n"
    "  # HALT_TESTPYPI.\n"
)
CD_COMMENT_ROOT = (
    "          # `python -c` puts its working directory first on sys.path, and this repository's root holds juniper_cascor/,\n"
    "          # so an import run inside a checkout of it can pass without the wheel. This job checks nothing out, and it still\n"
    "          # installs and imports from the runner's temporary directory, outside any checkout.\n"
)
CD_COMMENT_SUB = (
    "          # `python -c` puts its working directory first on sys.path: install and import from the runner's temporary\n"
    "          # directory, outside the sparse checkout the version is read from.\n"
)
CD = '          cd "${RUNNER_TEMP}"\n'
# M1 of the review (2026-11-23): every install check retries the install five times, 10 s apart, and after the fifth
# failure fails with an error that names index lag, rather than fall through to an import that fails as if the package
# were broken. The sub-package publishers had the loop without the error; publish.yml had no loop.
LAG_COMMENT = "          # TestPyPI's simple index can lag behind its JSON: five tries, 10 s apart, and then an error that says so.\n"
LAG_RETRY = '            echo "TestPyPI index lag — retrying in 10s (attempt ${attempt}/5)"\n            sleep 10\n          done\n'


def lag_loop_end(package: str, version: str) -> str:
    """The retry loop's end: after the fifth failed install, an error naming the lag and the remedy, and exit 1."""
    return (
        '            if [ "${attempt}" -eq 5 ]; then\n'
        f'              echo "::error::{package} ${{{version}}} is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"\n'
        "              exit 1\n"
        "            fi\n" + LAG_RETRY
    )


def lag_loop(package: str, version: str) -> str:
    """The whole retry loop, as the sub-package publishers wrote it, with its new end."""
    return (
        LAG_COMMENT
        + "          for attempt in 1 2 3 4 5; do\n"
        + "            if pip install \\\n              --no-deps \\\n              --index-url https://test.pypi.org/simple/ \\\n"
        + f'              "{package}==${{{version}}}"; then\n'
        + "              break\n            fi\n"
        + lag_loop_end(package, version)
    )


# N1 of the review: the release's tag reaches the script through `env`, never pasted into its text by an expression.
RELEASE_TAG_ENV = "        env:\n          # The tag reaches the script as a variable: an expression in `run` would be pasted into the script's text.\n          RELEASE_TAG: ${{ github.event.release.tag_name }}\n"
# M6 of the review: the protocol's metadata check passes for a wheel that lacks the package; find_spec locates it
# without running it (an import would load the numpy codec, absent under --no-deps). F8b of the round-2 review: it fails
# through SystemExit, since PYTHONOPTIMIZE strips an assert statement.
PROTOCOL_CHECK_OLD = (
    "          # version via importlib.metadata instead of importing the package.\n"
    "          python -c \"import importlib.metadata as m; print('TestPyPI install OK', m.version('juniper-cascor-protocol'))\"\n"
)
PROTOCOL_CHECK_NEW = (
    "          # version via importlib.metadata instead of importing the package, and that the wheel holds the\n"
    "          # package: find_spec locates it without running it. SystemExit fails the step: PYTHONOPTIMIZE would strip\n"
    "          # an assert statement.\n"
    "          python -c \"import importlib.metadata as m, importlib.util as u; spec = u.find_spec('juniper_cascor_protocol'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('juniper-cascor-protocol'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no juniper_cascor_protocol package')\"\n"
)


def cut(text: str, start: str, end: str, where: str) -> tuple[str, str, str]:
    """Split TEXT at two anchors, each matching exactly once, START before END: (before START, START..END, END on)."""
    for anchor in (start, end):
        if text.count(anchor) != 1:
            raise Refused(f"{where}: anchor matched {text.count(anchor)} times, expected 1: {anchor[:90]!r}")
    a, b = text.index(start), text.index(end)
    if a >= b:
        raise Refused(f"{where}: {start[:40]!r} does not come before {end[:40]!r}")
    return text[:a], text[a:b], text[b:]


def publish_yml(text: str) -> str:
    """The single-package publisher: its header, parameters, guard comment, TestPyPI job and the new install job."""
    where = PUBLISH
    checkout = action_pin(text, "actions/checkout", where)
    setup_python = action_pin(text, "actions/setup-python", where)
    text = replace_once(
        text,
        "#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both jobs the\n"
        "#    same artifact: TestPyPI takes it first and must then serve exactly those sha256, and PyPI takes\n"
        "#    it only after TestPyPI is checked again. Uses OIDC trusted publishing (no API tokens).\n",
        "#    Builds the sdist and wheel ONCE, records their sha256 in SHA256SUMS and hands both publish jobs\n"
        "#    the same artifact: TestPyPI takes it first and must then serve exactly those sha256, a job that\n"
        "#    cannot mint a credential installs it from TestPyPI, and PyPI takes it only after that install\n"
        "#    passed and TestPyPI is checked again. Uses OIDC trusted publishing (no API tokens).\n",
        where,
    )
    text = replace_once(text, "#    repository but the two `env` values below, so another publish workflow can copy them verbatim\n", "#    repository but the three `env` values below, so another publish workflow can copy them verbatim\n", where)
    text = replace_once(
        text,
        "# Each job states what it needs. Only the jobs that upload hold id-token: write, so the build cannot mint a credential.\n",
        "# Each job states what it needs. Only the jobs that upload hold id-token: write, so neither the build nor the install\n# check can mint a credential.\n",
        where,
    )
    old_env, new_env = env_block("juniper-cascor", "dist", "v", sub_package=False)
    text = replace_once(text, old_env, new_env, where)
    text = replace_once(
        text,
        "    # Both publish jobs depend on this one, so this guard gates the whole pipeline.\n    if: startsWith(github.event.release.tag_name, 'v')\n",
        "    # Both publish jobs depend on this one, so this guard gates the whole pipeline. The publish environments also admit\n"
        "    # `rc*` and `hf*` tags, kept for future release-candidate and hotfix conventions (D2 of juniper-ml's\n"
        "    # notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md). This guard skips them: a\n"
        "    # convention that adopts one must widen it, and PUBLISH_TAG_PREFIX with it.\n"
        "    if: startsWith(github.event.release.tag_name, 'v')\n",
        where,
    )
    setup = f"      - uses: {setup_python}\n        with:\n          python-version: \"3.12\"\n"
    text = replace_once(
        text,
        "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n"
        "    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n"
        f"    steps:\n      - uses: {checkout}\n\n" + setup + "\n",
        "  testpypi:\n    name: Publish to TestPyPI\n    needs: build\n    runs-on: ubuntu-latest\n    environment: testpypi\n"
        "    permissions:\n      id-token: write  # trusted publishing to TestPyPI; this job checks out nothing and runs no install check\n"
        "    steps:\n",
        where,
    )
    pypi_head = "\n  pypi:\n    name: Publish to PyPI\n    needs: testpypi\n"
    before, install, after = cut(text, "      - name: Verify TestPyPI install\n", pypi_head, where)
    install = replace_once(
        install,
        '        run: |\n          VERSION="${{ github.event.release.tag_name }}"\n          VERSION="${VERSION#v}"\n',
        RELEASE_TAG_ENV + "        run: |\n" + CD_COMMENT_ROOT + CD + '          VERSION="${RELEASE_TAG#v}"\n',
        where + " install check",
    )
    install = replace_once(install, "          pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==${VERSION}\n", lag_loop("juniper-cascor", "VERSION"), where + " install check")
    job = (
        INSTALL_JOB_COMMENT
        + f"  {INSTALL_JOB}:\n    name: {INSTALL_NAME}\n    needs: testpypi\n    runs-on: ubuntu-latest\n"
        + "    permissions:\n      contents: read  # and nothing else: this job runs the package TestPyPI serves\n"
        + "    steps:\n"
        + setup
        + "\n"
        + install
    )
    text = before + job + after
    text = replace_once(text, pypi_head, f"\n  pypi:\n    name: Publish to PyPI\n    needs: [testpypi, {INSTALL_JOB}]\n", where)
    return template_edits(text, where)


SUB_PERMISSIONS_COMMENT_OLD = "# Each job adds what it needs to this; only the jobs that upload add id-token: write.\n"
SUB_PERMISSIONS_COMMENT_NEW = (
    "# A job's own `permissions` replace this block rather than add to it: every job below states all it needs, and only\n"
    "# the jobs that upload hold id-token: write. This block is the default for a job added without its own.\n"
)


def sub_package_workflow(text: str, where: str) -> str:
    """A sub-package publisher: its permissions comment, parameters, TestPyPI job and the new install job."""
    package, test_id, prod_id, prefix = PUBLISHERS[where]
    checkout = action_pin(text, "actions/checkout", where)
    text = replace_once(text, SUB_PERMISSIONS_COMMENT_OLD, SUB_PERMISSIONS_COMMENT_NEW, where)
    old_env, new_env = env_block(package, f"{package}/dist", prefix, sub_package=True)
    text = replace_once(text, old_env, new_env, where)
    text = replace_once(
        text,
        "    permissions:\n      contents: read\n      id-token: write  # trusted publishing to TestPyPI\n",
        "    permissions:\n      id-token: write  # trusted publishing to TestPyPI; this job checks out nothing and runs no install check\n",
        where,
    )
    # M4 of the review: a plain dispatch builds only from this package's own tag, as a release does.
    text = replace_once(
        text,
        "    # also fires this workflow and must be skipped. A dispatch runs it, unless it asks for the republish job. Downstream jobs\n"
        "    # `needs: build`, so this one guard gates the whole pipeline.\n"
        f"    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)\n",
        "    # also fires this workflow and must be skipped. A dispatch runs it only from this package's own tag, and only when it\n"
        "    # does not ask for the republish job: from another package's tag it would publish this package's files under that\n"
        "    # tag's run. Downstream jobs `needs: build`, so this one guard gates the whole pipeline.\n"
        f"    if: (github.event_name == 'release' && startsWith(github.event.release.tag_name, '{prefix}')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))\n",
        where,
    )
    # N4 of the review: the PyPI job checks nothing out, so it holds id-token: write alone, as publish.yml's does.
    text = replace_once(
        text,
        "    runs-on: ubuntu-latest\n    permissions:\n      contents: read\n      id-token: write  # trusted publishing to PyPI\n    environment:\n      name: pypi\n",
        "    runs-on: ubuntu-latest\n    permissions:\n      id-token: write  # trusted publishing to PyPI; this job checks out nothing\n    environment:\n      name: pypi\n",
        where,
    )
    pypi_head = f"\n  {prod_id}:\n    name: Publish to PyPI\n    needs: {test_id}\n"
    sparse = f"      - uses: {checkout}\n        with:\n          sparse-checkout: |\n            {package}/pyproject.toml\n"
    before, install, after = cut(text, sparse, pypi_head, where)
    # N2 of the review: the checkout keeps no credential in the workspace while the package TestPyPI serves runs.
    install = replace_once(install, sparse, sparse + "          persist-credentials: false\n", where + " install check")
    install = replace_once(
        install,
        f"        run: |\n          set -euo pipefail\n          version=$(grep '^version' {package}/pyproject.toml | head -1 |",
        "        run: |\n          set -euo pipefail\n" + CD_COMMENT_SUB + CD + f"          version=$(grep '^version' \"${{GITHUB_WORKSPACE}}/{package}/pyproject.toml\" | head -1 |",
        where + " install check",
    )
    install = replace_once(install, "          for attempt in 1 2 3 4 5; do\n", LAG_COMMENT + "          for attempt in 1 2 3 4 5; do\n", where + " install check")
    install = replace_once(install, LAG_RETRY, lag_loop_end(package, "version"), where + " install check")
    if where == PROTOCOL:
        install = replace_once(install, PROTOCOL_CHECK_OLD, PROTOCOL_CHECK_NEW, where + " install check")
    job = (
        INSTALL_JOB_COMMENT
        + f"  {INSTALL_JOB}:\n    name: {INSTALL_NAME}\n    needs: {test_id}\n    runs-on: ubuntu-latest\n"
        + "    permissions:\n      contents: read  # the sparse checkout below, and nothing else: this job runs the package TestPyPI serves\n"
        + "    steps:\n"
        + "      # A sparse checkout, for the file the version is read from: nothing runs from it, and it keeps no credential.\n"
        + install
    )
    text = before + job + after
    text = replace_once(text, pypi_head, f"\n  {prod_id}:\n    name: Publish to PyPI\n    needs: [{test_id}, {INSTALL_JOB}]\n", where)
    return template_edits(text, where)


def check_workflows(out: dict[str, str]) -> None:
    """Post-conditions: the republish job is byte-identical in all three, and each file parses with its new wiring."""
    jobs = {rel: republish_job(out[rel], rel) for rel in PUBLISHERS}
    if len(set(jobs.values())) != 1:
        raise Refused("the republish job differs between the three publishers after the edits")
    try:
        import yaml  # noqa: PLC0415 -- optional: present wherever the checker runs
    except ImportError:
        print("note: PyYAML is not importable here; the parse post-condition is skipped")
        return
    for rel, (package, test_id, prod_id, prefix) in PUBLISHERS.items():
        data = yaml.safe_load(out[rel])
        wf_jobs = data["jobs"]
        if data["env"] != {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": "dist" if rel == PUBLISH else f"{package}/dist", "PUBLISH_TAG_PREFIX": prefix}:
            raise Refused(f"{rel}: env is {data['env']}")
        install = wf_jobs.get(INSTALL_JOB) or {}
        if install.get("name") != INSTALL_NAME or install.get("needs") != test_id or install.get("permissions") != {"contents": "read"}:
            raise Refused(f"{rel}: the install job is {install}")
        if wf_jobs[prod_id].get("needs") != [test_id, INSTALL_JOB] or wf_jobs[test_id].get("permissions") != {"id-token": "write"}:
            raise Refused(f"{rel}: the PyPI job needs {wf_jobs[prod_id].get('needs')}, the TestPyPI job holds {wf_jobs[test_id].get('permissions')}")
        if wf_jobs[prod_id].get("permissions") != {"id-token": "write"}:
            raise Refused(f"{rel}: the PyPI job holds {wf_jobs[prod_id].get('permissions')}")
        if any("pip install" in str(step.get("run") or "") or str(step.get("uses") or "").startswith("actions/checkout@") for step in wf_jobs[test_id]["steps"]):
            raise Refused(f"{rel}: the TestPyPI job still checks out or installs")
        runs = [str(step.get("run") or "") for step in install.get("steps") or []]
        if sum(run.count("pip install") for run in runs) != 1 or sum(run.count("not installable from TestPyPI after 5 tries (index lag?)") for run in runs) != 1 or any("${{" in run for run in runs):
            raise Refused(f"{rel}: the install check lacks its one retried install, its lag error, or reads an expression in its script")
        if rel != PUBLISH and [step.get("with") for step in install["steps"] if "uses" in step] != [{"sparse-checkout": f"{package}/pyproject.toml\n", "persist-credentials": False}]:
            raise Refused(f"{rel}: the install job's sparse checkout is not the version file alone, without a kept credential")
        guard = f"startsWith(github.event.release.tag_name, '{prefix}')"
        if rel != PUBLISH:
            guard = f"(github.event_name == 'release' && {guard}) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{prefix}'))"
        if wf_jobs["build"].get("if") != guard:
            raise Refused(f"{rel}: the build guard is {wf_jobs['build'].get('if')!r}")


# ─────────────────────────────────────────────────────────────────────────────────────────────
# src/tests/unit/test_publish_one_artifact.py: derived hunk by hunk from the reviewed new file, each OLD widened by whole
# lines until it matches exactly once on both bases; none names the person-word (the docstring lines that do are left).
# ─────────────────────────────────────────────────────────────────────────────────────────────
# BEGIN TEST_EDITS
TEST_EDITS = (
    # base line 13
    (r'''nothing. The steps are a template other Juniper publishers copy verbatim: they read only ``PUBLISH_PACKAGE`` and
``PUBLISH_DIST_DIR`` from the workflow ``env``, a step's ``INDEX_URL``, and the runner's own variables.

The static cases pin the wiring: one build, in a job without an environment or ``id-token``; the job chain and the two
job names juniper-ml's release-train ceremony reads; per-job permissions; the reuse step first in the build job and
guarding every later step; each upload preceded by the dist check; TestPyPI's JSON checked after the TestPyPI upload
and again before the PyPI one, and PyPI's after; no ``skip-existing``; an artifact that outlives the 30-day ``pypi``
gate; the republish job's trigger, gate, steps and name; the triggers and tag guards; and every copy of a template step
byte-identical. The rehearsals run each template step's own Python, extracted from ``publish.yml``, in a scratch
workspace, against a stand-in index and a stand-in GitHub API on 127.0.0.1.
''',
     r'''nothing. The steps are a template other Juniper publishers copy verbatim: they read only ``PUBLISH_PACKAGE``,
``PUBLISH_DIST_DIR`` and ``PUBLISH_TAG_PREFIX`` from the workflow ``env``, a step's ``INDEX_URL``, and the runner's own
variables.

The static cases pin the wiring: one build, in a job without an environment or ``id-token``; the job chain and the
job names juniper-ml's release-train ceremony reads; per-job permissions; each job's keys, runner and exact steps, with
no ``if:`` but the listed ones and no ``continue-on-error``; each build step's commands; the reuse step first in the
build job and guarding every later step; each upload preceded by the dist check; TestPyPI's JSON checked after the
TestPyPI upload and again before the PyPI one, and PyPI's after; no ``skip-existing`` and no ``attestations: false``;
an artifact kept 90 days, past the 30-day ``pypi`` gate; the install check in a job of its own, which cannot mint a
credential, runs exactly its commands from outside any checkout, and is needed by the PyPI job (ruling 2 of
2026-11-16); the republish job's trigger, gate, steps and name; the triggers, tag guards and tag prefixes; and every
copy of a template step byte-identical, and each action pinned to one ref. (The bounds the docs state are pinned in
``test_publish_docs_bounds.py``: this module reads the workflows alone.) The rehearsals run each template step's own
Python, extracted from ``publish.yml``, in a scratch workspace, against a stand-in index
and a stand-in GitHub API on 127.0.0.1, the republish job's refusal among them: it publishes nothing unless the tag's
newest release run passed its TestPyPI jobs in their latest attempt (ruling 1 of 2026-11-16). Each install check's own
shell runs too, against stand-in ``pip``, ``python`` and ``sleep`` commands.
'''),
    # base line 51
    (r'''#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build`` and a ``republish`` job.
''',
     r'''#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build``, an install check and a ``republish`` job.
'''),
    # base line 57
    (r'''#: workflow -> (top-level permissions, the PyPI job's). The build, TestPyPI and republish jobs hold the same in all three.
PERMISSIONS = {
    "publish.yml": ({}, {"id-token": "write"}),
    "publish-cascor-model.yml": ({"contents": "read"}, {"contents": "read", "id-token": "write"}),
    "publish-protocol.yml": ({"contents": "read"}, {"contents": "read", "id-token": "write"}),
}
''',
     r'''#: workflow -> (top-level permissions, the PyPI job's). The PyPI job checks nothing out, so it holds ``id-token: write``
#: alone in all three. The build, TestPyPI, install-check and republish jobs hold the same in all three.
PERMISSIONS = {
    "publish.yml": ({}, {"id-token": "write"}),
    "publish-cascor-model.yml": ({"contents": "read"}, {"id-token": "write"}),
    "publish-protocol.yml": ({"contents": "read"}, {"id-token": "write"}),
}
#: workflow -> PUBLISH_TAG_PREFIX, what the package's release tags start with (the version is the rest): ``v`` for the
#: app, ``<package>-v`` for a sub-package.
TAG_PREFIXES = {"publish.yml": "v", "publish-cascor-model.yml": "juniper-cascor-model-v", "publish-protocol.yml": "juniper-cascor-protocol-v"}
#: workflow -> its ``name:``. juniper-ml's release-train monitor drops every run of a workflow whose name does not end in
#: "to PyPI" (``PYPI_PUBLISHER_NAME_SUFFIX`` in ``util/release_train/ceremony.py``), so a renamed publisher fails quietly.
WORKFLOW_NAMES = {"publish.yml": "Publish to PyPI", "publish-cascor-model.yml": "Publish juniper-cascor-model to PyPI", "publish-protocol.yml": "Publish juniper-cascor-protocol to PyPI"}
#: Ruling 2 of 2026-11-16: the install check runs in a job of its own, which holds no ``id-token``. Its name holds
#: "TestPyPI", so the release-train ceremony counts it with the TestPyPI job and reads its failure as HALT_TESTPYPI.
INSTALL = "verify-testpypi-install"
INSTALL_NAME = "Verify the TestPyPI install"
#: workflow -> the install check's step name, kept from the TestPyPI job it moved out of.
INSTALL_STEPS = {"publish.yml": "Verify TestPyPI install", "publish-cascor-model.yml": "Verify install from TestPyPI (no-deps, version-only import)", "publish-protocol.yml": "Verify install from TestPyPI"}
#: The sub-package build jobs' release-convention gate. It runs on ``push`` alone, an event no publisher subscribes to, so
#: it never runs: it is the one build step exempt from the reuse condition, and it is exempt by its name.
RELEASE_GATE = "Require a GitHub Release for this tag"
'''),
    # base line 82
    (r'''    "PUBLISH_DIST_DIR",
''',
     r'''    "PUBLISH_DIST_DIR",
    "PUBLISH_TAG_PREFIX",
'''),
    # base line 103
    (r'''GATE_APPROVAL_DAYS = 30
''',
     r'''GATE_APPROVAL_DAYS = 30
#: The artifact's retention, as the docs state it: past the gate's 30 days and the 30-day re-run window.
RETENTION_DAYS = 90
'''),
    # base line 115
    (r'''FAKE_API_CREDENTIAL = "stand-in-credential"
''',
     r'''FAKE_API_CREDENTIAL = "stand-in-credential"
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
SUB_PACKAGE_BUILD_STEPS = [(REUSE, None), (None, CHECKOUT), (RELEASE_GATE, None), (None, SETUP_PYTHON), ("Install build tools", None), ("Build sdist + wheel", None), ("Validate distribution metadata", None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)]
BUILD_STEPS = {
    "publish.yml": [(REUSE, None), (None, CHECKOUT), (None, SETUP_PYTHON), ("Install build tools", None), ("Build package", None), ("Check package", None), (RECORD, None), (UPLOAD, UPLOAD_ACTION)],
    "publish-cascor-model.yml": SUB_PACKAGE_BUILD_STEPS,
    "publish-protocol.yml": SUB_PACKAGE_BUILD_STEPS,
}
#: The install-check job: setup-python, or the sparse checkout a sub-package reads its version from, then the check.
INSTALL_JOB_STEPS = {
    "publish.yml": [(None, SETUP_PYTHON), (INSTALL_STEPS["publish.yml"], None)],
    "publish-cascor-model.yml": [(None, CHECKOUT), (INSTALL_STEPS["publish-cascor-model.yml"], None)],
    "publish-protocol.yml": [(None, CHECKOUT), (INSTALL_STEPS["publish-protocol.yml"], None)],
}
#: workflow -> the exact inputs of its TestPyPI and its PyPI upload: no ``skip-existing`` (nor the action's older spelling
#: ``skip_existing``), no ``attestations: false``, and the downloaded dist directory as the only source.
TESTPYPI_INPUTS = {"repository-url": "https://test.pypi.org/legacy/", "packages-dir": DIST_INPUT}
UPLOAD_INPUTS = {
    "publish.yml": (TESTPYPI_INPUTS, {"packages-dir": DIST_INPUT}),
    "publish-cascor-model.yml": ({**TESTPYPI_INPUTS, "verbose": True}, {"packages-dir": DIST_INPUT, "verbose": True}),
    "publish-protocol.yml": ({**TESTPYPI_INPUTS, "verbose": True}, {"packages-dir": DIST_INPUT, "verbose": True}),
}
#: Every key the workflow and each of its jobs carries. An ``env`` on a job (``PIP_EXTRA_INDEX_URL``,
#: ``HASH_CHECK_ATTEMPTS``), a container, a matrix or another runner would change what a check runs, or against what.
WORKFLOW_KEYS = {"name", "on", "permissions", "env", "jobs"}
BUILD_JOB_KEYS = {"name", "if", "runs-on", "permissions", "steps"}
PUBLISH_JOB_KEYS = {"name", "needs", "runs-on", "environment", "permissions", "steps"}
INSTALL_JOB_KEYS = {"name", "needs", "runs-on", "permissions", "steps"}
REPUBLISH_JOB_KEYS = {"name", "if", "runs-on", "environment", "permissions", "steps"}
#: The keys a repository may add, none of which changes what a check runs. The workflow's: ``run-name``, which names the
#: run, and a ``concurrency`` group that never cancels a run in progress (the run it holds pending, and cancels when a
#: newer one queues, has run nothing yet). A job's: ``timeout-minutes``, which stops it sooner, and a job stopped so
#: fails, so nothing after it runs; the republish job takes one only in all three files at once, since it stays
#: identical in every publisher. No job takes a ``concurrency`` group: by default (``queue: single``) GitHub keeps one
#: pending job per group and cancels the older one when another queues, so a group on the PyPI job could stop a run
#: between its two uploads.
OPTIONAL_WORKFLOW_KEYS = {"run-name", "concurrency"}
OPTIONAL_JOB_KEYS = {"timeout-minutes"}
#: workflow -> each build step's command: the build, and the check of what it built.
SUB_PACKAGE_BUILD_RUNS = {"Install build tools": "pip install --upgrade build twine", "Build sdist + wheel": "python -m build --sdist --wheel", "Validate distribution metadata": "twine check dist/*"}
BUILD_RUNS = {
    "publish.yml": {"Install build tools": "pip install build twine", "Build package": "python -m build", "Check package": "twine check dist/*"},
    "publish-cascor-model.yml": SUB_PACKAGE_BUILD_RUNS,
    "publish-protocol.yml": SUB_PACKAGE_BUILD_RUNS,
}
#: The install checks' bounded retry: this many tries, this many seconds apart; publish.yml waits once before the first.
INSTALL_TRIES = 5
INSTALL_RETRY_SECONDS = 10
INSTALL_FIRST_WAIT_SECONDS = 30
LAG_ERROR = "is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats"


def _retried_install(package: str, version: str) -> list[str]:
    """The install every check runs: five tries, 10 s apart, and after the fifth failure an error that names index lag,
    rather than an import that fails as if the package were broken."""
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


def _version_from_pyproject(package: str) -> str:
    return f"""version=$(grep '^version' "${{GITHUB_WORKSPACE}}/{package}/pyproject.toml" | head -1 | sed -E 's/version = "(.+)"/\\1/')"""


#: workflow -> its install step's commands, exactly, comment and blank lines dropped: no ``exit 0``, ``trap``, earlier
#: install or second VERSION can be added and none dropped, while a comment may change freely. The protocol check reads
#: the metadata and finds the package without importing it (the import loads the numpy codec, absent under --no-deps).
INSTALL_COMMANDS = {
    "publish.yml": ['cd "${RUNNER_TEMP}"', 'VERSION="${RELEASE_TAG#v}"', "sleep 30", *_retried_install("juniper-cascor", "VERSION"), """python -c "from juniper_cascor import __version__; print(f'TestPyPI OK: v{__version__}')\""""],
    "publish-cascor-model.yml": [
        "set -euo pipefail",
        'cd "${RUNNER_TEMP}"',
        _version_from_pyproject("juniper-cascor-model"),
        *_retried_install("juniper-cascor-model", "version"),
        """python -c "import juniper_cascor_model; print('TestPyPI install OK', juniper_cascor_model.__version__)\"""",
    ],
    "publish-protocol.yml": [
        "set -euo pipefail",
        'cd "${RUNNER_TEMP}"',
        _version_from_pyproject("juniper-cascor-protocol"),
        *_retried_install("juniper-cascor-protocol", "version"),
        """python -c "import importlib.metadata as m, importlib.util as u; spec = u.find_spec('juniper_cascor_protocol'); origin = spec.origin if spec else None; print('TestPyPI install', m.version('juniper-cascor-protocol'), 'package at', origin); raise SystemExit(0 if origin else 'the installed wheel holds no juniper_cascor_protocol package')\"""",
    ],
}
#: workflow -> the install step's keys beyond its name and script: publish.yml's reads the release's tag through ``env``,
#: so no expression is pasted into the script's text.
INSTALL_STEP_EXTRA = {"publish.yml": {"env": {"RELEASE_TAG": "${{ github.event.release.tag_name }}"}}, "publish-cascor-model.yml": {}, "publish-protocol.yml": {}}
'''),
    # base line 147
    (r'''
def _assert_no_checkout_between(job: dict, start: int, end: int) -> None:
''',
     r'''
def _cancels(group) -> bool:
    """Whether a workflow's ``concurrency`` value cancels a run in progress. A group named alone, or one without
    ``cancel-in-progress``, never does: it holds a newer run pending, and cancels only an older pending run, which has
    run nothing yet."""
    return isinstance(group, dict) and group.get("cancel-in-progress", False) is not False


def _assert_no_checkout_between(job: dict, start: int, end: int) -> None:
'''),
    # base line 151
    (r'''    assert not [u for u in between if u.startswith("actions/checkout@")], f"a checkout runs between steps {start} and {end}: {between}"
''',
     r'''    assert not [u for u in between if u.startswith("actions/checkout@")], f"a checkout runs between steps {start} and {end}: {between}"


def _steps(job: dict) -> list[tuple[str | None, str | None]]:
    """Each step as (its name, the action it uses with the ``@ref`` dropped)."""
    return [(s.get("name"), str(s["uses"]).split("@", 1)[0] if s.get("uses") else None) for s in job.get("steps") or []]


def _by_action(value):
    """VALUE with every ``uses:`` reduced to the action's name, the ``@ref`` dropped."""
    if isinstance(value, dict):
        return {k: (str(v).split("@", 1)[0] if k == "uses" else _by_action(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_by_action(v) for v in value]
    return value


def _allowed_if(job_id: str, index: int, step: dict) -> str | None:
    """The one ``if:`` a step may carry: the reuse step's own, the reuse condition on every later build step but the
    push-only release gate (exempt by its name), and the republish job's download of the release run's artifact. Any
    other ``if:`` could skip a check."""
    if job_id == "build":
        if index == 0:
            return "github.run_attempt != '1'"
        return "github.event_name == 'push'" if step.get("name") == RELEASE_GATE else REUSE_IF
    if job_id == REPUBLISH and step.get("name") == FETCH_ORIGINAL:
        return "steps.original.outputs.run-id != ''"
    return None
'''),
    # base line 179
    (r'''    child = {"PATH": os.environ.get("PATH", ""), "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": "juniper-cascor", "PUBLISH_DIST_DIR": "dist"}
''',
     r'''    child = {"PATH": os.environ.get("PATH", ""), "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": "juniper-cascor", "PUBLISH_DIST_DIR": "dist", "PUBLISH_TAG_PREFIX": "v"}
'''),
    # base line 259
    (r'''        assert _workflow(workflow)["env"] == {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist_dir}
''',
     r'''        wf = _workflow(workflow)
        assert wf["env"] == {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist_dir, "PUBLISH_TAG_PREFIX": TAG_PREFIXES[workflow]}
        # A single-package publisher's tags are v<version>; a sub-package publisher's are <package>-v<version>.
        assert TAG_PREFIXES[workflow] == ("v" if workflow == "publish.yml" else f"{package}-v")
        # A job-level if: cannot read env, so the build job's tag guard repeats the prefix: the two must agree.
        assert f"startsWith(github.event.release.tag_name, '{TAG_PREFIXES[workflow]}')" in wf["jobs"]["build"]["if"]

    def test_the_workflow_name_ends_in_to_pypi_as_the_release_train_monitor_requires(self, workflow):
        name = _workflow(workflow)["name"]
        assert name == WORKFLOW_NAMES[workflow]
        assert name.lower().endswith("to pypi")
'''),
    # base line 272
    (r'''        assert sorted(jobs) == sorted(["build", test_id, prod_id, REPUBLISH])
        assert jobs[test_id]["needs"] == "build"
        assert jobs[prod_id]["needs"] == test_id
        # juniper-ml's util/release_train/ceremony.py tells the two jobs apart by name ("testpypi" / "pypi").
        assert jobs[test_id]["name"] == "Publish to TestPyPI"
''',
     r'''        assert sorted(jobs) == sorted(["build", test_id, INSTALL, prod_id, REPUBLISH])
        assert jobs[test_id]["needs"] == "build"
        assert jobs[INSTALL]["needs"] == test_id
        # PyPI waits for both TestPyPI jobs: the upload with its checks, and the install check.
        assert jobs[prod_id]["needs"] == [test_id, INSTALL]
        # juniper-ml's util/release_train/ceremony.py tells the jobs apart by name: "testpypi" (both TestPyPI jobs) and "pypi".
        assert jobs[test_id]["name"] == "Publish to TestPyPI"
        assert jobs[INSTALL]["name"] == INSTALL_NAME
'''),
    # base line 290
    (r'''        assert jobs[PUBLISHERS[workflow][2]]["permissions"] == {"contents": "read", "id-token": "write"}
''',
     r'''        # The job that can mint runs the template steps and the upload alone: it checks out nothing and installs nothing.
        assert jobs[PUBLISHERS[workflow][2]]["permissions"] == {"id-token": "write"}
        # The install check runs the package TestPyPI serves: it may read the repository, and nothing more.
        assert jobs[INSTALL]["permissions"] == {"contents": "read"}
'''),
    # base line 305
    (r'''        # runs on `push` alone, an event no publisher subscribes to.
        for step in build["steps"][1:]:
            if step.get("if") == "github.event_name == 'push'":
''',
     r'''        # runs on `push` alone, an event no publisher subscribes to. It is exempt by its name: an exemption by its `if:`
        # text would let any build step trade the reuse condition for the push condition.
        for step in build["steps"][1:]:
            if step.get("name") == RELEASE_GATE:
                assert step.get("if") == "github.event_name == 'push'"
'''),
    # base line 315
    (r'''        job = _workflow(workflow)["jobs"][test_id]
''',
     r'''        jobs = _workflow(workflow)["jobs"]
        job = jobs[test_id]
'''),
    # base line 320
    (r'''        installs = [i for i, s in enumerate(job["steps"]) if "pip install" in str(s.get("run") or "")]
        assert installs, "the TestPyPI install check is gone"
        assert min(installs) > _index(job, TESTPYPI_AFTER), "the install check must come after the sha256 check that vouches for what it installs"
        _assert_no_checkout_between(job, _index(job, DOWNLOAD), _index(job, TESTPYPI_AFTER))
''',
     r'''        # The job ends at the sha256 check that vouches for what the install check installs, in the job that needs it.
        assert _index(job, TESTPYPI_AFTER) == len(job["steps"]) - 1
        assert not [s for s in job["steps"] if "pip install" in str(s.get("run") or "")], "the job that can mint runs an install check"
        installs = [s for s in jobs[INSTALL]["steps"] if "pip install" in str(s.get("run") or "")]
        assert installs, "the TestPyPI install check is gone"
        assert jobs[INSTALL]["needs"] == test_id, "the install check must come after the sha256 check that vouches for what it installs"
        _assert_no_checkout_between(job, 0, len(job["steps"]))
'''),
    # base line 357
    (r'''        for job in _workflow(workflow)["jobs"].values():
            for i in _uploads(job):
                inputs = job["steps"][i].get("with") or {}
                assert inputs.get("packages-dir") == DIST_INPUT
                # skip-existing would keep an earlier file under the same name, and the install check would test it.
                assert "skip-existing" not in inputs
''',
     r'''        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        for job in jobs.values():
            for i in _uploads(job):
                inputs = job["steps"][i].get("with") or {}
                assert inputs.get("packages-dir") == DIST_INPUT
                # skip-existing would keep an earlier file under the same name, and the install check would test it. The
                # action still reads its older spelling too.
                assert "skip-existing" not in inputs
                assert "skip_existing" not in inputs
                # Attestations stay on, the action's default.
                assert inputs.get("attestations", True) is True
        for job_id, inputs in zip((test_id, prod_id), UPLOAD_INPUTS[workflow]):
            assert [jobs[job_id]["steps"][i].get("with") for i in _uploads(jobs[job_id])] == [inputs]
'''),
    # base line 371
    (r'''        assert int(upload["retention-days"]) > GATE_APPROVAL_DAYS
''',
     r'''        # Exactly the documented 90 days, which outlive the gate's 30 days and the 30-day re-run window.
        assert upload["retention-days"] == RETENTION_DAYS
        assert RETENTION_DAYS > GATE_APPROVAL_DAYS
'''),
    # base line 380
    (r'''            assert _step(jobs[job_id], name)["env"] == {"INDEX_URL": INDEX_CHECKS[name]}


''',
     r'''            assert _step(jobs[job_id], name)["env"] == {"INDEX_URL": INDEX_CHECKS[name]}

    def test_each_job_runs_exactly_its_listed_steps_in_order(self, workflow):
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        jobs = _workflow(workflow)["jobs"]
        want = {"build": BUILD_STEPS[workflow], test_id: TESTPYPI_STEPS, INSTALL: INSTALL_JOB_STEPS[workflow], prod_id: PYPI_STEPS, REPUBLISH: REPUBLISH_STEPS}
        assert {job_id: _steps(job) for job_id, job in jobs.items()} == want

    def test_no_step_or_job_can_switch_a_check_off(self, workflow):
        for job_id, job in _workflow(workflow)["jobs"].items():
            # A job or step that continues on error is a check that no longer blocks, and an if: can skip one. The build
            # and republish jobs' own if: are pinned to their exact text elsewhere; no other job may carry one (`always()`
            # on the PyPI job would publish after a failed install check).
            assert "continue-on-error" not in job, f"{job_id} would not fail the run"
            if job_id not in ("build", REPUBLISH):
                assert "if" not in job, f"{job_id} carries if: {job.get('if')!r}"
            for index, step in enumerate(job.get("steps") or []):
                label = f"{job_id}: {step.get('name') or step.get('uses')}"
                assert "continue-on-error" not in step, f"{label} would not fail its job"
                assert step.get("if") == _allowed_if(job_id, index, step), f"{label} carries if: {step.get('if')!r}"

    def test_every_job_carries_only_its_listed_keys_and_runs_on_a_hosted_runner(self, workflow):
        # A job-level env (PIP_EXTRA_INDEX_URL, or HASH_CHECK_ATTEMPTS over a JSON check's bounds), a container, a matrix
        # or a self-hosted runner would change what a check runs, or against what. The workflow's run-name and a
        # workflow concurrency group that never cancels, and a job's timeout-minutes, change no check, so a repository
        # may add them (OPTIONAL_*_KEYS); the republish job takes a timeout only in all three files, since it stays
        # identical in every publisher. A job's own concurrency group is refused: by default (queue: single) it cancels
        # the group's pending job when another queues.
        wf = _workflow(workflow)
        sub = workflow != "publish.yml"
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        required = WORKFLOW_KEYS | ({"concurrency"} if sub else set())
        assert required <= set(wf) <= required | OPTIONAL_WORKFLOW_KEYS, f"workflow keys {sorted(wf)}"
        want = {"build": BUILD_JOB_KEYS | ({"defaults"} if sub else set()), test_id: PUBLISH_JOB_KEYS, INSTALL: INSTALL_JOB_KEYS, prod_id: PUBLISH_JOB_KEYS, REPUBLISH: REPUBLISH_JOB_KEYS}
        assert {job_id: set(job) - OPTIONAL_JOB_KEYS for job_id, job in wf["jobs"].items()} == want
        assert {job_id: job["runs-on"] for job_id, job in wf["jobs"].items()} == dict.fromkeys(want, "ubuntu-latest")
        if sub:
            assert wf["jobs"]["build"]["defaults"] == {"run": {"working-directory": PUBLISHERS[workflow][0]}}

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
        package = PUBLISHERS[workflow][0]
        job = _workflow(workflow)["jobs"][INSTALL]
        assert "defaults" not in job
        step = _step(job, INSTALL_STEPS[workflow])
        assert "working-directory" not in step
        commands = [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")]
        if commands[0] == "set -euo pipefail":
            commands = commands[1:]
        # `python -c` puts its working directory first on sys.path, and this repository's root holds juniper_cascor/: an
        # import run inside a checkout could pass without the wheel. So the first command leaves for the runner's
        # temporary directory, and no command moves elsewhere.
        assert commands[0] == 'cd "${RUNNER_TEMP}"'
        assert [c for c in commands if c.split()[0] in ("cd", "pushd", "popd")] == ['cd "${RUNNER_TEMP}"']
        assert [c for c in commands if "pip install" in c]
        assert [c for c in commands if c.startswith("python -c ")]
        # A sub-package reads its version from a sparse checkout, and nothing runs from it. It keeps no credential in the
        # workspace while the package TestPyPI serves runs.
        checkouts = [s.get("with") for s in job["steps"] if str(s.get("uses") or "").startswith(f"{CHECKOUT}@")]
        assert checkouts == ([] if workflow == "publish.yml" else [{"sparse-checkout": f"{package}/pyproject.toml\n", "persist-credentials": False}])

    def test_the_install_step_runs_exactly_its_commands(self, workflow):
        # Exactly these commands, in this order, comment and blank lines dropped: no `exit 0`, trap, earlier install or
        # second VERSION can be added, and none dropped, while a comment may change freely. The step carries its name and
        # script, and publish.yml's the release's tag, through env: no expression is pasted into the script.
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        assert [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")] == INSTALL_COMMANDS[workflow]
        assert {key: value for key, value in step.items() if key not in ("name", "run")} == INSTALL_STEP_EXTRA[workflow]
        assert "${{" not in step["run"]

    def test_the_install_check_cannot_be_switched_off(self, workflow):
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        commands = "\n".join(line for line in step["run"].splitlines() if not line.strip().startswith("#"))
        # A failed install or import must fail the job: no `|| true` (nor any `||`), no `set +e`, the runner's default
        # shell, and neither continue-on-error nor if:.
        assert "||" not in commands
        assert "set +e" not in commands
        assert "shell" not in step
        assert "continue-on-error" not in step
        assert "if" not in step
        # TestPyPI alone, with no pypi.org fallback that a same-name squatter could answer (juniper-ml#384).
        assert "--index-url https://test.pypi.org/simple/" in commands
        assert "--extra-index-url" not in commands


def _run_install(workflow: str, tmp_path: Path, pip_failures: int, python_status: int = 0, tag: str = "v1.2.3") -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    """Run WORKFLOW's install step as the runner runs a ``run:`` without a ``shell:`` (``bash -e {0}``), against stand-in
    ``pip``, ``python`` and ``sleep`` commands that log each call (the command, its directory, its arguments): ``pip``
    fails its first PIP_FAILURES calls, and ``python`` exits with PYTHON_STATUS. A sub-package's version is 1.2.3."""
    package = PUBLISHERS[workflow][0]
    bin_dir, runner_temp, workspace = tmp_path / "bin", tmp_path / "runner-temp", tmp_path / "workspace"
    for directory in (bin_dir, runner_temp, workspace / package):
        directory.mkdir(parents=True)
    (workspace / package / "pyproject.toml").write_text('[project]\nname = "stand-in"\nversion = "1.2.3"\n', encoding="utf-8")
    log = tmp_path / "calls.log"
    stubs = {"pip": 'test "$(grep -c "^pip" "$STUB_LOG")" -gt "$STUB_PIP_FAILURES"\n', "python": 'exit "$STUB_PYTHON_STATUS"\n', "sleep": ""}
    for name, body in stubs.items():
        stub = bin_dir / name
        stub.write_text(f'#!/bin/sh\nprintf "%s\\t%s\\t%s\\n" "{name}" "$(pwd -P)" "$*" >> "$STUB_LOG"\n{body}', encoding="utf-8")
        stub.chmod(0o700)
    script = tmp_path / "install.sh"
    script.write_text(_step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])["run"], encoding="utf-8")
    bash = shutil.which("bash")
    assert bash, "the install checks run under bash"
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "RUNNER_TEMP": str(runner_temp), "GITHUB_WORKSPACE": str(workspace), "RELEASE_TAG": tag, "STUB_LOG": str(log), "STUB_PIP_FAILURES": str(pip_failures), "STUB_PYTHON_STATUS": str(python_status)}
    proc = subprocess.run([bash, "-e", str(script)], cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=60, check=False)  # nosec B603 - fixed argv: bash and the workflow's own extracted step
    calls = [line.split("\t", 2) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    return proc, calls


class TestInstallCheckScript:
    """Each install step's own shell, run as the runner runs it, against stand-in ``pip``, ``python`` and ``sleep``."""

    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_index_lag_that_outlasts_every_try_fails_naming_the_lag_and_never_imports(self, workflow, tmp_path):
        proc, calls = _run_install(workflow, tmp_path, pip_failures=INSTALL_TRIES)
        assert proc.returncode == 1
        assert f"::error::{PUBLISHERS[workflow][0]} 1.2.3 {LAG_ERROR}" in proc.stdout
        assert [call[0] for call in calls if call[0] != "sleep"] == ["pip"] * INSTALL_TRIES
        # A wait between tries and none after the last; publish.yml waits once before the first.
        first = [str(INSTALL_FIRST_WAIT_SECONDS)] if workflow == "publish.yml" else []
        assert [call[2] for call in calls if call[0] == "sleep"] == first + [str(INSTALL_RETRY_SECONDS)] * (INSTALL_TRIES - 1)

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
        assert [call[0] for call in calls if call[0] != "sleep"] == ["pip", "python"]

    def test_the_release_tag_is_read_as_data_never_run_as_script(self, tmp_path):
        # The tag reaches publish.yml's check through env: text in it that a shell would run, if pasted into the script,
        # is only a version that does not install.
        proc, calls = _run_install("publish.yml", tmp_path, pip_failures=0, tag="v1.2.3$(touch pasted)")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert [call[2] for call in calls if call[0] == "pip"] == ["install --no-deps --index-url https://test.pypi.org/simple/ juniper-cascor==1.2.3$(touch pasted)"]
        assert not list(tmp_path.rglob("pasted"))


'''),
    # base line 389
    (r'''        assert "concurrency" not in wf
        # The new dispatch builds nothing: this guard reads a release's tag, and a dispatch has none.
        assert wf["jobs"]["build"]["if"] == "startsWith(github.event.release.tag_name, 'v')"
        assert "if" not in wf["jobs"]["testpypi"]
''',
     r'''        # A concurrency group may queue its runs, never cancel one in progress: that could stop it between two uploads.
        assert not _cancels(wf.get("concurrency"))
        # The new dispatch builds nothing: this guard reads a release's tag, and a dispatch has none.
        assert wf["jobs"]["build"]["if"] == "startsWith(github.event.release.tag_name, 'v')"
        assert "if" not in wf["jobs"]["testpypi"]
        assert "if" not in wf["jobs"][INSTALL]
'''),
    # base line 406
    (r'''        # A plain dispatch still re-fires the whole publish; the republish dispatch runs the republish job alone.
        assert wf["jobs"]["build"]["if"] == f"(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)"
''',
     r'''        # A plain dispatch still re-fires the whole publish, from the package's own tag alone (a `v` tag's would publish
        # this package's files under the app's tag); the republish dispatch runs the republish job alone.
        assert wf["jobs"]["build"]["if"] == f"(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi && startsWith(github.ref_name, '{package}-v'))"
'''),
    # base line 426
    (r'''        jobs = [_workflow(workflow)["jobs"][REPUBLISH] for workflow in PUBLISHERS]
        assert all(job == jobs[0] for job in jobs)
''',
     r'''        # Compared with each action's @ref dropped: the next case pins each action to one ref in every publisher, so a
        # partial bump fails there, once, rather than here as a template difference.
        jobs = [_by_action(_workflow(workflow)["jobs"][REPUBLISH]) for workflow in PUBLISHERS]
        assert all(job == jobs[0] for job in jobs)

    def test_each_action_is_pinned_to_one_ref_in_every_publisher(self):
        # Dependabot bumps an action in all three files at once; a hand edit that bumps one copy fails here, wherever it is.
        refs: dict[str, set[str]] = {}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    if step.get("uses"):
                        name, _, ref = str(step["uses"]).partition("@")
                        refs.setdefault(name, set()).add(ref)
        assert {name: len(found) for name, found in refs.items()} == dict.fromkeys(refs, 1), refs
'''),
    # base line 667
    (r'''
class TestFindReleaseRun:
''',
     r'''
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


LIVE_ARTIFACT = [{"id": 7, "name": "juniper-cascor-dist", "expired": False}]


class TestFindReleaseRun:
'''),
    # base line 673
    (r'''    def test_the_newest_release_run_that_still_holds_the_artifact_is_found(self, workspace, tmp_path, stand):
        server = stand(
            {
                _runs_path("v9.9.9"): [(200, {"workflow_runs": [{"id": 111, "head_branch": "v9.9.9"}, {"id": 333, "head_branch": "v9.9.9"}, {"id": 222, "head_branch": "v9.9.9"}]})],
                _artifacts_path(333): [(200, {"artifacts": [{"id": 1, "name": "juniper-cascor-dist", "expired": True}]})],
                _artifacts_path(222): [(200, {"artifacts": [{"id": 2, "name": "juniper-cascor-dist", "expired": False}]})],
                _artifacts_path(111): [(200, {"artifacts": [{"id": 3, "name": "juniper-cascor-dist", "expired": False}]})],
            }
        )
        proc = _run(_script(FIND, tmp_path), workspace, **self._env(tmp_path, server))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _outputs(tmp_path) == {"version": "9.9.9", "run-id": "222"}
        assert _artifacts_path(111) not in server.paths()

    def test_a_sub_package_tag_names_its_version(self, workspace, tmp_path, stand):
        tag = "juniper-cascor-model-v1.2.3"
        server = stand({_runs_path(tag, "publish-cascor-model.yml"): [(200, {"workflow_runs": []})]})
        proc = _run(_script(FIND, tmp_path), workspace, PUBLISH_PACKAGE="juniper-cascor-model", **self._env(tmp_path, server, tag=tag, workflow="publish-cascor-model.yml"))
''',
     r'''    @staticmethod
    def _serve(stand, jobs: list[dict], artifacts: list[dict] | None = None, tag: str = "v9.9.9", workflow: str = "publish.yml", package: str = "juniper-cascor") -> _Stand:
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
        server = self._serve(stand, _attempt(1, 100), artifacts=[{"id": 7, "name": "juniper-cascor-dist", "expired": True}])
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
        tag = "juniper-cascor-model-v1.2.3"
        server = self._serve(stand, _attempt(1, 100), artifacts=[], tag=tag, workflow="publish-cascor-model.yml", package="juniper-cascor-model")
        proc = _run(_script(FIND, tmp_path), workspace, PUBLISH_PACKAGE="juniper-cascor-model", PUBLISH_TAG_PREFIX="juniper-cascor-model-v", **self._env(tmp_path, server, tag=tag, workflow="publish-cascor-model.yml"))
'''),
    # base line 695
    (r'''    @pytest.mark.parametrize(("tag", "ref_type"), [("v9.9.9", "branch"), ("main", "branch"), ("juniper-cascor-model-v1.2.3", "tag")], ids=["branch-named-like-a-tag", "branch", "another-packages-tag"])
''',
     r'''    @pytest.mark.parametrize(
        ("tag", "ref_type"),
        [("v9.9.9", "branch"), ("main", "branch"), ("juniper-cascor-model-v1.2.3", "tag"), ("juniper-cascor-v9.9.9", "tag"), ("v", "tag")],
        ids=["branch-named-like-a-tag", "branch", "another-packages-tag", "a-package-named-tag-in-a-single-package-publisher", "a-prefix-without-a-version"],
    )
'''),
    # base line 704
    (r'''    def test_an_api_failure_fails_the_job_rather_than_skip_the_check(self, workspace, tmp_path, stand):
        server = stand({_runs_path("v9.9.9"): [(502, {"message": "bad gateway"})]})
''',
     r'''    @pytest.mark.parametrize("tag", ["v1.2.3", "juniper-cascor-protocol-v1.2.3", "juniper-cascor-model-1.2.3"], ids=["the-meta-packages-v-tag", "a-sibling-sub-packages-tag", "a-tag-without-the-v"])
    def test_a_sub_package_publisher_refuses_every_tag_but_its_own_prefix(self, workspace, tmp_path, stand, tag):
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
'''),
    # base line 769
    (r'''        assert not [p for p, _ in server.requests if p.startswith("/files/")]

    @pytest.mark.parametrize(
''',
     r'''        assert not [p for p, _ in server.requests if p.startswith("/files/")]

    @pytest.mark.parametrize("which", ["the-release-run-lists-more", "testpypi-lists-more"])
    def test_testpypi_and_the_release_runs_sha256sums_must_name_the_same_files(self, tmp_path, stand, which):
        # A file one of them names and the other does not is refused, in either direction, before any file is fetched.
        root = tmp_path / "workspace"
        root.mkdir()
        extra = "juniper_cascor-9.9.9-py2.py3-none-any.whl"
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
'''),
)
# END TEST_EDITS


def test_file(text: str) -> str:
    for old, new in TEST_EDITS:
        text = replace_once(text, old, new, TEST_PATH)
    return text


# ─────────────────────────────────────────────────────────────────────────────────────────────
# src/tests/unit/test_publish_docs_bounds.py: a new module, written whole (the review's docs pins). It reads the docs as
# well as the workflows, so it stays out of test_publish_one_artifact.py, whose non-vacuity check copies the workflows
# alone. Spliced from the reviewed file; the writer refuses a tree that already holds it.
# ─────────────────────────────────────────────────────────────────────────────────────────────
DOCS_TEST_PATH = "src/tests/unit/test_publish_docs_bounds.py"
# BEGIN DOCS_TEST
DOCS_TEST = r'''"""Pin the publish docs' numbers to the publish workflows: the bounds the docs state are the bounds the steps run.

``docs/ci_cd/MANUAL.md`` and ``docs/ci_cd/REFERENCE.md`` give an operator the numbers that decide whether a failed
check was lag: how often and how far apart the JSON checks poll, how long each request may take, how many times the
install checks try and how long they wait. Each is read here from the workflows and required in the docs, so a change
to either side alone fails. A module of its own: ``test_publish_one_artifact.py`` reads the workflows alone, and its
non-vacuity check (``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py``) copies only those.

Project: juniper-cascor
Author: Paul Calnon
Created: 2026-11-23
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# CI's unit lane runs ``pytest -m "unit and not slow" src/tests/unit``, so an unmarked test is collected and then
# silently DESELECTED. Module-level, so it covers tests added later.
pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[3]
WORKFLOWS = REPO / ".github" / "workflows"
DOCS = REPO / "docs" / "ci_cd"
#: The JSON check every copy of the template runs; its first copy, in publish.yml's TestPyPI job, is read here.
INDEX_CHECK = "Verify TestPyPI serves exactly these files"
INSTALL = "verify-testpypi-install"
#: workflow -> its install check's step name
INSTALL_STEPS = {"publish.yml": "Verify TestPyPI install", "publish-cascor-model.yml": "Verify install from TestPyPI (no-deps, version-only import)", "publish-protocol.yml": "Verify install from TestPyPI"}


def _jobs(workflow: str) -> dict:
    return yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))["jobs"]


def _run(job: dict, name: str) -> str:
    found = [s for s in job.get("steps") or [] if s.get("name") == name]
    assert len(found) == 1, f"expected exactly one step named {name!r}"
    return str(found[0]["run"])


def _doc(name: str) -> str:
    """The doc's text with each run of whitespace made one space: a rewrapped paragraph states the same bounds."""
    return " ".join((DOCS / name).read_text(encoding="utf-8").split())


def _retry(workflow: str) -> tuple[int, list[int], list[int]]:
    """The install check's (tries, the waits inside its loop, the waits before it), read from its commands."""
    run = _run(_jobs(workflow)[INSTALL], INSTALL_STEPS[workflow])
    commands = [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]
    loops = [i for i, c in enumerate(commands) if re.fullmatch(r"for attempt in [0-9 ]+; do", c)]
    assert len(loops) == 1, f"{workflow}: expected one retry loop"
    start, end = loops[0], commands.index("done", loops[0])
    tries = len(commands[start].split()[3:-1])
    waits = [int(c.split()[1]) for c in commands[start:end] if re.fullmatch(r"sleep [0-9]+", c)]
    before = [int(c.split()[1]) for c in commands[:start] if re.fullmatch(r"sleep [0-9]+", c)]
    return tries, waits, before


class TestPublishDocsStateTheBounds:
    def test_the_json_checks_bounds(self):
        run = _run(_jobs("publish.yml")["testpypi"], INDEX_CHECK)
        attempts = int(re.search(r'"HASH_CHECK_ATTEMPTS", "(\d+)"', run).group(1))
        interval = int(re.search(r'"HASH_CHECK_INTERVAL", "(\d+)"', run).group(1))
        timeout = int(re.search(r"urllib\.request\.urlopen\(request, timeout=(\d+)\)", run).group(1))
        slept = (attempts - 1) * interval
        # The worst case: every sleep, and every request running to its timeout.
        minutes = round((slept + attempts * timeout) / 60)
        reference = _doc("REFERENCE.md")
        assert f"The JSON checks poll up to {attempts} times, {interval} s apart" in reference
        assert f"{slept} s of sleep, plus up to {attempts} request timeouts of {timeout} s" in reference
        assert f"A JSON check gives up after {attempts} attempts | The index never listed the version or a file within the bound: {attempts - 1} sleeps of {interval} s ({slept} s) plus up to {attempts} request timeouts of {timeout} s, about {minutes} minutes at worst" in _doc("MANUAL.md")

    def test_the_install_checks_retry(self):
        found = {workflow: _retry(workflow) for workflow in INSTALL_STEPS}
        tries, waits, _ = found["publish.yml"]
        # One loop in all three: its tries, a wait between them and none after the last; publish.yml waits once first.
        assert {workflow: (n, w) for workflow, (n, w, _) in found.items()} == dict.fromkeys(INSTALL_STEPS, (tries, waits))
        assert len(waits) == 1
        assert {workflow: before for workflow, (_, _, before) in found.items()} == {"publish.yml": found["publish.yml"][2], "publish-cascor-model.yml": [], "publish-protocol.yml": []}
        assert len(found["publish.yml"][2]) == 1
        wait, first = waits[0], found["publish.yml"][2][0]
        retry = f"{tries} tries, {wait} s apart"
        reference = _doc("REFERENCE.md")
        assert reference.count(f"; {retry} |") == len(INSTALL_STEPS)
        assert f"after a {first} s wait; {retry} |" in reference
        assert f"Each install check makes {retry} (`publish.yml` waits {first} s first)" in _doc("MANUAL.md")
        # The error each check stops with after its last try, as each step prints it and as the docs quote it.
        error = f"is not installable from TestPyPI after {tries} tries (index lag?)"
        for workflow in INSTALL_STEPS:
            assert error in _run(_jobs(workflow)[INSTALL], INSTALL_STEPS[workflow])
        for name in ("REFERENCE.md", "MANUAL.md"):
            assert error in _doc(name)
'''
# END DOCS_TEST


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Docs (items 7, 11, 15, 20, 21, 26, and the new job, gate and parameter) and the CHANGELOG entry
# ─────────────────────────────────────────────────────────────────────────────────────────────
MANUAL = "docs/ci_cd/MANUAL.md"
REFERENCE = "docs/ci_cd/REFERENCE.md"
QUICK_START = "docs/ci_cd/QUICK_START.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET.md"
AGENTS = "AGENTS.md"
CHANGELOG = "CHANGELOG.md"

MANUAL_EDITS = (
    (
        "   TestPyPI's JSON must list exactly those files and sha256\n        │\n        ▼\n"
        "   Verify install from TestPyPI ONLY\n   (--no-deps, --index-url https://test.pypi.org/simple/)\n        │\n        ▼\n"
        "   Publish to PyPI      (environment: pypi, id-token: write, needs: testpypi)\n",
        "   TestPyPI's JSON must list exactly those files and sha256\n        │\n        ▼\n"
        "   Verify the TestPyPI install  (its own job: contents: read, no environment, no id-token)\n"
        "   install from TestPyPI ONLY, outside any checkout\n   (--no-deps, --index-url https://test.pypi.org/simple/)\n        │\n        ▼\n"
        "   Publish to PyPI      (environment: pypi, id-token: write, needs: both TestPyPI jobs)\n",
    ),
    (
        "`juniper-cascor-protocol` asserts via `importlib.metadata` because importing the package pulls the numpy BinaryFrame codec (absent under `--no-deps`).\n\n### One Artifact, Checked Against TestPyPI\n",
        "`juniper-cascor-protocol` asserts via `importlib.metadata` because importing the package pulls the numpy BinaryFrame codec (absent under `--no-deps`), "
        "and finds the package with `importlib.util.find_spec`, which locates it without running it: the metadata alone would pass a wheel that lacks the package.\n\n"
        "**The install check runs in a job of its own**, `Verify the TestPyPI install` (ruling 2 of 2026-11-16). It needs `Publish to TestPyPI`, and `Publish to PyPI` needs both. "
        "It runs the package TestPyPI serves, so it holds `contents: read` and nothing else, with no environment and no `id-token`: nothing it runs can mint a credential, and the job that can, `Publish to TestPyPI`, runs only the template steps and the upload. "
        "It installs and imports from `$RUNNER_TEMP`, outside any checkout: `python -c` puts its working directory first on `sys.path`, and this repository's root holds `juniper_cascor/`, so an import run in a checkout could pass without the wheel. "
        "A sub-package's job reads its version from a sparse checkout that keeps no credential (`persist-credentials: false`), and `publish.yml`'s reads the release's tag through the step's `env`, never pasted into the script. "
        "Each install check makes 5 tries, 10 s apart (`publish.yml` waits 30 s first), because TestPyPI's simple index can lag behind its JSON. "
        "After the fifth failed try it stops with `… is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats`, rather than fall through to an import that fails as if the package were broken. "
        "Its name holds `TestPyPI`, so juniper-ml's release-train ceremony reads its failure as `HALT_TESTPYPI`. The ceremony's monitor gives a run 900 s (`DEFAULT_MONITOR_TIMEOUT_SECONDS`) to reach the `pypi` gate, and the new job adds one job start to that path.\n\n"
        "### One Artifact, Checked Against TestPyPI\n",
    ),
    (
        "**Intent:** PyPI receives exactly the files TestPyPI took and the install check tested, and the run proves it.",
        "**Intent:** PyPI receives exactly the files TestPyPI took, whose wheel the install check installed, and the run proves it.",
    ),
    (
        "it witnesses what the install check tested. Only the jobs that upload hold `id-token: write`, so the build cannot mint a credential. The step-by-step contract",
        "it witnesses the files the PyPI job uploads, whose wheel the install check installed. Only the jobs that upload hold `id-token: write`, so neither the build nor the install check can mint a credential. The step-by-step contract",
    ),
    (
        "read nothing but the workflow `env` values `PUBLISH_PACKAGE` (the distribution's name on the index) and `PUBLISH_DIST_DIR` (where the build writes, relative to the workspace), each JSON check's `INDEX_URL`, and the runner's own variables. Copy them verbatim, set the two values,",
        "read nothing but the workflow `env` values `PUBLISH_PACKAGE` (the distribution's name on the index), `PUBLISH_DIST_DIR` (where the build writes, relative to the workspace) and `PUBLISH_TAG_PREFIX` "
        "(what the package's release tags start with: `v` in a single-package publisher, `<package>-v` in a sub-package one; the build job's tag guard names the same prefix, since a job-level `if:` cannot read `env`), "
        "each JSON check's `INDEX_URL`, and the runner's own variables. Copy them verbatim, set the three values,",
    ),
    (
        "4. TestPyPI's JSON after the TestPyPI upload and before the install check, and again before the PyPI upload;\n5. PyPI's JSON after the PyPI upload;\n6. the `republish` job",
        "4. TestPyPI's JSON after the TestPyPI upload, as that job's last step, and again before the PyPI upload;\n"
        "5. the install check in a job of its own, `Verify the TestPyPI install`, which needs the TestPyPI job, holds `contents: read` alone, and installs and imports from `$RUNNER_TEMP`; the PyPI job needs both;\n"
        "6. PyPI's JSON after the PyPI upload;\n7. the `republish` job",
    ),
    (
        "Give the workflow `permissions: {}` (or `contents: read`) and each job its own: the build `contents: read` and `actions: read`; each uploading job `id-token: write`, plus `contents: read` where it checks out; the republish job `actions: read` and `id-token: write`.",
        "Give the workflow `permissions: {}` (or `contents: read`) and each job its own, which replace the workflow's rather than add to them: the build `contents: read` and `actions: read`; the TestPyPI job and the PyPI job `id-token: write` alone, since neither checks anything out; "
        "the install check `contents: read` alone; the republish job `actions: read` and `id-token: write`.",
    ),
    (
        "If the build job already runs on a dispatch, exclude the republish dispatch from its `if:`, as the sub-package publishers do.",
        "If the build job already runs on a dispatch, exclude the republish dispatch from its `if:`, and admit a plain dispatch only from the package's own tag (`startsWith(github.ref_name, '<prefix>')`), as the sub-package publishers do.",
    ),
    (
        "Never set `skip-existing` on the TestPyPI upload: an earlier file under the same name would be kept silently, and the install check would test that file.\n",
        "Never set `skip-existing` (nor the action's older `skip_existing`) on the TestPyPI upload: an earlier file under the same name would be kept silently, and the install check would test that file. "
        "Nor `attestations: false`; and no `continue-on-error`, `|| true` or `if:` beyond the template's on any check: each switches a check off.\n",
    ),
    (
        "   Only `Republish the tested files (dispatch only)` runs. It waits at the `pypi` gate like the release run (a fresh approval, then the 5-minute timer), builds nothing, downloads the version's files from TestPyPI, "
        "checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. It does not depend on the release run's age, "
        "only on TestPyPI still holding the files, and it works only from a tag whose workflow carries the job: tags cut before this change merged do not.\n",
        "   Only `Republish the tested files (dispatch only)` runs. It waits at the `pypi` gate like the release run (a fresh approval, then the 5-minute timer). "
        "Its first step then refuses unless the tag's newest release run of the workflow exists and each of its jobs whose name holds `TestPyPI`, `Publish to TestPyPI` and `Verify the TestPyPI install`, concluded success in its latest attempt (ruling 1 of 2026-11-16). "
        "A re-run gives every job a record in the new attempt: one it runs again gets its new result, and one \"Re-run failed jobs\" carries over gets a copy of its earlier one, so each job counts with its newest result. "
        "Then it builds nothing, downloads the version's files from TestPyPI, checks each file's bytes against TestPyPI's JSON and, while the release run's artifact exists (90 days), against its `SHA256SUMS`, uploads them, and checks PyPI's JSON. "
        "Once the artifact has expired, TestPyPI's JSON is the only record: the job takes every file TestPyPI lists for the version, each checked against the sha256 listed with it. "
        "It needs neither the release run's artifact nor its re-run window: only the run's record and TestPyPI still holding the files.\n",
    ),
    (
        "fetches the exact files that run built, for inspection.\n\n**Never",
        "fetches the exact files that run built, for inspection.\n\n"
        "**When rung 1 refuses, or a release run failed before PyPI:**\n\n"
        "- **A TestPyPI job failed on index lag** (a JSON check gave up, or the install check stopped with `… is not installable from TestPyPI after 5 tries (index lag?)`, before TestPyPI served the version): within 30 days, \"Re-run failed jobs\" on the release run. "
        "It runs the failed job and those after it again. A re-run `Publish to TestPyPI` uploads the same bytes, from the run's artifact, which the index accepts (HTTP 200 for a byte-identical file), and repeats its JSON check; the install check then runs again. "
        "Once both pass, the PyPI job waits at the gate as usual, and rung 1 has a release run to accept.\n"
        "- **The install check failed for real** (the package does not install or import, and a re-run fails the same way): cut a new patch version. If unsure, Re-run failed jobs first: index lag passes on a re-run, and a real failure repeats. "
        "Neither a re-run nor a same-version re-cut can fix a real failure, because the index refuses new bytes under a file name it already holds.\n"
        "- **A Release that was re-cut**: never delete a Release and publish it again to retry; use \"Re-run failed jobs\". A re-cut starts a new release run, which builds again. Once TestPyPI holds the version, it refuses the new run's files (HTTP 400: it holds those file names), "
        "and that failed run is then the tag's newest, so rung 1 refuses the tag for good, and the next rung applies: \"Re-run failed jobs\" on the original release run, within 30 days of it; then rung 3.\n"
        "- **A sub-package version that a plain `workflow_dispatch` re-fire published**: no release run of its tag passed its TestPyPI jobs, so rung 1 refuses it. Rung 2, \"Re-run failed jobs\", applies to that dispatch run, within 30 days of it; then rung 3.\n"
        "- **A tag that is not `PUBLISH_TAG_PREFIX` followed by the exact version** (`v<version>` here; `juniper-cascor-model-v<version>` and `juniper-cascor-protocol-v<version>` for the sub-packages): the republish takes the version from the tag, so such a tag cannot be republished, and the job fails without publishing "
        "(juniper-data-client's `v0.3.1-beta`, which shipped 0.3.1's files, is one). For tags cut after this change, a sub-package publisher dispatched from a `v<version>` tag publishes nothing: with `republish_from_testpypi` the republish job refuses the tag before any request, and without it the build job's guard skips the run.\n\n"
        "Each rung acts on the workflow file as of the tag: a tag cut before juniper-cascor#767 merged (2026-11-15), 0.14.0's included, has no rung 1, and one cut before this change runs rung 1 without the check of the release run's TestPyPI jobs.\n\n"
        "**Never",
    ),
    (
        "| TestPyPI verify can't find the version | Index lag | Protocol/model retry 5× with 10s sleep; main package sleeps 30s once — re-run the verify step if lag exceeds that |\n",
        "| `Verify the TestPyPI install` fails: `… is not installable from TestPyPI after 5 tries (index lag?)` | TestPyPI's simple index had not caught up after the 5 tries, or the package does not install | "
        "Use Re-run failed jobs on the release run: it runs the install job again, then the PyPI job. Index lag passes on a re-run; a real failure repeats, and needs a new patch version |\n",
    ),
    (
        "| `Verify TestPyPI serves exactly these files` or `Verify PyPI serves exactly these files` fails: the index lists a file this run did not build, or with another sha256 | The index already held other files for this version (an earlier run's build), or the artifact is not what the build recorded | Do not publish this version from this run; find which upload put the other file there. When the TestPyPI check failed, the run stopped before the PyPI upload |\n",
        "| `Verify TestPyPI serves exactly these files` fails: TestPyPI lists a file this run did not build, or with another sha256 | TestPyPI already held other files for this version (an earlier run's build), or the artifact is not what the build recorded | The run stopped before the install check and the PyPI upload, and rung 1 refuses the version. Find which upload put the other file there; cut a new patch version |\n"
        "| `Verify PyPI serves exactly these files` fails: PyPI lists a file this run did not build, or with another sha256 | PyPI already held another file for this version (an earlier upload) | This run's files are already on PyPI: the step runs after the upload, so there is no publish left to stop. Compare PyPI's JSON for the version with TestPyPI's and find which upload put the other file there; only a new patch version ships tested files under a clean version |\n",
    ),
    (
        "| Protocol verify import fails under `--no-deps` |",
        "| `Republish the tested files` fails at `Find the release run's artifact` | The tag is not `PUBLISH_TAG_PREFIX` and the version; the tag has no release run of this workflow; or a job of that run whose name holds `TestPyPI` did not conclude success in its latest attempt (ruling 1 of 2026-11-16), "
        "which is also what a re-cut Release of a version TestPyPI held leaves: a newest run that TestPyPI refused | "
        "The job's log names each TestPyPI job and its conclusion. Index lag: within 30 days, Re-run failed jobs on the release run, then rung 1 again if PyPI still lacks the version. A failed install check: Re-run failed jobs first; if it fails again, a new patch version. "
        "A re-cut Release: Re-run failed jobs on the original release run, within 30 days of it. A sub-package version a plain dispatch published: Re-run failed jobs on that dispatch run |\n"
        "| Protocol verify import fails under `--no-deps` |",
    ),
    (
        "| Protocol verify import fails under `--no-deps` | Expecting `import juniper_cascor_protocol` | Use `importlib.metadata` version check (workflow already does) |\n",
        "| Protocol verify import fails under `--no-deps` | Expecting `import juniper_cascor_protocol` | Use `importlib.metadata` for the version and `importlib.util.find_spec` for the package (the workflow does both) |\n",
    ),
    (
        "Dispatch from the release tag: both publish environments admit tag refs only, so a dispatch from a branch fails at `Publish to TestPyPI`.",
        "Dispatch from the release tag. A dispatch runs the workflow file as of its ref, so for tags cut after this change the build job runs a plain dispatch only from a ref whose name starts with the package's own prefix: one from a `v<version>` tag or another package's tag builds nothing. "
        "The guard tests the ref's name, not that it is a tag; both publish environments admit tag refs only, so a dispatch from a branch publishes nothing either.",
    ),
)

REFERENCE_EDITS = (
    (
        "they read only the workflow `env` values `PUBLISH_PACKAGE` and `PUBLISH_DIST_DIR`, a JSON check's `INDEX_URL`, and the runner's own variables",
        "they read only the workflow `env` values `PUBLISH_PACKAGE`, `PUBLISH_DIST_DIR` and `PUBLISH_TAG_PREFIX`, a JSON check's `INDEX_URL`, and the runner's own variables",
    ),
    (
        "| `Verify TestPyPI serves exactly these files` | TestPyPI job, after the upload | `https://test.pypi.org/pypi/<package>/<version>/json` lists exactly those files and sha256 |\n",
        "| `Verify TestPyPI serves exactly these files` | TestPyPI job, after the upload, its last step | `https://test.pypi.org/pypi/<package>/<version>/json` lists exactly those files and sha256 |\n"
        "| `Verify the TestPyPI install` (a job, not a template step) | after the TestPyPI job; the PyPI job needs both | The repository's own install check, run from `$RUNNER_TEMP`, outside any checkout, with `contents: read` alone: no environment, no `id-token` (ruling 2 of 2026-11-16) |\n",
    ),
    (
        "| `Find the release run's artifact` | republish (dispatch only), first | The version from the tag (`v<version>` or `<package>-v<version>`; anything else is refused); the newest release run for that tag still holding `<PUBLISH_PACKAGE>-dist` |\n",
        "| `Find the release run's artifact` | republish (dispatch only), first | The version from the tag, `PUBLISH_TAG_PREFIX` and the version; anything else is refused before any request. The tag's newest release run of this workflow must exist, and each of its jobs whose name holds `TestPyPI` must have concluded success in its latest attempt "
        "(`GET actions/runs/{id}/jobs?filter=all`, each job's record with the highest `(run_attempt, id)`; ruling 1 of 2026-11-16). That run's `<PUBLISH_PACKAGE>-dist`, while unexpired, gives the next step its `run-id` |\n",
    ),
    (
        "| workflow `permissions` | `{}` (`publish.yml`); `contents: read` (protocol/model) | No job inherits `id-token: write` |\n"
        "| build job | `contents: read`, `actions: read` | Checkout; the reuse step lists the run's artifacts. No `id-token`, so the build backend cannot mint a token |\n"
        "| TestPyPI job | `contents: read`, `id-token: write` | Checkout / sparse-checkout for the install check; OIDC token for Trusted Publishing |\n",
        "| workflow `permissions` | `{}` (`publish.yml`); `contents: read` (protocol/model) | No job inherits `id-token: write`; a job's own block replaces this one rather than adding to it |\n"
        "| build job | `contents: read`, `actions: read` | Checkout; the reuse step lists the run's artifacts. No `id-token`, so the build backend cannot mint a token |\n"
        "| TestPyPI job | `id-token: write` | OIDC token for Trusted Publishing. It checks out nothing and runs no install check: the job that can mint runs only the template steps and the upload |\n"
        "| install-check job (`Verify the TestPyPI install`) | `contents: read` | The sparse checkout a sub-package reads its version from, which keeps no credential (`persist-credentials: false`). No environment and no `id-token`: it runs the package TestPyPI serves |\n",
    ),
    (
        "republish job is step 1 of the recovery ladder: [`MANUAL.md` § Recovering a Release That Did Not Reach PyPI](MANUAL.md#recovering-a-release-that-did-not-reach-pypi). Pinned by `src/tests/unit/test_publish_one_artifact.py`.\n",
        "republish job is step 1 of the recovery ladder: [`MANUAL.md` § Recovering a Release That Did Not Reach PyPI](MANUAL.md#recovering-a-release-that-did-not-reach-pypi). Pinned by `src/tests/unit/test_publish_one_artifact.py`, "
        "and the numbers in this paragraph by `src/tests/unit/test_publish_docs_bounds.py`.\n",
    ),
    (
        "| PyPI job | `id-token: write` (`publish.yml`); plus `contents: read` (protocol/model) | OIDC token for Trusted Publishing |\n",
        "| PyPI job | `id-token: write` | OIDC token for Trusted Publishing. It checks out nothing |\n",
    ),
    (
        "| `juniper-cascor` | `--no-deps --index-url https://test.pypi.org/simple/` + 30s sleep | `from juniper_cascor import __version__` |\n"
        "| `juniper-cascor-model` | same + 5×10s retry | `import juniper_cascor_model` + `__version__` |\n"
        "| `juniper-cascor-protocol` | same + 5×10s retry | `importlib.metadata.version(...)` (no package import) |\n\nConstraints:\n",
        "| `juniper-cascor` | `--no-deps --index-url https://test.pypi.org/simple/`, after a 30 s wait; 5 tries, 10 s apart | `from juniper_cascor import __version__` |\n"
        "| `juniper-cascor-model` | `--no-deps --index-url https://test.pypi.org/simple/`; 5 tries, 10 s apart | `import juniper_cascor_model` + `__version__` |\n"
        "| `juniper-cascor-protocol` | `--no-deps --index-url https://test.pypi.org/simple/`; 5 tries, 10 s apart | `importlib.metadata.version(...)`, and `importlib.util.find_spec(...)` for the package (no package import) |\n\n"
        "Each runs in the job `Verify the TestPyPI install`, after `Publish to TestPyPI`, from `$RUNNER_TEMP` (`cd \"${RUNNER_TEMP}\"` first, outside any checkout), and `Publish to PyPI` needs it. "
        "After the fifth failed try it fails with `::error::<package> <version> is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats`, rather than fall through to the import. "
        "`publish.yml`'s reads the release's tag through the step's `env` (`RELEASE_TAG`), never pasted into the script.\n\n"
        "Constraints:\n",
    ),
    (
        "- A release that did not reach PyPI: the republish dispatch, then (within 30 days) **Re-run failed jobs**, then a new patch version",
        "- No `|| true`, `set +e`, `exit 0`, `trap`, `continue-on-error` or `if:` on the install check, and no `PIP_*` variable in any `env`: each would switch it off or send it to another index.\n"
        "- A release that did not reach PyPI: the republish dispatch, which refuses unless the tag's newest release run passed its TestPyPI jobs, then (within 30 days) **Re-run failed jobs**, then a new patch version",
    ),
)

QUICK_START_EDIT = (
    "→ install verify (`--no-deps`, TestPyPI index only) →",
    "→ install verify, in a job of its own that cannot mint a credential (`--no-deps`, TestPyPI index only, outside any checkout) →",
)

CHEATSHEET_EDITS = (
    (
        "TestPyPI verify uses `--no-deps` and TestPyPI index only. Every publisher builds once:",
        "TestPyPI verify runs in a job of its own, `Verify the TestPyPI install`, which cannot mint a credential and imports from outside any checkout; it uses `--no-deps` and TestPyPI index only, and `Publish to PyPI` needs it. Every publisher builds once:",
    ),
    (
        "(copies TestPyPI's files, builds nothing);",
        "(copies TestPyPI's files, builds nothing, and refuses unless the tag's newest release run passed its TestPyPI jobs);",
    ),
)

AGENTS_EDIT = (
    "→ install verify → PyPI, after TestPyPI's sha256 are checked again → sha256 check against PyPI's JSON. The dispatch republishes TestPyPI's files (one-artifact",
    "→ install verify (a job of its own, no `id-token`) → PyPI, after TestPyPI's sha256 are checked again → sha256 check against PyPI's JSON. The dispatch republishes TestPyPI's files once the release run passed its TestPyPI jobs (one-artifact",
)

CHANGELOG_ANCHOR = "    `docs/DEVELOPER_CHEATSHEET.md` (1.0.12) and `AGENTS.md`.\n\n"
# The round-4 review (a NIT): #767's own [Unreleased] entry, corrected in place. TestPyPI's record witnesses the files,
# and the install check installs their wheel alone (F8e of the round-2 review, on the PyPI job's comment).
CHANGELOG_767_OLD = "    record cannot change after the TestPyPI job: it witnesses what the install check tested.\n"
CHANGELOG_767_NEW = (
    "    record cannot change after the TestPyPI job: it witnesses the files the run built, whose wheel the install check\n"
    "    installs; no check installs the sdist.\n"
)
CHANGELOG_ENTRY = """\
- **The republish job copies nothing a release run did not pass, and the install check can mint no credential**
  (rulings 1 and 2 of 2026-11-16, on the one-artifact template above). `publish.yml`, `publish-cascor-model.yml` and
  `publish-protocol.yml` get the same changes, and the other Juniper publishers copy them.
  - **The install check has a job of its own** (ruling 2). `Verify the TestPyPI install` needs `Publish to TestPyPI`,
    and `Publish to PyPI` needs both. It runs the package TestPyPI serves, so it holds `contents: read` alone: no
    environment and no `id-token`. Until now the check ran in the TestPyPI job, so the package it imported ran with
    that job's OIDC token-request variables in its environment. Its steps moved with it: the same `--no-deps` install
    from TestPyPI alone and the same import or metadata check, now run from `$RUNNER_TEMP`. `python -c` puts its
    working directory first on `sys.path`, and the repository's root holds `juniper_cascor/`, so `publish.yml`'s check,
    run in a full checkout, could import the checkout's package and pass without the wheel. The TestPyPI job drops its
    checkout and `setup-python` and holds `id-token: write` alone, so the job that can mint runs only the template steps
    and the upload. The new job's name holds "TestPyPI", so juniper-ml's release-train ceremony reads its failure as
    `HALT_TESTPYPI` with no change on its side.
  - **Each install check makes 5 tries, 10 s apart, then names the lag.** After the fifth failed install it fails with
    "… is not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats". The
    sub-package checks had the loop but fell through to an import that failed as if the package were broken, and
    `publish.yml`'s had no retry. `publish.yml`'s reads the release's tag through the step's `env`, never pasted into
    the script by an expression. The sub-packages' sparse checkout keeps no credential (`persist-credentials: false`).
    The protocol's check also finds the package with `importlib.util.find_spec`, without running it, so a wheel that
    lacks the package no longer passes on its metadata alone; it fails through `SystemExit`, which `PYTHONOPTIMIZE`
    keeps, where it would strip an `assert` statement.
  - **A sub-package publisher's plain dispatch builds only from a ref named with its own tag prefix**, as its release
    builds only from its own tag: from the app's `v` tag it would have published the sub-package's files under that
    tag's run. Its PyPI job drops `contents: read`, so every PyPI job holds `id-token: write` alone.
  - **The republish job refuses unless the tag's release run passed its TestPyPI jobs** (ruling 1).
    `Find the release run's artifact` takes the tag's newest release run, whether or not its artifact has expired, and
    refuses unless each of its jobs whose name holds "TestPyPI" concluded success in its latest attempt
    (`GET actions/runs/{id}/jobs?filter=all`, each job's record with the highest attempt). It refuses as well when the
    tag has no release run. Rung 1 of the recovery ladder could otherwise copy files whose install check had failed, or
    never ran.
  - **`PUBLISH_TAG_PREFIX`**, the template's third parameter: `v` here, `juniper-cascor-model-v` and
    `juniper-cascor-protocol-v` in the sub-package publishers. The republish job takes the version from a tag only
    after this prefix, so a sub-package publisher dispatched from a `v<version>` tag now refuses before any request,
    and `publish.yml` refuses a `juniper-cascor-v<version>` tag. Each build guard repeats its prefix, since a job-level
    `if:` cannot read `env`.
  - **Comments.** The republish job's no longer says the ceremony never reads a dispatch run: since juniper-ml#2592 its
    monitor reads them and classifies a republish run by the run's own status. The find step's says "Re-run failed
    jobs" copies each job it carries over into the new attempt (a new id, the new attempt, the earlier conclusion), as
    a live re-run shows, and its log names "the latest attempt". The PyPI job's says TestPyPI's record witnesses the
    files the run built, whose wheel the install check installed (`MANUAL.md` now says so too), and that no check
    installs the sdist. The sub-package publishers' top comment says a job's `permissions` replace the workflow's
    rather than add to them. `publish.yml`'s `v` guard notes that a future `rc*` or `hf*` tag convention must widen it.
  - **Docs.** `docs/ci_cd/MANUAL.md` ({manual}) says when rung 1 refuses; that a TestPyPI job which failed on index lag
    is re-run ("Re-run failed jobs" uploads the same bytes, which the index accepts) while a failed install check
    needs a new patch version, because the index refuses new bytes under a name it holds, and to re-run first when
    unsure, since lag passes on a re-run and a real failure repeats; never to re-cut a Release to retry, because once
    TestPyPI holds the version the re-cut's run, refused by it, becomes the tag's newest and rung 1 then refuses the
    tag; that for tags cut after this change a plain dispatch builds only from a ref whose name starts with the
    package's tag prefix; that once the artifact expires the republish takes every file TestPyPI lists; that a failed
    `Verify PyPI serves exactly these files` comes after the upload; which tags the ladder covers; and what a version
    a plain dispatch published needs. `docs/ci_cd/REFERENCE.md` § One-Artifact Contract, its permissions table and its
    install-check contract, `docs/ci_cd/QUICK_START.md`, `docs/DEVELOPER_CHEATSHEET.md` ({cheatsheet}) and `AGENTS.md`
    follow.
  - **Pins**, in `src/tests/unit/test_publish_one_artifact.py` ({cases} cases, 87 before): the new job's name, `needs`,
    permissions and lack of an environment; the PyPI job needing both TestPyPI jobs; each job's permissions, keys (a
    workflow may add `run-name` and a `concurrency` group without `cancel-in-progress`, a job `timeout-minutes`, and no job
    a `concurrency` group of its own, which by default cancels its pending job when another queues), runner and exact
    steps, actions compared by name, and each action pinned to one ref in all three files; no `continue-on-error` and
    no `if:` beyond the listed ones; no `PIP_*` variable in any `env`; each build step's command; each install step's
    exact commands, run from `$RUNNER_TEMP`; no `skip_existing` and no `attestations: false`; retention of exactly 90
    days; the release-convention gate exempt from the reuse condition by its name; workflow names ending in "to PyPI",
    which juniper-ml's monitor requires; and each prefix with its guard. A new module,
    `src/tests/unit/test_publish_docs_bounds.py`, reads the poll and retry bounds from the workflows and requires the
    docs to state them, whitespace aside, so a rewrapped paragraph passes. The rehearsals run the new find step against
    the stand-in GitHub API: no release run, a failed upload, a failed or unfinished install check, a failed build, a
    job a re-run carried over, with and without GitHub's copies, a failure a re-run repaired, a "Re-run all jobs" whose
    second attempt failed, each listing order, a listing over two pages, an older run that passed behind a newer one
    that failed, and both prefixes; the fetch step against a release run and a TestPyPI that name different files; and
    each install check's own shell against stand-in `pip`, `python` and `sleep`: five failed tries, a try that
    installs, a check that fails after the install, and a tag that holds shell text. Each of {mutations} edits to a
    copy of the workflows, one at a time, fails the tests.
"""


def bump_patch(text: str, pattern: str, where: str) -> tuple[str, str]:
    """Raise the last component of the one version PATTERN's group matches; return (new text, new version)."""
    found = list(re.finditer(pattern, text))
    if len(found) != 1:
        raise Refused(f"{where}: version pattern matched {len(found)} times, expected 1")
    match = found[0]
    old = match.group(1)
    new = ".".join(old.split(".")[:-1] + [str(int(old.split(".")[-1]) + 1)])
    return text[: match.start(1)] + new + text[match.end(1) :], new


def set_date(text: str, pattern: str, today: str, where: str) -> str:
    """Set the one date PATTERN's group matches to TODAY."""
    found = list(re.finditer(pattern, text, re.MULTILINE))
    if len(found) != 1:
        raise Refused(f"{where}: date pattern matched {len(found)} times, expected 1")
    return text[: found[0].start(1)] + today + text[found[0].end(1) :]


def docs(read, today: str, cases: str, mutations: str) -> dict[str, str]:
    out: dict[str, str] = {}
    manual, manual_version = bump_patch(read(MANUAL), r"\*\*Version\*\*: (\d+\.\d+\.\d+)  \n", MANUAL)
    for old, new in MANUAL_EDITS:
        manual = replace_once(manual, old, new, MANUAL)
    out[MANUAL] = manual
    reference = set_date(read(REFERENCE), r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", today, REFERENCE)
    for old, new in REFERENCE_EDITS:
        reference = replace_once(reference, old, new, REFERENCE)
    out[REFERENCE] = reference
    out[QUICK_START] = replace_once(read(QUICK_START), *QUICK_START_EDIT, QUICK_START)
    cheatsheet, cheatsheet_version = bump_patch(read(CHEATSHEET), r"\*\*Version\*\*: (\d+\.\d+\.\d+)  \|  \*\*Date\*\*: \d{4}-\d{2}-\d{2}  \|", CHEATSHEET)
    cheatsheet = set_date(cheatsheet, r"\*\*Version\*\*: \d+\.\d+\.\d+  \|  \*\*Date\*\*: (\d{4}-\d{2}-\d{2})  \|", today, CHEATSHEET)
    for old, new in CHEATSHEET_EDITS:
        cheatsheet = replace_once(cheatsheet, old, new, CHEATSHEET)
    out[CHEATSHEET] = cheatsheet
    agents = set_date(read(AGENTS), r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", today, AGENTS)
    out[AGENTS] = replace_once(agents, *AGENTS_EDIT, AGENTS)
    entry = CHANGELOG_ENTRY.replace("{manual}", manual_version).replace("{cheatsheet}", cheatsheet_version).replace("{cases}", cases).replace("{mutations}", mutations)
    changelog = read(CHANGELOG)
    if changelog.count("## [Unreleased]\n") != 1:
        raise Refused("CHANGELOG.md: no single '## [Unreleased]' heading")
    unreleased_end = changelog.find("\n## [", changelog.index("## [Unreleased]\n") + 1)
    if changelog.count(CHANGELOG_ANCHOR) != 1 or not 0 <= changelog.index(CHANGELOG_ANCHOR) < unreleased_end:
        raise Refused("CHANGELOG.md: the one-artifact entry's last line is not once under [Unreleased]")
    if changelog.count(CHANGELOG_767_OLD) != 1 or not 0 <= changelog.index(CHANGELOG_767_OLD) < unreleased_end:
        raise Refused("CHANGELOG.md: the one-artifact entry's witness sentence is not once under [Unreleased]")
    changelog = changelog.replace(CHANGELOG_767_OLD, CHANGELOG_767_NEW)
    out[CHANGELOG] = changelog.replace(CHANGELOG_ANCHOR, CHANGELOG_ANCHOR + entry + "\n")
    return out


def apply(tree: Path, today: str, cases: str, mutations: str) -> tuple[dict[str, str], str]:
    """Return ({repo path: new text} for every file the sweep writes, the detected word); raise Refused on any miss."""

    def read(rel: str) -> str:
        return (tree / rel).read_text(encoding="utf-8")

    out: dict[str, str] = {}
    word = detect_word(read(PUBLISH))
    out[PUBLISH] = publish_yml(read(PUBLISH))
    for rel in (MODEL, PROTOCOL):
        out[rel] = sub_package_workflow(read(rel), rel)
    check_workflows(out)
    if not TEST_EDITS or not DOCS_TEST:
        raise Refused("TEST_EDITS or DOCS_TEST is empty: splice the derived edits and the new module in first")
    out[TEST_PATH] = test_file(read(TEST_PATH))
    if (tree / DOCS_TEST_PATH).exists():
        raise Refused(f"{DOCS_TEST_PATH} exists already: this sweep creates it")
    out[DOCS_TEST_PATH] = DOCS_TEST
    for rel in (TEST_PATH, DOCS_TEST_PATH):
        try:
            ast.parse(out[rel])
        except SyntaxError as exc:
            raise Refused(f"{rel}: the file does not parse: {exc}") from exc
    out.update(docs(read, today, cases, mutations))
    # The new text avoids the person-word (the brief's wording rule): no file may name it more often than before.
    grown = {rel: delta for rel, text in out.items() if (delta := sum(text.count(w) for w in WORDS) - sum((read(rel) if (tree / rel).exists() else "").count(w) for w in WORDS))}
    if grown:
        raise Refused(f"the new text names the person-word: {grown}")
    return out, word


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path, help="a fresh copy of juniper-cascor's tree (edited in place)")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat(), help="the day the docs' dates take (default: today, UTC)")
    # The measured values (2026-11-23, review round 2): test_publish_one_artifact.py's cases, and the mutation proof's
    # edits, every one caught (round 1's 34 and group R's 11).
    parser.add_argument("--changelog-cases", default="159", help="the case count the CHANGELOG entry states (default: 159)")
    parser.add_argument("--changelog-mutations", default="45", help="the mutation count the CHANGELOG entry states (default: 45)")
    args = parser.parse_args(argv)
    try:
        out, word = apply(args.tree, args.date, args.changelog_cases, args.changelog_mutations)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    print(f"the base's person-word: {word!r}")
    for rel, text in sorted(out.items()):
        target = args.tree / rel
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        if text == before:
            print(f"unchanged {rel}")
            continue
        target.write_text(text, encoding="utf-8")
        print(f"wrote {rel} ({sha256(before)[:12] if before else 'new'} -> {sha256(text)[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
