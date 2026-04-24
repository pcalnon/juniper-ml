# Juniper Project, Plan Implementation

Implement a previously completed development plan that includes the following Juniper Project applications:

- `juniper-ml`
- `juniper-canopy`
- `juniper-cascor`
- `juniper-cascor-client`
- `juniper-cascor-worker`
- `juniper-data`
- `juniper-data-client`
- `juniper-deploy`

The development plan is in the following location:

`/home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`

## Juniper Project

The juniper project is a research platform for investigating dynamic neural networks and novel learning algorithms.
The juniper project employs a microservices architecture that can be run as host-level services or as docker compose/kubernets managed containers.
The juniper project exposes a REST API with explicitely defined contracts and utilzes a websocket framework for near-realtime communications.
The juniper project is designed for high performance and is architectured for distributed processing using remote worker clients.
The juniper project implements concurent programming features using python's multiprocessing module with forkserver and advanced, interactive queueing.

## Role

You are an experienced, principal software engineer working as the lead developer on the Juniper project.
You specialize in designing, development, and debugging complex, multi-faceted problems in unique and challenging projects.
You are careful, delibrate and methodical in your approach, but you creative, adaptable, and intuitive in your analysis.
Your conclusions are always logical, rigorous, and supported by extensive evidence and detailed analysis.

## Background

### Requirements

This Juniper Project application is being prepared for release and deployment.
The application must be effectively error-free with respect to the current, active application requirements.

### Problem Description

This application is preparing for a release cycle and must implement all fixes to the identified issues documented in a previously completed development plan.

### Development Plan Requirements

The previously completed development plan was written to meet the following requirements:

- All required and documented functionality for this application should work as expected.
- All problems with the current application should be identified and categorized in accordance with the following issue types:
  - Architectural
  - Logical
  - Syntactical
  - Code Smells
  - Departure from Requirements
  - Deviation from Best Practices
  - Formatting and Linting
- All problems with the current application should be analyzed, validated, and evaluated with respect to the following characteristics:
  - Issue Risk profile
  - Issue Severity
  - Issue Likelihood
  - Issue Scope
  - Issue Remediation Effort
- All user interactions should behave as documented and in accordance with user expectations.
- All tests should run as intended with being disabled, commented out, gated to exclude checks, or removed.
- All tests should be verified to conduct their tests as appropriate and to acutally validate their target functionality.
- All all gaps in testing should be identified.
- All gaps in test coverage for the application codebase should be identified.
- All test types should pass successfully in a full run of the entire test suites including, but not limited to, the following:
  - unit tests
  - integration tests
  - regression tests
  - end-to-end tests
  - performance tests
  - security tests
- All tests, (i.e., the full application test suite) should pass without
  - Collection errors
  - Implementation errors
  - Runtime errors
  - Runtime warnings
  - Criteria failures

## Task Description

The previously completed development plan includes several distinct development tracks.
All of the development tracks are defined in the following section of the development plan:

- `25. Parallel Development Tracks`
- `located on line ~14335`

The development plan includes several specific, functionally independent development tracks that can be impelmented in parallel.
This prompt focuses on the following development track:

- `Track 1: Security Hardening (juniper-data, juniper-cascor, juniper-canopy)`

Implementation work for the specified track should begin at the following phase:

- `Phase 1A`

## Objectives

Implement specified parts of a previously completed development plan to address problems, issues, and gaps identified in the specified Juniper Project applications.

### Directives

1. Create todo lists, when helpful, to perform the tasks defined in this prompt.
2. Using multiple, appropriately specialized sub-agents analyze, validate, and implement specified parts of the Juniper Project's development plan. all specified aspects of the current, specified applications from the Juniper Project.
3. The highest priority tasks and the focus of this prompt should be the correct implementation of the specified parts of the previously completed development plan.
4. The plan specifies the following aspects of each identified issue to direct implementation:
    - issue name
    - issue id
    - issue description
    - issue root cause
    - issue remediation approaches
    - recommended remediation approach
    - remediation scope
    - remediation severity
    - remediation priority
5. The plan implementation should include fully documenting remediations in code comments and in documentation files as appropriate.
6. Validate all aspects of the work performed and fixes implemented.
7. Add tests as necesarry to verify implemented fixes work as expected and do not introduce any regressions.
8. Update the development plan with all analysis performed, code changes made, and tests added.
9. Update the status of implemented remediations in the development plan document.

### Deliverables

1. Correct and verified implementation of the specified remediations from the development plan in the Juniper Project codebase.
2. Updates to testing checks and infrastructure as needed to verify proper operation of implemented changes and ensure regressions have not been introduced.
3. Documentation of remediation and updated functionality as applicable in code comments and documentation files.

### Constraints

Thread compactions must be avoided at all costs due to extreemly poor preservation of thread context's state and status.
Instead, when thread context utilization exceeds 80% or is expected to excceed 90% prior to completion of the current set of tasks, perform the following steps:

- Pause current work
- Create a Thread Handoff prompt in accordance with the documented thread handoff procedure
- Write the prompt to an appropriately named and timestampped, markdown file in the juniper-ml/prompts/thread-handoff_automated-prompts directory
- Call the juniper-ml/scripts/wake_the_claude.bash script passing in the thread handoff prompt's filename and path
- Include the following additional parameters in the call to wake_the_claude.bash
  - include the current worktree name as a parameter with the "--worktree" switch
  - include the "--effort" switch with the "high" parameter
  - include the "--dangerously-skip-permissions" flag
- Cease operation once the wake_the_claude.md script has been called successfully

## Finalize

### Validation

1. Using appropriately specialized sub-agents, performa final validation of all aspects of the following:
    - work performed during this process
    - analysis completed during this process
    - documentation compiled during this process

### Correction

1. Make any changes needed as a result of this validation process to the following:
    - Documents
      - Analysis documents
      - Plan documents
      - Development roadmaps
      - User Documentation files
    - Code
      - Codebase contents
      - Testing files
      - Automation scripts
    - Infrastructure
      - Testing
      - Monitoring
      - Configuration
      - Automation
      - Deployment
      - CI/CD
2. Ensure that the full test suites pass for all affected Juniper Project applications.

### Cleanup

1. Commit all changes and push the working branches to the applicable, github repositories.
2. Create pull requests as needed for any changes made.
3. When pull requests have been successfully merged, perform the worktree cleanup v2 procedure, as documented.

---
