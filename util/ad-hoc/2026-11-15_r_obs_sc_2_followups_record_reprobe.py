#!/usr/bin/env python3
"""
Re-probe, from GitHub, PyPI, GHCR and the host, every fact plan v1.15.16 records about R-OBS-SC-2's follow-ups.

Project: juniper-ml
Sub-Project: ad-hoc tooling (consolidated plan record)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- single-use verifier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md v1.15.16;
         util/ad-hoc/2026-11-15_consolidated_plan_v1_15_16_r_obs_sc_2_followups.py (the writer);
         util/ad-hoc/2026-11-09_r_obs_sc_2_record_reprobe.py (the pattern; RETAINED, it records the pre-fix state);
         util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py (the rulings, from the transcripts);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md,
         HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md,
         HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md and
         HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md
         (the handoffs whose facts this checks)

Why
---
R-OBS-SC-2's follow-ups ran across six sessions (a4e1e914, 6e3bdef0, 218ff61e, 7d425759, 1b4fec84 and b9dfa450)
from 2026-11-09 to 2026-11-15, and plan v1.15.16 records them from their handoffs. A handoff is a session's summary,
not the source, so each fact the plan states is checked here against the record it names:

- the PRs' states, merge commits, merge (or close) times and files, juniper-deploy#278 among them;
- the three Releases' tags, target commits and ``published_at``;
- the three publish runs' jobs, approvals and ``pending_deployments``, the two image runs, and GHCR's tag lists; once a
  gate is open, PyPI's files against TestPyPI's (by sha256 for canopy, member by member for cascor);
- PyPI's and TestPyPI's files for juniper-ml 0.11.5, and TestPyPI's for juniper-cascor 0.14.0 and juniper-canopy 0.10.0;
- the floors in each consumer's ``pyproject.toml``, and juniper-deploy's image pins and helm tags on ``main`` against
  GHCR's highest tags;
- the register's ``APD-ECO-016`` row on ``main`` and the Docs Full Check run dispatched after juniper-ml#2576;
- the source lines each finding cites, on each repository's ``main``;
- the owner's answers and directive, from the session transcripts, each dated by the first timestamped entry that
  carries it;
- the trio's environments, and the parent ``Juniper/AGENTS.md`` and its copies (read in place, read-only).

Each check has an expected value and prints PASS or FAIL beside what it read.

State that moves
----------------
The two ``pypi`` gates (juniper-cascor run 43663237489 and juniper-canopy run 43664277663) moved when the owner
approved them, and so their checks accept either state, WAITING or PUBLISHED. juniper-deploy#278 pinned cascor and
canopy afterwards, so those pins are checked as fixed; its recurrence pin (``docker-compose.yml:598``) moves only if a
later PR moves it, and its check accepts BEHIND or CURRENT against GHCR's highest tag. A check FAILs only on a state that
is neither (a failed job, a gate that is open while PyPI does not serve the version, a half-moved pin). The plan states
what was read, and when.

Usage
-----
    python3 util/ad-hoc/2026-11-15_r_obs_sc_2_followups_record_reprobe.py

Exit 0 when every check passes, 1 otherwise. It needs ``gh`` (authenticated) and network access; it writes nothing.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OWNER = "pcalnon"
_REPO = Path(__file__).resolve().parents[2]
FAILS: list[str] = []
NOTES: list[str] = []

#: (repo, number) -> (state, merge-commit prefix or None, mergedAt (or closedAt) or None, files expected or None)
PRS = {
    ("juniper-ml", 2532): ("MERGED", "a03680c8", "2026-11-09T11:49:49Z", None),
    ("juniper-ml", 2546): ("MERGED", "348777f4", "2026-11-12T01:36:13Z", {"prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md"}),
    ("juniper-ml", 2555): ("MERGED", "26ea0ecb", "2026-11-13T00:49:00Z", None),
    ("juniper-ml", 2556): ("MERGED", "9238be21", "2026-11-13T01:21:02Z", {"prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-five-prs-validated-opening-next.md"}),
    ("juniper-ml", 2558): ("MERGED", "48b66130", "2026-11-13T10:08:14Z", None),
    ("juniper-ml", 2561): ("MERGED", "7ae846b6", "2026-11-13T10:38:29Z", {"notes/releases/RELEASE_NOTES_v0.11.5.md"}),
    ("juniper-ml", 2563): ("MERGED", "d747f9e5", "2026-11-14T07:53:39Z", {"prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md"}),
    ("juniper-ml", 2565): ("MERGED", "ef883f57", "2026-11-14T22:51:43Z", {"prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-0-11-5-at-pypi-gate-guard-cuts-plan-next.md"}),
    ("juniper-ml", 2568): (
        "MERGED",
        "7ce8d365",
        "2026-11-15T02:15:25Z",
        {
            "docs/QUICK_START.md",
            "prompts/generated/JUNIPER_ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING_DESIGN_2026-11-15_0010.md",
            "util/ad-hoc/2026-11-14_cascor_canopy_release_cochanges.py",
            "util/ad-hoc/2026-11-14_parent_agents_released_paragraph_0_11_5.py",
            "util/ad-hoc/2026-11-15_cascor_0_14_0_canopy_0_10_0_security_notes_header.py",
            "util/ad-hoc/2026-11-15_cascor_canopy_release_notes_corrections.py",
        },
    ),
    ("juniper-ml", 2570): ("MERGED", "bb600136", "2026-11-15T03:03:56Z", {"notes/releases/RELEASE_NOTES_juniper-cascor_v0.14.0.md"}),
    ("juniper-ml", 2571): ("MERGED", "0578d2ec", "2026-11-15T02:29:06Z", None),
    ("juniper-ml", 2572): ("MERGED", "eeb5c694", "2026-11-15T01:57:40Z", {"notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md"}),
    ("juniper-ml", 2573): ("CLOSED", None, "2026-11-15T02:40:36Z", None),
    ("juniper-ml", 2574): ("MERGED", "7914ba9f", "2026-11-15T03:29:46Z", {"prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md"}),
    ("juniper-ml", 2576): (
        "MERGED",
        "6befa3ba",
        "2026-11-15T02:51:37Z",
        {
            ".github/workflows/ci.yml",
            ".github/workflows/docs-full-check.yml",
            "CHANGELOG.md",
            "docs/REFERENCE.md",
            "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
            "tests/test_service_fork_drift.py",
            "util/ad-hoc/2026-11-12_retry_after_guard_mutation_check.py",
        },
    ),
    # #2507 closed while this record was drafted: ml#2579 and ml#2581 carry it (flood-4's ruling 14)
    ("juniper-ml", 2507): ("CLOSED", None, "2026-11-15T05:30:31Z", {"tests/test_pyproject_extras.py"}),
    ("juniper-ml", 2579): ("MERGED", "11cac1af", "2026-11-15T04:25:56Z", None),
    ("juniper-ml", 2581): ("MERGED", "4f53e69a", "2026-11-15T05:29:07Z", None),
    # juniper-deploy's pin PR after the gates: one GitHub-signed commit a79b3640 on base 6c9e57f8
    ("juniper-deploy", 278): ("MERGED", "db7b7cb4", "2026-11-15T05:48:57Z", {"CHANGELOG.md", "docker-compose.yml", "k8s/helm/juniper/values.yaml"}),
    ("juniper-cascor", 755): ("MERGED", "5834709a", "2026-11-13T00:27:18Z", {"CHANGELOG.md", "src/api/app.py", "src/tests/unit/api/test_api_app.py"}),
    ("juniper-cascor", 757): ("MERGED", "66b39a5c", "2026-11-13T01:07:08Z", None),
    ("juniper-cascor", 758): ("MERGED", "bf6f0108", "2026-11-15T01:14:13Z", {"AGENTS.md", "CHANGELOG.md", "pyproject.toml"}),
    ("juniper-canopy", 816): ("MERGED", "b9417b2f", "2026-11-13T00:34:13Z", {"CHANGELOG.md", "src/main.py", "src/tests/unit/test_main_import_and_lifespan.py"}),
    ("juniper-canopy", 817): ("MERGED", "55ac2168", "2026-11-13T01:02:07Z", None),
    ("juniper-canopy", 818): ("MERGED", "57d90dec", "2026-11-15T01:19:38Z", {"AGENTS.md", "CHANGELOG.md", "juniper_canopy/__init__.py", "pyproject.toml", "src/__init__.py", "src/canopy_constants.py"}),
    ("juniper-data", 537): ("MERGED", "3cf8867c", "2026-11-13T02:54:07Z", None),
    ("juniper-canopy", 776): ("MERGED", "c7846b4e", "2026-10-27T00:44:30Z", None),
    ("juniper-canopy", 777): ("MERGED", "33619d6d", "2026-10-27T01:08:22Z", None),
    ("juniper-canopy", 788): ("MERGED", "af650373", "2026-11-04T10:48:31Z", None),
}

#: (repo, tag) -> (commit prefix, published_at)
RELEASES = {
    ("juniper-ml", "v0.11.5"): ("48b66130", "2026-11-13T10:24:18Z"),
    ("juniper-cascor", "v0.14.0"): ("bf6f0108", "2026-11-15T01:28:19Z"),
    ("juniper-canopy", "v0.10.0"): ("57d90dec", "2026-11-15T01:41:30Z"),
}

#: The publish runs whose `pypi` gate the owner approves: (repo, run) -> (package, version, head prefix)
GATED_RUNS = {
    ("juniper-cascor", 43663237489): ("juniper-cascor", "0.14.0", "bf6f0108"),
    ("juniper-canopy", 43664277663): ("juniper-canopy", "0.10.0", "57d90dec"),
}
#: Once a gate is PUBLISHED, how PyPI's files must equal TestPyPI's: canopy's run shares one build job between the two
#: uploads, so by sha256; cascor's has none (each publish job builds its own files), so member by member, as for 0.13.0.
GATED_COMPARE = {"juniper-cascor": "members", "juniper-canopy": "sha256"}
#: The file hashes the plan records for cascor 0.14.0's wheel: (PyPI's, TestPyPI's) prefixes, a second build of the same members
FILE_SHAS = {"juniper_cascor-0.14.0-py3-none-any.whl": ("b70f3d39", "c5c9a5dc"), "juniper_cascor-0.14.0.tar.gz": ("79cc0da3", "92f0b146")}
#: juniper-deploy main after deploy#278: each image line and how often it appears, and the two DEPLOY-15 helm tags
DEPLOY_PINS = {"juniper-cascor:0.14.0": 2, "juniper-canopy:0.10.0": 3}
HELM_TAGS = {"juniper-cascor": "0.14.0", "juniper-canopy": "0.10.0"}
#: The image runs: (repo, run) -> tag
IMAGE_RUNS = {("juniper-cascor", 43663237432): "v0.14.0", ("juniper-canopy", 43664277607): "v0.10.0"}
GHCR_TAGS = {"juniper-cascor": ("0.14.0", "0.14"), "juniper-canopy": ("0.10.0", "0.10")}

#: TestPyPI's floors for the two cuts (requires_dist strings, as PyPI's metadata spells them)
TESTPYPI_FLOORS = {
    ("juniper-cascor", "0.14.0"): {"juniper-observability>=0.4.2", "juniper-service-core<0.8.0,>=0.7.2"},
    ("juniper-canopy", "0.10.0"): {"juniper-observability<0.5.0,>=0.4.2", "juniper-service-core<0.8.0,>=0.7.2"},
}

#: (repo, path, line, fragment): the floors on main; data's and recurrence's wait for their next release PR (round 1, ruling 1)
FLOOR_LINES = [
    ("juniper-ml", "pyproject.toml", 98, '"juniper-observability>=0.4.2",'),
    ("juniper-ml", "pyproject.toml", 99, '"juniper-service-core>=0.7.2,<0.8.0",'),
    ("juniper-cascor", "pyproject.toml", 87, '"juniper-observability>=0.4.2",'),
    ("juniper-cascor", "pyproject.toml", 118, '"juniper-service-core>=0.7.2,<0.8.0",'),
    ("juniper-canopy", "pyproject.toml", 117, '"juniper-observability>=0.4.2,<0.5.0",'),
    ("juniper-canopy", "pyproject.toml", 135, '"juniper-service-core>=0.7.2,<0.8.0",'),
    ("juniper-data", "pyproject.toml", 102, '"juniper-observability>=0.4.1",'),
    ("juniper-data", "pyproject.toml", 117, '"juniper-service-core>=0.7.1,<0.8.0",'),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml", 68, '"juniper-service-core>=0.7.1,<0.8.0",'),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml", 102, '"juniper-observability[prometheus]>=0.4.1,<0.5.0",'),
]

#: (repo, path, line, fragments that must all be on the line): the source lines the findings and records cite, on main
SOURCE_LINES = [
    # APD-ECO-016's post-fix sites, as the register row cites them
    ("juniper-data", "juniper_data/api/security.py", 243, ("return max(1, math.ceil(self._window - (now - window_start)))",)),
    ("juniper-data", "juniper_data/api/security.py", 276, ("return (False, 0, self._seconds_until_reset(now, window_start))",)),
    ("juniper-data", "juniper_data/api/security.py", 279, ("self._limit - count - 1, self._seconds_until_reset(now, window_start))",)),
    ("juniper-data", "juniper_data/api/security.py", 458, ("return (True, max(1, math.ceil(remaining)))",)),
    ("juniper-cascor", "src/api/security.py", 220, ("return max(1, math.ceil(self._window - (now - window_start)))",)),
    ("juniper-cascor", "src/api/security.py", 250, ("return (False, 0, self._seconds_until_reset(now, window_start))",)),
    ("juniper-cascor", "src/api/security.py", 253, ("self._limit - count - 1, self._seconds_until_reset(now, window_start))",)),
    ("juniper-cascor", "src/api/security.py", 412, ("return (True, max(1, math.ceil(remaining)))",)),
    ("juniper-canopy", "src/security.py", 259, ("return max(1, math.ceil(self._window - (now - window_start)))",)),
    ("juniper-canopy", "src/security.py", 291, ("return (False, 0, self._seconds_until_reset(now, window_start))",)),
    ("juniper-canopy", "src/security.py", 294, ("self._limit - count - 1, self._seconds_until_reset(now, window_start))",)),
    ("juniper-ml", "juniper-service-core/juniper_service_core/security.py", 236, ("return max(1, math.ceil(self._window - (now - window_start)))",)),
    ("juniper-ml", "juniper-service-core/juniper_service_core/security.py", 474, ("return (True, max(1, math.ceil(remaining)))",)),
    # The telemetry opt-outs (ruling 4) and the tests that skip below FastAPI 0.142 (finding: no non-skipping test)
    ("juniper-cascor", "src/api/app.py", 778, ("telemetry={",)),
    ("juniper-canopy", "src/main.py", 546, ("telemetry={",)),
    ("juniper-data", "juniper_data/api/app.py", 108, ("telemetry={",)),
    ("juniper-data", "juniper_data/tests/unit/test_api_app.py", 64, ('pytest.importorskip("fastapi.telemetry"',)),
    ("juniper-cascor", "src/tests/unit/api/test_api_app.py", 44, ('pytest.importorskip("fastapi.telemetry"',)),
    ("juniper-canopy", "src/tests/unit/test_main_import_and_lifespan.py", 330, ('pytest.importorskip("fastapi.telemetry"',)),
    # service-core's factory and recurrence's FastAPI (finding: the factory passes no telemetry=)
    ("juniper-ml", "juniper-service-core/juniper_service_core/app.py", 56, ("app = FastAPI(",)),
    ("juniper-recurrence", "juniper-recurrence/requirements.lock", 100, ("fastapi==0.141.1",)),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml", 55, ('"fastapi>=0.110",',)),
    # The wall clock in all four limiters, and canopy's eviction (finding: a backward step)
    ("juniper-data", "juniper_data/api/security.py", 257, ("now = time.time()",)),
    ("juniper-cascor", "src/api/security.py", 234, ("now = time.time()",)),
    ("juniper-canopy", "src/security.py", 273, ("now = time.time()",)),
    ("juniper-ml", "juniper-service-core/juniper_service_core/security.py", 250, ("now = time.time()",)),
    ("juniper-canopy", "src/security.py", 234, ("def _evict_expired(self, now: float) -> None:",)),
    # cascor's API reference against its middleware (finding: the "Exempt paths" row)
    ("juniper-cascor", "docs/api/JUNIPER_CASCOR_API_REFERENCE.md", 113, ("| Exempt paths |", "`/docs`", "`/openapi.json`", "`/redoc`")),
    ("juniper-cascor", "src/api/middleware.py", 16, ("EXEMPT_PATHS = {",)),
    # The WebSocket waits that round to one decimal (finding: 0.0 under 50 ms)
    ("juniper-cascor", "src/api/websocket/control_security.py", 81, ("return round(deficit / self._refill_rate, 1)",)),
    ("juniper-cascor", "src/api/websocket/control_security.py", 154, ("return round(remaining, 1)",)),
    ("juniper-ml", "juniper-service-core/juniper_service_core/websocket/control_security.py", 112, ("return round(deficit / self._refill_rate, 1)",)),
    ("juniper-ml", "juniper-service-core/juniper_service_core/websocket/control_security.py", 185, ("return round(remaining, 1)",)),
    # juniper-ml's registry test (finding: it walks tmp/)
    ("juniper-ml", "tests/test_release_train_registry.py", 178, ('skip_parts = {".claude", "build", "dist", "node_modules", ".git", ".tox", ".venv"}',)),
    ("juniper-ml", "tests/test_release_train_registry.py", 180, ('for pp in ml_root.rglob("pyproject.toml"):',)),
    # The released-section drift tool sees only bullets under a released heading (finding: #2360's second kind)
    ("juniper-ml", "util/ad-hoc/2026-09-23_released_section_drift.py", 2, ("List CHANGELOG bullets filed under a RELEASED version that its archived release notes do not carry.",)),
    # canopy's CPU conda spec against its floor (finding)
    ("juniper-canopy", "conf/conda_environment_cpu.yaml", 47, ("dash=3.3.0",)),
    ("juniper-canopy", "pyproject.toml", 56, ('"dash>=4.0.0",',)),
    # canopy's schema-drift comment against data's notify matrix (finding)
    ("juniper-canopy", ".github/workflows/juniper-data-schema-drift.yml", 40, ("It fires here only once",)),
    ("juniper-canopy", ".github/workflows/juniper-data-schema-drift.yml", 41, ("juniper-data's notify matrix lists juniper-canopy.",)),
    ("juniper-data", ".github/workflows/notify-consumers.yml", 78, ("repo: [juniper-recurrence, juniper-canopy]",)),
    # the flood-4 record's §8, which ends at 14 ("ruling 17" in two CHANGELOGs is read at the release tags: TAG_LINES)
    ("juniper-ml", "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md", 298, ("14. **juniper-ml#2507**",)),
    # The v2 draft's stale line (finding; v1 takes the record)
    ("juniper-ml", "notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md", 153, ("has no APD-ECO-016",)),
    # juniper-deploy's stale-pin check: a pin behind GHCR's highest X.Y.Z tag is flagged, and is an error only under --fail-on-stale
    ("juniper-deploy", "scripts/verify_published_images.py", 301, ("elif newest > pinned:",)),
    ("juniper-deploy", "scripts/verify_published_images.py", 325, ("if args.fail_on_stale:",)),
]

#: (repo, path, ref, line, fragments): lines read at a release tag, because a CHANGELOG line moves on main with each entry
TAG_LINES = [
    ("juniper-cascor", "CHANGELOG.md", "v0.14.0", 244, ("**Where it was found.**", "ruling 17", "stop-then-start")),
    ("juniper-canopy", "CHANGELOG.md", "v0.10.0", 156, ("ruling 17", "lists rulings 1 to 14 in §8")),
]

#: Text that must NOT be in a file on main: (repo, path, fragment, why)
ABSENT = [
    ("juniper-ml", "juniper-service-core/juniper_service_core/app.py", "telemetry=", "service-core's factory passes no telemetry="),
    ("juniper-ml", "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md", "\n15. **", "the flood-4 record's §8 lists no ruling after 14"),
]

#: Text that must be in a file on main: (repo, path, fragment, why)
PRESENT = [
    ("juniper-ml", "juniper-service-core/CHANGELOG.md", "so the release carrying it is a minor, 0.8.0, not a patch", "service-core's [Unreleased] makes its next release 0.8.0"),
    ("juniper-ml", "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md", "Note added 2026-11-15: when canopy gains a `FailedAuthThrottle`", "APD-ECO-010's row carries the round-2 review's note instead of a tripwire"),
]

#: The caps that must widen before service-core 0.8.0 (finding): (repo, path, line)
CAP_LINES = [
    ("juniper-ml", "pyproject.toml", 99),
    ("juniper-data", "pyproject.toml", 117),
    ("juniper-recurrence", "juniper-recurrence/pyproject.toml", 68),
    ("juniper-cascor", "pyproject.toml", 118),
    ("juniper-canopy", "pyproject.toml", 135),
]

#: The owner's answers: (session prefix, labels that must each appear as ="<label>", answered-at prefix, asked-at prefix)
ANSWERS = [
    ("a4e1e914", ("In release PRs (Recommended)", "Floor PR, then 0.11.5 (Recommended)", "Row + fix all three (Recommended)", "Port to both now (Recommended)"), "2026-11-09T14:48:41", "2026-11-09T14:27:13"),
    ("218ff61e", ("Yes, as patch 0.11.5 (Recommended)", "One at a time, with background", "Remove after checks (Recommended)"), "2026-11-13T01:57:00", "2026-11-13T01:50:37"),
    ("218ff61e", ("Now, in its own thread (Recommended)",), "2026-11-13T02:14:33", "2026-11-13T02:08:33"),
    ("218ff61e", ("cascor + canopy now (Recommended)",), "2026-11-13T02:28:23", "2026-11-13T02:24:03"),
    ("218ff61e", ("Probe per environment",), "2026-11-13T02:40:52", "2026-11-13T02:34:09"),
    ("218ff61e", ("Guarded session pulls (Recommended)",), "2026-11-13T10:10:51", "2026-11-13T02:41:20"),
    ("1b4fec84", ("Edit it (Recommended)",), "2026-11-14T22:59:11", "2026-11-14T22:57:35"),
    ("1b4fec84", ("0.14.0 (Recommended)",), "2026-11-14T23:36:54", "2026-11-14T22:59:16"),
    ("1b4fec84", ("0.10.0 (Recommended)",), "2026-11-14T23:42:13", "2026-11-14T23:37:02"),
    ("f2b4e7c3", ("WebSocket gaps beside N-4, Lifecycle races beside N-2, Match cascor's resume answers,  we should verify that follow up 3 is the right apprach",), "2026-11-12T23:34:04", "2026-11-12T23:29:29"),
    # the 2026-11-15 dialog: cascor 0.14.0, the fix's scope, the parent docs
    ("b9dfa450", ("Approve as is, verify after (Recommended)", "cascor, then every other (Recommended)", "Edit it once both publish (Recommended)"), "2026-11-15T05:24:49", "2026-11-15T05:17:06"),
]
#: Dialogs the owner sent back to clarify: (session prefix, asked-at prefix, answered-at prefix)
CLARIFIED = [("a4e1e914", "2026-11-09T14:49:42", "2026-11-12T00:20:11"), ("7d425759", "2026-11-14T10:20:43", "2026-11-14T22:10:39")]
#: The owner's typed words: (session prefix, timestamp prefix, fragment)
TYPED = [
    ("7d425759", "2026-11-14T22:37:55", "the four open questions should be handled by the session working from the updated handoff."),
    ("7d425759", "2026-11-14T22:12:40", "let's update the latest identified handoff doc for this work arc"),
    ("1b4fec84", "2026-11-14T22:53:41", "merge approval granted"),
    ("218ff61e", "2026-11-13T01:45:27", "merge approval granted"),
    ("6e3bdef0", "2026-11-12T00:39:16", "approval granted for merging and related git operations for this work arc."),
    ("b9dfa450", "2026-11-15T03:14:03", "merge approval granted"),
    # the owner's directive on the publish artifact, quoted verbatim in the plan
    (
        "b9dfa450",
        "2026-11-15T05:14:10",
        "this needs to be fixed. deploy to pypi should send the same artifact that was already sent to testpypi. an identical hash check, of the artifacts after testpypi deploy and prior to pypi deploy, might also be helpful here to prevent this from slipping through the cracks again.",
    ),
]

# --- Added with the two reviews' pass (2026-11-15): the facts it records, wherever a check is cheap -----------------

#: Commits that must be ancestors of a tag (compare API: behind_by 0): (repo, commit, tag)
ANCESTRY = [
    ("juniper-canopy", "c7846b4e", "v0.10.0"),
    ("juniper-canopy", "33619d6d", "v0.10.0"),
    ("juniper-canopy", "af650373", "v0.10.0"),
    # the telemetry opt-outs and the Retry-After round-ups ship in the two cuts
    ("juniper-canopy", "b9417b2f", "v0.10.0"),
    ("juniper-canopy", "55ac2168", "v0.10.0"),
    ("juniper-cascor", "5834709a", "v0.14.0"),
    ("juniper-cascor", "66b39a5c", "v0.14.0"),
]
#: The juniper-ml primary's code JuniperCascor1 imports, read from the local repository: (tag, path, the PR numbers of its commits)
PRIMARY_COMMIT = "eeb5c694"
UNRELEASED = [
    ("juniper-service-core-v0.7.2", "juniper-service-core/juniper_service_core", ["#2531", "#2534", "#2547", "#2557"]),
    ("juniper-observability-v0.4.2", "juniper-observability/juniper_observability", []),
]
#: The primary's reflog: the fast-forwards since ruling 7 of 2026-11-13 (answered 10:10:51Z): (old, new) prefixes
RULING7_AT = "2026-11-13T10:10:51Z"
PULLS_SINCE_RULING7 = [("01f9f89b", "48b66130"), ("48b66130", "7ae846b6"), ("7ae846b6", "d747f9e5"), ("d747f9e5", "9c2677b8"), ("9c2677b8", "4a786c81"), ("4a786c81", "eeb5c694")]
#: The parent AGENTS.md's prior copy, kept in the primary's tmp/ since 2026-11-15
PARENT_BACKUP = ("tmp", "2026-11-14-parent-agents-md-backup", "AGENTS.md.before-2026-11-14-edit")
PARENT_BACKUP_SHA = "90df27837369e0b4"
#: The parent AGENTS.md after its 2026-11-15 edit (ruling 3 of 2026-11-15), and that edit's two copies in the primary's tmp/
PARENT_SHA = "3009c3f413c95abb"
PARENT_PAIR = {
    ("tmp", "2026-11-15-parent-agents-md-backup", "AGENTS.md.before-cascor-0-14-0-canopy-0-10-0-edit"): "f3f69b34e33cfc8d",
    ("tmp", "2026-11-15-parent-agents-md-backup", "AGENTS.md.after-cascor-0-14-0-canopy-0-10-0-edit"): "3009c3f413c95abb",
}
#: (repo, path, ref, line, fragments): more lines this record cites
MORE_LINES = [
    ("juniper-canopy", "CHANGELOG.md", "v0.10.0", 221, ("owner ruling 17",)),
    ("juniper-ml", "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md", "main", 89, ("3. Ruling 17: build, validate and land four fixes",)),
    ("juniper-deploy", "docker-compose.yml", "main", 598, ("image: ghcr.io/pcalnon/juniper-recurrence:",)),
]
#: The v2 draft's lines this record lists as stale: (line, fragment)
V2_PATH = "notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md"
V2_STALE = [
    (110, "No running image carries observability 0.4.2 yet"),
    (150, "being carried out by session `6e3bdef0`"),
    (153, "has no APD-ECO-016"),
    (315, "**The R-OBS-SC-2 follow-ups**, in flight"),
    (322, "P3's follow-up session will open one for APD-ECO-016"),
    (357, "**0.11.5**, a patch"),
    (358, "whose start is unruled"),
    (398, "**Q4** who may move the juniper-ml primary"),
    (399, "whether that session may cut juniper-ml 0.11.5"),
    (409, "juniper-ml 0.11.5 first"),
    (455, "No session moves it (Q4)"),
    (480, "Never pull one or switch its branch"),
]
#: The parent AGENTS.md's 2026-11-15 edit: passages it added (each must be present) and the one it removed (must be absent)
PARENT_ADDED = (
    "**Last Updated**: 2026-11-15",
    "(re-probed against PyPI on 2026-11-15 UTC)",
    "juniper-deploy pinned the `0.13.0` image from juniper-deploy#266",
    "0.14.0, juniper-canopy 0.10.0 and juniper-ml 0.11.5's `[tools]` floor them",
    "- **juniper-canopy 0.10.0** (PyPI 2026-11-15 05:17Z, publish run 43664277663;",
    "juniper-deploy pins both images since juniper-deploy#278 (2026-11-15).",
)
PARENT_REMOVED = "juniper-deploy pins the `0.13.0` image since juniper-deploy#266"
#: The archived reviews' tallies: (file, regex, {severity: count}); review B's NITs are the sub-bullets of its item 29
REVIEWS = "reports/2026-11-15_r-obs-sc-2-follow-ups-reviews"
TALLIES = [
    ("guard-round-1_report.md", r"^\*\*\d+\. (BLOCKER|MAJOR|MINOR|NIT)", {"MAJOR": 1, "MINOR": 6, "NIT": 6}),
    ("guard-round-2_report.md", r"^\*\*\d+\. (BLOCKER|MAJOR|MINOR|NIT)", {"BLOCKER": 3, "MAJOR": 1, "MINOR": 5, "NIT": 7}),
    ("plan-v1-15-16-review-a_report.md", r"^\*\*\d+\. (BLOCKER|MAJOR|MINOR|NIT)", {"BLOCKER": 1, "MAJOR": 3, "MINOR": 3, "NIT": 10}),
    ("plan-v1-15-16-review-b_report.md", r"^\d+\. \*\*(BLOCKER|MAJOR|MINOR)", {"BLOCKER": 1, "MAJOR": 9, "MINOR": 19}),
]
#: The release bodies' round 1, by section: (heading, {severity: count})
NOTES_R1 = [("## juniper-cascor v0.14.0", {"BLOCKER": 2, "MAJOR": 4, "MINOR": 4, "NIT": 1}), ("## juniper-canopy v0.10.0", {"BLOCKER": 5, "MINOR": 6, "NIT": 4})]
FIXPASS = ("five-prs-validation-fixpass-round-1.md", "ad8d90912ec864c9")

PROJECTS = Path.home() / ".claude" / "projects"
CONDA_ENVS = Path("/opt/miniforge3/envs")
JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ML_PRIMARY = JUNIPER / "juniper-ml"
#: env -> (interpreter, the versions it must hold as plain installs); JuniperCascor1 is checked separately.
PLAIN_ENVS = {"JuniperData": ("bin/python3.14t", "0.4.0", "0.5.0"), "JuniperCanopy1": ("bin/python", "0.4.0", "0.5.0")}
TRIO_PORTS = (8101, 8202, 8051)


def check(ok: bool, label: str, seen: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {seen}")
    if not ok:
        FAILS.append(label)


def gh_json(*args: str) -> object:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)}: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


_RAW: dict[tuple[str, str, str], str] = {}


def gh_raw(repo: str, path: str, ref: str = "main") -> str:
    if (repo, path, ref) not in _RAW:
        out = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}"], capture_output=True, text=True, check=False)
        if out.returncode != 0:
            raise RuntimeError(f"{repo}:{path}@{ref}: {out.stderr.strip()[:300]}")
        _RAW[(repo, path, ref)] = out.stdout
    return _RAW[(repo, path, ref)]


def http(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310 -- fixed https index and registry URLs
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def http_json(url: str) -> dict | None:
    status, body = http(url)
    return json.loads(body) if status == 200 else None


def prs() -> None:
    print("== PRs")
    for (repo, number), (state, prefix, when, files) in PRS.items():
        data = gh_json("pr", "view", str(number), "--repo", f"{OWNER}/{repo}", "--json", "state,isDraft,mergedAt,closedAt,mergeCommit,files,title")
        oid = (data.get("mergeCommit") or {}).get("oid") or ""
        stamp = data.get("mergedAt") or data.get("closedAt")
        seen = f"{data['state']}{' draft' if data.get('isDraft') else ''} {stamp} {oid[:8]} {data['title'][:70]}"
        ok = data["state"] == state and (prefix is None or oid.startswith(prefix)) and (when is None or stamp == when)
        check(ok, f"{repo}#{number}", seen)
        if files is not None:
            got = {f["path"] for f in data["files"]}
            check(got == files, f"{repo}#{number} files", ", ".join(sorted(got)))


def resolve_tag(repo: str, tag: str) -> str:
    obj = gh_json("api", f"repos/{OWNER}/{repo}/git/ref/tags/{tag}")["object"]
    sha = obj["sha"]
    if obj["type"] == "tag":
        sha = gh_json("api", f"repos/{OWNER}/{repo}/git/tags/{sha}")["object"]["sha"]
    return sha


def releases() -> None:
    print("== Releases (tag -> commit, published_at)")
    for (repo, tag), (prefix, published) in RELEASES.items():
        rel = gh_json("api", f"repos/{OWNER}/{repo}/releases/tags/{tag}")
        sha = resolve_tag(repo, tag)
        latest = gh_json("api", f"repos/{OWNER}/{repo}/releases/latest").get("tag_name")
        ok = sha.startswith(prefix) and rel["published_at"] == published and rel["target_commitish"].startswith(prefix)
        check(ok, f"{repo} {tag}", f"commit {sha[:8]}, target {rel['target_commitish'][:8]}, published {rel['published_at']}; releases/latest is {latest}")


def jobs_of(repo: str, run: int) -> list[dict]:
    return gh_json("api", f"repos/{OWNER}/{repo}/actions/runs/{run}/jobs")["jobs"]


def owner_approvals(repo: str, run: int) -> list[str]:
    approvals = gh_json("api", f"repos/{OWNER}/{repo}/actions/runs/{run}/approvals") or []
    return [f"{a['state']} by {a['user']['login']} ({a.get('comment')!r})" for a in approvals if a["user"]["login"] == OWNER]


def published_run() -> None:
    print("== juniper-ml 0.11.5's publish run 43408809021 (approved and published)")
    for job in jobs_of("juniper-ml", 43408809021):
        check(job["conclusion"] == "success", f"run 43408809021 job '{job['name']}'", f"{job['status']}/{job['conclusion']} {job['started_at']} -> {job['completed_at']}")
        if job["name"] == "Publish to PyPI":
            check((job["started_at"], job["completed_at"]) == ("2026-11-14T00:16:06Z", "2026-11-14T00:16:27Z"), "Publish to PyPI ran 00:16:06Z-00:16:27Z", f"{job['started_at']} -> {job['completed_at']}")
    approvals = owner_approvals("juniper-ml", 43408809021)
    check(any("approved by pcalnon ('approved for pypi')" in a for a in approvals), "run 43408809021 owner approval", "; ".join(approvals) or "none")
    pending = gh_json("api", f"repos/{OWNER}/juniper-ml/actions/runs/43408809021/pending_deployments") or []
    check(not pending, "run 43408809021 pending_deployments", str([p["environment"]["name"] for p in pending]))


def gated_runs() -> None:
    print("== The two consumer publish runs (state that MOVES: WAITING at `pypi`, or PUBLISHED)")
    for (repo, run), (package, version, head) in GATED_RUNS.items():
        meta = gh_json("api", f"repos/{OWNER}/{repo}/actions/runs/{run}")
        jobs = {j["name"]: j for j in jobs_of(repo, run)}
        pending = [p["environment"]["name"] for p in (gh_json("api", f"repos/{OWNER}/{repo}/actions/runs/{run}/pending_deployments") or [])]
        approvals = owner_approvals(repo, run)
        status, _ = http(f"https://pypi.org/pypi/{package}/{version}/json")
        pypi_job = jobs.get("Publish to PyPI", {})
        others_ok = all(j["conclusion"] == "success" for name, j in jobs.items() if name != "Publish to PyPI")
        waiting = others_ok and pypi_job.get("status") == "waiting" and pending == ["pypi"] and not approvals and status == 404
        published = others_ok and pypi_job.get("conclusion") == "success" and not pending and bool(approvals) and status == 200
        state = "WAITING at pypi" if waiting else ("PUBLISHED" if published else "NEITHER")
        trail = "; ".join(f"{n}: {j['status']}/{j['conclusion']} {j['started_at']}->{j['completed_at']}" for n, j in jobs.items())
        check(meta["head_sha"].startswith(head) and (waiting or published), f"{repo} run {run} ({package} {version})", f"{state}; created {meta['created_at']}; {trail}; pending {pending}; owner approvals {approvals or 'none'}; PyPI /{version}/json {status}")
        NOTES.append(f"{package} {version}: {state} (read {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')})")
        if published:
            same_files(package, version, GATED_COMPARE[package])


def archive_members(name: str, blob: bytes) -> dict[str, str]:
    if name.endswith(".whl"):
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            return {i.filename: hashlib.sha256(archive.read(i)).hexdigest() for i in archive.infolist()}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
        return {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive.getmembers() if m.isfile()}


def same_files(package: str, version: str, by: str) -> None:
    """After a gate: PyPI's files against TestPyPI's, by sha256 (a shared build job) or member by member (none)."""
    prod = http_json(f"https://pypi.org/pypi/{package}/{version}/json")
    test = http_json(f"https://test.pypi.org/pypi/{package}/{version}/json")
    test_files = {u["filename"]: u for u in test["urls"]}
    for u in prod["urls"]:
        twin = test_files.get(u["filename"])
        if by == "sha256":
            same = bool(twin) and twin["digests"]["sha256"] == u["digests"]["sha256"]
            seen = f"uploaded {u['upload_time_iso_8601'][:19]}Z, sha256 {u['digests']['sha256'][:16]}, TestPyPI's {'same' if same else 'DIFFERENT or absent'}"
        else:
            a = archive_members(u["filename"], http(u["url"])[1])
            b = archive_members(u["filename"], http(twin["url"])[1]) if twin else {}
            differ = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            pair = (u["digests"]["sha256"][:8], twin["digests"]["sha256"][:8] if twin else "absent")
            # the plan records the wheel's two hashes; a file it names must still carry them
            same = bool(a) and not differ and FILE_SHAS.get(u["filename"], pair) == pair
            seen = f"uploaded {u['upload_time_iso_8601'][:19]}Z; sha256 PyPI {pair[0]}, TestPyPI {pair[1]}; {len(a)} members, {len(differ)} differ from TestPyPI's"
        check(same, f"PyPI {u['filename']} against TestPyPI's ({by})", seen)
    print("== Image runs and GHCR tags")
    for (repo, run), tag in IMAGE_RUNS.items():
        meta = gh_json("api", f"repos/{OWNER}/{repo}/actions/runs/{run}")
        check(meta["conclusion"] == "success" and meta["head_branch"] == tag and meta["event"] == "release", f"{repo} image run {run}", f"{meta['name']} {meta['event']} {meta['head_branch']} {meta['status']}/{meta['conclusion']} {meta['created_at']} -> {meta['updated_at']}")
    for repo, wanted in GHCR_TAGS.items():
        tags = ghcr_tags(repo)
        check(all(t in tags for t in wanted), f"GHCR {repo} tags {', '.join(wanted)}", f"{len(tags)} tags; {sorted(t for t in tags if t[:1].isdigit())}")


def ghcr_tags(repo: str) -> list[str]:
    token = json.loads(http(f"https://ghcr.io/token?scope=repository:{OWNER}/{repo}:pull")[1])["token"]
    req = urllib.request.Request(f"https://ghcr.io/v2/{OWNER}/{repo}/tags/list?n=1000", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310 -- fixed https registry URL
        return json.load(resp).get("tags", [])


def indexes() -> None:
    print("== PyPI and TestPyPI")
    prod = http_json("https://pypi.org/pypi/juniper-ml/0.11.5/json")
    test = http_json("https://test.pypi.org/pypi/juniper-ml/0.11.5/json")
    if prod is None or test is None:
        check(False, "juniper-ml 0.11.5 on PyPI and TestPyPI", f"PyPI {'200' if prod else 'missing'}, TestPyPI {'200' if test else 'missing'}")
    else:
        test_sha = {u["filename"]: u["digests"]["sha256"] for u in test["urls"]}
        for u in prod["urls"]:
            same = test_sha.get(u["filename"]) == u["digests"]["sha256"]
            check(same, f"PyPI {u['filename']}", f"uploaded {u['upload_time_iso_8601']}, sha256 {u['digests']['sha256'][:16]}, TestPyPI's {'same' if same else 'DIFFERENT or absent'}")
        tools = sorted(r for r in prod["info"]["requires_dist"] if 'extra == "tools"' in r and ("observability" in r or "service-core" in r))
        check(tools == ['juniper-observability>=0.4.2; extra == "tools"', 'juniper-service-core<0.8.0,>=0.7.2; extra == "tools"'], "juniper-ml 0.11.5 [tools] floors", "; ".join(tools))
        # §2's P12 row: 0.11.5 carries P12's floors too ([recurrence] unchanged since 0.11.4)
        rec = sorted(r for r in prod["info"]["requires_dist"] if 'extra == "recurrence"' in r and r.startswith("juniper-recurrence"))
        check('juniper-recurrence<0.9.0,>=0.8.1; extra == "recurrence"' in rec, "juniper-ml 0.11.5 [recurrence] floor", "; ".join(rec))
    for (package, version), floors in TESTPYPI_FLOORS.items():
        meta = http_json(f"https://test.pypi.org/pypi/{package}/{version}/json")
        if meta is None:
            check(False, f"TestPyPI {package} {version}", "404")
            continue
        files = ", ".join(f"{u['filename']} {u['upload_time_iso_8601'][:19]}Z" for u in meta["urls"])
        got = {r for r in (meta["info"].get("requires_dist") or []) if r.startswith(("juniper-observability", "juniper-service-core"))}
        check(got == floors, f"TestPyPI {package} {version} floors", f"{sorted(got)}; files {files}")


def line_of(repo: str, path: str, line: int, ref: str = "main") -> str:
    lines = gh_raw(repo, path, ref).split("\n")
    return lines[line - 1] if line <= len(lines) else "<past end>"


def floors_and_pins() -> None:
    print("== Floors on main (cascor and canopy raised theirs in their release PRs; data and recurrence wait)")
    for repo, path, line, fragment in FLOOR_LINES:
        text = line_of(repo, path, line).strip()
        check(text == fragment, f"{repo}:{path}:{line}", text[:150])
    print("== The service-core caps that widen before 0.8.0")
    for repo, path, line in CAP_LINES:
        text = line_of(repo, path, line).strip()
        check("juniper-service-core" in text and "<0.8.0" in text, f"{repo}:{path}:{line} caps <0.8.0", text[:150])
    print("== juniper-deploy's image pins on main: deploy#278 (2026-11-15) moved cascor and canopy; recurrence's MOVES only if a later PR moves it")
    compose = gh_raw("juniper-deploy", "docker-compose.yml")
    pins = {name: sorted(set(re.findall(rf"image:\s*ghcr\.io/{OWNER}/{name}:(\S+)", compose))) for name in ("juniper-cascor", "juniper-canopy", "juniper-data", "juniper-recurrence")}
    for image, count in DEPLOY_PINS.items():
        seen = compose.count(f"image: ghcr.io/{OWNER}/{image}\n")
        check(seen == count, f"docker-compose.yml pins {image} {count} times", f"{seen}; all pins {pins}")
    for image in ("juniper-cascor:0.13.0", "juniper-canopy:0.9.0"):
        check(f"ghcr.io/{OWNER}/{image}" not in compose, f"docker-compose.yml no longer pins {image}", "absent" if f"ghcr.io/{OWNER}/{image}" not in compose else "STILL PINNED")
    values = gh_raw("juniper-deploy", "k8s/helm/juniper/values.yaml")
    for repo, tag in HELM_TAGS.items():
        block = f'    repository: {repo}\n    # DEPLOY-15: pinned; bump with {repo} releases.\n    tag: "{tag}"\n'
        check(values.count(block) == 1, f"k8s/helm/juniper/values.yaml's DEPLOY-15 tag for {repo} is {tag}", f"{values.count(block)} match(es)")
    print("== GHCR's highest X.Y.Z tag against each pin: cascor and canopy CURRENT; recurrence's MOVES (BEHIND, or CURRENT if a PR moves it)")
    for repo, pinned in (("juniper-cascor", "0.14.0"), ("juniper-canopy", "0.10.0")):
        newest = max(tuple(int(x) for x in t.split(".")) for t in ghcr_tags(repo) if re.fullmatch(r"\d+\.\d+\.\d+", t))
        check(".".join(map(str, newest)) == pinned and pins[repo] == [pinned], f"{repo} pin is current on GHCR", f"highest X.Y.Z tag {'.'.join(map(str, newest))}; pins {pins[repo]}")
    newest = max(tuple(int(x) for x in t.split(".")) for t in ghcr_tags("juniper-recurrence") if re.fullmatch(r"\d+\.\d+\.\d+", t))
    pinned = pins["juniper-recurrence"]
    rstate = "BEHIND (0.8.0; GHCR serves 0.8.1)" if pinned == ["0.8.0"] else ("CURRENT (0.8.1)" if pinned == ["0.8.1"] else "NEITHER")
    check(newest == (0, 8, 1) and rstate != "NEITHER", "juniper-recurrence pin vs GHCR", f"{rstate}; highest X.Y.Z tag {'.'.join(map(str, newest))}; pins {pinned}")
    NOTES.append(f"juniper-deploy recurrence pin: {rstate}")


def register() -> None:
    print("== The register's APD-ECO-016 rows on main, and the guard")
    text = gh_raw("juniper-ml", "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")
    rows = [line for line in text.split("\n") if line.startswith("| APD-ECO-016 |")]
    check(len(rows) == 2, "two APD-ECO-016 table rows (§4.9 and §5.1)", f"{len(rows)} rows")
    if rows:
        main_row = rows[0]
        needles = ("**FIXED (", "juniper-data/pull/537", "juniper-cascor/pull/757", "juniper-canopy/pull/817", "filed 2026-11-15, already fixed")
        check(all(n in main_row for n in needles), "the §4.9 row is filed FIXED, naming data#537, cascor#757, canopy#817", main_row[:160])
    guard = gh_raw("juniper-ml", "tests/test_service_fork_drift.py")
    check('"retry-after-rounds-up"' in guard and "APD-ECO-016" in guard, "tests/test_service_fork_drift.py names retry-after-rounds-up and APD-ECO-016", f"{guard.count('retry-after-rounds-up')} mentions")
    print("== Docs Full Check, dispatched after juniper-ml#2576")
    meta = gh_json("api", f"repos/{OWNER}/juniper-ml/actions/runs/43669737463")
    check(meta["event"] == "workflow_dispatch" and meta["head_sha"].startswith("6befa3ba") and meta["conclusion"] == "success", "run 43669737463", f"{meta['name']} {meta['event']} {meta['head_sha'][:8]} {meta['conclusion']} {meta['created_at']}")
    job = gh_json("api", f"repos/{OWNER}/juniper-ml/actions/runs/43669737463/jobs")["jobs"][0]
    log = subprocess.run(["gh", "api", f"repos/{OWNER}/juniper-ml/actions/jobs/{job['id']}/logs"], capture_output=True, text=True, check=False).stdout
    start = log.find("python3 -m unittest -v tests/test_service_fork_drift.py")
    stop = start + 20000
    tail = log[start:stop] if start >= 0 else ""
    match = re.search(r"Ran (\d+) tests? in [0-9.]+s\s*\n\S*\s*\n\S*\s*(OK[^\n]*)", tail)
    ran = f"Ran {match.group(1)} tests; {match.group(2).strip()}" if match else "no fork-drift summary found"
    check(bool(match) and match.group(1) == "17" and match.group(2).strip() == "OK", "the fork-drift step: 17 tests, OK, no skips", ran)


def sources() -> None:
    print("== The source lines the findings cite, on each repository's main")
    for repo, path, line, fragments in SOURCE_LINES:
        try:
            text = line_of(repo, path, line).strip()
        except RuntimeError as exc:
            check(False, f"{repo}:{path}:{line}", str(exc))
            continue
        check(all(f in text for f in fragments), f"{repo}:{path}:{line}", text[:150])
    for repo, path, ref, line, fragments in TAG_LINES:
        text = line_of(repo, path, line, ref).strip()
        check(all(f in text for f in fragments), f"{repo}:{path}:{line} at {ref}", text[:150])
    middleware = gh_raw("juniper-cascor", "src/api/middleware.py")
    start = middleware.find("EXEMPT_PATHS = {")
    block = middleware[start:]
    end = block.find("}") + 1
    block = block[:end]
    paths = re.findall(r'"(/[^"]*)"', block)
    check(not {"/docs", "/openapi.json", "/redoc"} & set(paths), "cascor EXEMPT_PATHS exempts only health and /metrics", ", ".join(paths))
    for repo, path, fragment, why in ABSENT:
        check(fragment not in gh_raw(repo, path), f"{repo}:{path} lacks {fragment.strip()!r}", why)
    for repo, path, fragment, why in PRESENT:
        check(fragment in gh_raw(repo, path), f"{repo}:{path} holds {fragment[:50]!r}...", why)
    compare = gh_json("api", f"repos/{OWNER}/juniper-cascor/compare/v0.13.0...v0.14.0")
    names = [f["filename"] for f in compare["files"]]
    check("src/api/secrets.py" not in names, "cascor v0.13.0...v0.14.0 leaves src/api/secrets.py unchanged (no cascor F-S10 fix)", f"{compare['ahead_by']} commits, {len(names)} files")
    body = gh_json("pr", "view", "2576", "--repo", f"{OWNER}/juniper-ml", "--json", "body")["body"]
    needles = ("This filing makes three plan passages stale", '"with no register row"', '"has no APD-ECO-016"', "Known stale text, left unchanged")
    check(all(n in body for n in needles), "juniper-ml#2576's body lists the stale plan passages and the stale text it leaves", ", ".join(n for n in needles if n in body))


# --- The owner's answers, from the transcripts -------------------------------------------------------------------------


def transcript(prefix: str) -> Path | None:
    hits = sorted(PROJECTS.glob(f"*/{prefix}*.jsonl"))
    return hits[0] if len(hits) == 1 else None


def result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block.get("text", "") for block in content if isinstance(block, dict))
    return repr(content)


def ask_calls(path: Path) -> list[dict]:
    """Each AskUserQuestion call: when FIRST asked and FIRST answered by a timestamped entry, and the result text.

    util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py keeps the LAST entry carrying a result; a later
    ``api-request-blob`` copy has no timestamp, so it reads ``answered None`` for 218ff61e's call 5 and 7d425759's call.
    A call can also first appear in such a copy (1b4fec84's), so neither time is taken from an entry without one.
    """
    calls: dict[str, dict] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            continue
        for block in message["content"]:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                if block["id"] not in calls:
                    calls[block["id"]] = {"asked_at": None, "answered_at": None, "answer": None}
                    order.append(block["id"])
                if calls[block["id"]]["asked_at"] is None:
                    calls[block["id"]]["asked_at"] = entry.get("timestamp")
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in calls:
                record = calls[block["tool_use_id"]]
                if record["answered_at"] is None and entry.get("timestamp"):
                    record["answered_at"] = entry["timestamp"]
                    record["answer"] = result_text(block.get("content"))
    return [calls[i] for i in order]


def typed_turns(path: Path) -> list[tuple[str, str]]:
    turns = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "user" or not entry.get("timestamp") or entry.get("isSidechain"):
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, list):
            content = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        if isinstance(content, str) and content:
            turns.append((entry["timestamp"], content))
    return turns


def answers() -> None:
    print("== The owner's answers (transcripts found by session-id prefix; first timestamped result)")
    cache: dict[str, list[dict] | None] = {}
    for prefix in sorted({a[0] for a in ANSWERS} | {c[0] for c in CLARIFIED}):
        path = transcript(prefix)
        cache[prefix] = ask_calls(path) if path else None
    for prefix, labels, answered, asked in ANSWERS:
        calls = cache[prefix]
        if calls is None:
            check(False, f"{prefix} {labels[0][:40]}", "transcript not found (moved or expired)")
            continue
        hit = [c for c in calls if all(f'="{label}"' in (c["answer"] or "") for label in labels)]
        seen = f"asked {hit[0]['asked_at']}, answered {hit[0]['answered_at']}" if hit else "no call carries these labels"
        ok = bool(hit) and (hit[0]["answered_at"] or "").startswith(answered) and (hit[0]["asked_at"] or "").startswith(asked)
        check(ok, f"{prefix}: {' | '.join(label[:38] for label in labels)}", seen)
    for prefix, asked, answered in CLARIFIED:
        calls = cache[prefix]
        hit = [c for c in (calls or []) if (c["asked_at"] or "").startswith(asked)]
        ok = bool(hit) and (hit[0]["answered_at"] or "").startswith(answered) and "The user wants to clarify these questions." in (hit[0]["answer"] or "")
        check(ok, f"{prefix}: the dialog asked {asked}Z was sent back to clarify", f"answered {hit[0]['answered_at'] if hit else None}" if calls is not None else "transcript not found")
    for prefix, stamp, fragment in TYPED:
        path = transcript(prefix)
        turns = typed_turns(path) if path else []
        hit = [t for t, text in turns if t.startswith(stamp) and fragment in text]
        check(bool(hit), f"{prefix}: the owner wrote {fragment[:60]!r}", hit[0] if hit else ("transcript not found" if path is None else "not at that time"))


# --- The host: the trio's environments and the parent AGENTS.md (read-only) -------------------------------------------


def host() -> None:
    print("== The trio's environments, its ports, and the juniper-ml primary (read in place, read-only)")
    for env, (interp, obs, sc) in PLAIN_ENVS.items():
        code = "import importlib.metadata as m, json; print(json.dumps({p: m.version(p) for p in ('juniper-observability', 'juniper-service-core')}))"
        out = subprocess.run([str(CONDA_ENVS / env / interp), "-I", "-B", "-c", code], capture_output=True, text=True, check=False)
        got = json.loads(out.stdout) if out.returncode == 0 else {}
        check(got == {"juniper-observability": obs, "juniper-service-core": sc}, f"{env} ({interp})", json.dumps(got) if got else out.stderr.strip()[:200])
    site = CONDA_ENVS / "JuniperCascor1" / "lib" / "python3.14" / "site-packages"
    for dist, pkg in (("juniper_observability", "juniper-observability"), ("juniper_service_core", "juniper-service-core")):
        infos = sorted(site.glob(f"{dist}-*.dist-info/direct_url.json"))
        data = json.loads(infos[0].read_text(encoding="utf-8")) if len(infos) == 1 else {}
        editable = bool(data.get("dir_info", {}).get("editable"))
        check(editable and data.get("url", "").endswith(f"/juniper-ml/{pkg}"), f"JuniperCascor1 {pkg} is an editable install of the juniper-ml primary", f"{[p.parent.name for p in infos]} editable={editable}")
    head = (ML_PRIMARY / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    commit = head
    if head.startswith("ref: "):
        ref = head[5:]
        loose = ML_PRIMARY / ".git" / ref
        packed = ML_PRIMARY / ".git" / "packed-refs"
        if loose.exists():
            commit = loose.read_text(encoding="utf-8").strip()
        elif packed.exists():
            commit = next((line.split()[0] for line in packed.read_text(encoding="utf-8").split("\n") if line.endswith(" " + ref)), head)
    NOTES.append(f"the juniper-ml primary, which JuniperCascor1 imports: {head} at {commit[:8]}")
    print(f"  INFO  the juniper-ml primary's .git/HEAD: {head} at {commit[:8]}")
    for pkg, module, version in (("juniper-observability", "juniper_observability", "0.4.2"), ("juniper-service-core", "juniper_service_core", "0.7.2")):
        version_file = ML_PRIMARY / pkg / module / "_version.py"
        found = re.search(r'__version__\s*=\s*"([^"]+)"', version_file.read_text(encoding="utf-8")) if version_file.exists() else None
        check(bool(found) and found.group(1) == version, f"the primary's {pkg} _version.py reads {version} (pip's metadata still says the install-time version)", found.group(1) if found else "absent")
    out = subprocess.run(["ss", "-ltnH"], capture_output=True, text=True, check=False)
    listening = sorted({int(m.group(1)) for m in re.finditer(r":(\d+)\s", out.stdout)} & set(TRIO_PORTS))
    check(out.returncode == 0 and not listening, "the trio's ports 8101, 8202 and 8051 are closed (ss -ltnH)", f"listening: {listening or 'none'}")
    print("== The parent Juniper/AGENTS.md (unversioned; edited again on 2026-11-15, ruling 3 of 2026-11-15)")
    parent = JUNIPER / "AGENTS.md"
    raw = parent.read_bytes()
    text = raw.decode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    mtime = datetime.fromtimestamp(parent.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    check("**The meta-package: juniper-ml 0.11.5**" in text and "juniper-observability 0.4.2" in text, "the paragraph names juniper-ml 0.11.5 and observability 0.4.2", f"sha256 {digest[:16]}, modified {mtime}")
    check(digest.startswith(PARENT_SHA), "the parent AGENTS.md is the 2026-11-15 edit's result", f"sha256 {digest[:16]}, modified {mtime}")
    missing = [s for s in PARENT_ADDED if s not in text]
    check(not missing and PARENT_REMOVED not in text, "the 2026-11-15 edit's passages are in place", f"{len(PARENT_ADDED) - len(missing)} of {len(PARENT_ADDED)} added; removed sentence {'absent' if PARENT_REMOVED not in text else 'STILL PRESENT'}")


def review_pass() -> None:
    print("== Added with the two reviews' pass: ancestry, the primary's code and reflog, the backup, cited lines, the v2 draft")
    for repo, commit, tag in ANCESTRY:
        cmp = gh_json("api", f"repos/{OWNER}/{repo}/compare/{commit}...{tag}")
        check(cmp["behind_by"] == 0 and cmp["status"] in ("ahead", "identical"), f"{repo} {commit} is an ancestor of {tag}", f"{cmp['status']}, ahead {cmp['ahead_by']}, behind {cmp['behind_by']}")
    for tag, path, wanted in UNRELEASED:
        out = subprocess.run(["git", "-C", str(_REPO), "log", "--format=%h %s", f"{tag}..{PRIMARY_COMMIT}", "--", path], capture_output=True, text=True, check=False)
        prs = sorted(set(re.findall(r"\(#(\d+)\)", out.stdout)), key=int)
        got = [f"#{n}" for n in prs]
        check(out.returncode == 0 and got == wanted, f"{path} commits in {tag}..{PRIMARY_COMMIT}", f"{len(out.stdout.splitlines())} commits, PRs {got}")
    reflog = (ML_PRIMARY / ".git" / "logs" / "HEAD").read_text(encoding="utf-8").split("\n")
    since = []
    cutoff = datetime.strptime(RULING7_AT, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    for entry in reflog:
        head, _, message = entry.partition("\t")
        parts = head.split()
        if len(parts) >= 4 and parts[-2].isdigit() and int(parts[-2]) >= cutoff:
            since.append((parts[0][:8], parts[1][:8], message.strip()))
    found = [pair for pair in PULLS_SINCE_RULING7 if any((old, new) == pair and "Fast-forward" in msg for old, new, msg in since)]
    check(found == PULLS_SINCE_RULING7, "the primary's reflog holds the six fast-forwards since ruling 7 of 2026-11-13", f"{len(found)} of 6; {len(since)} entries since {RULING7_AT}")
    for old, new, msg in since:
        if (old, new) not in PULLS_SINCE_RULING7:
            print(f"  INFO  a later reflog entry: {old} -> {new} {msg[:60]}")
    backup = ML_PRIMARY.joinpath(*PARENT_BACKUP)
    digest = hashlib.sha256(backup.read_bytes()).hexdigest() if backup.exists() else "absent"
    check(digest.startswith(PARENT_BACKUP_SHA), "the parent AGENTS.md's prior copy in the primary's tmp/", f"sha256 {digest[:16]}")
    for parts, prefix in PARENT_PAIR.items():
        copy = ML_PRIMARY.joinpath(*parts)
        digest = hashlib.sha256(copy.read_bytes()).hexdigest() if copy.exists() else "absent"
        check(digest.startswith(prefix), f"the 2026-11-15 edit's copy {parts[-1]}", f"sha256 {digest[:16]}")
    for repo, path, ref, line, fragments in MORE_LINES:
        text = line_of(repo, path, line, ref).strip()
        check(all(f in text for f in fragments), f"{repo}:{path}:{line} at {ref}", text[:150])
    pin = line_of("juniper-deploy", "docker-compose.yml", 598).strip()
    state = "0.8.0 (unmoved)" if pin.endswith(":0.8.0") else ("0.8.1 (moved)" if pin.endswith(":0.8.1") else "NEITHER")
    check(state != "NEITHER", "juniper-deploy's recurrence pin (state that MOVES: 0.8.0, or 0.8.1)", state)
    NOTES.append(f"juniper-deploy's recurrence pin: {state}")
    v2 = gh_raw("juniper-ml", V2_PATH).split("\n")
    stale = [n for n, fragment in V2_STALE if fragment in v2[n - 1]]
    check(len(stale) == len(V2_STALE), "the v2 draft's stale lines this record lists", f"{len(stale)} of {len(V2_STALE)}: {stale}")
    section = gh_raw("juniper-canopy", "CHANGELOG.md", "v0.10.0")
    start = section.find("## [0.10.0]")
    end = section.find("\n## [", start + 5)
    body = section[start:end]
    hits = [w for w in ("#685", "APD-ECO-009", "APD-ECO-010", "APD-ECO-011", "APD-ECO-012") if w in body] + (["O3"] if re.search(r"\bO3\b", body) else [])
    check(start >= 0 and not hits, "canopy v0.10.0's [0.10.0] names no P3-06 item (#685, O3, APD-ECO-009..012)", f"{body.count(chr(10))} lines; hits {hits}")
    src = gh_raw("juniper-cascor", "src/main.py", "v0.14.0")
    k = src.find("def _resolve_sentry_dsn")
    lines = src[k:].split("\n")
    body = [lines[0]]
    for line in lines[1:]:
        if line and not line[0].isspace():
            break
        body.append(line)
    fn = "\n".join(body)
    check(k >= 0 and ("getenv" in fn or "environ" in fn) and not any(w in fn for w in ("_FILE", "read_text", "open(")), "cascor v0.14.0 reads its Sentry DSN from the environment only", f"{len(fn)} characters")
    out = subprocess.run(["ss", "-ltnH"], capture_output=True, text=True, check=False)
    legs = sorted({int(m.group(1)) for m in re.finditer(r":(\d+)\s", out.stdout)} & {8052, 8053, 8058, 8059})
    print(f"  INFO  canopy E2E legs listening (state that moves; their DSNs unread): {legs}")


def images_and_wheels() -> None:
    print("== The two images' revision labels, and cascor 0.13.0's PyPI files against TestPyPI's, member by member")
    for repo, (tag, revision) in {"juniper-cascor": ("0.14.0", "bf6f0108"), "juniper-canopy": ("0.10.0", "57d90dec")}.items():
        token = json.loads(http(f"https://ghcr.io/token?scope=repository:{OWNER}/{repo}:pull")[1])["token"]
        auth = {"Authorization": f"Bearer {token}"}
        accept = "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"
        with urllib.request.urlopen(urllib.request.Request(f"https://ghcr.io/v2/{OWNER}/{repo}/manifests/{tag}", headers={**auth, "Accept": accept}), timeout=30) as resp:  # nosec B310 -- fixed https registry URL
            digest = resp.headers.get("Docker-Content-Digest")
            index = json.load(resp)
        labels = set()
        for manifest in index.get("manifests", []):
            if manifest.get("platform", {}).get("architecture") in (None, "unknown"):
                continue
            accept_one = "application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"
            with urllib.request.urlopen(urllib.request.Request(f"https://ghcr.io/v2/{OWNER}/{repo}/manifests/{manifest['digest']}", headers={**auth, "Accept": accept_one}), timeout=30) as resp:  # nosec B310
                config = json.load(resp)["config"]["digest"]
            with urllib.request.urlopen(urllib.request.Request(f"https://ghcr.io/v2/{OWNER}/{repo}/blobs/{config}", headers=auth), timeout=60) as resp:  # nosec B310
                labels.add((json.load(resp).get("config", {}).get("Labels") or {}).get("org.opencontainers.image.revision", "")[:8])
        check(labels == {revision}, f"GHCR {repo}:{tag} index and revision label", f"{digest[:19]}..., revisions {sorted(labels)}")
    files = {}
    for host in ("pypi.org", "test.pypi.org"):
        files[host] = {u["filename"]: u["url"] for u in http_json(f"https://{host}/pypi/juniper-cascor/0.13.0/json")["urls"]}
    for name in sorted(files["pypi.org"]):
        members = []
        for host in ("pypi.org", "test.pypi.org"):
            blob = http(files[host][name])[1]
            got = {}
            if name.endswith(".whl"):
                with zipfile.ZipFile(io.BytesIO(blob)) as archive:
                    got = {i.filename: hashlib.sha256(archive.read(i)).hexdigest() for i in archive.infolist()}
            else:
                with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
                    got = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive.getmembers() if m.isfile()}
            members.append((hashlib.sha256(blob).hexdigest(), got))
        (sha_a, a), (sha_b, b) = members
        differ = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        check(not differ and bool(a), f"cascor 0.13.0 {name}: PyPI's members equal TestPyPI's", f"file sha256 {'same' if sha_a == sha_b else 'differs'}; {len(a)} members, {len(differ)} differ")


def archive() -> None:
    print("== The reviews' archive and its tallies (local files)")
    root = _REPO / REVIEWS
    names = sorted(p.name for p in root.iterdir()) if root.is_dir() else []
    check(len(names) == 14 and "README.md" in names, f"{REVIEWS}/ holds 14 files", f"{len(names)} files")
    script = _REPO / "util" / "ad-hoc" / "2026-11-15_archive_r_obs_sc_2_reviews.py"
    out = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True, check=False, cwd=_REPO)
    check(out.returncode == 0, "util/ad-hoc/2026-11-15_archive_r_obs_sc_2_reviews.py --check", f"exit {out.returncode}; {out.stdout.count('PASS')} PASS")
    name, sha = FIXPASS
    digest = hashlib.sha256((root / name).read_bytes()).hexdigest() if (root / name).exists() else "absent"
    check(digest.startswith(sha), f"{name} (a verbatim copy of tmp/lps/fixpass_r1.md)", f"sha256 {digest[:16]}")
    for name, pattern, wanted in TALLIES:
        text = (root / name).read_text(encoding="utf-8")
        got = {}
        for match in re.finditer(pattern, text, flags=re.M):
            got[match.group(1)] = got.get(match.group(1), 0) + 1
        if name.endswith("review-b_report.md"):
            first, last = text.find("29. **NIT**"), text.find("\n30. ")
            nits = text[first:last]
            got["NIT"] = len(re.findall(r"^    - ", nits, flags=re.M))
            wanted = {**wanted, "NIT": 9}
        check(got == wanted, f"{name} tally", json.dumps(got, sort_keys=True))
    text = (root / "notes-round-1_report.md").read_text(encoding="utf-8")
    for heading, wanted in NOTES_R1:
        start = text.find(heading)
        nxt = text.find("\n## ", start + 5)
        got = {}
        for match in re.finditer(r"^\d+\. \*\*(BLOCKER|MAJOR|MINOR|NIT)", text[start:nxt], flags=re.M):
            got[match.group(1)] = got.get(match.group(1), 0) + 1
        check(got == wanted, f"notes-round-1_report.md, {heading[3:]}", json.dumps(got, sort_keys=True))
    r2 = (root / "notes-round-2_report.md").read_text(encoding="utf-8")
    brief = (root / "notes-round-2_brief.md").read_text(encoding="utf-8")
    check("24 are RESOLVED" in r2 and "canopy 15 (the category order) was left as is" in brief, "the release bodies' round 2: 24 of 25 resolved; canopy 15 left as is", "both phrases present")


def main() -> int:
    for step in (prs, releases, published_run, gated_runs, indexes, floors_and_pins, register, sources, answers, host, review_pass, images_and_wheels, archive):
        try:
            step()
        except Exception as exc:  # noqa: BLE001 -- report and carry on; the exit code still fails
            check(False, step.__name__, f"{type(exc).__name__}: {exc}")
    print("\nState that moves: " + "; ".join(NOTES))
    print(f"\n{len(FAILS)} FAIL(s)" + (": " + "; ".join(FAILS) if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
