// ---------------------------------------------------------------------------
// ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
// Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/probe_bridge.js
// Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
// Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
// Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
// Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
//   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
// Everything below this block is the lane's file, unmodified.
// ---------------------------------------------------------------------------
// Lane 10-B2 probe: run canopy's REAL browser assets (websocket_client.js, ws_dash_bridge.js) and the
// REAL extendTraces clientside callback (extracted from metrics_panel.py by probe_relay.py) on the frames
// canopy's real relay broadcast (relayed_frames.json). No socket, no network: WebSocket/XHR are inert stubs.
"use strict";
const fs = require("fs");
const vm = require("vm");
const path = require("path");
const [assetsDir, scratch] = process.argv.slice(2);

class InertWebSocket { constructor(url) { this.url = url; this.readyState = 0; } send() {} close() {} }
InertWebSocket.CONNECTING = 0; InertWebSocket.OPEN = 1; InertWebSocket.CLOSING = 2; InertWebSocket.CLOSED = 3;
class InertXHR { open() {} send() {} }

const sandbox = {
  console: { log() {}, warn() {}, error: console.error },
  setTimeout, clearTimeout, Date, JSON, Math, Map,
  WebSocket: InertWebSocket, XMLHttpRequest: InertXHR,
  location: { protocol: "http:", host: "probe.invalid" },
};
sandbox.window = sandbox;
vm.createContext(sandbox);
for (const f of ["websocket_client.js", "ws_dash_bridge.js"]) {
  vm.runInContext(fs.readFileSync(path.join(assetsDir, f), "utf8"), sandbox, { filename: f });
}

const frames = JSON.parse(fs.readFileSync(path.join(scratch, "relayed_frames.json"), "utf8"));
for (const fr of frames) sandbox.cascorWS._handleMessage(fr);   // the real client dispatch
const drained = sandbox._juniperWsDrain.drainMetrics();
console.log("bridge ring after the relayed frames:", JSON.stringify(drained.map(e => ({ epoch: e.epoch, kind: e.kind === undefined ? "<absent>" : e.kind, phase: e.phase, flatLoss: e.loss !== undefined }))));

// The extendTraces fast path, with a recording Plotly and two plot elements whose trace 0 exists.
const calls = [];
const els = {
  "probe-loss-plot": { data: [{ name: "Output Training" }, { name: "Candidate Training" }] },
  "probe-accuracy-plot": { data: [{ name: "Accuracy" }] },
};
const fnSrc = fs.readFileSync(path.join(scratch, "extend_traces_fn.js"), "utf8");
const ctx2 = {
  window: { dash_clientside: { no_update: "NO_UPDATE" } },
  document: { getElementById: (id) => els[id] },
  Plotly: { extendTraces: (el, upd, idx) => calls.push({ plot: el === els["probe-loss-plot"] ? "loss" : "accuracy", trace: idx[0], x: upd.x[0], y: upd.y[0] }) },
};
vm.createContext(ctx2);
const fast = vm.runInContext("(" + fnSrc + ")", ctx2);
for (const [label, events] of [["relayed metrics frame only", drained.filter(e => e.kind === undefined)], ["relayed initial_metrics rows only", drained.filter(e => e.kind !== undefined)]]) {
  calls.length = 0;
  fast({ events }, "probe-loss-plot", "probe-accuracy-plot");
  console.log(`extendTraces <- ${label}: ${calls.length ? JSON.stringify(calls) : "no call (nothing extended)"}`);
}
