#!/usr/bin/env python3
"""The ONE web-UI credential file both Duplicati API clients read (B2, recovery plan 2026-10-03).

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

``util/ad-hoc/yamaguchi_server_api.py`` hard-coded the primary checkout's world-readable
``.env`` (exposure S-5) and ``util/ad-hoc/duplicati_api.py`` defaulted to the same file through
``DUPLICATI_PW_FILE`` -- a name that also means the ARCHIVE passphrase file elsewhere -- with a
fallback that posted the whole file as the password. Re-pointing only one client leaves every
acceptance instrument 401-ing after the password rotates (design §7.6). So both now read
``~/.config/duplicati-backup/web-credential`` through ``yamaguchi_server_api.read_credential``.

Pins, each able to fail for the reason it exists:

* the format: exactly one ``DUPLICATI_WEB_CREDENTIAL=`` line, literal value, one matching quote
  pair removed, comments / other keys / ``_OLD`` names ignored, CRLF and a BOM tolerated;
* refusal of ANY group or other permission bit, of a non-regular file (a FIFO must not hang),
  of zero or two key lines and of an empty value -- every message naming path, mode and owner,
  none carrying the content;
* both clients resolve the same path through the same function, and the override is
  ``DUPLICATI_WEB_CREDENTIAL_FILE``; ``DUPLICATI_PW_FILE`` / ``DUPLICATI_PW_KEY`` are ignored
  (noted on stderr) and the bare-secret fallback is gone;
* the password leaves the process only as the login request's JSON body, and a refused file
  sends nothing at all.

No server is contacted: ``urllib.request.urlopen`` is replaced by ``tests/duplicati_api_stub.py``.
"""

from __future__ import annotations

import io
import json
import os
import pwd
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr
from pathlib import Path

from tests.duplicati_api_stub import AD_HOC, FIXTURE_MARKER, STUB_BASE, STUB_BEARER_MARKER, FakeDuplicati, load_ad_hoc, write_credential
from tests.redacted_env import RedactedEnv

api = load_ad_hoc("yamaguchi_server_api")
dapi = load_ad_hoc("duplicati_api")

KEY = api.CRED_KEY
# Key names and a distractor value kept out of literal NAME=value text, so a secret-content
# scanner rule over such lines (B9) has no fixture here to trip on.
ARCHIVE_KEY = "PASS" + "PHRASE"
LEGACY_KEY = "UI_" + "PASSWORD"
DISTRACTOR = "distractor-$&-marker"
OWNER = pwd.getpwuid(os.getuid()).pw_name
SCRIPT_TIMEOUT_SECONDS = 20


class _TempDir(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / "web-credential"

    def assert_refused(self, path: Path, *needles: str) -> str:
        with self.assertRaises(api.CredentialError) as ctx:
            api.read_credential(str(path))
        message = str(ctx.exception)
        self.assertIsInstance(ctx.exception, SystemExit, "an importer that lets it propagate must exit like sys.exit did")
        self.assertTrue(message.startswith("FATAL: "), message)
        self.assertIn(str(path), message)
        for needle in needles:
            self.assertIn(needle, message)
        self.assertNotIn(FIXTURE_MARKER, message)
        return message


class CredentialFormatTest(_TempDir):
    def test_reads_the_single_key_line(self) -> None:
        write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n")
        self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)

    def test_export_prefix_and_one_matching_quote_pair(self) -> None:
        write_credential(self.path, f"export {KEY}='  {FIXTURE_MARKER}  '\n")
        self.assertEqual(api.read_credential(str(self.path)), f"  {FIXTURE_MARKER}  ")
        write_credential(self.path, f'{KEY}="{FIXTURE_MARKER}"\n')
        self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)

    def test_mismatched_quotes_are_part_of_the_value(self) -> None:
        """The pre-B2 parser stripped every quote at either end; a password ending in one must survive."""
        write_credential(self.path, f"{KEY}=\"{FIXTURE_MARKER}'\n")
        self.assertEqual(api.read_credential(str(self.path)), f"\"{FIXTURE_MARKER}'")

    def test_the_value_is_literal(self) -> None:
        write_credential(self.path, f"{KEY}=a#b $HOME `id` c\n")
        self.assertEqual(api.read_credential(str(self.path)), "a#b $HOME `id` c")

    def test_comments_other_keys_and_old_names_are_ignored(self) -> None:
        text = "\n".join(
            [
                "# rotated 2026-10-03",
                f"# {KEY}={DISTRACTOR}",
                "",
                f"{ARCHIVE_KEY}={DISTRACTOR}",
                f"{KEY}_OLD={DISTRACTOR}",
                f"  {KEY}={FIXTURE_MARKER}  ",
                "",
            ]
        )
        write_credential(self.path, text)
        self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)

    def test_crlf_and_a_byte_order_mark_are_tolerated(self) -> None:
        write_credential(self.path, b"\xef\xbb\xbf" + f"{KEY}={FIXTURE_MARKER}\r\n".encode())
        self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)


