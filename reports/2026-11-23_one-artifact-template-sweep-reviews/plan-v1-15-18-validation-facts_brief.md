# Lens A: the fact re-probe

Read `tmp/v1_15_18/val/VALIDATION_BRIEF_COMMON.md` first; it is part of this brief. Your output directory is
`tmp/v1_15_18/val/facts/`.

Your lens: every checkable fact in the draft's added or changed lines, re-derived from its primary source.

- Every PR number, its state, merge time (to the second), merge commit and head commit: from `gh`, not from the record.
- Every review count (BLOCKER/MAJOR/MINOR/NIT), finding id, time window, sha256 prefix, line count, test or mutation count
  and quoted error, from `REVIEW_DISPOSITIONS.md` (and the round report where one exists). A count the record states in
  two places that disagree is a finding.
- Every quoted ruling or option text, character for character, against `REVIEW_DISPOSITIONS.md`'s recorded text (and
  the handoff that also quotes it). Every "Not chosen" option list.
- Every session id, ListAgents name or reference, and every attribution of work to a session.
- Every host-state claim (the primary's branch and commit, the backups' sha256, containers, listening ports, the conda
  environments' versions): re-probe it read-only and give your own `date -u`.
- juniper-observability 0.4.3: the publish run's jobs (`gh run view 45739959764 --repo pcalnon/juniper-ml --json jobs`),
  TestPyPI's and PyPI's files and sha256.
- Every path the draft names that is on juniper-ml `main` (`util/ad-hoc/…`, `notes/…`, `prompts/…`): does it exist under
  that exact name? (Files the PR itself adds are out of your scope.)

Also check the sub-bullets the draft adds under OLD passages: does each describe the passage it sits under, at the
right list depth, without contradicting that passage's own date?
