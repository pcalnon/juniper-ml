#!/usr/bin/env python3
"""Exact-cap boundaries for the release-train archive and proposal-body limits.

``ceremony.plan_ceremony`` halts ``archive-too-large`` only when the base64 archive is
strictly longer than ``archive_b64_max()`` (``encoded_len > cap``). ``propose._fitted_pr_body``
keeps the notes draft when the body is at most ``PR_BODY_MAX`` UTF-8 bytes (``<=``), and
``execute_proposal`` refuses only a body strictly over that cap (``>``). The suites next to
these use a far-under archive, a far-over archive, a 70 KB draft, and ``PR_BODY_MAX + 1``.
None of those fail if ``>`` becomes ``>=`` or ``<=`` becomes ``<``.

An archive that exactly fills the one-request cap must still be planned: the 2026-10-26
measurement raised the cap because notes near the old ceiling were being halted. A proposal
body that exactly fills GitHub's 65,536-byte limit must still inline its notes and still
open. One byte over either cap takes the refusal path, and the refusal happens before any
branch or commit.

Hermetic: the notes renderer and every GitHub write are injected. No network, no gh, no git.

Run: python3 -m unittest -v tests/test_release_train_exact_caps.py
"""

from __future__ import annotations

import base64
import os
import sys
import textwrap
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "util" / "release_train"))

import ceremony as ce  # noqa: E402
import detect as d  # noqa: E402
import propose as pr  # noqa: E402

_DATE = "2026-10-21"

_CHANGELOG = textwrap.dedent("""\
    # Changelog

    ## [Unreleased]

    ## [0.5.0] - 2026-07-17

    ### Added

    - A new capability.

    ## [0.4.0] - 2026-06-01

    ### Added

    - The prior thing.
    """)


def _entry() -> d.PackageEntry:
    return d.PackageEntry(
        pypi_name="juniper-service-core",
        repo="juniper-ml",
        path="juniper-service-core/",
        version_source="static",
        tag_pattern="juniper-service-core-v*",
        archive_name="RELEASE_NOTES_juniper-service-core_v{version}.md",
        trigger={"now": "release", "target": "release"},
        verify={"now": "strict", "target": "strict"},
        depends_on=[],
        ship_paths=["juniper-service-core/juniper_service_core/"],
        exclude_paths=[],
    )


def _sources() -> ce.CeremonySources:
    return ce.CeremonySources(
        pypi_json=lambda _name: {"info": {"version": "0.4.0"}},
        read_file=lambda _entry, filename: _CHANGELOG if filename.endswith("CHANGELOG.md") else None,
        main_ci_conclusion=lambda _repo, _workflow: "success",
        list_open_prs=lambda _repo: [],
        release_exists=lambda _repo, _tag: False,
        archive_on_main=lambda _relpath: False,
        publish_run_status=lambda _repo, _tag: None,
        open_archive_pr=None,
        enable_automerge=None,
        create_release=None,
        upsert_halt_issue=None,
    )


def _plan() -> ce.CeremonyPlan:
    return ce.plan_ceremony(_entry(), {"pypi_name": "juniper-service-core", "repo": "juniper-ml", "released_version": "0.4.0", "declared_version": "0.5.0", "classification": "BUMPED_NOT_RELEASED"}, _sources(), REPO_ROOT, REPO_ROOT.parent, "2026-07-17")


def _encoded_len(content: str) -> int:
    return len(base64.b64encode(content.encode("utf-8")))


class ArchiveExactCapTest(unittest.TestCase):
    """The signed-commit cap admits an archive whose base64 length equals the cap."""

    def test_an_archive_that_exactly_fills_the_cap_is_planned_and_one_byte_over_halts(self) -> None:
        content = "A" * 300  # ASCII, so the base64 length is a pure function of len(content)
        encoded = _encoded_len(content)
        self.assertGreater(encoded, 1)

        with mock.patch.object(ce.notes_render, "render_notes", return_value=content):
            with mock.patch.dict(os.environ, {ce.ARCHIVE_B64_MAX_ENV: str(encoded)}):
                planned = _plan()
            with mock.patch.dict(os.environ, {ce.ARCHIVE_B64_MAX_ENV: str(encoded - 1)}):
                halted = _plan()

        self.assertEqual(planned.archive_content, content)
        self.assertEqual(_encoded_len(planned.archive_content), encoded)
        self.assertEqual(planned.state, "CEREMONY_PLANNED")
        self.assertFalse(planned.halted)
        self.assertEqual(planned.action_kinds[0], "open_archive_pr")

        self.assertEqual(halted.state, "HALTED")
        self.assertTrue(halted.halted)
        self.assertEqual(halted.issue["reason_key"], "archive-too-large")
        self.assertIn("nothing was written", halted.halt_reason)
        self.assertEqual(halted.action_kinds, ["halt_issue"])
        self.assertEqual(_encoded_len(halted.archive_content), encoded)


