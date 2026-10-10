#!/usr/bin/env python3
"""
Probe whether a gitleaks config actually detects secrets, and gate a push by scanning exactly the files to be published.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-04
Status: ad-hoc — investigation; its --scan-dir mode is the interim pre-push gate named by the plan below
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (XC-LEAKS, XC-PRESERVE);
         reports/2026-10-04_consolidated-development-plan/round4-*.md .. round11-*.md (how it was tested and broken);
         util/ad-hoc/2026-10-05_gate_regression.py (its regression cases)

Why this exists
---------------
1. A `.gitleaks.toml` that defines only `[allowlist]` (no `[[rules]]`, no `[extend] useDefault = true`) loads ZERO
   detection rules, so a scan with it reports "no leaks found" for anything (measured 2026-10-04, gitleaks v8.30.1).
2. The DEFAULT rules miss the backup-passphrase class (`PASSPHRASE=...`, `TIER2_PASSPHRASE=...`), which the B9 rule in
   `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` (row B9, L227)
   exists for. So the gate runs TWO scans and reports their union: v8.30.1's default rules, with no repository
   allowlist (CI runs gitleaks-action's 8.24.3 with each repository's own), and B9-class rules on their own, because `[extend] useDefault = true` would also import the default global allowlist,
   whose `^true|false|null$` alternation drops values that start "true", contain "false" or end "null".
3. A gate must fail CLOSED. Validation broke six earlier versions: round 4 (R4B-01) read a missing report as clean;
   round 5 (R5A-01) trusted the scanner to read what the tool counted; round 6 (R6A1-01) let a rule cross a line
   break, so an empty `PASSPHRASE_FILE=` swallowed the secret on the next line; round 7 (R7A-01, R7B1-01, R7B1-02)
   found the same swallow within one line and by the default rules, and missed code-spanned and italic names; round
   8 (R8A-01, R8B1-01..04) found the swallow with a prefixed name, and missed PEP 604 annotations, argv lists,
   JSON-list values and escaped refusal texts; round 9 (R9B1-01) found the swallow back whenever the `_FILE` key itself
   follows a separator (`cd x; PASSPHRASE_FILE=… PASSPHRASE=…`), because the path skip dropped the whole match.

How the gate works (--scan-dir)
-------------------------------
- It walks the directory itself and REFUSES (exit 3) what it cannot scan reliably: a symlink (file or directory), a
  non-regular file, an unreadable file or directory (any walk error), text that is not UTF-8 (a UTF-16 or UTF-32 BOM
  is refused too: convert such a file to UTF-8 first), a NUL character, or a line over 20,000 bytes. Copy the files
  themselves (`cp -L`); inspect binaries apart. Give --scan-dir once; a second one is an error.
- It STAGES every file as flat `NNNNN-PPP-u.txt` parts of at most 60,000 bytes, split at line boundaries, with CRLF
  normalised to LF. Lines are numbered by LF, as `sed -n` and `grep -n` number them; only a file with no LF at all is
  split at lone CRs. Each part repeats the last lines of the one before it: up to 9 lines when they fit in 20,000
  bytes, never fewer than 3. So a match spanning up to 9 line breaks (3 for long lines) is never cut at a part
  boundary. Flat names defeat path allowlists and a source-root `.gitleaksignore` (scanned as text, never honoured).
- Every B9-class rule matches within ONE line, except the Name/Value pair rules, which span at most 3 line breaks.
  Scan 2 also carries line-bounded rules for this ecosystem's other credential names in env style (`*_API_KEY`,
  `*_API_KEYS`, `*_TOKEN`, `*_PASSWORD` and `*_SECRET`, as assignments, environ["X"] subscripts, JSON-list values,
  labels and table rows), for `aescrypt`'s argv (a command line or a list), and for the three refusal texts that quote an
  API key verbatim (requests' `in header value: '…'`, h11's `Illegal header value b'…'` (httpx), and canopy's `invalid X-API-Key
  header: …`, with the key behind blanks or repr/JSON/HTML escapes), because the default rules' separators cross line
  breaks (round 7, R7B1-02, R7B1-03; round 8, R8B1-02..06).
- It runs a CANARY of thirty-two planted classes through the same staging and scans first; every one must be found.
- The forms it is tested on are the cases in util/ad-hoc/2026-10-05_gate_regression.py. Variants of them (other
  quoting, escaping, separators or wrappers) can be missed: read every added line that names a credential, and the
  lines below a name that has no value beside it, whatever the gate says
  (util/ad-hoc/2026-10-05_masked_finding_shape.py --names).
- It passes `--ignore-gitleaks-allow`, so an inline allow marker hides nothing.
- It accepts only the scanner's "clean" (0) and "leaks found" (10) exits, requires a JSON report that agrees, and
  requires the scanner's "scanned ~N bytes" to equal the staged bytes; on a mismatch it names the files skipped.
- Each run works in its own directory under --workdir; only the verified tarball is shared.
- A finding a session has READ, on its lines, and judged not to be a credential can be accepted with `--accept KEY`,
  KEY being exactly as printed: PATH:LINES:COLUMN:RULE:HASH. LINES is the matched line, or START-END when the match
  spans lines: read all of them, because the value can sit on the last. HASH covers the matched lines, so an edit
  changes it; an `--accept` that matches no finding is an error. Record each in the PR body. A finding on a line
  that two parts share can print two keys, one column apart: accept both.
- It pins the scanner release and re-verifies the tarball against the pinned sha256 on EVERY run.
- Run it unpiped, or read `${PIPESTATUS[0]}`: a pipeline reports its last command's status, not the gate's.

Known limits (it is a screen, not a proof of absence)
-----------------------------------------------------
- Names outside the B9 set (`PASSPHRASE`, `SETTINGS_ENCRYPTION_KEY`, `DUPLICATI_WEB_CREDENTIAL`, `webservice-password`,
  with any prefix, `_`/`-`/no separator inside the three multi-word names, and `_`/`-` suffixes) and outside the
  env-style names above; values under 8 characters; `PASS_PHRASE` and other split spellings of one-word names.
- A value on a different line from its name (`passphrase:` then the value below it), outside the Name/Value rules:
  a Kubernetes or Helm `- name: X` over `value: …`; a YAML block scalar; a label over its value; an argv list one item
  per line; a heredoc or here-string; a flag split from its value by a line continuation (round 9, R9B1-02).
- Prose, such as: the passphrase is …; set to …; rotated from …; a label followed by a dash; a name and its value
  separated only by a space, with no `--` (`passphrase <value>`). Also a multi-word unquoted value whose first word
  is short; a value in double backticks; a fallback value (`os.environ.get(…) or "…"`); table rows where the value
  is not in the cell right after the name; low-entropy table values.
- A credential written with no B9 name beside it: `printf`, `echo … | tee` or a redirect into a credential file;
  `openssl -pass pass:…`; a value set after a name check (`if s["Name"] == …: s["Value"] = …`); a comparison (`==`);
  a CSV row; sqlite3 `-box` output; XML; a bytes literal; ANSI-coloured output; Makefile `:=` and `?=`, and Go `:=`.
- Label and table variants: a value cell in quotes, or a code span holding a quoted value; words after a code-spanned
  name in its cell; an em dash, `***bold-italic***`, an HTML `<strong>` label, curly quotes or an NBSP around the
  name; a qualifier in `[…]` or over 40 characters.
- Value leads the bare-value classes refuse: `#` after a blank, `-` after a flag and a blank, `$` or `#` under an
  env-style name (`${NAME:-value}` included), bash `$'…'`, and triple quotes.
- Name/Value settings outside JSON or a dict (a dataclass repr, `dict(Name=…)`, YAML), a key between Name and Value,
  a TOML dotted suffix (`passphrase.old`), and `=>`.
- Same-line variants (round 9, R9B1-07): a bare value with a quote or a backtick among its first 8 characters, a JSON
  value with an escaped quote there, a Name/Value Value holding a quote, a value split by string concatenation, the
  settings-key flag spelled with underscores before a space, the web-credential name as a flag, a shell-quoted flag
  and value pair; and refusal texts behind three or more backslashes or a named HTML entity.
- A real value whose WHOLE shape is a placeholder's (`<x>`, `\\<x\\>`, `$VAR`, `${VAR}`, `{{ x }}`, `{x}`, `%(x)s`,
  `%X%`, `***`, `your-…-key`, `Field(default=None)`, an italic `*(word)*`, ...), or is itself a credential name
  (`TIER2_PASSPHRASE`, `settingsEncryptionKey`) or a credential name assigned such a placeholder (the swallowed half
  of an example, `X_FILE= <name>=<value>`; round 9's reconciliation). Under an env-style name, a value of lowercase
  words joined by hyphens is read as prose (round 9, R9B1-11).
- A value under a name ending `_file`, `_path` or `_dir` (treated as a path, not a secret), unless a second
  assignment follows it in the match.
- A match spanning more than 9 line breaks across a part boundary (a PEM block, for example), or more than 3 when the
  lines around it are long.
- The default rules' own gaps (stopwords; values starting `+` or `/`), and their CI version: CI runs gitleaks-action's
  8.24.3 with each repository's allowlists, and this gate runs 8.30.1's defaults with none.
- Commit messages and PR bodies are not files: copy them into the scanned directory, or they publish unscanned. Nor
  are paths and ref names, which it never scans (files are staged under flat names): write the pushed file list, the
  branch name, any Release title and tag name, and any issue title and body into a file there too (round 9, R9B1-14;
  round 10, R10B1-14).
- Round 10 (R10B1-03..05), each listed by the line read: a B9 name written as separate words (`pass phrase`, three
  words for the settings key or the web credential) in a label or a table row; an `openssl` password given as a quoted
  `pass:` argument or after `-k`/`-kfile`; the same-line swallow with `:` in place of each `=` (the second-assignment
  test reads only `=`); a path key's bare value that starts at a literal backslash escape inside a JSON string (the
  YAML absorb layout, its line break written `\n`); after an empty path key, a mixed-case value led by `$` (the
  placeholder-assignment skip takes it for a variable); a value wholly inside braces; and, under an env-style name, a
  value that is one run of lowercase letters of any length (the prose skip), or words under a `*_PASSWORD` name.
- Over-reach (round 10, R10B1-06), each cleared with `--accept` after reading: an argv list or tuple that holds a
  path key and a path (`juniper-b9-quoted-pair`), and a compose `environment:` item whose path holds a query-style
  `=`, which now defeats the path skip.
- Round 11 (R11B1-11), outside the line read's contract too unless it prints them: a Kubernetes entry whose `value:`
  comes before its `name:` (the read prints the line above since round 11); `openssl`'s `-k` or `-pass` with the
  value on a continuation line; a `.netrc` line, and a lowercase password key assigned words; and `http.client`'s
  refusal text (`Invalid header value %r`), which quotes a header but is not among the three it reads.
- Round 12 (R12B1-05, R12B1-12): `openssl`'s password as an argv-list item (`"-pass", "pass:…"`, also as
  `CalledProcessError` prints it, and `"-k", "…"`), pkcs12's `-password pass:` and the `Authorization` header (plain, or
  as WSGI's `HTTP_AUTHORIZATION`), each listed by the line read since round 12; scan 1's generic rule finds some of them
  when the value is high-entropy. Outside the line read too: an env-style name with a digit right after its credential
  word (`*_PASSWORD2`), and a kebab-case key (`db-password`) assigned words.

Modes
-----
``--config PATH`` (repeatable): run the canary, then report per-class detection COUNTS for the default rules, the
B9-class rules, and each given config. The planted strings are never printed.

``--scan-dir DIR``: the gate, on scratch COPIES of exactly the files you are about to publish, plus the commit
message and PR body as files; never on a home directory or on transcripts. Run it before EVERY signed upload, because
each upload publishes at once. It cannot scan git history: for that, run ``gitleaks git`` yourself on a fresh
``--mirror`` clone, once per config (``defaults.toml`` and ``b9.toml``, written to --workdir, and the exact config the
repository will ship), with ``--redact``, ``--ignore-gitleaks-allow``, an empty ``--gitleaks-ignore-path``, an
explicit ``--exit-code``, and a report path only the owner can read.

Exit codes
----------
0  clean, or every finding accepted (``--scan-dir``); every probed config detects something (``--config``)
1  a probed config detected nothing (zero-rule)
2  ``--scan-dir`` found something not accepted; each line gives the KEY, never a value
3  the gate could not run or could not be trusted. Treat this as NOT clean.

The scanner is downloaded into ``--workdir`` (a temporary directory by default), never into the repo. Linux x86-64 only.

Usage
-----
    python3 util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --config .gitleaks.toml
    python3 util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py --scan-dir /path/to/scratch/copies [--accept KEY ...]
"""
import argparse
import hashlib
import io
import json
import os
import platform
import random
import re
import shutil
import stat
import string
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

