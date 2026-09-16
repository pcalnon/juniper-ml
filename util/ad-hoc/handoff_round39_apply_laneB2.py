#!/usr/bin/env python3
"""Apply round-2 lane B2's findings to the round-39 handoff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reports/2026-09-15_round-39-consensus/laneB2-amputation-exec-naming.md

Lane B2 returned FAIL on amputation (10 LOST items) and on executability (the document never
states how a PR is opened in a fleet where a local ``git push`` cannot land a mergeable commit),
and PASS WITH CORRECTIONS on naming. Every restoration below was re-verified against the repos
before being written -- the byte-mirror obligation, the three X-C sites, the recurrence
data_quality gap and the canopy INFRASTRUCTURE_FIELDS state were each checked by hand, not taken
from the lane's word.
"""

from __future__ import annotations

import sys
from pathlib import Path

HANDOFF = (
    Path(__file__).resolve().parents[2]
    / "prompts/thread-handoff_automated-prompts"
    / "HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md"
)
REG = "`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`"

text = HANDOFF.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    if new in text and old not in text:
        print(f"  --  {label} (already applied)")
        return
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} occurrences of:\n{old[:200]}")
    text = text.replace(old, new, 1)
    print(f"  ok  {label}")


# ============================================================ NAMING (part 3)
sub(
    "**A bare \"§N\" means a section OF this document.** Every reference to another file names it.",
    "**A bare \"§N\" means a section OF this document.** Every reference to another file names it —\n"
    "and this document is\n"
    "`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`,\n"
    "which the changed-file list in §2 must name like any other.",
    "name this document",
)
sub(
    "it was written down only in the round-38 handoff, which §4.9's own preamble\n"
    "   > had already flagged as a gap.",
    "it was written down only in the predecessor handoff named at the top of this\n"
    "   > document, and §4.9 of " + REG + " had already flagged that as a gap.",
    "§4.9 belongs to the register, not here",
)
sub(
    "broad, and is corrected in the register.",
    "broad, and is corrected in " + REG + ".",
    "name the register at D-C",
)
sub(
    "consistent, re-read the ruling.",
    "consistent, re-read the `APD-RCLIENT-004` ruling in §4.9 of " + REG + ".",
    "name the register at C-C",
)
sub(
    "gate every sibling `0.y` release, and the register's own analysis is that the pattern is coherent.",
    "gate every sibling `0.y` release, and the `APD-ML-001` analysis in " + REG + " is that the\n"
    "  pattern is coherent.",
    "name the register at M-A",
)
sub(
    "Everything else in the register is ruled.",
    "Everything else in " + REG + " is ruled.",
    "name the register at §0.5",
)
sub(
    "The row said \"nothing can select it into a dataset\"; corrected 2026-09-15.",
    "`APD-DATA-048` in " + REG + " said \"nothing can select it into a dataset\"; corrected\n"
    "2026-09-15.",
    "name the row and register at §4",
)
sub(
    "Corrected in the register. |",
    "Corrected in " + REG + ". |",
    "name the register at the Retry-After row",
)
sub(
    "`origin/main` far ahead — the register is refreshed from `origin/main` before every edit, so diff\n"
    "against `origin/main`, never `HEAD`.",
    "`origin/main` far ahead (this worktree is at `44de51c5`; `origin/main` is well past it) —\n"
    + REG
    + " is refreshed from `origin/main` before every edit, so diff\n"
    "against `origin/main`, never `HEAD`. **Primary checkouts drift**: a lane that reads \"main\n"
    "today\" out of a checkout reads whatever that checkout last fetched. Read\n"
    "`git show origin/main:<path>`.",
    "§6 branch SHA + primary-checkout-drift rule",
)
sub(
    "Ecosystem: `Juniper/AGENTS.md` (not a git repo — edited directly, no PR, no CI; §5.7).",
    "Ecosystem: `Juniper/AGENTS.md` (not a git repo — edited directly, no PR, no CI; §5.8).",
    "fix the broken §5.7 -> §5.8 pointer",
)
sub(
    "   (`csv_import/generator.py`, `equities/generator.py` ×2), `docs/REFERENCE.md` and `CHANGELOG.md`.",
    "   (`csv_import/generator.py`, `equities/generator.py` ×2), `juniper-data/docs/REFERENCE.md` and\n"
    "   `juniper-data/CHANGELOG.md` (both filenames also exist in juniper-ml).",
    "disambiguate REFERENCE.md and CHANGELOG.md",
)
sub(
    "- [x] Thirty owner rulings taken and recorded in the register (§3)",
    "- [x] Thirty owner rulings taken and recorded in " + REG + " (§3)",
    "name the register in the checklist",
)

