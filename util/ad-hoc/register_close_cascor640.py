#!/usr/bin/env python3
"""
Close APD-CASCOR-009 / -010 / -012 against juniper-cascor#640, and record what it did to -011.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — one-off (refuses until cascor#640 reads MERGED)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-cascor#640; util/ad-hoc/register_round38_round2_fixes.py (which filed these rows);
         HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md

Four touches each (none of the three has a §3 detail entry): the §4.9 table row, a §5.1
verification row, the §2 status line, and the header date -- the protocol in §1 of the register.

`APD-CASCOR-011` is NOT closed. cascor#640 took a third path on it: the flag stays, and its
`--help`, a WARNING and the docs now say what it does and does not affect. The parked question was
*drop it or rewire the path*, and that is still owed a ruling, so the row stays open with what
shipped recorded on it.

On the authority for actioning these at all: the four cascor follow-ups were named as remaining
work in the Overtoad's own commissioning message for this arc (2026-09-08), which is an Overtoad
instruction. That is a different thing from the withdrawn §2 note, which tried to derive a licence
from a machine-written handoff citing a machine-written PR body -- see the note in §2.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PR = "[juniper-cascor#640](https://github.com/pcalnon/juniper-cascor/pull/640)"

state = json.loads(
    subprocess.run(
        ["gh", "pr", "view", "640", "--repo", "pcalnon/juniper-cascor", "--json", "state,mergedAt,mergeCommit"],
        check=True, capture_output=True, text=True,
    ).stdout
)
if state["state"] != "MERGED":
    sys.exit(f"REFUSED: cascor#640 is {state['state']}, not MERGED")
print(f"cascor#640 MERGED {state['mergedAt']} {state['mergeCommit']['oid'][:7]}")

text = REG.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n} for:\n---\n{old[:200]}\n---")
    text = text.replace(old, new)
    print(f"  ok  {label}")


# ---- 1. The three §4.9 table rows. -----------------------------------------------------------
sub("| APD-CASCOR-009 | `_auto_start_training` fetches the dataset",
    f"| APD-CASCOR-009 | **FIXED ({PR})** — `_auto_start_training` fetches the dataset",
    "§4.9 row -009")
sub("| APD-CASCOR-010 | `get_metrics()` / `/v1/metrics` carry no shortfall annotation",
    f"| APD-CASCOR-010 | **FIXED ({PR})** — `get_metrics()` / `/v1/metrics` carried no shortfall annotation",
    "§4.9 row -010")
sub("| APD-CASCOR-012 | No operator-facing document names",
    f"| APD-CASCOR-012 | **FIXED ({PR})** — no operator-facing document named",
    "§4.9 row -012")

# ---- 2. -011 keeps its row, gains what shipped. -----------------------------------------------
sub("*(Corrected 2026-09-09: `spiral` is fetched over HTTP through `JuniperDataClient`, not in-process as this row first said; what makes the flag inert is that the generator is hardcoded, not that the data is local.)*",
    "*(Corrected 2026-09-09: `spiral` is fetched over HTTP through `JuniperDataClient`, not in-process as this row first said; what makes the flag inert is that the generator is hardcoded and `spiral` is not truncatable, not that the data is local. "
    f"{PR} shipped a third option — the flag is kept and its `--help`, a WARNING on use, and the operator docs now state what it does and does not affect — so the inertness is no longer silent. "
    "The row stays OPEN because the parked question is *drop the flag or rewire the path*, and that is still owed a ruling.)*",
    "-011 records what shipped")

# ---- 3. The park block: the three closed rows leave it. ---------------------------------------
sub("- `APD-CASCOR-009`, `APD-CASCOR-010`, `APD-CASCOR-012` — **actionable**; one PR, the cascor#624 follow-ups.\n",
    "- `APD-CASCOR-009`, `APD-CASCOR-010`, `APD-CASCOR-012` — **closed 2026-09-09** by cascor#640, built under the\n"
    "  Overtoad's commissioning instruction for this arc, which named the four cascor follow-ups as remaining work.\n"
    "  That is an Overtoad instruction and is the only thing that licensed the work; it is **not** the withdrawn\n"
    "  §2 reasoning, which tried to derive a licence from a handoff.\n",
    "park block updated")

# ---- 4. The §2 status line. -------------------------------------------------------------------
sub("sixteen filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038` ([juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388)) and `APD-CASCOR-007` ([juniper-cascor#633](https://github.com/pcalnon/juniper-cascor/pull/633)) are FIXED and thirteen are open — **30 open in all**, 17 primer + 13 post-primer.",
    "sixteen filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038` ([juniper-data#388](https://github.com/pcalnon/juniper-data/pull/388)), `APD-CASCOR-007` ([juniper-cascor#633](https://github.com/pcalnon/juniper-cascor/pull/633)) "
    f"and `APD-CASCOR-009` / `APD-CASCOR-010` / `APD-CASCOR-012` ({PR}) are FIXED and ten are open — **27 open in all**, 17 primer + 10 post-primer.",
    "§2 status line")

# ---- 5. §5.1 verification rows. ---------------------------------------------------------------
start = text.index("### 5.1 ")
sep = "| --- | --- | --- | --- |\n"
at = text.index(sep, start) + len(sep)
rows = (
    f"| APD-CASCOR-009 | `_auto_start_training` fetched its own dataset, so an auto-started run on partial data reported `dataset_shortfall: null`, forwarded no opt-in, and swallowed its failure | {PR} | The stance resolution is now one shared static helper, `_resolve_truncation_stance`, which `_reload_dataset` also delegates to — the two had already drifted apart once. Auto-start forwards the deployment opt-in only when the caller is silent, annotates the run through `_build_dataset_shortfall` with the right `acceptance_source`, and logs a refusal at ERROR with the remedy. All three give-up paths now set `_auto_start_failure`, surfaced as `auto_start_failure` on `get_status()`: a field named for a failure that stays `null` while the failure sits in a log is the denial cascor#633 removed. 23 arms in the new `test_auto_start_shortfall.py`. |\n"
    f"| APD-CASCOR-010 | `get_metrics()` / `/v1/metrics` carried no shortfall annotation | {PR} | `dataset_shortfall` added to the returned dict, `None` when clean, so a metric read carries the mark of the data behind it. `get_metrics_history` deliberately unchanged (its rows are per-epoch). The golden snapshot `metrics_post_train.json` is an exact-compare fixture of that payload and was recaptured — it is triple-gated behind `--slow --integration --golden` and silently skips otherwise, which is how a change here can look clean and break the golden lane. |\n"
    f"| APD-CASCOR-012 | No operator-facing document named the truncation knob | {PR} | `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS` added to `AGENTS.md`'s env table and `.env.example`, and both `/v1/training/status` and `/v1/metrics` field lists in `docs/api/JUNIPER_CASCOR_API_REFERENCE.md` updated for the annotation. The `--help` text was corrected in the same PR after review: it had explained the flag's inertness on `main.py` by saying the spiral data is generated locally and juniper-data is never contacted, which is false — `main.py` health-checks the service and refuses to start without it. The true reason is that `spiral` is not a truncatable generator. |\n"
)
text = text[:at] + rows + text[at:]
print("  ok  three §5.1 verification rows")

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
raise SystemExit(crosscheck(text))
