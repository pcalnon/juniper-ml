#!/usr/bin/env python3
"""
Regression cases for the pre-push gate in util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py (--scan-dir mode).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-05
Status: ad-hoc — regression suite for an interim gate
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (XC-PRESERVE method);
         reports/2026-10-04_consolidated-development-plan/round4-*.md .. round11-*.md (where each case came from)

Every case is generated at run time in a temporary directory from SYNTHETIC random values (nothing is read from the
repository or the host), run through the gate, and checked: the exit code, and for some cases the reported lines.
The names are assembled from parts so that this file's own text passes the gate. Cases come from validation rounds
4-7 of the plan above (R4B-01; R5A-01/02/04/05/06; R5B-02/03; R6A1-01..11; R7A-01..03; R7B1-01..09) and from
round 7's reconciliation (a backslash-led value, and the escaped placeholder that must still pass), and from round 8
(R8A-01: the prefixed and no-blank same-line swallows; R8B1-*: as each case's comment says). Round 9 added nine
swallow layouts (R9B1-01), seven must-pass cases (R9B1-01, R9B1-11 and its reconciliation's placeholder example) and
the line read's check (`names`); round 10 added the line read's contract check (`contract`: R10A-01, R10A-02, R10B1-02,
R10B1-03, R10B1-05, R10B1-07), and round 11 widened it to the read's four-clause contract and its control: whole lines
with the line above, any short separator in a name, punctuation masked, lines numbered as the gate numbers them, the
refusals, and `--all` over the listed limits (R11A-02, R11A-08, R11A-10, R11B1-01..04, R11B1-07, R11B1-08,
R11B1-11). Its reconciliation checked that the contract check catches each of 23 mutants of the read. Round 12
found 22 more that survived both checks (R12A-01, R12B1-01..04) and a read that printed credential words in clear
(R12A-02, R12B1-06); its reconciliation added one case per survivor, a check that no printed line shows any
character in clear but blanks, KEY mode's whole lines and refusals, and keeps the mutation run as
util/ad-hoc/2026-10-08_line_read_mutation_run.py.

Usage
-----
    python3 util/ad-hoc/2026-10-05_gate_regression.py [--workdir DIR] [--only SUBSTRING]
Exit 0 when every case behaves as expected; 1 otherwise.
"""
import argparse
import base64
import os
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

GATE = Path(__file__).resolve().parent / "2026-10-04_gitleaks_zero_rule_probe.py"
P = "PASS" + "PHRASE"
p = P.lower()
K = "SETTINGS_" + "ENCRYPTION_KEY"
W = "DUPLICATI_" + "WEB_CREDENTIAL"
EQ = "="
MARK = "gitleaks" + ":" + "allow"


def v(n=24):
    return "Qz7" + "".join(random.choices(string.ascii_letters + string.digits, k=n - 5)) + "Mk"


def vd():
    """Like v(), but 24 distinct characters, so its entropy is always log2(24), about 4.58 bits.

    The line read calls a token random-looking at 4.0 bits or more, and about 4% of v()'s values fall below that, so
    a check that wants random-looking=1 on a v() value fails by chance (it did once, on 2026-10-08).
    """
    pool = [ch for ch in string.ascii_letters + string.digits if ch not in "Qz7Mk"]
    return "Qz7" + "".join(random.sample(pool, 19)) + "Mk"


def b64(lead):
    while True:
        s = base64.b64encode(os.urandom(48)).decode()
        if s[0] == lead:
            return s


