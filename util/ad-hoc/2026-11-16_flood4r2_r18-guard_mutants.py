#!/usr/bin/env python3
"""
One-line mutants of every function the agent guard's 1.4.0 hardening changed, against its two guard suites.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py 1.4.0; tests/test_claude_agent_guard.py; tests/test_claude_agent_guard_brace_cap.py;
         util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_mutants.py (the 1.3.0 carrier's mutation run).

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_mutants.py <repo root> <scratch dir> <out.json> <main guard.py> [<id> ...]

With mutant ids after the main guard, only those mutants run.

The repository's files are never written. Each of up to 4 workers gets its own COPY of the guard and the two
suites (with tests/redacted_env.py) under <scratch dir>. For each mutant the pristine guard text has ONE
substring replaced (the substring must occur exactly once, else the mutant is reported "not applied"), the copy is
written, stale __pycache__ is removed, and the brace-cap suite and the guard suite's Bash and MCP rule tests and its
self-test check run (``-f``, unittest exit status: non-zero = killed). The pristine guard is written back in a
``finally:`` block and its sha256 checked after every mutant. Last, main's guard runs the same tests: they must fail.
Every child runs with the six Sentry variables empty and a dead session bus.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- runs unittest on scratch copies
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
FILES = ("util/claude_agent_guard.py", "tests/test_claude_agent_guard.py", "tests/test_claude_agent_guard_brace_cap.py", "tests/redacted_env.py")
RUNS = (["tests/test_claude_agent_guard_brace_cap.py"], ["tests/test_claude_agent_guard.py", "-k", "BashRuleTests", "-k", "McpRuleTests", "-k", "test_self_test_passes"])

# (id, the function, the text replaced, its replacement)
MUTANTS = [
    ("M01", "_param_close", '        if s[j] == "}":\n            return j\n        end = _step_over(s, j)', '        if s[j] == "}" and j < 0:\n            return j\n        end = _step_over(s, j)'),
    ("M02", "_comsub_close (case)", 'elif command and word == "case":', 'elif command and word == "kase":'),
    ("M03", "_skip_heredoc_bodies", "            if text == delim:", "            if text == delim + \"x\":"),
    ("M04", "_comsub_close (comment)", '        elif ch == "#":\n            k = s.find("\\n", j)', '        elif ch == "\\x00":\n            k = s.find("\\n", j)'),
    ("M05", "_brace_mask (backslash)", '        if c == "\\\\" and quoted != "\'":', '        if c == "\\\\" and quoted == "x":'),
    ("M06", "_MASKED ($)", ', "$": chr(0xE005)}', "}"),
    ("M07", "_brace_mask (comsub in quotes)", "            elif quoted == '\"' and c == \"$\" and nxt == \"(\":", "            elif quoted == 'x' and c == \"$\" and nxt == \"(\":"),
    ("M08", "_brace_mask (${ level)", '            elif params and c in ",.":', '            elif params and c in "":'),
    ("M09", "_brace_mask ($')", "        elif c == \"$\" and nxt == \"'\":\n            end = _ansi_c_end(raw, i + 2)", "        elif c == \"$\" and nxt == \"x\":\n            end = _ansi_c_end(raw, i + 2)"),
    ("M10", "_first_brace_group ({} rule)", "            found = None  # bash's {} rule", "            found = found  # bash's {} rule"),
    ("M11", "bash_brace_expand", '    if "{" not in masked:\n        return [raw]', '    if "{" in masked:\n        return [raw]'),
    ("M12", "_bash_view (assignment prefix)", "(word.text in KEYWORDS or _ASSIGN_RE.match(word.raw or \"\"))", "(word.text in KEYWORDS)"),
    ("M13", "_bash_view (here-string)", 'word.kind in ("herestring", "heredoc", "heredoc-strip") else', 'word.kind in ("heredoc", "heredoc-strip") else'),
    ("M14", "_spliced", "        out.append(_SPLICED)", '        out.append("")'),
    ("M15", "_glob_pattern (computed part)", '    pattern = comp.replace(_SPLICED, "*")', "    pattern = comp"),
    ("M16", "_glob_pattern (extglob)", '    reduced = _EXTGLOB_GROUP_RE.sub("*", pattern)\n    while', "    reduced = pattern\n    while"),
    ("M17", "_names_b (empty reading)", '    if comp.replace(_SPLICED, "").casefold() == target:', "    if comp.casefold() == target:"),
    ("M18", "_names_b (bare dot)", '    if not bare_dot and not _glob_literal_chars(pattern).strip("."):', '    if not _glob_literal_chars(pattern).strip("."):'),
    ("M19", "_claude_protected_b", "    return _SPLICED in rest[1] or any(", "    return any("),
    ("M20", "_readings_b (normalise)", '    return _unique([os.path.normpath(os.path.join(root, tail.lstrip("/"))) for root in roots])', '    return _unique([os.path.join(root, tail.lstrip("/")) for root in roots])'),
    ("M21", "_readings_b (~+)", '            roots = list(bases) if spliced.startswith("~+") else list(bases) + list(self.ctx.home_variants)', "            roots = list(bases) + list(self.ctx.home_variants)"),
    ("M22", "is_signing_mention", 'if any(a == ".git" and b == "hooks" for a, b in zip(parts, parts[1:])):', 'if any(a == ".git" and b == "hookz" for a, b in zip(parts, parts[1:])):'),
    ("M23", "_scan (two readings)", '            for mode in ("A", "B"):', '            for mode in ("A",):'),
    ("M24", "_expand (reading A defers)", "        except MalformedInput:\n            return []", "        except KeyError:\n            return []"),
    ("M25", "_path_word (component defers)", "            except MalformedInput:  # a component's own expansion past the cap", "            except KeyError:  # a component's own expansion past the cap"),
    ("M26", "_segment (raw rules on bash's words)", '        if self._mode == "B":  # the raw-text rules', '        if self._mode == "C":  # the raw-text rules'),
    ("M27", "Lexer.run (extglob group)", "            elif self.faithful and ch in _EXTGLOB_OPENERS and nxt == \"(\":", "            elif self.faithful and ch in \"\" and nxt == \"(\":"),
    ("M28", "Lexer._close", '        return _comsub_close(self.s, j) if opener == "(" else _param_close(self.s, j)', "        return _find_close(self.s, j, opener)"),
    ("M29", "Lexer.word_only (escape)", '                self.quoted = True\n                self._add(nxt or "\\\\")\n                self.i += 2\n            elif ch == "\'":\n                k = s.find("\'", self.i + 1)\n                self.quoted = True\n                self._add(s[self.i + 1 :] if k < 0 else s[self.i + 1 : k])\n                self.i = self.n if k < 0 else k + 1\n            elif ch == \'"\':\n                self.quoted = True\n                self.i = self._double(self.i + 1)\n            elif ch == "$":\n                self.i = self._dollar(self.i, False)\n            elif ch == "`":\n                self.i = self._backtick(self.i)\n            elif ch in "<>" and nxt == "(":\n                end = self._close("(", self.i + 2)', '                self.quoted = True\n                self._add("\\\\" + nxt)\n                self.i += 2\n            elif ch == "\'":\n                k = s.find("\'", self.i + 1)\n                self.quoted = True\n                self._add(s[self.i + 1 :] if k < 0 else s[self.i + 1 : k])\n                self.i = self.n if k < 0 else k + 1\n            elif ch == \'"\':\n                self.quoted = True\n                self.i = self._double(self.i + 1)\n            elif ch == "$":\n                self.i = self._dollar(self.i, False)\n            elif ch == "`":\n                self.i = self._backtick(self.i)\n            elif ch in "<>" and nxt == "(":\n                end = self._close("(", self.i + 2)'),
    ("M30", "_comsub_close (here-document)", '            elif s.startswith("<<", j):\n                strip = s.startswith("<<-", j)', '            elif s.startswith("<<<<", j):\n                strip = s.startswith("<<-", j)'),
    ("M41", "_comsub_close (here-string)", "            if s.startswith(\"<<<\", j):  # a here-string, not a here-document\n                j += 3", "            if s.startswith(\"<<<<\", j):  # a here-string, not a here-document\n                j += 3"),
    ("M31", "_comsub_close (arithmetic)", '    if s[j : j + 1] == "(":\n        return _paren_close(s, j, 1)', '    if s[j : j + 1] == "(":\n        return _paren_close(s, j, 2)'),
    ("M32", "_heredoc_word (quoted delimiter)", "            out.append(s[j + 1 : k])\n            j = k + 1", "            out.append(s[j : k])\n            j = k + 1"),
    ("M33", "_step_over ($')", '    if ch == "$" and nxt == "\'":\n        return _ansi_c_end(s, j + 2)', '    if ch == "$" and nxt == "x":\n        return _ansi_c_end(s, j + 2)'),
    ("M35", "_path_word_b (home rests)", "            if _SPLICED in head or any(_names_b(head, name, bare_dot=True, dotglob=dotglob) for name in CRED_DIR_NAMES):", "            if any(_names_b(head, name, bare_dot=True, dotglob=dotglob) for name in CRED_DIR_NAMES):"),
    ("M36", "_path_word_b (signing on readings)", "        if self.ctx.is_signing_mention(readings):", "        if self.ctx.is_signing_mention([]):"),
    ("M37", "_command (reading A defers)", "        if not alts:  # reading A would refuse it", "        if alts is None:  # reading A would refuse it"),
    ("M38", "_opaque_fallback", "            except MalformedInput:  # reading B has refused it already", "            except KeyError:  # reading B has refused it already"),
    ("M39", "substitutions (faithful)", "            end = _comsub_close(text, j + 2) if faithful else _find_close(text, j + 2, \"(\")", "            end = _find_close(text, j + 2, \"(\")"),
    ("M42", "_bash_view (budget of words made)", "                    if self._made[0] < 0:\n", "                    if self._made[0] < -(10**12):\n"),
    ("M40", "_scan (memo)", "        if key in self._scanned:  # the two readings meet the same nested text; one scan judges it\n            return", "        if key in self._scanned and False:  # the two readings meet the same nested text; one scan judges it\n            return"),
    # round 2 (2026-11-16): the code the validation's findings F2-F5 and F7 added
    ("M43", "_path_word_b (.git + hooks)", '_can_be_b(b, "hooks") for a, b in zip(comps, comps[1:])', '_can_be_b(b, "hookz") for a, b in zip(comps, comps[1:])'),
    ("M44", "_path_word_b (~/.gitconfig)", 'if _names_b(head, ".gitconfig", dotglob=dotglob) or', 'if _names_b(head, ".gitconfiq", dotglob=dotglob) or'),
    ("M45", "_path_word_b (~/.config/git)", '_can_be_b(rest[1], "git")', '_can_be_b(rest[1], "gjt")'),
    ("M46", "_path_word_b (system gitconfig)", "for system in _SYSTEM_GITCONFIG_PARTS):", "for system in ()):"),
    ("M47", "_can_be_b (a glob)", "    return fnmatch.fnmatchcase(name.casefold(), pattern.casefold())\n\n\ndef _empty_reading", "    return False\n\n\ndef _empty_reading"),
    ("M48", "_scan (the splice views)", "                    for view, changed in self._splice_views(segments):", "                    for view, changed in []:"),
    ("M49", "_default_reading", "        m = _PARAM_DEFAULT_RE.match(word.text[start:end])", "        m = None"),
    ("M50", "_names_b (dotglob)", "    if dotglob:\n        return fnmatch.fnmatchcase(target, pattern.casefold())\n", ""),
    ("M51", "analyze (the dotglob flag)", "        self._dotglob = bool(_DOTGLOB_RE.search(command))", "        self._dotglob = False"),
    ("M52", "_dispatch (alias)", '        elif name == "alias":', '        elif name == "alias-x":'),
    ("M53", "_cd_bases (the cap, in the loop)", "            if len(out) > MAX_CD_BASES:", "            if len(out) > MAX_CD_BASES * 10**9:"),
    ("M54", "_tick", "        if self._deadline is not None and time.monotonic() > self._deadline:", "        if self._deadline is None and time.monotonic() > self._deadline:"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child_env() -> dict:
    env = dict(os.environ)
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    return env


def run_tests(tree: Path) -> tuple:
    shutil.rmtree(tree / "util" / "__pycache__", ignore_errors=True)
    shutil.rmtree(tree / "tests" / "__pycache__", ignore_errors=True)
    failed = []
    for args in RUNS:
        proc = subprocess.run([sys.executable, "-m", "unittest", "-f", *args], cwd=str(tree), env=child_env(), capture_output=True, text=True, timeout=900, check=False)  # nosec B603 -- unittest on a scratch copy
        if proc.returncode != 0:
            last = [line for line in proc.stderr.splitlines() if line.startswith(("FAIL:", "ERROR:"))]
            failed.append((args[0], last[:2]))
    return (not failed), failed


def main(argv: list) -> int:
    repo = Path(argv[1]).resolve()
    scratch = Path(argv[2]).resolve()
    out = Path(argv[3])
    main_guard = Path(argv[4]).resolve()
    pristine = (repo / FILES[0]).read_text(encoding="utf-8")
    pristine_sha = hashlib.sha256(pristine.encode("utf-8")).hexdigest()
    trees = []
    for k in range(4):
        tree = scratch / ("w%d" % k)
        for rel in FILES:
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / rel, tree / rel)
        trees.append(tree)
    free = list(trees)
    lock = threading.Lock()

    def one(mutant: tuple) -> dict:
        mid, func, old, new = mutant
        count = pristine.count(old)
        if count != 1:
            return {"id": mid, "function": func, "result": "not applied (%d matches)" % count}
        with lock:
            tree = free.pop()
        target = tree / FILES[0]
        try:
            target.write_text(pristine.replace(old, new, 1), encoding="utf-8")
            passed, failed = run_tests(tree)
        finally:
            target.write_text(pristine, encoding="utf-8")
            restored = sha256(target) == pristine_sha
            with lock:
                free.append(tree)
        return {"id": mid, "function": func, "result": "survived" if passed else "killed", "failing": failed, "restored_sha256_ok": restored}

    chosen = [m for m in MUTANTS if not argv[5:] or m[0] in argv[5:]]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(one, chosen))
    # main's guard under the new tests: they must fail
    tree = trees[0]
    target = tree / FILES[0]
    try:
        shutil.copyfile(main_guard, target)
        main_passed, main_failed = run_tests(tree)
    finally:
        target.write_text(pristine, encoding="utf-8")
    summary = {"mutants": len(chosen), "killed": sum(r["result"] == "killed" for r in results), "survived": [r["id"] for r in results if r["result"] == "survived"], "not_applied": [r["id"] for r in results if r["result"].startswith("not applied")], "all_restored": all(r.get("restored_sha256_ok", True) for r in results), "repo_guard_sha256_unchanged": sha256(repo / FILES[0]) == pristine_sha, "tests_on_main_guard": "pass (VACUOUS)" if main_passed else "fail, as they must", "main_failures": main_failed}
    out.write_text(json.dumps({"summary": summary, "results": results}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    for r in results:
        print(r["id"], r["function"], r["result"])
    return 0 if not summary["survived"] and not summary["not_applied"] and not main_passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