class ProposalBodyExactCapTest(unittest.TestCase):
    """GitHub's 65,536-byte body limit, measured at the byte that crosses it."""

    def _prop(self, notes: str) -> pr.Proposal:
        prop = pr.Proposal(pypi_name="juniper-thing", repo="juniper-ml", from_version="0.4.0", to_version="0.5.0", bump="minor", branch="release/juniper-thing-v0.5.0")
        prop.edits.append(pr.FileEdit(path="pyproject.toml", old_text="a", new_text="b"))
        prop.notes_draft = notes
        return prop

    def _pad(self) -> int:
        """How many ASCII note bytes make the inlined body exactly ``PR_BODY_MAX``."""
        empty = pr._fitted_pr_body(self._prop(""), _DATE)
        self.assertIn("<details><summary>Drafted release notes</summary>", empty)
        pad = pr.PR_BODY_MAX - pr._body_size(empty)
        self.assertGreater(pad, 0)
        return pad

    def test_a_body_that_exactly_fills_the_limit_keeps_the_notes(self) -> None:
        notes = "N" * self._pad()
        body = pr._fitted_pr_body(self._prop(notes), _DATE)
        self.assertEqual(pr._body_size(body), pr.PR_BODY_MAX)
        self.assertIn(notes, body)
        self.assertNotIn("Not inlined", body)

    def test_one_byte_over_the_limit_drops_the_notes(self) -> None:
        notes = "N" * (self._pad() + 1)
        prop = self._prop(notes)
        inlined = pr._pr_body(prop, _DATE, inline_notes=True)
        self.assertEqual(pr._body_size(inlined), pr.PR_BODY_MAX + 1)
        fitted = pr._fitted_pr_body(prop, _DATE)
        self.assertLessEqual(pr._body_size(fitted), pr.PR_BODY_MAX)
        self.assertIn("Not inlined", fitted)
        self.assertNotIn(notes, fitted)

    def test_execute_opens_a_body_that_exactly_fills_the_limit(self) -> None:
        calls: list = []
        sources = pr.ProposeSources(
            read_file=lambda _entry, _filename: None,
            list_open_prs=lambda _repo: [],
            resolve_ref_sha=lambda repo, ref: calls.append(("resolve", repo, ref)) or "sha",
            create_branch=lambda repo, branch, sha: calls.append(("branch", repo, branch)),
            create_signed_commit=lambda repo, branch, message, additions, expected_head_oid: calls.append(("commit", repo, branch)) or "c0ffee",
            open_pr=lambda repo, base, head, title, body: calls.append(("pr", body)) or "https://example.invalid/pull/1",
        )
        prop = self._prop("- small\n")
        prop.pr_body = "x" * pr.PR_BODY_MAX
        url = pr.execute_proposal(prop, sources, "main")
        self.assertEqual(url, "https://example.invalid/pull/1")
        self.assertEqual([call[0] for call in calls], ["resolve", "branch", "commit", "pr"])
        self.assertEqual(pr._body_size(calls[-1][1]), pr.PR_BODY_MAX)

    def test_execute_refuses_one_byte_over_before_any_write(self) -> None:
        calls: list = []
        sources = pr.ProposeSources(
            read_file=lambda _entry, _filename: None,
            list_open_prs=lambda _repo: [],
            resolve_ref_sha=lambda repo, ref: calls.append(("resolve",)) or "sha",
            create_branch=lambda repo, branch, sha: calls.append(("branch",)),
            create_signed_commit=lambda *args: calls.append(("commit",)) or "c0ffee",
            open_pr=lambda *args: calls.append(("pr",)) or "https://example.invalid/pull/1",
        )
        prop = self._prop("- small\n")
        prop.pr_body = "x" * (pr.PR_BODY_MAX + 1)
        with self.assertRaises(pr.SourceError) as ctx:
            pr.execute_proposal(prop, sources, "main")
        self.assertIn("nothing was written", str(ctx.exception))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
