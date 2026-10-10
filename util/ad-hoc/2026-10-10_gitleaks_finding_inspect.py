#!/usr/bin/env python3
"""Classify the findings in a REDACTED gitleaks JSON report without ever printing a value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc -- investigation (backup recovery B9 / design P0.5a item 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md section 6.2 row B9;
         notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md P0.5a item 6 and AC-8a;
         .gitleaks.toml (the juniper-secret-assignment rule and the [extend] useDefault switch)

WHY THIS EXISTS

B9 turned the repository's gitleaks scan on for real: until then `.gitleaks.toml` carried an `[allowlist]` and no
`[extend]`, so gitleaks loaded ZERO rules and every CI scan passed vacuously. Turning the default ruleset on, and
adding the content rule, surfaces historical findings that each have to be classified -- a true secret (stop, rotate)
or a false positive -- and that classification must not itself copy a value into a terminal, a transcript or a PR.

The report must have been produced with `--redact`: gitleaks then replaces the value inside `Match` with the word
REDACTED, so `Match` becomes a TEMPLATE (`NAME=" REDACTED"`) that locates the value in the file at the finding's
commit. From the value this prints only derived properties: its length, its character classes, the punctuation it
carries, its Shannon entropy, whether it is hex / base64 / a UUID / a shell expansion / a <template>, which
placeholder markers it contains, and a per-run HMAC id (random key, so equal values group across findings without
an offline-checkable hash). With --context N it prints N lines either side, with every located value and every other
long letter+digit token masked.

Usage:
    gitleaks git --redact --report-format json --report-path R.json ...      # produce the report (REDACTED)
    python3 util/ad-hoc/2026-10-10_gitleaks_finding_inspect.py R.json --summary
    python3 util/ad-hoc/2026-10-10_gitleaks_finding_inspect.py R.json --repo . --context 2

Exit codes: 0 report read; 2 the report is unreadable or was NOT produced with --redact (a value would be in it).
"""

from __future__ import annotations

import argparse
import base64
import binascii
import collections
import hashlib
import hmac
import json
import math
import os
import re
import subprocess  # nosec B404 -- runs `git show` with a fixed argv, never a shell
import sys
import tomllib
from pathlib import Path

PLACEHOLDER_MARKERS = (
    "example",
    "sample",
    "test",
    "fake",
    "dummy",
    "placeholder",
    "changeme",
    "change-me",
    "redacted",
    "xxx",
    "your",
    "demo",
    "sentinel",
    "canary",
    "fixture",
    "probe",
    "nonce",
    "1234",
    "0000",
)
LONG_RUN = re.compile(r"[^\s\"'`]{16,}")
RUN_KEY = os.urandom(16)
# RFC 6455 section 1.3's worked example: the Sec-WebSocket-Key nonce is base64("the sample nonce"). Built at runtime
# so this file carries no key-shaped literal of its own.
RFC6455_SAMPLE = base64.b64encode(b"the sample nonce").decode("ascii")
WORDS_FILE = "/usr/share/dict/words"


def load_words() -> set[str]:
    try:
        with open(WORDS_FILE, encoding="utf-8", errors="replace") as fh:
            return {w.strip().lower() for w in fh if len(w.strip()) >= 3}
    except OSError:
        return set()


WORDS = load_words()
SIBLINGS: list[str] = []


def git_object_type(value: str) -> str:
    """For a 40-hex value: the repository (of --sibling) holding it as a git object, and its type."""
    for repo in SIBLINGS:
        res = subprocess.run(["git", "-C", repo, "cat-file", "-t", value], capture_output=True, text=True)  # nosec B603 B607
        if res.returncode == 0:
            return f"{res.stdout.strip()} in {os.path.basename(os.path.normpath(repo))}"
    return "not an object in any --sibling"


FIND_IN: list[str] = []


def tracked_paths_holding(value: str) -> list[str]:
    """Paths (never lines) of tracked files in each --find-in repository that contain `value` verbatim.

    Files named `.env*` are skipped unread: they may hold live credentials, and the question is only whether the value
    is published somewhere as an example or a default.
    """
    out = []
    for repo in FIND_IN:
        res = subprocess.run(["git", "-C", repo, "grep", "-l", "-F", "-I", "-e", value, "--", ".", ":(exclude,glob)**/.env*"], capture_output=True, text=True)  # nosec B603 B607
        out += [f"{os.path.basename(os.path.normpath(repo))}:{p}" for p in res.stdout.splitlines()]
    return out


