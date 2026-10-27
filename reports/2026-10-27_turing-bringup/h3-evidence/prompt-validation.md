# H3's task prompts: validation record

The three H3 task prompts went through the `/template-agent` flow: discovery (`util/prompt_discovery/cli.py`), a filled copy of a template, and the `prompt-validator` subagent against `prompts/agent_templates/RUBRIC.md`, in a loop bounded at 3 rounds. Plan §11 applies the rubric to the H3 task prompts, not to the agent files. All three passed in round 3. The emitted files under `prompts/generated/` are the round-3 texts, byte for byte:

| Agent | Template (class) | Emitted prompt | sha256 | Rounds |
|---|---|---|---|---|
| `macos-host-sme` | `generic` (generic) | `prompts/generated/JUNIPER_ML_TURING-H3-MACOS-HOST-SME_AUDIT_2026-10-27_0121.md` | `6d9e186c5952994cb0612a0e636ad14ee4351234eb0a9489c69987ab03a65fe9` | PASS, PASS, PASS |
| `signing-auth-sme` | `generic` (generic) | `prompts/generated/JUNIPER_ML_TURING-H3-SIGNING-AUTH-SME_AUDIT_2026-10-27_0121.md` | `c749dcfa92932124c17bac80254984b6461fc716e63205964f6171dc0c975edb` | PASS, FAIL, PASS |
| `k8s-node-sme` | `audit` (analysis) | `prompts/generated/JUNIPER_ECOSYSTEM_TURING-H3-K8S-NODE-SME_AUDIT_2026-10-27_0121.md` | `3f574e75ac208da4b9c5ccc82afa7f1d54a1741d545da7989780d1bae19e31ac` | FAIL, FAIL, PASS |

Each round re-ran discovery (TTL 900 s) at HEAD `4db485921abbe075b01fa39cf6af1516a85d03d1`.

- The macos and signing prompts were also revised after their passing rounds.
  - The reasons: round 1's findings, plan D11 item 4's negative-test forms (:353), and round 2's false parenthetical.
  - Each revision was validated again.
  - The terminal state is `EMIT_WITH_CAVEATS` for all three: minor findings only, kept as accepted warnings.

## Prompt validation, round 1 (bundles captured 2026-10-27T00:30:26Z; HEAD 4db48592)

| Prompt | Template (class) | Overall | Findings |
|---|---|---|---|
| macos-host-sme | generic (generic) | PASS | 4 minor: R1.1 the signing plan (K10, K11) not in Resources and dependency disagreements not surfaced; R1.1 "the owner step it implies" dropped from the denial rule; R4 "at `main`" (local `main` is `ecc05079`; HEAD is `origin/main`); R4 the orchestrating session's independent run not named |
| signing-auth-sme | generic (generic) | PASS | 5 minor: R4 "at `main`"; R4 the `H3 negative test` section and gate record had no place; R1.1 K11 and §10.2 not cited; R1.1 D11 item 4 (plan :353) names the H3 negative-test forms (`cat ~/.ssh/config`, flag-first `gh api -X POST`) and the prompt used `-X GET`; R4 "its root cause" for two failing conditions |
| k8s-node-sme | audit (analysis) | **FAIL** | 1 major: R2.3 the agent has no clock (no Bash) and the host's local date (2026-10-26, CDT) differs from UTC (2026-10-27), so "dated in UTC" could not be executed. 3 minor: R4 "at `main`"; R4 the `H3 negative test` section's place and an item's severity when it passes; R3.4 the sentinel path's absence was asserted, not checked |

Round 2 applied every finding. It also moved the two Bash agents' negative tests to D11 item 4's forms, which the R1.1 finding on the signing prompt surfaced: `cat ~/.ssh/config` for `macos-host-sme` (was `sudo -n true`) and `gh api -X POST markdown -f text=h3-negative-test` for `signing-auth-sme` (was `gh api -X GET repos/pcalnon/juniper-ml/rulesets`).

## Prompt validation, round 2 (bundles captured 2026-10-27T00:47:41Z; HEAD 4db48592)

| Prompt | Overall | Findings |
|---|---|---|
| macos-host-sme | PASS | 4 minor: R4 the "`origin/main`'s tip when this prompt was grounded" parenthetical was true only for round 1's bundles; R4 "do not take a full probe run" and "reach `~/.ssh` in any other way" read literally against the check's own probe; R2.3 the dependencies directive 4 asks for had no place in deliverable 4; R2.2 "the only file you created" named no check |
| signing-auth-sme | **FAIL** | 1 blocker: R3.4 the same parenthetical was false for this bundle. A `git fetch` at 00:40:40Z had moved `origin/main` to `22e4a4b9` (#2366) before the capture, and GitHub's `main` then moved to `fb5598b2` (#2368, plan v1.4.9). The agent's step 4 reads GitHub's `main`, so it would have recorded `main`'s verification under the wrong SHA |
| k8s-node-sme | **FAIL** | 1 blocker: the same R3.4. 3 minor: R1.1 the plan at this commit still records the C8 install as pending (§16.2 :849), unsurfaced; R1.1 D11 :353 not cited, nor why this agent's test is the Read-tool form; R4 no one rule for the severity of an item with several findings |

Round 3 removed the parenthetical from all three: the commit is "this worktree's HEAD", `main` is ahead and may move, and every file is read from the checkout. The signing prompt has step 4 record the SHA `commits/main` returns, together with its verification. Every minor finding was applied, and the C8 "install pending" clause went into all three.

## Prompt validation, round 3 (bundles captured 2026-10-27T01:06:58Z; HEAD 4db48592): all PASS

Each verdict was `validator_status: ok`, with every `hallucination_risk` entry grounded by its own re-probe. The remaining findings are minor, recorded here as accepted warnings (template-agent terminal state `EMIT_WITH_CAVEATS`). The emitted prompts are the validated texts, byte for byte; no finding was applied after the pass.

| Prompt | Overall | Accepted warnings |
|---|---|---|
| macos-host-sme | PASS | R1.1 (minor): the "install pending" clause names only §16.2's C8 item 4 row (:849). §18.2's H2 row (:947: "H3 denials wait on C8 and C9", "Install pending") and C9 row (:949: "install OWNER") record the same pre-install state |
| signing-auth-sme | PASS | R4 (minor): "H3's own record brings the install into the plan" refers to a record that does not yet exist at this commit |
| k8s-node-sme | PASS | R4 (minor): "read every file from this checkout" read literally covers the juniper-k8s files, which the prompt gives by absolute path outside it; R4 (minor): the same forward reference to H3's record |
