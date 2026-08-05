# Ultrawork final status - Pros MCP client configuration (2026-06-05)

Status: SHIP remediation completed and verified.

Implemented/confirmed:
- `pros mcp status/configure/disable` for OpenCode and AnythingLLM HubSpot entries.
- HubSpot credentials handled through OS Credential Store with `pros mcp hubspot credentials set --client-id <id> --client-secret-stdin`.
- `pros-mcp-hubspot-remote` local wrapper used for both OpenCode and AnythingLLM.
- OpenCode Pros-managed HubSpot entry shape: `type: "local"`, `command: ["pros-mcp-hubspot-remote"]`, `enabled: true`.
- AnythingLLM Pros-managed HubSpot entry shape: `command: "pros-mcp-hubspot-remote"`, `args: []`.
- Configure refuses to overwrite non-Pros hubspot entries unless `--force` is used.
- Disable removes only exact Pros-managed shapes.
- Doctor/status check HubSpot credentials only for Pros-managed entries.
- Runtime workflow, runtime skills, manifest, README, CLI docs, credential docs, and design doc updated to remove stale OpenCode env-placeholder/remote-OAuth default guidance.

Verification passed after final docs/runtime changes:
- `npm run typecheck` in `packages/pros-cli`
- `npm run lint` in `packages/pros-cli`
- `npm test` in `packages/pros-cli` (136 passed, 1 skipped)
- `npm run build` in `packages/pros-cli`
- `node scripts/validate-runtime-files.js` (valid, 23 existing non-blocking skill-format warnings)
- `npm run release:dry-run`

Residual notes:
- `pros mcp status anythingllm --probe` remains optional live probe; static status/doctor are the default.
- `node scripts/validate-runtime-files.js` still emits a package.json module-type warning and known skill-format warnings; these are non-blocking and pre-existing for this work.
- `.serena/memories/*` workflow artifacts are untracked and should be treated as workflow context, not source changes unless intentionally committed.
