// ---------------------------------------------------------------------------
// ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
// Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/extend_traces_fn.js
// Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
// Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
// Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
// Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
//   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
// Everything below this block is the lane's file, unmodified except for trailing whitespace and the final
// newline, which this repo's pre-commit hooks normalize.
// ---------------------------------------------------------------------------

            function(wsBuffer, lossId, accId) {
                if (!wsBuffer || !wsBuffer.events || wsBuffer.events.length === 0) {
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update];
                }
                var events = wsBuffer.events;
                var epochs = [], losses = [], accuracies = [];
                var valEpochs = [], valLosses = [], valAccs = [];
                // N9 (C7/U-4): parallel arrays for the scalar classification
                // metrics, pushed under the SAME gate as loss/accuracy so every
                // series stays x-aligned with accuracy trace 0 (a length skew
                // would silently mis-append WS points). null => gap, never 0.
                var f1s = [], precisions = [], recalls = [], rocAucs = [];
                for (var i = 0; i < events.length; i++) {
                    var e = events[i];
                    var epoch = e.epoch || e.current_epoch || i;
                    var loss = e.loss || e.error || e.current_error;
                    var acc = e.accuracy || e.correct_percentage;
                    if (loss !== undefined && loss !== null) {
                        epochs.push(epoch);
                        losses.push(loss);
                        accuracies.push(acc !== undefined && acc !== null ? acc : 0);
                        // N9 (C7/U-4): read each scalar flat off the frame under
                        // the loss gate; null (missing / candidate phase / the
                        // ~every-25th-epoch sparsity) becomes a gap, not a zero.
                        f1s.push((e.f1 !== undefined && e.f1 !== null) ? e.f1 : null);
                        precisions.push((e.precision !== undefined && e.precision !== null) ? e.precision : null);
                        recalls.push((e.recall !== undefined && e.recall !== null) ? e.recall : null);
                        rocAucs.push((e.roc_auc !== undefined && e.roc_auc !== null) ? e.roc_auc : null);
                    }
                    // GAP-WS-14: collect validation values when present so the
                    // overlay traces stay in sync without forcing a rebuild.
                    var vLoss = (e.val_loss !== undefined) ? e.val_loss
                              : ((e.validation_loss !== undefined) ? e.validation_loss : null);
                    var vAcc = (e.val_accuracy !== undefined) ? e.val_accuracy
                             : ((e.validation_accuracy !== undefined) ? e.validation_accuracy : null);
                    if (vLoss !== null && vLoss !== undefined) {
                        valEpochs.push(epoch);
                        valLosses.push(vLoss);
                        valAccs.push(vAcc !== null && vAcc !== undefined ? vAcc : null);
                    }
                }
                if (epochs.length === 0 && valEpochs.length === 0) {
                    return [window.dash_clientside.no_update, window.dash_clientside.no_update];
                }

                // Locate optional traces by name. Positions vary depending on
                // whether candidate-training / validation overlays are
                // enabled in this view (GAP-WS-14).
                function findTraceIndex(el, name) {
                    if (!el || !el.data) return -1;
                    for (var k = 0; k < el.data.length; k++) {
                        if (el.data[k] && el.data[k].name === name) return k;
                    }
                    return -1;
                }

                // extendTraces on loss plot (trace 0 = Output Training)
                var lossEl = document.getElementById(lossId);
                if (lossEl && lossEl.data && lossEl.data.length > 0) {
                    if (epochs.length > 0) {
                        try {
                            Plotly.extendTraces(lossEl, {x: [epochs], y: [losses]}, [0], 5000);
                        } catch(e) {}
                    }
                    if (valEpochs.length > 0) {
                        var valLossIdx = findTraceIndex(lossEl, "Validation Loss");
                        if (valLossIdx >= 0) {
                            try {
                                Plotly.extendTraces(lossEl, {x: [valEpochs], y: [valLosses]}, [valLossIdx], 5000);
                            } catch(e) {}
                        }
                    }
                }
                // extendTraces on accuracy plot (trace 0 = Accuracy)
                var accEl = document.getElementById(accId);
                if (accEl && accEl.data && accEl.data.length > 0) {
                    if (epochs.length > 0) {
                        try {
                            Plotly.extendTraces(accEl, {x: [epochs], y: [accuracies]}, [0], 5000);
                        } catch(e) {}
                        // N9 (C7/U-4): extend each scalar series by name. Names
                        // MUST match MetricsPanel.SCALAR_SERIES display names.
                        // Absent traces (metric disabled / all-null at build
                        // time) are skipped; the 1 Hz REST rebuild adds the
                        // trace once real values land, then WS extends keep it
                        // live. Shares [epochs] so it stays aligned with acc[0].
                        var n9Series = [{n: "F1", v: f1s}, {n: "Precision", v: precisions}, {n: "Recall", v: recalls}, {n: "ROC-AUC", v: rocAucs}];
                        for (var s = 0; s < n9Series.length; s++) {
                            var n9Idx = findTraceIndex(accEl, n9Series[s].n);
                            if (n9Idx >= 0) {
                                try {
                                    Plotly.extendTraces(accEl, {x: [epochs], y: [n9Series[s].v]}, [n9Idx], 5000);
                                } catch(e) {}
                            }
                        }
                    }
                    if (valEpochs.length > 0) {
                        var valAccIdx = findTraceIndex(accEl, "Validation Accuracy");
                        if (valAccIdx >= 0) {
                            // Filter null val_accuracy values so the overlay
                            // only gains real points (the loss event may
                            // arrive before the matching accuracy).
                            var fEpochs = [], fAccs = [];
                            for (var j = 0; j < valEpochs.length; j++) {
                                if (valAccs[j] !== null && valAccs[j] !== undefined) {
                                    fEpochs.push(valEpochs[j]);
                                    fAccs.push(valAccs[j]);
                                }
                            }
                            if (fEpochs.length > 0) {
                                try {
                                    Plotly.extendTraces(accEl, {x: [fEpochs], y: [fAccs]}, [valAccIdx], 5000);
                                } catch(e) {}
                            }
                        }
                    }
                }
                return [window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
