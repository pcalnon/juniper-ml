#!/usr/bin/env python3
"""Survey every `NAME=` occurrence of the B9 credential names at HEAD by FORM and VALUE KIND, never by value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc -- investigation (backup recovery B9 / design P0.5a item 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: .gitleaks.toml (rule juniper-secret-assignment); tests/test_gitleaks_secret_assignment_rule.py;
         util/ad-hoc/2026-10-10_gitleaks_finding_inspect.py

WHY THIS EXISTS

The rule has to fire on a literal value in every form the repository uses -- `export`, systemd `Environment=`, a
comment, argv -- and stay silent on the forms that only NAME the variable: an empty value, a shell expansion, a
<template>, a format placeholder, a code expression such as `passphrase=args.passphrase`, and the placeholder words.
Tuning that by eye over 61 files is how a false positive class gets missed, so this tallies the corpus: one row per
(form, kind) with a count and example locations. With --rule it also says which kinds the rule in .gitleaks.toml
fires on, through the same model the regression suite uses (regex + the rule's allowlists, applied to the value).

Only a value of kind `literal` could be a secret, and for that kind only its shape is printed (length, character
classes, punctuation, entropy). Every other kind is a category name.

Usage:
    python3 util/ad-hoc/2026-10-10_secret_assignment_corpus_survey.py [--rule] [--show KIND]
"""

from __future__ import annotations

import argparse
import collections
import math
import re
import subprocess  # nosec B404 -- runs `git grep` with a fixed argv, never a shell
import sys
import tomllib
from pathlib import Path

NAMES = r"(SETTINGS_ENCRYPTION_KEY|PASSPHRASE(?:_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password|passphrase)"
LOOSE = re.compile(NAMES + r"=")
# POSIX ERE for `git grep -E`, which has no `(?:`.
NAMES_ERE = "(SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password|passphrase)="
RULE_ID = "juniper-secret-assignment"


def repo_root() -> Path:
    for cand in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (cand / ".gitleaks.toml").is_file() and (cand / ".github").is_dir():
            return cand
    raise SystemExit("no repo root above this script")


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = collections.Counter(value)
    return -sum((c / len(value)) * math.log2(c / len(value)) for c in counts.values())


def form_of(line: str, start: int) -> str:
    before = line[:start]
    stripped = before.lstrip()
    tags = []
    if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith(";"):
        tags.append("comment")
    if before.endswith("--"):
        tags.append("argv")
    elif before.endswith("Environment=") or before.endswith('Environment="') or before.endswith("Environment='"):
        tags.append("systemd")
    elif re.search(r"(^|\s)export\s+$", before):
        tags.append("export")
    elif before.endswith("{") or before.endswith("("):
        tags.append("format-or-call")
    elif re.search(r"[A-Za-z0-9_]$", before):
        tags.append("suffix-of-longer-name")
    return "+".join(tags) or "bare"


def value_after(line: str, end: int) -> tuple[str, str]:
    rest = line[end:]
    if rest[:1] in ("'", '"'):
        q = rest[0]
        close = rest.find(q, 1)
        return q, rest[1:close] if close > 0 else rest[1:]
    return "", re.split(r"[\s`'\";,)\]}]", rest, maxsplit=1)[0]


def kind_of(value: str) -> str:
    if value == "":
        return "empty"
    if re.match(r"\$[A-Za-z_{(]", value):
        return "shell-expansion"
    if value.startswith("<"):
        return "template"
    if value.startswith("{"):
        return "format-placeholder"
    if re.fullmatch(r"(?i).*(redacted|change[-_]?me|placeholder).*", value) or re.fullmatch(r"[^0-9A-WYZa-wyz]*", value):
        return "placeholder-word"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*(\(.*\)?|\[.*\]?)?", value) and ("." in value or "(" in value or "[" in value):
        return "code-expression"
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        return "bare-identifier-or-word"
    return "literal"


def shape(value: str) -> str:
    classes = "".join(f for f, t in (("a", str.islower), ("A", str.isupper), ("9", str.isdigit)) if any(t(c) for c in value))
    marks = "".join(sorted({c for c in value if not c.isalnum()}))
    return f"len={len(value)} classes={classes or '-'} marks={marks!r} entropy={entropy(value):.2f}"


def load_rule(root: Path) -> tuple[re.Pattern[str], int, list[re.Pattern[str]]]:
    with open(root / ".gitleaks.toml", "rb") as fh:
        cfg = tomllib.load(fh)
    rule = next(r for r in cfg.get("rules", []) if r.get("id") == RULE_ID)
    allow = [re.compile(rx) for a in rule.get("allowlists", []) if a.get("regexTarget", "secret") == "secret" for rx in a.get("regexes", [])]
    return re.compile(rule["regex"]), int(rule.get("secretGroup", 0)), allow


def rule_fires(line: str, model: tuple[re.Pattern[str], int, list[re.Pattern[str]]]) -> bool:
    rx, group, allow = model
    for m in rx.finditer(line):
        value = m.group(group) if group else m.group(0)
        if not any(a.search(value) for a in allow):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rule", action="store_true", help="also report whether the .gitleaks.toml rule fires on each line")
    ap.add_argument("--show", action="append", default=[], help="list every location of this kind (repeatable)")
    args = ap.parse_args()
    root = repo_root()
    model = load_rule(root) if args.rule else None

    out = subprocess.run(["git", "-C", str(root), "grep", "-n", "-I", "-E", NAMES_ERE], capture_output=True, text=True, check=False)  # nosec B603 B607
    rows: dict[tuple[str, str, str], list[str]] = collections.defaultdict(list)
    shapes: list[str] = []
    fired = 0
    for raw in out.stdout.splitlines():
        path, lineno, line = raw.split(":", 2)
        hit = rule_fires(line, model) if model else None
        fired += 1 if hit else 0
        for m in LOOSE.finditer(line):
            quote, value = value_after(line, m.end())
            k = kind_of(value)
            key = (form_of(line, m.start()), k, "FIRES" if hit else ("silent" if model else "-"))
            rows[key].append(f"{path}:{lineno}")
            if k == "literal":
                shapes.append(f"{path}:{lineno} quote={quote or '-'} {shape(value)}{' FIRES' if hit else ''}")
    for (form, k, verdict), locs in sorted(rows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"{len(locs):4}  form={form:28} kind={k:24} rule={verdict:6}  e.g. {', '.join(locs[:2])}")
        if k in args.show:
            for loc in locs:
                print(f"        {loc}")
    print(f"\nliteral-kind values ({len(shapes)}), shape only:")
    for s in shapes:
        print(f"  {s}")
    if model:
        print(f"\nlines on which the rule fires: {fired}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