# ============================================================ EXECUTABILITY (part 2)
sub(
    "In juniper-data, that the equities pair is at **5.0.0** and the corrected filter is in place:\n"
    "\n"
    "```bash\n"
    "git -C ../../../../juniper-data fetch origin\n"
    "git -C ../../../../juniper-data show origin/main:juniper_data/generators/equities/generator.py | grep -E '^VERSION|_SHARES_ABSOLUTE_CEILING = |kept_values'\n"
    "```\n",
    "That last line is **not decoration**. §4.9 of "
    + REG
    + " cites this handoff by\n"
    "filename, and `tests/test_thread_handoff_archive.py` requires every handoff a top-level note\n"
    "cites to exist in `prompts/thread-handoff_automated-prompts/`. Until both land in the same PR\n"
    "the test fails — which is why they are bundled.\n"
    "\n"
    "In juniper-data, that the equities pair is at **5.0.0** and the corrected filter is in place.\n"
    "**Absolute paths, not `-C ../../`** — a worktree-isolated session refuses a `git -C` whose\n"
    "target is computed at runtime (§5.13):\n"
    "\n"
    "```bash\n"
    "git -C /home/pcalnon/Development/python/Juniper/juniper-data fetch origin\n"
    "git -C /home/pcalnon/Development/python/Juniper/juniper-data show origin/main:juniper_data/generators/equities/generator.py | grep -E '^VERSION|_SHARES_ABSOLUTE_CEILING = |kept_values'\n"
    "```\n",
    "§1: absolute paths + why the archive test is there",
)
sub(
    "- **X-A · `APD-CASCOR-008`**, derive the truncatable-generator set from juniper-data's\n"
    "  `/v1/generators`. Ruled against the two cheaper options (widening cascor's `dataset_type` Literal,\n"
    "  or narrowing the constant to its one reachable member). The startup dependency this introduces is\n"
    "  a constraint on the implementation, not a reason to revisit.",
    "- **X-A · `APD-CASCOR-008`**, derive the truncatable-generator set from juniper-data's\n"
    "  `/v1/generators`. Ruled against the two cheaper options (widening cascor's `dataset_type`\n"
    "  Literal, or narrowing the constant to its one reachable member). The startup dependency this\n"
    "  introduces is a constraint on the implementation, not a reason to revisit — but the ruling does\n"
    "  **not** say what cascor does when juniper-data is unreachable at startup, and that has to be\n"
    "  decided before the code is written.\n"
    "  > **This edit is byte-mirrored, and the mirror has its own CI.** The constant is\n"
    "  > `_PROJECT_API_TRUNCATABLE_GENERATORS`, at **line 139 of both**\n"
    "  > `juniper-cascor/src/cascor_constants/constants_api/constants_api_defaults.py` and\n"
    "  > `juniper-cascor/juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`\n"
    "  > (also in each file's `__all__`, line 279). `juniper-cascor-model/tests/test_drift.py`\n"
    "  > compares the two trees byte-for-byte over\n"
    "  > `_EXTRACTED_DIRS = (\"candidate_unit\", \"utils\", \"log_config\", \"cascor_constants\")`. Mirror\n"
    "  > with `diff`, not by remembering that you copied the file — and note that\n"
    "  > `Test (Python 3.12)` is **not a required check on juniper-cascor**, so a red mirror merges\n"
    "  > and leaves `main` red with nothing naming it. juniper-cascor#633 did exactly that.",
    "X-A: the byte-mirror obligation",
)
sub(
    "- **X-C · `APD-CASCOR-005`**, port juniper-data's explicit non-short-circuiting `matched`-flag loop\n"
    "  into cascor and `juniper-service-core`. Two repos, four lines each, against a reference\n"
    "  implementation that already carries the rationale. Candidate for a named guard in\n"
    "  `juniper-ml/tests/test_service_fork_drift.py`.",
    "- **X-C · `APD-CASCOR-005`**, port juniper-data's explicit non-short-circuiting `matched`-flag\n"
    "  loop into cascor and `juniper-service-core`. All three sites, since the first draft named\n"
    "  none of them: the **reference** is\n"
    "  `juniper-data/juniper_data/api/security.py:99-103`; the two to change are\n"
    "  `juniper-cascor/src/api/security.py:61` and\n"
    "  `juniper-ml/juniper-service-core/juniper_service_core/security.py:66`, both currently\n"
    "  `return any(hmac.compare_digest(api_key, k) for k in self._api_keys)`. Every copy already\n"
    "  uses `compare_digest`; it is the `any(...)` **iteration** that short-circuits. Candidate for a\n"
    "  named guard in `juniper-ml/tests/test_service_fork_drift.py`. Note\n"
    "  `juniper-ml/juniper-service-core/` is a published sub-package, so this is a release, not just\n"
    "  a commit.",
    "X-C: name all three sites",
)
sub(
    "- **M-A · `APD-ML-001`**, state the pin-capping rule beside the pins and in the contract test's\n"
    "  docstring.",
    "- **M-A · `APD-ML-001`**, state the pin-capping rule beside the pins\n"
    "  (`juniper-ml/pyproject.toml:30-31`, `:34`, `:47-49`, `:52`, `:56` — the row in "
    + REG
    + " lists them) and in the docstring of\n"
    "  `juniper-ml/tests/test_pyproject_extras.py`, which is the contract test that reads them.",
    "M-A: name the pins and the test",
)
sub(
    "5. **D-E · idempotency.** `APD-ECO-001`, ruled as the **full mechanism on every mutating route**,\n"
    "   including create — the narrower option (key only batch-delete, cleanup-expired and batch-create,\n"
    "   and document create's natural content-addressed idempotency) was offered and rejected. Needs a\n"
    "   key store and an expiry policy, which lands in `juniper_data/storage/`; likely a new module, but\n"
    "   it is the same package D-B and D-F are both editing.",
    "5. **D-E · idempotency.** `APD-ECO-001`, ruled as the **full mechanism on every mutating route**,\n"
    "   including create — the narrower option (key only batch-delete, cleanup-expired and\n"
    "   batch-create, and document create's natural content-addressed idempotency) was offered and\n"
    "   rejected. Needs a key store and an expiry policy, which lands in `juniper_data/storage/`;\n"
    "   likely a new module, but it is the same package D-B and D-F are both editing, so run it\n"
    "   **after D-F**. **Three things the ruling does not settle and the implementer must:** the TTL,\n"
    "   the store backend, and the enumeration of \"every mutating route\" — write them down before\n"
    "   coding, because none of the three is recoverable from the ruling.",
    "D-E: unsettled decisions and its position",
)

