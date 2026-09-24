# Pending items for the NEXT register PR (the closes PR), after the fix-forward PR merges

## From the old session (bc31e993), ~10:50Z -- a NEW owner ruling + PRs in flight THERE (do not duplicate)
- RULING "Key leaks" (AskUserQuestion; verify verbatim from bc31e993's JSONL before quoting -- extend
  util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py MARKERS or add "Key leaks"): chosen "Fix everywhere
  now (Recommended)", no notes. Description: "Up to four PRs. canopy: check outbound keys where they're read,
  stop returning transport errors in API bodies, compare keys as bytes, plus #683's two LOW gaps. juniper-ml:
  observability stops capturing local variables, and service-core compares as bytes. juniper-data and
  juniper-cascor: bytes compare, keeping the drift-gate markers. Releases stay yours."
- Rows to FILE (IDs mine; ruled, in flight, NOT parked):
  - APD-ECO-013 (S): anonymous non-ASCII X-API-Key -> str compare_digest TypeError -> 500 -> Sentry
    include_local_variables=True records the real key (canopy security.py:113-117 at 8917fdac; same shape in
    service-core, data, cascor; juniper-observability does not disable local capture). Observed: real uvicorn +
    sentry-sdk 2.69.2.
  - APD-ECO-014 (S): canopy outbound keys read raw (backend/__init__.py:95; settings.py:486-489, :544-547);
    requests/httpx/websockets quote a key they refuse to send; logged at ERROR (cascor_service_adapter.py:2030,
    :1542, :1560; demo_mode.py:560, :1114, :1128, :2028; recurrence_backend.py:221), returned in bodies
    (service_backend.py:201 -> main.py:3712/:3714 409; recurrence_backend.py:219 -> :287; adapter {"error": str(e)}).
    Anonymous exfiltration with auth ON + JUNIPER_CASCOR_API_KEY="...\n": GET /api/csrf then POST /api/train/start
    (Origin localhost:8050) -> 409 detail contains the key. Also on 5907713b.
  - LOW 3 (_docs_enabled pinned by one sample, main.py:517) and LOW 4 (padded-key WARNING names CANOPY_API_KEY for
    a _FILE value; comment security.py:350 wrong) -> canopy E2E ledger.
- Peer's PRs: canopy fix/secret-leaks-683-validation (after #683 merges); juniper-ml observability
  include_local_variables=False + service-core bytes compare; juniper-data fix/bytes-compare-no-500; juniper-cascor
  same branch name. Numbers/SHAs to come.
- cascor#686 SUPERSEDED (conflict with cascor#687 merged 09:46Z) by a v2 PR on branch
  fix/shortfall-mixed-provenance-and-678-followups-v2 (all 5 validation findings fixed in e452a66: C901=11, 46/46
  mutants killed). Close CASCOR-008/-013 against the v2 PR's merge, not #686.
- canopy#683 (head 8917fdac) validated: all claims reproduce; title narrowed to "a padded CANOPY_API_KEY".
- CLOBBER WARNINGS SENT: data CHANGELOG/docs vs #438; juniper-ml docs/REFERENCE.md drift-gate section vs my next PR.
- PEER ACKED (~11:00Z): its data bytes-compare PR opens only AFTER data#438 MERGES (builds from post-merge main);
  it stops and reports if #438 has not merged ~60 min after its data work is ready -> #438's fix-in-place is
  TIME-SENSITIVE. Its juniper-ml PR avoids the register and REFERENCE.md's fork-drift section (~L2971-2976) and
  will report any other REFERENCE.md / root CHANGELOG.md sections it touches. APD-ECO-013/-014 IDs agreed; LOW 3/4
  -> canopy E2E ledger as FIXED-BY the canopy leak PR (fix/secret-leaks-683-validation).

Source of each item in brackets. Verify every one against source before filing.

