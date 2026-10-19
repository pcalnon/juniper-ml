"""
Inventory what dropping MacPorts' /opt/local/{bin,sbin} from PATH would change on turing (bring-up task D5).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — investigation (the evidence behind the owner's D5 ruling, 2026-10-19)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D5, §17);
         reports/2026-10-19_turing-d5-path-inventory/

Why: plan task D5 said to drop /opt/local/bin from the shell profile, because MacPorts is dead on turing (it was built
for darwin 18, and every `port` command errors). The plan treated that as a no-op cleanup, but MacPorts' 2019
binaries still run. Read-only, this script takes each command in /opt/local/{bin,sbin} and reports where it
resolves on PATH now and where it would resolve with both entries removed. The 2026-10-19 run found:
- 104 commands that would switch to a Homebrew or system copy;
- 128 that exist only in /opt/local, among them the owner's gpg2, gnupg and gnupg2 links into the Homebrew Cellar,
  which Homebrew itself does not link into /usr/local/bin.
The owner therefore ruled to demote the two entries to the end of PATH, not remove them.

Usage:
    python3 -I util/ad-hoc/2026-10-19_turing_d5_path_inventory.py [--path PATH_STRING]

--path evaluates the given PATH string instead of this process's PATH. Exit 0 always: it reports, never gates.
"""

import argparse
import os
import sys

DROP = ("/opt/local/bin", "/opt/local/sbin")


def first(name, dirs):
    for d in dirs:
        f = os.path.join(os.path.expanduser(d), name)
        if os.path.isfile(f) and os.access(f, os.X_OK):
            return f
    return None


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--path", default=os.environ.get("PATH", ""))
    args = ap.parse_args(argv)
    cur = [p for p in args.path.split(":") if p]
    new = [p for p in cur if p not in DROP]

    lost, changed, same = [], [], 0
    for d in DROP:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if name.startswith("."):
                continue  # MacPorts' .turd_MacPorts placeholder is not a command
            a, b = first(name, cur), first(name, new)
            if a is None or not a.startswith("/opt/local/"):
                same += 1  # an earlier PATH entry already wins, so nothing changes
            elif b is None:
                lost.append(name)
            else:
                changed.append((name, a, b))

    print("PATH evaluated: " + ":".join(cur))
    print(f"unchanged (an earlier entry wins): {same}")
    print(f"would resolve elsewhere: {len(changed)}")
    for name, a, b in changed:
        print(f"  {name:28s} {os.path.realpath(a)}  ->  {b}")
    print(f"only in /opt/local (lost from PATH): {len(lost)}")
    print("  " + " ".join(lost))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
