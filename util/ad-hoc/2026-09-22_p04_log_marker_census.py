#!/usr/bin/env python3
"""Census every anchor juniper-ml's scripts match against cascor's log records, and resolve each.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc, roadmap step P0.4(c))
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc — investigation (produces the P0.4 named-marker inventory)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md §3.1 (P0.4),
         notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md §6 N-4

WHY THIS EXISTS

RECON N-4 rates anchored MESSAGE TEXT as BREAKING for "~17 juniper-ml scripts", and an envelope
check PASSES a message-text change. P0.4(c) therefore asks for "every marker string those scripts
anchor on", asserted to be still emitted. No artifact enumerated them: "~17" was a count with no
list behind it. This tool is the list, derived mechanically so it can be re-derived:

  1. DISCOVER consumers: tracked files under util/, scripts/, tests/ that name a cascor log
     (``juniper_cascor.log`` = the file sink, ``juniper-cascor.log`` / ``direct_cli.log`` = the
     redirected-stdout sink).
  2. EXTRACT every anchor: Python via the AST (``re.*`` pattern arguments, ``"x" in line``,
     ``.startswith("x")``, ``.count("x")``), bash via ``grep`` arguments on lines that reference a
     log, plus Python heredocs embedded in bash (parsed with the same AST path).
  3. CLASSIFY each anchor: ENVELOPE_SENTINEL / ENVELOPE_TIMESTAMP / ENVELOPE_FUNC_LINE are
     recognised by shape; everything else is MESSAGE unless it appears in ``CURATED`` below with a
     stated reason. An anchor that is neither is UNCLASSIFIED and the tool exits 1 -- a new
     consumer anchor forces a decision instead of silently falling out of the inventory.
  4. RESOLVE each MESSAGE anchor against cascor's source at a revision: the regex is reduced to
     its literal fragments (``sre_parse``), and a site is an emit site when one string literal
     (plain, f-string, or %-format -- an f-string placeholder becomes a gap) contains every
     fragment IN ORDER. The enclosing logger call gives the level. LIVE = at least one site;
     GONE = none (the consumer is already broken, or the marker only ever existed on a
     diagnostic branch).

A consumer's regex often reaches ACROSS the envelope into the message --
``calculate_accuracy:\\d+\\].*Calculated accuracy:`` anchors on the ``func:LINE]`` prefix AND on
message text. Such a pattern yields two anchors, one of each class.

LIMITS -- read before trusting a GONE

  * A fragment is searched in cascor ``src/`` only, excluding ``src/tests/`` and any
    ``backups/`` tree (dead code must not satisfy a presence check).
  * A message assembled in a variable and logged later still resolves (the literal is found),
    but its level is UNKNOWN: the enclosing-call walk only sees a literal that is an argument of
    the logger call itself.
  * Text that originates OUTSIDE cascor's source (a torch exception, a Python warning, uvicorn)
    is curated as MESSAGE_EXTERNAL; it can never resolve, and that is not a defect.

EXIT CODES

  0  census complete; every anchor classified
  1  at least one UNCLASSIFIED anchor (or, with --check-inventory, the inventory drifted)
  2  usage / IO error (a cascor revision that does not resolve, an unreadable file)

USAGE

    python3 util/ad-hoc/2026-09-22_p04_log_marker_census.py \\
        --cascor /home/pcalnon/Development/python/Juniper/juniper-cascor --rev origin/main \\
        [--json out.json] [--emit-inventory marker_inventory.json] [--check-inventory path]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

try:  # Python 3.11+ moved the parser; both names exist on 3.12/3.13/3.14 with a warning on the old one
    import re._parser as sre_parse  # type: ignore[import-not-found]
    import re._constants as sre_constants  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - older interpreters
    import sre_constants  # type: ignore[no-redef]
    import sre_parse  # type: ignore[no-redef]

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_NAME_RE = re.compile(r"juniper[_-]cascor\.log|direct_cli\.log")
RE_FUNCS = {"compile", "search", "match", "findall", "finditer", "fullmatch", "sub", "split"}
LOGGER_METHODS = {"trace": 1, "verbose": 5, "debug": 10, "info": 20, "warning": 30, "warn": 30, "error": 40, "exception": 40, "critical": 50, "fatal": 60}

# Files that name a cascor log but READ NO RECORD CONTENT -- they write the log, or mention it in
# prose. Excluded as a whole, with the reason, so the exclusion is reviewable.
EXCLUDED_FILES: dict[str, str] = {
    "util/experiment_stack.bash": "launcher: WRITES the redirected-stdout sink (nohup > juniper-cascor.log); its greps read ss/docker/pgrep output",
    "util/isolated_stack.bash": "launcher: WRITES the redirected-stdout sink; its greps read ss output",
    "tests/test_experiment_stack_script.py": "tests experiment_stack.bash's own text; names the log only in a comment",
    "util/experiments/run_suite.py": "names the log in docstrings/error text only; its patterns read its own banner, pyproject.toml and override keys",
    "util/ad-hoc/2026-09-22_p01_logging_corpus_run.bash": "P0.1 corpus launcher: counts .prof files, reads no record",
    "util/ad-hoc/2026-09-22_p04_log_marker_census.py": "this tool",
    "util/ad-hoc/2026-09-22_p04_log_shape_survey.py": "P0.4 shape survey: classifies envelopes, anchors on no marker",
}

# Anchors that are extracted but are NOT a cascor-record anchor, or whose text is not cascor's.
# Key: (consumer path, anchor text). Value: (classification, reason).
CURATED: dict[tuple[str, str], tuple[str, str]] = {}


def curate(path: str, text: str, klass: str, reason: str) -> None:
    CURATED[(path, text)] = (klass, reason)


# --- OTHER: extracted by the heuristics, but it reads something that is not a cascor record ---------
curate("util/ad-hoc/2026-08-10_ea_aggregate_clean.py", r"hidden_units=\d+: best (\S+)", "OTHER", "reads juniper-ml's own summary.md, not a cascor record")
curate("util/ad-hoc/2026-08-16_h2h_collect.py", r"-\d{8}T\d{6}Z$", "OTHER", "matches a suite DIRECTORY name stamp")
curate("util/ad-hoc/2026-08-26_t6_stop_evidence_scan.py", "LIVE", "OTHER", "classifies the tool's own verdict string")
curate("util/ad-hoc/2026-08-26_census_post588_run.bash", "auditor ARMED", "OTHER", "reads the import-auditor's own audit-logs/*.log, not cascor's")
curate("util/ad-hoc/2026-08-26_census_post588_run.bash", "FINAL modules=", "OTHER", "reads the import-auditor's own audit-logs/*.log, not cascor's")
curate("util/ad-hoc/2026-08-26_census_post588_run.bash", "FIRST-IMPORT", "OTHER", "reads the import-auditor's own audit-logs/*.log, not cascor's")
curate("util/ad-hoc/2026-09-08_relay_repair_sequence.bash", "=> VERDICT", "OTHER", "reads a probe's own ws_drop_*.log")
curate("util/ad-hoc/2026-09-08_relay_repair_sequence.bash", "healthy|sha", "OTHER", "reads leg_swap_B.log, the swap script's own output")
curate("util/ad-hoc/2026-09-08_relay_repair_sequence.bash", "CONSOLE\\[", "OTHER", "reads live_run_52.log, a browser-driver log")
curate("util/ad-hoc/2026-09-08_relay_repair_sequence.bash", "=> |server growth|cards  |glow  |F-026 samples|metrics store", "OTHER", "reads live_run_52.log, a browser-driver log")
curate("util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash", "juniper_train_", "OTHER", "matches /dev/shm segment names")
curate("util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash", "sem.mp-", "OTHER", "matches /dev/shm semaphore names")
curate("util/ad-hoc/2026-08-25_cascor_stop_during_training_repro.bash", "^(juniper_train_|sem\\.mp-)", "OTHER", "matches /dev/shm names")
curate("util/ad-hoc/2026-08-16_h2h_collect.py", "service", "OTHER", "a dict-key test on the arms mapping (`'service' in arms`)")
curate("util/ad-hoc/2026-08-16_h2h_collect.py", "cli", "OTHER", "a dict-key test on the arms mapping (`'cli' in arms`)")
curate("util/ad-hoc/2026-08-18_h2h_pair_compare.py", "-[ab]$", "OTHER", "strips a replicate suffix from a DIRECTORY name")
curate("util/ad-hoc/2026-08-26_g4_post_fix_analysis.py", "--pattern", "OTHER", "an argv membership test")
curate("util/ad-hoc/2026-08-26_g4_post_fix_analysis.py", "argv[argv.index('--pattern') + 1]", "OTHER", "operator-supplied override of UNGRACEFUL_DEFAULT; the default itself is censused at :90")
curate("util/ad-hoc/2026-08-10_ea_aggregate_clean.py", "pattern", "OTHER", "field(text, pattern): every call site passes a summary.md pattern (hidden_units / train_accuracy / val_accuracy / completion reason)")
# --- MESSAGE_EXTERNAL: the text is real log content, but cascor's source does not author it ----------
curate("util/ad-hoc/2026-08-10_ea_aggregate_clean.py", "out of memory", "MESSAGE_EXTERNAL", "torch/CUDA OOM text; cascor logs the exception, it does not author the phrase")
curate("util/ad-hoc/2026-08-26_census_post588_run.bash", "SENTRY_SDK_DSN is deprecated", "MESSAGE_EXTERNAL", "a Python DeprecationWarning on stderr (direct_cli.log), not a logger record")


@dataclass
class Anchor:
    consumer: str
    line: int
    kind: str  # regex | in | startswith | count | grep
    text: str
    klass: str = ""
    reason: str = ""
    fragments: list[str] = field(default_factory=list)
    tolerant_ms: bool | None = None
    sites: list[dict] = field(default_factory=list)
    status: str = ""  # LIVE | GONE | n/a


# ---------------------------------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------------------------------


def _fold(node: ast.AST, names: dict[str, ast.AST], depth: int = 0) -> str | None:
    """Fold a string-valued expression to its value, or None when it is not static."""
    if depth > 8:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold(node.left, names, depth + 1), _fold(node.right, names, depth + 1)
        return left + right if left is not None and right is not None else None
    if isinstance(node, ast.Name) and node.id in names:
        return _fold(names[node.id], names, depth + 1)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "compile" and node.args:
        return _fold(node.args[0], names, depth + 1)  # TS = re.compile(r"..."); later r"..." + TS.pattern is rare
    return None


def extract_python(source: str, consumer: str, line_offset: int = 0) -> list[Anchor]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    names: dict[str, ast.AST] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            names[stmt.targets[0].id] = stmt.value
    out: list[Anchor] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            owner = node.func.value
            if attr in RE_FUNCS and isinstance(owner, ast.Name) and owner.id == "re" and node.args:
                text = _fold(node.args[0], names)
                out.append(Anchor(consumer, node.lineno + line_offset, "regex" if text is not None else "dynamic", text if text is not None else ast.unparse(node.args[0])))
            elif attr in {"startswith", "endswith", "count"} and node.args:
                text = _fold(node.args[0], names)
                if text is not None:
                    out.append(Anchor(consumer, node.lineno + line_offset, "startswith" if attr != "count" else "count", text))
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn)):
            text = _fold(node.left, names)
            if text is not None and isinstance(node.comparators[0], (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
                out.append(Anchor(consumer, node.lineno + line_offset, "in", text))
    return out


# ANY heredoc: the interpreter is often a variable (``"${PY}" - "$RUN" <<'EOF'`` in the stop repro),
# so the start line cannot be keyed on the word "python". A body that parses as Python is treated
# as Python; one that does not (a PR body, a config file) yields no anchors and is skipped whole.
_HEREDOC_START = re.compile(r"<<-?\s*['\"]?(?P<tag>[A-Za-z_]+)['\"]?\s*$")
_GREP = re.compile(r"\bgrep\b(?P<flags>(?:\s+-{1,2}[A-Za-z-]+(?:=\S+)?)*)\s+(?:-e\s+)?(?P<q>['\"])(?P<pat>.*?)(?P=q)")
_LOGREF = re.compile(r"\.log\b|_LOG\b|LOG\}|\$\{?log\}?\b")
_BASH_ASSIGN = re.compile(r"^\s*(?P<name>[A-Z_][A-Z0-9_]*)=(?P<q>['\"])(?P<val>.*?)(?P=q)\s*$")


def extract_bash(source: str, consumer: str) -> list[Anchor]:
    out: list[Anchor] = []
    lines = source.splitlines()
    assigns: dict[str, str] = {}
    for ln in lines:
        m = _BASH_ASSIGN.match(ln)
        if m:
            assigns[m.group("name")] = m.group("val")
    i = 0
    while i < len(lines):
        ln = lines[i]
        hd = _HEREDOC_START.search(ln)
        if hd:
            tag, body_start = hd.group("tag"), i + 1
            j = body_start
            while j < len(lines) and lines[j].strip() != tag:
                j += 1
            out.extend(extract_python("\n".join(lines[body_start:j]), consumer, line_offset=body_start))
            i = j + 1
            continue
        for gm in _GREP.finditer(ln):
            rest = ln[: gm.start("q")] + ln[gm.end():]
            if not _LOGREF.search(rest):
                continue
            pat = gm.group("pat")
            var = re.fullmatch(r"\$\{?([A-Z_][A-Z0-9_]*)\}?", pat)
            if var and var.group(1) in assigns:
                pat = assigns[var.group(1)]
            out.append(Anchor(consumer, i + 1, "grep", pat))
        i += 1
    return out


def discover(repo: Path) -> list[Path]:
    listed = subprocess.run(["git", "ls-files", "util", "scripts", "tests"], cwd=repo, capture_output=True, text=True, check=True).stdout.split()
    found = []
    for rel in listed:
        if not rel.endswith((".py", ".bash", ".sh")) or "/retired/" in rel:
            continue
        try:
            text = (repo / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if LOG_NAME_RE.search(text):
            found.append(Path(rel))
    return sorted(found)


# ---------------------------------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------------------------------

_TS_SHAPE = re.compile(r"\\d\{4\}-\\d(?:\{2\}|\\d)")
_FUNC_LINE_PINNED = re.compile(r"(?<![\w.])([A-Za-z_]\w*):(\d{2,})\b")


def literal_runs(pattern: str) -> list[list[tuple[str, str]]]:
    """Reduce a regex to, per top-level alternative, a token list of ("lit", text) / ("gap", kind)."""
    try:
        parsed = sre_parse.parse(pattern)
    except re.error:
        return [[("lit", pattern)]]
    items = list(parsed)
    alternatives: list[list] = []
    if len(items) == 1 and items[0][0] == sre_constants.BRANCH:
        alternatives = [list(alt) for alt in items[0][1][1]]
    else:
        alternatives = [items]
    out = []
    for alt in alternatives:
        tokens: list[tuple[str, str]] = []
        buf = ""
        for op, av in alt:
            if op == sre_constants.LITERAL:
                buf += chr(av)
                continue
            if buf:
                tokens.append(("lit", buf))
                buf = ""
            if op in (sre_constants.MAX_REPEAT, sre_constants.MIN_REPEAT):
                inner = list(av[2])
                digit = len(inner) == 1 and inner[0][0] == sre_constants.IN and any(x == (sre_constants.CATEGORY, sre_constants.CATEGORY_DIGIT) for x in inner[0][1])
                tokens.append(("gap", "digits" if digit else "repeat"))
            else:
                tokens.append(("gap", str(op)))
        if buf:
            tokens.append(("lit", buf))
        out.append(tokens)
    return out


def classify(anchor: Anchor) -> list[Anchor]:
    """Return one or more classified anchors (a pattern spanning envelope and message yields two)."""
    cur = CURATED.get((anchor.consumer, anchor.text))
    if cur:
        anchor.klass, anchor.reason = cur
        anchor.status = "n/a"
        return [anchor]
    if anchor.kind == "dynamic":
        anchor.klass, anchor.reason, anchor.status = "UNCLASSIFIED", "pattern is not static; resolve its call sites by hand", "n/a"
        return [anchor]
    if anchor.kind == "startswith" and anchor.text == "+":
        anchor.klass, anchor.reason, anchor.status = "ENVELOPE_SENTINEL", "splits Path-A ('+') records from stdlib ones", "n/a"
        return [anchor]
    results: list[Anchor] = []
    if anchor.kind in ("regex", "grep") and _TS_SHAPE.search(anchor.text):
        # A timestamp group may be the whole pattern (``TS = re.compile(...)``) or be embedded in a
        # larger one (``r"fit:1918.*" + TS + r".*Starting ..."``); either way it is an envelope anchor.
        tolerant = bool(re.search(r"\(\?:,|,\(\\d\{3\}\)\)\?|,\\d\+\)\?|,\\d\{3\}\)\?", anchor.text))
        reason = "tolerates ',mmm' (Path C)" if tolerant else "SECONDS ONLY: a millisecond (Path C) record fails to match -- silently skipped"
        results.append(Anchor(anchor.consumer, anchor.line, anchor.kind, anchor.text, "ENVELOPE_TIMESTAMP", reason, tolerant_ms=tolerant, status="n/a"))
    message_alts: list[list[str]] = []
    envelope_notes: list[str] = []
    for tokens in literal_runs(anchor.text) if anchor.kind in ("regex", "grep") else [[("lit", anchor.text)]]:
        frags: list[str] = []
        k = 0
        while k < len(tokens):
            kind, val = tokens[k]
            if kind == "lit":
                pinned = _FUNC_LINE_PINNED.fullmatch(val.strip())
                nxt = tokens[k + 1] if k + 1 < len(tokens) else None
                nxt2 = tokens[k + 2] if k + 2 < len(tokens) else None
                if pinned:
                    envelope_notes.append(f"{val.strip()} -- func:LINE with a PINNED line number")
                elif val.endswith(":") and nxt == ("gap", "digits") and nxt2 is not None and nxt2[0] == "lit" and nxt2[1].startswith("]"):
                    func = val.rsplit(" ", 1)[-1]
                    envelope_notes.append(f"{func}\\d+] -- func:LINE prefix")
                    rest = nxt2[1][1:]
                    tokens[k + 2] = ("lit", rest)
                    k += 2
                    continue
                else:
                    # A quote at a fragment's EDGE is usually rendered by a placeholder, not written
                    # in the source: ``"Reloaded dataset %r (...)"`` emits ``Reloaded dataset 'x'``,
                    # so a consumer anchored on ``Reloaded dataset '`` would otherwise resolve GONE
                    # against a live message (observed 2026-09-23, g4_overhead_decomposition.py:56).
                    trimmed = val.strip("'\"")
                    if len(trimmed.strip()) >= 3:
                        frags.append(trimmed)
            k += 1
        if frags:
            message_alts.append(frags)
    if envelope_notes:
        results.append(Anchor(anchor.consumer, anchor.line, anchor.kind, anchor.text, "ENVELOPE_FUNC_LINE", "; ".join(envelope_notes), status="n/a"))
    for frags in message_alts:
        results.append(Anchor(anchor.consumer, anchor.line, anchor.kind, anchor.text, "MESSAGE", "", fragments=frags))
    if not results:
        anchor.klass, anchor.reason, anchor.status = "UNCLASSIFIED", "no envelope shape and no literal of >= 3 chars", "n/a"
        results.append(anchor)
    return results


# ---------------------------------------------------------------------------------------------------
# Resolution against cascor
# ---------------------------------------------------------------------------------------------------


class Cascor:
    def __init__(self, root: Path, rev: str) -> None:
        self.root, self.rev = root, rev
        res = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", f"{rev}^{{commit}}"], capture_output=True, text=True)
        if res.returncode != 0:
            raise SystemExit(f"census: cascor revision {rev!r} does not resolve in {root}: {res.stderr.strip()}")
        self.sha = res.stdout.strip()
        self._files: dict[str, list[tuple[int, str, str]]] = {}

    def grep_files(self, fragment: str) -> list[str]:
        cmd = ["git", "-C", str(self.root), "grep", "-F", "-l", "-e", fragment, self.sha, "--", "src", ":(exclude)src/tests", ":(exclude,glob)**/backups/**"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return [ln.split(":", 1)[1] for ln in res.stdout.splitlines() if ":" in ln]

    def skeletons(self, path: str) -> list[tuple[int, str, str]]:
        """(line, skeleton, enclosing logger method or '') for every string literal in *path*."""
        if path in self._files:
            return self._files[path]
        src = subprocess.run(["git", "-C", str(self.root), "show", f"{self.sha}:{path}"], capture_output=True, text=True).stdout
        out: list[tuple[int, str, str]] = []
        try:
            tree = ast.parse(src)
        except SyntaxError:
            self._files[path] = out
            return out
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        for node in ast.walk(tree):
            skel = None
            if isinstance(node, ast.JoinedStr):
                skel = "".join(v.value if isinstance(v, ast.Constant) else "\x00" for v in node.values)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and not isinstance(parents.get(id(node)), ast.JoinedStr):
                skel = node.value
            if skel is None:
                continue
            method = ""
            cur = parents.get(id(node))
            hops = 0
            while cur is not None and hops < 4:
                if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute) and cur.func.attr in LOGGER_METHODS:
                    method = cur.func.attr
                    break
                if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) and cur.func.id == "print":
                    method = "print"
                    break
                cur = parents.get(id(cur))
                hops += 1
            out.append((node.lineno, skel, method))
        self._files[path] = out
        return out

    def resolve(self, frags: list[str]) -> list[dict]:
        longest = max(frags, key=len)
        sites = []
        for path in self.grep_files(longest):
            for line, skel, method in self.skeletons(path):
                pos = 0
                ok = True
                for frag in frags:
                    at = skel.find(frag, pos)
                    if at < 0:
                        ok = False
                        break
                    pos = at + len(frag)
                if ok:
                    sites.append({"file": path, "line": line, "method": method or "UNKNOWN"})
        return sites


# ---------------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------------


def run(args: argparse.Namespace) -> int:
    cascor = Cascor(Path(args.cascor).expanduser(), args.rev)
    consumers = discover(REPO_ROOT)
    anchors: list[Anchor] = []
    for rel in consumers:
        key = rel.as_posix()
        if key in EXCLUDED_FILES:
            continue
        text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
        raw = extract_python(text, key) if rel.suffix == ".py" else extract_bash(text, key)
        for anchor in raw:
            anchors.extend(classify(anchor))
    for anchor in anchors:
        if anchor.klass == "MESSAGE":
            anchor.sites = cascor.resolve(anchor.fragments)
            anchor.status = "LIVE" if anchor.sites else "GONE"

    print(f"census: juniper-ml {REPO_ROOT.name}  cascor {cascor.root} @ {args.rev} = {cascor.sha[:10]}")
    print(f"census: {len(consumers)} files name a cascor log; {len(EXCLUDED_FILES)} excluded by rule; {len({a.consumer for a in anchors})} carry anchors; {len(anchors)} anchors")
    by_class: dict[str, int] = {}
    for a in anchors:
        by_class[a.klass] = by_class.get(a.klass, 0) + 1
    print("census: by class: " + ", ".join(f"{k}={v}" for k, v in sorted(by_class.items())))
    live = sum(1 for a in anchors if a.status == "LIVE")
    gone = sum(1 for a in anchors if a.status == "GONE")
    print(f"census: MESSAGE anchors LIVE={live} GONE={gone}")
    print()
    for a in sorted(anchors, key=lambda a: (a.consumer, a.line, a.klass)):
        where = ""
        if a.status == "LIVE":
            where = "; ".join(f"{s['file']}:{s['line']} {s['method']}" for s in a.sites[:3]) + (f" (+{len(a.sites) - 3})" if len(a.sites) > 3 else "")
        extra = f"frags={a.fragments!r}" if a.klass == "MESSAGE" else a.reason
        print(f"{a.consumer}:{a.line}\t{a.klass}\t{a.status}\t{extra}\t{where}")

    if args.json:
        Path(args.json).write_text(json.dumps({"cascor_rev": cascor.sha, "anchors": [asdict(a) for a in anchors]}, indent=2) + "\n", encoding="utf-8")
    inventory = build_inventory(anchors, cascor.sha)
    if args.emit_inventory:
        Path(args.emit_inventory).write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
        print(f"\ncensus: wrote {len(inventory['markers'])} LIVE markers to {args.emit_inventory}")
    rc = 1 if by_class.get("UNCLASSIFIED") else 0
    if args.check_inventory:
        committed = json.loads(Path(args.check_inventory).read_text(encoding="utf-8"))
        want = {tuple(m["fragments"]) for m in inventory["markers"]}
        have = {tuple(m["fragments"]) for m in committed.get("markers", [])}
        missing, extra = sorted(want - have), sorted(have - want)
        for frags in missing:
            print(f"census: DRIFT -- consumed but NOT in {args.check_inventory}: {list(frags)!r}")
        for frags in extra:
            print(f"census: DRIFT -- in {args.check_inventory} but no longer consumed: {list(frags)!r}")
        if missing or extra:
            rc = 1
    if by_class.get("UNCLASSIFIED"):
        print("\ncensus: UNCLASSIFIED anchors exist -- add each to CURATED with a reason, or teach classify() the shape")
    return rc


def build_inventory(anchors: list[Anchor], sha: str) -> dict:
    markers: dict[tuple[str, ...], dict] = {}
    for a in anchors:
        if a.klass != "MESSAGE" or a.status != "LIVE":
            continue
        key = tuple(a.fragments)
        entry = markers.setdefault(key, {"fragments": list(a.fragments), "sites": [], "consumers": []})
        for s in a.sites:
            site = {"file": s["file"], "method": s["method"]}
            if site not in entry["sites"]:
                entry["sites"].append(site)
        ref = f"juniper-ml/{a.consumer}:{a.line}"
        if ref not in entry["consumers"]:
            entry["consumers"].append(ref)
    for entry in markers.values():
        # The level a consumer can rely on is the HIGHEST level at which any site emits it: a run
        # at that level sees the record. Lowering the last such site (info -> debug) silently
        # removes the marker from every run below the new level -- a change the source text alone
        # would never reveal. None when no site is a recognisable logger call (presence-only).
        known = [LOGGER_METHODS[s["method"]] for s in entry["sites"] if s["method"] in LOGGER_METHODS]
        entry["required_level"] = max(known) if known else None
        entry["sites"].sort(key=lambda s: (s["file"], s["method"]))
        entry["consumers"].sort()
    envelope: dict[str, list[str]] = {}
    for a in anchors:
        if a.klass.startswith("ENVELOPE_"):
            label = a.klass + (" (seconds-only)" if a.tolerant_ms is False else "")
            envelope.setdefault(label, []).append(f"juniper-ml/{a.consumer}:{a.line}")
    return {
        "generated_by": "juniper-ml/util/ad-hoc/2026-09-22_p04_log_marker_census.py",
        "cascor_rev": sha,
        "envelope_consumers": envelope,
        "markers": sorted(markers.values(), key=lambda m: m["fragments"]),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cascor", default="/home/pcalnon/Development/python/Juniper/juniper-cascor", help="juniper-cascor checkout (only its object store is read)")
    ap.add_argument("--rev", default="origin/main", help="cascor revision to resolve markers against (default origin/main)")
    ap.add_argument("--json", help="write the full census as JSON")
    ap.add_argument("--emit-inventory", help="write the LIVE-marker inventory JSON (the cascor fixture's source)")
    ap.add_argument("--check-inventory", help="compare against a committed inventory; exit 1 on drift")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"census: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
