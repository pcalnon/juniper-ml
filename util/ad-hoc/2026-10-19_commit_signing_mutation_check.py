"""
Show that the commit-signing suite kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — investigation (suite strength evidence for the commit-signing PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (§8, §10.1,
         regressions R-S1..R-S19); util/configure_commit_signing.py; tests/test_configure_commit_signing.py

Each mutant re-introduces one defect into a COPY of the tool. Examples:

- an unpinned key accepted;
- a program outside a GnuPG install accepted;
- the first config value taken as deciding instead of the last;
- D11's environment left in the tool's git calls;
- a planted local gpg.program ignored;
- a missing include passed;
- allow rules evaluated before deny rules;
- --remove deleting the owner's own include.

The suite then runs against that copy in a scratch tree that mirrors the repo layout (the suite
locates the tool relative to its own file). A mutant is KILLED when the suite fails. Each mutant also
names its pin, the test written for that defect, which must kill the mutant on its own. That way a
regression id is not carried by some other case. The unmutated control must pass, or the run is
void. This is the pattern of util/ad-hoc/2026-10-17_turing_b7_mutation_check.py.

Nothing in the repository is modified. It is not wired into CI: it is evidence, not a gate.

Exit codes:

- 0: every mutant was killed, by the suite and by its pin, and the control passed.
- 1: a mutant survived either, or the control failed.
- 2: a mutant's anchor text was not found exactly once (the tool changed; update the mutant).

Usage:
    python3 util/ad-hoc/2026-10-19_commit_signing_mutation_check.py
"""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404 - runs the unittest suite on a scratch copy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/configure_commit_signing.py"
SUITE = "tests/test_configure_commit_signing.py"

ALLOW_FIRST = (
    "    for key in allow:\n        pattern = vscode_rule(key)\n"
    '        if not isinstance(pattern, str) and pattern.search(command):\n            return "unprompted", f"allow rule {key!r}"\n'
    "    unknown_deny = None\n    for key in deny:\n"
)

