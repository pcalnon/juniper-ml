# Connect Slack to Claude-ai Web Chat

## Primary Objective

Configure Claude AI web chat (claude.ai) with read/write access to Slack.

## Completed so far

- Researched all available approaches for connecting claude.ai to Slack (Slack Connector, MCP Apps, Slack MCP Server)
- Wrote comprehensive setup procedure to notes/CLAUDE_SLACK_SETUP.md covering:
  - Approach 1: Slack Connector (read-only context pull)
  - Approach 2: MCP Apps / Interactive Tools (read + write with human-in-the-loop approval)
  - Approach 3: Slack's Official MCP Server for Claude Desktop/Code (programmatic read/write)
  - Prerequisites, security considerations, troubleshooting, and source links
- User edited the file after creation (formatting cleanup accepted)
- Attempted to execute the procedure via Chrome DevTools MCP but could not proceed — the browser session connected to DevTools is not authenticated on claude.ai (repeatedly lands on login page)

## Remaining work

1. Authenticate on claude.ai in the browser that Chrome DevTools MCP is connected to (or reconnect DevTools to the correct browser)
2. Execute Approach 1 — navigate to Settings > Connectors > Slack > Connect, complete OAuth flow
3. Execute Approach 2 — verify MCP Apps / interactive Slack tools are available after connector is enabled
4. Verify read access by asking Claude to search Slack messages
5. Verify write access by asking Claude to draft and send a test Slack message
6. Update notes/CLAUDE_SLACK_SETUP.md with any corrections discovered during execution

## Next Steps

1. verify the DevTools MCP is connected to a browser where you're authenticated on claude.ai
2. run list_pages and take_snapshot to confirm you see the chat interface, not the login page.

## Key context

- Procedure doc: notes/CLAUDE_SLACK_SETUP.md
- The Chrome DevTools MCP browser has no auth session for claude.ai — user said they were logged in but the page consistently showed the login screen. Likely a different browser/profile.
- Claude plan must be Pro, Max, Team, or Enterprise; Slack must be a paid plan
- Write access is human-in-the-loop (Claude drafts, user approves before sending)

## Git status

- Not a git repository at the parent Juniper/ level
- notes/CLAUDE_SLACK_SETUP.md was created and exists on disk

---

## Launch Command

```bash
claude --dangerously-skip-permissions --rename "P8.1: Connect Slack to Claude-ai Web Chat"
```

---
