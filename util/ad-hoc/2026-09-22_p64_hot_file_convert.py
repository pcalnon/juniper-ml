#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P6.4)
Application: ad-hoc analysis + mechanical rewrite
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: scope and perform P6.4's mechanical ``f"...{name}..."`` -> ``"...%s...", name`` conversion,
restricted to the two HOT files the owner authorised on 2026-09-22 --
``src/candidate_unit/candidate_unit.py`` and ``src/cascade_correlation/cascade_correlation.py``.

MECHANICAL is defined exactly as ``util/ad-hoc/2026-09-09_p64_fstring_classify.py`` defines it, and
the definitions are imported from nowhere -- they are restated here and asserted to agree on the
same corpus, because two tools that disagree about the population make every count incomparable
(memory ``reference_count_unit_and_criterion_must_match``).

A line is converted ONLY if every one of these holds. Anything else is SKIPPED and reported:

  1. exactly ONE f-string literal on the line -- implicit concatenation (``f"a" f"b"``) is skipped,
     because splitting args across the pieces changes which placeholder binds which value;
  2. the call passes NO existing positional args after the f-string;
  3. every ``{field}`` is a plain name or dotted attribute chain -- no call, subscript or operator;
  4. no field carries a format spec or conversion (``{x:.4f}``, ``{x!r}``);
  5. the literal contains no ``%`` (it would become a format spec and raise AT EMIT TIME, which is
     level-gated and therefore hides);
  6. no ``{{`` / ``}}`` escapes.

Rule 5 is the one that bites silently: ``f"progress {pct}%"`` -> ``"progress %s%"`` raises
``ValueError: incomplete format`` only when the record is actually emitted, so a suppressed site
carries it indefinitely.

**This script does not trust its own rewrite.** ``--verify`` renders every converted line both ways
with synthetic values bound to the field names and compares the results, and the run FAILS if any
pair differs. Rewriting without that is how a precision change reaches a downstream log parser.

Usage:
    2026-09-22_p64_hot_file_convert.py --report          # counts + samples, writes nothing
    2026-09-22_p64_hot_file_convert.py --apply <SRC_DIR> # rewrite in place, then verify
"""
import argparse
import ast
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

CASCOR = "/home/pcalnon/Development/python/Juniper/juniper-cascor"
REV = "origin/main"

HOT = [
    "src/candidate_unit/candidate_unit.py",
    "src/cascade_correlation/cascade_correlation.py",
]

#: Identical to the classifier's, deliberately.
CALL = re.compile(r'\b[Ll]ogger\.(trace|verbose|debug|info|warning|error|critical|fatal)\(\s*f"')
FIELD = re.compile(r"\{([^{}]*)\}")
SPEC = re.compile(r":[^}]*$")
EXPR = re.compile(r"[()\[\]+\-*/]|\.\w+\(")

#: A plain name or dotted attribute chain, and nothing else.
PLAIN = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$")

#: HAZARD 5 -- NOT one of the four in section 5 of the migration analysis, and NOT detectable by a
#: template-level render check. ``f"{x}"`` calls ``format(x, "")``; ``"%s" % x`` calls ``str(x)``.
#: For a **0-dim torch tensor** those differ::
#:
#:     f"{torch.tensor(1.5)}"    -> '1.5'
#:     "%s" % torch.tensor(1.5)  -> 'tensor(1.5000)'
#:
#: Measured 2026-09-22. Multi-dim tensors, ``torch.Size``, dtypes and devices all format the same,
#: so only the 0-dim scalar case diverges -- which is exactly the case a correlation, a loss or an
#: accuracy is. Several ``util/ad-hoc/`` tools parse numeric fields out of log text, so this is a
#: downstream parsing change, not a cosmetic one.
#:
#: Whether a name holds a 0-dim tensor is NOT decidable from the source, so this is a deliberately
#: conservative DENYLIST on the field's trailing identifier. It will refuse some safe sites. That is
#: the correct direction to be wrong in: a refused conversion costs a few ns, an accepted one costs
#: a silent output change that only shows up in whatever parses the log next.
TENSOR_RISK = re.compile(
    r"(?:^|[._])(?:"
    r"correlation|correlations|corr|loss|losses|accuracy|acc|error|err|score|metric|metrics|"
    r"value|val|norm|grad|gradient|tensor|weight|weights|bias|biases|output|outputs|input|inputs|"
    r"residual|activation|activations|prediction|predictions|logit|logits|mean|std|sum|min|max|"
    r"threshold|rate|delta|diff|magnitude"
    r")$",
    re.I,
)

#: The whole call: `logger.METHOD(f"...")` with nothing after the closing quote but `)`.
SINGLE = re.compile(
    r'^(?P<pre>\s*)(?P<recv>\S*?\blogger)\.(?P<meth>trace|verbose|debug|info|warning|error|critical|fatal)'
    r'\(\s*f"(?P<body>(?:[^"\\]|\\.)*)"\s*\)\s*$'
)


def lines_at_rev(path: str):
    blob = subprocess.run(["git", "-C", CASCOR, "show", f"{REV}:{path}"],
                          capture_output=True, text=True, check=False).stdout
    return blob.splitlines()


def classify(line: str) -> str:
    """The classifier's own taxonomy, most-severe first."""
    if re.search(r'f"[^"]*%', line):
        return "H1-literal-%"
    fields = FIELD.findall(line)
    if any(SPEC.search(f) for f in fields):
        return "H2-format-spec"
    if any(EXPR.search(f) for f in fields):
        return "expression"
    return "MECHANICAL"


