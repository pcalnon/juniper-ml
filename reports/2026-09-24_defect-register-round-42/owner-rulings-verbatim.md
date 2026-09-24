# Defect-register round 42 -- the owner's rulings, verbatim

Extracted by `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` from the two session transcripts. It selects every
AskUserQuestion call that mentions juniper-cascor's mixed-provenance gap and keeps the WHOLE call, so the rulings asked beside it
(the PR sweeper, juniper-data 0.16.0's contents, which session does the follow-ups) are recorded too. The questions and options
are the call's input as sent, JSON-dumped; the answer is the tool_result as returned. Nothing is paraphrased.

## Session `bc31e993`, asked 2026-09-24T03:34:45.231Z, answered 2026-09-24T07:32:48.582Z

Question(s) and options, as sent:

```json
[
  {
    "question": "cascor#678 (merged) has a mixed-data gap. After a partial fetch, an inline start that supplies only train data keeps the fetched val/test splits (cascor#582's retain-on-omit). The run early-stops on the partial val and reports on the partial test, while dataset_shortfall (and current_dataset) read null. That is the denial APD-CASCOR-007 removed. Which fix?",
    "header": "Mixed data",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep while fetched splits stay (Recommended)",
        "description": "The fetch's annotation (and current_dataset) stays for as long as any of its partitions is still loaded. It clears only once train, val and test have all been replaced. This extends your 'follows the loaded data' ruling to each partition, with no API shape change and no change to training behaviour."
      },
      {
        "label": "Drop fetched val/test on new X",
        "description": "New inline train data replaces all three partitions, so fetched val/test are never mixed with it. This reverses cascor#582's retain-on-omit: a train-only inline start would then run with no val/test unless the caller sends them."
      },
      {
        "label": "Annotate each partition",
        "description": "dataset_shortfall reports train, val and test separately. This is the most precise option, but it changes the API shape that canopy consumes, and is the largest change."
      }
    ]
  },
  {
    "question": "Four PRs from this arc (data#428, ml#2032, ml#2059 and canopy#678) were taken out of draft and armed 4-7 s later, as pcalnon, by nothing in this session. All four merged before their final validation rounds, and cascor#678 was armed the same way earlier. Is that sweeper yours?",
    "header": "PR sweeper",
    "multiSelect": false,
    "options": [
      {
        "label": "Mine: fix forward",
        "description": "The sweeper is yours and the merges are intended. I keep validating after the merge and fix forward with follow-up PRs."
      },
      {
        "label": "Not mine: validate pre-PR",
        "description": "I push branches and validate them before opening any PR, so nothing exists to be swept until validation clears. It costs one extra step per PR."
      },
      {
        "label": "Not mine: you'll look",
        "description": "You'll investigate what is un-drafting and arming PRs. Until then I validate before opening PRs."
      }
    ]
  }
]
```

Answer, as returned:

```text
Your questions have been answered: "cascor#678 (merged) has a mixed-data gap. After a partial fetch, an inline start that supplies only train data keeps the fetched val/test splits (cascor#582's retain-on-omit). The run early-stops on the partial val and reports on the partial test, while dataset_shortfall (and current_dataset) read null. That is the denial APD-CASCOR-007 removed. Which fix?"="Keep while fetched splits stay (Recommended)", "Four PRs from this arc (data#428, ml#2032, ml#2059 and canopy#678) were taken out of draft and armed 4-7 s later, as pcalnon, by nothing in this session. All four merged before their final validation rounds, and cascor#678 was armed the same way earlier. Is that sweeper yours?"="Mine: fix forward". You can now continue with these answers in mind.
```

## Session `bc31e993`, asked 2026-09-24T07:59:55.177Z, answered 2026-09-24T08:01:26.265Z

Question(s) and options, as sent:

```json
[
  {
    "question": "Another session (\"defect reg [977fa8]\") says you ruled \"Split: old does follow-ups\", which would mean this session finishes the cascor and canopy follow-up PRs. But you told this session to wrap up and stopped those agents. Their work is untested WIP in two worktrees, with patches in ml#2072. Should this session resume them?",
    "header": "Follow-ups",
    "multiSelect": false,
    "options": [
      {
        "label": "Resume both here",
        "description": "This session finishes the cascor follow-up (your mixed-data ruling plus seven findings) and the canopy follow-up (six items, including the key leak) from the kept WIP. It tests, validates and opens both PRs, then reports each PR number, merge SHA and validation summary to the other session."
      },
      {
        "label": "Stay wrapped up",
        "description": "This session does nothing more. The WIP worktrees and patches stay as they are, and the other session or a new one picks up the follow-ups."
      },
      {
        "label": "Resume cascor only",
        "description": "This session finishes only the cascor follow-up and leaves the canopy one for another session."
      }
    ]
  }
]
```

Answer, as returned:

```text
Your questions have been answered: "Another session ("defect reg [977fa8]") says you ruled "Split: old does follow-ups", which would mean this session finishes the cascor and canopy follow-up PRs. But you told this session to wrap up and stopped those agents. Their work is untested WIP in two worktrees, with patches in ml#2072. Should this session resume them?"="Resume both here". You can now continue with these answers in mind.
```

## Session `8f86dec2`, asked 2026-09-24T07:37:57.678Z, answered 2026-09-24T07:53:26.965Z

Question(s) and options, as sent:

```json
[
  {
    "question": "Yesterday 21:47–22:57Z, something acting as `pcalnon` readied and armed six drafted PRs from three sessions (including data#428, ml#2032 and ml#2059, each drafted with a 'held on purpose' comment), and merged canopy#678 and data-client#212 directly. No Claude Code process on this host issued those commands. Was it you?",
    "header": "PR sweeper",
    "multiSelect": false,
    "options": [
      {
        "label": "Yes, it was me",
        "description": "From the GitHub UI or another machine. I'll stop using drafts to hold PRs, validate on a pushed branch BEFORE opening a PR, and arm my own PRs with curated squash bodies."
      },
      {
        "label": "An automation of mine",
        "description": "Same handling as 'me'. Name it under Other if you want it recorded in memory."
      },
      {
        "label": "Not me",
        "description": "Treat it as a possible token compromise: I pause all merges, and you audit GitHub's security log and rotate the tokens that can act as pcalnon."
      }
    ]
  },
  {
    "question": "cascor#678 left a mixed-provenance hole. After a partial fetch sets `dataset_shortfall`, an inline train-only start (`POST /v1/training/start` with `inline_data {train_x, train_y}`) binds new X and sets the annotation to null. But it KEEPS the fetch's `X_val`/`X_test`, so the run early-stops on, and reports, the partial fetch's splits while status and `/v1/metrics` say null. The 2026-09-23 ruling's clauses conflict here: 'inline data sets null' against 'a run on fetched partial data always says so'. Which rule applies?",
    "header": "Shortfall",
    "multiSelect": false,
    "options": [
      {
        "label": "Keep while any split is fetched (Recommended)",
        "description": "The annotation stays whenever any partition the run uses came from a short fetch; it is null only when every partition is inline. Smallest change, never under-reports, and consistent with the ruling's rejection of the APD-CASCOR-007 denial."
      },
      {
        "label": "Drop retained val/test",
        "description": "A new inline X without val/test discards the kept val/test, so the run has no val/test from the fetch. This changes training behaviour: no early-stopping split for such a run."
      },
      {
        "label": "Annotate per partition",
        "description": "`dataset_shortfall` records train/val/test provenance separately. The most precise option, but it changes the API shape that canopy and the clients parse."
      }
    ]
  },
  {
    "question": "juniper-data 0.16.0 is bumped on main (#433, `7125e16`) but not released. #428 merged after the bump, so CHANGELOG.md now has two `## [0.16.0]` headings. The ceremony renders only the first, which holds #428's entries alone, so the 0.16.0 Release notes would drop #421/#422/#426/#427/#429 and could not be re-cut. The ceremony's `gh release create` passes no `--target`, so it tags main HEAD and 0.16.0 would ship #428's code, including its breaking change (the access counters leave the representation). What should 0.16.0 contain?",
    "header": "data 0.16.0",
    "multiSelect": false,
    "options": [
      {
        "label": "Fold #428 into 0.16.0 (Recommended)",
        "description": "One [0.16.0] section holding everything on main (#421/#422/#426/#427/#429 + #428 + #434), with an empty [Unreleased]. The notes then match what a Release cut from main ships, with #428's Breaking entry flagged."
      },
      {
        "label": "Keep #428 out of 0.16.0",
        "description": "Move #428 (and #434) to [Unreleased]. 0.16.0 must then be cut by hand with `--target 7125e16`, because the ceremony always tags main HEAD. #428 ships in 0.17.0."
      }
    ]
  }
]
```

Answer, as returned:

```text
The user answered: "Yesterday 21:47–22:57Z, something acting as `pcalnon` readied and armed six drafted PRs from three sessions (including data#428, ml#2032 and ml#2059, each drafted with a 'held on purpose' comment), and merged canopy#678 and data-client#212 directly. No Claude Code process on this host issued those commands. Was it you?"="the sweeper was mine. validate after merge and fix forward", "cascor#678 left a mixed-provenance hole. After a partial fetch sets `dataset_shortfall`, an inline train-only start (`POST /v1/training/start` with `inline_data {train_x, train_y}`) binds new X and sets the annotation to null. But it KEEPS the fetch's `X_val`/`X_test`, so the run early-stops on, and reports, the partial fetch's splits while status and `/v1/metrics` say null. The 2026-09-23 ruling's clauses conflict here: 'inline data sets null' against 'a run on fetched partial data always says so'. Which rule applies?"="Keep while any split is fetched (Recommended)", "juniper-data 0.16.0 is bumped on main (#433, `7125e16`) but not released. #428 merged after the bump, so CHANGELOG.md now has two `## [0.16.0]` headings. The ceremony renders only the first, which holds #428's entries alone, so the 0.16.0 Release notes would drop #421/#422/#426/#427/#429 and could not be re-cut. The ceremony's `gh release create` passes no `--target`, so it tags main HEAD and 0.16.0 would ship #428's code, including its breaking change (the access counters leave the representation). What should 0.16.0 contain?"="Fold #428 into 0.16.0 (Recommended)". Read the answers carefully — they may request clarification, changes, or that you not proceed — and follow what they actually say.
```
