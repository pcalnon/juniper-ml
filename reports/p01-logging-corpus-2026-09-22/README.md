# P0.1 / P0.2 — the post-merge logging corpus, and decision 1's gate

**Arc**: [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573).
**Roadmap**: [`notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`](../../notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md) §3 (P0.1, P0.2) and §13.1 decision 1.
**Taken**: 2026-09-22, cascor `8065ca0f` — i.e. **after** every Phase 1 merge (#644, #647, #648, #652, #653, #667, #670).

## The gate

Decision 1 pre-authorised a **10 %** threshold: below it P2 is cancelled and recorded as cancelled;
at or above, it runs.

> **Measured: 16.70 % → P2 RUNS.**

| | |
| --- | --- |
| worker self time (sum of `tottime`, 32 profiles) | **37.00 s** |
| attributable logging self time | **6.18 s** over 4,938,286 calls |
| **share** | **16.70 %** |

**What that number is, precisely.** It is the share the instrument can *attribute* — functions whose
own `tottime` is logging work. §3.1's acceptance caveat is load-bearing and still applies: f-string
*construction* cost for discarded records is inline in each calling function's own self time and is
**not separately attributable** from this corpus. So 16.70 % is a **lower bound** on total logging
cost. Decision 1 says the threshold is "measured on what the instrument can attribute", so this is
the figure it asked for — but do not restate it as "logging costs 16.7 %".

## The finding that did not survive contact with the re-baseline

August's headline (`JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md` §3) was that
the `Tensor.__format__` chain cost **27.98 s cumulative over 1.81 M calls, 33 %**, and that it came
from one line in `candidate_unit.py:_display_training_progress`.

**It is now 0.13 s over 2,912 calls.** Two shipped changes account for it: cascor#598's
`_tensor_brief`, and P1.4 (#670) guarding the three per-epoch sites in that same function.

The consequence for the roadmap is that **the cost has moved**. It is no longer in call-site message
construction; it is in the logger internals, which is P2/P3 territory:

| function | self time | calls |
| --- | ---: | ---: |
| `_log_at_level` | 1.024 s | 611,871 |
| `_filter_by_level` | 0.692 s | 611,870 |
| `currentframe` (eager, **paid on every call incl. discarded**) | 0.507 s | 611,870 |
| `_console_dict` | 0.506 s | 58,399 |
| `_frame_info` | 0.480 s | 116,798 |

`currentframe` at 611,870 calls is the eager `_frm()` evaluated as an *argument* at
`logger.py:620`, before `_log_at_level` reaches its level test — recorded as **NOT DONE** in
`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`.

## Cell identity (P0.1(c))

`cell.yaml` here is the cell **verbatim**, and `provenance.json` embeds it as a string as well as
naming its path. That is deliberate: the 2026-08-26 corpus recorded only a *path*, into
`~/.local/state`, which is neither version-controlled nor durable. A path is not an identity.

The cell is `util/ad-hoc/2026-09-22_p01_logging_corpus_cell.yaml`, and it is **not** the August
cell. **The August cell can no longer run**, and both ways it fails are worth knowing:

1. It carries `train_ratio: 0.8` / `test_ratio: 0.2` and no `val_ratio`, from before the val split.
   juniper-data now defaults `val_ratio: 0.1`, so the request sums to 1.1 and is refused with
   *"train_ratio (0.8) + val_ratio (0.1) + test_ratio (0.2) must be <= 1.0, got 1.1"*.
2. Setting `val_ratio: 0.0` gets past juniper-data, which emits an **empty** `X_val` — and then
   cascor refuses it at `cascade_correlation.py:1671`,
   *"ValidationError: Parameter 'x_val' cannot be an empty tensor"*.

So the CLI tolerates a **missing** val (`data_provider.py` keeps `X_val` out of `required_keys`,
design §6a) but **not an empty** one. Those are different states and only the first is tolerated.

The split used is `0.8 / 0.1 / 0.1` — train held at August's value, val carved out of **test**,
because the quantity measured is logging's share of *worker* self time and workers train candidates.

**This is a RE-BASELINE, not a repeat.** The generator version has moved since August (the `*_full`
retirement and the val split both bumped it), so `dataset_id` differs and the artifacts are not
byte-identical even at the same seed. Say so when comparing against the 2026-08-26 corpus.

## Files

| file | what |
| --- | --- |
| `provenance.json` | cascor sha, arm, bound, start time, Phase 1 PR list, and the cell verbatim |
| `cell.yaml` | the cell as run |
| `p02_logging_share_decomposition.txt` | P0.2 — the 16.70 % and its components |
| `format_caller_attribution.txt` | `Tensor.__format__` caller attribution (now 0.13 s) |
| `filter_by_level_attribution.txt` | `_filter_by_level` caller attribution |
| `prof_manifest.txt` | the 32 `.prof` files, sizes and names |

**The raw 32 `.prof` blobs are NOT in git** (2.0 MB of binary). They live at
`~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof/`, which is **not backed up and
not durable** — `prof_manifest.txt` is what survives. Re-create with
`util/ad-hoc/2026-09-22_p01_logging_corpus_run.bash`, which is reproducible from this cell.

## Reproducing

```bash
bash util/ad-hoc/2026-09-22_p01_logging_corpus_run.bash \
    <cascor-worktree>/src \
    util/ad-hoc/2026-09-22_p01_logging_corpus_cell.yaml \
    ~/.local/state/juniper-experiments/<NEW-out-root> 360

python util/ad-hoc/2026-09-22_p02_logging_share_decompose.py <out-root>/prof
```

The runner refuses a cascor tree that does not contain `8065ca0`, so it cannot silently produce a
pre-merge corpus. **Check the profile count** — the run exits 0 whether or not any profile was
written, and a zero-profile corpus is a hollow result, not a measurement. Two earlier attempts on
2026-09-22 produced exactly that, and only the control caught it.
