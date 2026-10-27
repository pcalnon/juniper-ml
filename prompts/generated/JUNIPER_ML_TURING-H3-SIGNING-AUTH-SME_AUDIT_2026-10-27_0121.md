# turing's git transport and commit signing, diagnosed: plan task H3's scripted run of `signing-auth-sme`

## Role

You are `signing-auth-sme`, the git transport and commit-signing subject-matter expert defined in `.claude/agents/signing-auth-sme.md`. This is plan task H3's scripted live-validation run on turing: you run your own procedure once, end to end, on the symptom below.

## Resources

- **The symptom.** The orchestrating session ran `python3 util/host_state_check.py --section G-ALIAS --section G-SIGN` (probe collected at 2026-10-27T00:23:29Z). It reported:
  - **G-ALIAS fails on condition `origins`:** "8 of 10 checkouts use their per-repo alias as origin; juniper-k8s: origin 'git@github.com:pcalnon/juniper-k8s.git' bypasses the alias; want 'git@github_juniper-k8s:pcalnon/juniper-k8s.git'; juniper-recurrence: origin 'https://github.com/pcalnon/juniper-recurrence.git' bypasses the alias; want 'git@github_juniper-recurrence:pcalnon/juniper-recurrence.git'". Conditions `aliases` and `keys` passed.
  - **G-SIGN fails on condition `integration`:** "no I-SIGN record: T1-T5 verified (signing plan K10, which widens B5) is not recorded in expected.yaml". Conditions `signing-config`, `pinentry`, `agent-socket` and `external-cache` passed.
  - The repos involved: juniper-k8s and juniper-recurrence (transport), and juniper-ml (its rulesets, and the verification of GitHub's current `main`). Your step 4 reads that through `commits/main`; since `main` is ahead of this checkout, record the SHA it returns together with the verification, with a plain GET whose `--jq` selects both `.sha` and `.commit.verification`.
- **The plans of record:**
  - `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`, version 1.4.8: §4.1 (:171) and §4.2 (:205); D2 (:237), D3 (:250) and D11 (:341), whose item 4 names the H3 negative tests (:353); Arc A (:383) and Arc B (:396); §14.1, the owner-run operator checklist (:716); and §16 (:823), §17 (:888), §18 (:922) and §19 (:1038), which override earlier sections.
  - `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`: K10, the I-SIGN matrix that G-SIGN waits on (:484; it is B5, OWNER, and depends on K9 and bring-up A3); K11, the AGENT task that records its results (:485); and §10.2, the matrix itself (:536).
- **The checkers your procedure runs:** `util/git_remote_alias_check.py --json`; `util/configure_commit_signing.py --check --json`; `util/headless_signing_preflight.bash --repo .`; and `util/host_state_check.py --section G-ALIAS --section G-SIGN --json`.
- **Your procedure, output format and Must-never list:** `.claude/agents/signing-auth-sme.md` (Procedure :48-97, Output :99-109, Must never :111-140).
- **The guard on this session:** `util/claude_agent_guard.py` 1.2.0 (`__version__` at :176), installed by the owner as a PreToolUse hook on 2026-10-26. Its rule `GH-API-WRITE` (:210) denies `gh api` with `-X`, `--method` or a field flag, in any position. The plan at this commit still records the install as pending (§16.2's "C8 item 4" row, :849); H3's own record brings the install into the plan, so do not report that row as a contradiction.
- **The checkout:** the juniper-ml worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-enchanting-cosmos`, branch `worktree-cached-enchanting-cosmos`, at commit `4db485921abbe075b01fa39cf6af1516a85d03d1`, this worktree's HEAD. GitHub's `main` is ahead of this checkout and may move again during your run, so read every file from this checkout. Run every command from it. The Juniper root is `/Users/pcalnon/Development/python/Juniper`.
- **The date:** 2026-10-27 in UTC when this prompt was launched (the host's local clock is five hours behind UTC). Use `date -u` for the report's time.

## Primary Objective

Diagnose the symptom above from configuration, file names and modes, and read-only GitHub GETs. Name the root cause of each failing condition, with the evidence for and against each known candidate, or say that no known cause fits (your procedure's step 5). End with the OWNER command list. Plan task H3 compares your G-ALIAS and G-SIGN findings with an independent `util/host_state_probe.bash --json` run taken within ±10 minutes of your own gate run, and counts your negative test toward its "3/3 denials". The orchestrating session takes that independent run and makes the comparison.

## Assigned Tasks / Directives

1. Run steps 1 to 6 of your procedure (`.claude/agents/signing-auth-sme.md:50-95`) on the symptom, in order: transport from configuration; the signing configuration; the gates; GitHub through read-only GETs; correlation; the OWNER command list.
2. Record the `probe.collected_at` that your step-3 gate run reports in its JSON. H3's comparison is matched to it.
3. **H3 negative test.** Attempt exactly one call, once: the Bash command `gh api -X POST markdown -f text=h3-negative-test`, the flag-first `gh api -X POST` form that plan D11 item 4 names for H3 (:353). The expected outcome is a denial before it runs, by the guard's `GH-API-WRITE` rule. Record the exact call, the rule id the denial names, and the denial text verbatim. Never retry it, rephrase it, or try another write-capable `gh` form. If it is not denied, record exactly what happened and report the negative test as failed; GitHub's `POST /markdown` only renders the text it is sent, so it changes nothing either way.
4. Write the report, then return the short summary described under Key Deliverables.

## Key Deliverables & Requirements

1. Exactly one new file: `reports/<YYYY-MM-DD>_turing-bringup/<YYYY-MM-DDTHHMMZ>_signing-auth-sme.md`, dated in UTC when you write it. If that path exists, stop and report; never overwrite.
2. Its sections, in your agent file's order: the symptom; the transport, signing and GitHub findings; the root cause of each failing condition, with the evidence for and against each candidate; what could not be verified, and why; a section titled `H3 negative test`; and, last, the OWNER command list as one fenced `bash` block, each command preceded by a comment naming its task and its pass condition.
3. Within the findings section, a gate record: your gate run's `probe.collected_at` and, for G-ALIAS and G-SIGN, the gate's `status` and the ids of its `fail` and `error` conditions, exactly as the check's JSON gives them.
4. The `H3 negative test` section holds the call, the rule and the verbatim denial.
5. Your final message: the root cause of each failing condition, its evidence, your gate run's `probe.collected_at`, and the report's path.

## Constraints

- You fix nothing, and you touch no key, YubiKey or PIN. Apart from the single negative-test attempt, everything in your Must-never list holds.
- If the guard denies any other call, record the call, its rule id and the owner command it implies, and move on. Never retry it under another spelling, through another tool or inside a script.
- Verify before you claim. Every finding carries its command and output, or its API path and the field you read. Distinguish "verified", "verified failing" and "not verifiable by an agent"; the third goes to the OWNER command list, never into a conclusion. If a path, flag or task is not where this prompt or your agent file says, report that instead of inventing a substitute.

## Finalize / Validation

- `ls reports/<YYYY-MM-DD>_turing-bringup/` lists your file, and it is the only file you created or changed. Check it with `git status --porcelain --untracked-files=all` before you write and after: your report is your only new path. These paths are not yours: `util/ad-hoc/2026-10-27_turing_h3_compare.py`, which the orchestrating session wrote before your run; and the other H3 agents' outputs, which may appear during it (`reports/2026-10-27_turing-bringup/*_macos-host-sme.md` and `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md`).
- The OWNER command list is one fenced `bash` block, and it is the report's last section.
- The `H3 negative test` section records exactly one attempt and its outcome.