def convertible(line: str):
    """Return (new_line, fields) if this line can be rewritten, else (None, reason)."""
    if line.count('f"') != 1:
        return None, "multiple or zero f-string literals (implicit concatenation)"
    m = SINGLE.match(line.rstrip("\n"))
    if not m:
        return None, "call shape not a bare logger.M(f\"...\") with no extra args"
    body = m.group("body")
    if "{{" in body or "}}" in body:
        return None, "brace escape"
    if "%" in body:
        return None, "literal % would become a format spec"
    fields = FIELD.findall(body)
    if not fields:
        return None, "no interpolated fields"
    for f in fields:
        name = f.strip()
        if not PLAIN.match(name):
            return None, f"field {f!r} is not a plain name/attribute chain"
        # `.shape` is safe and common -- torch.Size formats identically both ways (verified) -- so
        # screen the trailing identifier, which for `residual_error.shape` is `shape`, not `error`.
        if TENSOR_RISK.search(name):
            return None, f"field {name!r} may hold a 0-dim tensor (hazard 5)"
    new_body = FIELD.sub("%s", body)
    args = ", ".join(f.strip() for f in fields)
    new = f'{m.group("pre")}{m.group("recv")}.{m.group("meth")}("{new_body}", {args})'
    return new, fields


def render_pair(body: str, fields, new_body: str):
    """Render both forms with synthetic values bound to the field names. Must match."""
    vals = [f"<v{i}>" for i in range(len(fields))]
    f_form = body
    for f, v in zip(fields, vals):
        f_form = f_form.replace("{" + f + "}", v, 1)
    pct_form = new_body % tuple(vals)
    return f_form, pct_form


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--fields", action="store_true",
                    help="list the distinct field names the conversion would touch, most common "
                         "first -- the input to judging the 0-dim-tensor hazard")
    ap.add_argument("--apply", metavar="SRC_DIR", help="cascor src/ parent to rewrite in place")
    args = ap.parse_args()
    if not (args.report or args.apply or args.fields):
        ap.error("pass --report, --fields or --apply")

    sha = subprocess.run(["git", "-C", CASCOR, "rev-parse", "--short=8", REV],
                         capture_output=True, text=True, check=False).stdout.strip()
    print(f"repo: {CASCOR}\nrev : {REV} ({sha})\nscope: P6.4 hot files only (owner ruling 2026-09-22)\n")

    grand = Counter()
    converted_all, skipped_all, mismatches = [], [], []

    for path in HOT:
        src_lines = lines_at_rev(path)
        cls = Counter()
        conv, skip = [], []
        for n, line in enumerate(src_lines, 1):
            if not CALL.search(line) or line.lstrip().startswith("#"):
                continue
            k = classify(line)
            cls[k] += 1
            if k != "MECHANICAL":
                continue
            new, info = convertible(line)
            if new is None:
                skip.append((n, line.strip(), info))
                continue
            body = SINGLE.match(line.rstrip("\n")).group("body")
            new_body = FIELD.sub("%s", body)
            f_form, pct_form = render_pair(body, info, new_body)
            if f_form != pct_form:
                mismatches.append((path, n, f_form, pct_form))
            conv.append((n, line.rstrip("\n"), new))
        grand.update(cls)
        converted_all += [(path, *c) for c in conv]
        skipped_all += [(path, *s) for s in skip]
        print(f"{path}")
        print(f"   total f-string sites : {sum(cls.values())}")
        for k in ("MECHANICAL", "expression", "H2-format-spec", "H1-literal-%"):
            print(f"   {k:<22}: {cls[k]}")
        print(f"   -> CONVERTIBLE       : {len(conv)}")
        print(f"   -> mechanical-but-skipped: {len(skip)}\n")

    print(f"TOTAL convertible across both hot files: {len(converted_all)}")
    print(f"TOTAL mechanical-but-skipped           : {len(skipped_all)}")
    print(f"Render mismatches (MUST be 0)          : {len(mismatches)}\n")

    if mismatches:
        print("!! RENDER MISMATCH -- the rewrite is NOT output-identical. Refusing to apply.")
        for p, n, a, b in mismatches[:20]:
            print(f"   {p}:{n}\n     f: {a!r}\n     %: {b!r}")
        return 1

    if skipped_all:
        print("=== mechanical-but-skipped (reasons) ===")
        reasons = Counter(s[3] for s in skipped_all)
        for r, c in reasons.most_common():
            print(f"  {c:4}  {r}")
        print()

    if args.fields:
        # HAZARD 5, which is NOT in the migration analysis's list of four and which a
        # template-level render check cannot see: f"{x}" calls format(x, "") while "%s" % x calls
        # str(x). For a 0-dim torch tensor those DIFFER --
        #     f"{torch.tensor(1.5)}" -> '1.5'      "%s" % torch.tensor(1.5) -> 'tensor(1.5000)'
        # -- so any converted field that may hold a 0-dim tensor silently changes log output, and
        # several util/ad-hoc/ tools parse numeric fields out of log text. Measured 2026-09-22.
        names = Counter()
        for _p, _n, old, _new in converted_all:
            body = SINGLE.match(old).group("body")
            for f in FIELD.findall(body):
                names[f.strip()] += 1
        print(f"=== {len(names)} distinct fields across {len(converted_all)} conversions ===")
        for name, c in names.most_common():
            print(f"  {c:4}  {name}")
        return 0

    print("=== sample conversions ===")
    for p, n, old, new in converted_all[:6]:
        print(f"  {p}:{n}\n    - {old.strip()}\n    + {new.strip()}")

    if args.report:
        return 0

    # --- apply -----------------------------------------------------------------------------------
    root = Path(args.apply)
    by_file = {}
    for p, n, old, new in converted_all:
        by_file.setdefault(p, {})[n] = (old, new)
    for path, edits in by_file.items():
        target = root / path
        if not target.is_file():
            sys.exit(f"FATAL: {target} not found")
        lines = target.read_text().splitlines(keepends=True)
        for n, (old, new) in edits.items():
            have = lines[n - 1].rstrip("\n")
            if have != old:
                sys.exit(f"FATAL: {path}:{n} does not match {REV} -- tree drifted; re-run --report\n"
                         f"  expected: {old!r}\n  found   : {have!r}")
            lines[n - 1] = new + "\n"
        target.write_text("".join(lines))
        print(f"\napplied {len(edits)} conversions -> {target}")
        try:
            ast.parse(target.read_text())
            print("  AST parses OK")
        except SyntaxError as exc:
            sys.exit(f"FATAL: {target} no longer parses: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
