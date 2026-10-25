#!/usr/bin/env python3
"""Hermetic gate for util/mcp_setup.bash (turing bring-up task H4).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

Task H4 of ``notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`` writes each checkout's
``.mcp.json`` Serena entry: pinned to a full commit, bound to the checkout with ``--project``, and on a context
whose ``excluded_tools`` hold the shell tool (decision D10). Every case runs the script under ``/bin/bash``
(3.2 on macOS) against a temporary checkout and a pin file of its own; the real home and the repository's
own ``.mcp.json`` are never written.

Pinned here:

- the entry, argument for argument, with the checkout's resolved path; a worktree's ``.git`` file counts;
- the four defects the entry fixes: an entry without ``--project`` (audit A2-F1), one bound to another
  checkout (A2-F4), an unpinned ``git+https://github.com/oraios/serena`` (D10), and one that leaves
  Serena's usage report on (SER-E1 of the H6 audit; owner ruling 2026-10-25). ``--check`` fails on each,
  and a write replaces each. The opt-out is ``SERENA_USAGE_REPORTING`` set to exactly ``false``, the one
  value Serena v1.7.0 compares against;
- other servers and other top-level keys are kept; a changed file is backed up first and keeps its mode;
  a new file is 600; a second run writes nothing; ``--dry-run`` writes nothing;
- ``--remove`` keeps the rest, and deletes a file that held only Serena;
- every refusal exits 2 and writes nothing: a pin that is not a full commit, a context that is a path, a
  source other than upstream, another host's pin, a ``.mcp.json`` that is not a JSON object or is a
  symlink, no checkout, no pin, no python;
- the committed ``conf/hosts/turing/mcp.json`` drives the script and records both checks made at its
  commit, and ``.serena/project.yml`` excludes the shell tool too.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess  # nosec B404 - drives the script under test
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "mcp_setup.bash"
TURING_PIN = REPO_ROOT / "conf" / "hosts" / "turing" / "mcp.json"
BASH = "/bin/bash"
TIMEOUT_SECONDS = 60
SOURCE = "git+https://github.com/oraios/serena"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
OTHER_COMMIT = "fedcba9876543210fedcba9876543210fedcba98"
USAGE_OFF = {"SERENA_USAGE_REPORTING": "false"}  # src/serena/agent.py at v1.7.0 compares the exact string "false"
UNPINNED_A2_F1 = {"type": "stdio", "command": "uvx", "args": ["--from", SOURCE, "serena", "start-mcp-server", "--context", "claude-code"], "env": {}}
DEEPWIKI = {"type": "http", "url": "https://mcp.deepwiki.com/mcp"}
CONTEXT7 = {"type": "http", "url": "https://mcp.context7.com/mcp", "headers": {"CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"}}


class McpSetupHarness(unittest.TestCase):
    """A temporary checkout (a .git directory), a pin file for host 'testhost', and the script runner."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="mcp-setup-")
        self.root = Path(self._tmp.name)  # deliberately unresolved: /var/... vs /private/var/... on macOS
        self.checkout = self.root / "checkout"
        (self.checkout / ".git").mkdir(parents=True)
        self.mcp = self.checkout / ".mcp.json"
        self.conf = self.root / "mcp.json"
        self.write_conf()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_conf(self, host: str = "testhost", **serena) -> None:
        pin = {"source": SOURCE, "release": "v9.9.9", "commit": COMMIT, "context": "claude-code"}
        pin.update(serena)
        self.conf.write_text(json.dumps({"host": host, "serena": pin}), encoding="utf-8")

    def run_setup(self, *args: str, checkout=None, host: str = "testhost", conf=None, python=None) -> subprocess.CompletedProcess:
        argv = [BASH, str(SCRIPT)]
        if host:
            argv += ["--host", host]
        if conf is not False:
            argv += ["--conf", str(conf or self.conf)]
        argv += list(args)
        if checkout is not False:
            argv.append(str(checkout or self.checkout))
        env = RedactedEnv(os.environ)
        env["PYTHON"] = python or sys.executable
        return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603 - fixed argv

    def entry(self, checkout=None, commit: str = COMMIT, env=None) -> dict:
        project = os.path.realpath(checkout or self.checkout)
        args = ["--from", "%s@%s" % (SOURCE, commit), "serena", "start-mcp-server", "--context", "claude-code", "--project", project, "--open-web-dashboard", "False"]
        return {"type": "stdio", "command": "uvx", "args": args, "env": dict(USAGE_OFF) if env is None else env}

    def write_mcp(self, doc, mode=None) -> bytes:
        text = doc if isinstance(doc, str) else json.dumps(doc, indent=2) + "\n"
        self.mcp.write_text(text, encoding="utf-8")
        if mode is not None:
            os.chmod(self.mcp, mode)
        return self.mcp.read_bytes()

    def doc(self) -> dict:
        return json.loads(self.mcp.read_text(encoding="utf-8"))

    def backups(self) -> list:
        return sorted(self.checkout.glob(".mcp.json.bak-*"))

    def assert_rc(self, proc: subprocess.CompletedProcess, code: int) -> None:
        self.assertEqual(proc.returncode, code, "exit %d, want %d\nstdout: %s\nstderr: %s" % (proc.returncode, code, proc.stdout, proc.stderr))

    def assert_only_checkout_files(self, *names: str) -> None:
        self.assertEqual(sorted(p.name for p in self.checkout.iterdir()), sorted((".git",) + names), "nothing else may be written")


