#!/usr/bin/1env bash

# Custom Agent Development Script

# This script is used to develop custom agents for Claude Code.

# Example:
#   Output document filename format: [PROJECT]_[APPLICATION]_[SUBJECT]_TASK_TYPE]_[DATE].md.
#

# Notes:
#    This script is used to develop custom agents for Claude Code.
#
#    Custom Agent Types:
#       - Template Agent
#           - Purpose: Reusable task pattern for recurring work categories
#           - Frequency: ?
#           - Distinguishing features:
#               - Descriptive snake_case filename
#               - Full Role + Resources + Directives + Deliverables structure
#               - Explicit placeholders for customization
#               - Code change approval disclaimers
#               - Designed for reuse, not single sessions
#           - Description: This agent is used to create effective, actionable prompts for common tasks that fall into well-defined prompt type categories.
#               - Evaluate the provided task description to determine the nature of the task and specific requirements for the task whether implicit or explicit.
#               - Based on the task analysis and requirement identification, determine the prompt category of the task, based on the available templates.
#               - If the task is not a match for any of the available prompt templates, use the generic prompt template to create a custom prompt.
#                   - after work has completed, determine if the custom prompt can be converted to a template prompt for future use.
#               - Use the appropriate, selected prompt template to create the task-specific prompt.
#               - the generated, task-specific prompt should be properly formatted and linted markdown.
#           - Prompt structure:
#               ```
#               # [Category Title]
#               ## Role:
#               ## Resources:
#               ## Primary Objective:
#               ## Assigned Tasks / Directives:
#               ## Key Deliverables and Requirements:
#               ```
#       - Planning Agent
#           - Purpose: Design strategy, architecture, or migration plan
#           - Frequency: ?
#           - Distinguishing features:
#               - This agent type is a key aspect of the Juniper project's design-first approach.
#               - Often produces output documents (plans, proposals, analyses, designs, roadmaps, etc.)
#               - References existing architecture and dependencies
#               - Can be single or cross-repo in scope
#           -Description:
#               - the output document should be saved to the notes/ sub-directory of the Juniper Project directory: /home/pcalnon/Development/python/Juniper/juniper-ml/ .
#               - the output document should be named in upper snake case, in the following format: JUNIPER_[APPLICATION]_[SUBJECT]_TASK_TYPE]_[DATE].md.
#               - the outout document format should be in properly formatted and linted markdown.
#           - Prompt structure:
#               ```
#               # [Subject] Plan / Analysis / Design
#               ## Role:
#               ## Overview / Background
#               ## Resources:
#               ## Primary Objective:
#               ## Assigned Tasks / Directives:
#               ## Key Deliverables and Requirements:
#               ```
#       - Audit Agent
#           - Purpose: Systematic review and validation of existing state
#           - Distinguishing features:
#               - Checklist-driven
#               - Phase-based execution (iterate across repos)
#               - Comparison against standards or templates
#               - Comparison against existing documentation and codebase statej
#               - Produces findings reports
#               - References validation criteria
#                  - including but not limited to:
#                      - documentation references with line nubmers
#                      - codebase state with line numbers
#                      - external documents and sources with specific URL references, and downloaded content where possible.
#           - Description:
#               - the output document should be saved to the notes/ sub-directory of the Juniper Project directory: /home/pcalnon/Development/python/Juniper/juniper-ml/ .
#               - the output document should be named in upper snake case, in the following format: JUNIPER_[APPLICATION]_[SUBJECT]_AUDIT_[DATE].md.
#               - the outout document format should be in properly formatted and linted markdown.
#           - Prompt structure:
#               ```
#               # [Subject] Audit
#               ## Role:
#               ## Overview / Background
#               ## Resources:
#               ## Primary Objective:
#               ## Assigned Tasks / Directives:
#               ## Key Deliverables and Requirements:
#               ```
#       - Task Agent
#           - Purpose: Execute a specific task or action
#           - Distinguishing features:
#               - Numbered steps or phases
#               - May include code blocks with examples
#               - Usually targets 1-3 repos
#               - Variable length (short for focused tasks, long for multi-phase work)
#           - Description:
#               - the task agent will not necessarily produce an output document, but will execute the task and provide feedback on the task's progress and completion.
#               - the task agent should be able to execute tasks in a single repository or across multiple repositories.
#               - the task agent will typically be executing a prompt that has been previously generated by a template agent or planning agent.
#           - Prompt structure:
#               ```
#               # [Action Verb] [Task Subject] Task
#               ## Role:
#               ## Overview / Background:
#               ## Resources:
#               ## Primary Objective:
#               ## Assigned Tasks / Directives:
#               ## Key Deliverables and Requirements:
#               ```
#    Future Work:  Additional Agent Types:
#       - Infrastructure Agent
#       - Review Agent
#       - Refactor Agent
#       - Test Agent
#       - Documentation Agent
#       - Code Review Agent
#
#
#                      - existing documentation and codebase state with line numbers
#                      - existing documentation and codebase state with line numbers
