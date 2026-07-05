# juniper-canopy

This is a notes file for a new, run-all-tests script

## Initial environment setup

install juniper-data-client
start juniper-data application
start juniper-cascor backend service

## Environment Vars to set

RUN_SERVER_TESTS=1
CASCOR_BACKEND_AVAILABLE=1
JUNIPER_DATA_E2E_TEST=1
REDIS_INTEGRATION_TEST=1
CASSANDRA_INTEGRATION_TEST=1


CI PIPELINES:

# Next Steps

## Investigate V38a/c issue

0. develop a plan for addressing V38a/c.
1. thoroughly document the existing situation for V38a/c.
2. perform a detailed analysis of V38a/c, and document the analysis approach and results.
3. suggest several options to address each element identified in the analysis.
4. evaluate the options' strenghts, weaknesses, risks, and guard rails.
5. recommend a preferred option with the reasoning justifying that recommendation.
6. document results of all actions performed into a markdown file in the notes/ directory.
7. audit and validate all aspects of the markdown planning document.
7. lint the markdown file, and fix any syntax violations.

## Address the V17/V18 Secret config

0. develop a plan for addressing V17/V18.
1. thoroughly document the existing situation for V17/V18.
2. generate a detailed walkthrough for creating and properly configuring the associated secrets.
3. consider and document best practices and security concerns.
4. audit and validate all aspects of this plan / walkthrough.
5. write the results into a markdown file in the notes/ directory.
6. lint the markdown file, and fix any syntax violations.

---

ROADMAP:

all PRs have been merged.
yes, track the deferred CAN-015g/h items.
perform a detailed analysis of the CAN-015g/h issues.
create a plan for addressing these issues.
audit and validate all aspects of the plan.
write the plan into a markdown file in the notes/ directory.
lint the document and correct any syntax issues.