RELEASE = "v8.30.1"
# sha256 of gitleaks_8.30.1_linux_x64.tar.gz, from that release's gitleaks_8.30.1_checksums.txt (read 2026-10-05).
PINNED_SHA256 = {"v8.30.1": "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"}
LEAK_RC = 10  # passed as --exit-code; the scanner exits 1 on its own errors, so 1 must not mean "leaks"
PART_BYTES = 60_000  # parts split here; with LINE_BYTES, no part reaches the scanner's 100,000-byte read chunk
LINE_BYTES = 20_000  # a part is at most 3 carried long lines + 1 line = 80,000 bytes, under 100,000
CARRY_LINES = 9  # lines repeated at the start of the next part, so a match spanning up to 9 line breaks is never cut
CARRY_BYTES = 20_000  # ... as long as they fit in this many bytes
MIN_CARRY_LINES = 3  # ... and never fewer than this, whatever their size (the Name/Value rules span at most 3 breaks)
ALLOW_MARKER = "gitleaks" + ":" + "allow"  # built from parts so this file's own text never carries the marker
ANSI = re.compile(r"\x1b\[[0-9;]*m")
PART_NAME = re.compile(r"\d{5}-\d{3}-[pu]\.txt")

DEFAULTS_CONFIG = """title = "pre-push gate, scan 1 of 2: v8.30.1's default rules, with no repository allowlist"

[extend]
useDefault = true
"""

