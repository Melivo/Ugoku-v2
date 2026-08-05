# MCP Workflow Context Drift - 2026-07-08

## Symptom

QA review found that the shipped runtime workflow had enough commands for the narrow HubSpot/Graph/QNAP path, but not enough self-contained architecture context for an end-user LLM after `pros init`.

## Root Cause

The workflow relied on source-repo docs such as `docs/CLI-MCP-COMMANDS.md` and `docs/MCP-CREDENTIALS.md`, which are not installed into customer case folders. It also mixed `pros mcp configure` includes with SSOT/sync-managed local stdio MCPs and did not clearly separate Microsoft Graph OAuth URL preparation from readiness.

## Fix

- Added workflow-local shipped resources under `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/`.
- Added detailed redaction-safe troubleshooting context for OpenCode, AnythingLLM, HubSpot, Microsoft Graph, QNAP MCP Assistant, Serena, and local Office MCPs.
- Updated the workflow to load those resources, distinguish Pros-managed CLI includes from SSOT-managed MCPs, handle `validated-default-gated`, and clarify Microsoft Graph readiness and AnythingLLM probe behavior.
- Updated `README.md` so `--probe` is not presented as the normal post-config proof and the sample prompt is explicitly HubSpot-focused.
- Updated the MCP change inventory so these resources are reviewed for future MCP changes.

## Verification

- `npm test -- packages/pros-cli/src/runtime-builder.test.ts` PASS; verifies workflow resources including `mcp-architecture.md` and `debugging.md` are copied into the generated runtime projection.
- `git diff --check` PASS.
- `npm run lint` PASS.
- `npm run typecheck` PASS.
- `npm run release:dry-run` PASS for version `0.5.30` / tag `pros-v0.5.30`.
- `npm audit --audit-level=moderate` PASS, 0 vulnerabilities.
- `npm test` PASS, 213 passed / 1 skipped.