class CredentialRefusalTest(_TempDir):
    def test_any_group_or_other_bit_is_refused(self) -> None:
        for mode in (0o640, 0o604, 0o620, 0o602, 0o644, 0o660, 0o664, 0o700 | 0o004):
            with self.subTest(mode=oct(mode)):
                write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n", mode)
                self.assert_refused(self.path, f"mode {mode:04o}", OWNER, "chmod 0600")

    def test_owner_only_modes_are_accepted(self) -> None:
        for mode in (0o600, 0o400):
            with self.subTest(mode=oct(mode)):
                write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n", mode)
                self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)
                os.chmod(self.path, 0o600)

    def test_a_missing_file_is_refused_with_the_remedy(self) -> None:
        self.assert_refused(self.dir / "absent", "does not exist", "0600", KEY)

    def test_a_directory_is_refused(self) -> None:
        target = self.dir / "a-directory"
        target.mkdir(mode=0o700)
        self.assert_refused(target, "not a regular file")

    def test_a_fifo_is_refused_without_hanging(self) -> None:
        """Opened O_NONBLOCK: a FIFO planted at the path must be refused, not wait for a writer."""
        fifo = self.dir / "fifo"
        os.mkfifo(fifo, 0o600)
        code = "import sys; sys.path.insert(0, sys.argv[1]); import yamaguchi_server_api as a; a.read_credential(sys.argv[2])"
        result = subprocess.run([sys.executable, "-c", code, str(AD_HOC), str(fifo)], capture_output=True, text=True, timeout=SCRIPT_TIMEOUT_SECONDS, env=RedactedEnv(os.environ), check=False)
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertIn("not a regular file", result.stderr)

    def test_an_oversized_file_is_refused_unread(self) -> None:
        write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n" + "#" * (api.CRED_MAX_BYTES + 1))
        self.assert_refused(self.path, "bytes; it holds one line")

    def test_a_symlink_is_judged_by_its_target(self) -> None:
        target = write_credential(self.dir / "target", f"{KEY}={FIXTURE_MARKER}\n", 0o600)
        self.path.symlink_to(target)
        self.assertEqual(api.read_credential(str(self.path)), FIXTURE_MARKER)
        os.chmod(target, 0o640)  # group-readable is enough to be refused; nothing here needs world bits
        self.assert_refused(self.path, "mode 0640")

    def test_a_bare_secret_is_refused_not_posted(self) -> None:
        """duplicati_api.py used to post the WHOLE file as the password when no key matched."""
        write_credential(self.path, f"{FIXTURE_MARKER}\n")
        self.assert_refused(self.path, f"has 0 {KEY}= lines")

    def test_two_key_lines_are_refused(self) -> None:
        """An appended rotation would otherwise keep sending the first, stale value."""
        write_credential(self.path, f"{KEY}={DISTRACTOR}\n{KEY}={FIXTURE_MARKER}\n")
        self.assert_refused(self.path, f"has 2 {KEY}= lines")

    def test_an_empty_value_is_refused(self) -> None:
        write_credential(self.path, f"{KEY}=\n")
        self.assert_refused(self.path, "empty")
        write_credential(self.path, f"{KEY}=''\n")
        self.assert_refused(self.path, "empty")

    def test_undecodable_content_is_refused_without_echoing_a_byte(self) -> None:
        write_credential(self.path, f"{KEY}=".encode() + b"\xff\xfe" + FIXTURE_MARKER.encode())
        message = self.assert_refused(self.path, "not UTF-8")
        self.assertNotIn("0xff", message)