# --- scan 2: the B9-class rules -------------------------------------------------------------------------------------
# The names are joined at run time, and the canary lines are assembled from parts, so that this file's own text never
# matches its own rules: the gate must pass the PR that carries it without an --accept.
_PASS = "PASS" + "PHRASE"
_KEY = "SETTINGS_" + "ENCRYPTION_KEY"
_SEP = "[_-]*"  # inside a name: `_`, `-` or nothing (SETTINGS_ENCRYPTION_KEY, settings-encryption-key, settingsEncryptionKey)
_NAMES = "(?:" + "|".join(["SETTINGS" + _SEP + "ENCRYPTION" + _SEP + "KEY", _PASS, "DUPLICATI" + _SEP + "WEB" + _SEP + "CREDENTIAL", "WEBSERVICE" + _SEP + "PASSWORD"]) + ")"
_FLAGS = "(?:" + "|".join(["[a-z0-9-]*" + _PASS.lower(), "webservice-" + "password(?:-init)?", "settings-" + "encryption-key"]) + ")"
_SUFFIX = r"(?:[_-][A-Za-z0-9]+)*"
# Values: "double-quoted" or 'single-quoted' (spaces allowed), \"JSON-escaped\", or bare (optionally in backticks);
# 8+ characters. A bare value may start with a backslash, but not with \" (the JSON-escaped form). Every separator
# below is [ \t], never \s: a rule must not cross a line break (round 6, R6A1-01).
_VALUE = r"""(?:"([^"\r\n]{8,})"|'([^'\r\n]{8,})'|\\"([^"\\\r\n]{8,})\\"|`?((?:\\[^\s'"`]|[^\s'"#`\\])[^\s'"`]{7,}))"""
_HASH_VALUE = r"""(#[^\s'"`]{7,})"""  # a value may start with # only right after the separator: `= #x` is a comment
_FLAG_VALUE = r"""(?:"([^"\r\n]{8,})"|'([^'\r\n]{8,})'|`?([^\s'"#`-][^\s'"`]{7,}))"""
# After a name: code spans, **bold**, *italic* and __underscored__ labels, a quoted key (also \"JSON-escaped\"),
# environ["X"], and a parenthesised qualifier ("PASSPHRASE (tier 2):"), then = or : (round 7, R7B1-01; round 8,
# R8B1-05).
_KEY_TAIL = r"""[*_]{0,2}`?\\?['"]?\]?`?[*_]{0,2}(?:[ \t]*\([^()\r\n]{1,40}\))?[*_]{0,2}[ \t]*[:=][*_]{0,2}"""
# A type annotation: any type text up to the first `=`, so unions and nested brackets too (`str | None`, round 8,
# R8B1-01). `passphrase: str = "x"`; `passphrase: str | None = "x"`.
_ANN_TAIL = r"""[ \t]*:[ \t]*[A-Za-z_][^=\r\n]{0,80}?[ \t]*=[ \t]*"""
_GAP = r"[ \t]*(?:(?:\r?\n|\r)[ \t]*){0,3}"  # Name to Value: at most 3 line breaks (a lone CR too), within the carried lines
_Q = r"""\\?["']"""  # a quote, or a JSON-escaped one (JSON stored inside JSON, round 8, R8B1-05)
_ENV_NAME = r"(?:[A-Z][A-Z0-9_]*_)?(?:API_KEYS?|TOKEN|PASSWORD|SECRET)(?:_[A-Z0-9]+)*"
# requests' and h11's refusals and canopy's (round 11, R11B1-14); joined from parts so that this file never quotes one beside a long token
_REFUSALS = "|".join(["in header " + "value:", "illegal header " + "value", "invalid x-api-key " + "header:"])
# Before the key in a refusal text: blanks, and escapes as repr, JSON or HTML write them (round 8, R8B1-04)
_REFUSAL_SKIP = r"""(?:[ \t]|\\{1,2}(?:[nrtfv]|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4})|&#x?[0-9a-fA-F]+;)*"""
# An env-style name, with the wrappers a B9 name may have (code spans, bold, a quoted key, environ["X"]), then `=`
# or `:` with optional blanks around it (round 8, R8B1-06)
_ENV_KEY = r"""[*_]{0,2}`?""" + _ENV_NAME + r"""`?[*_]{0,2}\\?['"]?\]?[ \t]*(?:=|:)[*_]{0,2}[ \t]*"""
_ENV_VALUE = r"""(?:\[[ \t]*\\?["']([^"'\r\n]{8,})\\?["']|"([^"\r\n]{8,})"|'([^'\r\n]{8,})'|([^\s'"#`$][^\s'"`]{7,}))"""

