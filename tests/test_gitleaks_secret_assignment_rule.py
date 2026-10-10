#!/usr/bin/env python3
"""Gate for `.gitleaks.toml`: the ruleset is not empty, and `juniper-secret-assignment` fires on a backup credential.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
License:     MIT License

Backup recovery B9 (design P0.5a item 6, "Close the detection gap"). Two failures, one per half of this file:

1. **The scan could not fail.** `.gitleaks.toml` had an `[allowlist]` and no `[extend]`, and a gitleaks v8 config
   without `[extend] useDefault = true` loads ONLY its own `[[rules]]`, of which it had none. CI's Security Scan ran
   with zero rules from 2026-08-13 to 2026-10-10 and passed every time. Measured with gitleaks 8.24.3: the old
   config passed a fabricated GitHub token that the built-in config flags.
2. **The shape it missed.** A 36-character Duplicati settings key, in a commented systemd `Environment=` line,
   went through ml#1967 and ml#1968. Even with the defaults loaded, generic-api-key's value class `[\\w.=-]`
   stops at the `* @ $ %` such a key carries.

The model half reads `.gitleaks.toml` with `tomllib` and applies the rule the way gitleaks 8.24.3 does
(`detect/detect.go`): the regex's `secretGroup` is the value, and a value matched by any regex of the rule's
allowlists or of this file's global allowlist is dropped. (The built-in config's own global allowlist, which `[extend]`
merges in, is not modelled; the RealEngine tests are what cover it.) The regex is kept in the subset RE2 and Python `re` share and is
compiled with `re.ASCII`, matching RE2's ASCII `\\b`. Every positive value is ASSEMBLED AT RUNTIME, so this file
holds no literal the rule, the default ruleset or GitHub push protection would flag. The `RealEngine` tests run the
same samples through a gitleaks binary (`GITLEAKS_BIN`, else `gitleaks` on PATH); they skip without one, except in
ci.yml's Security Scan job, which sets `GITLEAKS_PARITY_REQUIRED=1` after gitleaks-action has installed it.

Run: python3 -m unittest -v tests/test_gitleaks_secret_assignment_rule.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import string
import subprocess  # nosec B404 -- runs the gitleaks binary with a fixed argv, never a shell
import tempfile
import tomllib
import unittest
from pathlib import Path

RULE_ID = "juniper-secret-assignment"
ENGINE_VERSION = "8.24.3"

#: Environment / systemd / comment spellings, and the argv spellings (used as `--name=`).
ENV_NAMES = (
    "SETTINGS_ENCRYPTION_KEY",
    "SETTINGS_ENCRYPTION_KEY_OLD",
    "PASSPHRASE",
    "PASSPHRASE_OLD",
    "DUPLICATI_WEB_CREDENTIAL",
    "DUPLICATI__PASSPHRASE",
    "DUPLICATI__SETTINGS_ENCRYPTION_KEY",
    "DUPLICATI__WEBSERVICE_PASSWORD",
)
ARGV_NAMES = ("passphrase", "webservice-password", "webservice-password-init", "settings-encryption-key")

ENV_FORMS = (
    ("bare", "{name}={value}"),
    ("double-quoted", '{name}="{value}"'),
    ("single-quoted", "{name}='{value}'"),
    ("export", "export {name}={value}"),
    ("export double-quoted", 'export {name}="{value}"'),
    ("systemd Environment=", "Environment={name}={value}"),
    ("systemd Environment= quoted", 'Environment="{name}={value}"'),
    ("comment", "# {name}={value}"),
    ("commented export", "# export {name}='{value}'"),
    ("commented systemd line", "#     Environment={name}={value}"),
)
ARGV_FORMS = (
    ("argv", "--{name}={value}"),
    ("argv in a command", "duplicati-server --{name}={value} --webservice-port=8300"),
    ("argv double-quoted", '--{name}="{value}"'),
    ("commented argv", "# ExecStart=/usr/bin/duplicati-server --{name}={value}"),
)

_ALNUM = string.digits + string.ascii_letters


def _repo_root() -> Path:
    for candidate in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (candidate / ".gitleaks.toml").is_file() and (candidate / ".github" / "workflows").is_dir():
            return candidate
    raise AssertionError("no repo root (with .gitleaks.toml and .github/workflows/) above this file")


ROOT = _repo_root()


def _load_config() -> dict:
    with open(ROOT / ".gitleaks.toml", "rb") as fh:
        return tomllib.load(fh)


def _rule(cfg: dict) -> dict:
    rules = [r for r in cfg.get("rules", []) if r.get("id") == RULE_ID]
    if len(rules) != 1:
        raise AssertionError(f"expected exactly one [[rules]] entry with id {RULE_ID!r}, found {len(rules)}")
    return rules[0]


class RuleModel:
    """How gitleaks 8.24.3 applies one rule to text: regex -> secretGroup value -> rule and global allowlists."""

    def __init__(self, cfg: dict) -> None:
        rule = _rule(cfg)
        self.regex = re.compile(rule["regex"], re.ASCII)
        self.group = int(rule.get("secretGroup", 0))
        allow = [rx for entry in rule.get("allowlists", []) if entry.get("regexTarget", "secret") == "secret" for rx in entry.get("regexes", [])]
        allow += list(cfg.get("allowlist", {}).get("regexes", []))
        self.allow = [re.compile(rx, re.ASCII) for rx in allow]

    def reported(self, text: str) -> list[str]:
        out = []
        for m in self.regex.finditer(text):
            value = m.group(self.group) if self.group else m.group(0)
            if not any(rx.search(value) for rx in self.allow):
                out.append(value)
        return out

    def fires(self, text: str) -> bool:
        return bool(self.reported(text))


def _spread(length: int, step: int = 23, offset: int = 0) -> str:
    """A deterministic, high-variety alphanumeric run: no randomness, no literal."""
    return "".join(_ALNUM[(offset + i * step) % len(_ALNUM)] for i in range(length))


def _shaped(length: int = 36, marks: str = "*@$%", offset: int = 1) -> str:
    """The 2026-09-20 literal's SHAPE (digit first; `* @ $ %` inside), never its value."""
    body = list(_spread(length - len(marks), offset=offset))
    for i, mark in enumerate(marks):
        body.insert(3 + i * max(1, (length - 6) // max(1, len(marks))), mark)
    return "".join(body)


def _hex64() -> str:
    return hashlib.sha256(b"juniper-ml B9 regression sample").hexdigest()


def _b64_44() -> str:
    return base64.b64encode(hashlib.sha256(b"juniper-ml B9 regression sample, base64").digest()).decode("ascii")


def _positive_values() -> list[tuple[str, str]]:
    hexed = _hex64()
    values = [
        ("2026-09-20 shape: 36 chars, digit first, * @ $ %", _shaped()),
        ("random-looking alphanumeric, 32", _spread(32, offset=5)),
        ("hex, 64", hexed),
        # A lowercase hex or alphanumeric value is a valid identifier; the code allowlist must not take it.
        ("hex starting with a letter (an identifier, lexically)", "f" + hexed[:39]),
        ("hex starting with a letter, then a paren", "c" + hexed[:23] + ")"),
        ("UPPER hex", hexed.upper()),
        # Upper-case alphanumeric groups joined by `_` look like an UPPER_SNAKE name; only a trailing `) ] ,` makes one code.
        ("UPPER groups joined by _", "Q" + hexed.upper()[:5] + "_" + hexed.upper()[5:11] + "_" + hexed.upper()[11:17]),
        ("base64 with + / =, 44", _b64_44()),
        ("12 chars with punctuation (the minimum)", _spread(11, offset=9) + "!"),
    ]
    for mark in "*@$%!#&+,/:;=?^~":
        values.append((f"16 chars carrying {mark!r}", _spread(7, offset=2) + mark + _spread(8, offset=40)))
    return values


def _with_names(value: str) -> list[tuple[str, str]]:
    """`value` under every name in every form: each ENV form for each ENV name, each ARGV form for each ARGV name."""
    out = []
    for form_label, template in ENV_FORMS:
        for name in ENV_NAMES:
            out.append((f"{form_label} | {name}", template.format(name=name, value=value)))
    for form_label, template in ARGV_FORMS:
        for name in ARGV_NAMES:
            out.append((f"{form_label} | --{name}", template.format(name=name, value=value)))
    return out


def _positive_lines() -> list[tuple[str, str]]:
    return [(f"{where} | {v_label}", line) for v_label, value in _positive_values() for where, line in _with_names(value)]


#: Values that only NAME or STAND IN for a credential. Each is checked under every ENV form and ARGV form.
NEGATIVE_VALUES = (
    ("empty", ""),
    ("$VAR", "$SETTINGS_ENCRYPTION_KEY"),
    ("${VAR}", "${PASSPHRASE}"),
    ("${VAR:-}", "${PASSPHRASE:-}"),
    ("${VAR:?message}", "${DUPLICATI_WEB_CREDENTIAL:?unset}"),
    ("$(command)", '$(cat "$KEY_FILE")'),
    ("$(command) no spaces", "$(systemd-creds-cat-settings-key)"),
    ("escaped expansion", "\\$(cat-the-key-file)"),
    ("<template>", "<the-36-character-settings-key>"),
    ("<template> with spaces", "<your passphrase here>"),
    ("REDACTED", "REDACTED"),
    ("REDACTED, long", "REDACTED-REDACTED-REDACTED"),
    ("***REDACTED***", "***REDACTED***"),
    ("<redacted>", "<redacted>"),
    ("changeme", "changeme"),
    ("CHANGEME, long", "CHANGEME_CHANGEME_CHANGEME"),
    ("change-me, with digits", "change-me-2026-10-10"),
    ("xxx", "xxx"),
    ("x run", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ("X groups", "XXXX-XXXX-XXXX-XXXX"),
    ("...", "..."),
    ("long ...", "................"),
    ("ellipsis", "…"),
    ("***", "***"),
    ("long ***", "************************************"),
    ("printf %s", "%s\\n"),
    ("systemd specifier", "%d/settings-encryption-key"),
    ("{format} field", "{settings_key}"),
    ("f-string field with suffix", "{PROBE_SETTINGS_KEY}\\n"),
    ("attribute access", "args.passphrase"),
    ("method call", "self._read_settings_key()"),
    ("call left open", "os.environ.get("),
    ("constant reference", "PROBE_PASSPHRASE_VALUE,"),
    ("name and paren", "passphrase_from_file)"),
    ("lowercase fixture", "abcdefghijklmnopqrstuvwxyz"),
    ("lowercase words", "correct-horse-battery-staple"),
    ("UPPER words with a number", "SYNTHETIC-TEST-VALUE-01"),
    ("UPPER words", "BACKUP_ARCHIVE_PASSPHRASE_2"),
    ("placeholder word", "placeholder-for-the-real-one"),
    ("example word", "Example-Settings-Key-1234"),
    ("dummy word", "dummy-passphrase-0001"),
    ("fixture word", "fixture-key-with-$-and-%"),
    ("fake word", "fake-web-credential-99"),
    ("short, punctuated (11 chars)", "Tr0ub4d0r&3"),
    ("word characters only, 15", "Ab3dEf6hIj9lMn2"),
    ("a quoted value with spaces", "correct horse battery staple"),
)

#: Lines that merely mention a name, or that use a name this rule does not cover. Every line ends its value before the
#: string ends: in the cached .pyc a string is followed by marshal bytes, not by a quote, and a value that ran on into
#: them would read as a finding to `gitleaks dir` (which, unlike the hook and CI, scans gitignored files).
NEGATIVE_LINES = (
    ("prose: set it in the env file", "set PASSPHRASE= in /etc/duplicati/env and nothing else"),
    ("prose: the line", "the SETTINGS_ENCRYPTION_KEY= line is refused by the wrapper"),
    ("prose: backticked", "`--passphrase=` and `--webservice-password=` are argv forms"),
    ("prose: an ellipsis", "PASSPHRASE=… (36 chars)"),
    ("prose: no assignment", "SETTINGS_ENCRYPTION_KEY is exported by the wrapper"),
    ("Python kwarg to a name", "run(passphrase=passphrase, timeout=10)"),
    ("Python kwarg, attribute", "client.restore(passphrase=args.passphrase) on the restore path"),
    ("Python dict", 'env["PASSPHRASE"] = value'),
    ("spaced assignment", "PASSPHRASE = value_read_from_the_file"),
    ("grep pattern", "grep -c '^SETTINGS_ENCRYPTION_KEY=' /etc/duplicati/env"),
    ("sed group", "PASSPHRASE=$(sed -nE 's/^PASSPHRASE=(.*)$/\\1/p' \"$F\")"),
    ("shell test", '[[ "${PASSPHRASE:-}" == "${EXPECTED:-}" ]] && echo "passphrase=match"'),
)


def _negative_lines() -> list[tuple[str, str]]:
    lines = [(f"{v_label} | {where}", line) for v_label, value in NEGATIVE_VALUES for where, line in _with_names(value)]
    lines += list(NEGATIVE_LINES)
    # A credential-SHAPED value under a name the rule does not cover: a different variable is not its business.
    shaped = _shaped(offset=7)
    for other in ("TEST_PASSPHRASE", "GPG_PASSPHRASE", "PASSPHRASE_FILE", "SETTINGS_ENCRYPTION_KEY_FILE", "DUPLICATI_WEB_CREDENTIAL_FILE", "Passphrase"):
        lines.append((f"other name {other}", other + "=" + shaped))
    lines.append(("argv option it does not cover", "--webservice-password-file=" + shaped))
    return lines


class RuleModelTest(unittest.TestCase):
    """The configuration, read the way gitleaks reads it, through a Python model of the matcher."""

    cfg: dict
    model: RuleModel

    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = _load_config()
        cls.model = RuleModel(cls.cfg)

    def test_config_extends_the_default_ruleset(self) -> None:
        # Without this, gitleaks loads only [[rules]] from this file: the zero-rule config that passed every scan.
        self.assertIs(self.cfg.get("extend", {}).get("useDefault"), True, "[extend] useDefault = true is missing: gitleaks would load no default rule")

    def test_global_allowlist_has_no_paths(self) -> None:
        self.assertNotIn("paths", self.cfg.get("allowlist", {}), "a global [allowlist].paths exempts whole files from EVERY rule (see the file's comment)")

    def test_rule_shape(self) -> None:
        rule = _rule(self.cfg)
        self.assertEqual(rule.get("secretGroup"), 1)
        self.assertEqual(self.model.regex.groups, 1, "one capture group: the value")
        for entry in rule.get("allowlists", []):
            self.assertIn(entry.get("regexTarget", "secret"), ("secret",), "allowlists are tested against the VALUE only")
            self.assertNotIn("paths", entry, "a path allowlist would blind the rule for a whole file")
            self.assertNotIn("commits", entry, "historical findings belong in .gitleaksignore, commit-scoped")

    def test_keywords_cover_every_name(self) -> None:
        # gitleaks evaluates a rule only on content containing one of its keywords, lowercased.
        keywords = [k.lower() for k in _rule(self.cfg).get("keywords", [])]
        for name in ENV_NAMES + ARGV_NAMES:
            with self.subTest(name=name):
                self.assertTrue(any(k in name.lower() for k in keywords), f"{name} contains no keyword: the rule would never run on it")

    def test_the_2026_09_20_shape_fires(self) -> None:
        # join(), not `"...KEY" + "="`: CPython folds adjacent literals, and the folded constant ending in `KEY=`
        # makes the cached .pyc (gitignored, but scanned by `gitleaks dir`) look like an assignment.
        line = "".join(("#     Environment=SETTINGS_ENCRYPTION_KEY", "=", _shaped()))
        self.assertEqual(len(self.model.reported(line)), 1)

    def test_positives_fire(self) -> None:
        cases = _positive_lines()
        self.assertGreater(len(cases), 500)
        for label, line in cases:
            with self.subTest(case=label):
                self.assertTrue(self.model.fires(line), "did not fire")

    def test_negatives_are_silent(self) -> None:
        cases = _negative_lines()
        self.assertGreater(len(cases), 500)
        for label, line in cases:
            with self.subTest(case=label):
                self.assertFalse(self.model.fires(line), "fired")

    def test_each_rule_allowlist_is_load_bearing(self) -> None:
        # Without its allowlists the bare regex must fire on some negative per allowlist: none is dead weight.
        rule = _rule(self.cfg)
        bare = re.compile(rule["regex"], re.ASCII)
        negatives = [line for _, line in _negative_lines()]
        for i, entry in enumerate(rule.get("allowlists", [])):
            regexes = [re.compile(rx, re.ASCII) for rx in entry.get("regexes", [])]
            with self.subTest(allowlist=entry.get("description", i)):
                hits = [line for line in negatives for m in bare.finditer(line) if any(rx.search(m.group(1)) for rx in regexes)]
                self.assertTrue(hits, "no negative sample exercises this allowlist")


class IgnoreFileTest(unittest.TestCase):
    """`.gitleaksignore` holds only documented, commit-scoped entries."""

    S1_ENTRIES = (
        "6708cb287e346a7ce411f0b3b1372c6654422949:scripts/duplicati-wrapper.bash:juniper-secret-assignment:49",
        "60d1c45db8a4a20ae702417a252386d3ce065ce4:scripts/duplicati-wrapper.bash:juniper-secret-assignment:46",
    )

    def setUp(self) -> None:
        self.lines = (ROOT / ".gitleaksignore").read_text(encoding="utf-8").splitlines()

    def test_entries_are_commit_scoped_and_commented(self) -> None:
        entry = re.compile(r"[0-9a-f]{40}:[^:]+:[a-z0-9-]+:[0-9]+")
        for i, raw in enumerate(self.lines):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            with self.subTest(line=i + 1):
                self.assertRegex(line, entry, "an entry must name its 40-hex commit; a file-scoped one would hide FUTURE secrets")
                self.assertTrue(self.lines[i - 1].strip().startswith("#"), "each entry carries a comment saying why")

    def test_the_two_s1_commits_are_ignored(self) -> None:
        entries = {line.strip() for line in self.lines if line.strip() and not line.strip().startswith("#")}
        self.assertEqual(entries, set(self.S1_ENTRIES), "only the 2026-09-20 literal's two commits are ignored")


class EnginePinTest(unittest.TestCase):
    """CI and the pre-commit hook run the same gitleaks version."""

    def test_ci_and_hook_pin_the_same_engine(self) -> None:
        import yaml  # the regression job installs PyYAML; the Security Scan job runs only the RealEngine tests

        ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        steps = ci["jobs"]["security"]["steps"]
        action = next(s for s in steps if str(s.get("uses", "")).startswith("gitleaks/gitleaks-action@"))
        self.assertEqual(str(action.get("env", {}).get("GITLEAKS_VERSION")), ENGINE_VERSION)
        hooks = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
        repo = next(r for r in hooks["repos"] if r.get("repo") == "https://github.com/gitleaks/gitleaks")
        self.assertEqual(repo.get("rev"), "v" + ENGINE_VERSION)
        self.assertIn("gitleaks", [h.get("id") for h in repo.get("hooks", [])])


def _gitleaks_bin() -> str | None:
    return os.environ.get("GITLEAKS_BIN") or shutil.which("gitleaks")


class RealEngineTest(unittest.TestCase):
    """The same samples through the gitleaks binary itself; ci.yml's Security Scan job requires these to run."""

    def setUp(self) -> None:
        self.bin = _gitleaks_bin()
        if self.bin is None:
            if os.environ.get("GITLEAKS_PARITY_REQUIRED") == "1":
                self.fail("GITLEAKS_PARITY_REQUIRED=1 but no gitleaks binary (GITLEAKS_BIN unset, none on PATH)")
            self.skipTest("no gitleaks binary (set GITLEAKS_BIN, or put gitleaks on PATH)")

    #: Lines per sample file. gitleaks `dir` reads a file in 100 kB chunks; ~40 kB files keep every sample whole.
    BATCH = 400

    def _scan(self, batches: list[list[str]]) -> dict[tuple[int, int], set[str]]:
        """Scan one sample file per batch in a single run; returns {(batch, line): {RuleID, ...}}."""
        with tempfile.TemporaryDirectory(prefix="b9-gitleaks-") as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            for i, batch in enumerate(batches):
                (samples / f"batch_{i:03d}.txt").write_text("".join(line + "\n" for line in batch), encoding="utf-8")
            report = Path(tmp) / "report.json"
            argv = [self.bin, "dir", "--no-banner", "--redact", "--exit-code=0", "--report-format=json", f"--report-path={report}", "--config", str(ROOT / ".gitleaks.toml"), str(samples)]
            res = subprocess.run(argv, capture_output=True, text=True, timeout=300, check=False)
            self.assertEqual(res.returncode, 0, f"gitleaks exited {res.returncode}: {res.stderr[-400:]}")
            with open(report, encoding="utf-8") as fh:
                findings = json.load(fh)
        hits: dict[tuple[int, int], set[str]] = {}
        for f in findings:
            index = int(re.search(r"batch_(\d+)\.txt$", f["File"]).group(1))
            hits.setdefault((index, f["StartLine"]), set()).add(f["RuleID"])
        return hits

    def test_real_engine_loads_the_default_ruleset(self) -> None:
        fabricated = "gh" + "p_" + _spread(36, step=29, offset=11)
        hits = self._scan([["GITHUB_TOKEN=" + fabricated]])
        self.assertIn("github-pat", hits.get((0, 1), set()), "the config's ruleset does not include the default rules")

    def test_real_engine_matches_the_model(self) -> None:
        cases = [(label, line, True) for label, line in _positive_lines()] + [(label, line, False) for label, line in _negative_lines()]
        batches = [cases[i : i + self.BATCH] for i in range(0, len(cases), self.BATCH)]
        hits = self._scan([[line for _, line, _ in batch] for batch in batches])
        for b, batch in enumerate(batches):
            for n, (label, _, expected) in enumerate(batch, start=1):
                with self.subTest(case=label):
                    self.assertEqual(RULE_ID in hits.get((b, n), set()), expected, "the binary and the model disagree")


if __name__ == "__main__":
    unittest.main()