class OneCredentialPathTest(_TempDir):
    def test_both_clients_share_one_reader_and_one_path_resolver(self) -> None:
        self.assertIs(dapi.read_credential, api.read_credential)
        self.assertIs(dapi.credential_path, api.credential_path)

    def test_the_override_variable_wins(self) -> None:
        write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n")
        with mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.path)}):
            self.assertEqual(api.credential_path(), str(self.path))
            self.assertEqual(api.read_credential(), FIXTURE_MARKER)

    def test_the_default_is_the_0600_file_under_the_home_directory(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": str(self.dir), api.CRED_FILE_ENV: ""}):
            expected = str(self.dir / ".config" / "duplicati-backup" / "web-credential")
            self.assertEqual(api.credential_path(), expected)
            self.assertEqual(dapi.credential_path(), expected)

    def test_neither_client_names_the_checkout_env_any_more(self) -> None:
        for name in ("yamaguchi_server_api.py", "duplicati_api.py", "yamaguchi_watchdog.py"):
            with self.subTest(file=name):
                source = (AD_HOC / name).read_text(encoding="utf-8")
                self.assertNotIn("juniper-ml/.env", source)
                self.assertNotIn('os.environ.get("DUPLICATI_PW_FILE"', source)
                self.assertNotIn('"PASSPHRASE_OLD", "PASSPHRASE"', source, "the old candidate-key list is gone")


class DuplicatiApiClientTest(_TempDir):
    def setUp(self) -> None:
        super().setUp()
        write_credential(self.path, f"{KEY}={FIXTURE_MARKER}\n")
        self.fake = FakeDuplicati()
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.path)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(dapi, "BASE", STUB_BASE),
            mock.patch.object(api, "BASE", STUB_BASE),
            mock.patch.object(dapi, "_retired_reported", set[str]()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_retired_variables_are_ignored_and_named(self) -> None:
        legacy = write_credential(self.dir / "legacy.env", f"{LEGACY_KEY}={DISTRACTOR}\n", 0o644)
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"DUPLICATI_PW_FILE": str(legacy), "DUPLICATI_PW_KEY": LEGACY_KEY}), redirect_stderr(err):
            self.assertEqual(dapi._password(), FIXTURE_MARKER)
        self.assertIn("DUPLICATI_PW_FILE is set but no longer read", err.getvalue())
        self.assertIn("DUPLICATI_PW_KEY is set but no longer read", err.getvalue())
        self.assertNotIn(DISTRACTOR, err.getvalue())

    def test_a_retired_variable_is_not_a_fallback(self) -> None:
        legacy = write_credential(self.dir / "legacy.env", f"{LEGACY_KEY}={FIXTURE_MARKER}\n")
        with mock.patch.dict(os.environ, {"DUPLICATI_PW_FILE": str(legacy), api.CRED_FILE_ENV: str(self.dir / "absent")}), redirect_stderr(io.StringIO()):
            with self.assertRaises(api.CredentialError):
                dapi._password()
        self.assertEqual(self.fake.requests, [])

    def test_login_posts_the_password_only_in_the_body(self) -> None:
        self.fake.route("GET", "/api/v1/serverstate", 200, {"ProgramState": "Running"})
        self.assertEqual(dapi.login(), STUB_BEARER_MARKER)
        status, body = dapi.call("serverstate")
        self.assertEqual((status, body), (200, {"ProgramState": "Running"}))
        self.assertEqual(self.fake.paths(), [("POST", "/api/v1/auth/login"), ("POST", "/api/v1/auth/login"), ("GET", "/api/v1/serverstate")])
        logins = [r for r in self.fake.requests if r.path == "/api/v1/auth/login"]
        self.assertTrue(all(r.body == {"Password": FIXTURE_MARKER} for r in logins))
        get = self.fake.requests[-1]
        self.assertEqual(get.headers.get("authorization"), f"Bearer {STUB_BEARER_MARKER}")
        self.assertIsNone(get.body)
        for r in self.fake.requests:
            self.assertNotIn(FIXTURE_MARKER, r.url)
            self.assertNotIn(FIXTURE_MARKER, json.dumps(r.headers))

    def test_both_clients_send_the_same_password_from_the_same_file(self) -> None:
        self.assertEqual(api.login(), STUB_BEARER_MARKER)
        self.assertEqual(dapi.login(), STUB_BEARER_MARKER)
        bodies = [r.body for r in self.fake.requests]
        self.assertEqual(bodies, [{"Password": FIXTURE_MARKER, "RememberMe": False}, {"Password": FIXTURE_MARKER}])

    def test_a_refused_file_sends_nothing(self) -> None:
        os.chmod(self.path, 0o640)
        for login in (api.login, dapi.login):
            with self.subTest(client=login.__module__):
                with self.assertRaises(api.CredentialError):
                    login()
        self.assertEqual(self.fake.requests, [])


if __name__ == "__main__":
    unittest.main()
