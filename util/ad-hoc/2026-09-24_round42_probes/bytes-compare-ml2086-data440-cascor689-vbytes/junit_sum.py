"""Summarise one or more junit XML files: passed / failed / errors / skipped, plus failing node ids."""
import sys
import xml.etree.ElementTree as ET

for path in sys.argv[1:]:
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    failing = []
    for case in ET.parse(path).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None:
            counts["failed"] += 1
            failing.append(node)
        elif case.find("error") is not None:
            counts["error"] += 1
            failing.append(node)
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    total = sum(counts.values())
    print(f"{path.rsplit('/', 1)[-1]}: {counts['passed']} passed, {counts['failed']} failed, {counts['error']} errors, {counts['skipped']} skipped ({total} total)")
    for node in failing[:40]:
        print(f"    FAIL {node}")
    if len(failing) > 40:
        print(f"    ... {len(failing) - 40} more")
