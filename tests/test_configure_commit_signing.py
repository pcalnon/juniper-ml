#!/usr/bin/env python3
"""Hermetic gate for util/configure_commit_signing.py (commit-signing plan, regressions R-S1..R-S19).

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`` signs the owner's
commits in the Juniper tree through one conditional include. That covers three paths:

- the terminal;
- the IDE Source Control view, through git's ``commit.gpgsign``. The IDEs' git extension adds
  ``-S`` only when told to, and never disables signing;
- the integrated terminal.

Agent sessions stay unsigned by construction (bring-up plan D11). The suite also pins where D11
stops: an explicit ``-S``, ``-c include.path=`` or ``--config-env`` still signs, and only the C8
guard and K12 close those paths.

How the suite stays hermetic:

- Real ``git`` runs on real repositories under a temp ``HOME``, with the Juniper root inside it.
  - Every ``GIT_*`` variable is scrubbed, including the session's ``GIT_CONFIG_COUNT`` signing guard.
  - ``GIT_CONFIG_NOSYSTEM=1`` keeps the runner's system config out.
  - ``XDG_CONFIG_HOME``, ``GNUPGHOME`` and the tool's own variables are scrubbed.
  - Environments are ``RedactedEnv`` (``tests/redacted_env.py``), the type
    ``tests/test_env_repr_safety.py`` enforces.
- ``gpg.program`` is a recording fake installed as Homebrew would install it: the file under
  ``opt/Cellar/gnupg/<version>/bin/``, reached through ``bin/gpg``. It logs its argv. It then answers
  the way git expects of a successful detached signature, with ``[GNUPG:] SIG_CREATED`` on fd 2 and
  an armored block on stdout. So an end-to-end ``git commit`` leaves a ``gpgsig`` header exactly when
  signing was configured. The tool itself must never run the fake, so the log is a tripwire for every
  tool run.
- Placeholder ``~/.gnupg`` and ``~/.ssh`` files exist under the temp HOME, so the audit-hook run can
  prove the tool opens neither. Nothing here touches the real keyring, card or agent.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - drives the tool and real git on temp repos
import sys
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "configure_commit_signing.py"
SYSTEM_PYTHON = "/usr/bin/python3"
TIMEOUT_SECONDS = 120
TODAY = "2026-10-19"

ACTIVE = ("canopy", "cascor", "cascor-client", "cascor-worker", "data", "data-client", "deploy", "k8s", "ml", "recurrence")
KEY = "B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!"
PATTERN = "gitdir/i:~/Development/python/Juniper/"
INCLUDE_KEY = f"includeIf.{PATTERN}.path"
INCLUDE_VALUE = "~/.config/git/juniper-signing.gitconfig"
D11_ENV = {"GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "commit.gpgsign", "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "tag.gpgsign", "GIT_CONFIG_VALUE_1": "false"}
# What Cursor 3.25.9's git extension appends to every git spawn (plan §3).
CURSOR_KEYS = (("safe.bareRepository", "explicit"), ("core.fsmonitor", "false"), ("core.attributesFile", "/dev/null"))
# The plan's S7 fallback deny pair (VS Code), from consensus round 1, reviewer R2.
S7_DENY_PAIR = {
    "/\\bgit\\b.*\\s(commit|merge|rebase|cherry-pick|revert|am|pull|tag)(?![\\w-])/i": False,
    "/--no-gpg-sign|gpgsign|gpg\\.program|--config-env|include(if)?\\b[^\\s=]*\\.path|GIT_CONFIG_|GNUPGHOME/i": False,
}

TOP_KEYS = {"schema", "mode", "root", "include_file", "global_config", "expected", "writes", "rollback", "checks", "ok", "exit_code", "summary"}
WRITE_KEYS = {"action", "file", "key", "from", "to", "applied"}
CHECK_KEYS = {"id", "status", "message", "remediation"}

GLOBAL_CONFIG = "[user]\n\tname = Signing Test\n\temail = signing-test@example.invalid\n[init]\n\tdefaultBranch = main\n"

FAKE_GPG = r"""#!/bin/sh
# Recording stand-in for gpg.program: log argv, swallow the payload, answer as a successful detached signature.
printf '%s\n' "$*" >> "$FAKE_GPG_LOG"
cat > /dev/null
printf '[GNUPG:] SIG_CREATED D 22 8 00 1760000000 B5619F58FDA4D94E2D73D8BABA18D1A733B1831A\n' >&2
printf -- '-----BEGIN PGP SIGNATURE-----\n\nZmFrZQ==\n-----END PGP SIGNATURE-----\n'
"""

# Runs the tool in-process under an audit hook, recording every file it opens (with the open flags)
# and every process it starts.
AUDIT_WRAPPER = r"""
import json, os, runpy, sys
log = {"open": [], "exec": []}
WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
def hook(event, args):
    if event == "open" and isinstance(args[0], str):
        mode, flags = args[1], args[2]
        writes = bool(flags & WRITE) if isinstance(flags, int) else bool(mode and any(c in mode for c in "wax+"))
        log["open"].append([args[0], writes])
    elif event in ("os.listdir", "os.scandir") and isinstance(args[0], str):
        log["open"].append([args[0], False])
    elif event == "subprocess.Popen":
        log["exec"].append([str(args[0]), [str(a) for a in (args[1] or [])]])
    elif event in ("os.exec", "os.posix_spawn", "os.spawn", "os.system"):
        log["exec"].append([str(args[0]), []])
