#!/usr/bin/env python3
"""``util/ad-hoc/2026-11-09_ac4_restore_drill.py``: the AC-4 restore drill's decrypt, parser, sample filter and oracle.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

The driver decrypts a Duplicati dlist in-process (the tool it replaces put the archive passphrase on argv), streams a
file list of about two million entries, samples only benign files, and judges each restored file by SHA-256 and
length. Until 2026-11-11 its only test was a self-test kept in a gitignored ``tmp/`` directory; this suite absorbs it
and adds the cases that self-test did not have.

What each group pins:

* **AES Crypt v2 and v3** round-trip at seven sizes against an encoder written from the format's specification, with a
  non-ASCII password. A wrong password, a flipped ciphertext byte, a flipped trailing HMAC byte, a truncated file and
  a file that is not AES Crypt each stop with exit 2 and write no usable output. Both HMACs are checked before any
  padding is trusted.
* **The streaming parser.** A UTF-8 BOM in front of the array (the .NET writer's, and the cause of the 2026-11-09 "0
  entries" run), a multibyte character split across two reads, an empty array, and three malformed streams, each of
  which must stop with exit 2 rather than yield nothing.
* **The sample filter** never selects a path under a secret-bearing tree or with a secret-shaped name, and
  ``stratum_of`` is exact at every size boundary.
* **The oracle** tells a verified file from a missing one, a length mismatch and a hash mismatch, and engages the live
  comparison only for a live file that predates the fileset.
* **Secrets.** The passphrase loader prints a 16-hex prefix of a hash and never the value, and the driver's source
  hands the passphrase to ``duplicati-cli`` through the environment, with neither local-blocks option on its argv.

The driver resolves the backup Source's home through ``pwd`` at import, so it is loaded here with that lookup
replaced. No Duplicati binary runs and no file outside a temporary directory is read.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import hmac
import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import unittest
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER = REPO_ROOT / "util" / "ad-hoc" / "2026-11-09_ac4_restore_drill.py"
HOME = "/srv/fixture-home/"
PHRASE = "pässwörd-Ω with spaces"  # a throwaway literal, not a credential; non-ASCII on purpose


def load_driver():
    spec = importlib.util.spec_from_file_location("ac4_restore_drill_under_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    with mock.patch("pwd.getpwnam", return_value=argparse.Namespace(pw_dir=HOME.rstrip("/"))):
        spec.loader.exec_module(module)
    return module


drill = load_driver()


def aescrypt(plain: bytes, phrase: str, version: int, *, iterations: int = 2000, v3_mac_extra: bytes = b"\x03") -> bytes:
    """An AES Crypt v2 or v3 file, written from the format's specification (not from the driver)."""
    iv1, iv2, key2 = os.urandom(16), os.urandom(16), os.urandom(32)
    out = b"AES" + bytes([version, 0]) + (2).to_bytes(2, "big") + b"xy" + b"\0\0"  # one extension, then the end-of-extensions marker
    if version == 2:
        key = iv1 + b"\0" * 16
        for _ in range(8192):
            key = hashlib.sha256(key + phrase.encode("utf-16-le")).digest()
    else:
        out += iterations.to_bytes(4, "big")
        key = hashlib.pbkdf2_hmac("sha512", phrase.encode("utf-8"), iv1, iterations, 32)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv1)).encryptor()
    wrapped = encryptor.update(iv2 + key2) + encryptor.finalize()
    out += iv1 + wrapped + hmac.new(key, wrapped + (v3_mac_extra if version == 3 else b""), hashlib.sha256).digest()
    if version == 2:
        pad = (16 - len(plain) % 16) % 16
        body = plain + b"\0" * pad
    else:
        pad = 16 - len(plain) % 16
        body = plain + bytes([pad]) * pad
    encryptor = Cipher(algorithms.AES(key2), modes.CBC(iv2)).encryptor()
    cipher = encryptor.update(body) + encryptor.finalize()
    return out + cipher + (bytes([len(plain) % 16]) if version == 2 else b"") + hmac.new(key2, cipher, hashlib.sha256).digest()


