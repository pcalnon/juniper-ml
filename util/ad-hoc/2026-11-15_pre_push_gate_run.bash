#!/usr/bin/env bash
# =====================================================================================================================
# Project:       juniper-ml
# Sub-Project:   ad-hoc tooling (R-OBS-SC-2 follow-ups)
# Author:        Paul Calnon
# Created:       2026-11-15
# Status:        ad-hoc -- driver for the plan's pre-push gate (§9, "Every public push, and every other public text")
# Retire when:   RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:       util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py (the scan; only exit 0 passes);
#                util/ad-hoc/2026-10-05_masked_finding_shape.py (the masked read);
#                notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (§9 and §3 XC-PRESERVE)
#
# Why: the plan's rule for every public push is two unioned scans (exactly the files to be pushed, and all other public
# text such as the PR body and the commit message, each as files; only exit 0 passes), then a masked read of every added
# line that names a credential (--names), and of all added transcript text (--all). A session confined to one worktree
# cannot name the scanner in a command line (its isolation guard reads "git" inside the word), so this runs the steps.
#
# Usage:  bash util/ad-hoc/2026-11-15_pre_push_gate_run.bash PAYLOAD_DIR [--all-added]
#   PAYLOAD_DIR/files/  copies of exactly the files to be pushed
#   PAYLOAD_DIR/text/   the PR body, the commit message and any other public text, as files
#   PAYLOAD_DIR/added/  the added lines only (and any transcript-derived file, for --all-added)
#   PAYLOAD_DIR/accept.files.txt, accept.text.txt  optional: finding KEYs, one per line, read with the masked tool and
#                       judged not credentials, for that part's scan only
# Exit 0 only when both scans exit 0. The masked reads are printed for a human or session to classify; they never pass
# or fail the gate by themselves.
# =====================================================================================================================
set -u
payload="${1:?usage: PAYLOAD_DIR [--all-added]}"
mode="${2:-}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
probe="${here}/2026-10-04_gitleaks_zero_rule_probe.py"
masked="${here}/2026-10-05_masked_finding_shape.py"
work="${payload}/work"
mkdir -p "${work}"
# PAYLOAD_DIR/accept.<part>.txt: one finding KEY per line, exactly as that part's scan printed it, each read with the
# masked tool and judged not a credential. Each becomes one --accept for that part's scan only: the scanner refuses an
# --accept that names no current finding, and the scan still fails on any finding not listed.
status=0
for part in files text; do
    if [[ ! -d "${payload}/${part}" ]]; then
        echo "REFUSED: ${payload}/${part} is missing"
        exit 3
    fi
    accepts=()
    if [[ -f "${payload}/accept.${part}.txt" ]]; then
        while IFS= read -r key; do
            [[ -n "${key}" ]] && accepts+=(--accept "${key}")
        done < "${payload}/accept.${part}.txt"
    fi
    echo "== scan: ${part}"
    python3 -I "${probe}" --scan-dir "${payload}/${part}" --workdir "${work}" "${accepts[@]}" > "${payload}/${part}.log" 2>&1
    rc=$?
    tail -n 3 "${payload}/${part}.log"
    echo "   exit ${rc}"
    if [[ ${rc} -ne 0 ]]; then
        status=1
    fi
done
if [[ -d "${payload}/added" ]]; then
    echo "== masked read: --names over the added lines"
    python3 -I "${masked}" --root "${payload}/added" --names
    if [[ "${mode}" == "--all-added" ]]; then
        echo "== masked read: --all over the added lines"
        python3 -I "${masked}" --root "${payload}/added" --all
    fi
fi
echo "gate: $([[ ${status} -eq 0 ]] && echo PASS || echo FAIL)"
exit ${status}