def text_cases():
    """(name, {relpath: str or bytes}, expected exit, {relpath: expected line} or None)."""
    c = []
    one = lambda name, rel, body, line=1: c.append((name, {rel: body}, 2, {rel: line}))  # noqa: E731
    # round 5's matrix: formats juniper-ml writes
    one("env", "a.env", f"# x\n{P}{EQ}{v()}\n", 2)
    one("yaml", "a.yaml", f"backup:\n  {p}: {v()}\n", 2)
    one("ini", "a.ini", f"[backup]\n{p} = {v()}\n", 2)
    one("json-key", "a.json", '{\n  "' + P + '": "' + v() + '"\n}\n', 2)
    one("python-dict", "a.py", 'E = {"' + P + '": "' + v() + '", "HOME": "/x"}\n')
    one("python-environ", "a.py", 'import os\nos.environ["' + P + '"] = "' + v() + '"\n', 2)
    one("cli-space", "a.sh", f"duplicati-cli backup x --{p} '{v()}'\n")
    one("cli-eq", "a.sh", f"duplicati-cli backup x --{p}{EQ}{v()}\n")
    one("ws-init", "a.txt", "--webservice-" + "password-init" + EQ + v() + "\n")
    one("ws-init-symbols", "a.txt", "--webservice-" + "password-init" + EQ + "Gm8!XrT3@qWp6%ZvN9kLc4Hb\n")
    one("key-old", "a.env", f"{K}_OLD{EQ}{v()}\n")
    one("dollar-letter", "a.env", f"{P}{EQ}$Rk{v()}\n")
    one("bash-default", "a.sh", f'{P}="${{BACKUP_{P}:-{v()}}}"\n')
    one("hash-inside", "a.env", f"{P}{EQ}Kx9#{v()}\n")
    one("hash-lead", "a.env", f"{P}{EQ}#{v()}\n")
    one("diceware-short-first", "a.env", f'{P}="maple quartz violet lantern harbor"\n')
    one("suffix-new", "a.env", f"{P}_NEW{EQ}{v()}\n")
    one("true-prefix", "a.env", f"{P}{EQ}TrueNorth{v()}\n")
    one("false-infix", "a.env", f"{P}{EQ}Pc2VxFalse{v()}\n")
    one("null-suffix", "a.env", f"{P}{EQ}{v()}Null\n")
    one("changeme-prefix", "a.env", "webservice-" + "password" + EQ + "Changeme2026" + v() + "\n")
    one("md-table", "a.md", f"| Name | Value |\n| --- | --- |\n| {P} | {v()} |\n", 3)
    one("md-table-words", "a.md", f"| Setting | Value |\n| --- | --- |\n| Backup {p} (tier 2) | {v()} |\n", 3)
    one("md-codespan", "a.md", f"Set `{P}{EQ}{v()}` in the file.\n")
    one("md-bold", "a.md", f"**{P.capitalize()}:** {v()}\n")
    one("hidden-dir", ".config/d/params.txt", f"--{p}{EQ}{v()}\n")
    one("deep-path", "a/b/c/d/e/f.conf", f"{p} {EQ} {v()}\n")
    one("systemd", "a.service", f'[Service]\nEnvironment="{K}{EQ}{v()}"\n', 2)
    one("compose", "c.yml", f"services:\n  d:\n    environment:\n      - {P}{EQ}{v()}\n", 4)
    one("toml-quoted", "a.toml", f'[env]\n"{P}" = "{v()}"\n', 2)
    one("server-pp", "a.txt", f"server-{p}{EQ}{v()}\n")
    one("dunder", "a.env", f"DUPLICATI__{p}{EQ}{v()}\n")
    one("new-pp-cli", "a.sh", f"duplicati-cli change-{p} x --new-{p}{EQ}{v()}\n")
    one("pdf-named", "a.pdf", f"{P}{EQ}{v()}\n")
    one("percent-prefix", "a.env", f"{P}{EQ}%Tq{v()}\n")
    one("yaml-quoted-key", "a.yaml", f'env:\n  "{P}": {v()}\n', 2)
    one("camel", "a.json", '{"settings' + 'EncryptionKey": "' + v() + '"}\n')
    # round 6: an empty name ending _FILE/_PATH/_DIR must not swallow the next line (R6A1-01)
    one("absorb-env", "a.env", f"{P}_FILE{EQ}\n{P}{EQ}{v()}\n", 2)
    one("absorb-yaml", "a.yaml", f"{p}_file:\n{p}: {v()}\n", 2)
    one("absorb-blank-lines", "a.env", f"{P}_FILE{EQ}\n\n\n{P}{EQ}{v()}\n", 4)
    one("absorb-webcred", "a.env", f"{W}_FILE{EQ}\n{W}{EQ}{v()}\n", 2)
    one("absorb-quoted-words", "a.yaml", f'{p}_dir:\n{p}: "maple quartz violet lantern"\n', 2)
    one("empty-then-tier2", "a.env", f"{P}{EQ}\nTIER2_{P}{EQ}{v()}\n", 2)
    one("value-holds-dir-eq", "a.env", f"{P}{EQ}abc_dir{EQ}{v()}\n")
    # round 6: the ecosystem's own flag form and base64 keys (R6A1-02)
    one("settings-flag-plus", "a.sh", f"x --settings-encryption-key{EQ}{b64('+')}\n")
    one("settings-flag-slash", "a.sh", f"x --settings-encryption-key{EQ}{b64('/')}\n")
    one("settings-flag-space", "a.sh", f"x --settings-encryption-key {b64('+')}\n")
    # round 6: structured forms (R6A1-05)
    one("name-value", "a.json", '[{"Name": "' + p + '", "Value": "' + v() + '"}]\n')
    one("name-value-pretty", "a.json", '[\n  {\n    "Name": "' + p + '",\n    "Value": "' + v() + '"\n  }\n]\n', 3)
    one("value-name", "a.json", '[{"Value": "' + v() + '", "Name": "' + p + '"}]\n')
    one("option-row", "a.sql", "INSERT INTO \"Option\" VALUES(0,'" + p + "','" + v() + "');\n")
    one("sqlite-row", "a.txt", f"1|0|{p}|{v()}\n")
    one("argv", "a.py", 'ARGS = ["--' + p + '", "' + v() + '"]\n')
    # inline allow markers hide nothing
    one("marker-exact", "a.env", f"{P}{EQ}{v()} # {MARK}\n")
    one("marker-upper", "a.env", f"{P}{EQ}{v()} # {MARK.upper()}\n")
    # encodings and line endings (R6A1-06). A UTF-16 or UTF-32 byte-order mark is refused (exit 3) since round 7
    # (R7B1-08): behind one, a file can carry a second encoding that no single reading sees.
    one("utf8-bom", "a.env", ("\ufeff" + f"x\n{P}{EQ}{v()}\n").encode("utf-8"), 2)
    c.append(("utf16le-bom", {"a.env": f"x\n{P}{EQ}{v()}\n".encode("utf-16")}, 3, None))
    c.append(("utf16be-bom", {"a.env": b"\xfe\xff" + f"x\n{P}{EQ}{v()}\n".encode("utf-16-be")}, 3, None))
    c.append(("bom-then-ascii", {"a.env": b"\xff\xfe" + f"{P}{EQ}{v()}\n".encode()}, 3, None))
    c.append(("bom-be-then-ascii", {"a.env": b"\xfe\xff" + f"{P}{EQ}{v()}\n".encode()}, 3, None))
    c.append(("utf32-bom", {"a.env": f"x\n{P}{EQ}{v()}\n".encode("utf-32")}, 3, None))
    c.append(("bom-utf16-then-utf8", {"a.env": "x\n".encode("utf-16") + f"{P}{EQ}{v()}\n".encode()}, 3, None))
    c.append(("bom-then-latin1", {"a.env": b"\xff\xfe" + f"caf\xe9 {P}{EQ}{v()}\n".encode("latin-1")}, 3, None))
    one("cr-only", "a.env", f"x\r{P}{EQ}{v()}\r", 2)
    one("crlf", "a.env", f"x\r\n{P}{EQ}{v()}\r\n", 2)
    one("lone-cr-numbered-by-lf", "a.log", f"a\rb\r{P}{EQ}{v()}\nok\n", 1)  # R7B1-04: sed -n 1p shows it
    # R7B1-04: a multi-line match names START-END, so a reviewer reads the value's line too
    c.append(("multiline-key-range", {"a.json": '[\n  {\n    "Name": "' + p + '",\n    "Value": "' + v() + '"\n  }\n]\n'}, 2, {"a.json": "3-4"}))
    # round 7: the same-line swallow (R7A-01), Markdown labels (R7B1-01), the default rules' swallow (R7B1-02),
    # F-S10's refusal texts (R7B1-03), shapes outside the old limits (R7B1-05), and the path skip (R7A-03)
    one("same-line-swallow", "a.sh", f"{P}_FILE{EQ} {P}{EQ}{v()} run-backup\n")
    one("same-line-webcred", "a.env", f"{W}_FILE{EQ} {W}{EQ}{v()}\n")
    one("md-codespan-colon", "a.md", f"- `{P}`: {v()}\n")
    one("md-codespan-value", "a.md", f"- `TIER2_{P}`: `{v()}`\n")
    one("md-codespan-eq", "a.md", f"`{W}` {EQ} {v()}\n")
    one("md-bold-codespan", "a.md", f"**`{P}_OLD`**: {v()}\n")
    one("md-table-bold", "a.md", f"| **{P}** | {v()} |\n")
    one("md-table-italic", "a.md", f"| *{p}* | {v()} |\n")
    one("md-table-colon", "a.md", f"| {p.capitalize()}: | {v()} |\n")
    one("md-table-bold-codespan", "a.md", f"| **`{K}`** | `{v()}` |\n")
    one("md-underscored-label", "a.md", f"__{p.capitalize()}:__ {v()}\n")
    one("qualifier-label", "a.md", f"{P} (tier 2): {v()}\n")
    one("bold-qualifier-label", "a.md", f"**{p.capitalize()} (old):** {v()}\n")
    api = "JUNIPER_DATA_" + "API_KEY"
    one("api-key-absorb", "a.env", f"{api}_FILE{EQ}\n{api}{EQ}{v()}\n", 2)
    one("api-key-absorb-canopy", "a.env", f"JUNIPER_CANOPY_{api}{EQ}\nJUNIPER_CASCOR_API_KEY{EQ}{v()}\n", 2)
    refusal = "in header " + "value:"
    one("header-refusal-502", "a.json", '{"detail": "Request failed: Invalid leading whitespace ' + refusal + " ' " + v() + "'\"}\n")
    one("header-refusal-bytes", "a.log", "Illegal header " + "value b' " + v() + "\\n'\n")
    one("header-refusal-canopy", "a.log", "invalid X-API-Key " + "header: " + v() + "\n")
    one("value-holds-name", "a.env", f"TIER2_{P}{EQ}maple-quartz-{p}-2026\n")
    one("aescrypt-ps", "a.txt", "duplicati-aes" + f"crypt d {v()} /tmp/x.aes /tmp/x\n")
    one("aescrypt-p", "a.sh", "aes" + f"crypt -e -p {v()} x.tar\n")
    one("python-repr-setting", "a.py", "{'Name': '" + p + "', 'Value': '" + v() + "'}\n")
    one("json-escaped-quotes", "a.json", '{"cmd": "x --' + p + EQ + '\\"' + v() + '\\""}\n')
    one("annotated-default", "a.py", f'{p}: str {EQ} "{v()}"\n')
    one("flag-dir-in-value", "a.sh", f"x --{p} maple-dir-quartz-{v()}\n")
    # the round-7 reconciliation: v5's first draft refused a bare value starting with a backslash
    one("backslash-lead", "a.sh", f"{P}{EQ}\\{v()}\n")
    # round 8 (R8A-01): the same-line swallow with a prefixed second name, or with no blank after the separator
    one("swallow-prefixed", "a.sh", f"TIER2_{P}_FILE{EQ} TIER2_{P}{EQ}{v()} run-backup\n")
    one("swallow-plain-then-prefixed", "a.env", f"{P}_FILE{EQ} TIER2_{P}{EQ}{v()}\n")
    one("swallow-dunder", "a.env", f"DUPLICATI__{P}_FILE{EQ} DUPLICATI__{P}{EQ}{v()}\n")
    one("swallow-export-path", "a.sh", f"export TIER2_{P}_PATH{EQ} TIER2_{P}{EQ}{v()}\n")
    one("swallow-no-blank", "a.env", f"TIER2_{P}_FILE{EQ}TIER2_{P}{EQ}{v()}\n")
    # round 8, Lane B1: shapes this ecosystem writes that v5 passed with exit 0
    one("ann-union-field", "a.py", f'class Job:\n    {p}: str | None {EQ} "{v()}"\n', 2)  # R8B1-01
    one("ann-union-constant", "a.py", f'TIER2_{P}: str | None {EQ} "{v()}"\n')
    one("ann-union-field-call", "a.py", f'{p}: str | None {EQ} Field(default{EQ}"{v()}")\n')
    aes = "duplicati-aes" + "crypt"
    one("aescrypt-list-repr", "a.log", f"INFO argv{EQ}['/usr/lib/duplicati/{aes}', 'd', '{v()}', '/tmp/x.aes', '/tmp/x']\n")  # R8B1-02
    one("aescrypt-list-called-process-error", "a.log", f"Command '['/usr/lib/duplicati/{aes}', 'd', '{v()}', '/tmp/x.aes', '/tmp/x']' returned non-zero exit status 4.\n")
    one("aescrypt-list-json", "a.json", f'["/usr/bin/{aes}", "-d", "-p", "{v()}", "x.aes"]\n')
    keys = "API_" + "KEYS"
    one("api-keys-json-list", "a.env", f'JUNIPER_CASCOR_{keys}{EQ}["{v()}"]\n')  # R8B1-03
    one("api-keys-json-list-two", "a.env", f'JUNIPER_DATA_{keys}{EQ}["{v()}","{v()}"]\n')
    hv = "in header " + "value:"
    one("refusal-json-newline", "a.json", '{"detail": "Request failed: Invalid leading whitespace ' + hv + " ' \\\\n" + v() + "'\"}\n")  # R8B1-04
    one("refusal-json-tab", "a.json", '{"detail": "Request failed: Invalid leading whitespace ' + hv + " '\\\\t" + v() + "'\"}\n")
    one("refusal-json-crlf", "a.json", '{"detail": "Request failed: Invalid leading whitespace ' + hv + " '\\\\r\\\\n" + v() + "'\"}\n")
    one("refusal-repr-nbsp", "a.log", "WARNING Request failed: " + hv + " '\\xa0" + v() + "'\n")
    one("refusal-bytes-vt", "a.log", "Illegal header " + "value b'\\x0b" + v() + "'\n")
    one("refusal-html", "a.html", "<div>Request failed: " + hv + " &#x27; " + v() + "&#x27;</div>\n")
    one("escaped-json-environ", "a.json", '{"source": ["os.environ[\\"' + P + '\\"] ' + EQ + ' \\"' + v() + '\\"\\n"]}\n')  # R8B1-05
    one("escaped-json-name-value", "a.log", '{"msg": "{\\"Name\\":\\"--' + p + '\\",\\"Value\\":\\"' + v() + '\\"}"}\n')
    one("escaped-json-argv", "a.log", '{"msg": "[\\"--' + p + '\\", \\"' + v() + '\\"]"}\n')
    one("escaped-json-dict", "a.ipynb", '{"cells": [{"source": ["job = {\\"' + p + '\\": \\"' + v() + '\\"}\\n"]}]}\n')
    one("escaped-json-embedded", "a.json", '{"body": "{\\"settings\\": {\\"' + p + '\\": \\"' + v() + '\\"}}"}\n')
    api = "JUNIPER_DATA_" + "API_KEY"
    one("env-environ-subscript", "conftest.py", f'os.environ["{api}"] {EQ} "{v()}"\n')  # R8B1-06
    one("env-table-row", "a.md", f"| {api} | {v()} |\n")
    one("env-codespan-label", "a.md", f"- `{api}`: {v()}\n")
    one("env-bold-label", "a.md", f"**{api}:** {v()}\n")
    one("env-spaced-swallow", "a.env", f"{api}_FILE {EQ} \n{api} {EQ} {v()}\n", 2)
    one("swallow-semicolon", "a.sh", f"{P}_FILE{EQ}/run/x;{P}{EQ}{v()}\n")  # R8B1-09
    one("swallow-comma", "a.sh", f"helm upgrade x --set {p}_file{EQ}/run/x,{p}{EQ}{v()}\n")
    one("swallow-ampersand", "a.txt", f"https://x.invalid/?{p}_file{EQ}/run/x&{p}{EQ}{v()}\n")
    one("your-diceware", "a.env", f"{P}{EQ}Your-maple-quartz-violet\n")  # R8B1-13
    one("key-file-label-row", "a.md", f"| Key-file {p} | {v()} |\n")
    one("key-file-flag", "a.txt", f"x --key-file-{p} {v()}\n")
    one("lone-cr-env-swallow", "a.env", f"{api}_FILE{EQ}\r{api}{EQ}{v()}\nok\n")  # R8B1-15
    one("lone-cr-name-value", "a.json", '[{"Name": "' + p + '",\r  "Value": "' + v() + '"}]\nok\n')
    # round 9 (R9B1-01): the swallow when the _FILE key itself follows a separator; the path skip used to drop the
    # whole match, the real assignment with it
    one("swallow-after-cd", "a.sh", f"cd /srv/backup;{P}_FILE{EQ}/run/x;{P}{EQ}{v()}\n")
    one("swallow-in-set-list", "a.sh", f"helm upgrade x --set image.tag{EQ}1.2,{p}_file{EQ}/run/x,{p}{EQ}{v()}\n")
    one("swallow-after-query", "a.txt", f"https://x.invalid/?a{EQ}1&{p}_file{EQ}/run/x&{p}{EQ}{v()}\n")
    one("swallow-empty-after-mode", "a.sh", f"MODE{EQ}full;{P}_FILE{EQ};{P}{EQ}{v()}\n")
    one("swallow-systemd-env", "a.service", f"Environment{EQ}TIER2_{P}_FILE{EQ}/run/x TIER2_{P}{EQ}{v()}\n")
    one("swallow-after-and", "a.sh", f"cd /srv/backup&&{P}_FILE{EQ} {P}{EQ}{v()} run-backup\n")
    one("swallow-after-mode-blank", "a.sh", f"MODE{EQ}full; {P}_FILE{EQ} {P}{EQ}{v()} run-backup\n")
    one("swallow-in-table-cell", "a.md", f"| x | {P}_FILE{EQ} {P}{EQ}{v()} run-backup |\n")
    one("swallow-yaml-command", "a.yml", f"command: TIER2_{P}_FILE{EQ} TIER2_{P}{EQ}{v()} run-backup\n")
    # part boundaries (R7A-02, R7B1-09): a match spanning 4 line breaks, and a Name/Value pair spanning 3, each with
    # the 60,000-byte boundary falling between key and value; the carried lines must keep each whole.
    # 1,153 filler lines of 52 bytes put the boundary just before each value line. The default rule allows at most 5
    # whitespace characters after `:`, and its stopwords can drop a random word-like value, so that value has no vowel.
    filler = "".join(f"filler line {i:06d} of an ordinary log, plain text..\n" for i in range(1, 1154))
    novowel = "".join(random.choices("0123456789QZXJKVBCDFGHLMNPRST", k=40))
    c.append(("default-gap-boundary", {"g.yml": filler + "api_key:\n\n\n\n\n" + novowel + "\n"}, 2, None))
    c.append(("name-value-gap-boundary", {"g.json": filler + '[{"Name": "' + p + '",\n\n\n  "Value": "' + v(40) + '"}]\n'}, 2, None))
    # chunk boundaries: many lines without blank lines, and one planted deep in a large file
    many = "".join(f"{P}{EQ}{v()}\n" for _ in range(3000))
    c.append(("chunk-3000", {"many.log": many}, 2, None))
    filler = "".join(f"line {i} of an ordinary log, nothing to see\n" for i in range(1, 60001))
    c.append(("deep-line", {"big.log": filler + f"{P}{EQ}{v()}\n"}, 2, {"big.log": 60001}))
    # clean cases
    c.append(("placeholders", {"a.md": f"Set `{P}{EQ}<your-{p}-here>`.\nThe `{P}{EQ}`/`{K}{EQ}` lines.\n{P}{EQ}$PASSFILE_VALUE or {K}{EQ}${{KEY_FROM_FILE}}.\n{P}{EQ}${{X:-}}\n"}, 0, None))
    c.append(("path-names", {"a.env": f"{P}_FILE{EQ}/run/credentials/juniper/{p}\n{K}_PATH{EQ}/etc/juniper/key\n"}, 0, None))
    c.append(("ignore-file-baseline", {".gitleaksignore": "abc123:docs/x.md:generic-api-key:12\n", ".github/workflows/ci.yml": "on: push\n"}, 0, None))
    c.append(("marker-in-prose", {"a.md": f"The gate passes `--ignore-{MARK.replace(':', '-')}`; a `{MARK}` comment hides nothing.\n"}, 0, None))
    c.append(("your-placeholder", {"a.env": f"{P}{EQ}your-{p}-here\n{K}{EQ}your_settings_key\n"}, 0, None))
    c.append(("env-path", {"a.md": "JUNIPER_DATA_" + f"API_KEY_FILE: /run/credentials/juniper/data-key\n| JUNIPER_DATA_" + "API_KEY_FILE | /run/credentials/juniper/data-key |\n"}, 0, None))
    c.append(("path-after-separator",{"a.env": f"X{EQ}{P}_FILE{EQ}/run/credentials/juniper/{p}\nenvironment: {P}_FILE: /run/credentials/juniper/{p}\nTIER2_{P}_FILE{EQ} TIER2_{P}_PATH{EQ}/run/credentials/juniper/tier2\n"}, 0, None))
    c.append(("md-escaped-placeholder",{"a.md": f"Run `x --{p}{EQ}\\<your-{p}\\> --settings-encryption-key{EQ}\\<key-here\\>`.\n"}, 0, None))
    # round 9: a path key after a separator still passes (R9B1-01's fix must not report it), and ordinary prose and code
    # that v6 reported (R9B1-11)
    c.append(("path-after-cd", {"a.sh": f"cd /x; {P}_FILE{EQ}/run/credentials/juniper/{p}\nEnvironment{EQ}{P}_FILE{EQ}/run/credentials/juniper/{p}\n"}, 0, None))
    api = "JUNIPER_DATA_" + "API_KEY"
    c.append(("env-table-description", {"a.md": f"| {api} | set-by-the-owner |\n"}, 0, None))
    c.append(("env-label-prose", {"a.md": "- `JUNIPER_CASCOR_" + "TOKEN`: assignments, labels and table rows\n"}, 0, None))
    c.append(("field-default-none", {"a.py": f"{p}: str | None {EQ} Field(default{EQ}None)\n"}, 0, None))
    c.append(("format-placeholder", {"a.py": 'print(f"' + P + EQ + '{value}")\n'}, 0, None))
    c.append(("italic-cell", {"a.md": "| **" + P.capitalize() + "** | *(required)* |\n"}, 0, None))
    # round 9's reconciliation: once the path skip stopped dropping a match with a second assignment, an example whose
    # second value is a placeholder was reported; its swallowed half is an assignment of a placeholder
    c.append(("swallow-placeholder-example", {"a.md": f"`TIER2_{P}_FILE{EQ} TIER2_{P}{EQ}<random>` and `{api}_FILE{EQ} {api}{EQ}<random>`\n"}, 0, None))
    return c


