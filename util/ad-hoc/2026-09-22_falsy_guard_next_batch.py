#!/usr/bin/env python3
"""2026-09-22_falsy_guard_next_batch.py -- apply the §6 BAR to the falsy-guard remainder.

Project: juniper-ml
Sub-Project: ad-hoc tooling (evidence-based triage)
Application: ad-hoc analysis
Author: Paul Calnon
License: MIT License

WHY THIS EXISTS

`notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md` §6 closes with a bar,
not a count:

    "The six fixed here were not chosen by count -- they were chosen because the file's own
     helper and its own `isinstance` precedent proved the author already considered the value
     untrusted. That is the bar for the next batch."

Nothing implements that bar. The census answers "where are the guards?", the triage answers
"where could a bad value come from?", and both say plainly that a count is not a verdict. The
question neither asks is the one §6 actually sets: **does this file already prove, in its own
source, that its author treats this value as untrusted -- and then fail to apply that belief
at some other site?**

That is the ml#1914 argument for `run_experiment.py`:1718 / :2065 generalised. There the proof
was same-key: the file read `meta` defensively at :1213 and :1658
(`x.get("meta") if isinstance(x.get("meta"), dict) else {}`) and bare at :1718 / :2065 -- the
author's own belief, unapplied at two sites.

WHAT IT REPORTS

For every read-class guard the census found, in a NON-ad-hoc file, this classifies the
in-file evidence that the author already distrusts the value:

  * `same-key`   -- the SAME key is read defensively elsewhere in this file (an
    `isinstance(..., dict)` test on a `.get(K)`, or a local coercer applied to one).
    This is the ml#1914 proof shape and the only tier that carries on its own.
  * `helper`     -- the file defines a local mapping coercer / validator (a function whose
    body tests `isinstance(..., dict)` and either returns `{}` or raises) and does not apply
    it here. `_mapping` in run_experiment.py and `_require_mapping` in run_suite.py are the
    two known shapes.
  * `file-level` -- the file contains SOME defensive `isinstance(..., dict)` read, but on a
    different key and through no reusable helper. Weakest; a prompt to look, not evidence.
  * `none`       -- no in-file evidence. §6 says leave it alone.

LIMITS -- read these before quoting anything below

  * THE BAR IS NOT A DEFECT TEST. `same-key` means the author guarded this key somewhere
    else, not that a truthy non-dict reaches THIS line. A site can clear the bar and still be
    unreachable. Only a failing test decides, which is why the output is a CANDIDATE LIST.
  * IT INHERITS THE CENSUS'S BLIND SPOT. Guards nested inside `while:` / `try:` / `if:` /
    `for:` are absent from the census input and therefore absent here. Run the triage's
    `--blind-spot` arm for those; this tool does not re-derive them.
  * A HELPER MAY BE DELIBERATELY UNAPPLIED. `run_suite.py` gates the whole document once at
    `load_suite` and reads it bare thereafter ON PURPOSE -- the type check already ran. A
    `helper` verdict there is correct about the source and wrong about the risk, which is why
    a raising validator's key arguments are reported as a load-time gate.
  * Evidence is traced WITHIN ONE FILE, exactly as the triage is, and for the same reason:
    interprocedural analysis is a different tool and pretending otherwise is how the first
    census produced a number nobody could defend.

EXIT CODES

  * 0 -- ran and reported.
  * 2 -- census JSON missing/unreadable, or it contained no read-class row. A screen that
         examined nothing must not print zero and exit clean.

Usage:
    python3 util/ad-hoc/2026-09-11_falsy_guard_census.py --json util/ > /tmp/c.json
    python3 util/ad-hoc/2026-09-22_falsy_guard_next_batch.py /tmp/c.json
    python3 util/ad-hoc/2026-09-22_falsy_guard_next_batch.py /tmp/c.json --tier same-key
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

TIERS = ("same-key", "helper", "file-level", "none")

#: Statement ceiling for "this function is a mapping coercer". `_mapping` is 1 statement and
#: `_require_mapping` is 3; anything an order of magnitude larger is an ordinary function that
#: merely contains an isinstance test. See `_FileEvidence._find_helpers`.
MAX_HELPER_STMTS = 12


def _get_key(node: ast.AST) -> "str | None":
    """The literal key of a `X.get('k')` / `X['k']` read, else None."""
    if isinstance(node, ast.Call):
        fn = node.func
        if isinstance(fn, ast.Attribute) and fn.attr == "get" and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                return a.value
    if isinstance(node, ast.Subscript):
        s = node.slice
        if isinstance(s, ast.Constant) and isinstance(s.value, str):
            return s.value
    return None


def _is_dict_isinstance(node: ast.AST) -> "ast.Call | None":
    """`isinstance(<expr>, dict)` -> the call node, else None."""
    if not isinstance(node, ast.Call):
        return None
    if not (isinstance(node.func, ast.Name) and node.func.id == "isinstance"):
        return None
    if len(node.args) != 2:
        return None
    t = node.args[1]
    names: list[str] = []
    if isinstance(t, ast.Name):
        names = [t.id]
    elif isinstance(t, ast.Tuple):
        names = [e.id for e in t.elts if isinstance(e, ast.Name)]
    if not any(n in ("dict", "Mapping", "MutableMapping") for n in names):
        return None
    return node


class _FileEvidence:
    """Everything one file says about whether its author distrusts a read."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.defensive_keys: set[str] = set()
        self.defensive_sites: dict[str, list[int]] = defaultdict(list)
        self.helpers: dict[str, int] = {}
        self.helper_applied_keys: set[str] = set()
        self.any_defensive = False
        self.gate_keys: set[str] = set()
        try:
            self.tree: "ast.Module | None" = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            self.tree = None
            return
        self._find_helpers()
        self._find_defensive_reads()

    def _find_helpers(self) -> None:
        """A local function is a mapping coercer if it tests isinstance(...,dict) and either
        returns an empty dict or raises. Both shapes exist in this repo (`_mapping`,
        `_require_mapping`).

        SIZE-BOUNDED ON PURPOSE. Without the bound this matched any large function that
        happened to contain an isinstance-dict test and a `raise` somewhere -- it named
        `expand_cells` and `materialise_cell` in run_suite.py as "helpers", which is a
        statement about the AST walk, not about the file. A coercer is small by nature; a
        function over MAX_HELPER_STMTS statements is doing something else and naming it here
        would repeat the over-broad-pattern failure the census itself was rebuilt to fix.
        """
        assert self.tree is not None
        for fn in ast.walk(self.tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(_is_dict_isinstance(n) for n in ast.walk(fn)):
                continue
            if sum(1 for n in ast.walk(fn) if isinstance(n, ast.stmt)) > MAX_HELPER_STMTS:
                continue
            returns_empty = any(
                isinstance(n, ast.Return) and isinstance(n.value, ast.Dict) and not n.value.keys
                for n in ast.walk(fn)
            )
            raises = any(isinstance(n, ast.Raise) for n in ast.walk(fn))
            if returns_empty or raises:
                self.helpers[fn.name] = fn.lineno

    def _find_defensive_reads(self) -> None:
        assert self.tree is not None
        for node in ast.walk(self.tree):
            call = _is_dict_isinstance(node)
            if call is not None:
                self.any_defensive = True
                k = _get_key(call.args[0])
                if k:
                    self.defensive_keys.add(k)
                    self.defensive_sites[k].append(getattr(call, "lineno", 0))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.helpers:
                for a in node.args:
                    k = _get_key(a)
                    if k:
                        self.helper_applied_keys.add(k)
                        self.defensive_sites[k].append(getattr(node, "lineno", 0))
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        # `_require_mapping(doc, "suite")` -- a load-time gate keyed by name
                        self.gate_keys.add(a.value)
                        self.helper_applied_keys.add(a.value)
                        self.defensive_sites[a.value].append(getattr(node, "lineno", 0))


def classify(ev: _FileEvidence, key: "str | None") -> str:
    if ev.tree is None:
        return "none"
    if key and (key in ev.defensive_keys or key in ev.helper_applied_keys):
        return "same-key"
    if ev.helpers:
        return "helper"
    if ev.any_defensive:
        return "file-level"
    return "none"


GUARD_KEY = re.compile(r"""\.get\(\s*['"]([^'"]+)['"]|\[\s*['"]([^'"]+)['"]\s*\]""")


def guard_key(expr: str) -> "str | None":
    m = GUARD_KEY.search(expr or "")
    if not m:
        return None
    return m.group(1) or m.group(2)


def main(argv: "list[str] | None" = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("census_json")
    p.add_argument("--tier", choices=TIERS, default=None, help="show only this tier")
    p.add_argument("--include-adhoc", action="store_true", help="include util/ad-hoc one-shots (default: excluded)")
    args = p.parse_args(argv)

    try:
        rows = json.loads(Path(args.census_json).read_text())
    except (OSError, ValueError) as exc:
        print(f"cannot read census JSON {args.census_json}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(rows, list) or not rows:
        print("census JSON held no rows -- refusing to report a vacuous zero", file=sys.stderr)
        return 2

    reads = [r for r in rows if (r.get("reads_untrusted") or r.get("risk") == "read")]
    if not reads:
        print("census JSON held no read-class row -- refusing to report a vacuous zero", file=sys.stderr)
        return 2
    if not args.include_adhoc:
        reads = [r for r in reads if "/ad-hoc/" not in r["file"]]
    if not reads:
        print("every read-class row was a util/ad-hoc one-shot; nothing to triage", file=sys.stderr)
        return 2

    # collapse uses -> distinct guards, the unit of REPAIR (triage §2a)
    guards: dict[tuple, dict] = {}
    for r in reads:
        k = (r["file"], r["guard_line"], r["guard"])
        g = guards.setdefault(k, {"file": r["file"], "line": r["guard_line"], "expr": r["guard"], "uses": 0})
        g["uses"] += 1

    ev_cache: dict[str, _FileEvidence] = {}
    by_tier: dict[str, list[dict]] = defaultdict(list)
    for g in guards.values():
        ev = ev_cache.get(g["file"])
        if ev is None:
            ev = ev_cache[g["file"]] = _FileEvidence(Path(g["file"]))
        key = guard_key(g["expr"])
        g["key"] = key
        g["tier"] = classify(ev, key)
        g["precedent"] = sorted(set(ev.defensive_sites.get(key or "", ())))
        g["helpers"] = ev.helpers
        g["gate"] = key in ev.gate_keys if key else False
        by_tier[g["tier"]].append(g)

    nfiles = len({g["file"] for g in guards.values()})
    print(f"distinct guards (unit of REPAIR): {len(guards)}   across {nfiles} file(s)")
    print("excluding util/ad-hoc/ one-shots" if not args.include_adhoc else "including util/ad-hoc/ one-shots")
    print()
    print("by in-file evidence that the author already distrusts the value:")
    for t in TIERS:
        print(f"  {t:<12} {len(by_tier[t]):>3} guard(s)")
    print()

    for t in TIERS:
        if args.tier and t != args.tier:
            continue
        rowset = sorted(by_tier[t], key=lambda g: (g["file"], g["line"]))
        if not rowset:
            continue
        print(f"=== {t} ({len(rowset)} guard(s)) ===")
        for g in rowset:
            print(f"  {g['file']}:{g['line']}  [{g['uses']} use(s)]  key={g['key']!r}")
            print(f"      {g['expr']}")
            if t == "same-key" and g["precedent"]:
                where = "LOAD-TIME GATE" if g["gate"] else "same key read defensively"
                print(f"      PRECEDENT: {where} at line(s) {g['precedent']}")
            if t == "helper" and g["helpers"]:
                hs = ", ".join(f"{n}():{ln}" for n, ln in sorted(g["helpers"].items(), key=lambda kv: kv[1]))
                print(f"      HELPER DEFINED IN FILE, not applied here: {hs}")
        print()

    print("A tier is not a verdict. `same-key` proves the AUTHOR guarded this key elsewhere,")
    print("not that a truthy non-dict reaches this line. Only a failing test decides that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
