# Re-land #2045's front-matter reformat, on its own and with its continuation fixed

## Why this exists separately

#2045 reported 669 files and +432,258/-633. Measured against current `main` rather than against its
stale merge-base, it changed **exactly one**: this document's front matter. All 615 files it listed
as `added` were already on `main`, and 53 of its 54 `modified` files were byte-identical to `main`
— including `.github/workflows/ci.yml`, `util/safe_merge.py` and all seven test files. Measured with
`util/ad-hoc/2026-09-23_pr2045_net_effect.py`; #2045 is closed with that evidence on it.

The reformat itself is a real readability gain, so it is re-landed here where it can be reviewed as
what it is. The **Companions** list is the clearest case: five links previously ran together as bare
lines with no structure.

## One correction to the original

#2045 placed `Verbatim reports:` at **column 0**, directly beneath a list item. Markdown treats that
as a **lazy continuation** — it renders as part of the bullet, so the output looks correct while the
source says otherwise, and the next editor to insert a blank line above it silently breaks the list.
Indented to two spaces here, which is what the renderer was inferring anyway.

## Changes

**Changed**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
(front matter only — 16 insertions, 18 deletions; no prose, no section, no tagged block touched).

**Added**: `util/ad-hoc/2026-09-24_reformat_design_frontmatter.py`,
`util/ad-hoc/2026-09-23_pr2045_net_effect.py` (the triage instrument that measured #2045).

## Verification

- `markdownlint 0.42.0` (the pinned hook version) — exit 0.
- `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check`: **0 staged, 13 already current** — no
  tagged block is touched, so no artifact changes.
- Edit script is idempotent: a second run reports `ALREADY applied` and writes nothing. It refuses
  any edit whose `old` is a substring of its `new`, and scans for over-width lines before writing.

## Requirements

References JR-DEP-SEC-005.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
