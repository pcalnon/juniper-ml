#!/usr/bin/env python3
"""
Mutation-check juniper-deploy's Helm data-egress render tests: each planted defect must turn its test red.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-deploy `tests/test_helm_networkpolicy_data_egress.py` (new) and the TCP 443 egress
         rule in `k8s/helm/juniper/templates/networkpolicy-data.yaml` (owner ruling 2026-09-24,
         the k8s half of the `data-egress` compose network).

Why: the first draft of these tests selected policies by a NAME prefix the chart never renders.
One test matched nothing and passed vacuously. The second draft (juniper-deploy#232) pinned only
the rule's exact wording, and validation lane B showed eight strictly broader rules passing it. So
each guard is proven here against a planted defect, including those eight. The script copies the tree once per mutation, rewrites one chart template (plain text, the
anchor asserted to occur exactly once), renders through the real `helm template` inside the tests,
and requires the named test to go red. The unmutated CONTROL must be green.

Usage
-----
    python3 util/ad-hoc/2026-09-24_helm_data_egress_mutation_check.py \
        --deploy-tree <path to an edited juniper-deploy tree> --python <interpreter with pytest+pyyaml>

Needs `helm` on PATH (the tests skip without it, which this script treats as a failure).
Exit 0 = control green and every mutation caught by its named test; 1 = otherwise.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_FILE = "tests/test_helm_networkpolicy_data_egress.py"
TPL = "k8s/helm/juniper/templates/"
RULE_443 = "      ports:\n        - protocol: TCP\n          port: 443\n"
DATA_END = "          port: 443\n{{- end }}"
EGRESS = "  egress:\n"

EXACT = "test_data_pod_effective_egress_is_exactly_dns_and_public_https"
OTHERS = "test_other_juniper_pods_have_no_public_or_unscoped_egress"
TOKEN = "test_data_pod_mounts_no_service_account_token"
OFF = "test_policies_off_leaves_no_policy_selecting_a_juniper_pod"
KINDS = "test_no_other_network_policy_kinds_are_rendered"
UNMODELLED = "test_render_has_no_unmodelled_constructs"
POLICY_TYPES = "  policyTypes:\n    - Ingress\n    - Egress\n"
DENY_EGRESS_BLOCK = "  egress:\n    # Allow DNS resolution\n    - ports:\n        - protocol: UDP\n          port: 53\n        - protocol: TCP\n          port: 53\n{{- end }}"
WORKER_EGRESS_BLOCK = "  egress:\n    {{- if .Values.cascor.enabled }}\n    - to:\n        - podSelector:\n            matchLabels:\n              app.kubernetes.io/component: cascor\n              app.kubernetes.io/instance: {{ .Release.Name }}\n      ports:\n        - port: {{ .Values.cascor.service.port }}\n          protocol: TCP\n    {{- end }}\n    - ports:\n        - protocol: UDP\n          port: 53\n        - protocol: TCP\n          port: 53\n{{- end }}"
DENY_NAME = '  name: {{ include "juniper.fullname" . }}-deny-all\n'
DATA_NAME = '  name: {{ include "juniper.data.fullname" . }}\n'
DATA_SELECTOR = '      {{- include "juniper.selectorLabels" (dict "ctx" . "component" "data") | nindent 6 }}\n'
CANOPY_SELECTOR = '      {{- include "juniper.selectorLabels" (dict "ctx" . "component" "canopy") | nindent 6 }}\n'
DENY_EGRESS = "  egress:\n    # Allow DNS resolution\n"
ALLOW_ALL_ON_DATA = "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: {name}\n{labels}spec:\n  podSelector:\n    matchLabels:\n      app.kubernetes.io/component: data\n  policyTypes:\n    - Egress\n  egress:\n{egress}"

# (name, template file, anchor, replacement, the test that must go red)
# M1-M5 are the first round's. M6-M13 are the eight broader rules validation lane B showed passing
# juniper-deploy#232's tests, which pinned the rule's WORDING; M14 is the same all-ports rule on the
# worker, added here. M15 is the service-account token the owner ruled off after lane B's
# API-server finding. M16-M26 are round-2 lane R2's shapes that passed #233's tests, which looked at
# ONE policy at a time where Kubernetes unions every policy selecting a pod (juniper-deploy#235 is
# the fix; test names are #235's).
MUTATIONS = [
    ("drop the data 443 rule", "networkpolicy-data.yaml", "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n", "    - to:\n        - ipBlock:\n            cidr: 10.255.255.0/24\n", EXACT),
    ("open port 80 instead of 443", "networkpolicy-data.yaml", RULE_443, RULE_443.replace("443", "80"), EXACT),
    ("stop excluding link-local", "networkpolicy-data.yaml", "              - 169.254.0.0/16\n", "", EXACT),
    ("give cascor the same rule", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n      ports:\n        - protocol: TCP\n          port: 443\n", OTHERS),
    ("render data's policy with policies off", "networkpolicy-data.yaml", "{{- if and .Values.networkPolicies.enabled .Values.data.enabled }}", "{{- if .Values.data.enabled }}", OFF),
    ("data: endPort widens 443 to every port above it", "networkpolicy-data.yaml", DATA_END, "          port: 443\n          endPort: 65535\n{{- end }}", EXACT),
    ("data: an extra 443 rule with no peers", "networkpolicy-data.yaml", DATA_END, DATA_END.replace("{{- end }}", "    - ports:\n        - protocol: TCP\n          port: 443\n{{- end }}"), EXACT),
    ("data: an extra all-ports rule to 0.0.0.0/0", "networkpolicy-data.yaml", DATA_END, DATA_END.replace("{{- end }}", "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n{{- end }}"), EXACT),
    ("cascor: all ports to 0.0.0.0/0", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n", OTHERS),
    ("cascor: 443 with no peers", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - ports:\n        - protocol: TCP\n          port: 443\n", OTHERS),
    ("cascor: 443 to ::/0", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: ::/0\n      ports:\n        - protocol: TCP\n          port: 443\n", OTHERS),
    ("cascor: 443 to two /1 halves", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/1\n        - ipBlock:\n            cidr: 128.0.0.0/1\n      ports:\n        - protocol: TCP\n          port: 443\n", OTHERS),
    ("cascor: the named port https to 0.0.0.0/0", "networkpolicy-cascor.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n      ports:\n        - protocol: TCP\n          port: https\n", OTHERS),
    ("worker: all ports to 0.0.0.0/0", "networkpolicy-worker.yaml", EGRESS, EGRESS + "    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n", OTHERS),
    ("data pod mounts a service-account token again", "data-deployment.yaml", "      automountServiceAccountToken: false\n", "", TOKEN),
    ("R2: deny-all egress gains every namespace", "networkpolicy-deny-all.yaml", DENY_EGRESS, "  egress:\n    - to:\n        - namespaceSelector: {}\n    # Allow DNS resolution\n", EXACT),
    ("R2: deny-all egress gains every pod in every namespace", "networkpolicy-deny-all.yaml", DENY_EGRESS, "  egress:\n    - to:\n        - namespaceSelector: {}\n          podSelector: {}\n    # Allow DNS resolution\n", EXACT),
    ("R2: a second juniper-labelled allow-all policy on the data pods", "networkpolicy-data.yaml", DATA_END, "          port: 443\n---\n" + ALLOW_ALL_ON_DATA.format(name="extra-data", labels="  labels:\n    app.kubernetes.io/part-of: juniper\n    app.kubernetes.io/component: data-internal\n", egress="    - {}\n") + "{{- end }}", EXACT),
    ("R2: an unlabelled allow-all policy on the data pods", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\n{{- if .Values.data.enabled }}\n" + ALLOW_ALL_ON_DATA.format(name="unlabelled-data", labels="", egress="    - {}\n") + "{{- end }}", EXACT),
    ("R2: an unlabelled all-ports ipBlock policy on the data pods", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\n" + ALLOW_ALL_ON_DATA.format(name="unlabelled-ipblock", labels="", egress="    - to:\n        - ipBlock:\n            cidr: 0.0.0.0/0\n        - ipBlock:\n            cidr: ::/0\n"), EXACT),
    ("R2: canopy's selector widened to every juniper pod", "networkpolicy-canopy.yaml", CANOPY_SELECTOR, "      app.kubernetes.io/part-of: juniper\n", EXACT),
    ("R2: the data policy selects no pod", "networkpolicy-data.yaml", DATA_SELECTOR, DATA_SELECTOR.replace('"component" "data"', '"component" "no-such-component"'), EXACT),
    ("R2: the data policy governs Ingress only", "networkpolicy-data.yaml", "    - Ingress\n    - Egress\n", "    - Ingress\n", EXACT),
    ("R2: a projected service-account token volume", "data-deployment.yaml", "      volumes:\n", "      volumes:\n        - name: sa-token\n          projected:\n            sources:\n              - serviceAccountToken:\n                  path: token\n", TOKEN),
    ("R2: a CiliumNetworkPolicy the tests cannot evaluate", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\napiVersion: cilium.io/v2\nkind: CiliumNetworkPolicy\nmetadata:\n  name: cilium-data\nspec:\n  endpointSelector: {}\n  egress:\n    - toEntities:\n        - world\n", KINDS),
    ("R2: the data policy's selector widened to every juniper pod", "networkpolicy-data.yaml", DATA_SELECTOR, "      app.kubernetes.io/part-of: juniper\n", OTHERS),
    # M27-M34: round-3 lane R3's shapes that passed #235's tests (juniper-deploy#236 is the fix).
    ("R3: an unlabelled allow-all policy on data with policyTypes: []", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\n" + ALLOW_ALL_ON_DATA.format(name="empty-types", labels="", egress="    - {}\n").replace("  policyTypes:\n    - Egress\n", "  policyTypes: []\n"), EXACT),
    ("R3: deny-all and worker policies default to Ingress-only (egress: [], no policyTypes)", [("networkpolicy-deny-all.yaml", POLICY_TYPES, ""), ("networkpolicy-deny-all.yaml", DENY_EGRESS_BLOCK, "  egress: []\n{{- end }}"), ("networkpolicy-worker.yaml", POLICY_TYPES, ""), ("networkpolicy-worker.yaml", WORKER_EGRESS_BLOCK, "  egress: []\n{{- end }}")], OTHERS),
    ("R3: the deny-all and data policies in another namespace", [("networkpolicy-deny-all.yaml", DENY_NAME, DENY_NAME + "  namespace: other\n"), ("networkpolicy-data.yaml", DATA_NAME, DATA_NAME + "  namespace: other\n")], EXACT),
    ("R3: the data Deployment in another namespace", "data-deployment.yaml", DATA_NAME, DATA_NAME + "  namespace: other\n", EXACT),
    ("R3: hostNetwork on the data pod", "data-deployment.yaml", "      automountServiceAccountToken: false\n", "      automountServiceAccountToken: false\n      hostNetwork: true\n", UNMODELLED),
    ("R3: an allow-all policy inside a List wrapper", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\napiVersion: v1\nkind: List\nitems:\n  - apiVersion: networking.k8s.io/v1\n    kind: NetworkPolicy\n    metadata:\n      name: listed\n    spec:\n      podSelector: {}\n      policyTypes:\n        - Egress\n      egress:\n        - {}\n", UNMODELLED),
    ("R3: an ungated Ingress-only policy still selecting pods with policies off", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\napiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: ungated-ingress-deny\n  labels:\n    app.kubernetes.io/part-of: juniper\nspec:\n  podSelector: {}\n  policyTypes:\n    - Ingress\n", OFF),
    ("R3: a stray Juniper-labelled Pod no policy governs", "networkpolicy-data.yaml", DATA_END, DATA_END + "\n---\napiVersion: v1\nkind: Pod\nmetadata:\n  name: stray\n  labels:\n    app.kubernetes.io/part-of: juniper\n    app.kubernetes.io/instance: someone-else\nspec:\n  containers:\n    - name: c\n      image: busybox\n", OTHERS),
]


def run_tests(tree: Path, python: str) -> subprocess.CompletedProcess:
    return subprocess.run([python, "-m", "pytest", TEST_FILE, "-q", "-p", "no:cacheprovider", "-rfs"], cwd=tree, capture_output=True, text=True, check=False)


def scratch_copy(src: Path, dst: Path) -> None:
    shutil.copytree(src / "tests", dst / "tests")
    shutil.copytree(src / "k8s", dst / "k8s")
    shutil.copy2(src / "pyproject.toml", dst / "pyproject.toml")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--deploy-tree", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    if shutil.which("helm") is None:
        print("  helm is not on PATH: the tests would skip, which proves nothing")
        return 1
    ok = True
    with tempfile.TemporaryDirectory(prefix="helm-egress-mut-") as tmp:
        control = Path(tmp) / "control"
        scratch_copy(args.deploy_tree, control)
        res = run_tests(control, args.python)
        last = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr.strip()[-200:]
        green = res.returncode == 0 and "skipped" not in last
        print(f"  CONTROL: {'green' if green else 'RED or SKIPPED'} ({last})")
        ok &= green
        for i, entry in enumerate(MUTATIONS):
            # A mutation is (name, file, anchor, replacement, test) or (name, [(file, anchor,
            # replacement), ...], test) when one defect needs edits in several templates.
            name, must_fail = entry[0], entry[-1]
            edits = entry[1] if isinstance(entry[1], list) else [(entry[1], entry[2], entry[3])]
            tree = Path(tmp) / f"m{i + 1}"
            scratch_copy(args.deploy_tree, tree)
            stopped = False
            for fname, anchor, replacement in edits:
                text = (tree / TPL / fname).read_text(encoding="utf-8")
                count = text.count(anchor)
                if count != 1:
                    print(f"  M{i + 1} {name}: ANCHOR found {count} times in {fname} -- stopped, nothing mutated")
                    stopped = True
                    break
                (tree / TPL / fname).write_text(text.replace(anchor, replacement), encoding="utf-8")
            if stopped:
                ok = False
                continue
            res = run_tests(tree, args.python)
            failed = [line for line in res.stdout.splitlines() if line.startswith("FAILED")]
            caught = any(f"::{must_fail}" in line for line in failed)
            verdict = "CAUGHT" if res.returncode != 0 and caught else "MISSED"
            print(f"  M{i + 1} {name}: {verdict} (expected red: {must_fail}; red: {[line.split('::')[-1].split(' ')[0] for line in failed]})")
            ok &= verdict == "CAUGHT"
    print("  ALL MUTATIONS CAUGHT" if ok else "  MUTATION CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