def error_cases(root: Path):
    """(name, setup(dir) -> extra args, expected exit). Each must exit 3."""
    def missing(d):
        return ["--scan-dir", str(d / "nope")]

    def empty(d):
        (d / "e").mkdir()
        return ["--scan-dir", str(d / "e")]

    def symlink_file(d):
        (d / "s").mkdir()
        (d / "t.env").write_text(f"{P}{EQ}{v()}\n")
        os.symlink(d / "t.env", d / "s" / "l.env")
        return ["--scan-dir", str(d / "s")]

    def symlink_dir(d):
        (d / "s").mkdir()
        (d / "t").mkdir()
        (d / "t" / "x.env").write_text(f"{P}{EQ}{v()}\n")
        (d / "s" / "ok.md").write_text("clean\n")
        os.symlink(d / "t", d / "s" / "linked")
        return ["--scan-dir", str(d / "s")]

    def gz(d):
        import gzip
        (d / "s").mkdir()
        (d / "s" / "x.log.gz").write_bytes(gzip.compress(f"{P}{EQ}{v()}\n".encode()))
        return ["--scan-dir", str(d / "s")]

    def sqlite_magic(d):
        (d / "s").mkdir()
        (d / "s" / "x.db").write_bytes(b"SQLite format 3\x00" + f"{P}{EQ}{v()}\n".encode())
        return ["--scan-dir", str(d / "s")]

    def pdf_signature(d):
        (d / "s").mkdir()
        (d / "s" / "x.txt").write_text(f"%PDF-1.7\n{P}{EQ}{v()}\n")
        return ["--scan-dir", str(d / "s")]

    def utf16_no_bom(d):
        (d / "s").mkdir()
        (d / "s" / "x.env").write_bytes(f"{P}{EQ}{v()}\n".encode("utf-16-le"))
        return ["--scan-dir", str(d / "s")]

    def latin1(d):
        (d / "s").mkdir()
        (d / "s" / "x.env").write_bytes(f"caf\xe9\n{P}{EQ}{v()}\n".encode("latin-1"))
        return ["--scan-dir", str(d / "s")]

    def utf16_nul(d):
        (d / "s").mkdir()
        (d / "s" / "x.env").write_bytes(f"a\x00b\n{P}{EQ}{v()}\n".encode("utf-16"))
        return ["--scan-dir", str(d / "s")]

    def mode000_file(d):
        (d / "s").mkdir()
        (d / "s" / "ok.md").write_text("clean\n")
        (d / "s" / "x.env").write_text(f"{P}{EQ}{v()}\n")
        os.chmod(d / "s" / "x.env", 0)
        return ["--scan-dir", str(d / "s")]

    def mode_dir(mode):
        def setup(d):
            (d / "s" / "sub").mkdir(parents=True)
            (d / "s" / "ok.md").write_text("clean\n")
            (d / "s" / "sub" / "x.env").write_text(f"{P}{EQ}{v()}\n")
            os.chmod(d / "s" / "sub", mode)
            return ["--scan-dir", str(d / "s")]
        return setup

    def long_line(d):
        (d / "s").mkdir()
        (d / "s" / "x.min.js").write_text("a" * 25000 + "\n")
        return ["--scan-dir", str(d / "s")]

    def workdir_file(d):
        (d / "s").mkdir()
        (d / "s" / "ok.md").write_text("clean\n")
        (d / "f").write_text("not a directory\n")
        return ["--scan-dir", str(d / "s"), "--workdir", str(d / "f")]

    def empty_scan_dir(d):
        return ["--config", str(GATE), "--scan-dir", ""]

    def unpinned(d):
        (d / "s").mkdir()
        (d / "s" / "ok.md").write_text("clean\n")
        return ["--scan-dir", str(d / "s"), "--release", "v8.29.0"]

    def repeat_scan_dir(d):  # R7B1-06: a second --scan-dir used to replace the first silently
        (d / "s1").mkdir()
        (d / "s1" / "x.env").write_text(f"{P}{EQ}{v()}\n")
        (d / "s2").mkdir()
        (d / "s2" / "ok.md").write_text("clean\n")
        return ["--scan-dir", str(d / "s1"), "--scan-dir", str(d / "s2")]

    def stale_accept(d):
        (d / "s").mkdir()
        (d / "s" / "ok.md").write_text("clean\n")
        return ["--scan-dir", str(d / "s"), "--accept", "ok.md:1:1:juniper-b9-assignment:0000000000"]

    return [("missing-dir", missing), ("empty-dir", empty), ("symlink-file", symlink_file), ("symlink-dir", symlink_dir),
            ("gzip", gz), ("sqlite-magic", sqlite_magic), ("pdf-signature-text", pdf_signature), ("utf16-no-bom", utf16_no_bom),
            ("latin1", latin1), ("utf16-with-nul", utf16_nul), ("mode000-file", mode000_file), ("mode000-dir", mode_dir(0)),
            ("mode0311-dir", mode_dir(0o311)), ("long-line", long_line), ("workdir-is-file", workdir_file),
            ("empty-scan-dir", empty_scan_dir), ("unpinned-release", unpinned), ("stale-accept", stale_accept),
            ("repeat-scan-dir", repeat_scan_dir)]


