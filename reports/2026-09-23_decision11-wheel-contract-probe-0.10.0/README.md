# Decision-11 wheel-contract probe: the published juniper-ml 0.10.0 set, 2026-09-23

**Result: 39 of 39 checks PASS and 0 FAIL across three runs (`union_A_B_BC.txt`).** Every package came
from PyPI into a clean venv. Nothing was read from a checkout.

That covers the decision-11 contract as `pip install` now serves it. The predecessor handoff
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_decision-11-re-evaluated-and-two-releases-cut.md`
§3) carried the coverage claim as unproven: the probe scored a SKIP as a pass, and the `[servers]` floor
changed after the last run.

## The instrument, and what changed in it

`util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py`, changed in the same PR as this folder:

- **SKIP no longer scores as success.** `main()` returned the FAIL count alone, so a venv holding none
  of the packages exited 0. A single run now exits non-zero when nothing PASSed, and `--strict` counts
  SKIPs. `--json-out` records a run, and `--union` merges several: a FAIL anywhere fails, and a check
  that SKIPped in **every** run is `UNCOVERED` and fails too.
- **ML-2 tested presence under a name that claims versions.** Its `want` table held versions that
  nothing compared. It also gated on `juniper-ml` alone, so a `[servers]` venv FAILed it rather than
  SKIPping. It now compares every version and gates on the client distributions.
- **ML-3 is new:** the `[servers]` floors that 0.10.0 raised, stated as behaviour. `juniper-data` is at
  or above 0.15.0, `juniper-canopy` at or above 0.8.1 and `juniper-cascor` at or above 0.11.0, and the
  installed `equities` / `equities_seq` generators are at or above 5.0.0. That makes 39 checks. The
  script held 38 when it was added (#1972, its only prior commit), although the predecessor handoff
  quoted "37".

## The three runs

| run | venv | installed from PyPI | PASS / FAIL / SKIP |
| --- | --- | --- | --- |
| A | `venvA` | `juniper-ml[clients,tools,recurrence]==0.10.0` (`freeze_A.txt`) | 19 / 0 / 20 |
| B | `venvB` | `juniper-ml[servers]==0.10.0`, plus CPU `torch` and `juniper-cascor[ml]` | 19 / 0 / 20 |
| BC | `venvB` again | B plus `juniper-ml[servers,clients]==0.10.0` (`freeze_BC.txt`) | 27 / 0 / 12 |

Python 3.12.11 in every run. Torch came from `https://download.pytorch.org/whl/cpu` (2.14.0+cpu) only
because the probe needs it importable and CUDA wheels would add about 3 GB. No check measures torch.

**B and BC ran with `LD_LIBRARY_PATH` unset** (`env -u LD_LIBRARY_PATH`). With it pointing at a foreign
libtorch, every cascor check SKIPs on `libtorch_python.so: undefined symbol: _PyCode_SetExtra`. That is
the host, not the wheel, and it is the reason `util/isolated_stack.bash` launches cascor with
`LD_LIBRARY_PATH=`. The first B run hit this. Its record was replaced by the clean re-run, so
`probe_B.*` is the clean run.

## What the union of A and B alone says, and why it matters (juniper-ml#2062)

`union_A_B.txt` holds 36 PASS and **3 UNCOVERED**: JD-8, CC-2 and CC-3. Those are the only checks that
need a Juniper client **inside** a server venv, and `juniper-ml[servers]` does not install one:

- canopy 0.8.1 declares `juniper-cascor-client` and `juniper-data-client` only as extras, so CP-1 in
  run B reports `backend.service_backend` not importable;
- cascor 0.11.0 declares `juniper-data-client` only as an extra, so CC-2 and CC-3 cannot import
  `spiral_problem.data_provider`.

Adding `[clients]` (run BC) covers all three. juniper-ml#2062 records the gap and the owner's options.

## Findings the probe reports without failing

- **CC-5:** the published cascor 0.11.0 wheel reports `juniper_cascor.__version__ = 0.6.0`. cascor#672
  fixed that on `main`, but no release carries it yet.
- **CP-4 (defect probe):** canopy 0.8.1 imports `cassandra`, `juniper_cascor_client`,
  `juniper_data_client` and `redis`, none of which it ships as base dependencies. The two clients are
  the #2062 gap. `cassandra` and `redis` are optional backends: both imports sit in `try` / `except
  ImportError` (`backend/redis_client.py`, `backend/cassandra_client.py` in the wheel), and neither is
  declared in any extra.
- **JD-6 / JD-7 (defect probes):** the 0.15.0 wheel's HF and Kaggle stores still emit the retired
  `X_full` / `y_full` family at `generator_version="1.0.0"`. juniper-data#422 conformed them on
  `main`, and no release carries that yet either.

## Reproduce

```bash
uv venv --python 3.12 A && uv pip install --python A/bin/python "juniper-ml[clients,tools,recurrence]==0.10.0"
uv venv --python 3.12 B && uv pip install --python B/bin/python --index-url https://download.pytorch.org/whl/cpu torch \
  && uv pip install --python B/bin/python "juniper-ml[servers]==0.10.0" "juniper-cascor[ml]"
P=util/ad-hoc/2026-09-21_decision11_wheel_contract_probe.py
A/bin/python $P --json-out probe_A.json
env -u LD_LIBRARY_PATH B/bin/python $P --json-out probe_B.json
uv pip install --python B/bin/python "juniper-ml[servers,clients]==0.10.0"
env -u LD_LIBRARY_PATH B/bin/python $P --json-out probe_BC.json
python3 $P --union probe_A.json probe_B.json              # 36 PASS, 3 UNCOVERED, exit 3
python3 $P --union probe_A.json probe_B.json probe_BC.json   # 39 PASS, exit 0
```
