#!/usr/bin/env python3
"""Lane C round 3, task 1c: attack the clearing script's gates on COPIES; each attack must refuse and write nothing.

Every case runs in its own minimal scratch tree (notes/D, the wrap helper, a copy of the clearing script),
records the exit status, the decisive stderr lines and the design's sha256 before and after.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
FROZEN = S / "frozen"
D_REL = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
CLEAR = FROZEN / "util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py"
WRAP = FROZEN / "util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py"
STAGED = (S / "staged_D.md").read_text(encoding="utf-8")
SCRIPT = CLEAR.read_text(encoding="utf-8")
OUT = S / "gate_attacks"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def append_edits(script: str, code: str) -> str:
    """Insert extra edit()/fence_edit() calls right before NOTE_8A (i.e. after every shipped edit)."""
    marker = "\nNOTE_8A = f\"\"\""
    assert script.count(marker) == 1
    return script.replace(marker, "\n" + code + "\n" + marker)


def run_case(name: str, design: str, script: str, env_extra: dict[str, str] | None = None, expect_write: bool = False):
    tree = OUT / name
    if tree.exists():
        shutil.rmtree(tree)
    (tree / "notes").mkdir(parents=True)
    (tree / "util/ad-hoc").mkdir(parents=True)
    (tree / D_REL).write_text(design, encoding="utf-8")
    shutil.copy(WRAP, tree / "util/ad-hoc" / WRAP.name)
    (tree / "util/ad-hoc/clear.py").write_text(script, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "FIXFWD_PR"}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_extra:
        env.update(env_extra)
    before = sha(tree / D_REL)
    r = subprocess.run([sys.executable, "util/ad-hoc/clear.py"], cwd=tree, env=env, capture_output=True, text=True)
    after = sha(tree / D_REL)
    (tree / "stdout.txt").write_text(r.stdout)
    (tree / "stderr.txt").write_text(r.stderr)
    decisive = [ln for ln in r.stderr.splitlines() if ln.strip().startswith(("FAIL", "GATE", "FATAL", "NON-IDEMPOTENT")) or "NOTHING written" in ln or "Traceback" in ln or "SystemExit" in ln]
    if not decisive:
        decisive = r.stdout.strip().splitlines()[-1:] + r.stderr.strip().splitlines()[-2:]
    wrote = before != after
    verdict = "OK (refused, nothing written)" if (r.returncode != 0 and not wrote) else ("WROTE" if wrote else "exit 0, nothing written")
    if expect_write:
        verdict = f"(control) {'WROTE' if wrote else 'did not write'}"
    print(f"== {name}: exit={r.returncode} wrote={wrote} -> {verdict}")
    print(f"   sha256 before={before[:16]} after={after[:16]}")
    for ln in decisive[:6]:
        print(f"   | {ln}")
    return r, wrote


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # --- control: the unmodified script on the staged design writes (and matches the frozen D) ---
    r, wrote = run_case("control_unmodified", STAGED, SCRIPT, expect_write=True)
    ctl = OUT / "control_unmodified" / D_REL
    print(f"   control output == frozen D: {sha(ctl) == sha(FROZEN / D_REL)}")

    # --- (a) anchors ---
    a1 = STAGED.replace("the next action in this arc is the follow-up change that clears the STOP block", "the next action in this arc is the follow-up change which clears the STOP block", 1)
    assert a1 != STAGED
    run_case("a1_anchor_missing_in_design", a1, SCRIPT)
    a2 = SCRIPT.replace('"### P0.5b — immediately after P0 step 8, same session",', '"### P0.5b — immediately after P0 step 8, same session (X)",', 1)
    assert a2 != SCRIPT
    run_case("a2_anchor_altered_in_script", STAGED, a2)
    heading = "### P0.5b — immediately after P0 step 8, same session"
    assert STAGED.count(heading) == 1
    a3 = STAGED.replace(heading, heading + "\n\n" + heading, 1)
    run_case("a3_anchor_twice_in_design", a3, SCRIPT)

    # --- (b) a prose edit strays into a fenced block ---
    inside = 'readonly CRED_NAME="settings-key"'
    print(f"   [b1 anchor count in staged D: {STAGED.count(inside)}]")
    b1 = append_edits(SCRIPT, f"edit('stray into the wrapper block', {inside!r}, {inside.replace('settings-key', 'settings-key2')!r})")
    run_case("b1_prose_edit_inside_tagged_block", STAGED, b1)
    b2 = append_edits(SCRIPT, "edit('stray into the DECLARED fence (info string)', '   ```text\\n   url=\"$(python3', '   ```bash\\n   url=\"$(python3')")
    run_case("b2_second_change_inside_declared_fence", STAGED, b2)
    b3 = append_edits(SCRIPT, "edit('prose edit that adds a fence', 'Require exit 0: it is', '```text\\nnew fence\\n```\\n\\nRequire exit 0: it is')")
    run_case("b3_prose_edit_adds_a_fence", STAGED, b3)
    # a prose edit that swallows a closing fence line (the 7.3.5 contract's closing fence + the next prose line)
    b4 = append_edits(SCRIPT, "edit('prose edit that removes the declared fence closer', '/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo \"guard exit=$?\"\\n   ```\\n', '/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo \"guard exit=$?\"\\n')")
    run_case("b4_prose_edit_removes_a_fence_line", STAGED, b4)

    # --- (c) the declared fence edit's text ---
    c1 = SCRIPT.replace("\n# --------------------------------------------------------------------------------------------\n# Sections 11 and 12",
                        "\nFENCE_EDITS[-1] = (FENCE_EDITS[-1][0], FENCE_EDITS[-1][1].replace('REFUSE:', 'REFUSED:'))\n# --------------------------------------------------------------------------------------------\n# Sections 11 and 12", 1)
    assert c1 != SCRIPT
    run_case("c1_declared_text_differs_from_applied", STAGED, c1)
    c2 = SCRIPT.replace("\n# --------------------------------------------------------------------------------------------\n# Sections 11 and 12",
                        "\n_i = [i for i, e in enumerate(EDITS) if e[0].startswith('P0 step 10: the guard dry-run')][0]\nEDITS[_i] = (EDITS[_i][0], EDITS[_i][1], EDITS[_i][2].replace('gave no TargetURL', 'gave no URL'), EDITS[_i][3])\n# --------------------------------------------------------------------------------------------\n# Sections 11 and 12", 1)
    assert c2 != SCRIPT
    run_case("c2_applied_text_differs_from_declared", STAGED, c2)
    c3 = STAGED.replace('yamaguchi_server_api.py export <id> \\\n       | python3', 'yamaguchi_server_api.py export <ID> \\\n       | python3', 1)
    assert c3 != STAGED
    run_case("c3_upstream_changed_the_declared_fence", c3, SCRIPT)
    c5 = append_edits(SCRIPT, "fence_edit('declared fence edit whose anchor is PROSE', 'Require exit 0: it is', 'Require exit zero: it is')")
    run_case("c5_declared_fence_edit_anchor_in_prose", STAGED, c5)

    # --- (d) the fix-forward placeholder ---
    run_case("d1_FIXFWD_placeholder", STAGED, SCRIPT, {"FIXFWD_PR": "ml#FIXFWD"})
    r, wrote = run_case("d2_FIXFWD_empty", STAGED, SCRIPT, {"FIXFWD_PR": ""}, expect_write=True)
    if wrote:
        t = (OUT / "d2_FIXFWD_empty" / D_REL).read_text(encoding="utf-8")
        print(f"   d2: 'Since  an absent id' present: {'Since  an absent id' in t}; 'fix-forward ,' present: {'fix-forward ,' in t or 'fix-forward  ' in t}")
    r, wrote = run_case("d3_FIXFWD_explicit_ml2134", STAGED, SCRIPT, {"FIXFWD_PR": "ml#2134"}, expect_write=True)
    print(f"   d3 output == frozen D: {sha(OUT / 'd3_FIXFWD_explicit_ml2134' / D_REL) == sha(FROZEN / D_REL)}")
    r, wrote = run_case("d4_FIXFWD_lowercase_placeholder", STAGED, SCRIPT, {"FIXFWD_PR": "ml#fixfwd"}, expect_write=True)

    # --- (e) the other gates, for completeness ---
    e1 = append_edits(SCRIPT, "edit('table row pushed over 512', '| AC-6 | **(Provable the day after P0', '| AC-6 | ' + 'x' * 600 + ' **(Provable the day after P0')")
    run_case("e1_table_row_over_width", STAGED, e1)
    e2 = append_edits(SCRIPT, "edit('reintroduce a stale phrase', 'but it is also not runnable before step 10.', 'but it is also not runnable before step 10 (one-`mv` key swap).')")
    run_case("e2_stale_phrase_reintroduced", STAGED, e2)
    e3 = append_edits(SCRIPT, "edit('non-idempotent', 'step 10.', 'step 10. step 10.')")
    run_case("e3_old_substring_of_new", STAGED, e3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
