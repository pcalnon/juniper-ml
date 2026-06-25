# Slack MCP Setup

Test the Slack MCP server integration that was just configured.

## Completed so far

- Installed korotovsky/slack-mcp-server as a Claude Code MCP server (user scope, stdio transport)
- Slack App created with User OAuth Token (xoxp-) and full scopes:
  - channels:history
  - channels:read
  - groups:history
  - groups:read
  - im:history
  - im:read
  - im:write
  - mpim:history
  - mpim:read
  - mpim:write
  - users:read
  - chat:write
  - search:read
- Token stored as SLACK_MCP_XOXP_TOKEN env var in ~/.bashrc
- MCP config references ${SLACK_MCP_XOXP_TOKEN} for runtime expansion
- Old incorrect xapp- token entry cleaned up from .bashrc

## Remaining work

- Verify the slack MCP server is running — check /mcp status
- Test read tools: channels_list, users_search, conversations_history
- Test search: conversations_search_messages
- Test write (if enabled): conversations_add_message
- If any tools fail, troubleshoot token permissions or server config

## Key context

- Server package: slack-mcp-server@latest by korotovsky (Go-based, runs via npx)
- Config location: ~/.claude.json (user scope)
- Message posting is disabled by default — set SLACK_MCP_ADD_MESSAGE_TOOL=true in env to enable
- Docs: <https://github.com/korotovsky/slack-mcp-server>

## Verification commands

```bash
/mcp                    # Check server status in Claude Code
claude mcp list         # Verify registration from terminal
claude mcp get slack    # View full config
```

---
