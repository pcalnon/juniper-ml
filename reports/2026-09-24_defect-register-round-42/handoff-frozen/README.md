# The frozen copies the handoff-validation reports cite

Each validation round of session `2fba4397`'s two handoffs ran against a frozen copy of the handoff,
identified by its sha256, so that the document could keep moving while the lanes read it. The reports
beside this directory (`handoff-2fba4397-round*-*.md` and `handoff-consolidated-round*-*.md`) cite those
copies by their scratch paths, which were on tmpfs, and cite lines as "L<n>" of them. These are the same
bytes, renamed. Match a report to its copy by the sha256 prefix it quotes, or by the scratch path it names.

| File | Scratch path the reports cite | sha256 (prefix) | Cited by |
|---|---|---|---|
| `handoff-2fba4397-r1.md` | `handoff_session_r1_frozen.md` | `1e5db1832f6131a8` | `handoff-2fba4397-round1-*`; `-round2-laneO` (as "R1", by path) |
| `handoff-2fba4397-r2.md` | `handoff_session_r2_frozen.md` | `6822f3ff0402793e` | `handoff-2fba4397-round2-*`, `-round3-laneF` |
| `handoff-2fba4397-r3.md` | `handoff_session_r3_frozen.md` | `c9ef84f352a82857` | `handoff-2fba4397-round3-*` |
| `doc1-at-consolidated-r1.md` | `hc1/doc1_frozen.md` | `c300e249764e45fc` | `handoff-consolidated-round1-laneO`, `handoff-2fba4397-round3-laneP` |
| `doc1-at-consolidated-r2.md` | `hc2/doc1_r2_frozen.md` | `17ef7db5b35f3744` | `handoff-consolidated-round2-laneF`, `-round2-laneO`; `-round3-laneF` (as "document 1", by path) |
| `handoff-consolidated-r1.md` | `hc1/consolidated_r1_frozen.md` | `96c1b58f52fb5377` | `handoff-consolidated-round1-*`, `-round2-laneO` |
| `handoff-consolidated-r2.md` | `hc2/consolidated_r2_frozen.md` | `79c0abb4b7dbdf15` | `handoff-consolidated-round2-*`, `-round3-*` |
| `handoff-consolidated-r3.md` | `hc3/consolidated_r3_frozen.md` | `cab844827349c45f` | `handoff-consolidated-round3-*`, `-round4-*` (as "r3", by path) |
| `handoff-consolidated-r4.md` | `hc4/consolidated_r4_frozen.md` | `6a052d09a1d2db6e` | `handoff-consolidated-round4-*` |
| `doc2-draft-0021z.md` | none: the live file at 00:21Z | `62f9b2bfca40f2e4` | `handoff-2fba4397-round2-laneO` (as "PEER") |

**Where the copies come from.**
- `handoff-2fba4397-*` and `doc1-at-*` are drafts of
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md`
  (called document 1). The shipped document 1 is byte-identical to `doc1-at-consolidated-r2.md`.
- `handoff-consolidated-*` are drafts of
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`.
  The shipped version is later than every copy here: each round's corrections were applied after it.
- `doc2-draft-0021z.md` is a draft of
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`
  (called document 2), written by session `bc31e993`. No file on disk still had it, so
  `util/ad-hoc/2026-09-24_rebuild_round42_doc2_draft_0021z.py` rebuilt it from that session's transcript.
  It replays all 25 of that session's writes to the file, and refuses unless the replay ends at the blob that
  juniper-ml#2097 carries.

**Cited but not copied, because git holds the same bytes.**
- `hc{1,2}/doc2_peer_final_2e4917c2.md` (sha256 `4ebd0143a5ea9c3e`) are document 2 as juniper-ml#2097
  carries it at `2e4917c2`.
- `hc{1,2}/doc3_predecessor_main.md` (`5b9cd399b12b1216`) are
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`
  on `main`.