RULES = [
    ("juniper-b9-assignment", "a B9 name, then = or :, then the value", "(?i)" + _NAMES + _SUFFIX + "(?:" + _KEY_TAIL + "|" + _ANN_TAIL + ")(?:" + _HASH_VALUE + r"|[ \t]*" + _VALUE + ")", None),
    # The assignment rule's match can swallow a second assignment on the same line (`X_FILE= PASSPHRASE=v`, or with
    # no blank, or a prefixed `TIER2_PASSPHRASE=v`), and matches never overlap, so this rule finds an assignment that
    # starts right after another one's separator, with any prefix (round 7, R7A-01; round 8, R8A-01).
    # The separator may also be `;`, `,`, `&` or `|` (shell, Helm --set, a URL query; round 8, R8B1-09).
    ("juniper-b9-swallowed", "a B9 assignment right after another assignment's separator, on one line", r"(?i)[:=;,&|][ \t]*[A-Za-z0-9_-]*?" + _NAMES + _SUFFIX + _KEY_TAIL + "(?:" + _HASH_VALUE + r"|[ \t]*" + _VALUE + ")", None),
    ("juniper-b9-cli-flag", "a B9-class flag, a space, then the value", "(?i)--" + _FLAGS + r"[ \t]+" + _FLAG_VALUE, None),
    ("juniper-b9-aescrypt", "an aescrypt command line: the passphrase after d, e or -p", r"(?i)aescrypt(?:\.exe)?[ \t]+(?:-[a-z][ \t]+)*(?:[de]|-p)[ \t]+" + _FLAG_VALUE, None),
    # aescrypt's argv as a list: a source literal, its repr in a log, CalledProcessError's text (round 8, R8B1-02)
    ("juniper-b9-aescrypt-list", "an aescrypt argv list: the passphrase item after d, e or -p", r"""(?i)aescrypt(?:\.exe)?\\?['"][ \t]*,[ \t]*(?:\\?['"]-[a-z]\\?['"][ \t]*,[ \t]*)*\\?['"](?:[de]|-p)\\?['"][ \t]*,[ \t]*\\?['"]([^'"\\\r\n]{8,})\\?['"]""", None),
    # The name cell is a short label: up to 30 characters each side of the name, with a bold, italic or code-span
    # wrapper directly around it, so prose cells that merely mention a name in a code span do not match.
    ("juniper-b9-pipe-cell", "a table or pipe row: a cell naming B9, then the next cell", r"(?im)(?:^|\|)[ \t]*[*_]{0,2}`?[*_]{0,2}[A-Za-z0-9_ ().,/-]{0,30}?" + _NAMES + r"""[A-Za-z0-9_ ().,/-]{0,30}?[*_]{0,2}`?[*_]{0,2}:?[ \t]*\|[ \t]*`?([^\s|`'"]{8,})""", 3.0),
    ("juniper-b9-quoted-pair", "two quoted items, the first naming B9 (argv lists, SQL rows, tuples)", r"""(?i)(?:'[^'\r\n]*""" + _NAMES + r"""[^'\r\n]*'|"[^"\r\n]*""" + _NAMES + r"""[^"\r\n]*")[ \t]*,[ \t]*\\?(?:'([^'\r\n]{8,})'|"([^"\r\n]{8,})")""", None),
    ("juniper-b9-name-value", 'Duplicati settings: "Name" naming B9, then "Value" (JSON or a Python dict)', "(?i)" + _Q + "Name" + _Q + r"[ \t]*:[ \t]*" + _Q + r"""[^"'\r\n]*""" + _NAMES + r"""[^"'\r\n]*""" + _Q + r"[ \t]*," + _GAP + _Q + "Value" + _Q + r"[ \t]*:[ \t]*" + _Q + r"""([^"'\r\n]{8,})""" + _Q, None),
    ("juniper-b9-value-name", 'Duplicati settings: "Value", then "Name" naming B9 (JSON or a Python dict)', "(?i)" + _Q + "Value" + _Q + r"[ \t]*:[ \t]*" + _Q + r"""([^"'\r\n]{8,})""" + _Q + r"[ \t]*," + _GAP + _Q + "Name" + _Q + r"[ \t]*:[ \t]*" + _Q + r"""[^"'\r\n]*""" + _NAMES + r"""[^"'\r\n]*""" + _Q, None),
    # The default rules' separators cross line breaks, so an empty `X_API_KEY_FILE=` line swallows the key below it
    # (round 7, R7B1-02). These line-bounded rules cover this ecosystem's other credential names, in env style, with
    # the wrappers, blanks around `=`, environ["X"] subscripts, JSON-list values and table rows of round 8 (R8B1-03,
    # R8B1-06). A lone CR counts as a boundary (R8B1-15).
    ("juniper-env-credential", "an env-style credential name (*_API_KEY(S), *_TOKEN, *_PASSWORD, *_SECRET), then = or : and the value", r"(?m)(?:^|[^A-Za-z0-9_\n])" + _ENV_KEY + _ENV_VALUE, 3.0),
    ("juniper-env-pipe-cell", "a table or pipe row: a cell holding an env-style credential name, then the next cell", r"(?m)(?:^|\|)[ \t]*[*_]{0,2}`?[*_]{0,2}" + _ENV_NAME + r"""[*_]{0,2}`?[*_]{0,2}:?[ \t]*\|[ \t]*`?([^\s|`'"]{8,})""", 3.0),
    ("juniper-header-refusal", "a refusal text that quotes an API key verbatim (F-S10)", r"(?i)(?:" + _REFUSALS + r""")[ \t]*b?\\?['"]?""" + _REFUSAL_SKIP + r"""([^\s'"\\]{8,})""", None),
]

