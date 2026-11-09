# Cursor Flood #4 — Disposition Render Inputs

**Project**: juniper-ml
**Author**: Paul Calnon
**Created**: 2026-11-08
**Record**: [`notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`](../../notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md) §5

---

The inputs from which the flood-4 record's §5 (per-PR disposition) is rendered, archived because their originals lived in worktree `tmp/` directories (four in the orchestrator's, two in the juniper-ml builders'), which `git worktree remove` deletes.

| File | What it is |
|---|---|
| `manifest_juniper-data_tests.json` | juniper-data tests carrier (#518): every carried draft with its outcome and evaluation, the mutations run, the checks |
| `manifest_juniper-data_docs.json` | juniper-data docs carrier (#519) |
| `manifest_juniper-canopy_tests.json` | juniper-canopy tests carrier (#797) |
| `manifest_juniper-canopy_docs.json` | juniper-canopy docs carrier (#802) |
| `manifest_juniper-ml_tests.json` | juniper-ml tests carrier (#2517) |
| `manifest_juniper-ml_docs.json` | juniper-ml docs carrier (#2519) |
| `render_config.json` | the renderer's config: the six carriers, and the rows no carrier holds (closed on a ruling, another arc's, round 3) |

Each manifest is a byte-for-byte copy of its builder's original (`util/ad-hoc/2026-11-08_flood4_archive_render_inputs.py` checks the sha256 of every copy). The rendered table truncates each evaluation at 420 characters, so a manifest holds more than §5 shows.

To re-render §5 from the repository root:

```bash
python3 util/ad-hoc/2026-11-07_flood4_disposition_render.py --config reports/2026-11-08_flood4-disposition/render_config.json
```

The renderer asks GitHub, through an authenticated `gh`, for each PR's live state and title, so a re-render shows the state at that moment, not at the record's date. Without `gh` authentication it still exits 0, but prints every carrier as "(open)" and every state as "?".

The manifests cite logs under `tmp/flood4/` as evidence (such as `claim_check.log`): the juniper-data and juniper-canopy manifests' in the orchestrator's worktree, the juniper-ml manifests' in their builders'. Those logs are not part of this archive.