class WriteTest(McpSetupHarness):
    def test_a_fresh_checkout_gets_the_pinned_project_bound_entry(self):
        proc = self.run_setup()
        self.assert_rc(proc, 0)
        self.assertEqual(self.doc(), {"mcpServers": {"serena": self.entry()}})
        self.assertIn("wrote", proc.stdout)
        self.assertEqual(stat.S_IMODE(self.mcp.stat().st_mode), 0o600, "a new .mcp.json is private")
        self.assert_only_checkout_files(".mcp.json")

    def test_the_project_is_the_checkouts_resolved_path(self):
        link = self.root / "link-to-checkout"
        link.symlink_to(self.checkout)
        self.assert_rc(self.run_setup(checkout=link), 0)
        project = self.doc()["mcpServers"]["serena"]["args"][7]
        self.assertEqual(project, os.path.realpath(self.checkout))
        self.assertTrue(os.path.isabs(project))

    def test_a_worktree_with_a_dot_git_file_counts(self):
        (self.checkout / ".git").rmdir()
        (self.checkout / ".git").write_text("gitdir: /elsewhere/.git/worktrees/x\n", encoding="utf-8")
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(self.doc()["mcpServers"]["serena"], self.entry())

    def test_serenas_usage_report_is_off(self):
        self.assert_rc(self.run_setup(), 0)
        env = self.doc()["mcpServers"]["serena"]["env"]
        self.assertEqual(env, {"SERENA_USAGE_REPORTING": "false"}, "SER-E1: Serena v1.7.0 skips the report only for this exact value; 'False' or '0' still reports")

    def test_an_entry_written_before_the_opt_out_is_replaced(self):
        old = self.write_mcp({"mcpServers": {"serena": self.entry(env={})}})
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(self.doc()["mcpServers"]["serena"], self.entry())
        self.assertEqual([b.read_bytes() for b in self.backups()], [old])

    def test_a_second_run_writes_nothing(self):
        self.assert_rc(self.run_setup(), 0)
        before = (self.mcp.read_bytes(), self.mcp.stat().st_mtime_ns)
        proc = self.run_setup()
        self.assert_rc(proc, 0)
        self.assertIn("already up to date", proc.stdout)
        self.assertEqual((self.mcp.read_bytes(), self.mcp.stat().st_mtime_ns), before)
        self.assertEqual(self.backups(), [], "an unchanged file needs no backup")

    def test_other_servers_and_top_level_keys_are_kept(self):
        old = self.write_mcp({"mcpServers": {"deepwiki": DEEPWIKI, "context7": CONTEXT7}, "x-note": "keep me"})
        proc = self.run_setup()
        self.assert_rc(proc, 0)
        self.assertEqual(self.doc(), {"mcpServers": {"deepwiki": DEEPWIKI, "context7": CONTEXT7, "serena": self.entry()}, "x-note": "keep me"})
        self.assertIn("kept: context7, deepwiki", proc.stdout)
        self.assertEqual([b.read_bytes() for b in self.backups()], [old], "the old file is backed up before the change")

    def test_the_a2_f1_entry_is_replaced_and_the_mode_kept(self):
        old = self.write_mcp({"mcpServers": {"serena": UNPINNED_A2_F1}}, mode=stat.S_IRUSR)
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(self.doc()["mcpServers"]["serena"], self.entry())
        self.assertEqual(stat.S_IMODE(self.mcp.stat().st_mode), stat.S_IRUSR, "a rewritten file keeps its mode, not a new file's 600")
        self.assertEqual([b.read_bytes() for b in self.backups()], [old])

    def test_an_entry_bound_to_another_checkout_is_rebound(self):
        self.write_mcp({"mcpServers": {"serena": self.entry(checkout="/Users/someone/elsewhere")}})
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(self.doc()["mcpServers"]["serena"], self.entry())

    def test_a_new_pin_replaces_the_old_one(self):
        self.assert_rc(self.run_setup(), 0)
        self.write_conf(commit=OTHER_COMMIT)
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(self.doc()["mcpServers"]["serena"], self.entry(commit=OTHER_COMMIT))

    def test_two_changes_in_one_second_keep_both_backups(self):
        self.write_mcp({"mcpServers": {"serena": UNPINNED_A2_F1}})
        self.assert_rc(self.run_setup(), 0)
        self.write_conf(commit=OTHER_COMMIT)
        self.assert_rc(self.run_setup(), 0)
        self.write_conf(commit=COMMIT)
        self.assert_rc(self.run_setup(), 0)
        self.assertEqual(len(self.backups()), 3, "no backup may overwrite another")