# Placeholders are skipped only when the WHOLE value has a placeholder shape; names ending _file/_path/_dir hold a path.
_ALLOWLISTS = r"""
[[rules.allowlists]]
description = "placeholder values, as B9 excludes them: whole-value shapes only"
regexTarget = "secret"
regexes = [
    '''^#?\\?<[^<>\s]+\\?>\\?[.,;:)]*$''',
    '''^\$\{?(?:[A-Z][A-Z0-9_]*|[a-z][a-z0-9_]*)\}?[.,;:)]*$''',
    '''^\$\{[A-Za-z_][A-Za-z0-9_]*:?[-?]\}[.,;:)]*$''',
    '''^\{\{\s*[A-Za-z_][A-Za-z0-9_.]*\s*\}\}[.,;:)]*$''',
    '''^%\([A-Za-z_][A-Za-z0-9_]*\)s[.,;:)]*$''',
    '''^%[A-Za-z_][A-Za-z0-9_]*%[.,;:)]*$''',
    '''^(?:\*{3,}|\.{3,}|…+|x{8,}|X{8,})[.,;:)]*$''',
    '''(?i)^(?:redacted|placeholder|changeme|example|your[-_][a-z0-9_-]*?(?:here|key|value|secret|token|pass(?:word|phrase)|credential|name))[.,;:)]*$''',
    '''^(?:[A-Z][A-Z0-9]*_)*@NAMES@(?:_[A-Z0-9]+)*[.,;:)]*$''',
    '''(?i)^@NAMES@[.,;:)]*$''',
    '''^\{[^{}\s]{1,60}\}["'`]?[.,;:)]*$''',
    '''^Field\((?:default=)?None[,)][.,;:)]*$''',
    '''^[*_]{1,2}\([a-z][a-z -]{0,40}\)[*_]{1,2}[.,;:)]*$''',
    '''(?i)^[A-Za-z0-9_-]*(?:@NAMES@|@ENV@)[A-Za-z0-9_-]*[ \t]*[:=][ \t]*(?:#?\\?<[^<>\s]+\\?>|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|\{\{[^}]*\}\}|\{[^{}\s]{1,60}\}|\*{3,}|\.{3,}|…+)["'`]?[.,;:)]*$''',
]

[[rules.allowlists]]
description = "a name ENDING _file, _path or _dir holds a path to the secret, not the secret: the key only, and only when no second assignment follows in the match (round 9, R9B1-01); or such a key whose value is another such assignment"
regexTarget = "match"
regexes = [
    '''(?i)^[|\s`"'*_:=;,&]*[^:=,|"'\s]*?[_-](?:file|path|dir)[*_`"'\]\\]*(?:[ \t]*[:=|]|[ \t]+[/~$.\\])[^=]*$''',
    '''(?i)^[|\s`"'*_:=;,&]*[^:=,|"'\s]*?[_-](?:file|path|dir)[*_`"'\]\\]*[ \t]*[:=][ \t]*[^:=,|"'\s]*?[_-](?:file|path|dir)[*_`"'\]\\]*[ \t]*[:=][^=]*$''',
]
"""

# The env-style rules only: a value of lowercase words joined by hyphens is a table's description cell or a prose word
# after a colon, not a key (round 9, R9B1-11). B9's rules keep such values, since a diceware passphrase looks like one.
_ENV_ALLOWLIST = r"""
[[rules.allowlists]]
description = "env-style rules only: lowercase words joined by hyphens are prose, not a key"
regexTarget = "secret"
regexes = ['''^[a-z]+(?:-[a-z]+)*[.,;:)]*$''']
"""


def _b9_config() -> str:
    parts = ['title = "pre-push gate, scan 2 of 2: interim B9-class rules (no [extend], so no default global allowlist)"\n']
    for rid, desc, regex, entropy in RULES:
        if "'''" in regex:
            raise SystemExit(f"rule {rid}: regex cannot be written as a TOML literal string")
        parts.append(f"\n[[rules]]\nid = \"{rid}\"\ndescription = {json.dumps(desc)}\nregex = '''{regex}'''\n")
        if entropy:
            parts.append(f"entropy = {entropy}\n")
        # a "value" that is itself a B9 name is a regex or a list; one that assigns a placeholder to a name is the
        # swallowed half of an example (`X_FILE= PASSPHRASE=<value>`, round 9's reconciliation)
        parts.append(_ALLOWLISTS.replace("@NAMES@", _NAMES).replace("@ENV@", _ENV_NAME))
        if rid.startswith("juniper-env-"):
            parts.append(_ENV_ALLOWLIST)
    return "".join(parts)


