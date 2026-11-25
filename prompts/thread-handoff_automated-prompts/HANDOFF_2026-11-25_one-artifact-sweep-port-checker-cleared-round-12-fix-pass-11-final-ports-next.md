# Handoff: one-artifact sweep. The port checker is CLEARED (round 12: no BLOCKER, no MAJOR) and FINAL after fix pass 11; next, the 15 ports in 7 repos, then plan v1.15.18

**Written**: 2026-11-25 (`date -u`, see the PR) by session `ffffd3` (`d935c226`), ListAgents name
`one-artifact-sweep-plan-v1-15-17-merged-round-4-majors-fix-pass-3-round-5-land-after-cascor-772`.
**Worktree**: `W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ethereal-munching-peacock`.

This file **supersedes** this session's two earlier handoffs, which you should also read for the ports' detail and the
traps:
- juniper-ml#2620: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_one-artifact-sweep-cascor-777-merged-checker-round-6-blocker-fix-pass-5-round-7-then-ports-plan-v1-15-18.md`;
- juniper-ml#2630: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_one-artifact-sweep-owner-rules-pin-exact-install-scripts-fix-pass-7-round-9-then-ports.md`.

**Merge approval** is per-session: ask the owner again. **Start in `$W`**, the only place the arc's untracked scripts
and evidence exist.

## State (the live record is `$W/tmp/sweep/REVIEW_DISPOSITIONS.md`; `grep -n '^## '` lists its sections)

- **juniper-cascor#777 is MERGED** (`f5ed3017`, 2026-11-24). The template is cascor `main`'s `publish.yml`. `main` has
  since moved (`5e3d9801` at round 12), and the three publishers are byte-identical.
