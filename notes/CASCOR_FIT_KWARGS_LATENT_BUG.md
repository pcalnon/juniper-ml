# Latent bug — `TrainingParams` fields silently break `start_training`

**Status**: Documented • **Date**: 2026-04-30 • **Discovered**: during Phase 6E Sprint A-1 wire-through • **Severity**: Low–Medium

## TL;DR

`POST /v1/training/start` accepts a typed `TrainingParams` body with 13+
fields, validates them through Pydantic, and passes them straight
through to `CascadeCorrelationNetwork.fit(**kwargs)`. But `fit()` only
accepts a narrow signature: `max_epochs, epochs, max_iterations,
early_stopping`. **Any other `TrainingParams` field — `learning_rate`,
`candidate_pool_size`, `patience`, `optimizer_type`, etc. — causes
`TypeError: fit() got an unexpected keyword argument`** at runtime.

The training thread catches the exception, transitions the FSM to
`Failed`, and broadcasts the error. But the API request returns
**HTTP 200**, so callers see "training_started" success even though
training will instantly fail. **It's a latent bug because no integration
test exercises the failure path** — every existing test either mocks
the lifecycle or restricts itself to the four valid kwargs.

Canopy is unaffected (it applies params via `set_params` over WS, which
goes through `update_params`'s setattr loop — not through the start
path's kwarg-passthrough). The bug bites direct API consumers and
any future tooling that uses `POST /v1/training/start` with a populated
`params:` body.

## Reproduction

```bash
# Network already created.
curl -X POST http://localhost:8201/v1/training/start \
  -H "Content-Type: application/json" \
  -d '{
    "inline_data": {"train_x": [[0,0]], "train_y": [[0]]},
    "params": {"learning_rate": 0.01}
  }'
# → HTTP 200 {"status": "training_started"}

# Then immediately:
curl http://localhost:8201/v1/training/status
# → state: "Failed", error: "fit() got an unexpected keyword argument 'learning_rate'"
```

## Code-path trace

Verified 2026-04-30:

| Step | File:line | What happens |
|---|---|---|
| 1 | `juniper-cascor/src/api/routes/training.py:62` | `kwargs.update(body.params.model_dump(exclude_none=True))` — the full TrainingParams dict lands in `kwargs` |
| 2 | `juniper-cascor/src/api/routes/training.py:68` | `lifecycle.start_training(x=..., **kwargs)` — full kwargs forwarded |
| 3 | `juniper-cascor/src/api/lifecycle/manager.py:635` | `start_training(**kwargs)` accepts via `**kwargs` |
| 4 | `juniper-cascor/src/api/lifecycle/manager.py:678` | `self._executor.submit(self._run_training, ..., **kwargs)` — submitted to background thread |
| 5 | `juniper-cascor/src/api/lifecycle/manager.py:351–387` | `monitored_fit` wrapper accepts `**kwargs` and forwards transparently |
| 6 | `juniper-cascor/src/api/lifecycle/manager.py:689` | `self.network.fit(x, y, x_val=..., y_val=..., **kwargs)` |
| 7 | `juniper-cascor/src/cascade_correlation/cascade_correlation.py:1378–1388` | `def fit(self, x_train, y_train, x_val=None, y_val=None, max_epochs=None, epochs=None, max_iterations=None, early_stopping=True)` — **no `**kwargs`**, raises `TypeError` for any extra |

The exception is caught by the lifecycle's training-thread error handler
(`monitored_fit` wraps the call), which transitions the FSM and broadcasts
the failure. The HTTP request has already returned 200 by then.

## Why no test catches it

`src/tests/unit/api/test_training_route_coverage.py:196–214` is the
closest test — it constructs a `TrainingParams` body with `learning_rate`
and `patience`, then asserts `lifecycle.start_training` was called with
the right kwargs. But it **mocks the lifecycle**, so the kwargs never
reach `fit()`. The TypeError-at-fit boundary is not exercised.

No end-to-end test:

- POSTs to `/v1/training/start` with a populated `params:` body
- AND lets training actually run to completion
- AND asserts on the final state

End-to-end coverage stops at request-body schema validation (Pydantic)
or at the lifecycle-spy boundary.

## Why canopy is unaffected

`juniper-canopy/src/backend/cascor_service_adapter.py` applies parameters
via `set_params()` over the `/ws/control` WebSocket. That command
dispatches to `lifecycle.update_params(...)` (not `start_training`),
which uses `setattr(self.network, key, value)` against the
`updatable_keys` whitelist. The fit-kwarg-passthrough path is bypassed
entirely.

This is why the bug was never observed in production — every shipping
client uses the WS path. Direct REST consumers and Postman / curl tests
hit the broken path.

## Recommended fix (post-Sprint-A)

Three options, in order of preference:

### Option 1 — Filter known fit kwargs in `start_training` (recommended)

Smallest defensive patch. In `lifecycle/manager.py` `start_training()`,
strip non-fit kwargs and apply network-attribute kwargs via
`update_params`'s setattr loop **before** calling `fit`:

```python
_FIT_KWARGS = {"max_epochs", "epochs", "max_iterations", "early_stopping"}

def start_training(self, x=None, y=None, x_val=None, y_val=None, **kwargs):
    ...
    # Apply network-attribute kwargs in-place so the next fit pass sees them.
    network_kwargs = {k: v for k, v in kwargs.items() if k not in _FIT_KWARGS}
    if network_kwargs:
        self.update_params(network_kwargs)  # uses the existing whitelist + rollback

    # Forward only fit-compatible kwargs.
    fit_kwargs = {k: v for k, v in kwargs.items() if k in _FIT_KWARGS}
    self._training_future = self._executor.submit(
        self._run_training, self._train_x, self._train_y,
        self._val_x, self._val_y, **fit_kwargs,
    )
```

**Pros**: contained to lifecycle; reuses the proven `update_params`
path; rejects unknown keys via the existing whitelist; fit signature
stays.

**Cons**: silently widens what `start_training` will accept (anything in
`updatable_keys` flows through). Mostly fine since `TrainingParams`
already does Pydantic validation.

### Option 2 — Add `**kwargs` to `fit()` and ignore unknown

```python
def fit(self, x_train, y_train, ..., **kwargs):
    if kwargs:
        self.logger.debug("fit: ignoring unrecognized kwargs %s", list(kwargs))
```

**Pros**: smallest patch.

**Cons**: silently swallows typos at the network boundary. Hides
configuration mistakes that would now report as "training succeeded"
but with the wrong settings.

### Option 3 — Apply kwargs to network attributes inside `_run_training`

Same idea as Option 1 but at the thread boundary. Slightly more code
churn, no real advantage over Option 1.

## Recommended PR scope

A single small PR after Sprint A wraps:

1. Adopt **Option 1** in `lifecycle/manager.py`.
2. Add an **end-to-end test** in
   `src/tests/unit/api/test_training_route_coverage.py` that:
   - POSTs `/v1/training/start` with `params: {"learning_rate": 0.005}`
   - Asserts `lifecycle.network.learning_rate == 0.005` after the call
3. Add a regression test that catches the original failure: with the
   pre-fix code, this test fails with `TypeError`.
4. Reference back to this notes doc in the PR description.

Estimated scope: ~30 LoC + ~80 LoC tests. Small.

## Test gap to close in CI

Beyond the specific fix above, there's a broader coverage gap: cascor
has no integration test that POSTs `/v1/training/start` with a populated
`params:` body and lets training finish. Adding even one such test
(against a 2x2 synthetic dataset, max_iterations=1, max_epochs=10) would
have caught this bug at the original PR. Worth adding to CI as a
guardrail when Sprint D-1 (CAS-005 shared-code) lands.

## Decision points for the user

1. **Schedule** — fix this immediately as a Sprint-A-orthogonal PR, or
   defer to post-Sprint-A cleanup? My lean: defer. Canopy works; direct
   API users haven't reported it; Sprint A-2's optimizer surface is more
   leverage-y than fixing the latent path.
2. **Option 1 vs. 2** — explicit filter (1) or `**kwargs`-tolerance (2)?
   My lean: Option 1. Hides less; reuses proven path; faster failure
   on typos.
3. **End-to-end CI test** — add as part of the fix PR, or as a separate
   "increase integration coverage" PR? My lean: bundle with the fix so
   the regression-protection lives next to the fix.