# ============================================================ AMPUTATION (part 1)
sub(
    "### 5.6 The GraphQL rate limit blocks PR creation while REST keeps working",
    "### 5.6 How a PR is opened here — a local `git push` cannot land a mergeable commit\n"
    "**Read this before writing any code.** All nine Juniper repos have `required_signatures`.\n"
    "Local signing hangs (the key needs a hardware touch), and an unsigned commit ANYWHERE in a\n"
    "branch's history blocks the merge — squash does not rescue it. Commits therefore go through\n"
    "GitHub's API, and only GraphQL `createCommitOnBranch` signs; `PUT /contents` does not.\n"
    "\n"
    "- **Open a PR**: `python3 util/open_signed_pr.py --repo <repo> --branch <branch> --add\n"
    "  LOCAL_PATH:REPO_PATH --message <commit msg> --title <title> --body-file <path>`. `--add` is\n"
    "  repeatable; exit 0 = opened, 1 = refused (a duplicate PR or an existing branch), 2 = hard\n"
    "  error. `--dry-run` resolves and prints the plan without writing.\n"
    "- **Add a follow-up commit** to a branch that already exists:\n"
    "  `python3 util/ad-hoc/2026-08-26_push_signed_fixup.py --repo <repo> --branch <branch> --add\n"
    "  … --message …`. It pins `expectedHeadOid` so a concurrent write fails loudly.\n"
    "- **Both tools send WHOLE FILES.** Re-check `git log HEAD..origin/main -- <path>` immediately\n"
    "  before every push, or you silently revert someone else's merged change.\n"
    "- **Verify a merge in two steps**: `gh pr view <N> --json state,mergedAt,mergeCommit` **and**\n"
    "  that the content is on `main`. A MERGED badge is not ancestry, and `util/safe_merge.py`\n"
    "  prints the *head* SHA, not the squash commit.\n"
    "- **Merge approval**: headless merges are gated on the owner's explicit approval, per memory\n"
    "  `feedback_headless_merge_approval_policy`; deploys are the owner's, per\n"
    "  `feedback_deploy_approvals_paul_manages`. A session-wide grant covers only the PRs of the\n"
    "  arc it was given for.\n"
    "\n"
    "### 5.7 The GraphQL rate limit blocks PR creation while REST keeps working",
    "restore the signed-PR procedure as a new §5.6",
)
sub(
    "### 5.7 `open_signed_pr.py` can create the BRANCH and fail the COMMIT",
    "### 5.8 `open_signed_pr.py` can create the BRANCH and fail the COMMIT",
    "renumber old §5.7 -> §5.8",
)
sub(
    "### 5.8 The ecosystem data contract is edited without CI",
    "### 5.9 The ecosystem data contract is edited without CI",
    "renumber old §5.8 -> §5.9",
)
sub(
    "### 5.9 Decision 11 set a floor, not a fixed point",
    "### 5.10 Decision 11 set a floor, not a fixed point",
    "renumber old §5.9 -> §5.10",
)
sub(
    "### 5.10 A value-changing fix without a `generator_version` bump serves the old numbers",
    "### 5.11 A value-changing fix without a `generator_version` bump serves the old numbers",
    "renumber old §5.10 -> §5.11",
)
sub(
    "### 5.11 A comment's numerator does not follow its denominator",
    "### 5.12 A comment's numerator does not follow its denominator",
    "renumber old §5.11 -> §5.12",
)
sub(
    "### 5.12 Environments",
    "### 5.13 The sandbox refuses shell STRUCTURE, and it is mode-dependent\n"
    "Loops, `&&` with a heredoc, `${PIPESTATUS}`, unquoted variables in an option position, a\n"
    "`git -C` whose target is computed at runtime, and any command computing a `git` / `gh`\n"
    "argument at runtime are all refused in a worktree-isolated session — which is why §1's\n"
    "juniper-data commands use absolute paths. Put every multi-line edit in a scratch script under\n"
    "`util/ad-hoc/` and run it by absolute path. That is also the ecosystem rule\n"
    "(`Juniper/AGENTS.md` § Cross-Project Conventions: `/tmp/` is prohibited as the home of any\n"
    "script that produces, modifies or analyses repository content), so the workaround and the\n"
    "convention agree.\n"
    "\n"
    "### 5.14 The register crosscheck catches two things a close silently misses\n"
    "`util/ad-hoc/register_status_crosscheck.py` caught both of this arc's protocol slips: a\n"
    "WON'T FIX close with no §5.1 verification row, and a status line naming ids in ABBREVIATED\n"
    "form (`-040`), which its `APD-[A-Z]+-\\d+` regex does not match. It also treats **every id on\n"
    "the status line as claimed-fixed**, so an open row mentioned there fails the check. Run it\n"
    "after every close — the four other touches of the five-touch protocol will not reveal any of\n"
    "these.\n"
    "\n"
    "### 5.15 Environments",
    "restore the sandbox + crosscheck traps, renumber Environments",
)
sub(
    "juniper-recurrence has **no** environment — borrow one and set\n"
    "`PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the worktree (in a borrowed\n"
    "env `test_crossval.py` does not collect and one torch test skips, both pre-existing). All three\n"
    "repos carry `-q` in `addopts`, so use `-v … | grep ' passed'` and `-p no:cacheprovider`.",
    "juniper-recurrence has **no** environment — borrow one and set\n"
    "`PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the worktree (in a\n"
    "borrowed env `test_crossval.py` does not collect and one torch test skips, both pre-existing).\n"
    "All three repos carry `-q` in `addopts`, so use `-v … | grep ' passed'` and\n"
    "`-p no:cacheprovider`. **canopy needs `conda run -n JuniperCanopy1`, not the env's python\n"
    "directly**: invoked directly it skips the hook that strips the Rust `libtorch` path, and\n"
    "anything importing torch then dies on `libtorch_python.so: undefined symbol`. Unit tests that\n"
    "never import torch pass either way, which is how a partial run reads healthy.",
    "restore the canopy conda-run mechanism",
)