class _Files(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.src, self.dst = self.dir / "volume.aes", self.dir / "volume.out"

    def decrypt(self, blob: bytes, phrase: str = PHRASE) -> bytes:
        self.src.write_bytes(blob)
        drill.aescrypt_decrypt(str(self.src), str(self.dst), phrase)
        return self.dst.read_bytes()

    def stops(self, blob: bytes, needle: str, phrase: str = PHRASE) -> None:
        self.src.write_bytes(blob)
        err = io.StringIO()
        with self.assertRaises(SystemExit) as caught, redirect_stderr(err):
            drill.aescrypt_decrypt(str(self.src), str(self.dst), phrase)
        self.assertEqual(caught.exception.code, 2)
        self.assertIn(needle, err.getvalue())
        self.assertNotIn(phrase, err.getvalue())


class AesCryptTest(_Files):
    SIZES = (1, 15, 16, 17, 4096, (1 << 20) + 5, 3 << 20)

    def test_both_versions_round_trip_at_every_size(self) -> None:
        for version in (2, 3):
            for size in self.SIZES:
                with self.subTest(version=version, size=size):
                    plain = os.urandom(size)
                    self.assertEqual(self.decrypt(aescrypt(plain, PHRASE, version)), plain)

    def test_an_empty_plaintext_round_trips_in_v3_and_is_refused_in_v2(self) -> None:
        self.assertEqual(self.decrypt(aescrypt(b"", PHRASE, 3)), b"")
        # v2 pads to a block multiple with nothing for an empty input, so there is no ciphertext block at all.
        self.stops(aescrypt(b"", PHRASE, 2), "not a positive multiple of 16")

    def test_v3_at_the_products_iteration_count_and_either_mac_form(self) -> None:
        plain = os.urandom(100)
        self.assertEqual(self.decrypt(aescrypt(plain, PHRASE, 3, iterations=300000)), plain)
        self.assertEqual(self.decrypt(aescrypt(plain, PHRASE, 3, v3_mac_extra=b"")), plain)

    def test_a_wrong_password_stops_at_the_header(self) -> None:
        for version in (2, 3):
            with self.subTest(version=version):
                self.stops(aescrypt(os.urandom(100), PHRASE, version), "header HMAC mismatch", phrase="not the passphrase")

    def test_tampering_stops_at_the_content_mac(self) -> None:
        for version in (2, 3):
            for label, offset in (("ciphertext", -40), ("trailing HMAC", -1)):
                with self.subTest(version=version, where=label):
                    blob = bytearray(aescrypt(os.urandom(100), PHRASE, version))
                    blob[offset] ^= 1
                    self.stops(bytes(blob), "content HMAC mismatch")

    def test_a_flipped_wrapped_key_byte_stops_at_the_header(self) -> None:
        blob = bytearray(aescrypt(os.urandom(100), PHRASE, 3))
        blob[5 + 2 + 2 + 2 + 4 + 16 + 3] ^= 1  # inside the 48 wrapped bytes that carry the content key
        self.stops(bytes(blob), "header HMAC mismatch")

    def test_what_is_not_an_aes_crypt_file_stops(self) -> None:
        self.stops(b"PK\x03\x04 a zip archive, not AES Crypt at all", "not an AES Crypt v2/v3 file")
        self.stops(b"AES\x01\x00" + bytes(200), "not an AES Crypt v2/v3 file")
        blob = aescrypt(os.urandom(4096), PHRASE, 3)
        self.stops(blob[:-7], "not a positive multiple of 16")
        self.stops(blob[:-16], "content HMAC mismatch")


class JsonStreamTest(unittest.TestCase):
    def stream(self, raw: bytes, chunk: int = 331) -> list:
        return list(drill.iter_json_array(io.BytesIO(raw), chunk=chunk))

    def stops(self, raw: bytes, needle: str) -> None:
        err = io.StringIO()
        with self.assertRaises(SystemExit) as caught, redirect_stderr(err):
            self.stream(raw)
        self.assertEqual(caught.exception.code, 2)
        self.assertIn(needle, err.getvalue())

    def test_a_large_array_arrives_whole_whatever_the_read_size(self) -> None:
        items = [{"type": "File", "path": f"{HOME}x{i}.py", "size": i, "hash": "h", "blocklists": ["a", "b"]} for i in range(5000)]
        raw = json.dumps(items).encode()
        for chunk in (777, 1 << 22):
            with self.subTest(chunk=chunk):
                self.assertEqual(self.stream(raw, chunk), items)
        few = json.dumps(items[:40]).encode()
        for chunk in (1, 2):  # an entry is then never complete in one read
            with self.subTest(chunk=chunk):
                self.assertEqual(self.stream(few, chunk), items[:40])

    def test_a_bom_and_a_split_multibyte_character(self) -> None:
        # The 2026-11-09 fault: .NET writes a BOM, the parser never saw "[" and returned nothing, with no error.
        items = [{"type": "File", "path": f"{HOME}ü€\U0001f600{i}.py", "size": i} for i in range(3000)]
        raw = b"\xef\xbb\xbf" + json.dumps(items, ensure_ascii=False).encode()
        self.assertEqual(self.stream(raw, 331), items)
        few = b"\xef\xbb\xbf" + json.dumps(items[:30], ensure_ascii=False).encode()
        for chunk in (1, 2, 3):  # every read ends inside the BOM or inside a two-, three- or four-byte character
            with self.subTest(chunk=chunk):
                self.assertEqual(self.stream(few, chunk), items[:30])

    def test_an_empty_array_yields_nothing_and_does_not_stop(self) -> None:
        for raw in (b"[]", b"\xef\xbb\xbf[ ]", b" \r\n[\n]\n"):
            self.assertEqual(self.stream(raw), [])

    def test_whitespace_and_commas_between_entries(self) -> None:
        self.assertEqual(self.stream(b'[ {"a": 1} ,\r\n\t{"a": 2},{"a":[1,2,{"b":"]"}]} ]'), [{"a": 1}, {"a": 2}, {"a": [1, 2, {"b": "]"}]}])

    def test_a_stream_that_is_not_an_array_stops(self) -> None:
        self.stops(b'{"type": "File"}', "does not start with a JSON array")
        self.stops(b"\xef\xbb\xbfnull", "does not start with a JSON array")
        self.stops(b'[{"type": "File", "path": "/x"', "ended inside an entry")

    def test_an_empty_stream_yields_nothing(self) -> None:
        # The driver's caller turns this into "yielded no entries -- a parser fault"; the parser itself has nothing to say.
        self.assertEqual(self.stream(b""), [])
        self.assertIn('fail("filelist.json yielded no entries', DRIVER.read_text(encoding="utf-8"))


class SampleFilterTest(unittest.TestCase):
    def test_secret_bearing_paths_are_never_eligible(self) -> None:
        refused = [".ssh/config.txt", ".gnupg/notes.md", ".config/duplicati-backup/env.txt", ".mozilla/firefox/x/places.txt", ".config/Slack/logs/a.txt", ".claude/projects/x.md", ".aws/credentials.txt", ".local/state/duplicati-server-db/readme.md", ".cache/thing.py", "proj/.env.py", "proj/secret_notes.md", "proj/api_token.txt", "proj/credentials.csv", "proj/password-list.txt", "proj/private/readme.md", "proj/id_rsa.txt", "proj/session_dump.txt", "proj/cookies.txt", "proj/passphrase.md"]
        for relative in refused:
            with self.subTest(path=relative):
                self.assertFalse(drill.eligible(HOME + relative))
        for name in ("server.key", "cert.pem", "store.p12", "vault.kdbx", "mail.asc", "data.gpg"):
            self.assertFalse(drill.eligible(HOME + "proj/" + name))

    def test_ordinary_project_and_media_files_are_eligible(self) -> None:
        for relative in ("proj/a.py", "Development/python/x/README.md", "Music/track.mp3", "Pictures/Screenshots/shot.png", ".conda/pkgs/lib/libthing.so", "proj/weights.pt"):
            with self.subTest(path=relative):
                self.assertTrue(drill.eligible(HOME + relative))

    def test_only_the_sources_home_an_allowed_extension_and_no_glob_character(self) -> None:
        self.assertFalse(drill.eligible("/etc/x.py"))
        self.assertFalse(drill.eligible("/srv/fixture-home-other/x.py"))
        self.assertFalse(drill.eligible(HOME + "proj/a.exe"))
        self.assertFalse(drill.eligible(HOME + "proj/noext"))
        for glob in "*?[]{}":
            self.assertFalse(drill.eligible(f"{HOME}proj/a{glob}b.py"), "duplicati-cli would read the path as a filter expression")
        self.assertFalse(drill.eligible(HOME + drill.NEGATIVE_NAME + "000000001.txt"), "the negative control's own name is never a candidate")

    def test_strata_are_exact_at_their_bounds(self) -> None:
        mib, gib = 1 << 20, 1 << 30
        # Sizes from 0 up. A File entry always carries `size`; the driver's `-1` default for a missing one is NOT
        # guarded by stratum_of (it reads as "small") -- recorded as a finding, left alone while drill 1 is pending.
        cases = {0: "empty", 1: "small", mib: "small", mib + 1: "multi", 64 * mib: "multi", 64 * mib + 1: None, 256 * mib - 1: None, 256 * mib: "large", 2 * gib: "large", 2 * gib + 1: None}
        for size, expected in cases.items():
            with self.subTest(size=size):
                self.assertEqual(drill.stratum_of(size), expected)


class OracleTest(_Files):
    def candidate(self, data: bytes, live: Path | None = None) -> dict:
        return {"path": str(live or self.dir / "no-live-copy.py"), "size": len(data), "hash": base64.b64encode(hashlib.sha256(data).digest()).decode()}

    def restored(self, data: bytes) -> str:
        path = self.dir / "restored.py"
        path.write_bytes(data)
        return str(path)

    def test_verified_missing_and_the_two_mismatches(self) -> None:
        data = os.urandom(5000)
        self.assertEqual(drill.judge(self.candidate(data), self.restored(data), 0), ("VERIFIED", None))
        self.assertEqual(drill.judge(self.candidate(data), None, 0), ("MISSING", None))
        self.assertEqual(drill.judge(self.candidate(data), self.restored(data[:-1]), 0)[0], "LENGTH_MISMATCH 4999 != 5000")
        flipped = bytearray(data)
        flipped[0] ^= 0xFF
        self.assertEqual(drill.judge(self.candidate(data), self.restored(bytes(flipped)), 0), ("HASH_MISMATCH", None))
        self.assertEqual(drill.judge(self.candidate(b""), self.restored(b""), 0), ("VERIFIED", None), "an empty file has nothing to hash")

    def test_the_live_oracle_engages_only_on_a_file_older_than_the_fileset(self) -> None:
        data = os.urandom(300)
        live = self.dir / "live.py"
        live.write_bytes(data)
        after = time.time() + 3600
        self.assertEqual(drill.judge(self.candidate(data, live), self.restored(data), after), ("VERIFIED", "match"))
        self.assertEqual(drill.judge(self.candidate(data, live), self.restored(data), 0), ("VERIFIED", None), "a live file modified after the fileset proves nothing either way")
        live.write_bytes(os.urandom(300))
        self.assertEqual(drill.judge(self.candidate(data, live), self.restored(data), after), ("VERIFIED", "contradiction"))
        live.write_bytes(data + b"x")
        self.assertEqual(drill.judge(self.candidate(data, live), self.restored(data), after)[1], "contradiction")

    def test_sha256_is_base64_as_the_dlist_stores_it(self) -> None:
        path = self.dir / "f.bin"
        path.write_bytes(b"abc")
        self.assertEqual(drill.sha256_b64(str(path)), "ungWv48Bz+pBQUDeXa4iI7ADYaOWF3qctBD/YfIAFa0=")


class SecretsTest(_Files):
    def load(self, text: str, key: str = "PASSPHRASE") -> tuple[str, str]:
        env = self.dir / "env"
        env.write_text(text, encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            value = drill.load_passphrase(str(env), key)
        return value, out.getvalue()

    def test_the_loader_returns_the_value_and_prints_only_a_hash_prefix(self) -> None:
        value, shown = self.load(f"# comment\nOTHER=1\nexport PASSPHRASE='{PHRASE}'\n")
        self.assertEqual(value, PHRASE)
        self.assertNotIn(PHRASE, shown)
        self.assertIn(f"sha256[:16]={hashlib.sha256(PHRASE.encode()).hexdigest()[:16]}", shown)
        self.assertEqual(self.load(f'PASSPHRASE="{PHRASE}"\n')[0], PHRASE)
        self.assertEqual(self.load(f"PASSPHRASE={PHRASE}\n")[0], PHRASE)
        self.assertEqual(self.load("PASSPHRASE=first\nPASSPHRASE=second\n")[0], "second", "the last assignment wins, as a shell would have it")

    def test_a_missing_or_empty_key_stops(self) -> None:
        for text in ("OTHER=1\n", "PASSPHRASE=\n", "", "#PASSPHRASE=commented\n"):
            with self.subTest(text=text):
                err = io.StringIO()
                env = self.dir / "env"
                env.write_text(text, encoding="utf-8")
                with self.assertRaises(SystemExit) as caught, redirect_stderr(err), redirect_stdout(io.StringIO()):
                    drill.load_passphrase(str(env), "PASSPHRASE")
                self.assertEqual(caught.exception.code, 2)
                self.assertIn("no PASSPHRASE= assignment", err.getvalue())

    def test_the_passphrase_reaches_duplicati_through_the_environment_only(self) -> None:
        tree = ast.parse(DRIVER.read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        argv = next(node.value for node in ast.walk(main) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "argv" for t in node.targets))
        names = {node.id for node in ast.walk(argv) if isinstance(node, ast.Name)}
        self.assertNotIn("passphrase", names, "the passphrase is not an element of duplicati-cli's argv")
        env = next(node.value for node in ast.walk(main) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "env" for t in node.targets))
        assert isinstance(env, ast.Call)
        self.assertIn("PASSPHRASE", {kw.arg for kw in env.keywords})
        literals = {node.value for node in ast.walk(argv) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertEqual(literals & {"duplicati-cli", "restore"}, {"duplicati-cli", "restore"})
        for forbidden in ("--no-local-blocks", "--restore-with-local-blocks", "duplicati-aescrypt"):
            self.assertFalse(any(forbidden in literal for literal in literals), f"{forbidden} is not passed (design AC-4)")


if __name__ == "__main__":
    unittest.main()
