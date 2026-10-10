# Round 3 — Lane A (re-probe the round-2 corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-3 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round3-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- Instrument:
  - `gh api` REST across the nine repositories, plus gitleaks-action at its pinned SHA.
  - PyPI JSON, and local reads at `cf711cf4`.
  - A read-only `ls` of `JuniperCascor1`.
  - One check of the requests 2.33.1 header validators, with a fake token and no network.
  - No repository script or test ran.
  - measured_at 2026-10-05T10:31Z–10:51Z, against plan sha256 prefix `68ba9e62dbc6c803`.
- Entry point: the added and changed lines of the v1.1→v1.2 diff.
- Sample: 42 claims re-derived. Nine mismatch: 2 MAJOR, 3 MINOR, 4 NIT.

<!-- markdownlint-disable MD013 -->

## Findings

| ID | Severity | Plan location (v1.2) | Plan says | Re-derived (command / file:line → result) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R3A-01 | MAJOR | §5 L546 (see L532, L547) | R-RECURRENCE-SEC is "a patch for W1.14". It carries "the 502 key-relay fix" and is ready when "W1.14 merged and validated" | `compare/juniper-recurrence-v0.5.0...main` shows 21 commits, including #172 `feat(snapshots)` (new routes) and #190 `feat(cli,api)` (a new `TrainResponse` field). `[Unreleased]` holds only Added and Changed. `util/release_train/detect.py:828-838` therefore proposes MINOR, i.e. **0.6.0**, the version P12 reserves for Phase 1 (P12 plan L509, L574). A cut from `main` (L532) is also "the first recurrence release carrying P12 W1.x" (L547), and it would skip that row's cap-PR gates | Owner ruling in §6 A1, one of: (a) 0.5.1 from the v0.5.0 tag plus W1.14, as an exception to L532; (b) 0.6.0 from `main`, merged into the P12-chain row with its gates |
| R3A-02 | MAJOR | §4 Wave 2 L500 | "W5.1 review → R5 → Phase 1 … → M0" | In the P12 plan, R5 gates only W5.4 (L752 "Gates", L676). M0 is P0's milestone, and only W0.1's service-core half is still open for it (L508). The handoff (L13) and the plan's own §2 (L223) say Phase 1 is next. As written, Phase 1 stalls behind an owner ruling | "M0 (after W0.1's service-core half) · Phase 1 → M1 · W5.1 review → R5 → W5.4" |
| R3A-03 | MINOR | Overview L77; S0.11 L429 | The key "reaches every `/v1/train` caller and the service log"; the fix adds "a route test" | `map_data_error` is also reached from `routers/predict.py:60-62` (the dataset form) and `routers/crossval.py:74-76`. Both log `exc` at WARNING | Name all three routes. Test `map_data_error` itself |
| R3A-04 | MINOR | §7.2 L719 | "the experiment launcher refuses `JuniperCascor1` until W0.1's service-core half lands" | The only preflight call is inside `recurrence_up()`: `experiment_stack.bash:815-858` (call at L832), and `isolated_stack.bash:434-473`, which runs only with `--with-recurrence` (L563). The isolated stack's override is `JUNIPER_E2E_SKIP_ENV_PREFLIGHT`. The `--cascor` runs in §7.2 are unaffected | "…refuses **recurrence legs** on `JuniperCascor1`…", naming both override variables |
| R3A-05 | MINOR | XC-FLEET L318 | canopy#701: "Re-run CI. Content matches `main`" | canopy#701 is now `dirty`. It and the merged canopy#702 both edit `CHANGELOG.md`, and `pull_request` CI does not run on a conflicted PR | "Rebase (resolve `CHANGELOG.md`) or close" |
| R3A-06 | NIT | L77; L326; L888 | The leak needs a "whitespace-padded" key | Under requests 2.33.1, leading whitespace or a trailing `\n` raises `InvalidHeader`, whose message contains the key; trailing spaces pass. `get_secret` strips only the `_FILE` form | "an env-var key with leading whitespace or a line break" |
| R3A-07 | NIT | L44; §10 L842 | "v1.3.0 on `main` since ml#2130" … "adds F-S10 … W1.14" | The file's commit history shows F-S10 and W1.14 arrived in ml#2151 (`a0a120d5`, 22:31Z) with the label unchanged | Credit ml#2151 |
| R3A-08 | NIT | §6 Group B L638-642 | P12's rulings "in the order of" its handoff, starting with DC-0.6; "R1" | The handoff (L32) names none of DC-0.6, O8, O12 or P4-Q6, and it says "R1 optional" | "DC-0.6, then the handoff's order"; keep "optional" |
| R3A-09 | NIT | L1079 | ml#2151 merged "overnight" | It merged at 2026-10-04T22:31:34Z, inside round 2's freeze window | "during round 2" |