# ------------------------------------------------- the two dropped open items
sub(
    "### 0.4 juniper-ml",
    "### 0.4 Two open items that belong to no register row\n"
    "Neither is in " + REG + " and neither is in §0.1–§0.3. They are\n"
    "recorded here because the alternative is that they are recorded nowhere.\n"
    "\n"
    "- **`equities_seq` has no `data_quality` consumer in the recurrence tier.** juniper-data#388\n"
    "  made the producer refuse and annotate; nothing reads the annotation downstream —\n"
    "  `grep -rn data_quality --include='*.py'` across\n"
    "  `/home/pcalnon/Development/python/Juniper/juniper-recurrence` returns **zero hits**\n"
    "  (re-checked 2026-09-15). A refusal nobody reads is a refusal that reaches no operator.\n"
    "- **`val_ratio` was excluded from canopy's sidebar and the direction was never recorded.**\n"
    "  `val_ratio` now sits in `INFRASTRUCTURE_FIELDS`\n"
    "  (`juniper-canopy/src/dataset_schema.py:114`), so the three ratio fields are treated alike —\n"
    "  but that was the non-obvious half of the choice: it makes the set consistent **and removes\n"
    "  the only sidebar control over the in-loop selection split**. No canopy note or ledger row\n"
    "  records it. §4.9's preamble in " + REG + " carries the same\n"
    "  correction; an earlier draft of that preamble claimed the item \"belongs to the canopy\n"
    "  ledger\", which named an intention as though it were a location.\n"
    "\n"
    "### 0.5 juniper-ml",
    "restore the two orphan open items as a new §0.4",
)
sub(
    "### 0.5 Owner decisions still owed",
    "### 0.6 Owner decisions still owed",
    "renumber Owner decisions -> §0.6",
)
sub(
    "Only one: **`APD-DATA-047`**, whether the absolute share-count ceiling stays, and at what value.",
    "Only one: **`APD-DATA-047`**, whether the absolute share-count ceiling stays, and at what\n"
    "value.",
    "reflow §0.6 opening",
)
sub(
    "sequenced into PR-sized units.\n\n---\n\n## 0. Remaining work",
    "sequenced into PR-sized units.\n\n"
    "**The owner's partial-data spec exists verbatim only in the memory\n"
    "`project_partial_data_contract_arc_2026-09-05`** — its table of the three options and their\n"
    "wire forms. " + REG + " and every handoff paraphrase it. D-A\n"
    "(§0.1) implements option 3's wire form, so read the memory, not the paraphrase.\n"
    "\n---\n\n## 0. Remaining work",
    "restore the partial-data-spec-only-in-memory note",
)

# ------------------------------------------------- §7: name the procedure
sub(
    "**Round 1:** three lanes, launched together — receipts-and-source (A), refutation (B1), and",
    "Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.\n"
    "\n"
    "**Round 1:** three lanes, launched together — receipts-and-source (A), refutation (B1), and",
    "§7: name the consensus procedure",
)

HANDOFF.write_text(text)
print(f"\nhandoff updated: {HANDOFF.name}")