class DryRunTest(McpSetupHarness):
    def test_dry_run_prints_the_document_and_writes_nothing(self):
        proc = self.run_setup("--dry-run")
        self.assert_rc(proc, 0)
        self.assertIn("would write", proc.stdout)
        self.assertIn("%s@%s" % (SOURCE, COMMIT), proc.stdout)
        self.assert_only_checkout_files()

    def test_dry_run_leaves_an_existing_file_alone(self):
        old = self.write_mcp({"mcpServers": {"serena": UNPINNED_A2_F1, "deepwiki": DEEPWIKI}})
        self.assert_rc(self.run_setup("--dry-run"), 0)
        self.assertEqual(self.mcp.read_bytes(), old)
        self.assertEqual(self.backups(), [])

    def test_dry_run_remove_writes_nothing(self):
        old = self.write_mcp({"mcpServers": {"serena": self.entry()}})
        proc = self.run_setup("--remove", "--dry-run")
        self.assert_rc(proc, 0)
        self.assertIn("would delete", proc.stdout)
        self.assertEqual(self.mcp.read_bytes(), old)
        self.assertEqual(self.backups(), [])


class CheckTest(McpSetupHarness):
    def test_check_passes_after_a_write(self):
        self.assert_rc(self.run_setup(), 0)
        proc = self.run_setup("--check")
        self.assert_rc(proc, 0)
        self.assertIn("OK", proc.stdout)

    def test_check_fails_when_the_file_is_missing_and_writes_nothing(self):
        proc = self.run_setup("--check")
        self.assert_rc(proc, 1)
        self.assertIn("does not exist", proc.stdout)
        self.assert_only_checkout_files()

    def test_check_fails_without_a_serena_entry(self):
        self.write_mcp({"mcpServers": {"deepwiki": DEEPWIKI}})
        self.assert_rc(self.run_setup("--check"), 1)

    def test_check_fails_on_the_unpinned_a2_f1_entry(self):
        old = self.write_mcp({"mcpServers": {"serena": UNPINNED_A2_F1}})
        proc = self.run_setup("--check")
        self.assert_rc(proc, 1)
        self.assertIn("differs from the pin", proc.stdout)
        self.assertEqual(self.mcp.read_bytes(), old, "--check never writes")

    def test_check_fails_on_another_checkouts_entry(self):
        self.write_mcp({"mcpServers": {"serena": self.entry(checkout="/Users/someone/elsewhere")}})
        self.assert_rc(self.run_setup("--check"), 1)

    def test_check_fails_on_a_superseded_pin(self):
        self.assert_rc(self.run_setup(), 0)
        self.write_conf(commit=OTHER_COMMIT)
        self.assert_rc(self.run_setup("--check"), 1)

    def test_check_fails_on_an_entry_that_still_reports_usage(self):
        for label, env in {"empty env (H4 before the opt-out)": {}, "capitalised value": {"SERENA_USAGE_REPORTING": "False"}}.items():
            with self.subTest(case=label):
                old = self.write_mcp({"mcpServers": {"serena": self.entry(env=env)}})
                proc = self.run_setup("--check")
                self.assert_rc(proc, 1)
                self.assertIn("differs from the pin", proc.stdout)
                self.assertEqual(self.mcp.read_bytes(), old, "--check never writes")


