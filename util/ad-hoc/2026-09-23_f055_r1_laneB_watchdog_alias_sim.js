// ---------------------------------------------------------------------------
// ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: the strand watchdog's sampling-alias model.
// Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/watchdog_alias_sim.js
// Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
// Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
//   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
// Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
// Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
//   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
// Everything below this block is the lane's file, unmodified.
// ---------------------------------------------------------------------------
// Drive the REGISTERED status-bar strand watchdog (verbatim inline script from the built fix
// app, fix/fix_callbacks.json) with a HEALTHY lane: every request completes, none strands.
// Any `false` it returns is therefore a false fire.
//
// Lane model (per request): disabled for r ~ U(rLo, rHi) seconds (dispatch -> completeJob),
// then enabled for w = 1.0 s (dcc.Interval restarts setInterval on re-enable: first tick at
// +interval, Interval.react.js handleTimer) + promotion delay ~ U(0, 0.05) s.
// Sampler: slow-update-interval, 5.0 s period, each sample delayed by U(0, 0.03) s.
// A fire "evicts" if the in-flight request still has > (1.0 s + promotion) to run: the tick
// that the re-enable schedules then requests the feeder while it is `watched`.
const fs = require('fs');
const dump = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const rec = dump.records.filter(r => r.output.startsWith('status-bar-interval.disabled@'));
if (rec.length !== 1) throw new Error('watchdog not found');
const fnName = rec[0].clientside.function_name;
const script = dump.inline_scripts.filter(s => s.includes(fnName))[0];

let now = 0;
global.window = {dash_clientside: {no_update: 'NU'}};
Date.now = () => now;
eval(script);
const fn = window.dash_clientside._dashprivate_clientside_funcs[fnName];

// deterministic PRNG (mulberry32) so the table is reproducible
function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

function run(rLo, rHi, hours, seed, extraEnabled = 0.0) {
  const rand = rng(seed);
  window.__statusBarDisabledSince = null;
  const horizon = hours * 3600;
  // build the lane timeline: list of [disabledStart, disabledEnd]
  const flights = [];
  let t = 0;
  while (t < horizon + 60) {
    const r = rLo + (rHi - rLo) * rand();
    flights.push([t, t + r]);
    t = t + r + 1.0 + extraEnabled * rand() + 0.05 * rand();
  }
  let k = 0, fires = 0, evicting = 0;
  const firstFire = [];
  for (let s = 5.0; s < horizon; s += 5.0) {
    const ts = s + 0.03 * rand();
    while (k < flights.length && flights[k][1] < ts) k++;
    const f = flights[k];
    const disabled = f && f[0] <= ts && ts < f[1];
    now = Math.round(ts * 1000);
    const out = fn(0, disabled, false);
    if (out === false) {
      fires++;
      if (firstFire.length < 1) firstFire.push(ts);
      if (disabled && f[1] - ts > 1.0) evicting++;
    }
  }
  return {fires, evicting, perHour: +(fires / hours).toFixed(2), evictingPerHour: +(evicting / hours).toFixed(2), firstFireAt_s: firstFire.length ? +firstFire[0].toFixed(1) : null};
}

const cases = [[0.2, 1.2], [1.0, 2.0], [1.5, 3.1], [3.0, 5.0], [5.0, 7.0], [6.9, 7.6], [7.0, 8.0]];
console.log('rLo-rHi(s)  cycle(s)   fires/h  evicting/h  first-fire(s)   [10 h simulated per row, seed 7]');
for (const [lo, hi] of cases) {
  const res = run(lo, hi, 10, 7);
  console.log(`${lo.toFixed(1)}-${hi.toFixed(1)}     ~${((lo + hi) / 2 + 1.03).toFixed(1)}      ${String(res.perHour).padStart(6)}   ${String(res.evictingPerHour).padStart(8)}     ${res.firstFireAt_s}`);
}
console.log('');
console.log('sensitivity at r = 6.9-7.6 s: enabled window = 1.0 s + U(0, X) s (tick->dispatch delay on a loaded page)');
for (const x of [0.0, 0.5, 1.0, 2.0, 3.0]) {
  const res = run(6.9, 7.6, 10, 11, x);
  console.log(`  X=${x.toFixed(1)}  fires/h=${res.perHour}  evicting/h=${res.evictingPerHour}`);
}
