// ---------------------------------------------------------------------------
// ARCHIVED VERBATIM, 2026-09-24: F-CANOPY-055 round 1, Lane B: the watchdog false-fire model with no user interaction.
// Source: session 259b4d16's tmpfs scratchpad, laneB_f055.Iywb95/no_interaction_sim.js
// Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
// Status: ad-hoc -- investigation (canopy E2E arc, Phase 9 consensus). Written by a review lane
//   (a subagent), not by the orchestrator; paths and ports inside are the lane's own.
// Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
// Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9;
//   reports/e2e-canopy-2026-09-02/consensus/2026-09-23_validator_reports_phase9_round1.md
// Everything below this block is the lane's file, unmodified.
// ---------------------------------------------------------------------------
// No user interaction at all: the guarded lane + the REGISTERED status-bar watchdog (verbatim,
// from fix/fix_callbacks.json) on a 5 s slow lane, with the renderer semantics cited in the
// review (running at dispatch :818-821; evict on re-request :3027 / drop :2697-2704; completeJob
// -> runningOff for evicted responses too :925-937; re-enable restarts a 1 s setInterval).
// Reports how much wall time the bar's last APPLIED response is older than a staleness bound.
const fs = require('fs');
const dump = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const rLo = parseFloat(process.argv[3]), rHi = parseFloat(process.argv[4]);
const hours = parseFloat(process.argv[5] || '10');
const rec = dump.records.filter(r => r.output.startsWith('status-bar-interval.disabled@'));
const fnName = rec[0].clientside.function_name;
const script = dump.inline_scripts.filter(s => s.includes(fnName))[0];
let nowMs = 0;
global.window = {dash_clientside: {no_update: 'NU'}};
Date.now = () => nowMs;
eval(script);
const wd = window.dash_clientside._dashprivate_clientside_funcs[fnName];

function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rand = rng(2055);
const H = hours * 3600;
let t = 0;
const fetches = [];
let watched = null;
let enabled = true, tickAt = 1.0;
let nextSample = 5.0;
let lastApplied = 0;
let fires = 0, evictions = 0, applied = 0;
const staleBounds = [10, 20, 60];
const staleTime = {10: 0, 20: 0, 60: 0};
let darkStart = null; const dark = [];
function advance(to) {
  // integrate staleness between t and `to`
  for (const b of staleBounds) {
    const s0 = Math.max(t, lastApplied + b);
    if (to > s0) staleTime[b] += to - s0;
  }
  t = to;
}
while (t < H) {
  let nextEnd = Infinity, idx = -1;
  for (let i = 0; i < fetches.length; i++) if (!fetches[i].done && fetches[i].end < nextEnd) { nextEnd = fetches[i].end; idx = i; }
  const nextTick = enabled ? tickAt : Infinity;
  const tNext = Math.min(nextEnd, nextTick, nextSample);
  advance(tNext);
  if (tNext === nextSample) {
    nowMs = Math.round(t * 1000);
    const out = wd(0, !enabled, false);
    if (out === false) { fires++; if (!enabled) { enabled = true; tickAt = t + 1.0 + 0.05 * rand(); } }
    nextSample += 5.0 + 0.03 * (rand() - 0.5);
    continue;
  }
  if (tNext === nextTick) {
    if (watched !== null && !fetches[watched].done) { fetches[watched].evicted = true; evictions++; }
    fetches.push({start: t, end: t + rLo + (rHi - rLo) * rand(), evicted: false, done: false});
    watched = fetches.length - 1;
    enabled = false;
    continue;
  }
  const f = fetches[idx];
  f.done = true;
  if (idx === watched && !f.evicted) {
    applied++;
    if (darkStart !== null && t - lastApplied > 60) dark.push(t - lastApplied);
    lastApplied = t; watched = null;
  }
  if (!enabled) { enabled = true; tickAt = t + 1.0 + 0.05 * rand(); }
  if (fetches.length > 5000) { const keep = fetches.filter(x => !x.done); watched = watched === null ? null : keep.indexOf(fetches[watched]); if (watched === -1) watched = null; fetches.length = 0; fetches.push(...keep); }
  darkStart = 0;
}
dark.sort((a, b) => a - b);
console.log(`r=${rLo}-${rHi}s, ${hours} h simulated, NO user interaction:`);
console.log(`  watchdog fires: ${fires} (${(fires / hours).toFixed(1)}/h), evictions: ${evictions}, applied: ${applied}`);
for (const b of staleBounds) console.log(`  share of wall time with last applied response older than ${b}s: ${(100 * staleTime[b] / H).toFixed(1)}%`);
console.log(`  dark periods > 60 s: ${dark.length}; median ${dark.length ? dark[Math.floor(dark.length / 2)].toFixed(0) : '-'} s; longest ${dark.length ? dark[dark.length - 1].toFixed(0) : '-'} s`);