# (mutant id, defect re-introduced, pin test, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("S1", "R-S1: an unpinned key spec is accepted", "RefusalTest.test_r_s1_an_unpinned_or_malformed_key_exits_2_before_any_write", [('[0-9A-Fa-f]{64})!")', '[0-9A-Fa-f]{64})!?")')]),
    ("S2", "R-S2: a relative gpg.program is accepted", "RefusalTest.test_r_s2_an_unsound_gpg_program_exits_2_before_any_write", [("    if not os.path.isabs(path):\n", "    if False:\n")]),
    ("S3", "R-S2: a group- or world-writable gpg.program is accepted", "RefusalTest.test_r_s2_an_unsound_program_in_the_config_fails_the_check", [('    if writable_by_others(info.st_mode):\n        return f"{target} is writable', '    if False:\n        return f"{target} is writable')]),
    ("S4", "R-S3: the first listed value decides instead of the last", "OverrideTest.test_r_s3_a_repo_local_override_fails_that_repo_and_names_the_scope", [("    return hits[-1] if hits else None\n", "    return hits[0] if hits else None\n")]),
    ("S5", "R-S4: D11's GIT_CONFIG_COUNT reaches the tool's git calls", "OverrideTest.test_r_s4_d11_keeps_plain_agent_commits_unsigned_and_does_not_mask_the_check", [("    return {k: v for k, v in os.environ.items() if k not in names}\n", "    return dict(os.environ)\n")]),
    ("S6", "R-S5: an injected GIT_CONFIG_* / GNUPGHOME / HOME in an IDE terminal env passes", "IdeSettingsTest.test_r_s5_injected_variables_fail_null_unsets_and_jsonc_parses", [("        injected = sorted(name for name, value in env.items() if name in DEFEATING_ENV and value is not None)\n", "        injected = []\n")]),
    ("S7", "R-S5: JSONC settings (comments, trailing commas) cannot be parsed", "IdeSettingsTest.test_r_s5_injected_variables_fail_null_unsets_and_jsonc_parses", [("        return json.loads(strip_jsonc(fh.read()))\n", "        return json.loads(fh.read())\n")]),
    ("S8", "R-S6: --apply --dry-run writes", "ApplyTest.test_r_s6_dry_run_writes_nothing_and_exits_like_check", [("        if (args.apply or args.remove) and not args.dry_run:\n", "        if args.apply or args.remove:\n")]),
    ("S9", "R-S7: --apply re-adds the include on every run", "ApplyTest.test_r_s7_a_second_apply_writes_nothing_and_changes_no_byte", [("    if not wired_values(git, root, include_file):\n", "    if True:\n")]),
    ("S10", "R-S8: an existing backup is overwritten", "ApplyTest.test_r_s8_backups_are_made_once_and_an_owner_include_is_kept", [("        if os.path.isfile(gcfg) and not os.path.exists(backup):\n", "        if os.path.isfile(gcfg):\n")]),
    ("S11", "R-S9: the tool runs gpg.program", "ContractTest.test_r_s9_never_opens_credentials_never_runs_gpg_and_writes_only_its_files", [("    target = os.path.realpath(path)\n", '    subprocess.run([path, "--version"], capture_output=True, check=False)  # nosec\n    target = os.path.realpath(path)\n')]),
    ("S12", "R-S10: the include pattern loses its trailing slash and matches no checkout", "EndToEndTest.test_r_s10_terminal_and_ide_commits_sign_with_the_pinned_key", [('    return "gitdir/i:" + render(root).rstrip("/") + "/"\n', '    return "gitdir/i:" + render(root).rstrip("/")\n')]),
    ("S13", "R-S12: the include pattern matches every repository on the host", "EndToEndTest.test_r_s12_a_repo_outside_the_root_is_untouched", [('    return "gitdir/i:" + render(root).rstrip("/") + "/"\n', '    return "gitdir/i:/"\n')]),
    ("S14", "R-S14: allow rules are evaluated before deny rules", "IdeSettingsTest.test_r_s14_vs_code_auto_approval_is_evaluated_deny_first", [("    unknown_deny = None\n    for key in deny:\n", ALLOW_FIRST)]),
    ("S15", "R-S13: a root with no checkout passes vacuously", "ContractTest.test_r_s13_usage_and_environment_errors_exit_2", [("        if not checkouts:\n", "        if False:\n")]),
    ("S16", "a failed check exits 0", "ContractTest.test_text_output_lists_each_failure_with_its_fix", [('        if "fail" in statuses:\n            return 1\n', '        if "fail" in statuses:\n            return 0\n')]),
    ("S17", "any pinned key passes, not the expected one", "RefusalTest.test_the_spec_is_normalised_and_the_long_id_is_a_different_spec", [('    elif normalize_keyspec(key_hit.value or "") != signing_key:\n', '    elif normalize_keyspec(key_hit.value or "") is None:\n')]),
    ("S18", "an unset user.email passes (IDE commits would fail)", "OverrideTest.test_gpg_format_ssh_and_a_missing_email_fail", [('    if email is None or not (email.value or "").strip():\n', "    if False:\n")]),
    ("S19", "gpg.openpgp.program is ignored", "RefusalTest.test_a_later_gpg_openpgp_program_decides_and_is_judged", [('    program = deciding(entries, "gpg.program", "gpg.openpgp.program")\n', '    program = deciding(entries, "gpg.program")\n')]),
    ("S20", "tag.gpgsign is not checked", "OverrideTest.test_tag_gpgsign_false_fails_on_its_own", [('    for key in ("commit.gpgsign", "tag.gpgsign"):\n', '    for key in ("commit.gpgsign",):\n')]),
    ("S21", "R-S15: paths are rendered without realpath", "RefusalTest.test_a_root_outside_home_is_written_as_its_realpath", [("    real, home = os.path.realpath(path), real_home()\n", '    real, home = os.path.abspath(path), expand("~")\n')]),
    ("S22", "R-S16: a planted local gpg.program / include.path / core.sshCommand passes", "OverrideTest.test_r_s16_planted_local_keys_fail_and_the_own_hooks_path_passes", [("        planted = entry.key in LOCAL_FORBIDDEN or entry.key.startswith(LOCAL_FORBIDDEN_PREFIXES)\n", "        planted = False\n")]),
    ("S23", "R-S16: the checkout's own hooks path is flagged as planted", "OverrideTest.test_r_s16_planted_local_keys_fail_and_the_own_hooks_path_passes", [("            planted = hooks_path(entry.value, base) != own_hooks\n", "            planted = True\n")]),
    ("S24", "R-S17: a wired but missing include passes", "IncludeIntegrityTest.test_r_s17_a_missing_include_fails_and_commits_then_land_unsigned", [('report.add("include", "fail", f"{gcfg} includes {include_file}, which is missing', 'report.add("include", "info", f"{gcfg} includes {include_file}, which is missing')]),
    ("S25", "R-S17: a symlinked include passes", "IncludeIntegrityTest.test_r_s17_a_symlinked_or_writable_include_or_directory_fails", [('    if os.path.islink(path):\n        return f"the {what} {path} is a symlink"\n', '    if False:\n        return f"the {what} {path} is a symlink"\n')]),
    ("S26", "R-S18: a program outside a known GnuPG install passes", "RefusalTest.test_r_s18_a_program_outside_a_known_gnupg_install_fails_unless_vouched_for", [("    if not known_gnupg(target):\n", "    if False:\n")]),
    ("S27", "R-S19: an unmanaged key in the include passes", "IncludeIntegrityTest.test_r_s19_an_unmanaged_key_in_the_include_fails", [("        extra = sorted({k for k, _ in git.file_keys(include_file)} - set(SIGNING_KEYS))\n", "        extra = []\n")]),
    ("S28", "--remove unsets without --fixed-value and drops the owner's include", "ApplyTest.test_remove_undoes_apply_exactly_and_keeps_the_owner_include", [('            git.checked("config", "--global", "--fixed-value", "--unset-all", write.key or "", write.old or "")\n', '            git.checked("config", "--global", "--unset-all", write.key or "")\n')]),
    ("S29", "--remove deletes an include the owner edited", "ApplyTest.test_remove_refuses_to_delete_an_edited_include_and_dry_run_writes_nothing", [("        elif managed_only(git, include_file):\n", "        elif True:\n")]),
    ("S30", "--apply --dry-run skips the checks and exits 0", "ApplyTest.test_r_s6_dry_run_writes_nothing_and_exits_like_check", [("        if not args.remove:\n            run_checks(", "        if not args.remove and not args.dry_run:\n            run_checks(")]),
    ("S31", "chat.tools.global.autoApprove passes", "IdeSettingsTest.test_r_s5_unparseable_files_dead_git_paths_and_global_auto_approve_fail", [('    if settings.get("chat.tools.global.autoApprove"):\n        problems.append(', '    if False:\n        problems.append(')]),
    ("S32", "a null terminal env value counts as an injection", "IdeSettingsTest.test_r_s5_injected_variables_fail_null_unsets_and_jsonc_parses", [(" and value is not None)", ")")]),
    ("S33", "terminal profile environments are not scanned", "IdeSettingsTest.test_r_s5_injected_variables_fail_null_unsets_and_jsonc_parses", [('        profiles = settings.get(f"terminal.integrated.profiles.{os_key}")\n', "        profiles = None\n")]),
    ("S34", "chat.tools.terminal.enableAutoApprove false is ignored", "IdeSettingsTest.test_r_s14_vs_code_auto_approval_is_evaluated_deny_first", [('    if settings.get("chat.tools.terminal.enableAutoApprove") is False:\n', "    if False:\n")]),
    ("S35", "the legacy chat.agent.terminal.autoApprove key is ignored", "IdeSettingsTest.test_r_s14_vs_code_auto_approval_is_evaluated_deny_first", [('    for key in ("chat.tools.terminal.autoApprove", "chat.agent.terminal.autoApprove"):\n', '    for key in ("chat.tools.terminal.autoApprove",):\n')]),
    ("S36", "Amp's last matching rule wins instead of the first", "IdeSettingsTest.test_r_s14_amp_permissions_first_match_wins", [("    for index, rule in enumerate(rules, start=1):\n", "    for index, rule in reversed(list(enumerate(rules, start=1))):\n")]),
    ("S37", "an include file under the Juniper root is accepted", "RefusalTest.test_r_s13_unusable_roots_and_include_paths_exit_2", [("    if under(real_include, os.path.realpath(root)):\n", "    if False:\n")]),
    ("S38", "a root that is $HOME or above is accepted", "RefusalTest.test_r_s13_unusable_roots_and_include_paths_exit_2", [("    if under(real_home(), os.path.realpath(root)):\n", "    if False:\n")]),
    ("S39", "an include file inside a git work tree is accepted", "RefusalTest.test_r_s13_unusable_roots_and_include_paths_exit_2", [('    if inside.returncode == 0 and inside.stdout.strip() == "true":\n', "    if False:\n")]),
    ("S40", "executable hooks are not listed", "EndToEndTest.test_executable_hooks_are_listed_with_their_digest", [("    if hook_names:\n", "    if False:\n")]),
    # Round 2 (plan §14.3): one mutant per defect class the second review found.
    ("S41", "N3: a VS Code rule that matches the empty string is taken at face value", "IdeSettingsTest.test_r_s14_vs_code_auto_approval_is_evaluated_deny_first", [('    if body not in (".*", "^", "$") and pattern.search("") is not None:\n', "    if False:\n")]),
    ("S42", "N2: a VS Code catch-all allow rule is not named", "IdeSettingsTest.test_r_s14_vs_code_auto_approval_is_evaluated_deny_first", [('        catch_all = vscode_catch_all(settings) if settings.get("chat.tools.terminal.enableAutoApprove") is not False else []\n', "        catch_all = []\n")]),
    ("S43", "N2: an unconditional Amp Bash allow is not named", "IdeSettingsTest.test_r_s14_amp_permissions_first_match_wins", [("        catch_all = [str(i) for i, r in enumerate(amp, start=1) if ", "        catch_all = [] and [str(i) for i, r in enumerate(amp, start=1) if ")]),
    ("S44", "N4: any Cellar-shaped path counts as a known GnuPG install", "RefusalTest.test_r_s18_a_cellar_shaped_path_outside_homebrew_is_not_a_known_install", [("    return OTHER_GNUPG_RE.fullmatch(target) is not None\n", '    return OTHER_GNUPG_RE.fullmatch(target) is not None or re.fullmatch(r".*/Cellar/gnupg/[^/]+/bin/gpg2?", target) is not None\n')]),
    ("S45", "N5: --remove deletes an include another wiring still uses", "ApplyTest.test_remove_keeps_an_include_another_root_still_uses", [("        if still:\n", "        if False:\n")]),
    ("S46", "N6: --apply writes through a symlinked include", "RefusalTest.test_apply_refuses_to_write_through_an_unsafe_include_or_directory", [("                if os.path.lexists(path):\n                    problem = file_problem(path, what)\n", "                if False:\n                    problem = file_problem(path, what)\n")]),
    ("S47", "N13: a planted key in a linked worktree passes", "OverrideTest.test_r_s16_a_planted_key_in_a_linked_worktree_fails", [("    for worktree in linked_worktrees(git, checkout):\n", "    for worktree in []:\n")]),
    ("S48", "N13: global and system hook or include settings go unreported", "OverrideTest.test_wider_scope_hook_and_include_settings_are_reported", [("        check_wider_scopes(git, checkouts[0][1], include_file, report)\n", "        pass\n")]),
    ("S49", "N18: --remove deletes an include whose comments the owner edited", "ApplyTest.test_remove_refuses_an_include_with_a_comment_added", [("    return normalize_keyspec(key) is not None and text == canonical_include(key, program)\n", "    return normalize_keyspec(key) is not None and set(values) == set(SIGNING_KEYS)\n")]),
    ("S50", "N18: a hooks path inside ~/.ssh is listed and its hooks read", "ContractTest.test_r_s9_apply_changes_only_its_own_files_and_never_lists_a_credential_directory", [('    listable = os.path.isdir(active_hooks) and not any(part.casefold() in (".ssh", ".gnupg") for part in active_hooks.split(os.sep))\n', "    listable = os.path.isdir(active_hooks)\n")]),
]

