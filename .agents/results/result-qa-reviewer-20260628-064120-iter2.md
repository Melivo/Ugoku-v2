# QA Result — 20260628-064120 Iteration 2 VERIFY Steps 6-8

## Review Result: WARNING

PASS/FAIL: FAIL

VERIFY_GATE: FAIL

## Summary

Fresh-context QA reviewed the C6 documentation remediation in:
- `docs/CLI-MCP-COMMANDS.md`
- `docs/pros-hilfe-src/endnutzerhandbuch.md`

Most requested Graph write-safety documentation is present: allowed wrapper-only write operations, `confirmationStatus: "CONFIRMED"`, attachment allow/deny rules and limits, shared delegated targets (`mailbox` / `calendarOwner`), readiness tiers, and forbidden direct send/delete/raw Graph operations.

However, `docs/CLI-MCP-COMMANDS.md` still lists the admin OAuth scopes as read-only (`Mail.Read`, `Calendars.Read`) and includes stale delete-support wording, while the implementation/tests require delegated business-write-safe scopes (`Mail.ReadWrite`, `Calendars.ReadWrite`) for the documented safe write wrappers. This is a MEDIUM docs alignment defect.

## Findings

### CRITICAL
- None.

### HIGH
- None.

### MEDIUM
- `docs/CLI-MCP-COMMANDS.md:112` — The Graph admin setup scope list documents only read-oriented scopes and says `offline_access` is for refresh "after local delete support exists". This contradicts the documented safe write wrappers and the implementation, which requests delegated `Mail.ReadWrite` and `Calendars.ReadWrite`, and it reintroduces confusing delete-support wording next to forbidden delete operations. — Remediation:
  ```md
  - Scopes are delegated-only: `User.Read`, `Mail.Read`, `Mail.ReadWrite`, `Calendars.ReadWrite`, `Files.Read`, and `offline_access`. No application permissions are used.
  ```

### LOW
- None.

## Verification Details

### Step 6 Alignment
- FAIL due the MEDIUM scope/delete wording issue above.
- Verified present elsewhere:
  - Allowed wrappers: `graph_create_calendar_event`, `graph_update_calendar_event`, `graph_invite_calendar_attendees`, `graph_create_email_draft`, `graph_update_email_draft`, `graph_add_email_draft_attachment` in `docs/CLI-MCP-COMMANDS.md:76`.
  - Confirmation and shared targets in `docs/CLI-MCP-COMMANDS.md:106` and `docs/pros-hilfe-src/endnutzerhandbuch.md:237`.
  - Attachment allow/deny and limits in `docs/CLI-MCP-COMMANDS.md:115` and `docs/pros-hilfe-src/endnutzerhandbuch.md:239`.
  - Readiness tiers in `docs/CLI-MCP-COMMANDS.md:119` and `docs/pros-hilfe-src/endnutzerhandbuch.md:243`.
  - Forbidden direct send/delete/raw operations in `docs/CLI-MCP-COMMANDS.md:117` and `docs/pros-hilfe-src/endnutzerhandbuch.md:241`.

### Step 7 Security/Bug Review
- PASS for no raw write CLI command exposure in the two reviewed docs: Serena search found no `pros integrations graph ... create/update/send/delete/draft/invite/attachment` commands.
- PASS for no direct send/delete/raw Graph tool exposure: forbidden operations are documented as forbidden, not supported.
- PASS for no client-config secret storage guidance: docs direct secrets/tokens to OS Credential Store and state no secrets in config.
- PASS for no application permissions: docs explicitly say no application permissions are used.

### Step 8 Regression Review
- `npm run typecheck`: PASS
- `npm run lint`: PASS
- `npm test`: PASS — 21 test files, 166 passed, 1 skipped

### Step 8.1 Quality Score
- Simple post-verify score: 89.0 / 100 (Grade B)
- Calculation: prior stable baseline 94.0 minus 5.0 for one MEDIUM documentation alignment issue.

## Scope / C1-C5 Regression Check

- Current worktree still contains broad uncommitted C1-C5 implementation files from earlier session work.
- Iteration-2 docs memory (`result-docs-20260628-064120-iter2`) lists only `docs/CLI-MCP-COMMANDS.md` and `docs/pros-hilfe-src/endnutzerhandbuch.md` as updated.
- This QA pass did not find evidence that C1-C5 were re-implemented during the C6 docs iteration; the remaining failure is docs-only.

## Acceptance Criteria Checklist

- [x] Reviewed both requested customer-facing docs.
- [x] Used Serena pattern searches to verify required documentation content.
- [x] Checked for forbidden raw write/send/delete/raw/application-permission/secret-storage implications.
- [x] Ran `npm run typecheck`.
- [x] Ran `npm run lint`.
- [x] Ran `npm test`.
- [x] Computed post-verify quality score.
- [ ] VERIFY_GATE passes — blocked by MEDIUM finding.
