#!/usr/bin/env python3
"""
Resolve the ml-code round-3 three-way conflicts in AGENTS.md, CHANGELOG.md and docs/REFERENCE.md, and set the stamps.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3 rebuild)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_rebuild.py (writes the merges this resolves); validator findings
         ml-code-port-lens F6 and ml-code-claims-lens F1 / F10 (the stamp collision; keep both CHANGELOG entries).

Usage (from the round-3 worktree root, right after the rebuild script):
    python3 util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_resolve.py <new REFERENCE version> <YYYY-MM-DD>

Each ``git merge-file`` conflict block (ours = the carrier, theirs = main) is replaced:
- AGENTS.md ``**Last Updated**:`` -> the date given (today's UTC date; the agents-md-touch-up check wants a bump);
- docs/REFERENCE.md ``**Version:**`` (header and footer) -> the new version, once each; both ``**Last Updated:**``
  lines -> the date; Version History -> main's rows unchanged, then the carrier's row with the new version and date
  (so it sits right after the highest-version row);
- CHANGELOG.md -> the carrier's entry, a blank line, then main's entry. The carrier's entry then sits between two
  of main's entries, so an entry that a later PR adds at the end of the subsection merges without a conflict.
Any other conflict shape aborts with exit 1 and nothing is written. Prints what it replaced.
"""
import re
import sys
from pathlib import Path

_BLOCK = re.compile(r"^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n", re.MULTILINE | re.DOTALL)
_ROW = re.compile(r"^\| (\d+\.\d+\.\d+) +\| (\d{4}-\d{2}-\d{2}) \|")
_MARKER = re.compile(r"^(<<<<<<<|=======|>>>>>>>)( |$)", re.MULTILINE)


def resolve_agents(text: str, date: str) -> tuple:
    log = []

    def replace(match: re.Match) -> str:
        ours, theirs = match.group(1), match.group(2)
        if not (ours.startswith("**Last Updated**: ") and theirs.startswith("**Last Updated**: ") and ours.count("\n") == 1 == theirs.count("\n")):
            raise SystemExit("unexpected AGENTS.md conflict:\n%s=======\n%s" % (ours[:300], theirs[:300]))
        log.append("AGENTS.md Last Updated: carrier %s / main %s -> %s" % (ours.split()[-1], theirs.split()[-1], date))
        return "**Last Updated**: %s\n" % date

    return _BLOCK.sub(replace, text), log


def resolve_reference(text: str, version: str, date: str) -> tuple:
    log = []

    def replace(match: re.Match) -> str:
        ours, theirs = match.group(1), match.group(2)
        if ours.startswith("**Version:** ") and theirs.startswith("**Version:** ") and ours.count("\n") == 1 == theirs.count("\n"):
            log.append("REFERENCE Version line: carrier %s / main %s -> %s" % (ours.split()[-1], theirs.split()[-1], version))
            return "**Version:** %s\n" % version
        their_rows = theirs.splitlines()
        if ours.count("\n") == 1 and _ROW.match(ours) and all(_ROW.match(line) for line in their_rows):
            highest = max(tuple(int(p) for p in _ROW.match(line).group(1).split(".")) for line in their_rows)
            last = tuple(int(p) for p in _ROW.match(their_rows[-1]).group(1).split("."))
            if last != highest or tuple(int(p) for p in version.split(".")) <= highest:
                raise SystemExit("main's last conflicting row is not its highest, or %s is not above it" % version)
            row = _ROW.sub("| %-7s | %s |" % (version, date), ours, count=1)
            log.append("REFERENCE Version History: main's %d row(s) kept (highest %s), then the carrier's row as %s / %s" % (len(their_rows), ".".join(map(str, highest)), version, date))
            return theirs + row
        raise SystemExit("unexpected REFERENCE conflict:\n%s=======\n%s" % (ours[:300], theirs[:300]))

    resolved = _BLOCK.sub(replace, text)
    resolved, count = re.subn(r"^\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}$", "**Last Updated:** %s" % date, resolved, flags=re.MULTILINE)
    if count != 2:
        raise SystemExit("expected 2 '**Last Updated:**' lines in docs/REFERENCE.md, found %d" % count)
    log.append("REFERENCE Last Updated (header and footer) -> %s" % date)
    return resolved, log


def resolve_changelog(text: str) -> tuple:
    log = []

    def replace(match: re.Match) -> str:
        ours, theirs = match.group(1), match.group(2)
        if not (ours.startswith("- **") and theirs.startswith("- **")):
            raise SystemExit("unexpected CHANGELOG conflict")
        log.append("CHANGELOG: the carrier's entry (%d lines), then main's (%d lines)" % (ours.count("\n"), theirs.count("\n")))
        return ours.rstrip("\n") + "\n\n" + theirs

    return _BLOCK.sub(replace, text), log


def main() -> int:
    version, date = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print("usage: <new REFERENCE version N.N.N> <YYYY-MM-DD>")
        return 1
    agents, reference, changelog = Path("AGENTS.md"), Path("docs/REFERENCE.md"), Path("CHANGELOG.md")
    new_agents, log_a = resolve_agents(agents.read_bytes().decode("utf-8"), date)
    new_reference, log_r = resolve_reference(reference.read_bytes().decode("utf-8"), version, date)
    new_changelog, log_c = resolve_changelog(changelog.read_bytes().decode("utf-8"))
    results = ((agents, new_agents, 1), (reference, new_reference, 3), (changelog, new_changelog, 1))
    for path, text, _ in results:
        if _MARKER.search(text):
            print("conflict markers remain in %s; nothing written" % path)
            return 1
    for log, (path, _, expected) in zip((log_a, log_r, log_c), results):
        resolved = len(log) - (1 if path == reference else 0)
        if resolved != expected:
            print("%s: resolved %d conflict(s), expected %d; nothing written" % (path, resolved, expected))
            return 1
    for path, text, _ in results:
        path.write_bytes(text.encode("utf-8"))  # bytes in, bytes out: no newline translation
    for line in log_a + log_r + log_c:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