def value_id(value: str) -> str:
    return hmac.new(RUN_KEY, value.encode("utf-8", "replace"), hashlib.sha256).hexdigest()[:8]


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = collections.Counter(value)
    n = len(value)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def describe(value: str) -> str:
    classes = "".join(flag for flag, test in (("a", str.islower), ("A", str.isupper), ("9", str.isdigit)) if any(test(ch) for ch in value))
    marks = "".join(sorted({ch for ch in value if not ch.isalnum()}))
    shapes = []
    if re.fullmatch(r"[0-9a-fA-F]+", value):
        shapes.append("hex")
    if re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", value) and len(value) % 4 == 0:
        shapes.append("base64")
    if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", value):
        shapes.append("uuid")
    if value.startswith("$"):
        shapes.append("shell-expansion")
    if value.startswith("<") and value.endswith(">"):
        shapes.append("template")
    if re.fullmatch(r"(.)\1{5,}", value):
        shapes.append("one-char-run")
    if value == RFC6455_SAMPLE:
        shapes.append("rfc6455-sample-nonce")
    if re.fullmatch(r"[0-9a-f]{40}", value) and SIBLINGS:
        shapes.append(f"git-object:{git_object_type(value)}")
    lowered = value.lower()
    markers = [m for m in PLACEHOLDER_MARKERS if m in lowered]
    parts = [p for p in re.split(r"[-_./ ]+", lowered) if p]
    words = sum(1 for p in parts if p.isalpha() and p in WORDS)
    # The first character's CLASS only (punctuation is named; a letter or digit is not), because the placeholder
    # exclusions key on it: `$` + name is an expansion, `<` a template, `{` a format field.
    first = value[:1] if value[:1] and not value[:1].isalnum() else ("letter" if value[:1].isalpha() else "digit")
    return f"len={len(value)} first={first!r} classes={classes or '-'} marks={marks!r} entropy={entropy(value):.2f} shapes={shapes or '-'} markers={markers or '-'} dictionary_words={words}/{len(parts)} vid={value_id(value)}"


def structure(value: str) -> str:
    """Character-class runs with their lengths (a=lower, A=upper, 9=digit, p=punctuation) -- never a character."""

    def cls(ch: str) -> str:
        return "a" if ch.islower() else "A" if ch.isupper() else "9" if ch.isdigit() else "p"

    runs: list[list] = []
    for ch in value:
        c = cls(ch)
        if runs and runs[-1][0] == c:
            runs[-1][1] += 1
        else:
            runs.append([c, 1])
    return " ".join(f"{c}{n}" for c, n in runs)


def file_at(repo: str, commit: str, path: str) -> list[str] | None:
    try:
        out = subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True, check=True)  # nosec B603 B607
    except subprocess.CalledProcessError:
        return None
    return out.stdout.decode("utf-8", "replace").split("\n")


RULE_MODELS: dict[str, tuple[re.Pattern[str], int]] = {}


def load_rule_models(config_path: str) -> None:
    """Python models of the config's own [[rules]] (regex + secretGroup), for exact value extraction."""
    with open(config_path, "rb") as fh:
        cfg = tomllib.load(fh)
    for rule in cfg.get("rules", []):
        try:
            RULE_MODELS[rule["id"]] = (re.compile(rule["regex"]), int(rule.get("secretGroup", 0)))
        except (KeyError, re.error):
            continue


def locate_by_rule(rule_id: str, text: str) -> list[str]:
    """The value exactly as gitleaks extracts it: secretGroup, else the first non-empty group, else the match."""
    rx, group = RULE_MODELS[rule_id]
    out = []
    for m in rx.finditer(text):
        if group:
            out.append(m.group(group))
        else:
            out.append(next((g for g in m.groups() if g), m.group(0)))
    return out


def locate(template: str, text: str) -> list[str]:
    """Values the REDACTED template stands for, found in `text` (empty when it cannot be located)."""
    parts = template.split("REDACTED")
    if len(parts) < 2 or not any(p.strip() for p in parts):
        return []
    # A middle hole is bounded by the literal after it; a TRAILING hole has none, and a lazy `(.+?)` there would
    # capture one character, so it takes the rest of the non-blank run instead.
    pattern = "(.+?)".join(re.escape(p) for p in parts[:-1]) + ("(.+?)" + re.escape(parts[-1]) if parts[-1] else r"(\S+)")
    found = re.search(pattern, text, flags=re.DOTALL)
    if not found:
        return []
    return [g for g in found.groups() if g]


PEM = re.compile(r"-----BEGIN[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----(.*?)-----END[ A-Z0-9_-]{0,100}PRIVATE KEY(?: BLOCK)?-----", re.DOTALL)


def describe_pem(text: str) -> tuple[str, list[str]]:
    found = PEM.search(text)
    if not found:
        return "pem: not located", []
    body = found.group(1)
    compact = re.sub(r"\s+", "", body)
    try:
        raw = base64.b64decode(compact, validate=True)
        decodes, der = True, raw[:1] == b"\x30"
    except (binascii.Error, ValueError):
        decodes, der = False, False
    lowered = body.lower()
    markers = [m for m in PLACEHOLDER_MARKERS if m in lowered] + (["..."] if "..." in body else [])
    return (f"pem: body_chars={len(compact)} body_lines={body.count(chr(10))} base64_decodes={decodes} der_sequence={der} markers={markers or '-'} vid={value_id(compact)}"), [line for line in body.split("\n") if line.strip()]