- **The port checker's review is DONE.**
  - Rounds 5-12 and fix passes 4-11 brought it to exact install-script pins
    (`util/ad-hoc/2026-11-24_publish_port_install_pins.json`, 18 pins), exact job-key sets, an exact extra-job
    allow-list (juniper-data's `notify-consumers` with its called file sha256-pinned), the template's exact action SHAs,
    YAML 1.2 typing, refusal of anchors, aliases and control characters at load, and escaped output.
  - Round 12 was COMPLETE with 0 BLOCKER and 0 MAJOR, which CLEARS THE PORTS. Fix pass 11 then fixed its MINORs and
    NITs, which the stopping rule allows without another round.
  - **The FINAL checker** is `util/ad-hoc/2026-11-23_publish_port_template_identity.py`, sha256
    `a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35`. It matches its line in
    `tmp/arc/sweep_scripts.sha256` (7 paths, all OK). Fix pass 11 finished at about 03:20Z on 2026-11-25. It refuses
    symlinked workflow and called files even when they point at a regular file, because git stores the link.
  - **Its residuals** are listed in § "Fix pass 11": the publish image's registry tag; unpinned build steps before the
    build; concurrency-group sharing; display wrap inside a value; symlinked parent directories; equality-only pins; no
    server-side parser; the SHA256SUMS version not tied to the tag; `timeout-minutes` unread; duplicate step ids.
- **The owner's three rulings of this arc** (verbatim in the dispositions file):
  - after round 5: the cascor PR landed while the checker was fixed (this session's decision, recorded);
  - after round 8: "Pin exact scripts";
  - after round 10: "Pin template SHAs".
- **ml#2606** (the rename) and the technical-owner sweep **#2632** are merged. The ml port builds on the renamed
  `main`.

## Remaining work

1. **Fix pass 11 has finished.** Confirm that `sha256sum -c tmp/arc/sweep_scripts.sha256` shows 7 OK and that the
   checker hashes to `a452db3d…`.
2. **The ports, one PR per repo, 15 publishers in total:**
   - canopy, data, data-client, cascor-client and cascor-worker: `publish.yml` each;
   - recurrence: its 3 publishers;
   - juniper-ml: its 7 publishers.

   The procedure and per-port changes are #2620's item 2, plus:
   - **Run the checker on each port exactly as § "Fix pass 11" says.** That means `--repo`, `--template` (cascor
     `main`'s `publish.yml`) and `--pins`. For juniper-data, fetch `notify-consumers.yml` beside `publish.yml`.
   - **Each port's review updates its pin** in the pins file. That file is untracked in `$W`, and it is the
     owner-ruled source of truth. The expected updates, from § "Fix pass 7":
     - R4-5's `find_spec` for cascor-client, cascor-worker, data, data-client, ml ci-tools and ml observability;
     - ml `publish.yml`'s template lag text, with `tests/test_publish_testpypi_verify.py:477` (R5-F5);
     - R4-1's retargeted ml test lookups, with no new skip.
   - **recurrence:** restore `#        owner       = pcalnon` at line 22 of all three publishers. It is technical
     rename collateral (§ "Port item added after #2630").
   - **No per-port action-ref changes are needed** (§ "Fix pass 9"): all repos use the template's SHAs today.
   - **Done** when `bash tmp/ports/verify_all_mains_v2.bash` prints `18 of 18 pass`. Adapt it first so it passes
     `--pins` and fetches juniper-data's called file.
3. **Plan v1.15.18**, on a FRESH clone of juniper-ml `main`. It records:
   - #777;
   - rounds 1-12 and fix passes 1-11;
   - the three rulings;
   - the ports;
   - the residuals: § "Fix pass 10" and § "Fix pass 11";
   - SWEEP items 28 and 29, with round 10's R10-7 path for item 28;
   - every input in `tmp/arc/plan_v1_15_18_inputs.md` (peers: deploy#284, ml#2619's group C/E/gaps, flood-4's
     `:120`/`:1159` staleness, R55).

   It also lands the 7 manifest scripts (the 6 earlier plus the pins file) and promotes or archives the proof tools
   under `tmp/sweep/` (`cascor-r3`, `cascor-r4`, `checker-r5` … `checker-r12`). Run the CodeQL prescreen and
   pre-commit first.

## Traps (new since #2630)

- **Reviewer rounds take time.** Each took 30-75 minutes and 0.3-0.7 M agent tokens. Do not re-open the checker's
  design without the owner.
- **Subagent reports can be lost when a session ends.** Every reviewer and executor here wrote its result to a file
  (`tmp/r*review/ROUND*_REPORT.md`, the dispositions sections). Keep that pattern.
- **Peers' names change.** Run `ListAgents` before any message.

## Verification (from `$W`, one per call)

```bash
grep -n '^## ' tmp/sweep/REVIEW_DISPOSITIONS.md        # last: "Fix pass 11 ... FINAL for the ports"
sha256sum -c tmp/arc/sweep_scripts.sha256              # 7 x OK
bash tmp/ports/verify_all_mains_v2.bash                # 3 of 18 until the ports land (adapt for --pins first)
```

## Git state of `$W`

- Branch `worktree-ethereal-munching-peacock` at `81b8eaf7`, behind juniper-ml `main`. Nothing staged.
- Untracked: three handoffs of this session, the predecessor's, 28 copies of files on `main`, and the 7 manifest
  files. NEVER delete those 7.
- `tmp/` adds `sweep/checker-r5` … `checker-r12`, `r5review` … `r12review` and the `FIXPASS*`/`ROUND*` briefs.
- Retention is as in #2620's handoff: keep `$W` until the 7 files land and `tmp/` is archived.

## Documents referenced / changed

- **Referenced**: the two earlier handoffs (above); `tmp/sweep/REVIEW_DISPOSITIONS.md`; `tmp/sweep/FIXPASS11_BRIEF.md`;
  `tmp/r12review/ROUND12_REPORT.md`; `tmp/arc/plan_v1_15_18_inputs.md`.
- **Changed in `$W` since #2630**:
  - `util/ad-hoc/2026-11-23_publish_port_template_identity.py` (fix passes 7-11);
  - `util/ad-hoc/2026-11-24_publish_port_install_pins.json` (new in fix pass 7);
  - `tmp/arc/sweep_scripts.sha256`;
  - `tmp/sweep/REVIEW_DISPOSITIONS.md` (rounds 9-12, fix passes 7-11, the two rulings, status notes);
  - `tmp/arc/plan_v1_15_18_inputs.md`;
  - the briefs `FIXPASS7`-`FIXPASS11` and `ROUND9`-`ROUND12` (the executors wrote the `ROUND*` briefs).
- This handoff lands through its own one-file PR.
