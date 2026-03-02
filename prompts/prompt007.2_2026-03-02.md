# Slack MCP Setup

Continue: Set up Slack MCP server in Claude Code

## Completed so far

- Verified no Slack MCP server is currently configured (~/.claude/settings.json is {})
- Confirmed the only active MCP servers are deepwiki and chrome-devtools
- User confirmed they have their Slack Bot Token (xoxb-...) ready
- User needs to look up their Slack Team/Workspace ID — was given instructions on how to find it (URL method: <https://app.slack.com/client/T.../...>)

## Remaining work

1. Collect the bot token and team ID from the user
2. Write the Slack MCP server config to ~/.claude/settings.json:

    ```json
    {
      "mcpServers": {
        "slack": {
          "command": "npx",
          "args": ["-y", "@anthropic/mcp-server-slack"],
          "env": {
            "SLACK_BOT_TOKEN": "<user's token>",
            "SLACK_TEAM_ID": "<user's team ID>"
          }
        }
      }
    }
    ```

3. Restart Claude Code (or run /mcp) to pick up the new server
4. Test the Slack MCP server: list channels, search for users

## Key context

- ~/.claude/settings.json currently contains {} — safe to write without losing existing config
- No project-level .claude/settings.json exists; this is a global (user-level) setup
- The user's original request was to test the Slack MCP server (list channels, search users) — setup is a prerequisite

---

## Launch Command

```bash
claude --dangerously-skip-permissions --rename "P7.2: Slack MCP Setup"
```

---