sys.addaudithook(hook)
out, script, argv = sys.argv[1], sys.argv[2], sys.argv[3:]
sys.argv = [script, *argv]
code = 0
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else 1
finally:
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(log, fh)
sys.exit(code)
"""


def tree_digest(path: Path) -> str:
    """A digest of every file name, mode and content under ``path`` (symlinks by target)."""
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames.sort()
        digest.update(os.path.relpath(dirpath, path).encode())
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            digest.update(os.path.relpath(full, path).encode())
            if os.path.islink(full):
                digest.update(os.readlink(full).encode())
                continue
            digest.update(oct(os.stat(full).st_mode).encode())
            with open(full, "rb") as fh:
                digest.update(fh.read())
    return digest.hexdigest()


class SigningHarness(unittest.TestCase):
    """A temp HOME with a Juniper root of real checkouts, a Homebrew-shaped fake gpg, and a scrubbed environment."""

    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="commit-signing-")))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.root = self.home / "Development" / "python" / "Juniper"
        self.root.mkdir(parents=True)
        (self.home / ".gitconfig").write_text(GLOBAL_CONFIG, encoding="utf-8")
        for secret_dir, name in ((".gnupg", "gpg-agent.conf"), (".ssh", "config")):
            (self.home / secret_dir).mkdir(mode=0o700)
            (self.home / secret_dir / name).write_text("placeholder: the tool must never open this\n", encoding="utf-8")
        self.gpg_real = self.install_gpg("2.4.8")
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.gpg = self.bin / "gpg"
        self.gpg.symlink_to(self.gpg_real)
        self.gpg_log = self.tmp / "gpg.log"
        self.include = self.home / ".config" / "git" / "juniper-signing.gitconfig"
        scrubbed = ("XDG_CONFIG_HOME", "JUNIPER_ROOT", "COMMIT_SIGNING_GPG_CANDIDATES", "COMMIT_SIGNING_TODAY", "COMMIT_SIGNING_GNUPG_CELLARS", "GNUPGHOME")
        base = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in scrubbed})
        self.cellar = self.tmp / "opt" / "Cellar"
        # GIT_CEILING_DIRECTORIES: TMPDIR is a repo's tmp/ (the 2026-10-26 rule), so without a ceiling git run
        # under self.tmp finds the ENCLOSING checkout, and the include file reads as inside a work tree. The
        # ceiling is self.tmp's PARENT because git ignores a ceiling equal to the directory it starts in.
        self.env = RedactedEnv(base, HOME=str(self.home), GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(self.tmp.parent), FAKE_GPG_LOG=str(self.gpg_log), COMMIT_SIGNING_TODAY=TODAY, COMMIT_SIGNING_GNUPG_CELLARS=str(self.cellar), LC_ALL="C")
        for name in ACTIVE:
            self.git("init", "-q", str(self.root / f"juniper-{name}"))

    # ------------------------------------------------------------------------------------- helpers

    def install_gpg(self, version: str) -> Path:
        path = self.tmp / "opt" / "Cellar" / "gnupg" / version / "bin" / "gpg"
        path.parent.mkdir(parents=True)
        path.write_text(FAKE_GPG, encoding="utf-8")
        path.chmod(0o755)
        return path

    def git(self, *args: str, env: dict | None = None, stdin: str | None = None, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
        proc = subprocess.run(["git", *args], env=RedactedEnv(self.env, **(env or {})), input=stdin, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False, cwd=cwd)
        if check and proc.returncode != 0:
            self.fail(f"git {' '.join(args)} exited {proc.returncode}: {proc.stderr}")
        return proc

    def tool(self, *args: str, env: dict | None = None, root: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-I", str(SCRIPT_PATH), "--root", str(root or self.root), *args], env=RedactedEnv(self.env, **(env or {})), capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)

    def tool_json(self, *args: str, env: dict | None = None, root: Path | None = None) -> tuple[int, dict]:
        proc = self.tool("--json", *args, env=env, root=root)
        self.assertIn(proc.returncode, (0, 1, 2), proc.stderr)
        try:
            report = json.loads(proc.stdout)
        except ValueError as exc:
            raise self.failureException(f"not JSON (exit {proc.returncode}): stdout={proc.stdout!r} stderr={proc.stderr!r}") from exc
        return proc.returncode, report

    def apply(self, *extra: str, env: dict | None = None) -> dict:
        code, report = self.tool_json("--apply", "--gpg-program", str(self.gpg), *extra, env=env)
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual(self.git("config", "--file", str(self.include), "--get", "gpg.program").stdout.strip(), str(self.gpg), "the fake must be the program before any commit")
        return report

    def checks(self, report: dict) -> dict:
        return {c["id"]: c for c in report["checks"]}

    def gpg_calls(self) -> list[str]:
        return self.gpg_log.read_text(encoding="utf-8").splitlines() if self.gpg_log.exists() else []

    def commit_header(self, repo: Path) -> str:
        return self.git("-C", str(repo), "cat-file", "commit", "HEAD").stdout.split("\n\n", 1)[0]

    def assert_signed(self, repo: Path, calls_before: int):
        self.assertIn("gpgsig -----BEGIN PGP SIGNATURE-----", self.commit_header(repo))
        calls = self.gpg_calls()[calls_before:]
        self.assertEqual(len(calls), 1, calls)
        self.assertIn(f"-bsau {KEY}", calls[0])

    def assert_unsigned(self, repo: Path, calls_before: int):
        self.assertNotIn("gpgsig ", self.commit_header(repo))
        self.assertEqual(len(self.gpg_calls()), calls_before)

    def assert_tripwire_quiet(self):
        self.assertEqual(self.gpg_calls(), [], "the tool ran gpg.program; it must only check paths and modes")


# ------------------------------------------------------------------------------------- apply, remove


class ApplyTest(SigningHarness):
    def test_apply_installs_the_include_and_its_wiring(self):
        original = (self.home / ".gitconfig").read_text(encoding="utf-8")
        report = self.apply()
        self.assertEqual(report["mode"], "apply")
        self.assertEqual([w["action"] for w in report["writes"]], ["mkdir", "create", "set", "set", "set", "set", "backup", "add"])
        self.assertTrue(all(w["applied"] for w in report["writes"]))
        self.assertTrue(self.include.read_text(encoding="utf-8").startswith("# Managed by util/configure_commit_signing.py"))
        values = {k: self.git("config", "--file", str(self.include), "--get", k).stdout.strip() for k in ("user.signingkey", "commit.gpgsign", "tag.gpgsign", "gpg.program")}
        self.assertEqual(values, {"user.signingkey": KEY, "commit.gpgsign": "true", "tag.gpgsign": "true", "gpg.program": str(self.gpg)})
        self.assertEqual(self.git("config", "--global", "--get-all", INCLUDE_KEY).stdout.split(), [INCLUDE_VALUE])
        self.assertEqual(oct(self.include.parent.stat().st_mode & 0o777), oct(0o700))
        self.assertEqual(oct(self.include.stat().st_mode & 0o777), oct(0o600))
        backup = self.home / f".gitconfig.bak-{TODAY}-pre-commit-signing"
        self.assertEqual(backup.read_text(encoding="utf-8"), original)
        by_id = self.checks(report)
        for name in ACTIVE:
            self.assertEqual(by_id[f"repo:juniper-{name}"]["status"], "pass", by_id[f"repo:juniper-{name}"])
        self.assertIn(str(self.include), by_id["repo:juniper-ml"]["message"])
        self.assertEqual(by_id["include"]["status"], "pass", by_id["include"])
        self.assertTrue(any("--fixed-value --unset-all" in line for line in report["rollback"]))
        self.assert_tripwire_quiet()

    def test_r_s7_a_second_apply_writes_nothing_and_changes_no_byte(self):
        self.apply()
        before = tree_digest(self.home)
        report = self.apply()
        self.assertEqual(report["writes"], [])
        self.assertEqual(report["rollback"], [])
        self.assertEqual(tree_digest(self.home), before)
        self.assertIn("wrote 0 changes", report["summary"])

    def test_r_s6_dry_run_writes_nothing_and_exits_like_check(self):
        before = tree_digest(self.tmp)
        code, report = self.tool_json("--apply", "--dry-run", "--gpg-program", str(self.gpg))
        self.assertEqual(code, 1, "a dry run changes nothing, so the checks still fail")
        self.assertEqual(report["mode"], "apply-dry-run")
        self.assertEqual(len(report["writes"]), 8)
        self.assertFalse(any(w["applied"] for w in report["writes"]))
        self.assertEqual(self.checks(report)["repo:juniper-ml"]["status"], "fail")
        self.assertEqual(tree_digest(self.tmp), before)
        text = self.tool("--apply", "--dry-run", "--gpg-program", str(self.gpg))
        self.assertIn("PLAN   create", text.stdout)
        self.assertIn("nothing written", text.stdout)
        self.apply()
        code, report = self.tool_json("--apply", "--dry-run", "--gpg-program", str(self.gpg))
        self.assertEqual((code, report["writes"]), (0, []))

    def test_r_s8_backups_are_made_once_and_an_owner_include_is_kept(self):
        owner_inc = self.home / "owner.inc"
        owner_inc.write_text("[core]\n\teditor = vi\n", encoding="utf-8")
        self.git("config", "--global", "--add", INCLUDE_KEY, str(owner_inc))
        with open(self.home / ".gitconfig", "a", encoding="utf-8") as fh:
            fh.write("[commit]\n\tgpgsign = false\n")
        code, report = self.tool_json("--apply", "--gpg-program", str(self.gpg))
        self.assertEqual(code, 1, "the owner's later global gpgsign=false still wins; --check is the guarantee, not position")
        self.assertIn("commit.gpgsign=false (global", self.checks(report)["repo:juniper-ml"]["message"])
        self.assertEqual(self.git("config", "--global", "--get-all", INCLUDE_KEY).stdout.split(), [str(owner_inc), INCLUDE_VALUE])
        self.git("config", "--global", "--unset", "commit.gpgsign")
        backup = self.home / f".gitconfig.bak-{TODAY}-pre-commit-signing"
        backup.write_text("an earlier backup\n", encoding="utf-8")
        self.git("config", "--global", "--fixed-value", "--unset", INCLUDE_KEY, INCLUDE_VALUE)
        self.git("config", "--file", str(self.include), "tag.gpgsign", "false")
        report = self.apply()
        self.assertEqual([w["action"] for w in report["writes"]], ["backup", "set", "add"])
        self.assertEqual(backup.read_text(encoding="utf-8"), "an earlier backup\n")
        include_backup = Path(f"{self.include}.bak-{TODAY}-pre-commit-signing")
        self.assertIn("gpgsign = false", include_backup.read_text(encoding="utf-8"))

    def test_apply_keeps_a_sound_existing_program(self):
        other = self.install_gpg("2.4.9")
        code, _ = self.tool_json("--apply", "--gpg-program", str(other))
        self.assertEqual(code, 0)
        code, report = self.tool_json("--apply", env={"COMMIT_SIGNING_GPG_CANDIDATES": str(self.gpg)})
        self.assertEqual(code, 0)
        self.assertEqual(report["writes"], [], "a sound existing gpg.program is kept, not replaced by a candidate")
        self.assertEqual(report["expected"]["gpg_program"], str(other))

    def test_candidates_must_be_sound_and_in_a_known_install(self):
        untrusted = self.bin / "my-gpg"
        shutil.copy2(self.gpg_real, untrusted)
        missing = self.tmp / "nowhere" / "gpg"
        code, report = self.tool_json("--apply", env={"COMMIT_SIGNING_GPG_CANDIDATES": f"{missing}:{untrusted}:{self.gpg}"})
        self.assertEqual(code, 0)
        self.assertEqual(report["expected"]["gpg_program"], str(self.gpg))
        shutil.rmtree(self.home / ".config")
        before = tree_digest(self.home)
        proc = self.tool("--apply", env={"COMMIT_SIGNING_GPG_CANDIDATES": f"{missing}:{untrusted}"})
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no sound gpg program", proc.stderr)
        self.assertEqual(tree_digest(self.home), before)

    def test_remove_undoes_apply_exactly_and_keeps_the_owner_include(self):
        original = (self.home / ".gitconfig").read_bytes()
        self.apply()
        code, report = self.tool_json("--remove")
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual([w["action"] for w in report["writes"]], ["unset", "remove-section", "delete", "rmdir"])
        self.assertEqual((self.home / ".gitconfig").read_bytes(), original)
        self.assertFalse(self.include.parent.exists())
        owner_inc = self.home / "owner.inc"
        owner_inc.write_text("[core]\n\teditor = vi\n", encoding="utf-8")
        self.git("config", "--global", "--add", INCLUDE_KEY, str(owner_inc))
        self.apply()
        code, report = self.tool_json("--remove")
        self.assertEqual(code, 0)
        self.assertNotIn("remove-section", [w["action"] for w in report["writes"]])
        self.assertEqual(self.git("config", "--global", "--get-all", INCLUDE_KEY).stdout.split(), [str(owner_inc)])

    def test_remove_refuses_to_delete_an_edited_include_and_dry_run_writes_nothing(self):
        self.apply()
        self.git("config", "--file", str(self.include), "core.editor", "vi")
        before = tree_digest(self.home)
        code, report = self.tool_json("--remove", "--dry-run")
        self.assertEqual(code, 1)
        self.assertEqual([w["action"] for w in report["writes"]], ["unset", "remove-section"], "the edited include is not planned for deletion")
        self.assertEqual(tree_digest(self.home), before)
        code, report = self.tool_json("--remove")
        self.assertEqual(code, 1)
        self.assertIn("left in place", self.checks(report)["remove"]["message"])
        self.assertTrue(self.include.exists())
        self.assertEqual(self.git("config", "--global", "--get-all", INCLUDE_KEY, check=False).returncode, 1, "the wiring is removed even when the file is kept")

    # ---------------------------------------------------------------------------------------- refusals

    def test_remove_keeps_an_include_another_root_still_uses(self):
        # Round 2, N5: deleting the file would make the other root's include fail open.
        other = self.home / "Projects" / "Juniper"
        self.git("init", "-q", str(other / "juniper-ml"))
        self.apply()
        code, _ = self.tool_json("--apply", "--gpg-program", str(self.gpg), root=other)
        self.assertEqual(code, 0)
        code, report = self.tool_json("--remove", root=other)
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual([w["action"] for w in report["writes"]], ["unset", "remove-section"])
        self.assertIn("still includes it", self.checks(report)["remove"]["message"])
        self.assertTrue(self.include.exists())
        repo = self.root / "juniper-ml"
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "the first root still signs")
        self.assert_signed(repo, before)

    def test_remove_refuses_an_include_with_a_comment_added(self):
        # Round 2, N18: "managed" means byte for byte what --apply writes, comments included.
        self.apply()
        with open(self.include, "a", encoding="utf-8") as fh:
            fh.write("# the owner's note\n")
        code, report = self.tool_json("--remove")
        self.assertEqual(code, 1)
        self.assertTrue(self.include.exists())
        self.assertIn("differs from what --apply writes", self.checks(report)["remove"]["message"])


class RefusalTest(SigningHarness):
    def test_apply_refuses_to_write_through_an_unsafe_include_or_directory(self):
        # Round 2, N6: git's --file writer follows a symlink, so the keys would land in the target.
        target = self.tmp / "elsewhere" / "target.gitconfig"
        target.parent.mkdir(parents=True)
        target.write_text("[core]\n\teditor = vi\n", encoding="utf-8")
        self.include.parent.mkdir(parents=True)
        self.include.symlink_to(target)
        proc = self.tool("--apply", "--gpg-program", str(self.gpg))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("will not write through it", proc.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "[core]\n\teditor = vi\n")
        self.include.unlink()
        self.include.parent.chmod(0o777)
        self.addCleanup(self.include.parent.chmod, 0o700)
        proc = self.tool("--apply", "--gpg-program", str(self.gpg))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("writable by group or others", proc.stderr)
        self.assertFalse(self.include.exists())

    def test_r_s18_a_cellar_shaped_path_outside_homebrew_is_not_a_known_install(self):
        # Round 2, N4: only Homebrew's own Cellar directories count; any ".../Cellar/gnupg/<v>/bin/gpg" does not.
        self.apply()
        code, report = self.tool_json("--check", env={"COMMIT_SIGNING_GNUPG_CELLARS": ""})
        self.assertEqual(code, 1)
        self.assertIn("not a known GnuPG install", self.checks(report)["repo:juniper-ml"]["message"])

    def test_r_s1_an_unpinned_or_malformed_key_exits_2_before_any_write(self):
        before = tree_digest(self.home)
        for spec in ("BA18D1A733B1831A", KEY[:-1], "XYZ!", "BA18D1A733B1831!", "!", "BA18D1A733B1831A!!"):
            with self.subTest(spec=spec):
                proc = self.tool("--apply", "--gpg-program", str(self.gpg), "--signing-key", spec)
                self.assertEqual(proc.returncode, 2, proc.stdout)
                self.assertIn("--signing-key", proc.stderr)
        self.assertEqual(tree_digest(self.home), before)

    def test_r_s1_an_unpinned_key_in_the_include_fails_the_check(self):
        self.apply()
        self.git("config", "--file", str(self.include), "user.signingkey", "BA18D1A733B1831A")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        message = self.checks(report)["repo:juniper-ml"]["message"]
        self.assertIn("user.signingkey=BA18D1A733B1831A", message)
        self.assertIn(f"expected {KEY}", message)

    def test_the_spec_is_normalised_and_the_long_id_is_a_different_spec(self):
        self.apply("--signing-key", "0xb5619f58fda4d94e2d73d8baba18d1a733b1831a!")
        self.assertEqual(self.git("config", "--file", str(self.include), "--get", "user.signingkey").stdout.strip(), KEY)
        code, _ = self.tool_json("--check", "--signing-key", "BA18D1A733B1831A!")
        self.assertEqual(code, 1)

    def test_r_s2_an_unsound_gpg_program_exits_2_before_any_write(self):
        plain = self.bin / "not-executable"
        plain.write_text("#!/bin/sh\n", encoding="utf-8")
        plain.chmod(0o644)
        writable = self.install_gpg("9.9.9")
        writable.chmod(0o775)
        before = tree_digest(self.home)
        for program, reason in (("gpg", "not an absolute path"), (str(self.tmp / "absent"), "does not exist"), (str(plain), "not executable"), (str(writable), "writable by group or others")):
            with self.subTest(program=program):
                proc = self.tool("--apply", "--gpg-program", program)
                self.assertEqual(proc.returncode, 2)
                self.assertIn(reason, proc.stderr)
        self.assertEqual(tree_digest(self.home), before)

    def test_r_s2_an_unsound_program_in_the_config_fails_the_check(self):
        self.apply()
        self.git("config", "--file", str(self.include), "gpg.program", "gpg")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertIn("not an absolute path", self.checks(report)["repo:juniper-ml"]["message"])
        self.git("config", "--file", str(self.include), "gpg.program", str(self.gpg))
        self.gpg_real.chmod(0o777)
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertIn("writable by group or others", self.checks(report)["repo:juniper-ml"]["message"])

    def test_r_s18_a_program_outside_a_known_gnupg_install_fails_unless_vouched_for(self):
        planted = self.home / ".local" / "bin" / "x"
        planted.parent.mkdir(parents=True)
        shutil.copy2(self.gpg_real, planted)
        self.apply()
        self.git("config", "--file", str(self.include), "gpg.program", str(planted))
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertIn("not a known GnuPG install", self.checks(report)["repo:juniper-ml"]["message"])
        code, _ = self.tool_json("--check", "--gpg-program", str(planted))
        self.assertEqual(code, 0)
        proc = self.tool("--apply", env={"COMMIT_SIGNING_GPG_CANDIDATES": str(self.gpg)})
        self.assertEqual(proc.returncode, 0, "--apply replaces an existing value that is not in a known install")
        self.assertEqual(self.git("config", "--file", str(self.include), "--get", "gpg.program").stdout.strip(), str(self.gpg))

    def test_a_later_gpg_openpgp_program_decides_and_is_judged(self):
        self.apply()
        self.git("config", "--global", "gpg.openpgp.program", "gpg2")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertIn("gpg.openpgp.program: 'gpg2' is not an absolute path", self.checks(report)["repo:juniper-ml"]["message"])

    def test_r_s15_home_and_root_spelled_through_symlinks_still_sign(self):
        link_home = self.tmp / "link-home"
        link_home.symlink_to(self.home)
        link_root = link_home / "Development" / "python" / "Juniper"
        code, report = self.tool_json("--apply", "--gpg-program", str(self.gpg), env={"HOME": str(link_home)}, root=link_root)
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual(self.git("config", "--global", "--get-all", INCLUDE_KEY).stdout.split(), [INCLUDE_VALUE])
        repo = self.root / "juniper-ml"
        before = len(self.gpg_calls())
        self.git("-C", str(link_root / "juniper-ml"), "commit", "--allow-empty", "-q", "-m", "through the symlinks", env={"HOME": str(link_home)})
        self.assert_signed(repo, before)

    def test_a_root_outside_home_is_written_as_its_realpath(self):
        outside = self.tmp / "srv" / "Juniper"
        (outside / "juniper-ml").mkdir(parents=True)
        self.git("init", "-q", str(outside / "juniper-ml"))
        link = self.tmp / "srv-link"
        link.symlink_to(self.tmp / "srv")
        code, report = self.tool_json("--apply", "--gpg-program", str(self.gpg), root=link / "Juniper")
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual(self.git("config", "--global", "--get-all", f"includeIf.gitdir/i:{outside}/.path").stdout.split(), [INCLUDE_VALUE])

    def test_r_s13_unusable_roots_and_include_paths_exit_2(self):
        dotfiles = self.tmp / "dotfiles"
        self.git("init", "-q", str(dotfiles))
        cases = (
            ([], self.home, "is $HOME or an ancestor"),
            ([], self.tmp, "is $HOME or an ancestor"),
            (["--include-file", str(self.root / "signing.inc")], self.root, "is under the Juniper root"),
            (["--include-file", str(dotfiles / "conf" / "signing.inc")], self.root, "inside a git work tree"),
        )
        for args, root, message in cases:
            with self.subTest(args=args, root=root):
                proc = self.tool("--apply", "--gpg-program", str(self.gpg), *args, root=root)
                self.assertEqual(proc.returncode, 2, proc.stdout)
                self.assertIn(message, proc.stderr)
        glob_root = self.home / "Development" / "Jun[ip]er"
        glob_root.mkdir()
        proc = self.tool("--check", root=glob_root)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("glob character", proc.stderr)


# ----------------------------------------------------------------------------------------- overrides


class OverrideTest(SigningHarness):
    def test_r_s3_a_repo_local_override_fails_that_repo_and_names_the_scope(self):
        self.apply()
        self.git("-C", str(self.root / "juniper-data"), "config", "--local", "commit.gpgsign", "false")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        by_id = self.checks(report)
        data = by_id["repo:juniper-data"]
        self.assertIn("commit.gpgsign=false (local file:.git/config)", data["message"])
        self.assertIn("--local --unset-all commit.gpgsign", data["remediation"])
        self.assertEqual(by_id["repo:juniper-ml"]["status"], "pass")

    def test_r_s3_a_later_global_false_wins_and_fails_every_repo(self):
        self.apply()
        with open(self.home / ".gitconfig", "a", encoding="utf-8") as fh:
            fh.write("[commit]\n\tgpgsign = false\n")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        for name in ACTIVE:
            self.assertIn("commit.gpgsign=false (global", self.checks(report)[f"repo:juniper-{name}"]["message"])

    def test_tag_gpgsign_false_fails_on_its_own(self):
        self.apply()
        self.git("config", "--file", str(self.include), "tag.gpgsign", "false")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        message = self.checks(report)["repo:juniper-ml"]["message"]
        self.assertIn("tag.gpgsign=false", message)
        self.assertNotIn("commit.gpgsign", message)

    def test_gpg_format_ssh_and_a_missing_email_fail(self):
        self.apply()
        self.git("config", "--global", "gpg.format", "ssh")
        self.git("config", "--global", "--unset", "user.email")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        message = self.checks(report)["repo:juniper-ml"]["message"]
        self.assertIn("gpg.format=ssh", message)
        self.assertIn("user.email is unset", message)

    def test_r_s16_planted_local_keys_fail_and_the_own_hooks_path_passes(self):
        self.apply()
        planted = {
            "juniper-data": ("gpg.program", str(self.gpg)),
            "juniper-deploy": ("include.path", str(self.tmp / "x.inc")),
            "juniper-canopy": ("core.sshCommand", "ssh -i /tmp/key"),
            "juniper-cascor": ("core.hooksPath", str(self.tmp / "hooks")),
            "juniper-cascor-worker": ("core.fsmonitor", str(self.tmp / "monitor")),
        }
        for repo, (key, value) in planted.items():
            self.git("-C", str(self.root / repo), "config", "--local", key, value)
        self.git("-C", str(self.root / "juniper-ml"), "config", "--local", "core.hooksPath", str(self.root / "juniper-ml" / ".git" / "hooks"))
        self.git("-C", str(self.root / "juniper-k8s"), "config", "--local", "core.fsmonitor", "true")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        by_id = self.checks(report)
        for repo, (key, _) in planted.items():
            with self.subTest(repo=repo):
                self.assertEqual(by_id[f"repo:{repo}"]["status"], "fail")
                self.assertIn(f"{key.lower()}=", by_id[f"repo:{repo}"]["message"])
                self.assertIn("outranks the include", by_id[f"repo:{repo}"]["message"])
        self.assertEqual(by_id["repo:juniper-ml"]["status"], "pass", by_id["repo:juniper-ml"])
        self.assertEqual(by_id["repo:juniper-k8s"]["status"], "pass", by_id["repo:juniper-k8s"])

    def test_r_s16_a_planted_key_in_a_linked_worktree_fails(self):
        # Round 2, N13: agents work in linked worktrees, whose config.worktree outranks the include.
        self.apply()
        repo = self.root / "juniper-ml"
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "base")
        self.git("-C", str(repo), "config", "--local", "extensions.worktreeConfig", "true")
        worktree = self.tmp / "agent-wt"
        self.git("-C", str(repo), "worktree", "add", "-q", "-b", "agent", str(worktree))
        self.git("-C", str(worktree), "config", "--worktree", "gpg.program", str(self.gpg))
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        ml = self.checks(report)["repo:juniper-ml"]
        self.assertIn(f"in the worktree {worktree}, gpg.program=", ml["message"])
        self.assertIn("--worktree --unset-all gpg.program", ml["remediation"])

    def test_wider_scope_hook_and_include_settings_are_reported(self):
        self.apply()
        self.git("config", "--global", "core.hooksPath", str(self.tmp / "global-hooks"))
        self.git("config", "--global", "--add", "include.path", str(self.tmp / "extra.inc"))
        _, report = self.tool_json("--check")
        message = self.checks(report)["wider-scopes"]["message"]
        self.assertIn("core.hookspath=", message)
        self.assertIn("include.path=", message)
        self.assertNotIn("juniper-signing", message, "our own include is not reported")

    def test_r_s4_d11_keeps_plain_agent_commits_unsigned_and_does_not_mask_the_check(self):
        self.apply()
        code, report = self.tool_json("--check", env=D11_ENV)
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        session = self.checks(report)["session"]
        self.assertIn("GIT_CONFIG_KEY_0=commit.gpgsign, GIT_CONFIG_VALUE_0=false", session["message"])
        repo = self.root / "juniper-ml"
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "agent commit", env=D11_ENV)
        self.assert_unsigned(repo, before)
        self.git("-C", str(repo), "tag", "agent-tag", env=D11_ENV)
        self.assertEqual(len(self.gpg_calls()), before)

    def test_r_s4_where_d11_stops_explicit_signing_still_reaches_gpg(self):
        # Documented boundary (plan §7.2, K12): D11's env does not stop these; the C8 guard and K12 must.
        self.apply()
        repo = self.root / "juniper-ml"
        extra = self.tmp / "sign.inc"
        extra.write_text("[commit]\n\tgpgsign = true\n", encoding="utf-8")
        for argv, env in (
            (["commit", "-S", "--allow-empty", "-q", "-m", "explicit -S"], D11_ENV),
            (["-c", f"include.path={extra}", "commit", "--allow-empty", "-q", "-m", "include.path"], D11_ENV),
            (["--config-env=commit.gpgsign=SIGN", "commit", "--allow-empty", "-q", "-m", "config-env"], dict(D11_ENV, SIGN="true")),
        ):
            with self.subTest(argv=argv[:2]):
                before = len(self.gpg_calls())
                self.git("-C", str(repo), *argv, env=env)
                self.assert_signed(repo, before)

    def test_a_global_layout_passes_and_a_relative_program_fails_by_design(self):
        # yamaguchi keeps the values in its global config; the repo checks judge effective values.
        for key, value in (("user.signingkey", KEY), ("commit.gpgsign", "true"), ("tag.gpgsign", "true"), ("gpg.program", str(self.gpg))):
            self.git("config", "--global", key, value)
        code, report = self.tool_json("--check")
        self.assertEqual(code, 0, json.dumps(report, indent=1))
        self.assertEqual(self.checks(report)["include"]["status"], "info")
        self.git("config", "--global", "gpg.program", "gpg2")
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertIn("'gpg2' is not an absolute path", self.checks(report)["repo:juniper-ml"]["message"])

    def test_environment_redirects_are_reported(self):
        self.apply()
        _, report = self.tool_json("--check", env={"XDG_CONFIG_HOME": str(self.home / ".config")})
        message = self.checks(report)["environment"]["message"]
        self.assertIn("GIT_CONFIG_NOSYSTEM=1", message)
        self.assertIn("XDG_CONFIG_HOME=", message)


# ------------------------------------------------------------------------------- include file (R-S17)


class IncludeIntegrityTest(SigningHarness):
    def test_r_s17_a_missing_include_fails_and_commits_then_land_unsigned(self):
        self.apply()
        self.include.unlink()
        code, report = self.tool_json("--check")
        self.assertEqual(code, 1)
        self.assertEqual(self.checks(report)["include"]["status"], "fail", "the include check itself must fail, not only the repo checks")
        self.assertIn("git skips a missing include silently", self.checks(report)["include"]["message"])
        repo = self.root / "juniper-ml"
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "fails open")
        self.assert_unsigned(repo, before)

    def test_r_s17_a_symlinked_or_writable_include_or_directory_fails(self):
        self.apply()
        real = self.tmp / "elsewhere.inc"
        shutil.copy2(self.include, real)
        self.include.unlink()
        self.include.symlink_to(real)
        for setup, needle in (
            (lambda: None, "is a symlink"),
            (lambda: (self.include.unlink(), shutil.copy2(real, self.include), self.include.chmod(0o664)), "writable by group or others"),
            (lambda: (self.include.chmod(0o644), self.include.parent.chmod(0o777)), "the directory"),
        ):
            with self.subTest(needle=needle):
                setup()
                code, report = self.tool_json("--check")
                self.assertEqual((code, self.checks(report)["include"]["status"]), (1, "fail"))
                self.assertIn(needle, self.checks(report)["include"]["message"])
        self.include.parent.chmod(0o700)

    def test_r_s19_an_unmanaged_key_in_the_include_fails(self):
        self.apply()
        self.git("config", "--file", str(self.include), "core.sshCommand", "ssh -i /tmp/key")
        code, report = self.tool_json("--check")
        self.assertEqual((code, self.checks(report)["include"]["status"]), (1, "fail"))
        self.assertIn("core.sshcommand, beyond the four signing keys", self.checks(report)["include"]["message"])


# ------------------------------------------------------------------------------------------ end to end


class EndToEndTest(SigningHarness):
    def test_r_s10_terminal_and_ide_commits_sign_with_the_pinned_key(self):
        self.apply()
        repo = self.root / "juniper-ml"
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "terminal commit")
        self.assert_signed(repo, before)
        # The IDEs' exact argv (vscode.git dist/main.js): no -S unless git.enableCommitSigning is true.
        for extra in ([], ["-S"]):
            with self.subTest(extra=extra):
                before = len(self.gpg_calls())
                self.git("-C", str(repo), "-c", "user.useConfigOnly=true", "commit", "--quiet", "--allow-empty-message", "--file", "-", *extra, "--allow-empty", stdin="ide commit\n")
                self.assert_signed(repo, before)

    def test_cursor_injected_config_still_signs_but_an_inherited_d11_env_does_not(self):
        self.apply()
        repo = self.root / "juniper-ml"
        cursor = {"GIT_CONFIG_COUNT": str(len(CURSOR_KEYS))}
        for i, (key, value) in enumerate(CURSOR_KEYS):
            cursor.update({f"GIT_CONFIG_KEY_{i}": key, f"GIT_CONFIG_VALUE_{i}": value})
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "-c", "user.useConfigOnly=true", "commit", "--quiet", "--allow-empty-message", "--file", "-", "--allow-empty", stdin="cursor commit\n", env=cursor)
        self.assert_signed(repo, before)
        # An IDE started from a Claude Code shell keeps D11's keys and appends its own (plan §7.3).
        inherited = dict(D11_ENV, GIT_CONFIG_COUNT=str(2 + len(CURSOR_KEYS)))
        for i, (key, value) in enumerate(CURSOR_KEYS, start=2):
            inherited.update({f"GIT_CONFIG_KEY_{i}": key, f"GIT_CONFIG_VALUE_{i}": value})
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "-c", "user.useConfigOnly=true", "commit", "--quiet", "--allow-empty-message", "--file", "-", "--allow-empty", stdin="inherited\n", env=inherited)
        self.assert_unsigned(repo, before)

    def test_merge_cherry_pick_and_annotated_tags_sign_and_a_lightweight_tag_now_needs_a_message(self):
        self.apply()
        repo = self.root / "juniper-ml"
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "base")
        self.git("-C", str(repo), "checkout", "-q", "-b", "side")
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "side")
        side = self.git("-C", str(repo), "rev-parse", "HEAD").stdout.strip()
        self.git("-C", str(repo), "checkout", "-q", "main")
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "main")
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "merge", "-q", "--no-edit", "side")
        self.assert_signed(repo, before)
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "cherry-pick", "--allow-empty", "--keep-redundant-commits", side)
        self.assert_signed(repo, before)
        before = len(self.gpg_calls())
        self.git("-C", str(repo), "tag", "-m", "probe tag", "v0-probe")
        self.assertIn("-----BEGIN PGP SIGNATURE-----", self.git("-C", str(repo), "cat-file", "tag", "v0-probe").stdout)
        self.assertEqual(len(self.gpg_calls()) - before, 1)
        lightweight = self.git("-C", str(repo), "tag", "v0-light", env={"GIT_EDITOR": "true"}, check=False)
        self.assertNotEqual(lightweight.returncode, 0, "tag.gpgsign turns a lightweight tag into a signed annotated one (plan S4)")
        self.assertIn("no tag message", lightweight.stderr)

    def test_r_s11_a_linked_worktree_outside_the_root_signs(self):
        self.apply()
        repo = self.root / "juniper-ml"
        self.git("-C", str(repo), "commit", "--allow-empty", "-q", "-m", "base")
        worktree = self.tmp / "elsewhere" / "wt"
        self.git("-C", str(repo), "worktree", "add", "-q", "-b", "wt-branch", str(worktree))
        before = len(self.gpg_calls())
        self.git("-C", str(worktree), "commit", "--allow-empty", "-q", "-m", "worktree commit")
        self.assert_signed(worktree, before)

    def test_r_s12_a_repo_outside_the_root_is_untouched(self):
        self.apply()
        outside = self.tmp / "elsewhere" / "other"
        self.git("init", "-q", str(outside))
        self.assertEqual(self.git("-C", str(outside), "config", "--get", "commit.gpgsign", check=False).returncode, 1)
        before = len(self.gpg_calls())
        self.git("-C", str(outside), "commit", "--allow-empty", "-q", "-m", "outside commit")
        self.assert_unsigned(outside, before)

    def test_executable_hooks_are_listed_with_their_digest(self):
        self.apply()
        hook = self.root / "juniper-data" / ".git" / "hooks" / "post-commit"
        hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hook.chmod(0o755)
        _, report = self.tool_json("--check")
        message = self.checks(report)["hooks:juniper-data"]["message"]
        self.assertIn("post-commit " + hashlib.sha256(hook.read_bytes()).hexdigest()[:12], message)
        self.assertNotIn("hooks:juniper-ml", self.checks(report), "sample hooks are not listed")


# --------------------------------------------------------------------------------------- IDE settings


class IdeSettingsTest(SigningHarness):
    def write_json(self, path: Path, text: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def ide(self, *files: Path) -> dict:
        # The fixtures may fail the post-apply checks on purpose, so --apply may exit 1 here.
        code, report = self.tool_json("--apply", "--gpg-program", str(self.gpg))
        self.assertIn(code, (0, 1))
        self.assertTrue(all(w["applied"] for w in report["writes"]))
        args = []
        for f in files:
            args += ["--ide-settings", str(f)]
        _, report = self.tool_json("--check", *args)
        return self.checks(report)

    def test_r_s5_injected_variables_fail_null_unsets_and_jsonc_parses(self):
        user = self.home / "Library" / "Application Support" / "Cursor" / "User"
        bad = self.write_json(user / "settings.json", json.dumps({"terminal.integrated.env.osx": {"GIT_CONFIG_COUNT": "1", "PATH": "/x"}, "terminal.integrated.env.linux": {"GNUPGHOME": None}}))
        profiles = self.write_json(self.tmp / "Profiles" / "User" / "settings.json", json.dumps({"terminal.integrated.profiles.osx": {"bash": {"path": "bash", "env": {"HOME": "/elsewhere"}}}, "chat.tools.terminal.terminalProfile.linux": {"path": "sh", "env": {"GIT_CONFIG_GLOBAL": "/dev/null"}}}))
        jsonc = self.write_json(
            self.tmp / "Code" / "User" / "settings.json",
            '{\n  // a comment, with a "quote" in it\n  "workbench.startupEditor": "none", /* block, */\n' '  "http.proxy": "http://example.invalid//not-a-comment",\n  "files.exclude": {"/* not a comment */": true},\n' '  "terminal.integrated.env.linux": {"GNUPGHOME": null},\n  "git.enableCommitSigning": true,\n}\n',
        )
        by_id = self.ide(bad, profiles, jsonc)
        self.assertEqual(by_id["ide:Cursor"]["status"], "fail")
        self.assertIn("injects GIT_CONFIG_COUNT", by_id["ide:Cursor"]["message"])
        self.assertNotIn("GNUPGHOME", by_id["ide:Cursor"]["message"], "a null value unsets the variable")
        self.assertIn("profiles.osx.bash.env injects HOME", by_id["ide:Profiles"]["message"])
        self.assertIn("terminalProfile.linux.env injects GIT_CONFIG_GLOBAL", by_id["ide:Profiles"]["message"])
        self.assertEqual(by_id["ide:Code"]["status"], "pass", by_id["ide:Code"])
        self.assertIn("passes -S on every commit", by_id["ide:Code"]["message"])

    def test_r_s5_unparseable_files_dead_git_paths_and_global_auto_approve_fail(self):
        broken = self.write_json(self.tmp / "broken" / "User" / "settings.json", '{"git.path": ')
        dead = self.write_json(self.tmp / "dead" / "User" / "settings.json", json.dumps({"git.path": [str(self.tmp / "no-git"), str(self.tmp / "no-git-2")]}))
        live = self.write_json(self.tmp / "live" / "User" / "settings.json", json.dumps({"git.path": [str(self.tmp / "no-git"), shutil.which("git")]}))
        yolo = self.write_json(self.tmp / "yolo" / "User" / "settings.json", json.dumps({"chat.tools.global.autoApprove": True}))
        self.write_json(self.root / "Juniper.code-workspace", json.dumps({"folders": [{"path": "."}], "settings": {"git.path": str(self.tmp / "no-git")}}))
        by_id = self.ide(broken, dead, live, yolo)
        self.assertIn("cannot be parsed", by_id["ide:broken"]["message"])
        self.assertIn("git.path names no executable", by_id["ide:dead"]["message"])
        self.assertEqual(by_id["ide:live"]["status"], "pass")
        self.assertIn("chat.tools.global.autoApprove is on", by_id["ide:yolo"]["message"])
        self.assertEqual(by_id["ide:Juniper.code-workspace"]["status"], "pass", "git.path is machine-scoped: an IDE ignores it in a workspace file")

    def test_r_s5_workspace_root_and_folder_settings_are_scanned(self):
        self.write_json(self.root / "Juniper.code-workspace", '{\n\t"folders": [{"path": "."}],\n\t"settings": {"terminal.integrated.env.linux": {"GNUPGHOME": "/tmp/x"}},\n}\n')
        self.write_json(self.root / ".vscode" / "settings.json", json.dumps({"cSpell.words": ["juniper"]}))
        self.write_json(self.root / "juniper-cascor" / ".vscode" / "settings.json", json.dumps({"editor.rulers": [512]}))
        empty = self.write_json(self.tmp / "none" / "User" / "settings.json", "{}")
        by_id = self.ide(empty)
        self.assertEqual(by_id["ide:Juniper.code-workspace"]["status"], "fail")
        self.assertIn("injects GNUPGHOME", by_id["ide:Juniper.code-workspace"]["message"])
        self.assertEqual(by_id["ide:root/.vscode"]["status"], "pass")
        self.assertEqual(by_id["ide:juniper-cascor/.vscode"]["status"], "pass")

    def test_default_user_locations_on_both_platforms_and_profiles(self):
        self.write_json(self.home / "Library" / "Application Support" / "Cursor" / "User" / "settings.json", "{}")
        self.write_json(self.home / ".config" / "Code" / "User" / "settings.json", "{}")
        self.write_json(self.home / ".config" / "Code" / "User" / "profiles" / "abc123" / "settings.json", json.dumps({"terminal.integrated.env.linux": {"GIT_CONFIG_PARAMETERS": "x"}}))
        self.tool_json("--apply", "--gpg-program", str(self.gpg))
        _, report = self.tool_json("--check")
        by_id = self.checks(report)
        self.assertEqual(by_id["ide:Cursor"]["status"], "pass")
        self.assertEqual(by_id["ide:Code"]["status"], "pass")
        self.assertEqual(by_id["ide:Code profile abc123"]["status"], "fail")
        self.assertIn("Cursor keeps its agent run mode outside settings.json", by_id["agents:Cursor"]["message"])

    def test_r_s14_vs_code_auto_approval_is_evaluated_deny_first(self):
        cases = {
            "allowall": ({"chat.tools.terminal.autoApprove": {"/.*/": True}}, ["a plain 'git commit -m probe' runs unprompted", "17 of 17 bypass spellings run unprompted", "catch-all allow rule '/.*/'"]),
            # The interim deny pair beside /.*/ still lets an alias, an autocorrected typo and gpg.<format>.program, hooksPath and fsmonitor writes through (round 2, N2).
            "pair": ({"chat.tools.terminal.autoApprove": {"/.*/": True, **S7_DENY_PAIR}}, ["a plain 'git commit -m probe' needs approval", "5 of 17 bypass spellings run unprompted, e.g. 'git -c alias.c=commit c --no-gpg -m probe'", "catch-all allow rule '/.*/'"]),
            "pairfirst": ({"chat.tools.terminal.autoApprove": {**S7_DENY_PAIR, "/.*/": True}}, ["needs approval", "5 of 17"]),
            "off": ({"chat.tools.terminal.enableAutoApprove": False, "chat.tools.terminal.autoApprove": {"/.*/": True}}, ["needs approval (chat.tools.terminal.enableAutoApprove is false)", "none of 17"]),
            # VS Code turns a pattern that matches the empty string into never-match: this deny protects nothing (round 2, N3).
            "emptymatch": ({"chat.tools.terminal.autoApprove": {"/--no-gpg-sign|gpgsign|/i": False, "/.*/": True}}, ["a plain 'git commit -m probe' runs unprompted", "17 of 17 bypass spellings run unprompted"]),
            "legacy": ({"chat.agent.terminal.autoApprove": {"/.*/": True}}, ["runs unprompted (allow rule '/.*/')"]),
            "object": ({"chat.tools.terminal.autoApprove": {"git commit": {"approve": False, "matchCommandLine": True}, "/.*/": True}}, ["a plain 'git commit -m probe' needs approval (deny rule 'git commit')"]),
            "prefix": ({"chat.tools.terminal.autoApprove": {"git": True}}, ["a plain 'git commit -m probe' runs unprompted (allow rule 'git')"]),
            "noprefix": ({"chat.tools.terminal.autoApprove": {"gitk": True}}, ["a plain 'git commit -m probe' needs approval (no rule matches)"]),
            "named": ({"chat.tools.terminal.autoApprove": {"/^(?<cmd>git) commit/": True}}, ["a plain 'git commit -m probe' runs unprompted"]),
            "jsonly": ({"chat.tools.terminal.autoApprove": {"/git/v": True}}, ["cannot be evaluated"]),
            "casesensitive": ({"chat.tools.terminal.autoApprove": {"/^GIT commit/": True}}, ["a plain 'git commit -m probe' needs approval", "1 of 17 bypass spellings run unprompted, e.g. 'GIT commit"]),
        }
        files = [self.write_json(self.tmp / name / "User" / "settings.json", json.dumps(settings)) for name, (settings, _) in cases.items()]
        by_id = self.ide(*files)
        for name, (_, needles) in cases.items():
            with self.subTest(case=name):
                message = by_id[f"agents:{name}"]["message"]
                self.assertEqual(by_id[f"agents:{name}"]["status"], "info")
                for needle in needles:
                    self.assertIn(needle, message)

    def test_r_s14_amp_permissions_first_match_wins(self):
        cases = {
            "ampask": ([{"tool": "Bash", "matches": {"cmd": ["*git*commit*", "*gpg.program*"]}, "action": "ask"}, {"tool": "Bash", "action": "allow"}], "a plain 'git commit -m probe' needs approval (rule 1: Bash ask)"),
            "ampall": ([{"tool": "Bash", "matches": {"cmd": "*git*push*"}, "action": "ask"}, {"tool": "Read", "action": "allow"}, {"tool": "Bash", "action": "allow"}], "a plain 'git commit -m probe' runs unprompted (rule 3: Bash allow)"),
            "ampcatchall": ([{"tool": "Bash", "action": "allow"}], "catch-all Bash allow rule 1"),
            "ampnone": ([{"tool": "Read", "action": "allow"}], "Amp's bundled defaults decide"),
        }
        files = [self.write_json(self.tmp / name / "User" / "settings.json", json.dumps({"amp.permissions": rules})) for name, (rules, _) in cases.items()]
        by_id = self.ide(*files)
        for name, (_, needle) in cases.items():
            with self.subTest(case=name):
                self.assertIn(needle, by_id[f"agents:{name} amp"]["message"])


# ----------------------------------------------------------------------------------------- contract


class ContractTest(SigningHarness):
    def audited(self, *args: str) -> tuple[int, dict]:
        wrapper = self.tmp / "audit_wrapper.py"
        wrapper.write_text(AUDIT_WRAPPER, encoding="utf-8")
        out = self.tmp / "audit.json"
        # -B: the interpreter's own bytecode-cache writes are not the script's. On a runner whose Python toolcache
        # lacks a module's .pyc, the import writes one (encodings/__pycache__/utf_8_sig...pyc.<id> on 3.12.15,
        # main verification, 2026-10-21), and the audit hook would charge it to the script.
        proc = subprocess.run([sys.executable, "-I", "-B", str(wrapper), str(out), str(SCRIPT_PATH), "--root", str(self.root), *args], env=self.env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)
        return proc.returncode, json.loads(out.read_text(encoding="utf-8"))

    def test_r_s9_never_opens_credentials_never_runs_gpg_and_writes_only_its_files(self):
        settings = self.home / "Library" / "Application Support" / "Code" / "User" / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"chat.tools.terminal.autoApprove": {"/.*/": True}}), encoding="utf-8")
        allowed_writes = {str(self.include), str(self.home / f".gitconfig.bak-{TODAY}-pre-commit-signing")}
        for args, may_write in ((("--apply", "--gpg-program", str(self.gpg)), True), (("--check",), False), (("--apply", "--dry-run", "--gpg-program", str(self.gpg)), False), (("--remove", "--dry-run"), False)):
            with self.subTest(args=args):
                code, log = self.audited(*args)
                self.assertIn(code, (0, 1))
                secret_dirs = (str(self.home / ".gnupg"), str(self.home / ".ssh"))
                self.assertEqual([p for p, _ in log["open"] if os.path.realpath(p).startswith(secret_dirs)], [])
                # subprocess opens /dev/null read-write for stdin, and the wrapper writes its own log.
                written = {os.path.realpath(p) for p, writes in log["open"] if writes} - {os.path.realpath(os.devnull), str(self.tmp / "audit.json")}
                self.assertLessEqual(written, allowed_writes if may_write else set(), written)
                self.assertTrue(log["exec"], "the audit hook saw no process at all, so it proves nothing")
                for executable, argv in log["exec"]:
                    self.assertNotIn(os.path.realpath(executable), (str(self.gpg_real), str(self.gpg)))
                    self.assertFalse(any(".gnupg" in a or ".ssh" in a for a in argv), argv)
        self.assert_tripwire_quiet()

    def test_r_s9_apply_changes_only_its_own_files_and_never_lists_a_credential_directory(self):
        # Round 2, N6/N18: git's own writes are outside the audit hook, so diff the tree as well.
        def snapshot() -> dict:
            out = {}
            for dirpath, dirnames, filenames in os.walk(self.home):
                for name in dirnames + filenames:
                    full = os.path.join(dirpath, name)
                    data = b"" if os.path.isdir(full) else Path(full).read_bytes()
                    out[full] = (os.lstat(full).st_mode, hashlib.sha256(data).hexdigest())
            return out

        before = snapshot()
        code, _ = self.audited("--apply", "--gpg-program", str(self.gpg))
        self.assertEqual(code, 0)
        after = snapshot()
        changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
        expected = {str(self.home / ".config"), str(self.include.parent), str(self.include), str(self.home / ".gitconfig"), str(self.home / f".gitconfig.bak-{TODAY}-pre-commit-signing")}
        self.assertLessEqual(changed, expected, sorted(changed - expected))
        # A hooks path planted inside ~/.ssh fails as planted, and its directory is never listed or read.
        (self.home / ".ssh" / "hooks").mkdir()
        (self.home / ".ssh" / "hooks" / "post-commit").write_text("#!/bin/sh\n", encoding="utf-8")
        self.git("-C", str(self.root / "juniper-data"), "config", "--local", "core.hooksPath", str(self.home / ".ssh" / "hooks"))
        code, log = self.audited("--check")
        self.assertEqual(code, 1)
        secret_dirs = (str(self.home / ".gnupg"), str(self.home / ".ssh"))
        self.assertEqual([p for p, _ in log["open"] if os.path.realpath(p).startswith(secret_dirs)], [])

    def test_r_s13_usage_and_environment_errors_exit_2(self):
        empty = self.home / "Development" / "empty-root"
        empty.mkdir()
        cases = (
            (["--root", str(self.tmp / "absent")], {}, "is not a directory"),
            (["--root", str(empty)], {}, "no active Juniper checkout"),
            ([], {"GIT": str(self.tmp / "no-such-git")}, "git not found"),
            (["--dry-run"], {}, "--dry-run needs --apply or --remove"),
            (["--check", "--apply"], {}, "not allowed with"),
            (["--bogus"], {}, "unrecognized arguments"),
            (["--ide-settings", str(self.tmp / "absent.json")], {}, "does not exist"),
            (["--apply", "--gpg-program", "/bin/sh"], {"COMMIT_SIGNING_TODAY": "today"}, "COMMIT_SIGNING_TODAY must be YYYY-MM-DD"),
        )
        for args, env, message in cases:
            with self.subTest(args=args):
                proc = self.tool(*args, env=env)
                self.assertEqual(proc.returncode, 2, proc.stdout)
                self.assertIn(message, proc.stderr)

    def test_json_schema_and_missing_checkouts(self):
        shutil.rmtree(self.root / "juniper-k8s")
        (self.root / "juniper-legacy").mkdir()
        report = self.apply()
        self.assertEqual(set(report), TOP_KEYS)
        self.assertEqual(report["schema"], 1)
        self.assertEqual(set(report["expected"]), {"signing_key", "gpg_program"})
        for write in report["writes"]:
            self.assertEqual(set(write), WRITE_KEYS)
        for check in report["checks"]:
            self.assertEqual(set(check), CHECK_KEYS)
            self.assertIn(check["status"], ("pass", "fail", "info", "error"))
        self.assertTrue(report["ok"])
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual([c["message"] for c in report["checks"] if c["id"] == "missing"], [f"juniper-k8s: no checkout under {self.root}, nothing to check"])
        self.assertNotIn("repo:juniper-k8s", self.checks(report))

    def test_text_output_lists_each_failure_with_its_fix(self):
        proc = self.tool("--check")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FAIL   repo:juniper-ml", proc.stdout)
        self.assertIn("-- fix: python3 util/configure_commit_signing.py --apply", proc.stdout)
        self.assertIn("RESULT: FAILED -- 10 of 10 checks did not pass", proc.stdout)
        self.assert_tripwire_quiet()

    def test_a_checkout_that_is_not_its_own_repository_is_skipped(self):
        shutil.rmtree(self.root / "juniper-deploy")
        (self.root / "juniper-deploy").mkdir()
        self.apply()
        _, report = self.tool_json("--check")
        self.assertIn("juniper-deploy (not its own git checkout): no checkout", " ".join(c["message"] for c in report["checks"] if c["id"] == "missing"))

    def test_the_script_parses_as_python_3_9(self):
        # turing's /usr/bin/python3 is 3.9.6. The grammar check catches 3.10+ syntax; the future
        # import keeps the PEP 604 annotations unevaluated there.
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        ast.parse(source, filename=str(SCRIPT_PATH), feature_version=(3, 9))
        self.assertIn("from __future__ import annotations", source)

    @unittest.skipUnless(os.access(SYSTEM_PYTHON, os.X_OK), "no /usr/bin/python3 on this host")
    def test_system_python_runs_the_tool(self):
        proc = subprocess.run([SYSTEM_PYTHON, "-I", str(SCRIPT_PATH), "--help"], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.apply()
        proc = subprocess.run([SYSTEM_PYTHON, "-I", str(SCRIPT_PATH), "--root", str(self.root), "--check", "--json"], env=self.env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["ok"])

    def test_flake8_clean_when_available(self):
        if importlib.util.find_spec("flake8") is None:
            self.skipTest("flake8 not installed (util/ is outside the pre-commit Python hooks, so this is the lint gate where it runs)")
        proc = subprocess.run([sys.executable, "-m", "flake8", "--max-line-length=512", "--extend-ignore=E203,W503", str(SCRIPT_PATH)], capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
