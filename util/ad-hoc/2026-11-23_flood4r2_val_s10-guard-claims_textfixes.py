#!/usr/bin/env python3
"""
Build and validate the claims lens's exact old -> new text fixes for the agent guard 1.4.0 carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- read-only validation (claims lens on the agent guard 1.4.0 texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py; CHANGELOG.md; docs/REFERENCE.md; tests/test_claude_agent_guard.py

Usage:
    python3 -I 2026-11-23_flood4r2_val_s10-guard-claims_textfixes.py <texts dir> <staged dir> <out text_fixes.json>
        [<checked copies dir>]

Each fix names a file: one of the carrier's texts (<texts dir>/pr_body.txt, commit_body.txt, changelog_entry.txt,
stamps.json) or a staged file (<staged dir>/<repo path>). The fixes are applied IN ORDER to in-memory copies, and
each ``old`` must occur exactly once in its file at its turn; the result is written to text_fixes.json with the
check. With <checked copies dir>, the fixed copies are written there (never over the inputs) so they can be judged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OPEN_MD = (
    "a substitution, or a parameter with no `:-` default, that makes up a whole path component or follows a lone dot,"
    " anywhere but the first component under a home or inside `~/.claude` (`cp hook .git/$(printf %s hoo ks)/post-commit`,"
    " `cp x ~/.config/$d/config`, `cat /x/$(printf %s .s sh)/config`, `cat /x/.$d/config`)"
)
SCOPE = "wherever its path component also holds a literal character other than a leading dot"

FIXES = [
    # F1 (+F3, F6): scope the path-reading claim; name the whole-component class, the quoted operator; variables
    ("F1", "pr_body.txt",
     "- **Path readings.** Each substitution or parameter is one part that may hold any text or none, for the credential\n  directories,",
     "- **Path readings.** Each substitution or parameter is one part that may hold any text or none " + SCOPE + ", for the\n  credential directories,"),
    ("F1", "pr_body.txt",
     "  `gh api repos/o/r --$(printf %s i)nput f`. Only the path rules read a computed part as any text.\n- A glob with no literal character as a whole signing-path component: `cat ~/.config/*/config`.",
     "  `gh api repos/o/r --$(printf %s i)nput f`, and the same through a quoted backtick body\n  (``sud\"`echo \"{o,Q}\"`\" id``). Only the path rules read a computed part as any text.\n"
     "- A parameter expansion whose operator is quoted: `s\"${x$':'-\"{u,Q}\"}\" id`.\n"
     "- A glob with no literal character as a whole signing-path component: `cat ~/.config/*/config`.\n"
     "- A substitution, or a parameter with no `:-` default, that makes up a whole path component or follows a lone dot,\n"
     "  anywhere but the first component under a home or inside `~/.claude`: `cp hook .git/$(printf %s hoo ks)/post-commit`,\n"
     "  `cp x ~/.config/$d/config`, `cat /x/$(printf %s .s sh)/config`, `cat /x/.$d/config`."),
    ("F6", "pr_body.txt",
     "- A variable that holds `..`, `/` or part of a name, even in the same command (gap 2): `d=~/.ss; cat ${d}h/config`.",
     "- A variable that holds `..` or `/`, even in the same command (gap 2): `d=~/.ss; cat ${d}h/config`."),
    ("F1", "commit_body.txt",
     "rules read a substitution or parameter as one part that may hold any text or\nnone, for the credential directories",
     "rules read a substitution or parameter as one part that may hold any text or\nnone wherever its path component also holds a literal character other than a\nleading dot, for the credential directories"),
    ("F1", "commit_body.txt",
     "literal character as a whole signing-path component, aliases and functions from\nthe shell's profile, a variable holding .. or part of a name, programs that hand",
     "literal character as a whole signing-path component, a parameter expansion whose\noperator is quoted, a substitution or parameter that makes up a whole path\n"
     "component or follows a lone dot anywhere but the first component under a home\nor inside ~/.claude (cp hook .git/$(printf %s hoo ks)/post-commit), aliases and\n"
     "functions from the shell's profile, a variable holding .. or /, programs that hand"),
    ("F1", "changelog_entry.txt",
     "`.ss$(printf h)`), at any position, for the credential directories",
     "`.ss$(printf h)`), " + SCOPE + ", for the credential directories"),
    ("F1", "changelog_entry.txt",
     "    (`d$(printf %s o)as id`, `gh api repos/o/r --$(printf %s i)nput f`); a glob with no literal character as a\n"
     "    whole signing-path component (`cat ~/.config/*/config`); aliases and functions from the shell's profile; a\n"
     "    variable that holds `..`, `/` or part of a name, even in the same command (gap 2: `d=~/.ss; cat ${d}h/config`);",
     "    (`d$(printf %s o)as id`, `gh api repos/o/r --$(printf %s i)nput f`); a parameter expansion whose operator is\n"
     "    quoted (`s\"${x$':'-\"{u,Q}\"}\" id`); a glob with no literal character as a whole signing-path component\n"
     "    (`cat ~/.config/*/config`); " + OPEN_MD + "; aliases and functions from the shell's profile; a variable that\n"
     "    holds `..` or `/`, even in the same command (gap 2: `d=~/.ss; cat ${d}h/config`);"),
    ("F1", "CHANGELOG.md",
     "`.ss$(printf h)`), at any position, for the credential directories",
     "`.ss$(printf h)`), " + SCOPE + ", for the credential directories"),
    ("F1", "CHANGELOG.md",
     "    (`d$(printf %s o)as id`, `gh api repos/o/r --$(printf %s i)nput f`); a glob with no literal character as a\n"
     "    whole signing-path component (`cat ~/.config/*/config`); aliases and functions from the shell's profile; a\n"
     "    variable that holds `..`, `/` or part of a name, even in the same command (gap 2: `d=~/.ss; cat ${d}h/config`);",
     "    (`d$(printf %s o)as id`, `gh api repos/o/r --$(printf %s i)nput f`); a parameter expansion whose operator is\n"
     "    quoted (`s\"${x$':'-\"{u,Q}\"}\" id`); a glob with no literal character as a whole signing-path component\n"
     "    (`cat ~/.config/*/config`); " + OPEN_MD + "; aliases and functions from the shell's profile; a variable that\n"
     "    holds `..` or `/`, even in the same command (gap 2: `d=~/.ss; cat ${d}h/config`);"),
    ("F1", "docs/REFERENCE.md",
     "(`.ss$(:)h` can be `.ssh`, at any position), for the credential directories",
     "(`.ss$(:)h` can be `.ssh`) " + SCOPE + ", for the credential directories"),
    ("F1", "docs/REFERENCE.md",
     "`gh api repos/o/r --$(printf %s i)nput f`); a glob with no literal character as a whole signing-path component (`cat ~/.config/*/config`); aliases and functions from the shell's profile (a command word bash replaces); a variable that holds `..`, `/` or part of a name, even in the same command",
     "`gh api repos/o/r --$(printf %s i)nput f`); a parameter expansion whose operator is quoted (`s\"${x$':'-\"{u,Q}\"}\" id`); a glob with no literal character as a whole signing-path component (`cat ~/.config/*/config`); " + OPEN_MD + "; aliases and functions from the shell's profile (a command word bash replaces); a variable that holds `..` or `/`, even in the same command"),
    ("F1", "util/claude_agent_guard.py",
     "any text or none (``.ss$(:)h`` can be ``.ssh``), for the credential directories, Claude's settings, the MCP files\nand the signing paths alike,",
     "any text or none (``.ss$(:)h`` can be ``.ssh``) wherever its path component also holds a literal character\nother than a leading dot, for the credential directories, Claude's settings, the MCP files and the signing paths\nalike,"),
    ("F1", "util/claude_agent_guard.py",
     "    ``gh api repos/o/r --$(printf %s i)nput f``); a glob with no literal character as a whole signing-path\n"
     "    component (``cat ~/.config/*/config``); aliases and functions from the shell's profile (a command word bash\n"
     "    replaces);\n"
     "    a variable that holds ``..``, ``/`` or a whole name (gap 2); and",
     "    ``gh api repos/o/r --$(printf %s i)nput f``); a parameter expansion whose operator is quoted\n"
     "    (``s\"${x$':'-\"{u,Q}\"}\" id``); a glob with no literal character as a whole signing-path component\n"
     "    (``cat ~/.config/*/config``); a substitution, or a parameter with no ``:-`` default, that makes up a whole\n"
     "    path component or follows a lone dot, anywhere but the first component under a home or inside ``~/.claude``\n"
     "    (``cp hook .git/$(printf %s hoo ks)/post-commit``, ``cp x ~/.config/$d/config``,\n"
     "    ``cat /x/$(printf %s .s sh)/config``, ``cat /x/.$d/config``); aliases and functions from the shell's profile\n"
     "    (a command word bash replaces); a variable that holds ``..`` or ``/`` (gap 2); and"),
    ("F6", "util/claude_agent_guard.py",
     "   that holds part of a name (``d=~/.ss; cat ${d}h/config``), a script written by one call",
     "   that holds a directory and part of a name (``d=~/.ss; cat ${d}h/config``), a script written by one call"),
    # F2: the count of shapes 1.3.0 runs past 60 s on (round2/timing_jl1_main.txt: seven TIMEOUT rows)
    ("F2", "pr_body.txt", "(1.3.0 runs past 60 s on eight of them:", "(1.3.0 runs past 60 s on seven of them:"),
    ("F2", "changelog_entry.txt", "60 s on eight of them)", "60 s on seven of them)"),
    ("F2", "CHANGELOG.md", "60 s on eight of them)", "60 s on seven of them)"),
    # F4 (+F8): a list inside a quoted backtick body is closed in a PATH word only
    ("F4", "pr_body.txt",
     "- the lists bash expands inside a quoted backtick body (`.ss\"`echo \"{h,x}\"`\"`) or a quoted `${x:-\"{h,y}\"}` default;",
     "- in a path word, the lists bash expands inside a quoted backtick body (``cat ~/X/../.ss\"`echo \"{h,x}\"`\"/config``)\n  or a quoted `${x:-\"{h,y}\"}` default;"),
    ("F4", "commit_body.txt",
     "a list, brace lists in option words, the lists bash expands inside a quoted\nbacktick body",
     "a list, brace lists in option words, in a path word the lists bash expands\ninside a quoted backtick body"),
    ("F4", "changelog_entry.txt",
     "    the lists bash expands inside a quoted backtick body or `${x:-\"...\"}`;",
     "    in a path word, the lists bash expands inside a quoted backtick body or `${x:-\"...\"}`;"),
    ("F4", "CHANGELOG.md",
     "    the lists bash expands inside a quoted backtick body or `${x:-\"...\"}`;",
     "    in a path word, the lists bash expands inside a quoted backtick body or `${x:-\"...\"}`;"),
    ("F4", "docs/REFERENCE.md",
     "; a list bash expands inside a quoted backtick body or a quoted `${x:-\"...\"}` default;",
     "; in a path word, a list bash expands inside a quoted backtick body or a quoted `${x:-\"...\"}` default;"),
    ("F4", "util/claude_agent_guard.py",
     "``git commit --{gpg-sign,x}``); the\n    lists bash expands inside a quoted backtick body",
     "``git commit --{gpg-sign,x}``); in a\n    path word, the lists bash expands inside a quoted backtick body"),
    # F5: the commit body names a docs/REFERENCE.md version that main already holds (0.6.78, 2026-11-23)
    ("F5", "commit_body.txt",
     "docs/REFERENCE.md 0.6.78 and CHANGELOG.md describe the change.",
     "docs/REFERENCE.md and CHANGELOG.md describe the change."),
    # F7: arc-internal wording in the PR body
    ("F7", "pr_body.txt", "while passing the round-1 1.4.0 are down to 218", "while passing this change's first draft are down to 218"),
    # F8: REFERENCE cites an unreleased draft's timing as "before the bound"
    ("F8", "docs/REFERENCE.md",
     "(nested `$( )` with `cd` at every level, which took 25 s to over 60 s before the bound, is refused in 0.1 s)",
     "(nested `$( )` with `cd` at every level is refused in 0.1 s)"),
    # F9: gap 12's opening reads as "every spelling known to pass 1.3.0"
    ("F9", "util/claude_agent_guard.py", "which denies the spellings known to pass 1.3.0:", "which denies these spellings, each known to pass 1.3.0:"),
    # F10: three named closed variants with no pinned row (each passes 1.3.0 and is denied by 1.4.0)
    ("F10", "tests/test_claude_agent_guard.py",
     r"""    ("cat ~/.ss{h,$'\\x7d'c}/config", CRED_BASH),  # $'\x7d' is a quoted } to bash's brace scan""",
     r"""    ("cat ~/.ss{h,$'\\x7d'c}/config", CRED_BASH),  # $'\x7d' is a quoted } to bash's brace scan
    ("cat ~/X/../.ss{h,$'\\x7d'c}/config", CRED_BASH),  # and behind a hop"""),
    ("F10", "tests/test_claude_agent_guard.py",
     r"""    ("shopt -s dotglob\ncat ~/*/config", CRED_BASH),""",
     r"""    ("shopt -s dotglob\ncat ~/*/config", CRED_BASH),
    ("GLOBIGNORE=x\ncat ~/*/config", CRED_BASH),"""),
    ("F10", "tests/test_claude_agent_guard.py",
     r"""    ("{pke${x:-x}ec,Q} id", PRIV),""",
     r"""    ("{pke${x:-x}ec,Q} id", PRIV),
    ("pke${x:-x}ec id", PRIV),"""),
    # F11: stamps.json describes a REFERENCE timing phrase the staged text no longer has
    ("F11", "stamps.json",
     "the guard bullet's timing sentence ('at most 3.2 s as the hook', '25 s to over 60 s')",
     "the guard bullet's timing sentence ('under 4 s as the hook', 'refused in 0.1 s', '(16 relative `cd`s)')"),
]
TEXTS = {"pr_body.txt", "commit_body.txt", "changelog_entry.txt", "stamps.json"}


def main(argv: list) -> int:
    texts, staged, out = Path(argv[1]), Path(argv[2]), Path(argv[3])
    checked = Path(argv[4]) if len(argv) > 4 else None
    contents = {}
    rows = []
    ok = True
    for finding, name, old, new in FIXES:
        path = (texts / name) if name in TEXTS else (staged / name)
        if name not in contents:
            contents[name] = path.read_text(encoding="utf-8")
        count = contents[name].count(old)
        good = count == 1
        ok = ok and good
        if good:
            contents[name] = contents[name].replace(old, new, 1)
        rows.append({"finding": finding, "file": name if name not in TEXTS else str(texts / name), "old": old, "new": new, "occurrences_at_its_turn": count})
        print("%-4s %-34s occurs %d %s" % (finding, name, count, "ok" if good else "FAIL"))
    if checked:
        for name, text in contents.items():
            target = checked / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
    out.write_text(json.dumps({"apply": "in order; each old occurs exactly once in its file at its turn (checked)", "staged_files_are": "the carrier's staged blobs (repo paths), as extracted to the session-10 staged copies", "all_valid": ok, "fixes": rows}, indent=1) + "\n", encoding="utf-8")
    print("all valid:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
