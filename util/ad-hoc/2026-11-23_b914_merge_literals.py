#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml (cross-repo tooling)
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: flake8-bugbear 26.11.22 B914 remediation)
"""Merge the same-line implicit string concatenations that flake8-bugbear's B914 reports.

Why this exists
---------------
flake8-bugbear 26.11.22 (PyPI, 2026-11-22) added B914: "implicit string concatenation of two literals
on the same line, inside brackets or call arguments". Seven Juniper repos select ``B9`` with an
unpinned ``flake8-bugbear>=24.0.0`` and CI runs ``pre-commit run --all-files`` behind a cache keyed
on ``.pre-commit-config.yaml``, so every cache miss fails pre-commit. Most hits are black's output:
at line-length 512 black joins a multi-line concatenation onto one line.

The owner ruled (2026-11-23): merge the literals, never suppress, never pin. This tool rewrites each
reported run of adjacent literals as ONE literal and proves the rewrite changes nothing: after every
single merge the whole module is re-parsed and its ``ast.dump`` must equal the original's. A merge
that cannot be proven (octal escape at the seam, ``\\N{...}`` moving into an f-string, raw/non-raw
mixes with backslashes, mismatched quotes that need escaping) is SKIPPED and reported, never forced.

Usage
-----
    # 1. scan: run flake8 --select=B914 over each flake8 hook's file scope from the repo's
    #    .pre-commit-config.yaml (needs a flake8 with flake8-bugbear>=26.11.22 installed)
    python3 2026-11-23_b914_merge_literals.py scan --repo /path/to/repo --flake8 /venv/bin/flake8 --out sites.json
    # 2. fix: dry-run by default; --apply writes the files
    python3 2026-11-23_b914_merge_literals.py fix --repo /path/to/repo --sites sites.json [--apply]
    # self-test of the merge rules (mutation-style: every rule has a case that must be refused)
    python3 2026-11-23_b914_merge_literals.py --self-test
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

PREFIX_RE = re.compile(r"^([A-Za-z]*)('''|\"\"\"|'|\")", re.S)


@dataclass
class Part:
    start: tuple[int, int]  # (line, col) 1-based line, 0-based col, as tokenize reports
    end: tuple[int, int]
    text: str


class MergeRefused(Exception):
    pass


# ----------------------------------------------------------------------------------------------
# literal merging
# ----------------------------------------------------------------------------------------------
def split_literal(text: str) -> tuple[str, str, str]:
    m = PREFIX_RE.match(text)
    if not m:
        raise MergeRefused(f"not a string literal: {text[:40]!r}")
    prefix, quote = m.group(1), m.group(2)
    if not text.endswith(quote) or len(text) < len(prefix) + 2 * len(quote):
        raise MergeRefused(f"unterminated literal: {text[:40]!r}")
    return prefix, quote, text[len(prefix) + len(quote) : len(text) - len(quote)]


def merge_two(a: str, b: str) -> str:
    pa, qa, ba = split_literal(a)
    pb, qb, bb = split_literal(b)
    la, lb = pa.lower(), pb.lower()
    if ("b" in la) != ("b" in lb):
        raise MergeRefused("bytes and str")
    if qa != qb:
        if len(qa) == 3 or len(qb) == 3:
            raise MergeRefused("triple-quoted part with a different delimiter")
        if qa in bb:
            raise MergeRefused(f"second part contains the first part's quote {qa!r}")
    ra, rb = "r" in la, "r" in lb
    if ra != rb and "\\" in bb:
        raise MergeRefused("raw and non-raw parts and the second carries a backslash")
    fa, fb = "f" in la, "f" in lb
    prefix = pa
    if fa != fb:
        if not fa:
            if "u" in la:
                raise MergeRefused("u-prefixed part cannot become an f-string")
            prefix = pa + "f"
            plain = ba
        else:
            plain = bb
        if not (ra if not fa else rb) and "\\N{" in plain:
            raise MergeRefused("a \\N{...} escape would move into an f-string")
        escaped = plain.replace("{", "{{").replace("}", "}}")
        if not fa:
            ba = escaped
        else:
            bb = escaped
    return f"{prefix}{qa}{ba}{bb}{qa}"


def _escape_quote(body: str, q: str, is_f: bool) -> tuple[str, int]:
    """Escape every unescaped ``q`` in the LITERAL regions of a non-raw body.

    Existing escape sequences are copied verbatim. In an f-string body, a ``q`` inside a
    replacement field refuses (reusing the delimiter there needs PEP 701, i.e. Python 3.12+,
    and several repos still support 3.11); ``{{`` / ``}}`` are literal braces.
    """
    out: list[str] = []
    n = 0
    i = 0
    depth = 0
    while i < len(body):
        c = body[i]
        if is_f and depth == 0 and body[i : i + 2] in ("{{", "}}"):
            out.append(body[i : i + 2])
            i += 2
            continue
        if is_f and c == "{":
            depth += 1
        elif is_f and c == "}" and depth > 0:
            depth -= 1
        elif depth > 0 and c == q:
            raise MergeRefused(f"the quote {q!r} occurs inside an f-string replacement field")
        elif depth == 0 and c == "\\":
            out.append(body[i : i + 2])
            i += 2
            continue
        elif depth == 0 and c == q:
            out.append("\\" + q)
            n += 1
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out), n


def merge_run(texts: list[str]) -> str:
    """Merge a same-line run of adjacent literals into ONE literal (refuses what it cannot prove)."""
    parts = [split_literal(t) for t in texts]
    quotes = {q for _, q, _ in parts}
    if any(len(q) == 3 for q in quotes):
        if len(quotes) != 1:
            raise MergeRefused("triple-quoted part with a different delimiter")
        out = texts[0]
        for t in texts[1:]:
            out = merge_two(out, t)
        return out
    low = [p.lower() for p, _, _ in parts]
    if len({"b" in lp for lp in low}) != 1:
        raise MergeRefused("bytes and str")
    is_bytes = "b" in low[0]
    raws = ["r" in lp for lp in low]
    if all(raws):
        raw = True
    elif not any("\\" in b for (lp, _, b), r in zip(parts, raws) if r):
        raw = False  # raw parts without a backslash read the same unraw
    elif not any("\\" in b for (lp, _, b), r in zip(parts, raws) if not r):
        raw = True  # non-raw parts without a backslash read the same raw
    else:
        raise MergeRefused("raw and non-raw parts both carry backslashes")
    fs = ["f" in lp for lp in low]
    is_f = any(fs)
    if is_f and "u" in low[0]:
        raise MergeRefused("u-prefixed part cannot become an f-string")
    bodies = []
    for (p, q, b), f in zip(parts, fs):
        if is_f and not f:
            if not raw and "\\N{" in b:
                raise MergeRefused("a \\N{...} escape would move into an f-string")
            b = b.replace("{", "{{").replace("}", "}}")
        bodies.append((q, b))
    best = None
    first_q = parts[0][1]
    # fewest escapes wins; on a tie keep the first part's quote (the file's existing style)
    for cand in (first_q, "'" if first_q == '"' else '"'):
        try:
            total = 0
            conv = []
            for (q, b), f in zip(bodies, fs):
                if q == cand:
                    conv.append(b)
                    continue
                if raw:
                    if cand in b:
                        raise MergeRefused(f"raw part contains the quote {cand!r}")
                    conv.append(b)
                    continue
                nb, k = _escape_quote(b, cand, is_f)
                total += k
                conv.append(nb)
        except MergeRefused as exc:
            last = exc
            continue
        if best is None or total < best[0]:
            best = (total, cand, conv)
    if best is None:
        raise last
    _, q, conv = best
    prefix = ("u" if ("u" in low[0] and not is_f) else "") + ("b" if is_bytes else "") + ("r" if raw else "") + ("f" if is_f else "")
    return f"{prefix}{q}{''.join(conv)}{q}"


# ----------------------------------------------------------------------------------------------
# locating literal runs
# ----------------------------------------------------------------------------------------------
def line_offsets(src: str) -> list[int]:
    offs = [0]
    for line in src.splitlines(keepends=True):
        offs.append(offs[-1] + len(line))
    return offs


def string_nodes(tree: ast.AST) -> list[ast.expr]:
    inner: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for v in node.values:
                inner.add(id(v))
    out = []
    for node in ast.walk(tree):
        if id(node) in inner:
            continue
        if isinstance(node, ast.JoinedStr) or (isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))):
            out.append(node)
    return out


def char_col(src_lines: list[str], line: int, byte_col: int) -> int:
    """ast columns are UTF-8 BYTE offsets; tokenize columns are CHARACTER offsets."""
    return len(src_lines[line - 1].encode("utf-8")[:byte_col].decode("utf-8", errors="replace"))


def node_parts(tokens: list[tokenize.TokenInfo], src_lines: list[str], node: ast.expr) -> list[Part] | None:
    start = (node.lineno, char_col(src_lines, node.lineno, node.col_offset))
    end = (node.end_lineno, char_col(src_lines, node.end_lineno, node.end_col_offset))
    parts: list[Part] = []
    depth = 0
    cur_start = None
    for tok in tokens:
        if tok.start < start or tok.end > end:
            continue
        if depth == 0:
            if tok.type == tokenize.STRING:
                parts.append(Part(tok.start, tok.end, tok.string))
                continue
            if tok.type == getattr(tokenize, "FSTRING_START", -1) or tok.type == getattr(tokenize, "TSTRING_START", -2):
                depth = 1
                cur_start = tok.start
                continue
            if tok.type in (tokenize.NL, tokenize.COMMENT, tokenize.NEWLINE):
                continue
            return None  # something other than literals between the parts: not a plain concatenation
        else:
            if tok.type in (getattr(tokenize, "FSTRING_START", -1), getattr(tokenize, "TSTRING_START", -2)):
                depth += 1
            elif tok.type in (getattr(tokenize, "FSTRING_END", -1), getattr(tokenize, "TSTRING_END", -2)):
                depth -= 1
                if depth == 0:
                    parts.append(Part(cur_start, tok.end, ""))
    if depth != 0:
        return None
    for p in parts:
        if not p.text:
            (l1, c1), (l2, c2) = p.start, p.end
            if l1 == l2:
                p.text = src_lines[l1 - 1][c1:c2]
            else:
                p.text = src_lines[l1 - 1][c1:] + "".join(src_lines[l1 : l2 - 1]) + src_lines[l2 - 1][:c2]
    return parts


def same_line_runs(parts: list[Part]) -> list[list[Part]]:
    runs: list[list[Part]] = []
    cur: list[Part] = []
    for p in parts:
        if cur and cur[-1].end[0] == p.start[0]:
            cur.append(p)
        else:
            if len(cur) > 1:
                runs.append(cur)
            cur = [p]
    if len(cur) > 1:
        runs.append(cur)
    return runs


def fix_source(src: str, sites: list[tuple[int, int]]) -> tuple[str, list[dict], list[dict]]:
    """Return (new_src, merged, skipped). sites are flake8 (line, col1) positions."""
    tree = ast.parse(src)
    want = ast.dump(tree)
    tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    lines = src.splitlines(keepends=True)
    nodes = string_nodes(tree)
    runs: dict[tuple, list[Part]] = {}
    skipped: list[dict] = []
    for line, col1 in sites:
        pos = (line, col1 - 1)
        cands = [n for n in nodes if (n.lineno, n.col_offset) <= pos <= (n.end_lineno, n.end_col_offset)]
        if not cands:
            skipped.append({"line": line, "col": col1, "why": "no string node covers the site"})
            continue
        node = min(cands, key=lambda n: (n.end_lineno - n.lineno, n.end_col_offset - n.col_offset if n.end_lineno == n.lineno else 10**9))
        parts = node_parts(tokens, lines, node)
        if not parts:
            skipped.append({"line": line, "col": col1, "why": "not a plain literal concatenation"})
            continue
        found = False
        for run in same_line_runs(parts):
            runs[(run[0].start, run[-1].end)] = run
            found = True
        if not found:
            skipped.append({"line": line, "col": col1, "why": "no same-line run in the covering node"})
    offs = line_offsets(src)
    merged: list[dict] = []
    new = src
    for key in sorted(runs, reverse=True):
        run = runs[key]
        a = offs[run[0].start[0] - 1] + run[0].start[1]
        b = offs[run[-1].end[0] - 1] + run[-1].end[1]
        old_text = new[a:b]
        try:
            lit = merge_run([p.text for p in run])
        except MergeRefused as exc:
            skipped.append({"line": run[0].start[0], "col": run[0].start[1] + 1, "why": str(exc), "text": old_text})
            continue
        cand = new[:a] + lit + new[b:]
        try:
            ok = ast.dump(ast.parse(cand)) == want
        except SyntaxError as exc:
            ok = False
            why = f"merged text does not parse: {exc.msg}"
        else:
            why = "merged module's AST differs from the original"
        if not ok:
            skipped.append({"line": run[0].start[0], "col": run[0].start[1] + 1, "why": why, "text": old_text})
            continue
        new = cand
        merged.append({"line": run[0].start[0], "old": old_text, "new": lit})
    return new, sorted(merged, key=lambda m: m["line"]), skipped


# ----------------------------------------------------------------------------------------------
# scan: flake8 --select=B914 over each flake8 hook's scope
# ----------------------------------------------------------------------------------------------
def flake8_hook_scopes(repo: Path) -> list[tuple[str | None, str | None]]:
    import yaml  # PyYAML

    cfg = yaml.safe_load((repo / ".pre-commit-config.yaml").read_text())
    scopes = []
    for r in cfg.get("repos", []):
        for h in r.get("hooks", []):
            if h.get("id") == "flake8":
                scopes.append((h.get("files"), h.get("exclude")))
    top_ex = cfg.get("exclude")
    return [(f, e if e else top_ex) for f, e in scopes]


def scan(repo: Path, flake8: str) -> list[dict]:
    files = subprocess.run(["git", "-C", str(repo), "ls-files", "*.py"], capture_output=True, text=True, check=True).stdout.split()
    chosen: set[str] = set()
    for inc, exc in flake8_hook_scopes(repo):
        for f in files:
            if inc and not re.search(inc, f):
                continue
            if exc and re.search(exc, f):
                continue
            chosen.add(f)
    sites: list[dict] = []
    batch = sorted(chosen)
    for i in range(0, len(batch), 200):
        r = subprocess.run([flake8, "--select=B914", "--max-line-length=512", *batch[i : i + 200]], cwd=repo, capture_output=True, text=True)
        for line in r.stdout.splitlines():
            m = re.match(r"^(.+?):(\d+):(\d+): (B914) ", line)
            if m:
                sites.append({"path": m.group(1), "line": int(m.group(2)), "col": int(m.group(3))})
        if r.returncode not in (0, 1):
            raise SystemExit(f"flake8 failed: {r.stderr[:2000]}")
    return sites


# ----------------------------------------------------------------------------------------------
# self-test
# ----------------------------------------------------------------------------------------------
def self_test() -> int:
    ok_cases = [
        ('x = ["a" "b"]\n', 'x = ["ab"]\n'),
        ("x = f('-x' '--y')\n", "x = f('-x--y')\n"),
        ('x = [f"{a} " "b"]\n', 'x = [f"{a} b"]\n'),
        ('x = ["{lit} " f"{a}"]\n', 'x = [f"{{lit}} {a}"]\n'),
        ('x = [r"\\d+" r"\\w"]\n', 'x = [r"\\d+\\w"]\n'),
        ('x = ["a" \'b\']\n', 'x = ["ab"]\n'),
        ('x = [b"a" b"b"]\n', 'x = [b"ab"]\n'),
        ('x = ["a" "b" "c",\n     "d"]\n', 'x = ["abc",\n     "d"]\n'),
        ('x = ["a" "b"\n     "c" "d"]\n', 'x = ["ab"\n     "cd"]\n'),
        ('x = [f"{a!r:>{w}}" "z"]\n', 'x = [f"{a!r:>{w}}z"]\n'),
        ('x = ["é — " "§5"]\n', 'x = ["é — §5"]\n'),
        ('y = "—"; x = g(k="a — " "b")\n', 'y = "—"; x = g(k="a — b")\n'),
        # mixed quotes: re-quote with the fewest escapes; a tie keeps the first part's quote
        ('x = ["a" \'"b\']\n', "x = ['a\"b']\n"),
        ('x = ["set -e\\n" \'url=""\\n\' \'for a in "$@"; do\\n\' "done\\n"]\n', "x = ['set -e\\nurl=\"\"\\nfor a in \"$@\"; do\\ndone\\n']\n"),
        ("x = [\"#!/bin/sh\\n\" f'cat \"{p}\" ;;\\n']\n", "x = [f'#!/bin/sh\\ncat \"{p}\" ;;\\n']\n"),
        ("x = [\"it's \" 'a \"q\"']\n", "x = ['it\\'s a \"q\"']\n"),
        ("x = [\"it's \" f'{d[\"k\"]}']\n", "x = [f'it\\'s {d[\"k\"]}']\n"),
        ('x = [r"a" "b"]\n', 'x = ["ab"]\n'),
    ]
    refuse_cases = [
        ('x = ["\\1" "2"]\n', "octal escape at the seam changes the value"),
        ('x = ["\\N{BULLET} " f"{a}"]\n', "\\N{...} into an f-string"),
        ('x = [r"\\d" "\\n"]\n', "raw + backslash"),
        ("x = [f'{d[\"k\"]}' f\"{e['j']}\"]\n", "each candidate quote occurs inside a replacement field"),
        ("x = [r'\"' r\"'\"]\n", "raw parts holding both quotes"),
    ]
    fails = 0
    for src, want in ok_cases:
        tree = ast.parse(src)
        nodes = string_nodes(tree)
        sites = [(n.lineno, n.col_offset + 1) for n in nodes]
        got, merged, skipped = fix_source(src, sites)
        if got != want:
            fails += 1
            print(f"FAIL ok-case {src!r}: got {got!r} want {want!r} skipped={skipped}")
    for src, why in refuse_cases:
        tree = ast.parse(src)
        sites = [(n.lineno, n.col_offset + 1) for n in string_nodes(tree)]
        got, merged, skipped = fix_source(src, sites)
        if got != src or not skipped:
            fails += 1
            print(f"FAIL refuse-case ({why}) {src!r}: got {got!r}")
    print(f"self-test: {len(ok_cases)} merge cases, {len(refuse_cases)} refusal cases, {fails} failure(s)")
    return 1 if fails else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--repo", required=True, type=Path)
    s.add_argument("--flake8", required=True)
    s.add_argument("--out", required=True, type=Path)
    f = sub.add_parser("fix")
    f.add_argument("--repo", required=True, type=Path)
    f.add_argument("--sites", required=True, type=Path)
    f.add_argument("--apply", action="store_true")
    f.add_argument("--report", type=Path)
    args = ap.parse_args()
    if args.cmd == "scan":
        sites = scan(args.repo, args.flake8)
        args.out.write_text(json.dumps(sites, indent=1))
        files = len({s["path"] for s in sites})
        print(f"B914 sites: {len(sites)} in {files} file(s) -> {args.out}")
        return 0
    sites = json.loads(args.sites.read_text())
    by_file: dict[str, list[tuple[int, int]]] = {}
    for s in sites:
        by_file.setdefault(s["path"], []).append((s["line"], s["col"]))
    report = {"merged": 0, "skipped": [], "files": []}
    for path, pos in sorted(by_file.items()):
        p = args.repo / path
        src = p.read_text()
        new, merged, skipped = fix_source(src, pos)
        report["merged"] += len(merged)
        for sk in skipped:
            sk["path"] = path
            report["skipped"].append(sk)
        if merged:
            report["files"].append(path)
            if args.apply:
                p.write_text(new)
        for m in merged:
            print(f"{path}:{m['line']}: {m['old']}  ->  {m['new']}")
    for sk in report["skipped"]:
        print(f"SKIPPED {sk['path']}:{sk['line']}:{sk['col']}: {sk['why']}  {sk.get('text', '')}")
    print(f"merged {report['merged']} run(s) in {len(report['files'])} file(s); skipped {len(report['skipped'])}; {'APPLIED' if args.apply else 'dry run'}")
    if args.report:
        args.report.write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
