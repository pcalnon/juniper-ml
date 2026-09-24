#!/usr/bin/env python
"""Check the Phase 9 tools' secret and e-mail shapes against constructed FAKE values, both ways.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- one-off (canopy E2E arc, Phase 9 ledger validation, round-6 fix pass)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-24_owner_answer_extract.py, util/ad-hoc/2026-09-24_merge_command_launch_scan.py,
         util/ad-hoc/2026-09-24_archive_phase9_tmpfs_evidence_round2.py and, since round 7,
         util/ad-hoc/2026-09-23_archive_consensus_reports_by_round.py (the four tools checked);
         reports/e2e-canopy-2026-09-02/consensus/2026-09-24_validator_reports_phase9_ledger_round6.md (Lane R6-B's
         finding 3, which found the extractor passing sk-ant-, sk-proj-, hf_, xoxb-, pypi-, a PEM header and a
         %40-encoded address), and the round-7 and round-8 reports, whose lanes found the archiver's gaps

Every value below is constructed and FAKE. The script prints case labels and PASS/FAIL only, never a value.
A "catch" case must be matched by every tool; a "leave" case (a look-alike word) by none; each GATE case must
be refused, or passed, by the archiver's --allow-shape gate as its last field says. Exit 1 on any FAIL. The
numbers the ledger quotes for round 6 (17 failures) and round 7 (14) were measured with this check as those
rounds left it; a later, larger check fails more often on the same old tools.

Usage:
    python3 -B util/ad-hoc/2026-09-24_secret_shape_check.py
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = [
    "2026-09-24_owner_answer_extract.py",
    "2026-09-24_merge_command_launch_scan.py",
    "2026-09-24_archive_phase9_tmpfs_evidence_round2.py",
    # Added in round 7 (Lane R7-B): the report archiver. It has no EMAIL_RE (a report may name a bot address),
    # so the e-mail cases skip it; its --allow-shape gate is tested separately below.
    "2026-09-23_archive_consensus_reports_by_round.py",
]
ARCHIVER = "2026-09-23_archive_consensus_reports_by_round.py"

CATCH = {
    "anthropic-style sk-ant- key": "sk-ant-api03-" + "Ab1" * 30,
    "project-style sk-proj- key": "sk-proj-" + "Cd2" * 20,
    "bare sk- key": "sk-" + "Ef3" * 16,
    # Round 7 (Lane R7-B): the launch scan, the tmpfs tool and the archiver used a 32-character floor from the
    # start, and round 6 raised the extractor's from 20 to 32, so 20-31 characters passed and no case saw it.
    "bare sk- key, 24 characters": "sk-" + "Op8" * 8,
    "hugging face hf_ token": "hf_" + "Gh4" * 12,
    "slack xoxb- token": "xoxb-" + "1234567890-" + "Ij5" * 6,
    "pypi token": "pypi-AgEIcHlwaS5vcmc" + "Kl6" * 30,
    "github ghp_ token": "ghp_" + "Mn7" * 12,
    # Concatenated so this file never holds the header whole: the detect-private-key hook would refuse it.
    "PEM private-key header": "-----BEGIN OPENSSH" + " PRIVATE KEY-----",
}
EMAIL_CATCH = {
    "plain address": "someone.fake@example.com",
    "%40-encoded address": "someone.fake%40example.com",
}
LEAVE = {
    "hyphenated word containing sk-": "task-scheduler-configuration-for-the-nightly-run-x",
    "desk- slug": "desk-top-application-configuration-file-name-long",
    "decorator after a diff plus": "+@pytest.mark.unit",
    "short pypi- slug": "pypi-publish-procedure",
}


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").removesuffix(".py"), HERE / name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# The archiver's --allow-shape gate: (label, report text, agent id, allows, must refuse?). Round 7 wrote the
# scoping cases, the first key-material case (then with a 39-character body) and the whole classic age key.
# Round 8 added the other key-material forms, after Lanes R8-A and R8-B passed fake keys through round 7's
# refusal, and lengthened the first case's body to 48 characters. That hid the form round 8's refusal had
# dropped, so round 9 added a 39-character case back (Lane R9-B). Every header is concatenated: see CATCH.
PEM = "-----BEGIN OPENSSH" + " PRIVATE KEY-----"
RSA = "-----BEGIN RSA" + " PRIVATE KEY-----"
END = "-----END OPENSSH" + " PRIVATE KEY-----"
B64 = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo0MTIzNDU2Nzg5"
GATE = [
    ("a quoted header, allowed for its own agent", f"its test used a {PEM} header", "aX", [f"aX={PEM}"], False),
    ("a quoted header then a SHA and a path, allowed", f"a {PEM} header, then `util/ad-hoc/2026-09-24_x.py` at 3297131f", "aX", [f"aX={PEM}"], False),
    ("a quoted header, allowed for another agent only", f"its test used a {PEM} header", "aX", [f"aY={PEM}"], True),
    ("a header followed by key material, allowed", f"{PEM}\n{B64}\n", "aX", [f"aX={PEM}"], True),
    ("a header then a 39-character body, allowed", f"{PEM}\n{B64[:39]}…", "aX", [f"aX={PEM}"], True),
    ("a JSON-escaped key, header allowed", '"private_key": "' + PEM + "\\n" + B64 + "\\n" + END + '"', "aX", [f"aX={PEM}"], True),
    ("a key in a blockquote, header allowed", f"> {PEM}\n> {B64}\n", "aX", [f"aX={PEM}"], True),
    ("a key in numbered lines, header allowed", f"     1\t{PEM}\n     2\t{B64}\n", "aX", [f"aX={PEM}"], True),
    ("a backticked header then a key, allowed", f"`{PEM}`\n{B64}\n", "aX", [f"aX={PEM}"], True),
    ("an encrypted RSA key, header allowed", f"{RSA}\nProc-Type: 4,ENCRYPTED\nDEK-Info: AES-128-CBC,0123456789ABCDEF\n\n{B64}\n", "aX", [f"aX={RSA}"], True),
    ("a PEM END line alone", f"… {END}", "aX", [], True),
    ("a whole age key, its prefix allowed", "AGE-SECRET-KEY-1" + "QWERTYUIOPASDFGHJKLZ", "aX", ["aX=AGE-SECRET-KEY-"], True),
    ("a post-quantum age identity, its prefix allowed", "AGE-SECRET-KEY-PQ-1" + "QWERTYUIOPASDFGHJKLZ", "aX", ["aX=AGE-SECRET-KEY-"], True),
    ("a report with no shape", "nothing to see here", "aX", [], False),
]


def main() -> int:
    fails = 0
    for tool in TOOLS:
        mod = load(tool)
        email = getattr(mod, "EMAIL_RE", None)
        for label, value in CATCH.items():
            ok = bool(mod.SECRET_RE.search(value))
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {tool}: catches {label}")
        for label, value in EMAIL_CATCH.items():
            if email is None:
                continue
            ok = bool(email.search(value))
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {tool}: catches {label}")
        for label, value in LEAVE.items():
            ok = not mod.SECRET_RE.search(value) and not (email and email.search(value))
            fails += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {tool}: leaves {label}")
        if tool == ARCHIVER:
            gate = getattr(mod, "unreviewed_shapes", None)
            for label, text, aid, allows, must_refuse in GATE:
                ok = gate is not None and bool(gate(text, aid, allows)) == must_refuse
                fails += not ok
                print(f"{'PASS' if ok else 'FAIL'}  {tool}: {'refuses' if must_refuse else 'passes'} {label}")
    print(f"{fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