## Checked and holds (short)

- **Item 1.**
  - F-S10 is at L146 and W1.14 at L401 of the P12 plan on `main`.
  - `_common.py:55` relays `{exc}` in a 502. `training.py:58-60` logs it and maps it.
  - The client wraps `RequestException` as "Request failed: …" (`client.py:349-350`).
  - W1.14 is effort S and needs owner acceptance. No key was printed.
- **Item 2.**
  - ml#2151 merged at 22:31:34Z and changed 7 files.
  - ml#2154 is open and clean, by `juniper-release-train[bot]`, opened 08:32:53Z. It had no auto-merge arm at 10:49Z, which is P9-14's datum.
  - There are 42 drafts, all from `cursor[bot]`: ml 28, canopy 8, cascor 2, worker 2, deploy 2.
  - The newest PyPI upload and the newest Release are both juniper-data 0.16.0, on 09-24.
  - The P12 handoff is on `main` and supports §2 and XC-P12, including item 3.
- **Item 3.**
  - The command matches L13 of ml#2134's body.
  - `--backup-id` is the script's real, required flag (L47-80).
  - `PRIMARY` is hard-coded, so syncing first is required.
  - Phase C steps 1–7 hold no Procedure B, so id 2 stands.
  - The watchdog's default `""` (L313) supports A2's N-1.
- **Item 4.** All six DSN names, and "`load_dotenv` re-injects", match L126.
- **Item 5.** The L86 quote is verbatim; its subject is P8's "Round 2". The three-agent cap is at L95 of `EX/extraction-P8-harness.md`.
- **Item 6.** All 28 paths exist (two only on `main`), and so does `pr2114.md`.
- **XC-LEAKS.**
  - Four configs have zero rules, and cascor and cascor-client extend the defaults.
  - juniper-recurrence has no gitleaks at all.
  - juniper-deploy has secret scanning and push protection off. Non-provider patterns are off in all nine repositories, and all nine are public.
  - The action is v3.0.0, which defaults to gitleaks 8.24.3. Only juniper-data's cron scans history.
- **Other v1.2 facts.**
  - The bench caps are `<0.17.0` at L97 and L106.
  - The installer's L205-214, the recovery plan's L255, the integrated design's L2277-2278, and the certification's L1683-1684 all hold.
  - The five image locks pin observability 0.4.0 and service-core 0.7.0.
  - `MEMORY.md` is 25,695 characters.
  - `JuniperCascor1` has service-core 0.5.0.
  - juniper-canopy has 59 commits and 24 non-test `.py` files since v0.8.1.
  - S0.8's paths hold.

## Could not check

- Whether `JUNIPER_DATA_API_KEY` was ever padded.
- The watchdog's host state.
- The image's requests version.
- gitleaks 8.24.3 on an empty config. I took that from round 2.

## What this report cannot support

- Any state after 10:51Z.
- That lines outside the v1.1→v1.2 diff are correct.
- Which branch of R3A-01 the owner picks.
