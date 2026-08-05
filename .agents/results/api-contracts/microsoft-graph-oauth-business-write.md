# Microsoft Graph OAuth Business Write Contracts

## Scope

This contract defines the cross-boundary interfaces for the Microsoft Graph business-write plan:

- Pros CLI commands for OAuth, status, and MCP client configuration.
- Local Microsoft Graph MCP tool contracts for OpenCode and AnythingLLM.
- Microsoft Graph delegated-permission boundary.

The implementation must consult official Microsoft Graph documentation whenever Graph behavior is unclear or an implementation attempt fails.

## Authentication

All Microsoft Graph calls use delegated OAuth for the signed-in Microsoft user. Tokens are stored only in the OS Credential Store. OpenCode and AnythingLLM client configs must not contain tokens, refresh tokens, auth codes, client secrets, or tenant secrets.

Required delegated scopes:

```text
openid profile offline_access User.Read Mail.Read Mail.ReadWrite Calendars.ReadWrite Files.Read
```

Product policy forbids send/delete/raw Graph operations even if Microsoft scopes technically permit them.

## CLI Contracts

### `pros integrations auth microsoft-graph start`

- Description: Start Microsoft Graph OAuth PKCE authorization.
- Inputs: optional profile ID if existing CLI supports it.
- Output: authorization URL, session ID, requested scopes.
- Errors: missing client ID, session write failure, invalid profile.

### `pros integrations auth microsoft-graph status`

- Description: Show credential readiness, signed-in account, token health, and capability tier.
- Output states: `needs-auth`, `ready-read`, `ready-business-write-safe`, `limited`, `needs-reauth`, `needs-admin-consent`.
- Errors: credential parse failure, refresh failure, Graph `/me` failure.

### `pros integrations auth microsoft-graph logout`

- Description: Delete stored Graph credential for the selected profile.
- Output: deleted/not-found status.
- Errors: credential store deletion failure.

### `pros mcp configure opencode --include microsoft-graph`

- Description: Configure OpenCode to launch the local Microsoft Graph MCP server.
- Output: changed/unchanged status and config path.
- Security: writes command-only config, no secrets.

### `pros mcp configure anythingllm --include microsoft-graph`

- Description: Configure AnythingLLM to launch the local Microsoft Graph MCP server.
- Output: changed/unchanged status and config path.
- Security: writes command-only config, no secrets.

## MCP Server Naming Contract

The customer-facing Microsoft Graph MCP server name should avoid unnecessary Pros branding.

Preferred exposed server name: `microsoft-graph`.

The implementation may keep an internal compatibility alias only if needed for existing tests, command wrappers, or released configs. If an alias is kept, document which name is canonical and which is compatibility-only.

## MCP Tool Contracts

All write tools require an explicit confirmation input, for example `confirmationStatus: "CONFIRMED"`. Missing confirmation must fail before any Graph call.

### `graph_status`

- Description: Return credential readiness and signed-in account summary.
- Input: optional `profileId`.
- Output: status, account summary, scopes, capability tier.
- Errors: `needs-auth`, `needs-reauth`, `needs-admin-consent`.

### `graph_search_mail`

- Description: Search bounded mail summaries.
- Input: `query`, optional `limit`, optional `mailbox`.
- Output: message summaries only.
- Errors: invalid query, permission denied, rate limited.

### `graph_list_calendar`

- Description: List bounded calendar events.
- Input: `start`, `end`, optional `limit`, optional `calendarOwner`.
- Output: event summaries.
- Errors: invalid range, permission denied, rate limited.

### `graph_create_calendar_event`

- Description: Create a calendar event for the signed-in user or delegated calendar.
- Input: subject, start, end, timeZone, optional attendees, location, body, calendarOwner, confirmationStatus.
- Output: created event summary and web link if available.
- Auth: requires `business-write-safe`.
- Errors: missing confirmation, invalid time range, permission denied, Graph validation failure.

### `graph_update_calendar_event`

- Description: Update allowed fields on an existing event without deleting it.
- Input: eventId, patch fields, optional calendarOwner, confirmationStatus.
- Output: updated event summary.
- Auth: requires `business-write-safe`.
- Errors: missing confirmation, event not found, ambiguous recurring event, permission denied.

### `graph_invite_calendar_attendees`

- Description: Add attendees to an existing event.
- Input: eventId, attendees, optional calendarOwner, confirmationStatus.
- Output: updated attendee summary.
- Auth: requires `business-write-safe`.
- Errors: missing confirmation, invalid attendee, event not found, permission denied.

### `graph_create_email_draft`

- Description: Create an email draft only.
- Input: to/cc/bcc, subject, body, optional mailbox, confirmationStatus.
- Output: draft ID and summary.
- Auth: requires `business-write-safe`.
- Errors: missing confirmation, invalid recipient, permission denied.

### `graph_update_email_draft`

- Description: Edit an existing draft only.
- Input: messageId, patch fields, optional mailbox, confirmationStatus.
- Output: updated draft summary.
- Auth: requires `business-write-safe`.
- Errors: missing confirmation, message not found, message is not a draft, permission denied.

### `graph_add_email_draft_attachment`

- Description: Add an allowed local attachment to an existing email draft.
- Input: messageId, localPath, optional mailbox, confirmationStatus.
- Output: attachment summary.
- Auth: requires `business-write-safe`.
- Validation: extension allowlist, MIME validation, conservative file and total-size bounds.
- Errors: missing confirmation, forbidden attachment type, file too large, message is not a draft, permission denied.

## Forbidden Interfaces

These interfaces must not be exposed:

- `graph_send_mail`
- `graph_delete_mail`
- `graph_delete_calendar_event`
- `graph_request`
- Any raw Microsoft Graph passthrough tool

## Attachment Allowlist

Allowed:

- `.pdf`
- `.docx`, `.xlsx`, `.pptx`
- `.odt`, `.ods`, `.odp`
- `.txt`, `.csv`, `.tsv`
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`

Forbidden:

- Archives such as `.zip`, `.tar`, `.gz`, `.rar`, `.7z`
- Binaries/executables such as `.exe`, `.dll`, `.msi`, `.bin`, `.dmg`, `.pkg`
- Scripts such as `.ps1`, `.bat`, `.cmd`, `.sh`, `.js`, `.vbs`, `.py`, `.rb`, `.pl`
- Source code such as `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.cs`, `.php`
- Macro Office files such as `.docm`, `.xlsm`, `.pptm`

## Shared Resource Contract

Tools may accept exact delegated targets:

- `mailbox`: shared mailbox email address.
- `calendarOwner`: shared calendar owner email address.

If omitted, tools default to the signed-in user's own mailbox/calendar. The implementation must not use application permissions or broad tenant-wide access.

## Error Model

Common error statuses:

- `needs-auth`
- `needs-reauth`
- `limited`
- `needs-admin-consent`
- `permission-denied`
- `not-found`
- `invalid-input`
- `confirmation-required`
- `forbidden-operation`
- `rate-limited`
- `graph-error`
