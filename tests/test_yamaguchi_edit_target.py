#!/usr/bin/env python3
"""``util/ad-hoc/yamaguchi_edit_target.py``: the passphrase-safe TargetURL repoint.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Migration step 3 is the one edit that can present every remote volume as missing: a PUT of a
new ``TargetURL`` against a populated local job DB. The script shipped with no tests. These
pin the refusals that must happen before that PUT, and the read-back that must happen after.

* a task or a non-empty queue is rc 3, and an empty queue is not;
* the same path, a path that is not a directory, an unmounted path, fewer volumes, or a
  different byte total is rc 4; ``--allow-shrink`` is the only way past the census, and it
  does not itself send the PUT;
* a mount with no fstab entry is rc 7, and ``--allow-non-durable`` does not skip the census;
* zero or two ``passphrase`` settings, the 15-character mask, or the wrong fingerprint is
  rc 5, before any PUT, and the secret is never printed;
* ``--dry-run`` substitutes the real passphrase in memory and sends nothing;
* a rejected PUT is rc 1; a read-back that moved a source, or that returned the real
  passphrase instead of the mask, is rc 6; a clean read-back is rc 0 and the PUT carried
  the real passphrase, not the mask.

No server is contacted: ``urllib.request.urlopen`` is ``tests/duplicati_api_stub.py``.
``mountpoint`` and ``findmnt`` are not executed.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tests.duplicati_api_stub import FIXTURE_MARKER, STUB_BASE, FakeDuplicati, load_ad_hoc, write_credential

edit = load_ad_hoc("yamaguchi_edit_target")
api = edit.api

BACKUP_ID = "7"
# Distinct from the web-UI fixture so a leak of either secret is visible.
PASSPHRASE = "fixture-archive-passphrase-Q7"
MASK = "*" * 15


def _fingerprint(value: str) -> str:
    """Stand-in for the 200k-round PBKDF2. Only the real passphrase matches the recorded prefix."""
    if value == PASSPHRASE:
        return edit.EXPECTED_FINGERPRINT_PREFIX + "abcd"
    return "0000000000000000"


class PureHelpersTest(unittest.TestCase):
    def test_local_path_is_a_file_url_or_nothing(self) -> None:
        self.assertIsNone(edit.local_path(None))
        self.assertIsNone(edit.local_path(""))
        self.assertIsNone(edit.local_path("file://"))
        self.assertIsNone(edit.local_path("s3://bucket/yamaguchi"))
        self.assertEqual(edit.local_path("file:///mnt/Backups/Yamaguchi"), "/mnt/Backups/Yamaguchi")
        self.assertEqual(edit.local_path("file:///mnt/My%20Dest"), "/mnt/My Dest")

    def test_census_counts_only_direct_duplicati_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "duplicati-a.dblock.zip").write_bytes(b"x" * 10)
            (root / "duplicati-b.dblock.zip").write_bytes(b"y" * 4)
            (root / "notes.txt").write_bytes(b"ignore-me")
            nested = root / "duplicati-looks-like-a-dir"
            nested.mkdir()
            (nested / "duplicati-nested").write_bytes(b"zzzz")
            self.assertEqual(edit.census(root), (2, 14))

    def test_setting_value_requires_exactly_one(self) -> None:
        one = [{"Name": "encryption-module", "Value": "aes"}]
        self.assertEqual(edit.setting_value(one, "encryption-module"), "aes")
        self.assertIsNone(edit.setting_value([], "encryption-module"))
        two = one + [{"Name": "encryption-module", "Value": "none"}]
        self.assertIsNone(edit.setting_value(two, "encryption-module"))

    def test_settings_summary_redacts_any_passphrase_name(self) -> None:
        text = edit.settings_summary(
            [
                {"Name": "passphrase", "Value": PASSPHRASE},
                {"Name": "Passphrase-old", "Value": PASSPHRASE + "-old"},
                {"Name": "encryption-module", "Value": "aes"},
            ]
        )
        self.assertNotIn(PASSPHRASE, text)
        self.assertIn("passphrase=<redacted>", text)
        self.assertIn("Passphrase-old=<redacted>", text)
        self.assertIn("encryption-module=aes", text)

    def test_read_passphrase_strips_quotes_and_refuses_a_missing_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "env"
            env.write_text("PASSPHRASE=\nexport PASSPHRASE='quoted secret'\n", encoding="utf-8")
            with mock.patch.object(edit, "ENV_FILE", str(env)):
                self.assertEqual(edit.read_passphrase("PASSPHRASE"), "quoted secret")
                with self.assertRaises(SystemExit) as ctx:
                    edit.read_passphrase("PASSPHRASE_OLD")
            self.assertIn("PASSPHRASE_OLD", str(ctx.exception))
            self.assertNotIn("quoted secret", str(ctx.exception))

    def test_fingerprint_is_a_stable_prefix_and_not_the_secret(self) -> None:
        first = edit.fingerprint(PASSPHRASE)
        self.assertEqual(first, edit.fingerprint(PASSPHRASE))
        self.assertEqual(len(first), 16)
        self.assertNotIn(PASSPHRASE, first)
        self.assertNotEqual(first, edit.fingerprint(PASSPHRASE + "x"))
        int(first, 16)


class _Drive(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.old = self.dir / "old"
        self.new = self.dir / "new"
        self.cred = write_credential(self.dir / "web-credential", f"{api.CRED_KEY}={FIXTURE_MARKER}\n")
        self.env_file = self.dir / "archive-env"
        self.env_file.write_text(f"PASSPHRASE={PASSPHRASE}\n", encoding="utf-8")
        self.fake = FakeDuplicati()
        self._mount = "/mnt/durable"
        self._mounted = True
        self._fstab = True
        for patcher in (
            mock.patch.dict(os.environ, {api.CRED_FILE_ENV: str(self.cred)}),
            mock.patch("urllib.request.urlopen", self.fake.urlopen),
            mock.patch.object(api, "BASE", STUB_BASE),
            mock.patch.object(edit, "ENV_FILE", str(self.env_file)),
            mock.patch.object(edit, "fingerprint", _fingerprint),
            mock.patch.object(edit, "mount_point_of", lambda _path: self._mount),
            mock.patch.object(edit, "is_mounted", lambda _path: self._mounted),
            mock.patch.object(edit, "in_fstab", lambda _path: self._fstab),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def volumes(self, path: Path, sizes: list[int]) -> None:
        path.mkdir(parents=True, exist_ok=True)
        for index, size in enumerate(sizes):
            (path / f"duplicati-{index}.dblock.zip").write_bytes(b"v" * size)

    def route_state(self, active: object = None, queue: list | None = None) -> None:
        self.fake.route(
            "GET",
            "/api/v1/serverstate",
            200,
            {
                "ProgramState": "Running",
                "ActiveTask": active,
                "SchedulerQueueIds": [] if queue is None else queue,
                "ProposedSchedule": [{"Item1": "7", "Item2": "2026-10-04T04:00:00Z"}],
            },
        )

    def route_job(self, target: str, settings: list | None = None, *, sources: list | None = None, after: dict | None = None) -> None:
        if settings is None:
            settings = [
                {"Name": "passphrase", "Value": MASK},
                {"Name": "encryption-module", "Value": "aes"},
            ]
        first = {
            "Backup": {
                "ID": BACKUP_ID,
                "Name": "Yamaguchi",
                "TargetURL": target,
                "Sources": ["/data"] if sources is None else sources,
                "Filters": [],
                "Settings": settings,
            },
            "Schedule": {"Time": "04:00", "Repeat": "1D", "LastRun": "2026-10-01T04:00:00Z"},
        }
        seen = {"n": 0}

        def handler(_query: dict) -> tuple[int, dict]:
            seen["n"] += 1
            if after is not None and seen["n"] > 1:
                return 200, after
            return 200, first

        self.fake.route("GET", f"/api/v1/backup/{BACKUP_ID}", handler=handler)

    def invoke(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["yamaguchi_edit_target.py", "--backup-id", BACKUP_ID, *argv]):
            with redirect_stdout(out), redirect_stderr(err):
                try:
                    edit.main()
                    rc = 0
                except SystemExit as exc:
                    if isinstance(exc.code, str):
                        err.write(exc.code + "\n")
                        rc = 1
                    else:
                        rc = 0 if exc.code is None else int(exc.code)
        text = out.getvalue() + err.getvalue()
        self.assertNotIn(FIXTURE_MARKER, text, "the web password must never be printed")
        self.assertNotIn(PASSPHRASE, text, "the archive passphrase must never be printed")
        return rc, out.getvalue(), err.getvalue()

    def puts(self) -> list:
        return [recorded for recorded in self.fake.requests if recorded.method == "PUT"]


class RefusalTest(_Drive):
    def test_a_busy_scheduler_exits_3_and_sends_no_put(self) -> None:
        cases = (
            {"Item1": 4, "Item2": BACKUP_ID},
            None,
        )
        queues = (None, [BACKUP_ID])
        # Active task alone, and a queue alone. An empty queue is the negative control below.
        for active, queue in ((cases[0], None), (None, queues[1])):
            with self.subTest(active=active, queue=queue):
                self.fake.requests.clear()
                self.route_state(active=active, queue=queue)
                rc, _, err = self.invoke("--new-target", str(self.new), "--dry-run")
                self.assertEqual(rc, 3)
                self.assertIn("rc 3", err)
                self.assertEqual(self.puts(), [])
                self.assertNotIn(("GET", f"/api/v1/backup/{BACKUP_ID}"), self.fake.paths())

    def test_an_empty_queue_is_not_busy(self) -> None:
        target = "file://" + os.path.abspath(self.new)
        self.route_state(active=None, queue=[])
        self.route_job(target)
        rc, _, err = self.invoke("--new-target", str(self.new), "--dry-run")
        self.assertEqual(rc, 4)
        self.assertIn("equals the current one", err)
        self.assertEqual(self.puts(), [])

    def test_a_path_that_is_not_a_directory_exits_4(self) -> None:
        self.new.write_text("not a directory", encoding="utf-8")
        self.route_state()
        self.route_job("file:///somewhere/else")
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 4)
        self.assertIn("not an existing directory", err)
        self.assertEqual(self.puts(), [])

    def test_an_unmounted_target_exits_4(self) -> None:
        self.new.mkdir()
        self._mounted = False
        self.route_state()
        self.route_job("file:///somewhere/else")
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 4)
        self.assertIn("not on a mounted filesystem", err)
        self.assertEqual(self.puts(), [])

    def test_fewer_volumes_and_a_different_byte_total_each_exit_4(self) -> None:
        self.volumes(self.old, [10, 10])
        self.route_state()
        self.route_job("file://" + str(self.old))
        self.volumes(self.new, [20])
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 4)
        self.assertIn("FEWER volumes", err)
        self.assertEqual(self.puts(), [])

        self.fake.requests.clear()
        self.new.joinpath("duplicati-0.dblock.zip").unlink()
        self.volumes(self.new, [10, 11])
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 4)
        self.assertIn("byte totals differ", err)
        self.assertEqual(self.puts(), [])

    def test_allow_shrink_still_does_not_put_on_a_dry_run(self) -> None:
        self.volumes(self.old, [10, 10])
        self.volumes(self.new, [20])
        self.route_state()
        self.route_job("file://" + str(self.old))
        rc, out, _ = self.invoke("--new-target", str(self.new), "--allow-shrink", "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("DRY RUN", out)
        self.assertEqual(self.puts(), [])

    def test_no_fstab_entry_exits_7_and_the_override_does_not_skip_the_census(self) -> None:
        self.new.mkdir()
        self._fstab = False
        self.route_state()
        self.route_job("s3://bucket/yamaguchi")
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 7)
        self.assertIn("no /etc/fstab entry", err)
        self.assertEqual(self.puts(), [])

        self.fake.requests.clear()
        rc, _, err = self.invoke("--new-target", str(self.new), "--allow-non-durable")
        self.assertEqual(rc, 4)
        self.assertIn("WARNING", err)
        self.assertIn("no duplicati-* volumes", err)
        self.assertEqual(self.puts(), [])

    def test_passphrase_guards_exit_5_before_any_put(self) -> None:
        self.volumes(self.old, [10])
        self.volumes(self.new, [10])
        old_url = "file://" + str(self.old)
        self.route_state()

        self.route_job(old_url, settings=[{"Name": "encryption-module", "Value": "aes"}])
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 5)
        self.assertIn("exactly one passphrase", err)
        self.assertEqual(self.puts(), [])

        self.fake.requests.clear()
        self.route_job(
            old_url,
            settings=[
                {"Name": "passphrase", "Value": MASK},
                {"Name": "passphrase", "Value": MASK},
                {"Name": "encryption-module", "Value": "aes"},
            ],
        )
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 5)
        self.assertEqual(self.puts(), [])

        self.fake.requests.clear()
        self.env_file.write_text(f"PASSPHRASE={MASK}\n", encoding="utf-8")
        self.route_job(old_url)
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 5)
        self.assertIn("mask", err)
        self.assertEqual(self.puts(), [])

        self.fake.requests.clear()
        self.env_file.write_text("PASSPHRASE=the-wrong-archive-secret\n", encoding="utf-8")
        rc, _, err = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 5)
        self.assertIn("fingerprint", err)
        self.assertNotIn("the-wrong-archive-secret", err)
        self.assertEqual(self.puts(), [])


class PutAndReadBackTest(_Drive):
    def _ready(self, after: dict | None = None) -> str:
        self.volumes(self.old, [10, 10])
        self.volumes(self.new, [10, 10])
        old_url = "file://" + str(self.old)
        self.route_state()
        new_url = "file://" + str(self.new)
        if after is None:
            after = {
                "Backup": {
                    "ID": BACKUP_ID,
                    "Name": "Yamaguchi",
                    "TargetURL": new_url,
                    "Sources": ["/data"],
                    "Filters": [],
                    "Settings": [
                        {"Name": "passphrase", "Value": MASK},
                        {"Name": "encryption-module", "Value": "aes"},
                    ],
                },
                "Schedule": {"Time": "04:00", "Repeat": "1D"},
            }
        self.route_job(old_url, after=after)
        self.fake.route("PUT", f"/api/v1/backup/{BACKUP_ID}", 200, {"Status": "OK"})
        return new_url

    def test_dry_run_sends_no_put(self) -> None:
        new_url = self._ready()
        rc, out, _ = self.invoke("--new-target", str(self.new), "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn(new_url, out)
        self.assertEqual(self.puts(), [])

    def test_a_rejected_put_exits_1(self) -> None:
        self._ready()
        self.fake.route("PUT", f"/api/v1/backup/{BACKUP_ID}", 500, {"Error": "refused"})
        rc, out, _ = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 1)
        self.assertIn("PUT", out)
        self.assertNotIn("VERIFIED", out)
        self.assertEqual(len(self.puts()), 1)
        phrase = [row for row in self.puts()[0].body["Backup"]["Settings"] if row["Name"] == "passphrase"]
        self.assertEqual(phrase[0]["Value"], PASSPHRASE)

    def test_a_read_back_that_moved_a_source_or_returned_the_secret_exits_6(self) -> None:
        new_url = "file://" + str(self.new)
        leaked = {
            "Backup": {
                "ID": BACKUP_ID,
                "Name": "Yamaguchi",
                "TargetURL": new_url,
                "Sources": ["/data", "/extra"],
                "Filters": [],
                "Settings": [
                    {"Name": "passphrase", "Value": PASSPHRASE},
                    {"Name": "encryption-module", "Value": "aes"},
                ],
            },
            "Schedule": {"Time": "04:00", "Repeat": "1D"},
        }
        self._ready(after=leaked)
        rc, out, _ = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 6)
        self.assertIn("FAIL", out)
        self.assertIn("sources unchanged", out)
        self.assertNotIn("VERIFIED", out)

    def test_a_clean_read_back_exits_0_and_the_put_carries_the_real_passphrase(self) -> None:
        new_url = self._ready()
        rc, out, _ = self.invoke("--new-target", str(self.new))
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("VERIFIED", out)
        self.assertIn("passphrase reads back masked", out)
        self.assertEqual(len(self.puts()), 1)
        body = self.puts()[0].body
        self.assertEqual(body["Backup"]["TargetURL"], new_url)
        self.assertEqual(body["Schedule"], {"Time": "04:00", "Repeat": "1D", "LastRun": "2026-10-01T04:00:00Z"})
        phrase = [row for row in body["Backup"]["Settings"] if row["Name"] == "passphrase"]
        self.assertEqual(phrase, [{"Name": "passphrase", "Value": PASSPHRASE}])
        self.assertEqual(self.puts()[0].path, f"/api/v1/backup/{BACKUP_ID}")


if __name__ == "__main__":
    unittest.main()
