# Backend Progress — 20260628-064120

Status: COMPLETED

Implemented Microsoft Graph MCP business-write plan for delegated user permissions only.

Completed:
- Canonical MCP server name changed to `microsoft-graph`; local compatibility command remains `pros-mcp-microsoft-graph`.
- OAuth scopes updated to `openid profile offline_access User.Read Mail.Read Mail.ReadWrite Calendars.ReadWrite Files.Read`.
- Graph status tiers implemented: `needs-auth`, `ready-read`, `ready-business-write-safe`, `limited`, `needs-reauth`, `needs-admin-consent`.
- Safety policy implemented: confirmation gate, delegated mailbox/calendar owner validation, attachment allow/deny/MIME/size policy.
- Calendar write helpers implemented: create event, update event, invite attendees; shared calendar owner path; no delete path.
- Mail draft helpers implemented: create draft, update draft only after `isDraft === true`, add allowed attachment only to drafts; shared mailbox path; no send/delete path.
- MCP tools added with explicit schemas and `confirmationStatus`; no send/delete/raw tools exposed.
- OpenCode and AnythingLLM config support added for command-only Microsoft Graph entries with no secrets.
- Docs/tracker updated for allowed/forbidden Graph operations and setup.

Official Microsoft docs consulted:
- https://learn.microsoft.com/en-us/graph/api/user-post-messages?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/message-update?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/message-post-attachments?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/user-post-events?view=graph-rest-1.0
- https://learn.microsoft.com/en-us/graph/api/event-update?view=graph-rest-1.0

Verification:
- npm test -- packages/pros-cli/src/integrations.test.ts packages/pros-cli/src/mcp-servers.test.ts: PASS
- npm test -- packages/pros-cli/src/microsoft-graph.test.ts: PASS
- npm test -- packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/mcp-servers.test.ts: PASS
- npm run typecheck: PASS
- npm run lint: PASS
- npm test: PASS (163 passed, 1 skipped)
