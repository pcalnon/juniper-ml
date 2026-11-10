#!/usr/bin/env python3
"""
Print tests, failures, errors and skipped for every JUnit XML report under a directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-29
Status: ad-hoc — investigation (flood-3 record, ninth update)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4, cascor's forced exit)

Why this exists
---------------
juniper-cascor's conftest ended a session with ``os._exit(0)`` whenever a non-daemon thread survived, so a
lane's exit status could not prove it had no failures (fixed by juniper-cascor#736). The JUnit report is
written before that exit, so it records the truth. This tallied ``main``'s reports to show nothing was
masked at the time:

    gh api repos/pcalnon/juniper-cascor/actions/runs/<run id>/artifacts --jq '.artifacts[] | [.id, .name] | @tsv'
    gh api repos/pcalnon/juniper-cascor/actions/artifacts/<artifact id>/zip > <dir>/<artifact id>.zip   # one per test artifact, then unzip each into its own folder
    python3 -I util/ad-hoc/2026-10-29_junit_totals.py <dir>

Download by artifact ID, not by name: two legs share the name ``unit-test-results-py3.12`` (the ubuntu and
macOS 3.12 legs), and ``gh run download -p <pattern>`` keeps only one of them, which yields five reports.
Run of record (cascor run 40768508350, ``e8e8bf4d``): six reports, four unit reports of 5,868 tests and two
integration reports of 172, every one with 0 failures and 0 errors. Exit 0 always; it reports.
"""

import sys
import xml.etree.ElementTree as ET  # nosec B405 - our own CI artifacts
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    for path in sorted(root.rglob("*.xml")):
        top = ET.parse(path).getroot()  # nosec B314 - our own CI artifacts
        suites = [top] if top.tag == "testsuite" else list(top.iter("testsuite"))
        tests = failures = errors = skipped = 0
        for suite in suites:
            tests += int(suite.get("tests", 0))
            failures += int(suite.get("failures", 0))
            errors += int(suite.get("errors", 0))
            skipped += int(suite.get("skipped", 0))
        print(f"{path.relative_to(root)}\ttests={tests}\tfailures={failures}\terrors={errors}\tskipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
