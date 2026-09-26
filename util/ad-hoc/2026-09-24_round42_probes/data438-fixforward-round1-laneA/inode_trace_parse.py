#!/usr/bin/env python3
"""Parse an strace -f log from inode_trace.py: list inode-allocating syscalls between the markers."""

import re
import sys

lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
inside = False
creating = []
unlinks = []
opens = 0
for line in lines:
    if "LANE_A_MARKER_BEGIN" in line:
        inside = True
        continue
    if "LANE_A_MARKER_END" in line:
        inside = False
        continue
    if not inside:
        continue
    if re.search(r"\b(open|openat|openat2)\(", line):
        opens += 1
        if "O_CREAT" in line:
            creating.append(line)
    if re.search(r"\b(creat|mkdir|mkdirat|mknod|mknodat|link|linkat|symlink|symlinkat)\(", line):
        creating.append(line)
    if re.search(r"\b(unlink|unlinkat)\(", line):
        unlinks.append(line)
print(f"open-family calls between markers: {opens}")
print(f"inode-allocating calls between markers: {len(creating)}")
for line in creating:
    print("  CREATE:", line[:220])
print(f"unlink calls between markers: {len(unlinks)}")
for line in unlinks:
    print("  UNLINK:", line[:220])
lock_opens = [line for line in lines if (".lock" in line and re.search(r"\bopenat\(", line))]
print("lock-file opens (whole run, last 6), path tail and flags:")
for line in lock_opens[-6:]:
    m = re.search(r'openat\(AT_FDCWD, "([^"]*)", ([^)]*)\) = (.*)$', line)
    if m:
        print(f"   .../{'/'.join(m.group(1).split('/')[-2:])}  {m.group(2)}  = {m.group(3)}")
