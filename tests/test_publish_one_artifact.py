#!/usr/bin/env python3
"""Pin the one-artifact publish: PyPI takes exactly the files TestPyPI took, and the run checks it by sha256.

The owner's directive of 2026-11-15: "deploy to pypi should send the same artifact that was already sent to testpypi.
an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to
prevent this from slipping through the cracks again." juniper-ml's seven publishers handed both publish jobs one
artifact, but nothing checked it, and a re-run broke it. juniper-ci-tools 0.9.1's run 38045867684: attempt 1's
``Publish to PyPI``, approved on day 11, failed at its download because the 7-day artifact had expired; attempt 2 ("Re-run
all jobs") built again, its TestPyPI upload passed under ``skip-existing`` while TestPyPI kept the first build, and PyPI
took the second. PyPI serves the wheel as ``1dc8e01e...``, TestPyPI as ``ade363e8...``.

Every publisher now carries juniper-cascor's one-artifact template (juniper-cascor#763 and #767), copied verbatim. The
build job records ``SHA256SUMS`` and uploads it with the dist directory as one artifact, kept 90 days, and a re-run
attempt reuses that artifact instead of building again. Each publish job checks the files against ``SHA256SUMS`` before
it uploads them. TestPyPI's JSON must list exactly those sha256 after the TestPyPI upload and again before the PyPI one,
and PyPI's after it. No upload sets ``skip-existing``, and only the jobs that upload hold ``id-token: write``. A
dispatch from the release tag with ``republish_from_testpypi`` runs the republish job, the first rung of the owner's
recovery ladder (2026-11-15): it copies TestPyPI's files for the version to PyPI and builds nothing.

The static cases pin that wiring in all seven workflows, what each workflow kept (``TestUnchanged``), and every copy of
a template step byte-identical to the others and to juniper-cascor's template. The rehearsals run each template step's
own Python, extracted from ``publish.yml``, in a scratch workspace, against a stand-in index and a stand-in GitHub API on
127.0.0.1. The negative control is ``util/ad-hoc/2026-11-15_verify_publish_one_artifact_tests_are_not_vacuous.py``.

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
#: workflow -> (PUBLISH_PACKAGE, PUBLISH_DIST_DIR, TestPyPI job, PyPI job); each also has a ``build`` and a ``republish`` job.
PUBLISHERS = {
    "publish.yml": ("juniper-ml", "dist", "testpypi", "pypi"),
    "publish-ci-tools.yml": ("juniper-ci-tools", "juniper-ci-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-config-tools.yml": ("juniper-config-tools", "juniper-config-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-doc-tools.yml": ("juniper-doc-tools", "juniper-doc-tools/dist", "publish-testpypi", "publish-pypi"),
    "publish-model-core.yml": ("juniper-model-core", "juniper-model-core/dist", "publish-testpypi", "publish-pypi"),
    "publish-observability.yml": ("juniper-observability", "juniper-observability/dist", "publish-testpypi", "publish-pypi"),
    "publish-service-core.yml": ("juniper-service-core", "juniper-service-core/dist", "publish-testpypi", "publish-pypi"),
}
SUB_PACKAGES = tuple(name for name in sorted(PUBLISHERS) if name != "publish.yml")
#: workflow -> (top-level permissions, the PyPI job's). No PyPI job checks anything out, so none holds ``contents: read``.
PERMISSIONS = {
    "publish.yml": ({}, {"id-token": "write"}),
    **{name: ({"contents": "read"}, {"id-token": "write"}) for name in SUB_PACKAGES},
}
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
#: sha256 of each template step's Python as juniper-cascor's ``publish.yml`` runs it at 675884888f5a (juniper-cascor#767's
#: merge), where the template lives. The copies here must be byte-identical to it, not merely to one another: a fix to the
#: template is made there and copied here, never made here alone.
TEMPLATE_SHA256 = {
    REUSE: "c744f3a279f2f16720404f5062bcc7bb8cbf4c8af0e76d63fc41416e3457e183",
    RECORD: "06d8816015be9b0935af13726272fe06923cdcec612a3b62547ea5ff9935fb1c",
    VERIFY_DIST: "152b836d0289b96fe6a2b2dcaedd3bd2dff387de3ab1678af7078f53e495f613",
    "index": "af011b56c175160a3234b4daf84e8bd42350c1522a3d5d4951308bebe023d43a",
    FIND: "ac1b2dcdc26325c3f4ab4f9579af53de37e7a541741d9d59c6625622da3162b4",
    FETCH: "82da3aa6708fb88197665a4c7da066c62b1202c812ae6454442a49e1739e30e0",
}
#: Everything a template step may read from its environment: the two parameters, a step's own inputs, the runner's variables.
TEMPLATE_ENV = {
    "PUBLISH_PACKAGE",
    "PUBLISH_DIST_DIR",
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
ARTIFACT = "${{ env.PUBLISH_PACKAGE }}-dist"
DIST_INPUT = "${{ env.PUBLISH_DIST_DIR }}/"
META_GUARD = "(github.event_name == 'release' && startsWith(github.event.release.tag_name, 'v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)"
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


@functools.lru_cache(maxsize=None)
def _workflow(name: str) -> dict:
    """The parsed workflow, read once per process. Every case only reads it."""
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) reads the bare `on:` key as boolean True.
    data["on"] = data.pop(True, data.get("on"))
    return data


def _names(job: dict) -> list[str]:
    return [str(s.get("name") or s.get("uses") or "") for s in job.get("steps") or []]


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


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script(kind: str, tmp_path: Path) -> Path:
    path = tmp_path / f"{re.sub(r'[^a-z]+', '_', kind.lower())}.py"
    path.write_text(_template_scripts()[kind], encoding="utf-8")
    return path


def _run(script: Path, workspace: Path, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run an extracted step as the runner does (``python3 {0}``), with a minimal environment rather than a copy of ours."""
    child = {"PATH": os.environ.get("PATH", ""), "GITHUB_WORKSPACE": str(workspace), "PUBLISH_PACKAGE": "juniper-ml", "PUBLISH_DIST_DIR": "dist"}
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
    def test_the_template_parameters_name_this_package(self) -> None:
        for workflow, (package, dist_dir, _, _) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                self.assertEqual(_workflow(workflow)["env"], {"PUBLISH_PACKAGE": package, "PUBLISH_DIST_DIR": dist_dir})

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
                self.assertEqual(sorted(jobs), sorted(["build", test_id, prod_id, REPUBLISH]))
                self.assertEqual(jobs[test_id]["needs"], "build")
                self.assertEqual(jobs[prod_id]["needs"], test_id)
                # util/release_train/ceremony.py tells the two jobs apart by name ("testpypi" / "pypi").
                self.assertEqual(jobs[test_id]["name"], "Publish to TestPyPI")
                self.assertEqual(jobs[prod_id]["name"], "Publish to PyPI")
                self.assertEqual(_environment(jobs[test_id]), "testpypi")
                self.assertEqual(_environment(jobs[prod_id]), "pypi")

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
                self.assertEqual(jobs[test_id]["permissions"], {"contents": "read", "id-token": "write"})
                self.assertEqual(jobs[prod_id]["permissions"], prod)
                self.assertEqual(jobs[REPUBLISH]["permissions"], {"actions": "read", "id-token": "write"})
                # A job that holds no contents: read must not check anything out.
                self.assertEqual(_uses(jobs[prod_id], "actions/checkout@"), [])

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
                # step gated on a push event (tests/test_publish_release_only_trigger.py), so there is no exception.
                for step in build["steps"][1:]:
                    self.assertEqual(step.get("if"), REUSE_IF, f"{step.get('name') or step.get('uses')} would run on a re-run that reuses the artifact")
                for name in (RECORD, UPLOAD):
                    self.assertEqual(_step(build, name).get("if"), REUSE_IF)

    def test_the_testpypi_job_checks_the_dist_uploads_then_checks_testpypi_before_the_install_check(self) -> None:
        for workflow, (_, _, test_id, _) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                job = _workflow(workflow)["jobs"][test_id]
                uploads = _uploads(job)
                self.assertEqual(len(uploads), 1)
                self.assertEqual(job["steps"][uploads[0]]["with"]["repository-url"], "https://test.pypi.org/legacy/")
                self.assertLess(_index(job, DOWNLOAD), _index(job, VERIFY_DIST))
                self.assertLess(_index(job, VERIFY_DIST), uploads[0])
                self.assertLess(uploads[0], _index(job, TESTPYPI_AFTER))
                installs = [i for i, s in enumerate(job["steps"]) if "pip install" in str(s.get("run") or "")]
                self.assertTrue(installs, "the TestPyPI install check is gone")
                self.assertGreater(min(installs), _index(job, TESTPYPI_AFTER), "the install check must come after the sha256 check that vouches for what it installs")
                # A checkout empties the workspace, so one between the download and the last template step would lose the files.
                between = _uses({"steps": job["steps"][_index(job, DOWNLOAD) : _index(job, TESTPYPI_AFTER)]}, "actions/checkout@")
                self.assertEqual(between, [], "a checkout runs between the download and the TestPyPI check")

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
                self.assertEqual(_step(job, FETCH_ORIGINAL)["if"], "steps.original.outputs.run-id != ''")
                self.assertEqual(_step(job, FETCH_ORIGINAL)["with"], {"name": ARTIFACT, "run-id": "${{ steps.original.outputs.run-id }}", "github-token": RUNNER_CREDENTIAL, "path": "${{ runner.temp }}/release-run"})
                self.assertEqual(_step(job, FETCH)["env"], {"INDEX_URL": "https://test.pypi.org", "VERSION": "${{ steps.original.outputs.version }}", "RELEASE_RUN_SUMS": "${{ runner.temp }}/release-run/SHA256SUMS"})
                self.assertEqual(_step(job, PYPI_AFTER)["env"], {"INDEX_URL": "https://pypi.org"})

    def test_every_upload_takes_the_downloaded_dist_and_none_skips_an_existing_file(self) -> None:
        for workflow in sorted(PUBLISHERS):
            with self.subTest(workflow=workflow):
                for job in _workflow(workflow)["jobs"].values():
                    for i in _uploads(job):
                        inputs = job["steps"][i].get("with") or {}
                        self.assertEqual(inputs.get("packages-dir"), DIST_INPUT)
                        # skip-existing would keep an earlier file under the same name, and the install check would test it.
                        self.assertNotIn("skip-existing", inputs)
                        self.assertNotIn("skip_existing", inputs)

    def test_one_artifact_carries_the_dist_and_sha256sums_and_outlives_the_pypi_gate(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                upload = _step(jobs["build"], UPLOAD)["with"]
                self.assertEqual(upload["name"], ARTIFACT)
                self.assertEqual([p.strip() for p in upload["path"].splitlines() if p.strip()], [DIST_INPUT, "SHA256SUMS"])
                self.assertEqual(upload["if-no-files-found"], "error")
                self.assertGreater(int(upload["retention-days"]), GATE_APPROVAL_DAYS)
                self.assertLess(_index(jobs["build"], RECORD), _index(jobs["build"], UPLOAD))
                for job_id in (test_id, prod_id):
                    self.assertEqual(_step(jobs[job_id], DOWNLOAD)["with"], {"name": ARTIFACT, "path": "${{ github.workspace }}"})

    def test_each_json_check_reads_its_own_index_and_keeps_the_default_bounds(self) -> None:
        for workflow, (_, _, test_id, prod_id) in sorted(PUBLISHERS.items()):
            with self.subTest(workflow=workflow):
                jobs = _workflow(workflow)["jobs"]
                for job_id, name in ((test_id, TESTPYPI_AFTER), (prod_id, TESTPYPI_BEFORE), (prod_id, PYPI_AFTER)):
                    self.assertEqual(_step(jobs[job_id], name)["env"], {"INDEX_URL": INDEX_CHECKS[name]})


class TestUnchanged(unittest.TestCase):
    """What each publisher kept. The permissions changed: TestWiring pins them per job."""

    def test_publish_yml_builds_on_its_release_or_a_plain_dispatch_and_keeps_its_tag_guard(self) -> None:
        wf = _workflow("publish.yml")
        self.assertEqual(set(wf["on"]), {"release", "workflow_dispatch"})
        self.assertEqual(wf["on"]["release"], {"types": ["published"]})
        self.assertNotIn("concurrency", wf)
        # A plain dispatch still re-fires the whole publish (it builds); the republish dispatch runs the republish job alone.
        self.assertEqual(wf["jobs"]["build"]["if"], META_GUARD)
        self.assertNotIn("if", wf["jobs"]["testpypi"])
        self.assertNotIn("if", wf["jobs"]["pypi"])

    def test_publish_yml_builds_with_the_commands_it_used_before_and_asserts_the_tag(self) -> None:
        build = _workflow("publish.yml")["jobs"]["build"]
        runs = [str(s.get("run") or "").strip() for s in build["steps"]]
        self.assertLess(runs.index("pip install build twine"), runs.index("python -m build"))
        self.assertLess(runs.index("python -m build"), runs.index("twine check dist/*"))
        assert_tag = _step(build, "Assert release tag matches built version")["run"]
        for token in ("util/assert_release_tag.bash", '--ref "${{ github.ref }}"', "--dist-dir dist", "--expect-prefix v"):
            self.assertIn(token, assert_tag)
        self.assertLess(runs.index("twine check dist/*"), _index(build, "Assert release tag matches built version"))
        self.assertLess(_index(build, "Assert release tag matches built version"), _index(build, RECORD))

    def test_publish_yml_keeps_its_checkout_before_the_download_and_its_two_phase_install_check(self) -> None:
        job = _workflow("publish.yml")["jobs"]["testpypi"]
        checkout = _uses(job, "actions/checkout@")
        setup = _uses(job, "actions/setup-python@")
        self.assertEqual(len(checkout), 1)
        self.assertEqual(len(setup), 1)
        # The install check reads the version from pyproject.toml, so the job keeps its checkout, which must run before
        # the download: a checkout empties the workspace.
        self.assertLess(checkout[0], _index(job, DOWNLOAD))
        self.assertLess(setup[0], _index(job, DOWNLOAD))
        self.assertEqual(job["steps"][setup[0]]["with"], {"python-version": "3.12"})
        verify = _step(job, "Verify TestPyPI install")["run"]
        self.assertGreater(_index(job, "Verify TestPyPI install"), _index(job, TESTPYPI_AFTER))
        self.assertIn("tomllib.load(open('pyproject.toml','rb'))['project']['version']", verify)
        self.assertIn('pip download --no-deps --index-url https://test.pypi.org/simple/ --dest "${DOWNLOAD_DIR}" "juniper-ml==${VERSION}"', verify)

    def test_publish_yml_keeps_attestations_on_both_uploads_and_its_pypi_job_sets_up_nothing(self) -> None:
        jobs = _workflow("publish.yml")["jobs"]
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
                # A plain dispatch still re-fires the whole publish; the republish dispatch runs the republish job alone.
                self.assertEqual(wf["jobs"]["build"]["if"], f"(github.event_name == 'release' && startsWith(github.event.release.tag_name, '{package}-v')) || (github.event_name == 'workflow_dispatch' && !inputs.republish_from_testpypi)")
                self.assertEqual(wf["jobs"]["build"]["defaults"], {"run": {"working-directory": package}})

    def test_the_sub_package_publishers_build_with_the_commands_they_used_before_and_assert_the_tag(self) -> None:
        for workflow in SUB_PACKAGES:
            with self.subTest(workflow=workflow):
                package = PUBLISHERS[workflow][0]
                build = _workflow(workflow)["jobs"]["build"]
                runs = [str(s.get("run") or "").strip() for s in build["steps"]]
                self.assertLess(runs.index("pip install --upgrade build twine"), runs.index("python -m build --sdist --wheel"))
                self.assertLess(runs.index("python -m build --sdist --wheel"), runs.index("twine check dist/*"))
                assert_tag = _step(build, "Assert release tag matches built version")["run"]
                for token in ("../util/assert_release_tag.bash", '--ref "${{ github.ref }}"', "--dist-dir dist", f"--expect-prefix {package}-v"):
                    self.assertIn(token, assert_tag)
                self.assertLess(_index(build, "Assert release tag matches built version"), _index(build, RECORD))

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
                # The sparse checkout the install check reads its version from comes after the JSON check: a checkout
                # empties the workspace, and the template steps are done with it by then.
                checkout = _uses(test_job, "actions/checkout@")
                installs = [i for i, s in enumerate(test_job["steps"]) if str(s.get("name") or "").startswith("Verify install from TestPyPI")]
                self.assertEqual(len(checkout), 1)
                self.assertEqual(len(installs), 1)
                self.assertLess(_index(test_job, TESTPYPI_AFTER), checkout[0])
                self.assertLess(checkout[0], installs[0])
                self.assertIn(f"{package}/", test_job["steps"][checkout[0]]["with"]["sparse-checkout"])
                install = test_job["steps"][installs[0]]["run"]
                for token in ("--no-deps", "--index-url https://test.pypi.org/simple/", f'"{package}==${{version}}"'):
                    self.assertIn(token, install)


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
        self.assertEqual({kind: _sha(run.encode("utf-8")) for kind, run in _template_scripts().items()}, TEMPLATE_SHA256)

    def test_the_republish_job_is_byte_identical_in_every_publisher(self) -> None:
        jobs = [_workflow(workflow)["jobs"][REPUBLISH] for workflow in sorted(PUBLISHERS)]
        for job in jobs[1:]:
            self.assertEqual(job, jobs[0])

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


def _runs_path(tag: str, workflow: str = "publish.yml") -> str:
    return f"/repos/{REPOSITORY}/actions/workflows/{workflow}/runs?event=release&branch={tag}&per_page=30"


def _artifacts_path(run_id: int, package: str = "juniper-ml") -> str:
    return f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?name={package}-dist&per_page=100"


class TestFindReleaseRun(_Scratch):
    @staticmethod
    def _env(case_dir: Path, server: _Stand, tag: str = "v9.9.9", ref_type: str = "tag", workflow: str = "publish.yml") -> dict[str, str]:
        return _github_env(case_dir, server, GITHUB_REF_NAME=tag, GITHUB_REF_TYPE=ref_type, GITHUB_REF=f"refs/{'tags' if ref_type == 'tag' else 'heads'}/{tag}", GITHUB_WORKFLOW_REF=f"{REPOSITORY}/.github/workflows/{workflow}@refs/tags/{tag}")

    def test_the_newest_release_run_that_still_holds_the_artifact_is_found(self) -> None:
        workspace = self.workspace()
        server = self.stand(
            {
                _runs_path("v9.9.9"): [(200, {"workflow_runs": [{"id": 111, "head_branch": "v9.9.9"}, {"id": 333, "head_branch": "v9.9.9"}, {"id": 222, "head_branch": "v9.9.9"}]})],
                _artifacts_path(333): [(200, {"artifacts": [{"id": 1, "name": "juniper-ml-dist", "expired": True}]})],
                _artifacts_path(222): [(200, {"artifacts": [{"id": 2, "name": "juniper-ml-dist", "expired": False}]})],
                _artifacts_path(111): [(200, {"artifacts": [{"id": 3, "name": "juniper-ml-dist", "expired": False}]})],
            }
        )
        proc = _run(_script(FIND, self.tmp_path), workspace, env=self._env(self.tmp_path, server))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path), {"version": "9.9.9", "run-id": "222"})
        self.assertNotIn(_artifacts_path(111), server.paths())

    def test_a_sub_package_tag_names_its_version(self) -> None:
        workspace = self.workspace()
        tag = "juniper-ci-tools-v1.2.3"
        server = self.stand({_runs_path(tag, "publish-ci-tools.yml"): [(200, {"workflow_runs": []})]})
        proc = _run(_script(FIND, self.tmp_path), workspace, env={"PUBLISH_PACKAGE": "juniper-ci-tools", **self._env(self.tmp_path, server, tag=tag, workflow="publish-ci-tools.yml")})
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(_outputs(self.tmp_path), {"version": "1.2.3", "run-id": ""})
        self.assertIn("::warning::", proc.stdout)

    def test_it_refuses_anything_but_a_release_tag_of_this_package(self) -> None:
        workspace = self.workspace()
        cases = {"branch-named-like-a-tag": ("v9.9.9", "branch"), "branch": ("main", "branch"), "another-packages-tag": ("juniper-ci-tools-v1.2.3", "tag")}
        for case, (tag, ref_type) in cases.items():
            with self.subTest(case=case):
                case_dir = self.tmp_path / case
                server = self.stand({})
                proc = _run(_script(FIND, self.tmp_path), workspace, env=self._env(case_dir, server, tag=tag, ref_type=ref_type))
                self.assertEqual(proc.returncode, 1)
                self.assertIn("::error::", proc.stdout)
                self.assertEqual(server.requests, [])
                self.assertEqual(_outputs(case_dir), {})

    def test_an_api_failure_fails_the_job_rather_than_skip_the_check(self) -> None:
        workspace = self.workspace()
        server = self.stand({_runs_path("v9.9.9"): [(502, {"message": "bad gateway"})]})
        proc = _run(_script(FIND, self.tmp_path), workspace, env=self._env(self.tmp_path, server))
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(_outputs(self.tmp_path), {})


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