FIRST_FAILURE = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+)\)", re.MULTILINE)
SUITE_MODULE = SUITE.removesuffix(".py").replace("/", ".")


def stage(tmp: Path) -> None:
    """Mirror the files the suite needs: the suite, the env helper and the tool."""
    for rel in (SCRIPT, SUITE, "tests/redacted_env.py", "tests/__init__.py"):
        if not (REPO / rel).exists():
            continue
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def run_tests(tmp: Path, target: str) -> tuple[bool, str]:
    """(passed, first failing test) for a suite path or a dotted test id. Fail-fast: one failure kills."""
    proc = subprocess.run([sys.executable, "-m", "unittest", "-f", target], cwd=tmp, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    match = FIRST_FAILURE.search(proc.stderr)
    # unittest names a failure "test_x (tests.test_module.SomeTest.test_x)"; keep "SomeTest.test_x".
    first = f"{match.group(3).split('.')[-2]}.{match.group(2)}" if match else "-"
    return proc.returncode == 0, first


def main() -> int:
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    for mid, _, _, edits in MUTANTS:
        for anchor, _ in edits:
            if original.count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {original.count(anchor)} times in {SCRIPT} (need exactly 1)")
                return 2

    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        passed, first = run_tests(tmp, SUITE)
        if not passed:
            print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT} (first failure: {first})")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}", flush=True)

        survivors = 0
        pins_missed = 0
        for mid, defect, pin, edits in MUTANTS:
            mutated = original
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / SCRIPT).write_text(mutated, encoding="utf-8")
            try:
                suite_passed, first = run_tests(tmp, SUITE)
                pin_passed, _ = run_tests(tmp, f"{SUITE_MODULE}.{pin}")
            finally:
                (tmp / SCRIPT).write_text(original, encoding="utf-8")
            survivors += 1 if suite_passed else 0
            pins_missed += 1 if pin_passed else 0
            verdict = "SURVIVED" if suite_passed else "KILLED"
            pin_note = "PIN MISSED" if pin_passed else "pin kills it"
            print(f"{verdict:8} {mid:4} {defect}\n                first failure: {first}; {pin_note}: {pin}", flush=True)

    total = len(MUTANTS)
    print(f"\n{total - survivors} of {total} mutants killed by the suite; {total - pins_missed} of {total} by their own pin test alone")
    return 0 if survivors == 0 and pins_missed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
