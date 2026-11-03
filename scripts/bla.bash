CLAUDE_SKIP_PERMISSIONS_PARAM: 1
CLAUDE_REMOTE_CONTROL_PARAM: 1
CLAUDE_WORKTREE_PARAM: 1
CLAUDE_PROMPT_PARAM: Hello World, Claude!
CLAUDE_EFFORT_PARAM: max
CLAUDE_RESUME_PARAM: 1
CLAUDE_MODEL_PARAM: opus
CLAUDE_ID_PARAM: 1
Launching Default Interactive session with Claude Code
/home/pcalnon/Development/python/Juniper/juniper-ml/scripts/wake_the_claude.bash --model opus --effort max -- --dangerously-skip-permissions --prompt \"Hello World, Claude!\" 
wake_the_claude.bash: main(185): Define Model Name Constants
wake_the_claude.bash: main(195): Define Model Name Array
wake_the_claude.bash: main(205): Define Model Name Alias Constants
wake_the_claude.bash: main(218): Define Model Alias Array
wake_the_claude.bash: main(228): Define Model Name and Alias Validation Array
wake_the_claude.bash: main(247): Define Effort values
wake_the_claude.bash: main(262): Define Effort Array
wake_the_claude.bash: main(278): Define Parsed Param values
wake_the_claude.bash: main(296): Define Parameter Flag and Value Arrays
wake_the_claude.bash: main(313): Define Param values to be passed to Claude
wake_the_claude.bash: main(320): Define Valid Prompt Boolean Flags
wake_the_claude.bash: main(335): Define Claude Code parameter flags
wake_the_claude.bash: main(353): Define Input parameter flags
wake_the_claude.bash: main(375): Define Index values for Valid Patterns Array
wake_the_claude.bash: main(377): MODEL_FLAGS_INDEX: 0
wake_the_claude.bash: main(378): EFFORT_FLAGS_INDEX: 1
wake_the_claude.bash: main(379): WORKTREE_FLAGS_INDEX: 2
wake_the_claude.bash: main(380): REMOTE_CONTROL_FLAGS_INDEX: 3
wake_the_claude.bash: main(381): SESSION_ID_FLAGS_INDEX: 4
wake_the_claude.bash: main(382): PERMISSIONS_FLAGS_INDEX: 5
wake_the_claude.bash: main(383): RESUME_FLAGS_INDEX: 6
wake_the_claude.bash: main(384): SPACER_FLAGS_INDEX: 7
wake_the_claude.bash: main(385): PROMPT_FLAGS_INDEX: 8
wake_the_claude.bash: main(386): PATH_FLAGS_INDEX: 9
wake_the_claude.bash: main(387): FILE_FLAGS_INDEX: 10
wake_the_claude.bash: main(388): HEADLESS_FLAGS_INDEX: 11
wake_the_claude.bash: main(389): FORK_SESSION_FLAGS_INDEX: 12
wake_the_claude.bash: main(390): MODEL_VERSION_FLAGS_INDEX: 13
wake_the_claude.bash: main(391): SCRIPT_VERSION_FLAGS_INDEX: 14
wake_the_claude.bash: main(392): HELP_FLAGS_INDEX: 15
wake_the_claude.bash: main(393): USAGE_FLAGS_INDEX: 16
wake_the_claude.bash: main(398): Define Valid Patterns Array
wake_the_claude.bash: main(1733): Verify that input parameters have been provided
wake_the_claude.bash: main(1735): Input Params: [10 args]
wake_the_claude.bash: main(1741): Completed verifying that input parameters have been provided
wake_the_claude.bash: main(1744): Parse input parameters
wake_the_claude.bash: main(1749): Current Flag: "--model"
wake_the_claude.bash: main(1750): Remaining Params: size: 9, values: [opus --effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1753): Validating Input Param Flag: "--model"
wake_the_claude.bash: main(1758): Validated Input Param Flag: "--model"
wake_the_claude.bash: main(1761): Saving current state of input parameters
wake_the_claude.bash: main(1763): Remaining Params: size: 9, values: [opus --effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1765): Updated Params: size: 9, values: [opus --effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1768): Parsing Input Param Flag: "--model"
wake_the_claude.bash: get_pattern_index(1641): Parsing Pattern Index
wake_the_claude.bash: get_pattern_index(1643): Current Element: "--model"
wake_the_claude.bash: get_pattern_index(1646): Valid Patterns: size: 17, values: [-m | --model | --llm-model | --ai-model | --model-type -e | --effort | --effort-type | --effort-level -w | --worktree | --work-tree | --working-tree -c | --remote | --control | --remote-control -i | --id | --session | --session-id | --session-name | -t | --thread | --thread-name | --thread-id -s | --skip | --skip-permissions | --dangerously-skip-permissions -r | --resume | --resume-thread | --resume-session -- -p | --prompt | --prompt-string -l | --path | --file-path -f | --file | --file-name -a | --print | --agent | --silent | --headless --fork | --fork-session | --resume-fork | --resume-fork_session -V | --version | --claude-version -v | --version -h | --help | -? -u | --usage]
wake_the_claude.bash: get_pattern_index(1648): Getting Pattern Index for Current Element: "--model"
wake_the_claude.bash: get_pattern_index(1655): Pattern Index: "0"
wake_the_claude.bash: main(1770): Pattern Index: 0
wake_the_claude.bash: parse_add_model_flags(884): Parsing add model flags
wake_the_claude.bash: parse_add_model_flags(886): Current Flag: "--model"
wake_the_claude.bash: parse_add_model_flags(888): Current Model: "opus"
wake_the_claude.bash: validate_model(643): Validating Model parameter value
wake_the_claude.bash: validate_model(645): Model parameter value: opus
wake_the_claude.bash: validate_model(647): 1. Valid Model parameter value: 0
wake_the_claude.bash: validate_model(649): Validate Claude Code Model Param Value: opus
wake_the_claude.bash: validate_model(652): Model Validated: opus
wake_the_claude.bash: validate_model(656): 2. Valid Model parameter value: 0
wake_the_claude.bash: validate_model(661): Successfully Validated Claude Code Model Param Value: opus
wake_the_claude.bash: validate_model(663): 3. Valid Model parameter value: 0
wake_the_claude.bash: parse_add_model_flags(923): Selected Model Name validated: "opus"
wake_the_claude.bash: parse_add_model_flags(934): Claude Model Value: "--model opus"
wake_the_claude.bash: parse_add_model_flags(935): Result Value: "0"
wake_the_claude.bash: parse_add_model_flags(937): Updating Current Params
wake_the_claude.bash: parse_add_model_flags(939): Current Params: size: 8, values: [--effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: parse_add_model_flags(941): Updated Params: size: 8, values: [--effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1797): Completed Parsing: "--model"
wake_the_claude.bash: main(1798): Setting Updated Params
wake_the_claude.bash: main(1800): Remaining Params: size: 8, values: [--effort max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1749): Current Flag: "--effort"
wake_the_claude.bash: main(1750): Remaining Params: size: 7, values: [max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1753): Validating Input Param Flag: "--effort"
wake_the_claude.bash: main(1758): Validated Input Param Flag: "--effort"
wake_the_claude.bash: main(1761): Saving current state of input parameters
wake_the_claude.bash: main(1763): Remaining Params: size: 7, values: [max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1765): Updated Params: size: 7, values: [max -- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1768): Parsing Input Param Flag: "--effort"
wake_the_claude.bash: get_pattern_index(1641): Parsing Pattern Index
wake_the_claude.bash: get_pattern_index(1643): Current Element: "--effort"
wake_the_claude.bash: get_pattern_index(1646): Valid Patterns: size: 17, values: [-m | --model | --llm-model | --ai-model | --model-type -e | --effort | --effort-type | --effort-level -w | --worktree | --work-tree | --working-tree -c | --remote | --control | --remote-control -i | --id | --session | --session-id | --session-name | -t | --thread | --thread-name | --thread-id -s | --skip | --skip-permissions | --dangerously-skip-permissions -r | --resume | --resume-thread | --resume-session -- -p | --prompt | --prompt-string -l | --path | --file-path -f | --file | --file-name -a | --print | --agent | --silent | --headless --fork | --fork-session | --resume-fork | --resume-fork_session -V | --version | --claude-version -v | --version -h | --help | -? -u | --usage]
wake_the_claude.bash: get_pattern_index(1648): Getting Pattern Index for Current Element: "--effort"
wake_the_claude.bash: get_pattern_index(1655): Pattern Index: "1"
wake_the_claude.bash: main(1770): Pattern Index: 1
wake_the_claude.bash: parse_add_effort_flags(949): Parsing effort flags
wake_the_claude.bash: parse_add_effort_flags(952): Current Flag: "--effort"
wake_the_claude.bash: parse_add_effort_flags(955): Current Effort: "max"
wake_the_claude.bash: parse_add_effort_flags(964): Received a Valid Effort Flag
wake_the_claude.bash: validate_effort(672): Validate Claude Code Effort Param Value: max
wake_the_claude.bash: validate_effort(675): Effort Validated: max
wake_the_claude.bash: validate_effort(684): Validated Claude Code Effort Param Value: max
wake_the_claude.bash: parse_add_effort_flags(979): Current Effort Name validated: "max"
wake_the_claude.bash: parse_add_effort_flags(988): Claude Effort Value: [--effort max]
wake_the_claude.bash: parse_add_effort_flags(989): Result Value: "0"
wake_the_claude.bash: parse_add_effort_flags(996): Effort Value: "--effort max"
wake_the_claude.bash: parse_add_effort_flags(997): Result Value: "0"
wake_the_claude.bash: parse_add_effort_flags(999): Updating Current Params
wake_the_claude.bash: parse_add_effort_flags(1001): Current Params: size: 6, values: [-- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: parse_add_effort_flags(1003): Updated Params: size: 6, values: [-- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1797): Completed Parsing: "--effort"
wake_the_claude.bash: main(1798): Setting Updated Params
wake_the_claude.bash: main(1800): Remaining Params: size: 6, values: [-- --dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1749): Current Flag: "--"
wake_the_claude.bash: main(1750): Remaining Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1753): Validating Input Param Flag: "--"
wake_the_claude.bash: main(1758): Validated Input Param Flag: "--"
wake_the_claude.bash: main(1761): Saving current state of input parameters
wake_the_claude.bash: main(1763): Remaining Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1765): Updated Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1768): Parsing Input Param Flag: "--"
wake_the_claude.bash: get_pattern_index(1641): Parsing Pattern Index
wake_the_claude.bash: get_pattern_index(1643): Current Element: "--"
wake_the_claude.bash: get_pattern_index(1646): Valid Patterns: size: 17, values: [-m | --model | --llm-model | --ai-model | --model-type -e | --effort | --effort-type | --effort-level -w | --worktree | --work-tree | --working-tree -c | --remote | --control | --remote-control -i | --id | --session | --session-id | --session-name | -t | --thread | --thread-name | --thread-id -s | --skip | --skip-permissions | --dangerously-skip-permissions -r | --resume | --resume-thread | --resume-session -- -p | --prompt | --prompt-string -l | --path | --file-path -f | --file | --file-name -a | --print | --agent | --silent | --headless --fork | --fork-session | --resume-fork | --resume-fork_session -V | --version | --claude-version -v | --version -h | --help | -? -u | --usage]
wake_the_claude.bash: get_pattern_index(1648): Getting Pattern Index for Current Element: "--"
wake_the_claude.bash: get_pattern_index(1655): Pattern Index: "7"
wake_the_claude.bash: main(1770): Pattern Index: 7
wake_the_claude.bash: parse_spacer_flags(1242): Received Spacer Flag
wake_the_claude.bash: parse_spacer_flags(1244): Current Flag: "--"
wake_the_claude.bash: parse_spacer_flags(1251): Received Spacer Flag: "--"
wake_the_claude.bash: parse_spacer_flags(1257): Result Value: "0"
wake_the_claude.bash: parse_spacer_flags(1260): Updating Current Params
wake_the_claude.bash: parse_spacer_flags(1262): Current Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: parse_spacer_flags(1264): Updated Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1797): Completed Parsing: "--"
wake_the_claude.bash: main(1798): Setting Updated Params
wake_the_claude.bash: main(1800): Remaining Params: size: 5, values: [--dangerously-skip-permissions --prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1749): Current Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: main(1750): Remaining Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1753): Validating Input Param Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: main(1758): Validated Input Param Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: main(1761): Saving current state of input parameters
wake_the_claude.bash: main(1763): Remaining Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1765): Updated Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1768): Parsing Input Param Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: get_pattern_index(1641): Parsing Pattern Index
wake_the_claude.bash: get_pattern_index(1643): Current Element: "--dangerously-skip-permissions"
wake_the_claude.bash: get_pattern_index(1646): Valid Patterns: size: 17, values: [-m | --model | --llm-model | --ai-model | --model-type -e | --effort | --effort-type | --effort-level -w | --worktree | --work-tree | --working-tree -c | --remote | --control | --remote-control -i | --id | --session | --session-id | --session-name | -t | --thread | --thread-name | --thread-id -s | --skip | --skip-permissions | --dangerously-skip-permissions -r | --resume | --resume-thread | --resume-session -- -p | --prompt | --prompt-string -l | --path | --file-path -f | --file | --file-name -a | --print | --agent | --silent | --headless --fork | --fork-session | --resume-fork | --resume-fork_session -V | --version | --claude-version -v | --version -h | --help | -? -u | --usage]
wake_the_claude.bash: get_pattern_index(1648): Getting Pattern Index for Current Element: "--dangerously-skip-permissions"
wake_the_claude.bash: get_pattern_index(1655): Pattern Index: "5"
wake_the_claude.bash: main(1770): Pattern Index: 5
wake_the_claude.bash: parse_add_permissions_flags(1011): Parsing add permissions flags
wake_the_claude.bash: parse_add_permissions_flags(1013): Current Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: parse_add_permissions_flags(1015): Current Permissions: "--prompt"
wake_the_claude.bash: parse_add_permissions_flags(1023): Received Valid Permissions Flag: "--dangerously-skip-permissions"
wake_the_claude.bash: parse_add_permissions_flags(1029): Warning: Received Spacer Flags as Permissions Value.
wake_the_claude.bash: parse_add_permissions_flags(1070): Result Value: "0"
wake_the_claude.bash: parse_add_permissions_flags(1071): Permissions Value: "--dangerously-skip-permissions"
wake_the_claude.bash: parse_add_permissions_flags(1073): Updating Current Params
wake_the_claude.bash: parse_add_permissions_flags(1075): Current Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: parse_add_permissions_flags(1077): Updated Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1797): Completed Parsing: "--dangerously-skip-permissions"
wake_the_claude.bash: main(1798): Setting Updated Params
wake_the_claude.bash: main(1800): Remaining Params: size: 4, values: [--prompt "Hello World, Claude!"]
wake_the_claude.bash: main(1749): Current Flag: "--prompt"
wake_the_claude.bash: main(1750): Remaining Params: size: 3, values: ["Hello World, Claude!"]
wake_the_claude.bash: main(1753): Validating Input Param Flag: "--prompt"
wake_the_claude.bash: main(1758): Validated Input Param Flag: "--prompt"
wake_the_claude.bash: main(1761): Saving current state of input parameters
wake_the_claude.bash: main(1763): Remaining Params: size: 3, values: ["Hello World, Claude!"]
wake_the_claude.bash: main(1765): Updated Params: size: 3, values: ["Hello World, Claude!"]
wake_the_claude.bash: main(1768): Parsing Input Param Flag: "--prompt"
wake_the_claude.bash: get_pattern_index(1641): Parsing Pattern Index
wake_the_claude.bash: get_pattern_index(1643): Current Element: "--prompt"
wake_the_claude.bash: get_pattern_index(1646): Valid Patterns: size: 17, values: [-m | --model | --llm-model | --ai-model | --model-type -e | --effort | --effort-type | --effort-level -w | --worktree | --work-tree | --working-tree -c | --remote | --control | --remote-control -i | --id | --session | --session-id | --session-name | -t | --thread | --thread-name | --thread-id -s | --skip | --skip-permissions | --dangerously-skip-permissions -r | --resume | --resume-thread | --resume-session -- -p | --prompt | --prompt-string -l | --path | --file-path -f | --file | --file-name -a | --print | --agent | --silent | --headless --fork | --fork-session | --resume-fork | --resume-fork_session -V | --version | --claude-version -v | --version -h | --help | -? -u | --usage]
wake_the_claude.bash: get_pattern_index(1648): Getting Pattern Index for Current Element: "--prompt"
wake_the_claude.bash: get_pattern_index(1655): Pattern Index: "8"
wake_the_claude.bash: main(1770): Pattern Index: 8
wake_the_claude.bash: parse_prompt_value_flags(1272): Parsing prompt value flags
wake_the_claude.bash: parse_prompt_value_flags(1274): Current Flag: "--prompt"
wake_the_claude.bash: parse_prompt_value_flags(1276): Current Prompt: ""Hello World, Claude!""
wake_the_claude.bash: parse_prompt_value_flags(1284): Received Prompt Value Flag: "--prompt"
wake_the_claude.bash: parse_prompt_value_flags(1300): Received an apparent valid Prompt Value: ""Hello World, Claude!"".
wake_the_claude.bash: parse_prompt_value_flags(1301): Setting Prompt Value: ""Hello World, Claude!""
wake_the_claude.bash: parse_prompt_value_flags(1309): Prompt Value: "--prompt "Hello World, Claude!""
wake_the_claude.bash: parse_prompt_value_flags(1310): Result Value: "0"
wake_the_claude.bash: parse_prompt_value_flags(1312): Updating Current Params
wake_the_claude.bash: parse_prompt_value_flags(1314): Current Params: size: 0, values: []
wake_the_claude.bash: parse_prompt_value_flags(1316): Updated Params: size: 0, values: []
wake_the_claude.bash: main(1797): Completed Parsing: "--prompt"
wake_the_claude.bash: main(1798): Setting Updated Params
wake_the_claude.bash: main(1800): Remaining Params: size: 0, values: []
wake_the_claude.bash: main(1816): Completed Appending Claude Code Params: 7
wake_the_claude.bash: main(1817): Claude Code Params: --model opus --effort max --dangerously-skip-permissions --prompt "Hello World, Claude!"
wake_the_claude.bash: main(1818): Completed Parsing input parameters
wake_the_claude.bash: main(1824): Build Claude Code Prompt
wake_the_claude.bash: main(1836): Completed building prompt, 7 total args
wake_the_claude.bash: main(1842): Executing claude with 7 args
wake_the_claude.bash: main(1870): "/home/pcalnon/.local/bin/claude" --model opus --effort max --dangerously-skip-permissions --prompt "Hello World, Claude!"
"/home/pcalnon/.local/bin/claude" --model opus --effort max --dangerously-skip-permissions --prompt "Hello World, Claude!"
error: unknown option '--prompt'
(Did you mean one of --from-pr, --print?)
wake_the_claude.bash: main(1875): Error: claude exited with non-zero status 1
Closed Default Interactive session with Claude Code
