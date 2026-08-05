# pros CLI junction entrypoint no-op

Date: 2026-06-30

## Symptom

- `pros init --force` in a fresh test folder exited with status 0 but printed no output and created no `.pros`, `AGENTS.md`, or runtime files.
- OpenCode reported `MCP error -32000: Connection closed` for `pros-mcp-docx-local`, `pros-mcp-microsoft-graph`, and `pros-mcp-office-files`.

## Root Cause

The global npm package was installed as a Windows junction from `%APPDATA%/npm/node_modules/@pro-select/pros-cli` to the local source workspace. The npm PowerShell wrappers launched the script through the junction path, while Node ESM resolved `import.meta.url` to the real workspace path. Entrypoint guards compared those paths textually, decided the module was not executed directly, skipped startup, and exited successfully without starting the CLI or MCP stdio server.

## Fix

- `packages/pros-cli/src/cli.ts`: added `isDirectCliExecution()` with symlink-/junction-safe realpath normalization.
- `packages/pros-cli/src/mcp-common.ts`: updated `isDirectMcpExecution()` to compare realpaths before normalized path comparison.
- `packages/pros-cli/src/cli.test.ts`: added a Windows npm junction regression test for the CLI entrypoint.
- `packages/pros-cli/src/mcp-servers.test.ts`: added a Windows npm junction regression test for MCP entrypoints.

## Verification

- `npm test -- --run src/cli.test.ts src/mcp-servers.test.ts`: pass.
- `npm run typecheck`: pass.
- `npm run lint`: pass.
- `npm run build`: pass.
- Runtime smoke: `pros init --force --workspace <temp>` through the global junction created `.pros` and `pros-runtime-manifest.md` again.
- MCP smoke: `pros-mcp-docx-local`, `pros-mcp-microsoft-graph`, and `pros-mcp-office-files` stayed running instead of exiting immediately.

## Similar Pattern Scan

Serena scan found all remaining `isDirectMcpExecution(import.meta.url)` callers in `mcp-docx-local.ts`, `mcp-microsoft-graph.ts`, `mcp-office-files.ts`, and `mcp-qnap-files.ts`; all use the fixed shared guard. `mcp-qnap-assistant.ts` uses a filename suffix guard and is not affected by the path equality issue.
