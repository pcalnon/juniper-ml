#!/usr/bin/env python3
"""One-shot edit: add the ledger-screening suite to tests/test_soak_probe_evidence.py.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-10

Single-use. Kept under util/ad-hoc/ rather than /tmp/ per the repo's script-placement
rule: /tmp/ is reaped when the session ends, and two scripts from the requirements
effort were lost that way.
"""

from __future__ import annotations

import pathlib

TARGET = pathlib.Path(__file__).resolve().parents[3] / "tests" / "test_soak_probe_evidence.py"

ANCHOR = "class ParseHonesty(unittest.TestCase):"

NEW = '''class LedgerIsScreened(unittest.TestCase):
    """Item F' of the 09-09 handoff: the ledger was an UNSCREENED answer sheet.

    ``reports/soak/pointer_follow_soak.jsonl`` records each observation's
    ``pointer``, its scored ``outcome`` and a ``note`` restating the answer in
    prose. The screen checked ``ANSWER_KEY='conf/soak_probes.json'`` and
    ``PROTOCOL_DOC='POINTER-FOLLOW-SOAK-LEDGER'`` (the NOTES filename); the
    ledger's own path matched neither, so an unscoped ``grep -rn`` that returned
    a prior record scored clean.

    Validated against the real corpus 2026-09-10: 8 of the 43 valid runs touched
    the ledger, exactly ONE read its contents
    (``P18-health-interval-non-positive``, 2026-08-22T21:41:09Z). Two independent
    implementations -- this screen and
    ``util/ad-hoc/2026-09-10_soak_stopping_rule/ledger_exposure_probe.py`` --
    agree on 1 / 7 / 8.
    """

    LEDGER_RECORD = (
        '{"obs_id": "a44e03cb-151b-4f9e-a7b6-a5c480d3d2fc", '
        '"probe_id": "P18-health-interval-non-positive", "outcome": "follow", '
        '"note": "RETRIEVED docs/REFERENCE.md via a directory-scoped search."}'
    )

    def test_reading_a_ledger_record_is_a_content_read(self) -> None:
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [tool_use("Grep", pattern="health_interval"), tool_result(self.LEDGER_RECORD)],
            )
            out = mod.scan(path)
        self.assertTrue(out["ledger_content_read"])
        self.assertTrue(out["ledger_touched"])
        self.assertEqual(out["ledger_filename_hits"], 0)

    def test_seeing_only_the_filename_is_not_a_content_read(self) -> None:
        """SEVEN of the eight. A porcelain status line, a diff stat, an `ls -t`.

        Folding these into the content count would overstate the exposure 8x on
        the number that feeds owner decision 8 -- whether the leak invalidates its
        runs -- which changes the DENOMINATOR of every rate in the arc.
        """
        for listing in (
            " M reports/soak/pointer_follow_soak.jsonl",
            "reports/soak/pointer_follow_soak.jsonl | 3 +++",
            "reports/soak/pointer_follow_soak.jsonl",
        ):
            with self.subTest(listing=listing), TemporaryDirectory() as t:
                path = write_transcript(
                    Path(t), [tool_use("Bash", command="git status"), tool_result(listing)]
                )
                out = mod.scan(path)
                self.assertFalse(out["ledger_content_read"], listing)
                self.assertTrue(out["ledger_touched"], listing)

    def test_a_clean_run_touches_the_ledger_not_at_all(self) -> None:
        """Negative control. If ``ledger_touched`` were always true the two tests
        above would still pass and the screen would flag every run."""
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="docs/REFERENCE.md")])
            out = mod.scan(path)
        self.assertFalse(out["ledger_touched"])
        self.assertFalse(out["ledger_content_read"])
        self.assertEqual(out["ledger_content_hits"], 0)
        self.assertEqual(out["ledger_filename_hits"], 0)

    def test_escaped_record_keys_still_count(self) -> None:
        """The transcript is itself JSON, so a record's key arrives backslash-escaped.
        The binder had to make this same correction; a screen that missed it would
        report every real content read as clean."""
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [
                    tool_use("Bash", command="cat reports/soak/pointer_follow_soak.jsonl"),
                    tool_result('{\\\\"obs_id\\\\": \\\\"x\\\\", \\\\"outcome\\\\": \\\\"follow\\\\"}'),
                ],
            )
            out = mod.scan(path)
        self.assertTrue(out["ledger_content_read"])

    def test_the_ledger_flag_is_separate_from_contaminated(self) -> None:
        """NOT folded into ``contaminated``. Whether a ledger read invalidates its
        run is owner decision 8 and is unsettled; rolling it in would decide it by
        implementation, and would silently change every prior contamination
        verdict."""
        with TemporaryDirectory() as t:
            path = write_transcript(
                Path(t),
                [tool_use("Grep", pattern="x"), tool_result(self.LEDGER_RECORD)],
            )
            out = mod.scan(path)
        self.assertTrue(out["ledger_content_read"])
        self.assertFalse(out["contaminated"])

    def test_the_answer_key_still_contaminates(self) -> None:
        """The other direction of the same separation: adding the ledger must not
        have displaced the marker the screen already had."""
        with TemporaryDirectory() as t:
            path = write_transcript(Path(t), [tool_use("Read", file_path="conf/soak_probes.json")])
            out = mod.scan(path)
        self.assertTrue(out["contaminated"])
        self.assertFalse(out["ledger_touched"])


'''


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    if "class LedgerIsScreened" in src:
        print("already applied")
        return 0
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor not unique in {TARGET} ({src.count(ANCHOR)} occurrences)")
    TARGET.write_text(src.replace(ANCHOR, NEW + ANCHOR), encoding="utf-8")
    print(f"added LedgerIsScreened to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
