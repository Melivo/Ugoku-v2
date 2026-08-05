# Test- und Lint-Failures behoben

Date: 2026-07-06
Workflow: debug
Session: debug-test-lint-20260706

## Symptom

- `npm run test` schlug fehl in `tests/mcp-config.test.ts` mit Assertion gegen `.agents/mcp_config.json`.
- Erwartet wurde `timeout: 180000`; erhalten wurde ein alter Serena-Shape mit `command: "serena"`, `--context antigravity`, `--open-web-dashboard`, ohne UTF-8-Env und ohne Timeout.
- `npm run lint` schlug fehl mit 67 Biome-Formatdiagnostics im Lint-Scope.

## Root Cause

- `.agents/mcp_config.json` war gegen den kanonischen Serena-Shape in `.agents/mcp.json` gedriftet.
- `tests/mcp-config.test.ts` validiert bewusst beide MCP-Dateien auf denselben lokalen, client-aware Serena-Startbefehl.
- Lint-Failures waren Format-/Line-ending-Diffs, keine TypeScript-Fehler.

## Fix Applied

- `.agents/mcp_config.json` Serena-Block auf den kanonischen Shape aus `.agents/mcp.json` gebracht.
- Biome-Formatierung auf den bestehenden `npm run lint`-Scope angewendet.

## Regression Tests / Verification

- `npm run test`: PASS, 26 test files, 197 passed, 1 skipped.
- `npm run lint`: PASS, 67 files checked.
- `npm run typecheck`: PASS.
- `git diff --check`: keine Whitespace-Fehler, nur Git-CRLF-Warnungen.

## Similar Pattern Scan

- MCP search for `--open-web-dashboard`, `"command": "serena"`, and `--context antigravity` found no remaining active config drift.
- Remaining hits are historical bug reports and the negative assertion in `tests/mcp-config.test.ts`.

## Files Changed

- `.agents/mcp_config.json`
- Formatting changes across the configured lint scope: `package.json`, `tsconfig*.json`, `packages/pros-cli/src`, `packages/pros-cli/package.json`, `packages/pros-cli/tsconfig.json`, `tests`.
