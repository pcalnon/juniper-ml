#!/usr/bin/env python3
"""Tests for util/push_signed_commit.py (one GitHub-signed commit onto an EXISTING branch).

The existing-branch sibling of util/open_signed_pr.py, promoted 2026-09-22 so the ad-hoc
copies under util/ad-hoc/ stop multiplying. ``util/`` is outside every pre-commit Python
hook's scope (flake8/black/mypy/bandit scope to ``scripts/`` + ``tests/``), so this suite
IS the gate.

Hermetic: ``gh`` is a PATH stub -- a small Python script that records its argv, replays a
canned GitHub state from a JSON config, and ENFORCES ``expectedHeadOid`` the way GitHub
does: a mutation whose pin is not the stub's current head is rejected as stale. That is
what lets these tests tell "sends the pinned sha" apart from "sends whatever the branch
reads right now". An unexpected ``gh`` call exits 99, so a call the tool starts making
fails a test instead of passing silently. No network, no real repo, no ``git``.

Contract pinned here:

- ``--expected-head`` is REQUIRED and must be the FULL 40-hex sha; an abbreviation is
  refused with exit 2 BEFORE any ``gh`` call.
- The commit goes through ``open_signed_pr.create_signed_commit`` -- this tool carries no
  mutation of its own -- and ``expectedHeadOid`` is the PINNED sha.
- Refusals exit 1 and write nothing: a missing branch (a 404, and only a 404), the default
  branch, and a branch whose head is not the pinned sha. A ref read that fails any other
  way is a hard error (exit 2), never "the branch does not exist".
- A push that lands between the pre-flight read and the commit is refused by the pin;
  the tool reports it (exit 2) and claims no commit.
- ``--dry-run`` performs only the read-only resolution: no mutation, no write verb.
- The read-back catches a head that did not move, an unverified commit, a commit not
  parented on the pin, content that differs from what was sent, and a deletion that did
  not happen -- each exit 2.

Run: python3 -m unittest -v tests/test_push_signed_commit.py

Project: juniper-ml
Author: Paul Calnon
Created: 2026-09-22
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import stat
import subprocess  # nosec B404 - drives the util's CLI with a PATH-stubbed `gh`
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

PINNED = "a" * 40
NEW_OID = "b" * 40
MOVED = "c" * 40
PAYLOAD = b"print('fixed')\n"
BRANCH = "fix/demo"
TARGET = "src/demo.py"


def _find_repo_root(start: Path) -> Path:
    for parent in [start, *start.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root (no .github/workflows/) above {start}")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent)
_MODULE_PATH = _REPO_ROOT / "util" / "push_signed_commit.py"


def _load():
    spec = importlib.util.spec_from_file_location("push_signed_commit", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The stub is written verbatim to <tmp>/bin/gh. It reads its settings from the JSON file named by
# PSC_GH_STUB_CONFIG, keeps the branch head in <dir>/head so a commit can MOVE it, and copies each
# mutation body to <dir>/mutation.json so a test can assert on the exact payload.
_GH_STUB = r'''#!/usr/bin/env python3
"""PATH stub for `gh` used by tests/test_push_signed_commit.py."""
import base64
import hashlib
import json
import os
import shutil
import sys
from urllib.parse import unquote

with open(os.environ["PSC_GH_STUB_CONFIG"], encoding="utf-8") as fh:
    cfg = json.load(fh)
state = cfg["dir"]
argv = sys.argv[1:]
with open(os.path.join(state, "gh.log"), "a", encoding="utf-8") as fh:
    fh.write(" ".join(argv) + "\n")
slug = cfg["owner"] + "/" + cfg["repo"]


def read_head():
    with open(os.path.join(state, "head"), encoding="utf-8") as fh:
        return fh.read().strip()


def write_head(sha):
    with open(os.path.join(state, "head"), "w", encoding="utf-8") as fh:
        fh.write(sha)


def bump(counter):
    path = os.path.join(state, counter)
    count = 1
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            count = int(fh.read()) + 1
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(str(count))
    return count


def not_found():
    sys.stdout.write('{"message":"Not Found","status":"404"}')
    sys.stderr.write("gh: Not Found (HTTP 404)\n")
    raise SystemExit(1)


if argv[:2] == ["api", "graphql"]:
    source = argv[argv.index("--input") + 1]
    shutil.copyfile(source, os.path.join(state, "mutation.json"))
    with open(source, encoding="utf-8") as fh:
        pin = json.load(fh)["variables"]["input"]["expectedHeadOid"]
    if pin != read_head():
        message = 'Expected branch to point to "%s" but it did not. Pull and try again.' % pin
        sys.stdout.write(json.dumps({"errors": [{"type": "STALE_DATA", "message": message}]}))
        sys.stderr.write("gh: " + message + "\n")
        raise SystemExit(1)
    if cfg["move_head"]:
        write_head(cfg["new_oid"])
    sys.stdout.write(json.dumps({"data": {"createCommitOnBranch": {"commit": {"oid": cfg["new_oid"], "url": "u"}}}}))
    raise SystemExit(0)

path = argv[1] if len(argv) > 1 and argv[0] == "api" else ""
if path == "repos/" + slug:
    print(cfg["default_branch"])
    raise SystemExit(0)

if path.startswith("repos/" + slug + "/git/ref/heads/"):
    if cfg["ref_error"]:
        sys.stderr.write("gh: " + cfg["ref_error"] + "\n")
        raise SystemExit(1)
    if not cfg["branch_exists"]:
        not_found()
    print(read_head())
    # A concurrent push landing right after the Nth read of the branch.
    if bump("ref_reads") == cfg["race_after_ref_reads"]:
        write_head(cfg["race_head"])
    raise SystemExit(0)

if path.startswith("repos/" + slug + "/git/commits/"):
    print(json.dumps({"verified": cfg["verified"], "reason": "valid" if cfg["verified"] else "unsigned", "parents": cfg["parents"]}))
    raise SystemExit(0)

prefix = "repos/" + slug + "/contents/"
if path.startswith(prefix):
    repo_path = unquote(path[len(prefix):].partition("?")[0])
    with open(os.path.join(state, "mutation.json"), encoding="utf-8") as fh:
        changes = json.load(fh)["variables"]["input"]["fileChanges"]
    stored = {a["path"]: base64.b64decode(a["contents"]) for a in changes.get("additions", [])}
    if repo_path in cfg["blob_overrides"]:
        print(cfg["blob_overrides"][repo_path])
    elif repo_path in stored:
        raw = stored[repo_path]
        print(hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest())
    elif repo_path in cfg["still_present"]:
        print("f" * 40)
    else:
        not_found()
    raise SystemExit(0)

sys.stderr.write("gh stub: unhandled call: " + " ".join(argv) + "\n")
raise SystemExit(99)
'''


class _Harness:
    """A tempdir with the stub `gh` on PATH, its JSON settings, and the file the tool uploads."""

    def __init__(self, tmp: Path, **settings) -> None:
        self.tmp = tmp
        self.state = tmp / "stub"
        self.state.mkdir()
        (self.state / "head").write_text(settings.pop("head", PINNED), encoding="utf-8")
        (self.state / "gh.log").write_text("", encoding="utf-8")
        config = {
            "dir": str(self.state),
            "owner": "pcalnon",
            "repo": "juniper-cascor",
            "default_branch": "main",
            "branch_exists": True,
            "ref_error": "",
            "move_head": True,
            "new_oid": NEW_OID,
            "verified": True,
            "parents": [PINNED],
            "race_after_ref_reads": 0,
            "race_head": MOVED,
            "blob_overrides": {},
            "still_present": [],
        }
        # A misspelt setting would leave the stub at its default and let a test pass vacuously.
        unknown = sorted(set(settings) - set(config))
        if unknown:
            raise KeyError(f"unknown stub setting(s): {unknown}")
        config.update(settings)
        self.config = tmp / "gh_stub.json"
        self.config.write_text(json.dumps(config), encoding="utf-8")

        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(_GH_STUB, encoding="utf-8")
        gh.chmod(gh.stat().st_mode | stat.S_IXUSR)
        self.bin_dir = bin_dir

        self.payload = tmp / "payload.py"
        self.payload.write_bytes(PAYLOAD)

    def env(self):
        env = RedactedEnv(os.environ)
        env["PATH"] = str(self.bin_dir) + os.pathsep + env.get("PATH", "")
        env["PSC_GH_STUB_CONFIG"] = str(self.config)
        return env

    def add(self) -> list:
        return ["--add", f"{self.payload}:{TARGET}"]

    def calls(self) -> list:
        return [line for line in (self.state / "gh.log").read_text(encoding="utf-8").splitlines() if line.strip()]

    def mutation(self) -> dict:
        path = self.state / "mutation.json"
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def head(self) -> str:
        return (self.state / "head").read_text(encoding="utf-8").strip()


def _run(harness: _Harness, extra: list, *, expected_head: str = PINNED, branch: str = BRANCH) -> tuple:
    argv = [
        sys.executable,
        str(_MODULE_PATH),
        "--repo",
        "juniper-cascor",
        "--branch",
        branch,
        "--expected-head",
        expected_head,
        "--message",
        "fix: demo",
        *extra,
    ]
    proc = subprocess.run(  # nosec B603 - fixed argv, stubbed PATH
        argv,
        capture_output=True,
        text=True,
        env=harness.env(),
        check=False,
        timeout=60,
    )
    return proc.returncode, proc.stdout + proc.stderr


class PushSignedCommitModuleTest(unittest.TestCase):
    """Unit-level checks that need no subprocess."""

    def test_full_sha_accepts_only_a_full_40_hex_sha(self) -> None:
        mod = _load()
        self.assertEqual(mod.full_sha(PINNED), PINNED)
        self.assertEqual(mod.full_sha("A" * 40), "a" * 40, "GitHub reports lower-case; an upper-case pin must still match")
        for bad in (PINNED[:7], PINNED[:12], PINNED[:39], PINNED + "a", "g" * 40, ""):
            with self.subTest(bad=bad), self.assertRaises(argparse.ArgumentTypeError):
                mod.full_sha(bad)

    def test_git_blob_sha_matches_git_hash_object(self) -> None:
        """The read-back compares blob shas, so this must be git's exact object hash."""
        mod = _load()
        self.assertEqual(mod.git_blob_sha(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self.assertEqual(mod.git_blob_sha(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_the_mutation_is_the_shared_helper_not_a_copy(self) -> None:
        """Ad-hoc drivers multiplied by each carrying a copy of the mutation; this one must not."""
        source = _MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("CreateCommitOnBranchInput", source)
        self.assertNotIn("createCommitOnBranch(input", source)
        self.assertIn("osp.create_signed_commit(", source)


class PushSignedCommitCliTest(unittest.TestCase):
    def test_happy_path_pins_expected_head_oid_and_reads_back_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 0, out)
            self.assertIn(f"signed commit {NEW_OID}", out)

            payload = h.mutation()["variables"]["input"]
            self.assertEqual(payload["expectedHeadOid"], PINNED)
            self.assertEqual(payload["branch"]["branchName"], BRANCH)
            self.assertEqual(payload["branch"]["repositoryNameWithOwner"], "pcalnon/juniper-cascor")
            adds = payload["fileChanges"]["additions"]
            self.assertEqual([a["path"] for a in adds], [TARGET])
            self.assertEqual(base64.b64decode(adds[0]["contents"]), PAYLOAD)
            self.assertNotIn("deletions", payload["fileChanges"], "empty deletions must be omitted, not sent as []")

            for line in ("verified head", "verified signature", "verified parent", f"verified {TARGET}"):
                self.assertIn(line, out)
            self.assertEqual(h.head(), NEW_OID)

    def test_pinned_head_mismatch_is_refused_and_writes_nothing(self) -> None:
        for mode in ([], ["--dry-run"]):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                h = _Harness(Path(td), head=MOVED)
                rc, out = _run(h, [*h.add(), *mode])
                self.assertEqual(rc, 1, out)
                self.assertIn("REFUSED", out)
                self.assertIn(MOVED, out)
                self.assertIn(PINNED, out)
                self.assertNotIn("graphql", " ".join(h.calls()), "a moved head must be refused before the mutation")
                self.assertEqual(h.head(), MOVED)

    def test_push_racing_the_commit_is_refused_by_the_pin(self) -> None:
        """A push after the pre-flight read: the pin, not a fresh read, is what refuses it.

        A tool that re-read the head just before committing would pass this push's head as
        expectedHeadOid, GitHub would accept it, and the whole-file upload would silently
        revert the push. That is the failure the pin exists to prevent.
        """
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), race_after_ref_reads=1)
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn("Expected branch to point to", out)
            self.assertNotIn("signed commit", out)
            self.assertEqual(h.mutation()["variables"]["input"]["expectedHeadOid"], PINNED)
            self.assertEqual(h.head(), MOVED, "the concurrent push must survive")
            joined = " ".join(h.calls())
            self.assertNotIn("git/commits/", joined, "no read-back of a commit that did not land")
            self.assertNotIn("contents/", joined)

    def test_missing_branch_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), branch_exists=False)
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 1, out)
            self.assertIn("does not exist", out)
            self.assertIn("open_signed_pr.py", out)
            joined = " ".join(h.calls())
            self.assertNotIn("graphql", joined)
            self.assertNotIn("git/refs", joined, "this tool must never create a branch")

    def test_ref_read_outage_is_a_hard_error_not_a_missing_branch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), ref_error="HTTP 502: Bad Gateway")
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn("502", out)
            self.assertNotIn("does not exist", out)
            self.assertNotIn("graphql", " ".join(h.calls()))

    def test_default_branch_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, h.add(), branch="main")
            self.assertEqual(rc, 1, out)
            self.assertIn("default branch", out)
            self.assertNotIn("graphql", " ".join(h.calls()))

    def test_short_sha_is_refused_before_any_api_call(self) -> None:
        for short in (PINNED[:7], PINNED[:12], PINNED[:39]):
            with self.subTest(short=short), tempfile.TemporaryDirectory() as td:
                h = _Harness(Path(td))
                rc, out = _run(h, h.add(), expected_head=short)
                self.assertEqual(rc, 2, out)
                self.assertIn("FULL 40-character sha", out)
                self.assertEqual(h.calls(), [], "an abbreviation must be refused before any gh call")

    def test_dry_run_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, [*h.add(), "--dry-run"])
            self.assertEqual(rc, 0, out)
            self.assertIn("DRY-RUN", out)
            self.assertIn("nothing written", out)
            calls = h.calls()
            joined = " ".join(calls)
            self.assertNotIn("graphql", joined, "dry-run must not create a commit")
            self.assertNotIn("git/refs", joined, "dry-run must not create a branch")
            for call in calls:
                self.assertNotIn("-X", call.split(), f"dry-run issued a non-default HTTP method: {call}")
            self.assertTrue(any(f"git/ref/heads/{BRANCH}" in c for c in calls), "dry-run must still resolve the branch head")
            self.assertEqual(h.head(), PINNED)

    def test_read_back_detects_a_head_that_did_not_move(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), move_head=False)
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn("VERIFY FAIL", out)
            self.assertIn(f"not the new commit {NEW_OID}", out)

    def test_read_back_detects_an_unverified_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), verified=False)
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn("NOT verified", out)

    def test_read_back_detects_a_commit_not_parented_on_the_pin(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), parents=[MOVED])
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn("parents", out)

    def test_read_back_detects_content_that_differs_from_what_was_sent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), blob_overrides={TARGET: "0" * 40})
            rc, out = _run(h, h.add())
            self.assertEqual(rc, 2, out)
            self.assertIn(TARGET, out)
            self.assertIn("hash to", out)

    def test_read_back_detects_a_deletion_that_did_not_happen(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td), still_present=["util/gone.py"])
            rc, out = _run(h, ["--delete", "util/gone.py"])
            self.assertEqual(rc, 2, out)
            self.assertIn("still present", out)

    def test_delete_is_carried_into_the_same_commit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            rc, out = _run(h, [*h.add(), "--delete", "util/old.py"])
            self.assertEqual(rc, 0, out)
            changes = h.mutation()["variables"]["input"]["fileChanges"]
            self.assertEqual([a["path"] for a in changes["additions"]], [TARGET])
            self.assertEqual([d["path"] for d in changes["deletions"]], ["util/old.py"])
            self.assertIn("verified util/old.py is gone", out)

    def test_commit_body_file_reaches_the_mutation(self) -> None:
        """The body is where a sequence-safety waiver trailer has to live."""
        with tempfile.TemporaryDirectory() as td:
            h = _Harness(Path(td))
            body = Path(td) / "body.txt"
            body.write_text("Why.\n\nAllow-Symbol-Loss: method:Demo.gone\n", encoding="utf-8")
            rc, out = _run(h, [*h.add(), "--commit-body-file", str(body)])
            self.assertEqual(rc, 0, out)
            message = h.mutation()["variables"]["input"]["message"]
            self.assertEqual(message, {"headline": "fix: demo", "body": "Why.\n\nAllow-Symbol-Loss: method:Demo.gone\n"})

    def test_usage_errors_exit_2_before_any_api_call(self) -> None:
        cases = {
            "mutually exclusive": lambda h: [*h.add(), "--commit-body", "x", "--commit-body-file", str(h.payload)],
            "nothing to commit": lambda h: [],
            "more than once": lambda h: [*h.add(), "--delete", TARGET],
            "cannot read": lambda h: ["--add", f"/nonexistent/nope.py:{TARGET}"],
        }
        for expected, build in cases.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as td:
                h = _Harness(Path(td))
                rc, out = _run(h, build(h))
                self.assertEqual(rc, 2, out)
                self.assertIn(expected, out)
                self.assertEqual(h.calls(), [])


if __name__ == "__main__":
    unittest.main()