## Closes (only after the PR merges AND its validation reports)
- APD-CASCOR-008 / APD-CASCOR-013 -> cascor#686 [peer defect reg [042116]]. Validated 2026-09-24 at 653bc3f and 8f28272 (merge of main + #685): ruling holds on every entry path (~60 HTTP probe steps), all 8 earlier findings resolved, CHANGELOG well-formed, canopy reads only current_dataset.dataset_type (shape unchanged). BLOCKED on C901 (start_training 16 > 15 after merging #685); implementer fixing (1) C901 by extraction, (2) auto-start annotation dropped silently when another fetch's split is loaded (bind auto-start wholesale), (3) mutants NM19/NM20/NM1/NM11 survive -> tests + CHANGELOG "full matrix" claim corrected, (4) flag-off ordinary 422 presented as a shortfall refusal -> looks_like_shortfall keys on "allow_truncation"/"incomplete_rows" (resolves residue a), (5) wording NITs. Need: merge SHA + final summary from the peer.
- APD-DATA-017 / -029 / -032 -> the juniper-data round-3 fix-forward (executor adf9f5dbe46b1b03c, branch fix/conditional-requests-round3-followups). Need: its PR, merge, post-merge validation.

## Residue to file (verify first)
- cascor residue (a): flag-off 422 shown as shortfall refusal naming the knob -> RESOLVED by #686 item (4) if it lands; record as found-and-fixed, not a row.
- cascor residue (b): current_dataset names the fetch after a partial inline start; canopy hydrates its selector from it -> peer confirms harmless and intended (owner's ruling scope, see owner-rulings-verbatim.md). Record, no row.
- cascor residue (c): cascor#678's squash message is stale (already recorded by ml#2074). Stands.
- canopy#683 (canopy follow-up, open, head 8917fdac855b): residue (a) padded JUNIPER_DATA_API_KEY / cascor key via httpx may leak the same way -- validator probing; (b) non-ASCII keys still 500 (documented, unchanged); (c) #678's mutation script 2026-09-23_blank_api_key_warning_mutation_check.py M5/M6 arms can no longer apply (anchor gone) -> its retire condition is met. #683 item 3 is a DISCLOSED behaviour change (whitespace-only env key -> /docs etc. 200).
- canopy NIT (pre-existing, from #686's validation): VERIFIED 2026-09-24 on canopy main -- src/frontend/dashboard_manager.py:8410 (`_producer_detail_from_refusal`, stops (" To accept it,", " The resulting dataset")) drops juniper-data's own last sentence of the cap refusal (juniper_data/core/limits.py:168: "...to import the first N. The resulting dataset will be permanently annotated as truncated."), so the user never sees that truncation is permanent. Fix = cut only at " To accept it,". Canopy behaviour -> canopy E2E ledger (F-CANOPY-*), per register §4.9, NOT a register row; hand to a canopy session.

## Status 2026-09-24 ~10:20Z
- ml#2074 MERGED 09:57:40Z (6aabe4cc); body corrected after merge (PATCH).
- ml#2080 (register fix-forward: 50 primer anchors, ECO-012, DATA-057, ...) MERGED 10:18:14Z (f2688a95). Needs post-merge validation lanes (not yet launched -- waiting for data#438 lanes to finish, session-limit caution).
- ml#2075 (primer v2+v3, head b67af000) re-armed with curated squash body; update-branch done after #2080; waiting on checks.
- ml#2081 (probe provenance, 205 files) armed, updated after #2075; required checks 17/17 GREEN but BLOCKED by the
  CodeQL results check: 61 new alerts in the probes (2 high py/clear-text-logging-sensitive-data, both FALSE
  POSITIVES: ml2074-round1-laneA/deploy_services.py:18 prints compose secret NAMES; canopy678-postmerge-v678c/
  boot_scenarios.py:106 prints hard-coded FAKE test keys; plus 24 file-not-closed, 17 unused-import, ...).
  codeql.yml = advanced setup, +security-and-quality, no config/paths-ignore. OWNER DECISION: (a) paths-ignore
  the probes dir via a CodeQL config, (b) dismiss 61 alerts as won't-fix evidence, (c) archive probes as a
  tarball. Probes are safe meanwhile on the pushed branch chore/round42-probe-provenance.
- ml#2075 MERGED 10:25:51Z (f4d050c6), curated squash body verified in history.
- data#438 (round-3 fix-forward + #437 CHANGELOG move 28fced18): Lane A a66ebaf4cc1925e56 DONE, archived as
  data438-round1-laneA-reprobe.md (all 8 items reproduce; F1 MEDIUM: POST /v1/datasets create -- save_versioned
  takes _version_lock only for named datasets, never _meta_write_lock -- can land inside a conditional PATCH window,
  so "every route that edits or deletes a dataset takes the locks" is false; F2 LOW cached-store scope sentence
  false; F3 LOW http_cache.py:17-19 + docs/REFERENCE.md:1362-1363 still misquote RFC 9110 §8.8.1; F4-F7 NITs;
  F8 next release not flagged breaking (#437 generator 6.0.0 in [Unreleased]) + PR body renderer counts stale).
  Lane B a48b63fe2cf4ce38b RUNNING. #438 is OPEN, CLEAN, NOT merged -> fix IN PLACE: resume the executor
  adf9f5dbe46b1b03c via SendMessage with the consolidated findings (it knows the worktree
  /home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2/).
- #2080 + #2075-v3 post-merge validation lanes: A a3212838e6d1674b7, B a833573c5bbdf2a36 (scratch r42/pr2080-lane{A,B}).
  Archive as ml2080-round1-laneA-reprobe.md / ml2080-round1-laneB-refute.md.
- PyPI v0.16.0 publish run 35977786108 WAITING owner approval; ships batch-tags race, NBSP star, symlink fault (fixed by #438). Owner decision.

## SECOND fix-forward (register + primer), from ml2080-round1-lane{A-reprobe,B-refute}.md -- both lanes agree on H1/M1
Register (notes/...DEFECT-REGISTER.md at main):
- H1 (both): 5 primer citations in 3 places still 3 short. L527 (§3 SVCCORE-003 `| **Primer** | III.7 — lines 7950-7951, 7962, 7964-7968`) -> 7953-7954, 7965, 7967-7971; L1736 "(7944)" -> (7947-7949) [quote at 7948-7949, sentence starts 7947]; L1737 "(8089)" -> (8092). Then restate L766's census (43 cells + 7 prose + 5 more) and fix L1781 ("every anchor past it was three short until 2026-09-24"; L1742's 8188-8195 was never short). Extend the audit to `| **Primer** |` rows and to prose bare numbers 5759-9866, content-checked by READING (the +3 content check alone cannot tell right from wrong for post-creation cites).
- H2 (B) / L1 (A): L1305 APD-ML-008 "a failed juniper-data or juniper-cascor clone skips every guard the same way, since juniper-ml's notes link into both (run on its own ... `OK (skipped=3)`)" is FALSE: juniper-ml has 0 cross-repo links into juniper-data (1 canopy, 4 cascor) so a missing DATA clone passes the link check and the drift step goes GREEN with all 16 sibling sites skipped (no root: `_ROOT_ANCHOR_REPOS` needs both anchors; canopy's sites skip too). Missing cascor/canopy clone -> link check fails first. Add remedy candidate: fail the drift step when GITHUB_ACTIONS=true and no root. Also docs/REFERENCE.md L2972 same false claim; register L1751 "cannot silently lose their markers" false on that path. The rejected A-nit was RIGHT (N6: ci.yml:500 runs the file too).
- L1 (B): lock-less writers undercounted: batch_delete (base.py:590-615) and delete_expired (:423-431) also unlocked (POST /batch-delete, POST /cleanup-expired); register L1302 "Neither of those two" + primer E.2 "makes" (present tense while #438 OPEN).
- L2 (B): L1307 "record_access, which every metadata read and artifact download fires" false: /latest, list, filter, versions record no access; call sites datasets.py:999, :1105, :1137, :1141.
- L5 (B): L302 "The sibling-package-drift group is CLOSED (2026-08-21)" false: last rows 08-24 (dclient#165, cclient#129) and 08-28 (cclient#143).
- L6 (B): blind-spot disclosure incomplete: **FIXED in a Source cell (open-set counts it, crosscheck doesn't); duplicated row invisible to both.
- L7 (B): ml2074 laneB #15 NITs neither applied nor rejected: L1299 FailedAuthThrottle anchors are class defs (wiring data :455, cascor :413); park bullets grouped vs "row-level sentence" (L1246).
- NITs: N1 (A) L1297 CASCOR-013 "three since #678" -> name start_training :2572, _rollback_pre_swap_state :3924, _reload_dataset :4691; N2 (A) L997 "#2059 ... closed 2026-09-24" -> #2059 merged 09-23; N3 (A) L766 "only commit to touch the primer since" false since #2075 -> "to move a line"; N4 (A) L1304 "#2071 then added" -> merged 52 s BEFORE the cut; N5 (both) L1496-1500 ruling descriptions truncated w/o ellipsis; N7 (A) L182 "round 42 added APD-DATA-055 and APD-DATA-057" -> -057 by the fix-forward; N8 (A) L766 context: 68f62f5b deleted the 4-line block #1098 restored; (B) DATA-057 "erased a conditional PATCH's 200" n=1 unstated; (B) L300 "APD-CASCOR-005 is a seventh of the kind" stale (ECO-008/-009/-010).
Primer (notes/...PRIMER.md at main):
- M1 (both): L9879-9880 "each metadata ETag" false for POST create 201 (L5838 hashes second.content only). Fix L5838: also assert first.content digest; add "POST create" mutant to util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py (reverting L5671-5672 passes 62/62 today).
- M2 (B): L9939 bold "A hash of serialized JSON is a strong validator" broader than the argument -> "A hash of the exact bytes sent is a strong validator; a hash of a separate serialization is not." The RFC quote at 9942-9943 is cut mid-sentence and its clause does not cover field-order churn (that IS a representation-data change): complete or drop.
- L2 (A): L1954 "juniper-data (v0.11.0) ... emits no cache headers at all" neither linked nor named -> append E1 marker.
- L3 (B): L5362-5363 "lost tags to a concurrent race until juniper-data#263 and #282" -- batch route kept losing tags through 0.16.0 (APD-DATA-057).
- L4 (B): NaN/Infinity POST -> text/plain 500 (breaks the toy's "RFC 9457 problem details on every error path", L5377); PR body's "refuses NaN again" overstates -> return a 422 ProblemException.
- NITs: (B) build proof checks only "\n" (a bare \r or U+2028 passes); (B) L3346 "a content-addressed identifier" unmarked; (A) L4223-4224 bolds part of a verbatim quote without "emphasis added".
Rejections re-checked (B): B12 and B15 rightly rejected.

## Fix-forward PR follow-ups
- After #2074 merges: PATCH #2074's body (gh api -X PATCH): "#2072 archived 8" -> 11 .md (8 final + 3 stopped-partial) + 2 patches; "byte-identical" -> identical in body; "Every present-tense hit is now dated or corrected" -> corrected-after-merge note naming the fix-forward PR. Saved body: scratchpad/pr2074_body_live.md.
- Rebuild the fix-forward from merged origin/main (register AND docs/REFERENCE.md -- main's perf-lane commit 2b53255a changed REFERENCE.md), re-run util/ad-hoc/2026-09-24_register_round42_fixforward.py, tools, tests, pre-commit, then open_signed_pr.
- Then #2075 (primer v2) needs update-branch; then primer round-2 lanes (a7631c36ca821d652, ad32dacf1c456fe8b) -> archive + fix forward.
- Probe-provenance PR: copy lanes incl. pr2074-laneA/B and primer-r2-laneA/B; README rows; copy script already updated locally.