def mask_line(line: str, values: list[str]) -> str:
    for v in sorted(values, key=len, reverse=True):
        if v and v in line:
            line = line.replace(v, f"<<V:{value_id(v)} len={len(v)}>>")

    def _mask(m: re.Match[str]) -> str:
        tok = m.group(0)
        if "<<V:" in tok:
            # Already holds a masked value; what surrounds it is the assignment's name, shown so the form is legible.
            # Mask any OTHER letter+digit run of 16+ inside it all the same.
            return re.sub(r"(?<![<:])\b(?=[^<>\s]*\d)(?=[^<>\s]*[A-Za-z])[^<>\s=]{16,}", lambda x: f"<<tok len={len(x.group(0))}>>", tok)
        if any(ch.isalpha() for ch in tok) and any(ch.isdigit() for ch in tok):
            return f"<<tok len={len(tok)}>>"
        return tok

    return LONG_RUN.sub(_mask, line)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="gitleaks JSON report produced WITH --redact")
    ap.add_argument("--repo", default=".", help="repository the report was produced from (for `git show`)")
    ap.add_argument("--summary", action="store_true", help="print RuleID / file / commit / line only")
    ap.add_argument("--context", type=int, default=0, help="masked context lines either side of each finding")
    ap.add_argument("--sibling", action="append", default=[], help="repository in which a 40-hex value is looked up as a git object (repeatable)")
    ap.add_argument("--config", help="gitleaks config whose own [[rules]] extract values exactly (else the REDACTED template is used)")
    ap.add_argument("--rule", action="append", default=[], help="only findings of this RuleID (repeatable)")
    ap.add_argument("--compact", action="store_true", help="one line per finding: location || value shape")
    ap.add_argument("--file", action="append", default=[], help="only findings in this path (repeatable)")
    ap.add_argument("--structure", action="store_true", help="also print each value's character-class runs (opt-in: it shows layout)")
    ap.add_argument("--find-in", action="append", default=[], help="repository whose tracked files are searched for each value; prints PATHS only, skips .env* (repeatable)")
    args = ap.parse_args()
    SIBLINGS.extend(args.sibling)
    FIND_IN.extend(args.find_in)
    if args.config:
        load_rule_models(args.config)

    try:
        with open(args.report, encoding="utf-8") as fh:
            findings = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"cannot read report: {exc}", file=sys.stderr)
        return 2
    if any(f.get("Secret") not in ("REDACTED", "") for f in findings):
        print("refusing: the report was not produced with --redact (a value is present)", file=sys.stderr)
        return 2

    if args.rule:
        findings = [f for f in findings if f.get("RuleID") in args.rule]
    if args.file:
        findings = [f for f in findings if f.get("File") in args.file]
    findings.sort(key=lambda f: (f.get("RuleID", ""), f.get("File", ""), f.get("Date", ""), f.get("StartLine", 0)))
    print(f"{len(findings)} finding(s); by rule: {dict(collections.Counter(f.get('RuleID') for f in findings))}")
    for i, f in enumerate(findings):
        head = f"[{i}] {f.get('RuleID')} | {f.get('File')} | {f.get('Commit', '')[:12] or 'worktree'} | L{f.get('StartLine')}-{f.get('EndLine')} | {f.get('Date', '')[:10]}"
        if args.summary:
            print(head)
            continue
        if f.get("Commit"):
            lines = file_at(args.repo, f["Commit"], f.get("File", ""))
        else:
            try:
                lines = Path(args.repo, f.get("File", "")).read_text(encoding="utf-8", errors="replace").split("\n")
            except OSError:
                lines = None
        if lines is None:
            print(head)
            print("    file not readable at that commit")
            continue
        lo, hi = f.get("StartLine", 1), f.get("EndLine", f.get("StartLine", 1))
        span = "\n".join(lines[lo - 1 : hi])
        values: list[str]
        if f.get("RuleID") == "private-key":
            desc, values = describe_pem(span)
            descs = [desc]
        else:
            values = locate_by_rule(f["RuleID"], span) if f.get("RuleID") in RULE_MODELS else locate(f.get("Match", ""), span)
            descs = [f"value: {describe(v)}" + (f" structure=[{structure(v)}]" if args.structure else "") + (f" also_in={tracked_paths_holding(v)}" if FIND_IN else "") for v in values] or ["value: not located from the template"]
        if args.compact:
            print(f"{head} || {' ;; '.join(descs)}")
        else:
            print(head)
            for d in descs:
                print(f"    {d}")
        if args.context:
            for n in range(max(1, lo - args.context), min(len(lines), hi + args.context) + 1):
                shown = mask_line(lines[n - 1], values)
                at = shown.find("<<V:")
                start = max(0, at - 110) if at >= 0 else 0
                print(f"    {n:5}: {'…' if start else ''}{shown[start : start + 220]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
