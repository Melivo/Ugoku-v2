# Bug Report: Serena OMA MCP Config

## Symptom

- Serena MCP calls timed out with `MCP error -32001: Request timed out`.
- Affected calls included code search and memory tools.

## Root Cause

- Current Serena MCP connection is stale or hung.
- Repo-local `.agents/mcp.json` had an OMA-shipped Serena entry using `command: "serena"`, `--context claude-code`, and `--project .`.
- `serena` is not available on PATH here; the working global configuration uses `uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context antigravity --project-from-cwd`.

## Upstream Source

- `first-fluke/oh-my-agent` currently ships the stale Serena entry in `.agents/mcp.json`, `.agents/mcp_config.json`, and `.mcp.json`.
- OMA install logic copies `.agents/mcp.json` on fresh/forced installs and Antigravity config derives from it.

## Fix Applied

- Patched `.agents/mcp.json` to use `uvx --from git+https://github.com/oraios/serena ... --context antigravity --project-from-cwd`.
- Added `timeout: 60000`.
- Added regression coverage in `tests/mcp-config.test.ts`.

## Verification

- `npm test -- tests/mcp-config.test.ts` passed.
- `opencode mcp list` shows Serena connected via the global uvx command.

## Similar Patterns

- No active global `.gemini`/`.claude`/`.cursor` MCP files with the stale Serena config were found.
- Upstream OMA remains the confirmed source that can regenerate the stale config.