class RemoveTest(McpSetupHarness):
    def test_remove_keeps_the_other_servers(self):
        old = self.write_mcp({"mcpServers": {"serena": self.entry(), "deepwiki": DEEPWIKI}})
        proc = self.run_setup("--remove")
        self.assert_rc(proc, 0)
        self.assertEqual(self.doc(), {"mcpServers": {"deepwiki": DEEPWIKI}})
        self.assertIn("kept: deepwiki", proc.stdout)
        self.assertEqual([b.read_bytes() for b in self.backups()], [old])

    def test_remove_deletes_a_file_that_held_only_serena(self):
        old = self.write_mcp({"mcpServers": {"serena": self.entry()}})
        self.assert_rc(self.run_setup("--remove"), 0)
        self.assertFalse(self.mcp.exists())
        self.assertEqual([b.read_bytes() for b in self.backups()], [old])

    def test_remove_keeps_other_top_level_keys(self):
        self.write_mcp({"mcpServers": {"serena": self.entry()}, "x-note": 1})
        self.assert_rc(self.run_setup("--remove"), 0)
        self.assertEqual(self.doc(), {"x-note": 1})

    def test_remove_without_an_entry_changes_nothing(self):
        old = self.write_mcp({"mcpServers": {"deepwiki": DEEPWIKI}})
        proc = self.run_setup("--remove")
        self.assert_rc(proc, 0)
        self.assertIn("nothing to remove", proc.stdout)
        self.assertEqual(self.mcp.read_bytes(), old)
        self.assertEqual(self.backups(), [])


class RefusalTest(McpSetupHarness):
    """Every refusal exits 2 and leaves the checkout as it was."""

    def assert_refused(self, proc: subprocess.CompletedProcess, needle: str) -> None:
        self.assert_rc(proc, 2)
        self.assertIn(needle, proc.stderr)

    def test_bad_arguments(self):
        cases = {
            ("--bogus",): "unknown option",
            ("--check", "--remove"): "cannot be combined",
            ("--host",): "needs a value",
        }
        for args, needle in cases.items():
            with self.subTest(args=args):
                self.assert_refused(self.run_setup(*args, checkout=False), needle)
        self.assert_refused(self.run_setup(str(self.checkout)), "only one checkout")
        self.assert_refused(self.run_setup(host="Bad_Host!"), "not a host name")
        self.assert_only_checkout_files()

    def test_the_checkout_must_be_a_git_checkout(self):
        self.assert_refused(self.run_setup(checkout=self.root / "missing"), "not a directory")
        plain = self.root / "plain"
        plain.mkdir()
        self.assert_refused(self.run_setup(checkout=plain), "not a git checkout")
        self.assertEqual(list(plain.iterdir()), [])

    def test_no_pin_no_serena(self):
        self.assert_refused(self.run_setup(conf=self.root / "absent.json"), "no Serena pin")
        proc = self.run_setup(host="nosuchhost", conf=False)
        self.assert_refused(proc, "conf/hosts/nosuchhost/mcp.json")
        self.assert_only_checkout_files()

    def test_a_pin_must_be_a_full_commit_of_upstream_serena_on_a_built_in_context(self):
        cases = {
            "short sha": ({"commit": COMMIT[:8]}, "full 40-hex commit"),
            "branch": ({"commit": "main"}, "full 40-hex commit"),
            "tag": ({"commit": "v1.7.0"}, "full 40-hex commit"),
            "upper-case hex": ({"commit": COMMIT.upper()}, "full 40-hex commit"),
            "context path": ({"context": "/tmp/evil-context.yml"}, "built-in context name"),
            "context climb": ({"context": "../evil"}, "built-in context name"),
            "a fork": ({"source": "git+https://github.com/someone/serena"}, "serena.source must be"),
        }
        for label, (serena, needle) in cases.items():
            with self.subTest(case=label):
                self.write_conf(**serena)
                self.assert_refused(self.run_setup(), needle)
        self.write_conf(host="otherhost")
        self.assert_refused(self.run_setup(), "the pin of host 'otherhost'")
        self.conf.write_text("{not json", encoding="utf-8")
        self.assert_refused(self.run_setup(), "cannot read the pin file")
        self.conf.write_text(json.dumps({"host": "testhost"}), encoding="utf-8")
        self.assert_refused(self.run_setup(), "has no 'serena' object")
        self.assert_only_checkout_files()

    def test_an_existing_file_that_is_not_a_json_object_is_never_overwritten(self):
        cases = {
            "invalid JSON": ('{"mcpServers": ', "not valid JSON"),
            "an array": ("[]\n", "not a JSON object"),
            "mcpServers a list": (json.dumps({"mcpServers": []}), "mcpServers is not a JSON object"),
        }
        for label, (text, needle) in cases.items():
            with self.subTest(case=label):
                old = self.write_mcp(text)
                self.assert_refused(self.run_setup(), needle)
                self.assertEqual(self.mcp.read_bytes(), old)
                self.assertEqual(self.backups(), [])

    def test_a_symlinked_mcp_json_is_refused(self):
        real = self.root / "shared-mcp.json"
        real.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
        self.mcp.symlink_to(real)
        self.assert_refused(self.run_setup(), "not a regular file")
        self.assertEqual(json.loads(real.read_text(encoding="utf-8")), {"mcpServers": {}})

    def test_no_python(self):
        self.assert_refused(self.run_setup(python="/nonexistent/python3"), "python3 not found")
        self.assert_only_checkout_files()