# Canary classes: file name -> content. {v} becomes a fresh random mixed-case value; {v36} a 36-character token.
_EQ = "="
_p = _PASS.lower()
CANARY = {
    "token.txt": 'token = "ghp_{v36}"\n',
    "passphrase.txt": _PASS + _EQ + "{v}\n",
    "prefixed.txt": "TIER2_" + _PASS + _EQ + "{v}\n",
    "suffixed.txt": _KEY + "_OLD" + _EQ + "{v}\n",
    "json-key.json": '{"' + _PASS + '": "{v}"}\n',
    "cli-space.sh": "duplicati-cli backup x --" + _p + " '{v}'\n",
    "dollar-mixed.env": _PASS + _EQ + "$Qz{v}\n",
    "codespan.md": "Set `" + _PASS + _EQ + "{v}` there.\n",
    "true-prefix.env": _PASS + _EQ + "True{v}\n",
    "marker.env": _PASS + _EQ + "{v} # " + ALLOW_MARKER + "\n",
    "table.md": "| Name | Value |\n| --- | --- |\n| " + _PASS + " | {v} |\n",
    "absorb.env": _PASS + "_FILE" + _EQ + "\n" + _PASS + _EQ + "{v}\n",
    "hyphen-flag.sh": "x --settings-" + "encryption-key" + _EQ + "+{v}/\n",
    "camel.json": '{"settings' + 'EncryptionKey": "{v}"}\n',
    "name-value.json": '[{"Name": "' + _p + '",\n  "Value": "{v}"}]\n',
    "option-row.sql": "INSERT INTO \"Option\" VALUES(0,'" + _p + "','{v}');\n",
    "argv.py": 'ARGS = ["--' + _p + '", "{v}"]\n',
    "bold.md": "**" + _PASS.capitalize() + ":** {v}\n",
    "hash-lead.env": _PASS + _EQ + "#{v}\n",
    "sqlite-row.txt": "1|0|" + _p + "|{v}\n",
    # round 7: the same-line swallow, a code-spanned label, the default rules' swallow, F-S10's text, aescrypt's argv
    "same-line.sh": "TIER2_" + _PASS + "_FILE" + _EQ + " TIER2_" + _PASS + _EQ + "{v} run-backup\n",
    "codespan-label.md": "- `" + _PASS + "`: {v}\n",
    "api-key-absorb.env": "JUNIPER_DATA_" + "API_KEY_FILE" + _EQ + "\nJUNIPER_DATA_" + "API_KEY" + _EQ + "{v}\n",
    "header-refusal.log": "Request failed: Invalid leading whitespace in header " + "value: ' {v}'\n",
    "aescrypt.txt": "duplicati-aes" + "crypt d {v} /tmp/x.aes /tmp/x\n",
    # round 8: a PEP 604 annotation, aescrypt's argv as CalledProcessError prints it, a JSON-list env value, and a
    # refusal text inside a JSON body with its line break escaped twice
    "annotated-union.py": "class Job:\n    " + _p + ": str | None = \"{v}\"\n",
    "aescrypt-list.log": "Command '['/usr/lib/duplicati/duplicati-aes" + "crypt', 'd', '{v}', '/tmp/x.aes', '/tmp/x']' returned non-zero exit status 4.\n",
    "api-keys-json.env": "JUNIPER_CASCOR_" + "API_KEYS" + _EQ + "[\"{v}\"]\n",
    "header-refusal-json.json": "{\"detail\": \"Request failed: Invalid leading whitespace in header " + "value: ' \\\\n{v}'\"}\n",
    # round 9: the swallow behind a YAML key (R9B1-01), and one class each for the env table and Value-then-Name
    # rules (R9B1-16)
    "yaml-command.yml": "command: TIER2_" + _PASS + "_FILE" + _EQ + " TIER2_" + _PASS + _EQ + "{v} run-backup\n",
    "env-table.md": "| JUNIPER_CASCOR_" + "TOKEN | {v} |\n",
    "value-name.json": '[{"Value": "{v}",\n  "Name": "' + _p + '"}]\n',
}


class GateError(Exception):
    """The scan could not run, or its result cannot be trusted."""


class _Parser(argparse.ArgumentParser):
    def error(self, message):  # argparse would exit 2, which this tool reserves for "found something"
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(3)


