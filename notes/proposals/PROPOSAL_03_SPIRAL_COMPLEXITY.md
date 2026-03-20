# Proposal 3: Spiral Dataset Complexity Creates Invisible Per-Unit Improvement

**Severity**: HIGH (for demo UX)
**Root Cause ID**: RC-P4

---

## Summary

The demo uses a 3-rotation spiral dataset (default from JuniperData: `n_rotations=3.0`), which requires 10-15 hidden units for good classification. Each unit contributes only ~0.001-0.003 MSE improvement — sub-pixel on the chart's default scale. The training appears stalled because the improvements are invisible, not because the algorithm is broken.

## Mechanism

- 3-rotation spiral → 6 decision boundary crossings
- Each tanh hidden unit resolves ~1 crossing
- Per-unit MSE improvement: ~0.001-0.003 (for well-trained candidates)
- Chart y-axis autoranges to [0, 1.0] → 0.002 improvement = 1 pixel on 400px chart
- Loss chart has no explicit y-axis range (unlike accuracy chart which sets [0, 1.0])

## Evidence

- `demo_mode.py` lines 595-600: `n_rotations` NOT specified in params dict
- JuniperData defaults: `SPIRAL_DEFAULT_N_ROTATIONS = 3.0`
- `metrics_panel.py` loss chart: no `yaxis.range` set (autoranges)
- Accuracy chart: explicitly sets `yaxis={"range": [0, 1.0]}`

## Comparison: 1 vs 3 Rotations

| Metric                   | 3 Rotations    | 1 Rotation          |
|--------------------------|----------------|---------------------|
| Boundary crossings       | 6              | 2                   |
| Units for >90% accuracy  | ~15-20         | 3-5                 |
| MSE improvement per unit | 0.001-0.003    | 0.01-0.04           |
| Visible on default chart | No (sub-pixel) | Yes (10-30+ pixels) |

## Proposed Fix

1. **Add `n_rotations=1.0`** to spiral params in `_generate_spiral_dataset_from_juniper_data()`
2. **Expose spiral complexity as a configurable demo parameter** (optional)
3. **Set loss chart y-axis range** based on recent loss values rather than full history autorange

## Risk Assessment

- **Very low effort**: Single-line parameter addition
- **Zero risk**: JuniperData already supports the parameter
- **High reward**: Transforms the demo from "appears broken" to "visually compelling staircase descent"

## Note

The previous plan (Phase 4) explicitly excluded this fix per user direction. The spiral retains its default complexity. However, this analysis documents the expected behavior: the algorithmic fixes must produce visible improvement ON the 3-rotation spiral, not just on simpler datasets.