class UsageTest(McpSetupHarness):
    def test_help(self):
        proc = self.run_setup("--help", checkout=False)
        self.assert_rc(proc, 0)
        self.assertIn("Usage: mcp_setup.bash", proc.stdout)

    def test_the_default_checkout_is_the_scripts_own(self):
        proc = self.run_setup("--dry-run", checkout=False)
        self.assert_rc(proc, 0)
        self.assertIn(str(REPO_ROOT.resolve()), proc.stdout, "with no checkout argument the script configures its own checkout")


class CommittedFilesTest(McpSetupHarness):
    """The committed pin and the project file that the agents on turing get."""

    def test_turings_pin_is_a_full_commit_of_upstream_serena(self):
        conf = json.loads(TURING_PIN.read_text(encoding="utf-8"))
        self.assertEqual(conf["host"], "turing")
        pin = conf["serena"]
        self.assertEqual(pin["source"], SOURCE)
        self.assertRegex(pin["commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(pin["release"], r"^v\d+\.\d+\.\d+$")
        self.assertEqual(pin["context"], "claude-code", "the context whose excluded_tools were verified at the pin")
        self.assertIn("execute_shell_command", pin["verified"], "a pin records that its context excludes the shell tool")
        self.assertIn("SERENA_USAGE_REPORTING", pin["verified"], "a pin records that the usage-report opt-out was checked at its commit")

    def test_turings_pin_drives_the_script(self):
        proc = self.run_setup("--dry-run", host="turing", conf=False)
        self.assert_rc(proc, 0)
        commit = json.loads(TURING_PIN.read_text(encoding="utf-8"))["serena"]["commit"]
        self.assertIn("%s@%s" % (SOURCE, commit), proc.stdout)
        self.assert_only_checkout_files()

    def test_the_serena_project_excludes_the_shell_tool(self):
        project = yaml.safe_load((REPO_ROOT / ".serena" / "project.yml").read_text(encoding="utf-8"))
        self.assertIn("execute_shell_command", project.get("excluded_tools") or [], "D10: belt and braces beside the context")

    def test_mcp_json_and_its_backups_stay_per_checkout(self):
        lines = [line.strip() for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(re.fullmatch(r"/?\.mcp\.json", line) for line in lines), "the entry holds a checkout's absolute path, so it is never committed")
        self.assertIn(".mcp.json.bak-*", lines, "a backup holds the previous file, API tokens included")


if __name__ == "__main__":
    unittest.main()