def run_gate(args, workdir):
    cmd = [sys.executable, str(GATE)] + args
    if "--workdir" not in args:
        cmd += ["--workdir", str(workdir)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    keys = re.findall(r"^  (?:OPEN    |ACCEPTED) (\S+)", proc.stdout, re.M)
    return proc.returncode, keys, proc.stdout + proc.stderr


def write_case(base: Path, files: dict):
    for rel, body in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            path.write_bytes(body)
        else:
            path.write_text(body)


def restore(d: Path):
    for root, dirs, files in os.walk(d):
        for name in dirs + files:
            try:
                os.chmod(os.path.join(root, name), 0o700)
            except OSError:
                pass  # best effort: restore() only reopens modes so the scratch tree can be removed


SHAPE = Path(__file__).resolve().parent / "2026-10-05_masked_finding_shape.py"


def names_check(base: Path):
    """The line read, `--names` (round 9: R9A-06, R9B1-02, R9B1-08, R9B1-09, R9B1-10). Returns (ok, why)."""
    api = "JUNIPER_DATA_" + "API_KEY"
    vals = {k: v() for k in ("bare", "dunder", "prefixed", "header", "openssl")}
    vals.update({k: vd() for k in ("k8s", "argv")})  # checked for random-looking=1 below
    keepwords, accented = "the-old-new-value-of-the-key", "Äpfel-Öl-Übermaß-straße"
    files = {
        "k8s.yaml": f"env:\n  - name: {api}\n    value: \"{vals['k8s']}\"\n",
        "argv.py": 'cmd = [\n    "duplicati-aes' + 'crypt",\n    "d",\n    "' + vals["argv"] + '",\n]\n',
        "names.env": ("API_" + f"KEY{EQ}{vals['bare']}\n" + "SETTINGS__ENCRYPTION__" + f"KEY{EQ}{vals['dunder']}\n"
                      + "db_pass" + f'word {EQ} "{vals["prefixed"]}"\n' + "X-API-" + f"Key: {vals['header']}\n"
                      + "openssl enc -pass " + f"pass:{vals['openssl']}\n"),
        "masking.env": f"{P}{EQ}{keepwords}\n{P}{EQ}{accented}\n",
        "control.txt": "an ordinary line with nothing to read\n",
    }
    write_case(base, files)
    cmd = [sys.executable, str(SHAPE), "--root", str(base), "--names"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    out = proc.stdout
    if proc.returncode != 0:
        return False, f"exit {proc.returncode}"
    if any(s in out for s in list(vals.values()) + [keepwords, accented]):
        return False, "a planted value is in the output"
    blocks, cur = {}, None
    for line in out.splitlines():
        if line.startswith("    below "):
            blocks.setdefault(cur, []).append(line)
        else:
            cur = line.split(" ", 1)[0]
            blocks.setdefault(cur, [])
    want = ["k8s.yaml:2", "argv.py:2", "names.env:1", "names.env:2", "names.env:3", "names.env:4", "names.env:5",
            "masking.env:1", "masking.env:2"]
    missing = [w for w in want if w not in blocks]
    if missing or any(k.startswith("control.txt") for k in blocks):
        return False, f"listed wrongly: missing {missing}"
    if not any("below L3 random-looking=1" in b for b in blocks["k8s.yaml:2"]):
        return False, "the value below the k8s name was not printed"
    if not any("below L4 random-looking=1" in b for b in blocks["argv.py:2"]):
        return False, "the argv item below the marker was not printed"
    refusals = {"symlink": None, "nul": None, "mode000": None}
    for kind in refusals:
        d = base.parent / f"names-refuse-{kind}"
        (d / "s").mkdir(parents=True)
        (d / "s" / "ok.md").write_text("clean\n")
        if kind == "symlink":
            (d / "t.env").write_text(f"{P}{EQ}{v()}\n")
            os.symlink(d / "t.env", d / "s" / "l.env")
        elif kind == "nul":
            (d / "s" / "x.env").write_bytes(f"{P}{EQ}{v()}\n".encode("utf-16-le"))
        else:
            (d / "s" / "sub").mkdir()
            (d / "s" / "sub" / "x.env").write_text(f"{P}{EQ}{v()}\n")
            os.chmod(d / "s" / "sub", 0)
        r = subprocess.run([sys.executable, str(SHAPE), "--root", str(d / "s"), "--names"], capture_output=True, text=True, timeout=120)
        restore(d)
        refusals[kind] = r.returncode
    if any(rc != 3 for rc in refusals.values()):
        return False, f"refusals {refusals} (want 3 each)"
    return True, ""


def _masked(text: str) -> str:
    """The read's class masking, written out here independently, so the check does not trust the read's own code."""
    def cls(tok):
        if not tok.isascii():
            return f"<N{len(tok)}>"
        if tok.isdigit():
            return f"<D{len(tok)}>"
        if tok.isupper():
            return f"<U{len(tok)}>"
        if tok.islower():
            return f"<l{len(tok)}>"
        return f"<M{len(tok)}>"
    # letters and digits by class and length; since round 11's reconciliation, any other non-blank run by its length
    return re.sub(r"[^\W_]+|(?:[^\w\s]|_)+", lambda m: cls(m.group(0)) if m.group(0)[0].isalnum() else f"<P{len(m.group(0))}>", text)


def _by_file(out: str) -> dict:
    """The read's --names output, grouped by file: each entry with the lines printed above and below it."""
    groups, pending, cur = {}, [], None
    for line in out.splitlines():
        if line.startswith("    above "):
            pending.append(line)
        elif line.startswith("    below "):
            groups.setdefault(cur, []).append(line)
        elif ":" in line.split(" ", 1)[0]:
            cur = line.split(" ", 1)[0].rsplit(":", 1)[0]
            groups.setdefault(cur, []).extend(pending + [line])
            pending = []
    return groups


def _content(line: str) -> str:
    """What a read output line prints of the file: the text after its `random-looking=N: ` prefix."""
    m = re.search(r" random-looking=\d+: (.*)$", line)
    return m.group(1) if m else ""


def _clear(line: str) -> str:
    """Whatever an output line prints in clear: its content with every mask tag removed and blanks dropped. Clause 3
    since round 12: nothing prints in clear but blanks, names included (R12A-02, R12B1-06)."""
    return re.sub(r"\s+", "", re.sub(r"<[UlMDNP]\d+>", "", _content(line)))


def _gate_lines(data: bytes) -> list:
    """A file's lines as the gate numbers them, written out here independently of the read."""
    text = data.decode("utf-8").replace("\r\n", "\n")
    if "\n" not in text:
        text = text.replace("\r", "\n")
    return text.split("\n")


def contract_check(base: Path, workdir: Path):
    """The line read's contract, as its docstring states it (rounds 10 to 12). Returns (ok, why).

    Every listed line prints whole, with the nearest non-blank line above it and the five non-blank lines below it;
    every run of letters, digits and other characters is masked on every printed line, names included, so nothing
    prints in clear but blanks; names with any short separator, every env-style name and every marker are listed;
    lines are numbered as the gate numbers them; KEY mode prints its range's lines whole with the finding's offset; and
    the read refuses what it cannot read, by lstat, without printing the input's bytes (R10A-01, R10A-02, R10B1-02,
    R10B1-03, R10B1-05, R10B1-07; R11A-02, R11A-08, R11A-10, R11B1-01..04, R11B1-07, R11B1-08, R11B1-11; R12A-01,
    R12A-02, R12A-14, R12B1-01..06, R12B1-10..12). Each case added in round 12 names the mutant it pins.
    """
    api = "JUNIPER_DATA_" + "API_KEY"
    tier2 = "TIER2_" + P
    v = {k: vd() for k in ("comment", "qualifier", "gap", "namevalue", "argv", "two", "three", "web", "quoted", "k",
                           "deep4", "deep5", "above", "pem", "auth", "tab", "dotted", "websvc", "cr", "k8sname",
                           "lim_above2", "lim_below6", "lim_split", "lim_cont", "lim_netrc", "lim_passcont", "lim_digit",
                           "token", "secret", "sep3", "soft", "nbh", "apikeys", "openssh", "pkcs8", "gapbelow", "deepgap",
                           "abovegap", "nasym", "argvpass", "argvcpe", "argvk", "pkcs12", "wsgi", "lim_http")}
    words = {k: "quantum-velvet-harbor-mosaic-" + w for k, w in
             [("table", "alpha"), ("envtable", "bravo"), ("longjson", "delta"), ("oneline", "golf"), ("dotkey", "kilo"),
              ("lim_lowerkey", "lima"), ("lim_kebab", "mike")]}
    lower = "".join(random.sample(string.ascii_lowercase, 24))
    lower18 = "".join(random.sample(string.ascii_lowercase, 18))
    tails = {k: vd() for k in ("secret", "lowerkey", "uptoken")}
    keepwords = "the-old-new-value-of-the-key"
    long_cell = "a long description of what this setting does and why the operator needs it, kept in one cell"
    # punctuation printed as it was: a value made of it, and half of one that alternates letters with symbols (R11B1-02)
    punct = "".join(random.sample("!#$%&()*+,-./:;<=>?@[]^{|}~", 24))
    marks = "!#$%&*+?@^~"  # none of them in the read's tags, its entry fields or the name
    alnum = random.sample(string.ascii_letters + string.digits, 13)
    symbols = "".join(a + random.choice(marks) for a in alnum[:12]) + alnum[12]
    # round 12's values: all digits (X16, C3a), runs of non-ASCII letters (X19), non-ASCII symbols inside a value (C3b),
    # words joined by double underscores (C3c), a hex key and a UUID (R12B1-11)
    digits = "".join(random.choices(string.digits, k=20))
    nonascii = "-".join("".join(random.choices("äöüßéèñçøåÄÖÜ", k=8)) for _ in range(3))
    nasym = v["nasym"][:10] + "€±" + v["nasym"][10:]
    under = "__".join("".join(random.sample(string.ascii_lowercase, 6)) for _ in range(3))
    hexkey, uid = os.urandom(32).hex(), str(uuid.uuid4())
    # values that are or contain a credential word, which printed in clear when names' words did (R12A-02, R12B1-06)
    tok, sec = "TOK" + "EN", "SEC" + "RET"
    credvals = ["Pass" + "phrase" + "".join(random.choices(string.digits, k=4)) + "!", "blue-pass" + "phrase-river",
                "blue-" + tok + "-river", sec, "pass_" + "phrase!!", "ab" + "Pass" + "phrase7"]
    pk = "PRIVATE " + "KEY-----"
    files = {
        # round 10: values below a name that has trailing text, or several lines down
        "k8s-comment.yaml": f"env:\n  - name: {api}  # rotated\n    value: \"{v['comment']}\"\n",
        "label-qualifier.md": "**Pass" + "phrase** (tier 2):\n\n" + v["qualifier"] + "\n",
        "k8s-gap.yaml": f"env:\n  - name: {api}\n    # rotated by the owner\n    # see the runbook\n    value: \"{v['gap']}\"\n",
        "name-value-gap.json": '{"Name": "--pass' + 'phrase",\n "Filter": "",\n "Argument": "",\n "Value": "' + v["namevalue"] + '"}\n',
        "argv-comment.py": 'cmd = [\n    "duplicati-aes' + 'crypt",  # the tool\n    "d",\n    "' + v["argv"] + '",\n]\n',
        "blank-names.md": ("**Pass" + " phrase:** " + v["two"] + "\n\n| Settings" + " encryption" + " key | " + v["three"]
                           + " |\n\n**Duplicati" + " web" + " credential:** " + v["web"] + "\n"),
        "openssl.sh": ("openssl enc -aes-256-cbc -pass '" + "pass:" + v["quoted"] + "' -in a -out b\n"
                       + "openssl enc -aes-256-cbc -k " + v["k"] + " -in a -out b\n"),
        "lower.env": f"{api}={lower}\n",
        "suffix.yaml": ("client: \"abc123_sec" + "ret_" + tails["secret"] + "\"\ntoken: \"jd_api_" + "key_" + tails["lowerkey"]
                        + "\"\nX=PROD_TO" + "KEN_" + tails["uptoken"].upper() + "\n"),
        "value-first.json": '{"Value": "' + keepwords + '", "Name": "pass' + 'phrase"}\n',
        # round 11: values past a window, or on a line that is itself listed (R11B1-01)
        "table-desc.md": "| **Pass" + "phrase** | " + long_cell + " | " + words["table"] + " |\n",
        "env-table.md": "| `" + api + "` | " + long_cell + " | " + words["envtable"] + " |\n",
        "below-long.json": '{"Name": "--pass' + 'phrase",\n' + " " * 245 + '"Value": "' + words["longjson"] + '"}\n',
        "k8s-comment-name.yaml": f"env:\n  - name: {api}\n    value: \"{v['k8sname']}\"  # the {tier2} one\n",
        "json-oneline.json": '{"Name": "--pass' + 'phrase", "Description": "' + long_cell + '", "Value": "' + words["oneline"] + '"}\n',
        # the depth of the contract (R11B1-07): the 4th and 5th non-blank lines below, and the line above (R11B1-11)
        "deep4.yaml": f"env:\n  - name: {api}\n    # a\n    # b\n    # c\n    value: \"{v['deep4']}\"\n",
        "deep5.yaml": f"env:\n  - name: {api}\n    # a\n    # b\n    # c\n    # d\n    value: \"{v['deep5']}\"\n",
        "value-above.yaml": f"env:\n  - value: \"{v['above']}\"\n    name: {api}\n",
        # round 12: NON-BLANK lines, below and above (X11, X12, C2a, C2b)
        "gap-below.md": "**Pass" + "phrase:**\n" + "\n" * 5 + v["gapbelow"] + "\n",
        "deep-gap.yaml": f"env:\n  - name: {api}\n    # a\n\n    # b\n\n\n    value: \"{v['deepgap']}\"\n",
        "above-gap.yaml": f"env:\n  - value: \"{v['abovegap']}\"\n\n    name: {api}\n",
        # markers and names the contract lists (R11B1-04, R11B1-07)
        "pem.txt": "-----BEGIN RSA " + pk + "\n" + v["pem"] + "\n",
        "refusals.log": ("requests said: in header " + "value: ' x'\n" + "h11 said: Illegal header " + "value b' x'\n"
                         + "canopy said: invalid x-api-key " + "header: x\n"),
        "kfile.sh": "openssl enc -aes-256-cbc -kfile ./key.bin -in a -out b\n",
        "auth.txt": "Authori" + "zation: Bearer " + v["auth"] + "\n",
        "tab-name.md": "Pass\t" + "phrase: " + v["tab"] + "\n",
        "dotted.properties": "settings.encryption." + "key=" + words["dotkey"] + "\npass.phrase=" + v["dotted"] + "\n",
        "websvc.md": "**Web service pass" + "word:** " + v["websvc"] + "\n",
        "lower18.env": f"{api}={lower18}\n",
        "punct.env": f"{api}: {punct}\n",
        "symbols.env": f"{api}={symbols}\n",
        # round 12, clause 1: env words (X3, X4, C1c, C1d), separators (C1a, C1b), PEM kinds (C1e), and openssl's
        # argv-list spellings, -password and the WSGI header (R12B1-05)
        "token.env": "JUNIPER_CASCOR_" + tok + "=" + v["token"] + "\n",
        "secret.env": "APP_" + sec + "=" + v["secret"] + "\n",
        "apikeys.json": '{"JUNIPER_API_' + 'KEYS": ["' + v["apikeys"] + '"]}\n',
        "sep3.md": "**Pass – " + "phrase:** " + v["sep3"] + "\n",
        "soft-hyphen.md": "Pass­" + "phrase: " + v["soft"] + "\n",
        "nb-hyphen.md": "Pass‑" + "phrase: " + v["nbh"] + "\n",
        "pem-openssh.txt": "-----BEGIN OPENSSH " + pk + "\n" + v["openssh"] + "\n",
        "pem-pkcs8.txt": "-----BEGIN " + pk + "\n" + v["pkcs8"] + "\n",
        "argv-pass.py": 'cmd = ["openssl", "enc", "-pass", "' + "pass:" + v["argvpass"] + '", "-in", "x"]\n',
        "argv-cpe.log": "Command '['openssl', 'enc', '-pass', '" + "pass:" + v["argvcpe"] + "']' returned non-zero exit status 1.\n",
        "argv-k.py": 'cmd = ["openssl", "enc", "-k", "' + v["argvk"] + '", "-in", "x"]\n',
        "pkcs12.sh": "openssl pkcs12 -export -pass" + "word " + "pass:" + v["pkcs12"] + " -out x\n",
        "wsgi.env": "HTTP_AUTHORI" + "ZATION=Bearer " + v["wsgi"] + "\n",
        # round 12, clause 3: values in clear only as blanks (X16, X19, C3a, C3b, C3c, R12A-02, R12B1-06); hex (R12B1-11)
        "digits.env": f"{api}={digits}\n",
        "nonascii.env": f"{api}={nonascii}\n",
        "nonascii-sym.env": f"{api}={nasym}\n",
        "underscored.env": f"{api}={under}\n",
        "credwords.env": "".join(f"{api}={c}\n" for c in credvals),
        "hex.env": f"{api}: {hexkey}\nX-API-" + f"Key: {uid}\n",  # after a blank, where the 4.0-bit test scores 0
        # listed limits, outside the contract, whose control is --all (R11B1-11, R12A-14, R12B1-12): a value two lines
        # above its name or six below it, a name split across lines, openssl's -k or -pass on a continuation line, a
        # .netrc line, a lowercase key assigned words, http.client's refusal text, a digit after the word, kebab-case
        "limit-above2.yaml": f"env:\n  - value: \"{v['lim_above2']}\"\n    # c\n    name: {api}\n",
        "limit-below6.yaml": f"env:\n  - name: {api}\n" + "".join(f"    # {c}\n" for c in "abcde") + f"    value: \"{v['lim_below6']}\"\n",
        "limit-split.md": "**Pass\n" + "phrase:** " + v["lim_split"] + "\n",
        "limit-cont.sh": "openssl enc -aes-256-cbc \\\n  -k " + v["lim_cont"] + " -in a -out b\n",
        "limit-passcont.sh": "openssl enc -aes-256-cbc -pass \\\n  " + "pass:" + v["lim_passcont"] + " -in a -out b\n",
        "limit-netrc.txt": "machine example.com login me pass" + "word " + v["lim_netrc"] + "\n",
        "limit-lowerkey.yaml": "pass" + "word: " + words["lim_lowerkey"] + "\n",
        "limit-httpclient.log": "http.client said: Invalid header " + "value b'" + v["lim_http"] + "'\n",
        "limit-digit.env": "DB_PASS" + "WORD2=" + v["lim_digit"] + "\n",
        "limit-kebab.yaml": "db-pass" + "word: " + words["lim_kebab"] + "\n",
    }
    write_case(base, files)
    (base / "cr-only.yaml").write_bytes(f"env:\r  - name: {api}\r    # c\r    value: \"{v['cr']}\"\r".encode())
    planted = (list(v.values()) + list(words.values()) + [lower, lower18, keepwords, tails["uptoken"].upper(), punct, symbols,
               digits, nasym, under, hexkey, uid] + list(tails.values()) + nonascii.split("-") + credvals)
    outs = {}
    for mode in ("--names", "--all"):
        proc = subprocess.run([sys.executable, str(SHAPE), "--root", str(base), mode], capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            return False, f"{mode}: exit {proc.returncode}"
        outs[mode] = proc.stdout
        if any(s in proc.stdout for s in planted) or "old-new" in proc.stdout:
            return False, f"{mode}: a planted value is in the output"
        # clause 3, on every printed line of every file: nothing in clear but blanks, names included (round 12)
        clear = [line.split(" ", 1)[0] for line in proc.stdout.splitlines() if _clear(line)]
        if clear:
            return False, f"{mode}: {len(clear)} line(s) print characters in clear, the first {clear[0]}"
    groups = _by_file(outs["--names"])
    # each value prints, masked, among the lines printed for its file
    shown = {"k8s-comment.yaml": v["comment"], "label-qualifier.md": v["qualifier"], "k8s-gap.yaml": v["gap"],
             "name-value-gap.json": v["namevalue"], "argv-comment.py": v["argv"], "table-desc.md": words["table"],
             "env-table.md": words["envtable"], "below-long.json": words["longjson"], "k8s-comment-name.yaml": v["k8sname"],
             "json-oneline.json": words["oneline"], "deep4.yaml": v["deep4"], "deep5.yaml": v["deep5"],
             "value-above.yaml": v["above"], "pem.txt": v["pem"], "auth.txt": v["auth"], "tab-name.md": v["tab"],
             "dotted.properties": words["dotkey"], "websvc.md": v["websvc"], "cr-only.yaml": v["cr"],
             "punct.env": punct, "symbols.env": symbols,
             "gap-below.md": v["gapbelow"], "deep-gap.yaml": v["deepgap"], "above-gap.yaml": v["abovegap"],
             "token.env": v["token"], "secret.env": v["secret"], "apikeys.json": v["apikeys"], "sep3.md": v["sep3"],
             "soft-hyphen.md": v["soft"], "nb-hyphen.md": v["nbh"], "pem-openssh.txt": v["openssh"],
             "pem-pkcs8.txt": v["pkcs8"], "argv-pass.py": v["argvpass"], "argv-cpe.log": v["argvcpe"],
             "argv-k.py": v["argvk"], "pkcs12.sh": v["pkcs12"], "wsgi.env": v["wsgi"], "digits.env": digits,
             "nonascii.env": nonascii, "nonascii-sym.env": nasym, "underscored.env": under, "hex.env": hexkey}
    for name, value in shown.items():
        if not any(_masked(value) in line for line in groups.get(name, [])):
            return False, f"{name}: its value did not print, masked"
    if any(ch in line for line in groups.get("symbols.env", []) for ch in marks):
        return False, "symbols.env: a symbol of the value printed"
    if any(ch in line for line in groups.get("nonascii-sym.env", []) for ch in "€±"):
        return False, "nonascii-sym.env: a non-ASCII symbol of the value printed"
    # --all, the listed limits' control: every line of every file, masked (a mutant that emptied it passed every check)
    every = {}
    for line in outs["--all"].splitlines():
        every.setdefault(line.split(" ", 1)[0].rsplit(":", 1)[0], []).append(line)
    for name, content in files.items():
        if len(every.get(name, [])) != len(content.split("\n")):
            return False, f"--all: {name} printed {len(every.get(name, []))} of its {len(content.split(chr(10)))} lines"
    limits = {"limit-above2.yaml": v["lim_above2"], "limit-below6.yaml": v["lim_below6"], "limit-split.md": v["lim_split"],
              "limit-cont.sh": v["lim_cont"], "limit-passcont.sh": v["lim_passcont"], "limit-netrc.txt": v["lim_netrc"],
              "limit-lowerkey.yaml": words["lim_lowerkey"], "limit-httpclient.log": v["lim_http"],
              "limit-digit.env": v["lim_digit"], "limit-kebab.yaml": words["lim_kebab"]}
    for name, value in list(shown.items()) + list(limits.items()):
        if not any(_masked(value) in line for line in every.get(name, [])):
            return False, f"--all: {name}'s value did not print, masked"
    # --all counts random-looking tokens on its lines too: row q selects on that count (Xrl, R12B1-11)
    if not every.get("auth.txt") or "random-looking=1" not in every["auth.txt"][0]:
        return False, "--all: auth.txt:1 not counted random-looking"
    # listed lines, with their random-looking values counted
    listed_want = ["blank-names.md:1", "blank-names.md:3", "blank-names.md:5", "openssl.sh:1", "openssl.sh:2", "lower.env:1",
                   "auth.txt:1", "tab-name.md:1", "dotted.properties:2", "websvc.md:1", "lower18.env:1",
                   "token.env:1", "secret.env:1", "apikeys.json:1", "sep3.md:1", "soft-hyphen.md:1", "nb-hyphen.md:1",
                   "argv-pass.py:1", "argv-cpe.log:1", "argv-k.py:1", "pkcs12.sh:1", "wsgi.env:1", "hex.env:1", "hex.env:2"]
    entries = {line.split(" ", 1)[0]: line for line in outs["--names"].splitlines() if not line.startswith("    ")}
    for entry in listed_want:
        if "random-looking=1" not in entries.get(entry, ""):
            return False, f"{entry}: not listed with its random-looking value"
    for entry in ["dotted.properties:1", "pem.txt:1", "pem-openssh.txt:1", "pem-pkcs8.txt:1", "refusals.log:1",
                  "refusals.log:2", "refusals.log:3", "kfile.sh:1", "gap-below.md:1", "deep-gap.yaml:2", "above-gap.yaml:4",
                  "cr-only.yaml:2"]:  # a file with no LF is split at its CRs, as the gate splits it
        if entry not in entries:
            return False, f"{entry}: not listed"
    # KEY mode: bytes after multibyte text (R10A-02), a line with lone CRs numbered by LF (R11B1-03), and, since round
    # 12, every line of the key's range whole and masked, checked against lines numbered and masked here, with the
    # offset at the name (R12B1-10), and a two-line Name/Value key whose value is on its second line (C3g)
    case = base.parent / "contract-keymode"
    nv = vd()
    write_case(case, {"c.md": "intro\n" + "—" * 12 + " " + P + "=" + keepwords + "\n",
                      "b.md": "intro\nthe-old-new prose " + P + "=" + vd() + " | " + long_cell + "\n",  # past any window
                      "nv.json": '[\n  {\n    "Name": "' + p + '",\n    "Value": "' + nv + '"\n  }\n]\n'})
    (case / "lone-cr.log").write_bytes(("a\rb\r" + P + "=" + vd() + "\n").encode())
    rc, keys, _ = run_gate(["--scan-dir", str(case)], workdir)
    if rc != 2 or len(keys) != 4 or not any(re.match(r"nv\.json:3-4:", k) for k in keys):
        return False, f"KEY mode: the gate gave exit {rc} with {len(keys)} key(s), want 2 with four, nv.json's at 3-4"
    for key in keys:
        km = re.match(r"^(.+):(\d+)(?:-(\d+))?:(\d+):", key)
        rel, first, last = km.group(1), int(km.group(2)), int(km.group(3) or km.group(2))
        proc = subprocess.run([sys.executable, str(SHAPE), "--root", str(case), key], capture_output=True, timeout=120)
        out = proc.stdout.decode("utf-8")
        if proc.returncode != 0 or "old-new" in out or keepwords in out or nv in out or any(_clear(ln) for ln in out.splitlines()):
            return False, f"KEY mode ({rel}): exit {proc.returncode}, or a character of a line printed in clear"
        lines = _gate_lines((case / rel).read_bytes())
        printed = [ln for ln in out.split("\n") if ln.startswith("    L")]
        if len(printed) != last - first + 1:
            return False, f"KEY mode ({rel}): printed {len(printed)} line(s) of a {last - first + 1}-line range"
        for n, ln in zip(range(first, last + 1), printed):
            if not ln.startswith(f"    L{n} ") or _content(ln) != _masked(lines[n - 1]):
                return False, f"KEY mode ({rel}): L{n} is not that line whole, masked"
        offset = re.search(r" offset=(\d+) ", printed[0])
        if not offset:
            return False, f"KEY mode ({rel}): no offset on the key's first line"
        if rel != "nv.json" and not lines[first - 1][int(offset.group(1)):].startswith(P):
            return False, f"KEY mode ({rel}): the offset is not at the name: a wrong line or column"
    # a KEY whose line the file does not have: numbered unlike the gate, so refused, not a crash or an empty window
    proc = subprocess.run([sys.executable, str(SHAPE), "--root", str(case), "c.md:99:1:juniper-b9-assignment:0123456789"],
                          capture_output=True, text=True, timeout=120)
    if proc.returncode != 3:
        return False, f"KEY mode: a line past the file's end gave exit {proc.returncode}, want 3"
    # KEY mode refuses as the walk does, by lstat: a symlink, and a FIFO, which it used to hang on (R12B1-04)
    kref = base.parent / "contract-keyrefuse"
    kref.mkdir(parents=True)
    (base.parent / "contract-keytarget.env").write_text(f"{P}{EQ}{vd()}\n")
    os.symlink(base.parent / "contract-keytarget.env", kref / "l.env")
    (base.parent / "contract-keytarget-dir").mkdir()
    (base.parent / "contract-keytarget-dir" / "x.env").write_text(f"{P}{EQ}{vd()}\n")
    os.symlink(base.parent / "contract-keytarget-dir", kref / "d")  # a symlink at a step above the file
    os.mkfifo(kref / "p.env")
    for rel in ("l.env", "d/x.env", "p.env"):
        try:
            r = subprocess.run([sys.executable, str(SHAPE), "--root", str(kref), f"{rel}:1:1:juniper-b9-assignment:0123456789"],
                               capture_output=True, text=True, timeout=30)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            rc = "a hang"
        if rc != 3:
            return False, f"KEY mode: a KEY naming {rel} ({'a symlink' if rel == 'l.env' else 'under a symlinked directory' if rel == 'd/x.env' else 'a FIFO'}) gave {rc}, want exit 3"
    os.unlink(kref / "p.env")
    # refusals: an empty root, text that is not UTF-8, an unreadable file (R11B1-07, R11B1-08); a FIFO (X20, C4a), a
    # symlinked subdirectory (C4b) and a symlinked root (C4f) (round 12)
    lead = vd()
    for kind in ("empty", "latin1", "unreadable", "fifo", "symdir", "symroot"):
        d = base.parent / f"contract-refuse-{kind}"
        d.mkdir(parents=True)
        root = d
        if kind == "latin1":
            (d / "x.env").write_bytes(lead.encode() + b"\xe9\n")
        elif kind == "unreadable":
            (d / "x.env").write_text("clean\n")
            os.chmod(d / "x.env", 0)
        elif kind == "fifo":
            (d / "ok.md").write_text("clean\n")
            os.mkfifo(d / "p.env")
        elif kind == "symdir":
            (d / "s").mkdir()
            (d / "s" / "ok.md").write_text("clean\n")
            (d / "t").mkdir()
            (d / "t" / "x.md").write_text("clean\n")
            os.symlink(d / "t", d / "s" / "sub")
            root = d / "s"
        elif kind == "symroot":
            (d / "t").mkdir()
            (d / "t" / "ok.md").write_text("clean\n")
            os.symlink(d / "t", d / "link")
            root = d / "link"
        try:
            r = subprocess.run([sys.executable, str(SHAPE), "--root", str(root), "--names"], capture_output=True, text=True, timeout=30)
            rc, err = r.returncode, r.stderr
        except subprocess.TimeoutExpired:
            rc, err = "a hang", ""
        if kind == "unreadable":
            os.chmod(d / "x.env", 0o600)
        if kind == "fifo":
            os.unlink(d / "p.env")
        if rc != 3:
            return False, f"refusal ({kind}): exit {rc}, want 3"
        if kind == "latin1" and ("0xe9" in err or "\\xe9" in err or lead[:8] in err):
            return False, "refusal (latin1): the reason printed the file's bytes"
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--workdir", help="gate workdir, so the scanner tarball is downloaded once")
    ap.add_argument("--only", help="run only cases whose name contains this")
    args = ap.parse_args()
    root = Path(tempfile.mkdtemp(prefix="gate-regression-"))
    workdir = Path(args.workdir) if args.workdir else root / "wd"
    failures, ran = [], 0
    try:
        for name, files, want, lines in text_cases():
            if args.only and args.only not in name:
                continue
            case = root / name
            case.mkdir()
            write_case(case, files)
            rc, keys, _ = run_gate(["--scan-dir", str(case)], workdir)
            ran += 1
            ok = rc == want
            if ok and lines:
                for rel, line in lines.items():  # a key names the line, or START-END for a multi-line match
                    if not any(k.startswith(f"{rel}:{line}:") or k.startswith(f"{rel}:{line}-") for k in keys):
                        ok = False
            print(f"{'ok  ' if ok else 'FAIL'} {name}: exit {rc} (want {want}){'' if ok else ' keys=' + str(keys[:4])}")
            if not ok:
                failures.append(name)
        for name, setup in error_cases(root):
            if args.only and args.only not in name:
                continue
            case = root / ("err-" + name)
            case.mkdir()
            rc = run_gate(setup(case), workdir)[0]
            restore(case)
            ran += 1
            ok = rc == 3
            print(f"{'ok  ' if ok else 'FAIL'} {name}: exit {rc} (want 3)")
            if not ok:
                failures.append(name)
        if not args.only or "accept" in args.only:
            case = root / "accept"
            case.mkdir()
            write_case(case, {"a.env": f"{P}{EQ}{v()} {P}_B{EQ}{v()}\n"})
            rc, keys, _ = run_gate(["--scan-dir", str(case)], workdir)
            ran += 1
            two = rc == 2 and len([k for k in keys if k.startswith("a.env:1:")]) >= 2
            rc1, _, _ = run_gate(["--scan-dir", str(case)] + sum((["--accept", k] for k in keys[:1]), []), workdir)
            rc_all, _, _ = run_gate(["--scan-dir", str(case)] + sum((["--accept", k] for k in keys), []), workdir)
            write_case(case, {"a.env": f"{P}{EQ}{v()} {P}_B{EQ}{v()}\n"})
            rc_edit, _, _ = run_gate(["--scan-dir", str(case)] + sum((["--accept", k] for k in keys), []), workdir)
            ok = two and rc1 == 2 and rc_all == 0 and rc_edit == 3
            print(f"{'ok  ' if ok else 'FAIL'} accept: two keys on one line {two}; one accepted -> {rc1} (want 2); all -> {rc_all} (want 0); after edit -> {rc_edit} (want 3)")
            if not ok:
                failures.append("accept")
        if not args.only or "concurrent" in args.only:
            ok_all = True
            for trial in range(5):
                a, b = root / f"race-secret-{trial}", root / f"race-clean-{trial}"
                value = v()
                write_case(a, {"x.env": f"{P}{EQ}{value}\n"})
                write_case(b, {"x.env": "Z" * len(f"{P}{EQ}{value}") + "\n"})
                cmd = [sys.executable, str(GATE), "--workdir", str(workdir), "--scan-dir"]
                pa = subprocess.Popen(cmd + [str(a)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pb = subprocess.Popen(cmd + [str(b)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ra, rb = pa.wait(timeout=900), pb.wait(timeout=900)
                ok_all = ok_all and ra == 2 and rb == 0
            ran += 1
            print(f"{'ok  ' if ok_all else 'FAIL'} concurrent: 5 trials of a secret run and a same-size clean run sharing one workdir")
            if not ok_all:
                failures.append("concurrent")
        if not args.only or "names" in args.only:
            ran += 1
            ok, why = names_check(root / "names")
            print(f"{'ok  ' if ok else 'FAIL'} names: the line read lists every planted line, prints the lines below, shows no value, and refuses what it cannot read{'' if ok else ' (' + why + ')'}")
            if not ok:
                failures.append("names")
        if not args.only or "contract" in args.only:
            ran += 1
            ok, why = contract_check(root / "contract", workdir)
            print(f"{'ok  ' if ok else 'FAIL'} contract: the line read lists names with any short separator and every marker, prints each listed line whole with the non-blank line above and the five below, prints nothing in clear but blanks, prints a KEY's lines whole, numbers lines as the gate does, and refuses what it cannot read{'' if ok else ' (' + why + ')'}")
            if not ok:
                failures.append("contract")
    finally:
        restore(root)
        shutil.rmtree(root, ignore_errors=True)
    print(f"\n{ran - len(failures)} of {ran} cases as expected" + (f"; FAILED: {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
