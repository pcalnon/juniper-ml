#!/usr/bin/env python3
"""
Reconcile the stray S-7 `.env` before it is removed -- prints names and True/False only, never a value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc -- one-off (backup arc, Phase C step 3a)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md note S-7a;
         notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md §6.3 step 3;
         notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md (the recorded
         sha256[:16] values -- the hand-reconciliation scheme, NOT the PBKDF2 pair)

Note S-7a says: reconcile the file's two values against the record FIRST, then remove the file (the file only;
its worktree is DO NOT SWEEP). Two independent questions are asked, because either alone can mislead:

  1. Does each value match the fingerprint recorded on 2026-08-25/26? Scheme as recorded: sha256 of the value,
     first 16 hex. The value is tried as written and with one pair of matching outer quotes stripped; the
     scheme that matched is named. Matching under some scheme is the evidence; failing under all is not proof
     of a different value, only of an unrecorded scheme.
  2. Does each value equal the same name in the live credential file? That file was rewritten on 2026-09-18
     20:45 CDT -- after the fingerprints were recorded -- so equality with it is no longer evidence for (1),
     and (1) is no longer evidence for it.

Verdict per name: SAFE TO REMOVE when (1) matched or (2) is True -- the value is then held elsewhere. Exit 0
only when every name found is SAFE and at least one name was found; exit 1 otherwise; exit 2 on a usage or
read error. Nothing is printed but names, booleans, scheme labels and counts.

Usage:
    python3 util/ad-hoc/2026-10-10_s7_env_reconcile.py \\
        [S7_FILE (default: juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env)] \\
        [LIVE_FILE (default: ~/.config/duplicati-backup/env)]
"""

import hashlib
import hmac
import os
import re
import sys

DEFAULT_S7 = os.path.expanduser("~/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env")
DEFAULT_LIVE = os.path.expanduser("~/.config/duplicati-backup/env")

# Recorded 2026-08-25 (certification note, the line that names the hand-reconciliation scheme).
RECORDED = (("PASSPHRASE", "6d8b263f6d064556"), ("PASSPHRASE_OLD", "b085454a8c34bd8c"))
NAMES = tuple(label for label, _ in RECORDED)
ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=(.*)$")


def read_assignments(path):
    """Map each wanted name to the list of its active (uncommented) values, in file order."""
    found = {label: [] for label in NAMES}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            match = ASSIGNMENT.match(line)
            if match and match.group(1) in found:
                found[match.group(1)].append(match.group(2))
    return found


def unquote(text):
    text = text.strip()
    if len(text) >= 2 and text[0] in "'\"" and text[-1] == text[0]:
        return text[1:-1]
    return text


def fingerprint_scheme(value, recorded):
    """Return the label of the first scheme whose sha256[:16] equals the recorded prefix, or None."""
    for label, candidate in (("as-written", value), ("quotes-stripped", unquote(value))):
        digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:16]
        if hmac.compare_digest(digest, recorded):
            return label
    return None


def main(argv):
    s7_path = argv[1] if len(argv) > 1 else DEFAULT_S7
    live_path = argv[2] if len(argv) > 2 else DEFAULT_LIVE
    try:
        s7 = read_assignments(s7_path)
        live = read_assignments(live_path)
    except OSError as exc:
        print(f"ERROR: cannot read an input file: {exc.__class__.__name__}", file=sys.stderr)
        return 2

    present = 0
    all_safe = True
    for label, recorded in RECORDED:
        values = s7[label]
        if not values:
            print(f"{label}: not present in the S-7 file")
            continue
        present += 1
        if len(values) > 1:
            print(f"{label}: {len(values)} active assignments in the S-7 file -- AMBIGUOUS, reconcile by hand")
            all_safe = False
            continue
        scheme = fingerprint_scheme(values[0], recorded)
        live_values = live[label]
        equal_live = len(live_values) == 1 and hmac.compare_digest(unquote(values[0]).encode("utf-8"), unquote(live_values[0]).encode("utf-8"))
        safe = scheme is not None or equal_live
        all_safe = all_safe and safe
        print(f"{label}: fingerprint match={scheme is not None}" + (f" (scheme={scheme})" if scheme else "") + f" | equals live credential file={equal_live} (live assignments: {len(live_values)}) -> {'SAFE TO REMOVE' if safe else 'KEEP -- value held nowhere recorded'}")

    if present == 0:
        print("no PASSPHRASE / PASSPHRASE_OLD assignment found -- nothing reconciled; do not remove on this result")
        return 1
    print("VERDICT: " + ("remove the file (the file only)" if all_safe else "do NOT remove the file"))
    return 0 if all_safe else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