def fetch_scanner(workdir: Path, run: Path, tag: str, expected: str) -> Path:
    """Verify the shared release tarball against the pin on every run; extract the binary into this run's directory."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise GateError(f"unsupported platform {platform.system()}/{platform.machine()}: this tool fetches the linux_x64 build")
    name = f"gitleaks_{tag.lstrip('v')}_linux_x64.tar.gz"
    tarball = workdir / name
    if not tarball.exists():
        url = f"https://github.com/gitleaks/gitleaks/releases/download/{tag}/{name}"
        tmp = run / (name + ".part")
        tmp.write_bytes(urllib.request.urlopen(url, timeout=120).read())  # nosec B310 — fixed https URL
        os.replace(tmp, tarball)
    data = tarball.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise GateError(f"{name}: sha256 {digest} does not match the pinned {expected}")
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        member = next((m for m in tf.getmembers() if m.isfile() and m.name.rsplit("/", 1)[-1] == "gitleaks"), None)
        if member is None:
            raise GateError(f"{name} holds no scanner binary")
        payload = tf.extractfile(member).read()
    binpath = run / f"scanner-{tag}"
    binpath.write_bytes(payload)
    binpath.chmod(0o755)
    return binpath


def _reading(data: bytes):
    """Return the text to scan for one file, or None if it is not UTF-8 text this gate can scan reliably.

    A UTF-16 or UTF-32 byte-order mark is refused outright (round 7, R7B1-08): behind one, a file can carry a second
    encoding that no single reading sees, and no file in six checkouts starts with one. Convert it to UTF-8 first.
    """
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or data[:4] == b"\x00\x00\xfe\xff":
        return None
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    return None if "\x00" in text else text


def _carry(chunk: list) -> list:
    """The lines repeated at the start of the next part: up to CARRY_LINES that fit in CARRY_BYTES, never fewer than MIN_CARRY_LINES."""
    carry, total = [], 0
    for piece in reversed(chunk[-CARRY_LINES:]):
        if len(carry) >= MIN_CARRY_LINES and total + len(piece) > CARRY_BYTES:
            break
        carry.insert(0, piece)
        total += len(piece)
    return carry


def stage(source: Path, staging: Path) -> tuple:
    """Copy every file under `source` into flat, overlapping text parts. Return (mapping, staged bytes, file count)."""
    problems, mapping, index = [], {}, 0
    staging.mkdir(parents=True)

    def walk_error(err):
        problems.append(f"cannot read {err.filename}: {err.strerror}")

    for root, dirs, files in os.walk(source, followlinks=False, onerror=walk_error):
        for d in dirs:
            full = os.path.join(root, d)
            if os.path.islink(full):
                problems.append(f"symlinked directory {Path(full).relative_to(source)}")
            elif not os.access(full, os.R_OK | os.X_OK):
                problems.append(f"unreadable directory {Path(full).relative_to(source)}")
        for f in sorted(files):
            path = Path(root, f)
            rel = os.fsdecode(path.relative_to(source))
            mode = os.lstat(path).st_mode
            if stat.S_ISLNK(mode):
                problems.append(f"symlink {rel}")
                continue
            if not stat.S_ISREG(mode):
                problems.append(f"not a regular file: {rel}")
                continue
            text = _reading(path.read_bytes())  # an unreadable file raises, which is exit 3
            if text is None:
                problems.append(f"not UTF-8 text (binary, archive, NUL, or a UTF-16/32 byte-order mark): {rel}")
                continue
            index += 1
            text = text.replace("\r\n", "\n")
            if "\n" not in text:  # a CR-only file: split at its CRs. Otherwise lines are numbered by LF, as sed numbers them
                text = text.replace("\r", "\n")
            lines = text.split("\n")
            part, first, chunk, size, carried = 0, 1, [], 0, 0
            for n, line in enumerate(lines, 1):
                piece = (line + ("\n" if n < len(lines) else "")).encode("utf-8")
                if len(piece) > LINE_BYTES:
                    problems.append(f"line {n} of {rel} is over {LINE_BYTES} bytes")
                    break
                if size + len(piece) > PART_BYTES and len(chunk) > carried:
                    name = f"{index:05d}-{part:03d}-u.txt"
                    (staging / name).write_bytes(b"".join(chunk))
                    mapping[name] = (rel, first)
                    carry = _carry(chunk)
                    part, first, chunk, size, carried = part + 1, n - len(carry), list(carry), sum(len(c) for c in carry), len(carry)
                chunk.append(piece)
                size += len(piece)
            name = f"{index:05d}-{part:03d}-u.txt"
            (staging / name).write_bytes(b"".join(chunk))
            mapping[name] = (rel, first)
    if problems:
        raise GateError("cannot scan reliably — " + "; ".join(problems[:20]) + (" …" if len(problems) > 20 else ""))
    if index == 0:
        raise GateError(f"{source} holds no files")
    return mapping, sum(p.stat().st_size for p in staging.iterdir()), index


def run_scan(binpath: Path, staging: Path, run: Path, config: Path, staged_bytes: int, mapping: dict) -> list:
    """One scanner run over the staging directory. Raise GateError unless it is a trustworthy clean or leaks result."""
    report = run / "report.json"
    if report.exists():
        report.unlink()
    no_ignore = run / "empty-ignore-dir"
    no_ignore.mkdir(exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITLEAKS_")}
    base = [str(binpath), "dir", str(staging), "--config", str(config), "--no-banner", "--redact", "--ignore-gitleaks-allow", "--gitleaks-ignore-path", str(no_ignore), "--exit-code", str(LEAK_RC), "--report-format", "json", "--report-path", str(report)]
    proc = subprocess.run(base, capture_output=True, text=True, env=env, cwd=str(no_ignore), timeout=900)  # nosec B603 — fixed argv, no shell
    log = ANSI.sub("", proc.stderr)
    if proc.returncode not in (0, LEAK_RC):
        raise GateError(f"scanner exited {proc.returncode} (expected 0 or {LEAK_RC}): {' | '.join(log.strip().splitlines()[-3:])}")
    scanned = re.search(r"scanned ~(\d+) bytes", log)
    if not scanned or int(scanned.group(1)) != staged_bytes:
        debug = subprocess.run(base[:-4] + ["--log-level", "debug"], capture_output=True, text=True, env=env, cwd=str(no_ignore), timeout=900)  # nosec B603
        skipped = sorted({mapping.get(m, ("?",))[0] for line in ANSI.sub("", debug.stderr).splitlines() if "skip" in line.lower() for m in PART_NAME.findall(line)})
        raise GateError(f"scanner read {scanned.group(1) if scanned else 'an unknown number of'} bytes of the {staged_bytes} staged; skipped: {skipped or 'unknown'} (text starting like a binary format, e.g. PDF, ZIP, ELF or SQLite, is skipped by type; if nothing was read, check that the --workdir path matches none of the default config's global path allowlists, e.g. 'gitleaks.toml' or 'node_modules/')")
    if not report.exists():
        raise GateError("scanner wrote no report")
    try:
        findings = json.loads(report.read_text())
    except ValueError as exc:
        raise GateError(f"report is not JSON: {exc}") from None
    if not isinstance(findings, list):
        raise GateError("report is not a JSON list")
    if (proc.returncode == LEAK_RC) != bool(findings):
        raise GateError(f"exit code {proc.returncode} disagrees with {len(findings)} reported finding(s)")
    return findings


def gate(binpath: Path, source: Path, run: Path, configs: dict, tag: str) -> dict:
    """Stage `source`, run every config over it, and return {KEY: (rel path, line, scan name)}."""
    staging = run / f"staged-{tag}"
    if staging.exists():
        shutil.rmtree(staging)
    mapping, staged_bytes, _ = stage(source, staging)
    texts = {}
    out = {}
    for cname, cfg in configs.items():
        for f in run_scan(binpath, staging, run, cfg, staged_bytes, mapping):
            part = Path(f.get("File", "")).name
            rel, first = mapping[part]
            if part not in texts:
                texts[part] = (staging / part).read_text(encoding="utf-8").split("\n")
            start, end = int(f.get("StartLine", 1)), int(f.get("EndLine", f.get("StartLine", 1)))
            digest = hashlib.sha256("\n".join(texts[part][start - 1:end]).encode("utf-8")).hexdigest()[:10]
            line = first + start - 1
            lines = f"{line}" if end <= start else f"{line}-{first + end - 1}"  # the value can sit on the last line (R7B1-04)
            out[f"{rel}:{lines}:{f.get('StartColumn', 0)}:{f.get('RuleID', '?')}:{digest}"] = (rel, line, cname)
    return out


def plant(directory: Path) -> None:
    directory.mkdir(parents=True)
    alnum = string.ascii_letters + string.digits
    for name, template in CANARY.items():
        value = "Qz7" + "".join(random.choices(alnum, k=21)) + "Mk"  # nosec B311 — synthetic fakes; mixed case by construction
        token = "".join(random.choices(alnum, k=36))  # nosec B311
        (directory / name).write_text(template.replace("{v36}", token).replace("{v}", value))
    (directory / ".gitleaksignore").write_text("token.txt:github-pat:1\n")  # must NOT be honoured


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    ap = _Parser(description=__doc__.splitlines()[1])
    ap.add_argument("--config", action="append", default=[], help="gitleaks config to probe (repeatable)")
    ap.add_argument("--scan-dir", action="append", help="directory of scratch copies to gate (give it once)")
    ap.add_argument("--accept", action="append", default=[], metavar="KEY", help="a finding read and judged not a credential, exactly as printed (repeatable)")
    ap.add_argument("--workdir", help="where to keep the verified scanner tarball (default: a temporary directory)")
    ap.add_argument("--release", default=RELEASE, help=f"scanner release tag (default and only pinned: {RELEASE})")
    ap.add_argument("--sha256", help="expected tarball sha256 for a --release other than the pinned one")
    args = ap.parse_args()
    if args.scan_dir is not None:
        if len(args.scan_dir) != 1:  # a second --scan-dir used to replace the first silently (round 7, R7B1-06)
            ap.error("give --scan-dir once: copy everything to be published into one directory")
        args.scan_dir = args.scan_dir[0]
        if not args.scan_dir.strip():
            ap.error("--scan-dir is empty")
    if not args.config and args.scan_dir is None:
        ap.error("give --config and/or --scan-dir")
    zero_rule = found_something = False
    run = None
    try:
        workdir = (Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="leakprobe-"))).resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        run = Path(tempfile.mkdtemp(prefix="run-", dir=workdir))  # one directory per run (round 6, R6A1-07)
        expected = PINNED_SHA256.get(args.release) or args.sha256
        if not expected:
            raise GateError(f"no pinned sha256 for {args.release}; pass --sha256 from that release's checksums file")
        binpath = fetch_scanner(workdir, run, args.release, expected)
        print(f"scanner {args.release}: tarball sha256 verified against the pin")
        configs = {"defaults": run / "defaults.toml", "b9": run / "b9.toml"}
        configs["defaults"].write_text(DEFAULTS_CONFIG)
        configs["b9"].write_text(_b9_config())
        for name in ("defaults.toml", "b9.toml"):  # the history-scan configs, for XC-LEAKS step 1
            shutil.copyfile(run / name, workdir / name)
        canary_dir = run / "canary"
        plant(canary_dir)
        hits = gate(binpath, canary_dir, run, configs, "canary")
        missed = [k for k in CANARY if not any(v[0] == k for v in hits.values())]
        print(f"canary (the gate: defaults + B9-class): {len(CANARY) - len(missed)} of {len(CANARY)} planted classes found")
        if missed:
            raise GateError(f"the gate missed planted class(es) {missed}; nothing it reports can be trusted")
        if args.config:
            for label, cfgs in (("default rules only", {"defaults": configs["defaults"]}), ("B9-class rules only", {"b9": configs["b9"]})):
                h = gate(binpath, canary_dir, run, cfgs, "probe")
                print(f"{label:32}: {sum(1 for k in CANARY if any(v[0] == k for v in h.values()))} of {len(CANARY)} classes")
            for cfg in args.config:
                h = gate(binpath, canary_dir, run, {"given": Path(cfg).resolve()}, "probe")
                n = sum(1 for k in CANARY if any(v[0] == k for v in h.values()))
                print(f"{cfg:32}: {n} of {len(CANARY)} classes", "-> ZERO-RULE (detects nothing)" if not n else "")
                zero_rule = zero_rule or not n
        if args.scan_dir is not None:
            target = Path(args.scan_dir).resolve()
            if not target.is_dir():
                raise GateError(f"--scan-dir {target} is not a directory")
            hits = gate(binpath, target, run, configs, "target")
            accepted = {a.strip() for a in args.accept}
            stale = sorted(accepted - set(hits))
            if stale:
                raise GateError(f"--accept names no current finding (stale, edited or mistyped): {stale}")
            open_keys = sorted(k for k in hits if k not in accepted)
            print(f"scan-dir: {len(hits)} finding(s) in {len({v[0] for v in hits.values()})} file(s); {len(hits) - len(open_keys)} accepted after review; {len(open_keys)} open")
            for key in sorted(hits):
                print(f"  {'ACCEPTED' if key in accepted else 'OPEN    '} {key}  ({hits[key][2]} scan)")
            found_something = bool(open_keys)
    except Exception as exc:  # noqa: BLE001 — any failure (GateError, network, timeout, I/O) means the gate did not run
        print(f"GATE ERROR (treat as NOT clean): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    finally:
        if run is not None:
            shutil.rmtree(run, ignore_errors=True)  # staged copies of the scanned files go with it
    return 2 if found_something else (1 if zero_rule else 0)


if __name__ == "__main__":
    sys.exit(main())
