# Progress — docs remediation (Ultrawork Iteration 2 Phase 2 IMPL)

- Session: `20260628-064120`
- Scope: C6 docs remediation only
- Updated docs:
  - `docs/CLI-MCP-COMMANDS.md`
  - `docs/pros-hilfe-src/endnutzerhandbuch.md`

## Completed

- Added Microsoft Graph canonical MCP server name and local compatibility command.
- Documented safe write MCP-wrapper-only Graph actions.
- Documented delegated-only / no-application-permissions stance.
- Added attachment allowlist / denylist / size limits.
- Added forbidden Graph operations and readiness tiers.

## Verification

- `npm run typecheck` ✅
- `npm run lint` ✅
- `npm test` ✅
- Doc search confirming allowed / forbidden Graph operations ✅

## Notes

- No implementation code was modified.
- Unrelated repository changes were present before this edit and were left untouched.
