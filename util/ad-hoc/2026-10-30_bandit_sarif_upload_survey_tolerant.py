#!/usr/bin/env python3
"""
Run juniper-cascor's Bandit SARIF upload survey on another repository, tallying a run whose job list GitHub
cannot serve as ``unreadable`` instead of aborting the survey.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-30
Status: ad-hoc — investigation (flood-3 record, tenth update: the SARIF rule in five more repositories)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor util/ad-hoc/2026-10-27_bandit_sarif_upload_survey.py (the survey this wraps, unchanged);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§4, §8)

Why this exists
---------------
On 2026-10-30 the survey aborted (exit 2) in all five repositories it was pointed at: GitHub answered
``GET /repos/<repo>/actions/runs/<id>/jobs`` with HTTP 502 for some runs, on every attempt and at any page size,
while the run itself (``GET .../runs/<id>``) loaded. The same runs loaded later, so the 502s were transient,
but they outlasted the survey's four attempts. One such run makes the whole survey unreadable, which is
the right default and the wrong outcome when 198 of 200 runs can be read. This loads the survey from its file,
replaces only ``upload_step`` with a version that returns ``("unreadable", "unreadable")`` on a ``SurveyError``,
and runs its ``main``. An unreadable run is printed in the survey's own tally and is never counted as an
executed upload, so it cannot read as a success.

    python3 -I util/ad-hoc/2026-10-30_bandit_sarif_upload_survey_tolerant.py <path to the cascor survey> --repo pcalnon/<repo> [--limit 200]

Exit status is the survey's: 0 clean, 1 a failed upload or a PR head missing its Bandit check, 2 nothing executed.

Read only the survey's Bandit-check half. Its "no upload step failed" line is blind to a failure behind
``continue-on-error: true``: GitHub's jobs API reports a step's conclusion AFTER ``continue-on-error`` is applied, so
juniper-canopy job 123689681187, whose upload logged ``Path does not exist: reports/security/bandit.sarif``, reads
``success``. The Bandit check that code scanning creates from a landed upload is an effect, and it is the measure that holds.

Runs of record (2026-10-30, ``--limit 200``), PR heads whose upload ran that carry Bandit: juniper-data 102/102
(2 runs unreadable), juniper-data-client 132/132, juniper-cascor-client 120/120 (2 unreadable), juniper-cascor-worker
113/113, juniper-canopy 1/109 (exit 1: 108 heads, 2026-10-16 to 10-29, uploaded nothing, juniper-canopy#780's failure).
"""

import importlib.util
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    spec = importlib.util.spec_from_file_location("bandit_sarif_upload_survey", sys.argv[1])
    survey = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = survey
    spec.loader.exec_module(survey)
    original = survey.upload_step

    def tolerant_upload_step(repo: str, run_id: int) -> tuple[str, str]:
        try:
            return original(repo, run_id)
        except survey.SurveyError as exc:
            print(f"::warning::run {run_id}: job list unreadable -- {str(exc)[:160]}", file=sys.stderr)
            return "unreadable", "unreadable"

    survey.upload_step = tolerant_upload_step
    return survey.main(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
